# Decide the docs acceptance protocol

Type: grilling
Status: resolved
Blocked by: 02-doc-set-layout
Assignee: alex.valentsinovich

## Question

How do we verify the docs are sufficient? Pin down the fresh-agent test: allowed inputs (docs + code only), the task (reproduce `examples/C01`, or a smaller excerpt such as C05), the pass criteria (schema-valid via `examples/validate_dexpi.py`, structural match to the golden XML), who runs it, and when it re-runs.

Input from [Decide the task recipes and the invariants/pitfalls catalogue](04-recipes-and-pitfalls.md): recipes cover exactly the C01 surface, and `tests/test_recipes.py` already checks mechanically that the recipe scripts cover the latest C01 golden. The fresh-agent test measures what that check can't: whether an agent can *use* the docs.

## Answer

Resolved by grilling on 2026-10-23. No ADR: every choice is cheap to reverse.

- **Tasks: a held-out set, not C01.** `examples/C01/build.py` is in the repo, so reproducing C01 would test copying, not the docs. The tasks are **I03** (tank, nozzle, PIF, PSGF, control valve, loop), **E06** (pump, plate heat exchanger, nozzles, piping system) and **P02** (pump, off-page connector by number). Together they cover all six recipes. C04/C05/C06/C08 ship only `.pptx`, so "C05" is not available. Every example with XML in `data/example_pids/` trims to XSD-valid output (checked 2026-10-23).
- **Feasibility first:** each task gets a contributor-written reference solution that proves the model can reproduce it exactly. A task that can't be reproduced is trimmed further or replaced.
- **Task input:** the trimmed Proteus XML plus the instruction "write `build() -> ConceptualModel` whose serialization reproduces this file". This is manual deserialization.
- **Pass criteria (per run):**
  1. the checker imports the agent's `build()` and serializes it with `to_proteus_xml` itself; hand-built XML strings don't count;
  2. `examples/validate_dexpi.py` reports VALID;
  3. `_canonical(got) == _canonical(input)`, the same comparison as the C01 golden test;
  4. `src/` is unmodified.
  On failure the checker prints a per-element diff; failures are triaged into doc fixes.
- **Sandbox:** a clean git worktree without `.scratch/`, `CLAUDE.md` (contributor entry; a library user never sees it), `acceptance/` and `data/example_pids/`. It keeps `README.md`, `docs/`, `CONTEXT.md`, `src/`, `examples/` (C01 included) and `tests/`. Web access is off. Only the task's `input.xml` is placed in.
- **Runs:** 3 per task on **Sonnet 5.5**, deliberately weaker than the authoring model. A task passes when 3/3 runs are schema-valid and at least 2/3 match exactly.
- **Runner and cadence:** `scripts/docs_acceptance.py` builds the sandbox, runs headless `claude -p`, checks the result and writes a report. It runs manually, not in pytest/CI (costly, nondeterministic): after the docs text is first written, after each new C01 milestone, and before a release.
- **Assets:** `acceptance/<task>/input.xml` (trimmed, committed like `examples/C01/verNNN/c01.xml`), `acceptance/<task>/solution.py` (reference) and `acceptance/README.md`. Raw `data/example_pids/` stays uncommitted.
- **Side finding (for the implementation subagent, outside this map):** trimmed C03 contains `ComponentClass="PipeFitting"`, while the model treats `PipeFitting` as abstract.
