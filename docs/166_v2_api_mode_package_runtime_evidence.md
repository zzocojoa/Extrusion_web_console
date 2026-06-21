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

## Source

- Branch: `codex/v2-completion-track`
- Source commit: `eedac29`
- Source commit purpose: document-only V2 status matrix baseline correction.
- Frontend build command: `cd frontend; npm run build:api`
- Package command: `.\packaging\assemble_operator_package.ps1 -FrontendMode api`
- Zip handoff command: `.\packaging\assemble_operator_package.ps1 -FrontendMode api -CreateZip`

## Package Metadata

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

## Rollback

Before merge, rollback this evidence by reverting the documentation commit that
adds this file and updates `docs/165_v2_status_matrix.md` and `CHANGELOG.md`.

After merge, rollback is a normal git revert of that documentation commit. No
operational DB rows, local state DB evidence, Supabase data, Docker state,
runtime logs, AppData config, or package outputs should be deleted as rollback.

If the candidate package is rejected for handoff, supersede it with a later
package and record the replacement evidence. Do not use reset or cleanup as a
package rollback.
