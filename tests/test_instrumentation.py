"""Tests for the instrumentation module (functions, actuating system, signals)."""

import pytest
from pydantic import ValidationError

from dexpigen.enumerations import FailActionClassification
from dexpigen.equipment import Chamber, Nozzle, Pump
from dexpigen.instrumentation import (
    ActuatingFunction,
    ActuatingSystem,
    ControlledActuator,
    CustomAttribute,
    FlowInSignalOffPageConnector,
    FlowOutSignalOffPageConnector,
    InstrumentationLoopFunction,
    OperatedValveReference,
    Positioner,
    ProcessControlFunction,
    ProcessInstrumentationFunction,
    ProcessSignalGeneratingFunction,
    SignalConveyingFunction,
    SignalConveyingFunctionSource,
    SignalConveyingFunctionTarget,
    SignalOffPageConnector,
)
from dexpigen.piping import (
    CheckValve,
    FlowMeasuringElement,
    OperatedValve,
    PipingNetworkSegment,
)


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
        process_instrumentation_functions_code="AL",
    )
    assert pif.process_instrumentation_function_number == "101"
    assert pif.process_instrumentation_function_category == "F"
    assert pif.process_instrumentation_function_modifier == "I"
    assert pif.process_instrumentation_functions_code == "AL"


def test_pif_old_process_instrumentation_functions_keyword_raises():
    # The v0.1 str field was renamed to ``process_instrumentation_functions_code``.
    # The old keyword must fail loudly instead of being dropped by ``extra=ignore``.
    with pytest.raises(ValueError, match="process_instrumentation_functions_code"):
        ProcessInstrumentationFunction(
            dex_id="PIF-1", process_instrumentation_functions="AL",
        )


def test_control_function_old_process_instrumentation_functions_keyword_raises():
    with pytest.raises(ValueError, match="process_instrumentation_functions_code"):
        ProcessControlFunction(
            dex_id="PCF-1", process_instrumentation_functions="AL",
        )


def test_instrumentation_loop_function_identity():
    assert InstrumentationLoopFunction.component_class == "InstrumentationLoopFunction"
    assert (
        InstrumentationLoopFunction.component_class_uri
        == "http://sandbox.dexpi.org/rdl/InstrumentationLoopFunction"
    )
    loop = InstrumentationLoopFunction(dex_id="ILF-1")
    assert loop.component_class == "InstrumentationLoopFunction"
    assert not hasattr(loop, "tag_name")


def test_instrumentation_loop_function_defaults():
    loop = InstrumentationLoopFunction(dex_id="ILF-1")
    assert loop.instrumentation_loop_function_number is None
    assert loop.process_instrumentation_functions == []


def test_instrumentation_loop_function_references_pifs():
    pif_1 = ProcessInstrumentationFunction(dex_id="PIF-1")
    pif_2 = ProcessInstrumentationFunction(dex_id="PIF-2")
    loop = InstrumentationLoopFunction(
        dex_id="ILF-1",
        instrumentation_loop_function_number="LOOP-7",
        process_instrumentation_functions=[pif_1, pif_2],
    )
    assert loop.instrumentation_loop_function_number == "LOOP-7"
    assert loop.process_instrumentation_functions[0] is pif_1
    assert loop.process_instrumentation_functions[1] is pif_2


def test_instrumentation_loop_function_does_not_take_ownership():
    pif = ProcessInstrumentationFunction(dex_id="PIF-1")
    loop_a = InstrumentationLoopFunction(
        dex_id="ILF-1", process_instrumentation_functions=[pif],
    )
    loop_b = InstrumentationLoopFunction(
        dex_id="ILF-2", process_instrumentation_functions=[pif],
    )
    # A PIF may be referenced by two loops without any ownership error.
    assert loop_a.process_instrumentation_functions[0] is pif
    assert loop_b.process_instrumentation_functions[0] is pif


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


def test_psgf_identity_and_fields():
    psgf = ProcessSignalGeneratingFunction(
        dex_id="PSGF-1",
        process_signal_generating_function_number="FT-101",
        sensor_type="FT",
    )
    assert psgf.dex_id == "PSGF-1"
    assert psgf.component_class == "ProcessSignalGeneratingFunction"
    assert (
        psgf.component_class_uri
        == "http://sandbox.dexpi.org/rdl/ProcessSignalGeneratingFunction"
    )
    assert psgf.process_signal_generating_function_number == "FT-101"
    assert psgf.sensor_type == "FT"
    assert psgf.sensing_location is None


def test_psgf_fields_are_optional():
    psgf = ProcessSignalGeneratingFunction(dex_id="PSGF-1")
    assert psgf.process_signal_generating_function_number is None
    assert psgf.sensor_type is None


def test_psgf_is_signal_source_only():
    assert issubclass(ProcessSignalGeneratingFunction, SignalConveyingFunctionSource)
    assert not issubclass(
        ProcessSignalGeneratingFunction, SignalConveyingFunctionTarget
    )


def test_psgf_is_valid_signal_source_not_target():
    pif = ProcessInstrumentationFunction(dex_id="PIF-1")
    psgf = ProcessSignalGeneratingFunction(dex_id="PSGF-1")
    signal = SignalConveyingFunction(dex_id="S-1", source=psgf, target=pif)
    assert signal.source is psgf
    with pytest.raises(ValidationError):
        SignalConveyingFunction(dex_id="S-2", source=pif, target=psgf)


def test_psgf_sensing_location_accepts_sensing_locations():
    segment = PipingNetworkSegment(dex_id="SEG-1")
    element = FlowMeasuringElement(dex_id="FME-1")
    nozzle = Nozzle(dex_id="N-1")
    for location in (segment, element, nozzle):
        psgf = ProcessSignalGeneratingFunction(dex_id="PSGF-1", sensing_location=location)
        assert psgf.sensing_location is location


def test_psgf_sensing_location_is_a_reference_not_ownership():
    element = FlowMeasuringElement(dex_id="FME-1")
    psgf = ProcessSignalGeneratingFunction(dex_id="PSGF-1", sensing_location=element)
    assert psgf.sensing_location is element
    # The sensing location does not compose the PSGF and may be referenced again.
    other = ProcessSignalGeneratingFunction(dex_id="PSGF-2", sensing_location=element)
    assert other.sensing_location is element


def test_psgf_sensing_location_rejects_non_sensing_location():
    with pytest.raises(ValidationError):
        ProcessSignalGeneratingFunction(
            dex_id="PSGF-1", sensing_location=Chamber(dex_id="CH-1")
        )


def test_pif_composes_psgf():
    pif = ProcessInstrumentationFunction(dex_id="PIF-1")
    psgf = ProcessSignalGeneratingFunction(dex_id="PSGF-1")
    pif.add_process_signal_generating_function(psgf)
    assert psgf in pif.process_signal_generating_functions


def test_pif_composes_psgf_via_constructor():
    psgf = ProcessSignalGeneratingFunction(dex_id="PSGF-1")
    pif = ProcessInstrumentationFunction(
        dex_id="PIF-1", process_signal_generating_functions=[psgf]
    )
    assert pif.process_signal_generating_functions == [psgf]


def test_psgf_cannot_have_two_owners():
    pif_a = ProcessInstrumentationFunction(dex_id="PIF-1")
    pif_b = ProcessInstrumentationFunction(dex_id="PIF-2")
    psgf = ProcessSignalGeneratingFunction(dex_id="PSGF-1")
    pif_a.add_process_signal_generating_function(psgf)
    with pytest.raises(ValueError):
        pif_b.add_process_signal_generating_function(psgf)


def test_psgf_cannot_have_two_owners_via_constructor():
    psgf = ProcessSignalGeneratingFunction(dex_id="PSGF-1")
    ProcessInstrumentationFunction(dex_id="PIF-1", process_signal_generating_functions=[psgf])
    with pytest.raises(ValueError):
        ProcessInstrumentationFunction(
            dex_id="PIF-2", process_signal_generating_functions=[psgf]
        )


def test_psgf_same_owner_readd_is_rejected():
    pif = ProcessInstrumentationFunction(dex_id="PIF-1")
    psgf = ProcessSignalGeneratingFunction(dex_id="PSGF-1")
    pif.add_process_signal_generating_function(psgf)
    with pytest.raises(ValueError, match="already composed under this"):
        pif.add_process_signal_generating_function(psgf)
    assert pif.process_signal_generating_functions == [psgf]


def test_actuating_function_same_owner_readd_is_rejected():
    pif = ProcessInstrumentationFunction(dex_id="PIF-1")
    function = ActuatingFunction(dex_id="AF-1")
    pif.add_actuating_function(function)
    with pytest.raises(ValueError, match="already composed under this"):
        pif.add_actuating_function(function)
    assert pif.actuating_functions == [function]


def test_signal_same_owner_readd_is_rejected():
    pif = ProcessInstrumentationFunction(dex_id="PIF-1")
    signal = SignalConveyingFunction(dex_id="S-1")
    pif.add_signal_conveying_function(signal)
    with pytest.raises(ValueError, match="already composed under this"):
        pif.add_signal_conveying_function(signal)
    assert pif.signal_conveying_functions == [signal]


@pytest.mark.parametrize(
    ("field", "function"),
    [
        ("process_signal_generating_functions",
         ProcessSignalGeneratingFunction(dex_id="PSGF-1")),
        ("actuating_functions", ActuatingFunction(dex_id="AF-1")),
        ("signal_conveying_functions", SignalConveyingFunction(dex_id="S-1")),
    ],
)
def test_duplicate_function_in_constructor_list_is_rejected(field, function):
    with pytest.raises(ValueError, match="already composed under this"):
        ProcessInstrumentationFunction(dex_id="PIF-1", **{field: [function, function]})


def test_same_function_in_constructor_list_is_not_bound_twice():
    psgf = ProcessSignalGeneratingFunction(dex_id="PSGF-1")
    pif = ProcessInstrumentationFunction(
        dex_id="PIF-1", process_signal_generating_functions=[psgf],
    )
    with pytest.raises(ValueError, match="already composed under this"):
        pif.add_process_signal_generating_function(psgf)
    assert pif.process_signal_generating_functions == [psgf]
