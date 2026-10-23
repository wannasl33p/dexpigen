"""Every recipe script runs, serializes and validates; together they cover C01.

The scripts are ``examples/minimal.py`` (the serialize-and-validate recipe and
the README example) and ``examples/recipes/*.py``. Each defines ``build()``.
The coverage check asserts that the union of ``ComponentClass`` values and
element tags the scripts emit covers everything in the latest
``examples/C01/verNNN/c01.xml`` golden, so a new C01 milestone with a new class
fails here until a recipe shows it.
"""

import importlib.util
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from dexpigen import to_proteus_xml

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
XSD = ROOT / "data" / "schemas" / "ProteusPIDSchema 4.1.1.xsd"
SCRIPTS = [EXAMPLES / "minimal.py", *sorted((EXAMPLES / "recipes").glob("*.py"))]
RECIPES = [
    "equipment_and_nozzles", "piping_network", "measurement", "control_valve",
    "custom_attributes",
]


def _load(path: Path):
    if str(EXAMPLES) not in sys.path:
        sys.path.insert(0, str(EXAMPLES))  # for ``from validate_dexpi import ...``
    spec = importlib.util.spec_from_file_location(f"recipe_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _latest_golden() -> Path:
    return sorted((EXAMPLES / "C01").glob("ver[0-9][0-9][0-9]/c01.xml"))[-1]


def _vocabulary(root: ET.Element) -> set[str]:
    tags = {f"tag:{e.tag}" for e in root.iter()}
    classes = {f"class:{e.get('ComponentClass')}" for e in root.iter() if e.get("ComponentClass")}
    return tags | classes


def test_every_recipe_script_exists():
    assert sorted(p.stem for p in SCRIPTS[1:]) == sorted(RECIPES)


@pytest.mark.parametrize("path", SCRIPTS, ids=lambda p: p.stem)
@pytest.mark.skipif(shutil.which("xmllint") is None, reason="xmllint is not on PATH")
def test_recipe_serializes_to_schema_valid_xml(path, tmp_path):
    xml = to_proteus_xml(_load(path).build())
    out = tmp_path / f"{path.stem}.xml"
    out.write_text(xml, encoding="utf-8")
    result = subprocess.run(
        ["xmllint", "--noout", "--schema", str(XSD), str(out)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("path", SCRIPTS, ids=lambda p: p.stem)
@pytest.mark.skipif(shutil.which("xmllint") is None, reason="xmllint is not on PATH")
def test_recipe_script_runs(path, tmp_path):
    result = subprocess.run(
        [sys.executable, str(path)], cwd=tmp_path, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_recipes_cover_latest_c01_golden():
    emitted: set[str] = set()
    for path in SCRIPTS:
        emitted |= _vocabulary(ET.fromstring(to_proteus_xml(_load(path).build())))
    golden = _latest_golden()
    missing = _vocabulary(ET.parse(golden).getroot()) - emitted
    assert not missing, (
        f"{golden.relative_to(ROOT).as_posix()} has tags/classes no recipe emits: "
        f"{sorted(missing)}; extend a script under examples/recipes/"
    )
