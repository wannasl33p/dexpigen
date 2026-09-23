"""Piping: network systems, segments, connections, and the source/target roles.

``PipingNetworkSystem`` (the line) composes ``PipingNetworkSegment`` objects; a
segment composes in-line ``items`` and endpoint ``connections`` (``Pipe``).
``PipingSourceItem`` / ``PipingTargetItem`` / ``PipingNodeOwner`` are abstract
role bases that concrete endpoint items (``Nozzle`` now, piping components and
off-page connectors later) implement, so a connection's source/target typing
carries the DEXPI endpoint-subtype restriction.
"""

from __future__ import annotations

from typing import ClassVar, Self

from pydantic import Field, PrivateAttr, model_validator

from dexpigen.base import DexpiBaseModel


class PipingNode(DexpiBaseModel):
    """A connection point owned by a ``PipingNodeOwner``."""

    _owner: PipingNodeOwner | None = PrivateAttr(default=None)


class PipingNodeOwner(DexpiBaseModel):
    """Abstract role: composes ``PipingNode`` connection points."""

    _abstract: ClassVar[bool] = True

    nodes: list[PipingNode] = Field(default_factory=list)

    @model_validator(mode="after")
    def _bind_nodes(self) -> Self:
        for node in self.nodes:
            self._adopt_node(node)
        return self

    def add_node(self, node: PipingNode) -> Self:
        """Compose ``node`` under this owner, enforcing single ownership."""
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


class PipingConnection(DexpiBaseModel):
    """Abstract base for a piping connection between two endpoints."""

    _abstract: ClassVar[bool] = True

    source_item: PipingSourceItem | None = None
    source_node: PipingNode | None = None
    target_item: PipingTargetItem | None = None
    target_node: PipingNode | None = None

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


class PipingNetworkSegment(DexpiBaseModel):
    """A stretch of a ``PipingNetworkSystem``."""

    segment_number: str | None = None

    items: list[PipingNetworkSegmentItem] = Field(default_factory=list)
    connections: list[PipingConnection] = Field(default_factory=list)

    _owner: PipingNetworkSystem | None = PrivateAttr(default=None)

    @model_validator(mode="after")
    def _bind_children(self) -> Self:
        for item in self.items:
            self._adopt_item(item)
        for connection in self.connections:
            self._adopt_connection(connection)
        return self

    def add_item(self, item: PipingNetworkSegmentItem) -> Self:
        """Compose ``item`` under this segment, enforcing single ownership."""
        self._adopt_item(item)
        self.items.append(item)
        return self

    def add_connection(self, connection: PipingConnection) -> Self:
        """Compose ``connection`` under this segment, enforcing single ownership."""
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

    line_number: str | None = None
    fluid_code: str | None = None
    piping_class_code: str | None = None

    segments: list[PipingNetworkSegment] = Field(default_factory=list)

    @model_validator(mode="after")
    def _bind_segments(self) -> Self:
        for segment in self.segments:
            self._adopt_segment(segment)
        return self

    def add_segment(self, segment: PipingNetworkSegment) -> Self:
        """Compose ``segment`` under this system, enforcing single ownership."""
        self._adopt_segment(segment)
        self.segments.append(segment)
        return self

    def _adopt_segment(self, segment: PipingNetworkSegment) -> None:
        owner = segment._owner
        if owner is not None and owner is not self:
            raise ValueError("segment is already owned by another system")
        segment._owner = self
