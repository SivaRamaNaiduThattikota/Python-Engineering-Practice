from lesson import *
from diagrams import *

lesson(
    id="m7-3", num="7.3", title="Designing error handling",
    intro="The decisions behind good error handling: asking permission or forgiveness, where in a program to handle each "
          "error, why swallowed errors are the worst bugs, logging a traceback once, keeping data consistent when a step "
          "fails halfway, and degrading gracefully with fallbacks and warnings. Applied to agents, batch jobs and LLM features.",
    desc="EAFP vs LBYL, where to handle errors, never swallowing, logging, consistency and fallbacks.",
    keys="eafp lbyl race condition toctou fail fast boundary layer swallow logging exception traceback log once atomic write consistency rollback fallback degrade graceful warnings suppress circuit breaker error budget",
)

term("EAFP", "\"Easier to ask forgiveness than permission\": just try the operation and handle the exception if it fails.")
term("LBYL", "\"Look before you leap\": check the conditions first (`if key in d`, `if os.path.exists(p)`) and only then act.")
term("Race condition", "A bug where the result depends on timing, such as a file deleted between checking that it exists and opening it.")
term("Graceful degradation", "Continuing with reduced service when a part fails, such as using a cached answer when the model is down, and recording that it happened.")

section("eafp", "Asking permission or forgiveness",
    fig(table(["style", "code", "risk"], [
        ["look before you leap", "if key in d: v = d[key]", "the check and the use can disagree (races)"],
        ["ask forgiveness", "try: v = d[key] / except KeyError", "must catch narrowly"],
    ], label="LBYL versus EAFP"),
        "Python usually prefers trying the operation and handling the specific failure, which avoids a gap between checking and acting."),
    p("""There are two styles of dealing with operations that may fail. **LBYL**, "look before you leap", checks every condition
    first: `if key in d: value = d[key]`. **EAFP**, "easier to ask forgiveness than permission", just does it and handles the
    failure: `try: value = d[key]` / `except KeyError: ...`. Python's culture leans towards EAFP, and there are good reasons,
    but neither is always right."""),
    ex("""
    import os, tempfile

    config = {"model": "small"}

    # LBYL: check, then act
    if "temperature" in config:
        t = config["temperature"]
    else:
        t = 0.7

    # EAFP: act, then handle failure
    try:
        t2 = config["temperature"]
    except KeyError:
        t2 = 0.7

    t3 = config.get("temperature", 0.7)      # the best tool when it exists
    print(t, t2, t3)

    path = os.path.join(tempfile.mkdtemp(), "cache.json")
    try:
        with open(path, encoding="utf-8") as f:   # EAFP for files: no gap between check and use
            data = f.read()
    except FileNotFoundError:
        data = "{}"
    print(data)
    """, "eafp_lbyl.py"),
    p("""EAFP wins in three situations. **Races:** with files, network resources and anything shared, the world can change between
    the check and the action. `if os.path.exists(p): open(p)` can still fail if another process deletes the file in between, a
    class of bug called **TOCTOU** ("time of check to time of use"). Only the `try` version is correct. **Duck typing:** instead of
    checking `isinstance(x, list)`, just use `x` the way you need and handle the error, so tuples, generators and custom types
    work too. **Many conditions:** when validity depends on several things (the key exists, the value is a dict, it has the right
    field), one `try` around the access is clearer than a pyramid of `if`s (problem 10)."""),
    p("""LBYL wins in others. When failure is **common**, raising and catching costs far more than a test (7.1). When the failure
    would happen **after side effects**, for example halfway through writing a file or sending a batch, checking first avoids
    leaving things half done. And when the check is a **built-in**, such as `dict.get`, `getattr(obj, name, default)` or
    `str.isdigit`, it is both clear and fast. The best code often uses both: check what can be checked cheaply up front, and
    still handle the failures that only reality can reveal."""),
)

section("where", "Where to handle each error",
    fig(chain(["low-level code|raises specific errors", "middle layers|add context, re-raise", ("the boundary (API, CLI, job)|logs, replies, sets exit code", "accent")]),
        "Errors are raised deep, enriched on the way up, and handled once at the boundary where the program talks to the outside world."),
    p("""Every exception is eventually handled somewhere, even if "somewhere" is the top level, where Python prints a traceback and
    stops. The design question is **which layer** should handle it. The rule of thumb: **handle an error at the lowest level that
    knows what to do about it**, and let it travel up until then. A function that parses a date does not know whether a bad date
    should skip the record, ask the user again or abort the import, so it should raise; the import loop knows, so it handles."""),
    p("""In a typical application the layers look like this. The **lowest layer** (parsing, database or API access) raises specific
    errors and translates library exceptions into the application's own types (7.2). The **middle layer** (business logic) handles
    what it can (retry a transient failure, use a default) and lets the rest pass. The **boundary** (the HTTP handler, the CLI's
    `main`, the loop of a batch job or an agent) catches broadly, logs the traceback, and converts the error into a result for
    the outside world: an HTTP 400 or 500 response, an exit code, a failed-record entry, or an error message for the model."""),
    ex("""
    class NotFoundError(Exception):
        pass

    DB = {"u1": {"name": "Ana", "plan": "pro"}}

    def get_user(user_id):                       # lowest layer: raise specific errors
        try:
            return DB[user_id]
        except KeyError:
            raise NotFoundError(f"no user {user_id!r}") from None

    def plan_limit(user_id):                     # middle layer: logic, no handling it cannot do
        return {"pro": 1000, "free": 50}[get_user(user_id)["plan"]]

    def handle_request(user_id):                 # boundary: turn errors into responses
        try:
            return 200, {"limit": plan_limit(user_id)}
        except NotFoundError as e:
            return 404, {"error": str(e)}
        except Exception as e:
            return 500, {"error": "internal error"}   # and log the traceback (below)

    print(handle_request("u1"), handle_request("u9"))
    """, "layers.py"),
    p("""The middle function contains no `try` at all, and that is correct: it has nothing useful to do with a missing user. A
    common anti-pattern is the opposite, `try`/`except` in every function "to be safe", each one logging, wrapping or returning
    `None`. It makes the code longer, hides the real origin of errors and produces the same failure logged five times. **Fail
    fast** at the bottom, handle **once** at the right level."""),
    callout("sql", "SQL / Power BI", """A stored procedure that hits a constraint violation should not catch it and carry on; it
    raises, the transaction rolls back, and the application that called it decides whether to show "this email already exists".
    The same separation applies in Python: low layers report precisely, the layer that talks to the user decides what it means."""),
)

section("swallow", "Never swallow errors",
    p("""The most damaging error-handling bug is the **swallowed exception**: `except Exception: pass`, or `except: return None`. The
    program keeps running, nothing is logged, and the output is quietly wrong, sometimes for months. A crash is visible and gets
    fixed; a swallowed error produces a dashboard that is 3% too low with no trace of why. If you genuinely want to ignore one
    specific, expected error, make it explicit and narrow, so a reader can see the decision. `contextlib.suppress` exists for
    exactly that (10.3)."""),
    ex("""
    import contextlib, os, tempfile

    path = os.path.join(tempfile.mkdtemp(), "lock.tmp")

    with contextlib.suppress(FileNotFoundError):   # "it is fine if the file is already gone"
        os.remove(path)
    print("cleanup done, nothing to remove")

    def risky_average(values):
        try:
            return sum(values) / len(values)
        except Exception:
            return None                            # swallowed: callers cannot tell why

    print(risky_average([]), risky_average(["3", "4"]), risky_average([3, 4]))
    """, "suppress_vs_swallow.py"),
    p("""`risky_average` returns `None` for an empty list (a normal edge case) and for strings (a bug in the caller) alike, and the
    `None` will cause a `TypeError` somewhere far away. Better: decide what the normal edge case should return, make that explicit
    (`if not values: return 0.0` or raise `ValueError("no values")`), and let the bug crash where it happens (problem 3)."""),
    p("""Returning `None` for failure has one more problem: callers forget to check it. When a function can fail in a way callers must
    handle, raising is usually safer than a special return value. When "no result" is a normal answer, such as a search with no
    match, `None` is fine, but document it, and use a type hint like `str | None` (11.1) so tools remind callers to check."""),
)

section("logging", "Logging an exception, once",
    p("""When you handle an error at a boundary, record it with its **traceback**, not just its message. `str(e)` for a `KeyError` is
    only `'model'`, which tells you nothing about where it happened. The `logging` module (12.3) has `logger.exception(message)`,
    which logs at error level and automatically appends the full traceback of the exception being handled; outside an `except`
    block, pass `exc_info=True` or `exc_info=e`. Use it **once**, at the place that handles the error."""),
    ex("""
    import io, logging

    stream = io.StringIO()
    logger = logging.getLogger("demo")
    logger.addHandler(logging.StreamHandler(stream))
    logger.propagate = False

    def load(cfg):
        return cfg["model"]["name"]

    try:
        load({"model": None})
    except Exception as e:
        logger.error("load failed: %s", e)           # message only
        logger.exception("load failed")               # message and traceback
    lines = stream.getvalue().splitlines()
    print(lines[0])
    print(lines[1], "| has traceback:", any(l.startswith("Traceback") for l in lines[2:]), "| last:", lines[-1])
    """, "log_exception.py"),
    p("""The first line says only that `'NoneType' object is not subscriptable`; the second gives the traceback with the function and
    line. The opposite mistake is logging at **every** level: each function catches, logs and re-raises, so one failure produces
    five log entries with five partial tracebacks, and on-call engineers count five incidents. Either handle an error (and log it
    there) or let it pass untouched (problem 6). Adding context on the way up is better done with `add_note` or a translated
    exception (7.2) than with extra log lines."""),
)

section("consistency", "Leaving data consistent",
    fig(chain(["write to a temporary place", "validate everything", "commit: rename or COMMIT", ("on any error: roll back,|the original is untouched", "good")]),
        "Leaving data consistent: do the risky work on a copy and switch over in one step, so a failure halfway changes nothing."),
    p("""An exception can interrupt a function **halfway through** a change: three of five orders applied, half of a file written,
    the cache updated but not the database. The caller then holds data in a state that no code path was designed for. The defence
    is to make changes **all or nothing**, using one of three patterns:"""),
    p("""- **Validate everything first, then change.** Check every input before the first modification, so the change itself cannot
      fail halfway for a predictable reason (problem 7).
    - **Build new, then swap.** Compute the complete new state in a separate object (a copy, a new list, a temporary file), and only
      when it is complete, replace the old one in a single step. If anything fails, the old state is untouched.
    - **Undo on failure.** If changes must happen in place, record what was done and reverse it in an `except` block, then
      re-raise. Databases do this for you with transactions."""),
    ex("""
    def apply_discounts_in_place(prices, discounts):
        for item, pct in discounts.items():
            prices[item] = round(prices[item] * (1 - pct), 2)    # fails halfway on an unknown item

    def apply_discounts(prices, discounts):
        new = dict(prices)                                    # build new...
        for item, pct in discounts.items():
            if item not in new:
                raise KeyError(f"unknown item {item!r}")
            new[item] = round(new[item] * (1 - pct), 2)
        return new                                            # ...the caller swaps

    prices = {"pen": 2.0, "book": 10.0}
    try:
        apply_discounts_in_place(prices, {"pen": 0.5, "lamp": 0.1})
    except KeyError:
        pass
    print(prices)                                             # half applied

    prices = {"pen": 2.0, "book": 10.0}
    try:
        prices = apply_discounts(prices, {"pen": 0.5, "lamp": 0.1})
    except KeyError as e:
        print("rejected:", e)
    print(prices)                                             # untouched
    """, "all_or_nothing.py"),
    p("""Files follow the same idea: write to a temporary file in the same directory, and when writing has fully succeeded, call
    `os.replace(tmp, final)`, which swaps the file into place in one step on every operating system. A crash during writing leaves
    the old file intact instead of a truncated one (problem 9). Model checkpoints, indexes and caches should always be saved this
    way."""),
)

section("degrade", "Fallbacks, degradation and warnings",
    p("""Sometimes the right response to a failure is to **continue with less**: answer from a cache when the model API is down,
    switch to a smaller model when the large one times out, return keyword search results when the vector store is unreachable.
    This is **graceful degradation**, and it is a deliberate product decision, not a way to hide errors. Two rules keep it honest:
    degrade only on the specific failures you planned for (timeouts, rate limits, connection errors, not every exception), and
    **record** every degradation (a log entry, a metric, a flag in the response), so you know how often users get the reduced
    version (problem 5)."""),
    p("""For problems that are not errors but deserve attention, such as a deprecated option, a suspicious input that was accepted, or
    a fallback that was used, Python has the **`warnings`** module. `warnings.warn(message, category)` emits a warning without
    stopping the program; by default each distinct warning is shown once, and tests or applications can turn warnings into errors
    or collect them. Libraries use `DeprecationWarning` to announce changes before they break anyone."""),
    ex("""
    import warnings

    def build_request(prompt, temperature=None, temp=None):
        if temp is not None:
            warnings.warn("'temp' is deprecated, use 'temperature'", DeprecationWarning, stacklevel=2)
            temperature = temp
        if temperature is not None and temperature > 1.5:
            warnings.warn(f"temperature {temperature} is unusually high", UserWarning, stacklevel=2)
        return {"prompt": prompt, "temperature": temperature}

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        print(build_request("hi", temp=1.8))
    print([(w.category.__name__, str(w.message)) for w in caught])

    with warnings.catch_warnings():
        warnings.simplefilter("error")             # strict mode, as in tests
        try:
            build_request("hi", temp=0.2)
        except DeprecationWarning as e:
            print("raised:", e)
    """, "warnings_demo.py"),
    p("""`stacklevel=2` makes the warning point at the **caller's** line instead of the line inside the library, which is where the
    fix belongs. Turning warnings into errors in a test suite (pytest's `-W error`, 13.1) catches deprecated usage before an
    upgrade removes it."""),
)

section("warmup", "Warm-up",
    predict("Permission and forgiveness", "easy",
        code="""
        cfg = {"model": "small", "limits": {"rpm": 60}}
        print(cfg.get("temperature", 0.7), getattr(cfg, "keys") is not None, hasattr(cfg, "model"))
        try:
            rpm = cfg["limits"]["rpm"]
            tpm = cfg["limits"]["tpm"]
        except KeyError as e:
            print("missing", e)
        print("rpm" in cfg, "rpm" in cfg["limits"])
        try:
            cfg["model"]["name"]
        except TypeError as e:
            print(type(e).__name__)
        """,
        hints=["`hasattr` looks for attributes, not dict keys. Indexing a string with a string raises `TypeError`."],
        why="""`get` returns the default for a missing key. `hasattr(cfg, "model")` is `False`: dict keys are not attributes, while `keys`
        is a method, so `getattr` finds it. Inside the `try`, `rpm` is read and the missing `tpm` raises `KeyError`, whose `str` is
        the quoted key. `in` checks only the top level of a dict. `cfg["model"]` is the string `"small"`, and indexing a string with
        a string is a `TypeError`, not a `KeyError`, which is why code that walks nested data must handle both."""),
    write("Get a nested value safely", "easy", tag="Data work",
        prompt="""API responses are deeply nested. Write `dig(data, path, default=None)` where `path` is a dotted string such as
        `"choices.0.message.content"`: each part is a dict key, or a list index when the current value is a list. Return `default`
        if any step is missing or the structure does not fit. Use EAFP.""",
        code="""
        def dig(data, path, default=None):
            pass
        """,
        tests="""
        resp = {"choices": [{"message": {"content": "Hi", "role": "assistant"}}], "usage": {"total_tokens": 12}}
        assert dig(resp, "choices.0.message.content") == "Hi"
        assert dig(resp, "usage.total_tokens") == 12
        assert dig(resp, "choices.1.message", "none") == "none"
        assert dig(resp, "choices.x.message") is None
        assert dig(resp, "usage.total_tokens.value", 0) == 0
        assert dig(resp, "missing.deep.key", "d") == "d"
        """,
        hints=["For each part: if the current value is a list, index it with `int(part)`; otherwise use `current[part]`.",
               "Catch `KeyError`, `IndexError`, `ValueError` (from `int`) and `TypeError` (indexing something that is not a container)."],
        solution="""
        def dig(data, path, default=None):
            current = data
            try:
                for part in path.split("."):
                    current = current[int(part)] if isinstance(current, list) else current[part]
            except (KeyError, IndexError, ValueError, TypeError):
                return default
            return current
        """,
        why="""One `try` around the whole walk replaces a check at every level for "is it a dict, does it have the key, is it a list, is
        the index in range". The four exception types are exactly the ways a path can fail to fit: missing key, index out of range,
        a non-numeric index for a list, and indexing something that is not a container (an `int` here). Anything else, such as a
        `NameError`, would still surface. This is how helpers like `jmespath` or `glom` behave, and it is convenient for optional
        fields; for fields that **must** exist, validate the response with a schema instead (11.4), so a missing field is an error,
        not a silent default."""),
    fix("A function that hides the edge case and the bug", "easy", tag="ML",
        prompt="""`mean_score(scores)` returns `None` for an empty list and for invalid input alike, and the `None` breaks reports
        later. Make an empty list return `0.0` (a decision of this team), and let invalid input raise where it happens.""",
        code="""
        def mean_score(scores):
            try:
                return sum(scores) / len(scores)
            except Exception:
                return None
        """,
        tests="""
        assert mean_score([0.5, 1.0]) == 0.75
        assert mean_score([]) == 0.0
        try:
            mean_score(["0.5", "1.0"])
            assert False, "strings should raise"
        except TypeError:
            pass
        """,
        hints=["Handle the empty list explicitly with an `if`, and remove the `try` entirely."],
        solution="""
        def mean_score(scores):
            if not scores:
                return 0.0
            return sum(scores) / len(scores)
        """,
        why="""The broad handler merged two different situations: an empty list, a normal edge case that deserves a defined answer, and a
        list of strings, a bug in the caller that deserves a crash at its source. Handling the edge case with an explicit `if` makes
        the decision visible in the code, and removing the `try` lets `sum` raise `TypeError` right where the bad data arrives. Note
        that `0.0` for "no scores" is a choice; for some reports `None` (with a type hint saying so) or an exception would be the
        right one, but it must be one decision, made on purpose."""),
    predict("Message versus traceback in logs", "easy",
        code="""
        import io, logging

        stream = io.StringIO()
        log = logging.getLogger("predict")
        log.addHandler(logging.StreamHandler(stream))
        log.propagate = False

        try:
            {"a": 1}["b"]
        except KeyError as e:
            log.error("lookup failed: %s", e)
            log.exception("lookup failed")
            log.error("with exc_info", exc_info=True)

        text = stream.getvalue()
        print(text.splitlines()[0])
        print(text.count("Traceback"), text.count("KeyError: 'b'"))
        """,
        hints=["`logger.exception` and `exc_info=True` add the traceback; a plain `error` with the message does not."],
        why="""The first entry is just the message, with the quoted key from `str(e)`. `log.exception(...)` and `log.error(...,
        exc_info=True)` both append the full traceback, which ends with the line `KeyError: 'b'`. So the text contains two
        tracebacks, and that line appears twice. In real logs the traceback is what tells you which function and line failed."""),
)

section("medium", "Medium",
    write("Fall back, and say so", "medium", tag="GenAI",
        prompt="""Write `answer(question, primary, fallback, events)` that calls `primary(question)`. If it raises
        `TimeoutError` or `ConnectionError`, call `fallback(question)` instead and append `("fallback", type name, question)` to the
        `events` list. Return `(text, source)` with source `"primary"` or `"fallback"`. Any other exception from `primary`, and any
        exception from `fallback`, must propagate.""",
        code="""
        def answer(question, primary, fallback, events):
            pass
        """,
        tests="""
        def ok(q): return f"big model: {q}"
        def small(q): return f"small model: {q}"
        def slow(q): raise TimeoutError("30s")
        def buggy(q): raise KeyError("prompt")
        events = []
        assert answer("refund?", ok, small, events) == ("big model: refund?", "primary") and events == []
        assert answer("refund?", slow, small, events) == ("small model: refund?", "fallback")
        assert events == [("fallback", "TimeoutError", "refund?")]
        try:
            answer("x", buggy, small, events)
            assert False
        except KeyError:
            pass
        try:
            answer("x", slow, slow, [])
            assert False
        except TimeoutError:
            pass
        """,
        hints=["Use `try` / `except (TimeoutError, ConnectionError) as e:` around the primary call only, and `else` for the primary result."],
        solution="""
        def answer(question, primary, fallback, events):
            try:
                text = primary(question)
            except (TimeoutError, ConnectionError) as e:
                events.append(("fallback", type(e).__name__, question))
                return fallback(question), "fallback"
            else:
                return text, "primary"
        """,
        why="""Only the failures you planned for, slow or unreachable service, trigger the fallback; a `KeyError` is a bug, and answering
        with the small model would hide it. The fallback call sits inside the `except` block but is not itself protected, so if the
        fallback also fails, the caller sees that error (with the primary's error attached as context). The event record is what
        makes degradation measurable: a dashboard of fallback rate tells you when the "temporary" fallback has become the normal path.
        Returning the source lets the UI or the logs mark degraded answers."""),
    fix("One failure, logged three times", "medium", tag="Data work",
        prompt="""Each layer of this request path catches, logs and re-raises, so every failure appears three times in the log.
        Change it so the failure is logged **once**, by `handle`, with the traceback marker, and `handle` still returns `(500,
        "internal error")`. The successful path must not log anything.""",
        code="""
        log = []

        def fetch(doc_id):
            try:
                return {"d1": "Refunds take 5 days."}[doc_id]
            except Exception as e:
                log.append(f"fetch failed: {e}")
                raise

        def summarise(doc_id):
            try:
                return fetch(doc_id)[:12]
            except Exception as e:
                log.append(f"summarise failed: {e}")
                raise

        def handle(doc_id):
            try:
                return 200, summarise(doc_id)
            except Exception as e:
                log.append(f"handle failed: {e}")
                return 500, "internal error"
        """,
        tests="""
        import traceback
        assert handle("d1") == (200, "Refunds take") and log == []
        assert handle("d9") == (500, "internal error")
        assert len(log) == 1 and log[0].startswith("request failed") and "Traceback" in log[0] and "fetch" in log[0]
        """,
        hints=["Remove the handlers from `fetch` and `summarise`. In `handle`, log `traceback.format_exc()` together with a message."],
        solution="""
        import traceback

        log = []

        def fetch(doc_id):
            return {"d1": "Refunds take 5 days."}[doc_id]

        def summarise(doc_id):
            return fetch(doc_id)[:12]

        def handle(doc_id):
            try:
                return 200, summarise(doc_id)
            except Exception:
                log.append("request failed\\n" + traceback.format_exc())
                return 500, "internal error"
        """,
        why="""The lower functions had nothing to do with the error except log it, and each log line contained only `str(e)`, which for a
        `KeyError` is just `'d9'`. Removing those handlers lets the exception travel to the boundary untouched, where one entry with
        the full traceback shows the complete path (`handle`, `summarise`, `fetch`) and the exact line. In real code this is
        `logger.exception("request failed")`. One failure, one log entry, one alert."""),
    write("All orders or none", "medium", tag="Data work",
        prompt="""Write `apply_orders(stock, orders)` where `stock` maps item to quantity and `orders` is a list of `(item, qty)`.
        Return a **new** stock dict with all orders applied. If any order is for an unknown item, has a non-positive quantity, or
        would take an item's stock below zero (counting earlier orders in the same batch), raise `ValueError` describing the first
        problem, and leave `stock` unchanged.""",
        code="""
        def apply_orders(stock, orders):
            pass
        """,
        tests="""
        stock = {"pen": 5, "book": 2}
        assert apply_orders(stock, [("pen", 2), ("book", 1), ("pen", 3)]) == {"pen": 0, "book": 1}
        assert stock == {"pen": 5, "book": 2}
        for orders, word in [([("pen", 1), ("lamp", 1)], "lamp"), ([("pen", 0)], "quantity"), ([("book", 2), ("book", 1)], "book")]:
            try:
                apply_orders(stock, orders)
                assert False, orders
            except ValueError as e:
                assert word in str(e)
            assert stock == {"pen": 5, "book": 2}
        """,
        hints=["Work on `new = dict(stock)` and only return it at the end; the original is never touched.",
               "Check each order before applying it to `new`."],
        solution="""
        def apply_orders(stock, orders):
            new = dict(stock)
            for item, qty in orders:
                if item not in new:
                    raise ValueError(f"unknown item {item!r}")
                if qty <= 0:
                    raise ValueError(f"quantity must be positive, got {qty} for {item!r}")
                if new[item] < qty:
                    raise ValueError(f"not enough {item!r}: {new[item]} left, {qty} ordered")
                new[item] -= qty
            return new
        """,
        why="""Building a new dict means an exception at any order simply abandons the copy: the caller's `stock` was never modified, so
        there is nothing to undo. Checking against `new` rather than `stock` accounts for earlier orders in the same batch, which is
        why two book orders of 2 and 1 fail when only 2 books exist. The caller completes the change with `stock = apply_orders(stock,
        orders)`, a single step. This is the "build new, then swap" pattern; a database gives the same guarantee with a
        transaction."""),
    trace("A change interrupted halfway", "medium",
        prompt="Fill in `state` after each marked line.",
        code="""
        state = {"a": 1, "b": 2}

        def bump_in_place(d, keys):
            for k in keys:
                d[k] += 10

        def bump_new(d, keys):
            new = dict(d)
            for k in keys:
                new[k] += 10
            return new

        try:
            bump_in_place(state, ["a", "x", "b"])
        except KeyError:
            pass  # row: "in place, failed on x"
        try:
            state = bump_new(state, ["b", "x"])
        except KeyError:
            pass  # row: "new copy, failed on x"
        state = bump_new(state, ["b"])  # row: "new copy, success"
        """,
        trace_vars=["state"],
        hints=["The in-place version has already changed `a` when it reaches `x`. The copy version fails before `state` is reassigned."],
        why="""The in-place update changed `a` and then failed on `x`, so `b` was never updated: a half-applied change. The copying version
        also failed on `x`, but the exception happened before the assignment `state = ...` ran, so `state` still refers to the
        unchanged dict. The successful call swaps in the new dict in one assignment."""),
    fix("A crash that leaves half a file", "medium", tag="ML",
        prompt="""`save_labels(path, labels)` writes one label per line. If a label is not a string, it crashes halfway and the
        existing file is left truncated. Make the write atomic: on failure the old file must be untouched and no temporary file left
        behind; on success the new content replaces it.""",
        code="""
        def save_labels(path, labels):
            with open(path, "w", encoding="utf-8") as f:
                for label in labels:
                    f.write(label + "\\n")
        """,
        tests="""
        import os, tempfile
        d = tempfile.mkdtemp()
        p = os.path.join(d, "labels.txt")
        def read(path):
            with open(path, encoding="utf-8") as f:
                return f.read()
        save_labels(p, ["spam", "ham"])
        assert read(p) == "spam\\nham\\n"
        try:
            save_labels(p, ["phish", 42, "x"])
            assert False
        except TypeError:
            pass
        assert read(p) == "spam\\nham\\n"
        assert os.listdir(d) == ["labels.txt"]
        """,
        hints=["Write to `path + \".tmp\"`, then `os.replace(tmp, path)` after the `with` block closes it.",
               "On any exception, remove the temporary file and re-raise."],
        solution="""
        import os

        def save_labels(path, labels):
            tmp = path + ".tmp"
            try:
                with open(tmp, "w", encoding="utf-8") as f:
                    for label in labels:
                        f.write(label + "\\n")
                os.replace(tmp, path)
            except BaseException:
                if os.path.exists(tmp):
                    os.remove(tmp)
                raise
        """,
        why="""Opening the real file with `"w"` truncates it immediately, so any crash afterwards loses the old content. Writing to a
        temporary file in the same directory and swapping it in with `os.replace` means the real file is only ever the complete old
        version or the complete new one; `os.replace` overwrites the target in one step on every platform. The cleanup handler catches
        `BaseException` deliberately, so even Ctrl+C removes the temporary file, and it always re-raises, so nothing is swallowed. The
        temporary file must be on the same file system as the target for the swap to be atomic, which is why it sits next to it."""),
    refactor("A pyramid of checks", "medium", tag="GenAI",
        prompt="Rewrite with EAFP: one `try` and specific exceptions, same results. Keep the tests green.",
        code="""
        def tool_name(response):
            if isinstance(response, dict):
                if "choices" in response:
                    choices = response["choices"]
                    if isinstance(choices, list) and len(choices) > 0:
                        message = choices[0].get("message") if isinstance(choices[0], dict) else None
                        if isinstance(message, dict) and "tool_calls" in message:
                            calls = message["tool_calls"]
                            if isinstance(calls, list) and calls and isinstance(calls[0], dict):
                                fn = calls[0].get("function")
                                if isinstance(fn, dict) and "name" in fn:
                                    return fn["name"]
            return None
        """,
        tests="""
        ok = {"choices": [{"message": {"tool_calls": [{"function": {"name": "search"}}]}}]}
        assert tool_name(ok) == "search"
        assert tool_name({"choices": [{"message": {"content": "hi"}}]}) is None
        assert tool_name({"choices": []}) is None and tool_name("oops") is None and tool_name(None) is None
        assert tool_name({"choices": [{"message": {"tool_calls": []}}]}) is None
        assert tool_name({"choices": [{"message": {"tool_calls": [{"function": None}]}}]}) is None
        """,
        hints=["`return response[\"choices\"][0][\"message\"][\"tool_calls\"][0][\"function\"][\"name\"]` inside `try`.",
               "Missing keys raise `KeyError`, empty lists `IndexError`, and `None` or strings in the way `TypeError`."],
        solution="""
        def tool_name(response):
            try:
                return response["choices"][0]["message"]["tool_calls"][0]["function"]["name"]
            except (KeyError, IndexError, TypeError):
                return None
        """,
        why="""Every `isinstance`, `in` and `len` check in the pyramid guards against one of three failures, which Python reports anyway:
        a missing key (`KeyError`), an empty list (`IndexError`), or something in the path that is not a container, such as `None` or a
        string (`TypeError`). The EAFP version states the intent, "the name of the first tool call", in one line, and the handler
        lists the ways it can be absent. As with `dig`, this suits optional data; if a tool call is required, parse the response
        into a validated model instead (11.4)."""),
    write("Run a tool and report errors to the model", "medium", tag="GenAI",
        prompt="""An agent loop calls tools that the model chose. Write `run_tool(tools, name, args)` returning `{"result": ...}` on
        success. Errors the model can fix are returned, not raised: unknown tool `{"error": "unknown tool 'x'"}`; wrong arguments
        (a `TypeError` raised **by the call itself**) `{"error": "bad arguments for 'x': <message>"}`; a `ToolError` raised by the
        tool `{"error": "<message>"}`. Any other exception is a bug in the tool and must propagate. Define `ToolError`.""",
        code="""
        def run_tool(tools, name, args):
            pass
        """,
        tests="""
        def search(query, k=3):
            if not query.strip():
                raise ToolError("query must not be empty")
            return [f"doc{i}" for i in range(k)]

        def broken(x):
            return x["field"]          # a bug when x is a string

        tools = {"search": search, "broken": broken}
        assert run_tool(tools, "search", {"query": "refund", "k": 2}) == {"result": ["doc0", "doc1"]}
        assert run_tool(tools, "fetch", {}) == {"error": "unknown tool 'fetch'"}
        assert run_tool(tools, "search", {"q": "x"})["error"].startswith("bad arguments for 'search':")
        assert run_tool(tools, "search", {"query": "  "}) == {"error": "query must not be empty"}
        try:
            run_tool(tools, "broken", {"x": "text"})
            assert False, "a bug inside a tool must propagate"
        except TypeError:
            pass
        """,
        hints=["`inspect.signature(fn).bind(**args)` raises `TypeError` for wrong arguments **without** calling the function, which separates argument errors from `TypeError`s inside the tool.",
               "Look up the tool with `tools.get(name)`."],
        solution="""
        import inspect


        class ToolError(Exception):
            pass


        def run_tool(tools, name, args):
            fn = tools.get(name)
            if fn is None:
                return {"error": f"unknown tool {name!r}"}
            try:
                inspect.signature(fn).bind(**args)
            except TypeError as e:
                return {"error": f"bad arguments for {name!r}: {e}"}
            try:
                return {"result": fn(**args)}
            except ToolError as e:
                return {"error": str(e)}
        """,
        why="""The hard part is telling two `TypeError`s apart: "the model passed `q` instead of `query`" (fixable by the model) and "the
        tool's own code indexed a string" (a bug). Catching `TypeError` around `fn(**args)` would treat both the same. Binding the
        arguments to the function's signature first, without calling it, raises `TypeError` only for argument problems; after that,
        the real call runs outside that handler. Errors the model can act on are returned as data, so the agent can show them to the
        model and let it try again; bugs propagate so they get fixed rather than "explained" to the model. Lesson 8.4 uses
        `inspect.signature` to build tool schemas from functions."""),
    predict("suppress and warnings", "medium",
        code="""
        import contextlib, warnings

        with contextlib.suppress(KeyError):
            print("before")
            {}["x"]
            print("after")
        print("continued")

        with contextlib.suppress(KeyError):
            try:
                int("x")
            except ValueError:
                print("ValueError handled inside")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            warnings.warn("old option", DeprecationWarning)
            warnings.warn("odd input")
        print([(x.category.__name__, str(x.message)) for x in w])
        """,
        hints=["`suppress` ends its whole block at the first suppressed exception. A warning's default category is `UserWarning`."],
        why="""`suppress(KeyError)` works like `try: ... except KeyError: pass` around the block: the `KeyError` ends the block, so
        "after" never prints, and execution continues after the `with`. The second block has its own handler for the `ValueError`,
        so `suppress` has nothing to do. `warnings.warn` without a category uses `UserWarning`; with `record=True` warnings are
        collected instead of printed, which is how tests check them."""),
)

section("hard", "Hard",
    write("A circuit breaker", "hard", tag="GenAI",
        prompt="""When a provider is down, calling it again and again wastes time and quota. Write `make_breaker(fn,
        max_failures, reset_after, clock)` returning a function `call(*args)`. It calls `fn(*args)` normally. After `max_failures`
        **consecutive** exceptions it opens: further calls raise `CircuitOpenError` immediately, without calling `fn`, until
        `reset_after` seconds have passed (measured with `clock()`). Then the next call is a trial: success closes the breaker and
        resets the count; failure opens it again for another `reset_after`. Exceptions from `fn` propagate unchanged. Define
        `CircuitOpenError`.""",
        code="""
        def make_breaker(fn, max_failures, reset_after, clock):
            pass
        """,
        tests="""
        now = [0.0]
        clock = lambda: now[0]
        calls = []
        outcomes = []
        def provider(x):
            calls.append(x)
            if outcomes.pop(0):
                return f"ok {x}"
            raise ConnectionError("down")

        call = make_breaker(provider, max_failures=2, reset_after=10, clock=clock)
        outcomes[:] = [True, False, False]
        assert call(1) == "ok 1"
        for x in (2, 3):
            try:
                call(x)
                assert False
            except ConnectionError:
                pass
        try:
            call(4)
            assert False
        except CircuitOpenError:
            pass
        assert calls == [1, 2, 3]
        now[0] = 10.5
        outcomes[:] = [False]
        try:
            call(5)
        except ConnectionError:
            pass
        try:
            call(6)
            assert False
        except CircuitOpenError:
            pass
        now[0] = 21.0
        outcomes[:] = [True, False, True]
        assert call(7) == "ok 7"
        try:
            call(8)
        except ConnectionError:
            pass
        assert call(9) == "ok 9" and calls == [1, 2, 3, 5, 7, 8, 9]
        """,
        hints=["Keep `failures` and `opened_at` in the enclosing function and update them with `nonlocal` (3.4).",
               "Open means `opened_at is not None and clock() - opened_at < reset_after`. After a trial failure, set `opened_at = clock()` again."],
        solution="""
        class CircuitOpenError(Exception):
            pass


        def make_breaker(fn, max_failures, reset_after, clock):
            failures = 0
            opened_at = None

            def call(*args):
                nonlocal failures, opened_at
                if opened_at is not None:
                    if clock() - opened_at < reset_after:
                        raise CircuitOpenError(f"circuit open for {reset_after - (clock() - opened_at):.1f}s more")
                    trial = True
                else:
                    trial = False
                try:
                    result = fn(*args)
                except Exception:
                    failures += 1
                    if trial or failures >= max_failures:
                        opened_at = clock()
                    raise
                failures = 0
                opened_at = None
                return result

            return call
        """,
        why="""The breaker has three states. **Closed**: calls go through and failures are counted. **Open**: calls fail immediately with
        `CircuitOpenError`, protecting both your users (no waiting for a timeout) and the struggling provider (no extra load).
        **Half-open**: once the cool-down has passed, one trial call decides whether to close again or reopen. The state lives in the
        closure (3.4), updated with `nonlocal`; Module 9 would make it a class. Injecting `clock` instead of calling `time.time()`
        makes the behaviour testable without sleeping, a pattern you will use again in 13.2. The bare `raise` keeps `fn`'s exception
        unchanged, and a success at any time resets the consecutive count. Libraries such as `pybreaker` implement the same states, and
        LLM gateways use breakers per provider so traffic can fail over to another one."""),
    fix("Read the code: a batch job that hides fatal errors", "hard", tag="Data work",
        prompt="""This imports records: `transform` raises `ValueError` for bad records, and `save` writes a row (it may raise
        `PermissionError` if the store is read-only). Bad records should be skipped and their ids returned in `failed`; a
        `PermissionError` is fatal and must stop the job immediately, re-raised unchanged; any other exception is a bug and must
        propagate too. The current code keeps going after everything. Read it, find the bugs and fix them.""",
        code="""
        def transform(record):
            if not record.get("email") or "@" not in record["email"]:
                raise ValueError(f"bad email in record {record.get('id')}")
            return {"id": record["id"], "email": record["email"].lower()}


        def run(records, save):
            done = 0
            failed = []
            for record in records:
                try:
                    row = transform(record)
                    save(row)
                    done += 1
                except Exception as e:
                    failed.append(record.get("id"))
            return done, failed
        """,
        tests="""
        saved = []
        records = [{"id": 1, "email": "A@x.io"}, {"id": 2, "email": "nope"}, {"id": 3, "email": "c@x.io"}]
        assert run(records, saved.append) == (2, [2]) and saved == [{"id": 1, "email": "a@x.io"}, {"id": 3, "email": "c@x.io"}]
        assert run([], saved.append) == (0, [])

        attempts = []
        def read_only(row):
            attempts.append(row["id"])
            raise PermissionError("store is read-only")
        try:
            run(records, read_only)
            assert False, "PermissionError must stop the job"
        except PermissionError:
            assert attempts == [1]

        try:
            run([{"id": 9, "email": "z@x.io", "extra": 1}, {"email": "q@x.io"}], saved.append)
            assert False, "a record without id is a bug here"
        except KeyError:
            pass
        """,
        hints=["Only `transform`'s `ValueError` means \"bad record\". Put just that call in the `try`, and catch only `ValueError`.",
               "`save` goes after the handler (in `else`), so its errors, fatal or not, propagate."],
        solution="""
        def transform(record):
            if not record.get("email") or "@" not in record["email"]:
                raise ValueError(f"bad email in record {record.get('id')}")
            return {"id": record["id"], "email": record["email"].lower()}


        def run(records, save):
            done = 0
            failed = []
            for record in records:
                try:
                    row = transform(record)
                except ValueError:
                    failed.append(record.get("id"))
                else:
                    save(row)
                    done += 1
            return done, failed
        """,
        why="""The single `except Exception` mixed three categories of failure. A **bad record** (`ValueError` from `transform`) is expected
        and should be recorded and skipped. A **fatal environment problem** (`PermissionError` from `save`) will happen for every
        remaining record, so continuing means a million identical failures, a run reported as "finished with 100% failed records" and
        possibly hours wasted; it must stop at the first occurrence. A **bug** (`KeyError` for a record without `id`, because
        `transform` assumes one) must surface. Narrowing the `try` to `transform` and the handler to `ValueError`, and moving `save`
        to `else`, gives each category the right behaviour without any extra code. In production, the fatal case would also be logged
        at the job's top level, and a large share of `ValueError`s would trigger an error-budget abort (next problem)."""),
    write("Stop when too many items fail", "hard", tag="ML",
        prompt="""Write `process(items, fn, max_error_rate, min_items)` that applies `fn` to each item, collecting results and
        skipping items for which `fn` raises `ValueError`. After each item, once at least `min_items` items have been processed, if
        the share of failures so far is **greater than** `max_error_rate`, stop and raise `RuntimeError` with a message giving the
        failure count and the number processed, chained from the last `ValueError`. Return `(results, failures)` where failures is
        a list of `(index, message)`.""",
        code="""
        def process(items, fn, max_error_rate, min_items):
            pass
        """,
        tests="""
        def parse(x):
            return float(x)
        results, failures = process(["1", "2", "x", "4", "5", "6"], parse, 0.2, 5)
        assert results == [1.0, 2.0, 4.0, 5.0, 6.0] and failures == [(2, "could not convert string to float: 'x'")]

        seen = []
        def tracked(x):
            seen.append(x)
            return parse(x)
        try:
            process(["1", "a", "b", "4", "c", "6", "7", "8"], tracked, 0.25, 4)
            assert False
        except RuntimeError as e:
            assert "2 of 4" in str(e) and isinstance(e.__cause__, ValueError) and seen == ["1", "a", "b", "4"]
        assert process([], parse, 0.1, 3) == ([], [])
        try:
            process(["1", None], parse, 0.9, 1)
            assert False
        except TypeError:
            pass
        """,
        hints=["Keep the last `ValueError` in a variable; the `as` name is deleted after the block.",
               "Check the rate after every item: `processed >= min_items and len(failures) / processed > max_error_rate`."],
        solution="""
        def process(items, fn, max_error_rate, min_items):
            results, failures = [], []
            last_error = None
            for i, item in enumerate(items):
                try:
                    results.append(fn(item))
                except ValueError as e:
                    failures.append((i, str(e)))
                    last_error = e
                processed = i + 1
                if processed >= min_items and len(failures) / processed > max_error_rate:
                    raise RuntimeError(
                        f"error budget exceeded: {len(failures)} of {processed} items failed"
                    ) from last_error
            return results, failures
        """,
        why="""Skipping bad items is right when they are rare; when they are common, something systematic has gone wrong (a schema change,
        a broken upstream export, a model that stopped following the format), and processing the rest only wastes time and produces
        a misleading result. An **error budget** distinguishes the two automatically. `min_items` avoids aborting on one bad item at
        the very start, when the rate is meaningless. The `RuntimeError` is chained from the last `ValueError`, so the traceback shows
        a concrete example of the failure. Only `ValueError` counts as a bad item; the `TypeError` from `None` is a bug and propagates
        immediately. Evaluation harnesses and labelling pipelines use exactly this rule."""),
    predict("Which exception wins", "hard",
        code="""
        def a():
            try:
                x = 1
            except ValueError:
                return "except"
            else:
                raise ValueError("raised in else")

        try:
            a()
        except ValueError as e:
            print("caller:", e)

        def b():
            try:
                raise KeyError("first")
            finally:
                raise RuntimeError("from finally")

        try:
            b()
        except Exception as e:
            print(type(e).__name__, "| context:", repr(e.__context__))

        def c():
            try:
                raise ValueError("original")
            except ValueError:
                raise TypeError("in handler")
            finally:
                print("finally runs")

        try:
            c()
        except Exception as e:
            print(type(e).__name__, "<-", type(e.__context__).__name__)
        """,
        hints=["An exception raised in `else` is not handled by the same statement's `except` clauses.",
               "An exception raised in `finally` replaces the one in flight, which becomes its context."],
        why="""In `a`, the `ValueError` comes from `else`, which the `except ValueError` of the same `try` does not cover (that is the
        point of `else`), so it reaches the caller. In `b`, the `KeyError` was on its way out when `finally` raised a `RuntimeError`,
        which **replaces** it; the original survives only as `__context__`. That is why cleanup code in `finally` must not raise:
        it hides the real error. In `c`, the handler raises a new `TypeError`; `finally` still runs, then the `TypeError` propagates
        with the `ValueError` as its context."""),
)

section("interview", "Interview questions",
    explain("Explain EAFP and LBYL. When would you choose each, and what is a TOCTOU bug?", "medium", tag="Interview",
        why="""LBYL ("look before you leap") checks preconditions before acting: `if key in d`, `if os.path.exists(path)`. EAFP ("easier
        to ask forgiveness than permission") performs the operation and handles the exception if it fails. EAFP is idiomatic Python
        and is the only correct option when the condition can change between the check and the use: a file can be deleted after
        `exists()` returns `True`, which is a time-of-check-to-time-of-use (TOCTOU) race; it also supports duck typing and replaces
        deep nests of checks with one `try`. LBYL is better when failure is frequent (exceptions are expensive to raise), when a
        failure would leave partial side effects, and when a cheap built-in check exists (`dict.get`, `getattr` with a default).
        In practice, validate the inputs you can check up front and still handle the failures only reality can reveal."""),
    explain("In a layered application (data access, business logic, API), where should exceptions be caught?", "medium", tag="Interview",
        why="""Catch an exception at the lowest layer that can do something meaningful with it, and nowhere else. The data-access layer
        translates library errors (driver, HTTP client) into the application's own exception types with `raise ... from`, and handles
        only what it truly can, such as retrying a dropped connection. The business layer applies decisions (a default, a fallback, a
        retry policy) and otherwise lets errors propagate; most of its functions need no `try` at all. The API or CLI boundary catches
        everything left, maps known error types to responses (404 for not found, 400 for validation, 429 for rate limits), logs
        unexpected ones once with their traceback and returns a generic 500 without leaking internals. Anti-patterns are catching in
        every layer, logging at every level, and converting exceptions to `None` return values that callers forget to check."""),
    explain("How would you design graceful degradation for an LLM-powered feature?", "hard", tag="Interview",
        why="""Start from what the user should get when each dependency fails. Put strict timeouts on model calls, retry transient errors
        a limited number of times with backoff, and use a circuit breaker per provider so an outage fails fast instead of making every
        request wait. Define fallbacks in order of quality: another provider or a smaller model, a cached answer for repeated questions,
        a non-LLM result (keyword search results instead of a generated answer), and finally a clear message ("the assistant is
        unavailable, here are relevant articles"). Trigger fallbacks only on specific failures, never on bugs or validation errors,
        and record every degradation in logs and metrics with the reason, so fallback rate and latency are monitored and alerting fires
        when degraded mode becomes common. Mark degraded responses so the UI can show it and evaluations can exclude them. Test the
        failure paths deliberately, with fake clients that time out or return errors, because fallbacks that are never exercised tend
        to be broken when they are finally needed."""),
)

recap(
    "EAFP (try, then handle) avoids races and pyramids of checks; LBYL (check first) suits common failures, side effects and cheap built-in checks like `get`.",
    "Handle each error at the lowest layer that can act on it; translate at the bottom, decide in the middle, convert to responses at the boundary.",
    "Never swallow: no `except: pass`, no `None` for errors callers will not check. Ignore specific errors explicitly with `contextlib.suppress`.",
    "Log once, with the traceback (`logger.exception`), at the place that handles the error.",
    "Keep data consistent: validate first, build new then swap (`os.replace` for files), or undo on failure. Degrade gracefully, and record it.",
)
