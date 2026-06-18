from datetime import date, datetime
from enum import Enum
from typing import Literal

from pydantic import Field, model_validator

from backend.app.schemas.upload_preview import ApiModel


class DeletePreflightStatus(str, Enum):
    ready = "ready"
    blocked = "blocked"
    expired = "expired"


class DeleteRunStatus(str, Enum):
    preparing = "preparing"
    running = "running"
    finalizing = "finalizing"
    blocked = "blocked"
    failed = "failed"
    succeeded = "succeeded"
    commit_unknown = "commit_unknown"
    reconciling = "reconciling"
    reconciled_succeeded = "reconciled_succeeded"
    reconciled_rolled_back = "reconciled_rolled_back"
    reconciliation_failed = "reconciliation_failed"


class DeleteRunItemStatus(str, Enum):
    pending = "pending"
    deleted = "deleted"
    blocked = "blocked"
    failed = "failed"
    unknown = "unknown"


class DeleteDbTargetGuard(ApiModel):
    status: Literal["passed", "blocked"]
    target_class: str
    fingerprint_hash: str | None = None
    reason_code: str | None = None


class DeletePreflightRequest(ApiModel):
    preview_run_id: str
    preview_item_ids: list[int] = Field(default_factory=list, min_length=1)
    expected_already_in_db_items: int = Field(ge=1)
    timestamp_start_date: date | None = None
    timestamp_end_date: date | None = None

    @model_validator(mode="after")
    def validate_timestamp_date_scope(self) -> "DeletePreflightRequest":
        if (self.timestamp_start_date is None) != (self.timestamp_end_date is None):
            raise ValueError("timestampStartDate and timestampEndDate must be supplied together")
        if self.timestamp_start_date and self.timestamp_end_date and self.timestamp_end_date < self.timestamp_start_date:
            raise ValueError("timestampEndDate must be on or after timestampStartDate")
        return self


class DeletePreflightResponse(ApiModel):
    preflight_id: str
    status: DeletePreflightStatus
    selected_item_count: int
    selected_key_count: int
    rollback_ready: bool
    rollback_blockers: list[str] = Field(default_factory=list)
    db_target_guard: DeleteDbTargetGuard
    selection_hash: str
    keyset_hash: str
    expires_at: datetime
    reason_code: str | None = None
    timestamp_start_date: date | None = None
    timestamp_end_date: date | None = None


class DeleteJobCreateRequest(ApiModel):
    preflight_id: str
    expected_delete_keys: int = Field(ge=1)
    typed_delete_keys: str
    acknowledge_no_undo: bool
    acknowledge_rollback_requires_fresh_preview_and_start_upload: bool


class DeleteJobCreateResponse(ApiModel):
    delete_run_id: str
    status: DeleteRunStatus
    expected_delete_keys: int
    deleted_keys: int
    rollback_ready: bool
    recovery_required: bool
    raw_keys_returned: bool = False


class DeleteJobDto(ApiModel):
    delete_run_id: str
    preflight_id: str
    preview_run_id: str
    status: DeleteRunStatus
    expected_delete_keys: int
    deleted_keys: int
    rollback_ready: bool
    recovery_required: bool
    db_fingerprint_hash: str | None = None
    selection_hash: str | None = None
    keyset_hash: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class DeleteJobLatestResponse(ApiModel):
    job: DeleteJobDto
    active_delete_blocker: bool


class DeleteReconcileRequest(ApiModel):
    acknowledge_reconciliation_retry: bool = False


class DeleteReconcileResponse(ApiModel):
    delete_run_id: str
    status: DeleteRunStatus
    expected_delete_keys: int
    keys_present: int
    keys_absent: int
    recovery_required: bool
    raw_keys_returned: bool = False
