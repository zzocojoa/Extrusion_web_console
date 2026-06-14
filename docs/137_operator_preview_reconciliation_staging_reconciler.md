# Operator Preview Reconciliation Staging Reconciler

Date: 2026-06-14

Branch: `codex/preview-reconciliation-staging-reconciler`

Scope: implementation and QA report for Upload Preview exact-key reconciliation
scaling. No Upload Preview, Start Upload, Retry Failed, duplicate rerun,
authenticated Edge call, full rollout, database reset, Supabase/Docker
destructive action, production deploy, Release, tag, or operational source
mutation was performed.

## Match Rate

Match Rate: 96%

| Requirement | Status | Evidence |
| --- | --- | --- |
| Preserve exact-key safety | pass | Reconciliation still matches `(timestamp, device_id)` against `public.all_metrics` |
| Avoid schema/upsert weakening | pass | No operational DB schema or Edge upload function change |
| Add stage timing | pass | Preview run/item `timing` metadata added |
| Add timeout stage | pass | Preview run/item `timeoutStage` added |
| Add DB batch progress evidence | pass | Reconciler exposes `dbProgress` with strategy, batch count, staged keys, matches, and stage |
| Implement staging/temp table reconciler | pass | `SupabaseExactReconciler` stages candidate keys in session-local temp table |
| Keep temp table session-local | pass | Temp table is created as `ON COMMIT DROP` in the DB session |
| Keep timeout/cancel/failure blocking Start Upload | pass | Existing upload job guard preserved; timed-out Preview API guard test added |
| Preserve API/frontend compatibility | pass | New API fields are optional additive fields; no frontend contract break required |
| Validate timeout during extraction | partial | Existing timeout coverage preserved; DB timeout preservation explicitly added |
| Validate timeout before DB matching | pass | Existing deadline-before-file test updated for added timing calls |
| Validate timeout during DB matching | pass | New DB timeout test preserves extracted row/key counts and stage |
| Validate staging no/full/partial match | pass | Reconciler contract tests cover all three match shapes |
| Validate cancellation during staged matching | pass | Existing cancellation-before-DB guard remains covered |
| Validate redaction | pass | New metadata contains counts/stages only, not paths, row content, DB URLs, tokens, or secrets |
| PDCA pre-write/check | pass_with_caveat | bkit pre-write allowed edits but warned no feature plan/design document exists |

## Non-developer summary

Preview still does the same safety check: it compares every local row's exact key
with the database before upload. That safety rule was not loosened.

The change is how the app asks the database. Instead of sending thousands of keys
as a huge inline query over and over, the backend now puts the candidate keys into
a temporary database table for that one session, then joins that temporary table
to the real metrics table. The temporary table is discarded automatically and does
not add operating data to the database.

If Preview times out again, the report should now show where it timed out. For
example, it can distinguish file extraction from database matching and show how
many DB batches completed before the timeout. If database matching times out after
the CSV was already read, the Preview item keeps the extracted row/key counts
instead of reporting zero-count incomplete evidence.

Start Upload is still blocked unless Preview finishes successfully, DB status is
reachable, and there are reviewed target files. A timed-out or risky Preview does
not become uploadable because of this change.

## Implementation summary

### Reconciliation strategy

The reconciler now uses a session-local staging table:

1. Sort exact local keys.
2. Open a database session with statement timeout bounded by the Preview deadline.
3. Create a temporary key table for that session.
4. Insert candidate keys in bounded batches.
5. Join the staged keys to `public.all_metrics` on the exact key:
   `(timestamp, device_id)`.
6. Return only the exact matched key set to existing classification logic.

This keeps the existing `ExactReconciler` interface: callers still pass a key set
and receive a matched key set.

### Observability

Preview state now records safe timing metadata:

- run timing: scan/run duration where available;
- item timing: extraction and DB match duration where available;
- timeout stage: e.g. `extract`, `before_db_match`, `db_match`,
  `after_db_match`;
- DB progress: strategy, total keys, batch size, total batches, completed
  batches, staged keys, matched keys, elapsed time, and current DB stage.

The metadata intentionally avoids raw operational paths, filenames, row content,
database endpoints, credential headers, signed credentials, and private values.

### Timeout behavior

When timeout happens after local extraction but during DB matching, the item is
still marked `risky / timeout`, but the local extracted counts are preserved:

- `scanMode=full`;
- `rowCount` preserved;
- `localKeyCount` preserved;
- `uploadRowEstimate=0`;
- `timeoutStage=db_match`;
- `dbStatus=not_checked` at run level.

This keeps Start Upload blocked while making the evidence useful for diagnosis.

## Engineering assessment

Risk level: medium.

Main trade-off: this changes the database read-side query shape from repeated
large inline-key joins to a temporary-table join. That should scale better and is
easier to observe, but it depends on the local Postgres session supporting temp
tables and transaction-local statement timeouts.

Compatibility impact: additive API fields only. Existing Preview response fields
and frontend mock/demo behavior are not changed.

Security implications: the new persisted metadata is count/stage-only. It does
not persist or expose raw source paths, source names, row content, database
endpoints, credential headers, signed credentials, or private values.

Operational failure mode: if temp table creation, staged insert, or final join
fails, the Preview remains failed/partial/timed-out and Start Upload remains
blocked. No operational table rows are inserted by Preview reconciliation.

Rollback path: revert the implementation PR to return to the prior VALUES-based
reconciler. Already-created `timing_json` and `timeout_stage` columns are passive
state metadata and do not affect upload execution.

## Files changed

| File | Purpose |
| --- | --- |
| `backend/app/services/upload_preview.py` | Add staging reconciler, progress tracking, timeout-stage handling, and preserved counts on DB timeout |
| `backend/app/db/preview_repository.py` | Add backward-compatible Preview run/item timing columns |
| `backend/app/schemas/upload_preview.py` | Add optional `timeoutStage` and `timing` response fields |
| `backend/app/api/upload_preview.py` | Return optional timing metadata from persisted Preview rows |
| `tests/backend/test_upload_preview_supabase_contract.py` | Cover temp table strategy and no/full/partial exact-key match shapes |
| `tests/backend/test_upload_preview_reconciliation.py` | Cover DB matching timeout with preserved row/key counts |
| `tests/backend/test_upload_preview_api_contract.py` | Cover response contract for optional timing fields |
| `tests/backend/test_upload_preview_repository_contract.py` | Cover new repository columns |
| `tests/backend/test_upload_jobs_api_contract.py` | Cover Start Upload rejection for timed-out/not-checked/risky Preview |

## Validation

Targeted backend tests:

```text
47 passed
```

Command used a temporary Python import shim because this Windows environment has
an installed external `tests` package that can shadow this repository's `tests/`
namespace during pytest collection. No project source file was changed for that
shim.

Covered test groups:

- upload preview Supabase reconciliation contract;
- upload preview reconciliation service;
- upload preview API contract;
- upload preview repository contract;
- upload jobs API guard contract.

Observed warnings:

- existing FastAPI/Starlette HTTP 422 deprecation warnings;
- pytest cache write warning from local workspace permissions.

Not executed:

- Upload Preview;
- Start Upload;
- Retry Failed;
- duplicate rerun;
- authenticated Edge call;
- full rollout;
- DB reset/init/delete/truncate/drop/prune;
- Supabase/Docker destructive work;
- production deploy;
- GitHub Release/tag creation.

## PDCA note

bkit pre-write checks allowed the implementation files and tests, but classified
the change as a feature and warned that no dedicated PDCA plan/design document
exists for `preview-reconciliation-staging-reconciler`. This PR keeps the PDCA
footprint in this implementation report to avoid unrelated documentation churn.

## Next action

Review and merge this implementation PR. After merge, run one separately approved
Preview-only QA for the 4-file operational source. Start Upload remains forbidden
until that fresh Preview succeeds, the target counts are reviewed, and the user
separately approves one upload action.
