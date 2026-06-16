# upload-deduplicate-before-edge-upsert - Design Document

> Version: 1.0.0 | Date: 2026-06-16 | Status: Draft
> Level: Dynamic | Plan: docs/01-plan/features/upload-deduplicate-before-edge-upsert.plan.md

---

## 1. Overview

### 1.1 Purpose

Add deterministic upload-path dedupe so duplicate conflict keys cannot reach a single Postgres upsert statement.

### 1.2 Design Goals

- Collapse duplicate `(timestamp, device_id)` keys before Edge upload.
- Use last-wins semantics based on source order.
- Preserve resume offsets against physical source rows.
- Keep the Edge function safe for non-backend callers.

## 2. Architecture

### 2.1 Backend Upload Service

`UploadJobService._upload_file` continues to stream canonical records from the CSV reader. Before each Edge POST, the service deduplicates the current product batch by `(timestamp, device_id)`.

The dedupe helper returns:

- `records`: deduplicated records to send to Edge.
- `duplicate_rows`: number of source rows collapsed.

### 2.2 Edge Function

`upload-metrics/index.ts` cleans incoming records as before. It then deduplicates cleaned metrics by the same conflict key before splitting into internal upsert batches.

### 2.3 Counters

- `processedRows`: physical canonical rows consumed from source.
- `uploadedRows`: deduplicated rows sent to Edge.
- `acceptedRows` / `insertedRows`: rows accepted by the Edge/Postgres upsert response.
- `resumeOffset`: physical source row offset.

## 3. Observability

When duplicate rows are collapsed, the backend records a `file.deduplicated` warning event. Event data contains counts only:

- `inputRows`
- `outputRows`
- `duplicateRows`
- `processedRows`

No raw row values, keys, file paths, source content, DB URLs, tokens, or secrets are stored.

## 4. API Compatibility

The Edge response keeps existing `accepted` and `inserted` fields. It also returns a non-breaking `deduplicated` count for observability. Existing backend parsing ignores unknown fields.

## 5. Test Plan

- Unit test deterministic last-wins backend dedupe helper.
- Service test duplicate keys in one upload batch:
  - Edge receives only unique keys.
  - Last duplicate value wins.
  - job succeeds.
  - processed/uploaded/accepted counters are separated.
  - warning event is recorded.
- Contract test Edge source dedupes cleaned records before upsert batching.

## 6. Security Considerations

- Dedupe logs must remain count-only.
- Upload retry is not part of this change.
- DB/Supabase/Docker destructive operations are forbidden for this implementation.
