# V2 Operational Delete Verification Gate

Date: 2026-06-22 Asia/Seoul

Status: `blocked_pending_atomic_single_use_delete_preflight_and_mutation_approval_lifecycles_no_operational_mutation`

> **Mandatory runtime blocker:** This document's approval record and wording are
> necessary evidence but are not sufficient authorization. Operational delete
> remains blocked until production code and deterministic tests implement the
> lifecycle addendum in `docs/164_operator_data_mutation_safety_gate.md`: a
> protected expiring `approvalId`/`deleteApprovalId` with
> `available -> claimed -> consumed|invalid`, atomically bound to at most one
> `deleteRunId`, and the exact preflight result with
> `ready_available -> claimed -> consumed|invalid`, atomically bound to the same
> approval/run. `invalid` is allowed only when no run commits; after one run
> commits, approval remains consumed through response loss, `commit_unknown`,
> failure, cancellation, audit/evidence failure, and reconciliation. Duplicate
> requests return/reconcile the same run, and pre-commit mismatch produces zero
> operational DB writes.
> Every newer field/state-machine requirement below is equally mandatory,
> including the exact-target singleton coordinator, preflight claim owner/fence/
> completion deadline, owner-only exact-byte source-provenance snapshot, an exact
> DB before-image written atomically with Delete, their bounded recovery-
> disposition lifecycle, and a pre-reserved target-side Delete mutation marker
> with marker-first reconciliation. Approval/run/result lifecycles alone do not
> unblock Delete. A CSV/source snapshot with matching keys is not an exact DB
> rollback image and can never make `rollbackReadiness=true` by itself.
> The prerequisite operational delete preflight is separately blocked until the
> protected expiring `deletePreflightApprovalId` lifecycle in `docs/164` is
> implemented/tested and atomically bound to exactly one `deletePreflightId`.
> The later hard-delete approval cannot be reused to authorize that earlier DB
> read/local evidence write.

## Purpose

This document defines the gate for V2 item 5, operational DB delete
verification.

It does not approve operational DB access, delete preflight, hard delete,
reconcile, feature-gate enablement, Upload Preview, Start Upload, Retry Failed,
Settings save, Supabase reset/cleanup, Docker cleanup, LAN exposure,
deployment, production DB schema/recovery-store migration, or fixture mutation.

The current executable delete baseline remains
`docs/156_operator_already_in_db_delete_contract.md`: selected Upload Preview
items with status `already_in_db`, exact-key preflight, typed exact count,
no-undo acknowledgement, rollback-limitation acknowledgement, local DB target
guard, DELETE privilege preflight, audit evidence, and all-or-nothing delete
semantics.

## Plain-Language Rule

Operational delete verification is not "try a delete and see what happens."

Before any operational delete is allowed, the approval must name exactly what
will be deleted, prove the target is the intended DB, prove the protected target
can atomically preserve the complete typed pre-delete rows, prove rollback
limitations are understood, and define the evidence report that will be
preserved after the run.

If those facts are not known, the correct action is to stop. Do not substitute a
broad approval, a guessed row count, a raw SQL query, or a manual DB cleanup.

## Approval Record Storage

Operational delete approval must be stored before mutation in an immutable or
append-only location.

Approved storage options:

- a dedicated sanitized markdown file under `docs/operator-evidence/` that is
  committed before mutation, with the commit SHA recorded in the evidence
  report;
- an internal operator record system that preserves timestamp, approver,
  executor, package source commit, and exact approval text in an append-only
  record.

GitHub PR or issue links may point to committed evidence or an internal
append-only record, but an editable PR body, issue body, or comment is not an
approved approval-record store by itself.

The approval record must not be edited after mutation. Corrections must be
append-only and must explain what changed, who changed it, and why the original
evidence remains preserved.

The human-approved payload remains immutable. Mutable-looking lifecycle fields
below are implemented as authenticated append-only transition records linked to
that payload; claiming or completing a lifecycle never rewrites the approved
scope or approval text.

The approval record must not contain raw operational source paths, filenames,
CSV row content, raw DB before-image values, raw `(timestamp, device_id)` keys,
raw SQL, DB URLs, tokens,
Authorization values, JWTs, credentials, internal URLs, or secret values.

Committed or otherwise externally visible approval/evidence records may contain
only opaque random protected-record ids, safe classes/counts, approved package
hashes, and reason codes. They must not contain deterministic digests derived
from a selection, exact keyset, source evidence, source file signatures, paths,
or filenames. Exact material, schema-verification material, and their integrity
data remain in an authenticated, owner-only protected store. If that store uses
digests, it must use versioned, domain-separated keyed HMACs under a non-exported
key; neither a private data/schema HMAC nor the key may be copied into repository
markdown, PRs, issues, audit payloads, or operator-facing evidence.

The current API fields named `selectionHash` and
`selectionDataHash`/`keysetHash` are legacy unkeyed digests, not approved public
evidence or approval bindings. The former draft fields `sourceEvidenceHash` and
`sourceFileSignatureSetHash` are rejected for the same reason. Small candidate
sets can make such digests guessable. Operational Delete remains blocked until
production code replaces their approval/evidence role with the protected opaque
bindings below and tests their confidentiality, integrity, and lifecycle.

The current `dbFingerprintHash` is also diagnostic only: it hashes coarse safe
host/port/database/schema/project classes and cannot distinguish a different
local cluster/database with the same classes. It is not an authorization
boundary. Operational Delete additionally requires the opaque `targetDbBindingId`
below, backed by authenticated exact DB-instance and database identity in the
owner-only protected store, from preflight approval through reconcile.

The current API's `rollbackReadiness=true` is likewise legacy and non-operational:
it is derived from source/key evidence and does not prove that current DB values
can be restored. Production code must implement the two-stage state below
(`false_pending_atomic_before_image -> true` only in the Delete transaction) and
must reject the legacy boolean as an authorization input.
Implementing the protected target-side before-image store will require a separate
production-code/schema work package, migration/rollback design, and explicit
approval. This document specifies that future contract but authorizes none of
those changes or any operational run.

## Required Approval Fields

Every operational delete approval record must include:

| Field | Required value |
| --- | --- |
| `approvalId` | Stable safe id for the approval record. |
| `deleteApprovalState` | `available` before the one-run claim; later transitions follow `docs/164`. |
| `deleteExecuteByUtc` | Hard deadline for the one-run delete claim. |
| `packageSourceCommit` | Exact package source commit approved for the run. |
| `packageLabel` | Package label or safe package id, without raw local path. |
| `zipSha256` | Required when `zipCreated=true`; otherwise `not_applicable`. |
| `dbTargetClass` | Safe target class such as `local_supabase_operator_db`, not a raw DB URL. |
| `dbFingerprintHash` | Safe coarse diagnostic hash from preflight evidence; never sufficient as the target authorization boundary. |
| `trustedTargetBaselineId` | Random non-derived opaque pre-existing owner-only expected-target baseline id established from separately verified installation/runtime provenance; first observation cannot create it. |
| `trustedTargetAlias` | Human-supplied/reviewed privacy-safe exact-target alias mapped to that baseline; never a deterministic derivative of raw target identity. |
| `trustedTargetBaselineState` | Must be `verified` and non-revoked. |
| `trustedTargetBaselineEvidenceId` | Random non-derived opaque safe out-of-band verification evidence id; exact identity and all keyed integrity values remain owner-only. |
| `targetIdentityPreparationApprovalId` | Consumed protected approval that created this exact target binding. |
| `targetIdentityPreparationApprovalState` | Must be terminal `consumed`. |
| `targetIdentityPreparationExecuteByUtc` | Exact claim/publication deadline from that approval. |
| `targetDbBindingId` | Opaque random id resolving only in the owner-only protected store to authenticated exact DB-instance and database identity; bound through preflight approval/result, delete approval/run, and reconcile. |
| `targetDbBindingState` | Must follow the canonical Delete target-binding subtable in `docs/173`: `previewed` or `upload_completed_delete_ready` remains unchanged through preflight, the joint hard-Delete claim atomically advances it to `delete_bound`, every marker/reconcile/recovery-pending path retains `delete_bound`, target mismatch before commit advances to `invalid` with zero Delete writes, and only verified terminal restore/disposition advances it to `completed`. `commit_unknown_blocked` or disposal failure may not advance it. |
| `targetDbBindingValidUntilUtc` | Non-extendable validity ceiling covering preflight, delete, approved reconcile, and any bounded before-image restore window; it must be no earlier than `deleteDbBeforeImageRetainUntilUtc`. |
| `targetDbBindingEvidenceId` | Opaque safe evidence for the protected target-identity lifecycle. |
| `deleteReconcileByUtc` | Hard deadline for any same-run read-only reconcile; no later than target binding validity. |
| `targetGlobalCoordinatorId` | Random non-derived opaque id resolving to the singleton protected coordinator for this exact trusted target across every Preview chain. |
| `targetGlobalCoordinatorState` | Must name this chain as the sole ready/active owner; after a resolved Delete it remains `recovery_disposition_pending` until restore/disposal closes. No older/newer Preview chain may overlap. |
| `targetGlobalCoordinatorOwnerFenceId` | Must equal this exact `targetOperationFenceId`. |
| `targetGlobalCoordinatorConsumer` | Exact target-global consumer, atomically changed with the chain consumer; empty at preflight eligibility, `delete_preflight`/`delete` during those stages, and `delete_disposition`/`delete_restore` only during the separately approved close. |
| `targetGlobalCoordinatorGeneration` | Monotonic target-global generation CAS-checked by Preview, preflight, Delete, Start, Retry, marker, and reconcile. |
| `targetGlobalCoordinatorEvidenceId` | Opaque safe evidence for the exact target-global owner/state/generation transition. |
| `targetOperationFenceId` | Random opaque protected fence shared with Start/Retry for this Preview/target binding. |
| `targetOperationFenceState` | Chain exclusion state; preflight claims `idle -> claimed -> active`, and Delete begins only while the preflight result owns fence state `active`, consumer `delete_preflight`, and separate `targetDeleteBranchState=delete_ready`. Resolved Delete remains `recovery_disposition_pending` until restore/disposal closes. |
| `targetUploadBranchState` | Must not be active/retryable-owned by Start/Retry when Delete preflight or Delete claims. |
| `targetDeleteBranchState` | `delete_preflight_ready` before preflight, `delete_ready` before the one Delete claim, then `recovery_disposition_pending` after resolved outcome until restore/disposal closes. |
| `targetOperationConsumer` | Empty at preflight eligibility, `delete_preflight` while/result-owned, `delete` for the run and recovery-pending hold, then `delete_disposition` or `delete_restore` only for the separately approved close. |
| `targetOperationFenceGeneration` | Exact monotonic generation atomically advanced by each claim/terminal transition. |
| `targetOperationFenceEvidenceId` | Opaque safe evidence for the exact state/generation/consumer transition. |
| `schemaClass` | Public non-secret versioned class for the expected contract, such as `all_metrics_timestamp_device_id_unique_v1`. |
| `schemaBindingId` | Opaque random id resolving only in the owner-only protected store to exact schema-verification material and any private keyed HMAC. |
| `deleteDbMutationSchemaFenceBindingId` | Opaque protected binding to every relation/catalog object and engine-appropriate DDL-conflicting lock or enforced monotonic schema-generation fence needed by both DELETE and exact restore INSERT. Each authoritative transaction acquires the bound fence before side-effect inspection, revalidates only after acquisition, and holds it through commit so concurrent DDL/configuration cannot invalidate the proof. |
| `deleteDbMutationSideEffectBindingId` | Opaque protected binding to complete side-effect inspection for both the exact-key DELETE and the later exact restore INSERT: foreign-key/cascade dependencies, DELETE/INSERT triggers and rules, RLS/policies, generated/default expressions, sequences, replication/publication/CDC hooks, transactional notifications, and every affected relation. Exact definitions remain owner-only. |
| `deleteDbMutationSideEffectReadiness` | Must be `direct_rows_only_no_unmodeled_or_nonrestorable_effects`: every listed class is absent or proven inert so only the selected direct rows can change and no externally observable secondary effect occurs. Otherwise DELETE and restore both perform zero writes; this contract does not permit a merely “modeled” secondary affected graph. |
| `previewRunId` | Exact Preview run id used for selection. |
| `deletePreflightApprovalId` | Exact protected approval id consumed by the one preflight run. |
| `deletePreflightApprovalState` | Must be `consumed`. |
| `deletePreflightExecuteByUtc` | Exact preflight-claim deadline from the protected approval. |
| `deletePreflightCompleteByUtc` | Human-supplied absolute deadline for source-provenance-snapshot and preflight-result publication. |
| `deletePreflightClaimId` | Opaque durable owner token created before any source copy or DB read. |
| `deletePreflightFence` | Monotonic generation advanced by claim, restart, expiry, invalidation, and terminal publication; stale workers cannot copy, read, or publish. |
| `deletePreflightId` | Exact unexpired delete preflight id. |
| `deletePreflightState` | Must be `ready_available` before the joint one-run claim and `consumed` after a run commits. |
| `consumedByDeleteApprovalId` | Empty before claim; after run commit must equal this exact `approvalId` permanently. |
| `deleteRunId` | Empty before claim; generated and atomically bound to both the approval and preflight result when exactly one run commits. |
| `deleteMutationId` | Random unique target mutation id pre-reserved in the immutable hard-delete approval and claimed only with its approval/preflight/run/source-provenance/before-image/coordinator bindings. |
| `deleteMutationOutcomeState` | `not_started`, `prepared`, `commit_pending`, `committed`, `aborted`, or `commit_unknown_blocked`; row presence/delta never determines it. |
| `deleteMutationOutcomeEvidenceId` | Opaque safe evidence from the immutable target marker or marker-first reconciliation. |
| `selectedAlreadyInDbItems` | Exact selected `already_in_db` item count. |
| `exactKeyCount` | Exact selected key count approved for delete. |
| `selectionBindingId` | Opaque random id resolving only in the owner-only protected store to the exact approved selection and its private integrity data. |
| `keysetBindingId` | Opaque random id resolving only in the owner-only protected store to the exact approved keyset and its private integrity data. |
| `sourceEvidenceBindingId` | Opaque random id resolving only in the owner-only protected store to exact source evidence without publishing a source-derived digest. |
| `sourceFileSignatureSetBindingId` | Opaque random id resolving only in the owner-only protected store to the exact source-file signature set and parsed keyset. |
| `deleteRecoverySnapshotId` | Legacy-named opaque random id for the owner-only encrypted immutable exact-byte **source-provenance** snapshot created under the preflight approval before any preflight DB read; it is distinct from and may not reuse an upload snapshot. It is not an exact DB rollback image. |
| `deleteRecoveryContentBindingId` | Opaque protected binding to private source-byte digests, file boundaries, parsed keys, and source provenance; no digest or filename is public and this binding alone cannot prove DB rollback readiness. |
| `deleteRecoverySnapshotState` | `preparing`, `prepared`, `preflight_bound`, `delete_bound`, `awaiting_recovery_disposition`, `disposed`, `disposal_failed_blocked`, or `invalid`; no source reopen or state regression is allowed. |
| `deleteRecoveryObservedBytes` | Exact read-only observed byte count reviewed before approval; never inferred. |
| `deleteRecoverySnapshotMaxBytes` | Human-approved non-inferred byte ceiling bound in the preflight approval. |
| `deleteRecoverySnapshotRetainUntilUtc` | Human-approved non-extendable retention/access deadline covering Delete, same-run reconcile, and the final recovery decision. A hard-delete approval may proceed only when `deleteDbBeforeImageRetainUntilUtc` is exactly this same deadline. |
| `deleteRecoveryCapacityEvidenceId` | Opaque safe evidence that protected storage can hold the approved bytes. |
| `deleteRecoveryConfidentialityClass` | Approved owner-only encryption/access-control class; no raw path or key material. |
| `deleteRecoveryDispositionState` | `scheduled`, `awaiting_recovery_disposition`, `in_progress`, `disposed`, or `disposal_failed_blocked`; key destruction and verified byte removal are mandatory on invalidation/preflight block/expiry or after the final recovery decision. |
| `deleteRecoveryFinalDispositionDecision` | Canonical pre-disposition sentinel is `not_decided`. After a resolved Delete, committed permits dual-record `accept_delete_and_dispose` or `separately_approved_restore_then_dispose`; aborted permits source-only `accept_delete_and_dispose` and makes restore not applicable. |
| `deleteRecoveryDispositionApprovalId` | Immutable/authenticated expiring single-use approval required for early `accept_delete_and_dispose`; `not_issued` until a human reviews the marker-proven outcome. Retention-expiry disposal of the source snapshot uses the original preflight approval; disposal of a committed DB before-image separately uses the consumed hard-delete approval that pre-reserved it. |
| `deleteRecoveryDispositionApprovalState` | `not_issued` before a human issues it; then `available`, `claimed`, `consumed`, or `invalid`. Disposition may claim it once atomically with the exact snapshot cleanup action. |
| `deleteRecoveryDispositionExecuteByUtc` | `not_approved` before issuance; otherwise a human-supplied early-disposition deadline no later than the minimum of source-snapshot and DB-before-image retention when a committed Delete created both records, or no later than source-snapshot retention for an aborted Delete with no DB before-image. |
| `deleteRecoveryDispositionEvidenceId` | Opaque safe evidence of cryptographic disposition; required after access closes. |
| `deleteDbBeforeImageId` | Random opaque id pre-reserved by the hard-delete approval for the owner-only encrypted exact DB before-image. The complete typed value of every column in every selected row is inserted under this id in the same authoritative transaction as the exact-key DELETE and committed marker transition. |
| `deleteDbBeforeImageContentBindingId` | Opaque protected binding to the complete canonical typed pre-delete row set; raw values and private integrity material remain owner-only. |
| `deleteDbBeforeImageSchemaBindingId` | Opaque protected binding to the exact table/schema version used to capture and later restore the before-image. |
| `deleteDbBeforeImageColumnSetBindingId` | Opaque protected binding to the complete ordered column set, including null/default/generated/system-column treatment. Any column that cannot be captured and restored exactly keeps `rollbackReadiness=false_pending_atomic_before_image` and forces transaction abort with zero DELETE. |
| `deleteDbBeforeImageRowCount` | Exact selected row count captured transactionally; it must equal `exactKeyCount` before DELETE. |
| `deleteDbBeforeImageObservedBytes` | `not_observed` in the approval; exact protected serialized bytes recorded by the authoritative transaction and required to be no greater than the approved ceiling. |
| `deleteDbBeforeImageMaxBytes` | Human-approved, non-inferred encrypted before-image byte ceiling named by the hard-delete approval. Overflow causes transaction rollback and zero DELETE. |
| `deleteDbBeforeImageCapacityEvidenceId` | Opaque safe evidence that the protected target-side recovery store has capacity for the approved ceiling before mutation. |
| `deleteDbBeforeImageConfidentialityClass` | Approved owner-only encryption/access-control class for exact DB row values. |
| `deleteDbBeforeImageRetainUntilUtc` | Human-approved non-extendable deadline exactly equal to `deleteRecoverySnapshotRetainUntilUtc`, no earlier than Delete reconcile and the final recovery-disposition window. Unequal deadlines invalidate the hard-delete approval before mutation. |
| `deleteDbBeforeImageState` | `not_created` before the authoritative transaction, `recovery_available` only when before-image + exact DELETE + committed marker have committed atomically, then `restoring`, `restored`, `disposed`, `disposal_failed_blocked`, or `invalid`; a committed Delete with missing/mismatched before-image is permanently blocked. |
| `deleteDbBeforeImageDispositionEvidenceId` | Opaque safe evidence for key-first disposal and verified byte removal of the before-image after accepted Delete or separately approved exact restore. |
| `deleteDbRestoreApprovalId` | `not_issued` in the hard-delete approval; a later random immutable/authenticated expiring single-use approval id is required for exact restore. |
| `deleteDbRestoreApprovalState` | `not_issued` before human review; then `available`, `claimed`, `consumed`, or `invalid`. |
| `deleteDbRestoreExecuteByUtc` | `not_approved` before issuance; otherwise a human-supplied claim deadline no later than the non-renewable restore active-use lease. |
| `deleteDbRestoreActiveUseExpiresAtUtc` | `not_approved` before issuance; otherwise the unrenewable authoritative-transaction commit deadline. It must be strictly earlier than `deleteDbRestoreReconcileByUtc`. A transaction at or after it rolls back every restore write. |
| `deleteDbRestoreReconcileByUtc` | `not_approved` before issuance; otherwise the last marker-first read-only reconcile/equality-publication deadline, no later than the minimum of target-binding validity and before-image retention after reserving the approved disposition margin. Reconcile after active-use expiry may prove an already committed marker but may issue no restore write. |
| `deleteDbRestoreDispositionMarginSeconds` | Positive human-approved margin between restore reconcile completion and the minimum target-binding/before-image deadline, sufficient for terminal disposition or safe blocked evidence publication. |
| `deleteDbRestoreMutationId` | `not_created` before issuance; later a random unique id pre-reserved in the restore approval for an atomic before-image restore marker/transaction. |
| `deleteDbRestoreOutcomeState` | `not_created`, then `prepared`, `committed`, `aborted`, or `commit_unknown_blocked`; current row presence never determines the outcome. |
| `deleteDbRestoreOutcomeEvidenceId` | Opaque safe evidence from the immutable restore marker or marker-first reconciliation. |
| `deletePolicy` | Must be `already_in_db_exact_key` unless a later approved policy gate says otherwise. |
| `noUndoAcknowledgement` | Explicit acknowledgement that the app has no undo. |
| `deleteDbBeforeImagePreparationReadiness` | Must be `true` before mutation: target-side storage/schema/column policy/capacity/confidentiality/retention are implemented, tested, and bound. It does not claim that a before-image already exists. |
| `rollbackReadiness` | Must be `false_pending_atomic_before_image` before mutation and may transition to `true` only inside the authoritative transaction after the complete before-image is inserted and revalidated, immediately before DELETE. A CSV/source snapshot never satisfies this field. |
| `rollbackLimitationAcknowledgement` | Explicit acknowledgement that exact recovery requires a separately approved restore of the retained DB before-image before its deadline/final disposition; source CSV, metadata, matching keys, or transformed values cannot recreate or replace the pre-delete DB row image. |
| `v2RowAttributionEnabled` | Explicit approved gate state, normally `false` unless separately approved. |
| `v2DbDeltaEvidenceRequired` | Explicit approved gate state. |
| `rowAttributionHmacAvailabilityClass` | Safe class such as `configured`, `not_configured`, or `not_applicable`; never the HMAC value. |
| `featureGateChangeApproved` | Must be `false` unless a separate approval explicitly changes gate state. |
| `approver` | Named human approver or approved role id. |
| `executor` | Named executor or approved role id. |
| `stopCondition` | Concrete condition that stops before mutation or after uncertain outcome. |
| `evidenceReportLocation` | Safe path or link where post-run evidence will be recorded. |
| `approvalExclusions` | Explicit list of actions not approved by this record. |

The immutable approval payload records the expected pre-mutation
`rollbackReadiness=false_pending_atomic_before_image`. The later `true` value is
not an edit to that approval: it is an authenticated target-transaction outcome
transition bound to the same approval/run/mutation/before-image and is valid only
if the atomic commit succeeds.

## Required Approval Wording

The field table and approval wording are both mandatory. The wording alone is
not a valid approval if any required field above is missing from the stored
approval record.

The approval must use this shape, with every placeholder filled from current
read-only evidence and delete preflight output:

```text
TEMPLATE STATUS: NOT AUTHORIZATION. Do not fill, sign, or execute this block until production code and deterministic tests implement every prerequisite for this action and a new human approval explicitly releases this gate.
I approve exactly one operational hard delete for approval <approvalId>, initially in state available and claimable only until <deleteExecuteByUtc>.
The approved package sourceCommit is <packageSourceCommit>, package label is <packageLabel>, and zip SHA-256 is <zipSha256>.
The approved DB target class is <dbTargetClass> and diagnostic DB fingerprint hash is <dbFingerprintHash>. The expected exact target is anchored by pre-existing baseline <trustedTargetBaselineId> in verified/non-revoked state <trustedTargetBaselineState>, privacy-safe alias <trustedTargetAlias>, and safe evidence <trustedTargetBaselineEvidenceId>. The exact target comes from consumed preparation approval <targetIdentityPreparationApprovalId>, completed by <targetIdentityPreparationExecuteByUtc>, and is protected binding <targetDbBindingId> in state <targetDbBindingState>, valid only until <targetDbBindingValidUntilUtc>, with safe evidence <targetDbBindingEvidenceId>. The singleton exact-target coordinator is <targetGlobalCoordinatorId>, state/sole owner/consumer/generation/evidence <targetGlobalCoordinatorState>/<targetGlobalCoordinatorOwnerFenceId>/<targetGlobalCoordinatorConsumer>/<targetGlobalCoordinatorGeneration>/<targetGlobalCoordinatorEvidenceId>; it must reject every different Preview-chain owner. The shared target operation fence is <targetOperationFenceId>, with exact chain/upload/Delete states <targetOperationFenceState>/<targetUploadBranchState>/<targetDeleteBranchState>, consumer <targetOperationConsumer>, generation <targetOperationFenceGeneration>, and safe evidence <targetOperationFenceEvidenceId>; it must be the same fence already claimed by the named preflight result and both coordinator/fence generations must be atomically claimed for this delete run. Any same-run reconcile must complete by <deleteReconcileByUtc>, no later than that validity. The schema class is <schemaClass> and protected schema binding is <schemaBindingId>.
The approved scope is preview run <previewRunId>, delete-preflight approval <deletePreflightApprovalId> consumed by <deletePreflightExecuteByUtc> and completed by <deletePreflightCompleteByUtc> under owner <deletePreflightClaimId>/fence <deletePreflightFence>, unexpired ready_available delete preflight result <deletePreflightId>, selected already_in_db items <selectedAlreadyInDbItems>, and exact keys <exactKeyCount>.
That preflight result may be atomically claimed and consumed only by this approval <approvalId> and the exactly one deleteRunId generated in the joint claim transaction; it may not be reused by another approval or run.
The random unique target delete mutation id <deleteMutationId> and DB before-image id <deleteDbBeforeImageId> are pre-reserved in this immutable approval and may be claimed only with this approval, preflight result, run, exact keyset/source-provenance binding, exact target, schema/column bindings, mutation-schema fence <deleteDbMutationSchemaFenceBindingId>, mutation-side-effect binding <deleteDbMutationSideEffectBindingId> in readiness <deleteDbMutationSideEffectReadiness=direct_rows_only_no_unmodeled_or_nonrestorable_effects> for both DELETE and exact restore INSERT, and both coordinator/fence generations. Before any delete, create exactly one target-side prepared marker with those bindings. In one authoritative target transaction, first acquire and hold the bound engine-appropriate DDL-conflicting relation/catalog locks or enforced schema-generation fence through commit; only then revalidate the schema/side-effect bindings and exact selected-row locks. Prove every DELETE/INSERT foreign-key/cascade, trigger/rule, RLS/policy, generated/default, sequence, replication/publication/CDC, notification, and affected-relation class is absent or inert so only the selected direct rows can change, capture every column's complete typed pre-delete value into the protected before-image under content/schema/column bindings <deleteDbBeforeImageContentBindingId>/<deleteDbBeforeImageSchemaBindingId>/<deleteDbBeforeImageColumnSetBindingId>, enforce exact row count <deleteDbBeforeImageRowCount=exactKeyCount> and byte ceiling <deleteDbBeforeImageMaxBytes>, transition rollbackReadiness from false_pending_atomic_before_image to true, execute the exact-key DELETE, and transition the marker to committed. Any unfenced DDL/configuration window, secondary relation or externally observable effect, missing row/column, schema or side-effect drift, unsupported restore semantics, overflow, capacity/confidentiality failure, binding mismatch, or concurrent value change rolls back the entire transaction and performs zero DELETE. Mark aborted only after non-commit is authoritative. Response loss/timeout becomes commit_unknown_blocked unless marker-first reconciliation proves the same committed marker and recovery_available before-image; current row presence/delta must never infer the outcome.
The approved delete policy is <deletePolicy>.
The approved protected selection binding is <selectionBindingId>, keyset binding is <keysetBindingId>, source evidence binding is <sourceEvidenceBindingId>, and source file signature-set binding is <sourceFileSignatureSetBindingId>.
The legacy-named source-provenance snapshot is <deleteRecoverySnapshotId>, protected source content binding <deleteRecoveryContentBindingId>, state <deleteRecoverySnapshotState>, observed bytes <deleteRecoveryObservedBytes>, approved byte ceiling <deleteRecoverySnapshotMaxBytes>, capacity evidence <deleteRecoveryCapacityEvidenceId>, owner-only confidentiality class <deleteRecoveryConfidentialityClass>, retention deadline <deleteRecoverySnapshotRetainUntilUtc>, disposition state <deleteRecoveryDispositionState>, final recovery disposition <deleteRecoveryFinalDispositionDecision or not_decided>, early-disposition approval <deleteRecoveryDispositionApprovalId=not_issued>/<deleteRecoveryDispositionApprovalState=not_issued>/<deleteRecoveryDispositionExecuteByUtc=not_approved>, and safe disposition evidence <deleteRecoveryDispositionEvidenceId or not_triggered>. It was created and privately content-verified before the preflight DB read under the named preflight approval, is distinct from every upload snapshot, and Delete/reconcile may not reopen the operational source. It proves source/key provenance only and is not an exact DB rollback image.
The exact DB before-image is pre-reserved as <deleteDbBeforeImageId>, initially <deleteDbBeforeImageState=not_created>, with protected content/schema/column bindings <deleteDbBeforeImageContentBindingId>/<deleteDbBeforeImageSchemaBindingId>/<deleteDbBeforeImageColumnSetBindingId>, mutation-schema fence <deleteDbMutationSchemaFenceBindingId>, mutation-side-effect binding/readiness <deleteDbMutationSideEffectBindingId>/<deleteDbMutationSideEffectReadiness=direct_rows_only_no_unmodeled_or_nonrestorable_effects>, expected row count <deleteDbBeforeImageRowCount=exactKeyCount>, observed bytes initially <deleteDbBeforeImageObservedBytes=not_observed>, approved byte ceiling <deleteDbBeforeImageMaxBytes>, capacity evidence <deleteDbBeforeImageCapacityEvidenceId>, owner-only confidentiality class <deleteDbBeforeImageConfidentialityClass>, retention deadline <deleteDbBeforeImageRetainUntilUtc=deleteRecoverySnapshotRetainUntilUtc>, disposition evidence <deleteDbBeforeImageDispositionEvidenceId or not_triggered>, and restore lifecycle <deleteDbRestoreApprovalId=not_issued>/<deleteDbRestoreApprovalState=not_issued>/<deleteDbRestoreExecuteByUtc=not_approved>/<deleteDbRestoreActiveUseExpiresAtUtc=not_approved>/<deleteDbRestoreReconcileByUtc=not_approved>/<deleteDbRestoreDispositionMarginSeconds=not_approved>/<deleteDbRestoreMutationId=not_created>/<deleteDbRestoreOutcomeState=not_created>/<deleteDbRestoreOutcomeEvidenceId=not_created>. The target transaction must capture complete typed values for every column before DELETE, prove both DELETE and exact restore INSERT are limited to the selected direct rows with no secondary or externally observable effect while the bound DDL/schema fence is held, record exact observed bytes within the approved ceiling, and commit that before-image atomically with the DELETE and marker. Before mutation, <deleteDbBeforeImagePreparationReadiness=true> and <rollbackReadiness=false_pending_atomic_before_image>; rollbackReadiness may become true only inside that transaction after exact capture/revalidation succeeds. A committed marker without the exact recovery_available before-image is a permanent blocker, never success evidence.
I understand this delete has no app-level undo and exact recovery requires a separately approved restore transaction from that exact retained DB before-image while it remains valid; a source CSV snapshot, current source file, metadata signature, matching-key reparse, or re-transform cannot replace it. After a committed Delete, the source-provenance snapshot is awaiting_recovery_disposition, the DB before-image remains recovery_available, and both share the exact same retention deadline while coordinator/fence remain recovery_disposition_pending. A separate immutable single-use disposition approval may atomically authorize early accept_delete_and_dispose for both, a separately scoped restore approval may authorize exact before-image restore_then_dispose, or expiry cleanup may run only under both the source preflight approval and hard-delete approval that independently authorize their respective record. After an authoritative aborted Delete, the DB before-image remains not_created, restore is forbidden, and only the source-provenance snapshot enters awaiting_recovery_disposition; source-only early or expiry disposition may close the chain. All unrelated or new mutations are blocked while the applicable decision or cleanup is unresolved; only the separately approved exact recovery action bound to the marker/coordinator and the records that actually exist may run before disposition.
The approved V2 gate states are v2RowAttributionEnabled=<v2RowAttributionEnabled>, v2DbDeltaEvidenceRequired=<v2DbDeltaEvidenceRequired>, rowAttributionHmacAvailabilityClass=<rowAttributionHmacAvailabilityClass>, and featureGateChangeApproved=<featureGateChangeApproved>.
The named approver is <approver>, the named executor is <executor>, and the stop condition is <stopCondition>.
The post-run evidence report will be recorded at <evidenceReportLocation>.
This approval excludes <approvalExclusions>.
This approval does not approve Upload Preview, Start Upload, Retry Failed, Settings save, feature gate enablement, Supabase reset/cleanup, Docker cleanup, LAN, deploy, arbitrary SQL delete, broad cleanup, or any delete outside the exact scope above.
```

## Pre-Mutation Checklist

Before mutation, the executor must prove all of these:

- delete-preflight approval is terminal `consumed`, names the same package/
  Preview/DB/source/selection scope, and produced exactly this
  `deletePreflightId` before its deadline;
- delete-preflight result is unexpired `ready_available`, has no existing
  `consumedByDeleteApprovalId` or `deleteRunId`, and can be claimed only in the
  same transaction that claims this hard-delete approval and creates one run;
- the same target operation fence generation is owned by that preflight result
  in Delete branch `delete_ready`, has no Start/Retry owner, is not terminal/
  stale, and can be atomically claimed only with this approval/result/run;
- hard-delete approval is protected, unexpired, and `available` for the atomic
  one-run claim required by `docs/164`;
- one random `deleteMutationId` is pre-reserved in that immutable approval; its
  target marker does not already exist under different bindings, and approval/
  result/run creation claims it exactly once;
- one random `deleteDbBeforeImageId` is pre-reserved in the same immutable
  approval, and protected target-side storage/schema/complete-column-set/capacity/
  confidentiality/retention bindings are implemented, tested, and ready before
  mutation; the before-image record itself does not yet exist;
- `deleteDbMutationSideEffectBindingId` resolves to an authenticated complete
  inspection of DELETE and exact restore INSERT foreign keys/cascades, triggers/
  rules, RLS/policies, generated/default expressions, sequences, replication/
  publication/CDC hooks, transactional notifications, and every affected
  relation, with readiness
  `direct_rows_only_no_unmodeled_or_nonrestorable_effects`; any secondary,
  external, non-transactional, or merely modeled affected-graph effect blocks
  both actions with zero writes;
- `deleteDbMutationSchemaFenceBindingId` resolves to the complete relation/catalog
  lock set or enforced monotonic schema generation, and the engine can acquire it
  before inspection and hold it through both DELETE and restore INSERT commit;
- source-provenance and DB-before-image retention deadlines are exactly equal,
  and the target binding remains valid through that shared deadline;
- approval record exists in an approved storage location;
- package metadata and checksum match the approval record;
- current local branch and operator package source commit match the approved
  source commit expectation for the run;
- Preview is fresh, latest, succeeded, and DB-reachable;
- selected Preview items are still `already_in_db`;
- delete preflight is ready and unexpired;
- selected item count and exact key count match, and every opaque selection,
  keyset, source-evidence, and source-file-signature-set binding resolves to the
  same authenticated owner-only protected record named by the approval;
- the preflight-bound source-provenance snapshot, not current source, carries the same
  protected file-boundary/content/keyset evidence behind
  `sourceFileSignatureSetBindingId` and `deleteRecoveryContentBindingId`; after
  snapshot publication there is no source existence/signature/reparse check;
- the preflight approval atomically created and claimed exactly one owner-only
  encrypted immutable `deleteRecoverySnapshotId` before its DB read; its private
  exact-byte/content binding, approved ceiling, retention, and disposition fields
  match the preflight result and approval, it is `preflight_bound`, and neither
  preflight nor Delete/reconcile reopens the operational source;
- every selected source entry is canonical-root-contained with no symlink,
  junction, reparse-point, or hard-link ambiguity at any component; one stable
  opened-handle identity is held while the same bytes are copied, privately
  digested, and parsed, and any root escape/link swap/identity change disposes
  partial bytes and blocks before DB read;
- the preflight claim owner/fence and completion deadline match every snapshot/
  DB-read/result publication CAS; no restart, expiry, invalidation, stale worker,
  or response-loss replay can publish a new/late result or perform a second read;
- `deleteDbBeforeImagePreparationReadiness=true`, while
  `rollbackReadiness=false_pending_atomic_before_image` before mutation; only the
  authoritative transaction may set it true after complete typed before-image
  capture and revalidation, and the rollback limitation is explicitly
  acknowledged in the approval record;
- local token protection is active for protected writes;
- audit logs are readable and append-only behavior is intact;
- DB target guard's safe class/diagnostic hash still match; the same verified,
  non-revoked trusted target baseline id/alias/state/evidence, consumed target-
  identity preparation approval, and exact binding id/state/validity/evidence all
  match; `deleteExecuteByUtc` and `deleteReconcileByUtc` do not exceed that
  validity; the opaque DB binding resolves unexpired to the same authenticated
  exact instance/database identity and is revalidated with the authoritative DB
  clock immediately before mutation; and the public schema class plus
  opaque schema binding resolve to the same authenticated owner-only
  verification record;
- the protected mutation-side-effect binding/readiness still matches the
  approval and authoritative transaction schema; no newly installed or changed
  trigger, rule, cascade, affected relation, replication/CDC hook, sequence
  effect, or non-transactional notification exists;
- DELETE privilege preflight is ready;
- no active Preview, Upload, Delete, Settings, Runtime, `commit_unknown`, or
  `reconciliation_failed` blocker exists;
- row attribution and DB delta gate state matches the approval record;
- `featureGateChangeApproved=false` unless a separate approval explicitly
  authorizes a gate state change.

Every approval must name the V2 gate states, HMAC availability class, and
post-run preservation requirements. Enabling those gates is not implied by this
document.

## Post-Run Evidence Report

After the run, the evidence report must record safe evidence only:

- approval id and approval record location;
- package source commit, package label, and checksum status;
- preview run id;
- delete preflight id;
- delete preflight result terminal state and its permanent
  `consumedByDeleteApprovalId`/`deleteRunId` binding;
- delete run id;
- delete policy;
- selected item count;
- exact key count;
- deleted row count;
- DB target class and diagnostic fingerprint hash;
- trusted target baseline id/alias/state/evidence, target-identity preparation
  approval id/state/deadline, and protected exact DB binding id/state/validity/
  evidence plus delete reconcile deadline;
- target operation fence id/chain state/upload branch/Delete branch/consumer/
  generation/evidence;
- public schema class;
- protected schema binding id;
- protected selection binding id;
- protected keyset binding id;
- protected source-evidence binding id;
- protected source-file-signature-set binding id;
- protected source-provenance snapshot/content-binding ids, state, observed/
  maximum bytes, capacity/confidentiality evidence, retention deadline, final
  recovery disposition approval id/state/deadline or separately scoped restore
  approval, disposition state, and safe disposition evidence id;
- protected DB before-image id/content/schema/column-set binding ids, exact row
  count, observed/approved-maximum bytes, capacity/confidentiality evidence, retention,
  lifecycle state, rollback-readiness transition, restore approval/mutation/
  outcome evidence, active-use/reconcile deadlines, disposition margin when
  applicable, and safe disposition evidence;
- protected mutation-schema fence plus DELETE/restore-INSERT side-effect binding/
  readiness and both authoritative-transaction lock/revalidation evidence classes;
- V2 gate states and HMAC availability class;
- feature gate change approved value;
- `upload.delete_start` audit id;
- final `upload.delete_succeeded`, `upload.delete_failed`,
  `upload.delete_blocked`, or `upload.delete_reconciled` audit id;
- DB delta id and expected/actual delta when the gate is explicitly approved and
  on;
- row attribution evidence count when the gate is explicitly approved and on;
- whether reconcile is required;
- final recovery state;
- delete mutation id/outcome/evidence id from target-marker-first proof;
- stop condition result;
- rollback or fix-forward decision.

Forbidden report content:

- raw operational source paths;
- filenames;
- CSV row content or DB before-image row values;
- raw `(timestamp, device_id)` keys;
- raw SQL;
- DB URLs;
- tokens, Authorization values, JWTs, credentials, or secrets;
- raw internal URLs;
- deterministic selection/keyset/source/signature digests or private keyed
  HMAC values.

## Reconcile And Failure Handling

If the delete returns `commit_unknown`, `db_delta_mismatch`,
`evidence_write_failed`, or `reconciliation_failed`, stop destructive work.

Allowed follow-up without a new destructive approval:

- read-only investigation of safe state;
- the approved reconcile endpoint for the same delete run, only before
  `deleteReconcileByUtc` and `targetDbBindingValidUntilUtc` after revalidating the
  same exact target identity/state/evidence on its authoritative DB session; it
  must lock/read the immutable target marker first and may never infer commit or
  rollback from current row presence, counts, or delta;
- preserving audit, DB delta, and row attribution evidence;
- documenting the failure and next stop condition.

The target-global coordinator, chain fence, source-provenance snapshot, and any
committed DB before-image remain owned/retained while the marker is nonterminal
or `commit_unknown_blocked`. After a committed outcome, the source snapshot is
`awaiting_recovery_disposition`, the DB before-image remains
`recovery_available`, and coordinator/fence remain non-advanceable
`recovery_disposition_pending` until both records are terminal. After an
authoritative aborted outcome, the DB before-image remains `not_created`, restore
is forbidden, only the source snapshot becomes `awaiting_recovery_disposition`,
and coordinator/fence remain `recovery_disposition_pending` until that one record
is terminal. No implementation may fabricate or require a DB before-image for an
aborted transaction. A committed marker is accepted only with the same
`recovery_available` before-image bindings; a missing, incomplete, or substituted
before-image is a permanent blocker.
Reinserted or re-deleted rows after the original transaction do not change its
marker-proven outcome. A missing, tampered, substituted, or still-`prepared`
marker at the reconcile deadline leaves the chain blocked; it does not authorize
another Delete, a restore, or disposal before the approved retention boundary.

Early `accept_delete_and_dispose` requires an immutable/authenticated
`deleteRecoveryDispositionApprovalId` in `available`, bound to the authoritative
marker outcome, coordinator/fence generation, human decision, deadline, and the
exact set of recovery records that exists. For a committed Delete it binds and
atomically claims both the source-provenance snapshot and exact DB before-image
with content/schema/column/side-effect bindings. For an aborted Delete it binds
and claims only the source-provenance snapshot while proving the pre-reserved DB
before-image remains `not_created`; restore and DB-before-image disposal are not
applicable. Cleanup performs key-first verified byte removal for every claimed
record and publishes exactly one safe evidence record; response loss returns the
same record. It must CAS the same target-global/chain owner and
`recovery_disposition_pending` generations to terminal only after every record
that exists is verified terminal. Missing/substituted/expired/replayed/concurrent
approval or outcome drift must not destroy any key/bytes.

Automatic retention-expiry authority is split by record and may never be
inherited across approvals. The original consumed preflight approval authorizes
expiry disposal only of its source-provenance snapshot. The consumed hard-delete
approval separately authorizes expiry disposal only of the DB before-image it
pre-reserved and created, with exact id/content/schema/column/side-effect/marker/
target/coordinator bindings. A committed Delete uses one CAS-bound dual-record
expiry close under both approvals at their required equal deadline; an aborted
Delete uses source-only expiry under the preflight approval. Each path fences an
early-disposition or restore claimant, and coordinator release waits for the
terminal join of all records that actually exist.
A restore requires its own separately scoped mutation approval, uses only the
exact DB before-image, restores and verifies every typed column under the bound
schema/column policy in one transaction, and is not authorized by this document.
Deterministic cleanup tests must crash/restart before and after approval claim,
key destruction, byte removal, absence verification, coordinator/fence terminal
CAS, and evidence publication. Recovery returns/publishes only the same terminal
result; it never restores a destroyed key, repeats a different cleanup, releases
the coordinator before verified removal, or loses the safe evidence record.
Restore tests must reject missing/substituted/expired/replayed/concurrently
claimed restore approvals and mutations; target/before-image/schema/column/side-
effect/generation substitution; any already-present key; and current source
access. They must install or drift every INSERT-specific trigger/rule/policy,
default/sequence/generated behavior, replication/CDC/notification, and affected-
relation class and prove zero restore writes unless the same binding proves direct-
rows-only inert behavior. They must deterministically race trigger/rule/FK/
publication installation before fence acquisition, after inspection, and before
commit for both DELETE and restore INSERT; only the lock/fenced winner may proceed,
and the losing mutation performs zero writes/effects. They must exercise just-before/at/after
`deleteDbRestoreActiveUseExpiresAtUtc`, `deleteDbRestoreReconcileByUtc`,
`targetDbBindingValidUntilUtc`, and `deleteDbBeforeImageRetainUntilUtc` at restore
approval claim, prepared-marker creation, authoritative transaction commit,
marker-first reconciliation, exact-equality publication, and disposition claim,
using the authoritative target clock for every target access. Starting or
committing a transaction at/after active-use expiry produces zero restore writes.
After active-use expiry but before reconcile deadline, marker-first reconcile may
prove an already committed marker and publish only the same local/evidence result;
it may issue no restore write. Deadline failure fences stale claimants, preserves
retained records/evidence, and never releases or retries the coordinator while
restore is active or `commit_unknown_blocked`. Tests must crash/restart before/after approval claim,
prepared restore marker, typed inserts, equality verification, marker commit,
response loss, and evidence/disposition publication, proving all-or-nothing no-
overwrite restore and only one recoverable outcome. Cleanup tests must cover
committed dual-record and aborted source-only early/expiry disposition, equal-
deadline enforcement, mismatch rejection, crash/response loss, replay,
early-versus-expiry races, cleanup failure, and proof that an aborted path neither
fabricates nor requires a DB before-image.

Required early-disposition approval wording, issued only after human review of a
terminal marker-proven Delete outcome:

```text
TEMPLATE STATUS: NOT AUTHORIZATION. Do not fill, sign, or execute this block until production code and deterministic tests implement every prerequisite for this action and a new human approval explicitly releases this gate.
The Delete recovery disposition approval id is <deleteRecoveryDispositionApprovalId>, initially available and claimable only by <deleteRecoveryDispositionExecuteByUtc>, no later than the minimum retention deadline of every recovery record that exists.
I approve exactly one early accept_delete_and_dispose action for source-provenance snapshot <deleteRecoverySnapshotId>/<deleteRecoveryContentBindingId>, retained only until <deleteRecoverySnapshotRetainUntilUtc>, from Delete mutation <deleteMutationId> in authoritative terminal outcome <deleteMutationOutcomeState> with evidence <deleteMutationOutcomeEvidenceId>. If that outcome is committed, this approval also binds exact DB before-image <deleteDbBeforeImageId>/<deleteDbBeforeImageContentBindingId>/<deleteDbBeforeImageSchemaBindingId>/<deleteDbBeforeImageColumnSetBindingId>/<deleteDbMutationSideEffectBindingId>, state recovery_available, retained until the same exact deadline <deleteDbBeforeImageRetainUntilUtc=deleteRecoverySnapshotRetainUntilUtc>. If that outcome is aborted, it instead requires <deleteDbBeforeImageState=not_created>, authorizes source-only disposition, and does not authorize restore or any DB-before-image disposition.
It binds exact-target coordinator/fence <targetGlobalCoordinatorId>/<targetOperationFenceId>, exact owner/consumer/generations/evidence <targetGlobalCoordinatorOwnerFenceId>/<targetGlobalCoordinatorConsumer>/<targetGlobalCoordinatorGeneration>/<targetGlobalCoordinatorEvidenceId>/<targetOperationFenceGeneration>/<targetOperationFenceEvidenceId>, named approver <approver>, and named executor <executor>.
The cleanup action must atomically claim this approval and the exact applicable record set, destroy each per-record key first, remove and verify absence of all bytes, publish exactly one <deleteRecoveryDispositionEvidenceId> and, only for a committed Delete, <deleteDbBeforeImageDispositionEvidenceId>, then finish consumed. Response loss returns only that same evidence; mismatch/expiry/concurrent/replay claim performs no early disposition and finishes invalid only if cleanup did not commit.
This approval authorizes only the protected recovery-record state transitions, key destruction, byte removal, verification, and safe disposition-evidence write above. It does not authorize restore, Preview, Start Upload, Retry Failed, Delete, unrelated operational-table DB read/write, source access/mutation, Settings save, runtime lifecycle, reset, cleanup outside these exact records, LAN, or deployment.
```

Required separately scoped restore approval wording, issued only after human
review of a committed Delete marker and its exact `recovery_available` before-
image:

```text
TEMPLATE STATUS: NOT AUTHORIZATION. Do not fill, sign, or execute this block until production code and deterministic tests implement every prerequisite for this action and a new human approval explicitly releases this gate.
The DB before-image restore approval id is <deleteDbRestoreApprovalId>, initially available and claimable exactly once by <deleteDbRestoreExecuteByUtc>; the pre-reserved restore mutation id is <deleteDbRestoreMutationId>. Its unrenewable active-use commit deadline is <deleteDbRestoreActiveUseExpiresAtUtc>, marker-first read-only reconcile/equality deadline is <deleteDbRestoreReconcileByUtc>, and protected disposition margin is <deleteDbRestoreDispositionMarginSeconds>. The ordering must be deleteDbRestoreExecuteByUtc <= deleteDbRestoreActiveUseExpiresAtUtc < deleteDbRestoreReconcileByUtc <= min(targetDbBindingValidUntilUtc, deleteDbBeforeImageRetainUntilUtc) minus that positive margin.
I approve exactly one restore_then_dispose transaction for Delete mutation <deleteMutationId> with committed evidence <deleteMutationOutcomeEvidenceId>, exact DB before-image <deleteDbBeforeImageId>/<deleteDbBeforeImageContentBindingId>/<deleteDbBeforeImageSchemaBindingId>/<deleteDbBeforeImageColumnSetBindingId>, row count <deleteDbBeforeImageRowCount>, retention <deleteDbBeforeImageRetainUntilUtc>, and original source-provenance snapshot <deleteRecoverySnapshotId>/<deleteRecoveryContentBindingId>.
It binds the same verified baseline <trustedTargetBaselineId>/<trustedTargetBaselineEvidenceId>, exact target <targetDbBindingId> valid until <targetDbBindingValidUntilUtc>, mutation-schema fence <deleteDbMutationSchemaFenceBindingId> and side-effect binding/readiness <deleteDbMutationSideEffectBindingId>/<deleteDbMutationSideEffectReadiness=direct_rows_only_no_unmodeled_or_nonrestorable_effects> for both DELETE and INSERT, target-global coordinator/fence <targetGlobalCoordinatorId>/<targetOperationFenceId> in recovery_disposition_pending with exact owner/consumers/generations/evidence, named approver <approver>, named executor <executor>, and restore evidence location <evidenceReportLocation>.
Before approval claim, prepared-marker creation, authoritative restore transaction, marker-first reconciliation, equality publication, and disposition claim, revalidate the applicable lease/deadline with the authoritative target clock. After the local approval/image/consumer claim and before any INSERT, a separate authoritative target transaction must durably create exactly one `prepared` restore marker under <deleteDbRestoreMutationId>, binding the approval/image/schema-fence/side-effect/target/coordinator/lease fields. It CAS-checks the same owner/generations and current time before <deleteDbRestoreActiveUseExpiresAtUtc>; duplicate or response-lost creation returns only that marker. The later authoritative restore transaction must lock this already committed `prepared` marker, then acquire and hold the exact engine-appropriate DDL-conflicting relation/catalog locks or enforced schema-generation fence through commit. Only then may it revalidate schema/INSERT-side-effect bindings, lock the exact keyset, require every selected target key still absent, and prove all INSERT side-effect classes remain absent/inert. It inserts every typed column from the protected before-image without overwrite, verifies exact row/column equality, and commits inserts plus marker transition `prepared -> committed` atomically only while current target time is strictly before <deleteDbRestoreActiveUseExpiresAtUtc>. Crossing that deadline rolls back every restore write and leaves the durable marker `prepared` for guarded abort/reconcile. Any unfenced DDL/configuration window, present key, schema/column/side-effect mismatch, secondary/external effect, missing/tampered/expired before-image, identity drift, overflow, concurrent writer, or verification failure also rolls back every restore write. Timeout or response loss becomes commit_unknown_blocked; after active-use expiry, marker-first read-only reconciliation may resolve an already committed marker only by <deleteDbRestoreReconcileByUtc> and may issue no restore write. Current row presence cannot infer outcome.
Only after committed restore and exact equality evidence may the same owner/generation enter key-first verified disposition for both retained records and publish <deleteDbRestoreOutcomeEvidenceId>, <deleteDbBeforeImageDispositionEvidenceId>, and <deleteRecoveryDispositionEvidenceId>. Disposal failure keeps the coordinator blocked. This approval does not authorize a new Delete, overwrite/upsert, Preview, Start Upload, Retry Failed, source access/mutation, Settings save, runtime lifecycle, reset, unrelated cleanup, LAN, or deployment.
```

The restore lifecycle is exact and non-replayable:

| Restore stage | Approval state | Before-image state | Outcome / coordinator consumers | Required result |
| --- | --- | --- | --- | --- |
| Approval not claimed by `deleteDbRestoreExecuteByUtc` | `invalid` | `recovery_available` | outcome `not_created`; consumers remain `delete` | Zero restore writes. A new separately reviewed approval may be issued only inside the remaining active-use/retention window. |
| Atomic claim succeeds | `claimed` | `restoring` | outcome `not_created`; both consumers become `delete_restore` under the same owner/generations | Exactly one approval/mutation/lease binding. Concurrent or replay claims fail without changing the image. Only the same owner may create or recover the target marker before the lease. |
| Durable prepared-marker transaction commits | `claimed` | `restoring` | outcome `prepared`; consumers remain `delete_restore` | A separate target transaction commits the exact bound marker before any INSERT. Response loss returns only that same marker. |
| Authoritative restore transaction commits | `consumed` | `restored` | outcome `committed`; consumers remain `delete_restore` until equality and disposition | Exact inserts, equality proof, and marker transition commit atomically before active-use expiry. |
| Response is lost or commit is not yet authoritative | `claimed` | `restoring` | outcome `commit_unknown_blocked`; consumers remain `delete_restore` | No retry, new approval, cleanup, or coordinator release. Marker-first read-only reconcile only by `deleteDbRestoreReconcileByUtc`. |
| Marker-first reconcile proves committed | `consumed` | `restored` | same committed outcome; consumers remain `delete_restore` until equality/disposition | Publish only the same outcome/equality evidence; never repeat INSERT. |
| Guarded recovery proves no marker was created, or locks `prepared` after active-use expiry with no committed INSERT transaction | `consumed` | `recovery_available` | outcome `aborted`; target marker is durably `aborted`; both consumers return to `delete` recovery hold under atomically advanced generations | Recovery first commits/CASes the pre-reserved target marker to `aborted`, fencing delayed creation/commit, then publishes local abort. The intact before-image is retry-eligible only through a new human approval within remaining deadlines. No old approval or mutation may reopen. |
| Reconcile deadline expires without authoritative terminal marker | `consumed` | `restoring` | outcome `commit_unknown_blocked`; consumers remain `delete_restore` | Permanent non-advanceable block pending separately authorized investigation; no restore/disposal/new mutation. |
| Equality verified and applicable disposal commits | `consumed` | `restored -> disposed` | outcome `committed`; consumers `delete_restore -> delete_disposition -> empty`, coordinator/fence terminal | Key-first verified disposal and safe evidence close every retained record exactly once. |

Deterministic tests must cover every row above, including crash/restart and
response loss after local claim but before marker creation, before/after durable
`prepared` commit, before/after marker lock, INSERT/equality/`prepared -> committed`
commit, consumer-generation, and disposition publication. They must race delayed
prepared creation/restore against guarded `aborted` marker creation and prove only
one terminal marker wins. Authoritative abort must restore only the intact before-
image lifecycle state, consume the attempted approval permanently, and require a
fresh approval without reopening the operational source.

Not allowed as rollback:

- broad manual DB delete;
- truncate;
- reset;
- Supabase cleanup;
- Docker cleanup;
- deleting audit, DB delta, row attribution, or delete run evidence.

## V2 Completion Interpretation

An operational delete can count as V2 operational delete verification only when:

- the mandatory protected single-use runtime lifecycle above is implemented,
  deterministically tested, and proven for the exact `approvalId`,
  `deletePreflightId`, preflight owner/fence/completion deadline, preflight-result
  consumer binding, and `deleteRunId`;
- it uses the exact approval record above;
- it stays inside the current selected `already_in_db` exact-key contract, or a
  later approved delete-expansion policy;
- it records the required post-run evidence report;
- public/audit/committed records contain only opaque random binding ids and safe
  counts/classes while exact material and versioned domain-separated keyed HMAC
  integrity data remain owner-only; dictionary/candidate attacks, domain/key-
  version substitution, rotation, tamper, replay, and equal-count substitution
  are deterministically tested; the protected exact target DB binding is carried
  through preflight approval/result, delete approval/run, and reconcile together
  with its trusted baseline id/alias/state/evidence, preparation approval/state/
  deadline, and binding state/validity/evidence,
  with every DB read/write before the binding/reconcile deadline and
  missing/revoked/rotated baseline, wrong same-port DB present at first
  observation, later same-loopback/same-port cluster/database replacement, and
  binding substitution tests plus just-before/at/after-expiry races;
  baseline/evidence ids and alias must also resist candidate enumeration and
  redact exact target/private keyed-integrity material;
- the shared operation fence proves independently eligible upload/Delete
  branches, zero-target-with-eligible-delete behavior without disposed upload-
  snapshot reuse, Start-vs-Delete and Retry-vs-Delete contention, terminal replay
  rejection, and crash/response-loss recovery of only one consumer;
- the singleton target-global coordinator serializes all Preview chains for the
  exact target and every action/marker/reconcile CAS-checks its owner, consumer,
  generation, and evidence without overlap or stale publication;
- one protected exact-byte Delete source-provenance snapshot is privately
  verified and retained from before preflight DB read through marker-
  resolved Delete and the bounded human recovery decision, never reuses the
  upload snapshot or reopens source, and completes key-first disposal with safe
  evidence; it is never treated as the DB rollback image;
- the authoritative Delete transaction captures a complete typed DB before-image
  for every selected row/column under exact schema/column bindings, verifies row
  count and approved byte ceiling, and commits before-image + exact DELETE +
  marker transition atomically; different DB values with identical source keys,
  null/default/generated/system-column handling, schema/value drift, capacity/
  overflow, crash at every transaction boundary, response loss, tamper/
  substitution, exact restore verification, and dual-record disposition races
  are deterministically tested;
- the protected mutation-side-effect binding proves both exact DELETE and restore
  INSERT are direct selected-row-only operations with no secondary affected
  relation or externally observable effect; deterministic tests concurrently
  install or drift
  DELETE- and INSERT-specific foreign-key cascades, triggers, rules, RLS/policies,
  generated/default expressions, sequences, replication/publication/CDC hooks,
  and notifications and prove zero writes unless every class is absent or inert;
- committed and aborted outcomes have distinct recovery closes, source and DB
  before-image retention deadlines are equal when both records exist, preflight
  and hard-delete approvals independently authorize only their own expiry
  disposal, and coordinator release occurs only after the terminal join of all
  records that actually exist;
- restore claim/commit/authoritative-abort/commit-unknown/reconcile transitions
  follow the exact approval, before-image, outcome, consumer, and generation table;
  an aborted attempt consumes its approval and requires a new approval, while an
  unresolved marker can never regress from `restoring` or release the coordinator;
- the immutable approval pre-reserves one `deleteMutationId`; its bound prepared
  target marker and exact DELETE commit atomically, reconciliation reads marker
  first, external reinsert/re-delete cannot alter the proven outcome, and missing/
  tampered/nonterminal marker state remains blocked;
- any gate-on DB delta and row attribution evidence is preserved;
- any uncertain outcome is reconciled or explicitly left blocked with evidence;
- `$review` has no unresolved safety finding for the evidence and rollback
  report.

If a run uses only the current v1 delete contract, including its source-derived
rollback boolean, it proves neither operational rollback safety nor V2 Delete
verification and must not be executed against operational data.

## Rollback

Document-only rollback before commit:

```powershell
git rm --cached --ignore-unmatch docs\171_v2_operational_delete_verification_gate.md
Remove-Item -LiteralPath docs\171_v2_operational_delete_verification_gate.md
git restore CHANGELOG.md docs\164_operator_data_mutation_safety_gate.md docs\165_v2_status_matrix.md
```

After commit, revert the document commit.

Operational rollback, if a later approved delete verification runs, is a separate
approved exact restore from the retained DB before-image, never regeneration from
source CSV. Preserve evidence, use approved marker-first reconcile for uncertain
delete runs, disable gates when approved, and fix forward from the recorded state.

## Stop Conditions

Stop before operational mutation when any of these are true:

- the protected preflight approval lifecycle in `docs/164` is absent/untested,
  `deletePreflightApprovalId` is not terminal `consumed`, its exact scope or
  deadline does not match, or it was not atomically bound to exactly one
  `deletePreflightId`;
- preflight claim owner/fence or human completion deadline is missing,
  substituted, expired, or not CAS-rechecked at snapshot/result publication; a
  crash/restart/delayed worker can copy/read/publish twice or after invalidation;
- the exact preflight result is not unexpired `ready_available` before claim,
  already names a consumer/run, can be used by two approvals/runs, can regress
  after claim/failure, or is not atomically claimed and terminally bound to the
  same `approvalId`/`deleteRunId` as the hard-delete run;
- approval record is missing, stale, edited after approval, or not stored in an
  approved location;
- the protected approval lifecycle in `docs/164` is absent/untested, the approval
  is not `available` before claim, the claim and one-run binding are non-atomic,
  a duplicate/concurrent request could create another run, or a committed run's
  approval could return to `available`/`invalid`;
- package metadata or checksum differs from the approval record;
- DB target class or diagnostic fingerprint differs, the protected exact DB
  binding is missing/unresolvable/substituted, or authoritative instance/
  database identity differs from the preflight approval/result or delete
  approval/run/reconcile binding;
- the singleton target-global coordinator id/state/owner/consumer/generation/
  evidence is missing, substituted, stale, overlaps another Preview/action, or
  is not atomically claimed with preflight/Delete/marker/reconcile;
- public schema class differs, the schema binding is missing/unresolvable/
  substituted, or owner-only schema verification fails;
- selected item count or exact key count differs, any protected binding is
  missing/unresolvable/substituted, or the owner-only exact material/integrity
  verification differs from the approval record;
- the Delete source-provenance snapshot/content binding is missing, mutable, expired,
  over ceiling, under-capacity, not owner-only/confidential, differs from exact
  preflight bytes/metric values/keys, reuses an upload snapshot, reopens source,
  lacks bounded final recovery disposition/disposal evidence, or is
  `disposal_failed_blocked`;
- the source-provenance snapshot is treated as an exact rollback image, or the
  target-side DB before-image store/schema/complete-column-set/capacity/
  confidentiality/retention contract is absent, untested, missing, substituted,
  over ceiling, incomplete, or not bound to the same approval/run/mutation/
  target/coordinator generations;
- the mutation-schema fence or DELETE/restore-INSERT side-effect binding/readiness
  is missing, substituted, stale, does not cover every foreign-key/cascade,
  trigger/rule, RLS/policy, generated/default, sequence, replication/publication/
  CDC, notification, and affected-relation class, does not hold required DDL-
  conflicting locks/schema generation through commit, or permits any secondary/
  external effect;
- the authoritative transaction does not lock/revalidate the selected rows,
  capture every typed column before DELETE, verify before-image row count equals
  `exactKeyCount`, atomically commit before-image + DELETE + marker, or roll back
  to zero DELETE on source-vs-DB value difference, schema/value drift, unsupported
  restore semantics, overflow, capacity failure, or concurrent change;
- `rollbackReadiness` is true before the exact DB before-image is transactionally
  captured, a committed marker lacks a matching `recovery_available` before-
  image, or restore/disposition can use source CSV instead of that before-image;
- DB-before-image retention exceeds the exact target-binding validity, or a
  restore lacks its immutable single-use approval/mutation id, same-target/
  coordinator bindings, exact-absence no-overwrite transaction, complete typed-
  column equality verification, marker-first recovery, or dual-record disposal;
- source-provenance and DB-before-image retention deadlines differ for a
  committed Delete, a preflight approval can dispose a DB before-image, a hard-
  delete approval can dispose a source snapshot, an aborted outcome requires or
  fabricates a DB before-image, or coordinator release does not wait for every
  recovery record that actually exists to become terminal;
- restore claim/marker/transaction/reconciliation/equality/disposition does not
  recheck both target-binding and DB-before-image validity with the authoritative
  target clock, lacks the ordered unrenewable active-use/reconcile/deadline margin,
  commits at/after active-use expiry, lets post-lease reconcile issue restore
  writes, or an expiry race can write, release, retry, or discard retained evidence;
- restore claim/commit/abort/unknown state does not match the exact lifecycle
  table, an aborted attempt reuses its consumed approval, an intact before-image
  cannot return to `recovery_available` with atomically advanced generations, or
  `commit_unknown_blocked` can release/dispose/retry;
- `deleteMutationId` is missing/not pre-reserved/substituted/reused, its target
  marker is missing/tampered/mismatched/nonterminal, Delete and marker transition
  are not one target transaction, reconcile infers outcome from row presence/
  delta instead of marker-first proof, or final recovery disposition is unresolved
  for any unrelated/new mutation;
- raw paths, filenames, raw keys, DB URLs, tokens, raw SQL, or secrets would be
  printed, committed, or pasted into evidence;
- a deterministic selection/keyset/source/signature digest or a private keyed
  HMAC would be returned, logged, printed, committed, or pasted into evidence;
- the request bundles Delete with Preview, Start Upload, Retry Failed, Settings
  save, feature-gate enablement, reset, cleanup, LAN, or deploy;
- an unresolved `commit_unknown` or `reconciliation_failed` blocker exists;
- the operator asks for broad cleanup or arbitrary SQL delete.
