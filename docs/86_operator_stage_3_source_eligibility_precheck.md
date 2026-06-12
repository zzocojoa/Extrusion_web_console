# Operator Stage 3 Source Eligibility Precheck

## Summary

- Date: 2026-06-12
- Branch: `codex/operator-stage-3-source-eligibility-precheck`
- Base commit: `4979cf7d94e070d35cef62b7892f17bf3ef360c5`
- QA mode: report-only, read-only source eligibility precheck
- Stage: Stage 3 Profile A, before Preview rerun
- Sanitized source label: `profile_a_bounded_source_precheck`
- Source scope class: `batch_bounded`
- Source kind class: `plc`
- Upload Preview executions: `0`
- Start Upload executions: `0`
- Duplicate rerun executions: `0`
- Edge authenticated upload calls: `0`
- Full operational dataset rollout: not performed
- Verdict: `blocked`

The configured Profile A candidate source stayed within the Profile A file and
row count bounds, but it did not pass filename-date eligibility. Two candidate
files would be excluded as `file_date_missing` before CSV key extraction.

Per `docs/82_operator_stage_3_bounded_rollout_plan.md`, Preview must not be
rerun from this source. Replace the bounded source with files whose basenames
preserve the supported Preview file-date metadata.

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
- operational source mutation or deletion;
- production deploy;
- GitHub Release or tag creation;
- feature branch deletion.

## Precheck Method

The precheck used the same filename-date parser rules documented in
`docs/82_operator_stage_3_bounded_rollout_plan.md` and covered by
`tests/backend/test_upload_preview_file_date_rules.py`.

No Upload Preview API, Supabase runtime command, DB connection, Edge call,
Docker command, or upload execution path was used.

The precheck recorded only:

- sanitized source label;
- source scope class;
- source kind class;
- file count;
- row count;
- eligible and ineligible counts;
- safe reason class counts;
- Profile A gate result.

Raw source paths, raw source filenames, source content, row content, full local
paths, DB URLs, tokens, Authorization headers, and JWT values are not recorded.

## Source Scope Result

| Check | Result |
| --- | --- |
| Sanitized source label | `profile_a_bounded_source_precheck` |
| Source scope class | `batch_bounded` |
| Source kind class | `plc` |
| Configured source class count | `1` |
| Source scope clarity | clear |
| File count | `3` |
| Row count status | `counted` |
| Row count | `20223` |
| Profile A file range `1-3` | passed |
| Profile A row range `1-25000` | passed |
| Full operational dataset used | no |
| Operational source modified | no |

The row count is a safe physical data-line count for the bounded source. It is
not a transformed exact-key count and was not derived from Upload Preview.

## Filename-Date Eligibility Result

| Item class | Count | Reason class |
| --- | ---: | --- |
| `eligible` | `1` | `filename_date_present` |
| `ineligible` | `2` | `file_date_missing` |

| Gate | Result |
| --- | --- |
| Eligible file count equals total file count | blocked |
| Ineligible file count | `2` |
| `file_date_missing` count | `2` |
| Expected excluded files before Preview | `0` |
| Raw path/name/content exposure risk observed | no |

## Stop Condition

| Stop condition | Result |
| --- | --- |
| ineligible file count greater than `0` | triggered |
| `file_date_missing` greater than `0` | triggered |
| source scope unclear | not triggered |
| Profile A file bounds exceeded | not triggered |
| Profile A row bounds exceeded | not triggered |
| raw path, filename, content, or secret exposure risk | not triggered |

The stop condition is deterministic and occurs before Preview. The source would
repeat the same exclusion class already investigated in
`docs/85_stage_3_file_date_metadata_investigation.md`.

## Stage 3 Preview Rerun Go/No-Go

| Question | Answer |
| --- | --- |
| Does the source meet Profile A file bounds? | yes |
| Does the source meet Profile A row bounds? | yes |
| Do all files preserve filename-date metadata? | no |
| Is `file_date_missing` count `0`? | no |
| Is Upload Preview rerun allowed from this source? | no |
| Is Start Upload allowed from this source? | no |

Next safe action: do not run Preview. Prepare a replacement bounded Profile A
source whose basenames satisfy the configured filename-date parser rules, then
repeat this read-only eligibility precheck before any Preview rerun.

## Documentation Caveat

`docs/84_operator_stage_3_bounded_preview_rerun.md` was requested as prior
context, but it is not present in the current `main` worktree. This precheck
therefore used `docs/83_operator_stage_3_bounded_preview.md`,
`docs/85_stage_3_file_date_metadata_investigation.md`, and the merged Stage 3
plan in `docs/82_operator_stage_3_bounded_rollout_plan.md` as the authoritative
current-state evidence.

## Validation

| Command or check | Result |
| --- | --- |
| Read-only source eligibility precheck | `blocked` |
| Upload Preview execution count | `0` |
| Start Upload execution count | `0` |
| Duplicate rerun execution count | `0` |
| Edge authenticated upload calls | `0` |
| Source file count | `3` |
| Source row count | `20223` |
| Eligible file count | `1` |
| Ineligible file count | `2` |
| `file_date_missing` count | `2` |
| Profile A file bounds | passed |
| Profile A row bounds | passed |

## Merge Readiness For This QA Report

This QA report PR is merge-ready when:

- the PR centers on `docs/86_operator_stage_3_source_eligibility_precheck.md`;
- targeted file-date and Upload Preview reconciliation tests pass;
- expanded Upload Preview backend tests pass when feasible;
- `git diff --check` passes;
- marker scan finds no raw secret, DB URL, token, Authorization header, JWT,
  operational source path, operational source filename, row content, full local
  path, or package output artifact marker;
- untracked `docs/.pdca-status.json`, `docs/assets/`, operational fixtures,
  `.gstack`, `frontend/dist`, and package output artifacts are not staged;
- no Upload Preview, Upload Start, duplicate rerun, Edge authenticated upload
  call, full operational dataset rollout, Supabase destructive command, DB
  mutation command, Docker delete, production deploy, Release, or tag operation
  was run.
