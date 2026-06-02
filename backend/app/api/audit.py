from datetime import datetime

from fastapi import APIRouter, Depends, Query

from backend.app.core.settings import Settings, get_settings
from backend.app.db.audit_repository import AuditLogFilters, AuditRepository, decode_params_json, sanitize_text
from backend.app.schemas.audit import (
    AuditFilterEchoDto,
    AuditLogDto,
    AuditLogListResponse,
    AuditOrder,
    AuditPageDto,
    AuditResult,
    AuditSort,
)

router = APIRouter(prefix="/api/audit", tags=["audit"])


def get_audit_repository(settings: Settings = Depends(get_settings)) -> AuditRepository:
    return AuditRepository(settings.state_db_path)


@router.get("", response_model=AuditLogListResponse)
def list_audit_logs(
    from_ts: datetime | None = Query(default=None, alias="fromTs"),
    to_ts: datetime | None = Query(default=None, alias="toTs"),
    action: str | None = Query(default=None, min_length=1, max_length=120),
    result: AuditResult | None = None,
    target_type: str | None = Query(default=None, alias="targetType", min_length=1, max_length=80),
    target_id: str | None = Query(default=None, alias="targetId", min_length=1, max_length=160),
    job_id: str | None = Query(default=None, alias="jobId", min_length=1, max_length=160),
    request_id: str | None = Query(default=None, alias="requestId", min_length=1, max_length=160),
    q: str | None = Query(default=None, min_length=1, max_length=200),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    sort: AuditSort = AuditSort.ts,
    order: AuditOrder = AuditOrder.desc,
    repository: AuditRepository = Depends(get_audit_repository),
) -> AuditLogListResponse:
    filters = AuditLogFilters(
        from_ts=from_ts,
        to_ts=to_ts,
        action=action,
        result=result,
        target_type=target_type,
        target_id=target_id,
        job_id=job_id,
        request_id=request_id,
        q=q,
        limit=limit,
        offset=offset,
        sort=sort,
        order=order,
    )
    result_page = repository.list_audit_logs(filters)
    items = [
        AuditLogDto(
            audit_id=int(row["audit_id"]),
            ts=row["ts"],
            actor=str(row["actor"]),
            action=str(row["action"]),
            target_type=str(row["target_type"]),
            target_id=row["target_id"],
            params=decode_params_json(row["params_json_redacted"]),
            result=row["result"],
            error_code=row["error_code"],
            error_message=sanitize_text(row["error_message"]),
            job_id=row["job_id"],
            request_id=row["request_id"],
            created_at=row["created_at"],
        )
        for row in result_page.rows
    ]
    return AuditLogListResponse(
        items=items,
        page=AuditPageDto(
            limit=limit,
            offset=offset,
            total_items=result_page.total_items,
            has_next=offset + limit < result_page.total_items,
            has_previous=offset > 0,
        ),
        filters=AuditFilterEchoDto(
            from_ts=from_ts,
            to_ts=to_ts,
            action=action,
            result=result,
            target_type=target_type,
            target_id=target_id,
            job_id=job_id,
            request_id=request_id,
            q=q,
            sort=sort,
            order=order,
        ),
    )
