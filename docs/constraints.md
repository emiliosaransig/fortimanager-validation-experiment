# Validation Constraints

V1 evaluates the frozen baseline constraints R01–R08 against an unvalidated
normalized dictionary. It reports every independently detectable violation in
rule order. Cross-field constraints are evaluated only for a known valid
`ha_state`; an R05 violation does not produce artificial R06–R08 follow-up
violations.

## R01 — Name present and non-empty

`name` must be present, must be a string, and must not equal `""`. `None`, a
missing key, and non-string values violate R01. Values are not converted.

## R02 — Serial number present and non-empty

`serial_number` must be present, must be a string, and must not equal `""`.
`None`, a missing key, and non-string values violate R02. Values are not
converted.

## R03 — Hardware model present, string, and non-empty

`hardware_model` must be present, must be a string, and must not equal `""`.
`None`, a missing key, and non-string values violate R03. R03 does not require a
FortiGate device; `"FortiClient-EMS"` is valid under this rule.

## R04 — Management IP present and valid IPv4

`management_ip` must be present as a string representing a valid IPv4 address.
A missing key, `None`, a non-string value, or a string that is not valid IPv4
violates R04. IPv6 and fallback conversion are not supported.

## R05 — Allowed HA state

`ha_state` must be present as a string equal to exactly `"standalone"` or
`"clustered"`. A missing key, `None`, a non-string value, or any other string
violates R05.

## R06 — Cluster requires an HA group name

R06 is evaluated only when `ha_state == "clustered"`. In that state,
`ha_group_name` must not be `None`. No additional general string constraint is
applied to `ha_group_name`.

## R07 — Cluster requires at least two HA members

R07 is evaluated only when `ha_state == "clustered"`. In that state,
`ha_members` must contain at least two members.

## R08 — Standalone cannot have an HA assignment

R08 is evaluated only when `ha_state == "standalone"`. In that state,
`ha_group_name` must be `None` and `ha_members` must equal `[]`. If one or both
conditions fail, one R08 violation is reported.

## R09 — Supported FortiGate model required for processing eligibility

R09 is an application-specific processing constraint and is not part of V1. V2
evaluates it only after a record passes R01–R08. A model-conformant record is
processing eligible exactly when `hardware_model.startswith("FortiGate-")`.

`"FortiClient-EMS"` therefore remains model conformant under V1 but is processing
ineligible under V2. An R09 violation does not turn it into a model-conformance
failure.
