# Preview Start Upload Freshness Gate Analysis

## Match Rate

96%

## Summary

Start Upload job creation now has an explicit backend gate before any upload job is queued.

The gate rejects a Preview when it is not the latest run, too old, risky, missing its source/config safety snapshot, or different from the current active source/config class. This closes the P0 gap where Start Upload previously depended mostly on `status`, `dbStatus`, and target count.

## Non-Developer Explanation

Preview is the operator's dry run. Start Upload is the step that can write data.

This change makes the system re-check the dry run at the exact moment the operator tries to start upload:

- Is this still the newest Preview?
- Is it recent enough?
- Did it finish successfully with DB reachable?
- Are there risky files?
- Is the source/config still the same as when Preview ran?

If any answer is unsafe, the upload job is not created.

## Behavior Change

- Start Upload rejects stale or non-latest Preview references.
- Start Upload rejects Preview runs with risky items.
- Start Upload rejects Preview runs that do not carry the new source/config safety snapshot.
- Start Upload rejects Preview runs whose saved source/config fingerprint differs from the current backend runtime.
- Preview response now exposes requested profile, applied profile, and auto profile reason.
- Upload UI shows the applied Preview mode when the backend provides it.
- Upload UI keeps Start Upload disabled when risky items are present or target rows are zero.

## Compatibility

No database migration is required. The new fields are stored in existing `config_snapshot_json` and exposed as optional API response fields.

Older Preview runs without the new source/config safety snapshot are intentionally not uploadable through Start Upload. Operators must run a fresh Preview before Start Upload.

## Safety Controls Preserved

- Upload Preview was not executed for this implementation work.
- Start Upload was not executed.
- Retry Failed was not executed.
- duplicate rerun was not executed.
- authenticated Edge manual calls were not executed.
- DB, Supabase, and Docker lifecycle or destructive operations were not executed.
- Operational CSV files were not modified.

## Rollback

Rollback path is PR revert. Reverting restores the previous Start Upload job creation behavior.

## Residual Risk

The freshness window is currently 24 hours. If operations require a shorter or longer approval window, that should be made configurable in a follow-up PR.
