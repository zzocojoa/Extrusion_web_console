# Upload Preview Already-In-DB Hard Delete Plan

Date: 2026-06-18

Branch: `codex/already-in-db-delete-implementation`

Status: `superseded_historical_implementation_plan_non_authorizing`

## Hard Gate

This document is retained only as historical planning and implementation/API
context. The 2026-06-18 follow-up approval is closed and is not reusable. This
document does not authorize code changes, automated or destructive fixture
tests, DB reads or writes, Delete Preflight, hard delete, reconciliation,
recovery, Upload Preview, Start Upload, Retry Failed, Supabase/Docker lifecycle
work, release, packaging, or any operational action.

Every imperative, state, request/response example, checklist, and verdict below
is historical unless a current source document explicitly restates it. In
particular, source-derived rollback readiness, a coarse DB fingerprint,
current-row-presence outcome inference, and a process/user-local operation lock
are obsolete and must not be implemented or used as evidence.

The current non-executable safety contracts are:

- `docs/164_operator_data_mutation_safety_gate.md`;
- `docs/171_v2_operational_delete_verification_gate.md`;
- `docs/173_v2_operational_upload_verification_gate.md`;
- `docs/176_v1_cutover_go_no_go_validation_plan.md`.

Those documents require, among other gates, a pre-existing verified exact-target
baseline; a protected target identity binding; one authenticated machine-global
target coordinator; a single-consumer chain fence; immutable approval,
preflight, execution, marker, and disposition lifecycles; an exact typed DB
before-image captured atomically with Delete and its target marker; marker-first
outcome reconciliation; and separately approved restore or disposition. Their
requirements are cumulative. None is granted by this historical file.

Any future implementation, fixture test, or operational execution needs a new,
explicitly scoped human authorization after the current contracts and required
deterministic tests are satisfied. Operational DB deletion remains unapproved.

## Problem

Operators can currently prove that a Preview item is fully represented in local
Supabase through the `already_in_db` status. There is no approved operator flow
for removing only those exact keys from `public.all_metrics`.

The desired feature is a production-critical hard delete flow that lets an
operator select only `already_in_db` Preview items and delete the exact
`(timestamp, device_id)` keys represented by those selected CSV files.

The unsafe version of this feature is straightforward to build and dangerous:

- it can point at the wrong database;
- DB state can change after Delete Preflight and before Start Delete;
- rollback is not app-level undo;
- partial deletes can leave the operator with unclear recovery work.

This plan blocks implementation until those risks are explicitly designed.

## Existing Behavior To Reuse

| Existing behavior | Reuse decision |
| --- | --- |
| Preview exact-key reconciliation rebuilds local `(timestamp, device_id)` keys and joins `public.all_metrics`. | Reuse the same key extraction. Count checks and recovery reconciliation must use SELECT-only DB reads; temp staging is allowed only inside the Start Delete destructive transaction. |
| Preview item statuses include `already_in_db`, `target`, `partial_overlap`, `risky`, and `excluded`. | Delete eligibility is restricted to selected `already_in_db` items only. |
| Start Upload backend gate checks latest Preview, freshness, DB reachable, risky count, source snapshot, expected target files, and expected rows. | Mirror the same backend gate shape for Delete Preflight and Start Delete. |
| Mutating APIs are protected by `X-EWC-Local-Token`. | All delete APIs must be protected by the same local token guard. |
| Audit rows redact params and are append-only in SQLite. | Delete preflight/start/success/failure/blocked paths must write safe audit rows. |
| Upload UI requires typed count confirmation before Start Upload. | Start Delete must require typed exact key count confirmation and explicit rollback limitation acknowledgement. |

## Not In Scope

- Deleting `target`, `partial_overlap`, `risky`, or `excluded` Preview items.
- Upload Preview execution.
- Start Upload execution.
- Retry Failed execution.
- DB reset, truncate, drop, or manual cleanup.
- Supabase or Docker lifecycle work.
- Remote Supabase deletion.
- App-level undo or automatic row restoration.
- Delete pause/resume/cancel after Start Delete begins. Operators may abandon a
  Preflight before Start Delete, but v1 has no in-flight delete cancel API.
- PostgreSQL schema changes to `public.all_metrics`.
- Release, tag, package, or rollout work.

## Required DB Target Guard

Historical limitation: the sanitized fingerprint described in this section is
diagnostic metadata only and cannot bind an exact database instance. A current
implementation must instead use the pre-provisioned trust anchor, protected
exact-target binding, machine-global coordinator, target-side mutation epoch,
and deadlines defined by `docs/164`, `docs/171`, and `docs/173`. The rules below
must not be treated as a sufficient target guard.

Start Delete must hard block unless every guard passes.

| Guard | Required behavior |
| --- | --- |
| DB URL configured | Block if the DB URL is missing. |
| Local target class | Block unless DB target classification is loopback plus the configured expected local DB port. |
| Runtime local stack status | Block unless local runtime status reports the configured local Supabase stack as ready. |
| DB port echo | On connection, verify the server port equals the configured local DB port. |
| Schema fingerprint | Verify `public.all_metrics` exists with the expected `(timestamp, device_id)` uniqueness contract. |
| DELETE privilege | Block unless a non-destructive privilege probe proves the connected role can delete from `public.all_metrics`. |
| Identity fingerprint | Compute a sanitized DB identity fingerprint from host class, port class, database name class, schema signature, and runtime project class. |
| Audit safety | Store only sanitized target class and fingerprint hashes in audit. Never store DB URLs. |

Preflight and Start Delete must both compute the same DB identity fingerprint.
If the fingerprint changes, Start Delete blocks with `db_target_changed`.
Reconcile must verify the same target/schema/fingerprint using a target guard
that excludes DELETE privilege because reconcile is SELECT-only against local
Supabase.

The plan must not trust Settings display values alone. The guard must connect to
the target DB and verify the effective database before any delete statement is
eligible to run.

### DELETE Permission Preflight

Delete Preflight and Start Delete must verify DELETE permission before any
destructive statement is constructed.

The check must be non-destructive. It should use PostgreSQL privilege metadata,
for example an equivalent of `has_table_privilege(current_user,
'public.all_metrics', 'DELETE')`, plus the existing schema fingerprint check.
It must not issue a no-op `DELETE` as a permission test.

If permission is absent or cannot be proven, block with
`db_delete_permission_denied`. Audit only the safe reason code and sanitized DB
target class.

The DELETE privilege guard is not used by reconcile. Reconcile must still prove
the configured local DB target, expected schema fingerprint, and stored DB
fingerprint hash before counting exact keys, but it must not block solely
because DELETE privilege is absent.

## Start-Time Revalidation

Historical limitation: reopening operational source files and rechecking their
metadata or keys is not valid Delete authorization or rollback proof. Current
Delete must use the separately protected immutable source-provenance snapshot,
must never reopen the operational source after snapshot publication, and must
bind every revalidation to the current target-global coordinator and target-side
marker contract in `docs/164` and `docs/171`.

Delete Preflight is advisory. Start Delete is authoritative.

Start Delete must repeat every safety check immediately before deletion:

- preview exists;
- preview is the latest run;
- preview is fresh within the approved freshness window;
- preview status is `succeeded`;
- preview `dbStatus` is `reachable`;
- active Preview is absent;
- active Upload Job is absent;
- active Delete Job is absent;
- selected item IDs still belong to the same Preview;
- every selected item status is still `already_in_db`;
- file signatures still match the Preview snapshot;
- re-extracted CSV keys match the preflight keyset hash;
- all selected keys still exist in `public.all_metrics`;
- DB identity fingerprint still matches preflight;
- DB DELETE permission is still present;
- `delete_run` state is durably created before DB mutation;
- `upload.delete_start` audit row is durably written before DB mutation;
- `delete_run` status is durably transitioned from `preparing` to `running`
  before any DB transaction is opened;
- typed confirmation matches exact delete key count.

If any check fails, Start Delete must not delete any rows.

If local state creation fails, block with `delete_run_state_write_failed`.
If the `upload.delete_start` audit insert fails, block with
`audit_write_failed`. In both cases, the backend must not open the destructive
DB transaction.

If the `preparing` to `running` state transition fails, block with
`delete_run_state_write_failed`, do not connect for the destructive transaction,
and do not open `BEGIN`. This durable handoff is the boundary that lets startup
recovery treat stale `preparing` as pre-mutation failure and stale `running` as
`commit_unknown`.

### Race Window Closure

The delete transaction must perform final DB revalidation and delete in one DB
transaction:

```text
Start Delete
  -> validate local token
  -> load preflight record from state DB
  -> re-read selected Preview items
  -> re-extract CSV keys and verify file signatures
  -> create delete_run state with status preparing
  -> write upload.delete_start audit row
  -> mark delete_run status running
  -> if running state write fails: block, no DB transaction
  -> connect to guarded local DB
  -> BEGIN
      -> set statement timeout
      -> acquire transaction-scoped advisory lock
      -> verify DELETE privilege again
      -> create temp key stage
      -> stage exact keys
      -> re-count matching all_metrics keys
      -> if count mismatch: ROLLBACK, blocked
      -> DELETE ... USING staged keys RETURNING 1
      -> if returned count mismatch: ROLLBACK, failed
    COMMIT
  -> mark delete_run status finalizing
  -> write state/audit success
```

The advisory lock is not a replacement for app-level active job checks. It is an
extra guard against concurrent console delete operations and any future upload
path that adopts the same lock convention.

The `RETURNING` clause is count-only. It must not return raw `timestamp` or
`device_id` values to application logs, API responses, audit params, job events,
or frontend state.

## Rollback Readiness

This feature does not provide app-level undo.

A fresh Preview plus Start Upload from source CSV is a new upload. It is not an
exact rollback and must never be represented as recovery of the deleted DB row
state. Matching paths, bytes, signatures, keys, or transformed values cannot
recreate arbitrary pre-delete values for every DB column.

Exact rollback readiness requires a protected, encrypted, complete typed DB
before-image for every selected row. Its id, schema/column/content bindings,
byte ceiling, capacity, confidentiality class, and retention deadline must be
pre-reserved by an immutable hard-delete approval. The authoritative target
transaction must capture and verify that before-image, execute the exact-key
Delete, and commit the target marker transition atomically. Any incomplete
capture, value/schema/side-effect drift, overflow, or binding mismatch must roll
back the whole transaction with zero Delete.

The separately protected immutable source snapshot defined by the current
contract proves source and key provenance only. It is not a DB before-image and
does not make rollback ready.

Delete Preflight must compute and expose:

| Field | Meaning |
| --- | --- |
| `rollbackReady` | Historical camel-case API name only. The current canonical state must begin `false_pending_atomic_before_image` and may become `true` only inside the authoritative target transaction after the complete typed DB before-image is captured and revalidated, immediately before Delete. |
| `rollbackBlockers` | Safe reason classes for any missing/mismatched before-image, target, schema, column, side-effect, capacity, confidentiality, retention, marker, coordinator, or approval binding. Source presence/signature stability cannot clear this gate. |
| `selectedFileCount` | Count only, no raw filenames in audit. |
| `selectedKeyCount` | Exact unique key count to delete. |
| `selectionHash` | Hash of selected Preview item IDs and keyset metadata. |
| `keysetHash` | Hash of exact `(timestamp, device_id)` keys, not the keys themselves. |

Start Delete must block unless the current contract can perform the atomic
before-image transition described above. A preflight response cannot truthfully
claim final rollback readiness before the authoritative target transaction.

There is no break-glass path in this plan. If operations later require deletion
without rollback readiness, that must be a separate approval and a separate
design review.

Operator-facing copy must state:

- this is a permanent DB hard delete;
- there is no in-app undo;
- exact recovery requires a separately approved restore using only the retained
  DB before-image before its active-use, reconcile, retention, and disposition
  deadlines;
- source CSV, a new Preview, and Start Upload do not replace that before-image or
  authorize recovery.

Audit params must record `rollbackReady`, safe blocker codes, counts, and hashes.
They must not record raw paths, raw filenames, DB URLs, tokens, JWTs, or secrets.

## Batch Transaction Policy

Version 1 should prefer bounded all-or-nothing deletion over partial progress.

Policy:

- one Start Delete request opens one PostgreSQL transaction;
- key staging may be chunked inside that transaction;
- per-batch commits are not allowed in v1;
- if the selected key count exceeds a conservative max, block with
  `delete_selection_too_large`;
- if any staging, revalidation, delete, or returned-count check fails, roll back
  the full transaction;
- if the process crashes before commit, PostgreSQL rolls back;
- if the process crashes after commit but before local state is updated, the
  delete run enters the current `commit_unknown_blocked`/incident-escrow flow;
  reconciliation must read and validate the exact target-side mutation marker
  first. Current row presence, absence, or delta must never infer the outcome.

The conservative max should be chosen during implementation review after timing
tests against a disposable local fixture DB. Until then, do not claim large-scale
delete support.

## Partial Failure Semantics

Delete run states must be explicit.

| State | Meaning | Operator action |
| --- | --- | --- |
| `preparing` | Local delete run exists and pre-DB guards or required start audit are being written. No DB mutation has started. | Wait. If found after process restart, mark failed before DB mutation. |
| `running` | Durable pre-transaction handoff succeeded and final DB revalidation/delete transaction is in progress or about to open. | Wait. Do not start Preview, Upload, Retry, or another Delete. |
| `finalizing` | DB transaction committed or rolled back and the backend is writing local state/audit finalization. | Wait. If finalization is interrupted, reconciliation is required before retry. |
| `blocked` | A pre-delete guard failed before DB mutation. | Fix blocker, run fresh Preview, retry preflight if still needed. |
| `failed` | Delete transaction rolled back. | No rows should be deleted. Review error and retry only after fresh preflight. |
| `succeeded` | Historical state. Current success requires the committed bound marker and matching `recovery_available` exact DB before-image, then remains recovery-disposition pending. | Do not infer recoverability from a fresh Preview. Follow the separately approved restore/disposition lifecycle. |
| `commit_unknown` | Historical name for a response-loss/crash ambiguity. | Treat as the current non-advanceable `commit_unknown_blocked` flow and reconcile the exact target marker first. |
| `reconciling` | Historical state. Read-only recovery reconciliation validates the exact bound target marker, coordinator generation, approval/run, and before-image binding. | Wait. Do not start another operation or inspect current row presence as outcome proof. |
| `reconciled_succeeded` | Historical state. The exact committed marker plus matching recovery-available before-image proved commit. | Continue only to the current recovery-disposition gate. |
| `reconciled_rolled_back` | Historical state. The exact aborted marker authoritatively proved non-commit. | Close the source-provenance disposition path; do not fabricate a DB before-image. |
| `reconciliation_failed` | Recovery could not prove DB state. | Stop. Manual maintainer investigation only; retry reconciliation only after the blocker is resolved. |

Retries must be idempotency-aware:

- never rerun Start Delete from the same preflight after any committed or
  commit-unknown state;
- require a fresh Preflight after `blocked` or `failed`;
- require recovery reconciliation before retrying a `commit_unknown` run.

### Active Delete Job Definition

For v1, an active Delete Job means any `delete_runs` row in an in-flight or
unresolved recovery state:

```text
active_or_unresolved_delete_statuses =
  preparing,
  running,
  finalizing,
  commit_unknown,
  reconciling,
  reconciliation_failed
```

Delete Preflight and Start Delete must block with `active_delete_job_exists`
while any row is in that set. `reconciliation_failed` is intentionally blocking
even though no worker is running, because DB outcome is not proven.

The only statuses that do not block a new Preflight by themselves are
`blocked`, `failed`, `succeeded`, `reconciled_succeeded`, and
`reconciled_rolled_back`.

On backend startup, stale process-bound `preparing` rows from a prior backend
process must be marked `failed` with `startup_interrupted_before_db_mutation`,
because no destructive DB transaction should have opened yet. Stale `running`
or `finalizing` rows must be moved to `commit_unknown` with
`recoveryRequired=true` and a safe audit note.

Startup recovery must not issue a DB DELETE and must not automatically classify
the final outcome from current `public.all_metrics` rows. The current contract
requires marker-first reconciliation and keeps the machine-global coordinator
non-advanceable until outcome and every applicable recovery disposition are
terminal.

### Commit-Unknown Reconciliation Entry Point

The v1 recovery execution path is an explicit API call:

```text
POST /api/upload/delete/jobs/{deleteRunId}/reconcile
```

This historical endpoint shape is not executable authorization. Current
reconciliation is read-only against local Supabase but must authenticate the
exact target and read the bound target-side marker first. It must not rebuild
authorization from current source files or infer the result by counting whether
selected rows are present. It must not run `CREATE TEMP`, `INSERT`, `DELETE`,
`UPDATE`, `UPSERT`, or any Supabase lifecycle operation against local Supabase.

Reconciliation outcomes:

- exact committed marker plus matching approval/run/mutation/coordinator and
  `recovery_available` DB before-image: publish the current committed outcome and
  keep recovery disposition pending;
- exact aborted marker: publish authoritative non-commit and close only the
  applicable source-provenance disposition path;
- missing, nonterminal, substituted, or mismatched marker/before-image/target/
  coordinator binding, DB unreachable, or identity uncertainty: remain blocked.

The endpoint must write `upload.delete_reconciled` audit rows with counts,
hashes, safe reason codes, and `recoveryRequired=false` only when the outcome is
proven. It must not return raw keys or raw source identifiers.

## State Model

The schemas below are historical sketches and omit mandatory current fields and
state machines. They must not be used for implementation or migration design.
The current model must include the immutable approval/preflight claims and
deadlines, source-provenance snapshot lifecycle, complete DB-before-image
lifecycle, target mutation id/marker, exact-target binding, machine-global
coordinator, chain fence, restore/disposition approvals, and incident escrow
defined in `docs/164`, `docs/171`, and `docs/173`.

No PostgreSQL migration is required for v1. Local SQLite state needs dedicated
delete records so audit and recovery are not inferred from upload job state.

### `delete_preflight_runs`

| Field | Purpose |
| --- | --- |
| `preflight_id` | Stable local preflight ID. |
| `preview_run_id` | Source Preview. |
| `status` | `ready`, `blocked`, `expired`. |
| `selected_item_count` | Selected Preview item count. |
| `selected_key_count` | Exact unique key count. |
| `selection_hash` | Hash of selected item IDs and file/key metadata. |
| `keyset_hash` | Hash of exact keyset. |
| `db_fingerprint_hash` | Sanitized DB identity hash. |
| `rollback_ready` | Boolean gate. |
| `rollback_blockers_json` | Safe reason codes only. |
| `expires_at` | Short validity window. |
| `created_at`, `updated_at` | Local state timestamps. |

### `delete_runs`

| Field | Purpose |
| --- | --- |
| `delete_run_id` | Stable local delete run ID. |
| `preflight_id` | Preflight used for authorization. |
| `preview_run_id` | Source Preview. |
| `status` | State from the partial failure table. |
| `expected_key_count` | Typed/approved exact key count. |
| `deleted_key_count` | Count returned by delete. |
| `db_fingerprint_hash` | Start-time DB identity hash. |
| `selection_hash`, `keyset_hash` | Revalidation hashes. |
| `start_audit_id` | Audit row ID proving `upload.delete_start` was written before DB mutation. |
| `error_code`, `error_message` | Safe diagnostics. |
| `started_at`, `finished_at`, `created_at`, `updated_at` | Local state timestamps. |

### `delete_run_items`

| Field | Purpose |
| --- | --- |
| `delete_run_id` | Parent delete run. |
| `preview_item_id` | Source Preview item. |
| `source_preview_status` | Must be `already_in_db`. |
| `file_signature_hash` | Signature hash for stability checks. |
| `local_key_count` | Expected key count for the item. |
| `db_match_count` | Expected DB match count for the item. |
| `status` | `pending`, `deleted`, `blocked`, `failed`, `unknown`. |
| `reason_code` | Safe reason code. |

Raw paths and filenames may already exist in Preview state. New delete audit
records must not copy them into audit params.

## API Contract Plan

All request/response bodies in this section are historical examples. They omit
mandatory current approval, exact-target, coordinator/fence, marker,
before-image, retention, restore, and disposition bindings and therefore are not
safe or complete API contracts.

### `POST /api/upload/delete/preflight`

Protected by local token.

Request:

```json
{
  "previewRunId": "string",
  "previewItemIds": [1],
  "expectedAlreadyInDbItems": 1
}
```

Response:

```json
{
  "preflightId": "string",
  "status": "ready",
  "selectedItemCount": 1,
  "selectedKeyCount": 100,
  "rollbackReady": true,
  "rollbackBlockers": [],
  "dbTargetGuard": {
    "status": "passed",
    "targetClass": "loopback_expected_db_port",
    "fingerprintHash": "string"
  },
  "selectionHash": "string",
  "keysetHash": "string",
  "expiresAt": "datetime"
}
```

Blocking responses must use safe reason codes:

- `preview_missing`
- `preview_not_latest`
- `preview_stale`
- `preview_not_succeeded`
- `preview_db_not_reachable`
- `active_preview_exists`
- `active_upload_job_exists`
- `active_delete_job_exists`
- `selection_empty`
- `selection_contains_non_already_in_db`
- `file_missing`
- `file_signature_changed`
- `keyset_mismatch`
- `db_target_not_local`
- `db_target_changed`
- `db_delete_permission_denied`
- `rollback_not_ready`

### `GET /api/upload/delete/jobs/latest`

Read-only status endpoint for UI gating.

Response must expose the latest delete run status, `recoveryRequired`, active
delete blocker status, counts, hashes, and safe reason codes. It must not expose
raw keys, raw paths, raw filenames, DB URLs, local token values, Authorization
values, JWTs, or secrets.

### `POST /api/upload/delete/jobs`

Protected by local token.

Request:

```json
{
  "preflightId": "string",
  "expectedDeleteKeys": 100,
  "typedDeleteKeys": "100",
  "acknowledgeNoUndo": true,
  "acknowledgeRollbackRequiresRetainedDbBeforeImage": true
}
```

Response:

```json
{
  "deleteRunId": "string",
  "status": "succeeded",
  "expectedDeleteKeys": 100,
  "deletedKeys": 100,
  "rollbackReady": true,
  "recoveryRequired": false,
  "rawKeysReturned": false
}
```

The API must not accept raw key arrays from the frontend. The historical source
derivation rule is superseded: a current Delete consumes only the immutable,
preflight-bound source-provenance evidence and must not reopen current source
files after snapshot publication.

The API must not return raw deleted keys. It returns counts, hashes, and safe
status fields only.

### `POST /api/upload/delete/jobs/{deleteRunId}/reconcile`

Protected by local token.

Allowed when the delete run is `commit_unknown`. A `reconciliation_failed` run
may be retried through the same endpoint only after a maintainer resolves the
blocker and supplies an explicit reconciliation retry acknowledgement. The
endpoint performs read-only exact-key reconciliation against the guarded local
DB and writes local state/audit outcome only.

Response:

```json
{
  "deleteRunId": "string",
  "status": "reconciled_succeeded",
  "expectedDeleteKeys": 100,
  "mutationMarkerOutcome": "committed",
  "dbBeforeImageState": "recovery_available",
  "recoveryRequired": false,
  "rawKeysReturned": false
}
```

The endpoint must not retry or continue the original delete transaction.

## UI Plan

Add the delete affordance only after implementation approval.

UI requirements:

- selector is available only for `already_in_db` Preview rows;
- mixed selections disable Delete Preflight;
- delete action is hidden or disabled when Preview is not latest, not fresh, not
  succeeded, or DB is not reachable;
- delete action is disabled while any Preview, Upload Job, or Delete Job is
  active;
- Preflight modal shows sanitized DB target guard, selected file count, exact key
  count, rollback readiness, and blocker reason codes;
- Start Delete modal requires typing the exact key count;
- Start Delete modal requires acknowledging no in-app undo and rollback limits;
- after a marker-proven committed result, UI must show the separately approved
  DB-before-image restore or disposition gate; a fresh Preview/Start Upload is
  not rollback.
- no Delete Cancel/Pause/Resume controls are shown in v1. While a Start Delete
  or reconciliation request is active, UI is read-only and shows the current
  status plus the next safe operator action.

The delete UI must not reuse Start Upload copy. Destructive language should be
plain and explicit.

## Audit Plan

Actions:

- `upload.delete_preflight`
- `upload.delete_start`
- `upload.delete_succeeded`
- `upload.delete_failed`
- `upload.delete_blocked`
- `upload.delete_reconciled`

Safe audit params:

- `previewRunId`
- `preflightId`
- `deleteRunId`
- `selectedItemCount`
- `selectedRowCount`
- `deletedRowCount`
- `rollbackReady`
- `rollbackBlockers`
- `dbTargetClass`
- `dbFingerprintHash`
- `selectionHash`
- `selectionDataHash`
- `startAuditId`
- `reasonCode`
- `rawMatchRowsReturned=false`

Forbidden audit params:

- raw file paths;
- raw filenames;
- raw `(timestamp, device_id)` keys;
- raw keys returned by SQL `RETURNING`;
- DB URLs;
- local token values;
- Authorization values;
- JWTs;
- secrets;
- raw SQL;
- raw exception payloads.

## QA And Review Plan

Plan-only validation:

- `git diff --check`
- marker scan for raw paths, DB URLs, tokens, JWTs, Authorization values,
  secrets, and operational filename markers.

Implementation PR validation before merge:

- full backend tests;
- targeted delete API contract tests;
- preview repository and delete state repository migration/bootstrap tests;
- audit redaction tests for every delete action;
- frontend typecheck and API-mode build if UI/API client changes;
- screenshot QA if Upload UI changes;
- zero-script QA with read-only checks first;
- destructive smoke only against a disposable local fixture DB.

Disposable destructive smoke must prove:

1. wrong DB target is blocked;
2. stale/non-latest Preview is blocked;
3. selected `target`, `partial_overlap`, `risky`, and `excluded` rows are blocked;
4. source-provenance snapshot content/binding mismatch is blocked and the
   operational source is never reopened after snapshot publication;
5. DB fingerprint mismatch between Preflight and Start Delete is blocked;
6. DELETE privilege absence is blocked as `db_delete_permission_denied`;
7. `delete_run` state write failure blocks before DB mutation;
8. `upload.delete_start` audit write failure blocks as `audit_write_failed` before DB mutation;
9. `preparing` to `running` state transition failure blocks as `delete_run_state_write_failed` before `BEGIN`;
10. exact key count mismatch rolls back;
11. successful delete removes exactly selected keys;
12. current row presence/absence cannot classify a response-loss Delete outcome;
13. complete typed DB before-image capture, exact Delete, and target-marker
    commit are atomic; separately approved restore uses only that before-image;
14. audit rows contain no forbidden markers;
15. stale `preparing` rows from prior process start are marked failed before DB mutation;
16. stale `running` or `finalizing` rows from prior process start are normalized to `commit_unknown`;
17. `commit_unknown` recovery can be resolved only through the reconcile endpoint;
18. reconcile endpoint is read-only against local Supabase and never issues temp-table, insert, delete, update, upsert, or lifecycle statements;
18a. reconcile verifies DB target/schema/fingerprint without requiring DELETE privilege, while Preflight and Start Delete still require DELETE privilege;
19. unresolved `commit_unknown`, `reconciling`, or `reconciliation_failed` states block new Delete Preflight and Start Delete;
20. Delete Cancel/Pause/Resume controls and APIs are absent in v1;
21. API responses, audit rows, events, and logs do not expose raw returned keys.

## Plan Review Checklist

Implementation cannot start until review confirms:

- DB target guard is stronger than current Preview DB reachability;
- Start Delete revalidates all Preflight evidence at mutation time;
- Start Delete proves `delete_run` state and `upload.delete_start` audit were written before mutation;
- Start Delete durably transitions `delete_run` from `preparing` to `running`
  before opening `BEGIN`, and blocks if that write fails;
- DB DELETE permission is proven non-destructively and rechecked at Start Delete;
- rollback readiness starts `false_pending_atomic_before_image`, becomes true
  only inside the authoritative transaction after complete typed DB before-image
  capture/revalidation, and blocks on every missing binding;
- batch policy is all-or-nothing for v1;
- partial failure and crash recovery states are operator-visible;
- intermediate delete states and active Delete Job blockers are explicitly
  defined;
- commit-unknown reconciliation has a single API-driven execution path;
- Delete cancel/pause/resume is explicitly out of v1 scope;
- no raw paths, filenames, DB URLs, tokens, JWTs, Authorization values, or
  secrets are added to audit or docs;
- destructive tests are limited to disposable local fixture DBs.

## Plan Review Recheck

Historical review verdict: `superseded_not_current_evidence`

The prior blocking concerns are addressed in this plan:

| Concern | Plan response |
| --- | --- |
| Wrong DB target risk | Required DB target guard blocks unless the effective DB is the configured local loopback DB port with matching sanitized identity fingerprint. |
| Delete Preflight to Start Delete race | Start Delete repeats source, preview, keyset, DB identity, DB match, and typed-count checks immediately before deletion inside the delete transaction. |
| Rollback relying on CSV only | Superseded. Source bytes prove provenance only. Current exact recovery requires a complete typed DB before-image captured atomically with Delete and the target marker, plus a separate restore approval. |
| Batch transaction ambiguity | V1 policy is bounded all-or-nothing: chunked staging inside one transaction, no per-batch commits, and large selections blocked. |
| Partial failure ambiguity | Delete states include `blocked`, `failed`, `succeeded`, `commit_unknown`, and recovery reconciliation outcomes. |
| Audit/state missing before mutation | Start Delete must create `delete_run` state and write `upload.delete_start` audit before opening the destructive DB transaction; `audit_write_failed` blocks deletion. |
| Running transition failure ambiguity | Start Delete must durably transition `delete_run` from `preparing` to `running` before opening `BEGIN`; failure blocks as `delete_run_state_write_failed`. |
| DB DELETE permission uncertainty | Delete Preflight and Start Delete must prove DELETE privilege non-destructively; failure blocks as `db_delete_permission_denied`. |
| Raw key leakage from delete result | SQL delete returns count-only rows and never exposes raw deleted `(timestamp, device_id)` keys to API, audit, logs, events, or frontend state. |
| Undefined intermediate states | `preparing`, `running`, `finalizing`, and `reconciling` are now defined and tied to active Delete Job blocking. |
| Commit-unknown recovery entry point | Recovery is API-driven through `POST /api/upload/delete/jobs/{deleteRunId}/reconcile`; startup marks stale `preparing` rows failed and normalizes stale `running`/`finalizing` rows to `commit_unknown`. |
| Cancel scope ambiguity | Delete Cancel/Pause/Resume is explicitly out of v1 scope after Start Delete begins. |

Remaining hard gate: this historical document cannot approve implementation or
tests. Any successor needs a new explicit work package and human authorization,
must implement the complete current contract, and must pass its deterministic
failure/race/tamper/replay test matrix before any separately authorized fixture
or operational action.

## Final Verdict

`superseded_historical_plan_no_implementation_test_or_execution_authorization`

The feature remains production-critical because it deletes rows from
`public.all_metrics`. Do not implement, test destructively, or execute it from
this file. Use the current contracts and obtain a new explicit authorization.
