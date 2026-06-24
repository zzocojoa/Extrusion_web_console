# upload-preview-range-options - Plan Document

> Version: 1.0.0 | Date: 2026-06-24 | Status: Ready for Review
> Level: Dynamic

---

## 1. Overview

### 1.1 Purpose
Extend the Upload Preview range selector so operators can choose recent operational windows without manually entering custom dates.

### 1.2 Background
The Upload page currently exposes `today`, `yesterday`, `last_2_days`, and `custom`. Operators need broader non-custom choices for recent data review and a clearly bounded folder-wide Preview candidate scan.

## 2. Goals

### 2.1 Primary Goals
- [x] Add `last_7_days`, `last_30_days`, and `folder_all` to the backend and frontend range contract.
- [x] Keep backend and frontend range definitions aligned.
- [x] Keep Preview approval scope fail-closed for every new range mode.
- [x] Keep `folder_all` as Preview-only scope expansion, not Start Upload approval.
- [x] Preserve existing Upload Preview safety behavior: configured sources only, top-level CSV only, stable lag, maxFiles, timeout budgets, and file-date metadata rules.

### 2.2 Non-Goals
- Do not execute Upload Preview as part of implementation.
- Do not change Start Upload, Retry Failed, Delete, or Settings save behavior.
- Do not add rangeMode persistence.
- Do not change audit panel CSS.
- Do not run Supabase reset/cleanup, Docker cleanup, LAN/deploy, or operational DB mutation.

## 3. Scope

### 3.1 In Scope
- Upload Preview Plan/Design documentation.
- Backend `PreviewRangeMode`, date-window behavior, auto safe-mode classification, and tests.
- Frontend API type, range selector options, approval-scope label mapping, and i18n strings.
- Existing Upload Preview contract docs that list accepted range modes.
- CHANGELOG entry because this is an operator-facing UI/API contract change.

### 3.2 Out of Scope
- README changes unless the high-level current status becomes inaccurate.
- Runtime, launcher, packaging, Supabase, Docker, and DB lifecycle changes.
- New recursive folder scanning.
- Persisting the selected range in localStorage.
- Any operational Preview or upload run.

## 4. Functional Requirements

| ID | Requirement |
|----|-------------|
| R1 | `last_7_days` means KST current day inclusive, from `current - 6 days` through `current`. |
| R2 | `last_30_days` means KST current day inclusive, from `current - 29 days` through `current`. |
| R3 | `folder_all` scans configured source folder top-level CSV candidates only. It is non-recursive. |
| R4 | `folder_all` keeps stable lag, maxFiles, timeout, file lock, and file-date metadata parsing rules. Files without parseable file dates remain excluded. |
| R5 | `folder_all` does not require `startDate` or `endDate`. Its approval scope start/end dates are `null`. |
| R6 | `folder_all` is a Preview-only gate expansion. It does not approve Start Upload, Retry Failed, Delete, or operational DB mutation. |
| R7 | Approval scope compares `expectedRangeMode` against actual `rangeMode` for new modes and blocks mismatches before run creation. |
| R8 | Large-source operational auto safe mode applies to `last_7_days`, `last_30_days`, and `folder_all`. |

## 5. Success Criteria

- [x] Plan and Design docs exist for `upload-preview-range-options`.
- [x] `docs/07_upload_preview_plan.md` and UI planning docs list the expanded range contract.
- [x] Backend DTO and scanner tests cover `last_7_days`, `last_30_days`, and `folder_all`.
- [x] API contract tests prove new range modes work with approval scope and fail closed on mismatch.
- [x] Frontend typecheck/build accepts the expanded range union and selector labels.
- [x] Screenshot QA runs without executing Upload Preview mutation.

## 6. Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| `folder_all` is misunderstood as recursive or unbounded | High | Medium | Document top-level CSV only, stable lag, maxFiles, timeout, and file-date metadata gates. |
| Operators confuse Preview range with upload approval | High | Medium | UI copy and docs state `folder_all` expands Preview-only scope; Start Upload still requires separate gate and approval. |
| Date-window boundary off by one | Medium | Medium | Add tests for KST current-day inclusive windows. |
| Frontend/backend range mismatch causes 422 | Medium | Low | Update backend enum, frontend type, labels, and approvalScope mapping together. |
| Wider ranges use short timeout budget | Medium | Low | Treat new wide ranges as large preview ranges for auto safe mode. |

## 7. Validation Plan

- `git diff --check`
- `.\.venv\Scripts\python -m pytest tests\backend\test_upload_preview_dtos.py tests\backend\test_upload_preview_reconciliation.py tests\backend\test_upload_preview_api_contract.py`
- `cd frontend; npm run typecheck`
- `cd frontend; npm run build:api`
- `cd frontend; $env:EWC_SCREENSHOT_QA_PORT='5176'; npm run qa:screenshots`

## 8. Rollback

- Before merge: close the branch/PR.
- After merge: revert the squash merge commit.
- Package/installer outputs are not regenerated unless a separate handoff asks for them.

## 9. References

- `docs/07_upload_preview_plan.md`
- `docs/03_ui_ux_plan.md`
- `docs/01-plan/features/large-source-preview-options.plan.md`
- `docs/02-design/features/large-source-preview-options.design.md`
- `backend/app/schemas/upload_preview.py`
- `backend/app/services/upload_preview.py`
- `backend/app/api/upload_preview.py`
- `frontend/src/api/uploadPreview.ts`
- `frontend/src/pages/UploadPage.tsx`
