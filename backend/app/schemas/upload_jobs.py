from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field

from backend.app.schemas.upload_preview import ApiModel


class UploadJobMode(str, Enum):
    preview_targets = "preview_targets"
    retry_failed = "retry_failed"


class UploadJobStatus(str, Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    partial_failed = "partial_failed"
    failed = "failed"
    pausing = "pausing"
    paused = "paused"
    cancelling = "cancelling"
    cancelled = "cancelled"
    interrupted = "interrupted"


class UploadJobFileStatus(str, Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    skipped = "skipped"
    cancelled = "cancelled"
    interrupted = "interrupted"


class JobEventLevel(str, Enum):
    debug = "debug"
    info = "info"
    warning = "warning"
    error = "error"


class UploadJobOptions(ApiModel):
    batch_rows: int = Field(default=2000, ge=100, le=10000)
    chunk_rows: int = Field(default=10000, ge=1000, le=100000)
    max_workers: int = Field(default=1, ge=1, le=4)
    http_timeout_seconds: int = Field(default=30, ge=5, le=120)
    retry_attempts: int = Field(default=3, ge=0, le=5)


class UploadJobCreateRequest(ApiModel):
    preview_run_id: str
    mode: UploadJobMode = UploadJobMode.preview_targets
    options: UploadJobOptions = Field(default_factory=UploadJobOptions)


class RetryFailedRequest(ApiModel):
    include_interrupted: bool = True
    include_cancelled: bool = False
    options: UploadJobOptions = Field(default_factory=UploadJobOptions)


class UploadJobCreateResponse(ApiModel):
    job_id: str
    status: UploadJobStatus
    detail_url: str
    events_url: str


class UploadJobSummary(ApiModel):
    total_files: int = 0
    succeeded_files: int = 0
    failed_files: int = 0
    cancelled_files: int = 0
    total_rows: int = 0
    processed_rows: int = 0
    uploaded_rows: int = 0
    inserted_rows: int = 0
    warning_count: int = 0


class UploadJobDto(ApiModel):
    job_id: str
    preview_run_id: str | None = None
    retry_of_job_id: str | None = None
    mode: UploadJobMode
    status: UploadJobStatus
    requested_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    actor: str
    summary: UploadJobSummary
    error_code: str | None = None
    error_message: str | None = None


class UploadJobFileDto(ApiModel):
    job_file_id: int
    job_id: str
    preview_item_id: int | None = None
    file_key: str
    folder_label: str
    folder_path: str
    filename: str
    path: str
    kind: str
    file_date: str | None = None
    file_signature: str
    status: UploadJobFileStatus
    row_count: int | None = None
    processed_rows: int = 0
    uploaded_rows: int = 0
    inserted_rows: int = 0
    resume_offset: int = 0
    retry_count: int = 0
    started_at: datetime | None = None
    finished_at: datetime | None = None
    last_error_code: str | None = None
    last_error_message: str | None = None


class JobEventDto(ApiModel):
    event_id: int
    job_id: str
    seq: int
    ts: datetime
    level: JobEventLevel
    event_type: str
    message: str
    job_file_id: int | None = None
    data: dict[str, Any] = Field(default_factory=dict)


class JobEventCursor(ApiModel):
    latest_seq: int = 0


class UploadJobDetailResponse(ApiModel):
    job: UploadJobDto
    files: list[UploadJobFileDto]
    events: list[JobEventDto]
    event_cursor: JobEventCursor


class UploadJobListResponse(ApiModel):
    jobs: list[UploadJobDto]
    total: int
