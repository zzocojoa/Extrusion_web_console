# V2 Status Matrix

Date: 2026-07-13 Asia/Seoul

Status: `main_baseline_with_wp01_and_operator_preview_evidence`

## Purpose

This document records the V2 plan-to-implementation status on current `main`.
It prevents completed foundations and narrow operator evidence from being
mistaken for a complete V2 release or for mutation approval.

This document does not approve code changes, operational DB access, Upload
Preview, Start Upload, Retry Failed, Delete, Settings save, feature-gate
enablement, LAN exposure, Supabase reset/cleanup, Docker cleanup, deployment,
commit, push, or PR creation.

## Evidence Reviewed

- Current `main` and `origin/main` baseline:
  `5695b93802f78f2e04a1aa83662e9400e1d49db2`.
- PR #229 is merged as the narrow Upload Job SSE/startup-recovery reliability
  patch. PR #230 is merged as the actual V2 WP-01 reliability foundation,
  including Preview DB-status correctness, representative legacy fixtures,
  synthetic large-Preview soak, Audit Logs failure-path coverage, route tests,
  launcher readiness checks, and duplicate LAN-setting cleanup.
- Historical operator mutation package metadata retained in `docs/164`:
  - `sourceCommit`: `cb8a3c8`
  - `packageLabel`: `ExtrusionWebConsole-cb8a3c8-20260621-160038-290`
  - `frontendMode`: `api`
  - `runtimeMode`: `operator-ready`
  - `zipCreated`: `false`
- Package evidence policy:
  - approval-time verification from the generated package
    `package-build-info.json` is canonical;
  - static `sourceCommit` and `packageLabel` values in this document are
    samples, not evergreen approval evidence;
  - before any future mutation approval, package `sourceCommit` must match the
    source commit named by that approval, or the package evidence remains
    sample-only and execution must stop.
- Historical local verification sample, not current approval evidence:
  - `sourceCommit`: `e405fcd`
  - `packageLabel`: `ExtrusionWebConsole-e405fcd-20260622-024709-519`
  - `createdUtc`: `2026-06-22T02:47:16.2854392Z`
  - `frontendMode`: `api`
  - `runtimeMode`: `operator-ready`
  - `frontendBuildMetadataPresent`: `true`
  - `zipCreated`: `false`
  - `zipSha256`: `not_applicable`
- Reviewed planning and implementation documents. `docs/159` through
  `docs/174` are merged `main` documents; their stored package samples do not
  become evergreen approval values.
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
  current `main`.
- Separately approved post-merge Preview-only operator-PC evidence for run
  `prv_ca38650a9e7d`: `succeeded`, DB `reachable`, 12 files, 0 target files,
  0 risky files, and Start Upload disabled. No Start Upload, Retry Failed,
  delete, Settings save, LAN, deployment, migration, reset, cleanup, or data
  mutation was executed in that evidence run.

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
| 1 | Operational upload verification | `Partial` | One separately approved post-merge `folder_all` Preview-only run succeeded on the operator PC with DB reachable, 12 files, `target=0`, `risky=0`, 64,766 partial-overlap rows excluded from target-only upload, matching Audit evidence, and Start Upload disabled. `docs/173` remains the evidence-chain source and `docs/164` remains the approval-wording source. | Start Upload is not applicable to the observed zero-target-only run. Formal inventory/package binding and partial-overlap disposition remain pending; any future action requires fresh scope evidence and its own exact approval. |
| 2 | API-mode package full runtime smoke and zip handoff | `Completed` | `docs/166` records API-mode build, package assembly, zip/SHA-256 metadata, launcher/shortcut `-CheckOnly`, and read-only HTTP smoke. | Does not approve operator mutation or replace the accepted mutation package in `docs/164`. |
| 3 | Operator-facing date-scoped delete UI | `Deferred` | `docs/168` completes only the default-off, non-mutating review shell for copy, i18n, and runbook review. | Executable/operator-facing date-scoped delete remains blocked until role matrix, policy/preflight, fixture evidence, production approval record, rollback evidence, and separate gate enablement are approved. |
| 4 | Delete expansion | `Deferred` | `docs/170` defines the fixture-first gate; `docs/160` defines the design constraints; `docs/161` leaves numeric limits and broader policy unapproved. | Concrete policy limits, fixture DB evidence, preflight/reconcile/audit/rollback proof, and separate approval. |
| 5 | Operational DB delete verification | `Deferred` | `docs/171` defines the approval record, storage, evidence report, rollback, and stop-condition gate; `docs/164` keeps exact destructive approval wording. | Exact approval record, safe evidence report, and separate approval before any operational DB delete. |
| 6 | Multi-user LAN | `Deferred` | `docs/172` adds a default-off startup guard and sanitized health state; `docs/159`, `docs/160`, and `docs/161` still block LAN exposure. | Auth/authz/session/actor audit/concurrency/CORS/bind implementation, tests, and explicit rescope. |
| 7 | Grafana/Vector observability hardening | `Completed` | `docs/167` records sanitized Grafana/Vector status classes, Vector runtime row implementation, alert/runbook classes, package/runtime checks, and explicit raw log/metric/trace export exclusions. Current operator-PC observation correctly reports non-core attention while API, DB, Studio, and Edge remain ready. | Cutover needs either resolution of the Grafana/Vector attention or explicit residual-risk acceptance with an owner and stop/rollback procedure. This does not approve cleanup, reset, LAN exposure, or operator mutation. |
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
| API-mode operator package validation | `Completed` | Merged `docs/166` records API-mode build, package assembly, zip/SHA-256 handoff metadata, launcher/shortcut `-CheckOnly`, and read-only HTTP smoke. Static metadata in that document is historical sample evidence only. | Verify current `package-build-info.json`, package label, and source commit before final cutover sign-off or any future mutation. |
| Operator data mutation gate | `Completed` | `docs/164` retains historical accepted-package metadata and exact approval templates for Preview-only, Start Upload, Retry Failed, and Delete. | Refresh package metadata from the executing artifact and obtain a separate exact approval before any future action. |
| Default-off date-scoped delete review shell | `Completed` | `docs/168` plus backend/frontend code provide a read-only gate and non-mutating Upload page shell; default settings render no normal-operator panel. | This is not an executable delete UI and does not approve gate enablement. |
| Operator-facing executable date-scoped delete UI | `Deferred` | `docs/161` still blocks enabled operator-facing executable UI; `docs/168` documents the completed review shell only. | Actual date-scoped delete preflight/start, role enforcement, limits, fixture evidence, production approval record, rollback evidence, and gate enablement remain separate blocked work. |
| Delete expansion beyond current selected `already_in_db` path | `Deferred` | `docs/170` requires explicit policy limits and fixture-first proof before broader delete capability can be implemented or discussed for operational data. | Fixture evidence, production approval format, limits, and separate approval. |
| Operational DB delete verification | `Deferred` | `docs/171` requires immutable or append-only approval storage, exact scope, no-undo acknowledgement, safe evidence report, and blocked rollback semantics before operational delete can be discussed. | Separate approval, current preflight evidence, and post-run evidence report. |
| Default-off LAN security guard | `Completed` | Backend code has a default-off `v2_lan_access_enabled` startup guard, request middleware blocks non-loopback client/server hosts when LAN is disabled, `/api/health` reports only sanitized LAN gate state, and `docs/172` records the safety boundary. | This does not approve LAN exposure, shared LAN identity, non-loopback bind, LAN CORS widening, or LAN rollout. |
| Multi-user LAN access | `Deferred` | `docs/159`, `docs/160`, `docs/161`, and `docs/172` block LAN, non-loopback bind, LAN CORS widening, LAN sessions, and LAN rollout; the guard is safety infrastructure only. | LAN authentication, authorization, role matrix, actor sessions, concurrency model, and explicit rescope. |
| Grafana/Vector observability hardening | `Completed` | Runtime readiness exposes sanitized Grafana and Vector status classes; Dashboard and package smoke guidance include Vector; `docs/167` records alert/runbook and rollback boundaries. | Resolve current attention or record explicit residual-risk acceptance, an owner, and a stop/rollback procedure before cutover; raw export, iframe embedding, LAN, and cleanup/reset remain excluded. |
| Supabase schema attribution | `Deferred` | Current approved path is local sidecar only; `docs/169` defines the minimum design gate for a future Supabase attribution table without changing `all_metrics(timestamp, device_id)`. | Later written approval before migration/backfill/fixture mutation/operational DB access. |
| Full V2 release | `Partial` | Several foundations are complete, but operational upload verification, executable date-scoped delete, delete expansion execution, operational DB delete verification, Multi-user LAN, Supabase schema attribution, and release gates are incomplete. | Do not describe V2 as complete until every deferred item is explicitly resolved or excluded. |
| Cloud Supabase migration | `Excluded` | `docs/159` and README keep Cloud Supabase out of scope. | Later approved rescope only. |
| Default legacy upload state import | `Excluded` | `docs/159` and README keep default legacy state import out of scope. | Later approved rescope only. |
| Grafana iframe embedding | `Excluded` | `docs/159`, `docs/160`, and README keep Grafana separate and linked. | Later approved rescope only. |

## Operator Interpretation

The current safe statement is:

```text
V2 is not complete. Current main at `5695b93` includes the merged evidence
foundation, upload readiness hardening, operator mutation gates, API-mode
package evidence, Grafana/Vector status hardening, default-off date-scoped
delete review shell, default-off LAN guard, Upload Job SSE/startup-recovery
patch, and V2 WP-01 reliability foundation. One separately approved Preview-only
operator-PC run persisted local run/audit state without operational DB mutation
and succeeded with zero target and risky files but 64,766 partial-overlap rows
excluded from target-only upload. Operational upload verification is Partial;
Start Upload and Retry Failed were not applicable and were not executed.
Package/inventory binding and partial-overlap disposition remain pending.
Executable date-scoped delete, delete expansion execution,
operational DB delete verification, Multi-user LAN, Supabase schema
attribution, and the overall V2 release remain deferred or excluded.
```

Do not say:

```text
V2 is complete.
```

Do not use package `sourceCommit` values from older handoffs or local
verification samples for a future mutation approval. The `cb8a3c8` values in
`docs/164_operator_data_mutation_safety_gate.md` are historical until that gate
is separately updated and matched to the executing artifact.

## Rollback

For this integration status update, before commit rollback is to inspect the
diff and revert only the specific integration hunks after confirming no
unrelated working-tree changes share the same files.

After commit, revert the specific integration merge or status-matrix commit. No
operational evidence, local state DB, Supabase data, Docker state, package
output, or LAN configuration should be deleted as rollback for this document.
