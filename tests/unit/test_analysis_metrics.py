from dataclasses import replace

from validation_experiment.analysis.metrics import (
    ResultRecord,
    calculate_classwise_detection,
    calculate_control_rejection,
    calculate_detection_delta,
)


def result(
    case_id: str,
    violation_class: str | None,
    treatment: str,
    *,
    detected: bool | None = None,
    accepted: bool = False,
) -> ResultRecord:
    return ResultRecord(
        case_id=case_id,
        mutation_id="M01" if violation_class in {"K1", "K2", "K3"} else None,
        violation_class=violation_class,
        treatment=treatment,
        ground_truth_model_conformant=violation_class is None,
        ground_truth_processing_eligible=(
            True if violation_class is None else None
        ),
        expected_rule="R01" if detected is not None else None,
        observed_rules=("R01",) if detected else (),
        expected_rule_detected=detected,
        accepted=accepted,
        observed_model_conformant=accepted,
        observed_processing_eligible=None,
    )


def synthetic_detection_results() -> tuple[ResultRecord, ...]:
    rows: list[ResultRecord] = []
    detected_by_group = {
        ("K1", "V1"): (True, False),
        ("K1", "V2"): (True, True),
        ("K2", "V1"): (False, False),
        ("K2", "V2"): (True, False),
        ("K3", "V1"): (True, True),
        ("K3", "V2"): (False, True),
    }
    case_number = 1
    for violation_class in ("K1", "K2", "K3"):
        for treatment in ("V1", "V2"):
            for detected in detected_by_group[(violation_class, treatment)]:
                rows.append(
                    result(
                        f"S{case_number:02d}",
                        violation_class,
                        treatment,
                        detected=detected,
                    )
                )
                case_number += 1
    return tuple(rows)


def test_classwise_detection_uses_detected_over_n_per_class_and_treatment() -> None:
    metrics = calculate_classwise_detection(synthetic_detection_results())

    assert [
        (
            metric.violation_class,
            metric.treatment,
            metric.n_cases,
            metric.detected_cases,
            metric.detection_rate,
        )
        for metric in metrics
    ] == [
        ("K1", "V1", 2, 1, 0.5),
        ("K1", "V2", 2, 2, 1.0),
        ("K2", "V1", 2, 0, 0.0),
        ("K2", "V2", 2, 1, 0.5),
        ("K3", "V1", 2, 2, 1.0),
        ("K3", "V2", 2, 1, 0.5),
    ]


def test_detection_delta_is_v2_minus_v1() -> None:
    classwise = calculate_classwise_detection(synthetic_detection_results())

    deltas = calculate_detection_delta(classwise)

    assert [
        (
            delta.violation_class,
            delta.v1_detection_rate,
            delta.v2_detection_rate,
            delta.delta_detection_rate,
        )
        for delta in deltas
    ] == [
        ("K1", 0.5, 1.0, 0.5),
        ("K2", 0.0, 0.5, 0.5),
        ("K3", 1.0, 0.5, -0.5),
    ]


def test_control_rejection_supports_zero_and_one_rejection_out_of_four() -> None:
    controls = tuple(
        result(f"C{number:02d}", None, treatment, accepted=True)
        for treatment in ("V1", "V2")
        for number in range(1, 5)
    )
    controls = tuple(
        replace(row, accepted=False)
        if row.case_id == "C01" and row.treatment == "V2"
        else row
        for row in controls
    )

    metrics = calculate_control_rejection(controls)

    assert [
        (
            metric.treatment,
            metric.n_controls,
            metric.rejected_controls,
            metric.control_rejection_rate,
        )
        for metric in metrics
    ] == [
        ("V1", 4, 0, 0.0),
        ("V2", 4, 1, 0.25),
    ]


def test_classwise_detection_excludes_k4() -> None:
    rows = synthetic_detection_results() + (
        result("N01", "K4", "V1", detected=None, accepted=True),
        result("N01", "K4", "V2", detected=True, accepted=False),
    )

    metrics = calculate_classwise_detection(rows)

    assert {metric.violation_class for metric in metrics} == {"K1", "K2", "K3"}
