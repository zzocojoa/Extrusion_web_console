# Extrusion Web Console Operator Package

This prepared folder is the operator handoff build for the local web console.

## Run

Use the `Extrusion Web Console` Desktop or Start menu shortcut after the maintainer installs shortcuts, or run `launcher\tray_supervisor.ps1` from PowerShell.

The tray supervisor starts or reuses the localhost backend, serves the built frontend, opens the browser, and keeps write APIs protected by a per-run local guard. Closing the browser does not stop the tray supervisor.

## Shortcuts

Maintainers can run `launcher\install_shortcuts.ps1` to create or refresh one Desktop shortcut and one Start menu shortcut for this prepared folder.

The shortcut uses hidden PowerShell execution with the tray supervisor, so normal operator launch opens the browser without leaving a command window on screen. The tray menu provides `Open` and `Exit`. `Exit` verifies `/api/health` reports `service=extrusion-web-console-api`, localhost-only status, and a matching backend process before it stops anything.

Use `-CheckOnly` on launcher and shortcut scripts when validating a package without starting or writing anything.

## Package Contents

The package contains the backend application, built frontend, launcher scripts, a prepared Python runtime folder, repository-owned Supabase source assets, version metadata, and this package note.

The included Supabase assets are source-only: `supabase/config.toml`, the `upload-metrics` Edge Function source, and the schema migration required for `all_metrics`.

The package intentionally does not include repository history, developer frontend source, Node dependencies, tests, raw local config files, Supabase local state, generated credentials, database files, logs, state databases, screenshots, temporary package output, or operational CSV data.

## Safety

Normal operator launch does not require Node or npm.

The launcher does not run database reset, database cleanup, Docker cleanup, package deletion, or AppData deletion.

The tray `Exit` action and maintainer stop/restart lifecycle scripts do not stop arbitrary port 8000 processes. They stop only the verified localhost Extrusion Web Console API backend reported by `/api/health`.

The package does not bootstrap, reset, migrate, or start Supabase by itself. Maintainer-approved runtime setup remains separate from normal operator launch.

When launched from the prepared package, the launcher sets process-only defaults for the package-local independent `Extrusion_web_console` Supabase target. Without explicit process overrides, DB reconciliation uses the package-local DB port from `supabase/config.toml`, and Edge routing uses the matching package-local API/Edge target class. Raw DB URLs and secret values are not printed. Explicit process environment overrides still take precedence for approved fallback or maintenance runs.

Local config, state, and logs remain outside this package and are managed by the running application.

If a required package file is missing, the launcher or package check should fail clearly instead of silently continuing.

## Observability

The Dashboard and runtime API expose Grafana and Vector as sanitized status
classes for operator visibility. They do not copy raw Grafana, Vector, Docker,
Supabase, or Edge logs into the package, and they must not print generated
credentials, DB URLs, Authorization values, JWTs, raw source paths, or raw CSV
content.

Grafana remains a status/link target only. The package does not embed Grafana in
an iframe and does not widen web-console LAN access.

Docker Desktop's `Expose daemon on tcp://localhost:2375 without TLS` setting is
not an operator package requirement and should stay off. A maintainer may enable
it only temporarily for diagnostics, release validation, or failure reproduction
when sanitized Docker/Vector evidence is needed, then must turn it off again.

Vector or Grafana attention is a non-core observability caveat when Supabase
API, DB, Edge, Upload Preview, and Audit evidence are normal. It does not
approve Docker cleanup/reset, Supabase reset/cleanup, LAN exposure, or upload
gate bypass.
