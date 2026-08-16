# V1 Cutover Read-Only Inventory Evidence

## Status

```text
read_only_inventory_human_confirmed_preview_not_approved_no_data_mutation
```

## Summary

- Evidence date: 2026-08-15 Asia/Seoul
- Inventory record id: `inv_20260815T031829Z_0d41338f`
- Inventory observation: `completed`
- Human reviewer class: `human_operator`
- Human review status: `confirmed`
- Preview approval: `not_approved`
- Upload Preview executions: `0`
- Operational DB queries or mutations: `0`
- Source mutations: `0`
- Final decision: `blocked`

This is a filled, sanitized read-only inventory evidence record for the V1
cutover gate. It is not an approval template and does not authorize Upload
Preview, Start Upload, Retry Failed, Delete, Settings save, runtime lifecycle,
Supabase or Docker lifecycle, LAN, deployment, migration, reset, cleanup, or
any source or database mutation.

## Package Binding

| Field | Recorded value |
| --- | --- |
| `packageSourceCommit` | `d16b822d4a461fc7705c5aca9cebd40cb19fe918` |
| `packageLabel` | `ExtrusionWebConsole-d16b822-20260815-030206-082` |
| `zipSha256` | `1e5416072511daeb884e4be7be3f257e7b00377fb9614df53c8c6df67129a83c` |
| Runtime mode | `operator-ready` |
| Frontend mode | `api` |
| Package installation or execution | not performed by this record |

The package label, source commit, and ZIP hash identify the artifact to which
this inventory is bound. They do not prove that this artifact is installed or
currently executing on the operator PC.

## Inventory Result

| Field | Recorded value |
| --- | --- |
| `inventoryEvidenceRecordId` | `inv_20260815T031829Z_0d41338f` |
| `inventoryObservedAtUtc` | `2026-08-15T03:18:29.4209312Z` |
| `sourceKind` | `plc` |
| `sourceScope` | `folder_all` |
| `sourceOriginClass` | `operator_config` |
| `sourceClass` | `drive_letter` |
| `sourceAlias` | `human_input_required_before_preview_approval` |
| `operatorPcClass` | `human_input_required_before_preview_approval` |
| `inventoryObservedFiles` | `12` |
| `inventoryObservedPhysicalDataLines` | `3451430` |
| `inventoryApprovedPhysicalRowsCeiling` | `3451430` |
| Stable files | `12` |
| Unstable files | `0` |
| Non-CSV files in the direct scope | `0` |
| Read errors | `0` |
| Files changed during read | `0` |
| Scope changed during inventory | `false` |
| `inventoryEvidenceBinding` | `inventoryEvidenceRecordId` |

The physical data-line count is the sum of physical file lines after removing
one header line from each non-empty CSV. The counter includes a final
non-empty line even when a file has no terminal newline. It is not a
transformed exact-key count, Preview target-row count, database match count, or
database row count.

An EOF-aware review recount at `2026-08-15T03:41:14.0385877Z` observed the same
12 files and 3,451,430 physical data lines, with zero files lacking a terminal
newline, zero read errors, and zero files changed during that recount.

## Human Confirmation

The human operator confirmed the following bounded values after the read-only
observation:

```text
inventoryObservedFiles = 12
inventoryApprovedPhysicalRowsCeiling = 3451430
Preview execution is not approved.
```

The reviewer is recorded as the sanitized role class `human_operator`; no
personal identifier is stored in this repository record.

The operator PC class and a privacy-safe alias for the exact configured source
folder were not supplied by the human and are not inferred here. Both missing
values are hard stops before any Preview-only approval may be issued. They are
downstream of the additional atomic-binding implementation/test and rebuilt-
package gate described below. The future alias must be random or otherwise
resistant to path guessing, and the human must confirm out of band that it maps
to the exact configured folder.

## Required Evidence Fields

| Field | Current value |
| --- | --- |
| `previewApprovalId` | `not_approved` |
| `previewApprovalState` | `not_approved` |
| `manifestPreparationApprovalId` | `not_approved` |
| `manifestPreparationApprovalState` | `not_approved` |
| `manifestPreparationExecuteByUtc` | `not_approved` |
| `contentManifestRecordId` | `not_created` |
| `contentManifestPreparedAtUtc` | `not_created` |
| `contentManifestExecuteByUtc` | `not_created` |
| `contentManifestState` | `not_created` |
| `contentSnapshotRecordId` | `not_created` |
| `contentSnapshotState` | `not_created` |
| `inventoryObservedBytes` | `not_observed` |
| `contentSnapshotMaxBytes` | `not_approved` |
| `contentSnapshotRetainUntilUtc` | `not_approved` |
| `contentSnapshotDispositionState` | `not_created` |
| `snapshotDispositionEvidenceId` | `not_created` |
| `atomicSnapshotBindingEvidenceId` | `not_created` |
| `previewRunId` | `not_run` |
| `previewStatus` | `not_run` |
| `previewTargetRows` | `not_observed` |
| `previewPartialOverlapRows` | `not_observed` |
| `previewRiskyCount` | `not_observed` |
| `dbStatusClass` | `not_queried` |
| `targetClassStatus` | `not_observed` |
| `runtimeReadinessClass` | `not_observed` |
| `trustedTargetBaselineId` | `not_provisioned` |
| `trustedTargetAlias` | `not_provisioned` |
| `trustedTargetBaselineState` | `not_provisioned` |
| `trustedTargetBaselineEvidenceId` | `not_created` |
| `targetIdentityPreparationApprovalId` | `not_approved` |
| `targetIdentityPreparationApprovalState` | `not_approved` |
| `targetIdentityPreparationExecuteByUtc` | `not_approved` |
| `targetIdentityPreparationClaimId` | `not_created` |
| `targetIdentityPreparationFence` | `not_created` |
| `targetDbBindingId` | `not_created` |
| `targetDbBindingState` | `not_created` |
| `targetDbBindingValidUntilUtc` | `not_approved` |
| `targetDbBindingEvidenceId` | `not_created` |
| `targetGlobalCoordinatorId` | `not_created` |
| `targetGlobalCoordinatorState` | `not_created` |
| `targetGlobalCoordinatorOwnerFenceId` | `not_created` |
| `targetGlobalCoordinatorConsumer` | `not_created` |
| `targetGlobalCoordinatorGeneration` | `not_created` |
| `targetGlobalCoordinatorEvidenceId` | `not_created` |
| `targetOperationFenceId` | `not_created` |
| `targetOperationFenceState` | `not_created` |
| `targetUploadBranchState` | `not_created` |
| `targetDeleteBranchState` | `not_created` |
| `targetOperationConsumer` | `not_created` |
| `targetOperationFenceGeneration` | `not_created` |
| `targetOperationFenceEvidenceId` | `not_created` |
| `deleteRecoverySnapshotId` | `not_created` |
| `deleteRecoverySnapshotState` | `not_created` |
| `deleteDbBeforeImageId` | `not_created` |
| `deleteDbBeforeImageContentBindingId` | `not_created` |
| `deleteDbBeforeImageSchemaBindingId` | `not_created` |
| `deleteDbBeforeImageColumnSetBindingId` | `not_created` |
| `deleteDbBeforeImageRowCount` | `not_observed` |
| `deleteDbBeforeImageObservedBytes` | `not_observed` |
| `deleteDbBeforeImageMaxBytes` | `not_approved` |
| `deleteDbBeforeImageCapacityEvidenceId` | `not_created` |
| `deleteDbBeforeImageConfidentialityClass` | `not_approved` |
| `deleteDbBeforeImageRetainUntilUtc` | `not_approved` |
| `deleteDbBeforeImageState` | `not_created` |
| `deleteDbBeforeImageDispositionEvidenceId` | `not_created` |
| `deleteDbBeforeImagePreparationReadiness` | `not_observed` |
| `rollbackReadiness` | `not_observed` |
| `deleteDbRestoreApprovalId` | `not_issued` |
| `deleteDbRestoreApprovalState` | `not_issued` |
| `deleteDbRestoreExecuteByUtc` | `not_approved` |
| `deleteDbRestoreMutationId` | `not_created` |
| `deleteDbRestoreOutcomeState` | `not_created` |
| `deleteDbRestoreOutcomeEvidenceId` | `not_created` |
| `edgeAuthClass` | `not_observed` |
| `startUploadApprovalId` | `not_approved` |
| `actionMaxDurationSeconds` | `not_approved` |
| `snapshotDispositionMarginSeconds` | `not_approved` |
| `snapshotActionLeaseId` | `not_created` |
| `snapshotActionLeaseState` | `not_created` |
| `actionMutationId` | `not_created` |
| `actionApprovedAbsentSetBindingId` | `not_created` |
| `actionApprovedAbsentKeyCount` | `not_observed` |
| `actionTargetAbsenceRevalidationEvidenceId` | `not_created` |
| `actionMutationOutcomeState` | `not_created` |
| `actionMutationOutcomeEvidenceId` | `not_created` |
| `approvedTargetRows` | `not_applicable` |
| `uploadJobId` | `not_created` |
| `acceptedRowsClass` | `not_applicable` |
| `retryApprovalId` | `not_approved` |
| `retryReconciliationCreationState` | `not_created` |
| `retryReconciliationSourceActionClass` | `not_created` |
| `retryReconciliationSourceFailureClass` | `not_observed` |
| `retryReconciliationCreationClaimId` | `not_created` |
| `retryReconciliationCreationFence` | `not_created` |
| `retryReconciliationCreationExpiresAtUtc` | `not_approved` |
| `retryReconciliationCreationEvidenceId` | `not_created` |
| `retryReconciliationRecordId` | `not_created` |
| `retryReconciliationState` | `not_created` |
| `retryReconciliationObservedAtUtc` | `not_observed` |
| `retryReconciliationExecuteByUtc` | `not_approved` |
| `retryReconciliationRetainUntilUtc` | `not_approved` |
| `retryReconciliationDispositionState` | `not_created` |
| `retryReconciliationDispositionEvidenceId` | `not_created` |
| `remainingPhysicalRows` | `not_applicable` |
| `auditEvidence` | `not_created` |
| `dbDeltaEvidence` | `not_queried` |
| `rowAttributionEvidence` | `not_queried` |
| `finalDecision` | `blocked` |

## Read-Only Method

The inventory used the operator-configured PLC source directly and considered
only direct child files with the `.csv` extension. It:

1. read the configured source using UTF-8;
2. classified the source without recording its raw path;
3. captured file size and modification metadata before reading;
4. streamed file bytes to count physical newline boundaries and included a
   non-empty EOF line without a terminal newline;
5. removed one header line from each non-empty CSV;
6. compared size, modification time, and scope before and after the scan; and
7. emitted only safe classes, counts, and the random inventory record id.

It did not call the Upload Preview API, start a backend, query Supabase, call an
Edge function, write audit or local application state, or modify a source file.

No deterministic raw-path fingerprint or inventory digest derived from one is
published. A predictable path can be recovered by testing candidate paths
against an unsalted digest. The random inventory record id plus version-control
history is the repository binding for this sanitized record.

## Redaction And Safety Validation

| Check | Result |
| --- | --- |
| Raw operational source path recorded | no |
| Raw source filename recorded | no |
| CSV content or row content recorded | no |
| Raw timestamp/device key recorded | no |
| DB URL, token, Authorization value, JWT, or credential recorded | no |
| Preview run or local Preview state created | no |
| Operational DB query or mutation performed | no |
| Source file mutation performed | no |

## Staleness And Stop Conditions

This record is historical baseline evidence for the recorded package identity,
source class, file count, and physical-row ceiling. It is not a reusable
long-term approval input. Do not refresh it for approval until production atomic
content binding, deterministic replacement/concurrency tests, and rebuilt-
package verification pass. Then repeat the same read-only inventory and create a
successor evidence record. A separate exact manifest-preparation approval must
create a protected single-use record before any later Preview-only approval.
Before the successor inventory, a separately controlled, pre-existing verified/
non-revoked trusted target baseline must already exist. After manifest/snapshot
preparation, a separate read-only target-identity preparation
approval/run/result must exactly match the observed DB identity to that owner-
only baseline before any later Preview approval.
Stop if:

- the human has not supplied the safe operator PC class or privacy-safe source
  alias;
- the successor record does not contain `inventoryObservedAtUtc`, a
  human-approved `inventoryMaxAgeSeconds`, and `previewExecuteByUtc`;
- the current time is later than `previewExecuteByUtc` or the inventory age
  exceeds `inventoryMaxAgeSeconds`;
- the operator PC, privacy-safe source alias, or configured source class
  differs;
- observed CSV files are not exactly `12`;
- physical data lines exceed `3451430`;
- any file is unstable, unreadable, or changes during inventory;
- the source scope changes;
- the package label, source commit, or ZIP hash differs; or
- protected manifest preparation is unapproved or its record is missing,
  expired, reused, tampered, unauthenticated, or mismatched; or
- trusted target baseline id/alias/state/evidence is missing, unresolved,
  substituted, revoked, or was created/self-attested from the first DB
  observation;
- target-identity preparation approval is not terminal `consumed`, its deadline
  is missing/inferred, claim/publication occurred after it, or its package/
  operator/inventory/manifest/
  snapshot/target-class/trusted-baseline binding differs;
- the protected target DB binding is missing, not `prepared`, expired, lacks safe
  evidence, or the observed authenticated exact identity does not match the
  owner-only expected trusted baseline identity; or
- Preview approval wording does not name the execution-adjacent successor
  inventory record, protected content manifest/snapshot, trusted target baseline,
  consumed target-identity preparation approval, and prepared unexpired target
  DB binding.

## Next Gate

No next execution gate is approved by this document. This record is a baseline,
not the record id for a later Preview approval. The next work is production
atomic content-manifest/snapshot binding retained through Preview, Start, and
Retry, bounded unrenewable Start/Retry leases with target-side transaction
fences/durable outcome markers, commit-unknown recovery, whole-attempt Retry
reconciliation, and disposition exclusion, deterministic replacement/
concurrency/source-reopen/lease-disposition/commit-window tests, and rebuilt-package verification. Only
after those pass and a separately controlled pre-provisioned verified target
baseline already exists may the operator and maintainer repeat the read-only
inventory, create a new record id, timestamp,
and reviewer confirmation bound to the exact package, a human-supplied safe
operator PC class, and a privacy-safe source alias that the human confirms out
of band maps to the exact configured folder. The successor record and approval
must also name `inventoryObservedAtUtc`, a human-approved
`inventoryMaxAgeSeconds`, and the resulting `previewExecuteByUtc`. No default
validity window may be inferred.

After the successor inventory, a separately approved protected local evidence
write must resolve and atomically claim an immutable/authenticated
`manifestPreparationApprovalId`, reject duplicate/concurrent claims, and create
exactly one owner-restricted, tamper-evident, single-use private content manifest
and immutable exact-byte snapshot bound to that approval plus inventory/package/
operator/source/scope. The approval ends `consumed` with one manifest/snapshot
pair or `invalid` on failure. It must also bind the inventory observation,
human-supplied maximum age, and a human-supplied claim/completed-publication
deadline within that validity window; a late claim or late publication is
invalid and any partial bytes are disposed. Raw file
identities, paths, filenames, content digests, manifest entries, and store
authentication material remain private. The human must review the safe approval
state and opaque `contentManifestRecordId`, `contentSnapshotRecordId`,
preparation time, deadline, bindings, counts, and both `prepared` states before
issuing any later Preview approval.

Next, and only after the safe manifest/snapshot result is human-reviewed, the
already provisioned `trustedTargetBaselineId` confirmed before successor
inventory must still be `verified`, non-revoked and resolve owner-only to the
expected authenticated DB-instance/database
identity. Its privacy-safe `trustedTargetAlias` and opaque
`trustedTargetBaselineEvidenceId` must be human-reviewed. Neither this record nor
first observation of the configured DB may create or rotate that trust anchor.
If it is absent, stop and require a separate security-reviewed installation/
provisioning work package and explicit approval.

Then a separately approved, immutable/authenticated, expiring, single-use
`targetIdentityPreparationApprovalId` may authorize exactly one bounded read of
authenticated DB-instance/database identity metadata and one protected local
result. Before any DB connection/read, production code must atomically claim the
approval with one owner claim id and monotonic fence. Only that claimant may
read; publication must CAS-recheck its token/fence/state/deadline/baseline, and
crash/restart/expiry/invalidation must advance the fence and end `invalid` so a
delayed reader/publisher cannot succeed. Before publication, production code must compare the observed exact
identity to the owner-only expected baseline. Exact match may publish one opaque
`targetDbBindingId` in `prepared` state with human-supplied
`targetDbBindingValidUntilUtc` and safe `targetDbBindingEvidenceId`; mismatch,
wrong DB at first observation, expiry, replay, owner/fence substitution, or baseline substitution makes
the approval/binding `invalid`. Human review of this safe exact-match result is
required before Preview approval.

The successor inventory must also record total observed source bytes. Exact
manifest/snapshot preparation approval must disclose that a confidential full-
byte operational CSV copy will be created, set a human-approved byte ceiling and
retention deadline, and require protected capacity/access-control evidence.
The exact preparation approval must also pre-authorize bounded automatic
cryptographic disposal at terminal chain completion (zero-target Preview or
completed Start/Retry), invalidation, or the retention deadline: stop access,
clear buffers, destroy the per-snapshot key first, remove
the byte file, verify absence, and record `snapshotDispositionEvidenceId`. Failed
removal leaves keyless bytes unreadable, alerts, and blocks new snapshot
preparation until idempotent same-record cleanup succeeds. This record itself
authorizes none of those future actions.

That later Preview approval must have its own immutable/authenticated
`previewApprovalId` and name the manifest-preparation approval, successor
inventory record, protected content manifest and immutable snapshot record ids,
trusted target baseline id/alias/state/evidence, consumed target-identity
preparation approval id/deadline/claim owner/fence, prepared target DB binding
id/state/validity/evidence, singleton exact-target coordinator id/expected state/
owner/empty consumer/generation/evidence, pre-reserved next operation-fence id,
and package source commit,
and state
`sourceClass=drive_letter`, `expectedFiles=12`, and
`expectedPhysicalRows<=3451430`. These are human approval fields, not
request-body fields accepted or enforced by the current Preview API.

No later Preview may claim the singleton coordinator while any older generation
is nonterminal, including `preview_claimed`, ready/active/retryable/delete-ready,
`commit_unknown_blocked`, `invalidating`, `recovery_disposition_pending`, or
`disposal_failed_blocked`. A resolved Delete holds its exact owner/generation
until separately approved exact DB-before-image restore plus disposal or verified
key-first disposal of every retained record is terminal. A source CSV snapshot is
provenance only and cannot establish exact rollback readiness. This record
authorizes none of those actions.

Public/committed content-snapshot evidence is limited to random opaque record ids,
safe states/classes/counts/timestamps, and approved package hashes. Separately
reviewed target evidence may additionally contain random non-derived baseline,
binding, claim, target-global-coordinator, operation-fence, and evidence ids plus a human-supplied privacy-
safe target alias and safe lifecycle states/timestamps. A later Delete record may
also publish random non-derived before-image ids plus safe counts/states/
timestamps, but never row values or private integrity material. Exact DB identity,
DB URLs, credentials, raw keys/rows, deterministic identity derivatives, and all
keyed integrity values remain owner-only.

Immediately before any approved API call, repeat the read-only scan and compare
the exact local file set, scope, size/mtime metadata, file count, physical-row
ceiling, package, operator PC class, source alias, and source class with the
successor record. Keep raw paths and filenames out of published evidence; record
only `preCallSnapshotCheckObservedAtUtc` and
`preCallSnapshotUnchanged=true`. Stop without calling Preview on expiry,
mismatch, unreadable/unstable input, or if this final comparison cannot be
evidenced. Preview remains unapproved.

The final metadata comparison does not make the current Preview implementation
safe to authorize. `backend/app/services/upload_preview.py` currently signs
files with size and mtime, so content can change after the check or be replaced
with equal-size/equal-mtime content. Preview must remain blocked until production
code and deterministic concurrency/replacement tests prove that it atomically
claims the Preview approval and protected manifest together, rejects
missing/expired/reused/tampered or mismatched approval/manifest records, verifies
private content digests, parses the same immutable snapshot, and terminally
consumes the manifest/Preview approval once while retaining the snapshot in
`previewed` state for any later separately approved Start/Retry chain. Start and
Retry workers must use only that snapshot and never reopen the operational
source; missing/tampered/mismatched snapshots must produce zero DB writes. Tests
must reject approval-id substitution plus duplicate/concurrent claims and source
change after Preview or before Retry. They must also reject concurrent/replayed
Preview claims across different chains for the same exact-target coordinator,
stale owner/generation publication, and a wrong same-port DB
present at first target observation, missing/revoked/rotated baseline, baseline/
alias/evidence substitution, target-binding expiry, and later target replacement.
Published content-snapshot evidence may record only approval ids/states and
opaque random `contentManifestRecordId`, `contentSnapshotRecordId`, and
`atomicSnapshotBindingEvidenceId` values. Separately reviewed target evidence
may use only the privacy-safe opaque ids/alias/states/timestamps allowed above;
raw paths, filenames, content hashes, manifest entries, exact target identity,
and keyed integrity material remain excluded.

This record authorizes neither trusted-baseline provisioning/rotation nor target-
identity preparation, Preview, Start, Retry, Delete, or any DB/runtime action.
