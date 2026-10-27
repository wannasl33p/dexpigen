# Decide the label-to-class mapping

Type: grilling
Status: open
Blocked by: 02-dex-c01-correspondence

## Question

Which DEXPI class (or classes) does each coarse Entity label produce, under the settled "coarse classes for now" rule? Cover `equipment`, `nozzle`, `valve`, `control-valve` (valve plus actuating system?), `actuator`, `instrument`, `flange`, `reducer`, `off-page-connector` (flow in or flow out?), `insulation`, `junction`, `deadend`, and unknown labels. Where does the mapping table live, and what happens to an Entity that maps to nothing (diagnostic, `CustomAttribute`, dropped)?

Input from [Research how the C01 Dex extraction corresponds to C01](02-dex-c01-correspondence.md): in C01, `valve` covers BallValve, ButterflyValve, SwingCheckValve and SpringLoadedGlobeSafetyValve, so a coarse `OperatedValve` is wrong for the check and safety valves. `flange` is a BlindFlange (not modelled yet). `insulation` is a drawing-only InsulationSymbol with no edges. `junction` is a PipeTee and `deadend` is an open segment end. Tell kinds apart by `node_type`, not `id`.

Input from [Decide the Dex extraction input contract](03-dex-input-contract.md): the coarse label is `SymbolEntity.symbol_class`, and `EquipmentEntity` always gives `equipment`. `junction` and `deadend` are graph-only nodes (`node_type`) without an Entity. An unknown label passes the loader and is handled here.
