# Operator Stage 3 Bounded Start Upload Rerun 2

Date: 2026-06-13 Asia/Seoul

## Summary

Stage 3 Profile A corrected bounded source Start Upload was executed exactly
once using the latest corrected Preview reference created by PR #112.

Verdict: `passed`

The upload job reached terminal status `succeeded`. The job processed,
uploaded, and accepted `24515` physical source rows. The DB row-count delta was
`21333`, matching the expected net-new transformed exact-key count confirmed
before Start Upload.

Full rollout, Retry Failed, duplicate rerun, manual Edge authenticated upload,
and additional Upload Preview were not performed.

## Scope And Guardrails

| Item | Result |
| --- | --- |
| Source label | Stage 3 Profile A corrected bounded source |
| Latest Preview source | PR #112 corrected Preview reference |
| Additional Preview in this QA | `0` |
| Start Upload execution count | `1` |
| Retry Failed execution count | `0` |
| Duplicate rerun execution count | `0` |
| Full operational dataset rollout | not performed |
| Manual Edge authenticated upload call | not performed |
| Supabase start/stop/reset | not performed |
| DB migration/reset/delete/prune/drop/truncate | not performed |
| Docker cleanup/delete/prune | not performed |

## Fresh Backend Identity

| Field | Value |
| --- | --- |
| Health status | `ok` |
| `startup_id` | `api_f84523d48c5b` |
| `started_at` | `2026-06-12T16:05:45.312592+00:00` |
| `process_id` | `38316` |
| Stale backend reuse | not observed |
| QA backend cleanup | stopped after evidence capture |

## Runtime Preflight

| Check | Result |
| --- | --- |
| API reachable | passed |
| DB reachable | passed |
| Studio reachable | passed |
| Edge route reachable | passed |
| Edge no-auth GET | `401` auth-class |
| Edge no-auth POST `{}` | `401` auth-class |
| DB target class | `loopback_expected_db_port` |
| Upload Edge target class | `loopback_expected_api_port_upload_metrics` |
| Runtime Edge target class | `loopback_expected_api_port_upload_metrics` |
| Upload/runtime Edge alignment | `true` |
| Target class preflight | `passed` |
| Non-core runtime attention | Grafana unreachable only |

## Latest Preview Reference

| Field | Value |
| --- | ---: |
| Preview run | `prv_9414108271fc` |
| Preview status | `succeeded` |
| `dbStatus` | `reachable` |
| Profile | `stage3_profile_a_bounded_full_scan` |
| `forceFullScan` | `true` |
| `maxFiles` | `3` |
| `maxRunSeconds` | `300` |
| `maxFileSeconds` | `120` |
| Total files | `1` |
| Target files | `1` |
| Physical source rows from Preview item | `24515` |
| Local exact-key count | `21333` |
| Upload target rows | `21333` |
| DB matches in Preview | `0` |
| Risky files | `0` |
| Excluded files | `0` |
| Failed/invalid file evidence | `0` |
| Upload jobs after latest Preview before this QA | `0` |
| `upload.start` audit after latest Preview before this QA | `0` |

## Operator Count Confirmation

| Count | Value |
| --- | ---: |
| Physical source rows | `24515` |
| Transformed exact keys | `21333` |
| Direct DB exact-key matches before Start Upload | `0` |
| Expected net-new exact keys | `21333` |
| Expected DB row-count delta | `21333` |

The Start Upload expectation uses transformed exact-key evidence, not physical
source-line count. Physical upload/accepted counts and DB row-count delta are
therefore recorded separately.

## Start Upload Result

| Field | Value |
| --- | --- |
| Upload job | `upl_7c8464460259` |
| Final status | `succeeded` |
| Terminal status observed | yes |
| Elapsed polling time | `6.3s` |
| Total files | `1` |
| Succeeded files | `1` |
| Failed files | `0` |
| Cancelled files | `0` |
| Warning count | `0` |
| Job error code | none |
| Job error message | none |

## Row Counts

| Count | Value |
| --- | ---: |
| Job total rows | `24515` |
| Processed rows | `24515` |
| Uploaded rows | `24515` |
| Accepted rows | `24515` |
| Inserted rows reported by job | `24515` |
| File resume offset | `0` |
| File retry count | `0` |
| File last error | none |

## DB Evidence

| Field | Value |
| --- | ---: |
| DB rows before Start Upload | `20225` |
| DB rows after Start Upload | `41558` |
| DB row-count delta | `21333` |
| Expected net-new exact keys | `21333` |
| Exact-key presence after Start Upload | `21333` |
| Exact-key presence completeness | complete |

The DB delta matches the expected net-new transformed exact-key count. The job
row counters remain physical-row counters and are intentionally not treated as
the DB delta.

## Audit And Job Events

| Evidence | Result |
| --- | ---: |
| Upload jobs after latest Preview before Start Upload | `0` |
| Upload jobs after latest Preview after Start Upload | `1` |
| `upload.start` audit after latest Preview before Start Upload | `0` |
| `upload.start` audit after latest Preview after Start Upload | `1` |
| `upload.succeeded` audit | `1` |
| `job.created` events | `1` |
| `job.started` events | `1` |
| `file.started` events | `1` |
| `file.progress` events | `13` |
| `file.succeeded` events | `1` |
| `job.succeeded` events | `1` |

SSE/log-equivalent job event evidence was captured from the active state DB.
No failed, cancelled, retry, or duplicate upload event evidence was observed.

## Browser And UI Smoke

Browser screenshot QA is covered by `npm run qa:screenshots` in validation.
The Start Upload itself was executed through the backend API to preserve a
single auditable execution path and avoid accidental UI double-submit risk.

## Redaction Result

The report does not include credential material, operational source locator
details, source names, or source row content. Source scope is documented only as
a sanitized Stage 3 Profile A corrected bounded source label.

## Stage 3 Acceptance Go/No-Go

| Question | Answer |
| --- | --- |
| Did the latest corrected Preview reference pass? | yes |
| Did operator count confirmation pass? | yes |
| Was Start Upload executed exactly once? | yes |
| Did the upload job succeed? | yes |
| Did DB delta match expected exact-key net-new rows? | yes |
| Is exact-key presence complete after upload? | yes |
| Were Retry Failed, duplicate rerun, and full rollout avoided? | yes |
| Stage 3 acceptance review allowed? | yes |

## Caveats

| Caveat | Impact |
| --- | --- |
| Physical row count and transformed exact-key count differ | Expected for this source; operational interpretation must use the exact-key count for DB delta. |
| Grafana was unreachable in runtime readiness | Non-core for this upload path; API, DB, Studio, and Edge were ready. |

## Validation

| Check | Result |
| --- | --- |
| Fresh backend guard | passed |
| Runtime target preflight | passed |
| Corrected source scope confirmation | passed |
| Direct DB exact-key preflight | passed |
| Start Upload exactly once | passed |
| DB row-count delta check | passed |
| Exact-key presence check | passed |
| Targeted backend tests | `103 passed` |
| `npm run typecheck` | passed |
| `npm run build:api` | passed |
| `npm run build` | passed |
| `npm run qa:screenshots` | passed |
| `git diff --check` | passed |
| New document marker scan | passed |
| PR file scope check | passed, PR #113 includes this document only |

## Next Safe Action

Proceed to a separate Stage 3 bounded acceptance review branch:

```text
codex/operator-stage-3-bounded-acceptance-review
```

Do not run full rollout from this PR.
