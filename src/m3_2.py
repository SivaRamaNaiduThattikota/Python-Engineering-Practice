from lesson import *

lesson(
    id="m3-2", num="3.2", title="Flexible arguments",
    intro="`*args`, `**kwargs`, keyword-only and positional-only parameters, and unpacking at the call site: what each "
          "one does step by step, why they exist, and the real bugs they cause and prevent in LLM clients, wrappers and "
          "config code.",
    desc="`*args`, `**kwargs`, keyword-only and positional-only parameters, unpacking calls.",
    keys="args kwargs star double star keyword only positional only slash parameter kinds unpacking call site spread forward wrapper boolean trap multiple values keywords must be strings inspect bind",
)

term("*args", "A parameter that collects any extra positional arguments into a new tuple.")
term("**kwargs", "A parameter that collects any extra keyword arguments into a new dict, in the order they were passed.")
term("Keyword-only parameter", "A parameter after `*` or `*args`: it can only be passed by name, never by position.")
term("Positional-only parameter", "A parameter before `/`: it can only be passed by position, so its name is free for `**kwargs` to use.")
term("Unpacking a call", "`f(*seq)` spreads a sequence into positional arguments, `f(**mapping)` spreads a dict into keyword arguments.")

section("kinds", "The five kinds of parameters",
    p("""A signature can contain up to five kinds of parameters, always in this order. Each kind answers one question:
    **how may a caller pass this value?**"""),
    html("""<div class="tbl"><table>
      <tr><th>Kind</th><th>Written as</th><th>By position?</th><th>By name?</th><th>Typical use</th></tr>
      <tr><td>positional-only</td><td>before <code>/</code></td><td>yes</td><td>no</td><td>names that must stay free, or may change later</td></tr>
      <tr><td>positional-or-keyword</td><td>plain <code>x</code></td><td>yes</td><td>yes</td><td>the normal case</td></tr>
      <tr><td>var-positional</td><td><code>*args</code></td><td>collects extras</td><td>no</td><td>any number of values</td></tr>
      <tr><td>keyword-only</td><td>after <code>*</code> or <code>*args</code></td><td>no</td><td>yes</td><td>options and flags</td></tr>
      <tr><td>var-keyword</td><td><code>**kwargs</code></td><td>no</td><td>collects extras</td><td>options passed through to other code</td></tr>
    </table></div>"""),
    p("""Here is one signature using all five, so you can see the order rule in action. It is the shape of a small
    database helper: the SQL text first, optional parameters, any extra statements, a timeout that must be named, and
    driver options passed through untouched:"""),
    ex("""
    def run_query(sql, /, params=None, *more_sql, timeout=30, **driver_opts):
        return {"sql": sql, "params": params, "more_sql": more_sql,
                "timeout": timeout, "driver_opts": driver_opts}

    print(run_query("SELECT 1"))
    print(run_query("SELECT 1", {"id": 7}, "SELECT 2", timeout=5, fetch_size=500))
    """, "five_kinds.py"),
    p("""Walk through the second call with the algorithm from 3.1. Positional arguments fill left to right:
    `"SELECT 1"` goes to `sql`, `{"id": 7}` to `params`, and `"SELECT 2"`, the extra one, is collected into the
    tuple `more_sql`. Then keywords by name: `timeout=5` fills the keyword-only `timeout`, and `fetch_size=500` matches no
    parameter, so it is collected into the dict `driver_opts`. Anything after `*more_sql` can only be reached by name, which
    is why `timeout` is safe from being filled by accident. In practice you rarely use all five in one function, but every
    signature you meet in a library is some subset of this table."""),
)

section("args", "`*args`: collecting extra positional arguments",
    p("""A parameter written `*name` (by convention `*args`) collects every positional argument that no earlier parameter
    took. Step by step, on every call Python builds a **new tuple** from the leftover positional arguments and binds the
    name to it. With no leftovers it is the empty tuple `()`, never `None`. Being a tuple, it cannot be changed, but its
    items are the caller's own objects (2.4)."""),
    ex("""
    def merge_tags(*tag_lists):
        print("received:", tag_lists)
        merged = []
        for tags in tag_lists:
            for t in tags:
                if t not in merged:
                    merged.append(t)
        return merged

    print(merge_tags(["faq", "billing"], ["billing", "eu"], ["faq"]))
    print(merge_tags())
    groups = [["a"], ["b", "a"]]
    print(merge_tags(groups))      # one argument: a list of lists
    print(merge_tags(*groups))     # spread: two arguments
    """, "star_args.py"),
    p("""The last two calls show the most common `*args` mistake. `merge_tags(groups)` passes **one** argument, a list
    that contains lists, so `tag_lists` is a tuple holding that one list and the loop sees the inner lists as "tags".
    `merge_tags(*groups)` **spreads** the list, so each inner list becomes its own argument. When a function takes
    `*args` and you already have the values in a list, you almost always want the `*` at the call."""),
    callout("note", "When `*args` is the right design", """Use `*args` when "any number of the same kind of thing" is the
    natural way to call the function: `print(a, b, c)`, `max(x, y, z)`, `os.path.join("a", "b", "c")`,
    `merge_tags(t1, t2)`. If callers will usually have a list already, take the list as one normal parameter instead.
    It is simpler, and it does not copy a large list into a tuple on every call (problem 8)."""),
)

section("kwargs", "`**kwargs`: collecting extra keyword arguments",
    p("""A parameter written `**name` (by convention `**kwargs`) collects every keyword argument that did not match a named
    parameter. On each call Python builds a **new dict** from those leftovers, with the keys in the order the caller wrote
    them, and binds the name to it. With no leftovers it is an empty dict. Because it is a new dict, the function may add
    or remove keys freely without affecting the caller; the values are still the caller's objects."""),
    ex("""
    def make_request(prompt, **params):
        params.setdefault("temperature", 0.2)     # changes only this call's dict
        return {"prompt": prompt, **params}

    settings = {"max_tokens": 256, "stop": ["###"]}
    print(make_request("hi"))
    print(make_request("hi", **settings, top_p=0.9))
    print(settings)                               # untouched: params was a new dict
    """, "star_kwargs.py"),
    p("""Two rules limit what can go into `**kwargs`. Keys must be **strings**, because they become parameter names.
    And a key can never be the name of another parameter of the same function, because then it would not be "extra":
    Python would try to give that parameter two values. The second rule causes a real bug, shown in the next section."""),
    callout("warn", "The cost of `**kwargs`", """`**kwargs` makes a function accept anything, which also means typos are
    accepted silently: `make_request("hi", temprature=0.9)` sends a misspelled key to the API instead of failing in your
    code. Use it where you truly pass options through to other code (an SDK, a driver, a model constructor). For your own
    options, prefer named keyword-only parameters, which catch typos at the call."""),
)

section("markers", "Why `*` and `/` exist",
    p("""A bare `*` in a signature collects nothing: it only marks every parameter after it as **keyword-only**. The main
    reason is the **boolean trap**. A call like `train(X, y, True, False)` is unreadable, and swapping the two booleans
    changes behaviour without any error. With keyword-only flags, the call must say `train(X, y, normalize=True,
    verbose=False)`, and the positional version fails immediately."""),
    ex("""
    def train(X, y, *, normalize=True, verbose=False):
        return f"normalize={normalize}, verbose={verbose}"

    print(train([[1]], [0], verbose=True))
    try:
        train([[1]], [0], True, False)
    except TypeError as e:
        print("TypeError:", e)
    """, "keyword_only.py"),
    p("""A `/` marks every parameter **before** it as **positional-only**: callers cannot use its name. That sounds like a
    restriction, but it solves a real problem: a function with `**kwargs` cannot accept a key that is also the name of one
    of its parameters. Step by step: Python fills `name` from the first positional argument, then meets the keyword
    `name=...` from the dict and tries to fill `name` again, which is the "multiple values" error. Making `name`
    positional-only takes it out of the keyword namespace, so `**fields` can receive a `name` key."""),
    ex("""
    def tag_v1(name, **fields):
        return name, fields

    def tag_v2(name, /, **fields):       # name can only be passed by position
        return name, fields

    row = {"name": "Ana", "tier": "gold"}
    try:
        tag_v1("customer", **row)
    except TypeError as e:
        print("TypeError:", e)
    print(tag_v2("customer", **row))
    """, "positional_only.py"),
    p("""Positional-only parameters also let a library rename a parameter later without breaking anyone, because no
    caller can have used the name. Many built-ins are positional-only for that reason: you cannot write `len(obj=x)`."""),
)

section("unpacking", "Unpacking at the call site",
    p("""The same symbols work in the opposite direction in a **call**. `f(*seq)` spreads any iterable into separate
    positional arguments; `f(**mapping)` spreads a dict into keyword arguments. You can use several of each, mixed with
    normal arguments, and Python processes them left to right with the same matching algorithm as always."""),
    ex("""
    def connect(host, port, *, user, timeout=10):
        return f"{user}@{host}:{port} (timeout {timeout})"

    addr = ["db.local", 1521]
    base = {"user": "etl"}
    print(connect(*addr, **base))
    print(connect(*addr, **base, timeout=3))

    defaults = {"user": "etl", "timeout": 10}
    override = {"timeout": 3}
    try:
        connect(*addr, **defaults, **override)
    except TypeError as e:
        print("TypeError:", e)
    print(connect(*addr, **(defaults | override)))
    """, "unpacking.py"),
    p("""The `TypeError` is worth understanding. In a **call**, `**defaults, **override` are spread one after the other, and
    each key becomes a keyword argument; a key that appears in both is the same keyword given twice, which Python refuses
    with "got multiple values for keyword argument". In a **dict display**, `{**defaults, **override}` (or
    `defaults | override`), a repeated key is allowed and the later value wins. So when you mean "defaults, then
    overrides", merge first into one dict and spread that dict once."""),
)

section("forwarding", "Forwarding: wrappers that accept anything",
    p("""Collecting and spreading combine into the **forwarding** pattern: accept `*args, **kwargs` and pass them on
    unchanged with `fn(*args, **kwargs)`. A wrapper written this way works for any function, whatever its signature,
    which is how retry helpers, timers, caches, loggers and decorators (Module 7) are built."""),
    ex("""
    import time

    def timed(fn, *args, **kwargs):
        start = time.perf_counter()
        result = fn(*args, **kwargs)         # forward exactly what was given
        elapsed = time.perf_counter() - start
        print(f"{fn.__name__} took {'under' if elapsed < 0.1 else 'over'} 0.1 s")
        return result

    def embed(texts, *, model="small"):
        return [len(t) for t in texts]

    print(timed(embed, ["a", "bcd"], model="large"))
    print(timed(sorted, [3, 1, 2], reverse=True))
    """, "forwarding.py"),
    p("""Forwarding has two costs to know about. First, a parameter of the wrapper itself (here `fn`) can collide with a
    keyword the wrapped function needs: `timed(f, fn=3)` gives `timed` two values for `fn`. Making the wrapper's own
    parameters positional-only (`def timed(fn, /, *args, **kwargs)`) avoids that. Second, `*args, **kwargs` hides the real
    signature from editors, type checkers and frameworks that read signatures (3.1). Decorators fix the second problem with
    `functools.wraps` (Module 7), and type checkers with `ParamSpec` (Module 11)."""),
)

section("warmup", "Warm-up",
    predict("Which calls work?", "easy",
        code="""
        def run_query(sql, /, params=None, *more_sql, timeout=30, **opts):
            return f"{sql} | {params} | {more_sql} | {timeout} | {opts}"

        calls = [
            'run_query("Q1")',
            'run_query("Q1", None, "Q2", "Q3")',
            'run_query("Q1", timeout=5, retries=2)',
            'run_query(sql="Q1")',
            'run_query("Q1", {"a": 1}, 60)',
        ]
        for c in calls:
            try:
                print(eval(c))
            except TypeError as e:
                print("TypeError:", e)
        """,
        hints=["Use the table: which parameters can be filled by position, and which only by name?",
               "In the last call, can `60` reach `timeout`?"],
        why="""Call 2 puts `"Q2"` and `"Q3"` into the tuple `more_sql`. Call 3 fills the keyword-only `timeout` and collects
        `retries` into `opts`. Call 4 fails because `sql` is positional-only, so `sql=` is not allowed; in fact the keyword is
        not even treated as an error for `sql` but collected into `**opts`, and then `sql` is reported missing. Call 5 is the
        trap: `60` is a positional argument, so it lands in `more_sql`, not in `timeout`, and the timeout silently stays 30.
        That is exactly why options like `timeout` should sit after the `*`: by position they can never be reached."""),
    write("Merge any number of tag lists", "easy", tag="Data work",
        prompt="""Write `merge_tags(*tag_lists)` that takes any number of tag lists and returns one list of the distinct
        tags, lower-cased, in first-seen order. With no arguments it returns `[]`.""",
        code="""
        def merge_tags(*tag_lists):
            pass
        """,
        tests="""
        assert merge_tags(["FAQ", "billing"], ["Billing", "eu"], ["faq"]) == ["faq", "billing", "eu"]
        assert merge_tags() == []
        assert merge_tags(["x"]) == ["x"]
        groups = [["a"], ["b", "A"]]
        assert merge_tags(*groups) == ["a", "b"]
        """,
        hints=["Loop over `tag_lists` (a tuple of lists), then over each list. A `dict.fromkeys` keeps first-seen order (2.2)."],
        solution="""
        def merge_tags(*tag_lists):
            return list(dict.fromkeys(t.lower() for tags in tag_lists for t in tags))
        """,
        why="""`*tag_lists` arrives as a tuple of the lists, so the nested comprehension reads "each tag in each list".
        `dict.fromkeys` removes repeats while keeping first-seen order, in one pass. The last test is the call-site side:
        with the lists already in `groups`, `merge_tags(*groups)` spreads them into separate arguments."""),
    fix("Flags that can be swapped", "easy", tag="ML",
        prompt="""Someone called `fit(X, y, False, True)` meaning "verbose, no normalisation", and silently got the
        opposite. Change the signature so the two flags can only be passed by name. The tests pass them by keyword and
        check that passing them by position is now an error.""",
        code="""
        def fit(X, y, normalize=True, verbose=False):
            return {"normalize": normalize, "verbose": verbose, "n": len(X)}
        """,
        tests="""
        def raises(exc, f, *args):
            try:
                f(*args)
            except exc:
                return True
            return False
        assert fit([[1], [2]], [0, 1]) == {"normalize": True, "verbose": False, "n": 2}
        assert fit([[1]], [0], verbose=True) == {"normalize": True, "verbose": True, "n": 1}
        assert raises(TypeError, fit, [[1]], [0], False, True)
        """,
        hints=["One character in the signature is enough."],
        solution="""
        def fit(X, y, *, normalize=True, verbose=False):
            return {"normalize": normalize, "verbose": verbose, "n": len(X)}
        """,
        why="""The bare `*` makes everything after it keyword-only, so `fit(X, y, False, True)` now raises
        `TypeError: fit() takes 2 positional arguments but 4 were given` instead of silently doing the wrong thing.
        scikit-learn made this change across its whole API (most estimator options became keyword-only in version 1.0) for
        exactly this reason. Changing a released function like this can break callers, so libraries announce it first."""),
    predict("What `*args` and `**kwargs` look like inside", "easy",
        code="""
        def show(*args, **kwargs):
            return f"args={args} kwargs={kwargs}"

        nums = [1, 2]
        opts = {"sep": "-"}
        print(show())
        print(show(nums, opts))
        print(show(*nums, **opts))
        print(show(*nums, nums, x=None, **opts))
        """,
        hints=["Without `*` or `**` at the call, a list or dict is just one ordinary argument."],
        why="""With no arguments, `args` is `()` and `kwargs` is `{}`. `show(nums, opts)` passes two ordinary arguments, so both
        end up in the tuple and `kwargs` stays empty. Spreading changes everything: `*nums` becomes `1, 2` and `**opts` becomes
        `sep="-"`. Spreads and normal arguments mix freely, and are taken in the order written."""),
)

section("medium", "Medium",
    fix("Defaults plus overrides crash the call", "medium", tag="GenAI",
        prompt="""`run` sends a prompt with the base settings plus any overrides. With no overrides it works, but overriding a
        base setting crashes. Fix it so overrides win.""",
        code="""
        BASE = {"model": "small", "temperature": 0.2}

        def send(**params):
            return params

        def run(prompt, **overrides):
            return send(prompt=prompt, **BASE, **overrides)
        """,
        tests="""
        assert run("hi") == {"prompt": "hi", "model": "small", "temperature": 0.2}
        assert run("hi", temperature=0.9) == {"prompt": "hi", "model": "small", "temperature": 0.9}
        assert run("hi", model="large", stop=["###"]) == {"prompt": "hi", "model": "large", "temperature": 0.2, "stop": ["###"]}
        assert BASE == {"model": "small", "temperature": 0.2}
        """,
        hints=["In a call, the same keyword twice is an error. In a dict display, the later key wins."],
        solution="""
        BASE = {"model": "small", "temperature": 0.2}

        def send(**params):
            return params

        def run(prompt, **overrides):
            return send(prompt=prompt, **(BASE | overrides))
        """,
        why="""`send(**BASE, **overrides)` spreads two dicts as keyword arguments, and a key in both is the same keyword twice:
        `TypeError: ... got multiple values for keyword argument 'temperature'`. `BASE | overrides` merges first, with the
        override winning, and the merged dict is spread once. This bug often hides until someone overrides a setting the
        base already has, which may be weeks after the code was written."""),
    write("A hyperparameter grid from keyword arguments", "medium", tag="ML",
        prompt="""Write `grid(**options)` where each keyword holds a list of values to try. Return a list of dicts, one per
        combination, with keys in the order they were passed and the **last** option changing fastest.
        `grid(lr=[0.1, 0.01], depth=[3, 5])` gives four dicts. With no options, return `[{}]` (one empty combination).""",
        code="""
        import itertools

        def grid(**options):
            pass
        """,
        tests="""
        assert grid(lr=[0.1, 0.01], depth=[3, 5]) == [
            {"lr": 0.1, "depth": 3}, {"lr": 0.1, "depth": 5}, {"lr": 0.01, "depth": 3}, {"lr": 0.01, "depth": 5}]
        assert grid() == [{}]
        assert grid(k=[5]) == [{"k": 5}]
        assert len(grid(a=[1, 2, 3], b=[1, 2], c=[1, 2])) == 12
        """,
        hints=["`options.keys()` keeps the order the caller wrote. `itertools.product(*options.values())` gives every combination as a tuple.",
               "`dict(zip(keys, combo))` turns one tuple back into a dict."],
        solution="""
        import itertools

        def grid(**options):
            keys = list(options)
            return [dict(zip(keys, combo)) for combo in itertools.product(*options.values())]
        """,
        why="""Two things from this lesson meet here. `**options` keeps keyword order, so the keys come out in the order the
        caller wrote them. And `itertools.product(*options.values())` **spreads** the lists into separate arguments, because
        `product` takes each iterable as its own argument (`product([0.1, 0.01], [3, 5])`). With no options, `product()`
        yields one empty tuple, which correctly becomes `[{}]`. This is the core of scikit-learn's `ParameterGrid`; for
        large spaces you would return a generator instead of a list (Module 6) or sample randomly."""),
    fix("A field called `name`", "medium", tag="Data work",
        prompt="""`make_node(label, **fields)` builds a graph node from a database row. It crashes for rows that have a
        `label` column. Fix it so any column name works, including `label`, without changing how it is called.""",
        code="""
        def make_node(label, **fields):
            return {"label": label, "fields": fields}
        """,
        tests="""
        row = {"id": 7, "label": "VIP", "name": "Ana"}
        assert make_node("customer", **row) == {"label": "customer", "fields": {"id": 7, "label": "VIP", "name": "Ana"}}
        assert make_node("product") == {"label": "product", "fields": {}}
        """,
        hints=["Python tries to give the parameter `label` two values: one by position, one from the `label` key.",
               "Which marker takes a parameter's name out of the keyword namespace?"],
        solution="""
        def make_node(label, /, **fields):
            return {"label": label, "fields": fields}
        """,
        why="""Without `/`, the `label` key in `**row` is matched to the parameter `label`, which already has a value from the
        first positional argument: "got multiple values for argument 'label'". The `/` makes `label` positional-only, so a
        keyword named `label` is not a match for it any more and simply lands in `fields`. This is the textbook reason
        positional-only parameters were added (PEP 570): functions that accept arbitrary keyword data need their own
        parameter names to stay out of the way."""),
    choose("Spreading a big list into `*args`", "medium",
        prompt="Both functions return the first item. Which call is faster for a million items?",
        setup="""big = list(range(1_000_000))
def first_star(*xs):
    return xs[0]
def first_list(xs):
    return xs[0]""",
        options={
            "a": "x = first_star(*big)",
            "b": "x = first_list(big)",
        },
        answer="b",
        hints=["What does Python have to build to call a function that takes `*xs`?"],
        why="""Calling `first_star(*big)` spreads a million values into positional arguments, and the function then collects
        them into a brand-new tuple: a full copy of a million references on every call. `first_list(big)` passes one reference
        to the existing list (2.4). Use `*args` for a handful of values given by hand, and a normal parameter when callers
        already have a collection."""),
    write("Retry any function, forwarding its arguments", "medium", tag="GenAI",
        prompt="""Write `with_retry(fn, /, *args, attempts=3, retry_on=(ValueError,), **kwargs)` that calls
        `fn(*args, **kwargs)`, retries when it raises one of the `retry_on` exceptions, and re-raises the last error after
        `attempts` failures. It must work for any function signature, including functions with their own `fn` or
        `attempts`-free keywords.""",
        code="""
        def with_retry(fn, /, *args, attempts=3, retry_on=(ValueError,), **kwargs):
            pass
        """,
        tests="""
        def raises(exc, f, *args, **kw):
            try:
                f(*args, **kw)
            except exc:
                return True
            return False
        def flaky_factory(fails):
            state = {"left": fails}
            def fn(text, *, fn="label"):
                if state["left"]:
                    state["left"] -= 1
                    raise ValueError("bad JSON from model")
                return f"{fn}:{text}"
            return fn
        assert with_retry(flaky_factory(2), "hi") == "label:hi"
        assert with_retry(flaky_factory(0), "hi", fn="tag") == "tag:hi"
        assert raises(ValueError, with_retry, flaky_factory(5), "hi", attempts=2)
        assert raises(KeyError, with_retry, lambda: {}["x"])
        """,
        hints=["Loop `attempts` times; `return fn(*args, **kwargs)` inside `try`, and remember the last exception in the `except`.",
               "Only catch `retry_on`: any other error should escape at once. `except retry_on as e:` works with a tuple."],
        solution="""
        def with_retry(fn, /, *args, attempts=3, retry_on=(ValueError,), **kwargs):
            last = None
            for _ in range(attempts):
                try:
                    return fn(*args, **kwargs)
                except retry_on as e:
                    last = e
            raise last
        """,
        why="""The signature does the hard work. `fn` is positional-only, so the wrapped function can have its own keyword
        called `fn` (the second test) and it is forwarded instead of colliding. `attempts` and `retry_on` sit after `*args`,
        so they are keyword-only and can never swallow one of the wrapped function's positional arguments. Everything else
        is forwarded untouched with `fn(*args, **kwargs)`. The remaining collision is real: a wrapped function that itself
        needs a keyword named `attempts` cannot get it through this wrapper, which is why libraries like `tenacity` configure
        retries in a decorator instead of in the call."""),
    refactor("Build a payload without repeating every option", "medium", tag="GenAI",
        prompt="""This builds an API payload, leaving out options that were not set. It works, but each option is handled by
        its own `if`. Keep the same named parameters (callers and editors rely on them), and remove the repetition. Keep the
        tests green.""",
        code="""
        def make_payload(prompt, temperature=None, top_p=None, max_tokens=None, stop=None):
            payload = {"prompt": prompt}
            if temperature is not None:
                payload["temperature"] = temperature
            if top_p is not None:
                payload["top_p"] = top_p
            if max_tokens is not None:
                payload["max_tokens"] = max_tokens
            if stop is not None:
                payload["stop"] = stop
            return payload
        """,
        tests="""
        assert make_payload("hi") == {"prompt": "hi"}
        assert make_payload("hi", temperature=0, stop=["###"]) == {"prompt": "hi", "temperature": 0, "stop": ["###"]}
        assert list(make_payload("hi", max_tokens=5, top_p=0.9)) == ["prompt", "top_p", "max_tokens"]
        """,
        hints=["Put the options in one dict with `dict(temperature=temperature, ...)`, then keep the ones that are not `None`."],
        solution="""
        def make_payload(prompt, temperature=None, top_p=None, max_tokens=None, stop=None):
            options = dict(temperature=temperature, top_p=top_p, max_tokens=max_tokens, stop=stop)
            return {"prompt": prompt, **{k: v for k, v in options.items() if v is not None}}
        """,
        why="""The named parameters stay, so typos like `temprature=` still fail at the call and editors still show the
        options. Only the repetitive body changed: one dict, one filter with `is not None` (so `temperature=0` is kept), one
        spread. Replacing the signature with `**params` would be shorter but would lose that safety, which is the trade-off
        from this lesson. The last test checks the key order, which comes from the order of the `dict(...)` call."""),
)

section("hard", "Hard",
    predict("Repeated keys: dicts versus calls", "hard",
        code="""
        def f(**kw):
            return kw

        a = {"x": 1}
        b = {"x": 2, "y": 3}
        print({**a, **b})
        print(f(**{**a, **b}))
        try:
            f(**a, **b)
        except TypeError as e:
            print("TypeError:", e)
        print(dict(a, **b))
        try:
            f(**{1: "one"})
        except TypeError as e:
            print("TypeError:", e)
        """,
        hints=["A dict display allows a repeated key (the last wins); a call does not allow a repeated keyword.",
               "Keyword argument names must be strings."],
        why="""In the dict display the later `"x"` wins. Spreading the merged dict once is a normal call. Spreading the two
        dicts separately gives `x` twice, which a call refuses. `dict(a, **b)` is allowed because `a` is a positional argument
        (the starting mapping) and only `b` is spread, so `x` is given once as a keyword and overrides the copy. Finally,
        `**{1: "one"}` fails because keyword names must be strings. Every one of these appears in real config code."""),
    fix("Read the code: a tracing wrapper that leaks a key", "hard", tag="GenAI",
        prompt="""`traced` wraps LLM client functions to log every call. It has two problems: the wrapped functions receive
        the wrong arguments, and the log lines contain the raw API key, which is a security incident waiting to happen. Fix
        both. The key must still reach the wrapped function; only the log must hide it.""",
        code="""
        LOG = []
        SECRET_KEYS = {"api_key", "authorization"}


        def traced(fn, /, *args, **kwargs):
            LOG.append(f"call {fn.__name__} args={args} kwargs={kwargs}")
            result = fn(args, kwargs)
            LOG.append(f"done {fn.__name__}")
            return result


        def complete(prompt, *, model="small", api_key):
            return f"{model} answered {prompt!r} (key ends {api_key[-4:]})"
        """,
        tests="""
        out = traced(complete, "hi", model="large", api_key="sk-test-1234")
        assert out == "large answered 'hi' (key ends 1234)"
        assert "sk-test-1234" not in " ".join(LOG)
        assert "'api_key': '***'" in LOG[0] and "'model': 'large'" in LOG[0]
        assert LOG[-1] == "done complete"
        """,
        hints=["`fn(args, kwargs)` passes two arguments: a tuple and a dict. How do you spread them instead?",
               "Build a separate, redacted copy of `kwargs` for the log line. Do not change `kwargs` itself."],
        solution="""
        LOG = []
        SECRET_KEYS = {"api_key", "authorization"}


        def traced(fn, /, *args, **kwargs):
            shown = {k: ("***" if k in SECRET_KEYS else v) for k, v in kwargs.items()}
            LOG.append(f"call {fn.__name__} args={args} kwargs={shown}")
            result = fn(*args, **kwargs)
            LOG.append(f"done {fn.__name__}")
            return result


        def complete(prompt, *, model="small", api_key):
            return f"{model} answered {prompt!r} (key ends {api_key[-4:]})"
        """,
        why="""`fn(args, kwargs)` passes the tuple as the first positional argument and the dict as the second, so `complete`
        gets `prompt=("hi",)` and complains about a missing `api_key`: forwarding needs the stars, `fn(*args, **kwargs)`. The
        log leak is the more serious bug. The fix builds a **separate** redacted dict for logging; deleting the key from
        `kwargs` would also hide it from the log, but then the real call would fail. Secrets in logs are a common finding in
        LLM application reviews, because tracing wrappers like this one log every argument by default. A real version would
        also redact secrets inside positional arguments and nested values, and would use the `logging` module (Module 12)."""),
    write("Bind arguments exactly the way Python would", "hard", tag="Interview",
        prompt="""Write `bind(fn, *args, **kwargs)` that returns a dict from parameter name to the value it would receive if
        `fn(*args, **kwargs)` were called, **including defaults**, without calling `fn`. Invalid calls must raise
        `TypeError`, just like a real call. Use the `inspect` module rather than reimplementing the rules.""",
        code="""
        import inspect

        def bind(fn, *args, **kwargs):
            pass
        """,
        tests="""
        def raises(exc, f, *args, **kw):
            try:
                f(*args, **kw)
            except exc:
                return True
            return False
        def run_query(sql, /, params=None, *more, timeout=30, **opts):
            raise RuntimeError("must not be called")
        assert bind(run_query, "Q1") == {"sql": "Q1", "params": None, "more": (), "timeout": 30, "opts": {}}
        assert bind(run_query, "Q1", {"a": 1}, "Q2", timeout=5, x=1) == {"sql": "Q1", "params": {"a": 1}, "more": ("Q2",), "timeout": 5, "opts": {"x": 1}}
        assert raises(TypeError, bind, run_query)
        assert raises(TypeError, bind, lambda a, *, b: 0, 1, 2)
        """,
        hints=["`inspect.signature(fn).bind(*args, **kwargs)` checks the call and returns a `BoundArguments` object.",
               "`.apply_defaults()` fills the missing parameters, and `.arguments` is the mapping you need."],
        solution="""
        import inspect

        def bind(fn, *args, **kwargs):
            bound = inspect.signature(fn).bind(*args, **kwargs)
            bound.apply_defaults()
            return dict(bound.arguments)
        """,
        why="""`Signature.bind` runs the same matching algorithm Python uses for a real call (positional, then keywords, then the
        `*args` and `**kwargs` collectors) and raises the same kind of `TypeError` for a bad call, but without running the
        function. `apply_defaults` then fills the defaults, including `()` for `*more` and `{}` for `**opts`. This is how
        caching decorators build a key that treats `f(1, b=2)` and `f(1, 2)` as the same call, and how validation layers check
        a tool call from an LLM before executing it. Knowing the matching rules well enough to predict this table is also a
        frequent interview question."""),
    predict("Keyword-only after `*args`", "hard",
        code="""
        def join(*parts, sep=" ", end="!"):
            return sep.join(parts) + end

        print(join("a", "b"))
        print(join("a", "b", "-"))
        print(join("a", "b", sep="-"))
        print(join(*"xyz", end=""))
        print(join(*["only"], sep="+", end="?"))
        """,
        hints=["Everything positional goes into `parts`. Only a keyword can reach `sep` or `end`.",
               "`*\"xyz\"` spreads a string into its characters."],
        why="""`join("a", "b", "-")` does not set the separator: `"-"` is just a third part, so the result is `"a b -!"`. Only
        `sep="-"` reaches the keyword-only parameter. Spreading a string spreads its characters, because a string is an
        iterable of one-character strings. With a single part there is nothing to separate, so `sep` has no visible effect.
        `print` itself has exactly this signature (`print(*objects, sep=" ", end="\\n")`), which is why `print("a", "-")`
        prints both values rather than using `"-"` as a separator."""),
    write("Call a function from command-line style arguments", "hard", tag="GenAI",
        prompt="""A small CLI turns `["k=5", "rerank=true", "query=refund policy"]` into a call. Write
        `call_from_strings(fn, pairs)` that splits each `"name=value"` string, converts the value to the **type of that
        parameter's default** (`int`, `float`, `bool`, or `str`; a parameter without a default stays a `str`), and calls `fn`
        with keyword arguments. For `bool`, accept `true`/`false`/`1`/`0` in any case. An unknown name must raise `TypeError`
        through the normal call.""",
        code="""
        import inspect

        def call_from_strings(fn, pairs):
            pass
        """,
        tests="""
        def raises(exc, f, *args):
            try:
                f(*args)
            except exc:
                return True
            return False
        def search(query, k=10, threshold=0.5, rerank=False):
            return (query, k, threshold, rerank)
        assert call_from_strings(search, ["k=5", "rerank=TRUE", "query=refund policy"]) == ("refund policy", 5, 0.5, True)
        assert call_from_strings(search, ["query=a=b", "threshold=0.75", "rerank=0"]) == ("a=b", 10, 0.75, False)
        assert raises(TypeError, call_from_strings, search, ["query=x", "kk=3"])
        """,
        hints=["`name, value = pair.split(\"=\", 1)` splits only at the first `=`, so values may contain `=`.",
               "Look up `inspect.signature(fn).parameters.get(name)`. If it has a default, use `type(param.default)` to choose the conversion; `bool(\"false\")` is `True`, so booleans need their own rule."],
        solution="""
        import inspect

        def to_value(text, default):
            if isinstance(default, bool):
                if text.lower() in {"true", "1"}:
                    return True
                if text.lower() in {"false", "0"}:
                    return False
                raise ValueError(f"not a boolean: {text!r}")
            if isinstance(default, (int, float)):
                return type(default)(text)
            return text

        def call_from_strings(fn, pairs):
            params = inspect.signature(fn).parameters
            kwargs = {}
            for pair in pairs:
                name, value = pair.split("=", 1)
                param = params.get(name)
                default = param.default if param is not None else inspect.Parameter.empty
                kwargs[name] = value if default is inspect.Parameter.empty else to_value(value, default)
            return fn(**kwargs)
        """,
        why="""This is a tiny version of what Typer and Click do: they read the signature (3.1) and turn strings into typed
        keyword arguments. Three details matter. `split("=", 1)` keeps any later `=` in the value. The `bool` check comes
        **before** the `int` check, because `bool` is a subclass of `int` (1.1), and `bool("false")` would be `True`, so
        booleans need their own parsing. And unknown names are passed through unconverted, so the normal call raises the usual
        `TypeError` instead of the helper inventing its own error. Building on `**kwargs` and the signature means the same
        helper works for any function."""),
)

section("interview", "Interview questions",
    explain("What do `/` and `*` mean in a function signature, and why would you use each?", "medium", tag="Interview",
        why="""Parameters before `/` are positional-only: callers cannot pass them by name. Parameters after `*` (or after
        `*args`) are keyword-only: callers must pass them by name. Use `*` for options and especially boolean flags, so calls
        are readable and arguments cannot be swapped silently (the boolean trap); scikit-learn made most estimator options
        keyword-only for this reason. Use `/` when a function also takes `**kwargs` and must accept keys that match its own
        parameter names (PEP 570's motivating case), or when you want freedom to rename a parameter later without breaking
        callers. Mention that many built-ins are positional-only, which is why `len(obj=x)` fails."""),
    explain("Why does `f(**a, **b)` fail when the dicts share a key, and how should you merge settings for a call?", "medium", tag="Interview",
        why="""In a call, `**a, **b` spreads both dicts into keyword arguments one after the other, so a key present in both
        is the same keyword passed twice, and Python raises "got multiple values for keyword argument". The fix is to merge
        first into one dict where the later value wins, `a | b` or `{**a, **b}`, and spread that once: `f(**(a | b))`. Being
        explicit about precedence (defaults, then environment, then per-call overrides) avoids silent surprises, and for
        nested settings you need a recursive merge (2.3), because `|` replaces nested dicts wholesale."""),
    explain("What is the downside of a public function with the signature `def f(*args, **kwargs)`?", "hard", tag="Interview",
        why="""It hides the real interface. Editors cannot autocomplete or show the parameters, type checkers cannot check calls,
        typos in keyword names are accepted silently and fail later (or never, if the value is just passed on), the docs and
        `help()` say nothing, and frameworks that read signatures (FastAPI, Typer, agent tool builders) cannot use it. Errors
        appear deep inside the function instead of at the call. It is fine for **forwarding** wrappers, which should then
        restore the wrapped function's metadata with `functools.wraps` and its types with `typing.ParamSpec`, or for true
        pass-through of options to another API, ideally after validating them. For your own public functions, name the
        parameters and make options keyword-only."""),
)

recap(
    "Five kinds, in order: positional-only (`/`), normal, `*args`, keyword-only, `**kwargs`. Each answers \"how may a caller pass this?\"",
    "`*args` is a new tuple and `**kwargs` a new dict on every call. Their values are still the caller's objects.",
    "Use `*` to make options and flags keyword-only (the boolean trap), and `/` when `**kwargs` must accept your own parameter names.",
    "In a call, `*` and `**` spread. A repeated keyword is an error, so merge settings first (`a | b`) and spread once.",
    "Forwarding with `*args, **kwargs` makes generic wrappers, at the cost of hiding the signature. Keep the wrapper's own parameters positional-only or keyword-only.",
)
