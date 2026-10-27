# Decide the public conversion API

Type: grilling
Status: open
Blocked by: 03-dex-input-contract

## Question

What does a developer call, and what do they get back? Decide:

- the entry points (`dex_to_model(extraction) -> ConceptualModel`, `dex_to_proteus(...) -> str`, a CLI?);
- the diagnostics for Entities and edges that could not be mapped (warnings, a report object, strict mode);
- how `dex_id` is formed from Entity ids: uuids may start with a digit, which is not an XML NCName, so a prefix is needed;
- how the result relates to `_check_model` and XSD validation.

Input from [Decide the Dex extraction input contract](03-dex-input-contract.md): there is no file loader in the public API. The converter takes `nx.Graph` + `Sequence[Entity]` + `DrawingSize`, and accepts both `dexpigen.entities` objects and the pipeline's `dexlib2` entities through `model_dump`. Contract violations raise `DexExtractionError`, which lists every problem. Decide how that error relates to the mapping diagnostics. `dex_id` sources include uuids and edge ids such as `edge_...`.
