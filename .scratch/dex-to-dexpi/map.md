# Dex extraction to DEXPI

Label: `wayfinder:map`

## Destination

A spec, ready to implement, for converting a **Dex extraction** into a `ConceptualModel` and then into Proteus XML. The output carries topology and, unless research finds a blocker, drawing graphics. The spec includes a structural acceptance test on C01: running `examples/C01/dex_model/` through the converter must match the original C01 P&ID on inventory, nesting and connections. Attributes are reported, not required.

## Notes

- Glossary: **Dex extraction**, **Dex graph**, **Entity** (`CONTEXT.md`). The input sample is `examples/C01/dex_model/` (an Opus-made extraction of high quality). The user's own pipeline is weaker today; the converter and its quality report must also serve it.
- Skills: `grilling` + `domain-modeling` for HITL tickets; `research` for AFK research tickets.
- The map produces decisions; a separate implementation agent builds from the resulting spec (same pattern as `.scratch/agent-docs/handoff.md`).
- **Settled while charting (2026-10-24):**
  - **No text.** Recognised texts (`text_entities.json`) are not used at all: no tags, no attributes from text, no subtypes from text.
  - **Coarse classes for now.** An Entity's DEXPI class comes only from its coarse label; a coarse label maps to its family root (`CustomEquipment`, `OperatedValve`, ...). Amended 2026-10-28 (ticket 04): an unknown label is skipped and reported, not mapped. A finer label vocabulary is later work.
  - **Piping hierarchy:** one `PipingNetworkSystem` per connected piping network; a segment is a chain between ends (nozzle, off-page connector, dead end) and tees; a branch at a tee starts a new segment.
  - **Acceptance shape:** compare structure, not XML text. Level 1 inventory per family, level 2 nesting, level 3 connections (piping graph regardless of system/segment grouping, signals, sensing locations, valve references) are exact for the Opus C01 extraction; level 4 attributes are reported only. Output must stay XSD-valid. The same levels give precision/recall for weaker pipelines.
  - **Reference structure** comes from the original C01 (`data/example_pids/C01 DEXPI Reference P&ID/C01V04-VER.EX01.xml`, which has graphics). Entities are matched to C01 objects by position. Checked: the dex equipment centres equal the C01 `Position` values in mm.
  - **Input models:** `src/dexpigen/entities/` becomes the input model layer. The details (own models, no `dexlib2`) are in [Decide the Dex extraction input contract](issues/03-dex-input-contract.md).
  - **Graphics** (`Position`, `Extent`, `CenterLine`, ...) are in scope if no blocker is found.

## Decisions so far

<!-- one line per closed ticket -->

- [Research how the C01 Dex extraction corresponds to C01](issues/02-dex-c01-correspondence.md): every Entity matches one C01 object by position (<= 4 mm); junction = PipeTee, deadend = open segment end, flange = BlindFlange; inventory, nozzle nesting, piping/signal/sensing/valve-reference links are derivable exactly, while chambers, exact classes and C01's system/segment grouping are not (branch `research-dex-c01-correspondence`).
- [Research the minimum Proteus graphics](issues/01-proteus-graphics-minimum.md): no blocker. All graphics are optional and XSD-valid: a `Position` per item and a `CenterLine` per pipe/signal, before nested children. Dex pixels -> mm with y flipped match C01 within 4 mm. Items need a shape to be visible in a renderer (branch `research-proteus-graphics-minimum`).
- [Decide the Dex extraction input contract](issues/03-dex-input-contract.md): input is `nx.Graph` + `Sequence[Entity]` + `DrawingSize`, all in PNG pixels. The library has its own `dexpigen.entities` models, field-compatible with the pipeline's `dexlib2` entities (no `dexlib2` dependency). Ids link Entities to graph nodes and edges. `LineKind` is `piping` / `signal-line` / `data-line`. Edges without a segment are attachments (equipment-nozzle, actuator-valve). Direction (`forward`/`reverse`/`bidirectional`) is relative to the segment LineString.
- [Decide the label-to-class mapping](issues/04-label-to-class-mapping.md): each coarse label maps to one class (valves to `OperatedValve`, actuators to a top-level `ActuatingSystem`), and unknown labels and insulation are skipped with one report line each.
- [Decide how piping topology is built from the Dex graph](issues/05-piping-topology-from-graph.md): one `Pipe` per piping line in flow order, with a missing direction taken from the geometry point order and reported, and segments cut at nozzles, off-page connectors, dead ends, tees and items with other than two piping lines.
- [Decide how instrumentation is built from the Dex graph](issues/06-instrumentation-from-graph.md): instruments become top-level PIFs, `signal-line` and `data-line` both become `SignalConveyingFunction`s with no marker, sensing lines become `ProcessSignalGeneratingFunction`s, and loops and PIF numbers are not read.
- [Decide how the model carries graphics](issues/07-graphics-in-the-model.md): graphics are optional fields on the model objects, written the way C01 carries positions and center lines, with an inline `PolyLine` outline for visibility and no rotation.
- [Decide the structural comparison and quality report](issues/08-structural-comparison.md): the C01 acceptance is per-family counts plus XSD validity rather than a comparison with the original XML, and the quality report for weaker pipelines stays open.
- [Decide the public conversion API](issues/09-public-api.md): `dex_to_model` returns a `DexConversion` (model and report) and `dex_to_proteus` returns the XML string, with contract errors raised as `DexExtractionError`, mapping gaps in the report, and no strict mode.

## Not yet specified

- **Attributes from entities:** mapping the Entity `attributes` dict (when a pipeline fills it) to first-class fields or `CustomAttribute`. Secondary; sharpens once the input contract is fixed.
- **Fine label vocabulary:** labels such as `centrifugal-pump` or `ball-valve` that map to exact DEXPI classes, and who owns that vocabulary.
- **Quality report thresholds:** which precision/recall levels count as good enough for the user's pipeline, and how the report is presented.
- **User docs for the dex path:** README entry and recipes for Dex extraction -> XML, under the existing docs rules (`tests/test_docs.py`). The input layer (`dexpigen.entities`, `check_extraction`) already has a README scope bullet and link.

## Out of scope

- Using recognised text in any form (OCR, tags, line numbers, data tables, attributes from text). Ruled out by the user while charting.
- A Proteus XML reader (XML -> `ConceptualModel`).
- Detection and computer vision: producing a Dex extraction from an image.
