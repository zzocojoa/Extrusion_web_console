from pathlib import Path
from typing import Sequence

from backend.app.core.settings import Settings
from backend.app.db.preview_repository import PreviewRepository
from backend.app.db.runtime_repository import RuntimeRepository
from backend.app.db.upload_job_repository import UploadJobRepository
from backend.app.schemas.runtime import RuntimeOperationKind
from backend.app.services.command_runner import CommandResult
from backend.app.services.runtime_control import RuntimeConflictError, RuntimeControlService


class FakeRunner:
    def __init__(self, docker_ps_output: str = "") -> None:
        self.docker_ps_output = docker_ps_output
        self.commands: list[tuple[str, ...]] = []

    def run(self, args: Sequence[str], *, timeout_seconds: int | None = None, required_containers_verified: bool = False) -> CommandResult:
        command = tuple(args)
        self.commands.append(command)
        if command == ("docker", "version", "--format", "{{json .}}"):
            return CommandResult(command, 0, "docker ok", "")
        if command == ("docker", "ps", "-a", "--format", "{{json .}}"):
            return CommandResult(command, 0, self.docker_ps_output, "")
        if command == ("wsl", "-l", "-v"):
            return CommandResult(command, 0, "Ubuntu Running", "")
        if command == ("supabase", "--version"):
            return CommandResult(command, 0, "2.0.0", "")
        return CommandResult(command, 0, "ok", "")


def settings(tmp_path: Path) -> Settings:
    project_path = tmp_path / "Extrusion_data"
    project_path.mkdir()
    return Settings(
        state_db_path=str(tmp_path / "state.db"),
        local_supabase_project_path=str(project_path),
        supabase_edge_url="",
        runtime_readiness_timeout_seconds=1,
    )


def test_start_blocks_when_required_container_missing_and_never_runs_supabase_start(tmp_path: Path) -> None:
    app_settings = settings(tmp_path)
    runtime = RuntimeRepository(app_settings.state_db_path)
    service = RuntimeControlService(
        settings=app_settings,
        runtime_repository=runtime,
        preview_repository=PreviewRepository(app_settings.state_db_path),
        upload_repository=UploadJobRepository(app_settings.state_db_path),
        runner=FakeRunner(docker_ps_output=""),
    )
    operation_id = service.queue_operation(RuntimeOperationKind.start)

    service.run_operation(operation_id)

    row = runtime.get_operation(operation_id)
    assert row is not None
    assert row["status"] == "blocked"
    assert row["error_code"] == "required_container_missing"
    assert ("supabase", "start") not in service.runner.commands  # type: ignore[attr-defined]
    audit = latest_audit(runtime)
    assert audit["action"] == "runtime.start"
    assert audit["result"] == "blocked"
    assert audit["error_code"] == "required_container_missing"


def test_mutating_operation_blocks_during_active_preview_and_writes_audit(tmp_path: Path) -> None:
    app_settings = settings(tmp_path)
    preview = PreviewRepository(app_settings.state_db_path)
    preview.create_run(
        preview_run_id="prv_active",
        range_mode="today",
        start_date=None,
        end_date=None,
        sources=["plc"],
        options={},
        config_snapshot={},
        retry_of_run_id=None,
    )
    runtime = RuntimeRepository(app_settings.state_db_path)
    service = RuntimeControlService(
        settings=app_settings,
        runtime_repository=runtime,
        preview_repository=preview,
        upload_repository=UploadJobRepository(app_settings.state_db_path),
        runner=FakeRunner(),
    )

    try:
        service.queue_operation(RuntimeOperationKind.stop)
    except RuntimeConflictError as exc:
        assert exc.reason == "active_preview_run"
    else:
        raise AssertionError("Expected active preview conflict")

    audit = latest_audit(runtime)
    assert audit["action"] == "runtime.stop"
    assert audit["result"] == "blocked"
    assert audit["error_code"] == "active_preview_run"


def test_passive_status_success_does_not_write_audit(tmp_path: Path) -> None:
    app_settings = settings(tmp_path)
    runtime = RuntimeRepository(app_settings.state_db_path)
    service = RuntimeControlService(
        settings=app_settings,
        runtime_repository=runtime,
        preview_repository=PreviewRepository(app_settings.state_db_path),
        upload_repository=UploadJobRepository(app_settings.state_db_path),
        runner=FakeRunner(),
    )

    service.status()

    with runtime.connect() as connection:
        row = connection.execute("SELECT COUNT(*) AS count FROM audit_log").fetchone()
    assert row["count"] == 0


def latest_audit(repository: RuntimeRepository):
    with repository.connect() as connection:
        return connection.execute("SELECT * FROM audit_log ORDER BY audit_id DESC LIMIT 1").fetchone()
