# Operator Stage 4 Full Rollout Plan Review

Date: 2026-06-13 Asia/Seoul

## Match Rate Criteria

Verdict: `plan_ready_with_caveats`

Stage 4 is not approved for execution by this document.

This plan review defines the approval criteria for a future full operational
dataset rollout. It does not run Upload Preview, Start Upload, Retry Failed,
duplicate rerun, Edge upload calls, Supabase runtime commands, DB maintenance,
Docker cleanup, production deploy, Release, or tag work.

Match rate for this planning step is based on document coverage, not execution:

| Required planning item | Covered |
| --- | --- |
| Stage 4 objective | yes |
| Stage 4 prerequisites | yes |
| Source scope confirmation | yes |
| Preview-only gate | yes |
| Start Upload gate | yes |
| DB delta and exact-key acceptance criteria | yes |
| Stop conditions | yes |
| Rollback/fallback policy | yes |
| Observability, audit, and log review | yes |
| Redaction policy | yes |
| Approval gates | yes |
| Go/no-go decision | yes |
| Next action | yes |

Planning match rate: `100%`

Execution match rate: `0%`, intentionally. Stage 4 execution requires a later
explicit approval.

## Stage 4 Objective

Stage 4 exists to move from accepted bounded evidence to a full operational
dataset rollout only after the operator acceptance owner explicitly approves the
scope and execution plan.

The objective is to prove that the full source scope can be reconciled, uploaded,
audited, and verified against the independent operator stack without mixing
legacy evidence, widening scope silently, or using destructive cleanup as a
recovery shortcut.

Stage 4 must remain split into at least two separate approvals:

1. Stage 4 Preview-only approval.
2. Stage 4 Start Upload approval after Preview-only evidence is reviewed.

## Stage 4 Prerequisites

| Prerequisite | Required state |
| --- | --- |
| Stage 0 readiness | accepted with documented caveats |
| Stage 1 Preview-only | passed |
| Stage 2 small Start Upload | passed |
| Stage 3 Profile A bounded batch | `passed_with_caveats` accepted |
| Independent target alignment | DB and Edge target classes remain independent and aligned |
| Runtime core readiness | API, DB, Studio, and Edge are ready enough for the scoped step |
| Edge no-auth class | `GET` and `POST {}` return auth-class, not server-class |
| Monitoring caveats | Grafana/vector caveats recorded separately from core readiness |
| Approval owner | named before any Stage 4 Preview-only run |
| Rollback decision owner | named before any Stage 4 Preview-only run |
| Evidence handling | sanitized labels, aggregate counts, safe ids, no raw operational locators |

If any prerequisite is not true, Stage 4 remains blocked and the next action is
an investigation or readiness-only review, not Preview.

## Evidence Basis

| Evidence | Stage 4 implication |
| --- | --- |
| `docs/76_operator_full_dataset_rollout_plan.md` | Defines staged rollout, Stage 4 separation, stop conditions, and non-destructive rollback. |
| `docs/82_operator_stage_3_bounded_rollout_plan.md` | Defines exact DB delta rule, bounded expansion discipline, and Stage 4 preconditions. |
| `docs/98_operator_stage_3_bounded_start_upload_rerun_2.md` | Shows one Profile A bounded Start Upload succeeded with exact DB delta reconciliation. |
| `docs/99_operator_stage_3_bounded_acceptance_review.md` | Accepts Stage 3 Profile A bounded batch as evidence with caveats, but not full rollout approval. |
| `docs/73_operator_final_readiness_summary.md` | Records readiness with caveats and keeps full source upload behind separate approval. |
| `docs/75_operator_final_runtime_smoke.md` | Records package-like runtime target class alignment and non-core monitoring caveats. |

## Source Scope Confirmation

Before Stage 4 Preview-only, the operator acceptance owner must approve the full
operational dataset scope using only safe labels and counts.

Required source scope evidence:

| Item | Requirement |
| --- | --- |
| Source label | sanitized label only |
| Source class | `full_operational_dataset` |
| File count | counted before Preview |
| Physical row count | counted or explicitly marked as too costly to count safely |
| Expected exact-key count | estimated or measured by the approved Preview-only path |
| Date metadata | file-date metadata rules documented for every included class |
| Exclusion rules | documented before Preview |
| Already-in-DB expectation | documented before Preview |
| Operator confirmation | explicit approval that the scope is full dataset, not bounded sample |

Do not infer scope from local locator details. Do not document source locator
details, source names, source row content, or raw local machine paths.

## Preview-Only Gate

Stage 4 Preview-only must be a separate PR or explicitly approved QA run.

Required Preview-only behavior:

| Gate | Requirement |
| --- | --- |
| Execution count | exactly `1` Preview for the approved full dataset scope |
| Start Upload | `0` in Preview-only PR |
| Retry Failed | `0` |
| Duplicate rerun | `0` |
| Full rollout upload | not performed |
| Runtime preflight | API, DB, Studio, Edge ready; target classes aligned |
| Edge no-auth probe | auth-class for `GET` and `POST {}` |
| Preview status | terminal and successful |
| `dbStatus` | `reachable` |
| Preview DB mutation | DB row-count delta `0` |
| Counts | total files, total rows if available, already-in-DB, target, excluded, risky, failed, invalid |
| Exact-key evidence | local exact-key count, DB match count, target estimate |
| Redaction | marker scan clean before sharing or merging evidence |

Preview-only go/no-go:

- If Preview target count is `0` because all exact keys are already represented,
  do not Start Upload. Record duplicate-safety evidence.
- If target count is non-zero and all gates pass, the next step may be a
  separate Start Upload approval.
- If `dbStatus` is not `reachable`, stop. Do not Start Upload from that Preview.

## Start Upload Gate

Stage 4 Start Upload requires a second explicit approval after Preview-only
evidence is reviewed.

Required Start Upload behavior:

| Gate | Requirement |
| --- | --- |
| Approval | explicit user approval for Stage 4 Start Upload scope |
| Preview reference | approved Stage 4 Preview-only result |
| Operator count confirmation | file count, physical row count, target exact-key count, expected DB delta |
| Runtime preflight | repeated immediately before Start Upload |
| Execution count | exactly `1` Start Upload |
| Retry Failed | `0` unless a later separate approval exists |
| Duplicate rerun | `0` |
| Upload job final status | `succeeded` |
| Failed files | `0` unless pre-approved with exact threshold |
| Invalid rows/files | `0` unless pre-approved with exact threshold |
| Warning count | `0` or explained non-blocking warning class |
| DB delta | exact match to expected net-new exact-key count |
| Audit/job events | start, progress, terminal status, and no unexplained gaps |
| UI/log evidence | safe labels and aggregate counts only |

Start Upload must stop after one approved full dataset execution. Any retry,
rerun, cleanup, or rollback must be handled in a separate PR.

## DB Delta And Exact-Key Acceptance Criteria

The acceptance rule is exact:

```text
actual DB row-count delta == expected net-new transformed exact-key count
```

Tolerance: `0`

Required count separation:

| Count class | Meaning |
| --- | --- |
| Physical row count | source-size and upload-throughput evidence |
| Upload processed/uploaded/accepted rows | upload job throughput evidence |
| Local exact-key count | transformed key basis |
| DB match count before upload | already represented exact keys |
| Expected net-new exact keys | DB delta expectation |
| DB row-count delta | acceptance evidence |
| Exact-key presence after upload | completeness evidence |

Do not treat physical row counters as DB delta. If the two differ, explain the
reason with transformed exact-key evidence.

## Stop Conditions

Stop before continuing if any condition appears:

| Stop condition | Required action |
| --- | --- |
| Operator has not explicitly approved the Stage 4 step | stop and request approval |
| Source scope cannot be confirmed with safe labels and counts | stop and define scope |
| Runtime core API, DB, Studio, or Edge is not ready | stop before Preview or Upload |
| DB and Edge target classes are not independent and aligned | stop and investigate config |
| Edge no-auth probes return server-class status | stop and investigate Edge readiness |
| Preview `dbStatus` is not `reachable` | stop, no Start Upload |
| Preview DB delta is not `0` | stop and investigate mutation source |
| Target count is unexpected or too broad for approval | stop and split or re-approve scope |
| Failed, invalid, risky, or unexpected excluded counts appear | stop and classify before upload |
| Upload job fails, cancels, or has failed files | stop, no retry in the same PR |
| DB delta differs from expected net-new exact keys | stop and preserve evidence |
| Redaction scan finds prohibited operational or credential material | stop and redact before sharing |
| Someone proposes destructive cleanup as the recovery path | stop and write a separate maintenance plan |

## Rollback And Fallback Policy

Rollback policy is non-destructive by default.

Forbidden in Stage 4 plan, Preview, or Start Upload PRs:

- DB reset, deletion, cleanup, prune, drop, or truncate;
- Docker volume, container, image, or network deletion;
- Supabase init, bootstrap, start, stop, or reset;
- operational source modification or deletion;
- forced duplicate upload;
- production deploy;
- Release or tag creation.

If Stage 4 fails:

1. stop the current step;
2. capture sanitized runtime, Preview/job, DB delta, exact-key, audit, and log
   evidence;
3. do not continue to another upload action;
4. do not repair by deleting DB rows or Docker resources;
5. create a separate investigation, recovery, or rollback plan.

Uploaded-row rollback is outside normal Stage 4. If reversal is required, write
a separate rollback PR with explicit scope, approval owner, evidence rules, and
non-destructive alternatives first.

## Observability, Audit, And Log Review

Stage 4 evidence must include:

| Evidence | Requirement |
| --- | --- |
| Runtime summary | API, DB, Studio, Edge, Grafana, vector caveat class |
| Preview evidence | status, `dbStatus`, count classes, DB delta `0` |
| Upload job evidence | status, file counts, row counters, failed/invalid/warning counts |
| DB evidence | before/after counts, exact-key reconciliation, delta comparison |
| Audit evidence | Preview and upload action records summarized safely |
| Job event evidence | start, progress, completion, failure absence |
| SSE/log evidence | reviewed if available, with safe labels only |
| UI evidence | optional unless acceptance owner requires it |
| Redaction evidence | marker scan and manual review result |

Grafana remains status/link-only unless the operator acceptance owner explicitly
requires dashboard evidence for Stage 4. Vector caveats remain monitoring/runtime
attention unless they correlate with API, DB, Studio, Edge, Preview, or Upload
failure.

## Redaction Policy

Allowed evidence:

- sanitized source label;
- stage id;
- status class;
- target class;
- file and row counts;
- exact-key count class;
- DB delta;
- safe preview/job ids;
- audit/log event counts;
- caveat class;
- marker scan result.

Forbidden evidence:

- credential material;
- raw connection material;
- auth header material;
- operational source locator details;
- operational source names;
- operational row content;
- full local machine locators;
- package output, archive, or checksum material.

## Approval Gates

| Gate | Approval required |
| --- | --- |
| Before Stage 4 Preview-only | explicit user approval for full dataset Preview-only scope |
| After Stage 4 Preview-only | acceptance of Preview counts, `dbStatus`, target rows, exclusions, and DB delta `0` |
| Before Stage 4 Start Upload | explicit user approval to execute Start Upload once |
| After Stage 4 Start Upload | acceptance of job status, DB delta, exact-key evidence, audit/log evidence, and caveats |
| Before any Retry Failed or duplicate rerun | separate explicit approval in a different PR |
| Before any rollback | separate explicit rollback plan and approval |
| Before production deploy, Release, or tag | separate explicit release approval |

Plain-language rule: Stage 4 full rollout does not start until the user directly
approves the specific Stage 4 execution step.

## Go/No-Go Decision

Current decision: `no-go_for_execution`

This document is ready for review as a plan. It does not approve or execute Stage
4 Preview-only or Stage 4 Start Upload.

Stage 4 Preview-only can become eligible only after this plan/review is approved
and the user gives a separate explicit approval for Preview-only.

Stage 4 Start Upload can become eligible only after Stage 4 Preview-only succeeds
and the user gives another separate explicit approval for Start Upload.

## Next Action

Recommended next branch after this plan/review is accepted:

```text
codex/operator-stage-4-preview-only
```

That branch must remain Preview-only unless the user explicitly changes the
scope. Start Upload remains forbidden until Stage 4 Preview-only evidence is
reviewed and separately approved.
