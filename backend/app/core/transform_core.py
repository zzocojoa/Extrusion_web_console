import csv
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Any


PLC_DEVICE_ID = "extruder_plc"
INTEGRATED_PLC_DEVICE_ID = "extruder_integrated"
TEMPERATURE_DEVICE_ID = "spot_temperature_sensor"

ALLOWED_METRIC_KEYS = {
    "timestamp",
    "device_id",
    "temperature",
    "main_pressure",
    "billet_length",
    "container_temp_front",
    "container_temp_rear",
    "production_counter",
    "current_speed",
    "extrusion_end_position",
    "mold_1",
    "mold_2",
    "mold_3",
    "mold_4",
    "mold_5",
    "mold_6",
    "billet_temp",
    "at_pre",
    "at_temp",
    "die_id",
    "billet_cycle_id",
}

INTEGRATED_PLC_MAP = {
    "Temperature": "temperature",
    "Mold1": "mold_1",
    "Mold2": "mold_2",
    "Mold3": "mold_3",
    "Mold4": "mold_4",
    "Mold5": "mold_5",
    "Mold6": "mold_6",
    "Billet_Temp": "billet_temp",
    "At_Pre": "at_pre",
    "At_Temp": "at_temp",
    "DIE_ID": "die_id",
    "Billet_CycleID": "billet_cycle_id",
}

LEGACY_PLC_ALIASES = {
    "main_pressure": ("main_pressure", "main pressure", "Main Pressure"),
    "billet_length": ("billet_length", "billet length", "Billet Length"),
    "container_temp_front": ("container_temp_front", "container temp front", "Container Temp Front"),
    "container_temp_rear": ("container_temp_rear", "container temp rear", "Container Temp Rear"),
    "production_counter": ("production_counter", "production counter", "Production Counter"),
    "current_speed": ("current_speed", "current speed", "Current Speed"),
    "extrusion_end_position": ("extrusion_end_position", "extrusion end position", "Extrusion End Position"),
}

TEMP_ALIASES = {
    "temperature": ("temperature", "Temperature", "temp", "Temp"),
}


def iter_canonical_record_chunks(
    file_row: Any,
    *,
    chunk_rows: int,
    start_offset: int = 0,
) -> Iterable[list[dict[str, Any]]]:
    path = Path(file_row["path"])
    try:
        yield from _iter_canonical_record_chunks_with_encoding(
            file_row,
            path,
            "utf-8-sig",
            chunk_rows,
            start_offset,
        )
    except UnicodeDecodeError:
        yield from _iter_canonical_record_chunks_with_encoding(
            file_row,
            path,
            "cp949",
            chunk_rows,
            start_offset,
        )


def count_canonical_records(file_row: Any) -> int:
    count = 0
    for chunk in iter_canonical_record_chunks(file_row, chunk_rows=10_000):
        count += len(chunk)
    return count


def _iter_canonical_record_chunks_with_encoding(
    file_row: Any,
    path: Path,
    encoding: str,
    chunk_rows: int,
    start_offset: int,
) -> Iterable[list[dict[str, Any]]]:
    chunk: list[dict[str, Any]] = []
    seen = 0
    with path.open("r", encoding=encoding, newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            record = canonical_record_from_row(file_row, row)
            if record is None:
                continue
            if seen < start_offset:
                seen += 1
                continue
            chunk.append(record)
            seen += 1
            if len(chunk) >= chunk_rows:
                yield chunk
                chunk = []
    if chunk:
        yield chunk


def canonical_record_from_row(file_row: Any, row: dict[str, str]) -> dict[str, Any] | None:
    kind = str(file_row["kind"])
    if kind == "plc":
        if _is_integrated_plc_row(row):
            return _integrated_plc_record(row)
        return _legacy_plc_record(file_row, row)
    if kind == "temperature":
        return _temperature_record(row)
    return _canonical_record(row)


def _canonical_record(row: dict[str, str]) -> dict[str, Any] | None:
    timestamp = clean(row.get("timestamp")) or clean(row.get("Timestamp"))
    device_id = clean(row.get("device_id")) or clean(row.get("Device ID"))
    if not timestamp or not device_id:
        return None
    record: dict[str, Any] = {"timestamp": timestamp, "device_id": device_id}
    for key, value in row.items():
        metric_key = canonical_metric_key(key)
        if metric_key is None or metric_key in {"timestamp", "device_id"}:
            continue
        record[metric_key] = coerce_metric_value(value, metric_key)
    return record


def _is_integrated_plc_row(row: dict[str, str]) -> bool:
    return {"Date", "Time"}.issubset(row.keys()) and any(key.startswith("Mold") for key in row)


def _integrated_plc_record(row: dict[str, str]) -> dict[str, Any] | None:
    timestamp = build_integrated_timestamp(row.get("Date"), row.get("Time"))
    if not timestamp:
        return None
    record: dict[str, Any] = {
        "timestamp": timestamp,
        "device_id": INTEGRATED_PLC_DEVICE_ID,
    }
    for source, target in INTEGRATED_PLC_MAP.items():
        if source in row:
            record[target] = coerce_metric_value(row[source], target)
    return record


def _legacy_plc_record(file_row: Any, row: dict[str, str]) -> dict[str, Any] | None:
    canonical = _canonical_record(row)
    if canonical is not None:
        return canonical
    time_value = clean(row.get("Time")) or clean(row.get("time"))
    file_date = clean(file_row["file_date"])
    if not time_value or not file_date:
        return None
    record: dict[str, Any] = {
        "timestamp": f"{file_date}T{time_value}+09:00",
        "device_id": PLC_DEVICE_ID,
    }
    for target, aliases in LEGACY_PLC_ALIASES.items():
        value = first_present(row, aliases)
        if value is not None:
            record[target] = coerce_metric_value(value, target)
    return record


def _temperature_record(row: dict[str, str]) -> dict[str, Any] | None:
    canonical = _canonical_record(row)
    if canonical is not None:
        return canonical
    timestamp = (
        clean(row.get("datetime"))
        or clean(row.get("Datetime"))
        or clean(row.get("date_time"))
        or clean(row.get("DateTime"))
    )
    if not timestamp:
        date_value = clean(row.get("date")) or clean(row.get("Date"))
        time_value = clean(row.get("time")) or clean(row.get("Time"))
        if date_value and time_value:
            timestamp = build_integrated_timestamp(date_value, time_value)
    if not timestamp:
        return None
    record: dict[str, Any] = {
        "timestamp": timestamp,
        "device_id": TEMPERATURE_DEVICE_ID,
    }
    value = first_present(row, TEMP_ALIASES["temperature"])
    if value is not None:
        record["temperature"] = coerce_metric_value(value, "temperature")
    return record


def build_integrated_timestamp(date_value: object, time_value: object) -> str | None:
    date_text = clean(date_value)
    time_text = clean(time_value)
    if not date_text or not time_text:
        return None
    timestamp_text = f"{date_text} {time_text}"
    for fmt in (
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S.%f",
        "%Y/%m/%d %H:%M:%S",
    ):
        try:
            return datetime.strptime(timestamp_text, fmt).strftime("%Y-%m-%dT%H:%M:%S.%f+09:00")
        except ValueError:
            continue
    if "T" in date_text:
        return date_text
    return f"{date_text}T{time_text}+09:00"


def canonical_metric_key(value: str) -> str | None:
    stripped = value.strip()
    if stripped in ALLOWED_METRIC_KEYS:
        return stripped
    normalized = normalize_column_name(stripped)
    if normalized in ALLOWED_METRIC_KEYS:
        return normalized
    return None


def normalize_column_name(value: str) -> str:
    normalized = "".join(ch if ch.isalnum() else "_" for ch in value.strip().lower())
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized.strip("_")


def first_present(row: dict[str, str], aliases: tuple[str, ...]) -> str | None:
    for alias in aliases:
        value = clean(row.get(alias))
        if value is not None:
            return value
    return None


def clean(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def coerce_metric_value(value: object, metric_key: str) -> str | int | float | None:
    cleaned = clean(value)
    if cleaned is None:
        return None
    if metric_key == "die_id":
        return cleaned
    try:
        if "." not in cleaned:
            return int(cleaned)
        return float(cleaned)
    except ValueError:
        return cleaned
