"""Paired execution and result export for experiment cases."""

import csv
from collections.abc import Sequence
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

from validation_experiment.experiment.cases import ExperimentCase
from validation_experiment.validation.baseline import validate_baseline
from validation_experiment.validation.processing import validate_processing


@dataclass(frozen=True)
class TreatmentResult:
    """Treatment-specific observation for one experimental case."""

    case_id: str
    fixture_id: str
    mutation_id: str | None
    violation_class: str | None
    treatment: str
    ground_truth_model_conformant: bool
    ground_truth_processing_eligible: bool | None
    expected_rule: str | None
    observed_rules: tuple[str, ...]
    expected_rule_detected: bool | None
    accepted: bool
    observed_model_conformant: bool
    observed_processing_eligible: bool | None


_CSV_FIELDS = (
    "case_id",
    "fixture_id",
    "mutation_id",
    "violation_class",
    "treatment",
    "ground_truth_model_conformant",
    "ground_truth_processing_eligible",
    "expected_rule",
    "observed_rules",
    "expected_rule_detected",
    "accepted",
    "observed_model_conformant",
    "observed_processing_eligible",
)


def expected_rule_for_treatment(
    case: ExperimentCase, treatment: str
) -> str | None:
    """Return the frozen expected rule for one case-treatment pairing."""

    if treatment not in ("V1", "V2"):
        raise ValueError(f"Unknown treatment: {treatment!r}")
    if case.case_id == "N01" and treatment == "V1":
        return None
    return case.expected_rule


def run_case(case: ExperimentCase) -> tuple[TreatmentResult, TreatmentResult]:
    """Run one case under V1 and V2 using independent deep copies."""

    v1_validation = validate_baseline(deepcopy(case.record))
    v1_expected_rule = expected_rule_for_treatment(case, "V1")
    v1_observed_rules = tuple(
        violation.rule_id for violation in v1_validation.violations
    )
    v1_result = TreatmentResult(
        case_id=case.case_id,
        fixture_id=case.fixture_id,
        mutation_id=case.mutation_id,
        violation_class=case.violation_class,
        treatment="V1",
        ground_truth_model_conformant=case.model_conformant,
        ground_truth_processing_eligible=case.processing_eligible,
        expected_rule=v1_expected_rule,
        observed_rules=v1_observed_rules,
        expected_rule_detected=(
            None
            if v1_expected_rule is None
            else v1_expected_rule in v1_observed_rules
        ),
        accepted=v1_validation.is_valid,
        observed_model_conformant=v1_validation.is_valid,
        observed_processing_eligible=None,
    )

    v2_validation = validate_processing(deepcopy(case.record))
    v2_expected_rule = expected_rule_for_treatment(case, "V2")
    v2_observed_rules = tuple(
        violation.rule_id for violation in v2_validation.violations
    )
    v2_result = TreatmentResult(
        case_id=case.case_id,
        fixture_id=case.fixture_id,
        mutation_id=case.mutation_id,
        violation_class=case.violation_class,
        treatment="V2",
        ground_truth_model_conformant=case.model_conformant,
        ground_truth_processing_eligible=case.processing_eligible,
        expected_rule=v2_expected_rule,
        observed_rules=v2_observed_rules,
        expected_rule_detected=(
            None
            if v2_expected_rule is None
            else v2_expected_rule in v2_observed_rules
        ),
        accepted=v2_validation.is_valid,
        observed_model_conformant=v2_validation.model_conformant,
        observed_processing_eligible=v2_validation.processing_eligible,
    )

    return v1_result, v2_result


def run_cases(cases: Sequence[ExperimentCase]) -> list[TreatmentResult]:
    """Run selected cases sequentially with deterministic V1/V2 ordering."""

    return [result for case in cases for result in run_case(case)]


def write_results_csv(
    results: Sequence[TreatmentResult], path: Path
) -> None:
    """Write treatment results using the stable scientific exchange schema."""

    with path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=_CSV_FIELDS,
            lineterminator="\n",
        )
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "case_id": result.case_id,
                    "fixture_id": result.fixture_id,
                    "mutation_id": result.mutation_id,
                    "violation_class": result.violation_class,
                    "treatment": result.treatment,
                    "ground_truth_model_conformant": (
                        result.ground_truth_model_conformant
                    ),
                    "ground_truth_processing_eligible": (
                        result.ground_truth_processing_eligible
                    ),
                    "expected_rule": result.expected_rule,
                    "observed_rules": "|".join(result.observed_rules),
                    "expected_rule_detected": result.expected_rule_detected,
                    "accepted": result.accepted,
                    "observed_model_conformant": (
                        result.observed_model_conformant
                    ),
                    "observed_processing_eligible": (
                        result.observed_processing_eligible
                    ),
                }
            )
