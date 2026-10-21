# Decide how to add PipeTee

Type: grilling
Status: resolved
Blocked by: research/07-pipetee-instrumentation-loop

## Question

How do we model `PipeTee` in v0.2? It is a three-port `PipingComponent` (one run, two branches). Decide its `ComponentClass`/URI, node count and flow direction (`FlowIn`/`FlowOut`), and whether the current `PipingComponent` base (source/target/node-owner with `flow_in_index`/`flow_out_index`) suffices, or a multi-port component needs new flow-direction handling.

## Answer

Add `PipeTee` as a concrete `PipeFitting` subtype with no fields of its own.

- **Identity**: `component_class = "PipeTee"`, `component_class_uri = "http://data.posccaesar.org/rdl/RDS427724"` (numeric RDS host, matching the existing fittings).
- **Fields**: none of its own — inherits `PipingComponent`'s six (`fluid_code`, `on_hold`, `piping_class_artefact`, `pressure_test_circuit_number`, `piping_component_name`, `piping_component_number`); `PipeFitting`'s heat-tracing/insulation fields stay unmodelled across all fittings.
- **Flow direction**: keep the existing `PipingNodeOwner` base (`flow_in_index` / `flow_out_index`, both optional). No new multi-port handling — DEXPI marks only the inlet via `FlowIn`; the two outlets are ordinary process nodes referenced as connection sources. The writer already reproduces C01/I13 verbatim (index math verified).
- **No node-count invariant**: `nodes` stays unconstrained (`Nodes` is `*` and unordered); no `model_validator` forcing 3 nodes, and `flow_out_index` stays optional.
- **`ComponentName` (general base change)**: model `component_name: str | None` on the shared base `DexpiBaseModel` (next to `component_class`/`component_class_uri`) and emit it as a conditional element attribute. Applies to all plant items, not just `PipeTee`. `ComponentType`/`Revision`/`Status` remain unmodelled.
- **Writer**: no `PipeTee`-specific change — `_class_key` already maps `PipingComponent` → `"PipingComponent"`, and `_emit_piping_component` + `_emit_connection_points` produce `NumPoints="4"`, `FlowIn`, and the process-node indices as-is.

## Comments

- research/07 §1(d) and §1(e) item 6 were wrong to call `ComponentName` "not in the XSD": it is defined at `ProteusPIDSchema 4.1.1.xsd:716` as an optional `xsd:string` attribute on the shared plant-item element base. It is a Proteus-level attribute, distinct from the DEXPI data field `PipingComponentName` (spec:34529, already modelled as `piping_component_name`).
- Reference examples use `ComponentName="T_TYPE_CONNECTION_SHAPE"` (a ShapeCatalogue/library name); extraction data uses `PipingComponent_<uuid>`.
