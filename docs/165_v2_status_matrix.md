# V2 Status Matrix

Date: 2026-06-22 Asia/Seoul

Status: `main_baseline_and_completion_track_candidate_matrix`

## Purpose

This document records the V2 plan-to-implementation status while separating the
current `main` baseline from the `codex/v2-completion-track` candidate. It
prevents completed foundation and candidate evidence from being mistaken for a
complete V2 release.

This document does not approve code changes, operational DB access, Upload
Preview, Start Upload, Retry Failed, Delete, Settings save, feature-gate
enablement, LAN exposure, Supabase reset/cleanup, Docker cleanup, deployment,
commit, push, or PR creation.

## Evidence Reviewed

- Current `main` and `origin/main` baseline:
  `baee4982d8be9f6ef8e44b4a8ca6f1a30a382222`.
- Current `codex/v2-completion-track` and
  `origin/codex/v2-completion-track` candidate baseline:
  `a80876fa5a03d021a98c588e4f4d3fabc3826e66`.
- Accepted operator mutation package metadata from `docs/164`:
  - `sourceCommit`: `cb8a3c8`
  - `packageLabel`: `ExtrusionWebConsole-cb8a3c8-20260621-160038-290`
  - `frontendMode`: `api`
  - `runtimeMode`: `operator-ready`
  - `zipCreated`: `false`
- Latest completion-track package evidence baseline:
  - `sourceCommit`: `a80876f`
  - `packageLabel`: `ExtrusionWebConsole-a80876f-20260622-003633-680`
  - `frontendMode`: `api`
  - `runtimeMode`: `operator-ready`
  - `frontendBuildMetadataPresent`: `true`
  - `zipCreated`: `false`
  - `zipSha256`: `not_applicable`
- Reviewed planning and implementation documents. `docs/159` through
  `docs/164` are the current `main` baseline. `docs/166` through `docs/174`
  are completion-track candidate evidence until PR #193 lands on `main`.
  - `docs/159_v2_scope_and_safety_plan.md`
  - `docs/160_v2_delete_lan_audit_rollback_technical_design.md`
  - `docs/161_v2_open_decisions_review.md`
  - `docs/162_v2_sidecar_row_attribution_ledger_design.md`
  - `docs/163_v2_sidecar_row_attribution_ledger_migration_plan.md`
  - `docs/164_operator_data_mutation_safety_gate.md`
  - `docs/166_v2_api_mode_package_runtime_evidence.md`
  - `docs/167_v2_observability_hardening_evidence.md`
  - `docs/168_v2_date_scoped_delete_ui_gate.md`
  - `docs/169_v2_supabase_schema_attribution_design.md`
  - `docs/170_v2_delete_expansion_fixture_gate.md`
  - `docs/171_v2_operational_delete_verification_gate.md`
  - `docs/172_v2_lan_security_gate.md`
  - `docs/173_v2_operational_upload_verification_gate.md`
- Code evidence in `backend/`, `frontend/`, and `tests/backend/`, scoped to
  the branch that contains the cited candidate document or implementation.

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
| 1 | Operational upload verification | `Deferred` | `docs/173` defines the V2 evidence record and completion interpretation; `docs/164` keeps the exact approval wording for fresh inventory, Preview-only, Start Upload, and Retry Failed. | Exact operational approval and fresh evidence are required before any Preview-only, Start Upload, or Retry Failed run. |
| 2 | API-mode package full runtime smoke and zip handoff | `Completed` | `docs/166` records API-mode build, package assembly, zip/SHA-256 metadata, launcher/shortcut `-CheckOnly`, and read-only HTTP smoke. | Does not approve operator mutation or replace the accepted mutation package in `docs/164`. |
| 3 | Operator-facing date-scoped delete UI | `Deferred` | `docs/168` completes only the default-off, non-mutating review shell for copy, i18n, and runbook review. | Executable/operator-facing date-scoped delete remains blocked until role matrix, policy/preflight, fixture evidence, production approval record, rollback evidence, and separate gate enablement are approved. |
| 4 | Delete expansion | `Deferred` | `docs/170` defines the fixture-first gate; `docs/160` defines the design constraints; `docs/161` leaves numeric limits and broader policy unapproved. | Concrete policy limits, fixture DB evidence, preflight/reconcile/audit/rollback proof, and separate approval. |
| 5 | Operational DB delete verification | `Deferred` | `docs/171` defines the approval record, storage, evidence report, rollback, and stop-condition gate; `docs/164` keeps exact destructive approval wording. | Exact approval record, safe evidence report, and separate approval before any operational DB delete. |
| 6 | Multi-user LAN | `Deferred` | `docs/172` adds a default-off startup guard and sanitized health state; `docs/159`, `docs/160`, and `docs/161` still block LAN exposure. | Auth/authz/session/actor audit/concurrency/CORS/bind implementation, tests, and explicit rescope. |
| 7 | Grafana/Vector observability hardening | `Completed` | `docs/167` records sanitized Grafana/Vector status classes, Vector runtime row implementation, alert/runbook classes, package/runtime checks, and explicit raw log/metric/trace export exclusions. | Does not approve Grafana iframe embedding, raw observability payload export, LAN exposure, reset/cleanup, or operator mutation. |
| 8 | Supabase schema attribution | `Deferred` | `docs/169` defines the required migration, backfill, rollback, and test design gate; `docs/161` still approves only sidecar phase 1. | Later written approval is required before any Supabase migration, backfill, fixture mutation, or operational DB access. |

## Matrix

| V2 area | Current status | Evidence | Remaining gate |
| --- | --- | --- | --- |
| V2 planning boundary | `Completed` | `docs/159` defines scope, non-goals, safety gates, and explicit rescope points. | Does not approve implementation by itself. |
| Delete/LAN/audit/rollback technical design | `Completed` | `docs/160` defines the implementation-facing design and safety constraints. | Later approvals still required before LAN, delete expansion, or operational DB mutation. |
| V2 open decisions | `Partial` | `docs/161` approves only the sidecar row attribution direction. LAN, date-scoped delete UI, role matrix, production approval record, and delete limits remain unresolved. | Follow-up decision records. |
| `row_attribution_ledger` sidecar foundation | `Completed` | Backend settings and local state DB code include the default-off row attribution gate and sidecar repository paths; backend tests cover bootstrap, append-only behavior, safe hashes, and gate-on linkage. | Gate enablement and any operational evidence writes require separate approval. |
| `db_delta_evidence` foundation | `Completed` | Backend includes append-only local state DB delta evidence and gate-on upload/delete service wiring; tests cover default-off no-write behavior, mismatch handling, and audit/delta/attribution linkage. | Operational use requires explicit mutation approval and gate-on approval. |
| Upload readiness hardening | `Completed` | `main` includes Start/Retry readiness hardening for local DB target class, Supabase API/DB/Edge readiness, Edge auth key class, and target-only row approval counts. | Does not approve Start Upload or Retry Failed. |
| API-mode operator package validation | `Completed` | Completion-track candidate `docs/166` records API-mode build, package assembly, zip/SHA-256 handoff metadata, launcher/shortcut `-CheckOnly`, and read-only HTTP smoke, plus the latest `a80876f` package metadata refresh for `ExtrusionWebConsole-a80876f-20260622-003633-680`. | This does not approve operator mutation and does not replace the `docs/164` accepted mutation package unless that gate is separately updated. |
| Operator data mutation gate | `Completed` | `docs/164` records current package metadata and exact approval templates for Preview-only, Start Upload, Retry Failed, and Delete. | Each mutation still requires its own exact approval at execution time. |
| Default-off date-scoped delete review shell | `Completed` | `docs/168` plus backend/frontend code provide a read-only gate and non-mutating Upload page shell; default settings render no normal-operator panel. | This is not an executable delete UI and does not approve gate enablement. |
| Operator-facing executable date-scoped delete UI | `Deferred` | `docs/161` still blocks enabled operator-facing executable UI; `docs/168` documents the completed review shell only. | Actual date-scoped delete preflight/start, role enforcement, limits, fixture evidence, production approval record, rollback evidence, and gate enablement remain separate blocked work. |
| Delete expansion beyond current selected `already_in_db` path | `Deferred` | `docs/170` requires explicit policy limits and fixture-first proof before broader delete capability can be implemented or discussed for operational data. | Fixture evidence, production approval format, limits, and separate approval. |
| Operational DB delete verification | `Deferred` | `docs/171` requires immutable or append-only approval storage, exact scope, no-undo acknowledgement, safe evidence report, and blocked rollback semantics before operational delete can be discussed. | Separate approval, current preflight evidence, and post-run evidence report. |
| Default-off LAN security guard | `Completed` | Backend code has a default-off `v2_lan_access_enabled` startup guard, request middleware blocks non-loopback client/server hosts when LAN is disabled, `/api/health` reports only sanitized LAN gate state, and `docs/172` records the safety boundary. | This does not approve LAN exposure, shared LAN identity, non-loopback bind, LAN CORS widening, or LAN rollout. |
| Multi-user LAN access | `Deferred` | `docs/159`, `docs/160`, `docs/161`, and `docs/172` block LAN, non-loopback bind, LAN CORS widening, LAN sessions, and LAN rollout; the guard is safety infrastructure only. | LAN authentication, authorization, role matrix, actor sessions, concurrency model, and explicit rescope. |
| Grafana/Vector observability hardening | `Completed` | Runtime readiness exposes sanitized Grafana and Vector status classes; Dashboard and package smoke guidance include Vector; `docs/167` records alert/runbook and rollback boundaries. | Raw log/metric/trace export, Grafana iframe embedding, LAN exposure, and cleanup/reset remain excluded. |
| Supabase schema attribution | `Deferred` | Current approved path is local sidecar only; `docs/169` defines the minimum design gate for a future Supabase attribution table without changing `all_metrics(timestamp, device_id)`. | Later written approval before migration/backfill/fixture mutation/operational DB access. |
| Full V2 release | `Partial` | Several foundations are complete, but operational upload verification, executable date-scoped delete, delete expansion execution, operational DB delete verification, Multi-user LAN, Supabase schema attribution, and release gates are incomplete. | Do not describe V2 as complete until every deferred item is explicitly resolved or excluded. |
| Cloud Supabase migration | `Excluded` | `docs/159` and README keep Cloud Supabase out of scope. | Later approved rescope only. |
| Default legacy upload state import | `Excluded` | `docs/159` and README keep default legacy state import out of scope. | Later approved rescope only. |
| Grafana iframe embedding | `Excluded` | `docs/159`, `docs/160`, and README keep Grafana separate and linked. | Later approved rescope only. |

## Operator Interpretation

The current safe statement is:

```text
V2 is not complete. Current main at `baee498` contains the already-merged local
evidence foundation, upload readiness hardening, and operator mutation gate
baseline. The completion-track candidate at `a80876f` adds the item 2
API-mode package evidence, item 7 Grafana/Vector observability evidence, the
default-off non-mutating date-scoped delete review shell, and the default-off
LAN security guard. Operational upload verification, executable date-scoped
delete, delete expansion execution, operational DB delete verification,
Multi-user LAN, Supabase schema attribution, and the overall V2 release remain
deferred or excluded until separate approvals resolve them.
```

Do not say:

```text
V2 is complete.
```

Do not use package `sourceCommit` values from older handoffs or from the latest
completion-track package refresh when approving a mutation from the accepted
`cb8a3c8` package unless `docs/164_operator_data_mutation_safety_gate.md` is
separately updated.

## Rollback

For this integration status update, before commit rollback is to inspect the
diff and revert only the specific integration hunks after confirming no
unrelated working-tree changes share the same files.

After commit, revert the specific integration merge or status-matrix commit. No
operational evidence, local state DB, Supabase data, Docker state, package
output, or LAN configuration should be deleted as rollback for this document.
