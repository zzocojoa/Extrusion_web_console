# Changelog

All notable changes to Extrusion Web Console are documented here.

## [0.1.0.1] - 2026-06-19

### Added

- Project status summaries and infographics now have a language policy that separates completed evidence, operating restrictions, review gates, conditional caveats, and intentional v1 exclusions instead of grouping them as generic unfinished work.
- README and the operator upload gate runbook now point future status artifacts to the status language policy so destructive-action restrictions are not mistaken for pending tasks.

## [0.1.0.0] - 2026-06-02

### Added

- Operators can start an upload job from a completed Upload Preview run.
- Upload jobs now persist job state, file state, resumable offsets, job events, and audit records in SQLite.
- Upload Job includes progress, file-level status, pause/resume/cancel controls, Retry Failed, and live event streaming through SSE.
- Backend now exposes Upload Job create, list, detail, retry, pause, resume, cancel, and event stream APIs.
- The Upload page now has a real Job tab with Korean/English UI text and mock mode for local UI QA.
- Project documentation now records the upload job/SSE implementation plan and shipped behavior.
- Logs now has separate Job Logs and Audit Logs tabs with Audit table filters, pagination, loading/empty/error states, and Korean/English UI text.
- Backend now exposes `GET /api/audit` with pagination, filter echo, sort allowlist, sanitized `errorMessage` values, and decoded redacted params.
- SQLite audit storage now installs append-only triggers `audit_log_no_update` and `audit_log_no_delete`.
- Settings now has a save UI connected to `GET /api/config` and `PUT /api/config`, with editable fields, dirty state, Save/Reset controls, validation feedback, save status, and hidden secret replacement behavior.
- Settings saves now write `settings.save` audit rows for success, failure, malformed request validation, and env override blocked paths.
- Env/process and repo `.env` overridden Settings fields are disabled/read-only and backend-blocked from config JSON writes.
- Upload Preview now writes `upload.preview` audit rows for success, DB unreachable, missing source, malformed request validation, and active preview conflict paths.
- Upload Job API responses, file rows, job events, and SSE replay now expose canonical `acceptedRows` for Edge/Supabase upsert-accepted row counts.
- Frontend now includes Playwright screenshot QA through `npm run qa:screenshots`, covering Dashboard, Upload Preview, Upload Job, Job Logs, Audit Logs, and Settings in mock mode without Docker, local Supabase, secrets, or operational CSV fixtures.
- Launcher phase 1 now provides Windows operator launcher scripts, `-CheckOnly`, explicit `-BuildFrontend`, and FastAPI serving of the built frontend from `frontend/dist` on `127.0.0.1`.
- Launcher phase 2 now adds per-run local token protection for mutating localhost APIs through `X-EWC-Local-Token`, with runtime HTML bootstrap, launcher env passing, and explicit dev-disabled mode.
- API docs hardening now disables `/api/docs`, `/api/openapi.json`, and ReDoc-style docs routes in operator launcher mode while retaining Swagger/OpenAPI for dev/test docs-enabled runs.
- Windows shortcut packaging v1 now adds maintainer-run Desktop and Start menu shortcut installation for prepared operator folders, with idempotent shortcut updates, safe `ShortcutName` validation, and no AppData config/state/log deletion.
- Operator package assembly v1 now adds a manifest and maintainer-run PowerShell assembly script for prepared operator folders, with allowlist-only copying, repo-internal `OutputRoot` blocking, denylist/redaction validation, optional zip creation, SHA-256 checksum output, `.venv` cache exclusion, package build metadata, and package smoke guidance.
- Frontend release builds now include build-mode metadata, and maintainers can run `npm run build:api` to create an API-mode `frontend/dist` for operator packages.
- API docs hardening QA passed targeted route/token/OpenAPI backend tests (`33 passed`), full backend tests from clean cwd (`153 passed`), frontend typecheck/build, screenshot QA, launcher `-CheckOnly`, operator HTTP smoke, dev/docs-enabled HTTP smoke, and `git diff --check`.
- Launcher local token QA passed targeted backend token/static/launcher tests (`17 passed`), full backend tests from clean cwd (`151 passed`), frontend typecheck/build, screenshot QA, launcher `-CheckOnly`, token HTTP smoke, and unsafe marker scans with `0` matches.

### Changed

- Start Upload only snapshots `target` Preview items. `already_in_db`, `partial_overlap`, `risky`, and `excluded` rows remain excluded in v1.
- Preview-origin upload disables legacy latest-timestamp Smart Sync filtering and keeps database upsert on `(timestamp, device_id)` as final duplicate protection.
- Upload Job UI now labels Edge/Supabase upsert-accepted row counts as `Accepted` / `수락`. The legacy `insertedRows` field remains as a deprecated compatibility alias and is not a net-new insert count.
- Screenshot QA now captures 32 viewport screenshots, verifies `Accepted` / `수락` and `DB에 있음` / `Already in DB`, blocks inserted-row wording, captures console/network failures, and writes ignored artifacts under `.gstack/screenshots/upload-job-browser-qa/`.
- Operator mode now serves the web console from the backend origin so `/`, `/upload`, `/logs`, and `/settings` work without a Vite dev server after `npm run build`.
- Launcher `-BuildFrontend` now fails clearly when `npm run build` fails or does not produce `frontend/dist/index.html`; the double-click operator flow still does not build automatically.
- Mutating API calls for Settings save, Upload Preview, Upload Job start/control, and Local Supabase start/stop now require the launcher-provided local token in operator mode. Read-only APIs remain token-free; API docs are disabled in operator launcher mode rather than token-gated.
- `OPTIONS` requests are not blocked by the local token guard. Route-level API method handling can still return the normal method response.
- `launcher/install_shortcuts.ps1` and `.bat` create or refresh `Extrusion Web Console` Desktop/Start menu shortcuts targeting the repo-local launcher in the prepared operator folder.
- Shortcut packaging rejects unsafe shortcut names before writing `.lnk` files, including empty or whitespace names, invalid Windows filename characters, path separators, `..` traversal markers, and absolute paths.
- Package assembly writes each run to a new timestamped repo-external output folder by default and never performs repo-wide recursive copy, package output deletion, shortcut installation, AppData deletion, database cleanup, or Docker cleanup. QA passed targeted packaging tests (`10 passed`), full backend tests from clean cwd (`175 passed`), frontend typecheck/build/screenshot QA, and package launcher/shortcut/HTTP/token/docs smoke.
- Operator package assembly now prunes runtime `.venv` cache/test-only content, preserves dependency metadata/license files, ships a sanitized package-local README instead of marker-heavy source docs, and expands package redaction checks for release-candidate marker classes. PR #38 QA passed targeted packaging tests (`11 passed`), full backend clean-cwd tests (`176 passed`), frontend typecheck/build/screenshot QA, package `-CreateZip`, zip-entry scans with test/cache/redaction counts `0`, packaged import smoke, launcher/shortcut smoke, HTTP/token smoke, and operator docs hardening smoke.
- Operator package assembly can now validate frontend build mode through `-FrontendMode api` and records `frontendMode` in `package-build-info.json`, preventing mock-mode `frontend/dist` from being assembled as an API-mode package. The default `-FrontendMode auto` remains backward-compatible for mock/default packages and can record `frontendMode=unknown` for legacy dist metadata.
- Operator package assembly now prunes dependency-provided `.agents` runtime entries from packaged `.venv` output, keeps package/zip `.agents` entry counts at `0`, and preserves dependency metadata/license/native/runtime files.

### Fixed

- Backend startup now marks active upload jobs as `interrupted` so background upload failures are not silent after a restart.
- Upload jobs now build Edge Function payload rows through the canonical legacy-compatible transform adapter instead of raw CSV normalization.
- Legacy Korean PLC and temperature CSV columns now map to the same canonical metric keys as the legacy GUI transform path, with fixture parity coverage.
- Upload Preview now extracts reconciliation keys through the same canonical transform path as Upload Job, preventing legacy Korean PLC/temperature CSVs from being excluded before Start Upload.
- Upload job finalization no longer overwrites cancelled, interrupted, or otherwise terminal jobs when a late worker finishes.
- Mutating upload APIs now audit blocked/failure paths, including missing config, invalid preview state, active job conflicts, and invalid pause/resume/cancel transitions.
- Pause handling now records `job.paused` only on the `pausing -> paused` transition.
- Upload Job SSE now preserves native reconnect behavior and replays job-scoped events from the persisted sequence cursor.
- Concurrent job event writers now append under an immediate SQLite transaction to avoid duplicate per-job sequence values.
- Audit Logs `q` search now stays within safe scalar fields and does not search raw `error_message` or raw params JSON, preventing reverse-search of secret-bearing diagnostics.
- Frontend mock Audit Logs search now matches the backend safe scalar search policy instead of searching sanitized `errorMessage`.
- Saved config JSON now loads into new `Settings` instances while repo `.env`, launcher env, and process environment overrides still take precedence.
- Config save audit params now record safe metadata such as `savedSettings`, `rejectedSettings`, and `validationReason` instead of raw config values, DB URLs, tokens, anon keys, service role values, or malformed request bodies.
- Config file writes now use a per-config-file lock, a unique temp filename, and atomic replace.
- Upload Preview audit params now record safe metadata such as `previewRunId`, counts, `dbStatus`, `reasonCode`, and `requestedFilters` instead of raw file paths, filenames, DB URLs, tokens, anon keys, service role values, secrets, or malformed request bodies.
- Korean Upload Preview `already_in_db` status now reads `DB에 있음` instead of inserted-row wording.
- Screenshot QA mock labels and redaction scans now avoid operational CSV filename-pattern strings, raw paths, DB URLs, tokens, and credential-like values in source, docs, and generated text artifacts.
- Missing or invalid local token attempts now return a stable `403 local_token_required` response and write rate-limited blocked audit rows with safe metadata only.
- Token values are kept out of URL queries, browser storage, launcher/backend logs, audit params, screenshot artifacts, committed `.gstack` content, and committed `frontend/dist` content.
