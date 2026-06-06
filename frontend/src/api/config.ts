export type ConfigSource = "default" | "config" | "env" | string;

export interface ConfigItem {
  key: string;
  label: string;
  value: string | number | boolean | null;
  source: ConfigSource;
  secret: boolean;
  envKey: string;
  overridden: boolean;
}

export interface ConfigResponse {
  configFilePath: string;
  items: ConfigItem[];
}

export interface ConfigSaveResponse {
  savedKeys: string[];
  configFilePath: string;
}

export type ConfigSaveValues = Record<string, string | number>;

export class ConfigApiError extends Error {
  reason: string;
  keys: string[];
  status: number;

  constructor(message: string, status: number, reason: string, keys: string[]) {
    super(message);
    this.name = "ConfigApiError";
    this.status = status;
    this.reason = reason;
    this.keys = keys;
  }
}

export async function fetchConfig(): Promise<ConfigResponse> {
  const response = await fetch("/api/config");
  if (!response.ok) throw new Error("Config could not be loaded");
  return response.json();
}

export async function saveConfig(values: ConfigSaveValues): Promise<ConfigSaveResponse> {
  const response = await fetch("/api/config", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ actor: "local_operator", values }),
  });
  if (!response.ok) {
    const raw = await response.json().catch(() => null);
    const reason = typeof raw?.detail?.reason === "string" ? raw.detail.reason : "config_save_failed";
    const keys = Array.isArray(raw?.detail?.keys) ? raw.detail.keys.map(String) : [];
    throw new ConfigApiError("Config save failed", response.status, reason, keys);
  }
  return response.json();
}
