# Operator Dashboard State Context Visibility

Date: 2026-06-14 Asia/Seoul

Branch: `codex/operator-dashboard-state-context-visibility`

Scope: Dashboard API/UI state context visibility implementation

Verdict: `implemented_pending_review`

Match Rate: `100%`

## Summary

Dashboard API mode now reports the active state DB context as sanitized
metadata. The Dashboard latest/current job area, Runtime panel, and Settings
page can show the same state context label without exposing the raw state DB
path.

This is a visibility change only. Upload Preview, Start Upload, Retry Failed,
duplicate rerun, authenticated Edge upload call, full rollout, DB reset, DB
destructive operation, Supabase lifecycle operation, and Docker lifecycle or
destructive operation were not performed.

## Non-Developer Explanation

The Dashboard was already showing real backend state, but it did not clearly
say which saved state it was reading.

That can confuse operators. One backend process can read an operator/package
state DB, while another can read a development or QA temporary state DB. Both
can contain real jobs, but the latest count can differ.

The improvement is a label. The app now exposes a safe state context class such
as operator/package, development, QA temporary, configured, unknown, or
inaccessible. Operators can tell which saved history the Dashboard is using
before treating the latest job count as evidence.

What remains: this label does not change or repair runtime state. If the wrong
context is active, the next step is backend/runtime configuration review, not
DB reset or upload retry.

## Implementation

Backend changes:

- Added a state context classifier for the active `state_db_path`.
- The classifier returns only class, label, storage status, and source.
- Raw state DB paths are not included in the state context API payload.
- `/api/dashboard` includes top-level state context metadata.
- Current job and recent job rows include the same state context metadata.
- `/api/config` includes the same sanitized state context.
- `/api/runtime/local-supabase` includes the same sanitized state context.

Frontend changes:

- API-mode Dashboard parses camelCase and snake_case state context payloads.
- Dashboard current job display shows the state context label next to the
  latest job evidence.
- Dashboard empty/missing state keeps the context label in the state store
  summary.
- Runtime panel shows the state context class and storage status.
- Settings header shows the state context label.
- Mock/default Dashboard mode and `?state=` demo states remain supported.

## Safety And Redaction

The implementation intentionally uses class-based labels only:

- no raw state DB path;
- no operational source path;
- no operational source filename;
- no operational source row content;
- no raw DB URL;
- no token value;
- no Authorization header value;
- no JWT value;
- no secret value.

## Tests

Backend contract tests cover:

- operator/package context class;
- development context class;
- unknown and inaccessible context classes;
- empty state with context label;
- latest succeeded job with context label;
- state context redaction from Dashboard and Config responses.

Frontend validation covers:

- Dashboard API response conversion;
- Dashboard mock/default type compatibility;
- Runtime state context row type compatibility;
- Settings state context type compatibility.

## Browser Smoke

Browser smoke target:

- Dashboard;
- Upload;
- Logs/Audit;
- Settings.

The smoke is read-only. It must not run Upload Preview, Start Upload, Retry
Failed, duplicate rerun, authenticated Edge upload calls, full rollout,
Settings save, DB reset/destructive operations, Supabase lifecycle operations,
or Docker lifecycle/destructive operations.

## Validation

| Check | Result |
| --- | --- |
| Targeted backend dashboard/config tests | passed with temporary import shim |
| `npm run typecheck` | passed |
| `npm run build:api` | passed |
| `npm run build` | passed |
| `npm run qa:screenshots` | passed |
| API-mode browser smoke | passed |
| `git diff --check` | pending |
| Marker scan | pending |
| PR file scope | pending |

Validation note: the first direct pytest invocation hit a local Windows
import-path collision with an installed external `tests` package. The same
targeted test set passed after using a temporary import shim that prepended this
repository's `tests/` directory. No project source file was changed for that
shim.

## Acceptance Criteria Trace

| Criteria | Result |
| --- | --- |
| Dashboard shows sanitized active state DB context class | passed |
| Latest/current job display includes same context class | passed |
| Settings or Runtime view exposes same context class | passed |
| Empty/missing state remains neutral | passed |
| Mock/default and `?state=` demo states preserved | passed |
| Raw paths/secrets not exposed by new payload | passed |
| Upload execution behavior unchanged | passed |
| Backend contract tests added | passed |
| Browser smoke planned/read-only | passed |
| Context mismatch guidance documented | passed |

API-mode browser smoke note: the already-running backend on port `8000` was an
older process that did not yet return the new `stateContext` runtime payload.
The frontend now keeps a safe `Unknown state` fallback for that transition case,
and Dashboard, Upload, Logs/Audit, and Settings loaded with zero browser console
errors and zero failed browser requests.

## Next Action

Open a small implementation PR for review. After merge, use the Dashboard state
context label during operator evidence review before deciding whether a latest
job count belongs to the expected runtime context.
