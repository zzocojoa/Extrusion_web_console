import { useTranslation } from "react-i18next";

import type { RuntimeCheckRow } from "../../pages/dashboard/dashboardTypes";
import { StatusBadge } from "../status/StatusBadge";
import { Panel } from "../ui/Panel";
import { formatKstTime } from "./formatters";

interface RuntimeCheckPanelProps {
  rows: RuntimeCheckRow[];
}

export function RuntimeCheckPanel({ rows }: RuntimeCheckPanelProps) {
  const { t } = useTranslation();

  return (
    <Panel className="runtime-check-panel" title={t("dashboard.runtime.title")}>
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
            {rows.map((row) => (
              <tr className={`row--${row.tone}`} key={row.id}>
                <td>{row.label}</td>
                <td><StatusBadge tone={row.tone} /></td>
                <td className="endpoint truncate">
                  {row.href ? <a href={row.href} target="_blank" rel="noreferrer">{row.detail}</a> : row.detail}
                </td>
                <td><time className="timestamp" dateTime={row.lastCheckedAt}>{formatKstTime(row.lastCheckedAt)}</time></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}
