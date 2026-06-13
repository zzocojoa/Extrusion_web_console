# Operator Stage 4 Start Upload Restored Reference QA

Date: 2026-06-13 Asia/Seoul

Branch: `codex/operator-stage-4-start-upload-restored-reference`

Base: `29596b93e3a990cf76d51c28de567c5f72ca98ee`

Scope: Stage 4 Start Upload from recovered PR #121 Preview reference

Verdict: `passed`

## Summary

Stage 4 Start Upload was executed exactly once after the recovered PR #121
Preview reference, fresh backend identity, runtime gates, target class preflight,
source scope, and target count confirmation all matched the approved values.

The upload job finished `succeeded`. It processed `17179` rows, uploaded `17179`
rows, and accepted `17179` rows. DB row-count delta was `17179`.

No additional Upload Preview, second Start Upload, Retry Failed, duplicate
rerun, manual authenticated Edge upload call, DB reset, Supabase lifecycle
operation, Docker lifecycle/destructive operation, or upload beyond the approved
target was performed.

## Approval And Scope

| Check | Result |
| --- | --- |
| User approval scope | Stage 4 Start Upload exactly once |
| Expected Preview reference | PR #121 recovered Preview |
| Expected Preview run | `prv_93e72aa21581` |
| Expected target files | `1` |
| Expected upload target rows | `17179` |
| Expected already-in-DB files | `1` |
| Additional Upload Preview allowed | no |
| Start Upload more than once allowed | no |
| Full rollout beyond approved target allowed | no |

## Fresh Backend Guard

| Check | Result |
| --- | --- |
| Fresh backend startup id | `api_b5321e9514fb` |
| Fresh backend started at | `2026-06-13T07:07:33.731890+00:00` |
| Fresh backend process id | `18452` |
| Backend host class | `loopback` |
| Backend port class | `ephemeral_loopback` |
| Stale backend reuse observed | no |
| Backend cleanup | stopped after evidence capture |

## Runtime Gates

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
| Upload/runtime Edge alignment | `true` |
| Target class preflight | `passed` |

The runtime `attention` state was from non-core runtime attention. The required
API, DB, Studio, Edge runtime, and target class gates all passed before Start
Upload.

## Source And Preview Confirmation

| Check | Result |
| --- | --- |
| Source config delivery | process-only env |
| Source locator class | `unc` |
| Source accessible to backend-style process | yes |
| Raw source locator recorded | no |
| Raw source filename recorded | no |
| Raw source content recorded | no |
| CSV count | `2` |
| Filename-date eligible CSV | `2` |
| `file_date_missing` | `0` |
| Latest Preview run | `prv_93e72aa21581` |
| Preview status | `succeeded` |
| `dbStatus` | `reachable` |
| Total files | `2` |
| Target files | `1` |
| Already-in-DB files | `1` |
| Excluded files | `0` |
| Risky files | `0` |
| Upload target rows | `17179` |
| DB matched rows | `20219` |
| Item status counts | `target:1`, `already_in_db:1` |
| Reason counts | `db_no_match:1`, `db_full_match:1` |

## Pre-Start Hard Stops

| Check | Result |
| --- | --- |
| Initial schema mismatch runner | stopped before Start Upload |
| Initial DB URL timeout runner | stopped before Start Upload |
| Start Upload calls before final gate | `0` |
| Final restored independent DB/API/Edge override | passed |
| Final pre-start confirmation | passed |

The first two guarded attempts did not call Start Upload. The only Start Upload
POST was the final execution after the restored reference and independent target
class were confirmed.

## Start Upload Result

| Check | Result |
| --- | --- |
| Start Upload execution count | `1` |
| Upload job id | `upl_d959e2a378a1` |
| Job final status | `succeeded` |
| Job target files | `1` |
| Succeeded files | `1` |
| Failed files | `0` |
| Cancelled files | `0` |
| Total rows | `17179` |
| Processed rows | `17179` |
| Uploaded rows | `17179` |
| Accepted rows | `17179` |
| Inserted rows | `17179` |
| Warning count | `0` |
| Job error code | none |
| Job error message | none |
| File status counts | `succeeded:1` |
| Latest job event seq | `14` |
| Event evidence | `job.created`, `job.started`, `file.started`, `file.progress`, `file.succeeded`, `job.succeeded` |

## DB Evidence

| Check | Before | After | Delta |
| --- | ---: | ---: | ---: |
| `all_metrics` row count | `41558` | `58737` | `17179` |
| Target range key-class count | `0` | `17179` | `17179` |

The DB delta matches the approved upload target rows and the job accepted rows.

## State And Audit Evidence

| Check | Before | After |
| --- | ---: | ---: |
| Upload jobs for restored Preview | `0` | `1` |
| Upload jobs total in restored QA state | `0` | `1` |
| `upload.start` audit count | `0` | `1` |
| `upload.preview` audit count | `1` | `1` |

No additional Preview was created during this QA. The only new state mutation was
the approved upload job and its `upload.start` audit record.

## Explicitly Not Performed

- Additional Upload Preview;
- second Start Upload;
- Retry Failed;
- duplicate rerun;
- manual authenticated Edge upload call outside the app flow;
- full rollout beyond the approved target;
- DB reset, init, delete, truncate, drop, or prune;
- Supabase reset, start, or stop;
- Docker delete or prune;
- operational source mutation or deletion.

## Redaction Result

This report does not include raw source locators, source names, source row
content, DB URL, credential material, local API token, Authorization header, JWT,
or connection strings. Source and target locations are recorded only as
sanitized classes.

## Validation

| Check | Result |
| --- | --- |
| Fresh backend guard | passed |
| Runtime gates | passed |
| Recovered Preview reference confirmation | passed |
| Target count confirmation | passed |
| Start Upload exactly once | passed |
| DB row-count delta | passed, `17179` |
| Upload job final status | passed, `succeeded` |
| Additional Preview check | passed, no additional Preview |
| Retry/duplicate/full-rollout check | passed, not performed |
| Redaction check | passed |
| `git diff --check` | passed |
| Targeted backend runtime/config/upload job tests | `68 passed` |
| `npm run typecheck` | passed |
| `npm run build:api` | passed |
| `npm run build` | passed |
| `npm run qa:screenshots` | passed |

## Next Safe Action

Review this report in PR. Do not run duplicate rerun or Retry Failed.

If accepted, the next operational step is an acceptance review of Stage 4 upload
evidence and whether any remaining source scope needs a separate Preview-only
gate before further upload action.
