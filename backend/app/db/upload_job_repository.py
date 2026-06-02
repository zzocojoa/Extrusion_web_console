import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from backend.app.db.preview_repository import iso_now
from backend.app.schemas.upload_jobs import UploadJobFileStatus, UploadJobMode, UploadJobStatus


ACTIVE_JOB_STATUSES = ("queued", "running", "pausing", "paused", "cancelling")
TERMINAL_JOB_STATUSES = ("succeeded", "partial_failed", "failed", "cancelled", "interrupted")


@dataclass(frozen=True)
class CreateJobFromPreviewResult:
    created: bool
    active_job_id: str | None = None
    rejection_reason: str | None = None
    rejection_status: str | None = None
    db_status: str | None = None
    file_count: int = 0


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _loads(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


class UploadJobRepository:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        self.bootstrap()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.db_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=5000")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def bootstrap(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS upload_jobs (
                  job_id TEXT PRIMARY KEY,
                  preview_run_id TEXT REFERENCES preview_runs(preview_run_id),
                  retry_of_job_id TEXT REFERENCES upload_jobs(job_id),
                  mode TEXT NOT NULL CHECK(mode IN ('preview_targets','retry_failed')),
                  status TEXT NOT NULL CHECK(status IN (
                    'queued','running','succeeded','partial_failed','failed',
                    'pausing','paused','cancelling','cancelled','interrupted'
                  )),
                  requested_at TEXT NOT NULL,
                  started_at TEXT,
                  finished_at TEXT,
                  actor TEXT NOT NULL DEFAULT 'local_operator',
                  options_json TEXT NOT NULL,
                  config_snapshot_json TEXT NOT NULL,
                  pause_requested INTEGER NOT NULL DEFAULT 0,
                  cancel_requested INTEGER NOT NULL DEFAULT 0,
                  total_files INTEGER NOT NULL DEFAULT 0,
                  succeeded_files INTEGER NOT NULL DEFAULT 0,
                  failed_files INTEGER NOT NULL DEFAULT 0,
                  cancelled_files INTEGER NOT NULL DEFAULT 0,
                  total_rows INTEGER NOT NULL DEFAULT 0,
                  processed_rows INTEGER NOT NULL DEFAULT 0,
                  uploaded_rows INTEGER NOT NULL DEFAULT 0,
                  inserted_rows INTEGER NOT NULL DEFAULT 0,
                  warning_count INTEGER NOT NULL DEFAULT 0,
                  error_code TEXT,
                  error_message TEXT,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS upload_job_files (
                  job_file_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  job_id TEXT NOT NULL REFERENCES upload_jobs(job_id) ON DELETE CASCADE,
                  preview_item_id INTEGER REFERENCES preview_items(preview_item_id),
                  file_key TEXT NOT NULL,
                  folder_label TEXT NOT NULL,
                  folder_path TEXT NOT NULL,
                  filename TEXT NOT NULL,
                  path TEXT NOT NULL,
                  kind TEXT NOT NULL,
                  file_date TEXT,
                  file_signature TEXT NOT NULL,
                  source_preview_status TEXT,
                  source_reason_code TEXT,
                  status TEXT NOT NULL CHECK(status IN (
                    'queued','running','succeeded','failed','skipped','cancelled','interrupted'
                  )),
                  row_count INTEGER,
                  processed_rows INTEGER NOT NULL DEFAULT 0,
                  uploaded_rows INTEGER NOT NULL DEFAULT 0,
                  inserted_rows INTEGER NOT NULL DEFAULT 0,
                  resume_offset INTEGER NOT NULL DEFAULT 0,
                  retry_count INTEGER NOT NULL DEFAULT 0,
                  started_at TEXT,
                  finished_at TEXT,
                  last_error_code TEXT,
                  last_error_message TEXT,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL,
                  UNIQUE(job_id, file_key)
                );

                CREATE TABLE IF NOT EXISTS upload_file_state (
                  file_key TEXT PRIMARY KEY,
                  legacy_key TEXT NOT NULL,
                  folder_label TEXT NOT NULL,
                  folder_path TEXT NOT NULL,
                  filename TEXT NOT NULL,
                  path TEXT NOT NULL,
                  kind TEXT NOT NULL,
                  file_signature TEXT NOT NULL,
                  state TEXT NOT NULL CHECK(state IN (
                    'new','in_progress','completed','failed','cancelled','interrupted'
                  )),
                  resume_offset INTEGER NOT NULL DEFAULT 0,
                  last_error_code TEXT,
                  last_error_message TEXT,
                  retry_count INTEGER NOT NULL DEFAULT 0,
                  completed_at TEXT,
                  failed_at TEXT,
                  last_job_id TEXT REFERENCES upload_jobs(job_id),
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS job_events (
                  event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  job_id TEXT NOT NULL REFERENCES upload_jobs(job_id) ON DELETE CASCADE,
                  seq INTEGER NOT NULL,
                  ts TEXT NOT NULL,
                  level TEXT NOT NULL CHECK(level IN ('debug','info','warning','error')),
                  event_type TEXT NOT NULL,
                  message TEXT NOT NULL,
                  job_file_id INTEGER REFERENCES upload_job_files(job_file_id),
                  data_json TEXT NOT NULL DEFAULT '{}',
                  created_at TEXT NOT NULL,
                  UNIQUE(job_id, seq)
                );

                CREATE TABLE IF NOT EXISTS audit_log (
                  audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  ts TEXT NOT NULL,
                  actor TEXT NOT NULL DEFAULT 'local_operator',
                  action TEXT NOT NULL,
                  target_type TEXT NOT NULL,
                  target_id TEXT,
                  params_json_redacted TEXT NOT NULL DEFAULT '{}',
                  result TEXT NOT NULL CHECK(result IN ('success','failure','cancelled','blocked')),
                  error_code TEXT,
                  error_message TEXT,
                  job_id TEXT,
                  request_id TEXT,
                  created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_upload_jobs_status_created
                  ON upload_jobs(status, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_upload_job_files_job_status
                  ON upload_job_files(job_id, status);
                CREATE INDEX IF NOT EXISTS idx_upload_file_state_state
                  ON upload_file_state(state, updated_at DESC);
                CREATE INDEX IF NOT EXISTS idx_job_events_job_seq
                  ON job_events(job_id, seq);
                CREATE INDEX IF NOT EXISTS idx_audit_log_job_id
                  ON audit_log(job_id, created_at DESC);
                """
            )

    def initialize(self) -> None:
        self.bootstrap()

    def ensure_schema(self) -> None:
        self.bootstrap()

    def get_preview_run(self, preview_run_id: str) -> sqlite3.Row | None:
        with self.connect() as connection:
            return connection.execute(
                "SELECT * FROM preview_runs WHERE preview_run_id = ?",
                (preview_run_id,),
            ).fetchone()

    def count_preview_targets(self, preview_run_id: str) -> int:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM preview_items
                WHERE preview_run_id = ? AND status = 'target'
                """,
                (preview_run_id,),
            ).fetchone()
        return int(row["count"] if row else 0)

    def get_active_job_id(self) -> str | None:
        with self.connect() as connection:
            row = connection.execute(
                f"""
                SELECT job_id
                FROM upload_jobs
                WHERE status IN ({",".join("?" for _ in ACTIVE_JOB_STATUSES)})
                ORDER BY created_at DESC
                LIMIT 1
                """,
                ACTIVE_JOB_STATUSES,
            ).fetchone()
        return None if row is None else str(row["job_id"])

    def create_job_from_preview(
        self,
        *,
        job_id: str,
        preview_run_id: str,
        options: dict[str, Any],
        config_snapshot: dict[str, Any],
    ) -> CreateJobFromPreviewResult:
        now = iso_now()
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            active = connection.execute(
                f"""
                SELECT job_id
                FROM upload_jobs
                WHERE status IN ({",".join("?" for _ in ACTIVE_JOB_STATUSES)})
                ORDER BY created_at DESC
                LIMIT 1
                """,
                ACTIVE_JOB_STATUSES,
            ).fetchone()
            if active is not None:
                return CreateJobFromPreviewResult(created=False, active_job_id=str(active["job_id"]))
            preview = connection.execute(
                "SELECT * FROM preview_runs WHERE preview_run_id = ?",
                (preview_run_id,),
            ).fetchone()
            if preview is None:
                return CreateJobFromPreviewResult(created=False, rejection_reason="preview_missing")
            if preview["status"] != "succeeded":
                return CreateJobFromPreviewResult(
                    created=False,
                    rejection_reason="preview_not_uploadable",
                    rejection_status=str(preview["status"]),
                )
            if preview["db_status"] != "reachable":
                return CreateJobFromPreviewResult(
                    created=False,
                    rejection_reason="preview_db_not_reachable",
                    db_status=str(preview["db_status"]),
                )
            target_count_row = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM preview_items
                WHERE preview_run_id = ? AND status = 'target'
                """,
                (preview_run_id,),
            ).fetchone()
            target_count = int(target_count_row["count"] if target_count_row else 0)
            if target_count <= 0:
                return CreateJobFromPreviewResult(created=False, rejection_reason="no_upload_targets")

            connection.execute(
                """
                INSERT INTO upload_jobs(
                  job_id, preview_run_id, mode, status, requested_at,
                  options_json, config_snapshot_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    preview_run_id,
                    UploadJobMode.preview_targets.value,
                    UploadJobStatus.queued.value,
                    now,
                    _json(options),
                    _json(config_snapshot),
                    now,
                    now,
                ),
            )
            connection.execute(
                """
                INSERT INTO upload_job_files(
                  job_id, preview_item_id, file_key, folder_label, folder_path, filename,
                  path, kind, file_date, file_signature, source_preview_status,
                  source_reason_code, status, row_count, created_at, updated_at
                )
                SELECT ?, preview_item_id, file_key, folder_label, folder_path, filename,
                       path, kind, file_date, file_signature, status, reason_code,
                       'queued', row_count, ?, ?
                FROM preview_items
                WHERE preview_run_id = ? AND status = 'target'
                ORDER BY filename ASC
                """,
                (job_id, now, now, preview_run_id),
            )
            self._recompute_job_summary(connection, job_id)
            self._append_event_in_connection(
                connection,
                job_id,
                event_type="job.created",
                level="info",
                message="Upload job was queued from preview targets.",
                data={"previewRunId": preview_run_id},
            )
            self._append_audit_in_connection(
                connection,
                action="upload.start",
                target_type="upload_job",
                target_id=job_id,
                params={"previewRunId": preview_run_id, "mode": UploadJobMode.preview_targets.value},
                result="success",
                job_id=job_id,
            )
        return CreateJobFromPreviewResult(created=True, file_count=target_count)

    def create_retry_job(
        self,
        *,
        job_id: str,
        source_job_id: str,
        include_interrupted: bool,
        include_cancelled: bool,
        options: dict[str, Any],
        config_snapshot: dict[str, Any],
    ) -> tuple[str | None, int]:
        now = iso_now()
        allowed = ["failed"]
        if include_interrupted:
            allowed.append("interrupted")
        if include_cancelled:
            allowed.append("cancelled")
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            active = connection.execute(
                f"""
                SELECT job_id
                FROM upload_jobs
                WHERE status IN ({",".join("?" for _ in ACTIVE_JOB_STATUSES)})
                ORDER BY created_at DESC
                LIMIT 1
                """,
                ACTIVE_JOB_STATUSES,
            ).fetchone()
            if active is not None:
                return str(active["job_id"]), 0
            source = connection.execute(
                "SELECT * FROM upload_jobs WHERE job_id = ?",
                (source_job_id,),
            ).fetchone()
            if source is None or source["status"] not in TERMINAL_JOB_STATUSES:
                return None, -1
            placeholders = ",".join("?" for _ in allowed)
            source_files = connection.execute(
                f"""
                SELECT *
                FROM upload_job_files
                WHERE job_id = ? AND status IN ({placeholders})
                ORDER BY filename ASC
                """,
                [source_job_id, *allowed],
            ).fetchall()
            if not source_files:
                return None, 0
            connection.execute(
                """
                INSERT INTO upload_jobs(
                  job_id, preview_run_id, retry_of_job_id, mode, status, requested_at,
                  options_json, config_snapshot_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    source["preview_run_id"],
                    source_job_id,
                    UploadJobMode.retry_failed.value,
                    UploadJobStatus.queued.value,
                    now,
                    _json(options),
                    _json(config_snapshot),
                    now,
                    now,
                ),
            )
            for row in source_files:
                connection.execute(
                    """
                    INSERT INTO upload_job_files(
                      job_id, preview_item_id, file_key, folder_label, folder_path, filename,
                      path, kind, file_date, file_signature, source_preview_status,
                      source_reason_code, status, row_count, resume_offset, retry_count,
                      created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'queued', ?, ?, ?, ?, ?)
                    """,
                    (
                        job_id,
                        row["preview_item_id"],
                        row["file_key"],
                        row["folder_label"],
                        row["folder_path"],
                        row["filename"],
                        row["path"],
                        row["kind"],
                        row["file_date"],
                        row["file_signature"],
                        row["source_preview_status"],
                        row["source_reason_code"],
                        row["row_count"],
                        row["resume_offset"],
                        int(row["retry_count"] or 0) + 1,
                        now,
                        now,
                    ),
                )
            self._recompute_job_summary(connection, job_id)
            self._append_event_in_connection(
                connection,
                job_id,
                event_type="job.created",
                level="info",
                message="Retry job was queued from failed files.",
                data={"retryOfJobId": source_job_id},
            )
            self._append_audit_in_connection(
                connection,
                action="upload.retry",
                target_type="upload_job",
                target_id=job_id,
                params={"retryOfJobId": source_job_id, "includeInterrupted": include_interrupted},
                result="success",
                job_id=job_id,
            )
        return None, len(source_files)

    def start_job(self, job_id: str) -> None:
        now = iso_now()
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            updated = connection.execute(
                """
                UPDATE upload_jobs
                SET status = 'running', started_at = COALESCE(started_at, ?), updated_at = ?
                WHERE job_id = ? AND status IN ('queued', 'paused')
                """,
                (now, now, job_id),
            )
            if updated.rowcount <= 0:
                return
            self._append_event_in_connection(
                connection, job_id, event_type="job.started", level="info", message="Upload job started."
            )

    def finish_job(self, job_id: str, status: UploadJobStatus, error_code: str | None = None, error_message: str | None = None) -> bool:
        now = iso_now()
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            current = connection.execute(
                "SELECT status, cancel_requested FROM upload_jobs WHERE job_id = ?",
                (job_id,),
            ).fetchone()
            if current is None or current["status"] in TERMINAL_JOB_STATUSES:
                return False
            final_status = status
            if (current["cancel_requested"] or current["status"] == UploadJobStatus.cancelling.value) and status == UploadJobStatus.succeeded:
                final_status = UploadJobStatus.cancelled
                error_code = "cancelled"
                error_message = "Upload job was cancelled before finalization."
            result = (
                "success"
                if final_status == UploadJobStatus.succeeded
                else "cancelled"
                if final_status == UploadJobStatus.cancelled
                else "failure"
            )
            self._recompute_job_summary(connection, job_id)
            updated = connection.execute(
                """
                UPDATE upload_jobs
                SET status = ?, finished_at = COALESCE(finished_at, ?),
                    error_code = ?, error_message = ?, updated_at = ?
                WHERE job_id = ? AND status NOT IN ('succeeded','partial_failed','failed','cancelled','interrupted')
                """,
                (final_status.value, now, error_code, error_message, now, job_id),
            )
            if updated.rowcount <= 0:
                return False
            event_type = f"job.{final_status.value}"
            level = (
                "info"
                if final_status == UploadJobStatus.succeeded
                else "warning"
                if final_status in {UploadJobStatus.partial_failed, UploadJobStatus.cancelled}
                else "error"
            )
            self._append_event_in_connection(
                connection,
                job_id,
                event_type=event_type,
                level=level,
                message=f"Upload job finished with status {final_status.value}.",
                data={"errorCode": error_code, "errorMessage": error_message},
            )
            self._append_audit_in_connection(
                connection,
                action=f"upload.{final_status.value}",
                target_type="upload_job",
                target_id=job_id,
                params={},
                result=result,
                error_code=error_code,
                error_message=error_message,
                job_id=job_id,
            )
        return True

    def request_pause(self, job_id: str) -> UploadJobStatus | None:
        with self.connect() as connection:
            row = connection.execute("SELECT status FROM upload_jobs WHERE job_id = ?", (job_id,)).fetchone()
        if row is not None and row["status"] == UploadJobStatus.paused.value:
            return UploadJobStatus.paused
        return self._set_control_flag(job_id, "pause_requested", UploadJobStatus.pausing, ("queued", "running"), "upload.pause")

    def resume_job(self, job_id: str) -> UploadJobStatus | None:
        now = iso_now()
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT status FROM upload_jobs WHERE job_id = ?", (job_id,)).fetchone()
            if row is None:
                return None
            if row["status"] != UploadJobStatus.paused.value:
                return UploadJobStatus(str(row["status"]))
            connection.execute(
                """
                UPDATE upload_jobs
                SET pause_requested = 0, status = 'running', updated_at = ?
                WHERE job_id = ?
                """,
                (now, job_id),
            )
            self._append_event_in_connection(
                connection, job_id, event_type="job.resumed", level="info", message="Upload job resumed."
            )
            self._append_audit_in_connection(
                connection,
                action="upload.resume",
                target_type="upload_job",
                target_id=job_id,
                params={},
                result="success",
                job_id=job_id,
            )
            return UploadJobStatus.running

    def request_cancel(self, job_id: str) -> UploadJobStatus | None:
        return self._set_control_flag(
            job_id,
            "cancel_requested",
            UploadJobStatus.cancelling,
            ("queued", "running", "pausing", "paused"),
            "upload.cancel",
        )

    def _set_control_flag(
        self,
        job_id: str,
        flag_column: str,
        next_status: UploadJobStatus,
        allowed_statuses: tuple[str, ...],
        audit_action: str,
    ) -> UploadJobStatus | None:
        now = iso_now()
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT status FROM upload_jobs WHERE job_id = ?", (job_id,)).fetchone()
            if row is None:
                return None
            if row["status"] not in allowed_statuses:
                return UploadJobStatus(str(row["status"]))
            connection.execute(
                f"UPDATE upload_jobs SET {flag_column} = 1, status = ?, updated_at = ? WHERE job_id = ?",
                (next_status.value, now, job_id),
            )
            self._append_event_in_connection(
                connection,
                job_id,
                event_type=f"job.{next_status.value}",
                level="warning",
                message=f"Upload job {next_status.value}.",
            )
            self._append_audit_in_connection(
                connection,
                action=audit_action,
                target_type="upload_job",
                target_id=job_id,
                params={},
                result="success",
                job_id=job_id,
            )
            return next_status

    def mark_paused(self, job_id: str) -> None:
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT status FROM upload_jobs WHERE job_id = ?", (job_id,)).fetchone()
            if row is None or row["status"] == UploadJobStatus.paused.value:
                return
            if row["status"] != UploadJobStatus.pausing.value:
                return
            connection.execute(
                "UPDATE upload_jobs SET status = 'paused', updated_at = ? WHERE job_id = ?",
                (iso_now(), job_id),
            )
            self._append_event_in_connection(
                connection, job_id, event_type="job.paused", level="warning", message="Upload job paused."
            )

    def get_control_flags(self, job_id: str) -> tuple[bool, bool, str | None]:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT pause_requested, cancel_requested, status FROM upload_jobs WHERE job_id = ?",
                (job_id,),
            ).fetchone()
        if row is None:
            return False, False, None
        return bool(row["pause_requested"]), bool(row["cancel_requested"]), str(row["status"])

    def list_job_files(self, job_id: str) -> list[sqlite3.Row]:
        with self.connect() as connection:
            return connection.execute(
                """
                SELECT *
                FROM upload_job_files
                WHERE job_id = ?
                ORDER BY
                  CASE status
                    WHEN 'failed' THEN 0
                    WHEN 'interrupted' THEN 1
                    WHEN 'running' THEN 2
                    WHEN 'queued' THEN 3
                    ELSE 4
                  END,
                  filename ASC
                """,
                (job_id,),
            ).fetchall()

    def get_job_file(self, job_file_id: int) -> sqlite3.Row | None:
        with self.connect() as connection:
            return connection.execute(
                "SELECT * FROM upload_job_files WHERE job_file_id = ?",
                (job_file_id,),
            ).fetchone()

    def mark_file_running(self, job_file_id: int) -> None:
        now = iso_now()
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM upload_job_files WHERE job_file_id = ?",
                (job_file_id,),
            ).fetchone()
            if row is None:
                return
            connection.execute(
                """
                UPDATE upload_job_files
                SET status = 'running', started_at = COALESCE(started_at, ?), updated_at = ?
                WHERE job_file_id = ?
                """,
                (now, now, job_file_id),
            )
            self._upsert_file_state_in_connection(connection, row, "in_progress", None, None, None)
            self._append_event_in_connection(
                connection,
                row["job_id"],
                event_type="file.started",
                level="info",
                message=f"Started {row['filename']}.",
                job_file_id=job_file_id,
            )

    def update_file_progress(
        self,
        job_file_id: int,
        *,
        processed_rows: int,
        uploaded_rows: int,
        inserted_rows: int,
        row_count: int | None,
        resume_offset: int,
    ) -> None:
        now = iso_now()
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM upload_job_files WHERE job_file_id = ?",
                (job_file_id,),
            ).fetchone()
            if row is None:
                return
            connection.execute(
                """
                UPDATE upload_job_files
                SET processed_rows = ?, uploaded_rows = ?, inserted_rows = ?,
                    row_count = COALESCE(?, row_count), resume_offset = ?, updated_at = ?
                WHERE job_file_id = ?
                """,
                (processed_rows, uploaded_rows, inserted_rows, row_count, resume_offset, now, job_file_id),
            )
            self._recompute_job_summary(connection, row["job_id"])
            self._upsert_file_state_in_connection(connection, row, "in_progress", resume_offset, None, None)
            self._append_event_in_connection(
                connection,
                row["job_id"],
                event_type="file.progress",
                level="debug",
                message=f"Progress {row['filename']}: {processed_rows}/{row_count or 0}.",
                job_file_id=job_file_id,
                data={
                    "processedRows": processed_rows,
                    "uploadedRows": uploaded_rows,
                    "insertedRows": inserted_rows,
                    "rowCount": row_count,
                },
            )

    def mark_file_completed(self, job_file_id: int, uploaded_rows: int, inserted_rows: int) -> None:
        now = iso_now()
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM upload_job_files WHERE job_file_id = ?", (job_file_id,)).fetchone()
            if row is None:
                return
            row_count = row["row_count"] if row["row_count"] is not None else uploaded_rows
            connection.execute(
                """
                UPDATE upload_job_files
                SET status = 'succeeded', processed_rows = ?, uploaded_rows = ?,
                    inserted_rows = ?, resume_offset = 0, finished_at = COALESCE(finished_at, ?),
                    last_error_code = NULL, last_error_message = NULL, updated_at = ?
                WHERE job_file_id = ?
                """,
                (row_count, uploaded_rows, inserted_rows, now, now, job_file_id),
            )
            self._recompute_job_summary(connection, row["job_id"])
            self._upsert_file_state_in_connection(connection, row, "completed", 0, None, None)
            self._append_event_in_connection(
                connection,
                row["job_id"],
                event_type="file.succeeded",
                level="info",
                message=f"Completed {row['filename']}.",
                job_file_id=job_file_id,
                data={"uploadedRows": uploaded_rows, "insertedRows": inserted_rows},
            )

    def mark_file_failed(self, job_file_id: int, error_code: str, error_message: str, resume_offset: int | None = None) -> None:
        now = iso_now()
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM upload_job_files WHERE job_file_id = ?", (job_file_id,)).fetchone()
            if row is None:
                return
            next_offset = int(resume_offset if resume_offset is not None else row["resume_offset"] or 0)
            connection.execute(
                """
                UPDATE upload_job_files
                SET status = 'failed', resume_offset = ?, finished_at = COALESCE(finished_at, ?),
                    last_error_code = ?, last_error_message = ?, updated_at = ?
                WHERE job_file_id = ?
                """,
                (next_offset, now, error_code, error_message, now, job_file_id),
            )
            self._recompute_job_summary(connection, row["job_id"])
            self._upsert_file_state_in_connection(connection, row, "failed", next_offset, error_code, error_message)
            self._append_event_in_connection(
                connection,
                row["job_id"],
                event_type="file.failed",
                level="error",
                message=f"Failed {row['filename']}: {error_message}",
                job_file_id=job_file_id,
                data={"errorCode": error_code, "errorMessage": error_message, "resumeOffset": next_offset},
            )

    def mark_remaining_cancelled(self, job_id: str) -> None:
        now = iso_now()
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            rows = connection.execute(
                """
                SELECT *
                FROM upload_job_files
                WHERE job_id = ? AND status IN ('queued', 'running')
                """,
                (job_id,),
            ).fetchall()
            for row in rows:
                connection.execute(
                    """
                    UPDATE upload_job_files
                    SET status = 'cancelled', finished_at = COALESCE(finished_at, ?),
                        last_error_code = 'cancelled', last_error_message = 'Upload job was cancelled.',
                        updated_at = ?
                    WHERE job_file_id = ?
                    """,
                    (now, now, row["job_file_id"]),
                )
                self._upsert_file_state_in_connection(connection, row, "cancelled", row["resume_offset"], "cancelled", "Upload job was cancelled.")
            self._recompute_job_summary(connection, job_id)

    def mark_interrupted_active_jobs(self) -> int:
        now = iso_now()
        changed = 0
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            jobs = connection.execute(
                f"""
                SELECT job_id, status, cancel_requested
                FROM upload_jobs
                WHERE status IN ({",".join("?" for _ in ACTIVE_JOB_STATUSES)})
                """,
                ACTIVE_JOB_STATUSES,
            ).fetchall()
            for job in jobs:
                job_id = str(job["job_id"])
                was_cancelling = bool(job["cancel_requested"]) or str(job["status"]) == UploadJobStatus.cancelling.value
                connection.execute(
                    """
                    UPDATE upload_jobs
                    SET status = 'interrupted', finished_at = COALESCE(finished_at, ?),
                        error_code = 'interrupted',
                        error_message = 'Upload job was interrupted before completion.',
                        updated_at = ?
                    WHERE job_id = ?
                    """,
                    (now, now, job_id),
                )
                pending_file_status = "cancelled" if was_cancelling else "interrupted"
                pending_error = "cancelled" if pending_file_status == "cancelled" else "interrupted"
                pending_message = (
                    "Upload job was cancelled before shutdown completed."
                    if pending_file_status == "cancelled"
                    else "Upload job was interrupted before completion."
                )
                file_rows = connection.execute(
                    """
                    SELECT *
                    FROM upload_job_files
                    WHERE job_id = ? AND status IN ('queued', 'running')
                    """,
                    (job_id,),
                ).fetchall()
                for file_row in file_rows:
                    connection.execute(
                        """
                        UPDATE upload_job_files
                            SET status = ?, finished_at = COALESCE(finished_at, ?),
                            last_error_code = ?,
                            last_error_message = ?,
                            updated_at = ?
                        WHERE job_file_id = ?
                        """,
                        (pending_file_status, now, pending_error, pending_message, now, file_row["job_file_id"]),
                    )
                    self._upsert_file_state_in_connection(
                        connection,
                        file_row,
                        pending_file_status,
                        file_row["resume_offset"],
                        pending_error,
                        pending_message,
                    )
                self._append_event_in_connection(
                    connection,
                    job_id,
                    event_type="job.interrupted",
                    level="error",
                    message="Upload job was interrupted before completion.",
                    data={"wasCancelling": was_cancelling},
                )
                self._append_audit_in_connection(
                    connection,
                    action="upload.interrupted",
                    target_type="upload_job",
                    target_id=job_id,
                    params={},
                    result="failure",
                    error_code="interrupted",
                    error_message="Upload job was interrupted before completion.",
                    job_id=job_id,
                )
                changed += 1
        return changed

    def list_jobs(self, status: str | None = None, limit: int = 50, offset: int = 0) -> tuple[list[sqlite3.Row], int]:
        where = ""
        params: list[Any] = []
        if status:
            where = "WHERE status = ?"
            params.append(status)
        with self.connect() as connection:
            total_row = connection.execute(f"SELECT COUNT(*) AS count FROM upload_jobs {where}", params).fetchone()
            rows = connection.execute(
                f"""
                SELECT *
                FROM upload_jobs
                {where}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                [*params, limit, offset],
            ).fetchall()
        return rows, int(total_row["count"] if total_row else 0)

    def get_latest_job(self) -> sqlite3.Row | None:
        with self.connect() as connection:
            return connection.execute(
                "SELECT * FROM upload_jobs ORDER BY created_at DESC LIMIT 1"
            ).fetchone()

    def get_job(self, job_id: str) -> sqlite3.Row | None:
        with self.connect() as connection:
            return connection.execute("SELECT * FROM upload_jobs WHERE job_id = ?", (job_id,)).fetchone()

    def list_events(self, job_id: str, after_seq: int = 0, limit: int = 200) -> list[sqlite3.Row]:
        with self.connect() as connection:
            return connection.execute(
                """
                SELECT *
                FROM job_events
                WHERE job_id = ? AND seq > ?
                ORDER BY seq ASC
                LIMIT ?
                """,
                (job_id, after_seq, limit),
            ).fetchall()

    def latest_event_seq(self, job_id: str) -> int:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT COALESCE(MAX(seq), 0) AS seq FROM job_events WHERE job_id = ?",
                (job_id,),
            ).fetchone()
        return int(row["seq"] if row else 0)

    def append_event(
        self,
        job_id: str,
        *,
        event_type: str,
        level: str,
        message: str,
        job_file_id: int | None = None,
        data: dict[str, Any] | None = None,
    ) -> int:
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            return self._append_event_in_connection(
                connection,
                job_id,
                event_type=event_type,
                level=level,
                message=message,
                job_file_id=job_file_id,
                data=data,
            )

    def _append_event_in_connection(
        self,
        connection: sqlite3.Connection,
        job_id: str,
        *,
        event_type: str,
        level: str,
        message: str,
        job_file_id: int | None = None,
        data: dict[str, Any] | None = None,
    ) -> int:
        row = connection.execute(
            "SELECT COALESCE(MAX(seq), 0) + 1 AS next_seq FROM job_events WHERE job_id = ?",
            (job_id,),
        ).fetchone()
        seq = int(row["next_seq"] if row else 1)
        now = iso_now()
        connection.execute(
            """
            INSERT INTO job_events(job_id, seq, ts, level, event_type, message, job_file_id, data_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (job_id, seq, now, level, event_type, message, job_file_id, _json(data or {}), now),
        )
        return seq

    def append_audit(
        self,
        *,
        action: str,
        target_type: str,
        target_id: str | None,
        params: dict[str, Any],
        result: str,
        error_code: str | None = None,
        error_message: str | None = None,
        job_id: str | None = None,
    ) -> None:
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._append_audit_in_connection(
                connection,
                action=action,
                target_type=target_type,
                target_id=target_id,
                params=params,
                result=result,
                error_code=error_code,
                error_message=error_message,
                job_id=job_id,
            )

    def _append_audit_in_connection(
        self,
        connection: sqlite3.Connection,
        *,
        action: str,
        target_type: str,
        target_id: str | None,
        params: dict[str, Any],
        result: str,
        error_code: str | None = None,
        error_message: str | None = None,
        job_id: str | None = None,
    ) -> None:
        now = iso_now()
        connection.execute(
            """
            INSERT INTO audit_log(
              ts, actor, action, target_type, target_id, params_json_redacted,
              result, error_code, error_message, job_id, created_at
            )
            VALUES (?, 'local_operator', ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (now, action, target_type, target_id, _json(redact(params)), result, error_code, error_message, job_id, now),
        )

    def _upsert_file_state_in_connection(
        self,
        connection: sqlite3.Connection,
        file_row: sqlite3.Row,
        state: str,
        resume_offset: int | None,
        error_code: str | None,
        error_message: str | None,
    ) -> None:
        now = iso_now()
        legacy_key = f"{file_row['folder_path']}::{file_row['filename']}"
        completed_at = now if state == "completed" else None
        failed_at = now if state in {"failed", "interrupted"} else None
        connection.execute(
            """
            INSERT INTO upload_file_state(
              file_key, legacy_key, folder_label, folder_path, filename, path, kind,
              file_signature, state, resume_offset, last_error_code, last_error_message,
              retry_count, completed_at, failed_at, last_job_id, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(file_key) DO UPDATE SET
              file_signature = excluded.file_signature,
              state = excluded.state,
              resume_offset = excluded.resume_offset,
              last_error_code = excluded.last_error_code,
              last_error_message = excluded.last_error_message,
              retry_count = excluded.retry_count,
              completed_at = COALESCE(excluded.completed_at, upload_file_state.completed_at),
              failed_at = COALESCE(excluded.failed_at, upload_file_state.failed_at),
              last_job_id = excluded.last_job_id,
              updated_at = excluded.updated_at
            """,
            (
                file_row["file_key"],
                legacy_key,
                file_row["folder_label"],
                file_row["folder_path"],
                file_row["filename"],
                file_row["path"],
                file_row["kind"],
                file_row["file_signature"],
                state,
                int(resume_offset if resume_offset is not None else file_row["resume_offset"] or 0),
                error_code,
                error_message,
                int(file_row["retry_count"] or 0),
                completed_at,
                failed_at,
                file_row["job_id"],
                now,
                now,
            ),
        )

    def _recompute_job_summary(self, connection: sqlite3.Connection, job_id: str) -> None:
        row = connection.execute(
            """
            SELECT
              COUNT(*) AS total_files,
              COALESCE(SUM(CASE WHEN status = 'succeeded' THEN 1 ELSE 0 END), 0) AS succeeded_files,
              COALESCE(SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END), 0) AS failed_files,
              COALESCE(SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END), 0) AS cancelled_files,
              COALESCE(SUM(COALESCE(row_count, 0)), 0) AS total_rows,
              COALESCE(SUM(processed_rows), 0) AS processed_rows,
              COALESCE(SUM(uploaded_rows), 0) AS uploaded_rows,
              COALESCE(SUM(inserted_rows), 0) AS inserted_rows
            FROM upload_job_files
            WHERE job_id = ?
            """,
            (job_id,),
        ).fetchone()
        connection.execute(
            """
            UPDATE upload_jobs
            SET total_files = ?, succeeded_files = ?, failed_files = ?, cancelled_files = ?,
                total_rows = ?, processed_rows = ?, uploaded_rows = ?, inserted_rows = ?,
                updated_at = ?
            WHERE job_id = ?
            """,
            (
                int(row["total_files"] or 0),
                int(row["succeeded_files"] or 0),
                int(row["failed_files"] or 0),
                int(row["cancelled_files"] or 0),
                int(row["total_rows"] or 0),
                int(row["processed_rows"] or 0),
                int(row["uploaded_rows"] or 0),
                int(row["inserted_rows"] or 0),
                iso_now(),
                job_id,
            ),
        )


def redact(params: dict[str, Any]) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    for key, value in params.items():
        lower = key.lower()
        if "key" in lower or "token" in lower or "secret" in lower or "password" in lower:
            redacted[key] = "***"
        else:
            redacted[key] = value
    return redacted


def decode_json(value: str | None, fallback: Any) -> Any:
    return _loads(value, fallback)
