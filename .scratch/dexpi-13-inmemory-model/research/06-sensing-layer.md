# The DEXPI 1.3 sensing / device layer

## Scope and sources

This note answers: *how does a `ProcessInstrumentationFunction` (PIF, the instrument bubble) connect to the physical piping process and "measure something"?* It covers the full sensing layer — the function side (`ProcessSignalGeneratingFunction`) and the device side (`ProcessSignalGeneratingSystem`, `PrimaryElement`, `Transmitter`, `InlinePrimaryElement`, `OfflinePrimaryElement`, `FlowDetector`) — and the association graph that ties them to the piping and to the information-flow functions.

Primary sources, both in this repo:

- **Spec** — `data/DEXPI-PID-Specification-1.3.pdf.md` (DEXPI P&ID Specification 1.3; Markdown conversion of the PDF). All "spec:NNNN" line citations below point into this file.
- **Proteus schema** — `data/schemas/ProteusPIDSchema 4.1.1.xsd` (the XML content model actually used by the example files).
- **Examples** — `data/example_pids/**/*.xml` (all 16 `I##` measurement/control sheets, plus `C01`, `C02`).

Companion notes: `01-dexpi-13-class-mapping.md` (class mapping to the HTML reference), `04-proteus-serialization.md` (writer format).

---

## 1. The full sensing-layer class set and its relationships

Two disjoint sides, joined at exactly two points (composition + `SensingLocation`):

### 1.1 Function side (the "what is measured" abstraction)

| Class | Abstract? | Supertype(s) | Spec |
| --- | --- | --- | --- |
| `ProcessInstrumentationFunction` | no | `CustomAttributeOwner`, `SignalConveyingFunctionSource`, `SignalConveyingFunctionTarget`, `TechnicalItem` (subtype: `ProcessControlFunction`) | spec:45969-45977 |
| `ProcessSignalGeneratingFunction` | no | `CustomAttributeOwner`, `SignalConveyingFunctionSource`, `TechnicalItem` | spec:46809-46813 |
| `SensingLocation` | **yes** | — (subtypes: `Nozzle`, `PipingComponent`, `PipingNetworkSegment`) | spec:47278-47297 |
| `SignalConveyingFunction` | no | `CustomAttributeOwner` (subtypes: `MeasuringLineFunction`, `SignalLineFunction`) | spec:47312-47347 |
| `MeasuringLineFunction` | no | `SignalConveyingFunction` — "Information flow function for measured values" | spec:44768-44803 |
| `SignalLineFunction` | no | `SignalConveyingFunction` — "Information flow function for signals" | spec:47713-47743 |
| `SignalConveyingFunctionSource` | **yes** | subtypes: `ActuatingFunction`, `FlowInSignalOffPageConnector`, `ProcessInstrumentationFunction`, `ProcessSignalGeneratingFunction` | spec:47643-47657 |
| `SignalConveyingFunctionTarget` | **yes** | subtypes: `ActuatingElectricalFunction`, `ActuatingFunction`, `FlowOutSignalOffPageConnector`, `ProcessInstrumentationFunction` | spec:47678-47693 |

Note the asymmetry: **`ProcessSignalGeneratingFunction` is only ever a `SignalConveyingFunctionSource`, never a `Target`** — it is the origin of the measuring line, and the PIF is where the measuring line ends. `ProcessInstrumentationFunction` is both source and target (spec:47655, 47693).

### 1.2 Device side (the physical artefact)

| Class | Abstract? | Supertype(s) | Proteus tag | `ComponentClass` / URI | Spec |
| --- | --- | --- | --- | --- | --- |
| `ProcessSignalGeneratingSystem` | no | `CustomAttributeOwner`, `TechnicalItem` (subtype: `FlowDetector`) | `<ProcessSignalGeneratingSystem>` | `ProcessSignalGeneratingSystem` / `…/rdl/ProcessSignalGeneratingSystem` | spec:47020-47089 |
| `FlowDetector` | no | `ProcessSignalGeneratingSystem` | `<ProcessSignalGeneratingSystem>` | `FlowDetector` (RDL "FLOW DETECTOR"; URI not printed) | spec:44361-44396 |
| `PrimaryElement` | no | `CustomAttributeOwner` (subtypes: `InlinePrimaryElementReference`, `OfflinePrimaryElement`) | `<ProcessSignalGeneratingSystemComponent>` | `PrimaryElement` / `…/rdl/PrimaryElement` | spec:45770-45820 |
| `InlinePrimaryElementReference` | no | `PrimaryElement` | `<ProcessSignalGeneratingSystemComponent>` | `InlinePrimaryElementReference` / `…/rdl/InlinePrimaryElementReference` | spec:44514-44565 |
| `OfflinePrimaryElement` | no | `PrimaryElement` | `<ProcessSignalGeneratingSystemComponent>` | `OfflinePrimaryElement` / `…/rdl/OfflinePrimaryElement` | spec:44815-44892 |
| `Transmitter` | no | `CustomAttributeOwner` | `<ProcessSignalGeneratingSystemComponent>` | `Transmitter` / `http://data.posccaesar.org/rdl/RDS267929` | spec:48130-48181 |
| `InlinePrimaryElement` | no | `PipingComponent` (so it *is* piping) | `<PipingComponent>` | `InlinePrimaryElement` / `…/rdl/InlinePrimaryElement` | spec:36358-36445 |
| `FlowMeasuringElement` and siblings | no | `InlinePrimaryElement` | `<PipingComponent>` | `FlowMeasuringElement` / `…/rdl/FlowMeasuringElement` | spec:35860-35905 |

**There is no DEXPI class named `MeasuringElement`.** That is an ISO 15926 term used in prose only ("A FLOW MEASURING ELEMENT is a MEASURING ELEMENT that is used to measure FLOW RATE", spec:35863). DEXPI models it as the `InlinePrimaryElement` family.

`InlinePrimaryElement` direct subtypes (spec:36393-36407): `CustomInlinePrimaryElement`, `ElectromagneticFlowMeter`, `FlowMeasuringElement`, `FlowNozzle`, `MassFlowMeasuringElement`, `PositiveDisplacementFlowMeter`, `TurbineFlowMeter`, `VariableAreaFlowMeter`, `VenturiTube`, `VolumeFlowMeasuringElement`.

`OfflinePrimaryElement` own fields are all connection/diameter/metadata: `ConnectionNominalDiameter*`, `FluidCode`, `HeatTracingType`, `InsulationThickness`, `InsulationType`, `LocationNominalDiameter*`, `LowerLimitHeatTracingTemperature` (spec:44832-44865). Despite the name it is *not* an `InlinePrimaryElement`; it is a sibling branch that is simply "not part of a PipingNetworkSegment" (spec:44819).

### 1.3 The two join points

1. **Function → device**: `ProcessSignalGeneratingFunction.Systems` → `ProcessSignalGeneratingSystem` (0..1), realised as an association `"is fulfilled by"` / `"fulfills"` (spec:46972-46984, example spec:47000-47018). This is *optional* — and unused by every example in `data/example_pids/`.
2. **Function → physics**: `ProcessSignalGeneratingFunction.SensingLocation` → `SensingLocation` (0..1), realised as `"is located in"` / `"is the location of"` (spec:46887-46898). The `SensingLocation` is a `Nozzle`, a `PipingComponent` (incl. `InlinePrimaryElement`), or a `PipingNetworkSegment`.

### 1.4 Compositions (XML child nesting)

- `ProcessInstrumentationFunction` composes `ProcessSignalGeneratingFunctions *` (spec:46018, 46468-46481), plus `ActuatingElectricalFunctions *`, `ActuatingFunctions *`, `SignalConnectors *`, `SignalConveyingFunctions *` (spec:46013-46022). XSD content model: `data/schemas/ProteusPIDSchema 4.1.1.xsd:1919-1938` — a single `xsd:choice maxOccurs="unbounded"` of `ActuatingFunction | ProcessSignalGeneratingFunction | InformationFlow | SignalOffPageConnector | ActuatingElectricalFunction`.
- `ProcessSignalGeneratingSystem` composes `CustomComponents *` (`CustomProcessSignalGeneratingSystemComponent`), `PrimaryElement` 0..1, `Transmitter` 0..1 (spec:47064-47069, 47128-47132, 47206-47212). XSD: `…xsd:2006-2025`.
- `ProcessSignalGeneratingSystem` has the "opposite end" label `ProcessSignalGeneratingSystems` drawn in its diagram (spec:47032-47035) but **no formal attribute** — the only formal link is `Systems` on the PSGF side.

---

## 2. The "instrument measures the process" association graph

```
                    +----------------------------------------------+
                    |      ProcessInstrumentationFunction          |  (the bubble)
                    |  (SignalConveyingFunctionSource + Target)     |
                    +----------------------------------------------+
                       |  composition "ProcessSignalGeneratingFunctions" (0..*)
                       |  = XML child element, no <Association>
                       v
                +--------------------------------+
                | ProcessSignalGeneratingFunction |  "the sensor"
                |  - PSGFNumber 0..1              |
                |  - SensorType 0..1              |
                +--------------------------------+
                  |                             |
  "is located in" | 0..1               "is fulfilled by" 0..1
  (opposite:      |                    (opposite: "fulfills", 0..*)
   "is the        v                    v
   location of",  +-------------------------+     +-------------------------------+
   0..*)          |     SensingLocation     |     | ProcessSignalGeneratingSystem |
                  |      (abstract)         |     |  - PSGSNumber 0..1            |
                  |  = Nozzle               |     |  - TypicalInformation 0..1    |
                  |  | PipingComponent      |     |  composes PrimaryElement 0..1 |
                  |  | PipingNetworkSegment |     |  composes Transmitter    0..1 |
                  +-------------------------+     |  composes CustomComponents *  |
                        ^                           +-------------------------------+
                        |                              ^ subtype: FlowDetector
                        |                              |
                        |                    +-------------------------------+
                        |                    | PrimaryElement                |
                        |                    |  + InlinePrimaryElement-      |
                        |                    |    Reference 0..1             |
                        |                    +-------------------------------+
                        |                        |
                        |                        | "refers to" / "is referenced by"
                        |                        v
                        |                    InlinePrimaryElement, which is
                        |                    itself a PipingComponent subtype
                        |                    (so it lives *inside* the pipe)
                        |
        +-------------------------------+
        | PipingNetworkSystem           |
        |   + PipingNetworkSegment      |
        |       <Connection> to         |
        |       PipingComponent (e.g.   |
        |         BlindFlange,          |
        |         FlowMeasuringElement) |
        |   + Nozzle (on Equipment)     |
        +-------------------------------+
```

And separately, the measuring line:

```
ProcessSignalGeneratingFunction  --"is logical start of"-->  MeasuringLineFunction
ProcessInstrumentationFunction   <--"has logical end"------  MeasuringLineFunction
```

### 2.1 Exact `Type=` strings (all verified against both the spec and the examples)

| Owner element | Attribute | Direction | `Association Type` | Opposite `Type` | Spec |
| --- | --- | --- | --- | --- | --- |
| `ProcessSignalGeneratingFunction` | `SensingLocation` 0..1 → `SensingLocation` | outward | **`is located in`** | **`is the location of`** (opposite mult. 0..*) | spec:46887-46898 |
| `Nozzle` / `PipingComponent` / `PipingNetworkSegment` | back-reference | outward | **`is the location of`** | `is located in` | spec:46927-46930; PipingComponent supertype list spec:38616 |
| `ProcessSignalGeneratingFunction` | `Systems` 0..1 → `ProcessSignalGeneratingSystem` | outward | **`is fulfilled by`** | **`fulfills`** | spec:46972-46984 |
| `ProcessSignalGeneratingSystem` | back-reference | outward | **`fulfills`** | `is fulfilled by` | spec:47013-47015 |
| `MeasuringLineFunction` / `SignalLineFunction` (`SignalConveyingFunction`) | `Source` 0..1 → `SignalConveyingFunctionSource` | outward | **`has logical start`** | **`is logical start of`** | spec:47543-47556 |
| `SignalConveyingFunctionSource` (PSGF, PIF, `ActuatingFunction`, `FlowInSignalOffPageConnector`) | back-reference | outward | **`is logical start of`** | `has logical start` | spec:47581-47591 |
| `SignalConveyingFunction` | `Target` 0..1 → `SignalConveyingFunctionTarget` | outward | **`has logical end`** | **`is logical end of`** | spec:47594-47606 |
| `SignalConveyingFunctionTarget` (PIF, `ActuatingFunction`, …) | back-reference | outward | **`is logical end of`** | `has logical end` | spec:47631-47639 |
| `InlinePrimaryElementReference` | `InlinePrimaryElement` 0..1 → `InlinePrimaryElement` | outward | **`refers to`** | **`is referenced by`** | spec:44571-44615 |

Note on wording: the spec's own prose is sometimes mangled by the PDF→Markdown conversion ("Association type for the attribute ower" = "…for the attribute **owner**"). The strings above are the ones that actually appear in the `<Association Type="…">` examples.

### 2.2 Cardinalities worth noting

- `PSGF.SensingLocation` is **0..1**, and its opposite is **0..\*** — so one pipe point can be the sensing location of several `ProcessSignalGeneratingFunction`s. `I07` does exactly this: `PipingNetworkSegment-1` carries two `is the location of` associations, one for `ProcessSignalGeneratingFunction-1` and one for `-2` (`data/example_pids/I07 …/I07V01-VER.EX01.xml:26-27`).
- `PIF.ProcessSignalGeneratingFunctions` is **\***, opposite **0..1** — a PSGF belongs to exactly one PIF (spec:46472-46475).
- The `Systems` link is 0..1 / 0..* (spec:46976-46979).
- `MeasuringLineFunction.Source` is 0..1 with opposite 0..* (spec:47547-47549), so one PSGF can start many measuring lines.

### 2.3 Note: the sensing relation is *only* on `ProcessSignalGeneratingFunction`

There is **no** direct association from `ProcessInstrumentationFunction` to a piping element, and no `is located in` on the PIF. The instrument's physical anchoring to the process always travels through the nested `ProcessSignalGeneratingFunction`. Confirmed by every example: the only `is located in` owners in the corpus are `ProcessSignalGeneratingFunction` elements.

---

## 3. The `ProcessSignalGeneratingFunction` class specifically

**Definition** (spec:46777-46778): "A function for instrumentation and/or control structures relating to Process Engineering."

**Supertypes** (spec:46809-46813): `CustomAttributeOwner`, `SignalConveyingFunctionSource`, `TechnicalItem`.

**Attributes (data)** (spec:46814-46820):

| Name | Multiplicity | Type | RDL / Proteus |
| --- | --- | --- | --- |
| `ProcessSignalGeneratingFunctionNumber` | 0..1 | `NullableString` | generic attribute `ProcessSignalGeneratingFunctionNumberAssignmentClass`, URI `…/rdl/ProcessSignalGeneratingFunctionNumberAssignmentClass` (spec:46849-46865); example value `"TT4750.03"` (spec:46867) — "usually contains the identifier of the ProcessInstrumentationFunction that includes the ProcessSignalGeneratingFunction" (spec:46851-46853) |
| `SensorType` | 0..1 | `NullableString` | generic attribute `SensorTypeAssignmentClass`, URI `…/rdl/SensorTypeAssignmentClass` (spec:46934-46946); example value `"MDM"` (spec:46949) |

**Attributes (reference)** (spec:46821-46824):

| Name | Multiplicity | Type | Realisation |
| --- | --- | --- | --- |
| `SensingLocation` | 0..1 | `SensingLocation` | `<Association Type="is located in" ItemID="…"/>`; opposite 0..* |
| `Systems` | 0..1 | `ProcessSignalGeneratingSystem` | `<Association Type="is fulfilled by" ItemID="…"/>` |

**Proteus implementation** (spec:46825-46833): plain element with RDL reference.

```xml
<ProcessSignalGeneratingFunction
  ID="processSignalGeneratingFunction1"
  ComponentClass="ProcessSignalGeneratingFunction"
  ComponentClassURI="http://sandbox.dexpi.org/rdl/ProcessSignalGeneratingFunction" ...>
  ...
</ProcessSignalGeneratingFunction>
```

**How it is nested.** It is a *composition child of the PIF*, not a top-level object (spec:46468-46481: "The element for the attribute value (a ProcessSignalGeneratingFunction) is a child of the `<ProcessInstrumentationFunction>` element for the attribute owner"). XSD: `…xsd:1924-1927` puts `ProcessSignalGeneratingFunction` in the PIF's child choice.

The **canonical minimal instance** is `I01` — `data/example_pids/I01 Measurement/I01V01-VER.EX01.xml`:

```xml
<!-- lines 12-23: the pipe point -->
<PipingNetworkSystem ID="PipingNetworkSystem-1" ...>
  <PipingNetworkSegment ID="PipingNetworkSegment-1" ...>
    <PipingComponent ID="BlindFlange-1" ComponentClass="BlindFlange" ComponentClassURI="http://data.posccaesar.org/rdl/RDS414719">
      ...
      <Association Type="is the location of" ItemID="ProcessSignalGeneratingFunction-1"/>   <!-- line 19 -->
    </PipingComponent>
    <Connection FromID="Nozzle-1" FromNode="1" ToID="BlindFlange-1" ToNode="1"/>
  </PipingNetworkSegment>
</PipingNetworkSystem>

<!-- lines 24-41: the instrument -->
<ProcessInstrumentationFunction ID="ProcessInstrumentationFunction-1" ...>
  <Association Type="is a part of" ItemID="InstrumentationLoopFunction-1"/>
  <Association Type="is logical end of" ItemID="MeasuringLineFunction-1"/>
  <ProcessSignalGeneratingFunction ID="ProcessSignalGeneratingFunction-1" ...>     <!-- line 33: nested -->
    <Association Type="is located in" ItemID="BlindFlange-1"/>                     <!-- line 34 -->
    <Association Type="is logical start of" ItemID="MeasuringLineFunction-1"/>     <!-- line 35 -->
  </ProcessSignalGeneratingFunction>
  <InformationFlow ID="MeasuringLineFunction-1" ComponentClass="MeasuringLineFunction" ...>
    <Association Type="has logical start" ItemID="ProcessSignalGeneratingFunction-1"/>
    <Association Type="has logical end" ItemID="ProcessInstrumentationFunction-1"/>
  </InformationFlow>
</ProcessInstrumentationFunction>
```

### 3.1 What the examples actually do

Every one of the 22 `ProcessSignalGeneratingFunction` instances in `data/example_pids/` — spread over 15 files (`C01`, `C02`, `I01`, `I03`–`I11`, `I13`–`I15`; `I02` and `I12` are control-only and have none) — uses exactly the same shape:

- nested inside a `ProcessInstrumentationFunction`,
- `is located in` → a `SensingLocation`,
- `is logical start of` → a `MeasuringLineFunction` that is itself nested in the same PIF,
- and *never* uses `Systems`, `PrimaryElement`, `Transmitter`, or `ProcessSignalGeneratingSystem`.

Observed `SensingLocation` targets across the corpus:

| Target class | Examples |
| --- | --- |
| `PipingNetworkSegment` | `I07 …/I07V01-VER.EX01.xml:53`, `I05 …/I05V01-VER.EX01.xml:89,112` (`PipingNetworkSegment-1`/`-2`) |
| `PipingComponent` (`BlindFlange`) | `I01 …/I01V01-VER.EX01.xml:34`, `C01 …/C01V04-VER.EX01.xml:2296, 2403`, `C02 …/C02V03-VER.EX02.xml:1091, 1196` |
| `PipingComponent` (`FlowMeasuringElement` = an `InlinePrimaryElement`) | `I11 …/I11V01-VER.EX01.xml:39`, `I04 …/I04V01-VER.EX01.xml` (PipingNetworkSystem-2), `I14 …/I14V01-VER.EX01.xml:48` |
| `Nozzle` | `C01 …/C01V04-VER.EX01.xml:5216` (`ProcessSignalGeneratingFunction-3`, whose PIF also carries `TT4750.03`) |
| `Equipment` (`Chamber`, `PressureVessel`) | the remaining `is located in` hits belong to the *plant structure* association (`Equipment`→`PlantStructureItem`), not to a PSGF — do not confuse them |

Note that when the sensing location is an `InlinePrimaryElement`, the XML element is `<PipingComponent ComponentClass="FlowMeasuringElement">` with `ComponentClassURI="http://sandbox.dexpi.org/rdl/FlowMeasuringElement"` and it participates in the segment via `<Connection>` like any other component (`data/example_pids/I11 Measurement/I11V01-VER.EX01.xml:15-25`). Its only own attribute in these files is `PipingComponentNumber` (`"FE 11"`).

`C01` additionally shows the *graphical* half of a measuring line: the `InformationFlow` element carries a `<Connection FromID="BlindFlange-1" ToID="ProcessInstrumentationFunction-1" FromNode="2" ToNode="2"/>` (`C01 …/C01V04-VER.EX01.xml:2289`), i.e. a drawn line from the pipe component's process node to the bubble. That is presentation, not semantics.

---

## 4. What subset is minimal to model "PIF measures a pipe point"

### 4.1 Strict minimum (matches every example in the corpus)

Four classes and three associations. Nothing else is needed — the physical device layer is entirely optional in DEXPI:

1. `ProcessInstrumentationFunction` — already in the model.
2. **`ProcessSignalGeneratingFunction`** — new. Fields: `ProcessSignalGeneratingFunctionNumber` (0..1 str), `SensorType` (0..1 str). Owned by (composed into) the PIF.
3. `MeasuringLineFunction` — already in the model (as `SignalConveyingFunction` family). Needs, on the sensing side, the `Source = PSGF` link.
4. `SensingLocation` — **not a new class in the object graph**: it is an interface-like abstract role played by existing `Nozzle` / `PipingComponent` / `PipingNetworkSegment` objects.

Associations to add:

- `PIF 1 —composes *→ PSGF` (XML child; no `Type` string; opposite 0..1).
- `PSGF —"is located in"→ <piping element>` (0..1), with the mirrored `"is the location of"` on the piping element (0..*).
- `MeasuringLineFunction —"has logical start"→ PSGF` / `PSGF —"is logical start of"→ MeasuringLineFunction`, alongside the already-modelled `has logical end` → PIF.

In the in-memory model, "which pipe point does this instrument measure?" is therefore a *single dereference*: `pif.process_signal_generating_functions[0].sensing_location`, plus the matching back-reference on the piping element so the graph is navigable from the pipe side too (the DEXPI graph stores the relation twice, once per direction — the user's remark "в dex графе все связи описаны" holds).

### 4.2 Optional extension, in cost order

Ranked by how much of the spec they unlock for how little modelling:

1. **`SensorType` / `PSGFNumber`** — trivial strings, already implied by (2). Both are generic attributes in Proteus, so the writer needs no new element.
2. **`InlinePrimaryElement` as a `SensingLocation`** — no new class needed if `PipingComponent` is already modelled as a generic piping item with a `ComponentClass` string; it is only a `ComponentClass` value (`FlowMeasuringElement`, `VenturiTube`, `FlowNozzle`, …). Needed if the model wants to distinguish "the sensor *is* an orifice plate in the line" from "the sensor taps a blind flange".
3. **`ProcessSignalGeneratingSystem` + `PrimaryElement` + `Transmitter`** — the full ISO-15926 device decomposition. It is real (spec:47020-47276, 45770-45820, 48130-48170) but **zero examples use it**, and it adds three classes, a composition tree, and three more `Type` strings for no gain in answering "what does this instrument measure". Recommended: leave out of the first cut.
4. **`OfflinePrimaryElement`** — a `PrimaryElement` deliberately *outside* the piping; only relevant for fields/lab analysers. Leave out.
5. **`FlowDetector`** — a `ProcessSignalGeneratingSystem` subtype (`ComponentClass="FlowDetector"`, tag `<ProcessSignalGeneratingSystem>`). Strictly a device-side class; irrelevant to the function-level graph.

### 4.3 Practical caveat for the writer

Because the PSGF is a **composition child** of the PIF while the *piping* object it references is a top-level object elsewhere in the document, the PSGF's `SensingLocation` must be written as an `<Association>` (forward + back-reference on the piping element), not as nesting. The PIF→PSGF link must be written as nesting (a child element). This mirrors the spec's own two mechanisms ("XML hierarchy of the Proteus file" vs "using Proteus `<Association>` elements") and matches every example file.

### 4.4 Round-trip invariant to preserve

On read and on write: every `is located in` on a PSGF must be mirrored by an `is the location of` on the target piping element, and every PSGF must be nested in exactly one PIF (`Opposite multiplicity: 0..1`, spec:46475). `I01` and `C01` both violate nothing here; a validator can assert both directions.
