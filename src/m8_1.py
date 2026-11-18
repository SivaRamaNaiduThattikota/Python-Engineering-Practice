from lesson import *

lesson(
    id="m8-1", num="8.1", title="Functions that wrap functions",
    intro="A decorator is a function that takes a function and returns a replacement for it. What `@` really does and when "
          "it runs, the wrapper pattern with `*args` and `**kwargs`, `functools.wraps` and why frameworks need it, state "
          "kept by a decorator, and the traps: lost return values, swallowed errors, generators. Applied to timing, "
          "tracing and validating calls, the way LLM observability tools do.",
    desc="The wrapper pattern, `*args` and `**kwargs` pass-through, `functools.wraps`.",
    keys="decorator wrapper at sign syntax functools wraps __wrapped__ args kwargs closure definition time call time timing tracing logging count calls memoize generator decorator observability",
)

term("Decorator", "A function that takes a function and returns a function (usually a wrapper around it). `@dec` above a `def` means `f = dec(f)`.")
term("Wrapper", "The inner function a decorator returns. It runs extra code before and after calling the original function.")
term("functools.wraps", "A decorator for wrappers that copies the original's name, docstring and signature information onto the wrapper.")

section("objects", "A function that takes and returns functions",
    p("""Everything in this lesson rests on two facts from Module 3. Functions are **objects**: you can pass them to other functions,
    return them, and store them in variables and dicts (3.5). And an inner function **remembers** the variables of the function
    that created it, even after that function has returned: a closure (3.4). Put together, you can write a function that receives
    a function and returns a new function that calls the original with something extra around it."""),
    ex("""
    def shout(func):
        def wrapper(text):
            return func(text).upper() + "!"      # call the original, then change its result
        return wrapper

    def greet(name):
        return f"hello {name}"

    loud_greet = shout(greet)
    print(greet("ana"), "|", loud_greet("ana"))
    print(loud_greet is greet, loud_greet.__name__)
    """, "wrapping.py"),
    p("""`shout(greet)` did not call `greet`; it built and returned `wrapper`, a new function that, **when called**, calls `greet` (which
    it remembers through the closure) and transforms the result. That pattern, "take a function, return a function that adds
    behaviour around it", is a **decorator**. Very often you want the new behaviour to replace the old function under the same
    name, so you write `greet = shout(greet)`. Python has syntax for exactly that line:"""),
    ex("""
    def shout(func):
        def wrapper(text):
            return func(text).upper() + "!"
        return wrapper

    @shout
    def greet(name):                 # the same as: greet = shout(greet), right after the def
        return f"hello {name}"

    print(greet("bo"))
    """, "at_syntax.py"),
    p("""`@shout` on the line above a `def` means: define the function, pass it to `shout`, and bind the **result** to the name
    `greet`. Nothing more. After that line, the name `greet` refers to `wrapper`, and the original function is reachable only
    through the closure. Any expression that evaluates to a callable can follow the `@`, which is how decorators with arguments
    work (8.2)."""),
)

section("when", "When decorator code runs",
    p("""A decorator has two separate moments, and mixing them up causes most decorator bugs. The **decorator function** runs once,
    at **definition time**: when Python executes the `def` statement, which for a module-level function is when the module is
    imported. The **wrapper** runs at **call time**, every time someone calls the decorated name. Code in the decorator's body
    (outside the wrapper) runs once; code inside the wrapper runs on every call."""),
    ex("""
    events = []

    def announce(func):
        events.append(f"decorating {func.__name__}")      # definition time: once
        def wrapper(*args, **kwargs):
            events.append(f"calling {func.__name__}")     # call time: every call
            return func(*args, **kwargs)
        return wrapper

    @announce
    def embed(text):
        return [len(text)]

    events.append("module loaded")
    embed("a"); embed("bc")
    print(events)
    """, "two_moments.py"),
    p("""The decoration happened before the module even finished loading, before any call. Frameworks rely on this: a FastAPI route
    decorator or an agent's tool registry records the function at import time, so by the time the app starts serving, every route
    and tool is known (8.4). It also means expensive work in the decorator body (opening a connection, loading a model) happens
    at import, whether or not the function is ever called, which is usually not what you want."""),
)

section("wrapper", "The wrapper pattern",
    p("""Almost every decorator has the same shape. The wrapper accepts **any** arguments with `*args` and `**kwargs` (3.2), does
    something before the call, calls the original with exactly those arguments, does something after, and **returns the result**.
    Using `*args, **kwargs` instead of copying the original's parameters is what lets one decorator work on any function:
    positional and keyword arguments, defaults, and keyword-only parameters all pass straight through (problem 6)."""),
    ex("""
    import time

    def timed(func):
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)                 # pass everything through, return the result
            finally:
                elapsed = time.perf_counter() - start
                wrapper.timings.append(round(elapsed, 6))    # runs on success and on failure
        wrapper.timings = []
        return wrapper

    @timed
    def score(text, *, threshold=0.5):
        if not text:
            raise ValueError("empty text")
        return len(text) > 10 * threshold

    print(score("refund request", threshold=0.2), score("hi"))
    try:
        score("")
    except ValueError as e:
        print("ValueError:", e)
    print(len(score.timings), all(t >= 0 for t in score.timings))
    """, "wrapper_pattern.py"),
    p("""Three details make this wrapper correct, and each one is a common bug when missing. It **returns** what the original
    returned; a wrapper that forgets `return` turns every result into `None` (problem 3). It lets **exceptions pass through**: the
    `try`/`finally` records the time even when the call fails, but does not catch anything, so callers still see the
    `ValueError` (problem 10). And it passes the arguments **unchanged**, including keyword-only ones like `threshold`."""),
    p("""The `wrapper.timings` list shows one way to keep **state** in a decorator: functions are objects and can have attributes, so
    the decorated function carries its own measurements, separate for every function decorated. A closure variable updated with
    `nonlocal` works too, but is invisible from outside; an attribute can be read by tests and dashboards."""),
)

section("wraps", "`functools.wraps`: keep the original's identity",
    p("""After decoration, the name `score` refers to `wrapper`. Unless you do something about it, the decorated function **looks**
    like `wrapper`: its `__name__` is `"wrapper"`, its docstring is gone, and `help()` and `inspect.signature()` describe `(*args,
    **kwargs)`. That breaks more than cosmetics. Logs and tracebacks show `wrapper` for every decorated function, test tools list
    them all under the same name, and frameworks that read a function's signature to decide what it accepts (FastAPI building an
    API from parameters, agent frameworks building a tool schema, pytest injecting fixtures) see the wrong one."""),
    p("""`functools.wraps(func)` is a decorator **for the wrapper**: it copies `__name__`, `__qualname__`, `__doc__`, `__module__`
    and the `__dict__` of the original onto the wrapper, and sets `wrapper.__wrapped__ = func`. `inspect.signature` follows
    `__wrapped__`, so it reports the original parameters. Write `@functools.wraps(func)` on every wrapper you write; there is no
    good reason to leave it out."""),
    ex("""
    import functools, inspect

    def plain(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper

    def proper(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper

    def search(query: str, k: int = 3) -> list:
        \"\"\"Search the knowledge base.\"\"\"
        return [query] * k

    a, b = plain(search), proper(search)
    print(a.__name__, a.__doc__, inspect.signature(a))
    print(b.__name__, b.__doc__, inspect.signature(b))
    print(b.__wrapped__ is search, b("x", k=1))
    """, "wraps.py"),
    p("""`__wrapped__` also gives you the undecorated function when you need it, for example to test the original logic without the
    decorator's side effects (no caching, no logging): `score.__wrapped__("text")`. Note that `wraps` copies **metadata**; the
    wrapper still runs its own code, so calling `b` still goes through the decorator."""),
)

section("traps", "Decorator traps",
    p("""Beyond forgetting `return` and `wraps`, three traps come up again and again."""),
    p("""**Recursion goes through the wrapper.** Inside a decorated recursive function, the recursive call looks up the function's name
    at call time (3.3), and that name now refers to the wrapper. So every recursive call is also decorated: a counting decorator
    counts all of them, a logging decorator logs every level, a timing decorator times each nested call. Sometimes that is exactly
    what you want (memoization relies on it, 8.3); sometimes it is a flood (problem 16)."""),
    p("""**Generators finish later.** A generator function returns its generator immediately (6.3), so a wrapper that times or logs
    "after the call" measures only the creation of the generator, not the streaming. To wrap a generator properly, the wrapper must
    itself be a generator that iterates the original and yields each item (problem 15). The same applies to `async def` functions,
    whose wrapper must be `async` too (14.4)."""),
    ex("""
    import functools

    def log_after(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            print(f"  {func.__name__} returned {type(result).__name__}")
            return result
        return wrapper

    @log_after
    def stream(n):
        for i in range(n):
            print(f"  producing {i}")
            yield i

    g = stream(2)                    # "returned generator" is printed now, before any item exists
    print(list(g))
    """, "generator_trap.py"),
    p("""**Decorating changes the object.** The decorated name is a different function, so `is` comparisons with the original fail,
    and attributes set on the original before decoration are only visible if `wraps` copied them. Decorators that return the
    original function unchanged (after registering it somewhere) avoid this entirely, which is the pattern of 8.4."""),
)

section("uses", "What decorators are used for",
    p("""Decorators are the standard way to add **cross-cutting** behaviour, the kind that is the same for many functions and unrelated
    to what each one does: timing, logging, tracing, counting, caching (8.3), retrying (8.3), rate limiting, checking permissions,
    validating arguments, and registering functions (8.4). The function keeps only its real logic, and the decorator line documents
    the extra behaviour where everyone reads it."""),
    p("""In GenAI code you meet them constantly. Observability tools trace LLM calls with a decorator: LangSmith's `@traceable`,
    Langfuse's `@observe` and OpenTelemetry's span decorators wrap a function, record its inputs, outputs, duration and errors, and
    send them to a dashboard. Agent frameworks turn plain functions into tools with `@tool`. Web frameworks map URLs to functions
    with `@app.get("/path")`. And the standard library offers `@functools.cache`, `@property`, `@classmethod`, `@staticmethod` and
    `@dataclass` (Modules 9 and 11), all built on exactly the mechanism of this lesson."""),
    ex("""
    import functools

    TRACE = []

    def traced(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            entry = {"name": func.__name__, "args": [repr(a)[:20] for a in args]}
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                entry["error"] = type(e).__name__
                raise
            else:
                entry["output"] = repr(result)[:30]
                return result
            finally:
                TRACE.append(entry)
        return wrapper

    @traced
    def retrieve(query):
        return ["Refunds take 5 days.", "No refunds after 30 days."]

    @traced
    def generate(query, context):
        if not context:
            raise ValueError("no context")
        return f"Answer based on {len(context)} chunks"

    generate("refund time?", retrieve("refund time?"))
    try:
        generate("x", [])
    except ValueError:
        pass
    for entry in TRACE:
        print(entry)
    """, "tracing.py"),
    p("""Each entry records the function name (correct thanks to `wraps`), a shortened view of the inputs (never log full prompts
    containing personal data without a policy, 7.4), and either the output or the error type. The exception is re-raised, so
    tracing never changes the program's behaviour, which is the one rule an observability decorator must obey."""),
)

section("warmup", "Warm-up",
    predict("Definition time and call time", "easy",
        code="""
        def deco(func):
            print("decorating", func.__name__)
            def wrapper(*args):
                print("before", args)
                result = func(*args)
                print("after", result)
                return result
            return wrapper

        @deco
        def add(a, b):
            return a + b

        print("defined")
        print(add(2, 3))
        print(add.__name__)
        """,
        hints=["The decorator runs once, when the `def` runs. The wrapper runs on every call."],
        why="""`deco` is called as soon as the `def` statement finishes, so "decorating add" prints first, before "defined". The call `add(2,
        3)` runs the wrapper: "before", the original, "after", and only then does the outer `print` show the returned 5. Without
        `functools.wraps`, the decorated name now reports itself as `wrapper`."""),
    write("Count the calls", "easy", tag="GenAI",
        prompt="""Write a decorator `count_calls` that keeps the number of calls on the decorated function as an attribute `calls`
        (starting at 0, counted even when the call raises), passes all arguments through, returns the result, and uses
        `functools.wraps`.""",
        code="""
        import functools

        def count_calls(func):
            pass
        """,
        tests="""
        @count_calls
        def complete(prompt, *, temperature=0.0):
            \"\"\"Call the model.\"\"\"
            if not prompt:
                raise ValueError("empty prompt")
            return f"{prompt}@{temperature}"

        assert complete.calls == 0
        assert complete("hi") == "hi@0.0" and complete("hi", temperature=0.5) == "hi@0.5"
        try:
            complete("")
        except ValueError:
            pass
        assert complete.calls == 3
        assert complete.__name__ == "complete" and complete.__doc__ == "Call the model."

        @count_calls
        def other():
            return 1
        other()
        assert other.calls == 1 and complete.calls == 3
        """,
        hints=["Increment `wrapper.calls` before calling `func`, so failed calls are counted too.", "Set `wrapper.calls = 0` after defining the wrapper, before returning it."],
        solution="""
        import functools

        def count_calls(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                wrapper.calls += 1
                return func(*args, **kwargs)
            wrapper.calls = 0
            return wrapper
        """,
        why="""Each decoration creates a new `wrapper` with its own `calls` attribute, so `complete` and `other` count separately. Incrementing
        before the call counts failures too; incrementing after would skip calls that raised. The attribute is set on `wrapper`, the
        object the decorated name refers to, which is why `complete.calls` works from outside. Counting model calls per function this
        way is a quick check on how many requests a pipeline really makes, often more than expected once retries and loops add up."""),
    fix("A wrapper that loses the result", "easy", tag="Data work",
        prompt="""`log_call` should record each call's function name and return value in `log`, without changing what the function
        returns. Every decorated function now returns `None`. Fix it.""",
        code="""
        import functools

        log = []

        def log_call(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                result = func(*args, **kwargs)
                log.append((func.__name__, result))
            return wrapper
        """,
        tests="""
        @log_call
        def total(xs):
            return sum(xs)

        assert total([1, 2, 3]) == 6
        assert total([]) == 0
        assert log == [("total", 6), ("total", 0)]
        """,
        hints=["A function without a `return` statement returns `None`."],
        solution="""
        import functools

        log = []

        def log_call(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                result = func(*args, **kwargs)
                log.append((func.__name__, result))
                return result
            return wrapper
        """,
        why="""The wrapper is what callers actually call, so whatever it returns is what they get. It computed the result and recorded it,
        then fell off the end, which returns `None`. This is the most common decorator bug, and it is silent: the log looks perfect,
        while every caller receives `None`. A decorator that adds behaviour must hand back the original return value unchanged."""),
    predict("What wraps preserves", "easy",
        code="""
        import functools, inspect

        def a(func):
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper

        def b(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper

        def embed(text: str, model: str = "small") -> list:
            "Embed one text."
            return [len(text)]
        embed.version = 2

        x, y = a(embed), b(embed)
        print(x.__name__, x.__doc__, hasattr(x, "version"))
        print(y.__name__, y.__doc__, y.version, inspect.signature(y))
        print(y.__wrapped__ is embed, y is embed, y("hi"))
        """,
        hints=["`wraps` copies name, docstring and the function's `__dict__` (its attributes), and sets `__wrapped__`."],
        why="""Without `wraps`, the wrapper keeps its own name and has no docstring or `version` attribute. With `wraps`, the name, the
        docstring and the custom attribute are copied, and `inspect.signature` follows `__wrapped__` to show the original parameters
        and annotations. The decorated object is still a different function from the original; it just carries its identity."""),
)

section("medium", "Medium",
    write("Trace calls without changing behaviour", "medium", tag="GenAI",
        prompt="""Write a decorator `traced` that appends one dict per call to the global list `TRACE`: `{"name": ..., "args":
        [...], "kwargs": {...}, "outcome": ...}`, where args and kwargs values are `repr`s cut to 30 characters, and `outcome` is
        `"ok"` or the exception's type name. The decorated function must return exactly what it returned, and raise exactly what it
        raised.""",
        code="""
        import functools

        TRACE = []

        def traced(func):
            pass
        """,
        tests="""
        @traced
        def retrieve(query, *, k=3):
            if k < 1:
                raise ValueError("k must be positive")
            return [f"doc{i}" for i in range(k)]

        assert retrieve("refund policy for customers in the European Union", k=2) == ["doc0", "doc1"]
        try:
            retrieve("x", k=0)
            assert False
        except ValueError as e:
            assert str(e) == "k must be positive"
        assert TRACE == [
            {"name": "retrieve", "args": ["'refund policy for customers i"], "kwargs": {"k": "2"}, "outcome": "ok"},
            {"name": "retrieve", "args": ["'x'"], "kwargs": {"k": "0"}, "outcome": "ValueError"},
        ]
        assert retrieve.__name__ == "retrieve"
        """,
        hints=["Build the entry before the call, set `outcome` in `try` / `except Exception` (then `raise`), and append in `finally`."],
        solution="""
        import functools

        TRACE = []

        def traced(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                entry = {
                    "name": func.__name__,
                    "args": [repr(a)[:30] for a in args],
                    "kwargs": {k: repr(v)[:30] for k, v in kwargs.items()},
                    "outcome": "ok",
                }
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    entry["outcome"] = type(e).__name__
                    raise
                finally:
                    TRACE.append(entry)
            return wrapper
        """,
        why="""`repr` (not `str`) shows quotes and escape characters, so `'x'` is distinguishable from `x` in the trace, and cutting to 30
        characters keeps a huge prompt from bloating the log. The `except` records the type and then re-raises with a bare `raise`, so
        the caller gets the original exception and traceback; `finally` appends the entry on both paths. This is the skeleton of
        LangSmith's `@traceable` and Langfuse's `@observe`, which also record timings, nest child calls under their parent, and send
        the entries to a server instead of a list."""),
    fix("A wrapper that only accepts one argument", "medium", tag="ML",
        prompt="""`check_finite` should raise `ValueError` if a function returns NaN or infinity, for any function. It works for
        `log_loss(p)` but breaks for functions with several or keyword arguments. Fix the wrapper so arguments pass through untouched,
        and add `functools.wraps`.""",
        code="""
        import math

        def check_finite(func):
            def wrapper(x):
                result = func(x)
                if not math.isfinite(result):
                    raise ValueError(f"{func.__name__} returned {result}")
                return result
            return wrapper
        """,
        tests="""
        import math

        @check_finite
        def log_loss(p):
            return -math.log(p) if p > 0 else math.inf

        @check_finite
        def weighted(a, b, *, w=0.5):
            return a * w + b * (1 - w)

        assert round(log_loss(0.5), 4) == 0.6931
        assert weighted(2, 4) == 3.0 and weighted(2, 4, w=1) == 2
        try:
            log_loss(0)
            assert False
        except ValueError as e:
            assert "log_loss returned inf" in str(e)
        assert weighted.__name__ == "weighted"
        """,
        hints=["`def wrapper(*args, **kwargs)` and `func(*args, **kwargs)` forward any call."],
        solution="""
        import functools
        import math

        def check_finite(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                result = func(*args, **kwargs)
                if not math.isfinite(result):
                    raise ValueError(f"{func.__name__} returned {result}")
                return result
            return wrapper
        """,
        why="""A wrapper with fixed parameters only fits functions with the same signature: `weighted(2, 4)` passed two arguments to a
        wrapper that takes one, and `w=1` was rejected too. `*args` collects every positional argument into a tuple and `**kwargs`
        every keyword argument into a dict, and the call `func(*args, **kwargs)` unpacks them back exactly as given (3.2), so the
        original function does its own argument checking. Checking for NaN and infinity after a loss computation is a cheap guard
        that catches a diverging training run at the first bad step."""),
    write("Reject None arguments by name", "medium", tag="Data work",
        prompt="""Write a decorator `no_none` that raises `TypeError(f"{param} must not be None")` before calling the function if
        any argument, positional or keyword, **including defaults**, is `None`, naming the parameter. Use
        `inspect.signature(func).bind(*args, **kwargs)` and `apply_defaults()`.""",
        code="""
        import functools, inspect

        def no_none(func):
            pass
        """,
        tests="""
        calls = []

        @no_none
        def chunk(text, size=200, overlap=None):
            calls.append(text)
            return [text[i:i + size] for i in range(0, len(text), size)]

        try:
            chunk("abc", 2)
            assert False, "overlap defaults to None"
        except TypeError as e:
            assert str(e) == "overlap must not be None"

        @no_none
        def label(text, model="small"):
            calls.append(text)
            return f"{model}:{text}"

        assert label("hi") == "small:hi" and label("hi", model="big") == "big:hi"
        try:
            label(None)
            assert False
        except TypeError as e:
            assert str(e) == "text must not be None"
        try:
            label("x", model=None)
            assert False
        except TypeError as e:
            assert "model" in str(e)
        assert calls == ["hi", "hi"]
        """,
        hints=["`bound = inspect.signature(func).bind(*args, **kwargs)`; `bound.apply_defaults()`; then loop over `bound.arguments.items()`.",
               "Compute the signature once, in the decorator body, not on every call."],
        solution="""
        import functools, inspect

        def no_none(func):
            sig = inspect.signature(func)

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                for name, value in bound.arguments.items():
                    if value is None:
                        raise TypeError(f"{name} must not be None")
                return func(*args, **kwargs)
            return wrapper
        """,
        why="""`*args` and `**kwargs` alone do not tell the wrapper which parameter a value belongs to; binding them to the signature does,
        exactly as Python would when calling the function, and `apply_defaults` fills in parameters that were not passed. The
        signature is computed once, at decoration time, because inspecting a function is comparatively slow and the result never
        changes. The check runs before the call, so the function body never sees bad input, which the `calls` list confirms. This is a
        tiny version of what Pydantic's `@validate_call` does with full type checking (11.4)."""),
    choose("Decorate once or wrap on every call", "medium",
        prompt="Both call a timed version of `f` 100,000 times. Which is faster?",
        setup="""import functools, time

def timed(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            wrapper.last = time.perf_counter() - start
    return wrapper

def f(x):
    return x + 1

timed_f = timed(f)""",
        options={
            "a": "for i in range(100_000):\n    timed(f)(i)",
            "b": "for i in range(100_000):\n    timed_f(i)",
        },
        answer="b",
        hints=["What work does `timed(f)` do each time it is evaluated?"],
        why="""Every `timed(f)` runs the whole decorator: it creates a new wrapper function and runs `functools.wraps`, which copies the
        name, docstring, module, qualified name and `__dict__` onto it. Version A pays that on every iteration, plus the call; version
        B decorated once and only pays for the call. The `@` syntax always decorates once, at definition time, which is the intended
        use. Wrapping inside a loop also creates a new wrapper with fresh state each time, so a counter or cache in the decorator would
        never accumulate anything."""),
    trace("Separate state per decorated function", "medium",
        prompt="Fill in `a_calls` and `b_calls` after each marked line.",
        code="""
        import functools

        def counted(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                wrapper.calls += 1
                return func(*args, **kwargs)
            wrapper.calls = 0
            return wrapper

        @counted
        def a(x):
            return x * 2

        @counted
        def b(x):
            return a(x) + a(x)

        a_calls, b_calls = a.calls, b.calls  # row: "after definitions"
        a(1)
        a_calls, b_calls = a.calls, b.calls  # row: "after a(1)"
        b(1)
        a_calls, b_calls = a.calls, b.calls  # row: "after b(1)"
        counted(a)(5)
        a_calls, b_calls = a.calls, b.calls  # row: "after counted(a)(5)"
        """,
        trace_vars=["a_calls", "b_calls"],
        hints=["Inside `b`, the name `a` refers to the decorated `a`.", "`counted(a)` creates a new wrapper around the already-decorated `a`."],
        why="""Each decoration creates its own wrapper with its own `calls`, starting at 0. `b(1)` counts one call to `b` and, because `b` calls
        the name `a`, which is the decorated wrapper, two calls to `a`. `counted(a)` wraps the decorated `a` again: the new outer
        wrapper counts its own call on a throwaway object (its counter starts at 0 again), and the inner wrapper, which is `a`, counts
        one more call. Decorating an already-decorated function stacks wrappers, the subject of 8.2."""),
    fix("A tracing decorator that swallows errors", "medium", tag="GenAI",
        prompt="""`observe` records each call's outcome in `EVENTS`. When the decorated function fails, the error is recorded but the
        caller receives `None` instead of the exception, so a failed model call looks like an empty answer. Fix it: record, then let
        the exception propagate unchanged.""",
        code="""
        import functools

        EVENTS = []

        def observe(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    result = func(*args, **kwargs)
                    EVENTS.append((func.__name__, "ok"))
                    return result
                except Exception as e:
                    EVENTS.append((func.__name__, f"error: {e}"))
            return wrapper
        """,
        tests="""
        @observe
        def complete(prompt):
            if prompt == "timeout":
                raise TimeoutError("model did not answer")
            return prompt.upper()

        assert complete("hi") == "HI"
        try:
            complete("timeout")
            assert False, "the error must reach the caller"
        except TimeoutError as e:
            assert str(e) == "model did not answer"
        assert EVENTS == [("complete", "ok"), ("complete", "error: model did not answer")]
        """,
        hints=["After recording, a bare `raise` re-raises the exception being handled."],
        solution="""
        import functools

        EVENTS = []

        def observe(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    result = func(*args, **kwargs)
                except Exception as e:
                    EVENTS.append((func.__name__, f"error: {e}"))
                    raise
                EVENTS.append((func.__name__, "ok"))
                return result
            return wrapper
        """,
        why="""An `except` block that does not re-raise **handles** the exception; after it, the wrapper fell off the end and returned `None`.
        An observability decorator must never change behaviour, so it records and re-raises with a bare `raise`, which keeps the
        original type, message and traceback (7.2). Moving the success bookkeeping out of the `try` block also keeps a failure in the
        logging itself from being reported as a failure of the function."""),
    refactor("Repeated boilerplate into a decorator", "medium", tag="GenAI",
        prompt="Move the repeated timing and logging into a decorator `logged(func)`, applied to both functions. Same results and same `LOG` entries. Keep the tests green.",
        code="""
        LOG = []

        def retrieve(query, clock):
            start = clock()
            try:
                return [query + " doc"]
            finally:
                LOG.append(("retrieve", round(clock() - start, 3)))

        def generate(query, docs, clock):
            start = clock()
            try:
                if not docs:
                    raise ValueError("no docs")
                return f"answer to {query} from {len(docs)} docs"
            finally:
                LOG.append(("generate", round(clock() - start, 3)))
        """,
        tests="""
        ticks = iter([0.0, 0.25, 1.0, 1.5, 2.0, 2.125])
        clock = lambda: next(ticks)
        docs = retrieve("refund", clock)
        assert generate("refund", docs, clock) == "answer to refund from 1 docs"
        try:
            generate("x", [], clock)
        except ValueError:
            pass
        assert LOG == [("retrieve", 0.25), ("generate", 0.5), ("generate", 0.125)]
        assert generate.__name__ == "generate"
        """,
        hints=["The wrapper finds the clock in `kwargs` or as the last positional argument: here it is always the last positional argument, `args[-1]`."],
        solution="""
        import functools

        LOG = []

        def logged(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                clock = args[-1]
                start = clock()
                try:
                    return func(*args, **kwargs)
                finally:
                    LOG.append((func.__name__, round(clock() - start, 3)))
            return wrapper

        @logged
        def retrieve(query, clock):
            return [query + " doc"]

        @logged
        def generate(query, docs, clock):
            if not docs:
                raise ValueError("no docs")
            return f"answer to {query} from {len(docs)} docs"
        """,
        why="""The two functions now contain only their real logic, and the cross-cutting part lives in one place, so changing the log format
        or adding a metric is a single edit. `func.__name__` replaces the hard-coded names. Taking the clock from the arguments is a
        compromise forced by this test; a real timing decorator would use `time.perf_counter` directly, or receive the clock when the
        decorator is created, which is exactly what decorator factories allow (8.2)."""),
    predict("What the decorator returns becomes the name", "medium",
        code="""
        REGISTRY = {}

        def register(func):
            REGISTRY[func.__name__] = func
            return func                      # the original, unchanged

        def describe(func):
            return f"<function {func.__name__}>"   # not a function at all

        @register
        def search(q):
            return [q]

        @describe
        def fetch(doc_id):
            return doc_id

        print(search("x"), REGISTRY["search"] is search)
        print(type(fetch).__name__, fetch)
        try:
            fetch(1)
        except TypeError as e:
            print("TypeError:", e)
        """,
        hints=["Whatever the decorator returns is bound to the name, whatever it is."],
        why="""`register` records the function and returns it unchanged, so `search` is still the original function and the registry holds the
        same object: the registration pattern of 8.4, with no wrapper at all. `describe` returns a string, so after decoration the name
        `fetch` refers to that string, and calling it fails. Python does not require a decorator to return a function; it simply binds
        the name to the result."""),
)

section("hard", "Hard",
    write("A small memoizer", "hard", tag="ML",
        prompt="""Write a decorator `memo` that caches results by arguments. The key combines the positional arguments and the
        keyword arguments sorted by name, so `f(1, b=2)` and `f(1, b=2)` share an entry (but `f(1, 2)` is a different key). If the
        arguments are unhashable (a list, a dict), call the function without caching. Expose the cache as `wrapper.cache` (a dict) and
        a `wrapper.cache_clear()` function. Use `functools.wraps`.""",
        code="""
        import functools

        def memo(func):
            pass
        """,
        tests="""
        calls = []

        @memo
        def embed(text, model="small"):
            calls.append((text, model))
            return [len(text), len(model)]

        assert embed("hi") == [2, 5] and embed("hi") == [2, 5] and calls == [("hi", "small")]
        embed("hi", model="large"); embed("hi", model="large")
        assert calls == [("hi", "small"), ("hi", "large")] and len(embed.cache) == 2

        @memo
        def total(xs):
            calls.append(tuple(xs))
            return sum(xs)
        assert total([1, 2]) == 3 and total([1, 2]) == 3 and calls[-2:] == [(1, 2), (1, 2)]
        assert total.cache == {}
        embed.cache_clear()
        assert embed.cache == {} and embed.__name__ == "embed"
        """,
        hints=["`key = (args, tuple(sorted(kwargs.items())))`. Test hashability with `hash(key)` inside `try` / `except TypeError`.",
               "`wrapper.cache = {}` and `wrapper.cache_clear = wrapper.cache.clear`."],
        solution="""
        import functools

        def memo(func):
            cache = {}

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                key = (args, tuple(sorted(kwargs.items())))
                try:
                    hash(key)
                except TypeError:
                    return func(*args, **kwargs)
                if key not in cache:
                    cache[key] = func(*args, **kwargs)
                return cache[key]

            wrapper.cache = cache
            wrapper.cache_clear = cache.clear
            return wrapper
        """,
        why="""A dict lookup by the argument tuple is the whole idea of memoization, and it only works for hashable keys, which is why lists
        bypass the cache instead of crashing. Sorting the keyword items makes `f(a=1, b=2)` and `f(b=2, a=1)` the same key. The
        `hash(key)` check is done separately so that a `TypeError` raised **inside** `func` is never mistaken for an unhashable key.
        Note that the cache returns the **same** list object each time, so a caller that modifies the returned list modifies the cached
        value too (2.2); caching functions that return mutable objects needs care. `functools.lru_cache` (8.3) is the production
        version, with a size limit and statistics; it treats `f(1, 2)` and `f(1, b=2)` as different keys too."""),
    fix("Read the code: a stats decorator", "hard", tag="GenAI",
        prompt="""This decorator collects per-function statistics for an LLM service dashboard: in `STATS[name]`, the number of
        calls, the number of errors and the total seconds, using an injected `clock`. On the dashboard, every function shows up as
        `wrapper` with the combined numbers, failed calls are missing from the counts, and the decorated functions have lost their
        names. Read it, find the bugs and fix them.""",
        code="""
        STATS = {}


        def with_stats(func, clock):
            def wrapper(*args, **kwargs):
                start = clock()
                result = func(*args, **kwargs)
                entry = STATS.setdefault(wrapper.__name__, {"calls": 0, "errors": 0, "seconds": 0.0})
                entry["calls"] += 1
                entry["seconds"] += clock() - start
                return result
            return wrapper
        """,
        tests="""
        ticks = iter([0.0, 1.5, 10.0, 10.25, 20.0, 22.0])
        clock = lambda: next(ticks)

        def complete(prompt):
            if prompt == "bad":
                raise ValueError("invalid prompt")
            return prompt[::-1]

        def embed(text):
            return [len(text)]

        complete = with_stats(complete, clock)
        embed = with_stats(embed, clock)
        assert complete("abc") == "cba" and embed("xy") == [2]
        try:
            complete("bad")
            assert False
        except ValueError:
            pass
        assert STATS == {"complete": {"calls": 2, "errors": 1, "seconds": 3.5}, "embed": {"calls": 1, "errors": 0, "seconds": 0.25}}
        assert complete.__name__ == "complete" and embed.__name__ == "embed"
        """,
        hints=["Key the stats by `func.__name__`, the original's name.", "Use `try` / `except` / `finally` so errors are counted and the time is recorded either way, and re-raise.", "Add `functools.wraps(func)`."],
        solution="""
        import functools

        STATS = {}


        def with_stats(func, clock):
            entry = STATS.setdefault(func.__name__, {"calls": 0, "errors": 0, "seconds": 0.0})

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start = clock()
                entry["calls"] += 1
                try:
                    return func(*args, **kwargs)
                except Exception:
                    entry["errors"] += 1
                    raise
                finally:
                    entry["seconds"] += clock() - start
            return wrapper
        """,
        why="""Three bugs. The stats were keyed by `wrapper.__name__`, which is `"wrapper"` for **every** decorated function (no `wraps`),
        so all functions shared one entry; keying by `func.__name__` gives each its own. Failed calls skipped all the bookkeeping,
        because the exception left the wrapper before the counting lines: the dashboard showed a 100% success rate for a function that
        was failing. With `try`/`except`/`finally`, every call is counted, errors are counted, the elapsed time is always added, and the
        exception still propagates. Finally, `functools.wraps` restores the names for tracebacks and frameworks. Creating the stats
        entry once at decoration time also means functions that have never been called appear on the dashboard with zeros. Taking the
        clock as a second parameter means this cannot be used with `@` directly; 8.2 shows how a decorator factory fixes that."""),
    write("Decorate a generator properly", "hard", tag="GenAI",
        prompt="""Streaming functions are generators, and a normal wrapper finishes before the stream starts. Write a decorator
        `stream_stats(func)` for **generator functions**: its wrapper must itself be a generator that yields every item of the original, and when the stream ends, appends `(name, item_count, status)` to the global
        list `STREAMS`, where status is `"complete"`, `"closed"` (the consumer stopped early) or the exception's type name. Exceptions
        must propagate. Use `functools.wraps`.""",
        code="""
        import functools

        STREAMS = []

        def stream_stats(func):
            pass
        """,
        tests="""
        import inspect

        @stream_stats
        def tokens(text, fail_at=None):
            for i, word in enumerate(text.split()):
                if i == fail_at:
                    raise ConnectionError("stream dropped")
                yield word

        assert inspect.isgeneratorfunction(tokens) and tokens.__name__ == "tokens"
        g = tokens("refunds take five days")
        assert STREAMS == []
        assert list(g) == ["refunds", "take", "five", "days"]
        g = tokens("a b c d")
        assert next(g) == "a" and next(g) == "b"
        g.close()
        try:
            list(tokens("x y z", fail_at=2))
            assert False
        except ConnectionError:
            pass
        assert STREAMS == [("tokens", 4, "complete"), ("tokens", 2, "closed"), ("tokens", 2, "ConnectionError")]
        """,
        hints=["Inside the wrapper, `for item in func(*args, **kwargs): count += 1; yield item`.",
               "Closing a generator raises `GeneratorExit` at its paused `yield` (6.3); catch it to record `\"closed\"`, then re-raise. Append in `finally`."],
        solution="""
        import functools

        STREAMS = []

        def stream_stats(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                count, status = 0, "complete"
                try:
                    for item in func(*args, **kwargs):
                        count += 1
                        yield item
                except GeneratorExit:
                    status = "closed"
                    raise
                except Exception as e:
                    status = type(e).__name__
                    raise
                finally:
                    STREAMS.append((func.__name__, count, status))
            return wrapper
        """,
        why="""Because the wrapper contains `yield`, it is a generator function itself, so calling `tokens(...)` creates a generator and runs
        nothing, exactly like the original; the test checks that `STREAMS` is still empty at that point. The bookkeeping happens when
        the wrapper's loop ends, which is when the stream really ends. `GeneratorExit` is how Python tells a paused generator it is
        being closed (by `close()`, or when it is garbage collected after the consumer breaks out of a loop); it is a `BaseException`,
        not an `Exception`, so it needs its own clause and must be re-raised. Counting items as they pass is exactly how streaming
        LLM tracers measure time to first token and the number of chunks. `yield from func(...)` would forward items more simply but
        would not let the wrapper count them."""),
    predict("Recursion through the wrapper", "hard",
        code="""
        import functools

        def counted(func):
            @functools.wraps(func)
            def wrapper(*args):
                wrapper.calls += 1
                return func(*args)
            wrapper.calls = 0
            return wrapper

        @counted
        def fib(n):
            return n if n < 2 else fib(n - 1) + fib(n - 2)

        print(fib(5), fib.calls)
        fib.calls = 0
        print(fib.__wrapped__(5), fib.calls)
        """,
        hints=["Inside `fib`, the name `fib` is looked up when the call happens, and it refers to the wrapper.",
               "Calling `__wrapped__` skips the wrapper only for the outermost call."],
        why="""Every recursive call looks up the global name `fib`, which is the wrapper, so all 15 calls of the recursion tree for `fib(5)` are
        counted. Calling `fib.__wrapped__(5)` skips the wrapper for the first call only: the original body still calls `fib` by name,
        so the 14 nested calls go through the wrapper again. This is why memoizing a recursive function with a decorator works (each
        nested call can hit the cache, 8.3), and why logging decorators on recursive functions produce floods of entries."""),
)

section("interview", "Interview questions",
    explain("What is a decorator in Python, and what exactly does the `@` syntax do?", "medium", tag="Interview",
        why="""A decorator is a callable that takes a function (or class) and returns a replacement, usually a wrapper that calls the original
        with extra behaviour before or after. `@decorator` on the line above a `def` is pure syntax: after the function is defined,
        Python calls `decorator(func)` and binds the function's name to whatever it returns. So `@d` / `def f` is equivalent to `def f`
        followed by `f = d(f)`. The decorator runs once, at definition time (usually import time); the wrapper runs on every call. With
        several decorators, they are applied bottom-up (8.2). Because the result can be anything, a decorator can return a wrapper,
        the original function unchanged (registration), or even a different kind of object (`property` returns a descriptor). It
        relies on functions being first-class objects and on closures to remember the original."""),
    explain("Why should every wrapper use `functools.wraps`?", "medium", tag="Interview",
        why="""Without it, the decorated name refers to a wrapper that presents itself as the wrapper: `__name__` is `"wrapper"`, the docstring
        is lost, `__module__` and `__qualname__` are wrong, and `inspect.signature` reports `(*args, **kwargs)`. That breaks logs and
        tracebacks (every decorated function appears as "wrapper"), documentation and `help()`, test reports, and any tool that keys on
        the name (metrics, registries, caches). It also breaks frameworks that introspect signatures, such as FastAPI's dependency
        injection, pytest fixtures and agent frameworks that build tool schemas from parameters. `functools.wraps(func)` copies the
        metadata and the function's `__dict__`, and sets `__wrapped__`, which `inspect` follows to find the real signature, and which
        gives tests access to the undecorated function."""),
    explain("How would you add tracing to every LLM call in a codebase with a decorator, and what can go wrong?", "hard", tag="Interview",
        why="""Write a decorator that, around each call, records the function name, a sanitised view of the inputs, the output or error type,
        duration, and model metadata such as token usage, and sends it to a tracing backend (or use an existing one: LangSmith's
        `@traceable`, Langfuse's `@observe`, OpenTelemetry spans), nesting child calls under the current trace so a RAG request shows
        retrieval, reranking and generation as one tree. Pitfalls: the decorator must never change behaviour, so it re-raises
        exceptions and returns results untouched, and failures in the tracing itself must be contained; it must use `functools.wraps`
        so names and signatures survive for frameworks; generator and `async` functions need generator and `async` wrappers, or
        streaming calls are measured wrongly; logging full prompts and outputs can leak personal data, so redact or sample; it adds
        overhead on hot paths, so keep the wrapper cheap and send data asynchronously; and recursion or retries inside a decorated
        function produce many nested entries, which should be grouped. Finally, test it with a fake backend to confirm that results,
        exceptions and streaming are unchanged."""),
)

recap(
    "A decorator takes a function and returns a replacement; `@d` above `def f` means `f = d(f)`, run once at definition time.",
    "The wrapper pattern: `def wrapper(*args, **kwargs)`, work before, `result = func(*args, **kwargs)`, work after, `return result`.",
    "Never lose the result or the exception: return what the function returned, and re-raise with a bare `raise`; use `finally` for work that must always happen.",
    "Always `@functools.wraps(func)`: it keeps the name, docstring and signature (via `__wrapped__`) that logs, tests and frameworks rely on.",
    "Recursive calls go through the wrapper; generators and `async` functions need wrappers of the same kind.",
)
