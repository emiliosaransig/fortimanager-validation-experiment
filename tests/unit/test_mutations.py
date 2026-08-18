import json
from copy import deepcopy
from pathlib import Path

import pytest

from validation_experiment.experiment.mutations import apply_mutation
from validation_experiment.normalization import normalize_device_record


FIXTURE_PATH = (
    Path(__file__).parents[2] / "data" / "fixtures" / "golden_devices.json"
)
REMOVED = object()
MUTATION_EXPECTATIONS = {
    "M01": ("F01", "name", REMOVED),
    "M02": ("F01", "serial_number", REMOVED),
    "M03": ("F01", "management_ip", REMOVED),
    "M04": ("F01", "hardware_model", 123),
    "M05": ("F01", "management_ip", "999.10.20.30"),
    "M06": ("F01", "ha_state", "unknown"),
    "M07": ("F02", "ha_group_name", None),
    "M08": ("F02", "ha_members", []),
    "M09": ("F01", "ha_group_name", "SYNTHETIC-CLUSTER"),
    "M10": ("F01", "ha_members", ["SYNTHETIC-MEMBER"]),
}


def normalized_fixture(fixture_id: str) -> dict[str, object]:
    fixture_entries = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    raw = next(
        entry["raw"]
        for entry in fixture_entries
        if entry["fixture_id"] == fixture_id
    )
    return normalize_device_record(raw)


@pytest.mark.parametrize("mutation_id", MUTATION_EXPECTATIONS)
def test_each_mutation_changes_only_its_specified_field(mutation_id: str) -> None:
    fixture_id, field, expected_value = MUTATION_EXPECTATIONS[mutation_id]
    original = normalized_fixture(fixture_id)
    original_before = deepcopy(original)
    expected = deepcopy(original)
    if expected_value is REMOVED:
        expected.pop(field)
    else:
        expected[field] = expected_value

    mutated = apply_mutation(original, mutation_id)

    assert mutated == expected
    assert original == original_before
    assert mutated is not original


@pytest.mark.parametrize("mutation_id", MUTATION_EXPECTATIONS)
def test_each_mutation_is_deterministic(mutation_id: str) -> None:
    fixture_id, _, _ = MUTATION_EXPECTATIONS[mutation_id]
    original = normalized_fixture(fixture_id)

    assert apply_mutation(original, mutation_id) == apply_mutation(
        original, mutation_id
    )
