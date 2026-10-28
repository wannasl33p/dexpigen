"""Black-box tests for the Dex extraction input layer (``dexpigen.entities``).

Written from the API spec alone: the Entity models, ``DrawingSize``, the
normalisation of the pipeline's foreign objects, and ``check_extraction`` with
its ``DexExtraction`` result and ``DexExtractionError`` problems. The pipeline
side is represented by a real ``model_dump()`` sample (``PIPELINE_DUMP``) and
by test-local pydantic classes that carry the pipeline's extra fields.
"""

import dataclasses
import math
import uuid

import networkx as nx
import numpy as np
import pytest
from pydantic import BaseModel, ValidationError
from shapely.geometry import LineString, Point, Polygon

from dexpigen.entities import (
    DexExtraction,
    DexExtractionError,
    Direction,
    DrawingSize,
    Entity,
    EquipmentEntity,
    LineKind,
    NodeType,
    SegmentEntity,
    SymbolEntity,
    check_extraction,
)

# A real model_dump() of the pipeline's dexlib2-based entities, captured before
# dexlib2 was removed. Note the extra fields (``anchor``, and ``quad`` on the
# equipment) and the float32 noise in the coordinates.
PIPELINE_DUMP = [
    {
        "class": "SymbolEntity",
        "dump": {
            "id": "nozzle-0",
            "attributes": {},
            "quad": [
                [1571.4300537109375, 1821.5699462890625],
                [1619.050048828125, 1821.5699462890625],
                [1619.050048828125, 1845.3800048828125],
                [1571.4300537109375, 1845.3800048828125],
            ],
            "symbol_class": "nozzle",
            "confidence": 0.97,
            "anchor": [1619.0476, 1833.4762],
        },
    },
    {
        "class": "EquipmentEntity",
        "dump": {
            "id": "529f6fe5-8667-5f52-8283-abd2c4811726",
            "attributes": {"Description": ""},
            "quad": [
                [1619.050048828125, 1556.68994140625],
                [1714.2900390625, 1556.68994140625],
                [1714.2900390625, 1860.260009765625],
                [1619.050048828125, 1860.260009765625],
            ],
            "polygon": [
                [1619.048, 1556.69],
                [1714.286, 1556.69],
                [1714.286, 1860.262],
                [1619.048, 1860.262],
                [1619.048, 1556.69],
            ],
        },
    },
    {
        "class": "SegmentEntity",
        "dump": {
            "id": "edge-3_line",
            "attributes": {"line_attributes": {"kind": "piping"}},
            "geometry": [[452.381, 1833.3333], [889.881, 1833.3333]],
        },
    },
]

# Image pixels, y down: the corners of a 10 x 10 box.
SQUARE = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
SIZE_DICT = {
    "image_width": 5000,
    "image_height": 3000,
    "drawing_width": 420.0,
    "drawing_height": 297.0,
}


# --- helpers -----------------------------------------------------------------


def _size() -> DrawingSize:
    return DrawingSize.model_validate(SIZE_DICT)


def _symbol(entity_id: str, symbol_class: str = "nozzle") -> SymbolEntity:
    return SymbolEntity(id=entity_id, symbol_class=symbol_class, quad=SQUARE)


def _equipment(entity_id: str) -> EquipmentEntity:
    return EquipmentEntity(id=entity_id, polygon=SQUARE)


def _segment(
    entity_id: str,
    kind: str = "piping",
    points: list[tuple[float, float]] | None = None,
) -> SegmentEntity:
    return SegmentEntity(
        id=entity_id,
        attributes={"line_attributes": {"kind": kind}},
        geometry=points if points is not None else [(0.0, 0.0), (50.0, 0.0)],
    )


def _valid_extraction() -> tuple[nx.Graph, list[Entity], DrawingSize]:
    """A small valid Dex extraction, built fresh for each call.

    Equipment ``eq`` with nozzles ``n1`` and ``n2`` (attachment edges without
    ``id``), a valve ``v1`` with actuator ``a1`` (attachment), a junction ``j1``
    and a deadend ``d1`` on a piping run, and an instrument ``pif1`` whose
    signal line reaches the actuator.
    """
    graph = nx.Graph()
    graph.add_node("eq", node_type="object")
    graph.add_node("n1", node_type="object")
    graph.add_node("n2", node_type="object")
    graph.add_node("v1", node_type="object")
    graph.add_node("a1", node_type="object")
    graph.add_node("pif1", node_type="object")
    graph.add_node("j1", node_type="junction", geometry=Point(25.0, 0.0))
    graph.add_node("d1", node_type="deadend", geometry=Point(60.0, 0.0))
    graph.add_edge("eq", "n1")
    graph.add_edge("eq", "n2")
    graph.add_edge("a1", "v1")
    graph.add_edge("n1", "j1", id="edge-piping-1")
    graph.add_edge("j1", "n2", id="edge-piping-2")
    graph.add_edge("v1", "d1", id="edge-piping-3")
    graph.add_edge("pif1", "a1", id="edge-signal-1")
    entities: list[Entity] = [
        _equipment("eq"),
        _symbol("n1", "nozzle"),
        _symbol("n2", "nozzle"),
        _symbol("v1", "valve"),
        _symbol("a1", "actuator"),
        _symbol("pif1", "instrument"),
        _segment("edge-piping-1", "piping", [(0.0, 0.0), (25.0, 0.0)]),
        _segment("edge-piping-2", "piping", [(25.0, 0.0), (50.0, 0.0)]),
        _segment("edge-piping-3", "piping", [(50.0, 0.0), (60.0, 0.0)]),
        _segment("edge-signal-1", "signal-line", [(100.0, 100.0), (200.0, 100.0)]),
    ]
    return graph, entities, _size()


def _as_digraph(graph: nx.Graph) -> nx.DiGraph:
    """A DiGraph with one arc per undirected edge (networkx lists each edge once)."""
    directed = nx.DiGraph()
    directed.add_nodes_from(graph.nodes(data=True))
    directed.add_edges_from(graph.edges(data=True))
    return directed


def _problems(graph: object, entities: list[Entity], size: object) -> list[str]:
    """Run check_extraction on bad input and return the problems it lists."""
    with pytest.raises(DexExtractionError) as info:
        check_extraction(graph, entities, size)
    return info.value.problems


def _assert_listed(problems: list[str], *fragments: str) -> None:
    """Assert that one problem line contains every fragment."""
    assert any(
        all(fragment in problem for fragment in fragments) for problem in problems
    ), problems


# --- 1. Entity models --------------------------------------------------------


@pytest.mark.parametrize(
    ("entity", "label"),
    [
        (_symbol("n1", "nozzle"), "nozzle"),
        (_symbol("x", "foo-widget"), "foo-widget"),
        (_equipment("eq"), "equipment"),
        (_segment("edge-1"), "segment"),
    ],
    ids=["symbol-nozzle", "symbol-unknown", "equipment", "segment"],
)
def test_label_is_the_coarse_label_of_each_class(entity, label):
    assert entity.label == label


def test_entity_base_class_is_abstract():
    with pytest.raises(TypeError):
        Entity(id="x")  # type: ignore[abstract]


def test_default_id_is_a_fresh_uuid4_string_and_is_frozen():
    entity = SymbolEntity(symbol_class="nozzle", quad=SQUARE)
    other = SymbolEntity(symbol_class="nozzle", quad=SQUARE)
    assert str(uuid.UUID(entity.id)) == entity.id
    assert uuid.UUID(entity.id).version == 4
    assert entity.id != other.id
    with pytest.raises(ValidationError):
        entity.id = "x"


def test_attributes_default_to_an_empty_dict_and_are_carried_as_given():
    assert _symbol("n1").attributes == {}
    attributes = {"Description": "", "nested": {"values": [1, 2]}}
    entity = SymbolEntity(
        id="n1", symbol_class="nozzle", quad=SQUARE, attributes=attributes
    )
    assert entity.attributes == attributes


def test_extra_fields_are_ignored_and_dropped():
    entity = SymbolEntity(
        id="nozzle-0", symbol_class="nozzle", quad=SQUARE, anchor=[1, 2]
    )
    assert "anchor" not in entity.model_dump()


def test_symbol_class_is_required_and_confidence_defaults_to_one():
    with pytest.raises(ValidationError):
        SymbolEntity(id="n1", quad=SQUARE)
    assert _symbol("n1").confidence == 1.0


@pytest.mark.parametrize(
    "quad",
    [
        [[0, 0], [1, 0], [1, 1], [0, 1]],
        ((0, 0), (1, 0), (1, 1), (0, 1)),
        np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=np.float32),
        [np.array([0, 0]), np.array([1, 0]), np.array([1, 1]), np.array([0, 1])],
    ],
    ids=["list", "tuple", "numpy", "numpy-rows"],
)
def test_quad_accepts_lists_tuples_or_numpy_arrays(quad):
    entity = SymbolEntity(symbol_class="nozzle", quad=quad)
    assert isinstance(entity.quad, tuple)
    assert all(isinstance(point, tuple) for point in entity.quad)
    assert entity.quad == ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
    assert entity.model_dump()["quad"] == [
        [0.0, 0.0],
        [1.0, 0.0],
        [1.0, 1.0],
        [0.0, 1.0],
    ]


@pytest.mark.parametrize(
    "quad",
    [
        None,
        "abc",
        [[0, 0], [1, 0], [1, 1]],
        [[0, 0], [1, 0], [1, 1], [0, 1], [2, 2]],
        [[0, 0], [1, 0], [1, 1], [0, 1, 9]],
        [[0, 0], [1, 0], [1, math.nan], [0, 1]],
        [[0, 0], [1, 0], [1, math.inf], [0, 1]],
        [[10**400, 0], [1, 0], [1, 1], [0, 1]],
    ],
    ids=["none", "string", "three-points", "five-points", "point-not-a-pair", "nan", "inf", "overflow"],
)
def test_quad_rejects_missing_wrong_count_non_pairs_and_non_finite_values(quad):
    with pytest.raises(ValidationError):
        SymbolEntity(symbol_class="nozzle", quad=quad)


@pytest.mark.parametrize(
    "polygon",
    [SQUARE, [*SQUARE, SQUARE[0]], Polygon(SQUARE)],
    ids=["open-ring", "closed-ring", "shapely-polygon"],
)
def test_polygon_accepts_open_closed_or_shapely_rings_and_dumps_them_closed(polygon):
    entity = EquipmentEntity(id="eq", polygon=polygon)
    assert entity.model_dump()["polygon"] == [
        [0.0, 0.0],
        [10.0, 0.0],
        [10.0, 10.0],
        [0.0, 10.0],
        [0.0, 0.0],
    ]


@pytest.mark.parametrize(
    "polygon",
    [
        None,
        [],
        [(0.0, 0.0)],
        [(0.0, 0.0), (1.0, 0.0)],
        [(0.0, 0.0), (math.nan, 0.0), (1.0, 1.0)],
        [(0.0, 0.0), (math.inf, 0.0), (1.0, 1.0)],
    ],
    ids=["none", "empty", "one-point", "two-points", "nan", "inf"],
)
def test_polygon_rejects_missing_empty_short_or_non_finite_rings(polygon):
    with pytest.raises(ValidationError):
        EquipmentEntity(id="eq", polygon=polygon)


def test_polygon_self_intersection_is_accepted_not_checked():
    bow_tie = [(0.0, 0.0), (10.0, 10.0), (10.0, 0.0), (0.0, 10.0)]
    entity = EquipmentEntity(id="eq", polygon=bow_tie)
    assert not entity.polygon.is_valid


@pytest.mark.parametrize(
    "geometry",
    [
        [(0.0, 0.0), (5.0, 5.0), (9.0, 1.0)],
        LineString([(0.0, 0.0), (5.0, 5.0), (9.0, 1.0)]),
    ],
    ids=["points", "linestring"],
)
def test_segment_geometry_accepts_points_or_a_linestring(geometry):
    entity = SegmentEntity(id="edge-1", attributes={}, geometry=geometry)
    assert entity.model_dump()["geometry"] == [[0.0, 0.0], [5.0, 5.0], [9.0, 1.0]]


@pytest.mark.parametrize(
    "geometry",
    [
        None,
        [],
        [(0.0, 0.0)],
        [(0.0, 0.0), (math.nan, 1.0)],
        [(0.0, 0.0), (1.0, math.inf)],
    ],
    ids=["none", "empty", "one-point", "nan", "inf"],
)
def test_segment_geometry_rejects_missing_short_or_non_finite_lines(geometry):
    with pytest.raises(ValidationError):
        SegmentEntity(id="edge-1", attributes={}, geometry=geometry)


# --- 2. SegmentEntity.kind ---------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("piping", LineKind.PIPING),
        ("signal-line", LineKind.SIGNAL_LINE),
        ("data-line", LineKind.DATA_LINE),
    ],
)
def test_kind_reads_each_line_kind(raw, expected):
    assert _segment("edge-1", kind=raw).kind is expected


@pytest.mark.parametrize(
    "attributes",
    [
        {},
        {"line_attributes": {}},
        {"line_attributes": {"kind": "pipe"}},
        {"line_attributes": {"kind": ""}},
        {"line_attributes": {"kind": "Piping"}},
    ],
    ids=["no-line-attributes", "no-kind-key", "unknown", "empty", "wrong-case"],
)
def test_kind_raises_value_error_when_missing_or_not_a_line_kind(attributes):
    entity = SegmentEntity(
        id="edge-1", attributes=attributes, geometry=[(0.0, 0.0), (1.0, 1.0)]
    )
    with pytest.raises(ValueError):
        _ = entity.kind


# --- 3. DrawingSize ----------------------------------------------------------


def test_drawing_size_accepts_size_json_with_an_extra_units_key():
    size = DrawingSize.model_validate({**SIZE_DICT, "units": "mm"})
    assert (size.image_width, size.image_height) == (5000, 3000)
    assert (size.drawing_width, size.drawing_height) == (420.0, 297.0)


@pytest.mark.parametrize(
    ("field", "bad"),
    [
        ("image_width", 0),
        ("image_height", -1),
        ("drawing_width", 0),
        ("drawing_height", -5.5),
    ],
)
def test_drawing_size_rejects_zero_or_negative_dimensions(field, bad):
    with pytest.raises(ValidationError):
        DrawingSize.model_validate({**SIZE_DICT, field: bad})


def test_drawing_size_is_frozen():
    with pytest.raises(ValidationError):
        _size().image_width = 1


# --- 4. Pipeline compatibility -----------------------------------------------


def test_pipeline_dump_keeps_ids_classes_confidence_attributes_and_geometry():
    symbol_dump, equipment_dump, segment_dump = (
        item["dump"] for item in PIPELINE_DUMP
    )

    symbol = SymbolEntity.model_validate(symbol_dump)
    assert symbol.id == "nozzle-0"
    assert symbol.symbol_class == "nozzle"
    assert symbol.label == "nozzle"
    assert symbol.confidence == pytest.approx(0.97)
    assert symbol.attributes == {}
    assert symbol.quad[0] == pytest.approx((1571.4300537109375, 1821.5699462890625))

    equipment = EquipmentEntity.model_validate(equipment_dump)
    assert equipment.id == "529f6fe5-8667-5f52-8283-abd2c4811726"
    assert equipment.label == "equipment"
    assert equipment.attributes == {"Description": ""}
    assert equipment.model_dump()["polygon"][0] == [1619.048, 1556.69]

    segment = SegmentEntity.model_validate(segment_dump)
    assert segment.id == "edge-3_line"
    assert segment.kind is LineKind.PIPING
    assert segment.model_dump()["geometry"] == [
        [452.381, 1833.3333],
        [889.881, 1833.3333],
    ]


def _foreign_classes() -> tuple[type[BaseModel], type[BaseModel], type[BaseModel]]:
    """Pydantic classes named like ours, standing in for the pipeline's objects.

    They are local to this function, so they are not our classes; each carries
    the extra fields of the pipeline's dump (``anchor``, ``quad`` on equipment).
    """

    class SymbolEntity(BaseModel):
        id: str
        attributes: dict = {}
        quad: list
        symbol_class: str
        confidence: float = 0.97
        anchor: list

    class EquipmentEntity(BaseModel):
        id: str
        attributes: dict = {}
        quad: list
        polygon: list

    class SegmentEntity(BaseModel):
        id: str
        attributes: dict = {}
        geometry: list

    return SymbolEntity, EquipmentEntity, SegmentEntity


def test_foreign_objects_are_normalised_to_our_classes():
    foreign_symbol, foreign_equipment, foreign_segment = _foreign_classes()
    graph = nx.Graph()
    graph.add_node("eq", node_type="object")
    graph.add_node("n1", node_type="object")
    graph.add_node("n2", node_type="object")
    graph.add_edge("eq", "n1")
    graph.add_edge("n1", "n2", id="edge-3_line")
    entities = [
        foreign_equipment(
            id="eq",
            attributes={"Description": ""},
            quad=SQUARE,
            polygon=[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]],
        ),
        foreign_symbol(id="n1", quad=SQUARE, symbol_class="nozzle", anchor=[5, 5]),
        foreign_symbol(id="n2", quad=SQUARE, symbol_class="nozzle", anchor=[5, 5]),
        foreign_segment(
            id="edge-3_line",
            attributes={"line_attributes": {"kind": "piping"}},
            geometry=[[452.381, 1833.3333], [889.881, 1833.3333]],
        ),
    ]

    extraction = check_extraction(graph, entities, _size())

    assert isinstance(extraction.entities["eq"], EquipmentEntity)
    assert isinstance(extraction.entities["n1"], SymbolEntity)
    assert isinstance(extraction.entities["n2"], SymbolEntity)
    assert isinstance(extraction.entities["edge-3_line"], SegmentEntity)
    assert extraction.entities["n1"].symbol_class == "nozzle"
    assert extraction.segment("n1", "n2").kind is LineKind.PIPING
    for entity in extraction.entities.values():
        assert not isinstance(
            entity, (foreign_symbol, foreign_equipment, foreign_segment)
        )


# --- 5. check_extraction on a valid extraction -------------------------------


def test_valid_extraction_returns_a_frozen_dex_extraction():
    graph, entities, size = _valid_extraction()
    extraction = check_extraction(graph, entities, size)
    assert isinstance(extraction, DexExtraction)
    assert extraction.size == size
    assert list(extraction.entities) == [entity.id for entity in entities]
    with pytest.raises(dataclasses.FrozenInstanceError):
        extraction.size = size


def test_node_type_and_point_are_read_from_the_dex_graph():
    graph, entities, size = _valid_extraction()
    extraction = check_extraction(graph, entities, size)
    assert extraction.node_type("eq") is NodeType.OBJECT
    assert extraction.node_type("j1") is NodeType.JUNCTION
    assert extraction.node_type("d1") is NodeType.DEADEND
    assert extraction.point("j1").equals(Point(25.0, 0.0))
    assert extraction.point("d1").equals(Point(60.0, 0.0))


def test_segment_is_the_line_entity_of_an_edge_and_none_for_attachments():
    graph, entities, size = _valid_extraction()
    extraction = check_extraction(graph, entities, size)
    line = extraction.segment("n1", "j1")
    assert isinstance(line, SegmentEntity)
    assert line.id == "edge-piping-1"
    assert line.kind is LineKind.PIPING
    assert extraction.segment("pif1", "a1").kind is LineKind.SIGNAL_LINE
    assert extraction.segment("eq", "n1") is None
    assert extraction.segment("a1", "v1") is None


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        ({"direction": "forward"}, Direction.FORWARD),
        ({"direction": "reverse"}, Direction.REVERSE),
        ({"direction": "bidirectional"}, Direction.BIDIRECTIONAL),
        ({"dualflow": True}, Direction.BIDIRECTIONAL),
        ({"dualflow": False}, None),
        ({}, None),
    ],
    ids=[
        "forward",
        "reverse",
        "bidirectional",
        "dualflow-true",
        "dualflow-false",
        "missing",
    ],
)
def test_direction_is_read_from_the_edge_and_none_when_unknown(change, expected):
    graph, entities, size = _valid_extraction()
    graph.edges["n1", "j1"].update(change)
    extraction = check_extraction(graph, entities, size)
    assert extraction.direction("n1", "j1") is expected


def test_direction_is_none_for_an_attachment_even_when_set():
    graph, entities, size = _valid_extraction()
    graph.edges["eq", "n1"]["direction"] = "forward"
    extraction = check_extraction(graph, entities, size)
    assert extraction.direction("eq", "n1") is None


def test_check_extraction_never_mutates_the_callers_graph():
    graph, entities, size = _valid_extraction()
    graph.edges["n1", "j1"]["dualflow"] = True
    before_nodes = {node: dict(data) for node, data in graph.nodes(data=True)}
    before_edges = {(u, v): dict(data) for u, v, data in graph.edges(data=True)}

    extraction = check_extraction(graph, entities, size)

    assert extraction.graph is not graph
    assert {node: dict(data) for node, data in graph.nodes(data=True)} == before_nodes
    assert {
        (u, v): dict(data) for u, v, data in graph.edges(data=True)
    } == before_edges


def test_entity_missing_from_the_graph_becomes_an_isolated_object_node():
    graph, entities, size = _valid_extraction()
    entities.append(_symbol("insulation", "insulation"))
    extraction = check_extraction(graph, entities, size)
    assert extraction.node_type("insulation") is NodeType.OBJECT
    assert extraction.graph.degree("insulation") == 0
    assert not graph.has_node("insulation")


def test_unknown_label_passes_and_is_carried_as_the_entity_label():
    graph, entities, size = _valid_extraction()
    entities = [
        _symbol("pif1", "foo-widget") if entity.id == "pif1" else entity
        for entity in entities
    ]
    extraction = check_extraction(graph, entities, size)
    assert extraction.entities["pif1"].label == "foo-widget"


@pytest.mark.parametrize("arc", [("n1", "j1"), ("j1", "n1")], ids=["as-listed", "reversed"])
def test_digraph_is_accepted_its_arc_order_is_ignored_and_the_result_is_undirected(arc):
    graph, entities, size = _valid_extraction()
    graph.edges["n1", "j1"]["direction"] = "reverse"
    directed = nx.DiGraph()
    directed.add_nodes_from(graph.nodes(data=True))
    directed.add_edges_from(
        (*arc, data) if {u, v} == {"n1", "j1"} else (u, v, data)
        for u, v, data in graph.edges(data=True)
    )

    extraction = check_extraction(directed, entities, size)

    assert isinstance(extraction.graph, nx.Graph)
    assert not extraction.graph.is_directed()
    assert extraction.segment("n1", "j1").id == "edge-piping-1"
    assert extraction.direction("n1", "j1") is Direction.REVERSE


# --- 6. Problems: every item of the spec, and one combined error -------------


def test_problem_1_duplicate_entity_id():
    graph, entities, size = _valid_extraction()
    entities.append(_symbol("n1", "nozzle"))
    _assert_listed(_problems(graph, entities, size), "duplicate Entity id 'n1'")


@pytest.mark.parametrize(
    ("edge_id", "fragment"),
    [
        ("edge-piping-1", "duplicate edge id 'edge-piping-1'"),
        ("n1", "id 'n1' names both a node and an edge"),
    ],
    ids=["duplicate-edge-id", "node-and-edge-id"],
)
def test_problem_2_duplicate_edge_id_or_an_id_shared_with_a_node(edge_id, fragment):
    graph, entities, size = _valid_extraction()
    graph.add_edge("v1", "n2", id=edge_id)
    _assert_listed(_problems(graph, entities, size), fragment)


@pytest.mark.parametrize("node_type", [None, "pump"], ids=["missing", "unknown"])
def test_problem_3_node_with_missing_or_unknown_node_type(node_type):
    graph, entities, size = _valid_extraction()
    if node_type is None:
        del graph.nodes["n1"]["node_type"]
    else:
        graph.nodes["n1"]["node_type"] = node_type
    _assert_listed(_problems(graph, entities, size), "node 'n1' has unknown node_type")


def test_problem_4_object_node_without_an_entity():
    graph, entities, size = _valid_extraction()
    entities = [entity for entity in entities if entity.id != "n2"]
    _assert_listed(_problems(graph, entities, size), "object node 'n2' has no Entity")


@pytest.mark.parametrize("label", ["", "   "], ids=["empty", "blank"])
def test_problem_5_object_node_whose_entity_has_a_blank_label(label):
    graph, entities, size = _valid_extraction()
    entities = [
        _symbol("n1", label) if entity.id == "n1" else entity for entity in entities
    ]
    _assert_listed(_problems(graph, entities, size), "object node 'n1' has no label")


@pytest.mark.parametrize(
    ("node", "change", "fragment"),
    [
        ("j1", "entity", "junction node 'j1' has an Entity"),
        ("d1", "entity", "deadend node 'd1' has an Entity"),
        ("j1", "no-geometry", "junction node 'j1' has no point geometry"),
        ("j1", "line-geometry", "junction node 'j1' has no point geometry"),
        ("j1", "empty-point", "junction node 'j1' has no point geometry"),
        ("d1", "no-geometry", "deadend node 'd1' has no point geometry"),
    ],
    ids=[
        "junction-with-entity",
        "deadend-with-entity",
        "junction-no-point",
        "junction-line-geometry",
        "junction-empty-point",
        "deadend-no-point",
    ],
)
def test_problem_6_junction_or_deadend_with_an_entity_or_without_a_point(
    node, change, fragment
):
    graph, entities, size = _valid_extraction()
    if change == "entity":
        entities.append(_symbol(node, "nozzle"))
    elif change == "no-geometry":
        del graph.nodes[node]["geometry"]
    elif change == "empty-point":
        graph.nodes[node]["geometry"] = Point()
    else:
        graph.nodes[node]["geometry"] = LineString([(0.0, 0.0), (1.0, 1.0)])
    _assert_listed(_problems(graph, entities, size), fragment)


def test_problem_6_a_blank_label_entity_on_a_junction_is_reported_once():
    graph, entities, size = _valid_extraction()
    entities.append(_symbol("j1", " "))
    assert _problems(graph, entities, size) == ["junction node 'j1' has an Entity"]


def test_problem_7_segment_entity_without_an_edge():
    graph, entities, size = _valid_extraction()
    entities.append(_segment("edge-orphan"))
    _assert_listed(
        _problems(graph, entities, size),
        "SegmentEntity 'edge-orphan' has no edge in the Dex graph",
    )


@pytest.mark.parametrize(
    ("attributes", "fragment"),
    [
        ({}, "SegmentEntity 'edge-piping-1' has no line kind"),
        (
            {"line_attributes": {"kind": "steam"}},
            "SegmentEntity 'edge-piping-1' has unknown line kind 'steam'",
        ),
    ],
    ids=["missing", "unknown"],
)
def test_problem_8_segment_with_missing_or_unknown_line_kind(attributes, fragment):
    graph, entities, size = _valid_extraction()
    entities = [
        SegmentEntity(
            id="edge-piping-1",
            attributes=attributes,
            geometry=[(0.0, 0.0), (25.0, 0.0)],
        )
        if entity.id == "edge-piping-1"
        else entity
        for entity in entities
    ]
    _assert_listed(_problems(graph, entities, size), fragment)


@pytest.mark.parametrize(
    ("u", "v", "edge_id", "prefix"),
    [
        ("n1", "n2", "edge-stray", "edge 'edge-stray' between"),
        ("eq", "v1", None, "edge between"),
    ],
    ids=["with-id", "without-id"],
)
def test_problem_9_edge_without_a_segment_that_is_not_an_attachment(
    u, v, edge_id, prefix
):
    graph, entities, size = _valid_extraction()
    graph.add_edge(u, v, **({} if edge_id is None else {"id": edge_id}))
    _assert_listed(
        _problems(graph, entities, size),
        prefix,
        "has no SegmentEntity and is not an attachment",
        f"'{u}'",
        f"'{v}'",
    )


@pytest.mark.parametrize(
    ("change", "fragment"),
    [
        (
            {"direction": "sideways"},
            "edge 'edge-piping-1' has unknown direction 'sideways'",
        ),
        (
            {"direction": "forward", "dualflow": True},
            "edge 'edge-piping-1' has direction 'forward' but dualflow true",
        ),
        (
            {"direction": "reverse", "dualflow": True},
            "edge 'edge-piping-1' has direction 'reverse' but dualflow true",
        ),
        ({"dualflow": "yes"}, "edge 'edge-piping-1' has unknown dualflow value"),
        ({"dualflow": 1}, "edge 'edge-piping-1' has unknown dualflow value"),
    ],
    ids=[
        "unknown-direction",
        "forward-with-dualflow",
        "reverse-with-dualflow",
        "dualflow-yes",
        "dualflow-int",
    ],
)
def test_problem_10_unknown_direction_or_bad_dualflow(change, fragment):
    graph, entities, size = _valid_extraction()
    graph.edges["n1", "j1"].update(change)
    _assert_listed(_problems(graph, entities, size), fragment)


@pytest.mark.parametrize(
    ("make_entity", "fragment"),
    [
        (
            lambda: _symbol("edge-att-1", "nozzle"),
            "SymbolEntity 'edge-att-1' has the id of an edge",
        ),
        (
            lambda: _equipment("edge-att-1"),
            "EquipmentEntity 'edge-att-1' has the id of an edge",
        ),
    ],
    ids=["symbol", "equipment"],
)
def test_problem_11_symbol_or_equipment_entity_with_an_edge_id(make_entity, fragment):
    # The attachment edge eq-n1 gets an id that no SegmentEntity uses, so the
    # only problem is that the Entity id is an edge id (no duplicate id).
    graph, entities, size = _valid_extraction()
    graph.edges["eq", "n1"]["id"] = "edge-att-1"
    entities.append(make_entity())
    _assert_listed(_problems(graph, entities, size), fragment)


def test_problem_12_foreign_object_that_fails_our_model():
    graph, entities, size = _valid_extraction()
    _, foreign_equipment, _ = _foreign_classes()
    entities.append(
        foreign_equipment(
            id="eq-broken",
            attributes={},
            quad=SQUARE,
            polygon=[[0, 0], [1, 1]],
        )
    )
    _assert_listed(
        _problems(graph, entities, size), "Entity #", "EquipmentEntity 'eq-broken'"
    )


def test_problem_12_a_rejected_foreign_entity_causes_no_follow_on_problems():
    # n1 and edge-piping-1 fail to convert; their node and edges are not
    # reported again as "has no Entity" or "is not an attachment".
    foreign_symbol, _, foreign_segment = _foreign_classes()
    graph, entities, size = _valid_extraction()
    entities = [entity for entity in entities if entity.id not in ("n1", "edge-piping-1")]
    entities += [
        foreign_symbol(id="n1", quad=SQUARE[:3], symbol_class="nozzle", anchor=[0, 0]),
        foreign_segment(
            id="edge-piping-1",
            attributes={"line_attributes": {"kind": "piping"}},
            geometry=[[0, 0]],
        ),
    ]
    problems = _problems(graph, entities, size)
    assert len(problems) == 2, problems
    _assert_listed(problems, "Entity #", "SymbolEntity 'n1'")
    _assert_listed(problems, "Entity #", "SegmentEntity 'edge-piping-1'")


def test_problem_12_foreign_object_of_an_unsupported_class():
    class Gizmo(BaseModel):
        id: str = "gizmo-1"

    graph, entities, size = _valid_extraction()
    entities.append(Gizmo())
    _assert_listed(
        _problems(graph, entities, size), "Entity #", "unsupported type Gizmo"
    )


def test_problem_12_invalid_drawing_size():
    graph, entities, _ = _valid_extraction()
    bad_size = {**SIZE_DICT, "drawing_width": 0}
    _assert_listed(_problems(graph, entities, bad_size), "invalid DrawingSize")


def _both_ways_digraph() -> nx.DiGraph:
    """The valid fixture as a DiGraph, with an arc added in each direction."""
    graph, _, _ = _valid_extraction()
    directed = _as_digraph(graph)
    u, v = ("n1", "j1") if directed.has_edge("n1", "j1") else ("j1", "n1")
    directed.add_edge(v, u, id="edge-back")
    return directed


@pytest.mark.parametrize(
    ("graph_factory", "fragments"),
    [
        (lambda: None, ("the Dex graph must be a networkx Graph, got",)),
        (lambda: {"not": "a graph"}, ("the Dex graph must be a networkx Graph, got",)),
        (
            lambda: nx.MultiGraph(_valid_extraction()[0]),
            ("parallel edges are not supported (got a MultiGraph)",),
        ),
        (
            lambda: nx.MultiDiGraph(_valid_extraction()[0]),
            ("parallel edges are not supported",),
        ),
        (
            _both_ways_digraph,
            ("parallel edges are not supported", "linked both ways", "'n1'", "'j1'"),
        ),
    ],
    ids=["none", "dict", "multigraph", "multidigraph", "both-ways-digraph"],
)
def test_problem_13_graph_type_is_checked(graph_factory, fragments):
    _, entities, size = _valid_extraction()
    _assert_listed(_problems(graph_factory(), entities, size), *fragments)


def test_all_independent_problems_are_listed_in_one_error():
    graph, entities, size = _valid_extraction()
    entities.append(_symbol("n1", "nozzle"))  # 1: duplicate Entity id
    graph.nodes["n2"]["node_type"] = "pump"  # 3: unknown node_type
    entities.append(_segment("edge-orphan"))  # 7: SegmentEntity without an edge
    graph.add_edge("n1", "n2", id="edge-stray")  # 9: neither segment nor attachment
    graph.edges["n1", "j1"]["direction"] = "sideways"  # 10: unknown direction

    with pytest.raises(DexExtractionError) as info:
        check_extraction(graph, entities, size)

    error = info.value
    assert isinstance(error, ValueError)
    assert len(error.problems) >= 5
    for problem in error.problems:
        assert f"- {problem}" in str(error)
    expected = [
        ("duplicate Entity id 'n1'",),
        ("node 'n2' has unknown node_type",),
        ("SegmentEntity 'edge-orphan' has no edge in the Dex graph",),
        ("edge 'edge-stray' between", "has no SegmentEntity and is not an attachment"),
        ("edge 'edge-piping-1' has unknown direction 'sideways'",),
    ]
    for fragments in expected:
        _assert_listed(error.problems, *fragments)
        assert all(fragment in str(error) for fragment in fragments)


def test_problem_node_with_a_non_string_id():
    graph, entities, size = _valid_extraction()
    graph.add_node(7, node_type="junction", geometry=Point(5.0, 5.0))
    _assert_listed(_problems(graph, entities, size), "node 7 has a non-string id")


def test_problem_entity_of_a_class_outside_the_contract():
    class Gadget(Entity):
        @property
        def label(self) -> str:
            return "instrument"

    graph, entities, size = _valid_extraction()
    entities.append(Gadget(id="gadget-1"))
    _assert_listed(_problems(graph, entities, size), "Entity #", "unsupported type Gadget")
