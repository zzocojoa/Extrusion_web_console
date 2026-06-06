from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.core.settings import get_settings
from backend.app.main import create_app


def _client_with_dist(
    tmp_path: Path,
    monkeypatch,
    dist_exists: bool = True,
    *,
    api_docs_mode: str | None = None,
    local_token_mode: str | None = None,
) -> TestClient:
    state_db_path = tmp_path / "state.db"
    config_path = tmp_path / "config.json"
    dist_path = tmp_path / "dist"
    monkeypatch.setenv("EWC_STATE_DB_PATH", str(state_db_path))
    monkeypatch.setenv("EWC_CONFIG_FILE_PATH", str(config_path))
    monkeypatch.setenv("EWC_FRONTEND_DIST_PATH", str(dist_path))
    if api_docs_mode is None:
        monkeypatch.delenv("EWC_API_DOCS_MODE", raising=False)
    else:
        monkeypatch.setenv("EWC_API_DOCS_MODE", api_docs_mode)
    if local_token_mode is None:
        monkeypatch.delenv("EWC_LOCAL_TOKEN_MODE", raising=False)
    else:
        monkeypatch.setenv("EWC_LOCAL_TOKEN_MODE", local_token_mode)
    if dist_exists:
        assets_path = dist_path / "assets"
        assets_path.mkdir(parents=True)
        (dist_path / "index.html").write_text(
            '<!doctype html><html><head><script type="module" src="/assets/app.js"></script></head><body>web console shell</body></html>',
            encoding="utf-8",
        )
        (assets_path / "app.js").write_text("console.log('app shell');", encoding="utf-8")
    get_settings.cache_clear()
    app = create_app()
    return TestClient(app)


def test_static_frontend_serves_root_routes_and_assets(tmp_path: Path, monkeypatch) -> None:
    client = _client_with_dist(tmp_path, monkeypatch)

    for route in ["/", "/upload", "/logs", "/settings"]:
        response = client.get(route)
        assert response.status_code == 200
        assert "web console shell" in response.text

    asset_response = client.get("/assets/app.js")
    assert asset_response.status_code == 200
    assert "app shell" in asset_response.text

    get_settings.cache_clear()


def test_api_routes_keep_precedence_over_static_fallback(tmp_path: Path, monkeypatch) -> None:
    client = _client_with_dist(tmp_path, monkeypatch)

    health_response = client.get("/api/health")
    assert health_response.status_code == 200
    assert health_response.headers["content-type"].startswith("application/json")

    audit_response = client.get("/api/audit?action=settings.save&limit=1")
    assert audit_response.status_code == 200
    assert audit_response.headers["content-type"].startswith("application/json")

    missing_api_response = client.get("/api/not-a-real-route")
    assert missing_api_response.status_code == 404
    assert "web console shell" not in missing_api_response.text

    get_settings.cache_clear()


def test_operator_api_docs_routes_are_disabled_without_spa_fallback(tmp_path: Path, monkeypatch) -> None:
    client = _client_with_dist(tmp_path, monkeypatch, api_docs_mode="disabled", local_token_mode="required")

    for route in ["/api/docs", "/api/openapi.json", "/api/redoc"]:
        response = client.get(route)
        assert response.status_code == 404
        assert response.headers["content-type"].startswith("application/json")
        assert "web console shell" not in response.text

    assert client.get("/api/health").status_code == 200
    assert client.get("/api/config").status_code == 200
    assert client.get("/api/audit").status_code == 200
    assert client.get("/").status_code == 200

    get_settings.cache_clear()


def test_dev_api_docs_routes_are_enabled(tmp_path: Path, monkeypatch) -> None:
    client = _client_with_dist(tmp_path, monkeypatch, api_docs_mode="enabled", local_token_mode="dev-disabled")

    docs_response = client.get("/api/docs")
    openapi_response = client.get("/api/openapi.json")
    redoc_response = client.get("/api/redoc")

    assert docs_response.status_code == 200
    assert openapi_response.status_code == 200
    assert "/api/health" in openapi_response.json()["paths"]
    assert redoc_response.status_code == 404

    get_settings.cache_clear()


def test_missing_frontend_build_returns_operator_message(tmp_path: Path, monkeypatch) -> None:
    client = _client_with_dist(tmp_path, monkeypatch, dist_exists=False)

    response = client.get("/")

    assert response.status_code == 503
    assert response.json()["detail"].startswith("Frontend build is missing")

    get_settings.cache_clear()


def test_frontend_index_injects_runtime_token_without_mutating_dist(tmp_path: Path, monkeypatch) -> None:
    client = _client_with_dist(tmp_path, monkeypatch)
    monkeypatch.setenv("EWC_LOCAL_TOKEN_MODE", "required")
    monkeypatch.setenv("EWC_LOCAL_API_TOKEN", "fixture-local-guard-value")
    get_settings.cache_clear()

    response = client.get("/")
    index_path = tmp_path / "dist" / "index.html"

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert "window.__EWC_BOOTSTRAP__" in response.text
    assert "localApiToken" in response.text
    assert "fixture-local-guard-value" in response.text
    assert "fixture-local-guard-value" not in index_path.read_text(encoding="utf-8")

    get_settings.cache_clear()
