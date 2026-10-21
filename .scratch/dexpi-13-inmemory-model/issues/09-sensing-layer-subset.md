# Decide the v0.2 sensing-layer subset

Type: grilling
Status: resolved
Blocked by: research/06-sensing-layer

## Question

Which DEXPI sensing/device classes do we model in v0.2 so a `ProcessInstrumentationFunction` can be connected to the piping process it measures? The candidates are `ProcessSignalGeneratingFunction` plus the physical devices (`PrimaryElement`, `Transmitter`, `MeasuringElement`, `FlowDetector`, ...). Decide the minimal subset, the compositions/references (and their `Association Type` strings), and where each object lives (top-level, under the PIF, under the measured piping component).

## Answer

Model the **strict minimum**: `ProcessSignalGeneratingFunction` (PSGF) plus the `SensingLocation` role and one piping class. No ISO-15926 device decomposition.

### Class identity

- Concrete `ProcessSignalGeneratingFunction(DexpiBaseModel, SignalConveyingFunctionSource)` in `instrumentation.py` — it is *only ever* a `SignalConveyingFunctionSource`, never a `Target`.
  `component_class = "ProcessSignalGeneratingFunction"`, `component_class_uri = "http://sandbox.dexpi.org/rdl/ProcessSignalGeneratingFunction"`.
- It is a **composition child of the PIF**, not a top-level object.

### Fields

- `process_signal_generating_function_number: str | None = None`
- `sensor_type: str | None = None`
- `sensing_location: SensingLocation | None = None` (reference)
- added to `ProcessInstrumentationFunction` as `process_signal_generating_functions: list[ProcessSignalGeneratingFunction]` (composition, XML child nesting) with an `add_process_signal_generating_function` helper; the existing `_adopt_function` single-ownership guard extends to PSGF.

### `SensingLocation` role base

New abstract role base `SensingLocation(DexpiBaseModel)` (`_abstract = True`) in `piping.py`, inherited by `Nozzle`, `PipingComponent`, and `PipingNetworkSegment`. Matches DEXPI's abstract `SensingLocation` 1:1 and the project's existing role-base pattern (`PipingSourceItem`, `SignalConveyingFunctionSource`). `piping.py` is the home because both `equipment.py` and `instrumentation.py` already import from it.

### `FlowMeasuringElement`

Add `FlowMeasuringElement(PipingComponent)` (`ComponentClass="FlowMeasuringElement"`, URI `http://sandbox.dexpi.org/rdl/FlowMeasuringElement`). It appears in the corpus as a `SensingLocation` (I04, I11, I14) and is a `PipingComponent`, so it inherits the role automatically. The wider `InlinePrimaryElement` family (10 subtypes) is **not** modelled.

### Associations

| Owner | Direction | `Type` | Opposite |
| --- | --- | --- | --- |
| PSGF | → sensing location | `is located in` | `is the location of` |
| sensing location (`Nozzle` / `PipingComponent` / `PipingNetworkSegment`) | → PSGF | `is the location of` | `is located in` |
| `SignalConveyingFunction` | → PSGF | `has logical start` | `is logical start of` |
| PSGF | → `SignalConveyingFunction` | `is logical start of` | `has logical start` |

The measuring line is the existing `SignalConveyingFunction` (the `SignalLineFunction` / `MeasuringLineFunction` split stays collapsed); its `source` may now be a PSGF.

### Serializer

- `_class_key` branch → `"ProcessSignalGeneratingFunction"`; `CLASS_ORDER["ProcessSignalGeneratingFunction"] = ["ProcessSignalGeneratingFunctionNumberAssignmentClass", "SensorTypeAssignmentClass"]`; a `_field_attributes` branch for the two strings (both URIs come free from the `sandbox/<Name>` fallback).
- `_emit_psgf(w, psgf)`: open `<ProcessSignalGeneratingFunction ID ComponentClass ComponentClassURI>`, `_emit_generic_attributes`, then `Association Type="is located in"` for the sensing location, then `Association Type="is logical start of"` for each signal sourced at this PSGF, close.
- **Back-references are resolved by write-time scan of `_MODEL`** (consistent with the InstrumentationLoopFunction decision): a helper returns the PSGF ids whose `sensing_location` is a given object, and the sensing-location emitters (`_emit_piping_component`, `_emit_nozzle`, `_emit_segment`) append `Association Type="is the location of"`. No `PrivateAttr` back-reference, no construction-time check.
- `_emit_pif` child order matches I01: generic attributes → PIF-level associations → PSGF children → `InformationFlow` children → `ActuatingFunction` children.
- **`_emit_pif` association direction is fixed.** It currently emits `is logical start of` unconditionally for every composed signal (`serialization.py:550-551`), which is wrong for the sensing shape where the PIF is the *target*. Emission becomes direction-aware, derived from `signal.source is pif` / `signal.target is pif` → `is logical start of` / `is logical end of`.
- `to_proteus_xml` gains no top-level loop (the PSGF nests under its PIF).

### Round-trip invariant

Every `is located in` on a PSGF is mirrored by an `is the location of` on the target piping element, and every PSGF is nested in exactly one PIF (opposite multiplicity 0..1). `I01` is the canonical minimal case.

### Do not model

`ProcessSignalGeneratingSystem`, `PrimaryElement`, `InlinePrimaryElementReference`, `OfflinePrimaryElement`, `Transmitter`, `FlowDetector`, the wider `InlinePrimaryElement` family, the `Systems` / `is fulfilled by` link, and the `MeasuringLineFunction` / `SignalLineFunction` split.

### Scope

The sensing layer comes out of the out-of-scope list during implementation (`spec.md:82`).

## Comments

- **Amended 2026-10-21 (implementation):** the `_emit_pif` child order above ("matches I01") was revised to match the C01 golden: generic attributes → signal associations (`is logical start of` / `is logical end of`) → `is a part of` → `InformationFlow` → `ActuatingFunction` → PSGF. I01 and C01 disagree on this order, and the XSD allows any (`xsd:choice maxOccurs="unbounded"`); C01 is the project's acceptance fixture.

- **Ticket-question correction:** DEXPI has **no** `MeasuringElement` class. It is an ISO 15926 term used in spec prose only; DEXPI models that concept as the `InlinePrimaryElement` family (spec:35863, 36358-36407).
- The device layer is real in the spec (spec:47020-47276, 45770-45820, 48130-48181) but is used by **zero** of the 22 PSGF instances in `data/example_pids/`.
- There is no direct association from a `ProcessInstrumentationFunction` to a piping element; the physical anchoring always travels through the nested PSGF (spec:46887-46898, research/06 §2.3).
- Citations: spec:46777-46833 (PSGF), 46887-46898 (`is located in` / `is the location of`), 46468-46481 + 46472-46475 (PIF composition, 0..1 opposite), 47543-47606 (logical start/end pair), 47278-47297 (`SensingLocation` subtypes).
