"""V2 processing validation treatment: V1 plus R09."""

from collections.abc import Mapping
from dataclasses import dataclass

from validation_experiment.domain import CanonicalDeviceRecord
from validation_experiment.validation.baseline import (
    ValidationViolation,
    validate_baseline,
)


@dataclass(frozen=True)
class ProcessingValidationResult:
    """Outcome separating model conformance from processing eligibility."""

    is_valid: bool
    model_conformant: bool
    processing_eligible: bool | None
    violations: tuple[ValidationViolation, ...]
    canonical_record: CanonicalDeviceRecord | None


def validate_processing(
    record: Mapping[str, object],
) -> ProcessingValidationResult:
    """Apply V1, then R09 only to a model-conformant device record."""

    baseline_result = validate_baseline(record)
    if not baseline_result.is_valid:
        return ProcessingValidationResult(
            is_valid=False,
            model_conformant=False,
            processing_eligible=None,
            violations=baseline_result.violations,
            canonical_record=None,
        )

    canonical_record = baseline_result.canonical_record
    if canonical_record is None:
        raise RuntimeError(
            "Baseline validation succeeded without a CanonicalDeviceRecord"
        )

    if canonical_record.hardware_model.startswith("FortiGate-"):
        return ProcessingValidationResult(
            is_valid=True,
            model_conformant=True,
            processing_eligible=True,
            violations=(),
            canonical_record=canonical_record,
        )

    return ProcessingValidationResult(
        is_valid=False,
        model_conformant=True,
        processing_eligible=False,
        violations=(
            ValidationViolation(
                rule_id="R09",
                message=(
                    "Device record is not eligible for the FortiGate "
                    "processing path."
                ),
            ),
        ),
        canonical_record=canonical_record,
    )
