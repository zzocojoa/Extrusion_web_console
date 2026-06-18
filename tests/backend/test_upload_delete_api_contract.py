from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.api.upload_delete import get_upload_delete_repository, get_upload_delete_service
from backend.app.core.settings import get_settings
from backend.app.db.upload_delete_repository import UploadDeleteRepository
from backend.app.main import app, create_app
from backend.app.schemas.upload_delete import DeletePreflightRequest
from tests.backend.test_upload_delete_service_contract import FakeDeleteDb, create_preview_for_delete, service


def test_upload_delete_routes_are_registered_in_openapi(monkeypatch) -> None:
    monkeypatch.setenv("EWC_API_DOCS_MODE", "enabled")
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.get("/api/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/upload/delete/preflight" in paths
    assert "post" in paths["/api/upload/delete/preflight"]
    assert "/api/upload/delete/jobs" in paths
    assert "post" in paths["/api/upload/delete/jobs"]
    assert "/api/upload/delete/jobs/latest" in paths
    assert "get" in paths["/api/upload/delete/jobs/latest"]
    assert "/api/upload/delete/jobs/{deleteRunId}/reconcile" in paths
    assert "post" in paths["/api/upload/delete/jobs/{deleteRunId}/reconcile"]
    get_settings.cache_clear()


def test_upload_delete_preflight_and_start_expose_safe_contract(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    item_id, _source_file = create_preview_for_delete(db_path, tmp_path / "source")
    fake_db = FakeDeleteDb()
    delete_service = service(db_path, fake_db)
    app.dependency_overrides[get_upload_delete_service] = lambda: delete_service
    app.dependency_overrides[get_upload_delete_repository] = lambda: UploadDeleteRepository(db_path)
    client = TestClient(app)

    try:
        preflight_response = client.post(
            "/api/upload/delete/preflight",
            json={
                "previewRunId": "prv_done",
                "previewItemIds": [item_id],
                "expectedAlreadyInDbItems": 1,
            },
        )
        start_response = client.post(
            "/api/upload/delete/jobs",
            json={
                "preflightId": preflight_response.json()["preflightId"],
                "expectedDeleteKeys": 2,
                "typedDeleteKeys": "2",
                "acknowledgeNoUndo": True,
                "acknowledgeRollbackRequiresFreshPreviewAndStartUpload": True,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert preflight_response.status_code == 200
    preflight = preflight_response.json()
    assert preflight["status"] == "ready"
    assert preflight["selectedKeyCount"] == 2
    assert preflight["rollbackReady"] is True
    assert preflight["dbTargetGuard"]["status"] == "passed"
    assert "2026-06-18T09:00:00" not in preflight_response.text
    assert "extruder_integrated" not in preflight_response.text

    assert start_response.status_code == 200
    started = start_response.json()
    assert started["status"] == "succeeded"
    assert started["expectedDeleteKeys"] == 2
    assert started["deletedKeys"] == 2
    assert started["rawKeysReturned"] is False
    assert fake_db.delete_calls == 1


def test_upload_delete_start_mismatch_returns_reason_without_db_mutation(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    item_id, _source_file = create_preview_for_delete(db_path, tmp_path / "source")
    fake_db = FakeDeleteDb()
    delete_service = service(db_path, fake_db)
    preflight = delete_service.create_preflight(
        DeletePreflightRequest(
            preview_run_id="prv_done",
            preview_item_ids=[item_id],
            expected_already_in_db_items=1,
        )
    )
    app.dependency_overrides[get_upload_delete_service] = lambda: delete_service
    client = TestClient(app)

    try:
        response = client.post(
            "/api/upload/delete/jobs",
            json={
                "preflightId": preflight.preflight_id,
                "expectedDeleteKeys": 2,
                "typedDeleteKeys": "1",
                "acknowledgeNoUndo": True,
                "acknowledgeRollbackRequiresFreshPreviewAndStartUpload": True,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["detail"]["reason"] == "typed_delete_keys_mismatch"
    assert fake_db.delete_calls == 0


def test_upload_delete_latest_returns_404_when_empty(tmp_path: Path) -> None:
    repository = UploadDeleteRepository(tmp_path / "state.db")
    app.dependency_overrides[get_upload_delete_repository] = lambda: repository
    client = TestClient(app)

    try:
        response = client.get("/api/upload/delete/jobs/latest")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
