# Operator Stage 3 Bounded Acceptance Review

Date: 2026-06-13 Asia/Seoul

## Verdict

`passed_with_caveats`

Stage 3 Profile A bounded batch evidence is acceptable as bounded-batch
acceptance evidence. It is not full rollout approval.

Core gates passed: source eligibility, bounded full-scan Preview, DB reachability,
single Start Upload execution, upload job success, exact DB delta reconciliation,
audit/job event evidence, and redaction controls.

The remaining caveats are process and interpretation caveats, not core upload
blockers.

## Acceptance Basis

| Gate | Result |
| --- | --- |
| Stage 3 source scope | `batch_bounded` |
| Profile | Profile A |
| Source eligibility | passed |
| File count bound `1-3` | passed, `1` |
| Physical row bound `1-25000` | passed, `24515` |
| Filename-date metadata | preserved |
| `file_date_missing` | `0` |
| Preview profile | `stage3_profile_a_bounded_full_scan` |
| Preview final status | `succeeded` |
| Preview `dbStatus` | `reachable` |
| Preview target files | `1` |
| Preview upload target exact keys | `21333` |
| Preview risky/excluded/failed/invalid evidence | `0` |
| Start Upload execution count | `1` |
| Upload job final status | `succeeded` |
| Upload job failed files | `0` |
| Warning count | `0` |
| DB delta tolerance | exact, `0` tolerance |
| DB delta | `21333` |
| Expected net-new exact keys | `21333` |
| DB delta matched expected | yes |
| Exact-key presence after upload | complete |
| Retry Failed | `0` |
| Duplicate rerun | `0` |
| Additional Preview after approved run | `0` |
| Full operational dataset rollout | not performed |

## Evidence Chain Summary

| Evidence | Finding |
| --- | --- |
| `docs/82_operator_stage_3_bounded_rollout_plan.md` | Defines Profile A bounds, DB delta rule, stop conditions, and full rollout separation. |
| `docs/88_operator_stage_3_source_eligibility_precheck_rerun.md` | Confirms the corrected bounded source passed file, row, and file-date eligibility. |
| `docs/89_operator_stage_3_bounded_preview_rerun_2.md` | Confirms an earlier Preview-only rerun passed with DB delta `0`, but predates the later exact-key clarification. |
| `docs/96_operator_stage_3_preview_timeout_profile.md` | Adds the explicit bounded full-scan Preview profile used for the corrected source. |
| PR `#112` artifact | Contains the corrected Preview reference recovery rerun report, but remains open and is not currently merged into `main`. |
| `docs/98_operator_stage_3_bounded_start_upload_rerun_2.md` | Records the accepted Start Upload evidence and embeds the latest corrected Preview reference confirmation. |

## Count Reconciliation

| Count | Value | Acceptance interpretation |
| --- | ---: | --- |
| Physical source rows | `24515` | Source-size and upload-job physical-row counter. |
| Preview local exact-key count | `21333` | Transformed exact-key target basis. |
| Direct DB exact-key matches before Start Upload | `0` | Confirms expected net-new exact keys. |
| Expected net-new exact keys | `21333` | DB delta expectation. |
| Job processed rows | `24515` | Physical rows processed by upload job. |
| Job uploaded rows | `24515` | Physical rows sent through the upload path. |
| Job accepted rows | `24515` | Physical rows accepted by the upload path. |
| DB row-count delta | `21333` | Net-new exact keys inserted into DB. |
| Exact-key presence after upload | `21333` | Complete exact-key reconciliation. |

The physical row counters and DB delta are intentionally different measures.
Acceptance should use the transformed exact-key count for DB delta, while keeping
the physical counters as upload-job throughput evidence.

## Caveats

| Caveat | Classification | Acceptance impact |
| --- | --- | --- |
| The corrected Preview rerun report from PR `#112` is still open and not merged into `main`. | Process caveat | Non-blocking for this review because `docs/98` records the same latest Preview reference confirmation used for Start Upload. Merge or close PR `#112` separately to keep document history tidy. |
| `docs/89` predates the explicit timeout profile and exact-key clarification. | Superseded evidence caveat | Non-blocking. Use `docs/96`, PR `#112`, and `docs/98` for the final exact-key interpretation. |
| Physical rows `24515` differ from DB delta `21333`. | Expected count interpretation caveat | Non-blocking. The DB delta matched expected net-new exact keys exactly. |
| Grafana readiness was non-core attention in the Start Upload evidence. | Non-core runtime caveat | Non-blocking. API, DB, Studio, and Edge were ready for the upload path. |

## Full Rollout Go/No-Go

| Question | Answer |
| --- | --- |
| Can this bounded batch be accepted as Stage 3 Profile A evidence? | yes, with caveats |
| Does this approve Stage 4 full rollout? | no |
| Can Profile B or Stage 4 planning begin? | yes, as a separate review/plan |
| Can another upload action run from this PR? | no |
| Is a separate explicit approval required before full rollout? | yes |

This PR must not be treated as full rollout approval. It only accepts one
bounded Profile A batch as evidence that the bounded flow can work under the
documented constraints.

## Required Next Approval

Before Stage 4 full rollout, require a separate PR or operator approval record
that explicitly confirms:

- whether to run Stage 3 Profile B first or move to Stage 4 planning;
- the proposed source scope and row/file bounds;
- DB/Edge target class alignment;
- expected net-new exact-key count and DB delta rule;
- rollback and stop conditions;
- redaction requirements;
- no destructive DB, Docker, or Supabase cleanup as a recovery shortcut.

If this review is merged, the next branch should be separate and should not
reuse this documentation branch for upload actions. The next branch should cover
either Stage 3 Profile B planning/QA or Stage 4 full rollout planning/review.

## Redaction Result

This report uses only sanitized source labels and aggregate counts. It does not
include credential material, operational source locator details, source names,
source row content, or raw connection material.

## Review Conclusion

Stage 3 Profile A bounded batch evidence is acceptable as
`passed_with_caveats`.

The accepted evidence is:

- bounded source eligibility passed;
- corrected bounded full-scan Preview passed with `dbStatus=reachable`;
- Start Upload ran exactly once;
- upload job succeeded;
- DB delta matched expected net-new exact keys exactly;
- no Retry Failed, duplicate rerun, additional Preview after approved run, or
  full rollout was performed.

Full rollout remains blocked until separately approved.
