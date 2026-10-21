---
name: design-system
description: >
  Layout and style for any HTML page Claude builds or edits: a report, a plan,
  a dashboard, a standalone artifact, or a template a script fills. Use
  whenever generating HTML or CSS for a page, restyling an existing page in
  this style, or when the user says "design system", "AI slop", "too busy",
  or "make it plain".
---

Pages here are utilitarian: they deliver information to colleagues as fast as
possible. This skill decides how a page looks and nothing else. What the page
says, in which order, and how it is grouped come from the request or from the
source page, and stay exactly as given.

The system is **closed**. `base.css` holds every visual value, `page.js`
holds every behavior, and a page uses only the elements listed below. When
content does not fit those elements, ask the user; never add CSS.

## Modes

- **Render:** build a new page from data and an outline that the request
  supplies. The sections, their order and their content are the request's;
  this skill only lays them out.
- **Restyle:** convert an existing page. Keep every heading with its text, its
  order and its nesting, and every value. Map each source element to the
  element set (see Restyle mapping), and change nothing else.

## Steps

1. **Start from the skeleton.** Copy the report or dashboard skeleton below.
   Paste `base.css` verbatim into the `<style>` and `page.js` verbatim into
   the last `<script>`. Set `data-seed` on `<body>` to the identifier of what
   the page is about, so every page about the same thing shares one
   fingerprint. Done when the page renders with its fingerprint.
2. **Fill it with elements from the element set.** Every tag and class in the
   page appears in the element set. Done when no other tag or class remains.
3. **Admit color and highlight.** Each meaningful chart color and each
   `<mark>` passes its admission questions, with the answers in a comment
   right before it. Done when every one has its comment, or is gone.
4. **Lint.** Run `python3 lint.py page.html` from this skill's folder; for a
   restyle, run `python3 lint.py page.html --source original.html`. Done when
   it prints nothing. Fix the page, never the linter; a finding the rules
   cannot resolve goes to the user.

For a script that fills a template, apply the steps to the template, then run
the linter on one rendered page.

## Skeletons

Report or plan:

```html
<!doctype html>
<html lang=en>
<head>
<meta charset=utf-8>
<meta name=viewport content="width=device-width, initial-scale=1">
<title>Page title, subject</title>
<link rel=stylesheet href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap">
<style>/* base.css, verbatim */</style>
</head>
<body data-seed="subject-id">
<nav class=index>
<div class=fingerprint></div>
<ol>
<li><a href="#s1">Summary</a></li>
<li><a href="#s2">Findings</a><ol><li><a href="#s2-1">...</a></li></ol></li>
</ol>
</nav>
<main>
<header><h1>Title</h1><p>One meta line: where the data came from.</p></header>
<section id=s1><h2>Summary</h2><p>...</p></section>
<section id=s2><h2>Findings</h2>
<section id=s2-1><h3>...</h3><p>...</p><table>...</table></section>
</section>
</main>
<script>/* page.js, verbatim */</script>
</body>
</html>
```

The index lists the `h2` and `h3` headings exactly as written. Headings
carry numbers only when the request or the source numbers them. The
fingerprint is the first thing in the index, so it stays in view while the
page scrolls.

Dashboard: no index, because a dashboard shows everything on one screen. The
fingerprint is the first thing in `main`.

```html
<body data-seed="subject-id">
<main>
<div class=fingerprint></div>
<header><h1>Title</h1></header>
<form class=filters>...</form>
<section><h2>Charts</h2>...</section>
<section><h2>Detail</h2><table>...</table></section>
</main>
<dialog><h2>Row title</h2><table>...</table><button>Close</button></dialog>
<script>/* the page's own code */</script>
<script>/* page.js, verbatim */</script>
</body>
```

Spacing comes from this nesting: `main`, `header` and `section` space their
children, and elements carry no margins. Keep the nesting and the spacing is
right: a section starts 48px of visible space below what precedes it, a
subsection 32px, blocks sit 20px apart, and a heading sits 8px above its
content. List items that hold blocks sit 28px apart.

`main` is centered in the window and the index sits at its left edge. Tables
and figures wider than the text column extend to the right; the text column
itself never widens.

## Element set

- **Text:** `h1` once, `h2`, `h3`, `p`, `ul`, `ol` (one level of nesting), `a`,
  `code`, `pre`, `mark`, `br`. A list item holds a line of text, or blocks
  (paragraphs, code blocks, tables, figures, figure rows) when each item is a
  unit with several parts.
- **Evidence:** `table` with `thead` and `tbody`, `tr.group` for group rows
  that the content already has, `.num` on every cell of a numeric column;
  `figure` with `img`, `svg` or `canvas` and an optional `figcaption`;
  `div.figure-row` for figures side by side on the same scale, used only when
  each figure stays legible at its share of the width. Wide figures (a
  long time series, a heatmap strip) stack one under another at full width.
- **Navigation:** `nav.index`, `div.fingerprint`.
- **Dashboard controls:** `form.filters`, `label`, `select`, `input` (search,
  number, checkbox, radio), `button`, `dialog`, and a tooltip on a chart mark.
  - A row that opens a modal does it through a link on its first cell.
  - A tooltip is the chart library's own, or an SVG `<title>` on the mark.

Prose is sentences. Weight and size are reserved for headings, so emphasis in
prose comes from sentence order. `code` is for values shown verbatim
(identifiers, paths, keys), set as in GitHub markdown: monospace at 85% on a
light grey background. It wraps at spaces like text, and `page.js` lets paths
break after a slash and comma-separated lists after a comma. A code block
(`pre`) keeps its line breaks, wraps long lines, and stays within the text
column. A `figcaption` keeps the text measure even when its figure is wider.
When rendering, headings and table headers are in sentence case; a restyle
keeps the source's wording.

## Tables

Every table has the same look: 14px text, tight rows, rules between rows.
Column widths come from the content. Numeric columns are right-aligned
(`.num`). When rendering, a numeric column has the same number of decimal
places in every cell; a restyle keeps the source's numbers exactly.

Write every table in full. `page.js` turns a table longer than 15 rows or
wider than its column into a **data table**: a search box and a Columns menu
above it (every column starts visible), headers that sort, 25 rows per page,
and a header row that stays on top while the rows scroll. Without the script
the full table shows.

A dashboard's own filters mark the rows they exclude with `data-out` and then
call `table.dispatchEvent(new Event("refresh"))`; the data table does the
rest. A React dashboard uses shadcn's Data Table with the same controls.

## Restyle mapping

| Source element | Becomes |
|---|---|
| Figure opened in a modal | the figure, inline |
| Badge, label, ribbon, tag | its text |
| Icon with no text (a check mark) | the word it stands for; the only text a restyle adds |
| Colored text (red failure, green OK) | plain text; color returns only through the color questions |
| Emoji in a heading or text | removed |
| Field label and value pairs | a table with one column per field |
| Heading levels | the heading's depth in the source's outline, skipped levels closed up; anything deeper than `h3` becomes `h3` in place |
| Bold, italic, underline in prose | plain text |
| Code block (`pre`, `pre code`) | `pre` with its line breaks; syntax colors removed |
| Site navigation (navbar, version, links to other pages) | a line of links in the `header`, after the meta line |
| Sidebar blocks with their own headings | sections after the main content, in source order |
| Logo, avatar, credits, loading text | removed |
| Two or more sibling wrappers of one kind under a heading, without headings of their own (cards, items, entries) | an `ol` with one item per wrapper; the browser numbers them, so the restyle adds no text |
| A single wrapper, layout grids, panels, dividers | their content, in order |

## Layers

A page has three **layers**: page, region (`form.filters`), overlay
(`dialog`, a dropdown, a tooltip). Each element contains only elements from a
lower layer:

- A region holds controls and text, and sits in `main` or a `section`.
- A modal drills into one row or mark and shows its details as text and
  tables under an `h2`, with one Close button. Escape and a click on the
  backdrop close it too.
- A tooltip shows the value of the mark under the pointer.

## Color

The page has black text, white ground, `#ddd` rules, link blue and highlight
yellow, all in `base.css`.

Charts follow the `dataviz` skill for form and marks, and draw in black by
default. Text inside a chart is 14px, like table text. When the chart
separates categories (control and treatment, region A and B), the categories take
`--chart-1`, `--chart-2` and onward in order, with no admission.

A color that carries meaning beyond telling categories apart (direction,
status, a threshold) or that lies outside the `--chart` tokens must pass all
five questions, with the answers in a `<!-- color: ... -->` comment before
the chart:

1. **Data, not chrome?** Only data marks get color.
2. **Does the reader act on it?** If a falling value changes nothing for the
   reader, it stays black; only the direction that matters gets color.
3. **Does black still mean one thing?** Once one direction has color, black
   must mean exactly "no change" or exactly "the other direction". Color the
   second direction only when black would have to mean both.
4. **Is there a field convention?** Use it when it exists, as with a loss in
   red in a financial table. Without one, write the reason a reader would
   agree with.
5. **Is the value also in text?** The sign, number or `↑`/`↓` stays readable
   without the color.

## Highlight

A `<mark>` is rare: one per page by default. It passes all four questions,
with the answers in a `<!-- highlight: ... -->` comment right before it:

1. **Would skimming past it cause a wrong decision?** Interesting is not
   enough.
2. **Does its position fail to say it already?** A phrase that is the first
   sentence or the heading already has the reader's attention.
3. **Is it the only one?** A second must beat the first in a direct
   comparison, or it goes.
4. **Is it a fact?** A finding, not an opinion about importance.

It marks a phrase inside a paragraph, never a heading, table cell or index
entry. A restyle adds no highlight the source did not have.

## Characters

Text is written with the punctuation of the language: commas, periods, colons
and semicolons. Lists are `ul` or `ol`. The linter rejects `·`, `•`, `|`, `/`
between spaces, `→`, `▸`, `✓`, `✗`, `★` and emoji outside `code`. `↑` and `↓`
appear only next to a number. An em dash appears only inside a sentence.

## Dashboards in React

A dashboard built with shadcn/ui pastes the two `:root` blocks of `base.css`
into its global CSS; the token names are shadcn's own. Use only the
components that match the element set: Data Table, Select, Combobox,
Checkbox, RadioGroup, Input, Button, Dialog, Tooltip, and charts. Lint a saved
copy of the rendered HTML; the CSS check does not apply there, every other
check does.

## Not covered

Dark mode and print styles do not exist: one light theme, on screen. Text
sizes are fixed and the page zooms with the browser.
