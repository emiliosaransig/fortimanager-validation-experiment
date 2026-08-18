import csv
import hashlib
import json
from pathlib import Path

import pytest

from validation_experiment.analysis.metrics import (
    FROZEN_RESULT_SHA256,
    ResultIntegrityError,
    load_frozen_results,
)
from validation_experiment.analysis.report import generate_analysis


REPOSITORY_ROOT = Path(__file__).parents[2]
RESULT_PATH = REPOSITORY_ROOT / "data" / "results" / "main_results.csv"
PROVENANCE_PATH = (
    REPOSITORY_ROOT / "data" / "results" / "main_run_provenance.json"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_frozen_main_result_passes_hash_and_structure_checks() -> None:
    frozen = load_frozen_results(RESULT_PATH, PROVENANCE_PATH)

    assert frozen.source_result_sha256 == FROZEN_RESULT_SHA256
    assert frozen.source_result_sha256 == sha256(RESULT_PATH)
    assert frozen.structure.case_count == 37
    assert frozen.structure.treatment_result_count == 74
    assert frozen.structure.mutated_case_count == 32
    assert frozen.structure.control_count == 4
    assert frozen.structure.k4_natural_case_count == 1
    assert frozen.structure.k1_count == 12
    assert frozen.structure.k2_count == 12
    assert frozen.structure.k3_count == 8


def test_tampered_temporary_result_fails_hash_check(tmp_path: Path) -> None:
    tampered_path = tmp_path / "main_results.csv"
    tampered_path.write_bytes(RESULT_PATH.read_bytes() + b"\n")

    with pytest.raises(ResultIntegrityError, match="SHA-256"):
        load_frozen_results(tampered_path, PROVENANCE_PATH)


def test_every_frozen_case_has_exactly_one_v1_and_one_v2_result() -> None:
    frozen = load_frozen_results(RESULT_PATH, PROVENANCE_PATH)
    treatments_by_case: dict[str, list[str]] = {}

    for result in frozen.results:
        treatments_by_case.setdefault(result.case_id, []).append(
            result.treatment
        )

    assert len(treatments_by_case) == 37
    assert all(
        sorted(treatments) == ["V1", "V2"]
        for treatments in treatments_by_case.values()
    )


def test_k4_n01_is_descriptive_and_has_no_detection_rate(
    tmp_path: Path,
) -> None:
    output = generate_analysis(
        RESULT_PATH,
        PROVENANCE_PATH,
        output_dir=tmp_path,
    )
    k4 = json.loads(output.k4_natural_case.read_text(encoding="utf-8"))
    classwise = list(
        csv.DictReader(
            output.classwise_detection.read_text(encoding="utf-8").splitlines()
        )
    )

    assert k4["case_id"] == "N01"
    assert k4["violation_class"] == "K4"
    assert k4["V1"] == {
        "expected_rule": None,
        "observed_rules": [],
        "accepted": True,
        "observed_model_conformant": True,
        "observed_processing_eligible": None,
    }
    assert k4["V2"] == {
        "expected_rule": "R09",
        "observed_rules": ["R09"],
        "accepted": False,
        "observed_model_conformant": True,
        "observed_processing_eligible": False,
    }
    assert all(row["violation_class"] != "K4" for row in classwise)


def test_analysis_export_is_deterministic_lf_only_and_preserves_sources(
    tmp_path: Path,
) -> None:
    source_hash_before = sha256(RESULT_PATH)
    provenance_hash_before = sha256(PROVENANCE_PATH)
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"

    first = generate_analysis(RESULT_PATH, PROVENANCE_PATH, first_dir)
    second = generate_analysis(RESULT_PATH, PROVENANCE_PATH, second_dir)

    assert first.filenames() == second.filenames()
    for filename in first.filenames():
        first_bytes = (first_dir / filename).read_bytes()
        second_bytes = (second_dir / filename).read_bytes()
        assert first_bytes == second_bytes
        assert b"\r\n" not in first_bytes
        assert first_bytes.endswith(b"\n")

    classwise_bytes = first.classwise_detection.read_bytes()
    assert classwise_bytes.splitlines()[0] == (
        b"violation_class,treatment,n_cases,detected_cases,detection_rate"
    )
    with first.classwise_detection.open(newline="", encoding="utf-8") as handle:
        classwise_rows = list(csv.DictReader(handle))
    assert [
        (row["violation_class"], row["treatment"])
        for row in classwise_rows
    ] == [
        ("K1", "V1"),
        ("K1", "V2"),
        ("K2", "V1"),
        ("K2", "V2"),
        ("K3", "V1"),
        ("K3", "V2"),
    ]

    assert sha256(RESULT_PATH) == source_hash_before
    assert sha256(PROVENANCE_PATH) == provenance_hash_before
