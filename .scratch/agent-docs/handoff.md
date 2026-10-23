# Handoff: build the agent-facing documentation set

Brief for the implementation agent. The map ([map.md](map.md)) is fully resolved; this file turns its decisions into ordered work. Each decision lives in exactly one ticket; this brief only sequences them and points there. When a ticket and this brief disagree, the ticket wins.

## Read first

- `CLAUDE.md`: toolchain and rules (`uv`, Python 3.13, modern typing, every generated XML validated with `examples/validate_dexpi.py`).
- `CONTEXT.md`: glossary. Use **Composition**, **Reference**, **DEX_ID**, **id** exactly as defined there.
- The tickets, in order: [02 layout](issues/02-doc-set-layout.md), [03 class index](issues/03-generated-class-index.md), [04 recipes and pitfalls](issues/04-recipes-and-pitfalls.md), [05 acceptance](issues/05-acceptance-protocol.md), [06 sync policy](issues/06-docs-code-sync-policy.md).

## Ground rules

- Do not touch the untracked `src/dexpigen/entities/` or `examples/C01/dex_model/`. Their role is undecided (map fog). Don't import them; don't delete them.
- Keep `uv run pytest` green after every work package (167 tests pass at handoff, commit `943b82e`).
- One work package per commit (Conventional Commits).
- The package version is `0.2.0`. You may bump it in `pyproject.toml` (`uv.lock` is gitignored) when a work package changes the public API, e.g. a new error a caller can hit in WP2.

## Work packages

Do them in order. Each one lists what it depends on.

### WP1 - `Composed` / `Ref` field markers ([03](issues/03-generated-class-index.md))

- Define the two markers in `dexpigen.base`. Annotate every field whose type is a `DexpiBaseModel` subclass, whether bare, in `list[...]`, or `| None`.
- The per-field call is not per-class. `PipingNode` is `Composed` in `PipingNodeOwner.nodes` and `Ref` in `Pipe.source_node` / `target_node`. Take each field's meaning from its docstring, its `add_*` / `_adopt_*` method and the serializer: a nested element means `Composed`, an `Association` means `Ref`.
- The `ConceptualModel` top-level lists are `Composed`: the serializer nests them under `PlantModel`.
- The markers must not change runtime behaviour or serialization. Done when every such field is marked and existing tests pass.

### WP2 - Enforcement gaps and side findings ([04](issues/04-recipes-and-pitfalls.md), [05](issues/05-acceptance-protocol.md))

- **Bug (fix it):** calling `Equipment.add_nozzle` / `add_drying_chamber` twice with the same child on the same owner appends a duplicate. Reject it the way PIF children do (`test_*_same_owner_readd_is_rejected`). Add tests.
- **Gaps (design is yours, keep it minimal):**
  - `dex_id` uniqueness and NCName shape: today only the XSD catches it, because it becomes Proteus `ID` (`xsd:ID`);
  - objects that are referenced but not composed anywhere reachable from `ConceptualModel`;
  - list mutation (`.nozzles.append`) bypassing `_adopt_*`.

  A gap you close gets a stable error message and a test. A gap you leave stays `not enforced` in pitfalls. Record what you did in a comment on ticket 04.
- **Investigate:** trimmed C03 contains `ComponentClass="PipeFitting"`, while the model treats `PipeFitting` as abstract. Check DEXPI 1.3 and report back; don't change the model on a guess.

### WP3 - Class index generator ([03](issues/03-generated-class-index.md)); needs WP1

- `scripts/gen_reference.py` writes `docs/reference/{index,equipment,piping,instrumentation,model,enumerations}.md`.
- Content, ordering and the leaf table follow ticket 03 exactly.
- Walk an **explicit module list** (`base`, `enumerations`, `equipment`, `piping`, `instrumentation`, `model`), not all of `dexpigen.*`: the `entities` package can't be imported. This is an interim choice until the fog item is decided.
- `tests/test_reference_docs.py` regenerates in memory and compares with the committed files. It fails with the regeneration command, and it also fails on a `DexpiBaseModel`-typed field without a marker.

### WP4 - Recipe scripts ([04](issues/04-recipes-and-pitfalls.md))

- `examples/minimal.py` (15-25 lines: small model, `to_proteus_xml`, validate) doubles as the `serialize-and-validate` script.
- `examples/recipes/{equipment_and_nozzles,piping_network,measurement,control_valve,custom_attributes}.py`: self-contained and runnable.
- `tests/test_recipes.py` runs every script, serializes the result and validates it with xmllint. It also asserts that the union of `ComponentClass` values and element tags covers the latest `examples/C01/verNNN/c01.xml`.

### WP5 - Documentation text ([02](issues/02-doc-set-layout.md), [04](issues/04-recipes-and-pitfalls.md), [06](issues/06-docs-code-sync-policy.md)); needs WP3, WP4

- `README.md` (<= 150 lines): sections and order as in ticket 02. The minimal example is copied from `examples/minimal.py`. End with a link list in the form `- [name](path): when to read`.
- `docs/recipes/<task>.md` (<= 100 lines each, six recipes): goal, prose steps naming classes, a link to the script, links to the relevant pitfalls. No copied code.
- `docs/pitfalls.md` (<= 200 lines, TOC): the 15 entries from ticket 04 in the Symptom / Why / Fix / Enforced by format. **Enforced by** reflects WP2's outcome.
- `CLAUDE.md`: one line pointing at `README.md`, and the rule "a change to the public API or to an error message updates README/recipes/pitfalls in the same commit".
- User docs never link into `.scratch/`.

### WP6 - Docs checks ([06](issues/06-docs-code-sync-policy.md)); needs WP5

`tests/test_docs.py` checks links and paths, backticked names, pitfall Symptom and Enforced by, size budgets, and that the README example matches `examples/minimal.py`. Every check is spelled out in ticket 06.

### WP7 - Acceptance ([05](issues/05-acceptance-protocol.md)); needs WP5

- For each of I03, E06 and P02:
  1. trim the raw example from `data/example_pids/` into `acceptance/<task>/input.xml`;
  2. write `acceptance/<task>/solution.py`;
  3. prove that `solution.py` reproduces `input.xml` canonically.

  If a task can't be reproduced, trim it further or replace it, and say so.
- `acceptance/README.md` and `scripts/docs_acceptance.py`: the runner sets up the sandbox, runs headless `claude -p` on Sonnet 5.5, checks the result and writes the report. Sandbox, pass criteria and run count follow ticket 05.
- The first run happens after WP5. Failures are triaged into doc fixes, not into the task.

## Not decided: ask the human

- Anything in the map's **Not yet specified** (the reader chapter, the `entities` package).
