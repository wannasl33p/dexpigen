# Instrumentation classes

Instrumentation functions, the control-valve assembly, signals, sensing and loops.

Generated from `dexpigen.instrumentation` by `scripts/gen_reference.py`; do not edit by hand.

## Contents

- [SignalConveyingFunctionSource](#signalconveyingfunctionsource)
  - [ProcessSignalGeneratingFunction](#processsignalgeneratingfunction)
  - [ProcessInstrumentationFunction](#processinstrumentationfunction)
    - [ProcessControlFunction](#processcontrolfunction)
  - [ActuatingFunction](#actuatingfunction)
- [SignalConveyingFunctionTarget](#signalconveyingfunctiontarget)
- [InstrumentationLoopFunction](#instrumentationloopfunction)
- [ControlledActuator](#controlledactuator)
- [OperatedValveReference](#operatedvalvereference)
- [Positioner](#positioner)
- [ActuatingSystem](#actuatingsystem)
- [SignalConveyingFunction](#signalconveyingfunction)
- [SignalOffPageConnector](#signaloffpageconnector)
  - [FlowInSignalOffPageConnector](#flowinsignaloffpageconnector)
  - [FlowOutSignalOffPageConnector](#flowoutsignaloffpageconnector)

## Classes

### SignalConveyingFunctionSource

Abstract role: a valid `SignalConveyingFunction` source.

- ComponentClass: -
- ComponentClassURI: -
- Bases: [DexpiBaseModel](model.md#dexpibasemodel)
- Abstract: yes

No own fields.

### ProcessSignalGeneratingFunction

The sensing function of a PIF: a signal source located on a piping object.

- ComponentClass: `ProcessSignalGeneratingFunction`
- ComponentClassURI: `http://sandbox.dexpi.org/rdl/ProcessSignalGeneratingFunction`
- Bases: [SignalConveyingFunctionSource](#signalconveyingfunctionsource)
- Abstract: no

| Field | Type | Default | Relation |
| --- | --- | --- | --- |
| `process_signal_generating_function_number` | str \| None | `None` |  |
| `sensor_type` | str \| None | `None` |  |
| `sensing_location` | [SensingLocation](piping.md#sensinglocation) \| None | `None` | ref |

### ProcessInstrumentationFunction

The P&ID instrument/function bubble.

- ComponentClass: `ProcessInstrumentationFunction`
- ComponentClassURI: `http://sandbox.dexpi.org/rdl/ProcessInstrumentationFunction`
- Bases: [SignalConveyingFunctionSource](#signalconveyingfunctionsource), [SignalConveyingFunctionTarget](#signalconveyingfunctiontarget)
- Abstract: no

| Field | Type | Default | Relation |
| --- | --- | --- | --- |
| `process_instrumentation_function_number` | str \| None | `None` |  |
| `process_instrumentation_function_category` | str \| None | `None` |  |
| `process_instrumentation_function_modifier` | str \| None | `None` |  |
| `process_instrumentation_functions_code` | str \| None | `None` |  |
| `actuating_functions` | list[[ActuatingFunction](#actuatingfunction)] | `[]` | composed |
| `signal_conveying_functions` | list[[SignalConveyingFunction](#signalconveyingfunction)] | `[]` | composed |
| `process_signal_generating_functions` | list[[ProcessSignalGeneratingFunction](#processsignalgeneratingfunction)] | `[]` | composed |
| `signal_connectors` | list[[SignalOffPageConnector](#signaloffpageconnector)] | `[]` | composed |

### ProcessControlFunction

A control/safeguarding system bubble (a function, not `Equipment`).

- ComponentClass: `ProcessControlFunction`
- ComponentClassURI: `http://sandbox.dexpi.org/rdl/ProcessControlFunction`
- Bases: [ProcessInstrumentationFunction](#processinstrumentationfunction)
- Abstract: no

No own fields.

### ActuatingFunction

The control-loop function that references its assembly and location.

- ComponentClass: `ActuatingFunction`
- ComponentClassURI: `http://sandbox.dexpi.org/rdl/ActuatingFunction`
- Bases: [SignalConveyingFunctionSource](#signalconveyingfunctionsource), [SignalConveyingFunctionTarget](#signalconveyingfunctiontarget)
- Abstract: no

| Field | Type | Default | Relation |
| --- | --- | --- | --- |
| `actuating_function_number` | str \| None | `None` |  |
| `systems` | [ActuatingSystem](#actuatingsystem) \| None | `None` | ref |
| `actuating_location` | [PipingNetworkSegment](piping.md#pipingnetworksegment) \| None | `None` | ref |

### SignalConveyingFunctionTarget

Abstract role: a valid `SignalConveyingFunction` target.

- ComponentClass: -
- ComponentClassURI: -
- Bases: [DexpiBaseModel](model.md#dexpibasemodel)
- Abstract: yes

No own fields.

### InstrumentationLoopFunction

A top-level loop function that collects one or more PIFs.

- ComponentClass: `InstrumentationLoopFunction`
- ComponentClassURI: `http://sandbox.dexpi.org/rdl/InstrumentationLoopFunction`
- Bases: [DexpiBaseModel](model.md#dexpibasemodel)
- Abstract: no

| Field | Type | Default | Relation |
| --- | --- | --- | --- |
| `instrumentation_loop_function_number` | str \| None | `None` |  |
| `process_instrumentation_functions` | list[[ProcessInstrumentationFunction](#processinstrumentationfunction)] | `[]` | ref |

### ControlledActuator

The energy-to-motion transducer of a control-valve assembly.

- ComponentClass: `ControlledActuator`
- ComponentClassURI: `http://sandbox.dexpi.org/rdl/ControlledActuator`
- Bases: [DexpiBaseModel](model.md#dexpibasemodel)
- Abstract: no

| Field | Type | Default | Relation |
| --- | --- | --- | --- |
| `device_type_name` | str \| None | `None` |  |
| `fail_action` | [FailActionClassification](enumerations.md#failactionclassification) \| None | `None` |  |
| `fail_action_representation` | str \| None | `None` |  |
| `sub_tag_name` | str \| None | `None` |  |

### OperatedValveReference

A reference to the `OperatedValve` a control-valve assembly controls.

- ComponentClass: `OperatedValveReference`
- ComponentClassURI: `http://sandbox.dexpi.org/rdl/OperatedValveReference`
- Bases: [DexpiBaseModel](model.md#dexpibasemodel)
- Abstract: no

| Field | Type | Default | Relation |
| --- | --- | --- | --- |
| `valve` | [OperatedValve](piping.md#operatedvalve) \| None | `None` | ref |
| `sub_tag_name` | str \| None | `None` |  |

### Positioner

The positioner of a control-valve assembly.

- ComponentClass: `Positioner`
- ComponentClassURI: `http://sandbox.dexpi.org/rdl/Positioner`
- Bases: [DexpiBaseModel](model.md#dexpibasemodel)
- Abstract: no

| Field | Type | Default | Relation |
| --- | --- | --- | --- |
| `device_type_name` | str \| None | `None` |  |
| `sub_tag_name` | str \| None | `None` |  |

### ActuatingSystem

A control-valve physical assembly (actuator, valve reference, positioner).

- ComponentClass: `ActuatingSystem`
- ComponentClassURI: `http://sandbox.dexpi.org/rdl/ActuatingSystem`
- Bases: [DexpiBaseModel](model.md#dexpibasemodel)
- Abstract: no

| Field | Type | Default | Relation |
| --- | --- | --- | --- |
| `actuating_system_number` | str \| None | `None` |  |
| `typical_information` | str \| None | `None` |  |
| `controlled_actuator` | [ControlledActuator](#controlledactuator) \| None | `None` | composed |
| `operated_valve_reference` | [OperatedValveReference](#operatedvalvereference) \| None | `None` | composed |
| `positioner` | [Positioner](#positioner) \| None | `None` | composed |

### SignalConveyingFunction

A dashed signal line connecting two functions (no graphics).

- ComponentClass: `SignalConveyingFunction`
- ComponentClassURI: `http://sandbox.dexpi.org/rdl/SignalConveyingFunction`
- Bases: [DexpiBaseModel](model.md#dexpibasemodel)
- Abstract: no

| Field | Type | Default | Relation |
| --- | --- | --- | --- |
| `source` | [SignalConveyingFunctionSource](#signalconveyingfunctionsource) \| None | `None` | ref |
| `target` | [SignalConveyingFunctionTarget](#signalconveyingfunctiontarget) \| None | `None` | ref |

### SignalOffPageConnector

Abstract base for a signal off-page connector.

- ComponentClass: -
- ComponentClassURI: -
- Bases: [DexpiBaseModel](model.md#dexpibasemodel)
- Abstract: yes

No own fields.

### FlowInSignalOffPageConnector

A signal off-page connector that is a valid signal source.

- ComponentClass: `FlowInSignalOffPageConnector`
- ComponentClassURI: `http://sandbox.dexpi.org/rdl/FlowInSignalOffPageConnector`
- Bases: [SignalOffPageConnector](#signaloffpageconnector), [SignalConveyingFunctionSource](#signalconveyingfunctionsource)
- Abstract: no

No own fields.

### FlowOutSignalOffPageConnector

A signal off-page connector that is a valid signal target.

- ComponentClass: `FlowOutSignalOffPageConnector`
- ComponentClassURI: `http://sandbox.dexpi.org/rdl/FlowOutSignalOffPageConnector`
- Bases: [SignalOffPageConnector](#signaloffpageconnector), [SignalConveyingFunctionTarget](#signalconveyingfunctiontarget)
- Abstract: no

No own fields.
