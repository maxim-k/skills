---
name: conventional-commit
description: >
  Personal commit message standard: every commit is a single-line
  Conventional Commit, scope drawn from a SCOPES.md file in the repo. Use
  whenever writing a git commit message or the user asks about commit style.
---

Every commit message is exactly one line:

```
<type>[(scope)]: <short summary>
```

`type` is one of `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`,
`chore`, `ci`, `build`; `!` after type/scope marks a breaking change. The
summary is imperative.

`hook.py` in this directory runs before every `git commit` and blocks a message
that breaks the format: a second line or trailer, an unknown type, a capital or
a trailing period in the summary, a multi-scope, or a scope missing from
`SCOPES.md`. When it blocks, fix the message — don't work around the hook.

## What the hook can't decide

- **One logical change per commit.** If a change doesn't cleanly fit one
  `type`, split it into separate commits rather than combining.
- **Which scope.** Conventional Commits doesn't define how to pick one — the
  repo's `SCOPES.md` (repo root) does, as a closed vocabulary. Omit the scope
  when nothing in it fits, rather than forcing one. A commit crossing several
  scopes has no scope; split it if the changes are separable.
- **Creating `SCOPES.md`** when the repo has none. Read the project's actual
  structure (top-level modules/packages, execution stages, I/O layers, CLI/API
  surface, infra) and derive 8–15 scopes from it — real architectural
  boundaries, not filenames or labels like `bugfix`/`frontend`. Write it as a
  list of `- scope: one-line description`, then use it.
- **Issue-tracker IDs** never go in the message, not even as a scope. Reference
  the ticket in the PR description instead.
