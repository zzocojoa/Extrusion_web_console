# Operator Stage 3 Source Eligibility Investigation

## Summary

- Date: 2026-06-12
- Branch: `codex/operator-stage-3-source-eligibility-investigation`
- Base branch: `codex/operator-stage-3-source-eligibility-precheck`
- Base commit: `2b5a755b9a170d1a43f8929ba65bcb31be7d30e3`
- Investigation mode: root-cause plus report-only QA
- Stage: Stage 3 Profile A source eligibility, before Preview rerun
- Sanitized source label: `profile_a_bounded_source_precheck`
- Upload Preview executions: `0`
- Start Upload executions: `0`
- Duplicate rerun executions: `0`
- Edge authenticated upload calls: `0`
- Full operational dataset rollout: not performed
- Current configured source verdict: `blocked`
- Corrected source selection verdict: `passed`

The `file_date_missing=2` result in PR #101 is not caused by the official
integrated PLC filename pattern. The parser accepts the official integrated PLC
pattern and the legacy PLC pattern.

The failure is in source preparation or source selection. The configured source
contains one basename-preserved file and two staged or renamed files whose
basenames no longer carry Preview-readable PLC date metadata.

## Explicitly Not Performed

- feature code, launcher, backend, frontend, or packaging script edits;
- Upload Preview;
- Upload Start;
- duplicate rerun or forced duplicate upload;
- Edge authenticated upload call;
- full operational dataset rollout;
- Supabase init, bootstrap, reset, start, or stop;
- DB migration, reset, delete, cleanup, prune, drop, or truncate;
- Docker volume, container, image, or network deletion;
- operational source mutation, deletion, or rename;
- production deploy;
- GitHub Release or tag creation;
- feature branch deletion.

## Parser Rule Confirmation

The current parser path is `backend/app/services/upload_preview.py`.

For `plc` source kind:

- `CandidateScanner.scan()` enumerates configured CSV files.
- It calls `parse_plc_file_date(entry.name)`.
- It uses only the basename, not directory names or file content.
- If parsing returns no date, the file is excluded as
  `file_date_missing` before CSV key extraction.

Confirmed parser behavior:

| Pattern class | Parser result |
| --- | --- |
| Official integrated PLC pattern | passed |
| Legacy PLC prefix pattern | passed |
| Renamed/staged PLC copy without supported date metadata | `file_date_missing` |
| CSV row timestamp only | does not rescue filename-date failure |

This means a correctly preserved integrated PLC basename is eligible. The
blocked result is not evidence that the official filename pattern is wrong.

## PR #101 Configured Source Recheck

The PR #101 configured source was rechecked read-only with sanitized file
indices only.

| Check | Result |
| --- | --- |
| Source class count | `1` |
| Source kind class | `plc` |
| File count | `3` |
| Row count status | `counted` |
| Row count | `20223` |
| Eligible file count | `1` |
| Ineligible file count | `2` |
| `file_date_missing` count | `2` |
| Profile A file bounds | passed |
| Profile A row bounds | passed |
| Current configured source verdict | `blocked` |

Sanitized per-file result:

| File index | Eligibility | Reason class | Pattern feature class | Row count |
| --- | --- | --- | --- | ---: |
| `file_1` | `eligible` | `filename_date_present` | integrated stem plus compact date present | `20219` |
| `file_2` | `ineligible` | `file_date_missing` | no integrated stem/date, no legacy prefix, no compact date token | `2` |
| `file_3` | `ineligible` | `file_date_missing` | no integrated stem/date, no legacy prefix, no compact date token | `2` |

Root cause: the configured source includes two files whose basename metadata was
damaged or replaced during staged source preparation, or the source selection
included files that were not part of the corrected basename-preserved set.

The source kind was not the cause. The source was interpreted as `plc`, which is
the expected parser class for integrated PLC files.

## Corrected Bounded Source Precheck

The corrected source selection was evaluated read-only as the basename-preserved
eligible set from the configured source. No files were copied, renamed, deleted,
or modified.

| Check | Result |
| --- | --- |
| Corrected source class | `basename_preserved_eligible_selection` |
| Source kind class | `plc` |
| Corrected file count | `1` |
| Corrected row count status | `counted` |
| Corrected row count | `20219` |
| Eligible file count | `1` |
| Ineligible file count | `0` |
| `file_date_missing` count | `0` |
| Profile A file bounds | passed |
| Profile A row bounds | passed |
| Corrected source selection verdict | `passed` |

The corrected selection passes the Stage 3 source eligibility gate because all
selected files preserve parser-readable filename-date metadata.

Important operational caveat: the currently configured source folder still
contains the two ineligible files. A Preview rerun is allowed only after the
runtime source is prepared or selected so that it contains the corrected
basename-preserved set only.

## Cause Classification

| Candidate cause | Result | Evidence |
| --- | --- | --- |
| Official integrated filename pattern is rejected | no | Parser probe passed. |
| Source kind was interpreted as non-PLC | no | Source kind class was `plc`. |
| Configured source had only one basename-preserved file | yes | `file_1` eligible, `file_2` and `file_3` ineligible. |
| Staging or replacement damaged basenames | likely | Ineligible files had no supported date metadata class. |
| Configured source differed from intended corrected set | likely | Corrected eligible-only selection passed. |

## Stage 3 Preview Rerun Go/No-Go

| Source | Preview rerun decision |
| --- | --- |
| Current configured source from PR #101 | no-go |
| Corrected basename-preserved selection | go, after runtime source is prepared to include only that corrected set |

The next Preview-only rerun must not use the full current configured folder.
It must use a corrected bounded source whose files all satisfy one of the
supported PLC filename-date rules.

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

## Validation

| Command or check | Result |
| --- | --- |
| Parser official integrated pattern probe | passed |
| Parser legacy PLC pattern probe | passed |
| Current configured source sanitized recheck | `blocked` |
| Corrected source selection sanitized precheck | `passed` |
| Upload Preview execution count | `0` |
| Start Upload execution count | `0` |
| Duplicate rerun execution count | `0` |
| Edge authenticated upload calls | `0` |

## Next Step

Prepare the runtime source so it points only at the corrected
basename-preserved bounded set. Then run one Stage 3 Profile A Preview-only QA
on branch:

```text
codex/operator-stage-3-bounded-preview-rerun-2
```

Do not run Preview against the current configured folder while the two
`file_date_missing` files remain in scope.
