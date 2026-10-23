"""Validate a Proteus XML file against the bundled XSD via ``xmllint``.

Requires ``xmllint`` (libxml2) on PATH.

Usage:
    uv run python examples/validate_dexpi.py [<file.xml>]

Default: examples/C01/ver001/c01.xml

From Python (with ``examples/`` on ``sys.path``)::

    from validate_dexpi import validate
    ok = validate("model.xml")
"""

import subprocess
import sys
from pathlib import Path

# Resolved from this file, so validation works from any working directory.
XSD = str(Path(__file__).resolve().parents[1] / "data" / "schemas" / "ProteusPIDSchema 4.1.1.xsd")


def validate(xml_path: str) -> bool:
    """Validate ``xml_path`` with xmllint; print its output and return success."""
    result = subprocess.run(
        ["xmllint", "--noout", "--schema", XSD, xml_path],
        capture_output=True,
        text=True,
    )
    if result.stdout:
        sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)
    return result.returncode == 0


if __name__ == "__main__":
    xml = sys.argv[1] if len(sys.argv) > 1 else "examples/C01/ver001/c01.xml"
    ok = validate(xml)
    print(f"\n{xml}: {'VALID' if ok else 'INVALID'}")
    sys.exit(0 if ok else 1)
