import json
import shutil
import subprocess
from pathlib import Path
from zipfile import ZipFile

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "packaging" / "operator-package.manifest.json"
ASSEMBLY_SCRIPT = REPO_ROOT / "packaging" / "assemble_operator_package.ps1"


def _powershell() -> str | None:
    return shutil.which("powershell") or shutil.which("pwsh")


def _copy_packaging_files(repo_root: Path) -> None:
    packaging = repo_root / "packaging"
    packaging.mkdir()
    shutil.copy2(MANIFEST_PATH, packaging / MANIFEST_PATH.name)
    shutil.copy2(ASSEMBLY_SCRIPT, packaging / ASSEMBLY_SCRIPT.name)


def _create_minimal_repo(repo_root: Path, *, include_venv: bool = True, include_dist: bool = True) -> None:
    (repo_root / "backend" / "app").mkdir(parents=True)
    (repo_root / "backend" / "app" / "main.py").write_text("app = object()\n", encoding="utf-8")
    (repo_root / "backend" / "requirements.txt").write_text("fastapi\n", encoding="utf-8")

    if include_dist:
        (repo_root / "frontend" / "dist" / "assets").mkdir(parents=True)
        (repo_root / "frontend" / "dist" / "index.html").write_text("<html>ok</html>\n", encoding="utf-8")
        (repo_root / "frontend" / "dist" / "assets" / "app.js").write_text("console.log('ok')\n", encoding="utf-8")

    (repo_root / "launcher").mkdir()
    for name in [
        "start_web_console.ps1",
        "start_web_console.bat",
        "install_shortcuts.ps1",
        "install_shortcuts.bat",
    ]:
        (repo_root / "launcher" / name).write_text("echo ok\n", encoding="utf-8")

    docs = repo_root / "docs"
    docs.mkdir()
    for name in [
        "23_launcher_integration_plan.md",
        "24_launcher_local_token_phase2_plan.md",
        "26_windows_shortcut_packaging_plan.md",
        "27_operator_package_smoke.md",
        "28_operator_package_manifest_plan.md",
    ]:
        (docs / name).write_text(f"# {name}\n", encoding="utf-8")

    (repo_root / "README.md").write_text("# README\n", encoding="utf-8")
    (repo_root / "CHANGELOG.md").write_text("# Changelog\n", encoding="utf-8")
    (repo_root / "VERSION").write_text("0.1.0.0\n", encoding="utf-8")

    if include_venv:
        scripts = repo_root / ".venv" / "Scripts"
        scripts.mkdir(parents=True)
        (scripts / "python.exe").write_text("stub runtime\n", encoding="utf-8")
        cache = repo_root / ".venv" / "Lib" / "site-packages" / "demo" / "__pycache__"
        cache.mkdir(parents=True)
        (cache / "module.cpython-311.pyc").write_bytes(b"compiled")
        (cache.parent / "module.pyo").write_bytes(b"optimized")

    for denylisted in [".git", ".gstack", ".agents", ".codex", ".bkit-codex", ".pytest_cache"]:
        (repo_root / denylisted).mkdir()
        (repo_root / denylisted / "marker.txt").write_text("deny\n", encoding="utf-8")
    (repo_root / "frontend" / "src").mkdir(parents=True, exist_ok=True)
    (repo_root / "frontend" / "src" / "main.tsx").write_text("deny\n", encoding="utf-8")
    (repo_root / "frontend" / "node_modules").mkdir(parents=True, exist_ok=True)
    (repo_root / "tests" / "backend" / "fixtures").mkdir(parents=True)
    (repo_root / "tests" / "backend" / "fixtures" / "operational_sample.csv").write_text(
        "must,not,copy\n", encoding="utf-8"
    )
    (repo_root / ".env").write_text("SECRET_VALUE=must-not-copy\n", encoding="utf-8")


def _run_assembly(repo_root: Path, output_root: Path, *extra_args: str) -> subprocess.CompletedProcess[str]:
    powershell = _powershell()
    if powershell is None:
        pytest.skip("PowerShell is not available")

    return subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(repo_root / "packaging" / "assemble_operator_package.ps1"),
            "-OutputRoot",
            str(output_root),
            *extra_args,
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_manifest_json_contract_is_valid() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert manifest["schemaVersion"] == 1
    assert manifest["packageRoot"] == "ExtrusionWebConsole"
    assert "backend/app" in manifest["requiredPaths"]
    assert "frontend/dist/index.html" in manifest["requiredPaths"]
    assert ".venv/Scripts/python.exe" in manifest["operatorReadyChecks"]
    assert any(entry["source"] == ".venv" for entry in manifest["includeAllowlist"])
    assert ".git" in manifest["excludeDenylist"]
    assert "tests" in manifest["excludeDenylist"]
    assert "*.csv" in manifest["excludeDenylist"]
    assert "X-EWC-Local-Token" not in MANIFEST_PATH.read_text(encoding="utf-8")


def test_assembly_powershell_syntax_parses() -> None:
    powershell = _powershell()
    if powershell is None:
        pytest.skip("PowerShell is not available")

    command = (
        "$tokens=$null; $errors=$null; "
        f"[System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw -LiteralPath '{ASSEMBLY_SCRIPT}'), [ref]$errors) | Out-Null; "
        "if ($errors.Count -gt 0) { $errors | ForEach-Object { Write-Error $_.Message }; exit 1 }"
    )
    result = subprocess.run(
        [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0, result.stderr


def test_assembly_script_keeps_command_policy_narrow() -> None:
    script = ASSEMBLY_SCRIPT.read_text(encoding="utf-8")
    lowered = script.lower()

    assert "copy-manifestdirectory" in lowered
    assert "includeallowlist" in lowered
    assert "compress-archive" in lowered
    assert "get-filehash" in lowered
    assert "invoke-expression" not in lowered
    assert "remove-item" not in lowered
    assert "supabase db reset" not in lowered
    assert "docker rm" not in lowered
    assert "docker volume" not in lowered
    assert "docker prune" not in lowered
    assert "docker compose down" not in lowered


def test_assembly_copies_allowlist_and_rejects_denylist(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    output_root = tmp_path / "out"
    repo_root.mkdir()
    _copy_packaging_files(repo_root)
    _create_minimal_repo(repo_root)

    result = _run_assembly(repo_root, output_root, "-PackageLabel", "fixture-package")

    assert result.returncode == 0, result.stderr
    package_root = output_root / "fixture-package" / "ExtrusionWebConsole"
    assert package_root.exists()
    assert (package_root / "backend" / "app" / "main.py").exists()
    assert (package_root / "frontend" / "dist" / "index.html").exists()
    assert (package_root / ".venv" / "Scripts" / "python.exe").exists()
    assert not (package_root / ".git").exists()
    assert not (package_root / ".gstack").exists()
    assert not (package_root / ".env").exists()
    assert not (package_root / "tests").exists()
    assert not (package_root / "frontend" / "src").exists()
    assert not list(package_root.rglob("*.csv"))
    assert not list(package_root.rglob("*.pyc"))
    assert not list(package_root.rglob("*.pyo"))
    assert not list(package_root.rglob("__pycache__"))

    build_info = json.loads((package_root / "package-build-info.json").read_text(encoding="utf-8-sig"))
    assert build_info["runtimeMode"] == "operator-ready"
    assert build_info["zipCreated"] is False


def test_assembly_fails_when_venv_is_missing_without_incomplete_switch(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    output_root = tmp_path / "out"
    repo_root.mkdir()
    _copy_packaging_files(repo_root)
    _create_minimal_repo(repo_root, include_venv=False)

    result = _run_assembly(repo_root, output_root, "-PackageLabel", "missing-venv")

    assert result.returncode != 0
    assert "Required package source is missing: .venv" in f"{result.stdout}\n{result.stderr}"
    assert not (output_root / "missing-venv").exists()


def test_assembly_allows_explicit_incomplete_runtime_mode(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    output_root = tmp_path / "out"
    repo_root.mkdir()
    _copy_packaging_files(repo_root)
    _create_minimal_repo(repo_root, include_venv=False)

    result = _run_assembly(
        repo_root,
        output_root,
        "-PackageLabel",
        "incomplete-runtime",
        "-AllowIncompleteRuntime",
    )

    assert result.returncode == 0, result.stderr
    package_root = output_root / "incomplete-runtime" / "ExtrusionWebConsole"
    build_info = json.loads((package_root / "package-build-info.json").read_text(encoding="utf-8-sig"))
    assert build_info["runtimeMode"] == "maintainer-prep-incomplete"
    assert not (package_root / ".venv").exists()


def test_assembly_fails_when_frontend_dist_is_missing(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    output_root = tmp_path / "out"
    repo_root.mkdir()
    _copy_packaging_files(repo_root)
    _create_minimal_repo(repo_root, include_dist=False)

    result = _run_assembly(repo_root, output_root, "-PackageLabel", "missing-dist")

    assert result.returncode != 0
    assert "Required package source is missing: frontend/dist" in f"{result.stdout}\n{result.stderr}"
    assert not (output_root / "missing-dist").exists()


def test_assembly_create_zip_records_checksum(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    output_root = tmp_path / "out"
    repo_root.mkdir()
    _copy_packaging_files(repo_root)
    _create_minimal_repo(repo_root)

    result = _run_assembly(repo_root, output_root, "-PackageLabel", "zip-package", "-CreateZip")

    assert result.returncode == 0, result.stderr
    zip_path = output_root / "zip-package.zip"
    checksum_path = output_root / "zip-package.zip.sha256"
    assert zip_path.exists()
    assert checksum_path.exists()
    checksum = checksum_path.read_text(encoding="ascii")
    assert "zip-package.zip" in checksum
    assert len(checksum.split()[0]) == 64

    with ZipFile(zip_path) as archive:
        names = archive.namelist()
    assert "ExtrusionWebConsole/frontend/dist/index.html" in names
    assert not any(name.startswith("ExtrusionWebConsole/tests/") for name in names)
    assert not any(name.endswith(".csv") for name in names)

    build_info = json.loads(
        (output_root / "zip-package" / "ExtrusionWebConsole" / "package-build-info.json").read_text(
            encoding="utf-8-sig"
        )
    )
    assert build_info["zipCreated"] is True
    assert build_info["zipSha256"] == checksum.split()[0]


def test_assembly_default_output_is_repeatable_without_deleting_existing_output(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    output_root = tmp_path / "out"
    repo_root.mkdir()
    _copy_packaging_files(repo_root)
    _create_minimal_repo(repo_root)

    first = _run_assembly(repo_root, output_root)
    second = _run_assembly(repo_root, output_root)

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    package_dirs = list(output_root.glob("ExtrusionWebConsole-*"))
    assert len(package_dirs) == 2
