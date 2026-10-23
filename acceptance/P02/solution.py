"""Reference solution for P02 (a pipe from an off-page connector to a pump nozzle)."""

from dexpigen import CustomAttribute
from dexpigen.equipment import CentrifugalPump, Nozzle
from dexpigen.model import ConceptualModel
from dexpigen.piping import (
    FlowInPipeOffPageConnector,
    Pipe,
    PipeOffPageConnectorReferenceByNumber,
    PipingNetworkSegment,
    PipingNetworkSystem,
    PipingNode,
)

NOMINAL_DIAMETER = "NominalDiameterNumericalValueRepresentationAssignmentClass"


def build() -> ConceptualModel:
    node = PipingNode(dex_id="PipingNode-2")
    node.add_custom_attribute(CustomAttribute(name=NOMINAL_DIAMETER, value="80"))
    nozzle = Nozzle(dex_id="Nozzle-1")
    nozzle.add_node(node)
    pump = CentrifugalPump(
        dex_id="CentrifugalPump-1", tag_name="P4712",
        tag_name_prefix="P", tag_name_sequence_number="4712",
    )
    pump.add_nozzle(nozzle)

    connector = FlowInPipeOffPageConnector(dex_id="FlowInPipeOffPageConnector-1", flow_out_index=1)
    connector.add_node(PipingNode(dex_id="PipingNode-1"))
    connector.add_custom_attribute(
        CustomAttribute(name="PipeConnectorNumberAssignmentClass", value="123")
    )
    connector.add_connector_reference(PipeOffPageConnectorReferenceByNumber(
        dex_id="PipeOffPageConnectorReferenceByNumber-1", referenced_connector_number="123",
    ))

    segment = PipingNetworkSegment(dex_id="PipingNetworkSegment-1", items=[connector])
    segment.add_connection(Pipe(
        dex_id="Pipe-1", source_item=connector, source_node=connector.nodes[0],
        target_item=nozzle, target_node=node,
    ))
    line = PipingNetworkSystem(
        dex_id="PipingNetworkSystem-1", line_number="48121",
        fluid_code="MNb", piping_class_code="75HB", segments=[segment],
    )
    line.add_custom_attribute(CustomAttribute(name=NOMINAL_DIAMETER, value="80"))

    return ConceptualModel(dex_id="P02", equipment=[pump], piping_network_systems=[line])
