"""Tests for the piping module (systems, segments, connections, components)."""

import pytest
from pydantic import ValidationError

import dexpigen.piping as piping
from dexpigen.enumerations import OnHoldClassification
from dexpigen.equipment import Nozzle
from dexpigen.piping import (
    BallValve,
    ButterflyValve,
    CheckValve,
    Flange,
    FlowInPipeOffPageConnector,
    FlowOutPipeOffPageConnector,
    GateValve,
    GlobeValve,
    LineBlind,
    NeedleValve,
    OperatedValve,
    Pipe,
    PipeFitting,
    PipeOffPageConnector,
    PipeOffPageConnectorReference,
    PipeOffPageConnectorReferenceByNumber,
    PipeReducer,
    PipeTee,
    PipingComponent,
    PipingConnection,
    PipingNetworkSegment,
    PipingNetworkSegmentItem,
    PipingNetworkSystem,
    PipingNode,
    PipingNodeOwner,
    PipingSourceItem,
    PipingTargetItem,
    SafetyValveOrFitting,
)


def test_connection_is_abstract():
    with pytest.raises(ValidationError):
        PipingConnection(dex_id="C-1")


def test_roles_are_abstract():
    for cls in (
        PipingNodeOwner,
        PipingSourceItem,
        PipingTargetItem,
        PipingNetworkSegmentItem,
    ):
        with pytest.raises(ValidationError):
            cls(dex_id="x")


def test_pipe_is_concrete():
    pipe = Pipe(dex_id="pipe-1")
    assert isinstance(pipe, PipingConnection)
    assert isinstance(pipe.id, str)


def test_system_composes_segments():
    segment = PipingNetworkSegment(dex_id="seg-1")
    system = PipingNetworkSystem(dex_id="S-1", segments=[segment])
    assert system.segments[0] is segment


def test_add_segment_composes_under_system():
    system = PipingNetworkSystem(dex_id="S-1")
    segment = PipingNetworkSegment(dex_id="seg-1")
    assert system.add_segment(segment) is system
    assert segment in system.segments


def test_segment_cannot_have_two_owners():
    sys_a = PipingNetworkSystem(dex_id="S-1")
    sys_b = PipingNetworkSystem(dex_id="S-2")
    segment = PipingNetworkSegment(dex_id="seg-1")
    sys_a.add_segment(segment)
    with pytest.raises(ValueError):
        sys_b.add_segment(segment)


def test_connection_cannot_have_two_owners():
    seg_a = PipingNetworkSegment(dex_id="seg-1")
    seg_b = PipingNetworkSegment(dex_id="seg-2")
    pipe = Pipe(dex_id="pipe-1")
    seg_a.add_connection(pipe)
    with pytest.raises(ValueError):
        seg_b.add_connection(pipe)


def test_line_number_is_optional():
    system = PipingNetworkSystem(dex_id="S-1")
    assert system.line_number is None
    named = PipingNetworkSystem(dex_id="S-2", line_number="100-P-1")
    assert named.line_number == "100-P-1"


def test_segment_fluid_and_piping_class_codes_are_optional():
    segment = PipingNetworkSegment(dex_id="seg-1")
    assert segment.fluid_code is None
    assert segment.piping_class_code is None
    named = PipingNetworkSegment(
        dex_id="seg-2", fluid_code="MNb", piping_class_code="75HB13"
    )
    assert named.fluid_code == "MNb"
    assert named.piping_class_code == "75HB13"


def test_nozzle_is_a_valid_piping_source_and_target():
    nozzle = Nozzle(dex_id="N-1")
    source_pipe = Pipe(dex_id="p-1", source_item=nozzle)
    assert source_pipe.source_item is nozzle
    target_pipe = Pipe(dex_id="p-2", target_item=nozzle)
    assert target_pipe.target_item is nozzle


def test_connection_node_must_belong_to_its_item():
    nozzle = Nozzle(dex_id="N-1")
    node = PipingNode(dex_id="node-1")
    nozzle.add_node(node)
    Pipe(dex_id="p-1", source_item=nozzle, source_node=node)


def test_connection_node_rejects_foreign_node():
    nozzle = Nozzle(dex_id="N-1")
    node = PipingNode(dex_id="node-1")  # not added to the nozzle
    with pytest.raises(ValidationError):
        Pipe(dex_id="p-1", source_item=nozzle, source_node=node)


def test_connection_node_without_item_is_rejected():
    node = PipingNode(dex_id="node-1")
    with pytest.raises(ValidationError):
        Pipe(dex_id="p-1", source_node=node)


def test_node_cannot_have_two_owners():
    nozzle_a = Nozzle(dex_id="N-1")
    nozzle_b = Nozzle(dex_id="N-2")
    node = PipingNode(dex_id="node-1")
    nozzle_a.add_node(node)
    with pytest.raises(ValueError):
        nozzle_b.add_node(node)


# --- Piping components, valves, fittings, and off-page connectors ---


def test_piping_component_is_abstract():
    with pytest.raises(ValidationError):
        PipingComponent(dex_id="C-1")


def test_pipe_fitting_is_abstract():
    with pytest.raises(ValidationError):
        PipeFitting(dex_id="F-1")


def test_pipe_off_page_connector_is_abstract():
    with pytest.raises(ValidationError):
        PipeOffPageConnector(dex_id="OPC-1")


def test_valve_family_roots_are_concrete():
    for cls in (OperatedValve, CheckValve, SafetyValveOrFitting):
        valve = cls(dex_id="V-1")
        assert isinstance(valve, PipingComponent)


def test_valve_leaves_inherit_operated_valve():
    for cls in (BallValve, GlobeValve, ButterflyValve, NeedleValve, GateValve):
        assert issubclass(cls, OperatedValve)
        assert issubclass(cls, PipingComponent)


def test_valve_extraction_names_map_to_concrete_classes():
    for name in (
        "BallValve",
        "GlobeValve",
        "ButterflyValve",
        "NeedleValve",
        "GateValve",
        "CheckValve",
    ):
        assert hasattr(piping, name)


def test_pipe_tee_is_concrete_pipe_fitting():
    tee = PipeTee(dex_id="T-1")
    assert isinstance(tee, PipeFitting)
    assert isinstance(tee, PipingComponent)
    assert tee.nodes == []
    assert tee.flow_in_index is None
    assert tee.flow_out_index is None


def test_pipe_tee_identity():
    assert PipeTee.component_class == "PipeTee"
    assert PipeTee.component_class_uri == "http://data.posccaesar.org/rdl/RDS427724"


def test_pipe_tee_accepts_three_nodes_without_validator():
    tee = PipeTee(dex_id="T-1")
    for i in range(3):
        tee.add_node(PipingNode(dex_id=f"node-{i}"))
    assert len(tee.nodes) == 3
    # No node-count invariant: a tee with an unusual node count is still accepted.
    PipeTee(dex_id="T-2", nodes=[PipingNode(dex_id="only-one")])


def test_fittings_are_pipe_fitting_descendants():
    for cls in (Flange, PipeReducer, LineBlind):
        assert issubclass(cls, PipeFitting)
        assert issubclass(cls, PipingComponent)


def test_flow_in_connector_is_source_not_target():
    assert issubclass(FlowInPipeOffPageConnector, PipingSourceItem)
    assert not issubclass(FlowInPipeOffPageConnector, PipingTargetItem)


def test_flow_out_connector_is_target_not_source():
    assert issubclass(FlowOutPipeOffPageConnector, PipingTargetItem)
    assert not issubclass(FlowOutPipeOffPageConnector, PipingSourceItem)


def test_off_page_connector_is_segment_item():
    assert issubclass(FlowInPipeOffPageConnector, PipingNetworkSegmentItem)
    assert issubclass(FlowOutPipeOffPageConnector, PipingNetworkSegmentItem)


def test_component_is_usable_as_source_and_target():
    valve = OperatedValve(dex_id="V-1")
    assert Pipe(dex_id="p-1", source_item=valve).source_item is valve
    assert Pipe(dex_id="p-2", target_item=valve).target_item is valve


def test_fitting_is_usable_as_source_and_target():
    flange = Flange(dex_id="F-1")
    assert Pipe(dex_id="p-1", source_item=flange).source_item is flange
    assert Pipe(dex_id="p-2", target_item=flange).target_item is flange


def test_flow_in_connector_usable_as_source():
    opc = FlowInPipeOffPageConnector(dex_id="OPC-1")
    assert Pipe(dex_id="p-1", source_item=opc).source_item is opc


def test_flow_in_connector_rejected_as_target():
    opc = FlowInPipeOffPageConnector(dex_id="OPC-1")
    with pytest.raises(ValidationError):
        Pipe(dex_id="p-1", target_item=opc)


def test_flow_out_connector_rejected_as_source():
    opc = FlowOutPipeOffPageConnector(dex_id="OPC-1")
    with pytest.raises(ValidationError):
        Pipe(dex_id="p-1", source_item=opc)


def test_component_composes_in_segment_items():
    segment = PipingNetworkSegment(dex_id="seg-1")
    valve = OperatedValve(dex_id="V-1")
    segment.add_item(valve)
    assert valve in segment.items


def test_component_cannot_have_two_segment_owners():
    seg_a = PipingNetworkSegment(dex_id="seg-1")
    seg_b = PipingNetworkSegment(dex_id="seg-2")
    valve = OperatedValve(dex_id="V-1")
    seg_a.add_item(valve)
    with pytest.raises(ValueError):
        seg_b.add_item(valve)


def test_component_owns_nodes():
    valve = OperatedValve(dex_id="V-1")
    node = PipingNode(dex_id="node-1")
    valve.add_node(node)
    Pipe(dex_id="p-1", source_item=valve, source_node=node)


def test_piping_component_fields_are_optional():
    valve = OperatedValve(dex_id="V-1")
    assert valve.fluid_code is None
    assert valve.on_hold is None
    assert valve.piping_class_artefact is None
    assert valve.pressure_test_circuit_number is None


def test_on_hold_enum_restricts_values():
    valve = OperatedValve(dex_id="V-1", on_hold=OnHoldClassification.ON_HOLD)
    assert valve.on_hold == OnHoldClassification.ON_HOLD
    with pytest.raises(ValidationError):
        valve.on_hold = "not-an-on-hold-value"


def test_generic_valve_class_is_not_defined():
    assert not hasattr(piping, "Valve")


def test_flame_arrestor_and_rupture_disc_are_excluded():
    assert not hasattr(piping, "FlameArrestor")
    assert not hasattr(piping, "RuptureDisc")


def test_piping_component_name_and_number_are_optional():
    valve = OperatedValve(dex_id="V-1")
    assert valve.piping_component_name is None
    assert valve.piping_component_number is None
    named = OperatedValve(
        dex_id="V-2", piping_component_name="HV", piping_component_number="02"
    )
    assert named.piping_component_name == "HV"
    assert named.piping_component_number == "02"


def test_off_page_connector_composes_reference():
    opc = FlowInPipeOffPageConnector(dex_id="OPC-1")
    reference = PipeOffPageConnectorReferenceByNumber(
        dex_id="REF-1", referenced_connector_number="123"
    )
    opc.add_connector_reference(reference)
    assert opc.connector_reference is reference
    assert reference.referenced_connector_number == "123"


def test_connector_reference_cannot_have_two_owners():
    opc_a = FlowInPipeOffPageConnector(dex_id="OPC-1")
    opc_b = FlowInPipeOffPageConnector(dex_id="OPC-2")
    reference = PipeOffPageConnectorReferenceByNumber(dex_id="REF-1")
    opc_a.add_connector_reference(reference)
    with pytest.raises(ValueError):
        opc_b.add_connector_reference(reference)


def test_pipe_off_page_connector_reference_is_abstract():
    with pytest.raises(ValidationError):
        PipeOffPageConnectorReference(dex_id="R-1")


def test_sensing_location_is_abstract():
    with pytest.raises(ValidationError):
        piping.SensingLocation(dex_id="SL-1")


def test_sensing_location_roles_are_inherited():
    assert issubclass(Nozzle, piping.SensingLocation)
    assert issubclass(piping.PipingComponent, piping.SensingLocation)
    assert issubclass(piping.PipingNetworkSegment, piping.SensingLocation)
    assert issubclass(piping.FlowMeasuringElement, piping.SensingLocation)
    assert issubclass(piping.FlowMeasuringElement, piping.PipingComponent)


def test_flow_measuring_element_is_concrete_piping_component():
    element = piping.FlowMeasuringElement(dex_id="FME-1")
    assert element.dex_id == "FME-1"
    assert element.component_class == "FlowMeasuringElement"
    assert (
        element.component_class_uri
        == "http://sandbox.dexpi.org/rdl/FlowMeasuringElement"
    )
    assert element.piping_component_number is None


def test_sensing_location_mro_keeps_piping_component_roles():
    element = piping.FlowMeasuringElement(dex_id="FME-1")
    assert isinstance(element, piping.PipingSourceItem)
    assert isinstance(element, piping.PipingTargetItem)
    assert isinstance(element, piping.PipingNetworkSegmentItem)
