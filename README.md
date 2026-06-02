# Extrusion Web Console

Local web operations console for extrusion data upload and local Supabase operations.

This project replaces the legacy Tkinter GUI in `C:\Users\user\Documents\GitHub\Extrusion_data`.

## Current Status

The first runnable scaffold is in place:

- FastAPI backend with `/api/health`, mock `/api/dashboard`, and mock `/api/dashboard/summary`.
- Upload Preview reconciliation API with persisted preview runs/items:
  - `POST /api/upload/preview`
  - `GET /api/upload/preview/latest`
  - `GET /api/upload/preview/{previewRunId}`
  - `POST /api/upload/preview/{previewRunId}/cancel`
- React + Vite + TypeScript frontend.
- Dashboard Variant D mock UI using design tokens from `docs/04_design_system.md`.
- Upload Preview UI with Preview/Job tabs, status summary, polling, filters, and the five preview states.
- Upload Job API/UI with Start Upload, Retry Failed, pause/resume/cancel, SQLite job/file/event state, and SSE event replay.
- TanStack Query mock-first Dashboard query.
- Korean/English i18n baseline with language persistence in `localStorage`.
- Mock Dashboard state switching with `?state=ready|attention|blocked|running`.
- Logs and Settings are placeholder pages only.

Local Supabase control, full Logs/Audit pages, launcher integration, and legacy upload state import are not implemented in this scaffold.

Upload Preview v1 scans configured local CSV folders, extracts exact `(timestamp, device_id)` keys, persists preview results in SQLite, and compares those keys with local Supabase when `EWC_SUPABASE_DB_URL` is configured. If the DB URL is missing or unreachable, DB-dependent files are shown as `risky/db_unreachable`; they are not silently treated as upload targets.

The Dashboard scaffold has been browser-QA'd at `1440x900`, `1366x768`, `1024x768`, and `720x900`.

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

Local Supabase, WSL, Docker, and Grafana are not required for the mock Dashboard and mock Upload Preview paths. Local Supabase is required only when testing real reachable Upload Preview reconciliation against `all_metrics`.

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

Upload Preview configuration is read from environment-backed settings:

```powershell
$env:EWC_PLC_DATA_DIR="C:\path\to\plc_csv"
$env:EWC_SUPABASE_DB_URL="postgresql://postgres:postgres@127.0.0.1:54322/postgres"
$env:EWC_SUPABASE_URL="http://127.0.0.1:54321"
$env:EWC_SUPABASE_ANON_KEY="<local anon key>"
$env:EWC_SUPABASE_EDGE_URL="http://127.0.0.1:54321/functions/v1/upload-metrics"
$env:EWC_STATE_DB_PATH="C:\tmp\ExtrusionWebConsole\web_console_state.db"
```

`EWC_SUPABASE_DB_URL` is optional for mock UI/dev smoke checks. It is required for real Upload Preview exact reconciliation. Without it, or when the local Supabase DB is unreachable, preview runs still persist and DB-dependent CSV candidates are shown as `risky/db_unreachable` under a `partial_failed` run.

`EWC_SUPABASE_ANON_KEY` and either `EWC_SUPABASE_EDGE_URL` or `EWC_SUPABASE_URL` are required for real Start Upload and Retry Failed execution. Preview-origin upload disables the legacy latest-timestamp Smart Sync filter and relies on the existing `all_metrics(timestamp, device_id)` upsert safety for final duplicate protection.

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
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

By default the frontend uses local mock data. To fetch the backend mock endpoint instead:

```powershell
$env:VITE_API_MODE="api"
npm run dev
```

The Vite dev server proxies `/api` to `http://127.0.0.1:8000`.

Important scaffold limitation: `?state=ready|attention|blocked|running` is implemented in the frontend mock data path. When `VITE_API_MODE="api"` is used, the backend mock currently returns the running Dashboard payload.

The Upload Preview page also uses mock data by default so all five preview states can be inspected without local Supabase. To use the real backend preview API, run the frontend with `VITE_API_MODE="api"` and configure the backend environment values above.

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
- Start Upload is enabled only for a succeeded preview with reachable DB and `target` rows.
- Start Upload excludes `already_in_db`, `partial_overlap`, `risky`, and `excluded` rows by default.
- Upload Job tab shows file progress, pause/resume/cancel controls, Retry Failed, and live/persisted events.

Browser QA has been run against:

- `http://127.0.0.1:5173/?state=ready`
- `http://127.0.0.1:5173/?state=attention`
- `http://127.0.0.1:5173/?state=blocked`
- `http://127.0.0.1:5173/?state=running`
- Upload Preview plus Logs and Settings placeholders through sidebar navigation.

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

Out of scope for this scaffold:

- Actual Supabase start/stop
- Actual local Supabase status probing
- Full legacy core extraction
- Full Logs/Audit pages
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
- Local Supabase is running and its Postgres port is reachable, usually `127.0.0.1:54322`.
- The local database contains `public.all_metrics` with the existing `timestamp, device_id` uniqueness policy.

This failure state is expected when the DB cannot be checked. The app should show the risk in the UI instead of treating files as upload targets.
