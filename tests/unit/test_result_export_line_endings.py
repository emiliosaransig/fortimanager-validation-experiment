from pathlib import Path

from validation_experiment.experiment.runner import (
    TreatmentResult,
    write_results_csv,
)


def test_csv_export_uses_lf_line_endings_for_clean_git_diffs(
    tmp_path: Path,
) -> None:
    result = TreatmentResult(
        case_id="C01",
        fixture_id="F01",
        mutation_id=None,
        violation_class=None,
        treatment="V1",
        ground_truth_model_conformant=True,
        ground_truth_processing_eligible=True,
        expected_rule=None,
        observed_rules=(),
        expected_rule_detected=None,
        accepted=True,
        observed_model_conformant=True,
        observed_processing_eligible=None,
    )
    output_path = tmp_path / "result.csv"

    write_results_csv([result], output_path)

    content = output_path.read_bytes()
    assert b"\r\n" not in content
    assert content.endswith(b"\n")
