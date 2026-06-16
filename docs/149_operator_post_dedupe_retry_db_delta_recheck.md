# Operator Post-Dedupe Retry DB Delta Recheck

Date: 2026-06-16 Asia/Seoul

## 1. Summary

Verdict: `retry_success_db_delta_reconciled_with_minor_counter_caveat`

Match Rate: `99%`

This report reduces the remaining DB delta caveat from
`docs/146_operator_post_dedupe_retry_execution.md` by adding a direct read-only
`public.all_metrics` row-count check and reconciling it with:

- partial mutation evidence from `docs/145_operator_upload_edge_500_partial_investigation.md`;
- retry job counters from `docs/146_operator_post_dedupe_retry_execution.md`;
- upload job event dedupe totals;
- audit events around the failed start and retry window.

No upload action was executed for this recheck. This was read-only except for
creating this document.

## 2. Non-Developer Explanation

The earlier failed upload was not a clean failure. It inserted `2,000` rows, then
stopped.

The later retry succeeded. A direct DB count now shows that the database grew by
the expected full target amount when the partial insert and retry are counted
together.

The important detail: the upload job's `acceptedRows` counter is not the same as
"new physical rows added to the DB." It counts rows accepted by the Edge/Postgres
upsert path. If a row is accepted as an upsert but does not create a new physical
row, `acceptedRows` can be higher than the DB row-count increase.

So the operational interpretation is:

- the original failed job added `2,000` physical rows;
- the retry added `861,419` net-new physical rows;
- together they account for the approved `863,419` unique target rows;
- the retry job reported `861,420` accepted rows, which is one row higher than the
  physical retry delta, consistent with accepted/upsert semantics.

No further upload or retry is justified by this report.

## 3. Evidence Scope

| Item | Result |
| --- | --- |
| Branch | `codex/post-dedupe-retry-db-delta-recheck` |
| Main baseline | `7a9f8bcc27e4962a73b4e7751e53eba7ff8c3f76` |
| Source failed job | `upl_59575d0cbe67` |
| Retry job | `upl_37b3da37b85d` |
| State DB access | read-only |
| Direct DB count | read-only transaction |
| Upload Preview executed | no |
| Start Upload executed | no |
| Retry Failed executed | no |
| Duplicate rerun executed | no |
| Manual authenticated Edge call executed | no |
| Full rollout executed | no |
| DB/Supabase/Docker lifecycle or destructive work | no |
| Settings save | no |
| Operational source mutation | no |

## 4. Job Counter Evidence

### Source Failed Job

| Field | Value |
| --- | ---: |
| Job id | `upl_59575d0cbe67` |
| Mode | `preview_targets` |
| Final status | `failed` |
| Total files | `1` |
| Succeeded files | `0` |
| Failed files | `1` |
| Total physical rows | `863823` |
| Processed rows | `2000` |
| Uploaded rows | `2000` |
| Accepted rows | `2000` |
| Resume offset | `2000` |
| Failure class | `upload_failed` |

### Retry Job

| Field | Value |
| --- | ---: |
| Job id | `upl_37b3da37b85d` |
| Retry of | `upl_59575d0cbe67` |
| Mode | `retry_failed` |
| Final status | `succeeded` |
| Total files | `1` |
| Succeeded files | `1` |
| Failed files | `0` |
| Total physical rows | `863823` |
| Processed rows | `863823` |
| Uploaded rows | `861420` |
| Accepted rows | `861420` |

Interpretation:

- `processedRows` is physical file progress and includes the preserved resume
  offset.
- `uploadedRows` and `acceptedRows` are retry-job counters after duplicate-safe
  batching.
- `acceptedRows` is the Edge/Postgres upsert accepted count. It is not a direct
  physical DB insert count.

## 5. Dedupe Event Evidence

| Metric | Value |
| --- | ---: |
| `file.deduplicated` events | `268` |
| Duplicate rows collapsed during retry | `403` |
| Dedupe input rows | `535823` |
| Dedupe output rows | `535420` |
| First dedupe processed marker | `4000` |
| Last dedupe processed marker | `863823` |

The retry job used the duplicate-safe upload path. The dedupe event totals match
the evidence recorded in `docs/146`.

## 6. Audit Evidence

Read-only audit inspection for the relevant execution window showed:

| Audit action | Count |
| --- | ---: |
| `upload.start` | `1` |
| `upload.failed` | `1` |
| `upload.retry` | `1` |
| `upload.succeeded` | `1` |

Sequence:

1. `upload.start` created the failed source job.
2. `upload.failed` recorded the partial failure.
3. `upload.retry` created the retry job.
4. `upload.succeeded` recorded retry completion.

There was no additional upload start or retry in the inspected window.

## 7. DB Delta Recheck

| Metric | Value |
| --- | ---: |
| DB count before failed Start Upload, from `docs/145` | `1884281` |
| DB count after partial failed Start Upload, from `docs/145` | `1886281` |
| Partial DB delta, from `docs/145` | `2000` |
| Current direct read-only DB count | `2747700` |
| Total net-new physical rows since pre-upload baseline | `863419` |
| Retry net-new physical rows after partial insert | `861419` |
| Approved unique target rows from Preview evidence | `863419` |
| Retry accepted rows | `861420` |
| Difference between retry accepted rows and retry net-new DB rows | `1` |

Calculation:

- `2747700 - 1884281 = 863419`
- `2747700 - 1886281 = 861419`
- `2000 + 861419 = 863419`

This reconciles the full target at the physical DB row-count level.

The remaining one-row difference is not evidence of a missing upload. It is the
expected class of difference between accepted/upsert counters and physical
net-new row growth. A row can be accepted by the upsert path without increasing
the table count.

## 8. Root Cause Hypothesis

Root cause hypothesis:
`docs_146_missing_direct_db_delta_capture_left_success_evidence_underexplained`

The retry execution itself succeeded, but the report lacked a direct read-only DB
count after completion. That made the evidence rely too heavily on job counters.

The new direct count shows:

- the failed job's `+2000` partial insert remained present;
- the retry completed the remaining physical row growth;
- total physical row growth matches the approved unique target count;
- retry `acceptedRows` should remain documented as an upsert accepted counter,
  not a net-new insert counter.

## 9. Caveats

- This report does not perform row-level exact-key diffing.
- The one-row difference between retry `acceptedRows` and retry physical DB delta
  is explained by counter semantics, but not row-level attributed.
- Later Preview runs and read-only checks may change active state context, but
  they do not change the historical job evidence reconciled here.

## 10. Start Upload / Retry Readiness

| Action | Readiness | Reason |
| --- | --- | --- |
| Additional Retry Failed for `upl_37b3da37b85d` | NO-GO | retry already succeeded |
| Retry Failed for `upl_59575d0cbe67` again | NO-GO | successful retry already exists |
| Start Upload from old Preview | NO-GO | no new approved target count in this report |
| Additional Upload Preview | separate approval required | outside this recheck scope |
| DB reset | NO-GO | evidence supports preserved data, reset would destroy QA evidence |

## 11. Redaction Result

The report uses only sanitized job ids, aggregate counts, and target classes. It
does not record raw operational source locators, source content, connection
strings, private credentials, or authenticated request material.

## 12. Validation

| Check | Result |
| --- | --- |
| Current branch checked | passed |
| Source failed job read-only detail | passed |
| Retry job read-only detail | passed |
| Retry dedupe event aggregate | passed |
| Audit window read-only query | passed |
| Direct DB row-count query | passed |
| `acceptedRows` vs DB delta distinction | documented |
| Forbidden operations | not performed |
