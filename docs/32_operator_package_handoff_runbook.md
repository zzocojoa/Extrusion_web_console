# Operator Package Handoff Runbook

Status: draft for maintainer handoff

Date: 2026-06-07

Scope: operator handoff procedure for a prepared Extrusion Web Console package that has passed final release smoke.

## Goal

Give a maintainer a repeatable, non-destructive handoff flow for delivering a prepared operator package to an operator PC.

This runbook covers:

- package zip and checksum handoff
- optional NSIS installer EXE handoff
- extraction location
- shortcut install
- first launch
- Settings verification
- log locations
- rollback
- support escalation

This document does not change product code, launcher behavior, package assembly, local Supabase runtime policy, AppData state, Docker state, database state, or operational CSV data.

## Preconditions

Before handoff, the maintainer must have:

| Item | Requirement |
| --- | --- |
| Package folder or zip | Built from a release-smoked package branch or `main` |
| Checksum file | Adjacent SHA-256 checksum for zip handoff |
| Optional NSIS installer | Built from the same verified package zip and checksum |
| Final release smoke | Passed and documented |
| Target PC | Windows operator PC with expected local runtime access |
| Prepared runtime | Package contains `.venv/Scripts/python.exe` |
| Built frontend | Package contains `frontend/dist/index.html` |
| Local config | Operator settings remain outside the package under AppData |

Do not ask the operator to install Node, npm, or Python packages during normal launch.

## Handoff Artifacts

For zip handoff, deliver exactly these release artifacts:

| Artifact | Purpose |
| --- | --- |
| `<package-label>.zip` | Prepared operator package |
| `<package-label>.zip.sha256` | Checksum verification |

For optional NSIS installer handoff, deliver exactly these release artifacts:

| Artifact | Purpose |
| --- | --- |
| `<package-label>-Setup.exe` | User-scope installer wrapping the prepared package zip |
| `<package-label>-Setup.exe.sha256` | Installer checksum verification |
| `<package-label>.zip` | Embedded payload source of truth for recovery/debugging |
| `<package-label>.zip.sha256` | Payload checksum verification |

The NSIS EXE is unsigned unless a separate signing process is completed.
Windows may show an unknown-publisher warning. Do not treat the EXE as a
different release artifact from the zip: the package metadata inside the
payload must still match the approved source commit, frontend mode, runtime
mode, and frontend build metadata state.

Optional maintainer-only evidence:

| Artifact | Purpose |
| --- | --- |
| Release smoke report | Shows package readiness and known limitations |
| Package build metadata | Confirms source commit and runtime mode |

Do not deliver raw `.env` files, logs, state databases, generated screenshots, package assembly temp folders, source-control folders, developer source trees, test fixtures, or operational CSV data.

## Verify Checksum

On the handoff machine, verify that the zip matches its checksum before extraction.

PowerShell example:

```powershell
$zip = "<package-label>.zip"
$checksum = "<package-label>.zip.sha256"
$actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $zip).Hash.ToLowerInvariant()
$expected = (Get-Content -LiteralPath $checksum -Raw).Split()[0].ToLowerInvariant()
if ($actual -ne $expected) { throw "Package checksum mismatch" }
```

If checksum verification fails, stop the handoff. Do not extract or run the package.

## Optional NSIS Installer

Maintainers can build a user-scope NSIS installer from an already assembled
API-mode package:

```powershell
.\packaging\build_nsis_installer.ps1 -PackageContainer <package-container>
```

The installer build requires `makensis.exe`. The build script searches `PATH`,
standard NSIS install locations, Scoop, and the local electron-builder NSIS
cache. Maintainers can pass `-MakensisPath` for an explicit compiler path. The
script validates the adjacent package zip checksum before producing the EXE and
records an adjacent EXE SHA-256 file. The embedded install script validates the
payload checksum and `package-build-info.json` before installing. The required
metadata class is:

```text
frontendMode=api
runtimeMode=operator-ready
frontendBuildMetadataPresent=true
```

For maintainer check-only smoke without installing:

```powershell
$env:EWC_INSTALLER_CHECK_ONLY = "1"
$setup = ".\<package-label>-Setup.exe"
$process = Start-Process -FilePath $setup -ArgumentList "/S" -Wait -PassThru
Remove-Item Env:\EWC_INSTALLER_CHECK_ONLY
if ($process.ExitCode -ne 0) { throw "Installer check-only failed: $($process.ExitCode)" }
```

For controlled install smoke, use temporary install and shortcut directories:

```powershell
$env:EWC_INSTALL_BASE = "<temp-smoke-root>\Programs"
$env:EWC_INSTALLER_DESKTOP_DIR = "<temp-smoke-root>\Desktop"
$env:EWC_INSTALLER_START_MENU_DIR = "<temp-smoke-root>\StartMenu"
$setup = ".\<package-label>-Setup.exe"
$process = Start-Process -FilePath $setup -ArgumentList "/S" -Wait -PassThru
Remove-Item Env:\EWC_INSTALL_BASE,Env:\EWC_INSTALLER_DESKTOP_DIR,Env:\EWC_INSTALLER_START_MENU_DIR
if ($process.ExitCode -ne 0) { throw "Installer smoke failed: $($process.ExitCode)" }
```

The installer must not delete AppData config, state databases, launcher logs,
local Supabase data, Docker containers, Docker volumes, or operational CSV
files. Installer rollback is the same package rollback model: retain the
previous known-good package, repoint shortcuts through that package's shortcut
installer, and preserve failed-package evidence for maintainer review.

## Extraction Location

Extract the package into a stable operator-owned folder.

Recommended shape:

```text
<operator-app-root>\
  ExtrusionWebConsole\
```

The package root must contain:

```text
ExtrusionWebConsole\
  backend\
  frontend\dist\
  launcher\
  .venv\
  README.md
  CHANGELOG.md
  VERSION
```

Do not extract into:

- a source repository folder
- a temporary download folder that may be cleaned automatically
- a synced folder that can lock files during launch
- an existing package folder unless this is an intentional replacement

## Pre-Launch Checks

From the extracted `ExtrusionWebConsole` folder, run:

```powershell
.\launcher\tray_supervisor.ps1 -CheckOnly
.\launcher\start_web_console.ps1 -CheckOnly
```

Expected result:

- tray supervisor prerequisites are present
- tray menu is `Open` and `Exit`
- package prerequisites are present
- local token policy is required in operator mode
- API docs policy is disabled in operator mode
- no backend process is started
- no token value is printed

Then run:

```powershell
.\launcher\install_shortcuts.ps1 -CheckOnly
```

Expected result:

- Desktop and Start menu each show one `Extrusion Web Console` shortcut target
- shortcut targets use hidden PowerShell tray execution, not direct `.bat` targets
- working directory is the package root
- legacy Stop/Restart shortcut cleanup is listed for the selected shortcut scopes
- no shortcut is written in check-only mode
- AppData config, state, logs, Docker data, database data, and operational CSV data are not deleted

If either check fails, stop and contact the maintainer before first launch.

## Install Shortcuts

After check-only passes, install or refresh shortcuts:

```powershell
.\launcher\install_shortcuts.ps1
```

This creates or updates:

- Desktop shortcut: `Extrusion Web Console`
- Start menu shortcut: `Extrusion Web Console`

Shortcut install is idempotent. Re-running updates existing shortcuts instead of creating duplicates. It also removes only legacy `Extrusion Web Console Stop` and `Extrusion Web Console Restart` `.lnk` files from the selected Desktop/Start menu shortcut directories.

Do not manually edit the shortcut target unless instructed by the maintainer.

## First Launch

Launch through one of these paths:

```text
Extrusion Web Console desktop shortcut
```

or:

```powershell
.\launcher\tray_supervisor.ps1
```

Expected first-launch behavior:

- tray supervisor stays running after the browser is opened
- backend binds to `127.0.0.1`
- browser opens the local web console
- no command window remains on screen when launched from the shortcut
- frontend is served from the package
- mutating APIs are protected by a per-run local token
- token is not printed or placed in the URL
- API docs routes are disabled in operator mode

The operator should see the Dashboard first. If the browser is closed, use the tray `Open` action to reopen it. If the browser does not open, the maintainer can open the localhost URL reported by the launcher log without copying any token values.

## Stop And Restart

Use the tray menu:

```text
Exit
```

or run the maintainer stop script:

```powershell
.\launcher\stop_web_console.ps1
```

Expected stop behavior:

- `/api/health` reports `service=extrusion-web-console-api`
- `/api/health` reports localhost-only status
- `/api/health` reports a process id
- the OS process matches the expected Python uvicorn backend command for the selected port
- only that verified backend process is stopped
- port `8000` closes after stop

If port `8000` is open but `/api/health` is missing, reports a different service, is not localhost-only, or points to a non-matching process, the stop script must refuse to stop anything and log the reason.

Maintainer restart remains script-only:

```powershell
.\launcher\restart_web_console.ps1
```

Restart runs the same safe stop path before starting the backend and opening the browser again. It is not exposed as a separate operator shortcut.

## Settings Verification

After first launch, open Settings and verify:

| Setting area | Expected check |
| --- | --- |
| Local Supabase settings | Presence and status are understandable |
| Source/config paths | Displayed only as intended by the app |
| Env/process overrides | Read-only fields are clearly disabled |
| Secret fields | Raw values are hidden |
| Save behavior | Operator-facing validation appears on invalid input |

Do not paste secrets into chat, tickets, screenshots, or runbook notes.

If Settings save is required, verify Audit Logs after save:

```text
Logs > Audit Logs
```

Expected result:

- `settings.save` row appears
- raw secret values are not visible
- raw DB URLs, tokens, and authorization values are not visible

## Runtime Smoke

For handoff acceptance, check these pages:

| Page | Expected result |
| --- | --- |
| Dashboard | Loads without browser console-visible crash |
| Upload | Upload Preview and Upload Job tabs are visible |
| Logs | Job Logs and Audit Logs are visible |
| Settings | Config sections load |

If Upload Preview or Upload Job requires local Supabase, verify local Supabase readiness separately using the operator site's runtime status. Do not run database reset, cleanup, prune, Docker cleanup, or destructive repair as part of handoff.

## Docker Desktop 2375 Diagnostic Exception

The Docker Desktop setting `Expose daemon on tcp://localhost:2375 without TLS`
must remain off for normal operator handoff and package smoke. Do not make it an
operator prerequisite.

Maintainers may enable it only temporarily for a bounded developer/maintainer
diagnostic or failure reproduction when sanitized Docker or Vector log evidence
is required and the normal runtime status probes are insufficient. Normal
package validation, routine release checks, and operator handoff must keep the
setting off. After the evidence is captured, turn the setting off again and
record that it was returned off.

Vector or Grafana `attention` is a non-core observability caveat when Supabase
API, DB, Edge, Upload Preview, and Audit evidence are normal. It should be
recorded for support, but it must not trigger Docker cleanup/reset, Supabase
reset/cleanup, LAN exposure, or a bypass of the upload approval gates.

## Log Locations

Launcher logs are stored under:

```text
%APPDATA%\ExtrusionWebConsole\logs\launcher\
```

Application config and state remain under:

```text
%APPDATA%\ExtrusionWebConsole\
```

When collecting support evidence:

- include timestamps
- include high-level error text
- do not include raw secret values
- do not include DB URLs
- do not include token values
- do not include operational CSV paths or CSV contents

## Rollback

Rollback means returning the operator shortcut to the previous known-good package folder.

Recommended rollback flow:

1. Close the browser tab.
2. Use tray `Exit`, or run `.\launcher\stop_web_console.ps1`, for the current package.
3. Keep the failed package folder for maintainer inspection.
4. Point shortcuts back to the previous known-good package folder by running that folder's shortcut installer.
5. Launch the previous package.
6. Verify Dashboard, Settings, and Logs load.

Do not delete AppData config, state databases, logs, local Supabase data, Docker containers, Docker volumes, or operational CSV files during rollback.

## Replacement Policy

When replacing a package:

- create or extract into a new versioned package folder
- verify checksum before extraction
- run launcher `-CheckOnly`
- run shortcut installer `-CheckOnly`
- update shortcuts only after checks pass
- keep the previous known-good package until the new package is accepted

Avoid overwriting the previous package folder in place. Keeping both folders makes rollback straightforward.

## Support Escalation

Escalate to the maintainer when:

- checksum verification fails
- launcher `-CheckOnly` fails
- shortcut `-CheckOnly` fails
- first launch does not open the local web console
- Settings cannot load
- Settings save fails unexpectedly
- Audit Logs cannot be opened after a Settings save
- local Supabase runtime status is unclear or blocked
- Upload Preview or Upload Job shows unexpected blocking errors

Support notes should include:

- package label
- package `VERSION`
- whether checksum verification passed
- whether `-CheckOnly` passed
- first failed step
- relevant timestamp
- sanitized error summary

Support notes must not include secret values, DB URLs, local API tokens, authorization headers, raw environment files, operational CSV paths, CSV contents, or raw row contents.

## Handoff Acceptance Checklist

| Check | Status |
| --- | --- |
| Zip checksum verified |  |
| Package extracted into stable folder |  |
| `launcher\tray_supervisor.ps1 -CheckOnly` passed |  |
| `launcher\start_web_console.ps1 -CheckOnly` passed |  |
| `launcher\stop_web_console.ps1 -CheckOnly` passed |  |
| `launcher\restart_web_console.ps1 -CheckOnly` passed |  |
| `launcher\install_shortcuts.ps1 -CheckOnly` passed |  |
| Single Desktop/Start menu tray shortcuts installed or refreshed |  |
| First launch opened Dashboard |  |
| Browser close left tray supervisor alive |  |
| Tray Exit closed the verified backend port |  |
| Maintainer restart script reopened Dashboard when tested |  |
| Settings loaded |  |
| Logs page loaded |  |
| Secret values hidden in UI |  |
| Previous known-good package retained |  |
| Rollback path understood |  |

## Out Of Scope

- feature implementation
- package assembly policy changes
- launcher behavior outside the documented tray Open/Exit lifecycle
- shortcut installer behavior outside hidden single tray shortcut refresh
- production deploy
- database reset/delete/cleanup/prune
- Docker volume/container delete or prune
- AppData config/state/log deletion
- packaging raw `.env` files
- packaging operational CSV fixtures, paths, or contents
- collecting or sharing secret values
