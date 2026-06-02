from ipaddress import ip_address

from fastapi import Request
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from backend.app.api.dashboard import router as dashboard_router
from backend.app.api.health import router as health_router
from backend.app.api.upload_jobs import router as upload_jobs_router
from backend.app.api.upload_preview import router as upload_preview_router
from backend.app.core.settings import get_settings
from backend.app.db.preview_repository import PreviewRepository
from backend.app.db.upload_job_repository import UploadJobRepository


def is_loopback_host(host: str | None) -> bool:
    if host in {None, "", "localhost", "testclient"}:
        return True
    try:
        return ip_address(host).is_loopback
    except ValueError:
        return False


def create_app() -> FastAPI:
    settings = get_settings()
    PreviewRepository(settings.state_db_path).mark_interrupted_active_runs()
    UploadJobRepository(settings.state_db_path).mark_interrupted_active_jobs()
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        openapi_url="/api/openapi.json",
        docs_url="/api/docs",
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

    app.include_router(health_router)
    app.include_router(dashboard_router)
    app.include_router(upload_preview_router)
    app.include_router(upload_jobs_router)
    return app


app = create_app()
