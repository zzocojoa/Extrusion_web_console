from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from backend.app.db.preview_repository import iso_now
from backend.app.schemas.upload_delete import DeleteRunStatus


ACTIVE_DELETE_STATUSES = (
    "preparing",
    "running",
    "finalizing",
    "commit_unknown",
    "reconciling",
    "reconciliation_failed",
)


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def decode_json(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


@dataclass(frozen=True)
class CreateDeleteRunResult:
    created: bool
    active_delete_run_id: str | None = None
    rejection_reason: str | None = None


class UploadDeleteRepository:
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
                CREATE TABLE IF NOT EXISTS delete_preflight_runs (
                  preflight_id TEXT PRIMARY KEY,
                  preview_run_id TEXT NOT NULL REFERENCES preview_runs(preview_run_id),
                  status TEXT NOT NULL CHECK(status IN ('ready','blocked','expired')),
                  selected_item_count INTEGER NOT NULL DEFAULT 0,
                  selected_key_count INTEGER NOT NULL DEFAULT 0,
                  selected_item_ids_json TEXT NOT NULL DEFAULT '[]',
                  selection_hash TEXT NOT NULL,
                  keyset_hash TEXT NOT NULL,
                  db_fingerprint_hash TEXT,
                  db_target_class TEXT NOT NULL DEFAULT 'unknown',
                  rollback_ready INTEGER NOT NULL DEFAULT 0,
                  rollback_blockers_json TEXT NOT NULL DEFAULT '[]',
                  expires_at TEXT NOT NULL,
                  timestamp_start_date TEXT,
                  timestamp_end_date TEXT,
                  reason_code TEXT,
                  error_message TEXT,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS delete_runs (
                  delete_run_id TEXT PRIMARY KEY,
                  preflight_id TEXT NOT NULL REFERENCES delete_preflight_runs(preflight_id),
                  preview_run_id TEXT NOT NULL REFERENCES preview_runs(preview_run_id),
                  status TEXT NOT NULL CHECK(status IN (
                    'preparing','running','finalizing','blocked','failed','succeeded',
                    'commit_unknown','reconciling','reconciled_succeeded',
                    'reconciled_rolled_back','reconciliation_failed'
                  )),
                  expected_key_count INTEGER NOT NULL DEFAULT 0,
                  deleted_key_count INTEGER NOT NULL DEFAULT 0,
                  db_fingerprint_hash TEXT,
                  selection_hash TEXT,
                  keyset_hash TEXT,
                  start_audit_id INTEGER,
                  rollback_ready INTEGER NOT NULL DEFAULT 0,
                  recovery_required INTEGER NOT NULL DEFAULT 0,
                  error_code TEXT,
                  error_message TEXT,
                  started_at TEXT,
                  finished_at TEXT,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS delete_run_items (
                  delete_run_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  delete_run_id TEXT NOT NULL REFERENCES delete_runs(delete_run_id) ON DELETE CASCADE,
                  preview_item_id INTEGER NOT NULL REFERENCES preview_items(preview_item_id),
                  source_preview_status TEXT NOT NULL,
                  file_signature_hash TEXT NOT NULL,
                  local_key_count INTEGER NOT NULL DEFAULT 0,
                  db_match_count INTEGER NOT NULL DEFAULT 0,
                  status TEXT NOT NULL CHECK(status IN ('pending','deleted','blocked','failed','unknown')),
                  reason_code TEXT,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL,
                  UNIQUE(delete_run_id, preview_item_id)
                );

                CREATE INDEX IF NOT EXISTS idx_delete_preflight_preview_created
                  ON delete_preflight_runs(preview_run_id, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_delete_runs_status_created
                  ON delete_runs(status, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_delete_runs_preflight
                  ON delete_runs(preflight_id, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_delete_run_items_run
                  ON delete_run_items(delete_run_id, status);
                """
            )
            self._ensure_column(connection, "delete_preflight_runs", "timestamp_start_date", "TEXT")
            self._ensure_column(connection, "delete_preflight_runs", "timestamp_end_date", "TEXT")

    def initialize(self) -> None:
        self.bootstrap()

    def _ensure_column(self, connection: sqlite3.Connection, table: str, column: str, definition: str) -> None:
        existing = {str(row["name"]) for row in connection.execute(f"PRAGMA table_info({table})").fetchall()}
        if column not in existing:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def ensure_schema(self) -> None:
        self.bootstrap()

    def get_active_delete_run_id(self) -> str | None:
        with self.connect() as connection:
            row = connection.execute(
                f"""
                SELECT delete_run_id
                FROM delete_runs
                WHERE status IN ({",".join("?" for _ in ACTIVE_DELETE_STATUSES)})
                ORDER BY created_at DESC
                LIMIT 1
                """,
                ACTIVE_DELETE_STATUSES,
            ).fetchone()
        return None if row is None else str(row["delete_run_id"])

    def mark_interrupted_active_delete_runs(self) -> int:
        now = iso_now()
        changed = 0
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            preparing = connection.execute(
                "SELECT delete_run_id FROM delete_runs WHERE status = 'preparing'"
            ).fetchall()
            for row in preparing:
                connection.execute(
                    """
                    UPDATE delete_runs
                    SET status = 'failed',
                        recovery_required = 0,
                        finished_at = COALESCE(finished_at, ?),
                        error_code = 'startup_interrupted_before_db_mutation',
                        error_message = 'Delete was interrupted before DB mutation started.',
                        updated_at = ?
                    WHERE delete_run_id = ?
                    """,
                    (now, now, row["delete_run_id"]),
                )
                changed += 1
            ambiguous = connection.execute(
                """
                SELECT delete_run_id
                FROM delete_runs
                WHERE status IN ('running','finalizing','reconciling')
                """
            ).fetchall()
            for row in ambiguous:
                connection.execute(
                    """
                    UPDATE delete_runs
                    SET status = 'commit_unknown',
                        recovery_required = 1,
                        error_code = 'startup_interrupted_commit_unknown',
                        error_message = 'Delete outcome must be reconciled before retry.',
                        updated_at = ?
                    WHERE delete_run_id = ?
                    """,
                    (now, row["delete_run_id"]),
                )
                connection.execute(
                    """
                    UPDATE delete_run_items
                    SET status = 'unknown',
                        reason_code = 'startup_interrupted_commit_unknown',
                        updated_at = ?
                    WHERE delete_run_id = ? AND status = 'pending'
                    """,
                    (now, row["delete_run_id"]),
                )
                changed += 1
        return changed

    def create_preflight(
        self,
        *,
        preflight_id: str,
        preview_run_id: str,
        status: str,
        selected_item_ids: list[int],
        selected_key_count: int,
        selection_hash: str,
        keyset_hash: str,
        db_fingerprint_hash: str | None,
        db_target_class: str,
        rollback_ready: bool,
        rollback_blockers: list[str],
        expires_at: str,
        timestamp_start_date: str | None = None,
        timestamp_end_date: str | None = None,
        reason_code: str | None = None,
        error_message: str | None = None,
    ) -> None:
        now = iso_now()
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO delete_preflight_runs(
                  preflight_id, preview_run_id, status, selected_item_count,
                  selected_key_count, selected_item_ids_json, selection_hash,
                  keyset_hash, db_fingerprint_hash, db_target_class, rollback_ready,
                  rollback_blockers_json, expires_at, timestamp_start_date,
                  timestamp_end_date, reason_code, error_message,
                  created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    preflight_id,
                    preview_run_id,
                    status,
                    len(selected_item_ids),
                    selected_key_count,
                    _json(selected_item_ids),
                    selection_hash,
                    keyset_hash,
                    db_fingerprint_hash,
                    db_target_class,
                    int(rollback_ready),
                    _json(rollback_blockers),
                    expires_at,
                    timestamp_start_date,
                    timestamp_end_date,
                    reason_code,
                    error_message,
                    now,
                    now,
                ),
            )

    def get_preflight(self, preflight_id: str) -> sqlite3.Row | None:
        with self.connect() as connection:
            return connection.execute(
                "SELECT * FROM delete_preflight_runs WHERE preflight_id = ?",
                (preflight_id,),
            ).fetchone()

    def expire_preflight(self, preflight_id: str) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE delete_preflight_runs
                SET status = 'expired', reason_code = 'preflight_expired', updated_at = ?
                WHERE preflight_id = ? AND status = 'ready'
                """,
                (iso_now(), preflight_id),
            )

    def get_preview_run(self, preview_run_id: str) -> sqlite3.Row | None:
        with self.connect() as connection:
            return connection.execute(
                "SELECT * FROM preview_runs WHERE preview_run_id = ?",
                (preview_run_id,),
            ).fetchone()

    def get_latest_preview_run_id(self) -> str | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT preview_run_id
                FROM preview_runs
                ORDER BY requested_at DESC, created_at DESC
                LIMIT 1
                """
            ).fetchone()
        return None if row is None else str(row["preview_run_id"])

    def get_preview_items(self, preview_run_id: str, preview_item_ids: list[int]) -> list[sqlite3.Row]:
        if not preview_item_ids:
            return []
        placeholders = ",".join("?" for _ in preview_item_ids)
        with self.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT *
                FROM preview_items
                WHERE preview_run_id = ? AND preview_item_id IN ({placeholders})
                ORDER BY preview_item_id ASC
                """,
                [preview_run_id, *preview_item_ids],
            ).fetchall()
        return list(rows)

    def has_active_preview_run(self) -> str | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT preview_run_id
                FROM preview_runs
                WHERE status IN ('queued','running','cancelling')
                ORDER BY created_at DESC
                LIMIT 1
                """
            ).fetchone()
        return None if row is None else str(row["preview_run_id"])

    def has_active_upload_job(self) -> str | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT job_id
                FROM upload_jobs
                WHERE status IN ('queued','running','pausing','paused','cancelling')
                ORDER BY created_at DESC
                LIMIT 1
                """
            ).fetchone()
        return None if row is None else str(row["job_id"])

    def create_delete_run_preparing(
        self,
        *,
        delete_run_id: str,
        preflight_id: str,
        preview_run_id: str,
        expected_key_count: int,
        db_fingerprint_hash: str,
        selection_hash: str,
        keyset_hash: str,
        rollback_ready: bool,
        selected_items: list[sqlite3.Row],
    ) -> CreateDeleteRunResult:
        now = iso_now()
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            active = connection.execute(
                f"""
                SELECT delete_run_id
                FROM delete_runs
                WHERE status IN ({",".join("?" for _ in ACTIVE_DELETE_STATUSES)})
                ORDER BY created_at DESC
                LIMIT 1
                """,
                ACTIVE_DELETE_STATUSES,
            ).fetchone()
            if active is not None:
                return CreateDeleteRunResult(created=False, active_delete_run_id=str(active["delete_run_id"]))
            connection.execute(
                """
                INSERT INTO delete_runs(
                  delete_run_id, preflight_id, preview_run_id, status,
                  expected_key_count, deleted_key_count, db_fingerprint_hash,
                  selection_hash, keyset_hash, rollback_ready, recovery_required,
                  started_at, created_at, updated_at
                )
                VALUES (?, ?, ?, 'preparing', ?, 0, ?, ?, ?, ?, 0, ?, ?, ?)
                """,
                (
                    delete_run_id,
                    preflight_id,
                    preview_run_id,
                    expected_key_count,
                    db_fingerprint_hash,
                    selection_hash,
                    keyset_hash,
                    int(rollback_ready),
                    now,
                    now,
                    now,
                ),
            )
            for item in selected_items:
                connection.execute(
                    """
                    INSERT INTO delete_run_items(
                      delete_run_id, preview_item_id, source_preview_status,
                      file_signature_hash, local_key_count, db_match_count,
                      status, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                    """,
                    (
                        delete_run_id,
                        item["preview_item_id"],
                        item["status"],
                        item["file_signature"],
                        int(item["local_key_count"] or 0),
                        int(item["db_match_count"] or 0),
                        now,
                        now,
                    ),
                )
        return CreateDeleteRunResult(created=True)

    def set_start_audit_id(self, delete_run_id: str, audit_id: int) -> bool:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                UPDATE delete_runs
                SET start_audit_id = ?, updated_at = ?
                WHERE delete_run_id = ? AND status = 'preparing'
                """,
                (audit_id, iso_now(), delete_run_id),
            )
        return cursor.rowcount == 1

    def mark_running(self, delete_run_id: str) -> bool:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                UPDATE delete_runs
                SET status = 'running', updated_at = ?
                WHERE delete_run_id = ? AND status = 'preparing' AND start_audit_id IS NOT NULL
                """,
                (iso_now(), delete_run_id),
            )
        return cursor.rowcount == 1

    def mark_status(
        self,
        delete_run_id: str,
        status_value: str,
        *,
        deleted_key_count: int | None = None,
        recovery_required: bool | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
        clear_error: bool = False,
        finish: bool = False,
    ) -> None:
        values: dict[str, Any] = {
            "status": status_value,
            "updated_at": iso_now(),
        }
        if deleted_key_count is not None:
            values["deleted_key_count"] = deleted_key_count
        if recovery_required is not None:
            values["recovery_required"] = int(recovery_required)
        if clear_error:
            values["error_code"] = None
            values["error_message"] = None
        elif error_code is not None:
            values["error_code"] = error_code
        if not clear_error and error_message is not None:
            values["error_message"] = error_message
        if finish:
            values["finished_at"] = iso_now()
        assignments = ", ".join(f"{key} = ?" for key in values)
        with self.connect() as connection:
            connection.execute(
                f"UPDATE delete_runs SET {assignments} WHERE delete_run_id = ?",
                [*values.values(), delete_run_id],
            )

    def mark_items(self, delete_run_id: str, status_value: str, reason_code: str | None = None) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE delete_run_items
                SET status = ?, reason_code = ?, updated_at = ?
                WHERE delete_run_id = ?
                """,
                (status_value, reason_code, iso_now(), delete_run_id),
            )

    def get_run(self, delete_run_id: str) -> sqlite3.Row | None:
        with self.connect() as connection:
            return connection.execute(
                "SELECT * FROM delete_runs WHERE delete_run_id = ?",
                (delete_run_id,),
            ).fetchone()

    def get_latest_run(self) -> sqlite3.Row | None:
        with self.connect() as connection:
            return connection.execute(
                "SELECT * FROM delete_runs ORDER BY created_at DESC LIMIT 1"
            ).fetchone()

    def get_run_items(self, delete_run_id: str) -> list[sqlite3.Row]:
        with self.connect() as connection:
            return list(
                connection.execute(
                    """
                    SELECT *
                    FROM delete_run_items
                    WHERE delete_run_id = ?
                    ORDER BY preview_item_id ASC
                    """,
                    (delete_run_id,),
                ).fetchall()
            )

    def selected_item_ids_for_preflight(self, preflight: sqlite3.Row) -> list[int]:
        decoded = decode_json(preflight["selected_item_ids_json"], [])
        if not isinstance(decoded, list):
            return []
        return [int(item) for item in decoded]

    def status_enum(self, row: sqlite3.Row) -> DeleteRunStatus:
        return DeleteRunStatus(str(row["status"]))
