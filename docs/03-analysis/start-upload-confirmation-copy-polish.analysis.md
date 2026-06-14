# Gap Analysis: start-upload-confirmation-copy-polish

> Date: 2026-06-15 | Scope: Start Upload confirmation modal copy polish

---

## Match Rate: 98%

## Summary

The copy polish keeps the Start Upload safety behavior from PR #152 intact while making the modal easier for operators to understand.

The modal now explains that continuing creates an upload job for the displayed target file count and formatted row count, and that a successful upload increases the local DB row count. The input hint now tells the operator to type the raw target row count and explicitly says commas are allowed.

The remaining 2% gap is that this change does not add a dedicated frontend component test. The behavior is covered by typecheck, build, and read-only browser smoke that does not click the final confirm button.

## Implemented Items

- [x] Korean and English modal eyebrow/title now use clearer final-confirmation language.
- [x] Warning copy includes target file count and formatted upload row count.
- [x] Warning copy states that successful upload increases local DB row count.
- [x] Input hint says which raw row count to type and that commas are allowed.
- [x] Confirm button includes formatted target row count.
- [x] Existing Start Upload confirmation gate remains unchanged.
- [x] Existing backend Start Upload guard remains unchanged.
- [x] Retry Failed flow remains unchanged.
- [x] No raw source path/content, DB URL, token, Authorization header, JWT, or secret is added.

## Non-Goals Confirmed

- [x] No backend changes.
- [x] No upload execution behavior changes.
- [x] No Start Upload execution.
- [x] No Upload Preview execution.
- [x] No Retry Failed, duplicate rerun, authenticated Edge call, full rollout, DB/Supabase/Docker lifecycle, or destructive operation.

## Validation Evidence

- `npm run typecheck`: passed.
- `npm run build:api`: passed.
- `npm run build`: passed.
- i18n JSON parse: passed.
- `rg "mock://plc" frontend/src`: no matches.
- Browser smoke without clicking confirm:
  - modal opened from Upload page.
  - copy polish text was visible.
  - wrong input kept confirm disabled.
  - exact `861351` enabled confirm.
  - comma-formatted input also enabled confirm after sanitization.
  - cancel closed the modal.
  - mutating upload job requests: `0`.
  - browser console errors: `0`.
  - failed browser requests: `0`.
  - latest upload job unchanged.
  - audit total unchanged: `77` before, `77` after.
- `git diff --check`: passed with Windows CRLF warnings only.
- marker scan: clean by classification; matches were existing i18n key names or negative documentation text.

## Next Step

Publish a draft PR for review. Start Upload remains forbidden until separately approved.
