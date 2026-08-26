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
| `{ }` diamond | decision node | two or more labelled outflows, label is a question |
| `[ ]` rectangle | component | a boundary, not expanded at this level |
| subgraph | package | composition only, never an arrow endpoint |

Adapt the vocabulary to the domain, but derive each entry the same way: name
the UML element it compresses, state its contract, and add the contract to the
validator in the same turn.

The failure this prevents, verbatim from the user who caught it: *"'condition'
nodes that do not have conditions and choices and just statements."* Eight
diamonds, none with a second branch, none labelled with a question.

## Structure and flow are different channels

**Containment carries structure.** A class sits inside its file, a method
inside its class. No `defines` or `holds` edges—nesting already says it.

**Arrows carry flow, and point the way things move.** A node consumes what
points at it and produces what points away. `TSV_RESULTS → the class`, never
the reverse.

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
- Color encodes exactly one thing, stated in the legend. See
  `information-design` before adding a second visual channel.

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
6. Report node and edge counts, then **stop** and wait.

## Failure modes

Each of these happened, and in each the reader caught it rather than the
author.

- **Asserting a rule and never checking it.** Both the arbitrary emphasis color
  and the broken diamonds came from this. The validator exists because of it.
- **Writing a caption to justify a choice made by eye.** If a set cannot be
  described by a rule, the set is wrong, not the description.
- **Drawing predicates instead of flow.**
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
