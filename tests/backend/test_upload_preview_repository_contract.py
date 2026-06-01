from __future__ import annotations

import sqlite3
from importlib import import_module
from pathlib import Path
from types import ModuleType

import pytest


def _repository_module() -> ModuleType:
    try:
        return import_module("backend.app.db.preview_repository")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Expected backend.app.repositories.preview with PreviewRepository and "
            "SQLite preview_runs/preview_items persistence"
        )
        raise exc


def _build_repository(db_path: Path) -> object:
    module = _repository_module()
    repository_class = getattr(module, "PreviewRepository", None)
    assert repository_class is not None, "PreviewRepository class is required"

    for kwargs in (
        {"db_path": db_path},
        {"database_path": db_path},
        {"state_db_path": db_path},
        {"path": db_path},
    ):
        try:
            return repository_class(**kwargs)
        except TypeError:
            continue

    return repository_class(db_path)


def _initialize_schema(repository: object) -> None:
    for method_name in ("initialize", "initialize_schema", "ensure_schema", "migrate"):
        method = getattr(repository, method_name, None)
        if method is not None:
            method()
            return

    pytest.fail("PreviewRepository must expose initialize/initialize_schema/ensure_schema/migrate")


def _connect(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def test_preview_repository_initializes_required_tables_and_columns(tmp_path: Path) -> None:
    db_path = tmp_path / "web_console_state.db"
    repository = _build_repository(db_path)

    _initialize_schema(repository)

    with _connect(db_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        assert {"preview_runs", "preview_items"}.issubset(tables)

        run_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(preview_runs)").fetchall()
        }
        assert {
            "preview_run_id",
            "status",
            "requested_at",
            "started_at",
            "finished_at",
            "range_mode",
            "sources_json",
            "options_json",
            "config_snapshot_json",
            "cancel_requested",
            "db_status",
            "target_count",
            "already_in_db_count",
            "partial_overlap_count",
            "risky_count",
            "excluded_count",
            "error_code",
            "error_message",
        }.issubset(run_columns)

        item_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(preview_items)").fetchall()
        }
        assert {
            "preview_item_id",
            "preview_run_id",
            "file_key",
            "filename",
            "path",
            "kind",
            "status",
            "reason_code",
            "scan_mode",
            "local_key_count",
            "db_match_count",
            "upload_row_estimate",
            "first_timestamp",
            "last_timestamp",
            "device_ids_json",
            "issues_json",
            "error_code",
            "error_message",
        }.issubset(item_columns)


def test_preview_repository_schema_enforces_statuses_and_unique_file_per_run(tmp_path: Path) -> None:
    db_path = tmp_path / "web_console_state.db"
    repository = _build_repository(db_path)

    _initialize_schema(repository)

    with _connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO preview_runs (
              preview_run_id, status, requested_at, actor, range_mode,
              sources_json, options_json, config_snapshot_json, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "prv_test",
                "queued",
                "2026-06-01T09:00:00+09:00",
                "local_operator",
                "today",
                '["plc"]',
                "{}",
                "{}",
                "2026-06-01T09:00:00+09:00",
                "2026-06-01T09:00:00+09:00",
            ),
        )

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO preview_runs (
                  preview_run_id, status, requested_at, actor, range_mode,
                  sources_json, options_json, config_snapshot_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "prv_bad",
                    "silently_passed",
                    "2026-06-01T09:00:00+09:00",
                    "local_operator",
                    "today",
                    '["plc"]',
                    "{}",
                    "{}",
                    "2026-06-01T09:00:00+09:00",
                    "2026-06-01T09:00:00+09:00",
                ),
            )

        item_values = (
            "prv_test",
            "PLC/Factory_Integrated_Log_20260601_090000.csv",
            "PLC",
            "C:\\data\\plc",
            "Factory_Integrated_Log_20260601_090000.csv",
            "C:\\data\\plc\\Factory_Integrated_Log_20260601_090000.csv",
            "plc",
            "sig",
            "target",
            "db_no_match",
            "No exact keys are currently present in the database.",
            "full",
            "2026-06-01T09:00:00+09:00",
            "2026-06-01T09:00:00+09:00",
        )
        insert_item_sql = """
            INSERT INTO preview_items (
              preview_run_id, file_key, folder_label, folder_path, filename, path,
              kind, file_signature, status, reason_code, reason_text, scan_mode,
              created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
        connection.execute(insert_item_sql, item_values)

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(insert_item_sql, item_values)
