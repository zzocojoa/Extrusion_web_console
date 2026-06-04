# Upload Job Real Local Supabase Auth-Ready Env Rerun QA

Status: report-only QA for branch `codex/upload-job-real-supabase-edge-auth-ready-env-smoke-rerun`

Date: 2026-06-04

Scope: authenticated Upload Job smoke rerun after PR #15 readiness checklist preparation

## Summary

Authenticated Upload Job real local Supabase Edge smoke was rerun without feature code changes.

The PR #15 readiness gate passed for the required PLC smoke path. Local Supabase API, Studio, DB TCP, and Edge runtime were reachable. Required DB URL, Edge URL, Supabase URL, anon/auth key, PLC source directory, and state DB path were present through local-only configuration. Secret values were not printed or documented.

The real Upload Preview API classified the operational PLC sample as already represented in DB. To avoid full operational upload and still verify authenticated Edge upload behavior, the smoke used a minimal temporary duplicate-safe sample derived from the operational fixture. The original fixture was read-only, the temporary sample was removed after the run, and no fixture or temp file was staged.

## Environment

| Item | Result |
| --- | --- |
| Backend | FastAPI local runtime |
| Frontend | React/Vite API-mode HTTP smoke |
| Data label | `integrated_plc_operational_fixture` |
| Upload sample label | `integrated_plc_minimal_duplicate_sample` |
| Checklist status | Passed |
| Supabase DB URL presence | Present |
| Supabase Edge URL presence | Present |
| Supabase URL presence | Present |
| Supabase anon/auth key presence | Present |
| PLC source directory presence | Present |
| State DB path presence | Present |
| Temperature source directory presence | Missing, not required for PLC-only smoke |
| Config file env presence | Missing, default app config path was present |
| Local Supabase API | Reachable |
| Local Supabase Studio | Reachable |
| Local Supabase DB TCP | Reachable |
| Edge runtime | Running |
| Edge route no-auth smoke | `401`, route reachable and auth required |
| `GET /api/config` secret hidden check | Passed, configured secret values hidden |

No DB reset, DB cleanup, DB delete, Docker volume deletion, Docker container deletion, Docker prune, migration repair, or feature code change was performed.

## Test Data

| Metric | Result |
| --- | --- |
| Sanitized fixture label | `integrated_plc_operational_fixture` |
| Fixture class | `integrated_plc_csv` |
| Minimal sample class | `integrated_plc_minimal_duplicate_sample` |
| Minimal sample row count | 12 |
| Original fixture mutation | No |
| Full operational fixture upload | No |
| Temporary sample cleanup | Removed after smoke |
| Fixture committed | No |

The report intentionally excludes raw file names, absolute paths, CSV contents, row contents, DB URLs, auth keys, service role values, JWTs, tokens, Authorization headers, and credential-bearing strings.

## Preview Result

The real Upload Preview API was executed against the configured PLC source using a narrow date filter and one candidate file limit.

| Metric | Result |
| --- | --- |
| Preview status | `succeeded` |
| DB status | `reachable` |
| Target files | 0 |
| Already in DB files | 1 |
| Partial overlap files | 0 |
| Risky files | 0 |
| Excluded files | 0 |
| Upload row estimate | 0 |
| DB matched rows | 20,219 |

Interpretation: the real operational sample is not an upload target because its exact keys are already represented in local Supabase. The authenticated upload smoke therefore used a controlled minimal duplicate-safe target sample instead of uploading the full operational fixture.

## Upload Job Smoke

| Scenario | Result |
| --- | --- |
| Edge authenticated upload route | Verified through `POST /api/upload/jobs` job execution |
| Controlled target preview setup | Succeeded |
| First Upload Job terminal status | `succeeded` |
| First Upload Job uploaded rows | 12 |
| First Upload Job Edge reported accepted/upserted rows through legacy `insertedRows` | 12 |
| First Upload Job succeeded files | 1 |
| First Upload Job failed files | 0 |
| Duplicate rerun terminal status | `succeeded` |
| Duplicate rerun uploaded rows | 12 |
| Duplicate rerun Edge reported accepted/upserted rows through legacy `insertedRows` | 12 |
| Duplicate rerun succeeded files | 1 |
| Duplicate rerun failed files | 0 |

Exact key count checks:

| Check | Count |
| --- | --- |
| Before first upload | 12 |
| After first upload | 12 |
| After duplicate rerun | 12 |
| Duplicate rerun DB row count delta | 0 |

Interpretation: duplicate-safe DB behavior passed. The same exact keys remained at 12 rows after both uploads, so the duplicate rerun did not increase `all_metrics` row count.

Observed limitation at the time of this QA: the Edge response reported legacy `insertedRows=12` for duplicate rows even though exact DB row count did not increase. PR #19 resolved the operator-facing naming risk by adding canonical `acceptedRows` for Edge/Supabase upsert-accepted rows and keeping `insertedRows` only as a deprecated compatibility alias. This remains not evidence of duplicate DB insertion in this run.

## Events And SSE

| Check | First upload | Duplicate rerun |
| --- | --- | --- |
| Latest event sequence | 6 | 6 |
| Persisted job events | Present |
| SSE full replay event count | 6 | 6 |
| SSE `afterSeq` replay event count | 1 | 1 |
| Terminal event present | Yes | Yes |

SSE replay passed for both full replay and `afterSeq` replay without requiring browser refresh or raw event body capture.

## Audit And Redaction

| Check | Result |
| --- | --- |
| `/api/audit?action=upload.start` row exists | Yes |
| Recent upload.start audit rows checked | 2 |
| Audit params raw marker leak count | 0 |
| Vite proxy audit API | `200` |
| Secret values written to report | Absent |
| Raw operational fixture filename in report | Absent |
| Raw operational fixture path in report | Absent |
| CSV contents in report | Absent |
| DB URL in report | Absent |
| Auth key/service role/JWT/token in report | Absent |
| Authorization header in report | Absent |

Audit params were checked for raw secret/path markers without recording the params body in this report.

## HTTP Smoke

| Smoke | Result |
| --- | --- |
| Backend health | `200` |
| Vite app root | `200` |
| Upload page | `200` |
| Logs page | `200` |
| Vite proxy audit API | `200` |
| Page/proxy sampled secret marker count | 0 |

Browser screenshot QA was not performed in this pass. HTTP smoke was used as the non-destructive UI/API reachability substitute.

## Validation

| Check | Result |
| --- | --- |
| Targeted Upload Job/Audit backend tests | Passed, 43 tests |
| Full backend tests | Passed, 130 tests |
| `npm run typecheck` | Passed |
| `npm run build` | Passed |
| `git diff --check` | Pending at report creation |

Test isolation note: the local `.env` required for authenticated smoke makes missing-config contract tests see configured upload auth. For automated backend tests, `.env` was temporarily moved to a local temp backup and restored immediately after each test run. Secret values were not printed.

Warnings observed:

- Existing FastAPI/Starlette `TestClient` deprecation warning.
- Existing HTTP 422 deprecation warning.
- Existing pytest cache write warning under repository `.pytest_cache`.

## Findings

### Passed: readiness blocker cleared

The previous `preconfigured_env_missing` and `runtime_unavailable` blockers were cleared for this local PLC smoke path.

### Passed: authenticated upload and duplicate-safe rerun

Two authenticated Upload Jobs reached `succeeded`. Exact key row count did not increase after the duplicate rerun.

### Resolved follow-up: Edge accepted row reporting semantics

PR #19 clarified the web app semantics: `acceptedRows` is the canonical field and label for Edge/Supabase upsert-accepted rows. It is not a net-new insert count, so duplicate reruns can have DB row count delta `0` while `acceptedRows` remains positive. The legacy `insertedRows` field remains only as a deprecated v1 compatibility alias.

### Follow-up: browser screenshot QA

Upload Job and Audit Logs browser screenshot QA remains a follow-up. This pass verified HTTP reachability and API behavior but did not capture screenshots.

## Reproduction Conditions

1. Prepare local Supabase runtime and local-only env/app settings using PR #15 readiness checklist.
2. Keep the operational PLC fixture untracked and read-only.
3. Run presence-only readiness checks; record only `present` or `missing`.
4. Verify local Supabase API, Studio, DB TCP, and Edge route reachability without printing secret-bearing output.
5. Run real Upload Preview API against the configured PLC source and record only status/counts.
6. Prepare a minimal duplicate-safe temp sample from the operational fixture.
7. Start Upload Job from a controlled target preview using the minimal sample.
8. Wait for terminal job status.
9. Verify persisted job events and SSE replay.
10. Repeat upload with the same exact keys and confirm DB row count does not increase.
11. Verify `/api/audit?action=upload.start` and redaction markers.

## Merge Readiness

This PR is mergeable as a report-only QA artifact.

It does not change feature code and does not prove large full-file authenticated upload soak behavior. PR #19 later clarified Edge accepted/upserted row semantics so operators no longer see the legacy inserted-row wording in Upload Job UI.

Completed follow-up:

`codex/upload-edge-accepted-rows-ui-api`
