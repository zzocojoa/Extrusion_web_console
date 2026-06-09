# Independent Start Upload Readiness

Date: 2026-06-09

Branch: `codex/independent-start-upload-readiness`

Base commit: `c9a12e120f8b749335e3e1db3b8d2543ff836a7b`

Scope: report-only QA for bounded Start Upload readiness against the independent `Extrusion_web_console` local Supabase runtime.

This QA run did not modify feature code, launcher code, backend code, frontend code, packaging scripts, production deployment, GitHub Release, or GitHub tag. No Supabase init/bootstrap/start/reset, DB migration, DB reset/delete/truncate/drop/cleanup/prune, Docker container/volume/image/network delete, Upload Start, Start Upload button click, authenticated Edge upload call, Authorization header, token use, operational full-source upload, operational source modification, or operational source deletion was run.

## Summary

Readiness verdict: `ready_with_caveats`.

The independent local Supabase core runtime remained available. Docker was reachable, the expected independent container family was present, API port `55321`, DB port `25433`, and Studio port `55323` were reachable, and direct no-auth Edge `GET` and `POST {}` probes returned auth-class `401` responses rather than `503`.

The backend runtime endpoint reported Docker, API, DB, Studio, and Edge as `ready` when the temporary backend was explicitly targeted at the independent Edge URL class. Overall status remained `attention` because Grafana was unreachable. Grafana remains link/status-only and is not the bounded Start Upload readiness blocker.

Start Upload was not executed. The Start Upload button was not clicked. No authenticated Edge upload call was made. The readiness decision uses the merged PR #74 DB-checkable Preview result as the Preview precondition: `succeeded`, `dbStatus=reachable`, total `1`, target `1`, already-in-DB `0`, excluded `0`, upload rows `5`, and DB matched rows `0`.

## QA Environment

| Item | Result |
| --- | --- |
| QA mode | report-only |
| Runtime setup action | not run |
| Supabase status | checked with raw output suppressed |
| Backend smoke | temporary loopback backend |
| Frontend smoke | API-mode build served by backend for browser checks |
| Bounded source basis | merged PR #74 synthetic bounded source evidence |
| Preview rerun in this QA | not run |
| Upload Start | not run |
| Start Upload button | not clicked |
| Edge authenticated call | not run |
| Authorization header or token | not used |
| Docker delete / DB reset / cleanup / prune | not run |
| Production deploy / Release / tag | not run |

## Runtime Readiness

| Check | Result |
| --- | --- |
| Docker daemon | reachable |
| Independent container count | `12` |
| Edge runtime container | running |
| Vector container | stopped/restarting caveat |
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

Runtime caveat: a temporary backend must be explicitly targeted at the independent Edge URL class for the backend Edge probe to report `ready`. The next bounded Start Upload smoke must keep the same independent target class and must not silently fall back to the legacy Edge route.

## Config, Source, And Auth Presence

| Config item | Result |
| --- | --- |
| `plcDataDir` | configured through env, source folder exists |
| `supabaseDbUrl` | configured through env, raw value hidden |
| `supabaseUrl` | configured through env |
| `supabaseAnonKey` | configured through env, raw value hidden |
| `supabaseEdgeUrl` | configured through env, raw value hidden |
| `localSupabaseProjectId` | `Extrusion_web_console` |
| Local API token guard | dev-disabled for the temporary maintainer backend |

Secret-bearing config items were rendered and recorded only as presence/hidden metadata. Raw DB URLs, keys, tokens, Authorization headers, JWT values, and raw Edge URL values were not recorded.

Local token caveat: this readiness smoke used a temporary maintainer backend in dev-disabled local-token mode. The later bounded Start Upload smoke should either use the operator launcher token bootstrap or explicitly document the maintainer backend token mode without exposing token values.

## Bounded Source Safety

| Field | Result |
| --- | --- |
| Source basis | PR #74 DB-checkable bounded Preview |
| Source label | `synthetic_bounded_plc_sample` |
| Source class | synthetic small PLC sample |
| Sample row count | `5` |
| Operational full-source upload | not run |
| Operational source modification/deletion | not run |
| Raw CSV path/content/filename | not printed or documented |

The bounded source evidence is sufficient for readiness because PR #74 exercised DB reconciliation on a small synthetic source and produced a bounded target. It is not an operational full-source ingest rehearsal.

## Preview Precondition

This QA did not rerun Upload Preview because the merged PR #74 result already provides the DB-checkable bounded Preview precondition.

| Field | PR #74 Result |
| --- | --- |
| Preview status | `succeeded` |
| `dbStatus` | `reachable` |
| Preview total count | `1` |
| Upload-target count | `1` |
| Already in DB count | `0` |
| Excluded count | `0` |
| Upload rows | `5` |
| DB matched rows | `0` |
| DB reconciliation | exercised by exact `(timestamp, device_id)` keys |

The current temporary backend also had a latest Preview record available, but it was not the DB-checkable PR #74 readiness source. This report therefore treats PR #74 as the authoritative Preview precondition and avoids overstating the current persisted latest Preview state.

## Edge And Auth Readiness

| Check | Result |
| --- | --- |
| Direct no-auth Edge route | auth-class `401` |
| Backend Edge readiness | `ready` with independent target class |
| Authenticated Edge upload call | not run |
| Authorization header value | not used or recorded |
| Token/JWT value | not used or recorded |

The no-auth route confirms the request reaches the auth boundary instead of failing at the runtime/gateway level. It does not prove authenticated upload execution; that remains the next separately approved smoke.

## Browser And UI Readiness

Browser smoke used the API-mode frontend build served by the temporary backend.

| Page | Loaded | Console errors | Marker scan | Notes |
| --- | --- | ---: | --- | --- |
| `/upload` | yes | `0` | clean | Preview-related UI text was present. Start Upload was not clicked. |
| `/logs` | yes | `0` | clean | Logs page loaded for read-only smoke. |
| `/settings` | yes | `0` | clean | Settings page loaded without raw secret/path markers in DOM scan. |

The smoke did not click Start Upload. The smoke did not make an authenticated Edge upload call. `Already in DB` wording was not re-proven with an already-in-DB row because the readiness precondition target count came from PR #74 and had `0` already-in-DB items.

## Audit And Redaction

| Check | Result |
| --- | --- |
| Audit API | reachable, read-only query only |
| Audit rows sampled | `20` |
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

None for proceeding to a separately approved bounded Start Upload smoke.

### Caveats

1. `explicit_independent_edge_target_required`: backend Edge readiness was accepted only with the independent Edge target class explicitly applied to the temporary backend. The next smoke must keep that target class and must not use a legacy Edge route.
2. `grafana_unreachable`: backend runtime remains `attention` because Grafana is unreachable. Grafana is link/status-only and not the Start Upload execution path.
3. `vector_container_restarting`: vector remains a secondary runtime caveat while API, DB, Studio, and Edge are reachable.
4. `dev_disabled_token_mode`: this smoke used a temporary maintainer backend with local token guard dev-disabled. The actual bounded Start Upload smoke must document token guard mode without exposing token values.
5. `synthetic_source_only`: readiness is based on a bounded synthetic source, not an operational full-source ingest rehearsal.
6. `already_in_db_wording_not_observed`: no already-in-DB row was available in the readiness evidence, so that UI wording remains unproven for this exact smoke.

### Passed

1. `core_runtime_ready`: Docker, API, DB, Studio, and Edge readiness passed for the independent target class.
2. `edge_auth_boundary_reachable`: direct no-auth Edge route returned auth-class, not `503`.
3. `config_source_auth_present`: source, DB, Supabase URL, anon key, Edge URL, and project id were present as configured/hidden metadata.
4. `preview_precondition_ready`: merged PR #74 provides DB-checkable `dbStatus=reachable` Preview evidence with bounded target rows.
5. `audit_read_only_safe`: Audit API read-only query was reachable and marker scan was clean.
6. `ui_redaction_safe`: `/upload`, `/logs`, and `/settings` DOM scans did not expose raw secret/path markers.
7. `dangerous_operations_avoided`: no forbidden Supabase, DB, Docker delete, Upload Start, Edge auth, release, tag, or deploy action was run.

## Start Upload Next-Step Decision

Start Upload allowed next step: `yes_with_caveats`.

The next task may run exactly one bounded Start Upload smoke in a separate branch/PR, only if it:

1. uses the same independent runtime target class;
2. uses a bounded synthetic or otherwise explicitly approved small source;
3. uses the PR #74-style DB-checkable Preview precondition or reruns Preview-only first;
4. records only sanitized counts/status;
5. does not perform operational full-source upload;
6. does not expose raw secrets, DB URLs, tokens, Authorization headers, JWTs, CSV paths, CSV filenames, or CSV row content.

## Validation

| Command/check | Result |
| --- | --- |
| Targeted backend runtime/config/upload preview/upload job tests | `133 passed` |
| `npm run typecheck` | passed |
| `npm run build:api` | passed for API-mode browser smoke |
| `npm run build` | passed |
| `npm run qa:screenshots` | passed, `1` Playwright test |
| Direct runtime reachability | API/DB/Studio reachable, Edge auth-class |
| Backend runtime endpoint | API/DB/Studio/Edge ready, Grafana attention |
| Browser `/upload`, `/logs`, `/settings` smoke | loaded, console clean, marker clean |
| `git diff --check` | passed |
| New report marker scan | clean |
| PR file-scope check | docs-only |
| Forbidden artifact staged-file check | clean |

## Next Step

Open a separate bounded Start Upload smoke PR only after this readiness report is reviewed and merged.

That next smoke is allowed to click Start Upload exactly once only under the bounded conditions above. Operational full-source upload remains out of scope.
