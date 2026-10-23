"""Docs acceptance: can a fresh agent rebuild held-out P&IDs from the docs alone?

Protocol (ticket 05, details in ``acceptance/README.md``): for each task a
clean sandbox is exported from ``HEAD`` without ``.scratch/``, ``CLAUDE.md``,
``acceptance/`` and this runner; only the task's ``input.xml`` is placed in it.
A headless ``claude -p`` session on Sonnet 5.5 writes ``solution.py`` with
``build() -> ConceptualModel``. The checker then imports ``build()``, serializes
it with ``to_proteus_xml`` itself, validates it with ``examples/validate_dexpi.py``
and compares it canonically with ``input.xml``; ``src/`` must be unmodified.
A task passes when all runs are schema-valid and at least two thirds match.

Commands (run from the repository root):

    uv run python scripts/docs_acceptance.py prepare
        Re-create acceptance/<task>/input.xml from data/example_pids/.
    uv run python scripts/docs_acceptance.py verify
        Check every reference solution against its input.xml (no sandbox).
    uv run python scripts/docs_acceptance.py run --dry-run [--runs 1]
        Build each sandbox and run the checker on the reference solution
        instead of an agent: tests the runner without any API cost.
    uv run python scripts/docs_acceptance.py run [--tasks I03 E06 P02] [--runs 3]
        The real, billed run with headless claude -p. Manual only.

The run writes a Markdown report to acceptance/reports/ (gitignored).
"""

from __future__ import annotations

import argparse
import difflib
import importlib.util
import io
import json
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE = ROOT / "acceptance"
REPORTS = ACCEPTANCE / "reports"
RAW = ROOT / "data" / "example_pids"

MODEL = "claude-sonnet-5-5"
RUNS = 3
TASKS: dict[str, str] = {
    "I03": "I03 Measurement and Control/I03V01-VER.EX01.xml",
    "E06": "E06 Pump, HeatExchanger, Nozzles Connected With PNS/E06V01-VER.EX01.xml",
    "P02": "P02 Pipe From OPC to Nozzle/P02V01-VER.EX01.xml",
}

# Removed from the sandbox: contributor docs, the held-out assets and their checks.
SANDBOX_EXCLUDE = [
    ".scratch", "CLAUDE.md", "acceptance", ".claude",
    "scripts/docs_acceptance.py", "tests/test_acceptance_assets.py",
]

# Top-level PlantModel children in the order ``to_proteus_xml`` writes them.
WRITER_ORDER = {
    "PlantInformation": 0, "ActuatingSystem": 1, "PipingNetworkSystem": 2,
    "ProcessInstrumentationFunction": 3, "Equipment": 4, "InstrumentationLoopFunction": 5,
}

PROMPT = """\
You are in a checkout of dexpigen, a Python library for DEXPI P&ID models.
The file input.xml in this directory is the Proteus XML of a small P&ID.

Task: write solution.py in this directory. It must define
    build() -> ConceptualModel
using the dexpigen classes, such that dexpigen.to_proteus_xml(build()) reproduces
input.xml. The comparison is element by element: same tags, same child order,
same attributes and values; whitespace, ID attribute values and ComponentName
are ignored, but every reference attribute (ItemID, FromID, ToID) must match,
so reuse the IDs from input.xml as dex_id values.

Rules:
- Use only this repository; start with README.md.
- Build the model with the library; do not write XML by hand.
- Do not modify anything under src/.
- Run Python through uv (for example: uv run python solution.py).
- Before finishing, serialize build() and validate the result with
  examples/validate_dexpi.py; it must report VALID.
"""

ALLOWED_TOOLS = [
    "Read", "Write", "Edit", "Glob", "Grep",
    "Bash(uv run *)", "Bash(uv sync*)", "Bash(ls *)", "Bash(xmllint *)",
]


# --- canonical comparison (same as tests/test_serialization.py::_canonical) ---


def canonical(root: ET.Element):
    """A comparable signature of an element tree (ignores ID and ComponentName)."""

    def norm(elem: ET.Element):
        attrs = {k: v for k, v in elem.attrib.items() if k not in ("ID", "ComponentName")}
        return (elem.tag, tuple(sorted(attrs.items())), [norm(c) for c in elem])

    return norm(root)


def _flatten(signature, depth: int = 0) -> list[str]:
    tag, attrs, children = signature
    line = "  " * depth + tag + "".join(f' {k}="{v}"' for k, v in attrs)
    return [line] + [row for child in children for row in _flatten(child, depth + 1)]


def element_diff(expected: ET.Element, got: ET.Element, limit: int = 120) -> str:
    """A unified per-element diff of two canonical trees."""
    lines = list(difflib.unified_diff(
        _flatten(canonical(expected)), _flatten(canonical(got)),
        "input.xml", "to_proteus_xml(build())", lineterm="",
    ))
    if len(lines) > limit:
        lines = lines[:limit] + [f"... ({len(lines) - limit} more diff lines)"]
    return "\n".join(lines)


# --- prepare: trim raw examples into acceptance inputs ---


def _top_level_spans(text: str) -> tuple[int, list[tuple[str, int, int]]]:
    """End offset of ``<PlantModel>`` and ``(tag, start, end)`` of each child."""
    depth = 0
    root_end = -1
    spans: list[tuple[str, int, int]] = []
    current: tuple[str, int] | None = None
    for match in re.finditer(r"<[^>]*>", text):
        token = match.group(0)
        if token.startswith(("<?", "<!")):
            continue
        name = re.match(r"</?\s*([\w.:-]+)", token).group(1)
        if token.startswith("</"):
            depth -= 1
            if depth == 1 and current is not None:
                spans.append((current[0], current[1], match.end()))
                current = None
        elif token.endswith("/>"):
            if depth == 1:
                spans.append((name, match.start(), match.end()))
        else:
            if depth == 0:
                root_end = match.end()
            elif depth == 1:
                current = (name, match.start())
            depth += 1
    return root_end, spans


def _writer_header() -> str:
    from dexpigen import to_proteus_xml
    from dexpigen.model import ConceptualModel

    xml = to_proteus_xml(ConceptualModel(dex_id="header"))
    return re.search(r"<PlantInformation\b.*?</PlantInformation>", xml, re.DOTALL).group(0)


def normalize(text: str) -> str:
    """Bring a trimmed file to the writer's document conventions.

    The model has no field for the ``PlantInformation`` header (the writer
    emits a fixed one) and writes top-level objects grouped by type, so the
    header is replaced with the writer's and the top-level children are
    stably reordered into the writer's order. Everything inside each top-level
    element is kept byte for byte.
    """
    root_end, spans = _top_level_spans(text)
    unknown = sorted({tag for tag, _, _ in spans} - set(WRITER_ORDER))
    if unknown:
        raise ValueError(f"top-level elements the writer cannot produce: {unknown}")
    header = _writer_header()
    children = [
        header if tag == "PlantInformation" else text[start:end]
        for tag, start, end in sorted(spans, key=lambda s: WRITER_ORDER[s[0]])
    ]
    return text[:root_end] + "".join(f"\n  {child}" for child in children) + "\n</PlantModel>\n"


def prepare(tasks: list[str]) -> int:
    sys.path.insert(0, str(ROOT / "examples"))
    from trim_dexpi_xml import trim
    from validate_dexpi import validate

    ok = True
    for task in tasks:
        source = RAW / TASKS[task]
        if not source.exists():
            print(f"{task}: raw example missing: {source}", file=sys.stderr)
            return 1
        target = ACCEPTANCE / task / "input.xml"
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            trimmed = Path(tmp) / "trimmed.xml"
            trim(str(source), str(trimmed))
            text = trimmed.read_text(encoding="utf-8")
        target.write_text(normalize(text), encoding="utf-8", newline="\n")
        ok = validate(str(target)) and ok
        print(f"{task}: wrote {target.relative_to(ROOT).as_posix()}")
    return 0 if ok else 1


# --- the checker ---


@dataclass
class Check:
    built: bool = False
    valid: bool = False
    exact: bool = False
    src_unmodified: bool | None = None
    error: str = ""
    diff: str = ""


def check_solution(solution: Path, input_xml: Path) -> Check:
    """Import ``build()`` from ``solution``, serialize, validate and compare."""
    result = Check()
    sys.path[:0] = [str(solution.parent), str(solution.parent / "examples"), str(ROOT / "examples")]
    try:
        from dexpigen import to_proteus_xml
        from dexpigen.model import ConceptualModel
        from validate_dexpi import validate

        spec = importlib.util.spec_from_file_location("acceptance_solution", solution)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        model = module.build()
        if not isinstance(model, ConceptualModel):
            result.error = f"build() returned {type(model).__name__}, not ConceptualModel"
            return result
        xml = to_proteus_xml(model)
        result.built = True
    except Exception as exc:  # the agent's code may fail in any way
        result.error = f"{type(exc).__name__}: {exc}"
        return result
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "got.xml"
        out.write_text(xml, encoding="utf-8")
        result.valid = validate(str(out))
    expected = ET.parse(input_xml).getroot()
    got = ET.fromstring(xml)
    result.exact = canonical(got) == canonical(expected)
    if not result.exact:
        result.diff = element_diff(expected, got)
    return result


def _check_in_subprocess(solution: Path, input_xml: Path) -> Check:
    """Run the checker in a fresh interpreter, isolated from the runner."""
    proc = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "check", str(solution), str(input_xml)],
        cwd=solution.parent, capture_output=True, text=True,
    )
    last = proc.stdout.strip().splitlines()[-1:] or [""]
    try:
        return Check(**json.loads(last[0]))
    except (json.JSONDecodeError, TypeError):
        return Check(error=f"checker crashed (exit {proc.returncode}): {proc.stderr[-2000:]}")


# --- sandbox and agent ---


def _git(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)


def make_sandbox(task: str) -> Path:
    """Export HEAD into a fresh git repo without the held-out material."""
    sandbox = Path(tempfile.mkdtemp(prefix=f"dexpigen-acceptance-{task}-"))
    archive = subprocess.run(["git", "archive", "--format=tar", "HEAD"], cwd=ROOT,
                             capture_output=True, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(sandbox, filter="data")
    for rel in SANDBOX_EXCLUDE:
        path = sandbox / rel
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()
    for rel in [*SANDBOX_EXCLUDE, "data/example_pids"]:
        assert not (sandbox / rel).exists(), rel
    shutil.copyfile(ACCEPTANCE / task / "input.xml", sandbox / "input.xml")
    _git("init", "-q", cwd=sandbox)
    _git("add", "-A", cwd=sandbox)
    _git("-c", "user.name=acceptance", "-c", "user.email=acceptance@localhost",
         "commit", "-q", "-m", "sandbox", cwd=sandbox)
    subprocess.run(["uv", "sync", "--quiet"], cwd=sandbox, check=True)
    return sandbox


def run_agent(sandbox: Path, model: str, max_budget_usd: float | None) -> dict:
    """Run headless Claude Code in ``sandbox``; return its JSON result."""
    command = [
        "claude", "-p", PROMPT, "--model", model, "--output-format", "json",
        "--safe-mode", "--no-session-persistence", "--permission-mode", "dontAsk",
        "--tools", "Bash", "Read", "Write", "Edit", "Glob", "Grep",
        "--allowedTools", *ALLOWED_TOOLS,
        "--disallowedTools", "WebFetch", "WebSearch",
    ]
    if max_budget_usd is not None:
        command += ["--max-budget-usd", str(max_budget_usd)]
    proc = subprocess.run(command, cwd=sandbox, capture_output=True, text=True)
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"is_error": True, "result": proc.stdout[-2000:] + proc.stderr[-2000:]}


@dataclass
class RunResult:
    task: str
    run: int
    check: Check
    sandbox: str = ""
    cost_usd: float | None = None
    agent_error: str = ""
    extra: dict = field(default_factory=dict)


def run(tasks: list[str], runs: int, model: str, dry_run: bool, keep: bool,
        max_budget_usd: float | None) -> int:
    dirty = _git("status", "--porcelain", "--untracked-files=no", "--", "README.md", "docs", "src", "examples",
                 "CONTEXT.md", cwd=ROOT).stdout.strip()
    if dirty:
        print("warning: uncommitted changes are not in the sandbox (it exports HEAD):\n" + dirty)
    results: list[RunResult] = []
    for task in tasks:
        for index in range(1, runs + 1):
            sandbox = make_sandbox(task)
            solution = sandbox / "solution.py"
            outcome = RunResult(task=task, run=index, check=Check())
            if dry_run:
                shutil.copyfile(ACCEPTANCE / task / "solution.py", solution)
            else:
                agent = run_agent(sandbox, model, max_budget_usd)
                outcome.cost_usd = agent.get("total_cost_usd")
                if agent.get("is_error"):
                    outcome.agent_error = str(agent.get("result", ""))[:500]
            if solution.exists():
                outcome.check = _check_in_subprocess(solution, sandbox / "input.xml")
            else:
                outcome.check.error = "no solution.py written"
            changed = _git("status", "--porcelain", "--", "src", cwd=sandbox).stdout.strip()
            outcome.check.src_unmodified = not changed
            if keep:
                outcome.sandbox = str(sandbox)
            else:
                shutil.rmtree(sandbox, ignore_errors=True)
            results.append(outcome)
            print(f"{task} run {index}: valid={outcome.check.valid} exact={outcome.check.exact} "
                  f"src_unmodified={outcome.check.src_unmodified} {outcome.check.error}")
    report, passed = write_report(results, tasks, runs, model, dry_run)
    print(f"report: {report.relative_to(ROOT).as_posix()}")
    return 0 if passed else 1


def task_passes(results: list[RunResult]) -> bool:
    """All runs schema-valid with ``src/`` untouched, and at least 2/3 exact."""
    ok = [r.check.valid and r.check.src_unmodified for r in results]
    exact = [r.check.exact and r.check.src_unmodified for r in results]
    return all(ok) and sum(exact) * 3 >= 2 * len(results)


def write_report(results: list[RunResult], tasks: list[str], runs: int, model: str,
                 dry_run: bool) -> tuple[Path, bool]:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    head = _git("rev-parse", "--short", "HEAD", cwd=ROOT).stdout.strip()
    REPORTS.mkdir(parents=True, exist_ok=True)
    path = REPORTS / f"{stamp}{'-dry' if dry_run else ''}.md"
    agent = "reference solution (dry run)" if dry_run else model
    lines = [
        f"# Docs acceptance {stamp}", "",
        f"- Commit: `{head}`", f"- Agent: {agent}", f"- Runs per task: {runs}", "",
        "| Task | Run | Valid | Exact | src unmodified | Cost (USD) | Error |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in results:
        cost = f"{r.cost_usd:.2f}" if r.cost_usd is not None else ""
        error = (r.check.error or r.agent_error).replace("|", "\\|").replace("\n", " ")[:200]
        lines.append(f"| {r.task} | {r.run} | {r.check.valid} | {r.check.exact} "
                     f"| {r.check.src_unmodified} | {cost} | {error} |")
    lines += ["", "## Verdict", ""]
    passed = True
    for task in tasks:
        verdict = task_passes([r for r in results if r.task == task])
        passed = passed and verdict
        lines.append(f"- {task}: {'PASS' if verdict else 'FAIL'}")
    diffs = [r for r in results if r.check.diff]
    if diffs:
        lines += ["", "## Diffs", ""]
        for r in diffs:
            lines += [f"### {r.task} run {r.run}", "", "```diff", r.check.diff, "```", ""]
    kept = [r for r in results if r.sandbox]
    if kept:
        lines += ["", "## Sandboxes", ""] + [f"- {r.task} run {r.run}: `{r.sandbox}`" for r in kept]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return path, passed


def verify(tasks: list[str]) -> int:
    ok = True
    for task in tasks:
        result = _check_in_subprocess(ACCEPTANCE / task / "solution.py", ACCEPTANCE / task / "input.xml")
        print(f"{task}: valid={result.valid} exact={result.exact} {result.error}")
        if result.diff:
            print(result.diff)
        ok = ok and result.valid and result.exact
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "verify", "run"):
        p = sub.add_parser(name)
        p.add_argument("--tasks", nargs="+", choices=sorted(TASKS), default=list(TASKS))
    run_parser = sub.choices["run"]
    run_parser.add_argument("--runs", type=int, default=RUNS)
    run_parser.add_argument("--model", default=MODEL)
    run_parser.add_argument("--dry-run", action="store_true",
                            help="use the reference solution instead of an agent")
    run_parser.add_argument("--keep", action="store_true", help="keep the sandboxes")
    run_parser.add_argument("--max-budget-usd", type=float, default=None,
                            help="per-run spending cap passed to claude -p")
    check = sub.add_parser("check", help="internal: check one solution, print JSON")
    check.add_argument("solution", type=Path)
    check.add_argument("input_xml", type=Path)
    args = parser.parse_args()

    if args.command == "prepare":
        return prepare(args.tasks)
    if args.command == "verify":
        return verify(args.tasks)
    if args.command == "check":
        result = check_solution(args.solution.resolve(), args.input_xml.resolve())
        print(json.dumps(asdict(result)))
        return 0
    return run(args.tasks, args.runs, args.model, args.dry_run, args.keep, args.max_budget_usd)


if __name__ == "__main__":
    sys.exit(main())
