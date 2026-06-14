# large-source-preview-options - Design Document

> Version: 1.0.0 | Date: 2026-06-14 | Status: Draft
> Level: Dynamic | Plan: docs/01-plan/features/large-source-preview-options.plan.md

---

## 1. Overview

### 1.1 Purpose
Expose a safe large-source Upload Preview mode in the existing Upload UI. The mode increases Preview extraction/run budgets for operational CSV batches while keeping upload execution controls unchanged.

### 1.2 Design Goals
- Preserve default quick Preview behavior.
- Require explicit operator selection for large-source Preview.
- Keep all upload safety gates unchanged.
- Avoid raw source path, filename, row content, DB URL, token, Authorization, JWT, or secret exposure.

## 2. Architecture

### 2.1 System Architecture
The existing Upload Preview flow remains:

1. Frontend builds a `PreviewCreateRequest`.
2. Backend validates `PreviewOptions`.
3. Backend executes Preview asynchronously.
4. Existing Preview result polling, timing, timeout stage, and Start Upload guard remain in place.

The change adds one backend profile value and one frontend selector. No new endpoint is required.

### 2.2 Component Design
- `backend/app/schemas/upload_preview.py`: add `large_source_operational` profile defaults.
- `frontend/src/api/uploadPreview.ts`: add matching frontend type/default request builder.
- `frontend/src/pages/UploadPage.tsx`: add explicit Preview mode selector.
- `frontend/src/i18n/locales/*.json`: add labels for the selector.

### 2.3 Data Flow
Default mode sends existing short options:

- `maxRunSeconds=120`
- `maxFileSeconds=30`
- `chunkRows=20000`
- `forceFullScan=false`

Large-source mode sends:

- `profile=large_source_operational`
- `maxRunSeconds=900`
- `maxFileSeconds=300`
- `chunkRows=1000`
- `forceFullScan=false`

The backend also enforces these profile defaults if a client sends the profile with stale or conflicting option values.

## 3. Data Model

### 3.1 Entities
No persisted schema change.

### 3.2 Relationships
No new relationships. Existing `preview_runs.options_json` stores the selected option payload.

## 4. API Specification

### 4.1 Endpoints
No new endpoint.

### 4.2 Request/Response
`POST /api/upload/preview` accepts an additional `options.profile` value:

```json
{
  "profile": "large_source_operational",
  "chunkRows": 1000,
  "maxRunSeconds": 900,
  "maxFileSeconds": 300,
  "forceFullScan": false
}
```

Response shape is unchanged.

## 5. Implementation Plan

### 5.1 File Structure
- Backend schema and tests.
- Frontend API type/request helper.
- Upload page selector and i18n strings.

### 5.2 Implementation Order
1. Add backend profile enum/defaults and DTO test.
2. Add frontend request helper and UI selector.
3. Add i18n labels.
4. Run targeted backend tests, frontend typecheck/build, marker scan, and browser smoke.

## 6. Test Plan

### 6.1 Unit Tests
- Backend DTO test proves default profile remains short.
- Backend DTO test proves large-source profile overrides stale conflicting values.

### 6.2 Integration Tests
- Frontend typecheck validates request profile and selector wiring.
- Browser smoke checks the Upload UI exposes the selector without executing Preview.

## 7. Security Considerations

- The selector does not expose file paths, filenames, row content, DB URLs, tokens, Authorization headers, JWTs, or secrets.
- The selector does not auto-run Preview.
- Start Upload remains gated by successful Preview, reachable DB status, and target rows.
- No DB/Supabase/Docker lifecycle or destructive operation is introduced.
