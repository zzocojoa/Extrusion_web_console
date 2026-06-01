import type { DashboardResponse } from "../pages/dashboard/dashboardTypes";

function toCamelDashboard(raw: any): DashboardResponse {
  return {
    overall: raw.overall,
    topbarChips: raw.topbarChips ?? raw.topbar_chips,
    statusMatrix: raw.statusMatrix ?? raw.status_matrix,
    currentJob: raw.currentJob ?? raw.current_job,
    recentJobs: raw.recentJobs ?? raw.recent_jobs,
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
