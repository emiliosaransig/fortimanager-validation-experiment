import json
from pathlib import Path

from validation_experiment.experiment.cases import (
    ExperimentCase,
    build_experiment_cases,
)
from validation_experiment.experiment.pilot import get_pilot_cases, run_pilot
from validation_experiment.normalization import normalize_device_record


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


def test_pilot_selects_exactly_five_unique_cases_in_frozen_order() -> None:
    pilot_cases = get_pilot_cases(experiment_cases())
    case_ids = tuple(case.case_id for case in pilot_cases)

    assert case_ids == ("E01", "E17", "E25", "C01", "N01")
    assert len(pilot_cases) == 5
    assert len(set(case_ids)) == 5


def test_pilot_produces_exactly_ten_ordered_treatment_results() -> None:
    results = run_pilot(experiment_cases())

    assert len(results) == 10
    assert [(result.case_id, result.treatment) for result in results] == [
        ("E01", "V1"),
        ("E01", "V2"),
        ("E17", "V1"),
        ("E17", "V2"),
        ("E25", "V1"),
        ("E25", "V2"),
        ("C01", "V1"),
        ("C01", "V2"),
        ("N01", "V1"),
        ("N01", "V2"),
    ]


def test_pilot_technical_assertions_match_frozen_expectations() -> None:
    results = {
        (result.case_id, result.treatment): result
        for result in run_pilot(experiment_cases())
    }

    for case_id, rule_id in (("E01", "R01"), ("E17", "R04"), ("E25", "R06")):
        for treatment in ("V1", "V2"):
            result = results[(case_id, treatment)]
            assert result.expected_rule == rule_id
            assert result.observed_rules == (rule_id,)
            assert result.expected_rule_detected is True
            assert result.accepted is False
            assert result.observed_model_conformant is False
            assert result.observed_processing_eligible is None

    c01_v1 = results[("C01", "V1")]
    c01_v2 = results[("C01", "V2")]
    for result in (c01_v1, c01_v2):
        assert result.expected_rule is None
        assert result.observed_rules == ()
        assert result.expected_rule_detected is None
        assert result.accepted is True
        assert result.observed_model_conformant is True
    assert c01_v1.observed_processing_eligible is None
    assert c01_v2.observed_processing_eligible is True

    n01_v1 = results[("N01", "V1")]
    assert n01_v1.expected_rule is None
    assert n01_v1.observed_rules == ()
    assert n01_v1.expected_rule_detected is None
    assert n01_v1.accepted is True
    assert n01_v1.observed_model_conformant is True
    assert n01_v1.observed_processing_eligible is None

    n01_v2 = results[("N01", "V2")]
    assert n01_v2.expected_rule == "R09"
    assert n01_v2.observed_rules == ("R09",)
    assert n01_v2.expected_rule_detected is True
    assert n01_v2.accepted is False
    assert n01_v2.observed_model_conformant is True
    assert n01_v2.observed_processing_eligible is False
