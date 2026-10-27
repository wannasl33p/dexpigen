# Decide the structural comparison and quality report

Type: grilling
Status: open
Blocked by: 02-dex-c01-correspondence, 07-graphics-in-the-model

## Question

How is the settled acceptance shape (levels 1-4) computed? Decide:

- how structure is extracted from a Proteus XML (ours and the original C01) into a comparable form;
- the family mapping for level 1 (which classes count as one family under coarse classes);
- position matching between our output and C01: tolerance, unmatched objects, whether matching reads our XML graphics or the Dex extraction;
- the exact-match test for the Opus C01 extraction (where it lives, what it asserts);
- the precision/recall report for weaker pipelines: its format and where it runs.

Input from [Research how the C01 Dex extraction corresponds to C01](02-dex-c01-correspondence.md): one-to-one nearest matching per label within 5 mm works on C01 (the worst error is 4 mm). The known differences acceptance must exclude or record are chambers and nozzle-in-chamber, equipment internals, exact classes, and C01's system/segment grouping. C01 uses classes the model lacks (BlindFlange, SwingCheckValve, SpringLoadedGlobeSafetyValve, MeasuringLineFunction), so level 1 compares by family. The script `02-correspond.py` on branch `research-dex-c01-correspondence` is a starting point.

Input from [Research the minimum Proteus graphics](01-proteus-graphics-minimum.md): if our XML carries `Position`s in C01's coordinate system (mm, y up), matching can read both XMLs directly instead of the Dex extraction. Expect constant per-kind offsets of up to 4 mm (symbol origins).

Input from [Decide the Dex extraction input contract](03-dex-input-contract.md): the Opus C01 sample reaches the converter through the adapter `examples/C01/dex_model/load.py` (`graph.json` -> `nx.Graph` + Entities). That adapter is not public API.
