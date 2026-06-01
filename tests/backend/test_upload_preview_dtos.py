from __future__ import annotations

from datetime import date
from importlib import import_module
from types import ModuleType

import pytest
from pydantic import ValidationError


def _schema_module() -> ModuleType:
    try:
        return import_module("backend.app.schemas.upload_preview")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Expected backend.app.schemas.upload_preview with the Upload Preview DTOs "
            "from docs/07_upload_preview_plan.md"
        )
        raise exc


def _enum_value(value: object) -> object:
    return getattr(value, "value", value)


def test_preview_create_request_accepts_camel_case_api_payload_and_defaults() -> None:
    schema = _schema_module()

    request = schema.PreviewCreateRequest.model_validate(
        {
            "rangeMode": "last_2_days",
            "sources": ["plc"],
            "options": {
                "stableLagMinutes": 5,
                "chunkRows": 5000,
                "maxRunSeconds": 30,
                "forceFullScan": True,
            },
        }
    )

    assert _enum_value(request.range_mode) == "last_2_days"
    assert [_enum_value(source) for source in request.sources] == ["plc"]
    assert request.start_date is None
    assert request.end_date is None
    assert request.options.stable_lag_minutes == 5
    assert request.options.chunk_rows == 5000
    assert request.options.max_run_seconds == 30
    assert request.options.force_full_scan is True

    api_payload = request.model_dump(by_alias=True)
    assert "rangeMode" in api_payload
    assert "stableLagMinutes" in api_payload["options"]
    assert "forceFullScan" in api_payload["options"]


def test_preview_create_request_custom_range_requires_both_dates_and_valid_order() -> None:
    schema = _schema_module()

    with pytest.raises(ValidationError):
        schema.PreviewCreateRequest.model_validate({"rangeMode": "custom", "sources": ["plc"]})

    with pytest.raises(ValidationError):
        schema.PreviewCreateRequest.model_validate(
            {
                "rangeMode": "custom",
                "startDate": date(2026, 6, 2),
                "endDate": date(2026, 6, 1),
                "sources": ["plc"],
            }
        )

    request = schema.PreviewCreateRequest.model_validate(
        {
            "rangeMode": "custom",
            "startDate": "2026-06-01",
            "endDate": "2026-06-02",
            "sources": ["plc"],
        }
    )

    assert request.start_date == date(2026, 6, 1)
    assert request.end_date == date(2026, 6, 2)


@pytest.mark.parametrize(
    "options",
    [
        {"stableLagMinutes": -1},
        {"sampleRows": 19},
        {"chunkRows": 999},
        {"maxFiles": 0},
        {"maxRunSeconds": 9},
        {"maxFileSeconds": 4},
    ],
)
def test_preview_options_reject_values_outside_backend_limits(options: dict[str, int]) -> None:
    schema = _schema_module()

    with pytest.raises(ValidationError):
        schema.PreviewCreateRequest.model_validate(
            {"rangeMode": "today", "sources": ["plc"], "options": options}
        )


def test_preview_request_rejects_arbitrary_filesystem_paths() -> None:
    schema = _schema_module()

    with pytest.raises(ValidationError):
        schema.PreviewCreateRequest.model_validate(
            {
                "rangeMode": "today",
                "sources": ["plc"],
                "path": "C:\\Users\\operator\\Desktop\\unexpected.csv",
            }
        )
