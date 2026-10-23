"""Serialization: Proteus output must validate and match the reference fixture.

The project rule (CLAUDE.md): after generating any Proteus XML, validate it
with ``xmllint`` against the schema. On top of that, serializing the C01 model
built by ``examples/C01/build.py`` must reproduce the latest golden,
``examples/C01/ver002/c01.xml`` (compared canonically: ignoring whitespace, ``ID``
values and the graphics-only ``ComponentName`` attribute). The earlier
``ver001/c01.xml`` is kept as a historical snapshot and is still checked for
XSD validity.
"""

import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

from dexpigen.equipment import Nozzle, Tank
from dexpigen.instrumentation import (
    ActuatingFunction,
    InstrumentationLoopFunction,
    ProcessControlFunction,
    ProcessInstrumentationFunction,
    ProcessSignalGeneratingFunction,
    SignalConveyingFunction,
)
from dexpigen.model import ConceptualModel
from dexpigen.piping import (
    FlowMeasuringElement,
    PipeTee,
    PipingNetworkSegment,
    PipingNetworkSystem,
    PipingNode,
)
from dexpigen.serialization import to_proteus_xml

XSD = "data/schemas/ProteusPIDSchema 4.1.1.xsd"
EXAMPLES = os.path.join(os.path.dirname(__file__), "..", "examples")


def proteus_is_valid(xml_path: str) -> bool:
    """Return True if ``xml_path`` validates against the bundled XSD."""
    result = subprocess.run(
        ["xmllint", "--noout", "--schema", XSD, xml_path],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _canonical(root: ET.Element):
    """A comparable, order-insensitive signature of an element tree."""

    def norm(elem: ET.Element):
        attrs = {k: v for k, v in elem.attrib.items() if k not in ("ID", "ComponentName")}
        return (elem.tag, tuple(sorted(attrs.items())), [norm(c) for c in elem])

    return norm(root)


@pytest.mark.skipif(shutil.which("xmllint") is None, reason="xmllint is not on PATH")
def test_generation_fixture_validates_against_xsd():
    assert proteus_is_valid("examples/C01/ver001/c01.xml")


@pytest.mark.skipif(shutil.which("xmllint") is None, reason="xmllint is not on PATH")
def test_ver002_fixture_validates_against_xsd():
    assert proteus_is_valid("examples/C01/ver002/c01.xml")


def test_serialize_matches_c01_fixture():
    sys.path.insert(0, EXAMPLES)
    from C01.build import build  # noqa: PLC0415

    got = ET.fromstring(to_proteus_xml(build()))
    expected = ET.parse(os.path.join(EXAMPLES, "C01", "ver002", "c01.xml")).getroot()
    assert _canonical(got) == _canonical(expected)


# --- PipeTee and the ComponentName wire attribute ---

def _tee_model(**tee_kwargs) -> ConceptualModel:
    tee = PipeTee(dex_id="TEE-1", flow_in_index=1, **tee_kwargs)
    for i in range(3):
        tee.add_node(PipingNode(dex_id=f"TEE-1-N{i + 1}"))
    segment = PipingNetworkSegment(dex_id="SEG-1")
    segment.add_item(tee)
    line = PipingNetworkSystem(dex_id="LINE-1", line_number="100-P-1")
    line.add_segment(segment)
    model = ConceptualModel(dex_id="MODEL-1")
    model.add_piping_network_system(line)
    return model


def _find_by_id(root, dex_id):
    matches = [e for e in root.iter() if e.get("ID") == dex_id]
    assert len(matches) == 1, dex_id
    return matches[0]


@pytest.mark.skipif(shutil.which("xmllint") is None, reason="xmllint is not on PATH")
def test_pipe_tee_serialized_xml_validates_against_xsd(tmp_path):
    xml = to_proteus_xml(_tee_model())
    path = tmp_path / "tee.xml"
    path.write_text(xml, encoding="utf-8")
    assert proteus_is_valid(str(path))


def test_pipe_tee_serializes_as_piping_component_with_connection_points():
    root = ET.fromstring(to_proteus_xml(_tee_model()))
    element = _find_by_id(root, "TEE-1")
    assert element.tag == "PipingComponent"
    assert element.get("ComponentClass") == "PipeTee"
    assert element.get("ComponentClassURI") == "http://data.posccaesar.org/rdl/RDS427724"
    points = element.find("ConnectionPoints")
    assert points is not None
    assert points.get("NumPoints") == "4"  # 3 process nodes + implicit default node
    assert points.get("FlowIn") == "1"
    assert points.get("FlowOut") is None
    process_ids = [
        n.get("ID") for n in points.findall("Node") if n.get("Type") == "process"
    ]
    assert process_ids == ["TEE-1-N1", "TEE-1-N2", "TEE-1-N3"]


def test_pipe_tee_is_placed_in_segment_items():
    root = ET.fromstring(to_proteus_xml(_tee_model()))
    segment = _find_by_id(root, "SEG-1")
    assert segment.tag == "PipingNetworkSegment"
    components = segment.findall("PipingComponent")
    assert [c.get("ID") for c in components] == ["TEE-1"]


def test_component_name_emitted_when_set():
    model = _tee_model(component_name="T_TYPE_CONNECTION_SHAPE")
    root = ET.fromstring(to_proteus_xml(model))
    element = _find_by_id(root, "TEE-1")
    assert element.get("ComponentName") == "T_TYPE_CONNECTION_SHAPE"


def test_component_name_absent_when_unset():
    root = ET.fromstring(to_proteus_xml(_tee_model()))
    element = _find_by_id(root, "TEE-1")
    assert "ComponentName" not in element.attrib


def test_component_name_is_emitted_on_any_plant_item_when_set():
    model = ConceptualModel(dex_id="MODEL-1")
    model.add_equipment(Tank(dex_id="TK-1", component_name="PipingComponent_abc"))
    model.add_equipment(Tank(dex_id="TK-2"))
    root = ET.fromstring(to_proteus_xml(model))
    assert _find_by_id(root, "TK-1").get("ComponentName") == "PipingComponent_abc"
    assert "ComponentName" not in _find_by_id(root, "TK-2").attrib


def test_component_name_is_not_emitted_on_connection_or_node():
    model = _tee_model(component_name="T_TYPE_CONNECTION_SHAPE")
    root = ET.fromstring(to_proteus_xml(model))
    for node in root.iter("Node"):
        assert "ComponentName" not in node.attrib
    for connection in root.iter("Connection"):
        assert "ComponentName" not in connection.attrib


@pytest.mark.skipif(shutil.which("xmllint") is None, reason="xmllint is not on PATH")
def test_component_name_serialized_xml_validates_against_xsd(tmp_path):
    xml = to_proteus_xml(_tee_model(component_name="T_TYPE_CONNECTION_SHAPE"))
    path = tmp_path / "tee_named.xml"
    path.write_text(xml, encoding="utf-8")
    assert proteus_is_valid(str(path))


# --- InstrumentationLoopFunction, PIF inverse association, ComponentClass ---

def _loop_model() -> ConceptualModel:
    pif_1 = ProcessInstrumentationFunction(
        dex_id="PIF-1", process_instrumentation_function_number="101",
        process_instrumentation_functions_code="ICSA",
    )
    pif_2 = ProcessInstrumentationFunction(
        dex_id="PIF-2", process_instrumentation_function_number="102",
    )
    loop = InstrumentationLoopFunction(
        dex_id="ILF-1", instrumentation_loop_function_number="LOOP-7",
        process_instrumentation_functions=[pif_1, pif_2],
    )
    model = ConceptualModel(dex_id="MODEL-1")
    model.add_equipment(Tank(dex_id="TK-1"))
    model.add_process_instrumentation_function(pif_1)
    model.add_process_instrumentation_function(pif_2)
    model.add_instrumentation_loop_function(loop)
    return model


def _generic_attribute(element, name):
    for attr in element.iter("GenericAttribute"):
        if attr.get("Name") == name:
            return attr
    raise AssertionError(f"no GenericAttribute {name!r}")


def test_pif_rename_emits_same_generic_attribute_name():
    root = ET.fromstring(to_proteus_xml(_loop_model()))
    element = _find_by_id(root, "PIF-1")
    attr = _generic_attribute(element, "ProcessInstrumentationFunctionsAssignmentClass")
    assert attr.get("Value") == "ICSA"


def test_instrumentation_loop_function_element():
    root = ET.fromstring(to_proteus_xml(_loop_model()))
    element = _find_by_id(root, "ILF-1")
    assert element.tag == "InstrumentationLoopFunction"
    assert element.get("ComponentClass") == "InstrumentationLoopFunction"
    assert element.get("ComponentClassURI") == (
        "http://sandbox.dexpi.org/rdl/InstrumentationLoopFunction"
    )
    number = _generic_attribute(element, "InstrumentationLoopFunctionNumberAssignmentClass")
    assert number.get("Value") == "LOOP-7"


def test_instrumentation_loop_function_collects_pifs_by_association():
    root = ET.fromstring(to_proteus_xml(_loop_model()))
    element = _find_by_id(root, "ILF-1")
    associations = [
        (a.get("Type"), a.get("ItemID")) for a in element.findall("Association")
    ]
    assert associations == [
        ("is a collection including", "PIF-1"),
        ("is a collection including", "PIF-2"),
    ]


def test_referenced_pif_gets_is_a_part_of_association():
    root = ET.fromstring(to_proteus_xml(_loop_model()))
    element = _find_by_id(root, "PIF-1")
    assert [
        (a.get("Type"), a.get("ItemID")) for a in element.findall("Association")
        if a.get("Type") == "is a part of"
    ] == [("is a part of", "ILF-1")]


def test_pif_gets_one_is_a_part_of_per_referencing_loop():
    pif = ProcessInstrumentationFunction(dex_id="PIF-1")
    loop_a = InstrumentationLoopFunction(
        dex_id="ILF-1", process_instrumentation_functions=[pif],
    )
    loop_b = InstrumentationLoopFunction(
        dex_id="ILF-2", process_instrumentation_functions=[pif],
    )
    model = ConceptualModel(dex_id="MODEL-1")
    model.add_process_instrumentation_function(pif)
    model.add_instrumentation_loop_function(loop_a)
    model.add_instrumentation_loop_function(loop_b)
    root = ET.fromstring(to_proteus_xml(model))
    element = _find_by_id(root, "PIF-1")
    part_of = [a.get("ItemID") for a in element.findall("Association")
               if a.get("Type") == "is a part of"]
    assert part_of == ["ILF-1", "ILF-2"]


def test_instrumentation_loop_function_is_serialized_after_equipment():
    root = ET.fromstring(to_proteus_xml(_loop_model()))
    children = list(root)
    loop_index = children.index(_find_by_id(root, "ILF-1"))
    equipment_indices = [i for i, c in enumerate(children) if c.tag == "Equipment"]
    assert equipment_indices
    assert max(equipment_indices) < loop_index
    assert loop_index == len(children) - 1


def test_process_control_function_keeps_its_own_component_class():
    model = ConceptualModel(dex_id="MODEL-1")
    model.add_process_instrumentation_function(ProcessControlFunction(dex_id="PCF-1"))
    root = ET.fromstring(to_proteus_xml(model))
    element = _find_by_id(root, "PCF-1")
    assert element.tag == "ProcessInstrumentationFunction"
    assert element.get("ComponentClass") == "ProcessControlFunction"
    assert element.get("ComponentClassURI") == (
        "http://sandbox.dexpi.org/rdl/ProcessControlFunction"
    )


@pytest.mark.skipif(shutil.which("xmllint") is None, reason="xmllint is not on PATH")
def test_instrumentation_loop_serialized_xml_validates_against_xsd(tmp_path):
    path = tmp_path / "loop.xml"
    path.write_text(to_proteus_xml(_loop_model()), encoding="utf-8")
    assert proteus_is_valid(str(path))


def _psgf_model() -> ConceptualModel:
    """An I01-like model: a PIF with a PSGF located at a flow measuring element.

    The measuring line runs from the PSGF (source) to the PIF bubble (target).
    """
    element = FlowMeasuringElement(dex_id="FME-1")
    segment = PipingNetworkSegment(dex_id="SEG-1", items=[element])
    line = PipingNetworkSystem(dex_id="LINE-1", segments=[segment])
    psgf = ProcessSignalGeneratingFunction(
        dex_id="PSGF-1", process_signal_generating_function_number="FT-101",
        sensor_type="FT", sensing_location=element,
    )
    pif = ProcessInstrumentationFunction(
        dex_id="PIF-1", process_instrumentation_function_number="101",
        process_instrumentation_functions_code="FI",
        process_signal_generating_functions=[psgf],
    )
    pif.add_signal_conveying_function(
        SignalConveyingFunction(dex_id="S-1", source=psgf, target=pif)
    )
    model = ConceptualModel(dex_id="MODEL-1")
    model.add_piping_network_system(line)
    model.add_process_instrumentation_function(pif)
    return model


def _assocs(element):
    return [(a.get("Type"), a.get("ItemID")) for a in element.findall("Association")]


def test_psgf_element_identity_and_fields():
    root = ET.fromstring(to_proteus_xml(_psgf_model()))
    element = _find_by_id(root, "PSGF-1")
    assert element.tag == "ProcessSignalGeneratingFunction"
    assert element.get("ComponentClass") == "ProcessSignalGeneratingFunction"
    assert element.get("ComponentClassURI") == (
        "http://sandbox.dexpi.org/rdl/ProcessSignalGeneratingFunction"
    )
    number = _generic_attribute(element, "ProcessSignalGeneratingFunctionNumberAssignmentClass")
    assert number.get("Value") == "FT-101"
    sensor = _generic_attribute(element, "SensorTypeAssignmentClass")
    assert sensor.get("Value") == "FT"


def test_psgf_is_located_in_sensing_location_and_location_is_mirrored():
    root = ET.fromstring(to_proteus_xml(_psgf_model()))
    assert ("is located in", "FME-1") in _assocs(_find_by_id(root, "PSGF-1"))
    element = _find_by_id(root, "FME-1")
    assert element.tag == "PipingComponent"
    assert element.get("ComponentClass") == "FlowMeasuringElement"
    assert ("is the location of", "PSGF-1") in _assocs(element)


def test_psgf_is_logical_start_of_its_signal():
    root = ET.fromstring(to_proteus_xml(_psgf_model()))
    assert _assocs(_find_by_id(root, "PSGF-1")) == [
        ("is located in", "FME-1"),
        ("is logical start of", "S-1"),
    ]


def test_pif_is_logical_end_of_signal_it_targets_not_start():
    root = ET.fromstring(to_proteus_xml(_psgf_model()))
    pif_assocs = _assocs(_find_by_id(root, "PIF-1"))
    assert ("is logical end of", "S-1") in pif_assocs
    assert ("is logical start of", "S-1") not in pif_assocs


def test_information_flow_links_psgf_start_and_pif_end():
    root = ET.fromstring(to_proteus_xml(_psgf_model()))
    flow = _find_by_id(root, "S-1")
    assert flow.tag == "InformationFlow"
    assert _assocs(flow) == [
        ("has logical start", "PSGF-1"),
        ("has logical end", "PIF-1"),
    ]


def test_pif_child_order_generic_assocs_information_flow_then_psgf():
    # C01 order: associations, InformationFlow, ActuatingFunction, PSGF.
    root = ET.fromstring(to_proteus_xml(_psgf_model()))
    pif = _find_by_id(root, "PIF-1")
    assert [child.tag for child in pif] == [
        "GenericAttributes", "Association", "InformationFlow",
        "ProcessSignalGeneratingFunction",
    ]


def test_pif_child_order_places_psgf_after_actuating_function():
    psgf = ProcessSignalGeneratingFunction(dex_id="PSGF-1")
    actuating = ActuatingFunction(dex_id="AF-1")
    pif = ProcessInstrumentationFunction(
        dex_id="PIF-1", process_instrumentation_function_number="101",
        process_signal_generating_functions=[psgf],
        actuating_functions=[actuating],
    )
    pif.add_signal_conveying_function(
        SignalConveyingFunction(dex_id="S-1", source=psgf, target=actuating)
    )
    model = ConceptualModel(dex_id="MODEL-1")
    model.add_process_instrumentation_function(pif)
    root = ET.fromstring(to_proteus_xml(model))
    tags = [child.tag for child in _find_by_id(root, "PIF-1")]
    assert tags == [
        "GenericAttributes", "InformationFlow", "ActuatingFunction",
        "ProcessSignalGeneratingFunction",
    ]


def test_nozzle_as_sensing_location_gets_is_the_location_of():
    nozzle = Nozzle(dex_id="N-1")
    tank = Tank(dex_id="T-1", nozzles=[nozzle])
    psgf = ProcessSignalGeneratingFunction(dex_id="PSGF-1", sensing_location=nozzle)
    pif = ProcessInstrumentationFunction(
        dex_id="PIF-1", process_signal_generating_functions=[psgf],
    )
    model = ConceptualModel(dex_id="MODEL-1")
    model.add_equipment(tank)
    model.add_process_instrumentation_function(pif)
    root = ET.fromstring(to_proteus_xml(model))
    assert ("is located in", "N-1") in _assocs(_find_by_id(root, "PSGF-1"))
    assert _assocs(_find_by_id(root, "N-1")) == [("is the location of", "PSGF-1")]


def test_segment_as_sensing_location_gets_is_the_location_of():
    segment = PipingNetworkSegment(dex_id="SEG-1")
    line = PipingNetworkSystem(dex_id="LINE-1", segments=[segment])
    psgf = ProcessSignalGeneratingFunction(dex_id="PSGF-1", sensing_location=segment)
    pif = ProcessInstrumentationFunction(
        dex_id="PIF-1", process_signal_generating_functions=[psgf],
    )
    model = ConceptualModel(dex_id="MODEL-1")
    model.add_piping_network_system(line)
    model.add_process_instrumentation_function(pif)
    root = ET.fromstring(to_proteus_xml(model))
    assert ("is located in", "SEG-1") in _assocs(_find_by_id(root, "PSGF-1"))
    assert ("is the location of", "PSGF-1") in _assocs(_find_by_id(root, "SEG-1"))


def test_signal_from_pif_source_keeps_is_logical_start_of():
    pif_source = ProcessInstrumentationFunction(dex_id="PIF-1")
    pif_target = ProcessInstrumentationFunction(dex_id="PIF-2")
    pif_source.add_signal_conveying_function(
        SignalConveyingFunction(dex_id="S-1", source=pif_source, target=pif_target)
    )
    model = ConceptualModel(dex_id="MODEL-1")
    model.add_process_instrumentation_function(pif_source)
    model.add_process_instrumentation_function(pif_target)
    root = ET.fromstring(to_proteus_xml(model))
    assert _assocs(_find_by_id(root, "PIF-1")) == [("is logical start of", "S-1")]


def test_signal_composed_under_other_pif_gives_logical_end_on_target():
    # The signal is composed under PIF-1 but targets PIF-2: PIF-2 must still
    # mirror it, otherwise the InformationFlow points at a dangling end.
    pif_source = ProcessInstrumentationFunction(dex_id="PIF-1")
    pif_target = ProcessInstrumentationFunction(dex_id="PIF-2")
    pif_source.add_signal_conveying_function(
        SignalConveyingFunction(dex_id="S-1", source=pif_source, target=pif_target)
    )
    model = ConceptualModel(dex_id="MODEL-1")
    model.add_process_instrumentation_function(pif_source)
    model.add_process_instrumentation_function(pif_target)
    root = ET.fromstring(to_proteus_xml(model))
    assert _assocs(_find_by_id(root, "PIF-2")) == [("is logical end of", "S-1")]
    assert _assocs(_find_by_id(root, "S-1")) == [
        ("has logical start", "PIF-1"),
        ("has logical end", "PIF-2"),
    ]


def test_signal_with_same_pif_as_source_and_target_emits_start_then_end():
    pif = ProcessInstrumentationFunction(dex_id="PIF-1")
    pif.add_signal_conveying_function(
        SignalConveyingFunction(dex_id="S-1", source=pif, target=pif)
    )
    model = ConceptualModel(dex_id="MODEL-1")
    model.add_process_instrumentation_function(pif)
    root = ET.fromstring(to_proteus_xml(model))
    assert _assocs(_find_by_id(root, "PIF-1")) == [
        ("is logical start of", "S-1"),
        ("is logical end of", "S-1"),
    ]


def test_psgf_without_sensing_location_has_no_located_in():
    psgf = ProcessSignalGeneratingFunction(dex_id="PSGF-1")
    pif = ProcessInstrumentationFunction(
        dex_id="PIF-1", process_signal_generating_functions=[psgf],
    )
    model = ConceptualModel(dex_id="MODEL-1")
    model.add_process_instrumentation_function(pif)
    root = ET.fromstring(to_proteus_xml(model))
    assert _assocs(_find_by_id(root, "PSGF-1")) == []


@pytest.mark.skipif(shutil.which("xmllint") is None, reason="xmllint is not on PATH")
def test_psgf_serialized_xml_validates_against_xsd(tmp_path):
    path = tmp_path / "psgf.xml"
    path.write_text(to_proteus_xml(_psgf_model()), encoding="utf-8")
    assert proteus_is_valid(str(path))


@pytest.mark.skipif(shutil.which("xmllint") is None, reason="xmllint is not on PATH")
def test_psgf_nozzle_and_segment_serialized_xml_validates_against_xsd(tmp_path):
    nozzle = Nozzle(dex_id="N-1")
    tank = Tank(dex_id="T-1", nozzles=[nozzle])
    segment = PipingNetworkSegment(dex_id="SEG-1")
    line = PipingNetworkSystem(dex_id="LINE-1", segments=[segment])
    pif = ProcessInstrumentationFunction(
        dex_id="PIF-1",
        process_signal_generating_functions=[
            ProcessSignalGeneratingFunction(dex_id="PSGF-1", sensing_location=nozzle),
            ProcessSignalGeneratingFunction(dex_id="PSGF-2", sensing_location=segment),
        ],
    )
    model = ConceptualModel(dex_id="MODEL-1")
    model.add_equipment(tank)
    model.add_piping_network_system(line)
    model.add_process_instrumentation_function(pif)
    path = tmp_path / "sensing.xml"
    path.write_text(to_proteus_xml(model), encoding="utf-8")
    assert proteus_is_valid(str(path))


# --- PipeOffPageConnectorReferenceByNumber fields ---

def _opc_model(**reference_kwargs) -> ConceptualModel:
    from dexpigen.piping import (  # noqa: PLC0415
        FlowInPipeOffPageConnector,
        PipeOffPageConnectorReferenceByNumber,
    )

    connector = FlowInPipeOffPageConnector(dex_id="OPC-1")
    connector.add_connector_reference(
        PipeOffPageConnectorReferenceByNumber(dex_id="OPCREF-1", **reference_kwargs)
    )
    segment = PipingNetworkSegment(dex_id="SEG-1")
    segment.add_item(connector)
    line = PipingNetworkSystem(dex_id="LINE-1")
    line.add_segment(segment)
    return ConceptualModel(dex_id="MODEL-1").add_piping_network_system(line)


def test_reference_by_number_fields_are_serialized():
    model = _opc_model(referenced_connector_number="123", referenced_drawing_number="D-2")
    element = _find_by_id(ET.fromstring(to_proteus_xml(model)), "OPCREF-1")
    assert element.tag == "PipeOffPageConnectorReference"
    names = [a.get("Name") for a in element.iter("GenericAttribute")]
    assert names == [
        "ReferencedConnectorNumberAssignmentClass",
        "ReferencedDrawingNumberAssignmentClass",
    ]
    values = [a.get("Value") for a in element.iter("GenericAttribute")]
    assert values == ["123", "D-2"]


@pytest.mark.skipif(shutil.which("xmllint") is None, reason="xmllint is not on PATH")
def test_reference_by_number_serialized_xml_validates_against_xsd(tmp_path):
    path = tmp_path / "opc.xml"
    path.write_text(to_proteus_xml(_opc_model(referenced_connector_number="123")), encoding="utf-8")
    assert proteus_is_valid(str(path))


# --- ActuatingFunction location and PipeOffPageConnectorObjectReference ---

def _actuating_location_model() -> ConceptualModel:
    segment = PipingNetworkSegment(dex_id="SEG-1")
    line = PipingNetworkSystem(dex_id="LINE-1", segments=[segment])
    function = ActuatingFunction(dex_id="AF-1", actuating_location=segment)
    pif = ProcessInstrumentationFunction(dex_id="PIF-1", actuating_functions=[function])
    model = ConceptualModel(dex_id="MODEL-1")
    model.add_piping_network_system(line)
    model.add_process_instrumentation_function(pif)
    return model


def test_actuating_location_is_located_in_and_mirrored_on_segment():
    root = ET.fromstring(to_proteus_xml(_actuating_location_model()))
    assert ("is located in", "SEG-1") in _assocs(_find_by_id(root, "AF-1"))
    assert ("is the location of", "AF-1") in _assocs(_find_by_id(root, "SEG-1"))


def test_actuating_function_without_location_has_no_located_in():
    function = ActuatingFunction(dex_id="AF-1")
    pif = ProcessInstrumentationFunction(dex_id="PIF-1", actuating_functions=[function])
    model = ConceptualModel(dex_id="MODEL-1").add_process_instrumentation_function(pif)
    element = _find_by_id(ET.fromstring(to_proteus_xml(model)), "AF-1")
    assert all(kind != "is located in" for kind, _ in _assocs(element))


@pytest.mark.skipif(shutil.which("xmllint") is None, reason="xmllint is not on PATH")
def test_actuating_location_serialized_xml_validates_against_xsd(tmp_path):
    path = tmp_path / "actuating_location.xml"
    path.write_text(to_proteus_xml(_actuating_location_model()), encoding="utf-8")
    assert proteus_is_valid(str(path))


def _object_reference_model() -> ConceptualModel:
    from dexpigen.piping import (  # noqa: PLC0415
        FlowInPipeOffPageConnector,
        FlowOutPipeOffPageConnector,
        PipeOffPageConnectorObjectReference,
    )

    outgoing = FlowOutPipeOffPageConnector(dex_id="OPC-OUT")
    incoming = FlowInPipeOffPageConnector(dex_id="OPC-IN")
    incoming.add_connector_reference(
        PipeOffPageConnectorObjectReference(dex_id="OPCREF-1", referenced_connector=outgoing)
    )
    first = PipingNetworkSegment(dex_id="SEG-1")
    first.add_item(outgoing)
    second = PipingNetworkSegment(dex_id="SEG-2")
    second.add_item(incoming)
    line = PipingNetworkSystem(dex_id="LINE-1")
    line.add_segment(first)
    line.add_segment(second)
    return ConceptualModel(dex_id="MODEL-1").add_piping_network_system(line)


def test_object_reference_refers_to_connector_and_is_mirrored():
    root = ET.fromstring(to_proteus_xml(_object_reference_model()))
    reference = _find_by_id(root, "OPCREF-1")
    assert reference.tag == "PipeOffPageConnectorReference"
    assert ("refers to", "OPC-OUT") in _assocs(reference)
    assert ("is referenced by", "OPCREF-1") in _assocs(_find_by_id(root, "OPC-OUT"))


@pytest.mark.skipif(shutil.which("xmllint") is None, reason="xmllint is not on PATH")
def test_object_reference_serialized_xml_validates_against_xsd(tmp_path):
    path = tmp_path / "opc_object_reference.xml"
    path.write_text(to_proteus_xml(_object_reference_model()), encoding="utf-8")
    assert proteus_is_valid(str(path))


def _signal_connector_model() -> ConceptualModel:
    from dexpigen.instrumentation import (  # noqa: PLC0415
        FlowInSignalOffPageConnector,
        FlowOutSignalOffPageConnector,
    )

    incoming = FlowInSignalOffPageConnector(dex_id="SOPC-IN")
    outgoing = FlowOutSignalOffPageConnector(dex_id="SOPC-OUT")
    pif = ProcessInstrumentationFunction(dex_id="PIF-1")
    pif.add_signal_connector(incoming)
    pif.add_signal_connector(outgoing)
    pif.add_signal_conveying_function(
        SignalConveyingFunction(dex_id="SIG-IN", source=incoming, target=pif)
    )
    pif.add_signal_conveying_function(
        SignalConveyingFunction(dex_id="SIG-OUT", source=pif, target=outgoing)
    )
    return ConceptualModel(dex_id="MODEL-1").add_process_instrumentation_function(pif)


def test_signal_connector_is_a_signal_off_page_connector_in_its_pif():
    root = ET.fromstring(to_proteus_xml(_signal_connector_model()))
    pif = _find_by_id(root, "PIF-1")
    children = [c for c in pif if c.tag == "SignalOffPageConnector"]
    assert [c.get("ID") for c in children] == ["SOPC-IN", "SOPC-OUT"]
    assert children[0].get("ComponentClass") == "FlowInSignalOffPageConnector"
    assert ("is logical start of", "SIG-IN") in _assocs(children[0])
    assert ("is logical end of", "SIG-OUT") in _assocs(children[1])


@pytest.mark.skipif(shutil.which("xmllint") is None, reason="xmllint is not on PATH")
def test_signal_connector_serialized_xml_validates_against_xsd(tmp_path):
    path = tmp_path / "signal_connector.xml"
    path.write_text(to_proteus_xml(_signal_connector_model()), encoding="utf-8")
    assert proteus_is_valid(str(path))
