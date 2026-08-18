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
- paired experiment-runner instrumentation;
- isolated pilot instrumentation and deterministic CSV export; and
- reproducible main-experiment capture with provenance and SHA-256 integrity.

Executed:

- the five-case pilot; and
- the full 37-case paired main experiment.

Captured:

- 74 treatment results in `data/results/main_results.csv`; and
- run provenance with the result-file SHA-256 in
  `data/results/main_run_provenance.json`.

The following activities have not been performed:

- scientific metric aggregation; and
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
`data/fixtures/golden_devices.json`; reviewed pilot and main-run outputs are
stored in `data/results/`.
