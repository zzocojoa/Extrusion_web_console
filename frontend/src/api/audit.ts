export type AuditResult = "success" | "failure" | "cancelled" | "blocked";
export type AuditSort = "ts" | "action" | "result" | "targetType";
export type AuditOrder = "asc" | "desc";

export interface AuditQuery {
  fromTs?: string;
  toTs?: string;
  action?: string;
  result?: AuditResult;
  targetType?: string;
  targetId?: string;
  jobId?: string;
  requestId?: string;
  q?: string;
  limit?: number;
  offset?: number;
  sort?: AuditSort;
  order?: AuditOrder;
}

export interface AuditLog {
  auditId: number;
  ts: string;
  actor: string;
  action: string;
  targetType: string;
  targetId: string | null;
  params: Record<string, unknown>;
  result: AuditResult;
  errorCode: string | null;
  errorMessage: string | null;
  jobId: string | null;
  requestId: string | null;
  createdAt: string;
}

export interface AuditPage {
  limit: number;
  offset: number;
  totalItems: number;
  hasNext: boolean;
  hasPrevious: boolean;
}

export interface AuditLogListResponse {
  items: AuditLog[];
  page: AuditPage;
  filters: AuditQuery;
}

export async function fetchAuditLogs(query: AuditQuery): Promise<AuditLogListResponse> {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined || value === null || value === "") continue;
    params.set(key, String(value));
  }
  const response = await fetch(`/api/audit?${params.toString()}`);
  if (!response.ok) throw new Error("Audit logs could not be loaded");
  return normalizeAuditResponse(await response.json());
}

export function normalizeAuditResponse(raw: any): AuditLogListResponse {
  const page = raw.page ?? {};
  return {
    items: (raw.items ?? []).map(normalizeAuditLog),
    page: {
      limit: page.limit ?? 50,
      offset: page.offset ?? 0,
      totalItems: page.totalItems ?? page.total_items ?? 0,
      hasNext: page.hasNext ?? page.has_next ?? false,
      hasPrevious: page.hasPrevious ?? page.has_previous ?? false,
    },
    filters: raw.filters ?? {},
  };
}

function normalizeAuditLog(raw: any): AuditLog {
  return {
    auditId: raw.auditId ?? raw.audit_id,
    ts: raw.ts,
    actor: raw.actor ?? "local_operator",
    action: raw.action,
    targetType: raw.targetType ?? raw.target_type,
    targetId: raw.targetId ?? raw.target_id ?? null,
    params: raw.params ?? {},
    result: raw.result,
    errorCode: raw.errorCode ?? raw.error_code ?? null,
    errorMessage: raw.errorMessage ?? raw.error_message ?? null,
    jobId: raw.jobId ?? raw.job_id ?? null,
    requestId: raw.requestId ?? raw.request_id ?? null,
    createdAt: raw.createdAt ?? raw.created_at ?? raw.ts,
  };
}
