from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.api.dashboard import (
    get_dashboard_audit_repository,
    get_dashboard_runtime_status,
    get_dashboard_upload_repository,
)
from backend.app.core.settings import Settings, get_settings
from backend.app.db.audit_repository import AuditRepository
from backend.app.db.upload_job_repository import UploadJobRepository
from backend.app.main import app
from backend.app.schemas.runtime import (
    RuntimeOverallStatus,
    RuntimePortStatus,
    RuntimeProbeStatus,
    RuntimeServiceStatus,
    RuntimeStatusResponse,
)
from backend.app.schemas.upload_jobs import UploadJobStatus
from tests.backend.test_upload_jobs_repository_contract import create_preview_with_items


def ready_runtime(tmp_path: Path) -> RuntimeStatusResponse:
    checked_at = datetime(2026, 6, 13, 9, 0, tzinfo=timezone.utc)
    return RuntimeStatusResponse(
        overall_status=RuntimeOverallStatus.ready,
        reason_code="runtime_ready",
        reason_text="Runtime ready.",
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
        grafana=RuntimeProbeStatus(name="Grafana", status=RuntimeServiceStatus.ready, detail="HTTP 200"),
        containers=[],
        config=[],
        active_operation=None,
    )


def test_dashboard_endpoint_returns_neutral_state_when_no_job_exists(tmp_path: Path) -> None:
    state_path = tmp_path / "missing-state.db"
    app.dependency_overrides[get_settings] = lambda: Settings(state_db_path=str(state_path))
    app.dependency_overrides[get_dashboard_runtime_status] = lambda: ready_runtime(tmp_path)
    client = TestClient(app)

    try:
        response = client.get("/api/dashboard")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["overall"]["state"] == "ready"
    assert data["overall"]["title"] == "No upload job recorded"
    assert data["currentJob"] is None
    assert data["recentJobs"] == []
    assert next(item for item in data["statusMatrix"] if item["id"] == "upload")["tone"] == "muted"
    assert "job_20260601_0912" not in response.text
    assert "running" not in data["topbarChips"][1]["tone"]


def test_dashboard_endpoint_uses_latest_succeeded_upload_job(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    upload_repository = UploadJobRepository(db_path)
    audit_repository = AuditRepository(db_path)
    upload_repository.create_job_from_preview(job_id="upl_stage4", preview_run_id="prv_done", options={}, config_snapshot={})
    upload_repository.start_job("upl_stage4")
    job_file_id = upload_repository.list_job_files("upl_stage4")[0]["job_file_id"]
    upload_repository.update_file_progress(
        job_file_id,
        processed_rows=17179,
        uploaded_rows=17179,
        inserted_rows=17179,
        row_count=17179,
        resume_offset=17179,
    )
    upload_repository.mark_file_completed(job_file_id, uploaded_rows=17179, inserted_rows=17179)
    upload_repository.finish_job("upl_stage4", UploadJobStatus.succeeded)
    audit_repository.insert_audit(
        action="upload.start",
        target_type="upload_job",
        target_id="upl_stage4",
        params={"rawParams": "hidden-value"},
        result="success",
        job_id="upl_stage4",
    )
    app.dependency_overrides[get_settings] = lambda: Settings(state_db_path=str(db_path))
    app.dependency_overrides[get_dashboard_upload_repository] = lambda: upload_repository
    app.dependency_overrides[get_dashboard_audit_repository] = lambda: audit_repository
    app.dependency_overrides[get_dashboard_runtime_status] = lambda: ready_runtime(tmp_path)
    client = TestClient(app)

    try:
        response = client.get("/api/dashboard")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["overall"]["state"] == "ready"
    assert data["overall"]["title"] == "Latest upload succeeded"
    assert "accepted 17179 rows" in data["overall"]["message"]
    assert data["currentJob"]["jobId"] == "upl_stage4"
    assert data["currentJob"]["status"] == "succeeded"
    assert data["currentJob"]["progressPct"] == 100
    assert data["currentJob"]["rowsSent"] == 17179
    assert data["recentJobs"][0]["status"] == "succeeded"
    assert data["recentJobs"][0]["rowsSent"] == 17179
    assert data["topbarChips"][1]["tone"] == "ready"
    assert data["auditSummary"][0]["action"] == "upload.start"
    assert "hidden-value" not in response.text


def test_dashboard_summary_endpoint_uses_same_real_state_contract(tmp_path: Path) -> None:
    state_path = tmp_path / "missing-state.db"
    app.dependency_overrides[get_settings] = lambda: Settings(state_db_path=str(state_path))
    app.dependency_overrides[get_dashboard_runtime_status] = lambda: ready_runtime(tmp_path)
    client = TestClient(app)

    try:
        response = client.get("/api/dashboard/summary")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["currentJob"] is None
    assert data["recentJobs"] == []
