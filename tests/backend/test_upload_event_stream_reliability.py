from pathlib import Path

from backend.app.db.upload_job_repository import UploadJobRepository
from backend.app.schemas.upload_jobs import UploadJobStatus
from backend.app.services.upload_event_stream import (
    MIN_REPLAY_BATCH_SIZE,
    SQLITE_MAX_INTEGER,
    read_upload_event_batch,
    resolve_upload_event_cursor,
    upload_event_replay_batch_size,
)
from tests.backend.test_upload_jobs_repository_contract import PREVIEW_GATE_SNAPSHOT, create_preview_with_items


def create_upload_job(db_path: Path, job_id: str = "upl_stream") -> UploadJobRepository:
    create_preview_with_items(db_path)
    repository = UploadJobRepository(db_path)
    repository.create_job_from_preview(
        job_id=job_id,
        preview_run_id="prv_done",
        expected_target_rows=2,
        expected_target_files=1,
        options={},
        config_snapshot={},
        preview_gate_snapshot=PREVIEW_GATE_SNAPSHOT,
    )
    return repository


def test_resolve_upload_event_cursor_uses_highest_valid_cursor() -> None:
    assert resolve_upload_event_cursor(7, "12") == 12
    assert resolve_upload_event_cursor(12, "7") == 12
    assert resolve_upload_event_cursor(7, None) == 7
    assert resolve_upload_event_cursor(-1, "2") == 2
    assert resolve_upload_event_cursor(7, str(SQLITE_MAX_INTEGER)) == SQLITE_MAX_INTEGER


def test_resolve_upload_event_cursor_ignores_malformed_or_non_ascii_ids() -> None:
    assert resolve_upload_event_cursor(7, "-1") == 7
    assert resolve_upload_event_cursor(7, " 12") == 7
    assert resolve_upload_event_cursor(7, "\u00b2") == 7
    assert resolve_upload_event_cursor(7, "not-a-seq") == 7
    assert resolve_upload_event_cursor(7, str(SQLITE_MAX_INTEGER + 1)) == 7
    assert resolve_upload_event_cursor(7, "9" * 5_000) == 7


def test_requested_tail_cannot_reduce_server_replay_batch_size() -> None:
    assert upload_event_replay_batch_size(1) == MIN_REPLAY_BATCH_SIZE
    assert upload_event_replay_batch_size(MIN_REPLAY_BATCH_SIZE) == MIN_REPLAY_BATCH_SIZE
    assert upload_event_replay_batch_size(500) == 500


def test_terminal_batch_closes_only_after_persisted_events_are_drained(tmp_path: Path) -> None:
    repository = create_upload_job(tmp_path / "state.db")
    repository.append_event("upl_stream", event_type="log.info", level="info", message="persisted")
    repository.finish_job("upl_stream", UploadJobStatus.succeeded)

    first = read_upload_event_batch(repository, "upl_stream", after_seq=0, limit=500)
    closed = read_upload_event_batch(repository, "upl_stream", after_seq=first.next_cursor, limit=500)

    assert first.events
    assert first.should_close is False
    assert closed.events == ()
    assert closed.should_close is True


def test_empty_active_batch_waits_but_missing_job_closes(tmp_path: Path) -> None:
    repository = create_upload_job(tmp_path / "state.db")
    cursor = repository.latest_event_seq("upl_stream")

    active = read_upload_event_batch(repository, "upl_stream", after_seq=cursor, limit=500)
    with repository.connect() as connection:
        connection.execute("DELETE FROM upload_jobs WHERE job_id = ?", ("upl_stream",))
    missing = read_upload_event_batch(repository, "upl_stream", after_seq=cursor, limit=500)

    assert active.events == ()
    assert active.should_close is False
    assert missing.events == ()
    assert missing.should_close is True


def test_synthetic_soak_reconnects_without_event_loss_or_duplicates(tmp_path: Path) -> None:
    repository = create_upload_job(tmp_path / "state.db", job_id="upl_soak")
    for index in range(1_000):
        repository.append_event(
            "upl_soak",
            event_type="log.info",
            level="info",
            message=f"synthetic-{index}",
        )
    repository.finish_job("upl_soak", UploadJobStatus.succeeded)
    expected = [int(row["seq"]) for row in repository.list_events("upl_soak", limit=2_000)]

    cursor = 0
    observed: list[int] = []
    reconnect_pattern = (1, 7, 19, 3, 31, 11)
    reconnect_count = 0
    while True:
        batch = read_upload_event_batch(repository, "upl_soak", after_seq=cursor, limit=47)
        if not batch.events:
            assert batch.should_close is True
            break
        take = min(reconnect_pattern[reconnect_count % len(reconnect_pattern)], len(batch.events))
        delivered = batch.events[:take]
        observed.extend(int(row["seq"]) for row in delivered)
        cursor = int(delivered[-1]["seq"])
        reconnect_count += 1

    assert reconnect_count > 50
    assert observed == expected
    assert len(observed) == len(set(observed))
