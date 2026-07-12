from __future__ import annotations

import csv
import json
import os
import time
import tracemalloc
from datetime import datetime, timedelta
from pathlib import Path

from backend.app.core.settings import Settings
from backend.app.db.audit_repository import AuditLogFilters, AuditRepository
from backend.app.db.preview_repository import PreviewRepository
from backend.app.schemas.upload_preview import PreviewCreateRequest
from backend.app.services.upload_preview import PreviewService


SYNTHETIC_ROW_COUNT = 25_000


class SoakReconciler:
    def __init__(self) -> None:
        self.key_count = 0
        self.chunk_rows = 0

    def find_existing_keys(
        self,
        keys: set[tuple[str, str]],
        *,
        chunk_rows: int,
        **_kwargs,
    ) -> set[tuple[str, str]]:
        self.key_count = len(keys)
        self.chunk_rows = chunk_rows
        return set()


def write_large_integrated_fixture(path: Path) -> None:
    started_at = datetime(2026, 6, 5, 0, 0, 0)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Date", "Time", "Mold1", "Temperature"])
        for offset in range(SYNTHETIC_ROW_COUNT):
            timestamp = started_at + timedelta(seconds=offset)
            writer.writerow(
                [
                    timestamp.strftime("%Y-%m-%d"),
                    timestamp.strftime("%H:%M:%S"),
                    offset % 100,
                    450 + (offset % 20),
                ]
            )
    old_mtime = datetime.now().timestamp() - 600
    os.utime(path, (old_mtime, old_mtime))


def test_synthetic_large_csv_preview_soak_is_bounded_and_db_checkable(tmp_path: Path) -> None:
    plc_dir = tmp_path / "plc"
    plc_dir.mkdir()
    csv_path = plc_dir / "Factory_Integrated_Log_20260605_000000.csv"
    write_large_integrated_fixture(csv_path)
    state_db = tmp_path / "state.db"
    repository = PreviewRepository(str(state_db))
    audit_repository = AuditRepository(str(state_db))
    reconciler = SoakReconciler()
    request = PreviewCreateRequest.model_validate(
        {
            "rangeMode": "custom",
            "startDate": "2026-06-05",
            "endDate": "2026-06-05",
            "sources": ["plc"],
            "options": {
                "stableLagMinutes": 0,
                "sampleRows": 200,
                "chunkRows": 4096,
                "maxFileSeconds": 30,
                "maxRunSeconds": 60,
            },
        }
    )
    repository.create_run(
        preview_run_id="prv_large_synthetic",
        range_mode=request.range_mode.value,
        start_date="2026-06-05",
        end_date="2026-06-05",
        sources=["plc"],
        options=request.options.model_dump(by_alias=True),
        config_snapshot={"sourceClass": "synthetic_test_fixture"},
        retry_of_run_id=None,
    )
    service = PreviewService(
        Settings(plc_data_dir=str(plc_dir), state_db_path=str(state_db)),
        repository,
        reconciler=reconciler,
        audit_repository=audit_repository,
    )

    tracemalloc.start()
    started = time.monotonic()
    try:
        service.run_preview("prv_large_synthetic", request)
        elapsed_seconds = time.monotonic() - started
        _, peak_bytes = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    run = repository.get_run("prv_large_synthetic")
    items, total = repository.list_items("prv_large_synthetic")
    assert run is not None
    assert run["status"] == "succeeded"
    assert run["db_status"] == "reachable"
    assert run["target_count"] == 1
    assert run["upload_row_estimate"] == SYNTHETIC_ROW_COUNT
    assert total == 1
    assert items[0]["status"] == "target"
    assert items[0]["row_count"] == SYNTHETIC_ROW_COUNT
    assert items[0]["local_key_count"] == SYNTHETIC_ROW_COUNT
    assert reconciler.key_count == SYNTHETIC_ROW_COUNT
    assert reconciler.chunk_rows == 4096
    assert elapsed_seconds < 30
    assert peak_bytes < 96 * 1024 * 1024

    audit = audit_repository.list_audit_logs(AuditLogFilters(action="upload.preview")).rows[0]
    assert audit["result"] == "success"
    assert str(csv_path) not in audit["params_json_redacted"]
    assert csv_path.name not in audit["params_json_redacted"]
    params = json.loads(audit["params_json_redacted"])
    assert params["candidateCount"] == 1
    assert params["targetCount"] == 1
    assert params["dbStatus"] == "reachable"
