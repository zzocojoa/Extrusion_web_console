# Windows Shortcut Packaging Plan

Status: implemented on branch `codex/windows-shortcut-packaging-impl` for shortcut installation, idempotency tests, and operator documentation. General installer/MSI/service packaging remains out of scope.

## Decision Summary

Launcher phase 3 will ship an operator-friendly Windows entry point without changing the local-only architecture. The v1 packaging model is a prepared operator folder plus Windows shortcuts, not an installer, service, or machine-wide deployment.

The primary operator entry point is a Windows shortcut named `Extrusion Web Console`. The shortcut targets `launcher/start_web_console.bat`, with the repository or packaged app root as the working directory. The PowerShell script remains the implementation entry point for maintainers and developer smoke checks.

## Goals

- Let a non-developer start the web console by double-clicking a Windows shortcut.
- Keep backend binding on `127.0.0.1`.
- Keep API docs disabled in operator mode.
- Keep per-run local token behavior from launcher phase 2.
- Avoid requiring Node, npm, or frontend build commands during operator startup.
- Preserve local Supabase safety policy: status and guidance only, no bootstrap, reset, delete, cleanup, prune, or Docker volume/container deletion.
- Keep secrets, database URLs, tokens, authorization headers, and operational CSV paths out of scripts, logs, docs, package manifests, and screenshots.

## Non-Goals

- MSI, MSIX, installer, Windows service, tray app, auto-update, code signing, registry writes, or machine-wide install.
- Production deploy.
- LAN or multi-user access.
- Supabase initialization, container creation, reset, cleanup, pruning, or data deletion.
- Operator-driven dependency installation.
- Upload, runtime, audit, or settings API behavior changes.

## User Journey

1. A maintainer prepares the operator folder on the operator PC.
2. The maintainer confirms `frontend/dist` and `.venv/Scripts/python.exe` are present.
3. The maintainer installs or refreshes the Desktop and optional Start menu shortcut.
4. The operator double-clicks `Extrusion Web Console`.
5. The launcher starts FastAPI on `127.0.0.1`, generates a per-run local API token, opens the browser, and writes logs under the AppData launcher log directory.
6. If startup fails, the launcher prints an operator-readable reason and the log location.
7. The operator closes the launcher window to stop the launcher-owned backend process.

## Package Model

The v1 package is a prepared operator folder. It can be delivered as a zip or copied folder, but it is not a general installer.

Included:

- `backend/`
- `frontend/dist/`
- `launcher/`
- project metadata needed by the backend and launcher
- README and operator-facing docs
- a target-PC prepared `.venv/` or a documented maintainer setup step that creates it before handoff

Excluded:

- `.git/`
- `.gstack/`
- `frontend/node_modules/`
- raw `.env` files containing secrets
- logs, state database files, and local config files
- generated screenshots
- operational CSV fixtures or samples
- developer-only cache folders

## Frontend Build Artifact

The operator package includes `frontend/dist`.

`npm run build` and launcher `-BuildFrontend` remain developer or release-maintainer actions only. The double-click operator flow must not run Node or npm.

If `frontend/dist/index.html` is missing, operator startup should fail fast with a clear message that the package is incomplete or the frontend build was not prepared. The launcher must not silently build the frontend in operator mode.

## Python Runtime

The operator flow requires `.venv/Scripts/python.exe` to be available before handoff.

For v1, the recommended release process is target-PC preparation by a maintainer:

- create or refresh the virtual environment
- install backend dependencies
- run launcher `-CheckOnly`
- run HTTP smoke
- install or refresh shortcuts

Dependency installation is a setup-maintainer task, not an operator task. A future helper such as `launcher/setup_operator_runtime.ps1` may automate this for maintainers, but it must not be part of the normal double-click startup path.

## Node And npm

Node and npm are not required in operator mode.

They are required only for developers or release maintainers who run frontend build, typecheck, or screenshot QA before producing the operator package.

## Shortcut Strategy

Primary shortcut:

- Name: `Extrusion Web Console`
- Target: `launcher/start_web_console.bat`
- Working directory: packaged app root
- Scope: Desktop shortcut by default

Optional shortcut:

- Start menu shortcut using the same target and working directory

The shortcut installer should be idempotent:

- refresh an existing shortcut when the package path changes
- avoid creating duplicates
- not modify AppData config, logs, or state
- not delete the feature branch, package folder, or runtime data

Implementation result:

- `launcher/install_shortcuts.ps1` creates or updates Desktop and Start menu shortcuts named `Extrusion Web Console`.
- `launcher/install_shortcuts.bat` provides a double-click wrapper for maintainers.
- The shortcut target is `launcher/start_web_console.bat`.
- The working directory is the prepared operator folder root.
- `-CheckOnly` previews target and shortcut paths without writing shortcuts.
- Test-only directory overrides allow idempotency validation without touching the real Desktop or Start menu.
- The script does not delete AppData config, state databases, launcher logs, Docker data, database data, or operational CSV files.

Shortcut uninstall should remove only shortcuts created by this app. It must not delete config, logs, state database files, local Supabase data, or operational CSV files.

## Logs

Launcher logs remain under:

- `%APPDATA%/ExtrusionWebConsole/logs/launcher/`

The launcher should print the log directory and latest log filename on startup and failure. Logs must not contain local API tokens, database URLs, authorization headers, raw config secret values, or operational CSV paths.

## Config And State Location

Config and state remain outside the package folder:

- config JSON under `%APPDATA%/ExtrusionWebConsole/`
- state database under `%APPDATA%/ExtrusionWebConsole/`

This keeps package replacement from overwriting operator settings or state. Package updates must not move, delete, or reset these files.

## Local Token Policy

The operator shortcut uses launcher defaults:

- generate a per-run local API token
- pass it to the backend through environment only
- expose it to the frontend only through the existing bootstrap flow
- send it only on mutating API requests
- never place it in URL query strings, shortcut arguments, logs, screenshots, config files, or package manifests

`EWC_LOCAL_TOKEN_MODE=dev-disabled` remains a developer/test opt-out and must not be used by the operator shortcut.

## API Docs Policy

Operator shortcut startup keeps API docs disabled.

The following routes remain unavailable in operator mode:

- `/api/docs`
- `/api/openapi.json`
- `/api/redoc`

`EWC_API_DOCS_MODE=enabled` is reserved for developer and automated test runs.

## Local Supabase And Docker Readiness

The launcher and shortcut do not start, initialize, repair, reset, prune, delete, or recreate local Supabase or Docker resources.

Readiness guidance should be status-oriented:

- Docker Desktop running
- local Supabase API reachable
- local Supabase DB reachable
- Edge runtime reachable when upload job flows need it

If readiness is missing, the launcher or app should state what is missing and where to see logs. It must not attempt destructive repair.

## Failure UX

Startup failures should be operator-readable and actionable.

Required failure messages:

- missing `.venv/Scripts/python.exe`: runtime setup required
- missing `frontend/dist/index.html`: package frontend build missing
- occupied port by this app: reuse or point to the running URL
- occupied port by another process: port conflict with guidance to close the conflicting app or use a maintainer override
- backend health timeout: backend failed to start, with log path
- browser open failure: print the local URL
- API docs disabled: expected operator policy
- local Supabase unavailable: runtime not ready, no destructive action taken
- token/bootstrap mismatch: close old launcher-owned backend and restart from the shortcut

## Release Flow

1. Start from clean `main`.
2. Build frontend as a developer or release-maintainer action.
3. Prepare or refresh the target-PC Python virtual environment.
4. Run backend tests and frontend checks appropriate for the release.
5. Run launcher `-CheckOnly`.
6. Run HTTP smoke against the packaged app:
   - `/`
   - `/upload`
   - `/logs`
   - `/settings`
   - `/api/health`
   - `/api/audit?action=settings.save&limit=1`
7. Confirm API docs are disabled in operator mode.
8. Confirm mutating API token guard remains enabled.
9. Confirm package manifest excludes `.gstack`, developer artifacts, secret files, and operational CSV fixtures.
10. Install or refresh Desktop and optional Start menu shortcuts.
11. Record release notes with package version, source commit, smoke result, and known limitations.

## Versioning And Release Notes

The package name should include the app version or release date and source commit short hash.

Release notes should include:

- source commit
- launcher behavior changes
- whether `frontend/dist` is included
- whether `.venv` was prepared on target PC
- smoke status
- known runtime readiness requirements

`VERSION` changes are not required unless the repository release convention later requires them.

## Test Plan

Implementation PRs for this plan should validate:

- shortcut target exists
- shortcut working directory is the package root
- shortcut launch starts backend on `127.0.0.1`
- browser auto-open works or prints a usable URL
- `frontend/dist` present path serves SPA routes
- missing `frontend/dist` fails clearly
- missing `.venv` fails clearly
- `/api/*` routes are not swallowed by SPA fallback
- `/api/docs`, `/api/openapi.json`, and `/api/redoc` are disabled in operator mode
- mutating API missing/invalid token requests are blocked
- read-only APIs remain token-free
- `-CheckOnly` reports readiness without starting destructive actions
- port conflict handling reports reuse or conflict accurately
- logs do not expose tokens, database URLs, authorization headers, or raw secret values
- package manifest excludes `.gstack`, generated screenshots, `frontend/node_modules`, raw `.env` files, operational CSV fixtures, and local state

Suggested checks:

- backend targeted launcher/static/token tests
- full backend tests when feasible
- `npm run typecheck`
- `npm run build`
- `npm run qa:screenshots`
- launcher HTTP smoke
- `git diff --check`
- package manifest redaction scan

## Implementation Order

1. Add shortcut install/update script with idempotent Desktop shortcut creation.
2. Add optional Start menu shortcut support.
3. Done: add shortcut tests for syntax, expected path generation, idempotency, repo-local target, working directory, and destructive command exclusions.
4. Done: update README operator instructions.
5. Deferred: shortcut uninstall script. If added later, it must remove only app-created shortcuts and must not delete AppData config/state/logs.
6. Deferred: package manifest allowlist and redaction scan.
7. Deferred: launcher readiness output for package mode.
8. Deferred: screenshot and HTTP smoke from a fully assembled packaged entry point.

## Remaining Risks

- A prepared virtual environment may still be tied to the target PC and Python version. This is acceptable for v1 because the package is intended for controlled operator-PC setup, not broad distribution.
- Without an installer, shortcut creation and package placement are maintainer responsibilities.
- Local Supabase readiness remains external to the launcher. This avoids unsafe automated repair but means operators may still need clear setup guidance when Docker or Supabase is unavailable.
- Code signing and SmartScreen handling are not addressed in v1.
- `frontend/dist` may be included in an operator package, but remains an ignored/generated artifact and is not committed to git.

## Merge Readiness For Implementation

An implementation PR is ready to merge when:

- the operator shortcut starts the app from a prepared folder
- no Node/npm is required for operator launch
- API docs remain disabled in operator mode
- local token guard remains enabled
- launcher and package logs are redacted
- generated artifacts and operational CSV fixtures are excluded
- failure states are clear enough for a non-developer operator
- tests and HTTP smoke are recorded
