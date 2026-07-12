from __future__ import annotations

from concurrent.futures import Future
from typing import Any, Callable


def approval_scope(
    *,
    source_class: str = "local",
    range_mode: str = "today",
    start_date: str | None = None,
    end_date: str | None = None,
    applied_profile: str = "default",
) -> dict[str, object]:
    return {
        "expectedSourceClasses": {"plc": source_class},
        "expectedRangeMode": range_mode,
        "expectedStartDate": start_date,
        "expectedEndDate": end_date,
        "expectedAppliedProfile": applied_profile,
    }


def pending_future() -> Future[None]:
    return Future()


def run_in_future(function: Callable[..., Any], *args: Any) -> Future[None]:
    future: Future[None] = Future()
    try:
        function(*args)
    except Exception as error:
        future.set_exception(error)
    else:
        future.set_result(None)
    return future
