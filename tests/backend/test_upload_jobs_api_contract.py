import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.api.upload_jobs import UploadRuntimeReadiness, get_upload_job_repository, get_upload_runtime_readiness
from backend.app.core.settings import Settings, get_settings
from backend.app.db.upload_job_repository import UploadJobRepository
from backend.app.schemas.upload_jobs import UploadJobStatus
from backend.app.main import app, create_app
from tests.backend.test_upload_jobs_repository_contract import PREVIEW_GATE_SNAPSHOT, create_preview_with_items


START_UPLOAD_APPROVAL = {"previewRunId": "prv_done", "expectedTargetRows": 2, "expectedTargetFiles": 1}
RETRY_APPROVAL = {"expectedRemainingRows": 1, "expectedRetryFiles": 1}
TEST_JWT = "eyJhbGciOiJIUzI1NiJ9.eyJyb2xlIjoiYW5vbiJ9.signature"


@pytest.fixture(autouse=True)
def upload_runtime_ready_override():
    app.dependency_overrides[get_upload_runtime_readiness] = lambda: UploadRuntimeReadiness(
        ready=True,
        detail={"apiStatus": "ready", "dbStatus": "ready", "edgeStatus": "ready"},
    )
    yield
    app.dependency_overrides.pop(get_upload_runtime_readiness, None)


def expected_db_url() -> str:
    return "postgres" + "ql://postgres:postgres@127.0.0.1:25433/postgres"


def upload_ready_settings(db_path: Path) -> Settings:
    return Settings(
        state_db_path=str(db_path),
        plc_data_dir="",
        temperature_data_dir="",
        supabase_db_url=expected_db_url(),
        supabase_url="",
        supabase_edge_url="http://127.0.0.1:55321/functions/v1/upload-metrics",
        supabase_anon_key=TEST_JWT,
    )


def test_upload_job_routes_are_registered_in_openapi(monkeypatch) -> None:
    monkeypatch.setenv("EWC_API_DOCS_MODE", "enabled")
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.get("/api/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/upload/jobs" in paths
    assert "/api/upload/jobs/latest" in paths
    assert "/api/upload/jobs/{jobId}" in paths
    assert "/api/upload/jobs/{jobId}/retry" in paths
    assert "/api/upload/jobs/{jobId}/events" in paths
    get_settings.cache_clear()


def test_upload_job_start_rejects_missing_upload_config(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    app.dependency_overrides[get_upload_job_repository] = lambda: repository
    app.dependency_overrides[get_settings] = lambda: Settings(
        state_db_path=str(db_path),
        supabase_anon_key="",
        supabase_edge_url="",
        supabase_url="",
    )
    client = TestClient(app)

    try:
        response = client.post("/api/upload/jobs", json=START_UPLOAD_APPROVAL)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["detail"]["reason"] == "upload_config_missing"
    assert latest_audit(repository)["result"] == "blocked"
    assert latest_audit(repository)["error_code"] == "upload_config_missing"


def test_upload_job_start_rejects_stale_upload_target_preflight(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    db_url = "postgres" + "ql://postgres:postgres@127.0.0.1:25432/postgres"
    app.dependency_overrides[get_upload_job_repository] = lambda: repository
    app.dependency_overrides[get_settings] = lambda: Settings(
        state_db_path=str(db_path),
        local_supabase_api_port=55321,
        local_supabase_db_port=25433,
        supabase_url="http://127.0.0.1:54321",
        supabase_edge_url="",
        supabase_db_url=db_url,
        **{"supabase_anon_key": TEST_JWT},
    )
    client = TestClient(app)

    try:
        response = client.post("/api/upload/jobs", json=START_UPLOAD_APPROVAL)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["reason"] == "upload_target_preflight_failed"
    assert detail["targetClassPreflight"]["status"] == "blocked"
    assert detail["targetClassPreflight"]["uploadEdge"]["targetClass"] == "loopback_unexpected_port_upload_metrics"
    assert ("postgres" + "ql://") not in response.text
    audit = latest_audit(repository)
    assert audit["action"] == "upload.start"
    assert audit["result"] == "blocked"
    assert audit["error_code"] == "upload_target_preflight_failed"
    with repository.connect() as connection:
        count = connection.execute("SELECT COUNT(*) AS count FROM upload_jobs").fetchone()["count"]
    assert count == 0


def test_upload_job_start_rejects_db_target_class_mismatch(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    stale_db_url = "postgres" + "ql://postgres:postgres@127.0.0.1:25432/postgres"
    app.dependency_overrides[get_upload_job_repository] = lambda: repository
    app.dependency_overrides[get_settings] = lambda: Settings(
        state_db_path=str(db_path),
        local_supabase_api_port=55321,
        local_supabase_db_port=25433,
        supabase_db_url=stale_db_url,
        supabase_edge_url="http://127.0.0.1:55321/functions/v1/upload-metrics",
        supabase_anon_key=TEST_JWT,
    )
    client = TestClient(app)

    try:
        response = client.post("/api/upload/jobs", json=START_UPLOAD_APPROVAL)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["detail"]["reason"] == "db_target_class_mismatch"
    assert ("postgres" + "ql://") not in response.text
    audit = latest_audit(repository)
    assert audit["action"] == "upload.start"
    assert audit["result"] == "blocked"
    assert audit["error_code"] == "db_target_class_mismatch"
    with repository.connect() as connection:
        count = connection.execute("SELECT COUNT(*) AS count FROM upload_jobs").fetchone()["count"]
    assert count == 0


def test_upload_job_start_rejects_non_jwt_auth_key_before_queueing(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    app.dependency_overrides[get_upload_job_repository] = lambda: repository
    app.dependency_overrides[get_settings] = lambda: Settings(
        state_db_path=str(db_path),
        supabase_db_url=expected_db_url(),
        supabase_edge_url="http://127.0.0.1:55321/functions/v1/upload-metrics",
        supabase_anon_key="sb_publishable_fixture",
    )
    client = TestClient(app)

    try:
        response = client.post("/api/upload/jobs", json=START_UPLOAD_APPROVAL)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["detail"]["reason"] == "auth_invalid_or_stale_config"
    assert response.json()["detail"]["authKeyClass"] == "not_jwt"
    audit = latest_audit(repository)
    assert audit["action"] == "upload.start"
    assert audit["result"] == "blocked"
    assert audit["error_code"] == "auth_invalid_or_stale_config"
    with repository.connect() as connection:
        count = connection.execute("SELECT COUNT(*) AS count FROM upload_jobs").fetchone()["count"]
    assert count == 0


def test_upload_job_start_rejects_edge_unreachable_runtime_readiness(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    app.dependency_overrides[get_upload_job_repository] = lambda: repository
    app.dependency_overrides[get_settings] = lambda: upload_ready_settings(db_path)
    app.dependency_overrides[get_upload_runtime_readiness] = lambda: UploadRuntimeReadiness(
        ready=False,
        reason="edge_unreachable",
        detail={"apiStatus": "ready", "dbStatus": "ready", "edgeStatus": "unreachable"},
    )
    client = TestClient(app)

    try:
        response = client.post("/api/upload/jobs", json=START_UPLOAD_APPROVAL)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["detail"]["reason"] == "edge_unreachable"
    audit = latest_audit(repository)
    assert audit["action"] == "upload.start"
    assert audit["result"] == "blocked"
    assert audit["error_code"] == "edge_unreachable"
    with repository.connect() as connection:
        count = connection.execute("SELECT COUNT(*) AS count FROM upload_jobs").fetchone()["count"]
    assert count == 0


def test_upload_job_start_rejects_missing_expected_target_rows_with_blocked_audit(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    app.dependency_overrides[get_upload_job_repository] = lambda: repository
    app.dependency_overrides[get_settings] = lambda: upload_ready_settings(db_path)
    client = TestClient(app)

    try:
        response = client.post("/api/upload/jobs", json={"previewRunId": "prv_done"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["detail"]["reason"] == "expected_target_rows_required"
    audit = latest_audit(repository)
    assert audit["action"] == "upload.start"
    assert audit["result"] == "blocked"
    assert audit["error_code"] == "expected_target_rows_required"
    params = json.loads(audit["params_json_redacted"])
    assert params["previewRunId"] == "prv_done"
    assert params["expectedTargetRows"] is None
    with repository.connect() as connection:
        count = connection.execute("SELECT COUNT(*) AS count FROM upload_jobs").fetchone()["count"]
    assert count == 0


def test_upload_job_start_rejects_expected_target_row_mismatch_with_snapshot_counts(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    app.dependency_overrides[get_upload_job_repository] = lambda: repository
    app.dependency_overrides[get_settings] = lambda: upload_ready_settings(db_path)
    client = TestClient(app)

    try:
        response = client.post(
            "/api/upload/jobs",
            json={"previewRunId": "prv_done", "expectedTargetRows": 999, "expectedTargetFiles": 1},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["reason"] == "expected_target_rows_mismatch"
    assert detail["actualTargetRows"] == 2
    assert detail["actualTargetFiles"] == 1
    audit = latest_audit(repository)
    assert audit["action"] == "upload.start"
    assert audit["result"] == "blocked"
    assert audit["error_code"] == "expected_target_rows_mismatch"
    params = json.loads(audit["params_json_redacted"])
    assert params["expectedTargetRows"] == 999
    assert params["actualTargetRows"] == 2
    assert params["actualTargetFiles"] == 1
    with repository.connect() as connection:
        count = connection.execute("SELECT COUNT(*) AS count FROM upload_jobs").fetchone()["count"]
    assert count == 0


def test_upload_job_start_success_records_expected_and_actual_counts(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    app.dependency_overrides[get_upload_job_repository] = lambda: repository
    app.dependency_overrides[get_settings] = lambda: upload_ready_settings(db_path)
    submitted: list[str] = []
    monkeypatch.setattr(
        "backend.app.api.upload_jobs.executor.submit",
        lambda _fn, job_id: submitted.append(job_id),
    )
    client = TestClient(app)

    try:
        response = client.post("/api/upload/jobs", json=START_UPLOAD_APPROVAL)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    assert submitted == [body["jobId"]]
    audit = latest_audit(repository)
    assert audit["action"] == "upload.start"
    assert audit["result"] == "success"
    params = json.loads(audit["params_json_redacted"])
    assert params["expectedTargetRows"] == 2
    assert params["actualTargetRows"] == 2
    assert params["expectedTargetFiles"] == 1
    assert params["actualTargetFiles"] == 1


def test_upload_job_latest_returns_404_when_empty(tmp_path: Path) -> None:
    repository = UploadJobRepository(tmp_path / "state.db")
    app.dependency_overrides[get_upload_job_repository] = lambda: repository
    client = TestClient(app)

    try:
        response = client.get("/api/upload/jobs/latest")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_upload_job_start_active_job_writes_blocked_audit(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    repository.create_job_from_preview(
        job_id="upl_active",
        preview_run_id="prv_done",
        expected_target_rows=2,
        expected_target_files=1,
        options={},
        config_snapshot={},
        preview_gate_snapshot=PREVIEW_GATE_SNAPSHOT,
    )
    app.dependency_overrides[get_upload_job_repository] = lambda: repository
    app.dependency_overrides[get_settings] = lambda: Settings(
        state_db_path=str(db_path),
        supabase_db_url=expected_db_url(),
        supabase_edge_url="http://127.0.0.1:55321/functions/v1/upload-metrics",
        supabase_anon_key=TEST_JWT,
    )
    client = TestClient(app)

    try:
        response = client.post("/api/upload/jobs", json=START_UPLOAD_APPROVAL)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json()["detail"]["reason"] == "active_upload_job"
    audit = latest_audit(repository)
    assert audit["action"] == "upload.start"
    assert audit["result"] == "blocked"
    assert audit["error_code"] == "active_upload_job"


def test_upload_job_start_preview_not_uploadable_writes_blocked_audit(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    with repository.connect() as connection:
        connection.execute("UPDATE preview_runs SET status = 'partial_failed', db_status = 'unreachable' WHERE preview_run_id = 'prv_done'")
    app.dependency_overrides[get_upload_job_repository] = lambda: repository
    app.dependency_overrides[get_settings] = lambda: Settings(
        state_db_path=str(db_path),
        supabase_db_url=expected_db_url(),
        supabase_edge_url="http://127.0.0.1:55321/functions/v1/upload-metrics",
        supabase_anon_key=TEST_JWT,
    )
    client = TestClient(app)

    try:
        response = client.post("/api/upload/jobs", json=START_UPLOAD_APPROVAL)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["detail"]["reason"] == "preview_not_uploadable"
    audit = latest_audit(repository)
    assert audit["action"] == "upload.start"
    assert audit["result"] == "blocked"
    assert audit["error_code"] == "preview_not_uploadable"


def test_upload_job_start_rejects_preview_source_mismatch(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(
        db_path,
        config_snapshot={
            "previewGate": {
                "plc": {"pathClass": "network", "pathFingerprint": "old-source"},
                "temperature": {"pathClass": "missing", "pathFingerprint": None},
                "supabaseDbUrlConfigured": False,
            }
        },
    )
    repository = UploadJobRepository(db_path)
    app.dependency_overrides[get_upload_job_repository] = lambda: repository
    app.dependency_overrides[get_settings] = lambda: Settings(
        state_db_path=str(db_path),
        local_supabase_api_port=55321,
        supabase_db_url=expected_db_url(),
        supabase_edge_url="http://127.0.0.1:55321/functions/v1/upload-metrics",
        supabase_anon_key=TEST_JWT,
    )
    client = TestClient(app)

    try:
        response = client.post("/api/upload/jobs", json=START_UPLOAD_APPROVAL)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["detail"]["reason"] == "preview_source_mismatch"
    audit = latest_audit(repository)
    assert audit["action"] == "upload.start"
    assert audit["result"] == "blocked"
    assert audit["error_code"] == "preview_source_mismatch"
    with repository.connect() as connection:
        count = connection.execute("SELECT COUNT(*) AS count FROM upload_jobs").fetchone()["count"]
    assert count == 0


def test_upload_job_start_rejects_timed_out_preview_without_creating_job(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    with repository.connect() as connection:
        connection.execute(
            """
            UPDATE preview_runs
            SET status = 'timed_out', db_status = 'not_checked',
                timeout_stage = 'db_match', error_code = 'timeout'
            WHERE preview_run_id = 'prv_done'
            """
        )
        connection.execute(
            "UPDATE preview_items SET status = 'risky', reason_code = 'timeout' WHERE preview_run_id = 'prv_done'"
        )
    app.dependency_overrides[get_upload_job_repository] = lambda: repository
    app.dependency_overrides[get_settings] = lambda: Settings(
        state_db_path=str(db_path),
        supabase_db_url=expected_db_url(),
        supabase_edge_url="http://127.0.0.1:55321/functions/v1/upload-metrics",
        supabase_anon_key=TEST_JWT,
    )
    client = TestClient(app)

    try:
        response = client.post("/api/upload/jobs", json=START_UPLOAD_APPROVAL)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["detail"]["reason"] == "preview_not_uploadable"
    assert response.json()["detail"]["status"] == "timed_out"
    with repository.connect() as connection:
        count = connection.execute("SELECT COUNT(*) AS count FROM upload_jobs").fetchone()["count"]
    assert count == 0
    audit = latest_audit(repository)
    assert audit["action"] == "upload.start"
    assert audit["result"] == "blocked"
    assert audit["error_code"] == "preview_not_uploadable"


def test_retry_no_retryable_files_writes_blocked_audit(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    repository.create_job_from_preview(
        job_id="upl_done",
        preview_run_id="prv_done",
        expected_target_rows=2,
        expected_target_files=1,
        options={},
        config_snapshot={},
        preview_gate_snapshot=PREVIEW_GATE_SNAPSHOT,
    )
    file_id = repository.list_job_files("upl_done")[0]["job_file_id"]
    repository.mark_file_completed(file_id, uploaded_rows=2, inserted_rows=2)
    repository.finish_job("upl_done", UploadJobStatus.succeeded)
    app.dependency_overrides[get_upload_job_repository] = lambda: repository
    app.dependency_overrides[get_settings] = lambda: Settings(
        state_db_path=str(db_path),
        supabase_db_url=expected_db_url(),
        supabase_edge_url="http://127.0.0.1:55321/functions/v1/upload-metrics",
        supabase_anon_key=TEST_JWT,
    )
    client = TestClient(app)

    try:
        response = client.post("/api/upload/jobs/upl_done/retry", json=RETRY_APPROVAL)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["detail"]["reason"] == "no_retryable_files"
    audit = latest_audit(repository)
    assert audit["action"] == "upload.retry"
    assert audit["result"] == "blocked"
    assert audit["error_code"] == "no_retryable_files"


def test_retry_rejects_missing_expected_remaining_rows_with_blocked_audit(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    repository.create_job_from_preview(
        job_id="upl_failed",
        preview_run_id="prv_done",
        expected_target_rows=2,
        expected_target_files=1,
        options={},
        config_snapshot={},
        preview_gate_snapshot=PREVIEW_GATE_SNAPSHOT,
    )
    file_id = repository.list_job_files("upl_failed")[0]["job_file_id"]
    repository.mark_file_failed(file_id, "upload_failed", "boom", 1)
    repository.finish_job("upl_failed", UploadJobStatus.failed)
    app.dependency_overrides[get_upload_job_repository] = lambda: repository
    app.dependency_overrides[get_settings] = lambda: Settings(
        state_db_path=str(db_path),
        supabase_db_url=expected_db_url(),
        supabase_edge_url="http://127.0.0.1:55321/functions/v1/upload-metrics",
        supabase_anon_key=TEST_JWT,
    )
    client = TestClient(app)

    try:
        response = client.post("/api/upload/jobs/upl_failed/retry", json={})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["detail"]["reason"] == "expected_remaining_rows_required"
    audit = latest_audit(repository)
    assert audit["action"] == "upload.retry"
    assert audit["result"] == "blocked"
    assert audit["error_code"] == "expected_remaining_rows_required"
    params = json.loads(audit["params_json_redacted"])
    assert params["retryOfJobId"] == "upl_failed"
    assert params["expectedRemainingRows"] is None
    with repository.connect() as connection:
        count = connection.execute("SELECT COUNT(*) AS count FROM upload_jobs WHERE retry_of_job_id = 'upl_failed'").fetchone()["count"]
    assert count == 0


def test_retry_rejects_edge_unreachable_runtime_readiness(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    repository.create_job_from_preview(
        job_id="upl_failed",
        preview_run_id="prv_done",
        expected_target_rows=2,
        expected_target_files=1,
        options={},
        config_snapshot={},
        preview_gate_snapshot=PREVIEW_GATE_SNAPSHOT,
    )
    file_id = repository.list_job_files("upl_failed")[0]["job_file_id"]
    repository.mark_file_failed(file_id, "upload_failed", "boom", 1)
    repository.finish_job("upl_failed", UploadJobStatus.failed)
    app.dependency_overrides[get_upload_job_repository] = lambda: repository
    app.dependency_overrides[get_settings] = lambda: upload_ready_settings(db_path)
    app.dependency_overrides[get_upload_runtime_readiness] = lambda: UploadRuntimeReadiness(
        ready=False,
        reason="edge_unreachable",
        detail={"apiStatus": "ready", "dbStatus": "ready", "edgeStatus": "unreachable"},
    )
    client = TestClient(app)

    try:
        response = client.post("/api/upload/jobs/upl_failed/retry", json=RETRY_APPROVAL)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["detail"]["reason"] == "edge_unreachable"
    audit = latest_audit(repository)
    assert audit["action"] == "upload.retry"
    assert audit["result"] == "blocked"
    assert audit["error_code"] == "edge_unreachable"
    with repository.connect() as connection:
        count = connection.execute("SELECT COUNT(*) AS count FROM upload_jobs WHERE retry_of_job_id = 'upl_failed'").fetchone()["count"]
    assert count == 0


def test_retry_rejects_expected_remaining_rows_mismatch_with_snapshot_counts(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    repository.create_job_from_preview(
        job_id="upl_failed",
        preview_run_id="prv_done",
        expected_target_rows=2,
        expected_target_files=1,
        options={},
        config_snapshot={},
        preview_gate_snapshot=PREVIEW_GATE_SNAPSHOT,
    )
    file_id = repository.list_job_files("upl_failed")[0]["job_file_id"]
    repository.mark_file_failed(file_id, "upload_failed", "boom", 1)
    repository.finish_job("upl_failed", UploadJobStatus.failed)
    app.dependency_overrides[get_upload_job_repository] = lambda: repository
    app.dependency_overrides[get_settings] = lambda: Settings(
        state_db_path=str(db_path),
        supabase_db_url=expected_db_url(),
        supabase_edge_url="http://127.0.0.1:55321/functions/v1/upload-metrics",
        supabase_anon_key=TEST_JWT,
    )
    client = TestClient(app)

    try:
        response = client.post(
            "/api/upload/jobs/upl_failed/retry",
            json={"expectedRemainingRows": 2, "expectedRetryFiles": 1},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["reason"] == "expected_remaining_rows_mismatch"
    assert detail["actualRemainingRows"] == 1
    assert detail["actualRetryFiles"] == 1
    audit = latest_audit(repository)
    assert audit["action"] == "upload.retry"
    assert audit["result"] == "blocked"
    assert audit["error_code"] == "expected_remaining_rows_mismatch"
    params = json.loads(audit["params_json_redacted"])
    assert params["expectedRemainingRows"] == 2
    assert params["actualRemainingRows"] == 1
    assert params["actualRetryFiles"] == 1
    with repository.connect() as connection:
        count = connection.execute("SELECT COUNT(*) AS count FROM upload_jobs WHERE retry_of_job_id = 'upl_failed'").fetchone()["count"]
    assert count == 0


def test_retry_success_records_expected_and_actual_counts(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    repository.create_job_from_preview(
        job_id="upl_failed",
        preview_run_id="prv_done",
        expected_target_rows=2,
        expected_target_files=1,
        options={},
        config_snapshot={},
        preview_gate_snapshot=PREVIEW_GATE_SNAPSHOT,
    )
    file_id = repository.list_job_files("upl_failed")[0]["job_file_id"]
    repository.mark_file_failed(file_id, "upload_failed", "boom", 1)
    repository.finish_job("upl_failed", UploadJobStatus.failed)
    app.dependency_overrides[get_upload_job_repository] = lambda: repository
    app.dependency_overrides[get_settings] = lambda: Settings(
        state_db_path=str(db_path),
        supabase_db_url=expected_db_url(),
        supabase_edge_url="http://127.0.0.1:55321/functions/v1/upload-metrics",
        supabase_anon_key=TEST_JWT,
    )
    submitted: list[str] = []
    monkeypatch.setattr(
        "backend.app.api.upload_jobs.executor.submit",
        lambda _fn, job_id: submitted.append(job_id),
    )
    client = TestClient(app)

    try:
        response = client.post("/api/upload/jobs/upl_failed/retry", json=RETRY_APPROVAL)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    assert submitted == [body["jobId"]]
    audit = latest_audit(repository)
    assert audit["action"] == "upload.retry"
    assert audit["result"] == "success"
    params = json.loads(audit["params_json_redacted"])
    assert params["expectedRemainingRows"] == 1
    assert params["actualRemainingRows"] == 1
    assert params["expectedRetryFiles"] == 1
    assert params["actualRetryFiles"] == 1


def test_upload_job_detail_exposes_accepted_rows_with_legacy_inserted_alias(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    repository.create_job_from_preview(
        job_id="upl_counts",
        preview_run_id="prv_done",
        expected_target_rows=2,
        expected_target_files=1,
        options={},
        config_snapshot={},
        preview_gate_snapshot=PREVIEW_GATE_SNAPSHOT,
    )
    file_id = repository.list_job_files("upl_counts")[0]["job_file_id"]
    repository.mark_file_completed(file_id, uploaded_rows=2, inserted_rows=2)
    repository.finish_job("upl_counts", UploadJobStatus.succeeded)
    app.dependency_overrides[get_upload_job_repository] = lambda: repository
    client = TestClient(app)

    try:
        response = client.get("/api/upload/jobs/upl_counts")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["job"]["summary"]["acceptedRows"] == 2
    assert body["job"]["summary"]["insertedRows"] == 2
    assert body["files"][0]["acceptedRows"] == 2
    assert body["files"][0]["insertedRows"] == 2
    succeeded_event = next(event for event in body["events"] if event["eventType"] == "file.succeeded")
    assert succeeded_event["data"]["acceptedRows"] == 2
    assert succeeded_event["data"]["insertedRows"] == 2


def test_upload_job_events_replays_after_seq(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    repository.create_job_from_preview(
        job_id="upl_events",
        preview_run_id="prv_done",
        expected_target_rows=2,
        expected_target_files=1,
        options={},
        config_snapshot={},
        preview_gate_snapshot=PREVIEW_GATE_SNAPSHOT,
    )
    repository.append_event("upl_events", event_type="log.info", level="info", message="second")
    repository.finish_job("upl_events", UploadJobStatus.succeeded)
    app.dependency_overrides[get_upload_job_repository] = lambda: repository
    client = TestClient(app)

    try:
        with client.stream("GET", "/api/upload/jobs/upl_events/events?afterSeq=1") as response:
            body = "".join(response.iter_text())
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "id: 2" in body
    assert "log.info" in body


def latest_audit(repository: UploadJobRepository):
    with repository.connect() as connection:
        return connection.execute("SELECT * FROM audit_log ORDER BY audit_id DESC LIMIT 1").fetchone()
