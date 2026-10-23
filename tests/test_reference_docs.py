"""The generated class index under ``docs/reference/`` must match the code.

``scripts/gen_reference.py`` is run in memory and compared with the committed
files. A mismatch means the code changed without regenerating the index.
Separately, every field typed with a ``DexpiBaseModel`` subclass must carry a
``Composed`` or ``Ref`` marker, since the index's Relation column comes from it.
"""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _generator():
    spec = importlib.util.spec_from_file_location(
        "gen_reference", ROOT / "scripts" / "gen_reference.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_reference_docs_are_up_to_date():
    gen = _generator()
    stale = []
    for filename, expected in gen.render().items():
        path = gen.OUT_DIR / filename
        actual = path.read_text(encoding="utf-8") if path.exists() else None
        if actual != expected:
            stale.append(filename)
    committed = sorted(p.name for p in gen.OUT_DIR.glob("*.md"))
    extra = sorted(set(committed) - set(gen.render()))
    assert not stale and not extra, (
        f"docs/reference is stale (changed: {stale}, unexpected: {extra}); "
        f"regenerate with: {gen.REGENERATE}"
    )


def test_every_model_typed_field_has_a_relation_marker():
    missing = _generator().unmarked_fields()
    assert not missing, (
        "annotate these fields with Annotated[..., Composed] or Annotated[..., Ref] "
        f"from dexpigen.base: {', '.join(missing)}"
    )
