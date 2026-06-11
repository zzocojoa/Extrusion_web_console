# Operator Package Edge Runtime Recovery QA

## Summary

- Date: 2026-06-11
- Branch: `codex/operator-edge-runtime-recovery`
- Base commit: `23928717bfe1d79d019ec66428878540e11ca488`
- QA mode: report-only
- Package path class: assembled operator package, not repo dev backend
- Recovery verdict: `recovered_with_caveats`
- Duplicate-safe rerun allowed next step: `yes_with_caveats`

This QA investigated and recovered the operator package blocker from PR #82: independent Edge runtime stopped and direct no-auth Edge route returning `503`.

Recovery succeeded for the required Edge gate:

- Before recovery, direct no-auth Edge `GET` and `POST {}` returned `503`.
- Before recovery, `supabase_edge_runtime_Extrusion_web_console` was stopped with an exited state.
- After recovery, direct no-auth Edge `GET` and `POST {}` returned auth-class `401`.
- After recovery, `supabase_edge_runtime_Extrusion_web_console` was running.
- Package-local `/api/runtime/local-supabase` reported Edge `ready`.

The remaining caveats are non-core runtime stability signals: Grafana unreachable, vector restarting, and `supabase start` instability during recovery.

## Scope And Guardrails

This QA did not modify feature code, launcher code, backend code, frontend code, packaging scripts, production deploys, GitHub Releases, or GitHub tags.

This QA did not run:

- Supabase init/bootstrap/reset
- DB migration/reset/delete/cleanup/prune/drop/truncate
- Docker volume/container/image/network deletion
- Upload Preview
- Upload Start
- duplicate rerun
- Edge authenticated upload call
- Authorization header or token usage
- operational CSV upload or source mutation

Allowed recovery actions used:

- Package assembly smoke into a repo-external output location
- Package launcher `-CheckOnly`
- Package-local backend/API read-only smoke
- Direct no-auth Edge GET/POST `{}` probes
- Package-local `supabase stop`
- Package-local `supabase start`
- Docker/Supabase status inspection with raw credential-bearing output suppressed

## QA Environment

| Item | Result |
| --- | --- |
| Branch | `codex/operator-edge-runtime-recovery` |
| Base commit | `23928717bfe1d79d019ec66428878540e11ca488` |
| Operator package frontend mode | api |
| Package required paths | present |
| Package Supabase assets | present |
| Package denylist matches | 0 |
| Package redaction matches | 0 |
| Legacy stack premise | observed legacy container state was stopped |
| Independent stack | `Extrusion_web_console` only |

The assembled package included repository-owned `supabase/config.toml`, Edge Function source, and migration source assets. Package output path is not recorded in this report.

## Before Recovery

| Check | Before result |
| --- | --- |
| Legacy `Extrusion_data` stack | observed stopped |
| Independent API port `55321` | reachable |
| Independent DB port `25433` | reachable |
| Independent Studio port `55323` | reachable |
| Edge runtime container | stopped, exited |
| Direct no-auth Edge `GET` | `503` service-unavailable |
| Direct no-auth Edge `POST {}` | `503` service-unavailable |
| Package-local `/api/health` | ok |
| Package-local `/api/runtime/local-supabase` | reachable |
| Package-local runtime overall | `attention` |
| Package-local runtime reason | `non_core_runtime_attention` |
| Package-local Edge status | unreachable |
| Package-local target class | DB independent, Edge independent |

Sanitized pre-recovery Edge log class:

| Log class | Result |
| --- | --- |
| Error marker | present |
| Raw log output | not recorded |

## Recovery Actions

Recovery was run from the assembled operator package project context.

| Step | Result |
| --- | --- |
| `supabase stop` | exit code `0` |
| First `supabase start` attempt | exit code `1` |
| Second `supabase start` attempt | exit code `1` |
| Sanitized follow-up `supabase start` inspection | exit code `1`, container-name conflict class |
| Exact container/port lookup after failed starts | independent stack containers absent; core ports closed |
| Final `supabase start` attempt | exit code `0` |
| Docker delete / volume delete / prune | not run |
| DB migration/reset/delete/cleanup/prune | not run |
| Raw generated credentials / connection strings | not recorded |

The failed start attempts reported a Docker container-name conflict class for the vector service. Docker delete was explicitly forbidden, so no delete or prune command was run. A later `supabase start` succeeded without deletion after the conflicting state no longer appeared in exact container lookup.

Successful `supabase start` and `supabase status` output contained credential-like markers, so raw output remains suppressed. The report records only exit codes, status classes, and availability markers.

## After Recovery

| Check | After result |
| --- | --- |
| Independent Edge runtime container | running |
| Independent API port `55321` | reachable |
| Independent DB port `25433` | reachable |
| Independent Studio port `55323` | reachable |
| Direct no-auth Edge `GET` | `401` auth-class |
| Direct no-auth Edge `POST {}` | `401` auth-class |
| Package-local `/api/health` | ok |
| Package-local `/api/config` | reachable |
| Package-local `/api/runtime/local-supabase` | reachable |
| Package-local `/api/audit?limit=5` | reachable |
| Package-local runtime overall | `attention` |
| Package-local runtime reason | `non_core_runtime_attention` |
| Package-local Edge status | ready |
| Package-local Edge detail class | reachable |
| Grafana | unreachable |
| Vector service | restarting |

Sanitized post-recovery Edge log class:

| Log class | Result |
| --- | --- |
| Deno marker | present |
| Error marker | present |
| Raw log output | not recorded |

The Edge readiness blocker is resolved for the operator package path. The remaining `attention` status is not caused by Edge; package-local readiness reports Edge `ready`.

## Target Alignment Confirmation

Package-local `/api/config` remained aligned after recovery:

| Setting | Result |
| --- | --- |
| `localSupabaseApiPort` | independent |
| `localSupabaseDbPort` | independent |
| `localSupabaseStudioPort` | independent |
| `supabaseDbUrl` | hidden |
| `supabaseEdgeUrl` | hidden |
| `supabaseUrl` | process/package target class |
| DB target class | independent |
| Edge target class | independent |
| DB/Edge alignment | aligned |

No raw DB URL, raw Edge URL, token, Authorization header, JWT, or secret value is recorded.

## Redaction Result

| Check | Result |
| --- | --- |
| Raw DB URL in report | absent |
| Raw token/auth/JWT in report | absent |
| Raw Authorization header in report | absent |
| Generated Supabase credentials in report | absent |
| Raw Supabase status/start output | absent |
| Raw Edge logs | absent |
| Raw env/dotenv values | absent |
| Operational CSV path/content/filename in report | absent |
| Package output/zip/checksum committed | no |
| `.gstack` artifacts committed | no |
| `frontend/dist` committed | no |
| Untracked PNG / operational fixture committed | no |

## Validation

| Command/check | Result |
| --- | --- |
| Targeted package/runtime tests, first run | `87 passed`, `1 failed` by PowerShell process exit code `3221225477` |
| Targeted package/runtime tests, retry | `88 passed` |
| `npm run typecheck` | passed |
| `npm run build:api` | passed |
| `npm run build` | passed |
| `npm run qa:screenshots` | passed |
| Package assembly smoke | passed |
| Package launcher `-CheckOnly` | passed |
| Package-local API smoke | passed |
| Direct no-auth Edge probes | recovered to auth-class |

The initial package assembly test failure was not fixed in this QA-only task. The retry passed without code changes, so it is recorded as a transient validation caveat.

## Blockers And Caveats

Resolved:

1. `edge_runtime_container_stopped`: resolved.
2. `edge_no_auth_503`: resolved.
3. `package_runtime_edge_unreachable`: resolved.
4. `db_edge_target_alignment`: remains aligned.

Caveats:

1. `supabase_start_instability`: multiple `supabase start` attempts failed before a later successful start.
2. `vector_restarting`: vector service remained restarting after recovery.
3. `grafana_unreachable`: Grafana remained unreachable; this is not the Edge upload blocker.
4. `raw_status_contains_credentials`: successful Supabase status/start output contains credential-like material and must remain suppressed.
5. `transient_package_test_failure`: first targeted test run failed from a PowerShell process exit code, then passed on retry without code changes.

## Final Judgment

| Question | Answer |
| --- | --- |
| Was legacy stack used? | no |
| Was independent package path used? | yes |
| Did Edge route move away from `503`? | yes |
| Does no-auth Edge route reach auth boundary? | yes |
| Does package runtime report Edge ready? | yes |
| Is DB/Edge target alignment still independent? | yes |
| Was Upload Preview run? | no |
| Was Upload Start run? | no |
| Was duplicate rerun run? | no |
| Was authenticated Edge upload called? | no |
| Is duplicate-safe rerun allowed next? | yes, with caveats |

## Next Step

Proceed to a separate operator package duplicate-safe rerun readiness QA only after reviewing this recovery report. Keep the next PR bounded: do not run full operational CSV upload, and do not run Start Upload until the duplicate-safe rerun readiness gate explicitly allows it.
