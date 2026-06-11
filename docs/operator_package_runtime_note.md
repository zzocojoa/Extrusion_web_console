# Extrusion Web Console Operator Package

This prepared folder is the operator handoff build for the local web console.

## Run

Double-click `launcher\start_web_console.bat`, or run `launcher\start_web_console.ps1` from PowerShell.

The launcher starts the localhost backend, serves the built frontend, opens the browser, and keeps write APIs protected by a per-run local guard.

## Shortcuts

Maintainers can run `launcher\install_shortcuts.ps1` to create or refresh Desktop and Start menu shortcuts for this prepared folder.

Use `-CheckOnly` on either launcher script when validating a package without starting or writing anything.

## Package Contents

The package contains the backend application, built frontend, launcher scripts, a prepared Python runtime folder, repository-owned Supabase source assets, version metadata, and this package note.

The included Supabase assets are source-only: `supabase/config.toml`, the `upload-metrics` Edge Function source, and the schema migration required for `all_metrics`.

The package intentionally does not include repository history, developer frontend source, Node dependencies, tests, raw local config files, Supabase local state, generated credentials, database files, logs, state databases, screenshots, temporary package output, or operational CSV data.

## Safety

Normal operator launch does not require Node or npm.

The launcher does not run database reset, database cleanup, Docker cleanup, package deletion, or AppData deletion.

The package does not bootstrap, reset, migrate, or start Supabase by itself. Maintainer-approved runtime setup remains separate from normal operator launch.

Local config, state, and logs remain outside this package and are managed by the running application.

If a required package file is missing, the launcher or package check should fail clearly instead of silently continuing.
