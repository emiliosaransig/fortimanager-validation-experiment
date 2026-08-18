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

The experimental data flow is:

```text
Source Record
    ↓
Normalization
    ↓
Normalized Dictionary
    ↓
Experimental Mutation Point
    ↓
Validation Treatment
```

Normalization is identical for both validation treatments. It only maps the
selected source fields into their canonical representation and performs the
defined source-format transformations. It does not validate constraints of the
later `CanonicalDeviceRecord` model.

Mutations are injected into the unvalidated normalized dictionary after
normalization. Only after this mutation point is V1, or later V2, executed. This
keeps model-constraint violations attributable to the validation treatment
rather than to shared preparation.

The V1 treatment, V2 treatment, mutation catalogue, and ground truth are
specified separately in later work packages. They are deliberately not defined
or implemented here.
