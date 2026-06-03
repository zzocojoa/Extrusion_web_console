# Upload Job Real Local Supabase Authenticated Edge Smoke QA

Status: report-only QA for branch `codex/upload-job-real-supabase-edge-auth-smoke`

Date: 2026-06-04

Scope: authenticated Upload Job smoke against local Supabase Edge Function using `integrated_plc_operational_fixture`

## Summary

Authenticated Upload Job real Edge smoke was attempted without feature code changes. The original operational fixture was not modified, and the untracked fixture was not staged.

Local Supabase API, Studio, DB TCP, and the Edge runtime were reachable. The Edge Function route returned `401` for a no-auth request, proving the route was alive and authentication was required.

Authenticated upload was not executed because the current preconfigured environment did not provide the required DB URL, anon key, source directory, or direct environment Edge URL. The app `Settings` instance had an Edge URL and state DB path, but DB URL and anon key were missing. Per the secret-handling rule for this QA pass, no secret-bearing status/config command was run and no key value was requested.

Result: this report records a QA blocker. Authenticated real Edge Upload Job execution, duplicate-safe rerun, job_events/SSE replay, exact key verification, and `upload.start` audit verification remain unverified.

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
| Edge runtime container | Running |
| Edge route no-auth smoke | `401` |
| Process env DB URL | Missing |
| Process env anon key | Missing |
| Process env Edge URL | Missing |
| Process env source directory | Missing |
| Settings DB URL | Missing |
| Settings anon key | Missing |
| Settings Edge URL | Present |
| Settings state DB path | Present |

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

The report intentionally excludes raw file names, absolute paths, CSV contents, DB URLs, tokens, anon keys, service role values, JWTs, and credential-bearing strings.

## Runtime Checks

| Check | Result |
| --- | --- |
| API port | Reachable |
| Studio port | Reachable |
| DB TCP port | Reachable |
| Edge runtime status | Running |
| Edge route no-auth smoke | `401`, route reachable but auth required |
| Edge authenticated route smoke | Not executed, `preconfigured_env_missing` |

The previous real Supabase Preview soak showed this fixture's exact keys were already present in `public.all_metrics`. This pass did not re-query those keys through a DB connection because the configured DB URL was missing.

## Upload Job Smoke

| Scenario | Result |
| --- | --- |
| Preconfigured env check | Failed, `preconfigured_env_missing` |
| Preview run for upload target | Not executed |
| Safe synthetic/minimal sample decision | Not executed because auth prerequisites were missing |
| Upload Job start | Not executed |
| Upload Job status/progress | Not verified |
| Uploaded rows | Not verified |
| Inserted rows | Not verified |
| Duplicate rerun row count behavior | Not verified |
| `job_events` persistence | Not verified against real Edge job |
| SSE replay | Not verified against real Edge job |
| Exact keys presence | Not verified in this pass |
| `/api/audit?action=upload.start` | Not verified against real Edge job |

Blocking reason: real upload requires configured Edge URL plus anon key, and exact DB row-count/key verification requires a configured DB connection. The current environment did not provide the required secret-bearing values through allowed preconfigured channels.

## Redaction Checks

| Check | Result |
| --- | --- |
| Secret values printed to console | Not observed |
| Secret values written to report | Absent |
| Raw operational fixture name in report | Absent |
| Raw operational fixture path in report | Absent |
| CSV contents in report | Absent |
| DB URL in report | Absent |
| Token/key/service role/JWT in report | Absent |
| Raw upload audit params | Not applicable, authenticated upload not executed |

Secret-bearing local Supabase status/config output was intentionally not collected.

## HTTP Smoke

| Smoke | Result |
| --- | --- |
| Backend health on temporary port | `200` |
| Backend audit API on temporary port | `200` |
| Vite app root on temporary port | `200` |
| Upload page on temporary port | `200` |
| Logs page on temporary port | `200` |
| Edge route without auth | `401` |

Browser screenshot QA was not completed in this pass. HTTP smoke was used as the non-destructive substitute.

## Validation

| Check | Result |
| --- | --- |
| Targeted Upload Job/Audit backend tests | Passed, 43 tests |
| Full backend tests | Passed, 130 tests |
| `npm run typecheck` | Passed |
| `npm run build` | Passed |

Warnings observed:

- Existing FastAPI/Starlette `TestClient` deprecation warning.
- Existing HTTP 422 deprecation warning.
- Existing pytest cache write warning under repository `.pytest_cache`; tests used `--basetemp` under `C:\tmp`.

## Findings

### Blocker: preconfigured authenticated Edge environment missing

The local runtime and Edge route were reachable, but authenticated upload could not be executed because the current process/app configuration did not provide the required DB URL and anon key. The QA rule explicitly prohibited extracting or requesting secret values, so the pass stopped at `preconfigured_env_missing`.

This means the following remain unverified:

- Start Upload through `POST /api/upload/jobs`.
- duplicate-safe Edge upsert behavior.
- inserted row reporting.
- exact key presence after upload.
- duplicate rerun row count stability.
- persisted `job_events`.
- SSE replay via `afterSeq`.
- `/api/audit?action=upload.start`.
- upload audit/log redaction for a real Edge job.

## Reproduction Conditions

1. Start from branch `codex/upload-job-real-supabase-edge-auth-smoke`.
2. Keep `integrated_plc_operational_fixture` untracked and read-only.
3. Ensure the existing local Supabase stack is running.
4. Confirm the Edge runtime container is running.
5. Confirm process/app DB URL and anon key are missing using presence-only checks.
6. POST an empty JSON array to the Edge route without auth.
7. Observe `401`.
8. Stop before authenticated upload because allowed preconfigured secret values are missing.

## Merge Readiness

This PR is mergeable only as a report-only artifact documenting the authenticated QA blocker.

It is not evidence that real Edge Upload Job execution is production-ready. The next pass should run with a preconfigured local test environment where DB URL, anon key, Edge URL, source directory, and state DB path are already present through approved channels. The test runner should still print only presence, status codes, counts, and redacted summaries.

Recommended follow-up branch:

`codex/upload-job-real-supabase-edge-auth-ready-smoke`

Follow-up should verify:

- `POST /api/upload/jobs` from a safe target preview.
- terminal Upload Job status and progress.
- uploaded/inserted row counts.
- duplicate rerun row count does not increase.
- exact key presence in `all_metrics`.
- persisted `job_events`.
- SSE replay via `afterSeq`.
- `/api/audit?action=upload.start`.
- audit/log/report redaction.
