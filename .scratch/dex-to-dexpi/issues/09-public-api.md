# Decide the public conversion API

Type: grilling
Status: resolved
Assignee: alex.valentsinovich
Blocked by: 03-dex-input-contract

## Question

What does a developer call, and what do they get back? Decide:

- the entry points (`dex_to_model(extraction) -> ConceptualModel`, `dex_to_proteus(...) -> str`, a CLI?);
- the diagnostics for Entities and edges that could not be mapped (warnings, a report object, strict mode);
- how `dex_id` is formed from Entity ids: uuids may start with a digit, which is not an XML NCName, so a prefix is needed;
- how the result relates to `_check_model` and XSD validation.

Input from [Decide the Dex extraction input contract](03-dex-input-contract.md): there is no file loader in the public API. The converter takes `nx.Graph` + `Sequence[Entity]` + `DrawingSize`, and accepts both `dexpigen.entities` objects and the pipeline's `dexlib2` entities through `model_dump`. Contract violations raise `DexExtractionError`, which lists every problem. Decide how that error relates to the mapping diagnostics. `dex_id` sources include uuids and edge ids such as `edge_...`.

## Answer

Resolved by a fast-path grilling with the user on 2026-10-28 (one round of multiple-choice questions; defaults taken by the orchestrator are marked).

- **Entry points (user's choice):** `dex_to_model(graph, entities, size, model_id="DexModel")` returns a `DexConversion` with `model` (a `ConceptualModel`) and `report` (a list of strings, one line each). `dex_to_proteus(graph, entities, size)` returns the XML string, equal to `to_proteus_xml(dex_to_model(...).model)`. Both live in `dexpigen.entities`. The user's shorthand left out `model_id`; the spec keeps it.
- **Errors and report (user's choice):** contract violations raise `DexExtractionError`, which lists every problem. Mapping gaps never raise; they go to the report.
- **No strict mode (user's choice):** no flag turns mapping gaps into errors.
- **No CLI:** the entry points are the two functions above; no command-line entry point is part of the decision.
- **dex_id (taken by default):** `f"{ClassName}-{id}"`, with characters outside `[A-Za-z0-9_.-]` replaced by `_`. The class-name prefix means every `ID` starts with a letter, so a uuid that starts with a digit is still a valid XML NCName. Nodes, pipes and segments are named from it, as in section C of the spec.
- **Report content (spec):** one line each for skipped Entities, unsupported signal or sensing ends, the direction summary, and the instrument count line.
- **Checks (taken by default):** `dex_to_proteus` calls `to_proteus_xml`, which runs `_check_model` before writing. XSD validation stays a separate step (`examples/validate_dexpi.py`); the tests validate the C01 output.
- **`model_id` (taken by default):** it becomes the model's `dex_id` and so the `Drawing` name; the default is `DexModel`.
- **Id collisions (taken by default):** two ids that differ only in replaced characters (for example `a:b` and `a_b`), or a derived id that meets an Entity id (a nozzle `a-n1-Node1` next to the node of nozzle `a-n1`), give one `dex_id`. `dex_to_model` does not check this; `to_proteus_xml`'s duplicate-ID check rejects it before writing.
