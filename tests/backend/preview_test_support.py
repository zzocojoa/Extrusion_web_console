from __future__ import annotations


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
