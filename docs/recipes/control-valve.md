# Control valve

**Goal:** model a controlled valve: the valve in the line, its actuating assembly, and the control function that drives it.

**Script:** [examples/recipes/control_valve.py](../../examples/recipes/control_valve.py) (a globe valve with actuator, positioner and a temperature controller).

## Steps

DEXPI splits a control valve into four related objects; there is no single "control valve" class.

1. **The valve.** Model the valve body as an `OperatedValve` subclass (for example `GlobeValve`) and place it in a segment's `items` like any other valve, with its nodes (see [piping network](piping-network.md)).
2. **The assembly.** An `ActuatingSystem` (optional `actuating_system_number`, `typical_information`) composes up to three components:
   - a `ControlledActuator` (`add_controlled_actuator`), with optional `device_type_name`, `fail_action` (a `FailActionClassification`: `FAIL_CLOSE`, `FAIL_OPEN`, `FAIL_RETAIN_POSITION`), `fail_action_representation` (the drawn text, for example "F.C.") and `sub_tag_name`;
   - an `OperatedValveReference` (`add_operated_valve_reference`) whose `valve` references the valve from step 1, plus an optional `sub_tag_name`;
   - an optional `Positioner` (`add_positioner`) with `device_type_name` and `sub_tag_name`.
   The constructor keywords `controlled_actuator`, `operated_valve_reference` and `positioner` do the same.
3. **The control function.** An `ActuatingFunction` (optional `actuating_function_number`) sets `systems` to the `ActuatingSystem`, and optionally `actuating_location` to the `PipingNetworkSegment` it acts on; both are references. Compose the function under the controlling `ProcessInstrumentationFunction` with `add_actuating_function`; it is not top-level.
4. **The signal.** A `SignalConveyingFunction` with `source` the PIF and `target` the `ActuatingFunction`, composed under the PIF with `add_signal_conveying_function`. A signal attaches to the `ActuatingFunction`, never to the `ActuatingSystem` or the actuator.
5. **Add to the model.** The line holding the valve (`add_piping_network_system`), the `ActuatingSystem` (`add_actuating_system`) and the PIF (`add_process_instrumentation_function`) are top-level.
6. **Serialize and validate** as in [serialize-and-validate](serialize-and-validate.md).

## What it becomes in Proteus XML

The `ActuatingSystem` element nests one `ActuatingSystemComponent` per component, distinguished by `ComponentClass` (`ControlledActuator`, `OperatedValveReference`, `Positioner`). The valve reference carries a "refers to" association to the valve, mirrored on the valve as "is referenced by". The `ActuatingFunction` is nested in its PIF with "is fulfilled by" pointing at the system, mirrored on the system as "fulfills"; its location is "is located in" the segment, mirrored on the segment as "is the location of". `fail_action` is written as `FailActionSpecialization` with its RDL URI.

## Pitfalls

- [Point an OperatedValveReference at an OperatedValve](../pitfalls.md#point-an-operatedvalvereference-at-an-operatedvalve)
- [Compose signals, actuating functions and sensors under a PIF](../pitfalls.md#compose-signals-actuating-functions-and-sensors-under-a-pif)
- [Compose everything you reference](../pitfalls.md#compose-everything-you-reference)
- [Give every composed child exactly one owner](../pitfalls.md#give-every-composed-child-exactly-one-owner)
