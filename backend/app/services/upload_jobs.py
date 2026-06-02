import csv
import time
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from backend.app.core.settings import Settings
from backend.app.db.upload_job_repository import UploadJobRepository, decode_json
from backend.app.schemas.upload_jobs import UploadJobOptions, UploadJobStatus
from backend.app.services.upload_preview import (
    INTEGRATED_PLC_DEVICE_ID,
    KST,
    PLC_DEVICE_ID,
    TEMPERATURE_DEVICE_ID,
    build_file_signature,
    build_integrated_timestamp,
    clean,
)


class UploadJobCancelled(RuntimeError):
    pass


@dataclass
class UploadCounters:
    processed_rows: int = 0
    uploaded_rows: int = 0
    inserted_rows: int = 0


def build_upload_headers(anon_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {anon_key}",
        "apikey": anon_key,
        "Content-Type": "application/json",
    }


class CsvUploadRecordReader:
    def iter_records(self, file_row: Any, chunk_rows: int, start_offset: int = 0) -> Iterable[list[dict[str, Any]]]:
        path = Path(file_row["path"])
        encoding = "utf-8-sig"
        try:
            yield from self._iter_records_with_encoding(file_row, path, encoding, chunk_rows, start_offset)
        except UnicodeDecodeError:
            yield from self._iter_records_with_encoding(file_row, path, "cp949", chunk_rows, start_offset)

    def _iter_records_with_encoding(
        self,
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
                record = self._row_to_record(file_row, row)
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

    def count_records(self, file_row: Any) -> int:
        count = 0
        for chunk in self.iter_records(file_row, chunk_rows=10_000, start_offset=0):
            count += len(chunk)
        return count

    def _row_to_record(self, file_row: Any, row: dict[str, str]) -> dict[str, Any] | None:
        timestamp, device_id = self._extract_key(file_row, row)
        if not timestamp or not device_id:
            return None
        record: dict[str, Any] = {"timestamp": timestamp, "device_id": device_id}
        for key, value in row.items():
            normalized_key = normalize_column_name(key)
            if normalized_key in {"timestamp", "device_id"}:
                continue
            clean_value = clean(value)
            if clean_value is None:
                record[normalized_key] = None
            else:
                record[normalized_key] = coerce_value(clean_value)
        return record

    def _extract_key(self, file_row: Any, row: dict[str, str]) -> tuple[str | None, str | None]:
        timestamp = clean(row.get("timestamp")) or clean(row.get("Timestamp"))
        device_id = clean(row.get("device_id")) or clean(row.get("Device ID"))
        if timestamp and device_id:
            return timestamp, device_id

        kind = str(file_row["kind"])
        if kind == "plc":
            if {"Date", "Time"}.issubset(row.keys()):
                return build_integrated_timestamp(row.get("Date"), row.get("Time")), INTEGRATED_PLC_DEVICE_ID
            time_value = clean(row.get("Time")) or clean(row.get("time"))
            file_date = clean(file_row["file_date"])
            if time_value and file_date:
                return f"{file_date}T{time_value}+09:00", PLC_DEVICE_ID

        if kind == "temperature":
            timestamp = clean(row.get("datetime")) or clean(row.get("Datetime")) or clean(row.get("date_time"))
            if timestamp:
                return timestamp, TEMPERATURE_DEVICE_ID
            date_value = clean(row.get("date")) or clean(row.get("Date"))
            time_value = clean(row.get("time")) or clean(row.get("Time"))
            if date_value and time_value:
                return f"{date_value}T{time_value}+09:00", TEMPERATURE_DEVICE_ID
        return None, None


class EdgeUploader:
    def __init__(self, settings: Settings, options: UploadJobOptions) -> None:
        self.edge_url = settings.upload_edge_url
        self.anon_key = settings.supabase_anon_key
        self.options = options

    def upload_batch(self, batch: list[dict[str, Any]]) -> int:
        headers = build_upload_headers(self.anon_key)
        retry_attempts = self.options.retry_attempts
        with httpx.Client(timeout=self.options.http_timeout_seconds) as client:
            for attempt in range(retry_attempts + 1):
                try:
                    response = client.post(self.edge_url, json=batch, headers=headers)
                    if response.status_code >= 500:
                        raise httpx.HTTPStatusError(
                            f"Edge server error {response.status_code}",
                            request=response.request,
                            response=response,
                        )
                    if response.status_code >= 300:
                        raise RuntimeError(f"Edge rejected upload ({response.status_code}): {response.text[:200]}")
                    try:
                        payload = response.json()
                    except Exception:
                        payload = {}
                    return int(payload.get("inserted", 0))
                except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError):
                    if attempt >= retry_attempts:
                        raise
                    time.sleep(min(2**attempt, 8))
        return 0


class UploadJobService:
    def __init__(
        self,
        settings: Settings,
        repository: UploadJobRepository,
        reader: CsvUploadRecordReader | None = None,
        uploader: EdgeUploader | None = None,
    ) -> None:
        self.settings = settings
        self.repository = repository
        self.reader = reader or CsvUploadRecordReader()
        self._uploader = uploader

    def run_job(self, job_id: str) -> None:
        options = self._load_options(job_id)
        uploader = self._uploader or EdgeUploader(self.settings, options)
        if not self.settings.upload_edge_url or not self.settings.supabase_anon_key:
            self.repository.finish_job(
                job_id,
                UploadJobStatus.failed,
                error_code="upload_config_missing",
                error_message="Supabase Edge URL or anon key is not configured.",
            )
            return
        self.repository.start_job(job_id)
        try:
            files = self.repository.list_job_files(job_id)
            if not files:
                self.repository.finish_job(
                    job_id,
                    UploadJobStatus.failed,
                    error_code="no_upload_targets",
                    error_message="Upload job has no target files.",
                )
                return

            for file_row in files:
                self._control_checkpoint(job_id)
                self._upload_file(job_id, file_row["job_file_id"], options, uploader)

            self._control_checkpoint(job_id)
            current_files = self.repository.list_job_files(job_id)
            statuses = [str(row["status"]) for row in current_files]
            if any(status == "failed" for status in statuses):
                if all(status == "failed" for status in statuses):
                    self.repository.finish_job(job_id, UploadJobStatus.failed, "upload_failed", "Every target file failed.")
                else:
                    self.repository.finish_job(job_id, UploadJobStatus.partial_failed)
            elif any(status == "cancelled" for status in statuses):
                self.repository.finish_job(job_id, UploadJobStatus.cancelled)
            else:
                self.repository.finish_job(job_id, UploadJobStatus.succeeded)
        except UploadJobCancelled:
            self.repository.mark_remaining_cancelled(job_id)
            self.repository.finish_job(job_id, UploadJobStatus.cancelled)
        except Exception as error:
            self.repository.append_event(
                job_id,
                event_type="log.error",
                level="error",
                message=f"Upload job failed: {error}",
                data={"error": str(error)},
            )
            self.repository.finish_job(job_id, UploadJobStatus.failed, "upload_job_failed", str(error))

    def _upload_file(self, job_id: str, job_file_id: int, options: UploadJobOptions, uploader: EdgeUploader) -> None:
        row = self.repository.get_job_file(job_file_id)
        if row is None or row["status"] not in {"queued", "running"}:
            return
        path = Path(row["path"])
        try:
            if not path.exists():
                self.repository.mark_file_failed(job_file_id, "file_missing", "File is missing after preview.", row["resume_offset"])
                return
            stat = path.stat()
            signature = build_file_signature(path, stat)
            if signature != row["file_signature"]:
                self.repository.mark_file_failed(
                    job_file_id,
                    "file_changed_since_preview",
                    "File changed since preview. Run Preview again before uploading.",
                    row["resume_offset"],
                )
                return
            self.repository.mark_file_running(job_file_id)
            refreshed = self.repository.get_job_file(job_file_id)
            if refreshed is None:
                return
            start_offset = int(refreshed["resume_offset"] or 0)
            total_rows = refreshed["row_count"]
            if total_rows is None:
                total_rows = self.reader.count_records(refreshed)
            counters = UploadCounters(processed_rows=start_offset)
            for chunk in self.reader.iter_records(refreshed, options.chunk_rows, start_offset=start_offset):
                self._control_checkpoint(job_id)
                for batch_start in range(0, len(chunk), options.batch_rows):
                    self._control_checkpoint(job_id)
                    batch = chunk[batch_start : batch_start + options.batch_rows]
                    inserted = uploader.upload_batch(batch)
                    counters.uploaded_rows += len(batch)
                    counters.inserted_rows += inserted
                    counters.processed_rows += len(batch)
                    self.repository.update_file_progress(
                        job_file_id,
                        processed_rows=counters.processed_rows,
                        uploaded_rows=counters.uploaded_rows,
                        inserted_rows=counters.inserted_rows,
                        row_count=total_rows,
                        resume_offset=counters.processed_rows,
                    )
            if counters.uploaded_rows == 0:
                self.repository.mark_file_failed(job_file_id, "no_valid_rows", "No valid upload rows were produced.", counters.processed_rows)
            else:
                self.repository.mark_file_completed(job_file_id, counters.uploaded_rows, counters.inserted_rows)
        except UploadJobCancelled:
            raise
        except Exception as error:
            latest = self.repository.get_job_file(job_file_id)
            resume_offset = int(latest["resume_offset"] if latest is not None else row["resume_offset"] or 0)
            self.repository.mark_file_failed(job_file_id, "upload_failed", str(error), resume_offset)

    def _control_checkpoint(self, job_id: str) -> None:
        while True:
            pause_requested, cancel_requested, status = self.repository.get_control_flags(job_id)
            if cancel_requested or status == UploadJobStatus.cancelling.value:
                raise UploadJobCancelled("Upload job was cancelled.")
            if pause_requested or status == UploadJobStatus.pausing.value:
                self.repository.mark_paused(job_id)
                time.sleep(0.2)
                continue
            return

    def _load_options(self, job_id: str) -> UploadJobOptions:
        row = self.repository.get_job(job_id)
        if row is None:
            return UploadJobOptions()
        return UploadJobOptions.model_validate(decode_json(row["options_json"], {}))


def normalize_column_name(value: str) -> str:
    normalized = "".join(ch if ch.isalnum() else "_" for ch in value.strip().lower())
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized.strip("_") or "value"


def coerce_value(value: str) -> str | int | float:
    try:
        if "." not in value:
            return int(value)
        return float(value)
    except ValueError:
        return value
