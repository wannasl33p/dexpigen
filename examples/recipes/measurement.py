"""Recipe: a measurement: PIF, its sensing function, a signal and a loop.

A temperature transmitter on a tank nozzle: the ``ProcessInstrumentationFunction``
(the bubble) composes a ``ProcessSignalGeneratingFunction`` located in the
nozzle and a ``SignalConveyingFunction`` from the sensor to the bubble. An
``InstrumentationLoopFunction`` collects the PIF by reference.

Guide: docs/recipes/measurement.md
Run:   uv run python examples/recipes/measurement.py
"""

import sys
import tempfile
from pathlib import Path

from dexpigen import to_proteus_xml
from dexpigen.equipment import Nozzle, Tank
from dexpigen.instrumentation import (
    InstrumentationLoopFunction,
    ProcessInstrumentationFunction,
    ProcessSignalGeneratingFunction,
    SignalConveyingFunction,
)
from dexpigen.model import ConceptualModel
from dexpigen.piping import PipingNode


def build() -> ConceptualModel:
    # The sensing location must be composed in the model (here: a tank nozzle).
    probe_nozzle = Nozzle(dex_id="Nozzle-1", sub_tag_name="N7")
    probe_nozzle.add_node(PipingNode(dex_id="PipingNode-1"))
    tank = Tank(dex_id="Tank-1", tag_name="T4750")
    tank.add_nozzle(probe_nozzle)

    # The bubble: its tag is split into number, category and functions code.
    pif = ProcessInstrumentationFunction(
        dex_id="ProcessInstrumentationFunction-1",
        process_instrumentation_function_number="4750.03",
        process_instrumentation_function_category="T",
        process_instrumentation_functions_code="I",
    )
    # The sensor is composed under the PIF and references (not owns) its location.
    sensor = ProcessSignalGeneratingFunction(
        dex_id="ProcessSignalGeneratingFunction-1",
        process_signal_generating_function_number="TT4750.03",
        sensing_location=probe_nozzle,
    )
    pif.add_process_signal_generating_function(sensor)
    # A signal line is composed under a PIF too; source/target are references.
    pif.add_signal_conveying_function(SignalConveyingFunction(
        dex_id="SignalConveyingFunction-1", source=sensor, target=pif,
    ))

    # The loop references the PIF; the PIF is still added at the top level.
    loop = InstrumentationLoopFunction(
        dex_id="InstrumentationLoopFunction-1",
        instrumentation_loop_function_number="4750.03",
        process_instrumentation_functions=[pif],
    )
    return (
        ConceptualModel(dex_id="measurement")
        .add_equipment(tank)
        .add_process_instrumentation_function(pif)
        .add_instrumentation_loop_function(loop)
    )


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # examples/
    from validate_dexpi import validate

    out = Path(tempfile.gettempdir()) / "measurement.xml"
    out.write_text(to_proteus_xml(build()), encoding="utf-8")
    sys.exit(0 if validate(str(out)) else 1)
