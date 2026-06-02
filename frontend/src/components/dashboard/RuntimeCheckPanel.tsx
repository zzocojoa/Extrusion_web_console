import { useTranslation } from "react-i18next";

import type { RuntimeStatusResponse, RuntimeServiceStatus } from "../../api/runtime";
import type { RuntimeCheckRow } from "../../pages/dashboard/dashboardTypes";
import type { StatusTone } from "../../pages/dashboard/dashboardTypes";
import { StatusBadge } from "../status/StatusBadge";
import { Panel } from "../ui/Panel";
import { formatKstTime } from "./formatters";

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
  const tableRows = runtimeStatus ? runtimeRows(runtimeStatus, t) : rows;
  const actionDisabled = actionPending || runtimeStatus?.overallStatus === "running";

  return (
    <Panel className="runtime-check-panel" title={t("dashboard.runtime.title")} titleId="runtime-check-title">
      {runtimeStatus ? (
        <div className={`runtime-summary runtime-summary--${toneForOverall(runtimeStatus.overallStatus)}`}>
          <div>
            <StatusBadge tone={toneForOverall(runtimeStatus.overallStatus)} label={t(`runtime.overall.${runtimeStatus.overallStatus}`)} />
            <p>{runtimeStatus.reasonText}</p>
          </div>
          <div className="runtime-actions">
            <button className="button button--secondary" type="button" onClick={onStart} disabled={actionDisabled}>
              {actionPending ? t("runtime.actions.working") : t("runtime.actions.start")}
            </button>
            <button className="button button--secondary" type="button" onClick={onStop} disabled={actionDisabled}>
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

function runtimeRows(runtimeStatus: RuntimeStatusResponse, t: (key: string) => string): RuntimeCheckRow[] {
  const checkedAt = runtimeStatus.checkedAt;
  return [
    {
      id: "supabase",
      label: t("runtime.services.api"),
      tone: toneForService(runtimeStatus.api.status),
      detail: `${runtimeStatus.api.host}:${runtimeStatus.api.port}`,
      lastCheckedAt: checkedAt,
    },
    {
      id: "database",
      label: t("runtime.services.db"),
      tone: toneForService(runtimeStatus.db.status),
      detail: `${runtimeStatus.db.host}:${runtimeStatus.db.port}`,
      lastCheckedAt: checkedAt,
    },
    {
      id: "edge_function",
      label: t("runtime.services.edge"),
      tone: toneForService(runtimeStatus.edgeRuntime.status),
      detail: runtimeStatus.edgeRuntime.detail,
      lastCheckedAt: checkedAt,
    },
    {
      id: "wsl_storage",
      label: t("runtime.services.wsl"),
      tone: toneForService(runtimeStatus.wsl.status),
      detail: runtimeStatus.wsl.detail,
      lastCheckedAt: checkedAt,
    },
    {
      id: "grafana",
      label: t("runtime.services.grafana"),
      tone: toneForService(runtimeStatus.grafana.status),
      detail: runtimeStatus.grafana.url ?? runtimeStatus.grafana.detail,
      href: runtimeStatus.grafana.url ?? undefined,
      lastCheckedAt: checkedAt,
    },
    {
      id: "state_store",
      label: t("runtime.services.containers"),
      tone: runtimeStatus.containers.some((row) => row.status === "missing") ? "blocked" : "ready",
      detail: `${runtimeStatus.containers.filter((row) => row.running).length}/${runtimeStatus.containers.length}`,
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
