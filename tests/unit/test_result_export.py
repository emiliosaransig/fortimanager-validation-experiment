import csv
import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

from validation_experiment.experiment.cases import (
    ExperimentCase,
    build_experiment_cases,
)
from validation_experiment.experiment.runner import (
    run_case,
    write_results_csv,
)
from validation_experiment.normalization import normalize_device_record


FIXTURE_PATH = (
    Path(__file__).parents[2] / "data" / "fixtures" / "golden_devices.json"
)
EXPECTED_HEADER = [
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
]


def experiment_case(case_id: str) -> ExperimentCase:
    fixture_entries = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    fixtures = {
        entry["fixture_id"]: normalize_device_record(entry["raw"])
        for entry in fixture_entries
    }
    return next(
        case
        for case in build_experiment_cases(fixtures)
        if case.case_id == case_id
    )


def test_csv_header_row_count_and_none_serialization_are_stable(
    tmp_path: Path,
) -> None:
    results = [
        *run_case(experiment_case("E01")),
        *run_case(experiment_case("C01")),
        *run_case(experiment_case("N01")),
    ]
    output_path = tmp_path / "results.csv"

    write_results_csv(results, output_path)

    with output_path.open(newline="", encoding="utf-8") as output_file:
        rows = list(csv.reader(output_file))
    assert rows[0] == EXPECTED_HEADER
    assert len(rows) == len(results) + 1

    with output_path.open(newline="", encoding="utf-8") as output_file:
        records = list(csv.DictReader(output_file))
    c01_v1 = next(
        record
        for record in records
        if record["case_id"] == "C01" and record["treatment"] == "V1"
    )
    assert c01_v1["mutation_id"] == ""
    assert c01_v1["violation_class"] == ""
    assert c01_v1["expected_rule"] == ""
    assert c01_v1["observed_rules"] == ""
    assert c01_v1["expected_rule_detected"] == ""
    assert c01_v1["observed_processing_eligible"] == ""


def test_csv_serializes_rule_ids_without_python_tuple_representation(
    tmp_path: Path,
) -> None:
    result = replace(
        run_case(experiment_case("E01"))[0],
        observed_rules=("R01", "R02"),
    )
    output_path = tmp_path / "rules.csv"

    write_results_csv([result], output_path)

    with output_path.open(newline="", encoding="utf-8") as output_file:
        record = next(csv.DictReader(output_file))
    assert record["observed_rules"] == "R01|R02"


def test_csv_export_does_not_modify_results_and_is_repeatable(
    tmp_path: Path,
) -> None:
    results = list(run_case(experiment_case("N01")))
    results_before = deepcopy(results)
    first_path = tmp_path / "first.csv"
    second_path = tmp_path / "second.csv"

    write_results_csv(results, first_path)
    write_results_csv(results, second_path)

    assert results == results_before
    assert first_path.read_text(encoding="utf-8") == second_path.read_text(
        encoding="utf-8"
    )
