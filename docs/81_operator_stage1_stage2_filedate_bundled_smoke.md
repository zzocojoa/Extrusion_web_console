# Operator Stage 1/2 File-Date Bundled Smoke QA

## Summary

- Date: 2026-06-12
- Branch: `codex/operator-stage1-stage2-filedate-bundled-smoke`
- QA mode: report-only
- Package path class: repo-external temp operator package
- Runtime target: independent `Extrusion_web_console`
- Source label: `bounded operational sample with preserved timestamp metadata`
- Verdict: `passed_with_caveats`
- Stage 1 Preview executions: `1`
- Stage 2 Start Upload executions: `1`
- Full operational dataset rollout: not performed

This QA reran Stage 1 using a bounded sample whose timestamp metadata was
preserved, then executed Stage 2 exactly once because the Stage 1 gates passed.

Stage 1 reached DB reconciliation with `dbStatus=reachable`, one upload target
file, and no excluded, risky, or partial-overlap files. Stage 2 then ran one
Start Upload against that approved Preview target. The upload job succeeded with
`20219` accepted rows and an independent DB row-count delta of `+20219`.

Exact-key presence was confirmed after upload using the application's transform
reader, because the operational sample does not expose the final `device_id`
column directly in raw CSV form. The transformed exact-key presence result was
`20219/20219`.

Raw source paths, source filenames, row content, DB URLs, tokens,
Authorization headers, JWTs, generated credentials, and secret values are not
recorded in this report.

## Explicitly Not Performed

- feature code, launcher, backend, frontend, or packaging script edits;
- Supabase init, bootstrap, reset, start, or stop;
- DB migration, reset, delete, cleanup, prune, drop, or truncate;
- Docker volume, container, image, or network deletion;
- duplicate rerun or forced duplicate upload;
- full operational dataset rollout;
- operational original mutation or deletion;
- production deploy;
- GitHub Release or tag creation;
- feature branch deletion.

## QA Environment

| Area | Result |
| --- | --- |
| Package assembly mode | `api` |
| Package `supabase/config.toml` | present |
| Package Edge Function asset | present |
| Package migration asset | present |
| Package forbidden asset scan | `0` matches |
| Package launcher `-CheckOnly` | exit code `0` |
| Launcher raw-value marker scan | clean |
| Package zip/checksum | not created |
| Legacy fallback | not used |

The package was assembled only for this QA smoke. Package output was not
committed.

## Source Scope

| Check | Result |
| --- | --- |
| Sanitized source label | `bounded operational sample with preserved timestamp metadata` |
| Source class | user-provided bounded temp sample copy |
| Source file count | `1` |
| Sample row count | `20219` |
| File-date metadata | preserved |
| Full operational dataset used | no |
| Operational original modified | no |

No raw source path, filename, file content, or row content is recorded.

## Runtime Preflight

| Check | Result |
| --- | --- |
| Independent API | reachable |
| Independent DB | reachable |
| Independent Studio | reachable |
| Edge no-auth `GET` | `401` auth-class |
| Edge no-auth `POST {}` | `401` auth-class |
| Package-local `/api/health` | `ok` |
| Package-local `/api/runtime/local-supabase` | reachable |
| Package-local runtime Edge | ready |
| DB target class | independent |
| Edge target class | independent |
| DB/Edge target alignment | aligned |

No Authorization header was used for no-auth Edge probes. The only
authenticated Edge upload path was the single Stage 2 upload job after Stage 1
passed.

## Stage 1 Preview Result

| Metric | Result |
| --- | --- |
| Preview executions | `1` |
| Preview create status | `202` |
| Preview final status | `succeeded` |
| `dbStatus` | `reachable` |
| Preview total count | `1` |
| Already-in-db count | `0` |
| Upload-target count | `1` |
| Excluded count | `0` |
| Risky count | `0` |
| Partial-overlap count | `0` |
| Upload-row estimate | `20219` |
| DB matched rows | `0` |
| DB row-count delta from Preview | `0` |

Stage 1 passed the gate for a single bounded Start Upload. Preview did not
mutate the DB. The Preview target count is a file count; the upload-row estimate
is the row scope for Stage 2.

## Stage 2 Start Upload Result

| Metric | Result |
| --- | --- |
| Start Upload executions | `1` |
| Upload job create status | `202` |
| Upload job final status | `succeeded` |
| Total files | `1` |
| Succeeded files | `1` |
| Failed files | `0` |
| Total rows | `20219` |
| Processed rows | `20219` |
| Uploaded rows | `20219` |
| Accepted rows | `20219` |
| Warning count | `0` |
| DB row-count delta from upload | `+20219` |

This was not a duplicate rerun. The upload job executed one authenticated Edge
upload path for the approved bounded sample only.

## Exact-Key Presence

| Check | Result |
| --- | --- |
| Exact-key calculation source | application transform reader |
| Transformed exact-key count | `20219` |
| DB exact-key presence after upload | `20219` |
| Exact-key presence class | complete |

The raw CSV does not directly expose the final `device_id` field used by
`all_metrics(timestamp, device_id)`. Exact-key evidence was therefore computed
from the same application transform path used by Upload Job execution, then
checked read-only against the independent DB.

## Audit And Redaction

| Check | Result |
| --- | --- |
| Audit API read-only check | reachable |
| Audit marker scan | clean |
| Launcher output marker scan | clean |
| Package forbidden artifact scan | clean |
| Raw DB URL in report | absent |
| Token/auth/JWT values in report | absent |
| Raw Authorization header in report | absent |
| Raw source path/content/filename in report | absent |
| Raw row content in report | absent |

Raw `/api/config` and Preview detail payloads were not copied into this report
because those API shapes can contain local path fields by design. The report
uses only presence, target class, status, and count evidence.

## Browser/UI Smoke

| Check | Result |
| --- | --- |
| Live `/upload` UI smoke | not run |
| Reason | Avoided copying or screenshotting raw source detail fields during an operational sample QA. |
| Mock screenshot QA | passed |

The API path was validated through package-local backend smoke. Mock screenshot
QA was used for UI regression coverage without operational source exposure.

## Caveats

| Caveat | Current state | Impact |
| --- | --- | --- |
| Vector | restarting marker observed | Observability/runtime caveat; core Preview/Upload path passed. |
| Grafana | unreachable | Not a core upload gate unless the operator requires Grafana readiness. |
| Supabase start instability history | not re-triggered | No start/stop was run in this QA. |
| Live UI source-detail exposure | not exercised | Keep operational UI screenshots out of reports unless redaction is verified. |

## Stage Judgment

| Question | Answer |
| --- | --- |
| Did Stage 1 use preserved timestamp metadata? | yes |
| Did Stage 1 reach `dbStatus=reachable`? | yes |
| Was the sample bounded? | yes |
| Was Start Upload executed exactly once? | yes |
| Was exact-key presence confirmed? | yes, transformed exact-key presence complete |
| Was full operational rollout avoided? | yes |
| Was duplicate rerun avoided? | yes |
| Did DB/Edge stay independent and aligned? | yes |
| Did audit/log redaction stay clean? | yes |
| Is the next staged rollout step allowed? | yes, with caveats |

## Validation

| Command or check | Result |
| --- | --- |
| Targeted package/runtime/upload preview/upload job backend tests | `140 passed` |
| `npm run typecheck` | passed |
| `npm run build:api` | passed |
| API-mode package assembly smoke | passed |
| Package launcher `-CheckOnly` | passed |
| Runtime preflight | API/DB/Studio reachable; Edge no-auth `401` auth-class |
| Stage 1 Preview-only execution count | exactly `1` |
| Stage 2 Start Upload execution count | exactly `1` |
| Read-only transformed exact-key presence | `20219/20219` complete |
| `npm run build` | passed |
| `npm run qa:screenshots` | passed |

## Next Action

Proceed to a Stage 2 acceptance review or a Stage 3 day-bounded/batch-bounded
rollout plan. Do not run a full operational dataset upload until Stage 3 gates
are explicitly approved and reported in a separate PR.
