import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
LAUNCHER_PS1 = REPO_ROOT / "launcher" / "start_web_console.ps1"
LAUNCHER_BAT = REPO_ROOT / "launcher" / "start_web_console.bat"
SHORTCUT_PS1 = REPO_ROOT / "launcher" / "install_shortcuts.ps1"
SHORTCUT_BAT = REPO_ROOT / "launcher" / "install_shortcuts.bat"


def test_launcher_scripts_exist_and_wrapper_targets_powershell() -> None:
    assert LAUNCHER_PS1.exists()
    assert LAUNCHER_BAT.exists()
    assert SHORTCUT_PS1.exists()
    assert SHORTCUT_BAT.exists()

    wrapper = LAUNCHER_BAT.read_text(encoding="utf-8")
    assert "powershell.exe" in wrapper
    assert "start_web_console.ps1" in wrapper
    assert "ExecutionPolicy Bypass" in wrapper

    shortcut_wrapper = SHORTCUT_BAT.read_text(encoding="utf-8")
    assert "powershell.exe" in shortcut_wrapper
    assert "install_shortcuts.ps1" in shortcut_wrapper
    assert "ExecutionPolicy Bypass" in shortcut_wrapper


def test_launcher_script_keeps_allowlist_narrow() -> None:
    script = LAUNCHER_PS1.read_text(encoding="utf-8")

    assert "127.0.0.1" in script
    assert "uvicorn" in script
    assert "localhost_only" in script
    assert "npm run build" in script
    assert "$LASTEXITCODE -ne 0" in script
    assert "did not produce frontend\\dist\\index.html" in script
    assert "npm run dev" not in script
    assert "-BuildFrontend" in script
    assert "Start-Process \"http://127.0.0.1:$BackendPort/\"" in script
    assert "New-LocalApiToken" in script
    assert "RandomNumberGenerator" in script
    assert "EWC_LOCAL_API_TOKEN" in script
    assert "EWC_LOCAL_TOKEN_MODE" in script
    assert "EWC_API_DOCS_MODE" in script
    assert "$env:EWC_API_DOCS_MODE = \"disabled\"" in script
    assert "required" in script
    assert "API docs policy: disabled in operator mode." in script
    assert "token value is hidden" in script
    assert "token query" not in script.lower()
    assert "?token" not in script.lower()

    forbidden_fragments = [
        "supabase init",
        "supabase db reset",
        "docker run",
        "docker create",
        "docker rm",
        "docker volume",
        "docker prune",
        "docker compose up",
        "docker compose down",
        "Invoke-Expression",
    ]
    lowered = script.lower()
    for fragment in forbidden_fragments:
        assert fragment not in lowered


def test_launcher_script_redacts_sensitive_log_markers() -> None:
    script = LAUNCHER_PS1.read_text(encoding="utf-8")

    assert "Redact-LauncherText" in script
    assert "authorization" in script.lower()
    assert "bearer" in script.lower()
    assert "service[_ -]?role" in script
    assert "anon[_ -]?key" in script
    assert "eyJ" in script
    assert "request or response bodies" not in script


def test_launcher_passes_local_token_through_environment_only() -> None:
    script = LAUNCHER_PS1.read_text(encoding="utf-8")

    assert "$env:EWC_LOCAL_API_TOKEN = New-LocalApiToken" in script
    assert "$env:EWC_API_DOCS_MODE = \"disabled\"" in script
    assert "$arguments = @(\"-m\", \"uvicorn\"" in script
    assert "EWC_LOCAL_API_TOKEN" not in script.split("$arguments = @", 1)[1]
    assert "Start-Process \"http://127.0.0.1:$BackendPort/\"" in script
    assert "http://127.0.0.1:$BackendPort/?" not in script
    assert "localApiToken" in script
    assert "Test-FrontendBootstrap" in script


def test_launcher_powershell_syntax_parses() -> None:
    powershell = shutil.which("powershell") or shutil.which("pwsh")
    if powershell is None:
        pytest.skip("PowerShell is not available")

    command = (
        "$tokens=$null; $errors=$null; "
        f"[System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw -LiteralPath '{LAUNCHER_PS1}'), [ref]$errors) | Out-Null; "
        "if ($errors.Count -gt 0) { $errors | ForEach-Object { Write-Error $_.Message }; exit 1 }"
    )
    result = subprocess.run(
        [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0, result.stderr


def test_shortcut_script_keeps_update_policy_safe() -> None:
    script = SHORTCUT_PS1.read_text(encoding="utf-8")
    lowered = script.lower()

    assert "start_web_console.bat" in script
    assert "GetFolderPath(\"Desktop\")" in script
    assert "GetFolderPath(\"Programs\")" in script
    assert "CreateShortcut" in script
    assert "WorkingDirectory = $WorkingDirectory" in script
    assert "CheckOnly" in script
    assert "does not delete AppData config, state, logs" in script
    assert "Docker data" in script
    assert "operational CSV files" in script

    forbidden_fragments = [
        "Remove-Item",
        "del ",
        "rmdir",
        "supabase db reset",
        "docker rm",
        "docker volume",
        "docker prune",
        "docker compose down",
        "Invoke-Expression",
    ]
    for fragment in forbidden_fragments:
        assert fragment.lower() not in lowered


def test_shortcut_powershell_syntax_parses() -> None:
    powershell = shutil.which("powershell") or shutil.which("pwsh")
    if powershell is None:
        pytest.skip("PowerShell is not available")

    command = (
        "$tokens=$null; $errors=$null; "
        f"[System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw -LiteralPath '{SHORTCUT_PS1}'), [ref]$errors) | Out-Null; "
        "if ($errors.Count -gt 0) { $errors | ForEach-Object { Write-Error $_.Message }; exit 1 }"
    )
    result = subprocess.run(
        [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0, result.stderr


def test_shortcut_install_check_only_reports_expected_paths(tmp_path: Path) -> None:
    powershell = shutil.which("powershell") or shutil.which("pwsh")
    if powershell is None:
        pytest.skip("PowerShell is not available")

    desktop = tmp_path / "desktop"
    start_menu = tmp_path / "programs"
    result = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(SHORTCUT_PS1),
            "-DesktopDirectory",
            str(desktop),
            "-StartMenuDirectory",
            str(start_menu),
            "-CheckOnly",
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0, result.stderr
    assert "Desktop" in result.stdout
    assert "Start menu" in result.stdout
    assert "start_web_console.bat" in result.stdout
    assert "CheckOnly completed" in result.stdout
    assert not list(tmp_path.rglob("*.lnk"))


def test_shortcut_install_is_idempotent_and_targets_repo_launcher(tmp_path: Path) -> None:
    powershell = shutil.which("powershell") or shutil.which("pwsh")
    if powershell is None:
        pytest.skip("PowerShell is not available")

    desktop = tmp_path / "desktop"
    start_menu = tmp_path / "programs"
    command = [
        powershell,
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(SHORTCUT_PS1),
        "-DesktopDirectory",
        str(desktop),
        "-StartMenuDirectory",
        str(start_menu),
    ]

    first = subprocess.run(command, capture_output=True, text=True, timeout=10)
    second = subprocess.run(command, capture_output=True, text=True, timeout=10)

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr

    desktop_shortcuts = list(desktop.glob("*.lnk"))
    start_menu_shortcuts = list(start_menu.glob("*.lnk"))
    assert len(desktop_shortcuts) == 1
    assert len(start_menu_shortcuts) == 1

    expected_target = REPO_ROOT / "launcher" / "start_web_console.bat"
    inspect_command = (
        "$shell = New-Object -ComObject WScript.Shell; "
        f"$shortcut = $shell.CreateShortcut('{desktop_shortcuts[0]}'); "
        "Write-Output $shortcut.TargetPath; "
        "Write-Output $shortcut.WorkingDirectory"
    )
    inspected = subprocess.run(
        [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", inspect_command],
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert inspected.returncode == 0, inspected.stderr
    lines = [line.strip() for line in inspected.stdout.splitlines() if line.strip()]
    assert Path(lines[0]) == expected_target
    assert Path(lines[1]) == REPO_ROOT
