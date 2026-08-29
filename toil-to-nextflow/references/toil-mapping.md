# Toil concept → Nextflow concept

The mechanical translation. Read this before Step 1 so the audit findings and
the `STAGES.md` spec land in the right Nextflow shape.

| Toil | Nextflow | Notes |
|---|---|---|
| A `Job` subclass with a `run(self, fileStore)` method | a `process` | one job class often becomes one process; a job that just fans out children becomes a scatter channel, not a process |
| `self.addChild(job)` | a scatter: `ch = channel.of(1..n); PROC(input.combine(ch))` | `addChild` = "run these in parallel, then continue" |
| `self.addFollowOn(job)` | a chained call: `B(A.out)` | `addFollowOn` = "run after this one finishes" |
| A `ProcessRunner` / driver job that loops `addChild` over `range(steps)` | `channel.of(1..steps)` in the calling workflow | the loop count is the scatter width; it is data, not code |
| `ContainerJob.call(cmd)` (runs `cmd` inside the `--docker`/`--singularity` image) | the process `script:` block + a `container '<image>'` directive | |
| bare `subprocess.check_call(cmd)` in a job (runs on the worker host, not the container) | still a process `script:` line, but the binary must be in the process container or staged from `assets/` | Toil pipelines often run helper binaries outside the container — fold them into one container or an `assets/` bin |
| `fileStore` / `fileStore.logToMaster` | Nextflow input/output staging; `log.info` / stdout | Nextflow stages files explicitly — no shared mutable filesystem |
| The job store (positional arg) + `--restart` | `-work-dir` + `-resume` | |
| `--batchSystem LSF` / `CustomLSF` / `singleMachine` and Toil resource flags | `nextflow.config` `process.executor` + profiles | the whole Toil batch-system layer is config now |
| `ContainerArgumentParser` + `get_parser(step)` | a typed `params {}` block in `main.nf` + `nextflow_schema.json` | one `add_argument` → one typed param |
| The hand-rolled sub-command dispatcher (`sys.argv[1]` pop) | `-entry <name>` or a `--step` param that branches in `main.nf` | it only exists because Toil claims `argv[1]` as the job store |
| `time.sleep(N)` after a job (NFS-latency workaround) | nothing — delete it | Nextflow stages task outputs; there is no shared-FS race to wait out |
| `processes = {name: {steps, memory, cores, runtime}}` dict | `steps` → scatter width in the workflow; `memory`/`cores`/`runtime` → `conf/base.config` labels + `withName:` | the dict conflates topology and resources; split them |
| Per-job `ContainerJob` subclass that only overrides `run()` | usually a `script:` branch or a `bin/` script, not a new process | |
| A custom exception module nobody catches by type | delete; use `ValueError` / `RuntimeError` | |
| `force_link` / `force_symlink` / `tar_dir` helpers | Nextflow staging; one `tar czf` line | |

**The shared working directory.** Many tool pipelines (cgpBattenberg-style)
keep one `tmp<Tool>/` directory that every stage reads and writes, with
progress touch-files. Toil tolerates this because jobs share a filesystem.
Nextflow does not. Options, in order of preference:

1. Collapse the stages that share the directory into one process (the "coarse"
   or "hybrid" granularity).
2. If the stages must stay separate, thread the directory as a channel: the
   first stage emits it as an output `path`, later stages take it as an input
   `path` with `stageInMode 'symlink'`. Only works if each stage touches a
   disjoint slice (e.g. per-chromosome) — verify against the tool's docs.
