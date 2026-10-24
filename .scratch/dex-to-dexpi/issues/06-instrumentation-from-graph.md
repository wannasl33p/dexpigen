# Decide how instrumentation is built from the Dex graph

Type: grilling
Status: open
Blocked by: 02-dex-c01-correspondence

## Question

How do `instrument`, `actuator` and `control-valve` Entities and their edges become DEXPI instrumentation? Decide:

- instrument -> `ProcessInstrumentationFunction`;
- instrument -> actuator edges -> `SignalConveyingFunction`, and which PIF composes it;
- actuator + control-valve -> `ActuatingSystem` (`ControlledActuator`, `OperatedValveReference`) plus `ActuatingFunction`, and which PIF owns the function;
- nozzle/flange -> instrument edges -> `ProcessSignalGeneratingFunction` with a sensing location;
- what is not derivable without text (loops, PIF codes) and how its absence shows in the output and the report.
