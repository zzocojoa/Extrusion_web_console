# Extrusion Web Console Product Scope

## Summary

- Goal: rebuild the extrusion data upload and operations experience as a local web operations console, not as a direct Tkinter screen clone.
- Runtime: Windows operator PC + WSL/Docker + local Supabase remain the target environment.
- Web app access: localhost only.
- Grafana: stays separate and may be exposed on the factory internal network as its own dashboard.
- Migration posture: hard replacement of the Tkinter GUI after Core Ops parity is proven.

## Product Direction

The right product framing is:

> A local operations console for reliable extrusion data upload, recovery, state visibility, and local Supabase/Grafana operations.

The wrong framing is:

> Convert the existing Tkinter GUI to a web page.

The web console must preserve the reliability properties of the legacy uploader while reducing UI/operations coupling.

## V1 Scope: Core Ops

Include in v1:

- Dashboard
- Settings
- Upload Preview
- Start Upload
- Retry Failed
- Upload progress and logs
- Local Supabase status/start/stop
- Grafana status/link only
- Audit logs
- Korean and English UI support
- Double-click launcher that starts the local web service and opens the browser

Exclude from v1 unless explicitly re-scoped:

- Data Mgmt archive/delete flows
- Supabase Mgmt delete UI
- Cycle Ops
- Training Dataset Builder
- Cloud Supabase migration
- Multi-user LAN access for the web app
- Grafana iframe embedding

## Key Decisions

- Supabase remains local.
- The web app itself remains localhost-only.
- Grafana is not embedded in the web console.
- Existing Tkinter GUI state is not imported by default.
- The new app starts with a new state store.
- Upload preview must reconcile local CSV candidates against local Supabase data before upload.
- Existing `all_metrics(timestamp, device_id)` upsert/dedup behavior must remain intact.
- Dangerous operations are protected primarily by audit logs rather than confirmation dialogs.

## Recommended Architecture Direction

Use a separated operations console architecture:

- Backend: Python API service that owns file system access, upload jobs, local Supabase control, config, audit logs, and integration with legacy core logic.
- Frontend: browser UI for Dashboard, Settings, Upload, and Logs.
- Worker/task model: upload and local runtime operations run as explicit jobs with observable status, logs, failures, and audit records.
- Launcher: double-click entrypoint that starts the backend/frontend and opens the browser.

The detailed technical architecture must be finalized with `plan-eng-review` before implementation.

## Existing Assets To Reuse Or Extract

Reference project:

`C:\Users\user\Documents\GitHub\Extrusion_data`

Candidates for reuse:

- `core/upload.py`
- `core/transform.py`
- `core/config.py`
- `core/files.py`
- `core/state_db.py` patterns where useful
- `supabase/functions/upload-metrics`
- `supabase/migrations`
- `grafana/provisioning`
- `grafana/dashboards`
- upload and Smart Sync tests

Do not directly port:

- `uploader_gui_tk.py`

The Tkinter file is useful as a behavior reference, not as architecture to copy.

## State And Migration Policy

The new app should start with a new state store. It should not automatically import the legacy GUI's `uploader_state.db`.

To reduce duplicate-upload risk, web preview must compare local CSV candidates with Supabase data and classify candidates before upload:

- upload target
- already represented in DB
- risky or unclear
- excluded with reason

The current database-level safety pattern, unique/upsert by `timestamp, device_id`, must remain the final duplicate protection.

## Audit Log Requirements

Audit logs must record at least:

- timestamp
- OS user or local actor identity
- action name
- request parameters safe for logging
- result: success, failure, cancelled, blocked
- error message when applicable
- related job id when applicable

Audit logged actions:

- Settings save
- Upload preview
- Upload start
- Upload retry
- Upload pause/resume/cancel if supported
- Local Supabase start
- Local Supabase stop
- Any failed operation

## Success Criteria

V1 is ready to replace the legacy GUI when:

- Core Ops flows work from the browser.
- Existing CSV upload behavior matches the legacy app for representative files.
- Smart Sync behavior is preserved.
- Duplicate risk is visible before upload.
- Local Supabase start/stop/status is visible and auditable.
- Upload failures are visible in UI, logs, and audit history.
- Korean and English UI text paths are present.
- README is enough for a developer/operator to run the app.
