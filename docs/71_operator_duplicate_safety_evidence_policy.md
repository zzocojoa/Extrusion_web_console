# Operator Duplicate-Safety Evidence Policy

## Summary

This document defines the QA and acceptance policy for operator duplicate-safety evidence in the independent `Extrusion_web_console` local Supabase rollout.

Policy verdict: duplicate-safety acceptance should not require a normal operator Upload Job to re-upload known duplicate exact keys. In the current product flow, a fresh Upload Preview must exclude duplicate exact keys as `already_in_db`; therefore the primary acceptance evidence is the Preview exclusion result plus unchanged DB exact-key counts. DB unique/upsert contract evidence remains the secondary safety boundary.

This policy is documentation-only. It does not modify feature code, launcher code, backend code, frontend code, packaging scripts, Supabase runtime state, DB schema, Docker state, package output, or operational source data.

## Problem Statement

The previous bounded duplicate-safe rerun smoke reached a `blocked` verdict because the product behaved as designed:

- the package path pointed DB and Edge targets at the independent stack class;
- the independent DB baseline had 5 total rows, 5 distinct exact keys, and 0 duplicate exact keys;
- a fresh Preview of the known bounded duplicate source returned `dbStatus=reachable`;
- all 5 exact keys were classified as `already_in_db`;
- upload target count was 0;
- no Upload Job was created;
- no Edge authenticated upload call was executed;
- DB row-count delta stayed 0, but only because no upload occurred.

That result is not a failed duplicate-safety control. It is evidence that the normal operator workflow prevents duplicate exact keys from entering the upload queue.

## Decision

For normal operator acceptance, duplicate-safety evidence is accepted when a DB-checkable fresh Preview proves that known duplicate exact keys are excluded before Start Upload.

The accepted evidence chain is:

1. Operator package path is used.
2. DB and Edge target classes are independent and aligned.
3. Preview DB reconciliation is reachable.
4. The known bounded duplicate source is scanned.
5. All duplicate exact keys are classified as `already_in_db`.
6. Upload target count is 0.
7. Upload Job is not created for the duplicate source.
8. Independent DB exact-key counts remain unchanged.
9. Audit/log/UI evidence remains redacted.

A forced duplicate Upload Job is not required for normal operator acceptance because it is not the normal operator flow.

## Primary Evidence

Primary duplicate-safety evidence comes from the normal product flow.

| Evidence | Required result | Why it matters |
| --- | --- | --- |
| Package path | assembled operator package path | Confirms acceptance covers the handoff path, not only a maintainer dev backend. |
| Target class | DB independent, Edge independent | Prevents mixed legacy/independent target evidence. |
| Preview DB status | `reachable` | Proves exact-key reconciliation actually checked the DB. |
| Known duplicate source class | bounded and approved | Keeps QA away from operational full-source upload. |
| Preview classification | all known duplicate exact keys `already_in_db` | Proves duplicate rows are excluded before upload. |
| Upload target count | 0 | Proves Start Upload has no duplicate target from this source. |
| Upload Job | not created | Expected outcome when target count is 0. |
| DB exact-key counts | unchanged total, distinct, duplicate counts | Confirms no accidental DB mutation during evidence QA. |
| Redaction | clean | Confirms evidence can be reviewed safely. |

## Secondary Evidence

Secondary evidence confirms that, if an approved upload does occur, the database and Edge write path preserve duplicate safety.

Required secondary evidence:

- `public.all_metrics` has a unique key on `(timestamp, device_id)`;
- the Edge upload function uses `onConflict: "timestamp,device_id"`;
- prior bounded Start Upload smoke inserted the expected bounded exact keys into the independent DB;
- Upload Job accepted-row wording is treated as accepted/upserted rows, not net-new physical insert rows;
- DB row-count delta is measured separately from accepted/upserted row count.

Secondary evidence is not a substitute for Preview DB reconciliation. It is the final safety boundary beneath the operator workflow.

## Why Normal Acceptance Does Not Require Forced Duplicate Upload

The normal operator flow is:

1. Preview scans configured source data.
2. Preview extracts exact `(timestamp, device_id)` keys.
3. Preview reconciles those keys against the configured DB.
4. Preview marks exact matches as `already_in_db`.
5. Start Upload creates jobs only from `target` Preview items.

Because known duplicate exact keys become `already_in_db`, the correct target count is 0. A normal Upload Job cannot be created from those duplicate rows. Forcing a duplicate upload would bypass or alter the operator-facing safety gate being tested.

Therefore:

- a blocked Upload Job creation is expected when there are no targets;
- Edge authenticated upload count can be 0 in normal duplicate-safety evidence QA;
- DB row-count delta 0 must not be described as proof of a successful duplicate rerun when no upload occurred;
- the proof is the exclusion behavior plus the DB/Edge safety contract.

## Test-Only Forced Duplicate Rerun

A forced duplicate rerun is optional and maintainer-only. It is not part of normal operator acceptance unless a later approval explicitly requires it.

Allowed only when all conditions are met:

- the test path is explicitly documented as maintainer-only or test-only;
- it is isolated from the normal operator UI flow;
- it uses a bounded synthetic or approved small source class;
- it does not use operational full-source upload;
- it does not expose raw DB URLs, tokens, Authorization headers, JWTs, secrets, source paths, filenames, or row contents;
- it does not require DB reset, DB delete, DB cleanup, DB prune, Docker delete, or Supabase reset;
- it records accepted/upserted rows separately from physical row-count delta;
- it confirms DB row-count delta 0 after the forced upload;
- it writes safe audit evidence.

Examples of acceptable future designs:

- a maintainer-only test fixture that directly exercises the Edge function with sanitized generated rows;
- a test-only API route compiled or enabled only in maintainer QA mode;
- an integration test that uses an isolated disposable DB fixture, not the operator runtime.

Examples of unacceptable designs:

- exposing a normal operator button that uploads `already_in_db` rows;
- changing Preview to mark known duplicate exact keys as `target`;
- using operational source data for forced duplicate upload;
- recording raw source paths, filenames, row content, secrets, DB URLs, or auth headers;
- using reset/delete/prune as part of the test.

## Acceptance Criteria

Operator duplicate-safety evidence is accepted when all criteria pass:

| Category | Acceptance criterion |
| --- | --- |
| Execution path | QA uses the assembled operator package path or an explicitly equivalent package-local path. |
| Runtime target | DB and Edge target classes are independent and aligned. |
| Runtime health | independent API, DB, Studio, and Edge are reachable enough for the scoped QA. |
| Preview DB check | Preview returns `dbStatus=reachable`. |
| Duplicate source | source class is bounded and approved; no operational full-source upload. |
| Preview result | known duplicate exact keys are all `already_in_db`. |
| Upload target | target count is 0 for the known duplicate source. |
| Upload job | no Upload Job is created for the duplicate source in the normal flow. |
| DB count | independent DB exact-key total, distinct, and duplicate counts remain unchanged. |
| Audit/log | audit and logs use safe summary fields only. |
| Redaction | marker scan is clean for DB URL, token, Authorization, JWT, secret, source path, filename, and row content classes. |
| Artifacts | no untracked PNG, operational fixture, `.gstack`, `frontend/dist`, package output, zip, or checksum is committed. |

## Non-Acceptance Criteria

Operator duplicate-safety evidence is not accepted if any condition is true:

| Condition | Reason |
| --- | --- |
| DB target class is legacy, unknown, or mismatched with Edge | Evidence does not cover the independent package path. |
| Edge target class is legacy, unknown, or mismatched with DB | Upload safety target is ambiguous. |
| Edge runtime is unhealthy for the scoped QA | Start Upload readiness is not established. |
| Preview `dbStatus` is `not_checked` or unreachable | Duplicate classification is not DB-backed. |
| Known duplicate source produces target count greater than 0 | Preview may be weakening duplicate exclusion. |
| Upload Job is created for known duplicate exact keys in normal flow | Product safety gate may be bypassed. |
| DB exact-key counts mutate unexpectedly | Duplicate-safety evidence is contradicted. |
| Raw secret/path/content marker appears in report, logs, screenshots, or PR body | Evidence is not safe to review. |
| Operational full-source upload is used | Scope violation. |
| DB reset/delete/cleanup/prune or Docker delete is required | Scope and data-safety violation. |

## Future QA Sequence

Use this sequence for the remaining operator acceptance work.

1. Operator package duplicate-safety evidence QA.
   - Use package path.
   - Confirm DB/Edge independent alignment.
   - Run only approved read-only checks and one fresh Preview if approved for that QA.
   - Expect `already_in_db` and target count 0 for known duplicate exact keys.
   - Do not require Upload Job creation.

2. Optional test-only forced duplicate rerun plan.
   - Create a separate plan before any implementation.
   - Keep it maintainer-only.
   - Do not mix it with normal operator acceptance.
   - Require explicit approval before any Edge authenticated call.

3. Final operator acceptance.
   - Confirm package path, runtime readiness, Preview exclusion evidence, DB/Edge contract evidence, audit/log redaction, and package artifact hygiene.
   - Keep GitHub Release/tag and production deploy out of scope until separately approved.

## Security And Redaction Policy

Evidence documents, PR bodies, logs, and screenshots must not include:

- raw DB URLs;
- local API tokens;
- Authorization headers;
- JWTs;
- anon keys or service role values;
- secret values;
- source paths;
- CSV filenames;
- row content;
- full local paths;
- generated Supabase credentials;
- package output paths;
- zip or checksum contents.

Allowed evidence is limited to status classes, counts, safe labels, target classes, and sanitized result codes.

## Merge Readiness For Future QA

A future duplicate-safety evidence QA PR is merge-ready when:

- it is document-only or otherwise explicitly scoped;
- it states whether Upload Preview, Upload Start, duplicate rerun, and Edge authenticated upload were run;
- it records primary evidence without overstating DB row-count delta;
- it separates normal operator evidence from optional forced test-only evidence;
- it includes marker scan results;
- it excludes untracked operational fixtures and generated artifacts;
- it recommends a next action consistent with this policy.
