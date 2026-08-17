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
> disposition lifecycle with non-interchangeable preflight-owned source,
> hard-delete-owned DB-before-image, and restore-owned cleanup ids/deadlines/
> states/evidence, and a pre-reserved target-side Delete mutation marker
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

`docs/156_operator_already_in_db_delete_contract.md` is only a legacy
implementation/API reference. It is non-operational, non-authorizing, and
superseded for readiness and execution decisions by this document together with
`docs/164_operator_data_mutation_safety_gate.md`. Its source-derived rollback,
coarse-target, and row-count reconciliation rules do not satisfy this gate and
must not be used to authorize or execute Delete.

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

Operational Delete, preflight, disposition, and restore approvals must be stored
before use in a human-authenticated, integrity-protected append-only authority
that implements revocation plus atomic expiring single-use state transitions.
The runtime resolves and claims the protected authority record, never a request-
supplied string or repository file.

A dedicated sanitized Markdown file under `docs/operator-evidence/`, Git commit,
PR, issue, or comment may export opaque approval ids/states and sanitized
evidence after the protected record exists. It is evidence only and is never the
runtime approval authority, even when committed before mutation. Links must point
back to the protected source record without exposing private material.

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
| `approvalContractRevision` | Exact `docs164-2026-08-17-r1`; any other or missing revision is invalid. |
| `approvalId` | Stable safe id for the approval record. |
| `deleteApprovalState` | `available` before the one-run claim; later transitions follow `docs/164`. |
| `deleteExecuteByUtc` | Hard deadline for the one-run delete claim. |
| `deleteActiveUseExpiresAtUtc` | Human-supplied, non-renewable authoritative DELETE commit deadline; claim must precede it and the target transaction must commit strictly before it using the target DB clock. At/after it every DELETE rolls back. |
| `deleteMutationReconcileMarginSeconds` | Positive base-10 integer within a fixed/versioned/tested maximum, reserving time between active-use expiry and normal reconcile; checked arithmetic requires `deleteActiveUseExpiresAtUtc <= deleteReconcileByUtc - deleteMutationReconcileMarginSeconds`. No default/coercion/extension. |
| `packageSourceCommit` | Exact package source commit approved for the run. |
| `packageLabel` | Package label or safe package id, without raw local path. |
| `zipSha256` | Exact trusted content-addressed ZIP/installer SHA-256; `zipCreated=true` is mandatory before operational preflight/Delete/reconcile/restore. |
| `artifactReleaseTrustRootId` | Random non-derived id for the pre-provisioned owner-controlled release trust root outside the candidate artifact. |
| `artifactSignerKeyId` | Opaque id for the exact authorized signing key under that trust root. |
| `artifactSignatureAlgorithmVersion` | Exact allowlisted signature/manifest verification algorithm revision. |
| `artifactSignerRevocationState` | Must be current and non-revoked at every stage admission. |
| `artifactIndependentVerifierEvidenceId` | Opaque evidence that an independent verifier, not candidate-supplied code or keys, authenticated the manifest/signature. |
| `artifactFullFileManifestId` | Opaque id plus authenticated hash for governed executable code, frontend assets, dependencies, and build metadata in the trusted artifact. |
| `installedTreeVerificationEvidenceId` | Opaque time-bound proof that the installed governed tree equals the trusted artifact manifest. |
| `executingTreeVerificationEvidenceId` | Opaque time-bound proof that the running backend/frontend/dependency roots are that verified tree, not another unpacked directory. |
| `artifactVerificationObservedAtUtc` | Exact UTC time of the full installed/executing-tree verification immediately preceding admission. |
| `artifactVerificationValidUntilUtc` | Human-bound expiry within a fixed/versioned/tested maximum age and no later than the approved stage deadline. |
| `artifactIntegrityLockEvidenceId` | Opaque evidence for an OS-enforced read-only package ACL and exclusive machine-global integrity lock held through preflight/Delete/reconcile/restore; any tamper signal fences work and permits zero further DB writes. |
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
| `targetGlobalCoordinatorId` | Random non-derived opaque id resolving through the fixed authenticated machine-global authority, never a user-profile/app-state DB, to the singleton coordinator for this exact trusted target across every Windows user, package, installation, and `EWC_STATE_DB_PATH` on the approved operator PC. |
| `targetGlobalCoordinatorState` | Must name this chain as the sole ready/active owner; after a resolved Delete it remains `recovery_disposition_pending` until restore/disposal closes. No older/newer Preview chain may overlap. |
| `targetGlobalCoordinatorOwnerFenceId` | Must equal this exact `targetOperationFenceId`. |
| `targetGlobalCoordinatorConsumer` | Exact target-global consumer, atomically changed with the chain consumer; empty at preflight eligibility, `delete_preflight`/`delete` during those stages, and `delete_disposition`/`delete_restore` only during the separately approved close. |
| `targetGlobalCoordinatorGeneration` | Monotonic target-global generation CAS-checked by Preview, preflight, Delete, Start, Retry, marker, and reconcile. |
| `targetGlobalCoordinatorEvidenceId` | Opaque safe evidence for the exact target-global owner/state/generation transition, fixed authority/ACL-restricted cross-session mutex, single-PC/local-target boundary, and target-side mutation epoch. |
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
| `deleteMutationOutcomeState` | `not_started`, `prepared`, `commit_pending`, `committed`, `aborted`, `commit_unknown_blocked`, or `commit_unknown_retention_incident_blocked`; row presence/delta never determines it. The incident state is permanent until marker-first outcome resolution plus its required terminal join, or mandatory DB-before-image cleanup immediately after committed proof/reconcile cutoff, never an inferred abort or wait-until-ceiling policy. |
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
| `deleteRecoverySnapshotRetainUntilUtc` | Human-approved standard non-extendable recovery-access deadline covering Delete, same-run reconcile, and the normal final recovery decision. At this instant decryption/recovery access ends irreversibly and the pre-reserved source cleanup is claimed; key-first byte removal/evidence then has only its separately approved positive cleanup margin. A hard-delete approval may proceed only when `deleteDbBeforeImageRetainUntilUtc` is exactly this same standard access deadline and a separate, later `deleteCommitUnknownEscrowRetainUntilUtc` is pre-authorized for the sole unresolved-outcome exception. |
| `deleteRecoveryCapacityEvidenceId` | Opaque safe evidence that protected storage can hold the approved bytes. |
| `deleteRecoveryConfidentialityClass` | Approved owner-only encryption/access-control class; no raw path or key material. |
| `deleteRecoveryDispositionState` | `scheduled`, `awaiting_recovery_disposition`, `in_progress`, `disposed`, or `disposal_failed_blocked`; key destruction and verified byte removal are mandatory on invalidation/preflight block/expiry or after the final recovery decision. |
| `deleteRecoveryFinalDispositionDecision` | Canonical pre-disposition sentinel is `not_decided`. After a resolved Delete, committed permits dual-record `accept_delete_and_dispose` or `separately_approved_restore_then_dispose`; aborted permits source-only `accept_delete_and_dispose` and makes restore not applicable. |
| `deleteRecoveryDispositionApprovalId` | Immutable/authenticated expiring single-use approval required for early `accept_delete_and_dispose`; `not_issued` until a human reviews the marker-proven outcome. Retention-expiry disposal of the source snapshot uses the original preflight approval; disposal of a committed DB before-image separately uses the consumed hard-delete approval that pre-reserved it. |
| `deleteRecoveryDispositionApprovalState` | `not_issued` before a human issues it; then `available`, `claimed`, `consumed`, or `invalid`. Disposition may claim it once atomically with the exact snapshot cleanup action. |
| `deleteRecoveryDispositionExecuteByUtc` | `not_approved` before issuance; otherwise a human-supplied early-disposition deadline no later than the minimum of source-snapshot and DB-before-image retention when a committed Delete created both records, or no later than source-snapshot retention for an aborted Delete with no DB before-image. |
| `deleteRecoveryDispositionEvidenceId` | Opaque safe evidence of cryptographic disposition; required after access closes. |
| `deleteSourceSnapshotCleanupTransactionId` | Random unique cleanup id pre-reserved only by the preflight approval that owns the source-provenance snapshot. It can claim, key-destroy, remove, and verify only `deleteRecoverySnapshotId`; it can never address a DB before-image. |
| `deleteSourceSnapshotCleanupMarginSeconds` | Positive base-10 integer, explicitly human-approved within a fixed/versioned/tested maximum. It reserves only key-first byte-removal/evidence time after source access expires; it never extends decryption or recovery access. |
| `deleteSourceSnapshotCleanupByUtc` | Hard source-snapshot cleanup-commit deadline computed with checked UTC addition as `deleteRecoverySnapshotRetainUntilUtc + deleteSourceSnapshotCleanupMarginSeconds`. At retention expiry access ends irreversibly and the cleanup is claimed immediately; key-first removal/evidence must commit strictly before this later deadline. Underflow/overflow, zero/non-integer/inferred margin, or impossible ordering blocks before approval claim. Early disposition may commit sooner. |
| `deleteSourceSnapshotCleanupState` | `not_started`, `claimed`, terminal `committed`, or `disposal_failed_blocked`; a committed cleanup leaves `deleteRecoverySnapshotState=disposed`, and response loss returns only the same transaction/evidence. No DB cleanup or restore state can consume this lifecycle. |
| `deleteSourceSnapshotCleanupEvidenceId` | Opaque safe proof that the preflight-owned source-snapshot key was destroyed first, its exact bytes were removed, and absence was verified without opening the operational source or touching target DB data. |
| `deleteDbBeforeImageId` | Random opaque id pre-reserved by the hard-delete approval for the owner-only encrypted exact DB before-image. The complete typed value of every column in every selected row is inserted under this id in the same authoritative transaction as the exact-key DELETE and committed marker transition. |
| `deleteDbBeforeImageContentBindingId` | Opaque protected binding to the complete canonical typed pre-delete row set; raw values and private integrity material remain owner-only. |
| `deleteDbBeforeImageSchemaBindingId` | Opaque protected binding to the exact table/schema version used to capture and later restore the before-image. |
| `deleteDbBeforeImageColumnSetBindingId` | Opaque protected binding to the complete ordered column set, including null/default/generated/system-column treatment. Any column that cannot be captured and restored exactly keeps `rollbackReadiness=false_pending_atomic_before_image` and forces transaction abort with zero DELETE. |
| `deleteDbBeforeImageRowCount` | Exact selected row count captured transactionally; it must equal `exactKeyCount` before DELETE. |
| `deleteDbBeforeImageObservedBytes` | `not_observed` in the approval; exact protected serialized bytes recorded by the authoritative transaction and required to be no greater than the approved ceiling. |
| `deleteDbBeforeImageMaxBytes` | Human-approved, non-inferred encrypted before-image byte ceiling named by the hard-delete approval. Overflow causes transaction rollback and zero DELETE. |
| `deleteDbBeforeImageCapacityEvidenceId` | Opaque safe evidence that the protected target-side recovery store has capacity for the approved ceiling before mutation. |
| `deleteDbBeforeImageConfidentialityClass` | Approved owner-only encryption/access-control class for exact DB row values. |
| `deleteDbBeforeImageRetainUntilUtc` | Human-approved standard deadline exactly equal to `deleteRecoverySnapshotRetainUntilUtc`, no earlier than Delete reconcile and the normal recovery-disposition window. Unequal standard deadlines invalidate the hard-delete approval before mutation. Only a pre-authorized unresolved-outcome escrow may retain authenticated keyless before-image bytes/metadata past this standard deadline, after the same boundary CAS has irreversibly destroyed any image key. |
| `deleteDbBeforeImageState` | `not_created` before the authoritative transaction; `recovery_available` only when before-image + exact DELETE + committed marker have committed atomically; normal recovery may then use `restoring`/`restored`; `incident_keyless_cleanup_pending` is allowed only after the standard-expiry unresolved-outcome CAS has irreversibly destroyed the image key and retained authenticated bytes/metadata for cleanup; cleanup may end in `disposed`, `disposal_failed_blocked`, or `invalid`. The incident state authorizes no decrypt/read/restore, and a committed Delete with missing/mismatched before-image is permanently blocked. |
| `deleteDbBeforeImageDispositionEvidenceId` | Opaque safe evidence for key-first disposal and verified byte removal of the before-image after accepted Delete or separately approved exact restore. |
| `deleteDbBeforeImageNormalCleanupMarginSeconds` | Positive base-10 integer, separately human-approved within a fixed/versioned/tested maximum. For a marker-proven terminal Delete at standard recovery expiry, it reserves only recovery-store key destruction/byte removal/evidence time and never extends restore or decryption access. |
| `deleteDbBeforeImageNormalCleanupByUtc` | Checked UTC sum `deleteDbBeforeImageRetainUntilUtc + deleteDbBeforeImageNormalCleanupMarginSeconds`, strictly later than standard access expiry and no later than `targetDbBindingValidUntilUtc`. At standard expiry a known committed outcome must atomically revoke access and claim cleanup; removal/evidence commits strictly before this deadline. Zero/non-integer/inferred margin, overflow, equality/late cleanup, or impossible ordering blocks. It is not the incident deadline. |
| `deleteCommitUnknownEscrowRetainUntilUtc` | Human-approved absolute incident-escrow ceiling, strictly later than the standard retention deadline, no later than `targetDbBindingValidUntilUtc`, and within a fixed/versioned implementation maximum. It is pre-reserved in the hard-delete approval, cannot be extended, and is used only when the marker remains nonterminal/missing/tampered at the standard deadline. |
| `deleteCommitUnknownEscrowDispositionMarginSeconds` | Positive base-10 integer, separately human-approved, within the implementation's fixed/versioned/documented/tested maximum; after the standard-expiry CAS has already destroyed any image key, it reserves time after incident reconciliation and before the earlier of escrow retention or target-binding validity only for key-absence verification, authenticated byte removal, absence verification, and permanent-block evidence publication. No default or coercion is allowed. |
| `deleteCommitUnknownEscrowReconcileByUtc` | Human-approved last marker-first read-only incident-reconcile deadline, later than the standard `deleteReconcileByUtc` only for the activated escrow path, with checked UTC arithmetic enforcing `deleteCommitUnknownEscrowReconcileByUtc <= min(deleteCommitUnknownEscrowRetainUntilUtc, targetDbBindingValidUntilUtc) - deleteCommitUnknownEscrowDispositionMarginSeconds`. Underflow or impossible ordering invalidates the approval before claim. It authorizes no row-presence inference, restore, Delete, or other DB read/write. |
| `deleteCommitUnknownEscrowState` | `not_active`, `active_locked`, `resolved_aborted`, `resolved_committed_disposition_pending`, `disposed_permanent_block`, or `disposal_failed_blocked`. Incident activation has already destroyed any image key and moved existing authenticated bytes/metadata to `incident_keyless_cleanup_pending`. A committed outcome first observed after standard retention cannot enter ordinary restore/disposition: it remains non-advanceable until the pre-authorized incident cleanup verifies key absence, removes/verifies absence of those bytes, and publishes permanent recovery-loss/security-incident NO-GO. |
| `deleteCommitUnknownEscrowEvidenceId` | Opaque safe evidence for incident activation/key destruction, marker-first resolution, or final key-absence verification plus byte removal/permanent block. It contains no row values, raw keys, or target identity. |
| `deleteDbBeforeImageCleanupTransactionId` | Random unique cleanup id pre-reserved only by the hard-delete approval that owns the Delete-created DB before-image. It binds that exact image, target binding, machine-global/target-global/chain owner and generations, deadline, and terminal evidence; it can never address the source snapshot or a later restore-owned cleanup. |
| `deleteDbBeforeImageCleanupByUtc` | Incident-only hard DB-before-image cleanup-commit deadline equal to the earlier of incident escrow retention and target-binding validity; it must retain the approved positive margin after incident reconcile and commit strictly before that deadline. It is selected only by an atomic unresolved-marker incident transition at standard expiry; a known terminal outcome must use `deleteDbBeforeImageNormalCleanupByUtc`. |
| `deleteDbBeforeImageCleanupState` | `not_started`, `claimed_early`, `claimed_normal`, `incident_locked`, `claimed_incident`, terminal `not_applicable_aborted_incident`, `committed`, `superseded_by_restore_cleanup`, `disposal_failed_blocked`, or terminal `disposed_permanent_block`; cleanup is idempotent and response loss returns the same transaction/evidence. A valid early-disposition approval may CAS only `not_started -> claimed_early` before standard expiry. At standard expiry an atomic CAS selects exactly one normal or incident deadline and makes every other branch inapplicable. Marker-first incident reconciliation may CAS `incident_locked -> not_applicable_aborted_incident` only with target-epoch-serialized authoritative proof that no before-image/key/bytes exist; an unexpected image must instead use `claimed_incident` and permanent-block cleanup. An authoritative committed restore or a restore still unknown at its reconcile cutoff atomically supersedes this unclaimed Delete-owned cleanup in favor of the exact restore-owned cleanup; an authoritative aborted restore leaves it unchanged. |
| `deleteDbBeforeImageCleanupEvidenceId` | Opaque safe proof that the hard-delete-approval-bound recovery-store-only transaction destroyed/verified absence of the exact before-image key, removed/verified absence of its bytes, and touched no marker, operational row, or source snapshot; for terminal `not_applicable_aborted_incident`, it instead proves under the same target epoch that no before-image/key/bytes existed and records the non-regressing absent branch. |
| `deleteDbRestoreApprovalId` | `not_issued` in the hard-delete approval; a later random immutable/authenticated expiring single-use approval id is required for exact restore. |
| `deleteDbRestoreApprovalState` | `not_issued` before human review; then `available`, `claimed`, `consumed`, or `invalid`. |
| `deleteDbRestoreExecuteByUtc` | `not_approved` before issuance; otherwise a human-supplied claim deadline no later than the non-renewable restore active-use lease. |
| `deleteDbRestoreActiveUseExpiresAtUtc` | `not_approved` before issuance; otherwise the unrenewable authoritative-transaction commit deadline. It must be strictly earlier than `deleteDbRestoreReconcileByUtc`. A transaction at or after it rolls back every restore write. |
| `deleteDbRestoreReconcileByUtc` | `not_approved` before issuance; otherwise the last marker-first read-only reconcile/equality-publication deadline, no later than the minimum of target-binding validity and before-image retention after reserving the approved disposition margin. Reconcile after active-use expiry may prove an already committed marker but may issue no restore write. |
| `deleteDbRestoreDispositionMarginSeconds` | Positive human-approved margin between restore reconcile completion and the minimum target-binding/before-image deadline, sufficient for terminal disposition or safe blocked evidence publication. |
| `deleteDbRestoreMutationId` | `not_created` before issuance; later a random unique id pre-reserved in the restore approval for an atomic before-image restore marker/transaction. |
| `deleteDbRestoreOutcomeState` | `not_created`, then `prepared`, `committed`, `aborted`, `commit_unknown_blocked`, or terminal `unknown_disposed_permanent_block`; current row presence never determines the outcome. The final state is allowed only after the approval-bound hard deadline forces key-first before-image disposal with no outcome inference and permanent NO-GO. |
| `deleteDbRestoreOutcomeEvidenceId` | Opaque safe evidence from the immutable restore marker or marker-first reconciliation. |
| `deleteDbRestoreCleanupTransactionId` | `not_created` before restore approval; then a new random unique cleanup id pre-reserved only by that restore approval. It may clean the exact DB before-image after a committed/unknown restore outcome and can never consume the source-snapshot or Delete-owned cleanup lifecycle. |
| `deleteDbRestoreCleanupByUtc` | `not_approved` before restore approval; otherwise the hard restore-owned before-image cleanup deadline, strictly after restore reconcile by the approved margin and no later than the minimum target-binding/before-image deadline. |
| `deleteDbRestoreCleanupState` | `not_created`, then `not_started`, `claimed`, `committed`, `not_applicable_aborted`, `disposal_failed_blocked`, or terminal `disposed_permanent_block`. It becomes active only when restore commits or remains unknown at reconcile cutoff; authoritative abort leaves it terminal `not_applicable_aborted` and preserves the Delete-owned cleanup lifecycle. |
| `deleteDbRestoreCleanupEvidenceId` | Opaque safe proof for the restore-approval-owned before-image cleanup; it is distinct from source-snapshot and Delete-owned incident/disposition evidence. |
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
The approved package sourceCommit is <packageSourceCommit>, package label is <packageLabel>, zipCreated is true, trusted ZIP/installer SHA-256 is <zipSha256>, authenticated full-file manifest is <artifactFullFileManifestId>, installed-tree evidence is <installedTreeVerificationEvidenceId>, executing-tree evidence is <executingTreeVerificationEvidenceId>, verification observation/expiry are <artifactVerificationObservedAtUtc>/<artifactVerificationValidUntilUtc>, and integrity-lock evidence is <artifactIntegrityLockEvidenceId>. Admission must immediately reverify and hold the OS-enforced read-only package ACL plus machine-global integrity lock through the stage; a mutable unpacked/self-reported/different or post-admission changed execution tree is invalid and permits zero further DB writes.
The approved DB target class is <dbTargetClass> and diagnostic DB fingerprint hash is <dbFingerprintHash>. The expected exact target is anchored by pre-existing baseline <trustedTargetBaselineId> in verified/non-revoked state <trustedTargetBaselineState>, privacy-safe alias <trustedTargetAlias>, and safe evidence <trustedTargetBaselineEvidenceId>. The exact target comes from consumed preparation approval <targetIdentityPreparationApprovalId>, completed by <targetIdentityPreparationExecuteByUtc>, and is protected binding <targetDbBindingId> in state <targetDbBindingState>, valid only until <targetDbBindingValidUntilUtc>, with safe evidence <targetDbBindingEvidenceId>. The singleton exact-target coordinator is <targetGlobalCoordinatorId>, state/sole owner/consumer/generation/evidence <targetGlobalCoordinatorState>/<targetGlobalCoordinatorOwnerFenceId>/<targetGlobalCoordinatorConsumer>/<targetGlobalCoordinatorGeneration>/<targetGlobalCoordinatorEvidenceId>; its evidence attests the fixed authenticated machine-global authority, ACL-restricted cross-session mutex, single-operator-PC/local-target boundary, and target-side mutation epoch, and it must reject every different Preview-chain owner or user-profile/app-state authority. The shared target operation fence is <targetOperationFenceId>, with exact chain/upload/Delete states <targetOperationFenceState>/<targetUploadBranchState>/<targetDeleteBranchState>, consumer <targetOperationConsumer>, generation <targetOperationFenceGeneration>, and safe evidence <targetOperationFenceEvidenceId>; it must be the same fence already claimed by the named preflight result and both coordinator/fence generations must be atomically claimed for this delete run. Any same-run reconcile must complete by <deleteReconcileByUtc>, no later than that validity. The schema class is <schemaClass> and protected schema binding is <schemaBindingId>.
The approved scope is preview run <previewRunId>, delete-preflight approval <deletePreflightApprovalId> consumed by <deletePreflightExecuteByUtc> and completed by <deletePreflightCompleteByUtc> under owner <deletePreflightClaimId>/fence <deletePreflightFence>, unexpired ready_available delete preflight result <deletePreflightId>, selected already_in_db items <selectedAlreadyInDbItems>, and exact keys <exactKeyCount>.
The one-run claim deadline is <deleteExecuteByUtc>. The non-renewable authoritative DELETE commit deadline is <deleteActiveUseExpiresAtUtc>, with positive human-approved reconcile margin <deleteMutationReconcileMarginSeconds>; checked ordering requires deleteExecuteByUtc < deleteActiveUseExpiresAtUtc <= deleteReconcileByUtc - deleteMutationReconcileMarginSeconds. The target transaction must commit strictly before active-use expiry using the authoritative target clock; at/after expiry it rolls back every DELETE and cannot renew or infer success.
That preflight result may be atomically claimed and consumed only by this approval <approvalId> and the exactly one deleteRunId generated in the joint claim transaction; it may not be reused by another approval or run.
The random unique target delete mutation id <deleteMutationId> and DB before-image id <deleteDbBeforeImageId> are pre-reserved in this immutable approval and may be claimed only with this approval, preflight result, run, exact keyset/source-provenance binding, exact target, schema/column bindings, mutation-schema fence <deleteDbMutationSchemaFenceBindingId>, mutation-side-effect binding <deleteDbMutationSideEffectBindingId> in readiness <deleteDbMutationSideEffectReadiness=direct_rows_only_no_unmodeled_or_nonrestorable_effects> for both DELETE and exact restore INSERT, and both coordinator/fence generations. Before any delete, create exactly one target-side prepared marker with those bindings. In one authoritative target transaction, first enforce the same target-global coordinator id/generation/owner through its target-side mutation epoch, then acquire and hold the bound engine-appropriate DDL-conflicting relation/catalog locks or enforced schema-generation fence through commit; only then revalidate the schema/side-effect bindings and exact selected-row locks. Prove every DELETE/INSERT foreign-key/cascade, trigger/rule, RLS/policy, generated/default, sequence, replication/publication/CDC, notification, and affected-relation class is absent or inert so only the selected direct rows can change, capture every column's complete typed pre-delete value into the protected before-image under content/schema/column bindings <deleteDbBeforeImageContentBindingId>/<deleteDbBeforeImageSchemaBindingId>/<deleteDbBeforeImageColumnSetBindingId>, enforce exact row count <deleteDbBeforeImageRowCount=exactKeyCount> and byte ceiling <deleteDbBeforeImageMaxBytes>, transition rollbackReadiness from false_pending_atomic_before_image to true, execute the exact-key DELETE, and transition the marker to committed. Any stale coordinator epoch, unfenced DDL/configuration window, secondary relation or externally observable effect, missing row/column, schema or side-effect drift, unsupported restore semantics, overflow, capacity/confidentiality failure, binding mismatch, or concurrent value change rolls back the entire transaction and performs zero DELETE. Mark aborted only after non-commit is authoritative. Response loss/timeout becomes commit_unknown_blocked unless marker-first reconciliation proves the same committed marker and recovery_available before-image; current row presence/delta must never infer the outcome.
The authoritative DELETE transaction must lock the same target-side coordinator epoch row used by reconcile/incident cleanup, recheck its generation and `target_clock < deleteActiveUseExpiresAtUtc` immediately before commit, and make the before-image + DELETE + marker commit conditional on that epoch. At active-use expiry, normal reconcile must serialize on that row and atomically advance the epoch/fence before finalizing an uncommitted prepared marker as aborted. Incident activation and the hard-delete-owned DB-before-image cleanup must acquire the same serialization point; that cleanup cannot claim, remove, or certify absence until every old-epoch DELETE has either committed first with its marker/before-image or is fenced to authoritative non-commit. A delayed old transaction can never commit after epoch advance.
The prepared marker and target-side epoch record must bind the exact active-use deadline and mutation-to-reconcile margin from this approval; a worker-supplied or renewed deadline is invalid.
The normal DB-before-image recovery-access cutoff is <deleteDbBeforeImageRetainUntilUtc>, with positive human-approved <deleteDbBeforeImageNormalCleanupMarginSeconds> and checked <deleteDbBeforeImageNormalCleanupByUtc=deleteDbBeforeImageRetainUntilUtc+deleteDbBeforeImageNormalCleanupMarginSeconds>, strictly within <targetDbBindingValidUntilUtc>. At that cutoff one epoch-serialized CAS must select exactly one branch: marker-proven committed irreversibly revokes decryption/restore access, claims <deleteDbBeforeImageCleanupState=claimed_normal>, and completes key-first removal/evidence strictly before the normal cleanup deadline; marker-proven aborted proves <deleteDbBeforeImageState=not_created>; only a still nonterminal/missing/tampered marker may select <deleteDbBeforeImageCleanupState=incident_locked>, irreversibly destroy any existing image key, transition that image to <deleteDbBeforeImageState=incident_keyless_cleanup_pending>, and select the later incident-only <deleteDbBeforeImageCleanupByUtc>. Normal and incident deadlines are mutually exclusive, cannot be inferred/renewed, and response loss returns the same selected branch.
The approved delete policy is <deletePolicy>.
The approved protected selection binding is <selectionBindingId>, keyset binding is <keysetBindingId>, source evidence binding is <sourceEvidenceBindingId>, and source file signature-set binding is <sourceFileSignatureSetBindingId>.
The legacy-named source-provenance snapshot is <deleteRecoverySnapshotId>, protected source content binding <deleteRecoveryContentBindingId>, state <deleteRecoverySnapshotState>, observed bytes <deleteRecoveryObservedBytes>, approved byte ceiling <deleteRecoverySnapshotMaxBytes>, capacity evidence <deleteRecoveryCapacityEvidenceId>, owner-only confidentiality class <deleteRecoveryConfidentialityClass>, retention/access deadline <deleteRecoverySnapshotRetainUntilUtc>, disposition state <deleteRecoveryDispositionState>, final recovery disposition <deleteRecoveryFinalDispositionDecision or not_decided>, early-disposition approval <deleteRecoveryDispositionApprovalId=not_issued>/<deleteRecoveryDispositionApprovalState=not_issued>/<deleteRecoveryDispositionExecuteByUtc=not_approved>, and preflight-owned cleanup <deleteSourceSnapshotCleanupTransactionId>/<deleteSourceSnapshotCleanupMarginSeconds>/<deleteSourceSnapshotCleanupByUtc=deleteRecoverySnapshotRetainUntilUtc+deleteSourceSnapshotCleanupMarginSeconds>/<deleteSourceSnapshotCleanupState=not_started>/<deleteSourceSnapshotCleanupEvidenceId=not_triggered>. At retention expiry decryption/recovery access ends and this cleanup is claimed immediately; the positive margin authorizes only key-first byte removal/absence verification/evidence strictly before its cleanup deadline, never continued access. It was created and privately content-verified before the preflight DB read under the named preflight approval, is distinct from every upload snapshot, and Delete/reconcile may not reopen the operational source. It proves source/key provenance only and is not an exact DB rollback image.
The exact DB before-image is pre-reserved as <deleteDbBeforeImageId>, initially <deleteDbBeforeImageState=not_created>, with protected content/schema/column bindings <deleteDbBeforeImageContentBindingId>/<deleteDbBeforeImageSchemaBindingId>/<deleteDbBeforeImageColumnSetBindingId>, mutation-schema fence <deleteDbMutationSchemaFenceBindingId>, mutation-side-effect binding/readiness <deleteDbMutationSideEffectBindingId>/<deleteDbMutationSideEffectReadiness=direct_rows_only_no_unmodeled_or_nonrestorable_effects>, expected row count <deleteDbBeforeImageRowCount=exactKeyCount>, observed bytes initially <deleteDbBeforeImageObservedBytes=not_observed>, approved byte ceiling <deleteDbBeforeImageMaxBytes>, capacity evidence <deleteDbBeforeImageCapacityEvidenceId>, owner-only confidentiality class <deleteDbBeforeImageConfidentialityClass>, standard retention deadline <deleteDbBeforeImageRetainUntilUtc=deleteRecoverySnapshotRetainUntilUtc>, pre-authorized unresolved-outcome incident ceiling <deleteCommitUnknownEscrowRetainUntilUtc>, positive cleanup margin <deleteCommitUnknownEscrowDispositionMarginSeconds>, hard-delete-owned before-image cleanup <deleteDbBeforeImageCleanupTransactionId>/<deleteDbBeforeImageCleanupByUtc=min(deleteCommitUnknownEscrowRetainUntilUtc,targetDbBindingValidUntilUtc)>/<deleteDbBeforeImageCleanupState=not_started>/<deleteDbBeforeImageCleanupEvidenceId=not_triggered>, escrow state/evidence <deleteCommitUnknownEscrowState=not_active>/<deleteCommitUnknownEscrowEvidenceId=not_triggered>, disposition evidence <deleteDbBeforeImageDispositionEvidenceId or not_triggered>, and restore lifecycle <deleteDbRestoreApprovalId=not_issued>/<deleteDbRestoreApprovalState=not_issued>/<deleteDbRestoreExecuteByUtc=not_approved>/<deleteDbRestoreActiveUseExpiresAtUtc=not_approved>/<deleteDbRestoreReconcileByUtc=not_approved>/<deleteDbRestoreDispositionMarginSeconds=not_approved>/<deleteDbRestoreMutationId=not_created>/<deleteDbRestoreOutcomeState=not_created>/<deleteDbRestoreOutcomeEvidenceId=not_created>/<deleteDbRestoreCleanupTransactionId=not_created>/<deleteDbRestoreCleanupByUtc=not_approved>/<deleteDbRestoreCleanupState=not_created>/<deleteDbRestoreCleanupEvidenceId=not_triggered>. The target transaction must capture complete typed values for every column before DELETE, prove both DELETE and exact restore INSERT are limited to the selected direct rows with no secondary or externally observable effect while the bound DDL/schema fence is held, record exact observed bytes within the approved ceiling, and commit that before-image atomically with the DELETE and marker. Before mutation, <deleteDbBeforeImagePreparationReadiness=true> and <rollbackReadiness=false_pending_atomic_before_image>; rollbackReadiness may become true only inside that transaction after exact capture/revalidation succeeds. A committed marker without the exact recovery_available before-image is a permanent blocker, never success evidence.
I understand this delete has no app-level undo and exact recovery requires a separately approved restore transaction from that exact retained DB before-image while it remains valid; a source CSV snapshot, current source file, metadata signature, matching-key reparse, or re-transform cannot replace it. After a committed Delete, the source-provenance snapshot is awaiting_recovery_disposition, the DB before-image remains recovery_available, and both share the exact same standard retention deadline while coordinator/fence remain recovery_disposition_pending. A separate immutable single-use disposition approval may atomically authorize early accept_delete_and_dispose by claiming both distinct record-owned cleanup ids for committed or only the source cleanup id plus verified before-image not_created for aborted. A separately scoped restore approval creates its own distinct DB cleanup id and may authorize exact before-image restore_then_dispose; normal expiry cleanup may run only under both the source preflight approval and hard-delete approval that independently authorize their respective cleanup ids. If the marker is still nonterminal/missing/tampered at the standard deadline, the source cleanup disposes only the source snapshot and any existing target-side DB before-image key is destroyed as the image transitions to <deleteDbBeforeImageState=incident_keyless_cleanup_pending>; only authenticated keyless bytes/metadata remain in incident escrow at most until the absolute <deleteCommitUnknownEscrowRetainUntilUtc>, subject to earlier mandatory cleanup immediately after the incident reconcile cutoff. This is not rollback readiness, an inferred abort, or a deadline extension. If marker-first incident reconciliation later proves committed, standard recovery has already expired: restore is forbidden, only the authenticated image bindings/metadata may be matched to the marker, the keyless bytes are removed only through <deleteDbBeforeImageCleanupTransactionId>, and permanent recovery-loss/security-incident NO-GO is recorded. If it proves aborted, target-epoch-serialized proof that no before-image/key/bytes exist must atomically set <deleteDbBeforeImageCleanupState=not_applicable_aborted_incident> and publish <deleteDbBeforeImageCleanupEvidenceId>; any unexpected keyless image is treated as tamper, disposed only through that same hard-delete-owned cleanup id, and permanently blocks. If outcome is still unknown when <deleteCommitUnknownEscrowReconcileByUtc> closes, the pre-reserved <deleteDbBeforeImageCleanupTransactionId> must be claimed immediately and key-absence verification, authenticated byte removal, absence verification, and permanent NO-GO evidence must commit strictly before <deleteDbBeforeImageCleanupByUtc>; reaching that cleanup deadline incomplete is disposal_failed_blocked, not delayed cleanup authority. All unrelated or new mutations remain blocked until every cleanup lifecycle that applies is terminal.
Missing that cleanup deadline permanently forfeits success/restore/general target access, but the same pre-reserved cleanup id alone retains emergency authority to destroy the exact key, remove the exact before-image bytes, and verify absence until terminal disposed_permanent_block. It may not decrypt/read content, inspect marker/operational rows, create another cleanup, release any coordinator, or lift permanent NO-GO.
The incident-escrow marker-first reconcile deadline <deleteCommitUnknownEscrowReconcileByUtc> may apply only after escrow activation, is later than the normal <deleteReconcileByUtc>, and must satisfy <deleteCommitUnknownEscrowReconcileByUtc> <= min(<deleteCommitUnknownEscrowRetainUntilUtc>, <targetDbBindingValidUntilUtc>) - <deleteCommitUnknownEscrowDispositionMarginSeconds>. Because incident activation already destroyed any image key, the separately human-approved positive margin reserves time only for key-absence verification, authenticated byte removal, absence verification, and permanent-block evidence; equality with the final ceiling is forbidden. The final escrow ceiling must be strictly later than the standard recovery deadline; none of these deadlines may be inferred or extended.
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
- source-provenance and DB-before-image standard retention deadlines are exactly
  equal, the target binding remains valid through that shared deadline, and the
  hard-delete approval pre-reserves a strictly later bounded unresolved-outcome
  escrow ceiling/state/evidence contract that remains within the same exact-target
  binding validity;
- approval record exists in an approved storage location;
- `zipCreated=true`, trusted artifact checksum/full-file manifest, and time-bound
  installed/executing-tree evidence match the approval record;
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
  match; `deleteExecuteByUtc`, `deleteActiveUseExpiresAtUtc`, normal
  `deleteReconcileByUtc`, incident-only
  `deleteCommitUnknownEscrowReconcileByUtc`, and final
  `deleteCommitUnknownEscrowRetainUntilUtc` do not exceed that validity; positive
  `deleteCommitUnknownEscrowDispositionMarginSeconds` is bound; the
  positive `deleteMutationReconcileMarginSeconds` is bound and checked ordering
  proves claim deadline < active-use deadline <= normal reconcile deadline minus
  that margin; the normal reconcile deadline is no later than the equal standard retention
  boundary, while the incident reconcile deadline is later than normal only on
  escrow activation and no later than the earlier final ceiling minus that
  margin; the opaque DB
  binding resolves unexpired to the same authenticated
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
- package source commit/label, trusted artifact checksum/full-file manifest, and
  installed/executing-tree evidence/time;
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
  evidence plus normal delete reconcile, incident-escrow reconcile, and final
  escrow retention deadlines;
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
  approval, disposition state, and safe disposition evidence id, plus the
  preflight-owned source cleanup id/positive margin/deadline/state/evidence;
- protected DB before-image id/content/schema/column-set binding ids, exact row
  count, observed/approved-maximum bytes, capacity/confidentiality evidence, retention,
  lifecycle state, rollback-readiness transition, restore approval/mutation/
  outcome evidence, active-use/reconcile deadlines, disposition margin when
  applicable, safe disposition evidence, hard-delete-owned cleanup id/normal
  positive margin/normal deadline/incident deadline/selected branch state/
  evidence, and any distinct restore-owned cleanup id/deadline/state/evidence;
- hard-Delete claim deadline, active-use commit deadline, positive mutation-to-
  reconcile margin, target-clock commit result, and target-side epoch/fence
  acquisition/advance evidence;
- unresolved-outcome escrow reconcile deadline, positive cleanup margin, final
  retention ceiling, state/evidence, and permanent incident/NO-GO result when the standard retention
  boundary was reached without an authoritative marker;
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
- after and only after `commit_unknown_retention_incident_blocked` activation,
  the same marker-first endpoint under the pre-reserved incident entitlement,
  only before `deleteCommitUnknownEscrowReconcileByUtc`,
  `deleteCommitUnknownEscrowRetainUntilUtc`, and
  `targetDbBindingValidUntilUtc`; it may read only the bound marker and recovery-
  record identity/state needed to prove committed+matching-before-image or
  authoritative aborted, and may not perform any row query or mutation;
- preserving audit, DB delta, and row attribution evidence;
- documenting the failure and next stop condition.

Before normal reconcile can publish authoritative abort, it must wait until
`deleteActiveUseExpiresAtUtc`, lock the same target-side coordinator epoch row as
the DELETE transaction, and atomically advance the action epoch/fence. The lock
serializes with any old transaction: a DELETE that wins must already have
committed strictly before the deadline with its marker/before-image; otherwise
the old transaction loses its conditional epoch check and rolls back before the
prepared marker becomes aborted. Incident activation and every recovery-store
cleanup claim repeat that same epoch serialization. No cleanup may certify
absence while an old-epoch transaction can still commit.

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

If that unresolved marker reaches the standard retention deadline, atomically
enter `commit_unknown_retention_incident_blocked`: fence every worker, end source
access and claim its cleanup under the preflight approval, transition the DB
cleanup from `not_started` to `incident_locked`, destroy any existing before-image
decryption key, transition that image from `recovery_available` to
`incident_keyless_cleanup_pending`, and retain only authenticated keyless bytes/
metadata as incident escrow under
the hard-delete approval's pre-reserved
`deleteCommitUnknownEscrowRetainUntilUtc`, and preserve the same coordinator/
fence owner. The escrow permits marker-first outcome reconciliation only; it is
not rollback readiness, outcome proof, or mutation approval. That read requires
the separate pre-reserved `deleteCommitUnknownEscrowReconcileByUtc` and exact-
target revalidation; after that deadline no marker or operational-row DB read is
allowed. The only permitted target-store access is the pre-authorized idempotent
DB-before-image-only incident cleanup transaction bound to
`deleteDbBeforeImageCleanupTransactionId`, exact before-image/owner/generations,
and terminal evidence: it verifies the key is already absent (or destroys it
idempotently), removes only those
bytes, verifies absence, and cannot read/write the marker or `all_metrics`. A
committed marker plus matching authenticated image bindings/metadata in
`incident_keyless_cleanup_pending` moves escrow to
`resolved_committed_disposition_pending`; ordinary disposition and restore are
not legal because the equal standard source/before-image retention has expired.
The hard-delete approval's incident-cleanup authority must CAS
`incident_locked -> claimed_incident`, verify key absence, remove bytes, publish
`disposed_permanent_block`, and
keep the target-global coordinator permanently `commit_unknown_blocked` with
recovery-loss/security-incident NO-GO. An aborted marker moves to
`resolved_aborted` only when target-epoch-serialized absence proof atomically CASes
`incident_locked -> not_applicable_aborted_incident` and publishes the exact DB-
cleanup absence evidence. That resolution must wait
until `deleteSourceSnapshotCleanupState=committed`, exact source-cleanup evidence
is durable, and no applicable cleanup remains active; cleanup failure keeps every
coordinator blocked. Only then may one atomic terminal join set target DB binding
and both chain branches `invalid`, chain fence `invalid`, target-global
coordinator `invalidated_terminal`, empty target consumers, commit resolution/
audit/disposition evidence, and release the machine-global operation coordinator
to `idle` with empty owner/consumer and an advanced generation. A fresh Preview
may claim only after that join. An unexpected keyless image is a tamper incident
and follows the same permanent-block disposal. If outcome remains unknown when
`deleteCommitUnknownEscrowReconcileByUtc` closes, immediately claim the pre-
reserved hard-delete-owned DB-before-image cleanup as `claimed_incident` and complete key-absence
verification, byte removal, and permanent block strictly before `deleteDbBeforeImageCleanupByUtc`; no further marker or
  operational-row read is allowed. Reaching that cleanup deadline without a
  committed cleanup becomes `disposal_failed_blocked` and alerts as a security
  incident. It permits only the same pre-reserved cleanup id to destroy the key,
  remove the exact bytes, and verify absence until `disposed_permanent_block`;
  decryption/content read, marker/operational-row access, restore, new cleanup id,
  coordinator release/generation, or any other action remains permanently
  forbidden. Neither
deadline may be extended after approval.

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

Normal automatic retention-expiry authority is split by record and may never be
inherited across approvals. The original consumed preflight approval authorizes
expiry access revocation plus cleanup only of its source-provenance snapshot. The consumed hard-delete
approval separately authorizes expiry disposal only of the DB before-image it
pre-reserved and created, with exact id/content/schema/column/side-effect/marker/
target/coordinator bindings. A marker-proven committed Delete uses one CAS-bound
dual-record expiry close at the equal standard access deadline: it irreversibly
revokes source and DB-before-image decryption/recovery access, claims the source
cleanup and `deleteDbBeforeImageCleanupState=claimed_normal` under their distinct
approvals, then completes each strictly before its own positive-margin cleanup
deadline. A marker-proven aborted Delete claims only the source cleanup id under
the preflight approval and proves the DB image remains `not_created`. A still-
unresolved marker instead revokes source access/claims source cleanup and
atomically selects DB cleanup `incident_locked` and any existing before-image
`incident_keyless_cleanup_pending`; it may not use the normal DB cleanup
deadline, while a known terminal outcome may not select the incident deadline.
Each path fences an
early-disposition or restore claimant, and coordinator release waits for the
terminal join of all records that actually exist. The only exception is the
pre-authorized unresolved-outcome incident transition above: it irreversibly
ends source access and claims its cleanup at the standard deadline, completing
key-first source-byte removal before the source cleanup deadline, and transitions
any existing target-side image to non-recoverable
`incident_keyless_cleanup_pending` under the
same epoch CAS while it quarantines the authenticated bytes/metadata
before-image only through the incident marker-read window. A committed proof or
the incident reconcile cutoff immediately CASes `incident_locked -> claimed_incident`
for the hard-delete-owned DB cleanup,
which must finish strictly before `deleteDbBeforeImageCleanupByUtc` and the later
escrow/target ceilings, without releasing the coordinator or enabling mutation.
A restore requires its own separately scoped mutation approval, uses only the
exact DB before-image, restores and verifies every typed column under the bound
schema/column policy in one transaction, and is not authorized by this document.
Deterministic cleanup tests must crash/restart before and after approval claim,
key destruction, byte removal, absence verification, coordinator/fence terminal
CAS, and evidence publication. Recovery returns/publishes only the same terminal
result; it never restores a destroyed key, repeats a different cleanup, releases
the coordinator before verified removal, or loses the safe evidence record.
Source-cleanup tests use an injected clock immediately before, exactly at, and
after `deleteRecoverySnapshotRetainUntilUtc` and
`deleteSourceSnapshotCleanupByUtc`; they prove access remains available before
retention, is irreversibly revoked and cleanup claimed at retention, no decrypt/
recovery read occurs during the margin, cleanup commits strictly before its
deadline, and equality/late completion becomes `disposal_failed_blocked`.
Numeric tests reject zero, negative, non-integer, coercion, maximum-plus-one,
checked-addition overflow, and inferred source cleanup margins.
Normal DB-before-image cleanup tests use an injected authoritative target clock
immediately before, exactly at, and after `deleteDbBeforeImageRetainUntilUtc` and
`deleteDbBeforeImageNormalCleanupByUtc`. They prove marker-proven committed
atomically revokes access and selects `claimed_normal`, marker-proven aborted
requires `not_created`, unresolved selects only cleanup `incident_locked` plus
image `incident_keyless_cleanup_pending`, and early
`claimed_early` excludes both. They race duplicate/replay/response-loss/crash
before and after branch CAS, key destruction, byte removal, absence verification,
and evidence publication; only one branch/deadline wins. Equality/late normal
cleanup becomes `disposal_failed_blocked`. Numeric tests reject zero, negative,
non-integer, coercion, maximum-plus-one, checked-addition overflow, target-validity
overrun, and inferred normal DB cleanup margins, while accepting one and the
fixed maximum only when all checked ordering remains valid.
They must combine process death immediately before DB-before-image key destruction
with restart at and after `deleteDbBeforeImageCleanupByUtc`: the state becomes
`disposal_failed_blocked`, only the same cleanup id can resume, the key is
eventually destroyed and exact bytes removed/absence-verified, terminal state is
`disposed_permanent_block`, and permanent NO-GO/coordinator blocking never lifts.
They must also cover a marker that remains missing, tampered, or `prepared`
immediately before/at/after the standard access deadline; atomic source access
revocation plus exact source-cleanup claim and incident-escrow activation,
followed by source cleanup strictly before its later deadline; incident marker-first read immediately before/at/
  after its distinct reconcile deadline; zero marker/operational-row reads after that deadline;
  committed/aborted resolution during escrow, including reconcile before/after
  source cleanup commit and proof that aborted resolution cannot terminal-join or
  release any coordinator until source cleanup state/evidence is committed;
  the absent branch must CAS `incident_locked -> not_applicable_aborted_incident`
  with durable target-epoch evidence, while an unexpected image races only into
  `claimed_incident` permanent-block cleanup; crash/response loss returns the same
  branch/evidence and source cleanup failure remains permanently blocked; immediate approval-bound permanent-
  block disposal after committed proof; proof that no ordinary disposition or
  restore approval can consume an expired/non-recoverable incident record; immediate
  unknown-outcome cleanup claim after reconcile cutoff, key-absence verification/
  byte-removal completion
  strictly before the cleanup/escrow/target ceiling, cleanup-deadline failure, and races with
new Preview/Start/Retry/Delete/restore/disposition. No path may infer abort,
release the coordinator or extend either deadline. A committed proof triggers
immediate permanent-block disposal; an outcome still unknown at reconcile cutoff
also triggers the exact cleanup, without inference, during the reserved margin.
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
committed dual-record and aborted source-only early/expiry disposition, equal
standard recovery-access-deadline enforcement with distinct record-owned cleanup
deadlines, mismatch rejection, crash/response loss, replay,
early-versus-expiry races, cleanup failure, and proof that an aborted path neither
fabricates nor requires a DB before-image. They must substitute and cross-claim
all three cleanup-id classes, proving a source cleanup can never delete a DB
before-image, a hard-delete incident cleanup can never delete source bytes or a
restore-owned record, and a restore cleanup can never consume either original
approval's lifecycle. They must race `claimed_early` against standard-expiry
`claimed_normal`/`incident_locked`, prove exactly one CAS branch wins, return the
same record after response loss, and prove aborted early disposition never moves
the DB cleanup from `not_started`. Restore commit/abort/unknown races must prove the Delete-
owned DB cleanup becomes `superseded_by_restore_cleanup` only on authoritative
commit or restore-unknown terminal cleanup, remains unconsumed on authoritative abort, and
that each retained record has exactly one terminal cleanup evidence id.

Required early-disposition approval wording, issued only after human review of a
terminal marker-proven Delete outcome:

```text
TEMPLATE STATUS: NOT AUTHORIZATION. Do not fill, sign, or execute this block until production code and deterministic tests implement every prerequisite for this action and a new human approval explicitly releases this gate.
The Delete recovery disposition approval id is <deleteRecoveryDispositionApprovalId>, initially available and claimable only by <deleteRecoveryDispositionExecuteByUtc>, no later than the minimum retention deadline of every recovery record that exists.
For a committed Delete, the joint early-disposition claim must CAS the hard-delete-owned DB cleanup from <deleteDbBeforeImageCleanupState=not_started> to <deleteDbBeforeImageCleanupState=claimed_early>; for aborted, it must leave that state `not_started` while proving the before-image `not_created`. `claimed_normal`, `incident_locked`, and `claimed_incident` are forbidden before standard expiry and cannot satisfy this approval.
I approve exactly one early accept_delete_and_dispose action for source-provenance snapshot <deleteRecoverySnapshotId>/<deleteRecoveryContentBindingId>, retained only until <deleteRecoverySnapshotRetainUntilUtc>, from Delete mutation <deleteMutationId> in authoritative terminal outcome <deleteMutationOutcomeState> with evidence <deleteMutationOutcomeEvidenceId>. If that outcome is committed, this approval also binds exact DB before-image <deleteDbBeforeImageId>/<deleteDbBeforeImageContentBindingId>/<deleteDbBeforeImageSchemaBindingId>/<deleteDbBeforeImageColumnSetBindingId>/<deleteDbMutationSideEffectBindingId>, state recovery_available, retained until the same exact deadline <deleteDbBeforeImageRetainUntilUtc=deleteRecoverySnapshotRetainUntilUtc>. If that outcome is aborted, it instead requires <deleteDbBeforeImageState=not_created>, authorizes source-only disposition, and does not authorize restore or any DB-before-image disposition.
It binds exact-target coordinator/fence <targetGlobalCoordinatorId>/<targetOperationFenceId>, exact owner/consumer/generations/evidence <targetGlobalCoordinatorOwnerFenceId>/<targetGlobalCoordinatorConsumer>/<targetGlobalCoordinatorGeneration>/<targetGlobalCoordinatorEvidenceId>/<targetOperationFenceGeneration>/<targetOperationFenceEvidenceId>, named approver <approver>, and named executor <executor>.
The cleanup action must atomically claim this approval and the exact cleanup lifecycles owned by the records that exist. A committed Delete claims <deleteSourceSnapshotCleanupTransactionId> and <deleteDbBeforeImageCleanupTransactionId> together; an aborted Delete claims only <deleteSourceSnapshotCleanupTransactionId> and proves <deleteDbBeforeImageState=not_created> without claiming, creating, or consuming any DB cleanup. It destroys each claimed record key first, removes and verifies absence of only that record's bytes, publishes exactly one <deleteSourceSnapshotCleanupEvidenceId>, <deleteRecoveryDispositionEvidenceId> and, only for committed, <deleteDbBeforeImageCleanupEvidenceId>/<deleteDbBeforeImageDispositionEvidenceId>, then finishes consumed with the claimed cleanup state(s)=committed. Response loss returns only that same per-record evidence; mismatch/expiry/concurrent/replay claim performs no early disposition and finishes invalid only if no cleanup committed.
This approval authorizes only the protected recovery-record state transitions, key destruction, byte removal, verification, and safe disposition-evidence write above. It does not authorize restore, Preview, Start Upload, Retry Failed, Delete, unrelated operational-table DB read/write, source access/mutation, Settings save, runtime lifecycle, reset, cleanup outside these exact records, LAN, or deployment.
```

Required separately scoped restore approval wording, issued only after human
review of a committed Delete marker and its exact `recovery_available` before-
image:

```text
TEMPLATE STATUS: NOT AUTHORIZATION. Do not fill, sign, or execute this block until production code and deterministic tests implement every prerequisite for this action and a new human approval explicitly releases this gate.
The DB before-image restore approval id is <deleteDbRestoreApprovalId>, initially available and claimable exactly once by <deleteDbRestoreExecuteByUtc>; the pre-reserved restore mutation id is <deleteDbRestoreMutationId> and this approval creates the distinct restore-owned before-image cleanup <deleteDbRestoreCleanupTransactionId>/<deleteDbRestoreCleanupByUtc>/<deleteDbRestoreCleanupState=not_started>/<deleteDbRestoreCleanupEvidenceId=not_triggered>. The preflight-owned source cleanup remains <deleteSourceSnapshotCleanupTransactionId>/<deleteSourceSnapshotCleanupState=not_started> and the hard-delete-owned DB cleanup remains <deleteDbBeforeImageCleanupTransactionId>/<deleteDbBeforeImageCleanupState=not_started>; neither is interchangeable with the restore-owned id. Its unrenewable active-use commit deadline is <deleteDbRestoreActiveUseExpiresAtUtc>, marker-first read-only reconcile/equality deadline is <deleteDbRestoreReconcileByUtc>, and protected disposition margin is <deleteDbRestoreDispositionMarginSeconds>. The ordering must be deleteDbRestoreExecuteByUtc <= deleteDbRestoreActiveUseExpiresAtUtc < deleteDbRestoreReconcileByUtc < deleteDbRestoreCleanupByUtc <= min(targetDbBindingValidUntilUtc, deleteDbBeforeImageRetainUntilUtc), with at least that positive margin after reconcile. I approve mandatory key-first disposal of both retained records by their deadlines if marker-first restore outcome remains unknown at the reconcile deadline: the source cleanup may touch only the source snapshot and the restore-owned cleanup may touch only the exact DB before-image. That terminal path performs no marker or operational-row DB read/write, records <deleteSourceSnapshotCleanupState=committed>/<deleteSourceSnapshotCleanupEvidenceId> and <deleteDbRestoreCleanupState=committed>/<deleteDbRestoreCleanupEvidenceId>, atomically marks <deleteDbBeforeImageCleanupState=superseded_by_restore_cleanup>, records <deleteDbRestoreOutcomeState=unknown_disposed_permanent_block>, and publishes permanent recovery-loss/security-incident NO-GO. It is not an inferred abort or permission to retry. An authoritative aborted restore instead records <deleteDbRestoreCleanupState=not_applicable_aborted>, leaves both original cleanup lifecycles unconsumed, and permits no cleanup under this approval.
I approve exactly one restore_then_dispose transaction for Delete mutation <deleteMutationId> with committed evidence <deleteMutationOutcomeEvidenceId>, exact DB before-image <deleteDbBeforeImageId>/<deleteDbBeforeImageContentBindingId>/<deleteDbBeforeImageSchemaBindingId>/<deleteDbBeforeImageColumnSetBindingId>, row count <deleteDbBeforeImageRowCount>, retention <deleteDbBeforeImageRetainUntilUtc>, and original source-provenance snapshot <deleteRecoverySnapshotId>/<deleteRecoveryContentBindingId>.
It binds the same verified baseline <trustedTargetBaselineId>/<trustedTargetBaselineEvidenceId>, exact target <targetDbBindingId> valid until <targetDbBindingValidUntilUtc>, mutation-schema fence <deleteDbMutationSchemaFenceBindingId> and side-effect binding/readiness <deleteDbMutationSideEffectBindingId>/<deleteDbMutationSideEffectReadiness=direct_rows_only_no_unmodeled_or_nonrestorable_effects> for both DELETE and INSERT, target-global coordinator/fence <targetGlobalCoordinatorId>/<targetOperationFenceId> in recovery_disposition_pending with exact owner/consumers/generations/evidence, named approver <approver>, named executor <executor>, and restore evidence location <evidenceReportLocation>.
Before approval claim, prepared-marker creation, authoritative restore transaction, marker-first reconciliation, equality publication, and disposition claim, revalidate the applicable lease/deadline with the authoritative target clock. After the local approval/image/consumer claim and before any INSERT, a separate authoritative target transaction must durably create exactly one `prepared` restore marker under <deleteDbRestoreMutationId>, binding the approval/image/schema-fence/side-effect/target/coordinator/lease fields. It CAS-checks the same owner/generations and current time before <deleteDbRestoreActiveUseExpiresAtUtc>; duplicate or response-lost creation returns only that marker. The later authoritative restore transaction must lock this already committed `prepared` marker, then acquire and hold the exact engine-appropriate DDL-conflicting relation/catalog locks or enforced schema-generation fence through commit. Only then may it revalidate schema/INSERT-side-effect bindings, lock the exact keyset, require every selected target key still absent, and prove all INSERT side-effect classes remain absent/inert. It inserts every typed column from the protected before-image without overwrite, verifies exact row/column equality, and commits inserts plus marker transition `prepared -> committed` atomically only while current target time is strictly before <deleteDbRestoreActiveUseExpiresAtUtc>. Crossing that deadline rolls back every restore write and leaves the durable marker `prepared` for guarded abort/reconcile. Any unfenced DDL/configuration window, present key, schema/column/side-effect mismatch, secondary/external effect, missing/tampered/expired before-image, identity drift, overflow, concurrent writer, or verification failure also rolls back every restore write. Timeout or response loss becomes commit_unknown_blocked; after active-use expiry, marker-first read-only reconciliation may resolve an already committed marker only by <deleteDbRestoreReconcileByUtc> and may issue no restore write. Current row presence cannot infer outcome.
Only after committed restore and exact equality evidence may the same owner/generation atomically mark the hard-delete-owned DB cleanup `superseded_by_restore_cleanup`, claim the preflight-owned source cleanup and restore-owned DB cleanup, enter key-first verified disposition for both retained records, and publish <deleteDbRestoreOutcomeEvidenceId>, <deleteSourceSnapshotCleanupEvidenceId>, <deleteDbRestoreCleanupEvidenceId>, <deleteDbBeforeImageDispositionEvidenceId>, and <deleteRecoveryDispositionEvidenceId>. No cleanup id may address the other record. Disposal failure keeps the coordinator blocked. This approval does not authorize a new Delete, overwrite/upsert, Preview, Start Upload, Retry Failed, source access/mutation, Settings save, runtime lifecycle, reset, unrelated cleanup, LAN, or deployment.
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
| Reconcile deadline expires without authoritative terminal marker | `consumed` | `restoring -> disposed` only through the approval-bound hard-deadline cleanups | outcome `unknown_disposed_permanent_block`; consumers remain `delete_restore`, while target-global coordinator remains permanently `commit_unknown_blocked` | Issue no further marker or operational-row DB read/write. Atomically supersede the Delete-owned DB cleanup, then claim `deleteSourceSnapshotCleanupTransactionId` for only the source snapshot and `deleteDbRestoreCleanupTransactionId` for only the exact before-image. Each destroys its own key first, removes only its bytes, verifies absence, and publishes its distinct terminal evidence; neither may inspect/infer outcome or touch `all_metrics`. Cleanup failure remains `disposal_failed_blocked`; no retry/new approval/new mutation/new coordinator generation is allowed. |
| Equality verified and applicable disposal commits | `consumed` | `restored -> disposed` | outcome `committed`; consumers `delete_restore -> delete_disposition -> empty`, coordinator/fence terminal | Key-first verified disposal and safe evidence close every retained record exactly once. |

Deterministic tests must cover every row above, including crash/restart and
response loss after local claim but before marker creation, before/after durable
`prepared` commit, before/after marker lock, INSERT/equality/`prepared -> committed`
commit, consumer-generation, and disposition publication. They must race delayed
prepared creation/restore against guarded `aborted` marker creation and prove only
one terminal marker wins. Authoritative abort must restore only the intact before-
image lifecycle state, consume the attempted approval permanently, and require a
fresh approval without reopening the operational source.
Tests must also exercise just-before/at/after restore reconcile and retention
deadlines when the marker remains unknown, crash/restart before and after key
destruction, byte removal, and terminal evidence publication, and cleanup
failure. They must prove zero post-deadline marker/operational-row DB reads/writes,
and exactly one idempotent approval-bound cleanup per retained record, using the
source-snapshot id for only source bytes and the restore-owned DB id for only the
before-image, with key-first removal/absence verification, no outcome inference,
no restoration of a destroyed key, response-loss recovery of only the same
terminal record, and permanent coordinator non-advanceability.

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
  exact target through the fixed authenticated machine-global authority and
  ACL-restricted cross-session mutex, independent of Windows user, installation,
  package, and `EWC_STATE_DB_PATH`; every mutating target transaction also checks
  the same target-side mutation epoch, and every action/marker/reconcile CAS-
  checks owner, consumer, generation, and evidence without overlap or stale
  publication;
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
- hard Delete uses the human-bound non-renewable active-use deadline and positive
  reconcile margin; the authoritative target clock and shared target-side epoch
  row make every at/after-deadline DELETE roll back, while normal reconcile,
  incident activation, and cleanup serialize/advance that epoch before declaring
  abort or absence. Tests delay a prepared transaction across active-use expiry,
  standard retention, incident reconcile cutoff, and cleanup commit, and prove it
  can never commit after the fencing transition;
- the protected mutation-side-effect binding proves both exact DELETE and restore
  INSERT are direct selected-row-only operations with no secondary affected
  relation or externally observable effect; deterministic tests concurrently
  install or drift
  DELETE- and INSERT-specific foreign-key cascades, triggers, rules, RLS/policies,
  generated/default expressions, sequences, replication/publication/CDC hooks,
  and notifications and prove zero writes unless every class is absent or inert;
- committed and aborted outcomes have distinct recovery closes, source and DB
  before-image standard retention deadlines are equal when both records exist, preflight
  and hard-delete approvals independently authorize only their own expiry
  disposal through distinct source/DB cleanup ids, a later restore uses its own
  cleanup id and can supersede the Delete-owned DB cleanup only after an
  authoritative committed/unknown restore while abort leaves it unconsumed, and
  coordinator release occurs only after the terminal join of all
  records that actually exist; an incident-time aborted resolution additionally
  records `not_applicable_aborted_incident` plus authoritative absence evidence,
  waits for committed source cleanup and durable evidence, and cleanup failure
  never releases a coordinator; unresolved outcome at the standard deadline
  activates the pre-authorized bounded incident escrow, ends source access and
  claims source cleanup for completion within its positive margin,
  never infers abort, and after marker-proven committed resolution performs only
  approval-bound before-image disposal plus permanent incident/NO-GO (no ordinary
  restore/disposition), or immediately claims the same permanent-block cleanup at
  the incident reconcile cutoff if still unknown and commits strictly before
  `deleteDbBeforeImageCleanupByUtc`; injected-clock tests cover immediately before,
  exactly at, and after incident-reconcile and cleanup-commit boundaries, while
  the later escrow/target ceiling proves no readable retained material or authority remains, and
  race the last allowed marker read against key-absence verification/byte cleanup, proving the
  positive disposition margin prevents overlap. Numeric tests reject non-integer,
  negative, zero, maximum-plus-one, coercion, checked-subtraction underflow, and
  impossible ordering; they accept one and the exact fixed maximum only when all
  deadlines remain valid, and every rejected approval creates zero DB writes;
- a known committed DB before-image loses decryption/restore access and selects
  `claimed_normal` exactly at standard expiry, then completes strictly before its
  positive-margin normal cleanup deadline within target validity; a known aborted
  outcome has no image, unresolved selects cleanup `incident_locked` plus image
  `incident_keyless_cleanup_pending`, early uses
  `claimed_early`, and deterministic branch/deadline/crash tests prove exactly one
  path and terminal evidence;
- restore claim/commit/authoritative-abort/commit-unknown/reconcile transitions
  follow the exact approval, before-image, outcome, consumer, and generation table;
  an aborted attempt consumes its approval and requires a new approval, while an
  unresolved restore marker can never regress from `restoring` or expose a new
  mutation; at its approval-bound hard deadline it must dispose key-first with
  `unknown_disposed_permanent_block` or remain `disposal_failed_blocked`;
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
  approved protected authority, or committed Markdown/request text is accepted
  as runtime approval authority;
- the protected approval lifecycle in `docs/164` is absent/untested, the approval
  is not `available` before claim, the claim and one-run binding are non-atomic,
  a duplicate/concurrent request could create another run, or a committed run's
  approval could return to `available`/`invalid`;
- `zipCreated` is not true, trusted artifact checksum/full-file manifest/
  installed-tree/executing-tree evidence is missing or stale, verification
  observation/expiry/integrity-lock evidence is missing/inferred/expired, the
  OS-enforced read-only ACL or exclusive machine-global lock cannot be held
  through the stage, or any governed file/dependency/build-info/execution root
  differs or changes after admission;
- `approvalContractRevision` differs from `docs164-2026-08-17-r1`, or release
  trust-root/signer/algorithm/revocation/independent-verifier evidence is missing,
  candidate-controlled, self-attested, revoked, substituted, or stale;
- DB target class or diagnostic fingerprint differs, the protected exact DB
  binding is missing/unresolvable/substituted, or authoritative instance/
  database identity differs from the preflight approval/result or delete
  approval/run/reconcile binding;
- the singleton target-global coordinator id/state/owner/consumer/generation/
  evidence is missing, substituted, stale, overlaps another Preview/action, or
  is not atomically claimed with preflight/Delete/marker/reconcile;
- the coordinator is scoped to a user-profile/app-state DB, changes with Windows
  user/package/install/`EWC_STATE_DB_PATH`, lacks the fixed authenticated machine-
  global authority or ACL-restricted cross-session mutex, the single-PC/local-
  target invariant is not proved, or the Delete/restore transaction does not
  enforce the same target-side mutation epoch;
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
- `deleteActiveUseExpiresAtUtc` or positive
  `deleteMutationReconcileMarginSeconds` is missing/inferred/invalid/renewed, the
  checked claim<active-use<=reconcile-minus-margin ordering fails, the target
  transaction can commit at/after active-use expiry, or reconcile/incident/
  cleanup does not serialize and advance the same target-side epoch before
  authoritative abort/absence publication;
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
- the preflight-owned source-snapshot, hard-delete-owned DB-before-image, and
  restore-owned cleanup ids/deadlines/states/evidence are missing, substituted,
  shared, cross-claimed, or can remove another record class; an incident-time
  aborted resolution can terminal-join/release before source cleanup is committed
  with durable evidence, or a failed source cleanup releases any coordinator; an aborted Delete
  consumes/creates DB cleanup, an aborted restore consumes either original
  cleanup, or a committed/unknown restore fails to atomically supersede the
  Delete-owned DB cleanup before its distinct restore cleanup becomes active;
- source recovery access remains available at/after
  `deleteRecoverySnapshotRetainUntilUtc`, its positive human-approved cleanup
  margin/deadline is missing/inferred/invalid/overflowed, cleanup is not claimed
  at access expiry, byte removal/evidence can commit at/after
  `deleteSourceSnapshotCleanupByUtc`, or cleanup starts only when that later hard
  deadline has already arrived;
- DB-before-image recovery/decryption access remains available at/after
  `deleteDbBeforeImageRetainUntilUtc` for a known terminal outcome, positive
  `deleteDbBeforeImageNormalCleanupMarginSeconds` or checked
  `deleteDbBeforeImageNormalCleanupByUtc` is missing/inferred/invalid/overflowed/
  beyond target validity, marker-proven committed fails to select
  `claimed_normal`, unresolved fails to select cleanup `incident_locked` and any
  existing image `incident_keyless_cleanup_pending`, early cleanup
  does not use `claimed_early`, more than one branch wins, or normal byte removal/
  evidence commits at/after its normal deadline;
- the hard-delete approval lacks the non-extendable unresolved-outcome incident-
  escrow ceiling/positive cleanup margin/state/evidence, its incident reconcile
  deadline is later than the earlier final ceiling minus that margin, a standard-
  deadline unknown outcome fails to destroy any existing image key, removes the
  authenticated keyless bytes/metadata before marker-proven committed resolution
  or reconcile cutoff, removes them afterward outside the bound cleanup, or
  retains readable source bytes, escrow permits
  any action other than marker-first reconcile and approval-bound incident
  cleanup, a post-standard-retention committed proof can enter ordinary restore/
  disposition instead of permanent-block cleanup, or committed/unknown outcome
  fails to claim cleanup immediately at proof/reconcile cutoff and finish key-
  absence verification plus byte removal before `deleteDbBeforeImageCleanupByUtc` with permanent recovery-loss/
  security-incident NO-GO;
- restore claim/marker/transaction/reconciliation/equality/disposition does not
  recheck both target-binding and DB-before-image validity with the authoritative
  target clock, lacks the ordered unrenewable active-use/reconcile/deadline margin,
  commits at/after active-use expiry, lets post-lease reconcile issue restore
  writes, or an expiry race can write, release, retry, or discard retained evidence;
- restore claim/commit/abort/unknown state does not match the exact lifecycle
  table, an aborted attempt reuses its consumed approval, an intact before-image
  cannot return to `recovery_available` with atomically advanced generations, or
  `commit_unknown_blocked` can release/retry, or a still-unknown restore lacks
  approval-bound hard-deadline key-first disposal plus terminal permanent NO-GO;
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
