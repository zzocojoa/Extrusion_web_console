import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from backend.app.schemas.upload_preview import (
    PreviewDbStatus,
    PreviewItemStatus,
    PreviewRunStatus,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().isoformat()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class PreviewRepository:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.bootstrap()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def bootstrap(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS preview_runs (
                  preview_run_id TEXT PRIMARY KEY,
                  status TEXT NOT NULL CHECK(status IN (
                    'queued','running','succeeded','partial_failed','failed',
                    'cancelling','cancelled','timed_out'
                  )),
                  requested_at TEXT NOT NULL,
                  started_at TEXT,
                  finished_at TEXT,
                  actor TEXT NOT NULL DEFAULT 'local_operator',
                  range_mode TEXT NOT NULL,
                  start_date TEXT,
                  end_date TEXT,
                  sources_json TEXT NOT NULL,
                  options_json TEXT NOT NULL,
                  config_snapshot_json TEXT NOT NULL,
                  retry_of_run_id TEXT,
                  cancel_requested INTEGER NOT NULL DEFAULT 0,
                  db_status TEXT NOT NULL DEFAULT 'not_checked'
                    CHECK(db_status IN ('not_checked','reachable','unreachable','query_failed')),
                  total_files INTEGER NOT NULL DEFAULT 0,
                  target_count INTEGER NOT NULL DEFAULT 0,
                  already_in_db_count INTEGER NOT NULL DEFAULT 0,
                  partial_overlap_count INTEGER NOT NULL DEFAULT 0,
                  risky_count INTEGER NOT NULL DEFAULT 0,
                  excluded_count INTEGER NOT NULL DEFAULT 0,
                  upload_row_estimate INTEGER NOT NULL DEFAULT 0,
                  db_match_count INTEGER NOT NULL DEFAULT 0,
                  warning_count INTEGER NOT NULL DEFAULT 0,
                  timeout_stage TEXT,
                  timing_json TEXT NOT NULL DEFAULT '{}',
                  error_code TEXT,
                  error_message TEXT,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS preview_items (
                  preview_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  preview_run_id TEXT NOT NULL REFERENCES preview_runs(preview_run_id) ON DELETE CASCADE,
                  file_key TEXT NOT NULL,
                  folder_label TEXT NOT NULL,
                  folder_path TEXT NOT NULL,
                  filename TEXT NOT NULL,
                  path TEXT NOT NULL,
                  kind TEXT NOT NULL,
                  file_date TEXT,
                  size_bytes INTEGER,
                  mtime_ns INTEGER,
                  modified_at TEXT,
                  file_signature TEXT NOT NULL,
                  status TEXT NOT NULL CHECK(status IN (
                    'target','already_in_db','partial_overlap','risky','excluded'
                  )),
                  reason_code TEXT NOT NULL,
                  reason_text TEXT NOT NULL,
                  scan_mode TEXT NOT NULL CHECK(scan_mode IN ('metadata','sample','full','incomplete')),
                  sample_row_count INTEGER,
                  row_count INTEGER,
                  local_key_count INTEGER,
                  db_match_count INTEGER,
                  upload_row_estimate INTEGER,
                  first_timestamp TEXT,
                  last_timestamp TEXT,
                  device_ids_json TEXT NOT NULL DEFAULT '[]',
                  issues_json TEXT NOT NULL DEFAULT '[]',
                  timeout_stage TEXT,
                  timing_json TEXT NOT NULL DEFAULT '{}',
                  error_code TEXT,
                  error_message TEXT,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL,
                  UNIQUE(preview_run_id, file_key)
                );

                CREATE INDEX IF NOT EXISTS idx_preview_runs_status_created
                  ON preview_runs(status, created_at DESC);

                CREATE INDEX IF NOT EXISTS idx_preview_items_run_status
                  ON preview_items(preview_run_id, status);

                CREATE INDEX IF NOT EXISTS idx_preview_items_run_filename
                  ON preview_items(preview_run_id, filename);
                """
            )
            self._ensure_column(connection, "preview_runs", "timeout_stage", "timeout_stage TEXT")
            self._ensure_column(
                connection,
                "preview_runs",
                "timing_json",
                "timing_json TEXT NOT NULL DEFAULT '{}'",
            )
            self._ensure_column(connection, "preview_items", "timeout_stage", "timeout_stage TEXT")
            self._ensure_column(
                connection,
                "preview_items",
                "timing_json",
                "timing_json TEXT NOT NULL DEFAULT '{}'",
            )

    def _ensure_column(
        self,
        connection: sqlite3.Connection,
        table_name: str,
        column_name: str,
        column_ddl: str,
    ) -> None:
        columns = {row["name"] for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()}
        if column_name not in columns:
            connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_ddl}")

    def initialize(self) -> None:
        self.bootstrap()

    def ensure_schema(self) -> None:
        self.bootstrap()

    def has_active_run(self) -> str | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT preview_run_id
                FROM preview_runs
                WHERE status IN ('queued', 'running', 'cancelling')
                ORDER BY created_at DESC
                LIMIT 1
                """
            ).fetchone()
        return None if row is None else str(row["preview_run_id"])

    def mark_interrupted_active_runs(self) -> int:
        now = iso_now()
        with self.connect() as connection:
            cursor = connection.execute(
                """
                UPDATE preview_runs
                SET status = 'failed',
                    finished_at = COALESCE(finished_at, ?),
                    error_code = 'interrupted',
                    error_message = 'Preview was interrupted before completion.',
                    updated_at = ?
                WHERE status IN ('queued', 'running', 'cancelling')
                """,
                (now, now),
            )
            return int(cursor.rowcount)

    def create_run_if_no_active(
        self,
        *,
        preview_run_id: str,
        range_mode: str,
        start_date: str | None,
        end_date: str | None,
        sources: list[str],
        options: dict[str, Any],
        config_snapshot: dict[str, Any],
        retry_of_run_id: str | None,
    ) -> str | None:
        now = iso_now()
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                """
                SELECT preview_run_id
                FROM preview_runs
                WHERE status IN ('queued', 'running', 'cancelling')
                ORDER BY created_at DESC
                LIMIT 1
                """
            ).fetchone()
            if row is not None:
                return str(row["preview_run_id"])
            connection.execute(
                """
                INSERT INTO preview_runs(
                  preview_run_id, status, requested_at, range_mode, start_date, end_date,
                  sources_json, options_json, config_snapshot_json, retry_of_run_id,
                  created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    preview_run_id,
                    PreviewRunStatus.queued.value,
                    now,
                    range_mode,
                    start_date,
                    end_date,
                    _json(sources),
                    _json(options),
                    _json(config_snapshot),
                    retry_of_run_id,
                    now,
                    now,
                ),
            )
            return None

    def create_run(
        self,
        *,
        preview_run_id: str,
        range_mode: str,
        start_date: str | None,
        end_date: str | None,
        sources: list[str],
        options: dict[str, Any],
        config_snapshot: dict[str, Any],
        retry_of_run_id: str | None,
    ) -> None:
        now = iso_now()
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO preview_runs(
                  preview_run_id, status, requested_at, range_mode, start_date, end_date,
                  sources_json, options_json, config_snapshot_json, retry_of_run_id,
                  created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    preview_run_id,
                    PreviewRunStatus.queued.value,
                    now,
                    range_mode,
                    start_date,
                    end_date,
                    _json(sources),
                    _json(options),
                    _json(config_snapshot),
                    retry_of_run_id,
                    now,
                    now,
                ),
            )

    def update_run(self, preview_run_id: str, **values: Any) -> None:
        if not values:
            return
        values["updated_at"] = iso_now()
        assignments = ", ".join(f"{key} = ?" for key in values)
        params = list(values.values()) + [preview_run_id]
        with self.connect() as connection:
            connection.execute(
                f"UPDATE preview_runs SET {assignments} WHERE preview_run_id = ?",
                params,
            )

    def request_cancel(self, preview_run_id: str) -> PreviewRunStatus | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT status FROM preview_runs WHERE preview_run_id = ?",
                (preview_run_id,),
            ).fetchone()
            if row is None:
                return None
            status = str(row["status"])
            if status in {"queued", "running"}:
                connection.execute(
                    """
                    UPDATE preview_runs
                    SET cancel_requested = 1, status = 'cancelling', updated_at = ?
                    WHERE preview_run_id = ?
                    """,
                    (iso_now(), preview_run_id),
                )
                return PreviewRunStatus.cancelling
            return PreviewRunStatus(status)

    def is_cancel_requested(self, preview_run_id: str) -> bool:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT cancel_requested FROM preview_runs WHERE preview_run_id = ?",
                (preview_run_id,),
            ).fetchone()
        return bool(row and row["cancel_requested"])

    def insert_item(self, preview_run_id: str, item: dict[str, Any]) -> int:
        now = iso_now()
        payload = {
            "preview_run_id": preview_run_id,
            "device_ids_json": _json(item.get("device_ids", [])),
            "issues_json": _json(item.get("issues", [])),
            "timing_json": _json(item.get("timing", {})),
            "created_at": now,
            "updated_at": now,
            **item,
        }
        payload.pop("device_ids", None)
        payload.pop("issues", None)
        payload.pop("timing", None)
        columns = ", ".join(payload.keys())
        placeholders = ", ".join("?" for _ in payload)
        with self.connect() as connection:
            cursor = connection.execute(
                f"INSERT INTO preview_items({columns}) VALUES ({placeholders})",
                list(payload.values()),
            )
            return int(cursor.lastrowid)

    def recompute_summary(
        self,
        preview_run_id: str,
        *,
        status: PreviewRunStatus,
        db_status: PreviewDbStatus,
        error_code: str | None = None,
        error_message: str | None = None,
        timeout_stage: str | None = None,
        timing: dict[str, Any] | None = None,
    ) -> None:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT status, COUNT(*) AS count,
                       COALESCE(SUM(upload_row_estimate), 0) AS upload_rows,
                       COALESCE(SUM(db_match_count), 0) AS db_matches
                FROM preview_items
                WHERE preview_run_id = ?
                GROUP BY status
                """,
                (preview_run_id,),
            ).fetchall()
            counts = {row["status"]: int(row["count"]) for row in rows}
            total = sum(counts.values())
            upload_rows = sum(int(row["upload_rows"]) for row in rows)
            db_matches = sum(int(row["db_matches"]) for row in rows)
            connection.execute(
                """
                UPDATE preview_runs
                SET status = ?, finished_at = COALESCE(finished_at, ?), db_status = ?,
                    total_files = ?, target_count = ?, already_in_db_count = ?,
                    partial_overlap_count = ?, risky_count = ?, excluded_count = ?,
                    upload_row_estimate = ?, db_match_count = ?,
                    timeout_stage = ?, timing_json = ?,
                    error_code = ?, error_message = ?, updated_at = ?
                WHERE preview_run_id = ?
                """,
                (
                    status.value,
                    iso_now(),
                    db_status.value,
                    total,
                    counts.get(PreviewItemStatus.target.value, 0),
                    counts.get(PreviewItemStatus.already_in_db.value, 0),
                    counts.get(PreviewItemStatus.partial_overlap.value, 0),
                    counts.get(PreviewItemStatus.risky.value, 0),
                    counts.get(PreviewItemStatus.excluded.value, 0),
                    upload_rows,
                    db_matches,
                    timeout_stage,
                    _json(timing or {}),
                    error_code,
                    error_message,
                    iso_now(),
                    preview_run_id,
                ),
            )

    def get_run(self, preview_run_id: str) -> sqlite3.Row | None:
        with self.connect() as connection:
            return connection.execute(
                "SELECT * FROM preview_runs WHERE preview_run_id = ?",
                (preview_run_id,),
            ).fetchone()

    def get_latest_run(self, completed_only: bool = False) -> sqlite3.Row | None:
        where = ""
        if completed_only:
            where = "WHERE status IN ('succeeded', 'partial_failed', 'failed', 'cancelled', 'timed_out')"
        with self.connect() as connection:
            return connection.execute(
                f"SELECT * FROM preview_runs {where} ORDER BY created_at DESC LIMIT 1"
            ).fetchone()

    def list_items(
        self,
        preview_run_id: str,
        *,
        status: str | None = None,
        query: str | None = None,
        sort: str = "status",
        order: str = "asc",
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[sqlite3.Row], int]:
        sortable = {
            "status": "status",
            "fileDate": "file_date",
            "filename": "filename",
            "uploadRows": "upload_row_estimate",
            "modifiedAt": "modified_at",
        }
        where = ["preview_run_id = ?"]
        params: list[Any] = [preview_run_id]
        if status:
            where.append("status = ?")
            params.append(status)
        if query:
            where.append("(filename LIKE ? OR path LIKE ? OR reason_code LIKE ? OR reason_text LIKE ?)")
            like_query = f"%{query}%"
            params.extend([like_query, like_query, like_query, like_query])
        where_sql = " AND ".join(where)
        order_sql = "DESC" if order.lower() == "desc" else "ASC"
        sort_sql = sortable.get(sort, "status")
        with self.connect() as connection:
            total_row = connection.execute(
                f"SELECT COUNT(*) AS count FROM preview_items WHERE {where_sql}",
                params,
            ).fetchone()
            rows = connection.execute(
                f"""
                SELECT *
                FROM preview_items
                WHERE {where_sql}
                ORDER BY {sort_sql} {order_sql}, filename ASC
                LIMIT ? OFFSET ?
                """,
                params + [limit, offset],
            ).fetchall()
        return rows, int(total_row["count"] if total_row else 0)
