"""C01 acceptance: the Dex sample converts into the C01 structure, with graphics.

``examples/C01/dex_model/load.py`` turns the sample into the converter input, and
``dex_to_model`` converts it (spec section D, research 02). The model must hold the C01
inventory, the nesting of nozzles in equipment, and the piping, signal, sensing and valve
links that the sample's graph implies. The Proteus output must be schema-valid, the report
must name the insulation Entity it skips, and every item must lie inside the 420 x 297 mm
sheet. Model ids follow the ``dex_id`` rule of spec section C: ``ClassName-<id>`` with each
character outside ``[A-Za-z0-9_.-]`` replaced by ``_``.
"""

import importlib.util
import re
import shutil
from collections import Counter
from pathlib import Path

import pytest

from dexpigen import to_proteus_xml
from dexpigen.base import DexpiBaseModel
from dexpigen.entities import dex_to_model, dex_to_proteus
from dexpigen.equipment import CustomEquipment, Nozzle
from dexpigen.instrumentation import (
    ActuatingFunction,
    ActuatingSystem,
    ControlledActuator,
    OperatedValveReference,
    ProcessInstrumentationFunction,
    ProcessSignalGeneratingFunction,
    SignalConveyingFunction,
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
    PipingNetworkSegment,
)

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
ADAPTER = EXAMPLES / "C01" / "dex_model" / "load.py"
SHEET = (420.0, 297.0)

# The model class that an object node of each coarse Dex label becomes (spec section C).
# A junction becomes a PipeTee and a dead end has no object, so neither is listed here.
OBJECT_CLASSES = {
    "equipment": ("CustomEquipment",),
    "nozzle": ("Nozzle",),
    "valve": ("OperatedValve",),
    "control-valve": ("OperatedValve",),
    "flange": ("Flange",),
    "reducer": ("PipeReducer",),
    # The class of an off-page connector depends on the flow; either name is accepted here.
    "off-page-connector": ("FlowInPipeOffPageConnector", "FlowOutPipeOffPageConnector"),
    "instrument": ("ProcessInstrumentationFunction",),
    "actuator": ("ControlledActuator",),
}


def _load_module(name: str, path: Path):
    """Import a file as a module, without putting its folder on ``sys.path``."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _validate(xml_path: Path) -> bool:
    """Return True when ``xml_path`` validates against the bundled XSD."""
    return _load_module("c01_validate_dexpi", EXAMPLES / "validate_dexpi.py").validate(
        str(xml_path)
    )


def _wire(text: str) -> str:
    """Replace each character outside ``[A-Za-z0-9_.-]`` with ``_``."""
    return re.sub(r"[^A-Za-z0-9_.-]", "_", text)


def _dex_id(class_name: str, entity_id: str) -> str:
    """The ``dex_id`` of the model object made from ``entity_id``."""
    return _wire(f"{class_name}-{entity_id}")


def _model_ids(graph, node: str) -> list[str]:
    """The ``dex_id`` candidates of the object a Dex node becomes; empty for a dead end."""
    data = graph.nodes[node]
    if data["node_type"] == "deadend":
        return []
    if data["node_type"] == "junction":
        return [_dex_id("PipeTee", node)]
    return [_dex_id(name, node) for name in OBJECT_CLASSES[data["label"]]]


def _piping_end(graph, node: str) -> set[str | None]:
    """The ``Pipe`` end a Dex node may make: its ``dex_id`` candidates, or ``None``."""
    return set(_model_ids(graph, node)) or {None}


def _labels(graph, u: str, v: str) -> set[str]:
    return {graph.nodes[u]["label"], graph.nodes[v]["label"]}


def _lines(graph, suffix: str) -> list[tuple[str, str, str]]:
    """``(u, v, edge id)`` for every edge whose id ends with ``suffix``."""
    return [
        (u, v, data["id"])
        for u, v, data in graph.edges(data=True)
        if data["id"].endswith(suffix)
    ]


def _is_sensing(graph, u: str, v: str) -> bool:
    """A piping line with an instrument at one end is a sensing line, not a pipe."""
    return "instrument" in _labels(graph, u, v)


def _end(item) -> str | None:
    return None if item is None else item.dex_id


def _segments(model: ConceptualModel) -> list[PipingNetworkSegment]:
    return [segment for line in model.piping_network_systems for segment in line.segments]


def _functions(model: ConceptualModel, field: str) -> list:
    """The functions of one kind composed under the PIFs, e.g. ``signal_conveying_functions``."""
    return [
        function
        for pif in model.process_instrumentation_functions
        for function in getattr(pif, field)
    ]


def _model_objects(model: ConceptualModel) -> list[DexpiBaseModel]:
    """Every model object reachable from ``model`` through its fields, each listed once."""
    found: dict[int, DexpiBaseModel] = {}
    stack: list[DexpiBaseModel] = [model]
    while stack:
        obj = stack.pop()
        if id(obj) in found:
            continue
        found[id(obj)] = obj
        for name in type(obj).model_fields:
            value = getattr(obj, name)
            for child in value if isinstance(value, list) else [value]:
                if isinstance(child, DexpiBaseModel):
                    stack.append(child)
    return list(found.values())


def _adapter():
    """The C01 sample adapter (not public API, see its docstring)."""
    return _load_module("c01_dex_acceptance_load", ADAPTER)


@pytest.fixture(scope="module")
def sample():
    return _adapter().load()


@pytest.fixture(scope="module")
def conversion(sample):
    return dex_to_model(*sample)


def test_equipment_and_nozzles_nest_by_their_attachment_edges(sample, conversion):
    graph, _, _ = sample
    model = conversion.model
    assert Counter(type(item) for item in model.equipment) == {CustomEquipment: 5}
    owners = {item.dex_id: item for item in model.equipment}
    nozzles = [nozzle for item in model.equipment for nozzle in item.nozzles]
    dex_nozzles = [node for node, label in graph.nodes(data="label") if label == "nozzle"]
    assert len(nozzles) == len(dex_nozzles) == 19
    assert all(type(nozzle) is Nozzle for nozzle in nozzles)
    assert {nozzle.dex_id for nozzle in nozzles} == {
        _dex_id("Nozzle", node) for node in dex_nozzles
    }
    # Each nozzle is composed under the equipment at the other end of its attachment edge.
    attachments = [
        (u, v) for u, v in graph.edges if _labels(graph, u, v) == {"equipment", "nozzle"}
    ]
    assert len(attachments) == 19
    for u, v in attachments:
        equipment, nozzle = (u, v) if graph.nodes[u]["label"] == "equipment" else (v, u)
        composed = [item.dex_id for item in owners[_dex_id("CustomEquipment", equipment)].nozzles]
        assert _dex_id("Nozzle", nozzle) in composed
    # A nozzle has exactly one process node, shared by its piping lines (spec section C).
    assert all(len(nozzle.nodes) == 1 for nozzle in nozzles)


def test_piping_inventory_matches_c01(conversion):
    model = conversion.model
    items = [item for segment in _segments(model) for item in segment.items]
    connections = [
        connection for segment in _segments(model) for connection in segment.connections
    ]
    assert Counter(type(item) for item in items) == {
        OperatedValve: 11,
        Flange: 2,
        PipeReducer: 1,
        PipeTee: 5,
        FlowInPipeOffPageConnector: 1,
        FlowOutPipeOffPageConnector: 1,
    }
    assert Counter(type(connection) for connection in connections) == {Pipe: 31}
    assert len(model.piping_network_systems) == 10
    assert len(_segments(model)) == 20


def test_instrumentation_inventory_matches_c01(conversion):
    model = conversion.model
    assert Counter(type(pif) for pif in model.process_instrumentation_functions) == {
        ProcessInstrumentationFunction: 4,
    }
    assert Counter(
        type(function)
        for function in _functions(model, "process_signal_generating_functions")
    ) == {ProcessSignalGeneratingFunction: 3}
    assert Counter(
        type(function) for function in _functions(model, "signal_conveying_functions")
    ) == {SignalConveyingFunction: 3}
    assert Counter(
        type(function) for function in _functions(model, "actuating_functions")
    ) == {ActuatingFunction: 3}
    systems = model.actuating_systems
    assert Counter(type(system) for system in systems) == {ActuatingSystem: 3}
    assert all(type(system.controlled_actuator) is ControlledActuator for system in systems)
    assert all(
        type(system.operated_valve_reference) is OperatedValveReference for system in systems
    )


def test_pipes_join_the_items_of_the_dex_piping_lines(sample, conversion):
    """The piping graph is compared without direction: each Pipe joins the two ends of a line."""
    graph, _, _ = sample
    lines = [line for line in _lines(graph, "_line") if not _is_sensing(graph, line[0], line[1])]
    assert len(lines) == 31
    pipes = {
        pipe.dex_id: pipe
        for segment in _segments(conversion.model)
        for pipe in segment.connections
    }
    assert set(pipes) == {_dex_id("Pipe", edge_id) for _, _, edge_id in lines}
    for u, v, edge_id in lines:
        pipe = pipes[_dex_id("Pipe", edge_id)]
        source, target = _end(pipe.source_item), _end(pipe.target_item)
        forward = source in _piping_end(graph, u) and target in _piping_end(graph, v)
        backward = source in _piping_end(graph, v) and target in _piping_end(graph, u)
        assert forward or backward, edge_id


def test_signals_run_from_each_pif_to_its_actuating_function(sample, conversion):
    graph, _, _ = sample
    model = conversion.model
    lines = _lines(graph, "_dashed")
    assert len(lines) == 3
    signals = {
        signal.dex_id: signal
        for signal in _functions(model, "signal_conveying_functions")
    }
    assert set(signals) == {_dex_id("SignalConveyingFunction", edge_id) for _, _, edge_id in lines}
    pifs = {pif.dex_id: pif for pif in model.process_instrumentation_functions}
    for u, v, edge_id in lines:
        assert _labels(graph, u, v) == {"instrument", "actuator"}, edge_id
        # Spec section C: instrument to actuator runs from the PIF to the ActuatingFunction.
        instrument, actuator = (u, v) if graph.nodes[u]["label"] == "instrument" else (v, u)
        signal = signals[_dex_id("SignalConveyingFunction", edge_id)]
        assert signal.source.dex_id == _dex_id("ProcessInstrumentationFunction", instrument)
        assert signal.target.dex_id == _dex_id("ActuatingFunction", actuator)
        owner = pifs[_dex_id("ProcessInstrumentationFunction", instrument)]
        assert signal.dex_id in [function.dex_id for function in owner.signal_conveying_functions]


def test_sensing_functions_are_located_at_the_other_end_of_their_lines(sample, conversion):
    graph, _, _ = sample
    model = conversion.model
    lines = [line for line in _lines(graph, "_line") if _is_sensing(graph, line[0], line[1])]
    assert len(lines) == 3
    psgfs = {
        psgf.dex_id: psgf
        for psgf in _functions(model, "process_signal_generating_functions")
    }
    assert set(psgfs) == {
        _dex_id("ProcessSignalGeneratingFunction", edge_id) for _, _, edge_id in lines
    }
    pifs = {pif.dex_id: pif for pif in model.process_instrumentation_functions}
    for u, v, edge_id in lines:
        instrument, location = (u, v) if graph.nodes[u]["label"] == "instrument" else (v, u)
        psgf = psgfs[_dex_id("ProcessSignalGeneratingFunction", edge_id)]
        # The location is the nozzle or piping component at the other end of the line.
        assert psgf.sensing_location.dex_id in _model_ids(graph, location), edge_id
        owner = pifs[_dex_id("ProcessInstrumentationFunction", instrument)]
        assert psgf.dex_id in [function.dex_id for function in owner.process_signal_generating_functions]


def test_each_actuator_is_an_actuating_system_on_its_control_valve(sample, conversion):
    graph, _, _ = sample
    model = conversion.model
    systems = {system.dex_id: system for system in model.actuating_systems}
    assert len(systems) == 3
    functions = {function.dex_id: function for function in _functions(model, "actuating_functions")}
    pifs = {pif.dex_id: pif for pif in model.process_instrumentation_functions}
    signalling = {}
    for u, v, _ in _lines(graph, "_dashed"):
        instrument, actuator = (u, v) if graph.nodes[u]["label"] == "instrument" else (v, u)
        signalling[actuator] = instrument
    attachments = [
        (u, v) for u, v in graph.edges if _labels(graph, u, v) == {"actuator", "control-valve"}
    ]
    assert len(attachments) == 3
    for u, v in attachments:
        actuator, valve = (u, v) if graph.nodes[u]["label"] == "actuator" else (v, u)
        system = systems[_dex_id("ActuatingSystem", actuator)]
        assert system.controlled_actuator.dex_id == _dex_id("ControlledActuator", actuator)
        reference = system.operated_valve_reference
        assert reference.dex_id == _dex_id("OperatedValveReference", actuator)
        assert reference.valve.dex_id == _dex_id("OperatedValve", valve)
        function = functions[_dex_id("ActuatingFunction", actuator)]
        assert function.systems.dex_id == system.dex_id
        # The ActuatingFunction is composed under the PIF that signals the actuator.
        owner = pifs[_dex_id("ProcessInstrumentationFunction", signalling[actuator])]
        assert function.dex_id in [f.dex_id for f in owner.actuating_functions]


def test_report_names_the_insulation_entity_and_counts_the_instruments(sample, conversion):
    _, entities, _ = sample
    (insulation,) = [entity for entity in entities if entity.label == "insulation"]
    report = conversion.report
    assert any(insulation.id in line and "insulation" in line for line in report)
    assert any(
        "4 instrument(s) without number, category or loop: no text is read" in line
        for line in report
    )


@pytest.mark.skipif(shutil.which("xmllint") is None, reason="xmllint is not on PATH")
def test_dex_to_proteus_output_is_schema_valid(tmp_path):
    xml = dex_to_proteus(*_adapter().load())
    path = tmp_path / "c01_dex.xml"
    path.write_text(xml, encoding="utf-8")
    assert _validate(path)


def test_dex_to_proteus_is_the_serialization_of_the_converted_model(conversion):
    assert dex_to_proteus(*_adapter().load()) == to_proteus_xml(conversion.model)


def test_every_c01_item_is_placed_inside_the_sheet(sample, conversion):
    graph, _, _ = sample
    model = conversion.model
    assert model.drawing_extent == SHEET
    objects = _model_objects(model)
    placed = {
        obj.dex_id: obj.position
        for obj in objects
        if getattr(obj, "position", None) is not None
    }
    assert placed
    for dex_id, (x, y) in placed.items():
        assert 0.0 <= x <= SHEET[0] and 0.0 <= y <= SHEET[1], dex_id
    # Every labelled object and every junction has a position; the insulation is not drawn.
    by_id = {obj.dex_id: obj for obj in objects}
    for node, data in graph.nodes(data=True):
        if data["node_type"] == "deadend" or data["label"] == "insulation":
            continue
        found = [by_id[dex_id] for dex_id in _model_ids(graph, node) if dex_id in by_id]
        assert found and found[0].position is not None, node
