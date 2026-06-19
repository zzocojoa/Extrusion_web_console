from pathlib import Path

import pytest

from backend.app.db.audit_repository import AuditRepository
from backend.app.db.row_attribution_repository import (
    RowAttributionRepository,
    build_exact_key_hash,
    build_safe_hash,
    build_source_evidence_hash,
)


HMAC_KEY = "fixture-row-attribution-key"


def test_exact_key_hash_is_deterministic_and_separates_keys() -> None:
    first = build_exact_key_hash("2026-06-18T09:00:00+09:00", "extruder_plc", HMAC_KEY)
    second = build_exact_key_hash("2026-06-18T09:00:00+09:00", "extruder_plc", HMAC_KEY)
    different_device = build_exact_key_hash("2026-06-18T09:00:00+09:00", "extruder_temperature", HMAC_KEY)
    different_timestamp = build_exact_key_hash("2026-06-18T09:01:00+09:00", "extruder_plc", HMAC_KEY)

    assert first == second
    assert first != different_device
    assert first != different_timestamp
    assert len(first) == 64


def test_source_evidence_hash_rejects_raw_sensitive_evidence() -> None:
    with pytest.raises(ValueError, match="unsafe_source_evidence_key"):
        build_source_evidence_hash({"rawExactKey": "synthetic-key"}, HMAC_KEY)

    with pytest.raises(ValueError, match="unsafe_source_evidence_key"):
        build_source_evidence_hash({"dbUrl": "unsafe-value"}, HMAC_KEY)

    with pytest.raises(ValueError, match="unsafe_row_attribution_value"):
        build_source_evidence_hash({"safeId": "Bearer unsafe-value"}, HMAC_KEY)


def test_ledger_row_stores_hashes_without_raw_exact_key_or_source_values(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    raw_timestamp = "2026-06-18T09:00:00+09:00"
    raw_device_id = "extruder_plc"
    raw_source_label = "operator-source-label"
    audit_id = AuditRepository(db_path).insert_audit(
        action="upload.start",
        target_type="upload_job",
        target_id="upl_1",
        params={},
        result="success",
        job_id="upl_1",
    )
    repository = RowAttributionRepository(db_path, writes_enabled=True)

    result = repository.append_attribution(
        operation_id="upl_1",
        operation_type="upload_start",
        operation_phase="after_mutation",
        audit_id=audit_id,
        actor_id="local_operator",
        actor_role="operator",
        exact_key_hash=build_exact_key_hash(raw_timestamp, raw_device_id, HMAC_KEY),
        source_evidence_hash=build_source_evidence_hash(
            {
                "operationId": "upl_1",
                "sourceItemId": build_safe_hash(raw_source_label, HMAC_KEY),
                "contentDigest": "c" * 64,
                "rowCount": 1,
            },
            HMAC_KEY,
        ),
        outcome="upsert_accepted",
        db_target_class="local_operational",
        db_fingerprint_hash=build_safe_hash("local_operational_db_fingerprint", HMAC_KEY),
        schema_fingerprint_hash=build_safe_hash("schema_fingerprint_v1", HMAC_KEY),
    )

    assert result.attribution_id is not None
    row = repository.get_attribution(result.attribution_id)
    assert row is not None
    stored_values = "|".join(str(row[key]) for key in row.keys())
    assert raw_timestamp not in stored_values
    assert raw_device_id not in stored_values
    assert raw_source_label not in stored_values
    assert "upl_1" in stored_values
