import { useTranslation } from "react-i18next";

import { AuditSummaryPanel } from "../components/dashboard/AuditSummaryPanel";
import { DashboardStatusMatrix } from "../components/dashboard/DashboardStatusMatrix";
import { RecentJobsPanel } from "../components/dashboard/RecentJobsPanel";
import { RuntimeCheckPanel } from "../components/dashboard/RuntimeCheckPanel";
import { SafetySummaryBanner } from "../components/dashboard/SafetySummaryBanner";
import { WarningQueuePanel } from "../components/dashboard/WarningQueuePanel";
import { useDashboardQuery } from "./dashboard/dashboardQuery";

export function DashboardPage() {
  const { t } = useTranslation();
  const { data, isLoading, isError } = useDashboardQuery();

  if (isLoading) {
    return (
      <main className="dashboard-page" aria-labelledby="dashboard-title">
        <section className="panel panel--loading">Local Supabase, upload, and state store 확인 중...</section>
      </main>
    );
  }

  if (isError || !data) {
    return (
      <main className="dashboard-page" aria-labelledby="dashboard-title">
        <section className="panel panel--error" role="alert">
          {t("dashboard.error")}
        </section>
      </main>
    );
  }

  return (
    <main className="dashboard-page" aria-labelledby="dashboard-title">
      <SafetySummaryBanner overall={data.overall} />
      <DashboardStatusMatrix items={data.statusMatrix} />
      <RecentJobsPanel jobs={data.recentJobs} currentJob={data.currentJob} />
      <section className="dashboard-lower-grid" aria-label="Dashboard detail summaries">
        <RuntimeCheckPanel rows={data.runtimeChecks} />
        <WarningQueuePanel rows={data.warningQueue} />
        <AuditSummaryPanel rows={data.auditSummary} />
      </section>
    </main>
  );
}
