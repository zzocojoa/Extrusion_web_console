import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
LAUNCHER_PS1 = REPO_ROOT / "launcher" / "start_web_console.ps1"
LAUNCHER_BAT = REPO_ROOT / "launcher" / "start_web_console.bat"


def test_launcher_scripts_exist_and_wrapper_targets_powershell() -> None:
    assert LAUNCHER_PS1.exists()
    assert LAUNCHER_BAT.exists()

    wrapper = LAUNCHER_BAT.read_text(encoding="utf-8")
    assert "powershell.exe" in wrapper
    assert "start_web_console.ps1" in wrapper
    assert "ExecutionPolicy Bypass" in wrapper


def test_launcher_script_keeps_allowlist_narrow() -> None:
    script = LAUNCHER_PS1.read_text(encoding="utf-8")

    assert "127.0.0.1" in script
    assert "uvicorn" in script
    assert "localhost_only" in script
    assert "npm run build" in script
    assert "npm run dev" not in script
    assert "-BuildFrontend" in script
    assert "Start-Process \"http://127.0.0.1:$BackendPort/\"" in script

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
