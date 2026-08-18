import json
from ipaddress import IPv4Address
from pathlib import Path

import pytest

from validation_experiment.normalization import normalize_device_record
from validation_experiment.validation.baseline import validate_baseline


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


@pytest.mark.parametrize("fixture_id", ["F01", "F02", "F03", "F04", "F05"])
def test_v1_accepts_all_golden_fixtures(fixture_id: str) -> None:
    result = validate_baseline(normalized_fixture(fixture_id))

    assert result.is_valid is True
    assert result.violations == ()
    assert result.canonical_record is not None


def test_v1_converts_f01_management_ip_in_canonical_record() -> None:
    result = validate_baseline(normalized_fixture("F01"))

    assert result.canonical_record is not None
    assert result.canonical_record.management_ip == IPv4Address("192.0.2.10")


def test_v1_accepts_f02_cluster_with_group_and_two_members() -> None:
    result = validate_baseline(normalized_fixture("F02"))

    assert result.is_valid is True
    assert result.canonical_record is not None
    assert result.canonical_record.ha_group_name == "CLUSTER-001"
    assert result.canonical_record.ha_members == ["SERIAL-005-A", "SERIAL-005-B"]


def test_v1_keeps_f05_forticlient_ems_without_eligibility_filtering() -> None:
    result = validate_baseline(normalized_fixture("F05"))

    assert result.is_valid is True
    assert result.violations == ()
    assert result.canonical_record is not None
    assert result.canonical_record.hardware_model == "FortiClient-EMS"
