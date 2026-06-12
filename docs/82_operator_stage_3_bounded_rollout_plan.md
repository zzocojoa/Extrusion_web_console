# Operator Stage 3 Bounded Rollout Plan

## Summary

- Date: 2026-06-12
- Branch: `codex/operator-stage-3-bounded-rollout-plan`
- Base commit: `5394ff6330bd5452305a8797a736665684466d81`
- PDCA phase: Plan
- Scope: documentation-only Stage 3 rollout plan
- Rollout status: `plan_ready_with_caveats`

This plan defines the gate between the accepted Stage 1/2 bounded smoke and any
broader operational rollout. It does not execute Upload Preview, Start Upload,
duplicate rerun, Edge authenticated upload, Supabase runtime commands, DB
changes, Docker cleanup, or full operational dataset rollout.

Stage 2 proved that one operator-approved bounded temp sample could complete
Preview and one Start Upload against the independent `Extrusion_web_console`
stack. That evidence is useful, but it is not full rollout evidence.

## Purpose

Stage 3 is a day-bounded or batch-bounded rollout stage. Its purpose is to
expand from the Stage 2 sample into controlled operational batches while keeping
review, stop, and rollback decisions small enough to reason about.

Stage 3 must not be interpreted as:

- full operational dataset approval;
- production deploy approval;
- GitHub Release or tag approval;
- permission to chain multiple batches automatically;
- permission to reset, delete, prune, or destructively clean DB or Docker state.

The Stage 2 result of `20219` accepted rows remains bounded sample evidence
only. It does not prove that a full operational dataset will be safe, fast, or
operationally acceptable.

## Stage 3 Scope Definition

Stage 3 can use one of two bounded scopes:

| Scope class | Definition | Approval requirement |
| --- | --- | --- |
| `day_bounded` | One operator-approved operational day or a smaller subset of one day. | Operator confirms the day class, expected file count, and expected row range before Preview. |
| `batch_bounded` | One operator-approved batch assembled from operational files. | Operator confirms the batch label, file count, row range, and exclusion rules before Preview. |

Required source rules:

- record only a sanitized source label;
- do not record raw source path, source filename, source content, row content, or
  full local path;
- preserve source filename date metadata through any temp copy or staging step;
- run the source eligibility precheck below before requesting Preview;
- use one approved source scope per PR;
- do not mix independent evidence with legacy fallback evidence;
- do not auto-select the next day or next batch;
- require operator approval before each batch and after each batch.

Allowed Stage 3 evidence:

- source class;
- sanitized source label;
- file count;
- row count;
- status class;
- target class;
- DB delta;
- exact-key count class;
- audit/log redaction result;
- caveat class.

## Source Eligibility Precheck

Run this precheck before any Stage 3 Preview-only run. The precheck is
read-only and must not call Upload Preview, Start Upload, duplicate rerun, Edge
authenticated upload, DB mutation commands, Supabase start/stop/reset, or Docker
cleanup.

File-date eligibility is based on the source filename only:

- PLC integrated files must preserve the configured integrated PLC stem followed
  by `_YYYYMMDD`.
- PLC legacy files must start with `YYMMDD`.
- Temperature files must contain `YYYY-MM-DD`.

The Preview scanner does not infer file date from directory names, filesystem
mtime, CSV headers, CSV row timestamps, config records, or source labels. If a
temp copy renames a file so the supported date metadata is no longer present in
the basename, Preview will classify it as `excluded/file_date_missing` before
CSV key extraction begins.

The precheck output must record only:

- sanitized source label;
- source class;
- file count;
- row count if counted safely;
- eligible file count;
- ineligible file count;
- reason class counts such as `file_date_missing`;
- whether all files satisfy the selected Profile A/B bounds.

If any file is ineligible and the exclusion was not explicitly approved before
Preview, stop and replace the bounded source. Do not blind rerun Preview.

## Numeric Gates

Stage 3 uses two numeric profiles. Start with Profile A. Profile B requires a
separate approval after Profile A evidence is reviewed.

| Gate | Profile A: first Stage 3 batch | Profile B: later Stage 3 batch |
| --- | --- | --- |
| Expected file count range | `1-3` files | `1-10` files |
| Expected row count range | `1-25000` rows | `1-100000` rows |
| Max allowed target files | `3` | `10` |
| Max allowed target rows | `25000` | `100000` |
| Preview `dbStatus` | must be `reachable` | must be `reachable` |
| Preview DB delta | must be `0` | must be `0` |
| Start Upload executions | exactly `1` for the approved batch | exactly `1` for the approved batch |
| DB delta tolerance | exact, `0` tolerance from expected net-new transformed exact keys | exact, `0` tolerance from expected net-new transformed exact keys |
| Failed files | `0` | `0` unless separately approved before upload |
| Invalid rows | `0` | `0` unless separately approved before upload |
| Risky files | `0` | `0` |
| Partial-overlap files | `0` | `0` |
| Excluded files | `0` unless expected and operator-approved before upload | `0` unless expected and operator-approved before upload |
| Upload job failed files | `0` | `0` |
| Upload warning count | `0` or explained non-blocking warning class | `0` or explained non-blocking warning class |

DB delta rule:

```text
actual DB row-count delta == expected net-new transformed exact-key count
```

Tolerance is intentionally `0`. If the delta differs, stop. Do not repair by
deleting rows, resetting the DB, pruning Docker, or forcing a duplicate rerun.

Already-in-DB and duplicate behavior:

- Preview should classify already represented exact keys as `already_in_db`.
- Already-in-DB rows must not become upload targets by default.
- If upload-target count is `0`, do not run Start Upload.
- If duplicate-safe evidence is needed, use normal-flow Preview exclusion
  evidence, not forced duplicate upload.
- A duplicate rerun is outside Stage 3 unless a separate PR explicitly approves
  it.

Exceeding a numeric gate does not mean the data is bad. It means the batch is
too broad for the current approval. Split it into a smaller batch and restart at
Preview-only.

## Preview Timeout Profile Requirement

Stage 3 Profile A full-scan Preview must use the explicit
`stage3_profile_a_bounded_full_scan` Preview option profile:

| Option | Required Profile A value |
| --- | ---: |
| `profile` | `stage3_profile_a_bounded_full_scan` |
| `forceFullScan` | `true` |
| `maxFiles` | `3` |
| `maxRunSeconds` | `300` |
| `maxFileSeconds` | `120` |

This profile exists only for operator-approved Stage 3 Profile A bounded
Preview. It must not be treated as a default Preview profile and must not be
used to broaden a full operational dataset rollout. The source eligibility
precheck and Profile A numeric gates still apply before and after Preview.

If a Stage 3 Profile A Preview times out with the default `30` second per-file
budget, stop and update the procedure or code path before any rerun. Do not
repair the evidence by running a second Preview, Start Upload, Retry Failed,
duplicate rerun, or full rollout in the same PR.

## Stage 3 Execution Sequence

Each Stage 3 batch must follow this exact sequence.

1. Fresh runtime preflight

   - confirm independent API, DB, Studio, and Edge are reachable;
   - confirm no-auth Edge `GET` and `POST {}` are auth-class, not `503`;
   - confirm DB and Edge target classes are both independent;
   - confirm package-local runtime core readiness;
   - record vector and Grafana caveats separately from core readiness.

2. Source scope confirmation

   - record the sanitized source label;
   - record source class: `day_bounded` or `batch_bounded`;
   - record expected file count range and expected row count range;
   - operator confirms this is not full operational dataset rollout.

3. Preview-only first

   - run one Preview for the approved source scope;
   - require `dbStatus=reachable`;
   - record total file count, target file count, already-in-db count,
     excluded count, risky count, partial-overlap count, failed count, invalid
     count, upload-row estimate, and DB matched rows;
   - confirm Preview DB row-count delta is `0`.

4. Operator count confirmation

   - compare Preview counts against the selected numeric profile;
   - if target files or target rows exceed the profile limit, stop;
   - if failed, invalid, risky, or unexpected excluded counts appear, stop;
   - operator explicitly approves or rejects Start Upload for this batch.

5. Start Upload, one bounded batch only

   - run Start Upload exactly once;
   - do not run Retry Failed, duplicate rerun, or a second batch in the same QA
     PR;
   - record upload job status, total files, succeeded files, failed files,
     processed rows, uploaded rows, accepted rows, and warning count.

6. DB and exact-key verification

   - record DB row-count before Preview, after Preview, and after Upload;
   - compute expected net-new transformed exact-key count;
   - require DB delta to match the expected net-new exact-key count with `0`
     tolerance;
   - record exact-key presence as complete, partial, or blocked.

7. Audit, job events, SSE, and log review

   - inspect audit and job event evidence read-only;
   - use SSE replay if applicable;
   - record only sanitized status classes and counts;
   - scan evidence for redaction failures.

8. Stop after one batch

   - do not auto-advance to another batch;
   - write a Stage 3 QA report;
   - require review and merge of that report before any next batch.

## Stop Conditions

Stop immediately if any condition is true:

| Stop condition | Required action |
| --- | --- |
| Edge no-auth route returns `503`, timeout, or server-class status | Stop before Preview or Upload. |
| DB target class is not independent | Stop and investigate config. |
| Edge target class is not independent | Stop and investigate config. |
| DB and Edge targets are mismatched | Stop and investigate config. |
| Package-local runtime core API, DB, Studio, or Edge is not ready | Stop before Preview. |
| Preview `dbStatus` is not `reachable` | Stop. No Start Upload from that Preview. |
| Preview target files exceed the selected profile maximum | Stop and split the batch. |
| Preview target rows exceed the selected profile maximum | Stop and split the batch. |
| Failed or invalid counts exceed `0` without pre-approval | Stop and record failure class. |
| Risky or partial-overlap files appear | Stop and investigate before upload. |
| Excluded count is unexpected | Stop and require operator confirmation. |
| DB delta after Preview is not `0` | Stop and investigate mutation source. |
| DB delta after Upload differs from expected net-new exact-key count | Stop and capture evidence. |
| Upload job has failed files | Stop. Do not run Retry Failed in the same PR. |
| Raw secret, DB URL, token, Authorization header, JWT, source path, source filename, source content, row content, or full local path appears in evidence | Stop and redact before sharing or merging. |
| Docker or Supabase instability clouds the upload decision | Stop and run a separate recovery/investigation PR. |
| Operator cannot confirm source scope | Stop. Do not infer scope from local paths. |

## Rollback And Fallback

Rollback policy is non-destructive.

Forbidden without a separate explicit approval:

- DB reset, delete, cleanup, prune, drop, truncate, or destructive migration;
- Docker container, volume, image, or network deletion;
- Supabase init, bootstrap, reset, start, or stop during this planning step;
- AppData config, state, or log deletion;
- operational source modification or deletion;
- forced duplicate upload.

If Stage 3 fails:

1. stop the current batch;
2. capture sanitized Preview, Upload Job, DB delta, audit, job event, and
   runtime evidence;
3. do not start another batch;
4. do not clean up by deleting DB rows or Docker resources;
5. create a follow-up investigation or rollback plan if needed.

Uploaded-row rollback:

- is not part of normal Stage 3;
- requires separate explicit approval;
- must name the exact rollback scope without raw source paths or filenames;
- should prefer compensating evidence and isolation over destructive cleanup.

Legacy `Extrusion_data` fallback:

- is allowed only through explicit maintainer env/config override;
- must be labeled as fallback evidence;
- must not be mixed with independent Stage 3 evidence;
- must not mutate or delete independent runtime data.

## Acceptance Criteria

Stage 3 verdicts:

| Verdict | Criteria |
| --- | --- |
| `passed` | All runtime, target alignment, Preview, Upload, DB delta, exact-key, audit/log, and redaction gates pass with no unresolved caveats. |
| `passed_with_caveats` | Core Preview and Upload gates pass, DB delta and exact-key evidence match, and remaining caveats are non-core, documented, and accepted. |
| `blocked` | Any stop condition triggers, operator approval is missing, or evidence cannot prove the batch remained bounded. |

Stage 4 full rollout cannot begin until:

- at least one Stage 3 report is reviewed and merged;
- the report identifies the exact profile used and whether Profile B is allowed;
- all blocking caveats are resolved or explicitly accepted;
- a separate full rollout PR is approved by the operator acceptance owner.

Stage 3 success does not automatically approve Stage 4.

## Security And Redaction

Do not document, paste, screenshot, or commit:

- raw secret values;
- DB URLs or connection strings;
- local API token values;
- Authorization headers;
- JWT values;
- anon key or service role values;
- operational CSV paths;
- operational CSV filenames;
- operational CSV content;
- row contents;
- full local paths;
- generated Supabase credentials;
- raw Supabase status/start output;
- package output paths, zip names, or checksum contents.

Allowed report evidence:

- sanitized source label;
- source class;
- stage profile;
- status class;
- target class;
- file count;
- row count;
- DB delta;
- exact-key presence class;
- audit/log redaction result;
- vector and Grafana caveat class.

Any redaction failure blocks merge of the Stage 3 QA report until corrected.

## Next QA

Recommended next PR:

```text
codex/operator-stage-3-bounded-preview
```

Recommended next QA flow:

1. run Stage 3 Profile A Preview-only QA first;
2. record sanitized source label, file count, row count, and Preview counts;
3. stop if `dbStatus` is not `reachable` or counts exceed Profile A;
4. only after Preview review, run a separate Start Upload QA for the same
   approved batch;
5. do not run a second batch or full operational dataset rollout in that PR.

If the operator wants Preview and Start Upload in one PR, the PR must explicitly
state that Start Upload is conditional on the Preview gate and must still stop
after exactly one bounded batch.

## Merge Readiness For This Plan

This plan PR is merge-ready when:

- the PR includes only `docs/82_operator_stage_3_bounded_rollout_plan.md`;
- `git diff --check` passes;
- marker scan finds no raw secret, DB URL, token, Authorization header, JWT,
  operational source path, operational source filename, row content, full local
  path, package output, zip, or checksum marker;
- untracked `docs/assets/`, PNG, and operational fixtures are not staged;
- `.gstack`, `frontend/dist`, package output, zip, and checksum files are not
  staged;
- no Supabase, DB, Docker, Upload Preview, Start Upload, duplicate rerun, Edge
  authenticated call, full operational rollout, production deploy, Release, or
  tag operation was run.
