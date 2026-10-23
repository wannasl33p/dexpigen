"""Recipe: a piping network system with segments, in-line items and connections.

Flow: off-page connector -> pump suction; pump discharge -> globe valve ->
reducer -> tee; tee run -> ball valve -> tank; tee branch -> butterfly valve
-> off-page connector.

Guide: docs/recipes/piping-network.md
Run:   uv run python examples/recipes/piping_network.py
"""

import sys
import tempfile
from pathlib import Path

from dexpigen import to_proteus_xml
from dexpigen.equipment import CentrifugalPump, Nozzle, Tank
from dexpigen.model import ConceptualModel
from dexpigen.piping import (
    BallValve,
    ButterflyValve,
    FlowInPipeOffPageConnector,
    FlowOutPipeOffPageConnector,
    GlobeValve,
    Pipe,
    PipeOffPageConnectorReferenceByNumber,
    PipeReducer,
    PipeTee,
    PipingComponent,
    PipingNetworkSegment,
    PipingNetworkSystem,
    PipingNode,
)


def with_nodes[T: PipingComponent](component: T, *node_ids: str) -> T:
    """Compose one process node per id; node i is addressed as index i + 1."""
    for node_id in node_ids:
        component.add_node(PipingNode(dex_id=node_id))
    return component


def build() -> ConceptualModel:
    # Endpoints owned by equipment: a nozzle owns its node.
    suction, discharge, inlet = (Nozzle(dex_id=f"Nozzle-{i}") for i in (1, 2, 3))
    for i, item in enumerate((suction, discharge, inlet), start=1):
        item.add_node(PipingNode(dex_id=f"NozzleNode-{i}"))
    pump = CentrifugalPump(dex_id="CentrifugalPump-1", tag_name="P4711")
    pump.add_nozzle(suction)
    pump.add_nozzle(discharge)
    tank = Tank(dex_id="Tank-1", tag_name="T4750")
    tank.add_nozzle(inlet)

    # In-line items. flow_in_index / flow_out_index are 1-based node indices.
    opc_in = FlowInPipeOffPageConnector(dex_id="FlowInPipeOffPageConnector-1", flow_out_index=1)
    opc_in.add_node(PipingNode(dex_id="PipingNode-1"))
    opc_in.add_connector_reference(PipeOffPageConnectorReferenceByNumber(
        dex_id="PipeOffPageConnectorReferenceByNumber-1",
        referenced_connector_number="7", referenced_drawing_number="PID-002",
    ))
    globe = with_nodes(GlobeValve(dex_id="GlobeValve-1", piping_component_number="V1",
                                  flow_in_index=1, flow_out_index=2), "PipingNode-2", "PipingNode-3")
    reducer = with_nodes(PipeReducer(dex_id="PipeReducer-1", flow_in_index=1, flow_out_index=2),
                         "PipingNode-4", "PipingNode-5")
    tee = with_nodes(PipeTee(dex_id="PipeTee-1", flow_in_index=1),
                     "PipingNode-6", "PipingNode-7", "PipingNode-8")
    ball = with_nodes(BallValve(dex_id="BallValve-1", flow_in_index=1, flow_out_index=2),
                      "PipingNode-9", "PipingNode-10")
    butterfly = with_nodes(ButterflyValve(dex_id="ButterflyValve-1", flow_in_index=1, flow_out_index=2),
                           "PipingNode-11", "PipingNode-12")
    opc_out = FlowOutPipeOffPageConnector(dex_id="FlowOutPipeOffPageConnector-1", flow_in_index=1)
    opc_out.add_node(PipingNode(dex_id="PipingNode-13"))

    def pipe(dex_id, source, source_node, target, target_node) -> Pipe:
        """A connection from ``source.nodes[source_node]`` to ``target.nodes[target_node]``.

        Indices here are Python list indices; the serializer writes them
        1-based as ``FromNode`` / ``ToNode``. Each node must belong to its item.
        """
        return Pipe(dex_id=dex_id, source_item=source, source_node=source.nodes[source_node],
                    target_item=target, target_node=target.nodes[target_node])

    # A segment composes its items and the connections between them.
    s1 = PipingNetworkSegment(dex_id="PipingNetworkSegment-1", segment_number="S1")
    s1.add_item(opc_in)
    s1.add_connection(pipe("Pipe-1", opc_in, 0, pump.nozzles[0], 0))
    s2 = PipingNetworkSegment(dex_id="PipingNetworkSegment-2", segment_number="S2")
    for item in (globe, reducer, tee):
        s2.add_item(item)
    s2.add_connection(pipe("Pipe-2", discharge, 0, globe, 0))
    s2.add_connection(pipe("Pipe-3", globe, 1, reducer, 0))
    s2.add_connection(pipe("Pipe-4", reducer, 1, tee, 0))
    s3 = PipingNetworkSegment(dex_id="PipingNetworkSegment-3", segment_number="S3", items=[ball])
    s3.add_connection(pipe("Pipe-5", tee, 1, ball, 0))  # an endpoint may sit in another segment
    s3.add_connection(pipe("Pipe-6", ball, 1, inlet, 0))
    s4 = PipingNetworkSegment(dex_id="PipingNetworkSegment-4", segment_number="S4",
                              items=[butterfly, opc_out])
    s4.add_connection(pipe("Pipe-7", tee, 2, butterfly, 0))
    s4.add_connection(pipe("Pipe-8", butterfly, 1, opc_out, 0))

    line = PipingNetworkSystem(dex_id="PipingNetworkSystem-1", line_number="47121",
                               fluid_code="MNc", piping_class_code="75HB13")
    for segment in (s1, s2, s3, s4):
        line.add_segment(segment)
    return (ConceptualModel(dex_id="piping-network")
            .add_equipment(pump).add_equipment(tank).add_piping_network_system(line))


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # examples/
    from validate_dexpi import validate

    out = Path(tempfile.gettempdir()) / "piping_network.xml"
    out.write_text(to_proteus_xml(build()), encoding="utf-8")
    sys.exit(0 if validate(str(out)) else 1)
