# Gap Analysis: preview-running-interim-summary

> Date: 2026-06-15 | Design: docs/02-design/features/preview-running-interim-summary.design.md

---

## Match Rate: 96%

## Summary
The implementation matches the design intent: active Preview runs now render item-based interim counts with an explicit interim note, active DB reconciliation can display as in progress, and terminal Preview states still use backend final run summary. Start Upload gating remains unchanged.

## Implemented Items
- [x] Frontend-only active-run display model in `frontend/src/pages/UploadPage.tsx`.
- [x] Item-based interim counts for active Preview runs.
- [x] DB reconciliation display label for active runs with item-level DB evidence.
- [x] Existing final summary behavior retained for terminal Preview runs.
- [x] Start Upload guard remains `succeeded + reachable + target > 0`.
- [x] Start Upload disabled reason is clearer during active Preview calculation.
- [x] Latest active Preview runs continue polling with read-only GET requests until terminal.
- [x] TypeScript item model preserves optional timing/error metadata already returned by API.
- [x] English and Korean i18n keys added.
- [x] Compact interim summary styling added without redesigning the Upload page.

## Missing Items
- [ ] Browser visual smoke is pending until validation. It must remain read-only and must not click Preview, Start Upload, Retry Failed, duplicate rerun, or any mutating controls.

## Changed Items
- [x] The interim summary derives from the loaded item rows during active states. This is intentionally labeled as interim and is not used for Start Upload eligibility.

## Recommendations
1. Proceed with validation.
2. If browser tooling is unavailable or the local app is not running, document that as a validation caveat instead of triggering any forbidden workflow.

## Next Steps
- [ ] Run frontend typecheck/build checks.
- [ ] Run i18n JSON parse.
- [ ] Run read-only API smoke.
- [ ] Run git diff and marker scans.
