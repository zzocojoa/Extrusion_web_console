import json
import re
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping
from uuid import uuid4

from backend.app.db.preview_repository import iso_now
from backend.app.db.row_attribution_repository import ALLOWED_OPERATION_TYPES


ALLOWED_DELTA_RESULTS = (
    "matched",
    "mismatched",
    "not_measured",
    "blocked",
    "failed_before_mutation",
    "unknown_requires_reconcile",
)
ALLOWED_DELTA_QUERY_CLASSES = (
    "exact_key_count",
    "not_measured",
)
REQUIRED_COLUMNS = {
    "delta_id",
    "operation_id",
    "operation_type",
    "audit_id",
    "actor_id",
    "actor_role",
    "delta_scope_json",
    "delta_query_class",
    "before_count",
    "after_count",
    "expected_delta",
    "actual_delta",
    "measured_at",
    "result",
    "reason_code",
    "db_target_class",
    "db_fingerprint_hash",
    "created_at",
}
REQUIRED_NOT_NULL_COLUMNS = {
    "operation_id",
    "operation_type",
    "audit_id",
    "actor_id",
    "actor_role",
    "delta_scope_json",
    "delta_query_class",
    "measured_at",
    "result",
    "db_target_class",
    "created_at",
}
REQUIRED_FOREIGN_KEYS = {
    ("audit_id", "audit_log", "audit_id"),
}
REQUIRED_CHECK_CONSTRAINTS = {
    "operation_type": ALLOWED_OPERATION_TYPES,
    "delta_query_class": ALLOWED_DELTA_QUERY_CLASSES,
    "result": ALLOWED_DELTA_RESULTS,
}
REQUIRED_INDEXES = {
    "idx_db_delta_operation_created",
    "idx_db_delta_audit",
    "idx_db_delta_result_created",
}
REQUIRED_TRIGGERS = {
    "db_delta_evidence_no_update",
    "db_delta_evidence_no_delete",
}

HEX_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
UNSAFE_TEXT_RE = re.compile(
    r"(?:[a-z][a-z0-9+.-]*://|Bearer\s+|eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.|[A-Za-z]:\\|\\\\|\.csv\b|\b(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)\b)",
    re.IGNORECASE,
)
UNSAFE_SCOPE_KEY_PARTS = (
    "authorization",
    "csv_row",
    "csvrow",
    "database_url",
    "databaseurl",
    "db_url",
    "dburl",
    "exception",
    "exact_key",
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


class DbDeltaEvidenceSchemaError(RuntimeError):
    pass


@dataclass(frozen=True)
class DbDeltaAppendResult:
    delta_id: str


def _json(value: Mapping[str, Any]) -> str:
    _assert_safe_scope(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def decode_delta_scope_json(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return decoded if isinstance(decoded, dict) else {}


def _assert_safe_scope(value: Any, path: str = "delta_scope") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            lower_key = key_text.lower()
            if any(part in lower_key for part in UNSAFE_SCOPE_KEY_PARTS):
                raise ValueError(f"unsafe_db_delta_scope_key:{path}.{key_text}")
            _assert_safe_scope(item, f"{path}.{key_text}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _assert_safe_scope(item, f"{path}[{index}]")
        return
    if isinstance(value, str):
        _assert_no_unsafe_text(value, path)


def _assert_no_unsafe_text(value: str | None, field_name: str) -> None:
    if value and UNSAFE_TEXT_RE.search(value):
        raise ValueError(f"unsafe_db_delta_value:{field_name}")


def _assert_hash_value(value: str | None, field_name: str, *, required: bool) -> None:
    if value is None:
        if required:
            raise ValueError(f"missing_db_delta_hash:{field_name}")
        return
    if not HEX_SHA256_RE.fullmatch(value):
        raise ValueError(f"invalid_db_delta_hash:{field_name}")


class DbDeltaEvidenceRepository:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
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
                CREATE TABLE IF NOT EXISTS db_delta_evidence (
                  delta_id TEXT PRIMARY KEY,
                  operation_id TEXT NOT NULL,
                  operation_type TEXT NOT NULL CHECK(operation_type IN (
                    'upload_start',
                    'upload_retry',
                    'delete_start',
                    'delete_reconcile'
                  )),
                  audit_id INTEGER NOT NULL REFERENCES audit_log(audit_id),
                  actor_id TEXT NOT NULL,
                  actor_role TEXT NOT NULL,
                  delta_scope_json TEXT NOT NULL DEFAULT '{}',
                  delta_query_class TEXT NOT NULL CHECK(delta_query_class IN (
                    'exact_key_count',
                    'not_measured'
                  )),
                  before_count INTEGER CHECK(before_count IS NULL OR before_count >= 0),
                  after_count INTEGER CHECK(after_count IS NULL OR after_count >= 0),
                  expected_delta INTEGER,
                  actual_delta INTEGER,
                  measured_at TEXT NOT NULL,
                  result TEXT NOT NULL CHECK(result IN (
                    'matched',
                    'mismatched',
                    'not_measured',
                    'blocked',
                    'failed_before_mutation',
                    'unknown_requires_reconcile'
                  )),
                  reason_code TEXT,
                  db_target_class TEXT NOT NULL,
                  db_fingerprint_hash TEXT,
                  created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_db_delta_operation_created
                  ON db_delta_evidence(operation_id, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_db_delta_audit
                  ON db_delta_evidence(audit_id);
                CREATE INDEX IF NOT EXISTS idx_db_delta_result_created
                  ON db_delta_evidence(result, created_at DESC);

                CREATE TRIGGER IF NOT EXISTS db_delta_evidence_no_update
                BEFORE UPDATE ON db_delta_evidence
                BEGIN
                  SELECT RAISE(ABORT, 'db_delta_evidence_append_only');
                END;

                CREATE TRIGGER IF NOT EXISTS db_delta_evidence_no_delete
                BEFORE DELETE ON db_delta_evidence
                BEGIN
                  SELECT RAISE(ABORT, 'db_delta_evidence_append_only');
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

    def append_delta(
        self,
        *,
        operation_id: str,
        operation_type: str,
        audit_id: int,
        actor_id: str,
        actor_role: str,
        delta_scope: Mapping[str, Any],
        delta_query_class: str,
        result: str,
        db_target_class: str,
        before_count: int | None = None,
        after_count: int | None = None,
        expected_delta: int | None = None,
        actual_delta: int | None = None,
        reason_code: str | None = None,
        db_fingerprint_hash: str | None = None,
        delta_id: str | None = None,
    ) -> DbDeltaAppendResult:
        actual_delta = self._validate_insert(
            operation_id=operation_id,
            operation_type=operation_type,
            actor_id=actor_id,
            actor_role=actor_role,
            delta_scope=delta_scope,
            delta_query_class=delta_query_class,
            before_count=before_count,
            after_count=after_count,
            expected_delta=expected_delta,
            actual_delta=actual_delta,
            result=result,
            reason_code=reason_code,
            db_target_class=db_target_class,
            db_fingerprint_hash=db_fingerprint_hash,
        )
        now = iso_now()
        next_delta_id = delta_id or f"ddl_{uuid4().hex[:12]}"
        _assert_no_unsafe_text(next_delta_id, "delta_id")
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO db_delta_evidence(
                  delta_id, operation_id, operation_type, audit_id, actor_id,
                  actor_role, delta_scope_json, delta_query_class, before_count,
                  after_count, expected_delta, actual_delta, measured_at, result,
                  reason_code, db_target_class, db_fingerprint_hash, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    next_delta_id,
                    operation_id,
                    operation_type,
                    audit_id,
                    actor_id,
                    actor_role,
                    _json(delta_scope),
                    delta_query_class,
                    before_count,
                    after_count,
                    expected_delta,
                    actual_delta,
                    now,
                    result,
                    reason_code,
                    db_target_class,
                    db_fingerprint_hash,
                    now,
                ),
            )
        return DbDeltaAppendResult(delta_id=next_delta_id)

    def get_delta(self, delta_id: str) -> sqlite3.Row | None:
        with self.connect() as connection:
            return connection.execute(
                "SELECT * FROM db_delta_evidence WHERE delta_id = ?",
                (delta_id,),
            ).fetchone()

    def list_by_operation(self, operation_id: str, *, limit: int = 100) -> list[sqlite3.Row]:
        with self.connect() as connection:
            return list(
                connection.execute(
                    """
                    SELECT *
                    FROM db_delta_evidence
                    WHERE operation_id = ?
                    ORDER BY created_at ASC, delta_id ASC
                    LIMIT ?
                    """,
                    (operation_id, limit),
                ).fetchall()
            )

    def _table_exists(self, connection: sqlite3.Connection) -> bool:
        row = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = 'db_delta_evidence'
            """
        ).fetchone()
        return row is not None

    def _assert_compatible_table(self, connection: sqlite3.Connection) -> None:
        column_rows = connection.execute("PRAGMA table_info(db_delta_evidence)").fetchall()
        columns = {str(row["name"]): row for row in column_rows}
        missing = sorted(REQUIRED_COLUMNS - set(columns))
        if missing:
            raise DbDeltaEvidenceSchemaError(f"db_delta_schema_incompatible:missing_columns:{','.join(missing)}")
        delta_id = columns["delta_id"]
        if int(delta_id["pk"]) != 1 or str(delta_id["type"]).upper() != "TEXT":
            raise DbDeltaEvidenceSchemaError("db_delta_schema_incompatible:invalid_primary_key:delta_id")
        self._assert_required_not_null_columns(columns)
        self._assert_required_foreign_keys(connection)
        self._assert_required_check_constraints(self._table_sql(connection))

    def _assert_required_not_null_columns(self, columns: Mapping[str, sqlite3.Row]) -> None:
        missing = sorted(column for column in REQUIRED_NOT_NULL_COLUMNS if int(columns[column]["notnull"]) != 1)
        if missing:
            raise DbDeltaEvidenceSchemaError(f"db_delta_schema_incompatible:missing_not_null:{','.join(missing)}")

    def _assert_required_foreign_keys(self, connection: sqlite3.Connection) -> None:
        foreign_keys = {
            (str(row["from"]), str(row["table"]), str(row["to"]))
            for row in connection.execute("PRAGMA foreign_key_list(db_delta_evidence)").fetchall()
        }
        missing = sorted(REQUIRED_FOREIGN_KEYS - foreign_keys)
        if missing:
            serialized = ",".join(f"{column}->{table}.{target}" for column, table, target in missing)
            raise DbDeltaEvidenceSchemaError(f"db_delta_schema_incompatible:missing_foreign_keys:{serialized}")

    def _assert_required_check_constraints(self, table_sql: str) -> None:
        missing: list[str] = []
        invalid: list[str] = []
        for column, required_values in REQUIRED_CHECK_CONSTRAINTS.items():
            value_sets = self._check_constraint_value_sets(table_sql, column)
            required_set = set(required_values)
            if not value_sets:
                missing.append(column)
            elif any(values != required_set for values in value_sets):
                invalid.append(column)
        if missing:
            raise DbDeltaEvidenceSchemaError(
                f"db_delta_schema_incompatible:missing_check_constraints:{','.join(sorted(missing))}"
            )
        if invalid:
            raise DbDeltaEvidenceSchemaError(
                f"db_delta_schema_incompatible:invalid_check_constraints:{','.join(sorted(invalid))}"
            )

    def _table_sql(self, connection: sqlite3.Connection) -> str:
        row = connection.execute(
            """
            SELECT sql
            FROM sqlite_master
            WHERE type = 'table' AND name = 'db_delta_evidence'
            """
        ).fetchone()
        if row is None or not row["sql"]:
            raise DbDeltaEvidenceSchemaError("db_delta_schema_incompatible:missing_table_sql")
        return str(row["sql"])

    @staticmethod
    def _check_constraint_value_sets(table_sql: str, column: str) -> list[set[str]]:
        check_pattern = re.compile(
            rf"CHECK\s*\(\s*{re.escape(column)}\s+IN\s*\((?P<values>[^)]*)\)",
            re.IGNORECASE | re.DOTALL,
        )
        return [set(re.findall(r"'([^']+)'", match.group("values"))) for match in check_pattern.finditer(table_sql)]

    def _assert_required_indexes(self, connection: sqlite3.Connection) -> None:
        indexes = {
            str(row["name"])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index' AND tbl_name = 'db_delta_evidence'"
            ).fetchall()
        }
        missing = sorted(REQUIRED_INDEXES - indexes)
        if missing:
            raise DbDeltaEvidenceSchemaError(f"db_delta_schema_incompatible:missing_indexes:{','.join(missing)}")

    def _assert_required_triggers(self, connection: sqlite3.Connection) -> None:
        triggers = {
            str(row["name"])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'trigger' AND tbl_name = 'db_delta_evidence'"
            ).fetchall()
        }
        missing = sorted(REQUIRED_TRIGGERS - triggers)
        if missing:
            raise DbDeltaEvidenceSchemaError(f"db_delta_schema_incompatible:missing_triggers:{','.join(missing)}")

    def _validate_insert(
        self,
        *,
        operation_id: str,
        operation_type: str,
        actor_id: str,
        actor_role: str,
        delta_scope: Mapping[str, Any],
        delta_query_class: str,
        before_count: int | None,
        after_count: int | None,
        expected_delta: int | None,
        actual_delta: int | None,
        result: str,
        reason_code: str | None,
        db_target_class: str,
        db_fingerprint_hash: str | None,
    ) -> int | None:
        if operation_type not in ALLOWED_OPERATION_TYPES:
            raise ValueError("invalid_db_delta_operation_type")
        if delta_query_class not in ALLOWED_DELTA_QUERY_CLASSES:
            raise ValueError("invalid_db_delta_query_class")
        if result not in ALLOWED_DELTA_RESULTS:
            raise ValueError("invalid_db_delta_result")
        for field_name, value in (
            ("operation_id", operation_id),
            ("actor_id", actor_id),
            ("actor_role", actor_role),
            ("delta_query_class", delta_query_class),
            ("reason_code", reason_code),
            ("db_target_class", db_target_class),
        ):
            _assert_no_unsafe_text(value, field_name)
        _assert_safe_scope(delta_scope)
        for field_name, value in (("before_count", before_count), ("after_count", after_count)):
            if value is not None and value < 0:
                raise ValueError(f"invalid_db_delta_count:{field_name}")
        if before_count is not None and after_count is not None:
            computed_delta = after_count - before_count
            if actual_delta is None:
                actual_delta = computed_delta
            elif actual_delta != computed_delta:
                raise ValueError("invalid_db_delta_actual_delta")
        if result in {"matched", "mismatched"} and (
            before_count is None or after_count is None or expected_delta is None or actual_delta is None
        ):
            raise ValueError("db_delta_counts_required")
        if result == "matched" and expected_delta != actual_delta:
            raise ValueError("db_delta_matched_result_conflicts_with_delta")
        if result == "mismatched" and expected_delta == actual_delta:
            raise ValueError("db_delta_mismatched_result_requires_delta_difference")
        _assert_hash_value(db_fingerprint_hash, "db_fingerprint_hash", required=result in {"matched", "mismatched"})
        return actual_delta
