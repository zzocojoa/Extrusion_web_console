from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Extrusion Web Console API"
    service_name: str = "extrusion-web-console-api"
    version: str = "0.1.0"
    environment: str = "dev"
    host: str = "127.0.0.1"
    port: int = 8000
    grafana_url: str = "http://localhost:3001"
    state_db_path: str = str(Path.home() / "AppData" / "Roaming" / "ExtrusionWebConsole" / "web_console_state.db")
    plc_data_dir: str = ""
    temperature_data_dir: str = ""
    supabase_db_url: str = ""
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_edge_url: str = ""
    cors_origins: tuple[str, ...] = (
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    )

    @property
    def upload_edge_url(self) -> str:
        if self.supabase_edge_url:
            return self.supabase_edge_url
        if self.supabase_url:
            return self.supabase_url.rstrip("/") + "/functions/v1/upload-metrics"
        return ""

    model_config = SettingsConfigDict(env_prefix="EWC_", env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
