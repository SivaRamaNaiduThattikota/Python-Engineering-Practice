from lesson import *

lesson(
    id="m3-4", num="3.4", title="Closures and late binding",
    intro="A function defined inside another function can keep using the outer function's variables after the outer "
          "function has returned. How that works (cells), what it is good for (factories, callbacks, small caches), and "
          "the late-binding trap that breaks closures built in loops.",
    desc="Functions that remember values, factories, and the loop-variable trap.",
    keys="closure free variable cell __closure__ cell_contents factory late binding loop variable lambda default argument nonlocal state memoize callback partial",
)

term("Closure", "A function together with the outer variables it uses. Those variables stay alive as long as the function does.")
term("Free variable", "A name a function reads that is neither its own local nor a global, but a local of an enclosing function.")
term("Cell", "The small box Python uses to share an enclosing variable between the outer function and the inner functions that use it.")
term("Late binding", "A closure looks up an outer variable's value when it runs, not when it was created.")
term("Factory function", "A function whose job is to build and return another function, configured by the factory's arguments.")

CELL_FIG = """
<svg viewBox="0 0 640 150" role="img" aria-label="make_scaler(3) creates a cell holding factor 3. The returned function scale points at the cell, so the value stays alive after make_scaler returns.">
  <defs><marker id="k1" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M0 0 L10 5 L0 10 z" style="fill:var(--label2)"/></marker></defs>
  <rect x="10" y="20" width="220" height="110" rx="14" class="box"/>
  <text x="120" y="42" class="h mid">call make_scaler(3)</text>
  <text x="120" y="66" class="mid">frame: finished and gone</text>
  <rect x="270" y="50" width="120" height="44" rx="12" class="box a"/><text x="330" y="77" class="w mid">cell: factor = 3</text>
  <rect x="450" y="40" width="170" height="64" rx="12" class="box b"/>
  <text x="535" y="66" class="w mid">scale (returned)</text><text x="535" y="86" class="w mid">__closure__ points at the cell</text>
  <path d="M230 72 L266 72" style="stroke:var(--label2);stroke-width:2;fill:none;stroke-dasharray:4 3" marker-end="url(#k1)"/>
  <path d="M450 72 L394 72" style="stroke:var(--label2);stroke-width:2;fill:none" marker-end="url(#k1)"/>
  <text x="330" y="124" class="mid">kept alive by the closure</text>
</svg>"""

section("what", "What a closure is",
    p("""When a function is defined **inside** another function and uses one of the outer function's local variables,
    the inner function remembers that variable even after the outer function has returned. The inner function together
    with the outer variables it uses is called a **closure**, and those variables are its **free variables** (not its own
    locals, not globals)."""),
    ex("""
    def make_scaler(factor):
        def scale(x):
            return x * factor        # factor is a free variable of scale
        return scale

    triple = make_scaler(3)
    halve = make_scaler(0.5)
    print(triple(10), halve(10))
    print(triple.__code__.co_freevars, triple.__closure__[0].cell_contents)
    """, "closure_basics.py"),
    p("""Step by step, here is what Python does. When it **compiles** `make_scaler`, it notices that `factor` is used by
    the inner function, so instead of an ordinary local slot it stores `factor` in a **cell**, a tiny shared box. When
    `make_scaler(3)` **runs**, it creates a new cell holding 3, then the `def scale` statement builds a new function
    object whose `__closure__` points at that cell. `make_scaler` returns and its frame disappears, but the cell survives
    because `scale` still refers to it. Calling `triple(10)` reads `factor` through the cell. `make_scaler(0.5)` is a
    separate call, so it creates a separate cell: `triple` and `halve` do not interfere."""),
    fig(CELL_FIG, "The outer call ends, but the cell holding `factor` stays alive as long as the returned function exists."),
    callout("sql", "SQL / Power BI", """A closure is like a parameterised query or a Power BI what-if parameter baked into a
    measure: `make_scaler(3)` returns "the measure, with 3 plugged in". Each call of the factory gives a separately
    configured measure, and each one keeps its own setting.""")
)

section("uses", "What closures are good for",
    p("""Closures let you **configure a function once and call it many times**, without a class and without globals.
    Four patterns cover most real uses:"""),
    p("""- **Factories:** functions that build configured functions, such as `make_scaler(3)` above, a tokenizer with fixed
      settings, or a validator for one schema.
    - **Callbacks:** functions you hand to other code (`sorted(key=...)`, a button handler, an early-stopping hook), which
      need some context when they are called later.
    - **Private state:** a counter, a running total or a small cache that only the returned functions can see, updated with
      `nonlocal` (3.3).
    - **Wrappers:** functions that wrap another function to add retries, logging or timing. That is exactly a decorator
      (Module 7)."""),
    ex("""
    def make_validator(required, max_len):
        def validate(record):
            missing = [k for k in required if record.get(k) is None]
            too_long = [k for k, v in record.items() if isinstance(v, str) and len(v) > max_len]
            return {"missing": missing, "too_long": too_long}
        return validate

    check_ticket = make_validator(required=["title", "priority"], max_len=20)
    print(check_ticket({"title": "Refund not received after 14 days", "priority": None}))
    print(check_ticket({"title": "Login", "priority": 2}))
    """, "factory.py"),
    p("""Compare that with the alternatives. Passing `required` and `max_len` on every call clutters every call site.
    Globals would make all validators share one setting (3.3). A class works too, and is the better choice once you need
    several methods or want the state to be visible and inspectable (Module 9). A closure is the lightest tool when the
    whole object is "one function plus a few settings"."""),
)

section("late", "Late binding: closures read the variable, not the value",
    p("""A closure stores the **variable** (the cell), not a copy of its value at the moment the inner function was
    created. It reads the current value **when it runs**. Usually that is what you want. It becomes a trap when closures are
    created in a loop: every closure shares the **same** loop variable, and by the time they run, the loop has finished and
    the variable holds its last value."""),
    ex("""
    handlers = []
    for name in ["search", "summarise", "translate"]:
        def handler():
            return f"running {name}"
        handlers.append(handler)

    print([h() for h in handlers])          # every handler sees the final name
    print(handlers[0].__closure__ is None)  # module-level loop: name is a global here
    """, "late_binding.py"),
    p("""Here the loop runs at module level, so `name` is a global and the functions simply read it when called. Inside a
    function the mechanism is a shared cell, but the effect is identical. There are two standard fixes, and both work by
    capturing the **value** at creation time instead of the variable:"""),
    ex("""
    fixed_default = []
    for name in ["search", "summarise", "translate"]:
        def handler(name=name):              # default evaluated now, once per pass (2.4)
            return f"running {name}"
        fixed_default.append(handler)
    print([h() for h in fixed_default])

    def make_handler(name):                  # a factory: each call gets its own cell
        def handler():
            return f"running {name}"
        return handler
    fixed_factory = [make_handler(n) for n in ["search", "summarise", "translate"]]
    print([h() for h in fixed_factory])
    """, "late_binding_fixes.py"),
    p("""The default-argument trick is short but leaves an extra parameter that a caller could pass by mistake. The factory
    is clearer and is what you should write in code others will read. `functools.partial(fn, value)` is a third option
    (lesson 3.5). The same trap appears with `lambda` in a comprehension, `[lambda: i for i in range(3)]`, in GUI and web
    callbacks registered in a loop, and in LLM tool registries built from a list of tool names (problem 4)."""),
)

section("state", "Closures with state, and what they keep alive",
    p("""Reading a free variable needs nothing special. **Rebinding** it needs `nonlocal`, because an assignment would
    otherwise make a new local (3.3). Changing a mutable object held in a free variable (a dict used as a cache) needs no
    declaration. Each call of the outer function creates fresh cells, so every closure made this way has private,
    independent state:"""),
    ex("""
    def make_cache(fn, max_items=2):
        store = {}
        hits = 0

        def cached(key):
            nonlocal hits
            if key in store:
                hits += 1
                return store[key]
            if len(store) >= max_items:
                store.pop(next(iter(store)))      # evict the oldest entry
            store[key] = fn(key)
            return store[key]

        def stats():
            return {"size": len(store), "hits": hits}

        return cached, stats

    embed, stats = make_cache(lambda text: len(text))
    for t in ["a", "bb", "a", "ccc", "a"]:
        embed(t)
    print(stats())
    """, "stateful_closure.py"),
    p("""Two things to keep in mind. First, a closure keeps **everything it closes over** alive for as long as the closure
    exists. A callback that closes over a big DataFrame or a loaded model keeps that object in memory until the callback is
    gone, a common memory leak in long-running services. Second, closure state is invisible from outside: you cannot
    inspect `store` without a helper like `stats`. When the state grows important enough that you want to look at it, test
    it or save it, move it into a class (Module 9) or a dataclass."""),
)

section("warmup", "Warm-up",
    predict("Two configured functions", "easy",
        code="""
        def make_prefixer(prefix):
            def add(text):
                return f"{prefix}: {text}"
            return add

        q = make_prefixer("Question")
        a = make_prefixer("Answer")
        print(q("refunds?"), "|", a("5 days"))
        print(q.__closure__[0].cell_contents, a.__closure__[0].cell_contents)
        print(q is a, q.__code__ is a.__code__)
        """,
        hints=["Each factory call builds a new function object with its own cell. Do they share the compiled code?"],
        why="""Each call of `make_prefixer` creates a new cell for `prefix` and a new function object pointing at it, so `q` and
        `a` are different functions with different settings. Their **code** is the same object: Python compiled the body once,
        and each function object pairs that one code object with its own cells. That is why closures are cheap to create."""),
    write("A threshold classifier factory", "easy", tag="ML",
        prompt="""Write `make_classifier(threshold, positive="yes", negative="no")` that returns a function `classify(score)`
        giving `positive` when `score >= threshold`, otherwise `negative`.""",
        code="""
        def make_classifier(threshold, positive="yes", negative="no"):
            pass
        """,
        tests="""
        spam = make_classifier(0.8, "spam", "ham")
        loose = make_classifier(0.3)
        assert [spam(s) for s in [0.9, 0.5]] == ["spam", "ham"]
        assert [loose(s) for s in [0.9, 0.5, 0.1]] == ["yes", "yes", "no"]
        assert spam(0.8) == "spam"
        """,
        hints=["Define `classify` inside, using `threshold`, `positive` and `negative` from the outer call, and return it."],
        solution="""
        def make_classifier(threshold, positive="yes", negative="no"):
            def classify(score):
                return positive if score >= threshold else negative
            return classify
        """,
        why="""All three settings become free variables of `classify`, held in cells for that one factory call. Two classifiers
        with different thresholds never interfere, which is exactly what you want when comparing operating points of a model
        (for example a strict and a lenient threshold on the same scores)."""),
    predict("Callbacks made in a loop", "easy",
        code="""
        def build():
            callbacks = []
            for step in [1, 2, 3]:
                callbacks.append(lambda: step * 10)
            return callbacks

        print([cb() for cb in build()])

        def build_fixed():
            return [lambda step=step: step * 10 for step in [1, 2, 3]]

        print([cb() for cb in build_fixed()])
        """,
        hints=["Inside `build`, how many `step` variables are there? When does each lambda read it?"],
        why="""All three lambdas in `build` close over the **one** `step` variable of that call, and they read it after the loop
        has finished, when it is 3. The default argument in `build_fixed` is evaluated as each lambda is created, so each one
        keeps its own value."""),
    fix("Handlers that all run the last tool", "easy", tag="GenAI",
        prompt="""An agent registers one handler per tool name. Every handler runs the last tool. Fix `register` with a
        factory function so each handler keeps its own tool name.""",
        code="""
        def run_tool(name, query):
            return f"{name}({query})"

        def register(tool_names):
            handlers = {}
            for name in tool_names:
                handlers[name] = lambda query: run_tool(name, query)
            return handlers
        """,
        tests="""
        h = register(["search", "calculator", "weather"])
        assert h["search"]("refunds") == "search(refunds)"
        assert h["calculator"]("2+2") == "calculator(2+2)"
        assert h["weather"]("Oslo") == "weather(Oslo)"
        """,
        hints=["Write `make_handler(name)` that returns the handler, and call it inside the loop."],
        solution="""
        def run_tool(name, query):
            return f"{name}({query})"

        def make_handler(name):
            def handler(query):
                return run_tool(name, query)
            return handler

        def register(tool_names):
            return {name: make_handler(name) for name in tool_names}
        """,
        why="""The lambdas all close over the single loop variable `name` of the `register` call, which ends as `"weather"`. Each
        `make_handler(name)` call creates a new cell holding the value for that pass, so each handler is bound to its own tool.
        The dict keys were right all along, which makes this bug easy to miss in a quick test: `h["weather"]` works perfectly,
        and only the other tools are wrong."""),
)

section("medium", "Medium",
    write("Late binding, on purpose", "medium", tag="GenAI",
        prompt="""Sometimes late binding is exactly what you want. Write `make_prompt_builder()` that returns
        `(set_style, build)`: `set_style(style)` changes a shared setting, and `build(question)` returns
        `f"[{style}] {question}"` using whatever style is current **when `build` is called**. The default style is `"brief"`.""",
        code="""
        def make_prompt_builder():
            pass
        """,
        tests="""
        set_style, build = make_prompt_builder()
        assert build("refunds?") == "[brief] refunds?"
        set_style("formal")
        assert build("refunds?") == "[formal] refunds?"
        other_set, other_build = make_prompt_builder()
        assert other_build("x") == "[brief] x"
        """,
        hints=["Keep `style = \"brief\"` in the outer function. `set_style` rebinds it, so it needs `nonlocal`."],
        solution="""
        def make_prompt_builder():
            style = "brief"

            def set_style(new_style):
                nonlocal style
                style = new_style

            def build(question):
                return f"[{style}] {question}"

            return set_style, build
        """,
        why="""Both inner functions share one cell for `style`. `set_style` rebinds it through `nonlocal`, and `build` reads it at
        call time, so it always sees the latest value: that is late binding working for you. A second builder is a separate
        factory call with its own cell, so it is unaffected. This is the same mechanism as the loop trap; the difference is
        only whether "read the current value" is what you meant."""),
    trace("Two closures sharing one cell", "medium",
        prompt="Fill in what `get()` and `get2()` would return after each marked line. `inc` and `get` share one factory call.",
        code="""
        def make_counter(start):
            n = start
            def inc(by=1):
                nonlocal n
                n += by
                return n
            def get():
                return n
            return inc, get

        inc, get = make_counter(10)
        inc2, get2 = make_counter(0)
        inc()  # row: "inc()"
        inc(5)  # row: "inc(5)"
        inc2()  # row: "inc2()"
        inc(-6)  # row: "inc(-6)"
        """,
        trace_vars=["get()", "get2()"],
        hints=["`inc` and `get` share the cell from the first factory call; `inc2` has its own."],
        why="""`inc()` makes the shared `n` 11 and `inc(5)` makes it 16, and `get()` reads that same cell, so it shows each new
        value. `inc2` belongs to a different call of `make_counter`, with its own cell starting at 0, so `inc2()` moves only
        `get2()` to 1. `inc(-6)` brings the first counter back to 10. Two closures from one factory call share state; two
        factory calls never do."""),
    write("Rate-limit any function", "medium", tag="GenAI",
        prompt="""Write `make_limited(fn, max_calls)` that returns a function `limited(*args, **kwargs)` which forwards to
        `fn` for the first `max_calls` calls and then raises `RuntimeError("rate limit reached")` without calling `fn`.
        Each `make_limited` call has its own budget.""",
        code="""
        def make_limited(fn, max_calls):
            pass
        """,
        tests="""
        def raises(exc, f, *args):
            try:
                f(*args)
            except exc:
                return True
            return False
        calls = []
        def complete(prompt, *, model="small"):
            calls.append(prompt)
            return f"{model}:{prompt}"
        lim = make_limited(complete, 2)
        assert lim("a") == "small:a" and lim("b", model="large") == "large:b"
        assert raises(RuntimeError, lim, "c")
        assert calls == ["a", "b"]
        other = make_limited(complete, 1)
        assert other("d") == "small:d"
        """,
        hints=["Keep `used = 0` in the factory and use `nonlocal used` inside `limited`. Check the budget before calling `fn`."],
        solution="""
        def make_limited(fn, max_calls):
            used = 0

            def limited(*args, **kwargs):
                nonlocal used
                if used >= max_calls:
                    raise RuntimeError("rate limit reached")
                used += 1
                return fn(*args, **kwargs)

            return limited
        """,
        why="""The closure combines three earlier ideas: a free variable with `nonlocal` for the budget (3.3), forwarding with
        `*args, **kwargs` (3.2), and a factory so each limiter is independent. Checking the budget **before** calling means a
        refused call costs nothing, which matters when each call is a paid API request. Real rate limiters count calls per time
        window (a token bucket) instead of a fixed total, but they keep their state in exactly this kind of closure or a small
        class."""),
    predict("What a closure keeps alive", "medium",
        code="""
        def make_summary(rows):
            total = sum(r["amount"] for r in rows)
            def report():
                return f"{len(rows)} rows, total {total}"
            return report

        data = [{"amount": 5}, {"amount": 7}]
        report = make_summary(data)
        data.append({"amount": 100})
        print(report())
        print(report.__code__.co_freevars)
        data = None
        print(report())
        """,
        hints=["Which free variables does `report` close over, and which of them point at objects that can change?"],
        why="""`report` closes over `rows` and `total`. `total` is an int computed once, but `rows` is the caller's list itself, so
        appending to `data` changes what `len(rows)` reports: the text says 3 rows but the total still covers only 2, a subtle
        inconsistency. Setting `data = None` only moves the caller's name; the list stays alive because the closure still
        refers to it. A closure that captures a large mutable object (a DataFrame, a list of documents) both sees later
        changes and keeps the object in memory as long as the closure exists."""),
    choose("Closure or class for a configured function", "medium",
        prompt="Both build a configured scorer once and call it a million times. Which runs the calls faster?",
        setup="""def make_scorer(w, b):
    def score(x):
        return w * x + b
    return score

class Scorer:
    def __init__(self, w, b):
        self.w, self.b = w, b
    def __call__(self, x):
        return self.w * x + self.b

xs = list(range(1_000_000))
closure = make_scorer(2, 1)
obj = Scorer(2, 1)""",
        options={
            "a": "r = [closure(x) for x in xs]",
            "b": "r = [obj(x) for x in xs]",
        },
        answer="a",
        hints=["Reading a free variable goes through a cell. Reading `self.w` goes through an attribute lookup. Calling an object goes through `__call__`."],
        why="""The closure reads `w` and `b` straight from its cells and is called as a plain function. The class instance has to
        go through `__call__` and then look up `self.w` and `self.b` as attributes on every call. Both are fine for most code,
        and the class is easier to inspect and extend; the point is that closures are not a slow or exotic choice. For real
        numeric work, a vectorised numpy expression (`2 * arr + 1`) beats both by far."""),
    fix("A memoiser that remembers the wrong thing", "medium", tag="ML",
        prompt="""`memoize` should cache results per argument value, so expensive feature computations run once per input.
        Instead every call after the first returns the first result. Fix it.""",
        code="""
        def memoize(fn):
            result = None
            def cached(x):
                nonlocal result
                if result is None:
                    result = fn(x)
                return result
            return cached
        """,
        tests="""
        calls = []
        def slow_square(x):
            calls.append(x)
            return x * x
        sq = memoize(slow_square)
        assert [sq(2), sq(3), sq(2), sq(3)] == [4, 9, 4, 9]
        assert calls == [2, 3]
        assert memoize(lambda x: None)(1) is None
        """,
        hints=["One `result` variable can only remember one result. What structure can remember one result per argument?",
               "The last test caches a function that returns `None`. Can `None` still mean \"not computed yet\"?"],
        solution="""
        def memoize(fn):
            cache = {}
            def cached(x):
                if x not in cache:
                    cache[x] = fn(x)
                return cache[x]
            return cached
        """,
        why="""The original stores one value and uses `None` as "empty", so it returns the first result forever, and it would
        call `fn` again and again for a function that returns `None`. A dict keyed by the argument stores one result per input,
        and `x not in cache` distinguishes "never computed" from "computed and was None". Because the dict is changed in place,
        no `nonlocal` is needed. The standard library version is `functools.cache` (or `lru_cache` with a size limit), which
        you will apply as a decorator in Module 7."""),
)

section("hard", "Hard",
    predict("Late binding inside a function", "hard",
        code="""
        def make_multipliers():
            fns = []
            for k in range(3):
                fns.append(lambda x: x * k)
            k = 10
            return fns

        fns = make_multipliers()
        print([f(1) for f in fns])
        print(fns[0].__closure__[0].cell_contents)
        print(fns[0].__closure__[0] is fns[2].__closure__[0])
        """,
        hints=["How many cells for `k` does one call of `make_multipliers` create?",
               "What is the last value assigned to `k` before the function returns?"],
        why="""One call of `make_multipliers` has exactly one cell for `k`, shared by all three lambdas. The loop assigns 0, 1, 2
        into that cell, and then `k = 10` assigns again, after the loop. When the lambdas finally run, they all read 10. The
        identity check confirms there is a single shared cell. Late binding means "the last value assigned before the call",
        not "the last value of the loop"."""),
    fix("Read the code: an event system with two closure bugs", "hard", tag="GenAI",
        prompt="""This small event bus lets an agent subscribe handlers to events such as `"tool_start"`. Two things are
        broken: handlers subscribed in the setup loop all report the last event name, and `make_bus()` called twice gives
        two buses that share their subscriptions. Read the whole module, find both bugs, and fix them.""",
        code="""
        _handlers = {}


        def make_bus():
            def subscribe(event, fn):
                _handlers.setdefault(event, []).append(fn)

            def emit(event, payload):
                return [fn(payload) for fn in _handlers.get(event, [])]

            return subscribe, emit


        def setup_logging(subscribe, events, log):
            for event in events:
                subscribe(event, lambda payload: log.append(f"{event}: {payload}"))
        """,
        tests="""
        sub_a, emit_a = make_bus()
        sub_b, emit_b = make_bus()
        log_a = []
        setup_logging(sub_a, ["tool_start", "tool_end"], log_a)
        emit_a("tool_start", "search")
        emit_a("tool_end", "search")
        assert log_a == ["tool_start: search", "tool_end: search"]
        assert emit_b("tool_start", "x") == []
        sub_b("tool_start", lambda p: p.upper())
        assert emit_b("tool_start", "x") == ["X"]
        assert len(emit_a("tool_start", "y")) == 1
        """,
        hints=["Where does `_handlers` live? Should each bus have its own?",
               "In `setup_logging`, which variable do the lambdas read when they run? Bind its value per pass."],
        solution="""
        def make_bus():
            handlers = {}

            def subscribe(event, fn):
                handlers.setdefault(event, []).append(fn)

            def emit(event, payload):
                return [fn(payload) for fn in handlers.get(event, [])]

            return subscribe, emit


        def make_logger(event, log):
            def handler(payload):
                log.append(f"{event}: {payload}")
            return handler


        def setup_logging(subscribe, events, log):
            for event in events:
                subscribe(event, make_logger(event, log))
        """,
        why="""Bug one is about **where** the state lives: `_handlers` is a module global, so every bus shares it, and `emit_b` sees
        the handlers subscribed on bus A. Moving the dict inside `make_bus` gives each call its own `handlers`, closed over by
        that bus's `subscribe` and `emit`. Bug two is late binding: every logging lambda reads the loop variable `event` when an
        event is emitted, long after the loop finished, so both log lines would say `tool_end`. A factory, `make_logger(event,
        log)`, captures the value per pass. Event buses, middleware chains and agent callback systems are built from closures
        like these, so both bugs show up in real frameworks."""),
    write("Retry with backoff, configured once", "hard", tag="GenAI",
        prompt="""Write `make_retrying(attempts, delays, sleep)` that returns a function `run(fn, *args, **kwargs)`. `run`
        calls `fn`, and on a `ConnectionError` waits `delays[i]` seconds (by calling the given `sleep` function) before the
        next attempt, up to `attempts` attempts in total. It returns the result, or re-raises the last error. It also records
        every wait in a list that `run.waits` exposes. Taking `sleep` as a parameter lets tests run instantly.""",
        code="""
        def make_retrying(attempts, delays, sleep):
            pass
        """,
        tests="""
        def raises(exc, f, *args):
            try:
                f(*args)
            except exc:
                return True
            return False
        slept = []
        run = make_retrying(3, [0.5, 1.0], slept.append)
        state = {"left": 2}
        def flaky(q):
            if state["left"]:
                state["left"] -= 1
                raise ConnectionError("reset")
            return f"ok {q}"
        assert run(flaky, "refunds") == "ok refunds"
        assert slept == [0.5, 1.0] and run.waits == [0.5, 1.0]
        def down(q):
            raise ConnectionError("down")
        assert raises(ConnectionError, run, down, "x")
        assert run.waits == [0.5, 1.0, 0.5, 1.0]
        """,
        hints=["Inside `run`: loop `for i in range(attempts)`; on `ConnectionError`, if this was not the last attempt, `sleep(delays[i])` and record it.",
               "Functions are objects: after defining `run`, set `run.waits = []` and append to it inside `run`."],
        solution="""
        def make_retrying(attempts, delays, sleep):
            def run(fn, *args, **kwargs):
                for i in range(attempts):
                    try:
                        return fn(*args, **kwargs)
                    except ConnectionError:
                        if i == attempts - 1:
                            raise
                        sleep(delays[i])
                        run.waits.append(delays[i])
            run.waits = []
            return run
        """,
        why="""The retry policy (attempts, delays) is configured once in the factory and closed over, so call sites only say
        `run(fn, ...)`. Taking `sleep` as a parameter is **dependency injection**: production passes `time.sleep`, tests pass
        `list.append`, and the logic is identical. A bare `raise` inside `except` re-raises the current error with its original
        traceback. `run.waits` works because a function is an object that can carry attributes (3.1); it is a light alternative
        to returning a second "stats" function. This is the shape of libraries like `tenacity`, written by hand."""),
    predict("Closures over a loop variable, three ways", "hard",
        code="""
        import functools

        def base(name, query):
            return f"{name}:{query}"

        names = ["a", "b"]
        late = [lambda q: base(n, q) for n in names]
        default = [lambda q, n=n: base(n, q) for n in names]
        partial = [functools.partial(base, n) for n in names]

        print([f("x") for f in late])
        print([f("x") for f in default])
        print([f("x") for f in partial])
        print(default[0]("x", "OOPS"))
        """,
        hints=["A comprehension has its own scope, but still only one `n` variable for the whole comprehension.",
               "The default-argument version leaves `n` as a real parameter. What happens if a caller passes it?"],
        why="""The comprehension has one `n` (in its own scope), so the `late` lambdas all read its final value, `"b"`. The
        default argument freezes each value, and `functools.partial` stores the value in a new object, so both give `a:x` and
        `b:x`. The last line shows the weakness of the default trick: `n` is an ordinary parameter, so a caller can override it
        by accident, here with `"OOPS"` landing in `n`. `partial` and factories do not have that hole, which is why they are
        preferred in code others call."""),
)

section("interview", "Interview questions",
    explain("What is a closure in Python, and how does it remember values after the outer function returns?", "medium", tag="Interview",
        why="""A closure is an inner function together with the variables from an enclosing function that it uses (its free
        variables). At compile time Python sees that the inner function uses the outer variable and stores it in a **cell**
        rather than a normal local slot. Each call of the outer function creates new cells, and the inner function object keeps
        references to them in `__closure__`, so the cells (and the objects they hold) survive after the outer frame is gone.
        Reading a free variable needs nothing special; rebinding it needs `nonlocal`. Uses: factories, callbacks with context,
        private state, decorators. Mention the cost: anything a closure captures stays in memory as long as the closure lives."""),
    explain("Why does `[lambda: i for i in range(3)]` give functions that all return 2, and how do you fix it?", "medium", tag="Interview",
        why="""Closures use late binding: each lambda refers to the variable `i`, not to its value at creation time, and all three
        lambdas share the comprehension's single `i`. They run after the comprehension has finished, when `i` is 2. Fixes:
        capture the value at creation with a default argument (`lambda i=i: i`), build each function with a factory
        (`def make(i): return lambda: i`), or use `functools.partial`. Say which you prefer and why: the factory or `partial`,
        because the default-argument trick adds a parameter callers can override. Real-world version: callbacks or tool handlers
        registered in a loop all acting on the last item."""),
    explain("When would you use a closure, and when a class?", "hard", tag="Interview",
        why="""Use a closure when the thing is essentially **one function plus a little configuration or private state**: a
        configured validator, a key function, a counter, a small cache, a decorator. It is concise and fast, and the state is
        truly private. Use a class when there are several operations on the same state, when the state should be inspectable,
        printable, serialisable or testable directly, when you need inheritance or protocols such as `__repr__`, or when other
        people will extend it. A good signal: if you find yourself returning several inner functions or adding attributes to a
        function object, a class (or a dataclass with methods) is probably clearer. Many teams also prefer classes for anything
        long-lived in a service, because closure state is invisible in a debugger and in logs."""),
)

recap(
    "A closure is an inner function plus the outer variables it uses. They live in cells, which survive after the outer call returns.",
    "Each call of the outer function creates new cells, so closures from different calls never share state.",
    "Closures read variables at call time (late binding). Closures built in a loop all share one loop variable: capture the value with a factory, `functools.partial`, or a default argument.",
    "Reading a free variable is free; rebinding needs `nonlocal`; changing a captured mutable object in place needs nothing.",
    "Closures keep alive everything they capture. When the state needs to be inspected or grow, use a class.",
)
