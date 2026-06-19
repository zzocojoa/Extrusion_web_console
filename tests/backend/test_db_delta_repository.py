import sqlite3
from pathlib import Path

import pytest

from backend.app.db.audit_repository import AuditRepository
from backend.app.db.db_delta_repository import (
    REQUIRED_INDEXES,
    REQUIRED_TRIGGERS,
    DbDeltaEvidenceSchemaError,
    DbDeltaEvidenceRepository,
    decode_delta_scope_json,
)


DB_HASH = "a" * 64


def _audit_id(db_path: Path) -> int:
    return AuditRepository(db_path).insert_audit(
        action="upload.delete_start",
        target_type="delete_run",
        target_id="del_1",
        params={"deleteRunId": "del_1"},
        result="success",
    )


def test_bootstrap_creates_delta_table_indexes_and_append_only_triggers(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    AuditRepository(db_path)
    DbDeltaEvidenceRepository(db_path)

    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        tables = {
            row["name"]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
        }
        indexes = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index' AND tbl_name = 'db_delta_evidence'"
            ).fetchall()
        }
        triggers = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'trigger' AND tbl_name = 'db_delta_evidence'"
            ).fetchall()
        }

    assert "db_delta_evidence" in tables
    assert REQUIRED_INDEXES.issubset(indexes)
    assert REQUIRED_TRIGGERS.issubset(triggers)


def test_append_delta_records_safe_counts_and_audit_link(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    audit_id = _audit_id(db_path)
    repository = DbDeltaEvidenceRepository(db_path)

    result = repository.append_delta(
        operation_id="del_1",
        operation_type="delete_start",
        audit_id=audit_id,
        actor_id="local_operator",
        actor_role="operator",
        delta_scope={
            "operationId": "del_1",
            "selectedRowCount": 2,
            "selectionDigest": "b" * 64,
        },
        delta_query_class="exact_key_count",
        before_count=2,
        after_count=0,
        expected_delta=-2,
        result="matched",
        db_target_class="loopback_expected_db_port",
        db_fingerprint_hash=DB_HASH,
    )

    row = repository.get_delta(result.delta_id)
    assert row is not None
    assert row["operation_id"] == "del_1"
    assert row["audit_id"] == audit_id
    assert row["actual_delta"] == -2
    assert row["result"] == "matched"
    assert decode_delta_scope_json(row["delta_scope_json"])["selectedRowCount"] == 2
    assert repository.list_by_operation("del_1")[0]["delta_id"] == result.delta_id


def test_append_only_triggers_block_delta_update_and_delete(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    audit_id = _audit_id(db_path)
    repository = DbDeltaEvidenceRepository(db_path)
    result = repository.append_delta(
        operation_id="del_1",
        operation_type="delete_start",
        audit_id=audit_id,
        actor_id="local_operator",
        actor_role="operator",
        delta_scope={"operationId": "del_1", "selectedRowCount": 2},
        delta_query_class="exact_key_count",
        before_count=2,
        after_count=0,
        expected_delta=-2,
        result="matched",
        db_target_class="loopback_expected_db_port",
        db_fingerprint_hash=DB_HASH,
    )

    with repository.connect() as connection:
        with pytest.raises(sqlite3.IntegrityError, match="db_delta_evidence_append_only"):
            connection.execute("UPDATE db_delta_evidence SET result = 'blocked' WHERE delta_id = ?", (result.delta_id,))

    with repository.connect() as connection:
        with pytest.raises(sqlite3.IntegrityError, match="db_delta_evidence_append_only"):
            connection.execute("DELETE FROM db_delta_evidence WHERE delta_id = ?", (result.delta_id,))


def test_delta_scope_rejects_raw_sensitive_evidence(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    audit_id = _audit_id(db_path)
    repository = DbDeltaEvidenceRepository(db_path)

    with pytest.raises(ValueError, match="unsafe_db_delta_scope_key"):
        repository.append_delta(
            operation_id="del_1",
            operation_type="delete_start",
            audit_id=audit_id,
            actor_id="local_operator",
            actor_role="operator",
            delta_scope={"rawExactKey": "2026-06-18T09:00:00+09:00|extruder_integrated"},
            delta_query_class="not_measured",
            result="not_measured",
            reason_code="measurement_error",
            db_target_class="loopback_expected_db_port",
        )

    with pytest.raises(ValueError, match="unsafe_db_delta_value"):
        repository.append_delta(
            operation_id="del_1",
            operation_type="delete_start",
            audit_id=audit_id,
            actor_id="local_operator",
            actor_role="operator",
            delta_scope={"operationId": "del_1", "note": "Bearer unsafe-value"},
            delta_query_class="not_measured",
            result="not_measured",
            reason_code="measurement_error",
            db_target_class="loopback_expected_db_port",
        )


def test_mismatched_delta_requires_actual_difference(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    audit_id = _audit_id(db_path)
    repository = DbDeltaEvidenceRepository(db_path)

    with pytest.raises(ValueError, match="db_delta_mismatched_result_requires_delta_difference"):
        repository.append_delta(
            operation_id="del_1",
            operation_type="delete_start",
            audit_id=audit_id,
            actor_id="local_operator",
            actor_role="operator",
            delta_scope={"operationId": "del_1", "selectedRowCount": 2},
            delta_query_class="exact_key_count",
            before_count=2,
            after_count=0,
            expected_delta=-2,
            result="mismatched",
            db_target_class="loopback_expected_db_port",
            db_fingerprint_hash=DB_HASH,
        )


def test_incompatible_existing_delta_table_fails_closed_without_rewrite(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    AuditRepository(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE db_delta_evidence (
              delta_id TEXT PRIMARY KEY,
              operation_id TEXT NOT NULL,
              operation_type TEXT NOT NULL,
              audit_id INTEGER NOT NULL,
              actor_id TEXT NOT NULL,
              actor_role TEXT NOT NULL,
              delta_scope_json TEXT NOT NULL,
              delta_query_class TEXT NOT NULL,
              before_count INTEGER,
              after_count INTEGER,
              expected_delta INTEGER,
              actual_delta INTEGER,
              measured_at TEXT NOT NULL,
              result TEXT NOT NULL,
              reason_code TEXT,
              db_target_class TEXT NOT NULL,
              db_fingerprint_hash TEXT,
              created_at TEXT NOT NULL
            )
            """
        )

    with pytest.raises(DbDeltaEvidenceSchemaError, match="db_delta_schema_incompatible") as exc_info:
        DbDeltaEvidenceRepository(db_path)

    assert "missing_foreign_keys:audit_id->audit_log.audit_id" in str(exc_info.value)
