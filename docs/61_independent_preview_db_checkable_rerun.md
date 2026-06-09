# Independent Preview DB-Checkable Rerun

Date: 2026-06-09

Branch: `codex/independent-preview-db-checkable-rerun`

Base commit: `3cbc45be02d84b29423def1483698049c7be2e54`

Scope: report-only QA for a DB-checkable bounded Upload Preview rerun against the independent `Extrusion_web_console` local Supabase runtime.

This QA run did not modify feature code, launcher code, backend code, frontend code, packaging scripts, production deployment, GitHub Release, or GitHub tag. No Supabase init/bootstrap/start/reset, DB migration, DB reset/delete/truncate/drop/cleanup/prune, Docker container/volume/image/network delete, Upload Start, authenticated Edge upload call, Authorization header, token use, operational source upload, operational source modification, or operational source deletion was run.

## Summary

Preview verdict: `passed`.

The independent runtime remained available after the Edge recovery and the previous Preview smoke. The expected independent container family was present, API, DB, and Studio ports were reachable, and direct no-auth Edge `GET` and `POST {}` probes returned auth-class `401` responses rather than `503`.

The backend runtime endpoint reported Docker, API, DB, Studio, and Edge as `ready`, with overall status `attention` only because Grafana remained unreachable. Grafana remains link/status-only and is not a Preview reconciliation blocker.

Upload Preview was executed once against a DB-checkable bounded source. The run finished `succeeded` with `dbStatus=reachable`. The sanitized result was total `1` candidate, target `1`, already-in-DB `0`, excluded `0`, risky `0`, upload rows `5`, and DB matched rows `0`. This confirms the Preview path reached the independent DB reconciliation query and classified the bounded candidate by exact keys.

## QA Environment

| Item | Result |
| --- | --- |
| QA mode | report-only |
| Runtime setup action | not run |
| Supabase status | checked with raw output suppressed |
| Backend smoke | temporary loopback backend with isolated config/state |
| Frontend smoke | API-mode build served by backend for browser checks |
| Bounded source | synthetic small PLC sample outside the repo |
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

## Config And Source Presence

| Config item | Result |
| --- | --- |
| `plcDataDir` | configured, source folder exists |
| `supabaseDbUrl` | configured through env override, raw value hidden |
| `supabaseUrl` | configured through env override, raw value not recorded |
| `supabaseAnonKey` | configured through env override, raw value hidden |
| `supabaseEdgeUrl` | configured through env override, raw value hidden |
| `localSupabaseProjectId` | `Extrusion_web_console` |

Secret-bearing config items were rendered by the Config API as overridden/hidden metadata. Raw DB URLs, keys, tokens, Authorization headers, and JWT values were not recorded.

## Bounded Source

| Field | Result |
| --- | --- |
| Source label | `synthetic_bounded_plc_sample` |
| Source class | synthetic small PLC sample |
| Source location | repo-external temporary folder, raw path not recorded |
| File count | `1` |
| Sample row count | `5` |
| Operational source files | not uploaded, modified, deleted, or copied into the repo |
| Raw CSV path/content/filename | not printed or documented |

The sample was created only to exercise Preview DB reconciliation. It was not committed and was not used for Upload Start.

## Upload Preview Result

Preview API call: `POST /api/upload/preview`.

| Field | Result |
| --- | --- |
| Request count | `1` |
| Preview status | `succeeded` |
| `dbStatus` | `reachable` |
| Preview total count | `1` |
| Already in DB count | `0` |
| Upload-target count | `1` |
| Partial-overlap count | `0` |
| Risky count | `0` |
| Excluded count | `0` |
| Failed / invalid count | `0` reported |
| Upload rows | `5` |
| DB matched rows | `0` |
| Item status groups | `target:1` |
| Scan mode | `full` |
| Sample rows observed | `5` |
| Row count observed | `5` |
| Local key count | `5` |
| DB match count | `0` |
| Upload row estimate | `5` |

Assessment: DB reconciliation was exercised and returned a reachable result. The bounded candidate was classified as a target because no exact `(timestamp, device_id)` matches were found in the independent DB.

## Browser And UI Smoke

Browser smoke used the API-mode frontend build served by the temporary backend.

| Page | Loaded | Console errors | Marker scan | Notes |
| --- | --- | ---: | --- | --- |
| `/upload` | yes | `0` | clean | Preview/Upload UI loaded and DB-related text was present. |
| `/settings` | yes | `0` | clean | Settings UI loaded without raw secret/path markers in DOM scan. |

The smoke did not click Start Upload. `Already in DB` wording was not observable because this Preview result had `0` already-in-DB rows.

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
| Raw CSV path/content/filename in report | absent |
| Raw Supabase status output | absent |
| Raw generated credentials | absent |

## Blockers And Caveats

### Blockers

None for Preview readiness.

### Caveats

1. `grafana_unreachable`: backend runtime remains `attention` because Grafana is unreachable. Grafana is link/status-only and not the Preview blocker.
2. `vector_container_restarting`: vector remains a secondary runtime caveat while API, DB, Studio, and Edge are reachable.
3. `already_in_db_wording_not_observed`: browser smoke could not confirm `Already in DB` wording because no already-in-DB rows were present in this Preview result.
4. `synthetic_source_only`: this was a bounded synthetic source, not an operational source ingest rehearsal. Start Upload still requires a separate approval and smoke.

### Passed

1. `edge_recovery_holds`: direct no-auth Edge route remained auth-class, not `503`.
2. `core_runtime_ready`: API, DB, Studio, and Edge readiness passed in the dedicated backend run.
3. `db_reconciliation_ready`: Preview reached the independent DB and returned `dbStatus=reachable`.
4. `preview_api_safe`: Upload Preview executed once and succeeded without Upload Start.
5. `audit_safe`: Preview audit row existed and marker scan was clean.
6. `ui_redaction_safe`: `/upload` and `/settings` DOM scans did not expose raw secret/path markers.
7. `dangerous_operations_avoided`: no forbidden Supabase, DB, Docker delete, Upload Start, Edge auth, release, tag, or deploy action was run.

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
| Upload Preview API smoke | succeeded with `dbStatus=reachable` |
| Browser `/upload` and `/settings` smoke | loaded, console clean, marker clean |
| Report marker scan | clean |
| PR file-scope check | docs-only |

## Next Step

Proceed to a separate Start Upload readiness smoke only after review and merge of this report.

The next smoke must remain bounded and separately approved. It must not use operational full-source upload by default, must not weaken Edge auth, and must continue to avoid raw secret, DB URL, token, Authorization header, JWT, CSV path, CSV filename, and CSV row disclosure in evidence.
