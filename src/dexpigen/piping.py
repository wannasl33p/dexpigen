"""Piping: network systems, segments, connections, and the source/target roles.

``PipingNetworkSystem`` (the line) composes ``PipingNetworkSegment`` objects; a
segment composes in-line ``items`` and endpoint ``connections`` (``Pipe``).
``PipingSourceItem`` / ``PipingTargetItem`` / ``PipingNodeOwner`` are abstract
role bases that concrete endpoint items (``Nozzle`` now, piping components and
off-page connectors later) implement, so a connection's source/target typing
carries the DEXPI endpoint-subtype restriction.
"""

from __future__ import annotations

from typing import Annotated, ClassVar, Self

from pydantic import Field, PrivateAttr, model_validator

from dexpigen.base import (
    Composed,
    DexpiBaseModel,
    Ref,
    reject_duplicates,
    reject_recomposition,
)
from dexpigen.enumerations import (
    OnHoldClassification,
    PipingClassArtefactClassification,
)

_NODE_ALREADY_COMPOSED = "node is already composed under this owner"
_ITEM_ALREADY_COMPOSED = "item is already composed under this segment"
_CONNECTION_ALREADY_COMPOSED = "connection is already composed under this segment"
_SEGMENT_ALREADY_COMPOSED = "segment is already composed under this system"


class PipingNode(DexpiBaseModel):
    """A connection point owned by a ``PipingNodeOwner``."""

    _owner: PipingNodeOwner | None = PrivateAttr(default=None)


class PipingNodeOwner(DexpiBaseModel):
    """Abstract role: composes ``PipingNode`` connection points."""

    _abstract: ClassVar[bool] = True

    nodes: Annotated[list[PipingNode], Composed] = Field(default_factory=list)
    # 1-based indices into ``nodes`` naming the flow-in / flow-out ports
    # (serialized as ConnectionPoints FlowIn/FlowOut). ``None`` = not declared.
    flow_in_index: int | None = None
    flow_out_index: int | None = None

    @model_validator(mode="after")
    def _bind_nodes(self) -> Self:
        reject_duplicates(self.nodes, _NODE_ALREADY_COMPOSED)
        for node in self.nodes:
            self._adopt_node(node)
        return self

    def add_node(self, node: PipingNode) -> Self:
        """Compose ``node`` under this owner, enforcing single ownership."""
        reject_recomposition(node, self.nodes, _NODE_ALREADY_COMPOSED)
        self._adopt_node(node)
        self.nodes.append(node)
        return self

    def _adopt_node(self, node: PipingNode) -> None:
        owner = node._owner
        if owner is not None and owner is not self:
            raise ValueError("node is already owned by another owner")
        node._owner = self


class PipingSourceItem(PipingNodeOwner):
    """Abstract role: a valid piping source item."""

    _abstract: ClassVar[bool] = True


class PipingTargetItem(PipingNodeOwner):
    """Abstract role: a valid piping target item."""

    _abstract: ClassVar[bool] = True


class SensingLocation(DexpiBaseModel):
    """Abstract role: a piping object a process signal generating function can
    be located in (``Nozzle``, ``PipingComponent``, ``PipingNetworkSegment``)."""

    _abstract: ClassVar[bool] = True


class PipingConnection(DexpiBaseModel):
    """Abstract base for a piping connection between two endpoints."""

    _abstract: ClassVar[bool] = True

    source_item: Annotated[PipingSourceItem | None, Ref] = None
    source_node: Annotated[PipingNode | None, Ref] = None
    target_item: Annotated[PipingTargetItem | None, Ref] = None
    target_node: Annotated[PipingNode | None, Ref] = None

    _owner: PipingNetworkSegment | None = PrivateAttr(default=None)

    @model_validator(mode="after")
    def _check_node_ownership(self) -> Self:
        if self.source_node is not None and (
            self.source_item is None or self.source_node not in self.source_item.nodes
        ):
            raise ValueError("connection source node must belong to its source item")
        if self.target_node is not None and (
            self.target_item is None or self.target_node not in self.target_item.nodes
        ):
            raise ValueError("connection target node must belong to its target item")
        return self


class Pipe(PipingConnection):
    """A concrete piping connection between two endpoints."""


class PipingNetworkSegmentItem(DexpiBaseModel):
    """Abstract role: an in-line item composed in a segment's ``items``."""

    _abstract: ClassVar[bool] = True

    _owner: PipingNetworkSegment | None = PrivateAttr(default=None)


class PipingComponent(
    PipingNetworkSegmentItem, PipingSourceItem, PipingTargetItem, SensingLocation
):
    """Abstract base for an in-line piping component (valve or fitting).

    A component sits in a segment's ``items``, owns ``PipingNode`` connection
    points, and can serve as both a piping source and target item.
    """

    _abstract: ClassVar[bool] = True

    fluid_code: str | None = None
    on_hold: OnHoldClassification | None = None
    piping_class_artefact: PipingClassArtefactClassification | None = None
    pressure_test_circuit_number: str | None = None
    piping_component_name: str | None = None
    piping_component_number: str | None = None


class OperatedValve(PipingComponent):
    """Concrete family root and fallback for an unspecified operated valve."""
    component_class: ClassVar[str] = "OperatedValve"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS11141590"


class CheckValve(PipingComponent):
    """Concrete family root and fallback for an unspecified check valve."""
    component_class: ClassVar[str] = "CheckValve"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS292229"


class SafetyValveOrFitting(PipingComponent):
    """Concrete family root and fallback for an unspecified safety valve/fitting."""
    component_class: ClassVar[str] = "SafetyValveOrFitting"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/SafetyValveOrFitting"


# Named operated-valve leaves, mapped 1:1 from the extraction vocabulary
# (issue 07): ``ball``/``globe``/``butterfly``/``needle``/``gate``.

class BallValve(OperatedValve):
    component_class: ClassVar[str] = "BallValve"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS416654"
class GlobeValve(OperatedValve):
    component_class: ClassVar[str] = "GlobeValve"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS416204"
class ButterflyValve(OperatedValve):
    component_class: ClassVar[str] = "ButterflyValve"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS416609"
class NeedleValve(OperatedValve):
    component_class: ClassVar[str] = "NeedleValve"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS421064"
class GateValve(OperatedValve):
    component_class: ClassVar[str] = "GateValve"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS416519"


class FlowMeasuringElement(PipingComponent):
    """An in-line flow measuring element, a sensing location for a flow signal."""

    component_class: ClassVar[str] = "FlowMeasuringElement"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/FlowMeasuringElement"


class PipeFitting(PipingComponent):
    """Concrete family root and fallback for an unspecified pipe fitting.

    DEXPI 1.3 (section 8.43) marks ``PipeFitting`` as a class, not an abstract
    class, with its own ``ComponentClass``; the C03 example instantiates it.
    """

    component_class: ClassVar[str] = "PipeFitting"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/PipeFitting"


class Flange(PipeFitting):
    component_class: ClassVar[str] = "Flange"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS13307654"
class PipeTee(PipeFitting):
    component_class: ClassVar[str] = "PipeTee"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS427724"
class PipeReducer(PipeFitting):
    component_class: ClassVar[str] = "PipeReducer"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS416294"
class LineBlind(PipeFitting):
    component_class: ClassVar[str] = "LineBlind"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS280034"


class PipeOffPageConnector(PipingNetworkSegmentItem, PipingNodeOwner):
    """Abstract base for a pipe off-page connector.

    A connector sits in a segment's ``items`` and owns ``PipingNode`` points;
    the concrete flow-in/flow-out subtypes add the source/target role.
    """

    _abstract: ClassVar[bool] = True

    connector_reference: Annotated[PipeOffPageConnectorReference | None, Composed] = None

    @model_validator(mode="after")
    def _bind_connector_reference(self) -> Self:
        if self.connector_reference is not None:
            self._adopt_connector_reference(self.connector_reference)
        return self

    def add_connector_reference(
        self, reference: PipeOffPageConnectorReference
    ) -> Self:
        """Compose ``reference`` under this connector, enforcing single ownership."""
        self._adopt_connector_reference(reference)
        self.connector_reference = reference
        return self

    def _adopt_connector_reference(self, reference: PipeOffPageConnectorReference) -> None:
        owner = reference._owner
        if owner is not None and owner is not self:
            raise ValueError("connector reference is already owned by another connector")
        reference._owner = self


class FlowInPipeOffPageConnector(PipeOffPageConnector, PipingSourceItem):
    """A pipe off-page connector that is a valid piping source."""
    component_class: ClassVar[str] = "FlowInPipeOffPageConnector"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/FlowInPipeOffPageConnector"


class FlowOutPipeOffPageConnector(PipeOffPageConnector, PipingTargetItem):
    """A pipe off-page connector that is a valid piping target."""
    component_class: ClassVar[str] = "FlowOutPipeOffPageConnector"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/FlowOutPipeOffPageConnector"


class PipeOffPageConnectorReference(DexpiBaseModel):
    """Abstract base for a reference to a pipe off-page connector."""

    _abstract: ClassVar[bool] = True

    _owner: PipeOffPageConnector | None = PrivateAttr(default=None)


class PipeOffPageConnectorObjectReference(PipeOffPageConnectorReference):
    """A reference to a ``PipeOffPageConnector`` object."""
    component_class: ClassVar[str] = "PipeOffPageConnectorObjectReference"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/PipeOffPageConnectorObjectReference"

    referenced_connector: Annotated[PipeOffPageConnector | None, Ref] = None


class PipeOffPageConnectorReferenceByNumber(PipeOffPageConnectorReference):
    """A reference to a pipe off-page connector by drawing and connector number."""
    component_class: ClassVar[str] = "PipeOffPageConnectorReferenceByNumber"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/PipeOffPageConnectorReferenceByNumber"

    referenced_connector_number: str | None = None
    referenced_drawing_number: str | None = None


class PipingNetworkSegment(SensingLocation):
    """A stretch of a ``PipingNetworkSystem``."""
    component_class: ClassVar[str] = "PipingNetworkSegment"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS267704"

    segment_number: str | None = None
    fluid_code: str | None = None
    piping_class_code: str | None = None

    items: Annotated[list[PipingNetworkSegmentItem], Composed] = Field(default_factory=list)
    connections: Annotated[list[PipingConnection], Composed] = Field(default_factory=list)

    _owner: PipingNetworkSystem | None = PrivateAttr(default=None)

    @model_validator(mode="after")
    def _bind_children(self) -> Self:
        reject_duplicates(self.items, _ITEM_ALREADY_COMPOSED)
        reject_duplicates(self.connections, _CONNECTION_ALREADY_COMPOSED)
        for item in self.items:
            self._adopt_item(item)
        for connection in self.connections:
            self._adopt_connection(connection)
        return self

    def add_item(self, item: PipingNetworkSegmentItem) -> Self:
        """Compose ``item`` under this segment, enforcing single ownership."""
        reject_recomposition(item, self.items, _ITEM_ALREADY_COMPOSED)
        self._adopt_item(item)
        self.items.append(item)
        return self

    def add_connection(self, connection: PipingConnection) -> Self:
        """Compose ``connection`` under this segment, enforcing single ownership."""
        reject_recomposition(connection, self.connections, _CONNECTION_ALREADY_COMPOSED)
        self._adopt_connection(connection)
        self.connections.append(connection)
        return self

    def _adopt_item(self, item: PipingNetworkSegmentItem) -> None:
        owner = item._owner
        if owner is not None and owner is not self:
            raise ValueError("item is already owned by another segment")
        item._owner = self

    def _adopt_connection(self, connection: PipingConnection) -> None:
        owner = connection._owner
        if owner is not None and owner is not self:
            raise ValueError("connection is already owned by another segment")
        connection._owner = self


class PipingNetworkSystem(DexpiBaseModel):
    """The DEXPI line object, composed of ``PipingNetworkSegment`` objects."""
    component_class: ClassVar[str] = "PipingNetworkSystem"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS270359"

    line_number: str | None = None
    fluid_code: str | None = None
    piping_class_code: str | None = None

    segments: Annotated[list[PipingNetworkSegment], Composed] = Field(default_factory=list)

    @model_validator(mode="after")
    def _bind_segments(self) -> Self:
        reject_duplicates(self.segments, _SEGMENT_ALREADY_COMPOSED)
        for segment in self.segments:
            self._adopt_segment(segment)
        return self

    def add_segment(self, segment: PipingNetworkSegment) -> Self:
        """Compose ``segment`` under this system, enforcing single ownership."""
        reject_recomposition(segment, self.segments, _SEGMENT_ALREADY_COMPOSED)
        self._adopt_segment(segment)
        self.segments.append(segment)
        return self

    def _adopt_segment(self, segment: PipingNetworkSegment) -> None:
        owner = segment._owner
        if owner is not None and owner is not self:
            raise ValueError("segment is already owned by another system")
        segment._owner = self
