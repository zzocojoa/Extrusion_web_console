import logging
from pathlib import Path

from backend.app import main as app_main
from backend.app.core.settings import Settings
from backend.app.db.upload_job_repository import UploadJobRepository
from tests.backend.test_upload_jobs_repository_contract import PREVIEW_GATE_SNAPSHOT, create_preview_with_items


def test_create_app_logs_safe_v2_feature_gate_snapshot(tmp_path: Path, monkeypatch, caplog) -> None:
    settings = Settings(
        state_db_path=str(tmp_path / "state.db"),
        config_file_path=str(tmp_path / "config.json"),
        local_token_mode="dev-disabled",
        row_attribution_hmac_key="secret-value",
        v2_delete_expansion_enabled=False,
        v2_date_scoped_delete_ui_enabled=True,
        v2_lan_access_enabled=False,
        v2_row_attribution_enabled=True,
        v2_db_delta_evidence_required=True,
    )
    monkeypatch.setattr(app_main, "get_settings", lambda: settings)
    caplog.set_level(logging.INFO, logger=app_main.__name__)

    app_main.create_app()

    messages = "\n".join(record.getMessage() for record in caplog.records if record.name == app_main.__name__)
    assert "V2 feature gate snapshot:" in messages
    assert "delete_expansion_requested_enabled=False" in messages
    assert "delete_expansion_effective_enabled=False" in messages
    assert "date_scoped_delete_ui_requested_enabled=True" in messages
    assert "date_scoped_delete_ui_effective_enabled=False" in messages
    assert "date_scoped_delete_ui_review_shell_visible=True" in messages
    assert "lan_access_requested_enabled=False" in messages
    assert "lan_access_effective_enabled=False" in messages
    assert "row_attribution_enabled=True" in messages
    assert "db_delta_evidence_required=True" in messages
    assert "secret-value" not in messages
    assert str(tmp_path) not in messages


def test_create_app_recovers_interrupted_upload_with_resume_offset(tmp_path: Path, monkeypatch, caplog) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    repository.create_job_from_preview(
        job_id="upl_restart",
        preview_run_id="prv_done",
        expected_target_rows=2,
        expected_target_files=1,
        options={},
        config_snapshot={},
        preview_gate_snapshot=PREVIEW_GATE_SNAPSHOT,
    )
    repository.start_job("upl_restart")
    file_id = str(repository.list_job_files("upl_restart")[0]["job_file_id"])
    repository.mark_file_running(file_id)
    repository.update_file_progress(
        file_id,
        processed_rows=1,
        uploaded_rows=1,
        inserted_rows=1,
        row_count=2,
        resume_offset=1,
    )
    settings = Settings(
        state_db_path=str(db_path),
        config_file_path=str(tmp_path / "config.json"),
        local_token_mode="dev-disabled",
    )
    monkeypatch.setattr(app_main, "get_settings", lambda: settings)
    caplog.set_level(logging.INFO, logger=app_main.__name__)

    app_main.create_app()

    recovered_job = repository.get_job("upl_restart")
    recovered_file = repository.get_job_file(file_id)
    retry = repository.create_retry_job(
        job_id="upl_restart_retry",
        source_job_id="upl_restart",
        include_interrupted=True,
        include_cancelled=False,
        expected_remaining_rows=1,
        expected_retry_files=1,
        options={},
        config_snapshot={},
    )
    messages = "\n".join(record.getMessage() for record in caplog.records if record.name == app_main.__name__)

    assert recovered_job is not None and recovered_job["status"] == "interrupted"
    assert recovered_file is not None and recovered_file["status"] == "interrupted"
    assert recovered_file["resume_offset"] == 1
    assert retry.created is True
    assert repository.list_job_files("upl_restart_retry")[0]["resume_offset"] == 1
    assert "Startup interruption recovery:" in messages
    assert "upload_jobs=1" in messages
    assert "total=1" in messages
    assert str(tmp_path) not in messages
