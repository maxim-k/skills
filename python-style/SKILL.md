---
name: python-style
description: >
  Personal Python coding standard: minimalist architecture, explicit typing,
  reST docstrings, ASD-STE100 plain language, why-not-what comments,
  actionable error handling, pragmatic logging, never log-and-raise. Use
  whenever writing, editing, or reviewing Python code — new modules,
  functions, CLI tools, adding try/except blocks, adding logging, or when the
  user says "python style", "clean python", "lean code", "idiomatic python".
---

Apply this standard to Python code you write or edit. It governs architecture,
typing, docstrings, language, comments, error handling, and logging as one
coherent set of rules — don't apply only part of it.

## Architecture

- Write clean, modern, idiomatic Python (dataclasses/`__slots__` where they
  earn their keep, stdlib over reinvention).
- Minimalist by default: no interface with only one implementation, no config
  for a value that never changes, no layer with a single caller.
- Reach for an abstract base class only when there are genuinely multiple
  concrete implementations today — not for a hypothetical future one.
- If the code is a CLI or streams data through a pipe, keep it pipe-safe:
  handle `BrokenPipeError` (e.g. downstream `head`/`tail` closing early)
  instead of letting it crash with a traceback, and don't buffer output that
  the caller expects to stream.

## Dependencies and environments

Manage dependencies with `uv` against a standard `pyproject.toml`. Two tables,
one boundary:

- `[project].dependencies` — runtime only. Every package here ships to
  production.
- `[dependency-groups]` (PEP 735) — everything else: anything used to build,
  test, check or debug the project, but never at run time.

Split the groups by purpose, so one job installs only what it needs. Compose
them into an umbrella `dev` group, so `dev` stays the single name a human
types:

```toml
[dependency-groups]
test = [...]
lint = [...]
dev  = [{include-group = "test"}, {include-group = "lint"}]
```

Which tools go in which group is a per-project decision. The rule is the
split, not the package list.

- `uv sync` installs the `dev` group as well. `uv sync --no-dev` gives the
  production environment. `--only-group <name>` isolates one job.
- Commit `uv.lock`. Use `--frozen` where reproducibility matters: CI, Docker.
- Use `[project.optional-dependencies]` (extras) only for a feature that a
  *consumer* opts into (`pip install pkg[viz]`). Development tooling goes in a
  group, for three mechanical reasons:
  - Extras are published package metadata. Groups stay local.
  - An extra installs only after the project itself builds. A group installs
    on its own, so a lint or test stage needs no source code in the image.
  - Groups compose with `include-group`. Extras have no equivalent.

The `dockerfile-style` skill maps these groups onto image targets: `prod`
syncs with `--no-dev`, `dev` syncs the `dev` group on top.

## Typing

- Every function/method signature gets explicit type hints: parameters,
  return type (including `-> None`), and `self`/`cls` excluded as usual.
- Type module-level and class-level variables explicitly when the type isn't
  obvious from the right-hand side (`count: int = 0` where inference is
  ambiguous, not `x: int = 5` where it's redundant).
- Use the precise type (`Sequence[str]`, `Mapping[str, int]`, `X | None`),
  not `Any`, unless the value is genuinely dynamic.

## Docstrings: reST format

Every public module, class, and function/method gets a docstring in reST
(Sphinx) format:

```python
def load_config(config_path: Path) -> Config:
    """Load and validate the configuration file.

    :param config_path: Path to the configuration file.
    :type config_path: Path
    :returns: The parsed configuration.
    :rtype: Config
    :raises ValueError: If the file is missing or fails validation.
    """
```

Use `:param:`/`:type:` per parameter, `:returns:`/`:rtype:`, and `:raises:`
per exception type that can propagate out of the function. Skip `:type:`
only where the signature's type hint already makes it fully redundant to a
reader of the rendered docs.

## Plain language: ASD-STE100

All non-code text — docstrings, comments, error messages, log messages,
CLI help strings — follows ASD-STE100 (Simplified Technical English):

- One instruction or fact per sentence. Don't join two actions with "and" —
  write two sentences.
- Active voice, present tense: "The function opens the file", not "The file
  is opened by the function."
- Short sentences (aim for at most ~20 words) and short paragraphs (at most
  ~6 sentences).
- Use a word the same way every time (don't alternate "delete"/"remove" for
  the same action; pick one and keep it).
- No jargon, idioms, or slang. No noun strings — "the config file path", not
  "the config path file location string."
- Spell out the actor and the action: avoid vague pronouns ("it", "this")
  when the antecedent isn't the immediately preceding noun.

This applies to `Error handling` and `Logging` below: every message must
also be Simplified-Technical-English-compliant.

ASD-STE100 governs text **inside code** only — docstrings, comments, error
messages, log messages, CLI help. Standalone Markdown prose (README, docs,
guides) goes through the `vale-google-style` skill instead; the two standards
disagree on contractions and person, so don't apply both to one file.

## Comments: why, never what

- Never translate code to English. Assume the reader knows Python and the
  shell (don't explain `with open(...)` or a `subprocess.run` call).
- Write a comment only when the code encodes something non-obvious: a hidden
  constraint, a workaround for a specific bug, an edge case a reader would
  otherwise "fix" by mistake. If removing the comment wouldn't confuse a
  future reader, don't write it.

## Error handling

- Use standard `try/except/raise` with built-in exception types
  (`ValueError`, `RuntimeError`, `FileNotFoundError`, ...). Don't create empty
  custom exception subclasses that add no fields or behavior.
- Every raised error message must name the specific value/variable that
  caused the failure and give a concrete troubleshooting hint — never a bare
  `raise` with no context, and never a generic "Failed" or "Something went
  wrong" message.
  - Good: `raise ValueError(f"Config file '{config_path}' is missing. Create it in the project root.")`
  - Bad: `raise ValueError("Failed to load config")`

## Logging

- Log structural breadcrumbs, not a step-by-step trace: major milestones,
  network/IO calls, and data shapes (counts, sizes) — enough to diagnose a
  failure without a debugger attached.
  - Good: `logger.info("Fetching remote metrics")` / `logger.info("Processed %d records", len(records))`
  - Bad: logging every loop iteration or every assignment.

## Never log-and-raise

Logging an error and then raising an exception with the same information
double-reports the same failure and bloats output. Pick one:

- If this function cannot recover, **raise** an informative exception (per
  the Error handling rule above) and let the caller decide whether to log it.
- Only **log** an error at the point where it is actually caught, handled,
  and execution continues — never at the point where you're about to
  propagate it upward.
