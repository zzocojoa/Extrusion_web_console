import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from backend.app.db.preview_repository import iso_now

ACTIVE_RUNTIME_OPERATION_STATUSES = ("queued", "running")


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def decode_json(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: ("[redacted]" if "key" in key.lower() or "token" in key.lower() else redact(item)) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


class RuntimeRepository:
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
                CREATE TABLE IF NOT EXISTS runtime_operations (
                  operation_id TEXT PRIMARY KEY,
                  kind TEXT NOT NULL CHECK(kind IN ('start','stop')),
                  status TEXT NOT NULL CHECK(status IN (
                    'queued','running','succeeded','failed','blocked','timed_out','cancelled','interrupted'
                  )),
                  requested_at TEXT NOT NULL,
                  started_at TEXT,
                  finished_at TEXT,
                  actor TEXT NOT NULL DEFAULT 'local_operator',
                  config_snapshot_json TEXT NOT NULL DEFAULT '{}',
                  error_code TEXT,
                  error_message TEXT,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS runtime_events (
                  event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  operation_id TEXT NOT NULL REFERENCES runtime_operations(operation_id) ON DELETE CASCADE,
                  seq INTEGER NOT NULL,
                  ts TEXT NOT NULL,
                  level TEXT NOT NULL CHECK(level IN ('info','warning','error')),
                  event_type TEXT NOT NULL,
                  message TEXT NOT NULL,
                  data_json TEXT NOT NULL DEFAULT '{}',
                  created_at TEXT NOT NULL,
                  UNIQUE(operation_id, seq)
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

                CREATE INDEX IF NOT EXISTS idx_runtime_operations_status_created
                  ON runtime_operations(status, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_runtime_events_operation_seq
                  ON runtime_events(operation_id, seq);
                CREATE INDEX IF NOT EXISTS idx_audit_log_runtime
                  ON audit_log(target_type, target_id, created_at DESC);
                """
            )

    def get_active_operation_id(self) -> str | None:
        with self.connect() as connection:
            row = connection.execute(
                f"""
                SELECT operation_id
                FROM runtime_operations
                WHERE status IN ({",".join("?" for _ in ACTIVE_RUNTIME_OPERATION_STATUSES)})
                ORDER BY created_at DESC
                LIMIT 1
                """,
                ACTIVE_RUNTIME_OPERATION_STATUSES,
            ).fetchone()
        return None if row is None else str(row["operation_id"])

    def create_operation(self, operation_id: str, *, kind: str, config_snapshot: dict[str, Any]) -> None:
        now = iso_now()
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO runtime_operations(
                  operation_id, kind, status, requested_at, actor, config_snapshot_json, created_at, updated_at
                )
                VALUES (?, ?, 'queued', ?, 'local_operator', ?, ?, ?)
                """,
                (operation_id, kind, now, _json(config_snapshot), now, now),
            )
            self._append_event_in_connection(
                connection,
                operation_id,
                event_type=f"runtime.{kind}.queued",
                level="info",
                message=f"Local Supabase {kind} operation queued.",
            )

    def mark_running(self, operation_id: str) -> None:
        now = iso_now()
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                UPDATE runtime_operations
                SET status = 'running', started_at = COALESCE(started_at, ?), updated_at = ?
                WHERE operation_id = ? AND status = 'queued'
                """,
                (now, now, operation_id),
            )
            self._append_event_in_connection(
                connection,
                operation_id,
                event_type="runtime.operation.started",
                level="info",
                message="Runtime operation started.",
            )

    def finish_operation(self, operation_id: str, *, status: str, error_code: str | None = None, error_message: str | None = None) -> None:
        now = iso_now()
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                UPDATE runtime_operations
                SET status = ?, finished_at = COALESCE(finished_at, ?), error_code = ?, error_message = ?, updated_at = ?
                WHERE operation_id = ? AND status IN ('queued','running')
                """,
                (status, now, error_code, error_message, now, operation_id),
            )
            level = "info" if status == "succeeded" else "error"
            self._append_event_in_connection(
                connection,
                operation_id,
                event_type=f"runtime.operation.{status}",
                level=level,
                message=f"Runtime operation finished with status {status}.",
                data={"errorCode": error_code, "errorMessage": error_message},
            )

    def mark_interrupted_active_operations(self) -> None:
        now = iso_now()
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            rows = connection.execute(
                "SELECT operation_id FROM runtime_operations WHERE status IN ('queued','running')"
            ).fetchall()
            for row in rows:
                operation_id = str(row["operation_id"])
                connection.execute(
                    """
                    UPDATE runtime_operations
                    SET status = 'interrupted', finished_at = ?, error_code = 'interrupted',
                        error_message = 'Runtime operation was interrupted before completion.', updated_at = ?
                    WHERE operation_id = ?
                    """,
                    (now, now, operation_id),
                )
                self._append_event_in_connection(
                    connection,
                    operation_id,
                    event_type="runtime.operation.interrupted",
                    level="error",
                    message="Runtime operation was interrupted before completion.",
                )
                self._append_audit_in_connection(
                    connection,
                    action="runtime.interrupted",
                    target_type="runtime_operation",
                    target_id=operation_id,
                    params={},
                    result="failure",
                    error_code="interrupted",
                    error_message="Runtime operation was interrupted before completion.",
                )

    def get_operation(self, operation_id: str) -> sqlite3.Row | None:
        with self.connect() as connection:
            return connection.execute("SELECT * FROM runtime_operations WHERE operation_id = ?", (operation_id,)).fetchone()

    def list_events(self, operation_id: str, *, limit: int = 100) -> list[sqlite3.Row]:
        with self.connect() as connection:
            return connection.execute(
                """
                SELECT * FROM runtime_events
                WHERE operation_id = ?
                ORDER BY seq ASC
                LIMIT ?
                """,
                (operation_id, limit),
            ).fetchall()

    def append_event(self, operation_id: str, *, event_type: str, level: str, message: str, data: dict[str, Any] | None = None) -> int:
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            return self._append_event_in_connection(
                connection,
                operation_id,
                event_type=event_type,
                level=level,
                message=message,
                data=data,
            )

    def _append_event_in_connection(
        self,
        connection: sqlite3.Connection,
        operation_id: str,
        *,
        event_type: str,
        level: str,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> int:
        row = connection.execute(
            "SELECT COALESCE(MAX(seq), 0) + 1 AS next_seq FROM runtime_events WHERE operation_id = ?",
            (operation_id,),
        ).fetchone()
        seq = int(row["next_seq"] if row else 1)
        now = iso_now()
        connection.execute(
            """
            INSERT INTO runtime_events(operation_id, seq, ts, level, event_type, message, data_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (operation_id, seq, now, level, event_type, message, _json(data or {}), now),
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
    ) -> None:
        now = iso_now()
        connection.execute(
            """
            INSERT INTO audit_log(
              ts, actor, action, target_type, target_id, params_json_redacted,
              result, error_code, error_message, created_at
            )
            VALUES (?, 'local_operator', ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (now, action, target_type, target_id, _json(redact(params)), result, error_code, error_message, now),
        )
