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


def normalized_fixture(fixture_id: str) -> dict[str, object]:
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
    assert result.canonical_record is None


def test_r06_rejects_cluster_without_ha_group_name() -> None:
    record = normalized_fixture("F02")
    record["ha_group_name"] = None

    assert_only_rules(validate_baseline(record), ("R06",))


@pytest.mark.parametrize("ha_members", [[], ["SERIAL-A"]])
def test_r07_rejects_cluster_with_fewer_than_two_members(
    ha_members: list[str],
) -> None:
    record = normalized_fixture("F02")
    record["ha_members"] = ha_members

    assert_only_rules(validate_baseline(record), ("R07",))


def test_r07_rejects_cluster_with_missing_members() -> None:
    record = normalized_fixture("F02")
    record.pop("ha_members")

    assert_only_rules(validate_baseline(record), ("R07",))


def test_r08_rejects_standalone_with_ha_group_name() -> None:
    record = normalized_fixture("F01")
    record["ha_group_name"] = "SYNTHETIC-CLUSTER"

    assert_only_rules(validate_baseline(record), ("R08",))


def test_r08_rejects_standalone_with_ha_members() -> None:
    record = normalized_fixture("F01")
    record["ha_members"] = ["SYNTHETIC-MEMBER"]

    assert_only_rules(validate_baseline(record), ("R08",))


def test_r08_is_reported_once_when_both_standalone_conditions_fail() -> None:
    record = normalized_fixture("F01")
    record["ha_group_name"] = "SYNTHETIC-CLUSTER"
    record["ha_members"] = ["SYNTHETIC-MEMBER"]

    assert_only_rules(validate_baseline(record), ("R08",))


def test_invalid_ha_state_does_not_create_cross_field_follow_up_errors() -> None:
    record = normalized_fixture("F02")
    record["ha_state"] = "unknown"
    record["ha_group_name"] = None
    record["ha_members"] = []

    assert_only_rules(validate_baseline(record), ("R05",))


def test_multiple_independent_violations_are_collected() -> None:
    record = normalized_fixture("F01")
    record["name"] = ""
    record["serial_number"] = ""

    assert_only_rules(validate_baseline(record), ("R01", "R02"))
