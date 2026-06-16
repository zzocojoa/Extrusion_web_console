import { Activity, CheckCircle, OctagonAlert, TriangleAlert } from "lucide-react";
import { useTranslation } from "react-i18next";

import type { DashboardOverall, OverallSystemState } from "../../pages/dashboard/dashboardTypes";
import { StatusBadge } from "../status/StatusBadge";
import { dashboardOverallMessage, dashboardOverallTitle, type Translate } from "./localizedDashboardText";

const overallIcon: Record<OverallSystemState, typeof CheckCircle> = {
  ready: CheckCircle,
  running: Activity,
  attention: TriangleAlert,
  blocked: OctagonAlert,
};

interface SafetySummaryBannerProps {
  overall: DashboardOverall;
}

export function SafetySummaryBanner({ overall }: SafetySummaryBannerProps) {
  const { t } = useTranslation();
  const translate: Translate = (key, options) => String(t(key, options));
  const Icon = overallIcon[overall.state];
  const actionLabel = overall.action
    ? {
        preview: t("dashboard.actions.preview"),
        start_upload: t("dashboard.actions.startUpload"),
        retry_failed: t("dashboard.actions.retryFailed"),
        open_job: t("dashboard.actions.openJob"),
        start_supabase: t("dashboard.actions.startSupabase"),
        open_logs: t("dashboard.actions.openLogs"),
      }[overall.action]
    : null;

  return (
    <section className={`safety-summary safety-summary--${overall.state}`} aria-live="polite">
      <div className="safety-summary__icon">
        <Icon aria-hidden="true" size={22} />
      </div>
      <div className="safety-summary__copy">
        <div className="safety-summary__kicker">
          <StatusBadge tone={overall.state === "ready" ? "ready" : overall.state} />
        </div>
        <h2>{dashboardOverallTitle(overall, translate)}</h2>
        <p>{dashboardOverallMessage(overall, translate)}</p>
      </div>
      {actionLabel ? (
        <button className="button button--secondary" type="button">
          {actionLabel}
        </button>
      ) : null}
    </section>
  );
}
