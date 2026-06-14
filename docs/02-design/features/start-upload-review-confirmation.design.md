# start-upload-review-confirmation - Design Document

> Version: 1.0.0 | Date: 2026-06-15 | Status: Draft
> Level: Dynamic | Plan: docs/01-plan/features/start-upload-review-confirmation.plan.md

---

## 1. Overview

### 1.1 Purpose
Add a frontend confirmation gate between Preview success and Start Upload execution. The gate forces the operator to review the final target counts and type the exact upload row count before the existing Start Upload mutation can run.

### 1.2 Design Goals
- Preserve existing backend upload job behavior and guards.
- Make the upload action visibly different from ordinary navigation or filtering.
- Avoid raw path, filename content, DB URL, token, Authorization, JWT, or secret exposure.
- Keep the UI dense, calm, and operator-focused.

## 2. Architecture

### 2.1 System Architecture
The feature is frontend-only. It sits inside `frontend/src/pages/UploadPage.tsx` between the existing Preview tab Start Upload button and the existing `startUploadMutation`.

```text
Preview succeeded + DB reachable + target rows
        |
        v
Start Upload button click
        |
        v
Confirmation modal opens
        |
        v
Operator types exact upload target rows
        |
        v
Confirm button calls existing startUploadMutation
```

### 2.2 Component Design
- `PreviewTab` receives the current Preview response, the existing `canStartUpload`, and the upload mutation state.
- The Start Upload button no longer calls `props.onStartUpload` directly.
- The button calls a local `openStartUploadReview` handler.
- A `StartUploadConfirmationModal` renders only when the modal state is open.
- The modal confirm button calls `props.onStartUpload` only after all frontend confirmation gates pass.

### 2.3 Data Flow
The modal reads only from `currentPreview.run.summary` and `currentPreview.run`:

- `previewRunId`
- `summary.target`
- `summary.uploadRows`
- `summary.alreadyInDb`
- `summary.risky`
- `summary.excluded`
- `dbStatus`
- `status`

No item paths, source filenames, raw source content, DB URLs, tokens, Authorization headers, JWTs, or secrets are passed into the modal.

## 3. Data Model

### 3.1 Entities
- `PreviewResponse`: existing frontend API DTO.
- `PreviewSummary`: existing count summary.
- `StartUploadConfirmationState`: local UI state containing `open` and typed row count.

### 3.2 Relationships
The modal is derived from the currently displayed Preview response. It does not create or mutate backend state until the final confirm button is clicked.

## 4. API Specification

### 4.1 Endpoints
No new endpoint is added.

### 4.2 Request/Response
The existing `POST /api/upload/jobs` request remains unchanged:

```json
{
  "previewRunId": "prv_...",
  "mode": "preview_targets",
  "options": {}
}
```

The UI confirmation gate only controls when the existing request is allowed to be sent.

## 5. Implementation Plan

### 5.1 File Structure
- `frontend/src/pages/UploadPage.tsx`: modal state, validation, and rendering.
- `frontend/src/pages/SettingsPage.tsx`: neutral mock-mode PLC source label.
- `frontend/src/pages/upload/mockUploadPreview.ts`: neutral mock preview source labels.
- `frontend/src/pages/upload/mockUploadJob.ts`: neutral mock upload job source labels.
- `frontend/src/styles/components.css`: modal layout and review count grid.
- `frontend/src/i18n/locales/en.json`: English text.
- `frontend/src/i18n/locales/ko.json`: Korean text.
- `docs/03-analysis/start-upload-review-confirmation.analysis.md`: check result.

### 5.2 Implementation Order
1. Add confirmation modal state and validation helpers.
2. Change Start Upload button to open the modal.
3. Add modal component with typed row count validation.
4. Add i18n strings and CSS.
5. Run typecheck/build and read-only browser smoke without clicking final confirm.
6. Remove `mock://plc` display references from frontend mock fixtures so mock mode does not appear to point at an active PLC source.

## 6. Test Plan

### 6.1 Unit/Static Checks
- `npm run typecheck`
- `npm run build:api`
- `npm run build`
- i18n JSON parse
- `git diff --check`
- marker scan

### 6.2 Integration Tests
- Targeted backend upload job guard tests to prove backend rejection paths still pass.
- Browser smoke in API mode:
  - Click Start Upload button.
  - Confirm modal opens.
  - Wrong row count keeps confirm disabled.
  - Correct row count enables confirm.
  - Cancel closes modal.
  - Do not click final confirm.

## 7. Security Considerations

- Start Upload is a DB-mutating operational action; it now has a frontend confirmation gate in addition to backend guards.
- This is not a replacement for backend authorization, local token guard, target class preflight, or preview uploadability checks.
- Modal copy must not imply that Preview success alone is approval to upload.
- The modal must not show raw source paths, source filenames, source content, DB URLs, tokens, Authorization headers, JWTs, or secrets.
