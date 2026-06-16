# Gap Analysis: preview-filename-date-parser-fix

> Date: 2026-06-16 | Scope: Upload Preview filename-date eligibility gate

---

## Match Rate: 100%

## Summary

The latest Preview run `prv_4c512bab22ce` did not fail because the filename-date
parser is missing a newly approved operational pattern. It succeeded as a
metadata-only Preview, but all three files were excluded from upload targeting:
one parsed file was outside the requested `today` range, and two files had no
Preview-readable date metadata in their basenames.

The safe decision is **no parser fix** for file_2 and file_3. They should be
removed, replaced, or renamed upstream into a supported operational filename
pattern before another Preview-only run. Start Upload remains no-go.

## Investigation Result

| Check | Result |
| --- | --- |
| Current branch created | `codex/preview-filename-date-parser-fix` |
| Base sync | `main == origin/main` before branch creation |
| Latest Preview run | `prv_4c512bab22ce` |
| Latest Preview status | `succeeded` |
| Latest Preview `dbStatus` | `not_checked` |
| Latest Preview target files | `0` |
| Latest Preview upload target rows | `0` |
| Latest Preview excluded files | `3` |
| Upload Preview rerun during investigation | `0` |
| Start Upload during investigation | `0` |
| Retry Failed during investigation | `0` |
| Duplicate rerun during investigation | `0` |
| Full rollout during investigation | not performed |

## Parser Rules Confirmed

Current PLC Preview eligibility is intentionally filename-based.

| Supported PLC basename metadata | Status |
| --- | --- |
| Integrated operational stem followed by compact `YYYYMMDD` | accepted |
| Legacy leading `YYMMDD` prefix | accepted |
| Date only in directory, source label, mtime, or CSV row content | rejected |
| Generic staged/export basename without date metadata | rejected |

This matches the existing parser tests in
`tests/backend/test_upload_preview_file_date_rules.py` and the prior Stage 3
file-date investigation.

## Current Source Classification

The active source was inspected read-only through the backend config value. Raw
source locators, source filenames, and file contents were not recorded.

| File index | Parser result | Pattern feature class | Row class | Decision |
| --- | --- | --- | --- | --- |
| `file_1` | parsed | integrated stem plus compact date token | positive | valid filename metadata, but outside the requested `today` range |
| `file_2` | `file_date_missing` | no integrated stem, no leading legacy prefix, no compact date token, no ISO date token, no digit run | positive | source cleanup required |
| `file_3` | `file_date_missing` | no integrated stem, no leading legacy prefix, no compact date token, no ISO date token, no digit run | positive | source cleanup required |

The two failing files do not present a narrowly supportable official filename
pattern. There is no safe parser expansion to add because the basename does not
carry a date token at all.

## Root Cause Classification

| Candidate cause | Result | Evidence |
| --- | --- | --- |
| Official integrated filename pattern rejected | disproven | `file_1` parsed through the existing integrated pattern |
| Legacy leading date pattern rejected | disproven | existing regression test covers the supported legacy prefix |
| New official compact date pattern missing from parser | not supported | file_2/file_3 have no compact date token |
| Active source contains nonconforming staged/export files | supported | file_2/file_3 have no supported date metadata feature |
| Requested date range excluded all parseable files | partially supported | file_1 parsed, but falls outside `today=2026-06-16` |

Root cause: the current active source is not Preview-ready for the requested
date gate. It contains two positive-row CSVs whose basenames lack any
Preview-readable date metadata, plus one parseable file outside the requested
date range.

## 비개발자 설명

업로드 미리보기는 파일 안의 내용을 읽기 전에 먼저 파일 이름에서 날짜를 찾습니다. 지금 문제의 두 파일은 행 데이터는 있지만, 파일 이름 쪽에 날짜 단서가 없습니다.

그래서 코드를 억지로 넓히면 “날짜 없는 파일도 업로드 후보로 보자”가 됩니다. 그건 안전 장치를 약하게 만드는 변경입니다. 올바른 조치는 파일명을 정식 패턴으로 준비하거나, 해당 파일을 Preview 대상 source에서 빼는 것입니다.

## Decision

Verdict: `source_cleanup_required_no_parser_fix`

Parser fix PR is not appropriate for file_2/file_3 because no official
filename-date pattern can be inferred from the current sanitized basename
features. The source should be cleaned before another Preview-only run.

Required source cleanup options:

1. Replace file_2/file_3 with operational CSV files whose basenames preserve the
   supported integrated operational stem and compact date metadata.
2. Remove file_2/file_3 from the active Preview source if they are temporary,
   export, note, or staging artifacts.
3. If file_2/file_3 are official despite lacking date metadata, define and
   approve an explicit naming rule first. Do not infer dates from row content,
   mtime, parent folder, or operator labels.

## Next Preview Gate

A future Preview-only run is safe only after all of these are true:

| Gate | Required result |
| --- | --- |
| Active source class | approved operational source class |
| CSV count | reviewed and expected |
| `file_date_missing` precheck count | `0`, unless exclusions are explicitly approved |
| Date range | includes the intended file dates |
| Preview execution approval | separate explicit approval |
| Start Upload | still forbidden until Preview succeeds and target rows are reviewed |

For the current parseable file, the next Preview-only request also needs a
custom date range that includes its parsed date. Running `today` again will keep
target rows at `0`.

## Redaction Result

| Check | Result |
| --- | --- |
| Raw source path recorded | no |
| Raw source filename recorded | no |
| Raw source content recorded | no |
| Full local path recorded | no |
| DB URL recorded | no |
| Token, Authorization header, or JWT recorded | no |
| Secret recorded | no |

## Validation

Planned validation before PR:

- targeted filename-date parser tests;
- targeted Upload Preview file-date rule tests;
- `git diff --check`;
- marker scan for raw source path/name/content and secrets;
- latest Preview id unchanged;
- upload job count unchanged;
- upload.start audit count unchanged.

## Recommendations

1. Do not change `parse_plc_file_date()` for file_2/file_3.
2. Clean or replace the active source so every intended upload candidate has
   Preview-readable filename-date metadata.
3. After source cleanup, request a separate Preview-only run with a custom range
   that includes the intended file dates.
4. Review target rows from that Preview before any separate Start Upload
   approval.
