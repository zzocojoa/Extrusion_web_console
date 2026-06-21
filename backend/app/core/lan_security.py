from dataclasses import dataclass
from ipaddress import ip_address
from urllib.parse import urlparse

from backend.app.core.settings import Settings


LOCALHOST_NAMES = {"localhost", "testclient", "testserver"}


@dataclass(frozen=True)
class LanSecurityState:
    enabled: bool
    status: str
    bind_host_class: str
    cors_origin_classes: tuple[str, ...]
    shared_local_token_allowed: bool
    reasons: tuple[str, ...]


def is_loopback_host(host: str | None) -> bool:
    if host in {None, ""}:
        return True
    normalized = host.strip().lower()
    if normalized in LOCALHOST_NAMES:
        return True
    try:
        return ip_address(normalized).is_loopback
    except ValueError:
        return False


def classify_host(host: str | None) -> str:
    if is_loopback_host(host):
        return "loopback"
    normalized = (host or "").strip()
    if normalized in {"0.0.0.0", "::"}:
        return "wildcard"
    try:
        return "non_loopback_ip" if ip_address(normalized) else "unknown"
    except ValueError:
        return "non_loopback_name"


def classify_cors_origin(origin: str) -> str:
    normalized = origin.strip()
    if normalized == "*":
        return "wildcard"
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return "invalid"
    return "loopback_origin" if is_loopback_host(parsed.hostname) else "non_loopback_origin"


def lan_security_state(settings: Settings) -> LanSecurityState:
    enabled = bool(settings.v2_lan_access_enabled)
    bind_host_class = classify_host(settings.host)
    cors_origin_classes = tuple(sorted({classify_cors_origin(origin) for origin in settings.cors_origins}))
    reasons: list[str] = []

    if bind_host_class != "loopback" and not enabled:
        reasons.append("lan_gate_disabled_non_loopback_configured_host")
    if any(origin_class != "loopback_origin" for origin_class in cors_origin_classes) and not enabled:
        reasons.append("lan_gate_disabled_non_loopback_cors")
    if enabled:
        reasons.append("lan_auth_not_implemented")
        reasons.append("lan_actor_session_not_implemented")
        reasons.append("lan_concurrency_not_implemented")

    status = "blocked" if reasons else "localhost_only"
    return LanSecurityState(
        enabled=enabled,
        status=status,
        bind_host_class=bind_host_class,
        cors_origin_classes=cors_origin_classes,
        shared_local_token_allowed=False,
        reasons=tuple(reasons),
    )


def assert_lan_security_gate(settings: Settings) -> None:
    state = lan_security_state(settings)
    if not state.reasons:
        return
    raise RuntimeError("LAN security gate blocked startup: " + ", ".join(state.reasons))


def server_host_from_scope_server(server: object) -> str | None:
    if not isinstance(server, (tuple, list)) or len(server) < 1:
        return None
    host = server[0]
    return host if isinstance(host, str) else None
