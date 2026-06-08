from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, status

from backend.app.core.settings import Settings, get_settings
from backend.app.db.preview_repository import PreviewRepository
from backend.app.db.runtime_repository import RuntimeRepository, decode_json
from backend.app.db.upload_job_repository import UploadJobRepository
from backend.app.schemas.runtime import (
    RuntimeEventDto,
    RuntimeEventLevel,
    RuntimeOperationCreateResponse,
    RuntimeOperationDetailResponse,
    RuntimeOperationKind,
    RuntimeOperationStatus,
    RuntimeStatusResponse,
)
from backend.app.services.command_runner import AllowedCommandRunner
from backend.app.services.runtime_control import RuntimeConflictError, RuntimeControlService, operation_dto

router = APIRouter(prefix="/api/runtime", tags=["runtime"])
executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="runtime-control")


def get_runtime_repository(settings: Settings = Depends(get_settings)) -> RuntimeRepository:
    return RuntimeRepository(settings.state_db_path)


def get_runtime_preview_repository(settings: Settings = Depends(get_settings)) -> PreviewRepository:
    return PreviewRepository(settings.state_db_path)


def get_runtime_upload_repository(settings: Settings = Depends(get_settings)) -> UploadJobRepository:
    return UploadJobRepository(settings.state_db_path)


def get_command_runner(settings: Settings = Depends(get_settings)) -> AllowedCommandRunner:
    return AllowedCommandRunner(
        settings.local_supabase_project_path,
        settings.runtime_command_timeout_seconds,
        project_id=settings.local_supabase_project_id,
    )


def get_runtime_service(
    settings: Settings = Depends(get_settings),
    runtime_repository: RuntimeRepository = Depends(get_runtime_repository),
    preview_repository: PreviewRepository = Depends(get_runtime_preview_repository),
    upload_repository: UploadJobRepository = Depends(get_runtime_upload_repository),
    runner: AllowedCommandRunner = Depends(get_command_runner),
) -> RuntimeControlService:
    return RuntimeControlService(
        settings=settings,
        runtime_repository=runtime_repository,
        preview_repository=preview_repository,
        upload_repository=upload_repository,
        runner=runner,
    )


@router.get("/local-supabase", response_model=RuntimeStatusResponse)
def local_supabase_status(service: RuntimeControlService = Depends(get_runtime_service)) -> RuntimeStatusResponse:
    return service.status()


@router.post("/local-supabase/start", response_model=RuntimeOperationCreateResponse, status_code=status.HTTP_202_ACCEPTED)
def start_local_supabase(service: RuntimeControlService = Depends(get_runtime_service)) -> RuntimeOperationCreateResponse:
    return _queue_runtime_operation(service, RuntimeOperationKind.start)


@router.post("/local-supabase/stop", response_model=RuntimeOperationCreateResponse, status_code=status.HTTP_202_ACCEPTED)
def stop_local_supabase(service: RuntimeControlService = Depends(get_runtime_service)) -> RuntimeOperationCreateResponse:
    return _queue_runtime_operation(service, RuntimeOperationKind.stop)


@router.get("/operations/{operationId}", response_model=RuntimeOperationDetailResponse)
def runtime_operation_detail(
    operation_id: str = Path(..., alias="operationId"),
    repository: RuntimeRepository = Depends(get_runtime_repository),
) -> RuntimeOperationDetailResponse:
    row = repository.get_operation(operation_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Runtime operation not found")
    return RuntimeOperationDetailResponse(
        operation=operation_dto(row),
        events=[event_dto(event_row) for event_row in repository.list_events(operation_id)],
    )


def _queue_runtime_operation(service: RuntimeControlService, kind: RuntimeOperationKind) -> RuntimeOperationCreateResponse:
    try:
        operation_id = service.queue_operation(kind)
    except RuntimeConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"reason": exc.reason, "activeId": exc.active_id},
        ) from exc
    executor.submit(service.run_operation, operation_id)
    return RuntimeOperationCreateResponse(
        operation_id=operation_id,
        status=RuntimeOperationStatus.queued,
        detail_url=f"/api/runtime/operations/{operation_id}",
    )


def event_dto(row: Any) -> RuntimeEventDto:
    return RuntimeEventDto(
        event_id=row["event_id"],
        operation_id=row["operation_id"],
        seq=row["seq"],
        ts=datetime.fromisoformat(row["ts"]),
        level=RuntimeEventLevel(row["level"]),
        event_type=row["event_type"],
        message=row["message"],
        data=decode_json(row["data_json"], {}),
    )
