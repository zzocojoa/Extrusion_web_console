import sqlite3
from pathlib import Path

import pytest

from backend.app.db.audit_repository import AuditRepository
from backend.app.db.row_attribution_repository import (
    FEATURE_DISABLED_REASON,
    RowAttributionRepository,
    build_exact_key_hash,
    build_safe_hash,
    build_source_evidence_hash,
)


HMAC_KEY = "fixture-row-attribution-key"


def _audit_id(db_path: Path, *, action: str = "upload.start") -> int:
    return AuditRepository(db_path).insert_audit(
        action=action,
        target_type="upload_job",
        target_id="upl_1",
        params={"mode": "preview_targets"},
        result="success",
        job_id="upl_1",
    )


def _attribution_kwargs(audit_id: int, *, operation_id: str = "upl_1") -> dict:
    return {
        "operation_id": operation_id,
        "operation_type": "upload_start",
        "operation_phase": "after_mutation",
        "audit_id": audit_id,
        "actor_id": "local_operator",
        "actor_role": "operator",
        "exact_key_hash": build_exact_key_hash("2026-06-18T09:00:00+09:00", "extruder_plc", HMAC_KEY),
        "source_evidence_hash": build_source_evidence_hash(
            {
                "operationId": operation_id,
                "sourceItemId": "preview_item_1",
                "rowCount": 1,
                "contentDigest": "a" * 64,
            },
            HMAC_KEY,
        ),
        "outcome": "upsert_accepted",
        "db_target_class": "local_operational",
        "db_fingerprint_hash": build_safe_hash("local_operational_db_fingerprint", HMAC_KEY),
        "schema_fingerprint_hash": build_safe_hash("schema_fingerprint_v1", HMAC_KEY),
    }


def test_default_feature_gate_blocks_attribution_writes(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    audit_id = _audit_id(db_path)
    repository = RowAttributionRepository(db_path)

    result = repository.append_attribution(**_attribution_kwargs(audit_id))

    assert result.created is False
    assert result.rejection_reason == FEATURE_DISABLED_REASON
    with repository.connect() as connection:
        row = connection.execute("SELECT COUNT(*) AS count FROM row_attribution_ledger").fetchone()
    assert row["count"] == 0


def test_enabled_repository_appends_and_lists_attribution_rows(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    audit_id = _audit_id(db_path)
    repository = RowAttributionRepository(db_path, writes_enabled=True)
    payload = _attribution_kwargs(audit_id)

    result = repository.append_attribution(**payload)

    assert result.created is True
    assert result.attribution_id is not None
    row = repository.get_attribution(result.attribution_id)
    assert row is not None
    assert row["operation_id"] == "upl_1"
    assert row["audit_id"] == audit_id
    assert row["outcome"] == "upsert_accepted"
    assert row["exact_key_hash"] == payload["exact_key_hash"]
    assert repository.list_by_operation("upl_1")[0]["attribution_id"] == result.attribution_id
    assert repository.list_by_exact_key_hash(payload["exact_key_hash"])[0]["operation_id"] == "upl_1"


def test_reconcile_attribution_inserts_later_row_without_mutating_original(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    first_audit_id = _audit_id(db_path, action="upload.delete_start")
    second_audit_id = _audit_id(db_path, action="upload.delete_reconciled")
    repository = RowAttributionRepository(db_path, writes_enabled=True)
    first_payload = _attribution_kwargs(first_audit_id, operation_id="del_1")
    first_payload["operation_type"] = "delete_start"
    first_payload["outcome"] = "unknown_requires_reconcile"
    first = repository.append_attribution(**first_payload)
    assert first.attribution_id is not None

    second_payload = _attribution_kwargs(second_audit_id, operation_id="del_1")
    second_payload["operation_type"] = "delete_reconcile"
    second_payload["outcome"] = "reconciled_absent"
    second = repository.append_reconcile_attribution(
        **{key: value for key, value in second_payload.items() if key != "operation_phase"},
        supersedes_attribution_id=first.attribution_id,
    )

    assert second.created is True
    rows = repository.list_by_operation("del_1")
    assert [row["outcome"] for row in rows] == ["unknown_requires_reconcile", "reconciled_absent"]
    assert rows[0]["supersedes_attribution_id"] is None
    assert rows[1]["supersedes_attribution_id"] == first.attribution_id


def test_missing_audit_row_is_rejected_by_foreign_key(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    AuditRepository(db_path)
    repository = RowAttributionRepository(db_path, writes_enabled=True)

    with pytest.raises(sqlite3.IntegrityError):
        repository.append_attribution(**_attribution_kwargs(999))


def test_invalid_hash_is_rejected_before_insert(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    audit_id = _audit_id(db_path)
    repository = RowAttributionRepository(db_path, writes_enabled=True)
    payload = _attribution_kwargs(audit_id)
    payload["exact_key_hash"] = "not-a-hash"

    with pytest.raises(ValueError, match="invalid_row_attribution_hash:exact_key_hash"):
        repository.append_attribution(**payload)
