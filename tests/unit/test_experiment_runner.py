import json
from copy import deepcopy
from pathlib import Path

import pytest

import validation_experiment.experiment.runner as runner_module
from validation_experiment.experiment.cases import (
    ExperimentCase,
    build_experiment_cases,
)
from validation_experiment.experiment.runner import (
    expected_rule_for_treatment,
    run_case,
    run_cases,
)
from validation_experiment.normalization import normalize_device_record
from validation_experiment.validation.baseline import validate_baseline
from validation_experiment.validation.processing import validate_processing


FIXTURE_PATH = (
    Path(__file__).parents[2] / "data" / "fixtures" / "golden_devices.json"
)


def experiment_cases() -> tuple[ExperimentCase, ...]:
    fixture_entries = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    fixtures = {
        entry["fixture_id"]: normalize_device_record(entry["raw"])
        for entry in fixture_entries
    }
    return build_experiment_cases(fixtures)


def experiment_case(case_id: str) -> ExperimentCase:
    return next(case for case in experiment_cases() if case.case_id == case_id)


def test_run_case_returns_exactly_v1_then_v2() -> None:
    results = run_case(experiment_case("E01"))

    assert len(results) == 2
    assert tuple(result.treatment for result in results) == ("V1", "V2")


def test_treatments_receive_independent_deep_copies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case = experiment_case("C01")
    original_record = deepcopy(case.record)
    received_records: list[dict[str, object]] = []

    def mutating_v1(record: dict[str, object]):
        received_records.append(record)
        result = validate_baseline(record)
        record["name"] = "V1-MUTATED"
        return result

    def mutating_v2(record: dict[str, object]):
        assert record == original_record
        received_records.append(record)
        result = validate_processing(record)
        record["name"] = "V2-MUTATED"
        return result

    monkeypatch.setattr(runner_module, "validate_baseline", mutating_v1)
    monkeypatch.setattr(runner_module, "validate_processing", mutating_v2)

    run_case(case)

    assert case.record == original_record
    assert received_records[0] is not received_records[1]
    assert all(record is not case.record for record in received_records)


@pytest.mark.parametrize(
    "case_id,expected_rule",
    [("E01", "R01"), ("E17", "R04"), ("E25", "R06")],
)
def test_mutated_k1_k2_k3_cases_detect_expected_rule_in_both_treatments(
    case_id: str, expected_rule: str
) -> None:
    v1_result, v2_result = run_case(experiment_case(case_id))

    for result in (v1_result, v2_result):
        assert result.expected_rule == expected_rule
        assert result.observed_rules == (expected_rule,)
        assert result.expected_rule_detected is True
        assert result.accepted is False
        assert result.observed_model_conformant is False
    assert v1_result.observed_processing_eligible is None
    assert v2_result.observed_processing_eligible is None
    assert "R09" not in v2_result.observed_rules


def test_control_has_no_expected_or_observed_rule() -> None:
    v1_result, v2_result = run_case(experiment_case("C01"))

    for result in (v1_result, v2_result):
        assert result.expected_rule is None
        assert result.observed_rules == ()
        assert result.expected_rule_detected is None
        assert result.accepted is True
        assert result.observed_model_conformant is True
    assert v1_result.observed_processing_eligible is None
    assert v2_result.observed_processing_eligible is True


def test_n01_has_treatment_specific_expected_rule_and_observations() -> None:
    case = experiment_case("N01")
    v1_result, v2_result = run_case(case)

    assert expected_rule_for_treatment(case, "V1") is None
    assert v1_result.expected_rule is None
    assert v1_result.observed_rules == ()
    assert v1_result.expected_rule_detected is None
    assert v1_result.accepted is True
    assert v1_result.observed_model_conformant is True
    assert v1_result.observed_processing_eligible is None

    assert expected_rule_for_treatment(case, "V2") == "R09"
    assert v2_result.expected_rule == "R09"
    assert v2_result.observed_rules == ("R09",)
    assert v2_result.expected_rule_detected is True
    assert v2_result.accepted is False
    assert v2_result.observed_model_conformant is True
    assert v2_result.observed_processing_eligible is False


def test_run_cases_produces_two_ordered_results_per_selected_case() -> None:
    selected = (experiment_case("E01"), experiment_case("C01"))

    results = run_cases(selected)

    assert [(result.case_id, result.treatment) for result in results] == [
        ("E01", "V1"),
        ("E01", "V2"),
        ("C01", "V1"),
        ("C01", "V2"),
    ]
