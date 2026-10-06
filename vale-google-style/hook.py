"""Run Vale on a Markdown file that Claude Code just edited.

Claude Code runs this script as a PostToolUse hook after Edit and Write.
The script reads the hook JSON on standard input and lints the file with
Vale. Errors and warnings go back to Claude as a block decision, which
Claude must fix. Suggestions alone go back as context, which Claude reports
to the user.

The script skips notes written for Claude rather than for people: plans,
memory, SKILL.md, CLAUDE.md and MEMORY.md. It exits 0 when Vale is missing.

Usage:
  python3 hook.py < hook-input.json
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

CLAUDE_HOME = Path.home() / ".claude"
SKIPPED_DIRS = (CLAUDE_HOME / "plans", CLAUDE_HOME / "projects")
SKIPPED_NAMES = {"SKILL.md", "CLAUDE.md", "MEMORY.md"}


def _skipped(path: Path) -> bool:
    if path.suffix != ".md" or not path.is_file() or path.name in SKIPPED_NAMES:
        return True
    resolved = path.resolve()
    return any(resolved.is_relative_to(d.resolve()) for d in SKIPPED_DIRS)


def _line(alert: dict) -> str:
    return (f"L{alert['Line']} {alert['Check']}: {alert['Message']} "
            f"(match: \"{alert['Match']}\")")


def main() -> int:
    data = json.load(sys.stdin)
    path = Path(data.get("tool_input", {}).get("file_path", ""))
    vale = shutil.which("vale") or "/opt/homebrew/bin/vale"
    if _skipped(path) or not Path(vale).is_file():
        return 0
    # Run from the file's directory so that a project .vale.ini wins over
    # ~/.vale.ini.
    result = subprocess.run([vale, "--output=JSON", "--no-exit", path.name],
                            cwd=path.parent, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"vale failed on {path}: {result.stderr.strip()}", file=sys.stderr)
        return 1
    alerts = [a for file_alerts in json.loads(result.stdout or "{}").values()
              for a in file_alerts]
    fixes = [_line(a) for a in alerts if a["Severity"] in ("error", "warning")]
    suggestions = [_line(a) for a in alerts if a["Severity"] == "suggestion"]
    if not fixes and not suggestions:
        return 0
    text = f"Vale findings in {path} (vale-google-style)."
    if fixes:
        text += ("\n\nFix these. Locate each one by its match, not its line:\n"
                 + "\n".join(fixes))
    if suggestions:
        text += ("\n\nSuggestions. Report these to the user, do not rewrite:\n"
                 + "\n".join(suggestions))
    if fixes:
        output = {"decision": "block", "reason": text}
    else:
        output = {"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                         "additionalContext": text}}
    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
