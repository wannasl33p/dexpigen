# Decide how piping topology is built from the Dex graph

Type: grilling
Status: resolved
Assignee: alex.valentsinovich
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

## Answer

Resolved by a fast-path grilling with the user on 2026-10-28 (one round of multiple-choice questions; defaults taken by the orchestrator are marked).

- **Flow order (user's choice):** the source is the end nearer the first point of the segment geometry, and `reverse` swaps it. A line with no `direction` (or `dualflow`, which means bidirectional) uses the same point order. Its flow indices are still set, and one summary report line says the direction was assumed.
- **Ports (taken by default):** each piping item (valve, flange, reducer, off-page connector, tee) gets one `PipingNode` per piping line, incoming lines first, then outgoing. `flow_in_index` is 1 when there is an incoming line; `flow_out_index` is the incoming count plus 1 when there is an outgoing line. A tee's three ports follow the same rule.
- **Piping and sensing lines (spec):** a piping line is a `PIPING` line with no instrument end, and it gives one `Pipe` from source to target. A sensing line (ticket 06) is not a piping line, so it adds no `Pipe` and no port. Attachment edges (equipment to nozzle, actuator to valve) add no `Pipe`.
- **Dead ends and nozzles (spec):** a dead end leaves that side of its `Pipe` as `None`. A nozzle has one node shared by all its piping lines. A nozzle-to-nozzle line is one `Pipe` between the two nodes; the spec does not discuss it, but its one-`Pipe`-per-line rule covers it.
- **Unlabelled and unknown ends:** an endpoint with no label is a contract error raised before conversion (ticket 03), not a mapping gap. An endpoint with an unknown label gives its line an open end (ticket 04).
- **Nearer positions (spec):** junction and deadend use their node point, equipment its polygon bbox centre, and symbols their quad centre. Research 02's zero-length-edge points are not used (see ticket 07).
- **Segment cut and systems (taken by default):** cut at nozzles, off-page connectors, dead ends, tees and any item with other than two piping lines; one `PipingNetworkSegment` per chain between cuts; one `PipingNetworkSystem` per connected piping network. On C01 this gives 20 segments (C01 has 23, because it also cuts at its check valve, reducer and safety valve) and 10 systems (C01 has 11).
- **Chain ends (taken by default):** a terminal tee, off-page connector or end flange sits in the first segment whose line flows into it, else in the first segment that reaches it. Segments elsewhere reference it through their pipes.
- **Junctions (taken by default):** a `PipeTee` gets one node per piping line, whatever their number, and a junction with other than three lines gets a report line. All C01 tees have three.
- **Degenerate lines (taken by default):** a line from a node to itself is skipped with a report line; a pipe with no item at either end (for example between two dead ends) is kept and reported.
- **Skipped nozzle (taken by default):** a nozzle attached to no equipment is skipped with a report line, and its piping lines get an open end there, like any skipped Entity.
