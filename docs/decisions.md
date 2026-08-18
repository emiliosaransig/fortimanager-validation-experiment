# Experimental Decisions

## ADR-001: Independence from the operational MVP

Experimental code is independent from the operational MVP.

## ADR-002: Mutation injection point

Mutations will be injected after normalization and immediately before
validation.

## ADR-003: FortiClient-EMS retention

FortiClient-EMS remains in the normalized dataset and is not filtered during
normalization.

## ADR-004: Minimal research model

The research model uses only the minimal attributes required by the experiment.

## ADR-005: Validation is separated from normalization

Normalization produces an unvalidated normalized dictionary and does not
construct `CanonicalDeviceRecord`. This separation preserves experimental
isolation: model violations can be attributed exclusively to the later
validation treatments.

Undefined source transformations remain normalization errors. In particular,
an unknown FortiManager `ha_mode` code fails during normalization because it
cannot be mapped to the canonical source representation.

## ADR-006: Baseline validation reports explicit rule identifiers

Every detected baseline violation is attributed to one frozen constraint
identifier from R01–R08. A plain accept/reject outcome is insufficient because
the experiment must later determine whether an injected violation was detected
by its expected constraint.

The treatment does not create implicit rule identifiers during execution. Any
unexpected mismatch between R01–R08 and the strict domain model is treated as an
implementation or specification inconsistency, not as a new experimental rule.
