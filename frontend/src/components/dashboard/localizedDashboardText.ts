import type { RuntimePortStatus, RuntimeProbeStatus, RuntimeStatusResponse } from "../../api/runtime";
import type { StateContext } from "../../api/stateContext";
import type { JobEvent } from "../../api/uploadJobs";
import type {
  AuditSummaryRow,
  DashboardOverall,
  StatusMatrixItem,
  TopbarStatusChip,
  WarningQueueRow,
} from "../../pages/dashboard/dashboardTypes";

export type Translate = (key: string, options?: Record<string, unknown>) => string;

export function stateContextLabel(stateContext: StateContext | null | undefined, t: Translate): string {
  const contextClass = stateContext?.contextClass ?? "unknown";
  const key = `stateContext.class.${contextClass}`;
  const translated = t(key);
  if (translated !== key) return translated;
  return stateContext?.label ?? t("stateContext.class.unknown");
}

export function storageStatusLabel(status: string | null | undefined, t: Translate): string {
  const key = `stateContext.storage.${status ?? "unknown"}`;
  const translated = t(key);
  return translated === key ? status ?? t("stateContext.storage.unknown") : translated;
}

export function dashboardChipLabel(chip: TopbarStatusChip, t: Translate): string {
  return t(`dashboard.status.${chip.id}`, { defaultValue: chip.label });
}

export function dashboardChipValue(chip: TopbarStatusChip, stateContext: StateContext, t: Translate): string {
  if (chip.id === "state_store") return stateContextLabel(stateContext, t);
  return translateStatusValue(chip.value, t);
}

export function dashboardItemLabel(item: StatusMatrixItem, t: Translate): string {
  return t(`dashboard.matrix.${item.id}.label`, { defaultValue: item.label });
}

export function dashboardItemValue(item: StatusMatrixItem, stateContext: StateContext, t: Translate): string {
  if (item.id === "state_store") return stateContextLabel(stateContext, t);
  return translateStatusValue(item.value, t);
}

export function dashboardItemDetail(item: StatusMatrixItem, stateContext: StateContext, t: Translate): string {
  if (item.id === "state_store") {
    return t("dashboard.messages.stateContextDetail", {
      contextClass: stateContextLabel(stateContext, t),
      storageStatus: storageStatusLabel(stateContext.storageStatus, t),
    });
  }
  return localizeDiagnosticMessage(item.detail, t);
}

export function dashboardActionLabel(action: StatusMatrixItem["action"], t: Translate): string | null {
  if (!action) return null;
  if (action.label === "Open Grafana") return t("dashboard.actions.openGrafana");
  return action.label;
}

export function dashboardOverallTitle(overall: DashboardOverall, t: Translate): string {
  const keyByTitle: Record<string, string> = {
    "No upload job recorded": "dashboard.overall.noJob.title",
    "Upload job is running": "dashboard.overall.running.title",
    "Latest upload succeeded": "dashboard.overall.succeeded.title",
    "Latest upload needs review": "dashboard.overall.review.title",
    "Upload ready": "dashboard.overall.ready.title",
    "Needs attention": "dashboard.overall.attention.title",
    "Upload blocked": "dashboard.overall.blocked.title",
    "Upload running": "dashboard.overall.running.title",
  };
  const key = keyByTitle[overall.title];
  return key ? t(key) : overall.title;
}

export function dashboardOverallMessage(overall: DashboardOverall, t: Translate): string {
  if (overall.message === "Dashboard is connected to API mode, but no persisted upload job exists in the active state store.") {
    return t("dashboard.overall.noJob.message");
  }
  return localizeDiagnosticMessage(overall.message, t);
}

export function warningLabel(row: WarningQueueRow, t: Translate): string {
  return t(`dashboard.warnings.rows.${row.id}.label`, { defaultValue: row.label });
}

export function warningImpact(row: WarningQueueRow, t: Translate): string {
  return t(`dashboard.warnings.rows.${row.id}.${row.count > 0 ? "impact" : "empty"}`, {
    defaultValue: row.impact,
    count: row.count,
  });
}

export function auditSummaryText(row: AuditSummaryRow, t: Translate): string {
  const [result, errorCode] = row.summary.split(":").map((value) => value.trim());
  const resultKey = `logs.audit.results.${result}`;
  const resultText = t(resultKey);
  const safeResult = resultText === resultKey ? result : resultText;
  return errorCode ? t("dashboard.audit.summaryWithCode", { result: safeResult, errorCode }) : safeResult;
}

export function runtimeReasonText(runtimeStatus: RuntimeStatusResponse, t: Translate): string {
  const key = `runtime.reason.${runtimeStatus.reasonCode}`;
  const translated = t(key);
  if (translated !== key) return translated;
  return localizeDiagnosticMessage(runtimeStatus.reasonText, t);
}

export function runtimeServiceDetail(service: RuntimePortStatus | RuntimeProbeStatus, t: Translate): string {
  const message = localizeDiagnosticMessage(service.detail, t);
  if (message !== service.detail) return message;
  return runtimeStatusLabel(service.detail, t);
}

export function runtimeStateContextDetail(stateContext: StateContext, t: Translate): string {
  return t("runtime.stateContext.detail", {
    contextClass: stateContextLabel(stateContext, t),
    storageStatus: storageStatusLabel(stateContext.storageStatus, t),
  });
}

export function runtimeStatusLabel(status: string, t: Translate): string {
  const normalized = status.trim().toLowerCase().replace(/\s+/g, "_");
  const key = `runtime.serviceStatus.${normalized}`;
  const translated = t(key);
  return translated === key ? status : translated;
}

export function localizeJobEvent(event: Pick<JobEvent, "message">, t: Translate): string {
  const statusMatch = event.message.match(/^Upload job finished with status ([a-z_]+)\.$/);
  if (statusMatch) {
    return t("logs.job.events.jobFinished", {
      status: jobStatusLabel(statusMatch[1], t),
    });
  }

  const progressWithFile = event.message.match(/^Progress (.+): (\d+)\/(\d+)\.$/);
  if (progressWithFile) {
    return t("logs.job.events.fileProgressWithName", {
      filename: progressWithFile[1],
      processed: progressWithFile[2],
      total: progressWithFile[3],
    });
  }

  const progressOnly = event.message.match(/^Progress (\d+)\/(\d+)\.$/);
  if (progressOnly) {
    return t("logs.job.events.fileProgress", {
      processed: progressOnly[1],
      total: progressOnly[2],
    });
  }

  const completedWithFile = event.message.match(/^Completed (.+)\.$/);
  if (completedWithFile) {
    return t("logs.job.events.fileCompleted", {
      filename: completedWithFile[1],
    });
  }

  return localizeDiagnosticMessage(event.message, t);
}

export function localizeDiagnosticMessage(message: string | null | undefined, t: Translate): string {
  if (!message) return "";

  const jobCount = message.match(/^Status ([a-z_]+): processed (\d+), uploaded (\d+), accepted (\d+) rows\.$/);
  if (jobCount) {
    return t("dashboard.messages.jobCount", {
      status: jobStatusLabel(jobCount[1], t),
      processed: formatInt(jobCount[2]),
      uploaded: formatInt(jobCount[3]),
      accepted: formatInt(jobCount[4]),
    });
  }

  const uploadDetail = message.match(/^(\d+)\/(\d+) files, (\d+) uploaded rows\.$/);
  if (uploadDetail) {
    return t("dashboard.messages.uploadDetail", {
      done: formatInt(uploadDetail[1]),
      total: formatInt(uploadDetail[2]),
      uploaded: formatInt(uploadDetail[3]),
    });
  }

  const stateContext = message.match(/^Context class ([^;]+); storage ([^.]+)\.$/);
  if (stateContext) {
    return t("dashboard.messages.stateContextDetail", {
      contextClass: stateContext[1],
      storageStatus: storageStatusLabel(stateContext[2], t),
    });
  }

  const apiDbEdge = message.match(/^API ([a-z_ ]+), DB ([a-z_ ]+), Edge ([a-z_ ]+)\.$/);
  if (apiDbEdge) {
    return t("dashboard.messages.apiDbEdge", {
      api: runtimeStatusLabel(apiDbEdge[1], t),
      db: runtimeStatusLabel(apiDbEdge[2], t),
      edge: runtimeStatusLabel(apiDbEdge[3], t),
    });
  }

  const wslCli = message.match(/^WSL ([a-z_ ]+), CLI ([a-z_ ]+)\.$/);
  if (wslCli) {
    return t("dashboard.messages.wslCli", {
      wsl: runtimeStatusLabel(wslCli[1], t),
      cli: runtimeStatusLabel(wslCli[2], t),
    });
  }

  const dockerStatus = message.match(/^Docker ([a-z_ ]+)$/);
  if (dockerStatus) {
    return t("dashboard.messages.dockerStatus", {
      status: runtimeStatusLabel(dockerStatus[1], t),
    });
  }

  const storageFree = message.match(/^(\d+(?:\.\d+)?\s*(?:GB|MB|TB)) free$/i);
  if (storageFree) {
    return t("dashboard.messages.storageFree", { amount: storageFree[1] });
  }

  const simpleMappings: Record<string, string> = {
    "No jobs": "dashboard.messages.noJobs",
    unknown: "dashboard.messages.unknown",
    "DB + Edge OK": "dashboard.messages.dbEdgeOk",
    "WAL ready": "dashboard.messages.walReady",
    "upload-metrics reachable": "dashboard.messages.uploadMetricsReachable",
    "Development upload scenario is running.": "dashboard.messages.developmentUploadRunning",
    "Development upload scenario is running. This is not an operator job.": "dashboard.messages.developmentUploadRunningDetail",
    "Supabase, State Store, and WSL storage are ready. No blocking items found.": "dashboard.overall.ready.message",
    "There are 3 partial overlaps and 2 retryable failures. Check Upload Preview.": "dashboard.overall.attention.message",
    "Upload start is blocked because Local Supabase is not responding.": "dashboard.overall.blocked.message",
    "Runtime status is not available.": "dashboard.messages.runtimeUnavailable",
    "Docker/WSL status is not available.": "dashboard.messages.dockerWslUnavailable",
    "Preview run exceeded the configured time limit.": "upload.reason.timeout",
    "Configured source folder is missing.": "upload.reason.source_missing",
    "Local console token is missing or invalid. Restart the web console from the launcher.": "settings.save.reason.local_token_required",
    "No persisted upload job found in the active state store.": "dashboard.messages.noPersistedUploadJob",
    "No failed files in the latest job.": "dashboard.warnings.rows.failed_retry.empty",
    "Retry review is needed.": "dashboard.warnings.rows.failed_retry.impact",
    "No warnings recorded for the latest job.": "dashboard.warnings.rows.risky.empty",
    "Review latest job warnings.": "dashboard.warnings.rows.risky.impact",
    "Local Supabase core runtime is not reachable.": "dashboard.warnings.rows.supabase_unreachable.impact",
    "Runtime gate is not blocking Dashboard review.": "dashboard.warnings.rows.supabase_unreachable.empty",
    "Docker is not reachable from the backend process.": "runtime.reason.docker_unreachable",
    "Edge route probe timed out.": "runtime.reason.edge_probe_timeout",
  };
  const key = simpleMappings[message];
  if (key) return t(key);

  return message;
}

function jobStatusLabel(status: string, t: Translate): string {
  const key = `upload.job.status.${status}`;
  const translated = t(key);
  return translated === key ? status : translated;
}

function translateStatusValue(value: string, t: Translate): string {
  const message = localizeDiagnosticMessage(value, t);
  if (message !== value) return message;
  return runtimeStatusLabel(value, t);
}

function formatInt(value: string): string {
  return Number(value).toLocaleString();
}
