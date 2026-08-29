# Boilerplate in every Toil pipeline

The `/ponytail:ponytail-audit` in Step 1 will find these. This list is here so
you can sort its findings fast: everything below is **delete now**, the
Nextflow engine or config replaces it. What is left after removing all of it
is the logic to reproduce.

| Construct | Typical file | Replacement |
|---|---|---|
| Sub-command dispatcher that pops `sys.argv[1]` "so Toil doesn't use it as the job store" | `cli.py`, `__main__.py` | `-entry` / `--step` param |
| `get_parser(step)` — one `add_argument` per flag, help strings with hard-coded cluster paths | `options.py` | typed `params {}` + `nextflow_schema.json` |
| Custom exception module — a base class plus 6–8 subclasses, most never raised | `exceptions.py` | `ValueError` / `RuntimeError` |
| Help-text heredocs (`*_DOCS` strings) printed by the hand-rolled CLI | `constants.py` | `nextflow run --help` |
| `force_link` / `force_symlink` (an `os.link` with an unlink guard) | `utils.py` | Nextflow input staging |
| `tar_dir` | `utils.py` | one `tar czf` in a `script:` block |
| `validate_patterns_are_files` / `_are_dirs` — glob + isfile + getsize loop | `validators.py` | Nextflow fails a task when a declared output is missing |
| `validate_bam` / `validate_reference` — `isfile(x) and isfile(x + ".bai")` | `validators.py` | process input typing; a one-line guard if you still want it |
| Range/float validators that duplicate a check already inside the math function | `validators.py` | keep one copy, in the function |
| `processes` dict mixing `steps` (scatter) with `memory`/`cores`/`runtime` | `jobs.py` | scatter width → workflow; resources → `conf/base.config` |
| `ProcessRunner` / driver job whose only job is `addChild` in a loop | `jobs.py` | `channel.of(1..n)` |
| `time.sleep(N)` after every job | `jobs.py` | delete |
| Per-job `ContainerJob` subclass overriding only `run()` | `jobs.py` | a `script:` branch or a `bin/` script |
| `__init__.py` hand-reading a `VERSION` file | `__init__.py` | `importlib.metadata.version()` or drop it |
| Dead deps in `setup.json` / `pyproject.toml` — `numpy`, `more-itertools`, `pytest` pinned as a runtime dep | packaging | remove |
| Tests for the fs wrappers, the exception module, the argparse layer | `tests/` | delete with the code they test |

**Route to a normal review, not the audit:** removed-API usage (`df.ix`,
`DataFrame.append`), off-by-one bugs, typos in test loops. The audit is
over-engineering only.

## What usually survives

- The tool invocation itself — the argument list each `jobs.py` job builds for
  the wrapped binary.
- The custom post-processing steps: output-file reshaping, closed-form
  parameter math, VCF/table conversions, plot regeneration, sex-chromosome
  special cases.
- Closed-form helpers like a `compute_<params>` function and the segment
  lookup that feeds it.
- One or two load-bearing constants (an output-glob list).
- The DAG order and the per-stage scatter widths and resources.
- The `data/` directory — bundled R/shell scripts and compiled binaries.
