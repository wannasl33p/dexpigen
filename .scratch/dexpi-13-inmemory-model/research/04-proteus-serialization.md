# Proteus XML serialization format (DEXPI P&ID 1.3)

## Scope and sources

This note records how DEXPI P&ID 1.3 objects are serialized to **Proteus XML**, distilled from every example file the user added under `data/example_pids/` (35 `.xml` files: E01–E14, P01–P04, I01–I15, C01/C02/C03), cross-checked against the specification source `data/DEXPI-PID-Specification-1.3.pdf.md`. It is the reference for the v0.1 in-memory model's Proteus writer.

Only the *conceptual* (non-graphical) subset is in scope here. Graphics, coordinates, labels, and the ShapeCatalogue are documented only to mark the boundary — they remain out of v0.1 scope.

## Document skeleton

```xml
<?xml version='1.0' encoding='UTF-8'?>
<PlantModel>
  <PlantInformation Application="Dexpi" ... Units="mm">
    <UnitsOfMeasure/>
  </PlantInformation>
  <!-- top-level objects -->
</PlantModel>
```

- `<PlantModel>` is the root, **no attributes**, no namespace, no `xsi:schemaLocation`.
- `<PlantInformation>` is always the first child; `<UnitsOfMeasure/>` is its only child and is always empty/self-closing.
- `PlantInformation` attributes (order is stable; values vary only in `Date`/`Time`/`OriginatingSystem*`/`Units`): `Application="Dexpi"`, `ApplicationVersion="1.3.1"`, `Date`, `Discipline="PID"`, `Is3D="no"`, `OriginatingSystem`, `OriginatingSystemVendor`, `OriginatingSystemVersion`, `SchemaVersion="4.1.1"` (Proteus schema, **not** DEXPI 1.3.1), `Time`, `Units` (`mm` | `m`).
- **Top-level child order** (loose): `PlantInformation` → `MetaData`? → `PlantStructureItem`* → `ActuatingSystem`* → `InstrumentationLoopFunction`* → `PipingNetworkSystem`* → `ProcessInstrumentationFunction`* → `Equipment`* → `Drawing`? → `ShapeCatalogue`?. Within a group the order is arbitrary (not ID-sorted).

`ConceptualModel` itself is **not** serialized as an element; it maps to the `<PlantModel>` root.

## Element identity: ID / ComponentClass / ComponentClassURI

Every modelled object becomes an XML element carrying exactly three attributes, in this order:

```xml
<Equipment ID="Tank-1" ComponentClass="Tank" ComponentClassURI="http://data.posccaesar.org/rdl/RDS445139">
```

- `ID` — the DEXPI instance identity. Examples use `<ComponentClass>-<n>` with a per-file, per-class counter, but the value is an arbitrary stable string; our frozen `id` (uuid4) is valid.
- `ComponentClass` — the RDL class discriminator (a string).
- `ComponentClassURI` — the RDL URI of the class.

**Polymorphic tags.** The XML tag is *not* the class; one tag hosts many `ComponentClass` values and the discriminator decides:

| Proteus tag | ComponentClass values (observed) |
|---|---|
| `<Equipment>` | Tank, Vessel, PressureVessel, CentrifugalPump, ReciprocatingPump, PlateHeatExchanger, TubularHeatExchanger, ProcessColumn, Chamber, ColumnSection, ColumnPackingsArrangement, ColumnTraysArrangement, TubeBundle, Impeller, Displacer, … |
| `<PipingComponent>` | BallValve, GlobeValve, ButterflyValve, SwingCheckValve, SpringLoadedGlobeSafetyValve, OperatedValve, BlindFlange, PipeReducer, Flange, PipeTee, RestrictionOrifice, PipeFitting, FlowMeasuringElement, … |
| `<PipeOffPageConnector>` | FlowInPipeOffPageConnector, FlowOutPipeOffPageConnector |
| `<PipeOffPageConnectorReference>` | PipeOffPageConnectorReferenceByNumber, PipeOffPageConnectorReferenceByNode |
| `<PipingNetworkSystem>` | PipingNetworkSystem |
| `<PipingNetworkSegment>` | PipingNetworkSegment |
| `<Nozzle>` | Nozzle |
| `<ActuatingSystem>` | ActuatingSystem |
| `<ActuatingSystemComponent>` | ControlledActuator, OperatedValveReference, Positioner |
| `<ActuatingFunction>` | ActuatingFunction |
| `<ProcessInstrumentationFunction>` | ProcessInstrumentationFunction (and ProcessControlFunction — see below) |
| `<InformationFlow>` | SignalConveyingFunction, SignalLineFunction, MeasuringLineFunction |
| `<InformationFlowOffPageConnector>` | FlowInSignalOffPageConnector, FlowOutSignalOffPageConnector |
| `<PlantStructureItem>` | Isa95Enterprise, SiteIsa95, IndustrialComplexIso10209-2012, ProcessPlant, PlantTrain, PlantSectionIso10209-2012, AreaIsa95 |
| `<InstrumentationLoopFunction>` | InstrumentationLoopFunction |
| `<ProcessSignalGeneratingFunction>` | ProcessSignalGeneratingFunction |
| `<MetaData>` | MetaData |

The v0.1 classes map to tags: `Equipment`→`<Equipment>`; `Nozzle`→`<Nozzle>`; valves/fittings→`<PipingComponent>`; pipe OPC→`<PipeOffPageConnector>` (+ nested `<PipeOffPageConnectorReference>`); `PipingNode`→`<Node>` inside `<ConnectionPoints>`; `Pipe`→`<Connection>`; `ActuatingSystem`→`<ActuatingSystem>`; `ControlledActuator`/`OperatedValveReference`/`Positioner`→`<ActuatingSystemComponent>`; `ActuatingFunction`→`<ActuatingFunction>`; `ProcessInstrumentationFunction`→`<ProcessInstrumentationFunction>`; `SignalConveyingFunction`→`<InformationFlow>`; signal OPC→`<InformationFlowOffPageConnector>`.

## Class → ComponentClassURI: two families

`ComponentClassURI` is always one of two hosts (never a bare name):

1. **`http://sandbox.dexpi.org/rdl/<ClassName>`** — the class name is the last path segment, spelled exactly as `ComponentClass`. Used for all instrumentation/signal classes and some equipment (`PlateHeatExchanger`, `ColumnSection`, `CustomEquipment`, …).
2. **`http://data.posccaesar.org/rdl/RDS<number>`** — a PCA RDL numeric id that **cannot be derived from the class name**. A lookup table is mandatory.

Observed RDS ids relevant to v0.1 (examples): `Tank=RDS445139`, `Vessel=RDS414674`, `PressureVessel=RDS427229`, `CentrifugalPump=RDS416834`, `ReciprocatingPump=RDS416969`, `TubularHeatExchanger=RDS13971182`, `ProcessColumn=RDS4316825224`, `Chamber=RDS903151421`, `Nozzle=RDS415214`, `OperatedValve=RDS11141590`, `BallValve=RDS416654`, `ButterflyValve=RDS416609`, `GlobeValve=RDS416204`, `SwingCheckValve=RDS610424`, `Flange=RDS13307654`, `PipeReducer=RDS416294`, `PipeTee=RDS427724`, `BlindFlange=RDS414719`, `PipingNetworkSystem=RDS270359`, `PipingNetworkSegment=RDS267704`, `Impeller=RDS414539`, `TubeBundle=RDS415259`.

The complete per-class table must be extracted from the spec source (each concrete class page lists its RDL/`ComponentClassURI`), because the examples cover only a subset and give no rule to derive `RDS<n>` from the name.

## Data fields → `<GenericAttributes>`

Almost every data field is serialized as a generic attribute, not as a direct XML attribute or element:

```xml
<GenericAttributes Set="DexpiAttributes" Number="4">
  <GenericAttribute Name="TagNameAssignmentClass"
                    AttributeURI="http://sandbox.dexpi.org/rdl/TagNameAssignmentClass"
                    Format="string" Value="T4750"/>
  ...
</GenericAttributes>
```

- `Set` is `DexpiAttributes` (standard) or `DexpiCustomAttributes` (vendor/custom); `Number` equals the child count. Multiple `<GenericAttributes>` siblings per element are allowed (one per `Set`).
- `<GenericAttribute>` attributes: `Name`, `AttributeURI`, `Format`, `Value`, and optionally `ValueURI` (only with `Format="anyURI"`), `Units`+`UnitsURI` (only with `Format="double"`, always both), `Language` (multi-language string). `Units` and `ValueURI` never co-occur on one attribute.
- `Format` ∈ {`string`, `double`, `anyURI`, `integer`}. (`boolean`/`dateTime`/`float` do **not** occur; dates are `Format="string"`.)
- The field's `Name` is `<FieldName>AssignmentClass` for *assignment-class* attributes (e.g. `TagNameAssignmentClass`, `FluidCodeAssignmentClass`, `LineNumberAssignmentClass`), but some physical/specialization fields have no suffix (`NominalDiameter`, `SetPressureHigh`, `LocationSpecialization`, `FailActionSpecialization`, `PortStatusSpecialization`, `NominalCapacity(Volume)` — the literal parentheses must be preserved).
- The canonical `Name`/`AttributeURI` per field is fixed RDL data; it is not derivable from the Python field name, so the writer needs a field → (`Name`, `AttributeURI`, `Format`, units) map (source: spec data file).
- `AttributeURI` order within an element is not significant and varies between files; the writer should emit a stable order.
- `Value` of an enumeration `anyURI` attribute is a short alias (`CentralLocation`, `FailOpen`) while `ValueURI` is the full RDL URI, which may live in a **different** host than the `AttributeURI` (e.g. `Field` → `http://data.posccaesar.org/rdl/RDS409545541`).

Observed mapping for the v0.1 first-class fields (examples): equipment tag `TagName`/`TagNamePrefix`/`TagNameSequenceNumber`/`TagNameSuffix`; nozzle `SubTagName`; PNS `FluidCode`/`LineNumber`/`PipingClassCode`/`NominalDiameterNumericalValueRepresentation`; piping component `PipingComponentName`/`PipingComponentNumber`/`FluidCode`/`PipingClassCode`; PIF `LocationSpecialization` + `ProcessInstrumentationFunctionCategory/Number/Functions`; `ActuatingSystemNumber`; `ActuatingFunctionNumber`; `ControlledActuator.DeviceTypeName`/`FailAction`(`Specialization`+`Representation`)/`SubTagName`.

## References → `<Association>`

A reference is NOT nested and NOT an `IDREF`; it is an `<Association>` element carrying a `Type` (RDL relationship name) and an `ItemID` (the target's `ID` string):

```xml
<Association Type="refers to" ItemID="GlobeValve-1"/>
```

**Every logical relationship is serialized twice** — once from each endpoint, with inverse `Type` strings. The model stores the reference once; the writer must emit both directions. The 12 distinct `Type` strings form 6 inverse pairs:

| forward | inverse |
|---|---|
| `is a part of` | `is a collection including` |
| `is located in` | `is the location of` |
| `is fulfilled by` | `fulfills` |
| `refers to` | `is referenced by` |
| `has logical start` | `is logical start of` |
| `has logical end` | `is logical end of` |

v0.1 references and their strings:

| model reference | owner-side `Type` | inverse `Type` (on target) |
|---|---|---|
| `OperatedValveReference.valve` | `refers to` | `is referenced by` |
| `ActuatingFunction.systems` | `is fulfilled by` | `fulfills` |
| `ActuatingFunction.actuating_location` | `is located in` | `is the location of` |
| `SignalConveyingFunction.source` | `has logical start` | `is logical start of` |
| `SignalConveyingFunction.target` | `has logical end` | `is logical end of` |

**Forward references are normal** (`ActuatingSystem` top-level references a nested `ActuatingFunction` declared later), so the writer must be able to emit `ItemID` before the target element, and a parser must resolve in two passes. A dangling signal (missing source/target) simply omits that association on both ends.

## Piping topology: nodes and connections

- `PipingNode` → `<Node>` inside `<ConnectionPoints>`:
  ```xml
  <ConnectionPoints NumPoints="2" FlowIn="1" FlowOut="2">
    <Node ID="GlobeValve-1-DefaultNode"/>
    <Node Type="process" ID="PipingNode-1"/>
    <Node Type="process" ID="PipingNode-2"/>
  </ConnectionPoints>
  ```
  - `NumPoints` == number of `<Node>` children.
  - **Index 0 is always an implicit default node** (unconnected stub) with no `Type`; the writer adds it and names it `<OwnerID>-DefaultNode` (or `<OwnerID>-Node-0`).
  - Process nodes have `Type="process"` (attribute order `Type` then `ID`, the one case where `ID` is not first). Signal nodes use `Type="signal"`.
  - `FlowIn`/`FlowOut` are **1-based indices into the process-node list** (not absolute positions), and may be absent.
- `Pipe` → `<Connection>` inside `PipingNetworkSegment`:
  ```xml
  <Connection FromID="Nozzle-1" FromNode="1" ToID="Nozzle-2" ToNode="1"/>
  ```
  - `FromID`/`ToID` reference the endpoint *object's* `ID` (a `Nozzle`/`PipingComponent`/`PipeOffPageConnector`); `FromNode`/`ToNode` are **1-based indices into that object's `<ConnectionPoints>` process-node list** (index `0` = the default node, never used by a `Connection`).
  - Attribute order `FromID, FromNode, ToID, ToNode`; a `From*` or `To*` pair may be omitted whole for a dangling end.
- `CenterLine` is graphics; the writer omits it (examples show both `<CenterLine NumPoints="0"/>` stubs and absent segments).

## Composition vs reference in the XML

- **Composition** = element nesting. Confirmed v0.1 nesting: `Equipment`→`Nozzle`; `Equipment`→`Equipment`(chamber); `PipingNetworkSystem`→`PipingNetworkSegment`; `PipingNetworkSegment`→`PipingComponent`/`PipeOffPageConnector`/`Connection`; `PipeOffPageConnector`→`PipeOffPageConnectorReference`; `ConnectionPoints`→`Node`; `ActuatingSystem`→`ActuatingSystemComponent`; **`ProcessInstrumentationFunction`→`ActuatingFunction`/`InformationFlow`**.
- **Reference** = `<Association>` (see above). In particular the valve of a control valve is reached only through `OperatedValveReference` → `GlobeValve` (a `PipingComponent` elsewhere in a `PipingNetworkSystem`), never by containment.

**Key structural finding (drives a model change):** in every example, `SignalConveyingFunction` (tag `<InformationFlow>`) and `ActuatingFunction` are **nested inside their owning `ProcessInstrumentationFunction`**, never top-level. `ActuatingSystem` *is* top-level. This contradicts the current v0.1 model, which keeps both as top-level `ConceptualModel` collections (issue 06 simplified the DEXPI containment). The DEXPI `ConceptualModel` top-level compositions are: `ActuatingSystems`, `PipingNetworkSystems`, `ProcessInstrumentationFunctions`, `TaggedPlantItems` (=equipment), plus out-of-scope `MetaData`, `PlantStructureItems`, `InstrumentationLoopFunctions`, `ProcessSignalGeneratingSystems` — it has **no** top-level signal/actuating-function collections.

## Declared-null vs absent

Both states are in active use and must round-trip distinctly:

- `Value=""` — attribute present, empty string (e.g. `TagNameSuffixAssignmentClass Value=""`).
- `Value` attribute entirely absent (e.g. some `Format="string"` attributes).
- Empty self-closing element (e.g. `<UnitsOfMeasure/>`, `<CenterLine NumPoints="0"/>`) vs the element being omitted entirely.

The current model (`str | None`) conflates "declared empty" with "absent" (also flagged in research 02). The writer must know which a field was, or default to one.

## Out of scope for the v0.1 writer (documented for boundary)

- **Graphics/coordinates**: `Position`, `Scale`, `Coordinate`, `PolyLine`, `Shape`, `Circle`, `Text`, `Label`, `Presentation`, `CenterLine` geometry, `ComponentName`, `<Drawing>`/`<DrawingBorder>`, `<ShapeCatalogue>`.
- **`PlantStructureItem`** (plant hierarchy) and **`MetaData`** (title-block metadata) — top-level DEXPI compositions not in the v0.1 user stories.
- **`InstrumentationLoopFunction`** (loop functions) and **`ProcessSignalGeneratingFunction`** (sensing layer) — deferred in issues 06/03.
- XSD validation and any round-trip acceptance gate.
