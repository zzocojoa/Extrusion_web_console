# Upload Job Real Local Supabase Auth-Ready Edge Smoke QA

Status: report-only QA for branch `codex/upload-job-real-supabase-edge-auth-ready-smoke`

Date: 2026-06-04

Scope: authenticated Upload Job smoke readiness against local Supabase Edge Function using `integrated_plc_operational_fixture`

## Summary

Authenticated Upload Job auth-ready smoke was attempted without feature code changes. The original operational fixture was not modified, and the untracked fixture was not staged.

The current preconfigured environment still does not provide the required DB URL, anon key, or source directory through approved channels. The app `Settings` instance has an Edge URL and state DB path, but the DB URL and anon key are missing. Local Supabase API, Studio, DB TCP, and Edge route were also unreachable in this pass because the local Docker daemon was not available.

Result: this report records `preconfigured_env_missing` plus local runtime unavailable. Authenticated real Edge Upload Job execution remains unverified.

## Environment

| Item | Result |
| --- | --- |
| Backend | FastAPI local test/runtime |
| Frontend | React/Vite HTTP smoke |
| Data label | `integrated_plc_operational_fixture` |
| Source access | Read-only metadata assumption from prior reports; no raw path or content emitted |
| Process env DB URL | Missing |
| Process env anon key | Missing |
| Process env Edge URL | Missing |
| Process env source directory | Missing |
| Process env state DB path | Missing |
| Settings DB URL | Missing |
| Settings anon key | Missing |
| Settings Edge URL | Present |
| Settings state DB path | Present |
| Local Supabase API | Unreachable |
| Local Supabase Studio | Unreachable |
| Local Supabase DB TCP | Unreachable |
| Docker daemon | Unavailable |
| Edge route no-auth smoke | `000`, route unreachable |
| Edge authenticated route smoke | Not executed, `preconfigured_env_missing` |

No DB reset, DB cleanup, DB delete, Docker volume deletion, Docker container deletion, or Docker prune was performed.

## Test Data

| Metric | Result |
| --- | --- |
| Sanitized label | `integrated_plc_operational_fixture` |
| File class | `integrated_plc_csv` |
| File size class | `medium_1_to_10_mib` from prior soak reports |
| Row count estimate | 20,219 from prior soak reports |
| Original fixture mutation | No |
| Fixture committed | No |

The report intentionally excludes raw file names, absolute paths, CSV contents, DB URLs, tokens, anon keys, service role values, JWTs, authorization headers, and credential-bearing strings.

## Preconfigured Settings Check

| Required item | Process env | App settings | QA result |
| --- | --- | --- | --- |
| Supabase DB URL | Missing | Missing | Blocked |
| Supabase anon/auth key | Missing | Missing | Blocked |
| Supabase Edge URL | Missing | Present | Partially ready |
| Source CSV/config path | Missing | Missing | Blocked |
| State DB/config path | Missing | Present | Ready |

The QA rules prohibit requesting, extracting, or printing secret values. Because required preconfigured values were missing, the authenticated upload path stopped before any upload attempt.

## Runtime Checks

| Check | Result |
| --- | --- |
| API port | Unreachable |
| Studio port | Unreachable |
| DB TCP port | Unreachable |
| Docker daemon status | Unavailable |
| Edge no-auth route | `000`, unreachable |
| Edge authenticated route | Not executed |

The local runtime was not made available during this pass. No destructive Docker or database operation was attempted to change that state.

## Upload Job Smoke

| Scenario | Result |
| --- | --- |
| Preconfigured env/app settings presence | Failed, `preconfigured_env_missing` |
| Local Supabase runtime reachable | Failed, runtime unavailable |
| Edge authenticated route reachable | Not executed |
| Preview run for upload target check | Not executed |
| Safe minimal sample preparation | Not executed |
| Upload Job start | Not executed |
| Upload Job status/progress | Not verified |
| Uploaded rows | Not verified |
| Inserted rows | Not verified |
| Duplicate rerun row count behavior | Not verified |
| `job_events` persistence | Not verified |
| SSE replay | Not verified |
| Exact keys presence | Not verified |
| `/api/audit?action=upload.start` | Not verified |

Blocking reason: real Upload Job execution requires a configured Edge URL plus anon/auth key, and exact key verification requires a configured DB connection. The current process/app configuration did not provide the required secret-bearing values through approved preconfigured channels.

## Redaction Checks

| Check | Result |
| --- | --- |
| Secret values printed to console | Not observed |
| Secret values written to report | Absent |
| Raw operational fixture filename in report | Absent |
| Raw operational fixture path in report | Absent |
| CSV contents in report | Absent |
| DB URL in report | Absent |
| Token/key/service role/JWT in report | Absent |
| Authorization header in report | Absent |
| Raw upload audit params | Not applicable, authenticated upload not executed |

Secret-bearing local Supabase status/config output was intentionally not collected.

## HTTP Smoke

HTTP smoke used temporary backend and Vite dev servers with a temporary state DB. The temporary processes were stopped after the smoke pass.

| Smoke | Result |
| --- | --- |
| Backend health on temporary port | `200` |
| Backend audit API on temporary port | `200` |
| Vite app root on temporary port | `200` |
| Upload page on temporary port | `200` |
| Logs page on temporary port | `200` |

Browser screenshot QA was not completed in this pass. HTTP smoke was used as the non-destructive substitute.

## Validation

| Check | Result |
| --- | --- |
| Targeted Upload Job/Audit backend tests | Passed, 43 tests |
| Full backend tests | Passed, 130 tests |
| `npm run typecheck` | Passed |
| `npm run build` | Passed |
| `git diff --check` | Passed |

Warnings observed:

- Existing FastAPI/Starlette `TestClient` deprecation warning.
- Existing HTTP 422 deprecation warning.
- Existing pytest cache write warning under repository `.pytest_cache`; tests used `--basetemp` under `C:\tmp`.

## Findings

### Blocker: preconfigured authenticated Edge environment missing

The required DB URL, anon/auth key, and source directory were not present through approved preconfigured channels. Per the QA rule, the pass did not request, extract, or print secret values and stopped at `preconfigured_env_missing`.

### Blocker: local Supabase runtime unavailable

Local Supabase API, Studio, DB TCP, Docker daemon, and Edge route were unavailable in this pass. The authenticated route could not be reached or exercised.

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

1. Start from branch `codex/upload-job-real-supabase-edge-auth-ready-smoke`.
2. Keep `integrated_plc_operational_fixture` untracked and read-only.
3. Run presence-only checks for required process env and app settings.
4. Observe missing DB URL, anon/auth key, and source directory.
5. Check local Supabase runtime ports and Edge route without printing secret-bearing output.
6. Observe runtime unavailable and Edge route unreachable.
7. Stop before authenticated upload because the approved preconfigured environment is incomplete.

## Merge Readiness

This PR is mergeable only as a report-only artifact documenting the current QA blocker.

It is not evidence that real Edge Upload Job execution is production-ready. The next pass should run after the operator environment has DB URL, anon/auth key, Edge URL, source directory, state DB path, local Supabase runtime, and Edge runtime already configured and reachable through approved channels. The test runner should still print only presence, status codes, counts, and redacted summaries.

Recommended follow-up branch:

`codex/upload-job-real-supabase-edge-auth-ready-env-smoke`

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
