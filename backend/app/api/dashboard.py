from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends

from backend.app.core.settings import Settings, get_settings
from backend.app.core.state_context import StateContext, build_state_context
from backend.app.db.audit_repository import AuditLogFilters, AuditOrder, AuditRepository, AuditSort
from backend.app.db.upload_job_repository import ACTIVE_JOB_STATUSES, UploadJobRepository
from backend.app.schemas.dashboard import (
    AuditSummaryRow,
    CurrentJobSummary,
    DashboardLinkAction,
    DashboardOverall,
    DashboardResponse,
    RecentJobRow,
    RuntimeCheckRow,
    StatusMatrixItem,
    TopbarStatusChip,
    WarningQueueRow,
)
from backend.app.schemas.runtime import RuntimeServiceStatus, RuntimeStatusResponse
from backend.app.services.command_runner import AllowedCommandRunner
from backend.app.services.runtime_readiness import RuntimeReadinessService

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

NON_CORE_OBSERVABILITY_CAVEAT = (
    "Non-core observability caveat only; core upload is not blocked when API, DB, Edge, Preview, and Audit are normal."
)


def get_dashboard_upload_repository(settings: Settings = Depends(get_settings)) -> UploadJobRepository | None:
    if not Path(settings.state_db_path).exists():
        return None
    return UploadJobRepository(settings.state_db_path)


def get_dashboard_audit_repository(settings: Settings = Depends(get_settings)) -> AuditRepository | None:
    if not Path(settings.state_db_path).exists():
        return None
    return AuditRepository(settings.state_db_path)


def get_dashboard_runtime_status(settings: Settings = Depends(get_settings)) -> RuntimeStatusResponse | None:
    try:
        runner = AllowedCommandRunner(
            settings.local_supabase_project_path,
            settings.runtime_command_timeout_seconds,
            project_id=settings.local_supabase_project_id,
        )
        return RuntimeReadinessService(settings, runner).check_status()
    except Exception:  # noqa: BLE001 - dashboard must degrade to unknown, not fail the first screen.
        return None


def build_dashboard(
    settings: Settings,
    upload_repository: UploadJobRepository | None,
    audit_repository: AuditRepository | None,
    runtime_status: RuntimeStatusResponse | None,
) -> DashboardResponse:
    now = _now()
    jobs, _ = upload_repository.list_jobs(limit=5) if upload_repository is not None else ([], 0)
    latest_job = jobs[0] if jobs else None
    runtime = _runtime_summary(runtime_status, settings)
    state_context = build_state_context(settings)
    state_store_ready = state_context.storage_status == "present"

    return DashboardResponse(
        overall=_overall(latest_job, runtime["supabase_tone"]),
        state_context=state_context.to_api(),
        topbar_chips=[
            TopbarStatusChip(id="supabase", label="Supabase", tone=runtime["supabase_tone"], value=runtime["supabase_value"]),
            TopbarStatusChip(id="upload", label="Upload", tone=_upload_tone(latest_job), value=_upload_value(latest_job)),
            TopbarStatusChip(id="grafana", label="Grafana", tone=runtime["grafana_tone"], value=runtime["grafana_value"]),
            TopbarStatusChip(id="state_store", label="State Store", tone="ready" if state_store_ready else "muted", value=state_context.label),
        ],
        status_matrix=[
            StatusMatrixItem(
                id="upload",
                label="Latest Upload",
                tone=_upload_tone(latest_job),
                value=_upload_value(latest_job),
                detail=_upload_detail(latest_job),
            ),
            StatusMatrixItem(
                id="supabase",
                label="Local Supabase",
                tone=runtime["supabase_tone"],
                value=runtime["supabase_value"],
                detail=runtime["supabase_detail"],
            ),
            StatusMatrixItem(
                id="storage",
                label="WSL / Docker",
                tone=runtime["storage_tone"],
                value=runtime["storage_value"],
                detail=runtime["storage_detail"],
            ),
            StatusMatrixItem(
                id="grafana",
                label="Grafana",
                tone=runtime["grafana_tone"],
                value=runtime["grafana_value"],
                detail=runtime["grafana_detail"],
                action=DashboardLinkAction(label="Open Grafana", href=settings.grafana_url, target="_blank"),
            ),
            StatusMatrixItem(
                id="state_store",
                label="State Store",
                tone="ready" if state_store_ready else "muted",
                value=state_context.label,
                detail=_state_context_detail(state_context),
            ),
        ],
        current_job=_current_job(latest_job, state_context),
        recent_jobs=[_recent_job(row, state_context) for row in jobs],
        runtime_checks=_runtime_checks(runtime_status, settings, now, state_context),
        warning_queue=_warning_queue(latest_job, runtime["supabase_tone"]),
        audit_summary=_audit_summary(audit_repository),
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _overall(row: Any | None, supabase_tone: str) -> DashboardOverall:
    if supabase_tone == "blocked":
        return DashboardOverall(
            state="blocked",
            title="Upload blocked",
            message="Local Supabase core runtime is not reachable.",
            action="start_supabase",
        )
    if row is None:
        return DashboardOverall(
            state="ready",
            title="No upload job recorded",
            message="Dashboard is connected to API mode, but no persisted upload job exists in the active state store.",
            action="preview",
        )
    status = str(row["status"])
    if status in ACTIVE_JOB_STATUSES:
        return DashboardOverall(
            state="running",
            title="Upload job is running",
            message=_job_count_message(row),
            action="open_job",
        )
    if status == "succeeded":
        return DashboardOverall(
            state="ready",
            title="Latest upload succeeded",
            message=_job_count_message(row),
            action="open_job",
        )
    return DashboardOverall(
        state="attention",
        title="Latest upload needs review",
        message=_job_count_message(row),
        action="open_logs",
    )


def _job_count_message(row: Any) -> str:
    return (
        f"Status {row['status']}: processed {int(row['processed_rows'] or 0)}, "
        f"uploaded {int(row['uploaded_rows'] or 0)}, accepted {int(row['inserted_rows'] or 0)} rows."
    )


def _upload_tone(row: Any | None) -> str:
    if row is None:
        return "muted"
    status = str(row["status"])
    if status in ACTIVE_JOB_STATUSES:
        return "running"
    if status == "succeeded":
        return "ready"
    if status in {"failed", "interrupted"}:
        return "failed"
    if status in {"partial_failed", "cancelled"}:
        return "attention"
    return "muted"


def _upload_value(row: Any | None) -> str:
    if row is None:
        return "No jobs"
    return str(row["status"])


def _upload_detail(row: Any | None) -> str:
    if row is None:
        return "No persisted upload job found in the active state store."
    return f"{int(row['succeeded_files'] or 0)}/{int(row['total_files'] or 0)} files, {int(row['uploaded_rows'] or 0)} uploaded rows."


def _state_context_detail(state_context: StateContext) -> str:
    return f"Context class {state_context.context_class}; storage {state_context.storage_status}."


def _progress_pct(row: Any) -> int:
    total_rows = int(row["total_rows"] or 0)
    processed_rows = int(row["processed_rows"] or 0)
    if str(row["status"]) == "succeeded":
        return 100
    if total_rows > 0:
        return max(0, min(100, round(processed_rows * 100 / total_rows)))
    total_files = int(row["total_files"] or 0)
    done_files = _done_files(row)
    if total_files > 0:
        return max(0, min(100, round(done_files * 100 / total_files)))
    return 0


def _done_files(row: Any) -> int:
    return int(row["succeeded_files"] or 0) + int(row["failed_files"] or 0) + int(row["cancelled_files"] or 0)


def _mode(row: Any) -> str:
    return "retry_failed" if str(row["mode"]) == "retry_failed" else "upload"


def _started_at(row: Any) -> str:
    return str(row["started_at"] or row["requested_at"] or row["created_at"])


def _current_job(row: Any | None, state_context: StateContext) -> CurrentJobSummary | None:
    if row is None:
        return None
    return CurrentJobSummary(
        job_id=str(row["job_id"]),
        status=str(row["status"]),
        progress_pct=_progress_pct(row),
        files_done=_done_files(row),
        files_total=int(row["total_files"] or 0),
        rows_sent=int(row["uploaded_rows"] or 0),
        started_at=_started_at(row),
        latest_message=_job_count_message(row),
        state_context=state_context.to_api(),
    )


def _recent_job(row: Any, state_context: StateContext) -> RecentJobRow:
    return RecentJobRow(
        job_id=str(row["job_id"]),
        status=str(row["status"]),
        started_at=_started_at(row),
        mode=_mode(row),
        files_done=_done_files(row),
        files_total=int(row["total_files"] or 0),
        rows_sent=int(row["uploaded_rows"] or 0),
        failure_count=int(row["failed_files"] or 0),
        warning_count=int(row["warning_count"] or 0),
        latest_message=_job_count_message(row),
        state_context=state_context.to_api(),
    )


def _runtime_summary(runtime_status: RuntimeStatusResponse | None, settings: Settings) -> dict[str, str]:
    if runtime_status is None:
        return {
            "supabase_tone": "muted",
            "supabase_value": "unknown",
            "supabase_detail": "Runtime status is not available.",
            "storage_tone": "muted",
            "storage_value": "unknown",
            "storage_detail": "Docker/WSL status is not available.",
            "grafana_tone": "muted",
            "grafana_value": "unknown",
            "grafana_detail": settings.grafana_url,
        }
    core_ready = _core_runtime_ready(runtime_status)
    supabase_tone = "ready" if core_ready else "blocked"
    storage_ready = runtime_status.docker.status == RuntimeServiceStatus.ready and runtime_status.wsl.status == RuntimeServiceStatus.ready
    grafana_tone = _observability_tone(runtime_status.grafana.status)
    return {
        "supabase_tone": supabase_tone,
        "supabase_value": "Core runtime OK" if core_ready else runtime_status.overall_status.value,
        "supabase_detail": f"API {runtime_status.api.status.value}, DB {runtime_status.db.status.value}, Studio {runtime_status.studio.status.value}, Edge {runtime_status.edge_runtime.status.value}.",
        "storage_tone": "ready" if storage_ready else "attention",
        "storage_value": f"Docker {runtime_status.docker.status.value}",
        "storage_detail": f"WSL {runtime_status.wsl.status.value}, CLI {runtime_status.supabase_cli.status.value}.",
        "grafana_tone": grafana_tone,
        "grafana_value": runtime_status.grafana.status.value,
        "grafana_detail": _non_core_observability_detail(runtime_status.grafana.detail, runtime_status.grafana.status, core_ready),
    }


def _core_runtime_ready(runtime_status: RuntimeStatusResponse) -> bool:
    return (
        runtime_status.api.status == RuntimeServiceStatus.ready
        and runtime_status.db.status == RuntimeServiceStatus.ready
        and runtime_status.studio.status == RuntimeServiceStatus.ready
        and runtime_status.edge_runtime.status == RuntimeServiceStatus.ready
    )


def _non_core_observability_detail(detail: str, status: RuntimeServiceStatus, core_ready: bool) -> str:
    if core_ready and status != RuntimeServiceStatus.ready:
        return f"{detail} {NON_CORE_OBSERVABILITY_CAVEAT}"
    return detail


def _runtime_tone(status: RuntimeServiceStatus) -> str:
    if status == RuntimeServiceStatus.ready:
        return "ready"
    if status in {RuntimeServiceStatus.unknown, RuntimeServiceStatus.stopped, RuntimeServiceStatus.missing}:
        return "muted"
    if status == RuntimeServiceStatus.unreachable:
        return "blocked"
    return "attention"


def _observability_tone(status: RuntimeServiceStatus) -> str:
    if status == RuntimeServiceStatus.ready:
        return "ready"
    if status in {RuntimeServiceStatus.starting, RuntimeServiceStatus.stopping}:
        return "running"
    if status in {
        RuntimeServiceStatus.unknown,
        RuntimeServiceStatus.stopped,
        RuntimeServiceStatus.missing,
        RuntimeServiceStatus.unreachable,
        RuntimeServiceStatus.unhealthy,
    }:
        return "attention"
    return "muted"


def _runtime_checks(runtime_status: RuntimeStatusResponse | None, settings: Settings, now: str, state_context: StateContext) -> list[RuntimeCheckRow]:
    if runtime_status is None:
        return [
            RuntimeCheckRow(id="supabase", label="Local Supabase", tone="muted", detail="Runtime status is not available.", last_checked_at=now),
            RuntimeCheckRow(id="edge_function", label="Edge Function", tone="muted", detail="Runtime status is not available.", last_checked_at=now),
            RuntimeCheckRow(id="grafana", label="Grafana", tone="muted", detail=settings.grafana_url, last_checked_at=now, href=settings.grafana_url),
            RuntimeCheckRow(id="vector", label="Vector", tone="muted", detail="Runtime status is not available.", last_checked_at=now),
            RuntimeCheckRow(id="state_context", label="State Context", tone="ready" if state_context.storage_status == "present" else "muted", detail=_state_context_detail(state_context), last_checked_at=now),
        ]
    checked_at = runtime_status.checked_at.isoformat()
    core_ready = _core_runtime_ready(runtime_status)
    return [
        RuntimeCheckRow(
            id="supabase",
            label="Local Supabase",
            tone=_runtime_tone(runtime_status.api.status),
            detail=f"API {runtime_status.api.status.value}.",
            last_checked_at=checked_at,
        ),
        RuntimeCheckRow(
            id="database",
            label="Database",
            tone=_runtime_tone(runtime_status.db.status),
            detail=f"DB {runtime_status.db.status.value}.",
            last_checked_at=checked_at,
        ),
        RuntimeCheckRow(
            id="edge_function",
            label="Edge Function",
            tone=_runtime_tone(runtime_status.edge_runtime.status),
            detail=f"Edge {runtime_status.edge_runtime.status.value}.",
            last_checked_at=checked_at,
        ),
        RuntimeCheckRow(
            id="grafana",
            label="Grafana",
            tone=_observability_tone(runtime_status.grafana.status),
            detail=_non_core_observability_detail(runtime_status.grafana.detail, runtime_status.grafana.status, core_ready),
            last_checked_at=checked_at,
            href=settings.grafana_url,
        ),
        RuntimeCheckRow(
            id="vector",
            label="Vector",
            tone=_observability_tone(runtime_status.vector.status),
            detail=_non_core_observability_detail(runtime_status.vector.detail, runtime_status.vector.status, core_ready),
            last_checked_at=checked_at,
        ),
        RuntimeCheckRow(
            id="state_context",
            label="State Context",
            tone="ready" if state_context.storage_status == "present" else "muted",
            detail=_state_context_detail(state_context),
            last_checked_at=checked_at,
        ),
    ]


def _warning_queue(row: Any | None, supabase_tone: str) -> list[WarningQueueRow]:
    failed_count = 0 if row is None else int(row["failed_files"] or 0)
    warning_count = 0 if row is None else int(row["warning_count"] or 0)
    return [
        WarningQueueRow(
            id="failed_retry",
            label="Failed files",
            tone="attention" if failed_count else "ready",
            count=failed_count,
            impact="Retry review is needed." if failed_count else "No failed files in the latest job.",
        ),
        WarningQueueRow(
            id="risky",
            label="Job warnings",
            tone="attention" if warning_count else "ready",
            count=warning_count,
            impact="Review latest job warnings." if warning_count else "No warnings recorded for the latest job.",
        ),
        WarningQueueRow(
            id="supabase_unreachable",
            label="Runtime gate",
            tone="blocked" if supabase_tone == "blocked" else "ready",
            count=1 if supabase_tone == "blocked" else 0,
            impact="Local Supabase core runtime is not reachable." if supabase_tone == "blocked" else "Runtime gate is not blocking Dashboard review.",
        ),
    ]


def _audit_summary(repository: AuditRepository | None) -> list[AuditSummaryRow]:
    if repository is None:
        return []
    page = repository.list_audit_logs(AuditLogFilters(limit=5, sort=AuditSort.ts, order=AuditOrder.desc))
    rows: list[AuditSummaryRow] = []
    for row in page.rows:
        summary = str(row["result"])
        if row["error_code"]:
            summary = f"{summary}: {row['error_code']}"
        rows.append(
            AuditSummaryRow(
                audit_id=str(row["audit_id"]),
                time=str(row["ts"]),
                result=str(row["result"]),
                action=str(row["action"]),
                actor=str(row["actor"]),
                summary=summary,
                job_id=row["job_id"],
            )
        )
    return rows


@router.get("", response_model=DashboardResponse)
def get_dashboard(
    settings: Settings = Depends(get_settings),
    upload_repository: UploadJobRepository | None = Depends(get_dashboard_upload_repository),
    audit_repository: AuditRepository | None = Depends(get_dashboard_audit_repository),
    runtime_status: RuntimeStatusResponse | None = Depends(get_dashboard_runtime_status),
) -> DashboardResponse:
    return build_dashboard(settings, upload_repository, audit_repository, runtime_status)


@router.get("/summary", response_model=DashboardResponse)
def get_dashboard_summary(
    settings: Settings = Depends(get_settings),
    upload_repository: UploadJobRepository | None = Depends(get_dashboard_upload_repository),
    audit_repository: AuditRepository | None = Depends(get_dashboard_audit_repository),
    runtime_status: RuntimeStatusResponse | None = Depends(get_dashboard_runtime_status),
) -> DashboardResponse:
    return build_dashboard(settings, upload_repository, audit_repository, runtime_status)
