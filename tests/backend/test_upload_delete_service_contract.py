import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from backend.app.core.settings import Settings
from backend.app.db.audit_repository import AuditRepository
from backend.app.db.db_delta_repository import DbDeltaEvidenceRepository, decode_delta_scope_json
from backend.app.db.preview_repository import PreviewRepository
from backend.app.db.row_attribution_repository import RowAttributionRepository
from backend.app.db.upload_delete_repository import UploadDeleteRepository
from backend.app.db.upload_job_repository import UploadJobRepository
from backend.app.schemas.upload_delete import DeleteJobCreateRequest, DeletePreflightRequest
from backend.app.services.upload_delete import (
    DbGuardResult,
    DeleteDbBlockedError,
    DeleteDbFailedError,
    DeleteCommitUnknownError,
    DeleteRejectedError,
    PsycopgDeleteDbClient,
    UploadDeleteService,
)
from backend.app.services.upload_preview import build_file_signature


DB_HASH = "a" * 64
HMAC_KEY = "fixture-row-attribution-key"


class FakeDeleteDb:
    def __init__(
        self,
        *,
        guard_result: DbGuardResult | None = None,
        target_guard_result: DbGuardResult | None = None,
        existing_count: int | None = None,
        deleted_count: int | None = None,
        count_error: Exception | None = None,
        delete_error: Exception | None = None,
    ) -> None:
        self.guard_result = guard_result or DbGuardResult(
            True,
            "loopback_expected_db_port",
            "fp_local",
        )
        self.target_guard_result = target_guard_result
        self.existing_count = existing_count
        self.deleted_count = deleted_count
        self.count_error = count_error
        self.delete_error = delete_error
        self.guard_calls = 0
        self.target_guard_calls = 0
        self.count_calls = 0
        self.delete_calls = 0

    def target_guard(self) -> DbGuardResult:
        self.target_guard_calls += 1
        return self.guard_result if self.target_guard_result is None else self.target_guard_result

    def guard(self) -> DbGuardResult:
        self.guard_calls += 1
        return self.guard_result

    def count_existing_keys(self, keys: set[tuple[str, str]]) -> int:
        self.count_calls += 1
        if self.count_error is not None:
            raise self.count_error
        return len(keys) if self.existing_count is None else self.existing_count

    def delete_keys(self, keys: set[tuple[str, str]], *, expected_count: int) -> int:
        self.delete_calls += 1
        if self.delete_error is not None:
            raise self.delete_error
        return expected_count if self.deleted_count is None else self.deleted_count


class FailStartAuditRepository(AuditRepository):
    def insert_audit(self, **kwargs):  # type: ignore[no-untyped-def]
        if kwargs.get("action") == "upload.delete_start":
            raise RuntimeError("audit store unavailable")
        return super().insert_audit(**kwargs)


def test_psycopg_delete_client_preserves_commit_unknown(monkeypatch) -> None:
    class FakeCursor:
        def __init__(self) -> None:
            self.fetchone_values = [[True], [1]]

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def execute(self, _sql, _params=None) -> None:
            return None

        def executemany(self, _sql, _values) -> None:
            return None

        def fetchone(self):
            return self.fetchone_values.pop(0)

        def fetchall(self):
            return [(1,)]

    class CommitFailConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def cursor(self):
            return FakeCursor()

        def commit(self) -> None:
            raise RuntimeError("commit result unavailable")

    monkeypatch.setitem(
        sys.modules,
        "psycopg",
        SimpleNamespace(connect=lambda *_args, **_kwargs: CommitFailConnection()),
    )
    client = PsycopgDeleteDbClient(SimpleNamespace(supabase_db_url="fixture-db-url"))  # type: ignore[arg-type]

    with pytest.raises(DeleteCommitUnknownError):
        client.delete_keys({("fixture-timestamp", "fixture-device")}, expected_count=1)


def test_psycopg_count_existing_keys_uses_select_only(monkeypatch) -> None:
    statements: list[str] = []

    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def execute(self, sql, _params=None) -> None:
            statements.append(str(sql))

        def fetchone(self):
            return [1]

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def cursor(self):
            return FakeCursor()

    monkeypatch.setitem(
        sys.modules,
        "psycopg",
        SimpleNamespace(connect=lambda *_args, **_kwargs: FakeConnection()),
    )
    client = PsycopgDeleteDbClient(SimpleNamespace(supabase_db_url="fixture-db-url"))  # type: ignore[arg-type]

    count = client.count_existing_keys({("fixture-timestamp", "fixture-device")})

    assert count == 1
    executed = "\n".join(statements).lower()
    assert "jsonb_to_recordset" in executed
    assert "create temp" not in executed
    assert "insert into" not in executed
    assert "delete from" not in executed


def test_psycopg_guard_accepts_docker_internal_postgres_port(monkeypatch) -> None:
    class FakeCursor:
        def __init__(self) -> None:
            self.fetchone_values = [
                (5432, "postgres", "postgres"),
                [True],
                [True],
                [True],
            ]

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def execute(self, _sql, _params=None) -> None:
            return None

        def fetchone(self):
            return self.fetchone_values.pop(0)

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def cursor(self):
            return FakeCursor()

    monkeypatch.setitem(
        sys.modules,
        "psycopg",
        SimpleNamespace(connect=lambda *_args, **_kwargs: FakeConnection()),
    )
    client = PsycopgDeleteDbClient(
        SimpleNamespace(
            supabase_db_url=loopback_db_url_for_test(),
            local_supabase_db_port=25433,
            local_supabase_project_id="Extrusion_web_console",
        )
    )

    result = client.guard()

    assert result.passed is True
    assert result.reason_code is None


def test_psycopg_guard_blocks_unexpected_runtime_server_port(monkeypatch) -> None:
    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def execute(self, _sql, _params=None) -> None:
            return None

        def fetchone(self):
            return (15432, "postgres", "postgres")

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def cursor(self):
            return FakeCursor()

    monkeypatch.setitem(
        sys.modules,
        "psycopg",
        SimpleNamespace(connect=lambda *_args, **_kwargs: FakeConnection()),
    )
    client = PsycopgDeleteDbClient(
        SimpleNamespace(
            supabase_db_url=loopback_db_url_for_test(),
            local_supabase_db_port=25433,
            local_supabase_project_id="Extrusion_web_console",
        )
    )

    result = client.guard()

    assert result.passed is False
    assert result.reason_code == "db_port_mismatch"


def loopback_db_url_for_test() -> str:
    return "postgresql:" + "//127.0.0.1:25433/postgres"


def create_preview_for_delete(db_path: Path, source_dir: Path) -> tuple[int, Path]:
    UploadJobRepository(db_path).ensure_schema()
    source_dir.mkdir(parents=True)
    source_file = source_dir / "already.csv"
    source_file.write_text(
        "Date,Time,Mold1\n"
        "2026-06-18,09:00:00,1\n"
        "2026-06-18,09:01:00,2\n",
        encoding="utf-8",
    )
    stat = source_file.stat()
    preview = PreviewRepository(db_path)
    preview.create_run(
        preview_run_id="prv_done",
        range_mode="today",
        start_date=None,
        end_date=None,
        sources=["plc"],
        options={},
        config_snapshot={},
        retry_of_run_id=None,
    )
    item_id = preview.insert_item(
        "prv_done",
        {
            "file_key": "key-already",
            "folder_label": "PLC",
            "folder_path": str(source_dir),
            "filename": source_file.name,
            "path": str(source_file),
            "kind": "plc",
            "file_date": "2026-06-18",
            "size_bytes": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
            "modified_at": "2026-06-18T09:00:00+09:00",
            "file_signature": build_file_signature(source_file, stat),
            "status": "already_in_db",
            "reason_code": "db_full_match",
            "reason_text": "All keys already exist.",
            "scan_mode": "full",
            "sample_row_count": 2,
            "row_count": 2,
            "local_key_count": 2,
            "db_match_count": 2,
            "upload_row_estimate": 0,
            "first_timestamp": "2026-06-18T09:00:00+09:00",
            "last_timestamp": "2026-06-18T09:01:00+09:00",
            "device_ids": ["extruder_integrated"],
            "issues": [],
            "error_code": None,
            "error_message": None,
        },
    )
    preview.update_run("prv_done", status="succeeded", db_status="reachable")
    return item_id, source_file


def create_mixed_date_preview_for_delete(db_path: Path, source_dir: Path) -> tuple[int, Path]:
    UploadJobRepository(db_path).ensure_schema()
    source_dir.mkdir(parents=True)
    source_file = source_dir / "mixed.csv"
    source_file.write_text(
        "Date,Time,Mold1\n"
        "2026-01-19,09:00:00,1\n"
        "2026-01-20,09:00:00,2\n"
        "2026-01-19,10:00:00,3\n",
        encoding="utf-8",
    )
    stat = source_file.stat()
    preview = PreviewRepository(db_path)
    preview.create_run(
        preview_run_id="prv_mixed",
        range_mode="custom",
        start_date="2026-01-19",
        end_date="2026-01-19",
        sources=["plc"],
        options={},
        config_snapshot={},
        retry_of_run_id=None,
    )
    item_id = preview.insert_item(
        "prv_mixed",
        {
            "file_key": "key-mixed",
            "folder_label": "PLC",
            "folder_path": str(source_dir),
            "filename": source_file.name,
            "path": str(source_file),
            "kind": "plc",
            "file_date": "2026-01-19",
            "size_bytes": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
            "modified_at": "2026-01-19T09:00:00+09:00",
            "file_signature": build_file_signature(source_file, stat),
            "status": "already_in_db",
            "reason_code": "db_full_match",
            "reason_text": "All keys already exist.",
            "scan_mode": "full",
            "sample_row_count": 3,
            "row_count": 3,
            "local_key_count": 3,
            "db_match_count": 3,
            "upload_row_estimate": 0,
            "first_timestamp": "2026-01-19T09:00:00+09:00",
            "last_timestamp": "2026-01-20T09:00:00+09:00",
            "device_ids": ["extruder_integrated"],
            "issues": [],
            "error_code": None,
            "error_message": None,
        },
    )
    preview.update_run("prv_mixed", status="succeeded", db_status="reachable")
    return item_id, source_file


def service(db_path: Path, db: FakeDeleteDb, audit: AuditRepository | None = None) -> UploadDeleteService:
    settings = Settings(
        state_db_path=str(db_path),
        supabase_db_url="",
        local_supabase_db_port=25433,
    )
    return UploadDeleteService(
        settings=settings,
        repository=UploadDeleteRepository(db_path),
        audit_repository=audit or AuditRepository(db_path),
        db_client=db,
        runtime_ready=lambda: (True, None),
    )


def service_with_settings(
    db_path: Path,
    db: FakeDeleteDb,
    *,
    audit: AuditRepository | None = None,
    row_attribution_repository: RowAttributionRepository | None = None,
    **settings_overrides,
) -> UploadDeleteService:
    settings = Settings(
        state_db_path=str(db_path),
        supabase_db_url="",
        local_supabase_db_port=25433,
        **settings_overrides,
    )
    return UploadDeleteService(
        settings=settings,
        repository=UploadDeleteRepository(db_path),
        audit_repository=audit or AuditRepository(db_path),
        row_attribution_repository=row_attribution_repository,
        db_client=db,
        runtime_ready=lambda: (True, None),
    )


def create_commit_unknown_delete_run(
    db_path: Path,
    source_dir: Path,
    db: FakeDeleteDb,
    *,
    delete_service: UploadDeleteService | None = None,
) -> str:
    item_id, _source_file = create_preview_for_delete(db_path, source_dir)
    service_under_test = delete_service or service_with_settings(
        db_path,
        db,
        v2_row_attribution_enabled=True,
        row_attribution_hmac_key=HMAC_KEY,
    )
    preflight = service_under_test.create_preflight(
        DeletePreflightRequest(
            preview_run_id="prv_done",
            preview_item_ids=[item_id],
            expected_already_in_db_items=1,
        )
    )
    with pytest.raises(DeleteRejectedError) as exc:
        service_under_test.start_delete(
            DeleteJobCreateRequest(
                preflight_id=preflight.preflight_id,
                expected_delete_keys=2,
                typed_delete_keys="2",
                acknowledge_no_undo=True,
                acknowledge_rollback_requires_fresh_preview_and_start_upload=True,
            )
        )
    assert exc.value.reason == "commit_unknown"
    with UploadDeleteRepository(db_path).connect() as connection:
        run = connection.execute("SELECT * FROM delete_runs ORDER BY created_at DESC LIMIT 1").fetchone()
    return str(run["delete_run_id"])


def latest_audit(db_path: Path):
    with UploadDeleteRepository(db_path).connect() as connection:
        return connection.execute("SELECT * FROM audit_log ORDER BY audit_id DESC LIMIT 1").fetchone()


def update_preview_item_status(db_path: Path, item_id: int, status: str) -> None:
    with UploadDeleteRepository(db_path).connect() as connection:
        connection.execute(
            """
            UPDATE preview_items
            SET status = ?, reason_code = 'fixture_status_changed'
            WHERE preview_item_id = ?
            """,
            (status, item_id),
        )


def test_preflight_blocks_when_delete_permission_is_not_proven(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    item_id, _source = create_preview_for_delete(db_path, tmp_path / "source")
    db = FakeDeleteDb(
        guard_result=DbGuardResult(
            False,
            "loopback_expected_db_port",
            None,
            "db_delete_permission_denied",
        )
    )

    response = service(db_path, db).create_preflight(
        DeletePreflightRequest(
            preview_run_id="prv_done",
            preview_item_ids=[item_id],
            expected_already_in_db_items=1,
        )
    )

    assert response.status == "blocked"
    assert response.reason_code == "db_delete_permission_denied"
    assert db.count_calls == 0
    assert db.delete_calls == 0
    audit = latest_audit(db_path)
    params = json.loads(audit["params_json_redacted"])
    assert audit["action"] == "upload.delete_preflight"
    assert audit["result"] == "blocked"
    assert params["rawMatchRowsReturned"] is False
    assert params["selectedRowCount"] == 2
    assert "2026-06-18T09:00:00" not in audit["params_json_redacted"]
    assert "extruder_integrated" not in audit["params_json_redacted"]


def test_start_delete_writes_start_audit_before_db_delete_and_succeeds(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    item_id, _source = create_preview_for_delete(db_path, tmp_path / "source")
    db = FakeDeleteDb()
    delete_service = service(db_path, db)
    preflight = delete_service.create_preflight(
        DeletePreflightRequest(
            preview_run_id="prv_done",
            preview_item_ids=[item_id],
            expected_already_in_db_items=1,
        )
    )

    response = delete_service.start_delete(
        DeleteJobCreateRequest(
            preflight_id=preflight.preflight_id,
            expected_delete_keys=2,
            typed_delete_keys="2",
            acknowledge_no_undo=True,
            acknowledge_rollback_requires_fresh_preview_and_start_upload=True,
        )
    )

    assert response.status == "succeeded"
    assert response.deleted_keys == 2
    assert response.raw_keys_returned is False
    assert db.delete_calls == 1
    with UploadDeleteRepository(db_path).connect() as connection:
        start_audit = connection.execute(
            "SELECT * FROM audit_log WHERE action = 'upload.delete_start'"
        ).fetchone()
        run = connection.execute("SELECT * FROM delete_runs WHERE delete_run_id = ?", (response.delete_run_id,)).fetchone()
    assert start_audit is not None
    assert run["start_audit_id"] == start_audit["audit_id"]
    assert run["status"] == "succeeded"


def test_default_v2_evidence_gate_does_not_write_delta_or_attribution(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    item_id, _source = create_preview_for_delete(db_path, tmp_path / "source")
    db = FakeDeleteDb(guard_result=DbGuardResult(True, "loopback_expected_db_port", DB_HASH))
    delete_service = service(db_path, db)
    preflight = delete_service.create_preflight(
        DeletePreflightRequest(
            preview_run_id="prv_done",
            preview_item_ids=[item_id],
            expected_already_in_db_items=1,
        )
    )

    delete_service.start_delete(
        DeleteJobCreateRequest(
            preflight_id=preflight.preflight_id,
            expected_delete_keys=2,
            typed_delete_keys="2",
            acknowledge_no_undo=True,
            acknowledge_rollback_requires_fresh_preview_and_start_upload=True,
        )
    )

    with UploadDeleteRepository(db_path).connect() as connection:
        delta_count = connection.execute("SELECT COUNT(*) AS count FROM db_delta_evidence").fetchone()["count"]
        attribution_count = connection.execute("SELECT COUNT(*) AS count FROM row_attribution_ledger").fetchone()["count"]
    assert delta_count == 0
    assert attribution_count == 0


def test_v2_evidence_gate_links_delete_audit_delta_and_row_attribution(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    item_id, _source = create_preview_for_delete(db_path, tmp_path / "source")
    db = FakeDeleteDb(guard_result=DbGuardResult(True, "loopback_expected_db_port", DB_HASH))
    delete_service = service_with_settings(
        db_path,
        db,
        v2_row_attribution_enabled=True,
        row_attribution_hmac_key=HMAC_KEY,
    )
    preflight = delete_service.create_preflight(
        DeletePreflightRequest(
            preview_run_id="prv_done",
            preview_item_ids=[item_id],
            expected_already_in_db_items=1,
        )
    )

    response = delete_service.start_delete(
        DeleteJobCreateRequest(
            preflight_id=preflight.preflight_id,
            expected_delete_keys=2,
            typed_delete_keys="2",
            acknowledge_no_undo=True,
            acknowledge_rollback_requires_fresh_preview_and_start_upload=True,
        )
    )

    deltas = DbDeltaEvidenceRepository(db_path).list_by_operation(response.delete_run_id)
    attributions = RowAttributionRepository(db_path).list_by_operation(response.delete_run_id)
    with UploadDeleteRepository(db_path).connect() as connection:
        start_audit = connection.execute(
            "SELECT * FROM audit_log WHERE action = 'upload.delete_start' ORDER BY audit_id DESC LIMIT 1"
        ).fetchone()
        success_audit = connection.execute(
            "SELECT * FROM audit_log WHERE action = 'upload.delete_succeeded' ORDER BY audit_id DESC LIMIT 1"
        ).fetchone()

    assert len(deltas) == 1
    assert deltas[0]["audit_id"] == start_audit["audit_id"]
    assert deltas[0]["before_count"] == 2
    assert deltas[0]["after_count"] == 0
    assert deltas[0]["expected_delta"] == -2
    assert deltas[0]["actual_delta"] == -2
    assert deltas[0]["result"] == "matched"
    assert decode_delta_scope_json(deltas[0]["delta_scope_json"])["selectedRowCount"] == 2
    assert len(attributions) == 2
    assert {row["audit_id"] for row in attributions} == {start_audit["audit_id"]}
    assert {row["db_delta_id"] for row in attributions} == {deltas[0]["delta_id"]}
    assert {row["outcome"] for row in attributions} == {"deleted"}
    success_params = json.loads(success_audit["params_json_redacted"])
    assert success_params["dbDeltaId"] == deltas[0]["delta_id"]
    assert success_params["attributionRowsCreated"] == 2
    stored_values = "|".join(
        [
            *(str(deltas[0][key]) for key in deltas[0].keys()),
            *(str(row[key]) for row in attributions for key in row.keys()),
            success_audit["params_json_redacted"],
        ]
    )
    assert "2026-06-18T09:00:00" not in stored_values
    assert "extruder_integrated" not in stored_values


def test_v2_delete_db_failure_marks_failed_and_records_evidence(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    item_id, _source = create_preview_for_delete(db_path, tmp_path / "source")
    db = FakeDeleteDb(
        guard_result=DbGuardResult(True, "loopback_expected_db_port", DB_HASH),
        delete_error=DeleteDbFailedError("deleted_count_mismatch"),
    )
    delete_service = service_with_settings(
        db_path,
        db,
        v2_row_attribution_enabled=True,
        row_attribution_hmac_key=HMAC_KEY,
    )
    preflight = delete_service.create_preflight(
        DeletePreflightRequest(
            preview_run_id="prv_done",
            preview_item_ids=[item_id],
            expected_already_in_db_items=1,
        )
    )

    with pytest.raises(DeleteRejectedError) as exc:
        delete_service.start_delete(
            DeleteJobCreateRequest(
                preflight_id=preflight.preflight_id,
                expected_delete_keys=2,
                typed_delete_keys="2",
                acknowledge_no_undo=True,
                acknowledge_rollback_requires_fresh_preview_and_start_upload=True,
            )
        )

    assert exc.value.reason == "deleted_count_mismatch"
    assert db.delete_calls == 1
    with UploadDeleteRepository(db_path).connect() as connection:
        run = connection.execute("SELECT * FROM delete_runs ORDER BY created_at DESC LIMIT 1").fetchone()
        audit = connection.execute(
            "SELECT * FROM audit_log WHERE action = 'upload.delete_failed' ORDER BY audit_id DESC LIMIT 1"
        ).fetchone()
        item_rows = connection.execute(
            "SELECT status, reason_code FROM delete_run_items WHERE delete_run_id = ?",
            (run["delete_run_id"],),
        ).fetchall()
    deltas = DbDeltaEvidenceRepository(db_path).list_by_operation(run["delete_run_id"])
    attributions = RowAttributionRepository(db_path).list_by_operation(run["delete_run_id"])
    assert run["status"] == "failed"
    assert run["recovery_required"] == 0
    assert run["error_code"] == "deleted_count_mismatch"
    assert run["finished_at"] is not None
    assert audit["result"] == "failure"
    assert audit["error_code"] == "deleted_count_mismatch"
    assert {row["status"] for row in item_rows} == {"failed"}
    assert {row["reason_code"] for row in item_rows} == {"deleted_count_mismatch"}
    assert len(deltas) == 1
    assert deltas[0]["audit_id"] == audit["audit_id"]
    assert deltas[0]["before_count"] == 2
    assert deltas[0]["after_count"] == 2
    assert deltas[0]["expected_delta"] == 0
    assert deltas[0]["actual_delta"] == 0
    assert deltas[0]["result"] == "failed_before_mutation"
    assert {row["outcome"] for row in attributions} == {"failed_before_mutation"}


def test_v2_successful_delete_evidence_write_failure_marks_commit_unknown(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    item_id, _source = create_preview_for_delete(db_path, tmp_path / "source")
    db = FakeDeleteDb(guard_result=DbGuardResult(True, "loopback_expected_db_port", DB_HASH))
    disabled_attribution = RowAttributionRepository(db_path, writes_enabled=False)
    delete_service = service_with_settings(
        db_path,
        db,
        row_attribution_repository=disabled_attribution,
        v2_row_attribution_enabled=True,
        row_attribution_hmac_key=HMAC_KEY,
    )
    preflight = delete_service.create_preflight(
        DeletePreflightRequest(
            preview_run_id="prv_done",
            preview_item_ids=[item_id],
            expected_already_in_db_items=1,
        )
    )

    with pytest.raises(DeleteRejectedError) as exc:
        delete_service.start_delete(
            DeleteJobCreateRequest(
                preflight_id=preflight.preflight_id,
                expected_delete_keys=2,
                typed_delete_keys="2",
                acknowledge_no_undo=True,
                acknowledge_rollback_requires_fresh_preview_and_start_upload=True,
            )
        )

    assert exc.value.reason == "evidence_write_failed"
    assert db.delete_calls == 1
    with UploadDeleteRepository(db_path).connect() as connection:
        run = connection.execute("SELECT * FROM delete_runs ORDER BY created_at DESC LIMIT 1").fetchone()
        audit = connection.execute("SELECT * FROM audit_log ORDER BY audit_id DESC LIMIT 1").fetchone()
        item_rows = connection.execute(
            "SELECT status, reason_code FROM delete_run_items WHERE delete_run_id = ?",
            (run["delete_run_id"],),
        ).fetchall()
    deltas = DbDeltaEvidenceRepository(db_path).list_by_operation(run["delete_run_id"])
    attributions = RowAttributionRepository(db_path).list_by_operation(run["delete_run_id"])
    assert run["status"] == "commit_unknown"
    assert run["deleted_key_count"] == 2
    assert run["recovery_required"] == 1
    assert run["error_code"] == "evidence_write_failed"
    assert audit["action"] == "upload.delete_failed"
    assert audit["result"] == "failure"
    assert audit["error_code"] == "evidence_write_failed"
    assert {row["status"] for row in item_rows} == {"unknown"}
    assert {row["reason_code"] for row in item_rows} == {"evidence_write_failed"}
    assert len(deltas) == 1
    assert deltas[0]["result"] == "matched"
    assert deltas[0]["before_count"] == 2
    assert deltas[0]["after_count"] == 0
    assert attributions == []


def test_v2_evidence_gate_blocks_delete_before_mutation_without_hmac_key(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    item_id, _source = create_preview_for_delete(db_path, tmp_path / "source")
    db = FakeDeleteDb(guard_result=DbGuardResult(True, "loopback_expected_db_port", DB_HASH))
    delete_service = service_with_settings(db_path, db, v2_row_attribution_enabled=True)
    preflight = delete_service.create_preflight(
        DeletePreflightRequest(
            preview_run_id="prv_done",
            preview_item_ids=[item_id],
            expected_already_in_db_items=1,
        )
    )

    with pytest.raises(DeleteRejectedError) as exc:
        delete_service.start_delete(
            DeleteJobCreateRequest(
                preflight_id=preflight.preflight_id,
                expected_delete_keys=2,
                typed_delete_keys="2",
                acknowledge_no_undo=True,
                acknowledge_rollback_requires_fresh_preview_and_start_upload=True,
            )
        )

    assert exc.value.reason == "row_attribution_hmac_key_missing"
    assert db.delete_calls == 0
    with UploadDeleteRepository(db_path).connect() as connection:
        run = connection.execute("SELECT * FROM delete_runs ORDER BY created_at DESC LIMIT 1").fetchone()
    assert run["status"] == "blocked"
    assert run["error_code"] == "row_attribution_hmac_key_missing"


def test_v2_delta_mismatch_prevents_success_attribution(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    item_id, _source = create_preview_for_delete(db_path, tmp_path / "source")
    db = FakeDeleteDb(
        guard_result=DbGuardResult(True, "loopback_expected_db_port", DB_HASH),
        deleted_count=1,
    )
    delete_service = service_with_settings(
        db_path,
        db,
        v2_row_attribution_enabled=True,
        row_attribution_hmac_key=HMAC_KEY,
    )
    preflight = delete_service.create_preflight(
        DeletePreflightRequest(
            preview_run_id="prv_done",
            preview_item_ids=[item_id],
            expected_already_in_db_items=1,
        )
    )

    with pytest.raises(DeleteRejectedError) as exc:
        delete_service.start_delete(
            DeleteJobCreateRequest(
                preflight_id=preflight.preflight_id,
                expected_delete_keys=2,
                typed_delete_keys="2",
                acknowledge_no_undo=True,
                acknowledge_rollback_requires_fresh_preview_and_start_upload=True,
            )
        )

    assert exc.value.reason == "db_delta_mismatch"
    with UploadDeleteRepository(db_path).connect() as connection:
        run = connection.execute("SELECT * FROM delete_runs ORDER BY created_at DESC LIMIT 1").fetchone()
        failed_audit = connection.execute(
            "SELECT * FROM audit_log WHERE action = 'upload.delete_failed' ORDER BY audit_id DESC LIMIT 1"
        ).fetchone()
    deltas = DbDeltaEvidenceRepository(db_path).list_by_operation(run["delete_run_id"])
    attributions = RowAttributionRepository(db_path).list_by_operation(run["delete_run_id"])
    assert run["status"] == "commit_unknown"
    assert run["recovery_required"] == 1
    assert run["error_code"] == "db_delta_mismatch"
    assert len(deltas) == 1
    assert deltas[0]["result"] == "mismatched"
    assert deltas[0]["expected_delta"] == -2
    assert deltas[0]["actual_delta"] == -1
    assert {row["outcome"] for row in attributions} == {"unknown_requires_reconcile"}
    failed_params = json.loads(failed_audit["params_json_redacted"])
    assert failed_params["dbDeltaId"] == deltas[0]["delta_id"]
    assert failed_params["attributionRowsCreated"] == 2


def test_timestamp_date_scope_deletes_only_matching_day_keys(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    item_id, _source = create_mixed_date_preview_for_delete(db_path, tmp_path / "source")
    db = FakeDeleteDb()
    delete_service = service(db_path, db)
    preflight = delete_service.create_preflight(
        DeletePreflightRequest(
            preview_run_id="prv_mixed",
            preview_item_ids=[item_id],
            expected_already_in_db_items=1,
            timestamp_start_date="2026-01-19",
            timestamp_end_date="2026-01-19",
        )
    )

    assert preflight.status == "ready"
    assert preflight.selected_key_count == 2
    assert preflight.timestamp_start_date.isoformat() == "2026-01-19"
    assert preflight.timestamp_end_date.isoformat() == "2026-01-19"

    response = delete_service.start_delete(
        DeleteJobCreateRequest(
            preflight_id=preflight.preflight_id,
            expected_delete_keys=2,
            typed_delete_keys="2",
            acknowledge_no_undo=True,
            acknowledge_rollback_requires_fresh_preview_and_start_upload=True,
        )
    )

    assert response.status == "succeeded"
    assert response.deleted_keys == 2
    with UploadDeleteRepository(db_path).connect() as connection:
        start_audit = connection.execute(
            "SELECT * FROM audit_log WHERE action = 'upload.delete_start' ORDER BY audit_id DESC LIMIT 1"
        ).fetchone()
        audit = connection.execute(
            "SELECT * FROM audit_log WHERE action = 'upload.delete_succeeded' ORDER BY audit_id DESC LIMIT 1"
        ).fetchone()
    start_params = json.loads(start_audit["params_json_redacted"])
    assert start_params["timestampStartDate"] == "2026-01-19"
    assert start_params["timestampEndDate"] == "2026-01-19"
    params = json.loads(audit["params_json_redacted"])
    assert params["timestampStartDate"] == "2026-01-19"
    assert params["timestampEndDate"] == "2026-01-19"
    assert "2026-01-20T09:00:00" not in audit["params_json_redacted"]
    assert "extruder_integrated" not in audit["params_json_redacted"]


def test_start_delete_blocks_when_start_audit_write_fails_before_db_mutation(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    item_id, _source = create_preview_for_delete(db_path, tmp_path / "source")
    db = FakeDeleteDb()
    preflight = service(db_path, db).create_preflight(
        DeletePreflightRequest(
            preview_run_id="prv_done",
            preview_item_ids=[item_id],
            expected_already_in_db_items=1,
        )
    )
    failing_audit = FailStartAuditRepository(db_path)

    with pytest.raises(DeleteRejectedError) as exc:
        service(db_path, db, failing_audit).start_delete(
            DeleteJobCreateRequest(
                preflight_id=preflight.preflight_id,
                expected_delete_keys=2,
                typed_delete_keys="2",
                acknowledge_no_undo=True,
                acknowledge_rollback_requires_fresh_preview_and_start_upload=True,
            )
        )

    assert exc.value.reason == "audit_write_failed"
    assert db.delete_calls == 0
    with UploadDeleteRepository(db_path).connect() as connection:
        run = connection.execute("SELECT * FROM delete_runs ORDER BY created_at DESC LIMIT 1").fetchone()
    assert run["status"] == "blocked"
    assert run["error_code"] == "audit_write_failed"


def test_start_delete_revalidates_preview_item_status_at_start_time(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    item_id, _source = create_preview_for_delete(db_path, tmp_path / "source")
    db = FakeDeleteDb()
    delete_service = service(db_path, db)
    preflight = delete_service.create_preflight(
        DeletePreflightRequest(
            preview_run_id="prv_done",
            preview_item_ids=[item_id],
            expected_already_in_db_items=1,
        )
    )
    assert db.count_calls == 1
    update_preview_item_status(db_path, item_id, "risky")

    with pytest.raises(DeleteRejectedError) as exc:
        delete_service.start_delete(
            DeleteJobCreateRequest(
                preflight_id=preflight.preflight_id,
                expected_delete_keys=2,
                typed_delete_keys="2",
                acknowledge_no_undo=True,
                acknowledge_rollback_requires_fresh_preview_and_start_upload=True,
            )
        )

    assert exc.value.reason == "selection_status_changed"
    assert db.count_calls == 1
    assert db.delete_calls == 0


def test_start_delete_revalidates_keyset_at_start_time(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    item_id, source_file = create_preview_for_delete(db_path, tmp_path / "source")
    db = FakeDeleteDb()
    delete_service = service(db_path, db)
    preflight = delete_service.create_preflight(
        DeletePreflightRequest(
            preview_run_id="prv_done",
            preview_item_ids=[item_id],
            expected_already_in_db_items=1,
        )
    )
    source_file.write_text("Date,Time,Mold1\n2026-06-18,09:00:00,1\n", encoding="utf-8")

    with pytest.raises(DeleteRejectedError) as exc:
        delete_service.start_delete(
            DeleteJobCreateRequest(
                preflight_id=preflight.preflight_id,
                expected_delete_keys=2,
                typed_delete_keys="2",
                acknowledge_no_undo=True,
                acknowledge_rollback_requires_fresh_preview_and_start_upload=True,
            )
        )

    assert exc.value.reason == "file_signature_changed"
    assert db.delete_calls == 0


def test_start_delete_marks_commit_unknown_for_ambiguous_commit(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    item_id, _source_file = create_preview_for_delete(db_path, tmp_path / "source")
    db = FakeDeleteDb(delete_error=DeleteCommitUnknownError())
    delete_service = service(db_path, db)
    preflight = delete_service.create_preflight(
        DeletePreflightRequest(
            preview_run_id="prv_done",
            preview_item_ids=[item_id],
            expected_already_in_db_items=1,
        )
    )

    with pytest.raises(DeleteRejectedError) as exc:
        delete_service.start_delete(
            DeleteJobCreateRequest(
                preflight_id=preflight.preflight_id,
                expected_delete_keys=2,
                typed_delete_keys="2",
                acknowledge_no_undo=True,
                acknowledge_rollback_requires_fresh_preview_and_start_upload=True,
            )
        )

    assert exc.value.reason == "commit_unknown"
    with UploadDeleteRepository(db_path).connect() as connection:
        run = connection.execute("SELECT * FROM delete_runs ORDER BY created_at DESC LIMIT 1").fetchone()
        audit = connection.execute("SELECT * FROM audit_log ORDER BY audit_id DESC LIMIT 1").fetchone()
    assert run["status"] == "commit_unknown"
    assert run["recovery_required"] == 1
    assert run["error_code"] == "commit_unknown"
    assert audit["action"] == "upload.delete_failed"
    assert audit["error_code"] == "commit_unknown"


def test_reconcile_fails_when_keyset_cannot_be_rebuilt(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    item_id, source_file = create_preview_for_delete(db_path, tmp_path / "source")
    db = FakeDeleteDb(delete_error=DeleteCommitUnknownError())
    delete_service = service(db_path, db)
    preflight = delete_service.create_preflight(
        DeletePreflightRequest(
            preview_run_id="prv_done",
            preview_item_ids=[item_id],
            expected_already_in_db_items=1,
        )
    )
    with pytest.raises(DeleteRejectedError):
        delete_service.start_delete(
            DeleteJobCreateRequest(
                preflight_id=preflight.preflight_id,
                expected_delete_keys=2,
                typed_delete_keys="2",
                acknowledge_no_undo=True,
                acknowledge_rollback_requires_fresh_preview_and_start_upload=True,
            )
        )
    with UploadDeleteRepository(db_path).connect() as connection:
        run = connection.execute("SELECT * FROM delete_runs ORDER BY created_at DESC LIMIT 1").fetchone()
    source_file.write_text("Date,Time,Mold1\n2026-06-18,09:00:00,1\n", encoding="utf-8")

    response = delete_service.reconcile(run["delete_run_id"])

    assert response.status == "reconciliation_failed"
    assert response.recovery_required is True
    assert db.count_calls == 2
    with UploadDeleteRepository(db_path).connect() as connection:
        updated = connection.execute("SELECT * FROM delete_runs WHERE delete_run_id = ?", (run["delete_run_id"],)).fetchone()
        audit = connection.execute("SELECT * FROM audit_log ORDER BY audit_id DESC LIMIT 1").fetchone()
    assert updated["status"] == "reconciliation_failed"
    assert updated["recovery_required"] == 1
    assert updated["error_code"] == "file_signature_changed"
    assert audit["action"] == "upload.delete_reconciled"
    assert audit["result"] == "failure"


def test_reconcile_marks_failed_when_db_count_fails_after_reconciling(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    item_id, _source_file = create_preview_for_delete(db_path, tmp_path / "source")
    db = FakeDeleteDb(delete_error=DeleteCommitUnknownError())
    delete_service = service(db_path, db)
    preflight = delete_service.create_preflight(
        DeletePreflightRequest(
            preview_run_id="prv_done",
            preview_item_ids=[item_id],
            expected_already_in_db_items=1,
        )
    )
    with pytest.raises(DeleteRejectedError):
        delete_service.start_delete(
            DeleteJobCreateRequest(
                preflight_id=preflight.preflight_id,
                expected_delete_keys=2,
                typed_delete_keys="2",
                acknowledge_no_undo=True,
                acknowledge_rollback_requires_fresh_preview_and_start_upload=True,
            )
        )
    with UploadDeleteRepository(db_path).connect() as connection:
        run = connection.execute("SELECT * FROM delete_runs ORDER BY created_at DESC LIMIT 1").fetchone()
    db.count_error = DeleteDbBlockedError("db_count_check_failed")

    response = delete_service.reconcile(run["delete_run_id"])

    assert response.status == "reconciliation_failed"
    assert response.recovery_required is True
    with UploadDeleteRepository(db_path).connect() as connection:
        updated = connection.execute("SELECT * FROM delete_runs WHERE delete_run_id = ?", (run["delete_run_id"],)).fetchone()
        audit = connection.execute("SELECT * FROM audit_log ORDER BY audit_id DESC LIMIT 1").fetchone()
    assert updated["status"] == "reconciliation_failed"
    assert updated["recovery_required"] == 1
    assert updated["error_code"] == "db_count_check_failed"
    assert audit["action"] == "upload.delete_reconciled"
    assert audit["result"] == "failure"


def test_reconcile_success_clears_previous_error_fields(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    item_id, _source_file = create_preview_for_delete(db_path, tmp_path / "source")
    db = FakeDeleteDb(delete_error=DeleteCommitUnknownError())
    delete_service = service(db_path, db)
    preflight = delete_service.create_preflight(
        DeletePreflightRequest(
            preview_run_id="prv_done",
            preview_item_ids=[item_id],
            expected_already_in_db_items=1,
        )
    )
    with pytest.raises(DeleteRejectedError):
        delete_service.start_delete(
            DeleteJobCreateRequest(
                preflight_id=preflight.preflight_id,
                expected_delete_keys=2,
                typed_delete_keys="2",
                acknowledge_no_undo=True,
                acknowledge_rollback_requires_fresh_preview_and_start_upload=True,
            )
        )
    with UploadDeleteRepository(db_path).connect() as connection:
        run = connection.execute("SELECT * FROM delete_runs ORDER BY created_at DESC LIMIT 1").fetchone()
    db.count_error = DeleteDbBlockedError("db_count_check_failed")

    failed = delete_service.reconcile(run["delete_run_id"])
    assert failed.status == "reconciliation_failed"

    db.count_error = None
    db.existing_count = 0
    response = delete_service.reconcile(run["delete_run_id"], acknowledge_retry=True)

    assert response.status == "reconciled_succeeded"
    assert response.recovery_required is False
    with UploadDeleteRepository(db_path).connect() as connection:
        updated = connection.execute("SELECT * FROM delete_runs WHERE delete_run_id = ?", (run["delete_run_id"],)).fetchone()
    assert updated["status"] == "reconciled_succeeded"
    assert updated["recovery_required"] == 0
    assert updated["error_code"] is None
    assert updated["error_message"] is None
    assert updated["finished_at"] is not None


def test_v2_reconcile_success_links_audit_delta_and_absent_attribution(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    db = FakeDeleteDb(
        guard_result=DbGuardResult(True, "loopback_expected_db_port", DB_HASH),
        delete_error=DeleteCommitUnknownError(),
    )
    delete_run_id = create_commit_unknown_delete_run(db_path, tmp_path / "source", db)
    db.delete_error = None
    db.existing_count = 0
    delete_service = service_with_settings(
        db_path,
        db,
        v2_row_attribution_enabled=True,
        row_attribution_hmac_key=HMAC_KEY,
    )

    response = delete_service.reconcile(delete_run_id)

    deltas = [
        row
        for row in DbDeltaEvidenceRepository(db_path).list_by_operation(delete_run_id)
        if row["operation_type"] == "delete_reconcile"
    ]
    attributions = [
        row
        for row in RowAttributionRepository(db_path).list_by_operation(delete_run_id)
        if row["operation_type"] == "delete_reconcile"
    ]
    with UploadDeleteRepository(db_path).connect() as connection:
        run = connection.execute("SELECT * FROM delete_runs WHERE delete_run_id = ?", (delete_run_id,)).fetchone()
        audit = connection.execute(
            "SELECT * FROM audit_log WHERE action = 'upload.delete_reconciled' ORDER BY audit_id DESC LIMIT 1"
        ).fetchone()

    assert response.status == "reconciled_succeeded"
    assert run["status"] == "reconciled_succeeded"
    assert run["recovery_required"] == 0
    assert len(deltas) == 1
    assert deltas[0]["audit_id"] == audit["audit_id"]
    assert deltas[0]["before_count"] == 2
    assert deltas[0]["after_count"] == 0
    assert deltas[0]["expected_delta"] == -2
    assert deltas[0]["actual_delta"] == -2
    assert deltas[0]["result"] == "matched"
    assert decode_delta_scope_json(deltas[0]["delta_scope_json"])["rowsAbsent"] == 2
    assert len(attributions) == 2
    assert {row["audit_id"] for row in attributions} == {audit["audit_id"]}
    assert {row["db_delta_id"] for row in attributions} == {deltas[0]["delta_id"]}
    assert {row["outcome"] for row in attributions} == {"reconciled_absent"}
    stored_values = "|".join(
        [
            *(str(deltas[0][key]) for key in deltas[0].keys()),
            *(str(row[key]) for row in attributions for key in row.keys()),
            audit["params_json_redacted"],
        ]
    )
    assert "2026-06-18T09:00:00" not in stored_values
    assert "extruder_integrated" not in stored_values


def test_v2_reconcile_rollback_links_audit_delta_and_unchanged_attribution(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    db = FakeDeleteDb(
        guard_result=DbGuardResult(True, "loopback_expected_db_port", DB_HASH),
        delete_error=DeleteCommitUnknownError(),
    )
    delete_run_id = create_commit_unknown_delete_run(db_path, tmp_path / "source", db)
    db.delete_error = None
    db.existing_count = 2
    delete_service = service_with_settings(
        db_path,
        db,
        v2_row_attribution_enabled=True,
        row_attribution_hmac_key=HMAC_KEY,
    )

    response = delete_service.reconcile(delete_run_id)

    deltas = [
        row
        for row in DbDeltaEvidenceRepository(db_path).list_by_operation(delete_run_id)
        if row["operation_type"] == "delete_reconcile"
    ]
    attributions = [
        row
        for row in RowAttributionRepository(db_path).list_by_operation(delete_run_id)
        if row["operation_type"] == "delete_reconcile"
    ]
    with UploadDeleteRepository(db_path).connect() as connection:
        run = connection.execute("SELECT * FROM delete_runs WHERE delete_run_id = ?", (delete_run_id,)).fetchone()
        audit = connection.execute(
            "SELECT * FROM audit_log WHERE action = 'upload.delete_reconciled' ORDER BY audit_id DESC LIMIT 1"
        ).fetchone()

    assert response.status == "reconciled_rolled_back"
    assert run["status"] == "reconciled_rolled_back"
    assert run["recovery_required"] == 0
    assert len(deltas) == 1
    assert deltas[0]["audit_id"] == audit["audit_id"]
    assert deltas[0]["before_count"] == 2
    assert deltas[0]["after_count"] == 2
    assert deltas[0]["expected_delta"] == 0
    assert deltas[0]["actual_delta"] == 0
    assert deltas[0]["result"] == "matched"
    assert len(attributions) == 2
    assert {row["db_delta_id"] for row in attributions} == {deltas[0]["delta_id"]}
    assert {row["outcome"] for row in attributions} == {"unchanged"}


def test_v2_reconcile_evidence_write_failure_does_not_leave_success_state(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    db = FakeDeleteDb(
        guard_result=DbGuardResult(True, "loopback_expected_db_port", DB_HASH),
        delete_error=DeleteCommitUnknownError(),
    )
    delete_run_id = create_commit_unknown_delete_run(db_path, tmp_path / "source", db)
    db.delete_error = None
    db.existing_count = 0
    disabled_attribution = RowAttributionRepository(db_path, writes_enabled=False)
    delete_service = service_with_settings(
        db_path,
        db,
        row_attribution_repository=disabled_attribution,
        v2_row_attribution_enabled=True,
        row_attribution_hmac_key=HMAC_KEY,
    )

    response = delete_service.reconcile(delete_run_id)

    deltas = [
        row
        for row in DbDeltaEvidenceRepository(db_path).list_by_operation(delete_run_id)
        if row["operation_type"] == "delete_reconcile"
    ]
    attributions = [
        row
        for row in RowAttributionRepository(db_path).list_by_operation(delete_run_id)
        if row["operation_type"] == "delete_reconcile"
    ]
    with UploadDeleteRepository(db_path).connect() as connection:
        run = connection.execute("SELECT * FROM delete_runs WHERE delete_run_id = ?", (delete_run_id,)).fetchone()
        latest_audit_row = connection.execute("SELECT * FROM audit_log ORDER BY audit_id DESC LIMIT 1").fetchone()

    assert response.status == "reconciliation_failed"
    assert run["status"] == "reconciliation_failed"
    assert run["recovery_required"] == 1
    assert run["error_code"] == "evidence_write_failed"
    assert latest_audit_row["action"] == "upload.delete_reconciled"
    assert latest_audit_row["result"] == "failure"
    assert latest_audit_row["error_code"] == "evidence_write_failed"
    assert len(deltas) == 1
    assert deltas[0]["result"] == "matched"
    assert attributions == []


def test_reconcile_does_not_require_delete_privilege(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    item_id, _source_file = create_preview_for_delete(db_path, tmp_path / "source")
    db = FakeDeleteDb(delete_error=DeleteCommitUnknownError())
    delete_service = service(db_path, db)
    preflight = delete_service.create_preflight(
        DeletePreflightRequest(
            preview_run_id="prv_done",
            preview_item_ids=[item_id],
            expected_already_in_db_items=1,
        )
    )
    with pytest.raises(DeleteRejectedError):
        delete_service.start_delete(
            DeleteJobCreateRequest(
                preflight_id=preflight.preflight_id,
                expected_delete_keys=2,
                typed_delete_keys="2",
                acknowledge_no_undo=True,
                acknowledge_rollback_requires_fresh_preview_and_start_upload=True,
            )
        )
    with UploadDeleteRepository(db_path).connect() as connection:
        run = connection.execute("SELECT * FROM delete_runs ORDER BY created_at DESC LIMIT 1").fetchone()
    guard_calls_before_reconcile = db.guard_calls
    db.guard_result = DbGuardResult(False, "loopback_expected_db_port", None, "db_delete_permission_denied")
    db.target_guard_result = DbGuardResult(True, "loopback_expected_db_port", "fp_local")
    db.existing_count = 0

    response = delete_service.reconcile(run["delete_run_id"])

    assert response.status == "reconciled_succeeded"
    assert response.recovery_required is False
    assert db.guard_calls == guard_calls_before_reconcile
    assert db.target_guard_calls == 1
    assert db.count_calls == 3
