# Gap Analysis: preview-auto-safe-mode

> Date: 2026-06-15
> Design: docs/02-design/features/preview-auto-safe-mode.design.md

## Match Rate: 96%

## Summary

The implementation matches the approved direction: normal operator Preview no longer depends on remembering a standard versus large-source selector, and the backend protects default operational PLC Preview requests with the large-source-safe budget. Start Upload behavior and upload execution paths were not changed.

## Implemented Items

- Backend auto safe-mode resolver added at the Upload Preview API boundary.
- Default PLC Preview requests are upgraded to `large_source_operational` when the active source path class is operational.
- Default PLC Preview requests are upgraded for large date ranges.
- Explicit bounded QA profiles are preserved.
- Frontend Upload page always creates a large-source-safe Preview request from the operator-facing Preview button.
- Preview mode selector was removed from the operator toolbar.
- Operator copy now describes automatic safe Preview budget and keeps upload approval separate.
- Backend tests cover operational source auto-upgrade, large date range auto-upgrade, explicit bounded profile preservation, and small local default behavior.
- Existing Start Upload guard tests passed without changes.

## Missing Items

- Response metadata does not yet expose a separate `requestedProfile` versus `appliedProfile`.
- Browser visual smoke was not performed because a browser automation package was not available in this workspace.

## Changed Items

- The design allowed optional sanitized applied-profile metadata. The implementation kept the API response shape stable and persists applied options in the existing Preview run options JSON instead.
- The frontend does not add an Advanced profile picker in this PR. Diagnostic explicit profiles remain available through API/test paths, not the main operator toolbar.

## Risk Review

- Rollback path: revert the API resolver and Upload page request/toolbar changes.
- Observability: applied profile is visible in persisted Preview options; no new raw source data is emitted.
- Migration risk: none. No DB schema or persisted state migration is required.
- Security: no raw operational source path, row content, connection string, auth header, credential, or secret value was added.
- Test coverage gap: no browser visual smoke; automated typecheck/build covers the UI compile path.

## Recommendations

1. Proceed to PR review with the current implementation.
2. Keep cache/skip as a separate design because it needs DB/source fingerprint invalidation.
3. After merge, run one separately approved Preview-only QA and review target rows before any Start Upload approval.

## Next Steps

- Create PR after final file scope review.
- Do not run Upload Preview or Start Upload as part of this implementation PR.
