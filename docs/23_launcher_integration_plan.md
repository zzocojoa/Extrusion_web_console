# Launcher Integration Plan

Status: phase 1 implemented on branch `codex/launcher-integration-impl`

Date: 2026-06-06

Scope: Windows launcher integration for the local operator web console.

Implementation result on branch `codex/launcher-integration-impl`:

- Added FastAPI static frontend serving for built `frontend/dist`.
- API routes under `/api/*` keep precedence over static and SPA fallback routes.
- `/`, `/upload`, `/logs`, and `/settings` return the built frontend shell when `frontend/dist/index.html` exists.
- Missing built frontend returns an operator-facing `503` message instead of silently serving a blank app.
- Added `launcher/start_web_console.ps1` and `launcher/start_web_console.bat`.
- The launcher starts Uvicorn with `backend.app.main:app` on `127.0.0.1` only, using the project virtualenv Python.
- The launcher waits for `/api/health`, opens the loopback browser URL, writes launcher/backend logs under `%APPDATA%\ExtrusionWebConsole\logs\launcher\`, and stops only its own backend child process on normal shutdown.
- The launcher reuses an already healthy Extrusion Web Console backend on the selected port and blocks unknown port occupants without killing them.
- The launcher does not run frontend build in the default double-click operator flow; `npm run build` is available only through the explicit `-BuildFrontend` developer flag.
- The explicit `-BuildFrontend` path fails clearly when `npm run build` exits non-zero or does not produce `frontend/dist/index.html`.
- Phase 1 does not add API token enforcement. Local token remains phase 2.
- Phase 1 does not run local Supabase bootstrap, reset, cleanup, prune, Docker create/delete, volume operations, or arbitrary command input.
- QA passed: targeted launcher/static tests 7 passed, full backend tests 141 passed, frontend typecheck/build/`qa:screenshots` passed, launcher `-CheckOnly` passed, launcher `-BuildFrontend -CheckOnly` passed, port conflict smoke passed, backend-origin HTTP smoke passed, and missing frontend `503` smoke passed.

Source documents:

- `AGENTS.md`
- `README.md`
- `docs/01_development_roadmap.md`
- `docs/02_engineering_plan.md`
- `docs/09_local_supabase_control_plan.md`
- `docs/10_audit_logs_plan.md`
- `docs/21_browser_screenshot_tooling_plan.md`
- `docs/22_settings_save_ui_operator_smoke.md`

## Goal

Give a non-developer operator a double-click path to run Extrusion Web Console on the operator PC without weakening the existing safety rules.

The launcher is the transition layer between the current developer commands and the eventual local product experience. It should make the app easy to start, make missing prerequisites obvious, keep secrets out of console/log output, and preserve the existing localhost-only, non-destructive runtime policy.

## Decisions

1. Add launcher files under `launcher/`.
   - Primary script: `launcher/start_web_console.ps1`
   - Double-click wrapper: `launcher/start_web_console.bat`
   - Optional stop helper can be added later only if it terminates launcher-owned processes by PID file.

2. Operator mode runs one backend process on `127.0.0.1`.
   - Backend command: project venv Python runs Uvicorn with `backend.app.main:app`.
   - Host must be `127.0.0.1`.
   - Default backend port remains `8000`.
   - The launcher must fail if the process would bind to `0.0.0.0` or a non-loopback address.

3. Operator mode serves the built frontend through FastAPI.
   - Build output: `frontend/dist`.
   - Backend adds static serving for `frontend/dist` in the implementation PR.
   - Browser opens the backend origin, for example `http://127.0.0.1:<backendPort>/`.
   - This avoids a second operator-facing Vite process and removes Vite proxy ambiguity.

4. Dev mode remains separate.
   - Existing developer flow stays: backend on `127.0.0.1:8000`, Vite on `127.0.0.1:5173`, `VITE_API_MODE=api`.
   - Phase 1 launcher does not implement `-Mode dev`.
   - If launcher dev mode is added later, it may start Vite only through `npm run dev` from `frontend/`.

5. Local Supabase is not bootstrapped by the launcher.
   - Launcher may check runtime reachability through app APIs after backend starts.
   - Launcher must not run Supabase init, bootstrap, db reset, Docker create/remove, compose up/down, prune, cleanup, or volume operations.
   - Starting/stopping existing local Supabase remains inside the web console runtime API and existing allowlist policy from `docs/09_local_supabase_control_plan.md`.
   - Default launcher behavior is status-only for local Supabase.

6. Config precedence stays unchanged.
   - Effective precedence remains:

```text
built-in defaults
< config JSON
< repo .env / launcher env
< process environment
```

   - The launcher may set only process env needed for its own run, such as host, port, config path, state DB path, and operator mode flags.
   - Launcher env overrides must be displayed read-only in Settings and remain blocked from config JSON writes.
   - Settings save UI continues to write only config JSON through `PUT /api/config`.

7. Secrets are presence-only in launcher diagnostics.
   - The launcher must never print DB URLs, anon keys, service role values, tokens, Authorization headers, or secret replacement values.
   - Readiness output may say `present` or `missing`.
   - Logs must redact credential-like strings before writing.

8. Port collision handling is explicit.
   - If backend port is free, start normally.
   - If the port is occupied by an already healthy Extrusion Web Console backend, open the browser and report reuse.
   - If the port is occupied by another process or stale backend, stop and show a clear message.
   - Do not kill unknown processes automatically.
   - Do not silently choose a random port in operator mode. Operator docs and Settings links must stay predictable.

9. Working directory is fixed.
   - The PowerShell script resolves the repository root from its own location.
   - All commands run from fixed known directories.
   - No user-supplied arbitrary command or arbitrary path is executed.

10. Browser open is best-effort and safe.
    - Open only a loopback URL created by the launcher.
    - Prefer PowerShell `Start-Process` with the local URL.
    - If browser open fails, keep backend running and print the local URL.

## Runtime Flow

```text
Operator double-clicks .bat
  -> .bat invokes PowerShell script in launcher/
  -> script resolves repo root
  -> script verifies allowed prerequisites
       Python venv
       backend dependencies
       frontend/dist exists
       backend port ownership
       config/state path directories
  -> script starts backend on 127.0.0.1
  -> script waits for GET /api/health
  -> script opens browser to backend origin
  -> operator uses Dashboard / Upload / Logs / Settings
  -> Ctrl+C or window close stops launcher-owned backend
```

Operator mode request path:

```text
Browser
  -> http://127.0.0.1:<backendPort>/
  -> FastAPI static frontend
  -> frontend calls same-origin /api/*
  -> FastAPI API routers
  -> SQLite state/config/audit
  -> local Supabase only through existing runtime/upload APIs
```

Dev mode request path:

```text
Browser
  -> http://127.0.0.1:5173/
  -> Vite dev server
  -> /api proxy to http://127.0.0.1:8000
  -> FastAPI API routers
```

## Launcher Files

### `launcher/start_web_console.ps1`

Responsibilities:

- Resolve repo root.
- Enforce loopback host.
- Read optional non-secret launcher parameters.
- Verify `.venv` Python exists.
- Verify `frontend/dist` exists for operator mode.
- Create app data/log directories if missing.
- Check backend port.
- Start backend with bounded, allowlisted arguments.
- Wait for `/api/health`.
- Open browser.
- Write redacted launcher logs.
- Stop only launcher-owned child process on normal exit.

Implemented parameters:

```powershell
param(
  [ValidateRange(1024, 65535)]
  [int]$BackendPort = 8000,
  [switch]$NoBrowser,
  [switch]$BuildFrontend,
  [switch]$CheckOnly
)
```

### `launcher/start_web_console.bat`

Responsibilities:

- Double-click entry point.
- Invoke PowerShell with execution policy scoped to this process.
- Keep the window open when startup fails so a non-developer can read the reason.
- Pass no secrets on the command line.

## Command Allowlist

Launcher commands are fixed and local. No user-supplied command strings.

Allowed commands:

```text
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port <allowed-port>
npm run build
Start-Process http://127.0.0.1:<allowed-port>/
Invoke-RestMethod http://127.0.0.1:<allowed-port>/api/health
```

Allowed only when explicitly requested by a developer flag:

```text
npm run build
```

Forbidden commands:

```text
supabase init
supabase db reset
supabase stop
docker run
docker create
docker rm
docker rmi
docker volume
docker network rm
docker prune
docker system prune
docker compose up
docker compose down
docker compose rm
any command containing shell fragments from user input
any DB reset/delete/cleanup/prune command
```

The launcher must not be a generic shell wrapper.

## Backend Static Serving

Phase 1 adds static frontend serving to FastAPI:

- API routes stay under `/api/*`.
- Static assets are served from `frontend/dist/assets`.
- SPA fallback returns `frontend/dist/index.html` for non-API routes.
- If `frontend/dist` is missing in operator mode, backend should expose a clear startup or root error, but the launcher should catch this before start.
- OpenAPI remains under `/api/openapi.json`.

Recommended implementation shape:

```text
backend/app/main.py
  include API routers first
  mount assets if frontend/dist exists
  add catch-all route after API routers
```

Do not serve source files, `.env`, `.gstack`, tests, or operational fixtures.

## Local Token Decision

Do not add mandatory token auth in the first launcher implementation PR.

Reason:

- Backend already enforces loopback clients.
- Mutating APIs and Settings have been tested under loopback assumptions.
- Adding token enforcement now would touch every frontend API call and many backend tests.

Phase 2 is now implemented on branch `codex/launcher-local-token-impl`:

- Launcher generates a per-run random token.
- Launcher passes it to backend through process env.
- Backend requires it for mutating APIs.
- Frontend receives it through runtime HTML bootstrap from the same backend origin.
- Audit params record token presence only, never token value.
- Missing/invalid token attempts return `403 local_token_required` and are rate-limited in audit.
- Read-only APIs remain token-free. Operator launcher mode disables `/api/docs`, `/api/openapi.json`, and ReDoc-style documentation routes by route configuration instead of token-gating them. `OPTIONS` is not blocked by the token guard, although normal route method handling can still return non-success responses.
- Developers using Vite should set `EWC_LOCAL_TOKEN_MODE=dev-disabled` unless they intentionally wire a test token path.

Phase 1 must still reserve the design:

- Do not design any API or static serving path that would make per-run token injection impossible later.
- Do not put tokens in URL query strings.
- Do not print token values in launcher logs.

## Env And Config Precedence

Launcher must respect current Settings behavior.

```text
built-in defaults
< %APPDATA% config JSON
< repo .env / launcher env
< process environment
```

Implications:

- If launcher sets `EWC_HOST` or `EWC_PORT`, Settings should show process/env source and disabled state where applicable.
- If operator edits a config JSON field through Settings, it affects later launcher runs unless overridden by `.env` or process env.
- If `.env` contains a key, Settings save attempts for that key remain backend-blocked and audit logged as `settings.save` blocked/failure according to current API behavior.
- Launcher documentation must teach presence-only checks, not secret value sharing.

## Logs

Launcher log location:

```text
%APPDATA%\ExtrusionWebConsole\logs\launcher\
```

Recommended files:

```text
launcher-YYYYMMDD-HHMMSS.log
backend-YYYYMMDD-HHMMSS.log
launcher-latest.log
backend-latest.log
```

Rules:

- Redact credential-like strings before writing.
- Do not write request or response bodies from config, upload, audit, or Edge calls.
- Record command names and sanitized status only.
- Record PID of launcher-owned backend process.
- Show the log path in the console.

## Shutdown And Cleanup

Normal shutdown:

- Ctrl+C or closing the launcher console stops only the backend process started by the launcher.
- Do not stop Docker Desktop, WSL, local Supabase, Grafana, or unknown processes.
- Do not delete state DB, config JSON, logs, screenshots, or operational fixtures.

Stale process handling:

- If a PID file points to a non-running process, remove only the PID file.
- If a PID file points to a running process and `/api/health` matches this app, reuse or ask the operator to close the existing window.
- If the port is occupied by an unknown process, stop and show the port conflict.

## Failure Modes

| Failure | Detection | Operator message | Safe behavior |
| --- | --- | --- | --- |
| Python venv missing | `.venv\Scripts\python.exe` absent | Backend environment is not installed | Stop, show setup step |
| Dependencies missing | backend import or health fails | Backend package install is incomplete | Stop, show log path |
| Frontend build missing | `frontend/dist/index.html` absent | Frontend build is missing | Stop or run build only with explicit flag |
| Backend port free | TCP probe | Ready to start | Start backend |
| Backend port used by same app | `/api/health` succeeds | Existing console is already running | Open browser, do not start duplicate |
| Backend port used by other app | health missing or wrong | Port is in use by another process | Stop, do not kill process |
| Health timeout | `/api/health` not ready | Backend did not become ready | Stop launcher-owned process |
| Browser open failure | `Start-Process` failure | Browser did not open automatically | Print URL |
| Local Supabase unavailable | runtime API status | Local Supabase is not ready | App shows Dashboard status, launcher does not repair |
| Secret-like output detected | redaction scan | Sensitive output was redacted | Write redacted log only |
| Non-loopback host requested | parameter validation | Only localhost is allowed | Stop before command execution |

No failure path should be silent. Each path needs a console message and redacted log entry.

## Tests And QA Result

Backend tests:

- Static frontend serving returns `index.html` for `/`.
- Static serving never captures `/api/*` routes.
- Missing `frontend/dist` behavior is explicit.
- Loopback middleware still rejects non-loopback clients.
- CORS remains limited to local dev origins.

Launcher tests:

- PowerShell parser accepts default operator mode.
- Non-loopback host is rejected.
- Known healthy backend is reused.
- Unknown port occupant blocks startup.
- Missing venv blocks startup with clear message.
- Missing frontend build blocks startup unless explicit build flag is used.
- Redaction masks DB URL-like strings, bearer tokens, JWT-like strings, anon/service-role-like labels, and Windows absolute paths in logs.
- Launcher stops only its child backend process.
- Forbidden commands are not present in launcher scripts.

Frontend/browser checks:

- `npm run qa:screenshots` still passes in mock mode.
- Operator mode browser smoke loads `/`, `/upload`, `/logs`, and `/settings` from backend origin.
- Settings page uses same-origin `/api/config`.
- Audit Logs can query `settings.save` from same-origin API.
- 720px viewport does not break the launcher-served app.

Validation result for PR #26:

- Targeted launcher/static backend tests: 7 passed.
- Full backend tests with clean config/env: 141 passed.
- `npm run typecheck`: passed.
- `npm run build`: passed.
- `npm run qa:screenshots`: passed.
- Launcher `-CheckOnly`: passed.
- Launcher `-BuildFrontend -CheckOnly`: passed.
- Port conflict smoke: passed.
- Backend-origin HTTP smoke for `/`, `/upload`, `/logs`, `/settings`, `/api/health`, `/api/audit?action=settings.save&limit=1`, and unknown `/api/*`: passed.
- Missing frontend `503` smoke: passed.
- `git diff --check`: passed.

Validation result for API docs operator hardening on PR #30:

- Targeted route/token/OpenAPI backend tests: 33 passed.
- Full backend tests with clean config/env: 153 passed.
- `npm run typecheck`: passed.
- `npm run build`: passed.
- `npm run qa:screenshots`: passed.
- Launcher `-CheckOnly`: passed and reports API docs disabled policy without printing token values.
- Operator HTTP smoke: `/api/docs`, `/api/openapi.json`, and `/api/redoc` returned `404`; `/api/health`, `/`, `/upload`, `/logs`, and `/settings` returned `200`.
- Dev/docs-enabled HTTP smoke with `EWC_API_DOCS_MODE=enabled`: `/api/docs`, `/api/openapi.json`, and `/api/health` returned `200`.
- Generated `.gstack` artifacts, `frontend/dist`, and the untracked operational CSV fixture were not committed.

Validation commands:

```powershell
.\.venv\Scripts\python -m pytest tests\backend
cd frontend
npm run typecheck
npm run build
npm run qa:screenshots
git diff --check
```

## Implementation Order And Status

1. Done: add backend static serving for `frontend/dist` with API route precedence.
2. Done: add tests for static serving, SPA fallback, and API route preservation.
3. Done: add `launcher/start_web_console.ps1` with operator mode.
4. Done: add redacted launcher logging and backend child-process handling.
5. Done: add `launcher/start_web_console.bat` double-click wrapper.
6. Done: add launcher tests for command policy, build handling, and redaction.
7. Done: update README with non-developer launcher instructions.
8. Done: run backend tests, frontend typecheck/build, screenshot QA, and operator mode smoke.
9. Deferred: dev mode support, if needed, after operator mode is stable.
10. Done: phase 2 local token enforcement for mutating localhost APIs.
11. Done: operator-mode API docs hardening with dev/test docs-enabled override.

## What Already Exists

| Existing piece | Reuse decision |
| --- | --- |
| FastAPI app and loopback client middleware | Reuse. Launcher must bind backend to `127.0.0.1`. |
| `GET /api/health` | Reuse as launcher readiness probe. |
| `GET /api/config` and `PUT /api/config` | Reuse. Launcher must not bypass Settings save policy. |
| Settings source metadata and override blocking | Reuse. Launcher env should appear as env/process source. |
| Local Supabase runtime API | Reuse for in-app status/start/stop. Launcher stays status-only by default. |
| Audit Logs API/UI | Reuse for operator evidence after app starts. |
| Playwright screenshot QA | Reuse for launcher-served browser smoke after static serving exists. |
| Vite dev server | Keep for developer mode, not default operator mode. |

## Worktree Parallelization

Phase 1 implementation is complete. The original lane split was:

| Step | Modules touched | Depends on |
| --- | --- | --- |
| Static serving | `backend/`, `tests/backend/` | none |
| Launcher scripts | `launcher/`, `tests/` | static serving health target |
| README/operator docs | `README.md`, `docs/` | static serving and launcher decisions |
| Browser QA update | `frontend/qa/`, `.gstack` artifacts ignored | static serving |

Parallel lanes:

- Lane A: backend static serving and backend tests.
- Lane B: launcher scripts and launcher tests, starts after Lane A defines the final backend origin.
- Lane C: docs and operator instructions, can run after Lane A decisions are stable.
- Lane D: browser QA update, starts after Lane A.

Execution order completed Lane A first, then launcher scripts, docs, and browser QA.

Conflict flags: Lane C and Lane D may both mention screenshot QA paths, coordinate README wording.

## NOT In Scope

- Production deploy. The app remains local operator PC software.
- Cloud Supabase migration.
- Multi-user LAN access.
- Docker Desktop installation or WSL installation.
- Supabase bootstrap, init, DB reset, cleanup, prune, or container/volume creation.
- Automatic upload of operational CSV data.
- Service installation as a Windows background service.
- Tray app, installer, code signing, MSI packaging, or auto-update.
- Mandatory local token auth in phase 1. Phase 2 implements it separately and keeps phase 1 rollback boundaries clear.
- Arbitrary command runner UI.
- Data Mgmt archive/delete flows.

## Acceptance Criteria

- Non-developer can double-click `launcher/start_web_console.bat`.
- Backend binds only to `127.0.0.1`.
- Browser opens to the app without requiring Vite.
- `/api/health`, `/api/config`, `/api/audit`, Upload, Logs, and Settings work from the backend origin.
- Port conflict messages distinguish same-app reuse from unknown process conflict.
- Launcher logs are written to a documented local path and redact secrets/paths.
- Phase 2 launcher token values stay out of URL queries, launcher logs, backend logs, audit params, screenshots, generated `.gstack` artifacts, and `frontend/dist`.
- Launcher does not start, stop, reset, prune, create, delete, or bootstrap Docker/Supabase resources.
- Settings save UI still writes config JSON through the API and respects env/process override blocking.
- Generated `.gstack` artifacts and operational CSV fixtures remain uncommitted.

## Rollback

Launcher implementation can be reverted by removing:

- `launcher/start_web_console.ps1`
- `launcher/start_web_console.bat`
- backend static serving additions
- launcher-specific README/docs updates
- launcher-specific tests

Rollback does not touch config JSON, state DB, local Supabase data, Docker containers, volumes, operational CSV files, or screenshot artifacts.
