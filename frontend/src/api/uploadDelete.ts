import { apiFetch } from "./client";

export type DeletePreflightStatus = "ready" | "blocked" | "expired";
export type DeleteRunStatus =
  | "preparing"
  | "running"
  | "finalizing"
  | "blocked"
  | "failed"
  | "succeeded"
  | "commit_unknown"
  | "reconciling"
  | "reconciled_succeeded"
  | "reconciled_rolled_back"
  | "reconciliation_failed";

export interface DeleteDbTargetGuard {
  status: "passed" | "blocked";
  targetClass: string;
  fingerprintHash: string | null;
  reasonCode: string | null;
}

export interface DeletePreflightResponse {
  preflightId: string;
  status: DeletePreflightStatus;
  selectedItemCount: number;
  selectedKeyCount: number;
  rollbackReady: boolean;
  rollbackBlockers: string[];
  dbTargetGuard: DeleteDbTargetGuard;
  selectionHash: string;
  keysetHash: string;
  expiresAt: string;
  reasonCode: string | null;
}

export interface DeleteJobCreateResponse {
  deleteRunId: string;
  status: DeleteRunStatus;
  expectedDeleteKeys: number;
  deletedKeys: number;
  rollbackReady: boolean;
  recoveryRequired: boolean;
  rawKeysReturned: boolean;
}

export interface DeleteJob {
  deleteRunId: string;
  preflightId: string;
  previewRunId: string;
  status: DeleteRunStatus;
  expectedDeleteKeys: number;
  deletedKeys: number;
  rollbackReady: boolean;
  recoveryRequired: boolean;
  dbFingerprintHash: string | null;
  selectionHash: string | null;
  keysetHash: string | null;
  errorCode: string | null;
  errorMessage: string | null;
  startedAt: string | null;
  finishedAt: string | null;
}

export interface DeleteJobLatestResponse {
  job: DeleteJob;
  activeDeleteBlocker: boolean;
}

export interface DeleteReconcileResponse {
  deleteRunId: string;
  status: DeleteRunStatus;
  expectedDeleteKeys: number;
  keysPresent: number;
  keysAbsent: number;
  recoveryRequired: boolean;
  rawKeysReturned: boolean;
}

export async function createDeletePreflight(input: {
  previewRunId: string;
  previewItemIds: number[];
  expectedAlreadyInDbItems: number;
}): Promise<DeletePreflightResponse> {
  const response = await apiFetch(
    "/api/upload/delete/preflight",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    },
    { mutating: true },
  );
  const raw = await readJson(response);
  if (!response.ok) throw new Error(reasonFrom(raw, "Delete preflight failed"));
  return normalizeDeletePreflight(raw);
}

export async function startDeleteJob(input: {
  preflightId: string;
  expectedDeleteKeys: number;
  typedDeleteKeys: string;
  acknowledgeNoUndo: boolean;
  acknowledgeRollbackRequiresFreshPreviewAndStartUpload: boolean;
}): Promise<DeleteJobCreateResponse> {
  const response = await apiFetch(
    "/api/upload/delete/jobs",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    },
    { mutating: true },
  );
  const raw = await readJson(response);
  if (!response.ok) throw new Error(reasonFrom(raw, "Delete job failed"));
  return normalizeDeleteJobCreate(raw);
}

export async function fetchLatestDeleteJob(): Promise<DeleteJobLatestResponse | null> {
  const response = await fetch("/api/upload/delete/jobs/latest");
  if (response.status === 404) return null;
  const raw = await readJson(response);
  if (!response.ok) throw new Error(reasonFrom(raw, "Latest delete job could not be loaded"));
  return {
    job: normalizeDeleteJob(raw.job ?? {}),
    activeDeleteBlocker: raw.activeDeleteBlocker ?? raw.active_delete_blocker ?? false,
  };
}

export async function reconcileDeleteJob(
  deleteRunId: string,
  acknowledgeReconciliationRetry = false,
): Promise<DeleteReconcileResponse> {
  const response = await apiFetch(
    `/api/upload/delete/jobs/${encodeURIComponent(deleteRunId)}/reconcile`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ acknowledgeReconciliationRetry }),
    },
    { mutating: true },
  );
  const raw = await readJson(response);
  if (!response.ok) throw new Error(reasonFrom(raw, "Delete reconcile failed"));
  return {
    deleteRunId: raw.deleteRunId ?? raw.delete_run_id,
    status: raw.status,
    expectedDeleteKeys: raw.expectedDeleteKeys ?? raw.expected_delete_keys ?? 0,
    keysPresent: raw.keysPresent ?? raw.keys_present ?? 0,
    keysAbsent: raw.keysAbsent ?? raw.keys_absent ?? 0,
    recoveryRequired: raw.recoveryRequired ?? raw.recovery_required ?? false,
    rawKeysReturned: raw.rawKeysReturned ?? raw.raw_keys_returned ?? false,
  };
}

async function readJson(response: Response): Promise<any> {
  return response.json().catch(() => null);
}

function reasonFrom(raw: any, fallback: string): string {
  return raw?.detail?.reason ?? raw?.detail?.code ?? fallback;
}

function normalizeDeletePreflight(raw: any): DeletePreflightResponse {
  const guard = raw.dbTargetGuard ?? raw.db_target_guard ?? {};
  return {
    preflightId: raw.preflightId ?? raw.preflight_id,
    status: raw.status,
    selectedItemCount: raw.selectedItemCount ?? raw.selected_item_count ?? 0,
    selectedKeyCount: raw.selectedKeyCount ?? raw.selected_key_count ?? 0,
    rollbackReady: raw.rollbackReady ?? raw.rollback_ready ?? false,
    rollbackBlockers: raw.rollbackBlockers ?? raw.rollback_blockers ?? [],
    dbTargetGuard: {
      status: guard.status ?? "blocked",
      targetClass: guard.targetClass ?? guard.target_class ?? "unknown",
      fingerprintHash: guard.fingerprintHash ?? guard.fingerprint_hash ?? null,
      reasonCode: guard.reasonCode ?? guard.reason_code ?? null,
    },
    selectionHash: raw.selectionHash ?? raw.selection_hash,
    keysetHash: raw.keysetHash ?? raw.keyset_hash,
    expiresAt: raw.expiresAt ?? raw.expires_at,
    reasonCode: raw.reasonCode ?? raw.reason_code ?? null,
  };
}

function normalizeDeleteJobCreate(raw: any): DeleteJobCreateResponse {
  return {
    deleteRunId: raw.deleteRunId ?? raw.delete_run_id,
    status: raw.status,
    expectedDeleteKeys: raw.expectedDeleteKeys ?? raw.expected_delete_keys ?? 0,
    deletedKeys: raw.deletedKeys ?? raw.deleted_keys ?? 0,
    rollbackReady: raw.rollbackReady ?? raw.rollback_ready ?? false,
    recoveryRequired: raw.recoveryRequired ?? raw.recovery_required ?? false,
    rawKeysReturned: raw.rawKeysReturned ?? raw.raw_keys_returned ?? false,
  };
}

function normalizeDeleteJob(raw: any): DeleteJob {
  return {
    deleteRunId: raw.deleteRunId ?? raw.delete_run_id,
    preflightId: raw.preflightId ?? raw.preflight_id,
    previewRunId: raw.previewRunId ?? raw.preview_run_id,
    status: raw.status,
    expectedDeleteKeys: raw.expectedDeleteKeys ?? raw.expected_delete_keys ?? 0,
    deletedKeys: raw.deletedKeys ?? raw.deleted_keys ?? 0,
    rollbackReady: raw.rollbackReady ?? raw.rollback_ready ?? false,
    recoveryRequired: raw.recoveryRequired ?? raw.recovery_required ?? false,
    dbFingerprintHash: raw.dbFingerprintHash ?? raw.db_fingerprint_hash ?? null,
    selectionHash: raw.selectionHash ?? raw.selection_hash ?? null,
    keysetHash: raw.keysetHash ?? raw.keyset_hash ?? null,
    errorCode: raw.errorCode ?? raw.error_code ?? null,
    errorMessage: raw.errorMessage ?? raw.error_message ?? null,
    startedAt: raw.startedAt ?? raw.started_at ?? null,
    finishedAt: raw.finishedAt ?? raw.finished_at ?? null,
  };
}
