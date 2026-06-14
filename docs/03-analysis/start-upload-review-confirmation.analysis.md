# Gap Analysis: start-upload-review-confirmation

> Date: 2026-06-15 | Design: docs/02-design/features/start-upload-review-confirmation.design.md

---

## Match Rate: 96%

## Summary
The implementation matches the design intent: Start Upload is no longer a single-click mutation from the Preview page. The first click opens a confirmation modal, and the existing upload mutation is reachable only from the modal confirm button after exact upload row count confirmation.

The remaining 4% gap is test depth: no dedicated frontend unit test file exists for this page, so validation relies on TypeScript, build, backend guard tests, and browser smoke that intentionally avoids final confirm.

## Implemented Items
- [x] Start Upload button opens a confirmation modal instead of calling the upload mutation directly.
- [x] Modal shows sanitized evidence only: Preview run id, target files, upload target rows, already-in-DB, risky, excluded, and dbStatus.
- [x] Confirm remains disabled until the typed row count exactly matches the upload target rows.
- [x] Confirm remains disabled when Preview is not succeeded, DB is not reachable, target rows are missing, or risky count is positive.
- [x] Cancel closes the modal without sending a mutating API request.
- [x] Confirm is the only modal path that calls the existing `startUploadMutation`.
- [x] Backend upload job API and guard behavior are unchanged.
- [x] Retry Failed flow is unchanged.
- [x] Korean and English i18n strings are present.
- [x] Modal avoids raw source paths, source filenames, source content, DB URLs, tokens, Authorization headers, JWTs, and secrets.
- [x] Frontend mock-mode `mock://plc` source labels were replaced with neutral demo labels to avoid confusion with active PLC source binding.

## Missing Items
- [ ] No dedicated frontend unit test was added because the project currently validates this page through TypeScript/build and browser smoke rather than a component test harness.

## Changed Items (Deviations from Design)
- [x] The implementation allows the Start Upload button to open the modal when the existing `canStartUpload` guard is true. The modal then applies the stricter risky-count and typed-row confirmation gates before the confirm button can execute.

## Validation Evidence
- `npm run typecheck`: passed.
- `npm run build:api`: passed.
- `npm run build`: passed.
- i18n JSON parse: passed.
- Targeted backend upload job/local token tests: 29 passed.
- Browser smoke: modal opened, wrong row count kept confirm disabled, exact `711488` enabled confirm, cancel closed modal, mutating API requests `0`, console errors `0`, failed requests `0`, latest upload job unchanged, `upload.start` audit total unchanged.
- `rg "mock://plc" frontend/src`: no matches after mock/demo label cleanup.
- `git diff --check`: passed with Windows CRLF warnings only.
- Marker scan: no real raw source path/content, DB URL, token, Authorization header, JWT, or secret exposure. Matches were existing i18n key names or negative documentation text.

## Recommendations
1. Proceed to draft PR review.
2. Keep Start Upload execution forbidden until the operator separately approves it after reviewing Preview target rows.

## Next Steps
- [x] Proceed to publish a draft PR.
