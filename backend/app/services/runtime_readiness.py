from __future__ import annotations

import json
import os
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from backend.app.core.settings import Settings
from backend.app.schemas.runtime import (
    RuntimeConfigItem,
    RuntimeContainerStatus,
    RuntimeOverallStatus,
    RuntimePortStatus,
    RuntimeProbeStatus,
    RuntimeServiceStatus,
    RuntimeStatusResponse,
)
from backend.app.services.command_runner import AllowedCommandRunner, CommandResult, REQUIRED_SUPABASE_CONTAINERS


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def port_status(name: str, port: int, *, timeout_seconds: float = 0.25) -> RuntimePortStatus:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=timeout_seconds):
            return RuntimePortStatus(name=name, port=port, status=RuntimeServiceStatus.ready, detail="Port is accepting connections.")
    except OSError as exc:
        return RuntimePortStatus(name=name, port=port, status=RuntimeServiceStatus.unreachable, detail=str(exc))


def probe_edge_route(url: str, *, timeout_seconds: float = 2.0) -> RuntimeProbeStatus:
    if not url:
        return RuntimeProbeStatus(name="Edge Function", status=RuntimeServiceStatus.unknown, detail="Edge URL is not configured.")
    try:
        response = httpx.post(url, json={}, timeout=timeout_seconds)
    except httpx.TimeoutException:
        return RuntimeProbeStatus(name="Edge Function", status=RuntimeServiceStatus.unreachable, detail="Edge route probe timed out.", url=url)
    except httpx.HTTPError as exc:
        return RuntimeProbeStatus(name="Edge Function", status=RuntimeServiceStatus.unreachable, detail=str(exc), url=url)

    body = response.text[:300]
    if response.status_code in {200, 201, 400, 401, 403, 422}:
        lowered = body.lower()
        if response.status_code in {401, 403} or "missing authorization" in lowered or "validation" in lowered:
            return RuntimeProbeStatus(name="Edge Function", status=RuntimeServiceStatus.ready, detail="Edge route is reachable.", url=url)
        if response.status_code in {400, 422}:
            return RuntimeProbeStatus(name="Edge Function", status=RuntimeServiceStatus.ready, detail="Edge route returned payload validation error.", url=url)
        return RuntimeProbeStatus(name="Edge Function", status=RuntimeServiceStatus.ready, detail="Edge route responded.", url=url)
    return RuntimeProbeStatus(
        name="Edge Function",
        status=RuntimeServiceStatus.unhealthy,
        detail=f"Edge route returned HTTP {response.status_code}.",
        url=url,
    )


class RuntimeReadinessService:
    def __init__(self, settings: Settings, runner: AllowedCommandRunner) -> None:
        self.settings = settings
        self.runner = runner

    def check_status(self, *, active_operation: Any | None = None) -> RuntimeStatusResponse:
        project_path = Path(self.settings.local_supabase_project_path)
        docker_result = self.runner.run(["docker", "version", "--format", "{{json .}}"], timeout_seconds=5)
        docker_status = self._probe_from_result("Docker", docker_result)
        wsl_status = self._probe_from_result("WSL", self.runner.run(["wsl", "-l", "-v"], timeout_seconds=5))
        cli_status = self._probe_from_result("Supabase CLI", self.runner.run(["supabase", "--version"], timeout_seconds=5))
        containers = self._container_statuses(docker_status)
        api = port_status("Supabase API", self.settings.local_supabase_api_port)
        db = port_status("Supabase DB", self.settings.local_supabase_db_port)
        studio = port_status("Supabase Studio", self.settings.local_supabase_studio_port)
        edge = probe_edge_route(self.settings.upload_edge_url, timeout_seconds=2.0)
        grafana = self._probe_grafana()

        missing_required = [container.name for container in containers if container.required and not container.exists]
        if active_operation is not None:
            overall = RuntimeOverallStatus.running
            reason_code = "runtime_operation_active"
            reason_text = "A local Supabase runtime operation is in progress."
        elif not project_path.exists():
            overall = RuntimeOverallStatus.blocked
            reason_code = "project_path_missing"
            reason_text = "The configured Extrusion_data project path does not exist."
        elif docker_status.status != RuntimeServiceStatus.ready:
            overall = RuntimeOverallStatus.blocked
            reason_code = "docker_unavailable"
            reason_text = "Docker is not reachable from the backend process."
        elif missing_required:
            overall = RuntimeOverallStatus.blocked
            reason_code = "required_container_missing"
            reason_text = "Required local Supabase containers are missing. v1 does not create a new stack."
        elif api.status != RuntimeServiceStatus.ready or db.status != RuntimeServiceStatus.ready:
            overall = RuntimeOverallStatus.blocked
            reason_code = "core_port_unreachable"
            reason_text = "Supabase API or DB port is not reachable."
        elif edge.status != RuntimeServiceStatus.ready or studio.status != RuntimeServiceStatus.ready or grafana.status != RuntimeServiceStatus.ready:
            overall = RuntimeOverallStatus.attention
            reason_code = "non_core_runtime_attention"
            reason_text = "Core DB/API is reachable, but Studio, Edge, or Grafana needs attention."
        else:
            overall = RuntimeOverallStatus.ready
            reason_code = "runtime_ready"
            reason_text = "Local Supabase runtime is ready."

        return RuntimeStatusResponse(
            overall_status=overall,
            reason_code=reason_code,
            reason_text=reason_text,
            checked_at=now_utc(),
            project_path=str(project_path),
            project_id=self.settings.local_supabase_project_id,
            docker=docker_status,
            wsl=wsl_status,
            supabase_cli=cli_status,
            api=api,
            db=db,
            studio=studio,
            edge_runtime=edge,
            grafana=grafana,
            containers=containers,
            config=self._config_items(),
            active_operation=active_operation,
        )

    def required_containers_exist(self) -> tuple[bool, list[str], list[RuntimeContainerStatus]]:
        docker_status = self._probe_from_result("Docker", self.runner.run(["docker", "version", "--format", "{{json .}}"], timeout_seconds=5))
        containers = self._container_statuses(docker_status)
        missing = [container.name for container in containers if container.required and not container.exists]
        return not missing and docker_status.status == RuntimeServiceStatus.ready, missing, containers

    def _probe_from_result(self, name: str, result: CommandResult) -> RuntimeProbeStatus:
        if result.ok:
            detail = (result.stdout or result.stderr or "OK").strip().splitlines()[0]
            return RuntimeProbeStatus(name=name, status=RuntimeServiceStatus.ready, detail=detail[:160])
        detail = (result.stderr or result.stdout or "Command failed.").strip()
        status = RuntimeServiceStatus.unreachable if result.return_code in {124, 127} else RuntimeServiceStatus.unhealthy
        return RuntimeProbeStatus(name=name, status=status, detail=detail[:240])

    def _container_statuses(self, docker_status: RuntimeProbeStatus) -> list[RuntimeContainerStatus]:
        rows: dict[str, dict[str, Any]] = {}
        if docker_status.status == RuntimeServiceStatus.ready:
            result = self.runner.run(["docker", "ps", "-a", "--format", "{{json .}}"], timeout_seconds=10)
            if result.ok:
                for line in result.stdout.splitlines():
                    try:
                        payload = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    name = str(payload.get("Names") or payload.get("Name") or "")
                    if name:
                        rows[name] = payload

        containers: list[RuntimeContainerStatus] = []
        for name in REQUIRED_SUPABASE_CONTAINERS:
            payload = rows.get(name)
            status_text = None if payload is None else str(payload.get("Status") or payload.get("State") or "")
            running = bool(status_text and status_text.lower().startswith("up"))
            if payload is None:
                status = RuntimeServiceStatus.missing
            elif running and "unhealthy" in status_text.lower():
                status = RuntimeServiceStatus.unhealthy
            elif running:
                status = RuntimeServiceStatus.ready
            else:
                status = RuntimeServiceStatus.stopped
            containers.append(RuntimeContainerStatus(name=name, required=True, exists=payload is not None, running=running, status=status, status_text=status_text))
        return containers

    def _probe_grafana(self) -> RuntimeProbeStatus:
        url = self.settings.grafana_url
        try:
            response = httpx.get(url, timeout=1.5)
        except httpx.HTTPError as exc:
            return RuntimeProbeStatus(name="Grafana", status=RuntimeServiceStatus.unreachable, detail=str(exc), url=url)
        status = RuntimeServiceStatus.ready if response.status_code < 500 else RuntimeServiceStatus.unhealthy
        return RuntimeProbeStatus(name="Grafana", status=status, detail=f"HTTP {response.status_code}", url=url)

    def _config_items(self) -> list[RuntimeConfigItem]:
        return [
            self._config_item("localSupabaseProjectPath", "Project path", self.settings.local_supabase_project_path, "EWC_LOCAL_SUPABASE_PROJECT_PATH"),
            self._config_item("localSupabaseWslPath", "WSL path", self.settings.local_supabase_wsl_path, "EWC_LOCAL_SUPABASE_WSL_PATH"),
            self._config_item("localSupabaseProjectId", "Project id", self.settings.local_supabase_project_id, "EWC_LOCAL_SUPABASE_PROJECT_ID"),
            self._config_item("localSupabaseApiPort", "API port", str(self.settings.local_supabase_api_port), "EWC_LOCAL_SUPABASE_API_PORT"),
            self._config_item("localSupabaseDbPort", "DB port", str(self.settings.local_supabase_db_port), "EWC_LOCAL_SUPABASE_DB_PORT"),
            self._config_item("localSupabaseStudioPort", "Studio port", str(self.settings.local_supabase_studio_port), "EWC_LOCAL_SUPABASE_STUDIO_PORT"),
            self._config_item("supabaseEdgeUrl", "Edge URL", self.settings.upload_edge_url, "EWC_SUPABASE_EDGE_URL"),
            self._config_item("grafanaUrl", "Grafana URL", self.settings.grafana_url, "EWC_GRAFANA_URL"),
        ]

    def _config_item(self, key: str, label: str, value: str, env_key: str) -> RuntimeConfigItem:
        return RuntimeConfigItem(key=key, label=label, value=value, source="env" if env_key in os.environ else "default")
