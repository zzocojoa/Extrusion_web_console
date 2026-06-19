# V2 Open Decisions Review

Date: 2026-06-19 Asia/Seoul

Status: `pre_implementation_decision_record`

## Purpose

This document resolves the eight open decisions listed in
`docs/160_v2_delete_lan_audit_rollback_technical_design.md` before V2
implementation starts.

This is not implementation approval. It does not approve code changes, database
migrations, production DB access, fixture DB mutation, destructive smoke tests,
LAN exposure, release packaging, branch creation, commit, push, or PR creation.

## Source Documents Reviewed

- `AGENTS.md`
- `README.md`
- `docs/00_product_scope.md`
- `docs/156_operator_already_in_db_delete_contract.md`
- `docs/159_v2_scope_and_safety_plan.md`
- `docs/160_v2_delete_lan_audit_rollback_technical_design.md`

## Classification Rules

Decision classifications:

- `Approved`: the design choice is approved as a planning constraint for the
  next V2 design step. It still does not approve code or migration work.
- `Deferred`: implementation is not approved. A later written approval must
  change the decision before code starts.
- `Needs additional design`: the direction is not precise enough for
  implementation. A follow-up design record is required.

## Executive Decision

V2 implementation must not start broadly from
`docs/160_v2_delete_lan_audit_rollback_technical_design.md`.

Only one design choice is approved now: V2 phase 1 row attribution should use a
sidecar attribution ledger in the local state DB and must not change the
Supabase `all_metrics(timestamp, device_id)` schema or upsert contract.

LAN, operator-facing date-scoped delete UI, production approval record format,
delete selection limits, and the exact authorization matrix remain blocked or
design-incomplete.

## Decision Classification

| # | Open decision | Classification | Implementation effect |
| --- | --- | --- | --- |
| 1 | Whether V2 LAN is approved at all. | `Deferred` | No LAN implementation, non-loopback bind, LAN CORS widening, LAN session work, or LAN rollout is approved. V1 remains localhost-only until a later product/security approval explicitly rescopes the app. |
| 2 | The chosen LAN authentication mechanism. | `Needs additional design` | No auth mechanism is selected. A later design must compare local account store, Windows-integrated identity, and reverse-proxy identity against actor attribution, session expiry, failed-login audit, CSRF behavior, testability, and rollback. |
| 3 | The exact role matrix for operator, maintainer, and admin. | `Needs additional design` | The minimum roles in `docs/160` are accepted only as a baseline constraint. Endpoint-level permissions, recovery powers, settings/runtime controls, admin functions, and denied-action audit behavior must be specified before implementation. |
| 4 | Whether V2 phase 1 uses only a sidecar attribution ledger or also changes Supabase schema. | `Approved` | V2 phase 1 uses only a sidecar `row_attribution_ledger` in the local state DB. Supabase schema changes are deferred and require a separate migration, backfill, rollback, and test design. |
| 5 | Maximum delete selection limits for each delete policy. | `Needs additional design` | No numeric delete limit is approved. Each delete policy must receive a concrete max row/key/item limit justified by fixture performance, operator risk, rollback evidence, and UI confirmation behavior. |
| 6 | Exact production approval record format and storage location. | `Needs additional design` | Operational DB destructive testing stays blocked. A later record must define required fields, storage location, immutability, audit linkage, evidence report path, retention, and redaction rules. |
| 7 | Whether LAN client context may store raw IP addresses or only coarse client context classes. | `Deferred` | Raw LAN client IP storage is not approved. Use only coarse client context classes unless a later privacy/security approval defines retention, redaction, visibility, and incident-response need. |
| 8 | Whether any operator-facing date-scoped delete UI is approved after copy, i18n, and runbook review. | `Deferred` | No operator-facing date-scoped delete UI is approved. Date-scoped delete remains maintainer-only and hidden from normal operator cleanup flows until a later UI/copy/i18n/runbook approval changes this. |

## Approved Follow-Up Design Scope

The following work may proceed only as follow-up design, not code, unless a later
approval explicitly expands scope:

- Define the local state DB shape for the sidecar attribution ledger.
- Define tests proving attribution uses safe hashes and never emits raw
  `(timestamp, device_id)` values, raw source paths, operational filenames, DB
  URLs, tokens, Authorization values, JWTs, secrets, raw SQL, or CSV row
  contents.
- Define how attribution records link to operation ids, audit ids, DB delta
  evidence, and recovery/reconcile states.

The approved row attribution direction must preserve the current
`all_metrics(timestamp, device_id)` unique/upsert behavior.

## Blocked Scope

The following work is blocked until later written approval:

- LAN enablement or non-loopback bind.
- LAN authentication implementation.
- LAN CORS widening or wildcard credentials.
- LAN session storage, user administration, or role administration.
- Operator-facing date-scoped delete UI.
- Raw LAN client IP retention.
- Operational DB destructive testing.
- Supabase schema migration for row attribution.
- Numeric delete limit implementation.
- Production approval record implementation.

## Required Follow-Up Records

Before implementation starts, write and approve these records:

1. LAN approval and authentication design, if LAN remains in V2 scope.
2. Endpoint-level role matrix for operator, maintainer, and admin.
3. Delete policy limit record with concrete max selection limits.
4. Production approval record schema and storage design.
5. Operator-facing date-scoped delete UI decision, including copy, Korean and
   English i18n, maintainer/operator visibility, runbook, and test plan.
6. Sidecar attribution ledger schema and test plan.

## Safety Gates

Future implementation must stop if any of these become necessary without a new
approval:

- code changes outside documentation;
- database migration;
- connection to operational DB data;
- destructive fixture DB mutation;
- LAN exposure;
- package, deploy, PR, commit, or push;
- storage or display of secrets, DB URLs, raw source paths, operational
  filenames, raw exact keys, raw SQL, or raw LAN IP addresses.

## Rollback

This is a document-only decision record. If rejected, rollback is to remove or
revise this file only after checking the current diff. No code, state DB,
Supabase, Docker, LAN, package, deployment, or operator data rollback is
involved.
