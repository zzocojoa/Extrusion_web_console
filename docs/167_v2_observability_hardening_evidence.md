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
- Dashboard runtime checks show a separate Vector row.
- `/api/dashboard` runtime checks include Vector as a separate observability row.
- Package manifest smoke guidance now includes read-only
  `/api/runtime/local-supabase` verification for sanitized Grafana and Vector
  status classes.
- The operator package runtime note records that Grafana and Vector evidence
  must remain sanitized and that Grafana iframe embedding remains excluded.

Not implemented by design:

- raw Grafana, Vector, Docker, Supabase, or Edge log export;
- raw metrics payload export;
- raw trace payload export;
- generated credential, DB URL, Authorization, JWT, raw source path, or raw CSV
  content capture;
- Grafana iframe embedding;
- LAN exposure or non-loopback bind changes.

## Alert And Runbook Classes

Operator-facing alert classes:

| Condition | Class | Operator action |
| --- | --- | --- |
| API, DB, Studio, or Edge is not reachable | `core_runtime_unreachable` | Stop upload mutation flow and inspect runtime readiness. |
| Grafana is unreachable while core runtime is ready | `non_core_runtime_attention` | Continue core upload review only if Grafana is not an acceptance gate; record caveat. |
| Vector is stopped, unhealthy, missing, or unknown while core runtime is ready | `non_core_runtime_attention` | Record observability caveat; do not run cleanup/reset/prune as a workaround. |
| Raw log, metric, trace, DB URL, token, JWT, source path, filename, or CSV content appears in evidence | `redaction_failure` | Stop and redact before sharing or merging evidence. |

Rollback and recovery:

- Do not delete operational DB rows.
- Do not delete local state DB evidence.
- Do not run Supabase reset/cleanup, Docker cleanup, prune, or broad container
  deletion.
- If the new Vector row is wrong, revert the code/docs commit or fix forward
  with sanitized status-class evidence.
- If runtime evidence has already been recorded, preserve it and add a corrected
  follow-up record instead of deleting the evidence.

## Validation

Targeted validation:

- `.\.venv\Scripts\python -m pytest tests\backend\test_runtime_control.py tests\backend\test_runtime_api.py tests\backend\test_dashboard.py tests\backend\test_operator_package_assembly.py`:
  `65 passed, 2 warnings`
- `cd frontend; npm run typecheck`: passed
- `git diff --check`: passed

Required before merge:

- full backend tests;
- frontend API-mode build;
- API-mode package assembly;
- API-mode zip package assembly;
- read-only package HTTP smoke including `/api/runtime/local-supabase`;
- `$review`.

## Security Notes

The implementation reads existing Docker container status summaries already used
by runtime readiness. It does not read raw Vector logs, Grafana logs, Edge logs,
Docker logs, metrics payloads, traces, source files, operational CSV content, or
secrets.

Vector evidence is a status class, not an identity, trace, log line, or metric
payload. The web console remains localhost-only.
