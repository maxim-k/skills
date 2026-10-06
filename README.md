# Claude Code skills

Personal global skills for [Claude Code](https://claude.com/claude-code), backed
up from `~/.claude/skills`.

## Skills

| Skill | What it does |
| --- | --- |
| [`conventional-commit`](conventional-commit/SKILL.md) | Single-line Conventional Commits, scope taken from the repo's `SCOPES.md`. |
| [`dockerfile-style`](dockerfile-style/SKILL.md) | Multi-stage Dockerfiles with dev and prod targets and BuildKit cache mounts for apt, uv, mamba, and ccache. |
| [`information-design`](information-design/SKILL.md) | Layout and information-density rules from Ruder and Tufte, with the standing rule that no visual claim ships without a check. |
| [`isabl-app`](isabl-app/SKILL.md) | Scaffold an Isabl app that wraps a bioinformatics tool, plus a static self-check for faults that otherwise only surface on HPC. |
| [`jupyter-notebook`](jupyter-notebook/SKILL.md) | Analytical notebook standard: plot style, small multiples, output-noise cleanup, two-pass dev-then-prod authoring. |
| [`python-style`](python-style/SKILL.md) | Minimalist Python: explicit typing, PEP 8 naming, PEP 257 docstrings in reST sized to what the signature does not say, plain language, actionable error handling, never log-and-raise. |
| [`system-diagram`](system-diagram/SKILL.md) | Mermaid diagrams of real systems: a node grammar borrowed from UML, a validator that enforces it, one hop per turn. |
| [`toil-to-nextflow`](toil-to-nextflow/SKILL.md) | Convert a Toil pipeline to a modern Nextflow DSL2 pipeline: audit the orchestration boilerplate, extract the logic that survives, design the processes and DAG, modernize the language, rewire the caller. |
| [`vale-google-style`](vale-google-style/SKILL.md) | Lint Markdown prose against the Google developer documentation style guide with Vale, then fix the findings. |

## Install

Clone into the Claude Code global skills directory:

```sh
git clone git@github.com:maxim-k/skills.git ~/.claude/skills
```

If `~/.claude/skills` already has content, clone elsewhere and copy the skill
directories you want.

Claude Code loads each skill from its `SKILL.md` and invokes it automatically
when the description matches the task. To invoke one by hand, type `/<skill-name>`.

## Hooks

A skill runs only when Claude chooses to load it, so its mechanical checks live
in hooks that Claude Code runs on every matching tool call. The skill keeps the
judgment. The hook does the checking.

| Hook | Runs | Does |
| --- | --- | --- |
| [`conventional-commit/hook.py`](conventional-commit/hook.py) | before `git commit` | Blocks a message that breaks the one-line format or uses a scope missing from `SCOPES.md`. |
| [`python-style/hook.py`](python-style/hook.py) | after a `.py` edit | Runs `ruff format`, `ruff check --fix` and `ty check` on the file through `uv`. |
| [`vale-google-style/hook.py`](vale-google-style/hook.py) | after a `.md` edit | Runs Vale and sends the findings back to Claude. |

Register them in `~/.claude/settings.json`:

```json
{
  "attribution": {"commit": "", "pr": ""},
  "hooks": {
    "PreToolUse": [{"matcher": "Bash", "hooks": [
      {"type": "command", "if": "Bash(git *)",
       "command": "python3 ~/.claude/skills/conventional-commit/hook.py"}]}],
    "PostToolUse": [{"matcher": "Edit|Write", "hooks": [
      {"type": "command", "timeout": 120,
       "command": "python3 ~/.claude/skills/python-style/hook.py"},
      {"type": "command",
       "command": "python3 ~/.claude/skills/vale-google-style/hook.py"}]}]
  }
}
```

The empty `attribution` stops Claude Code from adding a `Co-Authored-By`
trailer, which the commit hook would otherwise reject. Run
`python3 conventional-commit/hook.py --selfcheck` after changing that hook.
