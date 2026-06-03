# Upload Job Real Local Supabase Edge Smoke QA

Status: report-only QA for branch `codex/upload-job-real-supabase-edge-smoke`

Date: 2026-06-03

Scope: Upload Job smoke against local Supabase runtime and Edge Function route using `integrated_plc_operational_fixture`

## Summary

Upload Job real Edge smoke was attempted without feature code changes. The original operational fixture was not modified, and the untracked fixture was not staged.

Local Supabase API, Studio, and DB ports were reachable. The existing Edge runtime container was started non-destructively, and the `upload-metrics` route was reachable but required authentication. The current web-console `Settings` instance did not have DB URL or anon key configured, and credential extraction from local Supabase status was not performed because it would expose or access secret-bearing values without explicit approval.

Result: this report records a QA blocker. Authenticated real Edge Upload Job execution, duplicate-safe rerun, job_events/SSE replay, and `upload.start` audit verification remain unverified in this pass.

## Environment

| Item | Result |
| --- | --- |
| Backend | FastAPI local test/runtime |
| Frontend | React/Vite HTTP smoke |
| Data label | `integrated_plc_operational_fixture` |
| Source access | Read-only metadata/count check |
| Local Supabase API | Reachable |
| Local Supabase Studio | Reachable |
| Local Supabase DB TCP | Reachable |
| Edge runtime container | Existing container started, non-destructive |
| Edge route | Reachable, unauthenticated request returned `401` |
| Configured DB URL in web-console settings | Not configured |
| Configured anon key in web-console settings | Not configured |

No DB reset, DB cleanup, DB delete, Docker volume deletion, Docker container deletion, or Docker prune was performed.

## Test Data

| Metric | Result |
| --- | --- |
| Sanitized label | `integrated_plc_operational_fixture` |
| File class | `integrated_plc_csv` |
| File size class | `medium_1_to_10_mib` |
| Row count estimate | 20,219 |
| Original fixture mutation | No |
| Fixture committed | No |

The report intentionally excludes raw file names, absolute paths, CSV contents, DB URLs, tokens, anon keys, service role values, and credential-bearing strings.

## Runtime Checks

| Check | Result |
| --- | --- |
| API port | Reachable |
| Studio port | Reachable |
| DB TCP port | Reachable |
| Edge runtime status | Running after non-destructive start of existing container |
| Edge route no-auth smoke | `401`, route reachable but auth required |

The previous real Supabase Preview soak showed this fixture's exact keys were already present in `public.all_metrics`. This smoke did not re-query the DB with credentials and did not upload rows.

## Upload Job Smoke

| Scenario | Result |
| --- | --- |
| Preview target setup for upload | Not executed |
| Upload Job start | Not executed |
| Terminal job status | Not verified |
| Uploaded rows | Not verified |
| Inserted rows | Not verified |
| Duplicate rerun row count behavior | Not verified |
| `job_events` persistence | Not verified against real Edge job |
| SSE replay | Not verified against real Edge job |
| `/api/audit?action=upload.start` | Not verified against real Edge job |

Blocking reason: real upload requires configured Edge URL plus anon key, and DB row-count verification requires a DB connection. Edge URL was configured, but anon key and DB URL were not configured in the current web-console settings. Accessing local Supabase status or config to extract secret-bearing values was intentionally not done in this pass.

## Redaction Checks

| Check | Result |
| --- | --- |
| Raw operational fixture name in report | Absent |
| Raw operational fixture path in report | Absent |
| CSV contents in report | Absent |
| DB URL in report | Absent |
| Token/key/service role in report | Absent |
| Raw upload audit params | Not applicable, authenticated upload not executed |

## HTTP Smoke

| Smoke | Result |
| --- | --- |
| Backend health on temporary port | `200` |
| Backend audit API on temporary port | `200` |
| Vite app root | `200` |
| Upload page | `200` |
| Logs page | `200` |
| Vite proxy audit API | `200` |
| Edge route without auth | `401` |

PowerShell `Invoke-WebRequest` returned false negatives for one temporary backend process even while Uvicorn was running; `curl.exe` status-code smoke was used as the stable HTTP evidence.

Browser screenshot QA was not completed in this pass. HTTP smoke was used as the non-destructive substitute.

## Validation

| Check | Result |
| --- | --- |
| Targeted Upload Job/Preview backend tests | Passed, 31 tests |
| Full backend tests | Passed, 130 tests |
| `npm run typecheck` | Passed |
| `npm run build` | Passed |

Warnings observed:

- Existing FastAPI/Starlette `TestClient` deprecation warning.
- Existing HTTP 422 deprecation warning.
- Existing pytest cache write warning under repository `.pytest_cache`; tests used `--basetemp` under `C:\tmp`.

## Findings

### Blocker: authenticated Edge Upload Job not verified

The Edge Function route was reachable, but authenticated upload could not be executed because the current app settings did not have anon key and DB URL configured. Without those values, this pass cannot verify Start Upload, duplicate-safe Edge upsert, inserted row reporting, job_events persistence, SSE replay, or `upload.start` audit rows in the real local Supabase path.

### Non-blocking: HTTP smoke needed `curl.exe`

Temporary backend/Vite smoke was reliable with `curl.exe`. One `Invoke-WebRequest` pass returned unreachable while Uvicorn was active, so the report uses `curl.exe` status codes as evidence.

## Reproduction Conditions

1. Start from branch `codex/upload-job-real-supabase-edge-smoke`.
2. Keep `integrated_plc_operational_fixture` untracked and read-only.
3. Ensure the existing local Supabase stack is running.
4. Start the existing Edge runtime container non-destructively if it is stopped.
5. Confirm `Settings()` has Edge URL configured but does not have DB URL or anon key configured.
6. POST an empty JSON array to the Edge route without auth.
7. Observe `401`, proving the route is reachable but authenticated upload cannot proceed.

## Merge Readiness

This PR is mergeable only as a report-only artifact documenting the QA blocker.

It is not evidence that real Edge Upload Job execution is production-ready. The next branch should complete the authenticated smoke with explicit secret-handling approval or a preconfigured local test environment.

Recommended follow-up branch:

`codex/upload-job-real-supabase-edge-auth-smoke`

Follow-up should verify:

- `POST /api/upload/jobs` from a safe target preview.
- terminal Upload Job status.
- uploaded/inserted row counts.
- duplicate rerun row count does not increase.
- persisted `job_events`.
- SSE replay via `afterSeq`.
- `/api/audit?action=upload.start`.
- audit/log/report redaction.
