# Operator Retry / DB Delta Semantics Investigation

Date: 2026-06-17 Asia/Seoul

Scope: report-only P1 investigation for Retry Failed result counters, DB row
delta evidence, UI copy, audit/job evidence, and test coverage.

Verdict: `accepted_rows_db_delta_semantics_verified_with_row_level_caveat`

Match Rate: `96%`

## Summary

The P1 judgment is supported.

`docs/149_operator_post_dedupe_retry_db_delta_recheck.md` reconciles the
approved `863,419` unique target rows at the physical DB row-count level:

- pre-upload DB count: `1,884,281`;
- current DB count: `2,747,700`;
- total net-new physical DB rows: `863,419`;
- failed Start Upload partial DB delta: `2,000`;
- retry net-new physical DB rows after the partial insert: `861,419`;
- retry job `acceptedRows`: `861,420`.

The remaining caveat is real but bounded: the one-row difference between retry
`acceptedRows` and retry physical DB delta is not row-level attributed. Current
evidence explains the class of difference as upsert accepted count vs net-new
table growth, but it does not identify the exact key responsible for the
one-row non-growth.

This investigation did not execute Upload Preview, Start Upload, Retry Failed,
duplicate rerun, authenticated Edge call, full rollout, Settings save, DB reset,
Supabase/Docker lifecycle, or destructive work.

## Non-Developer Explanation

There are two different counters.

`acceptedRows` means "the upload system accepted this many rows for upsert."
That can include a row that updates or confirms an existing database key.

DB delta means "the database table physically grew by this many rows."

So `acceptedRows = 861,420` and DB delta `861,419` can both be true. It means
one accepted row did not increase the table row count. That is not evidence that
a row is missing. It is evidence that accepted/upsert counting and physical
table growth are different measurements.

No extra retry is approved by this finding.

## Root Cause Hypothesis

`aggregate_delta_reconciled_but_row_level_attribution_not_captured`

The retry execution and follow-up recheck reconciled aggregate DB counts, job
counters, dedupe event totals, and audit sequence. The evidence did not include
a row-level exact-key diff between retry accepted keys and net-new DB keys, so
the one-row accepted-vs-delta difference remains attributed by counter semantics
instead of by a specific `(timestamp, device_id)` key.

## Evidence Reviewed

| Evidence | Result |
| --- | --- |
| Product scope | Supabase upsert by `(timestamp, device_id)` remains final duplicate protection |
| README | `acceptedRows` is documented as Edge/Supabase upsert accepted count, not net-new insert count |
| `docs/146` | Retry executed exactly once and succeeded |
| `docs/149` | Direct read-only DB count reconciled `863,419` unique target rows |
| `docs/151` | Future Retry Failed requires remaining physical row review and separate approval |
| Backend service | Deduplicates before Edge call and tracks processed/uploaded/accepted separately |
| Backend repository | Retry job creation validates expected remaining physical rows inside `BEGIN IMMEDIATE` |
| Backend API | Missing/mismatched retry expected counts are blocked and audit logged |
| Frontend UI | Retry modal uses remaining physical rows as the typed retry confirmation gate |
| Tests | Targeted backend contract tests cover retry count blocking, acceptedRows alias, and dedupe |

## Code Semantics Review

### Upload Service

`backend/app/services/upload_jobs.py` separates three counters:

- `processed_rows`: physical source progress;
- `uploaded_rows`: deduplicated records sent to Edge;
- `inserted_rows`: Edge response accepted/upsert count, exposed as
  `acceptedRows`.

The key evidence:

- `parse_edge_accepted_rows` prefers `accepted`, then `upserted`, then legacy
  `inserted`.
- `deduplicate_upload_records` collapses duplicate `(timestamp, device_id)` keys
  before Edge upload.
- `counters.uploaded_rows += len(deduplicated_batch.records)`.
- `counters.inserted_rows += accepted`.
- `counters.processed_rows += len(source_batch)`.

This supports the documented meaning:

- processed rows are physical-source progress;
- uploaded/accepted rows can be lower than physical rows after dedupe;
- accepted rows can differ from DB table row-count delta because Edge/Postgres
  upsert acceptance is not a physical insert counter.

### Upload Job Repository

`backend/app/db/upload_job_repository.py` still stores accepted rows in the
legacy `inserted_rows` SQLite column. That is compatibility debt, not a current
operator-facing blocker, because API DTOs and UI labels expose the canonical
`acceptedRows` name.

The retry creation transaction uses `BEGIN IMMEDIATE` and computes:

```text
remaining physical rows = max(row_count - resume_offset, 0)
```

It blocks job creation when:

- no retryable files exist;
- remaining rows are `0`;
- expected retry file count mismatches;
- expected remaining rows mismatches.

Success path records both expected and actual retry counts in `job.created`
event data and `upload.retry` audit params.

### Upload Job API

`backend/app/api/upload_jobs.py` requires `expectedRemainingRows` for Retry
Failed. Missing or non-positive values are rejected before job creation with a
blocked `upload.retry` audit row.

Mismatches returned by the repository are converted to `422` with actual
snapshot counts in the error detail and audit params. This prevents a direct API
caller with a valid local token from creating a retry job without operator count
evidence.

### Frontend UI

`frontend/src/pages/UploadPage.tsx` builds Retry Failed confirmation from job
file state:

- retryable statuses: `failed` and `interrupted`;
- physical rows: sum of retryable file `rowCount`;
- resume offset rows: sum of `resumeOffset`;
- remaining physical rows: `max(rowCount - resumeOffset, 0)`;
- accepted rows so far: displayed as a separate metric.

The modal sends `expectedRemainingRows` and `expectedRetryFiles` only after the
operator types the exact remaining physical row count. It marks Preview-level
unique keys, duplicate key count, DB matched keys, and expected upload rows as
unavailable for retry state.

The i18n strings explicitly say:

- Start Upload approval rows, physical rows, `acceptedRows`, and DB row-count
  delta are separate.
- Retry Failed uses remaining physical rows only as the typed confirmation gate.
- Retry job state does not contain Preview-level unique key or deduped expected
  upload row counts.

## Audit / Job Evidence Review

The documented execution chain is consistent:

| Evidence | Count |
| --- | ---: |
| Failed Start Upload processed/uploaded/accepted | `2,000 / 2,000 / 2,000` |
| Retry processed/uploaded/accepted | `863,823 / 861,420 / 861,420` |
| Dedupe events | `268` |
| Duplicate rows collapsed during retry | `403` |
| Dedupe input rows | `535,823` |
| Dedupe output rows | `535,420` |
| Audit `upload.start` | `1` |
| Audit `upload.failed` | `1` |
| Audit `upload.retry` | `1` |
| Audit `upload.succeeded` | `1` |

`docs/149` adds the missing direct DB count and shows the full physical DB delta
matches the approved unique target rows:

```text
2,747,700 - 1,884,281 = 863,419
2,747,700 - 1,886,281 = 861,419
2,000 + 861,419 = 863,419
```

The aggregate evidence supports "retry succeeded with counter caveat." It does
not support "run Retry Failed again."

## Successful Retry Re-Retry Check

A successful retry job should not be retryable again.

Current code supports that:

- repository retry selection only includes failed files by default, plus
  interrupted/cancelled when explicitly included;
- succeeded files are not selected as retryable files;
- no selected retryable files returns `no_retryable_files`;
- API writes a blocked `upload.retry` audit row for that condition.

The backend API test
`test_retry_no_retryable_files_writes_blocked_audit` covers a succeeded job:

- retry request returns `422`;
- reason is `no_retryable_files`;
- audit action is `upload.retry`;
- audit result is `blocked`.

## Test Coverage Review

Validated coverage:

- `test_upload_job_service_deduplicates_duplicate_keys_before_edge_upload`
  proves physical processed rows can exceed uploaded/accepted rows after dedupe.
- `test_parse_edge_accepted_rows_prefers_canonical_count` proves canonical
  `accepted` wins over `upserted` and legacy `inserted`.
- `test_parse_edge_accepted_rows_falls_back_to_upserted_then_legacy_inserted`
  preserves backward compatibility.
- `test_retry_job_snapshots_failed_files_only` proves retry snapshot records
  expected and actual remaining rows/files.
- `test_retry_job_rejects_expected_remaining_rows_mismatch` blocks retry job
  creation before mutation when count evidence mismatches.
- `test_retry_rejects_missing_expected_remaining_rows_with_blocked_audit`
  blocks direct API retry without operator count evidence.
- `test_retry_no_retryable_files_writes_blocked_audit` blocks retry against a
  succeeded job.
- `test_upload_job_detail_exposes_accepted_rows_with_legacy_inserted_alias`
  proves `acceptedRows` is canonical while `insertedRows` remains compatibility.
- `test_upload_metrics_deduplicates_records_before_upsert_batching` confirms Edge
  source dedupes before upsert batching.

Coverage gap:

- There is no row-level exact-key attribution test or report for the one-row
  difference between retry `acceptedRows` and retry DB delta. That gap is
  acceptable for P1 documentation clarity, but it remains the reason this report
  is `96%`, not `100%`.

## P1 Decision

| Question | Answer |
| --- | --- |
| Is `863,419 unique rows` DB delta reconfirmed? | yes, by `docs/149` aggregate DB count |
| Is `acceptedRows` the same as DB delta? | no |
| Is the one-row caveat fully row-level attributed? | no |
| Is successful retry eligible for another Retry Failed? | no |
| Is UI copy separating Retry remaining physical rows from acceptedRows? | yes |
| Are backend retry expected counts enforced? | yes |
| Is immediate code patch required for P1? | no |

## Recommendations

1. Keep `docs/149` as the accepted aggregate DB delta reconciliation.
2. Do not approve additional Retry Failed for `upl_37b3da37b85d` or another retry
   of `upl_59575d0cbe67`.
3. Treat the one-row difference as an accepted counter-semantics caveat unless a
   future incident requires row-level exact-key attribution.
4. If the team wants to close the final 4%, create a separate read-only exact-key
   attribution investigation. It must not run upload/retry actions.
5. Keep future UI/docs/tests wording strict:
   - `acceptedRows = upsert accepted count`;
   - `DB delta = net-new physical rows`;
   - `Retry Failed approval = remaining physical rows`.

## Validation

| Check | Result |
| --- | --- |
| Branch separated | `codex/retry-db-delta-semantics-investigation` |
| Required docs reviewed | passed |
| Backend service/repository/API reviewed | passed |
| Frontend upload UI/API/i18n reviewed | passed |
| Targeted backend tests | `44 passed` |
| `npm run typecheck` | passed |
| `npm run build` | passed |
| Upload Preview executed | no |
| Start Upload executed | no |
| Retry Failed executed | no |
| duplicate rerun executed | no |
| authenticated Edge call executed | no |
| DB/Supabase/Docker lifecycle or destructive operation | no |
| Operational CSV mutation | no |

## Redaction Result

This report uses only repository file paths, sanitized job ids, aggregate counts,
and documented run ids. It does not include raw operational source locators,
source content, DB URLs, tokens, Authorization values, JWT-shaped values, or
operational CSV contents.
