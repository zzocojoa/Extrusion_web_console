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
- TanStack Query mock-first Dashboard query.
- Korean/English i18n baseline with language persistence in `localStorage`.
- Mock Dashboard state switching with `?state=ready|attention|blocked|running`.
- Logs and Settings are placeholder pages only.

No real upload job, Supabase control, or legacy upload state import is implemented in this scaffold.

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

Local Supabase, WSL, Docker, and Grafana are not required for this mock Dashboard scaffold.

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
$env:EWC_STATE_DB_PATH="C:\tmp\ExtrusionWebConsole\web_console_state.db"
```

`EWC_SUPABASE_DB_URL` is optional for UI/dev smoke checks. Without it, preview runs still persist and show DB-dependent CSV candidates as risky.

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
- Start Upload is present but disabled because actual upload job execution is not implemented in this phase.

Browser QA has been run against:

- `http://127.0.0.1:5173/?state=ready`
- `http://127.0.0.1:5173/?state=attention`
- `http://127.0.0.1:5173/?state=blocked`
- `http://127.0.0.1:5173/?state=running`
- Upload, Logs, and Settings placeholders through sidebar navigation.

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

- Actual upload job execution
- Actual Supabase start/stop
- Actual local Supabase status probing
- Full legacy core extraction
- SSE progress/log streaming
- Audit log persistence
- Data Mgmt
- Cycle Ops
- Training Dataset Builder
- Grafana iframe
- Cloud or multi-user web access
