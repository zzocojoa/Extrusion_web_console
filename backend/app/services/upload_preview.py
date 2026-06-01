import csv
import hashlib
import os
import re
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Protocol

from backend.app.core.settings import Settings
from backend.app.db.preview_repository import PreviewRepository, iso_now
from backend.app.schemas.upload_preview import (
    PreviewCreateRequest,
    PreviewDbStatus,
    PreviewItemStatus,
    PreviewRunStatus,
    PreviewSource,
)

KST = timezone(timedelta(hours=9))
PLC_DEVICE_ID = "extruder_plc"
INTEGRATED_PLC_DEVICE_ID = "extruder_integrated"
TEMPERATURE_DEVICE_ID = "spot_temperature_sensor"


class PreviewDbUnavailableError(RuntimeError):
    pass


class ExactReconciler(Protocol):
    def find_existing_keys(self, keys: set[tuple[str, str]]) -> set[tuple[str, str]]:
        ...


@dataclass(frozen=True)
class SourceFolder:
    label: str
    kind: str
    path: Path


@dataclass(frozen=True)
class CandidateFile:
    source: SourceFolder
    path: Path
    file_date: date | None
    stat: os.stat_result


@dataclass
class KeyExtractionResult:
    row_count: int
    local_keys: set[tuple[str, str]]
    first_timestamp: str | None
    last_timestamp: str | None
    device_ids: list[str]


def parse_plc_file_date(filename: str) -> date | None:
    legacy_match = re.match(r"^(\d{2})(\d{2})(\d{2})", filename)
    if legacy_match:
        year, month, day = legacy_match.groups()
        try:
            return date(int(f"20{year}"), int(month), int(day))
        except ValueError:
            return None
    integrated_match = re.search(r"Factory_Integrated_Log_(\d{4})(\d{2})(\d{2})", filename)
    if integrated_match:
        year, month, day = integrated_match.groups()
        try:
            return date(int(year), int(month), int(day))
        except ValueError:
            return None
    return None


def parse_temperature_file_date(filename: str) -> date | None:
    match = re.search(r"(\d{4})-(\d{2})-(\d{2})", filename)
    if not match:
        return None
    year, month, day = match.groups()
    try:
        return date(int(year), int(month), int(day))
    except ValueError:
        return None


def date_window(request: PreviewCreateRequest, now: datetime | None = None) -> tuple[date, date]:
    current = (now or datetime.now(KST)).astimezone(KST).date()
    if request.range_mode.value == "today":
        return current, current
    if request.range_mode.value == "yesterday":
        previous = current - timedelta(days=1)
        return previous, previous
    if request.range_mode.value == "last_2_days":
        return current - timedelta(days=1), current
    if request.start_date is None or request.end_date is None:
        raise ValueError("custom range requires startDate and endDate")
    return request.start_date, request.end_date


class CandidateScanner:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def source_folders(self, sources: Iterable[PreviewSource]) -> list[SourceFolder]:
        folders: list[SourceFolder] = []
        source_set = set(sources)
        if PreviewSource.plc in source_set and self.settings.plc_data_dir:
            folders.append(SourceFolder("PLC", "plc", Path(self.settings.plc_data_dir)))
        if PreviewSource.temperature in source_set and self.settings.temperature_data_dir:
            folders.append(
                SourceFolder("Temperature", "temperature", Path(self.settings.temperature_data_dir))
            )
        return folders

    def scan(self, request: PreviewCreateRequest) -> tuple[list[CandidateFile], list[dict[str, object]]]:
        start_date, end_date = date_window(request)
        candidates: list[CandidateFile] = []
        local_issues: list[dict[str, object]] = []
        folders = self.source_folders(request.sources)
        if not folders:
            source = SourceFolder("PLC", "plc", Path(""))
            local_issues.append(
                self._issue_item(
                    source,
                    Path("(not configured)"),
                    PreviewItemStatus.risky,
                    "source_not_configured",
                    "Preview source folder is not configured.",
                )
            )
            return candidates, local_issues

        now_ts = time.time()
        stable_before = now_ts - (request.options.stable_lag_minutes * 60)
        for folder in folders:
            if not folder.path.exists() or not folder.path.is_dir():
                local_issues.append(
                    self._issue_item(
                        folder,
                        folder.path,
                        PreviewItemStatus.risky,
                        "source_missing",
                        "Configured source folder is missing.",
                    )
                )
                continue
            count = 0
            for entry in sorted(folder.path.iterdir(), key=lambda value: value.name.lower()):
                if count >= request.options.max_files:
                    break
                if entry.suffix.lower() != ".csv":
                    continue
                try:
                    stat = entry.stat()
                except OSError as error:
                    local_issues.append(
                        self._issue_item(
                            folder,
                            entry,
                            PreviewItemStatus.risky,
                            "file_missing",
                            f"Could not read file metadata: {error}",
                        )
                    )
                    continue
                if stat.st_mtime > stable_before:
                    local_issues.append(
                        self._issue_item(
                            folder,
                            entry,
                            PreviewItemStatus.excluded,
                            "file_unstable",
                            "File was modified too recently.",
                            stat,
                        )
                    )
                    continue
                file_date = (
                    parse_plc_file_date(entry.name)
                    if folder.kind == "plc"
                    else parse_temperature_file_date(entry.name)
                )
                if file_date is None:
                    local_issues.append(
                        self._issue_item(
                            folder,
                            entry,
                            PreviewItemStatus.excluded,
                            "file_date_missing",
                            "File date could not be parsed.",
                            stat,
                        )
                    )
                    continue
                if file_date < start_date or file_date > end_date:
                    local_issues.append(
                        self._issue_item(
                            folder,
                            entry,
                            PreviewItemStatus.excluded,
                            "outside_date_range",
                            "File date is outside the preview range.",
                            stat,
                            file_date,
                        )
                    )
                    continue
                candidates.append(CandidateFile(folder, entry, file_date, stat))
                count += 1
        return candidates, local_issues

    def _issue_item(
        self,
        source: SourceFolder,
        path: Path,
        status: PreviewItemStatus,
        reason_code: str,
        reason_text: str,
        stat: os.stat_result | None = None,
        file_date: date | None = None,
    ) -> dict[str, object]:
        return {
            "file_key": build_file_key(source.path, path, stat),
            "folder_label": source.label,
            "folder_path": str(source.path),
            "filename": path.name,
            "path": str(path),
            "kind": source.kind,
            "file_date": file_date.isoformat() if file_date else None,
            "size_bytes": None if stat is None else stat.st_size,
            "mtime_ns": None if stat is None else stat.st_mtime_ns,
            "modified_at": None if stat is None else datetime.fromtimestamp(stat.st_mtime, KST).isoformat(),
            "file_signature": build_file_signature(path, stat),
            "status": status.value,
            "reason_code": reason_code,
            "reason_text": reason_text,
            "scan_mode": "metadata",
            "sample_row_count": None,
            "row_count": None,
            "local_key_count": None,
            "db_match_count": None,
            "upload_row_estimate": None,
            "first_timestamp": None,
            "last_timestamp": None,
            "device_ids": [],
            "issues": [{"code": reason_code, "message": reason_text}],
            "error_code": reason_code if status == PreviewItemStatus.risky else None,
            "error_message": reason_text if status == PreviewItemStatus.risky else None,
        }


class CsvKeyExtractor:
    def extract(self, candidate: CandidateFile, max_file_seconds: int) -> KeyExtractionResult:
        started = time.monotonic()
        row_count = 0
        keys: set[tuple[str, str]] = set()
        first_timestamp: str | None = None
        last_timestamp: str | None = None
        device_ids: set[str] = set()
        try:
            rows = self._open_rows(candidate.path)
            for row in rows:
                if time.monotonic() - started > max_file_seconds:
                    raise TimeoutError("CSV key extraction timed out")
                row_count += 1
                timestamp, device_id = self._extract_key(candidate, row)
                if not timestamp or not device_id:
                    continue
                keys.add((timestamp, device_id))
                device_ids.add(device_id)
                if first_timestamp is None or timestamp < first_timestamp:
                    first_timestamp = timestamp
                if last_timestamp is None or timestamp > last_timestamp:
                    last_timestamp = timestamp
        except UnicodeDecodeError:
            rows = self._open_rows(candidate.path, encoding="cp949")
            for row in rows:
                if time.monotonic() - started > max_file_seconds:
                    raise TimeoutError("CSV key extraction timed out")
                row_count += 1
                timestamp, device_id = self._extract_key(candidate, row)
                if not timestamp or not device_id:
                    continue
                keys.add((timestamp, device_id))
                device_ids.add(device_id)
                if first_timestamp is None or timestamp < first_timestamp:
                    first_timestamp = timestamp
                if last_timestamp is None or timestamp > last_timestamp:
                    last_timestamp = timestamp
        return KeyExtractionResult(
            row_count=row_count,
            local_keys=keys,
            first_timestamp=first_timestamp,
            last_timestamp=last_timestamp,
            device_ids=sorted(device_ids),
        )

    def _open_rows(self, path: Path, encoding: str = "utf-8-sig") -> Iterable[dict[str, str]]:
        with path.open("r", encoding=encoding, newline="") as handle:
            reader = csv.DictReader(handle)
            yield from reader

    def _extract_key(self, candidate: CandidateFile, row: dict[str, str]) -> tuple[str | None, str | None]:
        timestamp = clean(row.get("timestamp")) or clean(row.get("Timestamp"))
        device_id = clean(row.get("device_id")) or clean(row.get("Device ID"))
        if timestamp and device_id:
            return timestamp, device_id

        if candidate.source.kind == "plc":
            if {"Date", "Time"}.issubset(row.keys()):
                timestamp = build_integrated_timestamp(row.get("Date"), row.get("Time"))
                return timestamp, INTEGRATED_PLC_DEVICE_ID
            time_value = clean(row.get("Time")) or clean(row.get("time"))
            if time_value and candidate.file_date:
                return f"{candidate.file_date.isoformat()}T{time_value}+09:00", PLC_DEVICE_ID

        if candidate.source.kind == "temperature":
            timestamp = (
                clean(row.get("datetime"))
                or clean(row.get("Datetime"))
                or clean(row.get("date_time"))
            )
            if timestamp:
                return timestamp, TEMPERATURE_DEVICE_ID
            date_value = clean(row.get("date")) or clean(row.get("Date"))
            time_value = clean(row.get("time")) or clean(row.get("Time"))
            if date_value and time_value:
                return f"{date_value}T{time_value}+09:00", TEMPERATURE_DEVICE_ID

        return None, None


class SupabaseExactReconciler:
    def __init__(self, db_url: str) -> None:
        self.db_url = db_url

    def find_existing_keys(self, keys: set[tuple[str, str]]) -> set[tuple[str, str]]:
        if not self.db_url:
            raise PreviewDbUnavailableError("SUPABASE_DB_URL is not configured")
        try:
            import psycopg  # type: ignore[import-not-found]
        except Exception as error:
            raise PreviewDbUnavailableError("psycopg is not installed") from error

        existing: set[tuple[str, str]] = set()
        sorted_keys = sorted(keys)
        try:
            with psycopg.connect(self.db_url, autocommit=True) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    for index in range(0, len(sorted_keys), 1000):
                        batch = sorted_keys[index : index + 1000]
                        values_sql = ",".join(["(%s::timestamptz,%s::text)"] * len(batch))
                        params: list[str] = []
                        for timestamp, device_id in batch:
                            params.extend([timestamp, device_id])
                        cursor.execute(
                            f"""
                            WITH candidate_keys(timestamp, device_id) AS (
                              VALUES {values_sql}
                            )
                            SELECT c.timestamp::text, c.device_id
                            FROM candidate_keys c
                            JOIN public.all_metrics m
                              ON m."timestamp" = c.timestamp
                             AND m.device_id = c.device_id
                            """,
                            params,
                        )
                        for timestamp, device_id in cursor.fetchall():
                            existing.add((str(timestamp), str(device_id)))
        except Exception as error:
            raise PreviewDbUnavailableError(str(error)) from error
        return existing


class PreviewService:
    def __init__(
        self,
        settings: Settings,
        repository: PreviewRepository,
        reconciler: ExactReconciler | None = None,
    ) -> None:
        self.settings = settings
        self.repository = repository
        self.scanner = CandidateScanner(settings)
        self.extractor = CsvKeyExtractor()
        self.reconciler = reconciler or SupabaseExactReconciler(settings.supabase_db_url)

    def run_preview(self, preview_run_id: str, request: PreviewCreateRequest) -> None:
        self.repository.update_run(
            preview_run_id,
            status=PreviewRunStatus.running.value,
            started_at=iso_now(),
        )
        try:
            candidates, local_items = self.scanner.scan(request)
            for item in local_items:
                self.repository.insert_item(preview_run_id, item)
            if self.repository.is_cancel_requested(preview_run_id):
                self.repository.recompute_summary(
                    preview_run_id,
                    status=PreviewRunStatus.cancelled,
                    db_status=PreviewDbStatus.not_checked,
                )
                return

            db_error: str | None = None
            any_db_unreachable = False
            for candidate in candidates:
                if self.repository.is_cancel_requested(preview_run_id):
                    self.repository.recompute_summary(
                        preview_run_id,
                        status=PreviewRunStatus.cancelled,
                        db_status=PreviewDbStatus.not_checked,
                    )
                    return
                try:
                    extraction = self.extractor.extract(candidate, request.options.max_file_seconds)
                    if not extraction.local_keys:
                        self.repository.insert_item(
                            preview_run_id,
                            build_result_item(
                                candidate,
                                PreviewItemStatus.excluded,
                                "no_valid_keys",
                                "No valid timestamp/device_id keys were found.",
                                extraction,
                            ),
                        )
                        continue
                    try:
                        existing = self.reconciler.find_existing_keys(extraction.local_keys)
                        status, reason_code, reason_text = classify_keys(
                            len(extraction.local_keys),
                            len(existing),
                        )
                        self.repository.insert_item(
                            preview_run_id,
                            build_result_item(
                                candidate,
                                status,
                                reason_code,
                                reason_text,
                                extraction,
                                db_match_count=len(existing),
                            ),
                        )
                    except PreviewDbUnavailableError as error:
                        any_db_unreachable = True
                        db_error = str(error)
                        self.repository.insert_item(
                            preview_run_id,
                            build_result_item(
                                candidate,
                                PreviewItemStatus.risky,
                                "db_unreachable",
                                "Local Supabase DB could not be reached.",
                                extraction,
                                error_message=db_error,
                            ),
                        )
                except TimeoutError as error:
                    self.repository.insert_item(
                        preview_run_id,
                        build_error_item(candidate, "timeout", str(error)),
                    )
                except Exception as error:
                    self.repository.insert_item(
                        preview_run_id,
                        build_error_item(candidate, "transform_error", str(error)),
                    )

            if any_db_unreachable:
                self.repository.recompute_summary(
                    preview_run_id,
                    status=PreviewRunStatus.partial_failed,
                    db_status=PreviewDbStatus.unreachable,
                    error_code="db_unreachable",
                    error_message=db_error,
                )
            else:
                self.repository.recompute_summary(
                    preview_run_id,
                    status=PreviewRunStatus.succeeded,
                    db_status=PreviewDbStatus.reachable if candidates else PreviewDbStatus.not_checked,
                )
        except Exception as error:
            self.repository.recompute_summary(
                preview_run_id,
                status=PreviewRunStatus.failed,
                db_status=PreviewDbStatus.not_checked,
                error_code="preview_failed",
                error_message=str(error),
            )


def classify_keys(local_key_count: int, db_match_count: int) -> tuple[PreviewItemStatus, str, str]:
    if db_match_count == 0:
        return PreviewItemStatus.target, "db_no_match", "No matching rows were found in DB."
    if db_match_count >= local_key_count:
        return PreviewItemStatus.already_in_db, "db_full_match", "All local keys already exist in DB."
    return PreviewItemStatus.partial_overlap, "db_partial_match", "Some local keys already exist in DB."


def classify_reconciliation(
    *,
    local_keys: set[tuple[str, str]],
    matched_keys: set[tuple[str, str]] | None,
    db_status: str = "reachable",
    error_code: str | None = None,
) -> dict[str, object]:
    if db_status == "unreachable" or matched_keys is None:
        return {
            "status": PreviewItemStatus.risky,
            "reason_code": error_code or "db_unreachable",
            "db_match_count": None,
            "upload_row_estimate": 0,
        }
    exact_matches = set(local_keys) & set(matched_keys)
    status, reason_code, _reason_text = classify_keys(len(local_keys), len(exact_matches))
    return {
        "status": status,
        "reason_code": reason_code,
        "db_match_count": len(exact_matches),
        "upload_row_estimate": max(0, len(local_keys) - len(exact_matches))
        if status != PreviewItemStatus.already_in_db
        else 0,
    }


def build_result_item(
    candidate: CandidateFile,
    status: PreviewItemStatus,
    reason_code: str,
    reason_text: str,
    extraction: KeyExtractionResult,
    *,
    db_match_count: int = 0,
    error_message: str | None = None,
) -> dict[str, object]:
    local_count = len(extraction.local_keys)
    upload_estimate = max(0, local_count - db_match_count) if status != PreviewItemStatus.excluded else 0
    return {
        "file_key": build_file_key(candidate.source.path, candidate.path, candidate.stat),
        "folder_label": candidate.source.label,
        "folder_path": str(candidate.source.path),
        "filename": candidate.path.name,
        "path": str(candidate.path),
        "kind": candidate.source.kind,
        "file_date": candidate.file_date.isoformat() if candidate.file_date else None,
        "size_bytes": candidate.stat.st_size,
        "mtime_ns": candidate.stat.st_mtime_ns,
        "modified_at": datetime.fromtimestamp(candidate.stat.st_mtime, KST).isoformat(),
        "file_signature": build_file_signature(candidate.path, candidate.stat),
        "status": status.value,
        "reason_code": reason_code,
        "reason_text": reason_text,
        "scan_mode": "full",
        "sample_row_count": None,
        "row_count": extraction.row_count,
        "local_key_count": local_count,
        "db_match_count": db_match_count,
        "upload_row_estimate": upload_estimate,
        "first_timestamp": extraction.first_timestamp,
        "last_timestamp": extraction.last_timestamp,
        "device_ids": extraction.device_ids,
        "issues": [] if error_message is None else [{"code": reason_code, "message": error_message}],
        "error_code": reason_code if status == PreviewItemStatus.risky else None,
        "error_message": error_message,
    }


def build_error_item(candidate: CandidateFile, reason_code: str, reason_text: str) -> dict[str, object]:
    extraction = KeyExtractionResult(0, set(), None, None, [])
    return build_result_item(
        candidate,
        PreviewItemStatus.risky,
        reason_code,
        reason_text,
        extraction,
        error_message=reason_text,
    ) | {"scan_mode": "incomplete"}


def build_file_key(folder: Path, path: Path, stat: os.stat_result | None) -> str:
    signature = build_file_signature(path, stat)
    return f"{folder.resolve()}::{path.name}::{signature}"


def build_file_signature(path: Path, stat: os.stat_result | None) -> str:
    if stat is None:
        return hashlib.sha256(str(path).encode("utf-8")).hexdigest()
    return f"size={stat.st_size}|mtime_ns={stat.st_mtime_ns}"


def clean(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def build_integrated_timestamp(date_value: object, time_value: object) -> str | None:
    date_text = clean(date_value)
    time_text = clean(time_value)
    if not date_text or not time_text:
        return None
    parsed = None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
        try:
            parsed = datetime.strptime(f"{date_text} {time_text}", fmt)
            break
        except ValueError:
            continue
    if parsed is None:
        return f"{date_text}T{time_text}+09:00"
    return parsed.replace(tzinfo=KST).isoformat()
