# Decide the structural comparison and quality report

Type: grilling
Status: resolved
Assignee: alex.valentsinovich
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

## Answer

Resolved by a fast-path grilling with the user on 2026-10-28 (one round of multiple-choice questions; defaults taken by the orchestrator are marked).

- **Acceptance on C01 (user's choice):** per-family counts plus XSD validity. This is not a comparison with the original C01 XML, which stays possible later. Matching against the original C01 XML by position stays possible later.
- **XSD check (user's choice):** `validate(xml_path: str) -> bool` in `examples/validate_dexpi.py`.
- **Expected numbers (taken by default):** the counts in section D of the spec. The system and segment counts (10 and 20) come from the Dex graph, so they differ from C01's 11 and 23 (research 02).
- **Input (spec):** the C01 Dex extraction enters through the adapter `examples/C01/dex_model/load.py` as `dex_to_model(*load())`.
- **Extra checks (taken by default):** `tests/test_c01_dex_acceptance.py` also checks the report's insulation line, that every position lies on the 420 x 297 mm sheet, the nozzle nesting, the piping pairs, the signal and sensing ends and the valve references. That covers most of levels 2 and 3 without reading the original C01 XML.
- **Counting (taken by default):** counts are read from the converted model, per class; the two off-page connector classes count separately.
- **Open (later):** matching by position against the original C01 XML: tolerance, unmatched objects, and whether it reads our XML graphics or the Dex extraction. Research 02's 5 mm nearest match per label (worst error 4 mm) is the candidate.
- **Where (taken by default):** `tests/test_c01_dex_acceptance.py`; `tests/test_c01_dex_sample.py` keeps testing the adapter alone.
- **Open:** the weaker-pipeline precision and recall report: its format and where it runs. The thresholds stay under "Quality report thresholds" in the map.
- **Open:** research 02 says the C01 edge directions are only a hint to verify. Counts do not check them, so direction stays unverified.
