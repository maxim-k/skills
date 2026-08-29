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
| [`toil-to-nextflow`](toil-to-nextflow/SKILL.md) | Convert a Toil pipeline to a modern Nextflow DSL2 pipeline: audit the orchestration boilerplate, extract the logic that survives, design the processes and DAG, modernise the language, rewire the caller. |
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
