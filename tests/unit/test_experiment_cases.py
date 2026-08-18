import json
from copy import deepcopy
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from validation_experiment.experiment.cases import build_experiment_cases
from validation_experiment.experiment.mutations import apply_mutation
from validation_experiment.normalization import normalize_device_record


FIXTURE_PATH = (
    Path(__file__).parents[2] / "data" / "fixtures" / "golden_devices.json"
)
EXPECTED_MUTATED_CASES = (
    ("E01", "F01", "M01", "K1", "R01"),
    ("E02", "F02", "M01", "K1", "R01"),
    ("E03", "F03", "M01", "K1", "R01"),
    ("E04", "F04", "M01", "K1", "R01"),
    ("E05", "F01", "M02", "K1", "R02"),
    ("E06", "F02", "M02", "K1", "R02"),
    ("E07", "F03", "M02", "K1", "R02"),
    ("E08", "F04", "M02", "K1", "R02"),
    ("E09", "F01", "M03", "K1", "R04"),
    ("E10", "F02", "M03", "K1", "R04"),
    ("E11", "F03", "M03", "K1", "R04"),
    ("E12", "F04", "M03", "K1", "R04"),
    ("E13", "F01", "M04", "K2", "R03"),
    ("E14", "F02", "M04", "K2", "R03"),
    ("E15", "F03", "M04", "K2", "R03"),
    ("E16", "F04", "M04", "K2", "R03"),
    ("E17", "F01", "M05", "K2", "R04"),
    ("E18", "F02", "M05", "K2", "R04"),
    ("E19", "F03", "M05", "K2", "R04"),
    ("E20", "F04", "M05", "K2", "R04"),
    ("E21", "F01", "M06", "K2", "R05"),
    ("E22", "F02", "M06", "K2", "R05"),
    ("E23", "F03", "M06", "K2", "R05"),
    ("E24", "F04", "M06", "K2", "R05"),
    ("E25", "F02", "M07", "K3", "R06"),
    ("E26", "F04", "M07", "K3", "R06"),
    ("E27", "F02", "M08", "K3", "R07"),
    ("E28", "F04", "M08", "K3", "R07"),
    ("E29", "F01", "M09", "K3", "R08"),
    ("E30", "F03", "M09", "K3", "R08"),
    ("E31", "F01", "M10", "K3", "R08"),
    ("E32", "F03", "M10", "K3", "R08"),
)


def normalized_fixtures() -> dict[str, dict[str, object]]:
    fixture_entries = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    return {
        entry["fixture_id"]: normalize_device_record(entry["raw"])
        for entry in fixture_entries
    }


def cases_by_id():
    return {
        case.case_id: case
        for case in build_experiment_cases(normalized_fixtures())
    }


def test_case_counts_and_unique_ids_match_frozen_design() -> None:
    cases = build_experiment_cases(normalized_fixtures())
    case_ids = [case.case_id for case in cases]

    assert len(cases) == 37
    assert len(set(case_ids)) == 37
    assert sum(case.mutation_id is not None for case in cases) == 32
    assert sum(case.case_id.startswith("C") for case in cases) == 4
    assert sum(case.case_id == "N01" for case in cases) == 1


def test_violation_class_counts_match_frozen_design() -> None:
    cases = build_experiment_cases(normalized_fixtures())

    assert sum(case.violation_class == "K1" for case in cases) == 12
    assert sum(case.violation_class == "K2" for case in cases) == 12
    assert sum(case.violation_class == "K3" for case in cases) == 8
    assert sum(case.violation_class == "K4" for case in cases) == 1


@pytest.mark.parametrize(
    "case_id,fixture_id,mutation_id,violation_class,expected_rule",
    EXPECTED_MUTATED_CASES,
)
def test_e01_to_e32_match_exact_case_matrix(
    case_id: str,
    fixture_id: str,
    mutation_id: str,
    violation_class: str,
    expected_rule: str,
) -> None:
    case = cases_by_id()[case_id]
    source_record = normalized_fixtures()[fixture_id]

    assert case.fixture_id == fixture_id
    assert case.mutation_id == mutation_id
    assert case.violation_class == violation_class
    assert case.expected_rule == expected_rule
    assert case.model_conformant is False
    assert case.processing_eligible is None
    assert case.record == apply_mutation(source_record, mutation_id)


@pytest.mark.parametrize(
    "case_id,fixture_id",
    [("C01", "F01"), ("C02", "F02"), ("C03", "F03"), ("C04", "F04")],
)
def test_control_cases_match_ground_truth(case_id: str, fixture_id: str) -> None:
    case = cases_by_id()[case_id]

    assert case.fixture_id == fixture_id
    assert case.mutation_id is None
    assert case.violation_class is None
    assert case.expected_rule is None
    assert case.model_conformant is True
    assert case.processing_eligible is True
    assert case.record == normalized_fixtures()[fixture_id]


def test_n01_is_the_only_natural_f05_case() -> None:
    cases = build_experiment_cases(normalized_fixtures())
    n01 = next(case for case in cases if case.case_id == "N01")

    assert [case.case_id for case in cases if case.fixture_id == "F05"] == [
        "N01"
    ]
    assert n01.mutation_id is None
    assert n01.violation_class == "K4"
    assert n01.expected_rule == "R09"
    assert n01.model_conformant is True
    assert n01.processing_eligible is False
    assert n01.record == normalized_fixtures()["F05"]


def test_ha_mutations_follow_exact_applicability_matrix() -> None:
    cases = build_experiment_cases(normalized_fixtures())
    fixtures_by_mutation = {
        mutation_id: {
            case.fixture_id
            for case in cases
            if case.mutation_id == mutation_id
        }
        for mutation_id in ("M07", "M08", "M09", "M10")
    }

    assert fixtures_by_mutation == {
        "M07": {"F02", "F04"},
        "M08": {"F02", "F04"},
        "M09": {"F01", "F03"},
        "M10": {"F01", "F03"},
    }


def test_case_generation_does_not_modify_inputs_or_golden_fixture_file() -> None:
    fixtures = normalized_fixtures()
    fixtures_before = deepcopy(fixtures)
    golden_file_before = FIXTURE_PATH.read_text(encoding="utf-8")

    build_experiment_cases(fixtures)

    assert fixtures == fixtures_before
    assert FIXTURE_PATH.read_text(encoding="utf-8") == golden_file_before


def test_experiment_case_metadata_is_frozen() -> None:
    case = build_experiment_cases(normalized_fixtures())[0]

    with pytest.raises(FrozenInstanceError):
        case.case_id = "CHANGED"
