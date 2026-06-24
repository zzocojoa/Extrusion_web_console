# Upload Preview Reconciliation Plan

Status: implemented for v1 scaffold on branch `codex/upload-preview-reconciliation`

Branch: `codex/upload-preview-reconciliation`

Scope: v1 Core Ops Upload Preview only

This document finalizes the engineering plan for Upload Preview reconciliation. It follows `docs/00_product_scope.md`, `docs/02_engineering_plan.md`, `docs/03_ui_ux_plan.md`, and `docs/04_design_system.md`.

## Implementation Result

Implemented on branch `codex/upload-preview-reconciliation`:

- Backend Preview API:
  - `POST /api/upload/preview`
  - `GET /api/upload/preview/latest`
  - `GET /api/upload/preview/{previewRunId}`
  - `POST /api/upload/preview/{previewRunId}/cancel`
- SQLite `preview_runs` and `preview_items` persistence in the new web state store.
- Local CSV candidate scanning from configured backend source folders.
- Row-streamed `(timestamp, device_id)` key extraction without loading full transformed CSV data into memory.
- `sampleRows` schema preflight, `forceFullScan` override, and row-level cancel/deadline checks during key extraction.
- Chunked exact-key DB matching against Supabase/Postgres using `chunkRows`.
- Direct local Supabase exact reconciliation through `EWC_SUPABASE_DB_URL` and `public.all_metrics`.
- DB reconciliation time bounds through Postgres `connect_timeout`, per-batch `statement_timeout`, and cancel/deadline checks between DB batches.
- DB unreachable handling:
  - run status `partial_failed`
  - DB status `unreachable`
  - DB-dependent candidate rows `risky/db_unreachable`
  - upload row estimate held at `0` for unreachable DB rows
- Preview run polling and latest-run retrieval.
- Upload Preview frontend UI:
  - Preview and Job tabs
  - status summary
  - status/reason table
  - filters/search/sort/pagination wiring
  - mock data covering `target`, `already_in_db`, `partial_overlap`, `risky`, and `excluded`
  - mock DB unreachable and cancel states
  - Korean/English i18n entries
- `upload.preview` audit writer coverage for preview success, DB unreachable failure, missing source failure, malformed JSON and validation failures, and active preview conflict blocked paths.
- `/api/audit?action=upload.preview` queryability through the Audit Logs API.
- Safe preview audit params using `previewRunId`, counts, `dbStatus`, `reasonCode`, and `requestedFilters`; raw file paths, filenames, DB URLs, tokens, anon keys, service role values, secrets, and malformed raw request bodies are not stored in audit params.
- Start Upload remains visible but disabled because real upload execution is not implemented in this phase.

Still not implemented:

- Real upload job execution.
- Retry Failed execution.
- SSE upload progress/log streaming.
- Local Supabase start/stop/status controls.
- Legacy `uploader_state.db` import.
- Data Mgmt, Cycle Ops, Training Dataset Builder, cloud migration, multi-user LAN access, or Grafana iframe.

## Verification Result

Verified after implementation and QA:

- Backend tests: `.\.venv\Scripts\python -m pytest tests\backend`
- Frontend typecheck: `npm run typecheck`
- Frontend build: `npm run build`
- Browser QA for Dashboard regression:
  - `http://127.0.0.1:5173/?state=ready`
  - `http://127.0.0.1:5173/?state=attention`
  - `http://127.0.0.1:5173/?state=blocked`
  - `http://127.0.0.1:5173/?state=running`
- Browser QA for Upload Preview:
  - default mock preview table
  - DB unreachable mock state
  - cancelled mock state
  - Korean/English language switch
  - responsive widths `1440x900`, `1366x768`, `1024x768`, and `720x900`
- PR #9 API-centered audit QA:
  - targeted preview/audit backend tests
  - full backend tests
  - frontend typecheck/build
  - `git diff --check`
  - direct API smoke for `POST /api/upload/preview`, `GET /api/upload/preview/{id}`, `GET /api/upload/preview/latest`, and `/api/audit?action=upload.preview`
  - Vite/backend HTTP smoke for the running shell and API proxy

No browser console errors, page errors, or unexpected failed requests were observed during the QA pass.

## Remaining Risks

- Real reachable local Supabase reconciliation still needs operator-environment testing against representative `all_metrics` data.
- Legacy CSV fixture coverage should be expanded before upload execution work, especially for CP949 files, locked files, unstable files, empty files, and mixed date/source folders.
- `db_query_failed` and other partial batch-failure paths need more focused tests beyond the DB unreachable path.
- The currently wired service streams CSV rows and chunks DB matching, but it does not use the planned temporary `preview_key_stage` table. Very large CSV behavior is bounded by timeouts and key deduplication, not by temp-table staging yet.
- Cancel and deadline checks are wired before scanning, during CSV row extraction, and between DB batches. A single in-flight DB statement is bounded by Postgres `statement_timeout`, but true mid-statement cancellation still depends on the DB driver/network path.
- Timeout behavior is bounded and persisted, but it should still be rechecked with larger real CSV files on the operator PC.
- Preview retry creates new run state, but the full operator retry workflow should be revisited when real upload jobs and audit logs exist.
- Browser screenshot QA for PR #9 was not completed because `node_repl` failed with a kernel asset path error; HTTP smoke covered the running Vite shell and backend proxy instead.
- Large real CSV preview soak remains a separate operator-environment validation item.

## Goals

Upload Preview must let an operator compare local CSV candidates with rows already present in local Supabase before any upload job starts.

The preview is a safety and visibility feature, not a final duplicate prevention mechanism. Final duplicate prevention remains the Supabase/Postgres unique constraint and Edge Function upsert on `all_metrics(timestamp, device_id)`.

## Non-Goals

- Do not implement the real upload job in this phase.
- Do not implement upload SSE/progress streaming in this phase.
- Do not implement Supabase start/stop in this phase.
- Do not import or migrate legacy `uploader_state.db`.
- Do not use legacy `processed_files.log` as the source of truth.
- Do not implement Data Mgmt, Cycle Ops, Training Dataset Builder, cloud migration, or multi-user LAN access.
- Do not embed Grafana.

## Existing Behavior To Preserve

Reference project: `C:\Users\user\Documents\GitHub\Extrusion_data`.

Important reusable patterns:

- `core/files.py`: candidate scanning, KST date parsing, file stability checks, lock checks, sample CSV preflight, UTF-8/CP949 fallback.
- `core/transform.py`: canonical row generation for PLC, integrated PLC, and temperature CSVs. The output includes `timestamp` and `device_id`.
- `core/upload.py`: chunked upload patterns, progress accounting, and the existing Smart Sync regression tests. The preview plan must not reuse the latest-timestamp-only Smart Sync decision path.
- `core/config.py`: config loading, edge URL derivation, and validation patterns.
- `core/state.py` / `core/state_db.py`: SQLite WAL/state-store patterns and upload run/file-state concepts. The new web state store starts fresh.
- `supabase/functions/upload-metrics/index.ts`: upsert safety with `onConflict: "timestamp,device_id"`.
- `supabase/migrations/20260421000001_restore_all_metrics_device_scope.sql`: `all_metrics_timestamp_device_id_key UNIQUE ("timestamp", device_id)`.

## Core Decisions

1. Preview runs are backend-managed persisted tasks, not upload jobs.
   `POST /api/upload/preview` creates a `preview_run`, executes it in the backend `ThreadPoolExecutor`, and returns `202 Accepted` with `previewRunId`. The frontend polls `GET /api/upload/preview/{id}`.

2. Preview uses no SSE in this phase.
   Polling is sufficient because the operator needs run status and table results, not row-by-row upload progress. Upload job SSE remains a later feature.

3. Reconciliation uses exact `(timestamp, device_id)` keys.
   No preview status may be inferred from latest timestamp alone.

4. Full key extraction is required for `target`, `already_in_db`, and `partial_overlap`.
   If the backend cannot complete key extraction or DB matching within the configured budget, the item becomes `risky`, not guessed.

5. Supabase matching uses direct local Postgres read access.
   The backend should use a local Supabase DB connection through `psycopg` and batch `VALUES` joins against `public.all_metrics`. This is more reliable for exact composite-key matching than large PostgREST `or` filters.

6. The new web state store starts empty.
   Legacy `uploader_state.db` and legacy processed markers are not imported. New state may later mark files completed by this web app, but DB reconciliation is still the preview authority.

7. DB unreachable does not silently pass.
   The run completes with `partial_failed`, and DB-dependent candidate files become `risky` with reason `db_unreachable`. Start Upload must remain blocked for those rows.

## Status Model

Preview item status values:

| Status | Meaning | Upload Eligibility |
| --- | --- | --- |
| `target` | Full key extraction succeeded, DB reachable, no local keys exist in DB. | Eligible later when upload job exists. |
| `already_in_db` | Full key extraction succeeded and every local key exists in DB. | Not eligible. |
| `partial_overlap` | Full key extraction succeeded and some, but not all, local keys exist in DB. | Not eligible by default in v1. |
| `risky` | Safety cannot be determined: DB unreachable, transform failed, schema uncertain, timeout, key extraction incomplete. | Never eligible by default. |
| `excluded` | Deterministic local preflight excludes file: unsupported, out of range, locked, unstable, empty, not CSV, outside configured source. | Not eligible. |

Preview run status values:

| Status | Meaning |
| --- | --- |
| `queued` | Run has been accepted but not started. |
| `running` | Scanner/reconciler is active. |
| `succeeded` | Run finished without item-level system errors. Items may still be `risky` due local data issues. |
| `partial_failed` | Run produced usable results but a subsystem failed, usually Supabase DB access. |
| `failed` | Run-level failure prevented usable results. |
| `cancelling` | Cancel was requested and the worker is draining. |
| `cancelled` | Run stopped before completion by operator/API request. |
| `timed_out` | Run exceeded the configured wall-clock budget. |

Classification matrix:

```text
-------------------------------+--------------------+
| Condition                     | Preview item state |
+-------------------------------+--------------------+
| unsupported path/kind         | excluded           |
| file outside requested range  | excluded           |
| not stable enough             | excluded           |
| locked by writer              | excluded           |
| empty/read-empty CSV          | excluded           |
| sample schema mismatch        | risky              |
| transform cannot emit keys    | risky              |
| key extraction timeout        | risky              |
| Supabase DB unreachable       | risky              |
| local_key_count = 0           | excluded           |
| db_match_count = 0            | target             |
| db_match_count = local keys   | already_in_db      |
| 0 < db_match_count < keys     | partial_overlap    |
```

## Backend API

### `POST /api/upload/preview`

Creates a preview run.

Request body:

```json
{
  "rangeMode": "today",
  "startDate": null,
  "endDate": null,
  "sources": ["plc"],
  "options": {
    "stableLagMinutes": 3,
    "sampleRows": 200,
    "chunkRows": 20000,
    "maxFiles": 500,
    "maxRunSeconds": 120,
    "maxFileSeconds": 30,
    "forceFullScan": false
  },
  "retryOfRunId": null
}
```

Response `202`:

```json
{
  "previewRunId": "prv_20260601_000001",
  "status": "queued",
  "pollUrl": "/api/upload/preview/prv_20260601_000001"
}
```

Validation rules:

- `rangeMode`: `today | yesterday | last_2_days | last_7_days | last_30_days | folder_all | custom`.
- `custom` requires `startDate` and `endDate`.
- `folder_all` requires no dates and expands only the Preview candidate scan.
- `sources` initially supports `plc`; `temperature` is allowed only when configured and implemented.
- Paths are resolved from backend config. The request must not accept arbitrary filesystem paths.
- `maxRunSeconds`, `maxFileSeconds`, `maxFiles`, and `chunkRows` are clamped to backend limits.

### `GET /api/upload/preview/{previewRunId}`

Returns run summary and items.

Query parameters:

```text
status=target|already_in_db|partial_overlap|risky|excluded
q=<filename-or-path-search>
sort=status|fileDate|filename|uploadRows|modifiedAt
order=asc|desc
limit=100
offset=0
```

Response:

```json
{
  "run": {
    "previewRunId": "prv_20260601_000001",
    "status": "succeeded",
    "requestedAt": "2026-06-01T09:00:00+09:00",
    "startedAt": "2026-06-01T09:00:01+09:00",
    "finishedAt": "2026-06-01T09:00:14+09:00",
    "dbStatus": "reachable",
    "summary": {
      "total": 12,
      "target": 5,
      "alreadyInDb": 4,
      "partialOverlap": 1,
      "risky": 1,
      "excluded": 1,
      "uploadRows": 24012,
      "dbMatchedRows": 18003
    },
    "warnings": []
  },
  "items": [
    {
      "previewItemId": 101,
      "status": "partial_overlap",
      "reasonCode": "db_partial_match",
      "reasonText": "일부 행이 이미 DB에 있습니다.",
      "kind": "plc",
      "folderLabel": "PLC",
      "filename": "integrated_plc_sample_A.csv",
      "path": "configured_plc_source/integrated_plc_sample_A.csv",
      "fileDate": "2026-06-01",
      "sizeBytes": 8821234,
      "modifiedAt": "2026-06-01T09:02:00+09:00",
      "scanMode": "full",
      "rowCount": 20000,
      "localKeyCount": 20000,
      "dbMatchCount": 12000,
      "uploadRowEstimate": 8000,
      "firstTimestamp": "2026-06-01T08:59:00.000000+09:00",
      "lastTimestamp": "2026-06-01T09:30:00.000000+09:00",
      "deviceIds": ["extruder_integrated"],
      "issues": []
    }
  ],
  "page": {
    "limit": 100,
    "offset": 0,
    "totalItems": 12
  }
}
```

### `GET /api/upload/preview/latest`

Returns the newest preview run, optionally filtered by `completedOnly=true`.

Use case: Upload page reload and Dashboard upload summary.

### `POST /api/upload/preview/{previewRunId}/cancel`

Requests cancellation. The worker checks the cancellation flag between files and between CSV chunks.

Response:

```json
{
  "previewRunId": "prv_20260601_000001",
  "status": "cancelling"
}
```

### `DELETE /api/upload/preview/{previewRunId}`

Not in v1. Preview history retention is backend-managed.

## DTOs

Backend Pydantic models:

```python
class PreviewRangeMode(str, Enum):
    today = "today"
    yesterday = "yesterday"
    last_2_days = "last_2_days"
    last_7_days = "last_7_days"
    last_30_days = "last_30_days"
    folder_all = "folder_all"
    custom = "custom"

class PreviewSource(str, Enum):
    plc = "plc"
    temperature = "temperature"

class PreviewOptions(BaseModel):
    stable_lag_minutes: int = Field(default=3, ge=0, le=60)
    sample_rows: int = Field(default=200, ge=20, le=2000)
    chunk_rows: int = Field(default=20000, ge=1000, le=100000)
    max_files: int = Field(default=500, ge=1, le=5000)
    max_run_seconds: int = Field(default=120, ge=10, le=900)
    max_file_seconds: int = Field(default=30, ge=5, le=300)
    force_full_scan: bool = False

class PreviewCreateRequest(BaseModel):
    range_mode: PreviewRangeMode
    start_date: date | None = None
    end_date: date | None = None
    sources: list[PreviewSource] = [PreviewSource.plc]
    options: PreviewOptions = PreviewOptions()
    retry_of_run_id: str | None = None

class PreviewItemStatus(str, Enum):
    target = "target"
    already_in_db = "already_in_db"
    partial_overlap = "partial_overlap"
    risky = "risky"
    excluded = "excluded"

class PreviewRunStatus(str, Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    partial_failed = "partial_failed"
    failed = "failed"
    cancelling = "cancelling"
    cancelled = "cancelled"
    timed_out = "timed_out"
```

Reason codes:

```text
unsupported_kind
unsupported_extension
outside_date_range
file_unstable
file_locked
file_missing
read_error
empty_file
schema_mismatch
transform_error
timestamp_missing
device_id_missing
no_valid_keys
db_unreachable
db_query_failed
db_no_match
db_full_match
db_partial_match
timeout
cancelled
new_state_completed
```

## SQLite Schema

The tables live in the new web app SQLite database, not the legacy `uploader_state.db`.

```sql
CREATE TABLE IF NOT EXISTS preview_runs (
  preview_run_id TEXT PRIMARY KEY,
  status TEXT NOT NULL CHECK(status IN (
    'queued','running','succeeded','partial_failed','failed',
    'cancelling','cancelled','timed_out'
  )),
  requested_at TEXT NOT NULL,
  started_at TEXT,
  finished_at TEXT,
  actor TEXT NOT NULL DEFAULT 'local_operator',
  range_mode TEXT NOT NULL,
  start_date TEXT,
  end_date TEXT,
  sources_json TEXT NOT NULL,
  options_json TEXT NOT NULL,
  config_snapshot_json TEXT NOT NULL,
  retry_of_run_id TEXT,
  cancel_requested INTEGER NOT NULL DEFAULT 0,
  db_status TEXT NOT NULL DEFAULT 'not_checked'
    CHECK(db_status IN ('not_checked','reachable','unreachable','query_failed')),
  total_files INTEGER NOT NULL DEFAULT 0,
  target_count INTEGER NOT NULL DEFAULT 0,
  already_in_db_count INTEGER NOT NULL DEFAULT 0,
  partial_overlap_count INTEGER NOT NULL DEFAULT 0,
  risky_count INTEGER NOT NULL DEFAULT 0,
  excluded_count INTEGER NOT NULL DEFAULT 0,
  upload_row_estimate INTEGER NOT NULL DEFAULT 0,
  db_match_count INTEGER NOT NULL DEFAULT 0,
  warning_count INTEGER NOT NULL DEFAULT 0,
  error_code TEXT,
  error_message TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS preview_items (
  preview_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
  preview_run_id TEXT NOT NULL REFERENCES preview_runs(preview_run_id) ON DELETE CASCADE,
  file_key TEXT NOT NULL,
  folder_label TEXT NOT NULL,
  folder_path TEXT NOT NULL,
  filename TEXT NOT NULL,
  path TEXT NOT NULL,
  kind TEXT NOT NULL,
  file_date TEXT,
  size_bytes INTEGER,
  mtime_ns INTEGER,
  modified_at TEXT,
  file_signature TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN (
    'target','already_in_db','partial_overlap','risky','excluded'
  )),
  reason_code TEXT NOT NULL,
  reason_text TEXT NOT NULL,
  scan_mode TEXT NOT NULL CHECK(scan_mode IN ('metadata','sample','full','incomplete')),
  sample_row_count INTEGER,
  row_count INTEGER,
  local_key_count INTEGER,
  db_match_count INTEGER,
  upload_row_estimate INTEGER,
  first_timestamp TEXT,
  last_timestamp TEXT,
  device_ids_json TEXT NOT NULL DEFAULT '[]',
  issues_json TEXT NOT NULL DEFAULT '[]',
  error_code TEXT,
  error_message TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(preview_run_id, file_key)
);

CREATE INDEX IF NOT EXISTS idx_preview_runs_status_created
  ON preview_runs(status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_preview_items_run_status
  ON preview_items(preview_run_id, status);

CREATE INDEX IF NOT EXISTS idx_preview_items_run_filename
  ON preview_items(preview_run_id, filename);
```

Temporary key staging:

```sql
CREATE TEMP TABLE preview_key_stage (
  preview_item_id INTEGER NOT NULL,
  timestamp TEXT NOT NULL,
  device_id TEXT NOT NULL,
  PRIMARY KEY (preview_item_id, timestamp, device_id)
);
```

`preview_key_stage` is not retained after a run. Persisting every key would grow the state DB quickly and is not needed for the v1 UI.

Retention:

- Keep the latest 20 preview runs by default.
- Always keep the latest failed/partial_failed preview for diagnosis.
- Cleanup happens on preview run start or app startup.

## File Candidate Scanning

The scanner is a backend service, not a frontend feature.

Service boundary:

```text
PreviewService
  -> CandidateScanner
  -> CsvKeyExtractor
  -> SupabaseReconciliationRepository
  -> PreviewRepository
```

Candidate scanner responsibilities:

1. Resolve configured source folders from backend config.
2. Reject arbitrary user-supplied paths.
3. Enumerate `.csv` files using `os.scandir` / `pathlib`.
4. Classify source kind from configured folder, not filename alone.
5. Parse KST file date:
   - PLC legacy: filename starts with `YYMMDD`.
   - Integrated PLC: configured integrated PLC CSV naming pattern.
   - Temperature: date-bearing filename only when temperature source is enabled.
6. Apply requested date range.
7. Check file stability by `mtime <= now - stableLagMinutes`.
8. Check file lock on Windows.
9. Read sample rows with UTF-8 BOM fallback to CP949.
10. Persist one `preview_items` row for every candidate, including excluded/risky reasons.

Date range decision:

- `today`: KST today only.
- `yesterday`: KST yesterday only.
- `last_2_days`: KST yesterday through today inclusive.
- `last_7_days`: KST current day inclusive, from current day minus 6 through current day.
- `last_30_days`: KST current day inclusive, from current day minus 29 through current day.
- `folder_all`: configured source folder top-level CSV candidates after file-date metadata parses; no date-window exclusion.
- `custom`: inclusive KST start/end dates.

This intentionally avoids the legacy ambiguity where a `today` mode could include all dates up to today.
`folder_all` is a Preview-only candidate expansion. It is non-recursive and still uses configured source folders only, stable lag, `maxFiles`, file lock checks, timeout budgets, and file-date metadata parsing. It does not approve Start Upload, Retry Failed, Delete, or any operational DB mutation.

## CSV Sample And Full Scan Rules

Preview has two phases per file.

Phase 1: metadata/sample preflight

- Read up to `sampleRows` rows.
- Validate non-empty CSV.
- Validate that the schema can be transformed into canonical rows.
- Detect `timestamp` and `device_id` availability after transform.
- If this phase fails deterministically due empty/unsupported/out-of-range/locked/unstable, status is `excluded`.
- If schema or transform safety is uncertain, status is `risky`.

Phase 2: full key extraction

- Required for `target`, `already_in_db`, and `partial_overlap`.
- Read transformed rows in chunks.
- Extract only `(timestamp, device_id)` plus row counts.
- Deduplicate keys per file.
- Track `firstTimestamp`, `lastTimestamp`, and device ids.
- Never keep the full transformed dataframe in memory.
- If extraction exceeds `maxFileSeconds` or the run exceeds `maxRunSeconds`, stop and mark remaining/incomplete items `risky` or run `timed_out`.

Large CSV decision:

- Full scan is still attempted for large files because exact reconciliation is the product requirement.
- Large-file safety comes from chunking, deduplication, timeouts, and temporary key staging.
- The backend must not downgrade to latest-timestamp inference.

## Supabase Exact Reconciliation

Primary implementation: direct local Postgres connection with `psycopg`.

Configuration:

- Add `SUPABASE_DB_URL` or equivalent local DB connection setting to backend config.
- In local Supabase this should point at the local Postgres instance only.
- Use a read-only transaction for preview queries.
- Never write to Supabase during preview.

Batch query shape:

```sql
WITH candidate_keys(timestamp, device_id) AS (
  VALUES
    ($1::timestamptz, $2::text),
    ($3::timestamptz, $4::text)
)
SELECT c.timestamp::text, c.device_id
FROM candidate_keys c
JOIN public.all_metrics m
  ON m."timestamp" = c.timestamp
 AND m.device_id = c.device_id;
```

Batching rules:

- Batch by distinct local keys, not raw rows.
- Default batch size: 1000 keys.
- Clamp batch size if query time exceeds target latency.
- Compare timestamps using the same ISO/KST canonical representation emitted by `core/transform.py`. Normalize to timestamptz for SQL and return text for comparison.
- If duplicate rows exist within the same CSV, count rows and distinct keys separately. Status decisions use distinct keys; UI can show duplicate warning later if needed.

Fallback:

- PostgREST exact matching is allowed only as a development fallback and must keep strict URL-length and batch-size limits.
- The fallback must still query exact `(timestamp, device_id)` pairs, not latest timestamps.

## DB Unreachable Handling

If local Supabase DB cannot be reached:

- `preview_runs.status = 'partial_failed'`.
- `preview_runs.db_status = 'unreachable'`.
- Files that passed local preflight become `risky` with `reason_code = 'db_unreachable'`.
- Local excluded items remain `excluded`.
- The UI shows a top warning and disables upload start.
- The failure is stored in `preview_runs.error_code/error_message`.
- The failure is also written to audit log as `upload.preview` result `failure`.

No path may silently mark DB-dependent files as `target` when DB is unreachable.

## Timeout, Cancel, Retry

Timeout:

- Run timeout default: 120 seconds.
- File timeout default: 30 seconds.
- Timeout converts the run to `timed_out` if the run cannot finish.
- Completed items keep their statuses.
- Incomplete items become `risky` with `reason_code = 'timeout'`.

Cancel:

- `POST /api/upload/preview/{id}/cancel` sets `cancel_requested = 1`.
- Worker checks the flag before scanning, during CSV row extraction, and between DB batches.
- Run becomes `cancelling`, then `cancelled`.
- Already persisted items remain visible.
- Not-yet-scanned items are not inserted unless discovered; discovered-but-incomplete items become `risky` with `reason_code = 'cancelled'`.

Retry:

- Retry creates a new preview run with `retryOfRunId`.
- It does not mutate the old run.
- The UI should label the new run as a fresh preview.

Concurrency:

- Only one preview run may be `queued/running/cancelling` at a time.
- A new preview request while another is active returns `409` with the active `previewRunId`.
- This avoids multiple heavy CSV scans on an operator PC.

## Frontend Upload Preview UI

The Upload page keeps the fixed v1 structure:

```text
Upload
  [Preview] [Job]
```

Preview tab layout:

```text
+--------------------------------------------------------------+
| Upload Preview                                                |
| Range controls | Source summary | Run Preview | Start Upload  |
+--------------------------------------------------------------+
| Run status strip: status, DB status, last run time, duration  |
+--------------------------------------------------------------+
| Targets | Already in DB | Partial | Risky | Excluded | Total  |
+--------------------------------------------------------------+
| Filter/search/sort controls                                  |
+--------------------------------------------------------------+
| Preview table                                                 |
+--------------------------------------------------------------+
```

Table columns:

| Column | Content |
| --- | --- |
| Status | badge with icon, label, and color token |
| Filename | sticky data column, filename primary, folder label secondary |
| Kind | PLC / Temperature |
| File Date | KST date |
| Rows | parsed row count if known |
| DB Match | exact key match count |
| Upload Rows | estimated rows not found in DB |
| Reason | reason text; fixed minimum width for Korean |
| Modified | KST mtime |
| Path | truncated path with copy button later |

Start Upload behavior in this phase:

- The button may be present to preserve layout but must remain disabled with text indicating upload job is not implemented yet.
- When upload job is implemented later, only `target` rows are eligible by default.
- `partial_overlap` and `risky` are not included by default.

Status visual rules:

- `target`: ready/success style, not overly celebratory.
- `already_in_db`: muted/neutral.
- `partial_overlap`: attention warning style.
- `risky`: risk/failed warning style depending severity.
- `excluded`: muted badge.
- Status must use icon + label + color, not color alone.
- Long Korean reason text must wrap inside the table cell without row overlap.

Loading/empty/error states:

- No run yet: show an operator-facing empty state with Run Preview as the primary action.
- Running: show run status strip and table rows as they become available by polling.
- DB unreachable: show top warning and `risky` rows, not an empty table.
- No candidates: show completed run with zero counts and explain date/source scope.

## Data Flow

```text
Operator clicks Run Preview
  -> POST /api/upload/preview
  -> preview_runs row queued
  -> ThreadPoolExecutor starts PreviewService
  -> preview_runs row running
  -> CandidateScanner enumerates configured CSV folders
  -> preview_items inserted for excluded/local-risk items
  -> CsvKeyExtractor chunk-transforms candidate CSVs
  -> temporary preview_key_stage stores exact keys
  -> SupabaseReconciliationRepository queries all_metrics exact matches
  -> PreviewService classifies target/already/partial/risky/excluded
  -> preview_items and preview_runs summaries updated
  -> frontend polls GET /api/upload/preview/{id}
  -> Upload Preview table renders status/reason/counts
```

## Error Handling

No silent failures:

- Every run-level failure is persisted in `preview_runs.error_code/error_message`.
- Every file-level failure is persisted in `preview_items.error_code/error_message` and `issues_json`.
- UI shows run-level failures in the status strip.
- UI shows file-level failures in the table reason column.
- Backend logs include run id, file key, reason code, and exception class.
- Preview success, DB unreachable, missing source, malformed JSON, and validation failures are audit logged as `upload.preview` success or failure rows. Active preview conflicts are audit logged as `upload.preview` blocked rows.
- `upload.preview` audit params store safe summary fields such as `previewRunId`, counts, `dbStatus`, `reasonCode`, and `requestedFilters`; raw file paths, filenames, DB URLs, tokens, anon keys, service role values, secrets, and malformed raw request bodies are not stored in audit params.

Failure modes:

| Failure | Backend result | UI result |
| --- | --- | --- |
| Config missing source folder | run `failed` if no source usable; item `excluded` if per-source issue | top error |
| Source folder missing | items `excluded` or run `failed` if all missing | warning/counts visible |
| File locked | item `excluded/file_locked` | muted excluded row |
| File modified too recently | item `excluded/file_unstable` | muted excluded row |
| CSV read error | item `risky/read_error` | warning row |
| Schema mismatch | item `risky/schema_mismatch` | warning row |
| Transform emits no valid keys | item `excluded/no_valid_keys` or `risky/transform_error` | reason row |
| DB unreachable | run `partial_failed`, candidates `risky/db_unreachable` | blocked warning |
| DB query batch fails | run `partial_failed`, affected items `risky/db_query_failed` | warning rows |
| Timeout | run `timed_out`, incomplete items `risky/timeout` | timeout banner |
| Cancel | run `cancelled` | cancelled banner |
| App restart mid-preview | startup marks active run `failed/interrupted` | latest preview shows interrupted |

## Security And Localhost Constraints

- Preview APIs are localhost-only through the existing backend bind/CORS rules.
- Request bodies cannot include arbitrary file paths.
- Only configured source directories are scanned.
- Paths returned to UI are local operator-PC paths and must not be sent to remote services.
- Supabase DB connection is local-only.
- Secrets in config snapshots must be redacted.
- Preview performs read-only Supabase queries.

## Test Plan

Backend unit tests:

- DTO validation for range modes, options clamp, invalid custom date range.
- Candidate date parsing for legacy PLC and integrated PLC filenames.
- Date window behavior for today/yesterday/last_2_days/custom.
- File stability and lock-check classification.
- UTF-8 BOM and CP949 sample read fallback.
- Sample schema success/failure.
- Transform key extraction emits expected `(timestamp, device_id)` for:
  - legacy PLC -> `extruder_plc`
  - integrated PLC -> `extruder_integrated`
  - temperature -> `spot_temperature_sensor`
- Classification matrix for `target`, `already_in_db`, `partial_overlap`, `risky`, `excluded`.

Backend integration tests:

- Temporary CSV folder + fake reconciliation repository returning no matches -> `target`.
- Fake repository returning all keys -> `already_in_db`.
- Fake repository returning subset -> `partial_overlap`.
- DB repository raises connection error -> run `partial_failed`, candidate rows `risky/db_unreachable`.
- Key extraction timeout -> item `risky/timeout`.
- Cancel active preview -> run `cancelled`.
- New preview while running -> `409`.
- App startup marks stale `running` preview as `failed/interrupted`.

Supabase contract tests:

- Migration includes `UNIQUE ("timestamp", device_id)`.
- Edge Function upsert uses `onConflict: "timestamp,device_id"`.
- Preview repository query matches exact `(timestamp, device_id)` pairs.
- Regression test proves latest-timestamp-only would be wrong:
  - DB has a later timestamp for the same device.
  - CSV contains earlier timestamp missing in DB.
  - Preview must classify as `target` or `partial_overlap`, not `already_in_db`.

Frontend tests:

- Upload Preview empty state renders.
- Running state renders status strip.
- Table renders all five status badges with icon + label.
- Long Korean reason text wraps without overflow.
- Filters/search/sort do not hide run-level DB warnings.
- Start Upload remains disabled in this phase.
- i18n keys exist for Korean and English status/reason labels.

Manual QA:

- 1440x900, 1366x768, 1024x768, and 720px wide layouts.
- Korean UI default.
- English toggle.
- Long filename and long Windows path.
- DB unreachable state.
- Large CSV mock with chunked progress by polling.

## Implementation Order

1. Add `docs/07_upload_preview_plan.md` and keep it as the implementation source for this feature.
2. Add backend Pydantic DTOs for preview requests/responses.
3. Add SQLite migration/schema for `preview_runs` and `preview_items`.
4. Add `PreviewRepository` with run/item CRUD and active-run guard.
5. Extract `CandidateScanner` from legacy `core/files.py` patterns without legacy processed-state dependency.
6. Add `CsvKeyExtractor` using legacy transform builders in chunked mode.
7. Add `SupabaseReconciliationRepository` using direct local Postgres exact-key queries.
8. Add `PreviewService` classification and timeout/cancel logic.
9. Add FastAPI endpoints and polling response shape.
10. Add backend tests for DTOs, scanner, key extraction, classification, DB failure, cancel, timeout, and latest-timestamp regression.
11. Implement Upload Preview frontend table using mock data first.
12. Wire frontend to real preview endpoints with TanStack Query polling.
13. Add frontend tests and browser QA.
14. Update README with preview run instructions after implementation.

## Parallel Work Plan

```text
Lane A: SQLite schema + repository + DTOs
Lane B: scanner + transform/key extraction
Lane C: Supabase exact reconciliation repository + contract tests
Lane D: Upload Preview UI table + mock data + i18n

Merge order:
  A + B -> PreviewService local-only classification
  PreviewService + C -> exact DB reconciliation
  API + D -> full UI polling flow
```

## Acceptance Criteria

- Existing Dashboard scaffold still builds and renders.
- Preview API can create, poll, cancel, and retry preview runs.
- Preview does not import or read legacy `uploader_state.db`.
- Preview classification never depends on latest timestamp only.
- A DB outage is visible as run `partial_failed` and item `risky/db_unreachable`.
- Large CSV handling is chunked and bounded by timeout.
- All five preview item statuses render in the Upload Preview table.
- Risky/partial/excluded rows show reason text, not color alone.
- Tests cover the latest-timestamp regression.
- Supabase unique/upsert safety remains unchanged.
