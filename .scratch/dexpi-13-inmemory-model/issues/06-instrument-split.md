# Decide the Instrument model split

Type: grilling
Status: resolved
Blocked by: 01

## Question

Extraction has a single Instrument (attributes including tag). DEXPI 1.3 splits sensing, functions, loops, and signal conveying.

Which 1.3 classes are in v0.1, which attributes are first-class vs generic, and how a SignalLine attaches without graphics?

## Answer

The extraction `Instrument` maps to **`ProcessInstrumentationFunction`** (the bubble). v0.1 does not model the sensing or device layers; the DEXPI split collapses to bubble + loop function + signal.

**In v0.1:**

- `ProcessInstrumentationFunction` — the bubble. Tag = `ProcessInstrumentationFunctionNumber` + `ProcessInstrumentationFunctionCategory` + `ProcessInstrumentationFunctionModifier` + `ProcessInstrumentationFunctions` (all `0..1`). These four are first-class Pydantic fields; every other DEXPI field (`Location`, `PanelIdentificationCode`, `DeviceInformation`, `TypicalInformation`, `VendorCompanyName`, `VotingSystemRepresentation`, `GmpRelevance`, `GuaranteedSupplyFunction`, `QualityRelevance`, `SafetyRelevanceClass`) goes into a generic `CustomAttribute` bag.
- `ProcessControlFunction` — a subtype of `ProcessInstrumentationFunction` (same bubble, `ComponentClass="ProcessControlFunction"`) for control/safeguarding systems; extraction labels it "equipment" but it is a function.
- `ActuatingFunction` — the control-valve loop function (already in from tickets 03/04). Signal lines attach here, not to `ActuatingSystem`.
- `ActuatingSystem` + `ControlledActuator` + `OperatedValveReference` + `Positioner` — control-valve assembly (unchanged).
- `SignalConveyingFunction` — the signal line (concrete; has its own `ComponentClass`). Lives in a top-level `ConceptualModel` collection; `Source`/`Target` are `0..1` references (no lower bound — a dangling signal is valid; completeness is the mapper's job). Subclasses `SignalLineFunction`/`MeasuringLineFunction` are not generated in v0.1.
- `FlowInSignalOffPageConnector` / `FlowOutSignalOffPageConnector` — signal off-page connectors.

**Signal endpoints in v0.1** (DEXPI-allowed, restricted to in-scope types):

- `Source`: `ProcessInstrumentationFunction`, `ActuatingFunction`, `FlowInSignalOffPageConnector`.
- `Target`: `ProcessInstrumentationFunction`, `ActuatingFunction`, `FlowOutSignalOffPageConnector`.

**Deferred / out of v0.1:**

- `Transmitter` (physical device) — extraction yields one Instrument entity, no separate device.
- `PrimaryElement` / `MeasuringElement` / `FlowDetector` (sensing). Consequence: the instrument↔process-line connection has no DEXPI-native representation without the sensing layer, so it is not modeled in v0.1 (documented loss).
- `ProcessSignalGeneratingFunction`, `ActuatingElectricalFunction`, `InstrumentationLoopFunction`.
- `SignalLineFunction` / `MeasuringLineFunction` (Messlinie) — extraction parses line styles visually (dashed/x-line) and cannot distinguish signal vs measuring lines; map the dashed edge to the general `SignalConveyingFunction` instead of asserting `SignalLineFunction` (less lossy).

## Comments

- `InformationFlow` is the Proteus tag for the `SignalConveyingFunction` hierarchy; the concrete discriminator is `ComponentClass`/`ComponentClassURI` (`SignalLineFunction` vs `MeasuringLineFunction`), not `ComponentName` (a localized label such as "Wirkungslinie").
- Control-valve linkage ("actuator + valve combined") stays the factory + `OperatedValveReference.Valve` reference from tickets 03/04 — no facade class.
- Revised 2026-09-23: dashed edges map to the general `SignalConveyingFunction` (concrete, not abstract), not `SignalLineFunction` — so the model does not assert signal-vs-measuring.
