# Research the minimum Proteus graphics

Type: research
Status: resolved
Blocked by: -

## Question

What is the minimum graphics a Proteus 4.1.1 file needs so that plant items and lines are positioned on the drawing? Using the bundled XSD (`data/schemas/ProteusPIDSchema 4.1.1.xsd`), the original C01 (`data/example_pids/C01 DEXPI Reference P&ID/C01V04-VER.EX01.xml`) and the DEXPI 1.3 spec (`data/DEXPI-PID-Specification-1.3.pdf.md`), find:

- which graphics elements (`Drawing`, `Position`, `Extent`, `CenterLine`, `Presentation`, `ShapeCatalogue`, `ComponentName`) are required or optional, and where they go in each element we write;
- how C01 positions equipment, nozzles, piping components, connections and instrumentation;
- whether a symbol shape (`ShapeCatalogue`) is required for a viewer to draw an item, or whether position/extent alone is valid and useful;
- the coordinate system (units, origin, axis direction) compared with the Dex extraction (`examples/C01/dex_model/size.json`: pixels -> mm, image y axis down).

Answer: is there a blocker for writing graphics from a Dex extraction, and what is the minimal element set?

## Answer

Resolved by a research subagent on 2026-10-24. Findings: `.scratch/dex-to-dexpi/research/01-proteus-graphics-minimum.md` on branch `research-proteus-graphics-minimum` (`e230388`), with XSD-valid samples in `01-samples/`: `00-base-no-graphics.xml` (our writer today), `01-minimal-position.xml`, `02-drawable.xml`.

- **No blocker.** Every graphics element is optional in Proteus 4.1.1. A `Position` places a plant item and a `CenterLine` places a line; all samples validate.
- **Minimal set per kind:**
  - `Position` on `Equipment`, `Nozzle` (plus on its process `Node`), `PipingComponent` (plus on its nodes), `PipeOffPageConnector` (before its reference), `ProcessInstrumentationFunction`, and a ControlledActuator / Positioner `ActuatingSystemComponent`;
  - one `CenterLine` per `Pipe` inside its `PipingNetworkSegment` (a `Connection` cannot hold graphics), and one per `InformationFlow`, after its `Association`s;
  - nothing on chambers, systems, PSGF, `ActuatingSystem`, `ActuatingFunction` or loops;
  - an optional `Drawing` (`Name`, `Type="PID"`, `Presentation`, `Extent` 0,0-420,297).
- **Rules:**
  - `Position` = `Location`, `Axis (0,0,1)`, `Reference (x,y,0)`, in that order. `Reference` gives the rotation (the symbol's x axis, counter-clockwise).
  - Graphics come before an element's nested children. The only exception is the `InformationFlow` `CenterLine`, which comes last. Each rule was proved by breaking it under xmllint.
- **Coordinates:** mm, origin bottom-left, y up: `x_mm = x_px*420/5000`, `y_mm = 297 - y_px*297/3536`.
  - All 47 labelled Entities agree with C01: median error 2 mm, max 4 mm. The remaining offsets are constant per kind (symbol origin) and derivable from the attachment edges.
  - All 81 C01 `CenterLine` vertices lie within 0.02 mm of a Dex edge vertex; 35 lines on each side.
- **Caveats for graphics in the model (none blocks):**
  - Without a shape an item is invisible in a renderer. It needs `ComponentName` + a `ShapeCatalogue` entry, or an inline `PolyLine`/`Shape` (for example the Dex polygon). No third-party viewer was tested.
  - The spec ties each `Pipe` to one `CenterLine` in flow order. C01 writes one `Connection` per segment; ours (one per `Pipe`) is also valid.
  - The orientation (`Reference`) must be derived from geometry.
  - The "no graphics" rule in `CLAUDE.md` and the v0.1 spec must be amended first.
