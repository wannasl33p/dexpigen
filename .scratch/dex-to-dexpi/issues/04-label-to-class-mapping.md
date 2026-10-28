# Decide the label-to-class mapping

Type: grilling
Status: resolved
Assignee: alex.valentsinovich
Blocked by: 02-dex-c01-correspondence

## Question

Which DEXPI class (or classes) does each coarse Entity label produce, under the settled "coarse classes for now" rule? Cover `equipment`, `nozzle`, `valve`, `control-valve` (valve plus actuating system?), `actuator`, `instrument`, `flange`, `reducer`, `off-page-connector` (flow in or flow out?), `insulation`, `junction`, `deadend`, and unknown labels. Where does the mapping table live, and what happens to an Entity that maps to nothing (diagnostic, `CustomAttribute`, dropped)?

Input from [Research how the C01 Dex extraction corresponds to C01](02-dex-c01-correspondence.md): in C01, `valve` covers BallValve, ButterflyValve, SwingCheckValve and SpringLoadedGlobeSafetyValve, so a coarse `OperatedValve` is wrong for the check and safety valves. `flange` is a BlindFlange (not modelled yet). `insulation` is a drawing-only InsulationSymbol with no edges. `junction` is a PipeTee and `deadend` is an open segment end. Tell kinds apart by `node_type`, not `id`.

Input from [Decide the Dex extraction input contract](03-dex-input-contract.md): the coarse label is `SymbolEntity.symbol_class`, and `EquipmentEntity` always gives `equipment`. `junction` and `deadend` are graph-only nodes (`node_type`) without an Entity. An unknown label passes the loader and is handled here.

## Answer

Resolved by a fast-path grilling with the user on 2026-10-28 (one round of multiple-choice questions; defaults taken by the orchestrator are marked).

- **Coarse table (taken by default):** one class per coarse label, as in section C of the converter spec. `equipment` becomes `CustomEquipment` (`source_type_label="equipment"`), `valve` and `control-valve` become `OperatedValve`, `flange` becomes `Flange`, `reducer` becomes `PipeReducer`, `instrument` becomes `ProcessInstrumentationFunction`, and `nozzle` becomes a `Nozzle` under the equipment at the other end of its attachment edge (no equipment: skipped, with a report line).
- **Valves and flanges (taken by default):** every valve is an `OperatedValve` and every flange a `Flange`, so C01's check and safety valves and its blind flanges are not told apart. Exact classes wait for the fine label vocabulary.
- **Off-page connectors (taken by default):** `FlowInPipeOffPageConnector` when its piping line flows out of it, `FlowOutPipeOffPageConnector` when the line flows in. The direction comes from ticket 05.
- **Actuator (taken by default):** an `actuator` becomes a top-level `ActuatingSystem` that composes a `ControlledActuator`, plus an `OperatedValveReference` to the valve when it is attached to a valve or control valve. A control valve is only an `OperatedValve`.
- **Junction and deadend (taken by default):** a junction becomes a `PipeTee`, and a deadend makes no object. Both are graph nodes, told apart by `node_type`, never by id.
- **Unknown labels and insulation (user's choice):** skipped, with one report line each naming the Entity id and label. The Entity is dropped, not kept as a `CustomAttribute`. Its lines get open ends (for a piping line, the side at the skipped Entity is `None`, as for a dead end). This replaces the 2026-10-24 note that an unknown label falls back to a family root.
- **Fine labels (follows from the user's choice):** a fine label such as `centrifugal-pump` counts as unknown and is skipped, because no family can be read from a label the table does not know. An `EquipmentEntity` always has the label `equipment`, so equipment outlines are never dropped. Fine labels wait for the fine label vocabulary (map: Not yet specified).
- **Lines at a skipped Entity (taken by default):** a piping line gets an open end there. A signal or sensing line is skipped with a report line, because it has no function or location to point at.
- **Actuator without a valve (taken by default):** its `ActuatingSystem` is still built with the `ControlledActuator`, but without an `OperatedValveReference`, and the report says so.
- **Table and connectors (taken by default):** the table is `_INLINE` / `_MAPPED` in `src/dexpigen/entities/convert.py`. An off-page connector with no piping line, or with more than one, is skipped with a report line, and so is a valve, flange or reducer on no piping line. A `SymbolEntity` labelled `equipment` becomes `CustomEquipment` like an outline.
