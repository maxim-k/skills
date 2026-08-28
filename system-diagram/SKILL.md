---
name: system-diagram
description: >
  Build a Mermaid diagram of a real system—a codebase, a pipeline, an
  infrastructure layout—with a node grammar borrowed from UML and enforced by
  a validator, drawn one hop per turn against the real source. Use when the user
  asks for a diagram, a schema, a graph, or a visual map of how something works,
  and when a diagram targets Miro or another board.
---

A diagram of a system is a claim about that system. Every node names something
real, every edge quotes a real statement, and a validator proves the shapes
obey their own rules. Guessing produces a picture that looks authoritative and
teaches the reader something false.

## Shapes come from UML, contracts included

This is the idea the whole skill rests on. A diagram like this is a compressed,
modified UML—and UML's value was never the appearance of its elements, it is
that each element **prescribes behavior**. A decision node with one outgoing
edge is not a stylistic choice, it is a broken decision node.

So: **take the shape, take the behavior.** A shape whose contract you cannot
state in one checkable sentence does not enter the vocabulary.

| Shape | Compresses | Contract |
|---|---|---|
| `([ ])` stadium | action, activity | has an invoker |
| `[( )]` cylinder | datastore | consumed, never produced |
| `[/ /]` flag | input/output | something writes it |
| `{{ }}` hexagon | external actor | source or sink, never both |
| `{ }` diamond | decision node | two or more labelled outflows, label is a question; branches may share a target |
| `[ ]` rectangle | component | a boundary, not expanded at this level |
| subgraph | package | a real module, package, or class; composition only, never an arrow endpoint |

Adapt the vocabulary to the domain, but derive each entry the same way: name
the UML element it compresses, state its contract, and add the contract to the
validator in the same turn.

The failure this prevents, verbatim from the user who caught it: *"'condition'
nodes that do not have conditions and choices and just statements."* Eight
diamonds, none with a second branch, none labelled with a question.

The opposite failure is deleting decisions that are real. A branch counts when
it changes **what the system produces**—a flag added to a command, a file
written or not, a helper called with different arguments—even when both branches
flow on to the same node. Four diamonds in the `expanded_genomics` baseline
survive on that test: a matched-normal check that adds `--unmatched` to the
command, an html-pair check that registers one report or two, a project-id check
that runs the t-SNE with or without a purity filter, and an individual-passed
check that concatenates the tables or only globs them. Rule: if a conditional
changes an output, it is a diamond; if it only picks which statement runs next
and the outputs are identical, it is not.

A command, script, or config file the system builds for something else to run is
a flag, and it is terminal—draw it as the output of the method that assembles it
and stop. The external runtime that consumes it (an HPC job, a shell, a
scheduler) is one hop past the boundary and is not drawn.

## Structure and flow are different channels

**Containment carries structure.** A class sits inside its file, a method
inside its class. No `defines` or `holds` edges—nesting already says it. A
subgraph is only ever a file, package, or class that exists in the source. A box
drawn to group "the external things," "the outputs," or "everything on disk" is
not structure—it is a caption pretending to be one, and `information-design`
will strike it.

That rule is about which boxes you draw, not which nodes go in them. Every node
nests in the container holding the source it refers to—a constant in its file, a
diamond in the class if the branch is in a method or in the file if it is in a
module function. A diamond is not a `def`, but it has a location; one floating
outside every container leaves its bare `L94-105` pointing at open space.

**Arrows carry flow, and point the way things move.** A node consumes what
points at it and produces what points away. `TSV_RESULTS → the class`, never
the reverse.

The call graph is not the flow graph. When a method calls a helper to get a
value back, the value flows from the helper to the caller: draw
`get_purities → generate_tsne`, though the call reads the other way. The arrow
follows the data.

An artifact written by one node and read by one node in the same flow, with no
branch between them and no second consumer, carries no more than an edge does.
Label the edge with the file and delete the node. A node earns its place by
being read twice, branched on, or crossing the boundary.

A framework or abstract base that invokes lifecycle hooks—a template method, a
Django `save`/`clean`, an Isabl `AbstractApplication`—is not a control-flow hub.
Draw it as one bounded node with only the trigger edges it genuinely
originates, usually one per lifecycle entry point (`runs the analysis`, `runs
the project merge`). The hooks it calls do not call each other; connect them
through the artifacts they read and write, never hook → hook. "A function needs
a caller" is then satisfied by an upstream artifact, an input, or that single
trigger—not by a fan-out from the base. The dict a registration hook returns is
a flag the hooks write to (`registered results`), not an edge back to the
framework.

Collapsing the framework to one node does not absorb the class's data. A class
attribute carrying data a hook reads—a settings dict, a results schema, a skip
list—is a datastore (cylinder) with an edge into the hook that consumes it. Only
the scalar metadata (`NAME`, `VERSION`, `ASSEMBLY`) is plumbing and stays out.

`file --defines--> class` reads fine as a sentence and says nothing about where
anything goes. Drawing predicates instead of flow is the most common way a
diagram fills up while explaining less.

## Labels and references

- Node label is a name. Edge label is a verb phrase. Diamond label is a
  question ending in `?`.
- No kind prefixes such as `fn:` or `data:`. Shape carries kind, the legend
  states it once.
- A node carries its definition range on its own line, bare (`L90-139`),
  because it sits inside its file's container.
- An edge carries the line of the statement doing what it claims, qualified
  with a filename (`apps.py:173`), because edges cross files.
- Color encodes exactly one thing, stated in the legend. Adding a second
  visual channel means invoking `information-design` first, not deciding by
  eye.
- Lay the flow left to right (`flowchart LR`)—the long-axis rule from
  `information-design`: a landscape surface fits more before it scrolls. Miro
  reflows on import, but the source still reads left to right.

## The visual half is a separate skill

**Invoke `information-design`**—the skill itself, through the Skill tool, not
the idea of it. This skill governs what a diagram claims. That one governs
whether a reader can take it in: measure and scale on the surface it sits on,
and how many channels the marks spend on one fact.

Run it when you add or change a visual encoding, restyle the diagram, or render
it to a page. A diagram is not finished until both have run.

## Each hop

Build one region per turn. A diagram that grows in one pass stops being
reviewable.

1. **Read the real source first.** Take definition ranges from the AST, never
   by estimate. Quote real branches for conditions.
2. Rewrite the diagram in place. Never append a second copy.
3. Run `check_diagram.py <file.md>`. Zero violations, or fix before continuing.
4. Parse-check: `npx -y -p @mermaid-js/mermaid-cli mmdc -i x.mmd -o x.svg`.
   What fails locally also fails on the board.
5. Re-verify that every `file:line` reference resolves inside its file.
6. Invoke `information-design` over the result whenever this hop changed an
   encoding or the rendered page.
7. Report node and edge counts, then **stop** and wait.

## Failure modes

Each of these happened, and in each the reader caught it rather than the
author.

- **Asserting a rule and never checking it.** Both the arbitrary emphasis color
  and the broken diamonds came from this. The validator exists because of it.
- **Writing a caption to justify a choice made by eye.** If a set cannot be
  described by a rule, the set is wrong, not the description.
- **Drawing predicates instead of flow.**
- **Deleting every decision to avoid drawing a bad one.** Over-reading the
  broken-diamond warning and ending with zero diamonds when the source has four
  real forks. A conditional that changes an output is a decision node.
- **Drawing one hop too far.** Modelling the HPC job that runs the emitted
  command, or wrapping the one-hop imports in an "external" subgraph. The
  emitted command is a terminal flag; the imports are loose rectangles.
- **A node for every intermediate file.** Pass-through artifacts—written once,
  read once, no branch—belong on the edge, not in the graph.
- **The framework as a hub.** An abstract base with an edge to and from every
  method it invokes. It is one node with a trigger edge per lifecycle entry
  point and no in-edges; the methods connect through their artifacts.
- **Not verifying against the source.** One attempt diagrammed the wrong
  directory entirely: the prompt said "four files," the named folder held five,
  and the mismatch sat in the first `ls` output unread. When the target and the
  description disagree, stop and ask.

## Miro

Confirmed by import, not assumed:

- Flowcharts only. Miro rebuilds the diagram as native shapes and applies its
  own layout, so orientation hints are advisory.
- Subgraphs, colors, and `<br/>` breaks all survive the import.
- There is an unpublished shape ceiling. Miro's own fix is switching to
  free-form, which **permanently breaks** the sync with the code panel. Keep
  each hop lean and warn when a diagram approaches it.
- Unconnected nodes stack vertically even under `flowchart LR`. Force a legend
  into one row with invisible `~~~` links.
