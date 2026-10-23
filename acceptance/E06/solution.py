"""Reference solution for E06 (pump and plate heat exchanger connected by a line)."""

from dexpigen import CustomAttribute
from dexpigen.equipment import CentrifugalPump, Nozzle, PlateHeatExchanger
from dexpigen.model import ConceptualModel
from dexpigen.piping import Pipe, PipingNetworkSegment, PipingNetworkSystem, PipingNode


def _nozzle(dex_id: str, sub_tag_name: str, node_id: str) -> Nozzle:
    nozzle = Nozzle(dex_id=dex_id, sub_tag_name=sub_tag_name)
    nozzle.add_node(PipingNode(dex_id=node_id))
    return nozzle


def build() -> ConceptualModel:
    pump = CentrifugalPump(
        dex_id="CentrifugalPump-1", tag_name="P-4713",
        tag_name_prefix="P", tag_name_sequence_number="4713",
    )
    pump.add_nozzle(_nozzle("Nozzle-3", "N-1", "PipingNode-1"))
    discharge = _nozzle("Nozzle-1", "N-2", "PipingNode-2")
    pump.add_nozzle(discharge)

    exchanger = PlateHeatExchanger(
        dex_id="PlateHeatExchanger-1", tag_name="H-1009",
        tag_name_prefix="H", tag_name_sequence_number="1009",
    )
    inlet = _nozzle("Nozzle-2", "N-1", "PipingNode-3")
    exchanger.add_nozzle(inlet)
    exchanger.add_nozzle(_nozzle("Nozzle-4", "N-2", "PipingNode-4"))
    exchanger.add_nozzle(_nozzle("Nozzle-5", "N-3", "PipingNode-5"))
    exchanger.add_nozzle(_nozzle("Nozzle-6", "N-4", "PipingNode-6"))

    segment = PipingNetworkSegment(dex_id="PipingNetworkSegment-1")
    segment.add_connection(Pipe(
        dex_id="Pipe-1", source_item=discharge, source_node=discharge.nodes[0],
        target_item=inlet, target_node=inlet.nodes[0],
    ))
    line = PipingNetworkSystem(
        dex_id="PipingNetworkSystem-1", line_number="47132",
        fluid_code="MNb", piping_class_code="75HB13", segments=[segment],
    )
    line.add_custom_attribute(CustomAttribute(
        name="NominalDiameterNumericalValueRepresentationAssignmentClass", value="80",
    ))

    return ConceptualModel(
        dex_id="E06", equipment=[pump, exchanger], piping_network_systems=[line],
    )
