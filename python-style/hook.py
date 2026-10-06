"""Run ruff and ty on a Python file that Claude Code just edited.

Claude Code runs this script as a PostToolUse hook after Edit and Write.
The script reads the hook JSON on standard input. It formats the file,
applies the safe lint fixes, and type-checks it. When findings remain, it
exits with code 2 and writes them to standard error, which Claude reads.

The script skips a tool when the project already configures a tool for the
same job (black, flake8, pylint, mypy). It exits 0 when uv is missing.

Usage:
  python3 hook.py < hook-input.json
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

CONFIG_FILES = ("pyproject.toml", "setup.cfg", "tox.ini", ".flake8", ".pylintrc",
                "pylintrc", "mypy.ini", ".mypy.ini")
FORMATTER_MARKERS = ("[tool.black]",)
LINTER_MARKERS = ("[flake8]", "[tool.pylint", "[pylint", "[MASTER]")
TYPE_CHECKER_MARKERS = ("[mypy]", "[tool.mypy]")


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


def main() -> int:
    data = json.load(sys.stdin)
    path = Path(data.get("tool_input", {}).get("file_path", ""))
    if path.suffix != ".py" or not path.is_file():
        return 0
    uv = shutil.which("uv") or str(Path.home() / ".local/bin/uv")
    if not Path(uv).is_file():
        return 0
    root = _project_root(path)
    file = str(path)
    commands = []
    if not _uses(root, FORMATTER_MARKERS):
        commands.append(["ruff", "format", "--quiet", file])
    if not _uses(root, LINTER_MARKERS, (".flake8", ".pylintrc", "pylintrc")):
        # F401 is reported, never fixed: Claude often adds an import one edit
        # before the code that uses it, and --fix would delete it in between.
        commands.append(["ruff", "check", "--fix", "--unfixable", "F401",
                         "--output-format", "concise", "--quiet", file])
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
        if result.returncode != 0:
            findings.append(f"$ {' '.join(command[:2])}\n"
                            f"{(result.stdout + result.stderr).strip()}")
    if not findings:
        return 0
    print(f"python-style: findings in {file}. Fix the ones your edit "
          "introduced. Leave findings in code you did not change.\n\n"
          + "\n\n".join(findings), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
