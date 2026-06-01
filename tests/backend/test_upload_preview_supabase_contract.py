from __future__ import annotations

import re
import sys
from types import SimpleNamespace
from pathlib import Path

import pytest

from backend.app.services.upload_preview import PreviewCancelledError, SupabaseExactReconciler


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_supabase_reconciliation_repository_uses_exact_composite_key_join() -> None:
    source_path = REPO_ROOT / "backend" / "app" / "services" / "upload_preview.py"

    assert source_path.exists(), (
        "Expected SupabaseExactReconciler in backend/app/services/upload_preview.py"
    )
    source = source_path.read_text(encoding="utf-8")
    source_lower = source.lower()

    assert "public.all_metrics" in source
    assert "device_id" in source
    assert "timestamp" in source_lower
    assert re.search(r"\bvalues\b", source, re.IGNORECASE), (
        "Preview DB matching should batch exact candidate keys with VALUES"
    )
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

    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, sql: str, params=None) -> None:
            calls.append((sql, params))

        def fetchall(self):
            return []

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def cursor(self):
            return FakeCursor()

    def fake_connect(db_url: str, **kwargs):
        calls.append(("connect", kwargs))
        assert db_url == "postgresql://local"
        return FakeConnection()

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))

    SupabaseExactReconciler("postgresql://local").find_existing_keys(
        {
            ("2026-06-01T09:00:00+09:00", "a"),
            ("2026-06-01T09:01:00+09:00", "a"),
            ("2026-06-01T09:02:00+09:00", "a"),
            ("2026-06-01T09:03:00+09:00", "a"),
            ("2026-06-01T09:04:00+09:00", "a"),
        },
        chunk_rows=2,
    )

    connect_call = next(call for call in calls if call[0] == "connect")
    assert connect_call[1]["connect_timeout"] == 10
    query_calls = [sql for sql, _params in calls if "JOIN public.all_metrics" in sql]
    timeout_calls = [sql for sql, _params in calls if "set_config('statement_timeout'" in sql]
    assert len(query_calls) == 3
    assert len(timeout_calls) == 3


def test_supabase_reconciler_checks_cancel_before_db_query(monkeypatch) -> None:
    def fake_connect(*_args, **_kwargs):
        raise AssertionError("connect should not be called after cancellation")

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))

    with pytest.raises(PreviewCancelledError):
        SupabaseExactReconciler("postgresql://local").find_existing_keys(
            {("2026-06-01T09:00:00+09:00", "a")},
            should_cancel=lambda: True,
        )
