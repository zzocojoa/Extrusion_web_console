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
    PreviewApprovalScope,
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
from backend.app.services.preview_safety import (
    OPERATIONAL_PLC_SOURCE_CLASSES,
    source_gate_snapshot,
    source_path_class,
)
from backend.app.services.upload_preview import PreviewService

router = APIRouter(prefix="/api/upload/preview", tags=["upload-preview"])
executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="upload-preview")


def is_large_preview_range(request: PreviewCreateRequest) -> bool:
    if request.range_mode in {
        PreviewRangeMode.last_2_days,
        PreviewRangeMode.last_7_days,
        PreviewRangeMode.last_30_days,
        PreviewRangeMode.folder_all,
    }:
        return True
    if request.range_mode == PreviewRangeMode.custom and request.start_date and request.end_date:
        return (request.end_date - request.start_date).days >= 1
    return False


def preview_auto_safe_mode_reason(request: PreviewCreateRequest, settings: Settings) -> str | None:
    if request.options.profile != PreviewProfile.default:
        return None
    if PreviewSource.plc not in request.sources:
        return None
    if source_path_class(settings.plc_data_dir) in OPERATIONAL_PLC_SOURCE_CLASSES:
        return "operational_source_class"
    if is_large_preview_range(request):
        return "large_preview_range"
    return None


def resolve_preview_auto_safe_mode(request: PreviewCreateRequest, settings: Settings) -> PreviewCreateRequest:
    if preview_auto_safe_mode_reason(request, settings) is None:
        return request

    options = request.options.model_dump(mode="json", by_alias=True)
    options["profile"] = PreviewProfile.large_source_operational.value
    return request.model_copy(update={"options": PreviewOptions.model_validate(options)})


def source_classes_for_request(settings: Settings, request: PreviewCreateRequest) -> dict[str, str]:
    snapshot = source_gate_snapshot(settings)
    classes: dict[str, str] = {}
    for source in request.sources:
        source_snapshot = snapshot.get(source.value)
        if isinstance(source_snapshot, dict):
            classes[source.value] = str(source_snapshot.get("pathClass") or "missing")
        else:
            classes[source.value] = "missing"
    return classes


def actual_preview_approval_scope(settings: Settings, request: PreviewCreateRequest) -> dict[str, Any]:
    return {
        "sourceClasses": source_classes_for_request(settings, request),
        "rangeMode": request.range_mode.value,
        "startDate": request.start_date.isoformat() if request.start_date else None,
        "endDate": request.end_date.isoformat() if request.end_date else None,
        "appliedProfile": request.options.profile.value,
    }


def expected_preview_approval_scope(scope: PreviewApprovalScope | None) -> dict[str, Any] | None:
    if scope is None:
        return None
    return {
        "sourceClasses": {
            source.value if isinstance(source, PreviewSource) else str(source): source_class
            for source, source_class in scope.expected_source_classes.items()
        },
        "rangeMode": scope.expected_range_mode.value,
        "startDate": scope.expected_start_date.isoformat() if scope.expected_start_date else None,
        "endDate": scope.expected_end_date.isoformat() if scope.expected_end_date else None,
        "appliedProfile": scope.expected_applied_profile.value,
    }


def preview_approval_mismatch_fields(
    *,
    expected: dict[str, Any] | None,
    actual: dict[str, Any],
) -> list[str]:
    if expected is None:
        return ["approvalScope"]
    fields: list[str] = []
    for key in ("rangeMode", "startDate", "endDate", "appliedProfile"):
        if expected.get(key) != actual.get(key):
            fields.append(key)
    expected_sources = expected.get("sourceClasses")
    actual_sources = actual.get("sourceClasses")
    if expected_sources != actual_sources:
        fields.append("sourceClasses")
    return fields


def build_preview_config_snapshot(
    settings: Settings,
    *,
    requested_profile: PreviewProfile,
    applied_profile: PreviewProfile,
    auto_profile_reason: str | None,
    approval_scope: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "plcDataDir": settings.plc_data_dir,
        "temperatureDataDir": settings.temperature_data_dir,
        "supabaseDbUrlConfigured": bool(settings.supabase_db_url),
        "previewGate": source_gate_snapshot(settings),
        "previewProfile": {
            "requestedProfile": requested_profile.value,
            "appliedProfile": applied_profile.value,
            "autoProfileReason": auto_profile_reason,
        },
        "previewApprovalScope": approval_scope,
    }


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


def run_dto(row: Any, row_estimates_by_status: dict[str, int] | None = None) -> PreviewRunDto:
    config_snapshot = parse_json_dict(row["config_snapshot_json"])
    options = parse_json_dict(row["options_json"])
    profile_snapshot = config_snapshot.get("previewProfile", {})
    if not isinstance(profile_snapshot, dict):
        profile_snapshot = {}
    row_estimates = row_estimates_by_status or {}
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
            target_rows=row_estimates.get("target", 0),
            partial_overlap_rows=row_estimates.get("partial_overlap", 0),
            db_matched_rows=row["db_match_count"],
        ),
        warnings=[],
        requested_profile=profile_snapshot.get("requestedProfile") or options.get("profile"),
        applied_profile=profile_snapshot.get("appliedProfile") or options.get("profile"),
        auto_profile_reason=profile_snapshot.get("autoProfileReason"),
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

    requested_profile = request.options.profile
    auto_profile_reason = preview_auto_safe_mode_reason(request, settings)
    request = resolve_preview_auto_safe_mode(request, settings)
    actual_approval_scope = actual_preview_approval_scope(settings, request)
    expected_approval_scope = expected_preview_approval_scope(request.approval_scope)
    mismatch_fields = preview_approval_mismatch_fields(
        expected=expected_approval_scope,
        actual=actual_approval_scope,
    )
    if mismatch_fields:
        reason = (
            "preview_approval_scope_required"
            if request.approval_scope is None
            else "preview_approval_scope_mismatch"
        )
        audit_preview_scope_blocked(
            audit_repository,
            request=request,
            reason=reason,
            expected_scope=expected_approval_scope,
            actual_scope=actual_approval_scope,
            mismatch_fields=mismatch_fields,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "reason": reason,
                "mismatchFields": mismatch_fields,
                "actualApprovalScope": actual_approval_scope,
            },
        )
    preview_run_id = f"prv_{uuid4().hex[:12]}"
    active_run_id = repository.create_run_if_no_active(
        preview_run_id=preview_run_id,
        range_mode=request.range_mode.value,
        start_date=request.start_date.isoformat() if request.start_date else None,
        end_date=request.end_date.isoformat() if request.end_date else None,
        sources=[source.value for source in request.sources],
        options=request.options.model_dump(mode="json", by_alias=True),
        config_snapshot=build_preview_config_snapshot(
            settings,
            requested_profile=requested_profile,
            applied_profile=request.options.profile,
            auto_profile_reason=auto_profile_reason,
            approval_scope={
                "expected": expected_approval_scope,
                "actual": actual_approval_scope,
                "mismatchFields": [],
            },
        ),
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
                "approvalScope": {
                    "expected": expected_approval_scope,
                    "actual": actual_approval_scope,
                    "mismatchFields": [],
                },
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


def audit_preview_scope_blocked(
    audit_repository: AuditRepository,
    *,
    request: PreviewCreateRequest,
    reason: str,
    expected_scope: dict[str, Any] | None,
    actual_scope: dict[str, Any],
    mismatch_fields: list[str],
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
            "reasonCode": reason,
            "requestedFilters": safe_requested_filters(request),
            "approvalScope": {
                "expected": expected_scope,
                "actual": actual_scope,
                "mismatchFields": sorted(mismatch_fields),
            },
        },
        result=AuditResult.blocked,
        error_code=reason,
        error_message="Upload Preview approval scope did not match the current request.",
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
    row_estimates = repository.upload_row_estimates_by_status(preview_run_id)
    return PreviewRunDetailResponse(
        run=run_dto(row, row_estimates),
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
