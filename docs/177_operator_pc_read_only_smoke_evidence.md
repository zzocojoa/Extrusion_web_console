# Operator-PC Read-Only Smoke Evidence

Status: `blocked_backend_not_already_running`

Evidence id: `WP-A-2026-07-10-001`

## Executive Summary

This document records the first WP-A read-only operator-PC smoke evidence package
from `docs/176_v1_cutover_go_no_go_validation_plan.md`.

The package did not start the app, backend, Supabase, Docker, LAN, upload,
delete, migration, cleanup, or deployment flow. It only inspected repository
metadata and attempted a single read-only `GET /api/health` request against the
already expected local loopback backend.

Result: `BLOCKED`. The local backend was not already running or did not respond
to the loopback health request. Per the task boundary, no backend start was
attempted. Because health was blocked, `/api/config`, `/api/audit?limit=1`, UI
route load checks, and docs-disabled route checks were not run.

## Decision Boundary

Allowed in this evidence package:

- read-only package/git metadata inspection;
- `GET /api/health` against an already running local backend;
- `GET /api/config` only if the backend is already running;
- `GET /api/audit?limit=1` only if the backend is already running;
- route load checks for `/`, `/upload`, `/logs`, and `/settings` only if the
  backend is already running;
- docs-disabled route checks for `/api/docs` and `/api/openapi.json` only if the
  backend is already running.

Forbidden and not run:

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
- production DB access or mutation.

## Source Document Confirmation

| Source | Confirmation |
| --- | --- |
| `AGENTS.md` | V1 is Core Ops only; web app remains localhost-only; dangerous operations require audit logging. |
| `README.md` | Read-only APIs such as `/api/health`, `GET /api/config`, and `GET /api/audit` are token-free; mutating APIs remain protected; runtime control is non-destructive and does not run reset/cleanup/bootstrap/create/delete. |
| `docs/164_operator_data_mutation_safety_gate.md` | Preview-only, Start Upload, Retry Failed, Upload Delete, Settings save, runtime start/stop, reset/cleanup, LAN, and deployment remain blocked without separate approval. |
| `docs/173_v2_operational_upload_verification_gate.md` | Operational upload verification is a four-step chain and this document does not approve Preview, Start Upload, Retry Failed, delete, Settings save, cleanup, LAN, deployment, DB writes, or source-file mutation. |
| `docs/175_legacy_gui_replacement_gap_audit.md` | Core Ops is mostly implemented, but operator-PC local evidence, Audit Logs visibility, fixture coverage, and Preview soak evidence remain cutover gates. |
| `docs/176_v1_cutover_go_no_go_validation_plan.md` | WP-A permits only non-destructive route/config/audit smoke evidence and explicitly forbids Preview creation, upload, retry, delete, settings save, runtime start/stop, reset, cleanup, LAN, deployment, and production DB access. |

## Evidence Matrix

| Evidence area | Command or observation | Sanitized result | Status |
| --- | --- | --- | --- |
| Current source commit | `git rev-parse HEAD` | `358209a5b61a8bb2424a3aa4b6e1c812e88afe72` | Pass |
| Working tree at evidence start | `git status --short --branch` before edits | Branch `docs/operator-pc-read-only-smoke-evidence`; no changed files before documentation edits | Pass |
| Current HEAD summary | `git log -1 --oneline` | `358209a docs: add v1 cutover go no-go validation plan (#223)` | Pass |
| Source document discoverability | `rg` in README Source Documents | `docs/176_v1_cutover_go_no_go_validation_plan.md` referenced | Pass |
| Evidence document discoverability | README Source Documents update | `docs/177_operator_pc_read_only_smoke_evidence.md` referenced | Pass |
| Backend health | `GET /api/health` against local loopback backend with a 3 second timeout | `reachable=false`; `result=blocked_backend_not_already_running_or_not_responding`; `errorClass=WebException`; `messageClass=connection_or_http_failure` | Blocked |
| Config snapshot | Not run | Blocked because `/api/health` did not prove an already running backend | Blocked |
| Audit latest row | Not run | Blocked because `/api/health` did not prove an already running backend | Blocked |
| UI route `/` | Not run | Blocked because backend was not already running | Blocked |
| UI route `/upload` | Not run | Blocked because backend was not already running | Blocked |
| UI route `/logs` | Not run | Blocked because backend was not already running | Blocked |
| UI route `/settings` | Not run | Blocked because backend was not already running | Blocked |
| Docs-disabled `/api/docs` | Not run | Blocked because backend was not already running | Blocked |
| Docs-disabled `/api/openapi.json` | Not run | Blocked because backend was not already running | Blocked |

## Sanitized `/api/health` Evidence

The health request was read-only and used only to detect whether an operator
backend was already available. It did not start any process.

```json
{
  "endpoint": "/api/health",
  "reachable": false,
  "result": "blocked_backend_not_already_running_or_not_responding",
  "errorClass": "WebException",
  "messageClass": "connection_or_http_failure"
}
```

No raw operational source paths, filenames, CSV content, timestamp/device keys,
DB URLs, tokens, JWTs, Authorization values, credentials, internal URLs, or
secrets were captured.

## Pass/Fail Interpretation

This evidence package is not a V1 cutover pass. It is a valid blocked WP-A
record.

Cutover implication:

- package/source metadata can be tied to the merged PR #223 commit;
- read-only operator backend smoke evidence is still missing;
- no config snapshot, audit row, UI route load, or docs-disabled route evidence
  was captured because the backend was not already running;
- the next attempt must use an already running operator backend/package and must
  still avoid all mutation and destructive commands.

## Remaining Cutover Gates

- WP-A read-only route/config/audit smoke evidence against an already running
  local backend remains open.
- WP-B read-only inventory precheck remains open.
- WP-C Preview-only approval and evidence remains blocked until separate
  approval.
- WP-D Start Upload approval package remains blocked until fresh Preview-only
  evidence proves target rows and separate approval is granted.
- WP-E Retry Failed approval package remains conditional and separate.
- WP-F destructive delete remains excluded unless a separate `docs/171` package
  is explicitly approved.
- Legacy CSV fixture expansion and large CSV Preview soak remain required before
  a full GO decision.

## Verification Performed

Commands run:

```powershell
git branch --show-current
git status --short --branch
Test-Path docs/177_operator_pc_read_only_smoke_evidence.md
git switch main
git pull --ff-only origin main
git switch -c docs/operator-pc-read-only-smoke-evidence
rg -n "V1 Scope|Core Ops|localhost|legacy upload state|Dangerous operations|Do not include|Local Supabase|Grafana|Upload Preview|Start Upload|Retry Failed|delete|LAN|reset|cleanup|production" AGENTS.md README.md
rg -n "Allowed without|Not allowed|Preview-only|Start Upload|Retry Failed|Upload Delete|Settings save|Local Supabase start/stop|Supabase reset|Docker cleanup|LAN|deployment|read-only inventory|production|approval" docs/164_operator_data_mutation_safety_gate.md
rg -n "does not approve|evidence chain|Preview-only|Start Upload|Retry Failed|Stop Conditions|sourceCommit|target rows|remaining physical rows|reset|cleanup|Docker|LAN|deployment|operational DB writes|source-file mutation" docs/173_v2_operational_upload_verification_gate.md
rg -n "Core Ops|Must-Fix|Deferred|Evidence Matrix|upload evidence|legacy CSV|large real CSV|operator-PC|Audit Logs|LAN|date-scoped|schema attribution|legacy upload state|reset|cleanup|README|Operational validation blockers" docs/175_legacy_gui_replacement_gap_audit.md
rg -n "Non-Destructive Validation Package|Allowed read-only|GET /api/config|GET /api/audit|GET /api/health|route load|docs-disabled|Not allowed|creating a Preview|Local Supabase start/stop|Final Sign-Off|WP-A|forbidden|source paths|secrets" docs/176_v1_cutover_go_no_go_validation_plan.md
rg -n "@router.get|@router.put|prefix=.*/api/config|ConfigResponse|value=None|secret|targetClasses|save_config" backend/app/api/config.py backend/app/services/config_service.py
rg -n "@router.get|prefix=.*/api/audit|limit|params_json_redacted|redact|sanitize|AuditLogListResponse|q" backend/app/api/audit.py backend/app/db/audit_repository.py
rg -n "api/health|health_router|configure_frontend_static|docs_enabled|openapi_url|redoc_url|localhost|loopback|lan_security_state|lan_auth_not_implemented|service" backend/app/main.py backend/app/core/lan_security.py backend/app/api/health.py
rg -n "FORBIDDEN_WORDS|supabase.*start|init|reset|rm|rmi|prune|compose.*up|compose.*down|container_not_allowed|command_not_allowed|shell_syntax_not_allowed" backend/app/services/command_runner.py
git rev-parse HEAD
git status --short --branch
git show --stat --oneline --name-status HEAD
Invoke-WebRequest -Uri http://127.0.0.1:8000/api/health -Method GET -TimeoutSec 3 -UseBasicParsing
Get-Date -Format o
git log -1 --oneline
rg -n "Source Documents|docs/176_v1_cutover_go_no_go_validation_plan.md|docs/175_legacy_gui_replacement_gap_audit.md" README.md
git diff --check
git diff -- README.md
```

Evidence capture time:

- `2026-07-10T00:10:15.9813038+09:00`

Files changed:

- `README.md`
- `docs/177_operator_pc_read_only_smoke_evidence.md`

Diff hygiene:

- `git diff --check` passed with only the existing README LF-to-CRLF
  working-copy normalization warning.
- Changed files are documentation-only.

Tests run:

- Runtime tests were not run because this is a documentation-only evidence
  record.

Commands intentionally not run:

- no backend/app start;
- no Upload Preview creation;
- no Upload Preview cancellation;
- no Start Upload;
- no Retry Failed;
- no upload delete preflight/start/reconcile;
- no Settings save;
- no Local Supabase start/stop;
- no Supabase init/reset/migration/backfill/cleanup;
- no Docker create/rm/prune/volume delete/compose up/down;
- no LAN enablement or non-loopback testing;
- no deployment;
- no production DB access or mutation.
