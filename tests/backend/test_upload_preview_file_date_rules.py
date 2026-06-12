from datetime import date
from pathlib import Path

from backend.app.core.settings import Settings
from backend.app.schemas.upload_preview import PreviewCreateRequest
from backend.app.services.upload_preview import (
    CandidateScanner,
    INTEGRATED_FILENAME_STEM,
    parse_plc_file_date,
    parse_temperature_file_date,
)


def write_csv(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_plc_file_date_parser_accepts_only_supported_metadata_patterns() -> None:
    assert parse_plc_file_date(f"{INTEGRATED_FILENAME_STEM}_20260602_090000.csv") == date(
        2026, 6, 2
    )
    assert parse_plc_file_date("260602_legacy_plc.csv") == date(2026, 6, 2)

    assert parse_plc_file_date("stage3-copy-20260602.csv") is None
    assert parse_plc_file_date("profile-a-2026-06-02.csv") is None
    assert parse_plc_file_date("renamed_260602.csv") is None


def test_temperature_file_date_parser_accepts_iso_date_anywhere() -> None:
    assert parse_temperature_file_date("temperature_2026-06-02.csv") == date(2026, 6, 2)
    assert parse_temperature_file_date("2026-06-02_temperature.csv") == date(2026, 6, 2)

    assert parse_temperature_file_date("temperature_20260602.csv") is None
    assert parse_temperature_file_date("260602_temperature.csv") is None


def test_candidate_scanner_does_not_infer_file_date_from_csv_content(tmp_path: Path) -> None:
    plc_dir = tmp_path / "plc"
    plc_dir.mkdir()
    write_csv(
        plc_dir / "stage3-copy-20260602.csv",
        ["Date,Time,Mold1", "2026-06-02,09:00:00,1"],
    )
    request = PreviewCreateRequest.model_validate(
        {
            "rangeMode": "custom",
            "startDate": "2026-06-02",
            "endDate": "2026-06-02",
            "sources": ["plc"],
            "options": {"stableLagMinutes": 0},
        }
    )

    candidates, issues = CandidateScanner(Settings(plc_data_dir=str(plc_dir))).scan(request)

    assert candidates == []
    assert [issue["reason_code"] for issue in issues] == ["file_date_missing"]
