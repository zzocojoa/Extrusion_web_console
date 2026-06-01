from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status

from backend.app.core.settings import Settings, get_settings
from backend.app.db.preview_repository import PreviewRepository
from backend.app.schemas.upload_preview import (
    PreviewCancelResponse,
    PreviewCreateRequest,
    PreviewCreateResponse,
    PreviewDbStatus,
    PreviewItemDto,
    PreviewPageDto,
    PreviewRunDetailResponse,
    PreviewRunDto,
    PreviewRunStatus,
    PreviewRunSummary,
)
from backend.app.services.upload_preview import PreviewService

router = APIRouter(prefix="/api/upload/preview", tags=["upload-preview"])
executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="upload-preview")


def get_preview_repository(settings: Settings = Depends(get_settings)) -> PreviewRepository:
    return PreviewRepository(settings.state_db_path)


def parse_json_list(value: str | None) -> list[Any]:
    if not value:
        return []
    import json

    parsed = json.loads(value)
    return parsed if isinstance(parsed, list) else []


def run_dto(row: Any) -> PreviewRunDto:
    return PreviewRunDto(
        preview_run_id=row["preview_run_id"],
        status=PreviewRunStatus(row["status"]),
        requested_at=datetime.fromisoformat(row["requested_at"]),
        started_at=None if row["started_at"] is None else datetime.fromisoformat(row["started_at"]),
        finished_at=None if row["finished_at"] is None else datetime.fromisoformat(row["finished_at"]),
        db_status=PreviewDbStatus(row["db_status"]),
        summary=PreviewRunSummary(
            total=row["total_files"],
            target=row["target_count"],
            already_in_db=row["already_in_db_count"],
            partial_overlap=row["partial_overlap_count"],
            risky=row["risky_count"],
            excluded=row["excluded_count"],
            upload_rows=row["upload_row_estimate"],
            db_matched_rows=row["db_match_count"],
        ),
        warnings=[],
        error_code=row["error_code"],
        error_message=row["error_message"],
    )


def item_dto(row: Any) -> PreviewItemDto:
    return PreviewItemDto(
        preview_item_id=row["preview_item_id"],
        status=row["status"],
        reason_code=row["reason_code"],
        reason_text=row["reason_text"],
        kind=row["kind"],
        folder_label=row["folder_label"],
        filename=row["filename"],
        path=row["path"],
        file_date=None if row["file_date"] is None else datetime.fromisoformat(row["file_date"]).date(),
        size_bytes=row["size_bytes"],
        modified_at=None if row["modified_at"] is None else datetime.fromisoformat(row["modified_at"]),
        scan_mode=row["scan_mode"],
        sample_row_count=row["sample_row_count"],
        row_count=row["row_count"],
        local_key_count=row["local_key_count"],
        db_match_count=row["db_match_count"],
        upload_row_estimate=row["upload_row_estimate"],
        first_timestamp=row["first_timestamp"],
        last_timestamp=row["last_timestamp"],
        device_ids=parse_json_list(row["device_ids_json"]),
        issues=parse_json_list(row["issues_json"]),
        error_code=row["error_code"],
        error_message=row["error_message"],
    )


@router.post("", response_model=PreviewCreateResponse, status_code=status.HTTP_202_ACCEPTED)
def create_preview(
    request: PreviewCreateRequest,
    response: Response,
    settings: Settings = Depends(get_settings),
    repository: PreviewRepository = Depends(get_preview_repository),
) -> PreviewCreateResponse:
    active_run_id = repository.has_active_run()
    if active_run_id is not None:
        response.headers["Location"] = f"/api/upload/preview/{active_run_id}"
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"activePreviewRunId": active_run_id},
        )

    preview_run_id = f"prv_{uuid4().hex[:12]}"
    repository.create_run(
        preview_run_id=preview_run_id,
        range_mode=request.range_mode.value,
        start_date=request.start_date.isoformat() if request.start_date else None,
        end_date=request.end_date.isoformat() if request.end_date else None,
        sources=[source.value for source in request.sources],
        options=request.options.model_dump(mode="json", by_alias=True),
        config_snapshot={
            "plcDataDir": settings.plc_data_dir,
            "temperatureDataDir": settings.temperature_data_dir,
            "supabaseDbUrlConfigured": bool(settings.supabase_db_url),
        },
        retry_of_run_id=request.retry_of_run_id,
    )
    service = PreviewService(settings, repository)
    executor.submit(service.run_preview, preview_run_id, request)
    return PreviewCreateResponse(
        preview_run_id=preview_run_id,
        status=PreviewRunStatus.queued,
        poll_url=f"/api/upload/preview/{preview_run_id}",
    )


@router.get("/latest", response_model=PreviewRunDetailResponse)
def get_latest_preview(
    completed_only: bool = Query(default=False, alias="completedOnly"),
    repository: PreviewRepository = Depends(get_preview_repository),
) -> PreviewRunDetailResponse:
    row = repository.get_latest_run(completed_only=completed_only)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No preview run exists")
    return preview_detail(row["preview_run_id"], repository=repository)


@router.get("/{previewRunId}", response_model=PreviewRunDetailResponse)
def preview_detail(
    preview_run_id: str = Path(alias="previewRunId"),
    status_filter: str | None = Query(default=None, alias="status"),
    q: str | None = None,
    sort: str = "status",
    order: str = "asc",
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    repository: PreviewRepository = Depends(get_preview_repository),
) -> PreviewRunDetailResponse:
    row = repository.get_run(preview_run_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preview run not found")
    items, total_items = repository.list_items(
        preview_run_id,
        status=status_filter,
        query=q,
        sort=sort,
        order=order,
        limit=limit,
        offset=offset,
    )
    return PreviewRunDetailResponse(
        run=run_dto(row),
        items=[item_dto(item) for item in items],
        page=PreviewPageDto(limit=limit, offset=offset, total_items=total_items),
    )


@router.post("/{previewRunId}/cancel", response_model=PreviewCancelResponse)
def cancel_preview(
    preview_run_id: str = Path(alias="previewRunId"),
    repository: PreviewRepository = Depends(get_preview_repository),
) -> PreviewCancelResponse:
    run_status = repository.request_cancel(preview_run_id)
    if run_status is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preview run not found")
    return PreviewCancelResponse(preview_run_id=preview_run_id, status=run_status)
