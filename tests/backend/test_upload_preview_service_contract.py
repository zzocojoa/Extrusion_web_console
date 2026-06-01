from __future__ import annotations

from importlib import import_module
from types import ModuleType

import pytest


def _service_module() -> ModuleType:
    try:
        return import_module("backend.app.services.upload_preview")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Expected backend.app.services.upload_preview with PreviewService "
            "classification helpers"
        )
        raise exc


def _candidate_classifiers(module: ModuleType) -> list[object]:
    classifiers: list[object] = []
    for name in (
        "classify_reconciliation",
        "classify_preview_item",
        "classify_item_reconciliation",
    ):
        classifier = getattr(module, name, None)
        if classifier is not None:
            classifiers.append(classifier)

    preview_service = getattr(module, "PreviewService", None)
    if preview_service is not None:
        for name in (
            "classify_reconciliation",
            "classify_preview_item",
            "classify_item_reconciliation",
        ):
            classifier = getattr(preview_service, name, None)
            if classifier is not None:
                classifiers.append(classifier)

    assert classifiers, (
        "Preview service must expose a classification helper so exact-key and "
        "DB-failure behavior can be tested without starting real upload work"
    )
    return classifiers


def _classify(module: ModuleType, **kwargs: object) -> object:
    errors: list[Exception] = []
    for classifier in _candidate_classifiers(module):
        try:
            return classifier(**kwargs)
        except TypeError as exc:
            errors.append(exc)
            try:
                return classifier(kwargs)
            except TypeError as nested_exc:
                errors.append(nested_exc)

    details = "; ".join(str(error) for error in errors)
    pytest.fail(f"No preview classifier accepted the contract kwargs: {details}")


def _field(result: object, *names: str) -> object:
    for name in names:
        if isinstance(result, dict) and name in result:
            return result[name]
        if hasattr(result, name):
            return getattr(result, name)

    available = result.keys() if isinstance(result, dict) else dir(result)
    pytest.fail(f"Result {result!r} is missing any of {names}; available={available}")


def _value(value: object) -> object:
    return getattr(value, "value", value)


def test_service_classifies_exact_reconciliation_matrix() -> None:
    module = _service_module()
    key_a = ("2026-06-01T09:00:00+09:00", "extruder_plc")
    key_b = ("2026-06-01T09:01:00+09:00", "extruder_plc")

    target = _classify(module, local_keys={key_a, key_b}, matched_keys=set())
    assert _value(_field(target, "status")) == "target"
    assert _field(target, "db_match_count", "dbMatchCount") == 0

    already = _classify(module, local_keys={key_a, key_b}, matched_keys={key_a, key_b})
    assert _value(_field(already, "status")) == "already_in_db"
    assert _field(already, "upload_row_estimate", "uploadRowEstimate") == 0

    partial = _classify(module, local_keys={key_a, key_b}, matched_keys={key_a})
    assert _value(_field(partial, "status")) == "partial_overlap"
    assert _field(partial, "db_match_count", "dbMatchCount") == 1
    assert _field(partial, "upload_row_estimate", "uploadRowEstimate") == 1


def test_service_marks_db_unreachable_as_risky_without_upload_estimate() -> None:
    module = _service_module()
    key = ("2026-06-01T09:00:00+09:00", "extruder_integrated")

    result = _classify(
        module,
        local_keys={key},
        matched_keys=None,
        db_status="unreachable",
        error_code="db_unreachable",
    )

    assert _value(_field(result, "status")) == "risky"
    assert _field(result, "reason_code", "reasonCode") == "db_unreachable"
    assert _field(result, "upload_row_estimate", "uploadRowEstimate") in (0, None)


def test_service_does_not_treat_later_device_timestamp_as_already_in_db() -> None:
    module = _service_module()
    csv_key = ("2026-06-01T09:00:00+09:00", "extruder_plc")
    later_db_key_same_device = ("2026-06-01T10:00:00+09:00", "extruder_plc")

    result = _classify(
        module,
        local_keys={csv_key},
        matched_keys={later_db_key_same_device},
    )

    assert _value(_field(result, "status")) == "target"
    assert _field(result, "db_match_count", "dbMatchCount") == 0
    assert _field(result, "upload_row_estimate", "uploadRowEstimate") == 1
