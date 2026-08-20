from collections import Counter

import pytest

from validation_experiment.experiment.main import (
    assert_main_results,
    run_main_experiment,
)
from validation_experiment.experiment.runner import TreatmentResult


@pytest.fixture(scope="module")
def main_results() -> list[TreatmentResult]:
    return run_main_experiment()


def test_main_run_has_exact_frozen_case_and_treatment_order(
    main_results: list[TreatmentResult],
) -> None:
    expected_case_ids = [
        *(f"E{number:02d}" for number in range(1, 33)),
        "C01",
        "C02",
        "C03",
        "C04",
        "N01",
    ]

    assert len(main_results) == 74
    assert [
        (result.case_id, result.treatment) for result in main_results
    ] == [
        (case_id, treatment)
        for case_id in expected_case_ids
        for treatment in ("V1", "V2")
    ]
    assert len({result.case_id for result in main_results}) == 37
    assert len(
        {(result.case_id, result.treatment) for result in main_results}
    ) == 74
    assert Counter(result.case_id for result in main_results) == {
        case_id: 2 for case_id in expected_case_ids
    }


def test_main_run_result_category_counts_match_frozen_design(
    main_results: list[TreatmentResult],
) -> None:
    assert sum(result.mutation_id is not None for result in main_results) == 64
    assert sum(result.case_id.startswith("C") for result in main_results) == 8
    assert sum(result.case_id == "N01" for result in main_results) == 2


def test_all_mutated_cases_detect_their_expected_rule(
    main_results: list[TreatmentResult],
) -> None:
    mutated_results = [
        result for result in main_results if result.case_id.startswith("E")
    ]

    assert len(mutated_results) == 64
    for result in mutated_results:
        assert result.ground_truth_model_conformant is False
        assert result.ground_truth_processing_eligible is None
        assert result.expected_rule in {
            "R01",
            "R02",
            "R03",
            "R04",
            "R05",
            "R06",
            "R07",
            "R08",
        }
        assert result.expected_rule_detected is True
        assert result.expected_rule in result.observed_rules


def test_all_controls_are_accepted_with_treatment_specific_observations(
    main_results: list[TreatmentResult],
) -> None:
    controls = [
        result for result in main_results if result.case_id.startswith("C")
    ]

    assert len(controls) == 8
    for result in controls:
        assert result.ground_truth_model_conformant is True
        assert result.ground_truth_processing_eligible is True
        assert result.expected_rule is None
        assert result.observed_rules == ()
        assert result.expected_rule_detected is None
        assert result.accepted is True
        assert result.observed_model_conformant is True
        assert result.observed_processing_eligible is (
            None if result.treatment == "V1" else True
        )


def test_n01_matches_frozen_v1_v2_behavior(
    main_results: list[TreatmentResult],
) -> None:
    n01_v1, n01_v2 = [
        result for result in main_results if result.case_id == "N01"
    ]

    assert n01_v1.treatment == "V1"
    assert n01_v1.ground_truth_model_conformant is True
    assert n01_v1.ground_truth_processing_eligible is False
    assert n01_v1.expected_rule is None
    assert n01_v1.observed_rules == ()
    assert n01_v1.expected_rule_detected is None
    assert n01_v1.accepted is True
    assert n01_v1.observed_model_conformant is True
    assert n01_v1.observed_processing_eligible is None

    assert n01_v2.treatment == "V2"
    assert n01_v2.ground_truth_model_conformant is True
    assert n01_v2.ground_truth_processing_eligible is False
    assert n01_v2.expected_rule == "R09"
    assert n01_v2.observed_rules == ("R09",)
    assert n01_v2.expected_rule_detected is True
    assert n01_v2.accepted is False
    assert n01_v2.observed_model_conformant is True
    assert n01_v2.observed_processing_eligible is False


def test_main_result_assertion_accepts_the_frozen_observations(
    main_results: list[TreatmentResult],
) -> None:
    assert_main_results(main_results)
