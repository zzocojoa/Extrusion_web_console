# upload-deduplicate-before-edge-upsert - Plan Document

> Version: 1.0.0 | Date: 2026-06-16 | Status: Draft
> Level: Dynamic

---

## 1. Overview

### 1.1 Purpose

Prevent upload batches from sending duplicate `(timestamp, device_id)` keys to the Edge upsert path. Duplicate keys inside one Postgres `ON CONFLICT DO UPDATE` statement can fail with SQLSTATE `21000`.

### 1.2 Background

A large operational upload attempt failed after partial progress. Read-only investigation showed failed job `upl_59575d0cbe67` had already processed/uploaded/accepted `2000 / 2000 / 2000` rows and DB delta `+2000` before a later duplicate-key batch failed. The target file contained more physical canonical rows than unique upload keys. Preview reconciliation counted unique keys, while upload execution streamed physical canonical rows. A later product batch could therefore contain duplicate conflict keys and fail at the Edge/Postgres upsert boundary.

## 2. Goals

### 2.1 Primary Goals

- [x] Deduplicate records by `(timestamp, device_id)` before each backend Edge upload batch.
- [x] Keep last source-order record for each duplicate key.
- [x] Preserve physical row processing counters separately from deduplicated upload/accepted counters.
- [x] Add defensive dedupe inside the Edge function before internal upsert batching.
- [x] Add regression tests for backend dedupe and Edge source contract.

### 2.2 Non-Goals

- Do not run Upload Preview, Start Upload, Retry Failed, duplicate rerun, or full rollout.
- Do not reset or mutate DB/Supabase/Docker runtime.
- Do not change preview reconciliation semantics in this PR.
- Do not expose raw operational source paths, file contents, keys, DB URLs, tokens, or secrets.

## 3. Scope

### 3.1 In Scope

- Backend upload job batch dedupe.
- Edge upload-metrics defensive dedupe before upsert batching.
- Upload counter and job-event observability for deduplicated rows.
- Focused backend and contract tests.

### 3.2 Out of Scope

- Runtime upload retry for the failed job.
- UI redesign or Start Upload flow changes.
- Database schema migration.

## 4. Success Criteria

- [x] Duplicate keys in a product upload batch are collapsed before Edge POST.
- [x] Edge function also collapses duplicate keys before Postgres upsert.
- [x] `processedRows` can represent physical rows consumed while `uploadedRows` and `acceptedRows` represent deduplicated rows.
- [x] Existing non-duplicate upload behavior remains compatible.
- [x] Tests cover deterministic last-wins behavior and counter separation.

## 5. Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Counter interpretation changes | Medium | Medium | Keep `processedRows` as source rows and `uploadedRows`/`acceptedRows` as deduplicated DB-bound rows. |
| Hidden duplicate data difference | Medium | Medium | Use deterministic last-wins by source order and add warning event with counts only. |
| Edge-only caller bypasses backend | High | Low | Add Edge-side defensive dedupe before upsert. |
| Retrying before fix is merged | High | Medium | Keep retry/start upload forbidden until reviewed fix is merged and user separately approves. |

## 6. References

- `backend/app/services/upload_jobs.py`
- `supabase/functions/upload-metrics/index.ts`
- `tests/backend/test_upload_jobs_service.py`
