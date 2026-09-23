# Decide the Proteus XML writer and its model prerequisites

Type: grilling
Status: resolved
Blocked by: 01, 04, 06

## Question

v0.1 adds a Proteus XML writer for the in-memory model. How does the writer serialize the object graph, where does the `ComponentClass`/`ComponentClassURI`/field-URI knowledge live, and which model changes are prerequisites?

The serialization format is catalogued in [research/04](../research/04-proteus-serialization.md).

## Answer

A `serialization.py` (Proteus writer) module with `to_proteus_xml(model: ConceptualModel) -> str`, walking the object graph and emitting the document skeleton, polymorphic element tags, `GenericAttributes` for data fields, nested elements for composition, and `Association` for references (both directions). It is a pure writer: no XSD validation, no round-trip gate, no graphics.

### Class identity metadata

Every concrete model class gains two `ClassVar` attributes carrying the RDL discriminator, filled from the specification:

- `component_class: ClassVar[str]` — e.g. `"Tank"`, `"GlobeValve"`, `"ProcessInstrumentationFunction"`. Equal to the class name **except** the documented rename exceptions (research 01: `Blower`/`Fan`→`BlowerFan`, `Dryer`→`Drier`, `ReciprocatingExtruder`→`PistonExtruder`, `RotatingExtruder`→`AugerExtruder`, `GravitationalSeparator`→`GravitySeparator`, `StationarySieve`→`StationaryScreen`, `VibratingSieve`→`VibratingScreen`, `LoadingUnloadingSystem`→`Loading-UnloadingSystem`).
- `component_class_uri: ClassVar[str]` — from one of the two URI families (`http://sandbox.dexpi.org/rdl/<ClassName>` vs `http://data.posccaesar.org/rdl/RDS<n>`). The `RDS<n>` ids are a hardcoded lookup table extracted from the spec data file; they are not derivable from the name.

These live on the model classes (self-describing, pyDEXPI-shaped), not in a separate registry, so the writer is generic. The data-field metadata (each field's `Name`/`AttributeURI`/`Format`/`Units`) lives in the writer module as a field→RDL table, keyed by class + field, because it is serialization-only knowledge.

### Writer behaviour

- Emit `PlantInformation` (fixed attributes, `Units="mm"`) + `<UnitsOfMeasure/>`, then top-level objects in a stable order (`ActuatingSystem`, `PipingNetworkSystem`, `ProcessInstrumentationFunction`, `Equipment`).
- Each object → element `{ID, ComponentClass, ComponentClassURI}` using the polymorphic tag from research 04. `ID` = the object's `id`.
- Data fields → `<GenericAttributes Set="DexpiAttributes" Number="N">` in a fixed per-class order; `CustomAttribute` entries → `DexpiCustomAttributes` (or the named attribute when known).
- Composition → nested elements. References → `<Association Type="…" ItemID="<target.id>"/>` emitted on **both** endpoints with inverse `Type` strings.
- Piping: `Nozzle`/`PipingComponent`/`PipeOffPageConnector` emit `<ConnectionPoints>` with one implicit `<Node ID="<id>-DefaultNode"/>` plus one `Type="process"` node per model `PipingNode`; `Pipe` emits `<Connection FromID FromNode ToID ToNode>` with 1-based process-node indices.
- No `CenterLine`, no geometry, no `ShapeCatalogue`/`Drawing`/`MetaData`/`PlantStructureItem`.

### Model changes (prerequisites, applied before/with the writer)

1. **Add `component_class` + `component_class_uri` `ClassVar`s** to every concrete class, with the rename exceptions and the RDS table.
2. **Move `SignalConveyingFunction` and `ActuatingFunction` under `ProcessInstrumentationFunction`** as compositions (`signal_conveying_functions`, `actuating_functions`), and remove the two top-level `ConceptualModel` collections. This corrects issue 06's "top-level collection" simplification to match DEXPI's actual containment (research 04). Dangling signals remain representable: `source`/`target` stay optional; the owning PIF is still the composition parent.
3. **Add `PipeOffPageConnector.connector_reference`** — a `PipeOffPageConnectorReference` composition with the `…ByNumber`/`…ByNode` concrete subtypes (research 02 had it; it was dropped from the piping slice and the writer needs it).
4. **Add `piping_component_name` / `piping_component_number` to `PipingComponent`** (observed on valves/fittings in the examples; already in research 01).
5. **Deferred, noted:** the declared-null-vs-absent distinction (research 02/04) needs an explicit sentinel or `PydanticUndefined` to round-trip `Value=""` vs missing; do not block the writer on it — the writer defaults to omitting absent fields and emitting `Value=""` only where the model can represent it.

### Out of scope (unchanged from spec)

`PlantStructureItem`, `MetaData`, `InstrumentationLoopFunction`, `ProcessSignalGeneratingFunction`, graphics/coordinates/ShapeCatalogue, XSD validation, and the round-trip acceptance gate.

## Comments

- Source of truth for every URI and field name remains the spec data file; the examples only confirm the format and cover a subset of classes.
- The writer is read-only over the model (composition + references are walked, not mutated); it does not re-parent or clone.
