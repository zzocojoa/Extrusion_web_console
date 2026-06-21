# V2 Delete Expansion Fixture Gate

Date: 2026-06-22 Asia/Seoul

Status: `deferred_fixture_gate_no_mutation`

## Purpose

This document defines the gate for V2 delete expansion before any code path is
allowed beyond the current guarded delete behavior.

The current baseline remains
`docs/156_operator_already_in_db_delete_contract.md`: selected Upload Preview
items with status `already_in_db`, exact-key preflight, typed exact count,
no-undo acknowledgement, rollback-limitation acknowledgement, audit evidence,
DB target guard, and all-or-nothing delete semantics.

This document does not approve implementation, fixture DB mutation, operational
DB access, operational DB delete, feature-gate enablement, LAN exposure,
Supabase reset/cleanup, Docker cleanup, deployment, or operator-facing delete UI
expansion.

## Business Goal

Delete expansion is maintenance safety work, not a normal cleanup feature. The
goal is to make any future broader delete capability prove that it can block
unsafe scope, produce complete evidence, and recover from uncertain outcomes
before it is discussed for operational data.

## Policy Boundary

The only existing baseline delete path is selected `already_in_db` exact-key
delete under the current contract.

Any future expansion must be represented as an explicit policy with these
fields before code starts:

| Field | Required meaning |
| --- | --- |
| `policyId` | Stable identifier such as `already_in_db_exact_key`, `already_in_db_date_scoped`, or `admin_maintenance_delete`. |
| `roleRequired` | Minimum role allowed to request preflight and start. |
| `allowedSelectionSource` | Approved, immutable, server-rebuildable source only, such as Preview-derived evidence or a fixture seed manifest. Raw pasted keys, filenames, paths, SQL, and ad hoc operator key lists are forbidden. |
| `allowedDbScope` | Exact table and key/date boundary, without arbitrary SQL. |
| `maxSelectionItems` | Maximum Preview items or maintenance records allowed. |
| `maxExactKeys` | Maximum exact keys or rows allowed. |
| `requiresFixtureEvidence` | Must be true for every delete-expansion policy before merge. |
| `requiresOperationalApproval` | Whether a later operational approval record is required. |
| `requiresDbDeltaEvidence` | Must be true for every destructive delete-expansion policy before success. |
| `requiresRowAttributionEvidence` | Whether row attribution evidence must be written before success. |
| `rollbackModel` | Allowed recovery story and no-undo limitations. |

The following are not approved policies:

- arbitrary SQL delete;
- arbitrary table delete;
- broad date cleanup without Preview evidence;
- filename, folder, or wildcard delete;
- raw operator-provided key-list delete;
- deleting `target`, `partial_overlap`, `risky`, or `excluded` Preview items by
  treating their status as equivalent to `already_in_db`;
- DB reset, truncate, lifecycle cleanup, or manual Supabase cleanup through the
  web app.

## Selection Limits

No single long-term delete limit is approved for V2 delete expansion.

Every future policy must define concrete limits before implementation:

- maximum selected item count;
- maximum exact key or physical row count;
- maximum date span when date scope is part of the policy;
- maximum retries or reconcile attempts;
- timeout and stop condition.

These limits must come from fixture evidence, operator risk, rollback evidence,
and UI confirmation behavior. They must not be copied from an expected
operational folder size, a past run, or a future-growth blanket approval.

The current code-level `MAX_DELETE_KEYS` value is a guard for the current delete
contract. It is not a blanket approval for new policies. A future policy may
need a lower limit if fixture performance, evidence size, or recovery behavior
requires it.

## Fixture-First Gate

Fixture validation is required before operational delete verification is even
discussed.

Fixture validation must use only a disposable local fixture DB with synthetic
rows and an approved fixture seed manifest. It must not use the operator
database, production source folders, operational CSV files, raw operational
paths, raw filenames, raw exact keys, raw operator-provided key lists, DB URLs,
tokens, credentials, or internal URLs in evidence output.

Required setup evidence:

- fixture DB target class and fingerprint hash;
- isolated fixture config class and path class, without raw paths;
- pre-run gate state showing delete expansion and evidence gates disabled
  outside the fixture scope;
- run-scoped fixture gate enablement record;
- post-run gate state showing `v2_delete_expansion_enabled` and evidence gates
  disabled outside the fixture scope;
- schema fingerprint for the minimal `public.all_metrics` shape being tested;
- safe source evidence hash;
- safe selection hash and keyset hash;
- feature-gate state;
- actor id class and role, without exposing secrets;
- package/source commit under test;
- rollback limitation statement.

Required blocking cases before mutation:

- feature gate disabled;
- insufficient actor role;
- wrong DB target or target fingerprint drift;
- schema fingerprint drift;
- missing DELETE privilege for destructive paths;
- stale, missing, partial, DB-unreachable, or non-latest Preview when the
  policy depends on Preview evidence;
- selected item status drift;
- status not eligible for the policy;
- selection exceeds policy item/key/date limits;
- expected count mismatch;
- source/keyset rebuild failure;
- rollback readiness false;
- missing row attribution HMAC when gate-on attribution is required;
- audit-start write failure.

Required destructive fixture cases:

- ready preflight with exact synthetic keys succeeds;
- exact count mismatch rolls back and leaves fixture rows present;
- DB delete failure records `failed_before_mutation`;
- evidence write failure after DB success records `commit_unknown`;
- DB delta mismatch records `unknown_requires_reconcile`;
- successful delete records expected and actual DB delta safely;
- row attribution evidence uses safe hashes and is queryable by run id;
- raw keys are never returned by API, audit rows, logs, or evidence.

Required reconcile cases:

- reconcile remains SELECT-only against Supabase;
- commit-unknown recovery requires explicit reconcile;
- source/keyset rebuild failure becomes `reconciliation_failed`;
- DB count failure becomes `reconciliation_failed`;
- target/schema drift becomes `reconciliation_failed`;
- mixed key presence remains blocked or failed until a later approved recovery
  design exists;
- successful reconcile records safe DB delta and row attribution evidence when
  those gates are explicitly enabled.

## Approval Model

Fixture approval and operational approval are separate.

Fixture-only approval wording must be explicit:

```text
I approve exactly one disposable fixture DB delete-expansion validation run for policy <policyId>.
The approved fixture target class is <fixtureTargetClass>, expected synthetic rows is <rowCount>, and max exact keys is <= <keyLimit>.
This approval requires pre-run gate-off evidence, run-scoped fixture config, and post-run gate-off evidence.
This approval does not approve operational DB use, operational source use, Start Upload, Retry Failed, Settings save, feature gate enablement outside the fixture run, Supabase reset/cleanup, Docker cleanup, LAN, deploy, or operator-facing delete UI expansion.
```

Operational DB delete verification remains blocked until a later approval record
defines exact DB target class, preview/date/key scope, expected row count, DB
delta, no-undo acknowledgement, rollback limitation acknowledgement, named
approver, named executor, stop condition, and evidence report location.

## Implementation Merge Gate

Any future implementation PR for delete expansion must include:

- policy schema or typed configuration with default-off gates;
- backend tests for every blocking case above;
- backend tests proving current selected `already_in_db` behavior is unchanged;
- fixture-only destructive smoke evidence or an explicit decision to keep the PR
  draft until that evidence exists;
- API contract tests proving raw keys are not returned;
- audit redaction tests for paths, filenames, DB URLs, tokens, SQL, and raw
  exact keys;
- DB delta and row attribution evidence tests when those gates are enabled;
- frontend typecheck and build when UI changes;
- runbook and Korean/English copy review when UI changes;
- `git diff --check`;
- `$review` before Ready or merge.

## Rollback

Document-only rollback before commit:

```powershell
Remove-Item -LiteralPath docs\170_v2_delete_expansion_fixture_gate.md
git restore CHANGELOG.md docs\165_v2_status_matrix.md
```

After commit, revert the document commit.

If a future implementation writes fixture evidence, preserve evidence rows and
disable feature gates or fix forward. Do not delete audit, DB delta, or row
attribution evidence as rollback unless a later approved fixture cleanup plan
explicitly covers only disposable fixture data.

## Stop Conditions

Stop delete-expansion work before mutation when any of these are true:

- the policy lacks concrete item/key/date limits;
- the target DB class or fingerprint is ambiguous;
- fixture rows are not synthetic;
- operational source paths, filenames, DB URLs, tokens, raw SQL, or raw exact
  keys would be printed or committed;
- the request combines fixture validation with operational DB delete;
- the request asks for broad cleanup, reset, truncate, Supabase lifecycle, Docker
  cleanup, LAN exposure, deployment, or normal operator cleanup UI;
- `commit_unknown` or `reconciliation_failed` is unresolved.
