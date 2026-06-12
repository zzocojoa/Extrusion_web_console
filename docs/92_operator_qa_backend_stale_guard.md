# Operator QA Backend Stale Guard

## Summary

- Date: 2026-06-12
- Branch: `codex/operator-qa-backend-stale-guard`
- Base commit: `0afe402f3544d9ab5dca99a3b59ce27852488cfa`
- Goal: block stale backend/process reuse before any Start Upload retry.
- Start Upload executions during this work: `0`
- Retry Failed executions during this work: `0`
- Duplicate rerun executions during this work: `0`
- Upload Preview executions during this work: `0`
- Edge authenticated upload calls during this work: `0`
- Full operational dataset rollout: not performed

This PR adds a small runtime guard layer for the failure mode documented in
`docs/91_operator_stage_3_bounded_start_upload_investigation.md`.

## Root Cause Carried Forward

The prior failed Stage 3 Start Upload was most consistent with
`qa_backend_stale_process_port_reuse`:

1. an older backend process still owned the QA API port;
2. a replacement backend with corrected independent overrides failed to bind;
3. health/config calls still reached the older process;
4. Start Upload used that older process's upload execution target class;
5. the job failed before processing rows;
6. DB row-count delta stayed `0`.

The product upload transform path was not proven as the root cause.

## Implemented Guard

### Backend process identity

`/api/health` now returns non-secret process identity fields:

- `startup_id`
- `started_at`
- `process_id`

QA scripts can now prove that a health response came from the backend process
that was just launched, not from an older process still serving the port.

### Sanitized target class summary

`/api/config` now returns `targetClasses` with sanitized classes only:

- DB target class;
- upload execution Edge target class;
- runtime readiness Edge target class;
- upload/runtime Edge alignment;
- preflight status and reason.

No raw DB URL, secret, token, Authorization header, JWT, or full endpoint value
is added by this summary.

### Start Upload target class preflight

`POST /api/upload/jobs` and retry creation now run a non-secret target class
preflight before creating a job.

The preflight blocks with `upload_target_preflight_failed` when the upload
execution Edge target and runtime Edge target are not both the expected local
upload-metrics target class. The block happens before upload job creation and
before any Edge authenticated upload call.

The preflight intentionally reports DB target class as evidence but does not
use it as the Start Upload hard gate. DB reachability and DB target correctness
remain Preview/reconciliation gates. This keeps the Start Upload guard focused
on the failure class observed in PR #105: upload execution target drift.

### QA launcher fresh-backend guard

`launcher/start_web_console.ps1` now accepts `-RequireFreshBackend`.

When that switch is set, an already-open backend port is a hard launcher error
instead of a reuse path. Normal operator launch behavior is otherwise preserved.

## Safety Properties

| Check | Result |
| --- | --- |
| Raw DB URL exposed by new fields | no |
| Raw secret/token/Auth/JWT exposed by new fields | no |
| Operational CSV path/name/content exposed | no |
| Start Upload retried | no |
| Upload Preview rerun | no |
| Runtime/Supabase start/stop/reset | no |
| DB migration/reset/delete/prune/drop/truncate | no |
| Docker delete/cleanup/prune | no |
| Production deploy | no |

## Regression Coverage

| Test area | Coverage |
| --- | --- |
| Health API | verifies startup identity fields are present. |
| Config API | verifies sanitized target class summary for aligned and stale classes. |
| Upload job API | verifies stale upload target class is blocked before job creation. |
| Existing upload job contracts | verifies active-job and preview-not-uploadable behavior still wins when target class is aligned. |
| Launcher script | verifies `-RequireFreshBackend` is present and PowerShell syntax still parses. |

## Validation

Completed:

- Targeted backend runtime/config/upload job/launcher tests: `119 passed`.
- `npm run typecheck`: passed.
- `npm run build:api`: passed.
- `npm run build`: passed.
- `git diff --check`: passed.
- Added-line marker scan: passed.
- This document marker scan: passed.

Notes:

- Pytest emitted existing deprecation/cache warnings, with no test failures.
- Frontend build output was generated locally but is not part of the intended commit scope.
- PR file-scope check is required after push/PR creation.

## Start Upload Rerun Status

Start Upload remains blocked until this guard PR is reviewed and merged.

If the stale backend guard and sanitized upload target class preflight are
accepted, the next branch can be:

```text
codex/operator-stage-3-bounded-start-upload-rerun
```

That next branch must still run a fresh approved QA flow and must not reuse the
failed job as acceptance evidence.
