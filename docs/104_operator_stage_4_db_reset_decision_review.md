# Operator Stage 4 DB Reset Decision Review

Date: 2026-06-13 Asia/Seoul

Branch: `codex/operator-stage-4-db-reset-decision-review`

Scope: read-only investigation and pre-reset safety decision

Verdict: `accept_full_match_as_duplicate_safety_evidence`

Secondary verdict: `reset_not_recommended`

## Summary

Stage 4 Preview-only in PR #118 returned `already_in_db / db_full_match` with
upload target rows `0`. That is not evidence that Preview failed. It is evidence
that the approved source candidate's exact keys were already represented in the
current independent DB.

No DB reset, init, delete, truncate, drop, prune, Docker cleanup, Supabase
reset/start/stop, Upload Preview rerun, Start Upload, Retry Failed, duplicate
rerun, authenticated Edge call, or full rollout was executed during this
investigation.

## Read-Only Evidence

| Evidence | Result |
| --- | --- |
| Current DB class | `repo_independent_local_db` |
| Project class | `repo_independent_project` |
| API port class | `expected_api_port` |
| DB port class | `expected_db_port` |
| Studio port class | `expected_studio_port` |
| API reachability | `200` |
| Studio reachability | `307` |
| DB reachability | reachable |
| Current `all_metrics` row count | `41558` |
| Current distinct device count | `2` |
| Timestamp span present | yes |

The DB is the independent local stack used for QA. It is technically a reset
candidate only after explicit approval, backup/export, command review, and
stop-condition checks. It is not safe to treat it as disposable by default
because it now carries Stage 3 and Stage 4 acceptance evidence.

## PR #118 Preview Evidence

| Evidence | Result |
| --- | --- |
| Preview execution count | `1` |
| Preview final status | `succeeded` |
| `dbStatus` | `reachable` |
| Source scope class | `full_operational_dataset_candidate` |
| Source file count | `1` |
| Candidate files | `1` |
| Target files | `0` |
| Already-in-DB files | `1` |
| Upload target rows | `0` |
| DB matched exact keys | `20219` |
| Local source exact-key count | `20219` |
| Item status | `already_in_db` |
| Item reason class | `db_full_match` |
| DB row-count delta | `0` |
| Upload jobs created | `0` |
| `upload.start` audit rows | `0` |

The exact-key coverage is complete for the approved Preview scope:

```text
db matched exact keys == local source exact-key count == 20219
```

That means the Preview reconciler found every transformed source key already in
DB, so it correctly produced zero upload targets.

## Classification Meaning

The Preview reconciliation code classifies a candidate as `already_in_db` with
reason `db_full_match` when:

```text
db_match_count >= local_key_count
```

For this run, `db_match_count` and `local_key_count` were both `20219`. The
result is therefore consistent with the designed duplicate-safety rule:

- already represented exact keys are not uploaded again by default;
- upload target rows are `0`;
- Start Upload must not run when there is no upload target;
- duplicate proof should come from Preview reconciliation evidence, not from a
  forced duplicate upload.

## Reset Impact

Resetting the current independent DB would invalidate or weaken important
operator evidence:

| Evidence area | Reset impact |
| --- | --- |
| Stage 3 bounded upload history | historical row-count baselines and duplicate context would be lost |
| Stage 4 full-match evidence | the `already_in_db / db_full_match` proof would no longer be reproducible against the same DB state |
| Acceptance chain | reviewers would need to distinguish pre-reset evidence from post-reset evidence |
| Rollback reasoning | restoring the old state would require a verified backup/export path |
| Operator safety | a reset could create misleading target rows by removing legitimate existing records |

Resetting would answer a different question: "Can this source upload into an
empty database?" It would not answer "Is this source already represented in the
current accepted independent database?"

## Options Compared

| Option | Verdict | Why |
| --- | --- | --- |
| Keep current DB and accept full-match evidence | recommended | Preserves evidence and treats duplicate safety as a valid outcome |
| Use isolated empty QA stack/DB for upload proof | acceptable with approval | Tests empty-database upload behavior without destroying current evidence |
| Reset current independent DB | not recommended | Destroys current DB evidence and needs backup, rollback, and explicit approval |

## Recommended Path

Recommended verdict:

```text
accept_full_match_as_duplicate_safety_evidence
```

This means PR #118 should be reviewed as successful duplicate-safety evidence
with a blocked Start Upload decision, not as a failed upload-readiness run.

If the business question is "prove upload mechanics into an empty DB," use a
separate isolated empty QA stack or DB. Do not reset the current independent DB
just to force target rows.

## If Reset Is Still Requested

Reset is outside this investigation and must not happen without a separate,
explicit approval. Before any reset of the current independent DB, require:

1. Explicit written approval naming the target class as `current_independent_db`.
2. A backup/export plan reviewed before execution.
3. Backup integrity proof after export.
4. A rollback plan that restores the prior row-count and exact-key evidence.
5. Confirmation that no active Preview or Upload Job exists.
6. Confirmation that no PR depends on the current DB state for acceptance.
7. Exact destructive command review before execution.
8. A stop condition if target class, port class, or project class differs from
   the approved values.
9. A post-reset evidence plan with separate branch, document, and review.

No reset command is provided here because this PR is a decision review, not an
execution approval.

## Stop Conditions

Stop and do not reset if any of these are true:

- target class is not `repo_independent_local_db`;
- backup/export is missing or unverified;
- rollback path is not tested;
- the user has not explicitly approved the destructive operation;
- PR #118 or later review still needs the current DB state;
- the intent is only to manufacture upload targets for a duplicate source;
- raw source locator, filename, row content, connection string, credential, auth
  header, or signed credential material would be exposed in the process.

## Redaction Result

This document records only sanitized classes and aggregate counts.

- no raw connection string;
- no credential, auth header, or signed credential material;
- no raw operational source path;
- no raw operational source filename;
- no raw source row content;
- no full local source path;
- no destructive command output.

## Next Safe Action

Review PR #118 as duplicate-safety evidence. If upload-into-empty-DB proof is
still required, open a separate planning PR for an isolated empty QA stack or DB
with backup, rollback, and approval gates defined before any destructive action.

Start Upload remains forbidden for PR #118 because upload target rows are `0`.
