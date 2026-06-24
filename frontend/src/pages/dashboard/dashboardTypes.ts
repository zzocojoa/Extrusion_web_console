import type { StateContext } from "../../api/stateContext";

export type OverallSystemState = "ready" | "attention" | "blocked" | "running";

export type StatusTone =
  | "ready"
  | "running"
  | "attention"
  | "risk"
  | "failed"
  | "blocked"
  | "muted";

export type UploadJobStatus =
  | "queued"
  | "running"
  | "succeeded"
  | "partial_failed"
  | "failed"
  | "pausing"
  | "paused"
  | "cancelling"
  | "cancelled"
  | "interrupted";

export interface DashboardResponse {
  overall: DashboardOverall;
  stateContext: StateContext;
  topbarChips: TopbarStatusChip[];
  statusMatrix: StatusMatrixItem[];
  currentJob: CurrentJobSummary | null;
  recentJobs: RecentJobRow[];
  runtimeChecks: RuntimeCheckRow[];
  warningQueue: WarningQueueRow[];
  auditSummary: AuditSummaryRow[];
}

export interface DashboardOverall {
  state: OverallSystemState;
  title: string;
  message: string;
  action:
    | "preview"
    | "start_upload"
    | "retry_failed"
    | "open_job"
    | "start_supabase"
    | "open_logs"
    | null;
}

export type DashboardOverallAction = NonNullable<DashboardOverall["action"]>;

export interface TopbarStatusChip {
  id: "supabase" | "upload" | "grafana" | "state_store";
  label: string;
  tone: StatusTone;
  value: string;
}

export interface DashboardLinkAction {
  label: string;
  href?: string;
  target?: "_self" | "_blank";
}

export interface StatusMatrixItem {
  id: "upload" | "supabase" | "storage" | "grafana" | "state_store";
  label: string;
  tone: StatusTone;
  value: string;
  detail: string;
  action?: DashboardLinkAction;
}

export interface CurrentJobSummary {
  jobId: string;
  status: UploadJobStatus;
  progressPct: number;
  filesDone: number;
  filesTotal: number;
  rowsSent: number;
  startedAt: string;
  latestMessage: string;
  stateContext: StateContext;
}

export interface RecentJobRow {
  jobId: string;
  status: UploadJobStatus;
  startedAt: string;
  mode: "upload" | "retry_failed";
  filesDone: number;
  filesTotal: number;
  rowsSent: number;
  failureCount: number;
  warningCount: number;
  latestMessage: string;
  stateContext: StateContext;
}

export interface RuntimeCheckRow {
  id: "supabase" | "database" | "edge_function" | "wsl_storage" | "grafana" | "vector" | "state_store" | "state_context" | "containers";
  label: string;
  tone: StatusTone;
  detail: string;
  lastCheckedAt: string;
  href?: string;
}

export interface WarningQueueRow {
  id: "partial_overlap" | "failed_retry" | "failed_files" | "risky" | "job_warnings" | "stale_preview" | "supabase_unreachable" | "runtime_gate";
  label: string;
  tone: StatusTone;
  count: number;
  impact: string;
}

export interface AuditSummaryRow {
  auditId: string;
  time: string;
  result: "success" | "failure" | "cancelled" | "blocked";
  action: string;
  actor: string;
  summary: string;
  jobId?: string;
}
