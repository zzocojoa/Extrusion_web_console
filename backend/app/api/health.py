from fastapi import APIRouter, Depends

from backend.app.core.settings import Settings, get_settings
from backend.app.schemas.health import HealthResponse

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("", response_model=HealthResponse)
def get_health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.service_name,
        version=settings.version,
        environment=settings.environment,
        localhost_only=settings.host == "127.0.0.1",
    )
