# DEXPI 1.3 in-memory v0.1

Label: `wayfinder:map`

## Destination

A written spec a developer can implement without open architecture questions: a MIT-licensed Python 3.13 / Pydantic v2 in-memory DEXPI P&ID 1.3 ConceptualModel for the agreed PlantItem set, plus unit tests of construct-time invariants, plus a Proteus XML writer. No NetworkX mapper, no graphics.

## Notes

- Domain: DEXPI P&ID 1.3 conceptual model only. Source of truth: official spec (HTML/PDF 1.3 and GitLab tag `V1.3.0`). pyDEXPI is an architectural reference only, not a source of classes.
- Skills: `domain-modeling`, `grilling` for HITL tickets; `research` for spec lookups.
- Stack: Python 3.13, Pydantic v2, MIT.
- Fallback for unknown equipment types: `CustomEquipment`.
- Identity: frozen `id: str` (uuid4) plus required `dex_id: str`.
- Construction: pyDEXPI-shaped Pydantic API (direct constructors, nested composition, object references, `validate_assignment=True`); official DEXPI class names only.
- Control valve: Proteus tag `ActuatingSystemComponent`; conceptual model is `ActuatingSystem` + `OperatedValve`.
- Geometry: out of this effort.



## Decisions so far

- [Map extraction types to DEXPI 1.3 classes](issues/01-dexpi-13-class-mapping.md): extraction names alias official 1.3 classes; no generic `Valve`/`Instrument`/`MainProcessLine`; control-valve assembly is not a metamodel class named `ActuatingSystemComponent`.
- [Catalogue construct-time invariants for v0.1 classes](issues/02-construct-time-invariants.md): enforce typed compositions/references and ownership rules; all scoped DEXPI fields are optional, while UUID uniqueness is project policy.
- [Confirm ActuatingSystemComponent in DEXPI 1.3](issues/03-actuating-system-component.md): Proteus tag only; persist `OperatedValve` + `ActuatingSystem` + `ActuatingFunction` for signals.
- [Decide the public construction API](issues/04-public-construction-api.md): pyDEXPI-shaped Pydantic modules; nested composition; Python object refs; frozen string UUID `id`; required `dex_id`; no `ActuatingSystemComponent` type.
- [Decide MainProcessLine piping topology](issues/05-piping-topology.md): system owns segments; fittings/OPC in `items`; source/target are references; lineNumber uniqueness is mapper convention.
- [Decide the Instrument model split](issues/06-instrument-split.md): Instrument → `ProcessInstrumentationFunction` (+ `ProcessControlFunction` bubble subtype); tag fields first-class + generic `CustomAttribute` bag; only `ActuatingFunction` of the loop functions; `SignalConveyingFunction` top-level with `Source`/`Target` refs; sensing/device layers deferred.
- [Decide equipment and valve type-tree completeness](issues/07-type-tree-completeness.md): generate concrete classes 1:1 by name from the extraction `type`; `CustomEquipment` is the sole equipment fallback; valve family roots (`OperatedValve`/`CheckValve`/`SafetyValveOrFitting`) are the unspecified-valve fallback; no per-level `Custom*` leaves.
- [Decide the Proteus XML writer and its model prerequisites](issues/08-proteus-serialization.md): add a `serialization.py` writer emitting `PlantModel`/`PlantInformation`/polymorphic tags/`GenericAttributes`/`Association` (both directions); carry `ComponentClass`+`ComponentClassURI` as `ClassVar`s on each concrete class; move `SignalConveyingFunction`+`ActuatingFunction` under `ProcessInstrumentationFunction`; add `PipeOffPageConnector.connector_reference` and `PipingComponent` name/number.

## Not yet specified

- The full `component_class` / `component_class_uri` (and field `AttributeURI`) lookup table still needs to be extracted from the spec data file; the examples only cover a subset. This is implementation data for the writer, not an open architecture question.



## Out of scope

- XSD validation and any Proteus round-trip acceptance gate for v0.1.
- Mapper from NetworkX + Entity into the model.
- Graphics / coordinates / ShapeCatalogue.
- Plant structure (`PlantStructureItem`) and `MetaData` (title-block metadata).
- `InstrumentationLoopFunction` and the sensing/device layer (`PrimaryElement`/`Transmitter`, `ProcessSignalGeneratingFunction`).
- Using this library as a CAE import/export product.
- pyDEXPI as a dependency or source of classes.

