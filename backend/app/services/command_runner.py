from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

REQUIRED_SUPABASE_CONTAINERS = (
    "supabase_db_Extrusion_data",
    "supabase_kong_Extrusion_data",
    "supabase_auth_Extrusion_data",
    "supabase_rest_Extrusion_data",
    "supabase_realtime_Extrusion_data",
    "supabase_storage_Extrusion_data",
    "supabase_imgproxy_Extrusion_data",
    "supabase_meta_Extrusion_data",
    "supabase_studio_Extrusion_data",
    "supabase_inbucket_Extrusion_data",
    "supabase_edge_runtime_Extrusion_data",
    "supabase_analytics_Extrusion_data",
    "supabase_vector_Extrusion_data",
)

OPTIONAL_RUNTIME_CONTAINERS = ("grafana_local",)
ALLOWED_CONTAINERS = set(REQUIRED_SUPABASE_CONTAINERS).union(OPTIONAL_RUNTIME_CONTAINERS)

FORBIDDEN_WORDS = {
    "init",
    "reset",
    "run",
    "create",
    "rm",
    "rmi",
    "volume",
    "prune",
    "up",
    "down",
}


@dataclass(frozen=True)
class CommandResult:
    args: tuple[str, ...]
    return_code: int
    stdout: str
    stderr: str
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        return self.return_code == 0 and not self.timed_out


class CommandPolicyError(ValueError):
    pass


def redact_command_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        value = value.decode(errors="replace")
    value = re.sub(r"(?i)(authorization:\s*bearer\s+)[^\s]+", r"\1[redacted]", value)
    value = re.sub(r"(?i)(anon[_-]?key['\"]?\s*[:=]\s*['\"]?)[A-Za-z0-9._-]+", r"\1[redacted]", value)
    value = re.sub(r"eyJ[A-Za-z0-9._-]{20,}", "[redacted-jwt]", value)
    return value


class AllowedCommandRunner:
    def __init__(self, project_path: str, default_timeout_seconds: int = 20) -> None:
        self.project_path = Path(project_path)
        self.default_timeout_seconds = default_timeout_seconds

    def validate(self, args: Sequence[str], *, required_containers_verified: bool = False) -> tuple[str, ...]:
        command = tuple(str(arg) for arg in args)
        if not command:
            raise CommandPolicyError("empty_command")
        if any(not part or any(token in part for token in ("&&", "||", ";", "|", "`", "$(", ">", "<")) for part in command):
            raise CommandPolicyError("shell_syntax_not_allowed")
        if command[0] == "supabase":
            return self._validate_supabase(command, required_containers_verified=required_containers_verified)
        if command[0] == "docker":
            return self._validate_docker(command)
        if command[0] == "wsl":
            if command == ("wsl", "-l", "-v"):
                return command
            raise CommandPolicyError("wsl_command_not_allowed")
        raise CommandPolicyError("command_not_allowed")

    def run(
        self,
        args: Sequence[str],
        *,
        timeout_seconds: int | None = None,
        required_containers_verified: bool = False,
    ) -> CommandResult:
        command = self.validate(args, required_containers_verified=required_containers_verified)
        timeout = timeout_seconds or self.default_timeout_seconds
        try:
            completed = subprocess.run(
                command,
                cwd=str(self.project_path) if command[0] == "supabase" else None,
                shell=False,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            return CommandResult(
                args=command,
                return_code=completed.returncode,
                stdout=redact_command_output(completed.stdout),
                stderr=redact_command_output(completed.stderr),
            )
        except subprocess.TimeoutExpired as exc:
            return CommandResult(
                args=command,
                return_code=124,
                stdout=redact_command_output(exc.stdout or ""),
                stderr=redact_command_output(exc.stderr or "Command timed out."),
                timed_out=True,
            )
        except OSError as exc:
            return CommandResult(args=command, return_code=127, stdout="", stderr=str(exc))

    def _validate_supabase(self, command: tuple[str, ...], *, required_containers_verified: bool) -> tuple[str, ...]:
        if command == ("supabase", "--version"):
            return command
        if command == ("supabase", "start"):
            if not required_containers_verified:
                raise CommandPolicyError("required_container_precheck_missing")
            return command
        if any(word in FORBIDDEN_WORDS for word in command[1:]):
            raise CommandPolicyError("supabase_command_forbidden")
        raise CommandPolicyError("supabase_command_not_allowed")

    def _validate_docker(self, command: tuple[str, ...]) -> tuple[str, ...]:
        if command in {
            ("docker", "version", "--format", "{{json .}}"),
            ("docker", "ps", "--format", "{{json .}}"),
            ("docker", "ps", "-a", "--format", "{{json .}}"),
        }:
            return command
        if len(command) == 3 and command[1] in {"start", "stop"}:
            if command[2] not in ALLOWED_CONTAINERS:
                raise CommandPolicyError("container_not_allowed")
            return command
        if len(command) == 5 and command[1] == "inspect" and command[2] in ALLOWED_CONTAINERS and command[3] == "--format":
            allowed_formats = {"{{json .State}}", "{{.State.Status}}", "{{.State.Health.Status}}"}
            if command[4] in allowed_formats:
                return command
        if len(command) > 1 and command[1] in FORBIDDEN_WORDS:
            raise CommandPolicyError("docker_command_forbidden")
        if len(command) > 2 and command[1] == "compose" and command[2] in {"up", "down", "rm"}:
            raise CommandPolicyError("docker_compose_command_forbidden")
        raise CommandPolicyError("docker_command_not_allowed")
