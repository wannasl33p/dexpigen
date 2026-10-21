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
    c01.xml           # historical snapshot: serialization of build() at milestone 1
  ver002/
    c01.xml           # golden reference for the current build(): milestone 2
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

## Known gaps at ver002 (what trim still drops)

Still trimmed out of `ver002/c01.xml` (no model support yet):

- Graphics and layout (`Position`, `Shape`, `Presentation`, `Drawing`, ...); `MetaData`,
  `PlantStructureItem`, `ProcessSignalGeneratingSystem`.
- Equipment internals `TubeBundle`, `Impeller`, `Displacer`, and column internals
  (`ColumnSection`, packings and trays arrangements).
- Valve and fitting leaves `BlindFlange`, `SwingCheckValve`, `SpringLoadedGlobeSafetyValve`,
  and the other fitting/valve classes listed in `trim_dexpi_xml.py`.
- Primary elements and flow meters (`PrimaryElement`, `InlinePrimaryElement`,
  `VenturiTube`, ...). `FlowMeasuringElement` is modelled, but C01 contains none.
- Signal-level `ConnectionPoints` and `Node`s of instrumentation objects, and the
  `Connection`s between them (`INSTRUMENT_TAGS` in `trim_dexpi_xml.py`).
- The sensing layer is exercised only lightly by the ver002 golden: there are 3
  `ProcessSignalGeneratingFunction`s, only one has a location (`Nozzle-17`), none is a
  signal source, and C01 contains no `FlowMeasuringElement`. Those paths are covered
  by unit tests instead.

Data not yet first-class (kept as `CustomAttribute` in `_extras.py`):

- Nominal-diameter fields on pipe-tee and piping-node `GenericAttributes`, the
  `PipingClassCode` of piping components, and similar non-first-class data.
- `ComponentName` attributes (graphics references) are emitted only where the model
  sets `component_name` (pipe tees); blank lines from trimmed elements remain in the golden.
