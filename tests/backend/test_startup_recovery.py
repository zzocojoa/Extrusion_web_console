import logging
import traceback
from pathlib import Path

import pytest

from backend.app.db.runtime_repository import RuntimeRepository
from backend.app.services import startup_recovery


def test_startup_recovery_summary_aggregates_all_repositories(monkeypatch) -> None:
    class FakePreviewRepository:
        def __init__(self, state_db_path: str) -> None:
            assert state_db_path == "synthetic.db"

        def mark_interrupted_active_runs(self) -> int:
            return 1

    class FakeUploadRepository:
        def __init__(self, state_db_path: str) -> None:
            assert state_db_path == "synthetic.db"

        def mark_interrupted_active_jobs(self) -> int:
            return 2

    class FakeDeleteRepository:
        def __init__(self, state_db_path: str) -> None:
            assert state_db_path == "synthetic.db"

        def mark_interrupted_active_delete_runs(self) -> int:
            return 3

    class FakeRuntimeRepository:
        def __init__(self, state_db_path: str) -> None:
            assert state_db_path == "synthetic.db"

        def mark_interrupted_active_operations(self) -> int:
            return 4

    monkeypatch.setattr(startup_recovery, "PreviewRepository", FakePreviewRepository)
    monkeypatch.setattr(startup_recovery, "UploadJobRepository", FakeUploadRepository)
    monkeypatch.setattr(startup_recovery, "UploadDeleteRepository", FakeDeleteRepository)
    monkeypatch.setattr(startup_recovery, "RuntimeRepository", FakeRuntimeRepository)

    summary = startup_recovery.recover_interrupted_work("synthetic.db")

    assert summary.preview_runs == 1
    assert summary.upload_jobs == 2
    assert summary.delete_runs == 3
    assert summary.runtime_operations == 4
    assert summary.total == 10


def test_runtime_startup_recovery_reports_changed_operation_count(tmp_path: Path) -> None:
    repository = RuntimeRepository(tmp_path / "state.db")
    repository.create_operation("rtm_restart", kind="start", config_snapshot={})

    changed = repository.mark_interrupted_active_operations()

    operation = repository.get_operation("rtm_restart")
    assert changed == 1
    assert operation is not None and operation["status"] == "interrupted"
    assert repository.mark_interrupted_active_operations() == 0


def test_startup_recovery_logs_committed_counts_when_later_stage_fails(monkeypatch, caplog) -> None:
    class PreviewRepository:
        def __init__(self, state_db_path: str) -> None:
            pass

        def mark_interrupted_active_runs(self) -> int:
            return 2

    class FailingUploadRepository:
        def __init__(self, state_db_path: str) -> None:
            pass

        def mark_interrupted_active_jobs(self) -> int:
            raise RuntimeError("sensitive-path-must-not-be-logged")

    class UnexpectedRepository:
        def __init__(self, state_db_path: str) -> None:
            raise AssertionError("Recovery must stop at the failing stage")

    monkeypatch.setattr(startup_recovery, "PreviewRepository", PreviewRepository)
    monkeypatch.setattr(startup_recovery, "UploadJobRepository", FailingUploadRepository)
    monkeypatch.setattr(startup_recovery, "UploadDeleteRepository", UnexpectedRepository)
    monkeypatch.setattr(startup_recovery, "RuntimeRepository", UnexpectedRepository)
    caplog.set_level(logging.INFO, logger=startup_recovery.__name__)

    with pytest.raises(startup_recovery.StartupRecoveryError) as raised:
        startup_recovery.recover_interrupted_work("synthetic.db")

    messages = "\n".join(record.getMessage() for record in caplog.records)
    rendered_exception = "".join(traceback.format_exception(raised.value))
    assert "stage=preview_runs changed=2 committed_total=2" in messages
    assert "stage=upload_jobs" in messages
    assert "preview_runs=2" in messages
    assert "committed_total=2" in messages
    assert "error_type=RuntimeError" in messages
    assert "sensitive-path-must-not-be-logged" not in messages
    assert "stage upload_jobs (RuntimeError)" in str(raised.value)
    assert "sensitive-path-must-not-be-logged" not in rendered_exception
