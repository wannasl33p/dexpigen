"""The top-level ``ConceptualModel``: a single root aggregating a whole P&ID."""

from __future__ import annotations

from pydantic import Field

from dexpigen.base import DexpiBaseModel
from dexpigen.equipment import Equipment
from dexpigen.instrumentation import (
    ActuatingFunction,
    ActuatingSystem,
    ProcessInstrumentationFunction,
    SignalConveyingFunction,
)
from dexpigen.piping import PipingNetworkSystem


class ConceptualModel(DexpiBaseModel):
    """The root that aggregates all top-level objects of a P&ID."""

    equipment: list[Equipment] = Field(default_factory=list)
    piping_network_systems: list[PipingNetworkSystem] = Field(default_factory=list)
    process_instrumentation_functions: list[ProcessInstrumentationFunction] = Field(
        default_factory=list
    )
    actuating_systems: list[ActuatingSystem] = Field(default_factory=list)
    actuating_functions: list[ActuatingFunction] = Field(default_factory=list)
    signal_conveying_functions: list[SignalConveyingFunction] = Field(
        default_factory=list
    )
