"""Integrity checks and metrics for the frozen main-result CSV."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


FROZEN_RESULT_SHA256 = (
    "70713719e968531570c7db261f28864cf3395fe631568fdc1841533638d9a87e"
)
DETECTION_CLASSES = ("K1", "K2", "K3")
TREATMENTS = ("V1", "V2")
EXPECTED_CASE_COUNTS = {"K1": 12, "K2": 12, "K3": 8, "K4": 1}
EXPECTED_CONTROL_IDS = {"C01", "C02", "C03", "C04"}
EXPECTED_MUTATED_IDS = {f"E{number:02d}" for number in range(1, 33)}

REQUIRED_CSV_FIELDS = {
    "case_id",
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
}


class ResultIntegrityError(RuntimeError):
    """Raised when the frozen result bytes do not match their trusted hash."""


class ResultStructureError(RuntimeError):
    """Raised when the frozen result table violates its expected structure."""


@dataclass(frozen=True)
class ResultRecord:
    case_id: str
    mutation_id: str | None
    violation_class: str | None
    treatment: str
    ground_truth_model_conformant: bool
    ground_truth_processing_eligible: bool | None
    expected_rule: str | None
    observed_rules: tuple[str, ...]
    expected_rule_detected: bool | None
    accepted: bool
    observed_model_conformant: bool
    observed_processing_eligible: bool | None


@dataclass(frozen=True)
class StructureCounts:
    case_count: int
    treatment_result_count: int
    mutated_case_count: int
    control_count: int
    k4_natural_case_count: int
    k1_count: int
    k2_count: int
    k3_count: int


@dataclass(frozen=True)
class FrozenResults:
    source_result_file: str
    source_result_sha256: str
    results: tuple[ResultRecord, ...]
    structure: StructureCounts


@dataclass(frozen=True)
class ClasswiseDetection:
    violation_class: str
    treatment: str
    n_cases: int
    detected_cases: int
    detection_rate: float


@dataclass(frozen=True)
class DetectionDelta:
    violation_class: str
    v1_detection_rate: float
    v2_detection_rate: float
    delta_detection_rate: float


@dataclass(frozen=True)
class ControlRejection:
    treatment: str
    n_controls: int
    rejected_controls: int
    control_rejection_rate: float


@dataclass(frozen=True)
class K4TreatmentState:
    expected_rule: str | None
    observed_rules: tuple[str, ...]
    accepted: bool
    observed_model_conformant: bool
    observed_processing_eligible: bool | None


@dataclass(frozen=True)
class K4NaturalCase:
    case_id: str
    violation_class: str
    v1: K4TreatmentState
    v2: K4TreatmentState


def _load_provenance(provenance_path: Path) -> dict[str, object]:
    try:
        parsed = json.loads(provenance_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ResultIntegrityError(
            f"Could not read result provenance: {provenance_path}"
        ) from error
    if not isinstance(parsed, dict):
        raise ResultIntegrityError("Result provenance must be a JSON object")
    return parsed


def _read_verified_result_bytes(
    result_path: Path,
    provenance_path: Path,
) -> tuple[bytes, dict[str, object], str]:
    provenance = _load_provenance(provenance_path)
    provenance_sha256 = provenance.get("result_sha256")
    if provenance_sha256 != FROZEN_RESULT_SHA256:
        raise ResultIntegrityError(
            "Provenance SHA-256 does not match the frozen expected SHA-256"
        )
    try:
        result_bytes = result_path.read_bytes()
    except OSError as error:
        raise ResultIntegrityError(
            f"Could not read frozen result file: {result_path}"
        ) from error
    actual_sha256 = hashlib.sha256(result_bytes).hexdigest()
    if actual_sha256 != provenance_sha256:
        raise ResultIntegrityError(
            "Result SHA-256 mismatch: "
            f"expected {provenance_sha256}, calculated {actual_sha256}"
        )
    return result_bytes, provenance, actual_sha256


def verify_frozen_result_hash(
    result_path: Path,
    provenance_path: Path,
) -> str:
    """Verify exact result bytes against provenance and the frozen known hash."""

    _, _, actual_sha256 = _read_verified_result_bytes(
        Path(result_path), Path(provenance_path)
    )
    return actual_sha256


def _optional_text(value: str | None) -> str | None:
    if value is None:
        raise ResultStructureError("CSV row is missing a required field")
    return value or None


def _optional_bool(
    value: str | None,
    *,
    field_name: str,
    row_number: int,
) -> bool | None:
    if value == "":
        return None
    if value == "True":
        return True
    if value == "False":
        return False
    raise ResultStructureError(
        f"Row {row_number} has invalid boolean for {field_name}: {value!r}"
    )


def _required_bool(
    value: str | None,
    *,
    field_name: str,
    row_number: int,
) -> bool:
    parsed = _optional_bool(
        value,
        field_name=field_name,
        row_number=row_number,
    )
    if parsed is None:
        raise ResultStructureError(
            f"Row {row_number} has empty required boolean {field_name}"
        )
    return parsed


def _observed_rules(value: str | None, *, row_number: int) -> tuple[str, ...]:
    if value is None:
        raise ResultStructureError(
            f"Row {row_number} is missing observed_rules"
        )
    if value == "":
        return ()
    rules = tuple(value.split("|"))
    if any(not rule for rule in rules):
        raise ResultStructureError(
            f"Row {row_number} has an empty observed rule identifier"
        )
    return rules


def _parse_result_rows(result_bytes: bytes) -> tuple[ResultRecord, ...]:
    try:
        result_text = result_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ResultStructureError("Result CSV is not valid UTF-8") from error
    reader = csv.DictReader(io.StringIO(result_text, newline=""))
    fieldnames = set(reader.fieldnames or ())
    missing_fields = REQUIRED_CSV_FIELDS - fieldnames
    if missing_fields:
        raise ResultStructureError(
            "Result CSV is missing required fields: "
            + ", ".join(sorted(missing_fields))
        )

    parsed_rows: list[ResultRecord] = []
    for row_number, row in enumerate(reader, start=2):
        if None in row:
            raise ResultStructureError(
                f"Row {row_number} has more values than the CSV header"
            )
        case_id = row["case_id"]
        treatment = row["treatment"]
        if not case_id or not treatment:
            raise ResultStructureError(
                f"Row {row_number} has an empty case_id or treatment"
            )
        parsed_rows.append(
            ResultRecord(
                case_id=case_id,
                mutation_id=_optional_text(row["mutation_id"]),
                violation_class=_optional_text(row["violation_class"]),
                treatment=treatment,
                ground_truth_model_conformant=_required_bool(
                    row["ground_truth_model_conformant"],
                    field_name="ground_truth_model_conformant",
                    row_number=row_number,
                ),
                ground_truth_processing_eligible=_optional_bool(
                    row["ground_truth_processing_eligible"],
                    field_name="ground_truth_processing_eligible",
                    row_number=row_number,
                ),
                expected_rule=_optional_text(row["expected_rule"]),
                observed_rules=_observed_rules(
                    row["observed_rules"], row_number=row_number
                ),
                expected_rule_detected=_optional_bool(
                    row["expected_rule_detected"],
                    field_name="expected_rule_detected",
                    row_number=row_number,
                ),
                accepted=_required_bool(
                    row["accepted"],
                    field_name="accepted",
                    row_number=row_number,
                ),
                observed_model_conformant=_required_bool(
                    row["observed_model_conformant"],
                    field_name="observed_model_conformant",
                    row_number=row_number,
                ),
                observed_processing_eligible=_optional_bool(
                    row["observed_processing_eligible"],
                    field_name="observed_processing_eligible",
                    row_number=row_number,
                ),
            )
        )
    return tuple(parsed_rows)


def validate_result_structure(
    results: Iterable[ResultRecord],
) -> StructureCounts:
    rows = tuple(results)
    if len(rows) != 74:
        raise ResultStructureError(
            f"Expected 74 treatment results, found {len(rows)}"
        )

    rows_by_case: dict[str, list[ResultRecord]] = {}
    pairs: set[tuple[str, str]] = set()
    for row in rows:
        pair = (row.case_id, row.treatment)
        if pair in pairs:
            raise ResultStructureError(
                f"Duplicate case/treatment pair: {row.case_id}/{row.treatment}"
            )
        pairs.add(pair)
        rows_by_case.setdefault(row.case_id, []).append(row)

    if len(rows_by_case) != 37:
        raise ResultStructureError(
            f"Expected 37 unique cases, found {len(rows_by_case)}"
        )
    for case_id, case_rows in rows_by_case.items():
        if {row.treatment for row in case_rows} != set(TREATMENTS):
            raise ResultStructureError(
                f"Case {case_id} must have exactly V1 and V2 results"
            )
        classes = {row.violation_class for row in case_rows}
        mutations = {row.mutation_id for row in case_rows}
        if len(classes) != 1 or len(mutations) != 1:
            raise ResultStructureError(
                f"Case {case_id} has inconsistent class or mutation metadata"
            )

    case_class = {
        case_id: case_rows[0].violation_class
        for case_id, case_rows in rows_by_case.items()
    }
    control_ids = {
        case_id for case_id, value in case_class.items() if value is None
    }
    mutated_ids = {
        case_id
        for case_id, value in case_class.items()
        if value in DETECTION_CLASSES
    }
    k4_ids = {
        case_id for case_id, value in case_class.items() if value == "K4"
    }
    unknown_classes = {
        value
        for value in case_class.values()
        if value not in {*DETECTION_CLASSES, "K4", None}
    }
    if unknown_classes:
        raise ResultStructureError(
            f"Unexpected violation classes: {sorted(unknown_classes)}"
        )
    if control_ids != EXPECTED_CONTROL_IDS:
        raise ResultStructureError(
            f"Expected controls C01-C04, found {sorted(control_ids)}"
        )
    if mutated_ids != EXPECTED_MUTATED_IDS:
        raise ResultStructureError(
            "Mutated cases must be exactly E01-E32"
        )
    if k4_ids != {"N01"}:
        raise ResultStructureError("K4 natural case must be exactly N01")

    for case_id in mutated_ids:
        if rows_by_case[case_id][0].mutation_id is None:
            raise ResultStructureError(
                f"Mutated case {case_id} has no mutation_id"
            )
    for case_id in control_ids | k4_ids:
        if rows_by_case[case_id][0].mutation_id is not None:
            raise ResultStructureError(
                f"Unmutated case {case_id} unexpectedly has a mutation_id"
            )

    class_counts = {
        violation_class: sum(
            value == violation_class for value in case_class.values()
        )
        for violation_class in EXPECTED_CASE_COUNTS
    }
    if class_counts != EXPECTED_CASE_COUNTS:
        raise ResultStructureError(
            f"Unexpected class-level case counts: {class_counts}"
        )

    return StructureCounts(
        case_count=len(rows_by_case),
        treatment_result_count=len(rows),
        mutated_case_count=len(mutated_ids),
        control_count=len(control_ids),
        k4_natural_case_count=len(k4_ids),
        k1_count=class_counts["K1"],
        k2_count=class_counts["K2"],
        k3_count=class_counts["K3"],
    )


def load_frozen_results(
    result_path: Path,
    provenance_path: Path,
) -> FrozenResults:
    """Load results only after hash and frozen-structure verification."""

    result_bytes, provenance, actual_sha256 = _read_verified_result_bytes(
        Path(result_path), Path(provenance_path)
    )
    results = _parse_result_rows(result_bytes)
    structure = validate_result_structure(results)
    if provenance.get("case_count") != structure.case_count:
        raise ResultStructureError("Provenance case_count does not match CSV")
    if (
        provenance.get("treatment_result_count")
        != structure.treatment_result_count
    ):
        raise ResultStructureError(
            "Provenance treatment_result_count does not match CSV"
        )
    source_result_file = provenance.get("result_file")
    if source_result_file != "data/results/main_results.csv":
        raise ResultStructureError(
            "Provenance result_file is not data/results/main_results.csv"
        )
    return FrozenResults(
        source_result_file=source_result_file,
        source_result_sha256=actual_sha256,
        results=results,
        structure=structure,
    )


def calculate_classwise_detection(
    results: Iterable[ResultRecord],
) -> tuple[ClasswiseDetection, ...]:
    rows = tuple(results)
    metrics: list[ClasswiseDetection] = []
    for violation_class in DETECTION_CLASSES:
        for treatment in TREATMENTS:
            group = tuple(
                row
                for row in rows
                if row.violation_class == violation_class
                and row.treatment == treatment
            )
            if not group:
                raise ResultStructureError(
                    f"No results for {violation_class}/{treatment}"
                )
            detected_cases = sum(
                row.expected_rule_detected is True for row in group
            )
            metrics.append(
                ClasswiseDetection(
                    violation_class=violation_class,
                    treatment=treatment,
                    n_cases=len(group),
                    detected_cases=detected_cases,
                    detection_rate=detected_cases / len(group),
                )
            )
    return tuple(metrics)


def calculate_detection_delta(
    classwise_detection: Iterable[ClasswiseDetection],
) -> tuple[DetectionDelta, ...]:
    by_group = {
        (metric.violation_class, metric.treatment): metric
        for metric in classwise_detection
    }
    deltas: list[DetectionDelta] = []
    for violation_class in DETECTION_CLASSES:
        try:
            v1 = by_group[(violation_class, "V1")].detection_rate
            v2 = by_group[(violation_class, "V2")].detection_rate
        except KeyError as error:
            raise ResultStructureError(
                f"Missing classwise detection metric for {violation_class}"
            ) from error
        deltas.append(
            DetectionDelta(
                violation_class=violation_class,
                v1_detection_rate=v1,
                v2_detection_rate=v2,
                delta_detection_rate=v2 - v1,
            )
        )
    return tuple(deltas)


def calculate_control_rejection(
    results: Iterable[ResultRecord],
) -> tuple[ControlRejection, ...]:
    rows = tuple(results)
    metrics: list[ControlRejection] = []
    for treatment in TREATMENTS:
        controls = tuple(
            row
            for row in rows
            if row.violation_class is None and row.treatment == treatment
        )
        if not controls:
            raise ResultStructureError(
                f"No control results for treatment {treatment}"
            )
        rejected = sum(row.accepted is False for row in controls)
        metrics.append(
            ControlRejection(
                treatment=treatment,
                n_controls=len(controls),
                rejected_controls=rejected,
                control_rejection_rate=rejected / len(controls),
            )
        )
    return tuple(metrics)


def describe_k4_natural_case(
    results: Iterable[ResultRecord],
) -> K4NaturalCase:
    k4_rows = {
        row.treatment: row
        for row in results
        if row.case_id == "N01" and row.violation_class == "K4"
    }
    if set(k4_rows) != set(TREATMENTS):
        raise ResultStructureError("N01 must have one K4 result for V1 and V2")

    def state(row: ResultRecord) -> K4TreatmentState:
        return K4TreatmentState(
            expected_rule=row.expected_rule,
            observed_rules=row.observed_rules,
            accepted=row.accepted,
            observed_model_conformant=row.observed_model_conformant,
            observed_processing_eligible=row.observed_processing_eligible,
        )

    return K4NaturalCase(
        case_id="N01",
        violation_class="K4",
        v1=state(k4_rows["V1"]),
        v2=state(k4_rows["V2"]),
    )
