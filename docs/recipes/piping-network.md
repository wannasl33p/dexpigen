# Piping network

**Goal:** model a process line: a system of segments holding in-line items (valves, fittings, off-page connectors) and the pipes that connect items and nozzles.

**Script:** [examples/recipes/piping_network.py](../../examples/recipes/piping_network.py) (off-page connector to pump; pump through globe valve, reducer and tee to a tank; tee branch through a butterfly valve to an outgoing off-page connector).

## Steps

1. **Create the line.** A `PipingNetworkSystem` is the line; `line_number`, `fluid_code` and `piping_class_code` are optional and `line_number` need not be unique. Compose its stretches with `add_segment` (or `segments=[...]`).
2. **Create the segments.** A `PipingNetworkSegment` has optional `segment_number`, `fluid_code` and `piping_class_code`. It composes in-line items in `items` (`add_item`) and pipes in `connections` (`add_connection`).
3. **Create the in-line items with their nodes.** Use the concrete class: valves such as `GlobeValve`, `BallValve`, `ButterflyValve`, `GateValve`, `NeedleValve` (all `OperatedValve`), `CheckValve`, `SafetyValveOrFitting`, and fittings `PipeReducer`, `PipeTee`, `Flange`, `LineBlind`. An unspecified valve falls back to its family root, an unspecified fitting to `PipeFitting`. Compose one `PipingNode` per port with `add_node`, in port order. Name the flow ports with `flow_in_index` / `flow_out_index`: 1-based positions in `nodes` (a valve with nodes inlet, outlet uses 1 and 2; a tee usually declares only its inlet). `piping_component_number` and `piping_component_name` carry the component tag.
4. **Off-page connectors.** A line entering the drawing starts at a `FlowInPipeOffPageConnector` (a pipe source, usually `flow_out_index=1`); a line leaving it ends at a `FlowOutPipeOffPageConnector` (a pipe target, `flow_in_index=1`). Both are segment items with one node. To say where the line continues, compose a `PipeOffPageConnectorReferenceByNumber` with `add_connector_reference`, setting `referenced_connector_number` and `referenced_drawing_number`; when the other connector is in the same model, compose a `PipeOffPageConnectorObjectReference` with `referenced_connector` pointing at it instead.
5. **Connect with pipes.** A `Pipe` sets `source_item` / `source_node` and `target_item` / `target_node`. The items are references: nozzles of equipment, or items of any segment of the model. Each node must be one of its own item's `nodes`, so pass `item.nodes[i]`. Either end may be left empty for a pipe that runs off the modelled area. Compose the pipe in the segment it belongs to with `add_connection`.
6. **Add to the model.** `ConceptualModel.add_piping_network_system` adds the line; the equipment owning the nozzles must be added with `add_equipment` too, or the pipes point at nothing.
7. **Serialize and validate** as in [serialize-and-validate](serialize-and-validate.md).

## What it becomes in Proteus XML

The line is a `PipingNetworkSystem` element with nested `PipingNetworkSegment` elements. Valves and fittings are `PipingComponent` elements, connectors are `PipeOffPageConnector` elements; both carry `ConnectionPoints`, whose first `Node` is an implicit default node `<dex_id>-DefaultNode` followed by your nodes. Each pipe is a `Connection` with `FromID`/`FromNode`/`ToID`/`ToNode`; the node numbers are 1-based positions in the item's `nodes`. A `Pipe` has no `ID` on the wire. An object reference is a "refers to" association to the connector, mirrored on it as "is referenced by".

## Pitfalls

- [Take a connection node from its own item](../pitfalls.md#take-a-connection-node-from-its-own-item)
- [Count flow indices from 1](../pitfalls.md#count-flow-indices-from-1)
- [Compose everything you reference](../pitfalls.md#compose-everything-you-reference)
- [Give every composed child exactly one owner](../pitfalls.md#give-every-composed-child-exactly-one-owner)
- [Map extraction types by name, with the documented fallbacks](../pitfalls.md#map-extraction-types-by-name-with-the-documented-fallbacks)
