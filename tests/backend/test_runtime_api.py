from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.api.runtime import get_command_runner, get_runtime_service
from backend.app.core.settings import Settings, get_settings
from backend.app.main import app, create_app
from backend.app.schemas.runtime import (
    RuntimeContainerStatus,
    RuntimeOverallStatus,
    RuntimePortStatus,
    RuntimeProbeStatus,
    RuntimeServiceStatus,
    RuntimeStatusResponse,
)
from tests.backend.test_runtime_control import FakeRunner, write_supabase_config


def test_runtime_routes_are_registered_in_openapi(monkeypatch) -> None:
    monkeypatch.setenv("EWC_API_DOCS_MODE", "enabled")
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.get("/api/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/runtime/local-supabase" in paths
    assert "/api/runtime/local-supabase/start" in paths
    assert "/api/runtime/local-supabase/stop" in paths
    assert "/api/runtime/operations/{operationId}" in paths
    get_settings.cache_clear()


def test_runtime_status_returns_graceful_blocked_state_without_docker(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    project_path = tmp_path / "Extrusion_web_console"
    write_supabase_config(project_path)
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


def test_runtime_status_serializes_vector_container_as_non_required(tmp_path: Path) -> None:
    checked_at = datetime(2026, 6, 22, 9, 0, tzinfo=timezone.utc)

    class StaticRuntimeService:
        def status(self) -> RuntimeStatusResponse:
            return RuntimeStatusResponse(
                overall_status=RuntimeOverallStatus.attention,
                reason_code="non_core_runtime_attention",
                reason_text="Core runtime is reachable, but non-core Grafana or Vector needs attention.",
                checked_at=checked_at,
                project_path=str(tmp_path / "runtime"),
                project_id="Extrusion_web_console",
                docker=RuntimeProbeStatus(name="Docker", status=RuntimeServiceStatus.ready, detail="ready"),
                wsl=RuntimeProbeStatus(name="WSL", status=RuntimeServiceStatus.ready, detail="ready"),
                supabase_cli=RuntimeProbeStatus(name="Supabase CLI", status=RuntimeServiceStatus.ready, detail="ready"),
                api=RuntimePortStatus(name="Supabase API", port=55321, status=RuntimeServiceStatus.ready, detail="ready"),
                db=RuntimePortStatus(name="Supabase DB", port=25433, status=RuntimeServiceStatus.ready, detail="ready"),
                studio=RuntimePortStatus(name="Supabase Studio", port=55323, status=RuntimeServiceStatus.ready, detail="ready"),
                edge_runtime=RuntimeProbeStatus(name="Edge Function", status=RuntimeServiceStatus.ready, detail="ready"),
                grafana=RuntimeProbeStatus(name="Grafana", status=RuntimeServiceStatus.ready, detail="ready"),
                vector=RuntimeProbeStatus(name="Vector", status=RuntimeServiceStatus.missing, detail="Vector container status class is missing."),
                containers=[
                    RuntimeContainerStatus(
                        name="supabase_vector_Extrusion_web_console",
                        required=False,
                        exists=False,
                        running=False,
                        status=RuntimeServiceStatus.missing,
                    )
                ],
                config=[],
            )

    app.dependency_overrides[get_runtime_service] = lambda: StaticRuntimeService()
    client = TestClient(app)

    try:
        response = client.get("/api/runtime/local-supabase")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    vector_container = next(item for item in payload["containers"] if item["name"] == "supabase_vector_Extrusion_web_console")
    assert vector_container["required"] is False
    assert vector_container["status"] == "missing"


def test_runtime_start_blocks_active_preview_via_api(tmp_path: Path) -> None:
    from backend.app.db.preview_repository import PreviewRepository

    db_path = tmp_path / "state.db"
    project_path = tmp_path / "Extrusion_web_console"
    write_supabase_config(project_path)
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
