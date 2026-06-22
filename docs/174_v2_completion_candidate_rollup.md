# V2 Completion Candidate Rollup

Date: 2026-06-22 Asia/Seoul

Status: `completion_track_candidate_main_merge_precheck`

## Purpose

This document records the current V2 completion-track candidate for the eight
remaining V2 items and separates the current `main` baseline, the
completion-track candidate baseline, and package evidence baseline.

It does not approve merge, deployment, LAN exposure, Upload Preview, Start
Upload, Retry Failed, Delete, Settings save, feature-gate enablement, Supabase
reset/cleanup, Docker cleanup, schema migration, operational DB mutation, or
source-file mutation.

`main` is not yet a V2 completion candidate until PR #193 is reviewed, merged
to `main`, and the post-merge verification is rerun from `main` or proven to
match the exact tested completion-track commit.

## Baseline

- Current `origin/main` baseline:
  `baee4982d8be9f6ef8e44b4a8ca6f1a30a382222`.
- Reviewed completion-track candidate before this package-evidence rule update:
  `codex/v2-completion-track` and `origin/codex/v2-completion-track` at
  `e405fcddc0161c4fde48e4e314b642ad8472a0c9`.
- Package evidence policy:
  approval-time `package-build-info.json` verification is canonical. Static
  package metadata in this document is sample evidence only. Before PR #193 main
  merge approval, package `sourceCommit` must match the current PR #193
  `headRefOid` short SHA, or the package evidence remains sample-only and main
  merge must stop.
- Latest local verification sample:
  `sourceCommit=e405fcd`,
  `packageLabel=ExtrusionWebConsole-e405fcd-20260622-024709-519`,
  `frontendMode=api`, `runtimeMode=operator-ready`, `zipCreated=false`, and
  `zipSha256=not_applicable`.
- PR #193 is the remaining `codex/v2-completion-track` to `main` merge
  candidate. At the checked baseline it is open, ready, mergeable, and `CLEAN`.
- PR #202 was squash-merged into `codex/v2-completion-track` at
  `50aa6bf071b31f1d78f0c1476dff1936f29a3524`.
- PR #203 was squash-merged into `codex/v2-completion-track` at
  `a80876fa5a03d021a98c588e4f4d3fabc3826e66`.
- GitHub checks: no checks reported on PR #193 at the checked baseline.

## Item Map

Evidence paths are completion-track candidate scoped until PR #193 lands on
`main`. The PR column identifies where each item was originally reviewed or is
currently carried; do not claim `main` evidence until the file exists on `main`
after merge.

| Item | Candidate status | Origin PR / carrier | Evidence | Merge note |
| ---: | --- | --- | --- | --- |
| 1 | `Deferred` | #200 `docs: define v2 operational upload verification gate` | `docs/173_v2_operational_upload_verification_gate.md` defines fresh inventory, Preview-only, Start Upload, Retry Failed, safe evidence, stop conditions, and rollback boundaries. `$review` clean. | Does not run or approve operational upload. |
| 2 | `Completed` | #193 `docs: record v2 package runtime evidence` | `docs/166_v2_api_mode_package_runtime_evidence.md` records API-mode build, package assembly, zip/SHA-256 metadata, launcher/shortcut `-CheckOnly`, read-only HTTP smoke, and item 2 `$review` result. | Does not replace the accepted mutation package in `docs/164_operator_data_mutation_safety_gate.md`. |
| 3 | `Deferred` | #195 `[codex] add v2 date-scoped delete review gate` | `docs/168_v2_date_scoped_delete_ui_gate.md` records the default-off, non-mutating review shell and evidence; executable operator-facing date-scoped delete remains blocked. `$review` clean. | Gate enablement, preflight/start, role enforcement, fixture evidence, and rollback remain separate. |
| 4 | `Deferred` | #197 `docs: define v2 delete expansion fixture gate` | `docs/170_v2_delete_expansion_fixture_gate.md` defines fixture-first delete expansion gate, limits, reconcile, audit, rollback, and production block boundaries. `$review` clean. | No fixture or production mutation approved. |
| 5 | `Deferred` | #198 `docs: define v2 operational delete verification gate` | `docs/171_v2_operational_delete_verification_gate.md` defines immutable or append-only approval storage, exact scope, no-undo acknowledgement, safe evidence report, and blocked rollback semantics. `$review` clean. | No operational DB delete approved. |
| 6 | `Deferred` | #199 `feat: add v2 LAN security gate` | `docs/172_v2_lan_security_gate.md` records the default-off LAN security code guard, sanitized health state, launcher reuse guard, backend/frontend/package validation, and package read-only smoke evidence. `$review` clean. | Multi-user LAN remains disabled; shared local token is not LAN identity. |
| 7 | `Completed` | #194 `feat: expose vector observability status` | `docs/167_v2_observability_hardening_evidence.md` and code expose sanitized Grafana/Vector status classes, Vector non-required runtime behavior, alert/runbook classes, package/runtime checks, and raw observability export exclusions. `$review` clean. | Grafana iframe, raw log/metric/trace export, LAN, reset/cleanup, and operator mutation remain excluded. |
| 8 | `Deferred` | #196 `docs: define v2 supabase attribution schema gate` | `docs/169_v2_supabase_schema_attribution_design.md` defines schema attribution migration/backfill/rollback/test design while preserving sidecar compatibility and `all_metrics(timestamp, device_id)` upsert safety. `$review` clean. | No Supabase schema migration or backfill approved. |

## PR Stack State

Current landing state after the completion-track integration:

| PR | Base | Head | State | Merge interpretation |
| ---: | --- | --- | --- | --- |
| #193 | `main` | `codex/v2-completion-track` | open | Remaining main merge candidate; do not merge until the docs readiness fix and `$review` are complete. |
| #202 | `codex/v2-completion-track` | `codex/v2-completion-stack-rehearsal` | merged | Integration vehicle for the reviewed item PRs and rollup evidence; do not request or approve this merge again. |
| #203 | `codex/v2-completion-track` | `codex/vector-start-stop-symmetry` | merged | Runtime start/stop symmetry follow-up; included in the `a80876f` completion-track candidate baseline. |

Earlier item PRs #194 through #201 are represented in the merged PR #202
integration path for this candidate. Treat their individual GitHub state as
historical for the current landing path unless the team intentionally reopens an
item-by-item landing strategy and reruns the corresponding reviews.

## Pre-Merge Rehearsal

Read-only/synthetic merge rehearsal on 2026-06-22 Asia/Seoul did not update
branch refs or the working tree.

- #194 into `origin/codex/v2-completion-track`:
  `git merge-tree --write-tree --messages origin/codex/v2-completion-track
  origin/codex/v2-observability-hardening` exited 0 and produced synthetic
  tree `dcfe709eb3af0e66cca19ccab730e55fb976f015`.
- #195 into the synthetic tree after #194:
  `git merge-tree --write-tree --messages
  --merge-base=origin/codex/v2-completion-track
  dcfe709eb3af0e66cca19ccab730e55fb976f015
  origin/codex/v2-date-delete-ui` exited 1 with a content conflict in
  `docs/165_v2_status_matrix.md`.
- In that same rehearsal step, `CHANGELOG.md`, `frontend/src/i18n/locales/en.json`,
  and `frontend/src/i18n/locales/ko.json` auto-merged, but the run stopped at
  the first cumulative conflict.

Interpretation: individual PR `CLEAN` status is not enough. The first known
cumulative conflict is `docs/165_v2_status_matrix.md` after #194 then #195, and
the full stack must not be described as integrated until every cumulative
conflict is resolved and reviewed explicitly.

## Local Integration Rehearsal Update

A separate local-only rehearsal branch,
`codex/v2-completion-stack-rehearsal`, merged the PR heads for #194 through
#201 onto `origin/codex/v2-completion-track` without updating remote refs,
landing to `main`, deploying, or running any operational mutation.

The rehearsal confirmed these cumulative conflict points:

- #195 after #194: `docs/165_v2_status_matrix.md`.
- #196 after #194-#195: `CHANGELOG.md` and
  `docs/165_v2_status_matrix.md`.
- #197 after #194-#196: `CHANGELOG.md` and
  `docs/165_v2_status_matrix.md`.
- #198 after #194-#197: `CHANGELOG.md` and
  `docs/165_v2_status_matrix.md`.
- #199 after #194-#198: `CHANGELOG.md` and
  `docs/165_v2_status_matrix.md`.
- #200 after #194-#199: `CHANGELOG.md` and
  `docs/165_v2_status_matrix.md`.
- #201 after #194-#200: `CHANGELOG.md`.

Conflict resolution preserved all referenced evidence documents from
`docs/166` through `docs/173`, kept items 1, 3, 4, 5, 6, and 8 as `Deferred`,
kept items 2 and 7 as `Completed`, and kept the default-off LAN security guard
separate from full Multi-user LAN approval.

PR #202 exposed that rehearsal as a review-ready integration PR against
`codex/v2-completion-track` and was later squash-merged into the completion
track. It is an integration vehicle for the reviewed PR heads and the follow-up
runtime observability fixes; it is not approval to run operator mutations or a
claim that V2 is fully operational.

## Local Rehearsal Validation

Validation from `codex/v2-completion-stack-rehearsal` at commit `f98524e`:

- `git diff --check`: passed.
- Conflict marker scan across `CHANGELOG.md`, `README.md`, `docs`, `backend`,
  `frontend`, `launcher`, `tests`, and `packaging`: no conflict markers found.
- `.\.venv\Scripts\python -m pytest tests\backend`: `361 passed, 18 warnings`.
- `cd frontend; npm run typecheck; npm run build:api`: passed.
- `.\packaging\assemble_operator_package.ps1 -FrontendMode api`: passed.
- `.\packaging\assemble_operator_package.ps1 -FrontendMode api -CreateZip`:
  passed.
- Generated package launcher `.\launcher\start_web_console.ps1 -CheckOnly`:
  passed; no backend process was started.
- Generated package shortcut installer
  `.\launcher\install_shortcuts.ps1 -CheckOnly`: passed; no shortcuts were
  written.
- Generated package read-only HTTP smoke with
  `.\launcher\start_web_console.ps1 -NoBrowser -RequireFreshBackend -BackendPort 8010`:
  passed. The smoke called `/`, `/upload`, `/logs`, `/settings`,
  `/api/health`, `/api/config`, `/api/audit?limit=1`, and
  `/api/runtime/local-supabase`. Every route returned HTTP 200.
- Sanitized runtime smoke fields from `/api/runtime/local-supabase`:
  - `overallStatus`: `attention`
  - `grafana.status`: `unreachable`
  - `vector.status`: `unhealthy`
  - `vector.detail`: `Vector container status class is unhealthy.`
- The smoke backend was stopped after the run and port 8010 was confirmed
  closed.
- Package metadata:
  - `packageLabel`: `ExtrusionWebConsole-f98524e-20260621-224425-557`
  - `sourceCommit`: `f98524e`
  - `runtimeMode`: `operator-ready`
  - `frontendMode`: `api`
  - `zipCreated`: `true`
  - `zipSha256`:
    `4addd94b5be5f157a65395f00af7601c403995bbc6a42200893352323c7542a4`
- Codex read-only adversarial review found two runtime observability findings
  before commit `f98524e`; the commit blocks Start on non-core attention and
  maps Docker `Restarting` container status to `unhealthy` instead of
  `stopped`.
- A later Codex read-only adversarial review found that `docs/172` overstated
  the LAN guard's ability to prevent unsupported direct non-loopback Uvicorn
  socket binds. `docs/172` now states the actual boundary: supported
  operator/package starts must use the launcher, request middleware rejects
  remote requests after they reach the app, and direct
  `uvicorn ... --host 0.0.0.0` starts remain out of scope.
- Final Codex read-only adversarial review after the LAN boundary correction:
  no actionable findings.
- Follow-up Codex read-only review for item 2 package evidence in `docs/166`
  and `docs/165`: no actionable findings. The review checked overclaim risk,
  raw path or secret leakage, rollback coverage, and safety boundaries.

This read-only smoke does not approve Upload Preview, Start Upload, Retry
Failed, Delete, Settings save, feature-gate enablement, LAN exposure, deploy,
Supabase reset/cleanup, Docker cleanup, or any operational DB mutation.

## Post-Merge Runtime Review Follow-Up

After PR #202 was squash-merged into `codex/v2-completion-track` at commit
`50aa6bf071b31f1d78f0c1476dff1936f29a3524`, an independent read-only
`$review` found one runtime-control blocker: Runtime Stop can stop the
non-required Vector container, but Runtime Start only restarted required
containers and therefore left an existing stopped Vector container unrecoverable
without an out-of-scope reset, cleanup, or manual Docker action.

The follow-up branch `codex/vector-start-stop-symmetry` fixes that asymmetry by
allowing Runtime Start to restart an already-existing stopped
`supabase_vector_*` container while keeping missing, unhealthy, or unknown
Vector states as non-core runtime attention. This does not approve or implement
Supabase reset/cleanup, Docker cleanup, broad container deletion, LAN exposure,
operator mutation, or deploy.

Follow-up validation on `codex/vector-start-stop-symmetry`:

- targeted runtime-control tests for stopped Vector recovery, unhealthy started
  Vector timeout, existing runtime noop, and required container missing
  behavior: `4 passed, 1 warning`;
- `git diff --check`: passed;
- backend runtime/API/health tests:
  `.\.venv\Scripts\python -m pytest tests\backend\test_runtime_control.py tests\backend\test_runtime_api.py tests\backend\test_health.py`
  returned `35 passed, 2 warnings`;
- full backend tests: `362 passed, 18 warnings`;
- API-mode package assembly:
  `.\packaging\assemble_operator_package.ps1 -FrontendMode api` passed;
- independent read-only `$review`: first pass requested the unhealthy started
  Vector readiness fix; after that fix, rerun reported
  `No actionable findings.`

## Package Verification Evidence

Static entries in this section are verification samples. They document what was
checked locally at a point in time, but they are not evergreen approval evidence
after docs-only commits change PR #193 `headRefOid`.

Previous completion-track refresh sample after PR #203:

- `packageLabel`: `ExtrusionWebConsole-a80876f-20260622-003633-680`
- `sourceCommit`: `a80876f`
- `createdUtc`: `2026-06-22T00:36:40.1122717Z`
- `frontendMode`: `api`
- `runtimeMode`: `operator-ready`
- `frontendBuildMetadataPresent`: `true`
- `zipCreated`: `false`
- `zipSha256`: `not_applicable`

Latest local PR #193 precheck sample after PR #204:

- `packageLabel`: `ExtrusionWebConsole-e405fcd-20260622-024709-519`
- `sourceCommit`: `e405fcd`
- `createdUtc`: `2026-06-22T02:47:16.2854392Z`
- `frontendMode`: `api`
- `runtimeMode`: `operator-ready`
- `frontendBuildMetadataPresent`: `true`
- `zipCreated`: `false`
- `zipSha256`: `not_applicable`

Package-local `-CheckOnly` refreshes on 2026-06-22 Asia/Seoul passed for the
launcher and shortcut installer. Launcher checks did not start backend
processes, and shortcut checks did not write shortcuts.

Before PR #193 main merge approval, recheck the actual handoff package
`package-build-info.json`. If its `sourceCommit` does not match the current PR
#193 `headRefOid` short SHA, either rebuild the package from the current head or
mark the package evidence as sample-only and stop the merge.

These package samples are for PR #193 readiness review only. They do not replace
the accepted mutation package in
`docs/164_operator_data_mutation_safety_gate.md` and do not approve Upload
Preview, Start Upload, Retry Failed, Delete, Settings save, feature-gate
enablement, Supabase reset/cleanup, Docker cleanup, LAN exposure, schema
migration, deploy, or operational DB mutation.

## Landing Interpretation

Do not merge this stack as a claim that V2 is fully operational.

Safe landing interpretation after review:

- merge candidate for V2 status, package evidence, and explicit gate boundaries;
- completed narrow scopes: item 2 API-mode package evidence, item 7
  Grafana/Vector observability hardening;
- items 3 and 6 remain `Deferred`; their guard artifacts are evidence only and
  do not enable Delete or LAN;
- deferred operational scopes: item 1 operational upload, executable item 3
  date-scoped delete UI, item 4 delete expansion execution, item 5 operational
  DB delete verification, full item 6 Multi-user LAN, and item 8 Supabase schema
  attribution.

## Suggested Merge Order

No merge is approved by this document.

If the user approves landing later, use one deliberate sequence:

1. Do not merge PR #202 or PR #203 again; both are already represented in
   `codex/v2-completion-track`.
2. Land any docs readiness fix into `codex/v2-completion-track` if it is not
   already present, then confirm PR #193 points at the refreshed completion
   branch and remains `CLEAN`.
3. Immediately before approval, verify the actual handoff package
   `package-build-info.json`:
   - `sourceCommit` must match the current PR #193 `headRefOid` short SHA;
   - `frontendMode` must be `api`;
   - `runtimeMode` must be `operator-ready`;
   - `frontendBuildMetadataPresent` must be `true`;
   - when `zipCreated=false`, `zipSha256` is `not_applicable`;
   - when `zipCreated=true`, verify the generated zip SHA-256 sidecar.
4. Rerun verification from the updated completion branch:
   - `git diff --check`
   - `.\.venv\Scripts\python -m pytest tests\backend`
   - `cd frontend; npm run typecheck; npm run build:api`
   - `.\packaging\assemble_operator_package.ps1 -FrontendMode api`
   - `.\packaging\assemble_operator_package.ps1 -FrontendMode api -CreateZip`
   - package launcher/shortcut `-CheckOnly`
   - read-only package HTTP smoke
   - `$review`
5. Only after the refreshed completion branch and approval-time package metadata
   verification pass, merge PR #193 to `main`.
6. After the `main` merge, either prove that `main` HEAD is the exact tested
   completion commit or rerun the verification above from `main` before
   describing `main` as a V2 completion candidate.

## Required Approval Wording

To merge PR #193 from `codex/v2-completion-track` to `main`, the approval must
be explicit and narrow:

```text
I approve merging PR #193 from codex/v2-completion-track to main.
This approval is only for the reviewed V2 completion-track candidate at headRefOid <current PR #193 headRefOid>.
This approval does not approve Upload Preview, Start Upload, Retry Failed, Delete, Settings save, feature gate enablement, Supabase reset/cleanup, Docker cleanup, LAN exposure, schema migration, deploy, or operational DB mutation.
```

Before using the approval, replace `<current PR #193 headRefOid>` with the exact
`headRefOid` reported by GitHub at approval time. If that head differs from the
last reviewed completion-track candidate, rerun `git diff --check`, package
validation evidence review, and `$review` before using the approval. Also
record the actual handoff package `package-build-info.json` metadata checked at
approval time; static package samples above are not sufficient for approval.

## Stop Conditions

Stop and do not claim V2 completion when any of these are true:

- PR #193 is not mergeable, not `CLEAN`, or not pointing at the exact reviewed
  completion-track candidate;
- PR #202 or PR #203 merge commits are absent from the completion-track
  candidate being reviewed;
- any docs readiness fix required by `$review` is absent from the completion
  branch;
- any referenced evidence file is absent from the target branch after its
  corresponding PR merge;
- `docs/165_v2_status_matrix.md` classifications do not match this rollup:
  items 1, 3, 4, 5, 6, and 8 must remain `Deferred`; items 2 and 7 must be
  `Completed`;
- package metadata and source commits in evidence docs do not match the merged
  package, unless those entries are explicitly marked sample-only and
  approval-time `package-build-info.json` verification is performed;
- GitHub checks or local verification fail;
- operational approval text is missing for any requested mutation;
- raw source paths, filenames, exact keys, DB URLs, tokens, raw SQL, or secrets
  would enter committed evidence;
- a request bundles Upload Preview, Start Upload, Retry Failed, Delete,
  Settings save, feature-gate enablement, reset, cleanup, LAN, or deploy into
  one broad approval.

## Rollback

Before commit, inspect the diff and revert only the rollup document hunk and
matching `docs/165`, `docs/166`, or CHANGELOG hunks after confirming no
unrelated working-tree changes share those files.

After commit, revert the specific rollup document commit.

No operational evidence, local state DB, Supabase data, Docker state, package
output, LAN configuration, or source files should be deleted as rollback for
this document.
