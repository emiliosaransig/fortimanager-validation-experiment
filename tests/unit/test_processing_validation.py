import json
from pathlib import Path

import pytest

from validation_experiment.experiment.mutations import apply_mutation
from validation_experiment.normalization import normalize_device_record
from validation_experiment.validation.baseline import validate_baseline
from validation_experiment.validation.processing import validate_processing


FIXTURE_PATH = (
    Path(__file__).parents[2] / "data" / "fixtures" / "golden_devices.json"
)


def normalized_fixture(fixture_id: str) -> dict[str, object]:
    fixture_entries = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    raw = next(
        entry["raw"]
        for entry in fixture_entries
        if entry["fixture_id"] == fixture_id
    )
    return normalize_device_record(raw)


def rule_ids(violations) -> tuple[str, ...]:
    return tuple(violation.rule_id for violation in violations)


@pytest.mark.parametrize("fixture_id", ["F01", "F02", "F03", "F04"])
def test_v2_accepts_model_conformant_fortigate_fixtures(fixture_id: str) -> None:
    record = normalized_fixture(fixture_id)

    result = validate_processing(record)
    baseline_result = validate_baseline(record)

    assert baseline_result.is_valid is True
    assert result.is_valid is True
    assert result.model_conformant is True
    assert result.processing_eligible is True
    assert result.violations == ()
    assert result.canonical_record == baseline_result.canonical_record


def test_f05_is_valid_in_v1_but_processing_ineligible_in_v2() -> None:
    record = normalized_fixture("F05")

    baseline_result = validate_baseline(record)
    processing_result = validate_processing(record)

    assert baseline_result.is_valid is True
    assert baseline_result.violations == ()
    assert processing_result.is_valid is False
    assert processing_result.model_conformant is True
    assert processing_result.processing_eligible is False
    assert rule_ids(processing_result.violations) == ("R09",)
    assert processing_result.canonical_record is not None
    assert (
        processing_result.canonical_record.hardware_model
        == "FortiClient-EMS"
    )


@pytest.mark.parametrize("mutation_id,expected_rule", [("M01", "R01"), ("M05", "R04")])
def test_v2_does_not_evaluate_r09_for_model_invalid_f05(
    mutation_id: str, expected_rule: str
) -> None:
    record = apply_mutation(normalized_fixture("F05"), mutation_id)

    result = validate_processing(record)

    assert result.is_valid is False
    assert result.model_conformant is False
    assert result.processing_eligible is None
    assert rule_ids(result.violations) == (expected_rule,)
    assert "R09" not in rule_ids(result.violations)
    assert result.canonical_record is None


@pytest.mark.parametrize(
    "fixture_id,mutation_id,expected_rule",
    [
        ("F01", "M01", "R01"),
        ("F01", "M02", "R02"),
        ("F01", "M04", "R03"),
        ("F01", "M05", "R04"),
        ("F01", "M06", "R05"),
        ("F02", "M07", "R06"),
        ("F02", "M08", "R07"),
        ("F01", "M09", "R08"),
    ],
)
def test_v2_preserves_v1_rule_attribution_for_r01_to_r08(
    fixture_id: str, mutation_id: str, expected_rule: str
) -> None:
    record = apply_mutation(normalized_fixture(fixture_id), mutation_id)

    baseline_result = validate_baseline(record)
    processing_result = validate_processing(record)

    assert rule_ids(baseline_result.violations) == (expected_rule,)
    assert processing_result.violations == baseline_result.violations
    assert processing_result.model_conformant is False
    assert processing_result.processing_eligible is None
    assert processing_result.canonical_record is None
