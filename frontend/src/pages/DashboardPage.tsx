import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { fetchLocalSupabaseStatus, startLocalSupabase, stopLocalSupabase } from "../api/runtime";
import { AuditSummaryPanel } from "../components/dashboard/AuditSummaryPanel";
import { DashboardStatusMatrix } from "../components/dashboard/DashboardStatusMatrix";
import { RecentJobsPanel } from "../components/dashboard/RecentJobsPanel";
import { RuntimeCheckPanel } from "../components/dashboard/RuntimeCheckPanel";
import { SafetySummaryBanner } from "../components/dashboard/SafetySummaryBanner";
import { WarningQueuePanel } from "../components/dashboard/WarningQueuePanel";
import { useDashboardQuery } from "./dashboard/dashboardQuery";

const useApiRuntime = import.meta.env.VITE_API_MODE === "api";

export function DashboardPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const { data, isLoading, isError } = useDashboardQuery();
  const runtimeQuery = useQuery({
    queryKey: ["runtime", "local-supabase"],
    queryFn: fetchLocalSupabaseStatus,
    enabled: useApiRuntime,
    refetchInterval: 5000,
  });
  const runtimeMutation = useMutation({
    mutationFn: (action: "start" | "stop") => (action === "start" ? startLocalSupabase() : stopLocalSupabase()),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["runtime", "local-supabase"] });
    },
  });

  if (isLoading) {
    return (
      <main className="dashboard-page" aria-labelledby="dashboard-title">
        <section className="panel panel--loading">{t("dashboard.loading")}</section>
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
      <section className="dashboard-lower-grid" aria-label={t("a11y.dashboardDetailSummaries")}>
        <RuntimeCheckPanel
          rows={data.runtimeChecks}
          runtimeStatus={runtimeQuery.data}
          isRuntimeLoading={runtimeQuery.isLoading}
          runtimeError={runtimeQuery.isError ? t("runtime.error") : runtimeMutation.error?.message}
          onStart={() => runtimeMutation.mutate("start")}
          onStop={() => runtimeMutation.mutate("stop")}
          actionPending={runtimeMutation.isPending}
        />
        <WarningQueuePanel rows={data.warningQueue} />
        <AuditSummaryPanel rows={data.auditSummary} />
      </section>
    </main>
  );
}
