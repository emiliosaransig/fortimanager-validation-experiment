"""Frozen experimental case matrix E01–E32, C01–C04, and N01."""

from collections.abc import Mapping
from dataclasses import dataclass

from validation_experiment.experiment.mutations import apply_mutation


@dataclass(frozen=True)
class ExperimentCase:
    """One experimental unit with frozen ground-truth metadata."""

    case_id: str
    fixture_id: str
    mutation_id: str | None
    violation_class: str | None
    expected_rule: str | None
    model_conformant: bool
    processing_eligible: bool | None
    record: dict[str, object]


_MUTATED_CASE_SPECS = (
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
_CONTROL_CASE_SPECS = (
    ("C01", "F01"),
    ("C02", "F02"),
    ("C03", "F03"),
    ("C04", "F04"),
)


def build_experiment_cases(
    normalized_fixtures: Mapping[str, Mapping[str, object]],
) -> tuple[ExperimentCase, ...]:
    """Build the 37 frozen experimental units without executing treatments."""

    mutated_cases = tuple(
        ExperimentCase(
            case_id=case_id,
            fixture_id=fixture_id,
            mutation_id=mutation_id,
            violation_class=violation_class,
            expected_rule=expected_rule,
            model_conformant=False,
            processing_eligible=None,
            record=apply_mutation(
                normalized_fixtures[fixture_id], mutation_id
            ),
        )
        for (
            case_id,
            fixture_id,
            mutation_id,
            violation_class,
            expected_rule,
        ) in _MUTATED_CASE_SPECS
    )

    control_cases = tuple(
        ExperimentCase(
            case_id=case_id,
            fixture_id=fixture_id,
            mutation_id=None,
            violation_class=None,
            expected_rule=None,
            model_conformant=True,
            processing_eligible=True,
            record=dict(normalized_fixtures[fixture_id]),
        )
        for case_id, fixture_id in _CONTROL_CASE_SPECS
    )

    natural_case = ExperimentCase(
        case_id="N01",
        fixture_id="F05",
        mutation_id=None,
        violation_class="K4",
        expected_rule="R09",
        model_conformant=True,
        processing_eligible=False,
        record=dict(normalized_fixtures["F05"]),
    )

    return mutated_cases + control_cases + (natural_case,)
