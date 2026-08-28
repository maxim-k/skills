"""Check a Mermaid diagram obeys its own node grammar.

Every shape carries a behavioural contract borrowed from UML. This asserts each
contract mechanically, so a rule is never merely claimed. Beyond the per-node
contracts it also checks global structure: containment, empty containers, a
floating source node, and the boundary manifest.

Usage:
  python3 check_diagram.py <diagram.md>
  python3 check_diagram.py --selfcheck

A fenced block under a heading containing "legend" is treated as a key: samples
with no flow, so the behaviour rules do not apply to it.

Every non-legend block must start with a manifest comment naming its boundary
crossings:

    %% boundary: sources=Api,AssetBucket sinks=ObjectStore
"""

from collections import Counter
from pathlib import Path
import re
import sys

SHAPES = {  # opening delimiter -> kind
    "[(": "cylinder", "([": "stadium", "{{": "hexagon",
    "[/": "flag", "{": "diamond", "[": "rect",
}
NODE_RE = re.compile(
    r'\b(\w+)(\[\(.*?\)\]|\(\[.*?\]\)|\{\{.*?\}\}|\[/.*?/\]|\[.*?\]|\{.*?\})'
)
EDGE_RE = re.compile(
    r'^\s*(\w+)\s*(?:\[\(.*?\)\]|\(\[.*?\]\)|\{\{.*?\}\}|\[/.*?/\]|\[.*?\]|\{.*?\})?'
    r'\s*(?:-->|~~~)\s*(?:\|"?(.*?)"?\|)?\s*(\w+)'
)
BLOCK_RE = re.compile(r"```mermaid\n(.*?)\n```", re.S)
RANGE_RE = re.compile(r'(?<![\w:])L\d+(?:-\d+)?\b')  # a bare Lnn / Lnn-nn range
BOUNDARY_RE = re.compile(r'%%\s*boundary:\s*(.*)')


def parse(block: str):
    """Read one mermaid block into nodes, edges, containers and containment.

    :param block: The body of a fenced mermaid block.
    :type block: str
    :returns: node kind by id, node label by id, edge triples, container ids,
        innermost container id by node id ("" == top level).
    :rtype: tuple
    """
    kinds, labels, edges, subs, scope_of = {}, {}, [], set(), {}
    stack = []

    for line in block.splitlines():
        text = line.strip()
        if not text or text.startswith(("%%", "classDef", "class ", "linkStyle")):
            continue
        if text.startswith("subgraph"):
            sid = re.match(r"subgraph (\w+)", text).group(1)
            subs.add(sid)
            stack.append(sid)
            continue
        if text == "end":
            if stack:
                stack.pop()
            continue
        for node_id, body in NODE_RE.findall(text):
            if node_id in kinds:
                continue
            for opener in ("[(", "([", "{{", "[/", "{", "["):
                if body.startswith(opener):
                    kinds[node_id] = SHAPES[opener]
                    break
            quoted = re.search(r'"(.*)"', body, re.S)
            labels[node_id] = quoted.group(1) if quoted else body.strip("[](){}/")
            scope_of[node_id] = stack[-1] if stack else ""
        hit = EDGE_RE.match(text)
        if hit and "~~~" not in text:
            edges.append((hit.group(1), hit.group(2) or "", hit.group(3)))
    return kinds, labels, edges, subs, scope_of


def check_boundary(block: str, kinds: dict, into: Counter, out: Counter,
                   name: str) -> list:
    """Assert the `%% boundary:` manifest against the drawn nodes.

    :param block: The body of a fenced mermaid block.
    :param kinds: Node kind by id.
    :param into: In-degree by node id.
    :param out: Out-degree by node id.
    :param name: Name used in the report.
    :returns: One message per violation.
    :rtype: list
    """
    hit = BOUNDARY_RE.search(block)
    if not hit:
        return [f"{name}: no `%% boundary:` manifest; declare sources and sinks "
                f"on the first line"]
    decl = dict(re.findall(r'(sources|sinks)=([\w,]+)', hit.group(1)))
    bad = []
    for sid in filter(None, decl.get("sources", "").split(",")):
        if sid not in kinds:
            bad.append(f"{name}: declared source {sid} is not a node")
        elif out[sid] == 0:
            bad.append(f"{name}: declared source {sid} feeds nothing")
    for sid in filter(None, decl.get("sinks", "").split(",")):
        if sid not in kinds:
            bad.append(f"{name}: declared sink {sid} is not a node — dropped? a "
                       f"boundary crossing stays drawn even when its component "
                       f"is collapsed")
        elif into[sid] == 0:
            bad.append(f"{name}: declared sink {sid} receives nothing")
    return bad


def check(block: str, name: str) -> list:
    """Assert every grammar rule against one block.

    :param block: The body of a fenced mermaid block.
    :param name: Name used in the report.
    :returns: One message per violation.
    :rtype: list
    """
    kinds, labels, edges, subs, scope_of = parse(block)
    into, out = Counter(), Counter()
    edges_on = {}  # node id -> list of (src, label, dst) touching it
    for src, lbl, dst in edges:
        out[src] += 1
        into[dst] += 1
        edges_on.setdefault(src, []).append((src, lbl, dst))
        edges_on.setdefault(dst, []).append((src, lbl, dst))

    bad = []

    # --- global structure -------------------------------------------------
    used = set(scope_of.values())
    for sid in sorted(subs):
        if sid not in used:
            bad.append(f"{name}: container {sid} holds no node; a box earns its "
                       f"place by holding a node")

    for node in sorted(kinds):
        if RANGE_RE.search(labels.get(node, "")) and not scope_of.get(node):
            bad.append(f"{name}: {node} has a definition range but sits outside "
                       f"every container; its range points at open space")

    bad += check_boundary(block, kinds, into, out, name)

    hit = BOUNDARY_RE.search(block)
    boundary = set(re.findall(r'[\w]+', hit.group(1).replace("sources", "")
                              .replace("sinks", ""))) if hit else set()

    # --- per-node contracts ---------------------------------------------------
    for node, kind in sorted(kinds.items()):
        i, o = into[node], out[node]
        touching = edges_on.get(node, [])

        if kind == "diamond":
            if o < 2:
                bad.append(f"{name}: {node} is a diamond with {o} branch(es); a "
                           f"decision needs at least 2")
            if not labels[node].rstrip().endswith("?"):
                bad.append(f"{name}: {node} is a diamond whose label is not a "
                           f"question")

        if kind == "cylinder":
            # UML DataStoreNode: written and/or read. Every edge must name the
            # operation, so a store is never a silent pass-through.
            for src, lbl, dst in touching:
                if not lbl.strip():
                    bad.append(f"{name}: edge {src}->{dst} on store {node} is "
                               f"unlabelled; name the operation (reads / writes)")

        if kind == "flag" and i == 1 and o == 1 and node not in boundary:
            bad.append(f"{name}: {node} is a flag with one writer and one reader "
                       f"and is not a declared boundary crossing — a "
                       f"straight-through intermediate. Collapse it to a "
                       f"labelled edge, or declare it in the `%% boundary:` "
                       f"manifest if data really leaves the system there")

        if kind == "hexagon" and i and o:
            # UML Actor: bidirectional is legal for request/response, but then
            # every edge on the actor must be labelled.
            for src, lbl, dst in touching:
                if not lbl.strip():
                    bad.append(f"{name}: {node} is a bidirectional actor with an "
                               f"unlabelled edge {src}->{dst}; label each "
                               f"direction (request / response)")
                    break

        if kind == "stadium" and i == 0 and o > 0:
            fed_by_input = any(kinds.get(s) == "flag" for s, _, d in touching
                               if d == node)
            marked_entry = "entry" in labels[node].lower()
            if not (fed_by_input or marked_entry):
                bad.append(f"{name}: {node} is an action with no inflow and is "
                           f"not a declared entry point")

        if kind in ("rect", "hexagon") and i == 0 and o >= 4:
            targets = [d for s, _, d in edges if s == node]
            if targets and all(kinds.get(t) == "stadium" for t in targets):
                bad.append(f"{name}: {node} has {o} out-edges to actions and no "
                           f"in-edge — a framework hub. Draw one trigger edge per "
                           f"genuine entry point and connect the rest through "
                           f"artifacts; if the entry points are truly many, "
                           f"scope the diagram to one flow")

        if i == 0 and o == 0:
            bad.append(f"{name}: {node} is isolated")

    for src, _, dst in edges:
        for end in (src, dst):
            if end in subs:
                bad.append(f"{name}: edge {src}->{dst} touches container {end}; a "
                           f"container is structure, not an endpoint")
    return bad


def block_names(text: str) -> list:
    """Name each mermaid block after the markdown heading above it.

    :param text: The whole diagram document.
    :returns: One name per block, in document order.
    :rtype: list
    """
    names = []
    for hit in BLOCK_RE.finditer(text):
        headings = re.findall(r"^#+ +(.*)$", text[:hit.start()], re.M)
        names.append(headings[-1].strip().lower() if headings else f"block {len(names) + 1}")
    return names


def _selfcheck() -> int:
    """Assert each rule against the smallest diagram that should trip it."""
    good = (
        'flowchart LR\n'
        '%% boundary: sources=Api sinks=Store\n'
        'Api{{"api"}}\n'
        'Store{{"store"}}\n'
        'subgraph f["file.py"]\n'
        '  act(["do_thing<br/>L1-9"])\n'
        '  dec{"changed an output?"}\n'
        'end\n'
        'Api -->|"reads"| act\n'
        'act --> dec\n'
        'dec -->|"yes"| Store\n'
        'dec -->|"no"| Store'
    )
    assert check(good, "t") == [], check(good, "t")

    empty = good + '\nsubgraph g["empty.py"]\nend'
    assert any("holds no node" in m for m in check(empty, "t")), "empty container"

    floated = good.replace('  dec{', 'end\ndec{\n').replace('\nend\nAoops', '', 0)
    floated = (
        'flowchart LR\n'
        '%% boundary: sources=Api sinks=Store\n'
        'Api{{"api"}}\nStore{{"store"}}\n'
        'dec{"changed an output? L1-9"}\n'
        'subgraph f["file.py"]\n  act(["do_thing<br/>L1-9"])\nend\n'
        'Api -->|"reads"| act\nact --> dec\n'
        'dec -->|"yes"| Store\ndec -->|"no"| Store'
    )
    assert any("open space" in m for m in check(floated, "t")), "floating node"

    nomanifest = good.replace('%% boundary: sources=Api sinks=Store\n', '')
    assert any("no `%% boundary:`" in m for m in check(nomanifest, "t")), "manifest"

    nosink = good.replace('Store{{"store"}}\n', '').replace(
        'dec -->|"yes"| Store', 'dec -->|"yes"| act').replace(
        'dec -->|"no"| Store', 'dec -->|"no"| act')
    assert any("declared sink Store is not a node" in m
               for m in check(nosink, "t")), "dropped sink"

    hub = (
        'flowchart LR\n%% boundary: sources=Fw sinks=Store\n'
        'Fw["framework"]\nStore{{"store"}}\n'
        'subgraph f["f.py"]\n'
        '  a(["a<br/>L1-2"])\n  b(["b<br/>L3-4"])\n'
        '  c(["c<br/>L5-6"])\n  d(["d<br/>L7-8"])\nend\n'
        'Fw --> a\nFw --> b\nFw --> c\nFw --> d\na --> Store\n'
        'b --> Store\nc --> Store\nd --> Store'
    )
    assert any("framework hub" in m for m in check(hub, "t")), "hub"

    print("selfcheck ok")
    return 0


def main() -> int:
    """Check every mermaid block in the diagram named on the command line."""
    if len(sys.argv) == 2 and sys.argv[1] == "--selfcheck":
        return _selfcheck()
    if len(sys.argv) != 2:
        print("usage: python3 check_diagram.py <diagram.md> | --selfcheck")
        return 2

    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"no such file: {path}")
        return 2

    text = path.read_text()
    blocks = BLOCK_RE.findall(text)
    if not blocks:
        print(f"no mermaid blocks found in {path}")
        return 1

    problems = []
    for name, block in zip(block_names(text), blocks):
        kinds, _, edges, subs, _ = parse(block)
        print(f"{name}: {len(kinds)} nodes, {len(edges)} edges, "
              f"{len(subs)} containers")
        # a legend is a key: samples with no flow, so behaviour rules do not apply
        if "legend" not in name:
            problems += check(block, name)

    if problems:
        print(f"\n{len(problems)} violation(s):")
        for item in problems:
            print("  " + item)
        return 1
    print("\ngrammar: no violations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
