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
