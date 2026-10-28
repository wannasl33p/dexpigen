# CLAUDE.md

DEXPI 1.3 in-memory model — a Python library that holds a DEXPI P&ID 1.3 conceptual model in memory (a typed object graph, not Proteus XML; drawing graphics are optional fields, there is no shape catalogue). The model holds no NetworkX; NetworkX appears only in the `dexpigen.entities` input layer.

## Project map

- **User docs** — `README.md` is the entry for an agent that *uses* the library (scope, minimal example, links into `docs/`: recipes, pitfalls, generated class index). Start there for API questions.
- **Docs acceptance** — `acceptance/README.md`: held-out tasks a fresh agent rebuilds from the docs alone, run manually with `scripts/docs_acceptance.py` (billed; `run --dry-run` is free).
- **Spec** — `.scratch/dexpi-13-inmemory-model/spec.md` (implementation spec; read first).
- **Glossary** — `CONTEXT.md` (domain vocabulary; use it for every term).
- **Decisions** — `.scratch/dexpi-13-inmemory-model/map.md` + `issues/` (resolved architecture decisions).
- **Research** — `.scratch/dexpi-13-inmemory-model/research/` (DEXPI 1.3 facts with citations).
- **Dex input layer** — `src/dexpigen/entities/`: the Dex extraction input contract (Entities, `check_extraction`) and the converter (`dex_to_model`, `dex_to_proteus`), decided in `.scratch/dex-to-dexpi/` (`map.md` + `issues/`). `examples/C01/dex_model/` is the C01 sample; its adapter `load.py` is not public API.
- **Examples** — `examples/C01/` is the versioned recovery of the reference P&ID (see its `README.md`): `build.py` builds the model for the latest milestone, `verNNN/c01.xml` is that milestone's golden serialization. Trim with `examples/trim_dexpi_xml.py`, validate with `examples/validate_dexpi.py` (xmllint + XSD).

## Rules

- **Toolchain** — use `uv` for dependency and environment management (`pyproject.toml`, `uv add`, `uv sync`, `uv run`). Consult current docs via context7 when unsure.
- **Python** — target **3.13** (`requires-python = ">=3.13"`).
- **Typing** — modern typing only: `X | None` (not `typing.Optional`), builtin generics `list[...]` / `dict[...]` / `tuple[...]` (not `typing.List`), and `typing.Self` where appropriate. Pydantic v2.
- **Language** — all comments and docstrings in **English**.
- **Docs sync** — a change to the public API or to an error message updates README/recipes/pitfalls in the same commit. `tests/test_docs.py` checks their links, paths, backticked names, pitfall error texts and test ids, size budgets and the README example; regenerate the class index with `uv run python scripts/gen_reference.py`.
- **Serialization validation** — after generating any Proteus XML, validate it against the bundled XSD `data/schemas/ProteusPIDSchema 4.1.1.xsd` with `xmllint --noout --schema <xsd> <xml>` (see `examples/validate_dexpi.py`). Generated output must be schema-valid before it is considered done.
