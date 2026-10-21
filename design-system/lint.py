"""Check a page built with the design system.

Usage: ``python3 lint.py page.html [--source original.html]``

Prints one finding per line and exits with status 1 when it finds any.
With ``--source``, it also checks that a restyle kept the headings of the
original page in order, and every table value. It reads ``base.css`` from
its own folder.

Exports ``lint`` (findings for one page) and ``compare`` (findings for a
restyle against its source).
"""

import argparse
import difflib
import html as htmllib
import re
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

__all__ = ["compare", "lint"]

BASE_CSS = Path(__file__).with_name("base.css").read_text()
FONT_LINK = "https://fonts.googleapis.com/"

TAGS = {
    "html", "head", "meta", "title", "link", "style", "script", "body",
    "nav", "main", "header", "section", "div",
    "h1", "h2", "h3", "p", "ul", "ol", "li", "a", "code", "pre", "mark",
    "br", "wbr",
    "table", "thead", "tbody", "tr", "th", "td",
    "figure", "figcaption", "img", "svg", "canvas",
    "form", "label", "select", "option", "input", "button", "dialog",
}  # fmt: skip
CLASSES = {"index", "fingerprint", "figure-row", "num", "group", "filters"}
DIV_CLASSES = {"fingerprint", "figure-row"}
# Chart libraries draw the content of these elements, so the linter
# does not check it.
OPAQUE = {"svg", "canvas", "script", "style"}
# Literal text, where separators and arrows are data.
VERBATIM = {"code", "pre"}
# A modal shows details only. Its one Close button is not a control here.
CONTROLS = {"form", "select", "input"}
VOID = {"meta", "link", "br", "wbr", "img", "input"}
HEADINGS = {"h1", "h2", "h3", "h4", "h5", "h6"}

BANNED = re.compile(r"[·•|→▸►✓✔✗✘★☆]|\s/\s|[\U0001F300-\U0001FAFF☀-➿]")
STRAY_ARROW = re.compile(r"[↑↓](?!\s?[−\-+]?\d)")
NUMBER = re.compile(r"^[↑↓]?\s?[−\-+]?[\d,]*\.?\d+\s?%?$")
TOKENS = (
    "var(--chart-",
    "var(--foreground",
    "var(--background",
    "var(--border",
)


def normalize(css: str) -> str:
    """Collapse whitespace, so that formatting is not a change."""
    return re.sub(r"\s+", " ", css).strip()


def _admitted_colors(css: str) -> set[str]:
    # Black, white, the rule gray and the chart colors need no admission.
    palette = dict(re.findall(r"--(palette-[\w-]+):\s*(#[0-9a-fA-F]+)", css))
    names = ["palette-black", "palette-white", "palette-gray"]
    names += re.findall(r"--chart-\d+:\s*var\(--(palette-[\w-]+)\)", css)
    colors = {"none", "currentcolor", "black", "white"}
    for value in (palette[name].lower() for name in names):
        colors.add(value)
        if len(value) == 4:
            colors.add("#" + "".join(c * 2 for c in value[1:]))
    return colors


ADMITTED = _admitted_colors(BASE_CSS)


@dataclass
class Cell:
    """One table cell, as the linter sees it."""

    num: bool
    span: bool
    text: str = ""


@dataclass
class Table:
    """The header and body cells of one table."""

    header: list[str] = field(default_factory=list)
    rows: list[list[Cell]] = field(default_factory=list)
    row: list[Cell] | None = None
    cell: Cell | None = None
    in_head: bool = False


class Linter(HTMLParser):
    """Collect findings for one page."""

    def __init__(self, restyle: bool = False) -> None:
        """Create a linter.

        :param restyle: The page is a restyle. A restyle keeps the
            numbers of its source exactly, decimal places included.
        """
        super().__init__(convert_charrefs=True)
        self.restyle = restyle
        self.findings: list[tuple[int, str]] = []
        self.stack: list[str] = []
        self.last_comment = ""
        self.color_comment = False
        self.marks = 0
        self.tables: list[Table] = []

    def report(self, message: str) -> None:
        """Add a finding at the current line."""
        self.findings.append((self.getpos()[0], message))

    def opaque(self) -> bool:
        """Return True inside an element whose content is not checked."""
        return any(t in OPAQUE for t in self.stack)

    # Structure

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Check one start tag, and track the open elements."""
        a = dict(attrs)
        if self.opaque():
            self.check_svg_color(a)
            if tag not in VOID:
                self.stack.append(tag)
            return
        classes = set((a.get("class") or "").split())
        if tag not in TAGS:
            self.report(f"<{tag}> is not in the element set")
        for cls in sorted(classes - CLASSES):
            self.report(f'class "{cls}" is not in the element set')
        if "style" in a:
            self.report("style= attribute; use base.css only")
        if (
            tag == "link"
            and a.get("rel") == "stylesheet"
            and not (a.get("href") or "").startswith(FONT_LINK)
        ):
            self.report("stylesheet other than the font link")
        if tag == "div" and not classes & DIV_CLASSES:
            self.report("<div> is allowed only as .fingerprint or .figure-row")
        if tag == "form" and "form" in self.stack:
            self.report("region inside a region")
        if tag == "dialog" and "dialog" in self.stack:
            self.report("overlay inside an overlay")
        if tag in CONTROLS and "dialog" in self.stack:
            self.report("controls inside a modal; a modal only drills into a row")
        if tag == "mark":
            self.check_mark()
        self.track_table(tag, a, classes)
        self.last_comment = ""
        if tag in OPAQUE:
            self.check_svg_color(a)
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        """Close the open elements up to this tag."""
        if tag in VOID or tag not in self.stack:
            return
        while self.stack.pop() != tag:
            pass
        if self.opaque() or not self.tables:
            return
        t = self.tables[-1]
        if tag in ("th", "td") and t.cell:
            if t.in_head:
                t.header.append(normalize(t.cell.text))
            elif t.row is not None:
                t.row.append(t.cell)
            t.cell = None
        elif tag == "tr" and t.row:
            t.rows.append(t.row)
            t.row = None
        elif tag == "thead":
            t.in_head = False
        elif tag == "table":
            self.check_table(self.tables.pop())

    def track_table(
        self, tag: str, a: dict[str, str | None], classes: set[str]
    ) -> None:
        """Record the table structure that the numeric checks need."""
        if tag == "table":
            self.tables.append(Table())
        if not self.tables:
            return
        t = self.tables[-1]
        if tag == "thead":
            t.in_head = True
        if tag == "tr" and not t.in_head:
            t.row = None if "group" in classes else []
        if tag in ("th", "td"):
            t.cell = Cell(num="num" in classes, span="colspan" in a)

    # Content

    def handle_data(self, data: str) -> None:
        """Check one run of text for banned characters."""
        if not data.strip():
            return
        self.last_comment = ""
        if self.opaque():
            return
        if self.tables and self.tables[-1].cell:
            self.tables[-1].cell.text += data
        if any(t in VERBATIM for t in self.stack) or "title" in self.stack:
            return
        for m in BANNED.finditer(data):
            self.report(f'banned character "{m.group().strip()}"')
        if STRAY_ARROW.search(data):
            self.report("↑ or ↓ away from a number")

    def handle_comment(self, data: str) -> None:
        """Remember an admission comment for the next element."""
        self.last_comment = data.strip()
        if self.last_comment.lower().startswith("color"):
            self.color_comment = True

    # Checks that need a whole element

    def check_mark(self) -> None:
        """Allow one highlight per page, with its admission comment."""
        self.marks += 1
        if self.marks > 1:
            self.report("more than one highlight on the page")
        if not self.last_comment.lower().startswith("highlight"):
            self.report(
                "highlight without an admission comment "
                "(<!-- highlight: ... --> right before it)"
            )

    def check_svg_color(self, attrs: dict[str, str | None]) -> None:
        """Report a chart color that is not admitted."""
        for key in ("fill", "stroke"):
            value = (attrs.get(key) or "").strip().lower()
            if (
                value
                and value not in ADMITTED
                and not value.startswith(TOKENS)
                and not self.color_comment
            ):
                self.report(
                    f'{key}="{value}" without an admission comment '
                    "(<!-- color: ... --> before the chart)"
                )
                # Report a chart once, not each of its marks.
                self.color_comment = True

    def check_table(self, t: Table) -> None:
        """Check that numeric columns are right-aligned and even."""
        rows = [r for r in t.rows if not any(c.span for c in r)]
        if not rows:
            return
        for i in range(max(len(r) for r in rows)):
            cells = [r[i] for r in rows if i < len(r) and r[i].text.strip()]
            if not cells or not all(NUMBER.match(c.text.strip()) for c in cells):
                continue
            name = t.header[i] if i < len(t.header) else f"column {i + 1}"
            if not all(c.num for c in cells):
                self.report(f'numeric column "{name}" needs class="num" on every cell')
            decimals = {
                len(c.text.strip().rstrip("%").partition(".")[2]) for c in cells
            }
            if len(decimals) > 1 and not self.restyle:
                self.report(f'numeric column "{name}" mixes decimal places')

    def check_styles(self, html: str) -> None:
        """Report each <style> block that is not base.css verbatim."""
        base = normalize(BASE_CSS)
        for m in re.finditer(
            r"<style[^>]*>(.*?)</style>", html, re.DOTALL | re.IGNORECASE
        ):
            if normalize(m.group(1)) != base:
                line = html.count("\n", 0, m.start()) + 1
                message = (
                    "<style> differs from base.css; "
                    "paste base.css verbatim and add nothing"
                )
                self.findings.append((line, message))


def lint(html: str, restyle: bool = False) -> list[tuple[int, str]]:
    """Return the (line, message) findings for one page.

    :param restyle: The page is a restyle, so the decimal places of its
        numbers come from the source and are not checked.
    """
    linter = Linter(restyle)
    linter.check_styles(html)
    linter.feed(html)
    linter.close()
    return sorted(linter.findings)


class Outline(HTMLParser):
    """Collect the headings, table values and visible text of any page."""

    def __init__(self) -> None:
        """Create an empty outline."""
        super().__init__(convert_charrefs=True)
        self.headings: list[str] = []
        self.values: list[str] = []
        self.text: list[str] = []
        self.stack: list[str] = []
        self.heading: str | None = None
        self.cell: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Open a heading or a cell."""
        if tag in VOID:
            return
        self.stack.append(tag)
        if tag in HEADINGS:
            self.heading = ""
        if tag == "td":
            self.cell = ""

    def handle_endtag(self, tag: str) -> None:
        """Close a heading or a cell."""
        if tag not in self.stack:
            return
        while self.stack.pop() != tag:
            pass
        if tag in HEADINGS and self.heading is not None:
            self.headings.append(self.heading)
            self.heading = None
        if tag == "td" and self.cell is not None:
            self.values.append(self.cell)
            self.cell = None

    def handle_data(self, data: str) -> None:
        """Add visible text to the open heading or cell."""
        if {"script", "style", "title"} & set(self.stack):
            return
        self.text.append(data)
        if self.heading is not None:
            self.heading += data
        if self.cell is not None:
            self.cell += data


def comparable(text: str) -> str:
    """Remove what a restyle may change: emoji, numbering, case, a colon."""
    # An emoji often carries an invisible variation selector or joiner.
    # Remove those with the emoji.
    text = re.sub(r"[\ufe00-\ufe0f\u200d]", "", BANNED.sub(" ", htmllib.unescape(text)))
    text = re.sub(r"^\s*\d+(\.\d+)*\s+", "", normalize(text))
    return text.rstrip(":").strip().lower()


def outline(html: str) -> Outline:
    """Parse a page into its outline."""
    parsed = Outline()
    parsed.feed(html)
    parsed.close()
    return parsed


def compare(page: str, source: str) -> list[tuple[int, str]]:
    """Return findings where a restyle lost or moved source content."""
    new, old = outline(page), outline(source)
    findings: list[tuple[int, str]] = []
    text = comparable("".join(new.text))
    a = [h for h in map(comparable, old.headings) if h]
    b = [h for h in map(comparable, new.headings) if h]
    matcher = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op in ("delete", "replace"):
            for heading in a[i1:i2]:
                if heading in b:
                    findings.append(
                        (0, f'source heading "{heading}" is moved or missing')
                    )
                elif heading not in text:
                    # A heading that was a field label can become a table
                    # header. Only text that is gone counts.
                    findings.append((0, f'source heading "{heading}" is missing'))
        if op == "insert":
            for heading in b[j1:j2]:
                findings.append((0, f'heading "{heading}" is not in the source'))
    values = dict.fromkeys(map(comparable, old.values))
    missing = [v for v in values if v and v not in text]
    for value in missing[:10]:
        findings.append((0, f'source table value "{value}" is missing'))
    if len(missing) > 10:
        findings.append(
            (0, f"{len(missing) - 10} more source table values are missing")
        )
    return findings


def main() -> int:
    """Lint one page and print the findings."""
    parser = argparse.ArgumentParser(description="Check a design-system page.")
    parser.add_argument("page", type=Path)
    parser.add_argument("--source", type=Path, help="the original page of a restyle")
    args = parser.parse_args()
    page = args.page.read_text()
    findings = lint(page, restyle=args.source is not None)
    if args.source:
        findings += compare(page, args.source.read_text(errors="replace"))
    for line, message in findings:
        print(f"{args.page}:{line}: {message}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
