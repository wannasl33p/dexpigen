"""Enumerations for the DEXPI 1.3 in-memory model.

Most DEXPI code fields (e.g. ``FluidCode``, instrument category/modifier) are
unrestricted strings in the specification, so the model must not claim a
tighter vocabulary as a DEXPI rule. This module holds only the few fields that
genuinely are DEXPI enumerations and stays minimal.
"""

from enum import StrEnum


class OnHoldClassification(StrEnum):
    """DEXPI ``OnHoldClassification``: whether a piping component is on hold."""

    NOT_ON_HOLD = "NotOnHold"
    ON_HOLD = "OnHold"


class PipingClassArtefactClassification(StrEnum):
    """DEXPI ``PipingClassArtefactClassification``: piping-class-artefact flag."""

    NON_PIPING_CLASS_ARTEFACT = "NonPipingClassArtefact"
    PIPING_CLASS_ARTEFACT = "PipingClassArtefact"


class FailActionClassification(StrEnum):
    """DEXPI ``FailActionClassification``: actuator behaviour on power/air loss."""

    FAIL_CLOSE = "FailClose"
    FAIL_OPEN = "FailOpen"
    FAIL_RETAIN_POSITION = "FailRetainPosition"
