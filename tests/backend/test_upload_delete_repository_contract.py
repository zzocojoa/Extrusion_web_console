import sqlite3
from pathlib import Path

from backend.app.db.preview_repository import PreviewRepository
from backend.app.db.upload_delete_repository import UploadDeleteRepository


def _connect(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def test_delete_repository_initializes_required_tables_and_statuses(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    PreviewRepository(db_path).ensure_schema()
    repository = UploadDeleteRepository(db_path)

    repository.ensure_schema()

    with _connect(db_path) as connection:
        tables = {
            row["name"]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
        }
        assert {"delete_preflight_runs", "delete_runs", "delete_run_items"}.issubset(tables)

        run_columns = {row["name"] for row in connection.execute("PRAGMA table_info(delete_runs)").fetchall()}
        assert {
            "delete_run_id",
            "preflight_id",
            "preview_run_id",
            "status",
            "expected_key_count",
            "deleted_key_count",
            "db_fingerprint_hash",
            "selection_hash",
            "keyset_hash",
            "start_audit_id",
            "recovery_required",
            "error_code",
        }.issubset(run_columns)


def test_delete_repository_startup_recovery_distinguishes_preparing_from_running(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    PreviewRepository(db_path).ensure_schema()
    repository = UploadDeleteRepository(db_path)
    now = "2026-06-18T00:00:00+00:00"
    with repository.connect() as connection:
        connection.execute(
            """
            INSERT INTO preview_runs(
              preview_run_id, status, requested_at, range_mode, sources_json,
              options_json, config_snapshot_json, created_at, updated_at
            )
            VALUES ('prv_done', 'succeeded', ?, 'today', '["plc"]', '{}', '{}', ?, ?)
            """,
            (now, now, now),
        )
        for preflight_id, delete_run_id, status in (
            ("dpf_prepare", "del_prepare", "preparing"),
            ("dpf_run", "del_run", "running"),
            ("dpf_final", "del_final", "finalizing"),
        ):
            connection.execute(
                """
                INSERT INTO delete_preflight_runs(
                  preflight_id, preview_run_id, status, selected_item_count,
                  selected_key_count, selection_hash, keyset_hash, expires_at,
                  created_at, updated_at
                )
                VALUES (?, 'prv_done', 'ready', 1, 1, 'sel', 'key', ?, ?, ?)
                """,
                (preflight_id, now, now, now),
            )
            connection.execute(
                """
                INSERT INTO delete_runs(
                  delete_run_id, preflight_id, preview_run_id, status,
                  expected_key_count, db_fingerprint_hash, selection_hash,
                  keyset_hash, created_at, updated_at
                )
                VALUES (?, ?, 'prv_done', ?, 1, 'fp', 'sel', 'key', ?, ?)
                """,
                (delete_run_id, preflight_id, status, now, now),
            )

    changed = repository.mark_interrupted_active_delete_runs()

    assert changed == 3
    prepare = repository.get_run("del_prepare")
    running = repository.get_run("del_run")
    finalizing = repository.get_run("del_final")
    assert prepare["status"] == "failed"
    assert prepare["error_code"] == "startup_interrupted_before_db_mutation"
    assert running["status"] == "commit_unknown"
    assert running["recovery_required"] == 1
    assert finalizing["status"] == "commit_unknown"
    assert repository.get_active_delete_run_id() in {"del_run", "del_final"}
