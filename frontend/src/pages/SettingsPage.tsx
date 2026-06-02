import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { fetchLocalSupabaseStatus } from "../api/runtime";
import { StatusBadge } from "../components/status/StatusBadge";
import type { StatusTone } from "./dashboard/dashboardTypes";

const useApiRuntime = import.meta.env.VITE_API_MODE === "api";

export function SettingsPage() {
  const { t } = useTranslation();
  const runtimeQuery = useQuery({
    queryKey: ["runtime", "local-supabase", "settings"],
    queryFn: fetchLocalSupabaseStatus,
    enabled: useApiRuntime,
    refetchInterval: 10000,
  });
  const runtime = runtimeQuery.data;
  const status = runtime?.overallStatus ?? "unknown";
  const showUnavailable = !runtime && (!useApiRuntime || runtimeQuery.isError || !runtimeQuery.isLoading);

  return (
    <main className="settings-page" aria-labelledby="settings-title">
      <section className="panel settings-panel">
        <div className="panel__header">
          <div>
            <h2 id="settings-title">{t("settings.runtime.title")}</h2>
            <p>{t("settings.runtime.subtitle")}</p>
          </div>
          <StatusBadge tone={toneForOverall(status)} label={t(`runtime.overall.${status}`)} />
        </div>

        {runtimeQuery.isLoading ? <div className="inline-state">{t("runtime.loading")}</div> : null}
        {runtimeQuery.isError ? (
          <div className="inline-state inline-state--error" role="alert">
            {t("settings.runtime.error")}
          </div>
        ) : null}

        {showUnavailable ? (
          <div className="inline-state" role="status">
            {t("settings.runtime.unavailable")}
          </div>
        ) : null}

        {runtime ? (
          <div className="settings-readonly-grid" aria-label={t("settings.runtime.configLabel")}>
            {runtime.config.map((item) => (
            <label className="settings-field" key={item.key}>
              <span>{item.label}</span>
              <input type="text" value={item.secret ? "********" : item.value} readOnly />
              <small>{t("settings.runtime.source")}: {t(`settings.source.${item.source}`, item.source)}</small>
            </label>
            ))}
          </div>
        ) : null}
        <div className="settings-runtime-note">
          <strong>{t("settings.runtime.commandPolicyTitle")}</strong>
          <p>{t("settings.runtime.commandPolicy")}</p>
        </div>
      </section>
    </main>
  );
}

function toneForOverall(status: string): StatusTone {
  if (status === "ready") return "ready";
  if (status === "running") return "running";
  if (status === "attention") return "attention";
  if (status === "blocked") return "blocked";
  return "muted";
}
