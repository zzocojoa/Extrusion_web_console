# Operator Upload Gate Runbook

Date: 2026-06-17 Asia/Seoul

Scope: operator runbook for daily or file-added upload decisions after the
Future Upload Gate hardening work.

Verdict: `upload_gate_runbook_ready`

## Summary

This runbook defines the normal operator flow for deciding whether to upload,
not upload, or stop for investigation.

The upload gate is not a promise that every check ends in an upload. The gate is
working correctly when it allows upload only after a fresh Preview, target count
review, and separate approval, and when it stops the operator when there is no
new upload target.

This document does not execute Upload Preview, Start Upload, Retry Failed,
Settings save, database work, Supabase work, Docker work, source mutation,
release, or package creation.

## Non-Developer Explanation

Preview is the decision step.

If Preview says there are no target rows, the correct action is to stop and
record "no upload target." That is not skipping the gate. That is the gate doing
its job.

Start Upload is allowed only when a fresh Preview succeeds, the database check
is reachable, the target count is reviewed, and the operator separately approves
that exact count.

Retry Failed is also an upload action. It needs a separate review and approval
of the remaining physical rows.

Already-in-DB hard delete is not a normal upload action and not a cleanup
shortcut. It is a separately approved maintenance flow for selected
`already_in_db` Preview rows only.

## Golden Rules

| Rule | Meaning |
| --- | --- |
| Preview first | Never use Start Upload as the first check. |
| Fresh evidence only | Do not reuse old Preview or old job references. |
| Count review required | Review files, rows, risky, excluded, and DB status before upload. |
| Separate approval required | Preview success is not Start Upload permission. |
| No target means stop | `target rows = 0` is a normal no-upload outcome. |
| Failure means investigate | Timeout, failed Preview, risky files, or source mismatch block upload. |
| Retry is a new gate | Retry Failed requires remaining-row review and separate approval. |
| Delete is exceptional | Already-in-DB hard delete requires its own preflight, typed exact-key count, rollback acknowledgement, audit evidence, and separate approval. |

## Preflight Checks

Run these as read-only checks before any Preview-only run.

| Check | Required result |
| --- | --- |
| Branch/package identity | expected `main` or accepted package build |
| API health | reachable and `ok` |
| Config API | reachable |
| Source binding | expected process-data source class |
| Source access | accessible from the backend process |
| CSV count | matches the expected source state for the day |
| Target classes | `passed` |
| Runtime API/DB/Studio/Edge | ready |
| Edge auth boundary | no-auth probes return auth-class response |
| Active upload job | none before starting a new upload |
| Local token guard | mutating APIs remain protected |

Grafana or Vector can remain non-core caveats when the core gates above pass.
If they hide upload/job/audit evidence, promote the caveat to a blocker.

## Standard Operating Flow

### 1. Source Check

Use `/api/config` and the Upload/Settings screens as the source of truth.

Do not use frontend mock labels, old screenshots, or local memory as source
evidence.

Expected result:

- source class is the approved process-data source class;
- source is accessible;
- CSV count matches the expected folder state;
- target classes are passed.

If source is wrong, inaccessible, or unexpectedly points at test/sample data,
stop. Do not run Preview.

### 2. Preview-Only Gate

Run Upload Preview exactly once only after source and runtime preflight pass.

Backend checks before Preview run creation:

- `approvalScope` is present in the request;
- expected source class matches the active backend source class;
- expected range mode and custom date window match the request;
- expected applied profile matches the profile after backend safe-mode
  adjustment;
- mismatch or missing approval scope blocks run creation with a blocked
  `upload.preview` audit row.

Expected successful Preview:

- `status = succeeded`;
- `dbStatus = reachable`;
- `timeoutStage = null`;
- `risky = 0`;
- `appliedProfile` shows the safe operating profile when the source/range needs it.

Preview is allowed to return zero upload targets. That means there is nothing to
upload for that source/range.

### 3. Preview Result Decision

| Preview result | Operator decision |
| --- | --- |
| `failed` or `timed_out` | Stop. Investigate. No upload. |
| `dbStatus != reachable` | Stop. No upload. |
| `risky > 0` | Stop. Investigate risky files. |
| `target files = 0` or `upload target rows = 0` | Stop with no-upload acceptance. |
| `target files > 0`, `upload target rows > 0`, `risky = 0` | Eligible for separate Start Upload approval. |

Excluded files are not automatically a blocker, but the reason must be
understood. A file outside the selected date range can be expected. A missing
date token or source-missing result needs investigation before upload.

### 4. Start Upload Approval

Start Upload requires a separate approval message with the exact Preview run and
target rows.

Required approval wording:

```text
Preview run <previewRunId> 기준 target rows <targetRows>에 대해 Start Upload를 정확히 1회 승인합니다.
```

Backend checks before job creation:

- Preview is latest and fresh;
- Preview has safe source/config snapshot;
- current source/config still matches the Preview snapshot;
- Preview succeeded;
- DB status is reachable;
- risky count is zero;
- actual target rows match `expectedTargetRows`;
- optional target file count matches `expectedTargetFiles`;
- local token is valid.

If any check fails, the job must not be created.

### 5. Upload Completion Review

After Start Upload finishes, record:

- Preview run id;
- upload job id;
- final status;
- total/succeeded/failed files;
- processed/uploaded/accepted rows;
- warning count;
- DB row count before/after when safely available;
- upload job count delta;
- `upload.start` audit delta;
- `upload.succeeded` or failure audit evidence;
- whether any retry is needed.

If the upload fails after partial DB mutation, do not retry immediately. Preserve
job/audit evidence and investigate first.

### 6. Retry Failed Approval

Retry Failed is allowed only for a failed, interrupted, or retryable job after a
separate review.

Required count meaning:

```text
remaining physical rows = max(row_count - resume_offset, 0)
```

Required approval wording:

```text
Upload job <jobId> 기준 remaining physical rows <remainingRows>에 대해 Retry Failed를 정확히 1회 승인합니다.
```

Backend checks before retry job creation:

- retryable source job exists;
- no active upload job is running;
- retryable files exist;
- actual remaining physical rows match `expectedRemainingRows`;
- optional retry file count matches `expectedRetryFiles`;
- local token is valid.

If any check fails, retry job creation must be blocked and audit logged.

### 7. Already-In-DB Hard Delete Approval

Use this flow only when the operator explicitly needs to remove rows that
Preview has already proven are fully represented in local Supabase. It is not a
fallback for failed upload, DB mismatch, broad cleanup, or source uncertainty.

Required preconditions:

- latest Preview is fresh, `succeeded`, and `dbStatus = reachable`;
- selected rows are `already_in_db` only;
- no active Preview, Upload Job, or unresolved Delete Job exists;
- local token guard is active;
- local runtime API/DB/Studio/Edge are ready;
- backend can re-read the selected source files and reproduce the exact keyset;
- rollback readiness is true;
- DB target guard proves the configured local Supabase DB target;
- DELETE privilege is proven non-destructively.

Start Delete requires a separate approval message with the exact Preview run,
selected item count, and selected key count.

Required approval wording:

```text
Preview run <previewRunId> 기준 already_in_db items <itemCount>, exact keys <keyCount>에 대해 hard delete 정확히 1회 승인합니다.
```

Backend checks before DB mutation:

- ready preflight exists and is not expired;
- typed exact key count matches `expectedDeleteKeys`;
- no-undo acknowledgement is true;
- rollback-limitation acknowledgement is true;
- Preview item statuses, Preview freshness, latest run, source signatures,
  keyset hash, DB fingerprint, DB count, and DELETE privilege are revalidated
  at start time;
- any selected item missing or no longer `already_in_db` blocks before DB guard,
  DB count, audit-start, or destructive transaction;
- `delete_run` state is created as `preparing`;
- `upload.delete_start` audit is durably written;
- `delete_run` transitions to `running` before the destructive transaction opens.

If any check fails, no rows must be deleted.

After delete finishes, record:

- delete run id;
- status;
- expected exact keys;
- deleted exact keys;
- rollback readiness;
- recovery required;
- `upload.delete_start` and final `upload.delete_*` audit evidence;
- whether a fresh Preview is required for verification or rollback.

If status is `commit_unknown` or `reconciliation_failed`, do not run another
Delete, Start Upload, Retry Failed, or duplicate Preview workaround. Use the
explicit reconcile endpoint or stop for maintainer investigation.

Reconcile may mark success only after the backend rebuilds the original keyset,
verifies the original selection/keyset hashes, verifies the same DB target
schema/fingerprint, and completes the SELECT-only DB count. It must not issue
temp-table, insert, delete, update, upsert, or lifecycle statements against
local Supabase. Reconcile uses the target/schema/fingerprint guard only and must
not require DELETE privilege; DELETE privilege remains mandatory for Delete
Preflight and Start Delete.

If source rebuild, status
revalidation, keyset/hash comparison, DB target check, or DB count fails, the
delete run must become `reconciliation_failed` with `recoveryRequired = true`.

## No-Upload Acceptance Template

Use this when Preview succeeds but there is no upload target, or when a gate
correctly blocks upload before mutation.

```text
No-Upload Acceptance

Date/time:
Operator:
Runtime/source context:

Preflight:
- API health:
- Source class:
- Source accessible:
- CSV count:
- Target classes:
- Runtime API/DB/Studio/Edge:
- Non-core caveats:

Preview evidence:
- Preview run:
- Range:
- Status:
- dbStatus:
- appliedProfile:
- total files:
- target files:
- upload target rows:
- already in DB:
- partial overlap:
- risky:
- excluded:
- timeoutStage:
- reason counts:

Decision:
- Verdict: no upload
- Reason:
- Start Upload executed: no
- Retry Failed executed: no
- Additional Preview needed: yes/no

Audit/non-mutation evidence:
- upload.preview audit delta:
- upload.start audit delta:
- upload.retry audit delta:
- upload job total delta:
- DB row count delta if safely available:

Follow-up:
- Source cleanup required:
- Date/range change required:
- Runtime investigation required:
- Next allowed action:
```

## Start Upload Acceptance Template

Use this only after Preview returns target rows.

```text
Start Upload Acceptance

Preview run:
Approved target files:
Approved target rows:
Risky count:
Excluded count and reason:
DB status:
appliedProfile:

Approval:
- Exact approval phrase:
- Approved by:
- Date/time:

Execution result:
- Upload job:
- Final status:
- files total/succeeded/failed:
- processed/uploaded/accepted:
- warnings:
- error:
- DB delta:
- audit delta:

Further action:
- Retry required:
- Follow-up doc required:
- Next upload requires fresh Preview:
```

## Retry Acceptance Template

Use this only after a failed or interrupted job has been reviewed.

```text
Retry Failed Acceptance

Source job:
Source job status:
Retryable files:
Remaining physical rows:
Formula used:
- row_count:
- resume_offset:
- remaining:

Approval:
- Exact approval phrase:
- Approved by:
- Date/time:

Execution result:
- Retry job:
- Final status:
- processed/uploaded/accepted:
- deduplicated rows/events:
- warnings:
- failed files:
- audit delta:

Further action:
- Additional retry allowed:
- Investigation required:
- Next upload requires fresh Preview:
```

## Already-In-DB Delete Acceptance Template

Use this only after a separately approved already-in-DB hard delete.

```text
Already-In-DB Delete Acceptance

Preview run:
Selected already_in_db items:
Approved exact keys:
DB status:
appliedProfile:

Approval:
- Exact approval phrase:
- Approved by:
- Date/time:

Preflight:
- preflight id:
- rollbackReady:
- rollbackBlockers:
- dbTargetGuard:
- selectionHash:
- keysetHash:

Execution result:
- delete run:
- final status:
- expected exact keys:
- deleted exact keys:
- recoveryRequired:
- error/reason:
- audit delta:

Further action:
- Fresh Preview required:
- Rollback Start Upload required:
- Reconcile required:
- Investigation required:
```

## Stop Conditions

Stop and investigate when any of these occur:

- source inaccessible;
- source points at test/sample/fixture data;
- CSV count is unexpected;
- Preview status is `failed`, `timed_out`, or `cancelled`;
- DB status is not reachable;
- risky count is greater than zero;
- filename-date parsing is missing for expected operational files;
- target row count differs between UI, API, and approval text;
- backend rejects expected rows/files mismatch;
- Edge/runtime readiness fails;
- Audit logs cannot be read after a mutation;
- operator cannot identify whether the app is API mode or mock mode.

## Explicitly Not Allowed By This Runbook

- Start Upload without fresh Preview;
- Start Upload based on old Preview or old screenshot;
- Start Upload when target rows are zero;
- Start Upload when risky files exist;
- Retry Failed without remaining-row review;
- Already-in-DB hard delete without separate approval, ready preflight, typed exact-key count, and rollback acknowledgement;
- Already-in-DB hard delete for `target`, `partial_overlap`, `risky`, or `excluded` rows;
- Already-in-DB hard delete when a selected item changed status after preflight;
- another Delete, Preview workaround, Start Upload, or Retry Failed while delete recovery is unresolved;
- duplicate rerun to "see if it works";
- DB reset, truncate, delete, or manual cleanup as a normal upload fix;
- Docker/Supabase destructive cleanup as an upload workaround;
- Settings save as part of upload unless separately approved;
- sharing raw source paths, CSV contents, DB URLs, tokens, or authorization values.

## Related Documents

| Document | Use |
| --- | --- |
| `docs/32_operator_package_handoff_runbook.md` | Package handoff and first-launch flow |
| `docs/148_operator_legacy_gui_hard_retirement_review.md` | Legacy GUI retirement decision |
| `docs/150_operator_handoff_caveat_release_steady_template.md` | Steady period and non-core caveat policy |
| `docs/03-analysis/start-upload-expected-count-contract.analysis.md` | Start Upload count contract |
| `docs/03-analysis/retry-failed-expected-count-contract.analysis.md` | Retry Failed count contract |

## Redaction Policy

This document and any filled template must be safe to commit.

Do not include:

- raw operational source paths;
- raw operational filenames;
- CSV row content;
- DB URLs;
- credentials, tokens, Authorization values, or JWT-shaped values;
- local package output paths;
- raw logs containing local token material.

Use sanitized source classes, aggregate counts, run ids, job ids, audit counts,
and decision reasons.
