# FortiManager Validation Experiment

This repository contains a standalone scientific experiment for comparing
validation treatments over a small canonical device model. It is an independent
research artifact: it does not evaluate, reuse, or reproduce an operational or
company implementation.

## Current status

Implemented:

- the complete experiment pipeline;
- the frozen 37-case main experiment;
- reproducible result capture; and
- deterministic frozen-result analysis.

Executed:

- the five-case pilot;
- the 37-case paired main experiment; and
- the frozen-result metric analysis.

Outputs:

- `data/results/main_results.csv`;
- `data/results/main_run_provenance.json`;
- classwise detection analysis;
- detection deltas;
- control rejection analysis; and
- the descriptive K4 result.

Not part of the experiment code:

- scientific discussion;
- threats-to-validity interpretation; and
- thesis narrative.

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
`data/fixtures/golden_devices.json`; reviewed pilot, main-run, and derived
analysis outputs are stored in `data/results/`.
