"""Building blocks for lesson source files in src/.

A lesson file calls these functions. Nothing is rendered here: the build first runs
every snippet in Pyodide, checks the results, then turns the blocks into HTML.
"""
import re
import textwrap
from dataclasses import dataclass, field


def dedent(s):
    return textwrap.dedent(s).strip("\n")


# ---------- content blocks ----------

@dataclass
class Html:
    html: str


@dataclass
class Para:
    text: str


@dataclass
class Example:
    code: str
    label: str = "example.py"
    error_ok: bool = False      # the point of the example is the error


@dataclass
class Callout:
    kind: str                   # key, warn, sql, ok, bad, note
    title: str
    text: str


@dataclass
class Figure:
    svg: str
    caption: str


@dataclass
class Problem:
    kind: str                   # write fix refactor predict trace choose explain
    key: str
    title: str
    level: str                  # easy medium hard
    prompt: str = ""
    code: str = ""              # starter (write/fix/refactor) or code to read (predict/trace)
    tests: str = ""
    solution: str = ""
    why: str = ""
    hints: list = field(default_factory=list)
    trace_vars: list = field(default_factory=list)
    setup: str = ""             # choose: shared setup
    options: dict = field(default_factory=dict)
    answer: str = ""            # choose: the right key
    tag: str = ""               # optional label: "Interview", "Data work"


@dataclass
class Section:
    id: str
    title: str
    parts: list


@dataclass
class Lesson:
    id: str
    num: str
    title: str
    intro: str
    desc: str
    keys: str = ""
    theory: str = ""            # path of the matching theory notebook, if any
    sections: list = field(default_factory=list)
    recap: list = field(default_factory=list)
    terms: list = field(default_factory=list)


LESSON = None


def lesson(**kw):
    global LESSON
    LESSON = Lesson(**kw)
    return LESSON


def section(id, title, *parts):
    LESSON.sections.append(Section(id, title, list(parts)))


def recap(*points):
    LESSON.recap.extend(points)


def term(name, definition):
    LESSON.terms.append((name, definition))


def html(s): return Html(dedent(s))
def p(s): return Para(dedent(s))
def ex(code, label="example.py", error_ok=False): return Example(dedent(code), label, error_ok)
def callout(kind, title, text): return Callout(kind, title, dedent(text))
def fig(svg, caption): return Figure(dedent(svg), caption)


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40]


def _prob(kind, title, level, key=None, **kw):
    for k in ("prompt", "code", "tests", "solution", "why", "setup"):
        if k in kw and isinstance(kw[k], str):
            kw[k] = dedent(kw[k])
    if "options" in kw:
        kw["options"] = {k: dedent(v) for k, v in kw["options"].items()}
    return Problem(kind=kind, key=key or _slug(title), title=title, level=level, **kw)


def write(title, level, **kw): return _prob("write", title, level, **kw)
def fix(title, level, **kw): return _prob("fix", title, level, **kw)
def refactor(title, level, **kw): return _prob("refactor", title, level, **kw)
def predict(title, level, **kw): return _prob("predict", title, level, **kw)
def trace(title, level, **kw): return _prob("trace", title, level, **kw)
def choose(title, level, **kw): return _prob("choose", title, level, **kw)
def explain(title, level, **kw): return _prob("explain", title, level, **kw)
