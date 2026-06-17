# Gap Analysis: start-upload-expected-count-contract

> Date: 2026-06-17 | Scope: Start Upload expected count API contract

---

## Match Rate: 96%

## Summary

Start Upload now requires the operator-confirmed target row count in the API
request. The backend rechecks that expected count against the latest Preview
target snapshot inside the upload job creation transaction before any job is
created.

The frontend confirmation modal already required the operator to type the exact
row count. This change carries that confirmation into the backend contract and
audit trail.

## Non-Developer Summary

Before this change, the screen asked the operator to type the row count, but the
server only received the Preview run ID. A direct API caller with the local
console credential could skip the row-count evidence.

Now the server receives the count the operator approved. If it does not match
the Preview target rows at the exact moment Start Upload is requested, the
server refuses to create an upload job and records a blocked audit row.

## Implemented Items

- [x] Start Upload request accepts `expectedTargetRows`.
- [x] Start Upload request accepts optional `expectedTargetFiles`.
- [x] Missing or non-positive `expectedTargetRows` is blocked before job
  creation.
- [x] Invalid non-positive `expectedTargetFiles` is blocked before job creation.
- [x] Repository transaction recomputes actual target files and upload target
  rows from persisted Preview items.
- [x] `expectedTargetRows` mismatch blocks with
  `expected_target_rows_mismatch`.
- [x] `expectedTargetFiles` mismatch blocks with
  `expected_target_files_mismatch`.
- [x] Blocked audit rows include expected and actual counts when
  available.
- [x] Success audit rows include expected and actual counts.
- [x] `job.created` event includes expected and actual counts.
- [x] Frontend Start Upload confirmation passes the typed approval count through
  the existing mutating API client.

## Non-Goals

- [x] Upload execution behavior was not changed.
- [x] Retry Failed execution behavior was not changed.
- [x] Upload Preview was not executed.
- [x] Start Upload was not executed.
- [x] Retry Failed was not executed.
- [x] DB, Supabase, and Docker lifecycle or destructive operations were not
  executed.

## Follow-Up

Retry Failed still uses a separate confirmation modal based on remaining
physical rows. It should receive its own backend count contract in a later PR
because retry count semantics differ from Preview target rows:

- Start Upload approves Preview upload target rows.
- Retry Failed approves remaining physical rows from failed job state.

Keeping those contracts separate avoids mixing DB reconciliation evidence with
retry recovery evidence.

## Rollback

Rollback is PR revert. The change is API-contract level, so API-mode frontend
and backend should ship together. Older frontend builds that omit
`expectedTargetRows` will be blocked by design.
