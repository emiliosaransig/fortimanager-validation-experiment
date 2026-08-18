import json
from pathlib import Path

import pydantic
import pytest

from validation_experiment.experiment.main import run_main_experiment
from validation_experiment.experiment.provenance import (
    EXPERIMENT_DEFINITION_COMMIT,
    EXPERIMENT_DEFINITION_TAG,
    sha256_file,
    write_main_run_provenance,
)
from validation_experiment.experiment.runner import write_results_csv


EXPECTED_PROVENANCE_FIELDS = {
    "experiment_name",
    "experiment_definition_commit",
    "experiment_definition_tag",
    "execution_commit",
    "python_version",
    "pydantic_version",
    "pytest_version",
    "case_count",
    "treatment_count",
    "treatment_result_count",
    "result_file",
    "result_sha256",
    "run_timestamp_utc",
}


def test_provenance_is_parseable_complete_and_hash_consistent(
    tmp_path: Path,
) -> None:
    results = run_main_experiment()
    result_path = tmp_path / "main_results.csv"
    provenance_path = tmp_path / "main_run_provenance.json"
    write_results_csv(results, result_path)

    written = write_main_run_provenance(
        results=results,
        result_path=result_path,
        provenance_path=provenance_path,
        execution_commit="a" * 40,
        run_timestamp_utc="2026-08-18T12:00:00Z",
    )

    parsed = json.loads(provenance_path.read_text(encoding="utf-8"))
    assert parsed == written
    assert set(parsed) == EXPECTED_PROVENANCE_FIELDS
    assert parsed["experiment_name"] == "fortimanager-validation-experiment"
    assert parsed["experiment_definition_commit"] == (
        "74066ed0069e83a0fb239eea4ff2ce275fda15ef"
    )
    assert parsed["experiment_definition_commit"] == (
        EXPERIMENT_DEFINITION_COMMIT
    )
    assert parsed["experiment_definition_tag"] == "experiment-v1.0-pre-run"
    assert parsed["experiment_definition_tag"] == EXPERIMENT_DEFINITION_TAG
    assert parsed["execution_commit"] == "a" * 40
    assert parsed["python_version"] == "3.12.14"
    assert parsed["pydantic_version"] == pydantic.__version__
    assert parsed["pytest_version"] == pytest.__version__
    assert parsed["case_count"] == 37
    assert parsed["treatment_count"] == 2
    assert parsed["treatment_result_count"] == 74
    assert parsed["result_file"] == "data/results/main_results.csv"
    assert parsed["result_sha256"] == sha256_file(result_path)
    assert parsed["run_timestamp_utc"] == "2026-08-18T12:00:00Z"


def test_provenance_contains_no_local_or_secret_identifiers(
    tmp_path: Path,
) -> None:
    results = run_main_experiment()
    result_path = tmp_path / "main_results.csv"
    provenance_path = tmp_path / "main_run_provenance.json"
    write_results_csv(results, result_path)
    write_main_run_provenance(
        results=results,
        result_path=result_path,
        provenance_path=provenance_path,
        execution_commit="b" * 40,
        run_timestamp_utc="2026-08-18T12:00:00Z",
    )

    serialized = provenance_path.read_text(encoding="utf-8").lower()
    for forbidden in (
        "username",
        "hostname",
        "private_ip",
        "token",
        "secret",
        "/home/",
        "\\users\\",
    ):
        assert forbidden not in serialized


def test_main_csv_is_deterministic_and_lf_only(tmp_path: Path) -> None:
    first_path = tmp_path / "first.csv"
    second_path = tmp_path / "second.csv"

    write_results_csv(run_main_experiment(), first_path)
    write_results_csv(run_main_experiment(), second_path)

    first_bytes = first_path.read_bytes()
    assert first_bytes == second_path.read_bytes()
    assert b"\r\n" not in first_bytes
    assert first_bytes.count(b"\n") == 75
