from lesson import *
from diagrams import *

lesson(
    id="m4-3", num="4.3", title="Tuples and unpacking",
    intro="What makes something a tuple (the comma, not the brackets), how packing and unpacking work step by step, star "
          "unpacking, named tuples as lightweight records, and tuples as composite keys, the Python version of a SQL "
          "composite primary key.",
    desc="Immutability, packing and unpacking, star unpacking, swapping, `namedtuple`.",
    keys="tuple immutable comma packing unpacking star unpacking swap multiple assignment namedtuple typing namedtuple _replace _asdict composite key hashable zip transpose",
)

term("Tuple", "An immutable sequence: once created, which objects it holds and in what order can never change.")
term("Packing", "Building a tuple from comma-separated values, as in `point = 3, 4`.")
term("Unpacking", "Assigning the items of an iterable to several names at once: `x, y = point`.")
term("Star unpacking", "`first, *rest = items`: the starred name collects all leftover items into a list.")
term("namedtuple", "A tuple subclass whose positions also have field names: `Score(precision=0.8, recall=0.6).recall`.")
term("Composite key", "A key made of several values, such as `(user_id, day)`, used as one dict key or set member.")

section("what", "What a tuple is, and what makes one",
    p("""A tuple is an **immutable** sequence: a fixed-size array of references (like a list, 4.1) that can never change
    after it is created. You cannot assign to a position, append, remove or sort it in place. Indexing, slicing, `len`,
    `in`, `count` and `index` all work as for lists, and slicing a tuple returns a new tuple."""),
    p("""The part that trips people up: **the comma makes the tuple, not the parentheses**. Parentheses are only needed when
    the expression would otherwise be ambiguous, and for the empty tuple `()`. A one-item tuple needs a trailing comma, and a
    stray trailing comma creates a tuple you did not mean to create."""),
    ex("""
    a = (1)          # just the number 1 in brackets
    b = (1,)         # a one-item tuple
    c = 1, 2         # a tuple without any brackets
    d = ()           # the empty tuple
    e = "rag",       # a trailing comma: a tuple again
    print(type(a).__name__, type(b).__name__, c, d, e)

    config_name = "prod",       # a typo that makes a tuple instead of a string
    print(f"loading {config_name}")
    """, "comma.py"),
    p("""Why choose a tuple over a list? Three concrete reasons. **Safety**: nobody can change it, so it can be shared and
    returned without the copying worries of Module 2. **Hashability**: a tuple of hashable items can be a dict key or a set
    member (the last section). **Meaning**: by convention, a list is "many items of the same kind" and a tuple is "a fixed
    record whose positions mean different things", like `(latitude, longitude)` or `(name, score)`. Tuples are also slightly
    smaller and faster to create, and a tuple of constants is built once at compile time (problem 7)."""),
    callout("sql", "SQL / Power BI", """A tuple is like one **row** of a table: a fixed set of columns in a fixed order, each
    with its own meaning. A list is like a **column**: many values of the same kind. A list of tuples is a small table,
    which is exactly what a database driver returns from `cursor.fetchall()`."""),
)

section("unpack", "Packing and unpacking, step by step",
    fig(chain(["a, b = b, a", "right side first:|the tuple (b, a)", "then unpacked into|a and b", ("swapped, no|temporary name", "good")]),
        "The right-hand side is evaluated completely before any name is assigned, which is why the swap works."),
    p("""**Unpacking** assigns the items of any iterable to several names: `x, y = point`. Step by step, Python evaluates the
    whole right-hand side first, then checks that it yields exactly as many items as there are names, then assigns them
    from left to right. Too many or too few items raise `ValueError` with a message that says which."""),
    ex("""
    point = 3, 4                    # packing
    x, y = point                    # unpacking
    name, (lo, hi) = "latency", (12, 48)   # nested: the shape on the left matches the right
    print(x, y, name, lo, hi)

    for i, (doc, score) in enumerate([("faq", 0.9), ("guide", 0.7)], start=1):
        print(i, doc, score)

    for bad in ["a, b = (1, 2, 3)", "a, b, c = (1, 2)", "a, b = 5"]:
        try:
            exec(bad)
        except (ValueError, TypeError) as e:
            print(f"{bad:18} -> {type(e).__name__}: {e}")
    """, "unpacking.py"),
    p("""Swapping two variables is the most famous use: `a, b = b, a`. The right side `b, a` is evaluated completely first,
    using the **old** values, and only then are the names assigned. That is why no temporary variable is needed. The same
    rule makes `a, b = b, a + b` (the Fibonacci step) correct: both new values are computed from the old ones before either
    name changes."""),
    ex("""
    a, b = 0, 1
    for _ in range(6):
        a, b = b, a + b
    print(a, b)
    """, "swap.py"),
)

section("star", "Star unpacking",
    fig(table(["pattern = [1, 2, 3, 4]", "names get"], [
        ["first, *rest", "first = 1, rest = [2, 3, 4]"],
        ["*init, last", "init = [1, 2, 3], last = 4"],
        ["a, *_, z", "a = 1, z = 4"],
    ], label="star unpacking"),
        "A starred name collects whatever the other names do not take, always as a list."),
    p("""A starred name on the left collects **all the leftover items into a list**. It can appear at the start, the end or
    the middle, but only once, because otherwise the split would be ambiguous. If nothing is left over it is an empty list,
    never `None`, and it is always a **list**, even when the right side is a tuple or a string."""),
    ex("""
    first, *rest = ["system", "user", "assistant", "user"]
    *history, last = ["system", "user", "assistant", "user"]
    head, *middle, tail = "abcde"
    only, *nothing = ("x",)
    print(first, rest)
    print(history, last)
    print(head, middle, tail, only, nothing)

    header, *rows = [("id", "score"), (1, 0.9), (2, 0.4)]   # a CSV-like table
    print(header, rows)
    """, "star_unpacking.py"),
    p("""The same star works in literals and calls, in the other direction: it spreads an iterable into separate items.
    `[*a, *b]` concatenates any iterables into a list, `(*a, x)` builds a tuple, `{**d1, **d2}` merges dicts, and `f(*args)`
    spreads arguments (3.2). And `zip(*rows)` uses it to turn rows into columns: each row becomes one argument of `zip`,
    which then pairs up the first items, the second items and so on (problem 13)."""),
    ex("""
    rows = [("faq", 0.9, 120), ("guide", 0.7, 340), ("terms", 0.2, 80)]
    names, scores, tokens = zip(*rows)
    print(names, scores, tokens)
    print([*names, "extra"], (*scores, 1.0))
    """, "star_spread.py"),
)

section("named", "Named tuples: records without a class",
    p("""Positions are fine for two or three fields, but `result[2]` says nothing about what the value is. A **named tuple**
    gives each position a name while staying a real tuple: immutable, hashable, unpackable, and comparable to plain tuples.
    `typing.NamedTuple` is the modern way to write one, with type hints; `collections.namedtuple` is the older factory
    function."""),
    ex("""
    from typing import NamedTuple

    class Metrics(NamedTuple):
        precision: float
        recall: float
        support: int = 0

    m = Metrics(0.82, 0.61, support=140)
    print(m.recall, m[1], m)
    p, r, n = m                                  # still a tuple: unpacks by position
    print(p, r, n, m == (0.82, 0.61, 140))
    better = m._replace(recall=0.7)              # "changing" means building a new one
    print(better, m.recall, m._asdict())
    try:
        m.recall = 0.9
    except AttributeError as e:
        print("AttributeError:", e)
    """, "named_tuple.py"),
    p("""Named tuples shine for **function results** (`return Metrics(p, r, n)` instead of a bare tuple whose order a caller
    can confuse, problem 4) and for rows of fixed shape. Their limits: they are immutable (`_replace` builds a new one), and
    because they are tuples, `m == (0.82, 0.61, 140)` is `True`: they compare equal to any tuple with the same values, which
    can hide mix-ups between two different record types. When you need mutability, validation or methods, use a dataclass
    (Module 11)."""),
)

section("keys", "Tuples as keys",
    fig(refs(["(2025, 'eu')", "(2025, 'us')", "('ana', 'ml')"], ["sales total 120", "sales total 95", "team record"], [(0, 0), (1, 1), (2, 2)],
        title_names="tuple keys", title_objects="values", label="tuples as composite dict keys"),
        "Tuples of immutable values are hashable, so they make natural composite keys, like a multi-column primary key."),
    p("""A tuple is **hashable when all its items are hashable**, so it can be a dict key or a set member. That makes tuples
    the natural **composite key**: "one entry per user per day" is a dict keyed by `(user_id, day)`, exactly like a
    composite primary key in SQL. Tuples also compare **lexicographically**: first items first, and only if they are equal,
    the second items, and so on, which is why tuple keys sort by several rules at once (3.5)."""),
    ex("""
    usage = {}
    events = [("ana", "2025-06-01", 120), ("ben", "2025-06-01", 50), ("ana", "2025-06-01", 30), ("ana", "2025-06-02", 70)]
    for user, day, tokens in events:
        key = (user, day)                     # composite key
        usage[key] = usage.get(key, 0) + tokens
    print(usage)

    print((1, "b") < (1, "c"), (1, 2) < (1, 2, 0), (2,) > (1, 99))
    try:
        hash(("ana", ["tag"]))
    except TypeError as e:
        print("TypeError:", e)
    """, "tuple_keys.py"),
    p("""Remember the caveat from 2.2: a tuple is only as immutable as its contents. `("ana", ["tag"])` cannot be a key,
    because the list inside could change. When building cache keys from data that may contain lists or dicts, convert them
    first (2.2, `freeze`)."""),
)

section("warmup", "Warm-up",
    predict("What is a tuple?", "easy",
        code="""
        a = (5)
        b = (5,)
        c = 5, 6
        d = ("prod")
        e = "prod",
        print(type(a).__name__, type(b).__name__, type(c).__name__, type(d).__name__, type(e).__name__)
        print(len(b), len(c), len(e), len(d))
        """,
        hints=["Look for commas, not brackets."],
        why="""`(5)` and `("prod")` are just a number and a string inside brackets. `(5,)`, `5, 6` and `"prod",` all contain a
        comma, so they are tuples. `len(d)` is 4 because `d` is the string `"prod"`. The trailing-comma tuple is a real bug
        source: `name = "prod",` makes `name` a tuple, and the error shows up far away, for example when a path is built from
        it."""),
    write("Split a full name", "easy", tag="Data work",
        prompt="""Write `first_last(full_name)` that returns a tuple `(first, last)`: the first and last words of the name,
        ignoring middle names and extra spaces. A one-word name gives `(word, "")`, and an empty string gives `("", "")`. Use
        star unpacking.""",
        code="""
        def first_last(full_name):
            pass
        """,
        tests="""
        assert first_last("Ana Maria Lopez") == ("Ana", "Lopez")
        assert first_last("  Ben   Ortiz ") == ("Ben", "Ortiz")
        assert first_last("Cher") == ("Cher", "")
        assert first_last("") == ("", "")
        """,
        hints=["`first, *rest = words` puts everything after the first word in `rest`. The last name is then `rest[-1]` if there is one."],
        solution="""
        def first_last(full_name):
            words = full_name.split()
            if not words:
                return "", ""
            first, *rest = words
            return first, rest[-1] if rest else ""
        """,
        why="""`split()` with no argument splits on any run of whitespace and ignores leading and trailing spaces. Star unpacking
        takes the first word and leaves the rest in a list, which is empty for a one-word name, so `rest[-1] if rest else ""`
        covers both cases. `return first, ...` packs the two values into a tuple. Real names are messier (prefixes, particles
        such as "de la", non-Western order), which is why CRM systems store name parts separately instead of splitting them."""),
    predict("When unpacking fails", "easy",
        code="""
        row = ("faq.md", 0.92, 128)
        doc, score, tokens = row
        print(doc, score, tokens)
        for bad in ["doc, score = row", "doc, score, tokens, extra = row", "a, b = 'ab'", "a, b = 'abc'"]:
            try:
                exec(bad)
                print(bad, "-> ok")
            except ValueError as e:
                print(bad, "->", e)
        """,
        hints=["Unpacking works on any iterable, including a string. The count must match exactly."],
        why="""The number of names must equal the number of items. Too few names gives "too many values to unpack (expected
        2)", too many names gives "not enough values to unpack". A two-character string unpacks fine into two names, because a
        string is an iterable of characters; three characters into two names fails. These messages appear constantly when a
        function's return shape changes and a caller was not updated."""),
    fix("Metrics returned in a confusing order", "easy", tag="ML",
        prompt="""`evaluate` returns `(recall, precision, f1)`, and callers keep unpacking it as `precision, recall, f1`,
        reporting swapped numbers. Return a `NamedTuple` called `Metrics` with fields `precision`, `recall`, `f1`, so callers can
        use names.""",
        code="""
        def evaluate(tp, fp, fn):
            precision = tp / (tp + fp) if tp + fp else 0.0
            recall = tp / (tp + fn) if tp + fn else 0.0
            f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
            return recall, precision, f1
        """,
        tests="""
        m = evaluate(tp=8, fp=2, fn=8)
        assert m.precision == 0.8 and m.recall == 0.5
        assert abs(m.f1 - 0.6153846153846154) < 1e-12
        p, r, f = m
        assert (p, r) == (0.8, 0.5)
        assert evaluate(0, 0, 0) == (0.0, 0.0, 0.0)
        """,
        hints=["Define `class Metrics(NamedTuple):` with three float fields, in the order `precision, recall, f1`, and return `Metrics(...)`."],
        solution="""
        from typing import NamedTuple

        class Metrics(NamedTuple):
            precision: float
            recall: float
            f1: float

        def evaluate(tp, fp, fn):
            precision = tp / (tp + fp) if tp + fp else 0.0
            recall = tp / (tp + fn) if tp + fn else 0.0
            f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
            return Metrics(precision, recall, f1)
        """,
        why="""A bare tuple forces every caller to remember positions, and precision and recall are both floats between 0 and
        1, so a swap never raises an error: it just produces a wrong report. With a named tuple, `m.precision` cannot be
        confused, and old callers that unpack still work because it is still a tuple. Fixing the order to `precision, recall`
        also matches the usual convention (scikit-learn's `precision_recall_fscore_support` returns them in that order)."""),
)

section("medium", "Medium",
    write("Summarise tool calls with nested unpacking", "medium", tag="GenAI",
        prompt="""An agent logs each tool call as `(tool_name, arguments, (latency_ms, tokens))`. Write
        `summarise(calls)` returning a dict from tool name to a tuple `(count, total_tokens, max_latency_ms)`. Unpack each
        record in the `for` line itself.""",
        code="""
        def summarise(calls):
            pass
        """,
        tests="""
        log = [("search", {"q": "a"}, (120, 400)), ("calc", {"e": "1+1"}, (5, 20)), ("search", {"q": "b"}, (300, 380))]
        assert summarise(log) == {"search": (2, 780, 300), "calc": (1, 20, 5)}
        assert summarise([]) == {}
        """,
        hints=["`for name, _args, (latency, tokens) in calls:` unpacks the nested tuple directly. `_args` signals \"not used\".",
               "Keep the running tuple in the dict and rebuild it each time: tuples cannot be changed in place."],
        solution="""
        def summarise(calls):
            out = {}
            for name, _args, (latency, tokens) in calls:
                count, total, worst = out.get(name, (0, 0, 0))
                out[name] = (count + 1, total + tokens, max(worst, latency))
            return out
        """,
        why="""The loop header mirrors the shape of each record, so the body works with names instead of `call[2][1]`. Because a
        tuple cannot change, each update unpacks the current totals and stores a **new** tuple; for many updates a small mutable
        object (a list, a dict or a dataclass) would avoid rebuilding, but the immutable version cannot be corrupted by another
        part of the code holding a reference. The leading underscore in `_args` is a convention that tells readers and linters
        the value is intentionally unused."""),
    trace("Swaps and star unpacking", "medium",
        prompt="Fill in `a`, `b` and `rest` after each marked line.",
        code="""
        a, b, rest = 1, 2, []
        a, b = b, a  # row: "a, b = b, a"
        a, b = b, a + b  # row: "a, b = b, a + b"
        a, *rest = [b, a, 7, 8]  # row: "a, *rest = [b, a, 7, 8]"
        *rest, b = rest  # row: "*rest, b = rest"
        """,
        trace_vars=["a", "b", "rest"],
        hints=["The whole right side is evaluated with the old values before any name changes."],
        why="""The swap gives `a = 2, b = 1`. Then `b, a + b` is computed from the old values as `(1, 3)`, so `a = 1, b = 3`.
        `[b, a, 7, 8]` is built as `[3, 1, 7, 8]` before assigning, so `a = 3` and `rest = [1, 7, 8]`. Finally `*rest, b =
        rest` reads the current `rest` first, then assigns its last item to `b` and the others to a new list `rest`."""),
    choose("Creating a tuple or a list of constants", "medium",
        prompt="Both build a small record of five constants a million times. Which loop is faster?",
        setup="n = 1_000_000",
        options={
            "a": "for _ in range(n):\n    rec = [200, \"OK\", 0.25, True, None]",
            "b": "for _ in range(n):\n    rec = (200, \"OK\", 0.25, True, None)",
        },
        answer="b",
        hints=["A tuple of constants can never change. What can the compiler do with it?"],
        why="""Because a tuple of constants is immutable, the compiler builds it **once**, when the code is compiled, and stores
        it as a constant: each pass of the loop just loads that one object. A list must be a new object every time (someone
        might change it), so each pass allocates a list and fills five slots. You can see the difference with `dis.dis`:
        `LOAD_CONST` for the tuple versus `BUILD_LIST` for the list. This is a small effect per object, but it is one reason
        tuples suit fixed records and constant tables."""),
    write("One event per user per day", "medium", tag="Data work",
        prompt="""Write `first_per_day(events)` where each event is a dict with `user`, `ts` (ISO timestamp string such as
        `"2025-06-01T09:30"`) and `action`. Return the list of events that are the **first** for their `(user, day)` pair,
        in input order. Events are already in time order.""",
        code="""
        def first_per_day(events):
            pass
        """,
        tests="""
        ev = [{"user": "ana", "ts": "2025-06-01T09:30", "action": "login"},
              {"user": "ana", "ts": "2025-06-01T11:00", "action": "query"},
              {"user": "ben", "ts": "2025-06-01T10:00", "action": "login"},
              {"user": "ana", "ts": "2025-06-02T08:15", "action": "query"}]
        assert [e["ts"] for e in first_per_day(ev)] == ["2025-06-01T09:30", "2025-06-01T10:00", "2025-06-02T08:15"]
        assert first_per_day([]) == []
        """,
        hints=["The day is the part before `\"T\"`. Keep a set of `(user, day)` tuples you have already seen."],
        solution="""
        def first_per_day(events):
            seen = set()
            out = []
            for e in events:
                key = (e["user"], e["ts"].split("T")[0])
                if key not in seen:
                    seen.add(key)
                    out.append(e)
            return out
        """,
        why="""The tuple `(user, day)` is the composite key: two events collide only when **both** parts match, which a single
        string key would also do (`f"{user}|{day}"`) but with the risk of a separator appearing inside a value. Tuples need no
        separator and keep the parts typed. This is SQL's `ROW_NUMBER() OVER (PARTITION BY user, day ORDER BY ts) = 1`; in
        pandas, `df.drop_duplicates(subset=["user", "day"])`."""),
    fix("A cache key that is a list", "medium", tag="GenAI",
        prompt="""The response cache builds its key from the model name, the prompt and the stop sequences, and crashes with
        `TypeError: unhashable type: 'list'`. Fix `cache_key` so it returns a hashable key; equal requests must give equal keys.""",
        code="""
        _cache = {}

        def cache_key(model, prompt, stop):
            return [model, prompt, stop]

        def cached(model, prompt, stop, compute):
            key = cache_key(model, prompt, stop)
            if key not in _cache:
                _cache[key] = compute(prompt)
            return _cache[key]
        """,
        tests="""
        calls = []
        def fake(prompt):
            calls.append(prompt)
            return prompt.upper()
        assert cached("small", "hi", ["###", "END"], fake) == "HI"
        assert cached("small", "hi", ["###", "END"], fake) == "HI"
        assert cached("large", "hi", ["###", "END"], fake) == "HI"
        assert calls == ["hi", "hi"]
        assert hash(cache_key("m", "p", ["a"])) == hash(cache_key("m", "p", ["a"]))
        """,
        hints=["A list cannot be a dict key, and neither can a tuple that **contains** a list. Convert `stop` too."],
        solution="""
        _cache = {}

        def cache_key(model, prompt, stop):
            return (model, prompt, tuple(stop))

        def cached(model, prompt, stop, compute):
            key = cache_key(model, prompt, stop)
            if key not in _cache:
                _cache[key] = compute(prompt)
            return _cache[key]
        """,
        why="""Dict keys must be hashable, so the outer list must become a tuple. But `(model, prompt, stop)` would still fail,
        because a tuple is only hashable when everything inside it is, and `stop` is a list (2.2). `tuple(stop)` fixes the inner
        level. Including the model in the key matters: the same prompt sent to a different model must not reuse an answer, as
        the third call shows. For nested argument dicts, use the recursive `freeze` from 2.2."""),
    refactor("Indexes to unpacking", "medium",
        prompt="Replace the index lookups with unpacking, so each value has a name. Keep the tests green.",
        code="""
        def report(rows):
            lines = []
            for row in rows:
                if row[2] >= 0.5:
                    lines.append(f"{row[0]} ({row[1]}): {row[2]:.2f}")
            return lines
        """,
        tests="""
        rows = [("faq.md", "billing", 0.91), ("old.md", "misc", 0.32), ("guide.md", "auth", 0.5)]
        assert report(rows) == ["faq.md (billing): 0.91", "guide.md (auth): 0.50"]
        assert report([]) == []
        """,
        hints=["`for doc, topic, score in rows:` and a comprehension."],
        solution="""
        def report(rows):
            return [f"{doc} ({topic}): {score:.2f}" for doc, topic, score in rows if score >= 0.5]
        """,
        why="""`row[2]` forces the reader to remember that position 2 is the score; `score` says it. Unpacking in the loop header
        also checks the shape: a row with the wrong number of fields now raises immediately instead of silently reading the
        wrong position. When the same record type is used in many places, a named tuple (problem 4) makes the names
        permanent."""),
    predict("Named tuples are tuples", "medium",
        code="""
        from collections import namedtuple

        Hit = namedtuple("Hit", ["doc", "score"])
        h = Hit("faq.md", 0.9)
        print(h, h.score, h[0])
        print(h == ("faq.md", 0.9), isinstance(h, tuple))
        h2 = h._replace(score=0.95)
        print(h2, h)
        print(sorted([Hit("b", 0.5), Hit("a", 0.5), Hit("c", 0.9)])[0])
        print({h: "cached"}[("faq.md", 0.9)])
        """,
        hints=["A named tuple compares, sorts and hashes exactly like the plain tuple of its values."],
        why="""`Hit` is a subclass of `tuple`, so it equals the plain tuple with the same values, hashes the same (the plain
        tuple finds the cached entry), and sorts by its fields in order: `doc` first, so `Hit("a", 0.5)` comes first.
        `_replace` returns a new named tuple and leaves `h` unchanged. That equality with plain tuples is convenient, and also a
        trap: two different record types with the same values compare equal."""),
)

section("hard", "Hard",
    predict("Assignment order in multiple targets", "hard",
        code="""
        xs = [0, 0, 0]
        i = 0
        i, xs[i] = 1, 9
        print(i, xs)

        xs = [0, 0, 0]
        i = 0
        xs[i], i = 9, 1
        print(i, xs)

        a = [1, 2, 3]
        a[0], a[a[0]] = 2, 7
        print(a)
        """,
        hints=["The right side is evaluated first. Then the targets on the left are assigned **from left to right**, and each target expression is evaluated when its turn comes."],
        why="""In `i, xs[i] = 1, 9`, `i` is assigned 1 first, and only then is `xs[i]` evaluated as a target, so 9 goes into
        `xs[1]`. Swapping the targets, `xs[i], i = 9, 1`, uses the old `i` (0) for the list position. In the last example,
        `a[0]` becomes 2 first, so `a[a[0]]` means `a[2]`, which becomes 7. Code like this is legal but confusing: it is a
        favourite of tricky interviews and a source of real bugs when someone "swaps" a value and an index on one line."""),
    write("Transpose rows into columns", "hard", tag="Data work",
        prompt="""Write `columns(rows)` that turns a list of equal-length rows into a list of column tuples, using `zip` and
        star unpacking, and raises `ValueError` if the rows have different lengths. Also write `unzip_pairs(pairs)` that turns
        `[(name, score), ...]` into two lists `(names, scores)`, returning `([], [])` for no pairs.""",
        code="""
        def columns(rows):
            pass

        def unzip_pairs(pairs):
            pass
        """,
        tests="""
        def raises(exc, f, *args):
            try:
                f(*args)
            except exc:
                return True
            return False
        assert columns([(1, "a"), (2, "b"), (3, "c")]) == [(1, 2, 3), ("a", "b", "c")]
        assert columns([]) == []
        assert raises(ValueError, columns, [(1, 2), (3,)])
        assert unzip_pairs([("faq", 0.9), ("guide", 0.7)]) == (["faq", "guide"], [0.9, 0.7])
        assert unzip_pairs([]) == ([], [])
        """,
        hints=["`zip(*rows, strict=True)` (1.2) passes each row as a separate argument and refuses rows of different length.",
               "`names, scores = zip(*pairs)` fails for an empty list: `zip()` produces nothing, so there is nothing to unpack."],
        solution="""
        def columns(rows):
            return list(zip(*rows, strict=True))

        def unzip_pairs(pairs):
            if not pairs:
                return [], []
            names, scores = zip(*pairs)
            return list(names), list(scores)
        """,
        why="""`zip(*rows)` spreads the rows into separate arguments, and `zip` then yields the first items of every row, then the
        second items, which is a transpose. `strict=True` turns a ragged table into an error instead of silently dropping the
        extra values. The empty case is the classic trap: `zip(*[])` is `zip()`, which yields nothing, so `names, scores = ...`
        raises "not enough values to unpack". The guard makes the function total. For real tables, `pandas.DataFrame(rows).T`
        or `numpy.array(rows).T` do this on whole arrays."""),
    fix("Read the code: parsing tool calls", "hard", tag="GenAI",
        prompt="""This parses lines like `search refund policy` produced by a simple agent into `(tool, args)` pairs, and
        caches results per call. Two bugs: the default tool list is treated as single characters, and the cache crashes with
        `TypeError: unhashable type: 'list'`. Read the module, find both, and fix them.""",
        code="""
        DEFAULT_TOOLS = ("search")


        def parse(line, allowed=DEFAULT_TOOLS):
            tool, *args = line.split()
            if tool not in allowed:
                raise ValueError(f"unknown tool {tool!r}")
            return tool, args


        _results = {}


        def run(line, impl):
            call = parse(line)
            if call not in _results:
                tool, args = call
                _results[call] = impl(tool, *args)
            return _results[call]
        """,
        tests="""
        def raises(exc, f, *args):
            try:
                f(*args)
            except exc:
                return True
            return False
        assert parse("search refund policy") == ("search", ("refund", "policy"))
        assert raises(ValueError, parse, "s")
        assert raises(ValueError, parse, "delete everything")
        calls = []
        def impl(tool, *args):
            calls.append(args)
            return f"{tool}:{'+'.join(args)}"
        assert run("search refund policy", impl) == "search:refund+policy"
        assert run("search refund policy", impl) == "search:refund+policy"
        assert calls == [("refund", "policy")]
        """,
        hints=["What is `(\"search\")`? Then what does `\"s\" in (\"search\")` check?",
               "Star unpacking always produces a **list**. A tuple containing a list cannot be a dict key."],
        solution="""
        DEFAULT_TOOLS = ("search",)


        def parse(line, allowed=DEFAULT_TOOLS):
            tool, *args = line.split()
            if tool not in allowed:
                raise ValueError(f"unknown tool {tool!r}")
            return tool, tuple(args)


        _results = {}


        def run(line, impl):
            call = parse(line)
            if call not in _results:
                tool, args = call
                _results[call] = impl(tool, *args)
            return _results[call]
        """,
        why="""`("search")` is just a string, so `tool not in allowed` became a **substring** test: `"s"`, `"ear"` and `"search"`
        all passed as tools, a real security hole for an agent that should only run allowed tools. The trailing comma makes it a
        one-item tuple, where `in` checks whole items. Bug two: star unpacking always gives a list, so `(tool, args)` contains a
        list and cannot be a dict key. Converting with `tuple(args)` makes the call hashable and also matches what the tests
        expect from `parse`. Allow-lists should be sets (`{"search", "calc"}`, 4.4), which avoids the comma trap entirely and
        makes membership O(1)."""),
    write("A confusion matrix from pairs", "hard", tag="ML",
        prompt="""Write `confusion(pairs)` for `(actual, predicted)` label pairs, returning a dict keyed by `(actual,
        predicted)` tuples with counts, and `per_class(conf, label)` returning a `NamedTuple` `PRF(precision, recall,
        support)` for one label, where support is the number of items whose **actual** label is `label`. Use 0.0 when a ratio
        has a zero denominator.""",
        code="""
        from typing import NamedTuple

        def confusion(pairs):
            pass

        def per_class(conf, label):
            pass
        """,
        tests="""
        pairs = [("spam", "spam"), ("spam", "ham"), ("ham", "ham"), ("ham", "spam"), ("spam", "spam"), ("ham", "ham")]
        c = confusion(pairs)
        assert c == {("spam", "spam"): 2, ("spam", "ham"): 1, ("ham", "ham"): 2, ("ham", "spam"): 1}
        s = per_class(c, "spam")
        assert (round(s.precision, 4), round(s.recall, 4), s.support) == (0.6667, 0.6667, 3)
        assert per_class(c, "eggs") == (0.0, 0.0, 0)
        """,
        hints=["Count with `conf[(a, p)] = conf.get((a, p), 0) + 1`.",
               "True positives are `conf.get((label, label), 0)`. Predicted-as-label sums keys whose second item is `label`; support sums keys whose first item is `label`."],
        solution="""
        from typing import NamedTuple


        class PRF(NamedTuple):
            precision: float
            recall: float
            support: int


        def confusion(pairs):
            conf = {}
            for actual, predicted in pairs:
                conf[(actual, predicted)] = conf.get((actual, predicted), 0) + 1
            return conf


        def per_class(conf, label):
            tp = conf.get((label, label), 0)
            predicted = sum(n for (a, p), n in conf.items() if p == label)
            support = sum(n for (a, p), n in conf.items() if a == label)
            precision = tp / predicted if predicted else 0.0
            recall = tp / support if support else 0.0
            return PRF(precision, recall, support)
        """,
        why="""The tuple key `(actual, predicted)` is one cell of the confusion matrix, and unpacking `(a, p), n` in the
        comprehensions reads each cell by name. Precision divides by everything **predicted** as the label (a column of the
        matrix), recall by everything **actually** the label (a row). Returning a named tuple keeps the three numbers from being
        confused (problem 4) while still comparing equal to a plain tuple, which the last test uses. scikit-learn's
        `confusion_matrix` and `classification_report` compute the same numbers on arrays."""),
    predict("Comparing and hashing tuples", "hard",
        code="""
        print((1, "a") < (1, "b"), (1, 2) < (1, 2, 0), (2,) > (1, 99))
        print(sorted([(2, "b"), (1, "z"), (2, "a")]))
        try:
            print((1, None) < (1, 2))
        except TypeError as e:
            print("TypeError:", e)
        print((1, None) < (2, None))
        print(hash((1, (2, 3))) == hash((1, (2, 3))))
        try:
            hash((1, [2]))
        except TypeError as e:
            print("TypeError:", e)
        """,
        hints=["Comparison stops at the first position where the items differ. Later positions are never compared."],
        why="""Tuples compare position by position and stop at the first difference: `(1, 2) < (1, 2, 0)` because a shorter
        tuple that is a prefix of a longer one comes first, and `(2,) > (1, 99)` is decided by `2 > 1` alone. Comparing `(1,
        None)` with `(1, 2)` reaches `None < 2`, which Python refuses. `(1, None) < (2, None)` never compares the `None`s,
        because the first items already differ, so it works. That is why a tuple sort key with `None` in it can work on one
        dataset and crash on another. Hashing a tuple hashes every item, so a list anywhere inside makes it unhashable."""),
)

section("interview", "Interview questions",
    explain("When do you use a tuple, and when a list?", "medium", tag="Interview",
        why="""A list is for a variable-length collection of similar items that you add to, remove from or sort. A tuple is for
        a fixed-length record whose positions mean different things, and for anything that must not change: return values,
        constants, composite dict keys and set members. Tuples are immutable (safe to share, no defensive copies), hashable when
        their contents are, slightly smaller, and a tuple of constants is built once at compile time. Caveats: a tuple's
        immutability is shallow (a list inside can still change and makes it unhashable), and for records with more than two or
        three fields a named tuple or dataclass is clearer than positions."""),
    explain("Why can a tuple be a dict key but a list cannot? Can every tuple be a key?", "medium", tag="Interview",
        why="""Dict keys are found by hash, and the hash must never change while the key is in the dict, so keys must be
        immutable in everything that affects equality. A list can change, so lists are unhashable by design. A tuple cannot
        change which objects it holds, so its hash is computed from its items' hashes. But that only works if every item is
        hashable: `(1, "a")` is a valid key, `(1, [2])` raises `TypeError: unhashable type: 'list'`. To key by nested data,
        convert inner lists to tuples (and dicts to sorted item tuples or frozensets) first."""),
    explain("How does `a, b = b, a` work, and is it the same as `a = b; b = a`?", "hard", tag="Interview",
        why="""No. In `a, b = b, a`, the entire right side is evaluated first, producing the old values of `b` and `a`; only then
        are the targets assigned, left to right. So the values swap without a temporary variable. `a = b; b = a` assigns `a`
        first, and the second statement then copies the new `a` back into `b`, so both end up with the old value of `b`. Under
        the hood CPython does not even build a tuple for a two- or three-item swap: it evaluates both values onto its stack and
        swaps them there. Mention the left-to-right assignment order, which explains surprises like `i, xs[i] = 1, 9`."""),
)

recap(
    "The comma makes a tuple, not the brackets: `(1,)` is a tuple, `(1)` is not, and a stray trailing comma creates one.",
    "Unpacking evaluates the whole right side first, then assigns left to right; counts must match exactly.",
    "`first, *rest = items` collects leftovers into a list; `*` in literals and calls spreads; `zip(*rows)` transposes.",
    "Named tuples give positions names while staying tuples: immutable, hashable, and equal to plain tuples with the same values.",
    "Tuples of hashable items make composite keys, like a SQL composite primary key, and compare position by position.",
)
