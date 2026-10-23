"""Recipe: data without a first-class field, via ``CustomAttribute``; ``component_name``.

Every object has a ``custom_attributes`` bag; each ``CustomAttribute`` is
written as one Proteus ``<GenericAttribute>`` next to the first-class fields.
``component_name`` sets the Proteus ``ComponentName`` attribute (a shape name,
not DEXPI data).

Guide: docs/recipes/custom-attributes.md
Run:   uv run python examples/recipes/custom_attributes.py
"""

import sys
import tempfile
from pathlib import Path

from dexpigen import CustomAttribute, to_proteus_xml
from dexpigen.equipment import Chamber, Nozzle, Tank
from dexpigen.instrumentation import ProcessInstrumentationFunction
from dexpigen.model import ConceptualModel
from dexpigen.piping import PipeTee, PipingNetworkSegment, PipingNetworkSystem, PipingNode

RDS = "http://data.posccaesar.org/rdl/"


def build() -> ConceptualModel:
    # A physical quantity: format "double" plus units. attribute_uri defaults to
    # http://sandbox.dexpi.org/rdl/<name>.
    tank = Tank(dex_id="Tank-1", tag_name="T4750")
    tank.add_custom_attribute(CustomAttribute(
        name="NominalCapacity(Volume)", value="26", format="double",
        units="MetreCubed", units_uri=RDS + "RDS1349099",
    ))
    # A plain string attribute; set attribute_uri when the RDL uses another URI.
    chamber = Chamber(dex_id="Chamber-1", sub_tag_name="Chamber 1")
    chamber.add_custom_attribute(CustomAttribute(
        name="MaterialOfConstructionCodeAssignmentClass", value="1.4306",
        attribute_uri=RDS + "RDS1460719741",
    ))
    tank.add_drying_chamber(chamber)

    # Bags exist on every object, including connection nodes.
    node = PipingNode(dex_id="PipingNode-1")
    node.add_custom_attribute(CustomAttribute(
        name="NominalDiameterNumericalValueRepresentationAssignmentClass", value="80",
    ))
    nozzle = Nozzle(dex_id="Nozzle-1", sub_tag_name="N1")
    nozzle.add_node(node)
    tank.add_nozzle(nozzle)

    # component_name is a Proteus wire attribute (a shape-library name).
    tee = PipeTee(dex_id="PipeTee-1", flow_in_index=1, component_name="T_TYPE_CONNECTION_SHAPE")
    for i in (2, 3, 4):
        tee.add_node(PipingNode(dex_id=f"PipingNode-{i}"))
    tee.add_custom_attribute(CustomAttribute(name="PipingClassCodeAssignmentClass", value="75HB13"))
    line = PipingNetworkSystem(
        dex_id="PipingNetworkSystem-1",
        segments=[PipingNetworkSegment(dex_id="PipingNetworkSegment-1", items=[tee])],
    )

    # An enumerated (anyURI) value carries both the value and its URI.
    pif = ProcessInstrumentationFunction(
        dex_id="ProcessInstrumentationFunction-1", process_instrumentation_function_category="L",
    )
    pif.add_custom_attribute(CustomAttribute(
        name="LocationSpecialization", format="anyURI", value="CentralLocation",
        value_uri="http://sandbox.dexpi.org/rdl/CentralLocation",
    ))
    return (
        ConceptualModel(dex_id="custom-attributes")
        .add_equipment(tank)
        .add_piping_network_system(line)
        .add_process_instrumentation_function(pif)
    )


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # examples/
    from validate_dexpi import validate

    out = Path(tempfile.gettempdir()) / "custom_attributes.xml"
    out.write_text(to_proteus_xml(build()), encoding="utf-8")
    sys.exit(0 if validate(str(out)) else 1)
