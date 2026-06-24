from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.api.dashboard import (
    get_dashboard_audit_repository,
    get_dashboard_runtime_status,
    get_dashboard_upload_repository,
)
from backend.app.core.settings import DEFAULT_REPO_ROOT, Settings, get_settings
from backend.app.core.state_context import build_state_context
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
from tests.backend.test_upload_jobs_repository_contract import PREVIEW_GATE_SNAPSHOT, create_preview_with_items


def ready_runtime(
    tmp_path: Path,
    *,
    api: RuntimeServiceStatus = RuntimeServiceStatus.ready,
    db: RuntimeServiceStatus = RuntimeServiceStatus.ready,
    studio: RuntimeServiceStatus = RuntimeServiceStatus.ready,
    edge: RuntimeServiceStatus = RuntimeServiceStatus.ready,
    grafana: RuntimeServiceStatus = RuntimeServiceStatus.ready,
    vector: RuntimeServiceStatus = RuntimeServiceStatus.ready,
) -> RuntimeStatusResponse:
    checked_at = datetime(2026, 6, 13, 9, 0, tzinfo=timezone.utc)
    core_ready = (
        api == RuntimeServiceStatus.ready
        and db == RuntimeServiceStatus.ready
        and studio == RuntimeServiceStatus.ready
        and edge == RuntimeServiceStatus.ready
    )
    non_core_ready = grafana == RuntimeServiceStatus.ready and vector == RuntimeServiceStatus.ready
    if core_ready and non_core_ready:
        overall_status = RuntimeOverallStatus.ready
        reason_code = "runtime_ready"
        reason_text = "Runtime ready."
    elif not core_ready:
        overall_status = RuntimeOverallStatus.blocked
        reason_code = "core_runtime_unreachable"
        reason_text = "Core runtime unreachable."
    else:
        overall_status = RuntimeOverallStatus.attention
        reason_code = "non_core_runtime_attention"
        reason_text = "Core runtime is reachable. Grafana or Vector needs attention as a non-core observability caveat."
    return RuntimeStatusResponse(
        overall_status=overall_status,
        reason_code=reason_code,
        reason_text=reason_text,
        checked_at=checked_at,
        project_path=str(tmp_path / "runtime"),
        project_id="Extrusion_web_console",
        docker=RuntimeProbeStatus(name="Docker", status=RuntimeServiceStatus.ready, detail="ready"),
        wsl=RuntimeProbeStatus(name="WSL", status=RuntimeServiceStatus.ready, detail="ready"),
        supabase_cli=RuntimeProbeStatus(name="Supabase CLI", status=RuntimeServiceStatus.ready, detail="ready"),
        api=RuntimePortStatus(name="Supabase API", port=55321, status=api, detail="ready"),
        db=RuntimePortStatus(name="Supabase DB", port=25433, status=db, detail="ready"),
        studio=RuntimePortStatus(name="Supabase Studio", port=55323, status=studio, detail="ready"),
        edge_runtime=RuntimeProbeStatus(name="Edge Function", status=edge, detail="ready"),
        grafana=RuntimeProbeStatus(name="Grafana", status=grafana, detail="HTTP 200"),
        vector=RuntimeProbeStatus(
            name="Vector",
            status=vector,
            detail="Vector container is running." if vector == RuntimeServiceStatus.ready else f"Vector container status class is {vector.value}.",
        ),
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
    assert data["stateContext"]["contextClass"] == "qa_temporary"
    assert data["stateContext"]["storageStatus"] == "missing"
    assert data["topbarChips"][3]["value"] == data["stateContext"]["label"]
    assert next(item for item in data["statusMatrix"] if item["id"] == "upload")["tone"] == "muted"
    assert next(item for item in data["statusMatrix"] if item["id"] == "state_store")["value"] == data["stateContext"]["label"]
    assert "job_20260601_0912" not in response.text
    assert "running" not in data["topbarChips"][1]["tone"]
    assert str(state_path) not in response.text


def test_dashboard_endpoint_uses_latest_succeeded_upload_job(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    upload_repository = UploadJobRepository(db_path)
    audit_repository = AuditRepository(db_path)
    upload_repository.create_job_from_preview(
        job_id="upl_stage4",
        preview_run_id="prv_done",
        expected_target_rows=2,
        expected_target_files=1,
        options={},
        config_snapshot={},
        preview_gate_snapshot=PREVIEW_GATE_SNAPSHOT,
    )
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
    assert data["currentJob"]["stateContext"]["label"] == data["stateContext"]["label"]
    assert data["recentJobs"][0]["status"] == "succeeded"
    assert data["recentJobs"][0]["rowsSent"] == 17179
    assert data["recentJobs"][0]["stateContext"]["contextClass"] == data["stateContext"]["contextClass"]
    assert data["topbarChips"][1]["tone"] == "ready"
    assert data["auditSummary"][0]["action"] == "upload.start"
    assert "hidden-value" not in response.text
    assert str(db_path) not in response.text


@pytest.mark.parametrize("failed_probe", ["api", "db", "studio", "edge"])
def test_dashboard_marks_core_runtime_failure_as_blocking(tmp_path: Path, failed_probe: str) -> None:
    state_path = tmp_path / "missing-state.db"
    app.dependency_overrides[get_settings] = lambda: Settings(state_db_path=str(state_path))
    app.dependency_overrides[get_dashboard_runtime_status] = lambda: ready_runtime(
        tmp_path,
        api=RuntimeServiceStatus.unreachable if failed_probe == "api" else RuntimeServiceStatus.ready,
        db=RuntimeServiceStatus.unreachable if failed_probe == "db" else RuntimeServiceStatus.ready,
        studio=RuntimeServiceStatus.unreachable if failed_probe == "studio" else RuntimeServiceStatus.ready,
        edge=RuntimeServiceStatus.unreachable if failed_probe == "edge" else RuntimeServiceStatus.ready,
    )
    client = TestClient(app)

    try:
        response = client.get("/api/dashboard")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["overall"]["state"] == "blocked"
    runtime_chip = next(item for item in data["topbarChips"] if item["id"] == "supabase")
    runtime_warning = next(item for item in data["warningQueue"] if item["id"] == "supabase_unreachable")
    assert runtime_chip["tone"] == "blocked"
    assert runtime_warning["tone"] == "blocked"
    assert runtime_warning["count"] == 1


def test_dashboard_keeps_grafana_failure_as_non_core_caveat(tmp_path: Path) -> None:
    state_path = tmp_path / "missing-state.db"
    app.dependency_overrides[get_settings] = lambda: Settings(state_db_path=str(state_path))
    app.dependency_overrides[get_dashboard_runtime_status] = lambda: ready_runtime(tmp_path, grafana=RuntimeServiceStatus.unreachable)
    client = TestClient(app)

    try:
        response = client.get("/api/dashboard")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    runtime_chip = next(item for item in data["topbarChips"] if item["id"] == "supabase")
    grafana_chip = next(item for item in data["topbarChips"] if item["id"] == "grafana")
    runtime_warning = next(item for item in data["warningQueue"] if item["id"] == "supabase_unreachable")
    assert runtime_chip["tone"] == "ready"
    assert grafana_chip["tone"] == "attention"
    assert runtime_warning["tone"] == "ready"
    assert runtime_warning["count"] == 0


def test_dashboard_exposes_vector_as_non_core_observability_check(tmp_path: Path) -> None:
    state_path = tmp_path / "missing-state.db"
    app.dependency_overrides[get_settings] = lambda: Settings(state_db_path=str(state_path))
    app.dependency_overrides[get_dashboard_runtime_status] = lambda: ready_runtime(tmp_path, vector=RuntimeServiceStatus.stopped)
    client = TestClient(app)

    try:
        response = client.get("/api/dashboard")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    vector_row = next(item for item in data["runtimeChecks"] if item["id"] == "vector")
    runtime_chip = next(item for item in data["topbarChips"] if item["id"] == "supabase")
    runtime_warning = next(item for item in data["warningQueue"] if item["id"] == "supabase_unreachable")
    assert data["overall"]["state"] == "ready"
    assert runtime_chip["tone"] == "ready"
    assert runtime_chip["value"] == "Core runtime OK"
    assert vector_row["tone"] == "attention"
    assert vector_row["detail"] == "Vector container status class is stopped."
    assert runtime_warning["tone"] == "ready"
    assert runtime_warning["count"] == 0


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
    assert data["stateContext"]["label"]


def test_state_context_classifies_operator_package_path(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("backend.app.core.state_context.tempfile.gettempdir", lambda: str(tmp_path / "other-temp-root"))
    state_path = tmp_path / "ExtrusionWebConsole" / "web_console_state.db"
    state_path.parent.mkdir()
    state_path.write_text("", encoding="utf-8")

    state_context = build_state_context(Settings(state_db_path=str(state_path)))

    assert state_context.context_class == "operator_package"
    assert state_context.storage_status == "present"
    assert str(state_path) not in state_context.to_api().values()


def test_state_context_classifies_development_default_path() -> None:
    state_context = build_state_context(Settings(state_db_path=str(DEFAULT_REPO_ROOT / "README.md")))

    assert state_context.context_class == "development_default"
    assert state_context.storage_status == "present"
    assert str(DEFAULT_REPO_ROOT) not in state_context.to_api().values()


def test_state_context_classifies_unknown_and_inaccessible(tmp_path: Path) -> None:
    parent_file = tmp_path / "state-parent-file"
    parent_file.write_text("", encoding="utf-8")

    unknown_context = build_state_context(Settings(state_db_path=""))
    inaccessible_context = build_state_context(Settings(state_db_path=str(parent_file / "state.db")))

    assert unknown_context.context_class == "unknown"
    assert unknown_context.storage_status == "unknown"
    assert inaccessible_context.context_class == "inaccessible"
    assert inaccessible_context.storage_status == "inaccessible"
