"""Build lesson pages from src/*.py.

    python build/build.py            # every lesson
    python build/build.py m1_1       # one lesson

Every snippet is run in Pyodide (build/run_py.mjs) before any HTML is written.
The build stops if a solution fails its tests, a write/fix starter already passes,
a refactor starter fails, an example errors, or the "faster" option is not faster.
"""
import base64
import html as H
import json
import re
import runpy
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "build"))
import lesson as L  # noqa: E402

esc = H.escape
LEVELS = ("easy", "medium", "hard")


# ---------- tiny markup for prose: `code`, **bold**, paragraphs, "- " lists ----------

def inline(s):
    # Code spans are swapped for placeholders first, so `2 ** 3` is never read as bold,
    # while bold can still wrap a code span: **1. `band(x)`** works.
    codes = []

    def keep(m):
        codes.append(f"<code>{esc(m.group(1), quote=False)}</code>")
        return f"\x00{len(codes) - 1}\x00"

    s = re.sub(r"`([^`]+)`", keep, s)
    s = esc(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    return re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], s)


def md(text):
    out = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = [l.strip() for l in block.splitlines()]
        if lines[0].startswith("- "):
            items = []
            for l in lines:   # lines that do not start with "- " continue the previous item
                if l.startswith("- ") or not items:
                    items.append(l[2:] if l.startswith("- ") else l)
                else:
                    items[-1] += " " + l
            out.append("<ul>" + "".join(f"<li>{inline(i)}</li>" for i in items) + "</ul>")
        else:
            out.append(f"<p>{inline(' '.join(l.strip() for l in lines))}</p>")
    return "\n".join(out)


def code_block(code, label="", copy=True):
    bar = ""
    if label:
        bar = (f'<div class="code-bar"><span class="lights"><i></i><i></i><i></i></span><span class="lbl">{esc(label)}</span>'
               + ('<button class="copy">Copy</button>' if copy else "") + "</div>")
    return f'<div class="code">{bar}<pre><code class="py">{esc(code)}</code></pre></div>'


def output_block(text, label="Output"):
    return f'<div class="out"><span class="ol">{label}</span><pre>{esc(text) if text else "(nothing printed)"}</pre></div>'


# ---------- trace problems: lines marked "# row: <label>" record the variables ----------

def trace_source(code, names):
    shown, run = [], ["_rows = []"]
    for line in code.splitlines():
        m = re.match(r"^(\s*)(.*?)\s*# row:\s*(.+)$", line)
        if not m:
            shown.append(line); run.append(line); continue
        ind, body, label = m.groups()
        shown.append(ind + body); run.append(ind + body)
        vals = ", ".join(f"[repr({n}), str({n})]" for n in names)
        run.append(f"{ind}_rows.append([str({label}), [{vals}]])")
    run += ["import json as _json", "print(_json.dumps(_rows))"]
    return "\n".join(shown), "\n".join(run)


# ---------- collect jobs, run them, check them ----------

def problems(les):
    return [x for s in les.sections for x in s.parts if isinstance(x, L.Problem)]


def make_jobs(les):
    jobs = []
    for s in les.sections:
        for i, x in enumerate(s.parts):
            if isinstance(x, L.Example):
                jobs.append({"id": f"ex-{s.id}-{i}", "code": x.code})
    for pr in problems(les):
        k = pr.key
        if pr.kind in ("write", "fix", "refactor"):
            jobs.append({"id": f"start-{k}", "code": pr.code, "tests": pr.tests})
            jobs.append({"id": f"sol-{k}", "code": pr.solution, "tests": pr.tests})
        elif pr.kind == "predict":
            jobs.append({"id": f"pred-{k}", "code": pr.code})
        elif pr.kind == "trace":
            pr._shown, run = trace_source(pr.code, pr.trace_vars)
            jobs.append({"id": f"trace-{k}", "code": run})
        elif pr.kind == "choose":
            jobs.append({"id": f"time-{k}", "kind": "time", "setup": pr.setup, "stmts": list(pr.options.values())})
    return jobs


def run_jobs(jobs):
    with tempfile.TemporaryDirectory() as d:
        jp, rp = Path(d, "jobs.json"), Path(d, "res.json")
        jp.write_text(json.dumps(jobs), encoding="utf-8")
        try:
            subprocess.run(["node", str(ROOT / "build" / "run_py.mjs"), str(jp), str(rp)], check=True,
                           cwd=ROOT / "build", timeout=420)
        except subprocess.TimeoutExpired:
            sys.exit("Python run timed out: a starter, solution or example probably never stops (infinite loop?)")
        return json.loads(rp.read_text(encoding="utf-8"))


def all_pass(r):
    return not r["error"] and r["tests"] and all(t[1] for t in r["tests"])


def check(les, res):
    bad = []
    for s in les.sections:
        for i, x in enumerate(s.parts):
            if isinstance(x, L.Example):
                r = res[f"ex-{s.id}-{i}"]
                if r["error"] and not x.error_ok:
                    bad.append(f"example in {s.id} errors:\n{r['error']}")
                if x.error_ok and not r["error"]:
                    bad.append(f"example in {s.id} was meant to raise but did not")
    keys = set()
    for pr in problems(les):
        k = pr.key
        if k in keys:
            bad.append(f"duplicate problem key {k}")
        keys.add(k)
        if pr.level not in LEVELS:
            bad.append(f"{k}: level {pr.level}")
        if pr.kind in ("write", "fix", "refactor"):
            st, so = res[f"start-{k}"], res[f"sol-{k}"]
            n = sum(1 for t in so["tests"])
            if n < 2:
                bad.append(f"{k}: needs at least 2 asserts")
            if not all_pass(so):
                bad.append(f"{k}: solution fails: {so['error'] or [t for t in so['tests'] if not t[1]]}")
            if pr.kind == "refactor" and not all_pass(st):
                bad.append(f"{k}: refactor starter should pass its tests")
            if pr.kind in ("write", "fix") and all_pass(st):
                bad.append(f"{k}: starter already passes its tests")
        elif pr.kind == "predict":
            r = res[f"pred-{k}"]
            if r["error"]:
                bad.append(f"{k}: predict code errors:\n{r['error']}")
        elif pr.kind == "trace":
            r = res[f"trace-{k}"]
            if r["error"]:
                bad.append(f"{k}: trace code errors:\n{r['error']}")
        elif pr.kind == "choose":
            t = res[f"time-{k}"]["times"]
            keys_ = list(pr.options)
            best = keys_[t.index(min(t))]
            if best != pr.answer:
                bad.append(f"{k}: option {best} measured faster than the answer {pr.answer}: {t}")
    return bad


# ---------- render ----------

def fmt_time(s):
    return f"{s * 1e6:.2f} µs" if s < 1e-3 else f"{s * 1e3:.2f} ms" if s < 1 else f"{s:.2f} s"


def render_problem(les, pr, n, res):
    attrs = f'data-pid="{les.id}-{pr.key}" data-type="{pr.kind}" data-level="{pr.level}"'
    body, sol = [], []
    if pr.prompt:
        body.append(f'<div class="prob-q">{md(pr.prompt)}</div>')
    if pr.kind in ("write", "fix", "refactor"):
        body.append(f'<textarea class="prob-code" aria-label="Your code for problem {n}">{esc(pr.code)}\n</textarea>')
        body.append(f'<script type="text/plain" class="prob-tests">{pr.tests}</script>')
        nt = len(res[f"sol-{pr.key}"]["tests"])
        body.append(f'<details class="disc tests-show"><summary><span class="tag q">Tests</span><span class="q">The {nt} checks Run tests uses</span><span class="chev"></span></summary>'
                    f'<div class="ans">{code_block(pr.tests)}</div></details>')
        sol.append(code_block(pr.solution, "solution.py"))
    elif pr.kind == "predict":
        out = res[f"pred-{pr.key}"]["stdout"]
        attrs += f' data-answer="{esc(out)}"'
        body.append(code_block(pr.code))
        body.append('<div class="answer-row"><textarea class="prob-answer" aria-label="What it prints" placeholder="Type exactly what it prints"></textarea>'
                    '<button class="btn check" type="button">Check</button><span class="check-fb"></span></div>')
        sol.append(output_block(out, "Real output"))
    elif pr.kind == "trace":
        rows = json.loads(res[f"trace-{pr.key}"]["stdout"].splitlines()[-1])
        body.append(code_block(pr._shown))
        head = "".join(f"<th><code>{esc(v)}</code></th>" for v in pr.trace_vars)
        trs, srows = [], []
        for label, vals in rows:
            cells = "".join(f'<td><input class="cell" data-a="{esc(a)}" data-s="{esc(s)}" aria-label="{esc(v)} at {esc(label)}" autocomplete="off"></td>'
                            for v, (a, s) in zip(pr.trace_vars, vals))
            trs.append(f"<tr><td>{esc(label)}</td>{cells}</tr>")
            srows.append(f"<tr><td>{esc(label)}</td>" + "".join(f"<td><code>{esc(a)}</code></td>" for a, _ in vals) + "</tr>")
        body.append(f'<div class="tbl"><table class="trace"><tr><th>step</th>{head}</tr>{"".join(trs)}</table></div>')
        body.append('<div class="answer-row"><button class="btn check" type="button">Check</button><span class="check-fb"></span></div>')
        sol.append(f'<div class="tbl"><table class="trace"><tr><th>step</th>{head}</tr>{"".join(srows)}</table></div>')
    elif pr.kind == "choose":
        attrs += f' data-answer="{pr.answer}"'
        if pr.setup:
            body.append(code_block(pr.setup, "setup"))
        opts = "".join(f'<button class="opt" type="button" data-key="{k}"><b>{k.upper()}</b><pre><code class="py">{esc(c)}</code></pre></button>'
                       for k, c in pr.options.items())
        body.append(f'<div class="opts">{opts}</div><div class="answer-row"><span class="check-fb"></span></div>')
        t = res[f"time-{pr.key}"]["times"]
        rows = "".join(f"<tr><td>{k.upper()}</td><td>{fmt_time(x)}</td></tr>" for k, x in zip(pr.options, t))
        sol.append(f'<div class="tbl"><table><tr><th>Option</th><th>Time per run (measured at build time)</th></tr>{rows}</table></div>')
    hints = "".join(f'<details class="disc hint"><summary><span class="tag">Hint{" " + str(i + 1) if len(pr.hints) > 1 else ""}</span>'
                    f'<span class="q">Open a hint</span><span class="chev"></span></summary><div class="ans">{md(h)}</div></details>'
                    for i, h in enumerate(pr.hints))
    label = "Model answer" if pr.kind == "explain" else "Show the solution and why"
    sol_html = (f'<details class="disc sol"><summary><span class="tag">Solution</span><span class="q">{label}</span><span class="chev"></span></summary>'
                f'<div class="ans">{"".join(sol)}{md(pr.why)}</div></details>')
    tag = f'<span class="ptag">{esc(pr.tag)}</span>' if pr.tag else ""
    return (f'<article class="prob" id="p-{pr.key}" {attrs}>\n<header class="prob-head">{tag}<h3>{n}. {inline(pr.title)}</h3></header>\n'
            + "\n".join(body) + "\n" + hints + sol_html + "\n</article>")


def example_figures(les, s, i, r):
    # matplotlib figures drawn by an example are saved next to the page as PNG files
    imgs = r.get("images") or []
    if not imgs:
        return ""
    folder = ROOT / "lessons" / "img"
    folder.mkdir(exist_ok=True)
    tags = []
    for n, b64 in enumerate(imgs, 1):
        name = f"{les.id}-{s.id}-{i}-{n}.png"
        (folder / name).write_bytes(base64.b64decode(b64))
        tags.append(f'<img src="img/{name}" alt="Figure {n} drawn by the example above" loading="lazy">')
    return f'<div class="o-figs">{"".join(tags)}</div>'


def render_part(les, s, i, x, res, counter):
    if isinstance(x, L.Html):
        return x.html
    if isinstance(x, L.Para):
        return md(x.text)
    if isinstance(x, L.Callout):
        icon = {"sql": "≈", "warn": "!", "bad": "×", "ok": "✓", "key": "i", "note": "•"}.get(x.kind, "i")
        return (f'<div class="callout c-{x.kind}"><div class="ci">{icon}</div><div><div class="ct">{inline(x.title)}</div>{md(x.text)}</div></div>')
    if isinstance(x, L.Figure):
        return f'<figure class="fig"><div class="sv">{x.svg}</div><figcaption>{inline(x.caption)}</figcaption></figure>'
    if isinstance(x, L.Example):
        r = res[f"ex-{s.id}-{i}"]
        out = r["stdout"] + (("\n" if r["stdout"] else "") + r["error"] if r["error"] else "")
        return code_block(x.code, x.label).removesuffix("</div>") + output_block(out) + example_figures(les, s, i, r) + "</div>"
    if isinstance(x, L.Problem):
        counter[0] += 1
        return render_problem(les, x, counter[0], res)
    raise TypeError(x)


def module_name(stage):
    js = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
    m = re.search(rf"\n  {stage}: {{ name: '([^']+)' }}", js)
    return m.group(1) if m else f"Module {stage}"


def render(les, res, version):
    stage = int(re.match(r"m(\d+)", les.id).group(1))
    probs = problems(les)
    lv = {l: sum(p.level == l for p in probs) for l in LEVELS}
    counter = [0]
    secs = []
    for si, s in enumerate(les.sections, 1):
        inner = "\n".join(render_part(les, s, i, x, res, counter) for i, x in enumerate(s.parts))
        secs.append(f'<section class="sec" id="{s.id}">\n<h2><span class="n">{si}</span>{inline(s.title)}</h2>\n{inner}\n</section>')
    theory = (f'<a class="chip" href="https://github.com/SivaRamaNaiduThattikota/python-core-foundations/blob/main/{les.theory}">Full theory notebook →</a>'
              if les.theory else "")
    recap_html = "".join(f"<li>{inline(r)}</li>" for r in les.recap)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{les.num} · {esc(les.title)}</title>
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#F2F2F7" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#000000" media="(prefers-color-scheme: dark)">
<script src="../assets/boot.js"></script>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap">
<link rel="stylesheet" href="../assets/style.css">
<link rel="stylesheet" href="../assets/glass.css">
<link rel="stylesheet" href="../assets/practice.css">
</head>
<body data-id="{les.id}" data-root="../">
<div class="shell"><div class="main">
<main class="content page">

<section class="l-hero">
  <div class="crumbs"><a href="../index.html">Course</a><span>›</span><span>{esc(module_name(stage))}</span></div>
  <h1>{les.num} {esc(les.title)}</h1>
  <p>{inline(les.intro)}</p>
  <div class="chips"><span class="chip">{len(probs)} problems</span><span class="chip">{lv['easy']} easy · {lv['medium']} medium · {lv['hard']} hard</span><span class="chip" id="lesson-score"></span>{theory}</div>
</section>

<details class="toc" id="toc"></details>

{chr(10).join(secs)}

<section class="recap">
  <h2>Recap</h2>
  <ul>{recap_html}</ul>
  <p class="muted">Every output on this page comes from running the code in Python {version} (Pyodide), the same Python that runs your code here.</p>
</section>

<div class="done-bar"><span class="msg" id="done-msg"></span><label class="switch"><input type="checkbox" id="done-toggle"><span class="track"></span>Completed</label></div>
<nav class="pager" id="pager"></nav>

</main>
</div></div>
<script src="../assets/app.js"></script>
<script src="../assets/runner.js"></script>
</body>
</html>
"""


def js_str(s):
    return "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"


def update_manifest(les, n):
    p = ROOT / "assets" / "app.js"
    js = p.read_text(encoding="utf-8")
    entry = (f"  {{ id: '{les.id}', stage: {int(re.match(r'm(\d+)', les.id).group(1))}, num: '{les.num}', file: 'lessons/{les.id}.html', probs: {n},\n"
             f"    title: {js_str(les.title)},\n    desc: {js_str(les.desc)},\n    keys: {js_str(les.keys)} }},\n")
    pat = re.compile(r"  \{ id: '" + re.escape(les.id) + r"',.*?\},\n", re.S)
    if not pat.search(js):
        sys.exit(f"no manifest entry for {les.id} in assets/app.js")
    p.write_text(pat.sub(lambda _: entry, js, count=1), encoding="utf-8")


def write_terms(all_lessons):
    rows = [f"  [{js_str(n)}, {js_str(inline(d))}, '{les.id}']," for les in all_lessons for n, d in les.terms]
    (ROOT / "assets" / "terms.js").write_text(
        "// Generated by build/build.py from the term() calls in src/. Do not edit by hand.\nconst TERMS = [\n"
        + "\n".join(rows) + "\n];\n", encoding="utf-8")


def load(path):
    L.LESSON = None
    runpy.run_path(str(path))
    return L.LESSON


def main():
    srcs = sorted((ROOT / "src").glob("m*.py"))
    only = sys.argv[1:]
    lessons = [load(s) for s in srcs]
    for src, les in zip(srcs, lessons):
        if only and src.stem not in only:
            continue
        out = run_jobs(make_jobs(les))
        bad = check(les, out["results"])
        if bad:
            print(f"{src.name}: {len(bad)} problem(s), nothing written")
            for b in bad:
                print("  -", b)
            sys.exit(1)
        page = render(les, out["results"], out["version"])
        (ROOT / "lessons" / f"{les.id}.html").write_text(page, encoding="utf-8")
        update_manifest(les, len(problems(les)))
        print(f"{src.name}: ok, {len(problems(les))} problems, Python {out['version']}")
    write_terms(lessons)


if __name__ == "__main__":
    main()
