import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2, Lock, Save } from "lucide-react";
import { useTranslation } from "react-i18next";

import { ConfigApiError, fetchConfig, saveConfig, type ConfigItem, type ConfigResponse, type ConfigSaveValues } from "../api/config";

const useApiConfig = import.meta.env.VITE_API_MODE === "api";
const secretPlaceholder = "********";

type FormState = Record<string, string>;
type ValidationErrors = Record<string, string>;

type ConfigSectionId = "folders" | "connection" | "runtime" | "interface";

const sectionOrder: ConfigSectionId[] = ["folders", "connection", "runtime", "interface"];

const configSections: Record<ConfigSectionId, string[]> = {
  folders: ["plcDataDir", "temperatureDataDir"],
  connection: ["supabaseDbUrl", "supabaseUrl", "supabaseAnonKey", "supabaseEdgeUrl", "grafanaUrl"],
  runtime: [
    "localSupabaseProjectPath",
    "localSupabaseWslPath",
    "localSupabaseProjectId",
    "localSupabaseApiPort",
    "localSupabaseDbPort",
    "localSupabaseStudioPort",
    "runtimeCommandTimeoutSeconds",
    "runtimeReadinessTimeoutSeconds",
  ],
  interface: [],
};

const numericKeys = new Set([
  "localSupabaseApiPort",
  "localSupabaseDbPort",
  "localSupabaseStudioPort",
  "runtimeCommandTimeoutSeconds",
  "runtimeReadinessTimeoutSeconds",
]);

const mockConfig: ConfigResponse = {
  configFilePath: "mock://app-config",
  items: [
    { key: "plcDataDir", label: "PLC directory", value: "mock://plc-source", source: "config", secret: false, envKey: "EWC_PLC_DATA_DIR", overridden: false },
    {
      key: "temperatureDataDir",
      label: "Temperature directory",
      value: "mock://temperature-source",
      source: "default",
      secret: false,
      envKey: "EWC_TEMPERATURE_DATA_DIR",
      overridden: false,
    },
    { key: "supabaseDbUrl", label: "Supabase DB URL", value: null, source: "env", secret: true, envKey: "EWC_SUPABASE_DB_URL", overridden: true },
    { key: "supabaseUrl", label: "Supabase URL", value: "", source: "default", secret: false, envKey: "EWC_SUPABASE_URL", overridden: false },
    {
      key: "supabaseAnonKey",
      label: "Supabase anon key",
      value: null,
      source: "config",
      secret: true,
      envKey: "EWC_SUPABASE_ANON_KEY",
      overridden: false,
    },
    { key: "supabaseEdgeUrl", label: "Supabase Edge URL", value: null, source: "config", secret: true, envKey: "EWC_SUPABASE_EDGE_URL", overridden: false },
    { key: "grafanaUrl", label: "Grafana URL", value: "http://127.0.0.1:3000", source: "default", secret: false, envKey: "EWC_GRAFANA_URL", overridden: false },
    {
      key: "localSupabaseProjectPath",
      label: "Project path",
      value: "mock://local-supabase-project",
      source: "config",
      secret: false,
      envKey: "EWC_LOCAL_SUPABASE_PROJECT_PATH",
      overridden: false,
    },
    {
      key: "localSupabaseWslPath",
      label: "WSL path",
      value: "/mock/local-supabase-project",
      source: "config",
      secret: false,
      envKey: "EWC_LOCAL_SUPABASE_WSL_PATH",
      overridden: false,
    },
    { key: "localSupabaseProjectId", label: "Project id", value: "Extrusion_web_console", source: "default", secret: false, envKey: "EWC_LOCAL_SUPABASE_PROJECT_ID", overridden: false },
    { key: "localSupabaseApiPort", label: "API port", value: 55321, source: "default", secret: false, envKey: "EWC_LOCAL_SUPABASE_API_PORT", overridden: false },
    { key: "localSupabaseDbPort", label: "DB port", value: 25433, source: "default", secret: false, envKey: "EWC_LOCAL_SUPABASE_DB_PORT", overridden: false },
    { key: "localSupabaseStudioPort", label: "Studio port", value: 55323, source: "default", secret: false, envKey: "EWC_LOCAL_SUPABASE_STUDIO_PORT", overridden: false },
    {
      key: "runtimeCommandTimeoutSeconds",
      label: "Runtime command timeout",
      value: 90,
      source: "default",
      secret: false,
      envKey: "EWC_RUNTIME_COMMAND_TIMEOUT_SECONDS",
      overridden: false,
    },
    {
      key: "runtimeReadinessTimeoutSeconds",
      label: "Runtime readiness timeout",
      value: 60,
      source: "default",
      secret: false,
      envKey: "EWC_RUNTIME_READINESS_TIMEOUT_SECONDS",
      overridden: false,
    },
  ],
};

export function SettingsPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [formValues, setFormValues] = useState<FormState>({});
  const [saveStatus, setSaveStatus] = useState<{ type: "success" | "error"; message: string } | null>(null);

  const configQuery = useQuery({
    queryKey: ["config"],
    queryFn: fetchConfig,
    enabled: useApiConfig,
    refetchInterval: useApiConfig ? 30000 : false,
  });

  const config = useApiConfig ? configQuery.data : mockConfig;

  const originalValues = useMemo(() => buildFormState(config?.items ?? []), [config]);
  const groupedItems = useMemo(() => groupConfigItems(config?.items ?? []), [config]);

  useEffect(() => {
    setFormValues(originalValues);
  }, [originalValues]);

  const validationErrors = useMemo(() => validateValues(config?.items ?? [], formValues, t), [config, formValues, t]);
  const changedValues = useMemo(() => buildChangedValues(config?.items ?? [], originalValues, formValues), [config, formValues, originalValues]);
  const changedCount = Object.keys(changedValues).length;
  const hasValidationErrors = Object.keys(validationErrors).length > 0;

  const saveMutation = useMutation({
    mutationFn: saveConfig,
    onSuccess: (response) => {
      setSaveStatus({
        type: "success",
        message: t("settings.save.success", { count: response.savedKeys.length }),
      });
      void queryClient.invalidateQueries({ queryKey: ["config"] });
    },
    onError: (error) => {
      const message =
        error instanceof ConfigApiError
          ? t(`settings.save.reason.${error.reason}`, { defaultValue: t("settings.save.failure"), keys: error.keys.join(", ") })
          : t("settings.save.failure");
      setSaveStatus({ type: "error", message });
    },
  });

  const canSave = useApiConfig && changedCount > 0 && !hasValidationErrors && !saveMutation.isPending;

  function updateField(key: string, value: string) {
    setSaveStatus(null);
    setFormValues((current) => ({ ...current, [key]: value }));
  }

  function resetChanges() {
    setFormValues(originalValues);
    setSaveStatus(null);
  }

  function submitSave() {
    if (!canSave) return;
    saveMutation.mutate(changedValues);
  }

  return (
    <main className="settings-page" aria-labelledby="settings-title">
      <section className="panel settings-panel settings-panel--editor">
        <div className="panel__header settings-header">
          <div>
            <h2 id="settings-title">{t("settings.editor.title")}</h2>
            <p className="panel-subtitle">{t("settings.editor.subtitle")}</p>
          </div>
          <div className="settings-header__meta">
            <span>{t("settings.editor.configFile")}</span>
            <code>{useApiConfig ? t("settings.editor.configFileHidden") : t("settings.editor.mockMode")}</code>
          </div>
        </div>

        {configQuery.isLoading ? <div className="inline-state">{t("settings.editor.loading")}</div> : null}
        {configQuery.isError ? (
          <div className="inline-state inline-state--error" role="alert">
            {t("settings.editor.error")}
          </div>
        ) : null}
        {!useApiConfig ? (
          <div className="inline-state" role="status">
            {t("settings.editor.apiModeRequired")}
          </div>
        ) : null}

        {config ? (
          <>
            <div className="settings-section-list">
              {sectionOrder.map((sectionId) => {
                const items = groupedItems[sectionId];
                if (!items.length) return null;
                return (
                  <section className="settings-section" key={sectionId} aria-labelledby={`settings-section-${sectionId}`}>
                    <div className="settings-section__header">
                      <h3 id={`settings-section-${sectionId}`}>{t(`settings.sections.${sectionId}.title`)}</h3>
                      <p>{t(`settings.sections.${sectionId}.subtitle`)}</p>
                    </div>
                    <div className="settings-form-grid">
                      {items.map((item) => {
                        const disabled = item.overridden || saveMutation.isPending || !useApiConfig;
                        const error = validationErrors[item.key];
                        const value = formValues[item.key] ?? "";
                        return (
                          <label className={`settings-field ${disabled ? "settings-field--disabled" : ""}`} key={item.key}>
                            <span className="settings-field__label">{t(`settings.fields.${item.key}`, item.label)}</span>
                            <div className="settings-field__control">
                              {item.secret ? <Lock aria-hidden="true" /> : null}
                              <input
                                type={item.secret ? "password" : numericKeys.has(item.key) ? "number" : "text"}
                                inputMode={numericKeys.has(item.key) ? "numeric" : "text"}
                                value={value}
                                min={numericKeys.has(item.key) ? 1 : undefined}
                                max={numericKeys.has(item.key) ? 65535 : undefined}
                                placeholder={item.secret ? t("settings.editor.secretPlaceholder") : undefined}
                                disabled={disabled}
                                onChange={(event) => updateField(item.key, event.target.value)}
                              />
                            </div>
                            <span className="settings-field__meta">
                              {t("settings.runtime.source")}: {t(`settings.source.${item.source}`, item.source)}
                              {item.overridden ? (
                                <strong>{t("settings.editor.envOverride", { envKey: item.envKey })}</strong>
                              ) : item.secret && item.value === null ? (
                                <strong>{t("settings.editor.secretHidden")}</strong>
                              ) : null}
                            </span>
                            {error ? <span className="settings-field__error">{error}</span> : null}
                          </label>
                        );
                      })}
                    </div>
                  </section>
                );
              })}
            </div>

            <div className="settings-runtime-note">
              <strong>{t("settings.runtime.commandPolicyTitle")}</strong>
              <p>{t("settings.runtime.commandPolicy")}</p>
            </div>

            <div className="settings-save-bar" role="status" aria-live="polite">
              <div className="settings-save-bar__state">
                {saveStatus?.type === "success" ? <CheckCircle2 aria-hidden="true" /> : saveStatus?.type === "error" || hasValidationErrors ? <AlertTriangle aria-hidden="true" /> : null}
                <span>
                  {saveStatus?.message ??
                    (hasValidationErrors
                      ? t("settings.save.validationSummary")
                      : changedCount > 0
                        ? t("settings.save.dirty", { count: changedCount })
                        : t("settings.save.clean"))}
                </span>
              </div>
              <div className="settings-save-bar__actions">
                <button className="button button--secondary" type="button" disabled={changedCount === 0 || saveMutation.isPending} onClick={resetChanges}>
                  {t("settings.save.reset")}
                </button>
                <button className="button button--primary" type="button" disabled={!canSave} onClick={submitSave}>
                  <Save aria-hidden="true" />
                  {saveMutation.isPending ? t("settings.save.saving") : t("settings.save.button")}
                </button>
              </div>
            </div>
          </>
        ) : null}
      </section>
    </main>
  );
}

function buildFormState(items: ConfigItem[]): FormState {
  return Object.fromEntries(
    items.map((item) => {
      if (item.secret) return [item.key, ""];
      return [item.key, item.value == null ? "" : String(item.value)];
    }),
  );
}

function groupConfigItems(items: ConfigItem[]): Record<ConfigSectionId, ConfigItem[]> {
  const byKey = new Map(items.map((item) => [item.key, item]));
  return Object.fromEntries(
    sectionOrder.map((sectionId) => [sectionId, configSections[sectionId].map((key) => byKey.get(key)).filter((item): item is ConfigItem => Boolean(item))]),
  ) as Record<ConfigSectionId, ConfigItem[]>;
}

function validateValues(items: ConfigItem[], values: FormState, t: (key: string) => string): ValidationErrors {
  const errors: ValidationErrors = {};
  for (const item of items) {
    if (item.overridden) continue;
    const value = values[item.key] ?? "";
    if (!numericKeys.has(item.key)) continue;
    const parsed = Number(value);
    if (!Number.isInteger(parsed) || parsed < 1 || parsed > 65535) {
      errors[item.key] = t("settings.save.integerError");
    }
  }
  return errors;
}

function buildChangedValues(items: ConfigItem[], originalValues: FormState, values: FormState): ConfigSaveValues {
  const changed: ConfigSaveValues = {};
  for (const item of items) {
    if (item.overridden) continue;
    const current = values[item.key] ?? "";
    const original = originalValues[item.key] ?? "";
    if (item.secret && current === "") continue;
    if (current === original) continue;
    changed[item.key] = numericKeys.has(item.key) ? Number(current) : current;
  }
  return changed;
}
