# Operator Dashboard Real State Post-Merge Smoke

## Summary

Verdict: `passed_with_state_context_caveat`

PR #126 is merged into `main`, and the running API-mode Dashboard no longer shows the scaffold mock running job. The Dashboard reads the active backend state and displays a real latest upload job.

## Environment

- Branch: `main`
- Backend health: reachable
- Frontend dev UI: reachable at `http://127.0.0.1:5173/`
- Backend startup identity: recorded from `/api/health`
- Browser mode: headless Chromium smoke against the running dev UI

## API Evidence

Read-only API calls performed:

- `/api/health`
- `/api/dashboard`
- `/api/upload/jobs/latest`
- `/api/audit`
- `/api/runtime/local-supabase`

Observed API state:

- `/api/dashboard`: `200`
- Dashboard overall: `ready`
- Dashboard title: `Latest upload succeeded`
- Dashboard current job status: `succeeded`
- Dashboard current job uploaded rows: `24515`
- Dashboard scaffold job marker: not present
- Dashboard fake `12/18` running marker: not present
- `/api/upload/jobs/latest`: `200`
- Latest job status: `succeeded`
- Latest job processed/uploaded/accepted rows: `24515 / 24515 / 24515`
- Latest job total files: `1`
- `/api/audit`: reachable, recent rows returned
- `/api/runtime/local-supabase`: reachable
- Runtime summary: API/DB/Studio ready, Edge status unreachable, overall attention

## UI Evidence

Browser smoke checks:

- Dashboard loaded.
- Dashboard did not show the scaffold mock job id.
- Dashboard did not show the fake `12/18` running state.
- Dashboard showed `Latest upload succeeded`.
- Dashboard showed `24515`.
- Dashboard did not show `17179`.
- Dashboard requested `/api/dashboard`, proving API mode was active.
- Upload page loaded.
- Upload Job view showed the same latest job and `24515` count as Dashboard.
- Logs/Audit view loaded.
- Settings view loaded.
- Browser console errors: `0`
- Failed browser requests: `0`

## State Context Caveat

The active state DB used by the currently running backend contains a real latest successful upload job with `24515` rows. This differs from the reviewed Stage 4 evidence target of `17179` rows.

This is not a Dashboard mock failure. Dashboard and Upload Job agree on the same active backend state. If operators need to verify the reviewed Stage 4 restored-reference evidence specifically, the backend must be launched with the state DB context that contains that reviewed job.

## Redaction Result

Checked UI text for source locator, credential, header, and database connection markers. No raw source path/name/content or credential values were observed in Dashboard, Logs/Audit, or Settings.

## Forbidden Operations

Not performed:

- Upload Preview execution
- Start Upload
- Retry Failed
- duplicate rerun
- Edge authenticated upload call
- full rollout
- Settings save
- destructive database operations
- Supabase lifecycle operations
- Docker lifecycle/destructive operations

## Next Action

If Dashboard still looks unexpected in a human browser session, first verify which backend process and state DB context the frontend is using. Do not make Dashboard code changes until the active state context is confirmed.
