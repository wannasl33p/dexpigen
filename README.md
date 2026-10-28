# dexpigen

A Python 3.13 / Pydantic v2 library that holds a DEXPI P&ID 1.3 conceptual model in memory as a typed object graph and writes it as Proteus XML; it is not a drawing, not a NetworkX graph and not a Proteus parser.

## Scope and limits

- **Writes only.** `to_proteus_xml` turns a `ConceptualModel` into a Proteus 4.1.1 XML string. There is no reader: Proteus or DEXPI XML cannot be loaded back into the model yet.
- **Optional graphics, no symbol library.** Drawn items can carry a `position` and an `outline`, pipes and signals a `center_line`, the model a `drawing_extent` (sheet millimetres, y up); they are written as `Position`, inline `PolyLine`, `CenterLine` and `Drawing`. There is no `ShapeCatalogue`, no labels or text, and the `PlantInformation` header is the same fixed one for every model.
- **Covered DEXPI areas:** the equipment tree (98 concrete classes, the fallback `CustomEquipment` included), nozzles and chambers; piping network systems, segments, connections and nodes; operated, check and safety valves, pipe fittings (`PipeTee`, `PipeReducer`, `Flange`, `LineBlind`), `FlowMeasuringElement` and pipe off-page connectors; process instrumentation functions with sensing functions, signals, the control-valve assembly (`ActuatingSystem`, `ActuatingFunction`) and instrumentation loops.
- **Everything else** is carried as generic attributes (`CustomAttribute`) or is out of scope (plant structure, equipment internals such as column sections, most fitting and valve leaves, primary elements).
- **Checked, not schema-validated.** Constructors and `add_*` methods enforce ownership and reference types; `to_proteus_xml` checks the whole graph before writing. Schema validity is proven separately with the bundled XSD.
- **Dex extraction in.** `dexpigen.entities` takes the ML pipeline's output: the Dex graph (NetworkX), its Entities (`SymbolEntity`, `EquipmentEntity`, `SegmentEntity`) and the `DrawingSize`, all in image pixels. `check_extraction` checks them against the input contract and raises one `DexExtractionError` that lists every problem. `dex_to_model` converts them into a `ConceptualModel` with graphics and returns a `DexConversion` whose `report` names everything skipped or assumed; `dex_to_proteus` goes straight to XML. Classes are coarse: the label picks the family root (`CustomEquipment`, `OperatedValve`), since no text is read.

## Install and commands

The project uses [uv](https://docs.astral.sh/uv/). Validation needs `xmllint` (libxml2) on PATH.

```bash
uv sync                                                # create the environment
uv run pytest                                          # run the tests
uv run python examples/minimal.py                      # build, write and validate a small model
uv run python examples/validate_dexpi.py <file.xml>    # validate any Proteus XML against the XSD
uv run python scripts/gen_reference.py                 # regenerate docs/reference after a code change
uv run python examples/C01/dex_model/load.py           # check the C01 Dex sample and convert it to XML
```

Import classes from their modules: `dexpigen.equipment`, `dexpigen.piping`, `dexpigen.instrumentation`, `dexpigen.model` (`ConceptualModel`), `dexpigen.enumerations`; `to_proteus_xml` and `CustomAttribute` also come from `dexpigen`. The Dex extraction input comes from `dexpigen.entities`.

## Minimal example

A tank with one nozzle, written to Proteus XML and validated (this is `examples/minimal.py`):

```python
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
```

Every object takes a `dex_id`: it becomes the Proteus `ID`, so it must be unique and NCName-shaped. Children are composed with `add_*` methods (or constructor lists); references are plain fields holding the same Python object.

## Documentation

Read this file, then the recipe for your task, then the pitfalls; open the class index and the glossary when you need a detail.

- [Equipment and nozzles](docs/recipes/equipment-and-nozzles.md): when modelling equipment, nozzles, chambers and nozzle-in-chamber locations.
- [Piping network](docs/recipes/piping-network.md): when modelling lines, segments, valves, fittings, off-page connectors and the pipes between them.
- [Measurement](docs/recipes/measurement.md): when modelling an instrument bubble, its sensor and location, signals and loops.
- [Control valve](docs/recipes/control-valve.md): when modelling a controlled valve with its actuating system and actuating function.
- [Custom attributes](docs/recipes/custom-attributes.md): when a value has no first-class field, or for the Proteus `ComponentName`.
- [Serialize and validate](docs/recipes/serialize-and-validate.md): when writing the XML, validating it, or comparing it with a reference file.
- [Pitfalls](docs/pitfalls.md): before writing model code, and whenever an error message appears.
- [Class index](docs/reference/index.md): to look up a class, its `ComponentClass`, its fields and whether each field composes or references.
- [Glossary](CONTEXT.md): when a DEXPI or project term is unclear.
- [C01 reference P&ID build](examples/C01/build.py): for a large real example that reproduces most of the DEXPI C01 reference P&ID.
- [Dex extraction](src/dexpigen/entities/convert.py): when turning the ML pipeline's Dex graph and Entities into a model or XML; its docstring lists the mapping rules, `src/dexpigen/entities/extraction.py` the graph conventions, and `examples/C01/dex_model/load.py` converts a real sample.
