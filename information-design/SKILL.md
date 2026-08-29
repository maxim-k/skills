---
name: information-design
description: >
  Review and build any visual output—a diagram, a rendered page, a slide, a
  plot—against layout and information-density rules drawn from Emil Ruder and
  Edward Tufte. Use when a visual artifact needs a design pass, when the user
  says "visual hygiene", "clean this up", "review the layout", "too busy",
  "information density", "Ruder", or "Tufte", and as the visual half of the
  system-diagram skill.
---

Two halves. Ruder governs the surface a thing sits on: measure, scale, rhythm,
weight. Tufte governs how much the marks themselves say. Run both, in that
order, because a density fix inside a broken layout is invisible.

One rule outranks the rest, and it is the reason this skill exists:

**Never assert a visual rule you cannot check.** Every failure recorded here
began as a plausible principle applied by eye. If a new encoding goes in, a
check for it goes in the same turn—a validator, a script, or at minimum a
sentence stating the rule that a reader can test against the artifact.

## Ruder: the layout

**One modular scale, one spacing unit.** Hand-picked values are the tell. A
page under review ran type from 11.5 to 20 and spacing from 8 to 56, every
value picked by hand, so nothing lined up with anything. Pick a base and a
ratio, derive every size and gap from it, and leave raw pixels only at the base
unit and breakpoints.

**One measure cannot serve two contents.** Prose wants roughly 66 to 72
characters. A wide figure wants the window. Put them in the same column and the
figure gets strangled—a 4498px diagram trapped in a 1040px prose column used
58% of an 1800px screen with free space on both sides. Prose keeps the measure;
figures break out full-bleed.

**Lay content along the surface's long axis.** Screens, slides, and board
viewports are landscape—wider than tall. Content that flows down the short axis
exhausts it and scrolls while width sits empty; the same content flowing along
the long axis fits more before the first scroll. Density is a function of the
axis you spend first.

**A typeface does one job.** Mono meant code, data, headings, labels, controls,
and captions at once, so it contrasted with nothing. Give each face a single
role and let size and weight carry hierarchy.

**Chrome ranks below content.** Controls, legends, and captions belong in their
own band at lower weight, separated by a rule. At content weight they compete
with the thing they serve.

**Resizing is not zooming.** A control that changes the viewport onto a drawing
does nothing for a drawing larger than any viewport. Zoom sets a real dimension
on the artifact so scrollbars stay honest about the extent; a CSS transform
leaves the scroll area lying about how much there is.

## Tufte: the density

**One fact, one channel.** The worst offender found so far encoded node kind
three times: the shape, a `fn:` or `data:` prefix repeated across 36 labels,
and seven fill colors. Shape already carried it. The prefixes and five of the
colors went.

**Delete what is not information.** A container labelled with the folder
already named in the title. Markers reading `hop 3` that describe the working
order rather than the system. Gridlines, borders, and frames that separate
nothing.

**Layer only when you can state the rule and check it.** This is the expensive
one, because Tufte's own advice—layer for importance—is what produced the mess.
An earlier version thickened six edges and captioned them "the spine." The set
had no rule behind it, and the question that ended it had no answer: it
emphasized one edge while leaving another alone, the same function writing the
same kind of file. Either state the layering rule in a sentence and check it
mechanically, or use no emphasis at all.

**A caption cannot rescue a set chosen by eye.** If no rule describes a group,
the group is wrong. Rewriting the caption to fit hides the fault.

## Node graphs: a complexity budget

A node graph has a size past which it stops informing and starts intimidating.
The numbers below come from two measured diagrams — one that read well, one a
reader called "anxiety, not clarity" — not a corpus. A budget is a **band**: a
diagram well under it, of a system that is not small, has folded its structure
rather than its detail. Check both directions.

- **Glance budget: ~20 nodes, ~30 edges** for a graph someone takes in at once.
- **Working budget: ~35 nodes, ~45 edges** for a diagram of one flow that a
  reader studies. Past that, the boundary spans more than one flow — scope it to
  one entry point; do not delete containers or nodes to fit.
- **Edge/node ratio.** Past ~1.45 once there are more than 20 nodes, the graph
  is over-connected: a hub to draw as its contents, or a boundary wider than one
  flow.
- **Max degree.** A node with more than ~8 edges read and written by many is a
  medium — draw the artifacts through it as nodes. A source or sink that
  connected is telling you the boundary is too wide, not that it is a hub.
- **Decision density.** Many diamonds means guards were drawn as decisions. A
  decision sends the flow to a different node; a guard that only skips a write
  or aborts is an edge.
- **Label reach.** An auto-layout engine puts an edge label at the edge's
  midpoint; the longer the edge, the further the label from both endpoints. A
  label that is a full sentence on an edge spanning the diagram is unreadable in
  place. Short phrase; if they still collide, there are too many edges.

## Where Tufte stops

Tufte argues about static graphics that must survive alone. A collaborative
surface—a shared board, a document other people restyle—behaves differently,
because a teammate who recolors a shape destroys whatever that color encoded.
Redundant encoding is defensive there rather than wasteful.

Do not apply either half blind. State the trade: on an editable surface, keep
kind in a channel that survives editing, such as shape or containment, and
treat color as decoration that an editor may destroy.

## Running a review

1. Name the faults first, with their cause. "58% width" is a finding; `.wrap
   {max-width: 1040px}` is the fault. A review that stops at symptoms produces
   fixes that miss.
2. Ruder pass, then Tufte pass. Report each as a list.
3. Separate the uncontested changes from the ones that reverse an earlier
   decision, and say which is which.
4. Apply, then state what a reader loses. Every deletion costs something;
   naming the cost is how the user judges the trade.
