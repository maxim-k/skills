---
name: toil-to-nextflow
description: >
  Convert a Toil pipeline (a Python package that sequences containerized tool
  calls as a Toil job graph) into a modern Nextflow DSL2 pipeline. Covers the
  over-engineering audit, extracting the logic that survives, the process/DAG
  design, the language modernisation pass, and rewiring the caller. Use when
  the user asks to convert, port, migrate or rewrite a Toil pipeline (often a
  `toil_<tool>` repo) to Nextflow, says "Toil is outdated / a dead end", or
  points at a Toil package that wraps a bioinformatics tool.
---

A Toil pipeline is almost always an **orchestration layer**: the real analysis
is a tool (often Perl/R/C) shipped in a container, and the Python only splits
it into jobs, schedules them on a cluster, and bolts on a few custom
post-processing steps. The conversion keeps the tool calls and the custom
steps. It deletes the orchestration — Nextflow's engine replaces it.

Two sources of truth outrank this file:

1. The **nextflow-io agent-skills** bundle — `/nextflow:create-workflow`,
   `/nextflow:migrate-nextflow-code` and its `references/*.md`. The reference
   files are the authoritative statement of modern (Nextflow 26.04) style.
2. The **target repo's `CLAUDE.md`** and the **caller's `CLAUDE.md`** — repo
   conventions and the contract the caller depends on.

When they disagree with this skill, they win. Say so when you notice.

Do the steps in order. Each ends with a commit.

## Step 0 — Orient

**Tooling.** Nextflow ≥ 26.04 (`/nextflow:install-nextflow` if missing —
it also installs Java 21). `jq` and Java 17+ for the type checker. Docker or
Singularity. Note: `nextflow` needs `JAVA_HOME` in non-interactive shells if
Java came from SDKMAN.

**Read the whole Toil package, end to end**, before writing anything. Find:

- The **one module that holds the real logic** — usually `jobs.py` (the Toil
  `Job` subclasses). Everything else is boilerplate until proven otherwise.
- The **DAG builder** — usually a `run_toil` / `build_workflow` function that
  chains jobs with `addChild` (parallel) and `addFollowOn` (sequential).
- The **CLI** — a `ContainerArgumentParser` / argparse layer, plus a
  hand-rolled sub-command dispatcher that pops `sys.argv[1]` before Toil sees
  it. All of it goes.
- The **container** — the base image in the `Dockerfile`; the tool binary and
  any bundled scripts live there.

Read `references/toil-mapping.md` — the Toil-concept → Nextflow-concept map.

## Step 1 — Audit the over-engineering

Run `/ponytail:ponytail-audit` at **ultra** intensity on the Toil repo. It
produces a ranked delete/fold list, applies nothing.

`references/toil-boilerplate.md` lists the constructs that are boilerplate in
*every* Toil pipeline, with the Nextflow replacement for each. Use it to
sort the audit findings into "delete now" vs "logic that must be reproduced".

## Step 2 — Pin the contract

Extract and state back to the user:

| Question | Determines |
|---|---|
| Sub-commands / entry points (`subclones`, `refit`, `finalise`, …)? | Nextflow entry workflows or a `--step` param |
| Every CLI input — bams, references, panels, flags, per-step params? | typed `params {}` block + `nextflow_schema.json` |
| The DAG: stage order, which stages fan out and by how much? | process chain + scatter channels |
| Per-stage resources (memory/cores/runtime)? | `conf/base.config` labels + `withName` |
| Every output file / glob the caller reads? | the `output {}` block; **this is the contract** |
| The custom steps that are **not** just a tool call (R/Python post-processing, file reshaping, rho/psi-style math)? | `bin/` scripts, extracted in Step 4 |
| Shared mutable working directory between stages? | thread it as a channel (see `references/nextflow-conventions.md`) |

Then **decide the granularity** with the user:

| Option | What it means |
|---|---|
| **Faithful** | one Nextflow process per Toil job / tool sub-stage; scatter preserved. Highest fidelity, least idiomatic, fights Nextflow's file-I/O model if the tool uses a shared progress-file dir. |
| **Hybrid** (usual pick) | keep the scatter stages that genuinely parallelise; collapse the rest into one "core" process that runs the tool end to end. |
| **Coarse** | one process runs the whole tool with its own internal threading; scatter only what's outside the tool. Simplest; loses cross-node fan-out. |

## Step 3 — Branch

Namesake branch in the pipeline repo (`nextflow`), and a branch in the
caller's repo for Step 7. Create both before touching files.

## Step 4 — Stage spec + extract survivors

1. Write `STAGES.md` in the pipeline repo: the definitive stage list, each
   stage's exact tool invocation, scatter width, resources, inputs, outputs,
   and the custom-step data flow. Source it from `jobs.py`, the DAG builder,
   and the audit. This is the spec the Nextflow pipeline implements.
2. Extract **only the logic that carries into Nextflow** into `bin/` scripts,
   each written with the `python-style` skill, each with one `assert`-based
   `__main__` self-check. Typical survivors: a scatter-gather concat, an
   output-file reshaper, closed-form parameter math, a VCF-to-table
   conversion. Port any Python-2 / old-pandas idioms (`df.ix`, `df.append`)
   forward.
3. **Do not refactor the Toil package.** It stays as the reference
   implementation until the Nextflow version is validated on real data. Cleaning
   code you are about to delete is wasted work.

Carry bundled R/shell scripts and compiled binaries from the Toil `data/`
directory into the pipeline `assets/` unchanged. Note the rebuild recipe and
target architecture for any binary.

## Step 5 — Write the Nextflow pipeline

`/nextflow:create-workflow` is a **module-composition tool** — it searches the
Nextflow Registry and chains existing modules. It has **nothing to say about a
tool with no registry module**, which is the usual case for a Toil-wrapped
tool. Use it only to scaffold and for genuinely standard steps
(`nf-core/samtools/*` for a BAM-header read, etc.). The rest is hand-written
processes.

Read `references/nextflow-conventions.md` first — it is the distilled modern
style. Then:

1. Scaffold on the `nextflow` branch: `main.nf`, `nextflow.config` (profiles:
   `test`, `docker`, `singularity`, cluster executors), `conf/base.config`
   (resource labels), `modules/local/*.nf`, `subworkflows/local/*.nf`,
   `assets/`, `bin/`, `tests/` (`nf-test`).
2. Write the processes **to the modern conventions from the start** (typed
   inputs/outputs emitting one fat record, `container` pinned to the tool
   image, versions to the `versions` topic). Writing them right now makes
   Step 6 a lint pass instead of a rewrite.
3. Wire the entry workflows / `--step` branch. Scatter with `.combine()` in
   the caller, gather with `.join(by:)` / `.groupBy()`.
4. Handle a shared tool working directory by threading it as a channel with
   `stageInMode 'symlink'` — see `references/nextflow-conventions.md` for the
   pattern and the fallback.
5. Local validation only: `nextflow lint`, `nf-test test`, and
   `nextflow run . -stub -profile test` for each entry point (stub processes
   `touch` their declared outputs). The real tool usually cannot run on a dev
   machine — wrong arch, huge container, no reference data, no test inputs.
   Say so.

## Step 6 — Modernise the language

`/nextflow:migrate-nextflow-code`, in its mandatory dependency order, one
migration at a time, verifying behaviour is unchanged after each:

`strict syntax` → `topic channels` → `static typing` → `workflow outputs`

If Step 5 followed the conventions, this is mostly `nextflow lint -o concise .`
and the type checker (`nextflow-typecheck.sh`) coming back clean.

## Step 7 — Rewire the caller

The Toil pipeline had a caller — commonly an Isabl `AbstractApplication` that
built a `toil_<tool> <subcommand> …` command. Read `references/caller-rewire.md`
for the Isabl mechanism (`create_nextflow_script`, `params_as_json`, version
bump semantics).

The rule regardless of caller: **the output-file contract does not change.**
The pipeline writes the same filenames into the same output directory, so the
caller's result-collection code is untouched. Only the command that launches
the work changes.

## Step 8 — Verify and hand off

**Local — structure only:** `nextflow lint` clean, type checker clean,
`nf-test` green, `-stub` run of every entry point emits the expected filenames,
`pytest` on the `bin/` self-checks.

**Cluster — behaviour parity (the user runs this):** run the pipeline on a
known input, diff every key output against a run of the original Toil pipeline
on the same input. Numeric outputs exactly; plots by eye.

Report plainly: **written, not validated on real data.** List what is
outstanding — the parity run, any deferred scatter optimisation, caller
settings a deployment must fill in, binary rebuilds for the target arch. Keep
the Toil package in the repo until the user signs off on parity.
