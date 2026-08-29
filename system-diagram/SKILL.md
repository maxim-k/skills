---
name: system-diagram
description: >
  Build a Mermaid diagram of a real system—a codebase, a pipeline, an
  infrastructure layout—with a node grammar borrowed from UML and enforced by
  a validator, drawn at system altitude against the real source. Use when the user
  asks for a diagram, a schema, a graph, or a visual map of how something works,
  and when a diagram targets Miro or another board.
---

A diagram of a system is a claim about that system. Every node names something
real, every edge quotes a real statement, and a validator proves the shapes obey
their own rules. Guessing produces a picture that looks authoritative and
teaches the reader something false.

Decide, in order: **what is in scope** (the boundary), **how high to fly**
(altitude), **does an element earn a node** (membership), **where does it sit**
(containment), and only then **which shape and contract**. Shape comes last — it
says how an element that already earned its place must behave. Most diagram
faults are an altitude, membership, or containment error wearing a shape
question's clothes. The commonest by far: drawing the code instead of the
system, so every `if` becomes a diamond and every helper a node.

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
| `[/ /]` flag | activity parameter | a value at the boundary: an **input** nothing in the diagram writes, or an **output** something does — one declared in the manifest, tested for in the source, or read across entry points. Never an unnamed mid-flow value |
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

**Declare the crossings mechanically.** Every non-legend mermaid block carries a
manifest comment near the top (after the `%%{init}%%` directive and `flowchart`
line) naming the boundary nodes:

```
%% boundary: sources=API,asset_bucket sinks=object_store
```

The validator checks that every declared source and sink is a real node with
flow in the right direction — this is what catches a sink you dropped while
collapsing the component that writes to it.

## Altitude — the function is the atom

A system diagram shows **how data moves between the parts of a system** — what
each part takes in and what it hands on. It does not show what happens *inside* a
part, however much that is.

**Pick the altitude from the question.** "How does this system work" → the parts
the work passes through. "How does the pricing rule fire" → a lower diagram of
one part, its branches opened. A system with real branching that lives inside a
few large functions is asking for the lower diagram — say so rather than
flattening it to three boxes and an arrow.

**A function (or method, task, resource, handler) is a black box.** Its node
carries a name — a verb for a function, a noun for a store or a resource — and a
definition range. Edges in are what it reads — arguments, files, constants, the
results of other functions. Edges out are what it produces — its return value, a
file it writes, data it hands to the next function. The branches, loops, and
local variables inside it are **not diagram elements, even when they determine
the output.** `def f(a): ...; return c` is one node, one edge in from `a`, one
edge out to `c` — whether `c` is computed straight through, picked by an `if`,
or accumulated in a loop, the diagram is the same.

**A branch is a decision node only when it sends the flow to a different node.**
Two branches that land on the same node are one edge, whatever differs between
them along the way. So:

- an **orchestrator's body picks which function runs next** — `if valid:
  process() else: quarantine()` routes to two different nodes → diamond. But a
  dispatch over many co-equal cases — a router table, a subcommand switch, a
  registry lookup — is not a fan of diamonds and not one fat one; it is the
  signal to scope the diagram to one flow.
- a **branch produces a different output node** — one path writes
  `merged.tsv`, the other writes nothing there; one registers two results, the
  other registers one *to a different sink*. Different node out → diamond.

**Still not a diamond, even when a write differs:** a guard that skips a write to
leave an artifact the flow already produced alone (`if isfile`, `if not empty`,
`if files:`, an early `return`); a branch that decides only whether an
already-produced artifact is *additionally* copied to a mirror or backup — even
one in the manifest; an `assert` / `raise` / abort path. The artifact exists
either way; only a second location, or the run surviving, differs — fold it onto
the edge.

Expect few diamonds — a handful at most. Zero, on a system with real forks,
means the branches were read as inner detail.

### What altitude does not remove

Altitude is about not opening functions. It never licenses dropping the
structure around them. A validator `WARN:` is answered by **scoping the diagram
to one entry point**, or by drawing a hub as its contents — never by deleting
one of these:

- **Every source namespace inside the boundary that holds a drawn node is a
  container** — a file, a module, a package, or a class holding drawn methods
  (nested in whatever container holds *it*; see Containment). A collapsed
  out-of-boundary import is a bare rectangle, never a box. A subsystem inside the
  boundary that the question does not reach is one collapsed rectangle with its
  boundary crossings still drawn — that is the scaling mechanism, not deleting
  nodes.
- **Every function, method, task, or resource that transforms data is a node** —
  including one called from a single place. Only a one-line pass-through wrapper
  folds into its caller.
- **Every named module-level constant, table, or schema the flow reads is a
  node**, in its namespace — a settings object, a lookup table, a result schema;
  however few readers it has. A literal written inline inside one function as a
  local detail — a regex, a format string, a header list — is not.
- **Every artifact that crosses the boundary is a node** — one that is in the
  `%% boundary:` manifest, or that a different entry point reads than wrote it.
  An unnamed value handed straight from one function to the next is an edge.
- **A data source read by two or more functions is one node** with an edge to
  each — never inlined into two edge labels, never duplicated. Its degree is
  telling you how wide the boundary is, not that it is a hub to break up.

If the diagram is over budget with all of that drawn, the boundary spans more
than one flow — scope it to one entry point. If it is *under* budget on a system
that is not small, structure was folded — walk this list.

### The numbers

`information-design` states the budget; `check_diagram.py` warns past it. One
triple, used everywhere: **~35 nodes**, **~45 edges**, **ratio ~1.45** once past
20 nodes; plus **any node over 8 edges**. Each asks whether the boundary is one
flow or several — answer by scoping to one entry point or drawing a hub as its
contents, not by folding structure. These come from two measured diagrams (one
that read well, one called overwhelming), not a corpus — treat them as a
direction, not a line.

## Membership — does it earn a node

A node is a definition, a constant, a branch, or a named boundary crossing you
can point at with a `file:line`. Never a concept, a phase, or a summary.

Beyond that, an element earns a **standalone node** only if at least one holds:

- it is a **function that transforms data** (see Altitude — one call site is
  enough), or
- it is **read by two or more functions**, or
- it is **pre-existing or persistent state** the flow reads — a store, a config
  object, a schema, a lookup table — as opposed to something a function
  produces, or
- it is an **artifact that crosses the system boundary**.

An artifact produced by one step and consumed by one step, with no branch and no
second reader, **is an edge** — label the edge with the `file:line` and delete
the node. A chain of such intermediates collapses to labelled edges.

**A shared medium is drawn as its contents, not as one node.** A filesystem, a
queue, a bus, a database that many functions read and write: **promote the
individual artifacts that pass through it to nodes**, each with a producer edge
in and a consumer edge out. Replacing the medium with direct function→function
edges deletes the artifacts instead of drawing them — that is the opposite of
this rule. One node that every function connects to is a picture of the medium,
not the flow, and always the worst hub. Draw the medium itself only when its own
behaviour — contention, ordering, durability — is what the diagram is about.

A container earns its place the same way: **a subgraph is drawn iff it holds at
least one node.** An empty namespace is a table of contents, not structure.

### Decisions specifically

The failure to avoid, verbatim from the user who caught it: *"'condition' nodes
that do not have conditions and choices and just statements."* Eight diamonds,
none with a second branch, none a question.

The opposite failure is opening a function to draw its inner `if`s. **Altitude
settles this: a branch is a diamond only when it selects which function runs or
whether a whole output exists — never when it only shapes the value on an edge
that exists anyway.** A diamond's label is a question; its branches are guarded;
they may converge on one node afterward and usually do.

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

- Node label is a name. Edge label is a **short verb phrase plus one
  `file:line`** — "reads report files (apps.py:150)", not "reads:
  {ind}_research/_clinical/.html, *.json (apps.py:150-160)". A label the layout
  engine strands at the midpoint of a long edge is unreadable; a label that is a
  sentence is a paragraph the reader chases down a diagonal. Over ~60 characters
  means either the label or the edge count is wrong. Diamond label is a question
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
- Set a translucent edge-label background so a label does not punch a hole in
  the line it annotates. First line of the block:
  `%%{init: {'themeVariables': {'edgeLabelBackground': 'rgba(255,255,255,0.75)'}, 'flowchart': {'curve': 'basis'}}}%%`

## The visual half is a separate skill

**Invoke `information-design`** — the skill itself, through the Skill tool, not
the idea of it. This skill governs what a diagram claims. That one governs
whether a reader can take it in. Run it when you add or change a visual
encoding, restyle, or render to a page. A diagram is not finished until both
have run.

## Building it

One diagram, at the altitude the boundary and the question set. Build it in one
turn; if it will not come in under budget even fully collapsed, split into
per-region hops and build one per turn — but reach for that only when the
collapsed single diagram genuinely does not fit.

1. **Read the real source first.** Take definition ranges from the language's
   own parser or a symbol index (LSP, ctags, tree-sitter) — never by counting
   lines. If the system emits its own dependency graph (`terraform graph`,
   framework introspection), read that as the source of truth for edges. Quote
   real branches for conditions.
2. Write the diagram: `%%{init}%%` directive, `flowchart LR`, `%% boundary:`
   manifest, then the body. Rewrite in place — never append a second copy.
3. Run `check_diagram.py <file.md>`. Zero violations. A `WARN:` asks whether the
   boundary is one flow — answer it in your report: name the hub you drew as
   contents, the entry point you scoped to, or why the diagram is legitimately
   this size. Never answer a `WARN:` by deleting a container, a function node, a
   constant, or a boundary artifact.
4. Parse-check: `npx -y -p @mermaid-js/mermaid-cli mmdc -i x.mmd -o x.svg`.
   What fails locally also fails on the board.
5. Re-verify that every `file:line` reference resolves inside its file.
6. Invoke `information-design` over the result.
7. Report: node and edge counts; **and** the count of files, classes,
   module-level constants and functions inside the boundary — far fewer nodes
   than that means structure was folded, walk "What altitude does not remove".
   List the branches you folded that change what a deliverable *contains* — they
   belong in prose beside the diagram, not in it. Then **stop** and wait.

## Failure modes

Each of these happened, and in each the reader caught it, not the author.

- **Asserting a rule and never checking it.** The validator exists because of
  this.
- **Answering "what shape" when the fault is "whether a node".** Pass-through
  files drawn as nodes; an empty namespace drawn as a box.
- **Opening functions.** Every inner `if` a diamond, every one-line wrapper a
  node, the shared filesystem one 11-edge hub. Accurate and unreadable. A
  function is a black box — what goes in, what comes out, not the machinery.
- **Folding the structure to hit the budget.** Files not drawn as containers, a
  class flattened into its file, constants folded into edge labels, the
  boundary artifacts shown only as arrow text. Graspable and uninformative — the
  budget was read as a quota. A `WARN:` is answered by scoping the boundary, not
  by thinning the frame.
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
- The `%%{init}%%` `themeVariables` survive a `mmdc` render but Miro applies its
  own theme on import, so keep the diagram legible without the translucent-label
  trick too — mainly by having few enough edges that no label is stranded.
