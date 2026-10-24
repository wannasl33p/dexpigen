# Research the minimum Proteus graphics

Type: research
Status: open
Blocked by: -

## Question

What is the minimum graphics a Proteus 4.1.1 file needs so that plant items and lines are positioned on the drawing? Using the bundled XSD (`data/schemas/ProteusPIDSchema 4.1.1.xsd`), the original C01 (`data/example_pids/C01 DEXPI Reference P&ID/C01V04-VER.EX01.xml`) and the DEXPI 1.3 spec (`data/DEXPI-PID-Specification-1.3.pdf.md`), find:

- which graphics elements (`Drawing`, `Position`, `Extent`, `CenterLine`, `Presentation`, `ShapeCatalogue`, `ComponentName`) are required or optional, and where they go in each element we write;
- how C01 positions equipment, nozzles, piping components, connections and instrumentation;
- whether a symbol shape (`ShapeCatalogue`) is required for a viewer to draw an item, or whether position/extent alone is valid and useful;
- the coordinate system (units, origin, axis direction) compared with the Dex extraction (`examples/C01/dex_model/size.json`: pixels -> mm, image y axis down).

Answer: is there a blocker for writing graphics from a Dex extraction, and what is the minimal element set?
