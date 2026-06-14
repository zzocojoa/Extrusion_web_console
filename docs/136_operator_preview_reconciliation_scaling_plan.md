# Operator Preview Reconciliation Scaling Plan

Date: 2026-06-14

Branch: `codex/operator-preview-reconciliation-scaling-plan`

Scope: docs-only investigation and improvement plan. No upload, retry, full rollout,
database reset, Supabase lifecycle, Docker destructive action, or source mutation was
performed.

## Match Rate

Match Rate: 100%

| Requirement | Status | Evidence |
| --- | --- | --- |
| Current reconciliation flow reviewed | pass | `backend/app/services/upload_preview.py` |
| Exact-key compare method reviewed | pass | `SupabaseExactReconciler.find_existing_keys` |
| Growth behavior estimated | pass | Current `VALUES` batch join design analyzed |
| File duplicate cache option reviewed | pass | Covered in implementation options |
| Temp/staging table option reviewed | pass | Covered as preferred long-term fix |
| Progress/timing observability gap documented | pass | Covered below |
| Short-term and long-term actions separated | pass | Separate sections below |
| Forbidden operations avoided | pass | This document is docs-only |
| Raw source path/name/content and secret markers avoided | pass | Sanitized class/count evidence only |

## Non-developer summary

Preview is doing the safe thing, but it is doing it in a slow shape.

The app reads each CSV, extracts each row's exact safety key, then asks the local
database which keys already exist. This avoids duplicate uploads. That safety rule
must stay.

The problem is the comparison step. With four operating CSVs and 77,382 rows, the
current Preview can spend the whole 120 second default budget trying to compare
keys. It times out before it can say which file is new, which file is already in
the database, and which rows are upload targets.

So the safe decision is: do not press Start Upload from this Preview. The system
has not produced a trustworthy target count yet.

## Current evidence

Latest investigated Preview:

| Field | Value |
| --- | --- |
| Preview run | `prv_c05b17653eaf` |
| Status | `timed_out` |
| DB status | `not_checked` |
| Total files | 4 |
| Target files | 0 |
| Upload target rows | 0 |
| Risky files | 4 |
| Risky reason | `timeout` |
| Scan mode | `incomplete` for all 4 files |
| Latest upload job | unchanged |
| Start Upload | not executed |

Sanitized source shape:

| Ordinal | File date | Physical rows | Size class | Preview item result |
| --- | --- | ---: | ---: | --- |
| 1 | 2026-01-16 | 24,888 | 3.2 MB class | risky / timeout |
| 2 | 2026-01-19 | 15,096 | 2.0 MB class | risky / timeout |
| 3 | 2026-01-19 | 17,179 | 2.1 MB class | risky / timeout |
| 4 | 2026-02-09 | 20,219 | 2.5 MB class | risky / timeout |

Aggregate:

- CSV files: 4
- Physical rows: 77,382
- Runtime target class: passed
- Runtime API/database/Edge runtime: ready
- Grafana: unreachable, non-core caveat
- Offline key extraction check: completed for all 4 files in about 2 seconds

Interpretation: file access and key extraction are not the likely bottleneck. The
strongest current hypothesis is that exact-key database reconciliation consumed the
default Preview run budget.

## Current implementation flow

The current flow is:

1. `POST /api/upload/preview` creates a persisted Preview run.
2. `CandidateScanner.scan()` enumerates configured source folders and filters by
   file date, stability, lock state, extension, and `maxFiles`.
3. For each candidate, `CsvKeyExtractor.extract()` streams CSV rows and builds
   distinct `(timestamp, device_id)` keys.
4. `SupabaseExactReconciler.find_existing_keys()` sorts local keys and compares
   them against `public.all_metrics`.
5. The reconciler splits keys into batches, effectively capped at 5,000 keys per
   statement.
6. Each batch builds a `WITH candidate_keys AS (VALUES ...)` query and joins it to
   `public.all_metrics` on `(timestamp, device_id)`.
7. `classify_keys()` marks the file as `target`, `already_in_db`, or
   `partial_overlap`.
8. If the global run deadline is exceeded, incomplete work is recorded as
   `risky/timeout`, and the run finishes as `timed_out`.

The database schema preserves the important duplicate safety boundary:

- `public.all_metrics` has a unique constraint on `(timestamp, device_id)`.
- `idx_all_metrics_timestamp` exists.
- `idx_all_metrics_latest_timestamp_by_device` exists.

That schema is correct for final duplicate safety. The Preview issue is not a
weakened safety rule. It is the shape and observability of the read-side comparison.

## Complexity and scaling issue

For each candidate file:

- Key extraction is O(N) over CSV rows.
- Reconciliation is O(K log M) in database index lookup terms, where:
  - N = CSV rows in that file.
  - K = distinct local keys in that file.
  - M = existing rows in `public.all_metrics`.
- The current query shape also adds statement construction, bind parameter, parse,
  planning, network, and result materialization overhead per batch.

For 77,382 local keys, the effective 5,000-key batch cap means roughly 16 database
statements. Each statement has thousands of tuple values and twice as many bind
parameters. As the database grows, every Preview continues to ask the same basic
question row by row: "is this exact key already in the database?"

That is safe. It is not scalable enough for operator-facing Preview latency.

## Observability gap

The current Preview result does not say where time was spent.

Important gaps:

- No per-stage duration: scan, key extraction, DB connect, DB batch query, classify.
- No per-file extracted-key count is persisted when timeout happens during or after
  reconciliation.
- Timeout items use `scanMode=incomplete` and row/key counts of `0`, even when
  local extraction may already have succeeded.
- No count of completed DB batches before timeout.
- No slow-batch threshold or query timing in safe audit params.
- No clear split between file-read timeout and database-reconciliation timeout in
  stored reason codes.

This is why `prv_c05b17653eaf` can only support a strong hypothesis, not absolute
proof of the exact sub-stage. The offline check weakens file-read and transform as
the root cause, but the persisted run lacks enough timing evidence to prove the
database sub-stage directly.

## Short-term workaround

Use only after separate explicit approval for a single Preview-only run.

Recommended short-term request shape:

```json
{
  "rangeMode": "custom",
  "startDate": "2026-01-16",
  "endDate": "2026-02-09",
  "sources": ["plc"],
  "options": {
    "profile": "default",
    "stableLagMinutes": 3,
    "sampleRows": 200,
    "chunkRows": 1000,
    "maxFiles": 500,
    "maxRunSeconds": 900,
    "maxFileSeconds": 300,
    "forceFullScan": false
  },
  "retryOfRunId": null
}
```

Why this is only a workaround:

- It gives the current algorithm more time.
- It does not improve the algorithm.
- It can still fail as row counts and database size grow.
- It does not add stage-level timing.

Do not use `stage3_profile_a_bounded_full_scan` for this Stage 4 case. That profile
forces `maxFiles=3`, while the current source has 4 candidate files.

Start Upload must remain blocked unless a fresh Preview succeeds with:

- status `succeeded`;
- DB status `reachable`;
- target files and upload target rows reviewed by the operator;
- risky, failed, invalid, and excluded counts acceptable for the approved scope;
- separate explicit approval for Start Upload exactly once.

## Long-term fix options

### Option A: Timing observability only

Add stage timing and batch progress without changing reconciliation.

Work:

- Persist per-run and per-item timing fields or a safe timing event table.
- Track `scan_ms`, `extract_ms`, `db_match_ms`, `db_batches_done`,
  `db_batches_total`, and `timeout_stage`.
- Keep audit params sanitized.
- Show run progress in API response and optionally UI.

Pros:

- Smallest behavior risk.
- Makes the next timeout diagnosable.
- Helps prove the real bottleneck before larger DB changes.

Cons:

- Does not fix timeout.
- Operators still need larger timeouts for big datasets.

Use when: the team wants the safest first PR.

### Option B: Adaptive batching and smaller statements

Keep `VALUES` join, but reduce query payload and adapt batch size based on timing.

Work:

- Lower default `chunkRows` for large local key sets.
- Track per-batch time.
- Reduce batch size when a batch approaches statement timeout.
- Preserve exact-key semantics.

Pros:

- Low schema risk.
- Can reduce statement parsing pressure.
- Easier to test with fake reconciler and small local DB fixtures.

Cons:

- More round trips.
- Still O(K log M) with one batch query per chunk.
- May improve stability but not enough for future large datasets.

Use when: a minimal code PR is required before changing DB query architecture.

### Option C: Temporary database staging table

Bulk load candidate keys into a temporary table, index them, then perform a set join.

Work:

- Create a temp table for the Preview connection.
- Bulk insert candidate keys through `COPY` or batched `executemany`.
- Add or rely on temp table primary key/index for `(timestamp, device_id)`.
- Join temp keys to `public.all_metrics` once per file or once per run.
- Return match counts grouped by preview item.
- Keep all work read-only against `public.all_metrics`; temp table writes are
  session-local and should not mutate operational data.

Pros:

- Best fit for set-based database work.
- Reduces huge `VALUES` statement construction.
- Allows one database-side plan over staged keys.
- Can support per-file grouping and progress.

Cons:

- More implementation complexity.
- Requires careful transaction and cleanup handling.
- Needs tests for temp table lifecycle, cancellation, and timeout.

Use when: fixing the structural bottleneck is the priority.

### Option D: File-level duplicate cache

Cache file signature to Preview result mapping in local state.

Work:

- Store sanitized file signature, row count, local key count, DB match count,
  first/last timestamp, and classification for completed previews.
- Reuse classification only when file signature and relevant database watermark are
  safe.
- Invalidate cache after successful upload, database reset/recovery, or target class
  change.

Pros:

- Very fast repeat Preview for unchanged files.
- Useful for operator retry and recovery workflows.

Cons:

- Cache invalidation is hard.
- Unsafe if DB content changed outside this app.
- Cannot replace exact reconciliation for new or changed files.

Use when: combined with Option C or after a safe invalidation policy exists.

### Option E: Database summary/watermark shortcut

Use per-file or per-date summary tables to avoid exact-key comparison.

Pros:

- Fast if the summary is authoritative.

Cons:

- Risky unless the summary is derived from the same exact keys.
- Can recreate the old latest-timestamp blind spot if designed poorly.
- Not acceptable as a replacement for exact-key safety without a stronger proof.

Use when: not recommended for the next PR.

## Recommended plan

### Plan

Goal: make Preview reliable for operator-scale CSV batches without weakening exact
duplicate safety.

Success criteria:

- 77,382-row, 4-file Preview finishes within an operator-approved budget.
- DB status becomes `reachable`.
- Target/already/partial counts are trustworthy.
- Start Upload remains blocked for timeout/risky states.
- The next timeout shows the exact stage that exceeded budget.

### Do

Next implementation PR should include:

1. Reconciliation timing instrumentation.
2. A `timeout_stage` or equivalent safe persisted classification.
3. Reconciler progress counters for completed batches and local key counts.
4. A staging-table reconciler behind the existing `ExactReconciler` interface.
5. Targeted tests for:
   - timeout during extraction;
   - timeout before DB matching;
   - timeout during DB matching;
   - staging-table full match;
   - staging-table no match;
   - staging-table partial match;
   - cancellation during staged matching;
   - no raw path/name/content or secret-like audit params.

Keep this PR backend-focused first. Frontend can consume additional fields later if
the API returns backward-compatible timing metadata.

### Check

Validation gates:

- targeted backend upload preview tests;
- staging reconciler tests against a local test database or fake cursor contract;
- `npm run typecheck` if response DTO types change;
- `npm run build` if frontend types change;
- marker scan for source path/name/content and secret-like classes;
- operator QA Preview-only run, exactly once, after approval.

### Act

If staging-table matching solves the timeout:

- keep default 120 seconds for small interactive previews;
- add an explicit Stage 4 large-source Preview profile or documented operator-only
  option set;
- update Upload UI to show stage progress only after backend timing fields settle.

If staging-table matching still times out:

- split Preview into per-file resumable runs;
- add operator-visible progress and "continue Preview" flow;
- do not allow Start Upload from partial or timed-out evidence.

## Next implementation PR scope

Recommended branch:

`codex/preview-reconciliation-staging-reconciler`

Recommended PR title:

`fix: scale upload preview exact-key reconciliation`

Files likely in scope:

- `backend/app/services/upload_preview.py`
- `backend/app/db/preview_repository.py`
- `backend/app/schemas/upload_preview.py`
- `tests/backend/test_upload_preview_reconciliation.py`
- `tests/backend/test_upload_preview_supabase_contract.py`
- optional frontend API types only if response shape changes
- a follow-up docs report

Files out of scope:

- Upload Job execution behavior
- Edge upload function behavior
- Supabase migrations that alter `public.all_metrics`
- production deploy or release/tag work
- DB reset or destructive runtime operations

## Final go/no-go

Start Upload: NO-GO.

Reason: current Preview evidence is `timed_out`, `dbStatus=not_checked`, target files
`0`, upload target rows `0`, and risky files `4`.

Additional Preview: allowed only after separate explicit approval, with either the
short-term larger-budget options above or after the staging reconciler fix lands.

Upload retry, duplicate rerun, authenticated Edge call, and full rollout remain
forbidden until a fresh successful Preview and separate Start Upload approval exist.
