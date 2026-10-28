"""The top-level ``ConceptualModel``: a single root aggregating a whole P&ID."""

from __future__ import annotations

from typing import Annotated, Self

from pydantic import Field

from dexpigen.base import XY, Composed, DexpiBaseModel
from dexpigen.equipment import Equipment
from dexpigen.instrumentation import (
    ActuatingSystem,
    InstrumentationLoopFunction,
    ProcessInstrumentationFunction,
)
from dexpigen.piping import PipingNetworkSystem


class ConceptualModel(DexpiBaseModel):
    """The root that aggregates all top-level objects of a P&ID.

    ``SignalConveyingFunction`` and ``ActuatingFunction`` are not top-level:
    they are composed under their owning ``ProcessInstrumentationFunction``.
    ``drawing_extent`` (optional) is the sheet size in mm, written as the
    ``Drawing`` extent.
    """

    drawing_extent: XY | None = None

    equipment: Annotated[list[Equipment], Composed] = Field(default_factory=list)
    piping_network_systems: Annotated[list[PipingNetworkSystem], Composed] = Field(
        default_factory=list
    )
    process_instrumentation_functions: Annotated[
        list[ProcessInstrumentationFunction], Composed
    ] = Field(default_factory=list)
    actuating_systems: Annotated[list[ActuatingSystem], Composed] = Field(
        default_factory=list
    )
    instrumentation_loop_functions: Annotated[
        list[InstrumentationLoopFunction], Composed
    ] = Field(default_factory=list)

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

    def add_instrumentation_loop_function(
        self, loop: InstrumentationLoopFunction
    ) -> Self:
        """Aggregate ``loop`` at the top level of this model."""
        self.instrumentation_loop_functions.append(loop)
        return self
