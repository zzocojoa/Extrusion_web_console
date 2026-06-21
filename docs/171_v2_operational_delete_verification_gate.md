# V2 Operational Delete Verification Gate

Date: 2026-06-22 Asia/Seoul

Status: `deferred_no_operational_mutation`

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

The approval record must not contain raw operational source paths, filenames,
CSV row content, raw `(timestamp, device_id)` keys, raw SQL, DB URLs, tokens,
Authorization values, JWTs, credentials, internal URLs, or secret values.

## Required Approval Fields

Every operational delete approval record must include:

| Field | Required value |
| --- | --- |
| `approvalId` | Stable safe id for the approval record. |
| `packageSourceCommit` | Exact package source commit approved for the run. |
| `packageLabel` | Package label or safe package id, without raw local path. |
| `zipSha256` | Required when `zipCreated=true`; otherwise `not_applicable`. |
| `dbTargetClass` | Safe target class such as `local_supabase_operator_db`, not a raw DB URL. |
| `dbFingerprintHash` | Safe DB fingerprint hash from preflight evidence. |
| `schemaFingerprintHash` | Safe schema fingerprint hash proving the expected `all_metrics` exact-key contract. |
| `previewRunId` | Exact Preview run id used for selection. |
| `deletePreflightId` | Exact ready delete preflight id. |
| `selectedAlreadyInDbItems` | Exact selected `already_in_db` item count. |
| `exactKeyCount` | Exact selected key count approved for delete. |
| `selectionHash` | Safe selection hash. |
| `keysetHash` | Safe keyset hash. |
| `sourceEvidenceHash` | Safe source evidence hash without raw paths or filenames. |
| `sourceFileSignatureSetHash` | Safe hash proving selected source files are present, signature-stable, and parse to the same exact keyset. |
| `deletePolicy` | Must be `already_in_db_exact_key` unless a later approved policy gate says otherwise. |
| `noUndoAcknowledgement` | Explicit acknowledgement that the app has no undo. |
| `rollbackReadiness` | Must be `true`. This is not replaceable by acknowledgement. |
| `rollbackLimitationAcknowledgement` | Explicit acknowledgement that recovery requires fresh Preview plus separately approved Start Upload from unchanged source files, and only if those files remain unchanged later. |
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
I approve exactly one operational hard delete for approval <approvalId>.
The approved package sourceCommit is <packageSourceCommit>, package label is <packageLabel>, and zip SHA-256 is <zipSha256>.
The approved DB target class is <dbTargetClass>, DB fingerprint hash is <dbFingerprintHash>, and schema fingerprint hash is <schemaFingerprintHash>.
The approved scope is preview run <previewRunId>, delete preflight <deletePreflightId>, selected already_in_db items <selectedAlreadyInDbItems>, and exact keys <exactKeyCount>.
The approved delete policy is <deletePolicy>.
The approved selection hash is <selectionHash>, keyset hash is <keysetHash>, source evidence hash is <sourceEvidenceHash>, and source file signature set hash is <sourceFileSignatureSetHash>.
Rollback readiness is true, and the selected source files are present, signature-stable, and parse to the same exact keyset.
I understand this delete has no app-level undo and recovery requires a fresh Preview plus separately approved Start Upload from unchanged source files, and only if those files remain unchanged later.
The approved V2 gate states are v2RowAttributionEnabled=<v2RowAttributionEnabled>, v2DbDeltaEvidenceRequired=<v2DbDeltaEvidenceRequired>, rowAttributionHmacAvailabilityClass=<rowAttributionHmacAvailabilityClass>, and featureGateChangeApproved=<featureGateChangeApproved>.
The named approver is <approver>, the named executor is <executor>, and the stop condition is <stopCondition>.
The post-run evidence report will be recorded at <evidenceReportLocation>.
This approval excludes <approvalExclusions>.
This approval does not approve Upload Preview, Start Upload, Retry Failed, Settings save, feature gate enablement, Supabase reset/cleanup, Docker cleanup, LAN, deploy, arbitrary SQL delete, broad cleanup, or any delete outside the exact scope above.
```

## Pre-Mutation Checklist

Before mutation, the executor must prove all of these:

- approval record exists in an approved storage location;
- package metadata and checksum match the approval record;
- current local branch and operator package source commit match the approved
  source commit expectation for the run;
- Preview is fresh, latest, succeeded, and DB-reachable;
- selected Preview items are still `already_in_db`;
- delete preflight is ready and unexpired;
- selected item count, exact key count, selection hash, keyset hash, and source
  evidence hash match the approval record;
- source files are present, signature-stable, and parse to the same exact
  keyset recorded in `sourceFileSignatureSetHash`;
- rollback readiness is true and the rollback limitation is explicitly
  acknowledged in the approval record;
- local token protection is active for protected writes;
- audit logs are readable and append-only behavior is intact;
- DB target guard and schema fingerprint still match;
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
- delete run id;
- delete policy;
- selected item count;
- exact key count;
- deleted row count;
- DB target class and fingerprint hash;
- schema fingerprint hash;
- selection hash;
- keyset hash;
- source evidence hash;
- source file signature set hash;
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
- raw internal URLs.

## Reconcile And Failure Handling

If the delete returns `commit_unknown`, `db_delta_mismatch`,
`evidence_write_failed`, or `reconciliation_failed`, stop destructive work.

Allowed follow-up without a new destructive approval:

- read-only investigation of safe state;
- the approved reconcile endpoint for the same delete run;
- preserving audit, DB delta, and row attribution evidence;
- documenting the failure and next stop condition.

Not allowed as rollback:

- broad manual DB delete;
- truncate;
- reset;
- Supabase cleanup;
- Docker cleanup;
- deleting audit, DB delta, row attribution, or delete run evidence.

## V2 Completion Interpretation

An operational delete can count as V2 operational delete verification only when:

- it uses the exact approval record above;
- it stays inside the current selected `already_in_db` exact-key contract, or a
  later approved delete-expansion policy;
- it records the required post-run evidence report;
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

- approval record is missing, stale, edited after approval, or not stored in an
  approved location;
- package metadata or checksum differs from the approval record;
- DB target class or fingerprint differs from the approval record;
- schema fingerprint differs from the approval record;
- selected item count, exact key count, selection hash, keyset hash, or source
  evidence hash differs from the approval record;
- raw paths, filenames, raw keys, DB URLs, tokens, raw SQL, or secrets would be
  printed, committed, or pasted into evidence;
- the request bundles Delete with Preview, Start Upload, Retry Failed, Settings
  save, feature-gate enablement, reset, cleanup, LAN, or deploy;
- an unresolved `commit_unknown` or `reconciliation_failed` blocker exists;
- the operator asks for broad cleanup or arbitrary SQL delete.
