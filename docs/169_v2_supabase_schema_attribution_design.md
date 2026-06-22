# V2 Supabase Schema Attribution Design Gate

Date: 2026-06-22 Asia/Seoul

Status: `deferred_design_gate_defined`

## Purpose

This document defines the approval gate for any future V2 Supabase-backed row
attribution schema work.

The business goal is to make a future reviewer able to connect upload/delete
effects to operation evidence without weakening the existing
`all_metrics(timestamp, device_id)` upsert safety mechanism and without moving
raw operational identifiers into shared database evidence.

This is a design and safety gate only. It does not approve a Supabase migration,
backfill, fixture DB mutation, operational DB access, package handoff,
feature-gate enablement, LAN exposure, deploy, or operator mutation.

## Current Approved Path

The approved V2 phase 1 attribution path remains the local state DB sidecar:

- `row_attribution_ledger` in the local SQLite state DB;
- default-off writes through `v2_row_attribution_enabled`;
- HMAC-backed safe hashes for exact keys and source evidence;
- links to operation id, audit id, and DB delta evidence;
- append-only records with reconcile/follow-up rows instead of mutation.

The Supabase `public.all_metrics` table remains the operational measurement
table. Its current safety contract is:

- `UNIQUE ("timestamp", device_id)` remains present;
- upload upsert continues to rely on that key;
- Preview reconciliation continues to join against `public.all_metrics`;
- RLS and grants for the upload contract remain compatible with the existing
  Edge Function path;
- no raw source path, filename, DB URL, token, Authorization value, JWT, secret,
  row content, or raw exact key is emitted in API responses, audit rows, logs,
  docs, screenshots, or package evidence.

## Deferred Supabase Shape

If a later written approval rescopes Supabase schema attribution, the preferred
shape is a new append-only evidence table, not columns on `public.all_metrics`.

Working name:

```text
public.metric_row_attribution_evidence
```

Minimum logical fields:

```text
attribution_id
operation_id
operation_type
operation_phase
audit_id
db_delta_id
actor_id
actor_role
exact_key_hash
exact_key_hash_version
source_evidence_hash
source_evidence_hash_version
outcome
reason_code
db_target_class
db_fingerprint_hash
schema_fingerprint_hash
sidecar_attribution_id
supersedes_attribution_id
created_at
```

Design constraints:

- Do not add attribution columns to `public.all_metrics` in V2.
- Do not change or drop `all_metrics_timestamp_device_id_key`.
- Do not change the upload Edge Function upsert conflict target.
- Do not store raw `(timestamp, device_id)` values.
- Do not store raw source paths, filenames, CSV row content, SQL text, DB URLs,
  tokens, Authorization values, JWTs, service-role values, anon keys, or
  secrets.
- Do not use a foreign key from attribution evidence to `public.all_metrics`
  unless the approved design proves it does not require raw keys or weaken
  upload/delete behavior.
- Preserve local sidecar compatibility: sidecar evidence remains the source of
  truth for already-recorded local evidence, and Supabase attribution can only
  mirror or supplement it after approval.

## Migration Design Requirements

A future migration PR must include all of the following before merge:

1. Forward migration DDL for the new attribution evidence table.
2. Explicit proof that `public.all_metrics` DDL is unchanged except for
   separately approved additive indexes, if any.
3. A static migration test that fails if the migration drops, renames, or alters
   `all_metrics_timestamp_device_id_key`.
4. A static migration test that fails if the migration adds raw key columns such
   as `timestamp`, `device_id`, `source_path`, `filename`, or raw SQL payload
   columns to the attribution table.
5. Append-only enforcement through database policy, trigger, or strictly scoped
   write path, with tests.
6. RLS/grant design that does not give normal upload anon paths broad read/write
   access to attribution evidence unless explicitly approved.
7. Compatibility tests proving existing upload and preview code still use the
   current `all_metrics(timestamp, device_id)` contract.

No migration is approved until those requirements are present and reviewed.

## Backfill Design Requirements

Backfill is separate from migration.

Allowed backfill input, after approval:

- local sidecar `row_attribution_ledger` rows;
- local `db_delta_evidence` rows;
- audit ids and operation ids;
- safe hashes and aggregate counts only.

Blocked backfill input:

- raw operational source paths;
- operational filenames;
- raw CSV row content;
- raw `(timestamp, device_id)` exact keys;
- DB URLs or credentials;
- raw SQL query payloads;
- screenshots or logs containing sensitive markers.

Backfill must be idempotent by safe hash plus operation id plus sidecar
attribution id. It must record a bounded input count, inserted evidence count,
skipped duplicate count, and redaction scan result. It must not delete or edit
local sidecar evidence.

## Rollback Design Requirements

Rollback depends on whether production evidence has been written.

Before production writes:

- disable the Supabase attribution feature gate;
- drop only the new attribution evidence table in a fixture or disposable DB if
  the approved rollback test requires it;
- preserve `public.all_metrics` and all local state DB evidence.

After any production evidence exists:

- do not delete attribution evidence;
- disable writes and hide reads if necessary;
- preserve the table and add a corrective follow-up record or migration;
- document the evidence state and redaction result;
- do not run Supabase reset/cleanup, Docker cleanup, volume deletion, or broad
  table deletion as rollback.

## Test Plan

Required future tests:

- static SQL test: `all_metrics_timestamp_device_id_key` remains unique on
  `("timestamp", device_id)`;
- static SQL test: upload policies and grants for `public.all_metrics` remain
  compatible with the existing upload contract;
- static SQL test: attribution table contains only safe-hash/evidence fields;
- repository/service test: gate-off writes no Supabase attribution evidence;
- fixture DB test: gate-on writes append-only attribution evidence without raw
  keys;
- backfill test: sidecar rows can be mirrored idempotently by safe identifiers;
- rollback test: fixture rollback disables writes without touching
  `public.all_metrics`;
- redaction test: API/audit/log/package evidence contains no raw path, filename,
  DB URL, token, Authorization value, JWT, secret, raw SQL, raw exact key, or CSV
  content.

## Stop Conditions

Stop and report before implementation if any of these are required:

- changing `public.all_metrics` columns or unique key;
- executing a Supabase migration;
- connecting to operational DB data;
- running destructive fixture DB mutation without a fixture-specific approval;
- using raw source paths, filenames, exact keys, SQL, DB URLs, tokens, JWTs, or
  secrets in evidence;
- broad reset/cleanup/delete operations;
- using schema attribution as a prerequisite for Upload Preview, Start Upload,
  Retry Failed, Delete, LAN, or deploy.

## Current Classification

Supabase schema attribution remains `Deferred`.

The current approved and implemented attribution foundation is still the local
state DB sidecar. This document only defines the minimum design gate for a later
written approval to begin Supabase migration work.

## Rollback

This is a document-only change. Before commit, rollback is:

```powershell
git restore docs/169_v2_supabase_schema_attribution_design.md docs/165_v2_status_matrix.md CHANGELOG.md
```

After commit, revert the document commit. No code, state DB, Supabase data,
Docker state, package output, LAN configuration, or operational evidence should
be deleted as rollback for this design gate.
