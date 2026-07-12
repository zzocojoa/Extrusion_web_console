# Legacy GUI Replacement Gap Audit

## Executive Summary

Core Ops is mostly implemented in the current repository. The actual code has
Upload Preview, Start Upload, Retry Failed, upload progress/event logs, Audit
Logs, Settings save, local Supabase status/start/stop, Grafana status/link, and
the selected `already_in_db` exact-key delete path.

The remaining legacy-GUI-replacement work is not mainly new feature
implementation. V2 WP-01, the separately approved post-merge Preview-only run,
and later operator-PC read-only observations now
cover representative CSV compatibility, deterministic large-Preview soak,
Audit failure-path queries, a successful real `folder_all` Preview, runtime
readiness, Job/Audit Logs visibility, and Core Ops route rendering. Final
cutover still needs accepted package metadata, a compliant pre-Preview inventory
record, human disposition of partial-overlap rows, release-owner/operator
sign-off, and explicit ownership of the non-core Grafana/Vector attention state.

The following are not v1 cutover blockers unless separately re-scoped:
Multi-user LAN, executable date-scoped delete UI, delete expansion beyond the
selected `already_in_db` exact-key contract, Supabase schema attribution
migration/backfill, legacy GUI state import, and local Supabase
bootstrap/create/reset/cleanup.

## Evidence Matrix

| Area | Current classification | Actual code behavior | Documentation evidence | Remaining gate | Business risk | Recommended next action | Evidence paths with line references |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Upload Preview | Implemented Core Ops; operator Preview behavior passed | `POST /api/upload/preview`, latest/detail/cancel routes exist; results are persisted and exact DB reconciliation is supported when DB URL is configured. | V2 WP-01 covers DB-status correctness, legacy fixtures, and a deterministic 25,000-row soak. Separately approved operator-PC run `prv_ca38650a9e7d` completed `folder_all` as `succeeded/reachable` with 12 files, `target=0`, `risky=0`, and 64,766 partial-overlap rows excluded from target-only upload. | Future Preview or mutation decisions require fresh package/source and scope evidence; this run does not approve Start Upload. Human disposition of partial-overlap rows is still required for cutover. | Medium: stale binding or hidden partial overlap can produce a wrong readiness decision. | Preserve the run as Preview-only evidence, not read-only evidence; bind formal inventory/package records and disposition partial overlap before cutover. | `backend/app/api/upload_preview.py`; `tests/backend/test_upload_preview_reconciliation.py`; `tests/backend/test_upload_preview_large_synthetic_soak.py`; `docs/01_development_roadmap.md`; `README.md` |
| Start Upload | Implemented Core Ops with safety gate | API rejects missing/non-positive `expectedTargetRows`, checks runtime/upload config, and repository requires latest fresh succeeded DB-reachable preview with target rows and matching expected counts. Frontend sends target row/file approval counts. | V2 upload verification document says Start Upload still requires separate exact approval after Preview evidence. | Exact approval and fresh Preview evidence before any operational Start Upload. | High: running against stale preview/source can upload unintended rows. | Use `docs/173` four-step chain and record approved target-only row count. | `backend/app/api/upload_jobs.py`; `backend/app/db/upload_job_repository.py`; `frontend/src/api/uploadJobs.ts`; `frontend/src/pages/UploadPage.tsx`; `docs/173_v2_operational_upload_verification_gate.md` |
| Retry Failed | Implemented Core Ops with safety gate | Retry API rejects missing/non-positive `expectedRemainingRows`, checks runtime/upload config, and creates retry jobs only after repository validation. Frontend sends expected remaining rows/files. | V2 upload verification allows Retry Failed only after separate approval and only if failed/retryable rows remain. | Separate retry approval naming remaining physical rows. | Medium-high: retrying wrong job or count can duplicate work or hide failure cause. | Record failed-job evidence first, then request retry approval only when needed. | `backend/app/api/upload_jobs.py`; `frontend/src/api/uploadJobs.ts`; `frontend/src/pages/UploadPage.tsx`; `docs/173_v2_operational_upload_verification_gate.md` |
| Upload progress/logs | Implemented Core Ops; reliability and visibility evidence passed | SQLite job events are appended/listed; SSE endpoint streams event replay/heartbeats; frontend opens `EventSource` and renders job events/progress. | PR #229 adds single-snapshot terminal-close correctness and deterministic concurrency regression coverage. Read-only operator-PC checks returned the latest terminal `succeeded` job with persisted events and rendered Job Logs without browser errors. | A future mutation run still needs separate approval; no operational failure was created for this evidence. | Low-medium: future worker/Edge failures still require operator review at execution time. | Keep deterministic recovery/SSE tests and recheck Job Logs during any separately approved mutation. | `backend/app/api/upload_jobs.py`; `backend/app/db/upload_job_repository.py`; `frontend/src/pages/LogsPage.tsx`; `tests/backend` |
| Audit Logs | Implemented Core Ops; failure visibility evidence passed | `GET /api/audit` supports filters/pagination; audit table has append-only triggers; query search is limited to safe scalar fields. | V2 WP-01 adds representative failure/blocked API coverage. Read-only operator-PC inspection returned existing success, failure, blocked, and cancelled classes, and the Audit Logs UI rendered across all tested viewports without console or request errors. | Final human cutover sign-off remains; do not manufacture operational failures solely for evidence. | Low-medium: new failure classes must remain sanitized and understandable. | Retain automated failure-path coverage and review Audit Logs during future approved operations. | `backend/app/api/audit.py`; `backend/app/db/audit_repository.py`; `tests/backend/test_audit_failure_paths.py`; `frontend/src/pages/LogsPage.tsx` |
| Local Supabase status/start/stop | Implemented Core Ops; readiness evidence passed | Runtime start blocks when required containers are missing, starts only stopped allowed containers or `supabase start` after container precheck, and writes runtime audits. Command runner forbids init/reset/create/rm/prune/up/down. | Current operator-PC read-only status reports Docker, WSL, CLI, API, DB, Studio, and Edge ready with no missing required container. Overall remains `attention` only because Grafana is unreachable and Vector is unhealthy. | App-controlled start/stop evidence is required only when separately approved and needed for the cutover; non-core attention needs explicit disposition. | Medium: core runtime is ready, but lifecycle recovery and non-core attention must not be confused. | Accept or resolve the Grafana/Vector caveat, name an owner, and keep reset/cleanup prohibited. | `backend/app/services/runtime_control.py`; `backend/app/services/command_runner.py`; `README.md`; `docs/167_v2_observability_hardening_evidence.md` |
| Grafana status/link | Implemented Core Ops, link only | Dashboard exposes Grafana chip/status and an external `Open Grafana` link; no iframe behavior is implemented. | Scope includes Grafana status/link only and excludes iframe embedding. | Resolve the observed Grafana/Vector attention or record explicit residual-risk acceptance, an owner, and a non-destructive stop/rollback procedure. | Low-medium: Grafana attention is non-core unless it affects upload evidence. | Keep as status/link only; do not embed. | `backend/app/api/dashboard.py`; `docs/00_product_scope.md`; `README.md` |
| Settings save | Implemented Core Ops | `GET /api/config` and `PUT /api/config` exist; save validates payload, blocks env-overridden keys, writes config atomically, clears settings cache, and records `settings.save` audit rows. | Roadmap marks config API and Settings save UI done. | Operator validation only; no new feature implementation needed. | Medium: wrong settings can bind wrong source/target if operator process is not controlled. | Include read-only `GET /api/config` snapshot before Preview evidence. | `backend/app/api/config.py`; `backend/app/services/config_service.py`; `docs/01_development_roadmap.md` |
| Already-in-DB exact-key delete | Implemented backend/API/UI path, operator mutation requires separate approval | Backend preflight/start/reconcile only accepts selected Preview items still classified as `already_in_db`; frontend selection is limited to `already_in_db` rows and requires preflight, typed count, and rollback acknowledgement. | v1 scope includes this only when separately approved and guarded. README describes it as production-critical maintenance, not general cleanup. | Destructive operational DB delete verification and exact approval before any operational delete. | Production-critical: irreversible DB mutation if approval or evidence is wrong. | Treat as available code path but blocked for operational execution until `docs/171` approval package exists. | `backend/app/services/upload_delete.py`; `frontend/src/pages/UploadPage.tsx`; `docs/00_product_scope.md`; `README.md` |
| Operator-facing date-scoped delete UI | Review shell only, not executable UI | Backend feature gate reports `implemented=False` with `review_shell_implemented=True`; frontend renders a blocked disabled panel only when `reviewShellVisible`; frontend API wrapper does not send timestamp scope. | `docs/168` states the shell is non-mutating and no date-scoped API/preflight/job start is implemented. `docs/165` classifies executable UI as deferred. | Role model, policy/preflight/start, fixture evidence, production approval, rollback, and explicit gate enablement. | High if misunderstood as executable cleanup capability. | Do not expose as normal operator action; keep deferred. | `backend/app/services/config_service.py`; `frontend/src/api/uploadDelete.ts`; `frontend/src/pages/UploadPage.tsx`; `docs/168_v2_date_scoped_delete_ui_gate.md`; `docs/165_v2_status_matrix.md` |
| Delete expansion | Deferred V2 feature | Feature gate is `implemented=False`; no broader delete policy is executable. Current code remains selected `already_in_db` exact-key only. | `docs/170` says the only baseline delete path is selected `already_in_db` exact-key and any expansion needs explicit policy and fixture proof. | Policy limits, fixture DB evidence, production approval format, reconcile/audit/rollback proof. | Production-critical if broadened without proof. | Keep out of v1 cutover; prepare future fixture-first design only. | `backend/app/services/config_service.py`; `docs/170_v2_delete_expansion_fixture_gate.md`; `docs/165_v2_status_matrix.md` |
| Operational DB delete verification | Deferred pending approval/evidence | Code path exists for selected exact-key delete, but operational DB mutation was not run in this audit and remains gated. | `docs/171` explicitly does not approve operational DB access/delete/reconcile and defines the approval record and checklist. | Immutable/append-only approval record, exact scope, fresh preflight, post-run evidence, rollback evidence. | Production-critical. | Build a destructive-operation approval package separately; do not bundle with cutover docs. | `docs/171_v2_operational_delete_verification_gate.md` |
| Operational upload verification | Partial: Preview-only behavior passed | Preview/Start/Retry code exists with approval-count gates. One separately approved operator-PC Preview-only run succeeded with DB reachable and `target=0`; Start Upload remained disabled, so Start Upload and Retry Failed were not applicable and were not executed. The run also reported 64,766 partial-overlap rows excluded from target-only upload. | `docs/173` remains the four-step evidence chain and `docs/164` remains the approval wording. `docs/165` classifies this item as Partial. | Accepted package metadata, compliant inventory evidence, partial-overlap disposition, and final sign-off remain. Any future nonzero target requires fresh Start Upload approval. | Medium: this proves Preview behavior, not complete cutover evidence or a new data-mutation path. | Use the result as `no target-only upload` evidence only; do not imply all local rows are DB-matched or create mutation work merely to obtain test evidence. | `backend/app/api/upload_jobs.py`; `docs/173_v2_operational_upload_verification_gate.md`; `docs/165_v2_status_matrix.md`; `docs/176_v1_cutover_go_no_go_validation_plan.md` |
| Multi-user LAN | Deferred V2 feature, default-off guard implemented | `v2_lan_access_enabled` exists, LAN health state reports blocked reasons, and HTTP middleware rejects non-loopback server/client access. If LAN flag is enabled, missing auth/session/concurrency reasons are reported. | `docs/172` says the slice does not implement Multi-user LAN and does not approve non-loopback bind/CORS/auth/session rollout. | Auth/authz, sessions, actor audit, concurrency model, CORS/bind approval, tests, explicit rescope. | High if accidentally exposed; current guard reduces risk. | Keep localhost-only for v1; future LAN work must start from `docs/172`. | `backend/app/core/settings.py`; `backend/app/core/lan_security.py`; `backend/app/main.py`; `docs/172_v2_lan_security_gate.md`; `docs/00_product_scope.md` |
| Supabase schema attribution | Deferred V2 feature; local sidecar foundation exists | Local SQLite `row_attribution_ledger` schema exists with append-only triggers and default-off writes. No Supabase migration/backfill is approved or implemented. | `docs/169` approves only local sidecar phase and defines future `public.metric_row_attribution_evidence` as deferred shape. | Written approval before Supabase migration/backfill/fixture mutation/operational DB access. | Medium: current audit depth is local sidecar, not Supabase-native row attribution. | Keep sidecar only for v1; use future migration design gate if needed. | `backend/app/db/row_attribution_repository.py`; `docs/169_v2_supabase_schema_attribution_design.md` |
| Legacy upload state import | Intentional v1 exclusion | No default legacy GUI `uploader_state.db` import path was found or required; new state store is the intended path. | Product scope and README say the legacy GUI state is not imported by default and the new app starts with a new state store. | None for v1; only re-scope if business explicitly requires import. | Low if operators understand Preview reconciliation replaces state import. | Keep excluded; rely on Supabase-backed Preview/reconciliation. | `docs/00_product_scope.md`; `README.md`; `AGENTS.md` |
| Local Supabase bootstrap/create/reset/cleanup | Intentional v1 exclusion and safety restriction | Command runner forbids `supabase init`, reset, Docker create/rm/prune/up/down. Runtime start blocks missing containers instead of creating a stack. | README says runtime control does not run bootstrap/reset/cleanup/create/delete/volume/prune and v1 does not create a new stack. | Maintainer-only setup outside the app if the stack is missing. | High if bypassed; destructive cleanup can destroy evidence or data. | Preserve non-destructive runtime control; document manual recovery separately. | `backend/app/services/command_runner.py`; `backend/app/services/runtime_control.py`; `README.md` |
| Legacy CSV fixture and soak validation | Completed for V2 WP-01 Preview-only/observation scope | Current main covers representative UTF-8/CP949 PLC, temperature, and integrated fixtures, exact reconciliation and DB-status semantics, a deterministic 25,000-row synthetic soak, and one approved large real `folder_all` Preview. | Roadmap and `docs/11` record the automated foundation; WP-02 consolidates the operator evidence and leaves final cutover sign-off separate. | Preserve coverage and repeat operational Preview only when accepted package/source scope changes. | Low-medium: unrepresented future CSV shapes can still regress. | Add fixtures when a new legacy shape is discovered; do not use operational mutation as a fixture substitute. | `tests/backend/fixtures`; `tests/backend/test_upload_preview_large_synthetic_soak.py`; `tests/backend/test_upload_preview_reconciliation.py`; `docs/11_upload_preview_large_csv_soak.md`; `docs/01_development_roadmap.md` |
| README/API smoke instruction consistency | Documentation inconsistency fixed in this audit | Backend requires `expectedTargetRows` for Upload Job start and validates optional `expectedTargetFiles`; README smoke now fetches preview detail and posts both fields. | Existing start-upload contract analysis says missing/non-positive expected target rows are blocked by design. | None after this docs-only correction; future smoke docs must track approval-count contracts. | Medium: stale smoke docs cause false negative API checks or unsafe ad hoc workarounds. | Keep API smoke examples tied to backend approval contracts. | `backend/app/api/upload_jobs.py`; `backend/app/db/upload_job_repository.py`; `docs/03-analysis/start-upload-expected-count-contract.analysis.md`; `README.md` |
| Cleanup candidates | Duplicate LAN setting resolved; no Core Ops blocker | V2 WP-01 removed the duplicate `v2_lan_access_enabled` declaration. `UploadDbEvidenceClient` remains an intentional abstract/test seam while production defaults to `PsycopgUploadDbEvidenceClient`. | PR #230 and current `backend/app/core/settings.py` contain one LAN flag declaration. | None for V1 cutover. | Low. | Keep the abstraction; no standalone cleanup package is needed. | `backend/app/core/settings.py`; `backend/app/services/upload_jobs.py` |

## Must-Fix Before Legacy GUI Replacement

### Functional blockers

- No unimplemented Core Ops code blocker was found in this audit for Preview,
  Start Upload, Retry Failed, progress/logs, Audit Logs, Settings, local
  Supabase status/start/stop, Grafana link/status, or selected `already_in_db`
  exact-key delete.

### Operational validation blockers

- Preview execution behavior passed for the observed operator-PC source: DB
  reachable, `target=0`, `risky=0`, and 64,766 partial-overlap rows excluded
  from target-only upload. The formal `docs/173` chain remains incomplete until
  the compliant pre-Preview inventory record is located or the chain is repeated
  under a future fresh approval. Start Upload and Retry Failed are not
  applicable to the current evidence window.
- Representative legacy CSV fixtures, synthetic large Preview, real
  `folder_all` Preview, runtime readiness, Job Logs visibility, Audit Logs
  success/failure/blocked visibility, and Core Ops route rendering are complete.
- Current cutover execution is `NO-GO`. A `CONDITIONAL GO` candidate requires
  accepted package metadata, a compliant pre-Preview inventory record, human
  disposition of partial-overlap rows, final release-owner/operator sign-off,
  and resolution or explicit acceptance of the non-core Grafana/Vector
  attention state with an owner and stop procedure.
- App-controlled Local Supabase start/stop evidence remains separate and is
  required only when the accepted cutover procedure actually needs lifecycle
  control.

### Documentation blockers

- README Upload Job API smoke instructions were stale because they omitted
  `expectedTargetRows`. This audit updates the smoke example to post
  `expectedTargetRows` and `expectedTargetFiles` from the preview detail.
- No other direct doc/code contradiction was found in the mandatory files.

### Operator approval blockers

- Any operational Start Upload still needs exact approval after fresh Preview
  evidence.
- Retry Failed needs a separate approval and exact remaining-row count only if
  a retryable failure remains.
- Any operational DB delete needs the `docs/171` approval record and evidence
  package before execution.

## Deferred / Not Required For V1 Cutover

- Multi-user LAN web access.
- Executable operator-facing date-scoped delete UI.
- Delete expansion beyond selected `already_in_db` exact-key delete.
- Operational DB delete verification unless a destructive maintenance run is
  explicitly part of the cutover acceptance.
- Supabase schema attribution migration/backfill.
- Legacy GUI upload state import.
- Local Supabase bootstrap/create/reset/cleanup, Docker cleanup, volume delete,
  prune, `supabase init`, and `supabase db reset`.
- Data Mgmt archive/delete flows, Supabase Mgmt delete UI, Cycle Ops, Training
  Dataset Builder, Cloud Supabase migration, and Grafana iframe embedding.

## Risk Register

| Risk | Severity | Likelihood | Mitigation | Owner or approval gate | Required evidence |
| --- | --- | --- | --- | --- | --- |
| A later cutover reuses stale Preview evidence after package/source scope changes. | High | Medium | Re-enter the `docs/173` sequence and stop on package/source/Preview mismatch. | Operator approval plus maintainer evidence capture. | Current package metadata, fresh inventory/Preview, Start evidence only if target rows exist, Retry evidence only if needed. |
| A future legacy CSV shape diverges from the Tkinter behavior. | High | Low-medium | Add a representative fixture when the shape is discovered and rerun Preview reconciliation/soak tests. | Maintainer validation. | Fixture result and sanitized Preview classification evidence. |
| Non-core Grafana/Vector attention is mistaken for core API/DB failure or silently ignored. | Medium | Medium | Record the caveat, owner, and stop/rollback rule; resolve it before unconditional GO if the approver will not accept it. | Release owner/operator. | Sanitized runtime status and residual-risk acknowledgement. |
| A new failure class is not understandable in Audit Logs. | High | Low-medium | Keep automated success/failure/blocked coverage and inspect logs during future approved operations. | Maintainer QA and operator sign-off. | Safe Audit API/UI evidence. |
| Destructive DB delete is run without exact approval/evidence. | Production-critical | Low if gates are followed | Keep operational delete blocked until `docs/171` record exists. | Operator destructive approval. | Approval record, ready preflight, exact key count, hashes, rollback readiness, post-run evidence. |
| LAN exposure is mistaken as available because a guard exists. | High | Low | Keep localhost-only and classify LAN as deferred. | Future LAN security gate. | Auth/session/concurrency/CORS/bind tests and explicit rescope. |
| Supabase-native attribution is assumed complete. | Medium | Medium | Document local sidecar-only state and defer migration/backfill. | Future schema attribution gate. | Migration design, rollback, fixture mutation proof, operational approval. |
| Smoke docs drift from backend approval contracts. | Medium | Low after this update | Keep README smoke examples aligned with required approval fields. | Maintainer docs review. | `git diff --check` and API contract review. |

## Recommended Next Work Packages

### WP1: documentation consistency fixes

- Status: complete. README approval-count contracts and the current roadmap,
  V2 matrix, gap audit, and cutover recommendation are aligned.

### WP2: non-destructive validation coverage

- Status: complete for V2 WP-01 Preview-only/observation scope. Representative legacy fixtures,
  deterministic synthetic soak, approved real `folder_all` Preview, and
  failure/blocked Audit coverage are present.

### WP3: operator-PC E2E evidence capture

- Status: partial, sufficient only for a future `CONDITIONAL GO` candidate. Sanitized
  config/target classes, runtime readiness, Preview-only result, Job/Audit Logs,
  and Core Ops routes are captured. Accepted package metadata, a compliant
  pre-Preview inventory record, final human sign-off, and non-core caveat
  ownership remain; start/stop operation evidence is conditional on whether the
  accepted cutover procedure needs lifecycle control.
- Do not run reset, cleanup, container deletion, or upload mutation to close
  documentation evidence gaps.

### WP4: destructive operation approval package

- Do not prepare Start Upload or Retry Failed for the current evidence window:
  the approved Preview has zero target-only rows, 64,766 partial-overlap rows
  excluded from upload, and no retryable job.
- Prepare a separate approval package following `docs/173` only if a future
  fresh Preview proves nonzero target rows or a separately approved upload
  produces retryable rows.
- Prepare a separate package for selected `already_in_db` exact-key delete only
  if cutover acceptance requires destructive delete evidence, following
  `docs/171`.

### WP5: future LAN design gate

- Start only after v1 cutover readiness is resolved.
- Define auth, sessions, roles, actor audit, concurrency, CORS, bind policy,
  rollback, and test strategy before changing runtime exposure.

### WP6: future Supabase attribution migration design gate

- Start only after local sidecar needs are proven insufficient.
- Define `public.metric_row_attribution_evidence`, migration/backfill/rollback,
  fixture mutation, and operational approval before any DB schema mutation.

## WP-02 Update Verification

- Current `main` and `origin/main` matched `5695b93` before documentation edits.
- Sanitized health/config/runtime observations confirmed aligned target classes
  and ready API/DB/Studio/Edge services; Grafana/Vector remained non-core
  attention.
- Read-only latest Preview, Audit, and Upload Job queries confirmed the evidence
  summarized above without creating a run or job.
- `npm run qa:backend-served-responsive` passed six Core Ops views across seven
  viewports with no layout issues, console errors, or failed requests.
- `git diff --check` passed after the WP-02 documentation edits.
- No Preview, Start Upload, Retry Failed, delete, Settings save, runtime
  lifecycle operation, LAN, deployment, migration, reset, cleanup, or data
  mutation was executed by WP-02.

## Original Audit Verification Performed

### Commands run

- `git status --short`
- `rg -n "v2_lan_access_enabled|lan_auth_not_implemented|v2_date_scoped_delete_ui|v2_delete_expansion|timestamp_start_date|timestampStartDate|already_in_db|UploadDbEvidenceClient|PsycopgUploadDbEvidenceClient|row_attribution_ledger|metric_row_attribution_evidence|supabase start|supabase init|supabase db reset|docker rm|expected_target_rows|expectedTargetRows" AGENTS.md README.md docs backend frontend`
- `rg -n` targeted searches for V2 status docs, upload approval fields, delete gates, runtime command allowlist, Audit Logs, Settings save, Grafana, and row attribution.
- Targeted `Get-Content` line extraction for required source files and status/gate documents.

### Commands intentionally not run

- No actual upload to operational Supabase.
- No actual delete from operational Supabase.
- No `supabase init`.
- No `supabase db reset`.
- No `docker rm`, `docker compose down`, volume delete, prune, or cleanup.
- No schema migration or backfill.
- No LAN enablement or non-loopback exposure.

### Tests run

- `git diff --check` passed with exit code 0. Git reported an LF-to-CRLF
  working-copy normalization warning for `README.md`; no whitespace errors were
  reported.

### Tests not run and why

- Backend pytest and frontend typecheck/build/build:api were not required
  because no Python or TypeScript runtime code changed.
- Operational E2E tests were not run because they require operator approval,
  target PC/runtime evidence, and in some cases production mutation gates.

### Files changed

- `README.md`: fixed Upload Job API smoke example to include backend-required
  approval counts from preview detail.
- `docs/175_legacy_gui_replacement_gap_audit.md`: added this evidence-backed
  readiness/gap audit.
