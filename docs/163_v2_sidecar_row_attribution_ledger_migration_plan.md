# V2 Sidecar Row Attribution Ledger Migration Plan

Date: 2026-06-19 Asia/Seoul

Status: `design_only_pre_implementation`

## Purpose

This document defines the pre-implementation migration, rollback, append-only
enforcement, and test plan for the local state DB sidecar
`row_attribution_ledger` designed in
`docs/162_v2_sidecar_row_attribution_ledger_design.md`.

This document is not a migration approval. It does not approve code changes,
actual migration execution, Supabase schema changes, operational DB access,
fixture DB mutation, destructive smoke tests, LAN exposure, delete UI changes,
release packaging, commit, push, or PR creation.

## Source Documents Reviewed

- `AGENTS.md`
- `README.md`
- `docs/160_v2_delete_lan_audit_rollback_technical_design.md`
- `docs/161_v2_open_decisions_review.md`
- `docs/162_v2_sidecar_row_attribution_ledger_design.md`
- `backend/app/db/sqlite.py`
- `backend/app/db/audit_repository.py`
- `backend/app/db/upload_delete_repository.py`
- `tests/backend/test_audit_repository.py`

## Approved Scope Boundary

This plan only covers the local SQLite state DB used by the web console.

Allowed design scope:

- local state DB migration shape for `row_attribution_ledger`;
- rollback plan for local state DB changes;
- append-only enforcement design;
- non-destructive tests and future test commands.

Out of scope:

- executing the migration;
- writing code or migration files;
- changing Supabase schema;
- touching `public.all_metrics`;
- changing `all_metrics(timestamp, device_id)` uniqueness or upsert behavior;
- connecting to operational DB data;
- mutating fixture DBs;
- enabling LAN behavior;
- adding delete UI;
- packaging, deploy, PR, commit, or push.

## Current State DB Pattern

Current local state DB behavior is SQLite-backed:

- `backend/app/db/sqlite.py` creates parent directories, opens SQLite with
  `foreign_keys`, WAL journal mode, and `busy_timeout`;
- repositories bootstrap tables with `CREATE TABLE IF NOT EXISTS`;
- additive compatibility changes use guarded column checks before `ALTER TABLE`;
- `audit_log` is protected by append-only SQLite triggers
  `audit_log_no_update` and `audit_log_no_delete`;
- audit append-only behavior is covered by `tests/backend/test_audit_repository.py`.

The row attribution ledger should follow the same local state DB style. It must
not introduce Supabase DDL or depend on the operator database.

## Migration Strategy

Recommended implementation sequence for a later approved code change:

1. Add a dedicated repository/bootstrap path for attribution ledger local state.
2. Create the ledger table with `CREATE TABLE IF NOT EXISTS`.
3. Create lookup indexes with `CREATE INDEX IF NOT EXISTS`.
4. Create append-only triggers with `CREATE TRIGGER IF NOT EXISTS`.
5. Bootstrap from application startup only after audit, preview, upload job,
   delete, and runtime repositories can still initialize cleanly.
6. Keep the feature path disabled until schema contract tests, redaction tests,
   and rollback rehearsal pass.

The migration must be idempotent. Re-running bootstrap against an existing state
DB must not drop rows, rewrite rows, or change existing ledger evidence.

The migration must be additive. It may add the ledger table, indexes, and
triggers. It must not alter existing Preview, Upload Job, Delete, Runtime, or
Audit table semantics.

## Proposed Local Table Shape

This is proposed SQLite DDL shape for implementation planning only. Do not run
this from the document.

```text
CREATE TABLE IF NOT EXISTS row_attribution_ledger (
  attribution_id INTEGER PRIMARY KEY AUTOINCREMENT,
  operation_id TEXT NOT NULL,
  operation_type TEXT NOT NULL CHECK(operation_type IN (
    'upload_start',
    'upload_retry',
    'delete_start',
    'delete_reconcile'
  )),
  operation_phase TEXT NOT NULL CHECK(operation_phase IN (
    'before_mutation',
    'after_mutation',
    'reconcile',
    'blocked'
  )),
  audit_id INTEGER NOT NULL,
  db_delta_id TEXT,
  actor_id TEXT NOT NULL,
  actor_role TEXT NOT NULL,
  exact_key_hash TEXT NOT NULL,
  exact_key_hash_version TEXT NOT NULL,
  source_evidence_hash TEXT NOT NULL,
  source_evidence_hash_version TEXT NOT NULL,
  outcome TEXT NOT NULL CHECK(outcome IN (
    'inserted',
    'upsert_accepted',
    'unchanged',
    'deleted',
    'reconciled_absent',
    'blocked',
    'failed_before_mutation',
    'unknown_requires_reconcile'
  )),
  reason_code TEXT,
  db_target_class TEXT NOT NULL,
  db_fingerprint_hash TEXT NOT NULL,
  schema_fingerprint_hash TEXT NOT NULL,
  supersedes_attribution_id INTEGER,
  created_at TEXT NOT NULL,
  FOREIGN KEY(audit_id) REFERENCES audit_log(audit_id),
  FOREIGN KEY(supersedes_attribution_id)
    REFERENCES row_attribution_ledger(attribution_id)
);
```

Implementation may revise the exact DDL, but it must preserve the logical
fields and safety properties from `docs/162`.

## Index Plan

Indexes should support review queries without exposing raw keys:

```text
CREATE INDEX IF NOT EXISTS idx_row_attr_operation_created
  ON row_attribution_ledger(operation_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_row_attr_exact_key_created
  ON row_attribution_ledger(exact_key_hash, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_row_attr_audit
  ON row_attribution_ledger(audit_id);

CREATE INDEX IF NOT EXISTS idx_row_attr_db_delta
  ON row_attribution_ledger(db_delta_id);

CREATE INDEX IF NOT EXISTS idx_row_attr_outcome_created
  ON row_attribution_ledger(outcome, created_at DESC);
```

Do not add indexes on raw timestamp, raw device id, raw paths, filenames, raw
SQL, DB URLs, Authorization values, JWTs, or secrets because those values must
not exist in the table.

## Append-Only Enforcement

The ledger must reject updates and deletes in normal operation.

Proposed trigger shape:

```text
CREATE TRIGGER IF NOT EXISTS row_attribution_ledger_no_update
BEFORE UPDATE ON row_attribution_ledger
BEGIN
  SELECT RAISE(ABORT, 'row_attribution_ledger_append_only');
END;

CREATE TRIGGER IF NOT EXISTS row_attribution_ledger_no_delete
BEFORE DELETE ON row_attribution_ledger
BEGIN
  SELECT RAISE(ABORT, 'row_attribution_ledger_append_only');
END;
```

Corrections, recovery decisions, and reconcile results must insert later rows
instead of updating existing rows. Later rows may point to older rows with
`supersedes_attribution_id`.

Append-only enforcement is a local state DB safety control. It is not a
substitute for audit rows, DB delta evidence, or operation state transitions.

## Pre-Migration Checks

A later implementation must perform these checks before enabling writes:

- state DB path resolves to the active local state DB selected by settings;
- SQLite opens with `foreign_keys` enabled;
- existing repository bootstraps still pass;
- `audit_log` exists and append-only triggers are installed;
- `row_attribution_ledger` does not already exist with an incompatible shape;
- no Supabase connection string or operator DB target is required;
- no fixture DB mutation is required;
- the feature gate for attribution writes remains disabled until tests pass.

If a compatible ledger table already exists, bootstrap must be a no-op except
for creating any missing compatible indexes or triggers.

If an incompatible ledger table exists, startup must fail closed with a safe
reason code. It must not drop, rename, or rewrite the table automatically.

## Migration Failure Behavior

Migration failure must be visible and non-destructive:

- log a safe failure reason without raw paths, DB URLs, or secrets;
- write an audit failure only if the audit repository is already available and
  the audit write can use safe params;
- leave V1 Preview, Upload, Delete, Runtime, and Audit behavior available when
  safe;
- keep attribution writes disabled;
- do not attempt Supabase cleanup, DB reset, fixture mutation, Docker cleanup,
  or LAN behavior.

## Rollback Plan

Rollback is separated into three cases.

### Case 1: Pre-Write Rollback

Use when the table was created but no attribution rows have been written.

Allowed rollback design:

- disable the attribution feature gate;
- remove the unreferenced table, indexes, and triggers only in a separately
  approved local state DB maintenance step;
- or leave the empty table in place and keep writes disabled.

Leaving the empty table in place is preferred because it avoids unnecessary
state DB churn.

### Case 2: Post-Write Rollback

Use when attribution rows exist.

Allowed rollback design:

- disable attribution writes;
- preserve existing ledger rows as local evidence;
- keep read-only diagnostic access for maintainers if separately approved;
- do not delete attribution evidence as the default rollback path;
- fix forward with a compatible migration when possible.

Dropping the table after rows exist is not the default rollback path because it
destroys operation evidence.

### Case 3: Corrupt Or Incompatible State DB

Use only when startup cannot safely continue.

Required rollback design:

- stop attribution bootstrap and writes;
- preserve the original state DB file;
- restore from an operator-approved state DB backup only if the backup is known
  to be from the same local machine and no newer required operation evidence
  would be lost;
- otherwise keep the state DB read-only for investigation and use a new clean
  state DB only under separate operator approval.

No rollback case may connect to or mutate operational DB data.

## Backup And Restore Requirements

A later implementation plan must define backup handling before local state DB
migration execution:

- create a local state DB backup before first ledger migration on an existing
  state DB;
- store the backup outside package output and outside source control;
- do not print the backup path in generated docs, logs, screenshots, or reports
  if it contains user-specific path segments;
- record only safe backup evidence such as backup created yes/no, timestamp,
  size class, and safe reason code;
- restore only through a separately approved local maintenance run.

## Test Plan

These are future non-destructive tests. They are commands to run after code is
implemented, not commands approved by this document.

Targeted backend tests:

```powershell
.\.venv\Scripts\python -m pytest tests\backend\test_row_attribution_repository.py
.\.venv\Scripts\python -m pytest tests\backend\test_row_attribution_migration.py
.\.venv\Scripts\python -m pytest tests\backend\test_row_attribution_redaction.py
```

Regression tests:

```powershell
.\.venv\Scripts\python -m pytest tests\backend\test_audit_repository.py
.\.venv\Scripts\python -m pytest tests\backend\test_upload_jobs_repository_contract.py
.\.venv\Scripts\python -m pytest tests\backend\test_upload_delete_service_contract.py
.\.venv\Scripts\python -m pytest tests\backend
```

Required test cases:

1. Bootstrap creates `row_attribution_ledger`, indexes, and append-only triggers
   on a temporary local SQLite state DB.
2. Bootstrap is idempotent when run twice.
3. Existing Preview, Upload Job, Delete, Runtime, and Audit bootstraps still
   pass after attribution bootstrap.
4. Update attempts fail with `row_attribution_ledger_append_only`.
5. Delete attempts fail with `row_attribution_ledger_append_only`.
6. Correction and reconcile behavior inserts a later row instead of mutating an
   older row.
7. Foreign key behavior rejects attribution rows without an existing audit row
   when foreign keys are enabled.
8. Rows never contain raw `(timestamp, device_id)`, raw exact keys, raw source
   paths, filenames, CSV row content, raw SQL, DB URLs, tokens, Authorization
   values, JWTs, anon keys, service role values, secrets, or raw exception
   payloads.
9. `all_metrics(timestamp, device_id)` behavior is not touched by the local
   state DB migration.
10. Startup fails closed when an incompatible existing ledger table is detected.
11. Attribution feature gate remains off when migration or trigger creation
    fails.
12. Backup evidence records safe metadata only.

Marker scan after implementation:

- run the repository standard secret marker scan against the implementation
  diff;
- include generated logs, reports, screenshots, and packaging artifacts when
  they exist;
- the marker scan must return no matches.

## Acceptance Criteria Before Implementation

Implementation may start only after a later approval confirms:

- this migration plan is accepted or explicitly revised;
- the implementation path is local SQLite state DB only;
- no Supabase schema migration is included;
- rollback behavior preserves attribution evidence after writes exist;
- append-only triggers are required and tested;
- bootstrap idempotence is tested;
- incompatible existing table behavior fails closed;
- test commands and marker scans are included in the implementation PR plan.

## Rollback Of This Document

This is a document-only plan. If rejected, remove or revise this file and the
README Source Documents link after inspecting the current diff. No code,
migration execution, Supabase, fixture DB, operational DB, LAN, package,
deployment, or PR rollback is involved.
