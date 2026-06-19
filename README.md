# Extrusion Web Console

Local web operations console for extrusion data upload and local Supabase operations.

This project replaces the legacy Tkinter GUI in `C:\Users\user\Documents\GitHub\Extrusion_data`.

## Current Status

The current local console baseline is in place:

- FastAPI backend with `/api/health`, real-state `/api/dashboard`, and real-state `/api/dashboard/summary`.
- Upload Preview reconciliation API with persisted preview runs/items:
  - `POST /api/upload/preview`
  - `GET /api/upload/preview/latest`
  - `GET /api/upload/preview/{previewRunId}`
  - `POST /api/upload/preview/{previewRunId}/cancel`
- Upload Preview now writes `upload.preview` audit rows for success, DB unreachable, missing source, malformed request validation, and active preview conflict paths.
- React + Vite + TypeScript frontend.
- Dashboard Variant D UI using design tokens from `docs/04_design_system.md`.
- Upload Preview UI with Preview/Job tabs, status summary, polling, filters, and the five preview states.
- Upload Job API/UI with Start Upload, Retry Failed, pause/resume/cancel, SQLite job/file/event state, SSE event replay, and canonical `acceptedRows` counts for Edge/Supabase upsert-accepted rows.
- Already-in-DB hard delete API/UI for selected `already_in_db` Preview rows only, with local DB target guard, DELETE privilege preflight, typed exact-key confirmation, rollback-readiness gate, commit-unknown reconciliation, and safe audit evidence.
- Local Supabase runtime status/start/stop API with required-container precheck, runtime events, and audit logging.
- Dashboard runtime module connected to the runtime API in API mode.
- Settings save UI connected to `GET /api/config` and `PUT /api/config`, with editable config fields, dirty state, Save/Reset controls, validation feedback, and save status.
- Env/process and repo `.env` override fields are disabled/read-only in Settings and blocked by the backend from config JSON writes.
- Settings saves persist to `%APPDATA%\ExtrusionWebConsole\config.json`, are loaded by new `Settings` instances, and write `settings.save` success/failure/blocked audit rows.
- Logs page with separate Job Logs and Audit Logs tabs.
- Audit Logs API/UI with redacted, paginated, filtered, append-only audit rows.
- TanStack Query Dashboard query with separate frontend mock/default mode and API mode.
- Korean/English i18n baseline with language persistence in `localStorage`.
- Frontend-only mock Dashboard state switching with `?state=ready|attention|blocked|running`.
- Launcher phase 2 with FastAPI static frontend serving, Windows double-click launcher scripts, per-run local token protection for mutating APIs, and operator-mode API docs hardening.
Legacy upload state import is not implemented in this baseline.

In API mode, Dashboard endpoints read the active backend state instead of scaffold mock data. The response aggregates the active state DB latest upload job, runtime readiness summary, and safe audit summary. If the active state DB context is empty or different from a reviewed QA state DB, Dashboard shows that real empty/different state instead of fabricating a running upload.

Upload Preview v1 scans configured local CSV folders, extracts exact `(timestamp, device_id)` keys, persists preview results in SQLite, and compares those keys with local Supabase when `EWC_SUPABASE_DB_URL` is configured. If the DB URL is missing or unreachable, DB-dependent files are shown as `risky/db_unreachable`; they are not silently treated as upload targets.

Preview requests are audit logged as `upload.preview`. Successful previews write `success` rows; DB unreachable, missing source, malformed JSON, and validation failures write `failure` rows; active preview conflicts write `blocked` rows. Audit params use safe summary fields such as `previewRunId`, counts, `dbStatus`, `reasonCode`, and `requestedFilters`. Raw file paths, filenames, DB URLs, tokens, anon keys, service role values, secrets, and malformed raw request bodies are not stored in audit params.

Already-in-DB hard delete is a production-critical maintenance flow, not a general database cleanup tool. It can target only selected Preview items whose status is `already_in_db`. The backend rebuilds exact keys from current source files, verifies rollback readiness, proves the configured DB is the expected local Supabase target, checks DELETE privilege non-destructively, writes `delete_run` state and `upload.delete_start` audit before DB mutation, then performs an all-or-nothing transaction. API responses and audits expose counts, hashes, status, and safe reason codes only; raw `(timestamp, device_id)` values, source paths, filenames, DB URLs, tokens, Authorization values, JWTs, and secrets are not returned.

Date-scoped delete is a maintainer-only extension of the delete API for
mixed-date `already_in_db` evidence. It is not a general operator UI feature.
Maintainers may use `timestampStartDate` and `timestampEndDate` on Delete
Preflight only after separate approval for that exact timestamp-date scope.
Whole-item delete must not be used to remove one date from a mixed-date item.

Project status summaries and infographics must follow
`docs/158_operator_status_language_policy.md`. Do not label safety restrictions,
approval boundaries, intentional v1 exclusions, or conditional caveats as a
generic `미완료` / `미작업` / `미승인` bucket.

The Dashboard layout has been browser-QA'd at `1440x900`, `1366x768`, `1024x768`, and `720x900`.

## Repository Layout

```text
backend/
  app/
    api/
    core/
    schemas/
frontend/
  src/
    api/
    components/
    i18n/
    pages/
    styles/
tests/
  backend/
docs/
```

## Prerequisites

- Python 3.11 or newer
- Node.js 20 or newer
- npm

Local Supabase, WSL, Docker, and Grafana are not required for frontend mock/default Dashboard and Upload Preview development paths. Those mock paths are for development and screenshot QA only, not operational evidence. Local Supabase is required when testing real reachable Upload Preview reconciliation, Upload Job execution, API-mode Dashboard runtime evidence, or Local Supabase runtime controls.

## Operator Launcher

Launcher phase 3 lets an operator run the built web console from one localhost backend origin with a per-run local token protecting mutating APIs and optional Windows Desktop/Start menu shortcuts.

First build the frontend once from `frontend/`:

```powershell
npm run build
```

The default `npm run build` uses the frontend mock/default mode and is useful for local UI development and screenshot QA. It is not the API-mode operator validation build.

For an API-mode operator package that uses the real backend APIs instead of frontend mock data, build with:

```powershell
npm run build:api
```

Both build commands write `frontend/dist/frontend-build-info.json`. The package assembly step records this as `frontendMode` in `package-build-info.json`.

Then double-click:

```text
launcher\start_web_console.bat
```

Or run from PowerShell:

```powershell
.\launcher\start_web_console.ps1
```

Maintainers can install or refresh Windows shortcuts from the prepared operator folder:

```powershell
.\launcher\install_shortcuts.ps1
```

This creates or updates one Desktop shortcut and one Start menu shortcut named `Extrusion Web Console`. Re-running the script is idempotent: it updates the existing shortcuts instead of creating duplicates. The shortcuts target the repo-local `launcher\start_web_console.bat` and use the prepared folder as the working directory. `ShortcutName` is validated as a file name only: empty names, path separators, `..` traversal markers, Windows invalid filename characters, and absolute paths are rejected before any shortcut is written. A batch wrapper is also available:

```text
launcher\install_shortcuts.bat
```

Use `-CheckOnly` to preview the shortcut paths without writing shortcuts:

```powershell
.\launcher\install_shortcuts.ps1 -CheckOnly
```

The shortcut installer does not delete AppData config, state databases, launcher logs, Docker data, database data, or operational CSV files.

The launcher starts the backend on `127.0.0.1:8000`, waits for `/api/health`, then opens:

```text
http://127.0.0.1:8000/
```

Operator mode does not start Vite. FastAPI serves `frontend/dist` and the frontend calls same-origin `/api/*`.

The launcher generates a per-run local API token, passes it to the backend through process environment, and never puts it in the browser URL. FastAPI injects the token into the served app shell at response time, and the frontend keeps it in memory only. Protected writes such as Settings save, Upload Preview start/cancel, Upload Job start/retry/pause/resume/cancel, Upload Delete preflight/start/reconcile, and Local Supabase start/stop send `X-EWC-Local-Token`. Read-only APIs such as `/api/health`, `GET /api/config`, `GET /api/audit`, and upload/job status reads remain token-free. `OPTIONS` requests are not blocked by the local token guard; route-level method handling may still return the normal API response. Missing or invalid tokens return `403 local_token_required`, while valid-token requests proceed through the existing API validation. Operator launcher mode disables `/api/docs`, `/api/openapi.json`, and ReDoc-style docs routes instead of token-gating them.

The local API token must not be stored or copied into URL query strings, `localStorage`, `sessionStorage`, launcher logs, backend logs, audit params, screenshots, generated `.gstack` artifacts, or `frontend/dist`. Development with Vite should use explicit `EWC_LOCAL_TOKEN_MODE=dev-disabled` when the backend is not serving the token bootstrap. Dev/test API docs can be retained with `EWC_API_DOCS_MODE=enabled`; this override is for developer and test use only. If a developer sets only `EWC_LOCAL_API_TOKEN` on the backend while using the Vite dev shell, mutating API calls can fail because the Vite page does not receive the backend-served bootstrap token.

If `frontend/dist/index.html` is missing, the launcher stops with a clear message. It does not run `npm run build` by default. Developers can explicitly request a build:

```powershell
.\launcher\start_web_console.ps1 -BuildFrontend
```

The explicit build path fails clearly if `npm run build` exits non-zero or does not produce `frontend/dist/index.html`.

`-CheckOnly` verifies launcher prerequisites, local token policy, and operator API docs policy without starting a backend process. It reports presence/policy status only; it never prints token values.

Launcher logs are written under:

```text
%APPDATA%\ExtrusionWebConsole\logs\launcher\
```

The launcher reuses an already healthy Extrusion Web Console backend on the selected port. If another process owns the port, it stops and reports the conflict; it does not kill unknown processes.

Launcher phase 2 does not run local Supabase bootstrap, reset, cleanup, prune, Docker create/delete, or volume operations. Local Supabase status/start/stop remains inside the web console runtime API and existing command allowlist policy.

Prepared operator folders should include `frontend/dist` and a target-PC prepared `.venv\Scripts\python.exe`. Node/npm are not required for normal operator launch. The `.venv` may be tied to the target PC and Python version, so dependency setup remains a maintainer responsibility before handoff.

Maintainers can assemble a manifest-validated prepared package after building `frontend/dist` and preparing the target-PC `.venv`:

```powershell
.\packaging\assemble_operator_package.ps1
```

For API-mode package assembly, require the API-mode frontend metadata:

```powershell
.\packaging\assemble_operator_package.ps1 -FrontendMode api
```

If `-FrontendMode api` is used with a mock-mode or metadata-missing `frontend/dist`, assembly fails before package copy. Mock/default package assembly remains available through the default build and default assembly path.

The default `-FrontendMode auto` is backward-compatible for existing mock/default package assembly. If legacy `frontend/dist` lacks `frontend-build-info.json`, package metadata can record `frontendMode` as `unknown`; do not use `auto` for API-mode release packages. API-mode release assembly must use `-FrontendMode api`.

The assembly script copies only manifest-allowlisted runtime files into a new timestamped repo-external output folder by default. `OutputRoot` must be outside the repository root so package output cannot be created inside source control. The script validates required package contents, blocks denylisted files such as raw `.env*`, tests, developer artifacts, logs, state DB files, generated screenshots, and operational CSV data, and prunes `.venv` cache/test-only content such as `__pycache__`, compiled bytecode, pytest cache, dependency test directories, and dependency-provided `.agents` entries while preserving dependency metadata and license/notice files.

The operator package does not copy the repository README verbatim. It uses the sanitized package runtime note as the package-local README so marker-heavy engineering docs and path examples stay out of release artifacts.

The package docs subset is `README.md`, `CHANGELOG.md`, `VERSION`, and `docs/operator_package_runtime_note.md`. Marker-heavy engineering docs remain in the repository but are not copied into the operator package. PR #38 QA confirmed zip-entry scans with dependency test segments `0`, cache/bytecode entries `0`, marker-heavy docs `0`, denylist matches `0`, and redaction marker counts `0` for credential, operational filename-family, Windows path, DB URL, Authorization, and JWT classes. The current runtime prune implementation additionally removes dependency-provided `.agents` runtime entries and keeps package/zip `.agents` entry counts at `0` for mock/default and API-mode packages. Runtime `.py`, native files, dist-info metadata, `METADATA`, `RECORD`, and license/notice/copying material remain present. Python may create cache files after import or HTTP smoke; that post-runtime cache is distinct from clean zip contents.

Zip handoff is optional:

```powershell
.\packaging\assemble_operator_package.ps1 -CreateZip
```

When `-CreateZip` is used, a SHA-256 checksum file is written next to the zip. The package folder metadata records the actual zip hash after creation; the metadata inside the zip marks `zipCreated=true` and points to the adjacent checksum file. The script does not install shortcuts, delete existing package folders, delete AppData config/state/logs, run database cleanup, or run Docker cleanup.

For operator handoff, follow `docs/32_operator_package_handoff_runbook.md` for zip/checksum verification, extraction, shortcut install, first launch, Settings checks, log collection, rollback, and support escalation.

For day-to-day upload decisions, including the normal "no upload target" outcome,
follow `docs/151_operator_upload_gate_runbook.md`. This keeps fresh Preview-only,
target count review, separate Start Upload approval, and separate Retry Failed
approval as the required operating path.

## Backend Development

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r backend\requirements.txt
.\.venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Health checks:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
Invoke-RestMethod http://127.0.0.1:8000/api/dashboard
Invoke-RestMethod http://127.0.0.1:8000/api/dashboard/summary
```

Upload Preview configuration is read from environment-backed settings. Set values locally in PowerShell, a local `.env`, or app config; do not paste secret values into chat, logs, docs, or PR bodies.

```powershell
$env:EWC_PLC_DATA_DIR="<local PLC source folder>"
$env:EWC_SUPABASE_DB_URL="<local Supabase DB URL>"
$env:EWC_SUPABASE_URL="<local Supabase API URL>"
$env:EWC_SUPABASE_ANON_KEY="<local Supabase anon key>"
$env:EWC_SUPABASE_EDGE_URL="<local Supabase Edge URL>"
$env:EWC_STATE_DB_PATH="<local state DB path>"
```

For developer API-mode runs started through `launcher/start_web_console.ps1`, the launcher enforces the approved mapped-drive process-data source class before the backend starts. If process env, repo `.env`, or config JSON provides a non-canonical `plcDataDir`, the launcher refuses to start by default so Preview cannot drift to a fixture, stale UNC, or other wrong source. `-AllowNonCanonicalSource` is available only as an explicit diagnostics opt-in. Backend `Settings` does not silently replace explicit env/config source bindings. This is a developer launcher guard, not an operator package pin. Verify the active source with read-only `GET /api/config` and a backend-side path existence preflight before running Upload Preview.

The API-mode frontend does not use Settings mock fallback values for active source binding. Settings, Upload Preview, and Start Upload readiness must be judged from the backend `/api/config` response and its sanitized `items` / `targetClasses` fields. The default frontend mock build may show development sample values only; it is for screenshot QA and UI development, not operational source evidence.

`EWC_SUPABASE_DB_URL` is optional for mock UI/dev smoke checks. It is required for real Upload Preview exact reconciliation. Without it, or when the local Supabase DB is unreachable, preview runs still persist and DB-dependent CSV candidates are shown as `risky/db_unreachable` under a `partial_failed` run.

`EWC_SUPABASE_ANON_KEY` and either `EWC_SUPABASE_EDGE_URL` or `EWC_SUPABASE_URL` are required for real Start Upload and Retry Failed execution. Preview-origin upload disables the legacy latest-timestamp Smart Sync filter and relies on the existing `all_metrics(timestamp, device_id)` upsert safety for final duplicate protection.

Upload Job responses and job events expose `acceptedRows` as the canonical count of rows accepted/upserted by the Edge Function and Supabase upsert path. This is not a net-new physical insert count: duplicate-safe reruns can report positive `acceptedRows` while the DB row count delta stays `0`. The legacy `insertedRows` response field remains available as a deprecated compatibility alias for v1, but operator-facing Upload UI labels use `Accepted` / `수락` and avoid inserted-row wording. The existing SQLite `inserted_rows` storage column is retained without rename or migration.

Local Supabase runtime control defaults to this repository's independent local Supabase assets:

```powershell
$env:EWC_LOCAL_SUPABASE_PROJECT_PATH="<local Supabase project path>"
$env:EWC_LOCAL_SUPABASE_PROJECT_ID="Extrusion_web_console"
$env:EWC_LOCAL_SUPABASE_API_PORT="55321"
$env:EWC_LOCAL_SUPABASE_DB_PORT="25433"
$env:EWC_LOCAL_SUPABASE_STUDIO_PORT="55323"
```

Runtime control is intentionally non-destructive. It does not run bootstrap, reset, cleanup, Docker delete, volume delete, prune, `supabase init`, `supabase db reset`, `docker run/create/rm`, or `docker compose up/down`. If required Supabase containers are missing, start is blocked as `required_container_missing`; v1 does not create a new local Supabase stack.

The legacy local stack can still be selected explicitly through env/config overrides for rollback during rollout, but it is no longer the built-in default.

Config API smoke check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/config

$body = @{
  values = @{
    grafanaUrl = "http://localhost:3001"
    localSupabaseApiPort = 55321
  }
} | ConvertTo-Json -Depth 4

Invoke-RestMethod -Method Put `
  -Uri http://127.0.0.1:8000/api/config `
  -ContentType "application/json" `
  -Body $body

Invoke-RestMethod "http://127.0.0.1:8000/api/audit?action=settings.save&limit=20"
```

`PUT /api/config` accepts only known config keys. It rejects environment-overridden keys, including repo `.env` key-presence overrides, writes blocked audit rows for those attempts, and writes failure audit rows for validation failures including malformed JSON bodies. Audit params store safe metadata such as `savedSettings`, `rejectedSettings`, and `validationReason`; they do not store raw config values, DB URLs, tokens, anon keys, service role values, or malformed request bodies. Config writes use a per-config-file lock, a unique temp filename, and atomic replace. Settings precedence is built-in defaults, then config JSON, then repo `.env` or launcher env, then process environment.

The Settings page uses the config API in `VITE_API_MODE="api"`. Non-secret editable fields are sent only when changed. Secret fields display only an empty replacement input and hidden-value status; existing secret raw values are never rendered. Empty or unchanged secret inputs are excluded from the save payload, and a secret key is included only when the operator types a replacement value.

Runtime API smoke check. Run the start/stop calls only when no upload job or preview run is active:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/runtime/local-supabase
$runtime = Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/runtime/local-supabase/start
Invoke-RestMethod http://127.0.0.1:8000/api/runtime/operations/$($runtime.operationId)
```

Audit Logs API smoke check:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/audit?limit=50"
Invoke-RestMethod "http://127.0.0.1:8000/api/audit?result=blocked&sort=ts&order=desc"
Invoke-RestMethod "http://127.0.0.1:8000/api/audit?q=upload.start&limit=10"
```

The `q` parameter searches only safe scalar fields such as `auditId`, `action`, `targetType`, `targetId`, `result`, `jobId`, `requestId`, `actor`, and `errorCode`. It does not search raw `error_message` values or raw/redacted params JSON, so legacy rows containing secret-like diagnostics cannot be reverse-searched through `/api/audit`.

Upload Preview API smoke check:

```powershell
$body = @{
  rangeMode = "today"
  sources = @("plc")
  options = @{
    stableLagMinutes = 3
    sampleRows = 200
    chunkRows = 20000
    maxFiles = 500
    maxRunSeconds = 120
    maxFileSeconds = 30
    forceFullScan = $false
  }
  retryOfRunId = $null
} | ConvertTo-Json -Depth 5

$preview = Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/api/upload/preview `
  -ContentType "application/json" `
  -Body $body

Invoke-RestMethod http://127.0.0.1:8000/api/upload/preview/$($preview.previewRunId)
Invoke-RestMethod http://127.0.0.1:8000/api/upload/preview/latest
Invoke-RestMethod "http://127.0.0.1:8000/api/audit?action=upload.preview&limit=20"
```

Upload Job API smoke check after a successful preview with target rows:

```powershell
$job = Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/api/upload/jobs `
  -ContentType "application/json" `
  -Body (@{ previewRunId = $preview.previewRunId } | ConvertTo-Json)

Invoke-RestMethod http://127.0.0.1:8000/api/upload/jobs/$($job.jobId)
Invoke-RestMethod http://127.0.0.1:8000/api/upload/jobs/latest
```

Already-in-DB hard delete API contract:

- `POST /api/upload/delete/preflight` is a protected preflight. It accepts a Preview run id, selected Preview item ids, an expected selected item count, and optional maintainer-only `timestampStartDate` / `timestampEndDate` values for mixed-date delete scope. It returns `ready` or `blocked`, exact selected key count, rollback readiness, sanitized DB target guard, hashes, expiry, optional date scope, and safe reason code.
- `POST /api/upload/delete/jobs` is protected and destructive. It requires a ready preflight, typed exact key count, no-undo acknowledgement, and rollback-limit acknowledgement. It must not be used against operational data without separate explicit approval.
- `GET /api/upload/delete/jobs/latest` is read-only and safe for status checks.
- `POST /api/upload/delete/jobs/{deleteRunId}/reconcile` is protected but read-only against local Supabase. It updates local delete state/audit for `commit_unknown` or explicitly retried `reconciliation_failed` runs and never issues a delete.

Implementation and destructive smoke for delete must use disposable local fixture DBs unless an operator gives separate production approval. Normal upload troubleshooting must still not use DB reset, truncate, broad manual cleanup, Supabase lifecycle, or Docker cleanup. Date-scoped delete remains maintainer-only until frontend controls, operator copy, i18n, and runbook approval are implemented separately.

Backend tests:

```powershell
.\.venv\Scripts\python -m pytest tests\backend
```

## Frontend Development

From `frontend/`:

```powershell
npm install
npm run typecheck
npm run build
npm run build:api
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

By default the frontend uses local mock/demo data. To run against the backend API and active backend state instead:

```powershell
$env:VITE_API_MODE="api"
npm run dev
```

The Vite dev server proxies `/api` to `http://127.0.0.1:8000`.

Important mode split: `?state=ready|attention|blocked|running` is a frontend mock-mode feature only. When `VITE_API_MODE="api"` is used, Dashboard calls `/api/dashboard` and `/api/dashboard/summary`; those endpoints aggregate the active state DB latest upload job, runtime readiness, and safe audit summary. API mode should show neutral empty/unknown state when data is missing, not the old fake running job.

The Upload Preview and Upload Job pages also use mock data by default so preview/job states can be inspected without local Supabase. These mock paths are development and screenshot QA aids only. To use the real backend preview and job APIs, run the frontend with `VITE_API_MODE="api"` and configure the backend environment values above.

For release-maintainer API-mode package builds and operator validation, prefer:

```powershell
npm run build:api
```

This compiles the frontend with API mode and writes build metadata consumed by package assembly validation.

For API-mode release packages, follow the build with `.\packaging\assemble_operator_package.ps1 -FrontendMode api`. The default assembly mode is only for backward-compatible mock/default packaging and can record `frontendMode=unknown` when old build metadata is absent.

The Logs page shows mock audit rows by default for development and screenshot QA. It uses `GET /api/audit` when `VITE_API_MODE="api"` is enabled. Audit Logs never expose raw params, secrets, tokens, DB URLs, raw `error_message` search, raw params JSON search, or arbitrary SQL query controls. API responses return sanitized `errorMessage` values and decoded redacted params from `params_json_redacted`.

Local screenshot QA for Upload Job and Audit Logs can be run in mock mode without Docker or local Supabase:

```powershell
cd frontend
npm run qa:screenshots
```

The screenshot runner writes ignored artifacts under `.gstack/screenshots/upload-job-browser-qa/`, checks the required viewport matrix, verifies `Accepted` / `수락` wording, captures console/network failures, and redacts path/credential-like markers before writing text artifacts.
It uses `127.0.0.1:5175` by default and does not reuse an existing server, so screenshot QA cannot silently attach to a stale app or API-mode dev server.
The runner captures 32 screenshots across Dashboard, Upload Preview, Upload Job, Job Logs, Audit Logs, and Settings, verifies `DB에 있음` / `Already in DB`, blocks inserted-row wording such as `Inserted`, `적재`, `삽입`, and `새로 삽입`, and scans artifacts for generic timestamp-style CSV names, Windows absolute paths, DB URLs, tokens, and credential-like markers. Source docs and mock labels should use sanitized sample names instead of operational CSV filename patterns.

Mock Dashboard states can be checked with query strings:

```text
http://127.0.0.1:5173/?state=ready
http://127.0.0.1:5173/?state=attention
http://127.0.0.1:5173/?state=blocked
http://127.0.0.1:5173/?state=running
```

## Verification Checklist

- `npm run typecheck`
- `npm run build`
- `.\.venv\Scripts\python -m pytest tests\backend`
- `Invoke-RestMethod http://127.0.0.1:8000/api/health`
- Browser QA at `http://127.0.0.1:5173`

Dashboard QA:

- Sidebar shows only Dashboard, Upload, Logs, Settings.
- Dashboard first viewport shows safety summary, Upload, Local Supabase, WSL/Storage, Grafana, and State Store.
- Grafana is status/link only. No iframe.
- Status uses icon + label + semantic color.
- Tables keep 36px row height and horizontal scrolling on small widths.
- Korean/English language toggle does not break buttons, badges, or table cells.
- Korean/English language choice persists after reload.
- Ready, attention, blocked, and running mock states are visually distinct and internally consistent.

Upload Preview QA:

- Preview tab replaces the old Upload placeholder.
- Preview status table shows `target`, `already_in_db`, `partial_overlap`, `risky`, and `excluded`.
- Status uses icon + label + semantic color, not color alone.
- DB unreachable is visible in the run status strip and risky rows.
- Preview success, DB unreachable, missing source, malformed JSON, validation failure, and active preview conflict paths write `upload.preview` audit rows.
- Preview audit params expose safe summary fields only and do not include raw file paths, filenames, DB URLs, tokens, anon keys, service role values, secrets, or malformed raw request bodies.
- Start Upload is enabled only for a succeeded preview with reachable DB and `target` rows.
- Start Upload excludes `already_in_db`, `partial_overlap`, `risky`, and `excluded` rows by default.
- Already-in-DB delete selection is available only for `already_in_db` rows, requires API mode, preflight, typed exact count, rollback acknowledgements, local token protection, and safe audit rows.
- Delete commit-unknown recovery is visible and requires explicit reconcile before another delete preflight/start can proceed.
- Upload Job tab shows file progress, pause/resume/cancel controls, Retry Failed, and live/persisted events.

Audit Logs QA:

- Logs page has separate Job Logs and Audit Logs tabs.
- Audit Logs table uses a light table surface with result badges, params chips, and error columns.
- Filters work for action, result, recent window, job ID, request ID, and safe text search.
- Pagination works without exposing delete, update, export, or arbitrary SQL controls.
- Secret-like params and error messages are redacted before display, and `q` cannot reverse-search raw secret-bearing `error_message` rows.
- Raw params JSON search remains unavailable; only decoded redacted params are displayed.
- `audit_log` update/delete attempts are blocked by append-only SQLite triggers `audit_log_no_update` and `audit_log_no_delete`.
- PR #6 QA covered backend `/api/audit`, Vite proxy `/api/audit`, Logs tab switching, Audit filters, pagination, loading/empty/error states, Korean/English i18n, and Dashboard/Upload/Settings smoke regression.

Settings Save Audit QA:

- PR #8 QA passed targeted config/audit backend tests, full backend tests, frontend typecheck/build, `git diff --check`, and direct API smoke for `GET /api/config`, `PUT /api/config`, and `/api/audit?action=settings.save`.
- QA confirmed success, failure, and blocked `settings.save` audit rows, malformed JSON failure audit, env override blocking, config JSON loading into new `Settings`, env/process precedence over config JSON, and non-exposure of raw config values, DB URLs, tokens, anon keys, service role values, or malformed request bodies.
- PR #23 adds the Settings save UI and passed frontend typecheck/build, `npm run qa:screenshots`, config API targeted tests (`13 passed`), full backend tests (`134 passed`), `git diff --check`, and Settings API-mode smoke.
- QA confirmed editable fields, env/process override disabled state, repo `.env` override backend blocking, dirty state, Save/Reset behavior, validation feedback, save success/failure status, `/api/audit?action=settings.save` queryability, and secret placeholder behavior.
- QA confirmed raw secret values, DB URLs, tokens, anon keys, and service role values are not rendered in the Settings UI, save payloads, audit params, or screenshot QA artifacts. Clean-cwd backend tests remain intentional because repo `.env` presence changes override behavior by design.

Upload Preview Audit QA:

- PR #9 QA passed twice: targeted preview/audit backend tests, full backend tests, frontend typecheck/build, `git diff --check`, and direct API smoke for `POST /api/upload/preview`, `GET /api/upload/preview/{id}`, `GET /api/upload/preview/latest`, and `/api/audit?action=upload.preview`.
- QA confirmed `upload.preview` success, failure, and blocked audit rows for preview success, DB unreachable, missing source, malformed JSON, validation failure, and active preview conflict paths.
- QA confirmed audit params use `previewRunId`, counts, `dbStatus`, `reasonCode`, and `requestedFilters`, without raw file paths, filenames, DB URLs, tokens, anon keys, service role values, secrets, or malformed raw request bodies.
- Remaining risk: Browser screenshot QA for PR #9 was not completed because `node_repl` failed with a kernel asset path error; Vite/backend HTTP smoke covered the running shell and proxy instead. Large real CSV preview soak remains a separate operator-environment validation item.

Upload Job Accepted Rows QA:

- PR #19 QA passed targeted upload job backend tests, full backend tests, API/SSE smoke, frontend typecheck/build, `git diff --check`, Vite/backend HTTP smoke, and source/build wording checks.
- QA confirmed Upload Job API responses, file rows, job events, and SSE replay include canonical `acceptedRows` and compatibility `insertedRows`.
- QA confirmed Upload UI uses `acceptedRows` first, labels accepted/upserted rows as `Accepted` / `수락`, and no longer shows operator-facing `Inserted`, `적재`, `삽입`, or `새로 삽입` wording. Korean Upload Preview `already_in_db` now displays `DB에 있음`.
- Remaining risk: Browser screenshot QA for PR #19 was not completed because `node_repl` failed with a kernel asset path error and local Playwright was not installed; HTTP smoke covered Dashboard, Upload, Logs, Settings, and Vite proxy reachability.

Playwright Screenshot QA:

- PR #22 adds project-owned Playwright screenshot QA through `npm run qa:screenshots` under `frontend/`.
- QA runs in mock mode on `127.0.0.1:5175`, does not require Docker, local Supabase, DB URLs, auth keys, or operational CSV fixtures, and writes ignored artifacts under `.gstack/screenshots/upload-job-browser-qa/`.
- QA captures 32 screenshots across `1440x900`, `1366x768`, `1024x768`, and `720x900`; smoke covers `/`, `/upload`, `/logs`, and `/settings`.
- QA verifies `Accepted` / `수락`, `DB에 있음` / `Already in DB`, blocks inserted-row wording, captures console/page/network failures, and scans text artifacts for generic timestamp-style CSV names, Windows absolute paths, credential-like markers, DB URLs, and token markers.
- PR #22 blocker fix `b570207` removed operational CSV filename-pattern markers from source/docs and kept mock filename/path/event labels sanitized.

Launcher Local Token QA:

- PR #28 QA passed targeted backend token/static/launcher tests (`17 passed`), full backend tests from clean cwd (`151 passed`), frontend typecheck/build, `npm run qa:screenshots`, launcher `-CheckOnly`, token HTTP smoke, and `git diff --check`.
- QA confirmed read-only APIs stay token-free, protected mutating APIs reject missing/invalid tokens with `403`, valid-token Settings save proceeds, and `OPTIONS` is not blocked by the token guard.
- QA confirmed token values are absent from URL query strings, browser storage, audit params, backend logs, launcher logs, screenshot artifacts, committed `.gstack` content, and committed `frontend/dist` content. Unsafe marker scan count was `0`.
- PR #30 API docs hardening disables `/api/docs`, `/api/openapi.json`, and ReDoc-style docs routes in operator launcher mode while preserving Swagger/OpenAPI in dev/test docs-enabled mode through `EWC_API_DOCS_MODE=enabled`.
- PR #30 QA passed targeted route/token/OpenAPI backend tests (`33 passed`), full backend tests from clean cwd (`153 passed`), frontend typecheck/build, `npm run qa:screenshots`, launcher `-CheckOnly`, operator HTTP smoke (`/api/docs`, `/api/openapi.json`, `/api/redoc` all `404`), dev/docs-enabled HTTP smoke (`/api/docs` and `/api/openapi.json` both `200`), and `git diff --check`.
- PR #32 Windows shortcut packaging adds `launcher\install_shortcuts.ps1` and `.bat`, passed targeted launcher tests (`17 passed`), shortcut `-CheckOnly`, frontend typecheck/build, and `git diff --check`; path-safety review confirmed unsafe `ShortcutName` inputs are rejected before writing shortcuts.
- Full backend tests should be run from clean cwd when validating this branch because repo cwd `.env` presence intentionally changes Settings/config override behavior.

Operator Package Runtime Prune QA:

- PR #38 QA passed targeted packaging tests (`11 passed`), full backend tests from clean cwd (`176 passed`), frontend typecheck/build, `npm run qa:screenshots`, package assembly with `-CreateZip`, zip-entry prune/redaction scans, packaged import smoke, launcher/shortcut `-CheckOnly`, HTTP route smoke, no-token mutation guard, and operator docs hardening smoke.
- Zip-entry scan confirmed dependency test segments `0`, cache/bytecode entries `0`, marker-heavy docs `0`, denylist matches `0`, dependency-provided `.agents` entries `0`, and redaction marker counts `0` for credential, operational filename-family, Windows path, DB URL, Authorization, and JWT classes.
- Runtime `.py`, native files, dist-info metadata, `METADATA`, `RECORD`, and license/notice/copying material are preserved. Python cache generated after import or HTTP smoke is post-runtime output and is distinct from clean zip contents.

Browser QA has been run against:

- `http://127.0.0.1:5173/?state=ready`
- `http://127.0.0.1:5173/?state=attention`
- `http://127.0.0.1:5173/?state=blocked`
- `http://127.0.0.1:5173/?state=running`
- Upload Preview, Settings runtime section, and Logs page through sidebar navigation.

## Source Documents

- `AGENTS.md`
- `DESIGN.md`
- `docs/00_product_scope.md`
- `docs/01_development_roadmap.md`
- `docs/02_engineering_plan.md`
- `docs/03_ui_ux_plan.md`
- `docs/04_design_system.md`
- `docs/05_dashboard_design_review.md`
- `docs/06_dashboard_implementation_spec.md`
- `docs/07_upload_preview_plan.md`
- `docs/08_upload_job_sse_plan.md`
- `docs/09_local_supabase_control_plan.md`
- `docs/10_audit_logs_plan.md`
- `docs/156_operator_already_in_db_delete_contract.md`
- `docs/157_operator_2026-01-19_delete_execution.md`
- `docs/158_operator_status_language_policy.md`
- `docs/159_v2_scope_and_safety_plan.md`
- `docs/160_v2_delete_lan_audit_rollback_technical_design.md`
- `docs/161_v2_open_decisions_review.md`

## Reference Project

Legacy project:

```text
C:\Users\user\Documents\GitHub\Extrusion_data
```

Use the legacy project as a behavior reference and extraction source. Do not directly port `uploader_gui_tk.py`.

## V1 Target

Core Ops only:

- Dashboard
- Settings
- Upload Preview
- Start Upload
- Retry Failed
- Upload progress and logs
- Local Supabase status/start/stop
- Grafana status/link only
- Audit logs

Out of scope for this v1 baseline:

- Full legacy core extraction
- Data Mgmt
- Cycle Ops
- Training Dataset Builder
- Grafana iframe
- Cloud or multi-user web access

## Troubleshooting

If the backend fails after pulling this branch with `ModuleNotFoundError: psycopg` or a DB driver error, reinstall backend dependencies:

```powershell
.\.venv\Scripts\python -m pip install -r backend\requirements.txt
```

If Upload Preview reports `partial_failed` with `risky/db_unreachable`, check:

- `EWC_SUPABASE_DB_URL` is set for the backend process.
- Local Supabase is running and its Postgres port is reachable. For the independent web-console stack, the default DB TCP port is `127.0.0.1:25433` from `supabase/config.toml`.
- The local database contains `public.all_metrics` with the existing `timestamp, device_id` uniqueness policy.

This failure state is expected when the DB cannot be checked. The app should show the risk in the UI instead of treating files as upload targets.
