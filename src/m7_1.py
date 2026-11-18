from lesson import *
from diagrams import *

lesson(
    id="m7-1", num="7.1", title="Exceptions and try / except",
    intro="What happens when an error is raised, how it travels up the call stack, and how to read a traceback. "
          "`try`, `except`, `else` and `finally` step by step, the exception hierarchy, and catching narrowly so real "
          "bugs stay visible. Applied to parsing data rows, model replies and configuration files.",
    desc="How exceptions travel, `else` and `finally`, the hierarchy, catching narrowly.",
    keys="exception try except else finally raise traceback call stack hierarchy baseexception exception valueerror typeerror keyerror lookuperror oserror filenotfounderror jsondecodeerror catch narrowly bare except",
)

term("Exception", "An object describing an error, raised to stop normal execution. It travels up the call stack until a matching `except` handles it.")
term("Traceback", "The report Python prints for an unhandled exception: the chain of calls that led to it, oldest first, and the error on the last line.")
term("Call stack", "The list of function calls currently running, each waiting for the one it called to return.")
term("Exception hierarchy", "Exception classes inherit from each other, so `except LookupError` also catches `KeyError` and `IndexError`.")

section("travel", "What happens when an exception is raised",
    fig(stage_map(7, "a resilient JSON client"), "Module 7 at a glance: how exceptions travel, how to raise and design them, and how remote calls fail, building up to a client that survives all of it."),
    fig(flowchart({
        "raise": ("bad", 1, 0, "an exception is raised"),
        "here": ("ask", 1, 1, "a matching except|in this function?"),
        "handle": ("good", 2, 1, "run that handler,|continue after try"),
        "caller": ("ask", 1, 2, "is there a caller?"),
        "up": ("step", 0, 2, "leave this function,|go to the caller"),
        "crash": ("bad", 1, 3, "traceback printed,|program stops"),
    }, [("raise", "here"), ("here", "handle", "yes"), ("here", "caller", "no"), ("caller", "up", "yes"),
        ("up", "here", "", {"route": [(0, 1)]}), ("caller", "crash", "no")], cell=(210, 80),
        label="an exception travels up the call stack until a handler matches"),
        "An exception climbs the call stack function by function until an `except` matches its type; if none does, the program stops with a traceback."),
    p("""An **exception** is an object that describes an error. When Python hits a problem it cannot continue from, such as dividing
    by zero, a missing dict key or a string that is not a number, it **raises** an exception: it creates the exception object
    and stops running the current code immediately. No further line of that block runs. What happens next depends on whether
    anyone is ready to **handle** it."""),
    p("""To understand where an exception goes, picture the **call stack**: the list of function calls that are currently running.
    If `main` calls `load`, which calls `parse`, all three are on the stack, each paused and waiting for the one it called to
    return. When `parse` raises, Python looks for a handler (a matching `except`) in `parse`. If there is none, `parse` is
    abandoned and the exception travels to `load`, at the line that called `parse`. If `load` has no handler either, it is
    abandoned too, and so on up the stack. This is called **unwinding**. If the exception reaches the top without being
    handled, the program stops and prints a **traceback**."""),
    ex("""
    def parse(text):
        print("  parse starts")
        value = int(text)            # raises ValueError for "abc"
        print("  parse done")        # never runs for bad input
        return value

    def load(text):
        print(" load starts")
        result = parse(text) * 2
        print(" load done")          # skipped too: the exception passed through load
        return result

    def main():
        try:
            print(load("21"))
            print(load("abc"))
        except ValueError as e:
            print("main handled:", e)

    main()
    """, "unwinding.py"),
    p("""The second call shows the whole journey: `parse` stops at `int(text)`, `load` stops at the line that called `parse`, and
    the first matching handler, in `main`, receives the exception. Neither "done" line runs. Everything between the `raise` and
    the handler is skipped, which is the point: the code after a failed step usually cannot work, so Python does not try."""),
    p("""A **traceback** is the record of that journey. It lists the calls from the **oldest** (the top of your program) to the
    **most recent** (where the error happened), hence its header "most recent call last", and the **last line** names the
    exception type and message. Read it from the bottom: first what went wrong, then where, then how the program got there.
    The `traceback` module can format the same report as a string, which is what logging uses (7.3)."""),
    ex("""
    import traceback

    def parse(text):
        return int(text)

    def load(text):
        return parse(text) * 2

    try:
        load("abc")
    except ValueError:
        report = traceback.format_exc()
    lines = report.strip().splitlines()
    print(lines[0])
    print([l.split(", in ")[-1] for l in lines if l.strip().startswith("File")])   # oldest call first
    print(lines[-1])
    """, "traceback_parts.py"),
)

section("except", "`try` and `except`: catching by type",
    p("""A `try` block marks code whose exceptions you want to handle. After it come one or more `except` clauses, each naming the
    exception types it handles. When an exception is raised inside the `try` block, Python checks the `except` clauses **from
    top to bottom** and runs the **first** one whose type matches. "Matches" means `isinstance(exception, that_type)`: the
    exception is of that class or of a **subclass** of it. If none matches, the exception continues up the stack as if there
    were no `try` at all. If no exception happens, all the `except` clauses are skipped."""),
    ex("""
    def to_number(text):
        try:
            return float(text)
        except ValueError as e:
            print("  bad text:", e)
        except TypeError as e:
            print("  not a string:", e)
        return None

    print(to_number("3.5"), to_number("3,5"), to_number(None))
    """, "except_basics.py"),
    p("""`as e` binds the exception object to a name, so you can read its message with `str(e)` and its arguments with `e.args`.
    Several types can share one handler as a tuple, `except (ValueError, TypeError) as e:`. Because the first match wins, put
    **specific** types before **general** ones: an `except Exception` placed first would catch everything, and the specific
    clauses below it could never run (problem 3)."""),
    p("""One scope detail surprises people: at the end of the `except` block, Python **deletes** the name bound with `as`. The
    exception object refers to the whole traceback, which refers to every local variable of every frame involved, so keeping it
    alive would keep all of them alive. If you need the exception later, assign it to another name inside the block."""),
    ex("""
    try:
        {}["model"]
    except KeyError as e:
        print(repr(e), e.args, str(e))
        saved = e
    try:
        print(e)
    except NameError as missing:
        print("NameError:", missing)
    print(type(saved).__name__)
    """, "except_name.py"),
    p("""Notice that `str(e)` for a `KeyError` is the key's **repr**, with quotes, which is why logs show `KeyError: 'model'`. Most
    other exceptions just hold their message."""),
)

section("elsefinally", "`else` and `finally`: what runs when",
    fig(table(["what happens in try", "except", "else", "finally"], [
        ["no exception", "skipped", "runs", "runs"],
        ["exception, a handler matches", "runs", "skipped", "runs"],
        ["exception, no handler matches", "skipped", "skipped", "runs, then it propagates"],
    ], hl={(0, 3), (1, 3), (2, 3)}, label="which blocks run in each case"),
        "`finally` runs in every case; `else` runs only when the `try` body finished without an exception."),
    p("""A `try` statement can have two more clauses. **`else`** runs only if the `try` block finished **without** an exception.
    **`finally`** runs **always**, whether the block succeeded, raised an exception that was handled, raised one that was not
    handled, or left early with `return`, `break` or `continue`. The full order is: `try` block; then either the matching
    `except` (on error) or `else` (on success); then `finally`; then, if an exception is still unhandled, it continues up the
    stack."""),
    ex("""
    def attempt(text):
        try:
            print("  try")
            n = int(text)
        except ValueError:
            print("  except")
            return "bad"
        else:
            print("  else")
            return n * 2
        finally:
            print("  finally")

    print(attempt("4"))
    print(attempt("x"))
    """, "order.py"),
    p("""`finally` ran in both cases, and it ran **after** the `return` statement was reached but **before** the function actually
    returned: the return value is set aside, `finally` runs, then the function returns. That is what makes `finally` the place
    for cleanup that must happen no matter what: closing a file or connection, releasing a lock, stopping a timer, deleting a
    temporary file. (A `with` block, 10.2, packages exactly this pattern, and is usually the better tool.)"""),
    p("""`else` exists to keep the `try` block **small**. Code in the `try` block is covered by the `except` clauses, so if you put
    the follow-up work there too, an error in the follow-up could be caught by a handler meant for something else. Moving it
    to `else` means "only run this if the risky step worked, and do not catch its errors here"."""),
    ex("""
    import warnings

    code = '''
    def f():
        try:
            raise ValueError("lost")
        finally:
            return "finally won"
    '''
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        namespace = {}
        exec(compile(code.strip(), "<demo>", "exec"), namespace)
    print(namespace["f"](), [w.category.__name__ for w in caught])
    """, "return_in_finally.py"),
    p("""Never `return` (or `break` or `continue`) from inside `finally`. The `return` replaces whatever was happening, so an
    exception that was on its way up is silently **discarded**, as the example shows. Python 3.14 now warns about it with a
    `SyntaxWarning` when the code is compiled (PEP 765), but older versions accept it silently (problem 10)."""),
)

section("hierarchy", "The exception hierarchy",
    fig(flowchart({
        "base": ("accent", 2, 0, "BaseException"),
        "sys": ("step", 0, 1, "SystemExit"),
        "kb": ("step", 1, 1, "KeyboardInterrupt"),
        "exc": ("accent2", 3, 1, "Exception"),
        "val": ("step", 2, 2, "ValueError"),
        "look": ("step", 3, 2, "LookupError"),
        "os": ("step", 5, 2, "OSError"),
        "key": ("step", 3, 3, "KeyError"),
        "idx": ("step", 4, 3, "IndexError"),
        "fnf": ("step", 5, 3, "FileNotFoundError"),
    }, [("base", "sys"), ("base", "kb"), ("base", "exc"), ("exc", "val"), ("exc", "look"), ("exc", "os"),
        ("look", "key"), ("look", "idx"), ("os", "fnf")], cell=(160, 70), label="part of the built-in exception hierarchy"),
        "`except LookupError` also catches `KeyError` and `IndexError`; `except Exception` deliberately leaves out `SystemExit` and `KeyboardInterrupt`."),
    p("""Exception types are classes arranged in a tree, and that tree decides what each `except` clause catches. At the root is
    `BaseException`. Directly under it are a few special exceptions that are **not errors** in the usual sense:
    `KeyboardInterrupt` (the user pressed Ctrl+C), `SystemExit` (raised by `sys.exit()`), and `GeneratorExit` (used to close
    generators, 6.3). Everything that represents an actual error is under `Exception`. That is why `except Exception` is the
    widest handler you should normally write: it catches every error but still lets Ctrl+C and `sys.exit()` stop the
    program."""),
    html("""<div class="tbl"><table>
      <tr><th>Exception</th><th>Parent</th><th>Typical cause</th></tr>
      <tr><td><code>ValueError</code></td><td><code>Exception</code></td><td>right type, bad value: <code>int("abc")</code></td></tr>
      <tr><td><code>TypeError</code></td><td><code>Exception</code></td><td>wrong type: <code>"a" + 1</code>, calling with wrong arguments</td></tr>
      <tr><td><code>KeyError</code>, <code>IndexError</code></td><td><code>LookupError</code></td><td>missing dict key, list index out of range</td></tr>
      <tr><td><code>ZeroDivisionError</code></td><td><code>ArithmeticError</code></td><td>dividing by zero</td></tr>
      <tr><td><code>FileNotFoundError</code>, <code>PermissionError</code>, <code>TimeoutError</code></td><td><code>OSError</code></td><td>file system, network, operating system</td></tr>
      <tr><td><code>json.JSONDecodeError</code>, <code>UnicodeDecodeError</code></td><td><code>ValueError</code></td><td>invalid JSON, bytes that are not valid in the encoding</td></tr>
      <tr><td><code>AttributeError</code>, <code>NameError</code></td><td><code>Exception</code></td><td>usually a bug: a typo or a <code>None</code> where an object was expected</td></tr>
    </table></div>"""),
    ex("""
    import json

    for exc in [KeyError, json.JSONDecodeError, FileNotFoundError, KeyboardInterrupt]:
        print(exc.__name__, "->", [c.__name__ for c in exc.__mro__[1:-1]])

    try:
        json.loads("{bad")
    except ValueError as e:
        print("caught as ValueError:", type(e).__name__)
    """, "hierarchy.py"),
    p("""The tree has practical consequences. `except ValueError` also catches `JSONDecodeError` and `UnicodeDecodeError`, so a
    handler written for "the number was invalid" may quietly swallow "the file was not valid JSON" too. `except LookupError`
    handles both missing keys and bad indexes. `except OSError` covers most input/output failures at once. And a **bare**
    `except:` (with no type) is the same as `except BaseException:`: it catches Ctrl+C and `sys.exit()` as well, which can make
    a program impossible to stop. Never write it; if you truly want "any error", write `except Exception` and log it."""),
)

section("narrow", "Catching narrowly",
    fig(flowchart({
        "ask": ("ask", 0, 0, "can this code do something|useful about the error?"),
        "catch": ("good", 1, 0, "catch that specific type|and handle it"),
        "let": ("step", 0, 1, "let it propagate to|a layer that can"),
    }, [("ask", "catch", "yes"), ("ask", "let", "no")], cell=(270, 90), label="catch only what you can handle"),
        "Catch an exception only where you can recover from it, and only the types you expect; everything else should travel on."),
    p("""The hardest part of exception handling is not the syntax but deciding **what not to catch**. A handler is a promise: "if
    this goes wrong, I know what to do instead". Every exception you catch without being able to keep that promise turns a loud
    bug into a silent wrong result. Three rules follow from that:"""),
    p("""- **Catch the specific type** you expect (`ValueError` for a bad number, `FileNotFoundError` for a missing file), not
      `Exception`.
    - **Keep the `try` block as small as possible**: just the statement that can fail in the way you expect. Move the rest to
      `else` or after the statement.
    - **Only catch what you can handle**: retry, use a default, skip and record, or add context and re-raise (7.2). If you
      cannot do any of these, let it propagate."""),
    ex("""
    rows = [{"id": 1, "price": "9.5"}, {"id": 2, "price": "n/a"}, {"id": 3, "prce": "4"}]

    def total_broad(rows):
        total = 0.0
        for row in rows:
            try:
                total += float(row["price"])   # also hides the misspelled key
            except Exception:
                pass
        return total

    def total_narrow(rows):
        total, bad = 0.0, []
        for row in rows:
            raw = row.get("price")
            if raw is None:
                bad.append((row["id"], "missing price"))
                continue
            try:
                value = float(raw)
            except ValueError:
                bad.append((row["id"], f"not a number: {raw!r}"))
            else:
                total += value
        return total, bad

    print(total_broad(rows))
    print(total_narrow(rows))
    """, "narrow.py"),
    p("""Both versions return `9.5`, but only the second one tells you **why** the other two rows were not counted, and only it
    distinguishes a bad value from a missing field. The broad handler would also have hidden a real bug, such as a `NameError`
    from a typo in the loop, by treating it like a bad price. There is one legitimate place for a broad `except Exception`: a
    **boundary** where one failure must not stop everything else, such as the loop over requests in a server or over records
    in a batch job. There, catch broadly, log the full traceback, record the failure, and move on to the next item (7.3, 7.4)."""),
    callout("sql", "SQL / Power BI", """A `try`/`except` around one conversion is like `TRY_CAST(x AS FLOAT)` in SQL Server or
    `try ... otherwise` in Power Query: the bad value becomes `NULL` (or a default) instead of failing the whole query. Wrapping
    an entire query in an error handler that returns an empty table is the broad `except` equivalent, and just as risky: the
    report looks fine and is wrong."""),
)

section("cost", "What exceptions cost",
    p("""Entering a `try` block is essentially free in modern Python (3.11 made the no-exception path "zero-cost"). **Raising** and
    catching an exception is not: Python creates the exception object, records the traceback and unwinds the stack, which is
    much slower than an `if` test. So exceptions are the right tool for **exceptional** cases, the ones that rarely happen, and
    a poor tool for normal control flow in a hot loop where the "error" happens most of the time (problem 8). For a dict where
    keys are often missing, `d.get(key, default)` is both clearer and faster than catching `KeyError`."""),
    ex("""
    import timeit

    d = {"a": 1}
    def with_get():
        return d.get("zzz", 0)

    def with_except():
        try:
            return d["zzz"]
        except KeyError:
            return 0

    t_get = timeit.timeit(with_get, number=200_000)
    t_exc = timeit.timeit(with_except, number=200_000)
    print(t_exc > t_get)
    """, "exception_cost.py"),
)

section("warmup", "Warm-up",
    predict("try, except, else and finally", "easy",
        code="""
        def run(x):
            try:
                result = 10 / x
            except ZeroDivisionError:
                print("divide by zero")
                result = None
            else:
                print("ok", result)
            finally:
                print("finally", x)
            return result

        print(run(4))
        print(run(0))
        """,
        hints=["`else` runs only when the `try` block raised nothing. `finally` always runs."],
        why="""For 4, the division succeeds, so `except` is skipped, `else` prints the result, `finally` prints, and the function returns
        2.5. For 0, `ZeroDivisionError` is raised, its handler runs, `else` is skipped, `finally` still prints, and the function
        returns `None`. The `print` of the return value happens in the caller, after `finally`."""),
    write("Parse an integer with a default", "easy", tag="Data work",
        prompt="""Write `to_int(value, default=None)` that converts strings such as `" 42 "` or `"-7"`, and numbers, to `int`,
        returning `default` when the value cannot be converted: text that is not an integer, `None`, or other types. Floats with
        a fractional part such as `3.5` count as invalid; `3.0` is fine. Do not use a bare `except` or `except Exception`.""",
        code="""
        def to_int(value, default=None):
            pass
        """,
        tests="""
        assert to_int(" 42 ") == 42 and to_int("-7") == -7 and to_int(5) == 5
        assert to_int("4.0") is None and to_int("abc", 0) == 0 and to_int("", -1) == -1
        assert to_int(None, 0) == 0 and to_int([1], 0) == 0
        assert to_int(3.0) == 3 and to_int(3.5, "bad") == "bad"
        """,
        hints=["`int(\" 42 \")` already ignores surrounding spaces. `int(None)` raises `TypeError`, `int(\"abc\")` raises `ValueError`.",
               "For floats, check `value.is_integer()` before converting, because `int(3.5)` silently truncates to 3."],
        solution="""
        def to_int(value, default=None):
            if isinstance(value, float):
                return int(value) if value.is_integer() else default
            try:
                return int(value)
            except (ValueError, TypeError):
                return default
        """,
        why="""`int()` raises `ValueError` for text that is not an integer (including `"4.0"` and `""`) and `TypeError` for things that are
        not text or numbers (`None`, lists), so one handler with a tuple covers exactly the expected failures and nothing else.
        Floats need a check before the `try`, because `int(3.5)` does not fail: it silently truncates to `3`, which is the worst
        kind of conversion bug. Note that `bool` is a subclass of `int`, so `to_int(True)` returns `1`; whether that is acceptable
        depends on the data."""),
    fix("The specific handler never runs", "easy", tag="Data work",
        prompt="""`read_amount(text)` should return `("ok", value)`, `("bad number", text)` for text that is not a number, and
        `("error", type name)` for anything else. Bad numbers are reported as generic errors. Fix it.""",
        code="""
        def read_amount(text):
            try:
                return ("ok", float(text))
            except Exception as e:
                return ("error", type(e).__name__)
            except ValueError:
                return ("bad number", text)
        """,
        tests="""
        assert read_amount("9.5") == ("ok", 9.5)
        assert read_amount("9,5") == ("bad number", "9,5")
        assert read_amount(None) == ("error", "TypeError")
        """,
        hints=["`except` clauses are checked from top to bottom, and `ValueError` is a subclass of `Exception`."],
        solution="""
        def read_amount(text):
            try:
                return ("ok", float(text))
            except ValueError:
                return ("bad number", text)
            except Exception as e:
                return ("error", type(e).__name__)
        """,
        why="""Python runs the **first** matching clause. Every `ValueError` is an `Exception`, so the general clause matched first and the
        specific one was unreachable. Put specific types before general ones. Linters such as Ruff and Pylint warn about this
        ordering, which is a good reason to run one."""),
    predict("Which handler catches it", "easy",
        code="""
        import json

        def which(action):
            try:
                action()
            except LookupError as e:
                return "lookup: " + type(e).__name__
            except ValueError as e:
                return "value: " + type(e).__name__
            except OSError as e:
                return "os: " + type(e).__name__

        print(which(lambda: {}["k"]), which(lambda: [][3]))
        print(which(lambda: json.loads("{")), which(lambda: b"\\xff".decode("utf-8")))
        print(which(lambda: open("/no/such/file.txt")), which(lambda: int("x")))
        """,
        hints=["`KeyError` and `IndexError` are `LookupError`s; `JSONDecodeError` and `UnicodeDecodeError` are `ValueError`s; `FileNotFoundError` is an `OSError`."],
        why="""Each `except` matches its class **and all subclasses**, so the handler tells you the family and `type(e).__name__` the exact
        class. The middle line is the surprising one: invalid JSON and invalid UTF-8 are both caught by `except ValueError`, so a
        handler written for "bad number" catches them too, which can hide the real problem."""),
)

section("medium", "Medium",
    write("Parse rows, collect the failures", "medium", tag="Data work",
        prompt="""Write `parse_rows(rows)` for CSV-like rows (lists of strings) with the columns `id`, `name`, `score`. Return
        `(good, errors)`: `good` is a list of dicts with `id` as `int`, `name` stripped and `score` as `float`; `errors` is a list of
        `(row_number, message)` for rows that could not be parsed, numbered from 1. One bad row must not stop the others. Messages:
        `"expected 3 fields, got N"`, `"bad id: '...'"`, `"bad score: '...'"` (with the repr of the raw value).""",
        code="""
        def parse_rows(rows):
            pass
        """,
        tests="""
        rows = [["1", " Ana ", "0.9"], ["2", "Bo"], ["x", "Cy", "0.5"], ["4", "Dee", "high"], ["5", "Ed", " 0.75 "]]
        good, errors = parse_rows(rows)
        assert good == [{"id": 1, "name": "Ana", "score": 0.9}, {"id": 5, "name": "Ed", "score": 0.75}]
        assert errors == [(2, "expected 3 fields, got 2"), (3, "bad id: 'x'"), (4, "bad score: 'high'")]
        assert parse_rows([]) == ([], [])
        """,
        hints=["Check the field count with an `if` first; that is not an exceptional case worth an exception.",
               "Convert `id` and `score` in separate `try` blocks, so each error message can name the field."],
        solution="""
        def parse_rows(rows):
            good, errors = [], []
            for n, row in enumerate(rows, start=1):
                if len(row) != 3:
                    errors.append((n, f"expected 3 fields, got {len(row)}"))
                    continue
                raw_id, name, raw_score = row
                try:
                    row_id = int(raw_id)
                except ValueError:
                    errors.append((n, f"bad id: {raw_id!r}"))
                    continue
                try:
                    score = float(raw_score)
                except ValueError:
                    errors.append((n, f"bad score: {raw_score!r}"))
                    continue
                good.append({"id": row_id, "name": name.strip(), "score": score})
            return good, errors
        """,
        why="""Each `try` block holds exactly one conversion, so the handler knows which field failed and can say so. The field count is a
        normal condition to test with `if`, not to discover through an unpacking `ValueError`, which would also give a vague message.
        Collecting `(row, message)` pairs and continuing is how data loaders behave in practice: the caller decides whether 3 bad rows
        out of 5 is acceptable. `{raw!r}` shows the raw value with quotes, so an empty string or trailing spaces are visible in the
        message (5.3). `float(" 0.75 ")` accepts surrounding spaces, as `int` does."""),
    fix("A handler that hides a bug", "medium", tag="Data work",
        prompt="""`enrich(records, prices)` adds a `"total"` to each record from its quantity and the product's price, using
        `None` when the product is unknown. It returns `None` totals for everything, because of a typo, and the broad handler hides
        it. Fix the typo and narrow the handler so that only a missing product is handled.""",
        code="""
        def enrich(records, prices):
            out = []
            for r in records:
                try:
                    price = prices[r["product"]]
                    total = round(price * r["qty"], 2)
                    out.append({**r, "total": totl})
                except Exception:
                    out.append({**r, "total": None})
            return out
        """,
        tests="""
        prices = {"pen": 1.5, "book": 12.0}
        records = [{"product": "pen", "qty": 4}, {"product": "lamp", "qty": 1}, {"product": "book", "qty": 2}]
        assert enrich(records, prices) == [{"product": "pen", "qty": 4, "total": 6.0},
                                           {"product": "lamp", "qty": 1, "total": None},
                                           {"product": "book", "qty": 2, "total": 24.0}]
        assert enrich([], prices) == []
        try:
            enrich([{"product": "pen"}], prices)
            assert False, "a record without qty is a bug and should raise"
        except KeyError as e:
            assert "qty" in str(e)
        """,
        hints=["`totl` raises `NameError`, which `except Exception` turned into a `None` total.",
               "Only the price lookup should be inside the `try`, and only `KeyError` caught. Use `else` for the rest."],
        solution="""
        def enrich(records, prices):
            out = []
            for r in records:
                try:
                    price = prices[r["product"]]
                except KeyError:
                    out.append({**r, "total": None})
                else:
                    out.append({**r, "total": round(price * r["qty"], 2)})
            return out
        """,
        why="""The broad handler turned a `NameError` (a typo, a bug) into the same result as "unknown product" (an expected case), so
        the function ran without complaint and produced only `None`s. With a narrow `try` around just the price lookup and
        `except KeyError`, the expected case is handled and anything else surfaces. Moving the calculation into `else` means a
        missing `qty`, which is a data bug, raises its own `KeyError` from outside the handler, as the second test requires; inside
        the `try`, it would have been mistaken for an unknown product."""),
    write("Parse a score from a model reply", "medium", tag="GenAI",
        prompt="""An LLM judge is asked to reply with a score like `Score: 7/10`. Write `parse_score(reply)` returning the score as
        an `int` from 1 to 10. Accept any case and spacing, and an optional `/10`. If there is no score, or it is out of range,
        raise `ValueError` with a message that includes the first 40 characters of the reply, so the failure can be logged and
        retried.""",
        code="""
        import re

        def parse_score(reply):
            pass
        """,
        tests="""
        assert parse_score("Score: 7/10") == 7
        assert parse_score("The answer is good.\\nscore : 10 / 10") == 10
        assert parse_score("SCORE:3") == 3
        for bad in ["Score: 11/10", "I would rate it highly", "Score: 0"]:
            try:
                parse_score(bad)
                assert False, bad
            except ValueError as e:
                assert bad[:40] in str(e)
        """,
        hints=["`re.search(r\"score\\s*:\\s*(\\d+)\\s*(?:/\\s*10)?\", reply, re.IGNORECASE)` finds the number (5.5).",
               "`raise ValueError(f\"no score in reply: {reply[:40]!r}\")` when there is no match; check the range separately."],
        solution="""
        import re

        SCORE = re.compile(r"score\\s*:\\s*(\\d+)\\s*(?:/\\s*10)?", re.IGNORECASE)

        def parse_score(reply):
            m = SCORE.search(reply)
            if not m:
                raise ValueError(f"no score in reply: {reply[:40]!r}")
            score = int(m.group(1))
            if not 1 <= score <= 10:
                raise ValueError(f"score {score} out of range in reply: {reply[:40]!r}")
            return score
        """,
        why="""Raising instead of returning `None` forces the caller to decide what a bad reply means: retry the judge, skip the sample or
        fail the evaluation; a `None` would flow into an average and break it later, far from the cause. Including part of the reply
        in the message makes the log useful without dumping a huge text, and `!r` shows newlines and spaces. `ValueError` is the
        right type: the input is a string, as expected, but its value is not acceptable. Lesson 7.2 shows how to define a custom
        exception type for this, so callers can catch "bad model output" specifically."""),
    choose("Missing keys: catch KeyError or use get", "medium",
        prompt="Both look up 200,000 keys in a dict where 90% of them are missing, using 0 as the default. Which is faster?",
        setup="""d = {f"k{i}": i for i in range(1000)}
keys = [f"k{i}" if i % 10 == 0 else f"missing{i}" for i in range(200_000)]""",
        options={
            "a": "total = 0\nfor k in keys:\n    try:\n        total += d[k]\n    except KeyError:\n        total += 0",
            "b": "total = 0\nfor k in keys:\n    total += d.get(k, 0)",
        },
        answer="b",
        hints=["What does Python do every time a `KeyError` is raised and caught?"],
        why="""Each miss in version A creates a `KeyError` object with a traceback, unwinds to the handler and clears the exception: far more
        work than the miss itself. `d.get` handles the missing key inside the dict lookup, with no exception at all. When misses are
        rare, the `try` version costs almost nothing, since entering a `try` block is free in Python 3.11+; the cost is in
        **raising**. So use exceptions for cases that are genuinely exceptional, and plain checks or `get` when "missing" is
        normal."""),
    trace("Control flow through finally", "medium",
        prompt="Fill in `log` after each marked line.",
        code="""
        log = []

        def step(x):
            try:
                log.append("try")
                if x < 0:
                    raise ValueError("negative")
                log.append("body")
            except ValueError:
                log.append("except")
            else:
                log.append("else")
            finally:
                log.append("finally")

        step(1)  # row: "x = 1"
        log.clear(); step(-1)  # row: "x = -1"
        log.clear()
        try:
            step("a")
        except TypeError:
            log.append("caller")  # row: "x = 'a'"
        """,
        trace_vars=["log"],
        hints=["`\"a\" < 0` raises `TypeError`, which the `except ValueError` does not match."],
        why="""For 1, the block finishes, so `else` runs and then `finally`. For -1, the `raise` skips the rest of the block, the
        `ValueError` handler runs, `else` is skipped, `finally` runs. For `"a"`, comparing a string with 0 raises `TypeError`,
        which no clause in `step` handles: `finally` still runs on the way out, and then the exception reaches the caller's
        handler. That is the defining property of `finally`: it runs even while an exception is passing through."""),
    fix("An error that disappears in finally", "medium", tag="Data work",
        prompt="""`read_text(path)` should return a file's text and always close the file. When the file does not exist it
        returns `""` instead of raising `FileNotFoundError`. Fix it so the error reaches the caller and the file is still always
        closed.""",
        code="""
        def read_text(path):
            f = None
            try:
                f = open(path, encoding="utf-8")
                return f.read()
            finally:
                if f is not None:
                    f.close()
                return ""
        """,
        tests="""
        import os, tempfile
        p = os.path.join(tempfile.mkdtemp(), "notes.txt")
        with open(p, "w", encoding="utf-8") as out:
            out.write("hello")
        assert read_text(p) == "hello"
        empty = os.path.join(os.path.dirname(p), "empty.txt")
        open(empty, "w").close()
        assert read_text(empty) == ""
        try:
            read_text(p + ".missing")
            assert False, "should raise"
        except FileNotFoundError:
            pass
        """,
        hints=["A `return` inside `finally` replaces the function's result **and** cancels any exception in flight."],
        solution="""
        def read_text(path):
            with open(path, encoding="utf-8") as f:
                return f.read()
        """,
        why="""The `return ""` in `finally` ran in every case: it overrode the successful `return f.read()` (so even existing files gave
        `""`) and discarded the `FileNotFoundError`. Python 3.14 warns about this at compile time with a `SyntaxWarning`, but the
        code still runs. A `finally` block should only clean up. Here the cleanup is exactly what `with open(...)` does (10.2): the
        file is closed when the block ends, whether by `return` or by an exception, and the exception continues to the caller. If
        `open` itself fails, there is nothing to close."""),
    refactor("Duplicate handlers into one", "medium", tag="GenAI",
        prompt="Remove the duplication: same behaviour, one handler. Keep the tests green.",
        code="""
        import json

        def load_reply(raw):
            try:
                data = json.loads(raw)
                return {"label": data["label"], "confidence": float(data["confidence"])}
            except json.JSONDecodeError as e:
                return {"error": f"invalid reply: {type(e).__name__}"}
            except KeyError as e:
                return {"error": f"invalid reply: {type(e).__name__}"}
            except TypeError as e:
                return {"error": f"invalid reply: {type(e).__name__}"}
            except ValueError as e:
                return {"error": f"invalid reply: {type(e).__name__}"}
        """,
        tests="""
        assert load_reply('{"label": "spam", "confidence": "0.9"}') == {"label": "spam", "confidence": 0.9}
        assert load_reply("{bad") == {"error": "invalid reply: JSONDecodeError"}
        assert load_reply('{"label": "spam"}') == {"error": "invalid reply: KeyError"}
        assert load_reply('["spam"]') == {"error": "invalid reply: TypeError"}
        assert load_reply('{"label": "x", "confidence": "high"}') == {"error": "invalid reply: ValueError"}
        """,
        hints=["`JSONDecodeError` is already a `ValueError`, so a tuple of three types covers all four cases."],
        solution="""
        import json

        def load_reply(raw):
            try:
                data = json.loads(raw)
                return {"label": data["label"], "confidence": float(data["confidence"])}
            except (ValueError, KeyError, TypeError) as e:
                return {"error": f"invalid reply: {type(e).__name__}"}
        """,
        why="""A tuple in `except` matches any of its types, and because `JSONDecodeError` is a subclass of `ValueError`, listing
        `ValueError` covers both the invalid JSON and the bad confidence. `type(e).__name__` still reports the exact class, so the
        messages are unchanged. The three types are exactly the ways a reply can be malformed here: not JSON, missing a key,
        or the wrong shape (indexing a list with a string raises `TypeError`). Anything else, like a `NameError`, is still not
        caught. Pydantic (11.4) turns this kind of hand-written validation into a model declaration."""),
    predict("The exception object and its name", "medium",
        code="""
        try:
            {"a": 1}["b"]
        except KeyError as e:
            print(str(e), e.args, repr(e))
            err = e
        print(type(err).__name__, "e" in dir())
        try:
            int("4.2")
        except (TypeError, ValueError) as e:
            print(type(e).__name__, e.args[0])
        try:
            1 / 0
        except ArithmeticError as e:
            print(isinstance(e, ZeroDivisionError), e)
        """,
        hints=["The name bound with `as` is deleted at the end of the `except` block. A `KeyError`'s `str` is the repr of the key."],
        why="""`str(e)` of a `KeyError` shows the missing key with quotes, and `e.args` is the tuple of arguments the exception was
        created with. After the block, `e` no longer exists (Python deletes it to avoid keeping the traceback and all its frames
        alive), but `err` still holds the object. `int("4.2")` raises `ValueError` (the type is right, the value is not an
        integer literal), matched by the tuple. `ZeroDivisionError` is a subclass of `ArithmeticError`, so the general handler
        catches it and `isinstance` confirms the real class."""),
)

section("hard", "Hard",
    write("Retry on chosen exceptions", "hard", tag="GenAI",
        prompt="""Write `call_with_retry(fn, attempts, retry_on)` that calls `fn()` up to `attempts` times. If it raises an exception
        whose type is in the tuple `retry_on`, try again; if it raises anything else, let it propagate immediately. If every attempt
        fails, re-raise the **last** exception. Return `(result, tries)`, where `tries` is the number of calls made.""",
        code="""
        def call_with_retry(fn, attempts, retry_on):
            pass
        """,
        tests="""
        def flaky(results):
            it = iter(results)
            def fn():
                r = next(it)
                if isinstance(r, Exception):
                    raise r
                return r
            return fn

        assert call_with_retry(flaky([TimeoutError("t1"), ConnectionError("c"), "ok"]), 5, (TimeoutError, ConnectionError)) == ("ok", 3)
        assert call_with_retry(flaky(["first"]), 3, (TimeoutError,)) == ("first", 1)
        try:
            call_with_retry(flaky([TimeoutError("a"), TimeoutError("b"), TimeoutError("c")]), 3, (TimeoutError,))
            assert False
        except TimeoutError as e:
            assert str(e) == "c"
        try:
            call_with_retry(flaky([TimeoutError("a"), KeyError("bug"), "never"]), 5, (TimeoutError,))
            assert False
        except KeyError:
            pass
        """,
        hints=["Loop `for attempt in range(1, attempts + 1)`, `return fn(), attempt` inside `try`, and `except retry_on as e:` keeps the last error.",
               "After the loop, `raise last_error`. A tuple of types is valid in `except`."],
        solution="""
        def call_with_retry(fn, attempts, retry_on):
            if attempts < 1:
                raise ValueError("attempts must be at least 1")
            last_error = None
            for attempt in range(1, attempts + 1):
                try:
                    return fn(), attempt
                except retry_on as e:
                    last_error = e
            raise last_error
        """,
        why="""`except retry_on` accepts the tuple directly, so only the listed transient errors (timeouts, dropped connections) are
        retried; a `KeyError` is a bug, and retrying it would just repeat the bug and delay the report, so it propagates at once.
        The handler saves the exception to a second name because the `as` name is deleted when the block ends. Re-raising the last
        error keeps its original traceback, so the logs show where the final attempt failed. Real retry code adds waiting between
        attempts with exponential backoff and jitter, and respects the server's `Retry-After` header; lesson 8.3 turns this into a
        decorator."""),
    fix("Read the code: a config loader that hides everything", "hard", tag="GenAI",
        prompt="""This loads an LLM app's settings from a JSON file over a set of defaults. A missing file should give the
        defaults; invalid JSON should raise `ValueError` naming the file; `max_tokens` must end up as an `int`, and a value that
        cannot be converted should raise `ValueError`. Right now it returns the defaults in every case. Read it, find the bugs and
        fix them.""",
        code="""
        import json


        def load_settings(path, defaults):
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                settings = dict(defaults)
                settings.update(data)
                settings["max_tokens"] = int(settings["max_token"])
                return settings
            except:
                return dict(defaults)
        """,
        tests="""
        import os, tempfile
        d = tempfile.mkdtemp()
        defaults = {"model": "small", "max_tokens": 256}

        def write(name, text):
            p = os.path.join(d, name)
            with open(p, "w", encoding="utf-8") as f:
                f.write(text)
            return p

        assert load_settings(os.path.join(d, "missing.json"), defaults) == defaults
        assert load_settings(write("ok.json", '{"max_tokens": "512"}'), defaults) == {"model": "small", "max_tokens": 512}
        bad = write("bad.json", '{"model": "large",}')
        try:
            load_settings(bad, defaults)
            assert False, "invalid JSON should raise"
        except ValueError as e:
            assert "bad.json" in str(e)
        try:
            load_settings(write("tok.json", '{"max_tokens": "lots"}'), defaults)
            assert False, "bad max_tokens should raise"
        except ValueError as e:
            assert "max_tokens" in str(e)
        """,
        hints=["The bare `except:` catches the `KeyError` from the `max_token` typo (and would catch Ctrl+C too).",
               "Handle `FileNotFoundError` around `open` only, and turn `json.JSONDecodeError` into a `ValueError` that names the path.",
               "Convert `max_tokens` outside those handlers, with its own `try` and a clear message."],
        solution="""
        import json


        def load_settings(path, defaults):
            try:
                with open(path, encoding="utf-8") as f:
                    text = f.read()
            except FileNotFoundError:
                return dict(defaults)
            try:
                data = json.loads(text)
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}: invalid JSON at line {e.lineno}: {e.msg}")
            settings = {**defaults, **data}
            try:
                settings["max_tokens"] = int(settings["max_tokens"])
            except ValueError:
                raise ValueError(f"max_tokens must be an integer, got {settings['max_tokens']!r}")
            return settings
        """,
        why="""The bare `except:` turned every possible problem into "use the defaults": the `max_token` typo (a `KeyError` on every call,
        so the function **never** worked), invalid JSON, a bad value, and even Ctrl+C. A broken config file silently running the app
        with default settings is a classic production incident. The fix handles each case at its own step: only
        `FileNotFoundError` falls back to defaults, which is the one case the spec allows; a `JSONDecodeError` becomes a
        `ValueError` that names the file and the line (`e.lineno` and `e.msg` come from the JSON error), so the person who broke the
        file can find it; and the `int` conversion gets its own message. Raising a new exception inside `except` keeps the original
        attached as context; 7.2 shows how to make that link explicit with `raise ... from e`."""),
    write("The first reply that parses", "hard", tag="GenAI",
        prompt="""When a model's output must follow a format, a common trick is to sample several replies and keep the first one that
        parses. Write `first_valid(replies, parse)` that calls `parse(reply)` on each reply in order and returns `(index,
        parsed)` for the first one that does not raise `ValueError`. If none parses, raise `ValueError` whose message lists every
        failure as `"#i: message"`, one per line. Other exception types must propagate unchanged. Stop at the first success; do
        not parse the rest.""",
        code="""
        def first_valid(replies, parse):
            pass
        """,
        tests="""
        import json
        calls = []
        def parse(r):
            calls.append(r)
            data = json.loads(r)
            if "label" not in data:
                raise ValueError("missing label")
            return data["label"]

        assert first_valid(["not json", '{"x": 1}', '{"label": "spam"}', '{"label": "ham"}'], parse) == (2, "spam")
        assert len(calls) == 3
        try:
            first_valid(["{", '{"x": 1}'], parse)
            assert False
        except ValueError as e:
            lines = str(e).splitlines()
            assert lines[0].startswith("no valid reply") and lines[1].startswith("#0: ") and lines[2] == "#1: missing label"
        try:
            first_valid(["5"], parse)
            assert False
        except TypeError:
            pass
        """,
        hints=["Collect failure messages in a list inside `except ValueError as e:`; `str(e)` is the message.",
               "`json.loads` raises `JSONDecodeError`, a `ValueError`, so it is collected too. In the last test, `\"label\" not in 5` raises `TypeError`, which must not be collected."],
        solution="""
        def first_valid(replies, parse):
            failures = []
            for i, reply in enumerate(replies):
                try:
                    return i, parse(reply)
                except ValueError as e:
                    failures.append(f"#{i}: {e}")
            raise ValueError("no valid reply:\\n" + "\\n".join(failures))
        """,
        why="""The loop returns as soon as one reply parses, so later replies cost nothing, which the `calls` test checks. Only
        `ValueError` (including `JSONDecodeError`) counts as "this reply is malformed"; anything else signals a bug in the parser or
        the data, and must not be hidden behind "try the next sample". In the last test, `json.loads("5")` returns the number 5, and
        `"label" not in 5` raises `TypeError` because an `int` cannot be searched: that is a gap in the parser (it should check that
        the JSON is an object), and it surfaces at once instead of being reported as "no valid reply". Joining the collected messages
        gives one readable error for the log, with the index of each sample. This is the shape of "sample n, take the first valid"
        and of repair loops that feed the error messages back to the model."""),
    predict("Exceptions inside handlers", "hard",
        code="""
        def risky():
            try:
                return {}["key"]
            except KeyError:
                return int("not a number")

        try:
            risky()
        except ValueError as e:
            print(type(e).__name__, "| context:", type(e.__context__).__name__)

        for n in [1, 0, 2]:
            try:
                print("start", n)
                if n == 0:
                    break
            finally:
                print("cleanup", n)
        print("loop over")
        """,
        hints=["An exception raised while handling another keeps the first one in `__context__`.",
               "`break` inside `try` still runs `finally` before leaving the loop."],
        why="""The handler for `KeyError` raised a new `ValueError`. Python attaches the exception that was being handled to the new one
        as `__context__`, which is why tracebacks then say "During handling of the above exception, another exception occurred".
        The caller catches the `ValueError` and can still see the original `KeyError`. In the loop, `break` leaves the loop from
        inside `try`, but `finally` runs first, so "cleanup 0" is printed before the loop ends; 2 is never reached."""),
)

section("interview", "Interview questions",
    explain("What is the difference between `except Exception:` and a bare `except:`, and why does it matter?", "medium", tag="Interview",
        why="""A bare `except:` catches `BaseException`, the root of the hierarchy, so it also catches `KeyboardInterrupt` (Ctrl+C),
        `SystemExit` (`sys.exit()`) and `GeneratorExit`. Code with a bare `except` inside a loop can become impossible to stop with
        Ctrl+C, and it can swallow a deliberate exit. `except Exception:` catches all ordinary errors but lets those control-flow
        exceptions through. Even so, `except Exception` should be rare: it belongs at boundaries (a request handler, a batch loop,
        a worker), always with logging of the full traceback, never as `except Exception: pass`. Everywhere else, catch the
        specific types you can actually handle, so unexpected errors, which are usually bugs, stay visible."""),
    explain("What are `else` and `finally` for in a `try` statement? Give a real use for each.", "medium", tag="Interview",
        why="""`else` runs only if the `try` block raised nothing. Its purpose is to keep the `try` block minimal: put only the risky
        statement in `try`, and the code that depends on its success in `else`, so errors in that follow-up code are not
        accidentally caught by handlers meant for the risky step. Example: `try: f = open(path)`, `except FileNotFoundError:` use
        defaults, `else:` parse the file. `finally` runs no matter what: success, a handled or unhandled exception, or an early
        `return` or `break`. It is for cleanup that must always happen: closing a connection, releasing a lock, removing a
        temporary file, recording a metric of how long a call took. Never `return` from `finally`, since that discards any
        exception in flight; and for resources, a `with` statement usually replaces `try`/`finally`."""),
    explain("You run a batch job over one million records and some records are bad. How do you design the error handling?", "hard", tag="Interview",
        why="""Decide per error type whether it is a **record** problem or a **job** problem. Record problems (a malformed line, a missing
        field, a value out of range) should not stop the job: catch the specific exceptions per record, write the record and the
        error to a dead-letter file or table with enough context to fix it (record id, line number, message), count them, and
        continue. Job problems (the database is down, credentials are wrong, a bug such as a `NameError`) should stop the job fast
        instead of failing a million times; transient ones (timeouts, rate limits) get retries with backoff first. Add an **error
        budget**: if more than, say, 1% of records fail, abort, since that usually means a systematic problem such as a schema
        change. Log a summary at the end (processed, succeeded, failed by error type), make the job resumable with checkpoints, and
        keep writes idempotent so a re-run does not duplicate data. Only the outermost loop uses a broad `except Exception`, and it
        logs the traceback for every record it catches."""),
)

recap(
    "A raised exception stops the current block and unwinds the call stack to the first matching `except`; unhandled, it prints a traceback (read it from the bottom).",
    "`except` clauses are tried top to bottom and match subclasses too: specific types first. The `as` name is deleted after the block.",
    "`else` runs on success (keep `try` small); `finally` always runs, even on `return` or `break`. Never `return` inside `finally`.",
    "Errors live under `Exception`; `KeyboardInterrupt` and `SystemExit` do not. Never write a bare `except:`. `JSONDecodeError` is a `ValueError`.",
    "Catch narrowly: the specific type, the smallest block, only what you can handle. Raising is expensive; use `get` and checks for normal cases.",
)
