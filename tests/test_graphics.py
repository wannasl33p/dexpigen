"""Graphics: the optional drawing fields of the model and how ``to_proteus_xml`` writes them.

Spec section A. Every graphics field is optional and defaults to ``None``. Values are in
drawing millimetres (origin bottom-left, y up, no rotation). A point is a pair of finite
floats, and an outline or a center line has at least two points.

The writer puts a ``PolyLine`` and a ``Position`` before the children of a plant item, a
``Position`` inside a ``Node``, one ``CenterLine`` per pipe inside its segment (before the
segment's items), a ``CenterLine`` as the last child of an ``InformationFlow`` and a
``Drawing`` as the last child of ``PlantModel``. A model without graphics writes none of them.
"""

import importlib.util
import inspect
import math
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from pydantic import ValidationError

from dexpigen import equipment as equipment_module
from dexpigen import piping as piping_module
from dexpigen import to_proteus_xml
from dexpigen.equipment import CustomEquipment, Equipment, Nozzle, Tank
from dexpigen.instrumentation import (
    ActuatingFunction,
    ActuatingSystem,
    ControlledActuator,
    OperatedValveReference,
    Positioner,
    ProcessInstrumentationFunction,
    SignalConveyingFunction,
)
from dexpigen.model import ConceptualModel
from dexpigen.piping import (
    Flange,
    FlowInPipeOffPageConnector,
    FlowOutPipeOffPageConnector,
    GlobeValve,
    OperatedValve,
    Pipe,
    PipeReducer,
    PipeTee,
    PipingComponent,
    PipingNetworkSegment,
    PipingNetworkSystem,
    PipingNode,
)

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
# Elements that exist only to carry graphics; a model without graphics writes none.
GRAPHICS_TAGS = {"Position", "PolyLine", "CenterLine", "Drawing"}


def _load_example(path: Path):
    """Import an example script by file path, with ``examples/`` on ``sys.path``."""
    if str(EXAMPLES) not in sys.path:
        sys.path.insert(0, str(EXAMPLES))  # the scripts import ``validate_dexpi``
    spec = importlib.util.spec_from_file_location(f"graphics_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _validate(xml_path: Path) -> bool:
    """Return True when ``xml_path`` validates against the bundled XSD."""
    return _load_example(EXAMPLES / "validate_dexpi.py").validate(str(xml_path))


def _box(cx: float, cy: float, half: float = 5.0) -> list[tuple[float, float]]:
    """A closed square outline of five points around ``(cx, cy)``."""
    return [
        (cx - half, cy - half),
        (cx + half, cy - half),
        (cx + half, cy + half),
        (cx - half, cy + half),
        (cx - half, cy - half),
    ]


def _floats(element: ET.Element, *names: str) -> tuple[float, ...]:
    """The named attributes of ``element`` as floats, in the order given."""
    return tuple(float(element.get(name)) for name in names)


def _find(root: ET.Element, tag: str, dex_id: str) -> ET.Element:
    """The element ``<tag ID="dex_id">`` anywhere under ``root``."""
    element = root.find(f".//{tag}[@ID='{dex_id}']")
    assert element is not None, f"no <{tag} ID={dex_id!r}> in the output"
    return element


def _graphics_tags(xml: str) -> set[str]:
    """The graphics element names that occur in ``xml``."""
    return {element.tag for element in ET.fromstring(xml).iter()} & GRAPHICS_TAGS


def _graphic_model() -> ConceptualModel:
    """A small P&ID with graphics on every kind of item the spec draws.

    The tank and the pump each have one nozzle and one node. The valve sits in a segment
    between the two nozzles, with one pipe on each side. A second segment holds an
    off-page connector, a tee and a flange, with no pipes. A PIF signals an actuating
    function whose actuating system holds a controlled actuator and a positioner. The
    positioner has a position only, so it writes no outline.
    """
    tank = Tank(
        dex_id="Tank-1", tag_name="T-101",
        position=(50.0, 150.0), outline=_box(50.0, 150.0, 30.0),
    )
    tank_nozzle = Nozzle(
        dex_id="Nozzle-1", sub_tag_name="N1",
        position=(80.0, 150.0), outline=_box(80.0, 150.0),
    )
    tank_node = PipingNode(dex_id="PipingNode-1", position=(85.0, 150.0))
    tank_nozzle.add_node(tank_node)
    tank.add_nozzle(tank_nozzle)

    pump = CustomEquipment(
        dex_id="CustomEquipment-1", source_type_label="equipment",
        position=(200.0, 150.0), outline=_box(200.0, 150.0, 20.0),
    )
    pump_nozzle = Nozzle(
        dex_id="Nozzle-2", sub_tag_name="N2",
        position=(180.0, 150.0), outline=_box(180.0, 150.0),
    )
    pump_node = PipingNode(dex_id="PipingNode-2", position=(175.0, 150.0))
    pump_nozzle.add_node(pump_node)
    pump.add_nozzle(pump_nozzle)

    valve = GlobeValve(
        dex_id="GlobeValve-1", piping_component_number="V1",
        flow_in_index=1, flow_out_index=2,
        position=(120.0, 150.0), outline=_box(120.0, 150.0),
    )
    valve.add_node(PipingNode(dex_id="PipingNode-3", position=(110.0, 150.0)))
    valve.add_node(PipingNode(dex_id="PipingNode-4", position=(130.0, 150.0)))

    segment = PipingNetworkSegment(
        dex_id="PipingNetworkSegment-1", segment_number="S1", items=[valve],
    )
    segment.add_connection(Pipe(
        dex_id="Pipe-1", source_item=tank_nozzle, source_node=tank_node,
        target_item=valve, target_node=valve.nodes[0],
        center_line=[(85.0, 150.0), (110.0, 150.0)],
    ))
    segment.add_connection(Pipe(
        dex_id="Pipe-2", source_item=valve, source_node=valve.nodes[1],
        target_item=pump_nozzle, target_node=pump_node,
        center_line=[(130.0, 150.0), (175.0, 150.0)],
    ))

    connector = FlowInPipeOffPageConnector(
        dex_id="FlowInPipeOffPageConnector-1", flow_out_index=1,
        position=(300.0, 100.0), outline=_box(300.0, 100.0),
    )
    connector.add_node(PipingNode(dex_id="PipingNode-5", position=(305.0, 100.0)))
    tee = PipeTee(dex_id="PipeTee-1", position=(260.0, 150.0))
    flange = Flange(
        dex_id="Flange-1", position=(240.0, 150.0), outline=_box(240.0, 150.0, 3.0),
    )
    segment_2 = PipingNetworkSegment(
        dex_id="PipingNetworkSegment-2", segment_number="S2",
        items=[connector, tee, flange],
    )

    line = PipingNetworkSystem(
        dex_id="PipingNetworkSystem-1", line_number="47121",
        segments=[segment, segment_2],
    )

    actuating_system = ActuatingSystem(
        dex_id="ActuatingSystem-1", actuating_system_number="TV4750.03",
    )
    actuating_system.add_controlled_actuator(ControlledActuator(
        dex_id="ControlledActuator-1", device_type_name="general",
        sub_tag_name="TV4750.03_YC",
        position=(120.0, 200.0), outline=_box(120.0, 200.0),
    ))
    actuating_system.add_operated_valve_reference(OperatedValveReference(
        dex_id="OperatedValveReference-1", sub_tag_name="TV4750.03_YV", valve=valve,
    ))
    actuating_system.add_positioner(Positioner(
        dex_id="Positioner-1", sub_tag_name="TV4750.03_ZC", position=(140.0, 200.0),
    ))

    pif = ProcessInstrumentationFunction(
        dex_id="ProcessInstrumentationFunction-1",
        process_instrumentation_function_number="4750.03",
        process_instrumentation_function_category="T",
        process_instrumentation_functions_code="IC",
        position=(100.0, 250.0), outline=_box(100.0, 250.0, 8.0),
    )
    actuating = ActuatingFunction(
        dex_id="ActuatingFunction-1", actuating_function_number="TV4750.03",
        systems=actuating_system,
    )
    pif.add_actuating_function(actuating)
    pif.add_signal_conveying_function(SignalConveyingFunction(
        dex_id="SignalConveyingFunction-1", source=pif, target=actuating,
        center_line=[(100.0, 242.0), (120.0, 205.0)],
    ))

    return (
        ConceptualModel(dex_id="graphics", drawing_extent=(420, 297))
        .add_equipment(tank)
        .add_equipment(pump)
        .add_piping_network_system(line)
        .add_process_instrumentation_function(pif)
        .add_actuating_system(actuating_system)
    )


@pytest.fixture(scope="module")
def graphic_xml() -> str:
    return to_proteus_xml(_graphic_model())


@pytest.fixture(scope="module")
def graphic_root(graphic_xml: str) -> ET.Element:
    return ET.fromstring(graphic_xml)


# --- fields: defaults -------------------------------------------------------------


@pytest.mark.parametrize(
    "cls",
    [
        CustomEquipment, Tank, Nozzle, OperatedValve, GlobeValve, PipeTee, Flange,
        PipeReducer, FlowInPipeOffPageConnector, FlowOutPipeOffPageConnector,
        ProcessInstrumentationFunction, ControlledActuator, Positioner,
    ],
    ids=lambda cls: cls.__name__,
)
def test_plant_items_have_position_and_outline_defaulting_to_none(cls):
    item = cls(dex_id="Item-1")
    assert item.position is None
    assert item.outline is None


def test_every_concrete_equipment_and_piping_component_has_the_fields():
    """The mixin fields reach every concrete subclass, not only the ones named above."""
    concrete = [
        cls
        for module, base in ((equipment_module, Equipment), (piping_module, PipingComponent))
        for _, cls in inspect.getmembers(module, inspect.isclass)
        if issubclass(cls, base) and not cls._abstract
    ]
    assert {CustomEquipment, Tank, GlobeValve, PipeTee} <= set(concrete)
    for cls in concrete:
        assert {"position", "outline"} <= set(cls.model_fields), cls.__name__
        item = cls(dex_id="Item-1")
        assert item.position is None and item.outline is None, cls.__name__


def test_piping_node_pipe_signal_and_drawing_graphics_default_to_none():
    assert PipingNode(dex_id="PipingNode-1").position is None
    assert Pipe(dex_id="Pipe-1").center_line is None
    assert SignalConveyingFunction(dex_id="SignalConveyingFunction-1").center_line is None
    assert ConceptualModel(dex_id="model").drawing_extent is None


# --- fields: validation -----------------------------------------------------------

NON_FINITE_POINTS = [(math.nan, 1.0), (1.0, math.inf)]
POINT_FIELDS = {
    "tank position": lambda point: Tank(dex_id="Tank-1", position=point),
    "tank outline point": lambda point: Tank(
        dex_id="Tank-1", outline=[(0.0, 0.0), point, (1.0, 1.0)],
    ),
    "node position": lambda point: PipingNode(dex_id="PipingNode-1", position=point),
    "pipe center line point": lambda point: Pipe(
        dex_id="Pipe-1", center_line=[(0.0, 0.0), point],
    ),
    "signal center line point": lambda point: SignalConveyingFunction(
        dex_id="SignalConveyingFunction-1", center_line=[(0.0, 0.0), point],
    ),
    "drawing extent": lambda point: ConceptualModel(dex_id="model", drawing_extent=point),
}


@pytest.mark.parametrize("build", list(POINT_FIELDS.values()), ids=list(POINT_FIELDS))
@pytest.mark.parametrize("point", NON_FINITE_POINTS, ids=["nan-x", "inf-y"])
def test_non_finite_points_are_rejected(build, point):
    with pytest.raises(ValidationError):
        build(point)


POLYLINE_FIELDS = {
    "tank outline": lambda points: Tank(dex_id="Tank-1", outline=points),
    "pipe center line": lambda points: Pipe(dex_id="Pipe-1", center_line=points),
    "signal center line": lambda points: SignalConveyingFunction(
        dex_id="SignalConveyingFunction-1", center_line=points,
    ),
}


@pytest.mark.parametrize("build", list(POLYLINE_FIELDS.values()), ids=list(POLYLINE_FIELDS))
@pytest.mark.parametrize("points", [[], [(0.0, 0.0)]], ids=["no-points", "one-point"])
def test_outline_and_center_line_need_at_least_two_points(build, points):
    with pytest.raises(ValidationError):
        build(points)


def test_finite_points_and_two_point_lines_are_accepted():
    assert Tank(dex_id="Tank-1", position=(1.5, 2.0)).position == (1.5, 2.0)
    assert Tank(dex_id="Tank-1", outline=[(0.0, 0.0), (1.0, 1.0)]).outline == [
        (0.0, 0.0), (1.0, 1.0),
    ]
    assert Pipe(dex_id="Pipe-1", center_line=[(0.0, 0.0), (1.0, 0.0)]).center_line == [
        (0.0, 0.0), (1.0, 0.0),
    ]
    assert SignalConveyingFunction(
        dex_id="SignalConveyingFunction-1", center_line=[(0.0, 0.0), (0.0, 1.0)],
    ).center_line == [(0.0, 0.0), (0.0, 1.0)]
    assert ConceptualModel(dex_id="model", drawing_extent=(420, 297)).drawing_extent == (
        420.0, 297.0,
    )


# --- writer -----------------------------------------------------------------------


@pytest.mark.skipif(shutil.which("xmllint") is None, reason="xmllint is not on PATH")
def test_graphics_model_serializes_to_schema_valid_xml(graphic_xml, tmp_path):
    path = tmp_path / "graphics.xml"
    path.write_text(graphic_xml, encoding="utf-8")
    assert _validate(path)


@pytest.mark.parametrize(
    ("tag", "dex_id"),
    [
        ("Equipment", "Tank-1"),
        ("Equipment", "CustomEquipment-1"),
        ("Nozzle", "Nozzle-1"),
        ("PipingComponent", "GlobeValve-1"),
        ("PipeOffPageConnector", "FlowInPipeOffPageConnector-1"),
        ("PipingComponent", "PipeTee-1"),
        ("PipingComponent", "Flange-1"),
        ("ProcessInstrumentationFunction", "ProcessInstrumentationFunction-1"),
        ("ActuatingSystemComponent", "ControlledActuator-1"),
        ("ActuatingSystemComponent", "Positioner-1"),
    ],
    ids=[
        "tank", "custom-equipment", "nozzle", "globe-valve", "off-page-connector",
        "tee", "flange", "pif", "controlled-actuator", "positioner",
    ],
)
def test_plant_item_graphics_precede_its_children(graphic_root, tag, dex_id):
    item = _find(graphic_root, tag, dex_id)
    tags = [child.tag for child in item]
    graphics = [i for i, child_tag in enumerate(tags) if child_tag in {"PolyLine", "Position"}]
    others = [i for i, child_tag in enumerate(tags) if child_tag not in {"PolyLine", "Position"}]
    assert graphics and others, tags
    assert max(graphics) < min(others), tags
    if "PolyLine" in tags:
        assert tags.index("PolyLine") < tags.index("Position"), tags


def test_outline_is_written_as_a_polyline_with_a_presentation(graphic_root):
    polyline = _find(graphic_root, "Equipment", "Tank-1").find("PolyLine")
    assert polyline is not None
    assert polyline.get("NumPoints") == "5"
    presentation = polyline.find("Presentation")
    assert presentation is not None
    for name, value in {"LineType": "0", "LineWeight": "0.25", "R": "0", "G": "0", "B": "0"}.items():
        assert presentation.get(name) == value
    assert [_floats(point, "X", "Y") for point in polyline.findall("Coordinate")] == _box(
        50.0, 150.0, 30.0,
    )


def test_position_is_written_as_location_axis_and_reference(graphic_root):
    position = _find(graphic_root, "Equipment", "Tank-1").find("Position")
    assert [child.tag for child in position] == ["Location", "Axis", "Reference"]
    assert _floats(position.find("Location"), "X", "Y", "Z") == (50.0, 150.0, 0.0)
    assert _floats(position.find("Axis"), "X", "Y", "Z") == (0.0, 0.0, 1.0)
    assert _floats(position.find("Reference"), "X", "Y", "Z") == (1.0, 0.0, 0.0)
    # An item with a position and no outline writes no PolyLine.
    positioner = _find(graphic_root, "ActuatingSystemComponent", "Positioner-1")
    assert positioner.find("PolyLine") is None
    assert _floats(positioner.find("Position/Location"), "X", "Y") == (140.0, 200.0)
    tee = _find(graphic_root, "PipingComponent", "PipeTee-1")
    assert tee.find("PolyLine") is None
    assert _floats(tee.find("Position/Location"), "X", "Y") == (260.0, 150.0)


def test_piping_node_position_is_written_inside_its_node(graphic_root):
    node = graphic_root.find(".//Node[@ID='PipingNode-3']")
    assert node is not None
    assert node.get("Type") == "process"
    assert _floats(node.find("Position/Location"), "X", "Y") == (110.0, 150.0)


def test_pipe_center_lines_follow_the_connections_inside_the_segment(graphic_root):
    segment = _find(graphic_root, "PipingNetworkSegment", "PipingNetworkSegment-1")
    center_lines = segment.findall("CenterLine")
    assert [center_line.get("NumPoints") for center_line in center_lines] == ["2", "2"]
    assert [
        [_floats(point, "X", "Y") for point in center_line.findall("Coordinate")]
        for center_line in center_lines
    ] == [
        [(85.0, 150.0), (110.0, 150.0)],  # Pipe-1: tank nozzle node to the valve
        [(130.0, 150.0), (175.0, 150.0)],  # Pipe-2: the valve to the pump nozzle node
    ]
    # The center lines come before the segment's items, and a Connection holds none.
    tags = [child.tag for child in segment]
    first_item = tags.index("PipingComponent")
    assert all(i < first_item for i, child_tag in enumerate(tags) if child_tag == "CenterLine")
    assert segment.find("Connection/CenterLine") is None
    # A segment whose connections have no center line writes none.
    assert _find(graphic_root, "PipingNetworkSegment", "PipingNetworkSegment-2").find(
        "CenterLine"
    ) is None


def test_signal_center_line_is_the_last_child_of_its_information_flow(graphic_root):
    flow = _find(graphic_root, "InformationFlow", "SignalConveyingFunction-1")
    center_line = list(flow)[-1]
    assert center_line.tag == "CenterLine"
    assert center_line.get("NumPoints") == "2"
    assert [_floats(point, "X", "Y") for point in center_line.findall("Coordinate")] == [
        (100.0, 242.0), (120.0, 205.0),
    ]


def test_drawing_is_the_last_child_of_the_plant_model_with_the_sheet_extent(graphic_root):
    drawing = list(graphic_root)[-1]
    assert drawing.tag == "Drawing"
    assert len(graphic_root.findall("Drawing")) == 1
    assert drawing.get("Name") == "graphics"
    assert drawing.get("Type") == "PID"
    presentation = drawing.find("Presentation")
    assert presentation is not None
    assert {name: presentation.get(name) for name in ("R", "G", "B")} == {
        "R": "1", "G": "1", "B": "1",
    }
    assert _floats(drawing.find("Extent/Min"), "X", "Y") == (0.0, 0.0)
    assert _floats(drawing.find("Extent/Max"), "X", "Y") == (420.0, 297.0)


@pytest.mark.parametrize(
    "script",
    [EXAMPLES / "minimal.py", *sorted((EXAMPLES / "recipes").glob("*.py"))],
    ids=lambda script: script.stem,
)
def test_example_models_without_graphics_write_no_graphics_elements(script):
    """Backward compatibility: a model with no graphics fields writes none of the elements."""
    xml = to_proteus_xml(_load_example(script).build())
    assert _graphics_tags(xml) == set()
