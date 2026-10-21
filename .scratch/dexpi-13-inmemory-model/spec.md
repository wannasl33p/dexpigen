# DEXPI 1.3 in-memory model v0.1 — Spec

Status: ready-for-agent

## Problem Statement

An ML extraction pipeline produces a graph of a P&ID: typed plant items (equipment, valves, nozzles, instrument bubbles, control systems) connected by piping and signal edges. These need to be held in memory as a **DEXPI P&ID Specification 1.3 ConceptualModel** — a typed object graph, not a drawing, not a NetworkX graph, not a Proteus XML document. All architecture questions are already resolved (see the wayfinder map); what remains is a written spec a developer can implement without open questions, and the implementation itself.

## Solution

A MIT-licensed Python 3.13 / Pydantic v2 library that holds the DEXPI 1.3 conceptual model in memory and serializes it to Proteus XML. Callers build typed objects directly (pyDEXPI-shaped constructors, nested composition, Python object references, `validate_assignment=True`). Every object carries a frozen UUID `id` and a required extraction `dex_id`. Construct-time invariants are enforced as objects are assembled, so an invalid graph cannot be produced. No NetworkX mapper, no graphics.

## User Stories

1. As a library user, I want to construct a typed equipment (e.g. a pump) with a required `dex_id`, so that every in-memory object is traceable to its extraction source.
2. As a library user, I want every object to receive a frozen, auto-generated string UUID `id`, so that objects can be referenced by stable identity and later serialized by reference.
3. As a library user, I want the `id` to be immutable after construction, so that identity cannot be silently corrupted.
4. As a library user, I want the concrete DEXPI class (not a generic `Valve`/`Instrument`/`MainProcessLine`) to be the thing I instantiate, so that the model uses official 1.3 vocabulary only.
5. As a mapper, I want to resolve an extraction equipment `type` to the DEXPI concrete class of the same name (e.g. `tank` → `Tank`, `pump` → `Pump`), so that coarse extraction types land on typed classes.
6. As a mapper, I want an unmatched extraction `type` to fall back to `CustomEquipment`, so that unknown equipment is not forced into `Tank` or any other specific class.
7. As a library user, I want `CustomEquipment` to carry the original extraction type label, so that the unknown type string is not lost.
8. As a library user, I want nozzles to be composed under their equipment, so that a nozzle cannot exist without (or be shared between) equipment owners.
9. As a library user, I want a nozzle to be usable as a piping source and target, so that pipes can reference it as an endpoint.
10. As a library user, I want a piping line to be a `PipingNetworkSystem` composed of segments, so that a process line and its stretches are distinguished.
11. As a library user, I want a segment to hold its piping components and connectors in `items` and its pipes in `connections`, so that in-line items and between-item connections are separated.
12. As a library user, I want piping components (valves, flange, reducer, line-blind, off-page connectors) to be usable as piping source/target items, so that pipes can reference them as endpoints.
13. As a mapper, I want to map extraction valve names 1:1 to concrete DEXPI classes (`ball`→`BallValve`, `globe`→`GlobeValve`, `butterfly`→`ButterflyValve`, `needle`→`NeedleValve`, `gate`→`GateValve`, `check`→`CheckValve`), so that common valves are typed.
14. As a library user, I want an unspecified valve to fall back to the concrete family roots `OperatedValve`/`CheckValve`/`SafetyValveOrFitting`, so that a valve of unknown kind is still typed at the family level.
15. As a library user, I want a control valve represented as four related objects (`OperatedValve` + `ActuatingSystem` + `ActuatingFunction` + `OperatedValveReference`), so that the DEXPI split is preserved and no fake `ActuatingSystemComponent` class exists.
16. As a library user, I want `OperatedValveReference` to point at an `OperatedValve` (not a check or safety valve), so that the controlled-valve link is type-safe.
17. As a library user, I want an `ActuatingSystem` to compose a `ControlledActuator`, an `OperatedValveReference`, and an optional `Positioner`, so that the physical assembly matches DEXPI.
18. As a library user, I want an `ActuatingFunction` to reference its `ActuatingSystem` and its `PipingNetworkSegment`, so that the control loop is linked to its physical assembly and location.
19. As a mapper, I want an instrument bubble to map to `ProcessInstrumentationFunction`, so that the P&ID bubble has an official home.
20. As a library user, I want the instrument tag split into number, category, modifier, and functions fields, with all other DEXPI fields in a generic attribute bag, so that the tag is first-class without generating every optional field.
21. As a mapper, I want a control/safeguarding system to map to `ProcessControlFunction` (a subtype of `ProcessInstrumentationFunction`), so that a system bubble is a function, not equipment.
22. As a library user, I want a dashed signal line to be a `SignalConveyingFunction` whose `Source`/`Target` reference functions, so that signal connectivity is logical, not graphical.
23. As a library user, I want a signal line to connect only functions (`ProcessInstrumentationFunction`, `ProcessControlFunction`, `ActuatingFunction`, signal off-page connectors), so that it cannot be attached to physical equipment or nozzles.
24. As a mapper, I want a dangling signal (missing `Source` or `Target`) to be representable, so that completeness is the mapper's concern, not a construction error.
25. As a library user, I want the same Python object to be referenced from multiple fields (e.g. a valve referenced by an `OperatedValveReference`), so that references do not clone or re-parent their target.
26. As a library user, I want a top-level `ConceptualModel` that aggregates all top-level objects (equipment, lines, instrument functions, actuating systems), so that there is a single root for the whole P&ID. Signal lines and actuating functions are composed under their owning `ProcessInstrumentationFunction`.
27. As a library user, I want construct-time invariants enforced — a composition child has exactly one owner, a reference resolves to the declared type, a nozzle's chamber belongs to the same equipment, a connection's node belongs to its endpoint item — so that invalid graphs are rejected at build time.
28. As a library user, I want mutation to go through aggregate methods (e.g. add a nozzle, add a segment) with assignment re-validation, so that the model stays valid as it changes.
29. As a library user, I want all DEXPI data fields to be optional (`0..1`) and only `id`/`dex_id` required, so that the model never claims a DEXPI-required field the spec does not mandate.
30. As a downstream consumer, I want to navigate the object graph by typed relationships (equipment → nozzles, system → segments → items/connections, function → references), so that I can traverse the P&ID without parsing graphics.

## Implementation Decisions

**Module layout.** Split the library into modules mirroring the DEXPI packages: a base module (shared model), an equipment module (`Equipment` descendants, `Nozzle`, `Chamber`, `CustomEquipment`), a piping module (systems, segments, pipes, components, valves, off-page connectors), an instrumentation module (`ProcessInstrumentationFunction`, `ProcessControlFunction`, `ActuatingFunction`, `ActuatingSystem`, `SignalConveyingFunction`, signal off-page connectors), plus physical-quantity and enumeration modules, and a serialization module (`to_proteus_xml`). Callers import official class names from these modules.

**Base model.** A single Pydantic `BaseModel` subclass with `model_config = ConfigDict(validate_assignment=True)` is the root of every class. It declares `id: str` (frozen, `default_factory` uuid4 string), `dex_id: str` (required), and `custom_attributes: list[CustomAttribute]` (the DEXPI `CustomAttributeOwner` bag). `id` is a frozen in-memory object key; `dex_id` is the extraction identifier and is serialized as the Proteus `ID` attribute (the DEXPI instance identity).

**Official names, concrete only.** Use official DEXPI 1.3 class names. Abstract classes (`Equipment`, `PipingComponent`, `PipeFitting`, `PipeOffPageConnector`, `PipingConnection`) are bases only and must not be instantiated; every instantiable class is a concrete 1.3 class with its own `ComponentClass`.

**Equipment tree.** `Equipment` is the abstract root. Its ~29 direct subclasses are all concrete and are generated 1:1 by name from the extraction `type` vocabulary (`pump`→`Pump`, `vessel`→`Vessel`, `tank`→`Tank`, `silo`→`Silo`, `filter`→`Filter`, …). `CustomEquipment` is the sole fallback for an unmatched `type`, carrying the original label. Per-level `Custom*` leaves (`CustomPump`, `CustomVessel`, …) and un-named deep leaves are not generated.

**Valve tree.** `PipingComponent` is abstract; `OperatedValve`, `CheckValve`, and `SafetyValveOrFitting` are concrete family roots and are the fallback for an unspecified valve. Named concrete leaves are `BallValve`, `GlobeValve`, `ButterflyValve`, `NeedleValve`, `GateValve` (and `CheckValve` for `check`). `FlameArrestor` and `RuptureDisc` are excluded (fittings, not valves). `Flange`, `PipeReducer`, and `LineBlind` (spectacle blind) are `PipeFitting` descendants.

**Composition vs reference.** Composition is a nested Python object owned by its parent (e.g. `equipment.nozzles: list[Nozzle]`, `actuating_system.controlled_actuator`). A reference holds the same Python object in another field (e.g. `operated_valve_reference.valve: OperatedValve | None`) and never clones or re-parents it.

**Instrumentation.** `ProcessInstrumentationFunction` is the bubble; its tag is first-class (number, category, modifier, functions) and all other DEXPI fields go into a generic attribute bag. `ProcessControlFunction` is a subtype for control/safeguarding system bubbles. `ActuatingSystem` composes `ControlledActuator`, `OperatedValveReference`, and optional `Positioner`; `ActuatingFunction` references the system and its segment. `SignalConveyingFunction` is the dashed signal line, with `0..1` `Source`/`Target` references restricted to functions. `ProcessSignalGeneratingFunction` is composed under its PIF and references its `0..1` `SensingLocation` (a nozzle, a segment, or a `FlowMeasuringElement`); `InstrumentationLoopFunction` references the PIFs it collects without owning them.

**Optionality.** Every DEXPI data field is optional (`0..1` / `*`); the only required fields are the project-level `id` and `dex_id`. No field the spec leaves at multiplicity zero is made mandatory.

**Construct-time invariants.** Enforce, at construction/finalization: one composition owner per child; typed reference endpoints (source/target subtype sets); nozzle-chamber same-equipment ownership; connection-node-belongs-to-item ownership; and `OperatedValveReference` targets `OperatedValve` specifically. Preserve DEXPI's declared-null vs absent distinction where relevant.

## Testing Decisions

**One seam.** The single test seam is the public construction API: constructors plus aggregate methods, then finalization/validation. Tests build object graphs through that API and assert external behavior — valid graphs are accepted, invalid ones are rejected with a clear error. Tests never reach into Pydantic internals.

**What a good test looks like.** It states a DEXPI invariant (from the construct-time invariant catalogue) and asserts either that a well-formed graph passes or that a specific violation (wrong reference target, shared composition child, nozzle-chamber mismatch, connection node not owned by its item, abstract class instantiated) is rejected.

**Modules tested.** Base model, equipment (including `Nozzle`/`CustomEquipment`), piping (systems, segments, components, valves, off-page connectors), instrumentation (functions, actuating system, signal line), and the top-level `ConceptualModel`.

**Prior art.** Greenfield repository — no existing tests to mirror. Use pytest; the model under test is exercised only through its public construction API.

## Out of Scope

- The mapper from a NetworkX/entity graph into the model (a later effort; the 1:1 name rule is defined here but the mapper itself is not).
- Graphics, coordinates, and the ShapeCatalogue.
- Using this library as a CAE import/export product.
- pyDEXPI as a dependency or a source of classes (architectural reference only).
- Sensing/device layer beyond the `SensingLocation` subset: `Transmitter`, `PrimaryElement`, `MeasuringElement`, `FlowDetector`.
- Loop functions beyond `ActuatingFunction` and `InstrumentationLoopFunction`: `ActuatingElectricalFunction`.
- The `SignalLineFunction` vs `MeasuringLineFunction` distinction (collapse to `SignalConveyingFunction`).
- `FlameArrestor` / `RuptureDisc`.
- Per-level `Custom*` equipment leaves and un-named deep equipment leaves.
- JSON/reference serialization of the object graph.
- XSD validation and a Proteus round-trip acceptance gate (generated XML is validated in the examples/tests, but the library itself only writes).

## Further Notes

- Source of truth: the DEXPI P&ID Specification 1.3 (see the repo's data file) and the resolved wayfinder decisions (map + issue files). Use the project glossary (`CONTEXT.md`) for vocabulary throughout.
- The model is entirely in-memory; there is no persistence layer.
- Concrete class identity is carried by the Python class plus the `component_class`/`component_class_uri` ClassVars, which hold the DEXPI `ComponentClass`/RDL URI used by the writer.
