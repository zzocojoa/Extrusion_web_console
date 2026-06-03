# Upload Preview Large CSV Soak QA

Status: report-only QA for branch `codex/upload-preview-large-csv-soak`

Date: 2026-06-03

Scope: Upload Preview reconciliation soak for `integrated_plc_large_sample`

## Summary

Upload Preview was exercised against `integrated_plc_large_sample` using read-only source access through temporary copies. The original operational sample was not modified, and no feature code was changed.

The large-sample Preview path completed successfully in a controlled DB-reachable reconciliation run and produced consistent results on repeat. The controlled DB-unreachable run produced a `partial_failed` Preview with a `db_unreachable` reason and did not mark DB-dependent rows as upload targets.

No merge blocker was found in this report-only QA pass.

## Environment

| Item | Result |
| --- | --- |
| Backend | FastAPI local test/runtime |
| Frontend | React/Vite local dev server smoke |
| State store | Temporary SQLite state DBs for soak runs |
| Data label | `integrated_plc_large_sample` |
| Source access | Temporary copy, original sample unchanged |
| DB reachable mode | Controlled exact reconciler returning no existing keys |
| DB unreachable mode | Controlled exact reconciler raising DB unavailable |

The QA intentionally avoids publishing raw file names, absolute paths, CSV contents, DB URLs, tokens, keys, or credential-bearing strings.

## Test Data

| Metric | Result |
| --- | --- |
| Sanitized label | `integrated_plc_large_sample` |
| File size class | `medium_1_to_10_mib` |
| Row count estimate | 20,219 |
| Candidate file count | 1 |
| Sources | PLC |
| Date range mode | Custom range matching the sample date |

## Service Soak Results

### DB Reachable Run

| Metric | Result |
| --- | --- |
| Run status | `succeeded` |
| DB status | `reachable` |
| Candidate files | 1 |
| Target count | 1 |
| Already in DB count | 0 |
| Partial overlap count | 0 |
| Risky count | 0 |
| Excluded count | 0 |
| Upload row estimate | 20,219 |
| DB matched rows | 0 |
| First item status | `target` |
| First item reason | `db_no_match` |
| Preview duration | 60.86 seconds |
| Python allocation peak | 5.08 MiB |
| Timeout | No |
| Audit row created | Yes |
| Audit redaction | Passed |

### DB Unreachable Run

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
| Upload row estimate | 0 |
| DB matched rows | 0 |
| First item status | `risky` |
| First item reason | `db_unreachable` |
| Preview duration | 63.06 seconds |
| Python allocation peak | 5.08 MiB |
| Timeout | No |
| Audit row created | Yes |
| Audit redaction | Passed |

### Repeated Run

| Metric | Result |
| --- | --- |
| Run status | `succeeded` |
| DB status | `reachable` |
| Candidate files | 1 |
| Target count | 1 |
| Upload row estimate | 20,219 |
| DB matched rows | 0 |
| First item row count | 20,219 |
| Preview duration | 59.06 seconds |
| Python allocation peak | 5.08 MiB |
| Timeout | No |
| Count consistency | Passed |
| Audit redaction | Passed |

## API Smoke Results

FastAPI route smoke used a temporary state DB and the same sanitized large-sample setup.

| Endpoint | Result |
| --- | --- |
| `POST /api/upload/preview` | `202` |
| `GET /api/upload/preview/{id}` | terminal `succeeded` |
| `GET /api/upload/preview/latest?completedOnly=true` | `200` |
| `GET /api/audit?action=upload.preview&limit=5` | `200` |
| API route duration | 53.95 seconds |
| API summary total | 1 |
| API summary target | 1 |
| API summary upload rows | 20,219 |
| API audit row count | 1 |
| API audit redaction | Passed |

## Redaction Checks

Audit params were checked for forbidden raw values after reachable, unreachable, repeat, and API smoke runs.

| Check | Result |
| --- | --- |
| Raw operational sample name absent from audit params | Passed |
| Raw source path absent from audit params | Passed |
| DB URL absent from audit params | Passed |
| Token-like value absent from audit params | Passed |
| Bearer/authorization value absent from audit params | Passed |
| `anon`/`service_role` terms absent from audit params | Passed |
| Malformed raw body exposure | Not applicable to this soak path |

Audit params remained limited to safe summary data such as `previewRunId`, counts, `dbStatus`, `reasonCode`, and requested filter metadata.

## UI And HTTP Smoke

Existing local servers were detected and no new server was started.

| Smoke | Result |
| --- | --- |
| Vite app root | `200` |
| Backend health | `200` |
| Upload page | `200` |
| Logs page | `200` |
| Backend audit API | `200` |
| Vite proxy audit API | `200` |
| Backend latest preview API | `404`, no existing persisted preview in the running app |
| Vite proxy latest preview API | `404`, no existing persisted preview in the running app |

Browser screenshot QA was not completed because the browser automation kernel failed before screenshot capture. HTTP smoke was used as the non-destructive substitute.

## Validation

| Check | Result |
| --- | --- |
| Targeted Upload Preview backend tests | Passed, 45 tests |
| Full backend tests | Passed |
| `npm run typecheck` | Passed |
| `npm run build` | Passed |
| `git diff --check` | Passed |

The first targeted pytest attempt failed due to local pytest temp/cache permissions. Re-running with a temp base under `C:\tmp` passed.

## Findings

No functional merge blocker was found.

The main observation is performance: each controlled large-sample Preview run took roughly 59 to 63 seconds for about 20k rows, with low observed Python allocation peak. This stayed inside the configured 900 second run budget and 300 second file budget, but it is long enough that operator-facing progress, cancellation, and timeout handling remain important for larger production samples.

## Limitations

- This QA did not connect to a real local Supabase instance. DB-reachable and DB-unreachable states were controlled reconciliation paths.
- Browser screenshot QA was not completed because the browser automation kernel failed before capture.
- The local running app had no existing persisted Preview row during HTTP smoke, so latest Preview endpoints returned `404`.
- Large operator CSV soak covered Preview reconciliation only. Upload Job execution, Retry, SSE, and actual Edge upload were not part of this pass.
- No destructive DB reset, container cleanup, volume deletion, or source data mutation was performed.

## Merge Readiness

This report-only QA branch is merge-ready as a documentation artifact if reviewers accept the controlled DB reconciliation approach and the browser screenshot limitation.

Recommended follow-up branch:

`codex/upload-preview-real-supabase-soak`

That branch should run the same sanitized large-sample Preview against a real operator local Supabase environment and capture browser screenshots once automation is available.
