import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_CONFIG_FILE_PATH = str(Path.home() / "AppData" / "Roaming" / "ExtrusionWebConsole" / "config.json")
DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_FRONTEND_DIST_PATH = str(DEFAULT_REPO_ROOT / "frontend" / "dist")
DEFAULT_LOCAL_SUPABASE_PROJECT_ID = "Extrusion_web_console"
DEFAULT_LOCAL_SUPABASE_API_PORT = 55321
DEFAULT_LOCAL_SUPABASE_DB_PORT = 25433
DEFAULT_LOCAL_SUPABASE_STUDIO_PORT = 55323


def default_wsl_path(path: Path) -> str:
    drive = path.drive.rstrip(":").lower()
    if drive and len(drive) == 1:
        parts = "/".join(path.parts[1:])
        return f"/mnt/{drive}/{parts}"
    return str(path).replace("\\", "/")

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
    api_docs_mode: str = "auto"
    local_api_token: str = ""
    local_token_mode: str = "auto"
    grafana_url: str = "http://localhost:3001"
    state_db_path: str = str(Path.home() / "AppData" / "Roaming" / "ExtrusionWebConsole" / "web_console_state.db")
    config_file_path: str = DEFAULT_CONFIG_FILE_PATH
    plc_data_dir: str = ""
    temperature_data_dir: str = ""
    supabase_db_url: str = ""
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_edge_url: str = ""
    local_supabase_project_path: str = str(DEFAULT_REPO_ROOT)
    local_supabase_wsl_path: str = default_wsl_path(DEFAULT_REPO_ROOT)
    local_supabase_project_id: str = DEFAULT_LOCAL_SUPABASE_PROJECT_ID
    local_supabase_api_port: int = DEFAULT_LOCAL_SUPABASE_API_PORT
    local_supabase_db_port: int = DEFAULT_LOCAL_SUPABASE_DB_PORT
    local_supabase_studio_port: int = DEFAULT_LOCAL_SUPABASE_STUDIO_PORT
    local_supabase_edge_container: str = f"supabase_edge_runtime_{DEFAULT_LOCAL_SUPABASE_PROJECT_ID}"
    local_supabase_grafana_container: str = "grafana_local"
    runtime_command_timeout_seconds: int = 20
    runtime_readiness_timeout_seconds: int = 90
    v2_row_attribution_enabled: bool = False
    v2_db_delta_evidence_required: bool = True
    row_attribution_writes_enabled: bool = False
    row_attribution_hmac_key: str = ""
    cors_origins: tuple[str, ...] = (
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    )

    @property
    def effective_row_attribution_writes_enabled(self) -> bool:
        return bool(self.v2_row_attribution_enabled or self.row_attribution_writes_enabled)

    @property
    def upload_edge_url(self) -> str:
        if self.supabase_edge_url:
            return self.supabase_edge_url
        base_url = self.supabase_url or f"http://127.0.0.1:{self.local_supabase_api_port}"
        return base_url.rstrip("/") + "/functions/v1/upload-metrics"

    @property
    def local_runtime_edge_url(self) -> str:
        if self.supabase_edge_url:
            return self.supabase_edge_url
        return f"http://127.0.0.1:{self.local_supabase_api_port}/functions/v1/upload-metrics"

    @field_validator("api_docs_mode")
    @classmethod
    def validate_api_docs_mode(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"auto", "enabled", "disabled"}:
            raise ValueError("api_docs_mode must be one of: auto, enabled, disabled")
        return normalized

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
