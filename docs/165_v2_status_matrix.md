# V2 Status Matrix

Date: 2026-06-22 Asia/Seoul

Status: `current_main_status_matrix`

## Purpose

This document records the V2 plan-to-implementation status on current `main`.
It prevents the completed evidence foundation work from being mistaken for a
complete V2 release.

This document does not approve code changes, operational DB access, Upload
Preview, Start Upload, Retry Failed, Delete, Settings save, feature-gate
enablement, LAN exposure, Supabase reset/cleanup, Docker cleanup, deployment,
commit, push, or PR creation.

## Evidence Reviewed

- `main` and `origin/main`: `baee4982d8be9f6ef8e44b4a8ca6f1a30a382222`.
- Accepted operator package metadata:
  - `sourceCommit`: `cb8a3c8`
  - `packageLabel`: `ExtrusionWebConsole-cb8a3c8-20260621-160038-290`
  - `frontendMode`: `api`
  - `runtimeMode`: `operator-ready`
  - `zipCreated`: `false`
- Current planning and implementation documents:
  - `docs/159_v2_scope_and_safety_plan.md`
  - `docs/160_v2_delete_lan_audit_rollback_technical_design.md`
  - `docs/161_v2_open_decisions_review.md`
  - `docs/162_v2_sidecar_row_attribution_ledger_design.md`
  - `docs/163_v2_sidecar_row_attribution_ledger_migration_plan.md`
  - `docs/164_operator_data_mutation_safety_gate.md`
  - `docs/166_v2_api_mode_package_runtime_evidence.md`
  - `docs/171_v2_operational_delete_verification_gate.md`
- Current code evidence in `backend/`, `frontend/`, and `tests/backend/`.

## Status Definitions

| Status | Meaning |
| --- | --- |
| `Completed` | Implemented or documented for the stated narrow scope, with local validation evidence. |
| `Partial` | Some foundation or validation exists, but the full V2 item is not ready. |
| `Deferred` | Not implemented or not approved for execution until a later decision. |
| `Excluded` | Intentionally outside V2 unless a later approved document changes scope. |

## V2 Completion Track Items

| # | Item | Current status | Evidence | Remaining gate |
| ---: | --- | --- | --- | --- |
| 1 | Operational upload verification | `Deferred` | `docs/164` defines fresh inventory, Preview-only, Start Upload, and Retry Failed approval gates. | Exact operational approval and fresh evidence are required before any Preview-only, Start Upload, or Retry Failed run. |
| 2 | API-mode package full runtime smoke and zip handoff | `Completed` | `docs/166` records API-mode build, package assembly, zip/SHA-256 metadata, launcher/shortcut `-CheckOnly`, and read-only HTTP smoke. | Does not approve operator mutation or replace the accepted mutation package in `docs/164`. |
| 3 | Operator-facing date-scoped delete UI | `Deferred` | `docs/161` keeps operator-facing date-scoped delete UI unapproved. | Copy, Korean/English i18n, runbook, role matrix, feature gate, and explicit UI approval. |
| 4 | Delete expansion | `Deferred` | `docs/160` defines the design constraints; `docs/161` leaves numeric limits and broader policy unapproved. | Fixture DB evidence, limits, preflight/reconcile/audit/rollback proof, and separate approval. |
| 5 | Operational DB delete verification | `Deferred` | `docs/171` defines the approval record, storage, evidence report, rollback, and stop-condition gate; `docs/164` keeps exact destructive approval wording. | Exact approval record, safe evidence report, and separate approval before any operational DB delete. |
| 6 | Multi-user LAN | `Deferred` | `docs/159`, `docs/160`, and `docs/161` keep LAN and non-loopback bind blocked. | Auth/authz/session/actor audit/concurrency/CORS/bind design and explicit rescope. |
| 7 | Grafana/Vector observability hardening | `Deferred` | `docs/159` and `docs/160` require sanitized logs/metrics and keep Grafana linked, not embedded. | Separate implementation, alerts/runbook/package checks, and validation evidence. |
| 8 | Supabase schema attribution | `Deferred` | `docs/161` approves only sidecar phase 1 and defers Supabase schema changes. | Migration, backfill, rollback, and test design that preserves `all_metrics(timestamp, device_id)` upsert safety. |

## Matrix

| V2 area | Current status | Current main evidence | Remaining gate |
| --- | --- | --- | --- |
| V2 planning boundary | `Completed` | `docs/159` defines scope, non-goals, safety gates, and explicit rescope points. | Does not approve implementation by itself. |
| Delete/LAN/audit/rollback technical design | `Completed` | `docs/160` defines the implementation-facing design and safety constraints. | Later approvals still required before LAN, delete expansion, or operational DB mutation. |
| V2 open decisions | `Partial` | `docs/161` approves only the sidecar row attribution direction. LAN, date-scoped delete UI, role matrix, production approval record, and delete limits remain unresolved. | Follow-up decision records. |
| `row_attribution_ledger` sidecar foundation | `Completed` | Backend settings and local state DB code include the default-off row attribution gate and sidecar repository paths; backend tests cover bootstrap, append-only behavior, safe hashes, and gate-on linkage. | Gate enablement and any operational evidence writes require separate approval. |
| `db_delta_evidence` foundation | `Completed` | Backend includes append-only local state DB delta evidence and gate-on upload/delete service wiring; tests cover default-off no-write behavior, mismatch handling, and audit/delta/attribution linkage. | Operational use requires explicit mutation approval and gate-on approval. |
| Upload readiness hardening | `Completed` | `main` includes Start/Retry readiness hardening for local DB target class, Supabase API/DB/Edge readiness, Edge auth key class, and target-only row approval counts. | Does not approve Start Upload or Retry Failed. |
| API-mode operator package validation | `Completed` | `docs/166` records API-mode build, package assembly, zip/SHA-256 handoff metadata, launcher/shortcut `-CheckOnly`, and read-only HTTP smoke for candidate package `ExtrusionWebConsole-eedac29-20260621-165853-560`. | This does not approve operator mutation and does not replace the `docs/164` accepted mutation package unless that gate is separately updated. |
| Operator data mutation gate | `Completed` | `docs/164` records current package metadata and exact approval templates for Preview-only, Start Upload, Retry Failed, and Delete. | Each mutation still requires its own exact approval at execution time. |
| Operator-facing date-scoped delete UI | `Deferred` | `docs/159`, `docs/160`, and `docs/161` keep date-scoped delete maintainer-only and defer operator-facing UI. | Copy, i18n, runbook, role matrix, and explicit UI approval. |
| Delete expansion beyond current selected `already_in_db` path | `Deferred` | V2 design permits future policy work, but no broader delete policy is approved for operators. | Fixture evidence, production approval format, limits, and separate approval. |
| Operational DB delete verification | `Deferred` | `docs/171` requires immutable or append-only approval storage, exact scope, no-undo acknowledgement, safe evidence report, and blocked rollback semantics before operational delete can be discussed. | Separate approval, current preflight evidence, and post-run evidence report. |
| Multi-user LAN access | `Deferred` | `docs/159`, `docs/160`, and `docs/161` block LAN, non-loopback bind, LAN CORS widening, LAN sessions, and LAN rollout. | LAN security gate, auth design, role matrix, concurrency model, and explicit rescope. |
| Grafana/Vector observability hardening | `Deferred` | V2 requirements are documented, but no current implementation evidence shows the hardened observability release is complete. | Separate design and implementation approval; Grafana remains linked, not embedded. |
| Supabase schema attribution | `Deferred` | Current approved path is local sidecar only; Supabase schema changes are not approved. | Separate migration, backfill, rollback, and test design. |
| Full V2 release | `Partial` | Several foundations are complete, but LAN, date-scoped delete UI, production delete verification, observability hardening, and release gates are incomplete. | Do not describe V2 as complete until every deferred item is explicitly resolved or excluded. |
| Cloud Supabase migration | `Excluded` | `docs/159` and README keep Cloud Supabase out of scope. | Later approved rescope only. |
| Default legacy upload state import | `Excluded` | `docs/159` and README keep default legacy state import out of scope. | Later approved rescope only. |
| Grafana iframe embedding | `Excluded` | `docs/159`, `docs/160`, and README keep Grafana separate and linked. | Later approved rescope only. |

## Operator Interpretation

The current safe statement is:

```text
V2 is not complete. Current main has completed the local evidence foundation,
upload readiness hardening, and API-mode package runtime smoke for a candidate
handoff package. LAN, operator-facing date-scoped delete UI, operational DB
delete verification, Grafana/Vector hardening, and the overall V2 release remain
deferred or excluded until separate approvals resolve them.
```

Do not say:

```text
V2 is complete.
```

Do not use package `sourceCommit` values from older handoffs when approving a
mutation from the accepted `cb8a3c8` package unless
`docs/164_operator_data_mutation_safety_gate.md` is separately updated.

## Rollback

This is a document-only status matrix. Before commit, rollback is:

```powershell
git restore CHANGELOG.md docs\164_operator_data_mutation_safety_gate.md docs\165_v2_status_matrix.md
git rm --cached --ignore-unmatch docs\171_v2_operational_delete_verification_gate.md
Remove-Item -LiteralPath docs\171_v2_operational_delete_verification_gate.md
```

After commit, revert the document commit. No operational evidence, local state
DB, Supabase data, Docker state, package output, or LAN configuration should be
deleted as rollback for this document.
