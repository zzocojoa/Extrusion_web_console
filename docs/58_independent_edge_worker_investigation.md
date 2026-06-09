# Independent Edge Worker Investigation

Date: 2026-06-09

Branch: `codex/independent-edge-worker-investigation`

Scope: root-cause investigation for independent local Supabase Edge worker `503` responses on `/functions/v1/upload-metrics`.

This investigation did not run Supabase init/bootstrap/start/reset, DB migrations, DB reset/delete/cleanup/prune, Docker container/volume/image/network deletion, Upload Preview, Start Upload, Edge authenticated calls, GitHub Release/tag operations, or production deploy.

## Summary

Investigation verdict: `root_cause_found_no_code_change`.

The current direct no-auth `503` is not explained by a missing `upload-metrics` function asset, a gross path mismatch, or a Deno import/type failure. The direct root cause is that the independent Edge runtime container is not running. Kong still accepts the `/functions/v1/upload-metrics` route on the independent API port, but the upstream Edge runtime process is stopped, so direct no-auth `GET` and `POST {}` probes return `503` instead of reaching handler-level auth or validation responses.

No function/config fix was applied in this PR because the confirmed failure is runtime state, not a repository asset defect. The next action should be a maintainer-approved Edge runtime recovery/rerun that starts or recreates the Edge runtime through the approved Supabase runtime procedure, then reruns no-auth probes and backend readiness.

## Confirmed Facts

| Check | Result |
| --- | --- |
| Supabase project id | `Extrusion_web_console` |
| API port | `55321` |
| DB port | `25433` |
| Studio port | `55323` |
| Edge runtime config | enabled |
| Explicit `[functions.upload-metrics]` stanza | absent |
| Function asset path | present |
| Function mount destination | present in Edge container inspect |
| Internal function config | `upload-metrics` is registered with JWT verification enabled |
| Deno type/import check | passed |
| Deno format check | failed on line-ending format only |
| Independent Edge runtime container | exited, exit code `255` |
| OOM kill flag | false |
| Direct no-auth `GET` | `503` class |
| Direct no-auth `POST {}` | `503` class |
| Backend readiness | `attention`, Edge `unreachable` with timeout-class detail |

The backend readiness timeout does not contradict the direct `503`. The backend probe timeout is shorter than the observed direct route wait, so it can classify the same stopped-upstream condition as timeout instead of HTTP `503`.

## Disproven Or Weakened Hypotheses

| Hypothesis | Assessment |
| --- | --- |
| Function asset is missing | disproven; the repo asset exists at the expected conventional path. |
| `supabase/config.toml` points to the wrong project id or core ports | disproven; project id and API/DB/Studio ports match the independent plan. |
| Edge runtime is disabled | disproven; `[edge_runtime]` is enabled. |
| Deno import/type failure prevents static loading | weakened; `deno check --no-lock` passes for the function file. |
| Gross function mount/path mismatch | weakened; Edge container inspect shows a function-like mount and registered `upload-metrics` function config. |
| Backend URL precedence is the current root cause | disproven for this branch; PR #70 separated runtime Edge URL selection, and the temporary backend probe used independent runtime defaults. |
| Upload Preview or Start Upload is needed to reproduce | disproven; no-auth route probes reproduce the blocked Edge state without upload execution. |

## Root Cause

The current `503` is caused by a stopped independent Edge runtime upstream:

1. `supabase_kong_Extrusion_web_console` and core services are reachable.
2. `supabase_edge_runtime_Extrusion_web_console` exists but is not running.
3. The route `/functions/v1/upload-metrics` reaches the local Supabase gateway.
4. The gateway cannot hand the request to a healthy Edge runtime worker.
5. The no-auth route therefore returns `503` before the `upload-metrics` handler can return auth-required or payload-validation responses.

Sanitized Edge logs did not show an `upload-metrics` handler startup stack trace. They did show prior no-auth JWT-gate errors, which is consistent with Supabase's default behavior that Edge Functions require a valid JWT unless `functions.<name>.verify_jwt` is changed. That default is documented by Supabase and should not be disabled as a shortcut because this function writes to `public.all_metrics`.

## No-Code-Change Rationale

No code/config change was made because:

- the function asset exists and passes `deno check`;
- the `onConflict: "timestamp,device_id"` upload safety remains present;
- disabling JWT verification would make the route easier to probe but would weaken the upload boundary unless a separate handler-level auth design is implemented and tested;
- the active failure is a stopped Edge runtime container, which requires a maintainer-approved runtime recovery/rerun rather than a source edit;
- applying a source change without being able to restart/rerun the Edge runtime would not prove the 503 is fixed.

The only static issue found is line-ending format drift in `supabase/functions/upload-metrics/index.ts`. That is not a credible cause of the runtime `503`. It should be normalized in a separate small hygiene PR or alongside the next approved Edge runtime recovery task if the team wants `deno fmt --check` to be a hard gate.

## Before And After Status

| Probe | Before | After |
| --- | --- | --- |
| Direct no-auth `GET /functions/v1/upload-metrics` | `503` class | unchanged, no runtime recovery was run |
| Direct no-auth `POST /functions/v1/upload-metrics` with `{}` | `503` class | unchanged, no runtime recovery was run |
| Backend `/api/runtime/local-supabase` Edge result | timeout-class `unreachable` | unchanged, no runtime recovery was run |

Expected healthy evidence after runtime recovery:

- no-auth `GET` returns auth-required or validation-class response;
- no-auth `POST {}` returns auth-required or validation-class response;
- backend readiness reports Edge `ready`, or at minimum classifies a handler-level auth/validation response as reachable.

## Backend Readiness Result

A temporary read-only backend probe was run with independent runtime defaults and no Upload/Edge auth calls.

| Field | Result |
| --- | --- |
| `/api/health` | ok |
| `/api/runtime/local-supabase` | reachable |
| Overall status | `attention` |
| Reason code | `non_core_runtime_attention` |
| Docker | `ready` |
| API | `ready` |
| DB | `ready` |
| Studio | `ready` |
| Edge | `unreachable` |
| Edge detail class | timeout |
| Missing required containers | `0` |

Readiness currently treats the stopped Edge container as non-core attention because required-container presence is checked separately from route health. That is acceptable as a report for this investigation, but future runtime UX could be improved by surfacing stopped required containers more directly.

## Remaining Blockers And Caveats

### Blockers

1. `edge_runtime_container_exited`: the independent Edge runtime container exists but is not running.
2. `edge_route_503`: direct no-auth `GET` and `POST {}` return `503`.
3. `handler_not_reached`: probes do not reach function-level auth or validation responses.

### Caveats

1. `jwt_gate_default`: the function is registered with JWT verification enabled. This is the secure default and should not be disabled without a handler-level auth design.
2. `backend_probe_timeout_shape`: backend readiness may report timeout instead of HTTP `503` while the route waits longer than the probe timeout.
3. `deno_fmt_line_endings`: `deno fmt --check` fails on line endings, not type/import validity.
4. `vector_container_restarting`: vector remains a secondary runtime caveat outside the Edge upload blocker.
5. `grafana_unreachable`: Grafana remains link/status-only and is not the primary upload blocker.

### Not Tested By Design

1. Upload Preview was not run.
2. Start Upload was not run.
3. Authenticated Edge calls were not run.
4. Authorization headers or tokens were not used.
5. DB migrations, reset, delete, cleanup, and prune were not run.
6. Docker container, volume, image, or network deletion was not run.
7. Supabase init/bootstrap/start/reset was not run.

## Security And Redaction Result

| Check | Result |
| --- | --- |
| Raw DB URL in report | absent |
| Raw token/auth/JWT in report | absent |
| Raw Authorization header in report | absent |
| Generated Supabase credentials in report | absent |
| Raw Supabase status output | absent |
| Raw Edge logs | absent |
| Raw env/dotenv values | absent |
| Operational source path/content/filename in report | absent |

## Validation

| Command/check | Result |
| --- | --- |
| `deno fmt --check supabase/functions/upload-metrics/index.ts` | failed, line-ending format drift |
| `deno check --no-lock supabase/functions/upload-metrics/index.ts` | passed |
| Supabase config static inspection | passed |
| Docker Edge container state inspection | Edge container exited |
| Sanitized Edge log class inspection | JWT-gate error class found, raw logs suppressed |
| Direct no-auth `GET` | `503` class |
| Direct no-auth `POST {}` | `503` class |
| Backend runtime readiness probe | `attention`, Edge timeout-class `unreachable` |

Pre-PR checks still required after this document is staged:

- targeted backend runtime/config tests;
- targeted upload job tests if upload code is touched;
- `npm run typecheck`;
- `npm run build`;
- `git diff --check`;
- secret and operational marker scans;
- forbidden file-scope scan.

## Next Step

Run a maintainer-approved Edge runtime recovery/rerun task:

1. Keep Upload Preview, Start Upload, authenticated Edge calls, DB migrations, reset/delete/cleanup/prune, Docker delete, release/tag, and production deploy forbidden.
2. Use the approved independent runtime setup procedure to bring `supabase_edge_runtime_Extrusion_web_console` back to running state.
3. Rerun direct no-auth `GET` and `POST {}` route probes.
4. Rerun backend `/api/runtime/local-supabase`.
5. If no-auth still returns `503` while the Edge runtime is running, investigate worker boot/import failure next.
6. If no-auth returns auth-required or validation-class responses, proceed to an independent readiness rerun before any Preview smoke.

References:

- [Supabase Function Configuration](https://supabase.com/docs/guides/functions/function-configuration): `functions.<function_name>.verify_jwt` defaults to requiring JWT validation unless explicitly disabled.
- [Supabase CLI Config Reference](https://supabase.com/docs/guides/local-development/cli/config): per-function JWT verification is configured in `supabase/config.toml`.
