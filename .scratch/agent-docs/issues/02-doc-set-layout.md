# Decide the doc-set layout and agent entry point

Type: grilling
Status: resolved
Blocked by: 01-agent-doc-conventions
Assignee: alex.valentsinovich

## Question

Which files make up the doc set, where do they live, and how does an agent navigate them? Decide: the role of `CLAUDE.md` vs `CONTEXT.md` vs a new `docs/` tree (and whether a root `README.md` exists), the reading order, a size budget per file, and which parts are hand-written vs generated.

## Answer

Resolved by grilling on 2026-10-21. No ADR: every choice here is cheap to reverse.

- **Two entry points, two readers.** A new root `README.md` is the entry for an agent that *uses* the library. `CLAUDE.md` stays the entry for an agent that *develops* dexpigen (rules, toolchain, pointers) and gets one line pointing at `README.md`. No `AGENTS.md`.
- **`README.md` contents**, top to bottom: one line on what the library is and is not (not a drawing, not a graph, not a parser); a "Scope and limits" section (writes Proteus XML only, no reader yet; covered DEXPI areas); install and commands (`uv sync`, `uv run pytest`, `examples/validate_dexpi.py`); a minimal example (15-25 lines: build a small `ConceptualModel`, `to_proteus_xml`, validate) duplicated from a runnable `examples/minimal.py`, with a test that the README copy matches the file; a link list `- [name](path): when to read`.
- **Detail lives in a flat root `docs/`**, linked one level deep from `README.md`: `docs/recipes/<task>.md` (one file per task), `docs/pitfalls.md`, `docs/reference/` (generated). Docs are not shipped in the wheel.
- **`.scratch/` is contributor design history**, linked only from `CLAUDE.md`. User docs never link into it; a needed fact is copied into the docs.
- **`CONTEXT.md` stays the glossary** at the root, read on demand ("when a term is unclear"). Invariants go to `docs/pitfalls.md`, not into the glossary.
- **Only the class index is generated.** Everything else is hand-written; recipes link to runnable code instead of copying it. The README minimal example is the single exception (guarded by the test above).
- **Reading order:** `README.md` -> the task's recipe -> `docs/pitfalls.md` -> class index / `CONTEXT.md` on demand.
- **Size budgets** (by convention, no automated check yet): `CLAUDE.md` <= 200 lines, `README.md` <= 150, each recipe <= 100, `docs/pitfalls.md` <= 200 (TOC if over 100), class index unbounded but with a TOC.
- **Not done:** nested `CLAUDE.md` / `.claude/rules/` per-package notes (revisit when root `CLAUDE.md` nears its budget); a placeholder for the reader chapter.
- **`examples/C01/README.md` stays in place** as the contributor's milestone mechanism, linked from `CLAUDE.md`; the user `README.md` links `examples/C01/build.py` directly as the large real example.
