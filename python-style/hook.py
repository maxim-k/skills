"""Run ruff and ty on the lines of a Python file that Claude Code just edited.

Claude Code runs this script as a PostToolUse hook after Edit and Write.
The script reads the hook JSON on standard input. It formats only the lines
the edit changed, then lint- and type-checks the file and keeps the findings
on those lines. When findings remain, it exits with code 2 and writes them to
standard error, which Claude reads. It never fixes or formats other lines, so
an edit in a project with a different style does not rewrite the whole file.

The script skips a check when the project already configures a tool for the
same job (flake8, pylint, mypy). It exits 0 when uv is missing.

Usage:
  python3 hook.py < hook-input.json
  python3 hook.py --selfcheck
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CONFIG_FILES = ("pyproject.toml", "setup.cfg", "tox.ini", ".flake8", ".pylintrc",
                "pylintrc", "mypy.ini", ".mypy.ini")
LINTER_MARKERS = ("[flake8]", "[tool.pylint", "[pylint", "[MASTER]")
TYPE_CHECKER_MARKERS = ("[mypy]", "[tool.mypy]")
FINDING_RE = re.compile(r"^.*?:(\d+):\d+: ")


def _project_root(path: Path) -> Path:
    # The nearest ancestor with pyproject.toml, else the file's directory.
    for parent in path.parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    return path.parent


def _uses(root: Path, markers: tuple[str, ...], files: tuple[str, ...] = ()) -> bool:
    # True when the project configures a tool that has one of the markers.
    if any((root / name).is_file() for name in files):
        return True
    for name in CONFIG_FILES:
        config = root / name
        if config.is_file() and any(m in config.read_text(errors="ignore")
                                    for m in markers):
            return True
    return False


def _changed_ranges(response: dict, path: Path) -> list[tuple[int, int]]:
    """Return the inclusive line ranges that the edit added or replaced."""
    if response.get("type") == "create":
        return [(1, max(1, len(path.read_text().splitlines())))]
    changed = []
    for hunk in response.get("structuredPatch") or []:
        line = hunk["newStart"]
        for text in hunk["lines"]:
            if text.startswith("+"):
                changed.append(line)
            if not text.startswith("-"):
                line += 1
    ranges: list[tuple[int, int]] = []
    for line in sorted(set(changed)):
        if ranges and line == ranges[-1][1] + 1:
            ranges[-1] = (ranges[-1][0], line)
        else:
            ranges.append((line, line))
    return ranges


def _format(
    uv: str, root: Path, path: Path, ranges: list[tuple[int, int]]
) -> list[tuple[int, int]]:
    # Bottom-up, so a range that grows or shrinks moves only ranges below it,
    # which are already formatted. Returns the ranges after formatting.
    ranges = list(ranges)
    for i in reversed(range(len(ranges))):
        start, end = ranges[i]
        before = len(path.read_text().splitlines())
        subprocess.run(
            [
                uv,
                "tool",
                "run",
                "ruff",
                "format",
                "--quiet",
                f"--range={start}-{end + 1}",
                str(path),
            ],
            cwd=root,
            capture_output=True,
            check=False,
        )
        delta = len(path.read_text().splitlines()) - before
        ranges[i] = (start, max(start, end + delta))
        ranges[i + 1 :] = [(s + delta, e + delta) for s, e in ranges[i + 1 :]]
    return ranges


def check(data: dict) -> str:
    """Format the edited lines and return the findings on them."""
    path = Path(data.get("tool_input", {}).get("file_path", ""))
    if path.suffix != ".py" or not path.is_file():
        return ""
    uv = shutil.which("uv") or str(Path.home() / ".local/bin/uv")
    if not Path(uv).is_file():
        return ""
    ranges = _changed_ranges(data.get("tool_response") or {}, path)
    if not ranges:
        return ""
    root = _project_root(path)
    ranges = _format(uv, root, path, ranges)

    file = str(path)
    commands = []
    if not _uses(root, LINTER_MARKERS, (".flake8", ".pylintrc", "pylintrc")):
        commands.append(["ruff", "check", "--output-format", "concise", file])
    if not _uses(root, TYPE_CHECKER_MARKERS, ("mypy.ini", ".mypy.ini")):
        ty = ["ty", "check", "--output-format", "concise", file]
        if not (root / ".venv").is_dir() and "VIRTUAL_ENV" not in os.environ:
            # Without an environment every third-party import is unresolved.
            ty[2:2] = ["--ignore", "unresolved-import"]
        commands.append(ty)

    findings = []
    for command in commands:
        result = subprocess.run([uv, "tool", "run", *command], cwd=root,
                                capture_output=True, text=True)
        mine = [
            line
            for line in (result.stdout + result.stderr).splitlines()
            if (m := FINDING_RE.match(line))
            and any(s <= int(m.group(1)) <= e for s, e in ranges)
        ]
        if mine:
            findings.append(f"$ {' '.join(command[:2])}\n" + "\n".join(mine))
    if not findings:
        return ""
    return (
        f"python-style: findings on the lines you changed in {file}.\n\n"
        + "\n\n".join(findings)
    )


def _selfcheck() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "mod.py"
        original = "import os\nx  =  'a'\n\ndef f():\n    return 1\n\ny  =  'b'\n"
        edited = original.replace(
            "    return 1\n", "    z  =  'c'\n    return undefined\n"
        )
        path.write_text(edited)
        patch = [
            {
                "newStart": 4,
                "lines": [
                    " def f():",
                    "-    return 1",
                    "+    z  =  'c'",
                    "+    return undefined",
                    "",
                ],
            }
        ]
        message = check(
            {
                "tool_input": {"file_path": str(path)},
                "tool_response": {"structuredPatch": patch},
            }
        )
        text = path.read_text()
        assert '    z = "c"\n' in text, text
        assert "x  =  'a'" in text and "y  =  'b'" in text, text
        assert ":6:" in message and "undefined" in message, message
        assert "F401" not in message, message

        path.write_text(original)
        check(
            {
                "tool_input": {"file_path": str(path)},
                "tool_response": {"type": "create"},
            }
        )
        assert 'x = "a"' in path.read_text(), path.read_text()
    print("selfcheck passed")


def main() -> int:
    if sys.argv[1:] == ["--selfcheck"]:
        _selfcheck()
        return 0
    message = check(json.load(sys.stdin))
    if not message:
        return 0
    print(message, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
