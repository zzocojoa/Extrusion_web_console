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
}

export function RuntimeCheckPanel({
  rows,
  runtimeStatus,
  isRuntimeLoading = false,
  runtimeError,
  onStart,
  onStop,
  actionPending = false,
}: RuntimeCheckPanelProps) {
  const { t, i18n } = useTranslation();
  const translate: Translate = (key, options) => String(t(key, options));
  const tableRows = runtimeStatus ? runtimeRows(runtimeStatus, translate) : rows;
  const startDisabledReason = runtimeStatus ? startDisabledReasonFor(runtimeStatus, actionPending, translate) : translate("runtime.actions.apiRequired");
  const stopDisabledReason = runtimeStatus ? stopDisabledReasonFor(runtimeStatus, actionPending, translate) : translate("runtime.actions.apiRequired");
  const startDisabled = Boolean(startDisabledReason);
  const stopDisabled = Boolean(stopDisabledReason);

  return (
    <Panel className="runtime-check-panel" title={t("dashboard.runtime.title")} titleId="runtime-check-title">
      {runtimeStatus ? (
        <div className={`runtime-summary runtime-summary--${toneForOverall(runtimeStatus.overallStatus)}`}>
          <div>
            <StatusBadge tone={toneForOverall(runtimeStatus.overallStatus)} label={t(`runtime.overall.${runtimeStatus.overallStatus}`)} />
            <p>{runtimeReasonText(runtimeStatus, translate)}</p>
          </div>
          <div className="runtime-actions">
            <button
              aria-label={startDisabledReason || t("runtime.actions.start")}
              className="button button--secondary"
              disabled={startDisabled}
              onClick={onStart}
              title={startDisabledReason || undefined}
              type="button"
            >
              {actionPending ? t("runtime.actions.working") : t("runtime.actions.start")}
            </button>
            <button
              aria-label={stopDisabledReason || t("runtime.actions.stop")}
              className="button button--secondary"
              disabled={stopDisabled}
              onClick={onStop}
              title={stopDisabledReason || undefined}
              type="button"
            >
              {actionPending ? t("runtime.actions.working") : t("runtime.actions.stop")}
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
                <td className="endpoint truncate">
                  {row.href ? <a href={row.href} target="_blank" rel="noreferrer">{row.detail}</a> : row.detail}
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
      detail: runtimeStatus.grafana.url ?? runtimeServiceDetail(runtimeStatus.grafana, t),
      href: runtimeStatus.grafana.url ?? undefined,
      lastCheckedAt: checkedAt,
    },
    {
      id: "vector",
      label: t("runtime.services.vector"),
      tone: toneForObservabilityService(runtimeStatus.vector.status),
      detail: runtimeServiceDetail(runtimeStatus.vector, t),
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

function startDisabledReasonFor(runtimeStatus: RuntimeStatusResponse, actionPending: boolean, t: Translate): string {
  if (actionPending || runtimeStatus.overallStatus === "running" || runtimeStatus.activeOperation) return t("runtime.actions.operationActive");
  if (runtimeStatus.overallStatus === "ready") return t("runtime.actions.alreadyReady");
  if (runtimeStatus.reasonCode === "required_container_missing") return t("runtime.actions.requiredContainerMissing");
  if (runtimeStatus.docker.status !== "ready") return t("runtime.actions.dockerUnavailable");
  return "";
}

function stopDisabledReasonFor(runtimeStatus: RuntimeStatusResponse, actionPending: boolean, t: Translate): string {
  if (actionPending || runtimeStatus.overallStatus === "running" || runtimeStatus.activeOperation) return t("runtime.actions.operationActive");
  if (runtimeStatus.docker.status !== "ready") return t("runtime.actions.dockerUnavailable");
  if (!runtimeStatus.containers.some((row) => row.running)) return t("runtime.actions.alreadyStopped");
  return "";
}
