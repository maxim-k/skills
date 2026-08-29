# Rewiring the caller

A Toil pipeline is launched by something. For an Isabl shop that something is an
`AbstractApplication` subclass whose `get_command` builds a
`toil_<tool> <subcommand> --flag value …` string via
`isabl_apps.toil.build_toil_command`. Step 7 swaps that for a Nextflow launch.
The pattern generalises to any caller.

## The one rule

**The output-file contract does not change.** The Nextflow pipeline writes the
same filenames into the same output directory the Toil pipeline did. The
caller's result-collection code (`get_analysis_results`, an `output` glob, a
downstream job) stays untouched. Only the launch command changes.

## Isabl mechanism

`isabl_apps/nextflow/utils.py:create_nextflow_script` already exists (the
`sarek` app uses it). It writes a `.script.sh` that runs
`nextflow run <nf_tool> -config … -revision … -profile … --key value …` and
returns `bash <script>`.

In `apps/<tool>/apps.py:get_command`, replace the `build_toil_command(...)`
call with:

```python
from isabl_apps.nextflow.utils import create_nextflow_script

return create_nextflow_script(
    outdir=analysis["storage_url"],
    settings=settings,
    nf_tool=settings.nf_<tool>,            # git URL or local path
    nf_version=settings.nf_<tool>_revision,
    nf_profile=settings.nf_profile,
    nf_params={
        "step": self.<step_attr>,
        "outdir": analysis["storage_url"],
        # every --flag value the Toil command passed, as a param
        ...
    },
    params_as_json=True,                   # writes -params-file, avoids quoting hell
)
```

### `application_settings`

- **Drop** `toil`, `toil_<tool>`, `toil_batch_system`.
- **Add** `nf_<tool>` (the pipeline git URL `org/repo` or a local path),
  `nf_<tool>_revision` (tag/branch — pin it), `nf_profile` (the cluster
  executor profile), `nf_workdir` (scratch).
- **Keep** every reference-file / panel setting unchanged.
- Leave new deployment-specific values `NotImplemented`; they get filled by
  `isabl-apps patch-settings`.

### Version bump

Bump the app `VERSION` (minor is enough: `1.4.x` → `1.5.0`). A new version is a
**new Isabl application row** — existing Toil analyses stay on the old version,
new ones use Nextflow. This is the desired behaviour, not a migration.

### Left unchanged

`get_analysis_results`, `get_after_completion_status`, `validate_experiments`,
any `merge_*` methods, `constants.APPLICATION_RESULTS`, the app-local
`signals.py`. If a helper (e.g. a pre-flight `compute_<params>` duplicate of
pipeline math) lives in the app's `utils.py`, keep it but note it must stay in
sync with the `bin/` script.

### Restart semantics

Toil `--restart` + a per-subcommand job store → Nextflow `-resume` + a
per-analysis `-work-dir`. `create_nextflow_script` adds `-resume` when
`settings.get("restart")` is set. The per-subcommand jobstore cleanup logic in
the old `get_command` mostly disappears; keep any step that stages a chosen
input directory (a "finalise picks a solution dir" step).

### Environment

`nextflow` needs `JAVA_HOME` (or `java` on `PATH`) in the non-interactive shell
the caller runs. Set it via the caller's `bindpaths` setting or the
`nextflow.config` wrapper, not by assuming an interactive profile is sourced.

## Tests

Add a `get_command`-shape assertion to the app's test file: run `get_command`
with fake settings, assert the string contains `nextflow run`, the pipeline
identifier, `--step <x>`, and each mapped param. Isabl app test files often have
none that touch `get_command`.
