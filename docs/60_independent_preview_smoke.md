# Independent Preview Smoke

Date: 2026-06-09

Branch: `codex/independent-preview-smoke`

Base commit: `02331df0ba772b82fef5acd87c80691ba4d11811`

Scope: report-only QA for Upload Preview against the independent `Extrusion_web_console` local Supabase runtime after Edge runtime recovery.

This QA run did not modify feature code, launcher code, backend code, frontend code, packaging scripts, production deployment, GitHub Release, or GitHub tag. No Supabase init/bootstrap/start/reset, DB migration, DB reset/delete/truncate/drop/cleanup/prune, Docker container/volume/image/network delete, Upload Start, authenticated Edge upload call, Authorization header, token use, operational source modification, or operational source upload was run.

## Summary

Preview verdict: `passed_with_caveats`.

The independent runtime remained available after the Edge recovery report. The expected independent container family was present, API, DB, and Studio ports were reachable, and direct no-auth Edge `GET` and `POST {}` probes returned auth-class `401` responses rather than `503`.

The backend runtime endpoint reported API, DB, Studio, and Edge as `ready`, with overall status `attention` because Grafana remained unreachable. This matches the caveat carried forward from the recovery report and is not the primary Upload Preview blocker.

Upload Preview was executed once with the approved Preview-only API call. It finished `succeeded` and returned a sanitized total of `3` preview items. All `3` items were `excluded`, with `0` upload targets, `0` already-in-DB items, `0` risky items, and `0` upload rows. Because the run had no DB-checkable upload target rows, `dbStatus` remained `not_checked`; therefore this smoke confirms safe Preview execution and redaction, but does not prove DB exact-key reconciliation on a non-excluded source slice.

## QA Environment

| Item | Result |
| --- | --- |
| QA mode | report-only |
| Runtime setup action | not run |
| Supabase status | checked with raw output suppressed |
| Backend smoke | temporary loopback backend with isolated config/state |
| Frontend smoke | API-mode build served by backend for browser checks |
| Upload Preview | run once |
| Upload Start | not run |
| Edge authenticated call | not run |
| Authorization header or token | not used |
| Docker delete / DB reset / cleanup / prune | not run |
| Production deploy / Release / tag | not run |

## Runtime Readiness Summary

| Check | Result |
| --- | --- |
| Independent container count | `12` |
| Edge runtime container | running |
| Vector container | restarting |
| `supabase status` exit code | `0`, raw output suppressed |
| API port `55321` | reachable |
| DB port `25433` | reachable |
| Studio port `55323` | reachable |
| Direct no-auth Edge `GET` | `401` auth-class |
| Direct no-auth Edge `POST {}` | `401` auth-class |
| Backend runtime overall status | `attention` |
| Backend runtime reason code | `non_core_runtime_attention` |
| Backend Docker / API / DB / Studio / Edge | `ready` / `ready` / `ready` / `ready` / `ready` |
| Backend Grafana | `unreachable` |
| Missing required containers | `0` |
| Legacy container rows in runtime response | `0` |

The backend runtime smoke used explicit independent runtime configuration in the temporary process. A first temporary backend attempt used an incompatible project-path interpretation and returned `config_toml_missing`; that process was stopped and rerun with the repository root as the Supabase CLI project context. No source change was made.

## Config And Source Presence

| Config item | Result |
| --- | --- |
| `plcDataDir` | configured, source folder exists |
| `supabaseDbUrl` | configured through env override, raw value hidden |
| `supabaseUrl` | configured through env override, raw value not recorded |
| `supabaseAnonKey` | env override present, raw value hidden |
| `supabaseEdgeUrl` | configured through env override, raw value hidden |
| `localSupabaseProjectId` | `Extrusion_web_console` |

Secret-bearing config items were rendered by the Config API as overridden/hidden metadata. Raw DB URLs, keys, tokens, Authorization headers, and JWT values were not recorded.

## Upload Preview Result

Preview API call: `POST /api/upload/preview`.

| Field | Result |
| --- | --- |
| Request count | `1` |
| Preview status | `succeeded` |
| `dbStatus` | `not_checked` |
| Source class | configured source, sanitized |
| Preview total count | `3` |
| Already in DB count | `0` |
| Upload-target count | `0` |
| Partial-overlap count | `0` |
| Risky count | `0` |
| Excluded count | `3` |
| Upload rows | `0` |
| DB matched rows | `0` |
| Failed / invalid count | `0` reported |
| Warnings | `0` |

Assessment: Preview execution itself passed. DB reconciliation was not exercised because the eligible source slice produced only excluded items. This should block progression directly to Start Upload smoke until a maintainer-approved bounded source scope yields at least one DB-checkable target or already-in-DB row with `dbStatus=reachable`.

## Browser And UI Smoke

Browser smoke used the API-mode frontend build served by the temporary backend.

| Page | Loaded | Console errors | Marker scan | Notes |
| --- | --- | ---: | --- | --- |
| `/upload` | yes | `0` | clean | Preview/Upload UI loaded; `Already in DB` wording was not observable because this run had no already-in-DB rows. |
| `/settings` | yes | `0` | clean | Settings UI loaded without raw secret/path markers in DOM scan. |

The smoke did not click Start Upload. The UI smoke did not find Start Upload text in the rendered page for this excluded-only Preview state.

## Audit And Redaction

| Check | Result |
| --- | --- |
| Preview audit row | present |
| Audit action | `upload.preview` |
| Audit result | `success` |
| Audit target type | `preview_run` |
| Audit marker scan | clean |
| Raw DB URL in report | absent |
| Raw token/auth/JWT in report | absent |
| Raw Authorization header in report | absent |
| Operational source path/content/filename in report | absent |
| Raw Supabase status output | absent |
| Raw generated credentials | absent |

## Blockers And Caveats

### Blockers For Start Upload Progression

1. `db_reconciliation_not_exercised`: Preview completed with `dbStatus=not_checked` because all observed items were excluded.
2. `no_upload_targets`: Upload-target count was `0`, so this run cannot support a Start Upload smoke decision.

### Caveats

1. `grafana_unreachable`: backend runtime remains `attention` because Grafana is unreachable. Grafana is link/status-only and not the Preview blocker.
2. `vector_container_restarting`: vector remains a secondary runtime caveat while API/DB/Studio/Edge are reachable.
3. `project_path_context`: a temporary backend started with the `supabase/` directory as project path reported `config_toml_missing`; rerunning with the repository root as project context resolved it. Future runbooks should be explicit that the Supabase CLI project context is the repo root containing `supabase/config.toml`.
4. `already_in_db_wording_not_observed`: browser smoke could not confirm `Already in DB` wording because no already-in-DB rows were present in this Preview result.

### Passed

1. `edge_recovery_holds`: direct no-auth Edge route remained auth-class, not `503`.
2. `core_runtime_ready`: API, DB, Studio, and Edge readiness passed in the dedicated backend run.
3. `preview_api_safe`: Upload Preview executed once and succeeded without Upload Start.
4. `audit_safe`: Preview audit row existed and marker scan was clean.
5. `ui_redaction_safe`: `/upload` and `/settings` DOM scans did not expose raw secret/path markers.
6. `dangerous_operations_avoided`: no forbidden Supabase, DB, Docker delete, Upload Start, Edge auth, release, tag, or deploy action was run.

## Validation

| Command/check | Result |
| --- | --- |
| Targeted backend runtime/config/upload preview tests | `104 passed` |
| `npm run typecheck` | passed |
| `npm run build` | passed |
| `npm run build:api` | passed for API-mode browser smoke |
| `npm run qa:screenshots` | passed, `1` Playwright test |
| Direct runtime reachability | API/DB/Studio reachable, Edge auth-class |
| Backend runtime endpoint | API/DB/Studio/Edge ready, Grafana attention |
| Upload Preview API smoke | succeeded |
| Browser `/upload` and `/settings` smoke | loaded, console clean, marker clean |

Pre-PR hygiene checks still required after this report is staged:

- `git diff --check`;
- report marker scan;
- PR file-scope check;
- forbidden file staged check.

## Next Step

Do not proceed directly to Start Upload smoke from this result.

Run a second maintainer-approved Preview smoke with a bounded source scope that produces at least one DB-checkable candidate and confirms `dbStatus=reachable`, while still avoiding Upload Start and authenticated Edge calls. If that follow-up Preview passes with reachable DB reconciliation and target/already-in-DB counts are acceptable, proceed to Start Upload readiness smoke in a separate branch.
