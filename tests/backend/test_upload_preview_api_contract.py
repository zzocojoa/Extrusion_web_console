from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.api.upload_preview import get_preview_repository
from backend.app.db.preview_repository import PreviewRepository
from backend.app.main import app


def test_upload_preview_routes_are_registered_in_openapi() -> None:
    client = TestClient(app)

    response = client.get("/api/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/upload/preview" in paths
    assert "post" in paths["/api/upload/preview"]
    assert "/api/upload/preview/latest" in paths
    assert "get" in paths["/api/upload/preview/latest"]
    assert "/api/upload/preview/{previewRunId}" in paths
    assert "get" in paths["/api/upload/preview/{previewRunId}"]
    assert "/api/upload/preview/{previewRunId}/cancel" in paths
    assert "post" in paths["/api/upload/preview/{previewRunId}/cancel"]


def test_upload_preview_create_rejects_invalid_custom_range_before_work_starts(tmp_path) -> None:
    app.dependency_overrides[get_preview_repository] = lambda: PreviewRepository(
        str(tmp_path / "state.db")
    )
    client = TestClient(app)

    try:
        response = client.post(
            "/api/upload/preview",
            json={"rangeMode": "custom", "sources": ["plc"]},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_upload_preview_delete_is_not_a_v1_api() -> None:
    client = TestClient(app)

    response = client.delete("/api/upload/preview/prv_20260601_000001")

    assert response.status_code == 405
