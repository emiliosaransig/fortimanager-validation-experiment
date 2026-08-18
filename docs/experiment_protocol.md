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
normalization. Only after this mutation point is V1 or V2 executed. This keeps
model-constraint violations attributable to the validation treatment rather
than to shared preparation.

## V1 baseline treatment

V1 is the baseline model validation using R01–R08. Its input is the unvalidated
normalized dictionary, and its result reports each detected violation with the
corresponding frozen rule identifier.

A `CanonicalDeviceRecord` is constructed only after the dictionary passes every
R01–R08 check. At that point, V1 converts the validated management-IP string to
an `IPv4Address` for the strict domain model. An invalid result contains no
canonical record.

F05 remains model-conformant under V1 when it has no R01–R08 violation;
`"FortiClient-EMS"` is a valid non-empty hardware-model string. Processing
eligibility is not part of V1.

## V2 processing treatment

V2 is V1 plus R09. It always evaluates V1 first. If baseline validation fails,
V2 reports the unchanged R01–R08 violations, sets `model_conformant` to `False`,
and leaves `processing_eligible` unevaluated as `None`.

Only a model-conformant record is evaluated for R09. A hardware model beginning
with `"FortiGate-"` is processing eligible. A model-conformant but ineligible
record has `model_conformant=True`, `processing_eligible=False`, and an R09
violation while retaining its valid `CanonicalDeviceRecord`.

This separation makes model conformance distinct from application-specific
processing eligibility. F05 is the natural K4 control for this distinction: it
is accepted by V1 and rejected only for processing eligibility by V2.

## Mutation catalogue and applicability

Each mutation is deterministic, is applied to a copy of a normalized record,
and introduces exactly one intended fault. No random mutation generation is
used.

| Mutation | Class | Expected rule | Operation | Applicable fixtures |
| --- | --- | --- | --- | --- |
| M01 | K1 | R01 | Remove `name` | F01, F02, F03, F04 |
| M02 | K1 | R02 | Remove `serial_number` | F01, F02, F03, F04 |
| M03 | K1 | R04 | Remove `management_ip` | F01, F02, F03, F04 |
| M04 | K2 | R03 | Set `hardware_model` to `123` | F01, F02, F03, F04 |
| M05 | K2 | R04 | Set `management_ip` to `"999.10.20.30"` | F01, F02, F03, F04 |
| M06 | K2 | R05 | Set `ha_state` to `"unknown"` | F01, F02, F03, F04 |
| M07 | K3 | R06 | Set `ha_group_name` to `None` | F02, F04 |
| M08 | K3 | R07 | Set `ha_members` to `[]` | F02, F04 |
| M09 | K3 | R08 | Set `ha_group_name` to `"SYNTHETIC-CLUSTER"` | F01, F03 |
| M10 | K3 | R08 | Set `ha_members` to `["SYNTHETIC-MEMBER"]` | F01, F03 |

## Experimental units

The frozen matrix contains exactly 37 experimental units:

- E01–E32 are the 32 single-fault mutated cases defined by the applicability
  matrix. They are model-nonconformant and processing eligibility is not
  evaluated.
- C01–C04 are the four unmutated, valid F01–F04 controls. They are model
  conformant and processing eligible.
- N01 is the unmutated F05 record. It is a natural K4 case: model conformant but
  not eligible for the application-specific processing path, with R09 as its
  expected rule. It is not a synthetic data fault.

## Paired treatment runner

The runner executes each selected `ExperimentCase` first under V1 and then under
V2. Each treatment receives its own deep copy of the case record; neither
treatment can affect the other input, and the original case remains unchanged.

Expected rules are treatment-specific. E01–E32 expect their frozen baseline
rule under both V1 and V2. Controls expect no rule. N01 expects no rule under V1
and R09 under V2. When no rule is expected, expected-rule detection is recorded
as `None`, not as a failed detection.

The treatment result records all observed rule IDs and separately records model
conformance, processing eligibility, and acceptance. CSV export uses a stable
schema without timestamps and serializes multiple rule IDs with `|`.

## Pilot instrumentation check

The pilot contains exactly E01, E17, E25, C01, and N01, covering K1, K2, K3, a
valid control, and the natural K4 case. These five cases were executed under V1
and V2, producing ten treatment results in `data/results/pilot_results.csv`.

The pilot checks only that the experimental instrumentation behaves as frozen;
it is not used for metrics or scientific interpretation. The complete 37-case
experiment has not been executed, and no main-experiment result file exists.
