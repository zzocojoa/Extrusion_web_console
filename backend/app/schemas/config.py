from typing import Any

from pydantic import Field

from backend.app.schemas.state_context import StateContextDto
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


class FeatureGateDto(ApiModel):
    key: str
    enabled: bool
    source: str
    mutable: bool = False
    required_role: str | None = None
    status: str
    reason: str


class FeatureGatesDto(ApiModel):
    v2_delete_expansion: FeatureGateDto
    v2_date_scoped_delete_ui: FeatureGateDto
    v2_lan_access: FeatureGateDto


class ConfigResponse(ApiModel):
    config_file_path: str
    items: list[ConfigItemDto]
    feature_gates: FeatureGatesDto
    target_classes: TargetClassPreflightDto
    state_context: StateContextDto


class ConfigSaveRequest(ApiModel):
    values: dict[str, Any] = Field(default_factory=dict)
    actor: str = Field(default="local_operator", min_length=1, max_length=120)


class ConfigSaveResponse(ApiModel):
    saved_keys: list[str]
    config_file_path: str
