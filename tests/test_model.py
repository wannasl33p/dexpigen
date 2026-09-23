"""Tests for the top-level ``ConceptualModel``."""

from dexpigen.equipment import Nozzle, Pump
from dexpigen.instrumentation import (
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
    assert model.actuating_functions == []
    assert model.signal_conveying_functions == []


def test_conceptual_model_aggregates_top_level_objects():
    pump = Pump(dex_id="P-1", nozzles=[Nozzle(dex_id="N-1")])
    segment = PipingNetworkSegment(dex_id="seg-1")
    system = PipingNetworkSystem(dex_id="S-1", segments=[segment])
    pif = ProcessInstrumentationFunction(dex_id="PIF-1")
    signal = SignalConveyingFunction(dex_id="sig-1", source=pif)

    model = ConceptualModel(
        dex_id="M-1",
        equipment=[pump],
        piping_network_systems=[system],
        process_instrumentation_functions=[pif],
        signal_conveying_functions=[signal],
    )

    assert model.equipment[0] is pump
    assert model.piping_network_systems[0] is system
    assert model.process_instrumentation_functions[0] is pif
    assert model.signal_conveying_functions[0] is signal


def test_navigate_by_typed_relationships():
    pump = Pump(dex_id="P-1", nozzles=[Nozzle(dex_id="N-1")])
    segment = PipingNetworkSegment(dex_id="seg-1")
    system = PipingNetworkSystem(dex_id="S-1", segments=[segment])
    pif = ProcessInstrumentationFunction(dex_id="PIF-1")
    signal = SignalConveyingFunction(dex_id="sig-1", source=pif)

    model = ConceptualModel(
        dex_id="M-1",
        equipment=[pump],
        piping_network_systems=[system],
        process_instrumentation_functions=[pif],
        signal_conveying_functions=[signal],
    )

    # equipment -> nozzles
    assert model.equipment[0].nozzles[0].dex_id == "N-1"
    # system -> segments
    assert model.piping_network_systems[0].segments[0] is segment
    # function -> signal reference
    assert model.signal_conveying_functions[0].source is pif
