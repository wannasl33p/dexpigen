"""C01 Dex sample adapter: ``graph.json`` and ``size.json`` -> the ``dexpigen.entities`` input.

NOT public API. This module loads the sample in ``examples/C01/dex_model/`` so that the input
layer of ``dexpigen.entities`` can run on real data. ``tests/test_c01_dex_sample.py`` imports
it by file path. ``load()`` returns three things:

- a ``networkx.Graph``. A node carries ``node_type``, ``label`` and ``geometry``: a shapely
  ``Point`` for a junction or deadend, a ``Polygon`` for an object. An edge carries ``id``
  and ``geometry`` (a shapely ``LineString``). A line edge also carries
  ``direction="forward"``, because its geometry runs from the source node to the target
  node. An attachment edge carries no direction;
- the Entities: an ``EquipmentEntity`` or a ``SymbolEntity`` for each object node, and a
  ``SegmentEntity`` for each line edge. An attachment edge has no Entity;
- the ``DrawingSize`` read from ``size.json``.

In ``graph.json`` an object's polygon is ONE ring ``[[x, y], ...]``, not GeoJSON's list of
rings. All coordinates stay in image pixels with y down; nothing is converted here.

Run it from the repository root. It loads the sample, runs ``check_extraction``, prints a
short summary, converts the sample with ``dex_to_model`` (printing the report) and writes
and validates the Proteus XML::

    uv run python examples/C01/dex_model/load.py
"""

import json
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

import networkx as nx
from shapely.geometry import LineString, Point, Polygon

from dexpigen.entities import (
    DrawingSize,
    Entity,
    EquipmentEntity,
    SegmentEntity,
    SymbolEntity,
    check_extraction,
    dex_to_model,
)

HERE = Path(__file__).resolve().parent

# Line edges: the suffix of the edge id, and the line kind of its SegmentEntity.
LINE_KIND_BY_SUFFIX = {"_line": "piping", "_dashed": "signal-line"}


def load(directory: Path = HERE) -> tuple[nx.Graph, list[Entity], DrawingSize]:
    """Read ``graph.json`` and ``size.json`` from ``directory``.

    Raises ``ValueError`` for a node or edge the adapter cannot map: an object that is not
    equipment and whose ring is not a closed 5-point ring, or an edge id that matches no rule.
    """
    data = json.loads((directory / "graph.json").read_text(encoding="utf-8"))
    size = DrawingSize.model_validate(
        json.loads((directory / "size.json").read_text(encoding="utf-8"))
    )

    graph = nx.Graph()
    entities: list[Entity] = []
    for node in data["nodes"]:
        graph.add_node(
            node["id"],
            node_type=node["node_type"],
            label=node["label"],
            geometry=_geometry(node["geometry"]),
        )
        if node["node_type"] == "object":
            entities.append(_object_entity(node))

    for edge in data["edges"]:
        edge_id = edge["id"]
        line = LineString(edge["geometry"]["coordinates"])
        attributes = {"id": edge_id, "geometry": line}
        kind = _line_kind(edge_id)
        if kind is not None:
            attributes["direction"] = "forward"
            entities.append(
                SegmentEntity(
                    id=edge_id,
                    geometry=line,
                    attributes={"line_attributes": {"kind": kind}},
                )
            )
        graph.add_edge(edge["source"], edge["target"], **attributes)

    return graph, entities, size


def _geometry(geometry: dict) -> Point | Polygon:
    """Return the shapely geometry of a node. A Polygon is ONE ring, not a list of rings."""
    coordinates = geometry["coordinates"]
    if geometry["type"] == "Point":
        return Point(*coordinates)
    if geometry["type"] == "Polygon":
        return Polygon(coordinates)
    raise ValueError(f"unsupported node geometry type {geometry['type']!r}")


def _object_entity(node: dict) -> Entity:
    """Return the Entity of an ``object`` node.

    Equipment keeps its full ring as the polygon. Any other label becomes a symbol whose quad
    is the first four points of its ring, which must be closed and have 5 points.
    """
    node_id, label = node["id"], node["label"]
    ring = node["geometry"]["coordinates"]
    if label == "equipment":
        return EquipmentEntity(id=node_id, polygon=Polygon(ring))
    if len(ring) != 5 or ring[0] != ring[-1]:
        raise ValueError(f"object node {node_id!r} ({label}) is not a closed 5-point ring")
    return SymbolEntity(id=node_id, symbol_class=label, quad=ring[:4])


def _line_kind(edge_id: str) -> str | None:
    """Return the line kind of an edge id, or ``None`` when the edge is an attachment.

    ``<a>:<b>`` is an equipment-nozzle link and ``*_actuator`` an actuator-control-valve
    link. The colon test comes first, because the node ids inside ``<a>:<b>`` can end in
    ``_line`` (junction ids do).
    """
    if ":" in edge_id or edge_id.endswith("_actuator"):
        return None
    for suffix, kind in LINE_KIND_BY_SUFFIX.items():
        if edge_id.endswith(suffix):
            return kind
    raise ValueError(f"edge id {edge_id!r} matches no line or attachment rule")


def _tally(values: Iterable[object]) -> str:
    """Return ``value=count`` pairs sorted by value, for the console summary."""
    counts = Counter(str(value) for value in values)
    return ", ".join(f"{value}={count}" for value, count in sorted(counts.items()))


if __name__ == "__main__":
    import sys
    import tempfile

    from dexpigen import to_proteus_xml

    sys.path.insert(0, str(HERE.parents[1]))  # examples/, for validate_dexpi
    from validate_dexpi import validate

    sample = load()
    extraction = check_extraction(*sample)
    segments = [extraction.segment(u, v) for u, v in extraction.graph.edges]
    print("check_extraction: ok")
    print(
        "nodes by node_type:",
        _tally(extraction.node_type(node) for node in extraction.graph.nodes),
    )
    print(
        "line edges by kind:",
        _tally(segment.kind for segment in segments if segment is not None),
    )
    print("attachment edges:", sum(segment is None for segment in segments))

    conversion = dex_to_model(*sample, model_id="C01")
    print("dex_to_model report:", *conversion.report, sep="\n  ")
    out = Path(tempfile.gettempdir()) / "c01_dex.xml"
    out.write_text(to_proteus_xml(conversion.model), encoding="utf-8")
    sys.exit(0 if validate(str(out)) else 1)
