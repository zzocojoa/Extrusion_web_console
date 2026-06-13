# Operator Stage 4 Preview-Only Rerun 2 QA

Date: 2026-06-13 Asia/Seoul

Branch: `codex/operator-stage-4-preview-only-rerun-2`

Base: `686f1d4c7beb8718db8a78f6ee9f1da6af98a768`

Scope: Stage 4 full operational dataset Preview-only rerun 2 QA

Verdict: `passed_with_upload_targets`

## Summary

Stage 4 Preview-only rerun 2 was executed exactly once after the refreshed
source eligibility, fresh backend, runtime, and target-class gates passed.

The Preview run succeeded with `dbStatus=reachable`. It found one upload target
file with `17179` upload target rows and one already represented file with
`db_full_match`. DB row-count delta stayed `0`, and no upload job was created.

Start Upload remains forbidden until the user reviews these counts and
separately approves exactly one Start Upload.

## Explicitly Not Performed

- Start Upload;
- Retry Failed;
- duplicate rerun;
- authenticated Edge upload call;
- full operational dataset rollout;
- DB reset, init, delete, truncate, drop, or prune;
- Supabase reset, start, or stop;
- Docker delete or prune;
- operational source mutation or deletion.

## QA Environment

| Item | Result |
| --- | --- |
| Local `main` matched `origin/main` before branch | yes |
| QA branch created | yes |
| Fresh backend startup id | `api_00a726c3b4b3` |
| Fresh backend started at | `2026-06-13T03:32:04.770227+00:00` |
| Fresh backend process id | `40772` |
| Stale backend reuse observed | no |
| Temporary QA state DB used | yes |
| Source config delivery | `env` |
| Recommended path class | `unc_from_environment_or_config` |

## Sanitized Source Scope

| Item | Result |
| --- | --- |
| Sanitized source label | `stage4-full-candidate-a-refreshed` |
| Source class | `full_operational_dataset_candidate` |
| Source kind | `plc` |
| Source exists to backend-style process | yes |
| Raw source locator recorded | no |
| Raw source filename recorded | no |
| Raw source content opened | no |
| File count | `2` |
| CSV count | `2` |
| Filename-date eligible CSV | `2` |
| `file_date_missing` | `0` |
| Zero-row files | `0` |
| Total physical source rows | `37398` |
| Minimum rows per CSV | `17179` |
| Maximum rows per CSV | `20219` |

## Runtime Preflight

| Gate | Result |
| --- | --- |
| API reachable | passed |
| DB reachable | passed |
| Studio reachable | passed |
| Edge runtime reachable | passed |
| Runtime overall status | `attention` |
| Runtime reason | `non_core_runtime_attention` |
| Edge no-auth GET | `401 auth-class` |
| Edge no-auth POST `{}` | `401 auth-class` |
| DB target class | `loopback_expected_db_port` |
| Upload Edge target class | `loopback_expected_api_port_upload_metrics` |
| Runtime Edge target class | `loopback_expected_api_port_upload_metrics` |
| DB/Edge alignment | passed |
| Upload target preflight | `target_class_preflight_passed` |

The runtime status was `attention` only because of a non-core runtime attention
reason. The required Stage 4 gates for API, DB, Studio, Edge runtime, and
target class alignment all passed before Preview.

## Preview-Only Result

| Item | Result |
| --- | --- |
| Upload Preview execution count | `1` |
| Preview run id | `prv_93e72aa21581` |
| Request scope | approved refreshed source scope |
| Final status | `succeeded` |
| `dbStatus` | `reachable` |
| Total files | `2` |
| Candidate files | `2` |
| Target files | `1` |
| Already in DB files | `1` |
| Partial-overlap files | `0` |
| Risky files | `0` |
| Excluded files | `0` |
| Failed files | `0` |
| Invalid files | `0` |
| Upload target rows | `17179` |
| DB matched rows | `20219` |
| Item status counts | `target:1`, `already_in_db:1` |
| Reason class counts | `db_no_match:1`, `db_full_match:1` |

The result is actionable Preview-only evidence: one file is a new upload target,
and one file is already fully represented in DB.

## DB Non-Mutation Evidence

| Item | Result |
| --- | --- |
| DB row count before Preview | `41558` |
| DB row count after Preview | `41558` |
| DB row-count delta | `0` |
| Upload jobs created | `0` |
| Upload job files created | `0` |
| Upload job events created | `0` |
| Upload file state rows | `0` |
| `upload.start` audit rows | `0` |
| `upload.preview` audit rows | `1` |

Preview did not mutate production rows. The only local QA state change was the
expected Preview run record and Preview audit record in the temporary QA state
store.

## Decision

| Gate | Result |
| --- | --- |
| Source scope proven | passed |
| Filename-date metadata preserved | passed |
| Runtime gates passed | passed |
| Preview succeeded | passed |
| `dbStatus=reachable` | passed |
| DB delta `0` | passed |
| Upload target rows greater than `0` | passed |
| Start Upload allowed now | no |

Stage 4 Preview-only rerun 2 passes the Preview gate and produces non-zero
upload targets. This does not grant Start Upload approval.

## Browser And Redaction

| Item | Result |
| --- | --- |
| `/upload`, `/logs`, `/settings` screenshot QA | passed through `npm run qa:screenshots` |
| Raw source locator exposed in this document | no |
| Raw source filename exposed in this document | no |
| Raw row content exposed in this document | no |
| Credential or auth material exposed in this document | no |
| Package output included | no |

## Validation

| Check | Result |
| --- | --- |
| Targeted backend runtime/config/upload preview/upload job tests | `140 passed` |
| `npm run typecheck` | passed |
| `npm run build:api` | passed |
| `npm run build` | passed |
| `npm run qa:screenshots` | passed |
| `git diff --check` | passed |
| New document marker scan | passed |
| Branch diff file scope | docs-only |

## Caveats

- The Preview result proves target counts and duplicate classification only for
  the approved refreshed source scope.
- Start Upload requires separate explicit approval after count review.
- A duplicate rerun remains forbidden unless separately approved in a future
  scope.

## Next Safe Action

Review this PR. If accepted, the next branch can request explicit approval for
exactly one Stage 4 Start Upload using the recorded Preview run.

Start Upload remains forbidden until that separate approval is given.
