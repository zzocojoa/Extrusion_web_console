import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_CONFIG_FILE_PATH = str(Path.home() / "AppData" / "Roaming" / "ExtrusionWebConsole" / "config.json")
DEFAULT_FRONTEND_DIST_PATH = str(Path(__file__).resolve().parents[3] / "frontend" / "dist")

CONFIG_JSON_KEY_TO_FIELD = {
    "plcDataDir": "plc_data_dir",
    "temperatureDataDir": "temperature_data_dir",
    "supabaseDbUrl": "supabase_db_url",
    "supabaseUrl": "supabase_url",
    "supabaseAnonKey": "supabase_anon_key",
    "supabaseEdgeUrl": "supabase_edge_url",
    "grafanaUrl": "grafana_url",
    "localSupabaseProjectPath": "local_supabase_project_path",
    "localSupabaseWslPath": "local_supabase_wsl_path",
    "localSupabaseProjectId": "local_supabase_project_id",
    "localSupabaseApiPort": "local_supabase_api_port",
    "localSupabaseDbPort": "local_supabase_db_port",
    "localSupabaseStudioPort": "local_supabase_studio_port",
    "runtimeCommandTimeoutSeconds": "runtime_command_timeout_seconds",
    "runtimeReadinessTimeoutSeconds": "runtime_readiness_timeout_seconds",
}


def config_json_settings_source() -> dict[str, Any]:
    config_path = Path(os.environ.get("EWC_CONFIG_FILE_PATH", DEFAULT_CONFIG_FILE_PATH))
    if not config_path.exists():
        return {}
    try:
        decoded = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(decoded, dict):
        return {}
    return {CONFIG_JSON_KEY_TO_FIELD[key]: value for key, value in decoded.items() if key in CONFIG_JSON_KEY_TO_FIELD}


class Settings(BaseSettings):
    app_name: str = "Extrusion Web Console API"
    service_name: str = "extrusion-web-console-api"
    version: str = "0.1.0"
    environment: str = "dev"
    host: str = "127.0.0.1"
    port: int = 8000
    frontend_dist_path: str = DEFAULT_FRONTEND_DIST_PATH
    grafana_url: str = "http://localhost:3001"
    state_db_path: str = str(Path.home() / "AppData" / "Roaming" / "ExtrusionWebConsole" / "web_console_state.db")
    config_file_path: str = DEFAULT_CONFIG_FILE_PATH
    plc_data_dir: str = ""
    temperature_data_dir: str = ""
    supabase_db_url: str = ""
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_edge_url: str = ""
    local_supabase_project_path: str = r"C:\Users\user\Documents\GitHub\Extrusion_data"
    local_supabase_wsl_path: str = "/mnt/c/Users/user/Documents/GitHub/Extrusion_data"
    local_supabase_project_id: str = "Extrusion_data"
    local_supabase_api_port: int = 54321
    local_supabase_db_port: int = 25432
    local_supabase_studio_port: int = 54323
    local_supabase_edge_container: str = "supabase_edge_runtime_Extrusion_data"
    local_supabase_grafana_container: str = "grafana_local"
    runtime_command_timeout_seconds: int = 20
    runtime_readiness_timeout_seconds: int = 90
    cors_origins: tuple[str, ...] = (
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    )

    @property
    def upload_edge_url(self) -> str:
        if self.supabase_edge_url:
            return self.supabase_edge_url
        base_url = self.supabase_url or f"http://127.0.0.1:{self.local_supabase_api_port}"
        return base_url.rstrip("/") + "/functions/v1/upload-metrics"

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            config_json_settings_source,
            file_secret_settings,
        )

    model_config = SettingsConfigDict(env_prefix="EWC_", env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
