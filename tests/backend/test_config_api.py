import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.api.config import get_config_audit_repository
from backend.app.api.audit import get_audit_repository
from backend.app.core.settings import Settings, get_settings
from backend.app.db.audit_repository import AuditLogFilters, AuditRepository, decode_params_json
from backend.app.main import app
from backend.app.schemas.audit import AuditResult


CONFIG_ENV_KEYS = (
    "EWC_PLC_DATA_DIR",
    "EWC_TEMPERATURE_DATA_DIR",
    "EWC_SUPABASE_DB_URL",
    "EWC_SUPABASE_URL",
    "EWC_SUPABASE_ANON_KEY",
    "EWC_SUPABASE_EDGE_URL",
    "EWC_GRAFANA_URL",
    "EWC_LOCAL_SUPABASE_PROJECT_PATH",
    "EWC_LOCAL_SUPABASE_WSL_PATH",
    "EWC_LOCAL_SUPABASE_PROJECT_ID",
    "EWC_LOCAL_SUPABASE_API_PORT",
    "EWC_LOCAL_SUPABASE_DB_PORT",
    "EWC_LOCAL_SUPABASE_STUDIO_PORT",
    "EWC_RUNTIME_COMMAND_TIMEOUT_SECONDS",
    "EWC_RUNTIME_READINESS_TIMEOUT_SECONDS",
)


def _clear_config_env(monkeypatch) -> None:
    for key in CONFIG_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def _client(tmp_path: Path, **settings_overrides):
    db_path = tmp_path / "state.db"
    config_path = tmp_path / "config.json"
    settings = Settings(state_db_path=str(db_path), config_file_path=str(config_path), **settings_overrides)
    audit_repository = AuditRepository(db_path)
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_config_audit_repository] = lambda: audit_repository
    app.dependency_overrides[get_audit_repository] = lambda: audit_repository
    return TestClient(app), audit_repository, config_path


def _clear_overrides() -> None:
    app.dependency_overrides.clear()


def test_config_save_success_writes_settings_save_audit_without_raw_values(tmp_path: Path, monkeypatch) -> None:
    _clear_config_env(monkeypatch)
    client, audit_repository, config_path = _client(tmp_path)

    try:
        response = client.put(
            "/api/config",
            json={
                "values": {
                    "grafanaUrl": "http://localhost:4000",
                    "localSupabaseApiPort": 54322,
                    "supabaseAnonKey": "Authorization: Bearer secret-token",
                }
            },
        )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    assert response.json()["savedKeys"] == ["grafanaUrl", "localSupabaseApiPort", "supabaseAnonKey"]
    saved = json.loads(config_path.read_text(encoding="utf-8"))
    assert saved["grafanaUrl"] == "http://localhost:4000"
    assert saved["localSupabaseApiPort"] == 54322
    assert saved["supabaseAnonKey"] == "Authorization: Bearer secret-token"

    page = audit_repository.list_audit_logs(AuditLogFilters(action="settings.save"))
    assert page.total_items == 1
    row = page.rows[0]
    assert row["result"] == AuditResult.success.value
    params = decode_params_json(row["params_json_redacted"])
    assert params["savedSettings"] == ["grafanaUrl", "localSupabaseApiPort", "supabaseAnonKey"]
    assert "secret-token" not in row["params_json_redacted"]


def test_config_save_validation_failure_writes_failure_audit(tmp_path: Path, monkeypatch) -> None:
    _clear_config_env(monkeypatch)
    client, audit_repository, config_path = _client(tmp_path)

    try:
        response = client.put("/api/config", json={"values": {"localSupabaseApiPort": 70000}})
    finally:
        _clear_overrides()

    assert response.status_code == 422
    assert response.json()["detail"]["reason"] == "config_validation_failed"
    assert not config_path.exists()
    page = audit_repository.list_audit_logs(AuditLogFilters(action="settings.save"))
    assert page.total_items == 1
    row = page.rows[0]
    assert row["result"] == AuditResult.failure.value
    assert row["error_code"] == "config_validation_failed"
    assert decode_params_json(row["params_json_redacted"])["rejectedSettings"] == ["localSupabaseApiPort"]


def test_config_save_env_override_is_blocked_and_audited(tmp_path: Path, monkeypatch) -> None:
    _clear_config_env(monkeypatch)
    monkeypatch.setenv("EWC_GRAFANA_URL", "http://env.example")
    client, audit_repository, config_path = _client(tmp_path)

    try:
        response = client.put("/api/config", json={"values": {"grafanaUrl": "http://localhost:4000"}})
    finally:
        _clear_overrides()

    assert response.status_code == 409
    assert response.json()["detail"]["reason"] == "config_env_override"
    assert not config_path.exists()
    page = audit_repository.list_audit_logs(AuditLogFilters(action="settings.save"))
    assert page.total_items == 1
    row = page.rows[0]
    assert row["result"] == AuditResult.blocked.value
    assert row["error_code"] == "config_env_override"
    assert decode_params_json(row["params_json_redacted"])["rejectedSettings"] == ["grafanaUrl"]


def test_config_get_hides_secret_values_and_reports_sources(tmp_path: Path, monkeypatch) -> None:
    _clear_config_env(monkeypatch)
    monkeypatch.setenv("EWC_GRAFANA_URL", "http://env.example")
    client, _, config_path = _client(tmp_path)
    config_path.write_text(
        json.dumps(
            {
                "plcDataDir": "C:/data/plc",
                "supabaseAnonKey": "secret-token",
            }
        ),
        encoding="utf-8",
    )

    try:
        response = client.get("/api/config")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    items = {item["key"]: item for item in response.json()["items"]}
    assert items["plcDataDir"]["source"] == "config"
    assert items["plcDataDir"]["value"] == "C:/data/plc"
    assert items["supabaseAnonKey"]["source"] == "config"
    assert items["supabaseAnonKey"]["value"] is None
    assert items["grafanaUrl"]["source"] == "env"
    assert items["grafanaUrl"]["overridden"] is True


def test_config_save_is_queryable_through_audit_api(tmp_path: Path, monkeypatch) -> None:
    _clear_config_env(monkeypatch)
    client, _, _ = _client(tmp_path)

    try:
        save_response = client.put("/api/config", json={"values": {"plcDataDir": "C:/data/plc"}})
        audit_response = client.get("/api/audit?action=settings.save")
    finally:
        _clear_overrides()

    assert save_response.status_code == 200
    assert audit_response.status_code == 200
    body = audit_response.json()
    assert body["page"]["totalItems"] == 1
    assert body["items"][0]["action"] == "settings.save"
    assert body["items"][0]["params"]["savedSettings"] == ["plcDataDir"]
