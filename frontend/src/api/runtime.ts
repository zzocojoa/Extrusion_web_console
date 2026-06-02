export type RuntimeOverallStatus = "ready" | "running" | "attention" | "blocked" | "unknown";
export type RuntimeServiceStatus = "ready" | "starting" | "stopping" | "stopped" | "unreachable" | "missing" | "unhealthy" | "unknown";
export type RuntimeOperationStatus = "queued" | "running" | "succeeded" | "failed" | "blocked" | "timed_out" | "cancelled" | "interrupted";

export interface RuntimeProbeStatus {
  name: string;
  status: RuntimeServiceStatus;
  detail: string;
  url: string | null;
}

export interface RuntimePortStatus {
  name: string;
  host: string;
  port: number;
  status: RuntimeServiceStatus;
  detail: string;
}

export interface RuntimeContainerStatus {
  name: string;
  required: boolean;
  exists: boolean;
  running: boolean;
  status: RuntimeServiceStatus;
  statusText: string | null;
}

export interface RuntimeConfigItem {
  key: string;
  label: string;
  value: string;
  source: string;
  secret: boolean;
}

export interface RuntimeOperation {
  operationId: string;
  kind: "start" | "stop";
  status: RuntimeOperationStatus;
  requestedAt: string;
  startedAt: string | null;
  finishedAt: string | null;
  actor: string;
  errorCode: string | null;
  errorMessage: string | null;
}

export interface RuntimeStatusResponse {
  overallStatus: RuntimeOverallStatus;
  reasonCode: string;
  reasonText: string;
  checkedAt: string;
  projectPath: string;
  projectId: string;
  docker: RuntimeProbeStatus;
  wsl: RuntimeProbeStatus;
  supabaseCli: RuntimeProbeStatus;
  api: RuntimePortStatus;
  db: RuntimePortStatus;
  studio: RuntimePortStatus;
  edgeRuntime: RuntimeProbeStatus;
  grafana: RuntimeProbeStatus;
  containers: RuntimeContainerStatus[];
  config: RuntimeConfigItem[];
  activeOperation: RuntimeOperation | null;
}

export interface RuntimeOperationCreateResponse {
  operationId: string;
  status: RuntimeOperationStatus;
  detailUrl: string;
}

export async function fetchLocalSupabaseStatus(): Promise<RuntimeStatusResponse> {
  const response = await fetch("/api/runtime/local-supabase");
  if (!response.ok) throw new Error("Local Supabase status could not be loaded");
  return response.json();
}

export async function startLocalSupabase(): Promise<RuntimeOperationCreateResponse> {
  return mutateRuntime("start");
}

export async function stopLocalSupabase(): Promise<RuntimeOperationCreateResponse> {
  return mutateRuntime("stop");
}

async function mutateRuntime(action: "start" | "stop"): Promise<RuntimeOperationCreateResponse> {
  const response = await fetch(`/api/runtime/local-supabase/${action}`, { method: "POST" });
  if (!response.ok) {
    const raw = await response.json().catch(() => null);
    throw new Error(raw?.detail?.reason ?? `Local Supabase ${action} failed`);
  }
  return response.json();
}
