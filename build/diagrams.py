"""Small SVG diagram builders for lessons.

Every diagram uses the .fig classes from assets/style.css, so it follows the
module colour (var(--accent), var(--accent2)) and the light or dark theme.
Text in boxes can be split onto two lines with "|".

    flowchart(nodes, edges)    boxes and decisions on a grid, with routed arrows
    chain(items)               a left-to-right pipeline
    refs(names, objects, links) names pointing at objects (the object model)
    table(headers, rows)       a small grid, for state that changes step by step
    module_map(lessons, project) how a module's lessons build to its project
"""
import html
import itertools

_ids = itertools.count(1)
CHAR = 6.9          # rough width of one character at the figure font size


def _esc(s):
    return html.escape(str(s), quote=True)


def _open(W, H, aria):
    """Opening tag: drawn at its natural size (never stretched), shrinking on narrow screens."""
    return (f'<svg viewBox="0 0 {W:.0f} {H:.0f}" role="img" aria-label="{aria}" '
            f'style="max-width:{W:.0f}px;min-width:min({W:.0f}px,540px);margin:0 auto">')


def wrap(text, width):
    """Split text into lines of at most `width` characters, breaking at spaces; "|" forces a break."""
    lines = []
    for part in str(text).split("|"):
        cur = ""
        for word in part.split():
            if cur and len(cur) + 1 + len(word) > width:
                lines.append(cur)
                cur = word
            else:
                cur = f"{cur} {word}" if cur else word
        lines.append(cur)
    return lines


def _markers(uid):
    out = []
    for name, colour in (("n", "var(--label2)"), ("a", "var(--accent)"), ("r", "var(--red)"), ("g", "var(--green)")):
        out.append(f'<marker id="m{uid}{name}" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" '
                   f'orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" style="fill:{colour}"/></marker>')
    return "<defs>" + "".join(out) + "</defs>"


def _text_block(x, y, lines, cls, line_h=15):
    top = y - (len(lines) - 1) * line_h / 2 + 4.5
    return "".join(f'<text x="{x:.1f}" y="{top + i * line_h:.1f}" class="{cls}">{_esc(l)}</text>' for i, l in enumerate(lines))


_FILLED = {"start": "box a", "end": "box b", "accent": "box a", "accent2": "box b", "good": "box g", "bad": "box r", "warn": "box o"}


def _shape(kind, x, y, w, h):
    """Return (svg, text_class) for a node centred at x, y."""
    if kind == "ask":
        pts = f"{x},{y - h / 2} {x + w / 2},{y} {x},{y + h / 2} {x - w / 2},{y}"
        return f'<polygon points="{pts}" class="soft"/>', "v mid"
    if kind == "note":
        return (f'<rect x="{x - w / 2:.1f}" y="{y - h / 2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="10" '
                f'style="fill:none;stroke:var(--sep);stroke-dasharray:4 4"/>'), "mid"
    cls = _FILLED.get(kind, "box")
    rx = h / 2 if kind in ("start", "end") else 12
    text = "w mid" if cls != "box" else "v mid"
    return f'<rect x="{x - w / 2:.1f}" y="{y - h / 2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx:.1f}" class="{cls}"/>', text


def _edge_style(style):
    colour = {"a": "var(--accent)", "r": "var(--red)", "g": "var(--green)"}.get(style.replace("dash", "").strip(), "var(--label2)")
    marker = {"var(--accent)": "a", "var(--red)": "r", "var(--green)": "g"}.get(colour, "n")
    dash = ";stroke-dasharray:5 4" if "dash" in style else ""
    return f"stroke:{colour};stroke-width:2;fill:none{dash}", marker


def flowchart(nodes, edges, cell=(170, 78), label="", wrap_at=None):
    """nodes: {key: (kind, col, row, text)}; kinds: start end step ask good bad warn accent accent2 note.
    edges: (from, to) or (from, to, label) or (from, to, label, opts) where opts is a dict with
    "route": "hv" | "vh" | list of (col, row) waypoints, and "style": "a" | "r" | "g" | "dash"."""
    uid = next(_ids)
    cw, rh = cell
    pad = 16
    cols = max(n[1] for n in nodes.values()) + 1
    rows = max(n[2] for n in nodes.values()) + 1
    W, H = cols * cw + 2 * pad, rows * rh + 2 * pad
    wrap_at = wrap_at or max(8, int((cw - 64) / CHAR))
    geo = {}
    body = []
    for key, (kind, c, r, text) in nodes.items():
        x, y = pad + c * cw + cw / 2, pad + r * rh + rh / 2
        lines = wrap(text, wrap_at if kind != "ask" else max(6, wrap_at - 4))
        w = cw - 52
        h = max(40, 16 * len(lines) + 14)
        if kind == "ask":
            h = max(54, 16 * len(lines) + 26)
        geo[key] = (x, y, w, h, kind)
        svg, cls = _shape(kind, x, y, w, h)
        body.append(svg + _text_block(x, y, lines, cls))

    def gx(c):
        return pad + c * cw + cw / 2

    def gy(r):
        return pad + r * rh + rh / 2

    arrows = []
    for e in edges:
        a, b = e[0], e[1]
        lab = e[2] if len(e) > 2 else ""
        opts = e[3] if len(e) > 3 else {}
        ax, ay, aw, ah, _ = geo[a]
        bx, by, bw, bh, _ = geo[b]
        route = opts.get("route", "hv")
        if isinstance(route, list):
            mid = [(gx(c), gy(r)) for c, r in route]
        elif ax == bx or ay == by:
            mid = []
        elif route == "hv":
            mid = [(bx, ay)]
        elif route == "vh":
            mid = [(ax, by)]
        else:
            mid = [(ax, by)]
        pts = [(ax, ay)] + mid + [(bx, by)]

        def clip(p, q, w, h):
            (px, py), (qx, qy) = p, q
            if abs(qx - px) >= abs(qy - py):
                return (px + (w / 2 if qx > px else -w / 2), py)
            return (px, py + (h / 2 if qy > py else -h / 2))

        pts[0] = clip(pts[0], pts[1], aw, ah)
        pts[-1] = clip(pts[-1], pts[-2], bw, bh)
        d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
        style, marker = _edge_style(opts.get("style", ""))
        arrows.append(f'<path d="{d}" style="{style}" marker-end="url(#m{uid}{marker})"/>')
        if lab:
            (x1, y1), (x2, y2) = pts[0], pts[1]
            if abs(x2 - x1) >= abs(y2 - y1):
                step = min(abs(x2 - x1) / 2, 24)
                lx, ly, anchor = x1 + (step if x2 > x1 else -step), y1 - 8, " mid"
            else:
                step = min(abs(y2 - y1) / 2, 15)
                lx, ly, anchor = x1 + 8, y1 + (step + 4 if y2 > y1 else -step + 4), ""
            arrows.append(f'<text x="{lx:.1f}" y="{ly:.1f}" class="v{anchor}">{_esc(lab)}</text>')
    aria = _esc(label or "flow diagram")
    return (_open(W, H, aria) + _markers(uid)
            + "".join(arrows) + "".join(body) + "</svg>")


def chain(items, label="", gap=34, height=56, note=None):
    """A left-to-right pipeline. items: str or (text, kind), kinds as in flowchart (default "step")."""
    uid = next(_ids)
    specs = []
    for it in items:
        text, kind = (it, "step") if isinstance(it, str) else it
        lines = wrap(text, 16)
        w = max(96, max(len(l) for l in lines) * CHAR + 28)
        specs.append((lines, kind, w))
    W = sum(w for _, _, w in specs) + gap * (len(specs) - 1) + 32
    h = max(height, max(16 * len(s[0]) + 18 for s in specs))
    H = h + 32 + (26 if note else 0)
    x = 16
    y = 16 + h / 2
    parts = []
    for i, (lines, kind, w) in enumerate(specs):
        cx = x + w / 2
        svg, cls = _shape(kind, cx, y, w, h)
        parts.append(svg + _text_block(cx, y, lines, cls))
        if i < len(specs) - 1:
            parts.append(f'<path d="M{x + w + 3:.1f} {y:.1f} H{x + w + gap - 3:.1f}" style="stroke:var(--label2);stroke-width:2;fill:none" '
                         f'marker-end="url(#m{uid}n)"/>')
        x += w + gap
    if note:
        parts.append(f'<text x="{W / 2:.1f}" y="{H - 10:.1f}" class="mid">{_esc(note)}</text>')
    aria = _esc(label or " then ".join(" ".join(s[0]) for s in specs))
    return _open(W, H, aria) + _markers(uid) + "".join(parts) + "</svg>"


def refs(names, objects, links, label="", title_names="names", title_objects="objects"):
    """Names on the left, objects on the right, an arrow for each (name_index, object_index) link.
    objects: str or (text, kind); kind "accent" highlights an object."""
    uid = next(_ids)
    row = 58
    n = max(len(names), len(objects))
    W, H = 620, n * row + 52
    nx, ox = 110, 430
    parts = [f'<text x="{nx}" y="18" class="h mid">{_esc(title_names)}</text>', f'<text x="{ox}" y="18" class="h mid">{_esc(title_objects)}</text>']

    def ny(i, count):
        return 34 + (n * row - count * row) / 2 + i * row + row / 2

    for i, name in enumerate(names):
        y = ny(i, len(names))
        parts.append(f'<rect x="{nx - 70}" y="{y - 18:.1f}" width="140" height="36" rx="18" class="box"/>'
                     f'<text x="{nx}" y="{y + 4.5:.1f}" class="tk">{_esc(name)}</text>')
    for j, obj in enumerate(objects):
        text, kind = (obj, "step") if isinstance(obj, str) else obj
        lines = wrap(text, 30)
        y = ny(j, len(objects))
        h = max(40, 16 * len(lines) + 12)
        svg, cls = _shape(kind, ox, y, 260, h)
        parts.append(svg + _text_block(ox, y, lines, cls.replace("v mid", "tk") if kind == "step" else cls))
    for i, j in links:
        y1, y2 = ny(i, len(names)), ny(j, len(objects))
        parts.append(f'<path d="M{nx + 72} {y1:.1f} C{(nx + ox) / 2 - 20} {y1:.1f}, {(nx + ox) / 2 + 20} {y2:.1f}, {ox - 134} {y2:.1f}" '
                     f'style="stroke:var(--accent);stroke-width:2;fill:none" marker-end="url(#m{uid}a)"/>')
    aria = _esc(label or "names pointing at objects")
    return _open(W, H, aria) + _markers(uid) + "".join(parts) + "</svg>"


def table(headers, rows, hl=(), label="", col_w=None):
    """A grid of cells. hl: set of (row, col) to highlight (0-based, excluding the header row)."""
    ncol = len(headers)
    col_w = col_w or [max(80, max(len(str(x)) for x in [headers[c]] + [r[c] for r in rows]) * CHAR + 26) for c in range(ncol)]
    rh = 34
    W = sum(col_w) + 32
    H = rh * (len(rows) + 1) + 32
    parts = []
    y = 16
    for ri, cells in enumerate([headers] + list(rows)):
        x = 16
        for ci, val in enumerate(cells):
            w = col_w[ci]
            if ri == 0:
                cls, tcls = "box b", "w mid"
            elif (ri - 1, ci) in set(hl):
                cls, tcls = "box a", "tk w"
            else:
                cls, tcls = "box", "tk"
            parts.append(f'<rect x="{x + 1}" y="{y + 1}" width="{w - 2}" height="{rh - 2}" rx="7" class="{cls}"/>'
                         f'<text x="{x + w / 2:.1f}" y="{y + rh / 2 + 4.5:.1f}" class="{tcls}">{_esc(val)}</text>')
            x += w
        y += rh
    aria = _esc(label or "table")
    return _open(W, H, aria) + "".join(parts) + "</svg>"


def module_map(lessons, project, label=""):
    """lessons: list of (num, title). Draws the lessons as steps that lead to the module's mini project."""
    per_row = 3 if len(lessons) > 4 else len(lessons)
    nodes, edges = {}, []
    keys = []
    for i, (num, title) in enumerate(lessons):
        r, c = divmod(i, per_row)
        if r % 2:
            c = per_row - 1 - c
        key = f"l{i}"
        nodes[key] = ("step" if i else "accent", c, r, f"{num}|{title}")
        keys.append(key)
    last_r, last_c = nodes[keys[-1]][2], nodes[keys[-1]][1]
    if (last_r % 2 == 0 and last_c < per_row - 1) or (last_r % 2 == 1 and last_c > 0):
        pr, pc = last_r, last_c + (1 if last_r % 2 == 0 else -1)
    else:
        pr, pc = last_r + 1, last_c
    nodes["project"] = ("end", pc, pr, f"Mini project|{project}")
    keys.append("project")
    for a, b in zip(keys, keys[1:]):
        edges.append((a, b, "", {"style": "a"}))
    return flowchart(nodes, edges, cell=(206, 92), label=label or "how the lessons of this module lead to its mini project")
