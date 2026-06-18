from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.core.local_token import LOCAL_TOKEN_HEADER
from backend.app.core.local_token import _LAST_AUDIT_BY_BUCKET
from backend.app.core.settings import get_settings
from backend.app.db.audit_repository import AuditLogFilters, AuditRepository, decode_params_json
from backend.app.main import create_app


LOCAL_GUARD_VALUE = "fixture-local-guard-value"


def _client(tmp_path: Path, monkeypatch, *, mode: str = "required", guard_value: str = LOCAL_GUARD_VALUE) -> tuple[TestClient, AuditRepository]:
    monkeypatch.setenv("EWC_STATE_DB_PATH", str(tmp_path / "state.db"))
    monkeypatch.setenv("EWC_CONFIG_FILE_PATH", str(tmp_path / "config.json"))
    monkeypatch.setenv("EWC_FRONTEND_DIST_PATH", str(tmp_path / "dist"))
    monkeypatch.setenv("EWC_LOCAL_TOKEN_MODE", mode)
    if guard_value:
        monkeypatch.setenv("EWC_LOCAL_API_TOKEN", guard_value)
    else:
        monkeypatch.delenv("EWC_LOCAL_API_TOKEN", raising=False)
    _LAST_AUDIT_BY_BUCKET.clear()
    get_settings.cache_clear()
    app = create_app()
    return TestClient(app), AuditRepository(tmp_path / "state.db")


def test_mutating_api_missing_token_is_blocked_and_audited(tmp_path: Path, monkeypatch) -> None:
    client, audit_repository = _client(tmp_path, monkeypatch)

    response = client.put("/api/config", json={"values": {"grafanaUrl": "http://127.0.0.1:3001"}})

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "local_token_required"
    page = audit_repository.list_audit_logs(AuditLogFilters(action="settings.save"))
    assert page.total_items == 1
    row = page.rows[0]
    assert row["result"] == "blocked"
    assert row["error_code"] == "local_token_missing"
    params = decode_params_json(row["params_json_redacted"])
    assert params == {
        "method": "PUT",
        "reasonCode": "local_token_missing",
        "routeGroup": "config",
        "sourceHost": "loopback",
        "tokenPresent": False,
    }
    assert LOCAL_GUARD_VALUE not in row["params_json_redacted"]
    get_settings.cache_clear()


def test_mutating_api_invalid_token_is_blocked(tmp_path: Path, monkeypatch) -> None:
    client, audit_repository = _client(tmp_path, monkeypatch)

    response = client.put(
        "/api/config",
        json={"values": {"grafanaUrl": "http://127.0.0.1:3001"}},
        headers={LOCAL_TOKEN_HEADER: "wrong-local-guard-value"},
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "local_token_required"
    row = audit_repository.list_audit_logs(AuditLogFilters(action="settings.save")).rows[0]
    assert row["error_code"] == "local_token_invalid"
    params = decode_params_json(row["params_json_redacted"])
    assert params["tokenPresent"] is True
    assert "wrong-local-guard-value" not in row["params_json_redacted"]
    get_settings.cache_clear()


def test_mutating_api_valid_token_proceeds(tmp_path: Path, monkeypatch) -> None:
    client, _ = _client(tmp_path, monkeypatch)

    response = client.put(
        "/api/config",
        json={"values": {"grafanaUrl": "http://127.0.0.1:3001"}},
        headers={LOCAL_TOKEN_HEADER: LOCAL_GUARD_VALUE},
    )

    assert response.status_code == 200
    assert response.json()["savedKeys"] == ["grafanaUrl"]
    get_settings.cache_clear()


def test_read_only_and_options_do_not_require_token(tmp_path: Path, monkeypatch) -> None:
    client, _ = _client(tmp_path, monkeypatch)

    assert client.get("/api/health").status_code == 200
    assert client.get("/api/config").status_code == 200
    assert client.get("/api/audit").status_code == 200
    assert client.get("/api/docs").status_code == 404
    assert client.get("/api/openapi.json").status_code == 404
    assert client.options("/api/config").status_code != 403
    get_settings.cache_clear()


def test_protected_route_groups_block_without_token(tmp_path: Path, monkeypatch) -> None:
    client, audit_repository = _client(tmp_path, monkeypatch)

    protected_requests = [
        ("POST", "/api/upload/preview"),
        ("POST", "/api/upload/delete/preflight"),
        ("POST", "/api/upload/delete/jobs"),
        ("POST", "/api/upload/delete/jobs/del_fixture/reconcile"),
        ("POST", "/api/upload/jobs"),
        ("POST", "/api/upload/jobs/job_fixture/retry"),
        ("POST", "/api/upload/jobs/job_fixture/pause"),
        ("POST", "/api/upload/jobs/job_fixture/resume"),
        ("POST", "/api/upload/jobs/job_fixture/cancel"),
        ("POST", "/api/runtime/local-supabase/start"),
        ("POST", "/api/runtime/local-supabase/stop"),
        ("POST", "/api/not-a-real-route"),
    ]

    for method, path in protected_requests:
        response = client.request(method, path, json={})
        assert response.status_code == 403, path
        assert response.json()["detail"]["code"] == "local_token_required"

    actions = {row["action"] for row in audit_repository.list_audit_logs(AuditLogFilters()).rows}
    assert {
        "upload.preview",
        "upload.delete_preflight",
        "upload.delete_start",
        "upload.delete_reconciled",
        "upload.start",
        "upload.retry",
        "upload.pause",
        "upload.resume",
        "upload.cancel",
        "runtime.start",
        "runtime.stop",
        "local.token",
    }.issubset(actions)
    get_settings.cache_clear()


def test_runtime_token_failure_uses_configured_project_id_target(tmp_path: Path, monkeypatch) -> None:
    client, audit_repository = _client(tmp_path, monkeypatch)

    response = client.post("/api/runtime/local-supabase/start", json={})

    assert response.status_code == 403
    row = audit_repository.list_audit_logs(AuditLogFilters(action="runtime.start")).rows[0]
    assert row["target_id"] == "Extrusion_web_console"
    get_settings.cache_clear()


def test_repeated_missing_token_audit_is_rate_limited(tmp_path: Path, monkeypatch) -> None:
    client, audit_repository = _client(tmp_path, monkeypatch)

    for _ in range(3):
        response = client.put("/api/config", json={"values": {"grafanaUrl": "http://127.0.0.1:3001"}})
        assert response.status_code == 403

    assert audit_repository.list_audit_logs(AuditLogFilters(action="settings.save")).total_items == 1
    get_settings.cache_clear()


def test_dev_disabled_mode_allows_existing_mutating_flow_without_token(tmp_path: Path, monkeypatch) -> None:
    client, _ = _client(tmp_path, monkeypatch, mode="dev-disabled", guard_value="")

    response = client.put("/api/config", json={"values": {"grafanaUrl": "http://127.0.0.1:3001"}})

    assert response.status_code == 200
    get_settings.cache_clear()


def test_future_unknown_mutating_api_requires_token_by_default(tmp_path: Path, monkeypatch) -> None:
    client, _ = _client(tmp_path, monkeypatch)

    missing_response = client.post("/api/future-mutating-route")
    valid_response = client.post("/api/future-mutating-route", headers={LOCAL_TOKEN_HEADER: LOCAL_GUARD_VALUE})

    assert missing_response.status_code == 403
    assert valid_response.status_code != 403
    get_settings.cache_clear()
