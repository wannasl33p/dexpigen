"""Model checks run by ``to_proteus_xml`` before it writes anything.

They close the gaps the construction API cannot see on its own: a ``dex_id``
that would be an invalid or duplicate Proteus ``ID``, a reference to an object
that is not composed in the model, and a composition list mutated in place
(bypassing ``add_*``).
"""

import pytest

from dexpigen.equipment import Chamber, Nozzle, Tank
from dexpigen.instrumentation import (
    ActuatingSystem,
    InstrumentationLoopFunction,
    OperatedValveReference,
    ProcessInstrumentationFunction,
    ProcessSignalGeneratingFunction,
)
from dexpigen.model import ConceptualModel
from dexpigen.piping import (
    GlobeValve,
    Pipe,
    PipingNetworkSegment,
    PipingNetworkSystem,
    PipingNode,
)
from dexpigen.serialization import to_proteus_xml


def _tank_model(*nozzles: Nozzle) -> ConceptualModel:
    tank = Tank(dex_id="Tank-1")
    for nozzle in nozzles:
        tank.add_nozzle(nozzle)
    return ConceptualModel(dex_id="model").add_equipment(tank)


def test_valid_model_passes_the_checks():
    nozzle = Nozzle(dex_id="Nozzle-1")
    nozzle.add_node(PipingNode(dex_id="PipingNode-1"))
    assert "<Nozzle" in to_proteus_xml(_tank_model(nozzle))


# --- dex_id: unique NCName ---


def test_duplicate_dex_id_is_rejected():
    model = _tank_model(Nozzle(dex_id="N-1"), Nozzle(dex_id="N-1"))
    with pytest.raises(ValueError, match="the Proteus ID must be unique in the model"):
        to_proteus_xml(model)


def test_dex_id_colliding_with_default_node_id_is_rejected():
    model = _tank_model(Nozzle(dex_id="N-1"), Nozzle(dex_id="N-1-DefaultNode"))
    with pytest.raises(ValueError, match="duplicate dex_id 'N-1-DefaultNode'"):
        to_proteus_xml(model)


@pytest.mark.parametrize("dex_id", ["1", "Nozzle 1", "a:b", "", "-N"])
def test_dex_id_that_is_not_an_ncname_is_rejected(dex_id):
    model = _tank_model(Nozzle(dex_id=dex_id))
    with pytest.raises(ValueError, match="is not a valid XML NCName"):
        to_proteus_xml(model)


def test_root_dex_id_is_not_checked():
    # The root ConceptualModel has no Proteus ID, so its dex_id is free-form.
    model = ConceptualModel(dex_id="C01 model")
    assert "<PlantModel>" in to_proteus_xml(model)


# --- references must point at composed objects ---


def test_reference_to_uncomposed_object_is_rejected():
    valve = GlobeValve(dex_id="GlobeValve-1")  # never added to a segment
    system = ActuatingSystem(
        dex_id="AS-1",
        operated_valve_reference=OperatedValveReference(dex_id="OVR-1", valve=valve),
    )
    model = ConceptualModel(dex_id="model").add_actuating_system(system)
    with pytest.raises(ValueError, match="but not composed anywhere in the model"):
        to_proteus_xml(model)


def test_loop_referencing_pif_missing_from_model_is_rejected():
    pif = ProcessInstrumentationFunction(dex_id="PIF-1")
    loop = InstrumentationLoopFunction(
        dex_id="L-1", process_instrumentation_functions=[pif]
    )
    model = ConceptualModel(dex_id="model").add_instrumentation_loop_function(loop)
    with pytest.raises(ValueError, match="InstrumentationLoopFunction 'L-1'"):
        to_proteus_xml(model)
    model.add_process_instrumentation_function(pif)
    assert "is a collection including" in to_proteus_xml(model)


def test_sensing_location_must_be_composed():
    nozzle = Nozzle(dex_id="Nozzle-1")  # not under any equipment
    pif = ProcessInstrumentationFunction(dex_id="PIF-1")
    pif.add_process_signal_generating_function(
        ProcessSignalGeneratingFunction(dex_id="PSGF-1", sensing_location=nozzle)
    )
    model = ConceptualModel(dex_id="model").add_process_instrumentation_function(pif)
    with pytest.raises(ValueError, match="but not composed anywhere in the model"):
        to_proteus_xml(model)


def test_pipe_endpoint_must_be_composed():
    nozzle = Nozzle(dex_id="Nozzle-1")
    segment = PipingNetworkSegment(
        dex_id="SEG-1", connections=[Pipe(dex_id="Pipe-1", target_item=nozzle)]
    )
    model = ConceptualModel(dex_id="model").add_piping_network_system(
        PipingNetworkSystem(dex_id="PNS-1", segments=[segment])
    )
    with pytest.raises(
        ValueError, match="Nozzle 'Nozzle-1' is referenced by Pipe 'Pipe-1'.target_item"
    ):
        to_proteus_xml(model)


# --- composition lists mutated in place ---


def test_list_append_bypassing_add_is_rejected():
    tank = Tank(dex_id="Tank-1")
    tank.nozzles.append(Nozzle(dex_id="Nozzle-1"))
    model = ConceptualModel(dex_id="model").add_equipment(tank)
    with pytest.raises(
        ValueError, match=r"use the add_\* method instead of mutating the list in place"
    ):
        to_proteus_xml(model)


def test_child_appended_to_a_second_owner_is_rejected():
    first, second = Tank(dex_id="Tank-1"), Tank(dex_id="Tank-2")
    chamber = Chamber(dex_id="Chamber-1")
    first.add_drying_chamber(chamber)
    second.drying_chambers.append(chamber)
    model = ConceptualModel(dex_id="model").add_equipment(first).add_equipment(second)
    with pytest.raises(ValueError, match="is composed more than once in the model"):
        to_proteus_xml(model)


def test_top_level_object_added_twice_is_rejected():
    tank = Tank(dex_id="Tank-1")
    model = ConceptualModel(dex_id="model").add_equipment(tank).add_equipment(tank)
    with pytest.raises(
        ValueError, match="Tank 'Tank-1' is composed more than once in the model"
    ):
        to_proteus_xml(model)
