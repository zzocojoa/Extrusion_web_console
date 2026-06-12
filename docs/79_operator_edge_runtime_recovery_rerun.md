# Operator Edge Runtime Recovery Rerun QA

## Summary

- Date: 2026-06-12
- Branch: `codex/operator-edge-runtime-recovery-rerun`
- Base commit: `fb25039119e16508e37e983fdf4a27b7ceb92c86`
- QA mode: report-only
- Package path class: assembled operator package, repo-external temp package
- Recovery verdict: `recovered_with_caveats`
- Stage 1 Preview-only retry allowed next step: `yes_with_caveats`

This QA reran the operator Edge runtime recovery gate before retrying Stage 1
Preview-only. The Edge blocker was recovered:

- Before recovery, the independent Edge runtime container was not running.
- Before recovery, direct no-auth Edge `GET` and `POST {}` returned `503`.
- After recovery, the independent Edge runtime container was running.
- After recovery, direct no-auth Edge `GET` and `POST {}` returned `401`
  auth-class responses.
- Package-local `/api/runtime/local-supabase` reported Edge `ready`.

The remaining caveats are runtime stability and observability signals: Supabase
start instability during recovery, vector non-ready markers, and Grafana
unreachable. No Upload Preview, Upload Start, duplicate rerun, authenticated
Edge upload call, or full operational dataset rollout was performed.

## Scope And Guardrails

This QA did not modify feature code, launcher code, backend code, frontend code,
or packaging scripts.

This QA did not run:

- Supabase init, bootstrap, or reset;
- `supabase stop --no-backup`;
- DB migration, reset, delete, cleanup, prune, drop, or truncate;
- Docker volume, container, image, or network deletion;
- Upload Preview;
- Upload Start;
- duplicate rerun;
- Edge authenticated upload call;
- Authorization header or token usage;
- full operational dataset rollout;
- production deploy;
- GitHub Release or tag creation.

Allowed recovery actions used:

- operator package assembly smoke into a repo-external output location;
- package launcher `-CheckOnly`;
- package-local backend/API read-only smoke;
- package-local runtime readiness check;
- direct no-auth Edge `GET` and `POST {}` probes;
- sanitized Docker/Supabase status inspection;
- package-local `supabase stop`;
- package-local `supabase start`.

Raw generated credentials, connection strings, status output, and logs were not
recorded.

## QA Environment

| Item | Result |
| --- | --- |
| Runtime target | independent `Extrusion_web_console` |
| Legacy fallback | not used |
| Package assembly mode | `api` |
| Package `supabase/config.toml` | present |
| Package Edge Function asset | present |
| Package migration asset | present |
| Package forbidden asset scan | `0` matches |
| Package launcher `-CheckOnly` | exit code `0` |
| Launcher raw-value leak scan | clean |
| Operational source | not selected or consumed |

Package output path, full local paths, operational CSV path, operational
filename, CSV content, and row content are intentionally not recorded.

## Before Recovery

| Check | Before result |
| --- | --- |
| Edge runtime container | `not_running` |
| Direct no-auth Edge `GET` | `503` server-error class |
| Direct no-auth Edge `POST {}` | `503` server-error class |
| Independent API port | reachable |
| Independent DB port | reachable |
| Independent Studio port | reachable |
| Package-local `/api/health` | `ok` |
| Package-local `/api/config` | reachable; raw values hidden |
| Package-local `/api/runtime/local-supabase` | Edge `not_ready` |
| DB target class | independent |
| Edge target class | independent |

Raw Supabase status output was suppressed. No Authorization header was sent.
The POST probe used only an empty safe JSON object.

## Recovery Actions

Recovery was run from the assembled operator package project context.

| Step | Result |
| --- | --- |
| `supabase stop` | exit code `0` |
| `supabase start`, attempt 1 | exit code `1`; container-conflict/error class |
| `supabase start`, attempt 2 | exit code `0`; Edge running |
| Docker delete / volume delete / prune | not run |
| DB migration/reset/delete/cleanup/prune | not run |
| Raw generated credentials / connection strings | not recorded |

Successful `supabase start` and `supabase status` output can contain
credential-like material, so raw output remains suppressed. The report records
only exit codes, state classes, and availability markers.

Sanitized log inspection:

| Log source | Sanitized class |
| --- | --- |
| Edge runtime logs | Deno/error markers observed; raw logs suppressed |
| Vector logs | error marker observed; raw logs suppressed |

## After Recovery

| Check | After result |
| --- | --- |
| Edge runtime container | `running` |
| Direct no-auth Edge `GET` | `401` auth-class |
| Direct no-auth Edge `POST {}` | `401` auth-class |
| Independent API port | reachable |
| Independent DB port | reachable |
| Independent Studio port | reachable |
| Package-local `/api/health` | `ok` |
| Package-local `/api/runtime/local-supabase` overall | `attention` |
| Package-local runtime reason | `non_core_runtime_attention` |
| Package-local runtime API | `ready` |
| Package-local runtime DB | `ready` |
| Package-local runtime Studio | `ready` |
| Package-local runtime Edge | `ready` |
| Grafana reachability | `unreachable` |
| Vector caveat | non-ready marker observed |

The Edge readiness blocker is resolved. The remaining `attention` status is not
caused by Edge; package-local runtime readiness reports Edge `ready`.

## Target Alignment

| Target | Result |
| --- | --- |
| `localSupabaseApiPort` class | independent |
| `localSupabaseDbPort` class | independent |
| `localSupabaseStudioPort` class | independent |
| DB target class | independent |
| Edge target class | independent |
| DB/Edge alignment | aligned |
| Secret fields | hidden |

No raw DB URL, raw Edge URL, token, Authorization header, JWT, generated
credential, or secret value is recorded.

## Caveats

| Caveat | Current state | Impact |
| --- | --- | --- |
| Supabase start instability | first start attempt failed before a later successful start | Keep Stage 1 retry bounded and stop if Edge returns to `503`. |
| Vector | restarting/stopped non-ready markers observed | Observability/runtime caveat; not the Edge auth-class gate. |
| Grafana | unreachable | Not a core upload gate unless the operator requires Grafana readiness. |
| Raw status/log output | credential-like markers can appear | Continue suppressing raw Supabase output and raw logs. |

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

## Final Judgment

| Question | Answer |
| --- | --- |
| Was independent package path used? | yes |
| Was legacy fallback used? | no |
| Did Edge move away from `503`? | yes |
| Does no-auth Edge route reach auth boundary? | yes |
| Does package runtime report Edge ready? | yes |
| Is DB/Edge target alignment independent? | yes |
| Was Upload Preview run? | no |
| Was Upload Start run? | no |
| Was duplicate rerun run? | no |
| Was authenticated Edge upload called? | no |
| Was full operational rollout run? | no |
| Is Stage 1 Preview-only retry allowed next? | yes, with caveats |

## Validation

| Command or check | Result |
| --- | --- |
| Targeted package/runtime backend tests | `88 passed` |
| `npm run typecheck` | passed from `frontend` |
| `npm run build:api` | passed from `frontend` |
| `npm run build` | passed from `frontend` |
| `npm run qa:screenshots` | passed |
| Package assembly smoke | passed |
| Package launcher `-CheckOnly` | passed |
| Package-local API smoke | health and runtime passed; Edge `ready` |
| Direct no-auth Edge probes | recovered from `503` to auth-class `401` |

## Next Step

Retry Stage 1 small operational sample Preview-only in a separate QA PR. Keep
the retry bounded: if Edge returns `503`, vector/Grafana instability worsens, or
DB/Edge target alignment changes, stop before selecting or consuming an
operational source.
