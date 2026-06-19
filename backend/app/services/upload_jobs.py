import hashlib
import json
import time
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from backend.app.core.settings import Settings
from backend.app.core.target_class import classify_database_url
from backend.app.core.transform_core import count_canonical_records, iter_canonical_record_chunks
from backend.app.db.db_delta_repository import DbDeltaEvidenceRepository
from backend.app.db.row_attribution_repository import RowAttributionRepository
from backend.app.db.row_attribution_repository import build_exact_key_hash
from backend.app.db.row_attribution_repository import build_safe_hash as build_hmac_safe_hash
from backend.app.db.row_attribution_repository import build_source_evidence_hash
from backend.app.db.upload_job_repository import UploadJobRepository, decode_json
from backend.app.schemas.upload_jobs import UploadJobOptions, UploadJobStatus
from backend.app.services.upload_preview import build_file_signature, is_file_locked


class UploadJobCancelled(RuntimeError):
    pass


class UploadEvidenceBlockedError(RuntimeError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass
class UploadCounters:
    processed_rows: int = 0
    uploaded_rows: int = 0
    inserted_rows: int = 0


@dataclass(frozen=True)
class DeduplicatedUploadBatch:
    records: list[dict[str, Any]]
    duplicate_rows: int


@dataclass(frozen=True)
class UploadDbEvidenceContext:
    target_class: str
    fingerprint_hash: str


def _upload_record_key(record: dict[str, Any]) -> tuple[str, str] | None:
    timestamp = record.get("timestamp")
    device_id = record.get("device_id")
    if timestamp is None or device_id is None:
        return None
    return str(timestamp), str(device_id)


def deduplicate_upload_records(records: list[dict[str, Any]]) -> DeduplicatedUploadBatch:
    keyed_records: dict[tuple[str, str], dict[str, Any]] = {}
    key_order: list[tuple[str, str]] = []
    passthrough_records: list[dict[str, Any]] = []

    for record in records:
        key = _upload_record_key(record)
        if key is None:
            passthrough_records.append(record)
            continue
        if key not in keyed_records:
            key_order.append(key)
        keyed_records[key] = record

    deduplicated_records = [keyed_records[key] for key in key_order]
    return DeduplicatedUploadBatch(
        records=[*passthrough_records, *deduplicated_records],
        duplicate_rows=len(records) - len(passthrough_records) - len(key_order),
    )


def build_upload_headers(anon_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {anon_key}",
        "apikey": anon_key,
        "Content-Type": "application/json",
    }


class CsvUploadRecordReader:
    def iter_records(self, file_row: Any, chunk_rows: int, start_offset: int = 0) -> Iterable[list[dict[str, Any]]]:
        yield from iter_canonical_record_chunks(file_row, chunk_rows=chunk_rows, start_offset=start_offset)

    def count_records(self, file_row: Any) -> int:
        return count_canonical_records(file_row)


def parse_edge_accepted_rows(payload: dict[str, Any]) -> int:
    for key in ("accepted", "upserted", "inserted"):
        value = payload.get(key)
        if value is None:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return 0


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
                    return parse_edge_accepted_rows(payload)
                except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError):
                    if attempt >= retry_attempts:
                        raise
                    time.sleep(min(2**attempt, 8))
        return 0


class UploadDbEvidenceClient:
    def prepare(self) -> UploadDbEvidenceContext:
        raise NotImplementedError

    def count_existing_keys(self, keys: set[tuple[str, str]]) -> int:
        raise NotImplementedError


class PsycopgUploadDbEvidenceClient(UploadDbEvidenceClient):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def prepare(self) -> UploadDbEvidenceContext:
        if not self.settings.supabase_db_url:
            raise UploadEvidenceBlockedError("supabase_db_url_missing")
        classified = classify_database_url(
            self.settings.supabase_db_url,
            expected_db_port=self.settings.local_supabase_db_port,
            source="supabase_db_url",
        )
        if classified.target_class != "loopback_expected_db_port":
            raise UploadEvidenceBlockedError("db_target_guard_failed")
        try:
            import psycopg

            with psycopg.connect(self.settings.supabase_db_url, connect_timeout=5) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT to_regclass('public.all_metrics') IS NOT NULL")
                    if not bool(cursor.fetchone()[0]):
                        raise UploadEvidenceBlockedError("all_metrics_missing")
                    cursor.execute(
                        """
                        SELECT 1
                        FROM pg_indexes
                        WHERE schemaname = 'public'
                          AND tablename = 'all_metrics'
                          AND indexdef ILIKE '%timestamp%'
                          AND indexdef ILIKE '%device_id%'
                          AND indexdef ILIKE 'CREATE UNIQUE INDEX%'
                        LIMIT 1
                        """
                    )
                    if cursor.fetchone() is None:
                        raise UploadEvidenceBlockedError("all_metrics_unique_key_missing")
                    cursor.execute("SELECT current_database()")
                    database_name = str(cursor.fetchone()[0])
        except UploadEvidenceBlockedError:
            raise
        except Exception as error:
            raise UploadEvidenceBlockedError("db_delta_preflight_failed") from error
        fingerprint_hash = safe_hash(
            {
                "targetClass": classified.target_class,
                "databaseName": database_name,
                "schemaSignature": "public.all_metrics.timestamp_device_id_unique",
            }
        )
        return UploadDbEvidenceContext(target_class=classified.target_class, fingerprint_hash=fingerprint_hash)

    def count_existing_keys(self, keys: set[tuple[str, str]]) -> int:
        if not keys:
            return 0
        try:
            import psycopg

            with psycopg.connect(self.settings.supabase_db_url, connect_timeout=5) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        CREATE TEMP TABLE temp_upload_evidence_keys (
                          timestamp_text TEXT NOT NULL,
                          device_id TEXT NOT NULL
                        ) ON COMMIT DROP
                        """
                    )
                    cursor.executemany(
                        "INSERT INTO temp_upload_evidence_keys(timestamp_text, device_id) VALUES (%s, %s)",
                        sorted(keys),
                    )
                    cursor.execute(
                        """
                        SELECT COUNT(*)
                        FROM temp_upload_evidence_keys k
                        JOIN public.all_metrics m
                          ON m.timestamp = k.timestamp_text::timestamptz
                         AND m.device_id = k.device_id
                        """
                    )
                    return int(cursor.fetchone()[0])
        except Exception as error:
            raise UploadEvidenceBlockedError("db_delta_count_failed") from error


class UploadJobService:
    def __init__(
        self,
        settings: Settings,
        repository: UploadJobRepository,
        reader: CsvUploadRecordReader | None = None,
        uploader: EdgeUploader | None = None,
        db_delta_repository: DbDeltaEvidenceRepository | None = None,
        row_attribution_repository: RowAttributionRepository | None = None,
        evidence_db_client: UploadDbEvidenceClient | None = None,
    ) -> None:
        self.settings = settings
        self.repository = repository
        self.reader = reader or CsvUploadRecordReader()
        self._uploader = uploader
        self.db_delta_repository = db_delta_repository or DbDeltaEvidenceRepository(repository.db_path)
        self.row_attribution_repository = row_attribution_repository or RowAttributionRepository(
            repository.db_path,
            writes_enabled=settings.effective_row_attribution_writes_enabled,
        )
        self.evidence_db_client = evidence_db_client or PsycopgUploadDbEvidenceClient(settings)

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
        evidence_context = self._prepare_upload_evidence(job_id)
        if evidence_context is False:
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
                self._upload_file(job_id, file_row["job_file_id"], options, uploader, evidence_context)

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

    def _upload_file(
        self,
        job_id: str,
        job_file_id: int,
        options: UploadJobOptions,
        uploader: EdgeUploader,
        evidence_context: UploadDbEvidenceContext | None,
    ) -> None:
        row = self.repository.get_job_file(job_file_id)
        if row is None or row["status"] not in {"queued", "running"}:
            return
        path = Path(row["path"])
        try:
            if not path.exists():
                self.repository.mark_file_failed(job_file_id, "file_missing", "File is missing after preview.", row["resume_offset"])
                return
            path_error = validate_upload_path(path, Path(row["folder_path"]))
            if path_error is not None:
                code, message = path_error
                self.repository.mark_file_failed(job_file_id, code, message, row["resume_offset"])
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
                    source_batch = chunk[batch_start : batch_start + options.batch_rows]
                    deduplicated_batch = deduplicate_upload_records(source_batch)
                    if deduplicated_batch.duplicate_rows > 0:
                        self.repository.append_event(
                            job_id,
                            event_type="file.deduplicated",
                            level="warning",
                            message="Duplicate upload keys were collapsed before Edge upload.",
                            job_file_id=job_file_id,
                            data={
                                "inputRows": len(source_batch),
                                "outputRows": len(deduplicated_batch.records),
                                "duplicateRows": deduplicated_batch.duplicate_rows,
                                "processedRows": counters.processed_rows + len(source_batch),
                            },
                        )
                    if not deduplicated_batch.records:
                        counters.processed_rows += len(source_batch)
                        self.repository.update_file_progress(
                            job_file_id,
                            processed_rows=counters.processed_rows,
                            uploaded_rows=counters.uploaded_rows,
                            inserted_rows=counters.inserted_rows,
                            row_count=total_rows,
                            resume_offset=counters.processed_rows,
                        )
                        continue
                    evidence_keys = self._evidence_keys(deduplicated_batch.records) if evidence_context else set()
                    before_count = (
                        self.evidence_db_client.count_existing_keys(evidence_keys)
                        if evidence_context and evidence_keys
                        else None
                    )
                    accepted = uploader.upload_batch(deduplicated_batch.records)
                    if evidence_context and evidence_keys and before_count is not None:
                        after_count = self.evidence_db_client.count_existing_keys(evidence_keys)
                        self._record_upload_batch_evidence(
                            job_id=job_id,
                            job_file_id=job_file_id,
                            context=evidence_context,
                            keys=evidence_keys,
                            before_count=before_count,
                            after_count=after_count,
                            accepted_rows=accepted,
                        )
                    counters.uploaded_rows += len(deduplicated_batch.records)
                    counters.inserted_rows += accepted
                    counters.processed_rows += len(source_batch)
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
                self.repository.mark_file_completed(
                    job_file_id,
                    counters.uploaded_rows,
                    counters.inserted_rows,
                    processed_rows=counters.processed_rows,
                )
        except UploadJobCancelled:
            raise
        except Exception as error:
            latest = self.repository.get_job_file(job_file_id)
            resume_offset = int(latest["resume_offset"] if latest is not None else row["resume_offset"] or 0)
            self.repository.mark_file_failed(job_file_id, "upload_failed", str(error), resume_offset)

    def _prepare_upload_evidence(self, job_id: str) -> UploadDbEvidenceContext | None | bool:
        if not self._v2_evidence_enabled():
            return None
        if not self.settings.row_attribution_hmac_key:
            self.repository.finish_job(
                job_id,
                UploadJobStatus.failed,
                error_code="row_attribution_hmac_key_missing",
                error_message="V2 upload evidence requires row attribution HMAC configuration.",
            )
            return False
        try:
            return self.evidence_db_client.prepare()
        except UploadEvidenceBlockedError as error:
            self.repository.finish_job(
                job_id,
                UploadJobStatus.failed,
                error_code=error.reason,
                error_message="V2 upload evidence preflight failed.",
            )
            return False

    def _record_upload_batch_evidence(
        self,
        *,
        job_id: str,
        job_file_id: int,
        context: UploadDbEvidenceContext,
        keys: set[tuple[str, str]],
        before_count: int,
        after_count: int,
        accepted_rows: int,
    ) -> None:
        operation_type = self._upload_operation_type(job_id)
        audit_action = "upload.retry" if operation_type == "upload_retry" else "upload.start"
        audit_id = self.repository.latest_audit_id(job_id, audit_action)
        if audit_id is None:
            raise RuntimeError("upload_start_audit_missing")
        actual_delta = after_count - before_count
        expected_delta = len(keys) - before_count if accepted_rows == len(keys) else None
        reason_code: str | None = None
        if expected_delta is None:
            result = "not_measured"
            reason_code = "upload_acceptance_count_mismatch"
        elif actual_delta == expected_delta:
            result = "matched"
        else:
            result = "mismatched"
            reason_code = "upload_db_delta_mismatch"
        delta = self.db_delta_repository.append_delta(
            operation_id=job_id,
            operation_type=operation_type,
            audit_id=audit_id,
            actor_id="local_operator",
            actor_role="operator",
            delta_scope={
                "operationId": job_id,
                "jobFileId": int(job_file_id),
                "batchKeyCount": len(keys),
                "acceptedRows": accepted_rows,
                "reasonCode": reason_code,
            },
            delta_query_class="exact_key_count",
            before_count=before_count,
            after_count=after_count,
            expected_delta=expected_delta,
            actual_delta=actual_delta,
            result=result,
            reason_code=reason_code,
            db_target_class=context.target_class,
            db_fingerprint_hash=context.fingerprint_hash,
        )
        outcome = "upsert_accepted" if result == "matched" else "unknown_requires_reconcile"
        source_evidence_hash = build_source_evidence_hash(
            {
                "operationId": job_id,
                "operationType": operation_type,
                "operationPhase": "after_mutation",
                "dbDeltaId": delta.delta_id,
                "batchKeyCount": len(keys),
                "acceptedRows": accepted_rows,
                "outcome": outcome,
                "reasonCode": reason_code,
            },
            self.settings.row_attribution_hmac_key,
        )
        schema_fingerprint_hash = build_hmac_safe_hash(
            "public.all_metrics.timestamp_device_id_unique",
            self.settings.row_attribution_hmac_key,
        )
        for timestamp, device_id in sorted(keys):
            attribution = self.row_attribution_repository.append_attribution(
                operation_id=job_id,
                operation_type=operation_type,
                operation_phase="after_mutation",
                audit_id=audit_id,
                actor_id="local_operator",
                actor_role="operator",
                exact_key_hash=build_exact_key_hash(timestamp, device_id, self.settings.row_attribution_hmac_key),
                source_evidence_hash=source_evidence_hash,
                outcome=outcome,
                db_target_class=context.target_class,
                db_fingerprint_hash=context.fingerprint_hash,
                schema_fingerprint_hash=schema_fingerprint_hash,
                db_delta_id=delta.delta_id,
                reason_code=reason_code,
            )
            if not attribution.created:
                raise RuntimeError(attribution.rejection_reason or "row_attribution_write_rejected")
        if result != "matched":
            self.repository.append_event(
                job_id,
                event_type="upload.evidence_mismatch",
                level="warning",
                message="Upload DB delta evidence requires reconcile review.",
                job_file_id=job_file_id,
                data={
                    "dbDeltaId": delta.delta_id,
                    "reasonCode": reason_code,
                    "batchKeyCount": len(keys),
                    "acceptedRows": accepted_rows,
                },
            )

    def _upload_operation_type(self, job_id: str) -> str:
        row = self.repository.get_job(job_id)
        if row is not None and row["retry_of_job_id"]:
            return "upload_retry"
        return "upload_start"

    def _evidence_keys(self, records: list[dict[str, Any]]) -> set[tuple[str, str]]:
        return {key for record in records if (key := _upload_record_key(record)) is not None}

    def _v2_evidence_enabled(self) -> bool:
        return self.settings.effective_row_attribution_writes_enabled

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


def validate_upload_path(path: Path, folder_path: Path) -> tuple[str, str] | None:
    if path.suffix.lower() != ".csv":
        return "unsupported_extension", "Upload target is not a CSV file."
    if not path.is_file():
        return "file_not_regular", "Upload target is not a regular file."
    try:
        resolved_path = path.resolve()
        resolved_folder = folder_path.resolve()
        resolved_path.relative_to(resolved_folder)
    except ValueError:
        return "file_outside_source", "Upload target is outside the preview source folder."
    except OSError as error:
        return "file_path_error", f"Could not validate upload target path: {error}"
    if is_file_locked(path):
        return "file_locked", "Upload target is locked by another process."
    return None


def safe_hash(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
