# Gap Analysis: v1-decommission-plan

> Date: 2026-06-18
> Branch: codex/v1-decommission-plan
> Scope: decommission planning only. No v1 code, legacy files, rollback docs, runtime config, DB state, package artifacts, or operational data are removed by this document.

## Verdict

`do_not_decommission_all_v1_now`

The repository cannot safely stop using every `v1`, `legacy`, `compat`, and
`fallback` concept in one removal PR.

There are three different things mixed under those words:

- Active runtime dependencies that must stay because they are part of the
  current operator path or the Supabase local API shape.
- API/storage compatibility fields that can be removed only after consumer audit,
  dual-write/read migration, and rollback planning.
- Rollback/reference docs and test fixtures that should stay until a separate
  decommission decision explicitly removes the need for historical evidence.

The recommended path is a staged decommission program, not immediate deletion.

## Sources Checked

Read or searched:

- `docs/03-analysis/v1-compatibility-usage-audit.analysis.md`
- `backend/app/core/settings.py`
- `backend/app/core/target_class.py`
- `backend/app/db/upload_job_repository.py`
- `backend/app/services/upload_preview.py`
- `backend/app/core/transform_core.py`
- `frontend/src/api/uploadJobs.ts`
- `launcher/start_web_console.ps1`
- `launcher/start_edge_runtime.ps1`
- `packaging/assemble_operator_package.ps1`
- backend tests under `tests/backend`
- documentation under `docs/`
- `README.md`

Primary search:

```powershell
rg -n "v1|legacy_key|insertedRows|functions/v1|legacy|compat|fallback|rollback" backend frontend launcher tests docs README.md
```

This plan intentionally avoids raw operational source paths, raw operational
filenames, DB URLs, tokens, Authorization values, JWTs, and secret values.

## Removal Decision Matrix

| Item | Current role | Decision | Why |
| --- | --- | --- | --- |
| `/functions/v1/upload-metrics` route in backend settings, target classification, launcher defaults, tests, and docs | Active runtime dependency | Do not remove | `functions/v1` is the Supabase Functions API path convention. Removing or renaming it would break Edge routing and target preflight. |
| `UPLOAD_METRICS_PATH` constant in `backend/app/core/target_class.py` | Active runtime guardrail | Do not remove | It lets target-class preflight prove upload Edge and runtime Edge alignment. |
| `Settings.upload_edge_url` fallback from explicit Edge URL to Supabase URL/local API port | Active Upload Job compatibility | Keep for now | Upload Job execution still supports explicit `supabaseEdgeUrl`, then `supabaseUrl`, then local runtime-derived URL. Runtime readiness already avoids the wrong fallback path. |
| Legacy PLC aliases, encoded column mappings, and legacy time normalization in `backend/app/core/transform_core.py` | Active CSV compatibility | Do not remove | Current upload reader still uses these mappings for representative historical PLC/temperature CSVs. |
| Legacy PLC leading-date filename parser in `backend/app/services/upload_preview.py` | Active Preview eligibility | Do not remove | Preview date-window eligibility still accepts historical PLC filename shape. Removing it would make valid historical source files ineligible. |
| `insertedRows` API/event fields in backend and frontend | Deprecated API compatibility | Hold for staged removal | Canonical field is `acceptedRows`, but backend still emits and frontend still reads `insertedRows`. Removal needs consumer audit and API contract migration. |
| SQLite `inserted_rows` column | Persisted storage compatibility | Hold for schema migration | Renaming/removing needs migration, backfill, downgrade plan, and repository test updates. |
| `upload_file_state.legacy_key` column and computed value | Persisted state compatibility | Hold for schema migration | This is active SQLite state identity. Name is confusing, but removal is a DB migration, not cleanup. |
| `FrontendMode auto` and `frontendMode=unknown` package metadata handling | Package compatibility | Hold | API-mode release already requires explicit `-FrontendMode api`; auto/unknown keeps mock/default package assembly backward-compatible. |
| Legacy transform comparison tests and legacy fixture names | Test fixture only | Keep until replacement coverage exists | These tests verify parity for historical data formats. Removing them first would hide parser regressions. |
| Explicit legacy runtime fallback docs | Rollback/reference | Do not remove | Current policy says fallback is explicit only, not default. The knowledge remains useful until a separate decommission approval. |
| Historical v1 scope/design docs | Historical reference | Keep or annotate | They explain why Core Ops scope exists. Remove only after a documentation archive plan. |
| Operator-facing phrase "v1 does not create a new local Supabase stack" | Copy/docs cleanup candidate | Removable wording only | Behavior must stay. Copy can be modernized to avoid implying a current product version. |
| README phrase "Upload Preview v1" and similar current-status wording | Docs cleanup candidate | Removable wording only | Can be rewritten to "Upload Preview" or "Core Ops Preview" without changing behavior. |

## Immediate Removal Candidates

No runtime code should be deleted immediately.

Safe docs/copy-only candidates for a future small PR:

| Candidate | Required change | Risk |
| --- | --- | --- |
| Current operator copy that says `v1 does not create a new local Supabase stack` | Reword to "Runtime control does not create a new local Supabase stack." | Low, if tests assert reason code rather than exact prose. |
| README current-status phrase `Upload Preview v1` | Reword to `Upload Preview` or `Core Ops Upload Preview`. | Low. |
| Current docs that use `v1` only as a stale status label | Add supersession notes or reword to `Core Ops baseline`. | Low, but historical docs should be annotated rather than rewritten. |

These do not decommission compatibility. They only reduce naming confusion.

## Removal Blockers

| Blocker | Blocks removal of | Evidence to collect before PR |
| --- | --- | --- |
| Supabase route contract | `/functions/v1/upload-metrics` | Official local Supabase route behavior or replacement route support. Until then, do not change. |
| Unknown external consumers | `insertedRows` response/event alias | Search scripts, package docs, operator tooling, PR history, and any support notebooks for `insertedRows`. |
| Persisted SQLite schema | `inserted_rows`, `legacy_key` | Migration design, backfill query, downgrade behavior, repository tests, and state DB compatibility plan. |
| Operational CSV history | legacy parser/date compatibility | Current production source sample classification that proves no valid files need legacy formats. |
| Rollback obligations | legacy fallback docs/reference docs | Separate decommission approval stating rollback knowledge can be archived or removed. |
| Package release support | `FrontendMode auto`, mock/default package compatibility | Decision that mock/default package line is no longer supported and API-mode package is the only maintained handoff line. |

## Staged Decommission Plan

### Phase 0: Consumer And Data Audit

Goal: prove what is safe to remove.

Required evidence:

- Search all repository code, docs, tests, package scripts, and operator notes for
  `insertedRows`, `inserted_rows`, and `legacy_key`.
- Search any maintained external operator scripts or handoff materials, if any,
  for the same fields.
- Sample current operational source metadata without exposing raw paths or
  filenames. Record only source class, accepted filename pattern classes, and
  counts.
- Confirm whether mock/default package assembly remains supported.

Stop conditions:

- Any external consumer still reads `insertedRows`.
- Any active source still includes historical PLC/temperature formats.
- Any operator rollback process still depends on legacy reference docs.

### Phase 1: Names And Docs Cleanup

Goal: reduce confusion without changing behavior.

Allowed changes:

- Reword user-facing "v1" copy to "Core Ops" or "current runtime" where the text
  is not part of a historical record.
- Add notes to historical docs instead of deleting historical details.
- Add schema/API comments explaining why `insertedRows`, `inserted_rows`, and
  `legacy_key` remain.

Tests:

- `python -m pytest tests/backend -q`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run build:api`
- screenshot QA only if UI copy changes.

Rollback:

- Revert the docs/copy PR.

### Phase 2: API Alias Deprecation

Goal: remove `insertedRows` from runtime payloads only after consumers are ready.

Required design:

- Keep `acceptedRows` canonical.
- Add release notes that `insertedRows` is deprecated and scheduled for removal.
- Decide whether one transition release should emit `insertedRows` only in
  backend detail endpoints, job events, both, or neither.
- Update frontend normalization to stop depending on `insertedRows` fallback only
  after backend payload fixtures prove `acceptedRows` is always present.

Tests:

- Upload Job API contract tests.
- Upload Job service tests.
- Frontend API normalization tests if added.
- Full backend test suite and frontend typecheck/build.

Rollback:

- Reintroduce `insertedRows` alias in response mappers and event data.
- No data migration should be coupled to this API alias PR.

### Phase 3: SQLite Schema Migration

Goal: remove or rename confusing storage fields only with a real migration.

Candidate replacements:

| Existing field | Possible replacement | Notes |
| --- | --- | --- |
| `inserted_rows` | `accepted_rows` | Requires backfill and all repository read/write paths to move together. |
| `legacy_key` | `source_file_key` or `folder_filename_key` | Requires new column, backfill, dual-write window, then removal. |

Required migration controls:

- Forward migration that adds replacement columns and backfills existing rows.
- Dual-write period if old package versions may read the same state DB.
- Read fallback from old column during transition.
- Downgrade or revert plan that preserves data.
- State DB backup guidance before migration.

Tests:

- Repository bootstrap on empty DB.
- Repository migration on pre-existing DB with old columns.
- Upload job create/progress/complete/retry flows.
- Audit/event payload assertions.

Rollback:

- Keep old columns until at least one accepted operator period passes.
- If a revert is needed, continue reading old columns and ignore new columns.

### Phase 4: Legacy CSV Compatibility Review

Goal: decide whether historical data-format parsing can be retired.

Required evidence:

- Sanitized source inventory proving all active PLC and temperature files use
  canonical/integrated formats.
- Operator approval that historical CSV upload is no longer required.
- Replacement archive workflow for historical files, if they remain needed for
  audit or reprocessing.

Do not remove before:

- `backend/app/core/transform_core.py` legacy parser tests have replacement
  coverage for the accepted current formats.
- Preview file-date rules prove historical filename patterns are no longer in
  active source.

Rollback:

- Restore legacy parser functions and fixtures.

### Phase 5: Rollback/Reference Archive

Goal: archive, not delete, historical fallback knowledge.

Required approval:

- Named operator/maintainer approval that legacy GUI/runtime fallback is no
  longer an operational continuity path.
- Archive location and discoverability plan.
- Confirmation that release/tag/package formalization is separate and not
  implied by archive work.

Never combine with:

- Runtime DB migration.
- Upload Preview or Start Upload.
- Legacy project/file deletion.

## Keep Until Separate Approval

| Area | Keep item | Reason |
| --- | --- | --- |
| Runtime | `/functions/v1/upload-metrics` | Supabase API route convention. |
| Runtime | Upload Edge URL fallback behavior | Current Upload Job compatibility. |
| Runtime | Legacy CSV transform/date support | Current data compatibility. |
| API | `insertedRows` alias | Deprecated but not yet consumer-audited for removal. |
| Storage | `inserted_rows`, `legacy_key` | Persisted schema migration required. |
| Tests | Legacy transform and preview fixtures | Regression protection. |
| Docs | Rollback/fallback docs | Operational continuity knowledge. |
| Packaging | `FrontendMode auto` and mock/default package support | Backward-compatible package assembly. |

## Pre-Removal PR Checklist

Before any actual decommission PR:

- [ ] Prove the target item is not an active runtime dependency.
- [ ] Identify all API clients and test fixtures that reference it.
- [ ] Write migration design if DB/storage changes are involved.
- [ ] Define rollback and downgrade behavior.
- [ ] Run full backend tests.
- [ ] Run frontend typecheck and API-mode build.
- [ ] Run screenshot QA if UI copy or UI payload display changes.
- [ ] Run marker scan for raw paths, DB URLs, tokens, Authorization values, JWTs,
  secrets, and operational filename markers.
- [ ] Confirm no Upload Preview, Start Upload, Retry Failed, DB/Supabase/Docker
  lifecycle operation, release/tag/package creation, or legacy file deletion is
  included in the PR.

## Verification Plan

For this planning PR:

- `git status --short --branch`
- `rg -n "v1|legacy_key|insertedRows|functions/v1|legacy|compat|fallback|rollback" backend frontend launcher tests docs README.md`
- `python -m pytest tests/backend -q`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run build:api`
- `git diff --check`
- marker scan on the new analysis document and added diff lines

For any future runtime decommission PR, add targeted migration/API tests to the
full validation list above.

## Risk Review

- Rollback path: revert the docs-only decommission plan PR.
- Observability impact: none for this plan. Future API/storage decommission must
  preserve audit and job-event visibility.
- Migration risk: none in this plan. Future `inserted_rows` or `legacy_key`
  changes are migration-bearing and must be handled separately.
- Security impact: this plan records only sanitized route names, field names,
  and file references. It does not expose raw operator paths, operational
  filenames, DB URLs, tokens, Authorization values, JWTs, or secrets.
