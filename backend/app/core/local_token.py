import hmac
import logging
import time
from dataclasses import dataclass
from typing import Any

from fastapi import Request
from starlette.responses import JSONResponse

from backend.app.core.settings import Settings
from backend.app.db.audit_repository import AuditRepository
from backend.app.schemas.audit import AuditResult


LOCAL_TOKEN_HEADER = "X-EWC-Local-Token"
LOCAL_TOKEN_REQUIRED_CODE = "local_token_required"
LOCAL_TOKEN_MESSAGE = "Local console token is missing or invalid. Restart the web console from the launcher."
AUDIT_RATE_LIMIT_SECONDS = 10.0

_LOGGER = logging.getLogger(__name__)
_LAST_AUDIT_BY_BUCKET: dict[tuple[str, str, str], float] = {}


@dataclass(frozen=True)
class LocalTokenFailure:
    reason_code: str
    token_present: bool


@dataclass(frozen=True)
class ProtectedAction:
    action: str
    target_type: str
    target_id: str | None
    route_group: str


def local_token_enforcement_enabled(settings: Settings) -> bool:
    mode = settings.local_token_mode.strip().lower()
    if mode == "dev-disabled":
        return False
    if mode == "required":
        return True
    return bool(settings.local_api_token)


def should_protect_request(request: Request) -> bool:
    method = request.method.upper()
    if method in {"GET", "HEAD", "OPTIONS"}:
        return False
    path = request.url.path
    if not (path == "/api" or path.startswith("/api/")):
        return False
    return True


def validate_local_token(request: Request, settings: Settings) -> LocalTokenFailure | None:
    if not local_token_enforcement_enabled(settings) or not should_protect_request(request):
        return None

    expected = settings.local_api_token
    supplied = request.headers.get(LOCAL_TOKEN_HEADER)
    if not supplied:
        return LocalTokenFailure(reason_code="local_token_missing", token_present=False)
    if not expected or not hmac.compare_digest(supplied, expected):
        return LocalTokenFailure(reason_code="local_token_invalid", token_present=True)
    return None


def local_token_error_response() -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content={
            "detail": {
                "code": LOCAL_TOKEN_REQUIRED_CODE,
                "message": LOCAL_TOKEN_MESSAGE,
            }
        },
    )


def bootstrap_script_for_settings(settings: Settings) -> str | None:
    if not local_token_enforcement_enabled(settings) or not settings.local_api_token:
        return None
    # Runtime-only HTML injection. The token is never written into frontend/dist.
    import json

    payload = json.dumps({"localApiToken": settings.local_api_token}, ensure_ascii=False)
    return f"<script>window.__EWC_BOOTSTRAP__ = {payload};</script>"


def token_bootstrap_enabled(settings: Settings) -> bool:
    return bootstrap_script_for_settings(settings) is not None


async def audit_local_token_failure(
    request: Request,
    settings: Settings,
    failure: LocalTokenFailure,
) -> None:
    action = action_for_request(request, settings)
    bucket = (action.action, action.route_group, failure.reason_code)
    now = time.monotonic()
    last = _LAST_AUDIT_BY_BUCKET.get(bucket)
    if last is not None and now - last < AUDIT_RATE_LIMIT_SECONDS:
        return
    _LAST_AUDIT_BY_BUCKET[bucket] = now

    source_host = "loopback" if _is_loopback_request(request) else "non_loopback"
    params: dict[str, Any] = {
        "reasonCode": failure.reason_code,
        "method": request.method.upper(),
        "routeGroup": action.route_group,
        "sourceHost": source_host,
        "tokenPresent": failure.token_present,
    }
    try:
        AuditRepository(settings.state_db_path).insert_audit(
            action=action.action,
            target_type=action.target_type,
            target_id=action.target_id,
            params=params,
            result=AuditResult.blocked,
            error_code=failure.reason_code,
            error_message=LOCAL_TOKEN_MESSAGE,
        )
    except Exception:
        _LOGGER.exception("Failed to write local token failure audit row.")


def action_for_request(request: Request, settings: Settings | None = None) -> ProtectedAction:
    path = request.url.path
    parts = [part for part in path.split("/") if part]

    if path == "/api/config":
        return ProtectedAction("settings.save", "config", "app_config", "config")

    if path.startswith("/api/upload/preview"):
        target_id = parts[3] if len(parts) >= 4 and parts[3] != "cancel" else None
        return ProtectedAction("upload.preview", "upload_preview", target_id, "upload.preview")

    if path.startswith("/api/upload/delete"):
        if path == "/api/upload/delete/preflight":
            return ProtectedAction("upload.delete_preflight", "delete_preflight", None, "upload.delete")
        delete_run_id = parts[4] if len(parts) >= 5 and parts[3] == "jobs" else None
        action_segment = parts[5] if len(parts) >= 6 else ""
        action_name = "upload.delete_reconciled" if action_segment == "reconcile" else "upload.delete_start"
        return ProtectedAction(action_name, "delete_run", delete_run_id, "upload.delete")

    if path == "/api/upload/jobs":
        return ProtectedAction("upload.start", "upload_job", None, "upload.jobs")

    if path.startswith("/api/upload/jobs/"):
        job_id = parts[3] if len(parts) >= 4 else None
        action_segment = parts[4] if len(parts) >= 5 else ""
        action_name = {
            "retry": "upload.retry",
            "pause": "upload.pause",
            "resume": "upload.resume",
            "cancel": "upload.cancel",
        }.get(action_segment, "upload.start")
        return ProtectedAction(action_name, "upload_job", job_id, "upload.jobs")

    if path == "/api/runtime/local-supabase/start":
        return ProtectedAction(
            "runtime.start",
            "local_supabase",
            settings.local_supabase_project_id if settings is not None else None,
            "runtime",
        )

    if path == "/api/runtime/local-supabase/stop":
        return ProtectedAction(
            "runtime.stop",
            "local_supabase",
            settings.local_supabase_project_id if settings is not None else None,
            "runtime",
        )

    return ProtectedAction("local.token", "api", None, "api")


def _is_loopback_request(request: Request) -> bool:
    if request.client is None:
        return True
    return request.client.host in {"127.0.0.1", "::1", "localhost", "testclient"}
