"""Generate the class index under ``docs/reference/`` from the dexpigen code.

Run:  uv run python scripts/gen_reference.py

Every ``DexpiBaseModel`` subclass, every ``StrEnum`` and ``CustomAttribute``
is introspected from an explicit module list (not all of ``dexpigen.*``: the
untracked ``dexpigen.entities`` package cannot be imported). Output is
deterministic: classes follow the inheritance tree (root, then descendants
depth-first, siblings in definition order), with no timestamps.
``tests/test_reference_docs.py`` regenerates it in memory and fails when the
committed files are stale or a model-typed field lacks a ``Composed``/``Ref``
marker.
"""

from __future__ import annotations

import inspect
import re
import sys
import types
import typing
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from pydantic_core import PydanticUndefined

from dexpigen import base, enumerations, equipment, instrumentation, model, piping
from dexpigen.base import Composed, CustomAttribute, DexpiBaseModel, Ref, relation_of
from dexpigen.equipment import Equipment

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "reference"
REGENERATE = "uv run python scripts/gen_reference.py"

# Output file -> (title, one-line summary, modules it documents, in order).
FILES: dict[str, tuple[str, str, list[types.ModuleType]]] = {
    "model.md": (
        "Model root and shared base",
        "`ConceptualModel` (the root), `DexpiBaseModel` (every object's base) and `CustomAttribute`.",
        [base, model],
    ),
    "equipment.md": (
        "Equipment classes",
        "The `Equipment` tree, `Nozzle`, `Chamber` and `CustomEquipment`.",
        [equipment],
    ),
    "piping.md": (
        "Piping classes",
        "Piping network systems and segments, connections, nodes, valves, fittings and off-page connectors.",
        [piping],
    ),
    "instrumentation.md": (
        "Instrumentation classes",
        "Instrumentation functions, the control-valve assembly, signals, sensing and loops.",
        [instrumentation],
    ),
    "enumerations.md": (
        "Enumerations",
        "The DEXPI enumerations used by model fields, with their members.",
        [enumerations],
    ),
}

LEAF_TABLE_HEADING = "Equipment leaves without own fields"


def _documented(obj: Any) -> bool:
    if not inspect.isclass(obj):
        return False
    if issubclass(obj, StrEnum) and obj is not StrEnum:
        return True
    return obj is CustomAttribute or issubclass(obj, DexpiBaseModel)


def _classes(module: types.ModuleType) -> list[type]:
    """Documented classes defined in ``module``, in definition order."""
    found = [
        obj for obj in vars(module).values()
        if _documented(obj) and obj.__module__ == module.__name__
    ]
    for cls in found:
        if issubclass(cls, BaseModel) and not cls.__pydantic_complete__:
            cls.model_rebuild()
    return found


def _all_classes() -> dict[type, str]:
    """Every documented class mapped to the output file that documents it."""
    return {
        cls: filename
        for filename, (_, _, modules) in FILES.items()
        for module in modules
        for cls in _classes(module)
    }


def _anchor(cls: type) -> str:
    return cls.__name__.lower()


def _is_equipment_leaf(cls: type, everything: dict[type, str]) -> bool:
    if not (issubclass(cls, Equipment) and cls is not Equipment):
        return False
    if _own_fields(cls):
        return False
    return not any(other is not cls and cls in other.__bases__ for other in everything)


def _link(cls: type, here: str, everything: dict[type, str]) -> str:
    filename = everything.get(cls)
    if filename is None:
        return cls.__name__
    target = f"#{_anchor(cls)}"
    if _is_equipment_leaf(cls, everything):
        target = "#" + LEAF_TABLE_HEADING.lower().replace(" ", "-")
    if filename != here:
        target = filename + target
    return f"[{cls.__name__}]({target})"


def _type(tp: Any, here: str, everything: dict[type, str]) -> str:
    """Render a resolved field annotation as Markdown (table-cell safe)."""
    if tp is type(None):
        return "None"
    origin = typing.get_origin(tp)
    if origin in (typing.Union, types.UnionType):
        return " \\| ".join(_type(arg, here, everything) for arg in typing.get_args(tp))
    if origin is not None:
        args = ", ".join(_type(arg, here, everything) for arg in typing.get_args(tp))
        return f"{origin.__name__}[{args}]"
    if inspect.isclass(tp):
        return _link(tp, here, everything)
    return str(tp)


def _default(info: Any) -> str:
    if info.default_factory is list:
        return "`[]`"
    if info.default_factory is not None:
        return "generated"
    if info.default is PydanticUndefined:
        return "required"
    if isinstance(info.default, StrEnum):
        return f"`{info.default.value!r}`"
    return f"`{info.default!r}`"


def _relation(info: Any) -> str:
    relation = relation_of(info.metadata)
    if relation is Composed:
        return "composed"
    if relation is Ref:
        return "ref"
    return ""


def _own_fields(cls: type) -> list[str]:
    if not issubclass(cls, BaseModel):
        return []
    own = cls.__dict__.get("__annotations__", {})
    return [name for name in cls.model_fields if name in own]


def _summary(obj: Any) -> str:
    """First paragraph of the object's own docstring, on one line."""
    doc = obj.__dict__.get("__doc__")
    if not doc:
        return ""
    paragraph = inspect.cleandoc(doc).split("\n\n", 1)[0]
    text = " ".join(paragraph.split())
    return re.sub(r"``([^`]+)``", r"`\1`", text)


def _tree(classes: list[type]) -> list[tuple[type, int]]:
    """``classes`` in inheritance-tree order, each with its depth.

    A class's tree parent is its first base documented in the same file; a
    class with none is a root. Roots and siblings keep definition order.
    """
    members = set(classes)

    def parent(cls: type) -> type | None:
        return next((b for b in cls.__bases__ if b in members), None)

    children: dict[type | None, list[type]] = {}
    for cls in classes:
        children.setdefault(parent(cls), []).append(cls)

    ordered: list[tuple[type, int]] = []

    def walk(node: type | None, depth: int) -> None:
        for child in children.get(node, []):
            ordered.append((child, depth))
            walk(child, depth + 1)

    walk(None, 0)
    return ordered


def _class_section(cls: type, here: str, everything: dict[type, str]) -> list[str]:
    lines = [f"### {cls.__name__}", ""]
    summary = _summary(cls)
    if summary:
        lines += [summary, ""]
    component_class = getattr(cls, "component_class", "")
    component_class_uri = getattr(cls, "component_class_uri", "")
    bases = [b for b in cls.__bases__ if b in everything] or list(cls.__bases__)
    lines += [
        f"- ComponentClass: {f'`{component_class}`' if component_class else '-'}",
        f"- ComponentClassURI: {f'`{component_class_uri}`' if component_class_uri else '-'}",
        "- Bases: " + ", ".join(_link(b, here, everything) for b in bases),
        f"- Abstract: {'yes' if getattr(cls, '_abstract', False) else 'no'}",
        "",
    ]
    fields = _own_fields(cls)
    if not fields:
        return lines + ["No own fields.", ""]
    lines += ["| Field | Type | Default | Relation |", "| --- | --- | --- | --- |"]
    for name in fields:
        info = cls.model_fields[name]
        lines.append(
            f"| `{name}` | {_type(info.annotation, here, everything)} "
            f"| {_default(info)} | {_relation(info)} |"
        )
    return lines + [""]


def _enum_section(cls: type[StrEnum]) -> list[str]:
    lines = [f"### {cls.__name__}", ""]
    summary = _summary(cls)
    if summary:
        lines += [summary, ""]
    lines += ["| Member | Value |", "| --- | --- |"]
    lines += [f"| `{member.name}` | `{member.value}` |" for member in cls]
    return lines + [""]


def _render_file(filename: str, everything: dict[type, str]) -> str:
    title, summary, modules = FILES[filename]
    names = ", ".join(f"`{m.__name__}`" for m in modules)
    classes = [cls for module in modules for cls in _classes(module)]
    tree = _tree(classes)
    sections = [(cls, depth) for cls, depth in tree if not _is_equipment_leaf(cls, everything)]
    leaves = [cls for cls, _ in tree if _is_equipment_leaf(cls, everything)]

    lines = [
        f"# {title}",
        "",
        summary,
        "",
        f"Generated from {names} by `scripts/gen_reference.py`; do not edit by hand.",
        "",
        "## Contents",
        "",
    ]
    lines += [
        f"{'  ' * depth}- [{cls.__name__}](#{_anchor(cls)})" for cls, depth in sections
    ]
    if leaves:
        anchor = LEAF_TABLE_HEADING.lower().replace(" ", "-")
        lines.append(f"- [{LEAF_TABLE_HEADING}](#{anchor})")
    lines += ["", "## Classes", ""]
    for cls, _ in sections:
        if issubclass(cls, StrEnum):
            lines += _enum_section(cls)
        else:
            lines += _class_section(cls, filename, everything)
    if leaves:
        lines += [
            f"## {LEAF_TABLE_HEADING}",
            "",
            "Concrete equipment classes with no subclasses and no fields of their own.",
            "",
            "| Class | Parent | ComponentClass | ComponentClassURI |",
            "| --- | --- | --- | --- |",
        ]
        for cls in leaves:
            parent = cls.__bases__[0]
            lines.append(
                f"| `{cls.__name__}` | {_link(parent, filename, everything)} "
                f"| `{cls.component_class}` | `{cls.component_class_uri}` |"
            )
        lines.append("")
    return "\n".join(lines)


def _render_index() -> str:
    lines = [
        "# Class index",
        "",
        "Generated by `scripts/gen_reference.py` from the dexpigen code; do not edit by hand.",
        "Each file lists its classes in inheritance-tree order with their DEXPI `ComponentClass`,",
        "bases, abstractness and own fields. The Relation column says whether a field",
        "composes its value (`composed`) or references an object owned elsewhere (`ref`).",
        "",
    ]
    lines += [
        f"- [{title}]({filename}): {summary}"
        for filename, (title, summary, _) in FILES.items()
    ]
    return "\n".join(lines) + "\n"


def render() -> dict[str, str]:
    """Return every generated file as ``{filename: content}``."""
    everything = _all_classes()
    out = {"index.md": _render_index()}
    for filename in FILES:
        out[filename] = _render_file(filename, everything)
    return out


def _model_types(tp: Any) -> list[type]:
    origin = typing.get_origin(tp)
    if origin is None:
        return [tp] if inspect.isclass(tp) and issubclass(tp, DexpiBaseModel) else []
    return [found for arg in typing.get_args(tp) for found in _model_types(arg)]


def unmarked_fields() -> list[str]:
    """``Class.field`` for every model-typed field without a ``Composed``/``Ref`` marker."""
    missing: list[str] = []
    for cls in _all_classes():
        if not (inspect.isclass(cls) and issubclass(cls, DexpiBaseModel)):
            continue
        for name in _own_fields(cls):
            info = cls.model_fields[name]
            if _model_types(info.annotation) and relation_of(info.metadata) is None:
                missing.append(f"{cls.__name__}.{name}")
    return missing


def main() -> int:
    missing = unmarked_fields()
    if missing:
        print("fields without a Composed/Ref marker: " + ", ".join(missing), file=sys.stderr)
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for filename, content in render().items():
        (OUT_DIR / filename).write_text(content, encoding="utf-8", newline="\n")
        print(f"wrote {(OUT_DIR / filename).relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
