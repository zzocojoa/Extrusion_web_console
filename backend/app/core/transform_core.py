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
    "time": ("시간", "시각", "Time", "time"),
    "main_pressure": ("메인압력", "메인 압력", "main_pressure", "main pressure", "Main Pressure"),
    "billet_length": ("빌렛길이", "빌렛 길이", "billet_length", "billet length", "Billet Length"),
    "container_temp_front": (
        "콘테이너온도 앞쪽",
        "콘테이너 온도 앞쪽",
        "container_temp_front",
        "container temp front",
        "Container Temp Front",
    ),
    "container_temp_rear": (
        "콘테이너온도 뒤쪽",
        "콘테이너 온도 뒤쪽",
        "container_temp_rear",
        "container temp rear",
        "Container Temp Rear",
    ),
    "production_counter": (
        "생산카운터",
        "생산 카운터",
        "생산카운트",
        "생산 카운트",
        "production_counter",
        "production counter",
        "Production Counter",
    ),
    "current_speed": ("현재속도", "현재 속도", "current_speed", "current speed", "Current Speed"),
    "extrusion_end_position": (
        "압출종료 위치",
        "압출 종료 위치",
        "압출종료위치",
        "extrusion_end_position",
        "extrusion end position",
        "Extrusion End Position",
    ),
}

TEMP_ALIASES = {
    "datetime": ("datetime", "date_time", "날짜시간", "일시"),
    "date": ("date", "날짜", "일자"),
    "time": ("time", "시간", "시각"),
    "temperature": ("temperature", "온도", "temp"),
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
    colmap = legacy_plc_colmap(row)
    time_column = colmap.get("time")
    time_value = clean(row.get(time_column)) if time_column else None
    file_date = clean(file_row["file_date"])
    if not time_value or not file_date:
        return None
    record: dict[str, Any] = {
        "timestamp": f"{file_date}T{time_value}+09:00",
        "device_id": PLC_DEVICE_ID,
    }
    for target in (
        "main_pressure",
        "billet_length",
        "container_temp_front",
        "container_temp_rear",
        "production_counter",
        "current_speed",
        "extrusion_end_position",
    ):
        column = colmap.get(target)
        if column:
            record[target] = coerce_metric_value(row.get(column), target)
    return record


def _temperature_record(row: dict[str, str]) -> dict[str, Any] | None:
    canonical = _canonical_record(row)
    if canonical is not None:
        return canonical
    normalized = normalized_temperature_row(row)
    timestamp = None
    datetime_key = pick_normalized_key(normalized, TEMP_ALIASES["datetime"])
    if datetime_key:
        timestamp = build_temperature_timestamp(clean(normalized[datetime_key]), None)
    if not timestamp:
        date_key = pick_normalized_key(normalized, TEMP_ALIASES["date"])
        time_key = pick_normalized_key(normalized, TEMP_ALIASES["time"])
        date_value = clean(normalized[date_key]) if date_key else None
        time_value = clean(normalized[time_key]) if time_key else None
        if date_value and time_value:
            timestamp = build_temperature_timestamp(date_value, time_value)
    if not timestamp:
        return None
    record: dict[str, Any] = {
        "timestamp": timestamp,
        "device_id": TEMPERATURE_DEVICE_ID,
    }
    temperature_key = pick_normalized_key(normalized, TEMP_ALIASES["temperature"])
    if temperature_key:
        record["temperature"] = coerce_metric_value(normalized[temperature_key], "temperature")
    return record


def legacy_plc_colmap(row: dict[str, str]) -> dict[str, str]:
    colmap: dict[str, str] = {}
    columns = list(row.keys())
    for target, aliases in LEGACY_PLC_ALIASES.items():
        for alias in aliases:
            if alias in row:
                colmap[target] = alias
                break

    if "container_temp_rear" not in colmap:
        used = set(colmap.values())
        for column in columns:
            if column in used:
                continue
            if ("뒤" in column) or ("후" in column) or ("rear" in column.lower()):
                colmap["container_temp_rear"] = column
                break

    if "container_temp_rear" not in colmap and "container_temp_front" in colmap:
        try:
            front_index = columns.index(colmap["container_temp_front"])
        except ValueError:
            front_index = -1
        if front_index >= 0:
            used = set(colmap.values())
            for column in columns[front_index + 1 :]:
                if column in used:
                    continue
                if is_numeric_like(row.get(column)):
                    colmap["container_temp_rear"] = column
                    break

    if "production_counter" not in colmap:
        for column in columns:
            if "생산" in column and ("카운터" in column or "카운트" in column):
                colmap["production_counter"] = column
                break

    return colmap


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


def build_temperature_timestamp(date_value: object, time_value: object | None) -> str | None:
    date_text = clean(date_value)
    if not date_text:
        return None
    timestamp_text = date_text
    if time_value is not None:
        time_text = normalize_legacy_time(clean(time_value))
        if not time_text:
            return None
        timestamp_text = f"{date_text} {time_text}"
    else:
        timestamp_text = timestamp_text.replace("T", " ")
    for fmt in (
        "%Y-%m-%d %H:%M:%S.%f%z",
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S.%f",
        "%Y/%m/%d %H:%M:%S",
    ):
        try:
            parsed = datetime.strptime(timestamp_text, fmt)
            return parsed.strftime("%Y-%m-%dT%H:%M:%S.%f+09:00")
        except ValueError:
            continue
    return None


def normalize_legacy_time(value: str | None) -> str | None:
    if not value:
        return None
    if value.count(":") >= 3:
        head, tail = value.rsplit(":", 1)
        return f"{head}.{tail}"
    return value


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


def normalized_temperature_row(row: dict[str, str]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for key, value in row.items():
        normalized_key = key.strip().replace("[", "").replace("]", "").lower()
        normalized[normalized_key] = value
    return normalized


def pick_normalized_key(row: dict[str, str], aliases: tuple[str, ...]) -> str | None:
    for alias in aliases:
        normalized_alias = alias.strip().replace("[", "").replace("]", "").lower()
        if normalized_alias in row:
            return normalized_alias
    return None


def is_numeric_like(value: object) -> bool:
    cleaned = clean(value)
    if cleaned is None:
        return False
    try:
        float(cleaned)
    except ValueError:
        return False
    return True


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
