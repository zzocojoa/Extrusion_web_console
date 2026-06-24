from __future__ import annotations

import itertools
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from backend.app.core.settings import Settings
from backend.app.db.audit_repository import AuditLogFilters, AuditRepository, decode_params_json
from backend.app.db.preview_repository import PreviewRepository
from backend.app.schemas.upload_preview import PreviewCreateRequest, PreviewOptions
from backend.app.services.upload_preview import (
    CandidateScanner,
    CsvKeyExtractor,
    PreviewCancelledError,
    PreviewDbUnavailableError,
    ReconciliationProgress,
    PreviewSchemaMismatchError,
    PreviewService,
    classify_reconciliation,
    date_window,
)


FIXTURES = Path(__file__).parent / "fixtures"


class FakeReconciler:
    def __init__(self, matched_keys: set[tuple[str, str]] | None = None, fail: bool = False) -> None:
        self.matched_keys = matched_keys or set()
        self.fail = fail
        self.seen_keys: set[tuple[str, str]] = set()

    def find_existing_keys(self, keys: set[tuple[str, str]], **_kwargs) -> set[tuple[str, str]]:
        self.seen_keys = set(keys)
        if self.fail:
            raise PreviewDbUnavailableError("database down")
        return set(keys) & self.matched_keys


class TimeoutReconciler:
    def __init__(self) -> None:
        self.last_progress = ReconciliationProgress(
            strategy="temp_table",
            total_keys=2,
            batch_size=2,
            total_batches=1,
            batches_completed=1,
            keys_staged=2,
            stage="join_all_metrics",
        )

    def find_existing_keys(self, keys: set[tuple[str, str]], **_kwargs) -> set[tuple[str, str]]:
        self.last_progress.total_keys = len(keys)
        raise TimeoutError("Preview run exceeded the configured time limit")


class SchemaMismatchExtractor:
    def extract(self, *_args, **_kwargs):
        raise PreviewSchemaMismatchError("missing required columns")


class TransformErrorExtractor:
    def extract(self, *_args, **_kwargs):
        raise ValueError("bad transform")


def write_csv(path: Path, rows: list[str]) -> None:
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    old_mtime = datetime.now().timestamp() - 600
    os.utime(path, (old_mtime, old_mtime))


def copy_fixture(source_name: str, destination: Path) -> None:
    destination.write_text((FIXTURES / source_name).read_text(encoding="utf-8"), encoding="utf-8")
    old_mtime = datetime.now().timestamp() - 600
    os.utime(destination, (old_mtime, old_mtime))


def test_date_window_modes_are_exact_kst_days() -> None:
    now = datetime.fromisoformat("2026-06-01T10:00:00+09:00")

    today = PreviewCreateRequest.model_validate({"rangeMode": "today", "sources": ["plc"]})
    assert date_window(today, now=now) == (now.date(), now.date())

    last_two = PreviewCreateRequest.model_validate({"rangeMode": "last_2_days", "sources": ["plc"]})
    assert date_window(last_two, now=now) == (now.date() - timedelta(days=1), now.date())

    last_seven = PreviewCreateRequest.model_validate({"rangeMode": "last_7_days", "sources": ["plc"]})
    assert date_window(last_seven, now=now) == (now.date() - timedelta(days=6), now.date())

    last_thirty = PreviewCreateRequest.model_validate({"rangeMode": "last_30_days", "sources": ["plc"]})
    assert date_window(last_thirty, now=now) == (now.date() - timedelta(days=29), now.date())

    folder_all = PreviewCreateRequest.model_validate({"rangeMode": "folder_all", "sources": ["plc"]})
    assert date_window(folder_all, now=now) == (None, None)


def test_candidate_scanner_uses_configured_folder_and_no_legacy_state(tmp_path: Path) -> None:
    plc_dir = tmp_path / "plc"
    plc_dir.mkdir()
    write_csv(
        plc_dir / "Factory_Integrated_Log_20260601_090000.csv",
        ["Date,Time,Mold1", "2026-06-01,09:00:00,1"],
    )
    write_csv(
        plc_dir / "Factory_Integrated_Log_20260530_090000.csv",
        ["Date,Time,Mold1", "2026-05-30,09:00:00,1"],
    )
    (tmp_path / "uploader_state.db").write_text("not used", encoding="utf-8")
    (tmp_path / "processed_files.log").write_text("not used", encoding="utf-8")

    request = PreviewCreateRequest.model_validate(
        {
            "rangeMode": "custom",
            "startDate": "2026-06-01",
            "endDate": "2026-06-01",
            "sources": ["plc"],
            "options": {"stableLagMinutes": 0},
        }
    )
    scanner = CandidateScanner(Settings(plc_data_dir=str(plc_dir)))

    candidates, issues = scanner.scan(request)

    assert [candidate.path.name for candidate in candidates] == [
        "Factory_Integrated_Log_20260601_090000.csv"
    ]
    assert {issue["reason_code"] for issue in issues} == {"outside_date_range"}


def test_candidate_scanner_folder_all_keeps_file_date_rules_without_date_exclusion(
    tmp_path: Path,
) -> None:
    plc_dir = tmp_path / "plc"
    plc_dir.mkdir()
    write_csv(
        plc_dir / "Factory_Integrated_Log_20260601_090000.csv",
        ["Date,Time,Mold1", "2026-06-01,09:00:00,1"],
    )
    write_csv(
        plc_dir / "Factory_Integrated_Log_20250101_090000.csv",
        ["Date,Time,Mold1", "2025-01-01,09:00:00,1"],
    )
    write_csv(plc_dir / "no_date.csv", ["Date,Time,Mold1", "2026-06-01,09:00:00,1"])

    request = PreviewCreateRequest.model_validate(
        {
            "rangeMode": "folder_all",
            "sources": ["plc"],
            "options": {"stableLagMinutes": 0},
        }
    )
    scanner = CandidateScanner(Settings(plc_data_dir=str(plc_dir)))

    candidates, issues = scanner.scan(request)

    assert {candidate.path.name for candidate in candidates} == {
        "Factory_Integrated_Log_20260601_090000.csv",
        "Factory_Integrated_Log_20250101_090000.csv",
    }
    assert {issue["reason_code"] for issue in issues} == {"file_date_missing"}


def test_candidate_scanner_caps_excluded_rows_without_dropping_in_range_file(tmp_path: Path) -> None:
    plc_dir = tmp_path / "plc"
    plc_dir.mkdir()
    for day in ("20260527", "20260528", "20260529"):
        write_csv(
            plc_dir / f"Factory_Integrated_Log_{day}_090000.csv",
            ["Date,Time,Mold1", "2026-05-27,09:00:00,1"],
        )
    write_csv(
        plc_dir / "Factory_Integrated_Log_20260601_090000.csv",
        ["Date,Time,Mold1", "2026-06-01,09:00:00,1"],
    )
    request = PreviewCreateRequest.model_validate(
        {
            "rangeMode": "custom",
            "startDate": "2026-06-01",
            "endDate": "2026-06-01",
            "sources": ["plc"],
            "options": {"stableLagMinutes": 0, "maxFiles": 2},
        }
    )

    candidates, issues = CandidateScanner(Settings(plc_data_dir=str(plc_dir))).scan(request)

    assert [candidate.path.name for candidate in candidates] == [
        "Factory_Integrated_Log_20260601_090000.csv"
    ]
    assert len(issues) == 2
    assert {issue["reason_code"] for issue in issues} == {"outside_date_range"}


def test_csv_key_extractor_streams_integrated_plc_keys(tmp_path: Path) -> None:
    plc_dir = tmp_path / "plc"
    plc_dir.mkdir()
    csv_path = plc_dir / "Factory_Integrated_Log_20260601_090000.csv"
    write_csv(
        csv_path,
        [
            "Date,Time,Mold1",
            "2026-06-01,09:00:00,1",
            "2026-06-01,09:00:00,1",
            "2026-06-01,09:01:00,2",
        ],
    )
    request = PreviewCreateRequest.model_validate(
        {
            "rangeMode": "custom",
            "startDate": "2026-06-01",
            "endDate": "2026-06-01",
            "sources": ["plc"],
            "options": {"stableLagMinutes": 0},
        }
    )
    candidate = CandidateScanner(Settings(plc_data_dir=str(plc_dir))).scan(request)[0][0]

    result = CsvKeyExtractor().extract(
        candidate,
        max_file_seconds=5,
        sample_rows=2,
        force_full_scan=False,
    )

    assert result.row_count == 3
    assert result.sample_row_count == 2
    assert result.device_ids == ["extruder_integrated"]
    assert result.local_keys == {
        ("2026-06-01T09:00:00.000000+09:00", "extruder_integrated"),
        ("2026-06-01T09:01:00.000000+09:00", "extruder_integrated"),
    }


def test_csv_key_extractor_throttles_cancel_checks(tmp_path: Path, monkeypatch) -> None:
    plc_dir = tmp_path / "plc"
    plc_dir.mkdir()
    csv_path = plc_dir / "Factory_Integrated_Log_20260601_090000.csv"
    rows = ["Date,Time,Mold1"]
    rows.extend(f"2026-06-01,09:{index % 60:02d}:00,{index}" for index in range(2505))
    write_csv(csv_path, rows)
    request = PreviewCreateRequest.model_validate(
        {
            "rangeMode": "custom",
            "startDate": "2026-06-01",
            "endDate": "2026-06-01",
            "sources": ["plc"],
            "options": {"stableLagMinutes": 0},
        }
    )
    candidate = CandidateScanner(Settings(plc_data_dir=str(plc_dir))).scan(request)[0][0]
    cancel_checks = 0

    def should_cancel() -> bool:
        nonlocal cancel_checks
        cancel_checks += 1
        return False

    monkeypatch.setattr("backend.app.services.upload_preview.time.monotonic", lambda: 0.0)

    result = CsvKeyExtractor().extract(
        candidate,
        max_file_seconds=5,
        sample_rows=200,
        force_full_scan=False,
        should_cancel=should_cancel,
    )

    assert result.row_count == 2505
    assert cancel_checks == 3


def test_csv_key_extractor_honors_throttled_cancel_check(tmp_path: Path, monkeypatch) -> None:
    plc_dir = tmp_path / "plc"
    plc_dir.mkdir()
    csv_path = plc_dir / "Factory_Integrated_Log_20260601_090000.csv"
    rows = ["Date,Time,Mold1"]
    rows.extend(f"2026-06-01,09:{index % 60:02d}:00,{index}" for index in range(1500))
    write_csv(csv_path, rows)
    request = PreviewCreateRequest.model_validate(
        {
            "rangeMode": "custom",
            "startDate": "2026-06-01",
            "endDate": "2026-06-01",
            "sources": ["plc"],
            "options": {"stableLagMinutes": 0},
        }
    )
    candidate = CandidateScanner(Settings(plc_data_dir=str(plc_dir))).scan(request)[0][0]
    cancel_checks = 0

    def should_cancel() -> bool:
        nonlocal cancel_checks
        cancel_checks += 1
        return cancel_checks >= 2

    monkeypatch.setattr("backend.app.services.upload_preview.time.monotonic", lambda: 0.0)

    try:
        CsvKeyExtractor().extract(
            candidate,
            max_file_seconds=5,
            sample_rows=200,
            force_full_scan=False,
            should_cancel=should_cancel,
        )
    except PreviewCancelledError:
        pass
    else:
        raise AssertionError("Expected throttled cancel check to cancel extraction")

    assert cancel_checks == 2


def test_csv_key_extractor_honors_time_based_cancel_check(tmp_path: Path, monkeypatch) -> None:
    plc_dir = tmp_path / "plc"
    plc_dir.mkdir()
    csv_path = plc_dir / "Factory_Integrated_Log_20260601_090000.csv"
    write_csv(
        csv_path,
        [
            "Date,Time,Mold1",
            "2026-06-01,09:00:00,1",
            "2026-06-01,09:01:00,2",
            "2026-06-01,09:02:00,3",
        ],
    )
    request = PreviewCreateRequest.model_validate(
        {
            "rangeMode": "custom",
            "startDate": "2026-06-01",
            "endDate": "2026-06-01",
            "sources": ["plc"],
            "options": {"stableLagMinutes": 0},
        }
    )
    candidate = CandidateScanner(Settings(plc_data_dir=str(plc_dir))).scan(request)[0][0]
    cancel_checks = 0
    monotonic_values = iter([0.0, 0.0, 0.1, 0.2, 0.6])

    def should_cancel() -> bool:
        nonlocal cancel_checks
        cancel_checks += 1
        return cancel_checks >= 2

    def monotonic() -> float:
        try:
            return next(monotonic_values)
        except StopIteration:
            return 0.6

    monkeypatch.setattr("backend.app.services.upload_preview.time.monotonic", monotonic)

    try:
        CsvKeyExtractor().extract(
            candidate,
            max_file_seconds=5,
            sample_rows=200,
            force_full_scan=False,
            should_cancel=should_cancel,
        )
    except PreviewCancelledError:
        pass
    else:
        raise AssertionError("Expected time-based throttled cancel check to cancel extraction")

    assert cancel_checks == 2


def test_csv_key_extractor_streams_legacy_korean_plc_keys(tmp_path: Path) -> None:
    plc_dir = tmp_path / "plc"
    plc_dir.mkdir()
    csv_path = plc_dir / "260602_legacy_plc.csv"
    copy_fixture("legacy_plc_korean.csv", csv_path)
    request = PreviewCreateRequest.model_validate(
        {
            "rangeMode": "custom",
            "startDate": "2026-06-02",
            "endDate": "2026-06-02",
            "sources": ["plc"],
            "options": {"stableLagMinutes": 0},
        }
    )
    candidate = CandidateScanner(Settings(plc_data_dir=str(plc_dir))).scan(request)[0][0]

    result = CsvKeyExtractor().extract(
        candidate,
        max_file_seconds=5,
        sample_rows=2,
        force_full_scan=False,
    )

    assert result.row_count == 2
    assert result.sample_row_count == 2
    assert result.device_ids == ["extruder_plc"]
    assert result.local_keys == {
        ("2026-06-02T09:00:00+09:00", "extruder_plc"),
        ("2026-06-02T09:01:00+09:00", "extruder_plc"),
    }


def test_csv_key_extractor_streams_legacy_korean_temperature_keys(tmp_path: Path) -> None:
    temperature_dir = tmp_path / "temperature"
    temperature_dir.mkdir()
    csv_path = temperature_dir / "temperature_2026-06-02.csv"
    copy_fixture("legacy_temperature_korean.csv", csv_path)
    request = PreviewCreateRequest.model_validate(
        {
            "rangeMode": "custom",
            "startDate": "2026-06-02",
            "endDate": "2026-06-02",
            "sources": ["temperature"],
            "options": {"stableLagMinutes": 0},
        }
    )
    candidate = CandidateScanner(Settings(temperature_data_dir=str(temperature_dir))).scan(request)[0][0]

    result = CsvKeyExtractor().extract(
        candidate,
        max_file_seconds=5,
        sample_rows=2,
        force_full_scan=False,
    )

    assert result.row_count == 2
    assert result.sample_row_count == 2
    assert result.device_ids == ["spot_temperature_sensor"]
    assert result.local_keys == {
        ("2026-06-02T09:00:00.123000+09:00", "spot_temperature_sensor"),
        ("2026-06-02T09:01:00.000000+09:00", "spot_temperature_sensor"),
    }


def test_csv_key_extractor_uses_sample_rows_for_schema_mismatch(tmp_path: Path) -> None:
    plc_dir = tmp_path / "plc"
    plc_dir.mkdir()
    csv_path = plc_dir / "Factory_Integrated_Log_20260601_090000.csv"
    write_csv(
        csv_path,
        [
            "Bad,Columns,Time",
            "x,y,",
            "x,y,",
            "x,y,09:02:00",
        ],
    )
    request = PreviewCreateRequest.model_validate(
        {
            "rangeMode": "custom",
            "startDate": "2026-06-01",
            "endDate": "2026-06-01",
            "sources": ["plc"],
            "options": {"stableLagMinutes": 0},
        }
    )
    candidate = CandidateScanner(Settings(plc_data_dir=str(plc_dir))).scan(request)[0][0]

    try:
        CsvKeyExtractor().extract(
            candidate,
            max_file_seconds=5,
            sample_rows=2,
            force_full_scan=False,
        )
    except PreviewSchemaMismatchError:
        pass
    else:
        raise AssertionError("Expected sample schema mismatch")


def test_csv_key_extractor_force_full_scan_attempts_past_bad_sample(tmp_path: Path) -> None:
    plc_dir = tmp_path / "plc"
    plc_dir.mkdir()
    csv_path = plc_dir / "Factory_Integrated_Log_20260601_090000.csv"
    write_csv(
        csv_path,
        [
            "Bad,Columns,Time",
            "x,y,",
            "x,y,",
            "x,y,09:02:00",
        ],
    )
    request = PreviewCreateRequest.model_validate(
        {
            "rangeMode": "custom",
            "startDate": "2026-06-01",
            "endDate": "2026-06-01",
            "sources": ["plc"],
            "options": {"stableLagMinutes": 0},
        }
    )
    candidate = CandidateScanner(Settings(plc_data_dir=str(plc_dir))).scan(request)[0][0]

    result = CsvKeyExtractor().extract(
        candidate,
        max_file_seconds=5,
        sample_rows=2,
        force_full_scan=True,
    )

    assert result.row_count == 3
    assert result.sample_row_count == 2
    assert result.local_keys == {
        ("2026-06-01T09:02:00+09:00", "extruder_plc"),
    }


def test_classification_uses_exact_keys_not_latest_timestamp() -> None:
    csv_key = ("2026-06-01T09:00:00+09:00", "extruder_plc")
    later_key = ("2026-06-01T10:00:00+09:00", "extruder_plc")

    result = classify_reconciliation(local_keys={csv_key}, matched_keys={later_key})

    assert result["status"].value == "target"
    assert result["db_match_count"] == 0
    assert result["upload_row_estimate"] == 1


def test_preview_service_marks_db_unreachable_candidates_risky(tmp_path: Path) -> None:
    plc_dir = tmp_path / "plc"
    plc_dir.mkdir()
    write_csv(
        plc_dir / "Factory_Integrated_Log_20260601_090000.csv",
        ["Date,Time,Mold1", "2026-06-01,09:00:00,1"],
    )
    db_path = tmp_path / "state.db"
    repository = PreviewRepository(str(db_path))
    request = PreviewCreateRequest.model_validate(
        {
            "rangeMode": "custom",
            "startDate": "2026-06-01",
            "endDate": "2026-06-01",
            "sources": ["plc"],
            "options": PreviewOptions(stable_lag_minutes=0).model_dump(by_alias=True),
        }
    )
    repository.create_run(
        preview_run_id="prv_test",
        range_mode=request.range_mode.value,
        start_date="2026-06-01",
        end_date="2026-06-01",
        sources=["plc"],
        options=request.options.model_dump(by_alias=True),
        config_snapshot={},
        retry_of_run_id=None,
    )

    service = PreviewService(
        Settings(plc_data_dir=str(plc_dir)),
        repository,
        reconciler=FakeReconciler(fail=True),
    )
    service.run_preview("prv_test", request)

    row = repository.get_run("prv_test")
    items, total = repository.list_items("prv_test")

    assert row is not None
    assert row["status"] == "partial_failed"
    assert row["db_status"] == "unreachable"
    assert total == 1
    assert items[0]["status"] == "risky"
    assert items[0]["reason_code"] == "db_unreachable"
    assert items[0]["upload_row_estimate"] == 0


def test_preview_service_success_writes_upload_preview_audit_without_raw_values(
    tmp_path: Path,
) -> None:
    plc_dir = tmp_path / "plc"
    plc_dir.mkdir()
    write_csv(
        plc_dir / "Factory_Integrated_Log_20260601_090000.csv",
        ["Date,Time,Mold1", "2026-06-01,09:00:00,1"],
    )
    db_path = tmp_path / "state.db"
    repository = PreviewRepository(str(db_path))
    audit_repository = AuditRepository(str(db_path))
    request = PreviewCreateRequest.model_validate(
        {
            "rangeMode": "custom",
            "startDate": "2026-06-01",
            "endDate": "2026-06-01",
            "sources": ["plc"],
            "options": PreviewOptions(stable_lag_minutes=0).model_dump(by_alias=True),
        }
    )
    repository.create_run(
        preview_run_id="prv_success",
        range_mode=request.range_mode.value,
        start_date="2026-06-01",
        end_date="2026-06-01",
        sources=["plc"],
        options=request.options.model_dump(by_alias=True),
        config_snapshot={"supabaseDbUrl": "postgresql://user:secret-token@localhost/db"},
        retry_of_run_id=None,
    )

    service = PreviewService(
        Settings(
            plc_data_dir=str(plc_dir),
            supabase_db_url="postgresql://user:secret-token@localhost/db",
        ),
        repository,
        reconciler=FakeReconciler(),
        audit_repository=audit_repository,
    )
    service.run_preview("prv_success", request)

    page = audit_repository.list_audit_logs(AuditLogFilters(action="upload.preview"))
    assert page.total_items == 1
    row = page.rows[0]
    params = decode_params_json(row["params_json_redacted"])

    assert row["result"] == "success"
    assert row["target_id"] == "prv_success"
    assert params["previewRunId"] == "prv_success"
    assert params["candidateCount"] == 1
    assert params["targetCount"] == 1
    assert params["dbStatus"] == "reachable"
    assert params["requestedFilters"]["sources"] == ["plc"]
    assert str(plc_dir) not in row["params_json_redacted"]
    assert "Factory_Integrated_Log_20260601_090000.csv" not in row["params_json_redacted"]
    assert "secret-token" not in row["params_json_redacted"]
    assert "postgresql://user" not in row["params_json_redacted"]


def test_preview_service_db_unreachable_writes_failure_audit_without_raw_values(
    tmp_path: Path,
) -> None:
    plc_dir = tmp_path / "plc"
    plc_dir.mkdir()
    write_csv(
        plc_dir / "Factory_Integrated_Log_20260601_090000.csv",
        ["Date,Time,Mold1", "2026-06-01,09:00:00,1"],
    )
    db_path = tmp_path / "state.db"
    repository = PreviewRepository(str(db_path))
    audit_repository = AuditRepository(str(db_path))
    request = PreviewCreateRequest.model_validate(
        {
            "rangeMode": "custom",
            "startDate": "2026-06-01",
            "endDate": "2026-06-01",
            "sources": ["plc"],
            "options": PreviewOptions(stable_lag_minutes=0).model_dump(by_alias=True),
        }
    )
    repository.create_run(
        preview_run_id="prv_db_down",
        range_mode=request.range_mode.value,
        start_date="2026-06-01",
        end_date="2026-06-01",
        sources=["plc"],
        options=request.options.model_dump(by_alias=True),
        config_snapshot={},
        retry_of_run_id=None,
    )

    service = PreviewService(
        Settings(
            plc_data_dir=str(plc_dir),
            supabase_db_url="postgresql://user:secret-token@localhost/db",
        ),
        repository,
        reconciler=FakeReconciler(fail=True),
        audit_repository=audit_repository,
    )
    service.run_preview("prv_db_down", request)

    row = audit_repository.list_audit_logs(AuditLogFilters(action="upload.preview")).rows[0]
    params = decode_params_json(row["params_json_redacted"])

    assert row["result"] == "failure"
    assert row["error_code"] == "db_unreachable"
    assert params["previewRunId"] == "prv_db_down"
    assert params["dbStatus"] == "unreachable"
    assert params["reasonCode"] == "db_unreachable"
    assert params["riskyCount"] == 1
    assert str(plc_dir) not in row["params_json_redacted"]
    assert "secret-token" not in row["params_json_redacted"]
    assert "postgresql://user" not in row["params_json_redacted"]


def test_preview_service_missing_source_writes_failure_audit_without_raw_path(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "state.db"
    repository = PreviewRepository(str(db_path))
    audit_repository = AuditRepository(str(db_path))
    missing_dir = tmp_path / "missing"
    request = PreviewCreateRequest.model_validate(
        {
            "rangeMode": "today",
            "sources": ["plc"],
            "options": PreviewOptions(stable_lag_minutes=0).model_dump(by_alias=True),
        }
    )
    repository.create_run(
        preview_run_id="prv_missing_audit",
        range_mode=request.range_mode.value,
        start_date=None,
        end_date=None,
        sources=["plc"],
        options=request.options.model_dump(by_alias=True),
        config_snapshot={},
        retry_of_run_id=None,
    )

    service = PreviewService(
        Settings(plc_data_dir=str(missing_dir)),
        repository,
        reconciler=FakeReconciler(),
        audit_repository=audit_repository,
    )
    service.run_preview("prv_missing_audit", request)

    row = audit_repository.list_audit_logs(AuditLogFilters(action="upload.preview")).rows[0]
    params = decode_params_json(row["params_json_redacted"])

    assert row["result"] == "failure"
    assert row["error_code"] == "source_missing"
    assert params["previewRunId"] == "prv_missing_audit"
    assert params["reasonCode"] == "source_missing"
    assert str(missing_dir) not in row["params_json_redacted"]


def test_preview_service_marks_missing_source_as_failed(tmp_path: Path) -> None:
    repository = PreviewRepository(str(tmp_path / "state.db"))
    missing_dir = tmp_path / "missing"
    request = PreviewCreateRequest.model_validate(
        {
            "rangeMode": "today",
            "sources": ["plc"],
            "options": PreviewOptions(stable_lag_minutes=0).model_dump(by_alias=True),
        }
    )
    repository.create_run(
        preview_run_id="prv_missing_source",
        range_mode=request.range_mode.value,
        start_date=None,
        end_date=None,
        sources=["plc"],
        options=request.options.model_dump(by_alias=True),
        config_snapshot={},
        retry_of_run_id=None,
    )

    service = PreviewService(Settings(plc_data_dir=str(missing_dir)), repository, reconciler=FakeReconciler())
    service.run_preview("prv_missing_source", request)

    row = repository.get_run("prv_missing_source")
    items, total = repository.list_items("prv_missing_source")

    assert row is not None
    assert row["status"] == "failed"
    assert row["error_code"] == "source_missing"
    assert total == 1
    assert items[0]["reason_code"] == "source_missing"


def test_preview_service_honors_cancel_before_scanning(tmp_path: Path) -> None:
    plc_dir = tmp_path / "plc"
    plc_dir.mkdir()
    write_csv(
        plc_dir / "Factory_Integrated_Log_20260601_090000.csv",
        ["Date,Time,Mold1", "2026-06-01,09:00:00,1"],
    )
    repository = PreviewRepository(str(tmp_path / "state.db"))
    request = PreviewCreateRequest.model_validate(
        {
            "rangeMode": "custom",
            "startDate": "2026-06-01",
            "endDate": "2026-06-01",
            "sources": ["plc"],
            "options": PreviewOptions(stable_lag_minutes=0).model_dump(by_alias=True),
        }
    )
    repository.create_run(
        preview_run_id="prv_cancelled",
        range_mode=request.range_mode.value,
        start_date="2026-06-01",
        end_date="2026-06-01",
        sources=["plc"],
        options=request.options.model_dump(by_alias=True),
        config_snapshot={},
        retry_of_run_id=None,
    )
    repository.request_cancel("prv_cancelled")

    service = PreviewService(Settings(plc_data_dir=str(plc_dir)), repository, reconciler=FakeReconciler())
    service.run_preview("prv_cancelled", request)

    row = repository.get_run("prv_cancelled")
    items, total = repository.list_items("prv_cancelled")

    assert row is not None
    assert row["status"] == "cancelled"
    assert total == 0
    assert items == []


def test_preview_service_times_out_remaining_candidates(tmp_path: Path, monkeypatch) -> None:
    plc_dir = tmp_path / "plc"
    plc_dir.mkdir()
    write_csv(
        plc_dir / "Factory_Integrated_Log_20260601_090000.csv",
        ["Date,Time,Mold1", "2026-06-01,09:00:00,1"],
    )
    repository = PreviewRepository(str(tmp_path / "state.db"))
    request = PreviewCreateRequest.model_validate(
        {
            "rangeMode": "custom",
            "startDate": "2026-06-01",
            "endDate": "2026-06-01",
            "sources": ["plc"],
            "options": PreviewOptions(
                stable_lag_minutes=0,
                max_run_seconds=10,
            ).model_dump(by_alias=True),
        }
    )
    repository.create_run(
        preview_run_id="prv_timeout",
        range_mode=request.range_mode.value,
        start_date="2026-06-01",
        end_date="2026-06-01",
        sources=["plc"],
        options=request.options.model_dump(by_alias=True),
        config_snapshot={},
        retry_of_run_id=None,
    )

    service = PreviewService(
        Settings(plc_data_dir=str(plc_dir)),
        repository,
        reconciler=FakeReconciler(),
    )
    monotonic_values = itertools.chain([0.0, 0.0, 0.0, 11.0], itertools.repeat(11.0))
    monkeypatch.setattr("backend.app.services.upload_preview.time.monotonic", lambda: next(monotonic_values))
    service.run_preview("prv_timeout", request)

    row = repository.get_run("prv_timeout")
    items, total = repository.list_items("prv_timeout")

    assert row is not None
    assert row["status"] == "timed_out"
    assert row["error_code"] == "timeout"
    assert total == 1
    assert items[0]["status"] == "risky"
    assert items[0]["reason_code"] == "timeout"
    assert items[0]["upload_row_estimate"] == 0


def test_preview_service_db_timeout_preserves_extracted_counts_and_stage(tmp_path: Path) -> None:
    plc_dir = tmp_path / "plc"
    plc_dir.mkdir()
    write_csv(
        plc_dir / "Factory_Integrated_Log_20260601_090000.csv",
        [
            "Date,Time,Mold1",
            "2026-06-01,09:00:00,1",
            "2026-06-01,09:01:00,2",
        ],
    )
    repository = PreviewRepository(str(tmp_path / "state.db"))
    request = PreviewCreateRequest.model_validate(
        {
            "rangeMode": "custom",
            "startDate": "2026-06-01",
            "endDate": "2026-06-01",
            "sources": ["plc"],
            "options": {"stableLagMinutes": 0, "maxRunSeconds": 30},
        }
    )
    repository.create_run(
        preview_run_id="prv_db_timeout",
        range_mode=request.range_mode.value,
        start_date="2026-06-01",
        end_date="2026-06-01",
        sources=["plc"],
        options=request.options.model_dump(by_alias=True),
        config_snapshot={},
        retry_of_run_id=None,
    )

    service = PreviewService(
        Settings(plc_data_dir=str(plc_dir)),
        repository,
        reconciler=TimeoutReconciler(),
    )

    service.run_preview("prv_db_timeout", request)

    row = repository.get_run("prv_db_timeout")
    items, total = repository.list_items("prv_db_timeout")

    assert row is not None
    assert row["status"] == "timed_out"
    assert row["db_status"] == "not_checked"
    assert row["timeout_stage"] == "db_match"
    assert total == 1
    assert items[0]["status"] == "risky"
    assert items[0]["reason_code"] == "timeout"
    assert items[0]["scan_mode"] == "full"
    assert items[0]["row_count"] == 2
    assert items[0]["local_key_count"] == 2
    assert items[0]["upload_row_estimate"] == 0
    item_timing = json.loads(items[0]["timing_json"])
    assert item_timing["timeoutStage"] == "db_match"
    assert item_timing["dbProgress"]["strategy"] == "temp_table"
    assert item_timing["dbProgress"]["stage"] == "join_all_metrics"


def test_preview_service_non_timeout_extract_errors_do_not_persist_timeout_stage(tmp_path: Path) -> None:
    plc_dir = tmp_path / "plc"
    plc_dir.mkdir()
    write_csv(
        plc_dir / "Factory_Integrated_Log_20260601_090000.csv",
        ["Date,Time,Mold1", "2026-06-01,09:00:00,1"],
    )
    request = PreviewCreateRequest.model_validate(
        {
            "rangeMode": "custom",
            "startDate": "2026-06-01",
            "endDate": "2026-06-01",
            "sources": ["plc"],
            "options": {"stableLagMinutes": 0, "maxRunSeconds": 30},
        }
    )

    cases = [
        ("prv_schema_mismatch", SchemaMismatchExtractor(), "schema_mismatch"),
        ("prv_transform_error", TransformErrorExtractor(), "transform_error"),
    ]
    for preview_run_id, extractor, expected_reason in cases:
        repository = PreviewRepository(str(tmp_path / f"{preview_run_id}.db"))
        repository.create_run(
            preview_run_id=preview_run_id,
            range_mode=request.range_mode.value,
            start_date="2026-06-01",
            end_date="2026-06-01",
            sources=["plc"],
            options=request.options.model_dump(by_alias=True),
            config_snapshot={},
            retry_of_run_id=None,
        )
        service = PreviewService(
            Settings(plc_data_dir=str(plc_dir)),
            repository,
            reconciler=FakeReconciler(),
        )
        service.extractor = extractor

        service.run_preview(preview_run_id, request)

        items, total = repository.list_items(preview_run_id)
        assert total == 1
        assert items[0]["reason_code"] == expected_reason
        assert items[0]["timeout_stage"] is None
        item_timing = json.loads(items[0]["timing_json"])
        assert "extractMs" in item_timing
        assert "timeoutStage" not in item_timing
