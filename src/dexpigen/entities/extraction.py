"""Check a Dex extraction against the input contract and normalise it.

The input is the pipeline's in-memory objects, not a file: the Dex graph (a
NetworkX graph), its Entities and the ``DrawingSize``, all in image pixels.
``check_extraction`` collects every contract violation into one
``DexExtractionError``; an extraction that passes comes back as a
``DexExtraction`` with typed accessors for the graph conventions.

Dex graph conventions:

- node attribute ``node_type``: ``object``, ``junction`` or ``deadend``;
- an ``object`` node has the id of its ``SymbolEntity`` / ``EquipmentEntity``;
- a ``junction`` / ``deadend`` node has no Entity; its position is the shapely
  ``Point`` in node attribute ``geometry``;
- edge attribute ``id`` names the edge's ``SegmentEntity``. An edge without one
  must be an attachment: its ends are (``equipment``, ``nozzle``) or
  (``actuator``, ``valve`` / ``control-valve``);
- optional edge attribute ``direction`` (or ``dualflow: True``): a hint
  relative to the point order of the segment geometry.

Other node and edge attributes (labels, node polygons, edge geometry) are not read.
"""

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

import networkx as nx
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from shapely import Point

from dexpigen.entities.base import Entity
from dexpigen.entities.equipment import EquipmentEntity
from dexpigen.entities.segment import SegmentEntity
from dexpigen.entities.symbol import SymbolEntity


class NodeType(StrEnum):
    """The kind of a Dex graph node (its ``node_type`` attribute; a closed set)."""

    OBJECT = "object"  # has an Entity with the same id
    JUNCTION = "junction"  # a line junction (a tee); no Entity
    DEADEND = "deadend"  # an open line end; no Entity


class Direction(StrEnum):
    """A line's flow direction, relative to the point order of its segment geometry."""

    FORWARD = "forward"  # from the first point to the last
    REVERSE = "reverse"  # from the last point to the first
    BIDIRECTIONAL = "bidirectional"  # both ways; the pipeline may write ``dualflow: True`` instead


class DrawingSize(BaseModel):
    """The drawing size of a Dex extraction: the ``size.json`` fields.

    It relates image pixels to drawing millimetres; the input layer itself keeps pixels.
    """

    model_config = ConfigDict(frozen=True)

    image_width: int = Field(gt=0)  # px
    image_height: int = Field(gt=0)  # px
    drawing_width: float = Field(gt=0, allow_inf_nan=False)  # mm
    drawing_height: float = Field(gt=0, allow_inf_nan=False)  # mm


class DexExtractionError(ValueError):
    """A Dex extraction that breaks the input contract; ``problems`` lists every violation found."""

    def __init__(self, problems: list[str]) -> None:
        self.problems = problems
        count = f"{len(problems)} problem{'' if len(problems) == 1 else 's'}"
        lines = "\n".join(f"- {problem}" for problem in problems)
        super().__init__(f"{count} in the Dex extraction:\n{lines}")


# Our Entity classes by name: a pipeline object converts to the one named in its MRO.
_ENTITY_CLASSES: dict[str, type[Entity]] = {
    cls.__name__: cls for cls in (SymbolEntity, EquipmentEntity, SegmentEntity)
}

# The end labels an edge without a SegmentEntity may join: equipment-nozzle
# membership and the actuator on its valve.
_ATTACHMENTS = frozenset(
    {
        frozenset({"equipment", "nozzle"}),
        frozenset({"actuator", "valve"}),
        frozenset({"actuator", "control-valve"}),
    }
)


def _direction(edge: Mapping[str, Any]) -> Direction | None:
    """The direction hint of an edge; ``ValueError`` when it is malformed."""
    value, dualflow = edge.get("direction"), edge.get("dualflow")
    if dualflow is not None and not isinstance(dualflow, bool):
        raise ValueError(f"unknown dualflow value {dualflow!r}")
    if value is None:
        return Direction.BIDIRECTIONAL if dualflow else None
    try:
        direction = Direction(value)
    except ValueError:
        raise ValueError(f"unknown direction {value!r}") from None
    if dualflow and direction is not Direction.BIDIRECTIONAL:
        raise ValueError(f"direction {direction.value!r} but dualflow true")
    return direction


@dataclass(frozen=True, eq=False)
class DexExtraction:
    """A Dex extraction that passed ``check_extraction``.

    ``graph`` is an undirected copy of the input graph in which every Entity
    missing from it is an isolated ``object`` node; ``entities`` holds the
    normalised Entities by id, in input order.
    """

    graph: nx.Graph
    entities: dict[str, Entity]
    size: DrawingSize

    def node_type(self, node: str) -> NodeType:
        """The kind of ``node``."""
        return NodeType(self.graph.nodes[node]["node_type"])

    def point(self, node: str) -> Point:
        """The position of a ``junction`` or ``deadend`` node, in image pixels."""
        return self.graph.nodes[node]["geometry"]

    def segment(self, u: str, v: str) -> SegmentEntity | None:
        """The line Entity of the edge ``u``-``v``; ``None`` for an attachment."""
        edge_id = self.graph.edges[u, v].get("id")
        entity = self.entities.get(edge_id) if isinstance(edge_id, str) else None
        return entity if isinstance(entity, SegmentEntity) else None

    def direction(self, u: str, v: str) -> Direction | None:
        """The edge's direction hint; ``None`` when unknown and for an attachment."""
        if self.segment(u, v) is None:
            return None
        return _direction(self.graph.edges[u, v])


def check_extraction(
    graph: nx.Graph,
    entities: Iterable[Entity | BaseModel],
    size: DrawingSize | Mapping[str, Any] | BaseModel,
) -> DexExtraction:
    """Check one Dex extraction against the input contract and return it normalised.

    ``graph`` is the Dex graph: an ``nx.Graph``, or an ``nx.DiGraph`` whose
    direction is ignored; parallel edges (a ``MultiGraph``) are not supported.
    ``entities`` may mix this library's Entities with the pipeline's own: a
    pipeline object converts to the class of the same name in its MRO through
    ``model_dump``. ``size`` is a ``DrawingSize`` or its fields.

    Raises ``DexExtractionError`` listing every violation: an Entity that is no
    ``SymbolEntity``, ``EquipmentEntity`` or ``SegmentEntity``, a non-string
    node id, duplicate ids, an ``object`` node without an Entity or a label, a
    junction or dead end with an Entity or without a point, a ``SegmentEntity``
    without an edge, an edge without a segment that is not an attachment,
    broken geometry, and an unknown ``node_type``, line kind or direction.
    An unknown label, extra fields and an Entity missing from the graph pass.
    When the graph itself is unusable (not NetworkX, or with parallel edges),
    its nodes and edges are not checked; neither are the node and edges of an
    Entity that failed to convert. The input graph is not modified.
    """
    problems: list[str] = []
    by_id, rejected = _normalise_entities(entities, problems)
    drawing_size = _normalise_size(size, problems)
    simple = _simple_graph(graph, problems)
    if simple is not None:
        _check_graph(simple, by_id, rejected, problems)
    if problems or simple is None or drawing_size is None:
        raise DexExtractionError(problems)
    for entity_id, entity in by_id.items():
        if not isinstance(entity, SegmentEntity) and entity_id not in simple:
            simple.add_node(entity_id, node_type=NodeType.OBJECT.value)
    return DexExtraction(graph=simple, entities=by_id, size=drawing_size)


def _normalise_entities(entities: Iterable[Any], problems: list[str]) -> tuple[dict[str, Entity], set[str]]:
    """Our Entities by id, and the ids of the objects that failed to convert."""
    by_id: dict[str, Entity] = {}
    rejected: set[str] = set()
    duplicates: set[str] = set()
    for index, obj in enumerate(entities):
        entity = _normalise_entity(index, obj, problems)
        if entity is None:
            if isinstance(obj_id := getattr(obj, "id", None), str):
                rejected.add(obj_id)
            continue
        if entity.id not in by_id:
            by_id[entity.id] = entity
        elif entity.id not in duplicates:
            duplicates.add(entity.id)
            problems.append(f"duplicate Entity id {entity.id!r}")
    return by_id, rejected


def _normalise_entity(index: int, obj: Any, problems: list[str]) -> Entity | None:
    if isinstance(obj, SymbolEntity | EquipmentEntity | SegmentEntity):
        return obj
    cls = next(
        (_ENTITY_CLASSES[base.__name__] for base in type(obj).__mro__ if base.__name__ in _ENTITY_CLASSES),
        None,
    )
    if cls is None or not isinstance(obj, BaseModel):
        problems.append(f"Entity #{index}: unsupported type {type(obj).__name__}")
        return None
    try:
        return cls.model_validate(obj.model_dump())
    except (TypeError, ValueError) as exc:  # ValidationError is a ValueError
        problems.append(f"Entity #{index} ({type(obj).__name__} {getattr(obj, 'id', None)!r}): {_one_line(exc)}")
        return None


def _normalise_size(size: Any, problems: list[str]) -> DrawingSize | None:
    if isinstance(size, DrawingSize):
        return size
    try:
        return DrawingSize.model_validate(size.model_dump() if isinstance(size, BaseModel) else size)
    except (TypeError, ValueError) as exc:  # ValidationError is a ValueError
        problems.append(f"invalid DrawingSize: {_one_line(exc)}")
        return None


def _one_line(exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        return "; ".join(
            f"{'.'.join(str(part) for part in error['loc']) or 'value'}: {error['msg']}" for error in exc.errors()
        )
    return str(exc)


def _simple_graph(graph: Any, problems: list[str]) -> nx.Graph | None:
    """An undirected copy of ``graph``; ``None`` (with a problem) when it is not a simple NetworkX graph."""
    if not isinstance(graph, nx.Graph):
        problems.append(f"the Dex graph must be a networkx Graph, got {type(graph).__name__}")
        return None
    if graph.is_multigraph():
        problems.append(f"parallel edges are not supported (got a {type(graph).__name__})")
        return None
    both_ways: list[tuple[Any, Any]] = []
    if graph.is_directed():
        seen: set[frozenset[Any]] = set()
        for u, v in graph.edges:
            if u != v and graph.has_edge(v, u) and frozenset((u, v)) not in seen:
                seen.add(frozenset((u, v)))
                both_ways.append((u, v))
    for u, v in both_ways:
        problems.append(f"parallel edges are not supported: {u!r} and {v!r} are linked both ways")
    return None if both_ways else nx.Graph(graph)


def _label(entity: Entity | None) -> str | None:
    return None if entity is None or isinstance(entity, SegmentEntity) else entity.label


def _is_point(geometry: Any) -> bool:
    return (
        isinstance(geometry, Point)
        and not geometry.is_empty
        and math.isfinite(geometry.x)
        and math.isfinite(geometry.y)
    )


def _check_graph(graph: nx.Graph, entities: dict[str, Entity], rejected: set[str], problems: list[str]) -> None:
    """Check the graph conventions; nodes and edges of a ``rejected`` Entity id are skipped."""
    # Edge ids (a dict keeps them in graph order): unique, and never the id of a node.
    edge_ids: dict[str, None] = {}
    duplicates: set[str] = set()
    for _, _, edge_id in graph.edges(data="id"):
        if not isinstance(edge_id, str):
            continue
        if edge_id in edge_ids and edge_id not in duplicates:
            duplicates.add(edge_id)
            problems.append(f"duplicate edge id {edge_id!r}")
        edge_ids[edge_id] = None
    for edge_id in edge_ids:
        if edge_id in graph:
            problems.append(f"id {edge_id!r} names both a node and an edge")

    for node, data in graph.nodes(data=True):
        if not isinstance(node, str):
            problems.append(f"node {node!r} has a non-string id")
            continue
        raw = data.get("node_type")
        try:
            node_type = NodeType(raw)
        except ValueError:
            problems.append(f"node {node!r} has unknown node_type {raw!r}")
            continue
        entity = entities.get(node)
        if node_type is NodeType.OBJECT:
            if _label(entity) is None and node not in rejected:
                problems.append(f"object node {node!r} has no Entity")
            continue
        if entity is not None:
            problems.append(f"{node_type} node {node!r} has an Entity")
        if not _is_point(data.get("geometry")):
            problems.append(f"{node_type} node {node!r} has no point geometry")

    for u, v, data in graph.edges(data=True):
        edge_id = data.get("id")
        if u in rejected or v in rejected or (isinstance(edge_id, str) and edge_id in rejected):
            continue
        segment = entities.get(edge_id) if isinstance(edge_id, str) else None
        if isinstance(segment, SegmentEntity):
            try:
                _direction(data)
            except ValueError as exc:
                problems.append(f"edge {edge_id!r} has {exc}")
            continue
        if frozenset({_label(entities.get(u)), _label(entities.get(v))}) not in _ATTACHMENTS:
            name = f"edge {edge_id!r} between" if edge_id is not None else "edge between"
            problems.append(f"{name} {u!r} and {v!r} has no SegmentEntity and is not an attachment")

    for entity_id, entity in entities.items():
        if isinstance(entity, SegmentEntity):
            if entity_id not in edge_ids:
                problems.append(f"SegmentEntity {entity_id!r} has no edge in the Dex graph")
            try:
                _ = entity.kind  # reading the kind checks it
            except ValueError as exc:
                problems.append(str(exc))
        elif entity_id in edge_ids:
            problems.append(f"{type(entity).__name__} {entity_id!r} has the id of an edge")
        elif not entity.label.strip():
            # An Entity missing from the graph becomes an object node; on a
            # junction or dead end its presence is the problem, not its label.
            node_type = graph.nodes[entity_id].get("node_type") if entity_id in graph else NodeType.OBJECT
            if node_type == NodeType.OBJECT:
                problems.append(f"object node {entity_id!r} has no label")
