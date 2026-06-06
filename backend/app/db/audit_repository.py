import json
import re
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from backend.app.db.preview_repository import iso_now
from backend.app.schemas.audit import AuditOrder, AuditResult, AuditSort


REDACTED = "[redacted]"
MAX_ERROR_MESSAGE_LENGTH = 500

SENSITIVE_KEY_PARTS = (
    "password",
    "token",
    "secret",
    "key",
    "authorization",
    "credential",
    "dsn",
    "connection",
    "conn_str",
    "database_url",
    "db_url",
    "service_role",
    "anon_key",
    "service_key",
)

BEARER_RE = re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]+", re.IGNORECASE)
JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")
CREDENTIAL_URL_RE = re.compile(r"\b([a-z][a-z0-9+.-]*://)([^/\s:@]+):([^@\s/]+)@([^\s]+)", re.IGNORECASE)
SUPABASE_KEY_RE = re.compile(r"\b(?:sb_[A-Za-z0-9_-]{20,}|eyJ[A-Za-z0-9_-]{20,})")

SORT_COLUMNS = {
    AuditSort.ts: "ts",
    AuditSort.action: "action",
    AuditSort.result: "result",
    AuditSort.target_type: "target_type",
}


@dataclass(frozen=True)
class AuditLogFilters:
    from_ts: datetime | None = None
    to_ts: datetime | None = None
    action: str | None = None
    result: AuditResult | None = None
    target_type: str | None = None
    target_id: str | None = None
    job_id: str | None = None
    request_id: str | None = None
    q: str | None = None
    limit: int = 50
    offset: int = 0
    sort: AuditSort = AuditSort.ts
    order: AuditOrder = AuditOrder.desc


@dataclass(frozen=True)
class AuditLogQueryResult:
    rows: list[sqlite3.Row]
    total_items: int


def _json(value: Any) -> str:
    return json.dumps(redact_audit_payload(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def decode_params_json(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError:
        return {}
    if not isinstance(decoded, dict):
        return {}
    redacted = redact_audit_payload(decoded)
    return redacted if isinstance(redacted, dict) else {}


def sanitize_text(value: str | None, *, max_length: int = MAX_ERROR_MESSAGE_LENGTH) -> str | None:
    if value is None:
        return None
    sanitized = redact_secret_strings(str(value))
    if len(sanitized) > max_length:
        return f"{sanitized[:max_length]}..."
    return sanitized


def redact_secret_strings(value: str) -> str:
    redacted = BEARER_RE.sub(f"Bearer {REDACTED}", value)
    redacted = JWT_RE.sub(REDACTED, redacted)
    redacted = CREDENTIAL_URL_RE.sub(lambda match: f"{match.group(1)}{REDACTED}@{match.group(4)}", redacted)
    redacted = SUPABASE_KEY_RE.sub(REDACTED, redacted)
    return redacted


def redact_audit_payload(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            lower_key = key_text.lower()
            if lower_key == "tokenpresent" and isinstance(item, bool):
                redacted[key_text] = item
            elif any(part in lower_key for part in SENSITIVE_KEY_PARTS):
                redacted[key_text] = REDACTED
            else:
                redacted[key_text] = redact_audit_payload(item)
        return redacted
    if isinstance(value, list):
        return [redact_audit_payload(item) for item in value]
    if isinstance(value, str):
        return redact_secret_strings(value)
    return value


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class AuditRepository:
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

                CREATE INDEX IF NOT EXISTS idx_audit_log_ts
                  ON audit_log(ts DESC);
                CREATE INDEX IF NOT EXISTS idx_audit_log_action_ts
                  ON audit_log(action, ts DESC);
                CREATE INDEX IF NOT EXISTS idx_audit_log_result_ts
                  ON audit_log(result, ts DESC);
                CREATE INDEX IF NOT EXISTS idx_audit_log_target_ts
                  ON audit_log(target_type, target_id, ts DESC);
                CREATE INDEX IF NOT EXISTS idx_audit_log_job_id
                  ON audit_log(job_id, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_audit_log_runtime
                  ON audit_log(target_type, target_id, created_at DESC);

                CREATE TRIGGER IF NOT EXISTS audit_log_no_update
                BEFORE UPDATE ON audit_log
                BEGIN
                  SELECT RAISE(ABORT, 'audit_log_append_only');
                END;

                CREATE TRIGGER IF NOT EXISTS audit_log_no_delete
                BEFORE DELETE ON audit_log
                BEGIN
                  SELECT RAISE(ABORT, 'audit_log_append_only');
                END;
                """
            )

    def insert_audit(
        self,
        *,
        action: str,
        target_type: str,
        target_id: str | None,
        params: dict[str, Any],
        result: AuditResult | str,
        actor: str = "local_operator",
        error_code: str | None = None,
        error_message: str | None = None,
        job_id: str | None = None,
        request_id: str | None = None,
    ) -> int:
        now = iso_now()
        result_value = result.value if isinstance(result, AuditResult) else result
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO audit_log(
                  ts, actor, action, target_type, target_id, params_json_redacted,
                  result, error_code, error_message, job_id, request_id, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now,
                    actor,
                    action,
                    target_type,
                    target_id,
                    _json(params),
                    result_value,
                    error_code,
                    sanitize_text(error_message),
                    job_id,
                    request_id,
                    now,
                ),
            )
            return int(cursor.lastrowid)

    def list_audit_logs(self, filters: AuditLogFilters) -> AuditLogQueryResult:
        where_sql, params = self._where_clause(filters)
        sort_column = SORT_COLUMNS[filters.sort]
        order = filters.order.value.upper()
        limit = max(1, min(200, int(filters.limit)))
        offset = max(0, int(filters.offset))

        with self.connect() as connection:
            total_row = connection.execute(
                f"SELECT COUNT(*) AS count FROM audit_log {where_sql}",
                params,
            ).fetchone()
            rows = connection.execute(
                f"""
                SELECT *
                FROM audit_log
                {where_sql}
                ORDER BY {sort_column} {order}, audit_id {order}
                LIMIT ? OFFSET ?
                """,
                [*params, limit, offset],
            ).fetchall()
        return AuditLogQueryResult(rows=list(rows), total_items=int(total_row["count"] if total_row else 0))

    def _where_clause(self, filters: AuditLogFilters) -> tuple[str, list[Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if filters.from_ts is not None:
            clauses.append("ts >= ?")
            params.append(filters.from_ts.isoformat())
        if filters.to_ts is not None:
            clauses.append("ts <= ?")
            params.append(filters.to_ts.isoformat())
        for column, value in (
            ("action", filters.action),
            ("target_type", filters.target_type),
            ("target_id", filters.target_id),
            ("job_id", filters.job_id),
            ("request_id", filters.request_id),
        ):
            if value:
                clauses.append(f"{column} = ?")
                params.append(value)
        if filters.result is not None:
            clauses.append("result = ?")
            params.append(filters.result.value)
        if filters.q:
            like_value = f"%{_escape_like(filters.q.strip())}%"
            clauses.append(
                """
                (
                  CAST(audit_id AS TEXT) LIKE ? ESCAPE '\\'
                  OR action LIKE ? ESCAPE '\\'
                  OR target_type LIKE ? ESCAPE '\\'
                  OR target_id LIKE ? ESCAPE '\\'
                  OR result LIKE ? ESCAPE '\\'
                  OR job_id LIKE ? ESCAPE '\\'
                  OR request_id LIKE ? ESCAPE '\\'
                  OR error_code LIKE ? ESCAPE '\\'
                  OR actor LIKE ? ESCAPE '\\'
                )
                """
            )
            params.extend([like_value] * 9)
        if not clauses:
            return "", []
        return f"WHERE {' AND '.join(clauses)}", params
