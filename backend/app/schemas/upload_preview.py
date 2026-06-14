from datetime import date, datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")


class PreviewRangeMode(str, Enum):
    today = "today"
    yesterday = "yesterday"
    last_2_days = "last_2_days"
    custom = "custom"


class PreviewSource(str, Enum):
    plc = "plc"
    temperature = "temperature"


class PreviewProfile(str, Enum):
    default = "default"
    stage3_profile_a_bounded_full_scan = "stage3_profile_a_bounded_full_scan"


STAGE3_PROFILE_A_BOUNDED_MAX_FILES = 3
STAGE3_PROFILE_A_BOUNDED_MAX_RUN_SECONDS = 300
STAGE3_PROFILE_A_BOUNDED_MAX_FILE_SECONDS = 120


class PreviewOptions(ApiModel):
    profile: PreviewProfile = PreviewProfile.default
    stable_lag_minutes: int = Field(default=3, ge=0, le=60)
    sample_rows: int = Field(default=200, ge=20, le=2000)
    chunk_rows: int = Field(default=20000, ge=1000, le=100000)
    max_files: int = Field(default=500, ge=1, le=5000)
    max_run_seconds: int = Field(default=120, ge=10, le=900)
    max_file_seconds: int = Field(default=30, ge=5, le=300)
    force_full_scan: bool = False

    @model_validator(mode="before")
    @classmethod
    def apply_profile_defaults(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        profile = data.get("profile", PreviewProfile.default.value)
        profile_value = profile.value if isinstance(profile, PreviewProfile) else str(profile)
        if profile_value != PreviewProfile.stage3_profile_a_bounded_full_scan.value:
            return data

        values = dict(data)

        def set_option(snake_name: str, camel_name: str, value: Any) -> None:
            if snake_name in values and camel_name not in values:
                values[snake_name] = value
            else:
                values[camel_name] = value

        set_option("force_full_scan", "forceFullScan", True)
        set_option("max_files", "maxFiles", STAGE3_PROFILE_A_BOUNDED_MAX_FILES)
        set_option("max_run_seconds", "maxRunSeconds", STAGE3_PROFILE_A_BOUNDED_MAX_RUN_SECONDS)
        set_option("max_file_seconds", "maxFileSeconds", STAGE3_PROFILE_A_BOUNDED_MAX_FILE_SECONDS)
        return values


class PreviewCreateRequest(ApiModel):
    range_mode: PreviewRangeMode
    start_date: date | None = None
    end_date: date | None = None
    sources: list[PreviewSource] = Field(default_factory=lambda: [PreviewSource.plc])
    options: PreviewOptions = Field(default_factory=PreviewOptions)
    retry_of_run_id: str | None = None

    @model_validator(mode="after")
    def validate_date_range(self) -> "PreviewCreateRequest":
        if self.range_mode == PreviewRangeMode.custom:
            if self.start_date is None or self.end_date is None:
                raise ValueError("custom rangeMode requires startDate and endDate")
            if self.end_date < self.start_date:
                raise ValueError("endDate must be on or after startDate")
        return self


class PreviewItemStatus(str, Enum):
    target = "target"
    already_in_db = "already_in_db"
    partial_overlap = "partial_overlap"
    risky = "risky"
    excluded = "excluded"


class PreviewRunStatus(str, Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    partial_failed = "partial_failed"
    failed = "failed"
    cancelling = "cancelling"
    cancelled = "cancelled"
    timed_out = "timed_out"


class PreviewDbStatus(str, Enum):
    not_checked = "not_checked"
    reachable = "reachable"
    unreachable = "unreachable"
    query_failed = "query_failed"


class PreviewCreateResponse(ApiModel):
    preview_run_id: str
    status: PreviewRunStatus
    poll_url: str


class PreviewCancelResponse(ApiModel):
    preview_run_id: str
    status: PreviewRunStatus


class PreviewRunSummary(ApiModel):
    total: int = 0
    target: int = 0
    already_in_db: int = 0
    partial_overlap: int = 0
    risky: int = 0
    excluded: int = 0
    upload_rows: int = 0
    db_matched_rows: int = 0


class PreviewRunDto(ApiModel):
    preview_run_id: str
    status: PreviewRunStatus
    requested_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    db_status: PreviewDbStatus
    summary: PreviewRunSummary
    warnings: list[str] = Field(default_factory=list)
    timeout_stage: str | None = None
    timing: dict[str, Any] = Field(default_factory=dict)
    error_code: str | None = None
    error_message: str | None = None
    retry_of_run_id: str | None = None


class PreviewItemDto(ApiModel):
    preview_item_id: int
    status: PreviewItemStatus
    reason_code: str
    reason_text: str
    kind: PreviewSource
    folder_label: str
    filename: str
    path: str
    file_date: date | None = None
    size_bytes: int | None = None
    modified_at: datetime | None = None
    scan_mode: Literal["metadata", "sample", "full", "incomplete"]
    sample_row_count: int | None = None
    row_count: int | None = None
    local_key_count: int | None = None
    db_match_count: int | None = None
    upload_row_estimate: int | None = None
    first_timestamp: str | None = None
    last_timestamp: str | None = None
    device_ids: list[str] = Field(default_factory=list)
    issues: list[Any] = Field(default_factory=list)
    timeout_stage: str | None = None
    timing: dict[str, Any] = Field(default_factory=dict)
    error_code: str | None = None
    error_message: str | None = None


class PreviewPage(ApiModel):
    limit: int
    offset: int
    total_items: int


class PreviewDetailResponse(ApiModel):
    run: PreviewRunDto
    items: list[PreviewItemDto]
    page: PreviewPage


PreviewPageDto = PreviewPage
PreviewRunDetailResponse = PreviewDetailResponse
