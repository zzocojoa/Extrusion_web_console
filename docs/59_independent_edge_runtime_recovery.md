# Independent Edge Runtime Recovery

Date: 2026-06-09

Branch: `codex/independent-edge-runtime-recovery`

Scope: report-only QA for maintainer-approved recovery/rerun of the independent local Supabase Edge runtime.

This QA run did not modify feature code, launcher code, backend code, frontend code, packaging scripts, production deployment, GitHub Release, or GitHub tag. No Supabase init/bootstrap/reset, `supabase db reset`, `supabase db push`, explicit DB migration command, DB delete/truncate/drop/cleanup/prune command, Docker container/volume/image/network delete command, Upload Preview, Start Upload, authenticated Edge call, Authorization header, or token use was run.

## Summary

Recovery verdict: `recovered_with_caveats`.

The previous direct `503` blocker was reproduced before recovery: the independent Edge runtime container existed but was exited with code `255`, while API, DB, and Studio ports were reachable. Direct no-auth `GET` and `POST {}` probes to `/functions/v1/upload-metrics` returned `503` class responses.

Maintainer-approved runtime recovery used only `supabase stop` and `supabase start` from the repository-owned Supabase project context. The first `supabase start` attempt failed with raw output suppressed. A second `supabase start` attempt succeeded. After recovery, `supabase_edge_runtime_Extrusion_web_console` was running, API/DB/Studio remained reachable, and direct no-auth Edge `GET` and `POST {}` returned auth-class `401` responses instead of `503`.

Backend readiness was rerun with a dedicated temporary loopback backend process to avoid any existing local process state. It reported Edge `ready`, API/DB/Studio `ready`, no missing required containers, and overall `attention` only because Grafana remained unreachable. The Edge direct-vs-backend discrepancy is resolved for the dedicated backend run.

## QA Environment

| Item | Result |
| --- | --- |
| QA mode | report-only |
| Branch | `codex/independent-edge-runtime-recovery` |
| Base commit | `43692f19e405f5940ee8ca1fd91b208ae03714ad` |
| Supabase project context | repository-owned `supabase/` assets under this repo |
| Approved runtime actions | `supabase stop`, `supabase start` |
| Backend readiness smoke | temporary loopback backend with isolated config/state |
| Upload Preview / Start Upload | not run |
| Edge authenticated call | not run |
| Authorization header or token | not used |
| Docker delete / DB reset / cleanup / prune | not run |
| Production deploy / Release / tag | not run |

## Recovery Actions Performed

| Step | Result |
| --- | --- |
| Confirmed `supabase/config.toml` exists | pass |
| Confirmed project id | `Extrusion_web_console` |
| `supabase stop` | exit code `0` |
| First `supabase start` | exit code `1`, raw output suppressed |
| Second `supabase start` | exit code `0`, raw output suppressed |
| Raw generated credentials / connection strings | not recorded |
| Delete/reset/prune/drop/truncate markers in captured start/stop output | not observed |
| Explicit forbidden DB/Docker/Upload/Edge-auth command | not run |

Raw `supabase status` and `supabase start` output contained credential-like material during this QA, so the report records only availability states and status classes.

## Before And After Results

| Check | Before recovery | After recovery |
| --- | --- | --- |
| Independent container count | `12` | `12` |
| Edge runtime container | exited, code `255` | running |
| API port `55321` | reachable | reachable |
| DB port `25433` | reachable | reachable |
| Studio port `55323` | reachable | reachable |
| Direct no-auth `GET /functions/v1/upload-metrics` | `503` class | `401` auth-class |
| Direct no-auth `POST /functions/v1/upload-metrics` with `{}` | `503` class | `401` auth-class |
| Edge raw logs | suppressed | suppressed |
| Sanitized Edge log class | Deno/runtime marker class | Deno/runtime marker class |

The direct route result now satisfies the Edge readiness gate for unauthenticated route reachability: it reaches Supabase's auth boundary instead of returning gateway/runtime `503`.

## Backend Readiness Result

A dedicated temporary backend was started on a non-default loopback port for the final readiness rerun, with isolated config/state and explicit independent Edge URL class. No Upload Preview, Start Upload, or authenticated Edge call was made.

| Field | Result |
| --- | --- |
| `/api/health` | ok |
| `/api/config` | reachable |
| `/api/runtime/local-supabase` | reachable |
| Runtime overall status | `attention` |
| Runtime reason code | `non_core_runtime_attention` |
| Project id | `Extrusion_web_console` |
| Docker | `ready` |
| Supabase API | `ready` |
| Supabase DB | `ready` |
| Supabase Studio | `ready` |
| Edge | `ready` |
| Edge detail class | ready/auth-validation class |
| Missing required containers | `0` |
| Legacy container rows in runtime response | `0` |
| Grafana | `unreachable` |

Assessment: the Edge readiness discrepancy is resolved for the dedicated backend run. Overall status remains `attention` because Grafana is still unreachable, which is not the primary independent Supabase upload-readiness blocker.

## Remaining Blockers And Caveats

### Resolved

1. `edge_runtime_container_exited`: resolved. The independent Edge runtime container is running after recovery.
2. `edge_route_503`: resolved. Direct no-auth `GET` and `POST {}` now return auth-class `401`, not `503`.
3. `backend_edge_readiness`: resolved in a dedicated temporary backend run. Edge reports `ready`.

### Caveats

1. `grafana_unreachable`: backend readiness still reports Grafana unreachable. Grafana is link/status-only and not the Edge upload blocker.
2. `vector_container_restarting`: the vector container remained in restarting state after recovery. Core API/DB/Studio and Edge were reachable.
3. `first_start_failed`: the first `supabase start` attempt exited `1`; a second attempt exited `0`. Raw output was suppressed, so this remains an operational caveat to watch in the next smoke.
4. `raw_status_contains_credentials`: `supabase status` and successful start output contained credential-like material, so raw output must continue to be suppressed in reports.

### Not Tested By Design

1. Upload Preview was not run.
2. Start Upload was not run.
3. Authenticated Edge calls were not run.
4. Authorization headers or tokens were not used.
5. DB migrations, reset, delete, cleanup, prune, drop, and truncate were not run.
6. Docker container, volume, image, and network deletion was not run.
7. GitHub Release/tag and production deploy were not run.

## Edge Discrepancy Decision

Decision: `resolved_with_caveats`.

Direct no-auth Edge probes and dedicated backend readiness now agree that the Edge route is reachable. The remaining `attention` state is not caused by Edge; it is caused by non-core Grafana reachability, with vector still a secondary runtime caveat.

## Redaction Result

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
| Package output/zip/checksum committed | no |
| `.gstack` artifacts committed | no |
| `frontend/dist` committed | no |
| Untracked PNG / operational fixture committed | no |

## Validation

| Command/check | Result |
| --- | --- |
| Targeted backend runtime/config tests | `59 passed` |
| `npm run typecheck` | passed |
| `npm run build` | passed |
| `git diff --check` | passed |
| New report marker scan | clean |
| PR file-scope scan | clean |

Validation caveat: targeted backend tests emitted existing cache/deprecation warnings. No test failed.

## Next Step

Proceed to independent Preview smoke only after this recovery report is reviewed and merged. The Preview smoke must remain a separate task and must still avoid Start Upload until Preview succeeds with reachable DB and Edge readiness remains acceptable.

If a reviewer treats Grafana or vector as blocking for operator acceptance, run a separate runtime caveat investigation before Preview. Do not fold that into Upload Preview or Start Upload smoke.
