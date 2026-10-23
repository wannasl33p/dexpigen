"""Recipe: a control valve: operated valve, actuating system and actuating function.

DEXPI splits a control valve into four related objects: the ``GlobeValve``
(an ``OperatedValve``) in its segment, an ``ActuatingSystem`` composing the
``ControlledActuator``, an ``OperatedValveReference`` to the valve and an
optional ``Positioner``, and an ``ActuatingFunction`` composed under the
controlling PIF. A signal runs from the PIF to the actuating function.

Guide: docs/recipes/control-valve.md
Run:   uv run python examples/recipes/control_valve.py
"""

import sys
import tempfile
from pathlib import Path

from dexpigen import to_proteus_xml
from dexpigen.enumerations import FailActionClassification
from dexpigen.instrumentation import (
    ActuatingFunction,
    ActuatingSystem,
    ControlledActuator,
    OperatedValveReference,
    Positioner,
    ProcessInstrumentationFunction,
    SignalConveyingFunction,
)
from dexpigen.model import ConceptualModel
from dexpigen.piping import GlobeValve, PipingNetworkSegment, PipingNetworkSystem, PipingNode


def build() -> ConceptualModel:
    # 1. The valve itself sits in a segment like any other piping component.
    valve = GlobeValve(dex_id="GlobeValve-1", piping_component_number="C1",
                       flow_in_index=1, flow_out_index=2)
    valve.add_node(PipingNode(dex_id="PipingNode-1"))
    valve.add_node(PipingNode(dex_id="PipingNode-2"))
    segment = PipingNetworkSegment(dex_id="PipingNetworkSegment-1", items=[valve])
    line = PipingNetworkSystem(dex_id="PipingNetworkSystem-1", segments=[segment])

    # 2. The physical assembly; OperatedValveReference accepts an OperatedValve only.
    system = ActuatingSystem(dex_id="ActuatingSystem-1", actuating_system_number="TV4750.03")
    system.add_controlled_actuator(ControlledActuator(
        dex_id="ControlledActuator-1", device_type_name="general",
        fail_action=FailActionClassification.FAIL_OPEN, fail_action_representation="F.O.",
        sub_tag_name="TV4750.03_YC",
    ))
    system.add_operated_valve_reference(OperatedValveReference(
        dex_id="OperatedValveReference-1", sub_tag_name="TV4750.03_YV", valve=valve,
    ))
    system.add_positioner(Positioner(dex_id="Positioner-1", sub_tag_name="TV4750.03_ZC"))

    # 3. The control function: composed under the PIF, referencing the assembly.
    pif = ProcessInstrumentationFunction(
        dex_id="ProcessInstrumentationFunction-1",
        process_instrumentation_function_number="4750.03",
        process_instrumentation_function_category="T",
        process_instrumentation_functions_code="IC",
    )
    actuating = ActuatingFunction(
        dex_id="ActuatingFunction-1", actuating_function_number="TV4750.03", systems=system,
    )
    pif.add_actuating_function(actuating)
    pif.add_signal_conveying_function(SignalConveyingFunction(
        dex_id="SignalConveyingFunction-1", source=pif, target=actuating,
    ))

    # ActuatingSystem and the PIF are top-level; the ActuatingFunction is not.
    return (
        ConceptualModel(dex_id="control-valve")
        .add_piping_network_system(line)
        .add_actuating_system(system)
        .add_process_instrumentation_function(pif)
    )


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # examples/
    from validate_dexpi import validate

    out = Path(tempfile.gettempdir()) / "control_valve.xml"
    out.write_text(to_proteus_xml(build()), encoding="utf-8")
    sys.exit(0 if validate(str(out)) else 1)
