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
real, every edge quotes a real statement, and a validator proves the shapes obey
their own rules. Guessing produces a picture that looks authoritative and
teaches the reader something false.

Four things get decided for every element, in order: **is it in scope** (the
boundary), **does it earn a node** (membership), **where does it sit**
(containment), and only then **which shape and contract**. Shape comes last — it
says how an element that already earned its place must behave. Most diagram
faults are a membership or containment error wearing a shape question's clothes.

## Shapes come from UML, contracts included

A diagram like this is compressed, modified UML. UML's value was never the
appearance of its elements — it is that each element **prescribes behavior**. A
decision node with one outgoing edge is not a stylistic choice, it is a broken
decision node. So: **take the shape, take the behavior — the real UML behavior,
not a tighter one that happens to fit the system in front of you.** A shape
whose contract you cannot state in one checkable sentence does not enter the
vocabulary.

| Shape | UML element | Contract (checkable) |
|---|---|---|
| `([ ])` stadium | action / activity | reachable — has an incoming flow, or is a declared entry point |
| `[( )]` cylinder | data store (`«datastore»`) | persistent; every edge is labelled with its operation (`reads` / `writes`). A store the diagram never writes to just has no in-edge — one case, not the contract |
| `[/ /]` flag | activity parameter | a value at the boundary: an **input** nothing in the diagram writes, or an **output** something does. Never a mid-flow intermediate |
| `{{ }}` hexagon | actor / external system | a boundary role. One-directional if the interaction is; both directions if it is request/response — and then both edges are labelled |
| `{ }` diamond | decision node | one in, two or more guarded outflows. House rules: the label is a question, and the branches change what the system produces |
| `[ ]` rectangle | component / subsystem | shown collapsed. Its internals are out of scope; its boundary-crossing effects are not |
| subgraph | package / namespace | a module, package, or class that exists in the source. Drawn only if it holds a node. Never an edge endpoint |

Two of these were tighter in an earlier version and it cost portability: a
cylinder is a **store** — written *and* read (a SQL table, a queue, a cache; a
read-only constant is the degenerate no-write case) — and a hexagon actor
**interacts both ways** (an HTTP client sends a request and gets a response).
Use the UML contract; do not add a shape to cover the cases the narrow contract
excluded.

Adapt the vocabulary to a new domain the same way each entry was derived: name
the UML element, state the contract in one checkable sentence, add the check to
the validator in the same turn.

## The boundary — decided first, once

Before the first hop, state in the diagram's header what the system *is* — a
directory, a package, a service — and what is outside it.

- Everything outside is a **single node**: a rectangle for code you do not own
  or do not expand, a hexagon for an actor or external system. You never open it.
- You **do** draw every point where data crosses the line: a source the system
  reads, a sink it writes. Collapsing a component removes its internals from the
  picture, never its external effects — if the system's job is "produce reports
  and upload them", the upload destination is on the diagram even though the
  uploader itself is a collapsed one-hop rectangle.
- A command, script, or config the system builds for another runtime to execute
  is an **output flag and a terminal node**. Whether you then draw that runtime
  depends on the boundary: draw it if it is part of the system under study, stop
  at the flag if it is someone else's.
- `[ ]` rectangle is "not expanded *at this level*", and "this level" is
  whatever the boundary statement says. If a component would need expanding to
  answer the diagram's question, it is inside the boundary, not a rectangle.

**Declare the crossings mechanically.** The first line inside every non-legend
mermaid block is a manifest comment naming the boundary nodes:

```
%% boundary: sources=API,asset_bucket sinks=object_store
```

The validator checks that every declared source and sink is a real node with
flow in the right direction — this is what catches a sink you dropped while
collapsing the component that writes to it.

## Membership — does it earn a node

A node is a definition, a constant, a branch, or a named boundary crossing you
can point at with a `file:line`. Never a concept, a phase, or a summary.

Beyond that, an element earns a **standalone node** only if at least one holds:

- it is **read by two or more steps**, or
- it is **branched on** by a decision, or
- it is **pre-existing or persistent state** the flow reads — a store, a config
  object, a schema — as opposed to something a step in the flow produces, or
- it is a **point where data crosses the system boundary**.

An artifact produced by one step and consumed by one step, with no branch and no
second reader, **is an edge** — label the edge with the `file:line` and delete
the node. A chain of such intermediates collapses to labelled edges.

A container earns its place the same way: **a subgraph is drawn iff it holds at
least one node.** An empty namespace is a table of contents, not structure.

### Decisions specifically

The failure to avoid, verbatim from the user who caught it: *"'condition' nodes
that do not have conditions and choices and just statements."* Eight diamonds,
none with a second branch, none a question.

The opposite failure is deleting real decisions to be safe. The test is one
sentence: **a branch earns a diamond iff it changes what the system produces** —
a flag added to a command, a file written or not, a helper called with different
arguments. If it only picks which statement runs next and the outputs are
identical, it is not a diamond. Branches that then converge on one node are
normal — convergence is not a reason to drop the decision.

## Containment — where does it sit

Every node nests in the **smallest source namespace that contains what it refers
to**: a constant in its file, a method in its class, a decision in the method
whose `if` it quotes — or in the file, if that branch is in a module-level
function. A node is not always a definition, but it always has a location. A
node with a bare `L94-105` range floating outside every container points that
range at open space.

Containment is a different axis from which boxes exist. Only a real source
namespace gets a box; a box drawn to group "the external things", "the outputs",
or "everything on disk" is a caption pretending to be structure, and
`information-design` will strike it.

Nesting carries structure, so there are no `defines` or `holds` edges — the box
already says it.

## Flow — the arrows

Arrows carry flow and point the way things move. A node consumes what points at
it and produces what points away.

**The arrow follows the object, not the call.** When a step calls a helper to
get a value back, the value moves helper → caller: draw `parse_config →
build_command` even though the call reads the other way. (UML object flow: the
edge points where the token goes.)

**A source-declared edge is real and is drawn.** `a >> b`, `depends_on`,
`requires`, a registered middleware order — structure the author wrote down,
quoted like any other edge. What you do *not* draw is an edge you inferred to
make a node look reachable.

`file --defines--> class` reads fine as a sentence and says nothing about where
anything goes. Drawing predicates instead of flow is the most common way a
diagram fills up while explaining less.

## Frameworks and hidden orchestrators

An abstract base or framework that calls your code through lifecycle hooks — a
template method, a model's `save`/`clean`, a job base class — is **one node**,
not a hub. Give it one out-edge per genuine entry point it triggers.

Do **not** draw an edge from it to every method it calls just to satisfy "an
action needs an incoming flow". That inflow comes from the hook's real input: an
upstream artifact, a parameter, or the trigger itself. A value a hook returns to
the framework is a sink artifact, not a back-edge.

Collapsing the framework to one node does not absorb the *class's* data.
Configuration or reference data a hook reads — a settings object, a schema, a
lookup table — is a store with an edge into the hook. Identity constants that
only label the system (a name, a version) stay out.

If the framework exposes many co-equal entry points — dozens of routes,
commands, subscribed events — that is the signal to **scope the diagram to one
flow**, not to fan out from the node.

## Labels and references

- Node label is a name. Edge label is a verb phrase. Diamond label is a question
  ending in `?`.
- No kind prefixes such as `fn:` or `data:`. Shape carries kind; the legend
  states it once.
- A node carries its definition range on its own line, bare (`L90-139`), because
  it sits inside its file's container.
- An edge carries the `file:line` of the statement doing what it claims, because
  edges cross files.
- Color encodes exactly one thing, stated in the legend. A second visual channel
  means invoking `information-design` first, not deciding by eye.
- Default to `flowchart LR` — the long-axis rule from `information-design`: a
  landscape surface fits more before it scrolls. Use `TD` only when the system
  is a hierarchy or a dependency tree rather than a flow, and say why.

## The visual half is a separate skill

**Invoke `information-design`** — the skill itself, through the Skill tool, not
the idea of it. This skill governs what a diagram claims. That one governs
whether a reader can take it in. Run it when you add or change a visual
encoding, restyle, or render to a page. A diagram is not finished until both
have run.

## Each hop

Build one region per turn. A diagram that grows in one pass stops being
reviewable.

1. **Read the real source first.** Take definition ranges from the language's
   own parser or a symbol index (LSP, ctags, tree-sitter) — never by counting
   lines. If the system emits its own dependency graph (`terraform graph`,
   framework introspection), read that as the source of truth for edges. Quote
   real branches for conditions.
2. Rewrite the diagram in place, `%% boundary:` manifest on the first line.
   Never append a second copy.
3. Run `check_diagram.py <file.md>`. Zero violations, or fix before continuing.
4. Parse-check: `npx -y -p @mermaid-js/mermaid-cli mmdc -i x.mmd -o x.svg`.
   What fails locally also fails on the board.
5. Re-verify that every `file:line` reference resolves inside its file.
6. Invoke `information-design` whenever this hop changed an encoding or the
   rendered page.
7. Report node and edge counts, then **stop** and wait.

## Failure modes

Each of these happened, and in each the reader caught it, not the author.

- **Asserting a rule and never checking it.** The validator exists because of
  this.
- **Answering "what shape" when the fault is "whether a node".** Pass-through
  files drawn as nodes; an empty namespace drawn as a box.
- **Deleting every decision to avoid drawing a bad one.** A conditional that
  changes an output is a decision node.
- **A node floating outside every container** with a bare range pointing at open
  space.
- **Collapsing a component and losing its boundary crossing.** The imported
  helper is one node; the sink it writes to is still on the diagram.
- **Drawing one hop too far.** Modelling the runtime that executes an emitted
  command, when the boundary statement put that runtime outside.
- **The framework as a hub.** An abstract base with an edge to and from every
  method it invokes.
- **Inventing an edge to make a node reachable**, when a source-declared `>>` /
  `depends_on` was the real one, or when the node should not be there at all.
- **Not verifying against the source.** One attempt diagrammed the wrong
  directory: the prompt said "four files", the folder held five, and the
  mismatch sat in the first `ls` output unread. When target and description
  disagree, stop and ask.

## Miro

Confirmed by import, not assumed:

- Flowcharts only. Miro rebuilds the diagram as native shapes with its own
  layout, so orientation hints are advisory.
- Subgraphs, colors, and `<br/>` breaks survive the import.
- There is an unpublished shape ceiling. Miro's fix is switching to free-form,
  which **permanently breaks** the sync with the code panel. Keep each hop lean
  and warn when a diagram approaches it.
- Unconnected nodes stack vertically even under `flowchart LR`. Force a legend
  into one row with invisible `~~~` links.
- A node id that is a Mermaid reserved word (`click`, `end`, `graph`, …) breaks
  the parse. Suffix it (`clickLib`).
