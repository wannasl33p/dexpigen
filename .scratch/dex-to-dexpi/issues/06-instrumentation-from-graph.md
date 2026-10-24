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

Input from [Research how the C01 Dex extraction corresponds to C01](02-dex-c01-correspondence.md): there are 3 `_dashed` signal edges (instrument -> actuator) and 3 sensing edges (instrument <-> BlindFlange x2, Nozzle-17 -> PIF-4; in C01 these are MeasuringLineFunction + PSGF). The 3 actuator -> control-valve edges each match an OperatedValveReference. ActuatingSystem, ActuatingFunction, PSGF and loops have no Entity of their own and must be inferred from the edges.
