from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Path, status

from backend.app.core.settings import Settings, get_settings
from backend.app.db.audit_repository import AuditRepository
from backend.app.db.upload_delete_repository import UploadDeleteRepository
from backend.app.schemas.upload_delete import (
    DeleteJobCreateRequest,
    DeleteJobCreateResponse,
    DeleteJobDto,
    DeleteJobLatestResponse,
    DeletePreflightRequest,
    DeletePreflightResponse,
    DeleteReconcileRequest,
    DeleteReconcileResponse,
    DeleteRunStatus,
)
from backend.app.services.upload_delete import DeleteRejectedError, UploadDeleteService


router = APIRouter(prefix="/api/upload/delete", tags=["upload-delete"])


def get_upload_delete_repository(settings: Settings = Depends(get_settings)) -> UploadDeleteRepository:
    return UploadDeleteRepository(settings.state_db_path)


def get_upload_delete_audit_repository(settings: Settings = Depends(get_settings)) -> AuditRepository:
    return AuditRepository(settings.state_db_path)


def get_upload_delete_service(
    settings: Settings = Depends(get_settings),
    repository: UploadDeleteRepository = Depends(get_upload_delete_repository),
    audit_repository: AuditRepository = Depends(get_upload_delete_audit_repository),
) -> UploadDeleteService:
    return UploadDeleteService(
        settings=settings,
        repository=repository,
        audit_repository=audit_repository,
    )


@router.post("/preflight", response_model=DeletePreflightResponse)
def create_delete_preflight(
    request: DeletePreflightRequest,
    service: UploadDeleteService = Depends(get_upload_delete_service),
) -> DeletePreflightResponse:
    return service.create_preflight(request)


@router.get("/jobs/latest", response_model=DeleteJobLatestResponse)
def latest_delete_job(
    repository: UploadDeleteRepository = Depends(get_upload_delete_repository),
) -> DeleteJobLatestResponse:
    row = repository.get_latest_run()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No delete job exists")
    return DeleteJobLatestResponse(
        job=delete_job_dto(row),
        active_delete_blocker=repository.get_active_delete_run_id() is not None,
    )


@router.post("/jobs", response_model=DeleteJobCreateResponse)
def start_delete_job(
    request: DeleteJobCreateRequest,
    service: UploadDeleteService = Depends(get_upload_delete_service),
) -> DeleteJobCreateResponse:
    try:
        return service.start_delete(request)
    except DeleteRejectedError as exc:
        detail = {"reason": exc.reason}
        detail.update(exc.detail)
        raise HTTPException(status_code=exc.status_code, detail=detail) from exc


@router.post("/jobs/{deleteRunId}/reconcile", response_model=DeleteReconcileResponse)
def reconcile_delete_job(
    request: DeleteReconcileRequest,
    delete_run_id: str = Path(alias="deleteRunId"),
    service: UploadDeleteService = Depends(get_upload_delete_service),
) -> DeleteReconcileResponse:
    try:
        return service.reconcile(
            delete_run_id,
            acknowledge_retry=request.acknowledge_reconciliation_retry,
        )
    except DeleteRejectedError as exc:
        detail = {"reason": exc.reason}
        detail.update(exc.detail)
        raise HTTPException(status_code=exc.status_code, detail=detail) from exc


def delete_job_dto(row) -> DeleteJobDto:
    return DeleteJobDto(
        delete_run_id=row["delete_run_id"],
        preflight_id=row["preflight_id"],
        preview_run_id=row["preview_run_id"],
        status=DeleteRunStatus(row["status"]),
        expected_delete_keys=int(row["expected_key_count"] or 0),
        deleted_keys=int(row["deleted_key_count"] or 0),
        rollback_ready=bool(row["rollback_ready"]),
        recovery_required=bool(row["recovery_required"]),
        db_fingerprint_hash=row["db_fingerprint_hash"],
        selection_hash=row["selection_hash"],
        keyset_hash=row["keyset_hash"],
        error_code=row["error_code"],
        error_message=row["error_message"],
        started_at=_dt(row["started_at"]),
        finished_at=_dt(row["finished_at"]),
    )


def _dt(value: str | None) -> datetime | None:
    return None if value is None else datetime.fromisoformat(value)
