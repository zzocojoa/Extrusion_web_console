import json
import os
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from backend.app.core.settings import Settings, clear_settings_cache
from backend.app.core.state_context import build_state_context
from backend.app.core.target_class import build_upload_target_preflight
from backend.app.db.audit_repository import AuditRepository
from backend.app.schemas.audit import AuditResult
from backend.app.schemas.config import ConfigItemDto, ConfigResponse, ConfigSaveRequest, ConfigSaveResponse, TargetClassPreflightDto


@dataclass(frozen=True)
class ConfigField:
    key: str
    settings_attr: str
    label: str
    env_key: str
    value_type: type
    secret: bool = False


CONFIG_FIELDS: tuple[ConfigField, ...] = (
    ConfigField("plcDataDir", "plc_data_dir", "Process data directory", "EWC_PLC_DATA_DIR", str),
    ConfigField("temperatureDataDir", "temperature_data_dir", "Production daily report directory", "EWC_TEMPERATURE_DATA_DIR", str),
    ConfigField("supabaseDbUrl", "supabase_db_url", "Supabase DB URL", "EWC_SUPABASE_DB_URL", str, secret=True),
    ConfigField("supabaseUrl", "supabase_url", "Supabase URL", "EWC_SUPABASE_URL", str),
    ConfigField("supabaseAnonKey", "supabase_anon_key", "Supabase anon key", "EWC_SUPABASE_ANON_KEY", str, secret=True),
    ConfigField("supabaseEdgeUrl", "supabase_edge_url", "Supabase Edge URL", "EWC_SUPABASE_EDGE_URL", str, secret=True),
    ConfigField("grafanaUrl", "grafana_url", "Grafana URL", "EWC_GRAFANA_URL", str),
    ConfigField("localSupabaseProjectPath", "local_supabase_project_path", "Project path", "EWC_LOCAL_SUPABASE_PROJECT_PATH", str),
    ConfigField("localSupabaseWslPath", "local_supabase_wsl_path", "WSL path", "EWC_LOCAL_SUPABASE_WSL_PATH", str),
    ConfigField("localSupabaseProjectId", "local_supabase_project_id", "Project id", "EWC_LOCAL_SUPABASE_PROJECT_ID", str),
    ConfigField("localSupabaseApiPort", "local_supabase_api_port", "API port", "EWC_LOCAL_SUPABASE_API_PORT", int),
    ConfigField("localSupabaseDbPort", "local_supabase_db_port", "DB port", "EWC_LOCAL_SUPABASE_DB_PORT", int),
    ConfigField("localSupabaseStudioPort", "local_supabase_studio_port", "Studio port", "EWC_LOCAL_SUPABASE_STUDIO_PORT", int),
    ConfigField("runtimeCommandTimeoutSeconds", "runtime_command_timeout_seconds", "Runtime command timeout", "EWC_RUNTIME_COMMAND_TIMEOUT_SECONDS", int),
    ConfigField("runtimeReadinessTimeoutSeconds", "runtime_readiness_timeout_seconds", "Runtime readiness timeout", "EWC_RUNTIME_READINESS_TIMEOUT_SECONDS", int),
)

FIELDS_BY_KEY = {field.key: field for field in CONFIG_FIELDS}
_CONFIG_FILE_LOCKS: dict[Path, threading.Lock] = {}
_CONFIG_FILE_LOCKS_GUARD = threading.Lock()


def _dotenv_env_keys() -> set[str]:
    dotenv_path = Path(".env")
    if not dotenv_path.exists():
        return set()
    keys: set[str] = set()
    for line in dotenv_path.read_text(encoding="utf-8").splitlines():
        candidate = line.strip()
        if not candidate or candidate.startswith("#"):
            continue
        if candidate.startswith("export "):
            candidate = candidate.removeprefix("export ").strip()
        key, separator, _value = candidate.partition("=")
        if separator:
            keys.add(key.strip())
    return keys


def _has_env_override(env_key: str) -> bool:
    return env_key in os.environ or env_key in _dotenv_env_keys()


class ConfigSaveError(Exception):
    def __init__(self, *, status_code: int, error_code: str, message: str, keys: list[str]) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.keys = keys


def _field_names_from_validation_error(error: ValidationError) -> list[str]:
    fields: set[str] = set()
    for item in error.errors():
        loc = item.get("loc", ())
        if not loc:
            continue
        first = loc[0]
        if first == "values" and len(loc) > 1:
            fields.add(str(loc[1]))
        else:
            fields.add(str(first))
    return sorted(fields)


def _get_config_file_lock(path: Path) -> threading.Lock:
    lock_key = path.resolve(strict=False)
    with _CONFIG_FILE_LOCKS_GUARD:
        lock = _CONFIG_FILE_LOCKS.get(lock_key)
        if lock is None:
            lock = threading.Lock()
            _CONFIG_FILE_LOCKS[lock_key] = lock
        return lock


class ConfigService:
    def __init__(self, settings: Settings, audit_repository: AuditRepository) -> None:
        self.settings = settings
        self.audit_repository = audit_repository
        self.config_path = Path(settings.config_file_path)

    def get_config(self) -> ConfigResponse:
        saved = self._read_config_file()
        items: list[ConfigItemDto] = []
        for field in CONFIG_FIELDS:
            env_overridden = _has_env_override(field.env_key)
            saved_has_key = field.key in saved
            source = "env" if env_overridden else "config" if saved_has_key else "default"
            raw_value = getattr(self.settings, field.settings_attr)
            if not env_overridden and saved_has_key:
                raw_value = saved[field.key]
            items.append(
                ConfigItemDto(
                    key=field.key,
                    label=field.label,
                    value=None if field.secret and raw_value else raw_value,
                    source=source,
                    secret=field.secret,
                    env_key=field.env_key,
                    overridden=env_overridden,
                )
            )
        return ConfigResponse(
            config_file_path=str(self.config_path),
            items=items,
            target_classes=TargetClassPreflightDto.model_validate(build_upload_target_preflight(self.settings).to_api()),
            state_context=build_state_context(self.settings).to_api(),
        )

    def save_config_payload(self, payload: Any) -> ConfigSaveResponse:
        try:
            request = ConfigSaveRequest.model_validate(payload)
        except ValidationError as exc:
            rejected_fields = _field_names_from_validation_error(exc)
            error = self.audit_request_validation_failure(
                keys=rejected_fields,
                validation_reason="config_request_validation_failed",
            )
            raise error from exc
        return self.save_config(request.values, actor=request.actor)

    def audit_request_validation_failure(self, *, keys: list[str], validation_reason: str) -> ConfigSaveError:
        error = ConfigSaveError(
            status_code=422,
            error_code=validation_reason,
            message="Settings save request failed validation.",
            keys=keys,
        )
        self._audit_save(
            actor="local_operator",
            result=AuditResult.failure,
            error_code=error.error_code,
            error_message=error.message,
            keys=error.keys,
            validation_reason=error.error_code,
        )
        return error

    def save_config(self, values: dict[str, Any], *, actor: str) -> ConfigSaveResponse:
        try:
            normalized = self._validate_values(values)
            blocked_keys = [key for key in normalized if _has_env_override(FIELDS_BY_KEY[key].env_key)]
            if blocked_keys:
                raise ConfigSaveError(
                    status_code=409,
                    error_code="config_env_override",
                    message="Environment-overridden settings cannot be saved.",
                    keys=blocked_keys,
                )
            with _get_config_file_lock(self.config_path):
                saved = self._read_config_file()
                saved.update(normalized)
                try:
                    self._write_config_file(saved)
                except OSError as exc:
                    raise ConfigSaveError(
                        status_code=500,
                        error_code="config_write_failed",
                        message="Config file could not be written.",
                        keys=sorted(normalized.keys()),
                    ) from exc
        except ConfigSaveError as exc:
            self._audit_save(
                actor=actor,
                result=AuditResult.blocked if exc.error_code == "config_env_override" else AuditResult.failure,
                error_code=exc.error_code,
                error_message=exc.message,
                keys=exc.keys,
                validation_reason=exc.error_code if exc.status_code == 422 else None,
            )
            raise

        saved_keys = sorted(normalized.keys())
        clear_settings_cache()
        self._audit_save(actor=actor, result=AuditResult.success, keys=saved_keys)
        return ConfigSaveResponse(saved_keys=saved_keys, config_file_path=str(self.config_path))

    def _validate_values(self, values: dict[str, Any]) -> dict[str, Any]:
        if not values:
            raise ConfigSaveError(
                status_code=422,
                error_code="config_empty_update",
                message="At least one setting value is required.",
                keys=[],
            )
        unknown_keys = sorted(set(values) - set(FIELDS_BY_KEY))
        if unknown_keys:
            raise ConfigSaveError(
                status_code=422,
                error_code="config_unknown_key",
                message="Unknown setting key.",
                keys=unknown_keys,
            )

        normalized: dict[str, Any] = {}
        invalid_keys: list[str] = []
        for key, value in values.items():
            field = FIELDS_BY_KEY[key]
            if field.value_type is int:
                if isinstance(value, bool):
                    invalid_keys.append(key)
                    continue
                try:
                    int_value = int(value)
                except (TypeError, ValueError):
                    invalid_keys.append(key)
                    continue
                if int_value < 1 or int_value > 65535:
                    invalid_keys.append(key)
                    continue
                normalized[key] = int_value
            else:
                if not isinstance(value, str):
                    invalid_keys.append(key)
                    continue
                normalized[key] = value.strip()
        if invalid_keys:
            raise ConfigSaveError(
                status_code=422,
                error_code="config_validation_failed",
                message="One or more setting values failed validation.",
                keys=sorted(invalid_keys),
            )
        return normalized

    def _read_config_file(self) -> dict[str, Any]:
        if not self.config_path.exists():
            return {}
        try:
            decoded = json.loads(self.config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ConfigSaveError(
                status_code=422,
                error_code="config_file_invalid",
                message=f"Config file is not valid JSON: {exc.msg}",
                keys=[],
            ) from exc
        if not isinstance(decoded, dict):
            raise ConfigSaveError(
                status_code=422,
                error_code="config_file_invalid",
                message="Config file must contain a JSON object.",
                keys=[],
            )
        return dict(decoded)

    def _write_config_file(self, payload: dict[str, Any]) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.config_path.with_name(f".{self.config_path.name}.{uuid.uuid4().hex}.tmp")
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        try:
            tmp_path.replace(self.config_path)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def _audit_save(
        self,
        *,
        actor: str,
        result: AuditResult,
        keys: list[str],
        error_code: str | None = None,
        error_message: str | None = None,
        validation_reason: str | None = None,
    ) -> None:
        params: dict[str, Any] = {
            "savedSettings": sorted(keys) if result == AuditResult.success else [],
            "rejectedSettings": sorted(keys) if result != AuditResult.success else [],
            "configPathConfigured": bool(self.settings.config_file_path),
        }
        if validation_reason:
            params["validationReason"] = validation_reason
        self.audit_repository.insert_audit(
            action="settings.save",
            target_type="settings",
            target_id="app_config",
            params=params,
            result=result,
            actor=actor,
            error_code=error_code,
            error_message=error_message,
        )
