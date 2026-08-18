from ipaddress import IPv4Address

import pytest
from pydantic import ValidationError

from validation_experiment.domain import CanonicalDeviceRecord


def valid_record_data() -> dict[str, object]:
    return {
        "name": "DEVICE-001",
        "hostname": "HOST-001",
        "serial_number": "SERIAL-001",
        "hardware_model": "FortiGate-60F",
        "management_ip": IPv4Address("192.0.2.10"),
        "ha_state": "standalone",
        "ha_group_name": None,
        "ha_members": [],
    }


def test_valid_canonical_device_record_can_be_created() -> None:
    record = CanonicalDeviceRecord(**valid_record_data())

    assert record.name == "DEVICE-001"
    assert record.management_ip == IPv4Address("192.0.2.10")
    assert record.ha_members == []


def test_hostname_may_be_none() -> None:
    data = valid_record_data()
    data["hostname"] = None

    record = CanonicalDeviceRecord(**data)

    assert record.hostname is None


def test_invalid_management_ip_is_rejected() -> None:
    data = valid_record_data()
    data["management_ip"] = "not-an-ip-address"

    with pytest.raises(ValidationError):
        CanonicalDeviceRecord(**data)


def test_invalid_ha_state_is_rejected() -> None:
    data = valid_record_data()
    data["ha_state"] = "unknown"

    with pytest.raises(ValidationError):
        CanonicalDeviceRecord(**data)


def test_integer_hardware_model_is_not_coerced_to_string() -> None:
    data = valid_record_data()
    data["hardware_model"] = 60

    with pytest.raises(ValidationError):
        CanonicalDeviceRecord(**data)


def test_missing_required_fields_are_rejected() -> None:
    with pytest.raises(ValidationError):
        CanonicalDeviceRecord()
