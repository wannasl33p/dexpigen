"""Recipe: equipment, nozzles, chambers, and nozzles located in a chamber.

Guide: docs/recipes/equipment-and-nozzles.md
Run:   uv run python examples/recipes/equipment_and_nozzles.py
"""

import sys
import tempfile
from pathlib import Path

from dexpigen import to_proteus_xml
from dexpigen.equipment import (
    CentrifugalPump,
    Chamber,
    Nozzle,
    PlateHeatExchanger,
    ReciprocatingPump,
    Tank,
    TubularHeatExchanger,
)
from dexpigen.model import ConceptualModel
from dexpigen.piping import PipingNode


def nozzle(dex_id: str, sub_tag_name: str, node_id: str, chamber: Chamber | None = None) -> Nozzle:
    """A nozzle with one process node: the point a pipe connects to."""
    result = Nozzle(dex_id=dex_id, sub_tag_name=sub_tag_name, chamber=chamber)
    result.add_node(PipingNode(dex_id=node_id))
    return result


def build() -> ConceptualModel:
    # Concrete equipment class, tag split into its parts; every field is optional.
    pump = CentrifugalPump(
        dex_id="CentrifugalPump-1", tag_name="P4711",
        tag_name_prefix="P", tag_name_sequence_number="4711", tag_name_suffix="",
    )
    pump.add_nozzle(nozzle("Nozzle-1", "N1", "PipingNode-1"))
    pump.add_nozzle(nozzle("Nozzle-2", "N2", "PipingNode-2"))

    dosing_pump = ReciprocatingPump(dex_id="ReciprocatingPump-1", tag_name="P4712")
    dosing_pump.add_nozzle(nozzle("Nozzle-3", "N1", "PipingNode-3"))

    # Chambers are composed first: a nozzle may only sit in a chamber of its own equipment.
    plate_side_1 = Chamber(dex_id="Chamber-1", sub_tag_name="Chamber 1")
    plate_side_2 = Chamber(dex_id="Chamber-2", sub_tag_name="Chamber 2")
    exchanger = PlateHeatExchanger(dex_id="PlateHeatExchanger-1", tag_name="H1007")
    exchanger.add_drying_chamber(plate_side_1)
    exchanger.add_drying_chamber(plate_side_2)
    exchanger.add_nozzle(nozzle("Nozzle-4", "N1", "PipingNode-4", chamber=plate_side_1))
    exchanger.add_nozzle(nozzle("Nozzle-5", "N2", "PipingNode-5", chamber=plate_side_1))
    exchanger.add_nozzle(nozzle("Nozzle-6", "N3", "PipingNode-6", chamber=plate_side_2))

    # Constructor composition follows the same ownership rules as add_*.
    shell = Chamber(dex_id="Chamber-3", sub_tag_name="Shell")
    tubular = TubularHeatExchanger(
        dex_id="TubularHeatExchanger-1", tag_name="H1008", drying_chambers=[shell],
    )
    tubular.add_nozzle(nozzle("Nozzle-7", "N1", "PipingNode-7", chamber=shell))

    tank = Tank(dex_id="Tank-1", tag_name="T4750", equipment_description="Buffer tank")
    tank.add_nozzle(nozzle("Nozzle-8", "N1", "PipingNode-8"))

    return ConceptualModel(
        dex_id="equipment-and-nozzles",
        equipment=[pump, dosing_pump, exchanger, tubular, tank],
    )


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # examples/
    from validate_dexpi import validate

    out = Path(tempfile.gettempdir()) / "equipment_and_nozzles.xml"
    out.write_text(to_proteus_xml(build()), encoding="utf-8")
    sys.exit(0 if validate(str(out)) else 1)
