"""V1 baseline validation treatment."""

from collections.abc import Mapping
from dataclasses import dataclass
from ipaddress import AddressValueError, IPv4Address

from pydantic import ValidationError

from validation_experiment.domain import CanonicalDeviceRecord


@dataclass(frozen=True)
class ValidationViolation:
    """A model-constraint violation attributed to a frozen rule identifier."""

    rule_id: str
    message: str


@dataclass(frozen=True)
class BaselineValidationResult:
    """Outcome of the V1 baseline validation treatment."""

    is_valid: bool
    violations: tuple[ValidationViolation, ...]
    canonical_record: CanonicalDeviceRecord | None


def validate_baseline(record: Mapping[str, object]) -> BaselineValidationResult:
    """Validate a normalized record with the V1 baseline treatment."""

    violations: list[ValidationViolation] = []

    name = record.get("name")
    if not isinstance(name, str) or name == "":
        violations.append(
            ValidationViolation("R01", "name must be a non-empty string")
        )

    serial_number = record.get("serial_number")
    if not isinstance(serial_number, str) or serial_number == "":
        violations.append(
            ValidationViolation(
                "R02", "serial_number must be a non-empty string"
            )
        )

    hardware_model = record.get("hardware_model")
    if not isinstance(hardware_model, str) or hardware_model == "":
        violations.append(
            ValidationViolation(
                "R03", "hardware_model must be a non-empty string"
            )
        )

    validated_ip: IPv4Address | None = None
    management_ip = record.get("management_ip")
    if isinstance(management_ip, str):
        try:
            validated_ip = IPv4Address(management_ip)
        except AddressValueError:
            pass
    if validated_ip is None:
        violations.append(
            ValidationViolation(
                "R04", "management_ip must be a valid IPv4 address string"
            )
        )

    ha_state = record.get("ha_state")
    if not isinstance(ha_state, str) or ha_state not in (
        "standalone",
        "clustered",
    ):
        violations.append(
            ValidationViolation(
                "R05", "ha_state must be 'standalone' or 'clustered'"
            )
        )

    if ha_state == "clustered":
        if record.get("ha_group_name") is None:
            violations.append(
                ValidationViolation(
                    "R06", "clustered records require an HA group name"
                )
            )

        ha_members = record.get("ha_members")
        if not isinstance(ha_members, list) or len(ha_members) < 2:
            violations.append(
                ValidationViolation(
                    "R07", "clustered records require at least two HA members"
                )
            )
    elif ha_state == "standalone":
        if (
            record.get("ha_group_name") is not None
            or record.get("ha_members") != []
        ):
            violations.append(
                ValidationViolation(
                    "R08", "standalone records cannot have an HA assignment"
                )
            )

    if violations:
        return BaselineValidationResult(
            is_valid=False,
            violations=tuple(violations),
            canonical_record=None,
        )

    prepared = dict(record)
    prepared["management_ip"] = validated_ip

    try:
        canonical_record = CanonicalDeviceRecord.model_validate(prepared)
    except ValidationError as error:
        raise RuntimeError(
            "CanonicalDeviceRecord rejected a record that passed R01-R08"
        ) from error

    return BaselineValidationResult(
        is_valid=True,
        violations=(),
        canonical_record=canonical_record,
    )
