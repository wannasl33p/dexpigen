# Agent-facing documentation for dexpigen

Label: `wayfinder:map`

## Destination

The decided shape of an **agent-facing documentation set** for dexpigen: entry point, generated class index, task recipes, invariants/pitfalls catalogue, and an acceptance test. A fresh agent session given only the repo and these docs must be able to use the library correctly: build a `ConceptualModel`, serialize it to Proteus XML, and (once it exists) parse DEXPI XML back into the model. This map produces **decisions**; writing the documentation text is a separate step.

## Notes

- Audience: LLM agents first (the library is the base for an agent-written DEXPI framework); human contributors second.
- Form: English Markdown in the repo; no site generator. Existing entry points: `CLAUDE.md`, `CONTEXT.md` (glossary), `examples/C01/README.md`.
- Docs describe the code after v0.2 is implemented and the review defects are fixed; both are done by a separate implementation subagent, outside this map.
- Fact to carry: the library currently **only writes** Proteus XML (`spec.md`: "the library itself only writes"). A reader/parser is wanted but not designed.
- Skills: `domain-modeling`, `grilling` for HITL tickets; `research` for external conventions.
- Acceptance idea (Q7): a fresh agent session, with only docs + code, reproduces `examples/C01` (or part of it) and passes `examples/validate_dexpi.py`.

## Decisions so far

<!-- one line per closed ticket -->

- [Survey conventions for agent-facing library docs](issues/01-agent-doc-conventions.md): keep `CLAUDE.md` short pointers (<~200 lines), lazy-load detail via linked/nested files, prefer runnable examples over prose; no source prescribes code-generated docs or a CI doc-vs-code check (findings on branch `research-agent-doc-conventions`).
- [Decide the doc-set layout and agent entry point](issues/02-doc-set-layout.md): new root `README.md` is the library user's entry, `CLAUDE.md` stays the contributor's; flat `docs/` (`recipes/<task>.md`, `pitfalls.md`, generated `reference/`); `.scratch/` contributor-only; only the class index is generated; per-file size budgets.
- [Decide the generated class index](issues/03-generated-class-index.md): per-module `docs/reference/*.md` introspected by `scripts/gen_reference.py`, guarded by a pytest golden test; composition vs reference from a mandatory per-field `Composed`/`Ref` marker in code; wire names and the extraction-type lookup are not generated (lookup rule is hand-written in pitfalls).
- [Decide the task recipes and the invariants/pitfalls catalogue](issues/04-recipes-and-pitfalls.md): six recipes covering the C01 surface, each anchored to a runnable `examples/recipes/<task>.py` guarded by a coverage test against the latest C01 golden; 15 pitfalls in a Symptom/Why/Fix/Enforced-by format; unenforced traps (and a double-`add_nozzle` bug) handed to implementation; `DEX_ID`/`id` glossary corrected.

## Not yet specified

- **Reader chapter**: how docs describe parsing DEXPI/Proteus XML into the model (unknown elements, ID resolution, round-trip guarantees). Depends on a reader design that does not exist yet. Also covers documenting the field -> wire-name mapping (`TagNameAssignmentClass`, `<Connection>`), which today lives only in the serializer and which the reader needs in reverse.
- **Docs-vs-code sync policy**: the class index has its golden test and recipe scripts have `tests/test_recipes.py`; still open is how stale recipe *prose* and pitfall entries (a renamed class, a changed error message) are caught. Also covers: an automated check of the per-file size budgets, the test that the README minimal example matches `examples/minimal.py`, and whether these join the existing tests or a CI job.
- **Untracked `src/dexpigen/entities/` and `examples/C01/dex_model/`**: extraction-pipeline entity classes (`dexlib2`, `shapely`, `src.app` imports; not importable here) and C01 extraction output. Open: whether they become a documented input layer, and therefore whether the class-index generator walks an explicit module list or all of `dexpigen.*`. Deferred by the user.

## Out of scope

- Implementing v0.2 (`PipeTee`, `InstrumentationLoopFunction`, sensing layer) and fixing the review defects: separate implementation subagent.
- Designing and implementing the DEXPI reader/parser: a separate effort with its own map; this map only reserves room for its chapter.
- Writing the final documentation text (follows the decisions here).
- HTML/site generation (mkdocs etc.) and a Russian-language version.
- A library API for "extraction type -> class" lookup (e.g. `equipment_class_for`): new public API, not a docs decision; ruled out while resolving [Decide the generated class index](issues/03-generated-class-index.md).
