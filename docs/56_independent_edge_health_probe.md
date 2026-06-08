# Independent Edge Runtime Health Probe

Date: 2026-06-09

Branch: `codex/independent-edge-health-probe`

Base commit: `98691feb5ee3691ca0474db323ea989c17c34358`

Scope: report-only QA for the independent `Extrusion_web_console` local Supabase Edge runtime.

This probe did not modify feature code, launcher code, backend code, frontend code, packaging scripts, production deployment, GitHub Release, or GitHub tag. No `supabase start`, `supabase init`, `supabase db reset`, `supabase db push`, explicit migration command, DB delete/truncate/drop/cleanup/prune command, Docker delete command, Upload Preview, Start Upload, or authenticated Edge call was run.

## Summary

Edge health verdict: `blocked`.

The independent Supabase core runtime is present and reachable: the expected `supabase_*_Extrusion_web_console` container family exists, the Edge runtime container is up, and API, DB, and Studio ports are reachable. The `upload-metrics` Edge Function asset exists in the repo-owned Supabase project and the Edge runtime container has a function-like mount destination.

The Edge route itself remains unhealthy. Direct no-auth `GET` and `POST` probes to `/functions/v1/upload-metrics` both returned `503` class responses. Sanitized Edge runtime logs include the function name and generic runtime error markers, with no sensitive markers detected in the inspected log tail.

The backend/direct discrepancy has a strong configuration explanation: with the current backend config source set, the backend derives its Edge probe URL from a hidden `supabaseUrl` env override instead of the independent default API port, and reports Edge as `unreachable`. When the Supabase URL override is explicitly cleared for a controlled read-only backend probe, the backend Edge probe changes to `unhealthy` with `503` class detail, matching the direct no-auth route failure shape.

## QA Environment

| Item | Result |
| --- | --- |
| QA mode | report-only |
| Runtime setup action | not run |
| Backend smoke | temporary loopback backend for read-only config/runtime probes |
| Upload Preview / Start Upload | not run |
| Edge authenticated call | not run |
| Authorization header or token | not used |
| Docker delete / DB reset / cleanup / prune | not run |
| Production deploy / Release / tag | not run |

## Asset And Config Checks

| Check | Result |
| --- | --- |
| `supabase/functions/upload-metrics/index.ts` | present |
| `project_id` | `Extrusion_web_console` |
| API port | `55321` |
| DB port | `25433` |
| Studio port | `55323` |
| Edge runtime config | enabled |
| Explicit `[functions.upload-metrics]` stanza | absent |
| Expected function path | conventional path present |

Assessment: there is no evidence that the repo asset is missing. The absent function stanza is not by itself a blocker because the conventional Supabase function path exists and the Edge route reaches the runtime.

## Docker And Supabase State

| Check | Result |
| --- | --- |
| Independent container count | `12` |
| Independent container family | `supabase_*_Extrusion_web_console` |
| Legacy container family present | yes |
| Edge runtime container | up |
| Vector container | restarting |
| `supabase status` exit code | `0` |
| `supabase status` raw output | suppressed |
| Credential-like markers in raw status output | present, therefore not recorded |

Observed independent container names were limited to the expected `supabase_*_Extrusion_web_console` family. Legacy containers were present on the host but were not used as independent readiness substitutes.

## Local Reachability

| Probe | Result |
| --- | --- |
| API TCP `55321` | reachable |
| DB TCP `25433` | reachable |
| Studio TCP `55323` | reachable |
| API HTTP root | not-found class response |
| Studio HTTP root | success class response |

Core API, DB, and Studio reachability passed. These checks do not prove Edge upload readiness.

## Direct No-Auth Edge Probe

Endpoint path: `/functions/v1/upload-metrics`.

| Method | Authorization header | Status class | Body class |
| --- | --- | --- | --- |
| `GET` | not used | `5xx` / `503` | `service_unavailable_503` |
| `POST {}` | not used | `5xx` / `503` | `service_unavailable_503` |

Expected healthy route evidence would be an auth-required or validation-class response. The observed `503` means the route reaches the Edge stack but is not healthy enough for Preview-to-Start-Upload progression.

## Backend Readiness Probe

Read-only endpoint: `GET /api/runtime/local-supabase`.

Current backend config source behavior:

| Field | Result |
| --- | --- |
| Backend `/api/health` | `ok` |
| Runtime overall status | `attention` |
| Runtime reason code | `non_core_runtime_attention` |
| Project id | `Extrusion_web_console` |
| Docker | `ready` |
| Supabase CLI | `ready` |
| API | `ready` |
| DB | `ready` |
| Studio | `ready` |
| Edge | `unreachable` |
| Edge detail class | `other_transport_error` |
| Grafana | `unreachable` |
| Container rows | `12` |
| Existing container rows | `12` |
| Legacy container rows in backend response | `0` |
| Raw secret-like pattern in backend responses | absent |

Config source check:

| Config item | Source class | Value handling |
| --- | --- | --- |
| `supabaseUrl` | env | value present, raw value suppressed |
| `supabaseEdgeUrl` | env | raw value suppressed |
| `localSupabaseApiPort` | env | `55321` |

Controlled comparison with Supabase URL overrides cleared:

| Field | Result |
| --- | --- |
| Edge URL source | independent default path class |
| Edge | `unhealthy` |
| Edge detail class | `503_class` |
| API / DB / Studio | `ready` / `ready` / `ready` |
| Overall status | `attention` |

Assessment: the direct-vs-backend failure-shape discrepancy is not caused by Python `httpx` itself. A direct no-auth `httpx` probe receives the same `503` as PowerShell when pointed at the independent API port. The discrepancy is best explained by a hidden `supabaseUrl` env override causing the backend to probe a non-default Edge URL class. Clearing that override makes backend Edge evidence match the direct `503` failure shape.

## Edge Runtime Logs

Sanitized log inspection:

| Check | Result |
| --- | --- |
| Container | `supabase_edge_runtime_Extrusion_web_console` |
| Raw logs | suppressed |
| Sensitive-like markers in inspected tail | absent |
| Sanitized error classes | `denoRuntime`, `functionName`, `genericError` |
| Approximate error marker count | `5` |
| Recent `upload-metrics` marker | present |

The logs support a runtime/worker-level failure hypothesis but were not quoted to avoid exposing generated values or local environment details.

## Path And Mount Checks

| Check | Result |
| --- | --- |
| Edge container inspect | available |
| Raw inspect output | suppressed |
| Mount count | `2` |
| Function-like mount destination | present |
| Known function destination class | present |

Assessment: function asset missing or gross function path mismatch is less likely than a runtime startup/worker error. It is still possible that the function runtime cannot load or execute the asset correctly.

## Root Cause Hypothesis

Most likely causes, ordered by evidence strength:

1. `current_backend_edge_url_override`: backend readiness is using a hidden `supabaseUrl` env override for Edge URL derivation, which explains why current backend readiness reports a different failure shape than the direct independent-port probe.
2. `edge_runtime_worker_error`: independent direct Edge route still returns `503` even when probed without auth by both PowerShell and Python `httpx`; sanitized logs show runtime error markers tied to the Edge runtime/function.
3. `function_boot_or_import_error`: the function asset exists and appears mounted, but the runtime may fail during boot/import/execution.
4. `backend_probe_timeout_too_short`: less likely as the primary cause after the controlled backend comparison produced a `503_class` result, but timeout behavior can still mask the underlying error when probing the override-derived URL.
5. `port_or_proxy_mismatch`: less likely for direct independent-port probes because API, DB, and Studio ports are reachable and Python `httpx` has no proxy-env presence in the probe environment.
6. `function_not_served`: less likely because `/functions/v1/upload-metrics` reaches a `503` response rather than a clean route-not-found class.

## Blockers And Caveats

### Blockers

1. `edge_unhealthy_503`: direct no-auth `GET` and `POST` probes return `503`.
2. `backend_edge_url_override_discrepancy`: current backend readiness uses a hidden override-derived Edge URL class and reports Edge as `unreachable`; it does not reflect the independent default Edge route unless the override is cleared.
3. `edge_runtime_error_markers`: sanitized Edge runtime logs contain generic runtime error markers.

### Caveats

1. `vector_container_restarting`: vector is still restarting. This is secondary to Edge upload readiness.
2. `grafana_unreachable`: Grafana remains unreachable through backend readiness. Grafana is link/status-only and is not the primary upload blocker.
3. `explicit_function_stanza_absent`: no explicit function stanza was found in `supabase/config.toml`; the conventional function asset path exists.

### Not Tested By Design

1. Upload Preview was not run.
2. Start Upload was not run.
3. Authenticated Edge calls were not run.
4. Authorization headers or tokens were not used.
5. DB migrations, reset, delete, cleanup, and prune were not run.
6. Docker container, volume, image, or network deletion was not run.
7. Settings UI/browser QA was not run in this probe.

## Redaction Result

| Check | Result |
| --- | --- |
| Raw DB URL in report | absent |
| Raw token/auth/JWT in report | absent |
| Raw Authorization header in report | absent |
| Generated Supabase credentials in report | absent |
| Raw Supabase status output | absent |
| Raw Edge logs | absent |
| Operational source path/content/filename in report | absent |
| Package output/zip/checksum committed | no |
| `.gstack` artifacts committed | no |
| `frontend/dist` committed | no |
| Operational source fixture committed | no |

## Validation

| Command/check | Result |
| --- | --- |
| Targeted backend runtime/config/local-token tests | `42 passed` |
| `npm run typecheck` | passed |
| `npm run build` | passed |
| `git diff --check` | passed |
| Report secret marker scan | clean |
| Report operational data marker scan | clean |
| Forbidden file-scope scan | clean |
| Untracked operational source fixture | present but not staged |
| `.gstack`, `frontend/dist`, package output/zip/checksum | not staged |

Validation caveat: targeted backend tests emitted existing pytest cache/deprecation warnings. No test failed.

## Next Required Action

Create a code/config investigation PR before Preview smoke.

Recommended order:

1. Confirm whether the hidden `supabaseUrl` env override is intentional for independent runtime readiness. If not, update docs/config guidance or backend readiness precedence so local runtime readiness uses the independent Edge URL unless `supabaseEdgeUrl` is explicitly set.
2. Investigate the Edge runtime `503` using sanitized logs and an Edge serve/deploy smoke approved for Edge-only diagnosis. Do not run Upload Preview, Start Upload, or authenticated Edge calls in that task unless separately approved.
3. After the backend Edge URL source and direct `503` are resolved, rerun independent runtime readiness.
4. Proceed to Preview smoke only after Edge returns an auth-required or validation-class no-auth response and backend readiness agrees.

## Merge Blocker Assessment

This PR is documentation-only and has no feature-code merge blocker.

The runtime is not ready for Preview or Start Upload. The next implementation work should address the hidden backend Edge URL source and the independent Edge runtime `503` before any upload-facing smoke.
