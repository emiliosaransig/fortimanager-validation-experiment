# Experiment Protocol

## Purpose and boundary

The canonical model provides the stable input boundary for a scientific
comparison of validation treatments. This repository is a standalone research
artifact. It neither evaluates a company implementation nor incorporates code,
architecture, or implementation details from an operational software project.

The research data is derived from an anonymized FortiManager field structure and
contains only the attributes required by the experiment. The five golden
fixtures use documentation-only addresses, synthetic host names, and synthetic
serial numbers.

## Experimental position

The experiment begins after a raw, already anonymized device record has been
normalized and immediately before validation. Normalization is therefore shared
preparation, not an experimental validation treatment. Mutations will be
injected only at the boundary between normalization and validation.

The V1 treatment, V2 treatment, mutation catalogue, and ground truth are
specified separately in later work packages. They are deliberately not defined
or implemented here.
