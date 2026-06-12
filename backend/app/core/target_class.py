from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from backend.app.core.settings import Settings


UPLOAD_METRICS_PATH = "/functions/v1/upload-metrics"


@dataclass(frozen=True)
class SanitizedTargetClass:
    configured: bool
    source: str
    target_class: str
    host_class: str
    port_class: str
    path_class: str
    _comparison_key: tuple[str, str, int | None, str]

    def to_api(self) -> dict[str, Any]:
        return {
            "configured": self.configured,
            "source": self.source,
            "targetClass": self.target_class,
            "hostClass": self.host_class,
            "portClass": self.port_class,
            "pathClass": self.path_class,
        }


@dataclass(frozen=True)
class UploadTargetPreflight:
    db: SanitizedTargetClass
    upload_edge: SanitizedTargetClass
    runtime_edge: SanitizedTargetClass
    upload_runtime_aligned: bool
    passed: bool
    reason: str

    def to_api(self) -> dict[str, Any]:
        return {
            "db": self.db.to_api(),
            "uploadEdge": self.upload_edge.to_api(),
            "runtimeEdge": self.runtime_edge.to_api(),
            "uploadRuntimeAligned": self.upload_runtime_aligned,
            "status": "passed" if self.passed else "blocked",
            "reason": self.reason,
        }


def build_upload_target_preflight(settings: Settings) -> UploadTargetPreflight:
    db = classify_database_url(
        settings.supabase_db_url,
        expected_db_port=settings.local_supabase_db_port,
        source="supabase_db_url" if settings.supabase_db_url else "not_configured",
    )
    upload_edge = classify_http_url(
        settings.upload_edge_url,
        expected_api_port=settings.local_supabase_api_port,
        expected_path=UPLOAD_METRICS_PATH,
        source=_upload_edge_source(settings),
    )
    runtime_edge = classify_http_url(
        settings.local_runtime_edge_url,
        expected_api_port=settings.local_supabase_api_port,
        expected_path=UPLOAD_METRICS_PATH,
        source=_runtime_edge_source(settings),
    )
    upload_runtime_aligned = upload_edge._comparison_key == runtime_edge._comparison_key
    edge_ready = (
        upload_runtime_aligned
        and upload_edge.target_class == "loopback_expected_api_port_upload_metrics"
        and runtime_edge.target_class == "loopback_expected_api_port_upload_metrics"
    )

    if not edge_ready:
        reason = "edge_target_class_mismatch"
    else:
        reason = "target_class_preflight_passed"

    return UploadTargetPreflight(
        db=db,
        upload_edge=upload_edge,
        runtime_edge=runtime_edge,
        upload_runtime_aligned=upload_runtime_aligned,
        passed=edge_ready,
        reason=reason,
    )


def classify_http_url(
    url: str,
    *,
    expected_api_port: int,
    expected_path: str,
    source: str,
) -> SanitizedTargetClass:
    if not url:
        return SanitizedTargetClass(
            configured=False,
            source=source,
            target_class="not_configured",
            host_class="not_configured",
            port_class="not_configured",
            path_class="not_configured",
            _comparison_key=("", "not_configured", None, "not_configured"),
        )
    try:
        parsed = urlparse(url)
        port = parsed.port
    except ValueError:
        return SanitizedTargetClass(
            configured=True,
            source=source,
            target_class="invalid_url",
            host_class="invalid_url",
            port_class="invalid_url",
            path_class="invalid_url",
            _comparison_key=("", "invalid_url", None, "invalid_url"),
        )

    host_class, comparable_host = _host_class(parsed.hostname)
    path_class = "upload_metrics" if parsed.path.rstrip("/") == expected_path else "other_path"
    if port is None:
        port_class = "missing_port"
    elif port == expected_api_port:
        port_class = "expected_api_port"
    else:
        port_class = "unexpected_port"

    target_class = _join_class(host_class, port_class, path_class)
    return SanitizedTargetClass(
        configured=True,
        source=source,
        target_class=target_class,
        host_class=host_class,
        port_class=port_class,
        path_class=path_class,
        _comparison_key=(parsed.scheme.lower(), comparable_host, port, path_class),
    )


def classify_database_url(url: str, *, expected_db_port: int, source: str) -> SanitizedTargetClass:
    if not url:
        return SanitizedTargetClass(
            configured=False,
            source=source,
            target_class="not_configured",
            host_class="not_configured",
            port_class="not_configured",
            path_class="not_applicable",
            _comparison_key=("", "not_configured", None, "not_applicable"),
        )
    try:
        parsed = urlparse(url)
        port = parsed.port
    except ValueError:
        return SanitizedTargetClass(
            configured=True,
            source=source,
            target_class="invalid_url",
            host_class="invalid_url",
            port_class="invalid_url",
            path_class="not_applicable",
            _comparison_key=("", "invalid_url", None, "not_applicable"),
        )

    host_class, comparable_host = _host_class(parsed.hostname)
    if port is None:
        port_class = "missing_port"
    elif port == expected_db_port:
        port_class = "expected_db_port"
    else:
        port_class = "unexpected_port"

    target_class = _join_class(host_class, port_class)
    return SanitizedTargetClass(
        configured=True,
        source=source,
        target_class=target_class,
        host_class=host_class,
        port_class=port_class,
        path_class="not_applicable",
        _comparison_key=(parsed.scheme.lower(), comparable_host, port, "not_applicable"),
    )


def _upload_edge_source(settings: Settings) -> str:
    if settings.supabase_edge_url:
        return "supabase_edge_url"
    if settings.supabase_url:
        return "supabase_url_fallback"
    return "local_supabase_api_port"


def _runtime_edge_source(settings: Settings) -> str:
    if settings.supabase_edge_url:
        return "supabase_edge_url"
    return "local_supabase_api_port"


def _host_class(hostname: str | None) -> tuple[str, str]:
    if not hostname:
        return "missing_host", "missing_host"
    lowered = hostname.strip("[]").lower()
    if lowered in {"127.0.0.1", "localhost", "::1"}:
        return "loopback", "loopback"
    return "non_loopback", "non_loopback"


def _join_class(*parts: str) -> str:
    return "_".join(part for part in parts if part)
