# Independent Runtime Readiness Rerun

Date: 2026-06-09

Branch: `codex/independent-runtime-readiness-rerun`

Base commit: `12b1cfa031d30a463c814a9e094c692ef2ccd818`

Scope: report-only QA rerun for the independent `Extrusion_web_console` local Supabase runtime after the setup smoke report in `docs/54_independent_runtime_setup_smoke.md`.

This rerun did not modify feature code, launcher code, backend code, frontend code, packaging scripts, production deployment, GitHub Release, or GitHub tag. No `supabase start`, `supabase init`, `supabase db reset`, `supabase db push`, explicit migration command, DB delete/truncate/drop/cleanup/prune command, Docker delete command, Upload Preview, Start Upload, or authenticated Edge call was run.

## Summary

Readiness verdict: `blocked`.

The independent runtime was not still ready at rerun time because Docker Desktop's Linux engine was unavailable. Direct Docker inspection could not reach the daemon, `supabase status` exited non-zero, API/DB/Studio ports were unreachable, and the backend readiness endpoint reported `blocked` with reason code `docker_unavailable`.

The PR #67 backend Edge probe discrepancy could not be meaningfully re-evaluated while the runtime was down. Direct no-auth Edge route reachability was also unavailable, and backend Edge readiness reported timeout-class unreachable. Treat the prior discrepancy as unresolved, not fixed.

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
| Docker daemon | unavailable |
| Docker API error class | daemon endpoint missing/unreachable |
| Independent container count from direct Docker inspection | not verifiable |
| Legacy container family from direct Docker inspection | not verifiable |
| `supabase status` exit code | non-zero |
| `supabase status` raw output | suppressed |
| Credential-like markers in `supabase status` raw output | no |

No Docker repair, Docker start, Docker delete, Docker prune, Supabase start, Supabase reset, or migration command was run.

## Reachability Results

| Probe | Result |
| --- | --- |
| API TCP `55321` | unreachable |
| DB TCP `25433` | unreachable |
| Studio TCP `55323` | unreachable |
| API HTTP root | unreachable |
| Studio HTTP root | unreachable |
| Edge no-auth route | unreachable |

No authenticated Edge call was made.

## Backend Runtime Readiness

Read-only endpoint used: `GET /api/runtime/local-supabase`.

The unsupported alias `GET /api/runtime/status` was not used.

| Field | Result |
| --- | --- |
| `/api/health` | `ok` |
| `/api/config` | reachable |
| Runtime overall status | `blocked` |
| Runtime reason code | `docker_unavailable` |
| Project id | `Extrusion_web_console` |
| Docker status | `unhealthy` |
| Supabase CLI status | `ready` |
| API status | `unreachable` |
| DB status | `unreachable` |
| Studio status | `unreachable` |
| Backend Edge status | `unreachable` |
| Backend Edge detail class | timeout |
| Grafana status | `unreachable` |
| Runtime container rows | `12` expected rows |
| Runtime container exists count | `0` |
| Runtime container missing count | `12` |
| Legacy containers in runtime response | `0` |

Assessment: the app continues to target `Extrusion_web_console`, but the runtime cannot be considered ready while Docker is unavailable. The previous `required_container_missing` blocker is effectively reintroduced from the backend perspective because no expected containers can be confirmed through Docker.

## Edge Probe Discrepancy

| Check | Result |
| --- | --- |
| Direct no-auth Edge route | unreachable |
| Backend Edge probe | unreachable / timeout |
| Discrepancy resolved | no |
| Discrepancy reproduced | not meaningfully testable while Docker is unavailable |

PR #67 showed direct no-auth Edge route reachability with backend Edge probe timeout/503-class attention. This rerun cannot prove whether that discrepancy is fixed or still present because both direct and backend paths are blocked by runtime unavailability.

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
| Direct Docker legacy container inspection | not verifiable while Docker is unavailable |
| Legacy fallback selected | no evidence |

The backend response did not confuse the target project id with the legacy runtime. Direct host-level legacy container presence could not be verified because Docker was unavailable.

## Grafana And Vector Caveats

| Item | Result |
| --- | --- |
| Grafana | unreachable |
| Vector container | not verifiable while Docker is unavailable |
| Upload readiness impact | blocked by Docker/runtime unavailability before Grafana/vector can be evaluated |

Grafana and vector are not the primary blocker in this rerun. Docker unavailability blocks the runtime first.

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
| Docker/Supabase current-state smoke | blocked by Docker unavailable |
| API/DB/Studio direct reachability | unreachable |
| Edge no-auth direct reachability | unreachable |
| Backend runtime readiness | `blocked` |
| Settings redaction smoke | raw secret pattern absent |

Pre-PR hygiene checks still required after this report is staged:

- `git diff --check`;
- report marker scan;
- PR file-scope check;
- forbidden file staged check.

## Findings

### Blockers

1. `docker_unavailable`: Docker Desktop's Linux engine was not reachable, so independent runtime readiness is blocked.
2. `independent_runtime_unreachable`: API, DB, Studio, and Edge route reachability all failed because the runtime was unavailable.
3. `required_container_presence_unverified`: expected containers could not be confirmed by direct Docker inspection; backend readiness reported all expected container rows as missing.

### Caveats

1. `edge_probe_discrepancy_unresolved`: PR #67's direct-vs-backend Edge discrepancy could not be reassessed while the runtime was down.
2. `settings_ui_identity_visibility`: Settings DOM scan still did not show project id, Studio port, or password-type secret inputs.
3. `grafana_unreachable`: Grafana remains unreachable, but Docker/runtime unavailability is the primary blocker.
4. `vector_not_assessed`: vector state could not be checked while Docker was unavailable.

### Passed

1. `config_defaults_ready`: config API still reports project id `Extrusion_web_console` and ports `55321` / `25433` / `55323`.
2. `secret_redaction_ready`: config/app shell/Settings DOM scans did not expose raw secret-like patterns.
3. `legacy_not_selected`: backend runtime response targeted `Extrusion_web_console` and did not report legacy containers.
4. `dangerous_operations_avoided`: no prohibited Supabase, DB, Docker delete, Upload, Edge auth, release, tag, or deploy action was run.

## Merge Blocker Assessment

This QA report PR is documentation-only and has no feature-code merge blocker.

The runtime readiness result itself is blocked. Do not proceed to Preview smoke or Start Upload smoke until Docker is available, independent containers are confirmed, and backend runtime readiness is rerun. The Edge probe discrepancy from PR #67 remains unresolved and must be retested only after the runtime is reachable again.

## Next Step

Restore Docker Desktop availability outside the app, without Docker delete/prune or DB reset. Then rerun independent runtime readiness on a fresh QA branch before deciding whether an independent Preview smoke is allowed.
