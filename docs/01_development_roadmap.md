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
- Not done: real upload jobs, real Supabase runtime control, launcher integration.

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
- Verified: backend tests, frontend typecheck/build, and browser QA for Audit Logs UI/API, Vite proxy `/api/audit`, Dashboard/Upload/Settings regression, and responsive Logs viewports.
- Not done: launcher integration.

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

Current implementation note: mock Dashboard aggregation endpoints, Upload Preview APIs, Upload Job APIs, Local Supabase runtime control APIs, and Audit Logs query APIs exist. Audit Logs query search is limited to safe scalar columns and does not search raw `error_message` or raw params JSON. Config write and launcher APIs remain future work.

## 5. Build Frontend Core Ops

Implement frontend screens in this order:

1. Dashboard
2. Settings
3. Upload
4. Logs

The UI should be operational and dense, not marketing-oriented.

Current implementation note: Dashboard mock UI, Upload Preview UI, Upload Job tab, Settings runtime config/source display, and Logs page Job Logs/Audit Logs tabs are implemented. Audit Logs includes table filters, pagination, loading/empty/error states, redacted params display, sanitized error messages, and Korean/English labels. Job Logs remains a lightweight shell over existing upload job events.

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

- Partially started: Upload Preview now uses legacy scanning/transform behavior as reference and tests exact-key reconciliation.
- Still required: broader legacy CSV fixture coverage, local Supabase control E2E on the operator PC, and final operator validation of failure reporting across Audit Logs.

## 7. Package And Transition

Create a double-click launcher only after backend/frontend flows are stable.

Transition from the legacy GUI only after:

- Core Ops feature parity is verified
- audit logs are working
- duplicate risk preview is working
- upload behavior is tested with representative CSV files
- README run instructions are accurate

Current transition status: blocked. Duplicate-risk preview, real upload jobs, progress/event streaming, Local Supabase controls, and Audit Logs are implemented, but legacy GUI replacement still requires launcher integration, broader runtime E2E, and final operator workflow validation.
