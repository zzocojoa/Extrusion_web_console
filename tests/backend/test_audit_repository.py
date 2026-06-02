import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

from backend.app.db.audit_repository import AuditLogFilters, AuditRepository
from backend.app.db.runtime_repository import RuntimeRepository
from backend.app.db.upload_job_repository import UploadJobRepository
from backend.app.schemas.audit import AuditOrder, AuditResult, AuditSort


def test_audit_repository_bootstrap_installs_append_only_triggers(tmp_path: Path) -> None:
    repository = AuditRepository(tmp_path / "state.db")
    audit_id = repository.insert_audit(
        action="upload.start",
        target_type="upload_job",
        target_id="upl_1",
        params={},
        result=AuditResult.success,
    )

    with repository.connect() as connection:
        with pytest.raises(sqlite3.IntegrityError, match="audit_log_append_only"):
            connection.execute("UPDATE audit_log SET action = 'changed' WHERE audit_id = ?", (audit_id,))

    with repository.connect() as connection:
        with pytest.raises(sqlite3.IntegrityError, match="audit_log_append_only"):
            connection.execute("DELETE FROM audit_log WHERE audit_id = ?", (audit_id,))


def test_existing_upload_and_runtime_audit_inserts_pass_with_triggers(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    AuditRepository(db_path)
    upload_repository = UploadJobRepository(db_path)
    runtime_repository = RuntimeRepository(db_path)

    upload_repository.append_audit(
        action="upload.start",
        target_type="upload_job",
        target_id="upl_1",
        params={"token": "secret-token", "mode": "preview_targets"},
        result="blocked",
        error_code="upload_config_missing",
        error_message="Upload config is missing",
        job_id="upl_1",
    )
    runtime_repository.append_audit(
        action="runtime.start",
        target_type="local_supabase",
        target_id="Extrusion_data",
        params={"operationId": "run_1"},
        result="success",
    )

    audit_repository = AuditRepository(db_path)
    result = audit_repository.list_audit_logs(AuditLogFilters(limit=10))

    assert result.total_items == 2
    assert [row["action"] for row in result.rows] == ["runtime.start", "upload.start"]


def test_audit_repository_filters_sorts_and_paginates_without_searching_params(tmp_path: Path) -> None:
    repository = AuditRepository(tmp_path / "state.db")
    repository.insert_audit(
        action="upload.start",
        target_type="upload_job",
        target_id="upl_1",
        params={"hidden": "needle"},
        result=AuditResult.blocked,
        error_code="active_upload_job",
        job_id="upl_1",
    )
    repository.insert_audit(
        action="runtime.stop",
        target_type="local_supabase",
        target_id="Extrusion_data",
        params={},
        result=AuditResult.failure,
        error_code="docker_unavailable",
        error_message="Docker unavailable",
    )
    repository.insert_audit(
        action="runtime.start",
        target_type="local_supabase",
        target_id="Extrusion_data",
        params={},
        result=AuditResult.success,
    )

    failure_page = repository.list_audit_logs(
        AuditLogFilters(result=AuditResult.failure, limit=1, sort=AuditSort.action, order=AuditOrder.asc)
    )
    assert failure_page.total_items == 1
    assert failure_page.rows[0]["action"] == "runtime.stop"

    paged = repository.list_audit_logs(AuditLogFilters(limit=2, offset=1))
    assert paged.total_items == 3
    assert len(paged.rows) == 2

    params_search = repository.list_audit_logs(AuditLogFilters(q="needle"))
    assert params_search.total_items == 0

    scalar_search = repository.list_audit_logs(AuditLogFilters(q="docker"))
    assert scalar_search.total_items == 1
    assert scalar_search.rows[0]["error_code"] == "docker_unavailable"


def test_audit_repository_q_search_does_not_match_raw_error_message_secrets(tmp_path: Path) -> None:
    repository = AuditRepository(tmp_path / "state.db")
    with repository.connect() as connection:
        connection.execute(
            """
            INSERT INTO audit_log(
              ts, actor, action, target_type, target_id, params_json_redacted,
              result, error_code, error_message, job_id, request_id, created_at
            )
            VALUES (
              '2026-01-01T00:00:00+00:00', 'local_operator', 'upload.failed',
              'upload_job', 'upl_secret', '{}', 'failure', 'edge_call_failed',
              'Authorization: Bearer secret-token', 'upl_secret', 'req_secret',
              '2026-01-01T00:00:00+00:00'
            )
            """
        )

    secret_search = repository.list_audit_logs(AuditLogFilters(q="secret-token"))
    assert secret_search.total_items == 0

    assert repository.list_audit_logs(AuditLogFilters(q="edge_call_failed")).total_items == 1
    assert repository.list_audit_logs(AuditLogFilters(q="upload.failed")).total_items == 1
    assert repository.list_audit_logs(AuditLogFilters(q="upl_secret")).total_items == 1
    assert repository.list_audit_logs(AuditLogFilters(q="req_secret")).total_items == 1
    assert repository.list_audit_logs(AuditLogFilters(q="failure")).total_items == 1
    assert repository.list_audit_logs(AuditLogFilters(q="local_operator")).total_items == 1


def test_audit_repository_filters_by_timestamp_range(tmp_path: Path) -> None:
    repository = AuditRepository(tmp_path / "state.db")
    with repository.connect() as connection:
        connection.executemany(
            """
            INSERT INTO audit_log(
              ts, actor, action, target_type, target_id, params_json_redacted,
              result, error_code, error_message, job_id, request_id, created_at
            )
            VALUES (?, 'local_operator', ?, 'upload_job', NULL, '{}', 'success', NULL, NULL, NULL, NULL, ?)
            """,
            [
                ("2026-01-01T00:00:00+00:00", "upload.start", "2026-01-01T00:00:00+00:00"),
                ("2026-01-02T00:00:00+00:00", "upload.retry", "2026-01-02T00:00:00+00:00"),
                ("2026-01-03T00:00:00+00:00", "upload.cancel", "2026-01-03T00:00:00+00:00"),
            ],
        )

    result = repository.list_audit_logs(
        AuditLogFilters(
            from_ts=datetime(2026, 1, 2, tzinfo=timezone.utc),
            to_ts=datetime(2026, 1, 2, 23, 59, 59, tzinfo=timezone.utc),
        )
    )

    assert result.total_items == 1
    assert result.rows[0]["action"] == "upload.retry"


def test_audit_repository_decodes_invalid_params_as_empty_object(tmp_path: Path) -> None:
    repository = AuditRepository(tmp_path / "state.db")
    with repository.connect() as connection:
        connection.execute(
            """
            INSERT INTO audit_log(
              ts, actor, action, target_type, target_id, params_json_redacted,
              result, error_code, error_message, job_id, request_id, created_at
            )
            VALUES (
              '2026-01-01T00:00:00+00:00', 'local_operator', 'upload.failed',
              'upload_job', 'upl_1', '{not-json', 'failure', NULL, NULL, 'upl_1', NULL,
              '2026-01-01T00:00:00+00:00'
            )
            """
        )

    row = repository.list_audit_logs(AuditLogFilters()).rows[0]
    from backend.app.db.audit_repository import decode_params_json

    assert decode_params_json(row["params_json_redacted"]) == {}
