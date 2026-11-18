// Grading code shared by the browser worker and the build, so both judge code the same way.
export const HELPER = `
import ast, builtins, sys, traceback

def _no_input(*args):
    raise RuntimeError("input() does not work in the browser. Copy this one and run it locally.")

def _format(e):
    te = traceback.TracebackException.from_exception(e)
    te.stack = traceback.StackSummary.from_list(
        [f for f in te.stack if f.filename in ("main.py", "tests.py")])
    return "".join(te.format()).rstrip()

def _why(node, ns):
    # For "assert a == b" show what a actually was, which is what you want to see first.
    # Asserts nested inside try/for blocks get no detail.
    if not isinstance(node, ast.Assert):
        return ""
    t = node.test
    if not (isinstance(t, ast.Compare) and len(t.ops) == 1):
        return ""
    try:
        left = eval(compile(ast.Expression(t.left), "tests.py", "eval"), ns)
        right = eval(compile(ast.Expression(t.comparators[0]), "tests.py", "eval"), ns)
    except Exception:
        return ""
    if isinstance(t.ops[0], ast.Eq):
        return f"got {left!r}, expected {right!r}"
    return f"left side was {left!r}, right side was {right!r}"

def _run(code, tests):
    ns = {"__name__": "__main__", "input": _no_input, "__source__": code}
    res = {"error": None, "tests": []}
    try:
        exec(compile(code, "main.py", "exec"), ns)
    except BaseException as e:
        res["error"] = _format(e)
    if res["error"] is None and tests.strip():
        tree = ast.parse(tests, "tests.py")
        for node in tree.body:
            src = ast.get_source_segment(tests, node)
            is_test = isinstance(node, ast.Assert)
            try:
                exec(compile(ast.Module([node], []), "tests.py", "exec"), ns)
                if is_test:
                    res["tests"].append([src, True, ""])
            except AssertionError as e:
                res["tests"].append([src, False, str(e) or _why(node, ns) or "assert failed"])
            except BaseException as e:
                res["tests"].append([src, False, type(e).__name__ + ": " + str(e)])
    sys.stdout.flush(); sys.stderr.flush()
    return res

# Module 13 lessons grade test files by running real pytest on them.
# lessontools.run_pytest(test_source, modules) writes the modules and the test file
# to a fresh folder, runs pytest there and returns the outcome of every test.
_LESSONTOOLS = """
import contextlib, io, os, sys, tempfile, textwrap

class _Collector:
    def __init__(self):
        self.results = {}
        self.errors = []

    def pytest_runtest_logreport(self, report):
        name = report.nodeid.split("::", 1)[-1]
        if hasattr(report, "wasxfail"):
            self.results[name] = "xfailed" if report.skipped else "xpassed"
        elif report.when == "call":
            self.results[name] = report.outcome
        elif report.outcome != "passed":
            self.results[name] = "error" if report.failed else "skipped"

    def pytest_collectreport(self, report):
        if report.failed:
            self.errors.append(str(report.longrepr))

def run_pytest(test_source, modules=None, args=()):
    import pytest
    modules = dict(modules or {})
    folder = tempfile.mkdtemp()
    for name, src in modules.items():
        with open(os.path.join(folder, name + ".py"), "w", encoding="utf-8") as f:
            f.write(textwrap.dedent(src))
    with open(os.path.join(folder, "test_main.py"), "w", encoding="utf-8") as f:
        f.write(test_source)
    names = list(modules) + ["test_main"]
    for name in names:
        sys.modules.pop(name, None)
    collector = _Collector()
    out = io.StringIO()
    sys.path.insert(0, folder)
    try:
        with contextlib.redirect_stdout(out):
            code = pytest.main([folder, "-q", "-p", "no:cacheprovider", "--no-header", *args], plugins=[collector])
    finally:
        sys.path.remove(folder)
        for name in names:
            sys.modules.pop(name, None)
    values = list(collector.results.values())
    return {"exit": int(code), "outcomes": collector.results, "passed": values.count("passed"),
            "failed": values.count("failed") + values.count("error"), "skipped": values.count("skipped"),
            "errors": collector.errors, "output": out.getvalue()}

def swap_impl(source, impl):
    # Replaces the lines between "# --- code under test" and "# --- tests" with impl.
    lines = source.splitlines(keepends=True)
    start = next(i for i, line in enumerate(lines) if line.startswith("# --- code under test"))
    end = next(i for i, line in enumerate(lines) if line.startswith("# --- tests"))
    body = textwrap.dedent(impl).strip(chr(10)) + chr(10) * 3
    return "".join(lines[:start + 1] + [body] + lines[end:])
"""

def _install_lessontools():
    import types
    mod = types.ModuleType("lessontools")
    exec(_LESSONTOOLS, mod.__dict__)
    sys.modules["lessontools"] = mod

_install_lessontools()

def _time(setup, stmts, number=0):
    # Times each statement after the same setup. Used by the build for "pick the faster one".
    import timeit
    ns = {}
    exec(setup, ns)
    out = []
    for st in stmts:
        t = timeit.Timer(st, globals=ns)
        n = number or t.autorange()[0]
        out.append(min(t.repeat(3, n)) / n)
    return out
`;
