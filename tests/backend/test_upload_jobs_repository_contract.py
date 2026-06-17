import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from backend.app.db.preview_repository import PreviewRepository
from backend.app.db.upload_job_repository import UploadJobRepository
from backend.app.schemas.upload_jobs import UploadJobStatus


PREVIEW_GATE_SNAPSHOT = {
    "plc": {"pathClass": "missing", "pathFingerprint": None},
    "temperature": {"pathClass": "missing", "pathFingerprint": None},
    "supabaseDbUrlConfigured": False,
}


def create_preview_with_items(
    db_path: Path,
    *,
    preview_run_id: str = "prv_done",
    include_risky: bool = False,
    config_snapshot: dict | None = None,
) -> None:
    preview = PreviewRepository(str(db_path))
    preview.create_run(
        preview_run_id=preview_run_id,
        range_mode="today",
        start_date=None,
        end_date=None,
        sources=["plc"],
        options={},
        config_snapshot=config_snapshot
        if config_snapshot is not None
        else {
            "previewGate": PREVIEW_GATE_SNAPSHOT,
            "previewProfile": {
                "requestedProfile": "default",
                "appliedProfile": "large_source_operational",
                "autoProfileReason": "operational_source_class",
            },
        },
        retry_of_run_id=None,
    )
    items = [
        ("target", "target.csv"),
        ("partial_overlap", "partial.csv"),
        ("already_in_db", "already.csv"),
        ("excluded", "excluded.csv"),
    ]
    if include_risky:
        items.append(("risky", "risky.csv"))
    for status, filename in items:
        preview.insert_item(
            preview_run_id,
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
    preview.update_run(preview_run_id, status="succeeded", db_status="reachable")


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
        expected_target_rows=2,
        expected_target_files=1,
        options={},
        config_snapshot={},
        preview_gate_snapshot=PREVIEW_GATE_SNAPSHOT,
    )

    assert result.created is True
    job = repository.get_job("upl_test")
    files = repository.list_job_files("upl_test")
    events = repository.list_events("upl_test")
    assert job["status"] == "queued"
    assert job["total_files"] == 1
    assert [row["filename"] for row in files] == ["target.csv"]
    assert events[0]["event_type"] == "job.created"
    event_data = json.loads(events[0]["data_json"])
    assert event_data["expectedTargetRows"] == 2
    assert event_data["actualTargetRows"] == 2
    assert event_data["expectedTargetFiles"] == 1
    assert event_data["actualTargetFiles"] == 1
    with repository.connect() as connection:
        audit = connection.execute("SELECT * FROM audit_log ORDER BY audit_id DESC LIMIT 1").fetchone()
    audit_params = json.loads(audit["params_json_redacted"])
    assert audit_params["expectedTargetRows"] == 2
    assert audit_params["actualTargetRows"] == 2
    assert audit_params["expectedTargetFiles"] == 1
    assert audit_params["actualTargetFiles"] == 1


def test_create_job_from_preview_rejects_non_latest_preview(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path, preview_run_id="prv_old")
    create_preview_with_items(db_path, preview_run_id="prv_latest")
    repository = UploadJobRepository(db_path)

    result = repository.create_job_from_preview(
        job_id="upl_old_preview",
        preview_run_id="prv_old",
        expected_target_rows=2,
        expected_target_files=1,
        options={},
        config_snapshot={},
        preview_gate_snapshot=PREVIEW_GATE_SNAPSHOT,
    )

    assert result.created is False
    assert result.rejection_reason == "preview_not_latest"
    assert repository.get_job("upl_old_preview") is None


def test_create_job_from_preview_rejects_stale_preview(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    with repository.connect() as connection:
        connection.execute(
            """
            UPDATE preview_runs
            SET requested_at = ?, started_at = ?, finished_at = ?, updated_at = ?
            WHERE preview_run_id = ?
            """,
            (
                "2000-01-01T00:00:00+00:00",
                "2000-01-01T00:00:00+00:00",
                "2000-01-01T00:00:01+00:00",
                "2000-01-01T00:00:01+00:00",
                "prv_done",
            ),
        )

    result = repository.create_job_from_preview(
        job_id="upl_stale_preview",
        preview_run_id="prv_done",
        expected_target_rows=2,
        expected_target_files=1,
        options={},
        config_snapshot={},
        preview_gate_snapshot=PREVIEW_GATE_SNAPSHOT,
    )

    assert result.created is False
    assert result.rejection_reason == "preview_stale"
    assert repository.get_job("upl_stale_preview") is None


def test_create_job_from_preview_rejects_risky_preview(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path, include_risky=True)
    repository = UploadJobRepository(db_path)

    result = repository.create_job_from_preview(
        job_id="upl_risky_preview",
        preview_run_id="prv_done",
        expected_target_rows=2,
        expected_target_files=1,
        options={},
        config_snapshot={},
        preview_gate_snapshot=PREVIEW_GATE_SNAPSHOT,
    )

    assert result.created is False
    assert result.rejection_reason == "preview_has_risky_items"
    assert repository.get_job("upl_risky_preview") is None


def test_create_job_from_preview_rejects_expected_target_row_mismatch(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)

    result = repository.create_job_from_preview(
        job_id="upl_row_mismatch",
        preview_run_id="prv_done",
        expected_target_rows=999,
        expected_target_files=1,
        options={},
        config_snapshot={},
        preview_gate_snapshot=PREVIEW_GATE_SNAPSHOT,
    )

    assert result.created is False
    assert result.rejection_reason == "expected_target_rows_mismatch"
    assert result.file_count == 1
    assert result.upload_row_count == 2
    assert repository.get_job("upl_row_mismatch") is None


def test_create_job_from_preview_rejects_expected_target_file_mismatch(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)

    result = repository.create_job_from_preview(
        job_id="upl_file_mismatch",
        preview_run_id="prv_done",
        expected_target_rows=2,
        expected_target_files=2,
        options={},
        config_snapshot={},
        preview_gate_snapshot=PREVIEW_GATE_SNAPSHOT,
    )

    assert result.created is False
    assert result.rejection_reason == "expected_target_files_mismatch"
    assert result.file_count == 1
    assert result.upload_row_count == 2
    assert repository.get_job("upl_file_mismatch") is None


def test_create_job_from_preview_rejects_source_snapshot_mismatch(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)

    result = repository.create_job_from_preview(
        job_id="upl_source_mismatch",
        preview_run_id="prv_done",
        expected_target_rows=2,
        expected_target_files=1,
        options={},
        config_snapshot={},
        preview_gate_snapshot={
            **PREVIEW_GATE_SNAPSHOT,
            "plc": {"pathClass": "network", "pathFingerprint": "different"},
        },
    )

    assert result.created is False
    assert result.rejection_reason == "preview_source_mismatch"
    assert repository.get_job("upl_source_mismatch") is None


def test_create_job_from_preview_rejects_missing_source_snapshot(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path, config_snapshot={})
    repository = UploadJobRepository(db_path)

    result = repository.create_job_from_preview(
        job_id="upl_missing_source_snapshot",
        preview_run_id="prv_done",
        expected_target_rows=2,
        expected_target_files=1,
        options={},
        config_snapshot={},
        preview_gate_snapshot=PREVIEW_GATE_SNAPSHOT,
    )

    assert result.created is False
    assert result.rejection_reason == "preview_source_snapshot_missing"
    assert repository.get_job("upl_missing_source_snapshot") is None


def test_active_job_guard_blocks_second_job(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    repository.create_job_from_preview(
        job_id="upl_active",
        preview_run_id="prv_done",
        expected_target_rows=2,
        expected_target_files=1,
        options={},
        config_snapshot={},
        preview_gate_snapshot=PREVIEW_GATE_SNAPSHOT,
    )

    result = repository.create_job_from_preview(
        job_id="upl_new",
        preview_run_id="prv_done",
        expected_target_rows=2,
        expected_target_files=1,
        options={},
        config_snapshot={},
        preview_gate_snapshot=PREVIEW_GATE_SNAPSHOT,
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
        expected_target_rows=2,
        expected_target_files=1,
        options={},
        config_snapshot={},
        preview_gate_snapshot=PREVIEW_GATE_SNAPSHOT,
    )

    assert result.created is False
    assert result.rejection_reason == "preview_not_uploadable"
    assert repository.get_job("upl_blocked") is None


def test_startup_marks_active_upload_job_interrupted(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    repository.create_job_from_preview(
        job_id="upl_stale",
        preview_run_id="prv_done",
        expected_target_rows=2,
        expected_target_files=1,
        options={},
        config_snapshot={},
        preview_gate_snapshot=PREVIEW_GATE_SNAPSHOT,
    )
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
    repository.create_job_from_preview(
        job_id="upl_cancel",
        preview_run_id="prv_done",
        expected_target_rows=2,
        expected_target_files=1,
        options={},
        config_snapshot={},
        preview_gate_snapshot=PREVIEW_GATE_SNAPSHOT,
    )
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
    repository.create_job_from_preview(
        job_id="upl_interrupted",
        preview_run_id="prv_done",
        expected_target_rows=2,
        expected_target_files=1,
        options={},
        config_snapshot={},
        preview_gate_snapshot=PREVIEW_GATE_SNAPSHOT,
    )
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
    repository.create_job_from_preview(
        job_id="upl_pause",
        preview_run_id="prv_done",
        expected_target_rows=2,
        expected_target_files=1,
        options={},
        config_snapshot={},
        preview_gate_snapshot=PREVIEW_GATE_SNAPSHOT,
    )
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
    repository.create_job_from_preview(
        job_id="upl_events",
        preview_run_id="prv_done",
        expected_target_rows=2,
        expected_target_files=1,
        options={},
        config_snapshot={},
        preview_gate_snapshot=PREVIEW_GATE_SNAPSHOT,
    )

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
    repository.create_job_from_preview(
        job_id="upl_old",
        preview_run_id="prv_done",
        expected_target_rows=2,
        expected_target_files=1,
        options={},
        config_snapshot={},
        preview_gate_snapshot=PREVIEW_GATE_SNAPSHOT,
    )
    file_id = repository.list_job_files("upl_old")[0]["job_file_id"]
    repository.mark_file_failed(file_id, "upload_failed", "boom", 1)
    repository.finish_job("upl_old", status=UploadJobStatus.failed)

    result = repository.create_retry_job(
        job_id="upl_retry",
        source_job_id="upl_old",
        include_interrupted=True,
        include_cancelled=False,
        expected_remaining_rows=1,
        expected_retry_files=1,
        options={},
        config_snapshot={},
    )

    assert result.created is True
    assert result.active_job_id is None
    assert result.file_count == 1
    assert result.remaining_row_count == 1
    retry = repository.get_job("upl_retry")
    files = repository.list_job_files("upl_retry")
    events = repository.list_events("upl_retry", after_seq=0, limit=10)
    assert retry["retry_of_job_id"] == "upl_old"
    assert files[0]["resume_offset"] == 1
    assert files[0]["retry_count"] == 1
    event_data = json.loads(events[0]["data_json"])
    assert event_data["expectedRemainingRows"] == 1
    assert event_data["actualRemainingRows"] == 1
    assert event_data["expectedRetryFiles"] == 1
    assert event_data["actualRetryFiles"] == 1
    with repository.connect() as connection:
        audit = connection.execute("SELECT * FROM audit_log ORDER BY audit_id DESC LIMIT 1").fetchone()
    audit_params = json.loads(audit["params_json_redacted"])
    assert audit_params["expectedRemainingRows"] == 1
    assert audit_params["actualRemainingRows"] == 1
    assert audit_params["expectedRetryFiles"] == 1
    assert audit_params["actualRetryFiles"] == 1


def test_retry_job_rejects_expected_remaining_rows_mismatch(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    repository.create_job_from_preview(
        job_id="upl_old",
        preview_run_id="prv_done",
        expected_target_rows=2,
        expected_target_files=1,
        options={},
        config_snapshot={},
        preview_gate_snapshot=PREVIEW_GATE_SNAPSHOT,
    )
    file_id = repository.list_job_files("upl_old")[0]["job_file_id"]
    repository.mark_file_failed(file_id, "upload_failed", "boom", 1)
    repository.finish_job("upl_old", status=UploadJobStatus.failed)

    result = repository.create_retry_job(
        job_id="upl_retry_mismatch",
        source_job_id="upl_old",
        include_interrupted=True,
        include_cancelled=False,
        expected_remaining_rows=2,
        expected_retry_files=1,
        options={},
        config_snapshot={},
    )

    assert result.created is False
    assert result.rejection_reason == "expected_remaining_rows_mismatch"
    assert result.file_count == 1
    assert result.remaining_row_count == 1
    assert repository.get_job("upl_retry_mismatch") is None


def test_retry_job_rejects_expected_retry_file_mismatch(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    repository.create_job_from_preview(
        job_id="upl_old",
        preview_run_id="prv_done",
        expected_target_rows=2,
        expected_target_files=1,
        options={},
        config_snapshot={},
        preview_gate_snapshot=PREVIEW_GATE_SNAPSHOT,
    )
    file_id = repository.list_job_files("upl_old")[0]["job_file_id"]
    repository.mark_file_failed(file_id, "upload_failed", "boom", 1)
    repository.finish_job("upl_old", status=UploadJobStatus.failed)

    result = repository.create_retry_job(
        job_id="upl_retry_mismatch",
        source_job_id="upl_old",
        include_interrupted=True,
        include_cancelled=False,
        expected_remaining_rows=1,
        expected_retry_files=2,
        options={},
        config_snapshot={},
    )

    assert result.created is False
    assert result.rejection_reason == "expected_retry_files_mismatch"
    assert result.file_count == 1
    assert result.remaining_row_count == 1
    assert repository.get_job("upl_retry_mismatch") is None
