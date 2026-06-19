import hashlib
import hmac
import json
import re
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping

from backend.app.db.preview_repository import iso_now


EXACT_KEY_HASH_VERSION = "hmac-sha256-v1"
SOURCE_EVIDENCE_HASH_VERSION = "hmac-sha256-source-v1"
FEATURE_DISABLED_REASON = "row_attribution_feature_disabled"

ALLOWED_OPERATION_TYPES = ("upload_start", "upload_retry", "delete_start", "delete_reconcile")
ALLOWED_OPERATION_PHASES = ("before_mutation", "after_mutation", "reconcile", "blocked")
ALLOWED_OUTCOMES = (
    "inserted",
    "upsert_accepted",
    "unchanged",
    "deleted",
    "reconciled_absent",
    "blocked",
    "failed_before_mutation",
    "unknown_requires_reconcile",
)

REQUIRED_COLUMNS = {
    "attribution_id",
    "operation_id",
    "operation_type",
    "operation_phase",
    "audit_id",
    "db_delta_id",
    "actor_id",
    "actor_role",
    "exact_key_hash",
    "exact_key_hash_version",
    "source_evidence_hash",
    "source_evidence_hash_version",
    "outcome",
    "reason_code",
    "db_target_class",
    "db_fingerprint_hash",
    "schema_fingerprint_hash",
    "supersedes_attribution_id",
    "created_at",
}
REQUIRED_INDEXES = {
    "idx_row_attr_operation_created",
    "idx_row_attr_exact_key_created",
    "idx_row_attr_audit",
    "idx_row_attr_db_delta",
    "idx_row_attr_outcome_created",
}
REQUIRED_TRIGGERS = {
    "row_attribution_ledger_no_update",
    "row_attribution_ledger_no_delete",
}

HEX_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
UNSAFE_TEXT_RE = re.compile(
    r"(?:[a-z][a-z0-9+.-]*://|Bearer\s+|eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.|[A-Za-z]:\\|\\\\|\.csv\b|\b(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)\b)",
    re.IGNORECASE,
)
UNSAFE_SOURCE_EVIDENCE_KEY_PARTS = (
    "authorization",
    "csv_row",
    "csvrow",
    "database_url",
    "databaseurl",
    "db_url",
    "dburl",
    "exception",
    "exactkey",
    "file_path",
    "filepath",
    "filename",
    "folder_path",
    "folderpath",
    "jwt",
    "raw",
    "secret",
    "service_key",
    "servicekey",
    "service_role",
    "servicerole",
    "source_path",
    "sourcepath",
    "sql",
    "token",
)


class RowAttributionSchemaError(RuntimeError):
    pass


@dataclass(frozen=True)
class RowAttributionAppendResult:
    created: bool
    attribution_id: int | None = None
    rejection_reason: str | None = None


def build_exact_key_hash(timestamp: str, device_id: str, hmac_key: str | bytes) -> str:
    canonical = f"{timestamp.strip()}\x1f{device_id.strip()}"
    return _hmac_sha256_hex(canonical, hmac_key)


def build_source_evidence_hash(evidence: Mapping[str, Any], hmac_key: str | bytes) -> str:
    _assert_safe_source_evidence(evidence)
    canonical = json.dumps(evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return _hmac_sha256_hex(canonical, hmac_key)


def build_safe_hash(value: str, hmac_key: str | bytes) -> str:
    _assert_no_unsafe_text(value, "safe_hash_input")
    return _hmac_sha256_hex(value, hmac_key)


def _hmac_sha256_hex(value: str, hmac_key: str | bytes) -> str:
    key = hmac_key if isinstance(hmac_key, bytes) else hmac_key.encode("utf-8")
    if not key:
        raise ValueError("row_attribution_hmac_key_required")
    return hmac.new(key, value.encode("utf-8"), hashlib.sha256).hexdigest()


def _assert_safe_source_evidence(value: Any, path: str = "source_evidence") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            lower_key = key_text.lower()
            if any(part in lower_key for part in UNSAFE_SOURCE_EVIDENCE_KEY_PARTS):
                raise ValueError(f"unsafe_source_evidence_key:{path}.{key_text}")
            _assert_safe_source_evidence(item, f"{path}.{key_text}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _assert_safe_source_evidence(item, f"{path}[{index}]")
        return
    if isinstance(value, str):
        _assert_no_unsafe_text(value, path)


def _assert_no_unsafe_text(value: str | None, field_name: str) -> None:
    if value and UNSAFE_TEXT_RE.search(value):
        raise ValueError(f"unsafe_row_attribution_value:{field_name}")


def _assert_hash_value(value: str, field_name: str) -> None:
    if not HEX_SHA256_RE.fullmatch(value):
        raise ValueError(f"invalid_row_attribution_hash:{field_name}")


class RowAttributionRepository:
    def __init__(self, db_path: str | Path, *, writes_enabled: bool = False) -> None:
        self.db_path = str(db_path)
        self.writes_enabled = bool(writes_enabled)
        self.bootstrap()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.db_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=5000")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def bootstrap(self) -> None:
        with self.connect() as connection:
            if self._table_exists(connection):
                self._assert_compatible_table(connection)
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS row_attribution_ledger (
                  attribution_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  operation_id TEXT NOT NULL,
                  operation_type TEXT NOT NULL CHECK(operation_type IN (
                    'upload_start',
                    'upload_retry',
                    'delete_start',
                    'delete_reconcile'
                  )),
                  operation_phase TEXT NOT NULL CHECK(operation_phase IN (
                    'before_mutation',
                    'after_mutation',
                    'reconcile',
                    'blocked'
                  )),
                  audit_id INTEGER NOT NULL REFERENCES audit_log(audit_id),
                  db_delta_id TEXT,
                  actor_id TEXT NOT NULL,
                  actor_role TEXT NOT NULL,
                  exact_key_hash TEXT NOT NULL,
                  exact_key_hash_version TEXT NOT NULL,
                  source_evidence_hash TEXT NOT NULL,
                  source_evidence_hash_version TEXT NOT NULL,
                  outcome TEXT NOT NULL CHECK(outcome IN (
                    'inserted',
                    'upsert_accepted',
                    'unchanged',
                    'deleted',
                    'reconciled_absent',
                    'blocked',
                    'failed_before_mutation',
                    'unknown_requires_reconcile'
                  )),
                  reason_code TEXT,
                  db_target_class TEXT NOT NULL,
                  db_fingerprint_hash TEXT NOT NULL,
                  schema_fingerprint_hash TEXT NOT NULL,
                  supersedes_attribution_id INTEGER REFERENCES row_attribution_ledger(attribution_id),
                  created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_row_attr_operation_created
                  ON row_attribution_ledger(operation_id, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_row_attr_exact_key_created
                  ON row_attribution_ledger(exact_key_hash, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_row_attr_audit
                  ON row_attribution_ledger(audit_id);
                CREATE INDEX IF NOT EXISTS idx_row_attr_db_delta
                  ON row_attribution_ledger(db_delta_id);
                CREATE INDEX IF NOT EXISTS idx_row_attr_outcome_created
                  ON row_attribution_ledger(outcome, created_at DESC);

                CREATE TRIGGER IF NOT EXISTS row_attribution_ledger_no_update
                BEFORE UPDATE ON row_attribution_ledger
                BEGIN
                  SELECT RAISE(ABORT, 'row_attribution_ledger_append_only');
                END;

                CREATE TRIGGER IF NOT EXISTS row_attribution_ledger_no_delete
                BEFORE DELETE ON row_attribution_ledger
                BEGIN
                  SELECT RAISE(ABORT, 'row_attribution_ledger_append_only');
                END;
                """
            )
            self._assert_compatible_table(connection)
            self._assert_required_indexes(connection)
            self._assert_required_triggers(connection)

    def ensure_schema(self) -> None:
        self.bootstrap()

    def initialize(self) -> None:
        self.bootstrap()

    def append_attribution(
        self,
        *,
        operation_id: str,
        operation_type: str,
        operation_phase: str,
        audit_id: int,
        actor_id: str,
        actor_role: str,
        exact_key_hash: str,
        source_evidence_hash: str,
        outcome: str,
        db_target_class: str,
        db_fingerprint_hash: str,
        schema_fingerprint_hash: str,
        db_delta_id: str | None = None,
        reason_code: str | None = None,
        supersedes_attribution_id: int | None = None,
        exact_key_hash_version: str = EXACT_KEY_HASH_VERSION,
        source_evidence_hash_version: str = SOURCE_EVIDENCE_HASH_VERSION,
    ) -> RowAttributionAppendResult:
        if not self.writes_enabled:
            return RowAttributionAppendResult(created=False, rejection_reason=FEATURE_DISABLED_REASON)
        self._validate_insert(
            operation_id=operation_id,
            operation_type=operation_type,
            operation_phase=operation_phase,
            actor_id=actor_id,
            actor_role=actor_role,
            exact_key_hash=exact_key_hash,
            source_evidence_hash=source_evidence_hash,
            outcome=outcome,
            db_target_class=db_target_class,
            db_fingerprint_hash=db_fingerprint_hash,
            schema_fingerprint_hash=schema_fingerprint_hash,
            db_delta_id=db_delta_id,
            reason_code=reason_code,
            exact_key_hash_version=exact_key_hash_version,
            source_evidence_hash_version=source_evidence_hash_version,
        )
        now = iso_now()
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO row_attribution_ledger(
                  operation_id, operation_type, operation_phase, audit_id, db_delta_id,
                  actor_id, actor_role, exact_key_hash, exact_key_hash_version,
                  source_evidence_hash, source_evidence_hash_version, outcome,
                  reason_code, db_target_class, db_fingerprint_hash,
                  schema_fingerprint_hash, supersedes_attribution_id, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    operation_id,
                    operation_type,
                    operation_phase,
                    audit_id,
                    db_delta_id,
                    actor_id,
                    actor_role,
                    exact_key_hash,
                    exact_key_hash_version,
                    source_evidence_hash,
                    source_evidence_hash_version,
                    outcome,
                    reason_code,
                    db_target_class,
                    db_fingerprint_hash,
                    schema_fingerprint_hash,
                    supersedes_attribution_id,
                    now,
                ),
            )
            return RowAttributionAppendResult(created=True, attribution_id=int(cursor.lastrowid))

    def append_reconcile_attribution(self, **kwargs: Any) -> RowAttributionAppendResult:
        return self.append_attribution(operation_phase="reconcile", **kwargs)

    def get_attribution(self, attribution_id: int) -> sqlite3.Row | None:
        with self.connect() as connection:
            return connection.execute(
                "SELECT * FROM row_attribution_ledger WHERE attribution_id = ?",
                (attribution_id,),
            ).fetchone()

    def list_by_operation(self, operation_id: str, *, limit: int = 100) -> list[sqlite3.Row]:
        with self.connect() as connection:
            return list(
                connection.execute(
                    """
                    SELECT *
                    FROM row_attribution_ledger
                    WHERE operation_id = ?
                    ORDER BY created_at ASC, attribution_id ASC
                    LIMIT ?
                    """,
                    (operation_id, limit),
                ).fetchall()
            )

    def list_by_exact_key_hash(self, exact_key_hash: str, *, limit: int = 100) -> list[sqlite3.Row]:
        _assert_hash_value(exact_key_hash, "exact_key_hash")
        with self.connect() as connection:
            return list(
                connection.execute(
                    """
                    SELECT *
                    FROM row_attribution_ledger
                    WHERE exact_key_hash = ?
                    ORDER BY created_at ASC, attribution_id ASC
                    LIMIT ?
                    """,
                    (exact_key_hash, limit),
                ).fetchall()
            )

    def _table_exists(self, connection: sqlite3.Connection) -> bool:
        row = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = 'row_attribution_ledger'
            """
        ).fetchone()
        return row is not None

    def _assert_compatible_table(self, connection: sqlite3.Connection) -> None:
        columns = {str(row["name"]) for row in connection.execute("PRAGMA table_info(row_attribution_ledger)").fetchall()}
        missing = sorted(REQUIRED_COLUMNS - columns)
        if missing:
            raise RowAttributionSchemaError(f"row_attribution_schema_incompatible:missing_columns:{','.join(missing)}")

    def _assert_required_indexes(self, connection: sqlite3.Connection) -> None:
        indexes = {
            str(row["name"])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index' AND tbl_name = 'row_attribution_ledger'"
            ).fetchall()
        }
        missing = sorted(REQUIRED_INDEXES - indexes)
        if missing:
            raise RowAttributionSchemaError(f"row_attribution_schema_incompatible:missing_indexes:{','.join(missing)}")

    def _assert_required_triggers(self, connection: sqlite3.Connection) -> None:
        triggers = {
            str(row["name"])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'trigger' AND tbl_name = 'row_attribution_ledger'"
            ).fetchall()
        }
        missing = sorted(REQUIRED_TRIGGERS - triggers)
        if missing:
            raise RowAttributionSchemaError(f"row_attribution_schema_incompatible:missing_triggers:{','.join(missing)}")

    def _validate_insert(
        self,
        *,
        operation_id: str,
        operation_type: str,
        operation_phase: str,
        actor_id: str,
        actor_role: str,
        exact_key_hash: str,
        source_evidence_hash: str,
        outcome: str,
        db_target_class: str,
        db_fingerprint_hash: str,
        schema_fingerprint_hash: str,
        db_delta_id: str | None,
        reason_code: str | None,
        exact_key_hash_version: str,
        source_evidence_hash_version: str,
    ) -> None:
        if operation_type not in ALLOWED_OPERATION_TYPES:
            raise ValueError("invalid_row_attribution_operation_type")
        if operation_phase not in ALLOWED_OPERATION_PHASES:
            raise ValueError("invalid_row_attribution_operation_phase")
        if outcome not in ALLOWED_OUTCOMES:
            raise ValueError("invalid_row_attribution_outcome")
        for field_name, value in (
            ("operation_id", operation_id),
            ("actor_id", actor_id),
            ("actor_role", actor_role),
            ("db_target_class", db_target_class),
            ("db_delta_id", db_delta_id),
            ("reason_code", reason_code),
            ("exact_key_hash_version", exact_key_hash_version),
            ("source_evidence_hash_version", source_evidence_hash_version),
        ):
            _assert_no_unsafe_text(value, field_name)
        for field_name, value in (
            ("exact_key_hash", exact_key_hash),
            ("source_evidence_hash", source_evidence_hash),
            ("db_fingerprint_hash", db_fingerprint_hash),
            ("schema_fingerprint_hash", schema_fingerprint_hash),
        ):
            _assert_hash_value(value, field_name)
