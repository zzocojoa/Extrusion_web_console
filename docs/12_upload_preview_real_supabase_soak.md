# Upload Preview Real Local Supabase Soak QA

Status: report-only QA for branch `codex/upload-preview-real-supabase-soak`

Date: 2026-06-03

Scope: Upload Preview exact reconciliation against real local Supabase using `integrated_plc_operational_fixture`

## Summary

Upload Preview was exercised against `integrated_plc_operational_fixture` using read-only source access through temporary copies. The original operational fixture was not modified, and no feature code was changed.

The real local Supabase DB was reachable after starting the existing Docker Desktop daemon. No DB reset, cleanup, delete, prune, or container/volume deletion was performed. The Preview exact reconciliation path completed successfully and classified the fixture as `already_in_db`, with all extracted local keys matched in `public.all_metrics`.

No functional merge blocker was found in this report-only QA pass.

## Environment

| Item | Result |
| --- | --- |
| Backend | FastAPI local test/runtime |
| Frontend | React/Vite local dev server HTTP smoke |
| State store | Temporary SQLite state DBs for soak runs |
| Data label | `integrated_plc_operational_fixture` |
| Source access | Temporary copy, original fixture unchanged |
| Local Supabase API | Reachable |
| Local Supabase Studio | Reachable |
| Local Supabase DB | Reachable |
| Edge runtime | Stopped, not a Preview reconciliation blocker |
| Docker action | Existing Docker Desktop daemon started non-destructively |

Supabase CLI status output includes local keys and connection strings, so only sanitized runtime state is recorded here.

## Test Data

| Metric | Result |
| --- | --- |
| Sanitized label | `integrated_plc_operational_fixture` |
| File class | `integrated_plc_csv` |
| File size class | `medium_1_to_10_mib` |
| Row count estimate | 20,219 |
| Candidate file count | 1 |
| Sources | PLC |
| Date range mode | Custom range matching the fixture date |

## Local Supabase DB Checks

| Check | Result |
| --- | --- |
| DB TCP port | Reachable |
| `public.all_metrics` | Present |
| `all_metrics` row count | 13,568,232 |
| `(timestamp, device_id)` uniqueness | Present |
| Preview DB writes | None |
| DB destructive operation | None |

The reconciliation query used the existing exact-key Preview path. No latest-timestamp inference was used.

## Service Soak Results

### Real DB Reachable Run

| Metric | Result |
| --- | --- |
| Run status | `succeeded` |
| DB status | `reachable` |
| Candidate files | 1 |
| Target count | 0 |
| Already in DB count | 1 |
| Partial overlap count | 0 |
| Risky count | 0 |
| Excluded count | 0 |
| Row count | 20,219 |
| Local key count | 20,219 |
| DB matched rows | 20,219 |
| Upload row estimate | 0 |
| First item status | `already_in_db` |
| First item reason | `db_full_match` |
| Preview duration | 57.70 seconds |
| Python allocation peak | 18.84 MiB |
| Timeout | No |
| Audit row created | Yes |
| Audit redaction | Passed |

### Repeated Real DB Run

| Metric | Result |
| --- | --- |
| Run status | `succeeded` |
| DB status | `reachable` |
| Candidate files | 1 |
| Target count | 0 |
| Already in DB count | 1 |
| Partial overlap count | 0 |
| Risky count | 0 |
| Excluded count | 0 |
| Row count | 20,219 |
| Local key count | 20,219 |
| DB matched rows | 20,219 |
| Upload row estimate | 0 |
| First item status | `already_in_db` |
| First item reason | `db_full_match` |
| Preview duration | 59.02 seconds |
| Python allocation peak | 18.84 MiB |
| Timeout | No |
| Count consistency | Passed |
| Audit redaction | Passed |

### DB Unreachable Control Run

| Metric | Result |
| --- | --- |
| Run status | `partial_failed` |
| DB status | `unreachable` |
| Error code | `db_unreachable` |
| Candidate files | 1 |
| Target count | 0 |
| Already in DB count | 0 |
| Partial overlap count | 0 |
| Risky count | 1 |
| Excluded count | 0 |
| Row count | 20,219 |
| Local key count | 20,219 |
| DB matched rows | 0 |
| Upload row estimate | 0 |
| First item status | `risky` |
| First item reason | `db_unreachable` |
| Preview duration | 63.53 seconds |
| Python allocation peak | 9.28 MiB |
| Timeout | No |
| Audit row created | Yes |
| Audit redaction | Passed |

The DB unreachable run used a separate temporary backend configuration and did not stop or alter the real local Supabase stack.

## API Smoke Results

FastAPI route smoke used a temporary state DB, the real local Supabase DB, and the same sanitized fixture setup.

| Endpoint | Result |
| --- | --- |
| `POST /api/upload/preview` | `202` |
| `GET /api/upload/preview/{id}` | `200`, terminal `succeeded` |
| `GET /api/upload/preview/latest?completedOnly=true` | `200` |
| `GET /api/audit?action=upload.preview&limit=5` | `200` |
| API route duration | 52.28 seconds |
| API summary total | 1 |
| API summary target | 0 |
| API summary already in DB | 1 |
| API summary upload rows | 0 |
| API summary DB matched rows | 20,219 |
| API first item status | `already_in_db` |
| API first item reason | `db_full_match` |
| API audit row count | 1 |
| API audit redaction | Passed |

## Redaction Checks

Audit params were checked for forbidden raw values after real DB reachable, repeated, DB unreachable, and API smoke runs.

| Check | Result |
| --- | --- |
| Raw operational fixture name absent from audit params | Passed |
| Raw source path absent from audit params | Passed |
| DB URL absent from audit params | Passed |
| Token-like value absent from audit params | Passed |
| Bearer/authorization value absent from audit params | Passed |
| `anon`/`service_role` terms absent from audit params | Passed |
| Raw CSV content exposure | Not observed |
| Malformed raw body exposure | Not applicable to this soak path |

Audit params remained limited to safe summary data such as `previewRunId`, counts, `dbStatus`, `reasonCode`, and requested filter metadata.

## UI And HTTP Smoke

Existing local backend and Vite servers were already running and no new dev server was started.

| Smoke | Result |
| --- | --- |
| Vite app root | `200` |
| Upload page | `200` |
| Logs page | `200` |
| Backend health | `200` |
| Backend audit API for `upload.preview` | `200` |
| Vite proxy audit API for `upload.preview` | `200` |
| Backend latest preview API | `404`, no existing persisted preview in the running app state |
| Vite proxy latest preview API | `404`, no existing persisted preview in the running app state |

Browser screenshot QA was not completed because no usable browser automation tool was available in this session without installing new dependencies. HTTP smoke was used as the non-destructive substitute.

## Validation

| Check | Result |
| --- | --- |
| Targeted Upload Preview backend tests | Passed, 45 tests |
| Full backend tests | Passed, 130 tests |
| `npm run typecheck` | Passed |
| `npm run build` | Passed |
| `git diff --check` | Passed |

Warnings observed:

- FastAPI/Starlette `TestClient` deprecation warning.
- Existing pytest cache write warning under the repository `.pytest_cache`; tests were run with `--basetemp` under `C:\tmp`.
- Existing upload job HTTP 422 deprecation warnings.

These warnings did not fail the validation commands.

## Findings

No functional merge blocker was found.

The real DB result is operationally important: the fixture's 20,219 exact local keys all exist in `public.all_metrics`, so Preview correctly classified the candidate as `already_in_db` and estimated zero upload rows. The repeated run produced the same status and counts.

Performance remains a follow-up concern. Real DB Preview took about 52 to 59 seconds for the fixture in the reachable path and about 64 seconds in the DB-unreachable control path. This stayed inside the configured 900 second run budget and 300 second file budget, but larger operator samples should still be soaked before final legacy GUI replacement.

## Limitations

- Docker Desktop was initially not running. It was started to make the existing local Supabase stack reachable, without reset/delete/cleanup/prune.
- The Edge runtime was stopped during this Preview QA. That is not a direct blocker for Preview reconciliation, but it remains relevant for Upload Job execution.
- Browser screenshot QA was not completed because no browser automation package/tool was available without new dependency installation.
- The running dev backend had no persisted Preview history in its own state DB, so latest Preview HTTP smoke returned `404`. The API route smoke used a temporary state DB and returned `200` for latest after its run.
- This QA covered Preview reconciliation only. Upload Job execution, Retry, SSE, and Edge upload were not part of this pass.

## Merge Readiness

This report-only QA branch is merge-ready as a documentation artifact.

Recommended follow-up branch:

`codex/upload-job-real-supabase-edge-smoke`

That branch should verify Start Upload and Retry against the same local Supabase environment once Edge runtime is available.
