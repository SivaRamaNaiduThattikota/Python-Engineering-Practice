from lesson import *
from diagrams import *

lesson(
    id="m8-2", num="8.2", title="Decorators with arguments",
    intro="`@retry(times=3)` has one more layer than a plain decorator: a factory that takes the settings and returns the "
          "decorator. The three levels step by step, validating settings at import time, decorators that work with and "
          "without parentheses, stacking several decorators and why their order matters, and what settings capture. "
          "Applied to validation, deprecation, rate limiting and fallbacks.",
    desc="Decorator factories, optional arguments, stacking order, and what runs when.",
    keys="decorator factory arguments parameters three levels optional parentheses stacking order bottom up composition validate range deprecated warning rate limit sliding window fallback configuration import time",
)

term("Decorator factory", "A function that takes settings and returns a decorator: `retry(times=3)` returns the decorator that `@` then applies.")
term("Stacking", "Applying several decorators to one function. They are applied bottom-up at definition time, so the top one runs first at call time.")

section("factory", "Three levels: settings, function, call",
    fig(chain([("retry(times=3)|takes the settings", "accent"), "returns decorator(fn)", "returns wrapper(*args)", ("wrapper runs on|every call", "accent2")]),
        "A decorator with arguments has three levels: the settings call, the decorator that receives the function, and the wrapper that runs per call."),
    p("""A plain decorator receives the function and nothing else. Many decorators need **settings**: how many times to retry, which
    range is valid, which role is required. The `@` line can contain any expression that evaluates to a decorator, so the solution is
    a function that takes the settings and **returns** a decorator: a **decorator factory**. `@retry(times=3)` is evaluated in two
    steps: first `retry(times=3)` is **called**, returning a decorator; then that decorator is applied to the function below."""),
    ex("""
    import functools

    def clip(lo, hi):                          # level 1: the settings
        def decorator(func):                   # level 2: the function
            @functools.wraps(func)
            def wrapper(*args, **kwargs):      # level 3: each call
                return max(lo, min(hi, func(*args, **kwargs)))
            return wrapper
        return decorator

    @clip(0.0, 1.0)
    def confidence(raw):
        return raw / 10

    print(confidence(4), confidence(15), confidence(-3))

    def similarity(a, b):
        return a - b
    clipped = clip(-1, 1)(similarity)          # the same thing without @
    print(clipped(5, 1), clipped(0.25, 0))
    """, "three_levels.py"),
    p("""Read it from the outside in. `clip(0.0, 1.0)` runs once, creates a `decorator` function that remembers `lo` and `hi` in its
    closure, and returns it. The `@` then calls `decorator(confidence)`, which creates a `wrapper` that remembers `func`, `lo` and
    `hi`, and binds `confidence` to it. Each call of `confidence` runs only the innermost level. Writing `clip(-1, 1)(similarity)`
    spells out the two calls that `@clip(-1, 1)` performs. Every level is an ordinary closure (3.4); there is no special decorator
    machinery."""),
    p("""Because the settings are fixed when the decorator is applied, which is usually at import time, it is the right moment to
    **validate** them. A factory that checks `if times < 1: raise ValueError(...)` before returning the decorator makes a
    misconfigured function fail as soon as the module is imported, with a clear message, instead of misbehaving on the first call in
    production. Taking settings as **keyword-only** arguments (`def retry(*, times, on)`) makes every decorator line self-describing:
    `@retry(times=3, on=(TimeoutError,))`."""),
    ex("""
    import functools

    def validate_range(**ranges):
        for name, (lo, hi) in ranges.items():          # checked once, at decoration time
            if lo > hi:
                raise ValueError(f"bad range for {name}: {lo} > {hi}")

        def decorator(func):
            @functools.wraps(func)
            def wrapper(**kwargs):
                for name, (lo, hi) in ranges.items():
                    if name in kwargs and not lo <= kwargs[name] <= hi:
                        raise ValueError(f"{name} must be in [{lo}, {hi}], got {kwargs[name]}")
                return func(**kwargs)
            return wrapper
        return decorator

    @validate_range(temperature=(0, 2), top_p=(0, 1))
    def generate(**settings):
        return settings

    print(generate(temperature=0.7, top_p=0.9))
    for bad in [{"temperature": 3}, {"top_p": -0.1}]:
        try:
            generate(**bad)
        except ValueError as e:
            print("ValueError:", e)
    try:
        validate_range(temperature=(2, 0))
    except ValueError as e:
        print("at import:", e)
    """, "validate_settings.py"),
)

section("capture", "What the settings capture",
    p("""The factory's arguments are evaluated **once**, when the `@` line runs, and stored in closures. So `@log(level=LEVEL)` captures
    the value `LEVEL` had at import time; changing the global variable later has no effect on already-decorated functions. That is
    usually what you want for fixed configuration, and occasionally a surprise. When a setting must be read at **call** time (a
    feature flag, a per-request limit), pass something the wrapper can call or look up on each call, such as a function or a config
    object, instead of a plain value."""),
    ex("""
    import functools

    LEVEL = "info"
    LOG = []

    def log(level):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                current = level() if callable(level) else level     # a callable is read on every call
                LOG.append((func.__name__, current))
                return func(*args, **kwargs)
            return wrapper
        return decorator

    @log(LEVEL)
    def fixed():
        return 1

    @log(lambda: LEVEL)
    def dynamic():
        return 2

    fixed(); dynamic()
    LEVEL = "debug"
    fixed(); dynamic()
    print(LOG)
    """, "capture.py"),
    p("""This is also why decorating functions **in a loop** with a factory works as expected, unlike the lambdas in a comprehension of
    6.1. Each call of the factory creates a new closure with its own copy of the setting, so `[clip(0, n)(f) for n in range(3)]`
    gives three functions with three different limits. The late-binding problem only appears when several functions share one
    variable that changes after they were created (problem 16)."""),
)

section("optional", "Decorators that work with and without parentheses",
    p("""With a factory, `@log` (no parentheses) is a bug: Python calls `log(func)`, passing the function as the **settings**, and binds
    the name to the decorator that comes back. The function is then never called; calling it returns a wrapper (problem 3). Some
    libraries let both forms work, `@log` and `@log(level="debug")`, so users do not have to remember. The trick is to make the
    first parameter the optional function, and the settings keyword-only:"""),
    ex("""
    import functools

    def log(func=None, *, level="info"):
        def decorator(f):
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                wrapper.events.append(level)
                return f(*args, **kwargs)
            wrapper.events = []
            return wrapper
        if func is None:            # called with settings: @log(level=...)
            return decorator
        return decorator(func)      # used bare: @log

    @log
    def a():
        return "a"

    @log(level="debug")
    def b():
        return "b"

    print(a(), a.events, b(), b.events, a.__name__, b.__name__)
    """, "optional_parens.py"),
    p("""Used bare, `log` receives the function as `func` and decorates it immediately. Called with keyword settings, `func` is `None`, so
    it returns the decorator, which `@` then applies. The keyword-only marker `*` is what makes this unambiguous: a setting can never
    be passed positionally and mistaken for the function. pytest's `@pytest.fixture` and `@pytest.fixture(scope="module")`, and
    `@dataclass` versus `@dataclass(frozen=True)`, work exactly this way. For your own code, supporting only one form is simpler and
    perfectly fine (problem 14 shows how easily the dual form goes wrong)."""),
)

section("stacking", "Stacking decorators: order matters",
    fig(chain(["@a over @b over def f", "means f = a(b(f))", "a call runs a's wrapper,|then b's, then f", ("results return through|b, then a", "good")]),
        "Stacked decorators apply bottom-up but run top-down: the top decorator's wrapper is the outermost layer."),
    p("""Several decorators can sit on one function. They are **applied from the bottom up**: the one closest to the `def` wraps the
    function first, and the next one wraps that result. So `@a` / `@b` / `def f` means `f = a(b(f))`. At **call** time the order is
    the reverse: the outermost wrapper (`a`) runs first, calls `b`'s wrapper, which calls the original; on the way back, results pass
    through `b` first and `a` last, like layers of an onion."""),
    ex("""
    import functools

    events = []

    def layer(name):
        def decorator(func):
            events.append(f"apply {name}")
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                events.append(f"{name} before")
                result = func(*args, **kwargs)
                events.append(f"{name} after")
                return result
            return wrapper
        return decorator

    @layer("outer")
    @layer("inner")
    def answer():
        events.append("answer runs")
        return 42

    events.append("---")
    answer()
    print(events)
    """, "stacking.py"),
    p("""The order changes behaviour, not just the log. A few combinations that come up in practice:"""),
    p("""- **Timing and retries.** `@timed` above `@retry` measures the whole operation including all attempts and waits, which is what a
      user experiences; below it, it times each attempt separately. Decide which number you want (problem 10).
    - **Caching and everything else.** A cache placed outermost answers repeated calls without running any inner layer: no logging,
      no rate limiting, no retries. Placed innermost, every call still goes through the outer layers, and only the function body is
      skipped (problem 8).
    - **Permission checks and caching.** An authorisation check must run **before** a cache, or a cached result computed for one user
      could be returned to another who is not allowed to see it.
    - **Validation and retries.** Validate outside the retry: retrying a call whose arguments are invalid can only fail again."""),
)

section("shapes", "Other ways to configure a decorator",
    p("""A factory is not the only way to give a decorator settings. `functools.partial` can pre-fill the settings of a function that
    takes them along with the function: `strict = partial(validate, strict=True)`, then `@strict`. Classes can act as decorators
    too, since any callable works after `@`: a class whose `__init__` stores the settings and whose `__call__` method takes the
    function is a factory with named, inspectable state; Module 9 covers `__call__`. And many frameworks hang decorators off an
    object, as in `@app.get("/users")` or `@router.post(...)`: the object (`app`) holds the shared state, here the table of routes,
    and its method is the factory (8.4)."""),
    ex("""
    import functools

    def tag(func=None, **labels):
        if func is None:
            return functools.partial(tag, **labels)    # remember the settings, wait for the function
        func.labels = {**getattr(func, "labels", {}), **labels}
        return func                                    # metadata only: no wrapper at all

    @tag(team="search", cost="low")
    @tag(owner="ana")
    def rerank(docs):
        return sorted(docs)

    print(rerank.labels, rerank(["b", "a"]), rerank.__name__)
    """, "partial_and_metadata.py"),
    p("""`tag` returns the original function after attaching metadata, so stacking two of them merges the labels, and there is no wrapper
    and no call overhead. `functools.partial(tag, **labels)` is the factory: it returns a callable that, when `@` passes it the
    function, calls `tag(func, **labels)`. Attaching metadata this way is how test frameworks mark tests (`@pytest.mark.slow`) and how
    some agent frameworks annotate tools with descriptions."""),
)

section("warmup", "Warm-up",
    predict("When each level runs", "easy",
        code="""
        def deco(label):
            print("factory", label)
            def decorator(func):
                print("decorating", func.__name__)
                def wrapper(*args):
                    print("calling", label)
                    return func(*args)
                return wrapper
            return decorator

        @deco("A")
        def f(x):
            return x + 1

        print("ready")
        print(f(1), f(2))
        """,
        hints=["`deco(\"A\")` is called first; its result decorates `f`. Only the wrapper runs on calls."],
        why="""The `@` line evaluates `deco("A")` (printing "factory A"), then applies the returned decorator to `f` ("decorating f"), all
        before "ready". Each call then runs only the wrapper. In `print(f(1), f(2))`, both calls run before `print` displays anything,
        so the two "calling A" lines come first, then "2 3"."""),
    write("Clamp the result", "easy", tag="ML",
        prompt="""Write a decorator factory `clip(lo, hi)` that clamps the decorated function's numeric result to `[lo, hi]`. Raise
        `ValueError` **when the decorator is created** if `lo > hi`. Use `functools.wraps`.""",
        code="""
        import functools

        def clip(lo, hi):
            pass
        """,
        tests="""
        @clip(0.0, 1.0)
        def prob(logit):
            return logit / 4

        assert [prob(x) for x in (-8, 2, 8)] == [0.0, 0.5, 1.0]
        assert prob.__name__ == "prob"
        try:
            clip(1, 0)
            assert False
        except ValueError:
            pass
        assert clip(-1, 1)(lambda a, b: a * b)(3, 2) == 1
        """,
        hints=["Validate first, then define `decorator(func)` with a `wrapper` inside, and return `decorator`."],
        solution="""
        import functools

        def clip(lo, hi):
            if lo > hi:
                raise ValueError(f"lo ({lo}) must not exceed hi ({hi})")

            def decorator(func):
                @functools.wraps(func)
                def wrapper(*args, **kwargs):
                    return max(lo, min(hi, func(*args, **kwargs)))
                return wrapper
            return decorator
        """,
        why="""The check runs in the factory, so `clip(1, 0)` fails immediately, before any function is decorated: a typo in a decorator line is
        caught at import. `max(lo, min(hi, x))` clamps in one expression. The last test shows that a factory's result is an ordinary
        decorator that can be applied without `@`. Clamping model outputs to a valid range is common when a regression model's
        prediction must be a probability or a score."""),
    fix("A factory used without parentheses", "easy", tag="GenAI",
        prompt="""`retry` is a decorator factory, but `fetch_answer` was decorated with `@retry` instead of `@retry(...)`. Calling it
        returns a function instead of an answer. Fix the decoration so `fetch_answer` retries twice on `TimeoutError`.""",
        code="""
        import functools

        def retry(times=2, on=(TimeoutError,)):
            def decorator(func):
                @functools.wraps(func)
                def wrapper(*args, **kwargs):
                    for attempt in range(1, times + 1):
                        try:
                            return func(*args, **kwargs)
                        except on:
                            if attempt == times:
                                raise
                return wrapper
            return decorator

        state = {"calls": 0}

        @retry
        def fetch_answer(q):
            state["calls"] += 1
            if state["calls"] == 1:
                raise TimeoutError("slow")
            return f"answer to {q}"
        """,
        tests="""
        assert fetch_answer("refund?") == "answer to refund?"
        assert state["calls"] == 2
        assert fetch_answer.__name__ == "fetch_answer"
        """,
        hints=["`@retry` calls `retry(fetch_answer)`, passing the function as `times`. Write `@retry(times=2)` (or `@retry()`)."],
        solution="""
        import functools

        def retry(times=2, on=(TimeoutError,)):
            def decorator(func):
                @functools.wraps(func)
                def wrapper(*args, **kwargs):
                    for attempt in range(1, times + 1):
                        try:
                            return func(*args, **kwargs)
                        except on:
                            if attempt == times:
                                raise
                return wrapper
            return decorator

        state = {"calls": 0}

        @retry(times=2)
        def fetch_answer(q):
            state["calls"] += 1
            if state["calls"] == 1:
                raise TimeoutError("slow")
            return f"answer to {q}"
        """,
        why="""`@retry` without parentheses evaluates to `retry(fetch_answer)`: the function was passed as `times`, and the result, the inner
        `decorator`, was bound to the name `fetch_answer`. Calling it with `"refund?"` treated the string as the function to decorate
        and returned a wrapper; the original never ran. With parentheses, the factory is called with the settings and its decorator is
        applied to the function. Making settings keyword-only (`def retry(*, times=2, on=...)`) turns this mistake into an immediate
        `TypeError` at import instead of a silent bug."""),
    predict("Stacking order", "easy",
        code="""
        import functools

        def wrap(name):
            def decorator(func):
                @functools.wraps(func)
                def wrapper(x):
                    return f"{name}(" + func(x) + ")"
                return wrapper
            return decorator

        @wrap("a")
        @wrap("b")
        @wrap("c")
        def f(x):
            return x

        print(f("x"))
        g = wrap("a")(wrap("b")(wrap("c")(lambda x: x)))
        print(g("y"), f.__name__)
        """,
        hints=["The bottom decorator wraps the function first. The outermost wrapper runs first and adds its text around everything inside."],
        why="""Decorators apply bottom-up: `c` wraps `f`, `b` wraps that, `a` wraps the result, so `f = a(b(c(f)))`. At call time `a`'s
        wrapper runs first, but it calls the inner layers before building its own string, so the result reads from the outside in:
        `a(b(c(x)))`. The explicit nesting in `g` is the same structure. `wraps` at each layer keeps the name `f`."""),
)

section("medium", "Medium",
    write("Validate argument ranges", "medium", tag="GenAI",
        prompt="""Write a decorator factory `in_range(**ranges)` where each range is `(lo, hi)`. The wrapper binds the call's
        arguments to the function's signature (with defaults applied) and raises `ValueError(f"{name} must be in [{lo}, {hi}], got
        {value!r}")` for the first argument outside its range, before calling the function. Raise `TypeError` at decoration time if a
        range names a parameter the function does not have.""",
        code="""
        import functools, inspect

        def in_range(**ranges):
            pass
        """,
        tests="""
        @in_range(temperature=(0, 2), top_p=(0, 1))
        def generate(prompt, temperature=0.7, top_p=1.0):
            return (prompt, temperature, top_p)

        assert generate("hi") == ("hi", 0.7, 1.0) and generate("hi", 1.5, top_p=0.2) == ("hi", 1.5, 0.2)
        for args, kwargs, msg in [(("hi", 2.5), {}, "temperature must be in [0, 2], got 2.5"),
                                  (("hi",), {"top_p": -1}, "top_p must be in [0, 1], got -1")]:
            try:
                generate(*args, **kwargs)
                assert False
            except ValueError as e:
                assert str(e) == msg
        try:
            in_range(temprature=(0, 2))(generate.__wrapped__)
            assert False
        except TypeError as e:
            assert "temprature" in str(e)
        assert generate.__name__ == "generate"
        """,
        hints=["In `decorator(func)`, compute `sig = inspect.signature(func)` and check `set(ranges) - set(sig.parameters)`.",
               "In the wrapper: `bound = sig.bind(*args, **kwargs)`, `bound.apply_defaults()`, then check each named range."],
        solution="""
        import functools, inspect

        def in_range(**ranges):
            def decorator(func):
                sig = inspect.signature(func)
                unknown = set(ranges) - set(sig.parameters)
                if unknown:
                    raise TypeError(f"{func.__name__} has no parameter(s): {sorted(unknown)}")

                @functools.wraps(func)
                def wrapper(*args, **kwargs):
                    bound = sig.bind(*args, **kwargs)
                    bound.apply_defaults()
                    for name, (lo, hi) in ranges.items():
                        value = bound.arguments[name]
                        if not lo <= value <= hi:
                            raise ValueError(f"{name} must be in [{lo}, {hi}], got {value!r}")
                    return func(*args, **kwargs)
                return wrapper
            return decorator
        """,
        why="""The factory holds the ranges; the decorator, which is the first level that sees the function, checks that every named range
        matches a real parameter, so a misspelling like `temprature` fails at import instead of silently never validating anything.
        Binding to the signature is what lets the check work no matter how the argument was passed, positionally (`2.5`) or by keyword
        (`top_p=-1`), and with defaults filled in. The signature is computed once per decorated function. The test re-decorates the
        original through `__wrapped__`, which `wraps` provides."""),
    fix("Decorated functions that share one cache", "medium", tag="ML",
        prompt="""`cached(maxsize)` should give each decorated function its own cache of at most `maxsize` entries (dropping the
        oldest). Two decorated functions return each other's results for the same argument. Fix it.""",
        code="""
        import functools

        def cached(maxsize, store={}):
            def decorator(func):
                @functools.wraps(func)
                def wrapper(x):
                    if x not in store:
                        if len(store) >= maxsize:
                            store.pop(next(iter(store)))
                        store[x] = func(x)
                    return store[x]
                wrapper.store = store
                return wrapper
            return decorator
        """,
        tests="""
        @cached(maxsize=2)
        def square(x):
            return x * x

        @cached(maxsize=2)
        def double(x):
            return x * 2

        assert square(3) == 9 and double(3) == 6
        assert square(4) == 16 and square(5) == 25 and list(square.store) == [4, 5]
        assert double.store == {3: 6} and square.store is not double.store
        """,
        hints=["A mutable default (`store={}`) is created once, when `def cached` runs, and shared by every call of the factory (2.4).",
               "Create the dict inside `decorator`, so each decorated function gets a new one."],
        solution="""
        import functools

        def cached(maxsize):
            def decorator(func):
                store = {}

                @functools.wraps(func)
                def wrapper(x):
                    if x not in store:
                        if len(store) >= maxsize:
                            store.pop(next(iter(store)))
                        store[x] = func(x)
                    return store[x]
                wrapper.store = store
                return wrapper
            return decorator
        """,
        why="""`store={}` is a mutable default argument (2.4): one dict, created when `def cached` ran, shared by every call of the factory, so
        `square(3)` and `double(3)` used the same key `3` in the same dict and the second got the first's answer. State that belongs
        to **one decorated function** must be created in the decorator level, which runs once per function; state that belongs to one
        **call** goes in the wrapper. Dicts keep insertion order, so `next(iter(store))` is the oldest key, which gives a simple
        first-in-first-out eviction; `functools.lru_cache` (8.3) evicts the **least recently used** instead."""),
    write("Mark a function as deprecated", "medium", tag="Data work",
        prompt="""Write a decorator factory `deprecated(reason, alternative=None)` that emits a `DeprecationWarning` on the **first** call
        only, with the message `"<name> is deprecated: <reason>"` plus `"; use <alternative>"` if given, and `stacklevel=2` so it
        points at the caller. Calls still return the original result. Use `functools.wraps` and the `warnings` module.""",
        code="""
        import functools, warnings

        def deprecated(reason, alternative=None):
            pass
        """,
        tests="""
        import warnings

        @deprecated("the v1 API is retired", alternative="embed_v2")
        def embed_v1(text):
            return [len(text)]

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            assert embed_v1("ab") == [2] and embed_v1("abc") == [3]
        assert len(caught) == 1 and caught[0].category is DeprecationWarning
        assert str(caught[0].message) == "embed_v1 is deprecated: the v1 API is retired; use embed_v2"

        @deprecated("slow")
        def old():
            return "ok"
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            assert old() == "ok"
        assert str(caught[0].message) == "old is deprecated: slow" and old.__name__ == "old"
        """,
        hints=["Build the message in the decorator level. Keep a flag such as `wrapper.warned = False` and flip it on the first call."],
        solution="""
        import functools, warnings

        def deprecated(reason, alternative=None):
            def decorator(func):
                message = f"{func.__name__} is deprecated: {reason}"
                if alternative:
                    message += f"; use {alternative}"

                @functools.wraps(func)
                def wrapper(*args, **kwargs):
                    if not wrapper.warned:
                        wrapper.warned = True
                        warnings.warn(message, DeprecationWarning, stacklevel=2)
                    return func(*args, **kwargs)
                wrapper.warned = False
                return wrapper
            return decorator
        """,
        why="""The message is built once per function, at decoration time. `stacklevel=2` makes the warning report the line that **called**
        `embed_v1`, which is the line someone needs to change, instead of the line inside the wrapper (7.3). Warning only once avoids
        flooding logs from a hot loop; the `warnings` module also deduplicates by location by default, but the test switches that
        off with `simplefilter("always")`, which is why the flag matters. Python 3.13 added `warnings.deprecated` as a ready-made
        decorator with the same idea, which type checkers also understand."""),
    choose("Where to put the cache", "medium",
        prompt="Both decorate an expensive function with a slow logging layer and a cache, then call it 20,000 times with 10 distinct arguments. Which order is faster?",
        setup="""import functools

def slow_log(func):
    @functools.wraps(func)
    def wrapper(x):
        line = f"{func.__name__}({x!r})" * 20          # stands in for formatting and writing a log line
        return func(x)
    return wrapper

def memo(func):
    store = {}
    @functools.wraps(func)
    def wrapper(x):
        if x not in store:
            store[x] = func(x)
        return store[x]
    return wrapper

def work(x):
    return sum(i * i for i in range(2000)) + x

args = [i % 10 for i in range(20_000)]""",
        options={
            "a": "f = slow_log(memo(work))\nfor x in args:\n    f(x)",
            "b": "f = memo(slow_log(work))\nfor x in args:\n    f(x)",
        },
        answer="b",
        hints=["On a cache hit, which layers still run in each version?"],
        why="""With the cache outermost (B), a hit returns before the logging layer is reached, so only 10 calls ever log or compute. With the
        cache inside (A), every one of the 20,000 calls runs the logging wrapper first and only then finds the cached value. Both
        compute `work` only 10 times; the difference is the cost of the outer layers on every hit. Whether that is right depends on
        intent: if every request must be logged or rate-limited, the cache belongs inside; if repeated answers should be free, it belongs
        outside."""),
    trace("Layers in action", "medium",
        prompt="Fill in `events` after each marked line.",
        code="""
        import functools
        events = []

        def mark(name):
            def decorator(func):
                @functools.wraps(func)
                def wrapper(*args):
                    events.append(name + ">")
                    try:
                        return func(*args)
                    finally:
                        events.append("<" + name)
                return wrapper
            return decorator

        @mark("auth")
        @mark("cache")
        def load(x):
            events.append("load")
            if x < 0:
                raise ValueError(x)
            return x

        load(1)  # row: "success"
        events.clear()
        try:
            load(-1)
        except ValueError:
            events.append("caller")  # row: "failure"
        """,
        trace_vars=["events"],
        hints=["The outermost decorator (`auth`) enters first and leaves last. `finally` runs on the way out, even when an exception passes."],
        why="""`auth` was applied last, so its wrapper is outermost: it enters first, then `cache`, then the function. On the way out the order
        reverses. With an exception, each layer's `finally` still runs as the error passes through it, innermost first, and then the
        caller's handler runs. This onion order is why authorisation must be the **outer** layer when combined with a cache: it runs
        before the cache can answer."""),
    fix("Timing that measures the wrong thing", "medium", tag="GenAI",
        prompt="""`ask` is meant to record **one** timing per call, covering all retries, so the dashboard shows what the user waited.
        It records one timing per attempt instead. Fix the decorator order (nothing else).""",
        code="""
        import functools

        TIMINGS = []
        ticks = iter([0, 1, 1, 3, 3, 4, 10, 11])
        clock = lambda: next(ticks)

        def timed(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start = clock()
                try:
                    return func(*args, **kwargs)
                finally:
                    TIMINGS.append(clock() - start)
            return wrapper

        def retry(times):
            def decorator(func):
                @functools.wraps(func)
                def wrapper(*args, **kwargs):
                    for attempt in range(1, times + 1):
                        try:
                            return func(*args, **kwargs)
                        except TimeoutError:
                            if attempt == times:
                                raise
                return wrapper
            return decorator

        outcomes = iter([TimeoutError(), TimeoutError(), "ok"])

        @retry(times=3)
        @timed
        def ask(q):
            out = next(outcomes)
            if isinstance(out, Exception):
                raise out
            return out
        """,
        tests="""
        assert ask("refund?") == "ok"
        assert TIMINGS == [1]
        assert ask.__name__ == "ask"
        """,
        hints=["The decorator listed first is the outermost. Which one should wrap the other?"],
        solution="""
        import functools

        TIMINGS = []
        ticks = iter([0, 1, 1, 3, 3, 4, 10, 11])
        clock = lambda: next(ticks)

        def timed(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start = clock()
                try:
                    return func(*args, **kwargs)
                finally:
                    TIMINGS.append(clock() - start)
            return wrapper

        def retry(times):
            def decorator(func):
                @functools.wraps(func)
                def wrapper(*args, **kwargs):
                    for attempt in range(1, times + 1):
                        try:
                            return func(*args, **kwargs)
                        except TimeoutError:
                            if attempt == times:
                                raise
                return wrapper
            return decorator

        outcomes = iter([TimeoutError(), TimeoutError(), "ok"])

        @timed
        @retry(times=3)
        def ask(q):
            out = next(outcomes)
            if isinstance(out, Exception):
                raise out
            return out
        """,
        why="""With `@timed` below `@retry`, the timing wrapper sat **inside** the retry loop, so each of the three attempts was timed
        separately and the user-visible total was never recorded. Moving `@timed` to the top makes it the outermost layer: one
        `clock()` before the whole retry sequence and one after, here the ticks 0 and 1. Both orders are legitimate measurements;
        per-attempt latency is useful for spotting a slow provider. The decorator order is the place to say which one you mean."""),
    refactor("Near-identical decorators into one factory", "medium", tag="GenAI",
        prompt="Replace the three decorators with one factory `require(role)`. Same behaviour and messages. Keep the tests green.",
        code="""
        import functools

        def require_admin(func):
            @functools.wraps(func)
            def wrapper(user, *args, **kwargs):
                if "admin" not in user["roles"]:
                    raise PermissionError(f"{user['name']} needs role 'admin' for {func.__name__}")
                return func(user, *args, **kwargs)
            return wrapper

        def require_editor(func):
            @functools.wraps(func)
            def wrapper(user, *args, **kwargs):
                if "editor" not in user["roles"]:
                    raise PermissionError(f"{user['name']} needs role 'editor' for {func.__name__}")
                return func(user, *args, **kwargs)
            return wrapper

        def require_viewer(func):
            @functools.wraps(func)
            def wrapper(user, *args, **kwargs):
                if "viewer" not in user["roles"]:
                    raise PermissionError(f"{user['name']} needs role 'viewer' for {func.__name__}")
                return func(user, *args, **kwargs)
            return wrapper

        @require_admin
        def delete_index(user, name):
            return f"deleted {name}"

        @require_viewer
        def search(user, q):
            return [q]
        """,
        tests="""
        ana = {"name": "ana", "roles": {"admin", "viewer"}}
        bo = {"name": "bo", "roles": {"viewer"}}
        assert delete_index(ana, "faq") == "deleted faq" and search(bo, "x") == ["x"]
        try:
            delete_index(bo, "faq")
            assert False
        except PermissionError as e:
            assert str(e) == "bo needs role 'admin' for delete_index"
        assert delete_index.__name__ == "delete_index"
        """,
        hints=["`def require(role):` returns a decorator whose wrapper uses `role` from the closure. Then `@require(\"admin\")`."],
        solution="""
        import functools

        def require(role):
            def decorator(func):
                @functools.wraps(func)
                def wrapper(user, *args, **kwargs):
                    if role not in user["roles"]:
                        raise PermissionError(f"{user['name']} needs role {role!r} for {func.__name__}")
                    return func(user, *args, **kwargs)
                return wrapper
            return decorator

        @require("admin")
        def delete_index(user, name):
            return f"deleted {name}"

        @require("viewer")
        def search(user, q):
            return [q]
        """,
        why="""The three decorators differed only in one string, which is exactly what a factory parameter is for: the role now lives in the
        closure, and a new role needs no new code. `{role!r}` reproduces the quoted role in the message. The wrapper names `user` as its
        first parameter because every protected function takes the user first; that convention is part of the decorator's contract
        and worth documenting. Web frameworks do the same with dependencies such as FastAPI's `Security(...)` or Flask-Login's
        `@login_required`."""),
    predict("With and without parentheses", "medium",
        code="""
        import functools

        def flag(func=None, *, name="default"):
            def decorator(f):
                f.flag = name
                return f
            return decorator if func is None else decorator(func)

        @flag
        def a(): pass

        @flag(name="custom")
        def b(): pass

        print(a.flag, b.flag, a.__name__)
        c = flag(name="x")
        print(callable(c), c.__name__ if hasattr(c, "__name__") else "-")
        try:
            flag("positional")
        except Exception as e:
            print(type(e).__name__)
        """,
        hints=["Used bare, `func` is the function. Called with keywords only, `func` is `None` and the decorator is returned."],
        why="""`@flag` passes the function as `func`, so it is decorated at once with the default name; `@flag(name="custom")` returns the
        decorator first. `flag(name="x")` alone returns the inner `decorator` function. The last call passes a string positionally,
        so `flag` treats it as the function and tries to set an attribute on a string, which raises `AttributeError`. That is the
        weak spot of the dual form: a positional mistake is not caught by the signature."""),
)

section("hard", "Hard",
    write("A sliding-window rate limit", "hard", tag="GenAI",
        prompt="""Write a decorator factory `rate_limited(calls, per, clock)` that allows at most `calls` calls in any window of `per`
        seconds (measured with `clock()`). A call over the limit raises `RateLimitExceeded` (define it) with an attribute
        `retry_after`, the seconds until the oldest call in the window leaves it, and does **not** call the function. Each decorated
        function has its own limit. Use `collections.deque`.""",
        code="""
        import functools
        from collections import deque

        def rate_limited(calls, per, clock):
            pass
        """,
        tests="""
        now = [0.0]
        clock = lambda: now[0]
        ran = []

        @rate_limited(calls=2, per=10, clock=clock)
        def embed(text):
            ran.append(text)
            return [len(text)]

        assert embed("a") == [1]
        now[0] = 3.0
        assert embed("bb") == [2]
        now[0] = 4.0
        try:
            embed("ccc")
            assert False
        except RateLimitExceeded as e:
            assert e.retry_after == 6.0 and ran == ["a", "bb"]
        now[0] = 10.0
        assert embed("d") == [1]
        try:
            embed("e")
            assert False
        except RateLimitExceeded as e:
            assert e.retry_after == 3.0

        @rate_limited(calls=1, per=5, clock=clock)
        def other():
            return "ok"
        assert other() == "ok" and embed.__name__ == "embed"
        """,
        hints=["Keep a `deque` of call times per decorated function. On each call, pop times older than `now - per` from the left.",
               "If the deque is full, `retry_after = times[0] + per - now`. Otherwise append `now` and call the function."],
        solution="""
        import functools
        from collections import deque


        class RateLimitExceeded(Exception):
            def __init__(self, message, retry_after):
                super().__init__(message)
                self.retry_after = retry_after


        def rate_limited(calls, per, clock):
            if calls < 1 or per <= 0:
                raise ValueError("calls must be >= 1 and per > 0")

            def decorator(func):
                times = deque()

                @functools.wraps(func)
                def wrapper(*args, **kwargs):
                    now = clock()
                    while times and times[0] <= now - per:
                        times.popleft()
                    if len(times) >= calls:
                        wait = times[0] + per - now
                        raise RateLimitExceeded(f"{func.__name__}: {calls} calls per {per}s exceeded", retry_after=wait)
                    times.append(now)
                    return func(*args, **kwargs)
                return wrapper
            return decorator
        """,
        why="""A sliding window keeps the exact times of recent calls, so the limit holds for **any** `per`-second window, not just fixed
        minutes on the clock. A `deque` makes dropping expired times from the left O(1). The deque is created in the decorator level,
        so `embed` and `other` have independent limits. Raising instead of sleeping keeps the decorator honest and testable, and
        `retry_after` gives the caller (or a retry decorator stacked **outside** it) the exact wait, like the server's `Retry-After`
        header (7.4). Rejected calls are not recorded, so waiting callers do not extend each other's wait. At `now = 10`, the call
        from time 0 has left the window (`0 <= 10 - 10`), which is why `"d"` is allowed."""),
    fix("Read the code: a decorator with optional settings", "hard", tag="GenAI",
        prompt="""`log_calls` should work both as `@log_calls` and as `@log_calls(level="debug")`, recording `(level, name)` in `LOG`
        for each call and keeping the function's name. `@log_calls(level="debug")` currently breaks the function, and the bare form
        loses the name. Read it, find the bugs and fix them.""",
        code="""
        LOG = []


        def log_calls(func=None, level="info"):
            def decorator(f):
                def wrapper(*args, **kwargs):
                    LOG.append((level, f.__name__))
                    return f(*args, **kwargs)
                return wrapper
            return decorator(func)
        """,
        tests="""
        @log_calls
        def search(q):
            return [q]

        @log_calls(level="debug")
        def rerank(docs):
            return sorted(docs)

        assert search("x") == ["x"] and rerank(["b", "a"]) == ["a", "b"]
        assert LOG == [("info", "search"), ("debug", "rerank")]
        assert search.__name__ == "search" and rerank.__name__ == "rerank"
        try:
            log_calls("debug")
            assert False, "level must be keyword-only"
        except TypeError:
            pass
        """,
        hints=["With `@log_calls(level=...)`, `func` is `None`, and `decorator(None)` returns a wrapper around `None`.",
               "Return `decorator` when `func is None`. Make `level` keyword-only with `*`, and reject a non-callable `func`."],
        solution="""
        import functools

        LOG = []


        def log_calls(func=None, *, level="info"):
            def decorator(f):
                @functools.wraps(f)
                def wrapper(*args, **kwargs):
                    LOG.append((level, f.__name__))
                    return f(*args, **kwargs)
                return wrapper
            if func is None:
                return decorator
            if not callable(func):
                raise TypeError(f"log_calls expected a function, got {func!r}; pass settings as keywords")
            return decorator(func)
        """,
        why="""Three bugs. With settings, `func` is `None`, but the code still called `decorator(None)`, so `rerank` became a wrapper around
        `None`, and calling it raised `TypeError: 'NoneType' object is not callable` (after logging, which made the failure look like a
        logging bug). Returning the decorator when `func is None` lets `@` apply it. `level` was an ordinary parameter, so
        `log_calls("debug")` passed a string as the function; making it keyword-only with `*` and checking `callable(func)` turns that
        mistake into a clear error at import. And without `functools.wraps`, every decorated function was named `wrapper`. The dual
        form needs all three details right, which is why many teams prefer to support just `@log_calls()`."""),
    write("Fall back to other implementations", "hard", tag="GenAI",
        prompt="""Write a decorator factory `with_fallbacks(*fallbacks, on=(TimeoutError, ConnectionError))`. The decorated function
        is tried first; if it raises one of the `on` exceptions, each fallback is called with the **same** arguments, in order, until
        one succeeds. Record the name of the function that answered in `wrapper.last_source`. If all fail, raise the last exception
        with the earlier ones attached as notes (`"<name>: <Type>: <message>"`). Other exceptions propagate at once.""",
        code="""
        import functools

        def with_fallbacks(*fallbacks, on=(TimeoutError, ConnectionError)):
            pass
        """,
        tests="""
        def small_model(q, *, temperature=0.0):
            return f"small:{q}:{temperature}"

        def cached_answer(q, **kwargs):
            raise ConnectionError("cache offline")

        def canned(q, **kwargs):
            return "Please try again later."

        @with_fallbacks(small_model, canned)
        def big_model(q, *, temperature=0.0):
            raise TimeoutError("30s")

        assert big_model("refund?", temperature=0.2) == "small:refund?:0.2" and big_model.last_source == "small_model"

        @with_fallbacks(cached_answer, canned)
        def primary(q):
            raise ConnectionError("down")
        assert primary("x") == "Please try again later." and primary.last_source == "canned"

        @with_fallbacks(cached_answer)
        def lonely(q):
            raise TimeoutError("slow")
        try:
            lonely("x")
            assert False
        except ConnectionError as e:
            assert str(e) == "cache offline" and e.__notes__ == ["lonely: TimeoutError: slow"]

        @with_fallbacks(canned)
        def buggy(q):
            raise KeyError("bug")
        try:
            buggy("x")
            assert False
        except KeyError:
            assert buggy.__name__ == "buggy"
        """,
        hints=["Inside the wrapper, loop over `(func, *fallbacks)`. Collect notes for each `on` failure; on success, set `wrapper.last_source = f.__name__` and return.",
               "After the loop, add the collected notes (except the last failure's own) to the last exception and `raise` it."],
        solution="""
        import functools

        def with_fallbacks(*fallbacks, on=(TimeoutError, ConnectionError)):
            def decorator(func):
                chain = (func, *fallbacks)

                @functools.wraps(func)
                def wrapper(*args, **kwargs):
                    notes, last = [], None
                    for f in chain:
                        try:
                            result = f(*args, **kwargs)
                        except on as e:
                            if last is not None:
                                notes.append(f"{last[0]}: {type(last[1]).__name__}: {last[1]}")
                            last = (f.__name__, e)
                            continue
                        wrapper.last_source = f.__name__
                        return result
                    for note in notes:
                        last[1].add_note(note)
                    raise last[1]
                wrapper.last_source = None
                return wrapper
            return decorator
        """,
        why="""The primary and its fallbacks form one chain, tried in order with identical arguments, so fallbacks must accept the same call
        signature (`canned` takes `**kwargs` to ignore extras). Only the listed transient errors move on to the next option; a `KeyError`
        from a bug propagates from the first function that has it, as fallbacks must never hide bugs (7.3). When everything fails, the
        caller receives the **last** real exception, with each earlier failure recorded as a note, so the traceback tells the whole
        story without inventing a new exception type. `last_source` makes degradation visible to the caller and to metrics. This is the
        decorator form of the provider fallback in the 7.P client."""),
    predict("Settings captured per decoration", "hard",
        code="""
        import functools

        def limit(n):
            def decorator(func):
                @functools.wraps(func)
                def wrapper(xs):
                    return func(xs)[:n]
                return wrapper
            return decorator

        def top(xs):
            return sorted(xs, reverse=True)

        tops = [limit(n)(top) for n in range(1, 4)]
        print([f([5, 1, 4, 2]) for f in tops])

        lambdas = [lambda xs: top(xs)[:n] for n in range(1, 4)]
        print([f([5, 1, 4, 2]) for f in lambdas])

        N = 2
        @limit(N)
        def best(xs):
            return top(xs)
        N = 10
        print(best([5, 1, 4, 2]), N)
        """,
        hints=["Each call of `limit(n)` creates a new closure with its own `n`. The lambdas share the comprehension's single `n`."],
        why="""Every `limit(n)` call binds the current value of `n` as a parameter of a new function call, so each decorated function keeps its own
        limit: 1, 2 and 3 items. The lambdas instead all refer to the comprehension's variable `n`, looked up when they run, after it
        ended at 3: the late-binding trap of 6.1. The decorator factory avoids it for the same reason the `n=n` default trick does: the
        value is passed into a new scope at creation time. Likewise `@limit(N)` captured 2; changing `N` afterwards does nothing."""),
)

section("interview", "Interview questions",
    explain("Explain how a decorator with arguments works, level by level.", "medium", tag="Interview",
        why="""It is a function that returns a decorator. `@retry(times=3)` is evaluated in two steps: first `retry(times=3)` is called (level
        one, the factory) and returns a decorator that has `times` in its closure; then that decorator is called with the function
        below (level two), and returns a wrapper that has both `times` and the function in its closure; the name is bound to that
        wrapper. At call time only level three, the wrapper, runs. So `@retry(times=3) def f` equals `f = retry(times=3)(f)`. The
        factory is the right place to validate settings (fail at import), the decorator level the place for per-function state (a
        cache, counters, an inspected signature), and the wrapper the place for per-call work. Making settings keyword-only prevents
        `@retry` without parentheses from silently passing the function as a setting."""),
    explain("Does the order of stacked decorators matter? Give examples.", "medium", tag="Interview",
        why="""Yes. Decorators are applied bottom-up, so `@a @b def f` is `a(b(f))`, and at call time `a`'s wrapper runs first and sees
        everything `b` does. Examples: a timer outside a retry measures total latency including waits, inside it measures each attempt;
        a cache outside logging or rate limiting short-circuits them on hits, inside it does not; authorisation must sit outside a
        cache, or a cached result could be served to a user who is not allowed to see it; validation should sit outside retries, since
        retrying invalid input is pointless; a retry outside a rate limiter will retry rate-limit rejections, while inside it may hammer
        the limiter. Choosing the order is part of the design, and it is worth a comment when it matters."""),
    explain("You are asked to write a reusable `@llm_call(model=..., retries=..., timeout=...)` decorator for your team. What would you consider?", "hard", tag="Interview",
        why="""Settings: keyword-only arguments validated in the factory, so a bad model name or negative retry count fails at import; sensible
        defaults; and the ability to read some settings at call time (a feature flag, a per-request timeout) through callables or a
        config object rather than values frozen at import. Behaviour: retries only on transient errors with backoff, jitter and a
        deadline (7.4), the timeout passed to every attempt, and clear exceptions from one hierarchy. Correctness: `functools.wraps` for
        names and signatures, support for both sync and `async` functions (detect with `inspect.iscoroutinefunction` and return the
        matching wrapper), and streaming generators. Observability: one trace span per logical call with attempts, latency, tokens,
        model and errors, without logging secrets or raw personal data. Testability: injectable clock, sleep and transport, and access
        to the undecorated function through `__wrapped__`. Composition: document how it should be ordered with caching and rate limiting.
        Finally, consider whether an explicit client object with methods is clearer than a decorator for this much configuration; the
        decorator is best when it stays thin."""),
)

recap(
    "A decorator with arguments is a factory: `@retry(times=3)` calls `retry(times=3)`, which returns the decorator applied to the function.",
    "Three levels, three jobs: validate settings in the factory, create per-function state in the decorator, do per-call work in the wrapper.",
    "Settings are captured when the `@` line runs; pass a callable to read a value at call time. Never use a mutable default for shared state.",
    "Optional parentheses need `func=None` plus keyword-only settings; supporting one form is often simpler.",
    "Stacked decorators apply bottom-up and run top-down: order decides what a timer measures, what a cache skips and where checks happen.",
)
