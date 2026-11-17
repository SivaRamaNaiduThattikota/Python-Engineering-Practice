from lesson import *

lesson(
    id="m2-4", num="2.4", title="How arguments are passed",
    intro="Calling a function points its parameter names at your objects. That one rule explains why a function can "
          "change your list but not your variable, why mutable defaults leak between calls, and how to design "
          "functions that are safe to call.",
    desc="Passing a reference to an object, changing arguments, and the mutable default argument.",
    keys="argument parameter pass by object reference pass by assignment mutate rebind side effect pure function mutable default argument defaults evaluated once none sentinel __defaults__ args kwargs defensive copy inplace",
)

term("Pass by assignment", "Python's calling rule: each parameter name is assigned to the argument object, exactly like `param = arg`. Nothing is copied.")
term("Side effect", "A change a function makes outside itself, such as changing an argument in place, writing a file or calling an API.")
term("Pure function", "A function that only reads its arguments and returns a new result, with no side effects. Same input, same output.")
term("Mutable default argument", "A default like `items=[]`. It is created once, when the function is defined, and shared by every call that uses it.")

CALL_FIG = """
<svg viewBox="0 0 640 140" role="img" aria-label="Calling f(cart) points the parameter items at the same list as cart. items.append changes that list. items = [] only moves the parameter name.">
  <defs><marker id="p1" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M0 0 L10 5 L0 10 z" style="fill:var(--label2)"/></marker></defs>
  <text x="10" y="18" class="h">Caller</text>
  <rect x="10" y="40" width="70" height="30" rx="8" class="box"/><text x="45" y="60" class="tk">cart</text>
  <text x="250" y="18" class="h mid">One object</text>
  <rect x="190" y="52" width="120" height="40" rx="10" class="box a"/><text x="250" y="77" class="w mid">["a", "b"]</text>
  <text x="420" y="18" class="h">Inside f(items)</text>
  <rect x="420" y="40" width="70" height="30" rx="8" class="box"/><text x="455" y="60" class="tk">items</text>
  <rect x="520" y="96" width="100" height="30" rx="8" class="box b"/><text x="570" y="116" class="w mid">[ ]  new</text>
  <path d="M80 55 L186 68" style="stroke:var(--label2);stroke-width:2;fill:none" marker-end="url(#p1)"/>
  <path d="M420 55 L314 68" style="stroke:var(--label2);stroke-width:2;fill:none" marker-end="url(#p1)"/>
  <path d="M470 70 L530 94" style="stroke:var(--orange);stroke-width:2;fill:none;stroke-dasharray:4 3" marker-end="url(#p1)"/>
  <text x="250" y="116" class="mid">items.append(...) changes this</text>
  <text x="560" y="88" class="mid">items = [] moves only items</text>
</svg>"""

section("rule", "One rule: parameters are assigned, not copied",
    p("""When you call `f(cart)`, Python does what `items = cart` would do: it points the parameter name `items` at
    the **same object** that `cart` points at. Nothing is copied, which is why passing a million-row list to a function
    is instant. People argue whether this is "pass by value" or "pass by reference"; the accurate name is **pass by
    assignment** (or "pass by object reference"), and everything from 2.1 to 2.3 applies directly."""),
    fig(CALL_FIG, "The caller's name and the parameter point at one object. Changing it is visible to the caller; rebinding the parameter is not."),
    ex("""
    def add_item(items, x):
        items.append(x)        # changes the caller's list

    def reset(items):
        items = []             # moves only the local name

    cart = ["a"]
    add_item(cart, "b")
    reset(cart)
    print(cart)

    def bump(n):
        n += 1                 # an int cannot change: a new int, local name moved
        return n

    count = 1
    print(bump(count), count)
    """, "passing.py"),
    p("""So a function can **change a mutable argument in place** and the caller sees it, but **assigning to a parameter
    never affects the caller**. With immutable arguments (numbers, strings, tuples) a function cannot affect the caller's
    object at all; it can only return a new value."""),
    callout("sql", "SQL / Power BI", """Passing a list to a function is like giving a stored procedure the **name of a
    table**, not a copy of it: an `UPDATE` inside the procedure changes the real table. Assigning a new value to the
    parameter is like the procedure pointing its local variable at another table: the caller's table is untouched."""),
)

section("defaults", "Mutable default arguments",
    p("""A default value is evaluated **once, when the `def` statement runs**, and stored on the function object (you
    can see them in `f.__defaults__`). Every call that uses the default gets that same object. For immutable defaults this
    is harmless. For a list, dict or set, every call shares and changes one object, so data leaks from one call into the
    next."""),
    ex("""
    def log_event(event, log=[]):      # one list, created at definition time
        log.append(event)
        return log

    print(log_event("start"))
    print(log_event("stop"))           # the first call's event is still there
    print(log_event.__defaults__)
    """, "mutable_default.py"),
    p("""The fix is the `None` default plus a fresh object inside the function. If `None` is a valid value for that
    parameter, use a sentinel (2.1)."""),
    ex("""
    def log_event(event, log=None):
        if log is None:
            log = []                   # a new list on every call that needs one
        log.append(event)
        return log

    print(log_event("start"))
    print(log_event("stop"))
    shared = []
    log_event("a", shared); log_event("b", shared)
    print(shared)                      # passing a list on purpose still works
    """, "none_default.py"),
    callout("warn", "It is not only lists", """Anything computed in a default is computed once: `created=datetime.now()`
    freezes one timestamp for every call, `request_id=uuid4()` gives every request the same id, and
    `conn=connect()` opens one connection at import time. Use `None` and compute the value inside the function
    (problem 6)."""),
)

section("design", "Designing functions that are safe to call",
    p("""Because a function receives your actual objects, every function makes a choice, whether it says so or not:"""),
    p("""- **Pure:** read the arguments, return a new result, change nothing. Easiest to test, safe to call twice, safe
      to retry. The default choice for data transformations: `sorted`, `dict | dict`, comprehensions.
    - **In place:** change the argument and return `None`, like `list.sort()`. Saves memory on big data. The name or
      docstring should make the side effect obvious, and the `None` return stops callers from assuming they got a
      copy.
    - **Defensive copy at the boundary:** when you call code you do not control (plugins, agent tools, user callbacks),
      pass a copy so it cannot change your data (problem 15)."""),
    p("""What to avoid is the mixture: a function that changes its argument **and** returns it, so the caller thinks they
    got a new object but actually holds an alias (problems 7 and 11). pandas offers both styles through an
    `inplace=True` parameter, and has been moving away from it because the mixture caused so many bugs."""),
    callout("note", "*args and **kwargs (preview of 3.2)", """`*args` arrives as a **new tuple** and `**kwargs` as a
    **new dict** on every call, so changing those containers never affects the caller. The values inside them are still
    the caller's objects (problem 10)."""),
)

section("warmup", "Warm-up",
    predict("Change or rebind?", "easy",
        code="""
        def clear_all(items):
            items.clear()

        def replace(items):
            items = ["new"]
            return items

        data = [1, 2]
        clear_all(data)
        print(data)

        data = [1, 2]
        out = replace(data)
        print(data, out)

        def shout(text):
            text = text.upper()
        msg = "hi"
        shout(msg)
        print(msg)
        """,
        hints=["Which functions change the object they were given, and which only move their own parameter name?"],
        why="""`items.clear()` empties the caller's list in place. `items = ["new"]` moves only the local name, so `data`
        is unchanged, and the new list reaches the caller only because it is returned. `text.upper()` builds a new string
        and the local name moves; strings cannot be changed, so no function can change the caller's `msg`."""),
    fix("An event log that remembers too much", "easy",
        prompt="""Each call to `log_event` without a log should start a new log. Instead, events from earlier calls keep
        appearing. Fix it, and keep the option of passing an existing log.""",
        code="""
        def log_event(event, log=[]):
            log.append(event)
            return log
        """,
        tests="""
        assert log_event("start") == ["start"]
        assert log_event("stop") == ["stop"]
        mine = ["boot"]
        assert log_event("ready", mine) is mine and mine == ["boot", "ready"]
        assert log_event.__defaults__ == (None,)
        """,
        hints=["Use `None` as the default and create the list inside the function."],
        solution="""
        def log_event(event, log=None):
            if log is None:
                log = []
            log.append(event)
            return log
        """,
        why="""The `[]` in the signature is evaluated once, so every call without a `log` shares one list. With `None`
        as the default, `log = []` runs inside the function, on each call that needs it. The last test checks the fix
        directly through `__defaults__`. Linters flag this pattern (Ruff rule B006, from flake8-bugbear) because it is one
        of the most common bugs in Python code."""),
    predict("A default computed once", "easy",
        code="""
        import itertools

        counter = itertools.count(1)

        def make_job(name, job_id=next(counter)):
            return (name, job_id)

        print(make_job("a"), make_job("b"))
        print(make_job("c", next(counter)))
        print(make_job.__defaults__)
        """,
        hints=["`next(counter)` in the signature runs exactly once. When?"],
        why="""The default `next(counter)` ran once, when `def` executed, and stored `1`. Every call without a `job_id`
        reuses it, so jobs `"a"` and `"b"` both get id 1. The explicit `next(counter)` in the third call runs at call time
        and gets 2. The same thing happens with `datetime.now()`, `uuid4()` or `random.random()` used as defaults: one
        frozen value for the life of the program."""),
    write("Add a system prompt without changing the input", "easy", tag="GenAI",
        prompt="""Write `with_system(messages, system)` that returns a **new** list with a system message
        `{"role": "system", "content": system}` first. If the first message is already a system message, replace it in
        the new list instead of adding a second one. The caller's list must not change.""",
        code="""
        def with_system(messages, system):
            pass
        """,
        tests="""
        msgs = [{"role": "user", "content": "hi"}]
        out = with_system(msgs, "Be brief.")
        assert out == [{"role": "system", "content": "Be brief."}, {"role": "user", "content": "hi"}]
        assert msgs == [{"role": "user", "content": "hi"}]
        old = [{"role": "system", "content": "Old."}, {"role": "user", "content": "hi"}]
        out2 = with_system(old, "New.")
        assert out2[0]["content"] == "New." and len(out2) == 2
        assert old[0]["content"] == "Old."
        assert with_system([], "S") == [{"role": "system", "content": "S"}]
        """,
        hints=["Build the result with `+`, which makes a new list. Use a slice to skip an existing system message."],
        solution="""
        def with_system(messages, system):
            rest = messages[1:] if messages and messages[0]["role"] == "system" else messages
            return [{"role": "system", "content": system}] + rest
        """,
        why="""`[...] + rest` builds a new list, so the caller's list is never touched, and the replacement is done by
        **not including** the old system message rather than by editing it (which would change the caller's dict, 2.3).
        Pure functions like this are what make prompt-building code safe to call from several requests at once."""),
)

section("medium", "Medium",
    fix("Agent memory shared between users", "medium", tag="GenAI",
        prompt="""`answer` keeps conversation memory so follow-up questions have context. Two different users calling it
        without their own memory end up seeing each other's questions. Fix it so each call without `memory` starts empty,
        while a memory passed in is used and updated.""",
        code="""
        def answer(question, memory={}):
            history = memory.setdefault("history", [])
            history.append(question)
            return f"answering {question!r} with {len(history) - 1} earlier turns"
        """,
        tests="""
        assert answer("What is RAG?") == "answering 'What is RAG?' with 0 earlier turns"
        assert answer("Reset my password") == "answering 'Reset my password' with 0 earlier turns"
        session = {}
        answer("first", session)
        assert answer("second", session) == "answering 'second' with 1 earlier turns"
        assert session == {"history": ["first", "second"]}
        """,
        hints=["The `{}` default is one dict for the whole program, and `setdefault` stores the history list inside it."],
        solution="""
        def answer(question, memory=None):
            if memory is None:
                memory = {}
            history = memory.setdefault("history", [])
            history.append(question)
            return f"answering {question!r} with {len(history) - 1} earlier turns"
        """,
        why="""The default dict is created once and lives as long as the function, so the history of every caller who did
        not pass their own memory accumulates in it. In a web service that is a **privacy** bug, not just a logic bug:
        one user's questions become context for another user's answers. The `None` default gives each such call a fresh
        dict. In real agent frameworks memory is an explicit object created per session for exactly this reason."""),
    fix("Every record has the same timestamp", "medium", tag="Data work",
        prompt="""`make_record` should stamp each record with the time it was created. All records get the same time,
        the moment the module was loaded. Fix it so the time is taken on each call, while still letting callers pass
        their own `created` value (for backfills and tests).""",
        code="""
        from datetime import datetime, timezone

        def make_record(text, created=datetime.now(timezone.utc)):
            return {"text": text, "created": created}
        """,
        tests="""
        from datetime import datetime, timezone
        r1 = make_record("a")
        r2 = make_record("b")
        assert r1["created"] is not r2["created"]
        assert r1["created"].tzinfo is timezone.utc
        fixed = datetime(2025, 1, 1, tzinfo=timezone.utc)
        assert make_record("c", fixed)["created"] is fixed
        assert make_record.__defaults__ == (None,)
        """,
        hints=["Same fix as a mutable default: `None` in the signature, the real value computed inside."],
        solution="""
        from datetime import datetime, timezone

        def make_record(text, created=None):
            if created is None:
                created = datetime.now(timezone.utc)
            return {"text": text, "created": created}
        """,
        why="""The default `datetime.now(...)` ran once when the module was imported, so every record shares that one
        `datetime` object. A `datetime` is immutable, so this is not an aliasing bug, it is an **evaluated-once** bug, which
        is why the rule is about defaults in general, not just mutable ones. Accepting an explicit `created` keeps the
        function testable: tests can pass a fixed time instead of depending on the clock."""),
    trace("What the caller sees after each call", "medium",
        prompt="Fill in `data` and `result` after each marked line. Read `f` carefully first.",
        code="""
        def f(xs):
            xs.append(1)
            xs = xs + [2]
            xs.append(3)
            return xs

        data = [0]
        result = f(data)  # row: "result = f(data)"
        result.append(4)  # row: "result.append(4)"
        data = f(data)  # row: "data = f(data)"
        """,
        trace_vars=["data", "result"],
        hints=["Inside `f`, the first `append` changes the caller's list. After `xs = xs + [2]`, `xs` is a different list."],
        why="""The first `xs.append(1)` changes the caller's list, so `data` becomes `[0, 1]`. Then `xs + [2]` builds a new
        list, and the second `append` changes only that new list, which is returned as `result`. `result.append(4)`
        changes only `result`. The second call appends 1 to `data` again (it is the same list), then returns another new
        list, which `data` is rebound to. A function that changes its input **and** returns a different object is the
        hardest kind to reason about; this is why the mixture should be avoided."""),
    write("A transform with an explicit in-place option", "medium", tag="ML",
        prompt="""Write `scale_rows(rows, factor, inplace=False)`. By default it returns a **new** list of new rows with
        every value multiplied by `factor`, leaving `rows` untouched. With `inplace=True` it changes the caller's rows
        themselves (the same inner list objects) and returns `None`.""",
        code="""
        def scale_rows(rows, factor, inplace=False):
            pass
        """,
        tests="""
        data = [[1, 2], [3, 4]]
        out = scale_rows(data, 10)
        assert out == [[10, 20], [30, 40]] and data == [[1, 2], [3, 4]]
        assert out[0] is not data[0]
        inner = data[0]
        assert scale_rows(data, 2, inplace=True) is None
        assert data == [[2, 4], [6, 8]] and data[0] is inner
        assert scale_rows([], 3) == []
        """,
        hints=["For `inplace=True`, change each row's contents with slice assignment `row[:] = ...` so the row objects stay the same."],
        solution="""
        def scale_rows(rows, factor, inplace=False):
            if inplace:
                for row in rows:
                    row[:] = [v * factor for v in row]
                return None
            return [[v * factor for v in row] for row in rows]
        """,
        why="""The two modes make the side effect explicit at the call site: `scale_rows(x, 2)` is safe, and
        `scale_rows(x, 2, inplace=True)` says loudly that `x` changes. Returning `None` in place mode prevents
        `y = scale_rows(x, 2, inplace=True)` from looking like it produced a copy. pandas has been moving away from its `inplace`
        parameters because people mixed the modes up; if you add one, keep the two paths this clearly separated."""),
    choose("Does passing a list copy it?", "medium",
        prompt="Both look up the first item of a million-item list through a function. Which is faster?",
        setup="""big = list(range(1_000_000))
def first(xs):
    return xs[0]""",
        options={
            "a": "x = first(big)",
            "b": "x = first(list(big))",
        },
        answer="a",
        hints=["What does Python copy when you call `total(big)`?"],
        why="""Passing `big` copies nothing: the parameter just points at the same list, so A costs one index lookup, no
        matter how big the list is. B first builds a full copy of a million references, then throws it away. When the
        function itself does heavy work (say, summing every item), that work can hide the copy's cost in a measurement,
        but the copy is still wasted time and memory. Copy only when the function would otherwise change data the caller
        needs, or when calling code you do not trust."""),
    predict("What `*args` and `**kwargs` receive", "medium",
        code="""
        def capture(*args, **kwargs):
            return args, kwargs

        tags = ["x"]
        opts = {"k": 5}
        a, kw = capture(tags, **opts)
        a[0].append("y")
        kw["k"] = 9
        print(tags, opts)
        print(type(a).__name__, kw is opts)
        """,
        hints=["`*args` and `**kwargs` are new containers built for each call. What do they contain?"],
        why="""`args` is a new **tuple** and `kwargs` a new **dict**, built on every call, so `kw["k"] = 9` changes only
        that dict and `opts` keeps 5. But the tuple's item is the caller's own `tags` list, so appending to `a[0]` changes
        `tags`. Unpacking with `**opts` copies the keys and values into a new dict: one level, like a shallow copy (2.3)."""),
    fix("A cleaner that changes the raw data", "medium", tag="Data work",
        prompt="""`clean_record` normalises a CRM record before loading it. The raw record must be kept unchanged for the
        audit log, but after cleaning it has changed too. Make `clean_record` pure: return a new, cleaned dict.""",
        code="""
        def clean_record(rec):
            rec["email"] = rec["email"].strip().lower()
            if rec.get("phone") == "":
                del rec["phone"]
            rec["tags"].append("cleaned")
            return rec
        """,
        tests="""
        raw = {"email": "  Ana@Example.COM ", "phone": "", "tags": ["crm"]}
        out = clean_record(raw)
        assert out == {"email": "ana@example.com", "tags": ["crm", "cleaned"]}
        assert raw == {"email": "  Ana@Example.COM ", "phone": "", "tags": ["crm"]}
        assert out["tags"] is not raw["tags"]
        assert clean_record({"email": "B@x.io", "phone": "123", "tags": []}) == {"email": "b@x.io", "phone": "123", "tags": ["cleaned"]}
        """,
        hints=["Start from a copy of the record, but remember `tags` is a list inside it (2.3).",
               "Building the result directly is cleaner than copying and then deleting: include `phone` only if it is not empty."],
        solution="""
        def clean_record(rec):
            out = {k: v for k, v in rec.items() if not (k == "phone" and v == "")}
            out["email"] = rec["email"].strip().lower()
            out["tags"] = rec["tags"] + ["cleaned"]
            return out
        """,
        why="""The original changes the caller's dict three ways: a new value, a deleted key, and an append to the nested
        list. A shallow `dict(rec)` would fix the first two and still change `raw["tags"]`. The solution builds a new dict,
        leaves out the empty phone instead of deleting it, and makes a new tags list with `+`. Keeping the raw input intact
        is what makes a pipeline re-runnable: you can always clean the raw data again with a fixed version."""),
    refactor("A pure transform, written as one expression", "medium",
        prompt="This adds a tag to every document and returns new documents. It works but is long. Shorten it without changing behaviour. Keep the tests green.",
        code="""
        def tag_all(docs, tag):
            result = []
            for d in docs:
                new_d = {}
                for k in d:
                    new_d[k] = d[k]
                new_tags = []
                for t in d["tags"]:
                    new_tags.append(t)
                new_tags.append(tag)
                new_d["tags"] = new_tags
                result.append(new_d)
            return result
        """,
        tests="""
        docs = [{"id": 1, "tags": ["faq"]}, {"id": 2, "tags": []}]
        out = tag_all(docs, "v2")
        assert out == [{"id": 1, "tags": ["faq", "v2"]}, {"id": 2, "tags": ["v2"]}]
        assert docs == [{"id": 1, "tags": ["faq"]}, {"id": 2, "tags": []}]
        assert out[0] is not docs[0] and out[0]["tags"] is not docs[0]["tags"]
        """,
        hints=["`{**d, \"tags\": ...}` copies a dict and overrides one key in a single expression."],
        solution="""
        def tag_all(docs, tag):
            return [{**d, "tags": d["tags"] + [tag]} for d in docs]
        """,
        why="""`{**d, "tags": ...}` is a shallow copy of `d` with one key replaced, and `d["tags"] + [tag]` builds the new
        list, so no object of the input is changed and the one nested list that differs is new. This "copy and override"
        expression is the everyday way to write pure transformations of records in Python, and it reads like the spec:
        same document, with the tag added."""),
)

section("hard", "Hard",
    predict("Read the code: a default that escapes", "hard",
        code="""
        def collect(x, bucket=[]):
            bucket.append(x)
            return bucket

        first = collect(1)
        second = collect(2)
        first.append(99)
        print(collect(3))
        print(first is second, collect.__defaults__[0] is first)

        mine = collect(4, [])
        print(mine, collect.__defaults__)
        """,
        hints=["The function **returns** its default list, so the caller now holds an alias to it."],
        why="""Every call without `bucket` appends to the single default list and returns it, so `first`, `second` and
        `collect.__defaults__[0]` are all the same object. That is worse than a plain mutable default: the caller's
        `first.append(99)` writes straight into the function's default, so the next call sees 99. Passing `[]` explicitly
        uses a new list and leaves the default alone, so the last line shows `[4]` and the default still holding 1, 2,
        99 and 3."""),
    fix("Read the code: a retry wrapper with two leaks", "hard", tag="GenAI",
        prompt="""`call_with_retry` calls an LLM function up to `attempts` times and returns the result plus the errors it
        saw. In production, the error list of one request contains errors from earlier requests, and the caller's payload
        comes back with an `"attempt"` key in it, which then gets sent on the next request. Find both problems and fix
        them.""",
        code="""
        class TransientError(Exception):
            pass


        def call_with_retry(fn, payload, attempts=3, errors=[]):
            for attempt in range(1, attempts + 1):
                payload["attempt"] = attempt
                try:
                    return fn(payload), errors
                except TransientError as e:
                    errors.append(f"attempt {attempt}: {e}")
            raise RuntimeError(f"failed after {attempts} attempts: {errors}")


        def flaky(fails):
            state = {"left": fails}
            def fn(payload):
                if state["left"] > 0:
                    state["left"] -= 1
                    raise TransientError("rate limited")
                return f"ok on attempt {payload['attempt']}"
            return fn
        """,
        tests="""
        p = {"prompt": "hi"}
        result, errs = call_with_retry(flaky(1), p)
        assert result == "ok on attempt 2" and errs == ["attempt 1: rate limited"]
        assert p == {"prompt": "hi"}
        result2, errs2 = call_with_retry(flaky(0), {"prompt": "again"})
        assert result2 == "ok on attempt 1" and errs2 == []
        assert errs == ["attempt 1: rate limited"]
        """,
        hints=["`errors=[]` is created once. Every request that does not pass `errors` shares it.",
               "`payload[\"attempt\"] = attempt` writes into the caller's dict. Send a new dict to `fn` instead."],
        solution="""
        class TransientError(Exception):
            pass


        def call_with_retry(fn, payload, attempts=3, errors=None):
            if errors is None:
                errors = []
            for attempt in range(1, attempts + 1):
                try:
                    return fn({**payload, "attempt": attempt}), errors
                except TransientError as e:
                    errors.append(f"attempt {attempt}: {e}")
            raise RuntimeError(f"failed after {attempts} attempts: {errors}")


        def flaky(fails):
            state = {"left": fails}
            def fn(payload):
                if state["left"] > 0:
                    state["left"] -= 1
                    raise TransientError("rate limited")
                return f"ok on attempt {payload['attempt']}"
            return fn
        """,
        why="""Bug one is the mutable default: one `errors` list for the life of the process, so every request reports the
        failures of all earlier ones, and it grows without limit. Bug two is a side effect on the argument:
        `payload["attempt"] = ...` writes into the caller's dict, which is then reused for the next request with a stale
        `attempt` key in it. The fix builds a new dict per attempt with `{**payload, "attempt": attempt}`. Retry code is
        exactly where side effects hurt most, because the same call runs several times: anything a call changes in its
        input is changed again on every retry. (`flaky` uses a closure to keep its counter; closures are lesson 3.4.)"""),
    write("Call untrusted tools on copies", "hard", tag="GenAI",
        prompt="""An agent runs tool functions written by other teams, and some of them change the arguments they get.
        Write `safe_call(fn, *args, **kwargs)` that calls `fn` with **deep copies** of all positional and keyword
        arguments and returns its result, so no tool can change the agent's own data.""",
        code="""
        import copy

        def safe_call(fn, *args, **kwargs):
            pass
        """,
        tests="""
        def bad_tool(query, filters, *, limit):
            filters["year"] = 1999
            query["text"] = query["text"].upper()
            return f"{query['text']} {filters} {limit}"
        q = {"text": "refunds"}
        f = {"year": 2025, "tags": ["eu"]}
        assert safe_call(bad_tool, q, f, limit=3) == "REFUNDS {'year': 1999, 'tags': ['eu']} 3"
        assert q == {"text": "refunds"} and f == {"year": 2025, "tags": ["eu"]}
        def appender(items):
            items.append("x")
            return len(items)
        data = [1]
        assert safe_call(appender, data) == 2 and data == [1]
        """,
        hints=["Deep-copy the whole `args` tuple and the whole `kwargs` dict, then call `fn(*new_args, **new_kwargs)`."],
        solution="""
        import copy

        def safe_call(fn, *args, **kwargs):
            return fn(*copy.deepcopy(args), **copy.deepcopy(kwargs))
        """,
        why="""Copying the `args` tuple and `kwargs` dict as wholes copies every argument inside them, at every level, and
        one memo per call keeps shared arguments shared. This is a **defensive copy at the boundary**: inside your own
        code you avoid copies, but at the edge where code you do not control runs, you pay for one so the agent's state,
        logs and retries cannot be corrupted. It costs time on big arguments, so real frameworks often validate tool
        arguments into fresh objects instead (Pydantic models built from the LLM's JSON), which gives the same isolation
        as a side benefit."""),
    predict("Passing an iterator, not a list", "hard",
        code="""
        def stats(values):
            return min(values), max(values)

        data = [3, 1, 2]
        print(stats(data))
        gen = (x for x in data)
        try:
            print(stats(gen))
        except ValueError as e:
            print("ValueError:", e)
        """,
        hints=["A generator produces its values once. What is left for `max` after `min` has read them all?"],
        why="""A list can be read any number of times, so `stats(data)` works. A generator (Module 6) is used up as it is
        read: `min` consumes all three values, and `max` then sees an empty iterator and raises `ValueError`. The function
        "works in the test" with a list and fails in production when someone passes a generator, a file, or a database
        cursor. Either accept that the argument is read once (compute both in one loop), or turn it into a list at the start
        with `values = list(values)`, and document which one the function does."""),
)

section("interview", "Interview questions",
    explain("Is Python pass-by-value or pass-by-reference?", "medium", tag="Interview",
        why="""Neither, exactly. Python passes **references to objects**, and the parameter is assigned to the argument
        like a normal `=` ("pass by assignment" or "call by object reference"). Consequences: if the object is mutable and
        the function changes it in place, the caller sees the change, which looks like pass-by-reference. If the function
        assigns a new object to the parameter, the caller is unaffected, which looks like pass-by-value. Nothing is copied
        on a call, so passing large data is cheap. Give the two-line example (`append` versus `items = []`), and mention
        that immutable arguments can never be changed by the callee."""),
    explain("Why are mutable default arguments dangerous, and are they ever used on purpose?", "hard", tag="Interview",
        why="""Defaults are evaluated once when `def` runs and stored on the function (`__defaults__`), so a list or dict
        default is one object shared by every call that does not pass the argument. Data leaks between calls, and if the
        function returns it, callers hold aliases to it. The fix is `None` (or a sentinel) plus creating the object inside.
        The same once-only evaluation also freezes values like `datetime.now()` or `uuid4()`. Deliberate uses exist: a
        default dict as a cheap memo cache (`def fib(n, _cache={})`), but `functools.cache` does this more clearly and is
        what you should say you would use. Bonus: dataclasses refuse a mutable default and require
        `field(default_factory=list)`, which builds a new list per instance."""),
    explain("An agent's tool function changes the arguments dict the LLM produced. Why is that a problem, and how do you prevent it?", "hard", tag="Interview",
        why="""The same dict usually lives on after the call: it is logged, stored in the conversation history, shown in
        traces, and reused if the step is retried or replayed. A tool that changes it rewrites history: traces show
        arguments the model never sent, retries run with altered input, and evaluation datasets built from logs are wrong.
        Prevention, from lightest to strongest: write tools as pure functions; validate the LLM's JSON into a fresh object
        (a Pydantic model) before calling the tool, so the tool never sees the logged dict; pass a deep copy at the boundary
        when calling third-party tools; or store logged arguments in read-only form. The principle is the one from this
        lesson: a function receives your actual object, so the boundary decides who may change it."""),
)

recap(
    "A call does `param = argument`: nothing is copied. Changing a mutable argument in place is visible to the caller; assigning to the parameter never is.",
    "Defaults are evaluated once, at `def` time: `items=[]`, `memory={}`, `created=datetime.now()` are all shared or frozen. Use `None` and build the value inside.",
    "Choose deliberately: pure (return new, change nothing), or in place (change and return `None`). Never change the input and return it.",
    "Copy at boundaries you do not control (tools, plugins), not on every call. Passing a big list is free; copying it is not.",
    "An iterator argument can be read only once. Accept that, or convert to a list at the start.",
)
