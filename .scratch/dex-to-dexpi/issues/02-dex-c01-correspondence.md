# Research how the C01 Dex extraction corresponds to C01

Type: research
Status: open
Blocked by: -

## Question

How does every Entity and edge in `examples/C01/dex_model/graph.json` correspond to the original C01 (`data/example_pids/C01 DEXPI Reference P&ID/C01V04-VER.EX01.xml`) when matched by position (pixels -> mm via `size.json`, y flipped)? Report:

- for each Entity label (`equipment`, `nozzle`, `valve`, `control-valve`, `actuator`, `instrument`, `flange`, `reducer`, `off-page-connector`, `insulation`, `junction`, `deadend`): which C01 objects and classes it matches, the position error, and any unmatched Entities;
- which C01 objects (by class) have no Entity: chambers, signals, PSGFs, loops, and others;
- what the edges stand for: piping connections, nozzle membership, signal lines, actuator-valve links, sensing links. Does the edge direction (`source` -> `target`) follow the C01 flow direction (`FromID` -> `ToID`)?
- what `junction` and `deadend` nodes are in C01 terms (`PipeTee`? a pipe end?), and what the nodes with `None` labels are.

Record a correspondence table (Entity id -> C01 ID) as an asset; the structural-comparison and mapping tickets build on it.
