# API-Mode Start Upload Readiness Plan

Status: planned readiness checklist

Date: 2026-06-08

Branch: `codex/operator-api-mode-start-upload-readiness`

Scope: presence-only readiness procedure before rerunning API-mode operator package Start Upload smoke.

This document does not change feature code, launcher code, backend code, frontend code, packaging scripts, GitHub Release assets, tags, production deployment, local Supabase data, Docker data, database data, or operational CSV data.

Upload Start is out of scope for this readiness step. Do not click Start Upload while following this document.

## Goal

Lock the readiness gates that must pass before a future Start Upload smoke can run safely.

PR #59 correctly blocked Start Upload because DB/Edge/auth readiness was incomplete. The next step is not another Start Upload attempt. The next step is to prepare and verify DB, Edge, auth, source, Preview, and minimal duplicate-safe sample readiness using presence-only evidence.

## Non-Negotiable Safety Rules

| Rule | Requirement |
| --- | --- |
| Secret handling | Record only `configured`, `missing`, `hidden`, `reachable`, or `unreachable` style status. |
| Secret values | Do not print, paste, log, screenshot, commit, or document raw secret values. |
| DB values | Do not print, paste, log, screenshot, commit, or document raw DB connection values. |
| Auth values | Do not print, paste, log, screenshot, commit, or document raw auth key, auth header, bearer value, JWT, service role, or token values. |
| Source data | Do not print, paste, log, screenshot, commit, or document operational CSV path, filename, content, row content, or full local path. |
| Database safety | Do not run DB reset, delete, cleanup, prune, migration repair, or destructive SQL. |
| Docker safety | Do not delete containers, delete volumes, run prune, recreate stacks, or run destructive Docker commands. |
| Upload safety | Do not click Start Upload during readiness preparation. |
| Release safety | Do not create or modify GitHub Release assets or tags. |

## Required Readiness Matrix

All required rows must pass before Start Upload can be approved in a later QA task.

| Gate | Required evidence | Pass condition | Stop condition |
| --- | --- | --- | --- |
| `supabaseDbUrl` | Config API or Settings UI presence-only check | `configured` and secret display `hidden` | `missing`, raw value visible, or unclear source |
| `supabaseUrl` | Config API or Settings UI presence-only check | `configured` and value not copied into report | `missing` or raw value copied |
| `supabaseAnonKey` | Config API or Settings UI presence-only check | `configured` and secret display `hidden` | `missing`, raw value visible, or auth source unclear |
| `supabaseEdgeUrl` | Config API or Settings UI presence-only check | `configured` and secret display `hidden` | `missing` or raw value visible |
| Source config | Config API or Settings UI presence-only check | PLC source `configured` and source folder exists | `missing`, unsafe sample source, or raw path copied |
| Local Supabase API | Runtime status check | `reachable` or `ready` | `unreachable` |
| Local Supabase DB TCP | Runtime status check | `reachable` or `ready` | `unreachable` |
| Local Supabase Studio | Runtime status check | `reachable` or `ready` | `unreachable` for operator readiness |
| Edge runtime | Runtime status or Edge route smoke | `reachable` or no-auth route returns expected auth/validation response | `unreachable` or timeout |
| Operator token guard | HTTP smoke | mutating API without valid local token returns `403` | missing guard, raw token exposure, or token in URL |

## Edge/Auth Readiness

Edge/auth readiness must prove route reachability and auth behavior without exposing auth material.

Acceptable checks:

1. No-auth Edge route smoke returns expected `401` or an equivalent validation/auth-required response.
2. Authenticated Edge smoke can prove route acceptance only when the auth value is already preconfigured and never printed.
3. API-mode package runtime can read configured Edge/auth presence while hiding secret values.

Do not record raw request headers, raw response bodies that contain secret-like material, or full URLs. If a tool prints such data, redact before writing any report.

## Preview Precondition

Before Start Upload can be considered in a later QA task:

| Preview requirement | Expected result |
| --- | --- |
| Upload Preview request | Accepted |
| Terminal status | `succeeded` |
| DB status | `reachable` |
| Source | PLC-only unless a later task explicitly expands scope |
| Candidate scope | Narrow and operator-approved |
| Target interpretation | Must be either no-new-row safe or controlled minimal duplicate-safe |
| Audit | `upload.preview` success row found |

If Preview reports `partial_failed`, `risky`, `db_unreachable`, missing source, active preview conflict, or target volume that cannot be bounded, stop. Do not click Start Upload.

## Minimal Duplicate-Safe Sample Condition

Start Upload can be approved only if the sample is deliberately small and duplicate-safe.

Required properties:

| Sample requirement | Pass condition |
| --- | --- |
| Source | Sanitized temp sample label only |
| Size | Minimal row count agreed for smoke |
| Original data | Read-only; not modified |
| Full operational upload | Not performed |
| Exact-key safety | Existing DB keys or no-new-row condition proven before Start |
| Report language | Sanitized labels only; no raw path, filename, content, or row content |
| Cleanup | Temp sample may be removed only if it was created by the smoke and is outside operational data |

If the only available candidate is the full operational source, stop. If exact-key safety cannot be proven without exposing data, stop.

## Upload Start Approval Gate

A future Start Upload smoke may click Start Upload exactly once only when all of these are true:

1. DB/Edge/auth config readiness is `configured` and secret values are hidden.
2. Edge runtime is reachable or no-auth route proves auth-required reachability.
3. API-mode package launcher has passed.
4. Upload Preview has rerun and finished `succeeded`.
5. Preview DB status is `reachable`.
6. The sample is minimal.
7. The sample is duplicate-safe or no-new-row safe.
8. Large operational source upload is not in scope.
9. The operator/local token is present only in memory and not in the URL or storage.
10. A separate task explicitly approves the one Start Upload action.

## Upload Start Stop Conditions

Do not click Start Upload if any of these occur:

| Stop condition | Reason |
| --- | --- |
| `preconfigured_env_missing` | Required config presence is incomplete |
| `runtime_unavailable` | Docker/local Supabase core runtime is unavailable |
| `edge_runtime_unreachable` | Edge route cannot be reached |
| `edge_auth_unavailable` | Auth readiness cannot be proven without exposing values |
| `preview_not_run` | Fresh Preview evidence is missing |
| `preview_not_uploadable` | Preview did not finish as `succeeded` with reachable DB |
| `no_upload_targets` without explicit no-op scope | Start would not exercise upload behavior |
| `sample_unsafe` | Minimal duplicate-safe condition is not proven |
| `large_source_risk` | Candidate could upload too much operational data |
| `redaction_failure` | Raw secret/path/source marker appears in output |
| `active_upload_job` | Another upload job is active |

## Audit Verification

For readiness only:

- Check existing audit access with read-only `/api/audit` smoke.
- Do not require `upload.start` before Start Upload is actually clicked.

For a later approved Start Upload smoke:

| Audit check | Expected result |
| --- | --- |
| `/api/audit?action=upload.start` | Recent row exists after Start Upload |
| Result | `success`, `failure`, or `blocked` must match observed job outcome |
| Params | Safe metadata only |
| Redaction | No raw DB value, auth value, local path, source filename, CSV content, or row content |

## Rollback And Stop Procedure

Readiness preparation should be reversible without destructive cleanup.

| Situation | Action |
| --- | --- |
| Config value missing | Stop and ask the maintainer/operator to set it locally without sharing values |
| Wrong local config selected | Restore only the intended local app config value if it was changed during the readiness step |
| Edge remains unreachable | Stop; record `edge_runtime_unreachable` |
| Secret/path marker appears | Stop; redact report output and do not proceed |
| Package runtime started for smoke | Stop only the package runtime process that the smoke started |
| Temp sample created by smoke | Remove only that temp sample after confirming it is outside operational data |

Do not delete AppData config/state/logs, Docker data, database data, operational data, package release outputs, or source repository files as rollback.

## Validation For Readiness PR

Because this is a document-only plan, validation is limited to:

1. `git diff --check`
2. Marker scan for raw secret, DB value, auth value, local path, and operational source identifiers
3. PR file scope check: `docs/49_operator_api_mode_start_upload_readiness.md` only
4. Confirm `.gstack`, `frontend/dist`, package output, zip/checksum, and operational CSV fixture are not committed

## Implementation Order For Next QA

1. Launch API-mode operator package.
2. Confirm local token bootstrap and docs hardening.
3. Confirm config presence with hidden secret display.
4. Confirm Docker/local Supabase API, DB TCP, Studio, and Edge readiness.
5. Run no-auth Edge route smoke and record only status class.
6. Run fresh Upload Preview.
7. Confirm Preview succeeded with reachable DB.
8. Prepare or select a minimal duplicate-safe sample using sanitized labels only.
9. Confirm sample safety and expected row-count behavior.
10. Click Start Upload once only if every gate passed.
11. Poll Upload Job status and events.
12. Check `acceptedRows` and compatibility `insertedRows` semantics.
13. Check `/api/audit?action=upload.start`.
14. Scan reportable evidence for redaction markers.

## Out Of Scope

- Running Upload Start in this readiness step
- Running duplicate rerun
- Uploading full operational sources
- Changing backend, frontend, launcher, or packaging code
- Changing local Supabase schema or data
- Creating or modifying GitHub Release assets or tags
- Production deployment

## Next Step

After this checklist is merged, prepare operator config and Edge/auth readiness using presence-only evidence. Then create a separate QA-only branch for one approved Start Upload smoke.
