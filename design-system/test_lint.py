"""Self-check for lint.py.

Usage: ``python3 test_lint.py``

Lints a good page, a bad page and a restyle against its source, all
written inline. Prints one line and exits with status 0 when every check
passes.
"""

from lint import BASE_CSS, compare, lint

GOOD = f"""<!doctype html>
<html lang=en>
<head>
<meta charset=utf-8>
<title>Release review, PROJECT-42</title>
<link rel=stylesheet href="https://fonts.googleapis.com/css2?family=Inter">
<style>
{BASE_CSS}</style>
</head>
<body data-seed="PROJECT-42">
<nav class=index>
<div class=fingerprint></div>
<ol><li><a href="#summary">Summary</a></li><li><a href="#load">Load</a></li></ol>
</nav>
<main>
<header><h1>Release review</h1><p>Data from the staging cluster.</p></header>
<section id=summary><h2>Summary</h2>
<p>The release is ready. <!-- highlight: a reader who skims past it ships
a slower build --><mark>Median latency rose by 12 ms</mark> on the API.</p>
</section>
<section id=load><h2>Load</h2>
<table><thead><tr><th>Service</th><th>Requests</th></tr></thead><tbody>
<tr><td>api</td><td class=num>1.50</td></tr>
<tr><td>web</td><td class=num>12.25</td></tr></tbody></table>
<figure><svg viewBox="0 0 10 10"><rect fill="var(--chart-1)"/>
<rect fill="#0072b2"/><rect stroke="#000"/></svg>
<figcaption>Requests per second.</figcaption></figure>
</section>
</main>
</body>
</html>"""

BAD = """<!doctype html><html><head><style>body { color: red }</style></head>
<body><main>
<section><h2>Status</h2>
<p>Done · owner is Max → next week ✓ and this sentence is long enough.</p>
<div class=card><b>Bold</b></div>
<p style="color: red"><mark>no comment</mark> and
<!-- highlight: ok --><mark>second</mark></p>
<table><thead><tr><th>Name</th><th>Value</th></tr></thead><tbody>
<tr><td>a</td><td>1.5</td></tr><tr><td>b</td><td class=num>2</td></tr>
</tbody></table>
<form class=filters><form></form></form>
<dialog><select></select></dialog>
<svg><rect fill="#ff0000"/></svg>
</section></main></body></html>"""

EXPECTED = [
    "<style> differs from base.css",
    'banned character "·"',
    'banned character "→"',
    'banned character "✓"',
    "<div> is allowed only as",
    'class "card" is not in the element set',
    "<b> is not in the element set",
    "style= attribute",
    "highlight without an admission comment",
    "more than one highlight",
    'numeric column "Value" needs class="num"',
    'numeric column "Value" mixes decimal places',
    "region inside a region",
    "controls inside a modal",
    'fill="#ff0000" without an admission comment',
]

SOURCE = """<html><body><div class=card>
<h1>Install guide</h1>
<h2>🚀 Prerequisites</h2><p>A Linux host.</p>
<h3>Hardware</h3><table><tr><td>Memory</td><td>ECC memory</td></tr></table>
<h4>Disks:</h4><p>Two disks.</p>
<h2>Steps</h2><p>Run the installer.</p>
</div></body></html>"""

RESTYLE = """<main><header><h1>Install guide</h1></header>
<section><h2>Prerequisites</h2><p>A Linux host.</p>
<section><h3>Hardware</h3>
<table><thead><tr><th>Item</th><th>Size</th></tr></thead>
<tbody><tr><td>Memory</td><td>ECC memory</td></tr></tbody></table>
<h3>Disks</h3><p>Two disks.</p></section></section>
<section><h2>Steps</h2><p>Run the installer.</p></section></main>"""


def main() -> None:
    """Run every check and stop at the first failure."""
    good = lint(GOOD)
    assert good == [], f"the good page should be clean, got {good}"

    messages = [m for _, m in lint(BAD)]
    for expected in EXPECTED:
        assert any(expected in m for m in messages), (
            f"missing finding: {expected}\ngot: {messages}"
        )
    # Sky is an Okabe-Ito color but not a chart token, so it needs an
    # admission. Each page reports one unadmitted chart, so sky gets a
    # page of its own.
    sky = lint('<svg><rect fill="#56b4e9"/></svg>')
    assert any("#56b4e9" in m for _, m in sky), f"sky passed: {sky}"

    restyled = compare(RESTYLE, SOURCE)
    assert restyled == [], f"the restyle should keep the source, got {restyled}"

    # A restyle that drops a heading, moves another and loses a value must
    # be caught.
    broken = RESTYLE.replace("<h3>Disks</h3><p>Two disks.</p>", "")
    broken = broken.replace("<h2>Steps</h2>", "")
    broken = broken.replace("<main>", "<main><h2>Steps</h2>")
    broken = broken.replace("ECC memory", "")
    found = " ".join(m for _, m in compare(broken, SOURCE))
    for expected in (
        '"disks" is missing',
        '"steps" is moved or missing',
        '"ecc memory" is missing',
    ):
        assert expected in found, f"missing source finding: {expected}\ngot: {found}"
    print(
        f"ok: good page clean, bad page gives {len(messages)} findings, "
        "restyle kept, broken restyle caught"
    )


if __name__ == "__main__":
    main()
