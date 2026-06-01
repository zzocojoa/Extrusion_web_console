import { useTranslation } from "react-i18next";

import type { AuditSummaryRow, StatusTone } from "../../pages/dashboard/dashboardTypes";
import { StatusBadge } from "../status/StatusBadge";
import { Panel } from "../ui/Panel";
import { formatKstTime } from "./formatters";

const resultTone: Record<AuditSummaryRow["result"], StatusTone> = {
  success: "ready",
  failure: "failed",
  cancelled: "attention",
  blocked: "blocked",
};

interface AuditSummaryPanelProps {
  rows: AuditSummaryRow[];
}

export function AuditSummaryPanel({ rows }: AuditSummaryPanelProps) {
  const { t, i18n } = useTranslation();

  return (
    <Panel className="audit-summary-panel" title={t("dashboard.audit.title")} titleId="audit-summary-title">
      <div className="table-scroll">
        <table className="data-table data-table--audit">
          <thead>
            <tr>
              <th scope="col">{t("dashboard.audit.time")}</th>
              <th scope="col">{t("dashboard.audit.result")}</th>
              <th scope="col">{t("dashboard.audit.action")}</th>
              <th scope="col">{t("dashboard.audit.actor")}</th>
              <th scope="col">{t("dashboard.audit.summary")}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const tone = resultTone[row.result];
              return (
                <tr className={`row--${tone}`} key={row.auditId}>
                  <td><time className="timestamp" dateTime={row.time}>{formatKstTime(row.time, i18n.language)}</time></td>
                  <td><StatusBadge tone={tone} /></td>
                  <td className="endpoint truncate">{row.action}</td>
                  <td className="truncate">{row.actor}</td>
                  <td className="truncate">{row.summary}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}
