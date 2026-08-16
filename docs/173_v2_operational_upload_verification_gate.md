# V2 Operational Upload Verification Gate

Created: 2026-06-22 Asia/Seoul

Last updated: 2026-08-15 Asia/Seoul

Status: `deferred_no_operational_upload`

## Purpose

This document defines the V2 item 1 gate for operational upload verification.

It does not approve Upload Preview, Start Upload, Retry Failed, Delete,
Settings save, feature-gate enablement, Supabase reset/cleanup, Docker cleanup,
LAN exposure, deployment, operational DB writes, or source-file mutation.

The non-executable future approval templates remain in
`docs/164_operator_data_mutation_safety_gate.md`. They are usable only after
the documented implementation/test gates and protected approval lifecycle
exist and a new human approval explicitly releases the applicable gate. This
document defines the evidence record that must exist before item 1 can move
from `Deferred` to completed evidence.

## Plain-Language Rule

Operational upload verification is not "run upload and see if it works."

It is a six-step evidence chain:

1. read-only inventory precheck;
2. exactly one separately approved protected content-manifest preparation;
3. exactly one separately approved read-only target-identity preparation, followed
   by human review of the exact-match opaque target binding;
4. exactly one approved Preview-only run naming that protected manifest and
   reviewed target binding;
5. exactly one separately approved Start Upload, only if Preview proves target
   rows;
6. zero or more separately approved Retry Failed attempts, where each approval
   authorizes exactly one attempt only after authoritative outcome evidence
   proves rollback, fresh exact DB reconciliation of the entire prior attempted
   subset identifies still-absent rows, and a new approval names that exact
   reconciled subset.

Before this chain may start, production Preview must implement deterministic-
test-covered atomic content binding and a rebuilt package must be verified. The
current size/mtime signature does not satisfy this prerequisite.

If any step cannot produce safe evidence, stop. Do not replace missing evidence
with a guess, screenshot memory, old approval, old package source commit, DB
cleanup, or duplicate rerun.

## Required Evidence Record

After the atomic-binding implementation/tests and rebuilt-package verification
pass, create or identify a safe evidence record location before any Preview-only
approval is requested. The record may be a committed sanitized markdown file or
an internal append-only operator record. It must not be an editable chat message
or mutable issue/comment body by itself.

The record must not contain raw operational source paths, filenames, CSV row
content, raw `(timestamp, device_id)` keys, raw SQL, DB URLs, tokens,
Authorization values, JWTs, credentials, internal URLs, or secret values.

Minimum fields:

| Field | Meaning |
| --- | --- |
| `packageSourceCommit` | Source commit from accepted package metadata. |
| `packageLabel` | Safe package label. |
| `zipSha256` | Required when `zipCreated=true`; otherwise `not_applicable`. |
| `inventoryEvidenceRecordId` | Random, path-independent id for the execution-adjacent inventory record. |
| `inventoryObservedAtUtc` | UTC time of the execution-adjacent read-only inventory. |
| `inventoryMaxAgeSeconds` | Human-approved maximum age; no default may be inferred. |
| `previewExecuteByUtc` | Hard deadline derived from the observation time and approved maximum age. |
| `operatorPcClass` | Human-supplied safe class for the exact operator PC. |
| `sourceAlias` | Human-supplied privacy-safe alias, confirmed out of band for the exact configured source. |
| `sourceClass` | Safe class such as `drive_letter`, `network`, or `mounted`; never a raw path. |
| `inventoryObservedFiles` | Observed file count from fresh read-only inventory. |
| `inventoryApprovedPhysicalRowsCeiling` | Approved physical row ceiling from the same inventory. |
| `inventoryObservedBytes` | Total source bytes from the same read-only inventory; required before snapshot approval. |
| `contentSnapshotMaxBytes` | Human-approved full-byte snapshot ceiling; must be at least the observed bytes and must not be inferred. |
| `manifestPreparationApprovalId` | Separate approval for one protected local manifest-preparation write; does not approve Preview. |
| `manifestPreparationApprovalState` | `available`, `claimed`, `consumed`, or `invalid`; creation may claim it once. |
| `manifestPreparationExecuteByUtc` | Human-supplied deadline for both approval claim and completed protected manifest/snapshot publication; no later than inventory observation plus approved maximum age. |
| `contentManifestRecordId` | Opaque random id for the protected, single-use content manifest bound to the inventory record. |
| `contentSnapshotRecordId` | Opaque random id for the protected immutable byte snapshot created and hashed with the manifest. |
| `contentSnapshotState` | `prepared`, `preview_claimed`, `previewed`, `start_claimed`, `upload_bound`, `retryable`, `retry_claimed`, `completed`, or `invalid`. |
| `contentSnapshotRetainUntilUtc` | Human-approved access/retention deadline for the full-byte snapshot. |
| `contentSnapshotDispositionState` | `scheduled`, `in_progress`, `disposed`, or `disposal_failed_blocked`; preparation approval explicitly authorizes the bounded disposal lifecycle. |
| `snapshotDispositionEvidenceId` | Opaque safe record proving deadline/terminal trigger, per-snapshot key destruction, byte-file removal result, and final disposition state. |
| `actionMaxDurationSeconds` | Human-approved hard maximum for each Start/Retry action; it must be a positive base-10 integer within the implementation's fixed, versioned, documented, and deterministically tested safety ceiling. No default may be inferred. |
| `snapshotDispositionMarginSeconds` | Human-approved minimum interval reserved between action-lease expiry and snapshot retention expiry for outcome reconciliation and disposal; it must be a positive base-10 integer within the implementation's fixed, versioned, documented, and deterministically tested safety ceiling. No default may be inferred. |
| `snapshotActionLeaseId` | Opaque lease atomically created with a Start/Retry job to prevent disposition during its all-or-nothing mutation. |
| `snapshotActionLeaseExpiresAtUtc` | Exactly claim time plus `actionMaxDurationSeconds`, and plus the approved reconciliation/disposition margin no later than both `targetDbBindingValidUntilUtc` and `contentSnapshotRetainUntilUtc`; it cannot be renewed or extended. |
| `snapshotActionLeaseState` | `active`, `released_committed`, `released_rolled_back`, `expired_rolled_back`, or `commit_unknown_blocked`; no mutating action may proceed outside `active`, and no terminal state may regress. |
| `actionMutationId` | Random unique idempotency/fencing id pre-reserved inside the immutable Start/Retry approval record and bound to its approval/snapshot/subset/duration/margin; atomic action creation claims it, and the target marker enforces the same bindings. |
| `actionApprovedAbsentSetBindingId` | Opaque protected id binding the exact distinct target-only/still-absent keyset from Preview or reconciliation to the action approval; raw keys and unkeyed digests are never published. |
| `actionApprovedAbsentKeyCount` | Exact distinct-key count inside that protected binding; it must not be substituted with physical-row or file count. |
| `actionTargetAbsenceRevalidationEvidenceId` | Opaque safe evidence that the authoritative mutation transaction revalidated the complete approved keyset as absent and committed exactly that set, or detected drift and committed zero `all_metrics` writes. |
| `actionMutationOutcomeState` | `not_started`, `prepared`, `commit_pending`, `committed`, `rolled_back`, or `commit_unknown_blocked`; local `rolled_back` requires immutable target marker `aborted` and must never be inferred from timeout or response loss. |
| `actionMutationOutcomeEvidenceId` | Opaque safe evidence for the target-transaction marker/reconciliation result; required before a successful or retryable terminal decision. |
| `retryReconciliationCreationState` | Per-source-action single-use entitlement keyed uniquely by `actionMutationId`: `not_started`, `claimed`, `record_available`, `record_consumed`, or `invalid`; no state may regress or produce a sibling record. |
| `retryReconciliationSourceActionClass` | Immutable source action class, `start` or `retry`, bound when the entitlement is created and rechecked at claim/publication. |
| `retryReconciliationSourceFailureClass` | Immutable safe terminal failure class bound to the target outcome. `start_target_absence_drift_or_conflict` is never eligible; Retry target drift may be eligible only through the separately defined Retry policy. |
| `retryReconciliationCreationClaimId` | Opaque owner token durably created when the entitlement is claimed; only its holder may attempt publication. |
| `retryReconciliationCreationFence` | Monotonic fencing generation advanced by claim and any invalidation/disposition; a stale generation can never publish. |
| `retryReconciliationCreationExpiresAtUtc` | Absolute claim/publication deadline no later than the source action lease expiry and snapshot-retention ceiling. |
| `retryReconciliationCreationEvidenceId` | Opaque safe evidence binding the source action's entitlement claim to exactly one resulting record or terminal invalidation. |
| `retryReconciliationRecordId` | Opaque random protected record id for one post-rollback, whole-attempt exact DB reconciliation; it binds the prior action/marker/snapshot/attempted subset and private still-absent subset. |
| `retryReconciliationState` | `available`, `claimed`, `consumed`, `awaiting_successor_reconciliation`, or `invalid`; Retry creation may claim it atomically once, and only a retryable authoritative rollback may move its consumed input to `awaiting_successor_reconciliation`. |
| `retryReconciliationObservedAtUtc` | UTC observation time for the whole-attempt exact DB reconciliation. |
| `retryReconciliationExecuteByUtc` | Human-bound deadline for claiming the reconciliation record with Retry; no later than the source action lease/snapshot validity boundary. |
| `retryReconciliationRetainUntilUtc` | Non-extendable protected-subset access ceiling equal to the source approval's named `contentSnapshotRetainUntilUtc`; successful/non-retryable terminal outcome disposes earlier, while a retryable rollback retains the exact subset only until atomic successor publication or expiry. |
| `retryReconciliationDispositionState` | `scheduled`, `in_progress`, `disposed`, or `disposal_failed_blocked`; successful/non-retryable terminal Retry, invalidation, expiry, snapshot disposition, or completed atomic successor publication triggers disposal. |
| `retryReconciliationDispositionEvidenceId` | Opaque safe proof of record-key destruction, private-subset removal result, and final disposition; raw keys are never evidence. |
| `contentManifestPreparedAtUtc` | UTC time when the private content manifest was prepared. |
| `contentManifestExecuteByUtc` | Hard Preview deadline for the manifest; no later than the inventory deadline. |
| `contentManifestState` | `prepared`, `claimed`, `consumed`, or `invalid`; only `prepared` may be claimed, once. |
| `previewApprovalId` | Approval id for exactly one Preview-only run. |
| `previewApprovalState` | `available`, `claimed`, `consumed`, or `invalid`; Preview may claim it once with the manifest. |
| `preCallSnapshotCheckObservedAtUtc` | UTC time of the final read-only unchanged-snapshot check. |
| `preCallSnapshotUnchanged` | Must be `true` before the Preview API call. |
| `atomicSnapshotBindingEvidenceId` | Opaque random id proving that Preview verified and parsed the protected immutable snapshot and that later Start/Retry jobs remain bound to that same snapshot; unavailable under the current implementation. |
| `previewRunId` | Filled only after Preview-only runs. |
| `previewStatus` | Preview result class. |
| `previewTargetRows` | Target-only rows eligible for Start Upload. |
| `previewPartialOverlapRows` | Partial-overlap rows, separate from target-only rows. |
| `previewRiskyCount` | Risky files/items count. |
| `dbStatusClass` | Safe DB status class, not a raw DB URL. |
| `targetClassStatus` | Safe config target-class status. |
| `runtimeReadinessClass` | Safe Supabase API/DB/Edge readiness class. |
| `targetIdentityPreparationApprovalId` | Immutable/authenticated approval id for exactly one bounded read-only exact-target identity preparation run. |
| `targetIdentityPreparationApprovalState` | `available`, `claimed`, `consumed`, or `invalid`; only `available` may be claimed once. |
| `targetIdentityPreparationExecuteByUtc` | Human-approved hard deadline for claim and protected result publication; no value may be inferred. |
| `targetIdentityPreparationClaimId` | Opaque owner token durably created by the atomic approval claim before any DB connection/read. |
| `targetIdentityPreparationFence` | Monotonic fencing generation advanced by claim and every invalidation/restart/expiry; stale generations cannot read or publish. |
| `trustedTargetBaselineId` | Random non-derived opaque id for an immutable/authenticated owner-only expected DB-instance/database identity established from separately verified installation/runtime provenance before this chain; first observation cannot create it. |
| `trustedTargetAlias` | Human-supplied/reviewed privacy-safe exact-target alias mapped to that baseline; never a raw DB URL/credential or deterministic derivative of target identity. |
| `trustedTargetBaselineState` | Must be `verified` and not revoked before preparation; identity rotation requires a new separately verified baseline. |
| `trustedTargetBaselineEvidenceId` | Random non-derived opaque safe evidence id for out-of-band baseline verification; exact identity and every keyed integrity value remain owner-only. |
| `targetDbBindingId` | Opaque random id resolving only in the owner-only protected store to authenticated exact target DB-instance and database identity; safe target/readiness classes are diagnostic and cannot replace it. |
| `targetDbBindingState` | `preparing`, `prepared`, `preview_claimed`, `previewed`, `upload_completed_delete_ready`, `upload_bound`, `retryable`, `delete_bound`, `completed`, or `invalid`; transitions may follow only the canonical table below. A separately approved Retry may advance `retryable -> upload_bound` only with a strictly newer target-operation fence generation; same-generation or stale-generation reversal and movement to a different chain are forbidden. |
| `targetDbBindingValidUntilUtc` | Non-extendable identity-binding validity ceiling that must cover the approved Preview/Start/Retry chain and fit within the snapshot retention boundary. |
| `targetDbBindingEvidenceId` | Opaque safe evidence for the one preparation/verification lifecycle; exact instance/database identity and private MAC remain owner-only. |
| `targetGlobalCoordinatorId` | Random non-derived opaque id resolving to the one protected coordinator for the trusted baseline's exact DB-instance/database identity; every Preview chain for that target must contend on it. |
| `targetGlobalCoordinatorState` | Target-global state `idle`, `preview_claimed`, `chain_ready`, `action_claimed`, `action_active`, `commit_unknown_blocked`, `recovery_disposition_pending`, `invalidating`, `terminal`, or `invalidated_terminal`; a new Preview may claim only `idle` or a fully closed `terminal`/`invalidated_terminal` generation after advancing it. |
| `targetGlobalCoordinatorOwnerFenceId` | Exact `targetOperationFenceId` owning the current target-global generation; no second Preview/fence may coexist. |
| `targetGlobalCoordinatorConsumer` | Exact current `preview`, `start`, `retry`, `delete_preflight`, `delete`, `delete_disposition`, or `delete_restore` consumer. It is empty at `idle`, published `chain_ready`, and terminal states only. |
| `targetGlobalCoordinatorGeneration` | Monotonic target-global generation advanced by Preview claim and every claim/invalidation/terminal transition; all chains and actions CAS it. |
| `targetGlobalCoordinatorEvidenceId` | Opaque safe evidence for the target-global owner/state/generation transition; private target identity remains owner-only. |
| `targetOperationFenceId` | Random opaque protected single-consumer chain fence bound to the target-global coordinator generation, trusted baseline, target DB binding, Preview, snapshot, and operation chain. |
| `targetOperationFenceState` | Chain exclusion state `idle`, `claimed`, `active`, `recovery_disposition_pending`, `terminal`, or `invalid`; the only backward-looking releases are generation-advancing, CAS-fenced `active -> idle` transitions after successful Preview publication, successful whole-attempt reconciliation publication, or an eligible non-mutating failed preflight whose protected recovery records are terminal. Every other same-generation or stale-generation regression is forbidden. |
| `targetUploadBranchState` | `preview_pending`, `preview_ready`, `start_claimed`, `upload_active`, `retryable`, `retry_claimed`, `terminal`, `not_eligible`, or `invalid`. Preview claim starts `preview_pending`; positive target rows are required for publication as `preview_ready`. |
| `targetDeleteBranchState` | `preview_pending`, `delete_preflight_ready`, `delete_preflight_claimed`, `delete_ready`, `delete_claimed`, `delete_active`, `recovery_disposition_pending`, `terminal`, `not_eligible`, or `invalid`. Preview claim starts `preview_pending`; eligible `already_in_db` items, not target rows, control publication as `delete_preflight_ready`. |
| `targetOperationConsumer` | Exact chain consumer: `preview` while both branches are `preview_pending`; empty after publication in chain `idle`/global `chain_ready`; `start`, `retry`, `delete_preflight`, or `delete` while claimed/active; `delete` while recovery disposition is pending; `delete_disposition` or `delete_restore` during that approved close; empty only again when the chain fence is `terminal` or `invalid` and the target-global coordinator is correspondingly `terminal` or `invalidated_terminal`. |
| `targetOperationFenceGeneration` | Monotonic generation advanced by every atomic claim/invalidation/terminal transition; stale claimants cannot publish or mutate. |
| `targetOperationFenceEvidenceId` | Opaque safe evidence for the exact state/generation/consumer transition; private bindings remain owner-only. |
| `deleteRecoverySnapshotId` | When the Delete branch is used, the legacy-named owner-only exact-byte source-provenance snapshot from `docs/171`; it proves source/key provenance but is not a DB rollback image. |
| `deleteDbBeforeImageId` | When a Delete commits, the pre-reserved opaque exact DB before-image id whose complete typed rows commit atomically with DELETE and the target marker. |
| `deleteDbBeforeImageState` | `not_created` before mutation, `recovery_available` only after atomic before-image + DELETE + marker commit, then restore/disposition states from `docs/171`; a committed marker without the exact before-image blocks forever. |
| `deleteDbBeforeImageRetainUntilUtc` | Non-extendable protected retention boundary held with the target-global owner through exact restore or verified disposal. |
| `deleteDbMutationSchemaFenceBindingId` | Opaque protected binding to the DDL-conflicting relation/catalog locks or enforced schema-generation fence held through both DELETE and exact restore INSERT commit. |
| `deleteDbMutationSideEffectBindingId` | Opaque protected binding to every DELETE and restore-INSERT dependency/effect class and affected relation defined in `docs/171`; exact definitions remain owner-only. |
| `deleteDbMutationSideEffectReadiness` | Must be `direct_rows_only_no_unmodeled_or_nonrestorable_effects` for both DELETE and exact restore INSERT; any secondary relation or externally observable effect makes both transactions perform zero writes. |
| `deleteDbRestoreActiveUseExpiresAtUtc` | Unrenewable restore-transaction commit deadline, strictly before reconcile and target/before-image validity deadlines. |
| `deleteDbRestoreReconcileByUtc` | Marker-first read-only restore reconcile/equality deadline; after active-use expiry it may prove only an already committed marker and issue no restore write. |
| `deleteDbRestoreDispositionMarginSeconds` | Positive protected margin reserved between restore reconcile and the minimum target-binding/before-image deadline. |
| `edgeAuthClass` | Safe Edge auth boundary class. |
| `startUploadApprovalId` | Required only when Start Upload is separately approved. |
| `startUploadApprovalState` | `available`, `claimed`, `consumed`, or `invalid`; upload job creation may claim it once. |
| `startUploadExecuteByUtc` | Human-approved hard deadline for claiming the Start approval. |
| `approvedTargetRows` | Exact target-only rows in Start Upload approval. |
| `uploadJobId` | Filled only after Start Upload creates a job. |
| `acceptedRowsClass` | Accepted/upserted row count or safe failure class. |
| `retryApprovalId` | Required only when Retry Failed is separately approved. |
| `retryApprovalState` | `available`, `claimed`, `consumed`, or `invalid`; retry creation may claim it once. |
| `retryExecuteByUtc` | Human-approved hard deadline for claiming the Retry approval. |
| `remainingPhysicalRows` | Exact still-absent physical rows from fresh DB reconciliation of the entire prior attempted snapshot subset; never a worker cursor remainder. |
| `auditEvidence` | Safe audit ids/counts for preview/start/retry/failure. |
| `dbDeltaEvidence` | Required when the gate is explicitly approved and on. |
| `rowAttributionEvidence` | Required when the gate is explicitly approved and on. |
| `finalDecision` | `no_upload`, `upload_succeeded`, `failed_preserved`, or `blocked`. |

## Phase 1: Read-Only Inventory

Inventory is not Upload Preview. It must not create a Preview run, write local
state, write audit rows, query or mutate operational DB rows, call Edge
functions, change Settings, or alter source files.

Inventory may record only:

- a random, path-independent inventory evidence record id;
- inventory observation time, a human-approved maximum age, and the resulting
  Preview execution deadline;
- safe operator PC class;
- a privacy-safe source alias that is random or otherwise resistant to path
  guessing and is confirmed out of band for the exact configured source;
- source class;
- observed file count;
- physical data-line count or approved conservative physical row ceiling;
- total observed source bytes, as the canonical `inventoryObservedBytes` used by
  the later snapshot ceiling approval;
- safe go/no-go reason classes.

Do not publish a deterministic hash or fingerprint derived from a raw source
path. Such a value can disclose the path through candidate-path guessing.

`inventoryEvidenceRecordId`, `inventoryObservedAtUtc`,
`inventoryMaxAgeSeconds`, `previewExecuteByUtc`, `operatorPcClass`,
`sourceAlias`, `fileCount`, `rowLimit`, and `inventoryObservedBytes` in the
Preview-only approval must come from this fresh inventory and explicit human
wording. They must not be guesses, old run values, inferred validity defaults,
long-term defaults, or blanket approval for future folder growth.

## Phase 1A: Protected Content Manifest Preparation

This phase is not read-only. It is a narrowly scoped local evidence write that
copies the complete approved operational file bytes into a protected immutable
snapshot, not merely hashes or metadata. It requires a separate exact human
approval after the atomic-binding production
implementation/tests and rebuilt-package verification pass. Its exact future
wording includes only the bounded automatic snapshot disposal defined below. It
does not approve Preview, DB access, upload, retry, operational DB delete,
Settings save, runtime lifecycle, source mutation, or other cleanup.

The approval id must resolve to an immutable/authenticated protected approval
record; an arbitrary request string or Markdown text alone is insufficient. The
implementation must atomically transition that approval from `available` to
`claimed` before manifest capture, reject concurrent/duplicate claims, and then
mark it `consumed` with exactly one manifest or `invalid` on failure. A failed or
abandoned claim requires a new approval.

The approval must bind `inventoryObservedAtUtc`, the human-supplied
`inventoryMaxAgeSeconds`, and human-supplied
`manifestPreparationExecuteByUtc`, which must not exceed the inventory expiry.
Both the claim and completed protected manifest/snapshot publication must occur
by that deadline. Reject an expired claim before copying any byte. Expiry during
copying stops the copy, clears buffers, invalidates the approval/partial records,
and invokes the approved cryptographic disposition for any partial bytes; it may
never publish a late record as `prepared`.

The implementation must store the private manifest and full-byte snapshot in an
owner-restricted, confidentiality-protected, tamper-evident protected local
evidence boundary. Before copying, it must prove protected storage capacity for
`contentSnapshotMaxBytes`, at-rest access controls, and the human-approved
retention/disposition policy. The private record binds:

- the random `contentManifestRecordId` to the exact
  `inventoryEvidenceRecordId` and `manifestPreparationApprovalId`;
- package commit/label, operator PC class, source alias/class, scope, count, row
  ceiling, preparation time, and hard execution deadline;
- canonical private file identities and per-file content digests computed from
  file bytes, not only path, size, or mtime;
- an opaque `contentSnapshotRecordId` for an owner-restricted immutable copy of
  those exact bytes, created while hashing without modifying source files;
- source files opened without following links, verified as regular files and not
  symlinks, junctions, or other reparse points; hard-linked files are rejected;
  the canonical path and stable volume/file identity obtained from each opened
  handle must remain within the approved source-root handle before and throughout
  copying;
- observed snapshot bytes, human-approved byte ceiling, and
  `contentSnapshotRetainUntilUtc`;
- snapshot disposition state and the rule that the preparation approval
  pre-authorizes bounded automatic cryptographic disposal at terminal chain
  completion (zero-target Preview or completed Start/Retry), invalidation, or the
  retention deadline, whichever first applies;
- lifecycle state `prepared`, `claimed`, `consumed`, or `invalid`, with claim,
  use, expiry, and invalidation timestamps, plus the terminal
  `manifestPreparationApprovalState`.

Raw identities, paths, filenames, content digests, manifest entries, snapshot
bytes, and store authentication material remain private and confidential and
must not be copied into Markdown, PRs, Git, chat, issues, audit params, or
screenshots. Published evidence contains only opaque random record ids and safe
classes/counts/timestamps.

The approval and record are single-use and package/source/inventory-bound. A
successfully consumed preparation approval paired with a still-`prepared`
manifest is the required pre-Preview state, not a replay. Reject only a state
that is invalid for the current stage, as defined below.

### Approval, Manifest, Snapshot, And Target State Transitions

| Stage | Preparation approval | Content manifest | Content snapshot | Target DB binding | Disposition | Preview approval | Required result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Before manifest creation | `available` | absent | absent | absent | absent | absent/not issued | Creation may claim once only before `manifestPreparationExecuteByUtc` and inventory expiry. |
| Manifest/snapshot creation in progress | `claimed` | private in-progress | private in-progress | absent | not published | absent/not issued | Concurrent/duplicate creation is rejected; claim and completion deadline remains binding. |
| Manifest ready; before target-identity preparation | `consumed` | `prepared` | `prepared` | absent | `scheduled` | absent/not issued | Protected snapshot publication completed; a separate target-identity preparation approval is still required. |
| Target-identity preparation in progress | `consumed` | `prepared` | `prepared` | `preparing` | `scheduled` | absent/not issued | One approval/run may read only authenticated target identity metadata and publish no exact/private value. |
| Ready for human review/Preview approval | `consumed` | `prepared` | `prepared` | `prepared` | `scheduled` | absent/not issued | Opaque target binding is protected, unexpired, and reviewed; exact identity/private MAC remain owner-only. |
| Immediately before Preview claim | `consumed` | `prepared` | `prepared` | `prepared` | `scheduled` | `available` | All ids/bindings/deadlines match. |
| Preview in progress | `consumed` | `claimed` | `preview_claimed` | `preview_claimed` | `scheduled` | `claimed` | Preview reads only the protected snapshot and exact bound target. |
| Preview succeeded with target rows | `consumed` | `consumed` | `previewed` | `previewed` | `scheduled` | `consumed` | Snapshot and target binding remain protected for a separately approved Start/Retry chain. |
| Preview succeeded with zero target rows | `consumed` | `consumed` | `previewed` | `upload_completed_delete_ready` only while eligible `already_in_db` Delete branch remains open; otherwise `completed` | `scheduled -> in_progress -> disposed\|disposal_failed_blocked` | `consumed` | Upload branch is terminal and snapshot disposition proceeds. A separately approved Delete preflight may use only its own fresh source/key evidence under the Delete branch, never the disposed upload snapshot. Cutover exclusion closes that branch and yields `completed`. |
| Manifest or target preparation failed/abandoned | `invalid`/`consumed` | absent/`invalid`/`prepared` | absent/`invalid`/`prepared` | absent/`invalid` | absent, or `scheduled -> in_progress -> disposed\|disposal_failed_blocked` if any bytes exist | absent/not issued | No Preview authorization; a new stage-specific approval/result is required and no target binding may be guessed. |
| Preview failed after claim | `consumed` | `invalid` | `invalid` | `invalid` | `scheduled -> in_progress -> disposed\|disposal_failed_blocked` | `invalid` | Chain becomes unavailable; new inventory/manifest/snapshot/target-binding/Preview approval chain required. |
| Before Start claim | `consumed` | `consumed` | `previewed` | `previewed` | `scheduled` | `consumed` | A new Start approval must name the same snapshot, atomic evidence, and target DB binding. |
| Start creation in progress | `consumed` | `consumed` | `start_claimed` | `upload_bound` | `scheduled` | `consumed` | The Start approval, snapshot lease, target binding, and exactly one job are claimed/bound atomically. |
| Exactly one Start job record commits | `consumed` | `consumed` | `upload_bound` | `upload_bound` | `scheduled` | `consumed` | Worker uses only protected snapshot and exact target binding under the active lease. |
| Start target marker proves commit | `consumed` | `consumed` | `completed` | `completed` | `scheduled -> in_progress -> disposed\|disposal_failed_blocked` | `consumed` | Outcome evidence is durable; snapshot reads stop and automatic disposition starts. |
| Start target marker proves rollback after an eligible non-drift failure; before reconciliation publication | `consumed` | `consumed` | `upload_bound` | `upload_bound` | `scheduled` | `consumed` | The marker makes the single reconciliation entitlement eligible only; it does not expose Retry. Start target drift still invalidates the chain. |
| Start whole-attempt reconciliation record publishes | `consumed` | `consumed` | `retryable` | `retryable` | `scheduled` | `consumed` | The same publication CAS creates the one available record, advances both ready generations, empties consumers, and only then exposes the separately approved Retry scope. |
| Start outcome is unknown | `consumed` | `consumed` | `upload_bound` | `upload_bound` | `scheduled` until bounded reconciliation; mandatory retention disposal then permanently blocks chain if unresolved | `consumed` | `commit_unknown_blocked` forbids Retry/cutover and never implies rollback. |
| Retry creation in progress | `consumed` | `consumed` | `retry_claimed` | `upload_bound` | `scheduled` | `consumed` | Retry approval, snapshot lease/subset, target binding, and one action are claimed/bound atomically. |
| Exactly one Retry action record commits | `consumed` | `consumed` | `upload_bound` | `upload_bound` | `scheduled` | `consumed` | Retry worker uses only the same snapshot and exact bound target under the active lease. |
| Retry target marker proves commit | `consumed` | `consumed` | `completed` | `completed` | `scheduled -> in_progress -> disposed\|disposal_failed_blocked` | `consumed` | Outcome evidence is durable; snapshot reads stop and automatic disposition starts. |
| Retry target marker proves rollback and eligibility; before reconciliation publication | `consumed` | `consumed` | `upload_bound` | `upload_bound` | `scheduled` | `consumed` | The marker makes one new reconciliation entitlement eligible only; it does not expose another Retry. |
| Retry whole-attempt reconciliation record publishes | `consumed` | `consumed` | `retryable` | `retryable` | `scheduled` | `consumed` | The same publication CAS creates the new available record, advances both ready generations, empties consumers, and only then exposes another separately approved Retry scope. |
| Retry outcome is unknown | `consumed` | `consumed` | `upload_bound` | `upload_bound` | `scheduled` until bounded reconciliation; mandatory retention disposal then permanently blocks chain if unresolved | `consumed` | `commit_unknown_blocked` forbids further Retry/cutover and never implies rollback. |

Delete uses this exact target-binding subtable; `docs/171` supplies the remaining
Delete approval, recovery, and marker fields:

| Delete stage | Required target DB binding state | Next target DB binding state | Required atomic condition |
| --- | --- | --- | --- |
| Before/through Delete preflight claim and ready-result publication | `previewed` or `upload_completed_delete_ready`, unexpired | unchanged | Claim/publish the same target-global and chain-fence generations; preflight performs no operational mutation and cannot consume or rewrite the target binding. |
| Joint hard-Delete approval/preflight-result/run claim | same eligible state, unexpired | `delete_bound` | CAS the binding, approval, ready result, generated run id, coordinator owner/consumer, and both generations in one local transaction; any Start/Retry/different-chain winner rejects the Delete. |
| Prepared marker, authoritative Delete transaction, or bounded marker-first reconcile | `delete_bound`, unexpired for every target access | `delete_bound` | Revalidate the same exact target on the authoritative session; no current-row inference or state release is allowed. |
| Marker proves committed or authoritative aborted | `delete_bound` | `delete_bound` | Coordinator/fence enter `recovery_disposition_pending`; the binding remains owned until every recovery record that actually exists is terminal. |
| Target identity/binding mismatch before any Delete commit | eligible state or `delete_bound` | `invalid` | Fence every claimant and prove zero Delete writes before invalidation publication. |
| `commit_unknown_blocked`, unresolved marker, or disposal failure | `delete_bound` | `delete_bound` | Remain non-advanceable; no Preview/Start/Retry/Delete replay or terminalization is allowed. |
| Approved restore-then-dispose or applicable key-first disposal completes | `delete_bound` | `completed` | CAS the same owner/generations only after marker outcome and every applicable source snapshot/DB before-image/disposition record are verified terminal. |

State regression, skipped transitions, duplicate claims, or any combination not
allowed by this table is a hard stop. The table's separately approved Retry
cycle (`retryable -> retry_claimed -> upload_bound`) is not a regression only
when the target-operation fence generation advances atomically and the new
approval consumes the new whole-attempt reconciliation record; the same or a
stale generation must be rejected.

### Cross-Action Target Operation Fence

The protected baseline/exact-target identity resolves to exactly one
`targetGlobalCoordinatorId`, created by an atomic owner-only CAS during the first
successful exact-match target-identity publication if it does not already exist.
It is not a per-Preview object. Preview claim must atomically CAS that coordinator:
reject while any older Preview chain is claimed, ready, active, retryable,
delete-ready, or `commit_unknown_blocked`; only `idle` or a fully terminal prior
generation may advance to a new `preview_claimed` generation. `invalidating` is
not terminal: it may become `invalidated_terminal` only after every stale owner
is fenced, no DB read/write/unknown outcome remains, and every upload snapshot,
Delete source-provenance snapshot, DB before-image, reconciliation, and recovery
record is disposed or terminally closed with
safe evidence. `disposal_failed_blocked` and `commit_unknown_blocked` cannot
advance. In the same local
transaction and before the authoritative Preview DB query, every Preview claims
the protected random `targetOperationFenceId` pre-reserved in its immutable
approval and records it as the sole
`targetGlobalCoordinatorOwnerFenceId`, and starts both chain branches in
`preview_pending`, bound to the same trusted baseline, `targetDbBindingId`,
Preview, and target-global generation. The atomic claim publishes chain fence
state `claimed`; only the exact owner/generations may CAS it to `active` before
the first authoritative Preview DB query. The coordinator remains
`preview_claimed`, chain fence remains `active`, and both global/chain consumers
remain `preview` throughout the query. Preview publication must CAS the same
coordinator owner and currently claimed coordinator/fence generations, then
atomically advance both to one new published ready generation with the target
binding: it sets the upload branch to
`preview_ready` only for positive target rows or `not_eligible`, and independently
sets the Delete branch to `delete_preflight_ready` only for eligible
`already_in_db` items or `not_eligible`, then changes the coordinator to
`chain_ready`, chain fence `active -> idle`, and both consumers to empty. If neither
branch is eligible it terminalizes both. Query failure,
expiry, crash, invalidation, or a delayed/mismatched publication invalidates both
branches and advances both fences; it cannot leave a usable sibling. Start
creation and Delete preflight are
mutually exclusive consumers of both the same chain generation and target-global
generation: each must atomically claim chain `idle -> claimed`, target-global
`chain_ready -> action_claimed`, set the same exact consumer/owner, and advance
its branch in the same local transaction as its own approval/record claim. Only
one can commit across all Preview chains for that exact target.
A Start claim advances `start_claimed -> upload_active`. An authoritative
eligible `aborted` marker/complete rollback does not itself expose Retry: the
target-global coordinator remains `action_active`, chain fence remains `active`,
and both consumers remain the source `start` or `retry` while the single-use
whole-attempt reconciliation entitlement is claimed and published. Only the
same publication CAS that creates exactly one unexpired protected
`record_available` reconciliation record may recheck the marker/rollback,
snapshot/target validity, owner and both currently active generations, then
atomically increment both generations, set target binding/upload branch
`retryable`, coordinator `chain_ready`, chain fence `idle`, and both consumers
empty. The later Retry approval must bind those newly published generations.
Failure, expiry, invalidation, or crash before that CAS
never exposes Retry; it remains blocked or advances through `invalidating` after
fencing/cleanup. From `retryable`, only Retry may atomically claim
`retry_claimed -> upload_active`. Delete preflight advances
`delete_preflight_claimed -> delete_ready`; the later Delete must atomically
claim that exact generation with the ready preflight result and approval before
`delete_claimed -> delete_active`. Delete can never claim while upload is active/
retryable, and Start/Retry can never claim while Delete preflight/result/action
owns the chain and target-global coordinator.

Zero target rows terminalize only the upload branch. If eligible
`already_in_db` items exist, the Delete branch may remain
`delete_preflight_ready` under the separately approved Delete contract while the
upload snapshot is disposed; Delete must use its separately verified fresh
source/key evidence and may never reopen that disposed snapshot. Explicit cutover
Delete exclusion or committed upload may terminalize their branch. A resolved
Delete marker moves the coordinator, chain fence, and Delete branch to non-
advanceable `recovery_disposition_pending` and keeps both consumers `delete`.
For a committed marker, the source snapshot is
`awaiting_recovery_disposition`, the exact DB before-image remains
`recovery_available`, both share one equal retention deadline, and the marker is
accepted only with that complete-row before-image; source CSV with the same keys
is never rollback evidence. For an authoritative aborted marker, the before-
image remains `not_created`, restore is forbidden, and only the source snapshot
is retained for disposition. CAS-bound key-first verified disposal under
consumer `delete_disposition` claims every record that actually exists, while a
separately approved exact DB-before-image restore followed by verified disposal
under consumer `delete_restore` is available only for committed Delete. Only
those terminal joins may advance the same owner/generation to terminal;
`disposal_failed_blocked` remains non-
advanceable. Non-retryable failure, target-binding invalidation, or completed
branch disposition advances the applicable branch and finally
the chain fence and target-global coordinator to `terminal` or first to
`invalidating` and then `invalidated_terminal` after the closure proof above;
neither generation is reusable. A
blocked/expired non-mutating preflight may release to `idle` only by an atomic
generation advance that invalidates that preflight/result after its Delete
source-provenance snapshot key is destroyed, bytes are removal-verified, and safe
disposition evidence is committed. `disposal_failed_blocked` keeps the global
coordinator non-advanceable; any later attempt requires a fresh preflight
approval. A restore claim atomically moves the before-image `recovery_available
-> restoring` and both consumers `delete -> delete_restore`. Marker-proven commit
or reconciled commit consumes the approval and moves the image to `restored`; an
authoritative abort consumes that attempted approval, returns the intact image to
`recovery_available`, advances both generations, and returns consumers to
`delete`, so only a fresh human approval inside remaining deadlines may retry.
`commit_unknown_blocked` keeps the image `restoring` and consumers
`delete_restore`; no new action or disposition is possible. Reconcile-deadline
expiry without an authoritative marker is non-advanceable, not an abort. A
terminal target binding cannot be revived
for Delete; a fresh Preview, target-identity preparation/binding, and approvals
are required. Crash/response loss
recovers only the already committed consumer/state; invalidation/restart advances
both generations so delayed Preview/Start/Retry/Delete/preflight claimants fail.
All target markers and reconciliation records bind and recheck the same global
coordinator id/owner/generation plus chain fence id/generation.
Tests must cover positive-target, zero-target-with-eligible-delete-items, and
zero-target-with-no-eligible-delete-items claim-time `preview_pending` branch
initialization and publication. The last case must prove that publication
atomically advances the generation, completes the target binding, marks both
branches terminal/`not_eligible`, terminalizes the coordinator/fence with empty
consumers, disposes the upload snapshot, and rejects crash/replay publication.
Tests must also cover zero-target snapshot disposal without Delete snapshot
reuse, concurrent Start-vs-Delete-preflight, Retry-vs-Delete, two Delete
approvals, two concurrent Previews for the same target, cross-Preview and cross-
binding Preview-vs-Start/Retry/Delete claims, target swap, terminal-binding replay,
claim/query/publication/action response loss, crash at every transition, failed
Preview crash/restart in chain `claimed` and `active`, publication CAS failure,
crash before/after authoritative rollback and reconciliation publication,
reconciliation-publication CAS failure, and proof that Retry is never visible
without exactly one matching `record_available` record,
Preview/expired target/disposition failure to fresh-generation recovery, proof
that `invalidating`/disposal-failed/commit-unknown cannot advance, old-
chain Start/Delete racing a new Preview at claim/query/publication boundaries,
blocked/expired Delete preflight racing source-provenance-snapshot disposition and a new
Preview, resolved Delete racing early/expiry disposition or separately approved
restore against a new Preview/Start/Delete,
source keys matching while DB values differ, atomic complete-column before-image
capture/DELETE/marker commit, before-image overflow/schema drift/tamper/missing-
column failure, committed-marker/before-image mismatch, exact restore equality,
DELETE side-effect inspection/drift for cascades/triggers/rules/policies/
generated/default/sequence/replication/CDC/notification/affected-relation
classes plus concurrent DDL installation before/after fence acquisition for both
DELETE and restore INSERT, committed dual-record versus aborted source-only disposition, equal-
deadline and split-approval expiry authority, exact restore equality, and proof
that every pre-commit failure performs zero DELETE without fabricating a before-
image,
stale generation, and proof that losing paths perform zero DB
writes and publish no sibling record.

The full-byte snapshot may be read only for the human-approved Preview/Start/
Retry chain and only before `contentSnapshotRetainUntilUtc`. The preparation
approval must explicitly authorize automatic disposal at terminal chain
completion (zero-target Preview or completed Start/Retry), invalidation, or that
deadline. Each snapshot uses a per-record encryption key.
At the trigger, active snapshot work stops, in-memory buffers are cleared, and
disposition atomically claims `scheduled -> in_progress`; the key is destroyed
first, then the byte file is removed and absence is verified. Success records
`disposed`. If file removal fails, the already keyless bytes remain unreadable,
state becomes `disposal_failed_blocked`, an operator-visible alert is recorded,
and new snapshot preparation is blocked until idempotent cleanup of that same
record succeeds. Audit retains only sanitized ids, states, counts, and
timestamps plus `snapshotDispositionEvidenceId`.

Deterministic disposal tests must cover terminal completion, invalidation,
deadline while idle, deadline racing active Preview/Start/Retry, crash before and
after key destruction, byte-file removal failure, restart recovery, idempotent
same-record retry, proof that disposed/keyless bytes cannot be read, and blocking
new preparation while disposition is failed. They must reject early disposal,
cross-record substitution, and concurrent/replayed disposal that could affect a
different snapshot or falsely record `disposed`.

Start/Retry requires an atomic active-use lease, not a best-effort timer. The
approval binds `actionMaxDurationSeconds` and
`snapshotDispositionMarginSeconds`. Admission computes
`snapshotActionLeaseExpiresAtUtc = claimedAtUtc + actionMaxDurationSeconds` and
must prove it is no later than `contentSnapshotRetainUntilUtc -
snapshotDispositionMarginSeconds`; the lease cannot be renewed, extended, or
revived. Every duration/margin parse and deadline add/subtract uses checked
integer and UTC-instant arithmetic. Non-integer, non-positive, above-ceiling,
overflow, or underflow input fails before claim with zero DB writes. Equality at
the final permitted ceiling is valid only when every checked operation succeeds
and the positive-duration lease still starts before its expiry. Job/action
creation atomically claims the approval and snapshot, creates
one lease, and claims the approval's pre-reserved `actionMutationId`.
Substituted, duplicate, cross-approval, or cross-snapshot mutation ids are
rejected before any DB write. Disposition cannot claim `scheduled ->
in_progress` while any action lease/outcome is nonterminal, including lease
`active`/`commit_unknown_blocked` or outcome `prepared`, `commit_pending`, or
`commit_unknown_blocked`. The sole exception is mandatory forced disposition at
`contentSnapshotRetainUntilUtc` for an unresolved unknown outcome; that path
permanently blocks the chain and authorizes no Retry.

The operational DB executor must provide a target-side transaction fence and a
durable outcome marker keyed by `actionMutationId`. Before any `all_metrics`
write, an idempotent target transaction creates exactly one immutable-bound
`prepared` marker containing the action/fence identity and absolute expiry; this
marker write is part of the one approved action. The mutation transaction locks
that marker, requires state `prepared`, checks expiry using the authoritative
target DB clock, performs every action write, and changes the marker to
`committed` in the same target transaction. A failure/cancellation before that
commit rolls back every action write and leaves the marker `prepared`.

The approval and target marker also bind the same protected
`trustedTargetBaselineId`/alias/state/evidence,
`targetIdentityPreparationApprovalId`, `targetDbBindingId`,
`targetDbBindingState`, `targetDbBindingValidUntilUtc`, and
`targetDbBindingEvidenceId`, plus `targetGlobalCoordinatorId`, its sole owner/
exact active generation/consumer/evidence, and `targetOperationFenceId` with its
exact active generation/consumer. Before marker preparation, target-marker outcome
reconciliation, protected whole-attempt reconciliation, or any `all_metrics`
read/write, the same authoritative DB session/transaction must resolve and
revalidate the authenticated exact target instance/database identity and prove,
using the target DB clock, that the binding is unexpired. The action lease plus
`snapshotDispositionMarginSeconds` must end no later than both the target-binding
validity ceiling and the snapshot-retention ceiling. A missing/mismatched/expired binding or same-host/port
cluster/database replacement rolls back or blocks with zero action writes; safe
target/readiness classes do not qualify, and expiry never authorizes a new DB
read or reconciliation record.

The approval and target marker also bind one protected
`actionApprovedAbsentSetBindingId` and exact distinct
`actionApprovedAbsentKeyCount` produced by the succeeded Preview or protected
whole-attempt reconciliation. Before any `all_metrics` write, the same
authoritative transaction must use serializable isolation, acquire canonical
key-scope fences honored by every application writer, and revalidate that every
key in the complete protected set is still absent. Writes for this approved
absent-only scope use conflict-rejecting insert semantics, never an unconstrained
upsert update, and the transaction verifies that the inserted keyset/count
exactly matches the protected binding before the marker becomes `committed`.
A key found present before write, a concurrent unique-key conflict, serialization
failure, same-count key substitution, missing writer fence, or inserted-set
mismatch rolls back every action `all_metrics` write and the committed-marker
transition. The prepared marker is then guarded-finalized `aborted` with safe
`actionTargetAbsenceRevalidationEvidenceId`. Recovery is stage-specific: Start
drift is non-retryable and requires an entirely fresh Preview/manifest/snapshot
approval chain; Retry drift may proceed only through a new whole-attempt
reconciliation record and separate Retry approval under the lifecycle below.

The existing `all_metrics(timestamp, device_id)` uniqueness/upsert safety remains
intact for other paths. This future exact-absent action contract adds a no-
overwrite guard and cannot be implemented by the current unconstrained upsert
path alone. Any application writer that can touch `all_metrics` without the same
canonical key fence keeps Start/Retry blocked; an outside concurrent insert that
does not honor the fence must still be caught by the serializable/unique-conflict
conditional-insert rollback.

A separate guarded target finalizer may change `prepared -> aborted` only after
it acquires the marker lock after the mutation transaction has ended and either
the target-clock fence expired or an authoritative cancellation/failure proof
prevents any later commit. `committed` and `aborted` are immutable terminal
states; no missing marker, client clock, timeout, response loss, local job state,
or local lease expiry may substitute for one. A target commit after the absolute
fence is rejected. The local lease becomes `released_committed` only from
`committed`, and `released_rolled_back` or `expired_rolled_back` only from
`aborted` evidence proving non-commit and complete rollback. This target marker/
fence schema and code are an unimplemented gate, not authorization for an
operational DB migration or write.

A crash, timeout, or response loss after the target may have committed but
before the local terminal state is durable becomes `commit_unknown_blocked`,
not `expired_rolled_back`. It blocks Retry, disposition, and cutover while the
bounded read-only target-marker reconciliation runs within the remaining lease/
disposition-margin window. If reconciliation proves commit, recover
`released_committed`. If immutable target marker `aborted` is finalized and
observed before lease expiry, recover `released_rolled_back`; only an eligible
source action/failure class may then claim the protected whole-attempt
reconciliation entitlement before defining any Retry scope. Start target-
absence drift/conflict instead invalidates that entitlement and chain with zero
reconciliation DB reads or records. An `aborted` marker
finalized or first observed at/after lease expiry becomes
`expired_rolled_back`, invalidates the snapshot chain, and cannot authorize
Retry. If the
outcome is still unknown at `contentSnapshotRetainUntilUtc`, the preparation-
approved cryptographic disposition must still destroy snapshot access, but the
chain remains permanently blocked and cannot be retried or credited toward
cutover. The original approval expires and authorizes no post-retention marker
read. Any later read-only investigation requires its own immutable/authenticated,
action-bound approval and deadline under a separately reviewed plan. This
retention safety path must never claim rollback or authorize a new mutation.

Lease/outcome tests must cover insufficient duration/margin budget, exact expiry
calculation, renewal/revival rejection, target-binding expiry immediately before,
at, and after claim/marker/transaction/reconciliation boundaries, rejection when
an action lease plus margin would exceed `min(targetDbBindingValidUntilUtc,
contentSnapshotRetainUntilUtc)`, expiry before job creation, expiry during Start
and Retry, concurrent lease/disposition claims, ordinary failure,
cancellation, worker crash before target commit, target commit followed by crash
or response loss before local release, target rollback followed by response
loss, target-marker unavailability, disposition claiming each nonterminal state,
forced disposition exactly at retention, `aborted` proof just before/at/after
lease expiry, transaction commit racing the target-side fence, client/target
clock skew, duplicate marker preparation, prepared-marker lock/finalizer races,
immutable committed/aborted states, exact restart reconciliation, pre-reserved
mutation-id substitution/collision/cross-approval/cross-snapshot reuse, complete
rollback/no partial DB writes, protected absent-set id/key-count substitution,
target insert after Preview/reconciliation but before action transaction,
concurrent insert between in-transaction absence revalidation and conditional
write, same-count different-key drift, serialization/unique conflict, missing
writer fence, exact committed-keyset verification, zero action writes/no
overwrite on every drift path,
retention expiry while outcome remains unknown, and release/disposition ordering.
Until this all-or-nothing target-marker and lease contract exists, Start Upload
and Retry Failed remain blocked.

After an eligible retriable `aborted` marker is finalized and observed before
lease expiry, the same action approval exposes exactly one protected
reconciliation-creation entitlement keyed uniquely by its `actionMutationId`,
`retryReconciliationSourceActionClass`, and
`retryReconciliationSourceFailureClass`. The eligibility matrix explicitly
excludes `(start, start_target_absence_drift_or_conflict)`: that source outcome
must atomically make the entitlement `invalid`, permits zero reconciliation DB
reads and no record publication, and requires a fresh Preview/manifest/snapshot
approval chain. A Retry target-absence drift/conflict may remain eligible only
under the separate Retry transition below. Before any DB read, one
worker must durably and atomically claim `not_started -> claimed`, recording an
opaque owner `retryReconciliationCreationClaimId`, a monotonic
`retryReconciliationCreationFence`, and absolute
`retryReconciliationCreationExpiresAtUtc` no later than the source-lease,
`targetDbBindingValidUntilUtc`, and snapshot-retention boundaries. Only that
token/fence holder may perform the bounded read-
only exact DB reconciliation of the entire attempted snapshot subset and
protected local evidence write. Publication uses a compare-and-set transaction
that rechecks the same source action/failure class, eligibility decision, claim
id/fence, state `claimed`, unexpired absolute deadline, immutable target marker
`aborted` observed before source-lease expiry, pre-publication snapshot and target
binding state `upload_bound`, disposition `scheduled`, and the same unexpired
`targetDbBindingId`/validity/evidence revalidated on the authoritative target
session. It atomically
creates
exactly one immutable/authenticated
`retryReconciliationRecordId` in state `available`, bound to package/operator/
source, snapshot and atomic binding evidence, the same exact protected
`targetDbBindingId`, source job/action and
`actionMutationId`, immutable aborted outcome evidence, private exact attempted-
subset identity, private exact still-absent key/row subset, safe counts,
`retryReconciliationObservedAtUtc`, and human-bound
`retryReconciliationExecuteByUtc`, while the entitlement becomes
`record_available`, records `retryReconciliationCreationEvidenceId`, advances
the snapshot/target binding/upload branch to `retryable`, CAS-checks the current
active coordinator/fence generations, and atomically increments both to the new
published `chain_ready`/`idle` generations with empty consumers in the same local
transaction. A uniqueness constraint on source `actionMutationId`
forbids sibling records. Duplicate calls and response-loss recovery return the
same record. Failure/crash before record publication makes the entitlement
`invalid`, creates no reusable record, and requires a new separate human-approved
read-only reconciliation plan; the consumed action approval cannot be replayed.
Restart recovery, claim expiry, snapshot invalidation/disposition, or later action
advancement atomically advances the fence and sets `invalid`; a delayed claimant's
publication CAS then fails and any private buffers/partial bytes are disposed.

The attempted/still-absent identities and exact keys are owner-only,
tamper-evident, and encrypted with a per-record key. The record binds a
non-extendable `retryReconciliationRetainUntilUtc` equal to the source approval's
named snapshot-retention ceiling. Its private subset remains within the same
protected boundary when a Retry claims it; it is never copied to weaker
job/audit state. A successful, non-retryable, expired, or invalidated terminal
Retry, or snapshot disposition, atomically triggers `scheduled -> in_progress`:
active reads stop, buffers clear, the record key is destroyed first, private
bytes are removed, and absence is verified. A retryable rolled-back Retry instead
moves its consumed input record to `awaiting_successor_reconciliation`. That
record remains encrypted and readable only by the one fenced successor
reconciliation until the successor publication transaction atomically verifies
and claims/copies the exact whole-attempt subset into the new record, publishes
that record and the new ready generations, and starts disposition of the old
record. It may never expose Retry before that publication succeeds. If the
successor cannot publish before retention expiry, expiry disposes the old record
and permanently blocks the chain rather than inventing a successor. Success is
`disposed`; removal failure after key destruction is
`disposal_failed_blocked`, alerts the operator, and blocks Retry, snapshot
disposition completion, and new preparation until idempotent same-record cleanup
succeeds. Only opaque id/state/count/timestamp and
`retryReconciliationDispositionEvidenceId` remain. Raw keys remain protected and
unpublished.

Every Retry approval must name that opaque record id and exact safe counts. Retry
creation atomically claims the Retry approval, snapshot, reconciliation record,
pre-reserved next `actionMutationId`, and exactly one retry job/lease. Success
sets the record `consumed` and its source entitlement `record_consumed`; any
mismatch, stale/expired record, concurrent/replay claim, or creation failure
without a retry job sets both `invalid`, starts private-subset disposition, and
requires a new authorized chain. The record may never return to `available`, be
shared by two Retry approvals/actions, or be replaced by equal-count different
keys. Snapshot/action advancement rejects and disposes any unexpected older
available record before another Retry can proceed.

Reconciliation tests must cover source-action/failure-class and target-DB
binding/substitution, same-host/port target replacement, exact-identity
revalidation on every marker/reconciliation transaction, target-binding expiry
immediately before/at/after entitlement claim, DB read, and publication CAS,
rejection of any creation deadline beyond the minimum source-lease/target-
binding/snapshot ceiling, rejection of Start
target-absence drift/conflict before any
reconciliation DB read or record publication, eligibility of the separately
defined Retry drift path, failure after reported progress, complete
rollback of the prefix, whole-attempt versus cursor-only comparison, concurrent
entitlement creation, response loss/crash before and after record publication,
same-record recovery, uniqueness under source mutation id, claim owner-token/
fence/deadline substitution, expiry immediately before/during publication,
restart invalidation racing a delayed publisher, stale-generation rejection,
stale sibling replay,
equal-count subset substitution, stale/expired/replayed records, cross-action/
snapshot/outcome substitution, concurrent Retry claim, multi-Retry chaining with
a new entitlement/record per aborted action, owner-only encryption/tamper
rejection, and private-key redaction. They must prove a consumed record remains
readable only by its one active bound Retry or its one fenced successor
reconciliation, cannot be replayed or copied to weaker state, and is disposed
only after a successful/non-retryable terminal outcome, invalidation, expiry,
snapshot disposition, or atomic successor-record publication has made the old
subset unnecessary. They must race terminal disposition against successor claim,
copy, and publication and prove the losing path cannot destroy the only exact
subset or publish a sibling record. They must also cover crash and failed-removal
recovery and exact final-signoff propagation.

Preparation tests must cover missing/inferred/mismatched observation, maximum-
age, and preparation-deadline fields; expiry before claim; expiry during copy;
duplicate/concurrent claims; late publication rejection; partial-byte disposal;
and restart recovery. They must also prove that observed bytes above
`contentSnapshotMaxBytes`, insufficient protected capacity, missing per-snapshot
encryption, or missing owner-only access controls fail before an accessible
snapshot is published. Stage tests must prove retention expiry before or during
each of Preview, Start, and Retry stops further reads, clears active buffers,
records the correct action failure/evidence, and enters the bounded disposal
lifecycle without authorizing another job or retry.
Lease-boundary tests must inject an authoritative clock and cover non-integer,
negative, zero, one, exact fixed safety ceilings, ceiling-plus-one, checked
addition/subtraction overflow or underflow, and just-before/at/just-after each
derived deadline; only the explicitly permitted equality case may claim.
They must also cover symlink, junction/reparse-point, hard-link, canonical root-
escape, link-swap, and opened-handle identity substitution attempts; none may
publish a manifest/snapshot or copy bytes outside the approved source root.

### Protected Target-Identity Preparation

Inventory performs no DB query, and manifest/snapshot preparation authorizes no
DB access. Therefore `targetDbBindingId` must never be guessed, inferred, or
created opportunistically. After the protected snapshot is prepared and before
Preview approval, one separate immutable/authenticated, expiring, single-use
`targetIdentityPreparationApprovalId` must authorize exactly one bounded read-
only target-identity preparation run. It binds package source commit, operator PC
class, inventory/manifest/snapshot ids, configured safe target class,
`targetIdentityPreparationExecuteByUtc`, and a human-supplied
`targetDbBindingValidUntilUtc` no later than snapshot retention. It must also
name an already `verified`, non-revoked `trustedTargetBaselineId`, its human-
reviewed privacy-safe `trustedTargetAlias`, and
`trustedTargetBaselineEvidenceId`. That baseline resolves owner-only to expected
authenticated instance/database identity established from separately verified
installation/runtime provenance. Neither this run nor the first DB observation
may create, replace, or self-attest the trusted baseline.
The approval additionally names either the existing exact-target singleton
`targetGlobalCoordinatorId` or one pre-reserved random coordinator id. Exact-
match result publication may resolve or uniqueness-CAS-create only that id for
the trusted identity; it may never create a sibling coordinator.
This plan does not authorize baseline provisioning or rotation. If no such
baseline already exists, stop; a separate security-reviewed installation/
provisioning work package and explicit approval must establish it before this
chain can resume.

Before any DB connection or metadata read, one local transaction must atomically
claim `available -> claimed`, record opaque owner
`targetIdentityPreparationClaimId`, advance and bind
`targetIdentityPreparationFence`, and recheck the approval deadline plus the
same verified/non-revoked baseline id/alias/evidence. Only that token/fence holder
may perform the one bounded read of authenticated stable DB-instance/database
identity metadata; it may not query operational table keys/rows or mutate the DB.
Publication compares the observed exact identity to the expected identity behind
the named trusted baseline using owner-only material, then uses a CAS that
rechecks claim id/fence, state `claimed`, unexpired deadline, unchanged baseline
state/evidence, and exact package/operator/inventory/manifest/snapshot bindings.
Only an exact match may let that CAS create at most one random opaque
`targetDbBindingId`, resolve-or-create only the approval-bound singleton
`targetGlobalCoordinatorId`,
store exact identity plus a versioned domain-separated keyed integrity value in
an owner-only authenticated record, publish only safe classes/opaque ids/
timestamps, and finish the approval `consumed` with binding state `prepared`.
Response loss after publication returns the same record without another DB read.
Crash, expiry, restart, or invalidation before publication advances the fence,
ends `invalid`, and prevents a delayed reader/publisher from succeeding. A
missing/revoked baseline, alias/evidence
substitution, first-observation wrong DB, identity mismatch, expiry,
concurrent/replay claim, publication
failure, or same-port substitution makes the approval/binding `invalid`; it may
not return to `available` or authorize Preview. The human must review the safe
prepared result before issuing `previewApprovalId`.

Deterministic tests must cover missing/arbitrary approval ids, package/operator/
inventory/manifest/snapshot/target-class/deadline/trusted-baseline/alias/evidence
substitution, concurrent and duplicate claims, failure before/after claim/read/
local publication commit, response-loss recovery without a second read, claim-
owner/fence substitution, expiry during identity read/publication, restart/
invalidation racing a delayed reader/publisher, same-loopback/same-
port cluster/database swaps both before first observation and after binding,
missing/revoked/rotated baseline, wrong DB present at first observation, weak-
key/candidate-enumeration attacks against baseline/evidence ids or alias, private
identity/all keyed-integrity-value
redaction, cross-chain binding reuse, duplicate/sibling coordinator creation,
and zero operational-table reads/DB writes.

## Phase 2: Preview-Only

Preview-only remains blocked unless the exact wording in `docs/164` is supplied
for the accepted package metadata and names the execution-adjacent inventory
record id, `manifestPreparationApprovalId`, protected
`contentManifestRecordId`, trusted target baseline id/alias/state/evidence,
consumed `targetIdentityPreparationApprovalId`, prepared `targetDbBindingId`,
`previewApprovalId`, operator PC class, and
privacy-safe source alias.

Immediately before the API call, repeat the read-only scan and compare the exact
local file set, scope, size/mtime metadata, file count, physical-row ceiling,
package, operator PC class, source alias, and source class with the approved
record. Do not call Preview unless the deadline and maximum-age checks pass and
the scan produces `preCallSnapshotUnchanged=true`. Published evidence records
only the check timestamp and boolean; raw paths and filenames remain local.

That metadata check is necessary but not sufficient. The current Preview
implementation identifies a file by size and mtime and does not atomically bind
the approved content to the bytes it later parses. Phase 2 therefore remains
blocked until production code atomically claims the protected manifest, rejects
missing/expired/reused/tampered/mismatched records, opens an immutable snapshot
identified by `contentSnapshotRecordId`, verifies the private content digests
from those bytes, and parses those same bytes. The claim and terminal lifecycle
update must resolve an immutable/authenticated Preview approval record and
atomically claim the manifest, prepared target DB binding, and
`previewApprovalId` together. It binds the unchanged
`manifestPreparationApprovalId`, verified/non-revoked trusted target baseline,
consumed
`targetIdentityPreparationApprovalId`, `targetDbBindingId`, and
`previewApprovalId`, consumes the Preview approval/manifest and advances the DB
binding exactly once on success, and marks the claimed chain invalid on failure
so no approval or record can be substituted or replayed. Published content-
snapshot evidence uses only approval ids plus opaque random
`contentManifestRecordId`, `contentSnapshotRecordId`, and
`atomicSnapshotBindingEvidenceId`. Separately reviewed target evidence may add
only random non-derived baseline/binding/claim/target-global-coordinator/chain-
fence/evidence ids, the human-supplied privacy-safe alias, and safe states/
classes/counts/timestamps. Exact target identity, deterministic derivatives, and
all keyed integrity values remain owner-only.

Before any Preview target query, the Preview approval and protected run must bind
one pre-existing `targetDbBindingId`; the same authoritative DB session must
resolve and verify the exact protected instance/database identity before reading
keys. Safe loopback/port/target/readiness classes alone are insufficient. The
terminal Preview evidence carries only the opaque binding id, never the exact
identity or private MAC. A same-host/port database or cluster replacement blocks
the run and invalidates the chain.

If Preview finds target-only rows, its terminal protected transaction also stores
the exact distinct target-only keyset inside the snapshot's owner-only,
tamper-evident encrypted boundary and publishes only opaque
`actionApprovedAbsentSetBindingId` plus `actionApprovedAbsentKeyCount`. Raw keys
and unkeyed digests never enter API/audit/final evidence. This private set is
bound to the same Preview/snapshot, retained only while that snapshot is valid,
and cryptographically disposed with the snapshot. Start must consume this exact
binding; a count-only or reconstructed/substituted set is invalid. A zero-target
Preview records the binding as `not_created` and cannot authorize Start.

Deterministic tests must cover manifest mismatch, equal-size/equal-mtime content
replacement, concurrent replacement/write, change after pre-call metadata
check, stale record reuse, double claim, missing record, tampered record,
package/source/inventory mismatch, expiry, and failure before/after claim.
They must also reject missing or mismatched approval ids, arbitrary/unresolvable
approval strings, duplicate or concurrent manifest creation with one
`manifestPreparationApprovalId`, duplicate/concurrent Preview claims with one
`previewApprovalId`, inconsistent approval/record terminal states, and every
valid/invalid transition in the state table above.
They must prove snapshot bytes are immutable and that Preview never reopens the
operational source after the snapshot is prepared.
They must also prove exact target-only distinct-set construction, protected
binding/confidentiality, duplicate-key handling, same-count key substitution
rejection, zero-target `not_created`, and snapshot-coupled disposition. Target-
binding tests must cover missing/unresolvable/substituted ids, same-loopback/
same-port cluster or database replacement before/during Preview, exact identity
revalidation on the query session, and zero accepted evidence from the wrong DB.

After Preview-only, record:

- preview run id;
- inventory evidence record id;
- manifest-preparation approval id and Preview approval id exactly as bound in
  the protected manifest/claim lifecycle;
- target-identity preparation approval id/state/deadline and protected target DB
  binding id/state/validity/evidence exactly as bound in its one-run lifecycle;
- protected content manifest record id, prepared-at/deadline fields, and
  single-use terminal state;
- protected content snapshot record id, `previewed` state, observed/approved byte
  counts, retention deadline, disposition state, and
  `snapshotDispositionEvidenceId` when triggered;
- operator PC class;
- privacy-safe source alias;
- inventory observation time, maximum age, execution deadline, final check
  timestamp, and `preCallSnapshotUnchanged=true`;
- opaque `atomicSnapshotBindingEvidenceId`, unavailable until the production
  atomic-binding implementation and deterministic tests exist;
- protected target-only absent-set binding id and exact distinct-key count, or
  `not_created` for zero target rows;
- source class;
- run status;
- total files and status counts;
- target-only rows;
- partial-overlap rows;
- already-in-DB count;
- risky count;
- DB status class;
- opaque protected exact `targetDbBindingId` verified by Preview;
- audit evidence;
- confirmation that Start Upload, Retry Failed, Delete, Settings save, and
  feature-gate changes were not run.

If Preview fails, times out, returns unexpected source class, reports
`dbStatus != reachable`, or has `risky > 0`, stop and preserve evidence.

If Preview succeeds with zero target rows, record `finalDecision=no_upload`.
That can be valid V2 item 1 evidence for a no-upload operational day, but it is
not Start Upload evidence.

## Phase 3: Start Upload

Start Upload requires a separate exact approval after Preview evidence is
reviewed.

The approval id must resolve to an immutable/authenticated protected record in
state `available`, bound to package/operator/source, Preview run, exact target
rows/files, deadline, `actionMaxDurationSeconds`,
`snapshotDispositionMarginSeconds`, `contentSnapshotRecordId`, and
`atomicSnapshotBindingEvidenceId`, plus one random unique pre-reserved
`actionMutationId`, protected `actionApprovedAbsentSetBindingId`, and exact
distinct `actionApprovedAbsentKeyCount`, the same verified/non-revoked trusted
target baseline id/alias/state/evidence, and the same consumed
`targetIdentityPreparationApprovalId` plus exact protected `targetDbBindingId`,
state, validity ceiling, and evidence verified by Preview, plus the same
`targetGlobalCoordinatorId` in `chain_ready` naming this chain fence as sole
owner with empty consumer and exact generation/evidence, and the same
`targetOperationFenceId` in fence state `idle` with upload branch `preview_ready`
and exact generation/evidence. At claim time the
binding must be `previewed` and unexpired, and the unrenewable action lease plus
`snapshotDispositionMarginSeconds` must end no later than
`min(targetDbBindingValidUntilUtc, contentSnapshotRetainUntilUtc)`. The named snapshot must be the immutable
`previewed` snapshot from Preview evidence. Production code must atomically
claim the approval, snapshot, target-global coordinator, and chain operation
fence, create one active-use lease, claim that pre-
reserved `actionMutationId`, and create the upload job
atomically; it rejects
missing/expired/substituted/duplicate/
concurrent claims and finishes the approval
`invalid` only if no job commits. Once exactly one job commits, the approval is
permanently `consumed` and the job is permanently bound to that snapshot,
regardless of later succeeded/failed/cancelled worker outcome or response loss.
The worker must read only protected snapshot bytes before
`contentSnapshotRetainUntilUtc`, while disposition is `scheduled`, and must never
reopen the operational source. Its DB mutation and durable target outcome marker
must share the authoritative transaction/fence defined above; local timeout or
lease expiry cannot assert rollback. Until this lifecycle and deterministic
tests exist, Start Upload remains blocked even if the wording is filled.

| Start stage | Approval state | Snapshot state | Action lease | Mutation outcome | Upload job state | Required result |
| --- | --- | --- | --- | --- | --- | --- |
| Before creation | `available` | `previewed` | absent | `not_started` | absent | Exact bindings including consumed target-identity preparation approval, `targetDbBindingId`/state/validity/evidence, protected absent set/distinct-key count, duration/margin budget, and disposition deadline are rechecked; the binding is unexpired and the proposed lease fits both validity ceilings. |
| Atomic creation transaction | `claimed` | `start_claimed` | `active`, inserted atomically | `not_started`, pre-reserved mutation id claimed | being inserted | The target binding is atomically rechecked as the same unexpired `previewed` binding and becomes `upload_bound`; concurrent/duplicate claims cannot commit another lease/job or substitute the mutation id. |
| Creation fails before job commit | `invalid` | `invalid` | absent/`expired_rolled_back` | `not_started` | absent | Zero DB writes; new inventory/manifest/snapshot chain and approval are required. |
| Exactly one job record commits | `consumed` | `upload_bound` | `active` | `not_started` | committed, nonterminal | Approval stays consumed and the job uses only the snapshot under this lease. |
| Target outcome marker prepared | `consumed` | `upload_bound` | `active` | `prepared` | running | Exactly one target-clock-fenced marker is durable; no `all_metrics` write has occurred. |
| Target transaction in flight | `consumed` | `upload_bound` | `active` | `commit_pending` | running | On the same authoritative transaction, revalidate exact target identity and unexpired binding with the target clock, then under serializable/key fencing revalidate the whole approved keyset as absent and use conflict-rejecting conditional inserts; disposition and duplicate mutation are blocked. |
| Target absence drift/conflict before commit | `consumed` | `invalid` | `released_rolled_back` | `rolled_back` with absence evidence | terminal blocked/non-retryable | Zero action `all_metrics` writes and no overwrite; invalidate/dispose this chain and require a fresh Preview/manifest/snapshot approval chain. Reconciliation-to-Retry is forbidden for this Start failure class. |
| Target commit marker proves success | `consumed` | `completed` | `released_committed` | `committed` with absence evidence | terminal succeeded/recovered succeeded | Exact inserted keyset/count equals the protected approval binding; preserve sanitized evidence, block reads, and start automatic disposition. |
| Other retriable failure/cancellation; target marker `aborted` before lease expiry | `consumed` | `upload_bound -> retryable` only in fresh exact reconciliation publication CAS | `released_rolled_back` | `rolled_back` with evidence | terminal failed/retryable/cancelled | Excludes target-state drift. Marker rollback alone keeps the snapshot bound. Atomically publish the one protected record plus new ready generations; only then may a later Retry claim its still-absent subset. |
| Non-retryable failure proves rollback | `consumed` | `invalid` | `released_rolled_back` | `rolled_back` with evidence | terminal failed/blocked | Start automatic disposition; final decision is blocked/failed-preserved and Retry is forbidden. |
| Crash/timeout/response loss after possible target commit | `consumed` | `upload_bound` | `commit_unknown_blocked` | `commit_unknown_blocked` | terminal/nonterminal blocked | Do not infer rollback, dispose early, Retry, or create another job; reconcile the target marker. |
| Target-marker reconciliation proves commit | `consumed` | `completed` | `released_committed` | `committed` with evidence | recovered succeeded | Use the same job/mutation id and continue only to disposition. |
| Target marker is guarded-finalized `aborted` and observed before lease expiry after an eligible non-drift failure | `consumed` | `upload_bound -> retryable` only in fresh exact reconciliation publication CAS | `released_rolled_back` | `rolled_back` with evidence | recovered failed/retryable | Marker finalization alone does not expose Retry. The source action/failure-class-bound entitlement atomically publishes one protected record plus new ready generations; its whole-attempt still-absent subset is the only later Retry scope. Start target-absence drift/conflict remains excluded and invalidates the entitlement without a DB read or record. |
| Target marker is finalized/first observed `aborted` at or after lease expiry | `consumed` | `invalid` | `expired_rolled_back` | `rolled_back` with evidence | terminal failed/blocked | Start disposition; no Retry from this expired action. |
| Outcome remains unknown at retention deadline | `consumed` | `invalid` then inaccessible | `commit_unknown_blocked` | `commit_unknown_blocked` | terminal blocked | Perform mandatory cryptographic disposition and permanently block this chain; this approval authorizes no post-retention DB read. |
| Duplicate request after job commit/response loss | `consumed` | current recorded state | same recorded lease | same mutation id/outcome | the same committed job | Return/preserve the existing binding; never create another job. |

Tests must cover missing/unresolvable ids, binding mismatch, approval/action/
target-binding expiry, target-binding expiry immediately before/at/after atomic
claim, marker creation, mutation transaction, and outcome reconciliation, lease
end beyond the target-binding or snapshot-retention ceiling,
substitution of every package/operator/source/Preview/file/row/deadline/snapshot/
atomic-evidence/target-DB-binding/duration/margin/mutation-id/absent-set-id/
distinct-key-count field,
concurrent claims, failure before commit,
crash/response loss after target commit but before local lease release, target-
marker reconciliation, worker failure/cancellation, duplicate request after
response loss, single-use reconciliation creation/response-loss recovery and
private-subset disposition, source-action/failure-class substitution, and
inconsistent approval/snapshot/lease/outcome/job states. They must prove Start
target-absence drift/conflict invalidates the entitlement before any
reconciliation DB read/record publication, while the separately defined Retry
drift path remains eligible. They must
also cover operational-source replacement after Preview and before Start,
equal-size/equal-mtime replacement, concurrent source writes, missing/tampered
snapshots, and attempts by a worker to reopen the operational source. A mismatch
or missing protected snapshot before mutation must produce zero DB writes.

The approved row count must be target-only rows. Partial-overlap rows are not
included unless a later approved flow explicitly changes that policy.

After Start Upload, record:

- approval id;
- approval deadline and terminal state;
- preview run id;
- protected content snapshot record id, terminal state, retention deadline,
  disposition state, snapshot disposition evidence id, and atomic snapshot
  binding evidence id;
- action maximum duration, disposition margin, snapshot action lease id/expiry/
  terminal state, action mutation id/outcome/evidence id;
- protected approved-absent set binding id/distinct-key count and target absence-
  revalidation evidence id;
- trusted target baseline id/alias/state/evidence, target-identity preparation
  approval id/state/deadline, and protected exact target DB binding id/state/
  validity/evidence id;
- target operation fence id/state/generation/evidence and exact consumer action;
- reconciliation source action/failure class, creation state/evidence id and, if created, record id/state/
  observation/claim deadline/retention/disposition/evidence plus safe counts;
- upload job id;
- approved target-only rows;
- job final status;
- file counts;
- processed/uploaded/accepted rows;
- audit evidence for start and final status;
- DB delta evidence when explicitly approved and on;
- row attribution evidence when explicitly approved and on;
- whether failure requires investigation or Retry Failed.

If Start Upload fails, the action transaction must roll back every action DB
write before lease release or disposition. Any evidence of partial mutation is a
contract violation: preserve job, audit, DB delta, and row attribution evidence,
mark the chain blocked, and do not run Retry Failed or DB cleanup.

## Phase 4: Retry Failed

Retry Failed is not automatic rollback. It is a new upload action with its own
approval.

The approval id must resolve to an immutable/authenticated protected record in
state `available`, bound to package/operator/source, source job, exact freshly
reconciled still-absent physical rows/files, root failure class, deadline,
`actionMaxDurationSeconds`, `snapshotDispositionMarginSeconds`, the same
`contentSnapshotRecordId`, and the same
`atomicSnapshotBindingEvidenceId` as the
source job, plus one random unique pre-reserved `actionMutationId` and the exact
protected `retryReconciliationRecordId`/observation/deadline, which is also the
protected `actionApprovedAbsentSetBindingId`, plus exact distinct
`actionApprovedAbsentKeyCount`, the same verified/non-revoked trusted target
baseline id/alias/state/evidence, and the same consumed
`targetIdentityPreparationApprovalId` plus protected `targetDbBindingId`, state,
validity ceiling, and evidence from Preview/source action/reconciliation, plus
the same `targetGlobalCoordinatorId` in `chain_ready` naming this chain fence as
sole owner with empty consumer and exact generation/evidence, and the same
`targetOperationFenceId` in fence state `idle` with upload branch `retryable` and
exact generation/evidence. At
claim time the binding must be `retryable` and unexpired, and the unrenewable
action lease plus `snapshotDispositionMarginSeconds` must end no later than
`min(targetDbBindingValidUntilUtc, contentSnapshotRetainUntilUtc)`. The snapshot must
be `retryable`, and the approved Retry subset must
come from fresh exact DB reconciliation of the entire prior attempted subset and
refer only to that snapshot; a worker cursor or pre-rollback remainder is
invalid. Production code must atomically claim the approval, snapshot, target-
global coordinator, and chain operation fence, create
one active-use lease plus claim of that pre-reserved `actionMutationId`, claim
the reconciliation record, and create the retry job/event
atomically; it rejects missing/expired/substituted/duplicate/concurrent
claims and finishes `consumed` with exactly one
retry action or `invalid` only when no retry job/event commits. Once exactly one
action commits, the approval is permanently `consumed` regardless of later
succeeded/failed/cancelled outcome or response loss. The Retry worker must read
only the protected snapshot before `contentSnapshotRetainUntilUtc`, while
disposition is `scheduled`, and must never reopen the operational source. Its DB
mutation and durable target outcome marker must share the authoritative
transaction/fence defined above; local timeout or lease expiry cannot assert
rollback. Until this lifecycle and deterministic tests exist, Retry Failed
remains blocked even if the wording is filled.

| Retry stage | Approval state | Reconciliation entitlement/record | Snapshot state | Action lease | Mutation outcome | Retry job/event state | Required result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Before creation | `available` | `record_available` / `available`, exact/unexpired/`scheduled` | `retryable` | absent | `not_started`, pre-reserved id | absent | Exact bindings including consumed target-identity preparation approval, `targetDbBindingId`/state/validity/evidence, protected absent set/distinct-key count, confidentiality/retention, duration/margin budget, and all deadlines are rechecked; the binding is unexpired and the proposed lease fits both validity ceilings. |
| Atomic creation transaction | `claimed` | `record_available` / `claimed` | `retry_claimed` | `active`, inserted atomically | `not_started`, pre-reserved id claimed | being inserted | The target binding is atomically rechecked as the same unexpired `retryable` binding and becomes `upload_bound`; concurrent/duplicate claims cannot commit another record/lease/action. |
| Creation fails before action commit | `invalid` | `invalid` / `invalid`, disposition triggered | `invalid` | absent/`expired_rolled_back` | `not_started` | absent | Zero DB writes; a new authorized reconciliation and approved chain are required. |
| Exactly one retry record commits | `consumed` | `record_consumed` / `consumed` | `upload_bound` | `active` | `not_started` | committed, nonterminal | Approval and reconciliation records stay consumed and the action uses only their exact protected subset/snapshot under this lease. |
| Target outcome marker prepared | `consumed` | `record_consumed` / `consumed` | `upload_bound` | `active` | `prepared` | running | Exactly one target-clock-fenced marker is durable; no `all_metrics` write has occurred. |
| Target transaction in flight | `consumed` | `record_consumed` / `consumed` | `upload_bound` | `active` | `commit_pending` | running | On the same authoritative transaction, revalidate exact target identity and unexpired binding with the target clock, then under serializable/key fencing revalidate the whole still-absent set and use conflict-rejecting conditional inserts; disposition and duplicate mutation are blocked. |
| Target absence drift/conflict before commit | `consumed` | consumed input becomes `awaiting_successor_reconciliation`; it is disposed only after one new source entitlement/record atomically claims/copies the exact whole-attempt subset and publishes | `upload_bound -> retryable` only in the new reconciliation publication CAS | `released_rolled_back` | `rolled_back` with absence evidence | terminal failed/retryable | Zero action `all_metrics` writes and no overwrite; marker rollback alone keeps the snapshot bound. Another Retry becomes visible only when the new whole-attempt record and ready generations publish atomically, followed by separate approval. Expiry before publication disposes the old record and permanently blocks the chain. |
| Target commit marker proves success | `consumed` | `record_consumed` / `consumed`, disposition triggered | `completed` | `released_committed` | `committed` with absence evidence | terminal succeeded/recovered succeeded | Exact inserted keyset/count equals the protected record binding; preserve sanitized evidence, block reads, and start automatic disposition. |
| Retriable failure/cancellation proves rollback before lease expiry | `consumed` | consumed input becomes `awaiting_successor_reconciliation`; successor publication atomically claims/copies the exact subset before old-record disposition | `upload_bound -> retryable` only in the new reconciliation publication CAS | `released_rolled_back` | `rolled_back` with evidence | terminal failed/retryable/cancelled | Marker rollback alone keeps the snapshot bound. Reconcile the entire attempted Retry subset under one new entitlement; only its atomic record/generation publication exposes another Retry. Expiry before publication disposes the old record and permanently blocks the chain. |
| Non-retryable failure proves rollback | `consumed` | consumed input disposition triggered; no new record | `invalid` | `released_rolled_back` | `rolled_back` with evidence | terminal failed/blocked | Start automatic disposition; final decision is blocked/failed-preserved and further Retry is forbidden. |
| Crash/timeout/response loss after possible target commit | `consumed` | consumed input retained under the active unknown-outcome boundary | `upload_bound` | `commit_unknown_blocked` | `commit_unknown_blocked` | terminal/nonterminal blocked | Do not infer rollback, dispose early, Retry, or create another action; reconcile the target marker. |
| Target-marker reconciliation proves commit | `consumed` | consumed input disposition triggered | `completed` | `released_committed` | `committed` with evidence | recovered succeeded | Use the same retry/mutation id and continue only to disposition. |
| Target marker is guarded-finalized `aborted`, observed before lease expiry, and action is retryable | `consumed` | consumed input becomes `awaiting_successor_reconciliation`; one new source entitlement becomes `record_available` only when publication CAS claims/copies the exact subset and starts old-record disposition | `upload_bound -> retryable` only in that publication CAS | `released_rolled_back` | `rolled_back` with evidence | recovered failed/retryable | Marker finalization alone does not expose Retry. The atomic reconciliation record plus new ready generations define the next Retry scope as the whole-attempt still-absent subset. Expiry before publication disposes the old record and permanently blocks the chain. |
| Target marker is guarded-finalized `aborted` at/after lease expiry or first observed then | `consumed` | consumed input disposition triggered; no new record | `invalid` | `expired_rolled_back` | `rolled_back` with evidence | terminal failed/blocked | Start disposition; no further Retry from this expired action. |
| Outcome remains unknown at retention deadline | `consumed` | consumed input forcibly disposed with snapshot; no new record | `invalid` then inaccessible | `commit_unknown_blocked` | `commit_unknown_blocked` | terminal blocked | Perform mandatory cryptographic disposition and permanently block this chain; this approval authorizes no post-retention DB read. |
| Duplicate request after action commit/response loss | `consumed` | same entitlement/record/disposition state | current recorded state | same recorded lease | same mutation id/outcome | the same committed action | Return/preserve the existing binding; never create another action. |

Tests must cover missing/unresolvable ids, source-job/count mismatch, approval/
reconciliation/target-binding expiry, target-binding expiry immediately before/
at/after atomic claim, marker creation, mutation transaction, outcome/
whole-attempt reconciliation, lease or reconciliation deadline beyond the target-
binding or snapshot-retention ceiling,
substitution of every package/operator/source/source-job/file/row/failure-class/
deadline/snapshot/atomic-evidence/duration/margin/mutation-id/reconciliation-
record/target-DB-binding/absent-set-id/distinct-key-count field, concurrent claims,
failure before commit, crash/response loss after target commit but before local
lease release, target-marker reconciliation, worker failure/cancellation,
failure after reported progress followed by full rollback and whole-subset
reconciliation, duplicate request after response loss, and inconsistent
approval/snapshot/lease/outcome/action states. They must also cover operational-source change before
Retry, equal-size/equal-mtime replacement, concurrent source writes, missing/
tampered snapshots, and worker source-reopen attempts. Any mismatch before
mutation must produce zero DB writes.

Before Retry Failed, record:

- source job id;
- terminal failed or retryable state;
- retryable file count summary without filenames;
- fresh exact reconciled still-absent physical rows, not a worker cursor
  remainder;
- reason class for retry eligibility.

After Retry Failed, record retry job id or retry event id, accepted rows, final
status, approval id/deadline/terminal state, trusted target baseline id/alias/
state/evidence, target-identity preparation approval id/state/deadline/claim
owner/fence, and target DB binding id/state/validity/evidence,
target-global coordinator id/state/owner/consumer/generation/evidence, target
operation fence id/state/generation/evidence and exact consumer action,
reconciliation source action/
failure class and creation state/
evidence, record id/state/observation/claim deadline/retention/disposition/
evidence and source-action/mutation/outcome/target-DB binding, protected content snapshot record
id/state/retention deadline/disposition state/snapshot disposition evidence id,
action maximum duration, disposition margin, snapshot action lease id/expiry/
terminal state, action mutation id/outcome/evidence id, atomic snapshot binding
evidence id, protected approved-absent set id/distinct-key count, target absence-
revalidation evidence id, audit evidence, and whether any
unresolved failure remains.

## Stop Conditions

Stop before any operational upload mutation when any of these are true:

- package metadata or checksum differs from the accepted package record;
- inventory is missing, stale, guessed, or broader than the requested approval;
- inventory evidence record id, operator PC class, or privacy-safe source alias
  is missing or differs from approval;
- inventory observation time, approved maximum age, or execution deadline is
  missing, expired, inferred, or differs from approval;
- the immediately-before-call read-only scan is absent or does not confirm the
  exact file set, scope, size/mtime metadata, counts, package, operator PC,
  source alias, and source class are unchanged;
- the stage-specific approval/manifest state differs from the transition table;
  in particular, before Preview claim the preparation approval must be
  `consumed`, manifest and snapshot `prepared`, and Preview approval `available`;
- an approval/record is missing, expired, tampered, unauthenticated, mismatched,
  regressed, double-claimed, or reused outside its valid stage, or private
  manifest material would be published;
- `manifestPreparationApprovalId` or `previewApprovalId` is missing or differs
  between approval, protected manifest creation, atomic claim/run, terminal
  evidence, and final sign-off;
- `manifestPreparationExecuteByUtc` is missing/inferred, exceeds the inventory
  observation plus human maximum age, or preparation claim/completed publication
  occurs after it;
- atomic snapshot binding is not implemented and regression-tested, or Preview
  cannot prove that the content verified against the approved manifest is the
  same immutable content it parsed or prevent record replay;
- the protected snapshot is missing, mutable, tampered, mismatched, expired,
  in the wrong stage state, or Start/Retry would reopen the operational source;
- disposal is `in_progress`/`disposal_failed_blocked`, a terminal/deadline trigger
  lacks valid `snapshotDispositionEvidenceId`, or new preparation is requested
  while an earlier failed disposition remains unresolved;
- Start Upload is requested without a protected, unexpired
  `startUploadApprovalId` in state `available` whose exact bindings are
  atomically claimed with the `previewed` snapshot and creation of one upload
  job, or a mismatch could occur without guaranteeing zero DB writes;
- Retry Failed is requested without a protected, unexpired `retryApprovalId` in
  state `available` whose exact bindings are atomically claimed with creation of
  one retry job/event against the same `retryable` snapshot, or a mismatch could
  occur without guaranteeing zero DB writes;
- Start/Retry lacks exact human duration/disposition-margin bindings, one
  unrenewable target-fenced lease, the exact random mutation id pre-reserved in
  its immutable approval, or a durable target outcome marker committed atomically
  with all action writes;
- Start/Retry lacks one protected exact absent-set binding and distinct-key count,
  serializable in-transaction whole-set absence revalidation, canonical fences
  used by every application writer, conflict-rejecting conditional inserts, or
  exact committed-keyset verification; any target drift/conflict can overwrite an
  existing row or leave action writes instead of full rollback;
- commit/non-commit is inferred from timeout, response loss, local job state, or
  lease expiry; `commit_unknown_blocked` is treated as rollback/retryability; or
  disposition could race an active/commit-pending action;
- Retry rows/files come from a worker cursor or pre-rollback remainder instead
  of fresh exact DB reconciliation of the entire prior attempted snapshot subset
  after authoritative rollback evidence;
- Retry lacks an unexpired protected reconciliation record that is atomically
  claimed once with the approval/snapshot/job/lease, or its source action,
  mutation outcome, attempted subset, private still-absent subset, safe counts,
  observation, or deadline is substituted, stale, replayed, or mismatched;
- a source action can create more than one reconciliation record, its durable
  creation entitlement is absent/regressed/replayed, crash/response-loss recovery
  can publish a sibling, or Retry does not require the unique entitlement/record
  binding for that source `actionMutationId`;
- a reconciliation record's exact private subset is not owner-only, encrypted,
  tamper-evident, bounded by snapshot retention, and cryptographically disposed
  on terminal action/invalidation/expiry/snapshot disposition, or its disposal is
  `in_progress`/`disposal_failed_blocked` without safe evidence and blocking;
- source class differs from approval;
- raw operational path, filename, key, DB URL, token, credential, raw SQL, or
  secret would be written into evidence;
- Preview is not fresh, latest, succeeded, and DB-reachable;
- risky count is greater than zero;
- target-only rows differ across UI, API, and approval text;
- target-class or runtime readiness is not ready;
- trusted target baseline id/alias/state/evidence is missing, unresolved,
  substituted, revoked, self-attested from first observation, or differs across
  target preparation/Preview/Start/Retry/marker/reconciliation/final sign-off;
  observed exact identity was not compared to its owner-only expected identity;
- `targetIdentityPreparationApprovalId`, its terminal state/deadline, or
  `targetDbBindingId`/state/validity/evidence is missing, unresolved, substituted,
  was expired at any Preview/Start/Retry/marker/reconciliation DB access or
  action/reconciliation deadline, or differs across those stages/final
  sign-off; authoritative exact target identity or unexpired validity is not
  revalidated on the same DB session/transaction before every DB read/write; or
  an action lease/reconciliation deadline exceeds the minimum target-binding and
  snapshot-retention ceiling;
- target operation fence id/state/generation/evidence is missing, substituted,
  regressed, reused, or not atomically claimed with the stage approval/record;
  Start/Retry/Delete can hold concurrent consumers, Retry does not require
  `retryable`, Delete consumes a terminal/upload chain, or a losing/stale claimant
  can publish a record or perform DB reads/writes;
- Edge auth class is not ready for the current function auth mode;
- local token protection is not active for protected writes;
- audit evidence cannot be read after a run;
- request bundles Preview, Start Upload, Retry Failed, Delete, Settings save,
  feature-gate enablement, reset, cleanup, LAN, or deploy.

## V2 Completion Interpretation

Item 1 can be considered completed only for the scope actually evidenced:

- `no_upload` if fresh inventory and Preview-only prove there are no target
  rows and no upload mutation ran;
- `upload_succeeded` if Start Upload is separately approved, runs exactly once
  from the same protected snapshot Preview verified, and either its target
  marker proves committed success or a sequence of marker-proven complete
  rollbacks plus freshly reconciled, separately approved Retries ends in one
  marker-proven committed success with zero remaining rows; every lease/outcome/
  job/approved-absent-set binding, transaction-time absence evidence, and post-
  run evidence is preserved, including exact equality of the target-identity
  trusted target baseline id/alias/state/evidence, target-identity preparation
  approval id/state/deadline, and target DB binding id/state/validity/evidence
  across approval, execution, reconciliation, and final sign-off;
- a Start target-state-drift/conflict abort cannot be part of that recovered
  sequence; it invalidates the chain and only a later fresh Preview chain can
  produce independent `upload_succeeded` evidence;
- `failed_preserved` only as an investigation artifact, not as successful upload
  verification;
- `blocked` when any stop condition triggers.

Do not describe item 1 as full operational upload completion from a Preview-only
run, a no-upload day, a failed job, an old package, or an approval tied to a
different source commit.

## Rollback

Document-only rollback before commit:

```powershell
git restore --staged --worktree CHANGELOG.md docs\165_v2_status_matrix.md
git rm --cached --ignore-unmatch docs\173_v2_operational_upload_verification_gate.md
Remove-Item -LiteralPath docs\173_v2_operational_upload_verification_gate.md
```

After commit, revert the document commit.

Operational rollback, if a later approved upload verification runs, is not DB
cleanup. Preserve preview/job/audit/DB delta/row-attribution evidence, stop
additional mutation, and use a separately approved Retry Failed or fix-forward
path only when the evidence supports it.
