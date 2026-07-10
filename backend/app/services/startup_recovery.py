import logging
from dataclasses import dataclass

from backend.app.db.preview_repository import PreviewRepository
from backend.app.db.runtime_repository import RuntimeRepository
from backend.app.db.upload_delete_repository import UploadDeleteRepository
from backend.app.db.upload_job_repository import UploadJobRepository


_LOGGER = logging.getLogger(__name__)


class StartupRecoveryError(RuntimeError):
    def __init__(self, stage: str, error_type: str) -> None:
        super().__init__(f"Startup interruption recovery failed at stage {stage} ({error_type}).")


@dataclass(frozen=True)
class StartupRecoverySummary:
    preview_runs: int
    upload_jobs: int
    delete_runs: int
    runtime_operations: int

    @property
    def total(self) -> int:
        return self.preview_runs + self.upload_jobs + self.delete_runs + self.runtime_operations


def recover_interrupted_work(state_db_path: str) -> StartupRecoverySummary:
    """Mark stale active work deterministically before the API begins serving."""
    counts = {
        "preview_runs": 0,
        "upload_jobs": 0,
        "delete_runs": 0,
        "runtime_operations": 0,
    }
    steps = (
        ("preview_runs", lambda: PreviewRepository(state_db_path).mark_interrupted_active_runs()),
        ("upload_jobs", lambda: UploadJobRepository(state_db_path).mark_interrupted_active_jobs()),
        ("delete_runs", lambda: UploadDeleteRepository(state_db_path).mark_interrupted_active_delete_runs()),
        ("runtime_operations", lambda: RuntimeRepository(state_db_path).mark_interrupted_active_operations()),
    )
    for stage, recover in steps:
        try:
            counts[stage] = recover()
        except Exception as error:
            _LOGGER.error(
                "Startup interruption recovery failed: stage=%s preview_runs=%d upload_jobs=%d "
                "delete_runs=%d runtime_operations=%d committed_total=%d error_type=%s",
                stage,
                counts["preview_runs"],
                counts["upload_jobs"],
                counts["delete_runs"],
                counts["runtime_operations"],
                sum(counts.values()),
                type(error).__name__,
            )
            raise StartupRecoveryError(stage, type(error).__name__) from None
        _LOGGER.info(
            "Startup interruption recovery stage committed: stage=%s changed=%d committed_total=%d",
            stage,
            counts[stage],
            sum(counts.values()),
        )
    return StartupRecoverySummary(
        preview_runs=counts["preview_runs"],
        upload_jobs=counts["upload_jobs"],
        delete_runs=counts["delete_runs"],
        runtime_operations=counts["runtime_operations"],
    )
