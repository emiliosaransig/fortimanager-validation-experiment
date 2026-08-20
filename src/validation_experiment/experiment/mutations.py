"""Deterministic single-fault mutations M01–M10."""

from collections.abc import Mapping


def apply_mutation(
    record: Mapping[str, object], mutation_id: str
) -> dict[str, object]:
    """Apply one frozen mutation to a copy of a normalized record."""

    mutated = dict(record)

    match mutation_id:
        case "M01":
            mutated.pop("name")
        case "M02":
            mutated.pop("serial_number")
        case "M03":
            mutated.pop("management_ip")
        case "M04":
            mutated["hardware_model"] = 123
        case "M05":
            mutated["management_ip"] = "999.10.20.30"
        case "M06":
            mutated["ha_state"] = "unknown"
        case "M07":
            mutated["ha_group_name"] = None
        case "M08":
            mutated["ha_members"] = []
        case "M09":
            mutated["ha_group_name"] = "SYNTHETIC-CLUSTER"
        case "M10":
            mutated["ha_members"] = ["SYNTHETIC-MEMBER"]
        case _:
            raise ValueError(f"Unknown mutation_id: {mutation_id!r}")

    return mutated
