# Modern Nextflow (26.04) conventions

Distilled from the `/nextflow:migrate-nextflow-code` reference files. Write the
pipeline to these from the start in Step 5, so Step 6 is a check, not a rewrite.
When this summary and those reference files disagree, the reference files win.

## `create-workflow` is not a pipeline generator

It searches the Nextflow Registry (`nextflow module search`), views candidates
(`nextflow module view`), asks you to approve a plan, validates each module
with `/nextflow:run-module`, then composes them with managed includes
(`include { FOO } from 'nf-core/foo'`, no `./` prefix). It produces a bare
`main.nf` + `nextflow.config`.

It has **no branch for "no module exists"** — no guidance on writing a
`process`, declaring a `container`, or resource labels. A Toil-wrapped tool
almost never has a registry module. So `create-workflow` gets you the scaffold
and the standard edges (a `samtools` header read, an index step); you
hand-write everything else against this file.

## Processes

- **Typed inputs.** `nextflow.enable.types = true` per file. `path` →
  `Path`; `val` → the concrete type; a list → `List<Path>`; nullable →
  `Type?`. `Channel` / `Value` are not valid input types.
- **Records, not tuples.** Migrate `tuple(meta, bam, bai)` inputs to
  `record(meta: Map, bam: Path, bai: Path)`. Access by field name, never by
  index.
- **One fat output record**, not many skinny emits. `path "x"` → `file('x')`;
  `path "*.x"` → `files('*.x')`; `stdout` → `stdout()`; `env 'X'` → `env('X')`.
- **Versions to the topic**, in the `output:` section:
  `tuple(task.process, 'tool', eval('tool --version | head -1')) >> 'versions'`.
  No `$(...)` or bare `$` inside `eval()` (an outer `bash -c` expands it).
  Never let a process both emit to and consume the `versions` topic — deadlock.
- `container '<image>'` directive, pinned to an exact tag — the same image the
  Toil pipeline used. Set `docker.enabled` / `singularity.enabled` in a
  profile.
- Typed processes drop `when:` — gate in the calling workflow instead.
- Restricted stdlib inside process/workflow scope: `.flatten()` →
  `.collectMany{v->v}`, `.sort()` → `.toSorted()`, `.unique()` →
  `.toUnique().toList()`, `str.split(s)` → `str.tokenize(s)`,
  `x.toString()` → `"${x}"`, `task.memory.giga` → `task.memory.toGiga()`.

## Workflows

- `take:` / `emit:` gain types: `Channel<V>`, `Value<V>`, or plain `V`.
- Define `record` types for the things flowing between stages; construct with
  `record(field: value, …)`, extend with `r + record(extra: v)`.
- Allowed operators: `collect, combine, filter, flatMap, groupBy, join, map,
  mix, reduce, subscribe, unique, until, view`. Others are discouraged.
- `Channel.of` → `channel.of`. `.set{x}` / `.tap{x}` → plain assignment.
  `.join(other)` → `.join(other, by: 'id')` (`by` required). `.mix(a,b,c)` →
  `.mix(a).mix(b).mix(c)`. `.branch{}` → one `.filter` per branch.
  `.groupTuple()` → `.groupBy()`.
- `.out`: single-output process → the call *is* the channel (`bam = FOO(ch)`,
  no `.out`); multi-output → `out = FOO(ch); out.bam`.

## Scatter / gather

The `each` input qualifier is gone. Fan out in the **caller**:

```nextflow
chroms  = channel.of(1..22, 'X')
ALLELE_COUNT( samples.combine(chroms) )          // one task per (sample, chrom)
```

Gather back to one record per sample:

```nextflow
ALLELE_COUNT.out
    .map { r -> tuple(r.meta, r) }
    .groupBy()                                    // or .join(other, by: 'meta')
```

For a fixed expected group size feed `(key, size, value)` tuples to `groupBy`.

## Params

- Config-only params stay in `nextflow.config`'s `params {}`. **Script-used
  params** move to a typed `params {}` block in `main.nf`:

  ```nextflow
  params {
      tumor_bam:  Path
      reference:  Path
      sex:        String
      threads:    Integer = 8
      subclones_dir: Path?
  }
  ```

  No default = required (the run fails if omitted). `?` = optional. Boolean
  with no default = `false`.
- **Do not read the global `params` object inside a subworkflow or process.**
  The entry workflow reads typed params and threads them down as `take:`
  inputs. Bundle related params into a `record` and pass that.
- Keep `nextflow_schema.json`. `--flag false` from the CLI arrives as the
  string `'false'` (truthy) unless the param is typed `Boolean` — a real
  behaviour trap when porting a Toil `--is-male`-style flag.

## Workflow outputs

Replace every `publishDir` with a top-level `output {}` block and a `publish:`
section in the entry workflow. `outputDir = params.outdir` keeps `--outdir`
working. Per-sample routing: `path { r -> "cn/${r.meta.id}" }`. A record's
files are auto-extracted — no manual flattening.

**The output contract:** if the Toil pipeline's caller collects results by
globbing a directory, the `output {}` block must land the **same filenames in
the same directory**. Diff the published tree against a Toil run to confirm.

## Resources

No resource-tier convention ships with the skills — bring your own. The nf-core
pattern: `label 'process_high'` on a process, resolved in `conf/base.config`
with `withLabel:` / `withName:` selectors carrying `memory` / `cpus` / `time`.
Port the Toil `processes` dict's `memory`/`cores`/`runtime` values straight
into `withName:` blocks.

## Local validation without the real tool

- `nextflow lint -o concise .` — strict-syntax clean.
- `nextflow-typecheck.sh <dir>` (from the migrate skill's `scripts/`) — types
  clean; needs `jq` + Java 17+.
- `nf-test test` — with stub blocks.
- `nextflow run . -stub -profile test` — every process needs a `stub:` block
  that `touch`es its declared outputs; this exercises the whole DAG wiring
  without the tool.
