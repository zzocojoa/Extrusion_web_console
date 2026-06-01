from typing import Literal

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


OverallSystemState = Literal["ready", "attention", "blocked", "running"]
StatusTone = Literal["ready", "running", "attention", "risk", "failed", "blocked", "muted"]
UploadJobStatus = Literal[
    "queued",
    "running",
    "succeeded",
    "partial_failed",
    "failed",
    "pausing",
    "paused",
    "cancelling",
    "cancelled",
    "interrupted",
]


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class DashboardOverall(ApiModel):
    state: OverallSystemState
    title: str
    message: str
    action: Literal[
        "preview",
        "start_upload",
        "retry_failed",
        "open_job",
        "start_supabase",
        "open_logs",
    ] | None = None


class TopbarStatusChip(ApiModel):
    id: Literal["supabase", "upload", "grafana", "state_store"]
    label: str
    tone: StatusTone
    value: str


class DashboardLinkAction(ApiModel):
    label: str
    href: str | None = None
    target: Literal["_self", "_blank"] | None = None


class StatusMatrixItem(ApiModel):
    id: Literal["upload", "supabase", "storage", "grafana", "state_store"]
    label: str
    tone: StatusTone
    value: str
    detail: str
    action: DashboardLinkAction | None = None


class CurrentJobSummary(ApiModel):
    job_id: str
    status: UploadJobStatus
    progress_pct: int
    files_done: int
    files_total: int
    rows_sent: int
    started_at: str
    latest_message: str


class RecentJobRow(ApiModel):
    job_id: str
    status: UploadJobStatus
    started_at: str
    mode: Literal["upload", "retry_failed"]
    files_done: int
    files_total: int
    rows_sent: int
    failure_count: int
    warning_count: int
    latest_message: str


class RuntimeCheckRow(ApiModel):
    id: Literal["supabase", "database", "edge_function", "wsl_storage", "grafana", "state_store"]
    label: str
    tone: StatusTone
    detail: str
    last_checked_at: str
    href: str | None = None


class WarningQueueRow(ApiModel):
    id: Literal["partial_overlap", "failed_retry", "risky", "stale_preview", "supabase_unreachable"]
    label: str
    tone: StatusTone
    count: int
    impact: str


class AuditSummaryRow(ApiModel):
    audit_id: str
    time: str
    result: Literal["success", "failure", "cancelled", "blocked"]
    action: str
    actor: str
    summary: str
    job_id: str | None = None


class DashboardResponse(ApiModel):
    overall: DashboardOverall
    topbar_chips: list[TopbarStatusChip]
    status_matrix: list[StatusMatrixItem]
    current_job: CurrentJobSummary | None
    recent_jobs: list[RecentJobRow]
    runtime_checks: list[RuntimeCheckRow]
    warning_queue: list[WarningQueueRow]
    audit_summary: list[AuditSummaryRow]
