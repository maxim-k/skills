---
name: conventional-commit
description: >
  Personal commit message standard: every commit is a single-line
  Conventional Commit, scope drawn from a SCOPES.md file in the repo. Use
  whenever writing a git commit message or the user asks about commit style.
---

Every commit message is **exactly one line**. No body, no footer, no
trailers of any kind (no `Co-Authored-By:`, no "Generated with Claude
Code") — nothing after the summary line, ever.

```
<type>[(scope)]: <short summary>
```

- `type` is one of: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`,
  `test`, `chore`, `ci`, `build`. Use `!` after type/scope for a breaking
  change (there is no `BREAKING CHANGE:` footer here — it's one line).
- Summary is imperative, lowercase, no trailing period.
- One logical change per commit. If a change doesn't cleanly fit one `type`,
  split it into separate commits rather than combining.

## Scope: check `SCOPES.md`

Conventional Commits doesn't define how to pick a scope — this repo's
`SCOPES.md` (repo root) does. Before writing a commit:

1. **Look for `SCOPES.md`.** If it exists, pick a scope from it — a closed
   vocabulary, not invented ad hoc.
2. **If it doesn't exist, create it.** Read the project's actual structure
   (top-level modules/packages, execution stages, I/O layers, CLI/API
   surface, infra) and derive 8–15 scopes from it — real architectural
   boundaries, not filenames or labels like `bugfix`/`frontend`. Write
   `SCOPES.md` as a list of `- scope: one-line description`, then use it.
3. **A commit crossing multiple scopes has no scope.** Don't write
   `feat(cli, config, core): ...`. Drop the scope entirely, or split the
   commit if the changes are actually separable.
4. **Never use issue-tracker IDs as a scope.** They don't belong in a
   one-line message with no footer at all — drop them, or reference the
   ticket in the PR description instead.

Scope is optional per the spec — omit it when nothing in `SCOPES.md` fits,
rather than forcing one.
