from typing import Any

from pydantic import Field

from backend.app.schemas.upload_preview import ApiModel


class TargetClassItemDto(ApiModel):
    configured: bool
    source: str
    target_class: str
    host_class: str
    port_class: str
    path_class: str


class TargetClassPreflightDto(ApiModel):
    db: TargetClassItemDto
    upload_edge: TargetClassItemDto
    runtime_edge: TargetClassItemDto
    upload_runtime_aligned: bool
    status: str
    reason: str


class ConfigItemDto(ApiModel):
    key: str
    label: str
    value: Any | None = None
    source: str
    secret: bool = False
    env_key: str
    overridden: bool = False


class ConfigResponse(ApiModel):
    config_file_path: str
    items: list[ConfigItemDto]
    target_classes: TargetClassPreflightDto


class ConfigSaveRequest(ApiModel):
    values: dict[str, Any] = Field(default_factory=dict)
    actor: str = Field(default="local_operator", min_length=1, max_length=120)


class ConfigSaveResponse(ApiModel):
    saved_keys: list[str]
    config_file_path: str
