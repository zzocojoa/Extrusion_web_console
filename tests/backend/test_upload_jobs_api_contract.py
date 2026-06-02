from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.api.upload_jobs import get_upload_job_repository
from backend.app.core.settings import Settings, get_settings
from backend.app.db.upload_job_repository import UploadJobRepository
from backend.app.schemas.upload_jobs import UploadJobStatus
from backend.app.main import app
from tests.backend.test_upload_jobs_repository_contract import create_preview_with_items


def test_upload_job_routes_are_registered_in_openapi() -> None:
    client = TestClient(app)

    response = client.get("/api/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/upload/jobs" in paths
    assert "/api/upload/jobs/latest" in paths
    assert "/api/upload/jobs/{jobId}" in paths
    assert "/api/upload/jobs/{jobId}/retry" in paths
    assert "/api/upload/jobs/{jobId}/events" in paths


def test_upload_job_start_rejects_missing_upload_config(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    app.dependency_overrides[get_upload_job_repository] = lambda: repository
    app.dependency_overrides[get_settings] = lambda: Settings(state_db_path=str(db_path))
    client = TestClient(app)

    try:
        response = client.post("/api/upload/jobs", json={"previewRunId": "prv_done"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["detail"]["reason"] == "upload_config_missing"
    assert latest_audit(repository)["result"] == "blocked"
    assert latest_audit(repository)["error_code"] == "upload_config_missing"


def test_upload_job_latest_returns_404_when_empty(tmp_path: Path) -> None:
    repository = UploadJobRepository(tmp_path / "state.db")
    app.dependency_overrides[get_upload_job_repository] = lambda: repository
    client = TestClient(app)

    try:
        response = client.get("/api/upload/jobs/latest")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_upload_job_start_active_job_writes_blocked_audit(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    repository.create_job_from_preview(job_id="upl_active", preview_run_id="prv_done", options={}, config_snapshot={})
    app.dependency_overrides[get_upload_job_repository] = lambda: repository
    app.dependency_overrides[get_settings] = lambda: Settings(
        state_db_path=str(db_path),
        supabase_edge_url="http://localhost/upload",
        supabase_anon_key="anon",
    )
    client = TestClient(app)

    try:
        response = client.post("/api/upload/jobs", json={"previewRunId": "prv_done"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json()["detail"]["reason"] == "active_upload_job"
    audit = latest_audit(repository)
    assert audit["action"] == "upload.start"
    assert audit["result"] == "blocked"
    assert audit["error_code"] == "active_upload_job"


def test_upload_job_start_preview_not_uploadable_writes_blocked_audit(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    with repository.connect() as connection:
        connection.execute("UPDATE preview_runs SET status = 'partial_failed', db_status = 'unreachable' WHERE preview_run_id = 'prv_done'")
    app.dependency_overrides[get_upload_job_repository] = lambda: repository
    app.dependency_overrides[get_settings] = lambda: Settings(
        state_db_path=str(db_path),
        supabase_edge_url="http://localhost/upload",
        supabase_anon_key="anon",
    )
    client = TestClient(app)

    try:
        response = client.post("/api/upload/jobs", json={"previewRunId": "prv_done"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["detail"]["reason"] == "preview_not_uploadable"
    audit = latest_audit(repository)
    assert audit["action"] == "upload.start"
    assert audit["result"] == "blocked"
    assert audit["error_code"] == "preview_not_uploadable"


def test_retry_no_retryable_files_writes_blocked_audit(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    repository.create_job_from_preview(job_id="upl_done", preview_run_id="prv_done", options={}, config_snapshot={})
    file_id = repository.list_job_files("upl_done")[0]["job_file_id"]
    repository.mark_file_completed(file_id, uploaded_rows=2, inserted_rows=2)
    repository.finish_job("upl_done", UploadJobStatus.succeeded)
    app.dependency_overrides[get_upload_job_repository] = lambda: repository
    app.dependency_overrides[get_settings] = lambda: Settings(
        state_db_path=str(db_path),
        supabase_edge_url="http://localhost/upload",
        supabase_anon_key="anon",
    )
    client = TestClient(app)

    try:
        response = client.post("/api/upload/jobs/upl_done/retry", json={})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["detail"]["reason"] == "no_retryable_files"
    audit = latest_audit(repository)
    assert audit["action"] == "upload.retry"
    assert audit["result"] == "blocked"
    assert audit["error_code"] == "no_retryable_files"


def test_upload_job_events_replays_after_seq(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    repository.create_job_from_preview(job_id="upl_events", preview_run_id="prv_done", options={}, config_snapshot={})
    repository.append_event("upl_events", event_type="log.info", level="info", message="second")
    repository.finish_job("upl_events", UploadJobStatus.succeeded)
    app.dependency_overrides[get_upload_job_repository] = lambda: repository
    client = TestClient(app)

    try:
        with client.stream("GET", "/api/upload/jobs/upl_events/events?afterSeq=1") as response:
            body = "".join(response.iter_text())
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "id: 2" in body
    assert "log.info" in body


def latest_audit(repository: UploadJobRepository):
    with repository.connect() as connection:
        return connection.execute("SELECT * FROM audit_log ORDER BY audit_id DESC LIMIT 1").fetchone()
