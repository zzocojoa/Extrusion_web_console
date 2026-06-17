import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Query, status
from starlette.responses import StreamingResponse

from backend.app.core.settings import Settings, get_settings
from backend.app.core.target_class import build_upload_target_preflight
from backend.app.db.upload_job_repository import (
    ACTIVE_JOB_STATUSES,
    UploadJobRepository,
    decode_json,
)
from backend.app.schemas.upload_jobs import (
    JobEventCursor,
    JobEventDto,
    JobEventLevel,
    RetryFailedRequest,
    UploadJobCreateRequest,
    UploadJobCreateResponse,
    UploadJobDetailResponse,
    UploadJobDto,
    UploadJobFileDto,
    UploadJobListResponse,
    UploadJobMode,
    UploadJobStatus,
    UploadJobSummary,
)
from backend.app.services.preview_safety import source_gate_snapshot
from backend.app.services.upload_jobs import UploadJobService

router = APIRouter(prefix="/api/upload/jobs", tags=["upload-jobs"])
executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="upload-job")


def get_upload_job_repository(settings: Settings = Depends(get_settings)) -> UploadJobRepository:
    return UploadJobRepository(settings.state_db_path)


def _dt(value: str | None) -> datetime | None:
    return None if value is None else datetime.fromisoformat(value)


def job_dto(row: Any) -> UploadJobDto:
    return UploadJobDto(
        job_id=row["job_id"],
        preview_run_id=row["preview_run_id"],
        retry_of_job_id=row["retry_of_job_id"],
        mode=UploadJobMode(row["mode"]),
        status=UploadJobStatus(row["status"]),
        requested_at=datetime.fromisoformat(row["requested_at"]),
        started_at=_dt(row["started_at"]),
        finished_at=_dt(row["finished_at"]),
        actor=row["actor"],
        summary=UploadJobSummary(
            total_files=row["total_files"],
            succeeded_files=row["succeeded_files"],
            failed_files=row["failed_files"],
            cancelled_files=row["cancelled_files"],
            total_rows=row["total_rows"],
            processed_rows=row["processed_rows"],
            uploaded_rows=row["uploaded_rows"],
            accepted_rows=row["inserted_rows"],
            inserted_rows=row["inserted_rows"],
            warning_count=row["warning_count"],
        ),
        error_code=row["error_code"],
        error_message=row["error_message"],
    )


def file_dto(row: Any) -> UploadJobFileDto:
    return UploadJobFileDto(
        job_file_id=row["job_file_id"],
        job_id=row["job_id"],
        preview_item_id=row["preview_item_id"],
        file_key=row["file_key"],
        folder_label=row["folder_label"],
        folder_path=row["folder_path"],
        filename=row["filename"],
        path=row["path"],
        kind=row["kind"],
        file_date=row["file_date"],
        file_signature=row["file_signature"],
        status=row["status"],
        row_count=row["row_count"],
        processed_rows=row["processed_rows"],
        uploaded_rows=row["uploaded_rows"],
        accepted_rows=row["inserted_rows"],
        inserted_rows=row["inserted_rows"],
        resume_offset=row["resume_offset"],
        retry_count=row["retry_count"],
        started_at=_dt(row["started_at"]),
        finished_at=_dt(row["finished_at"]),
        last_error_code=row["last_error_code"],
        last_error_message=row["last_error_message"],
    )


def event_dto(row: Any) -> JobEventDto:
    return JobEventDto(
        event_id=row["event_id"],
        job_id=row["job_id"],
        seq=row["seq"],
        ts=datetime.fromisoformat(row["ts"]),
        level=JobEventLevel(row["level"]),
        event_type=row["event_type"],
        message=row["message"],
        job_file_id=row["job_file_id"],
        data=decode_json(row["data_json"], {}),
    )


def build_job_detail(
    job_id: str,
    repository: UploadJobRepository,
    *,
    event_tail: int = 100,
) -> UploadJobDetailResponse:
    row = repository.get_job(job_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload job not found")
    latest_seq = repository.latest_event_seq(job_id)
    after_seq = max(0, latest_seq - event_tail)
    return UploadJobDetailResponse(
        job=job_dto(row),
        files=[file_dto(file_row) for file_row in repository.list_job_files(job_id)],
        events=[event_dto(event_row) for event_row in repository.list_events(job_id, after_seq=after_seq, limit=event_tail)],
        event_cursor=JobEventCursor(latest_seq=latest_seq),
    )


def _validate_upload_config(settings: Settings) -> None:
    if not settings.upload_edge_url or not settings.supabase_anon_key:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"reason": "upload_config_missing"},
        )


def audit_blocked(
    repository: UploadJobRepository,
    *,
    action: str,
    target_type: str,
    target_id: str | None,
    reason: str,
    params: dict[str, Any] | None = None,
    job_id: str | None = None,
    message: str | None = None,
) -> None:
    repository.append_audit(
        action=action,
        target_type=target_type,
        target_id=target_id,
        params=params or {},
        result="blocked",
        error_code=reason,
        error_message=message or reason,
        job_id=job_id,
    )


def reject_with_audit(
    repository: UploadJobRepository,
    *,
    status_code: int,
    action: str,
    target_type: str,
    target_id: str | None,
    reason: str,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    detail_extra: dict[str, Any] | None = None,
) -> None:
    audit_blocked(
        repository,
        action=action,
        target_type=target_type,
        target_id=target_id,
        reason=reason,
        params=params,
    )
    detail = {"reason": reason}
    if detail_extra:
        detail.update(detail_extra)
    raise HTTPException(status_code=status_code, detail=detail, headers=headers)


def ensure_upload_config(settings: Settings, repository: UploadJobRepository, action: str, params: dict[str, Any]) -> None:
    if not settings.upload_edge_url or not settings.supabase_anon_key:
        reject_with_audit(
            repository,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            action=action,
            target_type="upload_job",
            target_id=None,
            reason="upload_config_missing",
            params=params,
        )
    target_preflight = build_upload_target_preflight(settings)
    if not target_preflight.passed:
        reject_with_audit(
            repository,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            action=action,
            target_type="upload_job",
            target_id=None,
            reason="upload_target_preflight_failed",
            params={**params, "targetClassPreflight": target_preflight.to_api()},
            detail_extra={"targetClassPreflight": target_preflight.to_api()},
        )


@router.post("", response_model=UploadJobCreateResponse, status_code=status.HTTP_202_ACCEPTED)
def create_upload_job(
    request: UploadJobCreateRequest,
    settings: Settings = Depends(get_settings),
    repository: UploadJobRepository = Depends(get_upload_job_repository),
) -> UploadJobCreateResponse:
    if request.mode != UploadJobMode.preview_targets:
        reject_with_audit(
            repository,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            action="upload.start",
            target_type="preview_run",
            target_id=request.preview_run_id,
            reason="unsupported_upload_mode",
            params={"previewRunId": request.preview_run_id, "mode": request.mode.value},
        )
    approval_params = {
        "previewRunId": request.preview_run_id,
        "expectedTargetRows": request.expected_target_rows,
        "expectedTargetFiles": request.expected_target_files,
    }
    if request.expected_target_rows is None or request.expected_target_rows <= 0:
        reject_with_audit(
            repository,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            action="upload.start",
            target_type="preview_run",
            target_id=request.preview_run_id,
            reason="expected_target_rows_required",
            params=approval_params,
        )
    if request.expected_target_files is not None and request.expected_target_files <= 0:
        reject_with_audit(
            repository,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            action="upload.start",
            target_type="preview_run",
            target_id=request.preview_run_id,
            reason="expected_target_files_invalid",
            params=approval_params,
        )
    expected_target_rows = request.expected_target_rows
    assert expected_target_rows is not None
    ensure_upload_config(settings, repository, "upload.start", approval_params)
    job_id = f"upl_{uuid4().hex[:12]}"
    result = repository.create_job_from_preview(
        job_id=job_id,
        preview_run_id=request.preview_run_id,
        expected_target_rows=expected_target_rows,
        expected_target_files=request.expected_target_files,
        options=request.options.model_dump(mode="json", by_alias=True),
        config_snapshot={
            "uploadEdgeUrlConfigured": bool(settings.upload_edge_url),
            "supabaseAnonKeyConfigured": bool(settings.supabase_anon_key),
            "targetClassPreflight": build_upload_target_preflight(settings).to_api(),
            "enableSmartSync": False,
        },
        preview_gate_snapshot=source_gate_snapshot(settings),
    )
    if result.active_job_id is not None:
        reject_with_audit(
            repository,
            status_code=status.HTTP_409_CONFLICT,
            action="upload.start",
            target_type="preview_run",
            target_id=request.preview_run_id,
            reason="active_upload_job",
            params={**approval_params, "activeJobId": result.active_job_id},
            headers={"Location": f"/api/upload/jobs/{result.active_job_id}"},
            detail_extra={"activeJobId": result.active_job_id},
        )
    if not result.created:
        reason = result.rejection_reason or "preview_not_uploadable"
        status_code = status.HTTP_404_NOT_FOUND if reason == "preview_missing" else status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_extra: dict[str, Any] = {}
        if result.rejection_status:
            detail_extra["status"] = result.rejection_status
        if result.db_status:
            detail_extra["dbStatus"] = result.db_status
        if result.file_count:
            detail_extra["actualTargetFiles"] = result.file_count
        if result.upload_row_count:
            detail_extra["actualTargetRows"] = result.upload_row_count
        reject_with_audit(
            repository,
            status_code=status_code,
            action="upload.start",
            target_type="preview_run",
            target_id=request.preview_run_id,
            reason=reason,
            params={
                **approval_params,
                "actualTargetFiles": result.file_count,
                "actualTargetRows": result.upload_row_count,
            },
            detail_extra=detail_extra,
        )
    executor.submit(UploadJobService(settings, repository).run_job, job_id)
    return UploadJobCreateResponse(
        job_id=job_id,
        status=UploadJobStatus.queued,
        detail_url=f"/api/upload/jobs/{job_id}",
        events_url=f"/api/upload/jobs/{job_id}/events",
    )


@router.get("", response_model=UploadJobListResponse)
def list_upload_jobs(
    status_filter: UploadJobStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    repository: UploadJobRepository = Depends(get_upload_job_repository),
) -> UploadJobListResponse:
    rows, total = repository.list_jobs(
        status=None if status_filter is None else status_filter.value,
        limit=limit,
        offset=offset,
    )
    return UploadJobListResponse(jobs=[job_dto(row) for row in rows], total=total)


@router.get("/latest", response_model=UploadJobDetailResponse)
def latest_upload_job(repository: UploadJobRepository = Depends(get_upload_job_repository)) -> UploadJobDetailResponse:
    row = repository.get_latest_job()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No upload job exists")
    return build_job_detail(row["job_id"], repository)


@router.get("/{jobId}", response_model=UploadJobDetailResponse)
def upload_job_detail(
    job_id: str = Path(alias="jobId"),
    repository: UploadJobRepository = Depends(get_upload_job_repository),
) -> UploadJobDetailResponse:
    return build_job_detail(job_id, repository)


@router.post("/{jobId}/retry", response_model=UploadJobCreateResponse, status_code=status.HTTP_202_ACCEPTED)
def retry_upload_job(
    request: RetryFailedRequest,
    job_id: str = Path(alias="jobId"),
    settings: Settings = Depends(get_settings),
    repository: UploadJobRepository = Depends(get_upload_job_repository),
) -> UploadJobCreateResponse:
    ensure_upload_config(settings, repository, "upload.retry", {"retryOfJobId": job_id})
    retry_job_id = f"upl_{uuid4().hex[:12]}"
    active_job_id, file_count = repository.create_retry_job(
        job_id=retry_job_id,
        source_job_id=job_id,
        include_interrupted=request.include_interrupted,
        include_cancelled=request.include_cancelled,
        options=request.options.model_dump(mode="json", by_alias=True),
        config_snapshot={
            "uploadEdgeUrlConfigured": bool(settings.upload_edge_url),
            "supabaseAnonKeyConfigured": bool(settings.supabase_anon_key),
            "targetClassPreflight": build_upload_target_preflight(settings).to_api(),
            "enableSmartSync": False,
        },
    )
    if active_job_id is not None:
        reject_with_audit(
            repository,
            status_code=status.HTTP_409_CONFLICT,
            action="upload.retry",
            target_type="upload_job",
            target_id=job_id,
            reason="active_upload_job",
            params={"retryOfJobId": job_id, "activeJobId": active_job_id},
            headers={"Location": f"/api/upload/jobs/{active_job_id}"},
            detail_extra={"activeJobId": active_job_id},
        )
    if file_count < 0:
        reject_with_audit(
            repository,
            status_code=status.HTTP_409_CONFLICT,
            action="upload.retry",
            target_type="upload_job",
            target_id=job_id,
            reason="source_job_not_retryable",
            params={"retryOfJobId": job_id},
        )
    if file_count == 0:
        reject_with_audit(
            repository,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            action="upload.retry",
            target_type="upload_job",
            target_id=job_id,
            reason="no_retryable_files",
            params={"retryOfJobId": job_id},
        )
    executor.submit(UploadJobService(settings, repository).run_job, retry_job_id)
    return UploadJobCreateResponse(
        job_id=retry_job_id,
        status=UploadJobStatus.queued,
        detail_url=f"/api/upload/jobs/{retry_job_id}",
        events_url=f"/api/upload/jobs/{retry_job_id}/events",
    )


@router.post("/{jobId}/pause", response_model=UploadJobDetailResponse)
def pause_upload_job(
    job_id: str = Path(alias="jobId"),
    repository: UploadJobRepository = Depends(get_upload_job_repository),
) -> UploadJobDetailResponse:
    next_status = repository.request_pause(job_id)
    if next_status is None:
        reject_with_audit(
            repository,
            status_code=status.HTTP_404_NOT_FOUND,
            action="upload.pause",
            target_type="upload_job",
            target_id=job_id,
            reason="upload_job_not_found",
        )
    if next_status not in {UploadJobStatus.pausing, UploadJobStatus.paused}:
        reject_with_audit(
            repository,
            status_code=status.HTTP_409_CONFLICT,
            action="upload.pause",
            target_type="upload_job",
            target_id=job_id,
            reason="invalid_upload_job_state",
            params={"status": next_status.value},
            detail_extra={"status": next_status.value},
        )
    return build_job_detail(job_id, repository)


@router.post("/{jobId}/resume", response_model=UploadJobDetailResponse)
def resume_upload_job(
    job_id: str = Path(alias="jobId"),
    repository: UploadJobRepository = Depends(get_upload_job_repository),
) -> UploadJobDetailResponse:
    next_status = repository.resume_job(job_id)
    if next_status is None:
        reject_with_audit(
            repository,
            status_code=status.HTTP_404_NOT_FOUND,
            action="upload.resume",
            target_type="upload_job",
            target_id=job_id,
            reason="upload_job_not_found",
        )
    if next_status != UploadJobStatus.running:
        reject_with_audit(
            repository,
            status_code=status.HTTP_409_CONFLICT,
            action="upload.resume",
            target_type="upload_job",
            target_id=job_id,
            reason="invalid_upload_job_state",
            params={"status": next_status.value},
            detail_extra={"status": next_status.value},
        )
    return build_job_detail(job_id, repository)


@router.post("/{jobId}/cancel", response_model=UploadJobDetailResponse)
def cancel_upload_job(
    job_id: str = Path(alias="jobId"),
    repository: UploadJobRepository = Depends(get_upload_job_repository),
) -> UploadJobDetailResponse:
    next_status = repository.request_cancel(job_id)
    if next_status is None:
        reject_with_audit(
            repository,
            status_code=status.HTTP_404_NOT_FOUND,
            action="upload.cancel",
            target_type="upload_job",
            target_id=job_id,
            reason="upload_job_not_found",
        )
    if next_status != UploadJobStatus.cancelling:
        reject_with_audit(
            repository,
            status_code=status.HTTP_409_CONFLICT,
            action="upload.cancel",
            target_type="upload_job",
            target_id=job_id,
            reason="invalid_upload_job_state",
            params={"status": next_status.value},
            detail_extra={"status": next_status.value},
        )
    return build_job_detail(job_id, repository)


@router.get("/{jobId}/events")
def upload_job_events(
    job_id: str = Path(alias="jobId"),
    after_seq: int = Query(default=0, ge=0, alias="afterSeq"),
    tail: int = Query(default=100, ge=1, le=500),
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
    repository: UploadJobRepository = Depends(get_upload_job_repository),
) -> StreamingResponse:
    if repository.get_job(job_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload job not found")
    start_after = after_seq
    if last_event_id and last_event_id.isdigit():
        start_after = max(start_after, int(last_event_id))

    def stream():
        seq = max(0, start_after)
        sent_any = False
        while True:
            events = repository.list_events(job_id, after_seq=seq, limit=tail)
            for row in events:
                seq = int(row["seq"])
                sent_any = True
                payload = event_dto(row).model_dump(mode="json", by_alias=True)
                yield f"id: {seq}\n"
                yield f"event: {row['event_type']}\n"
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
            job = repository.get_job(job_id)
            if job is None or (job["status"] not in ACTIVE_JOB_STATUSES and sent_any and not events):
                yield ": closed\n\n"
                break
            yield ": heartbeat\n\n"
            time.sleep(1)

    return StreamingResponse(stream(), media_type="text/event-stream")
