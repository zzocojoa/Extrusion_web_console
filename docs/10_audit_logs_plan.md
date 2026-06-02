# Audit Logs UI/API Implementation Plan

Status: decision-complete implementation plan
Branch: `codex/audit-logs-ui`
Scope: v1 Core Ops, Logs page Audit Logs tab and backend read API
Source of truth: `docs/00_product_scope.md`, `docs/02_engineering_plan.md`, `docs/03_ui_ux_plan.md`, `docs/04_design_system.md`

## 1. Goal

Audit Logs must make operator actions and critical background failures traceable from the web console.

The implementation must let an operator answer:

- What action was requested?
- Who or what requested it?
- Which job, preview run, runtime operation, or target did it affect?
- Did it succeed, fail, get blocked, or get cancelled?
- What safe, redacted reason or parameter summary explains it?

This feature is not a destructive control surface. It is a read-only operational evidence surface.

## 2. Product Decisions

- Audit Logs are part of v1 Core Ops.
- Audit Logs live under the existing `Logs` page as a separate `Audit Logs` tab.
- `Job Logs` and `Audit Logs` must remain visually and conceptually separate.
- Audit Logs use a light table, not the dark raw log viewer.
- The existing `audit_log` SQLite table is the canonical source.
- The new work adds query/API/UI behavior. It does not replace upload/runtime behavior.
- `audit_log` remains append-only. No delete, edit, archive, or cleanup UI is added.
- No arbitrary SQL query UI is added.
- Secrets, tokens, Supabase keys, connection strings, bearer tokens, and credential-bearing URLs must never be displayed.
- Full Data Mgmt, Cycle Ops, Training Dataset Builder, Supabase delete UI, Grafana iframe, and multi-user LAN web access remain out of scope.

## 3. Current State

Implemented audit writers already exist in upload/runtime paths:

- Upload job/retry/pause/resume/cancel paths write some audit rows.
- Runtime start/stop success/failure/blocked paths write audit rows.
- Passive runtime status polling success does not write audit rows.
- The Logs page is still a placeholder.
- Dashboard shows a mock/recent audit summary, not a real audit query.

Current `audit_log` shape exists in both upload and runtime repository bootstraps:

```text
audit_log(
  audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  actor TEXT NOT NULL DEFAULT 'local_operator',
  action TEXT NOT NULL,
  target_type TEXT NOT NULL,
  target_id TEXT,
  params_json_redacted TEXT NOT NULL DEFAULT '{}',
  result TEXT NOT NULL CHECK(result IN ('success','failure','cancelled','blocked')),
  error_code TEXT,
  error_message TEXT,
  job_id TEXT,
  request_id TEXT,
  created_at TEXT NOT NULL
)
```

Compatibility risks to preserve in the plan:

- Runtime action names in code are `runtime.start`, `runtime.stop`, and `runtime.interrupted`; do not invent `runtime.supabase.*` names for UI/API labels.
- `request_id` exists but is nullable and often not populated in v1.
- `params_json_redacted` is already redacted, but upload/runtime redaction code is not yet unified.
- `error_message` can contain unsafe diagnostic detail if future writers do not sanitize it before insert.
- Product scope requires `settings.save` and `upload.preview` audit records, but they are not fully implemented yet.

## 4. Backend API

### 4.1 Endpoints

Implement one v1 read endpoint first:

```text
GET /api/audit
```

No mutating audit endpoint exists in v1.

Forbidden endpoints:

```text
DELETE /api/audit/*
PUT    /api/audit/*
PATCH  /api/audit/*
POST   /api/audit/query
POST   /api/audit/export
```

Export can be revisited later, but v1 should avoid creating a second leakage path for redacted fields.

### 4.2 Query Parameters

```text
fromTs: ISO datetime, optional
toTs: ISO datetime, optional
action: string, optional, exact match
result: success | failure | cancelled | blocked, optional
targetType: string, optional, exact match
targetId: string, optional, exact match
jobId: string, optional, exact match
requestId: string, optional, exact match
q: string, optional, safe text search
limit: int, default 50, min 1, max 200
offset: int, default 0, min 0
sort: ts | action | result | targetType, default ts
order: desc | asc, default desc
```

`q` searches only safe scalar columns:

- `action`
- `target_type`
- `target_id`
- `job_id`
- `request_id`
- `error_code`
- sanitized `error_message`

`q` must not perform deep JSON search on `params_json_redacted` in v1. JSON search is slow, hard to reason about, and easy to misuse as an arbitrary query surface.

### 4.3 Response DTO

Use the existing `ApiModel` camelCase alias pattern.

```python
class AuditResult(str, Enum):
    success = "success"
    failure = "failure"
    cancelled = "cancelled"
    blocked = "blocked"

class AuditLogDto(ApiModel):
    audit_id: int
    ts: datetime
    actor: str
    action: str
    target_type: str
    target_id: str | None
    params: dict[str, Any]
    result: AuditResult
    error_code: str | None
    error_message: str | None
    job_id: str | None
    request_id: str | None
    created_at: datetime

class AuditPageDto(ApiModel):
    limit: int
    offset: int
    total_items: int
    has_next: bool
    has_previous: bool

class AuditFilterEchoDto(ApiModel):
    from_ts: datetime | None
    to_ts: datetime | None
    action: str | None
    result: AuditResult | None
    target_type: str | None
    target_id: str | None
    job_id: str | None
    request_id: str | None
    q: str | None
    sort: str
    order: str

class AuditLogListResponse(ApiModel):
    items: list[AuditLogDto]
    page: AuditPageDto
    filters: AuditFilterEchoDto
```

Frontend JSON shape:

```json
{
  "items": [
    {
      "auditId": 101,
      "ts": "2026-06-02T08:00:00+00:00",
      "actor": "local_operator",
      "action": "upload.start",
      "targetType": "upload_job",
      "targetId": "job_abc",
      "params": {"previewRunId": "preview_123", "mode": "preview_targets"},
      "result": "success",
      "errorCode": null,
      "errorMessage": null,
      "jobId": "job_abc",
      "requestId": null,
      "createdAt": "2026-06-02T08:00:00+00:00"
    }
  ],
  "page": {
    "limit": 50,
    "offset": 0,
    "totalItems": 1,
    "hasNext": false,
    "hasPrevious": false
  },
  "filters": {
    "fromTs": null,
    "toTs": null,
    "action": null,
    "result": null,
    "targetType": null,
    "targetId": null,
    "jobId": null,
    "requestId": null,
    "q": null,
    "sort": "ts",
    "order": "desc"
  }
}
```

### 4.4 Repository

Add:

```text
backend/app/db/audit_repository.py
backend/app/schemas/audit.py
backend/app/api/audit.py
```

`AuditRepository` responsibilities:

- Bootstrap `audit_log` compatibility table if needed.
- Add read-only query methods.
- Decode `params_json_redacted` to `params`.
- Apply strict sort allowlist.
- Apply server-side pagination.
- Return rows and total count from the same filter set.

Do not move all existing writers in the first implementation if it increases risk. The safe sequence is:

1. Add shared `audit_repository.py` with query + redaction helpers.
2. Keep existing upload/runtime append paths working.
3. Gradually route upload/runtime append calls through the shared repository in a later small refactor if duplication becomes risky.

## 5. Schema And Index Decisions

No column migration is required for v1.

Add read indexes:

```sql
CREATE INDEX IF NOT EXISTS idx_audit_log_ts
  ON audit_log(ts DESC);

CREATE INDEX IF NOT EXISTS idx_audit_log_action_ts
  ON audit_log(action, ts DESC);

CREATE INDEX IF NOT EXISTS idx_audit_log_result_ts
  ON audit_log(result, ts DESC);

CREATE INDEX IF NOT EXISTS idx_audit_log_target_ts
  ON audit_log(target_type, target_id, ts DESC);
```

Keep existing indexes:

```text
idx_audit_log_job_id
idx_audit_log_runtime
```

Append-only hardening:

- Application code must expose only insert/query methods.
- `AuditRepository` must not expose update/delete methods.
- Add SQLite triggers in v1 if tests confirm they do not break existing bootstraps:

```sql
CREATE TRIGGER IF NOT EXISTS audit_log_no_update
BEFORE UPDATE ON audit_log
BEGIN
  SELECT RAISE(ABORT, 'audit_log_append_only');
END;

CREATE TRIGGER IF NOT EXISTS audit_log_no_delete
BEFORE DELETE ON audit_log
BEGIN
  SELECT RAISE(ABORT, 'audit_log_append_only');
END;
```

If a future maintenance workflow needs compaction, it must be an explicit offline maintenance procedure, not a web UI feature.

## 6. Redaction Policy

### 6.1 Storage Rule

Only safe params may be stored in `params_json_redacted`.

Preferred identifiers:

- `previewRunId`
- `jobId`
- `operationId`
- `requestId`
- `targetType`
- `targetId`
- `fileKey`
- `folderLabel`
- `filename`
- `mode`
- `status`
- `errorCode`

Avoid absolute local paths in audit params. If path context is needed, store `folderLabel`, `filename`, or a stable hash.

### 6.2 Shared Redaction Helper

Create one shared recursive redaction helper and use it in all future audit writers.

Redact keys containing:

```text
password
token
secret
key
authorization
credential
dsn
connection
conn_str
database_url
db_url
service_role
anon_key
service_key
```

Redact values matching:

- `Authorization: Bearer ...`
- JWT-looking values beginning with `eyJ`
- URLs containing credentials, for example `postgres://user:password@host/db`
- Supabase anon/service role key patterns

Display redaction token:

```text
[redacted]
```

Do not use a decorative mask in API output. UI can render `[redacted]` as a muted chip.

### 6.3 Error Message Policy

`error_message` must be sanitized before insert or before response.

Decision:

- Backend API must sanitize `error_message` before returning it.
- Future audit writers should sanitize before insert.
- `error_message` is capped at 500 characters in the API response.
- Full raw command output must not be placed in `audit_log.error_message`.
- Detailed diagnostics belong in `job_events` or `runtime_events`, also redacted.

## 7. Action And Result Display Rules

### 7.1 Canonical Action Groups

```text
upload.preview
upload.start
upload.retry
upload.pause
upload.resume
upload.cancel
upload.succeeded
upload.partial_failed
upload.failed
upload.cancelled
upload.interrupted
runtime.start
runtime.stop
runtime.interrupted
settings.save
```

`settings.save` and `upload.preview` are product-required audit actions. If implementation begins before those writers exist, the Audit Logs page must still support their display shape and tests must document the gap.

### 7.2 Result Mapping

```text
success   -> ready tone, quiet
failure   -> failed tone, prominent
blocked   -> blocked tone, prominent
cancelled -> attention tone, visible but less severe than failure
```

Every row must show icon + label + color. Color alone is not enough.

### 7.3 Operator Labels

Use stable English action ids in API. Translate labels in UI:

```text
upload.start -> Start upload / 업로드 시작
upload.retry -> Retry failed files / 실패 파일 재시도
upload.pause -> Pause upload / 업로드 일시정지
upload.resume -> Resume upload / 업로드 재개
upload.cancel -> Cancel upload / 업로드 취소
runtime.start -> Start Local Supabase / Local Supabase 시작
runtime.stop -> Stop Local Supabase / Local Supabase 중지
settings.save -> Save settings / 설정 저장
```

Unknown actions remain visible as raw ids, with muted styling and no crash.

## 8. Logs Page IA

The `Logs` page has two tabs:

```text
Logs
  [Job Logs] [Audit Logs]
```

Default tab:

- `Job Logs`, because raw operational diagnosis is often the immediate path from an upload failure.

Deep links:

```text
Logs -> ?tab=job&jobId={jobId}
Logs -> ?tab=audit&jobId={jobId}
Logs -> ?tab=audit&auditId={auditId}
Logs -> ?tab=audit&result=failure
```

The current frontend uses app state instead of full routing. The implementation can model deep links as internal page state first, but URL query support is preferred if it does not require a routing rewrite.

## 9. Audit Logs UI

### 9.1 Layout

Audit Logs tab structure:

```text
Logs
  Tab bar: Job Logs | Audit Logs

  Audit Logs toolbar
    Date range
    Result select
    Action select
    Job ID input
    Target search
    Text search
    [Failures only] toggle
    [Clear filters]

  Summary strip
    Total visible
    Failure count
    Blocked count
    Last audit time

  Audit table
    rows

  Pagination
    Previous / Next
    limit selector
```

### 9.2 Table Columns

Column order:

```text
Time
Result
Action
Target
Actor
Job ID
Params
Error
```

Minimum widths:

```text
Time    156px
Result  128px
Action  160px
Target  220px
Actor   120px
Job ID  160px
Params  280px
Error   320px
```

Table min width: `1420px`.

Below available width, wrap table in horizontal overflow. Do not reshape audit rows into cards for desktop/tablet widths. This follows the Dashboard Variant D table-first direction and `docs/04_design_system.md`.

### 9.3 Params Display

Default cell:

- Compact redacted JSON summary.
- Show at most three key-value chips.
- If more keys exist, show `+N`.
- Redacted values render as a muted `[redacted]` chip.

Expanded row:

- Show full redacted JSON in a light bordered detail panel.
- Do not use the dark raw log viewer for Audit Logs.

### 9.4 Error Display

Default cell:

- Show `errorCode` badge if present.
- Show sanitized/truncated `errorMessage`.

Expanded row:

- Show sanitized full API response field, still capped.
- Never show raw secret-bearing command output.

## 10. Job Logs Relationship

Job Logs answer:

- What did the system do internally?
- Which event happened in a job stream?

Audit Logs answer:

- What did the operator/system request?
- What result was recorded for the request?

Rules:

- Do not merge Job Logs and Audit Logs into one timeline in v1.
- A failed upload job must be traceable in both tabs with the same `jobId`.
- A runtime operation should be traceable by `targetType=local_supabase` and `targetId=Extrusion_data`; if an `operationId` exists, put it in `targetId` or params consistently.
- Job Logs may link to related Audit Logs by `jobId`.
- Audit Logs may link to Job Logs by `jobId`.

## 11. Dashboard Integration

Dashboard must continue to show a compact audit summary, but the source should shift from mock data to API-backed data when Audit API is implemented.

Dashboard latest failure/warning rules:

1. Upload job events are the strongest source for active upload diagnostics.
2. Runtime events are the strongest source for local Supabase operation diagnostics.
3. Audit rows provide operator-action evidence and blocked/failure summaries.

Dashboard links:

- Latest failed upload -> `Logs` Job Logs tab filtered by `jobId`.
- Upload audit failure/blocked -> `Logs` Audit Logs tab filtered by `jobId` or `action`.
- Runtime start/stop failure -> `Logs` Audit Logs tab filtered by `action=runtime.start|runtime.stop`.
- Audit summary row -> `Logs` Audit Logs tab, preserving the row filter if available.

No new destructive Dashboard controls are added by this feature.

## 12. Empty, Loading, Error States

### Empty

Message:

```text
No audit logs match the current filters.
현재 필터와 일치하는 감사 로그가 없습니다.
```

Show `Clear filters` if any filter is active.

### Loading

Use table skeleton rows.

Message:

```text
Loading audit logs...
감사 로그를 불러오는 중...
```

### API Error

Show an inline banner with `role="alert"` above the table. Do not rely on toast-only error reporting.

Message:

```text
Audit logs could not be loaded.
감사 로그를 불러오지 못했습니다.
```

If API fails, keep the last successful table visible when possible and mark it stale.

## 13. Korean/English i18n

Add i18n keys for:

```text
logs.tabs.jobLogs
logs.tabs.auditLogs
logs.audit.title
logs.audit.subtitle
logs.audit.filters.dateRange
logs.audit.filters.result
logs.audit.filters.action
logs.audit.filters.jobId
logs.audit.filters.target
logs.audit.filters.search
logs.audit.filters.failuresOnly
logs.audit.filters.clear
logs.audit.columns.time
logs.audit.columns.result
logs.audit.columns.action
logs.audit.columns.target
logs.audit.columns.actor
logs.audit.columns.jobId
logs.audit.columns.params
logs.audit.columns.error
logs.audit.empty
logs.audit.loading
logs.audit.error
logs.audit.pagination.previous
logs.audit.pagination.next
logs.audit.pagination.limit
logs.audit.results.success
logs.audit.results.failure
logs.audit.results.blocked
logs.audit.results.cancelled
```

Korean copy must stay short enough for table headers and buttons:

```text
Audit Logs -> 감사 로그
Job Logs -> 작업 로그
Failures only -> 실패만
Clear filters -> 초기화
Params -> 파라미터
Error -> 오류
Job ID -> 작업 ID
```

Before implementation, validate UTF-8 JSON parsing and Korean rendering. PowerShell console mojibake is not sufficient evidence of broken app rendering.

## 14. Tests

### 14.1 Backend Unit/Contract Tests

Add:

```text
tests/backend/test_audit_api_contract.py
tests/backend/test_audit_repository.py
tests/backend/test_audit_redaction.py
```

Required tests:

- `GET /api/audit` returns newest rows first by default.
- Pagination returns `limit`, `offset`, `totalItems`, `hasNext`, `hasPrevious`.
- Filter by `result`.
- Filter by `action`.
- Filter by `targetType` and `targetId`.
- Filter by `jobId`.
- Filter by date range.
- Text search does not search raw JSON params.
- Invalid result returns 422.
- Invalid sort returns 422.
- Limit above max is rejected or clamped by documented behavior.
- `params_json_redacted` is decoded to `params`.
- Invalid params JSON returns `{}` instead of crashing.
- API response does not include raw `params_json_redacted`.
- API response sanitizes `errorMessage`.
- Redaction masks secret/token/key/password/authorization/JWT/credential URL values recursively.
- Append-only triggers reject update/delete if implemented.
- Existing upload/runtime audit rows remain readable.

### 14.2 Backend Regression Tests

Add or keep audit assertions for:

- Upload start success.
- Upload start blocked because preview missing or no targets.
- Retry blocked because no failed files.
- Pause/resume/cancel blocked by invalid status.
- Runtime start blocked by active upload.
- Runtime start blocked by active preview.
- Runtime start/stop success/failure/blocked.
- Passive runtime status polling success does not create audit rows.

### 14.3 Frontend Tests/Checks

If a test framework exists, add component tests for:

- Audit table renders result badges.
- Filters update query parameters sent to API.
- Empty/loading/error states render.
- Params render redacted chips.
- Long Korean labels do not overflow buttons.

If no frontend test runner exists yet, rely on:

- `npm run typecheck`
- `npm run build`
- Browser QA at `1440x900`, `1366x768`, `1024x768`, `720x900`
- Korean/English language switch

### 14.4 Browser QA

Required manual/browser QA:

- Logs page opens from sidebar.
- Tabs switch between Job Logs and Audit Logs.
- Audit Logs table loads sample/real audit rows.
- `failure`, `blocked`, `cancelled`, `success` all have distinct badges.
- Date/action/result/job filters work.
- Clear filters works.
- Params and errors are redacted.
- Horizontal overflow works at 720px width.
- Dashboard audit summary links into Audit Logs.
- Upload Preview/Upload Job/Runtime existing screens still work.

## 15. Failure Modes

| Failure | API behavior | UI behavior | Audit behavior |
| --- | --- | --- | --- |
| State DB missing | bootstrap read schema; return empty if no rows | empty state | no synthetic audit row |
| State DB locked | 503 or 500 with safe message | error banner, keep stale rows | no new audit row unless manual refresh failure policy is added |
| Invalid query filter | 422 | validation message | no audit row |
| Invalid params JSON in row | return `{}` and safe warning field if needed | show empty params | do not mutate row |
| Secret in params | return redacted value only | `[redacted]` chip | storage/query redaction test |
| Secret in error message | sanitize before response | sanitized message | future writer should sanitize before insert |
| Too many rows | pagination only | page controls | no export in v1 |
| Unknown action | return raw action | muted raw id label | no failure |
| Missing job for jobId link | link disabled or opens filtered empty state | empty state | no mutation |
| Backend restart | existing rows remain queryable | table reloads | append-only preserved |

## 16. Implementation Order

1. Add `backend/app/schemas/audit.py`.
2. Add `backend/app/db/audit_repository.py` with bootstrap, indexes, query, count, decode, redaction helpers.
3. Add `backend/app/api/audit.py` with `GET /api/audit`.
4. Register audit router in `backend/app/main.py`.
5. Add backend audit API/repository/redaction tests.
6. Add frontend `frontend/src/api/audit.ts`.
7. Replace Logs placeholder with `LogsPage`.
8. Implement `Job Logs` tab shell first without expanding scope beyond existing job events.
9. Implement `Audit Logs` tab table, filters, pagination, and states.
10. Add i18n keys in `en.json` and `ko.json`.
11. Connect Dashboard audit summary links to Logs/Audit filters.
12. Run backend tests, frontend typecheck/build, and browser QA.
13. Update README and roadmap to mark Audit Logs UI/API implemented.

Do not implement export, delete, archive, arbitrary query, retention, cloud audit sync, or multi-user actor identity in this phase.

## 17. Acceptance Criteria

- `GET /api/audit` returns paginated, filtered, redacted audit rows.
- API does not expose raw `params_json_redacted`.
- API does not expose known secret/token/key/credential values.
- Existing upload/runtime audit rows are visible without migration.
- Logs page has separate `Job Logs` and `Audit Logs` tabs.
- Audit Logs is a light operational table with filters and pagination.
- Result states are icon + label + semantic color.
- Failed/blocked audit rows are visually prominent.
- Empty/loading/error states are explicit.
- Korean/English UI keys exist for all new strings.
- Audit delete/update UI does not exist.
- Local Supabase command policy is untouched.
- Upload Preview, Upload Job, and Runtime behavior are not changed except for reading their existing audit rows.

## 18. Explicit Out Of Scope

- Audit row deletion, editing, archival, cleanup, retention policy UI.
- Arbitrary SQL query UI.
- Raw command output export.
- Audit CSV/JSON export.
- Cloud Supabase migration.
- Multi-user LAN identity.
- Data Mgmt archive/delete.
- Supabase delete UI.
- Cycle Ops.
- Training Dataset Builder.
- Grafana iframe or dashboard embedding.
- Changes to local Supabase start/stop command allowlist.
- Changes to upload transform, upload execution, retry, SSE, or preview reconciliation behavior.
