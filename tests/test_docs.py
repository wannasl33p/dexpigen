"""Docs-vs-code sync checks over the hand-written user docs.

Checked files: ``README.md``, ``docs/recipes/*.md`` and ``docs/pitfalls.md``
(the generated ``docs/reference/`` has its own test). The checks:

1. every relative link and backticked file path exists (and none points into
   ``.scratch/``, which is contributor-only); links into Markdown files with an
   ``#anchor`` must name an existing heading;
2. every backticked ``CamelCase`` / ``snake_case`` name resolves to a dexpigen
   symbol, an element or attribute name in the bundled XSD, or a string in the
   latest ``examples/C01/verNNN/c01.xml`` golden;
3. a pitfall's backticked error message occurs verbatim in ``src/dexpigen``
   (skipped for entries enforced by ``XSD only``);
4. a pitfall's ``tests/<file>.py::test_name`` exists;
5. line-count budgets;
6. the README minimal example equals ``examples/minimal.py``.

Whether the prose is still semantically right is left to review and the
manual docs acceptance run.
"""

import inspect
import re
from enum import Enum
from pathlib import Path

import pytest
from pydantic import BaseModel

import dexpigen
from dexpigen import base, entities, enumerations, equipment, instrumentation, model, piping, serialization

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
PITFALLS = ROOT / "docs" / "pitfalls.md"
RECIPES = sorted((ROOT / "docs" / "recipes").glob("*.md"))
USER_DOCS = [README, *RECIPES, PITFALLS]
XSD = ROOT / "data" / "schemas" / "ProteusPIDSchema 4.1.1.xsd"
MINIMAL = ROOT / "examples" / "minimal.py"

# Line budgets (ticket 02). The generated class index is exempt.
BUDGETS = {"CLAUDE.md": 200, "README.md": 150, "docs/pitfalls.md": 200}
RECIPE_BUDGET = 100

FENCE = re.compile(r"^```[^\n]*\n.*?^```[ \t]*$", re.MULTILINE | re.DOTALL)
INLINE = re.compile(r"`([^`\n]+)`")
LINK = re.compile(r"(?<!!)\[[^\]\n]*\]\(([^)\s]+)\)")
HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)
NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*")
FILE_SUFFIXES = (".md", ".py", ".xml", ".xsd", ".toml", ".txt")
TEST_ID = re.compile(r"(tests/[\w/]+\.py)::(\w+)")


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _prose(text: str) -> str:
    """Text outside fenced code blocks."""
    return FENCE.sub("", text)


def _spans(text: str) -> list[str]:
    return INLINE.findall(_prose(text))


def _slug(heading: str) -> str:
    """GitHub's anchor for a heading."""
    text = heading.strip().lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def _anchors(path: Path) -> set[str]:
    seen: dict[str, int] = {}
    anchors: set[str] = set()
    for heading in HEADING.findall(_prose(_read(path))):
        slug = _slug(heading)
        count = seen.get(slug, 0)
        anchors.add(slug if count == 0 else f"{slug}-{count}")
        seen[slug] = count + 1
    return anchors


def _latest_golden() -> Path:
    return sorted((ROOT / "examples" / "C01").glob("ver[0-9][0-9][0-9]/c01.xml"))[-1]


def _dexpigen_names() -> set[str]:
    names: set[str] = set()
    for module in (dexpigen, base, entities, enumerations, equipment, piping, instrumentation, model, serialization):
        for name, obj in vars(module).items():
            names.add(name)
            if not inspect.isclass(obj):
                continue
            names.update(dir(obj))
            if issubclass(obj, BaseModel):
                names.update(obj.model_fields)
            if issubclass(obj, Enum):
                names.update(obj.__members__)
                names.update(str(member.value) for member in obj)
    return names


def _xsd_names() -> set[str]:
    pattern = re.compile(r'<xsd:(?:element|attribute)\b[^>]*\bname="([^"]+)"')
    return set(pattern.findall(_read(XSD)))


def _is_checked_name(token: str) -> bool:
    return "_" in token or (re.search("[a-z]", token) and re.search("[A-Z]", token)) is not None


def _pitfall_entries() -> list[tuple[str, dict[str, str]]]:
    """``(heading, {field: text})`` for every pitfall section."""
    entries = []
    for block in re.split(r"^## ", _prose(_read(PITFALLS)), flags=re.MULTILINE)[1:]:
        heading, _, body = block.partition("\n")
        if heading.strip() == "Contents":
            continue
        fields = dict(re.findall(r"^- \*\*(Symptom|Why|Fix|Enforced by):\*\* (.*)$", body, re.MULTILINE))
        entries.append((heading.strip(), fields))
    return entries


@pytest.mark.parametrize("doc", USER_DOCS, ids=_rel)
def test_links_resolve(doc):
    broken = []
    for target in LINK.findall(INLINE.sub("", _prose(_read(doc)))):
        if re.match(r"[a-z]+:", target):
            continue  # http(s), mailto, ...
        path_part, _, anchor = target.partition("#")
        path = (doc.parent / path_part).resolve() if path_part else doc
        if ".scratch" in path.parts or not path.exists():
            broken.append(target)
        elif anchor and path.suffix == ".md" and anchor not in _anchors(path):
            broken.append(target)
    assert not broken, f"{_rel(doc)}: broken links {broken}"


@pytest.mark.parametrize("doc", USER_DOCS, ids=_rel)
def test_backticked_paths_exist(doc):
    missing = []
    for span in _spans(_read(doc)):
        if "/" in span and (ROOT / span).exists():
            continue  # a path with spaces, e.g. the XSD
        words = span.split()
        for word in words:
            word = word.rstrip(".,;:)")
            path_like = "/" in word or (len(words) == 1 and word.endswith(FILE_SUFFIXES))
            if not path_like or any(mark in word for mark in ("<", ">", "*", "://", "NNN")):
                continue
            word = word.split("::")[0]
            if word.startswith(".scratch") or not (ROOT / word).exists():
                missing.append(word)
    assert not missing, f"{_rel(doc)}: paths that do not exist {missing}"


@pytest.mark.parametrize("doc", USER_DOCS, ids=_rel)
def test_backticked_names_resolve(doc):
    known = _dexpigen_names() | _xsd_names()
    golden = _read(_latest_golden())
    unknown = []
    for span in _spans(_read(doc)):
        token = span.removesuffix("()")
        if not NAME.fullmatch(token) or token.endswith(FILE_SUFFIXES):
            continue
        for part in token.split("."):
            if not _is_checked_name(part) or part in known:
                continue
            if re.search(rf"(?<![\w]){re.escape(part)}(?![\w])", golden):
                continue
            unknown.append(part)
    assert not unknown, (
        f"{_rel(doc)}: backticked names that are not a dexpigen symbol, an XSD name "
        f"or a string in {_rel(_latest_golden())}: {sorted(set(unknown))}"
    )


def test_pitfalls_have_all_fields():
    entries = _pitfall_entries()
    assert entries
    for heading, fields in entries:
        assert set(fields) == {"Symptom", "Why", "Fix", "Enforced by"}, heading
        assert fields["Why"].startswith(("DEXPI 1.3", "Project policy")), heading


def test_pitfall_symptoms_occur_in_source():
    source = "\n".join(_read(path) for path in sorted((ROOT / "src" / "dexpigen").glob("*.py")))
    missing = []
    for heading, fields in _pitfall_entries():
        if "XSD only" in fields["Enforced by"]:
            continue
        for span in INLINE.findall(fields["Symptom"]):
            if " " in span and span not in source:
                missing.append(f"{heading}: {span!r}")
    assert not missing, "error messages not found verbatim in src/dexpigen: " + "; ".join(missing)


def test_pitfall_enforced_by_names_existing_tests():
    problems = []
    for heading, fields in _pitfall_entries():
        enforced = fields["Enforced by"].strip()
        ids = TEST_ID.findall(enforced)
        if not ids:
            if enforced not in ("not enforced", "XSD only"):
                problems.append(f"{heading}: {enforced!r} is not a test id, 'XSD only' or 'not enforced'")
            continue
        for file, name in ids:
            path = ROOT / file
            if not path.exists() or f"def {name}(" not in _read(path):
                problems.append(f"{heading}: {file}::{name} does not exist")
    assert not problems, "; ".join(problems)


def test_size_budgets():
    # CLAUDE.md is contributor-only and absent from a user's checkout (and from
    # the docs-acceptance sandbox), so a missing file is not a failure.
    over = [
        f"{name}: {len(_read(ROOT / name).splitlines())} > {limit}"
        for name, limit in BUDGETS.items()
        if (ROOT / name).exists() and len(_read(ROOT / name).splitlines()) > limit
    ]
    over += [
        f"{_rel(recipe)}: {len(_read(recipe).splitlines())} > {RECIPE_BUDGET}"
        for recipe in RECIPES
        if len(_read(recipe).splitlines()) > RECIPE_BUDGET
    ]
    assert not over, f"over the line budget: {over}"


def test_readme_minimal_example_matches_script():
    section = _read(README).split("## Minimal example", 1)[1]
    match = re.search(r"^```python\n(.*?)^```", section, re.MULTILINE | re.DOTALL)
    assert match, "README.md has no python block under '## Minimal example'"
    assert match.group(1).strip() == _read(MINIMAL).strip(), (
        "the README minimal example differs from examples/minimal.py; copy the file into README.md"
    )
