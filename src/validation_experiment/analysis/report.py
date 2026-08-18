"""Write deterministic derived files from the verified frozen results."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Mapping

from validation_experiment.analysis.metrics import (
    ClasswiseDetection,
    ControlRejection,
    DetectionDelta,
    K4NaturalCase,
    calculate_classwise_detection,
    calculate_control_rejection,
    calculate_detection_delta,
    describe_k4_natural_case,
    load_frozen_results,
    verify_frozen_result_hash,
)


DEFAULT_RESULT_PATH = Path("data/results/main_results.csv")
DEFAULT_PROVENANCE_PATH = Path("data/results/main_run_provenance.json")
DEFAULT_OUTPUT_DIR = Path("data/results")


@dataclass(frozen=True)
class AnalysisOutputs:
    classwise_detection: Path
    detection_delta: Path
    control_rejection: Path
    k4_natural_case: Path
    summary: Path

    def filenames(self) -> tuple[str, ...]:
        return (
            self.classwise_detection.name,
            self.detection_delta.name,
            self.control_rejection.name,
            self.k4_natural_case.name,
            self.summary.name,
        )


def _write_csv(
    path: Path,
    *,
    fieldnames: tuple[str, ...],
    rows: Iterable[Mapping[str, object]],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, value: Mapping[str, object]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def _k4_as_dict(k4_case: K4NaturalCase) -> dict[str, object]:
    def treatment_state(name: str) -> dict[str, object]:
        state = k4_case.v1 if name == "V1" else k4_case.v2
        return {
            "expected_rule": state.expected_rule,
            "observed_rules": list(state.observed_rules),
            "accepted": state.accepted,
            "observed_model_conformant": state.observed_model_conformant,
            "observed_processing_eligible": (
                state.observed_processing_eligible
            ),
        }

    return {
        "case_id": k4_case.case_id,
        "violation_class": k4_case.violation_class,
        "note": (
            "Natural model-conformant but processing-ineligible case; "
            "no class-level rate is calculated."
        ),
        "V1": treatment_state("V1"),
        "V2": treatment_state("V2"),
    }


def _classwise_rows(
    metrics: Iterable[ClasswiseDetection],
) -> list[dict[str, object]]:
    return [asdict(metric) for metric in metrics]


def _delta_rows(
    metrics: Iterable[DetectionDelta],
) -> list[dict[str, object]]:
    return [asdict(metric) for metric in metrics]


def _control_rows(
    metrics: Iterable[ControlRejection],
) -> list[dict[str, object]]:
    return [asdict(metric) for metric in metrics]


def generate_analysis(
    result_path: Path = DEFAULT_RESULT_PATH,
    provenance_path: Path = DEFAULT_PROVENANCE_PATH,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> AnalysisOutputs:
    """Verify, derive, and export the five frozen-result analysis files."""

    result_path = Path(result_path)
    provenance_path = Path(provenance_path)
    output_dir = Path(output_dir)
    frozen = load_frozen_results(result_path, provenance_path)

    classwise = calculate_classwise_detection(frozen.results)
    deltas = calculate_detection_delta(classwise)
    controls = calculate_control_rejection(frozen.results)
    k4_case = describe_k4_natural_case(frozen.results)

    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = AnalysisOutputs(
        classwise_detection=(
            output_dir / "analysis_classwise_detection.csv"
        ),
        detection_delta=output_dir / "analysis_detection_delta.csv",
        control_rejection=output_dir / "analysis_control_rejection.csv",
        k4_natural_case=output_dir / "analysis_k4_natural_case.json",
        summary=output_dir / "analysis_summary.json",
    )

    classwise_rows = _classwise_rows(classwise)
    delta_rows = _delta_rows(deltas)
    control_rows = _control_rows(controls)
    _write_csv(
        outputs.classwise_detection,
        fieldnames=(
            "violation_class",
            "treatment",
            "n_cases",
            "detected_cases",
            "detection_rate",
        ),
        rows=classwise_rows,
    )
    _write_csv(
        outputs.detection_delta,
        fieldnames=(
            "violation_class",
            "v1_detection_rate",
            "v2_detection_rate",
            "delta_detection_rate",
        ),
        rows=delta_rows,
    )
    _write_csv(
        outputs.control_rejection,
        fieldnames=(
            "treatment",
            "n_controls",
            "rejected_controls",
            "control_rejection_rate",
        ),
        rows=control_rows,
    )
    _write_json(outputs.k4_natural_case, _k4_as_dict(k4_case))
    _write_json(
        outputs.summary,
        {
            "source_result_file": frozen.source_result_file,
            "source_result_sha256": frozen.source_result_sha256,
            "case_count": frozen.structure.case_count,
            "treatment_result_count": (
                frozen.structure.treatment_result_count
            ),
            "classwise_detection": classwise_rows,
            "detection_delta": delta_rows,
            "control_rejection": control_rows,
            "k4_case": k4_case.case_id,
        },
    )

    verify_frozen_result_hash(result_path, provenance_path)
    return outputs


def main() -> None:
    generate_analysis()


if __name__ == "__main__":
    main()
