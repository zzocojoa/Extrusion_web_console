# V2 Completion Candidate Rollup

Date: 2026-06-22 Asia/Seoul

Status: `candidate_pr_stack_not_merged`

## Purpose

This document records the current V2 completion-candidate PR stack for the eight
remaining V2 items.

It does not approve merge, deployment, LAN exposure, Upload Preview, Start
Upload, Retry Failed, Delete, Settings save, feature-gate enablement, Supabase
reset/cleanup, Docker cleanup, schema migration, operational DB mutation, or
source-file mutation.

`main` is not yet a V2 completion candidate until the relevant PRs are reviewed,
merged in a deliberate order, and the post-merge verification is rerun from the
merged branch.

## Baseline

- `origin/main`: `baee4982d8be9f6ef8e44b4a8ca6f1a30a382222`
- V2 stack base: `origin/codex/v2-completion-track`
  `b6f11ad26c51440341f2663480b33e079abb4202`
- Current rollup branch: `codex/v2-completion-candidate-rollup`
- Open PRs reviewed for this rollup: #193 through #200
- Current rollup PR: #201
- GitHub checks: no checks reported on the reviewed branches at rollup time

## Item Map

Evidence paths are PR-scoped until their corresponding PR is merged into the
target branch. Do not land a rollup that references evidence files absent from
the target branch after the corresponding PR merge.

| Item | Candidate status | PR | Evidence | Merge note |
| ---: | --- | --- | --- | --- |
| 1 | `Deferred` | #200 `docs: define v2 operational upload verification gate` | `docs/173_v2_operational_upload_verification_gate.md` defines fresh inventory, Preview-only, Start Upload, Retry Failed, safe evidence, stop conditions, and rollback boundaries. `$review` clean. | Does not run or approve operational upload. |
| 2 | `Completed` | #193 `docs: record v2 package runtime evidence` | `docs/166_v2_api_mode_package_runtime_evidence.md` records API-mode build, package assembly, zip/SHA-256 metadata, launcher/shortcut `-CheckOnly`, and read-only HTTP smoke. | Does not replace the accepted mutation package in `docs/164_operator_data_mutation_safety_gate.md`. |
| 3 | `Deferred` | #195 `[codex] add v2 date-scoped delete review gate` | `docs/168_v2_date_scoped_delete_ui_gate.md` records the default-off, non-mutating review shell and evidence; executable operator-facing date-scoped delete remains blocked. `$review` clean. | Gate enablement, preflight/start, role enforcement, fixture evidence, and rollback remain separate. |
| 4 | `Deferred` | #197 `docs: define v2 delete expansion fixture gate` | `docs/170_v2_delete_expansion_fixture_gate.md` defines fixture-first delete expansion gate, limits, reconcile, audit, rollback, and production block boundaries. `$review` clean. | No fixture or production mutation approved. |
| 5 | `Deferred` | #198 `docs: define v2 operational delete verification gate` | `docs/171_v2_operational_delete_verification_gate.md` defines immutable or append-only approval storage, exact scope, no-undo acknowledgement, safe evidence report, and blocked rollback semantics. `$review` clean. | No operational DB delete approved. |
| 6 | `Deferred` | #199 `feat: add v2 LAN security gate` | `docs/172_v2_lan_security_gate.md` records the default-off LAN security code guard, sanitized health state, launcher reuse guard, backend/frontend/package validation, and package read-only smoke evidence. `$review` clean. | Multi-user LAN remains disabled; shared local token is not LAN identity. |
| 7 | `Completed` | #194 `feat: expose vector observability status` | `docs/167_v2_observability_hardening_evidence.md` and code expose sanitized Grafana/Vector status classes, Vector non-required runtime behavior, alert/runbook classes, package/runtime checks, and raw observability export exclusions. `$review` clean. | Grafana iframe, raw log/metric/trace export, LAN, reset/cleanup, and operator mutation remain excluded. |
| 8 | `Deferred` | #196 `docs: define v2 supabase attribution schema gate` | `docs/169_v2_supabase_schema_attribution_design.md` defines schema attribution migration/backfill/rollback/test design while preserving sidecar compatibility and `all_metrics(timestamp, device_id)` upsert safety. `$review` clean. | No Supabase schema migration or backfill approved. |

## PR Stack State

At rollup time:

| PR | Base | Head | State | Draft | Merge state |
| ---: | --- | --- | --- | --- | --- |
| #193 | `main` | `codex/v2-completion-track` | open | no | `CLEAN` |
| #194 | `codex/v2-completion-track` | `codex/v2-observability-hardening` | open | no | `CLEAN` |
| #195 | `codex/v2-completion-track` | `codex/v2-date-delete-ui` | open | no | `CLEAN` |
| #196 | `codex/v2-completion-track` | `codex/v2-schema-attribution-design` | open | no | `CLEAN` |
| #197 | `codex/v2-completion-track` | `codex/v2-delete-expansion-gate` | open | no | `CLEAN` |
| #198 | `codex/v2-completion-track` | `codex/v2-operational-delete-verification-gate` | open | no | `CLEAN` |
| #199 | `codex/v2-completion-track` | `codex/v2-lan-security-gate` | open | no | `CLEAN` |
| #200 | `codex/v2-completion-track` | `codex/v2-operational-upload-verification-gate` | open | no | `CLEAN` |
| #201 | `codex/v2-completion-track` | `codex/v2-completion-candidate-rollup` | open | no | `CLEAN` |

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

## Local Rehearsal Validation

Validation from `codex/v2-completion-stack-rehearsal` at commit `a4d55e4`:

- `git diff --check`: passed.
- Conflict marker scan across `CHANGELOG.md`, `README.md`, `docs`, `backend`,
  `frontend`, `launcher`, `tests`, and `packaging`: no conflict markers found.
- `.\.venv\Scripts\python -m pytest tests\backend`: `360 passed, 18 warnings`.
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
  - `vector.status`: `stopped`
  - `vector.detail`: `Vector container status class is stopped.`
- The smoke backend was stopped after the run and port 8010 was confirmed
  closed.
- Package metadata:
  - `packageLabel`: `ExtrusionWebConsole-a4d55e4-20260621-222940-214`
  - `sourceCommit`: `a4d55e4`
  - `runtimeMode`: `operator-ready`
  - `frontendMode`: `api`
  - `zipCreated`: `true`
  - `zipSha256`:
    `7bfbeecd6482be1d92aa4a459d569f16409894ee4501920721f0a21d4c4cc254`
- Codex read-only adversarial review against
  `origin/codex/v2-completion-track`: no actionable findings.

This read-only smoke does not approve Upload Preview, Start Upload, Retry
Failed, Delete, Settings save, feature-gate enablement, LAN exposure, deploy,
Supabase reset/cleanup, Docker cleanup, or any operational DB mutation.

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

1. Keep #193 open. Do not merge #193 into `main` at this step.
2. Merge item PRs #194 through #200 into `codex/v2-completion-track`.
   Resolve every conflicted file explicitly. `docs/165_v2_status_matrix.md`
   and `CHANGELOG.md` are expected conflict points, not an exhaustive conflict
   list. The pre-merge rehearsal already found a `docs/165_v2_status_matrix.md`
   conflict after #194 then #195. Record the final conflict review result
   before continuing.
3. After #194 through #200 are merged, update or rebase #201 onto the refreshed
   `codex/v2-completion-track`, resolve `CHANGELOG.md` and rollup-document
   conflicts explicitly, rerun `git diff --check` and `$review`, and merge #201
   into `codex/v2-completion-track` only if the rollup still matches the
   refreshed stack.
4. Confirm #193 now points at the refreshed `codex/v2-completion-track` that
   includes the reviewed #194 through #201 results.
5. Rerun verification from the updated completion branch:
   - `git diff --check`
   - `.\.venv\Scripts\python -m pytest tests\backend`
   - `cd frontend; npm run typecheck; npm run build:api`
   - `.\packaging\assemble_operator_package.ps1 -FrontendMode api`
   - `.\packaging\assemble_operator_package.ps1 -FrontendMode api -CreateZip`
   - package launcher/shortcut `-CheckOnly`
   - read-only package HTTP smoke
   - `$review`
6. Only after the merged completion branch passes, merge the refreshed
   completion branch to `main`.
7. After the `main` merge, either prove that `main` HEAD is the exact tested
   completion commit or rerun the verification above from `main` before
   describing V2 as a completion candidate.

## Stop Conditions

Stop and do not claim V2 completion when any of these are true:

- any PR above is not merged or is merged without conflict review;
- the known cumulative `docs/165_v2_status_matrix.md` conflict is not resolved
  and reviewed explicitly;
- any referenced evidence file is absent from the target branch after its
  corresponding PR merge;
- `docs/165_v2_status_matrix.md` classifications do not match this rollup:
  items 1, 3, 4, 5, 6, and 8 must remain `Deferred`; items 2 and 7 must be
  `Completed`;
- package metadata and source commits in evidence docs do not match the merged
  package;
- GitHub checks or local verification fail;
- operational approval text is missing for any requested mutation;
- raw source paths, filenames, exact keys, DB URLs, tokens, raw SQL, or secrets
  would enter committed evidence;
- a request bundles Upload Preview, Start Upload, Retry Failed, Delete,
  Settings save, feature-gate enablement, reset, cleanup, LAN, or deploy into
  one broad approval.

## Rollback

Before commit, inspect the diff and revert only the rollup document hunk and
the matching CHANGELOG hunk after confirming no unrelated working-tree changes
share those files.

After commit, revert the specific rollup document commit.

No operational evidence, local state DB, Supabase data, Docker state, package
output, LAN configuration, or source files should be deleted as rollback for
this document.
