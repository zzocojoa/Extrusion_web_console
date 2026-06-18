# Operator 2026-01-19 Delete Execution Evidence

Date: 2026-06-18 Asia/Seoul

Status: `executed_evidence_for_review`

## Purpose

This document records evidence for the approved removal of `2026-01-19`
rows from the local Supabase `public.all_metrics` table.

This is an execution evidence record, not a reusable operator procedure. It
does not grant permission for any additional delete, reset, truncate, Docker
cleanup, Supabase lifecycle, Upload Start, or Retry Failed action.

## Scope And Approval

Approval and scope:

- requested objective: remove `2026-01-19` data from the local DB and judge
  whether the delete function worked;
- approval source: confirmation was provided in the Codex session;
- approval owner identity: confirmation required, not independently verified;
- allowed mutation: delete only rows whose timestamp date is `2026-01-19`;
- forbidden follow-up actions without separate approval: additional operational
  DB delete, reset, truncate, Docker cleanup, Supabase lifecycle, Upload Start,
  and Retry Failed.

## Execution Summary

The deletion required two paths because the selected date included mixed-date
source evidence.

| Step | Scope | Result |
| --- | --- | --- |
| 1 | Item-level delete for fully `already_in_db` selected items | `32,275` rows deleted |
| 2 | Maintainer-only date-scoped delete for the remaining mixed-date item | `64,766` rows deleted |
| Total | `2026-01-19` timestamp-date rows | `97,041` rows deleted |

The second step used this date scope:

```text
timestampStartDate = 2026-01-19
timestampEndDate = 2026-01-19
```

## Evidence

Delete job evidence:

- date-scoped delete run: `del_3acdbb463edc`;
- final status: `succeeded`;
- expected keys: `64,766`;
- deleted keys: `64,766`;
- recovery required: `false`;
- active delete blocker after execution: `false`.

DB count verification:

| Timestamp date | Count after delete |
| --- | ---: |
| `2026-01-19` | `0` |
| `2026-01-20` | `365,454` |

Fresh Preview verification:

- preview run: `prv_1fdd673194d4`;
- status: `succeeded`;
- `alreadyInDb`: `0`;
- `target`: `2`;
- `partialOverlap`: `1`.

The `partialOverlap = 1` result is expected because one source item spans
multiple timestamp dates. The remaining overlap belongs to dates outside the
deleted `2026-01-19` timestamp-date scope.

## Maintainer-Only Date Scope

The date-scoped delete fields are a maintainer-only control path. They are not
a general operator UI feature and must not be documented as generally available
operator functionality.

Use this path only when all of the following are true:

- a mixed-date source item makes whole-item delete unsafe;
- the exact timestamp date range has been separately approved;
- Delete Preflight returns a ready state and the exact key count for that date
  scope;
- Start Delete is confirmed with the typed exact key count and rollback
  acknowledgements;
- fresh post-delete evidence is captured.

If these conditions are not true, stop. Do not use whole-item delete to remove
a date from a mixed-date item.

## Code Disposition Decision

Decision: keep the date-scoped backend logic and tests, but isolate the change
in a separate review branch/PR.

Reason:

- reverting the code would not restore already deleted DB rows;
- the mixed-date case showed a real safety gap in whole-item delete;
- keeping the backend path with tests preserves the safe remediation used for
  this execution;
- the feature is not ready to be advertised as general operator UI capability
  because frontend controls, operator copy, i18n, and a fully approved UI
  runbook are not included in this change.

Required review scope before merge:

- backend date-scope request/response contract;
- preflight persistence and migration of the local state DB;
- Start Delete and reconcile reuse of the stored date scope;
- audit redaction and safe date-scope metadata;
- tests proving mixed-date rows outside the selected date are not deleted;
- documentation that the path is maintainer-only.

## Rollback

There is no automatic undo.

Recovery means running a fresh Preview and then using a separately approved
Start Upload from unchanged source files. Reverting code or documentation does
not restore already deleted DB rows.

## Safety Notes

The evidence in this document is intentionally sanitized. It does not include
raw source paths, operational filenames, CSV contents, DB URLs, tokens,
Authorization values, JWTs, secrets, or raw exact keys.

This evidence does not approve production or operator destructive use beyond
the recorded `2026-01-19` execution.
