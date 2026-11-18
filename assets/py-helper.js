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
    ns = {"__name__": "__main__", "input": _no_input}
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
