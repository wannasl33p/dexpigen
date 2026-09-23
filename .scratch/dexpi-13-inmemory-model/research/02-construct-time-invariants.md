# Construct-time invariants for the DEXPI 1.3 v0.1 model

## Scope and interpretation

This catalogue covers the official DEXPI 1.3 classes selected in the [v0.1 class mapping](./01-dexpi-13-class-mapping.md): concrete `Equipment` descendants (including `CustomEquipment`), `OperatedValve`, `CheckValve`, `SafetyValveOrFitting` and their relevant descendants, `FlowInPipeOffPageConnector`, `FlowOutPipeOffPageConnector`, `ActuatingSystem`, `ControlledActuator`, `OperatedValveReference`, `Positioner`, `SignalLineFunction`, `PipingNetworkSystem`, `PipingNetworkSegment`, `Pipe`, `PipingComponent` descendants used for line blind/reducer/flange, `ProcessInstrumentationFunction`, and `Nozzle`.

Only constraints that can be checked from an in-memory object graph are included. Proteus/XML placement, tag names, association serialization, graphical order, symbols, and connection-point indices are deliberately excluded.

DEXPI uses `0..1` for an optional scalar/reference/composition and `*` for zero or more. In the scoped classes, **there is no DEXPI-required (`1` or `1..*`) data field, reference, or child collection**. A Pydantic API may still require fields for application usability, but that is a project policy, not a DEXPI 1.3 invariant. The specification also distinguishes an absent attribute (“not declared”) from a declared null value; preserving that distinction requires Pydantic's unset state or an explicit sentinel in addition to `None`. [DEXPI 1.3, modeling concepts, lines 790–799](../../../data/DEXPI-PID-Specification-1.3.pdf.md#L790-L799)

## Cross-cutting DEXPI constraints

### Type, multiplicity, and identity

- Every object has a DEXPI class identity. Abstract mapping classes (`Equipment`, `PipingComponent`, `PipingConnection`, `PipeOffPageConnector`, and the signal source/target interfaces) must not be instantiated where the model promises a concrete official object. The accepted discriminator must identify a concrete subtype from the class mapping.
- Every `0..1` member accepts zero or one value; every `*` member accepts zero or more values. Lists must therefore reject `None` entries and entries of the wrong DEXPI type, but may be empty.
- DEXPI object identity is not value equality: two nozzles with equal attributes remain different objects. The conceptual model does not define an `InstanceId`/UUID attribute or a model-wide UUID uniqueness rule. [DEXPI 1.3, classes and identity, lines 724–734](../../../data/DEXPI-PID-Specification-1.3.pdf.md#L724-L734)
- Where an attribute type is a DEXPI enumeration/classification, construction can restrict the value to that enumeration. Where DEXPI says a field is an unrestricted string (for example segment/system `FluidCode` and instrument category/modifier), the model must not claim that a tighter vocabulary is a DEXPI rule. [segment `FluidCode`, lines 39203–39209](../../../data/DEXPI-PID-Specification-1.3.pdf.md#L39203-L39209); [instrument category/modifier, lines 46309–46356](../../../data/DEXPI-PID-Specification-1.3.pdf.md#L46309-L46356)

### Composition versus reference

- A **composition** is ownership/lifetime containment. The child appears in the owner's child field, and the opposite multiplicity shown for scoped compositions is `0..1`; therefore one child cannot simultaneously be composed by two owners in one valid object graph.
- A **reference** points to an independently owned object. It must not clone or re-parent the target. Reference validators can enforce the declared target class and any explicit same-owner rule.
- These are conceptual constraints even though the specification explains that composition usually maps to XML parent/child and references usually map to associations. [DEXPI 1.3, reference/composition distinction, lines 1134–1139](../../../data/DEXPI-PID-Specification-1.3.pdf.md#L1134-L1139)
- A nested-only Pydantic construction can enforce local child types and maximum multiplicities immediately. Cross-object rules—single composition owner, uniqueness policies, and references resolving to an object in the same aggregate—require validation after the complete aggregate has been assembled.

## Class catalogue

### Equipment and `CustomEquipment`

DEXPI constraints:

- `Equipment` is abstract; construct a concrete mapped descendant. `CustomEquipment` is the official fallback when no other concrete equipment class applies.
- Inherited tag fields `TagName`, `TagNamePrefix`, `TagNameSequenceNumber`, and `TagNameSuffix` are all `0..1 NullableString`. `EquipmentDescription` is `0..1 MultiLanguageString`. None is required. [tag fields, lines 31399–31427](../../../data/DEXPI-PID-Specification-1.3.pdf.md#L31399-L31427); [equipment field, lines 18289–18344](../../../data/DEXPI-PID-Specification-1.3.pdf.md#L18289-L18344)
- `Nozzles: Nozzle[*]` is inherited composition from `NozzleOwner`. A nozzle has at most one owner (`0..1` opposite); the only `NozzleOwner` subtype in 1.3 is `Equipment`. [nozzle ownership, lines 25473–25489](../../../data/DEXPI-PID-Specification-1.3.pdf.md#L25473-L25489)
- `DryingChambers`, `GearBoxes`, `Motors` (`MotorAsComponent`), and `SprayNozzles` are independent composition collections with multiplicity `*`; they are not references. [equipment compositions, lines 18340–18349](../../../data/DEXPI-PID-Specification-1.3.pdf.md#L18340-L18349)
- Any additional fields/compositions of the selected concrete equipment subtype retain their specification multiplicity and type. The common v0.1 base does not make them mandatory.

### Nozzle

DEXPI constraints:

- `SubTagName`, all four nominal-pressure representations/classifications, and `Chamber` are each `0..1`; none is required. `Chamber`, if present, is a **reference** to `Equipment.Chamber`, not a composed child. [Nozzle table, lines 25190–25207](../../../data/DEXPI-PID-Specification-1.3.pdf.md#L25190-L25207)
- A nozzle is composed in exactly zero or one equipment's `Nozzles` collection; it cannot be shared by equipment owners.
- If `Chamber` is set, it must be a chamber composed by the **same equipment object** that composes the nozzle. This is an explicit DEXPI same-owner invariant. [Nozzle `Chamber`, lines 25227–25235](../../../data/DEXPI-PID-Specification-1.3.pdf.md#L25227-L25235)
- A nozzle composes `PipingNode[*]` and can serve as both `PipingSourceItem` and `PipingTargetItem`; those capabilities do not require it to have nodes or a connection. [Nozzle overview, lines 25152–25167](../../../data/DEXPI-PID-Specification-1.3.pdf.md#L25152-L25167)

### Generic valve API and piping components

DEXPI constraints:

- An API-level `Valve` must discriminate to an official concrete descendant of `OperatedValve`, `CheckValve`, or (where semantically appropriate) `SafetyValveOrFitting`; `Valve` itself is not a DEXPI 1.3 class.
- The common `PipingComponent` fields `FluidCode`, `OnHold`, `PipingClassArtefact`, and `PressureTestCircuitNumber` are all `0..1`. `PipingComponent` is abstract. [PipingComponent overview/table, lines 38583–38639](../../../data/DEXPI-PID-Specification-1.3.pdf.md#L38583-L38639)
- Selected valve-specific, pipe-fitting, reducer, flange, and line-blind fields remain optional (`0..1`) according to their concrete/base class tables. The official subtype discriminator—not the presence of a particular optional field—establishes the type.
- `PipeReducer`, `Flange`, `LineBlind`, and `PipeFlangeSpade` are piping-component descendants and therefore are `PipingNetworkSegmentItem`, `PipingNodeOwner`, `PipingSourceItem`, and `PipingTargetItem`. They may be composed into at most one segment's `Items` and may own zero or more nodes.
- A generic “spectacle blind” is not an official DEXPI discriminator: select `LineBlind` generally or `PipeFlangeSpade` only when that specific physical artefact is meant, as recorded in the class mapping.

### Off-page pipe connectors

DEXPI constraints:

- Use concrete `FlowInPipeOffPageConnector` or `FlowOutPipeOffPageConnector`; abstract `PipeOffPageConnector` is not constructible as a final v0.1 object.
- Each connector has `ConnectorReference: PipeOffPageConnectorReference | None` as a `0..1` **composition**. The reference wrapper is owned by the connector. [connector composition, lines 38117–38152](../../../data/DEXPI-PID-Specification-1.3.pdf.md#L38117-L38152)
- A `PipeOffPageConnectorObjectReference` has `ReferencedConnector: PipeOffPageConnector | None` as a `0..1` **reference**. The target must be a pipe off-page connector. The specification does not require opposite flow direction, non-self-reference, or reciprocity, so those would be project policies. [object reference, lines 38227–38247 and 38270–38278](../../../data/DEXPI-PID-Specification-1.3.pdf.md#L38227-L38247)
- `FlowInPipeOffPageConnector` is a valid piping source; `FlowOutPipeOffPageConnector` is a valid piping target. The asymmetry is type-enforceable. [source target subtype sets, lines 41517–41529 and 41542–41561](../../../data/DEXPI-PID-Specification-1.3.pdf.md#L41517-L41529)

### `PipingNetworkSystem` (“MainProcessLine” mapping)

DEXPI constraints:

- All system data fields in the v0.1 mapping—`LineNumber`, `FluidCode`, `PipingClassCode`, nominal-diameter fields, insulation/heat-tracing fields, jacket fields, `OnHold`, and `PipingNetworkSystemGroupNumber`—are `0..1`; none is a required line identifier. [system overview/table, lines 40356–40447](../../../data/DEXPI-PID-Specification-1.3.pdf.md#L40356-L40447)
- `Segments: PipingNetworkSegment[*]` is a **composition**, not a reference. A system may contain no segments, and each segment may be composed by at most one system (`0..1` opposite). [system composition, lines 40443–40449](../../../data/DEXPI-PID-Specification-1.3.pdf.md#L40443-L40449)

### `PipingNetworkSegment`, `Pipe`, and connectivity

DEXPI constraints:

- Segment data fields are all `0..1`. `Connections: PipingConnection[*]` and `Items: PipingNetworkSegmentItem[*]` are separate compositions; both may be empty. A connection/item belongs to at most one segment. [segment table, lines 38990–39051](../../../data/DEXPI-PID-Specification-1.3.pdf.md#L38990-L39051); [connection composition, lines 39117–39125](../../../data/DEXPI-PID-Specification-1.3.pdf.md#L39117-L39125); [item composition, lines 39454–39464](../../../data/DEXPI-PID-Specification-1.3.pdf.md#L39454-L39464)
- `PipingConnection` is abstract; use `Pipe` or `DirectPipingConnection`. Each connection has independently optional `SourceItem: PipingSourceItem`, `SourceNode: PipingNode`, `TargetItem: PipingTargetItem`, and `TargetNode: PipingNode`, each `0..1`. DEXPI does not state that all four or either endpoint pair is mandatory. [connection table, lines 38830–38860](../../../data/DEXPI-PID-Specification-1.3.pdf.md#L38830-L38860)
- Allowed source item types are `FlowInPipeOffPageConnector`, `Nozzle`, `PipingComponent`, and `PropertyBreak`; allowed target item types are `FlowOutPipeOffPageConnector`, `Nozzle`, `PipingComponent`, and `PropertyBreak`. This rules out out-connectors as sources and in-connectors as targets. [source/target subtype sets, lines 41517–41561](../../../data/DEXPI-PID-Specification-1.3.pdf.md#L41517-L41561)
- If `SourceNode` is present on a connection, it must be one of the nodes composed by `SourceItem`; if `TargetNode` is present, it must be one of the nodes composed by `TargetItem`. Consequently a node without its corresponding item is invalid even though each field is individually `0..1`. [connection node ownership, lines 38888–38908 and 38923–38933](../../../data/DEXPI-PID-Specification-1.3.pdf.md#L38888-L38908)
- A `PipingNodeOwner` (`Nozzle`, pipe off-page connector, piping component, or property break) composes `Nodes: PipingNode[*]`; each node has at most one owner, and DEXPI says this collection is unordered. [node ownership, lines 41410–41429 and 41442–41488](../../../data/DEXPI-PID-Specification-1.3.pdf.md#L41410-L41429)
- A segment itself has optional source/target item and node references, typed like connection endpoints. The specification does not explicitly repeat the connection's “node must belong to item” sentence for segment endpoints in the parsed text; enforcing it for segments is sensible project consistency, but must not be labelled an explicit DEXPI 1.3 rule. [segment endpoint fields, lines 39043–39051](../../../data/DEXPI-PID-Specification-1.3.pdf.md#L39043-L39051); [segment endpoint descriptions, lines 40081–40135](../../../data/DEXPI-PID-Specification-1.3.pdf.md#L40081-L40135)

### `ActuatingSystem` / control-valve assembly

DEXPI constraints:

- `ActuatingSystemNumber` and `TypicalInformation` are `0..1`.
- `ControlledActuator`, `OperatedValveReference`, and `Positioner` are three distinct `0..1` **compositions**; `CustomComponents` is `*`. None is required, and a composed component has at most one actuating-system owner. [ActuatingSystem table, lines 43645–43673](../../../data/DEXPI-PID-Specification-1.3.pdf.md#L43645-L43673)
- `ControlledActuator` and `Positioner` own only optional (`0..1`) data in the scoped model. They are not references to a valve.
- `OperatedValveReference.Valve` is a `0..1` **reference** whose allowed target type is specifically `OperatedValve`, not `CheckValve`, `SafetyValveOrFitting`, or an application `Valve` union. Its `SubTagName` is also `0..1`. [OperatedValveReference table, lines 45494–45533](../../../data/DEXPI-PID-Specification-1.3.pdf.md#L45494-L45533)
- Therefore the DEXPI control-valve structure is an `ActuatingSystem` that owns an optional `OperatedValveReference`, which may point to an independently owned `OperatedValve`; it is not a collapsed “actuating system component” object containing the valve.

### `ProcessInstrumentationFunction` (“Instrument” mapping)

DEXPI constraints:

- All scoped data fields, including `ProcessInstrumentationFunctionNumber`, category, modifier, additional functions, location, panel code, device/typical/vendor information, relevance fields, and voting representation, are `0..1`. Even the field described as a “unique identifier” is optional. [instrument table, lines 45919–46022](../../../data/DEXPI-PID-Specification-1.3.pdf.md#L45919-L46022); [number definition, lines 46388–46398](../../../data/DEXPI-PID-Specification-1.3.pdf.md#L46388-L46398)
- DEXPI describes `ProcessInstrumentationFunctionNumber` as unique, so if values are present, duplicate numbers can be rejected at aggregate construction/finalization. The scope of uniqueness is not made explicit in the cited paragraph; model-wide uniqueness is a conservative project interpretation and should be documented as such.
- `ActuatingElectricalFunctions`, `ActuatingFunctions`, `ProcessSignalGeneratingFunctions`, `SignalConnectors`, and `SignalConveyingFunctions` are separate `*` compositions. Children belong to at most one process instrumentation function. [instrument compositions, lines 46013–46022](../../../data/DEXPI-PID-Specification-1.3.pdf.md#L46013-L46022)
- Because `ProcessInstrumentationFunction` is both a `SignalConveyingFunctionSource` and `SignalConveyingFunctionTarget`, it is allowed at either end of a signal reference. This capability does not require any signal to be attached. [instrument supertypes, lines 45967–45976](../../../data/DEXPI-PID-Specification-1.3.pdf.md#L45967-L45976)

### `SignalLineFunction`

DEXPI constraints:

- `SignalLineFunction` inherits `SignalConveyingFunction`. `PortStatus`, `SignalConveyingType`, `SignalPointNumber`, and `SignalProcessControlFunctions` are each `0..1`.
- `Source` and `Target` are optional `0..1` **references**, not compositions. A source must implement `SignalConveyingFunctionSource`; a target must implement `SignalConveyingFunctionTarget`. A signal line may be constructed with neither or only one endpoint because DEXPI gives no lower bound of one. [signal function table, lines 47314–47363](../../../data/DEXPI-PID-Specification-1.3.pdf.md#L47314-L47363)
- Allowed source classes are `ActuatingFunction`, `FlowInSignalOffPageConnector`, `ProcessInstrumentationFunction`, and `ProcessSignalGeneratingFunction`. Allowed target classes are `ActuatingElectricalFunction`, `ActuatingFunction`, `FlowOutSignalOffPageConnector`, and `ProcessInstrumentationFunction`. [signal endpoint subtype sets, lines 47644–47697](../../../data/DEXPI-PID-Specification-1.3.pdf.md#L47644-L47697)
- One endpoint object may be referenced by multiple signal functions (`0..*` opposite). Do not enforce exclusive signal attachment. [source/target opposite multiplicities, lines 47542–47556 and 47594–47606](../../../data/DEXPI-PID-Specification-1.3.pdf.md#L47542-L47556)
- If a signal line is nested in `ProcessInstrumentationFunction.SignalConveyingFunctions`, that is composition ownership and is independent of its logical `Source` and `Target` references. The owner need not equal either endpoint; DEXPI states no such constraint. [instrument signal composition, lines 46624–46634](../../../data/DEXPI-PID-Specification-1.3.pdf.md#L46624-L46634)

## Project-level policies (not DEXPI 1.3 conceptual invariants)

The following are useful Pydantic/application rules but must be labelled separately:

- Generate a UUID/`InstanceId` for every object; require it; require model-wide UUID uniqueness; or use it for equality/reference resolution.
- Require non-empty tags, equipment tags, line numbers, instrument numbers, nozzle subtags, signal endpoints, piping endpoints, at least one segment, or at least one node. DEXPI gives the relevant members lower multiplicity zero.
- Require `TagName` to equal prefix + sequence + suffix, or require all decomposed tag parts whenever the full tag is present.
- Require `ProcessInstrumentationFunctionNumber` uniqueness across an entire document rather than only treating the specification's “unique identifier” wording as a semantic intent.
- Require reciprocal off-page references, opposite connector directions, no self-reference, matching connector/drawing numbers, or target existence inside the currently loaded aggregate.
- Require segment endpoints to use nodes belonging to their endpoint items; unlike `PipingConnection`, the parsed segment text does not explicitly state this ownership sentence.
- Require a piping graph to be connected, acyclic, free of duplicate edges, topologically ordered, or graphically contiguous; infer `NumberOfPorts` from node/edge counts; or require a valve/reducer/flange to have a fixed node count.
- Restrict DEXPI free-text codes or instrument letters to a company vocabulary, or reject declared-null values rather than preserving DEXPI's declared-null state.

## Recommended validation boundary

Field validation should enforce concrete discriminators, scalar/classification types, and `0..1` versus list shape. Object-level validation should enforce paired rules such as connection node ownership. Aggregate finalization should enforce one composition owner per child, nozzle/chamber same-equipment ownership, reference resolution, optional instrument-number uniqueness, and any explicitly adopted project identity/topology policies.
