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
- the 37 frozen experiment cases; and
- V2 processing validation with R09.

The following activities have not been executed or implemented:

- a pilot experiment;
- the full experiment runner;
- final result export; and
- metrics or statistical interpretation.

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
`data/fixtures/golden_devices.json`; `data/results/` is intentionally empty and
reserved for later work packages.
