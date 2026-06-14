from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
from typing import Any, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, status
from pydantic import ValidationError

from backend.app.core.settings import Settings, get_settings
from backend.app.db.audit_repository import AuditRepository
from backend.app.db.preview_repository import PreviewRepository
from backend.app.schemas.audit import AuditResult
from backend.app.schemas.upload_preview import (
    PreviewCancelResponse,
    PreviewCreateRequest,
    PreviewCreateResponse,
    PreviewDbStatus,
    PreviewItemDto,
    PreviewItemStatus,
    PreviewPageDto,
    PreviewRunDetailResponse,
    PreviewRunDto,
    PreviewRunStatus,
    PreviewRunSummary,
    PreviewOptions,
    PreviewProfile,
    PreviewRangeMode,
    PreviewSource,
)
from backend.app.services.upload_preview import PreviewService

router = APIRouter(prefix="/api/upload/preview", tags=["upload-preview"])
executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="upload-preview")


OPERATIONAL_PLC_SOURCE_CLASSES = {"network", "drive_letter", "mounted"}


def source_path_class(path: str) -> str:
    normalized = path.strip()
    if not normalized:
        return "missing"
    if normalized.startswith("\\\\") or normalized.startswith("//"):
        return "network"
    if len(normalized) >= 3 and normalized[1] == ":" and normalized[2] in {"\\", "/"}:
        return "drive_letter"
    if normalized.startswith("/mnt/"):
        return "mounted"
    return "local"


def is_large_preview_range(request: PreviewCreateRequest) -> bool:
    if request.range_mode == PreviewRangeMode.last_2_days:
        return True
    if request.range_mode == PreviewRangeMode.custom and request.start_date and request.end_date:
        return (request.end_date - request.start_date).days >= 1
    return False


def resolve_preview_auto_safe_mode(request: PreviewCreateRequest, settings: Settings) -> PreviewCreateRequest:
    if request.options.profile != PreviewProfile.default:
        return request
    if PreviewSource.plc not in request.sources:
        return request
    if (
        source_path_class(settings.plc_data_dir) not in OPERATIONAL_PLC_SOURCE_CLASSES
        and not is_large_preview_range(request)
    ):
        return request

    options = request.options.model_dump(mode="json", by_alias=True)
    options["profile"] = PreviewProfile.large_source_operational.value
    return request.model_copy(update={"options": PreviewOptions.model_validate(options)})


def get_preview_repository(settings: Settings = Depends(get_settings)) -> PreviewRepository:
    return PreviewRepository(settings.state_db_path)


def get_preview_audit_repository(settings: Settings = Depends(get_settings)) -> AuditRepository:
    return AuditRepository(settings.state_db_path)


def parse_json_list(value: str | None) -> list[Any]:
    if not value:
        return []
    import json

    parsed = json.loads(value)
    return parsed if isinstance(parsed, list) else []


def parse_json_dict(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    parsed = json.loads(value)
    return parsed if isinstance(parsed, dict) else {}


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
        timeout_stage=row["timeout_stage"],
        timing=parse_json_dict(row["timing_json"]),
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
        timeout_stage=row["timeout_stage"],
        timing=parse_json_dict(row["timing_json"]),
        error_code=row["error_code"],
        error_message=row["error_message"],
    )


@router.post("", response_model=PreviewCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_preview(
    raw_request: Request,
    settings: Settings = Depends(get_settings),
    repository: PreviewRepository = Depends(get_preview_repository),
    audit_repository: AuditRepository = Depends(get_preview_audit_repository),
) -> PreviewCreateResponse:
    try:
        payload = await raw_request.json()
    except json.JSONDecodeError as exc:
        audit_preview_request_failure(
            audit_repository,
            validation_reason="preview_request_json_invalid",
            rejected_fields=[],
        )
        raise HTTPException(
            status_code=422,
            detail={"reason": "preview_request_json_invalid", "keys": []},
        ) from exc
    try:
        request = PreviewCreateRequest.model_validate(payload)
    except ValidationError as exc:
        rejected_fields = preview_validation_fields(exc)
        audit_preview_request_failure(
            audit_repository,
            validation_reason="preview_request_validation_failed",
            rejected_fields=rejected_fields,
        )
        raise HTTPException(
            status_code=422,
            detail={"reason": "preview_request_validation_failed", "keys": rejected_fields},
        ) from exc

    request = resolve_preview_auto_safe_mode(request, settings)
    preview_run_id = f"prv_{uuid4().hex[:12]}"
    active_run_id = repository.create_run_if_no_active(
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
    if active_run_id is not None:
        audit_repository.insert_audit(
            action="upload.preview",
            target_type="preview_run",
            target_id=active_run_id,
            params={
                "previewRunId": active_run_id,
                "candidateCount": 0,
                "targetCount": 0,
                "alreadyInDbCount": 0,
                "partialOverlapCount": 0,
                "riskyCount": 0,
                "excludedCount": 0,
                "dbStatus": "not_checked",
                "reasonCode": "active_preview_run",
                "requestedFilters": safe_requested_filters(request),
            },
            result=AuditResult.blocked,
            error_code="active_preview_run",
            error_message="Another preview run is already active.",
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"activePreviewRunId": active_run_id},
            headers={"Location": f"/api/upload/preview/{active_run_id}"},
        )
    service = PreviewService(settings, repository, audit_repository=audit_repository)
    executor.submit(service.run_preview, preview_run_id, request)
    return PreviewCreateResponse(
        preview_run_id=preview_run_id,
        status=PreviewRunStatus.queued,
        poll_url=f"/api/upload/preview/{preview_run_id}",
    )


def preview_validation_fields(error: ValidationError) -> list[str]:
    fields: set[str] = set()
    for item in error.errors():
        loc = item.get("loc", ())
        if loc:
            fields.add(str(loc[0]))
            continue
        message = str(item.get("msg", ""))
        if "startDate" in message:
            fields.add("startDate")
        if "endDate" in message:
            fields.add("endDate")
    return sorted(fields)


def safe_requested_filters(request: PreviewCreateRequest) -> dict[str, Any]:
    return {
        "rangeMode": request.range_mode.value,
        "startDate": request.start_date.isoformat() if request.start_date else None,
        "endDate": request.end_date.isoformat() if request.end_date else None,
        "sources": [source.value for source in request.sources],
        "retryOfRunId": request.retry_of_run_id,
        "optionKeys": sorted(request.options.model_dump(mode="json", by_alias=True).keys()),
    }


def audit_preview_request_failure(
    audit_repository: AuditRepository,
    *,
    validation_reason: str,
    rejected_fields: list[str],
) -> None:
    audit_repository.insert_audit(
        action="upload.preview",
        target_type="preview_run",
        target_id=None,
        params={
            "previewRunId": None,
            "candidateCount": 0,
            "targetCount": 0,
            "alreadyInDbCount": 0,
            "partialOverlapCount": 0,
            "riskyCount": 0,
            "excludedCount": 0,
            "dbStatus": "not_checked",
            "reasonCode": validation_reason,
            "rejectedFields": sorted(rejected_fields),
            "requestedFilters": {},
        },
        result=AuditResult.failure,
        error_code=validation_reason,
        error_message="Upload Preview request failed validation.",
    )


@router.get("/latest", response_model=PreviewRunDetailResponse)
def get_latest_preview(
    completed_only: bool = Query(default=False, alias="completedOnly"),
    status_filter: PreviewItemStatus | None = Query(default=None, alias="status"),
    q: str | None = None,
    sort: Literal["status", "fileDate", "filename", "uploadRows", "modifiedAt"] = "status",
    order: Literal["asc", "desc"] = "asc",
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    repository: PreviewRepository = Depends(get_preview_repository),
) -> PreviewRunDetailResponse:
    row = repository.get_latest_run(completed_only=completed_only)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No preview run exists")
    return build_preview_detail(
        row["preview_run_id"],
        status_filter=None if status_filter is None else status_filter.value,
        q=q,
        sort=sort,
        order=order,
        limit=limit,
        offset=offset,
        repository=repository,
    )


def build_preview_detail(
    preview_run_id: str = Path(alias="previewRunId"),
    status_filter: str | None = None,
    q: str | None = None,
    sort: str = "status",
    order: str = "asc",
    limit: int = 100,
    offset: int = 0,
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


@router.get("/{previewRunId}", response_model=PreviewRunDetailResponse)
def preview_detail(
    preview_run_id: str = Path(alias="previewRunId"),
    status_filter: PreviewItemStatus | None = Query(default=None, alias="status"),
    q: str | None = None,
    sort: Literal["status", "fileDate", "filename", "uploadRows", "modifiedAt"] = "status",
    order: Literal["asc", "desc"] = "asc",
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    repository: PreviewRepository = Depends(get_preview_repository),
) -> PreviewRunDetailResponse:
    return build_preview_detail(
        preview_run_id,
        status_filter=None if status_filter is None else status_filter.value,
        q=q,
        sort=sort,
        order=order,
        limit=limit,
        offset=offset,
        repository=repository,
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
