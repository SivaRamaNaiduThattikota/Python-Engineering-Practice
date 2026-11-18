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

def make_tree(files, on_path=True):
    # Writes {relative path: source} into a fresh folder, like a small project on disk,
    # and puts that folder first on sys.path so its modules and packages can be imported.
    import importlib, tempfile
    from pathlib import Path
    root = Path(tempfile.mkdtemp())
    for rel, src in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(src), encoding="utf-8")
    if on_path:
        sys.path.insert(0, str(root))
    importlib.invalidate_caches()
    return root

def forget(*names):
    # Removes modules (and their submodules) from the import cache, so the next import runs them again.
    for mod in list(sys.modules):
        if any(mod == n or mod.startswith(n + ".") for n in names):
            del sys.modules[mod]

def make_module(name, source):
    # Creates an importable module from source, as if it were the file name + ".py".
    import types
    mod = types.ModuleType(name)
    mod.__file__ = name + ".py"
    sys.modules[name] = mod
    exec(compile(textwrap.dedent(source), name + ".py", "exec"), mod.__dict__)
    return mod

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

# Module 14: the browser cannot start threads or processes, and asyncio.run needs a
# feature most browsers lack. asyncio.run gets a small event loop that runs on simulated
# time (sleep(1) returns at once but advances loop.time() by 1), and the executors and
# Thread.start run each task immediately, in order, with the same API.
def _install_concurrency():
    if sys.platform != "emscripten":
        return
    import asyncio, asyncio.base_events as _be, asyncio.events as _ev
    import concurrent.futures as _cf, threading as _th

    class _Selector:
        def __init__(self, loop):
            self.loop = loop

        def select(self, timeout=None):
            if timeout is None:
                raise RuntimeError("event loop would wait forever: no task can make progress (a deadlock)")
            if timeout > 0:
                self.loop._now += timeout
            return []

    class VirtualTimeLoop(_be.BaseEventLoop):
        def __init__(self):
            super().__init__()
            self._now = 0.0
            self._selector = _Selector(self)

        def time(self):
            return self._now

        def _process_events(self, events):
            pass

        def _write_to_self(self):
            pass

    def run(main, *, debug=None, loop_factory=None):
        outer = _ev._get_running_loop()
        _ev._set_running_loop(None)
        loop = VirtualTimeLoop()
        try:
            return loop.run_until_complete(main)
        finally:
            try:
                loop.run_until_complete(loop.shutdown_asyncgens())
            finally:
                loop.close()
                _ev._set_running_loop(outer)

    asyncio.run = run

    class InlineExecutor(_cf.Executor):
        def __init__(self, max_workers=None, *args, initializer=None, initargs=(), **kwargs):
            self._max_workers = max_workers
            self._closed = False
            if initializer is not None:
                initializer(*initargs)

        def submit(self, fn, /, *args, **kwargs):
            if self._closed:
                raise RuntimeError("cannot schedule new futures after shutdown")
            future = _cf.Future()
            try:
                future.set_result(fn(*args, **kwargs))
            except BaseException as e:
                future.set_exception(e)
            return future

        def shutdown(self, wait=True, *, cancel_futures=False):
            self._closed = True

    import io as _io, pickle as _pickle, types as _types

    class _ProcessPickler(_pickle.Pickler):
        # Real processes receive the function, arguments and results by pickling.
        # Functions and classes travel by name, so only top-level ones work.
        def reducer_override(self, obj):
            if isinstance(obj, (_types.FunctionType, type)):
                name = getattr(obj, "__qualname__", "")
                if "<lambda>" in name or "<locals>" in name:
                    raise _pickle.PicklingError(
                        f"Can't pickle {obj!r}: a process can only receive functions and classes defined at the top level of a module")
                if getattr(obj, "__module__", None) == "__main__":
                    return (str, (name,))
            return NotImplemented

    def _check_picklable(obj):
        _ProcessPickler(_io.BytesIO()).dump(obj)

    class InlineProcessExecutor(InlineExecutor):
        def submit(self, fn, /, *args, **kwargs):
            if self._closed:
                raise RuntimeError("cannot schedule new futures after shutdown")
            future = _cf.Future()
            try:
                _check_picklable((fn, args, kwargs))
                result = fn(*args, **kwargs)
                _check_picklable(result)
                future.set_result(result)
            except BaseException as e:
                future.set_exception(e)
            return future

    _cf.ThreadPoolExecutor = InlineExecutor
    _cf.ProcessPoolExecutor = InlineProcessExecutor

    def _start(self):
        self._started.set()
        try:
            self.run()
        except BaseException as e:
            _th.excepthook(_th.ExceptHookArgs((type(e), e, e.__traceback__, self)))

    _th.Thread.start = _start
    _th.Thread.join = lambda self, timeout=None: None
    _th.Thread.is_alive = lambda self: False

_install_concurrency()

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
