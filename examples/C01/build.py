"""Build the in-memory model of the trimmed C01 reference P&ID (current version).

This is the model-builder half of a generation test sample: serializing the
``ConceptualModel`` returned by :func:`build` should reproduce
``examples/C01/ver002/c01.xml``.

The versioned-recovery workflow (see ``README.md`` in this folder): we grow the
model toward fully covering the original C01 P&ID. Each ``verNNN/`` snapshot is
the expected serialization for that milestone; ``build.py`` always builds the
latest one. ``ver002/c01.xml`` was produced from the official C01 P&ID by
``../trim_dexpi_xml.py``, which deletes only the tags the current model cannot
represent: graphics, plant structure, ``MetaData``, ``ProcessSignalGeneratingSystem``,
the equipment internals ``TubeBundle``/``Impeller``/``Displacer``, the valve and
fitting leaves ``BlindFlange``/``SwingCheckValve``/``SpringLoadedGlobeSafetyValve``,
the flow-meter and primary-element classes, and the signal-level ``ConnectionPoints``
and ``Node``s of instrumentation objects.

Known gaps:
  * Nozzle nominal-diameter fields and other non-first-class data live in the
    XML ``GenericAttributes`` and map to ``CustomAttribute`` bags (``_extras.py``).

Run:  uv run python examples/C01/build.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _extras import EXTRAS  # noqa: E402

from dexpigen.enumerations import FailActionClassification
from dexpigen.equipment import (
    CentrifugalPump,
    Chamber,
    Nozzle,
    PlateHeatExchanger,
    ReciprocatingPump,
    Tank,
    TubularHeatExchanger,
)
from dexpigen.instrumentation import (
    ActuatingFunction,
    ActuatingSystem,
    ControlledActuator,
    InstrumentationLoopFunction,
    OperatedValveReference,
    ProcessInstrumentationFunction,
    ProcessSignalGeneratingFunction,
    SignalConveyingFunction,
)
from dexpigen.model import ConceptualModel
from dexpigen.piping import (
    BallValve,
    ButterflyValve,
    FlowInPipeOffPageConnector,
    FlowOutPipeOffPageConnector,
    GlobeValve,
    Pipe,
    PipeReducer,
    PipeTee,
    PipingNetworkSegment,
    PipingNetworkSystem,
    PipingNode,
)


def _nozzle(nozzle_id: str, sub_tag: str, node_id: str) -> tuple[Nozzle, PipingNode]:
    nozzle = Nozzle(dex_id=nozzle_id, sub_tag_name=sub_tag)
    node = PipingNode(dex_id=node_id)
    nozzle.add_node(node)
    return nozzle, node


def _valve(cls, valve_id, in_node, out_node, number, name=None, fluid="MNc", flow_in=1, flow_out=2):
    valve = cls(
        dex_id=valve_id, piping_component_number=number, piping_component_name=name,
        fluid_code=fluid, flow_in_index=flow_in, flow_out_index=flow_out,
    )
    inlet = PipingNode(dex_id=in_node)
    outlet = PipingNode(dex_id=out_node)
    valve.add_node(inlet)
    valve.add_node(outlet)
    return valve, inlet, outlet


def _tee(tee_id, number, node_ids, flow_in, fluid="MNc"):
    tee = PipeTee(
        dex_id=tee_id, piping_component_number=number, fluid_code=fluid,
        flow_in_index=flow_in, component_name="T_TYPE_CONNECTION_SHAPE",
    )
    nodes = [PipingNode(dex_id=node_id) for node_id in node_ids]
    for node in nodes:
        tee.add_node(node)
    return tee, nodes


def _apply_extras(model: ConceptualModel) -> None:
    """Apply the generated custom attributes (from c01.xml) to every object."""

    def apply(obj) -> None:
        for attr in EXTRAS.get(obj.dex_id, []):
            obj.custom_attributes.append(attr)

    for equipment in model.equipment:
        apply(equipment)
        for chamber in equipment.drying_chambers:
            apply(chamber)
        for nozzle in equipment.nozzles:
            apply(nozzle)
            for node in nozzle.nodes:
                apply(node)
    for line in model.piping_network_systems:
        apply(line)
        for segment in line.segments:
            apply(segment)
            for item in segment.items:
                apply(item)
                for node in getattr(item, "nodes", []):
                    apply(node)
    for pif in model.process_instrumentation_functions:
        apply(pif)
        for af in pif.actuating_functions:
            apply(af)
        for signal in pif.signal_conveying_functions:
            apply(signal)
        for psgf in pif.process_signal_generating_functions:
            apply(psgf)
    for loop in model.instrumentation_loop_functions:
        apply(loop)
    for system in model.actuating_systems:
        apply(system)
        for component in (
            system.controlled_actuator,
            system.operated_valve_reference,
            system.positioner,
        ):
            if component is not None:
                apply(component)


def build() -> ConceptualModel:
    # ================= Equipment =================
    # CentrifugalPump-1
    cp = CentrifugalPump(
        dex_id="CentrifugalPump-1", tag_name="P4711",
        tag_name_prefix="P", tag_name_sequence_number="4711", tag_name_suffix="",
        drying_chambers=[Chamber(dex_id="Chamber-5")],
    )
    nozzle_1, nozzle_1_node = _nozzle("Nozzle-1", "N1", "PipingNode-52")
    nozzle_2, nozzle_2_node = _nozzle("Nozzle-2", "N2", "PipingNode-53")
    cp.add_nozzle(nozzle_1)
    cp.add_nozzle(nozzle_2)

    # ReciprocatingPump-1
    rp = ReciprocatingPump(
        dex_id="ReciprocatingPump-1", tag_name="P4712",
        tag_name_prefix="P", tag_name_sequence_number="4712", tag_name_suffix="",
        drying_chambers=[Chamber(dex_id="Chamber-6")],
    )
    nozzle_7, nozzle_7_node = _nozzle("Nozzle-7", "N1", "PipingNode-54")
    nozzle_9, nozzle_9_node = _nozzle("Nozzle-9", "N2", "PipingNode-55")
    rp.add_nozzle(nozzle_7)
    rp.add_nozzle(nozzle_9)

    # PlateHeatExchanger-1 (chambers 1/2; N3,N4 in chamber-1, N13,N14 in chamber-2)
    phe_ch1 = Chamber(dex_id="Chamber-1", sub_tag_name="Chamber 1")
    phe_ch2 = Chamber(dex_id="Chamber-2", sub_tag_name="Chamber 2")
    phe = PlateHeatExchanger(
        dex_id="PlateHeatExchanger-1", tag_name="H1007",
        tag_name_prefix="H", tag_name_sequence_number="1007", tag_name_suffix="",
        drying_chambers=[phe_ch1, phe_ch2],
    )
    nozzle_3, nozzle_3_node = _nozzle("Nozzle-3", "N1", "PipingNode-44")
    nozzle_4, nozzle_4_node = _nozzle("Nozzle-4", "N2", "PipingNode-45")
    nozzle_13, nozzle_13_node = _nozzle("Nozzle-13", "N3", "PipingNode-46")
    nozzle_14, nozzle_14_node = _nozzle("Nozzle-14", "N4", "PipingNode-47")
    nozzle_3.chamber = phe_ch1
    nozzle_4.chamber = phe_ch1
    nozzle_13.chamber = phe_ch2
    nozzle_14.chamber = phe_ch2
    for n in (nozzle_3, nozzle_4, nozzle_13, nozzle_14):
        phe.add_nozzle(n)

    # TubularHeatExchanger-1 (chambers 3/4; N10,N11 in 3, N16,N15 in 4)
    the_ch3 = Chamber(dex_id="Chamber-3", sub_tag_name="Chamber 1")
    the_ch4 = Chamber(dex_id="Chamber-4", sub_tag_name="Chamber 2")
    the = TubularHeatExchanger(
        dex_id="TubularHeatExchanger-1", tag_name="H1008",
        tag_name_prefix="H", tag_name_sequence_number="1008", tag_name_suffix="",
        drying_chambers=[the_ch3, the_ch4],
    )
    nozzle_10, nozzle_10_node = _nozzle("Nozzle-10", "N1", "PipingNode-48")
    nozzle_11, nozzle_11_node = _nozzle("Nozzle-11", "N2", "PipingNode-49")
    nozzle_16, nozzle_16_node = _nozzle("Nozzle-16", "N3", "PipingNode-50")
    nozzle_15, nozzle_15_node = _nozzle("Nozzle-15", "N4", "PipingNode-51")
    nozzle_10.chamber = the_ch3
    nozzle_11.chamber = the_ch3
    nozzle_16.chamber = the_ch4
    nozzle_15.chamber = the_ch4
    for n in (nozzle_10, nozzle_11, nozzle_16, nozzle_15):
        the.add_nozzle(n)

    # Tank-1 (chambers 7/8; seven nozzles)
    tank_ch7 = Chamber(dex_id="Chamber-7", sub_tag_name="Chamber 1")
    tank_ch8 = Chamber(dex_id="Chamber-8", sub_tag_name="Chamber 2")
    tank = Tank(
        dex_id="Tank-1", tag_name="T4750",
        tag_name_prefix="T", tag_name_sequence_number="4750", tag_name_suffix="",
        drying_chambers=[tank_ch7, tank_ch8],
    )
    nozzle_5, nozzle_5_node = _nozzle("Nozzle-5", "N1", "PipingNode-56")
    nozzle_6, nozzle_6_node = _nozzle("Nozzle-6", "N2", "PipingNode-57")
    nozzle_18, nozzle_18_node = _nozzle("Nozzle-18", "N3", "PipingNode-58")
    nozzle_8, nozzle_8_node = _nozzle("Nozzle-8", "N5", "PipingNode-59")
    nozzle_12, nozzle_12_node = _nozzle("Nozzle-12", "N6", "PipingNode-60")
    nozzle_17, nozzle_17_node = _nozzle("Nozzle-17", "N7", "PipingNode-61")
    nozzle_19, nozzle_19_node = _nozzle("Nozzle-19", "N8", "PipingNode-62")
    for n in (nozzle_5, nozzle_6, nozzle_18, nozzle_8, nozzle_12, nozzle_17, nozzle_19):
        tank.add_nozzle(n)

    # ================= Valves / fittings (with their process nodes) =================
    globe_2, globe_2_in, globe_2_out = _valve(GlobeValve, "GlobeValve-2", "PipingNode-2", "PipingNode-3", "C1", fluid="MNb")
    globe_1, globe_1_in, globe_1_out = _valve(GlobeValve, "GlobeValve-1", "PipingNode-40", "PipingNode-41", "C1")
    globe_3, globe_3_in, globe_3_out = _valve(GlobeValve, "GlobeValve-3", "PipingNode-42", "PipingNode-43", "C1", fluid="QSb")
    butterfly_1, _, _ = _valve(ButterflyValve, "ButterflyValve-1", "PipingNode-4", "PipingNode-5", "C1", "66KL21", flow_in=2, flow_out=1)
    reducer_1, _, reducer_1_out = _valve(PipeReducer, "PipeReducer-1", "PipingNode-8", "PipingNode-9", "C3", flow_out=None)
    ball_1, _, _ = _valve(BallValve, "BallValve-1", "PipingNode-10", "PipingNode-11", "C4", "73KH12")
    ball_2, ball_2_in, _ = _valve(BallValve, "BallValve-2", "PipingNode-17", "PipingNode-18", "C2", "73KH12", flow_in=2, flow_out=None)
    ball_3, _, _ = _valve(BallValve, "BallValve-3", "PipingNode-25", "PipingNode-26", "C5", "73KH12")
    ball_4, _, _ = _valve(BallValve, "BallValve-4", "PipingNode-28", "PipingNode-29", "C7", "73KH12")
    ball_5, _, _ = _valve(BallValve, "BallValve-5", "PipingNode-36", "PipingNode-37", "C10", "73KH12")

    # ================= Pipe tees (process nodes; the default node is implicit) =================
    tee_2, (tee_2_n1, tee_2_n2, tee_2_n3) = _tee("PipeTee-2", "C1", ["PipingNode-14", "PipingNode-15", "PipingNode-16"], flow_in=2)
    tee_1, (tee_1_n1, tee_1_n2, tee_1_n3) = _tee("PipeTee-1", "C3", ["PipingNode-19", "PipingNode-20", "PipingNode-21"], flow_in=1)
    tee_3, (tee_3_n1, tee_3_n2, tee_3_n3) = _tee("PipeTee-3", "C4", ["PipingNode-22", "PipingNode-23", "PipingNode-24"], flow_in=1)
    tee_4, (tee_4_n1, tee_4_n2, tee_4_n3) = _tee("PipeTee-4", "C8", ["PipingNode-30", "PipingNode-31", "PipingNode-32"], flow_in=1)
    tee_5, (tee_5_n1, tee_5_n2, tee_5_n3) = _tee("PipeTee-5", "C9", ["PipingNode-33", "PipingNode-34", "PipingNode-35"], flow_in=1)

    flow_in, flow_in_node = FlowInPipeOffPageConnector(dex_id="FlowInPipeOffPageConnector-1", flow_out_index=1), PipingNode(dex_id="PipingNode-1")
    flow_in.add_node(flow_in_node)
    flow_out, flow_out_node = FlowOutPipeOffPageConnector(dex_id="FlowOutPipeOffPageConnector-1", flow_in_index=1), PipingNode(dex_id="PipingNode-39")
    flow_out.add_node(flow_out_node)

    # ================= Piping network systems =================
    lines = []
    lines.append(PipingNetworkSystem(
        dex_id="PipingNetworkSystem-1", line_number="47121", fluid_code="MNb", piping_class_code="75HB13",
        segments=[PipingNetworkSegment(dex_id="PipingNetworkSegment-1", segment_number="S1", fluid_code="MNb", piping_class_code="75HB13", items=[flow_in], connections=[
            Pipe(dex_id="Pipe-1", source_item=flow_in, source_node=flow_in_node,
                 target_item=nozzle_1, target_node=nozzle_1_node),
        ])],
    ))
    lines.append(PipingNetworkSystem(
        dex_id="PipingNetworkSystem-2", line_number="47122", fluid_code="MNb", piping_class_code="75HB13",
        segments=[PipingNetworkSegment(dex_id="PipingNetworkSegment-2", segment_number="S1", fluid_code="MNb", piping_class_code="75HB13", connections=[
            Pipe(dex_id="Pipe-2", source_item=nozzle_2, source_node=nozzle_2_node,
                 target_item=nozzle_3, target_node=nozzle_3_node),
        ])],
    ))
    lines.append(PipingNetworkSystem(
        dex_id="PipingNetworkSystem-3", line_number="47123", fluid_code="MNb", piping_class_code="75HB13",
        segments=[PipingNetworkSegment(dex_id="PipingNetworkSegment-3", segment_number="S1", fluid_code="MNb", piping_class_code="75HB13", items=[globe_2], connections=[
            Pipe(dex_id="Pipe-3", source_item=nozzle_4, source_node=nozzle_4_node,
                 target_item=nozzle_5, target_node=nozzle_5_node),
        ])],
    ))
    lines.append(PipingNetworkSystem(
        dex_id="PipingNetworkSystem-4", line_number="47124", fluid_code="MNc", piping_class_code="75HB13",
        segments=[
            PipingNetworkSegment(dex_id="PipingNetworkSegment-4", segment_number="S1", fluid_code="MNc", piping_class_code="75HB13", items=[butterfly_1]),
            PipingNetworkSegment(dex_id="PipingNetworkSegment-5", segment_number="S2", fluid_code="MNc", piping_class_code="73HG12", items=[reducer_1]),
            PipingNetworkSegment(dex_id="PipingNetworkSegment-6", segment_number="S3", fluid_code="MNc", piping_class_code="73HG12", items=[ball_1], connections=[
                Pipe(dex_id="Pipe-4", source_item=reducer_1, source_node=reducer_1_out,
                     target_item=nozzle_7, target_node=nozzle_7_node),
            ]),
        ],
    ))
    lines.append(PipingNetworkSystem(
        dex_id="PipingNetworkSystem-5", line_number="47125", fluid_code="MNc", piping_class_code="73HG12",
        segments=[
            PipingNetworkSegment(dex_id="PipingNetworkSegment-7", segment_number="S1", fluid_code="MNc", piping_class_code="73HG12"),
            PipingNetworkSegment(dex_id="PipingNetworkSegment-8", segment_number="S2", fluid_code="MNc", piping_class_code="75HB13"),
        ],
    ))
    lines.append(PipingNetworkSystem(
        dex_id="PipingNetworkSystem-6", line_number="47126", fluid_code="MNc", piping_class_code="75HB13",
        segments=[
            PipingNetworkSegment(dex_id="PipingNetworkSegment-9", segment_number="S1", fluid_code="MNc", piping_class_code="75HB13", items=[tee_2], connections=[
                Pipe(dex_id="Pipe-10", source_item=nozzle_9, source_node=nozzle_9_node,
                     target_item=tee_2, target_node=tee_2_n1),
            ]),
            PipingNetworkSegment(dex_id="PipingNetworkSegment-10", segment_number="S2", fluid_code="MNc", piping_class_code="75HB13", items=[ball_2], connections=[
                Pipe(dex_id="Pipe-11", source_item=tee_2, source_node=tee_2_n3,
                     target_item=ball_2, target_node=ball_2_in),
            ]),
            PipingNetworkSegment(dex_id="PipingNetworkSegment-11", segment_number="S3", fluid_code="MNc", piping_class_code="75HB13", items=[tee_1], connections=[
                Pipe(dex_id="Pipe-12", source_item=tee_2, source_node=tee_2_n1,
                     target_item=tee_1, target_node=tee_1_n2),
            ]),
            PipingNetworkSegment(dex_id="PipingNetworkSegment-12", segment_number="S4", fluid_code="MNc", piping_class_code="75HB13", items=[tee_3], connections=[
                Pipe(dex_id="Pipe-13", source_item=tee_1, source_node=tee_1_n2,
                     target_item=tee_3, target_node=tee_3_n2),
            ]),
            PipingNetworkSegment(dex_id="PipingNetworkSegment-13", segment_number="S5", fluid_code="MNc", piping_class_code="75HB13", items=[ball_3]),
            PipingNetworkSegment(dex_id="PipingNetworkSegment-14", segment_number="S6", fluid_code="MNc", piping_class_code="75HB13", items=[ball_4, tee_4], connections=[
                Pipe(dex_id="Pipe-14", source_item=tee_3, source_node=tee_3_n2,
                     target_item=tee_4, target_node=tee_4_n2),
            ]),
            PipingNetworkSegment(dex_id="PipingNetworkSegment-15", segment_number="S7", fluid_code="MNc", piping_class_code="75HB13", connections=[
                Pipe(dex_id="Pipe-15", source_item=tee_4, source_node=tee_4_n3,
                     target_item=nozzle_10, target_node=nozzle_10_node),
            ]),
            PipingNetworkSegment(dex_id="PipingNetworkSegment-16", segment_number="S8", fluid_code="MNc", piping_class_code="75HB13", items=[tee_5], connections=[
                Pipe(dex_id="Pipe-16", source_item=tee_4, source_node=tee_4_n2,
                     target_item=tee_5, target_node=tee_5_n2),
            ]),
            PipingNetworkSegment(dex_id="PipingNetworkSegment-17", segment_number="S9", fluid_code="MNc", piping_class_code="75HB13", items=[ball_5]),
            PipingNetworkSegment(dex_id="PipingNetworkSegment-18", segment_number="S10", fluid_code="MNc", piping_class_code="75HB13", items=[flow_out], connections=[
                Pipe(dex_id="Pipe-17", source_item=tee_5, source_node=tee_5_n2,
                     target_item=flow_out, target_node=flow_out_node),
            ]),
        ],
    ))
    lines.append(PipingNetworkSystem(
        dex_id="PipingNetworkSystem-7", line_number="47127", fluid_code="MNc", piping_class_code="75HB13",
        segments=[PipingNetworkSegment(dex_id="PipingNetworkSegment-19", segment_number="S1", fluid_code="MNc", piping_class_code="75HB13", items=[globe_1], connections=[
            Pipe(dex_id="Pipe-5", source_item=nozzle_11, source_node=nozzle_11_node,
                 target_item=nozzle_12, target_node=nozzle_12_node),
        ])],
    ))
    lines.append(PipingNetworkSystem(
        dex_id="PipingNetworkSystem-8", line_number="47130", fluid_code="WKa", piping_class_code="75HB13",
        segments=[PipingNetworkSegment(dex_id="PipingNetworkSegment-20", segment_number="S1", fluid_code="WKa", piping_class_code="75HB13", connections=[
            Pipe(dex_id="Pipe-6", target_item=nozzle_13, target_node=nozzle_13_node),
        ])],
    ))
    lines.append(PipingNetworkSystem(
        dex_id="PipingNetworkSystem-9", line_number="47131", fluid_code="WKb", piping_class_code="75HB13",
        segments=[PipingNetworkSegment(dex_id="PipingNetworkSegment-21", segment_number="S1", fluid_code="WKb", piping_class_code="75HB13", connections=[
            Pipe(dex_id="Pipe-7", source_item=nozzle_14, source_node=nozzle_14_node),
        ])],
    ))
    lines.append(PipingNetworkSystem(
        dex_id="PipingNetworkSystem-10", line_number="47140", fluid_code="QSa", piping_class_code="75HB13",
        segments=[PipingNetworkSegment(dex_id="PipingNetworkSegment-22", segment_number="S1", fluid_code="QSa", piping_class_code="75HB13", connections=[
            Pipe(dex_id="Pipe-8", target_item=nozzle_15, target_node=nozzle_15_node),
        ])],
    ))
    lines.append(PipingNetworkSystem(
        dex_id="PipingNetworkSystem-11", line_number="47141", fluid_code="QSb", piping_class_code="75HB13",
        segments=[PipingNetworkSegment(dex_id="PipingNetworkSegment-23", segment_number="S1", fluid_code="QSb", piping_class_code="75HB13", items=[globe_3], connections=[
            Pipe(dex_id="Pipe-9", source_item=nozzle_16, source_node=nozzle_16_node),
        ])],
    ))

    # ================= Actuating systems =================
    as_1 = ActuatingSystem(
        dex_id="ActuatingSystem-1", actuating_system_number="PV4712.02",
        controlled_actuator=ControlledActuator(
            dex_id="ControlledActuator-1", device_type_name="general",
            fail_action=FailActionClassification.FAIL_CLOSE,
            fail_action_representation="F.C.", sub_tag_name="PV4712.02_YC",
        ),
        operated_valve_reference=OperatedValveReference(
            dex_id="OperatedValveReference-1", sub_tag_name="PV4712.02_YV", valve=globe_1,
        ),
    )
    as_2 = ActuatingSystem(
        dex_id="ActuatingSystem-2", actuating_system_number="HV4750.01",
        controlled_actuator=ControlledActuator(
            dex_id="ControlledActuator-2", device_type_name="general",
            fail_action=FailActionClassification.FAIL_CLOSE,
            fail_action_representation="F.C.", sub_tag_name="HV4750.01_YC",
        ),
        operated_valve_reference=OperatedValveReference(
            dex_id="OperatedValveReference-2", sub_tag_name="HV4750.01_YV", valve=globe_2,
        ),
    )
    as_3 = ActuatingSystem(
        dex_id="ActuatingSystem-3", actuating_system_number="TV4750.03",
        controlled_actuator=ControlledActuator(
            dex_id="ControlledActuator-3", device_type_name="general",
            fail_action=FailActionClassification.FAIL_OPEN,
            fail_action_representation="F.O.", sub_tag_name="TV4750.03_YC",
        ),
        operated_valve_reference=OperatedValveReference(
            dex_id="OperatedValveReference-3", sub_tag_name="TV4750.03_YV", valve=globe_3,
        ),
    )

    # ================= Instrumentation =================
    pif_1 = ProcessInstrumentationFunction(
        dex_id="ProcessInstrumentationFunction-1",
        process_instrumentation_function_number="4712.01",
        process_instrumentation_function_category="P",
        process_instrumentation_functions_code="I",
    )

    pif_2 = ProcessInstrumentationFunction(
        dex_id="ProcessInstrumentationFunction-2",
        process_instrumentation_function_number="4712.02",
        process_instrumentation_function_category="P",
        process_instrumentation_functions_code="ICSA",
    )
    af_1 = ActuatingFunction(
        dex_id="ActuatingFunction-1", actuating_function_number="PV4712.02", systems=as_1,
    )
    psgf_1 = ProcessSignalGeneratingFunction(
        dex_id="ProcessSignalGeneratingFunction-1",
        process_signal_generating_function_number="PT4712.01",
    )
    pif_1.add_process_signal_generating_function(psgf_1)

    pif_2.add_actuating_function(af_1)
    pif_2.add_signal_conveying_function(SignalConveyingFunction(
        dex_id="SignalConveyingFunction-1", source=pif_2, target=af_1,
    ))
    psgf_2 = ProcessSignalGeneratingFunction(
        dex_id="ProcessSignalGeneratingFunction-2",
        process_signal_generating_function_number="PT4712.02",
    )
    pif_2.add_process_signal_generating_function(psgf_2)

    pif_3 = ProcessInstrumentationFunction(
        dex_id="ProcessInstrumentationFunction-3",
        process_instrumentation_function_number="4750.01",
        process_instrumentation_function_category="H",
        process_instrumentation_functions_code="S",
    )
    af_2 = ActuatingFunction(
        dex_id="ActuatingFunction-2", actuating_function_number="HV4750.01", systems=as_2,
    )
    pif_3.add_actuating_function(af_2)
    pif_3.add_signal_conveying_function(SignalConveyingFunction(
        dex_id="SignalConveyingFunction-2", source=pif_3, target=af_2,
    ))

    pif_4 = ProcessInstrumentationFunction(
        dex_id="ProcessInstrumentationFunction-4",
        process_instrumentation_function_number="4750.03",
        process_instrumentation_function_category="T",
        process_instrumentation_functions_code="ICSA",
    )
    af_3 = ActuatingFunction(
        dex_id="ActuatingFunction-3", actuating_function_number="TV4750.03", systems=as_3,
    )
    psgf_3 = ProcessSignalGeneratingFunction(
        dex_id="ProcessSignalGeneratingFunction-3",
        process_signal_generating_function_number="TT4750.03",
        sensing_location=nozzle_17,
    )
    pif_4.add_actuating_function(af_3)
    pif_4.add_signal_conveying_function(SignalConveyingFunction(
        dex_id="SignalConveyingFunction-3", source=pif_4, target=af_3,
    ))
    pif_4.add_process_signal_generating_function(psgf_3)

    # ================= Instrumentation loop functions =================
    loop_1 = InstrumentationLoopFunction(
        dex_id="InstrumentationLoopFunction-1",
        instrumentation_loop_function_number="4712.01",
        process_instrumentation_functions=[pif_1],
    )
    loop_2 = InstrumentationLoopFunction(
        dex_id="InstrumentationLoopFunction-2",
        instrumentation_loop_function_number="4712.02",
        process_instrumentation_functions=[pif_2],
    )
    loop_3 = InstrumentationLoopFunction(
        dex_id="InstrumentationLoopFunction-3",
        instrumentation_loop_function_number="4750.01",
        process_instrumentation_functions=[pif_3],
    )
    loop_4 = InstrumentationLoopFunction(
        dex_id="InstrumentationLoopFunction-4",
        instrumentation_loop_function_number="4750.03",
        process_instrumentation_functions=[pif_4],
    )

    # ================= Root =================
    model = ConceptualModel(
        dex_id="C01-minimal",
        equipment=[phe, the, cp, rp, tank],
        piping_network_systems=lines,
        process_instrumentation_functions=[pif_1, pif_2, pif_3, pif_4],
        actuating_systems=[as_1, as_2, as_3],
        instrumentation_loop_functions=[loop_1, loop_2, loop_3, loop_4],
    )
    _apply_extras(model)
    return model


def summarize(model: ConceptualModel) -> None:
    print(f"ConceptualModel {model.dex_id!r}:")
    print(f"  equipment:   {len(model.equipment)}")
    print(f"  lines:       {len(model.piping_network_systems)}")
    print(f"  functions:   {len(model.process_instrumentation_functions)}")
    print(f"  actuating:   {len(model.actuating_systems)}")
    for item in model.equipment:
        print(f"    - {item.__class__.__name__} {item.tag_name} "
              f"({len(item.nozzles)} nozzles, {len(item.drying_chambers)} chambers)")
    for line in model.piping_network_systems:
        n_items = sum(len(s.items) for s in line.segments)
        n_conns = sum(len(s.connections) for s in line.segments)
        print(f"    - line {line.line_number}: {len(line.segments)} segments, "
              f"{n_items} items, {n_conns} connections")


if __name__ == "__main__":
    summarize(build())
