# Operator-PC Read-Only Smoke Evidence After Backend Readiness

Status: `read_only_smoke_blocked`

Evidence id: `WP-A-2026-07-10-002`

Approval id: `backend-readiness-WP-A-2026-07-10-001`

## Executive Summary

This document records the WP-A read-only smoke retry after the human/operator
provided the bounded backend readiness approval from `docs/178` and confirmed
that the backend/package was already running.

The retry is still `read_only_smoke_blocked`. `GET /api/health` against the
approved loopback endpoint did not respond. Per `docs/178`, the evidence
collector stopped there and did not run `/api/config`, `/api/audit?limit=1`, UI
route checks, docs route checks, Preview, upload, retry, delete, Settings save,
Local Supabase lifecycle, Docker lifecycle, LAN exposure, deployment, production
DB access, source-file mutation, or feature-gate changes.

This evidence record does not approve V1 cutover and does not claim a GO state.

## Decision Boundary

Allowed in this retry:

- validate the filled `docs/178` approval record;
- inspect git/package metadata read-only;
- run `GET /api/health` against an already running localhost backend;
- run later read-only config/audit/route checks only if health proves the
  expected Extrusion Web Console localhost-only backend.

Not allowed in this retry:

- starting backend/app/package processes;
- Upload Preview creation or cancellation;
- Start Upload;
- Retry Failed;
- upload delete preflight/start/reconcile;
- Settings save;
- Local Supabase start/stop;
- Supabase init/reset/migration/backfill/cleanup;
- Docker create/rm/prune/volume delete/compose up/down;
- LAN enablement or non-loopback testing;
- deployment;
- production DB access or mutation;
- source-file mutation;
- feature-gate changes.

## Source Document Confirmation

| Source | Confirmation |
| --- | --- |
| `AGENTS.md` | V1 remains Core Ops, localhost-only, with dangerous operations audited and legacy GUI state import excluded by default. |
| `README.md` | Read-only APIs such as `/api/health`, `GET /api/config`, and `GET /api/audit` are token-free; mutating APIs remain protected; operator launcher mode disables API docs routes. |
| `docs/164_operator_data_mutation_safety_gate.md` | Preview, upload, retry, delete, Settings save, runtime lifecycle, reset/cleanup, LAN, and deployment remain blocked without separate approval. |
| `docs/173_v2_operational_upload_verification_gate.md` | Operational upload evidence remains a separate four-phase chain and this retry does not approve Preview, Start Upload, Retry Failed, or DB writes. |
| `docs/175_legacy_gui_replacement_gap_audit.md` | Core Ops is mostly implemented, but cutover still requires fresh operational evidence and approval gates. |
| `docs/176_v1_cutover_go_no_go_validation_plan.md` | WP-A allows only non-destructive operator-PC route/config/audit smoke evidence against an already running local package. |
| `docs/177_operator_pc_read_only_smoke_evidence.md` | Prior WP-A evidence was blocked because `/api/health` was not reachable and no backend start was attempted. |
| `docs/178_operator_backend_readiness_approval_package.md` | A bounded human approval is required before one backend/package readiness attempt; the next collector may run only WP-A read-only checks after the backend is available. |

## Approval Record Validated

| Field | Supplied value |
| --- | --- |
| Approval id | `backend-readiness-WP-A-2026-07-10-001` |
| Approved package/source commit | `cb8a3c83de7437f127da71f013224e42a9a46219` |
| Approved package label | `ExtrusionWebConsole-cb8a3c8-20260621-160038-290` |
| Approved operator PC class | `intended_operator_pc_localhost_only` |
| Approved command class | `accepted package tray launch` |
| Approved bind scope | `localhost-only / 127.0.0.1` |
| Approved purpose | `WP-A read-only smoke evidence retry only` |
| Approver | `human_operator_approver` |
| Date/time | `2026-07-10T00:00:00+09:00` |
| Explicit exclusions acknowledged | `yes` |
| Backend/package state supplied by human/operator | `already running` |

Exact approval text supplied:

```text
I approve exactly one bounded local operator backend/package start attempt for `Extrusion_web_console`.

Approved package/source commit: cb8a3c83de7437f127da71f013224e42a9a46219
Approved package label: ExtrusionWebConsole-cb8a3c8-20260621-160038-290
Approved operator PC class: intended_operator_pc_localhost_only
Approved bind scope: localhost-only / 127.0.0.1
Approved purpose: make the backend available for WP-A read-only smoke evidence retry only.

This approval does not approve Upload Preview creation or cancellation, Start Upload, Retry Failed, upload delete preflight/start/reconcile, Settings save, Local Supabase start/stop, Supabase init/reset/migration/backfill/cleanup, Docker cleanup/rm/prune/volume delete/compose up/down, LAN exposure, deployment, production DB access, source-file mutation, or feature gate changes.
```

Validation result: `approval_record_complete_for_read_only_retry`.

## Package And Repository Metadata

| Field | Value |
| --- | --- |
| Evidence capture repository commit | `82c23b27c4434f0d751818c20afe373a12bdaccc` |
| Evidence capture branch | `docs/operator-pc-read-only-smoke-after-backend-readiness` |
| Latest merged documentation commit | `82c23b2 docs: add operator backend readiness approval package (#225)` |
| Approved package/source commit | `cb8a3c83de7437f127da71f013224e42a9a46219` |
| Approved package label | `ExtrusionWebConsole-cb8a3c8-20260621-160038-290` |

The approved package/source commit is the operator package identity from the
human approval record. The evidence capture repository commit is the local
documentation branch base after PR #225 landed.

## Evidence Matrix

| Check | Allowed command or observation class | Sanitized result | Status |
| --- | --- | --- | --- |
| Approval record | Validate filled `docs/178` fields before HTTP | Complete; explicit exclusions acknowledged; backend/package state supplied as already running | Pass |
| Backend health | `GET /api/health` against local loopback backend with timeout | `reachable=false`; `result=blocked_backend_not_reachable`; `errorClass=WebException`; `messageClass=connection_or_http_failure` | Blocked |
| Config snapshot | `GET /api/config` with sanitized output | Not run because `/api/health` did not prove the backend | Blocked |
| Audit latest row | `GET /api/audit?limit=1` with sanitized output | Not run because `/api/health` did not prove the backend | Blocked |
| UI route `/` | Route load check, no HTML body capture | Not run because `/api/health` did not prove the backend | Blocked |
| UI route `/upload` | Route load check, no HTML body capture | Not run because `/api/health` did not prove the backend | Blocked |
| UI route `/logs` | Route load check, no HTML body capture | Not run because `/api/health` did not prove the backend | Blocked |
| UI route `/settings` | Route load check, no HTML body capture | Not run because `/api/health` did not prove the backend | Blocked |
| Docs-disabled `/api/docs` | Status-code-only route check | Not run because `/api/health` did not prove the backend | Blocked |
| Docs-disabled `/api/openapi.json` | Status-code-only route check | Not run because `/api/health` did not prove the backend | Blocked |

## Sanitized `/api/health` Evidence

Observed at: `2026-07-10T01:22:32.3880211+09:00`

```json
{
  "endpoint": "/api/health",
  "reachable": false,
  "result": "blocked_backend_not_reachable",
  "errorClass": "WebException",
  "messageClass": "connection_or_http_failure"
}
```

No response body, token, config value, DB URL, source path, filename, CSV
content, raw key, audit params, or HTML body was captured.

## Pass/Fail Interpretation

Result: `read_only_smoke_blocked`.

The human/operator approval record was complete enough to allow a read-only
WP-A retry, and the human/operator stated the backend/package was already
running. However, the required first check, `/api/health`, did not respond on
the approved loopback endpoint. Per `docs/178`, no additional HTTP checks were
run after that blocked result.

This result preserves the prior WP-A blocker: operator-PC read-only route,
config, and audit smoke evidence is still missing.

## Remaining Cutover Gates

- Resolve backend/package availability for the approved localhost-only package
  without Codex starting processes or changing feature gates.
- Re-run WP-A only after a new or reaffirmed filled `docs/178` approval record
  and human/operator confirmation that the backend is already running.
- Capture sanitized `/api/health`, `/api/config`, `/api/audit?limit=1`, route
  load, and docs-disabled evidence if health passes.
- WP-B read-only inventory precheck remains pending.
- WP-C Preview-only approval and evidence remains pending and separate.
- WP-D Start Upload approval remains pending and separate after fresh Preview
  evidence proves exact target rows.
- WP-E Retry Failed approval remains conditional and separate.
- Destructive delete approval remains excluded and separate.

## Verification Performed

Commands run:

```powershell
git branch --show-current
git status --short --branch
git rev-parse HEAD
Test-Path docs/179_operator_pc_read_only_smoke_evidence_after_backend_readiness.md
rg -n "<targeted safety and endpoint patterns>" AGENTS.md README.md docs backend
Get-Content -Raw <mandatory source documents and reference code> | Measure-Object
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health" -Method GET -TimeoutSec 5
git show --stat --oneline --name-status HEAD
```

Commands intentionally not run:

- backend/app/package start;
- Local Supabase start/stop;
- Upload Preview creation or cancellation;
- Start Upload;
- Retry Failed;
- upload delete preflight/start/reconcile;
- Settings save;
- Supabase init/reset/migration/backfill/cleanup;
- Docker create/rm/prune/volume delete/compose up/down;
- LAN enablement or non-loopback test;
- deployment;
- production DB access;
- source-file mutation;
- feature-gate changes.

Tests run: none.

Tests not run: backend/frontend runtime tests were skipped because this evidence
record is documentation-only and no runtime code changed.

Files changed:

- `README.md`
- `docs/179_operator_pc_read_only_smoke_evidence_after_backend_readiness.md`
