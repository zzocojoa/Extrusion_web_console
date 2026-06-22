# V2 API-Mode Package Runtime Evidence

Date: 2026-06-22 Asia/Seoul

Status: `candidate_package_runtime_smoke_passed`

## Purpose

This document records non-mutating API-mode package validation evidence for the
V2 completion track.

This evidence does not approve Upload Preview, Start Upload, Retry Failed,
Delete, Settings save, feature-gate enablement, Supabase reset/cleanup, Docker
cleanup, LAN exposure, deployment, or any operational data mutation.

`docs/164_operator_data_mutation_safety_gate.md` remains the mutation approval
gate. Do not treat this package smoke as permission to replace the accepted
mutation package unless that gate is updated by a separate reviewed change.

## Package Evidence Rule

Approval-time package metadata verification is canonical. Before any PR #193
main merge approval, verify the generated package `package-build-info.json`
directly from the package being handed off.

Required approval-time checks:

- `sourceCommit` must match the current PR #193 `headRefOid` short SHA, unless
  the entry is explicitly marked as sample-only;
- `frontendMode` must be `api`;
- `runtimeMode` must be `operator-ready`;
- `frontendBuildMetadataPresent` must be `true`;
- when `zipCreated=false`, `zipSha256` is `not_applicable`;
- when `zipCreated=true`, the zip SHA-256 must be checked against the generated
  checksum sidecar;
- launcher and shortcut `-CheckOnly` must pass without starting the backend or
  writing shortcuts.

Static package metadata below is historical or sample evidence. Docs-only
follow-up commits can intentionally make a sample package `sourceCommit` older
than the current PR head. In that case the sample remains useful as local
validation history, but it must not be used as final approval evidence.

## Original Item 2 Source

- Branch: `codex/v2-completion-track`
- Source commit: `eedac29`
- Source commit purpose: document-only V2 status matrix baseline correction.
- Frontend build command: `cd frontend; npm run build:api`
- Package command: `.\packaging\assemble_operator_package.ps1 -FrontendMode api`
- Zip handoff command: `.\packaging\assemble_operator_package.ps1 -FrontendMode api -CreateZip`

## Original Item 2 Package Metadata

Candidate package:

- `packageLabel`: `ExtrusionWebConsole-eedac29-20260621-165853-560`
- `sourceCommit`: `eedac29`
- `frontendMode`: `api`
- `runtimeMode`: `operator-ready`
- `zipCreated`: `true`
- `zipSha256`: `6505ca7334ea900799bf473d2edc70c102c732f5b4fd1cb9c248da69b40b9dc1`
- zip size: `13422562` bytes
- checksum sidecar: `6505ca7334ea900799bf473d2edc70c102c732f5b4fd1cb9c248da69b40b9dc1  ExtrusionWebConsole-eedac29-20260621-165853-560.zip`

Package assembly safety output:

- required paths: present
- Supabase assets: present
- operator readiness: ready
- denylist matches: `0`
- redaction matches: `0`
- source cache pruned: `53`
- runtime cache pruned: `1644`
- runtime test segments pruned: `8`
- runtime agent entries pruned: `8`
- runtime metadata preserved: `275`

## Validation

Backend and frontend:

- `.\.venv\Scripts\python -m pytest tests\backend`: `343 passed, 18 warnings`
- `cd frontend; npm run typecheck`: passed
- `cd frontend; npm run build:api`: passed, `frontend build mode: api`
- `git diff --check`: passed

Package checks:

- `launcher/start_web_console.ps1 -CheckOnly`: passed; no backend process was
  started.
- `launcher/install_shortcuts.ps1 -CheckOnly`: passed; no shortcuts were
  written.
- `Get-FileHash -Algorithm SHA256` matched the package metadata and `.sha256`
  sidecar.

Read-only HTTP smoke used a dedicated localhost port and stopped the
launcher-owned backend after verification.

| Route | Status | Expected |
| --- | ---: | --- |
| `/` | `200` | pass |
| `/upload` | `200` | pass |
| `/logs` | `200` | pass |
| `/settings` | `200` | pass |
| `/api/health` | `200` | pass |
| `/api/config` | `200` | pass |
| `/api/audit?limit=1` | `200` | pass |
| `/api/docs` | `404` | pass, operator docs disabled |
| `/api/openapi.json` | `404` | pass, operator docs disabled |

The smoke did not run Upload Preview, Start Upload, Retry Failed, Delete,
Settings save, feature-gate enablement, Supabase reset/cleanup, Docker cleanup,
LAN exposure, or deployment.

## Previous Completion-Track Package Refresh Sample

After PR #202 and PR #203 were merged into `codex/v2-completion-track`, the
completion-track package evidence was refreshed from candidate commit
`a80876fa5a03d021a98c588e4f4d3fabc3826e66`.

Previous sample package metadata:

- `packageLabel`: `ExtrusionWebConsole-a80876f-20260622-003633-680`
- `sourceCommit`: `a80876f`
- `createdUtc`: `2026-06-22T00:36:40.1122717Z`
- `frontendMode`: `api`
- `runtimeMode`: `operator-ready`
- `frontendBuildMetadataPresent`: `true`
- `zipCreated`: `false`
- `zipSha256`: `not_applicable`

Package-local refresh checks:

- `launcher/start_web_console.ps1 -CheckOnly`: passed; no backend process was
  started.
- `launcher/install_shortcuts.ps1 -CheckOnly`: passed; no shortcuts were
  written.

This refresh does not replace the original item 2 zip handoff evidence above,
does not replace the accepted mutation package in
`docs/164_operator_data_mutation_safety_gate.md`, and does not approve Upload
Preview, Start Upload, Retry Failed, Delete, Settings save, feature-gate
enablement, Supabase reset/cleanup, Docker cleanup, LAN exposure, deployment,
or any operational DB mutation.

## Latest Local Verification Sample

After PR #204 was squash-merged into `codex/v2-completion-track`, PR #193
pointed at `headRefOid=e405fcddc0161c4fde48e4e314b642ad8472a0c9`. A local
non-mutating package validation sample was generated from that candidate.

Latest sample package metadata:

- `packageLabel`: `ExtrusionWebConsole-e405fcd-20260622-024709-519`
- `sourceCommit`: `e405fcd`
- `createdUtc`: `2026-06-22T02:47:16.2854392Z`
- `frontendMode`: `api`
- `runtimeMode`: `operator-ready`
- `frontendBuildMetadataPresent`: `true`
- `zipCreated`: `false`
- `zipSha256`: `not_applicable`

Package-local sample checks:

- `launcher/start_web_console.ps1 -CheckOnly`: passed; no backend process was
  started.
- `launcher/install_shortcuts.ps1 -CheckOnly`: passed; no shortcuts were
  written.

This sample does not remove the approval-time verification rule above. If a
later docs-only commit changes PR #193 `headRefOid`, rerun package assembly or
recheck the actual handoff package metadata before approval. Do not treat this
sample as permission for Upload Preview, Start Upload, Retry Failed, Delete,
Settings save, feature-gate enablement, Supabase reset/cleanup, Docker cleanup,
LAN exposure, deployment, schema migration, or operational DB mutation.

## Review

Codex read-only review of this document and `docs/165_v2_status_matrix.md`
reported `No actionable findings.` The review scope was limited to item 2
API-mode package evidence: overclaim risk, raw path or secret leakage,
rollback coverage, and safety boundaries.

The PR-diff command was unavailable inside the read-only review subprocess, so
this review used the current checkout copies of `docs/166` and `docs/165`.

## Rollback

Before merge, rollback this evidence by reverting the documentation commit that
adds this file and updates `docs/165_v2_status_matrix.md` and `CHANGELOG.md`.

After merge, rollback is a normal git revert of that documentation commit. No
operational DB rows, local state DB evidence, Supabase data, Docker state,
runtime logs, AppData config, or package outputs should be deleted as rollback.

If the candidate package is rejected for handoff, supersede it with a later
package and record the replacement evidence. Do not use reset or cleanup as a
package rollback.
