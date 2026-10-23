# Docs acceptance

Contributor material: checks that the user docs (`README.md`, `docs/`, `CONTEXT.md`) are enough for a fresh agent to use dexpigen correctly. Decided in `.scratch/agent-docs/issues/05-acceptance-protocol.md`. This directory never reaches the agent under test.

## Tasks

Held-out P&IDs, not C01 (its `build.py` is in the repo, so reproducing it would test copying).

| Task | Raw example (`data/example_pids/`) | Content | Recipes exercised |
| --- | --- | --- | --- |
| `I03` | I03 Measurement and Control | tank and nozzle, globe valve, actuating system, PIF with actuating function and PSGF, loop | equipment, piping, measurement, control valve, custom attributes |
| `E06` | E06 Pump, HeatExchanger, Nozzles Connected With PNS | centrifugal pump, plate heat exchanger, six nozzles, one line with a pipe | equipment, piping, custom attributes |
| `P02` | P02 Pipe From OPC to Nozzle | pump nozzle, flow-in off-page connector referenced by number, one pipe | equipment, piping, custom attributes |

All three use serialize-and-validate.

Per task:

- `input.xml`: the task input, committed. Produced by `uv run python scripts/docs_acceptance.py prepare`: `examples/trim_dexpi_xml.py` deletes what the model cannot represent, then two document-level normalizations the model cannot express are applied, keeping every top-level element's content byte for byte: the `PlantInformation` header is replaced by the fixed one `to_proteus_xml` writes, and the top-level elements are stably reordered into the writer's order (actuating systems, piping network systems, PIFs, equipment, loops). Without them no model could match the raw examples (they come from another tool version and order elements differently).
- `solution.py`: the reference solution, `build() -> ConceptualModel`. It proves the task is feasible: `uv run python scripts/docs_acceptance.py verify` and `tests/test_acceptance_assets.py` check that it serializes schema-valid and canonically equal to `input.xml`. The test also checks that `input.xml` is what `prepare` regenerates when `data/example_pids/` is present.

## Protocol

For each task and each run:

1. **Sandbox.** `HEAD` is exported with `git archive` into a new temporary directory, without `.scratch/`, `CLAUDE.md`, `acceptance/`, `scripts/docs_acceptance.py` and `tests/test_acceptance_assets.py` (`data/example_pids/` is never committed). It becomes a fresh git repository with a single commit, so the agent sees no history (a worktree of this repo would expose `acceptance/` through git objects). `uv sync` runs, then the task's `input.xml` is copied in. Kept: `README.md`, `docs/`, `CONTEXT.md`, `src/`, `examples/` (C01 included), `tests/`.
2. **Agent.** Headless Claude Code in the sandbox: `claude -p` with `--model claude-sonnet-5-5`, `--safe-mode` (no user CLAUDE.md, skills, plugins, hooks or MCP servers), `--permission-mode dontAsk`, tools limited to Read, Write, Edit, Glob, Grep and Bash restricted to `uv`, `ls` and `xmllint` commands; WebFetch and WebSearch are disallowed. The prompt (`PROMPT` in the runner) asks for `solution.py` with `build() -> ConceptualModel` reproducing `input.xml`, using only the repository and starting at `README.md`.
3. **Check.** In a separate interpreter the checker imports the agent's `build()` and serializes it with `to_proteus_xml` itself (hand-written XML does not count), validates the result with `examples/validate_dexpi.py`, and compares it with `input.xml` using the canonical comparison of `tests/test_serialization.py` (whitespace, `ID` values and `ComponentName` ignored). `git status` in the sandbox must show `src/` unmodified. On a mismatch the report carries a per-element diff.

A **task passes** when all runs are schema-valid with `src/` unmodified and at least two thirds (2 of 3) match exactly. The default is 3 runs per task on Sonnet 5.5, deliberately weaker than the authoring model.

## Running

```bash
uv run python scripts/docs_acceptance.py verify               # reference solutions only, no sandbox
uv run python scripts/docs_acceptance.py run --dry-run        # sandboxes + checker on the reference solutions, no API cost
uv run python scripts/docs_acceptance.py run                  # the real run: 3 x 3 billed claude -p sessions
uv run python scripts/docs_acceptance.py run --tasks I03 --runs 1 --keep --max-budget-usd 5
```

`--keep` keeps the sandboxes for inspection; `--model` overrides the model. Commit the docs first: the sandbox is built from `HEAD`, and the runner warns about uncommitted changes. Each run writes `acceptance/reports/<UTC timestamp>.md` (gitignored; `-dry` suffix for dry runs) with a row per run, the verdict per task and the diffs.

## When to run

Manually, never in pytest or CI (costly and nondeterministic): after the docs text changes substantially, after each new C01 milestone, and before a release.

## Triage

A failure is a docs problem, not a task problem: read the diff and the agent's sandbox (`--keep`), find the missing or misleading statement in `README.md`, a recipe or `docs/pitfalls.md`, fix it there, and re-run. Do not edit `input.xml` or the prompt to make a run pass.
