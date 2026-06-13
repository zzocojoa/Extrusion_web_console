from typing import Literal

from backend.app.schemas.upload_preview import ApiModel


StateContextClass = Literal[
    "operator_package",
    "development_default",
    "qa_temporary",
    "configured",
    "unknown",
    "inaccessible",
]
StateStorageStatus = Literal["present", "missing", "inaccessible", "unknown"]
StateContextSource = Literal["default", "env", "init", "unknown"]


class StateContextDto(ApiModel):
    context_class: StateContextClass
    label: str
    storage_status: StateStorageStatus
    source: StateContextSource


def unknown_state_context() -> StateContextDto:
    return StateContextDto(
        context_class="unknown",
        label="Unknown state",
        storage_status="unknown",
        source="unknown",
    )
