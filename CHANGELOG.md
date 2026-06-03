# Changelog

All notable changes to Extrusion Web Console are documented here.

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
- Backend now exposes `GET /api/config` and `PUT /api/config` for safe config reads and saves while the Settings page remains read-only.
- Settings saves now write `settings.save` audit rows for success, failure, malformed request validation, and env override blocked paths.
- Upload Preview now writes `upload.preview` audit rows for success, DB unreachable, missing source, malformed request validation, and active preview conflict paths.

### Changed

- Start Upload only snapshots `target` Preview items. `already_in_db`, `partial_overlap`, `risky`, and `excluded` rows remain excluded in v1.
- Preview-origin upload disables legacy latest-timestamp Smart Sync filtering and keeps database upsert on `(timestamp, device_id)` as final duplicate protection.

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
