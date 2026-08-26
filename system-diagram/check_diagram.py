"""Check a Mermaid diagram obeys its own node grammar.

Every shape carries a behavioural contract borrowed from UML. This asserts each
contract mechanically, so a rule is never merely claimed.

Usage:  python3 check_diagram.py <diagram.md>

A fenced block under a heading containing "legend" is treated as a key: samples
with no flow, so the behaviour rules do not apply to it.
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


def parse(block: str):
    """Read one mermaid block into nodes, edges and container ids.

    :param block: The body of a fenced mermaid block.
    :type block: str
    :returns: node kind by id, node label by id, edge triples, container ids.
    :rtype: tuple
    """
    kinds, labels, edges, subs = {}, {}, [], set()

    for line in block.splitlines():
        text = line.strip()
        if not text or text.startswith(("%%", "classDef", "class ", "linkStyle")):
            continue
        if text.startswith("subgraph"):
            subs.add(re.match(r"subgraph (\w+)", text).group(1))
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
        hit = EDGE_RE.match(text)
        if hit and "~~~" not in text:
            edges.append((hit.group(1), hit.group(2) or "", hit.group(3)))
    return kinds, labels, edges, subs


def check(block: str, name: str) -> list:
    """Assert every grammar rule against one block.

    :param block: The body of a fenced mermaid block.
    :type block: str
    :param name: Name used in the report.
    :type name: str
    :returns: One message per violation.
    :rtype: list
    """
    kinds, labels, edges, subs = parse(block)
    into, out = Counter(), Counter()
    for src, _, dst in edges:
        out[src] += 1
        into[dst] += 1

    bad = []
    for node, kind in sorted(kinds.items()):
        i, o = into[node], out[node]

        if kind == "diamond":
            if o < 2:
                bad.append(f"{name}: {node} is a diamond with {o} branch(es); a "
                           f"decision needs at least 2")
            if not labels[node].rstrip().endswith("?"):
                bad.append(f"{name}: {node} is a diamond whose label is not a "
                           f"question")
        if kind == "cylinder":
            for src, _, dst in edges:
                if dst == node and kinds.get(src) != "cylinder":
                    bad.append(f"{name}: {node} is data with an in-edge from {src}; "
                               f"data is consumed, not produced")
        if kind == "flag" and i == 0:
            bad.append(f"{name}: {node} is an artifact with no in-edge; nothing "
                       f"writes it")
        if kind == "hexagon" and i and o:
            bad.append(f"{name}: {node} is an external system that is both source "
                       f"and sink")
        if kind == "stadium" and i == 0:
            bad.append(f"{name}: {node} is a function with no caller")
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
    :type text: str
    :returns: One name per block, in document order.
    :rtype: list
    """
    names = []
    for hit in BLOCK_RE.finditer(text):
        headings = re.findall(r"^#+ +(.*)$", text[:hit.start()], re.M)
        names.append(headings[-1].strip().lower() if headings else f"block {len(names) + 1}")
    return names


def main() -> int:
    """Check every mermaid block in the diagram named on the command line."""
    if len(sys.argv) != 2:
        print("usage: python3 check_diagram.py <diagram.md>")
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
        kinds, _, edges, subs = parse(block)
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
