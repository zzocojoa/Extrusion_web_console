from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.api.runtime import get_command_runner
from backend.app.core.settings import Settings, get_settings
from backend.app.main import app
from tests.backend.test_runtime_control import FakeRunner


def test_runtime_routes_are_registered_in_openapi() -> None:
    client = TestClient(app)

    response = client.get("/api/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/runtime/local-supabase" in paths
    assert "/api/runtime/local-supabase/start" in paths
    assert "/api/runtime/local-supabase/stop" in paths
    assert "/api/runtime/operations/{operationId}" in paths


def test_runtime_status_returns_graceful_blocked_state_without_docker(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    project_path = tmp_path / "Extrusion_data"
    project_path.mkdir()
    app.dependency_overrides[get_settings] = lambda: Settings(
        state_db_path=str(db_path),
        local_supabase_project_path=str(project_path),
        supabase_edge_url="",
    )
    app.dependency_overrides[get_command_runner] = lambda: FakeRunner(docker_ps_output="")
    client = TestClient(app)

    try:
        response = client.get("/api/runtime/local-supabase")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["overallStatus"] == "blocked"
    assert payload["reasonCode"] == "required_container_missing"
    assert any(item["status"] == "missing" for item in payload["containers"])


def test_runtime_start_blocks_active_preview_via_api(tmp_path: Path) -> None:
    from backend.app.db.preview_repository import PreviewRepository

    db_path = tmp_path / "state.db"
    project_path = tmp_path / "Extrusion_data"
    project_path.mkdir()
    preview = PreviewRepository(db_path)
    preview.create_run(
        preview_run_id="prv_active",
        range_mode="today",
        start_date=None,
        end_date=None,
        sources=["plc"],
        options={},
        config_snapshot={},
        retry_of_run_id=None,
    )
    app.dependency_overrides[get_settings] = lambda: Settings(
        state_db_path=str(db_path),
        local_supabase_project_path=str(project_path),
        supabase_edge_url="",
    )
    app.dependency_overrides[get_command_runner] = lambda: FakeRunner()
    client = TestClient(app)

    try:
        response = client.post("/api/runtime/local-supabase/start")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json()["detail"]["reason"] == "active_preview_run"
