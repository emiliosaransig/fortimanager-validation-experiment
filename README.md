# FortiManager Validation Experiment

This repository contains a standalone scientific experiment for comparing
validation treatments over a small canonical device model. It is an independent
research artifact: it does not evaluate, reuse, or reproduce an operational or
company implementation.

## Current status

Implemented:

- normalization of the anonymized research fixtures;
- V1 baseline validation for R01–R08 with rule-attributed violations;
- the deterministic mutation catalogue M01–M10;
- the 37 frozen experiment cases;
- V2 processing validation with R09;
- paired experiment-runner instrumentation; and
- isolated pilot instrumentation and deterministic CSV export.

Executed:

- the five-case pilot only.

The following activities have not been executed:

- the full 37-case experiment;
- final metrics; and
- scientific result interpretation.

## Requirements

- Python 3.12 or newer
- Pydantic 2
- pytest (for development and verification)

## Setup and verification

```shell
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
pytest
```

The project uses a `src` layout. Research fixtures are stored in
`data/fixtures/golden_devices.json`. The reviewed pilot output is stored in
`data/results/pilot_results.csv`; no main-experiment output exists.
