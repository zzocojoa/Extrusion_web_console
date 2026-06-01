from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.dashboard import router as dashboard_router
from backend.app.api.health import router as health_router
from backend.app.core.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
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
    app.include_router(health_router)
    app.include_router(dashboard_router)
    return app


app = create_app()
