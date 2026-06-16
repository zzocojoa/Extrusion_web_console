# Gap Analysis: upload-deduplicate-before-edge-upsert

> Date: 2026-06-16 | Design: docs/02-design/features/upload-deduplicate-before-edge-upsert.design.md

---

## Match Rate: 96%

## Summary

The implementation matches the plan: backend upload batches are deduplicated before Edge POST, the Edge function has a defensive dedupe step before Postgres upsert, and tests cover deterministic last-wins behavior plus counter separation.

## Implemented Items

- [x] Backend dedupe helper keyed by `(timestamp, device_id)`.
- [x] Last-wins source-order behavior for duplicate records.
- [x] Backend upload service sends deduplicated records to Edge.
- [x] `processedRows` remains physical-source based while `uploadedRows` and `acceptedRows` are DB-bound row counts.
- [x] `file.deduplicated` warning event records count-only observability.
- [x] Edge function deduplicates cleaned metrics before upsert batching.
- [x] Backend regression tests and Edge contract test added.

## Missing Items

- [ ] A true Deno runtime unit test for the Edge function is not present because the repo does not currently include a Deno test harness.
- [ ] No upload retry was executed; this is intentional and remains a separate approval gate.

## Changed Items (Deviations from Design)

- [x] `UploadJobRepository.mark_file_completed` gained an optional `processed_rows` parameter to avoid overwriting physical processed count with preview row count.

## Recommendations

1. Review and merge the fix before any retry of the failed upload job.
2. After merge, request a separate Start Upload/Retry Failed approval referencing the exact failed job or recovered Preview evidence.
3. Treat final upload counters with the documented distinction: processed source rows may exceed uploaded/accepted rows when duplicate keys were collapsed.

## Validation Notes

- Targeted backend upload job, repository/API, preview reconciliation, Supabase contract, and Edge source contract tests passed.
- The first pytest invocation hit a local Windows import-path collision with an installed external `tests` package. The same targeted test set passed after using a temporary import shim that prepended this repository's `tests/` directory. No project source file was changed for that shim.
- `npm run typecheck`, `npm run build:api`, and `npm run build` passed from the frontend package.

## Next Steps

- [x] Run targeted tests and build checks.
- [ ] Create PR for review.
- [ ] Keep `upl_59575d0cbe67` retry forbidden until this fix is merged and a separate approval is given.
