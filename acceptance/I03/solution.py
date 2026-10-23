"""Reference solution for I03 (measurement and control): rebuilds input.xml."""

from dexpigen import CustomAttribute
from dexpigen.equipment import Nozzle, Tank
from dexpigen.instrumentation import (
    ActuatingFunction,
    ActuatingSystem,
    ControlledActuator,
    InstrumentationLoopFunction,
    OperatedValveReference,
    ProcessInstrumentationFunction,
    ProcessSignalGeneratingFunction,
)
from dexpigen.model import ConceptualModel
from dexpigen.piping import GlobeValve, PipingNetworkSegment, PipingNetworkSystem, PipingNode


def build() -> ConceptualModel:
    nozzle = Nozzle(dex_id="Nozzle-1")
    nozzle.add_node(PipingNode(dex_id="PipingNode-4"))
    tank = Tank(dex_id="Tank-1")
    tank.add_nozzle(nozzle)

    valve = GlobeValve(dex_id="GlobeValve-1", piping_component_number="LV 03",
                       flow_in_index=1, flow_out_index=2)
    valve.add_node(PipingNode(dex_id="PipingNode-1"))
    valve.add_node(PipingNode(dex_id="PipingNode-2"))
    line_1 = PipingNetworkSystem(dex_id="PipingNetworkSystem-1", segments=[
        PipingNetworkSegment(dex_id="PipingNetworkSegment-1", items=[valve]),
    ])
    line_2 = PipingNetworkSystem(dex_id="PipingNetworkSystem-2", segments=[
        PipingNetworkSegment(dex_id="PipingNetworkSegment-2"),
    ])

    system = ActuatingSystem(
        dex_id="ActuatingSystem-1",
        controlled_actuator=ControlledActuator(
            dex_id="ControlledActuator-1", device_type_name="Spring-diaphragm",
        ),
        operated_valve_reference=OperatedValveReference(
            dex_id="OperatedValveReference-1", valve=valve,
        ),
    )

    pif = ProcessInstrumentationFunction(
        dex_id="ProcessInstrumentationFunction-1",
        process_instrumentation_function_category="L",
        process_instrumentation_function_number="03",
        process_instrumentation_functions_code="ICSA",
    )
    pif.add_custom_attribute(CustomAttribute(
        name="LocationSpecialization", format="anyURI", value="CentralLocation",
        value_uri="http://sandbox.dexpi.org/rdl/CentralLocation",
    ))
    pif.add_actuating_function(ActuatingFunction(dex_id="ActuatingFunction-1", systems=system))
    pif.add_process_signal_generating_function(
        ProcessSignalGeneratingFunction(dex_id="ProcessSignalGeneratingFunction-1")
    )

    loop = InstrumentationLoopFunction(
        dex_id="InstrumentationLoopFunction-1",
        instrumentation_loop_function_number="03",
        process_instrumentation_functions=[pif],
    )

    return ConceptualModel(
        dex_id="I03",
        equipment=[tank],
        piping_network_systems=[line_1, line_2],
        process_instrumentation_functions=[pif],
        actuating_systems=[system],
        instrumentation_loop_functions=[loop],
    )
