# Operator Backend Readiness Approval Package

## Status

`approval_package_only_backend_not_started`

## Purpose

This package exists because WP-A read-only operator-PC smoke evidence was blocked
by local backend unavailability in
`docs/177_operator_pc_read_only_smoke_evidence.md`.

It prepares a bounded human approval to start or reuse the accepted local
operator backend/package on the intended operator PC only so WP-A read-only smoke
evidence can be retried later.

This document is not an execution record. No backend/app/package, Supabase,
Docker, Preview, upload, retry, delete, settings, migration, LAN, deployment, or
production DB command was run while creating it.

## Scope Boundary

This document separates these approval tracks:

| Track | Classification | This document's decision |
| --- | --- | --- |
| Backend/app/package start approval | Bounded readiness approval candidate | Prepares exact human approval wording only. |
| Read-only WP-A smoke retry | Non-destructive evidence collection | Allowed only after the backend is already running. |
| Local Supabase start/stop approval | Runtime lifecycle approval | Not approved here; remains separate. |
| Preview-only approval | Local-state write plus DB read/reconcile | Not approved here; use `docs/164` and `docs/173`. |
| Start Upload approval | Limited operational DB mutation | Not approved here; requires fresh Preview-only evidence and separate approval. |
| Retry Failed approval | Conditional upload action | Not approved here; requires failed/retryable job evidence and separate approval. |
| Destructive delete approval | Production-critical destructive mutation | Not approved here; use the `docs/171` package if ever required. |
| Deferred V2 items | Out of V1 scope or deferred | LAN, delete expansion, schema migration/backfill, reset, cleanup, and deployment remain excluded. |

This document does not approve any item except preparing the human approval
wording and runbook boundary for backend/app/package readiness.

## Source Documents

- `docs/164_operator_data_mutation_safety_gate.md`
- `docs/173_v2_operational_upload_verification_gate.md`
- `docs/175_legacy_gui_replacement_gap_audit.md`
- `docs/176_v1_cutover_go_no_go_validation_plan.md`
- `docs/177_operator_pc_read_only_smoke_evidence.md`
- `README.md`
- `docs/32_operator_package_handoff_runbook.md`
- `docs/operator_package_runtime_note.md`

## Current Blocked Evidence

| Field | Value |
| --- | --- |
| Evidence id | `WP-A-2026-07-10-001` |
| Status | `blocked` |
| Source commit at evidence capture | `358209a5b61a8bb2424a3aa4b6e1c812e88afe72` |
| Current accepted main commit for this package | `32ec7df53a97cd0513066110ffc2c1deb66e3c76` |
| Health result | `/api/health` was not reachable or did not respond on the expected local loopback backend. |
| Checks not run | `/api/config`, `/api/audit?limit=1`, `/`, `/upload`, `/logs`, `/settings`, `/api/docs`, and `/api/openapi.json`. |
| Start attempt during evidence capture | None. |

## Approval Candidate

Candidate action:

- exactly one bounded attempt to start or reuse the accepted local operator
  backend/package on the operator PC;
- localhost-only bind scope;
- expected local browser target is same-origin loopback web console;
- purpose is only to make the backend available for WP-A read-only smoke retry;
- no non-loopback bind;
- no LAN exposure;
- no Settings save;
- no Upload Preview creation or cancellation;
- no upload, retry, or delete;
- no Local Supabase start/stop;
- no Supabase reset, migration, backfill, bootstrap, or cleanup;
- no Docker cleanup or destructive command;
- no deployment;
- no production DB access or mutation.

## Required Preconditions

Before requesting the approval wording below, all of these must be true:

- local repository commit or accepted package source commit is known;
- package label is known;
- operator PC is the intended machine;
- accepted package/runbook source is available to the human operator or
  maintainer;
- no active Preview, upload, retry, or delete job is intentionally being
  manipulated by this approval;
- no feature gate changes are requested;
- no Local Supabase lifecycle change is bundled;
- no raw secrets, operational source paths, filenames, CSV content,
  timestamp/device keys, DB URLs, tokens, JWTs, Authorization values,
  credentials, internal URLs, or raw HTML bodies will be captured in evidence;
- operator understands this is only to make the backend available for a later
  read-only WP-A retry.

## Allowed Command Classes

Only command classes already documented in repository docs are listed here. This
document does not execute any of them.

| Command class | Concrete command if documented | Use in this approval | Source |
| --- | --- | --- | --- |
| Accepted package tray launch | `launcher\tray_supervisor.ps1` or the installed `Extrusion Web Console` shortcut | Allowed only after the human approval is filled; starts or reuses localhost backend through the documented tray path. | `README.md`; `docs/operator_package_runtime_note.md`; `docs/32_operator_package_handoff_runbook.md` |
| Accepted package direct launcher start | `launcher\start_web_console.ps1` or `launcher\start_web_console.bat` | Allowed only after the human approval is filled; starts or reuses localhost backend on the approved port. | `README.md`; `launcher/start_web_console.ps1` |
| Launcher prerequisite check | `launcher\start_web_console.ps1 -CheckOnly` | Documentation says this verifies prerequisites without starting a backend process. It may be used before approval if the human wants a non-starting readiness check. | `README.md`; `docs/32_operator_package_handoff_runbook.md`; `launcher/start_web_console.ps1` |
| Tray prerequisite check | `launcher\tray_supervisor.ps1 -CheckOnly` | Documentation says this checks tray prerequisites without starting backend or tray icon. | `docs/32_operator_package_handoff_runbook.md`; `docs/operator_package_runtime_note.md`; `launcher/tray_supervisor.ps1` |
| Shortcut prerequisite check | `launcher\install_shortcuts.ps1 -CheckOnly` | Documentation says this previews shortcut paths and writes no shortcuts. | `README.md`; `docs/32_operator_package_handoff_runbook.md`; `launcher/install_shortcuts.ps1` |
| Route health check after human start | `GET /api/health` on the approved localhost backend | Allowed after the human start attempt to confirm backend availability for WP-A retry. | `README.md`; `docs/176_v1_cutover_go_no_go_validation_plan.md`; `backend/app/main.py` |

If the accepted package runbook supplies a different approved operator start
entry point, record it as:

```text
<approved_operator_package_start_command_from_package_runbook>
```

Do not invent a new command. Do not use maintainer/developer commands as an
operator package start path unless the accepted package runbook explicitly
approves them for the target machine.

## Forbidden Commands

This package does not approve:

- Upload Preview creation or cancellation;
- Start Upload;
- Retry Failed;
- upload delete preflight/start/reconcile;
- Settings save;
- Local Supabase start/stop;
- Supabase init/reset/migration/backfill/cleanup;
- Docker create/rm/prune/volume delete/compose up/down;
- LAN enablement or non-loopback bind/CORS widening;
- deployment;
- production DB access or mutation;
- raw DB SQL;
- manual DB cleanup;
- source-file mutation;
- feature gate changes.

## Required Human Approval Wording

The approval must be filled exactly for one bounded attempt:

```text
I approve exactly one bounded local operator backend/package start attempt for `Extrusion_web_console`.

Approved package/source commit: <sourceCommit>
Approved package label: <packageLabel>
Approved operator PC class: <operatorPcClass>
Approved bind scope: localhost-only / 127.0.0.1
Approved purpose: make the backend available for WP-A read-only smoke evidence retry only.

This approval does not approve Upload Preview creation or cancellation, Start Upload, Retry Failed, upload delete preflight/start/reconcile, Settings save, Local Supabase start/stop, Supabase init/reset/migration/backfill/cleanup, Docker cleanup/rm/prune/volume delete/compose up/down, LAN exposure, deployment, production DB access, source-file mutation, or feature gate changes.
```

## Approval Record Template

| Field | Value |
| --- | --- |
| Approval id | `<backendReadinessApprovalId>` |
| Approval text | `<exact text from Required Human Approval Wording>` |
| Approved source commit | `<sourceCommit>` |
| Approved package label | `<packageLabel>` |
| Approved operator PC class | `<operatorPcClass>` |
| Approved command class | `<tray launch | direct launcher start | approved package start command>` |
| Approved bind scope | `localhost-only / 127.0.0.1` |
| Approved purpose | `WP-A read-only smoke evidence retry only` |
| Approver | `<approver>` |
| Date/time | `<ISO-8601 local time>` |
| Explicit exclusions acknowledged | `<yes/no>` |

Do not store raw token values, DB URLs, operational source paths, filenames, CSV
content, timestamp/device keys, raw HTML bodies, internal URLs, or credentials in
the approval record.

## Bounded Human Procedure

1. Verify the accepted source commit and package label match the approval record.
2. Confirm the operator PC class matches the approval record.
3. Confirm no request bundles Preview, upload, retry, delete, Settings save,
   Local Supabase lifecycle, Docker cleanup, LAN, migration, deployment, or DB
   access.
4. If desired, run only documented `-CheckOnly` command classes before start.
   These are not backend starts.
5. Run exactly one approved package/backend start attempt using the approved
   command class or the package runbook placeholder.
6. After the start attempt, run only read-only WP-A retry checks if the backend
   is available.
7. If `/api/health` is still unavailable, record a blocked result. Do not retry
   by changing settings, starting Supabase, cleaning Docker, resetting data, or
   enabling LAN.

## Read-Only WP-A Retry After Approval

After a human-approved backend/package start attempt succeeds, the next evidence
collector may run only the WP-A checks from `docs/176`:

- `GET /api/health`;
- `GET /api/config` with sanitized output;
- `GET /api/audit?limit=1` with sanitized output;
- route load checks for `/`, `/upload`, `/logs`, and `/settings`;
- docs-disabled checks for `/api/docs` and `/api/openapi.json`.

If `/api/health` is not reachable, stop and record blocked evidence again.

## Stop Conditions

Stop before approval or execution when any of these are true:

- source commit or package label is unknown;
- operator PC class is unknown or mismatched;
- approved command class is not documented in the accepted package/runbook;
- a request includes Preview, upload, retry, delete, Settings save, Supabase
  lifecycle, Docker cleanup, reset, migration, LAN, deployment, production DB
  access, source-file mutation, or feature gate changes;
- a raw secret, DB URL, token, JWT, Authorization value, operational source
  path, filename, CSV content, timestamp/device key, internal URL, credential, or
  raw HTML body would be captured;
- backend binds to anything other than localhost-only / `127.0.0.1`;
- `/api/health` reports a non-Extrusion Web Console service or non-localhost-only
  class.

## Evidence To Capture After Human Start

The next evidence record should capture only sanitized fields:

| Evidence field | Allowed value class |
| --- | --- |
| Approval id | Safe id |
| Source commit | Commit hash |
| Package label | Safe package label |
| Operator PC class | Safe class |
| Command class used | Safe command class, not raw absolute path |
| Health status | Safe status and service class |
| LAN class | `localhost_only` or blocked reason class |
| Config snapshot | Sanitized source/target classes only |
| Audit latest row | Sanitized action/result/reason classes only |
| Route checks | Status code/class only, no full HTML body |

## Verification Performed

Commands run while creating this documentation-only package:

```powershell
git branch --show-current
git status --short --branch
Test-Path docs/178_operator_backend_readiness_approval_package.md
git switch main
git pull --ff-only origin main
git switch -c docs/operator-backend-readiness-approval-package
rg -n "V1 Scope|Core Ops|localhost-only|localhost only|Dangerous operations|Do not include|Local Supabase|Upload Preview|Start Upload|Retry Failed|Settings save|delete|LAN|reset|cleanup|deployment|package|launcher" AGENTS.md README.md
rg -n "Do not run|Allowed without|Not allowed|Preview-only|Start Upload|Retry Failed|Upload Delete|Settings save|Local Supabase start/stop|Supabase reset|Docker cleanup|LAN|deployment|approval|mutation" docs/164_operator_data_mutation_safety_gate.md
rg -n "does not approve|evidence chain|Preview-only|Start Upload|Retry Failed|Stop Conditions|reset|cleanup|Docker|LAN|deployment|operational DB writes|source-file mutation|approval" docs/173_v2_operational_upload_verification_gate.md
rg -n "Core Ops|Must-Fix|Deferred|operator-PC|Audit Logs|Local Supabase|upload evidence|legacy CSV|large real CSV|LAN|reset|cleanup|Operational validation|README/API" docs/175_legacy_gui_replacement_gap_audit.md
rg -n "Non-Destructive Validation Package|WP-A|backend|already running|GET /api/health|GET /api/config|GET /api/audit|not allowed|creating a Preview|Start Upload|Retry Failed|Local Supabase start/stop|Docker|LAN|deployment|production DB|approval|Final Sign-Off" docs/176_v1_cutover_go_no_go_validation_plan.md
rg -n "blocked_backend_not_already_running|WP-A-2026-07-10-001|GET /api/health|not already running|no backend/app start|not a V1 cutover pass|Remaining Cutover Gates|no Upload Preview|no Start Upload|no Retry Failed|no Local Supabase|no Docker|no LAN|no deployment|no production DB" docs/177_operator_pc_read_only_smoke_evidence.md
rg -n "CheckOnly|start_web_console|tray|shortcut|GET /api/health|localhost|127.0.0.1|cleanup|reset|Docker|Supabase|Preview|Start Upload|Retry Failed" README.md docs/32_operator_package_handoff_runbook.md docs/operator_package_runtime_note.md launcher packaging
rg -n "api/health|configure_frontend_static|docs_enabled|openapi_url|docs_url|redoc_url|127.0.0.1|localhost|loopback|lan_security|EWC_HOST|include_router" backend/app/main.py backend/app/api/config.py backend/app/api/audit.py backend/app/core/lan_security.py
rg -n "runtime.start|runtime.stop|supabase start|docker.*start|docker.*stop|required_container_missing|FORBIDDEN_WORDS|init|reset|rm|rmi|prune|compose.*up|compose.*down|CommandPolicyError|container_not_allowed" backend/app/services/runtime_control.py backend/app/services/command_runner.py
git rev-parse HEAD
git log -1 --oneline
rg -n "Source Documents|docs/177_operator_pc_read_only_smoke_evidence.md|docs/176_v1_cutover_go_no_go_validation_plan.md" README.md
rg -n "^# Operator Backend Readiness Approval Package|^## Status|^## Purpose|^## Scope Boundary|^## Source Documents|^## Current Blocked Evidence|^## Approval Candidate|^## Required Preconditions|^## Allowed Command Classes|^## Forbidden Commands|^## Required Human Approval Wording|^## Approval Record Template|^## Bounded Human Procedure|^## Read-Only WP-A Retry After Approval|^## Stop Conditions|^## Evidence To Capture After Human Start|^## Verification Performed" docs/178_operator_backend_readiness_approval_package.md
git diff --check
git diff -- README.md
```

Files changed:

- `README.md`
- `docs/178_operator_backend_readiness_approval_package.md`

Diff hygiene:

- `git diff --check` passed with only the existing README LF-to-CRLF
  working-copy normalization warning.
- Changed files are documentation-only.

Tests run:

- Runtime tests were not run because this is a documentation-only approval
  package.

Commands intentionally not run:

- no backend/app/package launcher start;
- no Local Supabase start/stop;
- no Upload Preview creation or cancellation;
- no Start Upload;
- no Retry Failed;
- no upload delete preflight/start/reconcile;
- no Settings save;
- no Supabase init/reset/migration/backfill/cleanup;
- no Docker create/rm/prune/volume delete/compose up/down;
- no LAN enablement or non-loopback testing;
- no deployment;
- no production DB access or mutation.
