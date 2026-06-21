import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.api.config import get_config_audit_repository
from backend.app.api.audit import get_audit_repository
from backend.app.core.settings import Settings, get_settings
from backend.app.db.audit_repository import AuditLogFilters, AuditRepository, decode_params_json
from backend.app.main import app
from backend.app.schemas.audit import AuditResult
from backend.app.services.config_service import ConfigService


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
    "EWC_V2_DELETE_EXPANSION_ENABLED",
    "EWC_V2_DATE_SCOPED_DELETE_UI_ENABLED",
    "EWC_V2_LAN_ACCESS_ENABLED",
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
    monkeypatch.chdir(tmp_path)
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
    monkeypatch.chdir(tmp_path)
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


def test_config_save_malformed_json_body_writes_failure_audit(tmp_path: Path, monkeypatch) -> None:
    _clear_config_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    client, audit_repository, config_path = _client(tmp_path)

    try:
        response = client.put(
            "/api/config",
            content=b'{"values": ',
            headers={"Content-Type": "application/json"},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 422
    assert response.json()["detail"]["reason"] == "config_request_json_invalid"
    assert not config_path.exists()
    row = audit_repository.list_audit_logs(AuditLogFilters(action="settings.save")).rows[0]
    assert row["result"] == AuditResult.failure.value
    assert row["error_code"] == "config_request_json_invalid"
    params = decode_params_json(row["params_json_redacted"])
    assert params["validationReason"] == "config_request_json_invalid"
    assert params["rejectedSettings"] == []
    assert '{"values": ' not in row["params_json_redacted"]


def test_config_save_malformed_values_request_writes_failure_audit(tmp_path: Path, monkeypatch) -> None:
    _clear_config_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    client, audit_repository, config_path = _client(tmp_path)

    try:
        response = client.put("/api/config", json={"values": []})
    finally:
        _clear_overrides()

    assert response.status_code == 422
    assert response.json()["detail"]["reason"] == "config_request_validation_failed"
    assert not config_path.exists()
    row = audit_repository.list_audit_logs(AuditLogFilters(action="settings.save")).rows[0]
    assert row["result"] == AuditResult.failure.value
    assert row["error_code"] == "config_request_validation_failed"
    params = decode_params_json(row["params_json_redacted"])
    assert params["validationReason"] == "config_request_validation_failed"
    assert params["rejectedSettings"] == ["values"]


def test_config_save_actor_validation_writes_failure_audit(tmp_path: Path, monkeypatch) -> None:
    _clear_config_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    client, audit_repository, config_path = _client(tmp_path)

    try:
        response = client.put("/api/config", json={"actor": "", "values": {"plcDataDir": "C:/data/plc"}})
    finally:
        _clear_overrides()

    assert response.status_code == 422
    assert not config_path.exists()
    row = audit_repository.list_audit_logs(AuditLogFilters(action="settings.save")).rows[0]
    assert row["error_code"] == "config_request_validation_failed"
    assert decode_params_json(row["params_json_redacted"])["rejectedSettings"] == ["actor"]


def test_config_save_actor_type_validation_writes_failure_audit(tmp_path: Path, monkeypatch) -> None:
    _clear_config_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    client, audit_repository, config_path = _client(tmp_path)

    try:
        response = client.put("/api/config", json={"actor": ["local_operator"], "values": {"plcDataDir": "C:/data/plc"}})
    finally:
        _clear_overrides()

    assert response.status_code == 422
    assert not config_path.exists()
    row = audit_repository.list_audit_logs(AuditLogFilters(action="settings.save")).rows[0]
    assert row["error_code"] == "config_request_validation_failed"
    assert decode_params_json(row["params_json_redacted"])["rejectedSettings"] == ["actor"]


def test_config_save_extra_field_validation_writes_failure_audit(tmp_path: Path, monkeypatch) -> None:
    _clear_config_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    client, audit_repository, config_path = _client(tmp_path)

    try:
        response = client.put("/api/config", json={"values": {"plcDataDir": "C:/data/plc"}, "unexpected": "secret-token"})
    finally:
        _clear_overrides()

    assert response.status_code == 422
    assert not config_path.exists()
    row = audit_repository.list_audit_logs(AuditLogFilters(action="settings.save")).rows[0]
    params = decode_params_json(row["params_json_redacted"])
    assert row["error_code"] == "config_request_validation_failed"
    assert params["rejectedSettings"] == ["unexpected"]
    assert "secret-token" not in row["params_json_redacted"]


def test_config_save_env_override_is_blocked_and_audited(tmp_path: Path, monkeypatch) -> None:
    _clear_config_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
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


def test_config_save_dotenv_override_is_blocked_and_audited(tmp_path: Path, monkeypatch) -> None:
    _clear_config_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("EWC_GRAFANA_URL=http://dotenv.example\n", encoding="utf-8")
    client, audit_repository, config_path = _client(tmp_path)

    try:
        get_response = client.get("/api/config")
        save_response = client.put("/api/config", json={"values": {"grafanaUrl": "http://localhost:4000"}})
    finally:
        _clear_overrides()

    items = {item["key"]: item for item in get_response.json()["items"]}
    assert get_response.status_code == 200
    assert items["grafanaUrl"]["source"] == "env"
    assert items["grafanaUrl"]["overridden"] is True
    assert save_response.status_code == 409
    assert save_response.json()["detail"]["reason"] == "config_env_override"
    assert not config_path.exists()
    row = audit_repository.list_audit_logs(AuditLogFilters(action="settings.save")).rows[0]
    assert row["result"] == AuditResult.blocked.value
    assert row["error_code"] == "config_env_override"
    assert decode_params_json(row["params_json_redacted"])["rejectedSettings"] == ["grafanaUrl"]


def test_saved_config_json_is_loaded_by_new_settings_instance(tmp_path: Path, monkeypatch) -> None:
    _clear_config_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    client, _, config_path = _client(tmp_path)

    try:
        response = client.put(
            "/api/config",
            json={"values": {"grafanaUrl": "http://localhost:4000", "localSupabaseApiPort": 54322}},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    monkeypatch.setenv("EWC_CONFIG_FILE_PATH", str(config_path))
    loaded = Settings()
    assert loaded.grafana_url == "http://localhost:4000"
    assert loaded.local_supabase_api_port == 54322
    assert loaded.upload_edge_url == "http://127.0.0.1:54322/functions/v1/upload-metrics"


def test_config_save_clears_cached_settings_for_next_request(tmp_path: Path, monkeypatch) -> None:
    _clear_config_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    config_path = tmp_path / "config.json"
    db_path = tmp_path / "state.db"
    monkeypatch.setenv("EWC_CONFIG_FILE_PATH", str(config_path))
    get_settings.cache_clear()
    cached_before = get_settings()
    assert cached_before.grafana_url == "http://localhost:3001"

    service = ConfigService(cached_before, AuditRepository(db_path))
    response = service.save_config({"grafanaUrl": "http://localhost:4000"}, actor="local_operator")

    cached_after = get_settings()
    assert response.saved_keys == ["grafanaUrl"]
    assert cached_after.grafana_url == "http://localhost:4000"
    assert cached_after is not cached_before
    get_settings.cache_clear()


def test_environment_overrides_saved_config_json(tmp_path: Path, monkeypatch) -> None:
    _clear_config_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"grafanaUrl": "http://config.example"}), encoding="utf-8")
    monkeypatch.setenv("EWC_CONFIG_FILE_PATH", str(config_path))
    monkeypatch.setenv("EWC_GRAFANA_URL", "http://env.example")

    loaded = Settings()

    assert loaded.grafana_url == "http://env.example"


def test_config_get_hides_secret_values_and_reports_sources(tmp_path: Path, monkeypatch) -> None:
    _clear_config_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
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


def test_config_get_exposes_v2_feature_gates_default_off_and_read_only(tmp_path: Path, monkeypatch) -> None:
    _clear_config_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    client, _, _ = _client(tmp_path)

    try:
        response = client.get("/api/config")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    body = response.json()
    date_gate = body["featureGates"]["v2DateScopedDeleteUi"]
    assert date_gate == {
        "key": "v2_date_scoped_delete_ui_enabled",
        "enabled": False,
        "reviewShellVisible": False,
        "source": "default",
        "mutable": False,
        "requiredRole": "maintainer",
        "status": "hidden",
        "reason": "date_scoped_delete_ui_gate_default_off",
    }
    assert body["featureGates"]["v2DeleteExpansion"]["enabled"] is False
    assert body["featureGates"]["v2LanAccess"]["enabled"] is False
    assert "v2DateScopedDeleteUiEnabled" not in {item["key"] for item in body["items"]}


def test_config_get_reports_env_enabled_date_scoped_delete_review_shell_without_settings_item(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _clear_config_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("EWC_V2_DATE_SCOPED_DELETE_UI_ENABLED", "true")
    client, _, _ = _client(tmp_path)

    try:
        response = client.get("/api/config")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    body = response.json()
    gate = body["featureGates"]["v2DateScopedDeleteUi"]
    assert gate["enabled"] is False
    assert gate["reviewShellVisible"] is True
    assert gate["source"] == "env"
    assert gate["mutable"] is False
    assert gate["requiredRole"] == "maintainer"
    assert gate["status"] == "review_shell_visible"
    assert gate["reason"] == "date_scoped_delete_ui_review_shell_visible"
    assert "v2DateScopedDeleteUiEnabled" not in {item["key"] for item in body["items"]}


def test_config_get_reports_env_requested_lan_gate_as_blocked_until_lan_is_implemented(tmp_path: Path, monkeypatch) -> None:
    _clear_config_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("EWC_V2_LAN_ACCESS_ENABLED", "true")
    client, _, _ = _client(tmp_path)

    try:
        response = client.get("/api/config")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    gate = response.json()["featureGates"]["v2LanAccess"]
    assert gate["enabled"] is False
    assert gate["reviewShellVisible"] is False
    assert gate["source"] == "env"
    assert gate["mutable"] is False
    assert gate["requiredRole"] == "admin"
    assert gate["status"] == "blocked_not_implemented"
    assert gate["reason"] == "lan_access_not_implemented"


def test_config_save_cannot_enable_date_scoped_delete_gate(tmp_path: Path, monkeypatch) -> None:
    _clear_config_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    client, audit_repository, config_path = _client(tmp_path)

    try:
        response = client.put("/api/config", json={"values": {"v2DateScopedDeleteUiEnabled": True}})
    finally:
        _clear_overrides()

    assert response.status_code == 422
    assert response.json()["detail"]["reason"] == "config_unknown_key"
    assert response.json()["detail"]["keys"] == ["v2DateScopedDeleteUiEnabled"]
    assert not config_path.exists()
    row = audit_repository.list_audit_logs(AuditLogFilters(action="settings.save")).rows[0]
    assert row["result"] == AuditResult.failure.value
    assert row["error_code"] == "config_unknown_key"
    assert decode_params_json(row["params_json_redacted"])["rejectedSettings"] == ["v2DateScopedDeleteUiEnabled"]


def test_config_get_uses_independent_local_supabase_defaults(tmp_path: Path, monkeypatch) -> None:
    _clear_config_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    client, _, _ = _client(tmp_path, supabase_db_url="", supabase_url="", supabase_edge_url="")

    try:
        response = client.get("/api/config")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    items = {item["key"]: item for item in response.json()["items"]}
    assert items["localSupabaseProjectId"]["value"] == "Extrusion_web_console"
    assert items["localSupabaseApiPort"]["value"] == 55321
    assert items["localSupabaseDbPort"]["value"] == 25433
    assert items["localSupabaseStudioPort"]["value"] == 55323
    assert items["supabaseUrl"]["value"] == ""
    target_classes = response.json()["targetClasses"]
    assert target_classes["status"] == "passed"
    assert target_classes["reason"] == "target_class_preflight_passed"
    assert target_classes["uploadRuntimeAligned"] is True
    assert target_classes["uploadEdge"]["targetClass"] == "loopback_expected_api_port_upload_metrics"
    assert target_classes["runtimeEdge"]["targetClass"] == "loopback_expected_api_port_upload_metrics"
    assert target_classes["db"]["targetClass"] == "not_configured"
    state_context = response.json()["stateContext"]
    assert state_context["contextClass"] == "qa_temporary"
    assert state_context["storageStatus"] == "present"
    assert str(tmp_path / "state.db") not in response.text


def test_config_get_keeps_empty_plc_default_without_launcher_fallback(tmp_path: Path, monkeypatch) -> None:
    _clear_config_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    client, _, _ = _client(tmp_path, plc_data_dir="")

    try:
        response = client.get("/api/config")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    items = {item["key"]: item for item in response.json()["items"]}
    assert items["plcDataDir"]["source"] == "default"
    assert items["plcDataDir"]["overridden"] is False
    assert items["plcDataDir"]["value"] == ""


def test_settings_preserves_explicit_env_plc_source(tmp_path: Path, monkeypatch) -> None:
    _clear_config_env(monkeypatch)
    explicit_source = "//nas/share/plc"
    monkeypatch.setenv("EWC_PLC_DATA_DIR", explicit_source)

    settings = Settings(_env_file=None)

    assert settings.plc_data_dir == explicit_source


def test_config_get_preserves_explicit_config_plc_source(tmp_path: Path, monkeypatch) -> None:
    _clear_config_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    client, _, config_path = _client(tmp_path)
    explicit_source = "//nas/share/plc"
    config_path.write_text(json.dumps({"plcDataDir": explicit_source}), encoding="utf-8")

    try:
        response = client.get("/api/config")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    items = {item["key"]: item for item in response.json()["items"]}
    assert items["plcDataDir"]["source"] == "config"
    assert items["plcDataDir"]["overridden"] is False
    assert items["plcDataDir"]["value"] == explicit_source


def test_config_get_reports_stale_upload_target_class_without_raw_secret(tmp_path: Path, monkeypatch) -> None:
    _clear_config_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    db_url = "postgres" + "ql://postgres:postgres@127.0.0.1:25432/postgres"
    client, _, _ = _client(
        tmp_path,
        local_supabase_api_port=55321,
        local_supabase_db_port=25433,
        supabase_url="http://127.0.0.1:54321",
        supabase_edge_url="",
        supabase_db_url=db_url,
    )

    try:
        response = client.get("/api/config")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    body_text = response.text
    target_classes = response.json()["targetClasses"]
    assert target_classes["status"] == "blocked"
    assert target_classes["reason"] == "edge_target_class_mismatch"
    assert target_classes["uploadRuntimeAligned"] is False
    assert target_classes["uploadEdge"]["targetClass"] == "loopback_unexpected_port_upload_metrics"
    assert target_classes["runtimeEdge"]["targetClass"] == "loopback_expected_api_port_upload_metrics"
    assert target_classes["db"]["targetClass"] == "loopback_unexpected_port"
    assert ("postgres" + "ql://") not in body_text
    assert "postgres:postgres" not in body_text


def test_config_save_is_queryable_through_audit_api(tmp_path: Path, monkeypatch) -> None:
    _clear_config_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
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
