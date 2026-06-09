# Independent DB/Edge Target Class Alignment

Date: 2026-06-09

Branch: `codex/independent-db-edge-target-alignment`

Base commit: `b70618bee71fa9719a4a6c71205cc10e72783da4`

Scope: report-only QA to resolve the PR #76 target-class caveat. This QA checks whether Upload Preview DB reconciliation and Start Upload Edge configuration can be targeted at the same independent `Extrusion_web_console` local Supabase stack.

This QA run did not modify feature code, launcher code, backend code, frontend code, packaging scripts, production deployment, GitHub Release, or GitHub tag. No Supabase init/bootstrap/start/reset, DB migration, DB reset/delete/truncate/drop/cleanup/prune, Docker container/volume/image/network delete, Upload Start, duplicate rerun, authenticated Edge upload call, Authorization header, token use, operational full-source upload, operational source modification, or operational source deletion was run.

## Summary

Alignment verdict: `aligned_with_caveats`.

The temporary maintainer backend was started on an alternate local port with isolated state and config files. Its Supabase DB, Supabase API, Edge, local runtime ports, project id, and bounded source settings were all supplied as explicit independent-target environment overrides. Raw values were not recorded.

Runtime readiness showed the independent Supabase stack available on API port `55321`, DB port `25433`, and Studio port `55323`. Direct no-auth Edge `GET` and `POST {}` probes returned auth-class `401`, proving the independent Edge route reached the auth boundary rather than returning `503`.

Upload Preview was rerun once against a bounded synthetic source. The run finished `succeeded` with `dbStatus=reachable`, total `1`, target `1`, upload rows `2`, and DB matched rows `0`. Since the temporary backend DB target was explicitly independent and the independent DB was reachable in read-only checks, this confirms Preview DB reconciliation can target the same independent stack class as the configured Edge route.

PR #76 exact-key evidence was rechecked read-only against the independent DB. The independent `all_metrics` table remained reachable with total rows `5`, distinct `(timestamp, device_id)` keys `5`, and device rows `5`.

## QA Environment

| Item | Result |
| --- | --- |
| QA mode | report-only |
| Backend smoke | temporary maintainer backend on alternate local port |
| Backend state/config | isolated temporary files outside the repo |
| Bounded source | synthetic small PLC sample outside the repo |
| Source row count | `2` |
| Runtime setup action | not run |
| Supabase status | checked with raw output suppressed |
| Upload Preview | run once |
| Upload Start | not run |
| Duplicate rerun | not run |
| Edge authenticated upload call | not run |
| Authorization header or token | not used |
| Docker delete / DB reset / cleanup / prune | not run |
| Production deploy / Release / tag | not run |

## Target Class Comparison

| Target | Evidence | Class |
| --- | --- | --- |
| `supabaseDbUrl` | Config API reported env override with hidden secret value; Preview returned `dbStatus=reachable`; independent DB read-only count succeeded | independent |
| `supabaseUrl` | Config API reported env override on independent API port | independent |
| `supabaseEdgeUrl` | Config API reported env override with hidden secret value; direct no-auth Edge route on independent API port returned auth-class `401` | independent |
| `supabaseAnonKey` | Config API reported env override with hidden secret value | configured/hidden |
| `localSupabaseProjectId` | Config API and runtime endpoint reported `Extrusion_web_console` | independent |
| `localSupabaseApiPort` | Config API reported independent API port `55321` | independent |
| `localSupabaseDbPort` | Config API reported independent DB port `25433` | independent |
| `localSupabaseStudioPort` | Config API reported independent Studio port `55323` | independent |
| `plcDataDir` | Config API reported env override and source exists | configured |

Conclusion: the temporary backend configuration aligned the DB reconciliation target and Edge target to the independent stack class. The PR #76 mixed-target caveat is resolved for this maintainer-run configuration.

## Runtime Readiness

| Check | Result |
| --- | --- |
| Docker daemon | reachable |
| Independent container family | present |
| Independent API port `55321` | reachable |
| Independent DB port `25433` | reachable |
| Independent Studio port `55323` | reachable |
| Direct no-auth Edge `GET` | `401` auth-class |
| Direct no-auth Edge `POST {}` | `401` auth-class |
| Backend runtime overall status | `attention` |
| Backend Docker / API / DB / Studio / Edge | `ready` / `ready` / `ready` / `ready` / `ready` |
| Backend Grafana | `unreachable` |
| Missing required containers | `0` |

Legacy ports were also reachable on the host, so side-by-side runtime availability remains true. The QA target was the independent port class only.

## Preview-Only Result

Preview API call: `POST /api/upload/preview`.

| Field | Result |
| --- | --- |
| Request count | `1` |
| Preview status | `succeeded` |
| `dbStatus` | `reachable` |
| Preview total count | `1` |
| Upload-target count | `1` |
| Already-in-DB count | `0` |
| Partial-overlap count | `0` |
| Risky count | `0` |
| Excluded count | `0` |
| Upload rows | `2` |
| DB matched rows | `0` |
| Preview item status | `target` |
| Local key count | `2` |
| DB match count | `0` |

Start Upload was not executed from this Preview. The Preview was used only to prove the DB reconciliation target class and `dbStatus=reachable`.

## Read-Only Exact-Key Evidence

| Check | Result |
| --- | --- |
| Independent DB reachable | yes |
| Independent `all_metrics` total rows | `5` |
| Independent distinct `(timestamp, device_id)` keys | `5` |
| Independent rows with device id | `5` |

Assessment: the PR #76 post-upload independent DB evidence remains internally consistent. This QA did not read or document raw key values, row contents, file paths, or filenames.

## Browser, Audit, And Redaction

| Check | Result |
| --- | --- |
| `/upload` HTTP smoke | `200`, marker scan clean |
| `/logs` HTTP smoke | `200`, marker scan clean |
| `/settings` HTTP smoke | `200`, marker scan clean |
| Audit API read-only query | reachable |
| Preview audit row | present |
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

None for target class alignment in the maintainer-run QA environment.

### Caveats

1. `temporary_backend_env_alignment`: alignment was proven with an explicit maintainer backend environment, not through the operator launcher package flow.
2. `no_authenticated_edge_upload`: this QA intentionally did not run Upload Start or an authenticated Edge upload call.
3. `legacy_stack_side_by_side`: legacy ports were also reachable on the host, so future QA must continue to classify target ports instead of assuming a single running stack.
4. `grafana_unreachable`: backend runtime remains `attention` because Grafana is unreachable. Grafana is link/status-only and not part of DB/Edge upload target alignment.
5. `synthetic_source_only`: Preview-only used a bounded synthetic source, not an operational full-source ingest rehearsal.

### Passed

1. `db_target_independent`: Preview DB reconciliation reached a DB target that was explicitly configured for the independent stack class.
2. `edge_target_independent`: Edge target was explicitly configured for the independent stack class and no-auth probes reached the auth boundary.
3. `db_edge_target_classes_match`: DB and Edge target classes matched in the same temporary backend process.
4. `pr76_independent_db_evidence_holds`: independent DB read-only count and distinct-key count remained `5`.
5. `redaction_safe`: report, API smoke, audit sample, and marker scans did not expose raw secrets, DB URLs, tokens, Authorization headers, JWTs, source paths, CSV filenames, or row contents.
6. `dangerous_operations_avoided`: no forbidden Supabase, DB, Docker delete, Upload Start, duplicate rerun, Edge authenticated upload, release, tag, or deploy action was run.

## Duplicate-Safe Rerun Decision

Duplicate-safe rerun allowed next step: `yes_with_caveats`.

Allowed means a future, separately approved QA may run a bounded duplicate-safe Start Upload or rerun check only if it:

1. uses an explicitly aligned independent DB and Edge target class;
2. stays bounded and does not use operational full-source upload;
3. records only sanitized status/count evidence;
4. does not expose raw DB URLs, tokens, Authorization headers, JWTs, source paths, CSV filenames, or row contents;
5. does not run DB reset/delete/cleanup/prune or Docker delete operations.

Do not rerun the exact PR #76 upload as an unapproved duplicate. Any future upload execution must be a separate approved smoke.

## Validation

| Command/check | Result |
| --- | --- |
| Targeted backend runtime/config/upload preview/upload job tests | `133 passed` |
| `npm run typecheck` | passed |
| `npm run build` | passed |
| `npm run qa:screenshots` | passed, `1` Playwright test |
| Direct runtime reachability | API/DB/Studio reachable, Edge auth-class |
| Backend runtime endpoint | API/DB/Studio/Edge ready, Grafana attention |
| Upload Preview API smoke | succeeded with `dbStatus=reachable` |
| Independent DB read-only count | reachable, total `5`, distinct keys `5` |
| Browser `/upload`, `/logs`, `/settings` HTTP smoke | loaded, marker clean |
| `git diff --check` | passed |
| New report marker scan | clean |
| PR file-scope check | docs-only report file |
| Forbidden artifact staged-file check | clean |

## Next Step

Review and merge this report before treating PR #76's DB/Edge target-class caveat as resolved for maintainer-run QA.

The next implementation or QA step should verify the same target-class alignment through the operator launcher/package path, without exposing raw secrets or operational source details.
