# start-upload-review-confirmation - Plan Document

> Version: 1.0.0 | Date: 2026-06-15 | Status: Draft
> Level: Dynamic

---

## 1. Overview

### 1.1 Purpose
Prevent accidental Start Upload execution after a successful Preview by requiring an explicit operator confirmation step in the Upload UI.

### 1.2 Background
The latest API-mode Preview can legitimately reach a Start Upload-ready state. Operational policy still requires target count review and separate approval before DB-mutating upload execution. A single enabled Start Upload button is too easy to click by mistake.

## 2. Goals

### 2.1 Primary Goals
- [ ] Open a confirmation modal instead of starting upload on the first Start Upload click.
- [ ] Show sanitized Preview evidence: preview run id, target files, upload rows, already-in-DB, risky, excluded, and dbStatus.
- [ ] Require the operator to type the exact upload target row count before the modal confirm button is enabled.
- [ ] Preserve existing backend Start Upload guard and upload execution behavior.

### 2.2 Non-Goals
- Do not change backend upload job creation semantics.
- Do not change Retry Failed.
- Do not run Upload Preview, Start Upload, Retry Failed, duplicate rerun, authenticated Edge calls, full rollout, DB reset, Supabase lifecycle, or Docker lifecycle operations.
- Do not display raw source paths, source file content, DB URLs, tokens, Authorization headers, JWTs, or secrets.

## 3. Scope

### 3.1 In Scope
- Upload page Start Upload confirmation modal.
- Mock/demo upload and settings source labels that could be confused with a real PLC source.
- Frontend validation for typed upload row count.
- Korean and English i18n copy.
- Focused CSS for a dense operator modal.
- PDCA plan, design, and analysis documents.

### 3.2 Out of Scope
- Backend API changes.
- Upload execution worker changes.
- Retry Failed confirmation.
- Runtime recovery, Supabase/Docker operations, or production deploy.

## 4. Success Criteria

- [ ] Start Upload cannot be triggered by a single button click from the Preview page.
- [ ] Confirm remains disabled unless Preview is succeeded, DB is reachable, risky count is 0, target files are positive, upload rows are positive, and typed rows match the displayed upload target rows.
- [ ] Modal cancel closes without calling any mutating API.
- [ ] Confirm is the only path that calls the existing Start Upload mutation.
- [ ] Existing backend guard is not weakened.
- [ ] Validation proves no Upload Preview, Start Upload, Retry Failed, duplicate rerun, authenticated Edge call, full rollout, DB/Supabase/Docker lifecycle or destructive work was executed.

## 5. Schedule

| Phase | Target Date | Status |
|-------|------------|--------|
| Plan | 2026-06-15 | In Progress |
| Design | 2026-06-15 | Pending |
| Implementation | 2026-06-15 | Pending |
| Review | 2026-06-15 | Pending |

## 6. Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Confirmation accidentally starts upload | High | Low | Start button only opens modal; actual mutation stays behind confirm handler. Browser smoke will not click confirm. |
| Modal overstates readiness | Medium | Medium | Copy says this is a final review gate, not approval by itself. |
| Backend guard weakened | High | Low | No backend behavior change; targeted backend guard tests still run. |
| Secret/source exposure | High | Low | Modal uses counts and Preview run id only, no file paths or config values. |
| Mock/demo source label misread as active PLC source | Medium | Low | Replace `mock://plc` UI fixture references with neutral demo labels. |

## 7. References

- `AGENTS.md`
- `README.md`
- `DESIGN.md`
- `docs/00_product_scope.md`
- `docs/01_development_roadmap.md`
- `docs/06_dashboard_implementation_spec.md`
- `frontend/src/pages/UploadPage.tsx`
- `frontend/src/api/uploadJobs.ts`
