# Decide how piping topology is built from the Dex graph

Type: grilling
Status: open
Blocked by: 02-dex-c01-correspondence, 03-dex-input-contract

## Question

How do Dex graph edges become `PipingNode`s, `Pipe` connections and segment items? Decide:

- which node (port) of an item an edge attaches to, and how inlet/outlet (`flow_in_index` / `flow_out_index`) are chosen when flow direction is or is not known;
- how a tee's three ports are assigned;
- what dead ends, nozzle-to-nozzle edges and edges with unlabelled endpoints become;
- the segment cut (settled: chains between ends and tees) applied to real C01 cases;
- how the equipment-to-nozzle edges become nozzle composition.

Input from [Research how the C01 Dex extraction corresponds to C01](02-dex-c01-correspondence.md): all 31 piping edges follow the C01 flow direction, but only as a drawing artefact, so treat direction as a hint to verify. The settled cut gives 20 segments against C01's 23 (C01 also cuts at the check valve, reducer and safety valve), and 10 connected networks against 11 systems. Nozzle and actuator points come from their zero-length edges, not from the box centre. A tee has exactly 3 piping edges; a dead end has 1.

Input from [Decide the Dex extraction input contract](03-dex-input-contract.md): a piping line is an edge with a `SegmentEntity` of kind `piping`. Equipment-nozzle links are attachment edges without a segment. The optional direction `forward` / `reverse` / `bidirectional` (`dualflow: true`) is relative to the segment's LineString, and it may be missing. Junction and dead-end points come from the graph node. The input is an undirected `nx.Graph` with no parallel edges.
