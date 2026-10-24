# Research how the C01 Dex extraction corresponds to C01

Type: research
Status: resolved
Blocked by: -

## Question

How does every Entity and edge in `examples/C01/dex_model/graph.json` correspond to the original C01 (`data/example_pids/C01 DEXPI Reference P&ID/C01V04-VER.EX01.xml`) when matched by position (pixels -> mm via `size.json`, y flipped)? Report:

- for each Entity label (`equipment`, `nozzle`, `valve`, `control-valve`, `actuator`, `instrument`, `flange`, `reducer`, `off-page-connector`, `insulation`, `junction`, `deadend`): which C01 objects and classes it matches, the position error, and any unmatched Entities;
- which C01 objects (by class) have no Entity: chambers, signals, PSGFs, loops, and others;
- what the edges stand for: piping connections, nozzle membership, signal lines, actuator-valve links, sensing links. Does the edge direction (`source` -> `target`) follow the C01 flow direction (`FromID` -> `ToID`)?
- what `junction` and `deadend` nodes are in C01 terms (`PipeTee`? a pipe end?), and what the nodes with `None` labels are.

Record a correspondence table (Entity id -> C01 ID) as an asset; the structural-comparison and mapping tickets build on it.

## Answer

Resolved by a research subagent on 2026-10-24. Findings: `.scratch/dex-to-dexpi/research/02-dex-c01-correspondence.md` on branch `research-dex-c01-correspondence` (HEAD `0f2c0eb`), with `02-correspondence.csv`, `02-edges.csv` and the script `02-correspond.py`.

- **Every Entity matches exactly one C01 object, and every C01 symbol object has an Entity.** Rule: one-to-one nearest match within the label's class set, 5 mm tolerance. Errors are 0 mm for equipment, valves, instruments, tees and flanges. Nozzles are a constant 2 mm off and actuators 4 mm off, because C01 places their `Position` at the equipment end or valve stem. Their zero-length membership edges sit on the C01 point, so place them by that edge point, not by the box centre.
- **Labels in C01 terms:**
  - `valve` (8) = 5 BallValve + ButterflyValve + SwingCheckValve + SpringLoadedGlobeSafetyValve;
  - `control-valve` (3) = the actuated GlobeValves; `actuator` = ControlledActuator;
  - `junction` = PipeTee; `deadend` = an open segment end (4 utility lines);
  - `flange` = BlindFlange; `insulation` = an InsulationSymbol drawing marker with no edges (point-on-line finds its segment).
  - Tell node kinds apart by `node_type`, never by `id`: tee ids read `deadend-N_line`.
- **Edges (59):** 31 piping, 19 equipment-nozzle membership, 3 actuator-valve, 3 signal (`_dashed`), 3 sensing (instrument to BlindFlange x2 / Nozzle-17; in C01 these are MeasuringLineFunction + PSGF).
  - Direction agrees with C01 flow for all 31 piping edges and all 6 signal and sensing edges.
  - Edge geometry repeats the C01 CenterLines vertex for vertex, so the agreement may be an artefact of drawing. Treat direction as a hint to verify.
- **Not in the graph:** Chamber (8, and nozzle-in-chamber), equipment internals (TubeBundle, Impeller, Displacer), PipeFlowArrow, PipeSlopeSymbol, and the DEXPI functions that have no symbol of their own (ActuatingSystem, ActuatingFunction, OperatedValveReference, PSGF, loops). The last group must be inferred from the edges.
- **Feasibility:**
  - Inventory, nozzle nesting (19/19) and the undirected piping graph (31/31 pairs), signals, sensing locations and valve references (3/3) are all derivable exactly.
  - C01's own grouping is not. The graph gives 10 connected networks against 11 systems (systems 5 and 6 meet at PipeTee-1). The settled segment cut gives 20 segments against 23, because C01 also cuts at the check valve, reducer and safety valve.
  - Exact classes are not derivable either: the coarse `OperatedValve` is wrong for the check and safety valves.
  - C01 uses classes the model lacks: BlindFlange, SwingCheckValve, SpringLoadedGlobeSafetyValve, MeasuringLineFunction.
