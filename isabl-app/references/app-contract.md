# The `AbstractApplication` contract

Distilled from `isabl_cli/isabl_cli/app.py`. Line refs are to that file. When
this disagrees with the source, the source wins.

`AbstractApplication` is a plain class, not an ABC. `@abc.abstractmethod` is used
only to stamp `__isabstractmethod__` so the framework can feature-detect whether
you overrode a method. Nothing is enforced at instantiation.

## Attributes

### Identity

| Attribute | Required | Type | Default | Controls |
|---|---|---|---|---|
| `NAME` | **yes** | `str` | `None` | application row; CLI command name via `slugify(NAME)` |
| `VERSION` | **yes** | `str` | `None` | application row; bumping creates a *new* row, old analyses stay put |
| `ASSEMBLY` | all-or-nothing with `SPECIES` | `str` | `None` | CLI group `isabl apps-<assembly>`; `get_bam`/`get_bedfile` key |
| `SPECIES` | required iff `ASSEMBLY` set | `str` | `None` | assembly species |

Asserted at `app.py:558-569`. The app row also stores
`application_class = f"{__module__}.{__class__.__name__}"` — the framework
re-imports your class from that dotted path at status-patch time, so **the class
must stay importable at a stable path**. Renaming or moving it breaks existing
analyses with `{class} does not match: {application_class}` (`api.py:757`).

### Metadata

- `application_description` — `str`, default `""`.
- `application_url` — `str` or `None`. **Not `URL`.** `URL` is inert; several
  apps set it and publish nothing.

### Settings

- `application_settings` — `dict` of defaults, arbitrarily nested.
- `application_import_strings` — `set[str]` of setting *keys* whose values are
  dotted paths to import into objects.

Resolution (`settings.py:244-310`), per client:

- A falsy DB value falls back to the class default.
- `NotImplemented` as a default means **required**; unset →
  `Missing required setting: '<attr>'`.
- `"reference_data_id:<key>"` resolves to `assembly.reference_data[<key>]["url"]`;
  a missing key becomes `NotImplemented` → required-missing.
- Nested dict defaults are recursed and **unknown DB keys are rejected**
  (`Got unexpected setting '<k>' for '<attr>'`). Put `"skip_check": True` inside
  a dict default to disable key validation for that subtree.
- All errors aggregate into one `ConfigurationError`.

The result is a `Munch`: `settings.foo` and `settings["foo"]` both work. Three
keys are injected at run time and are always available inside `get_command`:
`settings.restart`, `settings.force`, `settings.run_args` (`app.py:877-884`).

`run_args` is the **only** channel from a custom `click.option` to your code.
Adding an option without reading `settings.run_args.get("<dest>")` silently does
nothing.

### Results

- `application_results` — `dict[str, dict]`. Key = result id.
- `application_protect_results` — `bool`, default `True`. `False` makes the app
  re-runnable: SUCCEEDED analyses are re-staged, storage is not chmod'd read-only.
- `application_project_level_results`, `application_individual_level_results` —
  auto-merge specs.

Spec keys the **CLI** reads:

| Key | Type | Meaning |
|---|---|---|
| `pattern` | `str` | glob (recursive `rglob`) of `analysis.storage_url`; auto-resolves the result, newest match first |
| `exclude` | `str` | skip matches whose *filename* contains this substring |
| `optional` | `bool` | if no file matches, return `None` instead of raising |
| `store_as_bam` | `bool` | register the path as the target experiment's BAM for `ASSEMBLY` |

Spec keys the **API** persists: `frontend_type`, `verbose_name`, `description`,
`external_link`, `optional`, `logo`, `hide_chip`, `order`, `data`. Anything else
(including `pattern`, `exclude`, `store_as_bam`) is dropped server-side — which
is fine, the CLI reads the class attribute, not the DB.

`frontend_type` values in real use: `text-file`, `tsv-file`, `string`, `number`,
`image`, `html`, `pdf`, `json`, `csv-file`, `url-link`, `ansi`, and the
parameterized `igv_bam:<index_result_key>`.

**The assertion that costs an HPC round trip** (`app.py:1244-1245`):

```python
for i in specification:
    assert i in results, f"Missing expected result {i} in: {results}"
```

Every declared key must be present after pattern resolution and
`get_analysis_results` are merged. `optional: True` does **not** waive this — it
only affects pattern lookup. This fires at status-patch time, i.e. from the job
script on the cluster, long after submission.

`command_script`, `command_log` and `command_err` are injected automatically.
Never declare or return them.

### Dependencies

- `application_inputs` — `dict`. Defaults for the `inputs` dict.
  `NotImplemented` = required and must be produced by dependencies, else
  `Required inputs missing from 'get_dependencies': ...`.
- `dependencies_results` — `list[dict]`, declarative. **When non-empty,
  `get_dependencies` is never called** (`app.py:1131`). Never write both.

```python
{
    "result": "bam",              # result key on the upstream analysis
    "name": "tumor_bam",          # key it gets in `inputs`
    "app": SomeApp(),             # or:
    "app_name": "MONDRIAN-QC",
    "app_version": "1.0.0",       # omit for any; "latest" for newest
    "app_assembly": "GRCh38",
    "linked": True,               # False = don't link as a dependency
}
```

Wrap it in `cached_property` when it instantiates another app — a bare class
attribute hits the API at import time, which slows every `isabl` invocation and
can kill CLI registration.

### Behavior flags

- `unique_analysis_per_individual` — `bool`, default `False`. One analysis per
  individual. Incompatible with individual-level auto-merge.
- `skip_status` — analyses in `{FAILED, FINISHED, STARTED, SUBMITTED, SUCCEEDED,
  REJECTED}` are never re-prepared. This, not permissions, is why `--force` and
  `--restart` exist.
- `skip_exceptions` — errors caught during command generation so the rest of the
  submission continues: `AssertionError`, `click.UsageError`,
  `MissingRequirementError`, `ConfigurationError`, `MissingOutputError`.
- `IS_UNMATCHED` — undocumented but honored: makes `validate_individuals` require
  targets and references from *different* individuals.
- `resources` — not an `AbstractApplication` attribute, but the collections'
  batch-system mappers read it: `{"cores": 1, "memory": 120, "runtime": 1440}`
  (runtime in minutes). Placement differs:
  - **isabl_apps** — either `application_settings["resources"]` or a class
    attribute `resources`; the setting wins if both exist.
  - **shahlab_apps** — `application_settings["resources"]` only. A class
    attribute is ignored.

  Declaring it costs one line and is the difference between sane resources and
  the 1 GB / 1 core default that fails on real data.

### CLI

- `cli_help` — `str`.
- `cli_options` — `list` of click option decorators, usually from
  `isabl_cli.options`.
- `cli_allow_force` / `cli_allow_restart` / `cli_allow_local` — `bool`, default
  `True`. Never add `FORCE`/`RESTART`/`QUIET`/`COMMIT` to `cli_options`; the
  framework adds equivalents and you'd get duplicate params.

## Methods

### Required in practice

```python
def get_command(self, analysis, inputs, settings) -> str
```
`app.py:151`. The whole point of the app. `NotImplementedError` is **not** in
`skip_exceptions`, so leaving it unimplemented crashes the run.

```python
def validate_experiments(self, targets, references) -> None
```
`app.py:213`. Raise `AssertionError` for tuples that don't make sense. The base
raises `NotImplementedError`, so it is effectively required — write `pass` if you
genuinely have nothing to check. Called once per existing analysis and once per
new tuple.

### Optional

| Method | Line | Returns | When |
|---|---|---|---|
| `get_experiments_from_cli_options(**cli_options)` | 169 | `[(targets, references), ...]` | designs the built-in options can't express |
| `get_dependencies(targets, references, settings)` | 230 | `([analysis_pks], {inputs})` | resolve upstream results |
| `get_analysis_results(analysis)` | 182 | `dict` | on completion, to catalog outputs |
| `validate_settings(settings)` | 200 | `None` | once per run, before anything is created |
| `get_after_completion_status(analysis)` | 196 | `"FINISHED"` or `"IN_PROGRESS"` | flag analyses for manual review |

Auto-merge trios — defining the `merge_*` method is what switches the feature on
and creates a `"{NAME} Project Application"` row:

- Project: `application_project_level_results` + `merge_project_analyses(analysis, analyses)` + `get_project_analysis_results(analysis)` + optional `validate_project_analyses(project, analyses)`
- Individual: the same four with `individual` in place of `project`

A merge needs **≥ 2 succeeded analyses** or it warns and returns.

## Run flow, with hook order

```
isabl apps-<assembly> <name>-<version> [opts]
└─ get_experiments_from_cli_options  (or the default builder)
└─ run()
   ├─ resolve all settings            → ConfigurationError surfaces here
   ├─ inject restart / force / run_args
   ├─ HOOK validate_settings
   ├─ get_or_create_analyses()
   │  ├─ HOOK get_dependencies / dependencies_results
   │  ├─ HOOK validate_experiments   (existing analyses, then new tuples)
   │  └─ create analyses, set storage_url
   └─ run_analyses()
      ├─ skip_status / --force / --restart handling
      ├─ HOOK get_command            (guarded by skip_exceptions)
      ├─ HOOK get_after_completion_status
      ├─ write head_job.sh
      └─ submit  (or STAGED without --commit)

... job runs on the cluster, then calls back:
isabl patch-status --key <pk> --status SUCCEEDED
└─ HOOK get_analysis_results + pattern resolution
   └─ assert every declared result key is present   ← fails here, not at submit
```

Note: `get_dependencies` is evaluated **twice** per analysis — Python evaluates
`dict.pop`'s default eagerly at `app.py:993`. Keep it idempotent and free of side
effects.

## CLI option vocabulary

From `isabl_cli.options`. At least one of these must be in `cli_options` unless
you override `get_experiments_from_cli_options` (`app.py:806` asserts).

| Option | Flag | Produces |
|---|---|---|
| `TARGETS` | `--targets-filters` / `-fi` | one tuple per target: `([t], references)` |
| `NORMAL_TARGETS` | `--normal-targets-filters` | same, forced `sample__category=NORMAL` |
| `REFERENCES` | `--references-filters` / `-rfi` | shared references list |
| `NULLABLE_REFERENCES` | same, optional | defaults to `[]` |
| `PAIR` | `--pair` / `-p` | one tumor/normal tuple |
| `PAIRS` | `--pairs` / `-p`, multiple | many tumor/normal tuples |
| `PAIRS_FROM_FILE` | `--pairs-from-file` / `-pf` | tuples from a two-column TSV |
| `ANALYSES` | `--analyses-filters` / `-fi` | `(a.targets, a.references)` per analysis |

## Validators

Instance methods — call from `validate_experiments`. All raise `AssertionError`,
which is caught and reported as an invalid tuple.

`validate_one_target(targets)` · `validate_one_target_no_references(targets, references)` ·
`validate_is_pair(targets, references)` · `validate_at_least_one_target_one_reference` ·
`validate_targets_not_in_references` · `validate_dna_only` · `validate_rna_only` ·
`validate_dna_pairs` · `validate_pdx_only` · `validate_methods(experiments, methods)` ·
`validate_same_technique` · `validate_same_platform` · `validate_species` ·
`validate_are_normals` · `validate_individuals` · `validate_source(experiments, source)` ·
`validate_has_raw_data` · `validate_fastq_only` · `validate_single_data_type` ·
`validate_is_file(path)` · `validate_is_dir(path)` · `validate_reference_genome` ·
`validate_bams(experiments)` · `validate_bedfiles(experiments, bedfile_type="targets")`

Note `validate_species` exists but is **not** called automatically — the call
site in `get_or_create_analyses` is commented out.

NGS accessors: `get_bam(experiment)`, `get_bams(experiments)`,
`get_bedfile(experiment, bedfile_type="targets")`, `get_result(...)`,
`get_results(...)`.

## Failure modes

| Message | Cause |
|---|---|
| `Missing expected result {k} in: {...}` | declared result key with no `pattern` and not returned by `get_analysis_results` |
| `Missing required setting: '{k}'` | `NotImplemented` default never supplied by `patch-settings` |
| `Got unexpected setting '{k}' for '{attr}'` | DB settings key not present in the class default dict |
| `Required inputs missing from 'get_dependencies': ...` | `application_inputs` entry left `NotImplemented` |
| `'{cls}.cli_options' must include at least one of ...` | no experiment-source option and no `get_experiments_from_cli_options` |
| `NAME must be set` / `ASSEMBLY must be set` | identity attributes missing or half-set |
| `Invalid configuration, failed to register {cls}: {err}` | `ConfigurationError`/`AttributeError` at CLI registration; the app is dropped |
| `Failed to import applications: {err}` | bad dotted path in `INSTALLED_APPLICATIONS` |
| `{cls} does not match: {application_class}` | class renamed or moved after analyses existed |
| `No file matching pattern '{p}' found in '{dir}'` | non-optional `pattern` matched nothing; turns the job FAILED |
| `{cls} is loading slowly...` | class body hits the API at import time |

Only `ConfigurationError` and `AttributeError` are caught at CLI registration.
**Any other exception in your class body kills the entire `isabl` CLI**, not just
your app.

## Minimal correct app

```python
from isabl_cli import AbstractApplication
from isabl_cli import options


class MyApp(AbstractApplication):
    NAME = "MY-APP"
    VERSION = "1.0.0"

    cli_help = "Run MY-APP on WGS pairs."
    cli_options = [options.PAIRS]
    application_description = "What it does and what the outputs mean."
    application_url = "https://github.com/org/tool"

    application_settings = {
        "my_app_sif": NotImplemented,                    # required
        "reference": "reference_data_id:genome_fasta",   # from assembly reference data
        "threads": 8,
    }

    application_results = {
        "vcf": {
            "description": "Somatic variants called against the matched normal.",
            "verbose_name": "Somatic VCF",
            "frontend_type": "tsv-file",
            "pattern": "*.somatic.vcf.gz",   # auto-resolved
        },
    }

    def validate_experiments(self, targets, references):
        self.validate_is_pair(targets, references)
        self.validate_methods(targets, {"WG"})
        self.validate_bams(targets + references)

    def validate_settings(self, settings):
        self.validate_is_file(settings.my_app_sif)

    def get_dependencies(self, targets, references, settings):
        return [], {
            "tumor_bam": self.get_bam(targets[0]),
            "normal_bam": self.get_bam(references[0]),
        }

    def get_command(self, analysis, inputs, settings):
        return (
            f"singularity exec --bind /data1 {settings.my_app_sif} tool "
            f"--ref {settings.reference} --threads {settings.threads} "
            f"--tumor {inputs['tumor_bam']} --normal {inputs['normal_bam']} "
            f"--out {analysis['storage_url']}"
        )


class MyAppGRCh38(MyApp):
    ASSEMBLY = "GRCh38"
    SPECIES = "HUMAN"
```

Every result here carries a `pattern`, so `get_analysis_results` can be omitted
entirely. Declare a key without one and you must return it.

For a long or multi-step command, write a script into the analysis directory and
return `bash -e .script.sh` — the universal idiom in both collections.
