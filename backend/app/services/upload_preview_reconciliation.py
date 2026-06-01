from __future__ import annotations

import csv
import os
import re
import time
from dataclasses import dataclass, field, replace
from datetime import date, datetime, time as datetime_time, timedelta, timezone
from enum import StrEnum
from pathlib import Path
from typing import Callable, Iterable, Iterator, Protocol

KST = timezone(timedelta(hours=9))
PLC_DEVICE_ID = "extruder_plc"
INTEGRATED_PLC_DEVICE_ID = "extruder_integrated"
TEMPERATURE_DEVICE_ID = "spot_temperature_sensor"


class PreviewItemStatus(StrEnum):
    TARGET = "target"
    ALREADY_IN_DB = "already_in_db"
    PARTIAL_OVERLAP = "partial_overlap"
    RISKY = "risky"
    EXCLUDED = "excluded"


class PreviewSourceKind(StrEnum):
    PLC = "plc"
    TEMPERATURE = "temperature"


class ScanMode(StrEnum):
    METADATA = "metadata"
    SAMPLE = "sample"
    FULL = "full"
    INCOMPLETE = "incomplete"


class DbStatus(StrEnum):
    NOT_CHECKED = "not_checked"
    REACHABLE = "reachable"
    UNREACHABLE = "unreachable"
    QUERY_FAILED = "query_failed"


MetricKey = tuple[str, str]
CancelCheck = Callable[[], bool]


@dataclass(frozen=True)
class SourceFolder:
    folder_label: str
    folder_path: Path
    kind: PreviewSourceKind
    enabled: bool = True


def source_folders_from_config(config: object) -> tuple[SourceFolder, ...]:
    """Build scanner sources from backend settings without accepting request paths."""
    sources: list[SourceFolder] = []
    plc_dir = getattr(config, "plc_data_dir", None) or getattr(config, "upload_plc_csv_dir", None)
    temperature_dir = getattr(config, "temperature_data_dir", None) or getattr(
        config, "upload_temperature_csv_dir", None
    )
    if plc_dir:
        sources.append(
            SourceFolder(
                folder_label="PLC",
                folder_path=Path(plc_dir),
                kind=PreviewSourceKind.PLC,
            )
        )
    if temperature_dir:
        sources.append(
            SourceFolder(
                folder_label="Temperature",
                folder_path=Path(temperature_dir),
                kind=PreviewSourceKind.TEMPERATURE,
            )
        )
    return tuple(sources)


@dataclass(frozen=True)
class DateWindow:
    start: date
    end: date

    def contains(self, value: date) -> bool:
        return self.start <= value <= self.end


@dataclass(frozen=True)
class PreviewScanOptions:
    stable_lag_minutes: int = 3
    sample_rows: int = 200
    max_files: int = 500
    check_locks: bool = True


@dataclass(frozen=True)
class CandidateFile:
    folder_label: str
    folder_path: Path
    filename: str
    path: Path
    kind: PreviewSourceKind
    file_key: str
    file_date: date | None
    size_bytes: int | None
    mtime_ns: int | None
    modified_at: datetime | None
    status: PreviewItemStatus | None = None
    reason_code: str | None = None
    reason_text: str | None = None
    scan_mode: ScanMode = ScanMode.METADATA
    issues: tuple[str, ...] = ()
    sample_row_count: int | None = None

    @property
    def needs_full_reconciliation(self) -> bool:
        return self.status is None


@dataclass(frozen=True)
class KeyExtractionOptions:
    chunk_rows: int = 20_000
    max_file_seconds: int = 30


@dataclass(frozen=True)
class KeyExtractionResult:
    candidate: CandidateFile
    keys: frozenset[MetricKey]
    row_count: int
    local_key_count: int
    first_timestamp: str | None
    last_timestamp: str | None
    device_ids: tuple[str, ...]
    issues: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReconciliationResult:
    db_status: DbStatus
    matched_keys: frozenset[MetricKey] = frozenset()
    error_code: str | None = None
    error_message: str | None = None


@dataclass(frozen=True)
class PreviewClassification:
    status: PreviewItemStatus
    reason_code: str
    reason_text: str
    db_match_count: int = 0
    upload_row_estimate: int = 0


@dataclass(frozen=True)
class ReconciledPreviewItem:
    candidate: CandidateFile
    classification: PreviewClassification
    row_count: int | None = None
    local_key_count: int | None = None
    first_timestamp: str | None = None
    last_timestamp: str | None = None
    device_ids: tuple[str, ...] = ()
    issues: tuple[str, ...] = ()


class ExactReconciler(Protocol):
    def find_existing_keys(self, keys: Iterable[MetricKey]) -> ReconciliationResult:
        ...


def kst_now() -> datetime:
    return datetime.now(KST)


def date_window_for_mode(
    range_mode: str,
    *,
    now: datetime | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> DateWindow:
    today = (now or kst_now()).astimezone(KST).date()
    if range_mode == "today":
        return DateWindow(today, today)
    if range_mode == "yesterday":
        yesterday = today - timedelta(days=1)
        return DateWindow(yesterday, yesterday)
    if range_mode == "last_2_days":
        return DateWindow(today - timedelta(days=1), today)
    if range_mode == "custom":
        if start_date is None or end_date is None:
            raise ValueError("custom range requires start_date and end_date")
        if start_date > end_date:
            raise ValueError("custom range start_date must be on or before end_date")
        return DateWindow(start_date, end_date)
    raise ValueError(f"unsupported preview range mode: {range_mode}")


def parse_plc_date_from_filename(name: str) -> date | None:
    legacy_match = re.match(r"^(\d{2})(\d{2})(\d{2})", name)
    if legacy_match:
        year, month, day = legacy_match.groups()
        try:
            return date(int(f"20{year}"), int(month), int(day))
        except ValueError:
            return None

    integrated_match = re.match(r"Factory_Integrated_Log_(\d{4})(\d{2})(\d{2})_", name)
    if integrated_match:
        year, month, day = integrated_match.groups()
        try:
            return date(int(year), int(month), int(day))
        except ValueError:
            return None

    return None


def parse_temperature_date_from_filename(name: str) -> date | None:
    matches = list(re.finditer(r"(\d{4})-(\d{2})-(\d{2})", name))
    if not matches:
        return None
    year, month, day = matches[-1].groups()
    try:
        return date(int(year), int(month), int(day))
    except ValueError:
        return None


def _parse_file_date_for_kind(kind: PreviewSourceKind, filename: str) -> date | None:
    if kind == PreviewSourceKind.PLC:
        return parse_plc_date_from_filename(filename)
    if kind == PreviewSourceKind.TEMPERATURE:
        return parse_temperature_date_from_filename(filename)
    return None


def _is_locked(path: Path) -> bool:
    try:
        if os.name == "nt":
            import msvcrt

            with path.open("rb") as file_handle:
                try:
                    msvcrt.locking(file_handle.fileno(), msvcrt.LK_NBLCK, 1)
                    msvcrt.locking(file_handle.fileno(), msvcrt.LK_UNLCK, 1)
                    return False
                except OSError:
                    return True
        return False
    except OSError:
        return True


def _read_sample_rows(path: Path, sample_rows: int) -> tuple[list[str], list[dict[str, str]], str]:
    if sample_rows <= 0:
        raise ValueError("sample_rows must be positive")

    last_error: UnicodeDecodeError | None = None
    for encoding in ("utf-8-sig", "cp949"):
        try:
            with path.open("r", newline="", encoding=encoding) as file_handle:
                reader = csv.DictReader(file_handle)
                fieldnames = [field.strip() for field in (reader.fieldnames or [])]
                rows = []
                for _, row in zip(range(sample_rows), reader):
                    rows.append({str(key).strip(): value for key, value in row.items() if key is not None})
                return fieldnames, rows, encoding
        except UnicodeDecodeError as error:
            last_error = error
            continue

    if last_error is not None:
        raise last_error
    return [], [], "utf-8-sig"


def _has_non_empty_row(rows: Iterable[dict[str, str]]) -> bool:
    return any(any(str(value).strip() for value in row.values()) for row in rows)


def _normalize_column(column: str) -> str:
    return re.sub(r"\[|\]", "", column).strip().lower()


def _sample_schema_matches(kind: PreviewSourceKind, columns: Iterable[str]) -> bool:
    column_set = {column.strip() for column in columns}
    normalized = {_normalize_column(column) for column in column_set}

    if kind == PreviewSourceKind.PLC:
        has_integrated_columns = {"Date", "Time", "Mold1"}.issubset(column_set)
        has_legacy_time_column = any(column in column_set for column in ("Time", "시간", "시각"))
        return has_integrated_columns or has_legacy_time_column

    if kind == PreviewSourceKind.TEMPERATURE:
        has_datetime_column = any(column in normalized for column in ("datetime", "date_time", "날짜시간", "일시"))
        has_date_column = any(column in normalized for column in ("date", "날짜", "일자"))
        has_time_column = any(column in normalized for column in ("time", "시간", "시각"))
        has_temperature_column = any(column in normalized for column in ("temperature", "온도", "temp"))
        return has_temperature_column and (has_datetime_column or (has_date_column and has_time_column))

    return False


def _safe_reason_text(reason_code: str) -> str:
    reason_texts = {
        "unsupported_extension": "File is not a CSV candidate.",
        "outside_date_range": "File date is outside the requested preview range.",
        "file_unstable": "File was modified too recently to scan safely.",
        "file_locked": "File appears to be locked by another process.",
        "file_missing": "Configured source folder or file is missing.",
        "read_error": "CSV sample could not be read.",
        "empty_file": "CSV contains no readable rows.",
        "schema_mismatch": "CSV schema does not match a supported extrusion source.",
        "transform_error": "CSV rows could not be transformed into reconciliation keys.",
        "timestamp_missing": "Transformed rows did not contain a valid timestamp.",
        "device_id_missing": "Transformed rows did not contain a valid device id.",
        "no_valid_keys": "CSV has no valid timestamp and device id keys.",
        "db_unreachable": "Local Supabase database could not be reached.",
        "db_query_failed": "Local Supabase exact-key query failed.",
        "db_no_match": "No local keys are present in the database.",
        "db_full_match": "Every local key is already present in the database.",
        "db_partial_match": "Some local keys are already present in the database.",
        "timeout": "Preview scan exceeded the configured time budget.",
        "cancelled": "Preview scan was cancelled.",
    }
    return reason_texts.get(reason_code, reason_code.replace("_", " "))


class CandidateScanner:
    def __init__(
        self,
        sources: Iterable[SourceFolder],
        *,
        now_provider: Callable[[], datetime] = kst_now,
    ) -> None:
        self._sources = tuple(sources)
        self._now_provider = now_provider

    def scan(
        self,
        date_window: DateWindow,
        options: PreviewScanOptions | None = None,
    ) -> tuple[CandidateFile, ...]:
        scan_options = options or PreviewScanOptions()
        candidates: list[CandidateFile] = []

        for source in self._sources:
            if not source.enabled:
                continue
            source_path = source.folder_path.expanduser()
            if not source_path.is_dir():
                candidates.append(self._excluded_missing_source(source))
                continue

            for entry in sorted(source_path.iterdir(), key=lambda path: path.name.lower()):
                if len(candidates) >= scan_options.max_files:
                    return tuple(candidates)
                if not entry.is_file():
                    continue
                candidates.append(self._scan_file(source, entry, date_window, scan_options))

        return tuple(candidates)

    def _excluded_missing_source(self, source: SourceFolder) -> CandidateFile:
        return CandidateFile(
            folder_label=source.folder_label,
            folder_path=source.folder_path,
            filename="",
            path=source.folder_path,
            kind=source.kind,
            file_key=f"{source.kind}:{source.folder_path}",
            file_date=None,
            size_bytes=None,
            mtime_ns=None,
            modified_at=None,
            status=PreviewItemStatus.EXCLUDED,
            reason_code="file_missing",
            reason_text=_safe_reason_text("file_missing"),
            issues=("configured_source_missing",),
        )

    def _scan_file(
        self,
        source: SourceFolder,
        path: Path,
        date_window: DateWindow,
        options: PreviewScanOptions,
    ) -> CandidateFile:
        try:
            stat = path.stat()
        except OSError as error:
            return self._candidate_with_status(
                source,
                path,
                None,
                None,
                None,
                None,
                PreviewItemStatus.EXCLUDED,
                "file_missing",
                (f"stat_error:{error.__class__.__name__}",),
            )

        modified_at = datetime.fromtimestamp(stat.st_mtime, timezone.utc).astimezone(KST)
        file_date = _parse_file_date_for_kind(source.kind, path.name)
        base = CandidateFile(
            folder_label=source.folder_label,
            folder_path=source.folder_path,
            filename=path.name,
            path=path,
            kind=source.kind,
            file_key=f"{source.kind}:{path.resolve()}",
            file_date=file_date,
            size_bytes=stat.st_size,
            mtime_ns=stat.st_mtime_ns,
            modified_at=modified_at,
        )

        if path.suffix.lower() != ".csv":
            return replace(
                base,
                status=PreviewItemStatus.EXCLUDED,
                reason_code="unsupported_extension",
                reason_text=_safe_reason_text("unsupported_extension"),
            )
        if file_date is None or not date_window.contains(file_date):
            return replace(
                base,
                status=PreviewItemStatus.EXCLUDED,
                reason_code="outside_date_range",
                reason_text=_safe_reason_text("outside_date_range"),
            )
        if modified_at > self._now_provider().astimezone(KST) - timedelta(minutes=options.stable_lag_minutes):
            return replace(
                base,
                status=PreviewItemStatus.EXCLUDED,
                reason_code="file_unstable",
                reason_text=_safe_reason_text("file_unstable"),
            )
        if options.check_locks and _is_locked(path):
            return replace(
                base,
                status=PreviewItemStatus.EXCLUDED,
                reason_code="file_locked",
                reason_text=_safe_reason_text("file_locked"),
            )

        try:
            columns, rows, _ = _read_sample_rows(path, options.sample_rows)
        except csv.Error as error:
            return replace(
                base,
                status=PreviewItemStatus.RISKY,
                reason_code="read_error",
                reason_text=_safe_reason_text("read_error"),
                issues=(f"csv_error:{error.__class__.__name__}",),
                scan_mode=ScanMode.SAMPLE,
            )
        except OSError as error:
            return replace(
                base,
                status=PreviewItemStatus.RISKY,
                reason_code="read_error",
                reason_text=_safe_reason_text("read_error"),
                issues=(f"os_error:{error.__class__.__name__}",),
                scan_mode=ScanMode.SAMPLE,
            )
        except UnicodeDecodeError:
            return replace(
                base,
                status=PreviewItemStatus.RISKY,
                reason_code="read_error",
                reason_text=_safe_reason_text("read_error"),
                scan_mode=ScanMode.SAMPLE,
            )

        if not columns or not rows or not _has_non_empty_row(rows):
            return replace(
                base,
                status=PreviewItemStatus.EXCLUDED,
                reason_code="empty_file",
                reason_text=_safe_reason_text("empty_file"),
                scan_mode=ScanMode.SAMPLE,
                sample_row_count=len(rows),
            )
        if not _sample_schema_matches(source.kind, columns):
            return replace(
                base,
                status=PreviewItemStatus.RISKY,
                reason_code="schema_mismatch",
                reason_text=_safe_reason_text("schema_mismatch"),
                scan_mode=ScanMode.SAMPLE,
                sample_row_count=len(rows),
            )

        return replace(base, scan_mode=ScanMode.SAMPLE, sample_row_count=len(rows))

    def _candidate_with_status(
        self,
        source: SourceFolder,
        path: Path,
        file_date: date | None,
        size_bytes: int | None,
        mtime_ns: int | None,
        modified_at: datetime | None,
        status: PreviewItemStatus,
        reason_code: str,
        issues: tuple[str, ...] = (),
    ) -> CandidateFile:
        return CandidateFile(
            folder_label=source.folder_label,
            folder_path=source.folder_path,
            filename=path.name,
            path=path,
            kind=source.kind,
            file_key=f"{source.kind}:{path}",
            file_date=file_date,
            size_bytes=size_bytes,
            mtime_ns=mtime_ns,
            modified_at=modified_at,
            status=status,
            reason_code=reason_code,
            reason_text=_safe_reason_text(reason_code),
            issues=issues,
        )


class CsvKeyExtractor:
    def extract(
        self,
        candidate: CandidateFile,
        options: KeyExtractionOptions | None = None,
        *,
        cancel_check: CancelCheck | None = None,
    ) -> KeyExtractionResult:
        extraction_options = options or KeyExtractionOptions()
        started_at = time.monotonic()
        keys: set[MetricKey] = set()
        row_count = 0
        first_timestamp: str | None = None
        last_timestamp: str | None = None
        device_ids: set[str] = set()

        try:
            for row in self._iter_rows(candidate.path):
                if cancel_check is not None and cancel_check():
                    raise TimeoutError("cancelled")
                if time.monotonic() - started_at > extraction_options.max_file_seconds:
                    raise TimeoutError("timeout")

                key = self._key_for_row(candidate, row)
                if key is None:
                    continue
                timestamp, device_id = key
                row_count += 1
                keys.add(key)
                device_ids.add(device_id)
                first_timestamp = timestamp if first_timestamp is None or timestamp < first_timestamp else first_timestamp
                last_timestamp = timestamp if last_timestamp is None or timestamp > last_timestamp else last_timestamp

                if row_count % extraction_options.chunk_rows == 0:
                    # This boundary is intentionally explicit so callers can add cancellation
                    # or progress hooks later without changing key semantics.
                    continue
        except TimeoutError:
            raise
        except (OSError, csv.Error, UnicodeDecodeError) as error:
            raise ValueError(f"CSV key extraction failed for {candidate.path}") from error

        return KeyExtractionResult(
            candidate=candidate,
            keys=frozenset(keys),
            row_count=row_count,
            local_key_count=len(keys),
            first_timestamp=first_timestamp,
            last_timestamp=last_timestamp,
            device_ids=tuple(sorted(device_ids)),
        )

    def _iter_rows(self, path: Path) -> Iterator[dict[str, str]]:
        last_error: UnicodeDecodeError | None = None
        for encoding in ("utf-8-sig", "cp949"):
            try:
                with path.open("r", newline="", encoding=encoding) as file_handle:
                    reader = csv.DictReader(file_handle)
                    for row in reader:
                        yield {str(key).strip(): value for key, value in row.items() if key is not None}
                return
            except UnicodeDecodeError as error:
                last_error = error
                continue
        if last_error is not None:
            raise last_error

    def _key_for_row(self, candidate: CandidateFile, row: dict[str, str]) -> MetricKey | None:
        if candidate.kind == PreviewSourceKind.PLC:
            return self._plc_key_for_row(candidate, row)
        if candidate.kind == PreviewSourceKind.TEMPERATURE:
            return self._temperature_key_for_row(row)
        return None

    def _plc_key_for_row(self, candidate: CandidateFile, row: dict[str, str]) -> MetricKey | None:
        if {"Date", "Time", "Mold1"}.issubset(row):
            timestamp = _canonical_timestamp(f"{row.get('Date', '')} {row.get('Time', '')}")
            device_id = INTEGRATED_PLC_DEVICE_ID
        else:
            time_value = _first_present(row, ("Time", "시간", "시각"))
            if candidate.file_date is None or time_value is None:
                return None
            timestamp = _canonical_timestamp(f"{candidate.file_date.isoformat()} {time_value}")
            device_id = PLC_DEVICE_ID

        if timestamp is None:
            return None
        return timestamp, device_id

    def _temperature_key_for_row(self, row: dict[str, str]) -> MetricKey | None:
        normalized = {_normalize_column(column): column for column in row}
        datetime_column = _first_key(normalized, ("datetime", "date_time", "날짜시간", "일시"))
        if datetime_column is not None:
            timestamp = _canonical_timestamp(row.get(datetime_column, ""))
        else:
            date_column = _first_key(normalized, ("date", "날짜", "일자"))
            time_column = _first_key(normalized, ("time", "시간", "시각"))
            if date_column is None or time_column is None:
                return None
            timestamp = _canonical_timestamp(f"{row.get(date_column, '')} {row.get(time_column, '')}")

        if timestamp is None:
            return None
        return timestamp, TEMPERATURE_DEVICE_ID


def _first_present(row: dict[str, str], candidates: Iterable[str]) -> str | None:
    for candidate in candidates:
        value = row.get(candidate)
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def _first_key(mapping: dict[str, str], candidates: Iterable[str]) -> str | None:
    for candidate in candidates:
        value = mapping.get(candidate)
        if value is not None:
            return value
    return None


def _canonical_timestamp(value: str) -> str | None:
    cleaned = value.strip()
    if not cleaned:
        return None

    normalized = cleaned.replace("T", " ")
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"

    parsed: datetime | None = None
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        for fmt in (
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d %H:%M:%S.%f",
            "%Y/%m/%d %H:%M:%S",
            "%y-%m-%d %H:%M:%S.%f",
            "%y-%m-%d %H:%M:%S",
        ):
            try:
                parsed = datetime.strptime(normalized, fmt)
                break
            except ValueError:
                continue

    if parsed is None:
        time_only = _parse_time_only(cleaned)
        if time_only is None:
            return None
        return time_only.strftime("%H:%M:%S.%f")

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=KST)
    else:
        parsed = parsed.astimezone(KST)
    return parsed.strftime("%Y-%m-%dT%H:%M:%S.%f+09:00")


def _parse_time_only(value: str) -> datetime_time | None:
    for fmt in ("%H:%M:%S.%f", "%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(value, fmt).time()
        except ValueError:
            continue
    return None


class SupabaseExactReconciler:
    def __init__(self, db_url: str | None, *, batch_size: int = 1000) -> None:
        self._db_url = db_url
        self._batch_size = max(1, batch_size)

    def find_existing_keys(self, keys: Iterable[MetricKey]) -> ReconciliationResult:
        distinct_keys = tuple(dict.fromkeys(keys))
        if not distinct_keys:
            return ReconciliationResult(db_status=DbStatus.REACHABLE)
        if not self._db_url:
            return ReconciliationResult(
                db_status=DbStatus.UNREACHABLE,
                error_code="db_unreachable",
                error_message="SUPABASE_DB_URL is not configured.",
            )

        try:
            import psycopg  # type: ignore[import-not-found]
        except ImportError:
            return ReconciliationResult(
                db_status=DbStatus.UNREACHABLE,
                error_code="db_unreachable",
                error_message="psycopg is not installed in the backend environment.",
            )

        matched: set[MetricKey] = set()
        try:
            with psycopg.connect(self._db_url) as connection:
                with connection.transaction():
                    connection.execute("SET TRANSACTION READ ONLY")
                    for batch in _batched(distinct_keys, self._batch_size):
                        matched.update(self._query_batch(connection, batch))
        except psycopg.OperationalError as error:
            return ReconciliationResult(
                db_status=DbStatus.UNREACHABLE,
                error_code="db_unreachable",
                error_message=str(error),
            )
        except Exception as error:
            return ReconciliationResult(
                db_status=DbStatus.QUERY_FAILED,
                error_code="db_query_failed",
                error_message=str(error),
            )

        return ReconciliationResult(db_status=DbStatus.REACHABLE, matched_keys=frozenset(matched))

    def _query_batch(self, connection: object, batch: tuple[MetricKey, ...]) -> set[MetricKey]:
        values_sql = ", ".join(["(%s::text, %s::timestamptz, %s::text)"] * len(batch))
        params: list[str] = []
        for timestamp, device_id in batch:
            params.extend([timestamp, timestamp, device_id])

        query = f"""
            WITH candidate_keys(local_timestamp, ts, device_id) AS (
              VALUES {values_sql}
            )
            SELECT c.local_timestamp, c.device_id
            FROM candidate_keys c
            JOIN public.all_metrics m
              ON m."timestamp" = c.ts
             AND m.device_id = c.device_id
        """
        cursor = connection.execute(query, params)  # type: ignore[attr-defined]
        return {(str(timestamp), str(device_id)) for timestamp, device_id in cursor.fetchall()}


def _batched(values: tuple[MetricKey, ...], batch_size: int) -> Iterator[tuple[MetricKey, ...]]:
    for index in range(0, len(values), batch_size):
        yield values[index : index + batch_size]


def classify_local_candidate(candidate: CandidateFile) -> PreviewClassification | None:
    if candidate.status is None:
        return None
    return PreviewClassification(
        status=candidate.status,
        reason_code=candidate.reason_code or "excluded",
        reason_text=candidate.reason_text or _safe_reason_text(candidate.reason_code or "excluded"),
    )


def classify_reconciliation(local_key_count: int, db_match_count: int) -> PreviewClassification:
    if local_key_count <= 0:
        return PreviewClassification(
            status=PreviewItemStatus.EXCLUDED,
            reason_code="no_valid_keys",
            reason_text=_safe_reason_text("no_valid_keys"),
        )
    if db_match_count <= 0:
        return PreviewClassification(
            status=PreviewItemStatus.TARGET,
            reason_code="db_no_match",
            reason_text=_safe_reason_text("db_no_match"),
            db_match_count=0,
            upload_row_estimate=local_key_count,
        )
    if db_match_count >= local_key_count:
        return PreviewClassification(
            status=PreviewItemStatus.ALREADY_IN_DB,
            reason_code="db_full_match",
            reason_text=_safe_reason_text("db_full_match"),
            db_match_count=local_key_count,
            upload_row_estimate=0,
        )
    return PreviewClassification(
        status=PreviewItemStatus.PARTIAL_OVERLAP,
        reason_code="db_partial_match",
        reason_text=_safe_reason_text("db_partial_match"),
        db_match_count=db_match_count,
        upload_row_estimate=local_key_count - db_match_count,
    )


def classify_risky(reason_code: str, *, db_match_count: int = 0) -> PreviewClassification:
    return PreviewClassification(
        status=PreviewItemStatus.RISKY,
        reason_code=reason_code,
        reason_text=_safe_reason_text(reason_code),
        db_match_count=db_match_count,
        upload_row_estimate=0,
    )


@dataclass
class PreviewReconciliationService:
    scanner: CandidateScanner
    extractor: CsvKeyExtractor
    reconciler: ExactReconciler
    scan_options: PreviewScanOptions = field(default_factory=PreviewScanOptions)
    extraction_options: KeyExtractionOptions = field(default_factory=KeyExtractionOptions)

    def build_preview_items(
        self,
        date_window: DateWindow,
        *,
        cancel_check: CancelCheck | None = None,
    ) -> tuple[ReconciledPreviewItem, ...]:
        candidates = self.scanner.scan(date_window, self.scan_options)
        local_results: list[ReconciledPreviewItem] = []
        extractions: list[KeyExtractionResult] = []
        all_keys: set[MetricKey] = set()

        for candidate in candidates:
            local_classification = classify_local_candidate(candidate)
            if local_classification is not None:
                local_results.append(ReconciledPreviewItem(candidate=candidate, classification=local_classification))
                continue

            try:
                extraction = self.extractor.extract(
                    candidate,
                    self.extraction_options,
                    cancel_check=cancel_check,
                )
            except TimeoutError as error:
                reason_code = "cancelled" if str(error) == "cancelled" else "timeout"
                local_results.append(
                    ReconciledPreviewItem(
                        candidate=candidate,
                        classification=classify_risky(reason_code),
                        issues=(reason_code,),
                    )
                )
                continue
            except ValueError as error:
                local_results.append(
                    ReconciledPreviewItem(
                        candidate=candidate,
                        classification=classify_risky("transform_error"),
                        issues=(f"transform_error:{error.__class__.__name__}",),
                    )
                )
                continue

            if extraction.local_key_count == 0:
                local_results.append(
                    ReconciledPreviewItem(
                        candidate=candidate,
                        classification=classify_reconciliation(0, 0),
                        row_count=extraction.row_count,
                        local_key_count=0,
                        device_ids=extraction.device_ids,
                    )
                )
                continue

            extractions.append(extraction)
            all_keys.update(extraction.keys)

        db_result = self.reconciler.find_existing_keys(all_keys)
        if db_result.db_status != DbStatus.REACHABLE:
            reason_code = db_result.error_code or "db_unreachable"
            return tuple(
                local_results
                + [
                    ReconciledPreviewItem(
                        candidate=extraction.candidate,
                        classification=classify_risky(reason_code),
                        row_count=extraction.row_count,
                        local_key_count=extraction.local_key_count,
                        first_timestamp=extraction.first_timestamp,
                        last_timestamp=extraction.last_timestamp,
                        device_ids=extraction.device_ids,
                        issues=tuple(filter(None, (db_result.error_message,))),
                    )
                    for extraction in extractions
                ]
            )

        reconciled = list(local_results)
        for extraction in extractions:
            db_match_count = len(extraction.keys.intersection(db_result.matched_keys))
            reconciled.append(
                ReconciledPreviewItem(
                    candidate=extraction.candidate,
                    classification=classify_reconciliation(extraction.local_key_count, db_match_count),
                    row_count=extraction.row_count,
                    local_key_count=extraction.local_key_count,
                    first_timestamp=extraction.first_timestamp,
                    last_timestamp=extraction.last_timestamp,
                    device_ids=extraction.device_ids,
                    issues=extraction.issues,
                )
            )

        return tuple(reconciled)
