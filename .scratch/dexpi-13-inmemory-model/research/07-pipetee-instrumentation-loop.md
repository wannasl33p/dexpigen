# `PipeTee` and `InstrumentationLoopFunction` in DEXPI P&ID Specification 1.3

Two classes the model wants to add: `PipeTee` (Piping package, section 8.51) and
`InstrumentationLoopFunction` (Instrumentation package, section 9.15).

Primary sources used:

- Spec text: `data/DEXPI-PID-Specification-1.3.pdf.md` (line numbers cited throughout).
- Proteus schema: `data/schemas/ProteusPIDSchema 4.1.1.xsd` (line numbers cited).
- Examples: `data/example_pids/C01 DEXPI Reference P&ID/C01V04-VER.EX01.xml`,
  `data/example_pids/C02 Process Column (BASF)/C02V03-VER.EX02.xml`,
  `data/example_pids/I01..I15 */I*V01-VER.EX01.xml`.

Notation used below: "→" reads as "composes/references"; `*` is DEXPI's
unbounded multiplicity.

---

# 1. `PipeTee`

## (a) Class identity + URI

| Item | Value | Citation |
| --- | --- | --- |
| Section | 8.51. PipeTee (p. 826), subsection 8.51.1 Overview | spec:319 (TOC), spec:38535-38537 |
| Class definition | "An 'artefact' that has three piping ends in T-shape, including a branch at 90 degrees (from `http://data.posccaesar.org/rdl/RDS427724`)." | spec:38538-38540 |
| Concrete? | Concrete (not marked abstract; contrast 8.52 PipingComponent "Abstract class" at spec:38584) | spec:38537-38540 |
| Supertypes | `PipeFitting` (single) | spec:38560-38561 |
| Proteus tag | `<PipingComponent>` | spec:38565 |
| **ComponentClass** | `PipeTee` | spec:38568 |
| **ComponentClassURI** | `http://data.posccaesar.org/rdl/RDS427724` | spec:38569-38570 |
| RDL reference | `PIPE TEE` | spec:38566 |
| Example statement | `pipeTee1 : PipeTee` | spec:38572 |
| RDL host | `data.posccaesar.org` (a numeric RDS id), **not** `sandbox.dexpi.org/<Name>` | spec:38569 |

Note the two RDL hosts: `PipeTee` uses `http://data.posccaesar.org/rdl/RDS427724`,
while other classes in the same package use `http://sandbox.dexpi.org/rdl/<Name>`
(e.g. `PipeFitting`, spec:37662). The existing model already mixes both hosts per
class (`piping.py:131,137,143`).

## (b) Fields

**`PipeTee` declares no data fields of its own.** The 8.51 section body (spec:38535-38581)
contains only the diagram, `Supertypes`, and `Implementation` — there is no
"Attributes (data)" table. Everything it carries is inherited:

| Inherited from | Field | Multiplicity | Type | Citation |
| --- | --- | --- | --- | --- |
| `PipeFitting` (8.43) | `HeatTracingType` | 0..1 | `HeatTracingTypeClassification` | spec:37588, 37642 |
| `PipeFitting` | `HeatTracingTypeRepresentation` | 0..1 | `NullableString` | spec:37590, 37643 |
| `PipeFitting` | `InsulationThickness` | 0..1 | `NullableLength` | spec:37591, 37645 |
| `PipeFitting` | `InsulationType` | 0..1 | `NullableString` | spec:37592, 37648 |
| `PipeFitting` | `LowerLimitHeatTracingTemperature` | 0..1 | `NullableTemperature` | spec:37593, 37650 |
| `PipeFitting` | `PipingClassCode` | 0..1 | `NullableString` | spec:37594, 37651 |
| `PipeFitting` | `PipingComponentName` | 0..1 | `NullableString` | spec:37596, 37652 |
| `PipeFitting` | `PipingComponentNumber` | 0..1 | `NullableString` | spec:37597, 37654 |
| `PipingComponent` (8.52) | `FluidCode` | 0..1 | `NullableString` | spec:38598/38629 |
| `PipingComponent` | `OnHold` | 0..1 | `OnHoldClassification` | spec:38600, 38630 |
| `PipingComponent` | `PipingClassArtefact` | 0..1 | `PipingClassArtefactClassification` | spec:38601, 38631 |
| `PipingComponent` | `PressureTestCircuitNumber` | 0..1 | `NullableString` | spec:38602, 38633 |

The full `PipeTee` inheritance chain is
`PipeTee` → `PipeFitting` (spec:38561, 37598-37600) → `PipingComponent` (spec:38584)
→ `CustomAttributeOwner`, `PipingNetworkSegmentItem`, `PipingNodeOwner`,
`PipingSourceItem`, `PipingTargetItem`, `SensingLocation` (spec:38608-38616).

`PipeTee` is listed among `PipeFitting`'s subtypes at spec:37630. `PipeFitting`'s
own RDL reference / ComponentClass / ComponentClassURI are `PIPE FITTING` /
`PipeFitting` / `http://sandbox.dexpi.org/rdl/PipeFitting` (spec:37659-37663).

## (c) Compositions and references + Association Type strings

`PipeTee` inherits all of these; the 8.51 diagram repeats them so they are
unambiguously part of the class (spec:38541-38551).

| Role | Owner class (introduced by) | Multiplicity | Type | Kind | Proteus serialization | Association Type (owner side) |
| --- | --- | --- | --- | --- | --- | --- |
| `CustomAttributes` | `CustomAttributeOwner` | * | `CustomAttribute` | composition | `<GenericAttributes>` / `<GenericAttribute>` | n/a (XML hierarchy, no `Association`) |
| `Nodes` | `PipingNodeOwner` (8.58) | * | `PipingNode` | composition | grouped in `<ConnectionPoints><Node>` | n/a (XML hierarchy) |
| `Items` | `PipingNetworkSegmentItem` (8.55) | * (segment side) | — | composition, inverse | XML hierarchy; component is a child of `<PipingNetworkSegment>` | n/a |
| `SourceItem` | `PipingSourceItem` (8.59) | 0..1 | `PipingConnection` | inverse reference | `<Connection FromID=...>` in the segment | (segment side) |
| `TargetItem` | `PipingTargetItem` (8.60) | 0..1 | `PipingConnection` | inverse reference | `<Connection ToID=...>` in the segment | (segment side) |
| `SensingLocation` | `SensingLocation` (9.25) | * (sensor side) | `ProcessSignalGeneratingFunction` | inverse reference | `<Association Type="is the location of">` **on the component** | sensor side emits `"is located in"`; the component side emits `"is the location of"` |

Citations for the role table: spec:38541-38551 (PipeTee diagram), spec:38608-38616
(PipingComponent supertypes), spec:41408-41429 (`PipingNodeOwner`, abstract; `Nodes *`
composition at spec:41429), spec:41442-41447 (`Nodes` details, opposite 0..1),
spec:47278-47297 (`SensingLocation` is abstract; subtypes `Nozzle`, `PipingComponent`,
`PipingNetworkSegment`), spec:46887-46900 (`ProcessSignalGeneratingFunction.SensingLocation`
0..1, opposite 0..*, association types `"is located in"` / `"is the location of"`).

Example of the `SensingLocation` pair in practice (`I13:46`, `I13:72`): the
`BlindFlange` carries `<Association Type="is the location of"
ItemID="ProcessSignalGeneratingFunction-1"/>` and the
`ProcessSignalGeneratingFunction` carries `<Association Type="is located in"
ItemID="BlindFlange-1"/>`. `PipeTee` is a `PipingComponent` and therefore a valid
`SensingLocation`, but no example attaches a sensor to a `PipeTee`.

### `Nodes` / `ConnectionPoints` semantics (the important part for `PipeTee`)

- spec:41449-41454: the `<Node>` elements are **not** direct children of the owner
  element; they are grouped in a single `<ConnectionPoints>` element.
- spec:41452-41454: the **first** `<Node>` in `<ConnectionPoints>` is the
  `PipingNodeOwner` itself, is **not** a DEXPI `PipingNode`, is not relevant to
  DEXPI, but must be present and **must not carry a `Type` attribute**.
- spec:41455: further `<Node>` elements with `Type="process"` **are** the DEXPI
  `PipingNode`s; `<Node>` without `Type`, or with `Type="signal"`, are not.
- spec:41479-41484: a `<Connection>`/`<Node>` reference uses the **zero-based**
  index of the `<Node>` within `<ConnectionPoints>`; these indices are a Proteus
  implementation detail with no DEXPI semantics.
- spec:41485: the DEXPI `Nodes` attribute is **unordered** — the first/second
  `PipingNode` is not meaningful.
- XSD `ConnectionPoints` (`ProteusPIDSchema 4.1.1.xsd:929-955`): "An ordered set
  of Nodes … The first Node (0) is coincident with the origin of the containing
  object. The next two (1 and 2) are the main flow and all others are secondary
  flows. Flowin and Flowout reference the Nodes indexed from 0 ie main flow is 1
  and 2." `NumPoints` is required; `FlowIn`/`FlowOut` are optional
  `xsd:positiveInteger` (the 4.0.1-alpha-1 profile **removed the defaults**, so
  omitting them means "not declared").

So a `PipeTee` in practice has `NumPoints="4"`: index 0 = the default node,
indices 1 and 2 = the two main-flow (run) ends, index 3 = the branch.

## (d) How it is serialized in the examples

`PipeTee` appears as `<PipingComponent ComponentClass="PipeTee">` in the C-series
and in one I-series file.

| File | Instances | Citation |
| --- | --- | --- |
| `data/example_pids/C01 DEXPI Reference P&ID/C01V04-VER.EX01.xml` | 5 (`PipeTee-1` .. `PipeTee-5`) | lines 1009, 1157, 1230, 1477, 1568 |
| `data/example_pids/C02 Process Column (BASF)/C02V03-VER.EX02.xml` | 1 (`PipeTee-1`) | line 300 |
| `data/example_pids/I13 Measurement/I13V01-VER.EX01.xml` | 1 (`PipeTee-1`) | line 16 |

(Counts are of `ComponentClass="PipeTee"`. `I13` is the only I-series file with a
`PipeTee`; it is otherwise a pure instrumentation example.)

### C01 (richest: positions, geometry, node diameters, component attributes)

C01:1009-1063 (`PipeTee-2`) is representative:

- `C01:1009` — `<PipingComponent ID="PipeTee-2" ComponentClass="PipeTee"
  ComponentClassURI="http://data.posccaesar.org/rdl/RDS427724"
  ComponentName="T_TYPE_CONNECTION_SHAPE">`. `ComponentName` is a
  Proteus-level attribute, **not** a DEXPI field: it is defined in the XSD as
  `xsd:attribute name="ComponentName" type="xsd:string"` (optional) on the shared
  plant-item element base (`ProteusPIDSchema 4.1.1.xsd:716`); the current writer never emits it.
- `C01:1010` — `<ConnectionPoints FlowIn="2" NumPoints="4">`, i.e. `FlowIn="2"`,
  no `FlowOut`.
- Four `<Node>` children: `C01:1011` `<Node ID="PipeTee-2-DefaultNode"/>` (no
  `Type` — the Proteus default node), then three `Type="process"` nodes:
  `C01:1012` `PipingNode-14` (DN 50), `C01:1025` `PipingNode-15` (DN 50),
  `C01:1038` `PipingNode-16` (DN 25). Each process node carries a nested
  `<GenericAttributes>` with `NominalDiameterNumericalValueRepresentationAssignmentClass`,
  `NominalDiameterRepresentationAssignmentClass`,
  `NominalDiameterStandardSpecialization` (`Format="anyURI"`, `ValueURI` set) and
  `NominalDiameterTypeRepresentationAssignmentClass`, plus a `<Position>`.
- `C01:1052-1057` — component `<Position>` (Location/Axis/Reference) and
  `<Scale X="0.0001" Y="0.0001"/>` (graphics only; out of model scope).
- `C01:1058-1062` — component-level `<GenericAttributes Set="DexpiAttributes" Number="3">`
  with `FluidCodeAssignmentClass="MNc"`, `PipingClassCodeAssignmentClass="75HB13"`,
  `PipingComponentNumberAssignmentClass="C1"`.

`FlowIn` values across C01: `PipeTee-2` = `"2"` (C01:1010), all others = `"1"`
(C01:1158, 1231, 1478, 1569). `NumPoints="4"` on all five.

Connections in C01 reference process nodes with the zero-based `<Node>` index
(cf. spec:41479-41483), e.g.:

- `C01:1064` `<Connection FromID="Nozzle-9" FromNode="1" ToID="PipeTee-2" ToNode="1"/>` → index 1 = `PipingNode-14`.
- `C01:1139` `<Connection FromID="PipeTee-2" FromNode="3" ToID="BallValve-2" ToNode="1"/>` → index 3 = the DN 25 branch.
- `C01:1212` `<Connection FromID="PipeTee-2" FromNode="1" ToID="PipeTee-1" ToNode="2"/>` (tee-to-tee).
- `C01:1285`, `1532`, `1623` — further tee-to-tee run connections.
- `C01:1397`, `1735` — tee branch (index 3) to a `BlindFlange`.
- `C01:1550` — tee branch to a `Nozzle`; `C01:1779` — tee run (index 2) to a `FlowOutPipeOffPageConnector`.

**Confirmed pattern: index 1 and 2 are the run, index 3 the branch.**

### C02 (node naming variant, `Scale` present, a dangling connection)

- `C02:300` — same attribute shape, `ComponentName="T_TYPE_CONNECTION_SHAPE"`.
- `C02:301` `<ConnectionPoints FlowIn="1" NumPoints="4">`; nodes named
  `PipeTee-1-Node-0` (C02:302, no `Type` = the default node), `Node-1` (C02:303,
  DN 150), `Node-2` (C02:316, DN 150), `Node-3` (C02:329, DN 80 — the branch).
- `C02:343-345` — component-level `GenericAttributes` with only
  `PipingComponentNumberAssignmentClass="*C1*"`.
- `C02:351` `<Scale X="0.0" Y="0.0"/>` — so `Scale` is optional/meaningless here.
- `C02:353` `ToID="PipeTee-1" ToNode="2"`; `C02:368` `<Connection FromID="PipeTee-1" FromNode="2"/>`
  (a connection with **no** target — the segment simply ends); `C02:456`
  `FromNode="3"` → `OperatedValve-1`.

### I13 (minimal instrumentation-example form)

- `I13:16` — `<PipingComponent ID="PipeTee-1" ComponentClass="PipeTee"
  ComponentClassURI="http://data.posccaesar.org/rdl/RDS427724">` — **no**
  `ComponentName`, no `Position`, no `Scale`, no `GenericAttributes`.
- `I13:17` `<ConnectionPoints FlowIn="1" NumPoints="4">`; `I13:18` default node,
  `I13:19-21` bare `<Node Type="process" ID="PipingNode-1|2|3"/>` with **no**
  `GenericAttributes`.
- `I13:24`, `I13:28`, `I13:48` — connections using indices 2 and 3.

### What the examples do *not* contain

- No `FlowOut` on any `PipeTee`.
- No `ComponentClassURI` on `PipeTee` other than `RDS427724`.
- No `<CustomAttributes>` on a `PipeTee` (only `GenericAttributes`).
- No `PipeTee` outside C01/C02/I13 (not in P01-P04, not in the E-series).

Cross-cutting aside (not specific to `PipeTee`, but visible here): the examples
use **two** `GenericAttributes` sets — `Set="DexpiAttributes"` for the DEXPI
attributes described above, and `Set="DexpiCustomAttributes"` for vendor
attributes with a foreign `AttributeURI` (`C02:58,93,167,212`, e.g.
`BasfLineNumberAssignmentClass` / `http://basf.com/rdl/...` on a
`PipingNetworkSystem`; `I04:7`, `NormalStateRepresentation` /
`http://www.flexpi.org/sandbox/...` on an `ActuatingSystem`). The current writer
hardcodes `Set="DexpiAttributes"` (`serialization.py:317`), so the
`DexpiCustomAttributes` set does not round-trip. Out of scope for `PipeTee`
itself.

## (e) What it would take to add `PipeTee` to the model

Small change — the model is already shaped for it.

1. **Add the class** in `src/dexpigen/piping.py` next to `PipeReducer`/`LineBlind`
   (`piping.py:175-180`):

   ```python
   class PipeTee(PipeFitting):
       component_class: ClassVar[str] = "PipeTee"
       component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS427724"
   ```

   `PipeFitting` already exists as an abstract subclass of `PipingComponent`
   (`piping.py:166-169`), so no hierarchy work is needed.

2. **No new data fields.** `PipingComponent` already declares the four DEXPI data
   fields plus the two `PipeFitting`-observed ones
   (`fluid_code`, `on_hold`, `piping_class_artefact`,
   `pressure_test_circuit_number`, `piping_component_name`,
   `piping_component_number` — `piping.py:120-125`). `PipeFitting`'s own 8 declared
   fields (heat tracing, insulation, `piping_class_code`) are still unmodelled
   across all fittings — adding `PipeTee` neither requires nor delivers them. If
   `PipingClassCode` is wanted, it belongs on `PipeFitting`, not on `PipeTee`.

3. **No serializer change.** `_class_key` already maps every
   `PipingComponent` to the element key `"PipingComponent"`
   (`serialization.py:290-291`), `_emit_piping_component` writes
   `ID`/`ComponentClass`/`ComponentClassURI` + `<ConnectionPoints>` +
   `<GenericAttributes>` + `is referenced by` associations
   (`serialization.py:445-454`), and `CLASS_ORDER["PipingComponent"]`
   (`serialization.py:251-255`) already orders the shared fields. `PipeTee`
   inherits into all of it for free.

4. **`ConnectionPoints` are already correct.** `_emit_connection_points`
   (`serialization.py:475-492`) writes `FlowIn`/`FlowOut` from
   `PipingNodeOwner.flow_in_index`/`flow_out_index` and a `NumPoints` of
   `len(nodes) + 1` for the implicit default node, emitting
   `<Node ID="{dex_id}-DefaultNode"/>` first with no `Type`. That matches
   C01/C02/I13 exactly. The model's convention is **1-based indices into
   `nodes`** (only process nodes are in `nodes`), and `_emit_connection`
   writes `index + 1` for `<Connection ...Node="n">`
   (`serialization.py:500,504`) — which is precisely the zero-based
   `<ConnectionPoints>` index of the spec (spec:41479-41483). So a `PipeTee`
   with `flow_in_index=1` and 3 nodes reproduces the C01/I13 form verbatim.

5. **Optional invariants.** DEXPI says `Nodes` is `*` and unordered
   (spec:41429, 41485), so nothing *must* be enforced. If we want to model the
   T-shape, a `model_validator` requiring exactly 3 process nodes (or
   `flow_in_index` non-null) would be a local convention, not a spec rule. Also
   decide whether `flow_out_index` should ever be set — the spec/XSD allow it,
   the examples never do it.

6. **Open question — `ComponentName`.** C01/C02 emit
   `ComponentName="T_TYPE_CONNECTION_SHAPE"` (C01:1009, C02:300) but I13 does
   not, and it is not a DEXPI field. Either ignore it (writer output won't
   byte-match C01/C02) or add an optional field + attribute emission. The spec does
   not define `ComponentName` as a DEXPI field, but the XSD defines it as an optional
   `xsd:string` attribute (`ProteusPIDSchema 4.1.1.xsd:716`). Resolved in issues/11.

7. **Tests.** Add `PipeTee` to whatever component-vocabulary/round-trip test
   enumerates `PipingComponent` subclasses, and (if `ComponentName` is skipped) a
   note that generated C01/C02 XML is semantically, not textually, equal.

8. **Scope.** `PipeTee` is **not** listed as out of scope anywhere
   (`spec.md:83`, `issues/06-instrument-split.md:35`,
   `issues/08-proteus-serialization.md:45` all name other classes), so this is a
   pure addition; the only coordination point is the extraction vocabulary that
   feeds `component_class`.

---

# 2. `InstrumentationLoopFunction`

## (a) Class identity + URI

| Item | Value | Citation |
| --- | --- | --- |
| Section | 9.15. InstrumentationLoopFunction (p. 946), subsection 9.15.1 Overview | spec:365 (TOC), spec:44618-44619 |
| Class definition | "An identified collection of related `ProcessInstrumentationFunctions` that interact for a known purpose." | spec:44620-44622 |
| Concrete? | Concrete (no "Abstract class" marker; contrast spec:38584) | spec:44620-44622 |
| Supertypes | `CustomAttributeOwner`, `TechnicalItem` | spec:44647-44649 |
| Proteus tag | `<InstrumentationLoopFunction>` | spec:44661 |
| **ComponentClass** | `InstrumentationLoopFunction` | spec:44665 |
| **ComponentClassURI** | `http://sandbox.dexpi.org/rdl/InstrumentationLoopFunction` | spec:44667 |
| RDL reference | `INSTRUMENTATION LOOP FUNCTION` | spec:44662 |
| Example statement | `instrumentationLoopFunction1 : InstrumentationLoopFunction` | spec:44669 |
| Listed as a `TechnicalItem` subtype | yes | spec:5865 |
| XSD element | `<xsd:element name="InstrumentationLoopFunction">` extending `PlantItem`, added in Proteus 4.0.1 alpha | XSD:1911-1917 |
| Allowed as a `<PlantModel>` child | yes (Proteus 4.0.1-alpha instrumentation model) | XSD:2051 |

There is **no** `sandbox` vs `data.posccaesar.org` ambiguity here: both the class
URI and the attribute URI are on `http://sandbox.dexpi.org/rdl/`.

## (b) Fields

`InstrumentationLoopFunction` has exactly **one** declared data field and one
reference attribute.

| Kind | Name | Multiplicity | Type | Citation |
| --- | --- | --- | --- | --- |
| data | `InstrumentationLoopFunctionNumber` | 0..1 | `NullableString` | spec:44642, 44650-44653 |
| reference | `ProcessInstrumentationFunctions` | * | `ProcessInstrumentationFunction` | spec:44644-44646, 44654-44656 |

### `InstrumentationLoopFunctionNumber` (9.15.2, spec:44682-44716)

- "The identification number of the InstrumentationLoopFunction."
  (spec:44685), multiplicity 0..1, type `NullableString` (spec:44686-44687).
- Implemented as a DEXPI **generic attribute** for string values (spec:44690-44691).
- `Name: InstrumentationLoopFunctionNumberAssignmentClass` (spec:44693-44694)
- `AttributeURI: http://sandbox.dexpi.org/rdl/InstrumentationLoopFunctionNumberAssignmentClass` (spec:44695)
- `RDL reference: INSTRUMENTATION LOOP FUNCTION NUMBER ASSIGNMENT CLASS` (spec:44692)
- Example value `"4750.01"` (spec:44697).

### Inherited data/associations

`TechnicalItem` (6.17) is **abstract** and declares **no data attributes**; it
contributes exactly one reference, `ParentStructure` 0..1 →
`TechnicalItemParentStructure`, association type `"is a part of"` on the owner
with opposite `"is a collection including"` (spec:5844-5846, 5873-5879,
5893-5895). `CustomAttributeOwner` contributes the `CustomAttributes *`
composition (spec:44631-44635).

Consequence worth recording: `InstrumentationLoopFunction` is a `TechnicalItem`
but **not** a `TaggedPlantItem`, so it has **no `TagName`** (the tag-like
identifier is `InstrumentationLoopFunctionNumber`). See the `TechnicalItem`
subtype list at spec:5858-5879, where `TaggedPlantItem` and
`InstrumentationLoopFunction` are siblings.

## (c) Compositions and references + Association Type strings

| Role | Multiplicity | Type | Kind | Opposite | Proteus serialization | Association Type (owner side) |
| --- | --- | --- | --- | --- | --- | --- |
| *(top-level)* `InstrumentationLoopFunctions` on `ConceptualModel` | * | `InstrumentationLoopFunction` | composition | 0..1 | `<InstrumentationLoopFunction>` as a **direct child of `<PlantModel>`** | n/a — XML hierarchy, no `Association` (spec:1305-1309) |
| `CustomAttributes` (from `CustomAttributeOwner`) | * | `CustomAttribute` | composition | 0..1 | `<GenericAttributes>` / `<GenericAttribute>` | n/a |
| `ProcessInstrumentationFunctions` | * | `ProcessInstrumentationFunction` | **reference** | 0..1 | `<Association Type="is a collection including" ItemID="..."/>` | **`"is a collection including"`** |
| `ParentStructure` (from `TechnicalItem`) | 0..1 | `TechnicalItemParentStructure` | reference | 0..* | `<Association Type="is a part of" .../>` | `"is a part of"` |

Association strings, verbatim from the spec:

- 9.15.3 (spec:44731-44736): "The attribute is implemented using Proteus
  `<Association>` elements. **Association type for the attribute owner: "is a
  collection including"**. **Opposite association type: "is a part of"**."
  Opposite multiplicity 0..1 (spec:44729).
- The spec's own XML example (spec:44743-44766) shows **both directions**:
  the loop function carries
  `<Association Type="is a collection including" ItemID="processInstrumentationFunction1" />`
  (spec:44748-44751) **and** the referenced PIF carries
  `<Association Type="is a part of" ItemID="instrumentationLoopFunction1" />`
  (spec:44761-44764).
- `TechnicalItem.ParentStructure` uses `"is a part of"` on the item and
  `"is a collection including"` on the structure (spec:5894-5895) — note these
  two strings are the same pair as for `ProcessInstrumentationFunctions`, but on
  different associations; do not conflate them.

### Top-level placement (ConceptualModel 4.2.3, spec:1290-1331)

- `ConceptualModel.InstrumentationLoopFunctions` is a **composition** with
  multiplicity `*` and opposite multiplicity `0..1` (spec:1294-1298).
- "For each `InstrumentationLoopFunction`, the corresponding
  `<InstrumentationLoopFunction>` element is a child of the `<PlantModel>`
  element that corresponds to the `DexpiModel` containing the `ConceptualModel`"
  (spec:1305-1309). The `ComponentClass`/`ComponentClassURI` example is at
  spec:1323-1327.
- The `ConceptualModel` implementation note (spec:1215-1230) lists
  `<InstrumentationLoopFunction>` among the elements whose presence in
  `<PlantModel>` implies a `ConceptualModel` (spec:1221).

## (d) How it is serialized in the examples

Top-level `<InstrumentationLoopFunction>` elements appear in **all 15 I-series
files** and in **C01**; there are **no** instances in C02/C03 or the E-/P-series.

| File | Instances | Numbers (`InstrumentationLoopFunctionNumber`) | `is a collection including` associations |
| --- | --- | --- | --- |
| `I01 Measurement/I01V01-VER.EX01.xml` | 1 | `"01"` | 1 |
| `I02 Control/I02V01-VER.EX01.xml` | 1 | `"02"` | 1 |
| `I03 Measurement and Control/I03V01-VER.EX01.xml` | 1 | `"03"` | 1 |
| `I04 Measurement and Control/I04V01-VER.EX01.xml` | 1 | `"04"` | 1 |
| `I05 Two flow indications and flow ratio control in CCR/I05V01-VER.EX01.xml` | 1 | `"031"` | **4** |
| `I06 CCR flow indication and high alarm, flow control, control valve/I06V01-VER.EX01.xml` | 3 | `"031"`, `"032"`, `"033"` | 3 |
| `I07 Local and CCR pressure indic., alarm and safety switch/I07V01-VER.EX01.xml` | 3 | `"041"`, `"042"`, `"043"` | 3 |
| `I08 Local pressure indication, CCR pressure indication, alarms and switches/I08V01-VER.EX01.xml` | 4 | `"044"`..`"047"` | 4 |
| `I09`..`I12`, `I15` | 1 each | `"09"`..`"12"`, `"15"` | 1 each |
| `I13 Measurement/I13V01-VER.EX01.xml` | 1 | `"13"` | **2** |
| `I14 Measurement/I14V01-VER.EX01.xml` | 1 | `"14"` | **2** |
| `C01 DEXPI Reference P&ID/C01V04-VER.EX01.xml` | 4 | `"4712.01"`, `"4712.02"`, `"4750.01"`, `"4750.03"` | 4 |

### Canonical shape (I01:6-11)

```xml
<InstrumentationLoopFunction ID="InstrumentationLoopFunction-1"
    ComponentClass="InstrumentationLoopFunction"
    ComponentClassURI="http://sandbox.dexpi.org/rdl/InstrumentationLoopFunction">
  <GenericAttributes Set="DexpiAttributes" Number="1">
    <GenericAttribute Name="InstrumentationLoopFunctionNumberAssignmentClass"
        AttributeURI="http://sandbox.dexpi.org/rdl/InstrumentationLoopFunctionNumberAssignmentClass"
        Format="string" Value="01"/>
  </GenericAttributes>
  <Association Type="is a collection including" ItemID="ProcessInstrumentationFunction-1"/>
</InstrumentationLoopFunction>
```

The inverse side, on the referenced bubble (`I01:31`):
`<Association Type="is a part of" ItemID="InstrumentationLoopFunction-1"/>`.

Observations:

- **Always exactly one `<GenericAttributes>` block with exactly one
  `InstrumentationLoopFunctionNumberAssignmentClass`** (`Format="string"`,
  value a quoted string; values seen range `"01"`..`"047"` and
  `"4712.01"`, `"4750.01"`, `"4750.03"`). Position: first child.
- **No `ComponentName`, no `Position`, no `Scale`, no `CustomAttributes`, no
  `ParentStructure` association** on any instance. The inherited
  `ParentStructure` reference is simply unused in the examples.
- **Placement inside `<PlantModel>`:** the I-series files put all loop functions
  immediately after `<PlantInformation>`/`<UnitsOfMeasure>` and before the first
  `<PipingNetworkSystem>` (I01:6, I05:14, I08:6-27, I13:6). `C01` puts them after
  the `<Equipment>` blocks (C01:5286-5309) and before `<Drawing>`. Both are valid
  — the examples give no canonical position.
- **Cardinality varies independently of instance count:** `I05` has **one** loop
  function holding **four** `is a collection including` associations (I05:17-20);
  `I13` has one loop with **two** (I13:10-11); `I08` has four loops with one each.
  A loop function therefore is genuinely 1..* PIFs, and the association can be
  many per loop.
- **Both directions are written.** Every `ItemID` on an `is a collection
  including` association is matched by an `is a part of` association on the
  referenced `ProcessInstrumentationFunction`: e.g. I05:17-20 ↔ the four PIFs;
  I13:10-11 ↔ `ProcessInstrumentationFunction-1` (I13:58) and `-2` (I13:68);
  C01:5290 ↔ the PIF's `is a part of` at C01:2280 (and C01:5296/5302/5308 ↔
  C01:2369/2475/2564).
- C01 loop functions **also** appear in the `.html` rendering
  (`C01V04-VER.EX01.html` contains the string) — same content, not a second source.

## (e) What it would take to add `InstrumentationLoopFunction` to the model

Larger than `PipeTee`: it is a new top-level aggregate with a many-to-many
reference, and it is currently **explicitly out of scope**.

Scope status (primary sources in this repo):

- `.scratch/dexpi-13-inmemory-model/spec.md:83` — "Loop functions beyond
  `ActuatingFunction`: `ActuatingElectricalFunction`,
  `InstrumentationLoopFunction`" is listed under **Out of Scope**.
- `.scratch/dexpi-13-inmemory-model/issues/06-instrument-split.md:35` — same,
  under "Deferred / out of v0.1".
- `.scratch/dexpi-13-inmemory-model/issues/08-proteus-serialization.md:45` —
  `InstrumentationLoopFunction` listed under "Out of scope (unchanged from spec)".
- `.scratch/dexpi-13-inmemory-model/map.md:45` — noted as not yet covered.

So adding it means **first** an explicit scope decision to pull it back in (a
spec/map/issue update), not just code.

Concrete work:

1. **New class** (natural home `src/dexpigen/instrumentation.py`, next to
   `ProcessInstrumentationFunction` at `instrumentation.py:36-90`):

   ```python
   class InstrumentationLoopFunction(DexpiBaseModel):
       component_class: ClassVar[str] = "InstrumentationLoopFunction"
       component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/InstrumentationLoopFunction"

       instrumentation_loop_function_number: str | None = None
       process_instrumentation_functions: list[ProcessInstrumentationFunction] = Field(default_factory=list)
   ```

   Reference (not composition) semantics: the same PIF could in principle belong
   to more than one loop; the spec gives the opposite multiplicity 0..1
   (spec:44729), so a back-pointer set by this object, not ownership, is the
   right shape (contrast the ownership `_owner` pattern used by
   `PipingNodeOwner._adopt_node`, `piping.py:53-57`).

2. **Field naming collision to resolve.** `ProcessInstrumentationFunction`
   already has a data field `process_instrumentation_functions: str | None`
   (`instrumentation.py:53`) — that is the DEXPI *string* field
   `ProcessInstrumentationFunctionsAssignmentClass` (the function letters, e.g.
   `"I"`, `"T"`; see `I13:56`). The loop function's reference is the DEXPI
   *reference* attribute `ProcessInstrumentationFunctions` →
   `ProcessInstrumentationFunction` (spec:44654-44656). Same DEXPI concept name,
   two different things. The loop side needs a distinct Python name (e.g.
   `process_instrumentation_functions` on the loop vs
   `process_instrumentation_functions_code` on the PIF) or the existing field
   should be renamed — either way this must be settled before coding.

3. **Generic-attribute emission needs two small edits.** The name suffix comes
   free: `_assignment_class` (`serialization.py:149-150`) turns
   `instrumentation_loop_function_number` into
   `InstrumentationLoopFunctionNumberAssignmentClass`, and the fallback URI is
   `SANDBOX + name` (`serialization.py:319`) =
   `http://sandbox.dexpi.org/rdl/InstrumentationLoopFunctionNumberAssignmentClass`,
   exactly the spec's `AttributeURI` (spec:44695). But `_field_attributes`
   (`serialization.py:159-216`) is an **explicit `isinstance` chain**, not a
   naming convention, so a branch must be added:
   `elif isinstance(obj, InstrumentationLoopFunction): add(_string("InstrumentationLoopFunctionNumber", obj.instrumentation_loop_function_number))`.
   Also add the declaration order:
   `CLASS_ORDER["InstrumentationLoopFunction"] = ["InstrumentationLoopFunctionNumberAssignmentClass"]`
   (`CLASS_ORDER` at `serialization.py:222`; cf. `"ActuatingSystem"` at 256).
   Note `_field_attributes` is checked *before* `custom_attributes` is appended
   (`_emit_generic_attributes`, `serialization.py:311-317`), and the examples put
   the number first, so a single-entry `CLASS_ORDER` is enough.

4. **`ConceptualModel` extension** (`model.py:18-52`): add
   `instrumentation_loop_functions: list[InstrumentationLoopFunction]` plus an
   `add_instrumentation_loop_function` helper, mirroring
   `add_actuating_system` (`model.py:49-52`).

5. **Writer work** in `src/dexpigen/serialization.py`:
   - `_class_key` branch returning `"InstrumentationLoopFunction"`
     (`serialization.py:279-308`).
   - `_emit_instrumentation_loop_function(w, loop)`: open
     `<InstrumentationLoopFunction ID ComponentClass ComponentClassURI>`, then
     `_emit_generic_attributes`, then one
     `w.leaf("Association", _attrs(Type="is a collection including", ItemID=pif.dex_id))`
     per referenced PIF, then close. Order matches every example.
   - **The inverse association must be added to `_emit_pif`**
     (`serialization.py:544-556`). The loop function holds the reference, so
     either give the PIF a back-reference `PrivateAttr` set when it is added to a
     loop (cheap, mirrors `_owner` at `instrumentation.py:109,120`), or resolve
     it at write time by scanning the model exactly as `_actuating_function_of`
     does (`serialization.py:344-349`; `_MODEL` is already set at
     `serialization.py:585-586`). The examples show the `is a part of`
     association appearing **after** the `GenericAttributes` and interleaved with
     `is logical end of`/`is logical start of` (I13:58-59, I13:68-70) — order
     among associations varies, so any order is defensible.
   - Add the top-level emission loop in `to_proteus_xml`
     (`serialization.py:584-602`). Decide the position among the existing
     `actuating_systems` → `piping_network_systems` → `process_instrumentation_functions`
     → `equipment` loops; the examples give no canonical answer (`I*` put loop
     functions first, `C01` puts them after `Equipment`). Putting them last is
     the least disruptive for existing golden-file tests; putting them first
     matches the I-series, which are the only examples that exercise this class.

6. **Adjacent inconsistency to be aware of:** `_emit_pif` currently hardcodes
   `ComponentClass="ProcessInstrumentationFunction"` instead of using
   `pif.component_class` (`serialization.py:545-548`), so a
   `ProcessControlFunction` (declared at `instrumentation.py:93-96`) is written
   with the parent's `ComponentClass`. Adding a third PIF-shaped class is a good
   moment to switch to `pif.component_class` / `pif.component_class_uri`.

7. **Do not model** (unsupported/unused in the primary sources):
   `ParentStructure` (inherited from `TechnicalItem`, never present on any
   example loop function), `TagName` (the class is not a `TaggedPlantItem`), and
   the Proteus `<PlantItem>` base (XSD:1912-1917) beyond what `DexpiBaseModel`
   already provides.

8. **Tests.** A round-trip over an I-series file exercises everything at once:
   one loop function with `InstrumentationLoopFunctionNumberAssignmentClass`
   plus `is a collection including` and the matching `is a part of` on the PIF.
   `I05` (1 loop, 4 PIFs) and `I08` (4 loops, 1 PIF each) are the two boundary
   cases; `I13` (1 loop, 2 PIFs) additionally carries a `PipeTee`, so it covers
   both classes in this document.
