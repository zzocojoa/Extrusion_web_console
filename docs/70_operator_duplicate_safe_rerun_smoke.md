# Operator Package Duplicate-Safe Rerun Smoke

## Summary

- Date: 2026-06-11
- Branch: `codex/operator-duplicate-safe-rerun-smoke`
- Base commit: `34fdd09fc3ff9252b559392c302f734f397fc774`
- QA mode: report-only
- Package path class: assembled operator package, not repo dev backend
- Duplicate-safe verdict: `blocked`
- Upload Start calls: `1` protected API attempt, blocked before job creation
- Edge authenticated upload calls: `0`
- Duplicate rerun executions: `0`

This QA attempted to run one bounded operator package duplicate-safe rerun against the independent `Extrusion_web_console` Supabase stack. The run is blocked by the normal Preview to Start Upload contract: once the bounded exact keys already exist in the independent DB, a fresh Preview classifies the source as `already_in_db`, produces `0` target rows, and leaves no valid Start Upload target.

No feature code, launcher code, backend code, frontend code, or packaging script was modified.

## Scope And Guardrails

This QA did not run:

- Supabase init/bootstrap/reset/start
- DB migration/reset/delete/cleanup/prune/drop/truncate
- Docker volume/container/image/network deletion
- operational full-source upload
- operational source modification/deletion
- production deploy
- GitHub Release or tag creation/modification
- feature branch deletion

This QA did run:

- package assembly smoke
- package launcher `-CheckOnly`
- package-local backend/API smoke
- package-local Upload Preview against a bounded synthetic exact-key source
- one protected `POST /api/upload/jobs` Start Upload attempt
- read-only DB exact-key counts before and after
- read-only audit checks
- browser smoke for `/upload` and `/logs`

## QA Environment

| Item | Result |
| --- | --- |
| Operator package frontend mode | api |
| Package required paths | present |
| Package Supabase assets | present |
| Package denylist matches | 0 |
| Package redaction matches | 0 |
| Package launcher `-CheckOnly` | passed |
| Package backend path | assembled operator package |
| Package backend local token mode | required, token hidden |
| Bounded source class | synthetic exact-key rerun sample |
| Bounded sample rows | 5 |
| Raw package path recorded | no |
| Raw source path/content/filename recorded | no |

## Runtime Readiness

| Check | Result |
| --- | --- |
| Docker independent containers | active |
| Independent API port `55321` | reachable |
| Independent DB port `25433` | reachable |
| Independent Studio port `55323` | reachable |
| Direct no-auth Edge `GET` | `401` auth-class |
| Direct no-auth Edge `POST {}` | `401` auth-class |
| Package `/api/health` | ok |
| Package `/api/runtime/local-supabase` | reachable |
| Package runtime overall | `attention` |
| Package runtime reason | `non_core_runtime_attention` |
| Package API / DB / Studio | ready / ready / ready |
| Grafana | unreachable |

Grafana remains link/status-only and was not treated as a duplicate-safe upload blocker.

## Config And Target Class

| Setting | Result |
| --- | --- |
| `plcDataDir` | process override configured for bounded synthetic source |
| `supabaseDbUrl` | env source, hidden, independent class |
| `supabaseUrl` | env source, independent class |
| `supabaseAnonKey` | configured, hidden |
| `supabaseEdgeUrl` | env source, hidden, independent class |
| `localSupabaseApiPort` | independent |
| `localSupabaseDbPort` | independent |
| `localSupabaseStudioPort` | independent |
| DB/Edge target alignment | aligned |

No raw DB URL, Edge URL, token, Authorization header, JWT, anon key, or secret value was recorded.

## Before Baseline

Read-only independent DB baseline before the Start Upload attempt:

| Metric | Result |
| --- | ---: |
| Total rows | 5 |
| Distinct `(timestamp, device_id)` keys | 5 |
| Duplicate exact keys | 0 |

This matched the readiness expectation from `docs/69_operator_duplicate_safe_rerun_readiness.md`.

## Bounded Preview Result

After correcting the package process source override, the bounded synthetic exact-key source produced:

| Field | Result |
| --- | --- |
| Preview status | `succeeded` |
| `dbStatus` | `reachable` |
| Preview item count | 1 |
| Item status | `already_in_db` |
| Row count | 5 |
| Local key count | 5 |
| DB match count | 5 |
| Upload row estimate | 0 |
| Reason code | `db_full_match` |
| Scan mode | `full` |

This is correct duplicate-prevention behavior for a fresh Preview, but it blocks an operator Start Upload because the app intentionally starts uploads from `target` preview items only.

## Start Upload Attempt

| Field | Result |
| --- | --- |
| Protected Start Upload API attempts | 1 |
| Request token | present, hidden |
| HTTP status | `422` |
| Job created | no |
| Block reason | `preview_db_not_reachable` |
| Upload Job final status | not applicable |
| Accepted rows | 0 |
| Uploaded rows | 0 |
| Job events count | 0 |
| SSE replay | not applicable |
| Edge authenticated upload call | not run |

The one Start Upload attempt was made against an earlier package Preview that was not uploadable. After the source override was corrected, the intended bounded Preview was DB-checkable and fully `already_in_db`, which also produced no valid Start Upload target. A second Start Upload attempt was not made, to preserve the one-attempt guardrail.

## After DB Exact-Key Count

Read-only independent DB count after the blocked Start Upload attempt:

| Metric | Result |
| --- | ---: |
| Total rows | 5 |
| Distinct `(timestamp, device_id)` keys | 5 |
| Duplicate exact keys | 0 |
| Row-count delta | 0 |

The row-count delta stayed `0`, but this is not a successful duplicate-safe rerun proof because no Upload Job was created and no Edge authenticated upload occurred.

## Audit And Redaction

| Check | Result |
| --- | --- |
| `upload.start` audit rows observed | present |
| `upload.start` latest result | `blocked` |
| `upload.start` latest error class | `preview_db_not_reachable` |
| `upload.preview` audit rows observed | present |
| Audit DB URL marker | clean |
| Audit Authorization marker | clean |
| Audit JWT marker | clean |
| Audit timestamp-style CSV marker | clean |
| Audit operational filename-family marker | clean |
| Audit Windows path marker | clean |
| Report raw DB URL/token/auth/JWT | absent |
| Report raw source path/content/filename | absent |
| Report operational CSV path/content/filename | absent |

## Browser And UI Smoke

Package UI smoke used the package-served API-mode frontend. Start Upload was not clicked in the browser.

| Page | Result |
| --- | --- |
| `/upload` | loaded |
| `/logs` | loaded |
| Browser console errors | 0 |
| Browser marker scan | clean |

## Blockers And Caveats

### Blocker

1. `no_duplicate_rerun_start_target`: the package path has no valid `target` Preview item for the existing bounded exact keys. A fresh Preview correctly classifies all 5 rows as `already_in_db`, so `POST /api/upload/jobs` cannot create a job for a duplicate-safe rerun through the normal Start Upload path.

### Caveats

1. `start_attempt_used_non_uploadable_preview`: the single Start Upload attempt was blocked before job creation. It did not exercise Upload Job execution or Edge authenticated upload.
2. `edge_authenticated_call_not_exercised`: Edge no-auth auth boundary remained healthy, but the authenticated upload path was not called in this QA because no Upload Job was created.
3. `initial_source_override_issue`: the first package backend launch did not apply the intended bounded source process override, so an initial Preview returned non-uploadable results. The backend was restarted with the process override corrected before the bounded exact-key Preview evidence was collected.
4. `grafana_unreachable`: package runtime remains `attention` because Grafana is unreachable. This is not the DB/Edge upload path.
5. `vector_restarting`: the independent vector service was observed restarting. Core API/DB/Studio/Edge remained reachable.

## Validation

| Command/check | Result |
| --- | --- |
| Package assembly smoke | passed |
| Package launcher `-CheckOnly` | passed |
| Package-local `/api/health` | passed |
| Package-local `/api/config` | passed, raw secret values hidden |
| Package-local `/api/runtime/local-supabase` | reachable, API/DB/Studio ready |
| Direct no-auth Edge probes | `401` auth-class |
| Before DB exact-key count | 5 total, 5 distinct, 0 duplicate |
| Bounded Preview | `succeeded`, `dbStatus=reachable`, 5 DB matches |
| Start Upload attempt | blocked, no job created |
| After DB exact-key count | 5 total, 5 distinct, 0 duplicate |
| Browser `/upload`, `/logs` smoke | loaded, console errors 0, marker clean |
| Audit marker scan | clean |
| Targeted package/runtime/upload preview/upload job tests | `145 passed` |
| `npm run typecheck` | passed |
| `npm run build:api` | passed |
| `npm run build` | passed |
| `npm run qa:screenshots` | passed, `1` Playwright test |
| `git diff --check` | passed |
| New report marker scan | clean |
| PR file-scope check | docs-only |
| Forbidden artifact staged-file check | clean |

## Final Judgment

| Question | Answer |
| --- | --- |
| Was the operator package path used? | yes |
| Were DB/Edge target classes independent? | yes |
| Was before baseline `5/5/0` confirmed? | yes |
| Was a bounded source used? | yes |
| Was Upload Start attempted more than once? | no |
| Was an Upload Job created? | no |
| Was Edge authenticated upload called? | no |
| Was DB row-count delta `0`? | yes, because no upload occurred |
| Is duplicate-safe rerun proven through Upload Job? | no |
| Verdict | `blocked` |

## Next Step

Do not proceed to final operator acceptance on duplicate-safe rerun evidence from this PR.

Choose one follow-up path:

1. Define an approved test-only duplicate-rerun mechanism that can re-upload an already represented bounded source without bypassing audit and redaction controls.
2. Adjust the QA plan to treat fresh Preview `already_in_db` plus DB unique/upsert contract evidence as the duplicate-safety proof, without requiring Start Upload to rerun already excluded rows.

Operational full-source upload remains out of scope.
