"""Generate ``_extras.py``: the non-first-class GenericAttributes per object.

Reads ``ver001/c01.xml`` and, for every element with an ``ID``, emits the
``GenericAttribute`` entries that are NOT first-class model fields into
``EXTRAS`` (a dict keyed by ``dex_id``). ``build.py`` applies these to each
object's ``custom_attributes`` bag.

Run:  uv run python examples/C01/_gen_extras.py
"""

import xml.etree.ElementTree as ET

SANDBOX = "http://sandbox.dexpi.org/rdl/"

# GenericAttribute names that are first-class model fields, per object type.
# The serializer emits these from the model fields; they must not be duplicated
# in custom_attributes.
def first_class(tag: str, cc: str) -> set[str]:
    if tag == "Equipment":
        if cc == "Chamber":
            return {"SubTagNameAssignmentClass"}
        return {
            "TagNameAssignmentClass", "TagNamePrefixAssignmentClass",
            "TagNameSequenceNumberAssignmentClass", "TagNameSuffixAssignmentClass",
            "EquipmentDescriptionAssignmentClass",
        }
    if tag == "Nozzle":
        return {"SubTagNameAssignmentClass"}
    if tag == "PipingNetworkSystem":
        return {"FluidCodeAssignmentClass", "LineNumberAssignmentClass",
                "PipingClassCodeAssignmentClass"}
    if tag == "PipingNetworkSegment":
        return {"FluidCodeAssignmentClass", "PipingClassCodeAssignmentClass",
                "SegmentNumberAssignmentClass"}
    if tag == "PipingComponent":
        return {"FluidCodeAssignmentClass", "PipingComponentNameAssignmentClass",
                "PipingComponentNumberAssignmentClass",
                "PressureTestCircuitNumberAssignmentClass"}
    if tag == "ActuatingSystem":
        return {"ActuatingSystemNumberAssignmentClass", "TypicalInformationAssignmentClass"}
    if tag == "ActuatingSystemComponent":
        if cc == "ControlledActuator":
            return {"DeviceTypeNameAssignmentClass", "FailActionSpecialization",
                    "FailActionRepresentationAssignmentClass", "SubTagNameAssignmentClass"}
        if cc == "OperatedValveReference":
            return {"SubTagNameAssignmentClass"}
        if cc == "Positioner":
            return {"DeviceTypeNameAssignmentClass", "SubTagNameAssignmentClass"}
        return set()
    if tag == "ActuatingFunction":
        return {"ActuatingFunctionNumberAssignmentClass"}
    if tag == "ProcessInstrumentationFunction":
        return {
            "ProcessInstrumentationFunctionCategoryAssignmentClass",
            "ProcessInstrumentationFunctionNumberAssignmentClass",
            "ProcessInstrumentationFunctionModifierAssignmentClass",
            "ProcessInstrumentationFunctionsAssignmentClass",
        }
    return set()


def main() -> None:
    tree = ET.parse("examples/C01/ver001/c01.xml")
    extras: dict[str, list[str]] = {}

    def walk(elem: ET.Element) -> None:
        eid = elem.get("ID")
        ga_blocks = elem.findall("GenericAttributes")
        if eid is not None and ga_blocks:
            fc = first_class(elem.tag, elem.get("ComponentClass", ""))
            for ga in ga_blocks:
                for a in ga.findall("GenericAttribute"):
                    name = a.get("Name")
                    if name in fc:
                        continue
                    parts = [f"name={name!r}"]
                    value = a.get("Value")
                    if value is not None:
                        parts.append(f"value={value!r}")
                    fmt = a.get("Format", "string")
                    if fmt != "string":
                        parts.append(f"format={fmt!r}")
                    uri = a.get("AttributeURI")
                    if uri and uri != SANDBOX + name:
                        parts.append(f"attribute_uri={uri!r}")
                    if a.get("Units"):
                        parts.append(f"units={a.get('Units')!r}")
                    if a.get("UnitsURI"):
                        parts.append(f"units_uri={a.get('UnitsURI')!r}")
                    if a.get("ValueURI"):
                        parts.append(f"value_uri={a.get('ValueURI')!r}")
                    if a.get("Language"):
                        parts.append(f"language={a.get('Language')!r}")
                    extras.setdefault(eid, []).append("CustomAttribute(" + ", ".join(parts) + ")")
        for child in elem:
            walk(child)

    for child in tree.getroot():
        walk(child)

    lines = [
        '"""Auto-generated extra GenericAttributes for the C01 fixture.',
        "",
        "Do not edit by hand — regenerate with ``examples/C01/_gen_extras.py``.",
        '"""',
        "",
        "from dexpigen.base import CustomAttribute",
        "",
        "EXTRAS: dict[str, list[CustomAttribute]] = {",
    ]
    for eid in sorted(extras):
        lines.append(f"    {eid!r}: [")
        for entry in extras[eid]:
            lines.append(f"        {entry},")
        lines.append("    ],")
    lines.append("}")
    lines.append("")

    with open("examples/C01/_extras.py", "w", encoding="utf-8", newline="") as f:
        f.write("\n".join(lines))
    total = sum(len(v) for v in extras.values())
    print(f"wrote {len(extras)} objects / {total} extra attributes")


if __name__ == "__main__":
    main()
