export type UploadJobMode = "preview_targets" | "retry_failed";
export type UploadJobStatus =
  | "queued"
  | "running"
  | "succeeded"
  | "partial_failed"
  | "failed"
  | "pausing"
  | "paused"
  | "cancelling"
  | "cancelled"
  | "interrupted";
export type UploadJobFileStatus =
  | "queued"
  | "running"
  | "succeeded"
  | "failed"
  | "skipped"
  | "cancelled"
  | "interrupted";
export type JobEventLevel = "debug" | "info" | "warning" | "error";

export interface UploadJobOptions {
  batchRows: number;
  chunkRows: number;
  maxWorkers: number;
  httpTimeoutSeconds: number;
  retryAttempts: number;
}

export interface UploadJobCreateResponse {
  jobId: string;
  status: UploadJobStatus;
  detailUrl: string;
  eventsUrl: string;
}

export interface UploadJobSummary {
  totalFiles: number;
  succeededFiles: number;
  failedFiles: number;
  cancelledFiles: number;
  totalRows: number;
  processedRows: number;
  uploadedRows: number;
  insertedRows: number;
  warningCount: number;
}

export interface UploadJob {
  jobId: string;
  previewRunId: string | null;
  retryOfJobId: string | null;
  mode: UploadJobMode;
  status: UploadJobStatus;
  requestedAt: string;
  startedAt: string | null;
  finishedAt: string | null;
  actor: string;
  summary: UploadJobSummary;
  errorCode: string | null;
  errorMessage: string | null;
}

export interface UploadJobFile {
  jobFileId: number;
  jobId: string;
  previewItemId: number | null;
  fileKey: string;
  folderLabel: string;
  folderPath: string;
  filename: string;
  path: string;
  kind: string;
  fileDate: string | null;
  fileSignature: string;
  status: UploadJobFileStatus;
  rowCount: number | null;
  processedRows: number;
  uploadedRows: number;
  insertedRows: number;
  resumeOffset: number;
  retryCount: number;
  startedAt: string | null;
  finishedAt: string | null;
  lastErrorCode: string | null;
  lastErrorMessage: string | null;
}

export interface JobEvent {
  eventId: number;
  jobId: string;
  seq: number;
  ts: string;
  level: JobEventLevel;
  eventType: string;
  message: string;
  jobFileId: number | null;
  data: Record<string, unknown>;
}

export interface UploadJobDetail {
  job: UploadJob;
  files: UploadJobFile[];
  events: JobEvent[];
  eventCursor: {
    latestSeq: number;
  };
}

export class ActiveUploadJobError extends Error {
  activeJobId: string;

  constructor(activeJobId: string) {
    super("An upload job is already active");
    this.name = "ActiveUploadJobError";
    this.activeJobId = activeJobId;
  }
}

const defaultOptions: UploadJobOptions = {
  batchRows: 2000,
  chunkRows: 10000,
  maxWorkers: 1,
  httpTimeoutSeconds: 30,
  retryAttempts: 3,
};

export async function createUploadJob(previewRunId: string): Promise<UploadJobCreateResponse> {
  const response = await fetch("/api/upload/jobs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      previewRunId,
      mode: "preview_targets",
      options: defaultOptions,
    }),
  });
  if (!response.ok) {
    if (response.status === 409) {
      const raw = await response.json().catch(() => null);
      const activeJobId = raw?.detail?.activeJobId;
      if (typeof activeJobId === "string" && activeJobId) throw new ActiveUploadJobError(activeJobId);
    }
    const raw = await response.json().catch(() => null);
    throw new Error(raw?.detail?.reason ?? "Upload job could not be started");
  }
  return normalizeCreateResponse(await response.json());
}

export async function retryUploadJob(jobId: string): Promise<UploadJobCreateResponse> {
  const response = await fetch(`/api/upload/jobs/${jobId}/retry`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ includeInterrupted: true, includeCancelled: false, options: defaultOptions }),
  });
  if (!response.ok) throw new Error("Retry job could not be started");
  return normalizeCreateResponse(await response.json());
}

export async function fetchLatestUploadJob(): Promise<UploadJobDetail | null> {
  const response = await fetch("/api/upload/jobs/latest");
  if (response.status === 404) return null;
  if (!response.ok) throw new Error("Latest upload job could not be loaded");
  return normalizeJobDetail(await response.json());
}

export async function fetchUploadJob(jobId: string): Promise<UploadJobDetail> {
  const response = await fetch(`/api/upload/jobs/${jobId}`);
  if (!response.ok) throw new Error("Upload job could not be loaded");
  return normalizeJobDetail(await response.json());
}

export async function controlUploadJob(
  jobId: string,
  action: "pause" | "resume" | "cancel",
): Promise<UploadJobDetail> {
  const response = await fetch(`/api/upload/jobs/${jobId}/${action}`, { method: "POST" });
  if (!response.ok) throw new Error(`Upload job could not ${action}`);
  return normalizeJobDetail(await response.json());
}

function normalizeCreateResponse(raw: any): UploadJobCreateResponse {
  return {
    jobId: raw.jobId ?? raw.job_id,
    status: raw.status,
    detailUrl: raw.detailUrl ?? raw.detail_url,
    eventsUrl: raw.eventsUrl ?? raw.events_url,
  };
}

export function normalizeJobEvent(raw: any): JobEvent {
  return {
    eventId: raw.eventId ?? raw.event_id,
    jobId: raw.jobId ?? raw.job_id,
    seq: raw.seq,
    ts: raw.ts,
    level: raw.level,
    eventType: raw.eventType ?? raw.event_type,
    message: raw.message,
    jobFileId: raw.jobFileId ?? raw.job_file_id ?? null,
    data: raw.data ?? {},
  };
}

function normalizeJobDetail(raw: any): UploadJobDetail {
  const job = raw.job ?? {};
  const summary = job.summary ?? {};
  return {
    job: {
      jobId: job.jobId ?? job.job_id,
      previewRunId: job.previewRunId ?? job.preview_run_id ?? null,
      retryOfJobId: job.retryOfJobId ?? job.retry_of_job_id ?? null,
      mode: job.mode,
      status: job.status,
      requestedAt: job.requestedAt ?? job.requested_at,
      startedAt: job.startedAt ?? job.started_at ?? null,
      finishedAt: job.finishedAt ?? job.finished_at ?? null,
      actor: job.actor ?? "local_operator",
      summary: {
        totalFiles: summary.totalFiles ?? summary.total_files ?? 0,
        succeededFiles: summary.succeededFiles ?? summary.succeeded_files ?? 0,
        failedFiles: summary.failedFiles ?? summary.failed_files ?? 0,
        cancelledFiles: summary.cancelledFiles ?? summary.cancelled_files ?? 0,
        totalRows: summary.totalRows ?? summary.total_rows ?? 0,
        processedRows: summary.processedRows ?? summary.processed_rows ?? 0,
        uploadedRows: summary.uploadedRows ?? summary.uploaded_rows ?? 0,
        insertedRows: summary.insertedRows ?? summary.inserted_rows ?? 0,
        warningCount: summary.warningCount ?? summary.warning_count ?? 0,
      },
      errorCode: job.errorCode ?? job.error_code ?? null,
      errorMessage: job.errorMessage ?? job.error_message ?? null,
    },
    files: (raw.files ?? []).map((file: any) => ({
      jobFileId: file.jobFileId ?? file.job_file_id,
      jobId: file.jobId ?? file.job_id,
      previewItemId: file.previewItemId ?? file.preview_item_id ?? null,
      fileKey: file.fileKey ?? file.file_key,
      folderLabel: file.folderLabel ?? file.folder_label,
      folderPath: file.folderPath ?? file.folder_path,
      filename: file.filename,
      path: file.path,
      kind: file.kind,
      fileDate: file.fileDate ?? file.file_date ?? null,
      fileSignature: file.fileSignature ?? file.file_signature,
      status: file.status,
      rowCount: file.rowCount ?? file.row_count ?? null,
      processedRows: file.processedRows ?? file.processed_rows ?? 0,
      uploadedRows: file.uploadedRows ?? file.uploaded_rows ?? 0,
      insertedRows: file.insertedRows ?? file.inserted_rows ?? 0,
      resumeOffset: file.resumeOffset ?? file.resume_offset ?? 0,
      retryCount: file.retryCount ?? file.retry_count ?? 0,
      startedAt: file.startedAt ?? file.started_at ?? null,
      finishedAt: file.finishedAt ?? file.finished_at ?? null,
      lastErrorCode: file.lastErrorCode ?? file.last_error_code ?? null,
      lastErrorMessage: file.lastErrorMessage ?? file.last_error_message ?? null,
    })),
    events: (raw.events ?? []).map(normalizeJobEvent),
    eventCursor: {
      latestSeq: raw.eventCursor?.latestSeq ?? raw.event_cursor?.latest_seq ?? 0,
    },
  };
}
