# Operator Dashboard Real State Integration

## Summary

Verdict: `implemented_pending_full_validation`

The API-mode Dashboard no longer depends on the scaffold mock running job. The backend `/api/dashboard` and `/api/dashboard/summary` endpoints now aggregate read-only runtime, upload job, and audit state when the active state store is available.

Frontend mock mode remains unchanged. Screenshot QA and demo URLs using `?state=ready|attention|blocked|running` still use the frontend mock query path when `VITE_API_MODE` is not `api`.

## Business Goal

Stage 4 Start Upload succeeded, but the first Dashboard screen could still show a fake running upload job from the original scaffold. Operators need the Dashboard to reflect the real latest upload state in API mode, including the latest successful job and its processed/uploaded/accepted row counts.

## Root Cause

Root cause classification: `scaffold_mock_endpoint_left_in_api_mode`

The frontend already separated mock mode from API mode. In API mode it called `/api/dashboard` correctly, but the backend endpoint still returned `build_mock_dashboard()`. Backend tests also asserted the mock running job contract, so the fake job became the API contract.

## Implementation

Changed backend Dashboard aggregation:

- Reads latest upload jobs from the active state DB when available.
- Maps the latest upload job into `currentJob` and `recentJobs`.
- Shows terminal `succeeded` jobs as succeeded instead of a fake running job.
- Surfaces processed, uploaded, and accepted row counts in the Dashboard overall/current/recent job message fields.
- Uses runtime readiness status for Supabase, Edge, Grafana, Docker/WSL, and state-store summary.
- Reads audit rows as safe summary rows only. Raw params are not included in the Dashboard response.
- Falls back to neutral empty/unknown state when no persisted state exists.

No upload execution behavior changed.

## Safety And Redaction

Forbidden operations not performed:

- Upload Preview execution
- Start Upload
- Retry Failed
- duplicate rerun
- Edge authenticated upload call
- full rollout
- DB reset/init/delete/truncate/drop/prune
- Supabase start/stop/reset
- Docker lifecycle or destructive operations

Redaction posture:

- No raw operational source path, source filename, source content, or full local source path is documented here.
- No credential values or database connection strings are documented here.
- Dashboard audit summary intentionally omits audit params and only shows action/result/error-code level summary.

## Verification Notes

Targeted backend Dashboard tests were updated to prove:

- Empty active state returns neutral Dashboard data, not the old mock running job.
- A persisted latest upload job with `succeeded` status returns `currentJob.status=succeeded`.
- The latest job exposes uploaded rows through existing Dashboard row fields.
- The Dashboard summary endpoint uses the same real-state contract.
- Sensitive audit params do not appear in the Dashboard response.

Live Stage 4 success visibility depends on the backend using the same active QA/operator state DB that contains the accepted Stage 4 upload job. If the process is launched against a different state DB context, the Dashboard correctly shows an empty or different latest state instead of fabricating success.

Current local state context note:

- A read-only default state check returned a real latest upload job with `status=succeeded`.
- The observed count was not the reviewed Stage 4 `17179` row target, so this local process context proves real-state rendering but does not prove that the active default state DB is the Stage 4 restored-reference state DB.

## Next Action

Run the targeted backend/runtime/audit tests, frontend typecheck/build, API-mode browser smoke, and marker scans. Then open a small implementation PR for review without merging.
