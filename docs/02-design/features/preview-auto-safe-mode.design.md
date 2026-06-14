# preview-auto-safe-mode - Design Document

> Version: 1.0.0 | Date: 2026-06-15 | Status: Draft
> Level: Dynamic | Plan: docs/01-plan/features/preview-auto-safe-mode.plan.md

## 1. Overview

### 1.1 Purpose

Design the smallest safe change that makes operational Upload Preview choose a large-source-safe budget automatically, without changing upload execution behavior.

### 1.2 Design Goals

- Protect the operator path from recurring default-profile timeouts.
- Preserve explicit test, demo, and bounded QA behavior.
- Keep response metadata sanitized.
- Keep Start Upload gates untouched.
- Avoid DB mutation or runtime lifecycle changes.

## 2. Architecture

### 2.1 Current Flow

The frontend sends Preview options to the backend. If the operator-facing mode is standard, the request uses the default profile budget. The backend persists request options and runs scan, extraction, and DB reconciliation against the active source.

### 2.2 Proposed Flow

Add a backend-side profile resolver before creating the Preview run:

1. Receive requested options.
2. Inspect sanitized source/config context already available to the API.
3. If the request is an operational source request and the profile is default/auto-compatible, apply large-source-safe options.
4. Preserve explicit bounded profiles and diagnostics.
5. Persist both requested and applied profile metadata if schema support is added, or persist the applied options with sanitized timing metadata.

Frontend behavior:

1. Operator-facing Preview defaults to automatic safe mode.
2. The UI states that operational sources may take longer because the system chooses a safe budget.
3. Advanced/manual mode stays non-primary or diagnostic.
4. Start Upload controls remain governed by existing Preview result gates.

## 3. Data Model

Preferred minimal metadata:

- `requestedProfile`: sanitized profile requested by client.
- `appliedProfile`: sanitized profile actually used by backend.
- `autoProfileReason`: sanitized enum such as `operational_source_class` or `large_candidate_scope`.

If metadata expansion is deferred, the applied options must still be visible in existing Preview option/timing fields.

No raw source path, source filename, source content, raw connection value, or credential should be added to state or responses.

## 4. API Design

Endpoint:

- Existing Upload Preview endpoint only.

Request compatibility:

- Existing requests remain accepted.
- Explicit bounded profiles are not rewritten.
- Default profile requests may be upgraded when source/scope qualifies.

Response compatibility:

- Existing fields remain.
- Optional sanitized applied-profile metadata may be added.
- Missing source/config state returns neutral failure or blocked status, not fake target counts.

## 5. Implementation Plan

1. Add backend profile resolver helper near Preview request handling.
2. Add unit tests for:
   - default small source remains default,
   - operational source default upgrades to large-source-safe options,
   - explicit bounded profile is preserved,
   - applied metadata is sanitized.
3. Update frontend Preview mode default/copy to automatic safe behavior.
4. Preserve screenshot/demo state behavior.
5. Update i18n strings.
6. Add implementation report after tests.

## 6. Cache / Skip Deferred Design

DB-full-match skip is not part of the first implementation.

Required future design elements:

- Strict file signature validation.
- DB context fingerprint.
- Target class fingerprint.
- Reset/import invalidation.
- Separate counts for skipped full-match files versus freshly reconciled full-match files.
- Tests that prove cache invalidates safely.

## 7. Test Plan

Backend:

- Preview schema/profile tests.
- Preview request resolver tests.
- Runtime/config source class tests if resolver depends on config shape.

Frontend:

- Typecheck.
- Build.
- i18n JSON parse.
- Component smoke if available without executing Preview.

General:

- `git diff --check`.
- Marker scan.
- PR file scope review.

## 8. Security and Operations

Security:

- Do not expose raw source paths, file contents, raw connection values, or credentials.
- Avoid logging full request payloads if they can include sensitive local config.

Operations:

- Longer Preview is acceptable only as a Preview gate, not an upload authorization.
- Start Upload remains a separate approved action.
- Failed/timed-out Preview remains no-go for upload.

Rollback:

- Revert the auto profile resolver and frontend default change.
- The existing explicit large-source profile remains the fallback if rollback is needed.
