# Decide the docs-vs-code sync policy

Type: grilling
Status: resolved
Blocked by: 03-generated-class-index, 04-recipes-and-pitfalls
Assignee: alex.valentsinovich

## Question

The class index has its golden test (`tests/test_reference_docs.py`) and the recipe scripts have `tests/test_recipes.py`. What catches the rest when code changes: stale recipe *prose* and pitfall entries (a renamed class, a changed error message in **Symptom**, a moved test in **Enforced by**), the README minimal example vs `examples/minimal.py`, and the per-file size budgets (`CLAUDE.md` <= 200, `README.md` <= 150, recipe <= 100, `docs/pitfalls.md` <= 200)? Decide which of these get automated checks, whether they join pytest or need CI, and what stays a review convention.

## Answer

Resolved by grilling on 2026-10-23. No ADR: every choice is cheap to reverse.

- **One `tests/test_docs.py` in the normal `uv run pytest` run.** Every check is fast and deterministic. No CI job: the repo has none, and a future CI just runs pytest. The checks over `README.md`, `docs/recipes/*.md` and `docs/pitfalls.md`:
  1. **Links and paths:** every relative link and file path exists.
  2. **Backticked names:** every `CamelCase` / `snake_case` token in backticks resolves to a `dexpigen` symbol, an element or attribute name in `data/schemas/ProteusPIDSchema 4.1.1.xsd`, or a string in the latest `examples/C01/verNNN/c01.xml` golden (where RDL names like `TagNameAssignmentClass` live). No hand-kept allowlist.
  3. **Pitfall Symptom:** a backticked error message must occur verbatim in `src/`. Entries whose symptom is xmllint output or wrong XML are marked `XSD only` and skipped.
  4. **Pitfall Enforced by:** `tests/<file>.py::test_name` must name an existing file containing `def test_name` (grep, no pytest collection). `not enforced` and `XSD only` are skipped.
  5. **Size budgets:** line counts `CLAUDE.md` <= 200, `README.md` <= 150, each recipe <= 100, `docs/pitfalls.md` <= 200; the numbers are constants in the test. The class index is exempt.
  6. **README minimal example == `examples/minimal.py`** (decided in ticket 02; it lives here).
- **Convention, not automated:** whether prose is still *semantically* right is caught by the acceptance protocol and review. `CLAUDE.md` gets the rule: "a change to the public API or to an error message updates README/recipes/pitfalls in the same commit". Writing that line is part of writing the docs.
