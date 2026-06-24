import { LoaderCircle, Play, Square } from "lucide-react";
import { useTranslation } from "react-i18next";

import type { RuntimeStatusResponse, RuntimeServiceStatus } from "../../api/runtime";
import { unknownStateContext } from "../../api/stateContext";
import type { RuntimeCheckRow } from "../../pages/dashboard/dashboardTypes";
import type { StatusTone } from "../../pages/dashboard/dashboardTypes";
import { StatusBadge } from "../status/StatusBadge";
import { Panel } from "../ui/Panel";
import { formatKstTime } from "./formatters";
import {
  runtimeReasonText,
  runtimeServiceDetail,
  runtimeStateContextDetail,
} from "./localizedDashboardText";

interface RuntimeCheckPanelProps {
  rows: RuntimeCheckRow[];
  runtimeStatus?: RuntimeStatusResponse;
  isRuntimeLoading?: boolean;
  runtimeError?: string;
  onStart?: () => void;
  onStop?: () => void;
  actionPending?: boolean;
  pendingAction?: "start" | "stop" | null;
}

export function RuntimeCheckPanel({
  rows,
  runtimeStatus,
  isRuntimeLoading = false,
  runtimeError,
  onStart,
  onStop,
  actionPending = false,
  pendingAction = null,
}: RuntimeCheckPanelProps) {
  const { t, i18n } = useTranslation();
  const translate: Translate = (key, options) => String(t(key, options));
  const tableRows = runtimeStatus ? runtimeRows(runtimeStatus, translate) : rows;
  const activeAction = actionPending
    ? pendingAction ?? runtimeStatus?.activeOperation?.kind ?? null
    : runtimeStatus?.activeOperation?.kind ?? null;
  const startPending = activeAction === "start";
  const stopPending = activeAction === "stop";
  const summaryTone = runtimeStatus ? (activeAction ? "running" : toneForOverall(runtimeStatus.overallStatus)) : "muted";
  const startLabel = startPending ? t("runtime.actions.starting") : t("runtime.actions.start");
  const stopLabel = stopPending ? t("runtime.actions.stopping") : t("runtime.actions.stop");
  const startDisabledReason = runtimeStatus ? startDisabledReasonFor(runtimeStatus, activeAction, translate) : translate("runtime.actions.apiRequired");
  const stopDisabledReason = runtimeStatus ? stopDisabledReasonFor(runtimeStatus, activeAction, translate) : translate("runtime.actions.apiRequired");
  const startDisabled = Boolean(startDisabledReason);
  const stopDisabled = Boolean(stopDisabledReason);
  const summaryLabel = activeAction
    ? t(activeAction === "start" ? "runtime.actions.starting" : "runtime.actions.stopping")
    : runtimeStatus
      ? t(`runtime.overall.${runtimeStatus.overallStatus}`)
      : t("runtime.overall.unknown");
  const summaryDetail = activeAction
    ? t(activeAction === "start" ? "runtime.actions.startingDetail" : "runtime.actions.stoppingDetail")
    : runtimeStatus
      ? runtimeReasonText(runtimeStatus, translate)
      : "";

  return (
    <Panel className="runtime-check-panel" title={t("dashboard.runtime.title")} titleId="runtime-check-title">
      {runtimeStatus ? (
        <div
          aria-busy={Boolean(activeAction)}
          className={`runtime-summary runtime-summary--${summaryTone}${activeAction ? " runtime-summary--busy" : ""}`}
        >
          <div className="runtime-summary__state" role="status" aria-live="polite">
            <StatusBadge tone={summaryTone} label={summaryLabel} busy={Boolean(activeAction)} />
            <p>{summaryDetail}</p>
          </div>
          <div className="runtime-actions">
            <button
              aria-label={startDisabledReason || startLabel}
              aria-busy={startPending}
              className={`button button--secondary runtime-actions__button${startPending ? " runtime-actions__button--pending" : ""}`}
              disabled={startDisabled}
              onClick={onStart}
              title={startDisabledReason || undefined}
              type="button"
            >
              {startPending ? (
                <LoaderCircle aria-hidden="true" className="button__icon button__icon--spin" size={15} />
              ) : (
                <Play aria-hidden="true" className="button__icon" size={15} />
              )}
              <span>{startLabel}</span>
            </button>
            <button
              aria-label={stopDisabledReason || stopLabel}
              aria-busy={stopPending}
              className={`button button--secondary runtime-actions__button${stopPending ? " runtime-actions__button--pending" : ""}`}
              disabled={stopDisabled}
              onClick={onStop}
              title={stopDisabledReason || undefined}
              type="button"
            >
              {stopPending ? (
                <LoaderCircle aria-hidden="true" className="button__icon button__icon--spin" size={15} />
              ) : (
                <Square aria-hidden="true" className="button__icon" size={15} />
              )}
              <span>{stopLabel}</span>
            </button>
          </div>
        </div>
      ) : null}
      {isRuntimeLoading ? <div className="inline-state">{t("runtime.loading")}</div> : null}
      {runtimeError ? (
        <div className="inline-state inline-state--error" role="alert">
          {runtimeError}
        </div>
      ) : null}
      <div className="table-scroll">
        <table className="data-table data-table--runtime">
          <thead>
            <tr>
              <th scope="col">{t("dashboard.runtime.service")}</th>
              <th scope="col">{t("dashboard.jobs.status")}</th>
              <th scope="col">{t("dashboard.runtime.detail")}</th>
              <th scope="col">{t("dashboard.runtime.lastCheck")}</th>
            </tr>
          </thead>
          <tbody>
            {tableRows.map((row) => (
              <tr className={`row--${row.tone}`} key={row.id}>
                <td>{row.label}</td>
                <td><StatusBadge tone={row.tone} /></td>
                <td className="endpoint runtime-detail-cell" title={row.detail}>
                  {row.href ? (
                    <a className="runtime-detail-cell__content" href={row.href} target="_blank" rel="noreferrer">
                      {row.detail}
                    </a>
                  ) : (
                    <span className="runtime-detail-cell__content">{row.detail}</span>
                  )}
                </td>
                <td><time className="timestamp" dateTime={row.lastCheckedAt}>{formatKstTime(row.lastCheckedAt, i18n.language)}</time></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}

type Translate = (key: string, options?: Record<string, unknown>) => string;

function runtimeRows(runtimeStatus: RuntimeStatusResponse, t: Translate): RuntimeCheckRow[] {
  const checkedAt = runtimeStatus.checkedAt;
  const stateContext = runtimeStatus.stateContext ?? unknownStateContext;
  return [
    {
      id: "supabase",
      label: t("runtime.services.api"),
      tone: toneForService(runtimeStatus.api.status),
      detail: `${runtimeStatus.api.host}:${runtimeStatus.api.port} - ${runtimeServiceDetail(runtimeStatus.api, t)}`,
      lastCheckedAt: checkedAt,
    },
    {
      id: "database",
      label: t("runtime.services.db"),
      tone: toneForService(runtimeStatus.db.status),
      detail: `${runtimeStatus.db.host}:${runtimeStatus.db.port} - ${runtimeServiceDetail(runtimeStatus.db, t)}`,
      lastCheckedAt: checkedAt,
    },
    {
      id: "edge_function",
      label: t("runtime.services.edge"),
      tone: toneForService(runtimeStatus.edgeRuntime.status),
      detail: runtimeServiceDetail(runtimeStatus.edgeRuntime, t),
      lastCheckedAt: checkedAt,
    },
    {
      id: "wsl_storage",
      label: t("runtime.services.wsl"),
      tone: toneForService(runtimeStatus.wsl.status),
      detail: runtimeServiceDetail(runtimeStatus.wsl, t),
      lastCheckedAt: checkedAt,
    },
    {
      id: "grafana",
      label: t("runtime.services.grafana"),
      tone: toneForObservabilityService(runtimeStatus.grafana.status),
      detail: observabilityRuntimeDetail(runtimeStatus.grafana, runtimeStatus, t),
      href: runtimeStatus.grafana.url ?? undefined,
      lastCheckedAt: checkedAt,
    },
    {
      id: "vector",
      label: t("runtime.services.vector"),
      tone: toneForObservabilityService(runtimeStatus.vector.status),
      detail: observabilityRuntimeDetail(runtimeStatus.vector, runtimeStatus, t),
      lastCheckedAt: checkedAt,
    },
    {
      id: "containers",
      label: t("runtime.services.containers"),
      tone: toneForContainers(runtimeStatus.containers),
      detail: containerDetail(runtimeStatus.containers, t),
      lastCheckedAt: checkedAt,
    },
    {
      id: "state_context",
      label: t("runtime.services.stateContext"),
      tone: toneForStateContext(stateContext.storageStatus),
      detail: runtimeStateContextDetail(stateContext, t),
      lastCheckedAt: checkedAt,
    },
  ];
}

function toneForOverall(status: string): StatusTone {
  if (status === "ready") return "ready";
  if (status === "running") return "running";
  if (status === "attention") return "attention";
  if (status === "blocked") return "blocked";
  return "muted";
}

function toneForService(status: RuntimeServiceStatus): StatusTone {
  if (status === "ready") return "ready";
  if (status === "starting" || status === "stopping") return "running";
  if (status === "stopped" || status === "unreachable" || status === "unhealthy") return "attention";
  if (status === "missing") return "blocked";
  return "muted";
}

function toneForObservabilityService(status: RuntimeServiceStatus): StatusTone {
  if (status === "ready") return "ready";
  if (status === "starting" || status === "stopping") return "running";
  if (status === "stopped" || status === "unreachable" || status === "unhealthy" || status === "missing" || status === "unknown") {
    return "attention";
  }
  return "muted";
}

function toneForContainers(containers: RuntimeStatusResponse["containers"]): StatusTone {
  if (containers.some((row) => row.required && row.status === "missing")) return "blocked";
  if (containers.some((row) => row.status === "stopped" || row.status === "unreachable" || row.status === "unhealthy" || row.status === "missing")) {
    return "attention";
  }
  if (containers.length > 0 && containers.every((row) => row.status === "ready")) return "ready";
  return "muted";
}

function toneForStateContext(storageStatus: RuntimeStatusResponse["stateContext"]["storageStatus"]): StatusTone {
  if (storageStatus === "present") return "ready";
  if (storageStatus === "missing" || storageStatus === "unknown") return "muted";
  return "attention";
}

function containerDetail(containers: RuntimeStatusResponse["containers"], t: Translate): string {
  const running = containers.filter((row) => row.running).length;
  const problemCount = containers.filter((row) => row.status !== "ready").length;
  return problemCount > 0
    ? t("runtime.containers.detailWithProblems", { running, total: containers.length, problemCount })
    : t("runtime.containers.detail", { running, total: containers.length });
}

type ObservabilityRuntimeProbe = RuntimeStatusResponse["grafana"] | RuntimeStatusResponse["vector"];

function coreRuntimeReady(runtimeStatus: RuntimeStatusResponse): boolean {
  return (
    runtimeStatus.api.status === "ready"
    && runtimeStatus.db.status === "ready"
    && runtimeStatus.studio.status === "ready"
    && runtimeStatus.edgeRuntime.status === "ready"
  );
}

function observabilityRuntimeDetail(service: ObservabilityRuntimeProbe, runtimeStatus: RuntimeStatusResponse, t: Translate): string {
  const detail = runtimeServiceDetail(service, t);
  if (service.status === "ready" || !coreRuntimeReady(runtimeStatus)) return detail;
  return t("runtime.observability.vectorCaveat", { detail });
}

type RuntimeAction = "start" | "stop";

function activeOperationDisabledReason(activeAction: RuntimeAction | null, t: Translate): string {
  if (activeAction === "start") return t("runtime.actions.startingActive");
  if (activeAction === "stop") return t("runtime.actions.stoppingActive");
  return "";
}

function startDisabledReasonFor(runtimeStatus: RuntimeStatusResponse, activeAction: RuntimeAction | null, t: Translate): string {
  const operationDisabledReason = activeOperationDisabledReason(activeAction, t);
  if (operationDisabledReason) return operationDisabledReason;
  if (runtimeStatus.overallStatus === "running" || runtimeStatus.activeOperation) return t("runtime.actions.operationActive");
  if (runtimeStatus.overallStatus === "ready") return t("runtime.actions.alreadyReady");
  if (runtimeStatus.reasonCode === "non_core_runtime_attention") return t("runtime.actions.nonCoreAttention");
  if (runtimeStatus.reasonCode === "required_container_missing") return t("runtime.actions.requiredContainerMissing");
  if (runtimeStatus.docker.status !== "ready") return t("runtime.actions.dockerUnavailable");
  return "";
}

function stopDisabledReasonFor(runtimeStatus: RuntimeStatusResponse, activeAction: RuntimeAction | null, t: Translate): string {
  const operationDisabledReason = activeOperationDisabledReason(activeAction, t);
  if (operationDisabledReason) return operationDisabledReason;
  if (runtimeStatus.overallStatus === "running" || runtimeStatus.activeOperation) return t("runtime.actions.operationActive");
  if (runtimeStatus.docker.status !== "ready") return t("runtime.actions.dockerUnavailable");
  if (!runtimeStatus.containers.some((row) => row.running)) return t("runtime.actions.alreadyStopped");
  return "";
}
