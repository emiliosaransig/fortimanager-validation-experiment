import json
from pathlib import Path

import pytest

from validation_experiment.normalization import normalize_device_record
from validation_experiment.validation.baseline import (
    BaselineValidationResult,
    validate_baseline,
)


FIXTURE_PATH = (
    Path(__file__).parents[2] / "data" / "fixtures" / "golden_devices.json"
)


def normalized_fixture(fixture_id: str = "F01") -> dict[str, object]:
    fixture_entries = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    raw = next(
        entry["raw"]
        for entry in fixture_entries
        if entry["fixture_id"] == fixture_id
    )
    return normalize_device_record(raw)


def assert_only_rules(
    result: BaselineValidationResult, expected_rule_ids: tuple[str, ...]
) -> None:
    assert result.is_valid is False
    assert tuple(violation.rule_id for violation in result.violations) == (
        expected_rule_ids
    )
    assert all(violation.message for violation in result.violations)
    assert result.canonical_record is None


def test_r01_rejects_missing_name() -> None:
    record = normalized_fixture()
    record.pop("name")

    assert_only_rules(validate_baseline(record), ("R01",))


@pytest.mark.parametrize("invalid_name", [None, "", 123])
def test_r01_rejects_none_empty_or_non_string_name(invalid_name: object) -> None:
    record = normalized_fixture()
    record["name"] = invalid_name

    assert_only_rules(validate_baseline(record), ("R01",))


def test_r02_rejects_missing_serial_number() -> None:
    record = normalized_fixture()
    record.pop("serial_number")

    assert_only_rules(validate_baseline(record), ("R02",))


@pytest.mark.parametrize("invalid_serial_number", [None, "", 123])
def test_r02_rejects_none_empty_or_non_string_serial_number(
    invalid_serial_number: object,
) -> None:
    record = normalized_fixture()
    record["serial_number"] = invalid_serial_number

    assert_only_rules(validate_baseline(record), ("R02",))


@pytest.mark.parametrize("invalid_hardware_model", [None, "", 123])
def test_r03_rejects_none_empty_or_non_string_hardware_model(
    invalid_hardware_model: object,
) -> None:
    record = normalized_fixture()
    record["hardware_model"] = invalid_hardware_model

    assert_only_rules(validate_baseline(record), ("R03",))


def test_r03_accepts_forticlient_ems_string() -> None:
    record = normalized_fixture()
    record["hardware_model"] = "FortiClient-EMS"

    result = validate_baseline(record)

    assert result.is_valid is True
    assert result.violations == ()


@pytest.mark.parametrize("invalid_management_ip", [None, 123, "999.10.20.30"])
def test_r04_rejects_none_non_string_or_invalid_ipv4(
    invalid_management_ip: object,
) -> None:
    record = normalized_fixture()
    record["management_ip"] = invalid_management_ip

    assert_only_rules(validate_baseline(record), ("R04",))


def test_r04_rejects_missing_management_ip() -> None:
    record = normalized_fixture()
    record.pop("management_ip")

    assert_only_rules(validate_baseline(record), ("R04",))


@pytest.mark.parametrize("invalid_ha_state", [None, 1, "unknown"])
def test_r05_rejects_none_non_string_or_unknown_ha_state(
    invalid_ha_state: object,
) -> None:
    record = normalized_fixture()
    record["ha_state"] = invalid_ha_state

    assert_only_rules(validate_baseline(record), ("R05",))


def test_r05_rejects_missing_ha_state_without_cross_field_follow_up() -> None:
    record = normalized_fixture()
    record.pop("ha_state")

    assert_only_rules(validate_baseline(record), ("R05",))
