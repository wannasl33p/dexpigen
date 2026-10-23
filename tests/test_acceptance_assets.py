"""The docs-acceptance assets stay feasible as the code changes.

Each ``acceptance/<task>/solution.py`` is the contributor's reference solution:
serializing its ``build()`` must be schema-valid and canonically equal to the
task's ``input.xml``, through the same checker the acceptance runner uses.
When the raw examples are present, ``input.xml`` must also be exactly what
``scripts/docs_acceptance.py prepare`` regenerates.

This file is excluded from the acceptance sandbox, together with ``acceptance/``.
"""

import importlib.util
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE = ROOT / "acceptance"

pytestmark = pytest.mark.skipif(not ACCEPTANCE.exists(), reason="no acceptance/ assets")


def _runner():
    spec = importlib.util.spec_from_file_location(
        "docs_acceptance", ROOT / "scripts" / "docs_acceptance.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their module by name
    spec.loader.exec_module(module)
    return module


RUNNER = _runner()


@pytest.mark.skipif(shutil.which("xmllint") is None, reason="xmllint is not on PATH")
@pytest.mark.parametrize("task", sorted(RUNNER.TASKS))
def test_reference_solution_reproduces_input(task):
    result = RUNNER._check_in_subprocess(
        ACCEPTANCE / task / "solution.py", ACCEPTANCE / task / "input.xml"
    )
    assert result.built, result.error
    assert result.valid
    assert result.exact, result.diff


@pytest.mark.parametrize("task", sorted(RUNNER.TASKS))
def test_input_is_what_prepare_generates(task):
    source = RUNNER.RAW / RUNNER.TASKS[task]
    if not source.exists():
        pytest.skip("raw example not present (data/example_pids is not committed)")
    sys.path.insert(0, str(ROOT / "examples"))
    from trim_dexpi_xml import trim

    with tempfile.TemporaryDirectory() as tmp:
        trimmed = Path(tmp) / "trimmed.xml"
        trim(str(source), str(trimmed))
        expected = RUNNER.normalize(trimmed.read_text(encoding="utf-8"))
    actual = (ACCEPTANCE / task / "input.xml").read_text(encoding="utf-8")
    assert actual == expected, "regenerate with: uv run python scripts/docs_acceptance.py prepare"


def test_task_verdict_rule():
    check, run = RUNNER.Check, RUNNER.RunResult

    def result(valid, exact):
        return run(task="T", run=1, check=check(built=True, valid=valid, exact=exact, src_unmodified=True))

    assert RUNNER.task_passes([result(True, True), result(True, True), result(True, False)])
    assert not RUNNER.task_passes([result(True, True), result(True, False), result(True, False)])
    assert not RUNNER.task_passes([result(True, True), result(True, True), result(False, False)])
    tampered = result(True, True)
    tampered.check.src_unmodified = False
    assert not RUNNER.task_passes([tampered, result(True, True), result(True, True)])
