---
name: design-system
description: >
  Layout and style for any HTML page Claude builds or edits: an article, a
  report, a CV, a product page, a standalone artifact, or a template a
  script fills. Use whenever generating HTML or CSS for a page,
  restyling an existing page in this style, or when the user says "design
  system", "AI slop", "too busy", or "make it plain".
---

Pages here are utilitarian: they deliver information as fast as possible.
This skill decides how a page looks and nothing else. What the page says, in
which order, and how it is grouped come from the request or from the source
page, and stay exactly as given.

The system is **closed**. `base.css` holds every visual value, `page.js`
holds every behavior, and a page uses only the elements listed below. When
content does not fit those elements, ask the user; never add CSS.

## Modes

- **Render:** build a new page from content that the request supplies. Its
  parts, their order and their nesting are the request's; this skill only
  lays them out.
- **Restyle:** convert an existing page. Keep every heading with its text, its
  order and its nesting, and every value. Map each source element to the
  element set (see Restyle mapping), and change nothing else.

## Steps

1. **Start from base.** Copy the base skeleton, and add the table of contents
   for a report (see Layouts). Paste `base.css` verbatim into the `<style>`
   and `page.js` verbatim into the last `<script>`. Done when the page
   renders.
2. **Fill it with elements from the element set.** Every tag and class in the
   page appears in the element set, and every heading has the level its
   depth gives it. Done when no other tag or class remains.
3. **Admit color and highlight.** Each meaningful chart color and each
   `<mark>` passes its admission questions, with the answers in a comment
   right before it. Done when every one has its comment, or is gone.
4. **Lint.** Run `python3 lint.py page.html` from this skill's folder; for a
   restyle, run `python3 lint.py page.html --source original.html`. Done when
   it prints nothing. Fix the page, never the linter; a finding the rules
   cannot resolve goes to the user.

For a script that fills a template, apply the steps to the template, then run
the linter on one rendered page.

## Layouts

Every page starts from **base**. A layout is base plus one addition, and the
addition moves nothing that base already placed.

Base:

```html
<!doctype html>
<html lang=en>
<head>
<meta charset=utf-8>
<meta name=viewport content="width=device-width, initial-scale=1">
<title>Title</title>
<link rel=stylesheet href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap">
<style>/* base.css, verbatim */</style>
</head>
<body>
<main>
<header><h1>Title</h1><p>...</p></header>
<section id=s1><h2>Section</h2><p>...</p></section>
<section id=s2><h2>Section</h2>
<section id=s2-1><h3>Subsection</h3><p>...</p></section>
<section id=s2-2><h3>Subsection</h3><p>...</p></section>
</section>
</main>
<script>/* page.js, verbatim */</script>
</body>
</html>
```

`main` is a text column centered in the window. Tables and charts wider than
it extend to the right; the text column itself never widens. The `header`
holds the `h1` and, when the content has them, paragraphs under it.

**Report** = base + a **table of contents** in `nav.index`, the first child
of `body`. It sits in the left column, beside `main`, and lists the `h2` and
`h3` headings exactly as written:

```html
<nav class=index>
<ol>
<li><a href="#s1">Section</a></li>
<li><a href="#s2">Section</a><ol><li><a href="#s2-1">Subsection</a></li><li><a href="#s2-2">Subsection</a></li></ol></li>
</ol>
</nav>
```

**Fingerprint**, on any layout and only when the user wants one: a
`div.fingerprint`, which `page.js` draws from `data-seed` on `<body>`. Set
`data-seed` to the identifier of what the page is about, so every page about
the same thing shares one fingerprint. It is the first thing in the table of
contents, where it stays in view while the page scrolls, or the first thing
in `main` when there is no table of contents. The browser tab icon is drawn
from the same seed, or from the title, on every page.

## Headings

A heading's level is its depth in the content's own nesting, never the size
it should look:

- `h1`: the page's title, once, in the `header`.
- `h2`: a division of the page.
- `h3`: a division of an `h2`.
- `h4`: a division of an `h3`. Content nested deeper is set as `h4`.

Each `h2`, `h3` and `h4` opens its own `section`, and the section's depth
gives its level. A level holds two or more sections, levels follow one after
another without a gap, and a heading with child sections also has content of
its own or several children. Headings carry numbers only when the content
numbers them. When rendering, headings are in sentence case; a restyle keeps
the source's wording.

Type and space each follow one ratio. Each heading level is 1.2 times the
one below it: `h4` is body text in semibold (16), `h3` 19, `h2` 23, `h1` 28.
The space before a heading grows by 4/3 per level from the 20px gap between
blocks: 27 before an `h4`, 36 before an `h3`, 48 before an `h2`. Every
heading sits 8px above its content. All of it comes from the nesting:
`main`, `header` and `section` space their children, and elements carry no
margins. Keep the nesting and the spacing is right.

## Element set

- **Text:** `h1`, `h2`, `h3`, `h4`, `p`, `ul`, `ol` (one level of nesting),
  `a`, `code`, `pre`, `mark`, `br`. A list item holds a line of text, or
  blocks (paragraphs, code blocks, tables, images, charts, rows) when each
  item is a unit with several parts; such items sit 27px apart.
- **Structure:** `header`, `section`, `nav.index`, `div.fingerprint`.
- **Pictures:** `figure` holding one image or one chart; `div.row` for
  pictures side by side.
- **Tables:** `table` with `thead` and `tbody`, `tr.group`, `.num`.

Prose is sentences. Weight and size are reserved for headings, so emphasis in
prose comes from sentence order. `code` is for values shown verbatim
(identifiers, paths, keys), set in monospace at 85% on a light grey
background. It wraps at spaces like text, and `page.js` lets paths break
after a slash and comma-separated lists after a comma. A code block (`pre`)
keeps its line breaks, wraps long lines, and stays within `main`.

## Images and charts

An **image** is a picture file: a photo, a screenshot, an illustration. It
is an `img` in a `figure`, shown at its own size, aligned left, and scaled
down only when it is wider than `main`. Its `alt` describes the picture for
a reader who cannot see it.

A **chart** is a picture drawn from data: an `svg` or a `canvas` in a
`figure`. An `svg` chart carries a `<title>` that says what it shows. A chart
may extend to the right of `main` when its data needs the length, as a long
time series or a heatmap strip does.

A **row** (`div.row`) puts pictures side by side on equal shares of `main`'s
width, used only when each one stays legible at its share. Each picture in a
row keeps the image rule within its share. On a narrow screen the row stacks.

Pictures have no captions: the heading or the sentence before a picture
names it.

## Tables

Every table has the same look: 13px text, one step below body text, tight
rows, rules between rows. Column widths come from the content.

- A table of records has a `thead` with one header cell per column and a
  `tbody` with one row per record. `tr.group` marks group rows that the
  content already has.
- A table of fields describes one thing. Up to five fields form one row with
  a column per field. More fields form a two-column table with no `thead`:
  each row holds the field name in a `th` and its value in a `td`.
- A numeric column has `.num` on every cell and is right-aligned. Its unit
  goes once in the header ("Size, GB"), so its cells hold bare numbers;
  negative numbers carry the minus sign `−`. When rendering, the column has
  the same number of decimal places in every cell; a restyle keeps the
  source's numbers exactly.
- An empty value is an empty cell.
- A cell holds text, numbers, `a`, `code` and `br`. A cell with long text is
  at least 24rem wide.
- The heading or the sentence before a table names it.

Write every table in full. `page.js` turns a table of records longer than 15
rows or wider than its space into a **data table**: a search box and a
Columns menu above it (every column starts visible), headers that sort, 25
rows per page, and a header row that stays on top while the rows scroll.

## Restyle mapping

| Source element | Becomes |
|---|---|
| Image or chart opened in a modal | the image or chart, inline |
| Caption on an image or chart | a paragraph right before it |
| Badge, label, ribbon, tag | its text |
| Icon with no text (a check mark) | the word it stands for; the only text a restyle adds |
| Colored text | plain text; color returns only through the color questions |
| Emoji in a heading or text | removed |
| Field label and value pairs | a table of fields |
| Heading levels | the heading's depth in the source's outline, skipped levels closed up; anything deeper than `h4` becomes `h4` in its own section |
| Bold, italic, underline in prose | plain text |
| Code block (`pre`, `pre code`) | `pre` with its line breaks; syntax colors removed |
| Site navigation (navbar, version, links to other pages) | a line of links in the `header`, after its paragraphs |
| Sidebar blocks with their own headings | sections after the main content, in source order |
| Logo, avatar, credits, loading text | removed |
| Two or more sibling wrappers of one kind under a heading, without headings of their own (cards, items, entries) | an `ol` with one item per wrapper; the browser numbers them, so the restyle adds no text |
| A single wrapper, layout grids, panels, dividers | their content, in order |

A restyle keeps the source's nesting even where a level holds one section.

## Color

The page has black text, white ground, `#ddd` rules, link blue and highlight
yellow, all in `base.css`.

Charts follow the `dataviz` skill for form and marks, and draw in black by
default. Text inside a chart is 13px, like table text. When the chart
separates categories, the categories take `--chart-1`, `--chart-2` and
onward in order, with no admission.

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

It marks a phrase inside a paragraph, never a heading, table cell or table
of contents entry. A restyle adds no highlight the source did not have.

## Characters

Text is written with the punctuation of the language: commas, periods, colons
and semicolons. Lists are `ul` or `ol`. The linter rejects `·`, `•`, `|`, `/`
between spaces, `→`, `▸`, `✓`, `✗`, `★` and emoji outside `code`. `↑` and `↓`
appear only next to a number. An em dash appears only inside a sentence.

## Not covered

Dark mode and print styles do not exist: one light theme, on screen. Text
sizes are fixed and the page zooms with the browser.
