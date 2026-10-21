"""Tests for the top-level ``ConceptualModel``."""

from dexpigen.equipment import Nozzle, Pump
from dexpigen.instrumentation import (
    ActuatingSystem,
    InstrumentationLoopFunction,
    ProcessInstrumentationFunction,
    SignalConveyingFunction,
)
from dexpigen.model import ConceptualModel
from dexpigen.piping import PipingNetworkSegment, PipingNetworkSystem


def test_conceptual_model_defaults_to_empty_collections():
    model = ConceptualModel(dex_id="M-1")
    assert model.equipment == []
    assert model.piping_network_systems == []
    assert model.process_instrumentation_functions == []
    assert model.actuating_systems == []


def test_conceptual_model_aggregates_top_level_objects():
    pump = Pump(dex_id="P-1", nozzles=[Nozzle(dex_id="N-1")])
    system = PipingNetworkSystem(dex_id="S-1")
    pif = ProcessInstrumentationFunction(dex_id="PIF-1")

    model = ConceptualModel(
        dex_id="M-1",
        equipment=[pump],
        piping_network_systems=[system],
        process_instrumentation_functions=[pif],
    )

    assert model.equipment[0] is pump
    assert model.piping_network_systems[0] is system
    assert model.process_instrumentation_functions[0] is pif


def test_navigate_by_typed_relationships():
    pump = Pump(dex_id="P-1", nozzles=[Nozzle(dex_id="N-1")])
    segment = PipingNetworkSegment(dex_id="seg-1")
    system = PipingNetworkSystem(dex_id="S-1", segments=[segment])
    pif = ProcessInstrumentationFunction(dex_id="PIF-1")
    signal = SignalConveyingFunction(dex_id="sig-1", source=pif)
    pif.add_signal_conveying_function(signal)

    model = ConceptualModel(
        dex_id="M-1",
        equipment=[pump],
        piping_network_systems=[system],
        process_instrumentation_functions=[pif],
    )

    # equipment -> nozzles
    assert model.equipment[0].nozzles[0].dex_id == "N-1"
    # system -> segments
    assert model.piping_network_systems[0].segments[0] is segment
    # function -> composed signal -> source reference
    assert model.process_instrumentation_functions[0].signal_conveying_functions[0] is signal
    assert model.process_instrumentation_functions[0].signal_conveying_functions[0].source is pif


def test_conceptual_model_add_methods():
    model = ConceptualModel(dex_id="M-1")
    pump = Pump(dex_id="P-1")
    system = PipingNetworkSystem(dex_id="S-1")
    pif = ProcessInstrumentationFunction(dex_id="PIF-1")
    actuating_system = ActuatingSystem(dex_id="AS-1")

    assert model.add_equipment(pump) is model
    assert model.add_piping_network_system(system) is model
    assert model.add_process_instrumentation_function(pif) is model
    assert model.add_actuating_system(actuating_system) is model

    assert pump in model.equipment
    assert system in model.piping_network_systems
    assert pif in model.process_instrumentation_functions
    assert actuating_system in model.actuating_systems


def test_conceptual_model_instrumentation_loop_functions_default_empty():
    model = ConceptualModel(dex_id="M-1")
    assert model.instrumentation_loop_functions == []


def test_conceptual_model_add_instrumentation_loop_function():
    model = ConceptualModel(dex_id="M-1")
    loop = InstrumentationLoopFunction(dex_id="ILF-1")
    assert model.add_instrumentation_loop_function(loop) is model
    assert loop in model.instrumentation_loop_functions


def test_pif_referenced_by_loop_can_also_be_top_level():
    pif = ProcessInstrumentationFunction(dex_id="PIF-1")
    loop = InstrumentationLoopFunction(
        dex_id="ILF-1", process_instrumentation_functions=[pif],
    )
    model = ConceptualModel(
        dex_id="M-1",
        process_instrumentation_functions=[pif],
        instrumentation_loop_functions=[loop],
    )
    assert model.process_instrumentation_functions[0] is pif
    assert model.instrumentation_loop_functions[0].process_instrumentation_functions[0] is pif
