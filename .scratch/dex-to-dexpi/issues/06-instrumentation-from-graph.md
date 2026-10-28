# Decide how instrumentation is built from the Dex graph

Type: grilling
Status: resolved
Assignee: alex.valentsinovich
Blocked by: 02-dex-c01-correspondence

## Question

How do `instrument`, `actuator` and `control-valve` Entities and their edges become DEXPI instrumentation? Decide:

- instrument -> `ProcessInstrumentationFunction`;
- instrument -> actuator edges -> `SignalConveyingFunction`, and which PIF composes it;
- actuator + control-valve -> `ActuatingSystem` (`ControlledActuator`, `OperatedValveReference`) plus `ActuatingFunction`, and which PIF owns the function;
- nozzle/flange -> instrument edges -> `ProcessSignalGeneratingFunction` with a sensing location;
- what is not derivable without text (loops, PIF codes) and how its absence shows in the output and the report.

Input from [Research how the C01 Dex extraction corresponds to C01](02-dex-c01-correspondence.md): there are 3 `_dashed` signal edges (instrument -> actuator) and 3 sensing edges (instrument <-> BlindFlange x2, Nozzle-17 -> PIF-4; in C01 these are MeasuringLineFunction + PSGF). The 3 actuator -> control-valve edges each match an OperatedValveReference. ActuatingSystem, ActuatingFunction, PSGF and loops have no Entity of their own and must be inferred from the edges.

Input from [Decide the Dex extraction input contract](03-dex-input-contract.md): signals come in two Line kinds. `signal-line` is an instrument signal. `data-line` is a data or software link, drawn with small circles. Both become signal connections of instrumentation functions. DEXPI's `SignalConveyingTypeClassification` has no data-link literal, so decide whether and how the two kinds are told apart in the output. Sensing lines arrive as `piping` segments with an `instrument` end. Actuator-valve links are attachment edges without a segment. Signal direction comes from the end kinds or from the optional segment direction.

## Answer

Resolved by a fast-path grilling with the user on 2026-10-28 (one round of multiple-choice questions; defaults taken by the orchestrator are marked).

- **Instruments (taken by default):** an `instrument` becomes a top-level `ProcessInstrumentationFunction` with no number, category or loop. Loops, PIF numbers and categories are not read (no text is used), so no loop is built; the spec's expected counts list none. The report gets one line: "N instrument(s) without number, category or loop: no text is read".
- **Signal kinds (user's choice):** `signal-line` and `data-line` are not told apart. Both become a `SignalConveyingFunction` with no marker, composed under the source PIF.
- **Instrument to actuator (taken by default):** the source is the instrument's PIF, set by the end kinds and not by the geometry. The target is the actuator's `ActuatingFunction`, created once and composed under the first PIF that signals the actuator; its `systems` is the actuator's `ActuatingSystem` (ticket 04).
- **Instrument to instrument (spec):** a `SignalConveyingFunction` from PIF to PIF in flow order (ticket 05). Any other signal end is skipped, with a report line.
- **Sensing lines (taken by default):** a piping line with one instrument end becomes a `ProcessSignalGeneratingFunction` composed under that PIF. Its `sensing_location` is the other end when that is a `Nozzle` or a `PipingComponent`; otherwise the line is skipped, with a report line. The line itself is not written.
- **Order (taken by default):** "first" is the Dex graph's edge order. A later instrument that signals the same actuator targets the existing `ActuatingFunction`.
- **Several valves (taken by default):** the first attached valve in edge order is referenced; an `ActuatingSystem` holds one `OperatedValveReference`.
- **Actuator without a signal (taken by default):** its `ActuatingSystem` has no `ActuatingFunction`, and the report says so. The writer then leaves out the system's `fulfills` association, whose empty `ItemID` would break the XSD.
