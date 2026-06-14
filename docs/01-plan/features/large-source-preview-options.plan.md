# large-source-preview-options - Plan Document

> Version: 1.0.0 | Date: 2026-06-14 | Status: Draft
> Level: Dynamic

---

## 1. Overview

### 1.1 Purpose
Add an explicit Upload Preview mode for large operational CSV sources so operators can run a longer Preview from the Web Console UI instead of calling the API manually.

### 1.2 Background
Preview run `prv_f54d56d8836c` timed out at `timeoutStage=extract`. The PR #144 staging reconciler was active, but DB matching was never reached because default UI limits remained `maxRunSeconds=120` and `maxFileSeconds=30`.

## 2. Goals

### 2.1 Primary Goals
- [ ] Preserve the existing quick/default Preview behavior.
- [ ] Add an explicit operator-selected large-source Preview profile.
- [ ] Keep Start Upload disabled unless Preview succeeds, DB is reachable, and target rows exist.
- [ ] Avoid automatic Preview execution.

### 2.2 Non-Goals
- Do not change Upload Job execution behavior.
- Do not run Preview, Start Upload, Retry Failed, duplicate rerun, or full rollout during implementation.
- Do not change Supabase, Docker, DB lifecycle, or destructive operations.

## 3. Scope

### 3.1 In Scope
- Backend Preview profile defaults for large operational sources.
- Frontend Preview request builder for the large-source profile.
- Upload page mode selector with normal vs large-source modes.
- Targeted backend test coverage and frontend type/build validation.

### 3.2 Out of Scope
- Upload execution changes.
- DB schema changes.
- Edge function changes.
- Runtime lifecycle controls.

## 4. Success Criteria

- [ ] Default Preview still sends the short interactive option set.
- [ ] Large-source Preview sends `maxRunSeconds=900`, `maxFileSeconds=300`, `forceFullScan=false`, and conservative DB chunking.
- [ ] UI clearly distinguishes normal Preview from large-source Preview.
- [ ] Start Upload gating remains unchanged.
- [ ] Tests and type/build checks pass.

## 5. Schedule

| Phase | Target Date | Status |
|-------|------------|--------|
| Plan | 2026-06-14 | In Progress |
| Design | 2026-06-14 | Pending |
| Implementation | 2026-06-14 | Pending |
| Review | 2026-06-14 | Pending |

## 6. Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Operators mistake large-source Preview for upload approval | High | Medium | Keep Start Upload gate unchanged and label mode as Preview-only behavior |
| Default quick Preview behavior changes | Medium | Low | Add DTO test for default profile and keep UI default set to standard |
| Long Preview hides timeout details | Medium | Low | Reuse PR #144 timing and timeoutStage fields |

## 7. References

- `docs/136_operator_preview_reconciliation_scaling_plan.md`
- `docs/137_operator_preview_reconciliation_staging_reconciler.md`
- `backend/app/schemas/upload_preview.py`
- `frontend/src/pages/UploadPage.tsx`
