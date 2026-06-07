import json
import shutil
import subprocess
from pathlib import Path
from zipfile import ZipFile

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "packaging" / "operator-package.manifest.json"
ASSEMBLY_SCRIPT = REPO_ROOT / "packaging" / "assemble_operator_package.ps1"
FRONTEND_PACKAGE_PATH = REPO_ROOT / "frontend" / "package.json"
FRONTEND_BUILD_SCRIPT = REPO_ROOT / "frontend" / "scripts" / "build.mjs"


def _powershell() -> str | None:
    return shutil.which("powershell") or shutil.which("pwsh")


def _copy_packaging_files(repo_root: Path) -> None:
    packaging = repo_root / "packaging"
    packaging.mkdir()
    shutil.copy2(MANIFEST_PATH, packaging / MANIFEST_PATH.name)
    shutil.copy2(ASSEMBLY_SCRIPT, packaging / ASSEMBLY_SCRIPT.name)


def _create_minimal_repo(
    repo_root: Path,
    *,
    include_venv: bool = True,
    include_dist: bool = True,
    frontend_mode: str = "mock",
    include_frontend_metadata: bool = True,
) -> None:
    (repo_root / "backend" / "app").mkdir(parents=True)
    (repo_root / "backend" / "app" / "main.py").write_text("app = object()\n", encoding="utf-8")
    (repo_root / "backend" / "requirements.txt").write_text("fastapi\n", encoding="utf-8")

    if include_dist:
        (repo_root / "frontend" / "dist" / "assets").mkdir(parents=True)
        (repo_root / "frontend" / "dist" / "index.html").write_text("<html>ok</html>\n", encoding="utf-8")
        (repo_root / "frontend" / "dist" / "assets" / "app.js").write_text("console.log('ok')\n", encoding="utf-8")
        if include_frontend_metadata:
            (repo_root / "frontend" / "dist" / "frontend-build-info.json").write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "frontendMode": frontend_mode,
                        "createdUtc": "2026-06-08T00:00:00.000Z",
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

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
    (docs / "operator_package_runtime_note.md").write_text("# Operator package\n", encoding="utf-8")
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
        package_root = repo_root / ".venv" / "Lib" / "site-packages" / "demo"
        (package_root / "__init__.py").write_text("VALUE = 1\n", encoding="utf-8")
        agents = package_root / ".agents" / "skills" / "demo"
        agents.mkdir(parents=True)
        (agents / "SKILL.md").write_text("# dependency agent skill\n", encoding="utf-8")
        for test_dir in ["test", "tests", "testing", "testsuite"]:
            (package_root / test_dir).mkdir(parents=True)
            (package_root / test_dir / "case.py").write_text("assert True\n", encoding="utf-8")
        pytest_cache = repo_root / ".venv" / "Lib" / "site-packages" / ".pytest_cache" / "v"
        pytest_cache.mkdir(parents=True)
        (pytest_cache / "cache").write_text("cache\n", encoding="utf-8")
        metadata = repo_root / ".venv" / "Lib" / "site-packages" / "demo-1.0.0.dist-info"
        metadata.mkdir()
        for name in ["METADATA", "RECORD", "WHEEL", "entry_points.txt", "LICENSE", "NOTICE", "COPYING"]:
            (metadata / name).write_text(f"{name}\n", encoding="utf-8")

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


def _marker_text(marker_class: str) -> str:
    marker_builders = {
        "credential-like-marker": lambda: "credential" + ": " + "synthetic-value",
        "database-url-marker": lambda: "postgres" + "://" + "user" + ":pass" + "@example.invalid/db",
        "authorization-bearer-marker": lambda: "Authorization" + ": Bearer " + "synthetic-token",
        "jwt-like-marker": lambda: ".".join(
            [
                "eyJ" + "syntheticHeader",
                "syntheticPayload",
                "syntheticSignature",
            ]
        ),
        "windows-absolute-path-marker": lambda: "C:" + "\\synthetic\\operator\\data",
        "operational-filename-family-marker": lambda: "Factory" + "_Synthetic_Log",
        "timestamp-style-csv-marker": lambda: "20260209" + "_" + "074100" + ".csv",
        "anon-key-assignment-marker": lambda: "anon" + "_key" + ": " + "synthetic-value",
        "service-role-assignment-marker": lambda: "service" + "_role" + ": " + "synthetic-value",
    }
    return marker_builders[marker_class]()


def test_manifest_json_contract_is_valid() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert manifest["schemaVersion"] == 1
    assert manifest["packageRoot"] == "ExtrusionWebConsole"
    assert "backend/app" in manifest["requiredPaths"]
    assert "frontend/dist/index.html" in manifest["requiredPaths"]
    assert ".venv/Scripts/python.exe" in manifest["operatorReadyChecks"]
    assert any(entry["source"] == ".venv" for entry in manifest["includeAllowlist"])
    assert any(entry["source"] == "docs/operator_package_runtime_note.md" for entry in manifest["includeAllowlist"])
    assert not any(entry["source"] == "README.md" for entry in manifest["includeAllowlist"])
    assert not any(entry["source"] == "docs/27_operator_package_smoke.md" for entry in manifest["includeAllowlist"])
    assert ".git" in manifest["excludeDenylist"]
    assert "tests" in manifest["excludeDenylist"]
    assert "*.csv" in manifest["excludeDenylist"]
    assert "windows-absolute-path-marker" in manifest["redactionChecks"]
    assert "operational-filename-family-marker" in manifest["redactionChecks"]
    assert "credential-like-marker" in manifest["redactionChecks"]
    venv_entry = next(entry for entry in manifest["includeAllowlist"] if entry["source"] == ".venv")
    assert ".agents" in venv_entry["exclude"]
    assert "package and zip .agents entries count is 0" in manifest["smokeChecks"]
    assert manifest["buildMetadata"]["frontendMode"] == "filled-by-assembly"
    assert manifest["buildMetadata"]["frontendBuildInfoPath"] == "frontend/dist/frontend-build-info.json"
    assert "api" in manifest["buildMetadata"]["supportedFrontendModes"]
    assert "mock" in manifest["buildMetadata"]["supportedFrontendModes"]
    assert "X-EWC-Local-Token" not in MANIFEST_PATH.read_text(encoding="utf-8")


def test_frontend_build_scripts_record_mode_metadata() -> None:
    package = json.loads(FRONTEND_PACKAGE_PATH.read_text(encoding="utf-8"))
    scripts = package["scripts"]
    build_script = FRONTEND_BUILD_SCRIPT.read_text(encoding="utf-8")

    assert scripts["build"] == "node scripts/build.mjs mock"
    assert scripts["build:api"] == "node scripts/build.mjs api"
    assert "VITE_API_MODE" in build_script
    assert "frontendMode" in build_script
    assert "frontend-build-info.json" in build_script


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
    assert "frontendmode" in lowered
    assert "frontend-build-info.json" in lowered
    assert "runtimeagentprunedcount" in lowered
    assert "runtime agent entries pruned" in lowered
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
    assert not list(package_root.rglob(".agents"))
    assert not list((package_root / ".venv").rglob(".pytest_cache"))
    assert not any(
        part.lower() in {"test", "tests", "testing", "testsuite"}
        for path in (package_root / ".venv").rglob("*")
        for part in path.relative_to(package_root / ".venv").parts
    )
    assert (package_root / ".venv" / "Lib" / "site-packages" / "demo" / "__init__.py").exists()
    metadata = package_root / ".venv" / "Lib" / "site-packages" / "demo-1.0.0.dist-info"
    assert (metadata / "METADATA").exists()
    assert (metadata / "RECORD").exists()
    assert (metadata / "LICENSE").exists()
    assert "runtime agent entries pruned:" in result.stdout
    assert (package_root / "README.md").read_text(encoding="utf-8") == "# Operator package\n"
    assert (package_root / "docs" / "operator_package_runtime_note.md").exists()
    assert not (package_root / "docs" / "27_operator_package_smoke.md").exists()

    build_info = json.loads((package_root / "package-build-info.json").read_text(encoding="utf-8-sig"))
    assert build_info["runtimeMode"] == "operator-ready"
    assert build_info["frontendMode"] == "mock"
    assert build_info["frontendBuildMetadataPresent"] is True
    assert build_info["frontendBuildInfoPath"] == "frontend/dist/frontend-build-info.json"
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
    assert build_info["frontendMode"] == "mock"
    assert not (package_root / ".venv").exists()


def test_assembly_records_explicit_api_frontend_mode(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    output_root = tmp_path / "out"
    repo_root.mkdir()
    _copy_packaging_files(repo_root)
    _create_minimal_repo(repo_root, frontend_mode="api")

    result = _run_assembly(
        repo_root,
        output_root,
        "-PackageLabel",
        "api-mode-package",
        "-FrontendMode",
        "api",
    )

    assert result.returncode == 0, result.stderr
    package_root = output_root / "api-mode-package" / "ExtrusionWebConsole"
    build_info = json.loads((package_root / "package-build-info.json").read_text(encoding="utf-8-sig"))
    assert build_info["frontendMode"] == "api"
    assert build_info["frontendBuildMetadataPresent"] is True
    assert "frontend mode: api" in result.stdout


def test_assembly_rejects_api_package_with_mock_frontend_dist(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    output_root = tmp_path / "out"
    repo_root.mkdir()
    _copy_packaging_files(repo_root)
    _create_minimal_repo(repo_root, frontend_mode="mock")

    result = _run_assembly(
        repo_root,
        output_root,
        "-PackageLabel",
        "api-mode-mismatch",
        "-FrontendMode",
        "api",
    )

    assert result.returncode != 0
    output = f"{result.stdout}\n{result.stderr}"
    assert "Frontend mode mismatch: expected api but found mock" in output
    assert not (output_root / "api-mode-mismatch").exists()


def test_assembly_rejects_explicit_api_mode_without_frontend_metadata(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    output_root = tmp_path / "out"
    repo_root.mkdir()
    _copy_packaging_files(repo_root)
    _create_minimal_repo(repo_root, include_frontend_metadata=False)

    result = _run_assembly(
        repo_root,
        output_root,
        "-PackageLabel",
        "api-mode-missing-metadata",
        "-FrontendMode",
        "api",
    )

    assert result.returncode != 0
    output = f"{result.stdout}\n{result.stderr}"
    assert "Frontend build metadata is missing" in output
    assert not (output_root / "api-mode-missing-metadata").exists()


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


def test_assembly_rejects_output_root_inside_repo(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _copy_packaging_files(repo_root)
    _create_minimal_repo(repo_root)

    result = _run_assembly(repo_root, repo_root / "package-output", "-PackageLabel", "inside-repo")

    assert result.returncode != 0
    assert "OutputRoot must be outside the repository root" in f"{result.stdout}\n{result.stderr}"
    assert not (repo_root / "package-output").exists()


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
        zipped_build_info = json.loads(
            archive.read("ExtrusionWebConsole/package-build-info.json").decode("utf-8-sig")
        )
    assert "ExtrusionWebConsole/frontend/dist/index.html" in names
    assert not any(name.startswith("ExtrusionWebConsole/tests/") for name in names)
    assert not any(name.endswith(".csv") for name in names)
    assert not any("/.agents/" in name or name.endswith("/.agents") for name in names)
    assert zipped_build_info["zipCreated"] is True
    assert zipped_build_info["zipSha256"] == "see-adjacent-sha256-file"

    build_info = json.loads(
        (output_root / "zip-package" / "ExtrusionWebConsole" / "package-build-info.json").read_text(
            encoding="utf-8-sig"
        )
    )
    assert build_info["zipCreated"] is True
    assert build_info["zipSha256"] == checksum.split()[0]


@pytest.mark.parametrize(
    "marker_class",
    [
        "credential-like-marker",
        "database-url-marker",
        "authorization-bearer-marker",
        "jwt-like-marker",
        "windows-absolute-path-marker",
        "operational-filename-family-marker",
        "timestamp-style-csv-marker",
        "anon-key-assignment-marker",
        "service-role-assignment-marker",
    ],
)
def test_assembly_redaction_blocks_release_marker_class(tmp_path: Path, marker_class: str) -> None:
    repo_root = tmp_path / "repo"
    output_root = tmp_path / "out"
    repo_root.mkdir()
    _copy_packaging_files(repo_root)
    _create_minimal_repo(repo_root)
    (repo_root / "docs" / "operator_package_runtime_note.md").write_text(
        _marker_text(marker_class),
        encoding="utf-8",
    )

    result = _run_assembly(repo_root, output_root, "-PackageLabel", f"redaction-block-{marker_class}")

    assert result.returncode != 0
    output = f"{result.stdout}\n{result.stderr}"
    assert "Package redaction validation failed" in output
    assert marker_class in output


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
