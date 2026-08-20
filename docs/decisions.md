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

## ADR-007: Processing eligibility follows successful baseline validation

R09 is evaluated only for records that have passed R01–R08. Model invalidity and
processing ineligibility are reported separately; baseline-invalid records have
no processing-eligibility assessment.

A model-conformant R09 case retains its valid `CanonicalDeviceRecord`. F05 is
therefore a natural K4 case rather than a synthetic data error: it is model
conformant but ineligible for the FortiGate processing path.

## ADR-008: Treatments operate on isolated copies

V1 and V2 receive independent deep copies of the same experimental case record.
This prevents either treatment from influencing the other's input and preserves
the original `ExperimentCase` unchanged.

## ADR-009: A pilot run precedes the main experiment

The five-case pilot checks instrumentation across K1, K2, K3, a valid control,
and K4. It does not support metrics or result interpretation. A review follows
the successful pilot before the main experiment may be executed.

## ADR-010: Main results are captured before metric interpretation

Raw treatment results are captured completely and hashed before any metric
aggregation or scientific interpretation. Separate provenance binds the result
bytes to runtime versions and distinguishes the frozen experiment-definition
commit from the later execution-code commit.

Subsequent analysis must consume the frozen result file rather than rerunning or
rewriting it implicitly.

## ADR-011: Scientific metrics are derived only from frozen raw results

Analysis does not execute the experiment code again. The frozen
`data/results/main_results.csv` is the sole source for all scientific metrics,
and its exact bytes must pass the SHA-256 check against provenance and the known
frozen hash before analysis begins.

K1–K3, controls, and K4 are derived through separate predefined paths. Because
K4 contains only the single natural N01 case, it is reported descriptively and
is not converted into a class-level percentage metric.
