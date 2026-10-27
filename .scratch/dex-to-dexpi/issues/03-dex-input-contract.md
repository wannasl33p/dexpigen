# Decide the Dex extraction input contract

Type: grilling
Status: resolved
Assignee: alex.valentsinovich
Blocked by: -

## Question

What are the input models, and how is a Dex extraction loaded? Decide:

- which classes in `src/dexpigen/entities/` stay (`EquipmentEntity`, `SymbolEntity`, `SegmentEntity`, `GraphEntity`, mixins) and which are deleted (text-only ones: `BaseTagEntity`, `MetadataEntity`; the `to_kh_object` / `to_forge_object` exports; the broken `src.app` imports);
- which classes are missing for `graph.json`: nozzles, junctions, dead ends, edges;
- the loader: `graph.json` + `size.json` -> a typed `DexExtraction`, including the non-GeoJSON polygon rings it uses;
- coordinates: pixels or mm, y axis direction, where the conversion happens;
- package placement (`dexpigen.dex`?) and the `dexlib2` / `shapely` dependency footprint.

## Answer

Resolved by grilling with the user on 2026-10-27. The contract is the pipeline's in-memory objects, not a file format. Glossary updated in `CONTEXT.md` (**Dex graph**, **Line kind**, **Entity**).

- **Input:** the converter takes `nx.Graph` + `Sequence[Entity]` + `DrawingSize`.
  - Every coordinate is in image (PNG) pixels with y down. `DrawingSize` carries the `size.json` fields `image_width`, `image_height`, `drawing_width` and `drawing_height`, and is passed as a separate argument, not as `G.graph[...]`.
  - The converter maps px to mm with y up through that size, in one place, when it writes graphics. The input models keep pixels.
  - `text_entities.json`, `img.png` and `visualization.html` are not read.
- **Graph link:** an Entity's `id` is the id of its graph node. A `SegmentEntity`'s `id` is the id of its graph edge (`edge_...`).
  - Geometry comes from Entities only, and graph node polygons are ignored.
  - The one exception is `junction` and `deadend` nodes. They have no Entity, and their point comes from the node's `geometry`.
  - Node kinds come from `node_type` (`object` / `junction` / `deadend`, a closed set).
- **Classes:** the library defines its own pydantic models in `dexpigen.entities`, with no `dexlib2`.
  - `Entity`: `id: str` (frozen), `attributes: dict` (carried, not read yet), and an abstract coarse `label`.
  - `SymbolEntity`: `symbol_class: str` is its `label`, plus `quad` (4 points, px) and `confidence: float = 1.0`.
  - `EquipmentEntity`: `polygon` (px); its `label` is always `"equipment"`.
  - `SegmentEntity`: `geometry: LineString` (px), plus a `kind: LineKind` property read from `attributes["line_attributes"]["kind"]`.
  - `LineKind` is a `StrEnum`: `piping` (becomes piping), `signal-line` and `data-line` (both become signal connections of instrumentation functions).
  - Deleted: `GraphEntity`, `BaseTagEntity`, `MetadataEntity`, `to_kh_object`, `to_forge_object`, `_horseshoe`, `KIND2COLOR`, `anchor`, and the `src.app` imports.
- **Compatibility:** field names match the pipeline's `dexlib2` entities. The converter accepts both its own Entities and the pipeline's. A foreign object is normalised with `X.model_validate(obj.model_dump())`, and extra fields are ignored. `dexlib2` is never imported.
- **Edges:**
  - An edge with a `SegmentEntity` is a line of its `LineKind`.
  - An edge without a `SegmentEntity` is an **attachment** only when its ends are (`equipment`, `nozzle`) or (`actuator`, `valve`/`control-valve`). It is a short structural link, and no geometry is used from it.
  - Any other edge without a segment is an error.
  - The meaning of a line (piping vs sensing, signal vs data) is derived by the converter from its kind and its ends.
- **Direction:** an optional edge direction is `forward` / `reverse` / `bidirectional`. `dualflow: true` is the same as `bidirectional`, and both forms are accepted. Direction is relative to the coordinate order of the `SegmentEntity.geometry`, because the `(u, v)` order of an `nx.Graph` is unreliable. A missing direction means "unknown", not an error. It is a hint, and its use is decided in the piping and instrumentation tickets.
- **Validation:** one `DexExtractionError` lists every problem found.
  - It is raised for: duplicate ids, an `object` node without an Entity, a `SegmentEntity` without an edge, an edge without a segment that is not an attachment, broken geometry, an unknown `node_type` or `LineKind`, and an `object` with no label.
  - These pass: an unknown `label` (left to the label mapping), extra fields, and an Entity missing from the graph (it becomes an isolated node, e.g. `insulation`).
  - Parallel edges are not supported (no `MultiGraph`).
- **Dependencies:** `shapely` and `networkx` are hard dependencies. `dexlib2`, its private index and the deploy token in `pyproject.toml` are removed. The `CLAUDE.md` rule "no NetworkX" is amended to "the model holds no NetworkX; NetworkX appears only in the `dexpigen.entities` input layer".
- **C01 sample:** an adapter `examples/C01/dex_model/load.py` (not public API) turns `graph.json` into a graph and Entities.
  - It builds `SymbolEntity.quad` from the 5-point ring and `EquipmentEntity.polygon` from the full ring.
  - It maps id suffixes: `_line` -> `piping`, `_dashed` -> `signal-line`, `_actuator` and `a:b` -> attachments without a segment.
  - It sets direction `forward`, because the edge geometry follows source -> target.
