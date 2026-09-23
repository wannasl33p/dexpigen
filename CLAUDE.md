# CLAUDE.md

DEXPI 1.3 in-memory model — a Python library that holds a DEXPI P&ID 1.3 conceptual model in memory (a typed object graph; no graphics, no Proteus XML, no NetworkX).

## Project map

- **Spec** — `.scratch/dexpi-13-inmemory-model/spec.md` (implementation spec; read first).
- **Glossary** — `CONTEXT.md` (domain vocabulary; use it for every term).
- **Decisions** — `.scratch/dexpi-13-inmemory-model/map.md` + `issues/` (resolved architecture decisions).
- **Research** — `.scratch/dexpi-13-inmemory-model/research/` (DEXPI 1.3 facts with citations).

## Rules

- **Toolchain** — use `uv` for dependency and environment management (`pyproject.toml`, `uv add`, `uv sync`, `uv run`). Consult current docs via context7 when unsure.
- **Python** — target **3.13** (`requires-python = ">=3.13"`).
- **Typing** — modern typing only: `X | None` (not `typing.Optional`), builtin generics `list[...]` / `dict[...]` / `tuple[...]` (not `typing.List`), and `typing.Self` where appropriate. Pydantic v2.
- **Language** — all comments and docstrings in **English**.
