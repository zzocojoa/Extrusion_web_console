from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.api.upload_preview import get_preview_repository
from backend.app.db.preview_repository import PreviewRepository
from backend.app.main import app
from backend.app.schemas.upload_preview import PreviewDbStatus, PreviewRunStatus


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


def test_upload_preview_latest_returns_persisted_run_details(tmp_path) -> None:
    repository = PreviewRepository(str(tmp_path / "state.db"))
    repository.create_run(
        preview_run_id="prv_latest",
        range_mode="today",
        start_date=None,
        end_date=None,
        sources=["plc"],
        options={},
        config_snapshot={},
        retry_of_run_id=None,
    )
    repository.insert_item(
        "prv_latest",
        {
            "file_key": "PLC/Factory_Integrated_Log_20260601_090000.csv",
            "folder_label": "PLC",
            "folder_path": "C:\\data\\plc",
            "filename": "Factory_Integrated_Log_20260601_090000.csv",
            "path": "C:\\data\\plc\\Factory_Integrated_Log_20260601_090000.csv",
            "kind": "plc",
            "file_date": "2026-06-01",
            "size_bytes": 100,
            "mtime_ns": 1,
            "modified_at": "2026-06-01T09:00:00+09:00",
            "file_signature": "sig",
            "status": "risky",
            "reason_code": "db_unreachable",
            "reason_text": "Local Supabase DB could not be reached.",
            "scan_mode": "full",
            "sample_row_count": 2,
            "row_count": 2,
            "local_key_count": 2,
            "db_match_count": None,
            "upload_row_estimate": 0,
            "first_timestamp": "2026-06-01T09:00:00+09:00",
            "last_timestamp": "2026-06-01T09:01:00+09:00",
            "device_ids": ["extruder_integrated"],
            "issues": ["db_unreachable"],
            "error_code": "db_unreachable",
            "error_message": "Local Supabase DB could not be reached.",
        },
    )
    repository.recompute_summary(
        "prv_latest",
        status=PreviewRunStatus.partial_failed,
        db_status=PreviewDbStatus.unreachable,
        error_code="db_unreachable",
        error_message="Local Supabase DB could not be reached.",
    )
    app.dependency_overrides[get_preview_repository] = lambda: repository
    client = TestClient(app)

    try:
        response = client.get("/api/upload/preview/latest")
        filtered_response = client.get("/api/upload/preview/latest?status=target")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["run"]["previewRunId"] == "prv_latest"
    assert payload["run"]["status"] == "partial_failed"
    assert payload["run"]["dbStatus"] == "unreachable"
    assert payload["items"][0]["status"] == "risky"
    assert payload["items"][0]["reasonCode"] == "db_unreachable"

    assert filtered_response.status_code == 200
    filtered_payload = filtered_response.json()
    assert filtered_payload["run"]["previewRunId"] == "prv_latest"
    assert filtered_payload["items"] == []
    assert filtered_payload["page"]["totalItems"] == 0


def test_upload_preview_conflict_returns_active_run_location(tmp_path) -> None:
    repository = PreviewRepository(str(tmp_path / "state.db"))
    repository.create_run(
        preview_run_id="prv_active",
        range_mode="today",
        start_date=None,
        end_date=None,
        sources=["plc"],
        options={},
        config_snapshot={},
        retry_of_run_id=None,
    )
    app.dependency_overrides[get_preview_repository] = lambda: repository
    client = TestClient(app)

    try:
        response = client.post(
            "/api/upload/preview",
            json={"rangeMode": "today", "sources": ["plc"]},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.headers["location"] == "/api/upload/preview/prv_active"
    assert response.json()["detail"]["activePreviewRunId"] == "prv_active"


def test_upload_preview_rejects_invalid_list_query_params(tmp_path) -> None:
    repository = PreviewRepository(str(tmp_path / "state.db"))
    repository.create_run(
        preview_run_id="prv_latest",
        range_mode="today",
        start_date=None,
        end_date=None,
        sources=["plc"],
        options={},
        config_snapshot={},
        retry_of_run_id=None,
    )
    app.dependency_overrides[get_preview_repository] = lambda: repository
    client = TestClient(app)

    try:
        response = client.get("/api/upload/preview/latest?status=not_a_status")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
