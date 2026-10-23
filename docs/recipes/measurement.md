# Measurement

**Goal:** model an instrument: the P&ID bubble, the sensor that measures at a location in the process, the signal from sensor to bubble, and the loop the bubble belongs to.

**Script:** [examples/recipes/measurement.py](../../examples/recipes/measurement.py) (a temperature measurement on a tank nozzle).

## Steps

1. **Create the bubble.** A `ProcessInstrumentationFunction` (PIF) is the instrument bubble. Its tag is first-class: `process_instrumentation_function_number`, `process_instrumentation_function_category` (for example "T"), `process_instrumentation_function_modifier` and `process_instrumentation_functions_code` (the letters after the category, for example "IC"). Everything else goes into `custom_attributes` (see [custom attributes](custom-attributes.md)). A control or safeguarding system bubble is a `ProcessControlFunction`, a PIF subclass, never equipment.
2. **Create the sensor.** A `ProcessSignalGeneratingFunction` (PSGF) is the sensing function, with optional `process_signal_generating_function_number` and `sensor_type`. Compose it under its PIF with `add_process_signal_generating_function`; it is not top-level.
3. **Locate the sensor.** Set the PSGF's `sensing_location` to the object it measures at: a `Nozzle`, a `PipingNetworkSegment` or a piping component such as a `FlowMeasuringElement`. It is a reference: the location stays composed where it is, and it must be composed somewhere in the model.
4. **Draw the signal.** A `SignalConveyingFunction` is the dashed signal line. Its `source` and `target` reference functions only, never equipment or nozzles: the source is a PSGF, a PIF or an `ActuatingFunction`; the target is a PIF or an `ActuatingFunction`. Compose it under a PIF with `add_signal_conveying_function`. Either end may stay empty. (The signal off-page connector classes exist, but the model has no place to compose them yet, so a signal to one cannot be written.)
5. **Collect the loop.** An `InstrumentationLoopFunction` with `instrumentation_loop_function_number` lists its PIFs in `process_instrumentation_functions`. That list references the PIFs; a PIF may belong to several loops.
6. **Add to the model.** Add the PIF with `add_process_instrumentation_function` and the loop with `add_instrumentation_loop_function`. The equipment or line that owns the sensing location is added as usual.
7. **Serialize and validate** as in [serialize-and-validate](serialize-and-validate.md).

## What it becomes in Proteus XML

The PIF is a `ProcessInstrumentationFunction` element. Its signals are nested `InformationFlow` elements (`ComponentClass="SignalConveyingFunction"`) with "has logical start" / "has logical end" associations; the PSGF is a nested `ProcessSignalGeneratingFunction` with an "is located in" association. The writer adds the reverse associations ("is the location of" on the location, "is logical start of" / "is logical end of" on the endpoints, "is a part of" on a PIF in a loop) itself. The loop is a top-level `InstrumentationLoopFunction` with one "is a collection including" association per PIF.

## Pitfalls

- [Compose signals, actuating functions and sensors under a PIF](../pitfalls.md#compose-signals-actuating-functions-and-sensors-under-a-pif)
- [Add the PIFs of a loop at the top level too](../pitfalls.md#add-the-pifs-of-a-loop-at-the-top-level-too)
- [Compose everything you reference](../pitfalls.md#compose-everything-you-reference)
- [Reference the same object, never a copy](../pitfalls.md#reference-the-same-object-never-a-copy)
