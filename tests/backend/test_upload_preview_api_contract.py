from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.api.audit import get_audit_repository
from backend.app.api.upload_preview import get_preview_audit_repository, get_preview_repository
from backend.app.db.audit_repository import AuditLogFilters, AuditRepository, decode_params_json
from backend.app.db.preview_repository import PreviewRepository
from backend.app.core.settings import get_settings
from backend.app.main import app, create_app
from backend.app.schemas.upload_preview import PreviewDbStatus, PreviewRunStatus


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
    get_settings.cache_clear()


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


def test_upload_preview_conflict_returns_active_run_location(tmp_path) -> None:
    repository = PreviewRepository(str(tmp_path / "state.db"))
    audit_repository = AuditRepository(str(tmp_path / "state.db"))
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
    app.dependency_overrides[get_preview_repository] = lambda: repository
    app.dependency_overrides[get_preview_audit_repository] = lambda: audit_repository
    client = TestClient(app)

    try:
        response = client.post(
            "/api/upload/preview",
            json={"rangeMode": "today", "sources": ["plc"]},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.headers["location"] == "/api/upload/preview/prv_active"
    assert response.json()["detail"]["activePreviewRunId"] == "prv_active"
    row = audit_repository.list_audit_logs(AuditLogFilters(action="upload.preview")).rows[0]
    assert row["result"] == "blocked"
    assert row["error_code"] == "active_preview_run"


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
