import sqlite3
from dataclasses import dataclass

from backend.app.db.upload_job_repository import ACTIVE_JOB_STATUSES, UploadJobRepository


SQLITE_MAX_INTEGER = (1 << 63) - 1


@dataclass(frozen=True)
class UploadEventBatch:
    events: tuple[sqlite3.Row, ...]
    next_cursor: int
    should_close: bool


def resolve_upload_event_cursor(after_seq: int, last_event_id: str | None) -> int:
    """Resolve the persisted event cursor without trusting a malformed SSE header."""
    cursor = max(0, after_seq)
    if not last_event_id or not last_event_id.isascii() or not last_event_id.isdecimal():
        return cursor
    try:
        parsed_last_event_id = int(last_event_id, 10)
    except ValueError:
        return cursor
    if parsed_last_event_id > SQLITE_MAX_INTEGER:
        return cursor
    return max(cursor, parsed_last_event_id)


def read_upload_event_batch(
    repository: UploadJobRepository,
    job_id: str,
    *,
    after_seq: int,
    limit: int,
) -> UploadEventBatch:
    """Read the next persisted batch and decide whether an idle stream is terminal."""
    cursor = max(0, after_seq)
    snapshot_events, snapshot_status = repository.read_event_stream_snapshot(
        job_id,
        after_seq=cursor,
        limit=limit,
    )
    events = tuple(snapshot_events)
    if events:
        return UploadEventBatch(
            events=events,
            next_cursor=int(events[-1]["seq"]),
            should_close=False,
        )

    should_close = snapshot_status is None or snapshot_status not in ACTIVE_JOB_STATUSES
    return UploadEventBatch(events=(), next_cursor=cursor, should_close=should_close)
