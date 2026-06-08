# Independent Runtime Readiness Rerun

Date: 2026-06-09

Branch: `codex/independent-runtime-readiness-rerun`

Base commit: `12b1cfa031d30a463c814a9e094c692ef2ccd818`

Scope: report-only QA rerun for the independent `Extrusion_web_console` local Supabase runtime after the setup smoke report in `docs/54_independent_runtime_setup_smoke.md`.

This rerun did not modify feature code, launcher code, backend code, frontend code, packaging scripts, production deployment, GitHub Release, or GitHub tag. No `supabase start`, `supabase init`, `supabase db reset`, `supabase db push`, explicit migration command, DB delete/truncate/drop/cleanup/prune command, Docker delete command, Upload Preview, Start Upload, or authenticated Edge call was run.

## Summary

Readiness verdict: `ready_with_caveats`.

Docker Desktop was available for this rerun. The independent `supabase_*_Extrusion_web_console` container family was present, and API, DB, and Studio reachability passed on the configured independent ports. The previous Docker-unavailable blocker from the earlier same-branch attempt is resolved.

The runtime is not fully ready for Preview or Start Upload because the Edge path remains unhealthy. A direct no-auth Edge route request returned a `503` class response, while backend readiness repeatedly reported Edge as `unreachable` with a timeout-class detail. This means the PR #67 backend Edge probe discrepancy is still unresolved: direct and backend probes disagree on the failure shape, but both indicate Edge is not healthy enough for upload work.

## QA Environment

| Item | Result |
| --- | --- |
| QA mode | report-only |
| Runtime setup action | not run |
| Supabase status | run with raw output suppressed |
| Backend smoke | loopback API-mode app started with temporary config/state |
| Frontend smoke | API-mode build served by backend |
| Upload Preview / Start Upload | not run |
| Edge authenticated call | not run |
| Docker delete / DB reset / cleanup / prune | not run |
| Production deploy / Release / tag | not run |

## Pre-Run Checks

| Check | Result |
| --- | --- |
| Base branch/head | `main` at `12b1cfa031d30a463c814a9e094c692ef2ccd818` |
| `supabase/config.toml` project id | `Extrusion_web_console` |
| API port in config | `55321` |
| DB port in config | `25433` |
| Studio port in config | `55323` |
| Untracked operational fixture | present but not staged |

## Docker And Supabase Current State

| Check | Result |
| --- | --- |
| Docker daemon | available |
| Supabase CLI | available |
| Independent container count | `12` |
| Independent container family | `supabase_*_Extrusion_web_console` |
| Legacy container family present | yes |
| `supabase status` exit code | `0` |
| `supabase status` raw output | suppressed |
| Credential-like markers in `supabase status` raw output | yes |

Observed independent containers:

- `supabase_analytics_Extrusion_web_console`
- `supabase_auth_Extrusion_web_console`
- `supabase_db_Extrusion_web_console`
- `supabase_edge_runtime_Extrusion_web_console`
- `supabase_inbucket_Extrusion_web_console`
- `supabase_kong_Extrusion_web_console`
- `supabase_pg_meta_Extrusion_web_console`
- `supabase_realtime_Extrusion_web_console`
- `supabase_rest_Extrusion_web_console`
- `supabase_storage_Extrusion_web_console`
- `supabase_studio_Extrusion_web_console`
- `supabase_vector_Extrusion_web_console`

Container caveat: `supabase_vector_Extrusion_web_console` was still restarting during the rerun. Core API/DB/Studio services remained reachable.

## Reachability Results

| Probe | Result |
| --- | --- |
| API TCP `55321` | reachable |
| DB TCP `25433` | reachable |
| Studio TCP `55323` | reachable |
| API HTTP root | reachable with not-found class response |
| Studio HTTP root | reachable with success class response |
| Edge no-auth route | reachable with `503` class response |

No authenticated Edge call was made.

## Backend Runtime Readiness

Read-only endpoint used: `GET /api/runtime/local-supabase`.

The unsupported alias `GET /api/runtime/status` was not used.

| Field | Result |
| --- | --- |
| `/api/health` | `ok` |
| `/api/config` | reachable |
| Runtime overall status | `attention` |
| Runtime reason code | `non_core_runtime_attention` |
| Project id | `Extrusion_web_console` |
| Docker status | `ready` |
| Supabase CLI status | `ready` |
| API status | `ready` |
| DB status | `ready` |
| Studio status | `ready` |
| Backend Edge status | `unreachable` |
| Backend Edge detail class | timeout |
| Grafana status | `unreachable` |
| Runtime container rows | `12` |
| Runtime container exists count | `12` |
| Runtime container missing count | `0` |
| Legacy containers in runtime response | `0` |

Assessment: the independent stack is present and core runtime readiness is no longer blocked by Docker or missing containers. Full readiness remains `attention` because Edge and Grafana are not ready.

## Edge Probe Discrepancy

| Check | Result |
| --- | --- |
| Direct no-auth Edge route | reachable with `503` class response |
| Backend Edge probe | unreachable / timeout |
| Discrepancy resolved | no |
| Edge upload readiness | not ready |

PR #67 showed a direct-vs-backend Edge probe discrepancy. This rerun still shows a discrepancy, but the direct path now returns `503` rather than an auth-required class response. The actionable interpretation is unchanged: Edge is not healthy enough for Preview-to-Start-Upload progression, and the backend probe behavior should be investigated without running authenticated Edge calls.

## Settings And Redaction

`GET /api/config` returned independent defaults without exposing raw secret values.

| Check | Result |
| --- | --- |
| Config project id | `Extrusion_web_console` |
| Config API/DB/Studio ports | `55321` / `25433` / `55323` |
| Secret-bearing config items present | yes |
| Raw secret pattern visible in config response | no |
| App shell reachable | yes |
| Raw secret pattern visible in app shell | no |
| Settings page loaded in API mode | yes |
| Settings page console errors | `0` |
| Raw secret pattern visible in Settings DOM/input scan | no |
| Project id visible in Settings DOM scan | no |
| Studio port visible in Settings DOM scan | no |
| Password-type inputs found in Settings DOM scan | `0` |

Settings UI caveat from PR #67 reproduced. API-level redaction passed, but the headless Settings DOM scan still did not confirm project id visibility, Studio port visibility, or password-type secret inputs.

## Legacy Runtime Confusion Check

| Check | Result |
| --- | --- |
| Runtime project id | `Extrusion_web_console` |
| Backend runtime response includes legacy containers | no |
| Direct Docker legacy container family present | yes |
| Legacy fallback selected | no evidence |

The host still has legacy container family presence, but backend runtime readiness remains scoped to the independent project id and did not use legacy containers as substitutes.

## Grafana And Vector Caveats

| Item | Result |
| --- | --- |
| Grafana | unreachable |
| Vector container | restarting |
| Upload readiness impact | secondary caveat; Edge remains the primary upload-readiness blocker |

Grafana remains link/status-only for the web console. Vector is a non-core runtime caveat in this smoke. Neither should be treated as resolved.

## Redaction Result

| Check | Result |
| --- | --- |
| Raw DB URL in report | absent |
| Raw token/auth/JWT in report | absent |
| Raw Authorization header in report | absent |
| Generated Supabase credentials in report | absent |
| Operational source path/content/filename in report | absent |
| Package output/zip/checksum committed | no |
| `.gstack` artifacts committed | no |
| `frontend/dist` committed | no |
| Operational source fixture committed | no |

## Validation

| Command/check | Result |
| --- | --- |
| Targeted backend runtime/config/local-token tests | `64 passed` |
| `npm run typecheck` | passed |
| `npm run build` | passed |
| `npm run build:api` | passed |
| Docker/Supabase current-state smoke | independent containers present |
| API/DB/Studio direct reachability | passed |
| Edge no-auth direct reachability | `503` class response |
| Backend runtime readiness | `attention` |
| Settings redaction smoke | raw secret pattern absent |

Pre-PR hygiene checks still required after this report is staged:

- `git diff --check`;
- report marker scan;
- PR file-scope check;
- forbidden file staged check.

## Findings

### Blockers

1. `edge_unhealthy`: direct no-auth Edge route returns `503` class response and backend Edge probe times out.
2. `edge_probe_discrepancy_unresolved`: direct and backend Edge probes disagree on failure shape, so the PR #67 discrepancy is not resolved.

### Caveats

1. `grafana_unreachable`: Grafana remains unreachable. It is not the primary independent Supabase upload blocker.
2. `vector_container_restarting`: the vector container is still restarting while core services are reachable.
3. `settings_ui_identity_visibility`: Settings DOM scan still did not show project id, Studio port, or password-type secret inputs.

### Passed

1. `docker_available`: Docker daemon is reachable again.
2. `independent_containers_present`: all 12 expected independent container rows exist.
3. `core_runtime_ready`: API, DB, and Studio are reachable and backend readiness reports them as `ready`.
4. `config_defaults_ready`: config API reports project id `Extrusion_web_console` and ports `55321` / `25433` / `55323`.
5. `secret_redaction_ready`: config/app shell/Settings DOM scans did not expose raw secret-like patterns.
6. `legacy_not_selected`: backend runtime response targeted `Extrusion_web_console` and did not report legacy containers.
7. `dangerous_operations_avoided`: no prohibited Supabase, DB, Docker delete, Upload, Edge auth, release, tag, or deploy action was run.

## Merge Blocker Assessment

This QA report PR is documentation-only and has no feature-code merge blocker.

The runtime itself is `ready_with_caveats`, not ready for Preview smoke. Do not proceed to Preview or Start Upload until the Edge unhealthy state and direct-vs-backend Edge probe discrepancy are investigated and a subsequent readiness rerun shows an acceptable Edge result.

## Next Step

Investigate the Edge runtime health and backend Edge probe discrepancy without authenticated Edge calls or upload execution. After Edge readiness is fixed or explained, rerun independent runtime readiness again before approving any independent Preview smoke.
