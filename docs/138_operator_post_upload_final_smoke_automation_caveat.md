# Operator Post-Upload Final Smoke and Automation Caveat

Date: 2026-06-14 Asia/Seoul

Scope: docs-only final smoke report for the approved Stage 4 post-upload state
and the follow-up automation caveat. This report does not execute Upload
Preview, Start Upload, Retry Failed, duplicate rerun, manual Edge upload calls,
full rollout, DB reset, Supabase lifecycle work, Docker lifecycle work, or any
destructive operation.

## Verdict

Verdict: `passed_with_automation_caveat`

Match Rate: `95%`

The final operational state is accepted for the completed upload job
`upl_b14ee8090c10`. The only caveat is not a product upload failure: a prior
post-upload smoke automation likely clicked the Preview run button through an
ambiguous button-index selector and created two metadata-only Preview runs.

## Non-Developer Summary

The approved upload finished correctly.

The console now shows the latest upload as successful, and the database row
count remains at the expected post-upload total. The extra issue found during
smoke testing was about the test automation, not the upload itself. The
automation appears to have pressed the Preview button while trying to navigate
the Upload page.

For future checks, the automation must click clearly scoped UI targets, such as
the Upload page job tab, instead of "the sixth button on the page." Index-based
clicking is fragile because the Upload page has both a Preview tab and a
Preview action button.

## Final Operational Status

| Check | Result | Evidence |
| --- | --- | --- |
| Dashboard latest job | passed | Dashboard API reported `Latest upload succeeded` |
| Dashboard current job | passed | `upl_b14ee8090c10`, status `succeeded` |
| Upload job detail | passed | job status `succeeded` |
| Processed rows | passed | `24888` |
| Uploaded rows | passed | `24888` |
| Accepted rows | passed | `24888` |
| DB row count | passed | `98721` |
| Upload job events | passed | `18` events for `upl_b14ee8090c10` |
| `upload.start` audit | passed | success audit exists for `upl_b14ee8090c10` |
| `upload.succeeded` audit | passed | success audit exists for `upl_b14ee8090c10` |

The latest upload job in the active state store is:

| Field | Value |
| --- | --- |
| Job id | `upl_b14ee8090c10` |
| Preview run | `prv_09c9083fb4a8` |
| Status | `succeeded` |
| Total rows | `24888` |
| Processed rows | `24888` |
| Uploaded rows | `24888` |
| Accepted rows | `24888` |

## Read-Only Smoke Result

Dashboard and Upload showed the successful latest upload state. Logs/Audit showed
the successful `upload.start` and `upload.succeeded` records for the same job.

Browser smoke recorded:

| UI area | Result |
| --- | --- |
| Dashboard | showed `upl_b14ee8090c10`, `succeeded`, `24888` |
| Upload job tab | showed `upl_b14ee8090c10`, completed state, `24888` |
| Logs/Audit | showed upload success audit evidence |
| Browser console errors | `0` |
| Failed browser requests | `0` |

## Automation Caveat

The prior smoke found two extra Preview runs:

| Preview run | Status | DB status | Target | Excluded | Reason class |
| --- | --- | --- | --- | --- | --- |
| `prv_63cadcc59ab0` | `succeeded` | `not_checked` | `0` | `4` | `outside_date_range` |
| `prv_cd4e18f42436` | `succeeded` | `not_checked` | `0` | `4` | `outside_date_range` |

Those runs were metadata-only and did not mutate operational DB rows. They used
the default `today` Preview filter, which excluded all four operational source
files as outside the date range.

Follow-up investigation found no product bug where Upload page entry
automatically creates a Preview run:

| Investigation item | Result |
| --- | --- |
| Upload page route entry | only read-only GET calls observed |
| Upload job tab switch | only read-only GET calls observed |
| `POST /api/upload/preview` on route entry | not observed |
| Frontend Preview creation path | tied to explicit Preview action handler |
| Product auto-preview side effect | not found |

Root cause classification:

`qa_smoke_selector_ambiguity_clicked_preview_action`

The prior automation used broad button-index selection. On the Upload page, that
is unsafe because the navigation, Preview tab, Job tab, Preview action, and
Start Upload button are all buttons in one document. Future smoke automation
must use scoped selectors.

## Future Automation Rule

Use scoped selectors only:

| Intent | Required selector style |
| --- | --- |
| Open Upload page | `.sidebar__nav-item` scoped by nav item or accessible label |
| Switch to Upload job tab | `.upload-tabs button` scoped to the tab group |
| Inspect Logs audit tab | logs tab group selector scoped to the Logs page |
| Never use | global button index such as "button 6" |

Automation must not click:

- Preview run button;
- Start Upload button;
- Retry Failed button;
- duplicate rerun controls;
- Settings Save;
- runtime start/stop controls.

## Operational Controls Preserved

During this final report task, the following were not executed:

- Upload Preview;
- Start Upload;
- Retry Failed;
- duplicate rerun;
- authenticated Edge upload call;
- full rollout;
- DB reset/init/delete/truncate/drop/prune;
- Supabase start/stop/reset;
- Docker lifecycle or destructive operation;
- operational source mutation.

Protected untracked items remain uncommitted and unmodified.

## Redaction Result

This report records only sanitized IDs, statuses, row counts, route classes, and
audit/action classes.

Marker scan result: clean for raw operational source locators, source names,
row content, full local source paths, database connection strings, and
credential-bearing values.

## Next Action

Operational status is complete for `upl_b14ee8090c10`.

If another upload is needed, restart the controlled upload gate from a fresh
Preview-only run, target count review, and separate explicit Start Upload
approval. For UI smoke, use scoped selectors and avoid any Preview or upload
action controls unless the user explicitly approves that action.
