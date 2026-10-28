"""The C01 Dex sample loads into the ``dexpigen.entities`` input and passes ``check_extraction``.

``examples/C01/dex_model/load.py`` is an adapter, not public API. It turns ``graph.json`` and
``size.json`` into a ``networkx.Graph``, a list of Entities and a ``DrawingSize``. The tests
load it by file path, as ``tests/test_recipes.py`` loads the example scripts. They check the
sample's counts, its attachments, the direction and kind of its lines, the node positions,
the drawing size and the symbol quads, and they check that malformed samples are rejected.
"""

import importlib.util
import json
import re
from collections import Counter
from pathlib import Path

import networkx as nx
import pytest
from shapely.geometry import Point

from dexpigen.entities import (
    DexExtraction,
    Direction,
    DrawingSize,
    EquipmentEntity,
    LineKind,
    NodeType,
    SegmentEntity,
    SymbolEntity,
    check_extraction,
)

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "examples" / "C01" / "dex_model" / "load.py"
SMALL_SIZE = {
    "image_width": 100,
    "image_height": 100,
    "drawing_width": 10.0,
    "drawing_height": 10.0,
    "units": "mm",
}


def _load_adapter():
    spec = importlib.util.spec_from_file_location("c01_dex_load", ADAPTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _junction_node(node_id: str, x: float, y: float) -> dict:
    return {
        "id": node_id,
        "node_type": "junction",
        "label": None,
        "geometry": {"type": "Point", "coordinates": [x, y]},
    }


def _object_node(node_id: str, label: str, ring: list[list[float]]) -> dict:
    return {
        "id": node_id,
        "node_type": "object",
        "label": label,
        "geometry": {"type": "Polygon", "coordinates": ring},
    }


def _edge(edge_id: str, source: str, target: str, coordinates: list[list[float]]) -> dict:
    return {
        "id": edge_id,
        "source": source,
        "target": target,
        "geometry": {"type": "LineString", "coordinates": coordinates},
    }


@pytest.fixture
def sample():
    return _load_adapter().load()


@pytest.fixture
def extraction(sample):
    graph, entities, size = sample
    return check_extraction(graph, entities, size)


def test_graph_has_the_sample_nodes_and_edges(sample):
    graph, _, _ = sample
    assert type(graph) is nx.Graph
    assert graph.number_of_nodes() == 57
    assert graph.number_of_edges() == 59
    kinds = Counter(
        (data["node_type"], data["geometry"].geom_type) for _, data in graph.nodes(data=True)
    )
    assert kinds == {
        ("object", "Polygon"): 48,
        ("junction", "Point"): 5,
        ("deadend", "Point"): 4,
    }


def test_entities_by_class_and_line_kind(sample):
    _, entities, _ = sample
    assert Counter(type(entity) for entity in entities) == {
        EquipmentEntity: 5,
        SymbolEntity: 43,
        SegmentEntity: 37,
    }
    segments = [entity for entity in entities if isinstance(entity, SegmentEntity)]
    assert Counter(segment.kind for segment in segments) == {
        LineKind.PIPING: 34,
        LineKind.SIGNAL_LINE: 3,
    }


def test_check_extraction_accepts_the_sample(sample):
    graph, entities, size = sample
    assert isinstance(check_extraction(graph, entities, size), DexExtraction)


def test_attachments_are_nozzle_and_control_valve_links(sample, extraction):
    graph, _, _ = sample
    attachments = [(u, v) for u, v in graph.edges if extraction.segment(u, v) is None]
    assert len(attachments) == 22
    end_labels = Counter(
        frozenset(graph.nodes[end]["label"] for end in (u, v)) for u, v in attachments
    )
    assert end_labels == {
        frozenset({"equipment", "nozzle"}): 19,
        frozenset({"actuator", "control-valve"}): 3,
    }
    for u, v in attachments:
        assert "direction" not in graph.edges[u, v]
        assert extraction.direction(u, v) is None


def test_line_edges_are_forward_and_keep_their_kind(sample, extraction):
    graph, _, _ = sample
    lines = [
        (u, v, data)
        for u, v, data in graph.edges(data=True)
        if data["id"].endswith(("_line", "_dashed"))
    ]
    assert len(lines) == 37
    for u, v, data in lines:
        segment = extraction.segment(u, v)
        assert segment is not None
        assert segment.id == data["id"]
        expected_kind = LineKind.SIGNAL_LINE if data["id"].endswith("_dashed") else LineKind.PIPING
        assert segment.kind == expected_kind
        assert data["direction"] == "forward"
        assert extraction.direction(u, v) == Direction.FORWARD


def test_junction_and_deadend_positions_come_from_their_nodes(extraction):
    assert extraction.point("deadend-5_line").equals(Point(1428.571, 2404.762))
    assert extraction.node_type("deadend-5_line") == NodeType.DEADEND
    # The id ends in "_line", but this node is a junction: the kind comes from node_type only.
    assert extraction.point("deadend-0_line").equals(Point(3154.762, 1833.476))
    assert extraction.node_type("deadend-0_line") == NodeType.JUNCTION


def test_insulation_is_an_isolated_object_node(sample, extraction):
    graph, _, _ = sample
    # The node id is a UUID, so the node is found by its label.
    nodes = [node for node, data in graph.nodes(data=True) if data["label"] == "insulation"]
    assert len(nodes) == 1
    (node,) = nodes
    assert graph.degree(node) == 0
    assert extraction.node_type(node) == NodeType.OBJECT
    assert extraction.graph.degree(node) == 0


def test_size_comes_from_size_json(sample):
    _, _, size = sample
    assert isinstance(size, DrawingSize)
    assert size.image_width == 5000
    assert size.image_height == 3536
    assert size.drawing_width == 420.0
    assert size.drawing_height == 297.0


def test_every_symbol_quad_is_the_first_four_points_of_its_ring(sample):
    graph, entities, _ = sample
    symbols = [entity for entity in entities if isinstance(entity, SymbolEntity)]
    assert len(symbols) == 43
    for symbol in symbols:
        ring = list(graph.nodes[symbol.id]["geometry"].exterior.coords)
        assert len(symbol.quad) == 4
        assert [tuple(point) for point in symbol.quad] == ring[:4]


@pytest.mark.parametrize(
    ("nodes", "edges", "problem"),
    [
        pytest.param(
            [_object_node("valve-1", "valve", [[0, 0], [10, 0], [10, 5], [0, 5], [3, 3]])],
            [],
            "'valve-1'",
            id="symbol-ring-not-closed",
        ),
        pytest.param(
            [_junction_node("j-1", 0, 0), _junction_node("j-2", 10, 0)],
            [_edge("edge-9_wire", "j-1", "j-2", [[0, 0], [10, 0]])],
            "'edge-9_wire'",
            id="edge-id-without-a-rule",
        ),
    ],
)
def test_malformed_sample_is_rejected(tmp_path, nodes, edges, problem):
    (tmp_path / "graph.json").write_text(
        json.dumps({"nodes": nodes, "edges": edges}), encoding="utf-8"
    )
    (tmp_path / "size.json").write_text(json.dumps(SMALL_SIZE), encoding="utf-8")
    with pytest.raises(ValueError, match=re.escape(problem)):
        _load_adapter().load(tmp_path)
