import { Activity, AlertTriangle, CheckCircle, OctagonAlert } from "lucide-react";
import { useTranslation } from "react-i18next";

import type { DashboardOverall, OverallSystemState } from "../../pages/dashboard/dashboardTypes";
import { StatusBadge } from "../status/StatusBadge";

const overallIcon: Record<OverallSystemState, typeof CheckCircle> = {
  ready: CheckCircle,
  running: Activity,
  attention: AlertTriangle,
  blocked: OctagonAlert,
};

interface SafetySummaryBannerProps {
  overall: DashboardOverall;
}

export function SafetySummaryBanner({ overall }: SafetySummaryBannerProps) {
  const { t } = useTranslation();
  const Icon = overallIcon[overall.state];

  return (
    <section className={`safety-summary safety-summary--${overall.state}`} aria-live="polite">
      <div className="safety-summary__icon">
        <Icon aria-hidden="true" size={22} />
      </div>
      <div className="safety-summary__copy">
        <div className="safety-summary__kicker">
          <StatusBadge tone={overall.state === "ready" ? "ready" : overall.state} />
        </div>
        <h2>{overall.title}</h2>
        <p>{overall.message}</p>
      </div>
      <button className="button button--secondary" type="button">
        {overall.action === "open_job" ? t("dashboard.actions.openJob") : t("dashboard.actions.openLogs")}
      </button>
    </section>
  );
}
