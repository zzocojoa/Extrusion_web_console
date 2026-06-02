from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.api.upload_jobs import get_upload_job_repository
from backend.app.core.settings import Settings, get_settings
from backend.app.db.upload_job_repository import UploadJobRepository
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


def test_upload_job_latest_returns_404_when_empty(tmp_path: Path) -> None:
    repository = UploadJobRepository(tmp_path / "state.db")
    app.dependency_overrides[get_upload_job_repository] = lambda: repository
    client = TestClient(app)

    try:
        response = client.get("/api/upload/jobs/latest")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
