"""Turn the python-core-foundations theory notebooks into live pages under theory/.

    python build/theory.py "../Python Core Foundations"

Markdown cells keep their own HTML and styling. Code cells use the site's code blocks,
with the outputs saved in the notebook (real runs), so nothing is retyped by hand.
"""
import base64
import html as H
import json
import re
import sys
from pathlib import Path

import nbformat
from nbconvert.filters import markdown2html

ROOT = Path(__file__).resolve().parent.parent
SRC_REPO = "https://github.com/SivaRamaNaiduThattikota/python-core-foundations/blob/main/"

# slug, module, title, notebook path. The order here is the reading order.
PAGES = [
    ("mutability", 2, "Mutability and the object model", "Mutability & the Object Model/theory.ipynb"),
    ("functions", 3, "Functions, scope and closures", "Functions, Scope & Closures/theory.ipynb"),
    ("list", 4, "2A List", "Sequences/List/theory.ipynb"),
    ("tuple", 4, "2B Tuple", "Sequences/tuple/theory.ipynb"),
    ("set", 4, "2C Set and frozenset", "Sequences/Set & frozenset/theory.ipynb"),
    ("dict", 4, "2D Dictionaries", "Sequences/Dictionaries/theory.ipynb"),
    ("strings", 5, "Strings", "Strings/theory.ipynb"),
    ("comprehensions", 6, "Comprehensions and generators", "Comprehensions & Generators/theory.ipynb"),
    ("decorators", 7, "Decorators", "Decorators/theory.ipynb"),
    ("errors", 8, "Error handling", "Error Handling/theory.ipynb"),
    ("oop-pillars", 9, "The four pillars of OOP", "OOP/00_four_pillars.ipynb"),
    ("classes", 9, "7A Classes and instances", "OOP/Classes & Instances/theory.ipynb"),
    ("dunders", 9, "7B Dunder methods", "OOP/Dunder Methods/theory.ipynb"),
    ("inheritance", 9, "7C Inheritance and MRO", "OOP/Inheritance & MRO/theory.ipynb"),
    ("properties", 9, "7D Properties and methods", "OOP/Properties & Methods/theory.ipynb"),
    ("iterators", 10, "Iterators and context managers", "Iterators & Context Managers/theory.ipynb"),
    ("typing", 11, "Typing and dataclasses", "Typing & Dataclasses/theory.ipynb"),
    ("concurrency", 14, "7E The GIL and concurrency", "OOP/GIL & Concurrency/theory.ipynb"),
]

ANSI = re.compile(r"\x1b\[[0-9;]*m")
esc = H.escape


def clean_markdown_html(s):
    # The notebook styles reset body / Jupyter containers for notebook viewers; on a real page
    # those rules would fight the site layout, so they are pointed at nothing.
    s = re.sub(r"body\s*,\s*\.jp-RenderedHTMLCommon", ".nb-unused", s)
    s = re.sub(r"(?m)^\s*body\s*\{", ".nb-unused{", s)
    # buttons that only worked inside the chat tool the notes were written in
    s = re.sub(r'\s*onclick="sendPrompt\([^"]*\)"', "", s)
    return s


def render_outputs(outputs):
    parts = []
    for o in outputs:
        t = o.get("output_type")
        if t == "stream":
            parts.append(("text", "".join(o.get("text", ""))))
        elif t in ("execute_result", "display_data"):
            d = o.get("data", {})
            if "image/png" in d:
                parts.append(("img", d["image/png"]))
            elif "text/html" in d:
                parts.append(("html", "".join(d["text/html"])))
            elif "text/plain" in d:
                parts.append(("text", "".join(d["text/plain"])))
        elif t == "error":
            parts.append(("err", ANSI.sub("", "\n".join(o.get("traceback", [])))))
    out = []
    for kind, v in parts:
        if kind == "text":
            out.append(f'<div class="out"><span class="ol">Output</span><pre>{esc(v.rstrip())}</pre></div>')
        elif kind == "err":
            out.append(f'<div class="out nb-err"><span class="ol">Error</span><pre>{esc(v.rstrip())}</pre></div>')
        elif kind == "html":
            out.append(f'<div class="out nb-html"><span class="ol">Output</span>{v}</div>')
        elif kind == "img":
            out.append(f'<div class="out nb-img"><img alt="Plot from the notebook" src="data:image/png;base64,{v.strip()}"></div>')
    return "".join(out)


def render_notebook(nb):
    cells = []
    for c in nb.cells:
        if c.cell_type == "markdown":
            cells.append(f'<div class="nb-md">{clean_markdown_html(markdown2html(c.source))}</div>')
        elif c.cell_type == "code" and c.source.strip():
            body = f'<pre><code class="py">{esc(c.source)}</code></pre>'
            cells.append(f'<div class="code nb-code">{body}{render_outputs(c.get("outputs", []))}</div>')
    return "\n".join(cells)


def module_name(stage):
    js = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
    m = re.search(rf"\n  {stage}: {{ name: '([^']+)' }}", js)
    return m.group(1) if m else f"Module {stage}"


def page(slug, stage, title, path, body, n_cells):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Theory · {esc(title)} · Python Engineering Practice</title>
<meta name="color-scheme" content="light dark">
<script src="../assets/boot.js"></script>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap">
<link rel="stylesheet" href="../assets/style.css">
<link rel="stylesheet" href="../assets/glass.css">
<link rel="stylesheet" href="../assets/practice.css">
</head>
<body data-id="t-{slug}" data-root="../" data-title="Theory · {esc(title)}" data-stage="{stage}">
<div class="shell"><div class="main">
<main class="content page">

<section class="l-hero">
  <div class="crumbs"><a href="../index.html">Course</a><span>›</span><a href="../index.html#theory">Theory</a><span>›</span><span>{esc(module_name(stage))}</span></div>
  <h1>{esc(title)}</h1>
  <p>The full theory notes for this module: concept, worked examples, edge cases, traps, ML uses and interview questions. Read here, then practise on the lesson pages.</p>
  <div class="chips"><span class="chip">Theory notes</span><span class="chip">{n_cells} sections</span><a class="chip chip-link" href="{SRC_REPO}{esc(path, quote=True).replace(' ', '%20')}" target="_blank" rel="noopener">Notebook on GitHub ↗</a></div>
</section>

<article class="nb">
{body}
</article>

<nav class="pager" id="theory-pager"></nav>

</main>
</div></div>
<script src="../assets/app.js"></script>
<script src="../assets/runner.js"></script>
</body>
</html>
"""


def main():
    src = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT.parent / "Python Core Foundations")
    out = ROOT / "theory"
    out.mkdir(exist_ok=True)
    for slug, stage, title, path in PAGES:
        nb = nbformat.read(src / path, as_version=4)
        n = sum(1 for c in nb.cells if c.cell_type == "markdown")
        (out / f"{slug}.html").write_text(page(slug, stage, title, path, render_notebook(nb), n), encoding="utf-8")
        print(f"theory/{slug}.html  ({len(nb.cells)} cells)")


if __name__ == "__main__":
    main()
