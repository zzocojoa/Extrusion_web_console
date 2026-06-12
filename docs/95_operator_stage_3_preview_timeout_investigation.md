# Operator Stage 3 Preview Timeout Investigation

## Summary

- Date: 2026-06-13
- Branch: `codex/operator-stage-3-preview-timeout-investigation`
- Investigation mode: read-only state DB, code, config, and test inspection
- Source label: `profile_a_corrected_bounded_source`
- Stage: Stage 3 Profile A Preview reference recovery
- Related PR: `#109`
- Related PR head: `52a2b1a23d46385cac7fbdb16bd40a90466af93b`
- Upload Preview executions during this investigation: `0`
- Start Upload executions during this investigation: `0`
- Retry Failed executions: `0`
- Duplicate rerun executions: `0`
- Edge authenticated upload calls: `0`
- Full operational dataset rollout: not performed
- Investigation verdict: `root_cause_found`

The failed Preview reference recovery did not time out in DB reconciliation,
repository writes, API polling, Edge runtime, or target-class preflight. It
timed out during CSV key extraction for the corrected bounded source.

The immediate trigger was the recovery request's per-file limit:
`maxFileSeconds=30` with `forceFullScan=true` against a `24515`-row Profile A
source. The active state DB item records `reason_code=timeout` and the safe
error class `CSV key extraction timed out`; `dbStatus` stayed `not_checked`
because the DB reconciliation stage was never reached.

## Explicitly Not Performed

- Upload Preview rerun;
- Start Upload;
- Retry Failed;
- duplicate rerun or forced duplicate upload;
- manual Edge authenticated upload call;
- full operational dataset rollout;
- Supabase init, bootstrap, start, stop, or reset;
- DB migration, reset, delete, cleanup, prune, drop, or truncate;
- Docker volume, container, image, or network deletion;
- operational source mutation or deletion;
- production deploy;
- GitHub Release or tag creation;
- feature branch deletion.

## Timeout Failure Summary

| Metric | Result |
| --- | ---: |
| Failed recovery Preview final status | `timed_out` |
| Failed recovery `dbStatus` | `not_checked` |
| Failed recovery total files | `1` |
| Failed recovery target files | `0` |
| Failed recovery upload target rows | `0` |
| Failed recovery risky files | `1` |
| Failed recovery excluded files | `0` |
| Failed recovery DB matched rows | `0` |
| Failed recovery reason class | `timeout` |
| Failed recovery item safe error class | `CSV key extraction timed out` |
| Preview executions during investigation | `0` |
| Start Upload executions during investigation | `0` |

The failure signature is consistent with a per-file CSV extraction timeout. It
is not consistent with a DB reconciliation timeout, because no DB matched rows
were recorded and the run DB status remained `not_checked`.

## Active State DB Evidence

Read-only inspection of the active backend state DB shows two Preview runs:

| Run class | Status | DB status | Total files | Target files | Risky | Excluded | DB matched rows |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Previous blocked Preview | `succeeded` | `reachable` | `3` | `0` | `0` | `2` | `20219` |
| Recovery Preview | `timed_out` | `not_checked` | `1` | `0` | `1` | `0` | `0` |

Recovery Preview item evidence:

| Field | Result |
| --- | --- |
| Item status | `risky` |
| Reason class | `timeout` |
| Scan mode | `incomplete` |
| Sample row count | `0` |
| Persisted row count | `0` |
| Local key count | `0` |
| DB match count | `0` |
| Upload row estimate | `0` |
| Safe error class | `CSV key extraction timed out` |

The persisted row counters are `0` because the timeout path writes an error item
without a partial `KeyExtractionResult`. That is an observability limitation,
not proof that the file contained no rows.

## Request Option Difference

The active state DB records a material option difference between the older
state run and the failed recovery run:

| Option | Older state run | Failed recovery run |
| --- | ---: | ---: |
| `forceFullScan` | `true` | `true` |
| `maxFileSeconds` | `120` | `30` |
| `maxRunSeconds` | `300` | `120` |
| `chunkRows` | `20000` | `20000` |
| `maxFiles` | `3` | `3` |
| `stableLagMinutes` | `0` | `0` |

The failed recovery used the default per-file timeout. That is too tight for
this corrected Profile A full-scan source under the observed local runtime.

## Code Path Classification

The timeout path is in `backend/app/services/upload_preview.py`:

| Stage | Evidence | Classification |
| --- | --- | --- |
| Source scan | Candidate exists, total files `1`, no `file_date_missing` | Passed |
| CSV key extraction | `CsvKeyExtractor.extract` raises `TimeoutError` when elapsed file time exceeds `max_file_seconds` | Failed |
| DB exact-key reconciliation | `ExactReconciler.find_existing_keys` was not reached for this item | Not reached |
| Repository summary write | Summary recomputed from one risky timeout item | Completed |
| API request/polling | Preview run reached terminal `timed_out` state | Not the timeout source |

Relevant code behavior:

- `PreviewOptions.max_file_seconds` defaults to `30`.
- `PreviewOptions.max_run_seconds` defaults to `120`.
- Frontend default Preview options also use `maxFileSeconds=30` and
  `maxRunSeconds=120`.
- `PreviewService.run_preview` creates a run-level deadline from
  `max_run_seconds`.
- `CsvKeyExtractor.extract` separately checks elapsed per-file time against
  `max_file_seconds`.
- A `TimeoutError` from extraction is caught around the candidate loop, inserted
  as a `risky/timeout` item, and later finishes the run as `timed_out` with
  `dbStatus=not_checked`.

## `dbStatus=not_checked` Explanation

`dbStatus=not_checked` is expected for this failure class.

The code sets `dbStatus=not_checked` when a Preview times out before any DB
unreachable condition is observed. DB reconciliation only sets DB-related
evidence after key extraction produces local exact keys. In this recovery run,
CSV extraction timed out before local keys were available, so DB reconciliation
did not run.

Independent DB read-only count was still reachable after the failure. The DB row
count remained `20225`, matching the prior non-mutation evidence.

## DB Non-Mutation Evidence

| Check | Result |
| --- | ---: |
| Independent DB reachable during investigation | yes |
| DB row count after failed recovery Preview | `20225` |
| Upload jobs in active state | `0` |
| `upload.start` audit rows in active state | `0` |
| Start Upload during investigation | `0` |

Preview timeout did not mutate the independent DB.

## Root Cause Candidates

| Candidate | Status | Rationale |
| --- | --- | --- |
| CSV key extraction exceeded per-file timeout | confirmed | State item has `risky/timeout` and safe error class `CSV key extraction timed out`; request had `maxFileSeconds=30`. |
| DB reconciliation timeout | weakened | `dbStatus=not_checked`, `db_match_count=0`, and extraction timeout happened before reconciliation. |
| DB/Edge target mismatch | weakened | PR #109 preflight passed target-class alignment and Edge no-auth auth-class. |
| Edge runtime failure | weakened | Preview reconciliation is direct DB-backed; no Edge authenticated call was made. |
| Source file-date metadata problem | disproven for recovery run | Corrected source recheck passed and latest recovery run had `file_date_missing=0`. |
| API client request timeout | weakened | Backend state reached terminal `timed_out`; this is a service-level terminal result, not only client polling. |
| Repository write failure | weakened | Preview run and item were persisted and summarized correctly. |
| Runtime load/performance variation | plausible contributor | A `24515`-row full scan exceeded the default 30-second per-file budget in this run, while earlier evidence used broader timeout budgets. |

Root cause hypothesis:

```text
The recovery procedure used the default per-file Preview timeout while forcing
full CSV key extraction. For the corrected Profile A source, local CSV key
extraction exceeded that 30-second file budget before DB reconciliation could
begin, producing `timed_out / dbStatus=not_checked / target=0 / risky=1`.
```

## No-Rerun Rationale

Preview rerun is not allowed in this investigation. PR #109 already consumed
the approved recovery Preview execution exactly once. A second Preview would
violate the recovery QA constraint and could overwrite the current evidence.

Start Upload is also not allowed because the active state DB still lacks a
`succeeded`, `dbStatus=reachable`, `target=1`, `uploadRows=24515` Preview
reference.

## Next Safe Action

Recommended next action: separate procedure or fix PR before another recovery
attempt.

Safe options to evaluate in that next PR:

1. Procedure-only: explicitly approve a new Preview-only recovery attempt using
   the same corrected bounded source but a larger bounded timeout budget, for
   example the previously recorded `maxFileSeconds=120` and `maxRunSeconds=300`
   class.
2. Code/UX fix: add a Stage 3/operator Preview preset or server-side guard so
   full-scan bounded batches cannot accidentally use the default 30-second
   per-file budget.
3. Observability fix: preserve partial extraction progress on timeout, or add a
   safe timeout stage field so future reports can distinguish file scan, CSV
   extraction, DB reconciliation, and repository stages without reading raw
   source metadata.

Do not run Preview again until the next recovery attempt is explicitly approved.
Do not run Start Upload until a corrected uploadable Preview reference exists in
the same active backend state DB.

## Redaction Result

| Check | Result |
| --- | --- |
| Raw source path recorded | no |
| Raw source filename recorded | no |
| Raw source content recorded | no |
| Row content recorded | no |
| Full local path recorded | no |
| Raw DB URL recorded | no |
| Token, Authorization header, or JWT recorded | no |
| Operational source modified | no |

## Validation

| Command or check | Result |
| --- | --- |
| Active state DB read-only inspection | passed |
| Code path inspection | passed |
| Upload Preview execution count during investigation | `0` |
| Start Upload execution count during investigation | `0` |
| DB non-mutation read-only check | passed |
| Targeted backend upload preview tests | passed |
| Targeted runtime/config tests | passed |
| Targeted backend test total | `109` passed |
| `npm run typecheck` | passed |
| `npm run build:api` | passed |
| `npm run build` | passed |
| `git diff --check` | passed |
| New document marker scan | passed |
| PR file scope | passed, investigation report document only |
