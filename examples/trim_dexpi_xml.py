"""Produce a trimmed copy of a DEXPI Proteus XML by deleting un-serializable tags.

The result preserves the original formatting byte-for-byte for everything that
is NOT deleted (no re-serialization, no attribute edits, no value changes) —
the output is a pure subset of the input.

Usage:
    uv run python examples/trim_dexpi_xml.py <src.xml> [<dst.xml>]

Defaults to the C01 reference P&ID -> examples/c01_minimal.xml.
"""

import re
import sys

DEFAULT_SRC = (
    r"data/example_pids/C01 DEXPI Reference P&ID/C01V04-VER.EX01.xml"
)
DEFAULT_DST = r"examples/C01/ver001/c01.xml"

# Graphics / layout elements the v0.1 model has no field for.
GRAPHICS_TAGS = {
    "Position", "Scale", "Label", "Text", "PolyLine", "Shape", "Circle",
    "Presentation", "Coordinate", "CenterLine", "Extent", "Drawing",
    "DrawingBorder", "ShapeCatalogue", "PipeSlopeSymbol", "PipeFlowArrow",
    "InsulationSymbol", "Symbol", "ObjectAttributesReference",
}

# Whole objects outside the v0.1 model.
UNSUPPORTED_TAGS = {
    "MetaData", "PlantStructureItem", "InstrumentationLoopFunction",
    "ProcessSignalGeneratingFunction", "ProcessSignalGeneratingSystem",
}

# ComponentClass values (under a supported tag) that we do not model.
UNSUPPORTED_CLASSES = {
    "TubeBundle", "Impeller", "Displacer",
    "ColumnSection", "ColumnPackingsArrangement", "ColumnTraysArrangement",
    "GearBox", "MotorAsComponent", "SprayNozzle",
    "PipeTee", "BlindFlange", "SwingCheckValve", "SpringLoadedGlobeSafetyValve",
    "RestrictionOrifice", "Hose", "Compensator", "SightGlass", "Silencer",
    "SteamTrap", "PipeFlangeSpade", "PipeFlangeSpacer", "FlameArrestor",
    "RuptureDisc", "FlowMeasuringElement", "PrimaryElement", "InlinePrimaryElement",
    "VenturiTube", "FlowNozzle", "TurbineFlowMeter", "VariableAreaFlowMeter",
    "ElectromagneticFlowMeter", "MassFlowMeasuringElement",
    "VolumeFlowMeasuringElement",
    "MeasuringLineFunction", "SignalLineFunction",
    "CustomActuatingSystemComponent",
}

# Instrumentation objects whose ConnectionPoints/Node (signal nodes) we do not model.
INSTRUMENT_TAGS = {
    "ProcessInstrumentationFunction", "ProcessControlFunction",
    "InformationFlow", "ActuatingFunction", "ActuatingSystemComponent",
}

TAG_RE = re.compile(r"<[^>]*>")


def _name_of(token: str) -> str | None:
    if token.startswith("</"):
        m = re.match(r"</\s*([A-Za-z_][\w.:-]*)", token)
    else:
        m = re.match(r"<\s*([A-Za-z_][\w.:-]*)", token)
    return m.group(1) if m else None


def _attr(inner: str, name: str) -> str | None:
    m = re.search(r"\b" + name + r'="([^"]*)"', inner)
    return m.group(1) if m else None


def _drop_self(name, inner, parent) -> bool:
    if name in GRAPHICS_TAGS or name in UNSUPPORTED_TAGS:
        return True
    if _attr(inner, "ComponentClass") in UNSUPPORTED_CLASSES:
        return True
    if name == "Node" and _attr(inner, "Type") == "signal":
        return True
    if name == "ConnectionPoints" and parent in INSTRUMENT_TAGS:
        return True
    # Signal connections (InformationFlow -> actuator etc.) use signal nodes the
    # model does not represent; they are dropped together with those nodes.
    if name == "Connection" and parent in INSTRUMENT_TAGS:
        return True
    return False


def trim(src: str, dst: str) -> None:
    text = open(src, encoding="utf-8").read()

    tokens = []
    for m in TAG_RE.finditer(text):
        tok = m.group(0)
        if tok.startswith("<?") or tok.startswith("<!"):
            continue
        name = _name_of(tok)
        if name is None:
            continue
        if tok.startswith("</"):
            kind = "end"
        elif tok.endswith("/>"):
            kind = "leaf"
        else:
            kind = "start"
        inner = tok[1:-1] if not tok.startswith("</") else tok[2:-1]
        tokens.append((m.start(), m.end(), kind, name, inner))

    dropped_spans = []
    dropped_ids = set()
    stack = []  # [name, start, self_drop, ancestor_drop, id]

    def parent_tag():
        return stack[-1][0] if stack else None

    def any_drop():
        return any(e[2] or e[3] for e in stack)

    for (start, end, kind, name, inner) in tokens:
        if kind == "start":
            self_drop = _drop_self(name, inner, parent_tag())
            stack.append([name, start, self_drop, any_drop(), _attr(inner, "ID")])
        elif kind == "leaf":
            if _drop_self(name, inner, parent_tag()) or any_drop():
                dropped_spans.append((start, end))
                eid = _attr(inner, "ID")
                if eid:
                    dropped_ids.add(eid)
        elif kind == "end":
            if stack:
                name_s, start_s, self_drop, ancestor_drop, eid = stack.pop()
                if self_drop or ancestor_drop:
                    dropped_spans.append((start_s, end))
                    if eid:
                        dropped_ids.add(eid)

    # Drop references to deleted objects (dangling ItemID/FromID/ToID).
    for (start, end, kind, name, inner) in tokens:
        if kind != "leaf":
            continue
        item = _attr(inner, "ItemID")
        if item is not None and item in dropped_ids:
            dropped_spans.append((start, end))
            continue
        if name == "Connection":
            frm, to = _attr(inner, "FromID"), _attr(inner, "ToID")
            if (frm and frm in dropped_ids) or (to and to in dropped_ids):
                dropped_spans.append((start, end))

    spans = sorted(set(dropped_spans))
    merged = []
    for s in spans:
        if merged and s[0] <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], s[1]))
        else:
            merged.append(list(s))

    for s, e in reversed(merged):
        text = text[:s] + text[e:]

    # Signal nodes were removed; fix each ConnectionPoints' NumPoints to match
    # the actual number of remaining <Node> children.
    def _fix_numpoints(m: re.Match) -> str:
        open_tag, inner, close_tag = m.group(1), m.group(2), m.group(3)
        count = inner.count("<Node ")
        return re.sub(r'NumPoints="\d+"', f'NumPoints="{count}"', open_tag) + inner + close_tag

    text = re.sub(
        r"(<ConnectionPoints\b[^>]*>)(.*?)(</ConnectionPoints>)",
        _fix_numpoints,
        text,
        flags=re.DOTALL,
    )

    open(dst, "w", encoding="utf-8", newline="").write(text)
    print(f"removed {len(merged)} subtree(s) / {len(dropped_ids)} IDs -> {dst}")


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SRC
    dst = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_DST
    trim(src, dst)
