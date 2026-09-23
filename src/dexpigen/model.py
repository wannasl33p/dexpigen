"""The top-level ``ConceptualModel``: a single root aggregating a whole P&ID."""

from __future__ import annotations

from typing import Self

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

    def add_equipment(self, item: Equipment) -> Self:
        """Aggregate ``item`` at the top level of this model."""
        self.equipment.append(item)
        return self

    def add_piping_network_system(self, system: PipingNetworkSystem) -> Self:
        """Aggregate ``system`` at the top level of this model."""
        self.piping_network_systems.append(system)
        return self

    def add_process_instrumentation_function(
        self, function: ProcessInstrumentationFunction
    ) -> Self:
        """Aggregate ``function`` at the top level of this model."""
        self.process_instrumentation_functions.append(function)
        return self

    def add_actuating_system(self, system: ActuatingSystem) -> Self:
        """Aggregate ``system`` at the top level of this model."""
        self.actuating_systems.append(system)
        return self

    def add_actuating_function(self, function: ActuatingFunction) -> Self:
        """Aggregate ``function`` at the top level of this model."""
        self.actuating_functions.append(function)
        return self

    def add_signal_conveying_function(
        self, function: SignalConveyingFunction
    ) -> Self:
        """Aggregate ``function`` at the top level of this model."""
        self.signal_conveying_functions.append(function)
        return self

