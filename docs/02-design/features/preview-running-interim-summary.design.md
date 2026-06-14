# preview-running-interim-summary - Design Document

> Version: 1.0.0 | Date: 2026-06-15 | Status: Draft
> Level: Dynamic | Plan: docs/01-plan/features/preview-running-interim-summary.plan.md

---

## 1. Overview

### 1.1 Purpose
Render Upload Preview active-run data without implying that run-level summary and DB status are final before the backend finishes reconciliation.

### 1.2 Design Goals
- Preserve existing backend API behavior.
- Use item rows already returned by `GET /api/upload/preview/latest` and `GET /api/upload/preview/{id}` to derive active-run interim display counts.
- Label active-run counts as interim.
- Keep terminal states on final backend run summary.
- Keep Start Upload guarded by final `succeeded + dbStatus=reachable + target>0`.

## 2. Architecture

### 2.1 System Architecture
This is a frontend presentation change inside the Upload page. The backend remains the source of truth for final Preview results. The frontend adds a derived display model for active run states only.

### 2.2 Component Design
- `UploadPage`
  - computes `previewDisplayState` from `PreviewResponse`.
  - preserves `canStartUpload` logic.
- `PreviewTab`
  - renders effective DB status label and optional interim note.
  - passes display summary to `PreviewSummaryStrip`.
- `PreviewSummaryStrip`
  - accepts `interim` and `statusLabelKey` metadata.
  - keeps the same card layout.

### 2.3 Data Flow
1. Frontend polls Preview detail/latest API.
2. If run status is terminal, display `run.summary` and `run.dbStatus`.
3. If run status is active and items exist, derive counts from `items`.
4. If active item statuses show DB-derived results while `run.dbStatus=not_checked`, display an active reconciliation label.
5. Start Upload remains disabled until the final existing gate passes.
6. If the latest Preview endpoint returns an active run, keep polling with read-only GET requests until the run reaches a terminal status.

## 3. Data Model

### 3.1 Entities
- `PreviewRun`: unchanged API run model.
- `PreviewItem`: existing item model, extended in TypeScript with optional `timing`, `timeoutStage`, and optional error fields so active reconciliation metadata can be preserved without changing backend schema.
- `PreviewDisplayState`: frontend-only view model with:
  - `summary`
  - `isInterim`
  - `dbStatusLabelKey`
  - `startUploadDisabledReasonKey`

### 3.2 Relationships
`PreviewDisplayState` is derived from one `PreviewResponse`. It is not persisted and does not affect upload execution.

## 4. API Specification

### 4.1 Endpoints
No endpoint changes.

### 4.2 Request/Response
No backend response changes. The frontend TypeScript model accepts optional fields already present in API payloads.

## 5. Implementation Plan

### 5.1 File Structure
- `frontend/src/api/uploadPreview.ts`
- `frontend/src/pages/UploadPage.tsx`
- `frontend/src/styles/components.css`
- `frontend/src/i18n/locales/en.json`
- `frontend/src/i18n/locales/ko.json`

### 5.2 Implementation Order
1. Add optional item metadata types and camel-case mapping.
2. Add active-run display helpers in `UploadPage.tsx`.
3. Render interim label and active DB reconciliation label.
4. Add i18n keys.
5. Add CSS for compact interim note.
6. Add PDCA analysis and validation.

## 6. Test Plan

### 6.1 Unit/Static Checks
- `npm run typecheck`
- `npm run build:api`
- `npm run build`
- i18n JSON parse

### 6.2 Integration/Smoke Checks
- Read-only API smoke for `/api/health` and `/api/upload/preview/latest`.
- Browser/UI smoke if local tooling is available, without triggering Preview or Upload actions.

## 7. Security Considerations

- Do not expose raw source paths, filenames, source content, DB URLs, tokens, Authorization headers, JWTs, or secrets in docs or PR body.
- Do not weaken Start Upload gating.
- Do not run mutating upload, DB, Supabase, Docker, or Edge operations during validation.
