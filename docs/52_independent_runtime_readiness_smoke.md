# Independent Runtime Readiness Smoke

Date: 2026-06-08

Branch: `codex/independent-runtime-readiness-smoke`

Base commit: `6674c2726b415bc8eb674f2489e79b4ca570038d`

Scope: report-only QA for independent local Supabase runtime readiness after PR #63 and PR #64.

This smoke did not modify feature code, launcher code, backend code, frontend code, packaging scripts, local Supabase data, Docker data, database data, GitHub Releases, tags, production deployment, or operational CSV data.

No Supabase init/bootstrap/start/reset command was run. No DB migration was executed. No Docker container or volume delete was run. No Upload Preview, Start Upload, or authenticated Edge call was run.

## Summary

Final verdict: `blocked`.

The web console now targets the repository-owned independent local Supabase identity by default. Config and Settings show project id `Extrusion_web_console`, independent ports, and hidden secret fields. Runtime readiness also evaluates required containers with the `supabase_*_Extrusion_web_console` naming pattern.

Readiness is blocked in this environment because no independent local Supabase containers exist and API, DB, Studio, and Edge are unreachable on the independent ports. Docker, WSL, and Supabase CLI are available. Legacy containers are present, but the runtime readiness response does not treat them as satisfying the independent project requirements.

## QA Environment

| Item | Result |
| --- | --- |
| Backend/API-mode app | started on loopback for smoke |
| Frontend API-mode build | completed for UI smoke |
| Config source mode | clean temporary state/config; no raw secret evidence recorded |
| Runtime endpoint used | `GET /api/runtime/local-supabase` |
| Requested alias check | `GET /api/runtime/status` returned `404` |
| Mutating runtime commands | not run |
| Upload Preview / Start Upload | not run |
| Edge authenticated call | not run |

## Config Defaults

| Field | Expected | Measured |
| --- | --- | --- |
| Project id | `Extrusion_web_console` | pass |
| Project path | repo-owned project containing `supabase/` | pass |
| API port | `55321` | pass |
| DB port | `25433` | pass |
| Studio port | `55323` | pass |
| Supabase API URL default | empty / unset | pass |
| Computed Edge URL | derived from API port | pass |

`supabase/config.toml` was compared with backend settings. Project id, API port, DB port, and Studio port all matched. Computed Edge URL uses the configured API port.

## Settings UI Smoke

| Check | Result |
| --- | --- |
| Settings page loads in API mode | pass |
| Console errors during Settings smoke | `0` |
| Project id shown | `Extrusion_web_console` |
| API/DB/Studio ports shown | `55321` / `25433` / `55323` |
| `supabaseUrl` default shown empty | pass |
| Secret fields use password inputs | pass |
| Secret fields render empty replacement inputs | pass |
| Raw DB URL/token/Authorization/JWT pattern visible | no |
| Env override disabled behavior | covered by targeted config tests; clean smoke had no override fields |

Secret-bearing fields were checked as presence/hidden behavior only. Raw values were not recorded in this report.

## Runtime Readiness

| Check | Result |
| --- | --- |
| Overall status | `blocked` |
| Reason code | `required_container_missing` |
| Docker available | yes |
| WSL available | yes |
| Supabase CLI available | yes |
| Independent API reachable | no |
| Independent DB TCP reachable | no |
| Independent Studio reachable | no |
| Independent Edge route reachable | no |
| Grafana reachable | no |
| Required container count | `12` |
| Required container names use independent project id | yes |
| Required independent containers existing | `0` |

The blocked result is expected for a presence-only smoke before maintainer-approved independent stack setup. The app did not attempt to create or repair the missing stack.

## Legacy Runtime Confusion Check

| Check | Result |
| --- | --- |
| Legacy container family present | yes |
| Independent container family present | no |
| Runtime readiness accepted legacy containers for independent readiness | no |
| Required container naming basis | `supabase_*_Extrusion_web_console` |

This confirms the current readiness check is scoped to the independent project identity and does not silently pass because a legacy runtime is present.

## Dangerous Command Policy

| Policy item | Result |
| --- | --- |
| `supabase init` rejected by tests | pass |
| `supabase db reset` rejected by tests | pass |
| Docker run/create/rm rejected by tests | pass |
| Docker volume/prune rejected by tests | pass |
| Docker compose up/down/rm rejected by tests | pass |
| Arbitrary shell command rejected by tests | pass |
| Runtime start/stop buttons clicked | no |

Policy verification used existing targeted backend tests and did not execute destructive commands.

## Read-Only API Smoke

| Endpoint | Result |
| --- | --- |
| `GET /api/health` | `ok` |
| `GET /api/config` | pass |
| `GET /api/runtime/local-supabase` | pass |
| `GET /api/runtime/status` | `404` |

The implemented runtime status endpoint is `GET /api/runtime/local-supabase`. The requested `/api/runtime/status` alias is not present. This did not block the smoke because the current frontend and backend use the implemented endpoint, but it is a documentation/API naming caveat.

## Redaction Result

| Check | Result |
| --- | --- |
| Raw DB URL in report | absent |
| Raw token/auth/JWT in report | absent |
| Raw Authorization header in report | absent |
| Operational CSV path/content/filename in report | absent |
| Package output/zip/checksum committed | no |
| `.gstack` artifacts committed | no |
| `frontend/dist` committed | no |
| Operational CSV fixture committed | no |

## Validation

| Command/check | Result |
| --- | --- |
| `pytest` targeted runtime/config/local-token tests | `64 passed` |
| `npm run typecheck` | passed |
| `npm run build:api` | passed for API-mode UI smoke |
| `npm run build` | passed |
| `supabase/config.toml` vs settings comparison | passed |
| Settings UI browser smoke | passed |

Additional pre-PR hygiene checks are required before commit:

- `git diff --check`;
- report marker scan;
- PR file scope check;
- forbidden file staged check.

## Findings

### Blockers

1. `independent_runtime_missing`: required independent Supabase containers are absent, so readiness is `blocked|required_container_missing`.
2. `independent_ports_unreachable`: independent API, DB, Studio, and Edge ports are not reachable because the independent stack is not running.

### Caveats

1. `runtime_status_alias_missing`: `/api/runtime/status` returns `404`; the implemented endpoint is `/api/runtime/local-supabase`.
2. `grafana_unreachable`: Grafana is unreachable in this smoke. It is not a direct independent Supabase readiness blocker, but the runtime status reports it.
3. `env_override_ui_not_present_in_clean_smoke`: clean smoke had no env-overridden config fields, so UI disabled override state was validated through targeted tests rather than live browser state.

### Passed

1. `independent_defaults_ready`: default project id and ports match repo-owned Supabase config.
2. `legacy_not_confused`: legacy containers do not satisfy independent runtime readiness.
3. `secret_redaction_ready`: secret-bearing Settings fields are hidden/replacement-only and report scans found no sensitive markers.
4. `dangerous_policy_ready`: destructive command rejection remains covered by targeted tests.

## Merge Blocker Assessment

This QA report PR is documentation-only and has no feature-code merge blocker.

The runtime readiness result itself is blocked until the independent local Supabase stack is created by a separately approved maintainer setup step. That is expected for this presence-only smoke and should not be fixed in this report-only PR.

## Next Step

Create a separate maintainer-approved independent runtime setup/readiness task. It should prepare or start the independent stack without reset/delete/upload, then rerun this smoke. Only after independent API, DB, Studio, and Edge readiness pass should the team proceed to a fresh Upload Preview smoke.
