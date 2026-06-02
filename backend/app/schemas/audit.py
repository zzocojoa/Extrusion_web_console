from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field

from backend.app.schemas.upload_preview import ApiModel


class AuditResult(str, Enum):
    success = "success"
    failure = "failure"
    cancelled = "cancelled"
    blocked = "blocked"


class AuditSort(str, Enum):
    ts = "ts"
    action = "action"
    result = "result"
    target_type = "targetType"


class AuditOrder(str, Enum):
    asc = "asc"
    desc = "desc"


class AuditLogDto(ApiModel):
    audit_id: int
    ts: datetime
    actor: str
    action: str
    target_type: str
    target_id: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)
    result: AuditResult
    error_code: str | None = None
    error_message: str | None = None
    job_id: str | None = None
    request_id: str | None = None
    created_at: datetime


class AuditPageDto(ApiModel):
    limit: int
    offset: int
    total_items: int
    has_next: bool
    has_previous: bool


class AuditFilterEchoDto(ApiModel):
    from_ts: datetime | None = None
    to_ts: datetime | None = None
    action: str | None = None
    result: AuditResult | None = None
    target_type: str | None = None
    target_id: str | None = None
    job_id: str | None = None
    request_id: str | None = None
    q: str | None = None
    sort: AuditSort = AuditSort.ts
    order: AuditOrder = AuditOrder.desc


class AuditLogListResponse(ApiModel):
    items: list[AuditLogDto]
    page: AuditPageDto
    filters: AuditFilterEchoDto
