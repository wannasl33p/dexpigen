# Enumerations

The DEXPI enumerations used by model fields, with their members.

Generated from `dexpigen.enumerations` by `scripts/gen_reference.py`; do not edit by hand.

## Contents

- [OnHoldClassification](#onholdclassification)
- [PipingClassArtefactClassification](#pipingclassartefactclassification)
- [FailActionClassification](#failactionclassification)

## Classes

### OnHoldClassification

DEXPI `OnHoldClassification`: whether a piping component is on hold.

| Member | Value |
| --- | --- |
| `NOT_ON_HOLD` | `NotOnHold` |
| `ON_HOLD` | `OnHold` |

### PipingClassArtefactClassification

DEXPI `PipingClassArtefactClassification`: piping-class-artefact flag.

| Member | Value |
| --- | --- |
| `NON_PIPING_CLASS_ARTEFACT` | `NonPipingClassArtefact` |
| `PIPING_CLASS_ARTEFACT` | `PipingClassArtefact` |

### FailActionClassification

DEXPI `FailActionClassification`: actuator behaviour on power/air loss.

| Member | Value |
| --- | --- |
| `FAIL_CLOSE` | `FailClose` |
| `FAIL_OPEN` | `FailOpen` |
| `FAIL_RETAIN_POSITION` | `FailRetainPosition` |
