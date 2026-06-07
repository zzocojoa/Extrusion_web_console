# Operator Package Manifest / Assembly Plan

Status: implemented on branch `codex/operator-package-assembly-impl`

Date: 2026-06-07

Scope: prepared operator package manifest and safe assembly plan.

This plan defines the package contents contract for the prepared Windows operator folder.

Implementation result on branch `codex/operator-package-assembly-impl`:

- Added `packaging/operator-package.manifest.json`.
- Added `packaging/assemble_operator_package.ps1`.
- The script copies only manifest allowlist entries and never performs a repository-root recursive copy.
- Default output is a new timestamped package folder under `C:\tmp\ExtrusionWebConsole-packages\`.
- Existing package output is not deleted; explicit duplicate package labels fail safely.
- `-CreateZip` creates an optional zip and writes a SHA-256 checksum next to it.
- Package root remains `ExtrusionWebConsole/`.
- Required path, operator readiness, denylist, and redaction validation run after assembly.
- `.venv` is required for operator-ready packages unless `-AllowIncompleteRuntime` is explicitly used.
- `.venv` runtime contents are allowed, but `__pycache__`, `*.pyc`, and `*.pyo` are filtered out during copy and rejected by validation.
- The script prints package smoke guidance without running shortcut install, AppData cleanup, database cleanup, or Docker cleanup.

## Goal

Make the operator package repeatable and reviewable before handoff.

The package must include only runtime material needed for the local web console, shortcuts, built frontend, and target-PC Python runtime. It must exclude source-control data, developer artifacts, raw environment files, logs, state databases, generated screenshots, and operational CSV data.

The operator should be able to launch the packaged console without Node or npm.

## Package Root

The prepared package root is:

```text
ExtrusionWebConsole/
```

Expected operator-ready tree:

```text
ExtrusionWebConsole/
  backend/
    app/
    requirements.txt
  frontend/
    dist/
      index.html
      assets/
  launcher/
    start_web_console.ps1
    start_web_console.bat
    install_shortcuts.ps1
    install_shortcuts.bat
  docs/
    23_launcher_integration_plan.md
    24_launcher_local_token_phase2_plan.md
    26_windows_shortcut_packaging_plan.md
    27_operator_package_smoke.md
    28_operator_package_manifest_plan.md
  .venv/
    Scripts/
      python.exe
  README.md
  CHANGELOG.md
  VERSION
```

The tree above is a runtime package shape, not an installer, MSI, Windows service, or machine-wide deployment.

## Include Allowlist

The future assembly script must copy only allowlisted paths. It must not copy the repository root recursively.

| Path | Required | Purpose |
| --- | --- | --- |
| `backend/app/` | Yes | FastAPI application runtime. |
| `backend/requirements.txt` | Yes | Maintainer-visible Python dependency record. |
| `frontend/dist/` | Yes | Built frontend served by FastAPI in operator mode. |
| `launcher/` | Yes | Start and shortcut scripts. |
| `README.md` | Yes | Operator and maintainer launch guidance. |
| `CHANGELOG.md` | Yes | Release history and package notes. |
| `VERSION` | Yes | Package version marker when present. |
| selected `docs/` files | Yes | Operator launcher, token, shortcut, package smoke, and manifest guidance. |
| `.venv/` | Yes for operator-ready package | Target-PC prepared Python runtime. |

Selected docs for v1 operator package:

- `docs/23_launcher_integration_plan.md`
- `docs/24_launcher_local_token_phase2_plan.md`
- `docs/26_windows_shortcut_packaging_plan.md`
- `docs/27_operator_package_smoke.md`
- `docs/28_operator_package_manifest_plan.md`

Other docs can be added later only when they are operator-facing or directly needed for package validation.

## Exclude Denylist

The future manifest and assembly validation must reject these paths if they appear in the package output:

| Path or class | Reason |
| --- | --- |
| `.git/` | Source-control metadata is not runtime material. |
| `.gstack/` | Generated QA artifacts and screenshots are not package contents. |
| `.agents/`, `.codex/`, `.bkit-codex/` | Developer-agent configuration is not operator runtime material. |
| `.pytest_cache/`, `__pycache__/`, `*.pyc` | Test/cache artifacts are not package contents. |
| `frontend/node_modules/` | Operator mode must not require Node/npm runtime dependencies. |
| `frontend/src/`, `frontend/qa/` | Frontend source and QA tooling are not served in operator mode. |
| `tests/` | Test fixtures and test code are not operator runtime material. |
| raw `.env*` files | Environment files can contain secrets or local paths. |
| logs | Logs remain outside the package under AppData. |
| state DB files | State remains outside the package under AppData. |
| generated screenshots | Screenshot artifacts are not release contents. |
| temp smoke folders | Smoke outputs are not release contents. |
| operational CSV fixtures or samples | Operational data must never be packaged. |
| operational CSV paths or contents | Sensitive local data location/content must not be documented or copied. |

The denylist is a safety backstop. The primary mechanism remains allowlist-only copy.

## Python Runtime Policy

An operator-ready package requires:

```text
.venv/Scripts/python.exe
```

The `.venv` is target-PC and Python-version sensitive. A maintainer must prepare or refresh it on the target PC before handoff.

If `.venv/Scripts/python.exe` is missing, the package is maintainer-prep incomplete. The launcher should fail clearly and should not ask the operator to install dependencies during normal startup.

## Frontend Build Policy

The package includes `frontend/dist/`.

The operator double-click flow must not run:

```text
npm run build
```

Frontend build is a developer or release-maintainer action before assembly. If `frontend/dist/index.html` is missing, the assembly validation must fail before handoff. The launcher already fails clearly when the built frontend is missing.

## Future Manifest Contract

Future implementation should add:

```text
packaging/operator-package.manifest.json
```

Planned JSON fields:

| Field | Meaning |
| --- | --- |
| `schemaVersion` | Manifest schema version. |
| `packageName` | Human-readable package name. |
| `requiredPaths` | Paths that must exist in an operator-ready package. |
| `includeAllowlist` | Explicit source-to-package copy rules. |
| `excludeDenylist` | Paths and patterns that must not appear in output. |
| `operatorReadyChecks` | Runtime readiness checks such as `.venv` and built frontend presence. |
| `redactionChecks` | Secret/path/content marker scans to run on package output and logs. |
| `smokeChecks` | Required package smoke checks. |
| `buildMetadata` | Source commit, build time, package label, and optional zip checksum metadata. |

The manifest must not contain secret values, local API tokens, authorization values, database connection strings, or operational data paths.

## Future Assembly Script Contract

Future implementation should add:

```text
packaging/assemble_operator_package.ps1
```

Required behavior:

- Run from the repository root or resolve the repository root from the script location.
- Copy only manifest allowlist entries.
- Create a new timestamped output folder by default.
- Avoid deleting existing package output by default.
- Write output outside the tracked source tree.
- Fail before copying when required source paths are missing.
- Fail after copying if any denylisted path or marker appears in output.
- Never read, copy, print, or package raw `.env` files or operational CSV data.
- Never delete AppData config, state databases, logs, Docker data, or database data.
- Never run DB reset/delete/cleanup/prune commands.
- Never run Docker volume/container delete or prune commands.
- Never run shortcut installation as part of assembly.

Recommended default output root for smoke and maintainer runs:

```text
C:\tmp\ExtrusionWebConsole-packages\
```

The generated package folder name should include a release label, source commit short hash, and timestamp.

## Zip And Checksum Policy

The primary output is the prepared folder.

Zip creation is a future maintainer option:

```text
-CreateZip
```

When a zip is created, the assembly script must also write a SHA-256 checksum next to it. The checksum is required for zip handoff verification.

Folder output validation is based on manifest verification and package smoke, not on a single folder checksum.

## AppData Config, State, And Logs

These stay outside the package:

```text
%APPDATA%\ExtrusionWebConsole\
```

Package assembly, shortcut install, and package replacement must not copy, overwrite, delete, reset, or prune AppData config, state DB files, or launcher logs.

This keeps package replacement separate from operator settings and runtime history.

## Shortcut Installer Relationship

The package includes:

```text
launcher/install_shortcuts.ps1
launcher/install_shortcuts.bat
```

Assembly must not execute shortcut installation. Shortcut install remains a maintainer step after the prepared folder exists.

Required shortcut validation remains:

- `launcher/install_shortcuts.ps1 -CheckOnly`
- temp Desktop/Start menu smoke in QA
- idempotent re-run with one shortcut per target
- target points to package-local `launcher/start_web_console.bat`
- working directory is the package root

## Local Token And API Docs Policy

The package must preserve launcher phase 2 behavior:

- operator mode generates a per-run local API token
- token is passed through process environment only
- token is injected into served HTML at runtime only
- token is sent only on same-origin mutating API requests
- read-only APIs remain token-free
- operator mode API docs routes remain disabled

The token must not appear in:

- manifest files
- package zip names
- shortcut arguments
- launcher logs
- backend logs
- audit rows
- screenshots
- generated artifacts
- documentation

## Redaction And Security Policy

Assembly logs and package validation output must be presence/count oriented.

Allowed output examples:

- `frontend dist: present`
- `python runtime: present`
- `denylist matches: 0`
- `token marker matches: 0`

Forbidden output classes:

- secret values
- database connection strings
- local API token values
- authorization header values
- raw environment file contents
- operational CSV paths
- operational CSV contents
- raw row contents

## Validation And Smoke Plan

Document-only PR validation:

- `git diff --check`
- confirm the PR changes only `docs/28_operator_package_manifest_plan.md`
- scan docs/source changes for secret values and operational data path/content markers
- confirm generated `.gstack` artifacts are not staged
- confirm `frontend/dist` is not staged
- confirm untracked operational CSV fixtures are not staged

Future implementation validation:

- manifest allowlist/denylist static validation
- package contents smoke
- `launcher/start_web_console.ps1 -CheckOnly`
- `launcher/install_shortcuts.ps1 -CheckOnly`
- shortcut temp path and idempotency smoke
- HTTP smoke:
  - `/`
  - `/upload`
  - `/logs`
  - `/settings`
  - `/api/health`
  - `/api/config`
  - `/api/audit?limit=1`
- token smoke:
  - read-only no-token requests succeed
  - mutating no-token request returns `403`
- operator docs smoke:
  - `/api/docs`
  - `/api/openapi.json`
  - `/api/redoc`
- redaction scan:
  - local token marker absent
  - authorization marker absent
  - database connection marker absent
  - secret-like marker absent
  - operational CSV path/content absent

## Implementation Order

1. Land this document-only plan.
2. Add `packaging/operator-package.manifest.json` in a follow-up implementation branch.
3. Add `packaging/assemble_operator_package.ps1`.
4. Add static package validation for allowlist, denylist, required paths, and redaction markers.
5. Run package assembly against a temp output root.
6. Run package contents smoke and launcher HTTP/token/docs smoke.
7. Record package smoke results in a follow-up QA report.

## Out Of Scope

- Assembly script implementation in this PR.
- Backend, frontend, launcher, or shortcut behavior changes in this PR.
- MSI, MSIX, installer, service, tray app, auto-update, registry writes, or code signing.
- Production deploy.
- LAN or multi-user access.
- DB reset, delete, cleanup, prune, migration, or destructive repair.
- Docker volume/container delete or prune.
- Supabase init/bootstrap/create.
- AppData config/state/log deletion.
- Packaging raw environment files.
- Packaging operational CSV fixtures, samples, paths, or contents.
