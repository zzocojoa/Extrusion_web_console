from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Sequence

import pytest

from backend.app.core.settings import Settings
from backend.app.db.preview_repository import PreviewRepository, iso_now
from backend.app.db.runtime_repository import RuntimeRepository
from backend.app.db.upload_job_repository import UploadJobRepository
from backend.app.schemas.runtime import (
    RuntimeOperationKind,
    RuntimeOverallStatus,
    RuntimePortStatus,
    RuntimeProbeStatus,
    RuntimeServiceStatus,
    RuntimeStatusResponse,
)
from backend.app.services.command_runner import required_supabase_containers
from backend.app.services.command_runner import CommandResult
from backend.app.services.runtime_control import RuntimeConflictError, RuntimeControlService


class FakeRunner:
    def __init__(self, docker_ps_output: str = "", *, project_id: str = "Extrusion_web_console") -> None:
        self.docker_ps_output = docker_ps_output
        self.commands: list[tuple[str, ...]] = []
        self.project_id = project_id
        self.required_supabase_containers = required_supabase_containers(project_id)

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
    project_path = tmp_path / "Extrusion_web_console"
    write_supabase_config(project_path)
    return Settings(
        state_db_path=str(tmp_path / "state.db"),
        local_supabase_project_path=str(project_path),
        local_supabase_wsl_path="/mnt/c/tmp/Extrusion_web_console",
        supabase_edge_url="",
        runtime_readiness_timeout_seconds=1,
    )


def write_supabase_config(project_path: Path, *, api_port: int = 55321, db_port: int = 25433, studio_port: int = 55323) -> None:
    supabase_path = project_path / "supabase"
    supabase_path.mkdir(parents=True)
    (supabase_path / "config.toml").write_text(
        f"""
[api]
enabled = true
port = {api_port}

[db]
port = {db_port}

[studio]
enabled = true
port = {studio_port}
""",
        encoding="utf-8",
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


def test_mutating_operation_blocks_during_active_upload_and_writes_audit(tmp_path: Path) -> None:
    app_settings = settings(tmp_path)
    runtime = RuntimeRepository(app_settings.state_db_path)
    preview = PreviewRepository(app_settings.state_db_path)
    upload = UploadJobRepository(app_settings.state_db_path)
    now = iso_now()
    with upload.connect() as connection:
        connection.execute(
            """
            INSERT INTO upload_jobs(
              job_id, mode, status, requested_at, actor, options_json, config_snapshot_json, created_at, updated_at
            )
            VALUES ('upl_active', 'preview_targets', 'queued', ?, 'local_operator', '{}', '{}', ?, ?)
            """,
            (now, now, now),
        )
    service = RuntimeControlService(
        settings=app_settings,
        runtime_repository=runtime,
        preview_repository=preview,
        upload_repository=upload,
        runner=FakeRunner(),
    )

    try:
        service.queue_operation(RuntimeOperationKind.start)
    except RuntimeConflictError as exc:
        assert exc.reason == "active_upload_job"
        assert exc.active_id == "upl_active"
    else:
        raise AssertionError("Expected active upload conflict")

    audit = latest_audit(runtime)
    assert audit["action"] == "runtime.start"
    assert audit["result"] == "blocked"
    assert audit["error_code"] == "active_upload_job"


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


def test_default_edge_url_uses_local_supabase_api_port() -> None:
    app_settings = Settings(supabase_edge_url="", supabase_url="", local_supabase_api_port=55321)

    assert app_settings.upload_edge_url == "http://127.0.0.1:55321/functions/v1/upload-metrics"


def test_status_blocks_when_config_ports_do_not_match(tmp_path: Path) -> None:
    project_path = tmp_path / "Extrusion_web_console"
    write_supabase_config(project_path, api_port=54322)
    app_settings = Settings(
        state_db_path=str(tmp_path / "state.db"),
        local_supabase_project_path=str(project_path),
        supabase_edge_url="",
        runtime_readiness_timeout_seconds=1,
    )
    service = RuntimeControlService(
        settings=app_settings,
        runtime_repository=RuntimeRepository(app_settings.state_db_path),
        preview_repository=PreviewRepository(app_settings.state_db_path),
        upload_repository=UploadJobRepository(app_settings.state_db_path),
        runner=FakeRunner(docker_ps_output=all_containers_output(running=True)),
    )

    status = service.status()

    assert status.overall_status == RuntimeOverallStatus.blocked
    assert status.reason_code == "config_port_mismatch"


def test_stop_with_docker_unavailable_fails_instead_of_noop_success(tmp_path: Path) -> None:
    app_settings = settings(tmp_path)
    runtime = RuntimeRepository(app_settings.state_db_path)
    service = RuntimeControlService(
        settings=app_settings,
        runtime_repository=runtime,
        preview_repository=PreviewRepository(app_settings.state_db_path),
        upload_repository=UploadJobRepository(app_settings.state_db_path),
        runner=FakeRunner(),
    )
    service.readiness = StaticReadiness(runtime_status(docker=RuntimeServiceStatus.unreachable))  # type: ignore[assignment]
    operation_id = service.queue_operation(RuntimeOperationKind.stop)

    service.run_operation(operation_id)

    row = runtime.get_operation(operation_id)
    assert row is not None
    assert row["status"] == "failed"
    assert row["error_code"] == "docker_unavailable"
    audit = latest_audit(runtime)
    assert audit["action"] == "runtime.stop"
    assert audit["result"] == "failure"
    assert audit["error_code"] == "docker_unavailable"


def test_start_noops_when_runtime_core_is_already_ready(tmp_path: Path) -> None:
    app_settings = settings(tmp_path)
    runtime = RuntimeRepository(app_settings.state_db_path)
    service = RuntimeControlService(
        settings=app_settings,
        runtime_repository=runtime,
        preview_repository=PreviewRepository(app_settings.state_db_path),
        upload_repository=UploadJobRepository(app_settings.state_db_path),
        runner=FakeRunner(docker_ps_output=all_containers_output(running=True)),
    )
    service.readiness = StaticReadiness(
        runtime_status(
            api=RuntimeServiceStatus.ready,
            db=RuntimeServiceStatus.ready,
            studio=RuntimeServiceStatus.ready,
            edge=RuntimeServiceStatus.ready,
        ),
        required_ready=True,
    )  # type: ignore[assignment]
    operation_id = service.queue_operation(RuntimeOperationKind.start)

    service.run_operation(operation_id)

    row = runtime.get_operation(operation_id)
    assert row is not None
    assert row["status"] == "succeeded"
    assert ("supabase", "start") not in service.runner.commands  # type: ignore[attr-defined]
    assert not any(command[:2] == ("docker", "start") for command in service.runner.commands)  # type: ignore[attr-defined]


@pytest.mark.parametrize("failed_probe", ["api", "db", "studio", "edge"])
def test_start_readiness_requires_api_db_studio_and_edge(tmp_path: Path, monkeypatch, failed_probe: str) -> None:
    app_settings = settings(tmp_path)
    runtime = RuntimeRepository(app_settings.state_db_path)
    service = RuntimeControlService(
        settings=app_settings,
        runtime_repository=runtime,
        preview_repository=PreviewRepository(app_settings.state_db_path),
        upload_repository=UploadJobRepository(app_settings.state_db_path),
        runner=FakeRunner(docker_ps_output=all_containers_output(running=True)),
    )
    service.readiness = StaticReadiness(
        runtime_status(
            api=RuntimeServiceStatus.unreachable if failed_probe == "api" else RuntimeServiceStatus.ready,
            db=RuntimeServiceStatus.unreachable if failed_probe == "db" else RuntimeServiceStatus.ready,
            studio=RuntimeServiceStatus.unreachable if failed_probe == "studio" else RuntimeServiceStatus.ready,
            edge=RuntimeServiceStatus.unreachable if failed_probe == "edge" else RuntimeServiceStatus.ready,
        ),
        required_ready=True,
    )  # type: ignore[assignment]
    monotonic_values = iter([0.0, 0.5, 2.0])
    monkeypatch.setattr("backend.app.services.runtime_control.time.monotonic", lambda: next(monotonic_values))
    monkeypatch.setattr("backend.app.services.runtime_control.time.sleep", lambda _: None)
    operation_id = service.queue_operation(RuntimeOperationKind.start)

    service.run_operation(operation_id)

    row = runtime.get_operation(operation_id)
    assert row is not None
    assert row["status"] == "timed_out"
    assert row["error_code"] == "readiness_timeout"
    audit = latest_audit(runtime)
    assert audit["action"] == "runtime.start"
    assert audit["result"] == "failure"


def test_stop_readiness_requires_api_db_and_studio_to_close(tmp_path: Path, monkeypatch) -> None:
    app_settings = settings(tmp_path)
    runtime = RuntimeRepository(app_settings.state_db_path)
    service = RuntimeControlService(
        settings=app_settings,
        runtime_repository=runtime,
        preview_repository=PreviewRepository(app_settings.state_db_path),
        upload_repository=UploadJobRepository(app_settings.state_db_path),
        runner=FakeRunner(),
    )
    service.readiness = SequenceReadiness(
        [
            runtime_status(
                api=RuntimeServiceStatus.ready,
                db=RuntimeServiceStatus.ready,
                studio=RuntimeServiceStatus.ready,
                edge=RuntimeServiceStatus.ready,
            ),
            runtime_status(
                api=RuntimeServiceStatus.unreachable,
                db=RuntimeServiceStatus.unreachable,
                studio=RuntimeServiceStatus.ready,
                edge=RuntimeServiceStatus.unreachable,
            ),
        ],
        required_ready=True,
    )  # type: ignore[assignment]
    monotonic_values = iter([0.0, 0.5, 2.0])
    monkeypatch.setattr("backend.app.services.runtime_control.time.monotonic", lambda: next(monotonic_values))
    monkeypatch.setattr("backend.app.services.runtime_control.time.sleep", lambda _: None)
    operation_id = service.queue_operation(RuntimeOperationKind.stop)

    service.run_operation(operation_id)

    row = runtime.get_operation(operation_id)
    assert row is not None
    assert row["status"] == "timed_out"
    assert row["error_code"] == "readiness_timeout"


def test_runtime_operation_enqueue_is_atomic_for_concurrent_requests(tmp_path: Path) -> None:
    app_settings = settings(tmp_path)
    runtime = RuntimeRepository(app_settings.state_db_path)
    preview = PreviewRepository(app_settings.state_db_path)
    upload = UploadJobRepository(app_settings.state_db_path)

    def queue() -> str:
        service = RuntimeControlService(
            settings=app_settings,
            runtime_repository=runtime,
            preview_repository=preview,
            upload_repository=upload,
            runner=FakeRunner(),
        )
        return service.queue_operation(RuntimeOperationKind.start)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(queue), executor.submit(queue)]

    operation_ids: list[str] = []
    conflicts: list[str] = []
    for future in futures:
        try:
            operation_ids.append(future.result())
        except RuntimeConflictError as exc:
            conflicts.append(exc.reason)

    assert len(operation_ids) == 1
    assert conflicts == ["active_runtime_operation"]
    with runtime.connect() as connection:
        row = connection.execute("SELECT COUNT(*) AS count FROM runtime_operations WHERE status = 'queued'").fetchone()
    assert row["count"] == 1


def latest_audit(repository: RuntimeRepository):
    with repository.connect() as connection:
        return connection.execute("SELECT * FROM audit_log ORDER BY audit_id DESC LIMIT 1").fetchone()


class StaticReadiness:
    def __init__(self, status: RuntimeStatusResponse, *, required_ready: bool = False) -> None:
        self._status = status
        self._required_ready = required_ready

    def check_status(self, *, active_operation=None):
        return self._status

    def required_containers_exist(self):
        return self._required_ready, [], self._status.containers


class SequenceReadiness:
    def __init__(self, statuses: list[RuntimeStatusResponse], *, required_ready: bool = False) -> None:
        self._statuses = statuses
        self._index = 0
        self._required_ready = required_ready

    def check_status(self, *, active_operation=None):
        status = self._statuses[min(self._index, len(self._statuses) - 1)]
        self._index += 1
        return status

    def required_containers_exist(self):
        status = self._statuses[0]
        return self._required_ready, [], status.containers


def runtime_status(
    *,
    docker: RuntimeServiceStatus = RuntimeServiceStatus.ready,
    api: RuntimeServiceStatus = RuntimeServiceStatus.unreachable,
    db: RuntimeServiceStatus = RuntimeServiceStatus.unreachable,
    studio: RuntimeServiceStatus = RuntimeServiceStatus.unreachable,
    edge: RuntimeServiceStatus = RuntimeServiceStatus.unreachable,
) -> RuntimeStatusResponse:
    from datetime import datetime, timezone

    return RuntimeStatusResponse(
        overall_status=RuntimeOverallStatus.blocked,
        reason_code="test",
        reason_text="test",
        checked_at=datetime.now(timezone.utc),
        project_path="C:\\tmp\\Extrusion_web_console",
        project_id="Extrusion_web_console",
        docker=RuntimeProbeStatus(name="Docker", status=docker, detail="test"),
        wsl=RuntimeProbeStatus(name="WSL", status=RuntimeServiceStatus.ready, detail="test"),
        supabase_cli=RuntimeProbeStatus(name="Supabase CLI", status=RuntimeServiceStatus.ready, detail="test"),
        api=RuntimePortStatus(name="Supabase API", port=55321, status=api, detail="test"),
        db=RuntimePortStatus(name="Supabase DB", port=25433, status=db, detail="test"),
        studio=RuntimePortStatus(name="Supabase Studio", port=55323, status=studio, detail="test"),
        edge_runtime=RuntimeProbeStatus(name="Edge Function", status=edge, detail="test"),
        grafana=RuntimeProbeStatus(name="Grafana", status=RuntimeServiceStatus.unreachable, detail="test"),
        containers=[
            container_status(name, running=docker == RuntimeServiceStatus.ready)
            for name in required_supabase_containers("Extrusion_web_console")
        ],
        config=[],
    )


def container_status(name: str, *, running: bool):
    from backend.app.schemas.runtime import RuntimeContainerStatus

    return RuntimeContainerStatus(
        name=name,
        required=True,
        exists=True,
        running=running,
        status=RuntimeServiceStatus.ready if running else RuntimeServiceStatus.stopped,
        status_text="Up" if running else "Exited",
    )


def all_containers_output(*, running: bool) -> str:
    status = "Up 10 seconds" if running else "Exited (0)"
    return "\n".join(f'{{"Names":"{name}","Status":"{status}"}}' for name in required_supabase_containers("Extrusion_web_console"))
