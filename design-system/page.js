// design-system page.js. Paste verbatim into a <script> at the end of <body>.

// Fingerprint: dark and light segments alternate, so neighbours always differ in lightness for colorblind readers.
const FINGERPRINT_DARK = ["#004D40", "#005AB5", "#781C6D", "#A63603", "#1E293B"];
const FINGERPRINT_LIGHT = ["#56B4E9", "#F0E442", "#E69F00", "#66C2A5", "#F4A582"];
// Asymmetric rhythms (percent of the width), so the shape itself is memorable.
const FINGERPRINT_RHYTHMS = [
  [58, 12, 30], [28, 12, 60], [16, 68, 16], [50, 32, 18],
  [18, 32, 50], [52, 12, 12, 24], [24, 12, 12, 52], [42, 14, 44],
];
let fingerprintCount = 0;

// FNV-1a with a Murmur3 finalizer: a one-character change in the seed gives an unrelated hash.
function hashSeed(str) {
  let h = 2166136261 >>> 0;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  h ^= h >>> 16; h = Math.imul(h, 0x85ebca6b);
  h ^= h >>> 13; h = Math.imul(h, 0xc2b2ae35);
  return (h ^ (h >>> 16)) >>> 0;
}

// Outline with continuous curvature: superellipse caps meet the straight edges with zero
// curvature, so there is no visible kink where a circular arc would start (metro line curves).
function squirclePath(width, height, n = 2.5) {
  const b = height / 2;
  const a = Math.min(height * 0.7, width / 2);
  const steps = 24;
  const cap = (cx, from, to) => {
    const points = [];
    for (let i = 0; i <= steps; i++) {
      const t = from + ((to - from) * i) / steps;
      const c = Math.cos(t), s = Math.sin(t);
      points.push(`${(cx + a * Math.sign(c) * Math.abs(c) ** (2 / n)).toFixed(2)},${(b + b * Math.sign(s) * Math.abs(s) ** (2 / n)).toFixed(2)}`);
    }
    return points.join(" L");
  };
  return `M${a},0 L${width - a},0 L${cap(width - a, -Math.PI / 2, Math.PI / 2)} L${a},${height} L${cap(a, Math.PI / 2, (3 * Math.PI) / 2)} Z`;
}

// Deterministic: the same seed draws the same picture at any size, so a refresh never changes it.
function fingerprintSvg(seed, width, height) {
  const h = hashSeed(seed);
  const rhythm = FINGERPRINT_RHYTHMS[h % FINGERPRINT_RHYTHMS.length];
  const startDark = ((h >>> 3) & 1) === 1;
  let d = (h >>> 4) % FINGERPRINT_DARK.length;
  let l = (h >>> 8) % FINGERPRINT_LIGHT.length;
  const dStep = ((h >>> 12) % (FINGERPRINT_DARK.length - 1)) + 1;
  const lStep = ((h >>> 16) % (FINGERPRINT_LIGHT.length - 1)) + 1;
  // The 30-degree skew pushes segments sideways; widen the canvas so both ends stay covered.
  const overhang = Math.ceil(height / Math.tan(Math.PI / 3));
  const total = width + overhang * 2;
  let x = -overhang;
  const rects = rhythm.map((pct, i) => {
    const dark = i % 2 === 0 ? startDark : !startDark;
    const color = dark ? FINGERPRINT_DARK[d] : FINGERPRINT_LIGHT[l];
    if (dark) d = (d + dStep) % FINGERPRINT_DARK.length;
    else l = (l + lStep) % FINGERPRINT_LIGHT.length;
    const w = (pct / 100) * total;
    const rect = `<rect x="${x.toFixed(1)}" y="-4" width="${w.toFixed(1)}" height="${height + 8}" fill="${color}" stroke="#fff" stroke-width="2"/>`;
    x += w;
    return rect;
  }).join("");
  const id = `fingerprint-${++fingerprintCount}`;
  const outline = squirclePath(width, height);
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">` +
    `<defs><clipPath id="${id}"><path d="${outline}"/></clipPath></defs>` +
    `<g clip-path="url(#${id})"><g transform="skewX(-30)">${rects}</g></g>` +
    `<path d="${outline}" fill="none" stroke="rgba(15,23,42,0.18)" stroke-width="2" clip-path="url(#${id})"/></svg>`;
}

function drawFingerprint() {
  const seed = document.body.dataset.seed || document.title;
  for (const el of document.querySelectorAll(".fingerprint")) {
    el.innerHTML = fingerprintSvg(seed, el.clientWidth, el.clientHeight);
  }
  const icon = document.querySelector("link[rel=icon]") || document.head.appendChild(document.createElement("link"));
  icon.rel = "icon";
  icon.href = "data:image/svg+xml," + encodeURIComponent(fingerprintSvg(seed, 32, 32));
}

// Marks the index entry of the section the reader is in, and collapses the fingerprint once the index sticks.
function trackScroll() {
  const nav = document.querySelector("nav.index");
  const list = nav && nav.querySelector(":scope > ol");
  if (!list) return;
  const links = new Map();
  for (const a of nav.querySelectorAll("a[href^='#']")) links.set(a.hash.slice(1), a);
  const sections = [...document.querySelectorAll("main section[id]")].filter((s) => links.has(s.id));
  const root = document.documentElement;
  // A section is current once its heading passes the page's top padding.
  const line = parseFloat(getComputedStyle(root).getPropertyValue("--page-pad-y"));
  let shown = null;
  const update = () => {
    const style = getComputedStyle(nav);
    const scrolled = style.position === "sticky" && nav.getBoundingClientRect().top <= parseFloat(style.top);
    if (scrolled !== root.classList.contains("scrolled")) {
      root.classList.toggle("scrolled", scrolled);
      drawFingerprint();
    }
    // Sections whose headings sit too close to the end of the page for the highlight to reach belong
    // to the last section it can reach.
    const left = root.scrollHeight - innerHeight - scrollY;
    let current = null, reach = null;
    for (const s of sections) {
      const top = s.getBoundingClientRect().top;
      if (top <= line) current = s;
      if (top - left <= line) reach = s;
    }
    if (current === shown) return;
    if (shown) links.get(shown.id).removeAttribute("aria-current");
    shown = current;
    if (!current) return;
    links.get(current.id).setAttribute("aria-current", "true");
    // Keep the highlighted entry, and any it owns, in sight: when it lies outside the visible part
    // of the list, turn the list (never the page) by a page: below it, the entry goes to the top;
    // above it, to the bottom.
    const last = current === reach ? sections[sections.length - 1] : current;
    const l = list.getBoundingClientRect(), r = links.get(current.id).getBoundingClientRect();
    if (links.get(last.id).getBoundingClientRect().bottom > l.bottom) list.scrollTop += r.top - l.top;
    else if (r.top < l.top) list.scrollTop += r.bottom - l.bottom;
  };
  window.addEventListener("scroll", update, { passive: true });
  update();
}

// Code wraps at spaces like text; a path may also break after each slash, and a
// comma-separated list after each comma.
function breakPaths() {
  for (const code of document.querySelectorAll("code")) {
    if (code.children.length || code.closest("pre")) continue;
    if (!/[\/,]/.test(code.textContent)) continue;
    const parts = code.textContent.split(/(?<=[\/,])/);
    code.replaceChildren(...parts.flatMap((part, i) => (i ? [document.createElement("wbr"), part] : [part])));
  }
}

// Data tables: a table longer than one screen or wider than its column gets search, column
// visibility, sorting and pagination. Without this script the full table shows as it is.
const PAGE_ROWS = 25;
const PLAIN_MAX_ROWS = 15;

function makeDataTables() {
  for (const table of document.querySelectorAll("main table")) {
    const head = table.tHead && table.tHead.rows[0];
    const body = table.tBodies[0];
    if (!head || !body) continue;
    const tooWide = table.offsetWidth > maxWidthPx(table) + 1;
    const dataRows = [...body.rows].filter((r) => !r.classList.contains("group"));
    if (dataRows.length <= PLAIN_MAX_ROWS && !tooWide) continue;
    dataTable(table, head, body);
  }
}

// The width a table may take: its max-width in px, or a percentage of its container.
function maxWidthPx(el) {
  const value = getComputedStyle(el).maxWidth;
  if (value.endsWith("%")) return (parseFloat(value) / 100) * el.parentElement.clientWidth;
  return parseFloat(value);
}

function dataTable(table, head, body) {
  const original = [...body.rows];
  const text = new Map(original.map((r) => [r, r.textContent.toLowerCase()]));
  const columns = [...head.cells];
  const state = { query: "", sortCol: -1, sortDir: 0, page: 0 };

  const wrap = document.createElement("div");
  wrap.className = "data-table";
  wrap.innerHTML =
    `<div class="data-table-tools"><input type="search" placeholder="Search" aria-label="Search table">` +
    `<button type="button" aria-expanded="false">Columns</button><div class="data-table-menu" hidden></div></div>` +
    `<div class="data-table-scroll"></div>` +
    `<div class="data-table-pager"><span></span><button type="button">Previous</button><button type="button">Next</button></div>`;
  table.replaceWith(wrap);
  wrap.querySelector(".data-table-scroll").append(table);
  const [search] = wrap.getElementsByTagName("input");
  const [columnsButton, previous, next] = wrap.querySelectorAll("button");
  const menu = wrap.querySelector(".data-table-menu");
  const status = wrap.querySelector(".data-table-pager span");

  // Long text gets a readable width; the table scrolls sideways instead of stacking single words.
  for (const cell of table.querySelectorAll("td")) if (cell.textContent.length > 60) cell.style.minWidth = "24rem";

  // Column visibility: everything starts visible.
  columns.forEach((th, i) => {
    const label = document.createElement("label");
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = true;
    label.append(checkbox, ` ${th.textContent.trim() || `Column ${i + 1}`}`);
    checkbox.addEventListener("change", (e) => {
      for (const row of table.rows) {
        if (row.cells.length === columns.length) row.cells[i].hidden = !e.target.checked;
      }
    });
    menu.append(label);
  });
  columnsButton.addEventListener("click", () => {
    menu.hidden = !menu.hidden;
    columnsButton.setAttribute("aria-expanded", String(!menu.hidden));
  });
  document.addEventListener("click", (e) => {
    if (!wrap.querySelector(".data-table-tools").contains(e.target)) menu.hidden = true;
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") menu.hidden = true; });

  // Sorting: ascending, descending, then back to the original order.
  columns.forEach((th, i) => {
    const button = document.createElement("button");
    button.type = "button";
    button.append(...th.childNodes);
    th.append(button);
    button.addEventListener("click", () => {
      state.sortDir = state.sortCol === i ? (state.sortDir + 1) % 3 : 1;
      state.sortCol = state.sortDir ? i : -1;
      columns.forEach((c) => c.removeAttribute("aria-sort"));
      if (state.sortDir) th.setAttribute("aria-sort", state.sortDir === 1 ? "ascending" : "descending");
      state.page = 0;
      render();
    });
  });

  search.addEventListener("input", () => { state.query = search.value.trim().toLowerCase(); state.page = 0; render(); });
  previous.addEventListener("click", () => { state.page--; render(); });
  next.addEventListener("click", () => { state.page++; render(); });

  function render() {
    // A dashboard's own filters mark rows with data-out and send "refresh" to the table.
    let rows = original.filter((r) => !r.classList.contains("group") && !r.hasAttribute("data-out"));
    if (state.query) rows = rows.filter((r) => text.get(r).includes(state.query));
    if (state.sortDir) {
      const sign = state.sortDir === 1 ? 1 : -1;
      rows = rows.map((r) => [sortKey(r.cells[state.sortCol]), r])
        .sort((a, b) => sign * compareKeys(a[0], b[0]))
        .map(([, r]) => r);
    }
    const pages = Math.max(1, Math.ceil(rows.length / PAGE_ROWS));
    state.page = Math.min(Math.max(state.page, 0), pages - 1);
    const start = state.page * PAGE_ROWS;
    const shown = new Set(rows.slice(start, start + PAGE_ROWS));
    // Group rows keep their place only in the original order; sorting or searching hides them.
    const ordered = state.sortDir || state.query ? rows : original;
    for (const r of original) r.hidden = true;
    body.append(...ordered);
    let group = null;
    for (const r of ordered) {
      if (r.classList.contains("group")) { group = r; continue; }
      if (shown.has(r)) { r.hidden = false; if (group) group.hidden = false; }
    }
    status.textContent = rows.length
      ? `Rows ${start + 1} to ${start + shown.size} of ${rows.length}`
      : "No rows match";
    previous.disabled = state.page === 0;
    next.disabled = state.page >= pages - 1;
  }
  table.addEventListener("refresh", () => { state.page = 0; render(); });
  render();
}

// A cell sorts by its number when it holds only a number, and by its text otherwise.
function sortKey(cell) {
  const text = cell ? cell.textContent.trim() : "";
  const num = /^[↑↓\-−+]?[\d,.]+%?$/.test(text) ? parseFloat(text.replace(/[,%↑↓]/g, "")) : NaN;
  return { text, num };
}

function compareKeys(x, y) {
  if (!x.text || !y.text) return x.text ? -1 : y.text ? 1 : 0;  // empty cells last
  if (!isNaN(x.num) && !isNaN(y.num)) return x.num - y.num;
  return x.text.localeCompare(y.text, undefined, { numeric: true });
}

drawFingerprint();
trackScroll();
breakPaths();
makeDataTables();
