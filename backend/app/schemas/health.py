from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str
    localhost_only: bool
    startup_id: str
    started_at: str
    process_id: int
