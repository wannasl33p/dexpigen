"""Serialization: Proteus output must validate and match the reference fixture.

The project rule (CLAUDE.md): after generating any Proteus XML, validate it
with ``xmllint`` against the schema. On top of that, serializing the C01 model
built by ``examples/C01/build.py`` must reproduce ``examples/C01/ver001/c01.xml``
(compared canonically: ignoring whitespace, ``ID`` values and the graphics-only
``ComponentName`` attribute).
"""

import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

from dexpigen.serialization import to_proteus_xml

XSD = "data/schemas/ProteusPIDSchema 4.1.1.xsd"
EXAMPLES = os.path.join(os.path.dirname(__file__), "..", "examples")


def proteus_is_valid(xml_path: str) -> bool:
    """Return True if ``xml_path`` validates against the bundled XSD."""
    result = subprocess.run(
        ["xmllint", "--noout", "--schema", XSD, xml_path],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _canonical(root: ET.Element):
    """A comparable, order-insensitive signature of an element tree."""

    def norm(elem: ET.Element):
        attrs = {k: v for k, v in elem.attrib.items() if k not in ("ID", "ComponentName")}
        return (elem.tag, tuple(sorted(attrs.items())), [norm(c) for c in elem])

    return norm(root)


@pytest.mark.skipif(shutil.which("xmllint") is None, reason="xmllint is not on PATH")
def test_generation_fixture_validates_against_xsd():
    assert proteus_is_valid("examples/C01/ver001/c01.xml")


def test_serialize_matches_c01_fixture():
    sys.path.insert(0, EXAMPLES)
    from C01.build import build  # noqa: PLC0415

    got = ET.fromstring(to_proteus_xml(build()))
    expected = ET.parse(os.path.join(EXAMPLES, "C01", "ver001", "c01.xml")).getroot()
    assert _canonical(got) == _canonical(expected)
