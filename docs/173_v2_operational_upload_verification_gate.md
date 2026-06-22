# V2 Operational Upload Verification Gate

Date: 2026-06-22 Asia/Seoul

Status: `deferred_no_operational_upload`

## Purpose

This document defines the V2 item 1 gate for operational upload verification.

It does not approve Upload Preview, Start Upload, Retry Failed, Delete,
Settings save, feature-gate enablement, Supabase reset/cleanup, Docker cleanup,
LAN exposure, deployment, operational DB writes, or source-file mutation.

The executable approval wording remains in
`docs/164_operator_data_mutation_safety_gate.md`. This document defines the
evidence record that must exist before item 1 can move from `Deferred` to
completed evidence.

## Plain-Language Rule

Operational upload verification is not "run upload and see if it works."

It is a four-step evidence chain:

1. read-only inventory precheck;
2. exactly one approved Preview-only run;
3. exactly one separately approved Start Upload, only if Preview proves target
   rows;
4. exactly one separately approved Retry Failed, only if a failed or retryable
   job remains and a new approval names the remaining physical rows.

If any step cannot produce safe evidence, stop. Do not replace missing evidence
with a guess, screenshot memory, old approval, old package source commit, DB
cleanup, or duplicate rerun.

## Required Evidence Record

Before any Preview-only approval is requested, create or identify a safe
evidence record location. The record may be a committed sanitized markdown file
or an internal append-only operator record. It must not be an editable chat
message or mutable issue/comment body by itself.

The record must not contain raw operational source paths, filenames, CSV row
content, raw `(timestamp, device_id)` keys, raw SQL, DB URLs, tokens,
Authorization values, JWTs, credentials, internal URLs, or secret values.

Minimum fields:

| Field | Meaning |
| --- | --- |
| `packageSourceCommit` | Source commit from accepted package metadata. |
| `packageLabel` | Safe package label. |
| `zipSha256` | Required when `zipCreated=true`; otherwise `not_applicable`. |
| `sourceClass` | Safe class such as `drive_letter`, `network`, or `mounted`; never a raw path. |
| `inventoryObservedFiles` | Observed file count from fresh read-only inventory. |
| `inventoryApprovedPhysicalRowsCeiling` | Approved physical row ceiling from the same inventory. |
| `inventoryEvidenceHash` | Safe hash or record id for the inventory evidence. |
| `previewApprovalId` | Approval id for exactly one Preview-only run. |
| `previewRunId` | Filled only after Preview-only runs. |
| `previewStatus` | Preview result class. |
| `previewTargetRows` | Target-only rows eligible for Start Upload. |
| `previewPartialOverlapRows` | Partial-overlap rows, separate from target-only rows. |
| `previewRiskyCount` | Risky files/items count. |
| `dbStatusClass` | Safe DB status class, not a raw DB URL. |
| `targetClassStatus` | Safe config target-class status. |
| `runtimeReadinessClass` | Safe Supabase API/DB/Edge readiness class. |
| `edgeAuthClass` | Safe Edge auth boundary class. |
| `startUploadApprovalId` | Required only when Start Upload is separately approved. |
| `approvedTargetRows` | Exact target-only rows in Start Upload approval. |
| `uploadJobId` | Filled only after Start Upload creates a job. |
| `acceptedRowsClass` | Accepted/upserted row count or safe failure class. |
| `retryApprovalId` | Required only when Retry Failed is separately approved. |
| `remainingPhysicalRows` | Exact remaining physical rows for Retry Failed approval. |
| `auditEvidence` | Safe audit ids/counts for preview/start/retry/failure. |
| `dbDeltaEvidence` | Required when the gate is explicitly approved and on. |
| `rowAttributionEvidence` | Required when the gate is explicitly approved and on. |
| `finalDecision` | `no_upload`, `upload_succeeded`, `failed_preserved`, or `blocked`. |

## Phase 1: Read-Only Inventory

Inventory is not Upload Preview. It must not create a Preview run, write local
state, write audit rows, query or mutate operational DB rows, call Edge
functions, change Settings, or alter source files.

Inventory may record only:

- source class;
- observed file count;
- physical data-line count or approved conservative physical row ceiling;
- inventory evidence hash or record id;
- safe go/no-go reason classes.

`fileCount` and `rowLimit` in the Preview-only approval must come from this
fresh inventory. They must not be guesses, old run values, long-term defaults,
or blanket approval for future folder growth.

## Phase 2: Preview-Only

Preview-only remains blocked unless the exact wording in `docs/164` is supplied
for the accepted package metadata.

After Preview-only, record:

- preview run id;
- source class;
- run status;
- total files and status counts;
- target-only rows;
- partial-overlap rows;
- already-in-DB count;
- risky count;
- DB status class;
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

The approved row count must be target-only rows. Partial-overlap rows are not
included unless a later approved flow explicitly changes that policy.

After Start Upload, record:

- approval id;
- preview run id;
- upload job id;
- approved target-only rows;
- job final status;
- file counts;
- processed/uploaded/accepted rows;
- audit evidence for start and final status;
- DB delta evidence when explicitly approved and on;
- row attribution evidence when explicitly approved and on;
- whether failure requires investigation or Retry Failed.

If Start Upload fails after partial DB mutation, preserve job, audit, DB delta,
and row attribution evidence. Do not run Retry Failed or DB cleanup without a
separate approval.

## Phase 4: Retry Failed

Retry Failed is not automatic rollback. It is a new upload action with its own
approval.

Before Retry Failed, record:

- source job id;
- terminal failed or retryable state;
- retryable file count summary without filenames;
- remaining physical rows;
- reason class for retry eligibility.

After Retry Failed, record retry job id or retry event id, accepted rows, final
status, audit evidence, and whether any unresolved failure remains.

## Stop Conditions

Stop before any operational upload mutation when any of these are true:

- package metadata or checksum differs from the accepted package record;
- inventory is missing, stale, guessed, or broader than the requested approval;
- source class differs from approval;
- raw operational path, filename, key, DB URL, token, credential, raw SQL, or
  secret would be written into evidence;
- Preview is not fresh, latest, succeeded, and DB-reachable;
- risky count is greater than zero;
- target-only rows differ across UI, API, and approval text;
- target-class or runtime readiness is not ready;
- Edge auth class is not ready for the current function auth mode;
- local token protection is not active for protected writes;
- audit evidence cannot be read after a run;
- request bundles Preview, Start Upload, Retry Failed, Delete, Settings save,
  feature-gate enablement, reset, cleanup, LAN, or deploy.

## V2 Completion Interpretation

Item 1 can be considered completed only for the scope actually evidenced:

- `no_upload` if fresh inventory and Preview-only prove there are no target
  rows and no upload mutation ran;
- `upload_succeeded` if Start Upload is separately approved, runs exactly once,
  and post-run evidence is preserved;
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
