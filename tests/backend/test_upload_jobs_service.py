from pathlib import Path

from backend.app.core.settings import Settings
from backend.app.db.upload_job_repository import UploadJobRepository, decode_json
from backend.app.schemas.upload_jobs import UploadJobStatus
from backend.app.services.upload_jobs import UploadJobService, parse_edge_accepted_rows
from tests.backend.test_upload_jobs_repository_contract import create_preview_with_items


class FakeUploader:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.batches: list[list[dict[str, object]]] = []

    def upload_batch(self, batch: list[dict[str, object]]) -> int:
        if self.fail:
            raise RuntimeError("edge timeout")
        self.batches.append(batch)
        return len(batch)


def prepare_target_job(tmp_path: Path, content: str) -> tuple[UploadJobRepository, str, Path]:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    csv_path = tmp_path / "target.csv"
    csv_path.write_text(content, encoding="utf-8")
    repository = UploadJobRepository(db_path)
    repository.create_job_from_preview(job_id="upl_service", preview_run_id="prv_done", options={}, config_snapshot={})
    file_id = repository.list_job_files("upl_service")[0]["job_file_id"]
    stat = csv_path.stat()
    signature = f"size={stat.st_size}|mtime_ns={stat.st_mtime_ns}"
    with repository.connect() as connection:
        connection.execute(
            """
            UPDATE upload_job_files
            SET path = ?, folder_path = ?, file_signature = ?
            WHERE job_file_id = ?
            """,
            (str(csv_path), str(tmp_path), signature, file_id),
        )
    return repository, "upl_service", csv_path


def test_upload_job_service_uploads_preview_targets_and_disables_smart_sync(tmp_path: Path) -> None:
    repository, job_id, _csv_path = prepare_target_job(
        tmp_path,
        "timestamp,device_id,value\n2026-06-02T09:00:00+09:00,extruder_plc,1\n2026-06-02T09:01:00+09:00,extruder_plc,2\n",
    )
    uploader = FakeUploader()
    service = UploadJobService(
        Settings(supabase_edge_url="http://localhost/upload", supabase_anon_key="anon"),
        repository,
        uploader=uploader,  # type: ignore[arg-type]
    )

    service.run_job(job_id)

    job = repository.get_job(job_id)
    files = repository.list_job_files(job_id)
    events = repository.list_events(job_id)
    assert job["status"] == UploadJobStatus.succeeded.value
    assert job["inserted_rows"] == 2
    assert files[0]["status"] == "succeeded"
    assert files[0]["uploaded_rows"] == 2
    assert files[0]["inserted_rows"] == 2
    assert uploader.batches[0][0]["timestamp"] == "2026-06-02T09:00:00+09:00"
    assert all(event["event_type"] != "smart_sync.filtered" for event in events)
    completed = next(event for event in events if event["event_type"] == "file.succeeded")
    completed_data = decode_json(completed["data_json"], {})
    assert completed_data["acceptedRows"] == 2
    assert completed_data["insertedRows"] == 2


def test_parse_edge_accepted_rows_prefers_canonical_count() -> None:
    payload = {"accepted": 4, "upserted": 3, "inserted": 2}

    assert parse_edge_accepted_rows(payload) == 4


def test_parse_edge_accepted_rows_falls_back_to_upserted_then_legacy_inserted() -> None:
    assert parse_edge_accepted_rows({"upserted": "3", "inserted": 2}) == 3
    assert parse_edge_accepted_rows({"inserted": "2"}) == 2
    assert parse_edge_accepted_rows({"accepted": "bad", "upserted": "3"}) == 3
    assert parse_edge_accepted_rows({}) == 0


def test_upload_job_service_records_file_failure_without_silent_exit(tmp_path: Path) -> None:
    repository, job_id, _csv_path = prepare_target_job(
        tmp_path,
        "timestamp,device_id,value\n2026-06-02T09:00:00+09:00,extruder_plc,1\n",
    )
    service = UploadJobService(
        Settings(supabase_edge_url="http://localhost/upload", supabase_anon_key="anon"),
        repository,
        uploader=FakeUploader(fail=True),  # type: ignore[arg-type]
    )

    service.run_job(job_id)

    job = repository.get_job(job_id)
    files = repository.list_job_files(job_id)
    events = repository.list_events(job_id)
    assert job["status"] == UploadJobStatus.failed.value
    assert files[0]["status"] == "failed"
    assert files[0]["last_error_code"] == "upload_failed"
    assert any(event["event_type"] == "file.failed" for event in events)
    assert any(event["event_type"] == "job.failed" for event in events)


def test_upload_job_service_blocks_changed_file_since_preview(tmp_path: Path) -> None:
    repository, job_id, csv_path = prepare_target_job(
        tmp_path,
        "timestamp,device_id,value\n2026-06-02T09:00:00+09:00,extruder_plc,1\n",
    )
    csv_path.write_text(
        "timestamp,device_id,value\n2026-06-02T09:00:00+09:00,extruder_plc,1\n2026-06-02T09:01:00+09:00,extruder_plc,2\n",
        encoding="utf-8",
    )
    uploader = FakeUploader()
    service = UploadJobService(
        Settings(supabase_edge_url="http://localhost/upload", supabase_anon_key="anon"),
        repository,
        uploader=uploader,  # type: ignore[arg-type]
    )

    service.run_job(job_id)

    job = repository.get_job(job_id)
    files = repository.list_job_files(job_id)
    assert job["status"] == UploadJobStatus.failed.value
    assert files[0]["last_error_code"] == "file_changed_since_preview"
    assert uploader.batches == []
