# V2 Scope And Safety Plan

Date: 2026-06-19 Asia/Seoul

Status: `v2_scope_draft_for_approval`

## Purpose

This document defines the proposed V2 scope and the safety gates required before
implementation.

V2 is not a silent continuation of V1. It includes items that change existing
product boundaries, especially delete capability and Multi-user LAN access. Any
item marked as `V2 rescope required` must be explicitly approved before design,
implementation, test execution, rollout, or operator documentation.

This document does not approve code changes, database migrations, production DB
access, destructive tests, LAN exposure, release packaging, branch creation,
commit, push, or PR creation.

## Source Documents Reviewed

- `AGENTS.md`
- `README.md`
- `DESIGN.md`
- `docs/00_product_scope.md`
- `docs/01_development_roadmap.md`
- `docs/151_operator_upload_gate_runbook.md`
- `docs/156_operator_already_in_db_delete_contract.md`
- `docs/157_operator_2026-01-19_delete_execution.md`
- `docs/158_operator_status_language_policy.md`

## Operator Summary

V1 is a localhost-only operator console for Core Ops. V2 may expand the product,
but it must not weaken the safety model that protects upload, delete, audit, and
local Supabase operations.

Plain-language approval points:

- Delete expansion can permanently remove database rows. There is no app-level
  undo.
- Production delete testing must not happen just because a fixture test passed.
  It needs separate approval for the exact operational DB and exact row scope.
- Multi-user LAN changes who can reach the app. It is a security rescope, not a
  port-binding change.
- Row-count evidence must distinguish accepted/upserted rows from actual DB row
  delta.
- Every destructive or mutating action needs actor attribution, audit evidence,
  and a rollback or recovery story before implementation is considered ready.

## V2 Scope

The following items are in proposed V2 scope only after approval of this plan.

| Item | V2 intent | Required handling |
| --- | --- | --- |
| Delete capability expansion | Support safer maintenance beyond the current selected `already_in_db` path. | `V2 rescope required`; admin/maintainer-only by default; no general cleanup UI without separate design approval. |
| Independent DB delta | Show before/after DB row evidence independent of upload API `acceptedRows`. | Must report DB row delta separately from Edge/Supabase accepted/upserted counts. |
| Row-level attribution | Attribute upload/delete effects to a run, actor, source evidence, and audit row. | Must choose a schema-backed or ledger-backed design before implementation. |
| Multi-user LAN access | Allow controlled internal-network access to the web app. | `V2 rescope required`; must pass the LAN Security Gate in this document. |
| Grafana/Vector observability hardening | Improve operational evidence and runtime diagnostics. | Grafana remains separate unless separately re-scoped; logs/metrics must stay sanitized. |

## Out Of Scope

These remain excluded from V2 unless a later approved document explicitly
changes them:

- Cloud Supabase migration.
- Default legacy upload state import.
- Direct port of `uploader_gui_tk.py`.
- Uncontrolled Supabase Management delete UI for operators.
- DB reset, truncate, broad manual cleanup, Docker cleanup, or Supabase lifecycle
  cleanup as a normal troubleshooting path.
- Grafana iframe embedding.
- Any production destructive test without separate operational approval.

## V1 Principle Conflicts

The existing product scope says the web app is localhost-only, Multi-user LAN is
excluded, Cloud Supabase is excluded, and the default legacy GUI state is not
imported.

The table below records where V2 changes require explicit rescope:

| Existing principle | V2 pressure | Decision marker |
| --- | --- | --- |
| Web app access is localhost only. | Multi-user LAN access. | `V2 rescope required`. |
| Multi-user LAN is excluded from V1. | LAN becomes proposed V2 scope. | `V2 rescope required`; blocked until LAN Security Gate passes. |
| Date-scoped delete is maintainer-only. | Delete expansion may tempt general operator cleanup. | Keep maintainer/admin-only unless a later approved UI/runbook changes it. |
| Supabase Mgmt delete UI is excluded. | Admin delete management may be requested. | Admin/maintainer-only control path; no normal operator cleanup UI. |
| Cloud Supabase migration is excluded. | Future remote DB option. | Still out of V2 scope. |
| Legacy upload state import is excluded. | Migration convenience. | Still out of V2 scope. |

## Safety Gates

### Gate 1: Planning Approval

Before implementation starts, approve:

- the exact V2 feature list;
- which items are `V2 rescope required`;
- whether delete expansion includes only admin/maintainer controls or any
  operator-facing UI;
- whether Multi-user LAN is allowed at all;
- the minimum audit evidence required for upload, delete, settings, runtime,
  and LAN actions.

### Gate 2: Design Review

Before code changes, produce a technical design covering:

- API contracts;
- frontend role and state behavior;
- state DB and Supabase schema impact;
- actor identity model;
- authorization model;
- concurrency controls;
- audit schema and redaction;
- rollback and recovery paths;
- migration plan, if row-level attribution needs schema changes.

### Gate 3: Fixture DB Validation

Any destructive delete behavior must pass disposable fixture DB validation before
operational testing is discussed.

Fixture DB validation must prove:

- wrong DB target blocking;
- missing DELETE privilege blocking;
- exact count mismatch rollback;
- audit-start failure blocking before DB mutation;
- commit-unknown reconciliation;
- source/keyset rebuild failure handling;
- DB count failure handling;
- no raw paths, operational filenames, DB URLs, tokens, Authorization values,
  JWTs, secrets, raw SQL, raw exact keys, or CSV row contents in output.

### Gate 4: Production DB Restricted Approval

Fixture validation does not approve production DB testing.

Operational DB delete or destructive smoke requires a separate approval record
that states:

- the exact DB target class;
- the exact date, row, preview, or key scope;
- expected selected row count;
- rollback limitations;
- no-undo acknowledgement;
- who approved the operation;
- what audit evidence must be captured;
- what stop condition cancels the operation.

Without that record, do not connect to, mutate, or test against operational DB
data.

### Gate 5: LAN Security Gate

Multi-user LAN cannot ship until all of these are true:

- explicit approval that V2 changes the localhost-only product principle;
- backend bind and CORS rules are intentionally designed for LAN, not widened by
  accident;
- authentication is required for every LAN user;
- authorization distinguishes operator, maintainer, and admin actions;
- mutating APIs cannot rely on one shared local token across all LAN clients;
- audit rows include the real actor, role, client context, action, result, and
  safe reason codes;
- concurrency rules prevent two users from starting conflicting Preview, Upload,
  Delete, Settings, or Runtime operations;
- active jobs and recovery blockers are visible to every authorized user;
- session expiry and logout behavior are defined;
- failed auth, denied authorization, and concurrency blocks are audit logged;
- secrets, DB URLs, tokens, raw source paths, raw exact keys, and raw filenames
  are not exposed to LAN clients.

## Delete Policy

V2 delete work must preserve the existing delete contract unless explicitly
re-scoped.

Baseline rules:

- Already-in-DB hard delete remains a production-critical maintenance flow, not a
  cleanup shortcut.
- Delete can target only approved evidence, never arbitrary SQL or arbitrary row
  filters.
- Date-scoped delete remains maintainer-only until frontend controls, operator
  copy, i18n, and runbook approval are separately completed.
- Supabase Management delete UI, if introduced, must be admin/maintainer-only.
- Operator UI must not present destructive DB cleanup as a normal upload fix.
- Start Delete requires typed exact count, no-undo acknowledgement, rollback
  limitation acknowledgement, local DB target proof, and audit-start success
  before DB mutation.
- A failed, unknown, or unresolved delete blocks the next delete until
  reconciliation or explicit recovery is complete.

No-undo approval language must be explicit:

```text
I understand this delete has no app-level undo. Recovery requires fresh Preview
and separately approved Start Upload from unchanged source files, if those files
still exist and still parse to the same exact keys.
```

## Independent DB Delta

V2 must separate these concepts:

- `acceptedRows`: rows accepted/upserted by the upload API path.
- DB row delta: actual database row count difference before and after an
  operation.
- selected exact-key count: exact keyset size approved for delete.
- affected row count: rows actually deleted or reconciled as absent.

Required evidence:

- before count;
- after count;
- expected delta;
- actual delta;
- delta source query class;
- run id;
- audit id;
- actor;
- timestamp;
- safe blocker or discrepancy code when counts disagree.

Raw exact keys, SQL text, source paths, filenames, DB URLs, tokens, and secrets
must not appear in API responses, audit rows, logs, screenshots, or generated
reports.

## Row-Level Attribution

V2 must define how a reviewer can answer:

- which run affected this row;
- which actor approved or started the run;
- which source evidence produced the row;
- which audit row records the decision;
- whether the row was inserted, upsert-accepted, unchanged, deleted, or
  reconciled.

Acceptable design directions:

- schema-backed attribution on operational tables, if a migration is approved;
- sidecar attribution ledger keyed by safe hashes and run ids;
- hybrid model with immutable audit rows plus a queryable attribution ledger.

The existing `all_metrics(timestamp, device_id)` upsert/dedup safety mechanism
must not be weakened.

## Audit Evidence

V2 audit evidence must cover:

- Settings save;
- Upload Preview;
- Start Upload;
- Retry Failed;
- Upload pause/resume/cancel;
- Delete preflight/start/succeeded/failed/blocked/reconciled;
- Local Supabase start/stop;
- LAN login/logout/auth failure/authorization denial;
- concurrency blocks;
- every failed operation.

Audit rows must include safe evidence:

- actor and role;
- action;
- result;
- run/job/preflight ids;
- selected item count;
- expected and actual safe counts;
- DB target class and fingerprint hash;
- source evidence hash;
- reason code;
- recovery blocker state;
- `rawMatchRowsReturned=false` for exact-key operations.

Audit rows must not include:

- raw source paths;
- raw operational filenames;
- CSV row content;
- raw `(timestamp, device_id)` values;
- DB URLs;
- tokens, Authorization values, JWTs, anon keys, service role values, or
  secrets;
- raw SQL;
- raw exception payloads.

## Grafana And Vector Observability

V2 observability can include stronger logs, metrics, and dashboards, but it must
not change the core product boundary without approval.

Requirements:

- Grafana stays separate and linked, not embedded, unless separately re-scoped.
- Vector or similar log collection must redact the same fields as Audit Logs.
- Metrics should report safe counts, durations, status codes, reason codes,
  queue/concurrency state, and recovery blockers.
- Observability must make `acceptedRows` versus DB row delta visible when both
  exist.
- Observability failure must not hide a failed upload, failed delete, or
  unresolved recovery blocker in the app UI.

## Rollback And Recovery

Document-only rollback:

- review `git diff`;
- revert only this document if the scope draft is rejected;
- do not restore unrelated user changes.

Future implementation rollback:

- feature flags or config gates must allow disabling V2 delete expansion and LAN
  access independently;
- database migrations must include forward and rollback plans before merge;
- LAN rollout must be reversible to localhost-only operation;
- delete operations have no app-level undo and must rely on fresh Preview plus
  separately approved Start Upload from unchanged source files;
- unresolved `commit_unknown` or reconciliation failures must block further
  destructive actions until resolved.

## Test And Review Requirements

Minimum checks before V2 implementation merge:

- backend service/API/repository tests for new contracts;
- frontend typecheck and API-mode build when UI changes;
- LAN auth, authorization, audit actor, and concurrency tests;
- fixture DB destructive smoke for delete behavior;
- marker scan for raw paths, operational filenames, DB URLs, tokens,
  Authorization values, JWTs, secrets, raw SQL, and raw exact keys;
- `git diff --check`;
- operator runbook update for any approved mutating flow;
- rollback guide update for any schema or LAN change.

Tests that must not run without separate approval:

- operational DB delete;
- production destructive smoke;
- DB reset or truncate;
- Docker/Supabase cleanup;
- mutation of operational source files.

## Acceptance Criteria

This V2 scope plan is acceptable when all are true:

- fixture DB pre-validation is required before destructive delete evidence;
- production DB testing requires restricted separate approval;
- no-undo acknowledgement is required for destructive delete;
- DB row delta is defined separately from `acceptedRows`;
- row-level attribution is required before implementation;
- Multi-user LAN requires authentication, authorization, audit actor evidence,
  and concurrency control;
- Supabase Management delete controls are admin/maintainer-only;
- Cloud Supabase remains out of scope;
- default legacy state import remains out of scope;
- conflicts with V1 localhost-only and maintainer-only delete principles are
  marked as `V2 rescope required`;
- rollback and recovery conditions are explicit;
- audit redaction rules are explicit.

## Current Decision

Recommended approval posture:

- approve this document as a V2 planning boundary;
- do not approve implementation from this document alone;
- require a separate technical design before any code, migration, LAN, or
  destructive-test work;
- keep V1 operator safety rules active until each V2 rescope item passes its
  own approval gate.
