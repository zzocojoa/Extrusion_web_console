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


@pytest.mark.parametrize("range_mode", ["last_7_days", "last_30_days", "folder_all"])
def test_preview_create_request_accepts_extended_range_modes_without_custom_dates(
    range_mode: str,
) -> None:
    schema = _schema_module()

    request = schema.PreviewCreateRequest.model_validate(
        {"rangeMode": range_mode, "sources": ["plc"]}
    )

    assert _enum_value(request.range_mode) == range_mode
    assert request.start_date is None
    assert request.end_date is None
    assert request.model_dump(by_alias=True)["rangeMode"] == range_mode


def test_preview_default_profile_keeps_short_interactive_timeout_budget() -> None:
    schema = _schema_module()

    request = schema.PreviewCreateRequest.model_validate(
        {"rangeMode": "today", "sources": ["plc"]}
    )

    assert _enum_value(request.options.profile) == "default"
    assert request.options.max_files == 500
    assert request.options.max_run_seconds == 120
    assert request.options.max_file_seconds == 30
    assert request.options.force_full_scan is False


def test_stage3_profile_a_bounded_full_scan_applies_bounded_timeout_budget() -> None:
    schema = _schema_module()

    request = schema.PreviewCreateRequest.model_validate(
        {
            "rangeMode": "custom",
            "startDate": "2026-05-23",
            "endDate": "2026-05-23",
            "sources": ["plc"],
            "options": {
                "profile": "stage3_profile_a_bounded_full_scan",
                "maxFiles": 500,
                "maxRunSeconds": 120,
                "maxFileSeconds": 30,
                "forceFullScan": False,
            },
        }
    )

    assert _enum_value(request.options.profile) == "stage3_profile_a_bounded_full_scan"
    assert request.options.max_files == 3
    assert request.options.max_run_seconds == 300
    assert request.options.max_file_seconds == 120
    assert request.options.force_full_scan is True

    api_payload = request.model_dump(by_alias=True)
    assert api_payload["options"]["profile"] == "stage3_profile_a_bounded_full_scan"
    assert api_payload["options"]["maxFiles"] == 3
    assert api_payload["options"]["maxRunSeconds"] == 300
    assert api_payload["options"]["maxFileSeconds"] == 120
    assert api_payload["options"]["forceFullScan"] is True


def test_large_source_operational_profile_applies_long_preview_budget() -> None:
    schema = _schema_module()

    request = schema.PreviewCreateRequest.model_validate(
        {
            "rangeMode": "custom",
            "startDate": "2026-01-01",
            "endDate": "2026-01-31",
            "sources": ["plc"],
            "options": {
                "profile": "large_source_operational",
                "chunkRows": 20000,
                "maxFiles": 3,
                "maxRunSeconds": 120,
                "maxFileSeconds": 30,
                "forceFullScan": True,
            },
        }
    )

    assert _enum_value(request.options.profile) == "large_source_operational"
    assert request.options.max_files == 500
    assert request.options.chunk_rows == 1000
    assert request.options.max_run_seconds == 900
    assert request.options.max_file_seconds == 300
    assert request.options.force_full_scan is False

    api_payload = request.model_dump(by_alias=True)
    assert api_payload["options"]["profile"] == "large_source_operational"
    assert api_payload["options"]["maxFiles"] == 500
    assert api_payload["options"]["chunkRows"] == 1000
    assert api_payload["options"]["maxRunSeconds"] == 900
    assert api_payload["options"]["maxFileSeconds"] == 300
    assert api_payload["options"]["forceFullScan"] is False


def test_preview_run_dto_serializes_applied_profile_metadata() -> None:
    schema = _schema_module()

    dto = schema.PreviewRunDto.model_validate(
        {
            "previewRunId": "prv_test",
            "status": "succeeded",
            "requestedAt": "2026-06-17T00:00:00+00:00",
            "dbStatus": "reachable",
            "summary": {"target": 1, "uploadRows": 10, "targetRows": 4, "partialOverlapRows": 6},
            "requestedProfile": "default",
            "appliedProfile": "large_source_operational",
            "autoProfileReason": "operational_source_class",
        }
    )

    payload = dto.model_dump(by_alias=True)
    assert payload["requestedProfile"] == "default"
    assert payload["appliedProfile"] == "large_source_operational"
    assert payload["autoProfileReason"] == "operational_source_class"
    assert payload["summary"]["targetRows"] == 4
    assert payload["summary"]["partialOverlapRows"] == 6


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
