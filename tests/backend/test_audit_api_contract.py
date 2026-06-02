from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.api.audit import get_audit_repository
from backend.app.db.audit_repository import AuditRepository
from backend.app.main import app
from backend.app.schemas.audit import AuditResult


def test_audit_route_is_registered_in_openapi() -> None:
    client = TestClient(app)

    response = client.get("/api/openapi.json")

    assert response.status_code == 200
    assert "/api/audit" in response.json()["paths"]


def test_audit_api_returns_paginated_redacted_audit_logs(tmp_path: Path) -> None:
    repository = AuditRepository(tmp_path / "state.db")
    repository.insert_audit(
        action="upload.start",
        target_type="upload_job",
        target_id="upl_1",
        params={"token": "secret-token", "mode": "preview_targets"},
        result=AuditResult.blocked,
        error_code="active_upload_job",
        error_message="Authorization: Bearer abc.def.ghi",
        job_id="upl_1",
        request_id="req_1",
    )
    repository.insert_audit(
        action="runtime.start",
        target_type="local_supabase",
        target_id="Extrusion_data",
        params={"operationId": "run_1"},
        result=AuditResult.success,
    )
    app.dependency_overrides[get_audit_repository] = lambda: repository
    client = TestClient(app)

    try:
        response = client.get("/api/audit?result=blocked&limit=1")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["page"] == {"limit": 1, "offset": 0, "totalItems": 1, "hasNext": False, "hasPrevious": False}
    assert body["filters"]["result"] == "blocked"
    item = body["items"][0]
    assert item["auditId"] > 0
    assert item["targetType"] == "upload_job"
    assert item["jobId"] == "upl_1"
    assert item["params"]["token"] == "[redacted]"
    assert "params_json_redacted" not in item
    assert item["errorMessage"] == "Authorization: Bearer [redacted]"


def test_audit_api_filters_searches_safe_scalars_and_rejects_invalid_params(tmp_path: Path) -> None:
    repository = AuditRepository(tmp_path / "state.db")
    repository.insert_audit(
        action="upload.start",
        target_type="upload_job",
        target_id="upl_1",
        params={"hidden": "needle"},
        result=AuditResult.blocked,
        error_code="active_upload_job",
        job_id="upl_1",
        request_id="req_1",
    )
    app.dependency_overrides[get_audit_repository] = lambda: repository
    client = TestClient(app)

    try:
        assert client.get("/api/audit?q=needle").json()["page"]["totalItems"] == 0
        assert client.get("/api/audit?q=active_upload_job").json()["page"]["totalItems"] == 1
        assert client.get("/api/audit?jobId=upl_1&requestId=req_1").json()["page"]["totalItems"] == 1
        assert client.get("/api/audit?sort=rawSql").status_code == 422
        assert client.get("/api/audit?result=unknown").status_code == 422
        assert client.get("/api/audit?limit=201").status_code == 422
    finally:
        app.dependency_overrides.clear()
