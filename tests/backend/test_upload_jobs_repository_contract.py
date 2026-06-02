from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from backend.app.db.preview_repository import PreviewRepository
from backend.app.db.upload_job_repository import UploadJobRepository
from backend.app.schemas.upload_jobs import UploadJobStatus


def create_preview_with_items(db_path: Path) -> None:
    preview = PreviewRepository(str(db_path))
    preview.create_run(
        preview_run_id="prv_done",
        range_mode="today",
        start_date=None,
        end_date=None,
        sources=["plc"],
        options={},
        config_snapshot={},
        retry_of_run_id=None,
    )
    for status, filename in [
        ("target", "target.csv"),
        ("risky", "risky.csv"),
        ("partial_overlap", "partial.csv"),
        ("already_in_db", "already.csv"),
        ("excluded", "excluded.csv"),
    ]:
        preview.insert_item(
            "prv_done",
            {
                "file_key": f"key-{filename}",
                "folder_label": "PLC",
                "folder_path": "C:\\data\\plc",
                "filename": filename,
                "path": f"C:\\data\\plc\\{filename}",
                "kind": "plc",
                "file_date": "2026-06-02",
                "size_bytes": 100,
                "mtime_ns": 1,
                "modified_at": "2026-06-02T09:00:00+09:00",
                "file_signature": "sig",
                "status": status,
                "reason_code": "db_no_match",
                "reason_text": "test",
                "scan_mode": "full",
                "sample_row_count": 1,
                "row_count": 2,
                "local_key_count": 2,
                "db_match_count": 0,
                "upload_row_estimate": 2,
                "first_timestamp": "2026-06-02T09:00:00+09:00",
                "last_timestamp": "2026-06-02T09:01:00+09:00",
                "device_ids": ["extruder_plc"],
                "issues": [],
                "error_code": None,
                "error_message": None,
            },
        )
    preview.update_run("prv_done", status="succeeded", db_status="reachable")


def test_upload_job_repository_initializes_required_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    repository = UploadJobRepository(db_path)

    repository.ensure_schema()

    with repository.connect() as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
    assert {"upload_jobs", "upload_job_files", "upload_file_state", "job_events", "audit_log"}.issubset(tables)


def test_create_job_from_preview_snapshots_only_target_items(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)

    result = repository.create_job_from_preview(
        job_id="upl_test",
        preview_run_id="prv_done",
        options={},
        config_snapshot={},
    )

    assert result.created is True
    job = repository.get_job("upl_test")
    files = repository.list_job_files("upl_test")
    events = repository.list_events("upl_test")
    assert job["status"] == "queued"
    assert job["total_files"] == 1
    assert [row["filename"] for row in files] == ["target.csv"]
    assert events[0]["event_type"] == "job.created"


def test_active_job_guard_blocks_second_job(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    repository.create_job_from_preview(job_id="upl_active", preview_run_id="prv_done", options={}, config_snapshot={})

    result = repository.create_job_from_preview(
        job_id="upl_new",
        preview_run_id="prv_done",
        options={},
        config_snapshot={},
    )

    assert result.active_job_id == "upl_active"
    assert repository.get_job("upl_new") is None


def test_create_job_from_preview_revalidates_preview_state_inside_transaction(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    PreviewRepository(str(db_path)).update_run("prv_done", status="partial_failed", db_status="unreachable")

    result = repository.create_job_from_preview(
        job_id="upl_blocked",
        preview_run_id="prv_done",
        options={},
        config_snapshot={},
    )

    assert result.created is False
    assert result.rejection_reason == "preview_not_uploadable"
    assert repository.get_job("upl_blocked") is None


def test_startup_marks_active_upload_job_interrupted(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    repository.create_job_from_preview(job_id="upl_stale", preview_run_id="prv_done", options={}, config_snapshot={})
    repository.start_job("upl_stale")

    changed = repository.mark_interrupted_active_jobs()

    job = repository.get_job("upl_stale")
    files = repository.list_job_files("upl_stale")
    events = repository.list_events("upl_stale")
    assert changed == 1
    assert job["status"] == "interrupted"
    assert files[0]["status"] == "interrupted"
    assert events[-1]["event_type"] == "job.interrupted"


def test_finish_job_does_not_overwrite_cancel_requested_job(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    repository.create_job_from_preview(job_id="upl_cancel", preview_run_id="prv_done", options={}, config_snapshot={})
    repository.start_job("upl_cancel")
    repository.request_cancel("upl_cancel")

    changed = repository.finish_job("upl_cancel", UploadJobStatus.succeeded)

    job = repository.get_job("upl_cancel")
    assert changed is True
    assert job["status"] == "cancelled"


def test_finish_job_does_not_overwrite_terminal_interrupted_job(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    repository.create_job_from_preview(job_id="upl_interrupted", preview_run_id="prv_done", options={}, config_snapshot={})
    repository.start_job("upl_interrupted")
    repository.mark_interrupted_active_jobs()

    changed = repository.finish_job("upl_interrupted", UploadJobStatus.succeeded)

    job = repository.get_job("upl_interrupted")
    assert changed is False
    assert job["status"] == "interrupted"


def test_mark_paused_is_idempotent_and_does_not_duplicate_events(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    repository.create_job_from_preview(job_id="upl_pause", preview_run_id="prv_done", options={}, config_snapshot={})
    repository.start_job("upl_pause")
    repository.request_pause("upl_pause")

    repository.mark_paused("upl_pause")
    repository.mark_paused("upl_pause")

    events = repository.list_events("upl_pause")
    paused_events = [event for event in events if event["event_type"] == "job.paused"]
    assert len(paused_events) == 1
    assert repository.request_pause("upl_pause") == UploadJobStatus.paused


def test_append_event_assigns_unique_monotonic_seq_under_concurrent_writers(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    repository.create_job_from_preview(job_id="upl_events", preview_run_id="prv_done", options={}, config_snapshot={})

    def append(index: int) -> int:
        return repository.append_event(
            "upl_events",
            event_type="log.info",
            level="info",
            message=f"event {index}",
        )

    with ThreadPoolExecutor(max_workers=8) as pool:
        seqs = list(pool.map(append, range(40)))

    events = repository.list_events("upl_events", after_seq=0, limit=100)
    all_seqs = [event["seq"] for event in events]
    assert len(seqs) == 40
    assert len(all_seqs) == len(set(all_seqs))
    assert all_seqs == sorted(all_seqs)


def test_retry_job_snapshots_failed_files_only(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    repository.create_job_from_preview(job_id="upl_old", preview_run_id="prv_done", options={}, config_snapshot={})
    file_id = repository.list_job_files("upl_old")[0]["job_file_id"]
    repository.mark_file_failed(file_id, "upload_failed", "boom", 1)
    repository.finish_job("upl_old", status=UploadJobStatus.failed)

    active, count = repository.create_retry_job(
        job_id="upl_retry",
        source_job_id="upl_old",
        include_interrupted=True,
        include_cancelled=False,
        options={},
        config_snapshot={},
    )

    assert active is None
    assert count == 1
    retry = repository.get_job("upl_retry")
    files = repository.list_job_files("upl_retry")
    assert retry["retry_of_job_id"] == "upl_old"
    assert files[0]["resume_offset"] == 1
    assert files[0]["retry_count"] == 1
