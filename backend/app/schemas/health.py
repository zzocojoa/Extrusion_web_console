from pydantic import BaseModel


class LanSecurityResponse(BaseModel):
    enabled: bool
    status: str
    bind_host_class: str
    cors_origin_classes: list[str]
    shared_local_token_allowed: bool
    reasons: list[str]


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str
    localhost_only: bool
    lan_security: LanSecurityResponse
    startup_id: str
    started_at: str
    process_id: int
