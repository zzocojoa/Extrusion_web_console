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
readiness, Job/Audit Logs visibility, and Core Ops route rendering. `docs/182`
now records a later package-bound inventory baseline. Final cutover first needs
production atomic content-manifest binding, bounded unrenewable Start/Retry
leases with target-side transaction fences/durable outcome markers, transaction-
time exact-absence/no-overwrite protection, commit-unknown recovery, whole-
attempt Retry reconciliation, deterministic replacement, concurrency, tamper,
replay, lease-disposition, target-drift, and commit-window tests, and a rebuilt
verified package. Only then
must a separately controlled pre-provisioned verified target baseline already
exist; then an execution-adjacent successor inventory with human-supplied
operator/source bindings, a separately approved protected single-use manifest
preparation, separately approved read-only target-identity preparation with human
exact-match review, and a later separately approved current Preview may be
prepared. This chain does not authorize baseline provisioning/rotation. Any
required human disposition of
partial-overlap rows, release-owner/operator sign-off, and explicit ownership of
the non-core Grafana/Vector attention state also remain. `docs/182` does not
retroactively validate the earlier Preview.

The following are not v1 cutover blockers unless separately re-scoped:
Multi-user LAN, executable date-scoped delete UI, delete expansion beyond the
selected `already_in_db` exact-key contract, Supabase schema attribution
migration/backfill, legacy GUI state import, and local Supabase
bootstrap/create/reset/cleanup.

## Evidence Matrix

| Area | Current classification | Actual code behavior | Documentation evidence | Remaining gate | Business risk | Recommended next action | Evidence paths with line references |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Upload Preview | Implemented Core Ops behavior; future operational Preview blocked by atomic-binding and trusted-target gaps | `POST /api/upload/preview`, latest/detail/cancel routes exist; results are persisted and exact DB reconciliation is supported when DB URL is configured. The current file signature is size plus mtime and does not atomically bind approved content to the bytes Preview parses or retain verified bytes for Start/Retry. Current safe target classes also do not prove the configured DB is the expected installation. | V2 WP-01 covers DB-status correctness, legacy fixtures, and a deterministic 25,000-row soak. Separately approved operator-PC run `prv_ca38650a9e7d` completed `folder_all` as `succeeded/reachable` with 12 files, `target=0`, `risky=0`, and 64,766 partial-overlap rows excluded from target-only upload. `docs/182` records a later package-bound inventory baseline. | Implement a protected manifest/full-byte immutable-snapshot lifecycle retained through Preview/Start/Retry and a pre-provisioned owner-only trusted target baseline whose expected exact identity is checked before binding publication, including explicit byte ceiling, capacity/confidentiality, retention/disposition controls and deterministic replacement/concurrency/tamper/replay/source-reopen/first-observation-wrong-DB tests; then rebuild/verify. | Production-critical: source bytes can change after metadata verification or before Start/Retry; first observation can trust a wrong same-port DB without an independent baseline; full operational copies also create confidentiality/retention risk if hidden or uncontrolled. | Preserve the earlier run only for its historical scope. Make protected atomic manifest/snapshot and trusted-target binding lifecycles/tests the next implementation work package; do not request preparation or Preview approval first. | `backend/app/api/upload_preview.py`; `backend/app/services/upload_preview.py`; `tests/backend/test_upload_preview_reconciliation.py`; `tests/backend/test_upload_preview_large_synthetic_soak.py`; `docs/01_development_roadmap.md`; `README.md` |
| Start Upload | Core Ops request/count checks implemented; operational execution blocked by approval/snapshot-lifecycle gaps | API rejects missing/non-positive `expectedTargetRows`, checks runtime/upload config, and repository requires latest fresh succeeded DB-reachable Preview with matching target counts. It does not atomically claim an immutable/authenticated single-use Start approval and Preview snapshot with one unrenewable lease/mutation id, provide a target-fenced durable outcome marker, prevent workers reopening source, or transactionally revalidate the exact target-only keyset before no-overwrite writes. | `docs/164` and `docs/173` require protected approval, same-snapshot lifecycle, target transaction marker, transaction-time exact-absence/no-overwrite enforcement, and commit-unknown recovery before wording can authorize execution. | Lifecycle/fence/marker/target-drift implementation/tests, fresh atomic-bound Preview, then exact protected Start approval bound to snapshot/evidence/duration/margin/absent set. | Production-critical: replay/substitution/concurrency, source replacement, target-state drift, retention/disposition race, or crash after remote commit before local release can overwrite a row, create duplicate/unknown mutation, or falsely certify rollback. | Implement/test atomic approval/snapshot/lease/mutation-id job claim, snapshot-only reads, target-transaction marker, serializable exact-absence/conflict rollback, post-commit crash reconciliation, and disposition exclusion; request Start only for nonzero target rows. | `backend/app/api/upload_jobs.py`; `backend/app/db/upload_job_repository.py`; `frontend/src/api/uploadJobs.ts`; `frontend/src/pages/UploadPage.tsx`; `docs/173_v2_operational_upload_verification_gate.md` |
| Retry Failed | Core Ops request/count checks implemented; operational execution blocked by approval/snapshot-lifecycle gaps | Retry API validates remaining counts and failed/retryable source jobs, but does not atomically claim an immutable/authenticated single-use Retry approval and source-job snapshot with one unrenewable lease/mutation id, provide a target-fenced durable outcome marker, distinguish cursor remainder from the post-rollback still-absent subset, or transactionally revalidate that exact keyset before no-overwrite writes. | `docs/164` and `docs/173` require protected approval, same-snapshot lifecycle, target transaction marker, transaction-time exact-absence/no-overwrite enforcement, commit-unknown recovery, and whole-attempt reconciliation before wording can authorize execution. | Lifecycle/fence/marker/target-drift implementation/tests, authoritative rollback plus fresh whole-attempt DB reconciliation, then exact protected Retry approval bound to snapshot/evidence/duration/margin/absent set. | Production-critical: replay/substitution/concurrency, source replacement, target-state drift, commit-acknowledgement loss, or cursor-only Retry can overwrite a row, duplicate mutation, or silently omit rolled-back rows. | Implement/test atomic approval/snapshot/lease/mutation-id retry claim, target-marker recovery, fresh whole-attempt reconciliation after rollback, serializable exact-absence/conflict rollback, snapshot-only reads, and disposition exclusion. | `backend/app/api/upload_jobs.py`; `frontend/src/api/uploadJobs.ts`; `frontend/src/pages/UploadPage.tsx`; `docs/173_v2_operational_upload_verification_gate.md` |
| Upload progress/logs | Implemented Core Ops; reliability and visibility evidence passed | SQLite job events are appended/listed; SSE endpoint streams event replay/heartbeats; frontend opens `EventSource` and renders job events/progress. | PR #229 adds single-snapshot terminal-close correctness and deterministic concurrency regression coverage. Read-only operator-PC checks returned the latest terminal `succeeded` job with persisted events and rendered Job Logs without browser errors. | A future mutation run still needs separate approval; no operational failure was created for this evidence. | Low-medium: future worker/Edge failures still require operator review at execution time. | Keep deterministic recovery/SSE tests and recheck Job Logs during any separately approved mutation. | `backend/app/api/upload_jobs.py`; `backend/app/db/upload_job_repository.py`; `frontend/src/pages/LogsPage.tsx`; `tests/backend` |
| Audit Logs | Implemented Core Ops; failure visibility evidence passed | `GET /api/audit` supports filters/pagination; audit table has append-only triggers; query search is limited to safe scalar fields. | V2 WP-01 adds representative failure/blocked API coverage. Read-only operator-PC inspection returned existing success, failure, blocked, and cancelled classes, and the Audit Logs UI rendered across all tested viewports without console or request errors. | Final human cutover sign-off remains; do not manufacture operational failures solely for evidence. | Low-medium: new failure classes must remain sanitized and understandable. | Retain automated failure-path coverage and review Audit Logs during future approved operations. | `backend/app/api/audit.py`; `backend/app/db/audit_repository.py`; `tests/backend/test_audit_failure_paths.py`; `frontend/src/pages/LogsPage.tsx` |
| Local Supabase status/start/stop | Implemented Core Ops; readiness evidence passed | Runtime start blocks when required containers are missing, starts only stopped allowed containers or `supabase start` after container precheck, and writes runtime audits. Command runner forbids init/reset/create/rm/prune/up/down. | Current operator-PC read-only status reports Docker, WSL, CLI, API, DB, Studio, and Edge ready with no missing required container. Overall remains `attention` only because Grafana is unreachable and Vector is unhealthy. | App-controlled start/stop evidence is required only when separately approved and needed for the cutover; non-core attention needs explicit disposition. | Medium: core runtime is ready, but lifecycle recovery and non-core attention must not be confused. | Accept or resolve the Grafana/Vector caveat, name an owner, and keep reset/cleanup prohibited. | `backend/app/services/runtime_control.py`; `backend/app/services/command_runner.py`; `README.md`; `docs/167_v2_observability_hardening_evidence.md` |
| Grafana status/link | Implemented Core Ops, link only | Dashboard exposes Grafana chip/status and an external `Open Grafana` link; no iframe behavior is implemented. | Scope includes Grafana status/link only and excludes iframe embedding. | Resolve the observed Grafana/Vector attention or record explicit residual-risk acceptance, an owner, and a non-destructive stop/rollback procedure. | Low-medium: Grafana attention is non-core unless it affects upload evidence. | Keep as status/link only; do not embed. | `backend/app/api/dashboard.py`; `docs/00_product_scope.md`; `README.md` |
| Settings save | Implemented Core Ops | `GET /api/config` and `PUT /api/config` exist; save validates payload, blocks env-overridden keys, writes config atomically, clears settings cache, and records `settings.save` audit rows. | Roadmap marks config API and Settings save UI done. | Operator validation only; no new feature implementation needed. | Medium: wrong settings can bind wrong source/target if operator process is not controlled. | Include read-only `GET /api/config` snapshot before Preview evidence. | `backend/app/api/config.py`; `backend/app/services/config_service.py`; `docs/01_development_roadmap.md` |
| Already-in-DB exact-key delete | Implemented backend/API/UI path, not operational/V2 proof | Backend/UI enforce selected `already_in_db` scope, but current code lacks the future target-global coordinator, fenced preflight owner/deadline/result CAS, canonical-root exact-byte source-provenance snapshot, atomic complete-row DB before-image and protected restore/disposition approvals, target mutation marker/marker-first reconcile, and privacy-safe opaque binding boundary. Current CSV/key evidence cannot recreate stored DB values that differ. | v1 scope includes this only when separately approved and guarded, but current code cannot satisfy the full `docs/164`/`docs/171` contract. | Implement/test every coordinator, preflight, source-provenance snapshot, atomic DB-before-image/restore/disposition, single-use Delete run, marker, exact-target, and privacy requirement in `docs/164`/`docs/171`. | Production-critical: wrong/duplicate/concurrent mutation, false outcome inference, loss of exact pre-delete values, arbitrary-source capture, or disclosure/recovery of exact keys/rows. | Keep operational Delete blocked; the current v1 path cannot count as operational or V2 proof. | `backend/app/services/upload_delete.py`; `frontend/src/pages/UploadPage.tsx`; `docs/164_operator_data_mutation_safety_gate.md`; `docs/171_v2_operational_delete_verification_gate.md` |
| Operator-facing date-scoped delete UI | Review shell only, not executable UI | Backend feature gate reports `implemented=False` with `review_shell_implemented=True`; frontend renders a blocked disabled panel only when `reviewShellVisible`; frontend API wrapper does not send timestamp scope. | `docs/168` states the shell is non-mutating and no date-scoped API/preflight/job start is implemented. `docs/165` classifies executable UI as deferred. | Role model, policy/preflight/start, fixture evidence, production approval, rollback, and explicit gate enablement. | High if misunderstood as executable cleanup capability. | Do not expose as normal operator action; keep deferred. | `backend/app/services/config_service.py`; `frontend/src/api/uploadDelete.ts`; `frontend/src/pages/UploadPage.tsx`; `docs/168_v2_date_scoped_delete_ui_gate.md`; `docs/165_v2_status_matrix.md` |
| Delete expansion | Deferred V2 feature | Feature gate is `implemented=False`; no broader delete policy is executable. Current code remains selected `already_in_db` exact-key only. | `docs/170` says the only baseline delete path is selected `already_in_db` exact-key and any expansion needs explicit policy and fixture proof. | Policy limits, fixture DB evidence, production approval format, reconcile/audit/rollback proof. | Production-critical if broadened without proof. | Keep out of v1 cutover; prepare future fixture-first design only. | `backend/app/services/config_service.py`; `docs/170_v2_delete_expansion_fixture_gate.md`; `docs/165_v2_status_matrix.md` |
| Operational DB delete verification | Deferred pending full hardened contract | Code path exists, but no operational DB mutation was run and current code lacks the target-global coordinator, fenced preflight owner/deadline/result lifecycle, source-provenance snapshot, atomic exact DB-before-image/restore/disposition lifecycle, single-use Delete approval/run, and target marker. | `docs/171` does not approve execution; `docs/164` makes every hardened lifecycle mandatory. | Implement/test the complete `docs/164`/`docs/171` coordinator/preflight/source-provenance/DB-before-image/restore/disposition/Delete-marker contract, then obtain separate current evidence and approval. | Production-critical. | Keep blocked; current v1 behavior cannot count as operational/V2 proof or be bundled with cutover. | `docs/171_v2_operational_delete_verification_gate.md`; `docs/164_operator_data_mutation_safety_gate.md` |
| Operational upload verification | Partial: historical Preview-only behavior passed; new Preview blocked | Preview/Start/Retry code exists with approval-count gates. One separately approved operator-PC Preview-only run succeeded with DB reachable and `target=0`; Start Upload remained disabled, so Start Upload and Retry Failed were not applicable and were not executed. Current workers do not prove they retain Preview-verified bytes, bind the DB to a pre-existing trusted expected identity, or safely resolve the remote-commit/local-release window. | `docs/173` remains the evidence chain and `docs/164` remains the approval-wording source; both block a new Preview until protected manifest/snapshot binding, separately verified target trust anchor plus target-identity preparation, and the Start/Retry target-outcome protocol exist. `docs/182` supplies baseline evidence only. | Production atomic manifest/snapshot binding, a pre-provisioned verified owner-only target baseline, separately approved target-identity exact-match preparation/review, target-fenced durable mutation outcomes, commit-unknown recovery, whole-attempt Retry reconciliation, deterministic replacement/concurrency/tamper/replay/source-reopen/wrong-initial-target/lease-disposition/commit-window tests, new package evidence, successor inventory, deadline-bound protected preparation, later approved Preview, partial-overlap disposition, and final sign-off remain. | Production-critical until the protected source/target/outcome lifecycles exist: actions can bind different bytes or a wrong same-port DB, reuse records, race disposition, falsely certify rollback, or omit rolled-back rows. | Implement/test the protected lifecycle first; then ensure the separately controlled verified target baseline exists, rebuild/verify, refresh inventory, separately prepare manifest/snapshot, separately approve/read-only-prepare and review the target identity, and only afterward seek Preview approval. This chain does not authorize baseline provisioning/rotation. Preserve the earlier result only as historical `no target-only upload` evidence. | `backend/app/services/upload_preview.py`; `backend/app/api/upload_jobs.py`; `docs/173_v2_operational_upload_verification_gate.md`; `docs/165_v2_status_matrix.md`; `docs/176_v1_cutover_go_no_go_validation_plan.md` |
| Multi-user LAN | Deferred V2 feature, default-off guard implemented | `v2_lan_access_enabled` exists, LAN health state reports blocked reasons, and HTTP middleware rejects non-loopback server/client access. If LAN flag is enabled, missing auth/session/concurrency reasons are reported. | `docs/172` says the slice does not implement Multi-user LAN and does not approve non-loopback bind/CORS/auth/session rollout. | Auth/authz, sessions, actor audit, concurrency model, CORS/bind approval, tests, explicit rescope. | High if accidentally exposed; current guard reduces risk. | Keep localhost-only for v1; future LAN work must start from `docs/172`. | `backend/app/core/settings.py`; `backend/app/core/lan_security.py`; `backend/app/main.py`; `docs/172_v2_lan_security_gate.md`; `docs/00_product_scope.md` |
| Supabase schema attribution | Deferred V2 feature; local sidecar foundation exists | Local SQLite `row_attribution_ledger` schema exists with append-only triggers and default-off writes. No Supabase migration/backfill is approved or implemented. | `docs/169` approves only local sidecar phase and defines future `public.metric_row_attribution_evidence` as deferred shape. | Written approval before Supabase migration/backfill/fixture mutation/operational DB access. | Medium: current audit depth is local sidecar, not Supabase-native row attribution. | Keep sidecar only for v1; use future migration design gate if needed. | `backend/app/db/row_attribution_repository.py`; `docs/169_v2_supabase_schema_attribution_design.md` |
| Legacy upload state import | Intentional v1 exclusion | No default legacy GUI `uploader_state.db` import path was found or required; new state store is the intended path. | Product scope and README say the legacy GUI state is not imported by default and the new app starts with a new state store. | None for v1; only re-scope if business explicitly requires import. | Low if operators understand Preview reconciliation replaces state import. | Keep excluded; rely on Supabase-backed Preview/reconciliation. | `docs/00_product_scope.md`; `README.md`; `AGENTS.md` |
| Local Supabase bootstrap/create/reset/cleanup | Intentional v1 exclusion and safety restriction | Command runner forbids `supabase init`, reset, Docker create/rm/prune/up/down. Runtime start blocks missing containers instead of creating a stack. | README says runtime control does not run bootstrap/reset/cleanup/create/delete/volume/prune and v1 does not create a new stack. | Maintainer-only setup outside the app if the stack is missing. | High if bypassed; destructive cleanup can destroy evidence or data. | Preserve non-destructive runtime control; document manual recovery separately. | `backend/app/services/command_runner.py`; `backend/app/services/runtime_control.py`; `README.md` |
| Legacy CSV fixture and soak validation | Completed for V2 WP-01 Preview-only/observation scope | Current main covers representative UTF-8/CP949 PLC, temperature, and integrated fixtures, exact reconciliation and DB-status semantics, a deterministic 25,000-row synthetic soak, and one approved large real `folder_all` Preview. | Roadmap and `docs/11` record the automated foundation; WP-02 consolidates the operator evidence and leaves final cutover sign-off separate. | Preserve coverage and repeat operational Preview only when accepted package/source scope changes. | Low-medium: unrepresented future CSV shapes can still regress. | Add fixtures when a new legacy shape is discovered; do not use operational mutation as a fixture substitute. | `tests/backend/fixtures`; `tests/backend/test_upload_preview_large_synthetic_soak.py`; `tests/backend/test_upload_preview_reconciliation.py`; `docs/11_upload_preview_large_csv_soak.md`; `docs/01_development_roadmap.md` |
| README/API live-smoke omission and schema consistency | Documentation safety correction complete | Backend requires `expectedTargetRows` for Upload Job start and validates optional `expectedTargetFiles`; README intentionally omits live Preview/Upload Job POST examples because the current runtime does not enforce the protected lifecycle required for operational use. | API source rejects missing/non-positive expected target rows; automated API tests cover the missing and positive-count mismatch paths, while README states that only synthetic tests may exercise the current path. | None for this docs-only correction; future contract checks must use backend source/schema/API tests without reintroducing an ad hoc live POST recipe. A zero-boundary regression test remains a separate coverage improvement. | Medium: stale live commands can bypass the documented execution gate, while stale schema descriptions can hide request-contract regressions. | Keep live POST examples absent until the protected runtime lifecycle is implemented/tested; verify request fields through source/schema/API tests. | `backend/app/api/upload_jobs.py`; `backend/app/schemas/upload_jobs.py`; `tests/backend/test_upload_jobs_api_contract.py`; `docs/03-analysis/start-upload-expected-count-contract.analysis.md`; `README.md` |
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
  from target-only upload. That historical `docs/173` chain remains incomplete
  because it predates `docs/182`; the later inventory is baseline evidence
  only. A future Preview remains blocked until protected atomic manifest/snapshot
  binding retained through Preview/Start/Retry and deterministic replacement/
  concurrency/tamper/replay/source-reopen/wrong-initial-target tests pass and a
  new package is verified. A pre-provisioned separately verified trusted target
  baseline must already exist. Only then may successor inventory, separately
  approved protected manifest/snapshot preparation, separately approved read-
  only target-identity preparation plus human review of its exact-match opaque
  result, and a later Preview approval proceed. This chain does not authorize
  baseline provisioning or rotation.
  Start Upload and Retry Failed are not applicable to the current evidence
  window.
- Representative legacy CSV fixtures, synthetic large Preview, real
  `folder_all` Preview, runtime readiness, Job Logs visibility, Audit Logs
  success/failure/blocked visibility, and Core Ops route rendering are complete.
- Current cutover execution is `NO-GO`. A `CONDITIONAL GO` candidate requires
  production atomic snapshot binding retained through Preview/Start/Retry and
  deterministic replacement/concurrency/tamper/replay/source-reopen tests, a
  rebuilt and verified executing package, an
  already provisioned/verified trusted target baseline,
  execution-adjacent successor inventory record with human-supplied safe
  operator-PC and privacy-safe exact-source bindings, separately approved
  protected manifest/snapshot preparation, separately approved target-identity
  preparation and human exact-match review, a later separately approved current Preview,
  any required human disposition of partial-overlap rows, final
  release-owner/operator sign-off,
  and resolution or explicit acceptance of the non-core Grafana/Vector
  attention state with an owner and stop procedure.
- App-controlled Local Supabase start/stop evidence remains separate and is
  required only when the accepted cutover procedure actually needs lifecycle
  control.

### Documentation blockers

- README intentionally omits live Upload Preview and Upload Job POST examples
  because the current runtime lacks the protected lifecycle required for
  operational use. Backend source rejects missing/non-positive
  `expectedTargetRows`; automated API tests cover missing and positive-count
  mismatch paths. A dedicated zero-boundary regression test is not claimed.
- No other direct doc/code contradiction was found in the mandatory files.

### Operator approval blockers

- Any operational Start Upload still needs same-snapshot runtime enforcement, an
  unrenewable target-fenced lease/durable outcome marker, commit-unknown
  recovery, serializable whole-keyset absence/no-overwrite enforcement, and exact
  approval after fresh Preview evidence.
- Retry Failed needs the same lease/outcome enforcement, authoritative rollback
  evidence, an owner-token/deadline-fenced per-source-action single-use creation
  entitlement for one protected encrypted/disposed whole-attempt DB-reconciliation
  record, a separate approval
  with a pre-reserved mutation id, transaction-time absence/no-overwrite
  enforcement, and the exact still-absent row count only if a retryable failure
  remains.
- Any operational DB delete remains blocked until a protected expiring preflight
  approval has durable owner/fence/deadlines and is atomically bound to one
  preflight/result, the singleton exact-target coordinator serializes all Preview/
  action chains, an owner-only canonical-root exact-byte source-provenance
  snapshot has bounded capacity/confidentiality/retention, a complete typed DB
  before-image can commit atomically with DELETE and the marker under exact
  schema/column/ceiling bindings, exact restore and both records have separately
  approved disposition, a separate protected expiring Delete approval is atomically
  claimed with that result and one run, and a pre-reserved target marker proves
  the atomic Delete outcome by marker-first reconciliation. Exact-target and
  opaque-public/private-exact privacy gates also remain mandatory;
  `docs/171` evidence is necessary but not sufficient.

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
| Destructive DB delete or its prerequisite preflight is run with replayable approval text or CSV-only rollback evidence. | Production-critical | Low if gates are followed | Keep operational delete blocked until a protected expiring single-use preflight approval is atomically bound to exactly one preflight, its ready result is single-consumer, a separate protected expiring single-use delete approval is atomically claimed with that result and exactly one delete run, and the target transaction preserves a complete typed DB before-image atomically with DELETE/marker; use `docs/171` as evidence input only. | Backend lifecycle implementation plus separate operator preflight/destructive/restore/disposition approvals. | Deterministic replay/concurrency tests, preflight and delete bindings, exact key/row/column counts, source-vs-DB value-difference cases, before-image/marker atomicity, opaque protected ids with owner-only row values, exact restore, and post-run disposition evidence. |
| LAN exposure is mistaken as available because a guard exists. | High | Low | Keep localhost-only and classify LAN as deferred. | Future LAN security gate. | Auth/session/concurrency/CORS/bind tests and explicit rescope. |
| Supabase-native attribution is assumed complete. | Medium | Medium | Document local sidecar-only state and defer migration/backfill. | Future schema attribution gate. | Migration design, rollback, fixture mutation proof, operational approval. |
| Live smoke docs or schema descriptions drift from backend approval contracts. | Medium | Low after this update | Keep live Preview/Upload Job POST examples omitted until the protected lifecycle exists, and keep schema/API tests aligned with required approval fields. | Maintainer docs review. | `git diff --check` plus schema and automated API contract review. |

## Recommended Next Work Packages

### WP1: documentation consistency fixes

- Status: complete. README's intentional no-live-smoke rule, backend approval-
  count contract references, roadmap, V2 matrix, gap audit, and cutover
  recommendation are aligned.

### WP2: non-destructive validation coverage

- Status: complete for V2 WP-01 Preview-only/observation scope. Representative legacy fixtures,
  deterministic synthetic soak, approved real `folder_all` Preview, and
  failure/blocked Audit coverage are present.

### WP3: atomic Preview binding, then operator-PC E2E evidence

- Status: blocked for any new Preview. The next work is a protected production
  content-manifest and immutable-snapshot lifecycle retained through Preview/
  Start/Retry plus deterministic replacement/concurrency/tamper/replay/source-
  reopen tests, followed by package rebuild and verification. Only then may the
  separately controlled verified target baseline be confirmed, inventory be
  refreshed, protected manifest/snapshot preparation separately approved,
  read-only target-identity preparation separately approved and its exact-match
  result human-reviewed, and a later operator-PC Preview approval requested.
  This work package does not authorize baseline provisioning/rotation.
  Existing config/runtime/Preview/log/UI evidence remains historical and partial;
  final human sign-off and non-core caveat ownership also remain.
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
  if cutover acceptance requires destructive delete evidence. First implement/
  test a protected expiring single-use preflight approval atomically bound to one
  preflight, a protected single-consumer ready result, and a separate protected
  expiring single-use delete approval atomically claimed with that result and one
  delete run; also implement the source-provenance snapshot plus complete typed DB
  before-image/marker atomic transaction, exact restore, and dual-record
  disposition contract. Only then use `docs/171` as evidence input under a
  separate plan.

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

- `README.md`: removed live Preview/Upload Job POST examples and documented the
  synthetic-test-only boundary until the protected runtime lifecycle exists.
- `docs/175_legacy_gui_replacement_gap_audit.md`: added this evidence-backed
  readiness/gap audit.
