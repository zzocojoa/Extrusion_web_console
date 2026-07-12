from __future__ import annotations

import re
import sys
from types import SimpleNamespace
from pathlib import Path

import pytest

from backend.app.services.upload_preview import (
    PreviewCancelledError,
    PreviewDbQueryError,
    PreviewDbUnavailableError,
    SupabaseExactReconciler,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_supabase_reconciliation_repository_uses_exact_composite_key_join() -> None:
    source_path = REPO_ROOT / "backend" / "app" / "services" / "upload_preview.py"

    assert source_path.exists(), (
        "Expected SupabaseExactReconciler in backend/app/services/upload_preview.py"
    )
    source = source_path.read_text(encoding="utf-8")
    source_lower = source.lower()

    assert "public.all_metrics" in source
    assert "CREATE TEMP TABLE preview_key_stage" in source
    assert "executemany" in source
    assert "device_id" in source
    assert "timestamp" in source_lower
    assert re.search(r"\bjoin\b", source, re.IGNORECASE), (
        "Preview DB matching should join candidate keys to public.all_metrics"
    )
    assert not re.search(r"max\s*\(\s*[\"']?timestamp", source_lower), (
        "Preview reconciliation must not infer matches from MAX(timestamp)"
    )
    assert "latest_timestamp" not in source_lower
    assert not re.search(
        r"order\s+by\s+[\"']?timestamp[\"']?\s+desc\s+limit\s+1",
        source_lower,
    )


def test_supabase_migration_preserves_all_metrics_timestamp_device_unique_key() -> None:
    migration_dir = Path(r"C:\Users\user\Documents\GitHub\Extrusion_data\supabase\migrations")

    if not migration_dir.exists():
        pytest.skip("Legacy Extrusion_data migrations are not available in this environment")
    migration_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in migration_dir.glob("*.sql")
        if "all_metrics" in path.read_text(encoding="utf-8", errors="ignore")
    ).lower()

    assert "all_metrics" in migration_text
    assert "unique" in migration_text
    assert "timestamp" in migration_text
    assert "device_id" in migration_text
    assert re.search(
        r"unique\s*\([^)]*[\"']?timestamp[\"']?[^)]*device_id",
        migration_text,
        re.DOTALL,
    ) or re.search(
        r"unique\s*\([^)]*device_id[^)]*[\"']?timestamp[\"']?",
        migration_text,
        re.DOTALL,
    )


def test_edge_function_upsert_still_conflicts_on_timestamp_device_id() -> None:
    function_path = Path(
        r"C:\Users\user\Documents\GitHub\Extrusion_data\supabase\functions\upload-metrics\index.ts"
    )

    if not function_path.exists():
        pytest.skip("Legacy Extrusion_data upload-metrics function is not available in this environment")
    source = function_path.read_text(encoding="utf-8")

    assert "upsert" in source
    assert re.search(
        r"onConflict\s*:\s*[\"']timestamp,\s*device_id[\"']",
        source,
    )


def test_supabase_reconciler_uses_chunk_rows_connect_timeout_and_statement_timeout(monkeypatch) -> None:
    calls: list[tuple[str, object]] = []
    matched_keys = {
        ("2026-06-01T09:00:00+09:00", "a"),
        ("2026-06-01T09:03:00+09:00", "a"),
    }

    class FakeCursor:
        def __init__(self, connection):
            self.connection = connection
            self.last_sql = ""

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, sql: str, params=None) -> None:
            self.last_sql = sql
            calls.append((sql, params))

        def executemany(self, sql: str, params) -> None:
            self.last_sql = sql
            batch = list(params)
            self.connection.staged.update(batch)
            calls.append((sql, batch))

        def fetchall(self):
            if "JOIN public.all_metrics" in self.last_sql:
                return sorted(self.connection.staged & matched_keys)
            return []

    class FakeConnection:
        def __init__(self):
            self.staged: set[tuple[str, str]] = set()

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def cursor(self):
            return FakeCursor(self)

    def fake_connect(db_url: str, **kwargs):
        calls.append(("connect", kwargs))
        assert db_url == "postgresql://local"
        return FakeConnection()

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))

    reconciler = SupabaseExactReconciler("postgresql://local")
    result = reconciler.find_existing_keys(
        {
            ("2026-06-01T09:00:00+09:00", "a"),
            ("2026-06-01T09:01:00+09:00", "a"),
            ("2026-06-01T09:02:00+09:00", "a"),
            ("2026-06-01T09:03:00+09:00", "a"),
            ("2026-06-01T09:04:00+09:00", "a"),
        },
        chunk_rows=2,
    )

    assert result == matched_keys
    connect_call = next(call for call in calls if call[0] == "connect")
    assert connect_call[1]["connect_timeout"] == 10
    assert connect_call[1]["autocommit"] is False
    query_calls = [sql for sql, _params in calls if "JOIN public.all_metrics" in sql]
    insert_calls = [sql for sql, _params in calls if "INSERT INTO preview_key_stage" in sql]
    timeout_calls = [sql for sql, _params in calls if "set_config('statement_timeout'" in sql]
    assert len(query_calls) == 1
    assert len(insert_calls) == 3
    assert len(timeout_calls) == 5
    assert reconciler.last_progress is not None
    assert reconciler.last_progress.strategy == "temp_table"
    assert reconciler.last_progress.batches_completed == 3
    assert reconciler.last_progress.keys_staged == 5
    assert reconciler.last_progress.matches_found == 2


def test_supabase_reconciler_checks_cancel_before_db_query(monkeypatch) -> None:
    def fake_connect(*_args, **_kwargs):
        raise AssertionError("connect should not be called after cancellation")

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))

    with pytest.raises(PreviewCancelledError):
        SupabaseExactReconciler("postgresql://local").find_existing_keys(
            {("2026-06-01T09:00:00+09:00", "a")},
            should_cancel=lambda: True,
        )


@pytest.mark.parametrize(
    ("existing_keys", "expected_keys"),
    [
        (set(), set()),
        (
            {("2026-06-01T09:00:00+09:00", "a"), ("2026-06-01T09:01:00+09:00", "a")},
            {("2026-06-01T09:00:00+09:00", "a"), ("2026-06-01T09:01:00+09:00", "a")},
        ),
        (
            {("2026-06-01T09:01:00+09:00", "a")},
            {("2026-06-01T09:01:00+09:00", "a")},
        ),
    ],
)
def test_supabase_reconciler_temp_table_match_shapes(monkeypatch, existing_keys, expected_keys) -> None:
    candidate_keys = {
        ("2026-06-01T09:00:00+09:00", "a"),
        ("2026-06-01T09:01:00+09:00", "a"),
    }

    class FakeCursor:
        def __init__(self, connection):
            self.connection = connection
            self.last_sql = ""

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, sql: str, params=None) -> None:
            self.last_sql = sql

        def executemany(self, _sql: str, params) -> None:
            self.connection.staged.update(params)

        def fetchall(self):
            if "JOIN public.all_metrics" in self.last_sql:
                return sorted(self.connection.staged & existing_keys)
            return []

    class FakeConnection:
        def __init__(self):
            self.staged: set[tuple[str, str]] = set()

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def cursor(self):
            return FakeCursor(self)

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=lambda *_args, **_kwargs: FakeConnection()))

    result = SupabaseExactReconciler("postgresql://local").find_existing_keys(candidate_keys, chunk_rows=1)

    assert result == expected_keys


def test_supabase_reconciler_classifies_connect_failure_as_unreachable(monkeypatch) -> None:
    def fail_connect(*_args, **_kwargs):
        raise OSError("connection refused")

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fail_connect))

    with pytest.raises(PreviewDbUnavailableError, match="connection refused"):
        SupabaseExactReconciler("postgresql://local").find_existing_keys(
            {("2026-06-01T09:00:00+09:00", "a")}
        )


def test_supabase_reconciler_classifies_post_connect_failure_as_query_failed(monkeypatch) -> None:
    class FailingCursor:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, *_args, **_kwargs) -> None:
            raise RuntimeError("permission denied for all_metrics")

    class ConnectedDatabase:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def cursor(self):
            return FailingCursor()

    monkeypatch.setitem(
        sys.modules,
        "psycopg",
        SimpleNamespace(connect=lambda *_args, **_kwargs: ConnectedDatabase()),
    )

    with pytest.raises(PreviewDbQueryError, match="permission denied"):
        SupabaseExactReconciler("postgresql://local").find_existing_keys(
            {("2026-06-01T09:00:00+09:00", "a")}
        )


def test_supabase_reconciler_classifies_cursor_acquisition_failure_as_query_failed(
    monkeypatch,
) -> None:
    class ConnectedDatabase:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def cursor(self):
            raise RuntimeError("cursor allocation failed")

    monkeypatch.setitem(
        sys.modules,
        "psycopg",
        SimpleNamespace(connect=lambda *_args, **_kwargs: ConnectedDatabase()),
    )

    with pytest.raises(PreviewDbQueryError, match="cursor allocation failed"):
        SupabaseExactReconciler("postgresql://local").find_existing_keys(
            {("2026-06-01T09:00:00+09:00", "a")}
        )


def test_supabase_reconciler_stages_large_synthetic_key_set_in_bounded_batches(
    monkeypatch,
) -> None:
    staged_rows = 0
    batch_sizes: list[int] = []
    join_count = 0
    connect_count = 0

    class TrackingCursor:
        def __init__(self) -> None:
            self.last_sql = ""

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, sql: str, _params=None) -> None:
            nonlocal join_count
            self.last_sql = sql
            if "JOIN public.all_metrics" in sql:
                join_count += 1

        def executemany(self, _sql: str, params) -> None:
            nonlocal staged_rows
            batch = list(params)
            staged_rows += len(batch)
            batch_sizes.append(len(batch))

        def fetchall(self):
            return []

    class TrackingConnection:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def cursor(self):
            return TrackingCursor()

    def connect(*_args, **_kwargs):
        nonlocal connect_count
        connect_count += 1
        return TrackingConnection()

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=connect))
    keys = {
        (f"2026-06-05T{offset // 3600:02d}:{(offset // 60) % 60:02d}:{offset % 60:02d}+09:00", "a")
        for offset in range(25_000)
    }

    reconciler = SupabaseExactReconciler("postgresql://local")
    result = reconciler.find_existing_keys(keys, chunk_rows=4096)

    assert result == set()
    assert connect_count == 1
    assert join_count == 1
    assert staged_rows == 25_000
    assert batch_sizes == [4096, 4096, 4096, 4096, 4096, 4096, 424]
    assert reconciler.last_progress is not None
    assert reconciler.last_progress.batches_completed == 7
    assert reconciler.last_progress.keys_staged == 25_000
