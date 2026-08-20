"""Fixed five-case pilot selection and execution."""

from collections.abc import Sequence

from validation_experiment.experiment.cases import ExperimentCase
from validation_experiment.experiment.runner import TreatmentResult, run_cases


_PILOT_CASE_IDS = ("E01", "E17", "E25", "C01", "N01")


def get_pilot_cases(
    cases: Sequence[ExperimentCase],
) -> tuple[ExperimentCase, ...]:
    """Select the five frozen pilot cases in deterministic order."""

    cases_by_id = {case.case_id: case for case in cases}
    return tuple(cases_by_id[case_id] for case_id in _PILOT_CASE_IDS)


def run_pilot(cases: Sequence[ExperimentCase]) -> list[TreatmentResult]:
    """Execute only the five selected pilot cases under V1 and V2."""

    return run_cases(get_pilot_cases(cases))
