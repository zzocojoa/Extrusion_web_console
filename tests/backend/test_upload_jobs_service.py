from pathlib import Path

from backend.app.core.settings import Settings
from backend.app.db.db_delta_repository import DbDeltaEvidenceRepository, decode_delta_scope_json
from backend.app.db.row_attribution_repository import RowAttributionRepository
from backend.app.db.upload_job_repository import UploadJobRepository, decode_json
from backend.app.schemas.upload_jobs import UploadJobStatus
from backend.app.services.upload_jobs import (
    UploadDbEvidenceContext,
    UploadJobService,
    deduplicate_upload_records,
    parse_edge_accepted_rows,
)
from tests.backend.test_upload_jobs_repository_contract import PREVIEW_GATE_SNAPSHOT, create_preview_with_items


DB_HASH = "b" * 64
HMAC_KEY = "fixture-upload-attribution-key"


class FakeUploader:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.batches: list[list[dict[str, object]]] = []

    def upload_batch(self, batch: list[dict[str, object]]) -> int:
        if self.fail:
            raise RuntimeError("edge timeout")
        self.batches.append(batch)
        return len(batch)


class FakeUploadEvidenceDb:
    def __init__(self, counts: list[int] | None = None) -> None:
        self.counts = list(counts or [0, 2])
        self.prepare_calls = 0
        self.counted_keys: list[set[tuple[str, str]]] = []

    def prepare(self) -> UploadDbEvidenceContext:
        self.prepare_calls += 1
        return UploadDbEvidenceContext(
            target_class="loopback_expected_db_port",
            fingerprint_hash=DB_HASH,
        )

    def count_existing_keys(self, keys: set[tuple[str, str]]) -> int:
        self.counted_keys.append(set(keys))
        return self.counts.pop(0)


def prepare_target_job(tmp_path: Path, content: str) -> tuple[UploadJobRepository, str, Path]:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    csv_path = tmp_path / "target.csv"
    csv_path.write_text(content, encoding="utf-8")
    repository = UploadJobRepository(db_path)
    repository.create_job_from_preview(
        job_id="upl_service",
        preview_run_id="prv_done",
        expected_target_rows=2,
        expected_target_files=1,
        options={},
        config_snapshot={},
        preview_gate_snapshot=PREVIEW_GATE_SNAPSHOT,
    )
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


def _upload_settings(db_path: str | Path, **overrides: object) -> Settings:
    return Settings(
        state_db_path=str(db_path),
        supabase_edge_url="http://localhost/upload",
        supabase_anon_key="anon",
        **overrides,
    )


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


def test_default_v2_evidence_gate_does_not_write_upload_delta_or_attribution(tmp_path: Path) -> None:
    repository, job_id, _csv_path = prepare_target_job(
        tmp_path,
        "timestamp,device_id,value\n2026-06-02T09:00:00+09:00,extruder_plc,1\n2026-06-02T09:01:00+09:00,extruder_plc,2\n",
    )
    service = UploadJobService(
        _upload_settings(repository.db_path),
        repository,
        uploader=FakeUploader(),  # type: ignore[arg-type]
        evidence_db_client=FakeUploadEvidenceDb(),  # type: ignore[arg-type]
    )

    service.run_job(job_id)

    with repository.connect() as connection:
        delta_count = connection.execute("SELECT COUNT(*) AS count FROM db_delta_evidence").fetchone()["count"]
        attribution_count = connection.execute("SELECT COUNT(*) AS count FROM row_attribution_ledger").fetchone()["count"]
    assert delta_count == 0
    assert attribution_count == 0


def test_v2_upload_evidence_links_start_audit_delta_and_row_attribution(tmp_path: Path) -> None:
    repository, job_id, _csv_path = prepare_target_job(
        tmp_path,
        "timestamp,device_id,value\n2026-06-02T09:00:00+09:00,extruder_plc,1\n2026-06-02T09:01:00+09:00,extruder_plc,2\n",
    )
    service = UploadJobService(
        _upload_settings(repository.db_path, v2_row_attribution_enabled=True, row_attribution_hmac_key=HMAC_KEY),
        repository,
        uploader=FakeUploader(),  # type: ignore[arg-type]
        evidence_db_client=FakeUploadEvidenceDb([0, 2]),  # type: ignore[arg-type]
    )

    service.run_job(job_id)

    deltas = DbDeltaEvidenceRepository(repository.db_path).list_by_operation(job_id)
    attributions = RowAttributionRepository(repository.db_path).list_by_operation(job_id)
    audit_id = repository.latest_audit_id(job_id, "upload.start")
    assert audit_id is not None
    assert len(deltas) == 1
    assert deltas[0]["operation_type"] == "upload_start"
    assert deltas[0]["audit_id"] == audit_id
    assert deltas[0]["before_count"] == 0
    assert deltas[0]["after_count"] == 2
    assert deltas[0]["expected_delta"] == 2
    assert deltas[0]["actual_delta"] == 2
    assert deltas[0]["result"] == "matched"
    assert decode_delta_scope_json(deltas[0]["delta_scope_json"])["batchKeyCount"] == 2
    assert len(attributions) == 2
    assert {row["audit_id"] for row in attributions} == {audit_id}
    assert {row["db_delta_id"] for row in attributions} == {deltas[0]["delta_id"]}
    assert {row["outcome"] for row in attributions} == {"upsert_accepted"}
    stored_values = "|".join(
        [
            *(str(deltas[0][key]) for key in deltas[0].keys()),
            *(str(row[key]) for row in attributions for key in row.keys()),
        ]
    )
    assert "2026-06-02T09:00:00" not in stored_values
    assert "extruder_plc" not in stored_values


def test_v2_upload_evidence_blocks_before_edge_upload_without_hmac_key(tmp_path: Path) -> None:
    repository, job_id, _csv_path = prepare_target_job(
        tmp_path,
        "timestamp,device_id,value\n2026-06-02T09:00:00+09:00,extruder_plc,1\n",
    )
    uploader = FakeUploader()
    evidence_db = FakeUploadEvidenceDb()
    service = UploadJobService(
        _upload_settings(repository.db_path, v2_row_attribution_enabled=True),
        repository,
        uploader=uploader,  # type: ignore[arg-type]
        evidence_db_client=evidence_db,  # type: ignore[arg-type]
    )

    service.run_job(job_id)

    job = repository.get_job(job_id)
    assert job["status"] == UploadJobStatus.failed.value
    assert job["error_code"] == "row_attribution_hmac_key_missing"
    assert uploader.batches == []
    assert evidence_db.prepare_calls == 0


def test_v2_upload_delta_mismatch_records_unknown_attribution_without_raw_keys(tmp_path: Path) -> None:
    repository, job_id, _csv_path = prepare_target_job(
        tmp_path,
        "timestamp,device_id,value\n2026-06-02T09:00:00+09:00,extruder_plc,1\n2026-06-02T09:01:00+09:00,extruder_plc,2\n",
    )
    service = UploadJobService(
        _upload_settings(repository.db_path, v2_row_attribution_enabled=True, row_attribution_hmac_key=HMAC_KEY),
        repository,
        uploader=FakeUploader(),  # type: ignore[arg-type]
        evidence_db_client=FakeUploadEvidenceDb([0, 1]),  # type: ignore[arg-type]
    )

    service.run_job(job_id)

    job = repository.get_job(job_id)
    deltas = DbDeltaEvidenceRepository(repository.db_path).list_by_operation(job_id)
    attributions = RowAttributionRepository(repository.db_path).list_by_operation(job_id)
    events = repository.list_events(job_id)
    assert job["status"] == UploadJobStatus.succeeded.value
    assert len(deltas) == 1
    assert deltas[0]["result"] == "mismatched"
    assert deltas[0]["expected_delta"] == 2
    assert deltas[0]["actual_delta"] == 1
    assert {row["outcome"] for row in attributions} == {"unknown_requires_reconcile"}
    assert any(event["event_type"] == "upload.evidence_mismatch" for event in events)


def test_deduplicate_upload_records_uses_last_record_for_duplicate_key() -> None:
    result = deduplicate_upload_records(
        [
            {"timestamp": "2026-06-02T09:00:00+09:00", "device_id": "extruder_plc", "temperature": 1},
            {"timestamp": "2026-06-02T09:01:00+09:00", "device_id": "extruder_plc", "temperature": 2},
            {"timestamp": "2026-06-02T09:00:00+09:00", "device_id": "extruder_plc", "temperature": 3},
        ],
    )

    assert result.duplicate_rows == 1
    assert result.records == [
        {"timestamp": "2026-06-02T09:00:00+09:00", "device_id": "extruder_plc", "temperature": 3},
        {"timestamp": "2026-06-02T09:01:00+09:00", "device_id": "extruder_plc", "temperature": 2},
    ]


def test_upload_job_service_deduplicates_duplicate_keys_before_edge_upload(tmp_path: Path) -> None:
    repository, job_id, _csv_path = prepare_target_job(
        tmp_path,
        "\n".join(
            [
                "timestamp,device_id,temperature",
                "2026-06-02T09:00:00+09:00,extruder_plc,1",
                "2026-06-02T09:01:00+09:00,extruder_plc,2",
                "2026-06-02T09:00:00+09:00,extruder_plc,3",
                "",
            ],
        ),
    )
    job_file_id = repository.list_job_files(job_id)[0]["job_file_id"]
    with repository.connect() as connection:
        connection.execute(
            "UPDATE upload_job_files SET row_count = ? WHERE job_file_id = ?",
            (3, job_file_id),
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
    deduplicated = next(event for event in events if event["event_type"] == "file.deduplicated")
    deduplicated_data = decode_json(deduplicated["data_json"], {})
    assert job["status"] == UploadJobStatus.succeeded.value
    assert job["processed_rows"] == 3
    assert job["uploaded_rows"] == 2
    assert job["inserted_rows"] == 2
    assert files[0]["processed_rows"] == 3
    assert files[0]["uploaded_rows"] == 2
    assert files[0]["inserted_rows"] == 2
    assert len(uploader.batches) == 1
    assert len(uploader.batches[0]) == 2
    assert uploader.batches[0][0]["timestamp"] == "2026-06-02T09:00:00+09:00"
    assert uploader.batches[0][0]["temperature"] == 3
    assert deduplicated_data["inputRows"] == 3
    assert deduplicated_data["outputRows"] == 2
    assert deduplicated_data["duplicateRows"] == 1


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
