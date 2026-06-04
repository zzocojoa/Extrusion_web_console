# Upload Edge Count Semantics Plan

Status: implemented on branch `codex/upload-edge-accepted-rows-ui-api`

Date: 2026-06-04

Scope: clarify Upload Job row count terminology across Edge Function, backend DTOs, job events, audit params, Upload UI, tests, and documentation.

Implementation result:

- `acceptedRows` is now the canonical Upload Job API/UI field and label for Edge/Supabase upsert-accepted rows.
- `insertedRows` remains available as a deprecated v1 compatibility alias.
- API detail responses, file rows, job events, and SSE replay payloads include `acceptedRows`.
- Frontend API normalization prefers `acceptedRows` and falls back to legacy `insertedRows`.
- Upload Job UI labels now display `Accepted` / `수락`; the Korean Upload Preview `already_in_db` label now reads `DB에 있음`.
- SQLite `inserted_rows` columns were not renamed or migrated.
- QA passed targeted upload job backend tests, full backend tests, API/SSE smoke, frontend typecheck/build, `git diff --check`, Vite/backend HTTP smoke, and wording checks. Browser screenshot QA remains limited by the local `node_repl` asset-path issue and missing local Playwright install.

## Summary

The authenticated real Edge smoke in `docs/18_upload_job_real_supabase_edge_auth_ready_env_rerun.md` proved that duplicate rerun DB row count delta was `0`, while the pre-PR #19 Upload Job summary still reported `insertedRows=12` for the duplicate rerun.

The pre-PR #19 `insertedRows` label was misleading. In the current Edge implementation, the returned `inserted` value is the number of rows returned by Supabase `upsert(...).select("timestamp,device_id")`. Supabase upsert performs insert or conflict update based on `onConflict`; returned rows are modified/upserted rows, not net-new inserted rows.

Decision implemented in PR #19: v1 renamed operator-facing semantics from `Inserted` to `Accepted` / `수락`. The existing SQLite `inserted_rows` storage and `insertedRows` DTO remain as deprecated compatibility aliases until a later migration. `acceptedRows` is the canonical API/UI field mapped from the current Edge-reported upsert count.

## Pre-Implementation Behavior Analysis

### Edge Function

Reference file:

```text
legacy reference project: supabase/functions/upload-metrics/index.ts
```

The current Edge Function:

- Cleans request records into valid metric rows.
- Splits rows into upsert batches.
- Calls Supabase:

```text
from("all_metrics")
  .upsert(batch, { onConflict: "timestamp,device_id" })
  .select("timestamp,device_id")
```

- Sums returned `data.length` into `totalInserted`.
- Responds with:

```json
{
  "success": true,
  "inserted": 12
}
```

Because the upsert uses `onConflict: "timestamp,device_id"`, duplicate rows can be accepted as updates/upserts without increasing the physical `all_metrics` row count.

### Supabase Semantics

Supabase JavaScript docs state that upsert inserts when no conflict exists, or performs the alternative conflict action when the `onConflict` columns already exist. They also state that `.insert()`, `.update()`, `.upsert()`, and `.delete()` do not return modified rows by default; chaining `.select()` returns modified rows.

Source references:

- Supabase JavaScript upsert docs: https://supabase.com/docs/reference/javascript/upsert
- Supabase JavaScript modifier `.select()` docs: https://supabase.com/docs/reference/javascript/db-modifiers-select

Implication: current `inserted` is not a reliable net-new insert count. It is better described as Edge-reported accepted/upserted rows.

### Backend Before PR #19

Pre-implementation backend flow:

- `EdgeUploader.upload_batch()` parses `payload.get("inserted", 0)`.
- `UploadCounters.inserted_rows` accumulates that value.
- `UploadJobRepository.update_file_progress()` persists `inserted_rows`.
- `UploadJobRepository.mark_file_completed()` persists final `inserted_rows`.
- `UploadJobRepository._recompute_job_summary()` sums file `inserted_rows`.
- Job events emit `insertedRows`.
- API DTOs expose `insertedRows`.

The backend currently treats Edge-reported `inserted` as `inserted_rows` without differentiating insert vs update.

### Frontend Before PR #19

Pre-implementation Upload UI:

- Summary metric label: English `Inserted`, Korean equivalent.
- File table column: English `Inserted`, Korean equivalent.
- API client normalizes `insertedRows`.
- Mock upload jobs generate `insertedRows`.

This is operator-facing and can be misread as net-new DB rows.

### QA Evidence

`docs/18_upload_job_real_supabase_edge_auth_ready_env_rerun.md` recorded:

| Metric | Result |
| --- | --- |
| First upload uploaded rows | 12 |
| First upload Edge reported inserted rows | 12 |
| Duplicate rerun uploaded rows | 12 |
| Duplicate rerun Edge reported inserted rows | 12 |
| Exact key count before first upload | 12 |
| Exact key count after first upload | 12 |
| Exact key count after duplicate rerun | 12 |
| Duplicate rerun DB row count delta | 0 |

This proves duplicate-safe upsert behavior and exposes only the naming problem.

## Chosen Terminology

### Canonical v1 Terms

| Term | Meaning | Source |
| --- | --- | --- |
| `processedRows` | Valid canonical rows read and processed by backend from CSV | Backend transform loop |
| `uploadedRows` | Rows submitted by backend to the Edge Function | Backend batch send count |
| `acceptedRows` | Rows the Edge Function reports as accepted/upserted after cleaning and Supabase upsert | Edge response `inserted`, renamed in web app |
| `netNewRows` | Physical new `all_metrics` row count delta | Not available in v1 standard path |

### Deprecated Compatibility Term

| Field | Decision |
| --- | --- |
| `insertedRows` | Keep as deprecated alias for `acceptedRows` during v1 compatibility window. Do not show it as "Inserted" in UI. |
| SQLite `inserted_rows` | Keep existing column. Define it in docs as legacy storage for Edge-reported accepted rows. No migration required for v1. |
| Edge response `inserted` | Keep as legacy Edge response field for now. Backend maps it to `acceptedRows`. |

## Decision

Use `acceptedRows` as the operator-facing and API-canonical term for v1.

Do not attempt to calculate `netNewRows` in the normal upload path for v1. Exact net-new counts require either pre/post exact-key DB counting, an Edge-side SQL/RPC path that explicitly returns inserted-vs-updated counts, or a dedicated database function. Those options add DB round trips, migration surface, and operational risk. They are not needed to preserve the existing safety guarantee because `all_metrics(timestamp, device_id)` upsert remains the duplicate protection boundary.

`netNewRows` can be added later only if operators need a distinct "new rows created" metric. Until then, the UI should not imply net-new insertion.

## API And DTO Plan

### Backend DTOs

Add canonical fields:

```text
UploadJobSummary.accepted_rows
UploadJobFileDto.accepted_rows
```

Keep compatibility aliases:

```text
UploadJobSummary.inserted_rows
UploadJobFileDto.inserted_rows
```

Response shape during compatibility window:

```json
{
  "summary": {
    "processedRows": 12,
    "uploadedRows": 12,
    "acceptedRows": 12,
    "insertedRows": 12
  }
}
```

Rules:

- `acceptedRows` is canonical in new frontend code and docs.
- `insertedRows` remains available for existing clients and tests.
- No `netNewRows` numeric field is emitted unless the backend has actually measured it.
- Do not emit `netNewRows: 0` for unknown; that would be misleading.

### Repository

Keep current SQLite columns:

```text
upload_jobs.inserted_rows
upload_job_files.inserted_rows
```

Document them as legacy persisted accepted/upserted row counts.

No migration is required for v1 because changing SQLite column names would create unnecessary compatibility risk and would not change the underlying measured value.

Optional future migration:

```text
accepted_rows INTEGER NOT NULL DEFAULT 0
net_new_rows INTEGER
```

Only add this after a concrete need for historical schema clarity or net-new counts is established.

## Edge Function Plan

Keep `onConflict: "timestamp,device_id"` unchanged.

For the next implementation PR:

1. Keep accepting existing Edge response:

```json
{ "success": true, "inserted": 12 }
```

2. Prefer a new Edge response field when available:

```json
{
  "success": true,
  "accepted": 12,
  "upserted": 12,
  "inserted": 12
}
```

3. Backend parsing order:

```text
accepted -> upserted -> inserted -> 0
```

4. Treat all three as the same v1 semantic: accepted/upserted rows.

Do not change the Edge Function in this planning PR. A later implementation can add `accepted` while preserving `inserted` for backward compatibility.

## UI Plan

Change operator-facing labels:

| Current | New |
| --- | --- |
| `Inserted` | `Accepted` |
| Korean current inserted label | Korean label meaning Edge accepted/processed, not net-new inserted |

Recommended English labels:

- Summary metric: `Accepted`
- File table column: `Accepted`
- Tooltip/help text if needed: `Rows accepted by Edge upsert. Duplicate-safe reruns may not create new DB rows.`

Implemented Korean labels:

- Summary metric: `수락`
- File table column: `수락`
- Upload Preview `already_in_db` status: `DB에 있음`
- Tooltip/help text if needed: `Edge upsert가 수락한 행입니다. 중복 재실행에서는 DB 신규 행이 늘지 않을 수 있습니다.`

Keep `Rows` as `processedRows / totalRows`.
Keep `Uploaded` as rows submitted to Edge.

## Events And Audit Plan

### Job Events

Update event payloads to include canonical field:

```json
{
  "processedRows": 12,
  "uploadedRows": 12,
  "acceptedRows": 12,
  "insertedRows": 12
}
```

Rules:

- New consumers should read `acceptedRows`.
- Keep `insertedRows` for compatibility through v1.
- Event message text should avoid "inserted" wording.

### Audit Params

`upload.start` currently records start metadata, not final row counts. Keep it that way unless a later upload completion audit is added.

If upload completion audit params are added later, use:

```json
{
  "uploadedRows": 12,
  "acceptedRows": 12,
  "duplicateSafe": true
}
```

Do not audit raw file paths, filenames, DB URLs, auth keys, service role values, tokens, Authorization headers, CSV contents, row contents, or raw Edge request/response bodies.

## Documentation Updates

Updated:

- `README.md`
- `docs/08_upload_job_sse_plan.md`
- `docs/18_upload_job_real_supabase_edge_auth_ready_env_rerun.md` or a follow-up note
- `CHANGELOG.md`

Documentation wording:

- Replace "inserted rows" in Upload Job UI/API sections with "accepted/upserted rows".
- Explain that `acceptedRows` can equal uploaded rows on duplicate-safe reruns while DB row count delta stays `0`.
- Keep `all_metrics(timestamp, device_id)` upsert safety as the authoritative duplicate protection.

## Tests

### Backend Unit Tests

Implemented tests prove:

- `EdgeUploader.upload_batch()` reads `accepted` when present.
- `EdgeUploader.upload_batch()` falls back to `upserted`.
- `EdgeUploader.upload_batch()` falls back to legacy `inserted`.
- `UploadJobService` stores Edge-reported accepted rows.
- API DTO contains `acceptedRows`.
- API DTO still contains compatibility `insertedRows`.
- Job event payloads contain `acceptedRows`.
- Existing `insertedRows` consumers remain compatible during v1.

### Repository Tests

Add tests to prove:

- Existing `inserted_rows` SQLite column remains populated from accepted rows.
- Job summary aggregation maps stored `inserted_rows` to both `acceptedRows` and compatibility `insertedRows`.
- No migration is required for existing state DB files.

### Frontend Tests Or Type Checks

Implemented coverage:

- TypeScript types use `acceptedRows` as canonical.
- API normalizer maps `acceptedRows` first and falls back to `insertedRows`.
- Upload page labels no longer display "Inserted" or Korean inserted-row wording.
- Mock upload job data populates `acceptedRows`.

### Contract Tests

Keep existing contract:

- Edge Function uses `onConflict: "timestamp,device_id"`.
- Preview exact reconciliation remains unchanged.
- Duplicate-safe rerun DB row count delta remains covered by QA report or a future environment smoke.

## Migration And Compatibility

### v1 Compatibility Decision

No SQLite migration in the first implementation.

Reasons:

- Current data is not wrong at storage level; the label is wrong.
- Renaming columns would require migration and compatibility handling without improving measurement accuracy.
- The app is still local operator-PC v1, and stable behavior matters more than schema cosmetics.

### API Compatibility

Maintain `insertedRows` as a deprecated alias for one v1 compatibility window.

Recommended deprecation path:

1. Implementation PR adds `acceptedRows` and keeps `insertedRows`.
2. Docs and UI switch to `acceptedRows`.
3. Later cleanup can remove `insertedRows` only after no frontend/API consumers depend on it.

## Implementation Order

Completed in PR #19:

1. Backend: introduce accepted-row naming in internal variables where low risk.
2. Backend: update `EdgeUploader` parser to prefer `accepted`, then `upserted`, then legacy `inserted`.
3. Backend: add DTO `acceptedRows` while keeping `insertedRows`.
4. Backend: update job event payloads to include `acceptedRows` plus compatibility `insertedRows`.
5. Frontend API: add `acceptedRows` to types and normalizer fallback.
6. Frontend mock data: emit `acceptedRows`.
7. Frontend UI/i18n: change labels from Inserted to Accepted.
8. Docs: update README and Upload Job plan terminology.
9. Tests: add parser/DTO/event/frontend coverage.
10. Validation: targeted backend upload job tests, full backend tests, `npm run typecheck`, `npm run build`, `git diff --check`.

## Non-Goals

- Do not change Upload Preview classification.
- Do not change Upload Job start/retry behavior.
- Do not change Edge upsert safety.
- Do not run DB reset, delete, cleanup, prune, or Docker destructive operations.
- Do not upload the full operational CSV fixture.
- Do not expose secrets, DB URLs, auth keys, service role values, tokens, Authorization headers, raw CSV paths, CSV contents, or row contents.

## Open Follow-Up

If operators later need true net-new row counts, create a separate implementation plan for `netNewRows`.

Likely options:

1. Pre/post exact-key count around each upload batch.
   - Pros: no Edge migration.
   - Cons: extra DB round trips and race-condition interpretation issues.

2. Edge SQL/RPC function returning inserted-vs-updated counts.
   - Pros: clearest semantics.
   - Cons: requires Supabase migration and more careful transaction design.

3. Post-upload sampled validation only.
   - Pros: cheaper.
   - Cons: not a precise metric.

Do not infer net-new counts from current `inserted` response.
