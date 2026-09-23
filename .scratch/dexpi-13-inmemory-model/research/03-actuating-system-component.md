# Control valve assembly in DEXPI P&ID Specification 1.3

## Question restated

Does DEXPI 1.3 have a metamodel class `ActuatingSystemComponent`? What is the canonical split of actuator + valve, and where do signals attach?

## Answer

There is **no DEXPI 1.3 conceptual class named `ActuatingSystemComponent`**. That name is the **Proteus XML element** used to serialize several different instrumentation classes. The canonical assembly is:

1. A piping `OperatedValve` (there is no class `Valve`).
2. An `ActuatingSystem` that *composes* `ControlledActuator`, `OperatedValveReference`, optional `Positioner`, and any `CustomActuatingSystemComponent`.
3. An `ActuatingFunction` that *references* that `ActuatingSystem` (`Systems`) and optionally a `PipingNetworkSegment` (`ActuatingLocation`).
4. A `SignalLineFunction` (via `SignalConveyingFunction`) whose `Source` / `Target` are `SignalConveyingFunctionSource` / `SignalConveyingFunctionTarget` objects — typically functions such as `ActuatingFunction` or `ProcessInstrumentationFunction`, **not** the XML tag `ActuatingSystemComponent`.

## Evidence

### `ActuatingSystemComponent` is a Proteus tag, not a package class

The Instrumentation package class index lists `ActuatingSystem`, `ControlledActuator`, `OperatedValveReference`, `Positioner`, and `CustomActuatingSystemComponent`. It does **not** list `ActuatingSystemComponent`. ([Instrumentation package index](https://dexpi.plants-and-bytes.de/reference/Instrumentation/index.html))

`CustomActuatingSystemComponent` is defined as “a custom component of an ActuatingSystem, i.e., a component other than a ControlledActuator, an OperatedValveReference, or a Positioner.” Its Proteus example uses tag `ActuatingSystemComponent` with `ComponentClass="CustomActuatingSystemComponent"`. ([CustomActuatingSystemComponent](https://dexpi.plants-and-bytes.de/reference/Instrumentation/CustomActuatingSystemComponent.html))

The same Proteus tag appears on the official pages for `ControlledActuator`, `OperatedValveReference`, and `Positioner` (as children of `ActuatingSystem`). ([ActuatingSystem](https://dexpi.plants-and-bytes.de/reference/Instrumentation/ActuatingSystem.html), [ControlledActuator](https://dexpi.plants-and-bytes.de/reference/Instrumentation/ControlledActuator.html), [OperatedValveReference](https://dexpi.plants-and-bytes.de/reference/Instrumentation/OperatedValveReference.html))

### Canonical composition: `ActuatingSystem`

`ActuatingSystem` is “an assembly of artefacts that is designed to fulfill an ActuatingFunction.” Data: `ActuatingSystemNumber` 0..1, `TypicalInformation` 0..1. Composition:

| Role | Multiplicity | Type |
| --- | --- | --- |
| ControlledActuator | 0..1 | ControlledActuator |
| OperatedValveReference | 0..1 | OperatedValveReference |
| Positioner | 0..1 | Positioner |
| CustomComponents | * | CustomActuatingSystemComponent |

RDL `ACTUATING SYSTEM`, `ComponentClass=ActuatingSystem`. ([ActuatingSystem](https://dexpi.plants-and-bytes.de/reference/Instrumentation/ActuatingSystem.html))

### Valve link: `OperatedValveReference` → `OperatedValve`

`OperatedValveReference` is “a reference to an OperatedValve.” It has `SubTagName` 0..1 and a reference `Valve` 0..1 of type `OperatedValve` (association “refers to”). ([OperatedValveReference](https://dexpi.plants-and-bytes.de/reference/Instrumentation/OperatedValveReference.html))

The referenced object is a **piping** `OperatedValve`, serialized in the example as `PipingComponent` with `ComponentClass="OperatedValve"`. There is no DEXPI class `Valve`. ([OperatedValve](https://dexpi.plants-and-bytes.de/reference/Piping/OperatedValve.html), [class mapping note](./01-dexpi-13-class-mapping.md))

### Actuator: `ControlledActuator`

`ControlledActuator` is the energy-to-motion transducer (fail action, device type, subtag). It is composed *under* `ActuatingSystem`, not a free-floating plant item equivalent to the valve. ([ControlledActuator](https://dexpi.plants-and-bytes.de/reference/Instrumentation/ControlledActuator.html))

### Function vs system: `ActuatingFunction`

`ActuatingFunction` is “a function for acting control structures relating to the process.” It **references** (does not compose) `Systems: ActuatingSystem` 0..1 (“is fulfilled by”) and `ActuatingLocation: PipingNetworkSegment` 0..1 (“is located in”). ([ActuatingFunction](https://dexpi.plants-and-bytes.de/reference/Instrumentation/ActuatingFunction.html))

So: **function** (control intent) vs **system** (physical assembly). A control valve on a P&ID is both.

### Signals do not target the Proteus tag

`SignalConveyingFunction` has `Source` 0..1 → `SignalConveyingFunctionSource` and `Target` 0..1 → `SignalConveyingFunctionTarget`. The spec examples use `ActuatingFunction` as a logical start and `ProcessInstrumentationFunction` as a logical end. ([SignalConveyingFunction](https://dexpi.plants-and-bytes.de/reference/Instrumentation/SignalConveyingFunction.html))

`SignalLineFunction` is the concrete signal-line class. ([SignalLineFunction](https://dexpi.plants-and-bytes.de/reference/Instrumentation/SignalLineFunction.html))

`ActuatingFunction` is given as an example subclass of `SignalConveyingFunctionSource`. ([SignalConveyingFunctionSource](https://dexpi.plants-and-bytes.de/reference/Instrumentation/SignalConveyingFunctionSource.html))

`ActuatingSystem` is not listed as a signal source/target on those pages; attaching a `SignalLine` directly to `ControlledActuator` or to an `ActuatingSystemComponent` XML element would be a serialization confusion, not the conceptual model.

## v0.1 recommendation

Model a control valve as **four related objects**, not one class named `ActuatingSystemComponent`:

- `Piping.OperatedValve` (or a concrete operated-valve subtype)
- `Instrumentation.ActuatingSystem`
- `Instrumentation.ControlledActuator` (0..1, composed)
- `Instrumentation.OperatedValveReference` (0..1, composed, pointing at the valve)
- `Instrumentation.ActuatingFunction` (optional in a minimal fixture, required if a `SignalLineFunction` must attach)

A factory `ControlValve(...)` may *build* this graph; it must not *be* the persisted DEXPI type.

## Relation to ticket 01

This note agrees with [01-dexpi-13-class-mapping](./01-dexpi-13-class-mapping.md) and adds the function/signal attachment layer that v0.1 instrumentation tickets still need to decide.
