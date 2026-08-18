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
