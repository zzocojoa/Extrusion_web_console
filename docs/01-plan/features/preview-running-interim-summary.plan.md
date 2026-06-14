# preview-running-interim-summary - Plan Document

> Version: 1.0.0 | Date: 2026-06-15 | Status: Draft
> Level: Dynamic

---

## 1. Overview

### 1.1 Purpose
Clarify the Upload Preview UI while a preview run is still active. The current running state can show final-looking zero summary cards and `dbStatus=not_checked` even though the table already contains item-level partial reconciliation results.

### 1.2 Background
After the preview auto-safe mode landed, a large operational preview could run long enough for operators to see partially reconciled table rows. During that window the backend run-level summary remains a finalization field, while item rows can already contain `target`, `already_in_db`, and timing evidence.

## 2. Goals

### 2.1 Primary Goals
- [ ] Make active Preview summary cards visually and textually read as interim, not final.
- [ ] Show DB reconciliation as in progress when active item rows already contain DB-derived statuses.
- [ ] Keep Start Upload disabled until the existing final gate is satisfied.
- [ ] Preserve mock/demo states and API contracts.

### 2.2 Non-Goals
- Change Preview execution, reconciliation, timeout, or persistence behavior.
- Execute Upload Preview, Start Upload, Retry Failed, duplicate rerun, Edge calls, or rollout actions.
- Redesign the Upload page.

## 3. Scope

### 3.1 In Scope
- Frontend-only active-run presentation logic.
- Optional API TypeScript fields for item timing metadata already returned by the backend.
- i18n labels for interim summary and active DB reconciliation.
- Small CSS treatment for the interim summary note.
- PDCA analysis for the implementation.

### 3.2 Out of Scope
- Backend run summary recomputation changes.
- Upload job creation and Start Upload safety rules.
- Source, DB, Supabase, Docker, and Edge runtime operations.

## 4. Success Criteria

- [ ] A running Preview with item rows no longer looks like a final zero-target result.
- [ ] Operators can distinguish interim item-based counts from final uploadable counts.
- [ ] Start Upload remains blocked for queued/running/cancelling previews.
- [ ] Terminal preview states keep final run-level summary behavior.
- [ ] Typecheck/build/diff/marker checks pass.

## 5. Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Operators mistake interim target rows for final approval | High | Medium | Label interim summary and keep Start Upload disabled |
| UI computes counts differently than backend final summary | Medium | Medium | Use item-based interim counts only for active runs, terminal states use backend summary |
| Mock/screenshot QA behavior regresses | Medium | Low | Preserve mock mode and run existing frontend checks |
| Sensitive path or source details leak in docs | High | Low | Keep docs generic and run marker scan |

## 6. References

- AGENTS.md
- README.md
- DESIGN.md
- docs/00_product_scope.md
- docs/01_development_roadmap.md
- frontend/src/pages/UploadPage.tsx
- frontend/src/api/uploadPreview.ts
