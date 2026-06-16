# Future Upload Gate Count Hardening

## Match Rate

96%

## Purpose

Recent upload evidence showed that operators can confuse physical CSV rows,
unique upload keys, `acceptedRows`, and DB row-count delta. This change hardens
the future Start Upload and Retry Failed gates so the UI separates those count
classes before a mutation action can be confirmed.

This is a UI and documentation hardening change only. It does not change backend
upload execution, backend guards, Preview reconciliation, Retry execution, or DB
write behavior.

## Non-Developer Summary

The console now shows the operator which count they are approving. The important
approval number is `expected upload rows`. Physical rows and DB delta are still
shown or explained, but they are not treated as the same thing.

For Retry Failed, the UI now makes the operator confirm the remaining physical
rows before sending the retry. It does not pretend that retry job state can
recompute deduped expected upload rows.

## Count Classes

- Target physical rows: rows physically present in target file metadata loaded
  by the Preview result.
- Target unique upload keys: deduplicated upload keys available for those target
  files from Preview metadata.
- Target duplicate key count: target physical rows minus target unique upload
  keys where available.
- Preview DB matched keys: exact keys already found in DB across the Preview
  reconciliation result, shown with explicit full-preview scope.
- Expected upload rows: the Start Upload approval gate from Preview summary.
- Retry remaining physical rows: a retry-only confirmation gate from job state.
  It is not the same as deduped expected upload rows.

`acceptedRows` and DB row-count delta remain post-execution evidence. They can
diverge from physical rows when duplicate keys, upserts, or already-present DB
keys are involved.

## Scope

- Start Upload confirmation copy and count cards.
- Retry Failed confirmation modal before calling the existing retry API.
- English and Korean operator-facing strings.
- Styling for count semantics notes.

## Safety

Forbidden operations were not performed:

- Upload Preview
- Start Upload
- Retry Failed
- duplicate rerun
- authenticated Edge call
- full rollout
- DB/Supabase/Docker lifecycle or destructive work
- Settings save
- operational CSV mutation

## Compatibility

Backend APIs and upload execution behavior are unchanged. The Retry Failed
button still uses the existing retry API, but only after the operator types the
remaining physical row count in the new confirmation modal.

## Rollback

Rollback is a frontend-only revert of the Upload page, i18n strings, and modal
styling changes. No data migration or runtime recovery is required.

## Remaining Risk

Retry job state does not contain Preview-level unique key, duplicate key, DB
match, or deduped expected upload row counts. The retry modal explicitly marks
those fields unavailable and directs the operator back to the approved Preview
evidence before retrying.
