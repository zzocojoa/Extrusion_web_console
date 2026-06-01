from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Extrusion Web Console API"
    service_name: str = "extrusion-web-console-api"
    version: str = "0.1.0"
    environment: str = "dev"
    host: str = "127.0.0.1"
    port: int = 8000
    grafana_url: str = "http://localhost:3001"
    cors_origins: tuple[str, ...] = (
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    )

    model_config = SettingsConfigDict(env_prefix="EWC_", env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
