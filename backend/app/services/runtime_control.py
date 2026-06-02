from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from backend.app.core.settings import Settings
from backend.app.db.preview_repository import PreviewRepository
from backend.app.db.runtime_repository import RuntimeRepository
from backend.app.db.upload_job_repository import UploadJobRepository
from backend.app.schemas.runtime import RuntimeOperationDto, RuntimeOperationKind, RuntimeOperationStatus, RuntimeStatusResponse
from backend.app.services.command_runner import REQUIRED_SUPABASE_CONTAINERS, AllowedCommandRunner
from backend.app.services.runtime_readiness import RuntimeReadinessService


class RuntimeConflictError(RuntimeError):
    def __init__(self, reason: str, active_id: str | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.active_id = active_id


class RuntimeControlService:
    def __init__(
        self,
        *,
        settings: Settings,
        runtime_repository: RuntimeRepository,
        preview_repository: PreviewRepository,
        upload_repository: UploadJobRepository,
        runner: AllowedCommandRunner,
    ) -> None:
        self.settings = settings
        self.runtime_repository = runtime_repository
        self.preview_repository = preview_repository
        self.upload_repository = upload_repository
        self.runner = runner
        self.readiness = RuntimeReadinessService(settings, runner)

    def status(self) -> RuntimeStatusResponse:
        active_operation_id = self.runtime_repository.get_active_operation_id()
        active_operation = None
        if active_operation_id:
            row = self.runtime_repository.get_operation(active_operation_id)
            active_operation = operation_dto(row) if row is not None else None
        return self.readiness.check_status(active_operation=active_operation)

    def queue_operation(self, kind: RuntimeOperationKind) -> str:
        self._ensure_mutation_allowed(kind)
        operation_id = f"rt_{uuid4().hex[:12]}"
        self.runtime_repository.create_operation(
            operation_id,
            kind=kind.value,
            config_snapshot={
                "projectPath": self.settings.local_supabase_project_path,
                "apiPort": self.settings.local_supabase_api_port,
                "dbPort": self.settings.local_supabase_db_port,
                "studioPort": self.settings.local_supabase_studio_port,
                "edgeContainer": self.settings.local_supabase_edge_container,
            },
        )
        return operation_id

    def run_operation(self, operation_id: str) -> None:
        row = self.runtime_repository.get_operation(operation_id)
        if row is None:
            return
        kind = RuntimeOperationKind(row["kind"])
        self.runtime_repository.mark_running(operation_id)
        try:
            if kind == RuntimeOperationKind.start:
                self._run_start(operation_id)
            else:
                self._run_stop(operation_id)
        except Exception as exc:  # noqa: BLE001 - background failures must be visible.
            self.runtime_repository.append_event(
                operation_id,
                event_type="runtime.operation.exception",
                level="error",
                message=str(exc),
                data={"errorCode": "runtime_operation_exception"},
            )
            self.runtime_repository.finish_operation(
                operation_id,
                status=RuntimeOperationStatus.failed.value,
                error_code="runtime_operation_exception",
                error_message=str(exc),
            )
            self.runtime_repository.append_audit(
                action=f"runtime.{kind.value}",
                target_type="runtime_operation",
                target_id=operation_id,
                params={},
                result="failure",
                error_code="runtime_operation_exception",
                error_message=str(exc),
            )

    def _ensure_mutation_allowed(self, kind: RuntimeOperationKind) -> None:
        active_runtime = self.runtime_repository.get_active_operation_id()
        if active_runtime:
            self._audit_blocked(kind, "active_runtime_operation", active_runtime)
            raise RuntimeConflictError("active_runtime_operation", active_runtime)
        active_upload = self.upload_repository.get_active_job_id()
        if active_upload:
            self._audit_blocked(kind, "active_upload_job", active_upload)
            raise RuntimeConflictError("active_upload_job", active_upload)
        active_preview = self.preview_repository.has_active_run()
        if active_preview:
            self._audit_blocked(kind, "active_preview_run", active_preview)
            raise RuntimeConflictError("active_preview_run", active_preview)

    def _audit_blocked(self, kind: RuntimeOperationKind, reason: str, active_id: str | None) -> None:
        self.runtime_repository.append_audit(
            action=f"runtime.{kind.value}",
            target_type="local_supabase",
            target_id=self.settings.local_supabase_project_id,
            params={"activeId": active_id},
            result="blocked",
            error_code=reason,
            error_message=reason,
        )

    def _run_start(self, operation_id: str) -> None:
        ready, missing, containers = self.readiness.required_containers_exist()
        if not ready:
            error_code = "required_container_missing" if missing else "docker_unavailable"
            message = "Required local Supabase containers are missing." if missing else "Docker is unavailable."
            self.runtime_repository.append_event(
                operation_id,
                event_type=f"runtime.start.{error_code}",
                level="error",
                message=message,
                data={"missingContainers": missing},
            )
            self.runtime_repository.finish_operation(operation_id, status=RuntimeOperationStatus.blocked.value, error_code=error_code, error_message=message)
            self.runtime_repository.append_audit(
                action="runtime.start",
                target_type="local_supabase",
                target_id=self.settings.local_supabase_project_id,
                params={"missingContainers": missing},
                result="blocked",
                error_code=error_code,
                error_message=message,
            )
            return

        stopped = [container.name for container in containers if container.exists and not container.running]
        if stopped:
            self.runtime_repository.append_event(
                operation_id,
                event_type="runtime.start.containers",
                level="info",
                message="Starting stopped local Supabase containers.",
                data={"containers": stopped},
            )
            for container_name in stopped:
                result = self.runner.run(["docker", "start", container_name], timeout_seconds=self.settings.runtime_command_timeout_seconds)
                if not result.ok:
                    self._finish_command_failure(operation_id, "runtime.start", "docker_start_failed", result.stderr or result.stdout)
                    return
        else:
            result = self.runner.run(
                ["supabase", "start"],
                timeout_seconds=self.settings.runtime_command_timeout_seconds,
                required_containers_verified=True,
            )
            if not result.ok:
                self._finish_command_failure(operation_id, "runtime.start", "supabase_start_failed", result.stderr or result.stdout)
                return

        self._wait_for_readiness(operation_id, action="runtime.start", expect_running=True)

    def _run_stop(self, operation_id: str) -> None:
        status = self.readiness.check_status()
        running = [container.name for container in status.containers if container.exists and container.running]
        if not running:
            self.runtime_repository.append_event(operation_id, event_type="runtime.stop.noop", level="info", message="Local Supabase containers are already stopped.")
            self._finish_success(operation_id, "runtime.stop")
            return
        for container_name in reversed(list(REQUIRED_SUPABASE_CONTAINERS)):
            if container_name not in running:
                continue
            result = self.runner.run(["docker", "stop", container_name], timeout_seconds=self.settings.runtime_command_timeout_seconds)
            if not result.ok:
                self._finish_command_failure(operation_id, "runtime.stop", "docker_stop_failed", result.stderr or result.stdout)
                return
        self._wait_for_readiness(operation_id, action="runtime.stop", expect_running=False)

    def _wait_for_readiness(self, operation_id: str, *, action: str, expect_running: bool) -> None:
        deadline = time.monotonic() + self.settings.runtime_readiness_timeout_seconds
        while time.monotonic() < deadline:
            status = self.readiness.check_status()
            if expect_running and status.api.status.value == "ready" and status.db.status.value == "ready":
                self._finish_success(operation_id, action)
                return
            if not expect_running and status.api.status.value != "ready" and status.db.status.value != "ready":
                self._finish_success(operation_id, action)
                return
            time.sleep(1)
        self.runtime_repository.finish_operation(
            operation_id,
            status=RuntimeOperationStatus.timed_out.value,
            error_code="readiness_timeout",
            error_message="Runtime readiness did not reach the expected state in time.",
        )
        self.runtime_repository.append_audit(
            action=action,
            target_type="local_supabase",
            target_id=self.settings.local_supabase_project_id,
            params={},
            result="failure",
            error_code="readiness_timeout",
            error_message="Runtime readiness did not reach the expected state in time.",
        )

    def _finish_success(self, operation_id: str, action: str) -> None:
        self.runtime_repository.finish_operation(operation_id, status=RuntimeOperationStatus.succeeded.value)
        self.runtime_repository.append_audit(
            action=action,
            target_type="local_supabase",
            target_id=self.settings.local_supabase_project_id,
            params={},
            result="success",
        )

    def _finish_command_failure(self, operation_id: str, action: str, error_code: str, message: str) -> None:
        self.runtime_repository.finish_operation(operation_id, status=RuntimeOperationStatus.failed.value, error_code=error_code, error_message=message)
        self.runtime_repository.append_audit(
            action=action,
            target_type="local_supabase",
            target_id=self.settings.local_supabase_project_id,
            params={},
            result="failure",
            error_code=error_code,
            error_message=message,
        )


def operation_dto(row: Any) -> RuntimeOperationDto:
    return RuntimeOperationDto(
        operation_id=row["operation_id"],
        kind=RuntimeOperationKind(row["kind"]),
        status=RuntimeOperationStatus(row["status"]),
        requested_at=row_dt(row["requested_at"]),
        started_at=row_dt(row["started_at"]),
        finished_at=row_dt(row["finished_at"]),
        actor=row["actor"],
        error_code=row["error_code"],
        error_message=row["error_message"],
    )


def row_dt(value: str | None):
    from datetime import datetime

    return None if value is None else datetime.fromisoformat(value)
