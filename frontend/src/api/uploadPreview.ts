import { apiFetch } from "./client";

export type PreviewRangeMode = "today" | "yesterday" | "last_2_days" | "custom";
export type PreviewSource = "plc" | "temperature";
export type PreviewProfile =
  | "default"
  | "stage3_profile_a_bounded_full_scan"
  | "large_source_operational";
export type PreviewItemStatus =
  | "target"
  | "already_in_db"
  | "partial_overlap"
  | "risky"
  | "excluded";
export type PreviewRunStatus =
  | "queued"
  | "running"
  | "succeeded"
  | "partial_failed"
  | "failed"
  | "cancelling"
  | "cancelled"
  | "timed_out";
export type PreviewDbStatus = "not_checked" | "reachable" | "unreachable" | "query_failed";
export type PreviewSortKey = "status" | "fileDate" | "filename" | "uploadRows" | "modifiedAt";
export type SortOrder = "asc" | "desc";

export interface PreviewOptions {
  profile: PreviewProfile;
  stableLagMinutes: number;
  sampleRows: number;
  chunkRows: number;
  maxFiles: number;
  maxRunSeconds: number;
  maxFileSeconds: number;
  forceFullScan: boolean;
}

export interface PreviewCreateRequest {
  rangeMode: PreviewRangeMode;
  startDate: string | null;
  endDate: string | null;
  sources: PreviewSource[];
  options: PreviewOptions;
  retryOfRunId: string | null;
}

export interface PreviewCreateResponse {
  previewRunId: string;
  status: PreviewRunStatus;
  pollUrl: string;
}

export interface PreviewSummary {
  total: number;
  target: number;
  alreadyInDb: number;
  partialOverlap: number;
  risky: number;
  excluded: number;
  uploadRows: number;
  dbMatchedRows: number;
}

export interface PreviewRun {
  previewRunId: string;
  status: PreviewRunStatus;
  requestedAt: string;
  startedAt: string | null;
  finishedAt: string | null;
  dbStatus: PreviewDbStatus;
  summary: PreviewSummary;
  warnings: string[];
  requestedProfile?: PreviewProfile | null;
  appliedProfile?: PreviewProfile | null;
  autoProfileReason?: string | null;
  timeoutStage?: string | null;
  timing?: Record<string, unknown> | null;
  errorCode?: string | null;
  errorMessage?: string | null;
}

export interface PreviewItem {
  previewItemId: number;
  status: PreviewItemStatus;
  reasonCode: string;
  reasonText: string;
  kind: PreviewSource;
  folderLabel: string;
  filename: string;
  path: string;
  fileDate: string | null;
  sizeBytes: number | null;
  modifiedAt: string | null;
  scanMode: "metadata" | "sample" | "full" | "incomplete";
  rowCount: number | null;
  localKeyCount: number | null;
  dbMatchCount: number | null;
  uploadRowEstimate: number | null;
  firstTimestamp: string | null;
  lastTimestamp: string | null;
  deviceIds: string[];
  issues: string[];
  timeoutStage?: string | null;
  timing?: Record<string, unknown> | null;
  errorCode?: string | null;
  errorMessage?: string | null;
}

export interface PreviewPage {
  limit: number;
  offset: number;
  totalItems: number;
}

export interface PreviewResponse {
  run: PreviewRun;
  items: PreviewItem[];
  page: PreviewPage;
}

export interface PreviewQueryParams {
  status?: PreviewItemStatus | "all";
  q?: string;
  sort?: PreviewSortKey;
  order?: SortOrder;
  limit?: number;
  offset?: number;
}

export class ActivePreviewRunError extends Error {
  activePreviewRunId: string;

  constructor(activePreviewRunId: string) {
    super("A preview run is already active");
    this.name = "ActivePreviewRunError";
    this.activePreviewRunId = activePreviewRunId;
  }
}

const defaultOptions: PreviewOptions = {
  profile: "default",
  stableLagMinutes: 3,
  sampleRows: 200,
  chunkRows: 20_000,
  maxFiles: 500,
  maxRunSeconds: 120,
  maxFileSeconds: 30,
  forceFullScan: false,
};

export const stage3ProfileABoundedFullScanOptions: PreviewOptions = {
  ...defaultOptions,
  profile: "stage3_profile_a_bounded_full_scan",
  maxFiles: 3,
  maxRunSeconds: 300,
  maxFileSeconds: 120,
  forceFullScan: true,
};

export const largeSourceOperationalOptions: PreviewOptions = {
  ...defaultOptions,
  profile: "large_source_operational",
  chunkRows: 1_000,
  maxFiles: 500,
  maxRunSeconds: 900,
  maxFileSeconds: 300,
  forceFullScan: false,
};

export function createDefaultPreviewRequest(
  rangeMode: PreviewRangeMode,
  startDate: string | null,
  endDate: string | null,
): PreviewCreateRequest {
  return {
    rangeMode,
    startDate,
    endDate,
    sources: ["plc"],
    options: { ...defaultOptions },
    retryOfRunId: null,
  };
}

export function createLargeSourceOperationalPreviewRequest(
  rangeMode: PreviewRangeMode,
  startDate: string | null,
  endDate: string | null,
): PreviewCreateRequest {
  return {
    rangeMode,
    startDate,
    endDate,
    sources: ["plc"],
    options: { ...largeSourceOperationalOptions },
    retryOfRunId: null,
  };
}

export function createStage3ProfileABoundedFullScanPreviewRequest(
  rangeMode: PreviewRangeMode,
  startDate: string | null,
  endDate: string | null,
): PreviewCreateRequest {
  return {
    rangeMode,
    startDate,
    endDate,
    sources: ["plc"],
    options: { ...stage3ProfileABoundedFullScanOptions },
    retryOfRunId: null,
  };
}

function toCamelPreviewResponse(raw: any): PreviewResponse {
  const run = raw.run ?? {};
  const summary = run.summary ?? {};

  return {
    run: {
      previewRunId: run.previewRunId ?? run.preview_run_id,
      status: run.status,
      requestedAt: run.requestedAt ?? run.requested_at,
      startedAt: run.startedAt ?? run.started_at ?? null,
      finishedAt: run.finishedAt ?? run.finished_at ?? null,
      dbStatus: run.dbStatus ?? run.db_status,
      summary: {
        total: summary.total ?? 0,
        target: summary.target ?? summary.target_count ?? 0,
        alreadyInDb: summary.alreadyInDb ?? summary.already_in_db ?? summary.already_in_db_count ?? 0,
        partialOverlap:
          summary.partialOverlap ?? summary.partial_overlap ?? summary.partial_overlap_count ?? 0,
        risky: summary.risky ?? summary.risky_count ?? 0,
        excluded: summary.excluded ?? summary.excluded_count ?? 0,
        uploadRows: summary.uploadRows ?? summary.upload_rows ?? summary.upload_row_estimate ?? 0,
        dbMatchedRows: summary.dbMatchedRows ?? summary.db_matched_rows ?? summary.db_match_count ?? 0,
      },
      warnings: run.warnings ?? [],
      requestedProfile: run.requestedProfile ?? run.requested_profile ?? null,
      appliedProfile: run.appliedProfile ?? run.applied_profile ?? null,
      autoProfileReason: run.autoProfileReason ?? run.auto_profile_reason ?? null,
      timeoutStage: run.timeoutStage ?? run.timeout_stage ?? null,
      timing: run.timing ?? null,
      errorCode: run.errorCode ?? run.error_code ?? null,
      errorMessage: run.errorMessage ?? run.error_message ?? null,
    },
    items: (raw.items ?? []).map((item: any) => ({
      previewItemId: item.previewItemId ?? item.preview_item_id,
      status: item.status,
      reasonCode: item.reasonCode ?? item.reason_code,
      reasonText: item.reasonText ?? item.reason_text,
      kind: item.kind,
      folderLabel: item.folderLabel ?? item.folder_label,
      filename: item.filename,
      path: item.path,
      fileDate: item.fileDate ?? item.file_date ?? null,
      sizeBytes: item.sizeBytes ?? item.size_bytes ?? null,
      modifiedAt: item.modifiedAt ?? item.modified_at ?? null,
      scanMode: item.scanMode ?? item.scan_mode,
      rowCount: item.rowCount ?? item.row_count ?? null,
      localKeyCount: item.localKeyCount ?? item.local_key_count ?? null,
      dbMatchCount: item.dbMatchCount ?? item.db_match_count ?? null,
      uploadRowEstimate: item.uploadRowEstimate ?? item.upload_row_estimate ?? null,
      firstTimestamp: item.firstTimestamp ?? item.first_timestamp ?? null,
      lastTimestamp: item.lastTimestamp ?? item.last_timestamp ?? null,
      deviceIds: item.deviceIds ?? item.device_ids ?? [],
      issues: item.issues ?? [],
      timeoutStage: item.timeoutStage ?? item.timeout_stage ?? null,
      timing: item.timing ?? null,
      errorCode: item.errorCode ?? item.error_code ?? null,
      errorMessage: item.errorMessage ?? item.error_message ?? null,
    })),
    page: raw.page ?? { limit: 100, offset: 0, totalItems: raw.items?.length ?? 0 },
  };
}

function appendPreviewQuery(url: URL, params: PreviewQueryParams) {
  if (params.status && params.status !== "all") url.searchParams.set("status", params.status);
  if (params.q) url.searchParams.set("q", params.q);
  if (params.sort) url.searchParams.set("sort", params.sort);
  if (params.order) url.searchParams.set("order", params.order);
  if (params.limit) url.searchParams.set("limit", String(params.limit));
  if (params.offset) url.searchParams.set("offset", String(params.offset));
}

export async function createUploadPreview(
  request: PreviewCreateRequest,
): Promise<PreviewCreateResponse> {
  const response = await apiFetch(
    "/api/upload/preview",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    },
    { mutating: true },
  );

  if (!response.ok) {
    if (response.status === 409) {
      const raw = await response.json().catch(() => null);
      const activePreviewRunId = raw?.detail?.activePreviewRunId;
      if (typeof activePreviewRunId === "string" && activePreviewRunId.length > 0) {
        throw new ActivePreviewRunError(activePreviewRunId);
      }
    }
    throw new Error("Upload preview could not be started");
  }

  const raw = await response.json();
  return {
    previewRunId: raw.previewRunId ?? raw.preview_run_id,
    status: raw.status,
    pollUrl: raw.pollUrl ?? raw.poll_url,
  };
}

export async function fetchUploadPreview(
  previewRunId: string,
  params: PreviewQueryParams,
): Promise<PreviewResponse> {
  const url = new URL(`/api/upload/preview/${previewRunId}`, window.location.origin);
  appendPreviewQuery(url, params);

  const response = await fetch(url.pathname + url.search);
  if (!response.ok) {
    throw new Error("Upload preview could not be loaded");
  }
  return toCamelPreviewResponse(await response.json());
}

export async function fetchLatestUploadPreview(
  params: PreviewQueryParams,
  completedOnly = false,
): Promise<PreviewResponse | null> {
  const url = new URL("/api/upload/preview/latest", window.location.origin);
  appendPreviewQuery(url, params);
  if (completedOnly) url.searchParams.set("completedOnly", "true");

  const response = await fetch(url.pathname + url.search);
  if (response.status === 404) return null;
  if (!response.ok) {
    throw new Error("Latest upload preview could not be loaded");
  }
  return toCamelPreviewResponse(await response.json());
}

export async function cancelUploadPreview(previewRunId: string): Promise<PreviewCreateResponse> {
  const response = await apiFetch(
    `/api/upload/preview/${previewRunId}/cancel`,
    { method: "POST" },
    { mutating: true },
  );
  if (!response.ok) {
    throw new Error("Upload preview could not be cancelled");
  }
  const raw = await response.json();
  return {
    previewRunId: raw.previewRunId ?? raw.preview_run_id,
    status: raw.status,
    pollUrl: raw.pollUrl ?? raw.poll_url ?? `/api/upload/preview/${previewRunId}`,
  };
}
