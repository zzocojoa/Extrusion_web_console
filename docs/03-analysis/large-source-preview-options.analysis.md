# Gap Analysis: large-source-preview-options

> Date: 2026-06-14 | Design: docs/02-design/features/large-source-preview-options.design.md

---

## Match Rate: 96%

## Summary
The implementation matches the design goal: API mode operators can explicitly select a large-source Upload Preview profile with a longer extraction/run budget while default Preview behavior and Start Upload safety gates remain unchanged.

## Implemented Items
- [x] Backend accepts `large_source_operational` as a Preview profile.
- [x] Backend enforces large-source defaults even if stale client values are sent.
- [x] Frontend preserves the standard Preview request as the default mode.
- [x] Frontend adds an explicit Preview mode selector for large-source operation.
- [x] Large-source mode sends `maxRunSeconds=900`, `maxFileSeconds=300`, `chunkRows=1000`, `maxFiles=500`, and `forceFullScan=false`.
- [x] UI copy distinguishes the longer Preview budget from Upload approval.
- [x] Existing Start Upload gating remains unchanged.
- [x] Backend DTO tests cover the new profile and stale-value override behavior.
- [x] No source path, filename, row content, DB URL, token, Authorization header, JWT, or secret is introduced.

## Missing Items
- [ ] Browser visual smoke was not executed because the existing screenshot QA flow clicks Preview and Start Upload controls, which is outside this task's forbidden-operation envelope.

## Changed Items
- [x] The backend profile also normalizes `maxFiles` to the default operational cap of 500. This avoids accidentally inheriting the Stage 3 bounded cap of 3 from a stale client payload.

## Recommendations
1. Review and merge this implementation before running another operational Preview.
2. For the next Preview-only QA, select the large-source mode explicitly and verify the request options in audit/API evidence.
3. Keep Start Upload forbidden until Preview succeeds, target rows are reviewed, and a separate approval is recorded.

## Next Steps
- [x] Proceed to report/review because match rate is above 90%.
