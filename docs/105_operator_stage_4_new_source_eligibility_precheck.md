# Operator Stage 4 New Source Eligibility Precheck

Date: 2026-06-13 Asia/Seoul

Branch: `codex/operator-stage-4-new-source-eligibility-precheck`

Scope: read-only Stage 4 source eligibility precheck

Verdict: `passed`

## Summary

The refreshed Stage 4 full operational source folder is accessible through the
approved backend/config path class. The folder now contains two operational CSV
files, both pass the official PLC filename-date parser, and no file has a zero
row count.

This precheck did not run Upload Preview, Start Upload, Retry Failed, duplicate
rerun, authenticated Edge upload call, full rollout, DB reset, DB init, DB
delete, DB truncate, DB drop, DB prune, Docker delete/prune, or Supabase
reset/start/stop.

## Source Scope

| Item | Result |
| --- | --- |
| Sanitized source label | `stage4-full-candidate-a-refreshed` |
| Source class | `full_operational_dataset_candidate` |
| Source kind | `plc` |
| Preferred path class | `unc_from_environment_or_config` |
| Human mapped path used in report | no |
| Raw source locator recorded | no |
| Raw source filename recorded | no |
| Raw source content opened | no |
| Source folder exists | yes |
| Source folder is directory | yes |

## Eligibility Results

| Check | Result |
| --- | ---: |
| File count | `2` |
| CSV file count | `2` |
| Filename-date eligible CSV count | `2` |
| `file_date_missing` | `0` |
| Parser failed count | `0` |
| Row count status | `counted` |
| Total physical source rows | `37398` |
| Minimum rows per CSV | `17179` |
| Maximum rows per CSV | `20219` |
| Zero-row files | `0` |
| Latest modified CSV parser check | passed |
| Latest modified CSV row-count check | positive |

The newly prepared operational CSV candidate is eligible for a separate Stage 4
Preview-only rerun from a source-shape standpoint. This document does not prove
DB reconciliation, upload target count, duplicate status, or Start Upload
readiness.

## Parser Basis

The precheck used the repository's official PLC filename-date parser from the
Upload Preview service. Accepted PLC patterns are the supported integrated stem
with compact date metadata or the supported legacy leading date pattern. Date
metadata was not inferred from directory names, file modification time, row
content, or operator labels.

## Stop Conditions

| Stop condition | Result |
| --- | --- |
| Source folder inaccessible | no |
| Source is not a directory | no |
| CSV file count is `0` | no |
| Any CSV fails filename-date parser | no |
| `file_date_missing > 0` | no |
| Any CSV has zero physical rows | no |
| Source scope unclear | no |

No stop condition was observed for source eligibility. Preview-only is still a
separate user-approved step and was not executed here.

## Redaction Result

This document records only sanitized source labels, source/path classes, and
aggregate counts.

- no raw source locator;
- no raw source filename;
- no source row content;
- no full local source path;
- no raw connection string;
- no credential or auth material;
- no destructive command output.

## Validation

| Check | Result |
| --- | --- |
| Upload Preview filename/date parser tests | `3 passed` |
| `git diff --check` | passed |
| New document marker scan | passed |
| Branch diff file scope | docs-only |

## Next Safe Action

If the user explicitly approves, proceed in a separate branch to Stage 4
Preview-only rerun using the approved source path class and refreshed source
scope.

Start Upload remains forbidden until Preview-only succeeds, counts are reviewed,
and the user separately approves exactly one Start Upload.
