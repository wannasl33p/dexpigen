# Decide the generated class index

Type: grilling
Status: resolved
Blocked by: 02-doc-set-layout
Assignee: alex.valentsinovich

## Question

What is generated from the code so it cannot drift: per class its DEXPI name, `ComponentClass`/URI, fields and types, role bases, abstractness, composition vs reference, and the "extraction type → class" lookup with its fallbacks (`CustomEquipment`, valve family roots)? Decide the output format, the generator's home and invocation, and how a stale index is detected.

## Answer

Resolved by grilling on 2026-10-23. No ADR: every choice is cheap to reverse.

- **Composition vs reference comes from an explicit per-field marker in the code** (`Annotated[list[Nozzle], Composed]`, `Annotated[PipingNode | None, Ref]`). It can't be inferred: `PipingNode` is composed in `PipingNodeOwner.nodes` but referenced in `Pipe.source_node`. The generator's test fails when a field typed with a `DexpiBaseModel` subclass (bare, in `list[...]`, or `| None`) has no marker. Adding the markers is a code change for the implementation subagent. Glossary terms: **Composition** and **Reference** (added to `CONTEXT.md`).
- **Contents, all introspected:** every `DexpiBaseModel` subclass under `dexpigen.*` (abstract roles and all equipment leaves included), every `StrEnum` with its members, and `CustomAttribute`. Per class: Python name, DEXPI `ComponentClass` and URI (empty for `Pipe`/`PipingNode`; can differ from the Python name, e.g. `LoadingUnloadingSystem` -> `Loading-UnloadingSystem`), bases as links, abstract yes/no, first docstring line, and a table of **own** fields only (name | type | default | composed/ref). Functions (`to_proteus_xml`) are not indexed; the README and recipes cover them.
- **Not in the index:** wire names (`TagNameAssignmentClass`, `<Connection>`, ...). They live in the serializer's `isinstance` chain and can't be generated without a serializer refactor. Deferred to the reader fog. Agents check wire output against `examples/C01/verNNN/c01.xml` and `examples/validate_dexpi.py`.
- **Extraction type -> class lookup is not generated.** No code holds it; it's a naming rule. It is hand-written in `docs/pitfalls.md` (or a mapping recipe; ticket 04 decides): same-name concrete class; unmatched equipment type -> `CustomEquipment` with `source_type_label`; unspecified valve -> `OperatedValve` / `CheckValve` / `SafetyValveOrFitting`. The generated index lists every concrete class, so the name-match set itself can't drift. A library lookup API is out of scope.
- **Layout:** one file per module: `docs/reference/equipment.md`, `piping.md`, `instrumentation.md`, `model.md`, `enumerations.md`, plus a short `docs/reference/index.md` (modules + one line each) with a TOC per file. Classes appear in inheritance-tree order (root, then descendants depth-first, siblings in module definition order). Equipment leaves with no own fields go into one compact table in the same tree order: class | parent | ComponentClass | URI.
- **Generator:** `scripts/gen_reference.py`, run with `uv run python scripts/gen_reference.py`; writes `docs/reference/`. Not part of the package, not in the wheel.
- **Stale detection:** `tests/test_reference_docs.py` runs the generator in memory and compares with the committed files. On mismatch it fails with the regeneration command. Output is deterministic (fixed ordering, no timestamps). The broader docs-vs-code sync (recipes, size budgets, README example) stays in the fog.
