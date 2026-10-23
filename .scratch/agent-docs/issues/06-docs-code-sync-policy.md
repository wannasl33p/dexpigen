# Decide the docs-vs-code sync policy

Type: grilling
Status: open
Blocked by: 03-generated-class-index, 04-recipes-and-pitfalls

## Question

The class index has its golden test (`tests/test_reference_docs.py`) and the recipe scripts have `tests/test_recipes.py`. What catches the rest when code changes: stale recipe *prose* and pitfall entries (a renamed class, a changed error message in **Symptom**, a moved test in **Enforced by**), the README minimal example vs `examples/minimal.py`, and the per-file size budgets (`CLAUDE.md` <= 200, `README.md` <= 150, recipe <= 100, `docs/pitfalls.md` <= 200)? Decide which of these get automated checks, whether they join pytest or need CI, and what stays a review convention.
