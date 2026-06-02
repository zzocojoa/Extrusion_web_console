import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { fetchLocalSupabaseStatus, type RuntimeStatusResponse } from "../api/runtime";
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
  const runtime = runtimeQuery.data ?? mockRuntimeStatus();

  return (
    <main className="settings-page" aria-labelledby="settings-title">
      <section className="panel settings-panel">
        <div className="panel__header">
          <div>
            <h2 id="settings-title">{t("settings.runtime.title")}</h2>
            <p>{t("settings.runtime.subtitle")}</p>
          </div>
          <StatusBadge tone={toneForOverall(runtime.overallStatus)} label={t(`runtime.overall.${runtime.overallStatus}`)} />
        </div>

        {runtimeQuery.isLoading ? <div className="inline-state">{t("runtime.loading")}</div> : null}
        {runtimeQuery.isError ? (
          <div className="inline-state inline-state--error" role="alert">
            {t("settings.runtime.error")}
          </div>
        ) : null}

        <div className="settings-readonly-grid" aria-label={t("settings.runtime.configLabel")}>
          {runtime.config.map((item) => (
            <label className="settings-field" key={item.key}>
              <span>{item.label}</span>
              <input type="text" value={item.secret ? "********" : item.value} readOnly />
              <small>{t("settings.runtime.source")}: {t(`settings.source.${item.source}`, item.source)}</small>
            </label>
          ))}
        </div>
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

function mockRuntimeStatus(): RuntimeStatusResponse {
  const checkedAt = new Date().toISOString();
  return {
    overallStatus: "unknown",
    reasonCode: "mock_runtime_config",
    reasonText: "Runtime status is available when VITE_API_MODE=api.",
    checkedAt,
    projectPath: "C:\\Users\\user\\Documents\\GitHub\\Extrusion_data",
    projectId: "Extrusion_data",
    docker: { name: "Docker", status: "unknown", detail: "API mode required.", url: null },
    wsl: { name: "WSL", status: "unknown", detail: "API mode required.", url: null },
    supabaseCli: { name: "Supabase CLI", status: "unknown", detail: "API mode required.", url: null },
    api: { name: "Supabase API", host: "127.0.0.1", port: 54321, status: "unknown", detail: "API mode required." },
    db: { name: "Supabase DB", host: "127.0.0.1", port: 25432, status: "unknown", detail: "API mode required." },
    studio: { name: "Supabase Studio", host: "127.0.0.1", port: 54323, status: "unknown", detail: "API mode required." },
    edgeRuntime: { name: "Edge Function", status: "unknown", detail: "API mode required.", url: "http://127.0.0.1:54321/functions/v1/upload-metrics" },
    grafana: { name: "Grafana", status: "unknown", detail: "API mode required.", url: "http://localhost:3001" },
    containers: [],
    config: [
      { key: "localSupabaseProjectPath", label: "Project path", value: "C:\\Users\\user\\Documents\\GitHub\\Extrusion_data", source: "default", secret: false },
      { key: "localSupabaseProjectId", label: "Project id", value: "Extrusion_data", source: "default", secret: false },
      { key: "localSupabaseApiPort", label: "API port", value: "54321", source: "default", secret: false },
      { key: "localSupabaseDbPort", label: "DB port", value: "25432", source: "default", secret: false },
      { key: "localSupabaseStudioPort", label: "Studio port", value: "54323", source: "default", secret: false },
      { key: "grafanaUrl", label: "Grafana URL", value: "http://localhost:3001", source: "default", secret: false },
    ],
    activeOperation: null,
  };
}
