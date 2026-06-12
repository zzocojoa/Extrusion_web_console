# Operator Stage 1 Preview-Only Rerun QA

## Summary

- Date: 2026-06-12
- Branch: `codex/operator-stage-1-preview-only-rerun`
- Base commit: `0b6f3bfd9f14e200cdd8722f52a599c4442a9942`
- QA mode: report-only
- Stage: 1, small operational sample Preview-only rerun
- Stage 1 verdict: `blocked`
- Stage 2 small operational sample Start Upload allowed next step: `no`

This QA reran Stage 1 after the Edge runtime recovery report from
`docs/79_operator_edge_runtime_recovery_rerun.md`.

Fresh runtime preflight passed the Edge gate: API, DB, Studio, and Edge were
reachable enough for a bounded Preview attempt, and direct no-auth Edge `GET`
and `POST {}` returned `401` auth-class responses.

The single allowed Preview was then executed against a 5-row bounded temp sample
copy. Preview completed without DB mutation, but it did not reach DB
reconciliation. The run returned `dbStatus=not_checked` because the sample was
excluded before scanning with `file_date_missing`.

Because Stage 1 requires `dbStatus=reachable`, this rerun is blocked. Stage 2
Start Upload must not proceed from this evidence.

## Explicitly Not Performed

- feature code, launcher, backend, frontend, or packaging script edits;
- Supabase init, bootstrap, reset, start, or stop;
- DB migration, reset, delete, cleanup, prune, drop, or truncate;
- Docker volume, container, image, or network deletion;
- Upload Start;
- duplicate rerun;
- Edge authenticated upload call;
- Authorization header or token use;
- full operational dataset rollout;
- operational source mutation or deletion;
- production deploy;
- GitHub Release or tag creation.

## QA Environment

| Area | Result |
| --- | --- |
| Package path class | `repo-external-temp-package` |
| Frontend package mode for assembly | `api` |
| Runtime target | independent `Extrusion_web_console` |
| Legacy fallback | not used |
| Source class | `bounded_temp_sample_copy` |
| Sanitized source label | `stage1-small-operational-sample` |
| Source file count | `1` |
| Sample row count | `5` |
| Operational original modified | no |
| Full operational dataset used | no |

The source path, source filename, full local path, CSV content, and row content
are intentionally not recorded.

## Package Smoke

| Check | Result |
| --- | --- |
| Package assembly | passed |
| Package `supabase/config.toml` | present |
| Package Edge Function asset | present |
| Package migration asset | present |
| Package forbidden asset scan | `0` matches |
| Package launcher `-CheckOnly` | exit code `0` |
| Launcher raw-value leak scan | clean |
| Package zip/checksum | not created |

The package was assembled only for QA smoke. Package output was not committed.

## Fresh Runtime Preflight

| Check | Result | Notes |
| --- | --- | --- |
| Sanitized Supabase status | exit code `0` | Raw status output was suppressed. |
| API port | reachable | Independent target class. |
| DB port | reachable | Independent target class. |
| Studio port | reachable | Independent target class. |
| Edge runtime container | running | Independent stack. |
| Edge no-auth `GET` | `401` auth-class | No Authorization header used. |
| Edge no-auth `POST {}` | `401` auth-class | Safe empty object body only. |
| Package-local `/api/health` | `ok` | Temporary package-local backend. |
| Package-local `/api/runtime/local-supabase` overall | `attention` | Non-core caveats remain. |
| Package-local runtime API | `ready` | Core path ready. |
| Package-local runtime DB | `ready` | Core path ready. |
| Package-local runtime Studio | `ready` | Core path ready. |
| Package-local runtime Edge | `ready` | Edge gate passed. |
| DB target class | independent | Raw value hidden. |
| Edge target class | independent | Raw value hidden. |

The runtime gate was good enough to attempt exactly one bounded Preview. The
remaining `attention` state is not caused by Edge.

## Source Scope

| Check | Result |
| --- | --- |
| Bounded source selected | yes |
| Source label sanitized | yes |
| Operational original read-only | yes |
| Temp sample copy used | yes |
| Sample row count | `5` |
| Full dataset avoided | yes |
| Raw source path recorded | no |
| Raw source filename recorded | no |
| Row content recorded | no |

The bounded temp sample was intentionally smaller than the available source so
Stage 1 would not expand into a broad operational run.

## Preview-Only Result

| Metric | Result |
| --- | --- |
| Preview executions | `1` |
| Preview status | `succeeded` |
| `dbStatus` | `not_checked` |
| Preview total count | `1` |
| Already-in-db count | `0` |
| Upload-target count | `0` |
| Excluded count | `1` |
| Risky count | `0` |
| Partial-overlap count | `0` |
| Failed/invalid count | `0` observed |
| Upload-row estimate | `0` |
| DB matched rows | `0` |
| Blocking item class | `excluded` |
| Blocking reason code | `file_date_missing` |

The Preview API returned a successful run status because the file was classified
cleanly, but it did not satisfy Stage 1 because DB reconciliation was not
performed.

No second Preview was run.

## DB Non-Mutation Evidence

| Check | Result |
| --- | --- |
| DB count before Preview | reachable |
| DB count after Preview | reachable |
| DB row-count delta | `0` |
| DB reset/delete/cleanup/prune | not run |
| DB migration | not run |

Preview did not mutate the independent DB row count.

## Audit And Redaction

| Check | Result |
| --- | --- |
| Audit API read-only check | reachable |
| Preview audit rows returned | yes |
| Audit credential marker scan | clean |
| Audit path/operational filename marker scan | clean |
| Preview response credential marker scan | clean |
| Preview detail raw path-like field | present in API schema, not recorded |
| Raw secret values in report | absent |
| Raw DB URL in report | absent |
| Token/auth/JWT values in report | absent |
| Raw operational CSV path/content/filename in report | absent |
| Raw row content in report | absent |

The report records only sanitized labels, status classes, reason codes, and
counts. Preview detail responses include path-like fields by API schema, so raw
detail payloads were not copied into this report.

## Browser/UI Smoke

| Check | Result |
| --- | --- |
| Live `/upload` browser smoke | not run |
| Reason | Stage 1 stopped after `dbStatus=not_checked`; no need to expose live detail payloads. |
| Mock screenshot QA | passed |
| Raw path/secret screenshot marker scan | clean in screenshot QA artifacts |

The live UI was not used to advance or repair the blocked Preview result.

## Blockers And Caveats

Resolved from previous Stage 1 attempt:

- Edge runtime was running.
- Edge no-auth `GET` and `POST {}` returned auth-class `401`, not `503`.
- Package-local runtime Edge reported `ready`.

Current blocker:

- `dbStatus=not_checked`: Preview excluded the bounded sample before DB
  reconciliation due to `file_date_missing`.

Current caveats:

| Caveat | Current state | Impact |
| --- | --- | --- |
| Vector | restarting/non-ready marker observed | Carry forward as runtime caveat. |
| Grafana | package-local runtime reports unreachable despite container health marker | Carry forward as observability caveat. |
| Supabase start instability history | not re-triggered in this QA | No start/stop was run. |
| Preview API detail shape | path-like fields exist by schema | Do not paste raw detail payloads into reports. |

## Stage 2 Go/No-Go

| Question | Answer |
| --- | --- |
| Did fresh runtime preflight pass? | yes, with caveats |
| Was source bounded? | yes |
| Did Preview run exactly once? | yes |
| Did Preview reach `dbStatus=reachable`? | no |
| Did Preview mutate DB rows? | no |
| Is Stage 2 Start Upload allowed next? | no |

Stage 2 is blocked. The next action should be another Stage 1 Preview-only QA
using a bounded sample that preserves the metadata needed for date selection and
DB reconciliation, while still avoiding raw path, filename, content, and row
evidence in the report.

## Validation

| Command or check | Result |
| --- | --- |
| Targeted package/runtime/upload preview backend tests | `117 passed` |
| `npm run typecheck` | passed |
| `npm run build:api` | passed |
| API-mode package assembly smoke | passed |
| Package launcher `-CheckOnly` | passed |
| Fresh runtime preflight | Edge auth-class and package-local Edge `ready` |
| Preview-only execution count | exactly `1` |
| Read-only DB row-count delta | `0` |
| `npm run build` | passed |
| `npm run qa:screenshots` | passed |

## Next Action

Do not run Stage 2 Start Upload from this Preview.

Prepare a separate Stage 1 Preview-only rerun with a bounded source whose
sanitized temp sample preserves file-date metadata. Keep the same guardrails:
one Preview only, no Start Upload, no duplicate rerun, no authenticated Edge
upload call, no full dataset rollout, and no destructive runtime or DB cleanup.
