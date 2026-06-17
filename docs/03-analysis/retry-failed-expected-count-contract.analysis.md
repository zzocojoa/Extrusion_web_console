# Gap Analysis: retry-failed-expected-count-contract

> Date: 2026-06-17 | Scope: Retry Failed expected count API contract

---

## Match Rate: 96%

## Summary

Retry Failed now requires the operator-confirmed remaining physical row count in
the API request. The backend recomputes retryable files and remaining rows from
the failed job state inside the retry job creation transaction before any retry
job is created.

This completes the follow-up left after the Start Upload expected count contract.
The retry contract intentionally uses different count semantics:

- Start Upload approves Preview upload target rows.
- Retry Failed approves remaining physical rows from failed or interrupted job
  file state.

## Non-Developer Summary

Before this change, the screen asked the operator to type the retry row count,
but the server did not receive that count. A direct API caller could ask for a
Retry Failed job with only the failed job ID.

Now the server receives the row count the operator approved. If the failed job
state has changed, or the typed number does not match the server's current
remaining-row calculation, the server refuses to create a retry job and records a
blocked audit row.

## Implemented Items

- [x] Retry Failed request accepts required `expectedRemainingRows`.
- [x] Retry Failed request accepts optional `expectedRetryFiles`.
- [x] Missing or non-positive `expectedRemainingRows` is blocked before retry
  job creation.
- [x] Invalid non-positive `expectedRetryFiles` is blocked before retry job
  creation.
- [x] Repository transaction recomputes actual retry file count from persisted
  failed job files.
- [x] Repository transaction recomputes actual remaining physical rows using
  `row_count - resume_offset`, clamped at zero.
- [x] `expectedRemainingRows` mismatch blocks with
  `expected_remaining_rows_mismatch`.
- [x] `expectedRetryFiles` mismatch blocks with
  `expected_retry_files_mismatch`.
- [x] Blocked audit rows include expected and actual retry counts when
  available.
- [x] Success audit rows include expected and actual retry counts.
- [x] `job.created` event includes expected and actual retry counts.
- [x] Frontend Retry Failed confirmation passes the typed approval count through
  the existing mutating API client.

## Non-Goals

- [x] Upload execution behavior was not changed.
- [x] Start Upload execution behavior was not changed.
- [x] Upload Preview was not executed.
- [x] Start Upload was not executed.
- [x] Retry Failed was not executed.
- [x] DB, Supabase, and Docker lifecycle or destructive operations were not
  executed.

## Compatibility

This is an intentional API contract hardening. Older frontend builds or direct
API callers that omit `expectedRemainingRows` are blocked by design.

API-mode frontend and backend should ship together.

## Rollback

Rollback is PR revert. If reverted, Retry Failed would return to relying on the
failed job ID without backend evidence that the operator-approved row count still
matches current retryable job state.
