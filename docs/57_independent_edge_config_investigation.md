# Independent Edge Config Investigation

Date: 2026-06-09

Branch: `codex/independent-edge-config-investigation`

Base commit: `853367b06b7442858aa60e4d62b4f5bb0004cd22`

Scope: root-cause investigation for independent local Supabase Edge readiness and backend Edge URL precedence.

This investigation did not run Supabase init/bootstrap/start/reset, DB migrations, DB reset/delete/cleanup/prune, Docker container/volume/image/network deletion, Upload Preview, Start Upload, Edge authenticated calls, GitHub Release/tag operations, or production deploy.

## Summary

Investigation verdict: `partial_fix_applied_edge_still_blocked`.

Two issues were separated:

1. `runtime_edge_url_precedence_bug`: backend runtime readiness reused the upload Edge URL property. That property intentionally supports `supabaseUrl` fallback for Upload Job compatibility, but it lets a hidden `supabaseUrl` setting change the Local Supabase runtime Edge probe target when no explicit Edge URL is present. This conflicts with the independent runtime expectation that the local Edge route is derived from `localSupabaseApiPort` unless an explicit Edge URL is configured.
2. `edge_runtime_503`: independent direct no-auth `GET` and `POST` probes still return `503`. This is not fixed by the config precedence change. The Edge runtime container is up, the function asset exists, and the route reaches the Edge stack, but the function does not return the expected auth-required or validation-class response.

The code fix adds a separate runtime readiness URL path:

- Upload Job execution keeps `Settings.upload_edge_url`, preserving the existing `supabaseEdgeUrl` then `supabaseUrl` fallback behavior.
- Local Supabase runtime readiness now uses `Settings.local_runtime_edge_url`, which uses explicit `supabaseEdgeUrl` when configured and otherwise derives from `localSupabaseApiPort`.

## Confirmed Facts

### Config precedence

| Question | Finding |
| --- | --- |
| Does `upload_edge_url` follow `supabaseUrl` when no explicit Edge URL is set? | yes, before and after this PR, for Upload Job compatibility |
| Does runtime readiness need the same fallback? | no, independent Local Supabase readiness should use the local runtime port unless an explicit Edge URL is configured |
| Was this covered by existing tests? | partially; tests covered no-`supabaseUrl` default but not `supabaseUrl`-present runtime readiness |
| Does the current working config have hidden Supabase URL keys? | yes, presence-only check found Supabase URL keys in repo dotenv |
| Are raw values recorded here? | no |

Presence-only config source check:

| Key | Process env presence | Repo dotenv key presence |
| --- | --- | --- |
| `EWC_SUPABASE_URL` | absent | present |
| `EWC_SUPABASE_EDGE_URL` | absent | present |
| `EWC_LOCAL_SUPABASE_API_PORT` | absent | absent |
| `EWC_LOCAL_SUPABASE_PROJECT_ID` | absent | absent |

The Config API correctly reports secret fields without exposing raw secret values. The remaining operator risk is interpretability: a hidden env/dotenv override can affect readiness while the raw value is intentionally hidden. The runtime status and follow-up docs should keep showing source/override state without exposing raw values.

### Edge direct probe

Endpoint path: `/functions/v1/upload-metrics`.

| Method | Authorization header | Status class | Body class |
| --- | --- | --- | --- |
| `GET` | not used | `5xx` / `503` | unclassified/empty service-unavailable response |
| `POST {}` | not used | `5xx` / `503` | unclassified/empty service-unavailable response |

Expected healthy no-auth evidence:

- `GET` without `device_id` should reach function code and return a validation-class response.
- `POST {}` should reach function code and return a validation-class response.
- Auth-required responses are also acceptable readiness evidence for protected routes.

Observed `503` means the request reaches the Edge stack but the function is not serving normally.

### Edge runtime state

| Check | Result |
| --- | --- |
| Independent container count | `12` |
| Edge runtime container | up |
| Vector container | restarting |
| Function asset path | present |
| Conventional function path | present |
| Edge runtime config | enabled |
| Raw Edge logs | suppressed |
| Sanitized Edge log classes | `deno_runtime`, `generic_error` |
| Sensitive-like markers in inspected log tail | absent |

### Asset comparison

The current repo-owned `upload-metrics` function differs from the legacy reference function, but the differences found in inspection are not a sufficient explanation for route-level `503`. The current function has the independent default internal Kong host and returns canonical `accepted` counts. The observed `503` happens before the request reaches the expected handler-level validation paths.

## Disproven Or Weakened Hypotheses

| Hypothesis | Assessment |
| --- | --- |
| Python `httpx` alone causes the discrepancy | weakened; direct Python `httpx` to the independent local port also receives `503` |
| Function asset is missing | disproven; repo asset exists at the expected conventional path |
| Gross mount/path mismatch | weakened; Edge container has function-like mount destinations |
| Direct route not found | weakened; route returns `503`, not a clean not-found class |
| `supabaseUrl` fallback should be used for Local Supabase readiness | rejected; it is useful for Upload Job compatibility but wrong for independent local runtime readiness |

## Root-Cause Hypothesis

### A. Config/root-cause

Confirmed bug:

- Runtime readiness used `Settings.upload_edge_url`.
- `Settings.upload_edge_url` must support Upload Job fallback from `supabaseUrl`.
- That made readiness sensitive to a hidden `supabaseUrl` value when no explicit Edge URL was set.

Fix:

- Add `Settings.local_runtime_edge_url`.
- Use it in `RuntimeReadinessService` for Edge probing and runtime config display.
- Keep `Settings.upload_edge_url` unchanged for Upload Job execution.

Remaining caveat:

- Explicit `supabaseEdgeUrl` still intentionally overrides the local runtime-derived URL. If the operator environment has an unintended hidden Edge URL override, readiness can still target that explicit value. That is a setup/config hygiene issue, not the `supabaseUrl` fallback bug.

### B. Edge runtime `503`

Most likely remaining causes:

1. `edge_worker_boot_or_runtime_error`: direct no-auth requests return `503` before expected handler validation; sanitized logs contain Deno/runtime generic error markers.
2. `function_import_or_runtime_dependency_error`: current code imports Supabase JS from JSR. The legacy function used the same import style, so this is plausible but not proven.
3. `edge_runtime_state_issue`: Edge container is up, but the worker may not be loading the function correctly.

Less likely:

- missing function asset;
- gross function path mismatch;
- API/DB/Studio port outage;
- Python client transport issue.

## Fixes Applied

Files changed:

- `backend/app/core/settings.py`
  - added `local_runtime_edge_url`;
  - explicit `supabaseEdgeUrl` still wins;
  - otherwise derives `/functions/v1/upload-metrics` from `localSupabaseApiPort`.

- `backend/app/services/runtime_readiness.py`
  - Edge route readiness now probes `local_runtime_edge_url`;
  - runtime config item for Edge URL now uses the runtime-specific URL.

- `tests/backend/test_runtime_control.py`
  - added coverage that Upload Job URL fallback to `supabaseUrl` is preserved;
  - added coverage that runtime readiness ignores `supabaseUrl` when no explicit Edge URL is set;
  - added coverage that explicit `supabaseEdgeUrl` still overrides runtime URL.

## Remaining Blockers And Caveats

### Blockers

1. `edge_runtime_503`: direct no-auth Edge `GET` and `POST` still return `503`.
2. `edge_runtime_error_class`: sanitized Edge logs still show Deno/runtime generic error markers.

### Caveats

1. `explicit_edge_url_override`: explicit `supabaseEdgeUrl` remains authoritative. This is intentional, but hidden env/dotenv overrides must be reviewed before operator acceptance.
2. `vector_container_restarting`: vector remains a secondary caveat.
3. `grafana_unreachable`: Grafana remains link/status-only and is not the primary upload blocker.

### Not Tested By Design

1. Upload Preview was not run.
2. Start Upload was not run.
3. Authenticated Edge calls were not run.
4. Authorization headers or tokens were not used.
5. DB migration/reset/delete/cleanup/prune was not run.
6. Docker container/volume/image/network deletion was not run.

## Redaction Result

| Check | Result |
| --- | --- |
| Raw DB URL in report | absent |
| Raw token/auth/JWT in report | absent |
| Raw Authorization header in report | absent |
| Raw Supabase status output | absent |
| Raw Edge logs | absent |
| Raw env/dotenv values | absent |
| Operational source path/content/filename in report | absent |

## Validation

| Command/check | Result |
| --- | --- |
| Targeted backend runtime/config/local-token/command-policy tests | `68 passed` |
| Targeted upload job tests | `13 passed` |
| `npm run typecheck` | passed |
| `npm run build` | passed |
| `git diff --check` | passed |
| Secret marker scan on added lines | clean |
| Operational data marker scan on added lines | clean |
| Forbidden file-scope scan | clean |

Validation caveat: pytest emitted existing cache/deprecation warnings. No test failed.

## Next Step

After this PR is reviewed, run an Edge-only runtime investigation focused on worker boot/import failure. That task should inspect sanitized Edge runtime error classes and, if separately approved, run an Edge serve/deploy smoke without Upload Preview, Start Upload, or authenticated Edge calls.
