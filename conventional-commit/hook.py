"""Block a git commit whose message breaks the conventional-commit standard.

Claude Code runs this script as a PreToolUse hook on Bash commands. The
script reads the hook JSON on standard input. When the command is a
``git commit`` with an invalid message, it prints a deny decision that
names each fault.

Usage:
  python3 hook.py < hook-input.json
  python3 hook.py --selfcheck
"""

from __future__ import annotations

import json
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

TYPES = ("feat", "fix", "docs", "style", "refactor", "perf", "test", "chore",
         "ci", "build")
HEADER_RE = re.compile(
    rf"^(?:{'|'.join(TYPES)})(?:\((?P<scope>[^)]*)\))?!?: (?P<summary>\S.*)$"
)
HEREDOC_RE = re.compile(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n(.*?)\n\s*\2\s*$",
                        re.S | re.M)
SCOPE_ITEM_RE = re.compile(r"^\s*[-*]\s+`?([\w.-]+)`?\s*:", re.M)
SEPARATORS = {"&&", "||", ";", "|", "&", "(", ")"}
GIT_OPTS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}


def _heredoc_body(text: str) -> str | None:
    match = HEREDOC_RE.search(text)
    return match.group(3) if match else None


def _commit_args(command: str, cwd: Path) -> tuple[list[str], Path] | None:
    # Return the arguments of the first `git commit` and the directory git
    # runs in. Return None when the command has no commit.
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    tokens = list(lexer)
    for start, token in enumerate(tokens):
        if token != "git":
            continue
        workdir, i = cwd, start + 1
        while i < len(tokens) and tokens[i].startswith("-"):
            if tokens[i] == "-C" and i + 1 < len(tokens):
                workdir = cwd / tokens[i + 1]
            i += 2 if tokens[i] in GIT_OPTS_WITH_VALUE else 1
        if i < len(tokens) and tokens[i] == "commit":
            end = i + 1
            while end < len(tokens) and tokens[end] not in SEPARATORS:
                end += 1
            return tokens[i + 1:end], workdir
    return None


def _message(args: list[str], command: str, workdir: Path) -> tuple[str | None, list[str]]:
    # Rebuild the message the way git does: each -m is one paragraph.
    paragraphs, faults = [], []
    i = 0
    while i < len(args):
        arg, value = args[i], None
        if arg in ("-m", "--message", "-F", "--file", "--trailer"):
            value = args[i + 1] if i + 1 < len(args) else ""
            i += 1
        elif arg.startswith(("--message=", "--file=", "--trailer=")):
            arg, value = arg.split("=", 1)
        elif arg.startswith("-m") and len(arg) > 2:
            arg, value = "-m", arg[2:]
        i += 1
        if value is None:
            continue
        if arg == "--trailer":
            faults.append(f"--trailer adds a trailer ({value}); "
                          "the message is one line with nothing after it.")
        elif arg in ("-m", "--message"):
            paragraphs.append(_heredoc_body(value) or value)
        elif value == "-":
            paragraphs.append(_heredoc_body(command) or "")
        else:
            path = workdir / value
            if path.is_file():
                paragraphs.append(path.read_text())
    if not paragraphs:
        return None, faults
    return "\n\n".join(p.strip() for p in paragraphs), faults


def _scopes(workdir: Path) -> set[str] | None:
    # Read the scope vocabulary from SCOPES.md at the repository root.
    result = subprocess.run(
        ["git", "-C", str(workdir), "rev-parse", "--show-toplevel"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return None
    scopes_file = Path(result.stdout.strip()) / "SCOPES.md"
    if not scopes_file.is_file():
        return None
    return set(SCOPE_ITEM_RE.findall(scopes_file.read_text()))


def check(command: str, cwd: Path) -> list[str]:
    """Return the faults in the commit message of a shell command.

    :returns: One sentence per fault. An empty list means the command is
        not a commit, the message comes from an editor, or the message is
        valid.
    """
    try:
        found = _commit_args(command, cwd)
    except ValueError:
        return []  # Unbalanced quotes: let git and the shell report it.
    if found is None:
        return []
    args, workdir = found
    message, faults = _message(args, command, workdir)
    if message is None:
        return faults
    lines = message.strip().splitlines()
    if len(lines) > 1:
        faults.append(f"The message has {len(lines)} lines. Write exactly one "
                      "line: no body, no blank line, no trailer such as "
                      "Co-Authored-By.")
    header = lines[0] if lines else ""
    match = HEADER_RE.match(header)
    if not match:
        faults.append(f"'{header}' does not match '<type>[(scope)]: <summary>'. "
                      f"Use one of these types: {', '.join(TYPES)}.")
        return faults
    summary, scope = match["summary"], match["scope"]
    if summary[0].isupper():
        faults.append("The summary starts with a capital letter. "
                      "Start it in lowercase.")
    if summary.endswith("."):
        faults.append("The summary ends with a period. Remove the period.")
    if scope is None:
        return faults
    if not scope or re.search(r"[,\s/]", scope):
        faults.append(f"The scope '({scope})' is not one scope. A commit that "
                      "crosses scopes has no scope: remove it, or split the "
                      "commit.")
        return faults
    scopes = _scopes(workdir)
    if scopes is None:
        faults.append("The repository root has no SCOPES.md. Create it as the "
                      "conventional-commit skill describes, or remove the "
                      "scope.")
    elif scope not in scopes:
        faults.append(f"The scope '{scope}' is not in SCOPES.md. Use one of: "
                      f"{', '.join(sorted(scopes))}. Or remove the scope.")
    return faults


def _selfcheck() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        (repo / "SCOPES.md").write_text("- `cli`: the CLI.\n- api: the API.\n")
        bad = {
            'git commit -m "Fix thing"': "does not match",
            'git commit -m "fix: Thing"': "capital",
            'git commit -m "fix: thing."': "period",
            'git commit -m "fix(db): thing"': "not in SCOPES.md",
            'git commit -m "fix(cli, api): thing"': "not one scope",
            'git commit -m "fix: thing" -m "Body."': "3 lines",
            'git add . && git commit -m "$(cat <<\'EOF\'\nfix: thing\n\n'
            'Co-Authored-By: X <x@y>\nEOF\n)"': "3 lines",
            'git commit -F - <<EOF\nfix: thing\nbody\nEOF': "2 lines",
            'git commit --trailer "Signed-off-by: X" -m "fix: thing"': "trailer",
        }
        for command, fault in bad.items():
            faults = check(command, repo)
            assert any(fault in f for f in faults), (command, faults)
        good = [
            'git commit -m "feat(cli): add a flag"',
            "git commit -m 'feat(api)!: drop v1'",
            f'git -C {repo} commit -am "docs: fix typo in readme"',
            'git commit -m "$(cat <<\'EOF\'\nfix: thing\nEOF\n)" && git push',
            "git commit --amend --no-edit",
            "git status && git log -1",
            'echo "git commit -m nonsense"',
        ]
        for command in good:
            assert check(command, repo) == [], (command, check(command, repo))
        no_scopes = repo / "sub"
        subprocess.run(["git", "init", "-q", str(no_scopes)], check=True)
        assert "no SCOPES.md" in check('git commit -m "fix(x): y"', no_scopes)[0]
    print("selfcheck passed")


def main() -> int:
    if sys.argv[1:] == ["--selfcheck"]:
        _selfcheck()
        return 0
    data = json.load(sys.stdin)
    command = data.get("tool_input", {}).get("command", "")
    faults = check(command, Path(data.get("cwd", ".")))
    if faults:
        reason = ("Commit blocked by the conventional-commit hook:\n- "
                  + "\n- ".join(faults))
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
