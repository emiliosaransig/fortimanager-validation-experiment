"""Minimal reproducibility metadata for the captured main experiment."""

import hashlib
import json
import platform
from collections.abc import Sequence
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

from validation_experiment.experiment.runner import TreatmentResult


EXPERIMENT_DEFINITION_COMMIT = (
    "74066ed0069e83a0fb239eea4ff2ce275fda15ef"
)
EXPERIMENT_DEFINITION_TAG = "experiment-v1.0-pre-run"
_RESULT_FILE = "data/results/main_results.csv"


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of the exact file bytes."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_main_run_provenance(
    *,
    results: Sequence[TreatmentResult],
    result_path: Path,
    provenance_path: Path,
    execution_commit: str,
    run_timestamp_utc: str | None = None,
) -> dict[str, object]:
    """Capture allowed main-run provenance and bind it to the result bytes."""

    timestamp = run_timestamp_utc or datetime.now(timezone.utc).isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")
    provenance: dict[str, object] = {
        "experiment_name": "fortimanager-validation-experiment",
        "experiment_definition_commit": EXPERIMENT_DEFINITION_COMMIT,
        "experiment_definition_tag": EXPERIMENT_DEFINITION_TAG,
        "execution_commit": execution_commit,
        "python_version": platform.python_version(),
        "pydantic_version": version("pydantic"),
        "pytest_version": version("pytest"),
        "case_count": len({result.case_id for result in results}),
        "treatment_count": len({result.treatment for result in results}),
        "treatment_result_count": len(results),
        "result_file": _RESULT_FILE,
        "result_sha256": sha256_file(result_path),
        "run_timestamp_utc": timestamp,
    }
    provenance_path.write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return provenance
