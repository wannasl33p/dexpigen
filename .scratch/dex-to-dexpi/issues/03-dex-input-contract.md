# Decide the Dex extraction input contract

Type: grilling
Status: open
Blocked by: -

## Question

What are the input models, and how is a Dex extraction loaded? Decide:

- which classes in `src/dexpigen/entities/` stay (`EquipmentEntity`, `SymbolEntity`, `SegmentEntity`, `GraphEntity`, mixins) and which are deleted (text-only ones: `BaseTagEntity`, `MetadataEntity`; the `to_kh_object` / `to_forge_object` exports; the broken `src.app` imports);
- which classes are missing for `graph.json`: nozzles, junctions, dead ends, edges;
- the loader: `graph.json` + `size.json` -> a typed `DexExtraction`, including the non-GeoJSON polygon rings it uses;
- coordinates: pixels or mm, y axis direction, where the conversion happens;
- package placement (`dexpigen.dex`?) and the `dexlib2` / `shapely` dependency footprint.
