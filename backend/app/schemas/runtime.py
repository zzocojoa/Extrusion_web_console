from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field

from backend.app.schemas.state_context import StateContextDto, unknown_state_context
from backend.app.schemas.upload_preview import ApiModel


class RuntimeOverallStatus(str, Enum):
    ready = "ready"
    running = "running"
    attention = "attention"
    blocked = "blocked"
    unknown = "unknown"


class RuntimeServiceStatus(str, Enum):
    ready = "ready"
    starting = "starting"
    stopping = "stopping"
    stopped = "stopped"
    unreachable = "unreachable"
    missing = "missing"
    unhealthy = "unhealthy"
    unknown = "unknown"


class RuntimeOperationKind(str, Enum):
    start = "start"
    stop = "stop"


class RuntimeOperationStatus(str, Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    blocked = "blocked"
    timed_out = "timed_out"
    cancelled = "cancelled"
    interrupted = "interrupted"


class RuntimeEventLevel(str, Enum):
    info = "info"
    warning = "warning"
    error = "error"


class RuntimeContainerStatus(ApiModel):
    name: str
    required: bool
    exists: bool
    running: bool
    status: RuntimeServiceStatus
    status_text: str | None = None


class RuntimePortStatus(ApiModel):
    name: str
    host: str = "127.0.0.1"
    port: int
    status: RuntimeServiceStatus
    detail: str


class RuntimeProbeStatus(ApiModel):
    name: str
    status: RuntimeServiceStatus
    detail: str
    url: str | None = None


class RuntimeConfigItem(ApiModel):
    key: str
    label: str
    value: str
    source: str
    secret: bool = False


class RuntimeOperationDto(ApiModel):
    operation_id: str
    kind: RuntimeOperationKind
    status: RuntimeOperationStatus
    requested_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    actor: str
    error_code: str | None = None
    error_message: str | None = None


class RuntimeEventDto(ApiModel):
    event_id: int
    operation_id: str
    seq: int
    ts: datetime
    level: RuntimeEventLevel
    event_type: str
    message: str
    data: dict[str, Any] = Field(default_factory=dict)


class RuntimeStatusResponse(ApiModel):
    overall_status: RuntimeOverallStatus
    reason_code: str
    reason_text: str
    checked_at: datetime
    project_path: str
    project_id: str
    docker: RuntimeProbeStatus
    wsl: RuntimeProbeStatus
    supabase_cli: RuntimeProbeStatus
    api: RuntimePortStatus
    db: RuntimePortStatus
    studio: RuntimePortStatus
    edge_runtime: RuntimeProbeStatus
    grafana: RuntimeProbeStatus
    containers: list[RuntimeContainerStatus]
    config: list[RuntimeConfigItem]
    state_context: StateContextDto = Field(default_factory=unknown_state_context)
    active_operation: RuntimeOperationDto | None = None


class RuntimeOperationCreateResponse(ApiModel):
    operation_id: str
    status: RuntimeOperationStatus
    detail_url: str


class RuntimeOperationDetailResponse(ApiModel):
    operation: RuntimeOperationDto
    events: list[RuntimeEventDto]
