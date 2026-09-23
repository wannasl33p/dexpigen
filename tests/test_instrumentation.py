"""Tests for the instrumentation module (functions, actuating system, signals)."""

import pytest
from pydantic import ValidationError

from dexpigen.enumerations import FailActionClassification
from dexpigen.equipment import Nozzle, Pump
from dexpigen.instrumentation import (
    ActuatingFunction,
    ActuatingSystem,
    ControlledActuator,
    CustomAttribute,
    FlowInSignalOffPageConnector,
    FlowOutSignalOffPageConnector,
    OperatedValveReference,
    Positioner,
    ProcessControlFunction,
    ProcessInstrumentationFunction,
    SignalConveyingFunction,
    SignalConveyingFunctionSource,
    SignalConveyingFunctionTarget,
    SignalOffPageConnector,
)
from dexpigen.piping import CheckValve, OperatedValve, PipingNetworkSegment


def test_signal_roles_are_abstract():
    for cls in (
        SignalConveyingFunctionSource,
        SignalConveyingFunctionTarget,
        SignalOffPageConnector,
    ):
        with pytest.raises(ValidationError):
            cls(dex_id="x")


def test_process_instrumentation_function_is_concrete():
    pif = ProcessInstrumentationFunction(dex_id="PIF-1")
    assert pif.dex_id == "PIF-1"
    assert pif.process_instrumentation_function_number is None


def test_process_instrumentation_function_tag_fields():
    pif = ProcessInstrumentationFunction(
        dex_id="PIF-1",
        process_instrumentation_function_number="101",
        process_instrumentation_function_category="F",
        process_instrumentation_function_modifier="I",
        process_instrumentation_functions="AL",
    )
    assert pif.process_instrumentation_function_number == "101"
    assert pif.process_instrumentation_function_category == "F"
    assert pif.process_instrumentation_function_modifier == "I"
    assert pif.process_instrumentation_functions == "AL"


def test_custom_attributes_bag():
    pif = ProcessInstrumentationFunction(
        dex_id="PIF-1",
        custom_attributes=[CustomAttribute(name="Location", value="rack 1")],
    )
    assert pif.custom_attributes[0].name == "Location"
    assert pif.custom_attributes[0].value == "rack 1"


def test_process_control_function_is_subtype():
    pcf = ProcessControlFunction(dex_id="PCF-1")
    assert isinstance(pcf, ProcessInstrumentationFunction)


def test_instrument_is_signal_source_and_target():
    assert issubclass(
        ProcessInstrumentationFunction, SignalConveyingFunctionSource
    )
    assert issubclass(ProcessInstrumentationFunction, SignalConveyingFunctionTarget)


def test_actuating_function_is_signal_source_and_target():
    assert issubclass(ActuatingFunction, SignalConveyingFunctionSource)
    assert issubclass(ActuatingFunction, SignalConveyingFunctionTarget)


def test_actuating_system_composes_children():
    actuator = ControlledActuator(dex_id="CA-1")
    reference = OperatedValveReference(dex_id="OVR-1")
    positioner = Positioner(dex_id="POS-1")
    system = ActuatingSystem(
        dex_id="AS-1",
        controlled_actuator=actuator,
        operated_valve_reference=reference,
        positioner=positioner,
    )
    assert system.controlled_actuator is actuator
    assert system.operated_valve_reference is reference
    assert system.positioner is positioner


def test_actuating_system_child_cannot_have_two_owners():
    actuator = ControlledActuator(dex_id="CA-1")
    ActuatingSystem(dex_id="AS-1", controlled_actuator=actuator)
    with pytest.raises(ValidationError):
        ActuatingSystem(dex_id="AS-2", controlled_actuator=actuator)


def test_operated_valve_reference_targets_operated_valve():
    valve = OperatedValve(dex_id="CV-1")
    reference = OperatedValveReference(dex_id="OVR-1", valve=valve)
    assert reference.valve is valve


def test_operated_valve_reference_rejects_check_valve():
    check = CheckValve(dex_id="CK-1")
    with pytest.raises(ValidationError):
        OperatedValveReference(dex_id="OVR-1", valve=check)


def test_actuating_function_references_system_and_segment():
    system = ActuatingSystem(dex_id="AS-1")
    segment = PipingNetworkSegment(dex_id="seg-1")
    function = ActuatingFunction(
        dex_id="AF-1", systems=system, actuating_location=segment
    )
    assert function.systems is system
    assert function.actuating_location is segment


def test_control_valve_assembly_is_four_related_objects():
    valve = OperatedValve(dex_id="CV-1")
    system = ActuatingSystem(
        dex_id="AS-1",
        controlled_actuator=ControlledActuator(dex_id="CA-1"),
        operated_valve_reference=OperatedValveReference(dex_id="OVR-1", valve=valve),
    )
    segment = PipingNetworkSegment(dex_id="seg-1")
    function = ActuatingFunction(
        dex_id="AF-1", systems=system, actuating_location=segment
    )
    assert system.operated_valve_reference.valve is valve
    assert function.systems is system


def test_signal_connects_functions():
    pif = ProcessInstrumentationFunction(dex_id="PIF-1")
    function = ActuatingFunction(dex_id="AF-1")
    signal = SignalConveyingFunction(dex_id="S-1", source=pif, target=function)
    assert signal.source is pif
    assert signal.target is function


def test_signal_rejects_equipment_source():
    pump = Pump(dex_id="P-1")
    with pytest.raises(ValidationError):
        SignalConveyingFunction(dex_id="S-1", source=pump)


def test_signal_rejects_nozzle_target():
    nozzle = Nozzle(dex_id="N-1")
    with pytest.raises(ValidationError):
        SignalConveyingFunction(dex_id="S-1", target=nozzle)


def test_dangling_signal_is_valid():
    signal = SignalConveyingFunction(dex_id="S-1")
    assert signal.source is None
    assert signal.target is None


def test_flow_in_signal_opc_is_source_not_target():
    assert issubclass(FlowInSignalOffPageConnector, SignalConveyingFunctionSource)
    assert not issubclass(
        FlowInSignalOffPageConnector, SignalConveyingFunctionTarget
    )


def test_flow_out_signal_opc_is_target_not_source():
    assert issubclass(FlowOutSignalOffPageConnector, SignalConveyingFunctionTarget)
    assert not issubclass(
        FlowOutSignalOffPageConnector, SignalConveyingFunctionSource
    )


def test_signal_opc_usable_as_signal_endpoint():
    source = FlowInSignalOffPageConnector(dex_id="OPC-1")
    signal = SignalConveyingFunction(dex_id="S-1", source=source)
    assert signal.source is source


def test_same_object_referenced_not_cloned():
    pif = ProcessInstrumentationFunction(dex_id="PIF-1")
    signal_a = SignalConveyingFunction(dex_id="S-1", source=pif)
    signal_b = SignalConveyingFunction(dex_id="S-2", target=pif)
    assert signal_a.source is pif
    assert signal_b.target is pif


def test_fail_action_enum_restricts_values():
    actuator = ControlledActuator(
        dex_id="CA-1", fail_action=FailActionClassification.FAIL_OPEN
    )
    assert actuator.fail_action == FailActionClassification.FAIL_OPEN
    with pytest.raises(ValidationError):
        actuator.fail_action = "not-a-fail-action"


def test_actuating_system_add_controlled_actuator():
    system = ActuatingSystem(dex_id="AS-1")
    actuator = ControlledActuator(dex_id="CA-1")
    assert system.add_controlled_actuator(actuator) is system
    assert system.controlled_actuator is actuator


def test_actuating_system_add_reference_and_positioner():
    system = ActuatingSystem(dex_id="AS-1")
    reference = OperatedValveReference(dex_id="OVR-1")
    positioner = Positioner(dex_id="POS-1")
    system.add_operated_valve_reference(reference)
    system.add_positioner(positioner)
    assert system.operated_valve_reference is reference
    assert system.positioner is positioner


def test_actuating_system_add_rejects_cross_owner():
    actuator = ControlledActuator(dex_id="CA-1")
    system_a = ActuatingSystem(dex_id="AS-1")
    system_b = ActuatingSystem(dex_id="AS-2")
    system_a.add_controlled_actuator(actuator)
    with pytest.raises(ValueError):
        system_b.add_controlled_actuator(actuator)


def test_add_custom_attribute():
    pif = ProcessInstrumentationFunction(dex_id="PIF-1")
    attribute = CustomAttribute(name="Location", value="rack 1")
    assert pif.add_custom_attribute(attribute) is pif
    assert attribute in pif.custom_attributes


def test_pif_composes_signal_and_actuating_functions():
    pif = ProcessInstrumentationFunction(dex_id="PIF-1")
    signal = SignalConveyingFunction(dex_id="S-1")
    function = ActuatingFunction(dex_id="AF-1")
    pif.add_signal_conveying_function(signal)
    pif.add_actuating_function(function)
    assert signal in pif.signal_conveying_functions
    assert function in pif.actuating_functions


def test_signal_cannot_have_two_owners():
    pif_a = ProcessInstrumentationFunction(dex_id="PIF-1")
    pif_b = ProcessInstrumentationFunction(dex_id="PIF-2")
    signal = SignalConveyingFunction(dex_id="S-1")
    pif_a.add_signal_conveying_function(signal)
    with pytest.raises(ValueError):
        pif_b.add_signal_conveying_function(signal)


def test_actuating_function_cannot_have_two_owners():
    pif_a = ProcessInstrumentationFunction(dex_id="PIF-1")
    pif_b = ProcessInstrumentationFunction(dex_id="PIF-2")
    function = ActuatingFunction(dex_id="AF-1")
    pif_a.add_actuating_function(function)
    with pytest.raises(ValueError):
        pif_b.add_actuating_function(function)
