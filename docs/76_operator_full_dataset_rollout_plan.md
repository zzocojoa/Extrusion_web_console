# Operator Full Dataset Rollout Plan

## Summary

- Date: 2026-06-11
- Branch: `codex/operator-full-dataset-rollout-plan`
- Base commit: `9ef43e9d582719f72537e2b4f08ff3835f659b3a`
- PDCA phase: Plan
- Scope: documentation-only staged rollout plan
- Rollout readiness: `plan_ready_with_caveats`

This plan defines how to move from bounded operator-package acceptance evidence
to a full operational dataset upload without jumping directly to a broad run.
It does not execute Upload Preview, Start Upload, duplicate rerun, Edge
authenticated upload, or full dataset rollout.

## Rollout Objective

The objective is to validate the independent `Extrusion_web_console` operator
package against real operational data in staged, reversible gates before any
full operational dataset upload.

The rollout must preserve these constraints:

- the independent `Extrusion_web_console` Supabase stack remains the default
  target;
- DB reconciliation and Edge upload targets remain aligned to the independent
  stack;
- the legacy `Extrusion_data` stack is never used implicitly;
- fallback to `Extrusion_data` is allowed only through explicit maintainer
  env/config override and must be recorded as fallback, not as independent
  evidence;
- no destructive cleanup is used as a recovery shortcut.

## Preconditions

Before Stage 0 starts, all of these must be true or explicitly waived by the
operator acceptance owner:

| Precondition | Required state |
| --- | --- |
| Final runtime smoke | `docs/75_operator_final_runtime_smoke.md` verdict is `ready_with_caveats`. |
| Operator readiness | `docs/73_operator_final_readiness_summary.md` accepts bounded package readiness with caveats. |
| Runtime target | DB and Edge target classes are both independent and aligned. |
| Edge route | no-auth Edge `GET` and `POST {}` return auth-class, not `503`. |
| Preview duplicate-safety | normal-flow duplicate evidence policy is accepted: DB-backed Preview exclusion is the primary proof. |
| Docker Desktop | running before any runtime or upload QA. |
| Supabase stack | independent API, DB, Studio, and Edge are reachable enough for the scoped stage. |
| Legacy stack | stopped is preferred; any fallback use must be explicit and must not be mixed with independent evidence. |
| Package path | assembled operator package or explicitly equivalent package-local path is used for rollout evidence. |
| Redaction | evidence records only status classes, safe labels, counts, and sanitized ids. |

Vector and Grafana remain caveats. They do not block core upload evidence by
themselves, but their state must be recorded before expanding scope.

## Rollout Stages

| Stage | Name | Allowed execution | Exit condition |
| --- | --- | --- | --- |
| Stage 0 | Readiness recheck only | Runtime/config/audit/UI read-only checks. No Preview or Start Upload. | Independent core runtime and target alignment are current. |
| Stage 1 | Small operational sample Preview only | One approved bounded Preview against a sanitized source label. No Start Upload. | Preview has `dbStatus=reachable` and bounded counts are acceptable. |
| Stage 2 | Small operational sample Start Upload | One Start Upload for the Stage 1 approved sample only. | DB row-count delta and job accepted/upserted counts match expectations. |
| Stage 3 | Day-bounded or batch-bounded rollout | One bounded day or batch at a time after operator approval. | Each batch passes Preview, Upload, audit/log, and DB delta checks. |
| Stage 4 | Full operational dataset | Full dataset only after Stages 0-3 are accepted. | Final upload report and monitoring review accepted. |

Stage numbers are gates. Do not skip directly from Stage 0 to Stage 4.

## Per-Stage Checks

### Stage 0: Readiness Recheck Only

Purpose: prove the operator package runtime is still in the same safe class as
the final runtime smoke.

Required checks:

- package launcher `-CheckOnly` or equivalent package-local read-only check;
- `/api/health`;
- `/api/config`;
- `/api/runtime/local-supabase`;
- Settings redaction;
- DB target class: independent;
- Edge target class: independent;
- API, DB, Studio, and Edge reachability;
- Edge no-auth status class;
- vector and Grafana caveat status;
- Audit Logs read-only redaction if available.

Stage 0 must not run Upload Preview or Start Upload.

### Stage 1: Small Operational Sample Preview Only

Purpose: confirm real operational data can be reconciled against the independent
DB before upload, using a bounded source scope.

Required checks:

- operator confirms the source is a small bounded sample, not the full
  operational dataset;
- source is documented only with a sanitized label;
- Preview runs once;
- `dbStatus=reachable`;
- total, already-in-db, upload-target, excluded, failed, and invalid counts are
  recorded;
- target count is bounded and expected for the sample;
- DB row count is not mutated by Preview;
- audit/log evidence is redacted;
- UI shows Preview results without raw secret or source details.

Stage 1 must not click Start Upload.

### Stage 2: Small Operational Sample Start Upload

Purpose: upload exactly the Stage 1 approved target rows once.

Required checks:

- repeat runtime target alignment immediately before upload;
- use the Stage 1 Preview result or a fresh approved Preview if the previous
  Preview is stale;
- operator confirms the sample scope and target count;
- Start Upload is executed once only after approval;
- upload job accepted/upserted count is recorded separately from DB row-count
  delta;
- DB row-count delta matches the expected net-new exact keys;
- failed-row count is zero or within the approved threshold;
- audit log contains safe upload summary evidence;
- UI shows completed job status and safe labels only.

If the target count is zero because all rows are `already_in_db`, do not force a
duplicate upload as part of normal operator acceptance. Record duplicate-safety
evidence per `docs/71_operator_duplicate_safety_evidence_policy.md`.

### Stage 3: Day-Bounded Or Batch-Bounded Rollout

Purpose: expand from a small sample to operationally meaningful batches while
preserving rollback decision points.

Required checks for each batch:

- operator confirms the bounded day or batch scope;
- Preview count is reviewed before Start Upload;
- `dbStatus=reachable`;
- already-in-db, upload-target, excluded, failed, and invalid counts are within
  expected bounds;
- Start Upload is approved for that batch only;
- DB row-count delta is recorded and compared with expected net-new exact keys;
- upload job events and SSE replay, if applicable, show no unexplained gaps;
- audit/log redaction is clean;
- operator signs off before the next batch.

Do not chain batches automatically. Each batch is a separate gate.

### Stage 4: Full Operational Dataset

Purpose: run the full operational dataset only after evidence from the smaller
stages proves the path is stable.

Required checks:

- Stages 0-3 have accepted reports;
- current runtime readiness is still independent and core-ready;
- operator approval explicitly names full dataset rollout as the approved scope;
- Preview completes with `dbStatus=reachable`;
- target count is reviewed and accepted before Start Upload;
- monitoring owner is assigned;
- rollback/fallback decision owner is assigned;
- final evidence report records counts, DB delta, upload job status, audit/log
  redaction, caveats, and next monitoring actions.

Full dataset rollout is not approved by this plan document. It requires a later
explicit QA/execution PR.

## Stop Conditions

Stop the current stage immediately if any condition is true:

| Stop condition | Required action |
| --- | --- |
| DB target class is legacy, unknown, or mismatched with Edge | Stop and investigate target config. Do not upload. |
| Edge target class is legacy, unknown, or mismatched with DB | Stop and investigate target config. Do not upload. |
| Edge route returns `503`, timeout, or server-class status | Stop and record Edge readiness blocker. |
| `/api/runtime/local-supabase` reports core API, DB, Studio, or Edge blocked | Stop before Preview or Upload. |
| Preview returns `dbStatus=not_checked` or unreachable | Stop. No Start Upload from that Preview. |
| Preview target count is unexpected or too large for the approved stage | Stop and require operator confirmation or smaller scope. |
| Failed or invalid count exceeds the stage threshold | Stop and inspect sanitized failure class. |
| Raw secret, DB URL, token, Authorization header, JWT, source path, source content, source filename, or full local path appears in evidence | Stop and redact before sharing or merging evidence. |
| Docker or Supabase instability affects core runtime | Stop and capture sanitized state. Do not reset, prune, or delete. |
| Operator cannot confirm bounded source scope | Stop. Do not infer scope from local paths or filenames. |
| Any reset, delete, cleanup, prune, drop, truncate, or Docker delete is suggested as required | Stop and escalate for a separate maintenance plan. |

## Rollback And Fallback

Rollback policy is non-destructive.

Forbidden without a separate explicit approval:

- DB reset, delete, cleanup, prune, drop, truncate, or destructive migration;
- Docker container, volume, image, or network deletion;
- Supabase reset or destructive bootstrap;
- AppData config/state/log deletion;
- operational source modification or deletion;
- forced duplicate upload using operational data.

If a stage fails:

1. stop the stage;
2. record sanitized runtime state, Preview/job status, counts, and audit/log
   evidence;
3. do not continue to the next stage;
4. do not clean up by deleting DB rows or Docker resources;
5. decide whether to keep the independent package idle, rerun readiness only, or
   use explicit legacy fallback.

Legacy `Extrusion_data` fallback:

- is allowed only through explicit maintainer env/config override;
- must be labeled as fallback evidence;
- must not be mixed with independent target evidence in the same acceptance
  claim;
- must not mutate or delete independent runtime data as part of fallback.

Uploaded-row rollback is not part of normal rollout. If a net-new upload must be
reversed, create a separate rollback plan with exact scope, approval, audit
requirements, and non-destructive alternatives first.

## Observability

Each stage report should collect only sanitized evidence:

- runtime status summary;
- Preview run status and counts;
- Upload Job status, accepted/upserted counts, failed counts, and completion
  class;
- upload job events;
- SSE replay status if applicable;
- audit log rows for Preview and Upload actions;
- UI status result;
- DB row-count delta;
- caveat status for vector and Grafana;
- redaction scan result.

Grafana remains status/link only. Grafana unreachable does not block core upload
unless the operator acceptance owner explicitly requires Grafana evidence for a
specific stage.

Vector restarting/stopped remains a caveat. Treat it as a monitoring/runtime
attention item unless it correlates with failed API, DB, Studio, Edge, Preview,
or Upload behavior.

## Security And Redaction

Do not document, paste, screenshot, or commit:

- raw secret values;
- DB URLs or connection strings;
- local API tokens;
- Authorization headers;
- JWT values;
- anon key or service role values;
- source paths;
- source filenames;
- row contents;
- full local paths;
- generated Supabase credentials;
- raw Supabase status/start output;
- package output paths, zip names, or checksum contents.

Allowed evidence:

- sanitized source label;
- stage id;
- status class;
- target class;
- non-secret port class;
- counts;
- redaction marker scan result;
- job/preview ids when safe;
- caveat class.

Stage reports must use counts and safe labels only.

## Approval Gates

| Gate | Approval required |
| --- | --- |
| Before Stage 0 | Approval to run readiness-only QA. |
| After Stage 0 | Acceptance that runtime target alignment and caveats are understood. |
| Before Stage 1 | Approval of bounded sample class and Preview-only scope. |
| After Stage 1 | Acceptance of Preview counts and `dbStatus=reachable`. |
| Before Stage 2 | Explicit approval to Start Upload once for the Stage 1 target only. |
| After Stage 2 | Acceptance of DB row-count delta, upload job status, and audit/log redaction. |
| Before each Stage 3 batch | Approval of the exact bounded batch class and expected count range. |
| After each Stage 3 batch | Acceptance before expanding to the next batch. |
| Before Stage 4 | Separate explicit approval for full operational dataset rollout. |

Production deploy, GitHub Release, and GitHub tag creation remain outside this
rollout plan and require separate approval.

## Stage Report Template

Use this template for future QA PRs.

```text
Stage:
Verdict:
Package path class:
Runtime readiness:
DB target class:
Edge target class:
Edge no-auth status class:
Source label:
Source scope confirmation:
Preview status:
dbStatus:
Preview total count:
Already-in-db count:
Upload-target count:
Excluded count:
Failed/invalid count:
Start Upload executed:
Upload job status:
Accepted/upserted count:
DB row-count delta:
Audit/log redaction:
UI evidence:
Vector caveat:
Grafana caveat:
Stop conditions hit:
Operator approval:
Next action:
```

Source label must be sanitized. Do not record raw source path, filename, or row
content.

## Next Recommended QA PR

Recommended next PR: Stage 0 readiness recheck only.

Suggested branch:

```text
codex/operator-stage-0-readiness-recheck
```

Stage 0 should confirm the current operator package runtime state without
running Upload Preview, Start Upload, duplicate rerun, Edge authenticated upload,
or full operational dataset rollout.

If Stage 0 is accepted, the following PR should be Stage 1 small operational
sample Preview-only. That PR must use a sanitized source label and must not
upload data.

## Merge Readiness For This Plan

This plan PR is merge-ready when:

- the PR includes only `docs/76_operator_full_dataset_rollout_plan.md`;
- `git diff --check` passes;
- marker scan finds no raw secret, DB URL, token, Authorization header, JWT,
  source path, source filename, row content, full local path, package output,
  zip, or checksum marker;
- untracked PNG and operational fixtures are not staged;
- `.gstack`, `frontend/dist`, package output, zip, and checksum files are not
  staged;
- no runtime, DB, Docker, Upload Preview, Start Upload, duplicate rerun, Edge
  authenticated call, production deploy, Release, or tag operation was run.
