import json
import shutil
import subprocess
from pathlib import Path

import pytest

from backend.app.core.transform_core import ALLOWED_METRIC_KEYS
from backend.app.services.upload_jobs import CsvUploadRecordReader


FIXTURES = Path(__file__).parent / "fixtures"
LEGACY_TRANSFORM = Path(r"C:\Users\user\Documents\GitHub\Extrusion_data\core\transform.py")


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


def collect_records_chunked(path: Path, *, kind: str = "plc") -> list[dict[str, object]]:
    reader = CsvUploadRecordReader()
    chunks = list(reader.iter_records(file_row(path, kind=kind), chunk_rows=1))
    return [record for chunk in chunks for record in chunk]


def collect_legacy_records(function_name: str, path: Path, filename: str, *, chunksize: int | None = None) -> list[dict[str, object]]:
    python = shutil.which("python")
    if python is None or not LEGACY_TRANSFORM.exists():
        pytest.skip("Legacy transform reference is not available in this environment.")
    code = """
import importlib.util
import json
import sys

transform_path, function_name, csv_path, filename, chunksize_text = sys.argv[1:]
spec = importlib.util.spec_from_file_location("legacy_transform", transform_path)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
chunksize = None if chunksize_text == "none" else int(chunksize_text)
result = getattr(module, function_name)(csv_path, filename, chunksize=chunksize)
frames = list(result) if chunksize is not None else [result]
records = []
for frame in frames:
    if frame.empty:
        continue
    clean = frame.where(frame.notna(), None)
    records.extend(clean.to_dict(orient="records"))
print(json.dumps(records, ensure_ascii=False))
"""
    completed = subprocess.run(
        [
            python,
            "-c",
            code,
            str(LEGACY_TRANSFORM),
            function_name,
            str(path),
            filename,
            "none" if chunksize is None else str(chunksize),
        ],
        capture_output=True,
        check=False,
        text=True,
    )
    if completed.returncode != 0:
        if "ModuleNotFoundError" in completed.stderr:
            pytest.skip(f"Legacy transform dependencies are not available: {completed.stderr}")
        raise AssertionError(completed.stderr)
    return json.loads(completed.stdout)


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


def test_upload_reader_matches_legacy_plc_korean_mapping_contract() -> None:
    csv_path = FIXTURES / "legacy_plc_korean.csv"

    records = collect_records(csv_path, kind="plc")
    legacy_records = collect_legacy_records("build_records_plc", csv_path, "260602_legacy_plc.csv")
    legacy_chunked_records = collect_legacy_records("build_records_plc", csv_path, "260602_legacy_plc.csv", chunksize=1)

    assert records == [
        {
            "timestamp": "2026-06-02T09:00:00+09:00",
            "device_id": "extruder_plc",
            "main_pressure": 12.5,
            "billet_length": 100,
            "container_temp_front": 450,
            "container_temp_rear": 440,
            "production_counter": 7,
            "current_speed": 8.2,
            "extrusion_end_position": 99,
        },
        {
            "timestamp": "2026-06-02T09:01:00+09:00",
            "device_id": "extruder_plc",
            "main_pressure": 13.5,
            "billet_length": 101,
            "container_temp_front": 451,
            "container_temp_rear": 441,
            "production_counter": 8,
            "current_speed": 8.4,
            "extrusion_end_position": 100,
        },
    ]
    assert records == legacy_records
    assert records == legacy_chunked_records
    assert all(set(record).issubset(ALLOWED_METRIC_KEYS) for record in records)
    assert collect_records_chunked(csv_path, kind="plc") == records


def test_upload_reader_matches_legacy_temperature_korean_mapping_contract() -> None:
    csv_path = FIXTURES / "legacy_temperature_korean.csv"

    records = collect_records(csv_path, kind="temperature")
    legacy_records = collect_legacy_records("build_records_temp", csv_path, "legacy_temperature_korean.csv")
    legacy_chunked_records = collect_legacy_records("build_records_temp", csv_path, "legacy_temperature_korean.csv", chunksize=1)

    assert records == [
        {
            "timestamp": "2026-06-02T09:00:00.123000+09:00",
            "device_id": "spot_temperature_sensor",
            "temperature": 41.5,
        },
        {
            "timestamp": "2026-06-02T09:01:00.000000+09:00",
            "device_id": "spot_temperature_sensor",
            "temperature": 42.0,
        },
    ]
    assert records == legacy_records
    assert records == legacy_chunked_records
    assert all(set(record).issubset(ALLOWED_METRIC_KEYS) for record in records)
    assert collect_records_chunked(csv_path, kind="temperature") == records


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
