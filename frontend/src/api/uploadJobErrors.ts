export const UPLOAD_WORKER_UNAVAILABLE_REASON = "upload_worker_unavailable";
export const UPLOAD_WORKER_RECONCILIATION_FAILED_REASON = "upload_worker_reconciliation_failed";
export const UPLOAD_WORKER_RETRY_RECOVERY =
  "Restart the web console from the launcher, then inspect the persisted failed upload job before retrying.";
export const UPLOAD_WORKER_RESTART_RECOVERY =
  "Restart the web console from the launcher before starting or retrying an upload job.";
export type UploadWorkerUnavailableReason =
  | typeof UPLOAD_WORKER_UNAVAILABLE_REASON
  | typeof UPLOAD_WORKER_RECONCILIATION_FAILED_REASON;

export class UploadWorkerUnavailableError extends Error {
  jobId: string;
  reason: UploadWorkerUnavailableReason;
  restartRequired: boolean;
  recovery: string;

  constructor(
    jobId: string,
    reason: UploadWorkerUnavailableReason,
    restartRequired: boolean,
    recovery: string,
  ) {
    super(recovery);
    this.name = "UploadWorkerUnavailableError";
    this.jobId = jobId;
    this.reason = reason;
    this.restartRequired = restartRequired;
    this.recovery = recovery;
  }
}

export function uploadWorkerRecoveryTranslationKey(
  error: UploadWorkerUnavailableError,
): "upload.job.workerUnavailableRecovery" | "upload.job.workerReconciliationFailedRecovery" {
  return error.reason === UPLOAD_WORKER_RECONCILIATION_FAILED_REASON
    ? "upload.job.workerReconciliationFailedRecovery"
    : "upload.job.workerUnavailableRecovery";
}

export function shouldClearRecoveredWorkerFailure(
  error: UploadWorkerUnavailableError,
  jobId: string | null | undefined,
  isTerminal: boolean,
): boolean {
  return error.reason === UPLOAD_WORKER_RECONCILIATION_FAILED_REASON
    && error.jobId === jobId
    && isTerminal;
}

export function parseUploadWorkerUnavailableError(
  response: Response,
  detail: unknown,
): UploadWorkerUnavailableError | null {
  if (response.status !== 503 || !isRecord(detail)) return null;
  const reason = detail.reason;
  if (
    reason !== UPLOAD_WORKER_UNAVAILABLE_REASON &&
    reason !== UPLOAD_WORKER_RECONCILIATION_FAILED_REASON
  ) {
    return null;
  }
  const jobId = workerUnavailableJobId(response, detail.jobId);
  const restartRequired = true;
  const recovery = reason === UPLOAD_WORKER_RECONCILIATION_FAILED_REASON
    ? UPLOAD_WORKER_RESTART_RECOVERY
    : UPLOAD_WORKER_RETRY_RECOVERY;
  if (
    !jobId ||
    detail.restartRequired !== restartRequired ||
    detail.recovery !== recovery
  ) {
    return null;
  }
  return new UploadWorkerUnavailableError(jobId, reason, restartRequired, recovery);
}

function canonicalUploadJobId(value: unknown): string | null {
  return typeof value === "string" && /^upl_[0-9a-f]{12}$/.test(value) ? value : null;
}

function workerUnavailableJobId(response: Response, bodyJobId: unknown): string | null {
  const prefix = "/api/upload/jobs/";
  const location = response.headers.get("Location");
  const locationJobId = location?.startsWith(prefix) ? canonicalUploadJobId(location.slice(prefix.length)) : null;
  const canonicalBodyJobId = canonicalUploadJobId(bodyJobId);
  return canonicalBodyJobId && canonicalBodyJobId === locationJobId ? canonicalBodyJobId : null;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
