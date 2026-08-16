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
> completion deadline, owner-only exact-byte Delete recovery snapshot and bounded
> recovery-disposition lifecycle, and pre-reserved target-side Delete mutation
> marker with marker-first reconciliation. Approval/run/result lifecycles alone
> do not unblock Delete.
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
deployment, or fixture mutation.

The current executable delete baseline remains
`docs/156_operator_already_in_db_delete_contract.md`: selected Upload Preview
items with status `already_in_db`, exact-key preflight, typed exact count,
no-undo acknowledgement, rollback-limitation acknowledgement, local DB target
guard, DELETE privilege preflight, audit evidence, and all-or-nothing delete
semantics.

## Plain-Language Rule

Operational delete verification is not "try a delete and see what happens."

Before any operational delete is allowed, the approval must name exactly what
will be deleted, prove the target is the intended DB, prove rollback limitations
are understood, and define the evidence report that will be preserved after the
run.

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
CSV row content, raw `(timestamp, device_id)` keys, raw SQL, DB URLs, tokens,
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
| `targetDbBindingState` | Current non-regressed protected state for this chain; must be valid for preflight/delete/reconcile. |
| `targetDbBindingValidUntilUtc` | Non-extendable validity ceiling covering preflight, delete, and any approved reconcile. |
| `targetDbBindingEvidenceId` | Opaque safe evidence for the protected target-identity lifecycle. |
| `deleteReconcileByUtc` | Hard deadline for any same-run read-only reconcile; no later than target binding validity. |
| `targetGlobalCoordinatorId` | Random non-derived opaque id resolving to the singleton protected coordinator for this exact trusted target across every Preview chain. |
| `targetGlobalCoordinatorState` | Must name this chain as the sole ready/active owner; after a resolved Delete it remains `recovery_disposition_pending` until restore/disposal closes. No older/newer Preview chain may overlap. |
| `targetGlobalCoordinatorOwnerFenceId` | Must equal this exact `targetOperationFenceId`. |
| `targetGlobalCoordinatorConsumer` | Exact target-global consumer, atomically changed with the chain consumer; empty at preflight eligibility, `delete_preflight`/`delete` during those stages, and `delete_disposition`/`delete_restore` only during the separately approved close. |
| `targetGlobalCoordinatorGeneration` | Monotonic target-global generation CAS-checked by Preview, preflight, Delete, Start, Retry, marker, and reconcile. |
| `targetGlobalCoordinatorEvidenceId` | Opaque safe evidence for the exact target-global owner/state/generation transition. |
| `targetOperationFenceId` | Random opaque protected fence shared with Start/Retry for this Preview/target binding. |
| `targetOperationFenceState` | Chain exclusion state; preflight begins from `idle`, Delete begins only from the preflight-owned `delete_ready` chain, and resolved Delete remains `recovery_disposition_pending` until restore/disposal closes. |
| `targetUploadBranchState` | Must not be active/retryable-owned by Start/Retry when Delete preflight or Delete claims. |
| `targetDeleteBranchState` | `delete_preflight_ready` before preflight, `delete_ready` before the one Delete claim, then `recovery_disposition_pending` after resolved outcome until restore/disposal closes. |
| `targetOperationConsumer` | Empty at preflight eligibility, `delete_preflight` while/result-owned, `delete` for the run and recovery-pending hold, then `delete_disposition` or `delete_restore` only for the separately approved close. |
| `targetOperationFenceGeneration` | Exact monotonic generation atomically advanced by each claim/terminal transition. |
| `targetOperationFenceEvidenceId` | Opaque safe evidence for the exact state/generation/consumer transition. |
| `schemaClass` | Public non-secret versioned class for the expected contract, such as `all_metrics_timestamp_device_id_unique_v1`. |
| `schemaBindingId` | Opaque random id resolving only in the owner-only protected store to exact schema-verification material and any private keyed HMAC. |
| `previewRunId` | Exact Preview run id used for selection. |
| `deletePreflightApprovalId` | Exact protected approval id consumed by the one preflight run. |
| `deletePreflightApprovalState` | Must be `consumed`. |
| `deletePreflightExecuteByUtc` | Exact preflight-claim deadline from the protected approval. |
| `deletePreflightCompleteByUtc` | Human-supplied absolute deadline for recovery-snapshot and preflight-result publication. |
| `deletePreflightClaimId` | Opaque durable owner token created before any source copy or DB read. |
| `deletePreflightFence` | Monotonic generation advanced by claim, restart, expiry, invalidation, and terminal publication; stale workers cannot copy, read, or publish. |
| `deletePreflightId` | Exact unexpired delete preflight id. |
| `deletePreflightState` | Must be `ready_available` before the joint one-run claim and `consumed` after a run commits. |
| `consumedByDeleteApprovalId` | Empty before claim; after run commit must equal this exact `approvalId` permanently. |
| `deleteRunId` | Empty before claim; generated and atomically bound to both the approval and preflight result when exactly one run commits. |
| `deleteMutationId` | Random unique target mutation id pre-reserved in the immutable hard-delete approval and claimed only with its approval/preflight/run/recovery-snapshot/coordinator bindings. |
| `deleteMutationOutcomeState` | `not_started`, `prepared`, `commit_pending`, `committed`, `aborted`, or `commit_unknown_blocked`; row presence/delta never determines it. |
| `deleteMutationOutcomeEvidenceId` | Opaque safe evidence from the immutable target marker or marker-first reconciliation. |
| `selectedAlreadyInDbItems` | Exact selected `already_in_db` item count. |
| `exactKeyCount` | Exact selected key count approved for delete. |
| `selectionBindingId` | Opaque random id resolving only in the owner-only protected store to the exact approved selection and its private integrity data. |
| `keysetBindingId` | Opaque random id resolving only in the owner-only protected store to the exact approved keyset and its private integrity data. |
| `sourceEvidenceBindingId` | Opaque random id resolving only in the owner-only protected store to exact source evidence without publishing a source-derived digest. |
| `sourceFileSignatureSetBindingId` | Opaque random id resolving only in the owner-only protected store to the exact source-file signature set and parsed keyset. |
| `deleteRecoverySnapshotId` | Opaque random id for the owner-only encrypted immutable exact-byte recovery snapshot created under the preflight approval before any preflight DB read; it is distinct from and may not reuse an upload snapshot. |
| `deleteRecoveryContentBindingId` | Opaque protected binding to private exact-byte digests, file boundaries, parsed keys, and recovery content; no digest or filename is public. |
| `deleteRecoverySnapshotState` | `prepared`, `preflight_bound`, `delete_bound`, `completed`, or `invalid`; no source reopen or state regression is allowed. |
| `deleteRecoveryObservedBytes` | Exact read-only observed byte count reviewed before approval; never inferred. |
| `deleteRecoverySnapshotMaxBytes` | Human-approved non-inferred byte ceiling bound in the preflight approval. |
| `deleteRecoverySnapshotRetainUntilUtc` | Human-approved non-extendable retention/access deadline covering Delete and same-run reconcile. |
| `deleteRecoveryCapacityEvidenceId` | Opaque safe evidence that protected storage can hold the approved bytes. |
| `deleteRecoveryConfidentialityClass` | Approved owner-only encryption/access-control class; no raw path or key material. |
| `deleteRecoveryDispositionState` | `scheduled`, `awaiting_recovery_disposition`, `in_progress`, `disposed`, or `disposal_failed_blocked`; key destruction and verified byte removal are mandatory on invalidation/preflight block/expiry or after the final recovery decision. |
| `deleteRecoveryFinalDispositionDecision` | After a resolved Delete: `accept_delete_and_dispose` only through the single-use disposition approval below, or `separately_approved_restore_then_dispose` only through a separately scoped restore approval; absent before human disposition. |
| `deleteRecoveryDispositionApprovalId` | Immutable/authenticated expiring single-use approval required for early `accept_delete_and_dispose`; `not_issued` until a human reviews the marker-proven outcome. Retention-expiry disposal uses the original preflight approval instead. |
| `deleteRecoveryDispositionApprovalState` | `not_issued` before a human issues it; then `available`, `claimed`, `consumed`, or `invalid`. Disposition may claim it once atomically with the exact snapshot cleanup action. |
| `deleteRecoveryDispositionExecuteByUtc` | `not_approved` before issuance; otherwise a human-supplied early-disposition deadline no later than snapshot retention. |
| `deleteRecoveryDispositionEvidenceId` | Opaque safe evidence of cryptographic disposition; required after access closes. |
| `deletePolicy` | Must be `already_in_db_exact_key` unless a later approved policy gate says otherwise. |
| `noUndoAcknowledgement` | Explicit acknowledgement that the app has no undo. |
| `rollbackReadiness` | Must be `true`. This is not replaceable by acknowledgement. |
| `rollbackLimitationAcknowledgement` | Explicit acknowledgement that recovery requires a separately approved exact recovery/Preview/Start chain bound to the retained immutable Delete recovery snapshot before its deadline/final disposition; current source files or matching metadata/keys cannot replace it. |
| `v2RowAttributionEnabled` | Explicit approved gate state, normally `false` unless separately approved. |
| `v2DbDeltaEvidenceRequired` | Explicit approved gate state. |
| `rowAttributionHmacAvailabilityClass` | Safe class such as `configured`, `not_configured`, or `not_applicable`; never the HMAC value. |
| `featureGateChangeApproved` | Must be `false` unless a separate approval explicitly changes gate state. |
| `approver` | Named human approver or approved role id. |
| `executor` | Named executor or approved role id. |
| `stopCondition` | Concrete condition that stops before mutation or after uncertain outcome. |
| `evidenceReportLocation` | Safe path or link where post-run evidence will be recorded. |
| `approvalExclusions` | Explicit list of actions not approved by this record. |

## Required Approval Wording

The field table and approval wording are both mandatory. The wording alone is
not a valid approval if any required field above is missing from the stored
approval record.

The approval must use this shape, with every placeholder filled from current
read-only evidence and delete preflight output:

```text
I approve exactly one operational hard delete for approval <approvalId>, initially in state available and claimable only until <deleteExecuteByUtc>.
The approved package sourceCommit is <packageSourceCommit>, package label is <packageLabel>, and zip SHA-256 is <zipSha256>.
The approved DB target class is <dbTargetClass> and diagnostic DB fingerprint hash is <dbFingerprintHash>. The expected exact target is anchored by pre-existing baseline <trustedTargetBaselineId> in verified/non-revoked state <trustedTargetBaselineState>, privacy-safe alias <trustedTargetAlias>, and safe evidence <trustedTargetBaselineEvidenceId>. The exact target comes from consumed preparation approval <targetIdentityPreparationApprovalId>, completed by <targetIdentityPreparationExecuteByUtc>, and is protected binding <targetDbBindingId> in state <targetDbBindingState>, valid only until <targetDbBindingValidUntilUtc>, with safe evidence <targetDbBindingEvidenceId>. The singleton exact-target coordinator is <targetGlobalCoordinatorId>, state/sole owner/consumer/generation/evidence <targetGlobalCoordinatorState>/<targetGlobalCoordinatorOwnerFenceId>/<targetGlobalCoordinatorConsumer>/<targetGlobalCoordinatorGeneration>/<targetGlobalCoordinatorEvidenceId>; it must reject every different Preview-chain owner. The shared target operation fence is <targetOperationFenceId>, with exact chain/upload/Delete states <targetOperationFenceState>/<targetUploadBranchState>/<targetDeleteBranchState>, consumer <targetOperationConsumer>, generation <targetOperationFenceGeneration>, and safe evidence <targetOperationFenceEvidenceId>; it must be the same fence already claimed by the named preflight result and both coordinator/fence generations must be atomically claimed for this delete run. Any same-run reconcile must complete by <deleteReconcileByUtc>, no later than that validity. The schema class is <schemaClass> and protected schema binding is <schemaBindingId>.
The approved scope is preview run <previewRunId>, delete-preflight approval <deletePreflightApprovalId> consumed by <deletePreflightExecuteByUtc> and completed by <deletePreflightCompleteByUtc> under owner <deletePreflightClaimId>/fence <deletePreflightFence>, unexpired ready_available delete preflight result <deletePreflightId>, selected already_in_db items <selectedAlreadyInDbItems>, and exact keys <exactKeyCount>.
That preflight result may be atomically claimed and consumed only by this approval <approvalId> and the exactly one deleteRunId generated in the joint claim transaction; it may not be reused by another approval or run.
The random unique target delete mutation id <deleteMutationId> is pre-reserved in this immutable approval and may be claimed only with this approval, preflight result, run, exact keyset/content binding, recovery snapshot, exact target, and both coordinator/fence generations. Before any delete, create exactly one target-side prepared marker with those bindings. The exact-key DELETE and prepared-to-committed marker transition must share one authoritative target transaction; mark aborted only after non-commit is authoritative. Response loss/timeout becomes commit_unknown_blocked unless marker-first reconciliation proves committed or aborted, and current row presence/delta must never infer the outcome.
The approved delete policy is <deletePolicy>.
The approved protected selection binding is <selectionBindingId>, keyset binding is <keysetBindingId>, source evidence binding is <sourceEvidenceBindingId>, and source file signature-set binding is <sourceFileSignatureSetBindingId>.
The immutable exact-byte Delete recovery snapshot is <deleteRecoverySnapshotId>, protected content binding <deleteRecoveryContentBindingId>, state <deleteRecoverySnapshotState>, observed bytes <deleteRecoveryObservedBytes>, approved byte ceiling <deleteRecoverySnapshotMaxBytes>, capacity evidence <deleteRecoveryCapacityEvidenceId>, owner-only confidentiality class <deleteRecoveryConfidentialityClass>, retention deadline <deleteRecoverySnapshotRetainUntilUtc>, disposition state <deleteRecoveryDispositionState>, final recovery disposition <deleteRecoveryFinalDispositionDecision or not_decided>, early-disposition approval <deleteRecoveryDispositionApprovalId=not_issued>/<deleteRecoveryDispositionApprovalState=not_issued>/<deleteRecoveryDispositionExecuteByUtc=not_approved>, and safe disposition evidence <deleteRecoveryDispositionEvidenceId or not_triggered>. It was created and privately content-verified before the preflight DB read under the named preflight approval, is distinct from every upload snapshot, and Delete/reconcile may not reopen the operational source.
Rollback readiness is true only because that protected snapshot retains the exact verified recovery bytes and parses to the same exact approved keyset/content binding.
I understand this delete has no app-level undo and recovery requires a separately approved recovery/Preview/Start chain from that exact retained snapshot while it remains valid; a current source file, metadata signature, or matching-key reparse cannot replace it. After a resolved Delete, the encrypted snapshot remains in awaiting_recovery_disposition until a separate immutable single-use disposition approval atomically authorizes early accept_delete_and_dispose, a separately scoped restore approval authorizes exact restore_then_dispose, or the original preflight approval's retention deadline triggers automatic key-first disposal. All unrelated or new mutations are blocked while that decision or cleanup is unresolved; only the separately approved exact recovery action bound to this retained snapshot/marker/coordinator may run before disposal.
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
- the preflight-bound recovery snapshot, not current source, carries the same
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
- rollback readiness is true and the rollback limitation is explicitly
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
- protected Delete recovery snapshot/content-binding ids, state, observed/maximum
  bytes, capacity/confidentiality evidence, retention deadline, final recovery
  disposition approval id/state/deadline or separately scoped restore approval,
  disposition state, and safe disposition evidence id;
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
- CSV row content;
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

The target-global coordinator, chain fence, and Delete recovery snapshot remain
owned/retained while the marker is nonterminal or `commit_unknown_blocked`, and
remain in non-advanceable `recovery_disposition_pending` after committed/aborted
outcome until exact restore/disposal is terminal.
Reinserted or re-deleted rows after the original transaction do not change its
marker-proven outcome. A missing, tampered, substituted, or still-`prepared`
marker at the reconcile deadline leaves the chain blocked; it does not authorize
another Delete, a restore, or disposal before the approved retention boundary.

Early `accept_delete_and_dispose` requires an immutable/authenticated
`deleteRecoveryDispositionApprovalId` in `available`, bound to the exact snapshot,
content binding, target marker/mutation outcome, coordinator/fence generation,
human decision, and deadline. Cleanup atomically claims that approval and the
snapshot disposition state, then performs key-first verified byte removal and
publishes exactly one safe evidence record; response loss returns the same
record. It must CAS the same target-global/chain owner and
`recovery_disposition_pending` generations to terminal only after verified
removal. Missing/substituted/expired/replayed/concurrent approval or outcome drift
must not destroy the key/bytes. Retention-expiry disposal remains pre-authorized
by the original preflight approval and must fence any early-disposition claimant.
A restore requires its own separately scoped mutation approval and is not
authorized by this document.
Deterministic cleanup tests must crash/restart before and after approval claim,
key destruction, byte removal, absence verification, coordinator/fence terminal
CAS, and evidence publication. Recovery returns/publishes only the same terminal
result; it never restores a destroyed key, repeats a different cleanup, releases
the coordinator before verified removal, or loses the safe evidence record.

Required early-disposition approval wording, issued only after human review of a
terminal marker-proven Delete outcome:

```text
The Delete recovery disposition approval id is <deleteRecoveryDispositionApprovalId>, initially available and claimable only by <deleteRecoveryDispositionExecuteByUtc>.
I approve exactly one early accept_delete_and_dispose action for recovery snapshot <deleteRecoverySnapshotId>, protected content binding <deleteRecoveryContentBindingId>, retained only until <deleteRecoverySnapshotRetainUntilUtc>, from Delete mutation <deleteMutationId> in authoritative terminal outcome <deleteMutationOutcomeState> with evidence <deleteMutationOutcomeEvidenceId>.
It binds exact-target coordinator/fence <targetGlobalCoordinatorId>/<targetOperationFenceId>, exact owner/consumer/generations/evidence <targetGlobalCoordinatorOwnerFenceId>/<targetGlobalCoordinatorConsumer>/<targetGlobalCoordinatorGeneration>/<targetGlobalCoordinatorEvidenceId>/<targetOperationFenceGeneration>/<targetOperationFenceEvidenceId>, named approver <approver>, and named executor <executor>.
The cleanup action must atomically claim this approval and the same awaiting_recovery_disposition snapshot, destroy its per-record key first, remove and verify absence of its bytes, publish exactly one <deleteRecoveryDispositionEvidenceId>, and finish consumed. Response loss returns only that same evidence; mismatch/expiry/concurrent/replay claim performs no early disposal and finishes invalid only if cleanup did not commit.
This approval does not authorize restore, Preview, Start Upload, Retry Failed, Delete, DB read/write, source access/mutation, Settings save, runtime lifecycle, reset, cleanup outside this exact snapshot, LAN, or deployment.
```

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
- one protected exact-byte Delete recovery snapshot is privately verified and
  retained from before preflight DB read through marker-resolved Delete and the
  bounded human recovery decision, never reuses the upload snapshot or reopens
  source, and completes key-first disposal with safe evidence; ceiling, capacity,
  confidentiality, expiry, crash, replacement, source removal/replacement after
  successful preflight without any Delete/reconcile source open, and disposal-
  failure tests pass;
- the immutable approval pre-reserves one `deleteMutationId`; its bound prepared
  target marker and exact DELETE commit atomically, reconciliation reads marker
  first, external reinsert/re-delete cannot alter the proven outcome, and missing/
  tampered/nonterminal marker state remains blocked;
- any gate-on DB delta and row attribution evidence is preserved;
- any uncertain outcome is reconciled or explicitly left blocked with evidence;
- `$review` has no unresolved safety finding for the evidence and rollback
  report.

If the run uses only the v1 delete contract with V2 gates off, it may prove the
current hard-delete maintenance path but must not be described as full V2
gate-on delete evidence.

## Rollback

Document-only rollback before commit:

```powershell
git rm --cached --ignore-unmatch docs\171_v2_operational_delete_verification_gate.md
Remove-Item -LiteralPath docs\171_v2_operational_delete_verification_gate.md
git restore CHANGELOG.md docs\164_operator_data_mutation_safety_gate.md docs\165_v2_status_matrix.md
```

After commit, revert the document commit.

Operational rollback, if a later approved delete verification runs, is not data
deletion. Preserve evidence, use approved reconcile for uncertain delete runs,
disable gates when approved, and fix forward from the recorded state.

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
- the Delete recovery snapshot/content binding is missing, mutable, expired,
  over ceiling, under-capacity, not owner-only/confidential, differs from exact
  preflight bytes/metric values/keys, reuses an upload snapshot, reopens source,
  lacks bounded final recovery disposition/disposal evidence, or is
  `disposal_failed_blocked`;
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
