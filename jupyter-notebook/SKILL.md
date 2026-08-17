---
name: jupyter-notebook
description: >
  Standard for building or editing analytical Jupyter notebooks (.ipynb) --
  plot style and legends, small multiples for many-category data, grid
  layout, quantifying visual claims, grounding parameters in the real data
  distribution, table rendering, output-noise cleanup, and the two-pass
  dev-then-prod authoring workflow. Use whenever creating or substantially
  editing a notebook that does data analysis and/or visualization, when the
  user says "jupyter", "notebook", asks for plots in a notebook, or invokes
  a dataviz critique (Tufte/Cairo/Knaflic-style).
---

A notebook is read by a human, not just executed. Every result needs prose
explaining it, not just code and output sitting there. This standard governs
plot style, legends, layout, workflow, and output hygiene as one coherent
set of rules -- don't apply only part of it.

## The two-pass workflow: dev, then a real markdown-first prod pass

This is backwards from how code normally gets written, and that's
intentional:

1. Write the code, run it, look at the *real* output.
2. With the real numbers/plots in hand, write a markdown cell **before**
   the code cell stating the conclusion in plain language, using those real
   numbers -- not what you expect to find, what you actually found.
3. Clean the code cell: remove prints that are now fully redundant with the
   markdown above them. Keep short, new, or receipt-style prints (e.g.
   `"wrote 14336 rows to path"`) -- those aren't noise, they're
   confirmation the code did what the prose claims.
4. Where raw output legitimately *is* the right thing to show (a real
   table, a key number), keep it -- but the markdown-with-conclusions-first
   rule still applies. The output supplements the prose; it never replaces it.

This is an **authoring-time** process, not a runtime toggle. Don't build a
`DEV_MODE = True/False` flag into the notebook -- nobody flips it at
runtime, and a flag nobody flips is unrequested complexity. Do the two
passes yourself, ship the clean one.

Never skip straight to writing markdown you *expect* to be true. Every
number in prose must have actually been produced by the cell it precedes.

## Plot style, set up once, used everywhere

Every notebook that plots anything gets one style-setup cell near the top.
Adapt the constants, keep the pattern:

```python
%config InlineBackend.figure_format = "retina"

import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

FIGSIZE = (7, 5)
DISPLAY_DPI = 150
SAVE_DPI = 300
FONT_SIZE = 10
TITLE_SIZE = 12
POINT_ALPHA = 0.6
POINT_SIZE = 8
GRAY = "#c9c9c4"  # background / "everything else"

sns.set_theme(style="whitegrid", context="notebook")
mpl.rcParams.update({
    "figure.figsize": FIGSIZE, "figure.dpi": DISPLAY_DPI, "savefig.dpi": SAVE_DPI,
    "font.size": FONT_SIZE, "axes.titlesize": TITLE_SIZE, "axes.labelsize": FONT_SIZE,
    "xtick.labelsize": FONT_SIZE, "ytick.labelsize": FONT_SIZE,
    "legend.fontsize": FONT_SIZE, "legend.title_fontsize": FONT_SIZE,
    "lines.linewidth": 0.8, "axes.linewidth": 0.6, "grid.linewidth": 0.4,
})

FIG_DIR = Path("figures"); FIG_DIR.mkdir(exist_ok=True)

def save_fig(fig, name):
    fig.savefig(FIG_DIR / f"{name}.png", bbox_inches="tight")
```

Rules that go with it:
- Legends go **outside** the axes: `loc="upper left", bbox_to_anchor=(1.01, 1.0), frameon=False`. Never let a legend overlap data.
- Dense scatter (thousands of points) needs a much smaller marker size than
  a strip/violin plot -- don't reuse `POINT_SIZE` for both, define a
  separate small size for dense embeddings.
- Continuous variables get a colorbar (`fig.colorbar(sc, ax=ax, shrink=0.8, label=...)`), not a discretized legend.
- "The space on the screen is free" -- don't cram plots small to save
  space. Make them large enough to actually read.
- **Every plot needs both a legend (if it has color-coding of any kind,
  including a heatmap's row/column color strip) and a markdown caption.**
  No exceptions -- a dendrogram or any other "structural" plot needs the
  same explanation as a scatter plot. An uncaptioned plot is a decoration,
  not an analysis.

## More than ~7-10 categorical colors: small multiples + a real taxonomy

A human reliably reads about 7-10 categorical hues in one legend. Beyond
that, it's noise ("rainbow vomit"), not signal -- a 40-color legend means
the reader can't actually tell which dot is which.

Fix: **small multiples**, one panel per group -- full dataset plotted first
in gray for context, that panel's members highlighted on top in their own
small (<=7-hue) palette. Group by a **real domain taxonomy** (the field's
actual classification system), never an invented bucket list -- and don't
trust automated code-to-taxonomy matching blindly: the same short code can
mean two unrelated things in two different systems. Verify each mapping
against the real, known identity of what it's labeling, not by string match
alone.

If given a reference image for this, check whether it's layout-only or
style-too before copying anything from it -- a dashboard screenshot's
layout idea does not mean adopt its chrome, fonts, or color scheme. Keep
using this notebook's own established style.

Grid shape: prefer taller/narrower over wide/short for small multiples
(fewer columns, more rows) -- panels that are cramped horizontally are
harder to read than panels that are merely tall. Iterate on the actual
render; the "right" shape is found by looking, not decided once. When
someone specifies a shape verbally, confirm rows vs. columns explicitly --
matplotlib's own convention is `subplots(nrows, ncols)`, but conversational
shorthand ("4x3", "2x6") is often stated width-first instead. Don't guess.

One overlaid category dominating another (e.g. a 2.7:1+ count imbalance)
makes the minority invisible under a shared scatter -- fix with same-axis
separate panels or a gray-background/colored-highlight overlay, don't just
accept it.

## Run alternative methods independently

When comparing two methods (e.g. a linear vs. a non-linear dimensionality
reduction), run each **directly on the same underlying feature matrix**,
independently. Never chain one into the other (e.g. running method B on
method A's output coordinates) unless that composition is specifically what
was asked for. The reason this matters: if the two methods disagree, that
disagreement is real information (an artifact one method shows and the
other doesn't) -- chaining them hides it.

## Compute is not an excuse to shortcut; imbalance is handled by addition, not substitution

If told compute/time isn't a constraint, don't downsample or subset for
efficiency. Run the full data as the primary analysis.

Class/group imbalance still needs addressing -- but as a **labeled,
additional** balanced-comparison view sitting alongside the full-data
analysis, never as a silent replacement that quietly discards most of the
data. Show both, label both.

## Quantify claims -- don't eyeball a plot and assert a conclusion

A visual claim ("well mixed", "separates cleanly", "recovers the known
groups") needs an actual computed statistic behind it, not just a picture.
Use the field's standard tools for the specific claim (e.g. silhouette
score, a local-neighborhood mixing test, adjusted Rand index against known
labels -- whatever fits the domain and the claim), implemented directly
against the data. Prefer a direct implementation (sklearn/scipy-level) over
pulling in a heavy new dependency when the metric is simple enough to write
in a few lines. If a claim can't be backed by a number, say what would be
needed to check it rather than asserting it from the plot alone.

## Ground every threshold in the real data -- never assume a round number

Any cutoff/parameter a plot or analysis depends on (a variable-selection
threshold, a sample-size cap, a cluster count) must be derived from the
actual observed distribution -- percentiles, knee/elbow detection, whatever
fits -- and the derivation should be visible (e.g. plot the ranked curve
with the chosen cutoff marked), not asserted from memory or a "reasonable
default." This applies even to numbers floated early and informally in
conversation, including the user's own first-draft suggestions -- an early
rough number is a starting hypothesis, not a requirement, until the data
actually supports it. If an early sketch gets superseded by real analysis,
say so plainly rather than quietly keeping the old number.

## Tables render as tables

Never let a `pandas.Series` or dict print as a monospace text dump. Convert
to a DataFrame with clean column names and make it the cell's trailing
expression (or pass to `display()`), so Jupyter's rich HTML rendering
kicks in:

```python
# not this:
print(some_series)

# this:
some_series.rename_axis("Category").reset_index(name="Count")
```

## Kill output noise

Remove raw object reprs and dumps (e.g. an AnnData/DataFrame `__repr__`
listing every column) from the final cell -- they say nothing a reader
needs and the two-pass workflow already moved the real findings into
markdown. Keep prints that are short, genuinely new information, or a
receipt for a side effect (`"wrote N rows to path"`). If in doubt: would a
reader learn something from this print that the preceding markdown doesn't
already say? If not, cut it.

## Execution hygiene

Bugs worth guarding against explicitly, because they're easy to hit and
easy to miss:

- **Pin the kernel.** `jupyter nbconvert --execute` can silently bind to
  whatever kernel Jupyter defaults to on the machine, including an
  unrelated project's environment, if the notebook's own
  `metadata.kernelspec` isn't set correctly. Always pass
  `--ExecutePreprocessor.kernel_name=<name>` explicitly and verify
  `nb.metadata["kernelspec"]` points at the environment you actually mean
  (e.g. the project's own venv-registered ipykernel), not just whatever
  happened to be selected.
- **Make expensive deterministic build steps idempotent.** If a cell
  rebuilds something costly from source (reads thousands of files, trains
  something, etc.) and the notebook gets re-executed top-to-bottom
  repeatedly during iteration, guard it with a skip-if-output-exists check.
  Otherwise "this file is never touched again" claims become false the
  next time the notebook runs, and every re-run pays the full cost again.
- **Background long executions correctly.** When running a long
  `nbconvert --execute` in the background, background the actual
  long-running command directly. Don't `nohup ... &` it *inside* an
  already-backgrounded shell call -- that detaches the real process from
  tracking, and the completion notification you get back is for the
  wrapper script (which returns almost instantly), not the real job. If
  that happens, find the actual PID and wait on it directly.
- **Verify "unchanged" claims, don't assume them.** Check a file's mtime
  (and ctime, since mtime alone can be ambiguous) against a known-good
  reference before asserting a supposedly-immutable artifact wasn't
  touched by a run. A clean exit code proves the notebook ran without
  error, not that a specific file was left alone.
