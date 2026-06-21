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
- Current code evidence in `backend/`, `frontend/`, and `tests/backend/`.

## Status Definitions

| Status | Meaning |
| --- | --- |
| `Completed` | Implemented or documented for the stated narrow scope, with local validation evidence. |
| `Partial` | Some foundation or validation exists, but the full V2 item is not ready. |
| `Deferred` | Not implemented or not approved for execution until a later decision. |
| `Excluded` | Intentionally outside V2 unless a later approved document changes scope. |

## Matrix

| V2 area | Current status | Current main evidence | Remaining gate |
| --- | --- | --- | --- |
| V2 planning boundary | `Completed` | `docs/159` defines scope, non-goals, safety gates, and explicit rescope points. | Does not approve implementation by itself. |
| Delete/LAN/audit/rollback technical design | `Completed` | `docs/160` defines the implementation-facing design and safety constraints. | Later approvals still required before LAN, delete expansion, or operational DB mutation. |
| V2 open decisions | `Partial` | `docs/161` approves only the sidecar row attribution direction. LAN, date-scoped delete UI, role matrix, production approval record, and delete limits remain unresolved. | Follow-up decision records. |
| `row_attribution_ledger` sidecar foundation | `Completed` | Backend settings and local state DB code include the default-off row attribution gate and sidecar repository paths; backend tests cover bootstrap, append-only behavior, safe hashes, and gate-on linkage. | Gate enablement and any operational evidence writes require separate approval. |
| `db_delta_evidence` foundation | `Completed` | Backend includes append-only local state DB delta evidence and gate-on upload/delete service wiring; tests cover default-off no-write behavior, mismatch handling, and audit/delta/attribution linkage. | Operational use requires explicit mutation approval and gate-on approval. |
| Upload readiness hardening | `Completed` | `main` includes Start/Retry readiness hardening for local DB target class, Supabase API/DB/Edge readiness, Edge auth key class, and target-only row approval counts. | Does not approve Start Upload or Retry Failed. |
| API-mode operator package validation | `Partial` | Package metadata for `cb8a3c8` records `frontendMode=api`, `runtimeMode=operator-ready`, and launcher/shortcut `-CheckOnly` passed. | Full runtime smoke and any operator mutation still require separate approval. |
| Operator data mutation gate | `Completed` | `docs/164` records current package metadata and exact approval templates for Preview-only, Start Upload, Retry Failed, and Delete. | Each mutation still requires its own exact approval at execution time. |
| Operator-facing date-scoped delete UI | `Deferred` | `docs/159`, `docs/160`, and `docs/161` keep date-scoped delete maintainer-only and defer operator-facing UI. | Copy, i18n, runbook, role matrix, and explicit UI approval. |
| Delete expansion beyond current selected `already_in_db` path | `Deferred` | V2 design permits future policy work, but no broader delete policy is approved for operators. | Fixture evidence, production approval format, limits, and separate approval. |
| Operational DB delete verification | `Deferred` | Documents require separate operational approval; no current evidence approves production destructive smoke. | Exact DB target class, row/key scope, no-undo acknowledgement, and audit evidence plan. |
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
upload readiness hardening, and partial API-mode package metadata validation.
LAN, operator-facing date-scoped delete UI, operational DB delete verification,
Grafana/Vector hardening, full runtime package smoke, and the overall V2 release
remain deferred or excluded until separate approvals resolve them.
```

Do not say:

```text
V2 is complete.
```

Do not use package `sourceCommit` values from older handoffs when approving a
mutation from the current `cb8a3c8` package.

## Rollback

This is a document-only status matrix. Before commit, rollback is:

```powershell
git restore CHANGELOG.md README.md docs/164_operator_data_mutation_safety_gate.md
Remove-Item -LiteralPath docs\165_v2_status_matrix.md
```

After commit, revert the document commit. No operational evidence, local state
DB, Supabase data, Docker state, package output, or LAN configuration should be
deleted as rollback for this document.
