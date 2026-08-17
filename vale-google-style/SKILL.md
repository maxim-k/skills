---
name: vale-google-style
description: >
  Lint technical prose against the Google Developer Documentation Style Guide
  with Vale, then fix the findings. Use after writing or editing any Markdown
  documentation — README, docs page, guide, changelog, design doc, release
  notes — and when the user says "vale", "lint this doc", "check the style",
  "google style guide", or asks for style-checked prose. Markdown and prose
  files only; not Python source.
---

Prose you generate is not finished until Vale passes on it. Run the loop below
on the Markdown file, don't hand over an unlinted draft.

## Setup (idempotent — check, create only what's missing)

1. `command -v vale`. If absent, install it: `brew install vale`. Ask the user
   before installing.
2. `~/.vale.ini`. If absent, create it. `StylesPath` must be an absolute path,
   Vale does not expand `~`:

   ```ini
   StylesPath = /Users/mkuleshov/.vale/styles
   MinAlertLevel = suggestion
   Vocab = Base
   Packages = Google

   [*.md]
   BasedOnStyles = Vale, Google
   ```
3. `~/.vale/styles/Google/`. If absent, run `vale sync` to download the
   official Google package.
4. `~/.vale/styles/config/vocabularies/Base/accept.txt` and `reject.txt`. If
   absent, create both (empty is fine). `Vocab = Base` errors without them.

A project with its own `.vale.ini` wins — Vale searches upward from the file
before falling back to `~/.vale.ini`. Leave a project config alone.

## Lint loop

1. Write the draft to its real destination path. Don't lint a temp copy: the
   fixes have to land in the file the user keeps. No destination yet? Use the
   session scratchpad.
2. Run:

   ```bash
   vale --output=JSON --no-exit <file>
   ```

   `--no-exit` matters: Vale exits 1 whenever it finds alerts, which otherwise
   reads as a crashed command. Exit code 2 is a real runtime or config error —
   report it and stop, don't parse the output.
3. Output is one object keyed by file path, each value an array of alerts with
   `Check`, `Message`, `Severity`, `Line`, `Span`, `Match`. `{}` or an empty
   array means the file passes. Say so and stop.
4. Fix every `error` and `warning`. **Locate each one by its `Match` string
   with Edit, never by `Line`** — line numbers go stale the moment an earlier
   edit changes the text. `Message` tells you the required change; use `Span`
   only to disambiguate a `Match` that repeats on one line.
5. Re-lint. **Two fix passes maximum**, then report what's left. Don't grind
   against the linter.
6. Report `suggestion`-level alerts instead of rewriting them: one line each,
   `<Check> (line <N>): <Message>`. Let the user decide.
7. `Vale.Spelling` on a real technical term (tool name, API, domain jargon)
   is a false positive — it fires on ordinary jargon like `config`. Append the term to
   `~/.vale/styles/config/vocabularies/Base/accept.txt` and re-lint. Never
   rename a correct term to satisfy a spell checker.
8. Ignore any alert whose `Match` sits inside a fenced code block. Vale skips
   fences in Markdown, but inline code and front matter can still leak through.

## Limits — state these, don't paper over them

- Vale checks style, not correctness. It will not catch a wrong fact, a broken
  command, or a bad code sample.
- `Google.Passive`, `Google.WordList` and similar checks are regex heuristics.
  A flagged sentence is sometimes right as written — say that rather than
  mangling it into compliance.
- Only `[*.md]` is configured. Other formats (`.rst`, `.txt`) need their own
  `.vale.ini` section; add one when a file needs it.
- Never run this on Python source. `python-style` governs text inside code
  (docstrings, comments, error and log messages) under ASD-STE100, which
  conflicts with Google style on contractions and person.
