# Operator Data Mutation Safety Gate

Status: `mutation_deferred_until_separate_approval`

Created: 2026-06-22

Last updated: 2026-08-15 Asia/Seoul

## Decision

Do not run Upload Preview, Start Upload, Retry Failed, Upload Delete,
Settings save, Local Supabase start/stop, feature-gate enablement, LAN
enablement, Supabase reset/migration/cleanup, Docker cleanup, deployment, or
any other mutating operator action from the handoff package until a separate
approval names the exact scope below.

The accepted handoff artifact is the main-based API-mode operator package:

- source commit: `cb8a3c8`
- full commit: `cb8a3c83de7437f127da71f013224e42a9a46219`
- artifact label: `ExtrusionWebConsole-cb8a3c8-20260621-160038-290`
- frontend mode: `api`
- runtime mode: `operator-ready`
- zip created: `false`
- zip SHA-256: not applicable because this accepted artifact is an unpacked
  package directory, not a zip handoff
- launcher `-CheckOnly`: passed, no backend process started
- shortcut installer `-CheckOnly`: passed, no shortcuts written

For a future package, do not reuse the source commit or artifact label above.
Update this package metadata block from that package's `package-build-info.json`
before requesting any mutation approval.

This document is not approval that the full V2 scope is complete. It is only a
mutation safety gate for the accepted operator package.

Current V2 implementation status is tracked separately in
`docs/165_v2_status_matrix.md`. That matrix is the current status reference;
this document is only the mutation approval gate.

## Current Boundary

Allowed without a new mutation approval:

- package metadata inspection;
- zip checksum verification only when the accepted package was created as a
  zip artifact;
- launcher `-CheckOnly`;
- shortcut installer `-CheckOnly`;
- read-only HTTP checks such as `/`, `/upload`, `/logs`, `/settings`,
  `/api/health`, `/api/config`, `/api/audit?limit=1`, and docs-disabled route
  checks.

Not allowed without a new mutation approval:

- Upload Preview creation or cancellation;
- Start Upload;
- Retry Failed;
- Upload Delete preflight, start, or reconcile;
- Settings save;
- Local Supabase start or stop;
- changing `v2_row_attribution_enabled`, `v2_db_delta_evidence_required`, or
  related evidence gates;
- operational DB writes or deletes;
- Supabase reset, migration, cleanup, prune, or Docker cleanup;
- LAN exposure, delete UI expansion, or deployment.

## Candidate Classification

| Candidate | Class | Default decision | Required approval |
| --- | --- | --- | --- |
| Package metadata, zip checksum when applicable, launcher `-CheckOnly`, read-only routes | read-only | allowed | none beyond task request |
| Protected content-manifest preparation | local protected evidence write; no DB/source mutation | hold | atomic-binding implementation/tests and verified package, then exact one-time manifest-preparation approval |
| Upload Preview-only against configured operational source | local-state write plus DB read/reconcile | blocked under current implementation | atomic content binding implementation/tests, verified rebuilt package, then exact Preview-only approval |
| Fixture mutation against disposable DB | fixture mutation | hold | exact fixture approval |
| Start Upload against real local Supabase | limited real mutation | blocked until single-use approval and immutable-snapshot lifecycle exists | lifecycle implementation/tests, fresh Preview, then exact Start Upload approval bound to the Preview snapshot |
| Retry Failed against real local Supabase | limited real mutation | blocked until single-use approval and immutable-snapshot lifecycle exists | lifecycle implementation/tests, failed-job evidence, then exact Retry Failed approval bound to the source-job snapshot |
| Already-in-DB hard delete | destructive real mutation | blocked until separate single-use preflight/delete lifecycles and atomic exact DB-before-image rollback exist | lifecycle implementation/tests, source-provenance preflight, protected target-side complete-row before-image + DELETE + marker transaction, exact restore/disposition tests, then complete exact hard-delete approval |
| Supabase reset/migration/cleanup, Docker cleanup, LAN, delete UI expansion, deployment | forbidden for this gate | blocked | new plan and separate approval |

## Preview-Only Approval Gate

Preview-only may be considered only after all of these are true:

- package metadata, and zip checksum when `zipCreated=true`, still match this
  document;
- launcher first-launch smoke remains passed or is rerun successfully;
- `/api/config` confirms the active source class and target class are expected;
- a separately approved protected target-identity preparation run produced an
  unexpired opaque `targetDbBindingId` that resolves owner-only to the
  authenticated exact intended local DB instance/database identity; safe target,
  loopback, port, and readiness classes are diagnostic only;
- the exact source is confirmed outside chat by the operator or maintainer and
  bound to a human-supplied privacy-safe `sourceAlias` plus
  `operatorPcClass`;
- local Supabase DB reachability is understood before interpreting DB-dependent
  preview states;
- a fresh read-only inventory precheck produced a random, path-independent
  `inventoryEvidenceRecordId`, the observed file count, and the approved
  physical row ceiling for the intended approval scope;
- the successor inventory record and approval name `inventoryObservedAtUtc`, a
  human-approved `inventoryMaxAgeSeconds`, and `previewExecuteByUtc`;
- a separately approved protected manifest-preparation step produced an opaque,
  unexpired, unused `contentManifestRecordId` plus an owner-restricted immutable
  `contentSnapshotRecordId`, bound to that inventory, package, operator, source,
  scope, counts, private per-file content digests, and exact
  `manifestPreparationApprovalId`;
- immediately before the Preview API call, a final read-only scan confirms the
  same file set, scope, size/mtime metadata, counts, package, operator PC, source
  alias, and source class;
- the production Preview path has an implemented and automated-test-covered
  atomic snapshot binding: it verifies a content-based manifest and parses the
  same protected immutable snapshot retained for later approved actions. A separate
  metadata scan and the current `size + mtime` file signature do not qualify;
- no Start Upload, Retry Failed, Delete, Settings save, or feature-gate change is
  bundled into the approval.

## Read-only Inventory Precheck

After atomic content binding is implemented/tested and the rebuilt package is
verified, run a read-only inventory precheck for the same source class and
intended approval scope before requesting Preview-only approval.

This precheck is not Upload Preview. It must not create a Preview run, call the
Upload Preview API, write to the DB, write audit or local state, mutate source
files, or run Start Upload, Retry Failed, Delete, Settings save, feature-gate
changes, Supabase cleanup, Docker cleanup, LAN enablement, or deployment.

The precheck may record only safe inventory evidence:

- source class such as `drive_letter`, `network`, or `mounted`, not raw path;
- safe operator PC class;
- a privacy-safe source alias that is random or otherwise resistant to path
  guessing and is confirmed out of band to map to the exact source;
- a random, path-independent inventory evidence record id;
- inventory observation time, a human-approved maximum age, and the resulting
  Preview execution deadline;
- observed files count for the intended scope;
- physical data-line count or a conservative approved physical row ceiling;
- total observed source bytes for a separately human-approved full-byte snapshot
  ceiling;
- source eligibility or go/no-go reason classes.

Do not publish a deterministic hash or fingerprint derived from a raw source
path. Such a value can disclose the path through candidate-path guessing.

The approval `<fileCount>`, `<rowLimit>`, and `<contentSnapshotMaxBytes>` must come from a fresh read-only
inventory precheck completed immediately before that approval. They must not be
user guesses, copied from an earlier run, reused as long-term defaults, or used
as blanket approval for future folder growth.

If inventory cannot establish observed files, an approved physical row ceiling,
and observed bytes, do not request snapshot preparation or Preview-only. If the operational folder grows
later, repeat read-only inventory and issue a new Preview-only approval for the
new observed scope only after the atomic-binding implementation/package gate is
still satisfied.

## Protected Content-Manifest Preparation Gate

This is a local evidence write, not part of the read-only inventory and not
Preview. It requires separate exact approval and must use the implemented,
tested, rebuilt package. The approval id must resolve to an immutable/
authenticated protected approval record, not an arbitrary request string or
Markdown alone. Manifest creation must atomically claim that approval once,
reject duplicate/concurrent claims, and finish it as `consumed` with one manifest
and one full-byte snapshot or `invalid` on failure. The private manifest and
exact-byte snapshot must be owner-restricted, confidentiality-protected at rest,
tamper-evident, single-use, and bound to the approval plus inventory/package/
operator/source scope. Storage protection and capacity for the approved byte
ceiling must pass before copying. The snapshot is created while the bytes are
hashed and must not mutate the operational source. The manifest contains
private canonical file identities and content digests; none of those values may
be published. Only approval/opaque record ids and safe classes/counts/timestamps
may leave the protected store.

The protected approval must bind `inventoryObservedAtUtc`, the human-supplied
`inventoryMaxAgeSeconds`, and a human-supplied
`manifestPreparationExecuteByUtc` no later than the inventory expiry. Both the
atomic claim and completed manifest/snapshot publication must occur before that
deadline. Reject an expired claim before any byte copy. If the deadline expires
during copying, stop, clear buffers, mark the approval/partial records `invalid`,
and cryptographically dispose any partial bytes; never publish them as
`prepared`.

Required manifest-preparation approval wording:

```text
The manifest-preparation approval id is <manifestPreparationApprovalId> and both claim and completed protected publication must occur by <manifestPreparationExecuteByUtc>.
I approve exactly one protected local content-manifest plus full-byte immutable snapshot preparation from package sourceCommit <sourceCommit> for inventory record <inventoryEvidenceRecordId>.
That inventory was observed at <inventoryObservedAtUtc> and is approved for at most <inventoryMaxAgeSeconds> seconds; the preparation deadline above is within that window.
The approved operator PC class is <operatorPcClass>, source alias is <sourceAlias>, source class is <sourceClass>, expected files is <fileCount>, expected physical rows is <= <rowLimit>, and full-byte snapshot size is <= <contentSnapshotMaxBytes> bytes.
The snapshot may be read only by the later separately approved Preview/Start/Retry chain and only until <contentSnapshotRetainUntilUtc>.
I approve automatic bounded cryptographic disposal at terminal chain completion (zero-target Preview or completed Start/Retry), invalidation, or that deadline, whichever occurs first: stop active access, clear buffers, destroy the per-snapshot encryption key first, remove the byte file, verify absence, and record <snapshotDispositionEvidenceId>. A failed removal must leave keyless bytes unreadable, alert the operator, block new snapshot preparation, and retry idempotently only for the same record.
I acknowledge that this write stores a confidential complete copy of the approved operational CSV bytes in owner-restricted protected storage.
This approval permits only that protected manifest/snapshot write and its bounded automatic disposal described above. It does not approve Upload Preview, Start Upload, Retry Failed, Delete, Settings save, DB access, runtime lifecycle, source mutation, any other cleanup, LAN, or deployment.
```

After preparation, publish only `manifestPreparationApprovalId`, its claim/
completion deadline and terminal state `consumed`, `contentManifestRecordId`, `contentManifestPreparedAtUtc`,
`contentManifestExecuteByUtc`, safe bindings, and manifest lifecycle class
`prepared`, plus opaque `contentSnapshotRecordId` and snapshot state `prepared`.
Also publish safe observed/approved byte counts,
`contentSnapshotRetainUntilUtc`, disposition state `scheduled`, and later safe
`snapshotDispositionEvidenceId`. Stop if
protected capacity, confidentiality/access controls, authentication material, or
the retention/disposition policy is missing; the record cannot be proven
tamper-evident; or any binding differs. Preview approval may be requested only
after the human reviews that safe result.

### Protected Target-Identity Preparation Approval

Inventory performs no DB query and manifest/snapshot preparation authorizes no
DB access. After the snapshot is prepared, an immutable/authenticated, expiring,
single-use `targetIdentityPreparationApprovalId` is required to create the exact
target binding before Preview approval. It authorizes only one bounded read of
authenticated stable DB-instance/database identity metadata plus one protected
local evidence/audit write. It does not authorize operational table row/key
queries or any DB mutation.
This gate does not authorize creation or rotation of the trusted target
baseline. If it is absent, stop and use a separate security-reviewed
installation/provisioning work package with explicit approval.

```text
The target-identity preparation approval id is <targetIdentityPreparationApprovalId>; claim and protected publication must complete by <targetIdentityPreparationExecuteByUtc>.
I approve exactly one read-only target-identity preparation for package sourceCommit <sourceCommit>, operator PC class <operatorPcClass>, inventory <inventoryEvidenceRecordId>, manifest <contentManifestRecordId>, snapshot <contentSnapshotRecordId>, and configured safe target class <targetClassStatus>.
The expected exact target is anchored by pre-existing protected baseline <trustedTargetBaselineId> in state <trustedTargetBaselineState>, human-reviewed privacy-safe alias <trustedTargetAlias>, and safe out-of-band verification evidence <trustedTargetBaselineEvidenceId>. This preparation may not create, replace, or self-attest that baseline from the first DB observation.
The baseline/evidence ids must be random, opaque, path-independent, and not
derived from DB URL, cluster/system id, database name, or any target material;
the alias must be human-supplied and not a deterministic target derivative.
Exact identity and all keyed integrity values remain owner-only.
The resulting opaque target DB binding may remain valid only until <targetDbBindingValidUntilUtc>, no later than snapshot retention <contentSnapshotRetainUntilUtc>.
This approval also binds exact-target singleton coordinator <targetGlobalCoordinatorId> as either the existing coordinator for that baseline identity or the one pre-reserved random id that an exact-match publication CAS may create if none exists. It may never create a second coordinator for the same exact target.
This approval permits only authenticated DB-instance/database identity metadata read and one protected local evidence/audit write. It does not approve operational table row/key queries, Upload Preview, Start Upload, Retry Failed, Delete, Settings save, DB mutation, runtime lifecycle, cleanup, LAN, or deployment.
```

Before any DB connection/read, the runtime must atomically claim
`available -> claimed`, record opaque owner
`targetIdentityPreparationClaimId` plus monotonic
`targetIdentityPreparationFence`, and recheck the deadline and already
`verified`, non-revoked trusted baseline. Only that token/fence holder may perform
the one bounded identity read. Publication compares the observed authenticated
exact DB identity to its owner-only expected identity and CAS-rechecks the same
claim id/fence, `claimed` state, deadline, baseline state/evidence, and all
approval bindings. Only an exact match may create at most one random opaque
`targetDbBindingId` and resolve-or-create by uniqueness CAS the approval-bound
`targetGlobalCoordinatorId` for that trusted exact identity,
keep exact identity and versioned domain-
separated keyed integrity material in an authenticated owner-only store, and
finish `consumed/prepared` before the deadline. Public evidence contains only
approval/claim/fence/baseline/binding/coordinator ids, privacy-safe alias, safe class/state, timestamps, and
`targetDbBindingEvidenceId`. Response loss after publication recovers only the
same result without another DB read; crash/expiry/restart/invalidation before
publication advances the fence and ends `invalid`;
missing/revoked/rotated baseline, wrong DB at first observation, failure, expiry,
mismatch, concurrency, replay, or same-port target substitution
ends `invalid`. Human review of the safe result is required before Preview
approval.

Tests must cover every package/operator/inventory/manifest/snapshot/target-class/
deadline/trusted-baseline/alias/evidence/claim-owner/fence field substitution,
arbitrary/missing ids, duplicate/concurrent claims, failure before/after claim/
read/publication commit, response-loss recovery without a second read, restart/
expiry/invalidation racing a delayed reader/publisher, same-loopback/same-
port cluster/database replacement before first observation and after binding,
wrong DB present at first observation, missing/revoked/rotated baseline, private
identity/all keyed-integrity-value redaction, candidate enumeration against
baseline/evidence ids and alias, cross-chain
reuse, duplicate/sibling coordinator creation, and zero operational-table reads/DB writes.

Required approval wording:

```text
The Preview approval id is <previewApprovalId> and it binds manifest-preparation approval <manifestPreparationApprovalId>.
It binds pre-existing trusted target baseline <trustedTargetBaselineId> in verified/non-revoked state <trustedTargetBaselineState>, privacy-safe alias <trustedTargetAlias>, and safe evidence <trustedTargetBaselineEvidenceId>.
It also binds consumed target-identity preparation approval <targetIdentityPreparationApprovalId>, completed by <targetIdentityPreparationExecuteByUtc>, and prepared target DB binding <targetDbBindingId> in state <targetDbBindingState>, valid only until <targetDbBindingValidUntilUtc>, with safe evidence <targetDbBindingEvidenceId>.
It binds the singleton exact-target coordinator <targetGlobalCoordinatorId> in expected state <idle | terminal | invalidated_terminal>, expected owner <targetGlobalCoordinatorOwnerFenceId or none>, empty consumer, generation <targetGlobalCoordinatorGeneration>, and safe evidence <targetGlobalCoordinatorEvidenceId>, plus pre-reserved next chain fence <targetOperationFenceId>. Preview must atomically claim that exact coordinator generation and install only the pre-reserved fence as its sole next owner; any claimed/ready/active/retryable/delete-ready/commit-unknown/invalidating older chain for the same target must reject this Preview.
I approve exactly one Upload Preview-only run from package sourceCommit <sourceCommit>.
The approved inventory record is <inventoryEvidenceRecordId> on operator PC class <operatorPcClass>.
The approved protected content manifest is <contentManifestRecordId>, prepared at <contentManifestPreparedAtUtc>, and it must be consumed no later than <contentManifestExecuteByUtc>.
The approved immutable content snapshot is <contentSnapshotRecordId> in state prepared.
Its approved maximum size is <contentSnapshotMaxBytes> bytes, it may be read only until <contentSnapshotRetainUntilUtc>, and its disposition state is scheduled.
The approved source alias is <sourceAlias>, the source class is <sourceClass>, expected files is <fileCount>, and expected physical rows is <= <rowLimit>.
The approved exact operational DB target is protected binding <targetDbBindingId>; safe target/readiness classes do not replace it.
The inventory was observed at <inventoryObservedAtUtc>, its approved maximum age is <inventoryMaxAgeSeconds> seconds, and Preview must start no later than <previewExecuteByUtc>.
This approval does not approve Start Upload, Retry Failed, Delete, Settings save, feature gate enablement, Supabase reset/cleanup, or Docker cleanup.
```

In this wording, `expected files` means observed files from the fresh read-only
inventory, and `expected physical rows` means the approved physical row ceiling
from that same inventory. The inventory record id, protected content manifest
record id, content snapshot record id, operator PC class, source alias, and
trusted target baseline id/alias/state/evidence,
`targetIdentityPreparationApprovalId`, and `targetDbBindingId` must match
exactly. No validity window or record reuse may be inferred. All three approval
ids must resolve to
immutable/authenticated protected approval records; arbitrary request strings or
Markdown alone do not satisfy the runtime gate. Preview must atomically claim its
approval, manifest, and prepared target DB binding together. Immediately before the API call, repeat
the read-only scan; stop unless the observation is unexpired and the file set,
scope, size/mtime metadata, counts, package, operator PC, source alias, and
source class are unchanged. This final metadata scan is supplementary and does
not close the check/use race. Until the Preview implementation atomically claims
the protected manifest, verifies the private content digests, consumes the same
protected immutable snapshot bytes, and records a single-use terminal
state with unchanged `manifestPreparationApprovalId` and `previewApprovalId`,
this approval wording must not be used to run Preview.
For positive target rows, that same protected terminal operation must also store
the exact distinct target-only keyset inside the snapshot's owner-only encrypted
boundary and expose only `actionApprovedAbsentSetBindingId` plus exact
`actionApprovedAbsentKeyCount`. Raw keys/unkeyed digests remain unpublished; the
private set is disposed with the snapshot. A count-only/reconstructed binding is
invalid, and zero-target Preview records `not_created`.

Evidence to record after Preview-only:

- package label and source commit;
- preview run id;
- inventory evidence record id, operator PC class, and privacy-safe source alias;
- protected content manifest record id, prepared-at/deadline fields, and
  single-use terminal state;
- protected content snapshot record id and `previewed` state;
- snapshot retention/disposition state and
  `snapshotDispositionEvidenceId` when disposal has triggered;
- manifest-preparation approval id/state and Preview approval id/state exactly
  as bound in manifest creation, claim/run, and terminal evidence;
- target-identity preparation approval id/state/deadline and target DB binding
  id/state/validity/evidence id;
- inventory observation/deadline fields, final check timestamp, and
  `preCallSnapshotUnchanged=true`;
- opaque `atomicSnapshotBindingEvidenceId`, unavailable until the production
  atomic-binding implementation and deterministic tests exist;
- protected target-only absent-set binding id and exact distinct-key count, or
  `not_created` for zero target rows;
- source class, not raw path;
- run status;
- total files, status counts, target row count, risky count, already-in-DB
  count, partial-overlap count;
- DB status class, not raw DB URL;
- opaque protected exact target DB binding id verified on the Preview query
  session;
- audit evidence for `upload.preview` or blocked/failure event;
- confirmation that no upload/delete/retry/settings mutation was run.

When Preview succeeds with zero target rows, the upload/snapshot branch is
terminal: automatic snapshot disposition must reach `disposed` with safe evidence
before a proceed decision. An independently eligible `already_in_db` Delete
branch may remain `delete_preflight_ready` but may not reuse that disposed
snapshot; the whole target chain completes only after Delete is explicitly
excluded or independently reaches a terminal state. With positive target rows,
disposition may remain `scheduled` only until separately approved Start/Retry
completes or the retention deadline.

Rollback for Preview-only:

- do not delete operational DB rows;
- preserve preview and audit evidence;
- if Preview points at the wrong source, stop and document the blocked result;
- do not use Start Upload, Retry Failed, or Delete as a cleanup workaround.

## Fixture Mutation Gate

Fixture mutation may be considered only for disposable local fixture DBs that are
not operational data and can be recreated from source-controlled fixtures or a
maintainer-approved test backup.

Required approval wording:

```text
I approve exactly one mutation smoke against disposable fixture DB <fixtureId>.
This approval does not approve operational DB use, operational CSV use, Supabase reset/cleanup, Docker cleanup, LAN, or delete UI expansion.
```

Evidence to record:

- fixture identifier, not a raw sensitive path;
- setup command class;
- operation type;
- before/after row counts;
- audit rows and state DB evidence;
- teardown or preservation decision.

Rollback:

- discard or recreate only the fixture DB;
- never reuse fixture rollback instructions for operational data.

## Start Upload Gate

Start Upload against real local Supabase is blocked until a fresh Preview-only run
has completed and the result is reviewed.

It also remains blocked until production code implements and deterministically
tests an immutable/authenticated, expiring, single-use Start approval record and
retains the protected immutable snapshot through execution. The service must
atomically claim `startUploadApprovalId` and the `previewed` snapshot, create one
unrenewable active-use lease, claim the approval's pre-reserved
`actionMutationId`, and create the upload
job; it must reject substitution/
duplicate/concurrent claims and finish
the approval `invalid` only if no job commits. Once exactly one job commits, the
approval is permanently `consumed` regardless of the later job outcome; worker
failure, cancellation, response loss, or retry must never reopen it. The worker
must use only the protected snapshot and never reopen the operational source.

Deterministic coverage must include operational-source replacement after Preview
and before Start, equal-size/equal-mtime replacement, concurrent source writes,
missing/tampered snapshots, worker source-reopen attempts, and zero DB writes on
any pre-mutation snapshot mismatch. It must also prove the target-side fence and
durable outcome marker required by `docs/173`, including crash/response loss
after target commit but before local lease release, never infer rollback, bind
one unrenewable lease to the human duration/margin, reconcile
`commit_unknown_blocked`, prevent disposition races, and, after an authoritative
eligible retryable rollback, atomically consume one source-action/failure-class-
bound reconciliation-creation entitlement with an owner token, fencing
generation, and absolute publication
deadline; reject a delayed publisher after invalidation/expiry, recover only the
same published record, and dispose its encrypted private subset within snapshot
retention.
Coverage must prove a Start target-absence drift/conflict makes that entitlement
`invalid` before any reconciliation DB read/record publication, while the
separately defined Retry drift policy remains eligible.
It must also bind the exact protected target-only keyset/distinct-key count and
prove serializable in-transaction absence revalidation, canonical writer fencing,
conflict-rejecting conditional inserts, exact committed-set verification, and
zero action writes/no overwrite when target state drifts before or during Start.
It must bind the same `targetDbBindingId` from Preview through approval, job,
marker, transaction, reconciliation, and final evidence, revalidate exact target
identity on each DB session/transaction, and reject same-loopback/same-port
cluster or database replacement with zero action writes.
Coverage must also exercise target-binding expiry immediately before, at, and
after atomic claim, marker preparation, mutation, outcome reconciliation, and
whole-attempt reconciliation publication; a lease or publication deadline beyond
the minimum target-binding/snapshot ceiling must be rejected with zero writes.

Required preconditions:

- Preview run is fresh and succeeded;
- Preview source class matches the approved source class;
- DB status is reachable and reviewed;
- current app config still points to the expected local DB target class, and
  runtime readiness for Supabase API, DB, and Edge is ready;
- the pre-existing trusted target baseline id/alias/state/evidence remains the
  same verified, non-revoked trust anchor reviewed before Preview;
- the consumed `targetIdentityPreparationApprovalId` and protected exact
  `targetDbBindingId`/state/validity/evidence from Preview resolve, the binding is
  still `previewed` and unexpired, and it revalidates to the same authenticated
  target instance/database identity;
- the protected `targetOperationFenceId` is globally `idle`, upload branch
  `preview_ready`, Delete branch unowned, and its exact generation/evidence is
  bound in the Start approval; Start claims it atomically with the approval/
  snapshot/job so a Delete preflight cannot win concurrently;
- the same exact-target singleton `targetGlobalCoordinatorId` names this fence
  as its sole owner in `chain_ready`; its exact generation/evidence is bound in
  the Start approval and is atomically claimed with the chain fence;
- configured Edge auth is ready for the function JWT mode; a publishable key or
  stale non-JWT value must not be treated as a Start Upload approval key while
  the Edge function still requires JWT verification;
- `risky = 0`;
- target files and target rows are greater than zero;
- target-only row count matches UI/API/approval text;
- partial-overlap rows are reviewed separately and are not included in the
  Start Upload approval row count unless a later explicitly approved flow says
  otherwise;
- package source commit, and zip checksum when `zipCreated=true`, still match
  this document;
- a protected `startUploadApprovalId` is `available`, unexpired, and bound to the
  package, operator/source, Preview run, exact target rows/files, deadline,
  `actionMaxDurationSeconds`, `snapshotDispositionMarginSeconds`,
  `contentSnapshotRecordId`, and `atomicSnapshotBindingEvidenceId` from the
  succeeded Preview;
- the succeeded Preview produced one protected `actionApprovedAbsentSetBindingId`
  for the exact target-only distinct keyset and exact
  `actionApprovedAbsentKeyCount`, and both are bound in the approval;
- the protected snapshot is immutable and in state `previewed`, and a mismatch
  or failed claim before mutation is guaranteed to produce zero DB writes;
- `contentSnapshotRetainUntilUtc` has not passed and disposition state is
  `scheduled`;
- the human-approved `actionMaxDurationSeconds` plus disposal margin fits before
  both the target DB binding validity and snapshot retention deadlines; exact
  `snapshotDispositionMarginSeconds` is bound, the action lease expires no later
  than `min(targetDbBindingValidUntilUtc, contentSnapshotRetainUntilUtc)`, and
  one random unique `actionMutationId` is pre-reserved in the immutable approval
  and can be claimed with one target-fenced DB mutation lease atomically with the
  job;
- no feature gate is enabled as part of the upload approval.

Required approval wording:

```text
The Start Upload approval id is <startUploadApprovalId> and it must be claimed by <startUploadExecuteByUtc>.
I approve exactly one Start Upload for preview run <previewRunId> with target files <targetFiles> and target rows <targetRows>.
The protected exact target-only set binding is <actionApprovedAbsentSetBindingId> with distinct keys <actionApprovedAbsentKeyCount>.
This approval is for package sourceCommit <sourceCommit>, operator PC class <operatorPcClass>, source alias <sourceAlias>, and source class <sourceClass>.
It binds the same pre-existing trusted target baseline <trustedTargetBaselineId> in verified/non-revoked state <trustedTargetBaselineState>, privacy-safe alias <trustedTargetAlias>, and safe evidence <trustedTargetBaselineEvidenceId> used by Preview.
It binds protected target operation fence <targetOperationFenceId> in chain state idle, upload branch preview_ready, with exact generation <targetOperationFenceGeneration> and safe evidence <targetOperationFenceEvidenceId>. Job creation must atomically claim that generation for consumer start; a concurrent Delete preflight or any stale/terminal generation must fail.
It binds exact-target singleton coordinator <targetGlobalCoordinatorId>, sole owner fence <targetOperationFenceId>, state chain_ready, empty consumer, exact generation <targetGlobalCoordinatorGeneration>, and safe evidence <targetGlobalCoordinatorEvidenceId>. Job creation must atomically claim both generations for consumer start; any different Preview-chain owner or concurrent target consumer must fail.
The approved exact operational DB target comes from consumed preparation approval <targetIdentityPreparationApprovalId>, completed by <targetIdentityPreparationExecuteByUtc>, and is protected binding <targetDbBindingId> in state <targetDbBindingState>, valid only until <targetDbBindingValidUntilUtc>, with safe evidence <targetDbBindingEvidenceId>. It must be unexpired and revalidated on the authoritative target transaction; safe target/readiness classes do not replace it.
It is bound to immutable content snapshot <contentSnapshotRecordId> and atomic snapshot binding evidence <atomicSnapshotBindingEvidenceId> from that Preview.
That snapshot may be read only until <contentSnapshotRetainUntilUtc>; this approval does not authorize snapshot deletion or extend retention.
The action maximum duration is <actionMaxDurationSeconds> seconds and the required disposition margin is <snapshotDispositionMarginSeconds> seconds. Job creation must atomically create one unrenewable snapshot action lease whose expiry is claim time plus that duration and whose expiry plus that margin is no later than both <targetDbBindingValidUntilUtc> and <contentSnapshotRetainUntilUtc>, and claim the pre-reserved <actionMutationId>.
The random unique actionMutationId above is pre-reserved in this immutable approval and may only be claimed with this approval, snapshot, exact subset, duration, margin, lease, and job.
As part of that one Start action, I approve creation of exactly one target-side prepared outcome/fence marker for the same actionMutationId before any all_metrics write; it authorizes no other DB mutation. Every action write and the prepared-to-committed marker transition must share one authoritative target transaction; a guarded prepared-to-aborted finalization may occur only after non-commit is authoritative.
That transaction must first revalidate the exact target identity and unexpired target binding using the authoritative target DB clock, then serializably revalidate every key in the protected approved-absent set, use canonical key fences honored by every application writer and conflict-rejecting conditional inserts, and commit only if the exact inserted keyset/count equals the binding. Any expired/substituted target, preexisting/concurrent key, or mismatch must roll back every action all_metrics write without overwrite and require a fresh Preview and approval.
I approve bounded read-only target-outcome reconciliation for that same actionMutationId within this window and, only if its immutable aborted marker is finalized and observed before lease expiry, exactly one whole-attempt exact DB reconciliation plus protected retry-reconciliation evidence record. Timeout, response loss, or lease expiry must become commit_unknown_blocked unless the immutable target marker proves committed or aborted/complete rollback.
This authorization explicitly excludes Start target-absence drift/conflict. For that failure class the reconciliation-creation entitlement must become invalid, no reconciliation DB read or record is allowed, and a fresh Preview/manifest/snapshot approval chain is required.
Any eligible reconciliation must atomically claim the source action's unique single-use creation entitlement before any DB read, durably recording and binding its source action class, safe terminal failure class, owner claim id, monotonic fence, and absolute publication deadline no later than the source lease, target-binding validity, and snapshot boundaries. Publication must compare-and-set that exact eligible action/failure class, unexpired token/fence, the same unexpired target binding, and current rollback/snapshot/disposition state; invalidation advances the fence, so a delayed publisher cannot succeed. Duplicate or response-loss recovery may return only the same record. Its exact private subset must remain owner-only, tamper-evident, per-record encrypted, use the named snapshot retention deadline as its non-extendable access ceiling, and be cryptographically disposed earlier on terminal Retry, invalidation, expiry, or snapshot disposition.
This approval does not approve Retry Failed, Delete, Settings save, or feature gate enablement.
```

Evidence to record after Start Upload:

- preview run id;
- Start Upload approval id, deadline, and terminal state;
- protected content snapshot record id/state, retention deadline, disposition
  state, `snapshotDispositionEvidenceId`, and atomic snapshot binding evidence
  id;
- action maximum duration, disposition margin, snapshot action lease id/expiry/
  terminal state, action mutation id/outcome/evidence id;
- protected approved-absent set binding id/distinct-key count and target absence-
  revalidation evidence id;
- trusted target baseline id/alias/state/evidence, target-identity preparation
  approval id/state/deadline, and protected exact target DB binding id/state/
  validity/evidence id;
- target operation fence id/chain state/upload branch/Delete branch/consumer/
  generation/evidence;
- reconciliation source action/failure class, creation state/evidence id and, if created, protected record id/
  state/owner claim id/fence/creation expiry/observation/claim deadline/retention/
  disposition/evidence with safe counts;
- upload job id;
- approved target-only row count;
- full upload estimate, target-only rows, and partial-overlap rows as separate
  counts when available;
- started/completed timestamps;
- file counts and job status;
- accepted/upserted row count from the Edge response class;
- final job event status;
- audit evidence for upload start and completion or failure;
- whether any partial failure requires investigation.

A succeeded Start with no retryable remainder requires snapshot state
`completed`, disposition `disposed`, and safe disposition evidence. A retryable
failure may retain `scheduled` only until the approved retention deadline.

Rollback:

- do not delete rows as a default rollback;
- preserve `all_metrics(timestamp, device_id)` uniqueness/upsert safety for other
  paths, but never use an unconstrained upsert update for this approved absent-
  only action;
- any partial DB mutation is a blocking all-or-nothing contract violation;
  preserve job/audit evidence, prohibit Retry and cleanup, and resume only under
  a separately designed reconciliation/fix-forward protocol that proves the
  committed outcome;
- Retry Failed is possible only after authoritative rollback evidence plus fresh
  exact DB reconciliation defines every still-absent row and a separate approval
  below; however, Start target-state drift/conflict is explicitly non-retryable
  and invalidates this chain, so it requires a fresh Preview/manifest/snapshot
  approval chain rather than reconciliation-to-Retry.

## Retry Failed Gate

Retry Failed is blocked until a failed or retryable upload job is reviewed.

It also remains blocked until production code implements and deterministically
tests an immutable/authenticated, expiring, single-use Retry approval record and
retains the source job's protected immutable snapshot. The service must
atomically claim `retryApprovalId` and the `retryable` snapshot, create one
unrenewable active-use lease, claim the approval's pre-reserved
`actionMutationId`, and create the retry
job/event; it must reject substitution/
duplicate/concurrent claims and finish the
approval `invalid` only if no retry job/event commits. Once exactly one action
commits, the approval is permanently `consumed` regardless of the later retry
outcome; worker failure, cancellation, response loss, or another retry request
must never reopen it. The Retry worker must use only the same protected snapshot
and never reopen the operational source.

Deterministic coverage must include operational-source change before Retry,
equal-size/equal-mtime replacement, concurrent source writes, missing/tampered
snapshots, worker source-reopen attempts, and zero DB writes on any pre-mutation
snapshot mismatch. It must also prove the target-side fence and durable outcome
marker required by `docs/173`, including failure after reported progress, crash/
response loss after target commit but before local lease release, whole-subset
reconciliation after rollback, unique source-action record creation and response-
loss recovery, owner-token/fence/deadline CAS against expiry/invalidation,
encrypted private-subset retention/disposition,
`commit_unknown_blocked`, and disposition races.
It must also revalidate the complete protected still-absent distinct keyset inside
the authoritative serializable mutation transaction, use canonical writer fences
and conflict-rejecting conditional inserts, and fully roll back without overwrite
when target state changes before or during Retry.

Before Retry approval, the source-job snapshot must be `retryable`, its
`contentSnapshotRetainUntilUtc` must not have passed, disposition must remain
`scheduled`, and the approved remaining files/rows must be the fresh exact DB-
reconciled still-absent subset of the entire prior attempted snapshot subset,
not a worker cursor remainder. The human-approved `actionMaxDurationSeconds`
plus exact `snapshotDispositionMarginSeconds` must fit before both the target DB
binding validity and snapshot retention deadlines, and the action lease plus
that margin must end no later than `min(targetDbBindingValidUntilUtc,
contentSnapshotRetainUntilUtc)`. One random unique `actionMutationId` must be pre-reserved in the
immutable approval and claimed with one target-fenced DB mutation lease
atomically with the retry action.
The protected `retryReconciliationRecordId` must be `available`, unexpired, and
bound to the source action/mutation outcome, snapshot, entire attempted subset,
private exact still-absent subset, safe counts, observation time, deadline, and
the same consumed `targetIdentityPreparationApprovalId` and protected exact
`targetDbBindingId`/state/validity/evidence. The binding must be `retryable`,
unexpired, and revalidated on the authoritative target DB session before any
reconciliation or mutation read.
The same `targetOperationFenceId` must be globally `idle` with upload branch
`retryable`, no Delete consumer, and the exact next generation/evidence bound in
the Retry approval; Retry claims it atomically with approval/snapshot/record/job.
That record is the `actionApprovedAbsentSetBindingId` for Retry and binds exact
`actionApprovedAbsentKeyCount`; neither physical-row nor file count may replace
the distinct-key count.
The same exact-target singleton `targetGlobalCoordinatorId` must name this chain
fence as sole owner in `chain_ready`; Retry atomically claims its exact global
generation/evidence with the chain fence, approval, snapshot, record, and job.
Its source action's `retryReconciliationCreationState` must be
`record_available`, uniquely bound to that one record, and its encrypted private
subset disposition must be `scheduled` with retention no later than snapshot
retention. The creation evidence must bind the exact eligible source action/
failure class, owner claim id, monotonic fence, and creation expiry used by the
successful publication CAS. Retry creation
must claim it atomically with the approval/snapshot/
job/lease, transition the entitlement to `record_consumed`, and keep the subset
inside the same protected boundary until terminal Retry disposition.
Deterministic coverage must exercise target-binding expiry immediately before,
at, and after Retry claim, marker preparation, mutation, outcome reconciliation,
and whole-attempt publication CAS, plus rejection when the lease or publication
deadline exceeds the minimum target-binding/snapshot ceiling.

Required approval wording:

```text
The Retry Failed approval id is <retryApprovalId> and it must be claimed by <retryExecuteByUtc>.
I approve exactly one Retry Failed using protected reconciliation record <retryReconciliationRecordId>, observed at <retryReconciliationObservedAtUtc> and claimable by <retryReconciliationExecuteByUtc>, for upload job <jobId> with freshly reconciled still-absent files <remainingFiles> and physical rows <remainingRows> from the entire prior attempted subset, preserving root failure class <rootFailureClass>.
That reconciliation record is the protected approved-absent set binding <actionApprovedAbsentSetBindingId> with distinct keys <actionApprovedAbsentKeyCount>.
This approval is for package sourceCommit <sourceCommit>, operator PC class <operatorPcClass>, source alias <sourceAlias>, and source class <sourceClass>.
It binds the same pre-existing trusted target baseline <trustedTargetBaselineId> in verified/non-revoked state <trustedTargetBaselineState>, privacy-safe alias <trustedTargetAlias>, and safe evidence <trustedTargetBaselineEvidenceId> used by Preview/source action/reconciliation.
It binds protected target operation fence <targetOperationFenceId> in chain state idle, upload branch retryable, with exact generation <targetOperationFenceGeneration> and safe evidence <targetOperationFenceEvidenceId>. Retry creation must atomically claim that generation for consumer retry; any Delete owner or stale/terminal generation must fail.
It binds exact-target singleton coordinator <targetGlobalCoordinatorId>, sole owner fence <targetOperationFenceId>, state chain_ready, empty consumer, exact generation <targetGlobalCoordinatorGeneration>, and safe evidence <targetGlobalCoordinatorEvidenceId>. Retry creation must atomically claim both generations for consumer retry; any different Preview-chain owner or concurrent target consumer must fail.
The approved exact operational DB target comes from consumed preparation approval <targetIdentityPreparationApprovalId>, completed by <targetIdentityPreparationExecuteByUtc>, and is protected binding <targetDbBindingId> in state <targetDbBindingState>, valid only until <targetDbBindingValidUntilUtc>, with safe evidence <targetDbBindingEvidenceId>. It must match Preview, the source action, reconciliation record, marker, and authoritative Retry transaction.
It is bound to immutable content snapshot <contentSnapshotRecordId> and atomic snapshot binding evidence <atomicSnapshotBindingEvidenceId> from the source job.
That snapshot may be read only until <contentSnapshotRetainUntilUtc>; this approval does not authorize snapshot deletion or extend retention.
The action maximum duration is <actionMaxDurationSeconds> seconds and the required disposition margin is <snapshotDispositionMarginSeconds> seconds. Retry creation must atomically create one unrenewable snapshot action lease whose expiry is claim time plus that duration and whose expiry plus that margin is no later than both <targetDbBindingValidUntilUtc> and <contentSnapshotRetainUntilUtc>, and claim the pre-reserved <actionMutationId>.
The random unique actionMutationId above is pre-reserved in this immutable approval and may only be claimed with this approval, reconciliation record, snapshot, exact subset, duration, margin, lease, and retry action.
As part of that one Retry action, I approve creation of exactly one target-side prepared outcome/fence marker for the same actionMutationId before any all_metrics write; it authorizes no other DB mutation. Every retry write and the prepared-to-committed marker transition must share one authoritative target transaction; a guarded prepared-to-aborted finalization may occur only after non-commit is authoritative.
That transaction must first revalidate the exact target identity and unexpired target binding using the authoritative target DB clock, then serializably revalidate every key in the protected still-absent set, use canonical key fences honored by every application writer and conflict-rejecting conditional inserts, and commit only if the exact inserted keyset/count equals the binding. Any expired/substituted target, preexisting/concurrent key, or mismatch must roll back every action all_metrics write without overwrite and require a fresh whole-attempt reconciliation and approval.
I approve bounded read-only target-outcome reconciliation for that same actionMutationId within this window and, only if its immutable aborted marker is finalized and observed before lease expiry, exactly one whole-attempt exact DB reconciliation plus a new protected retry-reconciliation evidence record. Timeout, response loss, or lease expiry must become commit_unknown_blocked unless the immutable target marker proves committed or aborted/complete rollback.
That reconciliation must atomically claim the source action's unique single-use creation entitlement before any DB read, durably recording and binding source action class retry, its safe terminal failure class, an owner claim id, monotonic fence, and absolute publication deadline no later than the source lease, target-binding validity, and snapshot boundaries. Publication must compare-and-set that exact eligible action/failure class, unexpired token/fence, the same unexpired target binding, and current rollback/snapshot/disposition state; invalidation advances the fence, so a delayed publisher cannot succeed. Duplicate or response-loss recovery may return only the same record. Its exact private subset must remain owner-only, tamper-evident, per-record encrypted, use the named snapshot retention deadline as its non-extendable access ceiling, and be cryptographically disposed earlier on terminal Retry, invalidation, expiry, or snapshot disposition.
This approval does not approve Start Upload, Delete, Settings save, or feature gate enablement.
```

Evidence to record:

- original job id;
- Retry approval id, deadline, and terminal state;
- retry reconciliation record id/state/observation/deadline plus source action/
  mutation/outcome binding and safe attempted/still-absent counts;
- retry reconciliation source action/failure class, creation state/owner claim id/fence/creation expiry/
  evidence id and private-subset retention/disposition state/evidence id;
- protected content snapshot record id/state, retention deadline, disposition
  state, `snapshotDispositionEvidenceId`, and atomic snapshot binding evidence
  id;
- action maximum duration, disposition margin, snapshot action lease id/expiry/
  terminal state, action mutation id/outcome/evidence id;
- protected approved-absent set binding id/distinct-key count and target absence-
  revalidation evidence id;
- trusted target baseline id/alias/state/evidence, target-identity preparation
  approval id/state/deadline, and protected exact target DB binding id/state/
  validity/evidence id;
- target operation fence id/chain state/upload branch/Delete branch/consumer/
  generation/evidence;
- retry job id or retry event id;
- remaining row count;
- retryable file list summary without raw operational paths;
- accepted/upserted row count;
- audit and job event evidence.

A succeeded Retry with no remainder requires snapshot state `completed`,
disposition `disposed`, and safe disposition evidence. Any failed disposition
blocks cutover and further snapshot preparation.

Rollback:

- preserve original and retry job evidence;
- do not run broad DB cleanup;
- if retry fails, stop and investigate before another retry.

## Delete Preflight-Only Approval Gate

Operational delete preflight is a bounded DB read plus protected local-state/
audit write. It is not covered by the later hard-delete approval because that
approval must be constructed from the preflight output. It requires its own
immutable/authenticated, expiring, single-use `deletePreflightApprovalId` before
any preflight call.

The preflight approval binds the accepted package commit/label/checksum,
operator PC/source alias/class, latest Preview run, DB target class, opaque
protected exact `targetDbBindingId`, expected schema class, exact selected item
count, opaque protected selection-request binding id, and
`deletePreflightExecuteByUtc`, human-supplied
`deletePreflightCompleteByUtc`, exact read-only observed source bytes, human-supplied
`deleteRecoverySnapshotMaxBytes` and `deleteRecoverySnapshotRetainUntilUtc`,
protected capacity evidence, and an approved owner-only confidentiality class.
It authorizes exactly one protected exact-byte Delete source-provenance snapshot before
the preflight DB read and exactly one preflight run, and no DB
mutation, hard delete, reconcile, Preview, upload, retry, Settings save, runtime
lifecycle, cleanup, LAN, or deployment.

```text
The delete-preflight approval id is <deletePreflightApprovalId>; it must be claimed by <deletePreflightExecuteByUtc>, and protected source-provenance-snapshot plus preflight-result publication must complete by <deletePreflightCompleteByUtc>.
I approve exactly one read-only operational delete preflight for package <packageSourceCommit>/<packageLabel>/<zipSha256>, Preview <previewRunId>, operator PC <operatorPcClass>, source <sourceAlias>/<sourceClass>, DB target <dbTargetClass> anchored to pre-existing trusted baseline <trustedTargetBaselineId> in verified/non-revoked state <trustedTargetBaselineState>, privacy-safe alias <trustedTargetAlias>, and safe evidence <trustedTargetBaselineEvidenceId>, from consumed target-identity preparation approval <targetIdentityPreparationApprovalId> completed by <targetIdentityPreparationExecuteByUtc>, with protected exact binding <targetDbBindingId> in state <targetDbBindingState>, valid only until <targetDbBindingValidUntilUtc>, safe evidence <targetDbBindingEvidenceId>, and target operation fence <targetOperationFenceId> in chain state idle with Delete branch delete_preflight_ready, exact generation <targetOperationFenceGeneration>, safe evidence <targetOperationFenceEvidenceId>, expected schema <schemaClass>, selected items <selectedItemCount>, and protected selection-request binding <selectionRequestBindingId>.
It also binds exact-target singleton coordinator <targetGlobalCoordinatorId>, sole owner fence <targetOperationFenceId>, state chain_ready, empty consumer, exact generation <targetGlobalCoordinatorGeneration>, and safe evidence <targetGlobalCoordinatorEvidenceId>. Preflight creation must atomically claim both generations for consumer delete_preflight; any different Preview-chain owner or concurrent target consumer must fail.
Before any source copy or preflight DB read, this approval permits creation of exactly one owner-only encrypted immutable Delete source-provenance snapshot <deleteRecoverySnapshotId> and protected exact-byte content binding <deleteRecoveryContentBindingId>. The reviewed source scope is the selected files/items above, observed bytes are <deleteRecoveryObservedBytes>, the non-inferred approved ceiling is <deleteRecoverySnapshotMaxBytes>, protected capacity evidence is <deleteRecoveryCapacityEvidenceId>, the approved confidentiality/access class is <deleteRecoveryConfidentialityClass>, and bytes may be read only until <deleteRecoverySnapshotRetainUntilUtc>. Every selected entry must remain inside the canonical approved source root, with no symlink/junction/reparse-point/hard-link ambiguity at any path component; copy, private digest, and parse must use the same stable opened-handle identity. Any root escape, link swap, or handle-identity change disposes partial bytes and stops before DB read. Creation must atomically bind the snapshot to this approval/Preview/selection/source/coordinator/fence, privately verify exact bytes, file boundaries, metric values and parsed keys, and never reuse the disposed upload snapshot. Preflight and Delete/reconcile must read this snapshot only and never reopen the operational source. This source snapshot proves provenance and selected keys only: it is not an exact DB rollback image and cannot make rollbackReadiness true. Preflight must separately report whether the future protected target-side DB-before-image schema/complete-column-set/capacity/confidentiality contract is ready, but it must not create a before-image or mutate the DB. Invalidation, blocked/expired preflight, or retention expiry pre-authorizes automatic per-record key destruction plus verified byte removal. After a resolved Delete, it remains encrypted in awaiting_recovery_disposition together with any committed DB before-image until a separate immutable single-use early-disposition approval atomically authorizes accept_delete_and_dispose for both, a separately scoped restore approval authorizes DB-before-image restore_then_dispose, or the approved retention deadlines trigger automatic cleanup; all unrelated/new mutations are blocked while unresolved, and only that exact separately approved recovery action may run before disposal. Disposal failure blocks and alerts.
This approval permits only that preflight DB read and its protected local evidence/audit write. It does not approve hard delete, reconcile, Preview, Start Upload, Retry Failed, Settings save, runtime lifecycle, source mutation, cleanup, LAN, or deployment.
```

| Preflight stage | Approval state | Preflight/result state | Required result |
| --- | --- | --- | --- |
| Before preflight | `available` | absent | Every exact binding and deadline is checked; the target-identity preparation approval is consumed and the exact target binding is unexpired and revalidated. |
| Atomic preflight/snapshot creation | `claimed` | being inserted in the same transaction | Both target-global and chain generations are atomically claimed for consumer `delete_preflight`; one durable `deletePreflightClaimId`/monotonic `deletePreflightFence` and one protected source-provenance snapshot owner/record are reserved before source copy/DB read. Concurrent Preview/Start/Retry/Delete or duplicate claims cannot create another preflight/snapshot. |
| Source-provenance snapshot preparation, before DB read | `claimed` | snapshot `preparing` | Copy once under the byte ceiling, privately verify exact-byte digests/file boundaries/metric values/parsed keys, and CAS-publish one immutable `prepared` snapshot/content binding using the exact claim/fence, both deadlines, target binding, coordinator/fence generations, and snapshot state. Expiry, replacement, concurrent change, restart, failure, or late publication advances the fence, invalidates/disposes it, and permits zero DB mutation. |
| Preflight DB read and result publication | `claimed` | snapshot `preflight_bound`; result in progress | Read only the snapshot-derived keys. CAS-publish exactly one `ready_available` or `blocked` result after rechecking the same owner/fence/deadlines/target/coordinator/snapshot state. Response loss returns only the same record without another source copy or DB read. |
| Failure before preflight record commits | `invalid` | absent | Zero operational DB writes; a new approval is required. |
| Exactly one preflight record commits | `consumed` | committed, later `ready_available` or `blocked` | Approval remains consumed despite response loss or later read/evidence failure. A ready result is available to exactly one later delete claim. |
| Duplicate request after commit/response loss | `consumed` | same committed preflight | Return/preserve the existing preflight; never create another. |

The safe preflight output records the approval id/state/claim and completion
deadlines/owner claim/fence,
`deletePreflightId`, safe coarse DB fingerprint, trusted target baseline id/
alias/state/evidence, consumed target-identity
preparation approval id/state/deadline, opaque protected exact
`targetDbBindingId`/state/validity/evidence, target operation fence id/chain
state/upload branch/Delete branch/consumer/generation/evidence, public versioned schema class, opaque protected schema
binding id, selected item/exact key counts,
opaque protected selection/keyset/source-evidence/source-file-signature-set
binding ids, protected Delete source-provenance snapshot/content-binding ids/state/
observed and maximum bytes/capacity/confidentiality/retention/final-disposition/
disposition/evidence, `deleteDbBeforeImagePreparationReadiness`,
`rollbackReadiness=false_pending_atomic_before_image`, rollback limitations, expiry,
safe reason class, and `deletePreflightState`. Only a `ready_available`, unexpired
result may be used to construct the separate complete `docs/171` hard-delete
approval. That result has a protected single-consumer lifecycle
`ready_available -> claimed -> consumed|invalid`. It binds
`consumedByDeleteApprovalId` and `deleteRunId` during the later atomic run-create
transaction and can never regress, be shared, or return to `ready_available`.

Deterministic tests must reject missing/arbitrary/unresolvable, expired,
substituted, replayed, or concurrently claimed preflight approvals; field and
selection-request substitution; multiple preflight creation; response loss;
failure before/after record commit; and any attempt to perform DB mutation.
Pre-commit mismatch/failure must produce zero operational DB writes, and a
duplicate request must resolve only the same `deletePreflightId`. Same-loopback/
same-port local cluster or database replacement and target-binding substitution
must fail before any preflight result is published or any later mutation occurs.
Target-binding expiry immediately before, at, and after preflight claim/query/
result publication, Delete claim/transaction, and same-run reconcile must fail;
every expired-target pre-mutation path produces zero operational DB writes.
Tests must cover zero-target Preview with eligible `already_in_db` items, upload-
snapshot disposal without Delete reuse, concurrent Start-vs-preflight and Retry-
vs-preflight, stale/terminal fence generation, response loss/crash, and proof that
only one operation consumer/result can commit.
They must cover crash/response loss at claim, source copy, snapshot publication,
DB read, and result publication; delayed publishers racing restart/expiry/target-
binding/coordinator/snapshot invalidation; and recovery without a second copy or
DB read. They must also cover equal-size/equal-mtime and same-key/different-
metric-value replacement before/after snapshot publication and before/during
Delete, proof that source values never substitute for different current DB values,
concurrent source writes, byte ceiling/capacity/confidentiality failures,
canonical-root escape and Windows symlink/junction/reparse-point/hard-link plus
opened-handle identity races, blocked/expired preflight, Delete success/failure/
commit-unknown, missing/substituted/expired/replayed/concurrent early-disposition
approval, outcome drift, response-loss idempotency, retention-expiry races, and
cleanup failure, including crash/restart before and after approval claim, key
destruction, byte removal, absence verification, coordinator/fence terminal CAS,
and evidence publication.
Tests must also prove that public/audit/committed evidence exposes only opaque
random binding ids and safe counts/classes; exact material and versioned domain-
separated keyed HMAC integrity data remain owner-only. Legacy unkeyed selection,
keyset, source-evidence, or source-signature digests, private HMACs, and
candidate-enumerable values must never be accepted as public approval/evidence.

## Delete Gate

Already-in-DB hard delete remains exceptional and production-critical. It is
blocked unless production code first implements and deterministically tests an
immutable/authenticated, expiring, single-use delete approval record that is
atomically claimed with exactly one `deleteRunId`. The current `docs/171` record
and wording alone do not satisfy this runtime enforcement requirement. An exact
delete preflight and separate destructive approval are also required.
The current API's source-derived `rollbackReadiness=true` is legacy evidence and
must not satisfy this gate; only the atomic DB-before-image transition defined in
`docs/171` can establish exact rollback readiness.
The target-side recovery store and any supporting schema migration are future
production implementation under a separate approved work package. This document
does not authorize that migration, DB access, or a Delete/restore execution.

Required preconditions:

- fresh Preview evidence for selected `already_in_db` items;
- a protected delete-preflight approval is terminal `consumed` and its exactly
  one bound delete preflight result is `ready_available` and unexpired;
- exact selected item count;
- exact key count;
- protected DB-before-image preparation readiness is true, rollback readiness is
  `false_pending_atomic_before_image` before mutation, and rollback limitations
  are explicitly acknowledged; only the authoritative transaction may set
  rollback readiness true after complete typed capture and revalidation;
- local DB target guard is ready;
- trusted target baseline id/alias/state/evidence, consumed target-identity
  preparation approval id/state/deadline, and protected
  exact target DB binding id/state/validity/evidence match across preflight
  approval/result and the later delete approval; the binding remains unexpired
  through `deleteExecuteByUtc`, `deleteReconcileByUtc`, and
  `deleteDbBeforeImageRetainUntilUtc` and is revalidated with the authoritative
  DB clock inside every delete/reconcile/restore transaction;
- the same target operation fence is owned only by the consumed preflight result
  in `delete_ready`; its exact generation/evidence is atomically claimed for
  consumer `delete` with the delete approval/result/run, and no Start/Retry owner
  or terminal/stale generation exists;
- the same immutable protected Delete source-provenance snapshot/content binding from
  preflight is `preflight_bound`, unexpired, within its approved ceiling, and
  atomically becomes `delete_bound`; no upload snapshot or current source reparse
  can replace it, and Delete/reconcile never reopen the operational source;
- one random unique `deleteMutationId` is pre-reserved in the immutable Delete
  approval and can be claimed only with the exact approval/preflight/run/keyset/
  source-provenance/target-global/chain bindings;
- one random unique `deleteDbBeforeImageId` plus exact content/schema/complete-
  column-set bindings, row count, human-approved byte ceiling, protected capacity/
  confidentiality evidence, and retention deadline are pre-reserved in the same
  immutable approval; the target-side record is created only inside the
  authoritative Delete transaction;
- DELETE privilege preflight is ready;
- no mixed-date whole-item workaround is used;
- package source commit, and zip checksum when `zipCreated=true`, still match
  this document.

Required approval wording:

This is a lifecycle addendum to the complete authoritative field table and exact
approval wording in `docs/171`; it does not replace or shorten that contract.
`deleteApprovalId` below is exactly the same value as `approvalId` in `docs/171`.
The protected approval record must retain every `docs/171` binding, including
package label/checksum, safe coarse DB fingerprint, trusted target baseline id/
alias/state/evidence, target-identity preparation
approval id/state/deadline, protected exact target DB binding id/state/validity/
evidence, delete reconcile deadline, public schema class, protected schema binding id, preflight id,
selection/keyset/source/source-file-signature/Delete-source-provenance-snapshot
and DB-before-image protected binding ids, policy/gate states,
approver/executor, stop condition, and evidence location, plus
`deleteExecuteByUtc` and the single-run lifecycle fields below.

```text
In addition to every exact field and sentence required by docs/171, including trusted target baseline id/alias/state/evidence, target-identity preparation approval id/state/deadline, target DB binding id/state/validity/evidence, target operation fence id/chain and branch states/consumer/generation/evidence, and <deleteReconcileByUtc>, the protected delete approval id/approvalId is <deleteApprovalId> and it must be claimed by <deleteExecuteByUtc>.
The ready delete-preflight result <deletePreflightId> is initially ready_available and may be claimed and consumed only by this <deleteApprovalId> and the one deleteRunId generated in the joint claim transaction.
I approve one atomic transaction that claims both this delete approval and that ready preflight result and durably binds both to exactly one generated deleteRunId; no response loss, commit_unknown result, audit/evidence failure, cancellation, reconciliation, or second approval may create or authorize a second run from either record.
The random unique <deleteMutationId> and exact DB before-image <deleteDbBeforeImageId> are pre-reserved in this immutable approval. Before any DELETE, exactly one target-side prepared marker binds this approval/preflight/run, exact keyset/source provenance, before-image content/schema/complete-column-set bindings, target DB binding, and both target-global and chain fence generations. One authoritative target transaction must lock and revalidate every selected row, capture every column's complete typed pre-delete value, record <deleteDbBeforeImageObservedBytes> within <deleteDbBeforeImageMaxBytes>, verify row count <deleteDbBeforeImageRowCount=exactKeyCount>, set rollbackReadiness true, then commit the before-image, exact-key DELETE, and prepared-to-committed marker transition atomically. Missing rows/columns, DB values that differ from source, schema/value drift, unsupported restore semantics, overflow/capacity/confidentiality failure, or concurrent change rolls back to zero DELETE. Aborted may be finalized only after non-commit is authoritative; timeout/response loss is commit_unknown_blocked until marker-first reconciliation proves committed or aborted and a committed marker has the exact recovery_available before-image. Current row presence/delta may never infer the outcome.
```

| Delete stage | Approval state | Preflight result state | Delete run state | Required result |
| --- | --- | --- | --- | --- |
| Before creation | `available` | `ready_available`, exact and unexpired | absent | Every `docs/171` binding and deadline is rechecked, including unexpired exact target binding and reconcile ceiling. |
| Atomic creation transaction | `claimed` | `claimed` | being inserted in the same transaction | The exact `delete_ready` target operation fence generation is claimed for consumer `delete` in this same transaction; concurrent/duplicate/different-approval/Start/Retry claims cannot commit another run. |
| Creation fails before any run commit | `invalid` | `invalid` | absent | Zero DB writes; new preflight and approval are required. Neither record may regress. |
| Exactly one run commits | `consumed` | `consumed`, bound to this approval/run | committed, mutation `not_started` | Both records and the pre-reserved mutation id remain consumed/bound despite response loss, failure, cancellation, audit/evidence failure, or `commit_unknown`. |
| Target marker prepared | `consumed` | same consumed binding | running, mutation `prepared`, before-image `not_created` | Marker binds the exact approval/preflight/run/keyset/source-provenance/before-image/target/coordinator generations before any DELETE. |
| Authoritative Delete transaction commits | `consumed` | same consumed binding | terminal succeeded, mutation `committed`, before-image `recovery_available` | Complete typed before-image, exact DELETE, and marker transition commit atomically; both retained records and both coordinator/fence states become non-advanceable `recovery_disposition_pending`. |
| Non-commit is authoritative | `consumed` | same consumed binding | terminal failed, mutation `aborted` | No approved DELETE committed; retain marker/evidence and keep both coordinator/fence states `recovery_disposition_pending` until final restore/disposal. |
| Duplicate request after commit/response loss | `consumed` | same consumed binding | same committed run | Return or reconcile only the existing run; never create another run. |
| A different approval requests the same preflight result | any | `consumed`/`claimed` by original approval | absent for different approval | Reject before mutation; the preflight result has one consumer. |
| Outcome is `commit_unknown` | `consumed` | same consumed binding | same committed run; mutation `commit_unknown_blocked` | Only marker-first read-only reconcile for that run is allowed. Keep global/chain ownership and every retained record; a committed marker requires the exact `recovery_available` before-image, and row presence/delta cannot prove outcome. |

Deterministic tests must cover every `docs/171` field substitution, expiry,
missing/unresolvable approval, concurrent claims, failure before run commit,
response loss/crash after commit, `commit_unknown`, audit/evidence failure,
cancellation, duplicate request after response loss, and inconsistent approval/
preflight/run states. They must also cover sequential and concurrent attempts to
use one ready result from two delete approvals, run-create failure after either
claim, replay after response loss, and permanent no-regression of both records.
They must cover exact target-binding expiry immediately before/at/after joint
claim, mutation, and reconcile plus same-port target replacement at each boundary.
They must also cover Start-vs-Delete, Retry-vs-Delete, zero-target Preview with
eligible Delete items, terminal-binding replay, stale operation-fence generation,
and crash/response-loss at every claim/terminal transition.
They must cover target marker substitution/tamper, crash before/after its prepare
and before/after atomic Delete commit, response loss followed by external reinsertion
or re-deletion of the same keys, external non-fenced writers, marker-first
reconciliation, duplicate requests, and proof that row presence/delta cannot
misclassify committed versus aborted.
They must also cover DB rows whose keys match the source snapshot while one or
more values differ, updates before/while locks are acquired, every nullable/
default/generated/system column policy, schema/column-set drift, before-image
byte-ceiling/capacity failure, crash before/after before-image insertion, Delete,
marker transition, and commit, committed-marker/before-image mismatch or tamper,
exact restore equality, and disposition racing restore/new operations. Every
pre-commit failure must leave both the selected DB rows and marker outcome
unchanged with no usable partial before-image.
At most one `deleteRunId` may commit. Any mismatch or failure before run commit
must produce zero operational DB writes and invalidate both records; later
uncertainty may use only read-only reconciliation of the same run.

Evidence to record after delete:

- preview run id;
- delete approval id, deadline, and terminal state;
- delete preflight id;
- delete preflight result terminal state, consumed delete approval id, and bound
  delete run id;
- delete run id;
- trusted target baseline id/alias/state/evidence, target-identity preparation
  approval id/state/deadline, and protected exact target DB binding id/state/
  validity/evidence plus delete reconcile deadline;
- target operation fence id/chain state/upload branch/Delete branch/consumer/
  generation/evidence;
- delete mutation id/outcome/evidence id from the target marker;
- Delete source-provenance snapshot/content binding/state/retention/final
  disposition/evidence;
- exact DB before-image id/content/schema/column-set bindings, state, row count,
  byte ceiling, capacity/confidentiality/retention, rollback-readiness transition,
  restore state, and disposition evidence;
- selected item count;
- exact key count;
- deleted row count;
- rollback readiness and limitations;
- `upload.delete_start` and final `upload.delete_*` audit evidence;
- DB delta and attribution evidence when gates are explicitly approved and on;
- whether reconcile is required.

Rollback:

- do not perform broad manual DB deletes, truncates, resets, or Docker cleanup;
- if commit is unknown, run only the approved reconcile path;
- if the marker proves committed, any restore requires a separate immutable
  approval and must use only the retained exact DB before-image; never rebuild
  deleted rows from source CSV or transformed matching-key data;
- if gate-on evidence has been written, preserve `db_delta_evidence` and
  `row_attribution_ledger` rows;
- use feature-gate disablement or fix-forward rather than deleting evidence.

## Stop Conditions

Stop before any mutation when any of these are true:

- package metadata, or zip checksum when `zipCreated=true`, differs from this
  document;
- `main` and `origin/main` do not match the recorded source commit;
- active source class is unexpected;
- the inventory evidence record id, operator PC class, or privacy-safe source
  alias is missing or differs from the exact Preview-only approval;
- `inventoryObservedAtUtc`, `inventoryMaxAgeSeconds`, or `previewExecuteByUtc`
  is missing, the deadline has passed, or the approved maximum age is exceeded;
- the immediately-before-call read-only scan does not produce
  `preCallSnapshotUnchanged=true` for the exact file set, scope, size/mtime
  metadata, counts, package, operator PC, source alias, and source class;
- the stage-specific approval/manifest state differs from the transition table
  in `docs/173`; immediately before Preview claim the manifest-preparation
  approval must be `consumed`, manifest `prepared`, and Preview approval
  `available`;
- an approval/record is missing, expired, tampered, unauthenticated, mismatched,
  regressed, double-claimed, or reused outside its valid stage;
- `manifestPreparationApprovalId` or `previewApprovalId` is missing,
  unresolvable, in a state invalid for the current stage, or differs across
  approval, manifest creation, atomic claim/run, terminal evidence, and final
  sign-off;
- `targetIdentityPreparationApprovalId` is missing/unresolvable/not terminal
  `consumed`, its claim/publication deadline is missing/inferred, its claim or
  publication occurred after that deadline, or its
  package/operator/inventory/manifest/snapshot/target-class binding differs;
- trusted target baseline id/alias/state/evidence is missing, unresolved,
  substituted, revoked, created from the first observation, or differs across
  preparation/Preview/Start/Retry/marker/reconciliation/final evidence; observed
  exact identity was not compared to the owner-only expected baseline identity;
- `targetDbBindingState` is not `prepared` before Preview claim, validity has
  expired or exceeds snapshot retention, or safe `targetDbBindingEvidenceId` is
  missing;
- `manifestPreparationExecuteByUtc` is missing/inferred, exceeds the inventory
  observation plus human-approved maximum age, or preparation claim/completed
  protected publication occurs after it;
- the Preview implementation can verify only metadata such as size and mtime,
  or cannot prove that the bytes verified against the approved content manifest
  are the same bytes parsed by Preview, or cannot prevent record replay;
- the protected immutable snapshot is missing, tampered, mismatched, in the
  wrong lifecycle state, beyond `contentSnapshotRetainUntilUtc`, not protected
  for confidentiality, over the approved byte ceiling, in disposition, or
  Start/Retry would reopen the operational source;
- snapshot preparation lacks protected capacity/access-control evidence or exact
  human acknowledgement that a full confidential copy is created and
  automatically disposed, or disposal cannot destroy the per-snapshot key,
  remove/verify the byte file, record `snapshotDispositionEvidenceId`, and block
  new preparation after failure;
- target-identity preparation approval id/state/deadline or protected exact
  `targetDbBindingId`/state/validity/evidence is missing, unresolved, substituted,
  expired, relies only on safe loopback/port/target/readiness classes, or differs
  across Preview/Start/Retry/marker/reconciliation/final evidence; exact target
  identity and unexpired validity are not revalidated on the same authoritative
  DB session/transaction before every query/write; or an action lease/
  reconciliation deadline exceeds the minimum target-binding/snapshot ceiling;
- target operation fence id/chain or branch state/consumer/generation/evidence
  is missing, substituted, stale, regressed, terminally replayed, or not claimed
  atomically with the stage records; Start/Retry/Delete/preflight can overlap or
  a losing claimant can read/write/publish;
- Start Upload is requested without an implemented/tested protected
  `startUploadApprovalId` lifecycle in state `available`, with exact
  package/operator/source/Preview/count/deadline/snapshot/atomic-evidence/
  target-DB bindings and atomic snapshot-plus-job-create claim with zero DB writes on
  mismatch;
- Retry Failed is requested without an implemented/tested protected
  `retryApprovalId` lifecycle in state `available`, with exact
  package/operator/source/source-job/remaining-count/deadline/snapshot/
  atomic-evidence/target-DB bindings and atomic snapshot-plus-retry-create claim with zero
  DB writes on mismatch;
- Start/Retry lacks human-approved action duration and exact disposition margin,
  one unrenewable target-fenced snapshot lease plus mutation id, or a durable
  target outcome marker atomically committed with all action writes; outcome is
  inferred from timeout/response loss/lease expiry; `commit_unknown_blocked` is
  treated as rollback/retryability; or disposition could race an active/pending
  outcome;
- Start/Retry lacks a protected exact absent-set binding/distinct-key count,
  serializable whole-set transaction-time absence revalidation, canonical fences
  for every application writer, conflict-rejecting conditional inserts, or exact
  committed-keyset verification; target drift can overwrite an existing row or
  fail to roll back every action write;
- Retry scope is a worker cursor/pre-rollback remainder rather than every still-
  absent row from fresh exact DB reconciliation of the entire prior attempted
  snapshot subset after authoritative rollback evidence;
- a Start/Retry mutation id was not pre-reserved in the immutable approval or is
  substituted/colliding/reused, or Retry lacks the exact unexpired protected
  whole-attempt reconciliation record claimed atomically with its action;
- a source action lacks an atomic single-use reconciliation-creation entitlement
  bound to an eligible source action/failure class, Start target-absence drift/
  conflict can claim it or cause any reconciliation DB read/record publication,
  can publish sibling records under concurrency/crash/response loss, or the
  entitlement/record binding regresses or differs from its `actionMutationId`;
- reconciliation publication lacks the exact durable owner claim id, monotonic
  fence, absolute deadline, and CAS recheck of source action/failure-class
  eligibility plus source lease/target-binding/rollback/snapshot/disposition
  state, or a stale claimant can publish after invalidation/expiry;
- a reconciliation record's private exact subset lacks owner-only tamper-evident
  per-record encryption, bounded retention, terminal/invalidation/expiry/snapshot-
  coupled cryptographic disposition, safe evidence, or failure blocking;
- Delete is requested without an implemented/tested protected
  `deleteApprovalId` lifecycle in state `available`, exact preflight/scope/
  count/deadline bindings, and an atomic claim with both the `ready_available`
  preflight result and exactly one `deleteRunId`;
- Delete lacks a pre-reserved unique `deleteMutationId`, exact bound target-side
  prepared marker, atomic DELETE-plus-marker commit, marker-first reconciliation,
  or authoritative terminal outcome evidence; row presence/delta is used to infer
  outcome, or an unknown/tampered marker does not keep the chain blocked;
- Delete lacks a pre-reserved `deleteDbBeforeImageId`, protected exact content/
  schema/complete-column-set bindings, exact row-count/byte-ceiling/capacity/
  confidentiality/retention contract, or an authoritative transaction that
  locks/revalidates current rows and atomically commits their complete typed
  before-image with DELETE and the marker transition;
- Delete preflight is requested without an implemented/tested protected
  `deletePreflightApprovalId` in state `available`, exact package/Preview/DB/
  source/selection/deadline bindings, and an atomic claim with exactly one
  `deletePreflightId`;
- Delete preflight lacks a durable owner claim id, monotonic fence, human claim/
  completion deadlines, or CAS publication rechecks; a crash/restart/delayed
  worker can copy/read/publish twice or after target/coordinator invalidation;
- a delete preflight result is not `ready_available`, unexpired, and unconsumed,
  or it could be claimed by two approvals/runs, regress after failure, or be
  consumed without atomically binding `consumedByDeleteApprovalId` and
  `deleteRunId`;
- the exact-target singleton coordinator is missing/stale/substituted, does not
  serialize every Preview chain and Delete/Start/Retry claim, or can advance from
  invalidating/disposal-failed/commit-unknown state;
- the owner-only immutable Delete source-provenance snapshot/content binding is missing,
  not exact-byte/metric verified before DB read, over ceiling, under-capacity,
  unprotected, expired, source-reopened, reused from upload, not retained through
  marker outcome/final recovery disposition, or lacks key-first verified disposal
  and failure blocking;
- an early Delete recovery-snapshot disposal lacks a protected expiring single-
  use approval atomically bound to both the exact source-provenance snapshot and
  DB before-image/content/schema/column bindings plus marker/outcome/coordinator/
  deadlines, or a restore lacks its own separately scoped approval and exact
  before-image-only restore/equality contract;
- source CSV, metadata, matching keys, or transformed values are used to claim
  rollback readiness; `rollbackReadiness` becomes true before exact DB before-
  image capture; a committed marker lacks a matching `recovery_available` before-
  image; or missing rows/columns, schema/value drift, unsupported restore
  semantics, overflow, capacity failure, or concurrent change can still DELETE;
- a resolved Delete can terminalize/release the target-global coordinator or
  chain fence before exact source-provenance and DB-before-image restore/disposal
  are both terminal, or early/
  expiry disposal/restore fails to CAS the same `recovery_disposition_pending`
  owner/generations and block a concurrent new Preview/Start/Delete;
- a Delete approval/evidence path publishes deterministic selection/keyset/
  source/signature digests or private keyed HMACs instead of opaque random
  protected binding ids, or exact material/integrity data is not owner-only;
- Delete preflight/delete/reconcile relies on the coarse DB fingerprint rather
  than one protected exact `targetDbBindingId`, or a same-port instance/database
  replacement or binding substitution is not rejected before DB access/write;
- fresh read-only inventory was not run, is stale, or did not produce observed
  file count and approved physical row ceiling;
- file count or row limit is a user guess, an earlier-run value, a long-term
  default, or blanket approval for future folder growth;
- row counts differ between UI, API, and approval text;
- audit logs cannot be read;
- local token protection is not active for protected writes;
- Supabase local runtime status is unknown for DB-dependent actions;
- the request bundles Preview, Start Upload, Retry Failed, or Delete into one
  broad approval;
- the request asks for reset, cleanup, Docker cleanup, LAN, delete UI expansion,
  feature-gate enablement, or deployment.

## Next Decision

Current decision: hold all mutating actions.

The next safe action is a separately authorized production implementation and
test work package for atomic content-manifest/snapshot binding retained through
Preview, Start, and Retry, followed by package
rebuild and verification. Only after that prerequisite passes may the inventory
be refreshed. A separately controlled pre-provisioned verified target baseline
must already exist; then protected manifest preparation may be separately
approved/reviewed, read-only target-identity preparation separately approved and
its exact-match opaque result human-reviewed, and only then may the later exact
Preview-only approval be requested. This gate does not authorize baseline
provisioning/rotation. Start Upload, Retry Failed,
and Delete remain separately gated even if a later Preview succeeds.
