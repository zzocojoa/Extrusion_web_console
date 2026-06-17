# Operator Full Rollout Separate Approval Investigation

Date: 2026-06-17 Asia/Seoul

Scope: report-only P1 investigation for full rollout approval boundaries,
Preview-only approval boundaries, mutating action protection, audit evidence,
and stop-condition clarity.

Verdict: `full_rollout_separate_approval_boundary_verified_with_preview_approval_caveat`

Match Rate: `95%`

## Summary

The P1 judgment is supported.

Current repository evidence does not show an approved full rollout state. The
docs consistently separate these concepts:

- bounded or single-target upload acceptance;
- Stage 4 planning readiness;
- Stage 4 Preview-only evidence;
- Stage 4 Start Upload evidence;
- future full rollout approval.

The code also has no separate `full_rollout` execution mode. Operational upload
mutation happens through explicit Preview, Start Upload, or Retry Failed API
actions. Start Upload and Retry Failed have backend count contracts and blocked
audit paths. Upload Preview is protected by the local token guard, writes
`upload.preview` audit rows, and blocks concurrent active previews, but the
backend cannot prove a human approval record for each Preview request by itself.
That is the remaining caveat and why this report is `95%`, not `100%`.

This investigation did not execute Upload Preview, Start Upload, Retry Failed,
duplicate rerun, authenticated Edge call, full rollout, Settings save,
DB/Supabase/Docker lifecycle, DB destructive work, or operational source
mutation.

## Non-Developer Explanation

There is no "do everything now" button hidden in the app.

The app has separate gates:

1. Preview checks what would happen.
2. Start Upload uploads only the reviewed target count.
3. Retry Failed retries only after a new retry approval.

The full rollout is an operating plan, not a single automatic feature. Even if a
document says a prior upload was accepted, that means "that one reviewed upload
was accepted." It does not mean the next Preview, next upload, or whole remaining
dataset is approved.

## Root Cause Hypothesis

`full_rollout_is_operational_scope_not_product_mode`

The term "full rollout" appears in planning and acceptance documents, but not as
a distinct backend or frontend execution mode. The actual product exposes lower
level actions: Upload Preview, Start Upload, Retry Failed, and upload controls.
Safety therefore depends on two layers:

- code-level protection around each mutating action;
- operator runbook discipline requiring fresh Preview, count review, and
  separate approval before each broader scope.

The code-level gates are strong for Start Upload and Retry Failed. Preview
approval remains primarily procedural because a valid local console session can
start a Preview without the backend knowing whether the user separately approved
that specific Preview.

## Documents Reviewed

| Document | Finding |
| --- | --- |
| `AGENTS.md` | Core Ops includes Preview, Start Upload, Retry, logs, and audit. Dangerous operations must be audit logged. |
| `README.md` | Day-to-day upload decisions must follow `docs/151_operator_upload_gate_runbook.md`; future uploads require fresh Preview, target count review, and separate approval. |
| `docs/00_product_scope.md` | Preview reconciliation is required before upload; DB upsert remains final duplicate protection. |
| `docs/01_development_roadmap.md` | Upload jobs, retry, audit, token guard, and accepted row semantics are implemented Core Ops, not a full rollout shortcut. |
| `docs/03_ui_ux_plan.md` | Upload UI separates Preview and Job tabs; risky/partial rows are excluded by default; Start Upload is disabled for stale, blocked, or absent Preview. |
| `docs/76_operator_full_dataset_rollout_plan.md` | Full dataset rollout is not approved by the plan document; Stage 4 requires later explicit QA/execution approval. |
| `docs/82_operator_stage_3_bounded_rollout_plan.md` | Stage 3 success does not approve Stage 4; no automatic batch chaining; each batch requires approval. |
| `docs/99_operator_stage_3_bounded_acceptance_review.md` | Stage 3 Profile A evidence is accepted only as bounded-batch evidence, not full rollout approval. |
| `docs/100_operator_stage_4_full_rollout_plan_review.md` | Stage 4 plan is `no-go_for_execution`; Preview-only and Start Upload require separate approvals. |
| `docs/110_operator_stage_4_final_acceptance_summary.md` | Accepts one executed target only; explicitly does not approve additional Preview, Start Upload, Retry, or full rollout beyond that target. |
| `docs/140_operator_large_source_upload_acceptance_summary.md` | Accepts one large-source Preview and one Start Upload; no wider rollout or further upload is approved. |
| `docs/150_operator_handoff_caveat_release_steady_template.md` | Future uploads still require fresh Preview-only, target review, and separate Start Upload or Retry Failed approval. |

## Approval Wording Review

The potentially broad words are `accepted`, `ready`, `next action`, and
`may proceed`.

Current docs keep them bounded:

- `docs/99` says bounded Stage 3 evidence is accepted, then states full rollout
  remains blocked until separately approved.
- `docs/100` says Stage 4 planning is ready, but the execution decision is
  `no-go_for_execution`.
- `docs/110` says Stage 4 evidence is accepted for the single approved upload
  target already executed, then lists additional Preview, Start Upload, Retry,
  and full rollout beyond the target as not approved.
- `docs/140` accepts one large-source upload and states future work must start
  from a new Preview-only gate.
- `docs/150` keeps operational handoff separate from release/tag and future
  upload approval.

No reviewed document grants standing approval for full rollout or automatic
future Preview.

## Backend Gate Review

### Upload Preview

`backend/app/api/upload_preview.py` protects Preview creation as a mutating API
through the local token middleware classification in
`backend/app/core/local_token.py`.

Preview creation also:

- validates JSON and request shape before creating a run;
- writes failure audit rows for malformed or invalid Preview requests;
- creates a run only through `create_run_if_no_active`;
- blocks concurrent active Preview runs with `409`;
- writes blocked `upload.preview` audit evidence for active Preview conflicts;
- records safe request metadata such as range mode, source class keys, option
  keys, and count summaries.

Caveat: the backend does not require an `expectedTargetRows`-style human
approval payload for Preview itself. So "additional Preview requires separate
approval" is enforced by runbook/process plus token/audit, not by a count
contract in the Preview API.

### Start Upload

`backend/app/api/upload_jobs.py` accepts only `preview_targets` mode for Start
Upload. There is no full-rollout mode.

Start Upload requires:

- valid upload config;
- DB/Edge target preflight pass;
- `expectedTargetRows`;
- optional positive `expectedTargetFiles`;
- no active upload job.

`backend/app/db/upload_job_repository.py` revalidates inside `BEGIN IMMEDIATE`:

- preview exists;
- preview is latest;
- preview freshness is known;
- preview is not stale;
- preview status is `succeeded`;
- preview DB status is `reachable`;
- risky item count is `0`;
- preview source snapshot matches current source gate snapshot;
- target files and target rows are positive;
- expected files/rows match the current preview snapshot.

Rejected cases do not create an upload job and are converted into blocked
`upload.start` audit rows by the API layer.

### Retry Failed

Retry Failed is a separate API action and separate audit action.

It requires:

- valid upload config;
- DB/Edge target preflight pass;
- `expectedRemainingRows`;
- optional positive `expectedRetryFiles`;
- no active upload job.

The repository computes retryable files and remaining physical rows inside
`BEGIN IMMEDIATE`, rejects mismatches before job creation, and records expected
versus actual retry counts in `job.created` event data and `upload.retry` audit
params.

### Local Token Boundary

`backend/app/core/local_token.py` protects every non-GET, non-HEAD, non-OPTIONS
same-origin `/api/*` request when token enforcement is enabled. Known upload
routes map to audit actions:

- `POST /api/upload/preview` -> `upload.preview`;
- `POST /api/upload/jobs` -> `upload.start`;
- `POST /api/upload/jobs/{jobId}/retry` -> `upload.retry`;
- pause/resume/cancel map to their own upload audit actions.

Unknown future mutating API routes fall back to `local.token` and are still
blocked without a valid local token.

## Frontend Gate Review

`frontend/src/pages/UploadPage.tsx` separates UI actions:

- Run Preview calls Preview creation only.
- Start Upload button opens `StartUploadConfirmationModal`; it does not call
  the mutation directly.
- Start Upload is enabled only for a succeeded Preview with reachable DB,
  positive target files, positive upload rows, and zero risky rows.
- The confirmation modal requires typing the exact unformatted target row
  count before enabling the final confirm button.
- Final Start Upload mutation sends `expectedTargetRows` and
  `expectedTargetFiles`.
- Retry Failed opens a separate confirmation modal and requires typing the exact
  remaining physical row count before sending `expectedRemainingRows` and
  `expectedRetryFiles`.

The i18n copy keeps the Preview and upload steps separate. There is no visible
full-rollout action label in the Upload UI.

## Test Coverage Review

Validated tests cover the P1 boundary:

- `tests/backend/test_upload_preview_api_contract.py`
  - Preview malformed/invalid requests write failure audit rows.
  - Active Preview conflict writes blocked audit evidence.
  - Preview audit rows are queryable through the audit API.
- `tests/backend/test_upload_jobs_repository_contract.py`
  - non-latest Preview is rejected.
  - stale Preview is rejected.
  - risky Preview is rejected.
  - source snapshot mismatch and missing snapshot are rejected.
  - expected Start Upload rows/files mismatch is rejected.
  - retry expected remaining rows mismatch is rejected.
- `tests/backend/test_upload_jobs_api_contract.py`
  - missing upload config and target preflight failure block Start Upload.
  - missing/mismatched expected target rows write blocked `upload.start` audit.
  - preview source mismatch writes blocked `upload.start` audit.
  - no retryable files, missing expected retry rows, and retry count mismatch
    write blocked `upload.retry` audit.
- `tests/backend/test_local_token.py`
  - missing and invalid local tokens block mutating APIs.
  - upload preview, upload start, upload retry, runtime start/stop, and unknown
    future mutating API routes are protected.
- `tests/backend/test_audit_repository.py`
  - audit log is append-only.
  - safe scalar search does not expose raw secret-like params or raw error
    messages.

Coverage caveat:

- There is no backend "Preview approval token" or operator-signed Preview count
  contract. That is acceptable for the current P1 investigation because Preview
  is non-uploading and audited, but it means the statement "additional Preview
  requires separate approval" is a procedural/runbook invariant rather than a
  backend count-contract invariant.

Follow-up implementation note:

- Branch `codex/preview-approval-scope-contract` narrows this caveat by adding
  a backend Preview approval-scope contract. Preview creation now requires
  expected source class, range, and applied profile evidence, blocks mismatches
  before run creation, and records expected/actual scope in `upload.preview`
  audit evidence. This does not approve any Preview run by itself; it makes the
  approved Preview scope machine-checkable.

## P1 Decision

| Question | Answer |
| --- | --- |
| Has full rollout been approved by current docs? | no |
| Does any reviewed acceptance doc approve future upload automatically? | no |
| Is there a product/API mode named full rollout? | no |
| Is Start Upload separately gated from Preview? | yes |
| Is Retry Failed separately gated from Start Upload? | yes |
| Are Start Upload and Retry blocked before job creation when counts mismatch or approval counts are missing? | yes |
| Is additional Preview automatically blocked without a human approval artifact? | partially |
| Does Preview still require local token and audit evidence? | yes |
| Is an immediate code patch required for full rollout separation? | no |

## Blocking Issues

No blocking code issue was found for the current P1 decision.

Full rollout remains unapproved. Additional Preview also remains unapproved by
policy, but the Preview API currently enforces this through local-token/audit and
active-run conflict only. If the team wants machine-enforced Preview approvals,
that should be a separate feature.

## Recommendations

1. Treat `docs/76`, `docs/100`, and `docs/151` as the controlling operating
   policy for full rollout and future upload gates.
2. Do not interpret `docs/110` or `docs/140` as approval for any future upload
   activity. They accept only the already executed target in each report.
3. Keep full rollout as a separate execution approval with:
   - fresh Preview-only evidence;
   - explicit full dataset source scope;
   - target count review;
   - runtime target class pass;
   - stop conditions;
   - separate Start Upload approval.
4. If the remaining 5% caveat matters, add a future Preview request approval
   contract, for example an `approvalScope` or `expectedSourceClass` field that
   is audited and validated before Preview creation. Do not mix that with an
   upload execution PR.
5. Keep UI copy strict: "Ready" and "Accepted" mean the current reviewed step,
   not standing approval for the next Preview, next upload, or full rollout.

## Validation

| Check | Result |
| --- | --- |
| Branch separated | `codex/full-rollout-separate-approval-investigation` |
| Required policy docs reviewed | passed |
| Backend Preview API reviewed | passed |
| Backend Upload Job API/repository reviewed | passed |
| Local token guard reviewed | passed |
| Frontend Upload UI/i18n reviewed | passed |
| Rollout-mode code search | no full-rollout execution mode found |
| Targeted backend tests | `63 passed` |
| `npm run typecheck` | passed |
| `npm run build` | passed |
| Upload Preview executed | no |
| Start Upload executed | no |
| Retry Failed executed | no |
| duplicate rerun executed | no |
| authenticated Edge call executed | no |
| full rollout executed | no |
| Settings save executed | no |
| DB/Supabase/Docker lifecycle or destructive operation | no |
| Operational CSV mutation | no |

Test warnings observed:

- FastAPI/Starlette deprecation warning for `HTTP_422_UNPROCESSABLE_ENTITY`.
- Pytest cache write warning for `.pytest_cache` access.

Neither warning changes the P1 approval-boundary finding.

## Redaction Result

This report uses repository file paths, document names, code-level action names,
and aggregate test counts only. It does not include raw operational source
locators, operational source filenames, source content, row content, DB URLs,
credential material, local token values, Authorization values, JWT-shaped
values, or package output paths.

## Next Action

Publish this docs-only report for review if the team wants this P1 decision on
main.

No full rollout, additional Preview, Start Upload, or Retry Failed is approved
by this report. Any future upload work must start with a fresh Preview-only
approval, target count review, and a separate explicit Start Upload or Retry
Failed approval.
