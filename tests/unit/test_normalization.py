import json
from ipaddress import IPv4Address
from pathlib import Path

import pytest

from validation_experiment.domain import CanonicalDeviceRecord
from validation_experiment.normalization import normalize_device_record


FIXTURE_PATH = (
    Path(__file__).parents[2] / "data" / "fixtures" / "golden_devices.json"
)


def load_fixtures() -> dict[str, dict[str, object]]:
    fixture_entries = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    return {entry["fixture_id"]: entry["raw"] for entry in fixture_entries}


def test_all_five_golden_fixtures_can_be_loaded() -> None:
    fixtures = load_fixtures()

    assert list(fixtures) == ["F01", "F02", "F03", "F04", "F05"]


@pytest.mark.parametrize("fixture_id", ["F01", "F02", "F03", "F04", "F05"])
def test_all_golden_fixtures_can_be_normalized(fixture_id: str) -> None:
    record = normalize_device_record(load_fixtures()[fixture_id])

    assert isinstance(record, CanonicalDeviceRecord)


def test_f01_is_normalized_to_standalone_record() -> None:
    record = normalize_device_record(load_fixtures()["F01"])

    assert record.name == "DEVICE-001"
    assert record.hostname == "HOST-001"
    assert record.serial_number == "SERIAL-001"
    assert record.hardware_model == "FortiGate-60F"
    assert record.management_ip == IPv4Address("192.0.2.10")
    assert record.ha_state == "standalone"
    assert record.ha_group_name is None
    assert record.ha_members == []


def test_f02_is_normalized_to_clustered_record_with_two_members() -> None:
    record = normalize_device_record(load_fixtures()["F02"])

    assert record.ha_state == "clustered"
    assert record.ha_group_name == "CLUSTER-001"
    assert record.ha_members == ["SERIAL-005-A", "SERIAL-005-B"]


def test_f05_retains_forticlient_ems_and_normalizes_empty_hostname() -> None:
    record = normalize_device_record(load_fixtures()["F05"])

    assert record.hostname is None
    assert record.hardware_model == "FortiClient-EMS"


def test_unknown_ha_mode_raises_explicit_error() -> None:
    raw = {**load_fixtures()["F01"], "ha_mode": 7}

    with pytest.raises(ValueError, match="Unknown ha_mode: 7"):
        normalize_device_record(raw)


def test_empty_ha_group_name_is_normalized_to_none() -> None:
    record = normalize_device_record(load_fixtures()["F03"])

    assert record.ha_group_name is None
