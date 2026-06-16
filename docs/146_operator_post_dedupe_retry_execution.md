# Operator Post-Dedupe Retry Execution

> Date: 2026-06-16 | Level: Dynamic | Status: Draft

---

## 1. Summary

### 1.1 Verdict

`succeeded`

The approved Retry Failed execution for `upl_59575d0cbe67` was performed exactly once after PR #161 was merged and runtime preflight passed.

### 1.2 Match Rate

`96%`

The retry met the approved execution scope and terminal success criteria. The remaining 4% caveat is that direct DB row-count delta was not captured through a safe API in this run; upload job counters and audit deltas were captured through read-only backend APIs after completion.

## 2. Approval Scope

- Approved action: Retry Failed exactly once for `upl_59575d0cbe67`.
- Source failed job: `upl_59575d0cbe67`.
- Original Preview reference: `prv_b9d2ab033ef4`.
- PR #161 merge commit: `089912b2d7e46d32927d2e3399ecfd2df9c35f04`.
- Upload Preview: not executed.
- Start Upload: not executed.
- Duplicate rerun: not executed.
- Authenticated manual Edge call: not executed.
- Full rollout: not executed.
- DB/Supabase/Docker destructive or lifecycle work: not executed.

## 3. Preflight Evidence

| Gate | Result |
|------|--------|
| `main == origin/main` | passed |
| Merged code includes PR #161 duplicate-safe upload path | passed |
| Backend health | ok |
| Backend launched with operator/launcher environment | passed |
| Source class | approved mapped-drive/local-drive class |
| Source accessibility | accessible |
| Source CSV count class | positive |
| Target class preflight | passed |
| Runtime API | ready |
| Runtime DB | ready |
| Runtime Studio | ready |
| Runtime Edge | ready |
| Edge no-auth GET | auth-class |
| Edge no-auth POST `{}` | auth-class |
| Latest Preview used for execution | no, explicit job id only |

Non-core runtime caveat: Grafana remained unreachable. This did not block upload retry because API, DB, Studio, and Edge runtime gates were ready.

## 4. Source Failed Job State

| Field | Value |
|-------|-------|
| Job id | `upl_59575d0cbe67` |
| Status before retry | `failed` |
| Preview run id | `prv_b9d2ab033ef4` |
| Processed rows | `2000` |
| Uploaded rows | `2000` |
| Accepted rows | `2000` |
| Row count | `863823` |
| Failed file count | `1` |
| Resume offset | `2000` |

The failed job was retryable because it had one failed file and a preserved physical resume offset after the first 2000 rows.

## 5. Retry Execution Result

| Field | Value |
|-------|-------|
| Retry POST count | `1` |
| Retry POST result | `202 Accepted` |
| New retry job id | `upl_37b3da37b85d` |
| Retry of job id | `upl_59575d0cbe67` |
| Final status | `succeeded` |
| Processed rows | `863823` |
| Uploaded rows | `861420` |
| Accepted rows | `861420` |
| Failed files | `0` |
| Succeeded files | `1` |
| Active files after completion | `0` |
| Active upload jobs after completion | `0` |

Counter interpretation:

- `processedRows` is physical source progress and includes the preserved resume offset.
- `uploadedRows` and `acceptedRows` are deduplicated rows sent to and accepted by the Edge/Postgres path during the retry job.
- Original failed job accepted `2000` rows before failing.

## 6. Deduplication Evidence

| Metric | Value |
|--------|-------|
| `file.deduplicated` events fetched | `268` |
| Duplicate rows collapsed during retry | `403` |
| Dedupe input rows total across affected batches | `535823` |
| Dedupe output rows total across affected batches | `535420` |
| First dedupe processed row marker | `4000` |
| Last dedupe processed row marker | `863823` |

The dedupe events show that the PR #161 upload path was active during retry and collapsed duplicate `(timestamp, device_id)` keys before Edge upsert.

## 7. Audit And Mutation Guard

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Upload retry audit count in read window | `2` | `3` | `+1` |
| Upload start audit count in read window | `11` | `11` | `0` |
| Upload job count in read window | `12` | `13` | `+1` |
| Active upload job count after completion | `0` | `0` | `0` |

No additional Preview, Start Upload, duplicate rerun, or second Retry was executed.

## 8. Caveats

- Direct DB row-count delta was not captured through a safe read-only API during this execution.
- Latest Preview remained non-authoritative and was not used for execution decisions.
- The source failed job remains `failed`; the successful evidence is the retry job `upl_37b3da37b85d`.

## 9. Next Action

Review and merge this docs-only acceptance summary. Further upload, retry, or Preview work requires a new explicit gate and approval.
