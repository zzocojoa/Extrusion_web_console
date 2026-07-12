from __future__ import annotations

import json
from concurrent.futures import Future
from pathlib import Path

from fastapi.testclient import TestClient

import backend.app.api.upload_preview as upload_preview_api
from backend.app.api.audit import get_audit_repository
from backend.app.api.upload_preview import get_preview_audit_repository, get_preview_repository
from backend.app.core.settings import Settings
from backend.app.core.settings import get_settings
from backend.app.db.audit_repository import AuditLogFilters, AuditRepository, decode_params_json
from backend.app.db.preview_repository import PreviewRepository
from backend.app.main import app, create_app
from backend.app.schemas.upload_preview import PreviewDbStatus, PreviewRunStatus
from backend.app.services.upload_preview import PREVIEW_FAILED_MESSAGE
from tests.backend.preview_test_support import approval_scope, pending_future, run_in_future


def test_upload_preview_routes_are_registered_in_openapi(monkeypatch) -> None:
    monkeypatch.setenv("EWC_API_DOCS_MODE", "enabled")
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.get("/api/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/upload/preview" in paths
    assert "post" in paths["/api/upload/preview"]
    assert "/api/upload/preview/latest" in paths
    assert "get" in paths["/api/upload/preview/latest"]
    assert "/api/upload/preview/{previewRunId}" in paths
    assert "get" in paths["/api/upload/preview/{previewRunId}"]
    assert "/api/upload/preview/{previewRunId}/cancel" in paths
    assert "post" in paths["/api/upload/preview/{previewRunId}/cancel"]
    worker_response = paths["/api/upload/preview"]["post"]["responses"]["503"]
    detail_schema = worker_response["content"]["application/json"]["schema"]["properties"]["detail"]
    assert worker_response["description"].startswith("The Preview run was persisted")
    assert set(detail_schema["required"]) == {
        "reason",
        "previewRunId",
        "restartRequired",
        "recovery",
    }
    assert detail_schema["properties"]["reason"]["enum"] == [
        "preview_worker_unavailable",
        "preview_worker_reconciliation_failed",
    ]
    assert "Location" in worker_response["headers"]
    get_settings.cache_clear()


def test_upload_preview_worker_contract_matches_frontend_fixture() -> None:
    contract = json.loads(
        (Path(__file__).parents[1] / "contracts" / "upload_preview_worker_error_contract.json").read_text(
            encoding="utf-8"
        )
    )
    assert contract == {
        "unavailable": {
            "reason": upload_preview_api.PREVIEW_WORKER_UNAVAILABLE_REASON,
            "recovery": upload_preview_api.PREVIEW_WORKER_RETRY_RECOVERY,
        },
        "reconciliationFailed": {
            "reason": upload_preview_api.PREVIEW_WORKER_RECONCILIATION_FAILED_REASON,
            "recovery": upload_preview_api.PREVIEW_WORKER_RESTART_RECOVERY,
        },
    }


def test_upload_preview_create_rejects_invalid_custom_range_before_work_starts(tmp_path) -> None:
    audit_repository = AuditRepository(str(tmp_path / "state.db"))
    app.dependency_overrides[get_preview_repository] = lambda: PreviewRepository(str(tmp_path / "state.db"))
    app.dependency_overrides[get_preview_audit_repository] = lambda: audit_repository
    client = TestClient(app)

    try:
        response = client.post(
            "/api/upload/preview",
            json={"rangeMode": "custom", "sources": ["plc"]},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    page = audit_repository.list_audit_logs(AuditLogFilters(action="upload.preview"))
    assert page.total_items == 1
    row = page.rows[0]
    params = decode_params_json(row["params_json_redacted"])
    assert row["result"] == "failure"
    assert row["error_code"] == "preview_request_validation_failed"
    assert params["reasonCode"] == "preview_request_validation_failed"
    assert params["rejectedFields"] == ["endDate", "startDate"]


def test_upload_preview_create_invalid_json_writes_failure_audit(tmp_path) -> None:
    audit_repository = AuditRepository(str(tmp_path / "state.db"))
    app.dependency_overrides[get_preview_repository] = lambda: PreviewRepository(str(tmp_path / "state.db"))
    app.dependency_overrides[get_preview_audit_repository] = lambda: audit_repository
    client = TestClient(app)

    try:
        response = client.post(
            "/api/upload/preview",
            content=b'{"rangeMode": ',
            headers={"Content-Type": "application/json"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["detail"]["reason"] == "preview_request_json_invalid"
    row = audit_repository.list_audit_logs(AuditLogFilters(action="upload.preview")).rows[0]
    params = decode_params_json(row["params_json_redacted"])
    assert row["result"] == "failure"
    assert row["error_code"] == "preview_request_json_invalid"
    assert params["reasonCode"] == "preview_request_json_invalid"
    assert params["rejectedFields"] == []
    assert '{"rangeMode": ' not in row["params_json_redacted"]


def test_upload_preview_create_auto_applies_large_source_budget_for_operational_plc_source(
    tmp_path,
    monkeypatch,
) -> None:
    repository = PreviewRepository(str(tmp_path / "state.db"))
    audit_repository = AuditRepository(str(tmp_path / "state.db"))
    settings = Settings(state_db_path=str(tmp_path / "state.db"), plc_data_dir="//operator-share/plc")
    submitted: list[tuple[str, object]] = []
    monkeypatch.setattr(
        upload_preview_api.executor,
        "submit",
        lambda fn, preview_run_id, request: (
            submitted.append((preview_run_id, request)) or pending_future()
        ),
    )
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_preview_repository] = lambda: repository
    app.dependency_overrides[get_preview_audit_repository] = lambda: audit_repository
    client = TestClient(app)

    try:
        response = client.post(
            "/api/upload/preview",
            json={
                "rangeMode": "last_2_days",
                "sources": ["plc"],
                "options": {
                    "profile": "default",
                    "chunkRows": 20000,
                    "maxRunSeconds": 120,
                    "maxFileSeconds": 30,
                },
                "approvalScope": approval_scope(
                    source_class="network",
                    range_mode="last_2_days",
                    applied_profile="large_source_operational",
                ),
            },
        )
        detail_response = client.get(f"/api/upload/preview/{response.json()['previewRunId']}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 202
    assert detail_response.status_code == 200
    preview_run_id = response.json()["previewRunId"]
    row = repository.get_run(preview_run_id)
    assert row is not None
    options = json.loads(row["options_json"])
    assert options["profile"] == "large_source_operational"
    assert options["chunkRows"] == 1000
    assert options["maxRunSeconds"] == 900
    assert options["maxFileSeconds"] == 300
    run = detail_response.json()["run"]
    assert run["requestedProfile"] == "default"
    assert run["appliedProfile"] == "large_source_operational"
    assert run["autoProfileReason"] == "operational_source_class"
    assert submitted[0][1].options.profile.value == "large_source_operational"


def test_upload_preview_create_preserves_explicit_bounded_profile_for_operational_plc_source(
    tmp_path,
    monkeypatch,
) -> None:
    repository = PreviewRepository(str(tmp_path / "state.db"))
    audit_repository = AuditRepository(str(tmp_path / "state.db"))
    settings = Settings(state_db_path=str(tmp_path / "state.db"), plc_data_dir="//operator-share/plc")
    monkeypatch.setattr(upload_preview_api.executor, "submit", lambda *_args, **_kwargs: pending_future())
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_preview_repository] = lambda: repository
    app.dependency_overrides[get_preview_audit_repository] = lambda: audit_repository
    client = TestClient(app)

    try:
        response = client.post(
            "/api/upload/preview",
            json={
                "rangeMode": "custom",
                "startDate": "2026-05-23",
                "endDate": "2026-05-23",
                "sources": ["plc"],
                "options": {"profile": "stage3_profile_a_bounded_full_scan"},
                "approvalScope": approval_scope(
                    source_class="network",
                    range_mode="custom",
                    start_date="2026-05-23",
                    end_date="2026-05-23",
                    applied_profile="stage3_profile_a_bounded_full_scan",
                ),
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 202
    row = repository.get_run(response.json()["previewRunId"])
    assert row is not None
    options = json.loads(row["options_json"])
    assert options["profile"] == "stage3_profile_a_bounded_full_scan"
    assert options["maxFiles"] == 3
    assert options["maxRunSeconds"] == 300
    assert options["maxFileSeconds"] == 120


def test_upload_preview_create_auto_applies_large_source_budget_for_large_date_range(
    tmp_path,
    monkeypatch,
) -> None:
    repository = PreviewRepository(str(tmp_path / "state.db"))
    audit_repository = AuditRepository(str(tmp_path / "state.db"))
    settings = Settings(state_db_path=str(tmp_path / "state.db"), plc_data_dir="local-plc")
    monkeypatch.setattr(upload_preview_api.executor, "submit", lambda *_args, **_kwargs: pending_future())
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_preview_repository] = lambda: repository
    app.dependency_overrides[get_preview_audit_repository] = lambda: audit_repository
    client = TestClient(app)

    try:
        response = client.post(
            "/api/upload/preview",
            json={
                "rangeMode": "custom",
                "startDate": "2026-01-01",
                "endDate": "2026-01-02",
                "sources": ["plc"],
                "options": {"profile": "default"},
                "approvalScope": approval_scope(
                    range_mode="custom",
                    start_date="2026-01-01",
                    end_date="2026-01-02",
                    applied_profile="large_source_operational",
                ),
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 202
    row = repository.get_run(response.json()["previewRunId"])
    assert row is not None
    options = json.loads(row["options_json"])
    assert options["profile"] == "large_source_operational"
    assert options["chunkRows"] == 1000
    assert options["maxRunSeconds"] == 900
    assert options["maxFileSeconds"] == 300


def test_upload_preview_create_auto_applies_large_source_budget_for_folder_all(
    tmp_path,
    monkeypatch,
) -> None:
    repository = PreviewRepository(str(tmp_path / "state.db"))
    audit_repository = AuditRepository(str(tmp_path / "state.db"))
    settings = Settings(state_db_path=str(tmp_path / "state.db"), plc_data_dir="local-plc")
    monkeypatch.setattr(upload_preview_api.executor, "submit", lambda *_args, **_kwargs: pending_future())
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_preview_repository] = lambda: repository
    app.dependency_overrides[get_preview_audit_repository] = lambda: audit_repository
    client = TestClient(app)

    try:
        response = client.post(
            "/api/upload/preview",
            json={
                "rangeMode": "folder_all",
                "sources": ["plc"],
                "options": {"profile": "default"},
                "approvalScope": approval_scope(
                    range_mode="folder_all",
                    applied_profile="large_source_operational",
                ),
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 202
    row = repository.get_run(response.json()["previewRunId"])
    assert row is not None
    assert row["range_mode"] == "folder_all"
    assert row["start_date"] is None
    assert row["end_date"] is None
    options = json.loads(row["options_json"])
    assert options["profile"] == "large_source_operational"
    assert options["maxRunSeconds"] == 900
    assert options["maxFileSeconds"] == 300


def test_upload_preview_create_keeps_default_budget_for_small_local_source(
    tmp_path,
    monkeypatch,
) -> None:
    repository = PreviewRepository(str(tmp_path / "state.db"))
    audit_repository = AuditRepository(str(tmp_path / "state.db"))
    settings = Settings(state_db_path=str(tmp_path / "state.db"), plc_data_dir="local-plc")
    monkeypatch.setattr(upload_preview_api.executor, "submit", lambda *_args, **_kwargs: pending_future())
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_preview_repository] = lambda: repository
    app.dependency_overrides[get_preview_audit_repository] = lambda: audit_repository
    client = TestClient(app)

    try:
        response = client.post(
            "/api/upload/preview",
            json={
                "rangeMode": "today",
                "sources": ["plc"],
                "options": {"profile": "default"},
                "approvalScope": approval_scope(),
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 202
    row = repository.get_run(response.json()["previewRunId"])
    assert row is not None
    options = json.loads(row["options_json"])
    assert options["profile"] == "default"
    assert options["maxRunSeconds"] == 120
    assert options["maxFileSeconds"] == 30


def test_upload_preview_create_rejects_new_range_mode_scope_mismatch_before_run_creation(
    tmp_path,
) -> None:
    repository = PreviewRepository(str(tmp_path / "state.db"))
    audit_repository = AuditRepository(str(tmp_path / "state.db"))
    settings = Settings(state_db_path=str(tmp_path / "state.db"), plc_data_dir="local-plc")
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_preview_repository] = lambda: repository
    app.dependency_overrides[get_preview_audit_repository] = lambda: audit_repository
    client = TestClient(app)

    try:
        response = client.post(
            "/api/upload/preview",
            json={
                "rangeMode": "folder_all",
                "sources": ["plc"],
                "options": {"profile": "default"},
                "approvalScope": approval_scope(
                    range_mode="last_30_days",
                    applied_profile="large_source_operational",
                ),
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["reason"] == "preview_approval_scope_mismatch"
    assert detail["mismatchFields"] == ["rangeMode"]
    assert repository.get_latest_run() is None
    row = audit_repository.list_audit_logs(AuditLogFilters(action="upload.preview")).rows[0]
    params = decode_params_json(row["params_json_redacted"])
    assert row["result"] == "blocked"
    assert params["approvalScope"]["expected"]["rangeMode"] == "last_30_days"
    assert params["approvalScope"]["actual"]["rangeMode"] == "folder_all"


def test_upload_preview_create_rejects_missing_approval_scope_before_run_creation(tmp_path) -> None:
    repository = PreviewRepository(str(tmp_path / "state.db"))
    audit_repository = AuditRepository(str(tmp_path / "state.db"))
    settings = Settings(state_db_path=str(tmp_path / "state.db"), plc_data_dir="local-plc")
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_preview_repository] = lambda: repository
    app.dependency_overrides[get_preview_audit_repository] = lambda: audit_repository
    client = TestClient(app)

    try:
        response = client.post(
            "/api/upload/preview",
            json={"rangeMode": "today", "sources": ["plc"], "options": {"profile": "default"}},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["detail"]["reason"] == "preview_approval_scope_required"
    assert repository.get_latest_run() is None
    row = audit_repository.list_audit_logs(AuditLogFilters(action="upload.preview")).rows[0]
    params = decode_params_json(row["params_json_redacted"])
    assert row["result"] == "blocked"
    assert row["error_code"] == "preview_approval_scope_required"
    assert params["reasonCode"] == "preview_approval_scope_required"
    assert params["approvalScope"]["actual"]["sourceClasses"] == {"plc": "local"}
    assert params["approvalScope"]["mismatchFields"] == ["approvalScope"]


def test_upload_preview_create_rejects_approval_scope_mismatch_before_run_creation(tmp_path) -> None:
    repository = PreviewRepository(str(tmp_path / "state.db"))
    audit_repository = AuditRepository(str(tmp_path / "state.db"))
    settings = Settings(state_db_path=str(tmp_path / "state.db"), plc_data_dir="//operator-share/plc")
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_preview_repository] = lambda: repository
    app.dependency_overrides[get_preview_audit_repository] = lambda: audit_repository
    client = TestClient(app)

    try:
        response = client.post(
            "/api/upload/preview",
            json={
                "rangeMode": "today",
                "sources": ["plc"],
                "options": {"profile": "default"},
                "approvalScope": approval_scope(
                    source_class="drive_letter",
                    range_mode="today",
                    applied_profile="default",
                ),
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["reason"] == "preview_approval_scope_mismatch"
    assert set(detail["mismatchFields"]) == {"sourceClasses", "appliedProfile"}
    assert repository.get_latest_run() is None
    row = audit_repository.list_audit_logs(AuditLogFilters(action="upload.preview")).rows[0]
    params = decode_params_json(row["params_json_redacted"])
    assert row["result"] == "blocked"
    assert params["approvalScope"]["expected"]["sourceClasses"] == {"plc": "drive_letter"}
    assert params["approvalScope"]["actual"]["sourceClasses"] == {"plc": "network"}
    assert params["approvalScope"]["actual"]["appliedProfile"] == "large_source_operational"
    assert "operator-share" not in row["params_json_redacted"]


def test_upload_preview_delete_is_not_a_v1_api() -> None:
    client = TestClient(app)

    response = client.delete("/api/upload/preview/prv_20260601_000001")

    assert response.status_code == 405


def test_upload_preview_latest_returns_persisted_run_details(tmp_path) -> None:
    repository = PreviewRepository(str(tmp_path / "state.db"))
    repository.create_run(
        preview_run_id="prv_latest",
        range_mode="today",
        start_date=None,
        end_date=None,
        sources=["plc"],
        options={},
        config_snapshot={},
        retry_of_run_id=None,
    )
    repository.insert_item(
        "prv_latest",
        {
            "file_key": "PLC/Factory_Integrated_Log_20260601_090000.csv",
            "folder_label": "PLC",
            "folder_path": "C:\\data\\plc",
            "filename": "Factory_Integrated_Log_20260601_090000.csv",
            "path": "C:\\data\\plc\\Factory_Integrated_Log_20260601_090000.csv",
            "kind": "plc",
            "file_date": "2026-06-01",
            "size_bytes": 100,
            "mtime_ns": 1,
            "modified_at": "2026-06-01T09:00:00+09:00",
            "file_signature": "sig",
            "status": "risky",
            "reason_code": "db_unreachable",
            "reason_text": "Local Supabase DB could not be reached.",
            "scan_mode": "full",
            "sample_row_count": 2,
            "row_count": 2,
            "local_key_count": 2,
            "db_match_count": None,
            "upload_row_estimate": 0,
            "first_timestamp": "2026-06-01T09:00:00+09:00",
            "last_timestamp": "2026-06-01T09:01:00+09:00",
            "device_ids": ["extruder_integrated"],
            "issues": ["db_unreachable"],
            "timeout_stage": "db_match",
            "timing": {"extractMs": 7, "dbProgress": {"strategy": "temp_table"}},
            "error_code": "db_unreachable",
            "error_message": "Local Supabase DB could not be reached.",
        },
    )
    repository.recompute_summary(
        "prv_latest",
        status=PreviewRunStatus.partial_failed,
        db_status=PreviewDbStatus.unreachable,
        error_code="db_unreachable",
        error_message="Local Supabase DB could not be reached.",
        timeout_stage="db_match",
        timing={"scanMs": 3, "timeoutStage": "db_match"},
    )
    app.dependency_overrides[get_preview_repository] = lambda: repository
    client = TestClient(app)

    try:
        response = client.get("/api/upload/preview/latest")
        filtered_response = client.get("/api/upload/preview/latest?status=target")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["run"]["previewRunId"] == "prv_latest"
    assert payload["run"]["status"] == "partial_failed"
    assert payload["run"]["dbStatus"] == "unreachable"
    assert payload["items"][0]["status"] == "risky"
    assert payload["items"][0]["reasonCode"] == "db_unreachable"
    assert payload["run"]["timeoutStage"] == "db_match"
    assert payload["run"]["timing"]["scanMs"] == 3
    assert payload["items"][0]["timeoutStage"] == "db_match"
    assert payload["items"][0]["timing"]["dbProgress"]["strategy"] == "temp_table"

    assert filtered_response.status_code == 200
    filtered_payload = filtered_response.json()
    assert filtered_payload["run"]["previewRunId"] == "prv_latest"
    assert filtered_payload["items"] == []
    assert filtered_payload["page"]["totalItems"] == 0


def test_upload_preview_summary_separates_target_and_partial_rows(tmp_path) -> None:
    repository = PreviewRepository(str(tmp_path / "state.db"))
    repository.create_run(
        preview_run_id="prv_rows",
        range_mode="today",
        start_date=None,
        end_date=None,
        sources=["plc"],
        options={},
        config_snapshot={},
        retry_of_run_id=None,
    )
    base_item = {
        "folder_label": "PLC",
        "folder_path": "C:\\data\\plc",
        "kind": "plc",
        "file_date": "2026-06-01",
        "size_bytes": 100,
        "mtime_ns": 1,
        "modified_at": "2026-06-01T09:00:00+09:00",
        "file_signature": "sig",
        "reason_text": "test",
        "scan_mode": "full",
        "sample_row_count": 1,
        "row_count": 1,
        "local_key_count": 1,
        "db_match_count": 0,
        "first_timestamp": "2026-06-01T09:00:00+09:00",
        "last_timestamp": "2026-06-01T09:00:00+09:00",
        "device_ids": ["extruder_plc"],
        "issues": [],
        "error_code": None,
        "error_message": None,
    }
    for status_name, upload_rows in (("target", 2), ("partial_overlap", 5), ("already_in_db", 0)):
        repository.insert_item(
            "prv_rows",
            {
                **base_item,
                "file_key": f"key-{status_name}",
                "filename": f"{status_name}.csv",
                "path": f"C:\\data\\plc\\{status_name}.csv",
                "status": status_name,
                "reason_code": "db_no_match" if status_name == "target" else "db_partial_match",
                "upload_row_estimate": upload_rows,
            },
        )
    repository.recompute_summary(
        "prv_rows",
        status=PreviewRunStatus.succeeded,
        db_status=PreviewDbStatus.reachable,
    )
    app.dependency_overrides[get_preview_repository] = lambda: repository
    client = TestClient(app)

    try:
        response = client.get("/api/upload/preview/prv_rows")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    summary = response.json()["run"]["summary"]
    assert summary["uploadRows"] == 7
    assert summary["targetRows"] == 2
    assert summary["partialOverlapRows"] == 5


def test_upload_preview_conflict_returns_active_run_location(tmp_path) -> None:
    repository = PreviewRepository(str(tmp_path / "state.db"))
    audit_repository = AuditRepository(str(tmp_path / "state.db"))
    settings = Settings(state_db_path=str(tmp_path / "state.db"), plc_data_dir="local-plc")
    repository.create_run(
        preview_run_id="prv_active",
        range_mode="today",
        start_date=None,
        end_date=None,
        sources=["plc"],
        options={},
        config_snapshot={},
        retry_of_run_id=None,
    )
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_preview_repository] = lambda: repository
    app.dependency_overrides[get_preview_audit_repository] = lambda: audit_repository
    client = TestClient(app)

    try:
        response = client.post(
            "/api/upload/preview",
            json={
                "rangeMode": "today",
                "sources": ["plc"],
                "approvalScope": approval_scope(),
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.headers["location"] == "/api/upload/preview/prv_active"
    assert response.json()["detail"]["activePreviewRunId"] == "prv_active"
    row = audit_repository.list_audit_logs(AuditLogFilters(action="upload.preview")).rows[0]
    assert row["result"] == "blocked"
    assert row["error_code"] == "active_preview_run"


def test_upload_preview_submit_failure_reconciles_run_and_returns_safe_503(
    tmp_path,
    monkeypatch,
    caplog,
) -> None:
    repository = PreviewRepository(str(tmp_path / "state.db"))
    audit_repository = AuditRepository(str(tmp_path / "state.db"))
    settings = Settings(state_db_path=str(tmp_path / "state.db"), plc_data_dir="local-plc")
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_preview_repository] = lambda: repository
    app.dependency_overrides[get_preview_audit_repository] = lambda: audit_repository

    def reject_submission(*_args, **_kwargs):
        raise RuntimeError("sensitive-preview-submit-detail")

    monkeypatch.setattr(upload_preview_api.executor, "submit", reject_submission)
    client = TestClient(app)
    try:
        response = client.post(
            "/api/upload/preview",
            json={
                "rangeMode": "today",
                "sources": ["plc"],
                "approvalScope": approval_scope(),
            },
        )
    finally:
        app.dependency_overrides.clear()

    detail = response.json()["detail"]
    preview_run_id = detail["previewRunId"]
    run = repository.get_run(preview_run_id)
    audit = audit_repository.list_audit_logs(AuditLogFilters(action="upload.preview")).rows[0]
    assert response.status_code == 503
    assert detail == {
        "reason": "preview_worker_unavailable",
        "previewRunId": preview_run_id,
        "restartRequired": True,
        "recovery": upload_preview_api.PREVIEW_WORKER_RETRY_RECOVERY,
    }
    assert response.headers["location"] == f"/api/upload/preview/{preview_run_id}"
    assert run is not None
    assert run["status"] == "failed"
    assert run["error_code"] == "preview_worker_unavailable"
    assert "sensitive-preview-submit-detail" not in run["error_message"]
    assert repository.has_active_run() is None
    assert audit["result"] == "failure"
    assert audit["error_code"] == "preview_worker_unavailable"
    assert "sensitive-preview-submit-detail" not in audit["error_message"]
    assert "sensitive-preview-submit-detail" not in caplog.text


def test_upload_preview_submit_audit_failure_rolls_back_run_and_recovers_on_startup(
    tmp_path,
    monkeypatch,
    caplog,
) -> None:
    repository = PreviewRepository(str(tmp_path / "state.db"))
    audit_repository = AuditRepository(str(tmp_path / "state.db"))
    settings = Settings(state_db_path=str(tmp_path / "state.db"), plc_data_dir="local-plc")
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_preview_repository] = lambda: repository
    app.dependency_overrides[get_preview_audit_repository] = lambda: audit_repository

    def reject_submission(*_args, **_kwargs):
        raise RuntimeError("sensitive-submit-detail")

    def reject_audit_insert(*_args, **_kwargs):
        raise RuntimeError("sensitive-reconciliation-detail")

    monkeypatch.setattr(upload_preview_api.executor, "submit", reject_submission)
    monkeypatch.setattr(
        AuditRepository,
        "insert_audit_in_transaction",
        reject_audit_insert,
    )
    client = TestClient(app)
    try:
        response = client.post(
            "/api/upload/preview",
            json={
                "rangeMode": "today",
                "sources": ["plc"],
                "approvalScope": approval_scope(),
            },
        )
    finally:
        app.dependency_overrides.clear()

    detail = response.json()["detail"]
    preview_run_id = detail["previewRunId"]
    assert response.status_code == 503
    assert detail == {
        "reason": "preview_worker_reconciliation_failed",
        "previewRunId": preview_run_id,
        "restartRequired": True,
        "recovery": upload_preview_api.PREVIEW_WORKER_RESTART_RECOVERY,
    }
    assert response.headers["location"] == f"/api/upload/preview/{preview_run_id}"
    assert repository.get_run(preview_run_id)["status"] == "queued"
    assert repository.has_active_run() == preview_run_id
    assert audit_repository.list_audit_logs(AuditLogFilters(action="upload.preview")).total_items == 0
    assert "sensitive-submit-detail" not in caplog.text
    assert "sensitive-reconciliation-detail" not in caplog.text

    assert repository.mark_interrupted_active_runs() == 1
    assert repository.has_active_run() is None
    assert repository.get_run(preview_run_id)["status"] == "failed"


def test_upload_preview_observes_async_finalization_failure_and_requires_restart(
    tmp_path,
    monkeypatch,
    caplog,
) -> None:
    repository = PreviewRepository(str(tmp_path / "state.db"))
    audit_repository = AuditRepository(str(tmp_path / "state.db"))
    settings = Settings(
        state_db_path=str(tmp_path / "state.db"),
        plc_data_dir=str(tmp_path / "missing-source"),
    )
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_preview_repository] = lambda: repository
    app.dependency_overrides[get_preview_audit_repository] = lambda: audit_repository

    def reject_audit_insert(*_args, **_kwargs):
        raise RuntimeError("sensitive-async-audit-detail")

    monkeypatch.setattr(upload_preview_api.executor, "submit", run_in_future)
    monkeypatch.setattr(
        AuditRepository,
        "insert_audit_in_transaction",
        reject_audit_insert,
    )
    client = TestClient(app)
    try:
        response = client.post(
            "/api/upload/preview",
            json={
                "rangeMode": "today",
                "sources": ["plc"],
                "approvalScope": approval_scope(
                    source_class="drive_letter",
                    applied_profile="large_source_operational",
                ),
            },
        )
    finally:
        app.dependency_overrides.clear()

    preview_run_id = response.json()["previewRunId"]
    run = repository.get_run(preview_run_id)
    assert response.status_code == 202
    assert run is not None
    assert run["status"] == "running"
    assert repository.has_active_run() == preview_run_id
    assert audit_repository.list_audit_logs(AuditLogFilters(action="upload.preview")).total_items == 0
    assert "restart_required=true" in caplog.text
    assert "error_type=RuntimeError" in caplog.text
    assert "sensitive-async-audit-detail" not in caplog.text

    assert repository.mark_interrupted_active_runs() == 1
    assert repository.has_active_run() is None
    assert repository.get_run(preview_run_id)["status"] == "failed"


def test_upload_preview_future_observer_sanitizes_repository_read_failure(
    tmp_path,
    monkeypatch,
    caplog,
) -> None:
    repository = PreviewRepository(str(tmp_path / "state.db"))
    audit_repository = AuditRepository(str(tmp_path / "state.db"))
    settings = Settings(state_db_path=str(tmp_path / "state.db"), plc_data_dir="local-plc")
    request = upload_preview_api.PreviewCreateRequest.model_validate(
        {"rangeMode": "today", "sources": ["plc"]}
    )
    service = upload_preview_api.PreviewService(
        settings,
        repository,
        audit_repository=audit_repository,
    )
    future: Future[None] = Future()
    future.set_exception(RuntimeError("sensitive-worker-detail"))

    def reject_run_read(*_args, **_kwargs):
        raise RuntimeError("postgresql://operator:secret-token@localhost/state")

    monkeypatch.setattr(repository, "get_run", reject_run_read)

    upload_preview_api._observe_preview_future("prv_abc123def456", request, service, future)

    assert "restart_required=true" in caplog.text
    assert "error_type=RuntimeError" in caplog.text
    assert "reconciliation_error_type=RuntimeError" in caplog.text
    assert "sensitive-worker-detail" not in caplog.text
    assert "secret-token" not in caplog.text
    assert "postgresql://" not in caplog.text


def test_upload_preview_transient_audit_failure_persists_only_safe_fallback(
    tmp_path,
    monkeypatch,
    caplog,
) -> None:
    repository = PreviewRepository(str(tmp_path / "state.db"))
    audit_repository = AuditRepository(str(tmp_path / "state.db"))
    settings = Settings(
        state_db_path=str(tmp_path / "state.db"),
        plc_data_dir=str(tmp_path / "missing-source"),
    )
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_preview_repository] = lambda: repository
    app.dependency_overrides[get_preview_audit_repository] = lambda: audit_repository
    original_insert = AuditRepository.insert_audit_in_transaction
    calls = 0

    def fail_once(self, connection, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("postgresql://operator:secret-token@localhost/internal-state")
        return original_insert(self, connection, **kwargs)

    monkeypatch.setattr(upload_preview_api.executor, "submit", run_in_future)
    monkeypatch.setattr(AuditRepository, "insert_audit_in_transaction", fail_once)
    client = TestClient(app)
    try:
        response = client.post(
            "/api/upload/preview",
            json={
                "rangeMode": "today",
                "sources": ["plc"],
                "approvalScope": approval_scope(
                    source_class="drive_letter",
                    applied_profile="large_source_operational",
                ),
            },
        )
        detail = client.get(response.json()["pollUrl"])
    finally:
        app.dependency_overrides.clear()

    preview_run_id = response.json()["previewRunId"]
    run = detail.json()["run"]
    audit = audit_repository.list_audit_logs(AuditLogFilters(action="upload.preview")).rows[0]
    serialized = detail.text + str(dict(audit)) + caplog.text
    assert response.status_code == 202
    assert detail.status_code == 200
    assert calls == 2
    assert run["previewRunId"] == preview_run_id
    assert run["status"] == "failed"
    assert run["errorCode"] == "preview_failed"
    assert run["errorMessage"] == PREVIEW_FAILED_MESSAGE
    assert audit["error_code"] == "preview_failed"
    assert "secret-token" not in serialized
    assert "postgresql://" not in serialized


def test_upload_preview_callback_reconciles_accepted_worker_as_preview_failed(
    tmp_path,
    monkeypatch,
    caplog,
) -> None:
    repository = PreviewRepository(str(tmp_path / "state.db"))
    audit_repository = AuditRepository(str(tmp_path / "state.db"))
    settings = Settings(
        state_db_path=str(tmp_path / "state.db"),
        plc_data_dir=str(tmp_path / "missing-source"),
    )
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_preview_repository] = lambda: repository
    app.dependency_overrides[get_preview_audit_repository] = lambda: audit_repository
    original_insert = AuditRepository.insert_audit_in_transaction
    calls = 0

    def fail_twice(self, connection, **kwargs):
        nonlocal calls
        calls += 1
        if calls <= 2:
            raise RuntimeError("postgresql://operator:secret-token@localhost/internal-state")
        return original_insert(self, connection, **kwargs)

    monkeypatch.setattr(upload_preview_api.executor, "submit", run_in_future)
    monkeypatch.setattr(AuditRepository, "insert_audit_in_transaction", fail_twice)
    client = TestClient(app)
    try:
        response = client.post(
            "/api/upload/preview",
            json={
                "rangeMode": "today",
                "sources": ["plc"],
                "approvalScope": approval_scope(
                    source_class="drive_letter",
                    applied_profile="large_source_operational",
                ),
            },
        )
        detail = client.get(response.json()["pollUrl"])
    finally:
        app.dependency_overrides.clear()

    run = detail.json()["run"]
    audits = audit_repository.list_audit_logs(AuditLogFilters(action="upload.preview"))
    serialized = detail.text + str([dict(row) for row in audits.rows]) + caplog.text
    assert response.status_code == 202
    assert detail.status_code == 200
    assert calls == 3
    assert run["status"] == "failed"
    assert run["errorCode"] == "preview_failed"
    assert run["errorMessage"] == PREVIEW_FAILED_MESSAGE
    assert audits.total_items == 1
    assert audits.rows[0]["error_code"] == "preview_failed"
    assert "preview_worker_unavailable" not in serialized
    assert "secret-token" not in serialized
    assert "postgresql://" not in serialized


def test_upload_preview_audit_rows_are_queryable_through_audit_api(tmp_path) -> None:
    audit_repository = AuditRepository(str(tmp_path / "state.db"))
    audit_repository.insert_audit(
        action="upload.preview",
        target_type="preview_run",
        target_id="prv_queryable",
        params={
            "previewRunId": "prv_queryable",
            "candidateCount": 1,
            "targetCount": 1,
            "alreadyInDbCount": 0,
            "partialOverlapCount": 0,
            "riskyCount": 0,
            "excludedCount": 0,
            "dbStatus": "reachable",
            "reasonCode": None,
            "requestedFilters": {"rangeMode": "today", "sources": ["plc"], "optionKeys": []},
        },
        result="success",
    )
    app.dependency_overrides[get_audit_repository] = lambda: audit_repository
    client = TestClient(app)

    try:
        response = client.get("/api/audit?action=upload.preview")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["page"]["totalItems"] == 1
    assert payload["items"][0]["action"] == "upload.preview"
    assert payload["items"][0]["targetId"] == "prv_queryable"


def test_upload_preview_rejects_invalid_list_query_params(tmp_path) -> None:
    repository = PreviewRepository(str(tmp_path / "state.db"))
    repository.create_run(
        preview_run_id="prv_latest",
        range_mode="today",
        start_date=None,
        end_date=None,
        sources=["plc"],
        options={},
        config_snapshot={},
        retry_of_run_id=None,
    )
    app.dependency_overrides[get_preview_repository] = lambda: repository
    client = TestClient(app)

    try:
        response = client.get("/api/upload/preview/latest?status=not_a_status")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
