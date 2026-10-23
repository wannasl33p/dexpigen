"""Build a small model, write Proteus XML and validate it against the XSD."""

import sys
import tempfile
from pathlib import Path

from validate_dexpi import validate  # examples/validate_dexpi.py

from dexpigen import to_proteus_xml
from dexpigen.equipment import Nozzle, Tank
from dexpigen.model import ConceptualModel
from dexpigen.piping import PipingNode


def build() -> ConceptualModel:
    nozzle = Nozzle(dex_id="Nozzle-1", sub_tag_name="N1")
    nozzle.add_node(PipingNode(dex_id="PipingNode-1"))
    tank = Tank(dex_id="Tank-1", tag_name="T-101")
    tank.add_nozzle(nozzle)
    return ConceptualModel(dex_id="minimal").add_equipment(tank)


if __name__ == "__main__":
    out = Path(tempfile.gettempdir()) / "minimal.xml"
    out.write_text(to_proteus_xml(build()), encoding="utf-8")
    sys.exit(0 if validate(str(out)) else 1)
