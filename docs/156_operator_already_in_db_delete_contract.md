# Operator Already-In-DB Delete Contract

Date: 2026-06-18 Asia/Seoul

Status: `implementation_contract_for_review`

## Purpose

This document records the approved implementation contract for deleting only
selected Upload Preview items with status `already_in_db` from local Supabase
`public.all_metrics`.

This is not a general cleanup feature. It is not a substitute for Upload
Preview, Start Upload, Retry Failed, DB reset, Docker cleanup, or Supabase
lifecycle work.

## API Contract

| Endpoint | Mutation class | Purpose |
| --- | --- | --- |
| `POST /api/upload/delete/preflight` | local state/audit only | Validate selected `already_in_db` Preview items, rollback readiness, DB target guard, and DELETE privilege. |
| `POST /api/upload/delete/jobs` | destructive DB delete | Start one all-or-nothing exact-key delete after typed count and acknowledgements. |
| `GET /api/upload/delete/jobs/latest` | read-only | Show latest delete status and unresolved recovery blocker. |
| `POST /api/upload/delete/jobs/{deleteRunId}/reconcile` | local state/audit only | Resolve `commit_unknown` or explicitly retried `reconciliation_failed` by read-only exact-key DB count. |

All POST endpoints require the local API token. The reconcile endpoint mutates
local state and audit rows but must remain SELECT-only against local Supabase.
It must not issue temp-table, insert, delete, update, upsert, or lifecycle
statements against local Supabase. Delete Preflight and Start Delete use the
full DB guard, including the non-destructive DELETE privilege probe; reconcile
uses only the target/schema/fingerprint guard plus SELECT-only exact-key count
and must not require DELETE privilege.

## Required Gates

Start Delete must block before DB mutation unless all conditions are true:

- preflight is ready and not expired;
- selected Preview items are still `already_in_db`;
- Preview is latest, fresh, `succeeded`, and `dbStatus = reachable`;
- no active Preview, Upload Job, or unresolved Delete Job exists;
- source files are present, signature-stable, and parse to the same keyset;
- rollback readiness is true;
- DB target is the configured local loopback Supabase DB port;
- schema fingerprint proves the expected `all_metrics` exact-key contract;
- DELETE privilege is proven non-destructively;
- DB count still matches selected exact-key count;
- typed exact-key count matches;
- no-undo and rollback-limitation acknowledgements are true;
- `delete_run` state is created as `preparing`;
- `upload.delete_start` audit write succeeds;
- `delete_run` transitions to `running` before opening the destructive
  transaction.

Start Delete must re-read the selected Preview items at start time. If any
selected item is missing or no longer has status `already_in_db`, the backend
must block before DB guard, DB count, audit-start, or destructive transaction.

## Transaction Policy

Version 1 uses one all-or-nothing transaction per Start Delete request.

- Key staging may be chunked inside the Start Delete transaction.
- Count checks before Start Delete and reconcile recovery use SELECT-only exact
  key matching, not temp-table staging.
- Per-batch commits are not allowed.
- A conservative max selection blocks oversized deletes.
- Final DB count and DELETE privilege are rechecked inside the transaction.
- SQL `RETURNING` is count-only; raw keys are never returned.
- Crash after possible commit moves the run to `commit_unknown`, requiring
  explicit reconciliation before another delete can proceed.

Reconciliation may classify a run as `reconciled_succeeded` or
`reconciled_rolled_back` only after the backend rebuilds the selected keyset,
proves the selection/keyset hashes still match the delete run, proves the DB
target fingerprint still matches, and completes the read-only DB count. It does
not prove DELETE privilege because no destructive DB statement is allowed on the
reconcile path. Source rebuild failure, status drift, keyset/hash mismatch, DB
target drift, or DB count failure must finish the attempt as
`reconciliation_failed`, not leave the run in `reconciling` or infer success
from an empty keyset.

## Rollback Limit

There is no app-level undo.

Rollback means a future fresh Preview plus separately approved Start Upload from
unchanged source files. That path is valid only if source files still exist,
still parse, and still produce the same exact keyset. The UI and audit must make
this limitation explicit.

## Audit And Redaction

Audit actions:

- `upload.delete_preflight`
- `upload.delete_start`
- `upload.delete_succeeded`
- `upload.delete_failed`
- `upload.delete_blocked`
- `upload.delete_reconciled`

Allowed audit evidence:

- run/preflight ids;
- selected item count;
- selected/deleted row counts;
- rollback readiness and safe blocker codes;
- sanitized DB target class and fingerprint hash;
- selection hash and selection data hash;
- reason codes;
- `rawMatchRowsReturned=false`.

Forbidden in API responses, audit rows, logs, events, screenshots, and docs:

- raw source paths;
- raw operational filenames;
- CSV row content;
- raw `(timestamp, device_id)` values;
- DB URLs;
- tokens, Authorization values, JWTs, anon keys, service role values, secrets;
- raw SQL;
- raw exception payloads.

## QA Requirements

Required non-destructive validation before merge:

- backend delete service/API/repository contract tests;
- local token route coverage for delete preflight/start/reconcile;
- frontend typecheck and API-mode build;
- screenshot QA if Upload UI changed;
- `git diff --check`;
- diff marker scan for raw paths, DB URLs, tokens, Authorization values, JWTs,
  secrets, and operational filename markers.

Destructive smoke is allowed only against a disposable local fixture DB. It must
prove wrong DB target blocking, DELETE permission blocking, audit-write failure
blocking before DB mutation, exact count mismatch rollback, success count match,
startup recovery, start-time status drift blocking, source/keyset rebuild
failure reconciliation, DB count failure reconciliation, and commit-unknown
reconciliation.

## Disposable Fixture DB Smoke Procedure

Status: `not_run_requires_separate_approval`

Do not run this procedure against the operator database, configured production
source, or any DB containing operational rows. Run it only after separate
approval for disposable fixture destructive smoke.

Required setup:

- create or select a disposable local Postgres/Supabase fixture DB;
- create only the minimal `public.all_metrics` shape needed for exact-key
  delete validation;
- seed synthetic rows with non-operational timestamps, device ids, and filenames;
- point a disposable API config at the fixture DB only;
- verify the DB target guard class identifies the fixture as the intended local
  disposable target before any delete case;
- keep operational config, source folders, and local runtime state untouched.

Smoke cases:

- wrong target guard blocks before delete;
- missing DELETE privilege blocks before delete;
- ready preflight with exact fixture keys succeeds;
- exact count mismatch rolls back and leaves all fixture rows present;
- start-time selected item status drift blocks before DB guard/count/audit-start;
- audit-start failure blocks before DB mutation;
- simulated commit-unknown requires reconcile;
- reconcile with missing/source-changed key evidence becomes
  `reconciliation_failed`;
- reconcile DB count failure becomes `reconciliation_failed`;
- reconcile success clears stale `error_code` and `error_message` from prior
  `commit_unknown` or `reconciliation_failed` attempts;
- reconcile target/schema guard is separated from the DELETE privilege guard;
- startup recovery leaves `preparing` as failed and `running`/`finalizing` as
  `commit_unknown`.

Required evidence:

- fixture-only DB target proof;
- delete run ids and safe audit ids;
- expected/deleted/present/absent counts;
- reason codes for each blocked or failed case;
- marker scan showing no raw source paths, operational filenames, DB URLs,
  tokens, Authorization values, JWTs, secrets, or raw exact keys.

## PR Ready Gate Checklist

PR #182 must stay Draft until all merge gates are recorded:

- backend delete service/API/repository tests pass;
- full backend tests pass;
- frontend typecheck and build pass;
- API-mode build is restored after any mock build or screenshot QA;
- `git diff --check` passes;
- marker scan has no raw paths, DB URLs, tokens, Authorization values, JWTs,
  secrets, or operational filename markers;
- reconcile contract is SELECT-only against local Supabase;
- reconcile target/schema/fingerprint guard is separated from DELETE privilege
  checks, which remain mandatory for Delete Preflight and Start Delete;
- destructive smoke is either completed against a disposable local fixture DB
  under separate approval or explicitly deferred with PR remaining Draft;
- no operational Upload Preview, Start Upload, Retry Failed, runtime mutation,
  Docker/Supabase lifecycle, or operational DB delete was executed during PR
  readiness checks.
