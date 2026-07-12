from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from fastapi.testclient import TestClient

import backend.app.api.runtime as runtime_api
import backend.app.api.upload_preview as upload_preview_api
from backend.app.api.audit import get_audit_repository
from backend.app.api.config import get_config_audit_repository
from backend.app.api.runtime import get_command_runner
from backend.app.api.upload_preview import get_preview_audit_repository, get_preview_repository
from backend.app.core.settings import Settings, get_settings
from backend.app.db.audit_repository import AuditRepository
from backend.app.db.preview_repository import PreviewRepository
from backend.app.main import app
from backend.app.schemas.upload_preview import PreviewDbStatus, PreviewRunStatus
from tests.backend.test_runtime_control import (
    FakeRunner,
    install_synthetic_runtime_network_probes,
    write_supabase_config,
)


def approval_scope(
    *,
    range_mode: str,
    start_date: str | None = None,
    end_date: str | None = None,
    source_class: str = "drive_letter",
    applied_profile: str = "large_source_operational",
) -> dict[str, object]:
    return {
        "expectedSourceClasses": {"plc": source_class},
        "expectedRangeMode": range_mode,
        "expectedStartDate": start_date,
        "expectedEndDate": end_date,
        "expectedAppliedProfile": applied_profile,
    }


def test_audit_api_surfaces_representative_failure_and_blocked_paths(
    tmp_path: Path,
    monkeypatch,
) -> None:
    install_synthetic_runtime_network_probes(monkeypatch)
    state_db = tmp_path / "state.db"
    config_path = tmp_path / "config.json"
    plc_dir = tmp_path / "plc"
    plc_dir.mkdir()
    csv_path = plc_dir / "Factory_Integrated_Log_20260606_090000.csv"
    csv_path.write_text(
        "Date,Time,Mold1\n2026-06-06,09:00:00,1\n",
        encoding="utf-8",
    )
    old_mtime = datetime.now().timestamp() - 600
    os.utime(csv_path, (old_mtime, old_mtime))
    project_path = tmp_path / "Extrusion_web_console"
    write_supabase_config(project_path)
    settings = Settings(
        state_db_path=str(state_db),
        config_file_path=str(config_path),
        plc_data_dir=str(plc_dir),
        supabase_db_url="",
        local_supabase_project_path=str(project_path),
        local_supabase_wsl_path="/mnt/c/synthetic/Extrusion_web_console",
        runtime_readiness_timeout_seconds=1,
    )
    preview_repository = PreviewRepository(str(state_db))
    audit_repository = AuditRepository(str(state_db))
    fake_runner = FakeRunner(docker_ps_output="")

    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_preview_repository] = lambda: preview_repository
    app.dependency_overrides[get_preview_audit_repository] = lambda: audit_repository
    app.dependency_overrides[get_config_audit_repository] = lambda: audit_repository
    app.dependency_overrides[get_audit_repository] = lambda: audit_repository
    app.dependency_overrides[get_command_runner] = lambda: fake_runner
    monkeypatch.setattr(upload_preview_api.executor, "submit", lambda fn, *args: fn(*args))
    monkeypatch.setattr(runtime_api.executor, "submit", lambda fn, *args: fn(*args))
    client = TestClient(app)

    try:
        malformed_preview = client.post(
            "/api/upload/preview",
            content=b'{"rangeMode": ',
            headers={"Content-Type": "application/json"},
        )
        invalid_settings = client.put(
            "/api/config",
            json={"values": {"localSupabaseApiPort": 70_000}},
        )
        runtime_blocked = client.post("/api/runtime/local-supabase/start")

        preview_repository.create_run(
            preview_run_id="prv_active_audit",
            range_mode="today",
            start_date=None,
            end_date=None,
            sources=["plc"],
            options={},
            config_snapshot={},
            retry_of_run_id=None,
        )
        active_conflict = client.post(
            "/api/upload/preview",
            json={
                "rangeMode": "today",
                "sources": ["plc"],
                "approvalScope": approval_scope(range_mode="today"),
            },
        )
        preview_repository.recompute_summary(
            "prv_active_audit",
            status=PreviewRunStatus.failed,
            db_status=PreviewDbStatus.not_checked,
            error_code="synthetic_test_cleanup",
            error_message="Synthetic active-run fixture completed.",
        )

        db_unreachable = client.post(
            "/api/upload/preview",
            json={
                "rangeMode": "custom",
                "startDate": "2026-06-06",
                "endDate": "2026-06-06",
                "sources": ["plc"],
                "options": {"stableLagMinutes": 0},
                "approvalScope": approval_scope(
                    range_mode="custom",
                    start_date="2026-06-06",
                    end_date="2026-06-06",
                ),
            },
        )
        preview_detail = client.get(db_unreachable.json()["pollUrl"])
        failures = client.get("/api/audit?result=failure&limit=200")
        blocked = client.get("/api/audit?result=blocked&limit=200")
    finally:
        app.dependency_overrides.clear()

    assert malformed_preview.status_code == 422
    assert invalid_settings.status_code == 422
    assert runtime_blocked.status_code == 202
    assert active_conflict.status_code == 409
    assert db_unreachable.status_code == 202
    assert preview_detail.status_code == 200
    assert preview_detail.json()["run"]["status"] == "partial_failed"
    assert preview_detail.json()["run"]["dbStatus"] == "unreachable"
    assert fake_runner.commands
    assert ("supabase", "start") not in fake_runner.commands

    assert failures.status_code == 200
    assert blocked.status_code == 200
    failure_codes = {item["errorCode"] for item in failures.json()["items"]}
    blocked_codes = {item["errorCode"] for item in blocked.json()["items"]}
    assert {
        "preview_request_json_invalid",
        "config_validation_failed",
        "db_unreachable",
    }.issubset(failure_codes)
    assert {"required_container_missing", "active_preview_run"}.issubset(blocked_codes)

    serialized_audit = failures.text + blocked.text
    assert str(csv_path) not in serialized_audit
    assert csv_path.name not in serialized_audit
    assert "postgresql://" not in serialized_audit
    assert "secret-token" not in serialized_audit
