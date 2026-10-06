---
name: vale-google-style
description: >
  Fix the findings that Vale reports on Markdown against the Google Developer
  Documentation Style Guide. A hook lints every Markdown file after it is
  edited; use this skill to act on its findings — README, docs page, guide,
  changelog, design doc, release notes — and when the user says "vale", "lint
  this doc", "check the style", "google style guide", or asks for
  style-checked prose. Markdown and prose files only; not Python source.
---

`hook.py` in this directory runs `vale --output=JSON --no-exit` after every Edit
or Write of a `.md` file. It skips notes written for Claude rather than people:
`~/.claude/plans/`, `~/.claude/projects/` (memory), and any `SKILL.md`,
`CLAUDE.md` or `MEMORY.md`. Errors and warnings come back as a block you must
fix; suggestions come back as context. The hook is silent when Vale is not
installed — run the setup below once.

## Setup (idempotent — check, create only what's missing)

1. `command -v vale`. If absent, install it: `brew install vale`. Ask the user
   before installing.
2. `~/.vale.ini`. Create it if absent. If it exists, check it against the
   content below and add whatever is missing — a config that predates
   `Google.Passive = error` leaves passive voice at suggestion level, where it
   is never fixed. `StylesPath` must be an absolute path, Vale does not
   expand `~`:

   ```ini
   StylesPath = /Users/mkuleshov/.vale/styles
   MinAlertLevel = suggestion
   Vocab = Base
   Packages = Google

   [*.md]
   BasedOnStyles = Vale, Google
   Google.Passive = error
   ```
3. `~/.vale/styles/Google/`. If absent, run `vale sync` to download the
   official Google package.
4. `~/.vale/styles/config/vocabularies/Base/accept.txt` and `reject.txt`. If
   absent, create both (empty is fine). `Vocab = Base` errors without them.

A project with its own `.vale.ini` wins — Vale searches upward from the file
before falling back to `~/.vale.ini`. Leave a project config alone.

## Fixing the findings

1. Write the draft to its real destination path. Don't draft in a temp copy:
   the fixes have to land in the file the user keeps.
2. Fix every `error` and `warning`. **Locate each one by its `Match` string
   with Edit, never by `Line`** — line numbers go stale the moment an earlier
   edit changes the text. `Message` tells you the required change.
3. `Google.Passive` is an `error` here, not the suggestion it is upstream. Kill
   passive voice: name the actor and make it the subject. Programming
   documentation always knows the actor — a module, a function, a caller, the
   user — so passive voice drops a fact the writer already holds. "The data is
   derived" becomes "the module derives the data from the API." If naming the
   actor needs a fact the document doesn't contain, that is a content gap:
   report it, don't invent an actor.
4. Each fix re-runs the hook. **Two fix passes maximum**, then report what's
   left. Don't grind against the linter.
5. Report `suggestion`-level alerts instead of rewriting them: one line each,
   `<Check> (line <N>): <Message>`. Let the user decide.
6. `Vale.Spelling` on a proper noun or an established term of art (`IPython`,
   `samtools`, `germline`) is a false positive. Append the term to
   `~/.vale/styles/config/vocabularies/Base/accept.txt`; the next edit re-lints.
   Never rename a correct term to satisfy a spell checker. But the accept list is a
   filter, and it only filters while it stays small: append only a word the
   writer cannot avoid, never an ordinary word that could have been written
   differently (`onco`, `namespaced`, `bool`). In doubt, do what step 5 does
   with a suggestion — report the alert and leave the word alone. One document
   rarely earns more than one or two entries.
7. Never rewrite words you don't own. Ignore any alert whose `Match` sits
   inside a fenced code block — Vale skips fences in Markdown, but inline code
   and front matter can still leak through. The same holds for a quotation, a
   blockquote, and any sentence quoted as an example of what *not* to write:
   report the alert and leave the wording alone.

## Limits — state these, don't paper over them

- Vale checks style, not correctness. It will not catch a wrong fact, a broken
  command, or a bad code sample.
- `Google.WordList` and similar checks are regex heuristics. A flagged sentence
  is sometimes right as written — say that rather than mangling it into
  compliance.
- `Google.Passive` is mandatory, but its regex matches a form of `be` followed
  by any participle, so it also fires on participles used as adjectives: "is
  required", "are published", "is deprecated". Those carry no hidden actor and
  are not passive voice. Leave them and name them in the report. That case and
  quoted material are the only accepted reasons to skip a `Google.Passive`
  error.
- The config covers `[*.md]` only. Other formats (`.rst`, `.txt`) need their own
  `.vale.ini` section; add one when a file needs it.
- Never run this on Python source. `python-style` governs text inside code
  (docstrings, comments, error and log messages) under ASD-STE100, which
  conflicts with Google style on contractions and person.
