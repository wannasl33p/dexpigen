# DEXPI 1.3 in-memory v0.2

Label: `wayfinder:map`

## Destination

Grow the v0.1 model to v0.2: add `PipeTee`, `InstrumentationLoopFunction`, and the sensing layer (`ProcessSignalGeneratingFunction` linking an instrument to the piping process it measures). Same constraints as v0.1: MIT-licensed Python 3.13 / Pydantic v2, construct-time invariants, a Proteus XML writer. No NetworkX mapper, no graphics.

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
- [Decide how to add PipeTee](issues/11-pipetee.md): add `PipeTee(PipeFitting)` (`RDS427724`); existing `PipingComponent` base + serializer suffice (no multi-port handling, no 3-node invariant); model `component_name` on the shared base.
- [Decide how to add InstrumentationLoopFunction](issues/10-instrumentation-loop-function.md): top-level `InstrumentationLoopFunction` that references (not composes) PIFs via `is a collection including` / `is a part of` resolved at write time; rename the PIF `ProcessInstrumentationFunctions` string field to `…_code`; fix the hardcoded `ComponentClass` in `_emit_pif`.
- [Decide the v0.2 sensing-layer subset](issues/09-sensing-layer-subset.md): add `ProcessSignalGeneratingFunction` (composed under the PIF) + an abstract `SensingLocation` role base + `FlowMeasuringElement`; `is located in` / `is the location of` mirrored at write time; no ISO-15926 device layer; make `_emit_pif` logical associations direction-aware.

## Not yet specified

- None — the v0.2 frontier is fully resolved. Every open decision has an answer and the way to the destination is clear; what remains is implementation, not wayfinding.



## Out of scope

- XSD validation and any Proteus round-trip acceptance gate for v0.1.
- Mapper from NetworkX + Entity into the model.
- Graphics / coordinates / ShapeCatalogue.
- Plant structure (`PlantStructureItem`) and `MetaData` (title-block metadata).
- Using this library as a CAE import/export product.
- pyDEXPI as a dependency or source of classes.
- JSON/reference serialization of the object graph ([Decide JSON/reference serialization for v0.2](issues/12-json-reference-serialization.md), closed unclaimed): ruled out of the v0.2 destination — not needed for this effort. Its research note stays on disk; it returns only as a fresh effort against a redrawn destination.

