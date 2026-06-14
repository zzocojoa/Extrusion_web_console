import type { DashboardResponse } from "../pages/dashboard/dashboardTypes";
import { unknownStateContext, type StateContext } from "./stateContext";

function coerceStateContext(raw: any, fallback: StateContext = unknownStateContext): StateContext {
  const source = raw ?? fallback;
  return {
    contextClass: source.contextClass ?? source.context_class ?? fallback.contextClass,
    label: source.label ?? fallback.label,
    storageStatus: source.storageStatus ?? source.storage_status ?? fallback.storageStatus,
    source: source.source ?? fallback.source,
  };
}

function toCamelDashboard(raw: any): DashboardResponse {
  const stateContext = coerceStateContext(raw.stateContext ?? raw.state_context);
  const currentJob = raw.currentJob ?? raw.current_job;
  const recentJobs = raw.recentJobs ?? raw.recent_jobs ?? [];
  return {
    overall: raw.overall,
    stateContext,
    topbarChips: raw.topbarChips ?? raw.topbar_chips,
    statusMatrix: raw.statusMatrix ?? raw.status_matrix,
    currentJob: currentJob
      ? {
          ...currentJob,
          stateContext: coerceStateContext(currentJob.stateContext ?? currentJob.state_context, stateContext),
        }
      : null,
    recentJobs: recentJobs.map((job: any) => ({
      ...job,
      stateContext: coerceStateContext(job.stateContext ?? job.state_context, stateContext),
    })),
    runtimeChecks: raw.runtimeChecks ?? raw.runtime_checks,
    warningQueue: raw.warningQueue ?? raw.warning_queue,
    auditSummary: raw.auditSummary ?? raw.audit_summary,
  };
}

export async function fetchDashboard(): Promise<DashboardResponse> {
  const response = await fetch("/api/dashboard");
  if (!response.ok) {
    throw new Error("Dashboard load failed");
  }
  return toCamelDashboard(await response.json());
}
