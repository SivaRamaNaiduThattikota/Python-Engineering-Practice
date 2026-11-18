from lesson import *
from diagrams import *

lesson(
    id="m8-p", num="8.P", title="Module 8 practice set and mini project",
    intro="Mixed problems from all of Module 8: wrappers and `functools.wraps`, decorator factories and stacking order, "
          "caching, retries and timing, and registration with signature introspection. Then a mini project that needs all "
          "of it: a small tool framework for an agent, with generated schemas, caching, retries and statistics.",
    desc="Mixed problems from the whole module, then one small program that uses all of it.",
    keys="practice mixed review project tool framework agent registry schema cache retry stats decorator factory wraps stacking feature flag once generator guard",
)

section("how", "How to use this page",
    fig(stage_map(8, "a tool framework for an agent"), "Module 8 at a glance: from wrapping one function to decorators with settings, caching and registration, building up to a tool framework."),
    p("""For every decorator, ask three questions. **What runs when?** The factory and the decorator run once, at definition time; the
    wrapper runs on every call (8.1, 8.2). **What does the name end up bound to?** A wrapper (then `functools.wraps` is mandatory), the
    original function (registration, 8.4), or something else. **What must the wrapper never change?** The arguments, the return
    value and the exceptions, unless changing them is the decorator's stated purpose (8.1). And with several decorators, decide the
    order on purpose: the top one is the outermost layer (8.2)."""),
    p("""The problems mix the lessons on purpose. The mini project at the end combines all of them in one small framework of the kind
    agent libraries provide."""),
)

section("set", "Practice set",
    predict("Two moments and a name", "easy",
        code="""
        import functools

        def stamp(func):
            print("stamping", func.__name__)
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return f"[{func.__name__}] " + func(*args, **kwargs)
            return wrapper

        print("start")

        @stamp
        def reply(text, *, polite=False):
            return ("Please: " if polite else "") + text

        print(reply("hi"), "|", reply("hi", polite=True))
        print(reply.__name__, reply.__wrapped__("raw"))
        """,
        hints=["The decorator body runs when the `def` statement runs; `__wrapped__` is the original."],
        why=""""start" prints first because it comes before the `def`; "stamping reply" prints when the decorated function is defined. Calls go
        through the wrapper, which adds the prefix and forwards the keyword argument unchanged. `wraps` keeps the name and provides
        `__wrapped__`, which calls the original function without the prefix."""),
    write("Check the return type", "easy", tag="GenAI",
        prompt="""Write a decorator factory `returns(*types)` that checks the decorated function's result is an instance of one of
        `types` and raises `TypeError(f"{name} returned {type_name}, expected {expected}")` otherwise, where `expected` is the type names
        joined with `" or "`. Use `functools.wraps`.""",
        code="""
        import functools

        def returns(*types):
            pass
        """,
        tests="""
        @returns(str)
        def summarise(text):
            return text[:10] if text else None

        @returns(int, float)
        def score(x):
            return x

        assert summarise("refund policy text") == "refund pol" and score(3) == 3 and score(0.5) == 0.5
        try:
            summarise("")
            assert False
        except TypeError as e:
            assert str(e) == "summarise returned NoneType, expected str"
        try:
            score("high")
            assert False
        except TypeError as e:
            assert str(e) == "score returned str, expected int or float"
        assert summarise.__name__ == "summarise"
        """,
        hints=["`isinstance(result, types)` accepts a tuple of types directly."],
        solution="""
        import functools

        def returns(*types):
            expected = " or ".join(t.__name__ for t in types)

            def decorator(func):
                @functools.wraps(func)
                def wrapper(*args, **kwargs):
                    result = func(*args, **kwargs)
                    if not isinstance(result, types):
                        raise TypeError(f"{func.__name__} returned {type(result).__name__}, expected {expected}")
                    return result
                return wrapper
            return decorator
        """,
        why="""The expected-types text is built once in the factory, and `isinstance` with a tuple covers several types in one check. A
        function that sometimes returns `None` instead of a string is a classic source of errors far downstream (a prompt containing
        the text `"None"`); checking at the boundary turns it into an immediate, precise error. Static type checkers catch many such
        problems before running (11.1), but data from models and APIs can still surprise you at run time."""),
    fix("A factory with a missing level", "easy", tag="Data work",
        prompt="""`truncate(n)` should be used as `@truncate(5)` to cut the decorated function's list result to `n` items. Decorating
        fails at import with a `TypeError`. Fix the factory.""",
        code="""
        import functools

        def truncate(n):
            @functools.wraps(n)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)[:n]
            return wrapper
        """,
        tests="""
        @truncate(2)
        def top_docs(q):
            return [f"{q}-{i}" for i in range(5)]

        assert top_docs("refund") == ["refund-0", "refund-1"]
        assert top_docs.__name__ == "top_docs"
        """,
        hints=["A decorator with arguments needs three levels: the factory takes `n`, the decorator takes `func`, the wrapper takes the call's arguments."],
        solution="""
        import functools

        def truncate(n):
            def decorator(func):
                @functools.wraps(func)
                def wrapper(*args, **kwargs):
                    return func(*args, **kwargs)[:n]
                return wrapper
            return decorator
        """,
        why="""`@truncate(2)` first calls `truncate(2)`, and whatever that returns is applied to the function. The broken version returned
        `wrapper` directly, after applying `functools.wraps(2)` to it, which fails because an integer has no function attributes; even
        without that, the function would have been passed to `wrapper` as an argument. The middle level, `decorator(func)`, is what
        receives the function and gives `func` a meaning inside the wrapper's closure (8.2)."""),
    predict("Layers and a cache", "medium",
        code="""
        import functools

        LOG = []

        def logged(func):
            @functools.wraps(func)
            def wrapper(x):
                LOG.append(func.__name__)
                return func(x)
            return wrapper

        @logged
        @functools.lru_cache(maxsize=None)
        def outer_log(x):
            return x * 2

        @functools.lru_cache(maxsize=None)
        @logged
        def inner_log(x):
            return x * 3

        for x in [1, 1, 2, 1]:
            outer_log(x); inner_log(x)
        print(LOG.count("outer_log"), LOG.count("inner_log"))
        print(outer_log.__wrapped__.cache_info().hits, inner_log.cache_info().hits)
        """,
        hints=["A cache placed outside the logger answers hits before the logger runs."],
        why="""For `outer_log`, the logger is outermost, so all four calls are logged, even the two that the cache answers. For `inner_log`, the
        cache is outermost, so only the two misses reach the logger. `outer_log.__wrapped__` is the cached function inside the logger
        (thanks to `wraps`), with 2 hits; `inner_log` is itself the cache, also with 2 hits. Same cache, same hits, different logging,
        purely because of the order."""),
    write("Versioned prompt registry", "medium", tag="GenAI",
        prompt="""Write a decorator factory `prompt(name, version)` that registers the decorated function in the global dict `PROMPTS`
        under `(name, version)`, sets `func.prompt_name` and `func.prompt_version`, raises `ValueError` if that pair is already
        registered, and returns the function. Then write `latest(name)` returning the registered function with the highest version
        for `name` (versions are integers), raising `KeyError(name)` if there is none.""",
        code="""
        PROMPTS = {}

        def prompt(name, version):
            pass

        def latest(name):
            pass
        """,
        tests="""
        @prompt("summary", 1)
        def summary_v1(text):
            return f"Summarise: {text}"

        @prompt("summary", 3)
        def summary_v3(text):
            return f"Summarise in 3 bullet points: {text}"

        @prompt("summary", 2)
        def summary_v2(text):
            return f"Summarise briefly: {text}"

        @prompt("qa", 1)
        def qa_v1(context, q):
            return f"{context}\\nQ: {q}"

        assert latest("summary") is summary_v3 and latest("summary")("x").startswith("Summarise in 3")
        assert summary_v2.prompt_version == 2 and summary_v2.prompt_name == "summary" and latest("qa") is qa_v1
        try:
            prompt("summary", 2)(lambda t: t)
            assert False
        except ValueError:
            pass
        try:
            latest("translate")
            assert False
        except KeyError:
            pass
        """,
        hints=["`latest` filters the keys with `key[0] == name` and takes `max` by version."],
        solution="""
        PROMPTS = {}

        def prompt(name, version):
            def decorator(func):
                key = (name, version)
                if key in PROMPTS:
                    raise ValueError(f"prompt {name!r} version {version} is already registered")
                func.prompt_name = name
                func.prompt_version = version
                PROMPTS[key] = func
                return func
            return decorator

        def latest(name):
            versions = [v for (n, v) in PROMPTS if n == name]
            if not versions:
                raise KeyError(name)
            return PROMPTS[(name, max(versions))]
        """,
        why="""Prompts change often, and comparing versions in evaluations requires keeping the old ones; a registry keyed by name and version
        does that, and the attributes on each function let traces and logs record which version produced an answer. Registration order
        does not matter, because `latest` picks the maximum version, not the last one registered (v2 was defined after v3). The
        duplicate check catches a copy-pasted decorator at import. Production systems often store prompt versions outside the code
        (a prompt management tool or a database), but the lookup logic is the same."""),
    fix("A framework that cannot see the parameters", "medium", tag="GenAI",
        prompt="""A mini framework calls handlers with values taken **by parameter name** from a request dict, using
        `inspect.signature`. After `@audit` was added, every handler fails with a missing argument. Fix the decorator so the framework
        sees the real parameters.""",
        code="""
        import inspect

        AUDIT = []

        def audit(func):
            def wrapper(*args, **kwargs):
                AUDIT.append(func.__name__)
                return func(*args, **kwargs)
            return wrapper

        def call_handler(handler, request):
            names = inspect.signature(handler).parameters
            return handler(**{n: request[n] for n in names if n in request})
        """,
        tests="""
        @audit
        def get_order(order_id, user):
            return f"order {order_id} for {user}"

        request = {"order_id": 7, "user": "ana", "trace_id": "t1"}
        assert call_handler(get_order, request) == "order 7 for ana"
        assert AUDIT == ["get_order"] and get_order.__name__ == "get_order"
        """,
        hints=["Without `functools.wraps`, `inspect.signature` sees the wrapper's `(*args, **kwargs)`."],
        solution="""
        import functools
        import inspect

        AUDIT = []

        def audit(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                AUDIT.append(func.__name__)
                return func(*args, **kwargs)
            return wrapper

        def call_handler(handler, request):
            names = inspect.signature(handler).parameters
            return handler(**{n: request[n] for n in names if n in request})
        """,
        why="""The framework asked the decorated function for its parameters and got `args` and `kwargs`, neither of which is in the request, so it
        called the handler with nothing. `functools.wraps` sets `__wrapped__`, and `inspect.signature` follows it to the original's
        `(order_id, user)`. This is precisely how a decorator without `wraps` breaks FastAPI routes, pytest fixtures and agent tool
        schemas: the code still runs, but every tool that introspects it is misled (8.1, 8.4)."""),
    write("Run once, then reuse", "medium", tag="ML",
        prompt="""Loading a model or creating a client should happen once, lazily, on first use. Write a decorator `once` for functions
        without arguments: the first call runs the function and stores its result; later calls return the stored result without
        calling it again. If the first call raises, nothing is stored and the next call tries again. Provide `wrapper.reset()` to
        forget the stored result. Use `functools.wraps`.""",
        code="""
        import functools

        def once(func):
            pass
        """,
        tests="""
        loads = []
        attempts = iter([ConnectionError("hub unreachable"), "model-v1", "model-v2"])

        @once
        def load_model():
            loads.append(1)
            out = next(attempts)
            if isinstance(out, Exception):
                raise out
            return out

        try:
            load_model()
            assert False
        except ConnectionError:
            pass
        assert load_model() == "model-v1" and load_model() == "model-v1" and len(loads) == 2
        load_model.reset()
        assert load_model() == "model-v2" and len(loads) == 3 and load_model.__name__ == "load_model"
        """,
        hints=["Use a private sentinel `_UNSET = object()` (2.1) to tell \"not loaded yet\" apart from a function that returns `None`.",
               "Keep the state in a one-item dict or with `nonlocal`, so `reset` can change it."],
        solution="""
        import functools

        _UNSET = object()

        def once(func):
            state = {"value": _UNSET}

            @functools.wraps(func)
            def wrapper():
                if state["value"] is _UNSET:
                    state["value"] = func()
                return state["value"]

            def reset():
                state["value"] = _UNSET

            wrapper.reset = reset
            return wrapper
        """,
        why="""The sentinel distinguishes "never loaded" from "loaded, and the result happens to be `None`", which a plain `None` check would get
        wrong (2.1). If `func()` raises, the assignment never happens, so the state stays unset and the next call retries: a transient
        failure at start-up does not leave the process permanently broken. `functools.cache` on a zero-argument function gives the
        same caching but no simple per-function reset and no retry semantics you control. In threaded servers, two requests could both
        see the unset state and load twice; a lock around the check fixes that (14.2)."""),
    choose("Recursive edit distance: plain or cached", "medium", tag="ML",
        prompt="Both compute the edit distance between two 7-character words with the same recursive definition. Which is faster?",
        setup="""import functools

def dist(a, b):
    if not a:
        return len(b)
    if not b:
        return len(a)
    if a[0] == b[0]:
        return dist(a[1:], b[1:])
    return 1 + min(dist(a[1:], b), dist(a, b[1:]), dist(a[1:], b[1:]))

@functools.lru_cache(maxsize=None)
def cdist(a, b):
    if not a:
        return len(b)
    if not b:
        return len(a)
    if a[0] == b[0]:
        return cdist(a[1:], b[1:])
    return 1 + min(cdist(a[1:], b), cdist(a, b[1:]), cdist(a[1:], b[1:]))

x, y = "refunds", "rufands" """,
        options={
            "a": "d = dist(x, y)",
            "b": "cdist.cache_clear()\nd = cdist(x, y)",
        },
        answer="b",
        hints=["How many times does the plain version solve the same pair of suffixes?"],
        why="""The plain recursion branches three ways at every mismatch and solves the same `(suffix, suffix)` pairs over and over, so its work
        grows exponentially with the length. The cached version solves each of the at most 8 x 8 suffix pairs once; every repeated
        sub-problem is a dictionary lookup, because the recursive calls go through the cached wrapper (8.1). This is dynamic programming
        by memoization, the subject of 16.5. Clearing the cache inside the measured code makes the comparison fair: every run starts
        empty."""),
    trace("Counting through a registry", "medium",
        prompt="Fill in `calls` and `names` after each marked line.",
        code="""
        import functools

        REG = {}
        calls = {}

        def counted(func):
            @functools.wraps(func)
            def wrapper(*args):
                calls[func.__name__] = calls.get(func.__name__, 0) + 1
                return func(*args)
            return wrapper

        def reg(func):
            REG[func.__name__] = func
            return func

        @reg
        @counted
        def a(x):
            return x

        @counted
        @reg
        def b(x):
            return x

        names = sorted(REG)  # row: "after definitions"
        REG["a"](1); REG["b"](1)
        names = sorted(REG)  # row: "through the registry"
        a(1); b(1)
        names = sorted(REG)  # row: "by name"
        """,
        trace_vars=["calls", "names"],
        hints=["`a` registered its counted wrapper; `b` registered the plain function and was wrapped afterwards."],
        why="""Both functions are registered, under their own names. Through the registry, `a` is counted (its registered object is the counted
        wrapper) but `b` is not, because `reg` saw `b` before `counted` wrapped it. Called by name, both go through their counted
        wrappers. The difference is only the order of the two decorators."""),
    refactor("Inline retries and timing into decorators", "medium", tag="GenAI",
        prompt="Move the retry loop and the timing into two decorators, `retrying(attempts)` and `timed`, and apply them so the behaviour and `TIMES` stay the same. Keep the tests green.",
        code="""
        TIMES = []
        ticks = iter(range(0, 1000, 5))
        clock = lambda: next(ticks)

        def fetch(q, flaky):
            start = clock()
            try:
                for attempt in range(1, 4):
                    try:
                        if flaky and attempt < 3:
                            raise TimeoutError("slow")
                        return f"result for {q}"
                    except TimeoutError:
                        if attempt == 3:
                            raise
            finally:
                TIMES.append(clock() - start)
        """,
        tests="""
        assert fetch("refund", flaky=False) == "result for refund"
        assert fetch("reset", flaky=True) == "result for reset"
        assert TIMES == [5, 5]
        assert fetch.__name__ == "fetch"
        """,
        hints=["The timing covers all attempts, so `@timed` must be the outer decorator.",
               "Inside the decorated function, failures must depend on an attempt counter; keep it in a small dict keyed by the query."],
        solution="""
        import functools

        TIMES = []
        ticks = iter(range(0, 1000, 5))
        clock = lambda: next(ticks)

        def timed(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start = clock()
                try:
                    return func(*args, **kwargs)
                finally:
                    TIMES.append(clock() - start)
            return wrapper

        def retrying(attempts):
            def decorator(func):
                @functools.wraps(func)
                def wrapper(*args, **kwargs):
                    for attempt in range(1, attempts + 1):
                        try:
                            return func(*args, **kwargs)
                        except TimeoutError:
                            if attempt == attempts:
                                raise
                return wrapper
            return decorator

        _tries = {}

        @timed
        @retrying(attempts=3)
        def fetch(q, flaky):
            _tries[q] = _tries.get(q, 0) + 1
            if flaky and _tries[q] < 3:
                raise TimeoutError("slow")
            return f"result for {q}"
        """,
        why="""The original mixed three concerns in one function: the real work, retrying and timing. With decorators, `fetch` contains only the
        work, and the two policies are reusable and visible in its header. `@timed` sits on top so the measurement covers the whole retry
        sequence, as before; the clock is read twice per call either way, so `TIMES` is unchanged. The attempt counter had to move into
        state that survives across calls, because each retry is now a separate call of the inner function, a small sign of how
        decorators separate "the attempt" from "the policy". In real code the flakiness would come from the network, not a counter."""),
    write("Stop a stream at a size limit", "hard", tag="GenAI",
        prompt="""Write a decorator factory `max_chars(limit)` for **generator functions** that yield text chunks. The wrapper yields the
        chunks unchanged until the total length would exceed `limit`; it then yields only the part of that chunk that fits (if any),
        **closes** the underlying generator, sets `wrapper.truncated = True` and stops. If the stream ends within the limit,
        `wrapper.truncated` is `False`. Use `functools.wraps`.""",
        code="""
        import functools

        def max_chars(limit):
            pass
        """,
        tests="""
        closed = []

        @max_chars(12)
        def answer(chunks):
            try:
                for c in chunks:
                    yield c
            finally:
                closed.append(True)

        assert "".join(answer(["Refunds ", "take five ", "days."])) == "Refunds take"
        assert answer.truncated is True and closed == [True]
        assert list(answer(["short", " one"])) == ["short", " one"] and answer.truncated is False
        assert list(answer(["exactly12chr"])) == ["exactly12chr"] and answer.truncated is False
        assert list(answer(["123456789012", "3"])) == ["123456789012"] and answer.truncated is True
        assert answer.__name__ == "answer"
        """,
        hints=["Keep a running total. Create the inner generator yourself, `gen = func(*args, **kwargs)`, so you can call `gen.close()`.",
               "If `total + len(chunk) > limit`, yield `chunk[:limit - total]` if it is not empty, close, mark truncated, `return`."],
        solution="""
        import functools

        def max_chars(limit):
            def decorator(func):
                @functools.wraps(func)
                def wrapper(*args, **kwargs):
                    wrapper.truncated = False
                    total = 0
                    gen = func(*args, **kwargs)
                    try:
                        for chunk in gen:
                            if total + len(chunk) > limit:
                                rest = chunk[:limit - total]
                                if rest:
                                    yield rest
                                wrapper.truncated = True
                                return
                            total += len(chunk)
                            yield chunk
                    finally:
                        gen.close()
                wrapper.truncated = False
                return wrapper
            return decorator
        """,
        why="""The wrapper is itself a generator (8.1), so the limit is applied while streaming, chunk by chunk, and the consumer receives text as
        soon as it arrives. Holding a reference to the inner generator lets the wrapper **close** it as soon as the limit is reached,
        which runs its `finally` block (the test's `closed` list); in a real stream, that is where the HTTP connection to the provider is
        released, so you stop paying for tokens you will discard. The `finally` in the wrapper also closes the source when the consumer
        itself stops early. Exactly reaching the limit is not truncation; only a chunk that would exceed it is. Guards like this protect
        UIs and logs from runaway generations."""),
    fix("Read the code: a feature-flag decorator", "hard", tag="ML",
        prompt="""`@feature(name, fallback)` should route calls to the decorated function when `FLAGS[name]` is true **at call time**,
        and to `fallback` with the same arguments otherwise; it should keep the function's name, and record each choice in `ROUTED`.
        Turning a flag on at run time has no effect, the fallback receives the wrong arguments, and the name is lost. Read it, find the
        bugs and fix them.""",
        code="""
        FLAGS = {"new_ranker": False}
        ROUTED = []


        def feature(name, fallback):
            enabled = FLAGS.get(name, False)

            def decorator(func):
                def wrapper(*args, **kwargs):
                    if enabled:
                        ROUTED.append(func.__name__)
                        return func(*args, **kwargs)
                    ROUTED.append(fallback.__name__)
                    return fallback(*args)
                return wrapper
            return decorator
        """,
        tests="""
        def old_rank(docs, *, top=3):
            return sorted(docs)[:top]

        @feature("new_ranker", fallback=old_rank)
        def new_rank(docs, *, top=3):
            return sorted(docs, key=len)[:top]

        docs = ["ccc", "a", "bb", "dddd"]
        assert new_rank(docs, top=2) == ["a", "bb"] and ROUTED == ["old_rank"]
        FLAGS["new_ranker"] = True
        assert new_rank(docs, top=2) == ["a", "bb"] and new_rank(["zz", "y"], top=1) == ["y"]
        FLAGS["new_ranker"] = False
        assert new_rank(["zz", "y"], top=1) == ["y"]
        assert ROUTED == ["old_rank", "new_rank", "new_rank", "old_rank"]
        assert new_rank.__name__ == "new_rank"
        FLAGS["new_ranker"] = True
        assert new_rank(["zz", "yyy", "x"], top=2) == ["x", "zz"]
        """,
        hints=["`enabled` is computed once, in the factory, at import time. Read `FLAGS.get(name, False)` inside the wrapper.",
               "`fallback(*args)` drops the keyword arguments. And add `functools.wraps`."],
        solution="""
        import functools

        FLAGS = {"new_ranker": False}
        ROUTED = []


        def feature(name, fallback):
            def decorator(func):
                @functools.wraps(func)
                def wrapper(*args, **kwargs):
                    if FLAGS.get(name, False):
                        ROUTED.append(func.__name__)
                        return func(*args, **kwargs)
                    ROUTED.append(fallback.__name__)
                    return fallback(*args, **kwargs)
                return wrapper
            return decorator
        """,
        why="""Three bugs. The flag was read in the factory, which runs once at import (8.2), so the value was frozen at `False` and flipping the flag
        later did nothing; a feature flag must be read on each call. The fallback received only `*args`, so `top=2` was silently
        dropped and it used its default of 3, returning the wrong number of results without any error. And without `functools.wraps`,
        traces and the routing log of other tools would show `wrapper`. Feature flags like this let a team roll out a new retriever or
        prompt to some traffic and compare metrics, with the old path as an instant rollback; the two implementations must accept the
        same arguments, which the test checks with a keyword argument."""),
    explain("When should you not use a decorator?", "medium", tag="Interview",
        why="""When the behaviour is not cross-cutting, or when it needs to vary per call. A decorator applies the same policy to every call of a
        function, fixed at definition time, which is ideal for logging, timing, caching, registration and simple retries, but awkward when
        the caller must choose (a timeout per request, a retry policy per endpoint, a different model per tenant); pass a parameter or use
        an explicit client object instead. Avoid decorators that change a function's signature or return type in surprising ways, that
        hide important control flow (a decorator that sometimes skips the call), or that accumulate so many settings they become a
        configuration language. Stacks of five decorators make the order of effects hard to see. And remember the practical limits:
        generators and `async` functions need matching wrappers, recursion goes through the wrapper, and introspection needs
        `functools.wraps`. A plain function call inside the body is often the clearest choice."""),
    explain("How do you test code that uses decorators?", "hard", tag="Interview",
        why="""Test the decorator itself once, with tiny fake functions: that it returns results and raises exceptions unchanged, preserves the
        name and signature, and applies its policy (number of retries, cache hits, recorded timings) correctly; inject the clock,
        `sleep` and random generator so those tests run instantly. Then test decorated business functions without the decorator's side
        effects when they get in the way: call `func.__wrapped__` to reach the original, clear caches between tests with `cache_clear()`
        (or a fixture that does it automatically, 13.2), and give registries a fresh instance per test instead of a global dict. For
        registration, assert that importing the module registers what you expect, and that duplicates fail. For decorators that read
        configuration, test both values of each flag, and test that the value is read at the intended time. Finally, include a few tests
        through the real decorated path, because the composition order of stacked decorators is itself behaviour worth checking."""),
    predict("Everything at once", "hard",
        code="""
        import functools

        REG = {}

        def tool(name=None):
            def decorator(func):
                REG[name or func.__name__] = func
                return func
            return decorator

        def shout(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs).upper()
            return wrapper

        @tool("loud_hello")
        @shout
        @functools.lru_cache(maxsize=None)
        def hello(name):
            print("computing", name)
            return f"hello {name}"

        print(REG["loud_hello"]("ana"), hello("ana"), hello("bo"))
        print(hello.__wrapped__.cache_info().hits, list(REG), hello.__name__)
        """,
        hints=["Bottom-up: cache, then the shouting wrapper, then registration of the shouting wrapper."],
        why="""The cache is innermost, the uppercasing wrapper goes around it, and the registry receives that wrapper under the name `loud_hello`,
        returning it unchanged, so `REG["loud_hello"]` and `hello` are the same object. `"ana"` is computed once (the print appears once)
        and the second call is a cache hit; `"bo"` is computed. `hello.__wrapped__` is the cached function, with one hit. All three
        results are upper-cased, since every call passes through `shout`. The arguments of `print` are evaluated left to right, so both
        "computing" lines appear before the results."""),
)

section("project", "Mini project: a tool framework for an agent",
    fig(chain(["@tool registers|functions", "schemas from|signatures", "model picks a tool", "dispatch with|validation", ("result or error|back to the model", "good")]),
        "The tool framework: registration, schemas, dispatch and error handling, each a decorator pattern from this module."),
    p("""Agent libraries let you turn plain functions into tools with a decorator. Build a small version: tools are registered with
    metadata, their schemas are generated from signatures and type hints, idempotent tools can be cached, flaky ones retried, every
    call goes through one dispatcher that validates arguments and returns errors the model can act on, and per-tool statistics are
    kept. Every rule in the spec maps to a lesson in this module."""),
    write("Build the toolkit", "hard", key="toolkit", tag="Project",
        prompt="""Implement `make_toolkit()` returning `(tool, run, schemas, stats)`.

        - **`tool(*, description=None, cache=False, retries=0, retry_on=(TimeoutError,))`** is a decorator factory. It registers the
          function under its name (duplicates raise `ValueError`), with the description or else the first docstring line. Every
          parameter must have a type annotation among `str`, `int`, `float`, `bool`, or `TypeError` is raised at decoration time. It
          returns the function unchanged.
        - **`schemas()`** returns a list, sorted by tool name, of `{"name", "description", "parameters": {"type": "object",
          "properties": {p: {"type": json_type}}, "required": [...]}}`.
        - **`run(name, args)`** returns `{"result": value}` or `{"error": message}`: `"unknown tool 'x'"`; `"bad arguments: <bind
          error>"` for missing or unknown arguments. Then it calls the tool: with `cache=True`, results are cached by
          `(name, sorted argument items)`; with `retries=n`, an exception in `retry_on` is retried up to `n` more times, and if it still
          fails, `run` returns `{"error": "<name> failed: <Type>: <message>"}`. Any other exception propagates.
        - **`stats()`** returns `{name: {"calls": c, "cache_hits": h, "errors": e}}` for every registered tool, where `calls` counts
          `run` calls that reached the tool (cache hits included) and `errors` counts calls that ended in a returned failure.""",
        code="""
        import inspect, typing

        JSON_TYPES = {str: "string", int: "integer", float: "number", bool: "boolean"}


        def make_toolkit():
            pass
        """,
        tests="""
        tool, run, schemas, stats = make_toolkit()
        hits = []

        @tool(cache=True)
        def get_order(order_id: int) -> dict:
            \"\"\"Look up an order by id.

            More detail here.
            \"\"\"
            hits.append(order_id)
            return {"id": order_id, "status": "shipped"}

        flaky = iter([TimeoutError("slow"), TimeoutError("slow again"), "ok"])

        @tool(description="Search the help centre.", retries=2)
        def search(query: str, limit: int = 3):
            out = next(flaky)
            if isinstance(out, Exception):
                raise out
            return [f"{query}-{i}" for i in range(limit)]

        @tool(retries=1)
        def ping(host: str):
            raise TimeoutError(f"{host} timed out")

        assert [s["name"] for s in schemas()] == ["get_order", "ping", "search"]
        assert schemas()[0] == {"name": "get_order", "description": "Look up an order by id.",
                                "parameters": {"type": "object", "properties": {"order_id": {"type": "integer"}}, "required": ["order_id"]}}
        assert schemas()[2]["parameters"]["required"] == ["query"] and schemas()[2]["description"] == "Search the help centre."

        assert run("get_order", {"order_id": 7}) == {"result": {"id": 7, "status": "shipped"}}
        assert run("get_order", {"order_id": 7})["result"]["id"] == 7 and hits == [7]
        assert run("search", {"query": "refund", "limit": 2}) == {"result": ["refund-0", "refund-1"]}
        assert run("ping", {"host": "db"}) == {"error": "ping failed: TimeoutError: db timed out"}
        assert run("cancel", {}) == {"error": "unknown tool 'cancel'"}
        assert run("get_order", {}) == {"error": "bad arguments: missing a required argument: 'order_id'"}
        assert stats() == {"get_order": {"calls": 2, "cache_hits": 1, "errors": 0},
                           "search": {"calls": 1, "cache_hits": 0, "errors": 0},
                           "ping": {"calls": 1, "cache_hits": 0, "errors": 1}}

        try:
            @tool()
            def get_order(order_id: int):
                return {}
            assert False, "duplicate"
        except ValueError:
            pass
        try:
            @tool()
            def untyped(x):
                return x
            assert False, "no annotation"
        except TypeError:
            pass

        @tool()
        def boom(n: int):
            raise KeyError("bug")
        try:
            run("boom", {"n": 1})
            assert False
        except KeyError:
            pass
        assert get_order(1) == {"id": 1, "status": "shipped"}
        """,
        hints=["Keep one dict of entries, `name -> {\"func\", \"description\", \"schema\", \"cache\", \"retries\", \"retry_on\", \"stats\"}`, filled by the decorator; build the schema there, at decoration time.",
               "In `run`: look up, `inspect.signature(func).bind(**args)` for argument errors, then the cache check, then the retry loop around the call.",
               "The cache dict can live in the entry; the key is `tuple(sorted(args.items()))`."],
        solution="""
        import inspect, typing

        JSON_TYPES = {str: "string", int: "integer", float: "number", bool: "boolean"}


        def _schema(func, description):
            hints = typing.get_type_hints(func)
            props, required = {}, []
            for pname, p in inspect.signature(func).parameters.items():
                kind = hints.get(pname)
                if kind not in JSON_TYPES:
                    raise TypeError(f"{func.__name__}: parameter {pname!r} needs a str, int, float or bool annotation")
                props[pname] = {"type": JSON_TYPES[kind]}
                if p.default is p.empty:
                    required.append(pname)
            return {"name": func.__name__, "description": description,
                    "parameters": {"type": "object", "properties": props, "required": required}}


        def make_toolkit():
            entries = {}

            def tool(*, description=None, cache=False, retries=0, retry_on=(TimeoutError,)):
                def decorator(func):
                    name = func.__name__
                    if name in entries:
                        raise ValueError(f"tool {name!r} is already registered")
                    doc = inspect.getdoc(func) or ""
                    desc = description or (doc.splitlines()[0] if doc else "")
                    entries[name] = {
                        "func": func,
                        "schema": _schema(func, desc),
                        "cache": {} if cache else None,
                        "retries": retries,
                        "retry_on": retry_on,
                        "stats": {"calls": 0, "cache_hits": 0, "errors": 0},
                    }
                    return func
                return decorator

            def run(name, args):
                entry = entries.get(name)
                if entry is None:
                    return {"error": f"unknown tool {name!r}"}
                func = entry["func"]
                try:
                    inspect.signature(func).bind(**args)
                except TypeError as e:
                    return {"error": f"bad arguments: {e}"}
                entry["stats"]["calls"] += 1
                key = tuple(sorted(args.items()))
                if entry["cache"] is not None and key in entry["cache"]:
                    entry["stats"]["cache_hits"] += 1
                    return {"result": entry["cache"][key]}
                for attempt in range(entry["retries"] + 1):
                    try:
                        result = func(**args)
                    except entry["retry_on"] as e:
                        if attempt == entry["retries"]:
                            entry["stats"]["errors"] += 1
                            return {"error": f"{name} failed: {type(e).__name__}: {e}"}
                        continue
                    if entry["cache"] is not None:
                        entry["cache"][key] = result
                    return {"result": result}

            def schemas():
                return [entries[n]["schema"] for n in sorted(entries)]

            def stats():
                return {n: dict(e["stats"]) for n, e in entries.items()}

            return tool, run, schemas, stats
        """,
        why="""Every lesson of the module has a job here:

        - **Decorator factories (8.2):** `@tool(cache=True)` and `@tool(retries=2)` carry settings, validated and stored when the module is
          imported; settings are keyword-only, so `@tool` cannot be misused positionally without an error.
        - **Registration and introspection (8.4):** the decorator returns the function unchanged (so `get_order(1)` still works
          directly), refuses duplicates, and generates each schema once from the signature, the type hints and the docstring, so the
          schemas the model sees can never drift from the code. Unannotated parameters fail at import, not when the model calls them.
        - **Caching and retries (8.3):** the cache key is built from sorted argument items, so argument order does not matter; only
          successful results are cached; only the configured transient errors are retried, and a final failure becomes a message for
          the model rather than a crash, while a `KeyError` from a bug propagates (7.3).
        - **Wrapper rules (8.1):** nothing about the tools' behaviour changes; the policies live in the dispatcher, and statistics
          record calls, hits and returned errors per tool.

        Putting caching and retries in `run` rather than in wrappers around each function keeps the registered object identical to the
        user's function, which makes tools easy to test directly. Real frameworks add timeouts, permissions and tracing in the same
        dispatcher, and build parameter validation from Pydantic models (11.4)."""),
)

recap(
    "Decorators run once at definition time; wrappers run per call and must pass arguments, results and exceptions through unchanged.",
    "Every wrapper gets `functools.wraps`: names, signatures and `__wrapped__` are what frameworks, logs and tests rely on.",
    "Factories validate settings at import; read anything dynamic (flags, limits) at call time.",
    "Order is behaviour: registration outermost, caches outside what they should skip, timers outside retries when measuring the user's wait.",
    "Registries plus `inspect.signature` and type hints turn plain functions into routes, commands and tools.",
)
