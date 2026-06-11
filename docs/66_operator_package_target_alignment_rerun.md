# Operator Package Target Alignment Rerun QA

Date: 2026-06-11

Branch: `codex/operator-package-target-alignment-rerun`

Base commit: `91d327286d47ed3699cd9a4b5d1ae3216eddf4c2`

Scope: report-only QA after PR #79. This run checks whether the assembled operator package now includes repo-owned Supabase source assets, whether the previous `config_toml_missing` package-path blocker is resolved, and whether the package launcher path keeps Preview DB reconciliation and Start Upload Edge routing on the same independent `Extrusion_web_console` stack class.

This QA did not modify feature code, launcher code, backend code, frontend code, packaging scripts, production deployment, GitHub Release, or GitHub tag. No Supabase init/bootstrap/start/reset, DB migration, DB reset/delete/truncate/drop/cleanup/prune, Docker container/volume/image/network delete, Upload Start, duplicate rerun, authenticated Edge upload call, Authorization header, token use, operational full-source upload, operational source modification, or operational source deletion was run.

## Summary

Alignment verdict: `blocked`.

PR #79 fixed the package asset blocker. The assembled API-mode operator package contains `supabase/config.toml`, the `upload-metrics` function source, the upload contract migration, `supabase/README.md`, and `supabase/.gitignore`. Package denylist and redaction validation passed with zero matches, and package-local settings confirmed that the default project path resolves to the package root and can see `supabase/config.toml`.

The previous `config_toml_missing` runtime blocker is resolved. The package-launched backend returned `/api/runtime/local-supabase` with `reasonCode=docker_unavailable`, not `config_toml_missing`.

Target alignment is still blocked. Package-local settings classified `supabaseDbUrl` as `legacy`, while the computed Edge target class was `independent`. That means Preview DB reconciliation and Start Upload Edge routing are not proven to target the same independent stack from the operator package path.

Runtime reachability was also blocked because Docker was unavailable during this QA. Independent API port `55321`, DB port `25433`, Studio port `55323`, and direct no-auth Edge route probes were unreachable. Because DB was unreachable and token/header use was out of scope, this QA did not run Preview-only, Upload Start, duplicate rerun, or an authenticated Edge call.

## QA Environment

| Item | Result |
| --- | --- |
| QA mode | report-only |
| Execution path | operator package launcher path |
| Backend port | alternate local port |
| Frontend mode | API-mode packaged frontend |
| Package output | repo-external temporary package |
| Runtime setup action | not run |
| Upload Preview | not run |
| Upload Start | not run |
| Duplicate rerun | not run |
| Edge authenticated upload call | not run |
| Authorization header or token | not used |
| Docker delete / DB reset / cleanup / prune | not run |
| Production deploy / Release / tag | not run |

## Package Asset Presence

| Check | Result |
| --- | --- |
| Package assembly | passed |
| Package frontend mode | `api` |
| `supabase/config.toml` | present |
| `supabase/README.md` | present |
| `supabase/.gitignore` | present |
| `supabase/functions/upload-metrics/index.ts` | present |
| `supabase/migrations/20260608000001_create_all_metrics_upload_contract.sql` | present |
| Package required paths | present |
| Package Supabase assets validation | present |
| Package denylist matches | `0` |
| Package redaction matches | `0` |

Forbidden package classes were absent: raw env files, Supabase local state directories, DB state files, generated dumps/backups, logs, operational data files, package zip/checksum outputs, repo tests, frontend source, and generated QA artifacts.

## Operator Path Evidence

| Check | Result |
| --- | --- |
| Package launcher `-CheckOnly` | passed |
| Package shortcut installer `-CheckOnly` | passed |
| Package launcher backend | reachable |
| Package launcher path class | operator package path |
| Repo dev backend path | not used |
| Package default project path | package root, path hidden |
| Package-local `supabase/config.toml` | present |
| `config_toml_missing` resolved | yes |

## Runtime Readiness

| Check | Result |
| --- | --- |
| Docker daemon | unavailable |
| Independent API port `55321` | unreachable |
| Independent DB port `25433` | unreachable |
| Independent Studio port `55323` | unreachable |
| Direct no-auth Edge `GET` | unreachable |
| Direct no-auth Edge `POST {}` | unreachable |
| Package runtime endpoint | HTTP `200` |
| Package runtime overall status | `blocked` |
| Package runtime reason | `docker_unavailable` |
| Package runtime project id | `Extrusion_web_console` |
| Package Docker / API / DB / Studio / Edge | `unreachable` / `unreachable` / `unreachable` / `unreachable` / `unreachable` |
| Missing required containers | `12` |

Assessment: package asset ownership is fixed, but live runtime readiness cannot pass until Docker and the independent local Supabase stack are available.

## Target Class Comparison

| Target | Evidence | Class |
| --- | --- | --- |
| `localSupabaseProjectId` | package config/default reported `Extrusion_web_console` | independent |
| `localSupabaseApiPort` | package config/default reported `55321` | independent |
| `localSupabaseDbPort` | package config/default reported `25433` | independent |
| `localSupabaseStudioPort` | package config/default reported `55323` | independent |
| `localSupabaseProjectPath` | package root, raw path hidden | package-local |
| `supabaseDbUrl` | package-local settings classified hidden configured value by port class | legacy |
| `supabaseUrl` | package-local settings classified value as missing | missing |
| `supabaseEdgeUrl` / computed upload Edge URL | package-local settings classified computed target by port class | independent |
| `supabaseAnonKey` | configured, raw value hidden | configured/hidden |
| `plcDataDir` | configured and exists, raw path hidden | configured/hidden |

Conclusion: DB reconciliation target class and Edge target class are not aligned. The package path now owns Supabase assets, but the currently loaded DB URL still points at the legacy class while Edge routing computes from the independent local API port.

## Preview And DB Evidence

| Check | Result |
| --- | --- |
| Preview-only rerun | not run |
| Preview latest read-only query | reachable, marker caveat |
| Preview `dbStatus` from rerun | not applicable |
| Independent DB read-only exact-key count | not run, DB port unreachable |
| Upload Start | not run |
| Duplicate rerun | not run |
| Authenticated Edge upload call | not run |

Preview-only was not rerun because it would require protected write flow token use, and runtime DB reachability was already blocked. The latest Preview read-only API response contained operational filename marker classes from prior state; raw values were not recorded in this report.

## Browser, Audit, And Redaction

| Check | Result |
| --- | --- |
| `/` HTTP smoke | `200`, marker scan clean |
| `/upload` HTTP smoke | `200`, marker scan clean |
| `/logs` HTTP smoke | `200`, marker scan clean |
| `/settings` HTTP smoke | `200`, marker scan clean |
| `/api/health` read-only smoke | `200`, marker scan clean |
| `/api/config` read-only smoke | `200`, marker scan clean |
| `/api/audit?limit=1` read-only smoke | `200`, marker scan clean |
| `/api/runtime/local-supabase` read-only smoke | `200`, raw path/secret not recorded |
| Latest Preview API marker scan | operational filename marker class present, raw values omitted |
| Raw DB URL in report | absent |
| Raw token/auth/JWT in report | absent |
| Raw Authorization header in report | absent |
| Operational source path/content/filename in report | absent |
| Raw row content in report | absent |
| Raw generated credentials | absent |

## Blockers And Caveats

### Blockers

1. `db_edge_target_class_mismatch`: package-local settings classified `supabaseDbUrl` as legacy and computed Edge target as independent.
2. `docker_unavailable`: Docker was unavailable, so independent runtime reachability and container state could not pass.
3. `independent_runtime_unreachable`: API, DB, Studio, and Edge route probes for the independent stack were unreachable.

### Caveats

1. `preview_not_rerun`: Preview-only was not rerun because protected token use was out of scope and DB reachability was already blocked.
2. `read_only_db_count_not_available`: independent DB exact-key count was not run because the DB port was unreachable.
3. `latest_preview_marker_caveat`: the latest Preview read-only response contained operational filename marker classes from prior state. Raw values were not recorded.
4. `legacy_config_persistence`: the DB target mismatch appears to come from persisted package-loaded config or inherited environment. It must be corrected without documenting raw values.

### Passed

1. `package_supabase_assets_present`: PR #79 package asset inclusion is working.
2. `config_toml_missing_resolved`: package runtime no longer blocks on missing `supabase/config.toml`.
3. `operator_launcher_backend_reachable`: packaged launcher path started a reachable backend on the alternate local port.
4. `package_redaction_safe`: package assembly denylist and redaction checks reported zero matches.
5. `dangerous_operations_avoided`: no forbidden Supabase, DB, Docker delete, Upload Start, duplicate rerun, Edge authenticated upload, release, tag, or deploy action was run.

## Duplicate-Safe Rerun Decision

Duplicate-safe rerun allowed next step: `no`.

Do not proceed to a duplicate-safe rerun or any upload execution from the operator package path until:

1. the hidden DB target class is corrected to independent or the legacy fallback is explicitly selected and documented as fallback;
2. package-launched config proves DB and Edge target classes are both independent with raw values hidden;
3. Docker and the independent local Supabase runtime are available;
4. package runtime readiness is no longer blocked;
5. a separate QA confirms Preview `dbStatus=reachable` through the operator package path.

## Validation

| Command/check | Result |
| --- | --- |
| Package assembly smoke | passed |
| Package file manifest scan | required Supabase assets present, forbidden classes `0` |
| Package launcher `-CheckOnly` | passed |
| Package shortcut installer `-CheckOnly` | passed |
| Package launcher backend smoke | backend reachable |
| Package-local settings smoke | config exists, DB class legacy, Edge class independent |
| Runtime endpoint smoke | HTTP `200`, blocked with `docker_unavailable` |
| Browser `/`, `/upload`, `/logs`, `/settings` HTTP smoke | loaded, marker clean |
| API `/api/health`, `/api/config`, `/api/audit?limit=1` smoke | loaded, marker clean |
| Upload Preview | not run |
| Upload Start / duplicate rerun / authenticated Edge upload | not run |

## Next Step

Open a config/QA follow-up to remove the legacy DB target from the operator package path without exposing raw config values, then rerun operator package target alignment after Docker and the independent local Supabase runtime are available.
