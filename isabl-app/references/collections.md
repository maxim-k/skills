# The two app collections

The workspace holds exactly one. They diverge on layout, registration and
versioning — check which you're in before writing anything. Each repo's
`CLAUDE.md` is authoritative; this is the summary.

Shared by both: apps contain **no pipeline logic**. They build a shell command
that invokes a container, a toil script, or a nextflow workflow. Reference paths
and executables belong in settings, never inline in `get_command`.

Also shared: commit messages via the `conventional-commit` skill, Python via the
`python-style` skill, imports via isort with `force_single_line=true` and
`from_first=true` (one import per line, `from x import y` before `import x`).

---

# isabl_apps (MSK Papaemmanuil)

## Layout — one directory per tool

```
isabl_apps/apps/my_new_app/
├── __init__.py          # empty
├── apps.py              # the AbstractApplication subclasses
├── constants.py         # APPLICATION_RESULTS, APPLICATION_DESCRIPTION
├── utils.py             # non-trivial helpers (optional)
├── docker/Dockerfile    # dev container, built from this dir
└── SCOPE.md             # commit scopes for this app
```

Branch and folder are both the namesake, snake_case: app `MyNewApp` → branch
`my_new_app` → `isabl_apps/apps/my_new_app/`.

Commit scopes come from the **per-app `SCOPE.md`**, not the repo-root `SCOPES.md`
that `conventional-commit` describes. That override wins here.

## Registration — generated, do not hand-edit

`isabl_apps/apps/__init__.py` is produced by:

```bash
isabl-apps update-imports
```

It exports every class in an `apps.py` that has **`NAME`, `VERSION`, `SPECIES`
and `ASSEMBLY` all set** and lacks `_PRIVATE = True`.

Two consequences:

- The abstract base is correctly **not** exported — it has no `ASSEMBLY`. That is
  intended, not a bug.
- An assembly subclass missing `SPECIES` is **silently skipped**. No error, no
  warning; the app simply never appears. Always confirm your class landed in the
  regenerated file.

There is a third, subtler filter: `member.__module__` must start with
`isabl_apps.apps.<tool>.apps`. A class **defined in a sibling module** and merely
imported into `apps.py` is not exported — its `__module__` is
`isabl_apps.apps.<tool>._impl`. Define app classes directly in `apps.py` here.
(This is the opposite of shahlab_apps, where `_<pipeline>.py` + re-export is the
required pattern. Don't carry the habit across.)

The scan accepts either `apps/<tool>/apps.py` or `apps/<tool>/apps/__init__.py`.

## Command builders

Pick the one matching the tool:

| Helper | Module | For |
|---|---|---|
| `get_docker_command(image, entrypoint)` | `isabl_apps/utils.py` | plain container calls |
| `build_toil_command(...)` | `isabl_apps/toil.py` | toil pipelines |
| `create_nextflow_script(...)` | `isabl_apps/nextflow/utils.py` | nf-core workflows |

`nextflow/results.py` holds `NEXTFLOW_RESULTS` to spread into
`application_results`.

## Containers: dev vs HPC

The app code is identical in both. Only the setting's *value* changes:

- **Dev** — `get_docker_command("org/image:tag", "entrypoint")` produces a
  `docker run ...` prefix, stored as a setting.
- **HPC** — a path to a pre-generated singularity wrapper script, or a full
  `singularity exec --bind ... <sif>` string.

Newer apps (`viper`, `aracne`, `telomerehunter2`) embed the `.sif` path directly
in `application_settings` as a `*_sif` key. Older ones indirect through
`clients.py`. Both are current; follow whichever the neighbouring apps use.

## Settings wiring (out of this skill's scope, but know it exists)

Two layers: `isabl_apps/clients.py` holds per-deployment path constants;
`isabl_apps/settings.py` maps them onto apps via `patch_application_settings`.
Applied with `isabl-apps patch-settings -c <client>`. Leave `NotImplemented`
settings for that step and flag them.

## Tests

Flat `tests/test_<tool>.py` at repo root. Shape:

```python
def test_my_app(tmpdir, datadir, commit):
    app = MyAppGRCh37()
    app.application.settings.default_client = {
        "my_tool": tmpdir.docker("org/image:tag"),
        "reference": join(datadir, "..."),
    }
    target = utils.create_experiment(method="WG", bam=..., bedfile="fake.bed")
    utils.assert_run(application=app, tuples=[([target], [])],
                     commit=commit, results=["score"])
```

Reuse an existing tuple fixture from `conftest.py` (`strelka_tuples`,
`star_tuples`, `mutect_tuples`, …) rather than inventing one.

## Worked file list (from real commits)

```
isabl_apps/apps/__init__.py              | +1     generated
isabl_apps/apps/my_new_app/__init__.py   |  0
isabl_apps/apps/my_new_app/apps.py       | +N
isabl_apps/apps/my_new_app/constants.py  | +N
isabl_apps/apps/my_new_app/docker/Dockerfile | +N
tests/test_my_new_app.py                 | +N
```

---

# shahlab_apps (Shah Lab)

## Layout — one file per pipeline, grouped by category

```
shahlab_apps/apps/<category>/
├── __init__.py          # empty
├── _<pipeline>.py       # the AbstractApplication subclasses
├── apps.py              # re-exports every class from the _*.py files
├── constants.py         # APPLICATION_X_DESCRIPTION, APPLICATION_X_RESULTS
└── versions.json        # one record per (name, version) — mandatory
```

Categories: `wgs`, `ont`, `scdna`, `scrna_apps`, `atac`, `cfdna`, `qc`, `rna`,
`spatial`, `protein`, `hmftools`, `mondrian_nf`. `apps/atac/` is the cleanest
minimal template.

Branch is the namesake (`clairs`, `wakhan_cna`, `T2T`). Unlike isabl_apps, apps
are **not** one per folder — a new pipeline is a new `_<pipeline>.py` in an
existing category.

No `SCOPES.md` here — use the app or category name as the commit scope (`ont`,
`wgs`, `signals`).

## Registration — the category's `apps.py`

`shahlab_apps/apps/__init__.py` is empty and stale; ignore it. The real surface
is the category's `apps.py`, one import line per class:

```python
from shahlab_apps.apps.ont._whatshap import ONTwhatshap
from shahlab_apps.apps.ont._whatshap import ONTwhatshapGRCh38
from shahlab_apps.apps.ont._whatshap import ONTwhatshapGRCh38P14
```

Re-export the **base class too** — `signals.py` dispatches on it. (This differs
from isabl_apps, where the base is deliberately excluded.)

A syntax or import error in any `_*.py` breaks the whole category, and therefore
signals and the CLI.

## versions.json — mandatory, and the usual way to break an import

Apps resolve pipeline versions at **class-definition time**:

```python
PIPELINE_VERSION, COMPATIBILITY = helpers.get_version_and_compatibility(NAME, VERSION)
```

`utils/versions.py` routes app name → `versions.json` via an if/elif chain of
name prefixes. **If the name doesn't match a branch it raises at import**, taking
down the category, signals and the CLI. So adding an app means both:

1. A record in the right `versions.json` — the lookup asserts **exactly one**
   match for the (name, version) pair:

```json
{
  "isabl_app_name": "ONT-WHATSHAP",
  "isabl_app_version": "0.0.1",
  "pipeline_name": null,
  "pipeline_version": null,
  "compatibility": { "ONT-NANOSEQ": ["0.0.1"], "ONT-SNV": ["0.0.1"] }
}
```

2. A routing branch in `utils/versions.py` if the name prefix is new:

```python
elif app_name.lower().startswith('atac'):
    versions_path = os.path.join(ROOT, 'apps', 'atac', 'versions.json')
```

`compatibility` maps upstream app name → acceptable versions, and is consumed by
`helpers.get_result(...)` when resolving dependencies.

## Reference paths and helpers

- Reference files go in `utils/assemblies.py` (`ASSEMBLIES`, keyed by assembly
  name), never inline in an app.
- `helpers.py` star-imports every module in `utils/`, so new shared code in a
  `utils/` module becomes visible as `helpers.<thing>` automatically.
- Per-assembly subclasses merge into the base settings:

```python
class ONTwhatshapGRCh38P14(ONTwhatshap):
    ASSEMBLY = "GRCh38-P14"
    SPECIES  = "HUMAN"
    application_settings = {**ONTwhatshap.application_settings,
                            "genome": helpers.ASSEMBLIES["GRCh38-P14"]["genome"]}
```

## Containers

Singularity inline, three styles — all current:

1. Full invocation embedded in `application_settings`:
   `"whatshap": "singularity run --bind /data1/shahs3 <...>/whatshap.sif whatshap"`
2. `singularity exec` written directly in `get_command`.
3. A pipeline wrapper that writes a config plus `run_pipeline.sh` (see
   `apps/wgs/apps.py`).

`.sif` files live under `/data1/shahs3/isabl_data_lake/software/sifs/<family>/`.

## Tests

Only five test files exist and recent app commits add none. Follow the isabl_apps
shape if you write one.

## Worked file list (from real commits)

New pipeline in an existing category:

```
shahlab_apps/apps/ont/_my_pipeline.py | +N
shahlab_apps/apps/ont/apps.py         | +1   one re-export per class
shahlab_apps/apps/ont/constants.py    | +N
shahlab_apps/apps/ont/versions.json   | +N   REQUIRED
```

New category adds `apps/<category>/__init__.py` (empty) and a routing branch in
`shahlab_apps/utils/versions.py`.
