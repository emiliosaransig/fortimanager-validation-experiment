# FortiManager Validation Experiment

This repository contains a standalone scientific experiment for comparing
validation treatments over a small canonical device model. It is an independent
research artifact: it does not evaluate, reuse, or reproduce an operational or
company implementation.

The frozen first work package contains only:

- the `CanonicalDeviceRecord` domain model;
- normalization of the selected, anonymized FortiManager-shaped fields;
- five golden research fixtures; and
- unit tests and protocol documentation.

Validators, mutation generation, experiment execution, metrics, result export,
CLI integration, NetBox integration, and FortiManager API access are outside the
scope of this package.

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
