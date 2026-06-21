from fastapi import APIRouter, Depends

from backend.app.core.lan_security import lan_security_state
from backend.app.core.runtime_identity import PROCESS_ID, PROCESS_STARTED_AT, PROCESS_STARTUP_ID
from backend.app.core.settings import Settings, get_settings
from backend.app.schemas.health import LanSecurityResponse
from backend.app.schemas.health import HealthResponse

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("", response_model=HealthResponse)
def get_health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    lan_state = lan_security_state(settings)
    return HealthResponse(
        status="ok",
        service=settings.service_name,
        version=settings.version,
        environment=settings.environment,
        localhost_only=lan_state.status == "localhost_only",
        lan_security=LanSecurityResponse(
            enabled=lan_state.enabled,
            status=lan_state.status,
            bind_host_class=lan_state.bind_host_class,
            cors_origin_classes=list(lan_state.cors_origin_classes),
            shared_local_token_allowed=lan_state.shared_local_token_allowed,
            reasons=list(lan_state.reasons),
        ),
        startup_id=PROCESS_STARTUP_ID,
        started_at=PROCESS_STARTED_AT.isoformat(),
        process_id=PROCESS_ID,
    )
