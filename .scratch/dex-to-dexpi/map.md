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
  - **Coarse classes for now.** An Entity's DEXPI class comes only from its coarse label; an unknown or coarse label falls back to the family root (`CustomEquipment`, `OperatedValve`, ...). A finer label vocabulary is later work.
  - **Piping hierarchy:** one `PipingNetworkSystem` per connected piping network; a segment is a chain between ends (nozzle, off-page connector, dead end) and tees; a branch at a tee starts a new segment.
  - **Acceptance shape:** compare structure, not XML text. Level 1 inventory per family, level 2 nesting, level 3 connections (piping graph regardless of system/segment grouping, signals, sensing locations, valve references) are exact for the Opus C01 extraction; level 4 attributes are reported only. Output must stay XSD-valid. The same levels give precision/recall for weaker pipelines.
  - **Reference structure** comes from the original C01 (`data/example_pids/C01 DEXPI Reference P&ID/C01V04-VER.EX01.xml`, which has graphics). Entities are matched to C01 objects by position. Checked: the dex equipment centres equal the C01 `Position` values in mm.
  - **Input models:** `src/dexpigen/entities/` becomes the input model layer. Clean it up, delete what text-free conversion does not need, and keep `dexlib2` and `shapely` as dependencies.
  - **Graphics** (`Position`, `Extent`, `CenterLine`, ...) are in scope if no blocker is found.

## Decisions so far

<!-- one line per closed ticket -->

## Not yet specified

- **Attributes from entities:** mapping the Entity `attributes` dict (when a pipeline fills it) to first-class fields or `CustomAttribute`. Secondary; sharpens once the input contract is fixed.
- **Fine label vocabulary:** labels such as `centrifugal-pump` or `ball-valve` that map to exact DEXPI classes, and who owns that vocabulary.
- **Quality report thresholds:** which precision/recall levels count as good enough for the user's pipeline, and how the report is presented.
- **User docs for the dex path:** README entry and recipes for Dex extraction -> XML, under the existing docs rules (`tests/test_docs.py`).

## Out of scope

- Using recognised text in any form (OCR, tags, line numbers, data tables, attributes from text). Ruled out by the user while charting.
- A Proteus XML reader (XML -> `ConceptualModel`).
- Detection and computer vision: producing a Dex extraction from an image.
