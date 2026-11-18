from lesson import *
from diagrams import *

lesson(
    id="m3-p", num="3.P", title="Module 3 practice set and mini project",
    intro="Mixed problems from all of Module 3: defining and calling, flexible arguments, scope, closures and functions "
          "as values. Then a mini project that needs all of it: a small tool runtime for an agent.",
    desc="Mixed problems from the whole module, then one small program that uses all of it.",
    keys="practice mixed review project tool runtime registry signature closures dispatch partial scope keyword only",
)

section("how", "How to use this page",
    fig(stage_map(3, "a tool runtime for an agent"), "Module 3 at a glance: from defining functions to passing them around as values, building up to a tool runtime."),
    p("""Before opening a hint, name the idea the problem is about: how a call fills parameters (3.1, 3.2), where a name is
    looked up or assigned (3.3), what a closure captures and when it reads it (3.4), or passing functions around (3.5).
    Several problems mix two of these, as real bugs do."""),
)

section("set", "Practice set",
    predict("Factories, defaults and keywords together", "easy",
        code="""
        def make(n, items=None, *, tag="x"):
            items = [] if items is None else items
            items.append(n)
            return lambda: (n, len(items), tag)

        shared = []
        fs = [make(i, shared, tag=t) for i, t in zip(range(3), "abc")]
        print([f() for f in fs])
        print(make(9)(), shared)
        """,
        hints=["Each `make` call has its own `n` and `tag`, but which calls share one `items` list?"],
        why="""Every call gets its own `n` and `tag` cells, so the three lambdas report 0, 1, 2 and a, b, c. But the first three
        calls all receive the same `shared` list and append to it, so by the time the lambdas run it holds three items, and all
        three report a length of 3: the closure reads the list when it is called (late binding of the object's contents).
        `make(9)` gets a fresh list from the `None` default, so it reports 1 and does not touch `shared`."""),
    fix("An accumulator that crashes", "easy",
        prompt="""`collect_errors` should gather error messages across a batch and return them. It raises
        `UnboundLocalError` on the first error. Fix it with the smallest change that keeps the module free of global state.""",
        code="""
        def collect_errors(rows):
            def check(row):
                if row.get("amount") is None:
                    errors = errors + [f"row {row['id']}: missing amount"]
            errors = []
            for row in rows:
                check(row)
            return errors
        """,
        tests="""
        rows = [{"id": 1, "amount": 5}, {"id": 2}, {"id": 3, "amount": None}]
        assert collect_errors(rows) == ["row 2: missing amount", "row 3: missing amount"]
        assert collect_errors([]) == []
        """,
        hints=["`errors = errors + [...]` assigns `errors`, so inside `check` it is a local name.",
               "Either change the list in place, or declare that you mean the enclosing variable."],
        solution="""
        def collect_errors(rows):
            def check(row):
                if row.get("amount") is None:
                    errors.append(f"row {row['id']}: missing amount")
            errors = []
            for row in rows:
                check(row)
            return errors
        """,
        why="""The assignment `errors = errors + [...]` makes `errors` local to `check` (3.3), so reading it on the right-hand side
        fails. `errors.append(...)` changes the enclosing list in place without assigning the name, so no declaration is needed.
        `nonlocal errors` would also work, but appending is simpler and avoids building a new list for every error (2.2)."""),
    write("A normaliser fitted once", "medium", tag="ML",
        prompt="""Write `fit_minmax(values)` that computes the minimum and maximum of `values` and returns a function
        `transform(x)` giving `(x - lo) / (hi - lo)`. If all values are equal, `transform` returns 0.0. The returned function
        must not change if the caller later changes `values`.""",
        code="""
        def fit_minmax(values):
            pass
        """,
        tests="""
        train = [10, 20, 30]
        t = fit_minmax(train)
        assert [t(x) for x in [10, 25, 30, 40]] == [0.0, 0.75, 1.0, 1.5]
        train.append(1000)
        assert t(30) == 1.0
        assert fit_minmax([5, 5])(7) == 0.0
        """,
        hints=["Compute `lo` and `hi` in the factory, then close over those numbers, not over the list."],
        solution="""
        def fit_minmax(values):
            lo, hi = min(values), max(values)
            span = hi - lo

            def transform(x):
                return 0.0 if span == 0 else (x - lo) / span

            return transform
        """,
        why="""The closure captures the fitted **numbers** `lo` and `span`, computed once in the factory, not the list itself, so
        later changes to `train` cannot change the transform (compare 3.4, problem 8, where capturing the list caused that).
        Values outside the training range map outside 0 to 1, which is correct behaviour for min-max scaling: scikit-learn's
        `MinMaxScaler` does the same unless you pass `clip=True`. Fitting on training data and reusing the fitted state on test
        data is the whole idea of `fit` / `transform`."""),
    predict("Scope and closures in one function", "medium",
        code="""
        level = "global"

        def outer():
            level = "outer"
            def show():
                return level
            def change():
                nonlocal level
                level = "changed"
            before = show()
            change()
            return before, show(), level

        print(outer(), level)
        """,
        hints=["`show` and `change` share outer's `level` cell. `change` rebinds it."],
        why="""`show` reads `outer`'s `level` through a cell. `change` uses `nonlocal`, so it rebinds that same cell to
        `"changed"`. So `show()` returns `"outer"` before the change and `"changed"` after, and `outer`'s own `level` changed
        too, since it is the same variable. The global `level` is never touched."""),
    write("Route a question to the first matching handler", "medium", tag="GenAI",
        prompt="""Write `route(question, routes, default)` where `routes` is a list of `(predicate, handler)` pairs. Call the
        handler of the **first** pair whose predicate returns a truthy value for the question, and return its result. If none
        match, return `default(question)`. Handlers must only be called when chosen.""",
        code="""
        def route(question, routes, default):
            pass
        """,
        tests="""
        called = []
        def sql_handler(q):
            called.append("sql")
            return "SQL: " + q
        def rag_handler(q):
            called.append("rag")
            return "RAG: " + q
        routes = [(lambda q: "how many" in q.lower(), sql_handler),
                  (lambda q: "policy" in q.lower(), rag_handler)]
        assert route("How many refunds last week?", routes, str.upper) == "SQL: How many refunds last week?"
        assert route("What is the refund policy?", routes, str.upper) == "RAG: What is the refund policy?"
        assert route("hello", routes, str.upper) == "HELLO"
        assert called == ["sql", "rag"]
        """,
        hints=["Loop over the pairs, unpacking each into `predicate, handler`; return as soon as one matches."],
        solution="""
        def route(question, routes, default):
            for predicate, handler in routes:
                if predicate(question):
                    return handler(question)
            return default(question)
        """,
        why="""Both the rules and the actions are passed in as functions, so the router has no knowledge of SQL or RAG: adding a
        route means adding a pair. Returning inside the loop guarantees only the chosen handler runs (the `called` list proves
        it), which matters when handlers make paid API calls. This is the "hybrid router" pattern in LLM apps (decide between
        text-to-SQL, retrieval and a plain answer), usually with an LLM classifier as one of the predicates."""),
    fix("A two-direction sort that crashes", "medium", tag="Data work",
        prompt="""`order_tickets` should sort by `team` ascending, then by `title` **descending** within each team. Negating
        the title crashes, because you cannot negate a string. Fix it.""",
        code="""
        def order_tickets(tickets):
            return sorted(tickets, key=lambda t: (t["team"], -t["title"]))
        """,
        tests="""
        tickets = [{"team": "billing", "title": "Refund"}, {"team": "auth", "title": "Login"},
                   {"team": "billing", "title": "Invoice"}, {"team": "auth", "title": "Reset"}]
        assert [(t["team"], t["title"]) for t in order_tickets(tickets)] == [
            ("auth", "Reset"), ("auth", "Login"), ("billing", "Refund"), ("billing", "Invoice")]
        assert order_tickets([]) == []
        """,
        hints=["Python's sort is stable. Sort by the secondary rule first, then by the primary rule."],
        solution="""
        def order_tickets(tickets):
            by_title = sorted(tickets, key=lambda t: t["title"], reverse=True)
            return sorted(by_title, key=lambda t: t["team"])
        """,
        why="""A tuple key can reverse a **number** by negating it, but there is no negative string. Stability solves it: the
        second sort orders by team, and within equal teams it keeps the order the first sort produced, which was title
        descending. Sorting by the least important rule first and the most important last works for any mix of directions,
        and it is the method the Python sorting HOWTO recommends."""),
    choose("A dispatch dict or an `if` chain", "medium",
        prompt="Both choose one of 20 handlers by name, and the name asked for is the 20th. Which is faster over many calls?",
        setup="""handlers = {f"h{i}": (lambda i=i: i) for i in range(20)}
def via_chain(name):
    if name == "h0": return handlers["h0"]()
    elif name == "h1": return handlers["h1"]()
    elif name == "h2": return handlers["h2"]()
    elif name == "h3": return handlers["h3"]()
    elif name == "h4": return handlers["h4"]()
    elif name == "h5": return handlers["h5"]()
    elif name == "h6": return handlers["h6"]()
    elif name == "h7": return handlers["h7"]()
    elif name == "h8": return handlers["h8"]()
    elif name == "h9": return handlers["h9"]()
    elif name == "h10": return handlers["h10"]()
    elif name == "h11": return handlers["h11"]()
    elif name == "h12": return handlers["h12"]()
    elif name == "h13": return handlers["h13"]()
    elif name == "h14": return handlers["h14"]()
    elif name == "h15": return handlers["h15"]()
    elif name == "h16": return handlers["h16"]()
    elif name == "h17": return handlers["h17"]()
    elif name == "h18": return handlers["h18"]()
    elif name == "h19": return handlers["h19"]()
def via_dict(name):
    return handlers[name]()""",
        options={
            "a": "for _ in range(20000):\n    via_chain(\"h19\")",
            "b": "for _ in range(20000):\n    via_dict(\"h19\")",
        },
        answer="b",
        hints=["How many string comparisons does the chain make before it reaches `h19`?"],
        why="""The `if` chain compares the name with each option in order, so the last option costs 20 comparisons on every call:
        O(n) in the number of options. The dict hashes the name once and jumps straight to the handler: O(1) on average (lesson
        4.4). Speed is the smaller benefit, though; the dispatch table is also shorter, cannot have a copy-paste mismatch
        between the name tested and the handler called, and gives you the list of valid names for free."""),
    refactor("Replace a hand-written sort", "medium",
        prompt="This orders leaderboard entries by score (highest first), then name (A to Z), with a hand-written selection sort. Replace it with one `sorted` call. Keep the tests green.",
        code="""
        def leaderboard(entries):
            items = list(entries)
            out = []
            while items:
                best = items[0]
                for e in items[1:]:
                    if e["score"] > best["score"] or (e["score"] == best["score"] and e["name"] < best["name"]):
                        best = e
                items.remove(best)
                out.append(best)
            return out
        """,
        tests="""
        entries = [{"name": "cy", "score": 0.8}, {"name": "ana", "score": 0.9}, {"name": "ben", "score": 0.8}]
        assert [e["name"] for e in leaderboard(entries)] == ["ana", "ben", "cy"]
        assert leaderboard([]) == []
        assert entries[0]["name"] == "cy"
        """,
        hints=["Tuple key: negated score, then name."],
        solution="""
        def leaderboard(entries):
            return sorted(entries, key=lambda e: (-e["score"], e["name"]))
        """,
        why="""The selection sort is O(n²) and hides the ordering rule inside a comparison; the key states the rule directly and
        `sorted` runs in O(n log n). Note one subtle problem the old version had: `items.remove(best)` removes the first **equal**
        entry (2.1), which only worked because the entries happened to be distinct dicts. The new version cannot have that bug."""),
    write("A memoiser that treats equivalent calls the same", "hard", tag="Interview",
        prompt="""Write `memoize(fn)` returning a function that caches results by the **bound** arguments, so `f(1, 2)`,
        `f(1, b=2)` and `f(a=1, b=2)` share one cache entry, and defaults are included (so `f(1)` is the same as `f(1, 2)` when
        `b=2` is the default). Arguments are hashable. Expose the cache size as `wrapper.cache_size()`.""",
        code="""
        import inspect

        def memoize(fn):
            pass
        """,
        tests="""
        calls = []
        def score(a, b=2, *, scale=1):
            calls.append((a, b, scale))
            return (a + b) * scale
        s = memoize(score)
        assert s(1, 2) == 3 and s(1, b=2) == 3 and s(a=1, b=2) == 3 and s(1) == 3
        assert s(1, scale=10) == 30
        assert calls == [(1, 2, 1), (1, 2, 10)]
        assert s.cache_size() == 2
        """,
        hints=["Build the key with `inspect.signature(fn).bind(*args, **kwargs)`, then `apply_defaults()` (3.2, problem 13).",
               "`tuple(bound.arguments.items())` is a hashable key when the values are hashable."],
        solution="""
        import inspect

        def memoize(fn):
            sig = inspect.signature(fn)
            cache = {}

            def wrapper(*args, **kwargs):
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                key = tuple(bound.arguments.items())
                if key not in cache:
                    cache[key] = fn(*args, **kwargs)
                return cache[key]

            wrapper.cache_size = lambda: len(cache)
            return wrapper
        """,
        why="""A naive cache keyed by `(args, tuple(kwargs.items()))` treats `f(1, 2)` and `f(1, b=2)` as different calls, so the
        same expensive work runs again. Binding the arguments to the signature normalises every spelling of a call into one
        mapping from parameter names to values, defaults included. The signature is computed once in the factory, not on every
        call, and `cache` lives in the closure (3.4). `functools.lru_cache` does **not** normalise like this: it treats
        `f(1, 2)` and `f(1, b=2)` as different keys, a known limitation worth mentioning in an interview."""),
    fix("Read the code: a router with two bugs", "hard", tag="GenAI",
        prompt="""A minimal HTTP-style router for an LLM service. Routes are registered from a table in a loop, and each handler
        should receive the request's query parameters as keyword arguments. Every route answers as the last one, and handlers
        crash on their arguments. Read the module, find both bugs, and fix them.""",
        code="""
        def summarise(text, max_words=20):
            return " ".join(text.split()[:max_words])

        def translate(text, target="fr"):
            return f"[{target}] {text}"

        ROUTE_TABLE = [("/summarise", summarise), ("/translate", translate)]


        def build_router():
            routes = {}
            for path, fn in ROUTE_TABLE:
                routes[path] = lambda params: fn(params)
            return routes


        def handle(routes, path, params):
            handler = routes.get(path)
            if handler is None:
                return {"status": 404}
            return {"status": 200, "body": handler(params)}
        """,
        tests="""
        r = build_router()
        assert handle(r, "/summarise", {"text": "one two three four", "max_words": 2}) == {"status": 200, "body": "one two"}
        assert handle(r, "/translate", {"text": "hello"}) == {"status": 200, "body": "[fr] hello"}
        assert handle(r, "/translate", {"text": "hi", "target": "de"})["body"] == "[de] hi"
        assert handle(r, "/missing", {}) == {"status": 404}
        """,
        hints=["Which `fn` does each lambda call when a request arrives, long after the loop ended?",
               "`fn(params)` passes the whole dict as one positional argument. How do you spread it into keyword arguments?"],
        solution="""
        def summarise(text, max_words=20):
            return " ".join(text.split()[:max_words])

        def translate(text, target="fr"):
            return f"[{target}] {text}"

        ROUTE_TABLE = [("/summarise", summarise), ("/translate", translate)]


        def make_handler(fn):
            def handler(params):
                return fn(**params)
            return handler


        def build_router():
            return {path: make_handler(fn) for path, fn in ROUTE_TABLE}


        def handle(routes, path, params):
            handler = routes.get(path)
            if handler is None:
                return {"status": 404}
            return {"status": 200, "body": handler(params)}
        """,
        why="""Bug one is late binding (3.4): every lambda reads the loop variable `fn` when a request arrives, and by then it is
        `translate`, so `/summarise` runs `translate`. A factory captures each function per pass (storing `fn` directly,
        `routes[path] = fn`, would also work here, but the factory keeps the place to add per-route logic). Bug two is
        argument passing (3.2): `fn(params)` hands the dict to the first parameter, `text`; `fn(**params)` spreads it into
        keyword arguments, so `max_words` and `target` arrive by name and defaults apply when they are missing. FastAPI's router
        does this mapping for you, from the function's signature (3.1)."""),
    explain("Walk through exactly what happens when Python runs a `def` statement, and later calls the function.", "medium", tag="Interview",
        why="""Running `def`: Python evaluates the default values once, builds a function object that holds the already-compiled
        code, the defaults, the docstring and a reference to the module's globals (plus cells for any enclosing variables it
        uses), and binds the function's name to it. The body does not run. Calling it: Python creates a new frame with a fresh
        local scope, binds the arguments to the parameters (positional, then keywords, then defaults, collecting extras into
        `*args`/`**kwargs`, raising `TypeError` for mismatches), runs the body, resolving names with LEGB (with local names fixed
        at compile time), and returns the value of the `return` expression or `None`. The frame is discarded, except for any
        cells kept alive by closures created during the call."""),
    explain("Design a plugin system where users register their own Python functions. What features do you use, and what pitfalls do you guard against?", "hard", tag="Interview",
        why="""Use a registry dict from name to function (functions as values), a `register` function (or decorator) that
        validates names and rejects duplicates, and `inspect.signature` to describe each plugin's parameters and check calls
        before running them. Call plugins with keyword arguments built from validated input. Keep options keyword-only. Keep
        the registry inside an object or closure rather than a module global, so tests and tenants can have separate registries.
        Pitfalls: late binding when registering plugins in a loop (use factories or `partial`); plugins that change their
        arguments (pass copies or validated objects, 2.4); plugins with mutable defaults or module state that leak between
        calls; unbounded execution (timeouts, rate limits); and security, since a plugin is arbitrary code: only load trusted
        plugins, and never `eval` strings to build them."""),
)

section("project", "Mini project: a tool runtime for an agent",
    fig(chain(["model asks for a tool|name + JSON arguments", "look it up in|the registry dict", "bind and validate|the arguments", ("call it, return the|result or the error", "good")]),
        "The tool runtime: every piece is a function value, found by name and called with checked arguments."),
    p("""An agent receives tool calls from an LLM as `{"name": ..., "arguments": {...}}`. Build the small runtime that
    registers tools, describes them, executes calls safely and tracks usage. Every rule below comes from this module, and
    the tests check each one."""),
    write("An agent tool runtime", "hard", key="tool-runtime", tag="Project",
        prompt="""Implement `make_runtime(max_calls_per_tool=None)` returning a tuple `(register, describe, call, usage)`,
        all sharing one private registry (no module-level state):

        **1. `register(fn, /, *, name=None)`**: register `fn` under `name`, or under `fn.__name__` when `name` is `None`. A name
        that is already taken raises `ValueError`. Return the name.

        **2. `describe()`**: a list of dicts sorted by name, each `{"name": ..., "params": [...], "required": [...]}` listing
        the parameter names in order and the ones without a default. Leave out `*args` and `**kwargs` parameters.

        **3. `call(name, arguments)`**: return `{"ok": True, "result": ...}` on success. Return `{"ok": False, "error": ...}`
        (never raise) when the tool is unknown, when a required argument is missing, or when the tool has reached
        `max_calls_per_tool`. Unknown argument keys are dropped, unless the tool accepts `**kwargs`. A refused call does not
        count as usage.

        **4. `usage()`**: a list of `(name, count)` pairs for tools called at least once, most used first, ties by name.

        Also write **`make_template_tools(templates)`**: for a dict from name to template string (with a `{text}` field), return
        a list of `(name, function)` pairs where each function takes `text` and fills **its own** template.""",
        code="""
        import inspect


        def make_runtime(max_calls_per_tool=None):
            pass


        def make_template_tools(templates):
            pass
        """,
        tests="""
        register, describe, call, usage = make_runtime(max_calls_per_tool=2)

        def search(query, k=3, *, rerank=False):
            return f"{k} hits for {query!r}" + (" (reranked)" if rerank else "")

        def log_event(event, **fields):
            return f"{event}: {sorted(fields)}"

        assert register(search) == "search"
        assert register(log_event, name="log") == "log"
        def raises(exc, f, *args, **kw):
            try:
                f(*args, **kw)
            except exc:
                return True
            return False
        assert raises(ValueError, register, search)
        assert describe() == [
            {"name": "log", "params": ["event"], "required": ["event"]},
            {"name": "search", "params": ["query", "k", "rerank"], "required": ["query"]},
        ]
        assert call("search", {"query": "refunds", "reason": "user asked"}) == {"ok": True, "result": "3 hits for 'refunds'"}
        assert call("search", {"query": "refunds", "k": 5, "rerank": True})["result"] == "5 hits for 'refunds' (reranked)"
        third = call("search", {"query": "again"})
        assert third["ok"] is False and "limit" in third["error"]
        assert call("log", {"event": "start", "user": "ana", "step": 1}) == {"ok": True, "result": "start: ['step', 'user']"}
        missing = call("log", {"user": "ana"})
        assert missing["ok"] is False and "event" in missing["error"]
        assert call("nope", {})["ok"] is False
        assert usage() == [("search", 2), ("log", 1)]

        r2, d2, c2, u2 = make_runtime()
        assert d2() == [] and u2() == []
        for name, fn in make_template_tools({"shout": "{text}!!", "quote": '"{text}"'}):
            r2(fn, name=name)
        assert c2("shout", {"text": "hi"})["result"] == "hi!!"
        assert c2("quote", {"text": "hi"})["result"] == '"hi"'
        assert [c2("shout", {"text": str(i)})["ok"] for i in range(5)] == [True] * 5
        """,
        hints=["Keep `tools = {}` and `counts = {}` inside `make_runtime`; the four inner functions close over them (3.4).",
               "For `describe` and `call`, read `inspect.signature(fn).parameters`. A parameter is required when `p.default is inspect.Parameter.empty`; skip kinds `VAR_POSITIONAL` and `VAR_KEYWORD` (3.1, problem 15).",
               "In `call`, check (in this order) unknown tool, limit, then filter arguments, then missing required names, then call with `fn(**kept)`, and only then count it.",
               "`usage`: `sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))` (3.5). `make_template_tools`: a factory per template, never a lambda reading the loop variable."],
        solution="""
        import inspect

        VAR_KINDS = (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)


        def make_runtime(max_calls_per_tool=None):
            tools = {}
            counts = {}

            def register(fn, /, *, name=None):
                name = fn.__name__ if name is None else name
                if name in tools:
                    raise ValueError(f"tool {name!r} already registered")
                tools[name] = fn
                return name

            def describe():
                out = []
                for name in sorted(tools):
                    params = inspect.signature(tools[name]).parameters.values()
                    named = [p for p in params if p.kind not in VAR_KINDS]
                    out.append({
                        "name": name,
                        "params": [p.name for p in named],
                        "required": [p.name for p in named if p.default is inspect.Parameter.empty],
                    })
                return out

            def call(name, arguments):
                fn = tools.get(name)
                if fn is None:
                    return {"ok": False, "error": f"unknown tool {name!r}"}
                if max_calls_per_tool is not None and counts.get(name, 0) >= max_calls_per_tool:
                    return {"ok": False, "error": f"call limit reached for {name!r}"}
                params = inspect.signature(fn).parameters
                takes_any = any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values())
                kept = arguments if takes_any else {k: v for k, v in arguments.items() if k in params}
                missing = [p.name for p in params.values()
                           if p.kind not in VAR_KINDS and p.default is inspect.Parameter.empty and p.name not in kept]
                if missing:
                    return {"ok": False, "error": f"missing arguments: {missing}"}
                result = fn(**kept)
                counts[name] = counts.get(name, 0) + 1
                return {"ok": True, "result": result}

            def usage():
                return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))

            return register, describe, call, usage


        def make_template_tools(templates):
            def make_tool(template):
                def tool(text):
                    return template.format(text=text)
                return tool
            return [(name, make_tool(template)) for name, template in templates.items()]
        """,
        why="""Each part uses a different tool from the module:

        - **Closures (3.4):** `tools` and `counts` live in one `make_runtime` call, so two runtimes never share tools or usage,
          and no module state exists (3.3). Both dicts are changed in place, so no `nonlocal` is needed.
        - **Parameter kinds (3.2):** `register(fn, /, *, name=None)` keeps `fn` positional-only and `name` keyword-only, so a
          registration reads clearly and cannot be confused.
        - **Signatures (3.1):** `describe` and `call` read `inspect.signature`, which is how real agent frameworks generate a
          tool schema for the LLM and validate calls. Checking required arguments **before** calling turns a crash inside the
          tool into a structured error the model can react to.
        - **Functions as values (3.5):** the registry is a dispatch table, `usage` sorts with a tuple key, and
          `make_template_tools` uses a factory so each tool keeps its own template, avoiding the late-binding trap (3.4).

        A refused call is not counted, so a broken call cannot burn the limit. A production runtime would also validate
        argument **types** from the annotations (Pydantic, Module 11), put timeouts on tool calls, run them concurrently
        (Module 14), and log every call for tracing."""),
)

recap(
    "A call fills parameters by position, then name, then defaults; `*` and `/` control which are allowed. Read `TypeError` messages word by word.",
    "Any assignment makes a name local to the whole function; change outer objects in place, or use `nonlocal` / `global` deliberately.",
    "Closures keep their outer variables in cells and read them at call time. Capture loop values with a factory or `partial`.",
    "Functions are values: key functions, dispatch tables and higher-order helpers keep code short and extensible.",
    "Read signatures with `inspect` to describe and validate calls, the same way FastAPI and agent frameworks do.",
)
