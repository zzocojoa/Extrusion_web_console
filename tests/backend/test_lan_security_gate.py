from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.core.lan_security import lan_security_state
from backend.app.core.settings import Settings, get_settings
from backend.app.main import create_app


def _set_isolated_app_env(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("EWC_STATE_DB_PATH", str(tmp_path / "state.db"))
    monkeypatch.setenv("EWC_CONFIG_FILE_PATH", str(tmp_path / "config.json"))
    monkeypatch.setenv("EWC_FRONTEND_DIST_PATH", str(tmp_path / "dist"))
    monkeypatch.delenv("EWC_HOST", raising=False)
    monkeypatch.delenv("EWC_V2_LAN_ACCESS_ENABLED", raising=False)
    get_settings.cache_clear()


def test_lan_gate_reports_default_off_localhost_only(tmp_path: Path, monkeypatch) -> None:
    _set_isolated_app_env(tmp_path, monkeypatch)

    client = TestClient(create_app())
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["localhost_only"] is True
    assert body["lan_security"]["enabled"] is False
    assert body["lan_security"]["status"] == "localhost_only"
    assert body["lan_security"]["bind_host_class"] == "loopback"
    assert body["lan_security"]["shared_local_token_allowed"] is False
    assert body["lan_security"]["reasons"] == []
    get_settings.cache_clear()


def test_lan_gate_rejects_non_loopback_bind_when_disabled(tmp_path: Path, monkeypatch) -> None:
    _set_isolated_app_env(tmp_path, monkeypatch)
    monkeypatch.setenv("EWC_HOST", "0.0.0.0")
    get_settings.cache_clear()

    with pytest.raises(RuntimeError, match="lan_gate_disabled_non_loopback_configured_host"):
        create_app()
    get_settings.cache_clear()


def test_lan_gate_rejects_enablement_without_auth_session_and_concurrency(
    tmp_path: Path, monkeypatch
) -> None:
    _set_isolated_app_env(tmp_path, monkeypatch)
    monkeypatch.setenv("EWC_V2_LAN_ACCESS_ENABLED", "true")
    get_settings.cache_clear()

    with pytest.raises(RuntimeError) as exc_info:
        create_app()

    message = str(exc_info.value)
    assert "lan_auth_not_implemented" in message
    assert "lan_actor_session_not_implemented" in message
    assert "lan_concurrency_not_implemented" in message
    get_settings.cache_clear()


def test_lan_gate_blocks_non_loopback_cors_when_disabled() -> None:
    settings = Settings(cors_origins=("http://192.0.2.10:8000",))

    state = lan_security_state(settings)

    assert state.status == "blocked"
    assert state.cors_origin_classes == ("non_loopback_origin",)
    assert state.reasons == ("lan_gate_disabled_non_loopback_cors",)
    assert "192.0.2.10" not in " ".join(state.reasons)


def test_non_loopback_client_is_blocked_by_default(tmp_path: Path, monkeypatch) -> None:
    _set_isolated_app_env(tmp_path, monkeypatch)

    client = TestClient(create_app(), client=("192.0.2.10", 50000))
    response = client.get("/api/health")

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Extrusion Web Console LAN access is blocked until the LAN security gate is approved."
    )
    get_settings.cache_clear()


def test_non_loopback_request_server_is_blocked_by_default(tmp_path: Path, monkeypatch) -> None:
    _set_isolated_app_env(tmp_path, monkeypatch)

    client = TestClient(create_app(), base_url="http://192.0.2.10")
    response = client.get("/api/health")

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Extrusion Web Console LAN bind is blocked until the LAN security gate is approved."
    )
    get_settings.cache_clear()
