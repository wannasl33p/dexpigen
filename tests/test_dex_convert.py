"""Black-box tests for the Dex-to-DEXPI converter (``dexpigen.entities``).

Written from the converter spec alone: ``dex_to_model`` returns a
``DexConversion`` (the ``ConceptualModel`` and its report), ``dex_to_proteus``
serialises that model, and both raise ``DexExtractionError`` on a contract
violation. Every test builds a small hand-made Dex extraction in image pixels,
on a 1000 x 1000 px image of a 100 x 100 mm drawing, so px -> mm is ``x / 10``
and ``y = 100 - y / 10``. The converted objects are found by ``dex_id`` and read
through their public fields.
"""

import re
import shutil
import sys
from collections import Counter
from pathlib import Path

import networkx as nx
import pytest
from shapely.geometry import Point

from dexpigen import to_proteus_xml
from dexpigen.base import DexpiBaseModel
from dexpigen.entities import (
    DexConversion,
    DexExtractionError,
    DrawingSize,
    Entity,
    EquipmentEntity,
    SegmentEntity,
    SymbolEntity,
    dex_to_model,
    dex_to_proteus,
)
from dexpigen.equipment import CustomEquipment, Nozzle
from dexpigen.instrumentation import (
    ActuatingSystem,
    ControlledActuator,
    ProcessInstrumentationFunction,
)
from dexpigen.model import ConceptualModel
from dexpigen.piping import (
    Flange,
    FlowInPipeOffPageConnector,
    FlowOutPipeOffPageConnector,
    OperatedValve,
    Pipe,
    PipeReducer,
    PipeTee,
    PipingNetworkSegmentItem,
)

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
NCNAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]*$")
SIZE = DrawingSize(image_width=1000, image_height=1000, drawing_width=100.0, drawing_height=100.0)

type Plant = tuple[nx.Graph, list[Entity], DrawingSize]


# --- helpers -----------------------------------------------------------------


def _rect(x0: float, y0: float, x1: float, y1: float) -> list[tuple[float, float]]:
    """The corners of an axis-aligned box in px: top-left, top-right, bottom-right, bottom-left."""
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _box(cx: float, cy: float) -> list[tuple[float, float]]:
    """The corners of a 20 x 20 px symbol box centred on ``(cx, cy)``."""
    return _rect(cx - 10.0, cy - 10.0, cx + 10.0, cy + 10.0)


def _symbol(entity_id: str, symbol_class: str, cx: float, cy: float) -> SymbolEntity:
    return SymbolEntity(id=entity_id, symbol_class=symbol_class, quad=_box(cx, cy))


def _segment(
    entity_id: str, points: list[tuple[float, float]], kind: str = "piping"
) -> SegmentEntity:
    return SegmentEntity(
        id=entity_id, attributes={"line_attributes": {"kind": kind}}, geometry=points
    )


def _mm(x_px: float, y_px: float) -> tuple[float, float]:
    """The px -> mm map of ``SIZE``: ``x / 10`` and ``100 - y / 10``."""
    return (x_px / 10.0, 100.0 - y_px / 10.0)


def _flat(points) -> list[float]:
    """The coordinates of ``points`` as one flat list of floats, for ``pytest.approx``."""
    return [float(value) for point in points for value in point]


def _open_ring(points) -> list[tuple[float, float]]:
    """``points`` without the closing point that a shapely exterior ring repeats."""
    ring = [tuple(point) for point in points]
    return ring[:-1] if len(ring) > 1 and ring[0] == ring[-1] else ring


def _closed(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """``points`` followed by their first point again."""
    return [*points, points[0]]


def _add_run(
    graph: nx.Graph,
    entities: list[Entity],
    prefix: str,
    y: float,
    item_label: str = "valve",
    direction: str | None = "forward",
) -> None:
    """Add one in-line run at height ``y`` px, with nozzles on one equipment.

    The run is ``<prefix>-n1`` -> ``<prefix>-item`` -> ``<prefix>-n2`` at x = 100,
    500 and 900 px, joined by the piping lines ``<prefix>-line-1`` and
    ``<prefix>-line-2``. The lines start and end on the symbol borders.
    """
    equipment, n1, item, n2 = (f"{prefix}-{name}" for name in ("eq", "n1", "item", "n2"))
    line_1, line_2 = f"{prefix}-line-1", f"{prefix}-line-2"
    attributes = {} if direction is None else {"direction": direction}
    for node in (equipment, n1, item, n2):
        graph.add_node(node, node_type="object")
    graph.add_edge(equipment, n1)
    graph.add_edge(equipment, n2)
    graph.add_edge(n1, item, id=line_1, **attributes)
    graph.add_edge(item, n2, id=line_2, **attributes)
    entities.extend(
        [
            EquipmentEntity(id=equipment, polygon=_rect(0.0, y - 100.0, 1000.0, y + 100.0)),
            _symbol(n1, "nozzle", 100.0, y),
            _symbol(item, item_label, 500.0, y),
            _symbol(n2, "nozzle", 900.0, y),
            _segment(line_1, [(110.0, y), (490.0, y)]),
            _segment(line_2, [(510.0, y), (890.0, y)]),
        ]
    )


def _plant(item_label: str = "valve", direction: str | None = "forward") -> Plant:
    """One in-line run ``a`` (see ``_add_run``) whose item carries ``item_label``."""
    graph = nx.Graph()
    entities: list[Entity] = []
    _add_run(graph, entities, "a", 500.0, item_label, direction)
    return graph, entities, SIZE


def _actuated_plant(kind: str = "signal-line") -> Plant:
    """The control-valve run, an actuator on that valve and an instrument signalling it.

    The actuator ``act`` sits at (500, 400) px, above the control valve ``a-item``.
    The instrument ``pif1`` at (500, 100) px sends the line ``sig-1``, of kind
    ``kind``, down to the actuator.
    """
    graph, entities, size = _plant(item_label="control-valve")
    graph.add_node("act", node_type="object")
    graph.add_node("pif1", node_type="object")
    graph.add_edge("act", "a-item")
    graph.add_edge("pif1", "act", id="sig-1")
    entities.extend(
        [
            _symbol("act", "actuator", 500.0, 400.0),
            _symbol("pif1", "instrument", 500.0, 100.0),
            _segment("sig-1", [(500.0, 110.0), (500.0, 390.0)], kind),
        ]
    )
    return graph, entities, size


def _tee_plant() -> Plant:
    """Three nozzles on one equipment, joined at the junction ``j`` (500, 500) px.

    The lines are ``t-1`` (n1 -> j), ``t-2`` (j -> n2) and ``t-3`` (n3 -> j), all forward.
    """
    graph = nx.Graph()
    for node in ("eq", "n1", "n2", "n3"):
        graph.add_node(node, node_type="object")
    graph.add_node("j", node_type="junction", geometry=Point(500.0, 500.0))
    for nozzle in ("n1", "n2", "n3"):
        graph.add_edge("eq", nozzle)
    graph.add_edge("n1", "j", id="t-1", direction="forward")
    graph.add_edge("j", "n2", id="t-2", direction="forward")
    graph.add_edge("n3", "j", id="t-3", direction="forward")
    entities: list[Entity] = [
        EquipmentEntity(id="eq", polygon=_rect(0.0, 0.0, 1000.0, 1000.0)),
        _symbol("n1", "nozzle", 100.0, 500.0),
        _symbol("n2", "nozzle", 900.0, 500.0),
        _symbol("n3", "nozzle", 500.0, 900.0),
        _segment("t-1", [(110.0, 500.0), (490.0, 500.0)]),
        _segment("t-2", [(510.0, 500.0), (890.0, 500.0)]),
        _segment("t-3", [(500.0, 890.0), (500.0, 510.0)]),
    ]
    return graph, entities, SIZE


def _objects(model: ConceptualModel) -> list[DexpiBaseModel]:
    """Every object reachable from ``model`` through its fields, each listed once."""
    found: dict[int, DexpiBaseModel] = {}
    pending: list[DexpiBaseModel] = [model]
    while pending:
        obj = pending.pop()
        if id(obj) in found:
            continue
        found[id(obj)] = obj
        for name in type(obj).model_fields:
            value = getattr(obj, name)
            children = value if isinstance(value, list) else [value]
            pending.extend(child for child in children if isinstance(child, DexpiBaseModel))
    return list(found.values())


def _by_dex_id(model: ConceptualModel) -> dict[str, DexpiBaseModel]:
    """The reachable objects of ``model`` by ``dex_id``; a repeated ``dex_id`` fails the test."""
    objects = _objects(model)
    ids = [obj.dex_id for obj in objects]
    assert len(set(ids)) == len(ids), sorted(ids)
    return {obj.dex_id: obj for obj in objects}


def _of_class(model: ConceptualModel, cls: type) -> list[DexpiBaseModel]:
    """The reachable objects of exactly class ``cls``; subclasses are not included."""
    return [obj for obj in _objects(model) if type(obj) is cls]


def _is_in(obj: object, items: list[object]) -> bool:
    """Whether ``obj`` is one of ``items``, by identity (pydantic ``==`` compares values)."""
    return any(item is obj for item in items)


def _validate(xml_path: Path) -> bool:
    """Validate ``xml_path`` with ``examples/validate_dexpi.py``, the project's xmllint wrapper."""
    if str(EXAMPLES) not in sys.path:
        sys.path.insert(0, str(EXAMPLES))  # for ``from validate_dexpi import validate``
    from validate_dexpi import validate

    return validate(str(xml_path))


# --- 1. API ------------------------------------------------------------------


def test_dex_to_model_returns_a_conversion_with_the_model_and_a_report():
    conversion = dex_to_model(*_plant())
    assert isinstance(conversion, DexConversion)
    assert isinstance(conversion.model, ConceptualModel)
    assert isinstance(conversion.report, list)
    assert all(isinstance(line, str) for line in conversion.report)


def test_clean_extraction_has_an_empty_report():
    # Every line has a direction, nothing is skipped and there is no instrument.
    assert dex_to_model(*_plant()).report == []


@pytest.mark.skipif(shutil.which("xmllint") is None, reason="xmllint is not on PATH")
def test_dex_to_proteus_returns_xml_that_validates_against_the_xsd(tmp_path):
    xml = dex_to_proteus(*_actuated_plant())
    assert isinstance(xml, str)
    path = tmp_path / "converted.xml"
    path.write_text(xml, encoding="utf-8")
    assert _validate(path)


def test_dex_to_proteus_is_the_serialisation_of_dex_to_model():
    graph, entities, size = _actuated_plant()
    expected = to_proteus_xml(dex_to_model(graph, entities, size).model)
    assert dex_to_proteus(graph, entities, size) == expected


@pytest.mark.parametrize("convert", [dex_to_model, dex_to_proteus], ids=["model", "proteus"])
def test_contract_violation_raises_dex_extraction_error(convert):
    graph, entities, size = _plant()
    del graph.nodes["a-n1"]["node_type"]
    with pytest.raises(DexExtractionError) as info:
        convert(graph, entities, size)
    assert isinstance(info.value, ValueError)
    assert any("node_type" in problem for problem in info.value.problems)


# --- 2. Label table ----------------------------------------------------------


def test_equipment_becomes_custom_equipment_labelled_equipment():
    graph = nx.Graph()
    graph.add_node("eq", node_type="object")
    entities = [EquipmentEntity(id="eq", polygon=_rect(0.0, 0.0, 100.0, 100.0))]
    (equipment,) = dex_to_model(graph, entities, SIZE).model.equipment
    assert type(equipment) is CustomEquipment
    assert equipment.source_type_label == "equipment"


def test_nozzle_is_composed_under_its_attached_equipment():
    graph, entities, size = _plant()
    (equipment,) = dex_to_model(graph, entities, size).model.equipment
    assert sorted(nozzle.dex_id for nozzle in equipment.nozzles) == ["Nozzle-a-n1", "Nozzle-a-n2"]
    assert all(type(nozzle) is Nozzle for nozzle in equipment.nozzles)


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("valve", OperatedValve),
        ("control-valve", OperatedValve),
        ("flange", Flange),
        ("reducer", PipeReducer),
    ],
    ids=["valve", "control-valve", "flange", "reducer"],
)
def test_in_line_items_become_their_classes(label, expected):
    graph, entities, size = _plant(item_label=label)
    model = dex_to_model(graph, entities, size).model
    assert [item.dex_id for item in _of_class(model, expected)] == [f"{expected.__name__}-a-item"]


@pytest.mark.parametrize(
    ("direction", "expected"),
    [("forward", FlowInPipeOffPageConnector), ("reverse", FlowOutPipeOffPageConnector)],
    ids=["line-flows-out", "line-flows-in"],
)
def test_off_page_connector_is_flow_in_or_out_by_the_direction_of_its_line(direction, expected):
    # Forward: the line starts at the connector, so it flows out of it.
    graph = nx.Graph()
    for node in ("eq", "opc", "n2"):
        graph.add_node(node, node_type="object")
    graph.add_edge("eq", "n2")
    graph.add_edge("opc", "n2", id="o-line", direction=direction)
    entities = [
        EquipmentEntity(id="eq", polygon=_rect(800.0, 400.0, 1000.0, 600.0)),
        _symbol("opc", "off-page-connector", 200.0, 500.0),
        _symbol("n2", "nozzle", 900.0, 500.0),
        _segment("o-line", [(210.0, 500.0), (890.0, 500.0)]),
    ]
    model = dex_to_model(graph, entities, SIZE).model
    assert [c.dex_id for c in _of_class(model, expected)] == [f"{expected.__name__}-opc"]


def test_instrument_becomes_a_top_level_process_instrumentation_function():
    graph = nx.Graph()
    graph.add_node("pif1", node_type="object")
    entities = [_symbol("pif1", "instrument", 500.0, 100.0)]
    model = dex_to_model(graph, entities, SIZE).model
    (pif,) = model.process_instrumentation_functions
    assert type(pif) is ProcessInstrumentationFunction
    assert pif.dex_id == "ProcessInstrumentationFunction-pif1"


def test_actuator_on_a_control_valve_becomes_an_actuating_system():
    graph, entities, size = _actuated_plant()
    model = dex_to_model(graph, entities, size).model
    (system,) = model.actuating_systems
    assert type(system) is ActuatingSystem
    assert type(system.controlled_actuator) is ControlledActuator
    reference = system.operated_valve_reference
    assert reference is not None
    assert reference.valve is _by_dex_id(model)["OperatedValve-a-item"]


def test_actuator_without_a_valve_keeps_its_system_and_is_reported():
    graph, entities, size = _plant()
    graph.add_node("lone-act", node_type="object")
    entities.append(_symbol("lone-act", "actuator", 500.0, 900.0))
    conversion = dex_to_model(graph, entities, size)
    (system,) = conversion.model.actuating_systems
    assert type(system.controlled_actuator) is ControlledActuator
    assert system.operated_valve_reference is None
    assert any("lone-act" in line and "no valve" in line for line in conversion.report)


@pytest.mark.parametrize("label", ["foo-widget", "insulation"], ids=["unknown-label", "insulation"])
def test_unknown_label_and_insulation_are_skipped_and_named_in_the_report(label):
    graph, entities, size = _plant()
    graph.add_node("widget-x7", node_type="object")
    entities.append(_symbol("widget-x7", label, 500.0, 900.0))
    conversion = dex_to_model(graph, entities, size)
    assert not any("widget-x7" in obj.dex_id for obj in _objects(conversion.model))
    assert any("widget-x7" in line and label in line for line in conversion.report)


def test_nozzle_without_equipment_is_skipped_and_named_in_the_report():
    graph = nx.Graph()
    graph.add_node("lone-n", node_type="object")
    entities = [_symbol("lone-n", "nozzle", 500.0, 500.0)]
    conversion = dex_to_model(graph, entities, SIZE)
    assert not any("lone-n" in obj.dex_id for obj in _objects(conversion.model))
    assert any("lone-n" in line for line in conversion.report)


# --- 3. dex_id ---------------------------------------------------------------


def test_dex_ids_follow_the_class_and_id_scheme():
    graph, entities, size = _actuated_plant()
    ids = _by_dex_id(dex_to_model(graph, entities, size).model)
    assert {
        "CustomEquipment-a-eq",
        "Nozzle-a-n1",
        "OperatedValve-a-item",
        "OperatedValve-a-item-Node1",
        "Pipe-a-line-1",
        "PipingNetworkSystem-1",
        "PipingNetworkSegment-1",
        "ProcessInstrumentationFunction-pif1",
        "SignalConveyingFunction-sig-1",
        "ActuatingSystem-act",
        "ControlledActuator-act",
        "OperatedValveReference-act",
        "ActuatingFunction-act",
    } <= set(ids)


@pytest.mark.parametrize(
    ("entity_id", "dex_id"),
    [
        ("7-eq", "CustomEquipment-7-eq"),
        ("eq:9", "CustomEquipment-eq_9"),
        ("eq 9/x", "CustomEquipment-eq_9_x"),
    ],
    ids=["leading-digit", "colon", "space-and-slash"],
)
def test_entity_ids_with_a_leading_digit_or_a_colon_stay_ncname_safe(entity_id, dex_id):
    graph = nx.Graph()
    graph.add_node(entity_id, node_type="object")
    entities = [EquipmentEntity(id=entity_id, polygon=_rect(0.0, 0.0, 100.0, 100.0))]
    (equipment,) = dex_to_model(graph, entities, SIZE).model.equipment
    assert equipment.dex_id == dex_id
    assert NCNAME.match(equipment.dex_id)


def test_every_dex_id_is_unique_and_ncname_safe():
    graph, entities, size = _actuated_plant()
    _add_run(graph, entities, "b", 900.0)
    ids = [obj.dex_id for obj in _objects(dex_to_model(graph, entities, size).model)]
    assert len(ids) >= 20
    assert len(set(ids)) == len(ids)
    assert all(NCNAME.match(dex_id) for dex_id in ids)


# --- 4. Piping ---------------------------------------------------------------


def test_each_piping_line_becomes_one_pipe_between_its_items():
    graph, entities, size = _plant()
    objects = _by_dex_id(dex_to_model(graph, entities, size).model)
    pipes = sorted(obj.dex_id for obj in objects.values() if type(obj) is Pipe)
    assert pipes == ["Pipe-a-line-1", "Pipe-a-line-2"]
    nozzle_1, valve, nozzle_2 = (
        objects["Nozzle-a-n1"],
        objects["OperatedValve-a-item"],
        objects["Nozzle-a-n2"],
    )
    line_1, line_2 = objects["Pipe-a-line-1"], objects["Pipe-a-line-2"]
    assert line_1.source_item is nozzle_1
    assert line_1.source_node is nozzle_1.nodes[0]
    assert line_1.target_item is valve
    assert line_1.target_node is valve.nodes[0]
    assert line_2.source_item is valve
    assert line_2.source_node is valve.nodes[1]
    assert line_2.target_item is nozzle_2
    assert line_2.target_node is nozzle_2.nodes[0]


def test_valve_between_two_nozzles_has_two_nodes_with_flow_indexes_one_and_two():
    graph, entities, size = _plant()
    valve = _by_dex_id(dex_to_model(graph, entities, size).model)["OperatedValve-a-item"]
    assert len(valve.nodes) == 2
    assert valve.flow_in_index == 1
    assert valve.flow_out_index == 2


def test_reverse_direction_swaps_source_and_target():
    graph, entities, size = _plant(direction="reverse")
    objects = _by_dex_id(dex_to_model(graph, entities, size).model)
    nozzle_1, valve = objects["Nozzle-a-n1"], objects["OperatedValve-a-item"]
    line_1 = objects["Pipe-a-line-1"]
    assert line_1.source_item is valve
    assert line_1.target_item is nozzle_1
    # Incoming lines come first: line 2 enters the valve, line 1 leaves it.
    assert line_1.source_node is valve.nodes[1]
    assert line_1.target_node is nozzle_1.nodes[0]
    assert valve.flow_in_index == 1
    assert valve.flow_out_index == 2


def test_missing_direction_uses_point_order_and_reports_one_assumed_line():
    graph, entities, size = _plant(direction=None)
    conversion = dex_to_model(graph, entities, size)
    objects = _by_dex_id(conversion.model)
    assert objects["Pipe-a-line-1"].source_item is objects["Nozzle-a-n1"]
    assert objects["Pipe-a-line-2"].target_item is objects["Nozzle-a-n2"]
    assumed = [line for line in conversion.report if "assumed" in line]
    assert len(assumed) == 1
    assert "a-line-1" in assumed[0]
    assert "a-line-2" in assumed[0]


def test_dead_end_leaves_the_pipe_open_on_that_side():
    graph = nx.Graph()
    for node in ("eq", "n1", "a-item"):
        graph.add_node(node, node_type="object")
    graph.add_node("end", node_type="deadend", geometry=Point(900.0, 500.0))
    graph.add_edge("eq", "n1")
    graph.add_edge("n1", "a-item", id="a-line-1", direction="forward")
    graph.add_edge("a-item", "end", id="a-line-2", direction="forward")
    entities = [
        EquipmentEntity(id="eq", polygon=_rect(0.0, 400.0, 1000.0, 600.0)),
        _symbol("n1", "nozzle", 100.0, 500.0),
        _symbol("a-item", "valve", 500.0, 500.0),
        _segment("a-line-1", [(110.0, 500.0), (490.0, 500.0)]),
        _segment("a-line-2", [(510.0, 500.0), (890.0, 500.0)]),
    ]
    objects = _by_dex_id(dex_to_model(graph, entities, SIZE).model)
    open_pipe = objects["Pipe-a-line-2"]
    assert open_pipe.source_item is objects["OperatedValve-a-item"]
    assert open_pipe.target_item is None
    assert open_pipe.target_node is None


def test_junction_becomes_a_tee_with_one_node_per_piping_line():
    graph, entities, size = _tee_plant()
    (tee,) = _of_class(dex_to_model(graph, entities, size).model, PipeTee)
    assert len(tee.nodes) == 3
    # Two lines come in (t-1, t-3) and one goes out (t-2): incoming first, then outgoing.
    assert tee.flow_in_index == 1
    assert tee.flow_out_index == 3


def test_separate_networks_become_separate_systems():
    graph, entities, size = _plant()
    _add_run(graph, entities, "b", 900.0)
    model = dex_to_model(graph, entities, size).model
    assert len(model.piping_network_systems) == 2


def test_a_tee_joining_three_chains_cuts_three_segments():
    graph, entities, size = _tee_plant()
    (system,) = dex_to_model(graph, entities, size).model.piping_network_systems
    assert len(system.segments) == 3


def test_every_in_line_item_is_in_exactly_one_segment():
    for graph, entities, size in (_actuated_plant(), _tee_plant()):
        model = dex_to_model(graph, entities, size).model
        items = [obj for obj in _objects(model) if isinstance(obj, PipingNetworkSegmentItem)]
        assert items
        placements = Counter(
            id(item)
            for system in model.piping_network_systems
            for segment in system.segments
            for item in segment.items
        )
        assert {item.dex_id: placements[id(item)] for item in items} == {
            item.dex_id: 1 for item in items
        }


# --- 5. Instrumentation ------------------------------------------------------


@pytest.mark.parametrize("kind", ["signal-line", "data-line"])
def test_signal_and_data_lines_both_link_the_instrument_to_the_actuating_function(kind):
    graph, entities, size = _actuated_plant(kind)
    objects = _by_dex_id(dex_to_model(graph, entities, size).model)
    pif = objects["ProcessInstrumentationFunction-pif1"]
    actuating = objects["ActuatingFunction-act"]
    (signal,) = pif.signal_conveying_functions
    assert signal.dex_id == "SignalConveyingFunction-sig-1"
    assert signal.source is pif
    assert signal.target is actuating
    assert _is_in(actuating, pif.actuating_functions)
    assert actuating.systems is objects["ActuatingSystem-act"]


def test_sensing_line_to_a_nozzle_locates_the_signal_generating_function_at_the_nozzle():
    graph, entities, size = _plant()
    graph.add_node("pif-s", node_type="object")
    graph.add_edge("pif-s", "a-n1", id="sense-1")
    entities.extend(
        [
            _symbol("pif-s", "instrument", 100.0, 300.0),
            _segment("sense-1", [(100.0, 310.0), (100.0, 490.0)]),
        ]
    )
    objects = _by_dex_id(dex_to_model(graph, entities, size).model)
    pif = objects["ProcessInstrumentationFunction-pif-s"]
    (psgf,) = pif.process_signal_generating_functions
    assert psgf.dex_id == "ProcessSignalGeneratingFunction-sense-1"
    assert psgf.sensing_location is objects["Nozzle-a-n1"]
    # A sensing line is not written as a pipe.
    assert "Pipe-sense-1" not in objects


def test_sensing_line_to_a_flange_locates_the_signal_generating_function_on_the_flange():
    graph, entities, size = _plant(item_label="flange")
    graph.add_node("pif-f", node_type="object")
    graph.add_edge("pif-f", "a-item", id="sense-2")
    entities.extend(
        [
            _symbol("pif-f", "instrument", 500.0, 300.0),
            _segment("sense-2", [(500.0, 310.0), (500.0, 490.0)]),
        ]
    )
    objects = _by_dex_id(dex_to_model(graph, entities, size).model)
    (psgf,) = objects["ProcessInstrumentationFunction-pif-f"].process_signal_generating_functions
    assert psgf.sensing_location is objects["Flange-a-item"]


def test_instruments_without_numbers_get_one_report_line():
    graph = nx.Graph()
    graph.add_node("pif-1", node_type="object")
    graph.add_node("pif-2", node_type="object")
    entities = [
        _symbol("pif-1", "instrument", 100.0, 100.0),
        _symbol("pif-2", "instrument", 300.0, 100.0),
    ]
    report = dex_to_model(graph, entities, SIZE).report
    lines = [line for line in report if "without number, category or loop" in line]
    assert len(lines) == 1
    assert re.search(r"\b2 instrument", lines[0])
    assert "no text is read" in lines[0]


# --- 6. Graphics -------------------------------------------------------------


def test_equipment_position_is_the_bbox_centre_and_outline_the_ring_in_mm():
    graph = nx.Graph()
    graph.add_node("eq", node_type="object")
    entities = [EquipmentEntity(id="eq", polygon=_rect(200.0, 100.0, 400.0, 300.0))]
    (equipment,) = dex_to_model(graph, entities, SIZE).model.equipment
    assert _flat([equipment.position]) == pytest.approx([30.0, 80.0])
    ring = [(20.0, 90.0), (40.0, 90.0), (40.0, 70.0), (20.0, 70.0)]
    assert _flat(_open_ring(equipment.outline)) == pytest.approx(_flat(ring))


def test_symbol_position_is_the_quad_centre_and_outline_the_closed_quad_in_mm():
    graph, entities, size = _actuated_plant()
    objects = _by_dex_id(dex_to_model(graph, entities, size).model)
    centres = {
        "Nozzle-a-n1": (100.0, 500.0),
        "OperatedValve-a-item": (500.0, 500.0),
        "ControlledActuator-act": (500.0, 400.0),
        "ProcessInstrumentationFunction-pif1": (500.0, 100.0),
    }
    for dex_id, (cx, cy) in centres.items():
        symbol = objects[dex_id]
        assert _flat([symbol.position]) == pytest.approx(_flat([_mm(cx, cy)])), dex_id
        assert len(symbol.outline) == 5, dex_id
        quad = _closed([_mm(x, y) for x, y in _box(cx, cy)])
        assert _flat(symbol.outline) == pytest.approx(_flat(quad)), dex_id


def test_tee_position_is_the_junction_point_in_mm_and_it_has_no_outline():
    graph, entities, size = _tee_plant()
    (tee,) = _of_class(dex_to_model(graph, entities, size).model, PipeTee)
    assert _flat([tee.position]) == pytest.approx([50.0, 50.0])
    assert tee.outline is None


@pytest.mark.parametrize(
    ("direction", "expected"),
    [
        ("forward", [(11.0, 50.0), (49.0, 50.0)]),
        ("reverse", [(49.0, 50.0), (11.0, 50.0)]),
    ],
    ids=["forward", "reverse"],
)
def test_pipe_center_line_is_in_flow_order_in_mm(direction, expected):
    graph, entities, size = _plant(direction=direction)
    pipe = _by_dex_id(dex_to_model(graph, entities, size).model)["Pipe-a-line-1"]
    assert _flat(pipe.center_line) == pytest.approx(_flat(expected))


def test_signal_center_line_runs_from_source_to_target_in_mm():
    graph, entities, size = _actuated_plant()
    objects = _by_dex_id(dex_to_model(graph, entities, size).model)
    signal = objects["SignalConveyingFunction-sig-1"]
    assert signal.source is objects["ProcessInstrumentationFunction-pif1"]
    assert _flat(signal.center_line) == pytest.approx(_flat([(50.0, 89.0), (50.0, 61.0)]))


def test_drawing_extent_is_the_drawing_size_and_each_axis_scales_by_its_own_size():
    size = DrawingSize(
        image_width=2000, image_height=1000, drawing_width=420.0, drawing_height=297.0
    )
    graph = nx.Graph()
    graph.add_node("eq", node_type="object")
    entities = [EquipmentEntity(id="eq", polygon=_rect(200.0, 100.0, 400.0, 300.0))]
    model = dex_to_model(graph, entities, size).model
    assert _flat([model.drawing_extent]) == pytest.approx([420.0, 297.0])
    (equipment,) = model.equipment
    # x: 300 of 2000 px is 63 mm; y: 200 of 1000 px down from the top is 297 - 59.4 mm.
    assert _flat([equipment.position]) == pytest.approx([63.0, 237.6])


def test_piping_node_positions_are_the_line_ends_in_mm():
    graph, entities, size = _plant()
    objects = _by_dex_id(dex_to_model(graph, entities, size).model)
    valve = objects["OperatedValve-a-item"]
    # The incoming line a-line-1 ends at x = 490 px, the outgoing a-line-2 starts at x = 510 px.
    assert _flat([valve.nodes[0].position]) == pytest.approx([49.0, 50.0])
    assert _flat([valve.nodes[1].position]) == pytest.approx([51.0, 50.0])
    # A nozzle has one node, at the end of its line a-line-1 (x = 110 px).
    assert _flat([objects["Nozzle-a-n1"].nodes[0].position]) == pytest.approx([11.0, 50.0])


# --- review regressions: inputs that pass the contract but are odd ----------------


def test_actuator_without_a_signal_is_reported_and_its_xml_validates(tmp_path):
    graph, entities, size = _plant(item_label="control-valve")
    graph.add_node("act", node_type="object")
    graph.add_edge("act", "a-item")
    entities.append(_symbol("act", "actuator", 500.0, 400.0))
    conversion = dex_to_model(graph, entities, size)
    assert any("'act' receives no signal" in line for line in conversion.report)
    path = tmp_path / "unsignalled.xml"
    path.write_text(to_proteus_xml(conversion.model), encoding="utf-8")
    assert _validate(path)


def test_in_line_symbol_on_no_piping_line_is_reported():
    graph, entities, size = _plant()
    graph.add_node("loose-valve", node_type="object")
    entities.append(_symbol("loose-valve", "valve", 500.0, 900.0))
    conversion = dex_to_model(graph, entities, size)
    assert "OperatedValve-loose-valve" not in _by_dex_id(conversion.model)
    assert any("'loose-valve': it is on no piping line" in line for line in conversion.report)


def test_symbol_labelled_equipment_becomes_custom_equipment():
    graph = nx.Graph()
    graph.add_node("eq-symbol", node_type="object")
    conversion = dex_to_model(graph, [_symbol("eq-symbol", "equipment", 500.0, 500.0)], SIZE)
    (equipment,) = conversion.model.equipment
    assert type(equipment) is CustomEquipment
    assert len(equipment.outline) == 5


def test_line_from_a_node_to_itself_is_skipped_and_reported():
    graph, entities, size = _plant()
    graph.add_edge("a-item", "a-item", id="loop-1")
    entities.append(_segment("loop-1", [(500.0, 490.0), (520.0, 470.0), (500.0, 490.0)]))
    conversion = dex_to_model(graph, entities, size)
    assert "Pipe-loop-1" not in _by_dex_id(conversion.model)
    assert any("'loop-1': it starts and ends at 'a-item'" in line for line in conversion.report)


def test_odd_junctions_and_open_pipes_are_reported(tmp_path):
    graph = nx.Graph()
    for node, x in (("d1", 100.0), ("j", 500.0), ("d2", 900.0)):
        graph.add_node(node, node_type="deadend" if node != "j" else "junction", geometry=Point(x, 500.0))
    graph.add_edge("d1", "j", id="o-1", direction="forward")
    graph.add_edge("j", "d2", id="o-2", direction="forward")
    graph.add_node("d3", node_type="deadend", geometry=Point(100.0, 800.0))
    graph.add_node("d4", node_type="deadend", geometry=Point(900.0, 800.0))
    graph.add_edge("d3", "d4", id="o-3", direction="forward")
    entities = [
        _segment("o-1", [(100.0, 500.0), (500.0, 500.0)]),
        _segment("o-2", [(500.0, 500.0), (900.0, 500.0)]),
        _segment("o-3", [(100.0, 800.0), (900.0, 800.0)]),
    ]
    conversion = dex_to_model(graph, entities, SIZE)
    assert any("junction 'j' has 2 piping line(s)" in line for line in conversion.report)
    assert any("pipe 'o-3' has no item at either end" in line for line in conversion.report)
    path = tmp_path / "open.xml"
    path.write_text(to_proteus_xml(conversion.model), encoding="utf-8")
    assert _validate(path)
