# Serialize and validate

**Goal:** turn a finished `ConceptualModel` into Proteus 4.1.1 XML and prove the file is schema-valid.

**Script:** [examples/minimal.py](../../examples/minimal.py) (also the minimal example in the [README](../../README.md)).

## Steps

1. **Build the model** and keep a function that returns it, conventionally `build() -> ConceptualModel`. The recipes and `examples/C01/build.py` all follow this shape.
2. **Serialize** with `to_proteus_xml(model)` from `dexpigen`. It returns the whole document as a string: the `PlantModel` root, a fixed `PlantInformation` header, then the top-level objects in a fixed order (actuating systems, piping network systems, PIFs, equipment, loops), each followed by its composed children.
3. **Expect model errors here.** Before writing, `to_proteus_xml` checks the model graph and raises a ValueError for an object composed twice or appended to a list in place, a `dex_id` that is not a unique XML NCName, or a reference to an object that is not composed in the model. The messages are listed in [pitfalls](../pitfalls.md).
4. **Write the string to a file** with UTF-8 encoding.
5. **Validate the file** against the bundled schema `data/schemas/ProteusPIDSchema 4.1.1.xsd`: run `uv run python examples/validate_dexpi.py <file.xml>`, or import `validate` from `examples/validate_dexpi.py` (with `examples/` on `sys.path`) and check that it returns True. Both use xmllint, which must be on PATH. A file is done only when it reports VALID.
6. **Compare with a reference file** if you are reproducing one: compare element trees, not text. The project's comparison (in `tests/test_serialization.py`) ignores whitespace, `ID` values and `ComponentName`, and compares tags, the other attributes and child order.

## What the writer does not do

- It does not validate against the XSD (step 5 does).
- It writes no graphics, no `ShapeCatalogue`, no plant structure, and the same `PlantInformation` header for every model.
- It does not read Proteus XML; there is no parser yet.

## Pitfalls

- [Validate every XML you write](../pitfalls.md#validate-every-xml-you-write)
- [Treat dex_id as the wire identity, not id](../pitfalls.md#treat-dex_id-as-the-wire-identity-not-id)
- [Compose everything you reference](../pitfalls.md#compose-everything-you-reference)
- [Compose with add methods, never by mutating a list](../pitfalls.md#compose-with-add-methods-never-by-mutating-a-list)
