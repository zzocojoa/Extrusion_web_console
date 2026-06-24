# V2 Grafana/Vector Observability Hardening Evidence

Date: 2026-06-22 Asia/Seoul

Status: `candidate_observability_hardening_passed`

## Purpose

This document records the V2 item 7 implementation evidence for Grafana/Vector
observability hardening inside the local web console scope.

This evidence does not approve Upload Preview, Start Upload, Retry Failed,
Delete, Settings save, feature-gate enablement, Supabase reset/cleanup, Docker
cleanup, LAN exposure, deployment, Grafana iframe embedding, or operational data
mutation.

## Implemented Scope

Implemented:

- `/api/runtime/local-supabase` now exposes a separate `vector` status object.
- Vector status uses only sanitized Docker container status classes such as
  `ready`, `stopped`, `missing`, `unhealthy`, or `unknown`.
- Vector non-ready states are non-core runtime attention when API, DB, Studio,
  Edge, and required container existence gates are otherwise satisfied.
- Runtime Start now recovers an existing stopped Vector container that Runtime
  Stop can stop as part of local Supabase shutdown. This is limited to an
  already-existing `supabase_vector_*` container with stopped status; missing or
  otherwise unhealthy Vector remains non-core runtime attention and is not
  recreated by reset, cleanup, prune, or broad container deletion.
- Dashboard runtime checks show a separate Vector row.
- `/api/dashboard` runtime checks include Vector as a separate observability row.
- Package manifest smoke guidance now includes read-only
  `/api/runtime/local-supabase` verification for sanitized Grafana and Vector
  status classes. Evidence must record only `overallStatus`, `grafana.status`,
  `vector.status`, and `vector.detail`, not the full JSON response.
- The operator package runtime note records that Grafana and Vector evidence
  must remain sanitized and that Grafana iframe embedding remains excluded.
- Docker Desktop `Expose daemon on tcp://localhost:2375 without TLS` is
  documented as a default-off maintainer diagnostic setting, not an operator
  runtime requirement.

Not implemented by design:

- raw Grafana, Vector, Docker, Supabase, or Edge log export;
- raw metrics payload export;
- raw trace payload export;
- generated credential, DB URL, Authorization, JWT, raw source path, or raw CSV
  content capture;
- Grafana iframe embedding;
- LAN exposure or non-loopback bind changes.

## Docker Desktop 2375 Policy

Docker Desktop's `Expose daemon on tcp://localhost:2375 without TLS` setting
must stay off for normal operator use, package handoff, and routine runtime
smoke. It is a developer/maintainer diagnostic exception only.

Temporary enablement is allowed only for:

- developer diagnostics;
- release validation;
- failure reproduction when sanitized Docker or Vector log evidence is needed
  and cannot be collected through the normal status-class probes.

After the diagnostic evidence is captured, return the setting to off and record
that it was returned off in the validation note. Do not treat port `2375` as a
package prerequisite, operator setup step, or LAN access mechanism.

Vector `attention` or `needs-check` remains a non-core observability caveat
when Supabase API, DB, Edge, Upload Preview, and Audit evidence are normal. It
does not approve Upload Preview, Start Upload, Retry Failed, Delete, Settings
save, Supabase reset/cleanup, Docker cleanup, LAN exposure, deployment, or any
operational DB mutation.

## Alert And Runbook Classes

Operator-facing alert classes:

| Condition | Class | Operator action |
| --- | --- | --- |
| API, DB, Studio, or Edge is not reachable | `core_runtime_unreachable` | Stop upload mutation flow and inspect runtime readiness. |
| Grafana is unreachable while core runtime is ready | `non_core_runtime_attention` | Continue core upload review only if Grafana is not an acceptance gate; record caveat. |
| Vector is stopped while core runtime is ready and the container already exists | `non_core_runtime_attention` | Runtime Start may restart that existing Vector container and then record sanitized status-class evidence. Do not turn Docker Desktop `2375` on unless a maintainer diagnostic needs sanitized log evidence. |
| Vector is unhealthy, missing, or unknown while core runtime is ready | `non_core_runtime_attention` | Record only the sanitized status class and observability caveat; do not run cleanup/reset/prune or keep Docker Desktop `2375` enabled as a workaround. |
| Raw log, metric, trace, DB URL, token, JWT, source path, filename, or CSV content appears in evidence | `redaction_failure` | Stop and redact before sharing or merging evidence. |

Rollback and recovery:

- Do not delete operational DB rows.
- Do not delete local state DB evidence.
- Do not run Supabase reset/cleanup, Docker cleanup, prune, or broad container
  deletion.
- Do not leave Docker Desktop `Expose daemon on tcp://localhost:2375 without
  TLS` enabled after a bounded maintainer diagnostic.
- If stopped Vector recovery is wrong, revert the runtime-control follow-up
  commit or fix forward. Do not use reset/cleanup/prune as rollback.
- If the new Vector row is wrong, revert the code/docs commit or fix forward
  with sanitized status-class evidence.
- If runtime evidence has already been recorded, preserve it and add a corrected
  follow-up record instead of deleting the evidence.

## Validation

Targeted validation:

- `.\.venv\Scripts\python -m pytest tests\backend\test_runtime_control.py tests\backend\test_runtime_api.py tests\backend\test_dashboard.py tests\backend\test_operator_package_assembly.py`:
  `68 passed, 2 warnings`
- `cd frontend; npm run typecheck`: passed
- `git diff --check`: passed

Full validation:

- `.\.venv\Scripts\python -m pytest tests\backend`: `348 passed, 18 warnings`
- `cd frontend; npm run build:api`: passed, `frontend build mode: api`
- `.\packaging\assemble_operator_package.ps1 -FrontendMode api -CreateZip`:
  passed; package rebuilt from current branch `HEAD`
- `launcher/start_web_console.ps1 -CheckOnly`: passed; no backend process was
  started
- `launcher/install_shortcuts.ps1 -CheckOnly`: passed; no shortcuts were written

Candidate package metadata:

- `packageLabel`: `ExtrusionWebConsole-041e6ee-20260621-200102-587`
- `sourceCommit`: `041e6ee`
- `frontendMode`: `api`
- `runtimeMode`: `operator-ready`
- `zipCreated`: `true`
- `zipSha256`: `e5464be7626ef2a6c7edf97c39def4aa6e4d3baf60c80c9c00c6b7b8bb1249d4`
- `packageAgentEntries`: `0`
- `zipAgentEntries`: `0`

Read-only package HTTP smoke:

| Route | Status | Expected |
| --- | ---: | --- |
| `/` | `200` | pass |
| `/upload` | `200` | pass |
| `/logs` | `200` | pass |
| `/settings` | `200` | pass |
| `/api/health` | `200` | pass |
| `/api/config` | `200` | pass |
| `/api/audit?limit=1` | `200` | pass |
| `/api/runtime/local-supabase` | `200`; recorded only `overallStatus=attention`, `grafana.status=unreachable`, `vector.status=stopped`, and `vector.detail="Vector container status class is stopped."` | pass, sanitized status fields only |
| `/api/docs` | `404` | pass, operator docs disabled |
| `/api/openapi.json` | `404` | pass, operator docs disabled |
| `POST /api/upload/preview` without local token | `403` | pass, rejected before mutation |

Independent `$review` rerun after the Vector start-gate and Dashboard tone fixes:
`No actionable findings.`

Follow-up validation for stopped Vector recovery:

- Targeted runtime-control test selection:
  `test_start_recovers_stopped_vector_non_core_attention`,
  `test_start_times_out_when_started_vector_stays_unhealthy`,
  `test_start_noops_when_runtime_core_is_already_ready`, and
  `test_start_blocks_when_required_container_missing_and_never_runs_supabase_start`:
  `4 passed, 1 warning`
- `git diff --check`: passed
- `.\.venv\Scripts\python -m pytest tests\backend\test_runtime_control.py tests\backend\test_runtime_api.py tests\backend\test_health.py`:
  `35 passed, 2 warnings`
- `.\.venv\Scripts\python -m pytest tests\backend`: `362 passed, 18 warnings`
- `.\packaging\assemble_operator_package.ps1 -FrontendMode api`: passed
- Independent `$review`: first pass requested changes for unhealthy started
  Vector readiness; after requiring started containers to be both running and
  `ready`, rerun reported `No actionable findings.`

## Security Notes

The implementation reads existing Docker container status summaries already used
by runtime readiness. It does not read raw Vector logs, Grafana logs, Edge logs,
Docker logs, metrics payloads, traces, source files, operational CSV content, or
secrets.

Vector evidence is a status class, not an identity, trace, log line, or metric
payload. The web console remains localhost-only.
