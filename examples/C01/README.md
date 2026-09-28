# C01 — versioned recovery of the reference P&ID

We grow the model toward **fully covering** the original DEXPI reference P&ID
`data/example_pids/C01 DEXPI Reference P&ID/C01V04-VER.EX01.xml`.

The mechanism is a sequence of version snapshots. Each version says: *this is
what the model can serialize at this milestone*. Early versions are heavily
trimmed (graphics and out-of-scope classes deleted); later versions keep more,
until one version is byte-equivalent to the original.

## Layout

```
examples/C01/
  build.py            # builds the in-memory ConceptualModel for the latest version
  ver001/
    c01.xml           # expected serialization of build() at version 1
  ver002/ ...         # next milestone, once the model grows
```

- `build.py` always builds the **latest** milestone's model.
- `verNNN/c01.xml` is the **golden reference**: `serialize(build()) == verNNN/c01.xml`.
- Earlier `verNNN/` folders are kept as historical snapshots.

## How a new version is produced

1. Grow the model (add classes / fields) so it can hold more of the original C01.
2. Regenerate the trimmed reference for the new coverage:
   ```bash
   uv run python examples/trim_dexpi_xml.py \
     "data/example_pids/C01 DEXPI Reference P&ID/C01V04-VER.EX01.xml" \
     examples/C01/verNNN/c01.xml
   ```
   `trim_dexpi_xml.py` deletes only the tags the model cannot yet represent.
3. Update `build.py` to build the corresponding model.
4. Validate the result (see below) and update the test if needed.

## Validation rule

After **every generation**, validate against the bundled XSD:

```bash
uv run python examples/validate_dexpi.py examples/C01/verNNN/c01.xml
```

This wraps `xmllint --noout --schema data/schemas/ProteusPIDSchema 4.1.1.xsd <xml>`.
The same rule is enforced by `tests/test_serialization.py`.

## Known gaps at ver001 (what still needs model growth)

- `Chamber` serializes as `ComponentClass="Chamber"` (fixed); the chamber subtypes
  are not modeled.
- `PipingNetworkSegment` has `fluid_code` / `piping_class_code` (added at ver001).
- Nozzle nominal-diameter fields and other non-first-class data would map to
  `CustomAttribute` bags (writer concern, not yet in the model).
- `ComponentName` attributes (graphics references) and blank lines from the
  trimmed elements are left in `ver001/c01.xml`.
