from pathlib import Path


def test_upload_metrics_deduplicates_records_before_upsert_batching() -> None:
    source = Path("supabase/functions/upload-metrics/index.ts").read_text(encoding="utf-8")

    dedupe_call = "const deduplicated = deduplicateMetricsByKey(cleaned);"
    upsert_split_call = "const upsertBatches = splitIntoUpsertBatches("
    assert "function deduplicateMetricsByKey" in source
    assert "function metricConflictKey" in source
    assert source.index(dedupe_call) < source.index(upsert_split_call)
    assert "deduplicated: cleaned.length - deduplicated.length" in source
