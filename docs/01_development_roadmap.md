# Development Roadmap

## 1. Create The Project Baseline

- Keep this repository separate from `Extrusion_data`.
- Treat the legacy repository as the behavior reference and fallback.
- Store product scope in `docs/00_product_scope.md`.
- Store project rules in `AGENTS.md`.

## 2. Run Engineering Review Before Coding

Before implementation, ask Codex:

```text
docs/00_product_scope.md and AGENTS.md are the source of truth.
Use plan-eng-review to define the technical architecture, APIs, data flow, job execution model, audit log design, test strategy, and migration constraints for this new web project.
Use C:\Users\user\Documents\GitHub\Extrusion_data as the reference project.
```

The engineering review must decide:

- backend framework
- frontend framework
- project directory structure
- config storage
- upload job state model
- log streaming mechanism
- audit log storage
- local Supabase start/stop mechanism
- launcher/packaging strategy
- exact legacy code extraction strategy

## 3. Scaffold The Application

Create a runnable empty skeleton first:

```text
backend/
frontend/
launcher/
supabase/
grafana/
docs/
tests/
```

Do not port business logic until the skeleton can start and show a health page.

Status on branch `codex/web-console-scaffold`:

- Done: FastAPI backend scaffold with `/api/health`, `/api/dashboard`, and `/api/dashboard/summary`.
- Done: React + Vite + TypeScript frontend scaffold.
- Done: Dashboard Variant D mock UI with `ready`, `attention`, `blocked`, and `running` mock states.
- Done: Sidebar navigation limited to Dashboard, Upload, Logs, Settings.
- Done: Upload, Logs, and Settings placeholder pages.
- Done: Korean/English i18n baseline with persisted language selection.
- Done: backend tests for health and Dashboard mock API contracts.
- Verified: frontend typecheck/build, backend tests, browser QA at `1440x900`, `1366x768`, `1024x768`, and `720x900`.
- Not done: real upload jobs and real Supabase runtime control.

Status on branch `codex/upload-preview-reconciliation`:

- Done: Upload Preview backend API.
- Done: SQLite `preview_runs` and `preview_items` persistence for preview results.
- Done: local CSV candidate scanning for configured source folders.
- Done: row-streamed `(timestamp, device_id)` key extraction with chunked exact-key DB matching.
- Done: exact Supabase reconciliation when `EWC_SUPABASE_DB_URL` is configured.
- Done: DB unreachable path persists run `partial_failed` and item `risky/db_unreachable`.
- Done: Upload page Preview UI with status summary, table, filters, polling, mock data, and Korean/English i18n.
- Done on branch `codex/upload-job-sse`: Upload Job API, retry failed API, pause/resume/cancel API, SQLite upload job/file/file-state/event/audit persistence, Start Upload from completed Preview targets, SSE event replay, and Upload Job tab UI.
- Done on branch `codex/local-supabase-control-impl`: Local Supabase status/start/stop API, required-container existence precheck, non-destructive command allowlist, runtime operation/event persistence, mutating-operation audit logging, Dashboard runtime module API connection, and Settings runtime config/source display.
- Done on branch `codex/audit-logs-ui-impl`: `GET /api/audit`, append-only audit triggers, redacted audit query API, safe scalar `q` search, and Logs page Job Logs/Audit Logs tabs with filters, pagination, loading/empty/error states, and Korean/English i18n.
- Done on branch `codex/settings-save-audit-writer`: `GET /api/config`, `PUT /api/config`, config JSON loading into `Settings`, env/process precedence over config JSON, and `settings.save` success/failure/blocked audit writer coverage.
- Done on branch `codex/settings-save-ui`: Settings save UI connected to `GET /api/config` and `PUT /api/config`, editable fields, env/process override disabled state, repo `.env` override backend blocking, secret placeholder replacement behavior, dirty state, Save/Reset, validation feedback, save status, and screenshot QA coverage.
- Done on branch `codex/upload-preview-audit-writer`: `upload.preview` audit writer coverage for preview success, DB unreachable, missing source, malformed JSON, validation failure, and active preview conflict paths.
- Done on branch `codex/upload-edge-accepted-rows-ui-api`: Upload Job API/UI now exposes `acceptedRows` as the canonical Edge/Supabase upsert-accepted row count, keeps `insertedRows` as a deprecated v1 compatibility alias, preserves the existing SQLite `inserted_rows` storage without migration, adds `acceptedRows` to job event/SSE payloads, and removes operator-facing inserted-row wording including the Korean Preview status label `DB 적재됨`.
- Verified: backend tests, frontend typecheck/build, and browser QA for Audit Logs UI/API, Vite proxy `/api/audit`, Dashboard/Upload/Settings regression, and responsive Logs viewports.
- Verified: PR #8 targeted/full backend tests, frontend typecheck/build, direct config API smoke, and Settings/Dashboard/Upload/Logs browser smoke. Vite proxy `/api/config` was not fully verified against the PR head because an older uvicorn process occupied port `8000`.
- Verified: PR #9 review approved and QA passed twice with targeted preview/audit backend tests, full backend tests, frontend typecheck/build, `git diff --check`, direct Upload Preview API smoke, and Vite/backend HTTP smoke. Browser screenshot QA was not completed because `node_repl` failed with a kernel asset path error.
- Verified: PR #19 review approved and QA passed with targeted upload job backend tests, full backend tests, API/SSE smoke, frontend typecheck/build, `git diff --check`, Vite/backend HTTP smoke, and source/build wording checks for inserted-row terminology. Browser screenshot QA was not completed because `node_repl` failed with a kernel asset path error and local Playwright was not installed.
- Done on branch `codex/launcher-integration-impl`: Launcher phase 1, FastAPI static frontend serving for built `frontend/dist`, `/api/*` precedence before SPA fallback, Windows `launcher/start_web_console.ps1` and `.bat`, `127.0.0.1` backend bind, `-CheckOnly`, explicit `-BuildFrontend`, clear missing-build `503`, port conflict handling, browser open, and documented launcher logs.
- Verified: PR #26 review approved and QA passed with targeted launcher/static backend tests, full backend tests, frontend typecheck/build, screenshot QA, launcher `-CheckOnly`, launcher `-BuildFrontend -CheckOnly`, port conflict smoke, backend-origin HTTP smoke for `/`, `/upload`, `/logs`, `/settings`, `/api/health`, `/api/audit?action=settings.save&limit=1`, and missing frontend `503` smoke.

## 4. Build Backend Core Ops

Implement backend capabilities in this order:

1. config read/write
2. audit log append/query
3. local Supabase status
4. Grafana status/link
5. upload preview
6. upload start/retry
7. progress and log streaming
8. launcher integration

Current implementation note: mock Dashboard aggregation endpoints, Upload Preview APIs, Upload Job APIs, Local Supabase runtime control APIs, Config APIs, Audit Logs query APIs, and launcher phase 1 exist. `PUT /api/config` writes only allowed config keys to config JSON, blocks env-overridden keys, records `settings.save` success/failure/blocked audit rows, and keeps raw values, secrets, DB URLs, tokens, anon keys, service role values, and malformed request bodies out of audit params. `POST /api/upload/preview` records `upload.preview` success/failure/blocked audit rows with safe metadata only, including `previewRunId`, counts, `dbStatus`, `reasonCode`, and `requestedFilters`; it does not store raw file paths, filenames, DB URLs, tokens, anon keys, service role values, secrets, or malformed raw bodies in audit params. Upload Job responses and job events use `acceptedRows` for Edge/Supabase upsert-accepted row counts and retain `insertedRows` only as a deprecated compatibility alias; `acceptedRows` is not a net-new insert count, so duplicate-safe reruns can have DB row count delta `0` while `acceptedRows` is positive. Audit Logs query search is limited to safe scalar columns and does not search raw `error_message` or raw params JSON. FastAPI serves built frontend routes in operator mode while preserving `/api/*` route precedence.

## 5. Build Frontend Core Ops

Implement frontend screens in this order:

1. Dashboard
2. Settings
3. Upload
4. Logs

The UI should be operational and dense, not marketing-oriented.

Current implementation note: Dashboard mock UI, Upload Preview UI, Upload Job tab, Settings save UI, and Logs page Job Logs/Audit Logs tabs are implemented. Upload Job UI displays accepted/upserted row counts as `Accepted` / `수락`, and Upload Preview Korean `already_in_db` now reads `DB에 있음` to avoid net-new insert wording. Settings uses `GET /api/config` and `PUT /api/config` in API mode, disables env/process and repo `.env` overridden fields, excludes empty/unchanged secret placeholders from save payloads, sends secret keys only when the operator types a replacement value, and refetches after save. Audit Logs includes table filters, pagination, loading/empty/error states, redacted params display, sanitized error messages, and Korean/English labels. Job Logs remains a lightweight shell over existing upload job events.

## 6. Validate Against Legacy Behavior

Compare the new app against the legacy GUI for:

- candidate file detection
- preview exclusion reasons
- upload batching
- Smart Sync filtering
- failure reporting
- local Supabase readiness
- settings precedence where retained

Status:

- Automated foundation complete on `main` commit `5695b93802f78f2e04a1aa83662e9400e1d49db2`: Upload Preview uses legacy scanning/transform behavior as reference, tests exact-key reconciliation and DB-status semantics, covers representative UTF-8/CP949 legacy and integrated CSV fixtures, runs a deterministic 25,000-row synthetic Preview soak, and queries representative failure/blocked evidence through the Audit Logs API.
- Post-merge operator-PC evidence complete for the separately approved Preview-only scope: one `folder_all` large-source Preview (`prv_ca38650a9e7d`) persisted local run/audit state and succeeded without operational DB mutation, with DB reachable, 12 files classified, `target=0`, `risky=0`, 64,766 partial-overlap rows excluded from target-only upload, and Start Upload disabled. Later read-only Audit/Job/config/runtime observations and Core Ops route QA also passed.
- `docs/182` now binds a freshly assembled package artifact from `d16b822d4a461fc7705c5aca9cebd40cb19fe918` to human-confirmed read-only inventory baseline evidence. It does not prove that package is installed or executing, does not retroactively validate the earlier Preview, and does not approve Preview.
- Still required before any cutover can proceed: verify the exact executing package; repeat the read-only inventory immediately before approval; create an execution-adjacent successor record with human-supplied operator-PC and privacy-safe exact-source bindings; complete a separately approved fresh Preview chain; record any required partial-overlap disposition and final release-owner/operator sign-off; and resolve or explicitly accept the current non-core Grafana/Vector attention with an owner and stop/rollback procedure. Local Supabase start/stop remains separately approved operational evidence only when a cutover actually requires lifecycle control.

## 7. Package And Transition

Create a double-click launcher only after backend/frontend flows are stable.

Transition from the legacy GUI only after:

- Core Ops feature parity is verified
- audit logs are working
- duplicate risk preview is working
- upload behavior is tested with representative CSV files
- README run instructions are accurate

Current transition status: `NO-GO` for cutover execution; `CONDITIONAL GO` candidate after the hard gates above are satisfied. Core Ops implementation, representative legacy CSV automation, synthetic soak, the separately approved operator-PC Preview-only run, later read-only UI/log observations, and the package/inventory baseline record in `docs/182` are complete for their stated scopes. The earlier Preview had zero target-only rows, so Start Upload and Retry Failed were not applicable and were not executed, but it predates `docs/182` and its 64,766 partial-overlap rows still require human disposition if that evidence is used. Exact executing-package verification, an execution-adjacent successor inventory record, a separately approved current Preview, final sign-off, and Grafana/Vector risk ownership prevent a current proceed decision.
