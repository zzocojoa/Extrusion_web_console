# Operator Data Mutation Safety Gate

Status: `mutation_deferred_until_separate_approval`

Date: 2026-06-20

## Decision

Do not run Upload Preview, Start Upload, Retry Failed, Upload Delete,
Settings save, Local Supabase start/stop, feature-gate enablement, LAN
enablement, Supabase reset/migration/cleanup, Docker cleanup, deployment, or
any other mutating operator action from the handoff package until a separate
approval names the exact scope below.

The accepted handoff artifact is the main-based API-mode operator package:

- source commit: `ebd0db5`
- full commit: `ebd0db5333b06c10c28741fd09b6dd610b08fc33`
- artifact label: `ExtrusionWebConsole-ebd0db5-main-validation-20260619-211807`
- zip SHA-256: `6dc297afd075e5bdb5cb9ac09396bed1d4132475c3dcf8b455e42eb0bd0d7cb5`
- handoff memo: `ExtrusionWebConsole-ebd0db5-main-validation-20260619-211807-handoff-memo.md`
- first-launch smoke: passed, read-only routes only

This document is not approval that the full V2 scope is complete. It is only a
mutation safety gate for the accepted operator package.

## Current Boundary

Allowed without a new mutation approval:

- checksum verification;
- package metadata inspection;
- launcher `-CheckOnly`;
- shortcut installer `-CheckOnly`;
- read-only HTTP checks such as `/`, `/upload`, `/logs`, `/settings`,
  `/api/health`, `/api/config`, `/api/audit?limit=1`, and docs-disabled route
  checks.

Not allowed without a new mutation approval:

- Upload Preview creation or cancellation;
- Start Upload;
- Retry Failed;
- Upload Delete preflight, start, or reconcile;
- Settings save;
- Local Supabase start or stop;
- changing `v2_row_attribution_enabled`, `v2_db_delta_evidence_required`, or
  related evidence gates;
- operational DB writes or deletes;
- Supabase reset, migration, cleanup, prune, or Docker cleanup;
- LAN exposure, delete UI expansion, or deployment.

## Candidate Classification

| Candidate | Class | Default decision | Required approval |
| --- | --- | --- | --- |
| Package checksum, metadata, launcher `-CheckOnly`, read-only routes | read-only | allowed | none beyond task request |
| Upload Preview-only against configured operational source | local-state write plus DB read/reconcile | hold | exact Preview-only approval |
| Fixture mutation against disposable DB | fixture mutation | hold | exact fixture approval |
| Start Upload against real local Supabase | limited real mutation | hold | fresh Preview plus exact Start Upload approval |
| Retry Failed against real local Supabase | limited real mutation | hold | failed job evidence plus exact Retry Failed approval |
| Already-in-DB hard delete | destructive real mutation | hold | exact delete preflight plus exact hard-delete approval |
| Supabase reset/migration/cleanup, Docker cleanup, LAN, delete UI expansion, deployment | forbidden for this gate | blocked | new plan and separate approval |

## Preview-Only Approval Gate

Preview-only may be considered only after all of these are true:

- package checksum and metadata still match this document;
- launcher first-launch smoke remains passed or is rerun successfully;
- `/api/config` confirms the active source class and target class are expected;
- source path is confirmed outside chat by the operator or maintainer;
- local Supabase DB reachability is understood before interpreting DB-dependent
  preview states;
- a fresh read-only inventory precheck produced the observed file count and
  approved physical row ceiling for the intended approval scope;
- no Start Upload, Retry Failed, Delete, Settings save, or feature-gate change is
  bundled into the approval.

## Read-only Inventory Precheck

Before requesting Preview-only approval, run a read-only inventory precheck for
the same source class and intended approval scope.

This precheck is not Upload Preview. It must not create a Preview run, call the
Upload Preview API, write to the DB, write audit or local state, mutate source
files, or run Start Upload, Retry Failed, Delete, Settings save, feature-gate
changes, Supabase cleanup, Docker cleanup, LAN enablement, or deployment.

The precheck may record only safe inventory evidence:

- source class such as `drive_letter`, `network`, or `mounted`, not raw path;
- observed files count for the intended scope;
- physical data-line count or a conservative approved physical row ceiling;
- source eligibility or go/no-go reason classes.

The approval `<fileCount>` and `<rowLimit>` must come from a fresh read-only
inventory precheck completed immediately before that approval. They must not be
user guesses, copied from an earlier run, reused as long-term defaults, or used
as blanket approval for future folder growth.

If inventory cannot establish observed files and an approved physical row
ceiling, do not request or run Preview-only. If the operational folder grows
later, repeat read-only inventory and issue a new Preview-only approval for the
new observed scope.

Required approval wording:

```text
I approve exactly one Upload Preview-only run from package sourceCommit ebd0db5.
The approved source class is <sourceClass>, expected files is <fileCount>, and expected physical rows is <= <rowLimit>.
This approval does not approve Start Upload, Retry Failed, Delete, Settings save, feature gate enablement, Supabase reset/cleanup, or Docker cleanup.
```

In this wording, `expected files` means observed files from the fresh read-only
inventory, and `expected physical rows` means the approved physical row ceiling
from that same inventory.

Evidence to record after Preview-only:

- package label and source commit;
- preview run id;
- source class, not raw path;
- run status;
- total files, status counts, target row count, risky count, already-in-DB
  count, partial-overlap count;
- DB status class, not raw DB URL;
- audit evidence for `upload.preview` or blocked/failure event;
- confirmation that no upload/delete/retry/settings mutation was run.

Rollback for Preview-only:

- do not delete operational DB rows;
- preserve preview and audit evidence;
- if Preview points at the wrong source, stop and document the blocked result;
- do not use Start Upload, Retry Failed, or Delete as a cleanup workaround.

## Fixture Mutation Gate

Fixture mutation may be considered only for disposable local fixture DBs that are
not operational data and can be recreated from source-controlled fixtures or a
maintainer-approved test backup.

Required approval wording:

```text
I approve exactly one mutation smoke against disposable fixture DB <fixtureId>.
This approval does not approve operational DB use, operational CSV use, Supabase reset/cleanup, Docker cleanup, LAN, or delete UI expansion.
```

Evidence to record:

- fixture identifier, not a raw sensitive path;
- setup command class;
- operation type;
- before/after row counts;
- audit rows and state DB evidence;
- teardown or preservation decision.

Rollback:

- discard or recreate only the fixture DB;
- never reuse fixture rollback instructions for operational data.

## Start Upload Gate

Start Upload against real local Supabase is blocked until a fresh Preview-only run
has completed and the result is reviewed.

Required preconditions:

- Preview run is fresh and succeeded;
- Preview source class matches the approved source class;
- DB status is reachable and reviewed;
- `risky = 0`;
- target files and target rows are greater than zero;
- target row count matches UI/API/approval text;
- package source commit and checksum still match this document;
- no feature gate is enabled as part of the upload approval.

Required approval wording:

```text
I approve exactly one Start Upload for preview run <previewRunId> with target rows <targetRows>.
This approval is for package sourceCommit ebd0db5 and source class <sourceClass>.
This approval does not approve Retry Failed, Delete, Settings save, or feature gate enablement.
```

Evidence to record after Start Upload:

- preview run id;
- upload job id;
- approved target row count;
- started/completed timestamps;
- file counts and job status;
- accepted/upserted row count from the Edge response class;
- final job event status;
- audit evidence for upload start and completion or failure;
- whether any partial failure requires investigation.

Rollback:

- do not delete rows as a default rollback;
- rely on `all_metrics(timestamp, device_id)` upsert safety for duplicates;
- if failure occurs after partial DB mutation, preserve job/audit evidence and
  investigate before any Retry Failed;
- Retry Failed needs a separate approval below.

## Retry Failed Gate

Retry Failed is blocked until a failed or retryable upload job is reviewed.

Required approval wording:

```text
I approve exactly one Retry Failed for upload job <jobId> with remaining physical rows <remainingRows>.
This approval is for package sourceCommit ebd0db5.
This approval does not approve Start Upload, Delete, Settings save, or feature gate enablement.
```

Evidence to record:

- original job id;
- retry job id or retry event id;
- remaining row count;
- retryable file list summary without raw operational paths;
- accepted/upserted row count;
- audit and job event evidence.

Rollback:

- preserve original and retry job evidence;
- do not run broad DB cleanup;
- if retry fails, stop and investigate before another retry.

## Delete Gate

Already-in-DB hard delete remains exceptional and production-critical. It is
blocked unless an exact delete preflight and a separate destructive approval are
both present.

Required preconditions:

- fresh Preview evidence for selected `already_in_db` items;
- ready delete preflight;
- exact selected item count;
- exact key count;
- rollback readiness is true or rollback limitation is explicitly acknowledged;
- local DB target guard is ready;
- DELETE privilege preflight is ready;
- no mixed-date whole-item workaround is used;
- package source commit and checksum still match this document.

Required approval wording:

```text
I approve exactly one hard delete for preview run <previewRunId>, already_in_db items <itemCount>, and exact keys <keyCount>.
I understand the no-undo and rollback limitation boundaries.
This approval is for package sourceCommit ebd0db5.
This approval does not approve Start Upload, Retry Failed, Settings save, or feature gate enablement.
```

Evidence to record after delete:

- preview run id;
- delete preflight id;
- delete run id;
- selected item count;
- exact key count;
- deleted row count;
- rollback readiness and limitations;
- `upload.delete_start` and final `upload.delete_*` audit evidence;
- DB delta and attribution evidence when gates are explicitly approved and on;
- whether reconcile is required.

Rollback:

- do not perform broad manual DB deletes, truncates, resets, or Docker cleanup;
- if commit is unknown, run only the approved reconcile path;
- if gate-on evidence has been written, preserve `db_delta_evidence` and
  `row_attribution_ledger` rows;
- use feature-gate disablement or fix-forward rather than deleting evidence.

## Stop Conditions

Stop before any mutation when any of these are true:

- package checksum or metadata differs from this document;
- `main` and `origin/main` do not match the recorded source commit;
- active source class is unexpected;
- fresh read-only inventory was not run, is stale, or did not produce observed
  file count and approved physical row ceiling;
- file count or row limit is a user guess, an earlier-run value, a long-term
  default, or blanket approval for future folder growth;
- row counts differ between UI, API, and approval text;
- audit logs cannot be read;
- local token protection is not active for protected writes;
- Supabase local runtime status is unknown for DB-dependent actions;
- the request bundles Preview, Start Upload, Retry Failed, or Delete into one
  broad approval;
- the request asks for reset, cleanup, Docker cleanup, LAN, delete UI expansion,
  feature-gate enablement, or deployment.

## Next Decision

Current decision: hold all mutating actions.

The next safe action, if requested, is a Preview-only approval using the exact
wording above. Start Upload, Retry Failed, and Delete remain separately gated
even if Preview succeeds.
