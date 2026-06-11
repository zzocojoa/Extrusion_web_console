# Operator Duplicate-Safety Evidence QA

## Summary

- Date: 2026-06-11
- Branch: `codex/operator-duplicate-safety-evidence-qa`
- Base commit: `85c67cfa01d282e7b83006ad07633f8996d42bf2`
- QA mode: report-only
- Package path class: assembled operator package
- Evidence verdict: `accepted_with_caveats`

This QA applies the policy from `docs/71_operator_duplicate_safety_evidence_policy.md`.
It verifies duplicate-safety through the normal operator flow evidence chain: a
fresh DB-checkable Preview excludes known bounded duplicate exact keys before
Start Upload.

The accepted evidence is:

- DB and Edge target classes were independent and aligned.
- Independent API, DB, and Studio ports were reachable.
- Direct no-auth Edge `GET` and `POST {}` returned `401` auth-class.
- The independent DB baseline was `5` total rows, `5` distinct exact keys, and
  `0` duplicate exact-key groups.
- The evidence Preview completed with `dbStatus=reachable`.
- The bounded exact-key sample produced `1` Preview item with `5` DB matches.
- The Preview item was classified as `already_in_db`.
- Upload target count was `0`.
- Upload row estimate was `0`.
- No Upload Job was created.
- DB counts remained unchanged after QA.

This QA did not run Upload Start, forced duplicate upload, duplicate rerun, or
Edge authenticated upload.

## Scope And Guardrails

This QA did not modify feature code, launcher code, backend code, frontend code,
or packaging scripts.

This QA did not run:

- Supabase init/bootstrap/reset/start
- DB migration/reset/delete/cleanup/prune/drop/truncate
- Docker volume/container/image/network deletion
- Upload Start
- forced duplicate upload
- duplicate rerun
- Edge authenticated upload call
- Authorization header or Edge upload token use
- operational full-source upload
- operational source modification/deletion
- production deploy
- GitHub Release or tag creation/modification
- feature branch deletion

One local launcher token was used internally only for the permitted package-local
Upload Preview request because operator-mode Preview is a protected write API.
The token value was not printed, logged in this report, committed, or used for
Edge upload authorization.

## QA Environment

| Item | Result |
| --- | --- |
| Operator package frontend mode | api |
| Package assembly smoke | passed |
| Package Supabase assets | present |
| Package denylist matches | `0` |
| Package redaction matches | `0` |
| Package launcher `-CheckOnly` | passed |
| Package backend health | `ok` |
| Package path label | `assembled_operator_package` |
| Bounded source class | `bounded_synthetic_exact_key_sample` |
| Bounded sample rows | `5` |
| Raw package output path recorded | no |
| Raw source path/content/filename recorded | no |

The bounded source was generated outside the repository from read-only
independent DB exact keys. Its raw path, filename, and row content are not
recorded.

## Runtime And Target Readiness

| Check | Result |
| --- | --- |
| DB target class | independent |
| Edge target class | independent |
| DB/Edge target alignment | aligned |
| Independent API port | reachable |
| Independent DB port | reachable |
| Independent Studio port | reachable |
| Package `/api/health` | `ok` |
| Package `/api/runtime/local-supabase` | reachable |
| Runtime overall | `attention` |
| Runtime reason | `non_core_runtime_attention` |
| Direct no-auth Edge `GET` | `401` auth-class |
| Direct no-auth Edge `POST {}` | `401` auth-class |

The runtime readiness caveat is non-core attention. Core target evidence for
this QA came from direct API/DB/Studio reachability, direct Edge auth-class
probes, package-local config, and the successful DB-backed Preview.

## Before DB Baseline

Read-only independent DB exact-key baseline before the evidence Preview:

| Metric | Result |
| --- | ---: |
| Total rows | `5` |
| Distinct `(timestamp, device_id)` keys | `5` |
| Duplicate exact-key groups | `0` |

This matches the duplicate-safety policy precondition: the prior bounded keys
already exist in the independent DB and there are no duplicate exact-key groups.

## Fresh Preview Evidence

The accepted evidence Preview was run once against the bounded synthetic
exact-key source.

| Field | Result |
| --- | --- |
| Preview status | `succeeded` |
| `dbStatus` | `reachable` |
| Preview item count | `1` |
| Preview item status | `already_in_db` |
| Sample row count | `5` |
| DB matched rows | `5` |
| Already-in-DB item count | `1` |
| Upload target count | `0` |
| Upload row estimate | `0` |
| Risky count | `0` |
| Excluded count | `0` |

This is the expected normal operator duplicate-safety behavior. The duplicate
exact keys are excluded at Preview time, so Start Upload has no duplicate target.

## After DB Baseline

Read-only independent DB exact-key baseline after QA:

| Metric | Result |
| --- | ---: |
| Total rows | `5` |
| Distinct `(timestamp, device_id)` keys | `5` |
| Duplicate exact-key groups | `0` |
| Row-count delta | `0` |

The DB row-count delta remained `0` because no upload was run. This is not
presented as forced duplicate-upload proof. It is supporting evidence that the
normal Preview exclusion QA did not mutate the DB.

## Upload Job Evidence

| Check | Result |
| --- | --- |
| Upload Start executed | no |
| Forced duplicate upload executed | no |
| Duplicate rerun executed | no |
| Upload Job created | no |
| Upload Job count in isolated package state | `0` |
| Edge authenticated upload call | no |

No Upload Job is expected when the Preview target count is `0`.

## Secondary Contract Evidence

Secondary evidence was source-inspection only. No DB migration or DB mutation was
run.

| Contract | Evidence |
| --- | --- |
| DB unique key | `supabase/migrations/20260608000001_create_all_metrics_upload_contract.sql` defines `all_metrics_timestamp_device_id_key` and `UNIQUE ("timestamp", device_id)`. |
| Edge upsert conflict target | `supabase/functions/upload-metrics/index.ts` uses `onConflict: "timestamp,device_id"`. |

This confirms the safety boundary beneath the normal operator Preview flow.

## Audit, Log, And Redaction

| Check | Result |
| --- | --- |
| Preview audit row | present |
| Audit marker scan | clean |
| Report raw DB URL/token/auth/JWT | absent |
| Report raw Authorization header | absent |
| Report raw source path/content/filename | absent |
| Report operational CSV path/content/filename | absent |
| Report raw package output path | absent |
| Preview API response raw path/filename | not copied into report |

The Preview API response naturally contains file metadata for the running
backend, so the report records only sanitized status/count evidence.

## Browser And UI Smoke

Browser UI smoke was not completed in this QA. Package-local API and static
backend health were verified, but a follow-up status-only static page probe hit a
local Windows process-launch issue during recheck. No product bug is concluded
from that tool issue.

The browser gap does not block duplicate-safety evidence because the acceptance
criteria in this policy are the package path, DB/Edge target alignment, DB-backed
Preview exclusion, no Upload Job, DB unchanged, and redaction-safe evidence.

## Blockers And Caveats

### Blockers

None for operator duplicate-safety evidence acceptance.

### Caveats

1. `preview_setup_validation_reject`: an initial automation attempt produced a
   malformed Preview request and was rejected before candidate scan. It did not
   create an Upload Job, call Edge auth, or mutate the DB. The accepted evidence
   Preview is the later DB-checkable run summarized above.
2. `runtime_non_core_attention`: package runtime overall status is `attention`
   because of non-core runtime attention. Core API/DB/Studio/Edge evidence for
   this QA remained usable.
3. `browser_http_smoke_not_completed`: browser/static page smoke was not
   completed because a local process-launch recheck failed. API and duplicate
   evidence checks completed.
4. `local_preview_token_hidden`: the permitted package-local Preview call used
   the operator local token guard internally. The raw value was never printed or
   documented, and no Edge Authorization header was used.

## Validation

| Command/check | Result |
| --- | --- |
| Package assembly smoke | passed |
| Package launcher `-CheckOnly` | passed |
| Package-local `/api/health` | passed |
| Package-local `/api/runtime/local-supabase` | reachable |
| Direct API/DB/Studio reachability | reachable |
| Direct no-auth Edge probes | `401` auth-class |
| Read-only DB baseline before | `5` total, `5` distinct, `0` duplicate groups |
| Fresh Preview evidence | `succeeded`, `dbStatus=reachable`, `already_in_db`, target `0` |
| Read-only DB baseline after | `5` total, `5` distinct, `0` duplicate groups |
| DB row-count delta | `0` |
| Upload Job count | `0` |
| Edge authenticated upload call | not run |
| Audit marker scan | clean |
| Secondary contract source inspection | unique key and Edge `onConflict` confirmed |
| Targeted package/runtime/upload preview/upload job tests | `143 passed` |
| `npm run typecheck` | passed |
| `npm run build:api` | passed |
| `npm run build` | passed |
| `npm run qa:screenshots` | passed, `1` Playwright test |
| `git diff --check` | passed |
| New report marker scan | clean |
| PR file-scope check | docs-only target confirmed before staging |

## Final Judgment

| Question | Answer |
| --- | --- |
| Was the operator package path used? | yes |
| Were DB/Edge target classes independent and aligned? | yes |
| Was `dbStatus=reachable`? | yes |
| Were bounded exact keys classified as `already_in_db`? | yes |
| Was upload target count `0`? | yes |
| Was an Upload Job created? | no |
| Did DB counts remain unchanged? | yes |
| Was forced duplicate upload run? | no |
| Was Upload Start run? | no |
| Was Edge authenticated upload called? | no |
| Verdict | `accepted_with_caveats` |

## Next Step

Review and merge this QA report if the caveats are acceptable. The next operator
acceptance step can proceed from the policy-approved duplicate-safety evidence
chain without requiring a forced duplicate upload through the normal operator
flow.
