"""Normalization at the input boundary of the experiment."""


class NormalizationError(ValueError):
    """A source value cannot be mapped to the normalized representation."""


def normalize_device_record(raw: dict[str, object]) -> dict[str, object]:
    """Map selected source fields without validating domain-model constraints."""

    ha_mode = raw["ha_mode"]
    if type(ha_mode) is int and ha_mode == 0:
        ha_state = "standalone"
    elif type(ha_mode) is int and ha_mode == 1:
        ha_state = "clustered"
    else:
        raise NormalizationError(f"Unknown ha_mode: {ha_mode!r}")

    ha_slave = raw["ha_slave"]
    if ha_slave is None:
        ha_members = []
    elif isinstance(ha_slave, list):
        ha_members = [member["sn"] for member in ha_slave]
    else:
        raise TypeError("ha_slave must be a list or None")

    return {
        "name": raw["name"],
        "hostname": None if raw["hostname"] == "" else raw["hostname"],
        "serial_number": raw["sn"],
        "hardware_model": raw["platform_str"],
        "management_ip": raw["ip"],
        "ha_state": ha_state,
        "ha_group_name": (
            None if raw["ha_group_name"] == "" else raw["ha_group_name"]
        ),
        "ha_members": ha_members,
    }
