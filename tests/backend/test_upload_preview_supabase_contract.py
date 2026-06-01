from __future__ import annotations

import re
from pathlib import Path


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

    assert migration_dir.exists(), "Expected copied Supabase migrations under supabase/migrations"
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

    assert function_path.exists(), (
        "Expected copied upload-metrics Edge Function under "
        "supabase/functions/upload-metrics/index.ts"
    )
    source = function_path.read_text(encoding="utf-8")

    assert "upsert" in source
    assert re.search(
        r"onConflict\s*:\s*[\"']timestamp,\s*device_id[\"']",
        source,
    )
