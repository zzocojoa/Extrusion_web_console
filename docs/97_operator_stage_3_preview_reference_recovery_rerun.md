# Operator Stage 3 Preview Reference Recovery Rerun

## Summary

- Date: 2026-06-13
- Branch: `codex/operator-stage-3-preview-reference-recovery-rerun`
- Base commit: `b16ad9fc945cff28c8ebec6a6170511f621a4a37`
- QA mode: report-only Preview reference recovery rerun
- Stage: Stage 3 Profile A corrected bounded source
- Sanitized source label: `profile_a_corrected_bounded_source`
- Source scope class: `batch_bounded`
- Source kind class: `plc`
- Required Preview profile: `stage3_profile_a_bounded_full_scan`
- Upload Preview executions during this QA: `1`
- Start Upload executions during this QA: `0`
- Retry Failed executions: `0`
- Duplicate rerun executions: `0`
- Edge authenticated upload calls: `0`
- Full operational dataset rollout: not performed
- Verdict: `passed_with_caveats`

The corrected Stage 3 Profile A bounded source was Previewed exactly once using
the explicit `stage3_profile_a_bounded_full_scan` profile merged in PR `#111`.

The Preview completed as `succeeded` with `dbStatus=reachable`, one uploadable
target file, no excluded/risky/failed/invalid file evidence, and no
`file_date_missing` evidence. Start Upload was not executed.

The main caveat is count interpretation: the physical source row count is
`24515`, while Preview produced an exact-key upload target estimate of `21333`.
This remains within Profile A bounds, but the operator must confirm that the
next Start Upload expectation should use transformed exact-key count evidence,
not physical source-line count.

## Explicitly Not Performed

- Start Upload;
- Retry Failed;
- duplicate rerun or forced duplicate upload;
- manual Edge authenticated upload call;
- full operational dataset rollout;
- Supabase init, bootstrap, start, stop, or reset;
- DB migration, reset, delete, cleanup, prune, drop, or truncate;
- Docker volume, container, image, or network deletion;
- operational source mutation or deletion;
- production deploy;
- GitHub Release or tag creation;
- feature branch deletion.

## Fresh Backend Identity

| Check | Result |
| --- | --- |
| Preview execution backend port class | ephemeral QA port |
| Preview execution backend health gate before Preview | passed |
| Preview execution uvicorn server process class | fresh server process observed |
| Preview execution stale backend reuse | not observed |
| Read-only recovery `/api/health` | reachable |
| Read-only recovery `startup_id` | `api_2cdc5101b2f3` |
| Read-only recovery `started_at` | `2026-06-12T15:53:28.554773+00:00` |
| Read-only recovery `process_id` | `44680` |

The Preview execution script reached `/api/health` before issuing the single
Preview request. Its final evidence formatter failed after Preview completion,
so the Preview execution `startup_id` was not retained in the captured output.
The backend was launched on an ephemeral QA port and the uvicorn server process
was observed in the sanitized backend log, so stale port reuse was not observed.

A second backend was launched later for read-only recovery evidence only. It did
not run Upload Preview, Start Upload, Retry Failed, duplicate rerun, or Edge
authenticated upload.

## Runtime Preflight

| Check | Result |
| --- | --- |
| API reachable | passed |
| DB TCP reachable | passed |
| Studio TCP reachable | passed |
| DB read-only query | passed |
| DB row count after Preview | `20225` |
| Edge no-auth `GET` | auth-class |
| Edge no-auth `POST {}` | auth-class |
| DB target class | `loopback_expected_db_port` |
| Upload Edge target class | `loopback_expected_api_port_upload_metrics` |
| Runtime Edge target class | `loopback_expected_api_port_upload_metrics` |
| Upload/runtime Edge alignment | `true` |
| Upload target preflight status | `passed` |
| Upload target preflight reason | `target_class_preflight_passed` |

No auth header was used for the Edge no-auth probes. Raw DB URL, token, source
path, source filename, source content, row content, and full local path were not
recorded.

## Corrected Source Recheck

| Check | Result |
| --- | ---: |
| Sanitized source label | `profile_a_corrected_bounded_source` |
| Source scope class | `batch_bounded` |
| Source kind class | `plc` |
| Source exists | yes |
| Source is directory | yes |
| CSV file count | `1` |
| Physical source row count | `24515` |
| Eligible file count | `1` |
| `file_date_missing` count | `0` |
| Profile A file range `1-3` | passed |
| Profile A row range `1-25000` | passed |
| Full operational dataset used | no |
| Operational source modified | no |

The source itself still matches the corrected Profile A bounded source class.

## Preview Request Profile

The persisted Preview run options show the required Stage 3 Profile A profile:

| Option | Result |
| --- | --- |
| `profile` | `stage3_profile_a_bounded_full_scan` |
| `forceFullScan` | `true` |
| `maxFiles` | `3` |
| `maxRunSeconds` | `300` |
| `maxFileSeconds` | `120` |
| `chunkRows` | `20000` |
| `sampleRows` | `200` |
| `stableLagMinutes` | `0` |

The failed default-timeout recovery class was not repeated.

## Preview-Only Result

| Metric | Result |
| --- | ---: |
| Preview execution count in this QA | `1` |
| Preview final status | `succeeded` |
| `dbStatus` | `reachable` |
| Preview total files | `1` |
| Target files | `1` |
| Already-in-db files | `0` |
| Partial-overlap files | `0` |
| Risky files | `0` |
| Excluded files | `0` |
| Failed files | `0` |
| Invalid files | `0` |
| Physical source rows | `24515` |
| Preview item row count | `24515` |
| Preview local exact-key count | `21333` |
| Upload target rows | `21333` |
| DB matched rows | `0` |
| Reason class | `db_no_match` |
| Scan mode | `full` |
| `file_date_missing` count | `0` |

The latest active state DB Preview is a corrected uploadable reference:

| Check | Result |
| --- | --- |
| Latest Preview is this recovery rerun | yes |
| Latest Preview status | `succeeded` |
| Latest Preview `dbStatus` | `reachable` |
| Latest Preview target files | `1` |
| Latest Preview target rows | `21333` |
| Latest Preview risky files | `0` |
| Latest Preview excluded files | `0` |

## Threshold Judgment

| Gate | Result |
| --- | --- |
| Preview execution count exactly `1` | passed |
| Start Upload execution count `0` | passed |
| Required profile used | passed |
| `dbStatus=reachable` | passed |
| Source file count within Profile A | passed |
| Source row count within Profile A | passed |
| Target files within Profile A max `3` | passed |
| Target rows within Profile A max `25000` | passed |
| Excluded files threshold `0` | passed |
| Risky files threshold `0` | passed |
| Failed files threshold `0` | passed |
| Invalid files threshold `0` | passed |
| `file_date_missing=0` | passed |
| Physical row vs exact-key target count | caveat, operator confirmation required |

## DB Non-Mutation Evidence

| Check | Result |
| --- | ---: |
| Prior merged Preview baseline DB row count | `20225` |
| DB row count after this Preview rerun | `20225` |
| Baseline-to-after row-count delta | `0` |
| Upload jobs after latest Preview | `0` |
| `upload.start` audit rows after latest Preview | `0` |

The execution script collected a direct DB count before and after the Preview,
but the final evidence formatter failed before printing that pair. The
recoverable evidence still shows no mutation path: Preview completed without
Start Upload, no upload job or upload.start audit was created after the latest
Preview, and the current read-only DB count matches the previously merged
Preview baseline.

## Start Upload Go/No-Go

| Question | Answer |
| --- | --- |
| Did Preview run exactly once? | yes |
| Did Preview complete successfully? | yes |
| Did Preview reach `dbStatus=reachable`? | yes |
| Did Preview use the Stage 3 timeout profile? | yes |
| Are target files and rows within Profile A bounds? | yes |
| Did Preview create failed/risky/invalid/excluded evidence? | no |
| Was Start Upload executed in this QA? | no |
| Is Start Upload allowed in this PR? | no |
| Is Start Upload eligible for a next separate QA branch? | yes, with caveats |

Next Start Upload QA must explicitly confirm whether the expected net-new DB
delta is the Preview exact-key target estimate of `21333`. Do not use the
physical source row count as the DB delta expectation without operator review.

## Caveats

| Caveat | Impact |
| --- | --- |
| Preview execution `startup_id` output was lost after the evidence formatter failed | Non-core evidence gap. Fresh ephemeral backend and server process evidence still indicate stale reuse was not observed. |
| Direct before/after DB count output was lost after Preview completion | Non-mutation evidence is recovered through prior baseline, current DB count, and absence of upload job/audit evidence. |
| Physical source rows differ from Preview exact-key target estimate | Operator count confirmation required before Start Upload. |
| UI `/upload` was not used to execute Preview | Backend Preview API evidence is authoritative for this recovery gate; screenshot QA is covered by project screenshot tests. |

## Redaction Result

| Check | Result |
| --- | --- |
| Raw source path recorded | no |
| Raw source filename recorded | no |
| Raw source content recorded | no |
| Row content recorded | no |
| Full local path recorded | no |
| Raw DB URL recorded | no |
| Token, auth header, or JWT recorded | no |
| Operational source modified | no |
| Package output, archive, or digest recorded | no |

## Validation

Required validation for this QA report:

- targeted backend package/runtime/upload preview tests;
- `npm run typecheck`;
- `npm run build:api`;
- `npm run build`;
- `npm run qa:screenshots`;
- `git diff --check`;
- new document marker scan;
- PR file scope check.

## Next Safe Action

If the caveats are accepted, the next branch can be:

```text
codex/operator-stage-3-bounded-start-upload-rerun-2
```

That next branch must use the latest corrected Preview reference from the same
active backend state DB, run Start Upload exactly once, and keep full rollout,
Retry Failed, duplicate rerun, and Edge authenticated manual upload calls
forbidden.
