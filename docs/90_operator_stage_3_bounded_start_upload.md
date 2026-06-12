# Operator Stage 3 Bounded Start Upload QA

## Summary

- Date: 2026-06-12
- Branch: `codex/operator-stage-3-bounded-start-upload`
- Base commit: `4768ec6ebe52afa862be9ffee6694dbe7073b19e`
- QA mode: report-only Start Upload QA
- Stage: Stage 3 Profile A corrected bounded source
- Sanitized source label: `profile_a_corrected_bounded_source`
- Source scope class: `batch_bounded`
- Source kind class: `plc`
- Upload Preview executions during this QA: `0`
- Start Upload executions during this QA: `1`
- Duplicate rerun executions: `0`
- Retry Failed executions: `0`
- Full operational dataset rollout: not performed
- Verdict: `blocked`

Start Upload was executed exactly once from the previously approved corrected
bounded Preview evidence. The upload job did not pass the Stage 3 gate. It
finished as `failed` before any rows were uploaded or accepted, and the
independent DB row-count delta stayed `0`.

No second Start Upload, Retry Failed, duplicate rerun, Edge authenticated manual
call, or full operational rollout was executed after the failure.

## Explicitly Not Performed

- feature code, launcher, backend, frontend, or packaging script edits;
- second Start Upload;
- Retry Failed;
- duplicate rerun or forced duplicate upload;
- manual Edge authenticated upload call;
- full operational dataset rollout;
- Supabase init, bootstrap, reset, start, or stop;
- DB migration, reset, delete, cleanup, prune, drop, or truncate;
- Docker volume, container, image, or network deletion;
- operational source mutation or deletion;
- production deploy;
- GitHub Release or tag creation;
- feature branch deletion.

## Operator Count Confirmation

The operator-provided objective and merged Preview evidence confirmed the
bounded batch before Start Upload:

| Check | Confirmed value |
| --- | ---: |
| Expected source file count | `1` |
| Expected Preview upload target rows | `24515` |
| Expected failed files before upload | `0` |
| Expected invalid files before upload | `0` |
| Expected excluded files before upload | `0` |
| Expected risky files before upload | `0` |
| Expected duplicate rerun count | `0` |
| Expected Start Upload execution count | `1` |

The upload job later proved that the upload execution path failed before it
could upload or accept rows. Therefore the expected DB delta was not reached.
The actual DB delta and accepted-row counts are recorded separately below.

## Corrected Bounded Source Recheck

| Check | Result |
| --- | --- |
| Sanitized source label | `profile_a_corrected_bounded_source` |
| Source scope class | `batch_bounded` |
| Source kind class | `plc` |
| Source exists | yes |
| Source is directory | yes |
| CSV file count | `1` |
| Row count status | `counted` |
| Physical source row count | `24515` |
| Eligible file count | `1` |
| `file_date_missing` count | `0` |
| Profile A file range `1-3` | passed |
| Profile A row range `1-25000` | passed |
| Full operational dataset used | no |
| Operational source modified | no |

Raw source path, source filename, source content, row content, and full local
path are not recorded.

## Fresh Runtime Preflight

| Check | Result |
| --- | --- |
| QA API `/api/health` | reachable |
| QA API `/api/config` | reachable |
| QA API `/api/runtime/local-supabase` | reachable |
| Independent DB direct read | reachable |
| Independent DB row count before Start Upload | `20225` |
| Independent Studio TCP check | reachable |
| Edge no-auth `GET` direct probe | auth-class |
| Edge no-auth `POST {}` direct probe | auth-class |
| Corrected source process override | configured |
| Local Supabase containers | running |

Important caveat: the direct independent DB and Edge probes passed, but the
backend process used for Start Upload was later found to be using a stale
upload target class for the upload execution path. That mismatch should have
blocked Start Upload before the job was created.

## Prior Preview Evidence Used

| Metric | Result |
| --- | --- |
| Preview run ID | `prv_c09dc35af26c` |
| Preview status | `succeeded` |
| `dbStatus` | `reachable` |
| Preview total files | `1` |
| Target files | `1` |
| Upload target rows | `24515` |
| Already-in-db files | `0` |
| Excluded files | `0` |
| Risky files | `0` |
| Partial-overlap files | `0` |
| Failed files | `0` |
| Invalid files | `0` |
| `file_date_missing` count | `0` |

No additional Upload Preview was executed during this Start Upload QA.

## Start Upload Result

| Metric | Result |
| --- | --- |
| Start Upload executions | `1` |
| Upload job ID | `upl_ce40b106c644` |
| Job create status | `queued` |
| Final job status | `failed` |
| Total files | `1` |
| Succeeded files | `0` |
| Failed files | `1` |
| Cancelled files | `0` |
| Total rows | `24515` |
| Processed rows | `0` |
| Uploaded rows | `0` |
| Accepted rows | `0` |
| Deprecated inserted-row alias | `0` |
| Warning count | `0` |
| File status summary | `failed:1` |
| Job event count | `5` |
| Job event types | `job.created`, `job.started`, `file.started`, `file.failed`, `job.failed` |

Safe failure classification:

| Check | Result |
| --- | --- |
| Job error code | `upload_failed` |
| File error code | `upload_failed` |
| Failure class | connection refused during upload execution |
| Raw error message recorded in this report | no |
| Retry allowed in this PR | no |
| Second Start Upload allowed in this PR | no |

## DB Non-Mutation Evidence

| Check | Result |
| --- | ---: |
| DB row count before Start Upload | `20225` |
| DB row count after failed Start Upload | `20225` |
| DB row-count delta after Start Upload | `0` |
| Accepted rows | `0` |
| Uploaded rows | `0` |
| Processed rows | `0` |

The job failed before any upload batch completed. DB delta and accepted/uploaded
counts are therefore consistent with no DB mutation.

## Exact-Key Evidence

| Check | Result |
| --- | ---: |
| Canonical upload record count | `24515` |
| Unique transformed exact-key count | `21333` |
| DB-matched exact keys after failed upload | `0` |

Because the upload job failed before processing rows, exact-key presence is not
complete. This blocks Stage 3 acceptance for this batch.

## Audit, Job Event, SSE, And Log Evidence

| Evidence | Result |
| --- | --- |
| `upload.start` audit rows for this job | `1` |
| `upload.start` audit result | `success` |
| `upload.failed` audit rows for this job | `1` |
| `upload.failed` audit result | `failure` |
| Audit error code class | `upload_failed` |
| Job event levels | `info:3`, `error:2` |
| SSE/job-event persistence | events persisted in job detail |
| Raw source path/name/content marker in job/audit evidence | not detected |
| Secret/DB URL/token/Auth/JWT marker in job/audit evidence | not detected |

The report records only safe action, result, error-code, and count classes. It
does not include raw event error messages because they can contain operational
source names.

## UI And Browser Smoke

| Check | Result |
| --- | --- |
| Backend-served `/upload` HTTP route | `200` |
| Backend-served `/logs` HTTP route | `200` |
| Backend-served `/settings` HTTP route | `200` |
| HTTP route marker scan | clean |
| Browser `/upload` smoke | `200`, console errors `0`, marker matches `0` |
| Browser `/logs` smoke | `200`, console errors `0`, marker matches `0` |
| Browser `/settings` smoke | `200`, console errors `0`, marker matches `0` |

Screenshots were written only to ignored `.gstack` artifacts and are not part of
the PR.

## Stop Condition Result

| Stop condition | Result |
| --- | --- |
| Runtime target mismatch or config drift | triggered |
| Upload Job final status failed/cancelled/unknown | triggered, `failed` |
| DB delta differs from expected upload completion | triggered because upload failed before mutation |
| Start Upload 2회 이상 risk | mitigated by stopping after first execution |
| Raw source path/name/content/secret exposure risk | not triggered in report |

The failed job is not accepted Stage 3 evidence. Do not repair this by running
Retry Failed, duplicate rerun, a second Start Upload, DB cleanup, or Docker
cleanup in this PR.

## Redaction Result

| Check | Result |
| --- | --- |
| Raw source path recorded | no |
| Raw source filename recorded | no |
| Raw source content recorded | no |
| Row content recorded | no |
| Full local path recorded | no |
| Raw DB URL recorded | no |
| Token, Authorization header, or JWT recorded | no |
| Operational source modified | no |

## Blockers

| Blocker | Impact |
| --- | --- |
| Start Upload job failed before processing rows | Stage 3 Start Upload acceptance is blocked. |
| Upload execution target drift was discovered after job failure | The next attempt must prove backend API config and direct DB/Edge probes are aligned before Start Upload. |
| DB row-count delta stayed `0` with accepted rows `0` | No upload success evidence exists for this batch. |

## Next Step

Do not proceed to acceptance review. Do not run full rollout.

Recommended next branch:

```text
codex/operator-stage-3-bounded-start-upload-investigation
```

Recommended next QA flow:

1. investigate why the QA backend upload execution path used a stale upload
   target class while the direct independent preflight passed;
2. prove `/api/config`, `/api/runtime/local-supabase`, direct DB count, and
   Edge no-auth probes all describe the same independent target before any
   upload;
3. only after review, run a new bounded Start Upload attempt in a separate
   approved PR;
4. still do not run duplicate rerun, Retry Failed, DB cleanup, Docker cleanup,
   or full operational dataset rollout.

## Validation

| Command or check | Result |
| --- | --- |
| Corrected bounded source recheck | passed |
| Runtime direct DB/Edge preflight | passed with caveat |
| Backend API config alignment check | blocked, stale upload target class observed |
| Start Upload execution count | exactly `1` |
| Upload Job final status | `failed` |
| DB row-count delta after failed Start Upload | `0` |
| Exact-key post-failure DB match | `0` |
| Audit/job event redaction scan | passed |
| UI/browser smoke | passed |
| Duplicate rerun execution count | `0` |
| Retry Failed execution count | `0` |
| Full operational dataset rollout | not performed |
| Targeted backend package/runtime/upload tests | passed, `161` tests |
| `npm run typecheck` | passed |
| `npm run build:api` | passed |
| `npm run build` | passed |
| `npm run qa:screenshots` | passed, `1` Playwright test |
| `git diff --check` | passed |
| New document marker scan | passed |
| PR file scope | passed, QA report document only |
