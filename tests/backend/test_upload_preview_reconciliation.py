from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path

from backend.app.core.settings import Settings
from backend.app.db.preview_repository import PreviewRepository
from backend.app.schemas.upload_preview import PreviewCreateRequest, PreviewOptions
from backend.app.services.upload_preview import (
    CandidateScanner,
    CsvKeyExtractor,
    PreviewDbUnavailableError,
    PreviewService,
    classify_reconciliation,
    date_window,
)


class FakeReconciler:
    def __init__(self, matched_keys: set[tuple[str, str]] | None = None, fail: bool = False) -> None:
        self.matched_keys = matched_keys or set()
        self.fail = fail
        self.seen_keys: set[tuple[str, str]] = set()

    def find_existing_keys(self, keys: set[tuple[str, str]]) -> set[tuple[str, str]]:
        self.seen_keys = set(keys)
        if self.fail:
            raise PreviewDbUnavailableError("database down")
        return set(keys) & self.matched_keys


def write_csv(path: Path, rows: list[str]) -> None:
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    old_mtime = datetime.now().timestamp() - 600
    os.utime(path, (old_mtime, old_mtime))


def test_date_window_modes_are_exact_kst_days() -> None:
    now = datetime.fromisoformat("2026-06-01T10:00:00+09:00")

    today = PreviewCreateRequest.model_validate({"rangeMode": "today", "sources": ["plc"]})
    assert date_window(today, now=now) == (now.date(), now.date())

    last_two = PreviewCreateRequest.model_validate({"rangeMode": "last_2_days", "sources": ["plc"]})
    assert date_window(last_two, now=now) == (now.date() - timedelta(days=1), now.date())


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

    result = CsvKeyExtractor().extract(candidate, max_file_seconds=5)

    assert result.row_count == 3
    assert result.device_ids == ["extruder_integrated"]
    assert result.local_keys == {
        ("2026-06-01T09:00:00+09:00", "extruder_integrated"),
        ("2026-06-01T09:01:00+09:00", "extruder_integrated"),
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
    monotonic_values = iter([0.0, 11.0])
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
