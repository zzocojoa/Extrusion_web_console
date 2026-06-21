from ipaddress import ip_address
import logging
from pathlib import Path

from fastapi import Request
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.responses import FileResponse
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles

from backend.app.api.dashboard import router as dashboard_router
from backend.app.api.audit import router as audit_router
from backend.app.api.config import router as config_router
from backend.app.api.health import router as health_router
from backend.app.api.runtime import router as runtime_router
from backend.app.api.upload_delete import router as upload_delete_router
from backend.app.api.upload_jobs import router as upload_jobs_router
from backend.app.api.upload_preview import router as upload_preview_router
from backend.app.core.local_token import audit_local_token_failure
from backend.app.core.local_token import bootstrap_script_for_settings
from backend.app.core.local_token import local_token_enforcement_enabled
from backend.app.core.local_token import local_token_error_response
from backend.app.core.local_token import validate_local_token
from backend.app.core.settings import Settings
from backend.app.core.settings import get_settings
from backend.app.db.audit_repository import AuditRepository
from backend.app.db.db_delta_repository import DbDeltaEvidenceRepository
from backend.app.db.preview_repository import PreviewRepository
from backend.app.db.runtime_repository import RuntimeRepository
from backend.app.db.row_attribution_repository import RowAttributionRepository
from backend.app.db.upload_delete_repository import UploadDeleteRepository
from backend.app.db.upload_job_repository import UploadJobRepository


API_PREFIX_SEGMENT = "api"
_LOGGER = logging.getLogger(__name__)


def api_docs_enabled(settings: Settings) -> bool:
    mode = settings.api_docs_mode.strip().lower()
    if mode == "enabled":
        return True
    if mode == "disabled":
        return False
    return settings.local_token_mode.strip().lower() != "required"


def is_loopback_host(host: str | None) -> bool:
    if host in {None, "", "localhost", "testclient"}:
        return True
    try:
        return ip_address(host).is_loopback
    except ValueError:
        return False


def configure_frontend_static(app: FastAPI, frontend_dist_path: str) -> None:
    dist_path = Path(frontend_dist_path)
    index_path = dist_path / "index.html"
    assets_path = dist_path / "assets"

    if assets_path.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")

    @app.get("/")
    async def serve_frontend_root():
        if index_path.exists():
            return _frontend_index_response(index_path)
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Frontend build is missing. Run npm run build from frontend or start the launcher with the developer build flag."
            },
        )

    @app.get("/{path:path}")
    async def serve_frontend_route(path: str):
        if path == "favicon.ico":
            favicon_path = dist_path / "favicon.ico"
            if favicon_path.exists():
                return FileResponse(favicon_path)
        if path.startswith(f"{API_PREFIX_SEGMENT}/") or path == API_PREFIX_SEGMENT:
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        if index_path.exists():
            return _frontend_index_response(index_path)
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Frontend build is missing. Run npm run build from frontend or start the launcher with the developer build flag."
            },
        )


def _frontend_index_response(index_path: Path):
    settings = get_settings()
    bootstrap_script = bootstrap_script_for_settings(settings)
    if not bootstrap_script:
        return FileResponse(index_path)

    html = index_path.read_text(encoding="utf-8")
    if "</head>" in html:
        html = html.replace("</head>", f"{bootstrap_script}</head>", 1)
    else:
        html = f"{bootstrap_script}{html}"
    return HTMLResponse(
        html,
        headers={
            "Cache-Control": "no-store",
        },
    )


def log_v2_feature_gate_snapshot(settings: Settings) -> None:
    _LOGGER.info(
        "V2 feature gate snapshot: "
        "delete_expansion_enabled=%s "
        "date_scoped_delete_ui_enabled=%s "
        "lan_access_enabled=%s "
        "row_attribution_enabled=%s "
        "db_delta_evidence_required=%s",
        settings.v2_delete_expansion_enabled,
        settings.v2_date_scoped_delete_ui_enabled,
        settings.v2_lan_access_enabled,
        settings.v2_row_attribution_enabled,
        settings.v2_db_delta_evidence_required,
    )


def create_app() -> FastAPI:
    settings = get_settings()
    if not local_token_enforcement_enabled(settings):
        _LOGGER.warning("Local token enforcement is disabled by explicit mode or missing runtime token.")
    log_v2_feature_gate_snapshot(settings)
    AuditRepository(settings.state_db_path).bootstrap()
    DbDeltaEvidenceRepository(settings.state_db_path).bootstrap()
    RowAttributionRepository(
        settings.state_db_path,
        writes_enabled=settings.effective_row_attribution_writes_enabled,
    ).bootstrap()
    PreviewRepository(settings.state_db_path).mark_interrupted_active_runs()
    UploadJobRepository(settings.state_db_path).mark_interrupted_active_jobs()
    UploadDeleteRepository(settings.state_db_path).mark_interrupted_active_delete_runs()
    RuntimeRepository(settings.state_db_path).mark_interrupted_active_operations()
    docs_enabled = api_docs_enabled(settings)
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        openapi_url="/api/openapi.json" if docs_enabled else None,
        docs_url="/api/docs" if docs_enabled else None,
        redoc_url=None,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def enforce_loopback_client(request: Request, call_next):
        if not is_loopback_host(request.client.host if request.client else None):
            return JSONResponse(
                status_code=403,
                content={"detail": "Extrusion Web Console only accepts localhost clients."},
            )
        return await call_next(request)

    @app.middleware("http")
    async def enforce_local_api_token(request: Request, call_next):
        current_settings = get_settings()
        failure = validate_local_token(request, current_settings)
        if failure is not None:
            await audit_local_token_failure(request, current_settings, failure)
            return local_token_error_response()
        return await call_next(request)

    app.include_router(health_router)
    app.include_router(dashboard_router)
    app.include_router(config_router)
    app.include_router(audit_router)
    app.include_router(upload_preview_router)
    app.include_router(upload_jobs_router)
    app.include_router(upload_delete_router)
    app.include_router(runtime_router)
    configure_frontend_static(app, settings.frontend_dist_path)
    return app


app = create_app()
