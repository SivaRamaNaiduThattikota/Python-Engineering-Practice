from lesson import *

lesson(
    id="m3-5", num="3.5", title="Functions as values",
    intro="Functions are objects you can store, pass and return. That gives you `lambda`, `key=` functions for sorting "
          "and grouping, `map` and `filter`, `functools.partial`, and dispatch tables: the way agents route a tool name "
          "to the code that runs it.",
    desc="`lambda`, `key=` functions, `sorted`, `map`, `filter` and `functools.partial`.",
    keys="first class function higher order lambda key function sorted max min map filter reduce partial operator itemgetter attrgetter dispatch table callback strategy pipeline compose",
)

term("First-class function", "A function that can be treated like any other value: stored in variables and containers, passed as an argument, returned.")
term("Higher-order function", "A function that takes a function as an argument or returns one, such as `sorted(key=...)`, `map` or a decorator.")
term("lambda", "An expression that creates a small, unnamed function: `lambda x: x * 2`. Its body is a single expression.")
term("Key function", "A function passed as `key=` that turns each item into the value used for sorting, `min`, `max` or grouping.")
term("Dispatch table", "A dict from names (or types) to functions, used to pick the code to run instead of a long `if`/`elif` chain.")

section("values", "Functions are values",
    p("""Since `def` simply binds a name to a function object (3.1), a function can go anywhere a value can go. You can
    assign it to another name, put it in a list or dict, pass it to another function, and return it from a function. A
    function that **takes or returns a function** is called a **higher-order function**. You have already used several:
    `sorted(key=...)`, the factories in 3.4, and `with_retry` in 3.2."""),
    ex("""
    def shout(text):
        return text.upper()

    def whisper(text):
        return text.lower()

    styles = {"shout": shout, "whisper": whisper}   # functions stored in a dict
    speak = styles["whisper"]                       # a function assigned to a name
    print(speak("Hello"), styles["shout"]("hello"))

    def apply_twice(fn, value):                     # a function passed as an argument
        return fn(fn(value))
    print(apply_twice(lambda s: s + "!", "hi"))
    """, "functions_as_values.py"),
    p("""The key distinction is between the **function** and the **result of calling it**. `styles["shout"]` is the function
    object; `styles["shout"]("hello")` calls it. Passing `shout` hands over the function itself; passing `shout("x")`
    would hand over a string. A very common beginner bug is `sorted(items, key=len())` (calling `len` with no argument)
    instead of `key=len`."""),
    callout("sql", "SQL / Power BI", """Passing a function is like passing an **expression** to `ORDER BY`, or a lambda-like
    expression to DAX iterators: `SUMX(Sales, Sales[Qty] * Sales[Price])` evaluates the expression once per row.
    `sorted(rows, key=...)`, `map` and `max(key=...)` work the same way: you give the "per-row expression", and the function
    applies it to every item."""),
)

section("lambda", "`lambda`: small functions in one expression",
    p("""`lambda params: expression` builds a function object, exactly like `def`, with three limits: it has no name (its
    `__name__` is `<lambda>`), its body must be **one expression** (no statements, no assignments, no `return`; the value of
    the expression is returned), and it cannot hold a docstring or type hints. It exists for short functions you need
    right where you pass them."""),
    ex("""
    by_score = lambda doc: doc["score"]          # same as: def by_score(doc): return doc["score"]
    docs = [{"id": "a", "score": 0.4}, {"id": "b", "score": 0.9}, {"id": "c", "score": 0.7}]
    print(sorted(docs, key=by_score)[0]["id"], by_score.__name__)

    print(sorted(docs, key=lambda d: d["score"], reverse=True)[0]["id"])
    print((lambda x, y=2: x * y)(5))             # parameters and defaults work as usual
    """, "lambda.py"),
    p("""When **not** to use `lambda`: when the function needs more than one expression, when it is reused in several places,
    or when you assign it to a name as above. Style guides (PEP 8) say to use `def` then, because a named function gives
    better tracebacks and can have a docstring. A good rule: if you would have to think for more than a second to read
    the `lambda`, write a `def`."""),
)

section("key", "Key functions: sort, min, max and group by any rule",
    p("""`sorted`, `list.sort`, `min`, `max` and `itertools.groupby` all accept `key=`. Step by step, `sorted(items,
    key=f)` calls `f` **once per item** to get a key, sorts the items by their keys, and returns the items themselves (not
    the keys). A key can be any comparable value; a **tuple** key sorts by several rules at once, compared element by
    element, which is how you express "by priority, then by date"."""),
    ex("""
    tickets = [
        {"id": 1, "priority": 2, "age_h": 30},
        {"id": 2, "priority": 1, "age_h": 5},
        {"id": 3, "priority": 1, "age_h": 48},
        {"id": 4, "priority": 2, "age_h": 2},
    ]
    # priority ascending, then oldest first (negate a number to reverse just that part)
    order = sorted(tickets, key=lambda t: (t["priority"], -t["age_h"]))
    print([t["id"] for t in order])

    print(max(tickets, key=lambda t: t["age_h"])["id"])           # the oldest ticket
    words = ["Embedding", "rag", "Agent", "chunk"]
    print(sorted(words), sorted(words, key=str.lower))            # case-insensitive
    """, "key_functions.py"),
    p("""Two details explain most surprises. Python's sort is **stable**: items with equal keys keep their original order,
    so you can sort by a secondary rule first and the primary rule second and get both (lesson 4.2). And `str.lower` is
    passed as an **unbound method**, a plain function that takes the string as its argument, so `key=str.lower` works
    without any `lambda`. The `operator` module has ready-made key functions too: `operator.itemgetter("score")` is a faster,
    clearer `lambda d: d["score"]`, and `itemgetter("priority", "age_h")` returns a tuple key."""),
)

section("mapfilter", "`map`, `filter`, `reduce` and comprehensions",
    p("""`map(fn, iterable)` calls `fn` on each item; `filter(pred, iterable)` keeps the items for which `pred(item)` is
    truthy. Both return **lazy iterators** (Module 6): nothing is computed until you loop over them or wrap them in `list()`,
    and they can only be consumed **once**. `functools.reduce(fn, iterable, start)` folds the items into one value by
    calling `fn(running, item)` repeatedly."""),
    ex("""
    from functools import reduce

    prices = ["12.50", "7", "3.25"]
    as_float = map(float, prices)             # lazy: nothing converted yet
    print(as_float)
    print(list(as_float), list(as_float))     # the second list() finds it already used up

    lengths = [len(s) for s in ["rag", "", "agents"]]
    non_empty = list(filter(None, ["rag", "", "agents"]))   # None means "keep truthy items"
    print(lengths, non_empty)

    print(reduce(lambda acc, x: acc * x, [2, 3, 4], 1))
    """, "map_filter.py"),
    p("""In modern Python a **comprehension** is usually clearer than `map` or `filter` with a `lambda`:
    `[x * 2 for x in xs if x > 0]` reads better than `list(map(lambda x: x * 2, filter(lambda x: x > 0, xs)))`. `map` is
    still nice when you already have a named function (`map(float, prices)`, `map(str.strip, lines)`), and `filter(None,
    ...)` is a common idiom. For `reduce`, there is almost always a clearer built-in: `sum`, `max`, `math.prod`,
    `"".join`, `any`, `all`."""),
)

section("partial", "`functools.partial` and dispatch tables",
    p("""`functools.partial(fn, *args, **kwargs)` returns a new callable that remembers some arguments and fills them in
    for you. It is a ready-made factory (3.4): `partial(complete, model="large")` is a version of `complete` that always
    uses the large model. Unlike a `lambda` in a loop, it stores the **values** right away, so it has no late-binding trap,
    and it keeps a readable `repr`."""),
    ex("""
    from functools import partial

    def complete(prompt, *, model="small", temperature=0.2):
        return f"{model}@{temperature}: {prompt}"

    creative = partial(complete, model="large", temperature=0.9)
    print(creative("Write a haiku"))
    print(creative("Write a haiku", temperature=0.5))     # later keywords override
    print(creative.func.__name__, creative.keywords)
    """, "partial.py"),
    p("""A **dispatch table** is a dict whose values are functions. Instead of a long `if name == "search": ... elif ...`
    chain, you look the function up by name and call it. This is exactly how an agent runs tools: the LLM returns a tool
    name and arguments, the code looks the name up in a registry dict and calls the function with the arguments. Adding a
    tool means adding one entry, and an unknown name is a single, clear error path."""),
    ex("""
    def search(query, k=3):
        return f"top {k} results for {query!r}"

    def calculator(expression):
        allowed = set("0123456789+-*/(). ")
        if not set(expression) <= allowed:
            raise ValueError("unsupported characters")
        return str(eval(expression))         # tiny demo only: never eval untrusted input in real code

    TOOLS = {"search": search, "calculator": calculator}

    def run_tool(call):
        fn = TOOLS.get(call["name"])
        if fn is None:
            return f"error: unknown tool {call['name']!r}"
        return fn(**call["arguments"])

    print(run_tool({"name": "search", "arguments": {"query": "refund policy"}}))
    print(run_tool({"name": "calculator", "arguments": {"expression": "2 * (3 + 4)"}}))
    print(run_tool({"name": "weather", "arguments": {}}))
    """, "dispatch.py"),
    callout("warn", "A note on `eval`", """The calculator uses `eval` only to keep the example tiny, behind a strict character
    check. In real agent code, never `eval` text that came from a user or an LLM: use a safe expression parser (for example
    the `ast` module or a library such as `numexpr`). Tool registries are a classic place for injection bugs."""),
)

section("warmup", "Warm-up",
    predict("The function or its result?", "easy",
        code="""
        def get_score(d):
            return d["score"]

        docs = [{"id": "a", "score": 0.3}, {"id": "b", "score": 0.8}]
        f = get_score
        print(f is get_score, f(docs[0]))
        print(max(docs, key=get_score)["id"])
        try:
            max(docs, key=get_score())
        except TypeError as e:
            print("TypeError:", e)
        """,
        hints=["`key=` wants a function. What does `get_score()` with no argument try to do?"],
        why="""`f = get_score` gives the same function object another name. `key=get_score` hands the function to `max`, which
        calls it once per document. `key=get_score()` **calls** `get_score` right away with no argument, so the error happens
        before `max` even runs: the `TypeError` is about the missing `d`. Passing a function versus passing the result of
        calling it is the core idea of this lesson."""),
    write("Rank retrieved chunks", "easy", tag="RAG",
        prompt="""Write `rank(chunks)` that returns the chunks sorted by `score`, highest first. Ties are broken by the
        shorter `text` first, then by `id` ascending. Use a single `sorted` call with a key function.""",
        code="""
        def rank(chunks):
            pass
        """,
        tests="""
        chunks = [
            {"id": 3, "score": 0.9, "text": "Refunds take five days."},
            {"id": 1, "score": 0.7, "text": "Contact support."},
            {"id": 2, "score": 0.9, "text": "Refunds: 5 days."},
            {"id": 4, "score": 0.9, "text": "Refunds: 5 days."},
        ]
        assert [c["id"] for c in rank(chunks)] == [2, 4, 3, 1]
        assert rank([]) == []
        assert chunks[0]["id"] == 3
        """,
        hints=["A tuple key: `(-score, len(text), id)`. Negating the score sorts it descending while the rest stay ascending."],
        solution="""
        def rank(chunks):
            return sorted(chunks, key=lambda c: (-c["score"], len(c["text"]), c["id"]))
        """,
        why="""The tuple key is compared element by element: score first (negated, so higher comes first), then text length, then
        id, so one sort expresses all three rules. `sorted` returns a new list and leaves the input alone (the last test). The
        negation trick only works for numbers; to reverse a string part of a key you sort twice using stability (lesson 4.2) or
        use `reverse=True` on one pass."""),
    predict("`map` is lazy and single-use", "easy",
        code="""
        lines = ["  alpha ", "beta", "  gamma"]
        cleaned = map(str.strip, lines)
        print(type(cleaned).__name__)
        print(list(cleaned))
        print(list(cleaned))

        lengths = list(map(len, lines))
        kept = list(filter(lambda s: s.strip().startswith("g"), lines))
        print(lengths, kept)
        """,
        hints=["A `map` object is an iterator. What is left after one full pass?"],
        why="""`map` returns a lazy iterator: `list(cleaned)` runs `str.strip` on every line, and a second `list(cleaned)` finds
        nothing left. Wrap it in `list()` once if you need the values more than once. `str.strip` and `len` are passed as
        functions without a `lambda`. This single-use behaviour is the same as the generator trap in 2.4 and Module 6."""),
    fix("A sort that crashes on missing values", "easy", tag="Data work",
        prompt="""`newest_first(rows)` should sort rows by `updated` (an ISO date string), newest first, with rows that have
        no `updated` value at the **end**. It crashes when any row has `None`. Fix the key function.""",
        code="""
        def newest_first(rows):
            return sorted(rows, key=lambda r: r["updated"], reverse=True)
        """,
        tests="""
        rows = [{"id": 1, "updated": "2025-03-01"}, {"id": 2, "updated": None},
                {"id": 3, "updated": "2025-06-10"}, {"id": 4, "updated": None}]
        assert [r["id"] for r in newest_first(rows)] == [3, 1, 2, 4]
        assert newest_first([]) == []
        """,
        hints=["Comparing a string with `None` raises `TypeError`. Make the key a tuple whose first part says whether the value is missing.",
               "With `reverse=True`, think about which first value puts the missing rows at the end."],
        solution="""
        def newest_first(rows):
            return sorted(rows, key=lambda r: (r["updated"] is not None, r["updated"] or ""), reverse=True)
        """,
        why="""Python 3 refuses to compare `None` with a string, so any `None` in the key crashes the whole sort. The tuple
        `(has_value, value)` fixes it: rows with a value get `True`, missing ones `False`, and with `reverse=True` the
        `True` rows come first, ordered newest first, while the missing ones go last. `or ""` replaces `None` with a
        comparable placeholder. Because the sort is stable, rows with no date keep their original order (2 before 4)."""),
)

section("medium", "Medium",
    write("A tool registry with a dispatch table", "medium", tag="GenAI",
        prompt="""Write `make_registry()` returning `(register, call)`. `register(name, fn)` adds a tool, and raises
        `ValueError` if the name is taken. `call(name, arguments)` calls the tool with the `arguments` dict as keyword
        arguments, and returns `{"ok": True, "result": ...}`, or `{"ok": False, "error": "..."}` when the tool is unknown or
        the call raises `TypeError` (wrong arguments from the LLM). Each registry is independent.""",
        code="""
        def make_registry():
            pass
        """,
        tests="""
        def raises(exc, f, *args):
            try:
                f(*args)
            except exc:
                return True
            return False
        register, call = make_registry()
        register("search", lambda query, k=3: f"{k} hits for {query}")
        register("add", lambda a, b: a + b)
        assert call("search", {"query": "refunds"}) == {"ok": True, "result": "3 hits for refunds"}
        assert call("add", {"a": 2, "b": 3}) == {"ok": True, "result": 5}
        assert call("weather", {})["ok"] is False and "unknown tool" in call("weather", {})["error"]
        assert call("add", {"a": 2})["ok"] is False
        assert raises(ValueError, register, "add", print)
        _, call2 = make_registry()
        assert call2("add", {"a": 1, "b": 1})["ok"] is False
        """,
        hints=["Keep `tools = {}` in the factory. `call` looks the name up with `tools.get(name)`.",
               "Wrap only the actual tool call in `try/except TypeError`, so other errors are not hidden."],
        solution="""
        def make_registry():
            tools = {}

            def register(name, fn):
                if name in tools:
                    raise ValueError(f"tool {name!r} already registered")
                tools[name] = fn

            def call(name, arguments):
                fn = tools.get(name)
                if fn is None:
                    return {"ok": False, "error": f"unknown tool {name!r}"}
                try:
                    return {"ok": True, "result": fn(**arguments)}
                except TypeError as e:
                    return {"ok": False, "error": f"bad arguments: {e}"}

            return register, call
        """,
        why="""The registry is a dict from names to function objects, kept private in a closure (3.4), so two registries never
        mix. Returning a structured error instead of raising lets the agent loop send the error text back to the LLM, which can
        then correct its call: that feedback loop is how real agents recover from bad tool calls. Catching only `TypeError`
        is deliberate: a bug inside the tool raising something else should not be disguised as "bad arguments". A real version
        would validate arguments against a schema first (Module 11) and limit what tools may do."""),
    fix("A pipeline that loses its steps", "medium", tag="Data work",
        prompt="""`make_pipeline(*steps)` should return a function that passes a value through every step in order. Every
        pipeline only applies the **last** step. Fix it.""",
        code="""
        def make_pipeline(*steps):
            def run(value):
                for step in steps:
                    result = step(value)
                return result
            return run
        """,
        tests="""
        clean = make_pipeline(str.strip, str.lower, lambda s: s.replace("  ", " "))
        assert clean("  Hello  World ") == "hello world"
        double_then_inc = make_pipeline(lambda x: x * 2, lambda x: x + 1)
        assert double_then_inc(5) == 11
        assert make_pipeline()("same") == "same"
        """,
        hints=["Each step must receive the output of the previous step, not the original value.",
               "With no steps, the function should return its input unchanged."],
        solution="""
        def make_pipeline(*steps):
            def run(value):
                for step in steps:
                    value = step(value)
                return value
            return run
        """,
        why="""The loop fed the **original** value into every step and kept only the last result, so earlier steps had no effect.
        Rebinding `value` passes each output into the next step. It also fixes the empty pipeline, which used to raise
        `UnboundLocalError` because `result` was never assigned (3.3). Composing functions into a pipeline is the idea behind
        scikit-learn's `Pipeline`, text-cleaning chains and LangChain's `|` operator."""),
    trace("Sorting with a key, step by step", "medium",
        prompt="""`sorted` computes one key per word, then orders the words by their keys. Fill in the key computed for each
        word, and the final order (it is computed first, at the top, so it is the same on every row).""",
        code="""
        words = ["agent", "RAG", "api", "Embed"]
        order = sorted(words, key=lambda w: (len(w), w.lower()))
        key = (len(words[0]), words[0].lower())  # row: "key of 'agent'"
        key = (len(words[1]), words[1].lower())  # row: "key of 'RAG'"
        key = (len(words[2]), words[2].lower())  # row: "key of 'api'"
        key = (len(words[3]), words[3].lower())  # row: "key of 'Embed'"
        """,
        trace_vars=["key", "order"],
        hints=["A key here is a tuple `(length, lowercase word)`. Tuples compare element by element."],
        why="""Each key is `(length, lowercase word)`. Three-letter words come first, and between `"RAG"` and `"api"` the second
        part decides: `"api" < "rag"`. The five-letter words compare `"agent" < "embed"`. The sort returns the original words,
        with their original capitalisation, in key order: `["api", "RAG", "agent", "Embed"]`. The keys themselves are thrown
        away once the sort is done."""),
    write("Group records by any rule", "medium", tag="Data work",
        prompt="""Write `group_by(items, key)` that returns a dict from `key(item)` to the list of items with that key, in
        first-seen order of keys and items. `key` is any function, like the `key=` of `sorted`.""",
        code="""
        def group_by(items, key):
            pass
        """,
        tests="""
        tickets = [{"id": 1, "team": "billing"}, {"id": 2, "team": "auth"}, {"id": 3, "team": "billing"}]
        g = group_by(tickets, key=lambda t: t["team"])
        assert {k: [t["id"] for t in v] for k, v in g.items()} == {"billing": [1, 3], "auth": [2]}
        assert list(group_by(["apple", "avocado", "bean"], key=lambda w: w[0])) == ["a", "b"]
        assert group_by([1, 2, 3, 4], key=lambda n: n % 2 == 0) == {False: [1, 3], True: [2, 4]}
        assert group_by([], key=len) == {}
        """,
        hints=["Loop once; `out.setdefault(key(item), []).append(item)` (2.P)."],
        solution="""
        def group_by(items, key):
            out = {}
            for item in items:
                out.setdefault(key(item), []).append(item)
            return out
        """,
        why="""Taking the grouping rule as a function makes one helper serve every grouping: by team, by first letter, by
        parity, by month. That is the same design as `sorted(key=...)` and pandas `groupby` with a function. Unlike
        `itertools.groupby`, this works on unsorted input, because it collects into a dict instead of grouping only
        **consecutive** equal keys (lesson 6.4)."""),
    choose("A lambda or `operator.itemgetter` as the key", "medium",
        prompt="Both find the highest-scoring record among 500,000 records. Which is faster?",
        setup="""import random
from operator import itemgetter
rows = [{"id": i, "score": random.random()} for i in range(500_000)]""",
        options={
            "a": "best = max(rows, key=lambda r: r[\"score\"])",
            "b": "best = max(rows, key=itemgetter(\"score\"))",
        },
        answer="b",
        hints=["Both call the key once per record. What runs inside each call?"],
        why="""`max` calls the key once per record, 500,000 times, and does little else, so the key's own cost is what you are
        timing. The `lambda` is a Python function, so each call builds a frame and runs bytecode; `itemgetter("score")` is
        implemented in C, so each call is a direct lookup. Inside `sorted` the difference is often hidden by the cost of the sort
        itself, but it is still there. Prefer `itemgetter` / `attrgetter` for simple field keys: it is at least as fast and states
        the intent; use a `lambda` when the key needs logic."""),
    fix("Pick a scorer by name", "medium", tag="ML",
        prompt="""`evaluate(preds, gold, metric)` chooses a metric function by name. Adding a metric means editing a growing
        `if` chain, and a typo in the metric name silently returns `None`. Replace the chain with a dispatch table, and make an
        unknown name raise `ValueError` listing the known metrics.""",
        code="""
        def accuracy(p, g):
            return sum(a == b for a, b in zip(p, g)) / len(g)

        def error_rate(p, g):
            return 1 - accuracy(p, g)

        def evaluate(preds, gold, metric):
            if metric == "accuracy":
                return accuracy(preds, gold)
            elif metric == "error_rate":
                return error_rate(preds, gold)
        """,
        tests="""
        def raises(exc, f, *args):
            try:
                f(*args)
            except exc as e:
                return str(e)
            return False
        assert evaluate([1, 0, 1], [1, 1, 1], "accuracy") == 2 / 3
        assert abs(evaluate([1, 0, 1], [1, 1, 1], "error_rate") - 1 / 3) < 1e-12
        msg = raises(ValueError, evaluate, [1], [1], "acuracy")
        assert msg and "accuracy" in msg and "error_rate" in msg
        """,
        hints=["`METRICS = {\"accuracy\": accuracy, \"error_rate\": error_rate}`, then look the name up."],
        solution="""
        def accuracy(p, g):
            return sum(a == b for a, b in zip(p, g)) / len(g)

        def error_rate(p, g):
            return 1 - accuracy(p, g)

        METRICS = {"accuracy": accuracy, "error_rate": error_rate}

        def evaluate(preds, gold, metric):
            try:
                fn = METRICS[metric]
            except KeyError:
                raise ValueError(f"unknown metric {metric!r}; choose from {sorted(METRICS)}") from None
            return fn(preds, gold)
        """,
        why="""The `if` chain had a silent fall-through: an unknown name returned `None` (3.1), which later shows up as a broken
        report rather than an error. The dict maps names to functions, so adding a metric is one line, and the list of valid
        names is available for the error message, the CLI help or a config check. `from None` hides the internal `KeyError`
        so the user sees one clean error (Module 8). scikit-learn's `scoring="f1"` strings work exactly this way: a registry
        from names to scorer functions."""),
    refactor("Comprehension instead of map and filter", "medium",
        prompt="Rewrite this with one list comprehension, keeping the result identical. Keep the tests green.",
        code="""
        def clean_scores(raw):
            parsed = map(lambda s: float(s.strip()), filter(lambda s: s.strip() != "", raw))
            return list(filter(lambda x: 0.0 <= x <= 1.0, parsed))
        """,
        tests="""
        assert clean_scores([" 0.5", "", "1.5", "0.25 ", "  "]) == [0.5, 0.25]
        assert clean_scores([]) == []
        """,
        hints=["Filter empty strings, convert, then keep values in range. A nested comprehension or the walrus operator `:=` can avoid converting twice."],
        solution="""
        def clean_scores(raw):
            values = [float(s) for s in raw if s.strip()]
            return [x for x in values if 0.0 <= x <= 1.0]
        """,
        why="""Three lambdas inside `map` and `filter` force the reader to work inside-out. Two comprehensions read top to
        bottom: "convert the non-empty strings, keep those in range". `float(" 0.5")` already ignores surrounding spaces, so the
        `strip()` before converting was unnecessary. A single comprehension with `:=` (`[x for s in raw if s.strip() if 0 <= (x
        := float(s)) <= 1]`) also works, but two steps are easier to read and to debug."""),
)

section("hard", "Hard",
    predict("Methods as functions", "hard",
        code="""
        from operator import methodcaller, attrgetter

        words = ["  Rag ", "AGENT", " embed"]
        print(list(map(str.strip, words)))
        print(sorted(words, key=str.lower))
        print(list(map(methodcaller("strip", " "), words)))

        upper = "abc".upper
        print(upper(), upper.__self__)
        print(attrgetter("real", "imag")(3 + 4j))
        """,
        hints=["`str.strip` is a plain function taking the string. `\"abc\".upper` is a method already bound to `\"abc\"`.",
               "`sorted(key=str.lower)` compares lower-cased versions, including their leading spaces."],
        why="""`str.strip` taken from the class is an ordinary function whose first argument is the string, so `map` can call it on
        each item. Sorting by `str.lower` compares the lower-cased strings, spaces included, and a space sorts before letters,
        which puts `"  Rag "` first. `methodcaller("strip", " ")` builds a function that calls `.strip(" ")` on whatever it is
        given. `"abc".upper` is a **bound method**: the object is stored in `__self__`, so calling it needs no argument.
        `attrgetter` with several names returns a tuple, which makes it a ready-made multi-field key."""),
    write("Compose functions", "hard", tag="Interview",
        prompt="""Write `compose(*fns)` that returns a function applying the functions **right to left**, like maths:
        `compose(f, g, h)(x) == f(g(h(x)))`. The rightmost function may take any arguments; each other function receives the
        previous result. With no functions, return the identity function (one argument, returned unchanged).""",
        code="""
        def compose(*fns):
            pass
        """,
        tests="""
        inc = lambda x: x + 1
        dbl = lambda x: x * 2
        assert compose(inc, dbl)(5) == 11
        assert compose(dbl, inc)(5) == 12
        assert compose(str.upper, " ".join)(["a", "b"]) == "A B"
        assert compose(len, max)([3, 9], [1, 2, 3], key=len) == 3
        assert compose()(7) == 7
        """,
        hints=["Call the last function with `*args, **kwargs`, then loop over the rest in reverse, feeding each the result.",
               "`reversed(fns[:-1])` walks the remaining functions right to left."],
        solution="""
        def compose(*fns):
            if not fns:
                return lambda x: x
            *rest, last = fns
            def composed(*args, **kwargs):
                result = last(*args, **kwargs)
                for fn in reversed(rest):
                    result = fn(result)
                return result
            return composed
        """,
        why="""Only the innermost function sees the original arguments, so it alone is called with `*args, **kwargs`; that is
        why `compose(len, max)` can forward `key=len` to `max`. Star-unpacking `*rest, last = fns` (lesson 4.3) splits off the
        last function. The order matters and is a classic interview check: `compose(inc, dbl)(5)` doubles first. Many libraries
        offer this (`toolz.compose`), and the "pipe" style (left to right, as in problem 6) is often easier for readers; in an
        interview, say which one you implemented."""),
    fix("Read the code: callbacks that fire with the wrong settings", "hard", tag="ML",
        prompt="""This training-loop helper lets you register callbacks that run after each epoch. A sweep registers one
        early-stopping callback per patience setting, plus a logging callback built with `partial`. The early-stopping
        callbacks all use the last patience value, and the logger ignores its prefix. Read the module, find both bugs, and fix
        them.""",
        code="""
        from functools import partial


        def train(epochs, losses, callbacks):
            history = []
            for epoch in range(epochs):
                loss = losses[epoch]
                history.append(loss)
                messages = [cb(epoch, history) for cb in callbacks]
                if "stop" in messages:
                    return epoch, messages
            return epochs - 1, []


        def make_callbacks(patiences, log):
            callbacks = []
            for patience in patiences:
                def early_stop(epoch, history):
                    best = min(history)
                    since_best = len(history) - 1 - history.index(best)
                    return "stop" if since_best >= patience else "go"
                callbacks.append(early_stop)
            callbacks.append(partial(log_epoch, log))
            return callbacks


        def log_epoch(log, epoch, history, prefix="run"):
            log.append(f"{prefix} epoch {epoch}: {history[-1]}")
            return "go"
        """,
        tests="""
        log = []
        cbs = make_callbacks([1, 5], log, prefix="sweep")
        stopped, msgs = train(6, [1.0, 0.8, 0.9, 0.95, 0.97, 0.99], cbs)
        assert stopped == 2 and msgs == ["stop", "go", "go"]
        assert log == ["sweep epoch 0: 1.0", "sweep epoch 1: 0.8", "sweep epoch 2: 0.9"]
        cb1 = make_callbacks([3], [], prefix="x")[0]
        assert cb1(3, [1.0, 0.5, 0.6, 0.7]) == "go" and cb1(4, [1.0, 0.5, 0.6, 0.7, 0.8]) == "stop"
        """,
        hints=["Each `early_stop` reads `patience` when it runs, after the loop has ended. Build each callback with a factory or `partial`.",
               "`make_callbacks` has no `prefix` parameter. Add one and pass it to `partial` as a keyword."],
        solution="""
        from functools import partial


        def train(epochs, losses, callbacks):
            history = []
            for epoch in range(epochs):
                loss = losses[epoch]
                history.append(loss)
                messages = [cb(epoch, history) for cb in callbacks]
                if "stop" in messages:
                    return epoch, messages
            return epochs - 1, []


        def early_stop(epoch, history, *, patience):
            best = min(history)
            since_best = len(history) - 1 - history.index(best)
            return "stop" if since_best >= patience else "go"


        def make_callbacks(patiences, log, prefix="run"):
            callbacks = [partial(early_stop, patience=p) for p in patiences]
            callbacks.append(partial(log_epoch, log, prefix=prefix))
            return callbacks


        def log_epoch(log, epoch, history, prefix="run"):
            log.append(f"{prefix} epoch {epoch}: {history[-1]}")
            return "go"
        """,
        why="""Bug one is late binding (3.4): all the `early_stop` closures share the single `patience` variable of
        `make_callbacks`, which ends at 5, so the patience-1 callback never stops. `partial(early_stop, patience=p)` stores each
        value immediately. Moving `early_stop` to module level with a keyword-only `patience` also makes it testable on its own
        (the last test). Bug two is a missing parameter: the test passes `prefix="sweep"`, but `make_callbacks` had nowhere to
        put it, so the starter fails at the call. The fixed version forwards it into `partial` as a keyword, so each logger
        carries its own prefix. Keras and PyTorch Lightning callbacks are configured exactly like this, usually as small
        classes."""),
    write("A safe calculator tool without eval", "hard", tag="GenAI",
        prompt="""An agent needs a calculator tool, and `eval` is not allowed. Write `calculate(tokens)` for an expression
        already split into tokens, numbers and the four operators, such as `["2", "+", "3", "*", "4"]`, evaluated **left to
        right with no operator precedence** (so that example gives 20). Use a dispatch table from operator symbols to functions
        from the `operator` module. Raise `ValueError` for an unknown operator, and `ZeroDivisionError` must propagate.""",
        code="""
        import operator

        def calculate(tokens):
            pass
        """,
        tests="""
        def raises(exc, f, *args):
            try:
                f(*args)
            except exc:
                return True
            return False
        assert calculate(["2", "+", "3", "*", "4"]) == 20
        assert calculate(["10", "/", "4"]) == 2.5
        assert calculate(["7"]) == 7
        assert calculate(["1.5", "-", "0.5", "*", "3"]) == 3.0
        assert raises(ValueError, calculate, ["2", "^", "3"])
        assert raises(ZeroDivisionError, calculate, ["1", "/", "0"])
        """,
        hints=["`OPS = {\"+\": operator.add, \"-\": operator.sub, \"*\": operator.mul, \"/\": operator.truediv}`.",
               "Start from the first number, then walk the rest in pairs `(op, number)`: `zip(tokens[1::2], tokens[2::2])`."],
        solution="""
        import operator

        OPS = {"+": operator.add, "-": operator.sub, "*": operator.mul, "/": operator.truediv}

        def to_number(text):
            return float(text) if "." in text else int(text)

        def calculate(tokens):
            result = to_number(tokens[0])
            for op, text in zip(tokens[1::2], tokens[2::2]):
                fn = OPS.get(op)
                if fn is None:
                    raise ValueError(f"unknown operator {op!r}")
                result = fn(result, to_number(text))
            return result
        """,
        why="""The dispatch table maps each symbol to a real function, so the evaluator never runs arbitrary code: only the four
        operations in `OPS` can ever execute, which is the safety property `eval` cannot give. Supporting a new operator is one
        dict entry (`"%": operator.mod`). Slicing with steps pairs each operator with the number after it. Real precedence
        (`*` before `+`) needs a proper parser, for example one built on Python's `ast` module that walks only allowed node
        types, which is how safe calculator tools are usually written."""),
)

section("interview", "Interview questions",
    explain("What does \"functions are first-class objects\" mean, and what does it let you do?", "medium", tag="Interview",
        why="""A function is an object like any other: it can be bound to names, stored in lists and dicts, passed as an argument,
        returned from another function, and given attributes. That enables higher-order functions (`sorted(key=...)`, `map`,
        `filter`), callbacks, factories and closures, `functools.partial`, decorators, and dispatch tables that replace long
        `if` chains (tool registries, metric registries, command handlers). A good answer gives one concrete example from real
        work, such as passing a scoring function into an evaluation loop or routing LLM tool calls through a dict."""),
    explain("`lambda` or `def`: when do you use each?", "medium", tag="Interview",
        why="""Both create function objects. `lambda` is limited to one expression, has no name in tracebacks (`<lambda>`), and
        cannot carry a docstring or annotations. Use it for short, obvious functions passed inline: `key=lambda r: r["score"]`,
        a tiny callback. Use `def` for anything with logic, anything reused, anything you would name (PEP 8 discourages
        assigning a lambda to a name), and anything that needs testing or documentation. Also mention the better alternatives
        to many lambdas: `operator.itemgetter` / `attrgetter`, `functools.partial`, bound methods like `str.lower`, and
        comprehensions instead of `map`/`filter` with a lambda."""),
    explain("How would you design the part of an agent that executes the tool calls an LLM returns?", "hard", tag="Interview",
        why="""Keep a **registry**: a dict from tool name to a function (often with a schema and description, generated from
        the function's signature and docstring, 3.1). For each tool call: look up the name (unknown name means a structured
        error back to the model, not a crash); validate the arguments against the schema before calling (Pydantic), returning
        validation errors to the model so it can retry; call the function with the validated arguments as keyword arguments;
        catch and report tool failures, distinguishing bad arguments from internal bugs; and log the call and result for
        tracing. Safety: never `eval` model output, give tools the least privilege they need, put timeouts and rate limits on
        external calls (3.4's limiter), and pass copies or validated objects so tools cannot change the agent's state (2.4)."""),
)

recap(
    "Functions are values: store them, pass them, return them. `f` is the function; `f()` is the result of calling it.",
    "`lambda` is a one-expression function for short inline uses. Anything bigger or reused deserves a `def`.",
    "`key=` functions run once per item. Tuple keys sort by several rules; `operator.itemgetter` is a fast, clear field key.",
    "`map` and `filter` are lazy and single-use. A comprehension is usually clearer; `reduce` usually has a clearer built-in.",
    "`functools.partial` fixes arguments without late-binding traps. Dispatch tables (dicts of functions) replace `if` chains and power agent tool registries.",
)
