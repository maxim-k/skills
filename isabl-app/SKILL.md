---
name: isabl-app
description: >
  Build a new Isabl application from a spec — wrapping a bioinformatics tool or
  pipeline as an AbstractApplication in isabl_apps or shahlab_apps. Covers
  scaffolding, the app class, the dev Dockerfile, registration, and a static
  self-check that catches the faults which otherwise only surface on HPC. Use
  whenever the user asks to write, create, scaffold or generate an Isabl app,
  says "wrap <tool> as an isabl app", "new isabl app", points at a spec or plan
  for one, or asks why an app isn't showing up under `isabl apps-*`.
---

An Isabl app is a wrapper around a bash command. It takes experiments as input,
emits a shell command, and registers result files as an analysis. Nothing more.

Two sources of truth outrank everything below, including this file:

1. `isabl_cli/isabl_cli/app.py` — the `AbstractApplication` class. Read it.
2. The target collection's `CLAUDE.md` — repo conventions.

When they disagree with this skill, they win. Say so out loud when you notice.

## Step 0 — Check the workspace, then orient

**Run this first. Do not write anything until it passes.** The skill grounds
itself in `app.py` and the collection's `CLAUDE.md`; without them it would be
guessing from stale 2023 docs.

```bash
GOLD=/Users/mkuleshov/mskcc/isabl

for d in isabl_cli isabl_api; do
  [ -d "repos/$d" ] || echo "MISSING repos/$d"
done
[ -f CLAUDE.md ] || echo "MISSING CLAUDE.md"
found=$(ls -d repos/isabl_apps repos/shahlab_apps 2>/dev/null)
echo "collections: ${found:-NONE — MISSING}"
```

Expected layout:

```
/MyProject/
├── CLAUDE.md              workspace map
├── info/                  spec material: notes, tasks, papers, tool manuals
└── repos/
    ├── isabl_cli/         required — app.py is the source of truth
    ├── isabl_api/         required — models and API contracts
    ├── isabl_apps/        required — one collection (or shahlab_apps)
    └── <tool repos>/      the tool being wrapped, its variants, legacy versions
```

On anything missing, **stop and repair before continuing**. On this machine the
gold-standard workspace at `$GOLD` is already set up with `CLAUDE.md` files, so
copy rather than clone:

```bash
mkdir -p repos
cp -R "$GOLD/repos/isabl_cli" "$GOLD/repos/isabl_api" repos/
cp -R "$GOLD/repos/isabl_apps" repos/        # or shahlab_apps — pick one
cp "$GOLD/CLAUDE.md" .                       # describes what each source is
```

`cp -R` carries `.git` with the GitHub `origin` intact, so branching, committing
and pushing all work from the copy. It also carries the per-repo `CLAUDE.md`
files, which are **untracked** in the gold standard — a `git clone` would not
bring them, which is the whole reason to copy instead. Skip `docs/`
deliberately: it is frozen at 2023 and the code supersedes it. Budget ~10 MB for
`isabl_cli` + `isabl_api`, plus ~200 MB for `isabl_apps` or ~8 MB for
`shahlab_apps`.

The copy inherits the gold standard's working tree as-is. Run `git status` in
the copied collection and confirm it is clean apart from `CLAUDE.md`, so you
don't build on top of stale uncommitted work.

If `$GOLD` does not exist, stop and ask the user to clone from GitHub instead —
do not proceed with a partial workspace.

**Then pick the collection.** If both are present, ask which one this app belongs
to; the choice is not inferable and everything downstream depends on it. They
differ substantially — layout, registration, versioning. Read
`references/collections.md` for the one you land on.

Read, in order: that repo's `CLAUDE.md`, then `isabl_cli/isabl_cli/app.py`, then
the spec. A spec commonly points at:

- `/info` — meeting notes, task lists, papers (PDFs), tool manuals. Read the
  science, not just the CLI flags: it tells you what the outputs *mean*, which
  is what `application_results` descriptions have to say.
- `/repos` — the tool's own repo, sometimes several implementations of it
  (`cgpBattenberg` vs `Battenberg`, `VIPER` vs `pyVIPER`), different versions
  (`TelomereHunter` vs `TelomereHunter2`), related pipelines, or a legacy
  version of the app itself. Establish which one you are wrapping before writing
  a line, and check the legacy app first if one exists.

## Step 1 — Pin the contract before writing code

Extract from the spec and state back to the user:

| Question | Determines |
|---|---|
| Which tool, which version, which repo? | `NAME`, `VERSION`, `application_url` |
| What does it consume — BAM, FASTQ, VCF, counts? | `get_dependencies` / `dependencies_results` |
| Produced by which upstream Isabl app? | `dependencies_results` entries |
| One sample, tumor/normal pair, cohort? | `cli_options` (see `references/app-contract.md`) |
| Which assemblies and species? | subclasses; `ASSEMBLY`/`SPECIES` |
| Which outputs are worth surfacing in the UI? | `application_results` |
| Executable, reference files, thresholds? | `application_settings` |
| Does it aggregate across a project or individual? | auto-merge trio |

Where the spec is silent on a **decision** (which assembly, which upstream app,
whether results are per-sample or project-level), ask. Where it is silent on a
**detail** (a threshold, a verbose name), pick a sane default and flag it.

## Step 2 — Branch

Both repos require a namesake branch: app `MyNewApp` → branch `my_new_app`.
Create it in the collection repo before touching files.

## Step 3 — Dockerfile

Wrap the tool for local iteration. Use the `docker-build-cache` skill.

Convention (from `apps/aracne/docker/`, `apps/viper/docker/`): the Dockerfile
lives **inside the app folder** at `<app>/docker/Dockerfile`, alongside any
scripts it copies in, and is built from the app dir:

```bash
docker build -f docker/Dockerfile -t <tool> .
```

For anything that compiles, use a multi-stage build with a slim `runtime` target
— that is the one that becomes the `.sif`:

```bash
docker buildx build --target runtime --platform=linux/amd64 -t <tool> .
```

Stop here on containers. **Singularity conversion is a separate manual
finalization step** — the app that ships runs `singularity exec` on HPC, but
producing and registering the `.sif` is not this skill's job. Write the app
against a `*_sif` setting and say it needs filling in.

Commit.

## Step 4 — Write the app class

Layout per `references/collections.md`. Contract per `references/app-contract.md`
— read it before writing, it is the distilled `app.py`.

The dominant idiom in both repos: an abstract base carrying `NAME`, `VERSION`,
`cli_help`, `cli_options`, `application_results`, `application_settings`,
`validate_experiments` and `get_command`, plus thin per-assembly subclasses that
set only `ASSEMBLY` and `SPECIES`. Results and descriptions go in a sibling
`constants.py`; non-trivial helpers in a sibling `utils.py`.

Apply the `python-style` skill. `apps/telomerehunter2/apps.py` on the
`telomerehunter2` branch is the current best template — type hints throughout,
reST docstrings, one concern per method.

Commit.

## Step 5 — Register

Per collection — see `references/collections.md` for the exact files. Summary:

- **isabl_apps** — run `isabl-apps update-imports`. Never hand-edit
  `apps/__init__.py`; it is generated.
- **shahlab_apps** — add one re-export line per class (including the base) to the
  category's `apps.py`, plus a `versions.json` record and, if the app name
  doesn't match an existing prefix, a routing branch in `utils/versions.py`.

Registration only makes the dotted path importable. The app still has to be
listed in the client's `INSTALLED_APPLICATIONS` **in the API database** to appear
under `isabl apps-*`. That is a deployment action, not a repo change — tell the
user it's outstanding.

Commit.

## Step 6 — Self-check

Every item below fails silently or only on the cluster. Run them all.

1. **Import it.** `python -c "from <pkg>.apps import <Class>"`. Catches typos, a
   missing re-export, and in shahlab an unrouted `versions.json` (which raises at
   class-definition time and takes down the whole category).
2. **isabl_apps export eligibility.** `update-imports` exports only classes with
   `NAME`, `VERSION`, `SPECIES` **and** `ASSEMBLY` set and no `_PRIVATE = True`.
   A subclass missing `SPECIES` is skipped with no error. Confirm the class is in
   the regenerated `apps/__init__.py`.
3. **Every `application_results` key resolves.** Each key must either carry a
   `pattern` or be returned by `get_analysis_results`. Otherwise `app.py:1245`
   asserts `Missing expected result {key}` — at status-patch time, after the
   cluster job already ran.
4. **`optional: True` does not waive that.** It only lets a *pattern* lookup
   return `None`; the key must still be present.
5. **`run_args` propagation.** Every custom `click.option` in `cli_options` must
   be read somewhere as `settings.run_args.get("<dest>")`. Nothing links the two
   — an unread option is silently ignored.
6. **`cli_options` includes a supported default option** (`TARGETS`, `PAIRS`,
   `PAIRS_FROM_FILE`, `REFERENCES`, `NULLABLE_REFERENCES`, `PAIR`,
   `NORMAL_TARGETS`, `ANALYSES`) unless you override
   `get_experiments_from_cli_options`. `app.py:806` asserts.
7. **`ASSEMBLY` and `SPECIES` are all-or-nothing** (`app.py:566`).
8. **`application_url`, not `URL`.** `URL` is inert — several existing apps set
   it and publish nothing.
9. **Never both `dependencies_results` and `get_dependencies`.** When the former
   is non-empty the latter is never called (`app.py:1131`).
10. **Nothing hits the API at class-definition time.** It slows every `isabl`
    invocation and can kill CLI registration. Wrap `dependencies_results` in
    `cached_property` when it instantiates another app.
11. **Lint.** black, `pylint --rcfile=.pylintrc`, `pydocstyle --config=.pydocstylerc`,
    isort with `force_single_line=true` and `from_first=true`.

## Step 7 — Hand off

Report plainly: **written and registered, not verified.** Running it against a
live API is the separate Isabl app verification skill's job.

List what is deliberately outstanding:

- `NotImplemented` and placeholder settings still needing `patch-settings`.
- The `.sif` — built from the Dockerfile, not yet produced or registered.
- Cluster resources. Setting `application_settings["resources"]` is in scope and
  worth doing — one line, and both collections' batch mappers honour it. The
  per-app branch in `slurm.py`/`lsf.py` is not. Without either, the app gets
  1 GB and 1 core, which will fail on real data.
- `INSTALLED_APPLICATIONS` — the app is invisible to `isabl` until added.
