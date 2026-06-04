# Upload Job Real Local Supabase Auth-Ready Env Smoke QA

Status: report-only QA for branch `codex/upload-job-real-supabase-edge-auth-ready-env-smoke`

Date: 2026-06-04

Scope: authenticated Upload Job smoke readiness using the PR #15 environment checklist and `integrated_plc_operational_fixture`

## Summary

Authenticated Upload Job real Edge smoke was attempted without feature code changes. The original operational fixture was not modified, and the untracked fixture was not staged.

The PR #15 readiness checklist did not pass. Required preconfigured DB URL, anon/auth key, and source path were still missing through approved local channels. Local Supabase API, Studio, DB TCP, Docker daemon, and Edge route were also unavailable.

Result: this pass stopped before authenticated upload with `preconfigured_env_missing` and `runtime_unavailable`.

## Environment

| Item | Result |
| --- | --- |
| Backend | FastAPI local test/runtime |
| Frontend | React/Vite HTTP smoke |
| Data label | `integrated_plc_operational_fixture` |
| Source access | No source content emitted; original fixture untouched |
| Checklist status | Failed |
| Process env DB URL | Missing |
| Process env Edge URL | Missing |
| Process env Supabase URL | Missing |
| Process env anon/auth key | Missing |
| Process env source directory | Missing |
| Process env state DB path | Missing |
| Process env config file path | Missing |
| Settings DB URL | Missing |
| Settings Edge URL | Present |
| Settings anon/auth key | Missing |
| Settings PLC source directory | Missing |
| Settings temperature source directory | Missing |
| Settings state DB path | Present |
| Settings config file path | Present |
| Local Supabase API | Unreachable |
| Local Supabase Studio | Unreachable |
| Local Supabase DB TCP | Unreachable |
| Docker daemon | Unavailable |
| Edge route no-auth smoke | `000`, route unreachable |
| Edge authenticated route smoke | Not executed |

No DB reset, DB cleanup, DB delete, Docker volume deletion, Docker container deletion, or Docker prune was performed.

## Test Data

| Metric | Result |
| --- | --- |
| Sanitized label | `integrated_plc_operational_fixture` |
| File class | `integrated_plc_csv` |
| Sample class | Not prepared |
| Sample row count | Not applicable |
| Original fixture mutation | No |
| Fixture committed | No |

The report intentionally excludes raw file names, absolute paths, CSV contents, DB URLs, auth keys, service role values, JWTs, tokens, Authorization headers, and credential-bearing strings.

## Readiness Checklist Result

| Checklist item | Result |
| --- | --- |
| Docker Desktop running | Failed |
| Local Supabase API reachable | Failed |
| Local Supabase Studio reachable | Failed |
| Local Supabase DB TCP reachable | Failed |
| Edge runtime running | Failed, not reachable |
| Edge route no-auth reachable | Failed, `000` |
| Required env/app settings present | Failed |
| `GET /api/config` secret hidden check | Not executed against configured secrets because required secrets are missing |
| Backend actual head check | Passed in local git; backend HTTP smoke used current branch |
| Vite proxy to backend | Passed in temporary API-mode smoke |
| Operational fixture untracked | Passed |
| Minimal sample strategy safe | Not reached |
| Duplicate-safe verification plan | Not executed |
| Audit verification plan | Not executed |
| SSE verification plan | Not executed |

Stop conditions reached:

- `preconfigured_env_missing`
- `runtime_unavailable`

## Upload Job Smoke

| Scenario | Result |
| --- | --- |
| Edge authenticated route reachable | Not executed |
| Preview run for upload target | Not executed |
| Safe minimal sample preparation | Not executed |
| Upload Job start | Not executed |
| Upload Job status/progress | Not verified |
| Uploaded rows | Not verified |
| Inserted rows | Not verified |
| Duplicate rerun row count behavior | Not verified |
| `job_events` persistence | Not verified |
| SSE full replay | Not verified |
| SSE `afterSeq` replay | Not verified |
| Exact key presence in `all_metrics` | Not verified |
| `/api/audit?action=upload.start` | Not verified for real Edge job |

Blocking reason: real Upload Job execution requires preconfigured DB URL, Edge URL, anon/auth key, source path, state/config path, reachable local Supabase runtime, and reachable Edge route. The approved preconfigured channels did not provide those prerequisites in this pass.

## Redaction Checks

| Check | Result |
| --- | --- |
| Secret values printed to console | Not observed |
| Secret values written to report | Absent |
| Raw operational fixture filename in report | Absent |
| Raw operational fixture path in report | Absent |
| CSV contents in report | Absent |
| DB URL in report | Absent |
| Auth key/service role/JWT/token in report | Absent |
| Authorization header in report | Absent |
| Raw upload audit params | Not applicable, authenticated upload not executed |

Secret-bearing local Supabase status/config output was intentionally not collected.

## HTTP Smoke

HTTP smoke used temporary backend and Vite dev servers with a temporary state DB and API-mode frontend. The temporary processes were stopped after the smoke pass.

| Smoke | Result |
| --- | --- |
| Backend health on temporary port | `200` |
| Backend audit API on temporary port | `200` |
| Backend config API on temporary port | `200` |
| Vite app root on temporary port | `200` |
| Upload page on temporary port | `200` |
| Logs page on temporary port | `200` |
| Vite proxy audit API | `200` |

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

Required DB URL, anon/auth key, and source path were not present through approved local channels. The pass did not request, extract, print, or document secret values.

### Blocker: local runtime unavailable

Local Supabase API, Studio, DB TCP, Docker daemon, and Edge route were unavailable. The Edge no-auth route returned `000`, so authenticated route smoke could not proceed.

### Remaining unverified items

- Start Upload through `POST /api/upload/jobs`.
- Preview run for safe target rows.
- safe minimal sample upload.
- duplicate-safe Edge upsert behavior.
- uploaded and inserted row reporting.
- exact key presence after upload.
- duplicate rerun row count stability.
- persisted `job_events`.
- SSE full replay and `afterSeq` replay.
- `/api/audit?action=upload.start`.
- upload audit/log redaction for a real Edge job.

## Reproduction Conditions

1. Start from branch `codex/upload-job-real-supabase-edge-auth-ready-env-smoke`.
2. Keep `integrated_plc_operational_fixture` untracked and read-only.
3. Run PR #15 presence-only readiness checks.
4. Observe missing DB URL, anon/auth key, and source path.
5. Check local Supabase runtime ports and Edge route without printing secret-bearing output.
6. Observe local runtime unavailable and Edge route `000`.
7. Stop before authenticated upload per checklist.

## Merge Readiness

This PR is mergeable only as a report-only artifact documenting the current environment blocker.

It is not evidence that real Edge Upload Job execution is production-ready. The next pass should run after the operator environment has all required preconfigured values present and local Supabase runtime reachable through the PR #15 checklist.

Recommended follow-up branch:

`codex/upload-job-real-supabase-edge-auth-ready-env-smoke-rerun`

Follow-up should verify:

- PR #15 readiness checklist passes.
- `POST /api/upload/jobs` from a safe target preview.
- terminal Upload Job status and progress.
- uploaded/inserted row counts.
- duplicate rerun row count does not increase.
- exact key presence in `all_metrics`.
- persisted `job_events`.
- SSE full replay and `afterSeq` replay.
- `/api/audit?action=upload.start`.
- audit/log/report redaction.
