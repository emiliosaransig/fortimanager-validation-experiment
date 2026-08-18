"""Deterministic execution and technical validation of the main experiment."""

import json
from collections.abc import Sequence
from pathlib import Path

from validation_experiment.experiment.cases import build_experiment_cases
from validation_experiment.experiment.runner import TreatmentResult, run_cases
from validation_experiment.normalization import normalize_device_record


_FIXTURE_PATH = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "fixtures"
    / "golden_devices.json"
)
_EXPECTED_CASE_IDS = (
    *(f"E{number:02d}" for number in range(1, 33)),
    "C01",
    "C02",
    "C03",
    "C04",
    "N01",
)


def run_main_experiment() -> list[TreatmentResult]:
    """Run all 37 frozen cases once under V1 and V2 in fixed order."""

    fixture_entries = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    normalized_fixtures = {
        entry["fixture_id"]: normalize_device_record(entry["raw"])
        for entry in fixture_entries
    }
    cases = build_experiment_cases(normalized_fixtures)
    return run_cases(cases)


def assert_main_results(results: Sequence[TreatmentResult]) -> None:
    """Raise if main-run observations differ from the frozen expectations."""

    expected_pairs = [
        (case_id, treatment)
        for case_id in _EXPECTED_CASE_IDS
        for treatment in ("V1", "V2")
    ]
    observed_pairs = [
        (result.case_id, result.treatment) for result in results
    ]
    if len(results) != 74 or observed_pairs != expected_pairs:
        raise AssertionError(
            "Main run must contain 37 ordered V1/V2 case pairs"
        )
    if len(set(observed_pairs)) != 74:
        raise AssertionError("Main run contains a duplicate case-treatment pair")

    for result in results:
        if result.case_id.startswith("E"):
            if (
                result.ground_truth_model_conformant is not False
                or result.ground_truth_processing_eligible is not None
                or result.expected_rule is None
                or result.expected_rule_detected is not True
                or result.expected_rule not in result.observed_rules
            ):
                raise AssertionError(
                    f"{result.case_id}/{result.treatment} did not detect its "
                    "frozen expected rule"
                )
        elif result.case_id.startswith("C"):
            expected_processing = (
                None if result.treatment == "V1" else True
            )
            if (
                result.ground_truth_model_conformant is not True
                or result.ground_truth_processing_eligible is not True
                or result.expected_rule is not None
                or result.observed_rules != ()
                or result.expected_rule_detected is not None
                or result.accepted is not True
                or result.observed_model_conformant is not True
                or result.observed_processing_eligible
                is not expected_processing
            ):
                raise AssertionError(
                    f"{result.case_id}/{result.treatment} control was not "
                    "accepted as frozen"
                )

    n01_v1, n01_v2 = [
        result for result in results if result.case_id == "N01"
    ]
    if (
        n01_v1.treatment != "V1"
        or n01_v1.ground_truth_model_conformant is not True
        or n01_v1.ground_truth_processing_eligible is not False
        or n01_v1.expected_rule is not None
        or n01_v1.observed_rules != ()
        or n01_v1.expected_rule_detected is not None
        or n01_v1.accepted is not True
        or n01_v1.observed_model_conformant is not True
        or n01_v1.observed_processing_eligible is not None
    ):
        raise AssertionError("N01/V1 differs from the frozen expectation")
    if (
        n01_v2.treatment != "V2"
        or n01_v2.ground_truth_model_conformant is not True
        or n01_v2.ground_truth_processing_eligible is not False
        or n01_v2.expected_rule != "R09"
        or n01_v2.observed_rules != ("R09",)
        or n01_v2.expected_rule_detected is not True
        or n01_v2.accepted is not False
        or n01_v2.observed_model_conformant is not True
        or n01_v2.observed_processing_eligible is not False
    ):
        raise AssertionError("N01/V2 differs from the frozen expectation")
