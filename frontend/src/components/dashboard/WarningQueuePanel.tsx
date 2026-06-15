import { useTranslation } from "react-i18next";

import type { WarningQueueRow } from "../../pages/dashboard/dashboardTypes";
import { StatusBadge } from "../status/StatusBadge";
import { Panel } from "../ui/Panel";
import { warningImpact, warningLabel, type Translate } from "./localizedDashboardText";

interface WarningQueuePanelProps {
  rows: WarningQueueRow[];
}

export function WarningQueuePanel({ rows }: WarningQueuePanelProps) {
  const { t } = useTranslation();
  const translate: Translate = (key, options) => String(t(key, options));

  return (
    <Panel className="warning-queue-panel" title={t("dashboard.warnings.title")} titleId="warning-queue-title">
      <div className="table-scroll">
        <table className="data-table data-table--warning">
          <thead>
            <tr>
              <th scope="col">{t("dashboard.warnings.type")}</th>
              <th scope="col">{t("dashboard.jobs.status")}</th>
              <th className="num" scope="col">{t("dashboard.warnings.count")}</th>
              <th scope="col">{t("dashboard.warnings.impact")}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr className={`row--${row.tone}`} key={row.id}>
                <td>{warningLabel(row, translate)}</td>
                <td><StatusBadge tone={row.tone} /></td>
                <td className="num">{row.count}</td>
                <td className="truncate">{warningImpact(row, translate)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}
