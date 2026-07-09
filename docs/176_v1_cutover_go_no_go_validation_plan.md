# V1 Cutover Go/No-Go Validation Plan

Status: `plan_only_requires_separate_operational_approval`

## Executive Summary

This document is a decision package for deciding whether the legacy Tkinter GUI
can be replaced by `Extrusion_web_console` for V1 Core Ops.

It does not approve Upload Preview, Start Upload, Retry Failed, DB delete,
Settings save, Supabase start/stop, Supabase reset, Docker cleanup, schema
migration, LAN exposure, deployment, production DB access, or source-file
mutation by itself. Any action that writes local state, mutates the DB, changes
runtime state, exposes the app, or deploys a package needs the separate approval
gate named in the relevant source document.

The current cutover decision is evidence-led. `docs/175` found no broad
unimplemented Core Ops blocker for Preview, Start Upload, Retry Failed,
progress/logs, Audit Logs, Settings, local Supabase status/start/stop, or the
guarded selected `already_in_db` exact-key delete path. The remaining V1 cutover
work is to collect fresh operator-PC evidence, prove CSV compatibility and large
Preview behavior, verify failure visibility, and record explicit approvals where
mutation is requested.

## Decision Scope

This plan can decide:

- whether current evidence is sufficient for `GO`, `CONDITIONAL GO`, `NO-GO`,
  or `BLOCKED` for replacing the legacy GUI for V1 Core Ops;
- whether a non-destructive operator-PC validation package is complete;
- whether a Preview-only approval package is ready to request;
- whether a Start Upload or Retry Failed approval package is ready to request
  after Preview evidence exists;
- whether deferred or excluded items are correctly kept out of the V1 cutover
  decision.

This plan cannot decide or approve:

- operational Start Upload, Retry Failed, or DB delete execution;
- Upload Preview execution without the Preview-only approval required by
  `docs/164` and `docs/173`;
- Supabase reset, migration, backfill, bootstrap, cleanup, prune, Docker delete,
  Docker volume delete, or broad DB cleanup;
- executable operator-facing date-scoped delete UI or delete expansion;
- LAN enablement, non-loopback bind, LAN CORS widening, LAN auth/session rollout,
  or deployment;
- import of legacy GUI upload state as a default migration path.

Relationship to source documents:

- `docs/175_legacy_gui_replacement_gap_audit.md` is the gap audit that this plan
  turns into evidence and approval work packages.
- `docs/173_v2_operational_upload_verification_gate.md` defines the operational
  upload evidence chain: inventory, Preview-only, Start Upload, and Retry Failed.
- `docs/164_operator_data_mutation_safety_gate.md` defines exact approval
  wording and separates read-only checks from local-state writes and DB
  mutations.
- `docs/165_v2_status_matrix.md` classifies deferred V2 items, including LAN,
  executable date-scoped delete UI, delete expansion, operational delete
  verification, and Supabase schema attribution.
- `docs/171_v2_operational_delete_verification_gate.md` is the separate gate for
  any operational destructive delete. This plan only excludes delete or points to
  that package.

## Go/No-Go Decision States

| State | Meaning | Required evidence | Example |
| --- | --- | --- | --- |
| `GO` | V1 Core Ops replacement is approved for the named package, operator PC, source class, and evidence window. | All required non-destructive evidence is current; Preview-only evidence is fresh and succeeded; Start Upload evidence exists if target rows were approved; Audit Logs and Job Logs visibility are proven; final sign-off is complete. | Preview proves target rows, a separately approved Start Upload succeeds, no retryable rows remain, and sanitized evidence is reviewed. |
| `CONDITIONAL GO` | Replacement may proceed only inside named limits with explicit residual risk acceptance. | All hard stop conditions are clear, but one non-core caveat remains documented with an owner and rollback/stop procedure. | Grafana status is attention-only while API, DB, Preview, Audit, and upload evidence are normal. |
| `NO-GO` | Replacement must not proceed. | One or more required V1 cutover evidence items failed or is missing. | Large Preview soak fails, Audit Logs do not show failure rows, or target row counts mismatch between UI/API/approval. |
| `BLOCKED` | The decision cannot be made because evidence or approval is unavailable. | The blocker is documented and no workaround is allowed without violating a safety gate. | Operator PC cannot reach the configured local Supabase DB, or package metadata cannot be matched to source commit. |
| `DEFERRED / NOT V1 SCOPE` | Item is intentionally excluded from the V1 cutover decision. | Source document classification shows deferred or excluded status. | Multi-user LAN, executable date-scoped delete UI, Supabase schema attribution migration, and legacy upload state import. |

## Required Cutover Evidence Matrix

| Evidence area | Required artifact | Allowed command or observation class | Forbidden actions | Pass condition | Fail / stop condition | Evidence owner | Source reference |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Package/source commit verification | Package label, source commit, build metadata, and source tree commit record | Read-only package metadata inspection; `git rev-parse HEAD`; `git show --stat --oneline --name-status HEAD` | Rebuilding, deploying, or editing package metadata during evidence capture | Package source commit and label match the accepted package and docs | Missing, stale, or mismatched package metadata | Maintainer | `README.md:216`; `README.md:224`; `docs/175_legacy_gui_replacement_gap_audit.md:100` |
| README/API smoke contract verification | Contract note proving README smoke uses `previewRunId`, `expectedTargetRows`, and `expectedTargetFiles` | Read-only README and schema inspection | Start Upload execution | README snippet matches backend required approval-count contract | Missing `expectedTargetRows`, stale camelCase fields, or ad hoc payload | Maintainer | `README.md:358`; `backend/app/api/upload_jobs.py:314`; `backend/app/api/upload_jobs.py:318`; `backend/app/schemas/upload_preview.py:10` |
| GET `/api/config` safe snapshot | Sanitized config evidence showing source class, target classes, mode, and override classes | `GET /api/config` against an already running local operator backend; store sanitized classes only | `PUT /api/config`, Settings save, raw path or secret capture | Snapshot confirms expected API mode/source class without raw paths or secret values | Config source class is wrong, raw sensitive value would be recorded, or endpoint unavailable | Maintainer/operator | `backend/app/api/config.py:24`; `backend/app/services/config_service.py:214`; `README.md:145`; `README.md:264` |
| Local Supabase status evidence | Sanitized runtime readiness/status-class output | Read-only dashboard/runtime status observation and existing status endpoints | Start/stop/reset/cleanup/init/migration | Status proves local Supabase readiness class or a clear blocked class | DB-dependent class is blocked and unresolved | Maintainer/operator | `docs/00_product_scope.md:34`; `README.md:272`; `README.md:282`; `docs/175_legacy_gui_replacement_gap_audit.md:31` |
| Local Supabase start/stop evidence, only if separately approved | Operation id, event ids, before/after status classes, and audit ids | Runtime start/stop only after separate approval and no active job/preview | Supabase init/reset, Docker create/rm/prune/up/down, volume deletion | Start/stop is bounded, audited, and returns expected readiness or stopped class | Required containers missing, active job/preview, broad cleanup requested, or audit unavailable | Maintainer/operator | `backend/app/services/runtime_control.py:109`; `backend/app/services/runtime_control.py:158`; `backend/app/services/command_runner.py:30`; `backend/app/services/command_runner.py:172` |
| Read-only inventory precheck | Filled inventory template with counts, row ceiling, excluded data, and reviewer | Read-only file inventory/count procedure that stores no raw names, paths, content, or keys | Preview, upload, delete, settings save, cleanup, LAN, deployment | File count and approved physical row ceiling are current and reviewer-signed | Guessed count, stale inventory, source class mismatch, or raw sensitive evidence | Maintainer with operator review | `docs/164_operator_data_mutation_safety_gate.md:96`; `docs/164_operator_data_mutation_safety_gate.md:111`; `docs/173_v2_operational_upload_verification_gate.md:39` |
| Preview-only evidence | Preview approval id, preview run id, summary counts, DB status class, audit evidence | Exactly one separately approved Preview-only run | Start Upload, Retry Failed, Delete, Settings save, reset, cleanup, LAN, deployment | Preview is latest, fresh, succeeded, DB reachable, and counts match approval ceiling | Risky count > 0, DB unreachable, count mismatch, stale preview, active conflict unresolved | Maintainer/operator | `docs/164_operator_data_mutation_safety_gate.md:80`; `docs/164_operator_data_mutation_safety_gate.md:123`; `docs/173_v2_operational_upload_verification_gate.md:100`; `backend/app/api/upload_preview.py:245` |
| Start Upload approval package, separate and optional | Exact approval text and record naming preview run, target rows, source class, and package commit | Approval preparation only until the operator explicitly approves | Running Start Upload from this plan; bundling Retry Failed/Delete/Settings save | Fresh Preview proves target rows and approval text matches exact target-only rows | Zero target rows, mismatch across UI/API/approval, stale preview, or missing approval | Operator approval with maintainer evidence | `docs/164_operator_data_mutation_safety_gate.md:179`; `docs/164_operator_data_mutation_safety_gate.md:204`; `docs/173_v2_operational_upload_verification_gate.md:125`; `backend/app/api/upload_jobs.py:318` |
| Retry Failed approval package, separate and conditional | Retry approval record naming job id and remaining physical rows | Approval preparation only after failed/retryable job evidence | Automatic retry, broad cleanup, DB reset, or retry without exact remaining rows | Failed/retryable rows are known and separate approval exists | No retryable rows, count unknown, root failure not preserved, or approval missing | Operator approval with maintainer evidence | `docs/164_operator_data_mutation_safety_gate.md:234`; `docs/173_v2_operational_upload_verification_gate.md:151`; `backend/app/api/upload_jobs.py:449`; `frontend/src/pages/UploadPage.tsx:2151` |
| Audit Logs success/failure visibility | Sanitized Audit Logs API/UI evidence for success, failure, and blocked classes | `GET /api/audit?limit=1`; UI Audit Logs observation; non-destructive failure-path validation | Raw params JSON search, arbitrary SQL, secret capture, destructive failure creation | Operators can see relevant safe action/result/reason evidence | Audit unavailable, missing failure rows, unsafe raw values displayed | Maintainer QA and operator | `backend/app/api/audit.py:24`; `backend/app/db/audit_repository.py:96`; `README.md:439`; `docs/175_legacy_gui_replacement_gap_audit.md:30` |
| Job Logs visibility | Upload Job tab or API event evidence for latest job states | Read-only job/detail/event observation; SSE replay observation | Creating upload/retry jobs without approval | Job events and final states are visible and understandable | Missing events, final status unclear, or errors hidden | Maintainer QA and operator | `backend/app/api/upload_jobs.py:622`; `backend/app/db/upload_job_repository.py:1116`; `frontend/src/pages/UploadPage.tsx:2033`; `docs/175_legacy_gui_replacement_gap_audit.md:29` |
| Representative legacy CSV fixture coverage | Test or review evidence for known legacy edge cases | Non-operational fixture tests or Preview-only fixture evidence in disposable/non-production context | Operational upload mutation; raw operational CSV content in evidence | Representative fixtures cover expected legacy parsing/classification cases | Known legacy CSV shape untested or classification drift found | Maintainer QA | `docs/01_development_roadmap.md:126`; `docs/175_legacy_gui_replacement_gap_audit.md:43`; `docs/00_product_scope.md:57` |
| Large real CSV Preview soak | Preview-only soak evidence with sanitized counts and timing | Only after separate Preview-only approval for the real source class | Start Upload, Retry Failed, Delete, cleanup, raw file evidence | Large Preview completes within accepted bounds and produces stable classifications | Timeout, memory failure, risky rows, DB unreachable, or count mismatch | Maintainer/operator | `docs/01_development_roadmap.md:126`; `docs/175_legacy_gui_replacement_gap_audit.md:61`; `docs/173_v2_operational_upload_verification_gate.md:100` |
| Operator-PC browser/UI evidence | Sanitized route screenshots or observations for `/`, `/upload`, `/logs`, `/settings` | Browser route load checks against already running local package; screenshots only after redaction review | Capturing secrets, raw paths, filenames, DB URLs, tokens, internal URLs, CSV content | Routes load in API mode and show expected readiness/log surfaces | Route unavailable, mock mode mistaken as operational, or sensitive data visible | Maintainer/operator | `backend/app/main.py:63`; `backend/app/main.py:74`; `README.md:145`; `README.md:264`; `docs/175_legacy_gui_replacement_gap_audit.md:127` |
| Rollback / stop procedure evidence | Runbook record for stopping app use and reverting to legacy GUI/manual procedure | Documentation review and operator acknowledgement | DB reset/cleanup as rollback; deleting evidence | Stop procedure is understood and no destructive cleanup is required | Rollback depends on destructive cleanup or unavailable legacy fallback | Release owner/operator | `docs/173_v2_operational_upload_verification_gate.md:215`; `docs/171_v2_operational_delete_verification_gate.md:201`; `README.md:135` |
| Destructive delete exclusion or separate `docs/171` package | Either explicit exclusion or a complete destructive approval package | Documentation-only exclusion for V1 cutover; `docs/171` package if delete is requested | Operational DB delete from this plan | Delete is excluded from cutover or separately approved with exact-key scope | Request bundles delete with Preview/Start/Retry/settings/reset/LAN | Operator approval plus maintainer evidence | `docs/171_v2_operational_delete_verification_gate.md:12`; `docs/171_v2_operational_delete_verification_gate.md:119`; `docs/175_legacy_gui_replacement_gap_audit.md:37` |
| LAN exclusion | Localhost-only sign-off | Config/doc review; `/api/health` sanitized LAN state if available | LAN enablement, non-loopback bind, LAN CORS widening, auth/session rollout | V1 remains localhost-only and LAN stays deferred | Non-loopback access requested or LAN feature gate enabled | Release owner | `docs/00_product_scope.md:47`; `backend/app/core/lan_security.py:55`; `backend/app/core/lan_security.py:66`; `docs/165_v2_status_matrix.md:89` |
| Supabase reset/cleanup exclusion | Explicit exclusion record | Documentation review and command-policy review | `supabase init`, `supabase db reset`, Docker rm/prune/compose up/down, volume delete | No reset/cleanup/create command is part of cutover evidence | Missing containers trigger cleanup request instead of blocked evidence | Release owner/maintainer | `README.md:282`; `backend/app/services/command_runner.py:30`; `backend/app/services/command_runner.py:147`; `backend/app/services/command_runner.py:172` |
| Security/secrets redaction | Sanitized evidence review checklist | Redaction review before attaching evidence | Raw paths, filenames, CSV content, DB URLs, tokens, JWTs, Authorization values, exact keys, internal URLs, secrets | Evidence contains only safe ids, classes, counts, hashes, and reason codes | Sensitive value would be written or screenshot cannot be safely redacted | Maintainer/security reviewer | `README.md:40`; `README.md:145`; `backend/app/db/audit_repository.py:96`; `docs/171_v2_operational_delete_verification_gate.md:58` |
| Final sign-off record | Completed sign-off table with decision, evidence ids, accepted package, residual risks, and next action | Documentation-only sign-off | Treating old evidence or future folder growth as approval | Approver accepts exact evidence set and residual risks | Evidence ids missing, package mismatch, stale preview, or unresolved stop condition | Release owner/operator approver | `docs/173_v2_operational_upload_verification_gate.md:190`; `docs/175_legacy_gui_replacement_gap_audit.md:47` |

## Non-Destructive Validation Package

These validations can be prepared or run without mutation approval when they only
observe an already running local operator package and store sanitized output.

Allowed read-only commands or observations:

```powershell
git rev-parse HEAD
git status --short --branch
git show --stat --oneline --name-status HEAD
```

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health |
  ConvertTo-Json -Depth 8
```

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/config |
  ConvertTo-Json -Depth 8
```

Store only sanitized source classes, target classes, modes, override classes,
safe booleans, and non-secret status fields from `/api/config`. Do not store raw
source paths, DB URLs, anon keys, service role values, tokens, JWTs, or
Authorization values.

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/audit?limit=1" |
  ConvertTo-Json -Depth 8
```

```powershell
Invoke-WebRequest http://127.0.0.1:8000/ -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:8000/upload -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:8000/logs -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:8000/settings -UseBasicParsing
```

Docs-disabled route checks, when the package is in operator launcher mode:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/api/docs -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:8000/api/openapi.json -UseBasicParsing
```

Expected result is disabled or unavailable docs in operator mode, not secret or
token output.

Not allowed in this package:

- creating a Preview run;
- cancelling a Preview run;
- starting upload jobs;
- retrying failed upload jobs;
- upload delete preflight/start/reconcile;
- Settings save;
- Local Supabase start/stop;
- Supabase init/reset/migration/backfill/cleanup;
- Docker create/rm/prune/volume delete/compose up/down;
- LAN enablement or non-loopback testing;
- production DB mutation.

## Read-Only Inventory Precheck Template

Use this template before requesting Preview-only approval. It records counts and
classes, not raw operational data.

| Field | Value |
| --- | --- |
| Evidence id | `<inventoryEvidenceId>` |
| Date/time | `<ISO-8601 local time>` |
| Operator PC class | `<operatorPcClass>` |
| Package source commit | `<sourceCommit>` |
| Package label | `<packageLabel>` |
| Source class, not raw path | `<sourceClass>` |
| Observed file count | `<fileCount>` |
| Approved physical row ceiling | `<rowLimit>` |
| Inventory evidence hash or internal record id | `<inventoryHashOrRecordId>` |
| Excluded data | `<excludedDataClasses>` |
| Stop condition result | `<clear | blocked: reason>` |
| Reviewer | `<reviewer>` |

Do not record raw filenames, raw paths, raw CSV content, raw timestamp/device_id
keys, DB URLs, tokens, JWTs, Authorization values, internal URLs, or secrets.

## Preview-Only Approval Template

This approval is separate from the validation plan. It must be filled from a
fresh read-only inventory precheck.

```text
I approve exactly one Upload Preview-only run from package sourceCommit <sourceCommit>.
The approved source class is <sourceClass>.
The approved file count is <fileCount>.
The approved physical row ceiling is <rowLimit>.
This approval does not approve Start Upload, Retry Failed, Delete, Settings save,
feature gate enablement, Supabase reset/cleanup, Docker cleanup, LAN, or deployment.
```

Stop if the requested source class, file count, row ceiling, package commit, or
operator PC differs from the fresh inventory evidence.

## Preview-Only Evidence Template

| Field | Value |
| --- | --- |
| Preview approval id | `<previewApprovalId>` |
| Preview run id | `<previewRunId>` |
| Source class | `<sourceClass>` |
| Status | `<succeeded | failed | blocked | cancelled>` |
| Total files | `<totalFiles>` |
| Target files | `<targetFiles>` |
| Already-in-DB count | `<alreadyInDbCount>` |
| Partial-overlap count | `<partialOverlapCount>` |
| Risky count | `<riskyCount>` |
| Target-only rows | `<targetRows>` |
| Partial-overlap rows | `<partialOverlapRows>` |
| DB status class | `<dbStatusClass>` |
| Runtime readiness class | `<runtimeReadinessClass>` |
| Audit evidence | `<auditEvidenceId>` |
| Confirmation no mutation actions were bundled | `<yes/no plus note>` |

Pass requires `status=succeeded`, DB reachable/expected, `riskyCount=0`, and
matching counts across UI/API/evidence. A Preview with zero target rows may
support `no_upload`; it is not Start Upload evidence.

## Start Upload Approval Template

This is separate and not approved by this validation plan. Request it only after
a fresh, succeeded Preview-only run proves exact target-only rows.

```text
I approve exactly one Start Upload for preview run <previewRunId> with target rows <targetRows>.
This approval is for package sourceCommit <sourceCommit> and source class <sourceClass>.
This approval does not approve Retry Failed, Delete, Settings save, or feature gate enablement.
```

Required before approval:

- fresh succeeded Preview-only evidence;
- preview run id;
- exact target-only rows;
- source class;
- package source commit;
- confirmation partial-overlap rows are not included unless separately approved;
- confirmation `expectedTargetRows` and `expectedTargetFiles` match the latest
  Preview detail.

## Start Upload Evidence Template

| Field | Value |
| --- | --- |
| Start approval id | `<startUploadApprovalId>` |
| Preview run id | `<previewRunId>` |
| Upload job id | `<uploadJobId>` |
| Approved target-only row count | `<targetRows>` |
| Job final status | `<succeeded | failed | blocked | cancelled>` |
| Processed rows | `<processedRows>` |
| Uploaded rows | `<uploadedRows>` |
| Accepted rows | `<acceptedRows>` |
| Audit evidence | `<auditEvidenceId>` |
| Job event evidence | `<jobEventEvidenceId>` |
| DB delta evidence, only if explicitly approved and enabled | `<dbDeltaEvidenceId | not approved>` |
| Row attribution evidence, only if explicitly approved and enabled | `<rowAttributionEvidenceId | not approved>` |
| Unresolved failure condition | `<none | reason>` |

If Start Upload fails after partial mutation, preserve job, audit, DB delta, and
row attribution evidence. Do not run Retry Failed or cleanup without a separate
approval.

## Retry Failed Approval And Evidence Template

Retry Failed is separate and conditional. It is not automatic rollback.

Required before requesting approval:

- failed or retryable upload job evidence;
- job id;
- exact remaining physical rows;
- source class and package commit;
- root failure class preserved;
- confirmation no broad cleanup is requested.

Approval wording:

```text
I approve exactly one Retry Failed for upload job <jobId> with remaining physical rows <remainingRows>.
This approval is for package sourceCommit <sourceCommit>.
This approval does not approve Start Upload, Delete, Settings save, or feature gate enablement.
```

Evidence after retry:

| Field | Value |
| --- | --- |
| Retry approval id | `<retryApprovalId>` |
| Source upload job id | `<jobId>` |
| Retry job id or event id | `<retryJobOrEventId>` |
| Approved remaining physical rows | `<remainingRows>` |
| Retry files | `<retryFiles>` |
| Final status | `<succeeded | failed | blocked | cancelled>` |
| Accepted rows | `<acceptedRows>` |
| Audit evidence | `<auditEvidenceId>` |
| Job event evidence | `<jobEventEvidenceId>` |
| Stop-after-failure confirmation | `<yes/no plus reason>` |

If retry fails, stop. Preserve evidence. Do not run broad DB cleanup, reset, or
manual delete as a workaround.

## Audit Logs Failure-Path Validation

Prove failure visibility without destructive production mutation where possible.
Use sanitized evidence only.

Required failure or blocked classes:

- DB unreachable or DB-dependent blocked class;
- malformed request or validation failure;
- active Preview conflict;
- Settings validation failure;
- runtime blocked state;
- upload config missing or auth invalid class.

Allowed validation methods:

- fixture or development-only malformed requests that do not touch operational
  data;
- read-only inspection of existing Audit Logs for recent blocked/failure rows;
- operator UI observation of Audit Logs filters and safe params;
- runtime status blocked evidence when required containers are missing, without
  cleanup or create commands.

Stop if producing a failure would require operational upload, operational delete,
Settings save, DB reset, Docker cleanup, LAN exposure, or recording raw sensitive
data.

## Operator-PC E2E Checklist

| Item | Evidence id | Status | Notes |
| --- | --- | --- | --- |
| Browser `/` route loads from local package | `<evidenceId>` | `<pending/pass/fail>` | Store sanitized screenshot only. |
| Browser `/upload` route loads in API mode | `<evidenceId>` | `<pending/pass/fail>` | Confirm not mock-only evidence. |
| Browser `/logs` route shows Job Logs and Audit Logs | `<evidenceId>` | `<pending/pass/fail>` | No raw params or secrets. |
| Browser `/settings` route loads read-only before mutation | `<evidenceId>` | `<pending/pass/fail>` | Do not save settings. |
| API mode confirmation | `<evidenceId>` | `<pending/pass/fail>` | Use config/metadata class, not raw URLs. |
| Local token protection confirmation, if available | `<evidenceId>` | `<pending/pass/fail>` | Missing/stale tokens must not reveal token values. |
| Config snapshot | `<evidenceId>` | `<pending/pass/fail>` | Store sanitized classes only. |
| Runtime readiness | `<evidenceId>` | `<pending/pass/fail>` | Status evidence only unless start/stop separately approved. |
| Preview-only readiness | `<evidenceId>` | `<pending/pass/fail>` | Requires separate Preview-only approval before run. |
| Logs/audit visibility | `<evidenceId>` | `<pending/pass/fail>` | Include success/failure/blocked classes where possible. |

Screenshots are allowed only if they do not expose secrets, raw paths, filenames,
raw DB URLs, tokens, JWTs, Authorization values, internal URLs, raw CSV content,
or exact keys.

## Go/No-Go Checklist

| Item | Required before GO | Evidence id | Status | Approver | Notes |
| --- | --- | --- | --- | --- | --- |
| Accepted package/source commit | Yes | `<evidenceId>` | `<pending/pass/fail>` | `<approver>` | Must match package label. |
| README/API smoke contract | Yes | `<evidenceId>` | `<pending/pass/fail>` | `<approver>` | Must include approval counts. |
| Sanitized config snapshot | Yes | `<evidenceId>` | `<pending/pass/fail>` | `<approver>` | Source class only. |
| Local Supabase readiness | Yes | `<evidenceId>` | `<pending/pass/fail>` | `<approver>` | Status evidence required. |
| Read-only inventory precheck | Yes | `<evidenceId>` | `<pending/pass/fail>` | `<approver>` | No guessed counts. |
| Preview-only evidence | Yes, if upload cutover is being evaluated | `<evidenceId>` | `<pending/pass/fail>` | `<approver>` | Separate approval required. |
| Start Upload evidence | Yes when Preview proves approved target rows | `<evidenceId>` | `<pending/pass/fail/not applicable>` | `<approver>` | Separate approval required. |
| Retry Failed evidence | Conditional | `<evidenceId>` | `<pending/pass/fail/not applicable>` | `<approver>` | Only if retryable rows remain. |
| Audit Logs failure visibility | Yes | `<evidenceId>` | `<pending/pass/fail>` | `<approver>` | Safe params only. |
| Job Logs visibility | Yes | `<evidenceId>` | `<pending/pass/fail>` | `<approver>` | Final job status visible. |
| Representative CSV fixture coverage | Yes | `<evidenceId>` | `<pending/pass/fail>` | `<approver>` | Legacy edge coverage. |
| Large real CSV Preview soak | Yes | `<evidenceId>` | `<pending/pass/fail>` | `<approver>` | Preview-only approval required. |
| Operator-PC UI route evidence | Yes | `<evidenceId>` | `<pending/pass/fail>` | `<approver>` | Sanitized screenshots/observations. |
| Rollback/stop procedure | Yes | `<evidenceId>` | `<pending/pass/fail>` | `<approver>` | No reset/cleanup rollback. |
| Delete excluded or separately approved | Yes | `<evidenceId>` | `<pending/pass/fail>` | `<approver>` | Use `docs/171` if needed. |
| LAN excluded | Yes | `<evidenceId>` | `<pending/pass/fail>` | `<approver>` | Localhost-only. |
| Reset/cleanup excluded | Yes | `<evidenceId>` | `<pending/pass/fail>` | `<approver>` | No Supabase/Docker cleanup. |
| Secrets redaction complete | Yes | `<evidenceId>` | `<pending/pass/fail>` | `<approver>` | No raw sensitive data. |
| Final sign-off record | Yes | `<evidenceId>` | `<pending/pass/fail>` | `<approver>` | Decision state recorded. |

## Risk Register

| Risk statement | Severity | Likelihood | Mitigation | Owner or approval gate | Required evidence |
| --- | --- | --- | --- | --- | --- |
| Fresh operational upload evidence is missing at cutover. | High | Medium | Use the `docs/173` chain and stop on stale/mismatched inventory, Preview, package, or approval data. | Operator approval plus maintainer evidence capture | Inventory, Preview-only, Start Upload if target rows exist, Retry Failed if needed |
| Legacy CSV edge-case behavior drifts from the Tkinter GUI. | High | Medium | Expand representative fixture coverage and run large Preview soak before GO. | Maintainer QA | Fixture coverage report and large Preview soak evidence |
| Operator-PC runtime readiness fails during cutover. | High | Medium | Capture local Supabase status evidence and approve start/stop separately only when needed. | Maintainer/operator | Runtime status, operation events if approved, audit rows |
| Audit Logs do not surface critical failures clearly. | High | Medium | Validate success/failure/blocked visibility with sanitized evidence. | Maintainer QA and operator sign-off | Audit Logs API/UI evidence |
| Accidental destructive delete or cleanup is bundled into validation. | Production-critical | Low | Treat delete, reset, cleanup, and Docker destructive commands as hard exclusions unless separately approved. | `docs/171` or new destructive plan | Exclusion record or exact approval package |
| Package/source mismatch leads to testing the wrong build. | High | Low | Verify package metadata and source commit before every evidence package. | Release owner | Package commit, label, and hash/metadata evidence |
| Secrets or raw operational data leak into evidence. | High | Medium | Store only safe classes, counts, ids, hashes, and reason codes; review screenshots before attachment. | Security reviewer/maintainer | Redaction checklist and sanitized artifacts |

## Stop Conditions

Stop before GO, Preview, Start Upload, Retry Failed, delete, or any operator
cutover decision when any of these are true:

- package metadata, source commit, or package label is stale or mismatched;
- read-only inventory is missing, stale, broader than the requested scope, or
  guessed;
- physical row count or target row count is guessed;
- Preview is not fresh, latest, succeeded, and DB reachable;
- risky count is greater than zero;
- target rows mismatch between UI, API, approval text, and evidence;
- Audit Logs evidence is unavailable;
- Job Logs evidence is unavailable for an upload decision;
- source class differs between inventory, Preview, approval, and config evidence;
- raw sensitive data would be written to evidence;
- request bundles Preview, Start Upload, Retry Failed, Delete, Settings save,
  reset, cleanup, LAN, migration, deployment, Docker destructive command, or
  feature gate enablement;
- request asks for Supabase init/reset/migration/backfill/cleanup, Docker
  create/rm/prune/volume delete/compose up/down, LAN exposure, or production DB
  mutation without a separate approved plan.

## Final Sign-Off Record

| Field | Value |
| --- | --- |
| Decision | `<GO | CONDITIONAL GO | NO-GO | BLOCKED | DEFERRED / NOT V1 SCOPE>` |
| Evidence ids | `<evidenceIds>` |
| Accepted package commit | `<sourceCommit>` |
| Accepted package label | `<packageLabel>` |
| Operator PC | `<operatorPcClass>` |
| Reviewer | `<reviewer>` |
| Approver | `<approver>` |
| Date/time | `<ISO-8601 local time>` |
| Residual risks | `<acceptedRisks>` |
| Next action | `<nextAction>` |

Approver acknowledgement:

```text
I reviewed the evidence ids above and approve the recorded decision only for the
accepted package commit, package label, operator PC class, source class, and time
window named in this record. This sign-off does not approve any future upload,
retry, delete, reset, cleanup, migration, LAN exposure, deployment, or feature
gate change outside the evidence and approvals listed here.
```

## Recommended Next Work Packages

### WP-A: non-destructive operator-PC route/config/audit smoke evidence

Goal: capture sanitized route, health, config, and audit visibility evidence
against the accepted package without creating Preview runs or mutating runtime
state.

### WP-B: read-only inventory precheck evidence

Goal: record current source class, file count, physical row ceiling, excluded
data classes, and reviewer sign-off without raw paths, filenames, CSV content,
or exact keys.

### WP-C: Preview-only approval and evidence capture

Goal: request exactly one Preview-only approval using `docs/164` wording, run the
approved Preview-only action, and record sanitized Preview summary, DB status,
runtime readiness class, and audit evidence.

### WP-D: Start Upload approval package, only if Preview proves target rows

Goal: prepare the exact Start Upload approval package after Preview-only evidence
proves target rows. Do not run Start Upload until that approval is explicitly
granted.

### WP-E: Retry Failed approval package, only if failed/retryable rows remain

Goal: preserve failed-job evidence, identify exact remaining physical rows, and
prepare a separate Retry Failed approval if retry is warranted.

### WP-F: destructive delete approval package, only if separately required

Goal: exclude operational delete from V1 cutover by default. If delete is
business-required, use `docs/171` and do not bundle it with upload cutover.

### WP-G: legacy CSV fixture expansion

Goal: expand representative fixture coverage for legacy CSV edge cases and
Preview classifications without using operational data mutation.

### WP-H: large CSV Preview soak

Goal: after separate Preview-only approval, run a large real CSV Preview soak and
record sanitized performance, classification, DB status, and Audit Logs evidence.

## Verification Performed

Commands run for this documentation update:

```powershell
git branch --show-current
git status --short --branch
Test-Path docs/176_v1_cutover_go_no_go_validation_plan.md
git switch main
git pull --ff-only origin main
git switch -c docs/v1-cutover-go-no-go-validation-plan
rg -n "docs/175|Source Documents|Upload Job API smoke|previewRunId|expectedTargetRows|expectedTargetFiles" README.md
rg -n "Core Ops|not in v1|legacy upload state|Success Criteria|localhost|Supabase|Grafana|LAN|delete" docs/00_product_scope.md
rg -n "Core Ops|implemented|validation|evidence|LAN|Supabase|delete|upload verification|large CSV|fixture|Audit Logs" docs/01_development_roadmap.md
rg -n "Implemented Core Ops|Deferred pending approval/evidence|Review shell only|Intentional v1 exclusion|Safety gate" docs/158_operator_status_language_policy.md
rg -n "approval|does not approve|Preview-only|Start Upload|Retry Failed|Delete|Settings save|feature gate|reset|cleanup|LAN|deployment" docs/164_operator_data_mutation_safety_gate.md
rg -n "upload verification|date-scoped|delete expansion|LAN|schema attribution|legacy upload state|reset|cleanup|Deferred|blocked|review shell|operational" docs/165_v2_status_matrix.md
rg -n "does not approve|Already-in-DB|exact-key|approval|preflight|hard delete|Start Upload|Retry Failed|Settings save|reset|cleanup|Docker|LAN|Stop|blocked" docs/171_v2_operational_delete_verification_gate.md
rg -n "does not approve|evidence chain|Preview-only|Start Upload|Retry Failed|approval|sourceCommit|target rows|remaining physical rows|reset|cleanup|Docker|LAN|Stop|blocked|DB delta|row attribution" docs/173_v2_operational_upload_verification_gate.md
rg -n "Core Ops|Must-Fix|Deferred|Evidence Matrix|upload evidence|legacy CSV|large real CSV|operator-PC|Audit Logs|LAN|date-scoped|schema attribution|legacy upload state|reset|cleanup|README" docs/175_legacy_gui_replacement_gap_audit.md
rg -n "class UploadJobCreateRequest|expected_target_rows|expected_target_files|class RetryFailedRequest|expected_remaining_rows|expected_retry_files" backend/app/schemas/upload_jobs.py
rg -n "expected_target_rows_required|expected_remaining_rows_required|preview_run_id|expected_target_rows|expected_target_files|expected_remaining_rows|expected_retry_files" backend/app/api/upload_jobs.py
rg -n "to_camel|populate_by_name|target_rows|partial_overlap_rows|already_in_db|partial_overlap|risky|preview_run_id" backend/app/schemas/upload_preview.py
rg -n "expectedTargetRows|expectedTargetFiles|expectedRemainingRows|expectedRetryFiles|previewRunId" frontend/src/api/uploadJobs.ts frontend/src/pages/UploadPage.tsx
rg -n "@router.get|@router.put|api/config|settings.save|save_config|secret" backend/app/api/config.py backend/app/services/config_service.py
rg -n "@router.get|Audit|limit|safe|redact|AuditLog" backend/app/api/audit.py backend/app/db/audit_repository.py
rg -n "@router.post|@router.get|active_preview|upload.preview|blocked|dbStatus|previewRunId|summary|cancel" backend/app/api/upload_preview.py
rg -n "supabase start|supabase init|supabase db reset|docker rm|docker compose down|FORBIDDEN|allowed|start|stop|reset|cleanup|prune|rm|compose down|init" backend/app/services/runtime_control.py backend/app/services/command_runner.py
```

Files changed by this documentation update:

- `README.md`
- `docs/176_v1_cutover_go_no_go_validation_plan.md`

Tests run:

- Runtime tests were not run because this is a documentation-only change.

Checks run before commit:

- `git status --short --branch`: only `README.md` and
  `docs/176_v1_cutover_go_no_go_validation_plan.md` changed.
- `git diff --check`: passed; Git reported only the existing README
  working-copy LF-to-CRLF normalization warning and no whitespace errors.
- `git diff -- README.md`: Source Documents update only.
- `git status --short --branch`: confirms the new validation-plan document is
  untracked before staging and no runtime/code files are changed.

Forbidden commands intentionally not run:

- no Start Upload;
- no Retry Failed;
- no Upload Preview execution;
- no DB delete;
- no Settings save;
- no Local Supabase start/stop;
- no Supabase init/reset/migration/backfill/cleanup;
- no Docker cleanup/rm/prune/volume delete/compose up/down;
- no LAN enablement;
- no deployment;
- no production DB access.
