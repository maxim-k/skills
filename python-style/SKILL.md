---
name: python-style
description: >
  Personal Python coding standard: minimalist architecture, explicit typing,
  PEP 8 naming, PEP 257 docstrings in reST, ASD-STE100 plain language,
  why-not-what comments, actionable error handling, pragmatic logging, never
  log-and-raise. Use whenever writing, editing, or reviewing Python code — new
  modules, functions, CLI tools, adding try/except blocks, adding logging, or
  when the user says "python style", "clean python", "lean code", "idiomatic
  python".
---

Apply this standard to Python code you write or edit. It governs architecture,
typing, naming, docstrings, language, comments, error handling, and logging.

These rules serve readability, which is the reason PEP 8 gives for having them:
"code is read much more often than it is written." They are guidelines, not a
mandate to apply at full weight everywhere. PEP 8's own opening applies to this
document too — "know when to be inconsistent — sometimes style guide
recommendations just aren't applicable" — and the first reason it lists is
"when applying the guideline would make the code less readable." A
self-explanatory one-line helper carrying a five-line docstring is that
failure. Judge each rule against the code in front of you.

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

## Naming and layout

Standard PEP 8 conventions. The docstring rules below depend on the underscore
one, so it is not optional here:

- `snake_case` for functions, methods, variables and modules.
- `CapWords` for classes. `UPPER_CASE_WITH_UNDERSCORES` for constants.
- Exceptions are classes, so `CapWords`, with an `Error` suffix where the name
  denotes a failure (`ConfigError`).
- A single leading underscore marks a name as internal. That underscore is the
  line the docstring rule uses: `_helper` is non-public.
- Declare the public surface with `__all__` in a module meant to be imported
  from.

Line length: 79 characters for code, 72 for docstrings and comments. PEP 8
allows a project to raise code to 99, "provided that comments and docstrings
are still wrapped at 72 characters." Follow whatever a project already
configures for ruff or black; where nothing is configured, use these numbers.

## Docstrings

The house format is reST (Sphinx) fields. How much docstring a function gets is
set by PEP 257 and PEP 8, not by habit: the weight is proportional to what the
signature does not already say.

### Where a docstring is required

Public modules, functions, classes and methods, including `__init__`.

A non-public name (single leading underscore) does not need one. PEP 8:
"Docstrings are not necessary for non-public methods, but you should have a
comment that describes what the method does. This comment should appear after
the `def` line." Write that comment only where the name and signature don't
already carry the meaning — see `Comments` below.

### Default: one line

"One-liners are for really obvious cases." Most functions are that case, so a
one-line docstring is the default and going past it needs a reason.

```python
def _to_seconds(ms: int) -> float:
    """Convert milliseconds to seconds."""
```

- Closing `"""` on the same line as the opening quotes.
- No blank line before or after it.
- A phrase ending in a period.
- Imperative mood. PEP 257: a docstring "prescribes the function or method's
  effect as a command ("Do this", "Return that"), not as a description; e.g.
  don't write "Returns the pathname ..."." Write `Convert milliseconds to
  seconds.` — not `Converts ...`, and not `This function converts ...`.

### Never restate the signature

PEP 257: "The one-line docstring should NOT be a "signature" reiterating the
function/method parameters (which can be obtained by introspection)."

Every signature here carries type hints (see `Typing`), so the hints are the
introspectable part. Therefore:

- **Never write `:type:` or `:rtype:`.** The annotation is the type, and Sphinx
  renders it from the annotation.
- **Never write a `:param:` that only repeats the name and the hint.**
  `:param path: The path.` against `path: Path` adds nothing. Leave it out.
- **Never write a `:returns:` that only repeats the summary line.**

### Expand only for what the signature can't say

Add a field when a reader who has already read the signature would still be
missing something:

- `:param x:` — units, a constraint, a default behaviour, the meaning of a
  sentinel value, or which of several readings applies.
- `:returns:` — when the return value needs more than the summary line gives.
- `:raises X:` — for an exception the function raises deliberately, as part of
  its contract. Not for every exception that could propagate from below.

```python
def load_config(path: Path) -> Config:
    """Load and validate the configuration file.

    :param path: Location of the TOML file. A relative path resolves
        against the project root, not the working directory.
    :raises ValueError: If a required key is missing.
    """
```

`path: Path` already says it is a path, so the `:param:` earns its place on the
resolution rule alone. There is no `:type:`, no `:rtype:`, and no `:returns:`
repeating the summary.

### Multi-line mechanics

- Summary line, blank line, then the elaboration.
- Closing `"""` on a line by itself.
- A blank line after every class docstring.
- A module docstring lists what the module exports, one line for each. A
  package docstring (in `__init__.py`) lists the modules and subpackages.
- A script's module docstring doubles as its usage message: what the script
  does, the command line syntax, and the environment variables and files it
  uses.

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

One carve-out: a docstring summary line takes the imperative mood that PEP 257
requires ("Open the file."), not the actor-plus-verb form of the second rule
above. Every other rule in this list still applies to that line.

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
- One exception, and it comes from PEP 8: a non-public function may carry a
  short what-comment after the `def` line in place of a docstring. That is the
  only sanctioned what-comment. It is still unnecessary when the name and the
  signature already say it — `_to_seconds(ms: int) -> float` needs nothing.

Mechanics:

- Complete sentences. Capitalize the first word, unless it is an identifier
  that begins with a lowercase letter — never alter the case of an identifier.
- Block comments sit at the indentation of the code they describe. Each line
  starts with `#` and one space. Separate paragraphs inside one block with a
  line holding a bare `#`.
- Inline comments sparingly, at least two spaces clear of the statement.
- "Comments that contradict the code are worse than no comments." A comment
  that no longer matches the code gets updated or deleted in the same edit.

## Error handling

- Use standard `try/except/raise` with built-in exception types
  (`ValueError`, `RuntimeError`, `FileNotFoundError`, ...). Define a custom
  exception only when a caller needs to catch that failure specifically: PEP 8
  builds a hierarchy around "the distinctions code catching the exceptions
  needs to make". An exception that nobody catches by type earns nothing — use
  a built-in.
- Derive from `Exception`, never from `BaseException`.
- Catch specific exceptions. Never write a bare `except:` — it also catches
  `SystemExit` and `KeyboardInterrupt`, so Ctrl-C stops working. Use
  `except Exception:` only where the intent really is every program error.
- Chain when you replace an exception. `raise X from Y` keeps the original
  traceback. Use `raise X from None` only to hide an inner error that tells the
  reader nothing, and then carry its useful details into the new message.
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
