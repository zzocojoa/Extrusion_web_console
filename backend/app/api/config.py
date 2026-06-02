from fastapi import APIRouter, Depends, HTTPException

from backend.app.core.settings import Settings, get_settings
from backend.app.db.audit_repository import AuditRepository
from backend.app.schemas.config import ConfigResponse, ConfigSaveRequest, ConfigSaveResponse
from backend.app.services.config_service import ConfigSaveError, ConfigService

router = APIRouter(prefix="/api/config", tags=["config"])


def get_config_audit_repository(settings: Settings = Depends(get_settings)) -> AuditRepository:
    return AuditRepository(settings.state_db_path)


def get_config_service(
    settings: Settings = Depends(get_settings),
    audit_repository: AuditRepository = Depends(get_config_audit_repository),
) -> ConfigService:
    return ConfigService(settings, audit_repository)


@router.get("", response_model=ConfigResponse)
def get_config(service: ConfigService = Depends(get_config_service)) -> ConfigResponse:
    return service.get_config()


@router.put("", response_model=ConfigSaveResponse)
def save_config(request: ConfigSaveRequest, service: ConfigService = Depends(get_config_service)) -> ConfigSaveResponse:
    try:
        return service.save_config(request.values, actor=request.actor)
    except ConfigSaveError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"reason": exc.error_code, "keys": exc.keys},
        ) from exc
