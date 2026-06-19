import sqlite3
from pathlib import Path

import pytest

from backend.app.db.audit_repository import AuditRepository
from backend.app.db.preview_repository import PreviewRepository
from backend.app.db.row_attribution_repository import (
    ALLOWED_OPERATION_PHASES,
    ALLOWED_OPERATION_TYPES,
    ALLOWED_OUTCOMES,
    REQUIRED_INDEXES,
    REQUIRED_TRIGGERS,
    RowAttributionRepository,
    RowAttributionSchemaError,
    build_exact_key_hash,
    build_safe_hash,
    build_source_evidence_hash,
)
from backend.app.db.runtime_repository import RuntimeRepository
from backend.app.db.upload_delete_repository import UploadDeleteRepository
from backend.app.db.upload_job_repository import UploadJobRepository


HMAC_KEY = "fixture-row-attribution-key"


def _connect(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _audit_id(db_path: Path) -> int:
    return AuditRepository(db_path).insert_audit(
        action="upload.start",
        target_type="upload_job",
        target_id="upl_1",
        params={},
        result="success",
        job_id="upl_1",
    )


def _payload(audit_id: int) -> dict:
    return {
        "operation_id": "upl_1",
        "operation_type": "upload_start",
        "operation_phase": "after_mutation",
        "audit_id": audit_id,
        "actor_id": "local_operator",
        "actor_role": "operator",
        "exact_key_hash": build_exact_key_hash("2026-06-18T09:00:00+09:00", "extruder_plc", HMAC_KEY),
        "source_evidence_hash": build_source_evidence_hash(
            {"operationId": "upl_1", "sourceItemId": "preview_item_1", "contentDigest": "b" * 64},
            HMAC_KEY,
        ),
        "outcome": "upsert_accepted",
        "db_target_class": "local_operational",
        "db_fingerprint_hash": build_safe_hash("local_operational_db_fingerprint", HMAC_KEY),
        "schema_fingerprint_hash": build_safe_hash("schema_fingerprint_v1", HMAC_KEY),
    }


def _check_clause(column: str, values: tuple[str, ...]) -> str:
    serialized = ", ".join(f"'{value}'" for value in values)
    return f" CHECK({column} IN ({serialized}))"


def _existing_ledger_sql(
    *,
    audit_fk: bool = True,
    supersedes_fk: bool = True,
    primary_key: bool = True,
    operation_id_not_null: bool = True,
    checks: bool = True,
) -> str:
    attribution_id = "attribution_id INTEGER PRIMARY KEY AUTOINCREMENT" if primary_key else "attribution_id INTEGER"
    operation_id = "operation_id TEXT NOT NULL" if operation_id_not_null else "operation_id TEXT"
    operation_type_check = _check_clause("operation_type", ALLOWED_OPERATION_TYPES) if checks else ""
    operation_phase_check = _check_clause("operation_phase", ALLOWED_OPERATION_PHASES) if checks else ""
    outcome_check = _check_clause("outcome", ALLOWED_OUTCOMES) if checks else ""
    audit_id = "audit_id INTEGER NOT NULL REFERENCES audit_log(audit_id)" if audit_fk else "audit_id INTEGER NOT NULL"
    supersedes_attribution_id = (
        "supersedes_attribution_id INTEGER REFERENCES row_attribution_ledger(attribution_id)"
        if supersedes_fk
        else "supersedes_attribution_id INTEGER"
    )
    return f"""
        CREATE TABLE row_attribution_ledger (
          {attribution_id},
          {operation_id},
          operation_type TEXT NOT NULL{operation_type_check},
          operation_phase TEXT NOT NULL{operation_phase_check},
          {audit_id},
          db_delta_id TEXT,
          actor_id TEXT NOT NULL,
          actor_role TEXT NOT NULL,
          exact_key_hash TEXT NOT NULL,
          exact_key_hash_version TEXT NOT NULL,
          source_evidence_hash TEXT NOT NULL,
          source_evidence_hash_version TEXT NOT NULL,
          outcome TEXT NOT NULL{outcome_check},
          reason_code TEXT,
          db_target_class TEXT NOT NULL,
          db_fingerprint_hash TEXT NOT NULL,
          schema_fingerprint_hash TEXT NOT NULL,
          {supersedes_attribution_id},
          created_at TEXT NOT NULL
        )
    """


def test_bootstrap_creates_table_indexes_and_append_only_triggers(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    AuditRepository(db_path)
    RowAttributionRepository(db_path)

    with _connect(db_path) as connection:
        tables = {
            row["name"]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
        }
        indexes = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index' AND tbl_name = 'row_attribution_ledger'"
            ).fetchall()
        }
        triggers = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'trigger' AND tbl_name = 'row_attribution_ledger'"
            ).fetchall()
        }

    assert "row_attribution_ledger" in tables
    assert REQUIRED_INDEXES.issubset(indexes)
    assert REQUIRED_TRIGGERS.issubset(triggers)


def test_bootstrap_is_idempotent_and_preserves_existing_rows(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    audit_id = _audit_id(db_path)
    repository = RowAttributionRepository(db_path, writes_enabled=True)
    result = repository.append_attribution(**_payload(audit_id))
    assert result.created is True

    RowAttributionRepository(db_path).ensure_schema()

    rows = RowAttributionRepository(db_path).list_by_operation("upl_1")
    assert len(rows) == 1
    assert rows[0]["attribution_id"] == result.attribution_id


def test_existing_repository_bootstraps_still_pass_after_attribution_bootstrap(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    AuditRepository(db_path)
    RowAttributionRepository(db_path).ensure_schema()

    PreviewRepository(db_path).ensure_schema()
    UploadJobRepository(db_path).ensure_schema()
    UploadDeleteRepository(db_path).ensure_schema()
    RuntimeRepository(db_path)

    with _connect(db_path) as connection:
        tables = {
            row["name"]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
        }
    assert {
        "audit_log",
        "preview_runs",
        "upload_jobs",
        "delete_runs",
        "runtime_operations",
        "row_attribution_ledger",
    }.issubset(tables)


def test_append_only_triggers_block_update_and_delete(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    audit_id = _audit_id(db_path)
    repository = RowAttributionRepository(db_path, writes_enabled=True)
    result = repository.append_attribution(**_payload(audit_id))
    assert result.attribution_id is not None

    with repository.connect() as connection:
        with pytest.raises(sqlite3.IntegrityError, match="row_attribution_ledger_append_only"):
            connection.execute(
                "UPDATE row_attribution_ledger SET outcome = 'blocked' WHERE attribution_id = ?",
                (result.attribution_id,),
            )

    with repository.connect() as connection:
        with pytest.raises(sqlite3.IntegrityError, match="row_attribution_ledger_append_only"):
            connection.execute(
                "DELETE FROM row_attribution_ledger WHERE attribution_id = ?",
                (result.attribution_id,),
            )


def test_incompatible_existing_table_fails_closed_without_rewrite(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    with _connect(db_path) as connection:
        connection.execute("CREATE TABLE row_attribution_ledger (attribution_id INTEGER PRIMARY KEY)")

    with pytest.raises(RowAttributionSchemaError, match="row_attribution_schema_incompatible"):
        RowAttributionRepository(db_path)

    with _connect(db_path) as connection:
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(row_attribution_ledger)").fetchall()}
    assert columns == {"attribution_id"}


@pytest.mark.parametrize(
    ("schema_kwargs", "error_fragment"),
    [
        ({"audit_fk": False}, "missing_foreign_keys:audit_id->audit_log.audit_id"),
        (
            {"supersedes_fk": False},
            "missing_foreign_keys:supersedes_attribution_id->row_attribution_ledger.attribution_id",
        ),
        ({"primary_key": False}, "invalid_primary_key:attribution_id"),
        ({"operation_id_not_null": False}, "missing_not_null:operation_id"),
        ({"checks": False}, "missing_check_constraints:operation_phase,operation_type,outcome"),
    ],
)
def test_existing_table_missing_required_schema_contract_fails_closed(
    tmp_path: Path, schema_kwargs: dict, error_fragment: str
) -> None:
    db_path = tmp_path / "state.db"
    AuditRepository(db_path)
    with _connect(db_path) as connection:
        connection.execute(_existing_ledger_sql(**schema_kwargs))

    with pytest.raises(RowAttributionSchemaError, match="row_attribution_schema_incompatible") as exc_info:
        RowAttributionRepository(db_path)

    assert error_fragment in str(exc_info.value)
