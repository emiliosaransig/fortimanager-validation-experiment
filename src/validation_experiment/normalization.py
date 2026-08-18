"""Normalization at the input boundary of the experiment."""

from ipaddress import IPv4Address
from typing import Any

from validation_experiment.domain import CanonicalDeviceRecord


def normalize_device_record(raw: dict[str, Any]) -> CanonicalDeviceRecord:
    """Normalize the selected fields of an anonymized FortiManager record."""

    ha_mode = raw["ha_mode"]
    if type(ha_mode) is int and ha_mode == 0:
        ha_state = "standalone"
    elif type(ha_mode) is int and ha_mode == 1:
        ha_state = "clustered"
    else:
        raise ValueError(f"Unknown ha_mode: {ha_mode!r}")

    ha_slave = raw["ha_slave"]
    if ha_slave is None:
        ha_members = []
    elif isinstance(ha_slave, list):
        ha_members = [member["sn"] for member in ha_slave]
    else:
        raise TypeError("ha_slave must be a list or None")

    management_ip = raw["ip"]
    if not isinstance(management_ip, str):
        raise TypeError("ip must be a string")

    return CanonicalDeviceRecord(
        name=raw["name"],
        hostname=None if raw["hostname"] == "" else raw["hostname"],
        serial_number=raw["sn"],
        hardware_model=raw["platform_str"],
        management_ip=IPv4Address(management_ip),
        ha_state=ha_state,
        ha_group_name=(
            None if raw["ha_group_name"] == "" else raw["ha_group_name"]
        ),
        ha_members=ha_members,
    )
