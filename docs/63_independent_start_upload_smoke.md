# Independent Start Upload Smoke

Date: 2026-06-09

Branch: `codex/independent-start-upload-smoke`

Base commit: `4d6089ed18780038cb9bcd8d37530b7a6730f155`

Scope: report-only QA for exactly one bounded Start Upload smoke against the independent `Extrusion_web_console` local Supabase runtime.

This QA run did not modify feature code, launcher code, backend code, frontend code, packaging scripts, production deployment, GitHub Release, or GitHub tag. No Supabase init/bootstrap/start/reset, DB migration, DB reset/delete/truncate/drop/cleanup/prune, Docker container/volume/image/network delete, operational full-source upload, operational source modification, operational source deletion, or duplicate rerun was performed.

## Summary

Upload smoke verdict: `passed_with_caveats`.

Exactly one Start Upload API call was executed against a bounded synthetic source. The Upload Job reached final status `succeeded`, reported accepted rows `5`, uploaded rows `5`, and produced `6` job events. The authenticated Edge upload path was exercised once through the Upload Job service. The independent DB exact-key check after the job found all `5` bounded synthetic keys present.

The smoke remained bounded. It used a synthetic small PLC sample with `5` rows, not an operational full-source ingest. Raw CSV path, filename, row content, DB URL, token, Authorization header, JWT, and generated credentials were not recorded.

Important caveat: the temporary backend was explicitly targeted at the independent Edge URL class, but the repo-local environment DB URL class was observed as legacy-port class when checked from the shell. Therefore, the final Preview produced a safe bounded target, and the independent Edge upload wrote the expected exact keys to the independent DB, but this smoke does not prove that the Preview reconciliation DB URL and Edge upload target were aligned to the same independent stack in the temporary backend. Treat this as a config-alignment caveat before final operator acceptance.

## QA Environment

| Item | Result |
| --- | --- |
| QA mode | report-only |
| Runtime setup action | not run |
| Backend smoke | temporary loopback backend with isolated state DB |
| Backend local token mode | dev-disabled maintainer mode |
| Frontend smoke | API-mode build served by backend |
| Bounded source | synthetic small PLC sample outside the repo |
| Sample row count | `5` |
| Upload Preview | final bounded Preview run succeeded |
| Start Upload | run exactly once |
| Edge authenticated upload call | exercised exactly once through Upload Job |
| Duplicate rerun | not run |
| Docker delete / DB reset / cleanup / prune | not run |
| Production deploy / Release / tag | not run |

## Runtime Readiness

| Check | Result |
| --- | --- |
| Docker daemon | reachable |
| Supabase API port `55321` | reachable |
| Supabase DB port `25433` | reachable |
| Supabase Studio port `55323` | reachable |
| Direct no-auth Edge `GET` | `401` auth-class |
| Direct no-auth Edge `POST {}` | `401` auth-class |
| Backend runtime overall status | `attention` |
| Backend Docker / API / DB / Studio / Edge | `ready` / `ready` / `ready` / `ready` / `ready` |
| Backend Grafana | `unreachable` |

Grafana remains link/status-only and was not treated as a Start Upload blocker.

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

Target-class caveat:

- Shell-level DB URL class was observed as legacy-port class.
- Shell-level Edge URL class was observed as legacy-port class.
- The temporary backend explicitly overrode Edge to the independent target class for the Upload Job.
- The temporary backend did not prove DB URL class alignment to the independent target during Preview reconciliation.

No raw values were recorded.

## Bounded Source Safety

| Field | Result |
| --- | --- |
| Source label | `synthetic_bounded_start_upload_sample` |
| Source class | synthetic small PLC sample |
| Source location | repo-external temporary folder, raw path not recorded |
| File count | `1` |
| Sample row count | `5` |
| Operational full-source upload | not run |
| Operational source modification/deletion | not run |
| Raw CSV path/content/filename | not printed or documented |

Two setup-only Preview attempts occurred before the final valid Preview:

1. An invalid Preview request was rejected before upload because the range mode was unsupported.
2. A synthetic filename that did not satisfy PLC date parsing yielded zero candidates.

No Start Upload was executed during those setup attempts. The final bounded source used a parseable synthetic PLC date class and produced one target candidate.

## Preview Precondition

| Field | Result |
| --- | --- |
| Final Preview status | `succeeded` |
| Final `dbStatus` | `reachable` |
| Preview total count | `1` |
| Upload-target count | `1` |
| Already in DB count | `0` |
| Excluded count | `0` |
| Upload rows | `5` |
| DB matched rows | `0` |
| Count bounded/safe | yes |

The Preview precondition was sufficient to allow exactly one bounded Start Upload. The target-class caveat above remains: DB reconciliation alignment to the independent DB was not proven by this temporary backend configuration.

## Start Upload Result

| Field | Result |
| --- | --- |
| Start Upload calls | `1` |
| Job id | present, value not recorded |
| Final job status | `succeeded` |
| Accepted rows | `5` |
| Uploaded rows | `5` |
| Job events count | `6` |
| SSE replay | `200` event-stream class |
| Duplicate rerun | not run |

Operator-facing wording caveat: the API exposes canonical accepted rows, and this report records accepted/uploaded counts. Browser mock screenshot QA still separately validates accepted-row wording.

## DB Exact-Key Check

| Check | Result |
| --- | --- |
| Legacy-class DB row count before | `13568232` |
| Legacy-class exact key matches before | `0` |
| Legacy-class row count delta after | `0` |
| Legacy-class exact key matches after | `0` |
| Independent DB reachable after upload | yes |
| Independent DB row count after | `5` |
| Independent exact key matches after | `5` |
| Independent synthetic device rows after | `5` |

Row-count baseline caveat: the pre-upload row count baseline was captured against the legacy-class DB URL, not the independent DB. Because duplicate rerun is forbidden, this report does not attempt a second upload to recreate the measurement. The independent DB after-state proves the bounded exact keys are present after the one approved upload.

## Audit And Redaction

| Check | Result |
| --- | --- |
| `upload.start` audit rows | `1` |
| Audit marker scan | clean |
| Raw DB URL in report | absent |
| Raw token/auth/JWT in report | absent |
| Raw Authorization header in report | absent |
| Operational source path/content/filename in report | absent |
| Raw CSV path/content/filename in report | absent |
| Raw Supabase status output | absent |
| Raw generated credentials | absent |

## Browser And UI Smoke

Browser smoke used the API-mode frontend build served by the temporary backend. It did not click Start Upload.

| Page | Loaded | Console errors | Marker scan | Notes |
| --- | --- | ---: | --- | --- |
| `/upload` | yes | `0` | clean | Upload/Preview UI loaded after the job. |
| `/logs` | yes | `0` | clean | Logs page loaded for read-only smoke. |
| `/settings` | yes | `0` | clean | Settings page loaded without raw secret/path markers in DOM scan. |

## Blockers And Caveats

### Blockers

None for the single bounded upload execution itself. The job succeeded and independent DB exact keys were present after upload.

### Caveats

1. `preview_db_edge_target_mixed`: Preview DB reconciliation was not proven to use the same independent target class as the Edge upload. This must be resolved before final operator acceptance.
2. `independent_pre_upload_db_baseline_missing`: independent DB pre-upload row count was not captured before the one approved upload. Duplicate rerun was not performed.
3. `grafana_unreachable`: backend runtime remains `attention` because Grafana is unreachable. Grafana is link/status-only and not the Start Upload execution path.
4. `dev_disabled_token_mode`: this smoke used a temporary maintainer backend with local token guard dev-disabled. Operator launcher token bootstrap remains a separate package/launcher acceptance concern.
5. `synthetic_source_only`: this was a bounded synthetic source, not an operational full-source ingest rehearsal.

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
| Upload Preview API smoke | succeeded with bounded target |
| Start Upload API smoke | succeeded, exactly one call |
| DB exact-key check | independent exact keys present after upload |
| Browser `/upload`, `/logs`, `/settings` smoke | loaded, console clean, marker clean |
| `git diff --check` | passed |
| New report marker scan | clean |
| PR file-scope check | docs-only |
| Forbidden artifact staged-file check | clean |

## Next Step

Review this report before merging.

Before final operator acceptance, run a follow-up config-alignment QA or implementation fix so Preview DB reconciliation and Edge upload target are both explicitly independent. Do not rerun this same bounded upload as a duplicate smoke. Operational full-source upload remains out of scope.
