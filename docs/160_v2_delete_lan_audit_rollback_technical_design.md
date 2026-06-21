# V2 Delete, LAN, Audit, And Rollback Technical Design

Date: 2026-06-19 Asia/Seoul

Status: `technical_design_draft_pre_implementation`

## Purpose

This document turns the V2 scope boundary in
`docs/159_v2_scope_and_safety_plan.md` into an implementation-facing technical
design draft.

It is not an implementation approval. It does not approve code changes,
database migrations, production DB access, destructive smoke tests, LAN
exposure, release packaging, branch creation, commit, push, or PR creation.

The business goal is to let V2 delete, LAN, audit, DB-delta, row-attribution,
and rollback work proceed only after the security and data-loss boundaries are
explicit enough for review.

## Source Documents Reviewed

- `AGENTS.md`
- `README.md`
- `DESIGN.md`
- `docs/00_product_scope.md`
- `docs/01_development_roadmap.md`
- `docs/02_engineering_plan.md`
- `docs/10_audit_logs_plan.md`
- `docs/156_operator_already_in_db_delete_contract.md`
- `docs/159_v2_scope_and_safety_plan.md`

## Current Constraints

V1 remains the active product contract until an approved V2 implementation
changes it.

- Runtime remains a Windows operator PC, WSL/Docker, local Supabase, and a
  browser UI.
- The web app is localhost-only in V1.
- Grafana stays separate and linked, not embedded.
- Cloud Supabase remains out of scope.
- Default legacy GUI state import remains out of scope.
- `all_metrics(timestamp, device_id)` upsert and de-dup behavior must not be
  weakened.
- Already-in-DB exact-key hard delete is a production-critical maintenance flow,
  not a general cleanup tool.
- Date-scoped delete remains maintainer-only.
- Supabase Management delete controls, if introduced, are admin/maintainer-only.
- Dangerous operations must be audit logged and must not fail silently.

The following V2 items are `V2 rescope required`:

- Multi-user LAN access, because it changes the localhost-only product
  boundary.
- Delete capability expansion beyond the current selected `already_in_db`
  contract.
- Any operator-visible general delete or cleanup UI.
- Any production destructive test against operational data.

## Design Summary

Recommended V2 implementation posture:

1. Keep V1 controls as the default.
2. Add independent feature gates for delete expansion and LAN access.
3. Add a V2 operation ledger in the local state DB before expanding
   destructive behavior.
4. Use read-only DB delta evidence as a separate measurement from
   `acceptedRows`.
5. Use row-level attribution through safe hashes and run ids, not raw keys in
   API responses, audit rows, logs, screenshots, or reports.
6. Treat LAN as an authentication, authorization, audit, and concurrency design,
   not as a host bind change.
7. Make rollback paths explicit before any migration or LAN rollout merges.

## Non-Goals

This design does not add:

- Cloud Supabase.
- Default import of legacy `uploader_state.db`.
- DB reset, truncate, broad manual cleanup, Docker cleanup, Docker prune, or
  Supabase lifecycle cleanup as normal troubleshooting.
- Raw SQL UI.
- Normal operator Supabase Management delete UI.
- Grafana iframe embedding.
- Production destructive smoke without a separate written approval record.

## Feature Gates

V2 must ship behind independent gates.

| Gate | Default | Scope |
| --- | --- | --- |
| `v2_delete_expansion_enabled` | `false` | Allows approved delete policies beyond selected `already_in_db`. |
| `v2_date_scoped_delete_ui_enabled` | `false` | Allows only the non-mutating date-scoped delete review shell until role enforcement, executable policy, and runbook approval are complete. |
| `v2_lan_access_enabled` | `false` | Allows non-loopback bind only after LAN Security Gate approval. |
| `v2_row_attribution_enabled` | `false` | Enables attribution ledger writes after schema review. |
| `v2_db_delta_evidence_required` | `true` for new V2 mutations | Requires before/after DB delta evidence where measurable. |

Gate values must come from a reviewed startup/configuration path and be visible
through safe config output, but dangerous gates must not be silently enabled by
a stale ordinary Settings save. The backend startup path must log safe gate
state without printing secrets.

Implementation status as of 2026-06-19: the backend has a default-off
`v2_row_attribution_enabled` gate, keeps the legacy
`row_attribution_writes_enabled` setting as a compatibility alias, and requires
an explicit `row_attribution_hmac_key` before gate-on delete evidence can write
row attribution. The gate is not enabled by default and this document still does
not approve LAN exposure, delete UI expansion, Supabase schema changes, or
operational DB mutation.

Implementation status as of 2026-06-22: the backend exposes default-off
read-only gate state for `v2_delete_expansion_enabled`,
`v2_date_scoped_delete_ui_enabled`, and `v2_lan_access_enabled` through
`GET /api/config`. The date-scoped delete UI gate controls only the
non-mutating review shell. Delete expansion and LAN remain
`enabled=false` with `status=blocked_not_implemented` until their matching
capabilities are implemented. These gates are intentionally not writable
through ordinary Settings save or config JSON keys. Feature-gate enablement
still requires a separate approval and reviewed startup/runtime configuration
change.

## Delete Technical Design

### Baseline Policy

The current delete contract in
`docs/156_operator_already_in_db_delete_contract.md` remains the baseline.

The existing endpoints remain the V1 compatibility contract:

```text
POST /api/upload/delete/preflight
POST /api/upload/delete/jobs
GET  /api/upload/delete/jobs/latest
POST /api/upload/delete/jobs/{deleteRunId}/reconcile
```

V2 may add a delete policy layer, but it must not weaken existing guards.

Recommended V2 policy model:

```text
DeletePolicy
  id
  roleRequired
  allowedSelectionSource
  allowedDbScope
  requiresFixtureEvidence
  requiresProductionApproval
  requiresNoUndoAck
  requiresRollbackLimitAck
  requiresDbDeltaEvidence
  maxSelectionRows
```

Initial allowed policies:

| Policy | Role | Scope | Operator exposure |
| --- | --- | --- | --- |
| `already_in_db_exact_key` | maintainer | selected Preview rows only | existing guarded UI |
| `already_in_db_date_scoped` | maintainer | selected Preview rows narrowed by date | hidden until UI/copy/i18n/runbook approval |
| `admin_maintenance_delete` | admin | separately approved maintenance scope | no normal operator UI |

Forbidden policies:

- arbitrary SQL delete;
- arbitrary table delete;
- broad date cleanup without Preview evidence;
- filename or folder wildcard delete;
- DB reset, truncate, or manual cleanup through the web app.

### Delete Preflight

Every destructive delete path must produce a preflight record before mutation.

Required preflight evidence:

- policy id;
- actor id and role;
- preview run id, when applicable;
- selected item count;
- exact key count;
- selection hash;
- source evidence hash;
- DB target class and fingerprint hash;
- schema fingerprint;
- DELETE privilege result for destructive paths;
- rollback readiness state;
- expected DB delta;
- expiry;
- blocker code if not ready.

Preflight must block if:

- feature gate is disabled;
- actor role is insufficient;
- latest Preview is missing, stale, partial, or DB-unreachable for a DB-backed
  policy;
- any selected item is no longer eligible;
- an active Preview, Upload, Delete, Settings, Runtime, or unresolved recovery
  blocker conflicts with the request;
- DB target is not the approved local target or separately approved production
  target;
- expected count differs from current read-only count;
- rollback readiness is false;
- audit-start cannot be written.

### Start Delete

Start Delete must re-read all eligibility evidence at start time.

The destructive transaction may start only after:

- ready preflight is current and unexpired;
- typed exact-key count matches;
- no-undo acknowledgement is present;
- rollback-limit acknowledgement is present;
- production approval record is present if the target is operational DB data;
- `upload.delete_start` audit row has been written with safe evidence;
- delete run has transitioned to `running`;
- DB target and schema fingerprints still match.

The transaction policy remains all-or-nothing for V2 phase 1. Per-batch commits
are rejected until a separate design defines resumable destructive semantics.

### Reconcile

Reconcile remains SELECT-only against Supabase.

It may update local state and audit rows, but it must not issue temp-table,
insert, update, upsert, delete, truncate, reset, lifecycle, or DDL statements
against Supabase.

Reconcile can classify:

- `reconciled_succeeded`;
- `reconciled_rolled_back`;
- `reconciliation_failed`.

It must not infer success from missing evidence. Source rebuild failure,
selection hash mismatch, DB target drift, schema drift, or DB count failure
finishes as `reconciliation_failed` and keeps destructive operations blocked.

## Production DB Approval

Fixture DB validation is necessary but not sufficient.

Any operational DB destructive test requires a separate approval record with:

- exact DB target class;
- approved date, preview, row, or key scope;
- expected selected row count;
- expected DB delta;
- named approver;
- named executor;
- no-undo acknowledgement;
- rollback limitation acknowledgement;
- stop condition;
- required audit ids and evidence report location.

Without this record, implementation and QA must not connect to, mutate, or test
against operational DB data.

## Multi-User LAN Technical Design

LAN access is blocked until `v2_lan_access_enabled=true` and the LAN Security
Gate is approved.

### Network Boundary

Default V1 behavior remains:

```text
bind host: 127.0.0.1
CORS: same-origin or explicit localhost dev origins
```

V2 LAN behavior must require explicit config:

```text
bind host: configured LAN interface or 0.0.0.0 only after approval
CORS: exact allowlist, no wildcard credentials
API docs: disabled in operator mode unless dev/test override is explicit
```

The implementation must fail closed if LAN is enabled without auth,
authorization, actor attribution, and concurrency controls.

### Authentication

The existing per-run local token is not sufficient for LAN because it represents
one local process, not a human actor.

V2 LAN requires per-user authentication.

Minimum requirements:

- every LAN user has a distinct actor id;
- sessions expire;
- logout invalidates the session;
- failed login attempts are rate limited and audit logged;
- mutating API calls require an authenticated session plus CSRF-safe request
  behavior appropriate for the selected frontend delivery model;
- secrets and tokens are not stored in URL queries, localStorage,
  sessionStorage, launcher logs, backend logs, audit rows, screenshots, or
  generated artifacts.

The final auth mechanism is an open decision. Acceptable design directions:

- local account store in the state DB with memory-hard password hashing;
- Windows-integrated identity if it can be tested and audited locally;
- reverse-proxy identity only if the app still receives a stable actor and role
  claim and rejects missing or ambiguous claims.

### Authorization

Minimum roles:

| Role | Allowed |
| --- | --- |
| `operator` | read Dashboard, Settings read, Upload Preview, Start Upload, Retry Failed, Logs read, Grafana link. |
| `maintainer` | operator actions plus date-scoped delete preflight/start when approved, selected maintenance recovery, local runtime controls. |
| `admin` | maintainer actions plus user/role administration and separately approved admin maintenance delete controls. |

Authorization must be enforced in the backend, not only hidden in the UI.

Denied authorization writes an audit row with:

- actor;
- role;
- action;
- target type;
- safe target id;
- result `blocked`;
- reason code.

### LAN Concurrency

LAN introduces conflicting users. V2 must add a central operation lock model.

Conflicting operation classes:

- Upload Preview;
- Start Upload and Retry Failed;
- Delete Preflight and Start Delete;
- Delete Reconcile;
- Settings save;
- Local Supabase start/stop;
- any future DB maintenance action.

The lock model must store:

- lock id;
- operation class;
- actor id;
- role;
- acquired timestamp;
- expiry or heartbeat;
- related run/job/preflight id;
- visible safe status;
- release reason.

Every authorized user must see active jobs, held locks, and recovery blockers
before starting a conflicting action.

Stale lock recovery is maintainer/admin-only and must be audit logged.

## DB Delta Evidence

`acceptedRows` and DB row delta are different measures.

Definitions:

- `acceptedRows`: rows accepted/upserted by the upload API or Edge path.
- `expectedDelta`: predicted DB row count change for an operation.
- `actualDelta`: after count minus before count.
- `deltaScope`: the bounded read-only count scope used to measure delta.
- `deltaQueryClass`: a safe class label, not raw SQL.

Required V2 delta record:

```text
db_delta_evidence(
  delta_id,
  operation_id,
  operation_type,
  audit_id,
  actor_id,
  role,
  delta_scope,
  delta_query_class,
  before_count,
  after_count,
  expected_delta,
  actual_delta,
  measured_at,
  result,
  reason_code,
  db_target_class,
  db_fingerprint_hash
)
```

Implementation status as of 2026-06-19: the local SQLite state DB now includes
an append-only `db_delta_evidence` sidecar with the logical fields above,
stored as safe ids, counts, class labels, hashes, and `delta_scope_json`. The
sidecar is bootstrapped after `audit_log` and is independent of Supabase schema.
Gate-on upload start/retry, delete start, and delete reconcile paths can link
`audit_id`, `delta_id`, and row attribution rows. Gate-off behavior writes no DB
delta or attribution rows.

Forbidden in delta evidence:

- raw SQL;
- raw exact keys;
- raw source paths;
- raw operational filenames;
- CSV row contents;
- DB URLs;
- tokens;
- Authorization values;
- JWTs;
- anon keys;
- service role values;
- secrets.

If delta cannot be measured, the operation must record why:

- `db_unreachable`;
- `scope_unmeasurable`;
- `operation_failed_before_mutation`;
- `target_guard_failed`;
- `approval_missing`;
- `measurement_error`.

For destructive delete, a mismatched delta is a blocker until reconcile or
manual recovery is explicitly recorded.

Implemented failure mode: when gate-on delete fails before a confirmed DB
commit, the backend records `failed_before_mutation` evidence and leaves the
run `failed`; when the DB delete succeeds but V2 evidence write fails, the
backend leaves the run `commit_unknown` with `evidence_write_failed`. When
gate-on delete returns a row-count delta that does not match the expected
destructive delta, the backend records mismatched DB delta evidence, writes
`unknown_requires_reconcile` attribution evidence, marks the delete run
`commit_unknown`, and returns `db_delta_mismatch` instead of reporting success.
Gate-on delete reconcile writes DB delta and row attribution evidence before
committing a reconciled success state; if that evidence write fails, the run
remains `reconciliation_failed` with `evidence_write_failed`. Gate-on upload
evidence measures exact key presence before and after each accepted upload
batch. If the upload DB delta does not
match the expected exact-key presence delta, the backend records mismatched DB
delta evidence, writes `unknown_requires_reconcile` attribution evidence, and
emits an `upload.evidence_mismatch` event for review. If the gate is on but HMAC
or required DB fingerprint evidence is missing before mutation, start delete is
blocked before the DB delete call and upload is blocked before the Edge call.

## Row-Level Attribution

V2 must let a reviewer answer which run affected a row without exposing raw
business keys in logs or UI.

Recommended phase 1 design: sidecar attribution ledger in the local state DB.

```text
row_attribution_ledger(
  attribution_id,
  operation_id,
  operation_type,
  audit_id,
  actor_id,
  role,
  exact_key_hash,
  source_evidence_hash,
  outcome,
  db_target_class,
  db_fingerprint_hash,
  created_at
)
```

`exact_key_hash` must be derived from a canonical `(timestamp, device_id)` value
using a local installation secret, for example an HMAC. The raw timestamp and
device id must not be stored in the ledger or emitted through API responses.

`source_evidence_hash` must represent normalized source evidence without storing
raw source paths, raw filenames, or CSV row contents.

Allowed outcomes:

- `inserted`;
- `upsert_accepted`;
- `unchanged`;
- `deleted`;
- `reconciled_absent`;
- `blocked`;
- `failed_before_mutation`;
- `unknown_requires_reconcile`.

The ledger must not change the Supabase `all_metrics(timestamp, device_id)`
unique/upsert contract. A future schema-backed attribution design may be
approved separately, but it must include migration, backfill, and rollback plans
before merge.

## Audit Evidence Design

The existing `audit_log` remains append-only.

V2 can extend safe params or add sidecar evidence tables, but must not add audit
update/delete behavior.

Required V2 audit event classes:

- LAN login;
- LAN logout;
- LAN auth failure;
- authorization denial;
- concurrency block;
- delete preflight;
- delete start;
- delete succeeded;
- delete failed;
- delete blocked;
- delete reconciled;
- DB delta measured;
- row attribution recorded;
- rollback or recovery decision recorded.

Required safe fields:

- actor id;
- role;
- action;
- result;
- operation id;
- run/job/preflight id;
- selected item count;
- expected count;
- actual count;
- expected delta;
- actual delta;
- DB target class;
- DB fingerprint hash;
- source evidence hash;
- reason code;
- recovery blocker state;
- client context class for LAN, without raw IPs unless separately approved.

Forbidden fields:

- raw source paths;
- raw operational filenames;
- CSV row content;
- raw `(timestamp, device_id)` values;
- DB URLs;
- tokens;
- Authorization values;
- JWTs;
- anon keys;
- service role values;
- secrets;
- raw SQL;
- raw exception payloads.

Audit write failure before a destructive mutation blocks the mutation.

Audit write failure after a possible commit must move the operation to an
explicit unknown or recovery-required state instead of reporting success.

## State Model

V2 should use an operation-level state model shared across delete, LAN recovery,
DB delta, and attribution evidence.

```text
requested
  -> preflighting
  -> blocked
  -> ready
  -> running
  -> finalizing
  -> succeeded
  -> failed
  -> commit_unknown
  -> reconciling
  -> reconciled_succeeded
  -> reconciled_rolled_back
  -> reconciliation_failed
```

State transitions must be append-evidenced through audit rows or operation
events. Silent transition failure is not allowed.

## Rollback And Recovery

### Document Rollback

If this design draft is rejected:

- review `git diff`;
- remove or revise only this document;
- do not touch code, migrations, state DB, Supabase, Docker, or unrelated user
  changes.

### Implementation Rollback

Future implementation must support:

- disabling delete expansion independently from LAN;
- disabling LAN and returning to localhost-only bind;
- leaving V1 Upload Preview, Start Upload, Retry Failed, Audit Logs, and
  already-in-DB delete behavior available when safe;
- forward and rollback migration plans for any state DB or Supabase schema
  change;
- startup recovery for interrupted operations;
- unresolved `commit_unknown` or `reconciliation_failed` blockers that prevent
  further destructive operations.

Delete has no app-level undo. Recovery means a fresh Preview plus separately
approved Start Upload from unchanged source files, if those files still exist
and still parse to the same exact keys.

### LAN Rollback

LAN rollout must be reversible by configuration:

- stop accepting non-loopback traffic;
- clear active LAN sessions;
- preserve audit evidence;
- preserve local operator access;
- keep Grafana separate;
- keep API docs disabled in operator mode.

## Test And Review Plan

This design does not authorize test execution. It defines required tests before
future V2 implementation can merge.

Required non-destructive checks:

- backend contract tests for feature gates;
- backend authorization tests for every mutating API class;
- LAN auth/session expiry/logout/failed-login audit tests;
- concurrency lock tests for Preview, Upload, Delete, Settings, and Runtime;
- audit redaction tests for all new evidence fields;
- DB delta record tests using synthetic fixtures;
- row attribution ledger tests using safe hashes only;
- frontend typecheck and build if UI changes;
- marker scan for raw paths, filenames, DB URLs, tokens, Authorization values,
  JWTs, secrets, raw SQL, and raw exact keys;
- `git diff --check`.

Required destructive fixture checks before operational testing is discussed:

- wrong DB target blocks before mutation;
- missing DELETE privilege blocks before mutation;
- delete DB failure records `failed_before_mutation` and remains `failed`;
- delete evidence write failure after DB success remains `commit_unknown`;
- exact count mismatch rolls back;
- audit-start failure blocks before mutation;
- commit-unknown recovery requires reconcile;
- source/keyset rebuild failure becomes `reconciliation_failed`;
- DB count failure becomes `reconciliation_failed`;
- expected and actual DB delta are recorded safely;
- row attribution evidence is safe and queryable by run id;
- marker scan finds no unsafe values.

Implementation test evidence for the local evidence foundation:

- `.\.venv\Scripts\python -m pytest tests\backend\test_upload_delete_service_contract.py tests\backend\test_db_delta_repository.py tests\backend\test_upload_jobs_service.py`
  reported `41 passed, 1 warning` on 2026-06-19.

Full backend regression also passed on 2026-06-19:
`.\.venv\Scripts\python -m pytest tests\backend` reported
`334 passed, 14 warnings`.

Forbidden without separate approval:

- operational DB delete;
- production destructive smoke;
- DB reset;
- DB truncate;
- Docker or Supabase cleanup;
- mutation of operational source files;
- LAN exposure on an operator network.

## Acceptance Criteria

This technical design draft is acceptable when all are true:

- V2 delete expansion preserves the existing already-in-DB delete contract.
- Date-scoped delete remains maintainer-only.
- Supabase Management delete is admin/maintainer-only if introduced.
- Production DB destructive testing requires a separate approval record.
- LAN access is treated as auth, authorization, audit, and concurrency work.
- The existing shared local token is rejected as sufficient LAN identity.
- DB delta is defined separately from `acceptedRows`.
- Row-level attribution uses safe hashes and run ids.
- Audit evidence fields and forbidden fields are explicit.
- Rollback to localhost-only and disabling delete expansion are explicit.
- No code, migration, operational DB access, destructive test, push, or PR is
  approved by this document.

## Open Decisions Before Implementation

These require approval before code starts:

1. Whether V2 LAN is approved at all.
2. The chosen LAN authentication mechanism.
3. The exact role matrix for operator, maintainer, and admin.
4. Whether V2 phase 1 uses only a sidecar attribution ledger or also changes
   Supabase schema.
5. Maximum delete selection limits for each delete policy.
6. Exact production approval record format and storage location.
7. Whether LAN client context may store raw IP addresses or only coarse client
   context classes.
8. Whether any operator-facing date-scoped delete UI is approved after copy,
   i18n, and runbook review.
