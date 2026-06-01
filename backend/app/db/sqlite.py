import sqlite3
from pathlib import Path


SCHEMA_SQL = """
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


def connect(db_path: str | Path) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def init_db(db_path: str | Path) -> None:
    with connect(db_path) as connection:
        connection.executescript(SCHEMA_SQL)
