import logging
from pathlib import Path

from backend.app import main as app_main
from backend.app.core.settings import Settings


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
    assert "delete_expansion_enabled=False" in messages
    assert "date_scoped_delete_ui_enabled=True" in messages
    assert "lan_access_enabled=False" in messages
    assert "row_attribution_enabled=True" in messages
    assert "db_delta_evidence_required=True" in messages
    assert "secret-value" not in messages
    assert str(tmp_path) not in messages
