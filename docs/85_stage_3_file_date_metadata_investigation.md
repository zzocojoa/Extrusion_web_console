# Stage 3 File-Date Metadata Investigation

## Summary

- Date: 2026-06-12
- Branch: `codex/stage-3-file-date-metadata-investigation`
- Investigation mode: root-cause, no runtime upload actions
- Scope: Upload Preview file-date metadata gate
- Result: root cause confirmed
- Runtime Preview executions: `0`
- Upload Start executions: `0`
- Duplicate rerun executions: `0`
- Edge authenticated upload calls: `0`
- Full operational dataset rollout: not performed

Two Stage 3 Profile A attempts stopped on the same gate:

- upload target count stayed `0`;
- excluded file count stayed `2`;
- excluded reason class was `file_date_missing`.

Root cause: Upload Preview does not infer file date from CSV content, directory
metadata, filesystem mtime, config records, or source labels. For candidate
eligibility, it parses file date from the source filename before CSV key
extraction begins. If a temp copy or replacement source changes the basename so
the supported date metadata is missing, the file is excluded as
`file_date_missing` even when CSV rows contain parseable timestamps.

## Investigation Questions

### 1. Where Preview Infers File Date

File date is inferred in `backend/app/services/upload_preview.py`:

- `CandidateScanner.scan()` iterates configured source folders.
- For PLC files, it calls `parse_plc_file_date(entry.name)`.
- For temperature files, it calls `parse_temperature_file_date(entry.name)`.
- If the parser returns `None`, scanner records
  `excluded/file_date_missing` and does not create a candidate.
- CSV parsing happens later in `CsvKeyExtractor.extract()`, only for candidates
  that already passed the filename date gate.

The scanner uses `entry.name`, not the full path. Directory names do not satisfy
the date gate.

### 2. Confirmed Filename Rules

The current rules are:

| Source kind | Accepted date metadata |
| --- | --- |
| PLC integrated | configured integrated PLC stem followed by `_YYYYMMDD` |
| PLC legacy | filename starts with `YYMMDD` |
| Temperature | filename contains `YYYY-MM-DD` |

Not accepted for PLC:

- `YYYY-MM-DD` date text without the integrated PLC stem;
- `YYYYMMDD` date text without the integrated PLC stem;
- `YYMMDD` that appears later in the basename rather than at the start;
- dates only in directory names;
- dates only in CSV headers or row values.

Invalid calendar dates return no file date.

### 3. Why Stage 2 Passed

The Stage 1/2 bounded smoke used one bounded temp sample whose filename date
metadata was preserved. That let `CandidateScanner` create one candidate, then
`CsvKeyExtractor` transformed the file into `20219` exact keys. Preview returned
one target file, no exclusions, no risky files, and `dbStatus=reachable`, so the
Stage 2 Start Upload gate could be approved for that single bounded sample.

The important point: Stage 2 did not pass because CSV row timestamps alone were
enough. It passed because the file reached CSV extraction after the filename
date gate had already succeeded.

### 4. Why The Stage 3 Sources Failed

The first Stage 3 Profile A report recorded:

- `3` total files;
- `1` already-in-db file;
- `0` upload-target files;
- `2` excluded files;
- excluded reason class `file_date_missing`.

The rerun report repeated the same shape:

- `3` total files;
- `1` file with preserved Preview file-date metadata;
- `2` files missing Preview file-date metadata;
- `0` upload-target files;
- excluded reason class `file_date_missing`.

This proves the replacement source did not fix the filename eligibility
problem. Two files still failed before CSV content could participate in exact-key
extraction or DB reconciliation.

### 5. Can Temp Copy Damage Metadata?

Yes. The code reads date metadata from the copied file basename. A temp copy that
preserves CSV content but renames the file into a generic Stage 3 label can
destroy Preview eligibility.

Safe temp copy rule:

- preserve the basename date metadata required by the parser;
- do not rely on parent folder dates;
- do not rely on filesystem modified time;
- do not rely on CSV row timestamps to rescue a renamed PLC file.

Reports still must use sanitized labels and counts only. Do not document raw
source paths or raw source filenames.

### 6. Preview-Only Dry-Run Check

Yes, Stage 3 can run a non-runtime eligibility precheck before Preview:

1. enumerate the approved bounded source folder read-only;
2. for each file basename, call the same parser used by Preview;
3. count eligible and ineligible files by safe reason class;
4. compare file count and optional row count with Profile A/B numeric gates;
5. stop if any file would become `file_date_missing` unless the exclusion was
   explicitly approved before Preview.

This precheck does not need DB access, Supabase runtime, Upload Preview, Upload
Start, Edge auth, or Docker operations.

### 7. Should Stage 3 Plan Add Eligibility Precheck?

Yes. `docs/82_operator_stage_3_bounded_rollout_plan.md` now adds a source
eligibility precheck before Preview. The plan explicitly says file-date
eligibility is filename-based and that blind reruns should stop when
`file_date_missing` repeats.

## Confirmed Root Cause

Root cause: Stage 3 source preparation preserved row content and file count but
did not preserve the filename date metadata required by the Upload Preview
candidate scanner for every file. The scanner therefore excluded two files as
`file_date_missing` before CSV extraction and DB reconciliation.

This is a process/eligibility gap, not a DB, Edge, Supabase, or upload execution
failure.

## Test Evidence Added

Added `tests/backend/test_upload_preview_file_date_rules.py`:

- verifies accepted PLC integrated and PLC legacy filename date patterns;
- verifies accepted temperature `YYYY-MM-DD` date pattern;
- verifies common renamed Stage 3 copy basenames fail PLC file-date parsing;
- verifies scanner does not infer PLC file date from CSV row content.

The new scanner test is intentionally non-runtime. It does not call Upload
Preview API, Supabase, DB, Edge, Docker, or Upload Start.

## Stage 3 Source Eligibility Precheck

Before the next Stage 3 Profile A Preview-only run, require this safe precheck:

| Gate | Required result |
| --- | --- |
| Source class | `day_bounded` or `batch_bounded` |
| Source label | sanitized only |
| File count | within Profile A `1-3` |
| Row count | within Profile A `1-25000` if counted |
| Filename date metadata | eligible for every file |
| `file_date_missing` precheck count | `0` |
| Expected excluded files | `0` unless approved before Preview |
| Raw source path/name/content in evidence | absent |

If the precheck finds `file_date_missing`, do not run Preview. Replace the
bounded source or explicitly approve the exclusion policy in a separate plan.

## Next Safe Rerun Criteria

The next Preview-only rerun is safe only when:

- all files pass the filename date metadata parser;
- temp copy preserves source basename date metadata;
- source remains Profile A bounded;
- operator confirms expected file and row counts;
- no raw source path, source filename, or row content is recorded;
- runtime preflight is still independent and aligned;
- no Upload Start is attempted until Preview returns target rows and no
  unexpected exclusions.

## Explicitly Not Performed

- Upload Preview API call;
- Upload Start;
- duplicate rerun;
- Edge authenticated upload call;
- full operational dataset rollout;
- Supabase init, bootstrap, reset, start, or stop;
- DB migration, reset, delete, cleanup, prune, drop, or truncate;
- Docker volume, container, image, or network deletion;
- operational source mutation or deletion;
- production deploy;
- GitHub Release or tag creation;
- feature branch deletion.

## Validation Plan

This investigation is ready for review when:

- relevant file-date parser and scanner tests pass;
- related Upload Preview reconciliation tests pass;
- `git diff --check` passes;
- new docs/tests marker scan finds no raw secret, DB URL, token,
  Authorization header, JWT, raw operational path, raw operational filename,
  row content, package output path, archive, or hash artifact;
- PR scope is limited to the investigation doc, Stage 3 plan precheck wording,
  and non-runtime unit tests.
