from pathlib import Path

from backend.app.core.transform_core import ALLOWED_METRIC_KEYS
from backend.app.services.upload_jobs import CsvUploadRecordReader


def file_row(path: Path, *, kind: str = "plc", file_date: str = "2026-06-02") -> dict[str, object]:
    return {
        "path": str(path),
        "kind": kind,
        "file_date": file_date,
    }


def collect_records(path: Path, *, kind: str = "plc") -> list[dict[str, object]]:
    reader = CsvUploadRecordReader()
    chunks = list(reader.iter_records(file_row(path, kind=kind), chunk_rows=2))
    return [record for chunk in chunks for record in chunk]


def test_upload_reader_filters_unknown_columns_from_edge_payload(tmp_path: Path) -> None:
    csv_path = tmp_path / "canonical.csv"
    csv_path.write_text(
        "timestamp,device_id,value,main_pressure,die_id\n"
        "2026-06-02T09:00:00+09:00,extruder_plc,999,12.5,D-1\n",
        encoding="utf-8",
    )

    records = collect_records(csv_path)

    assert records == [
        {
            "timestamp": "2026-06-02T09:00:00+09:00",
            "device_id": "extruder_plc",
            "main_pressure": 12.5,
            "die_id": "D-1",
        }
    ]
    assert set(records[0]).issubset(ALLOWED_METRIC_KEYS)
    assert "value" not in records[0]


def test_upload_reader_maps_integrated_plc_to_legacy_keys(tmp_path: Path) -> None:
    csv_path = tmp_path / "integrated.csv"
    csv_path.write_text(
        "Date,Time,Temperature,Mold1,Mold2,Billet_Temp,At_Pre,At_Temp,DIE_ID,Billet_CycleID,Ignored\n"
        "2026-06-02,09:00:00,460.5,11,12,430,5.5,44.2,D-7,88,drop\n",
        encoding="utf-8",
    )

    records = collect_records(csv_path)

    assert len(records) == 1
    assert records[0]["device_id"] == "extruder_integrated"
    assert records[0]["timestamp"] == "2026-06-02T09:00:00.000000+09:00"
    assert records[0]["temperature"] == 460.5
    assert records[0]["mold_1"] == 11
    assert records[0]["mold_2"] == 12
    assert records[0]["billet_temp"] == 430
    assert records[0]["at_pre"] == 5.5
    assert records[0]["at_temp"] == 44.2
    assert records[0]["die_id"] == "D-7"
    assert records[0]["billet_cycle_id"] == 88
    assert set(records[0]).issubset(ALLOWED_METRIC_KEYS)


def test_upload_reader_maps_temperature_to_legacy_keys(tmp_path: Path) -> None:
    csv_path = tmp_path / "temperature.csv"
    csv_path.write_text(
        "datetime,temperature,Ignored\n"
        "2026-06-02T09:00:00.000000+09:00,41.5,drop\n",
        encoding="utf-8",
    )

    records = collect_records(csv_path, kind="temperature")

    assert records == [
        {
            "timestamp": "2026-06-02T09:00:00.000000+09:00",
            "device_id": "spot_temperature_sensor",
            "temperature": 41.5,
        }
    ]
    assert set(records[0]).issubset(ALLOWED_METRIC_KEYS)


def test_upload_reader_resume_offset_skips_canonical_records(tmp_path: Path) -> None:
    csv_path = tmp_path / "canonical.csv"
    csv_path.write_text(
        "timestamp,device_id,main_pressure\n"
        "2026-06-02T09:00:00+09:00,extruder_plc,1\n"
        "2026-06-02T09:01:00+09:00,extruder_plc,2\n",
        encoding="utf-8",
    )

    reader = CsvUploadRecordReader()
    chunks = list(reader.iter_records(file_row(csv_path), chunk_rows=10, start_offset=1))

    assert chunks == [
        [
            {
                "timestamp": "2026-06-02T09:01:00+09:00",
                "device_id": "extruder_plc",
                "main_pressure": 2,
            }
        ]
    ]
