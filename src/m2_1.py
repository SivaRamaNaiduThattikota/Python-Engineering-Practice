from lesson import *

lesson(
    id="m2-1", num="2.1", title="Names, objects and identity",
    intro="What `=` really does, how `is` differs from `==`, and the places where that difference turns into "
          "real bugs: missing values, caches keyed by `id()`, NaN in your features, and list methods that grab "
          "the wrong item.",
    desc="`is` vs `==`, `id`, rebinding a name versus changing an object.",
    keys="name object identity id is equality eq none singleton sentinel interning small int cache constant folding nan containers list remove index garbage",
)

term("Identity", "Which object a name points at. `id(x)` gives a number for it, `a is b` asks whether two names point at the same object.")
term("Equality", "Whether two objects count as equal by value: `a == b`. Each type decides this itself, through its `__eq__` method.")
term("Sentinel", "A unique object, such as `MISSING = object()`, used to mean \"not given\" when `None` is itself a valid value.")
term("Singleton", "A type with exactly one object. `None`, `True`, `False` and `...` are singletons, which is why `is None` is safe.")
term("Rebinding", "Pointing a name at a different object (`x = ...`). The old object is not changed by it.")

NAMES_FIG = """
<svg viewBox="0 0 640 170" role="img" aria-label="After b = a, both names point at one list. After a = a + [2], a points at a new list and b still points at the old one.">
  <defs><marker id="n1" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M0 0 L10 5 L0 10 z" style="fill:var(--label2)"/></marker></defs>
  <text x="10" y="18" class="h">After  b = a</text>
  <rect x="10" y="38" width="44" height="30" rx="8" class="box"/><text x="32" y="58" class="tk">a</text>
  <rect x="10" y="98" width="44" height="30" rx="8" class="box"/><text x="32" y="118" class="tk">b</text>
  <rect x="150" y="62" width="110" height="40" rx="10" class="box a"/><text x="205" y="87" class="w mid">[1]</text>
  <path d="M54 53 L146 76" style="stroke:var(--label2);stroke-width:2;fill:none" marker-end="url(#n1)"/>
  <path d="M54 113 L146 90" style="stroke:var(--label2);stroke-width:2;fill:none" marker-end="url(#n1)"/>
  <text x="205" y="125" class="mid">one object, two names</text>
  <text x="340" y="18" class="h">After  a = a + [2]</text>
  <rect x="340" y="38" width="44" height="30" rx="8" class="box"/><text x="362" y="58" class="tk">a</text>
  <rect x="340" y="98" width="44" height="30" rx="8" class="box"/><text x="362" y="118" class="tk">b</text>
  <rect x="480" y="30" width="130" height="40" rx="10" class="box b"/><text x="545" y="55" class="w mid">[1, 2]  new</text>
  <rect x="480" y="96" width="130" height="40" rx="10" class="box a"/><text x="545" y="121" class="w mid">[1]  old</text>
  <path d="M384 53 L476 50" style="stroke:var(--label2);stroke-width:2;fill:none" marker-end="url(#n1)"/>
  <path d="M384 113 L476 116" style="stroke:var(--label2);stroke-width:2;fill:none" marker-end="url(#n1)"/>
  <text x="545" y="158" class="mid">a moved, b did not</text>
</svg>"""

section("names", "Names point at objects",
    p("""Every value in Python is an **object** living somewhere in memory. A variable is a **name** that points at an
    object. `x = something` does one thing only: it makes the name `x` point at that object. It never copies the
    object, and it never changes the object that `x` pointed at before. Your theory notes call this a tag on an
    object; this lesson is about what that means in real code."""),
    ex("""
    a = [1]
    b = a              # b now points at the SAME list as a
    print(a is b)

    a = a + [2]        # a + [2] builds a NEW list, then a is pointed at it
    print(a, b)        # b still points at the old list
    print(a is b)
    """, "names.py"),
    fig(NAMES_FIG, "`=` moves a name. `a + [2]` built a brand-new list, so only `a` moved."),
    p("""Read every `=` as "point this name at that object". Two consequences follow, and the rest of the lesson
    depends on them:"""),
    p("""- **Several names can point at one object.** Then any change made *through* one name is visible through all
      of them, because there is only one object. (Changing objects is lesson 2.2.)
    - **Pointing a name somewhere else changes nothing else.** `a = a + [2]` did not touch the old list, so `b` was
      not affected."""),
    p("""It helps to see the two steps of an assignment separately. **First** Python evaluates the right-hand side completely,
    which produces (or finds) an object. **Then** it binds the name on the left to that object, by storing the pair "name to
    object" in a **namespace**. A namespace is literally a dictionary: at the top level of a script it is the one returned
    by `globals()`, and inside a function it is the function's local namespace (3.3). So `x = 5` is, underneath, close to
    `globals()["x"] = 5`: a key in a dict now refers to the object `5`."""),
    ex("""
    a = [1, 2]
    print(globals()["a"] is a)      # the name lives in a dict of names

    x = y = []                      # ONE list, two names: the right side is evaluated once
    x.append("shared")
    print(y, x is y)

    a, b = 1, 2
    a, b = b, a                     # the right side (2, 1) is built first, then unpacked
    print(a, b)
    """, "assignment_steps.py"),
    p("""The two steps explain both of the other lines. In `x = y = []`, the right-hand side `[]` is evaluated **once**, and
    both names are bound to that single list, so a change through `x` shows through `y`: a common bug when someone writes
    `seen = results = []` meaning two empty lists. (For immutable values like `a = b = 0` it is harmless, because nobody can
    change the `0`.) And the swap `a, b = b, a` works without a temporary variable because the right-hand side builds the
    tuple `(2, 1)` from the **current** values before any name is rebound."""),
    p("""Containers hold references too. A list does not contain its items; it contains **references** to item objects, exactly
    like names do. That is why the same object can be in two lists at once, and why putting a list inside a dict and then
    changing the list changes what the dict shows. Lesson 2.2 builds on this."""),
)

section("identity", "Identity and equality",
    p("""Every object has an **identity**: a number that stays the same for the object's whole life. `id(x)` returns
    it. Two questions sound alike but are completely different:"""),
    p("""- `a is b` asks: **is this the same object?** It compares identities. Nothing else is looked at.
    - `a == b` asks: **do these count as equal?** Python asks the object itself, by calling its `__eq__` method, and
      the object can answer whatever its type decides."""),
    callout("sql", "SQL / Power BI", """`is` is like comparing **primary keys**: same key, same row. `==` is like
    comparing **all the columns**: two different rows can have exactly the same values. A deduplication that should keep
    distinct rows but compares values instead of keys deletes real data, and the same mistake exists in Python."""),
    ex("""
    a = [1, 2, 3]
    b = [1, 2, 3]
    print(a == b, a is b)        # equal values, two different objects
    print(id(a) == id(b))        # is compares exactly these numbers

    import numpy as np
    x = np.array([1, 2, 3])
    print(x == 2)                # numpy answers == with a whole array, not True / False
    """, "is_vs_eq.py"),
    p("""Because `==` is decided by the type, it is not always a yes/no question. numpy compares element by element and
    returns an array. pandas does the same with a Series. Some libraries go further: in SQLAlchemy, `column == None`
    does not compare anything at all, it builds a piece of SQL (`IS NULL`). `is` can never be redefined by a type, so it
    always means exactly one thing and is very fast."""),
    p("""Equality also works **across types** in ways worth knowing. Numbers compare by value whatever their type, so `1 == 1.0`
    and even `1 == True` are true (`bool` is a subtype of `int`). Containers of different types are not equal even with the
    same contents: `[1, 2] == (1, 2)` is false. And for an object whose type does not define its own `__eq__`, Python falls
    back to identity: two separate `object()` instances are never equal. The negated forms follow the same split: `!=` asks
    the type, `is not` compares identities, and `a is not b` is the readable way to write `not (a is b)`."""),
    ex("""
    print(1 == 1.0, 1 == True, [1, 2] == (1, 2), list((1, 2)) == [1, 2])
    o1, o2 = object(), object()
    print(o1 == o2, o1 == o1, o1 is not o2)
    print({"a": 1} == {"a": 1.0}, "1" == 1)
    """, "equality_rules.py"),
    p("""The last line shows a real data-cleaning trap: the string `"1"` and the number `1` are never equal. Ids read from a CSV
    are strings, ids from a JSON API are often numbers, and a join or a membership test between them silently finds
    nothing. Convert to one type at the boundary, where the data comes in."""),
    callout("key", "Rule of thumb", """Use `==` to compare values. Use `is` only to ask "is this that exact object?":
    with `None` and the other singletons, with sentinels, and when you really mean identity (problem 14). Never use
    `is` to compare numbers or strings: Python even warns you (`SyntaxWarning: "is" with 'int' literal`)."""),
)

section("singletons", "None, singletons and sentinels",
    p("""A **singleton** is a type that only ever has one object. `None`, `True`, `False` and `...` (Ellipsis) are
    singletons: every `None` in your program is the same object. That is why `x is None` is the right test. It is exact
    (nothing can pretend to be `None`), and it works on numpy arrays and pandas objects, where `x == None` either returns an
    array or raises an error inside an `if`."""),
    ex("""
    def first(rows):
        return rows[0] if rows else None

    r = first([])
    print(r is None)
    print(type(None)() is None)   # even asking the type for a new None gives the same one
    """, "none.py"),
    p("""Sometimes `None` is a valid value, so it cannot also mean "not given". An LLM API is a good example:
    `stop=None` can mean "clear the stop sequences", which is different from "use the server default". The standard answer
    is a **sentinel**: a private object created once, which no caller can pass by accident."""),
    ex("""
    MISSING = object()            # a unique object; nothing else is ever this object

    def get_setting(settings, key, default=MISSING):
        if key in settings:
            return settings[key]
        if default is MISSING:
            raise KeyError(key)
        return default            # includes default=None, which is a real choice

    cfg = {"model": "small", "stop": None}
    print(get_setting(cfg, "stop"))
    print(get_setting(cfg, "temperature", None))
    try:
        get_setting(cfg, "temperature")
    except KeyError as e:
        print("KeyError:", e)
    """, "sentinel.py"),
    p("""`dict.get`, `getattr` and many library functions use exactly this trick inside. Recognising it makes a lot of
    library code easier to read."""),
)

section("caching", "Caching is not a rule",
    p("""CPython, the normal Python, saves memory by reusing some immutable objects. Small integers from -5 to 256 are
    created once and shared. Many short strings that look like names are **interned**: kept in one shared copy. And when
    the same constant appears twice in one piece of compiled code, the compiler may store it only once. All of this
    is an **implementation detail**: it can differ between Python versions, between the REPL and a script, and between
    a literal and a value computed at run time."""),
    ex("""
    a = 256; b = 256
    print(a is b)                       # small ints are shared

    c = int("257"); d = int("257")
    print(c is d, c == d)               # computed at run time: two objects

    s1 = "hello_world"
    s3 = "".join(["hello", "_world"])
    print(s1 == s3, s1 is s3)           # built at run time: equal, not identical
    """, "caching.py"),
    p("""So `is` on numbers or strings can be `True` in your test and `False` in production with other data. Values
    that come from files, APIs and databases are created at run time, so they are usually separate objects even when they
    are equal. Always compare them with `==`."""),
    p("""The reason for caching is memory and speed: a program creates small numbers and identifier-like strings all the time,
    and sharing one copy saves allocations, and lets dictionary lookups on interned strings compare by identity first. You
    can use the same trick deliberately with `sys.intern`, which returns the one shared copy of a string. It is worth it when
    you hold millions of copies of a few distinct strings, such as labels or category names in a large dataset loaded row by
    row; pandas solves the same problem with its `category` dtype."""),
    ex("""
    import sys

    rows = ["".join(["sp", "am"]) for _ in range(3)]       # three separate but equal strings
    print(rows[0] == rows[1], rows[0] is rows[1])
    shared = [sys.intern(r) for r in rows]
    print(shared[0] is shared[1] is shared[2])
    """, "intern.py"),
)

section("containers", "Containers check identity first",
    p("""When a list, tuple or dict looks for a value (for `in`, `==`, `count`, `index`, `remove` or a dict key), it
    compares each item with `x is item or x == item`: identity first, equality second. Usually you never notice. Two
    cases make it visible."""),
    p("""**NaN.** The float `nan` ("not a number", what pandas uses for missing numbers) is defined as not equal to
    anything, itself included: `nan == nan` is `False`. But the identity check comes first, so the **same** nan object is
    still found in a list."""),
    ex("""
    nan = float("nan")
    print(nan == nan)                   # NaN equals nothing, not even itself
    print(nan in [nan])                 # found anyway: the identity check comes first
    print(float("nan") in [nan])        # a different NaN object: not found
    """, "nan.py"),
    callout("sql", "SQL / Power BI", """NaN behaves like SQL's `NULL`: `NULL = NULL` is not true, so you write
    `IS NULL`. In pandas the equivalent is `s.isna()`, never `s == np.nan` (problem 17)."""),
    p("""**Equal but different objects.** `list.remove(x)` deletes the **first item equal to** `x`, and
    `list.index(x)` returns the position of the first equal item. If the list holds two equal objects (two chat
    messages that both say "ok"), they find the first one, which may not be the one you meant (problem 15)."""),
)

section("lifetime", "Object lifetime and id reuse",
    p("""`del x` deletes the **name** `x`, not the object. An object stays alive as long as at least one name or
    container still points at it. When nothing points at it any more, Python frees it, and its memory can be reused for
    the next object. Since `id()` is based on that memory, **an id can be reused** after its object is gone."""),
    ex("""
    a = [1, 2, 3]
    b = a
    del a                 # removes the name a; the list is still reachable through b
    print(b)

    # Each [] here dies right after id() reads it, so the second one can land in the same
    # memory. The result depends on the run: never rely on it either way.
    print(id([]) == id([]))
    """, "lifetime.py"),
    p("""How does Python know when nothing points at an object? CPython keeps a **reference count** in every object: the number of
    names, containers and other places that currently refer to it. Binding a name, putting the object in a list or passing it
    to a function adds one; a name being rebound or deleted, or the list being emptied, subtracts one. When the count reaches
    zero, the object is freed immediately. `sys.getrefcount(x)` shows the count (it reports one extra, for its own
    argument)."""),
    ex("""
    import sys, gc

    data = ["a large", "list"]
    before = sys.getrefcount(data)
    holder = [data, data]                  # two more references, from inside a list
    print(sys.getrefcount(data) - before)
    holder.clear()
    print(sys.getrefcount(data) - before)

    a = []
    a.append(a)                            # a list that contains itself: a reference cycle
    del a                                  # the count never reaches zero by itself...
    print(gc.collect() >= 1)               # ...so the cycle collector frees it
    """, "refcount.py"),
    p("""Reference counting cannot free a **cycle**, a group of objects that refer to each other but are not reachable from the
    program, so CPython also runs a cycle-detecting garbage collector from time to time (`gc.collect()` forces a run). In
    everyday code you rarely think about either. They matter when memory keeps growing in a long-running service: a global
    cache, a list of past requests or a closure (3.4) that holds a reference keeps every object it reaches alive, however
    large, which is the usual cause of "memory leaks" in Python."""),
    callout("warn", "Never key long-lived data by id()", """`id()` is only unique among objects that are alive **at the
    same time**. A cache keyed by `id(prompt)` misses when an equal prompt arrives as a new object, and can even return
    another prompt's answer once the old object is freed and its id reused (problem 8). Key by the value instead."""),
)

section("warmup", "Warm-up",
    predict("Rebinding immutable values", "easy",
        code="""
        model = "gpt"
        alias = model
        model = model + "-mini"
        print(model, alias)
        print(model is alias)

        retries = 3
        limit = retries
        retries += 1
        print(retries, limit, retries is limit)
        """,
        hints=["Strings and ints cannot be changed, so `+` and `+=` on them always build a new object and move the name."],
        why="""`model + "-mini"` builds a new string and points `model` at it. `alias` still points at the old `"gpt"`.
        `retries += 1` on an int works the same way: a new int object `4`, while `limit` keeps `3`. Lesson 2.2 shows that
        `+=` on a **list** is different: it changes the list in place."""),
    write("Missing fields in an LLM's JSON", "easy", tag="GenAI",
        prompt="""An LLM was asked to return JSON with some required fields. Write `missing_fields(record, required)` that
        returns the required keys that are **absent or `None`**, in the order of `required`. A value of `0`, `""` or `[]`
        is a real answer and must not count as missing.""",
        code="""
        def missing_fields(record, required):
            pass
        """,
        tests="""
        r = {"title": "Refund", "priority": 0, "tags": [], "owner": None}
        assert missing_fields(r, ["title", "priority", "tags", "owner", "due"]) == ["owner", "due"]
        assert missing_fields({}, ["a"]) == ["a"]
        assert missing_fields({"a": ""}, ["a"]) == []
        assert missing_fields({"a": False}, ["a"]) == []
        """,
        hints=["`record.get(key)` returns `None` both when the key is absent and when the value is `None`, which is exactly the rule here.",
               "Test with `is None`. A plain `if not value` would also catch `0`, `\"\"` and `[]`."],
        solution="""
        def missing_fields(record, required):
            return [key for key in required if record.get(key) is None]
        """,
        why="""`record.get(key)` gives `None` for an absent key, so one `is None` test covers both cases. The trap is
        `if not record.get(key)`: priority `0`, an empty tag list and `False` are valid answers, and truthiness would report
        them as missing (the COALESCE trap from 1.1). In production you would validate this with Pydantic (Module 11), and
        it uses the same `is None` idea inside."""),
    predict("Equal or the same?", "easy",
        code="""
        a = [1, 2]
        b = [1, 2]
        c = a
        print(a == b, a is b)
        print(c == a, c is a)
        print(a is not b, not a is b)
        print(None is None, type(None)() is None)
        """,
        hints=["`a is not b` is one operator, the opposite of `is`. `not a is b` reads as `not (a is b)`."],
        why="""`a` and `b` are two lists with equal values: `==` is `True`, `is` is `False`. `c = a` points `c` at the
        same list, so both are `True`. `a is not b` and `not a is b` mean the same thing; Python style prefers
        `is not`. `None` is a singleton, and even calling its type returns that same object."""),
    fix("The numpy check that crashes", "easy", tag="ML",
        prompt="""`describe` should say `"missing"` for `None` and `"array of N"` for a numpy array. It crashes on
        `np.array([1, 2])`. Run it, read the error, then fix it.""",
        code="""
        import numpy as np

        def describe(x):
            if x == None:
                return "missing"
            return f"array of {len(x)}"
        """,
        tests="""
        import numpy as np
        assert describe(None) == "missing"
        assert describe(np.array([1, 2])) == "array of 2"
        assert describe(np.array([5])) == "array of 1"
        assert describe(np.array([])) == "array of 0"
        """,
        hints=["What does `np.array([1, 2]) == None` return? Then what does `if` do with that?"],
        solution="""
        import numpy as np

        def describe(x):
            if x is None:
                return "missing"
            return f"array of {len(x)}"
        """,
        why="""numpy answers `==` element by element: `np.array([1, 2]) == None` is `array([False, False])`. An `if` then
        has to turn a two-item array into one True / False, which numpy refuses: "The truth value of an array with more
        than one element is ambiguous". An empty array fails the same way ("The truth value of an empty array is
        ambiguous"), and a one-item array happens to work, so a quick test with `np.array([5])` hides the bug.
        `x is None` never asks the array anything. This exact crash is common in ML code
        that checks optional arrays such as `sample_weight` or `mask`."""),
)

section("medium", "Medium",
    write("Optional API parameters with a sentinel", "medium", tag="GenAI",
        prompt="""Write `make_payload(prompt, *, temperature=MISSING, stop=MISSING)` that builds the request body for an
        LLM API. Arguments that were **not passed** must be left out completely, so the server uses its own defaults.
        But an argument passed as `None` must be **included** as `None`: for this API, `"stop": None` means "clear the stop
        sequences". (The `*` makes `temperature` and `stop` keyword-only; lesson 3.2 covers it.)""",
        code="""
        MISSING = object()

        def make_payload(prompt, *, temperature=MISSING, stop=MISSING):
            pass
        """,
        tests="""
        assert make_payload("hi") == {"prompt": "hi"}
        assert make_payload("hi", temperature=0) == {"prompt": "hi", "temperature": 0}
        assert make_payload("hi", stop=None) == {"prompt": "hi", "stop": None}
        assert make_payload("hi", temperature=0.2, stop=["###"]) == {"prompt": "hi", "temperature": 0.2, "stop": ["###"]}
        """,
        hints=["Start from `{\"prompt\": prompt}` and add each key only when its argument `is not MISSING`.",
               "Why not `if temperature:`? Look at the second test."],
        solution="""
        MISSING = object()

        def make_payload(prompt, *, temperature=MISSING, stop=MISSING):
            payload = {"prompt": prompt}
            if temperature is not MISSING:
                payload["temperature"] = temperature
            if stop is not MISSING:
                payload["stop"] = stop
            return payload
        """,
        why="""Three cases have to stay apart: not passed, passed as `None`, passed as a real value. `None` cannot mark
        "not passed" because it is one of the values the caller may send, and truthiness fails even earlier:
        `temperature=0` is falsy but is the most common setting of all. `MISSING` is a fresh object that only this module
        knows, so `is not MISSING` is true exactly when the caller passed something. Real SDKs use the same pattern;
        the OpenAI Python client calls its sentinel `NOT_GIVEN`."""),
    predict("NaN in a list and a dict", "medium", tag="ML",
        code="""
        nan = float("nan")
        print(nan == nan)
        print(nan in [nan], float("nan") in [nan])
        print([nan] == [nan], [nan] == [float("nan")])
        print({nan: "a"}.get(nan), {nan: "a"}.get(float("nan")))
        print([1, nan, nan].count(nan))
        """,
        hints=["Every container comparison is `x is item or x == item`. Each `float(\"nan\")` call makes a new object."],
        why="""`nan == nan` is `False` by definition. But lists compare items with "identity first", so the **same** nan
        object is found, counted and compared equal, while a new `float("nan")` is not. Dict lookups work the same way:
        the key is found only through the identical object. This is why missing values must be found with `math.isnan`,
        `np.isnan` or `pd.isna`, never with `==` or `in`."""),
    trace("Names moving, objects changing", "medium",
        prompt="""Fill in `a`, `b` and whether `a is b` after each line. Type values the way Python prints them, such as
        `[1, 2]` and `True`.""",
        code="""
        a = [1]
        b = a  # row: "b = a"
        a = a + [2]  # row: "a = a + [2]"
        b.append(3)  # row: "b.append(3)"
        a = b  # row: "a = b"
        """,
        trace_vars=["a", "b", "a is b"],
        hints=["`a + [2]` builds a new list. `b.append(3)` changes the list `b` points at, without moving any name."],
        why="""After `b = a` both names share one list. `a = a + [2]` builds a new list `[1, 2]` and moves only `a`.
        `b.append(3)` changes the old list in place, so `b` is `[1, 3]` and `a` is untouched. `a = b` points `a` back at
        that same list, so they are identical again. Two kinds of steps: moving a name (`=`) and changing an object
        (`append`). Lesson 2.2 is all about the second kind."""),
    fix("A cache keyed by id()", "medium", tag="GenAI",
        prompt="""To save money, this wraps an LLM call in a cache. Two prompts with the same text should cost one call,
        but they cost two. Fix the cache key.""",
        code="""
        calls = []

        def fake_llm(prompt):
            calls.append(prompt)
            return f"answer to: {prompt}"

        _cache = {}

        def cached_complete(prompt):
            key = id(prompt)
            if key not in _cache:
                _cache[key] = fake_llm(prompt)
            return _cache[key]
        """,
        tests="""
        p1 = "".join(["What is ", "RAG?"])
        p2 = "".join(["What is ", "RAG?"])
        assert p1 == p2 and p1 is not p2
        assert cached_complete(p1) == "answer to: What is RAG?"
        assert cached_complete(p2) == "answer to: What is RAG?"
        assert len(calls) == 1
        """,
        hints=["Prompts built at run time (from templates, user input, files) are separate objects even when the text is equal.",
               "A `str` can be a dict key directly."],
        solution="""
        calls = []

        def fake_llm(prompt):
            calls.append(prompt)
            return f"answer to: {prompt}"

        _cache = {}

        def cached_complete(prompt):
            if prompt not in _cache:
                _cache[prompt] = fake_llm(prompt)
            return _cache[prompt]
        """,
        why="""`id(prompt)` identifies the object, not the text, so equal prompts get different keys and miss. The worse
        bug is hidden: once a prompt object is freed, its id can be reused by a **different** prompt, which would then get
        the old prompt's cached answer. Key by the value itself. For long prompts, real caches key by a hash of the text plus
        the model and settings, for example `hashlib.sha256(f"{model}|{prompt}".encode()).hexdigest()`, since a different
        model or temperature must not share an answer."""),
    choose("Checking for None at scale", "medium",
        prompt="Both count the missing records among 20,000 objects whose class defines `__eq__` in Python. Which is faster?",
        setup="""class Record:
    def __init__(self, v):
        self.v = v
    def __eq__(self, other):
        return isinstance(other, Record) and self.v == other.v

records = [Record(i) for i in range(20000)] + [None] * 100""",
        options={
            "a": "missing = sum(1 for r in records if r == None)",
            "b": "missing = sum(1 for r in records if r is None)",
        },
        answer="b",
        hints=["What does `r == None` have to do for every `Record`?"],
        why="""`r == None` calls `Record.__eq__` for each of the 20,000 objects, which is a Python function call doing an
        `isinstance` check every time. `r is None` compares two identities, one machine-level comparison with no
        call at all. On objects with expensive or unusual `__eq__` (ORM rows, dataframes, arrays) the gap grows, and
        `== None` may not even return a bool."""),
    write("Merge retriever results without repeats", "medium", tag="RAG",
        prompt="""A hybrid retriever gets chunks from BM25 and from a vector search. Both return **references to the same
        chunk objects** from one shared store, so one chunk often appears in both lists. Write `merge_results(first, second)`
        that keeps the order of `first` then `second` and drops an item if **that same object** was already kept. Two
        separate chunks with equal content are different index entries and must both be kept. Chunks are dicts, which
        cannot go in a set.""",
        code="""
        def merge_results(first, second):
            pass
        """,
        tests="""
        c1 = {"doc": "faq.md", "text": "Reset your password from Settings."}
        c2 = {"doc": "faq.md", "text": "Reset your password from Settings."}
        c3 = {"doc": "guide.md", "text": "Contact support."}
        out = merge_results([c1, c3], [c3, c2, c1])
        assert len(out) == 3
        assert out[0] is c1 and out[1] is c3 and out[2] is c2
        assert merge_results([], []) == []
        assert len(merge_results([c1, c1], [])) == 1
        """,
        hints=["A dict cannot go in a set, but its `id()` can, and every chunk here is alive while the function runs.",
               "Why not `if item not in out`? `in` falls back to `==`, so it would drop `c2`."],
        solution="""
        def merge_results(first, second):
            seen = set()
            out = []
            for chunk in first + second:
                if id(chunk) not in seen:
                    seen.add(id(chunk))
                    out.append(chunk)
            return out
        """,
        why="""Keying by `id()` is safe **here**, because every chunk is alive (held by the input lists) for the whole
        call, so no id can be reused, unlike the long-lived cache in problem 8. A set of ids makes each check O(1); the
        tempting `if chunk not in out` is O(n) per item and compares by `==`, so it would also drop `c2`, an equal but
        separate chunk. Whether equal-content chunks should be merged is a separate decision. If they should, deduplicate by
        a content key such as `(doc, text)`."""),
    refactor("Read a flag from config", "medium",
        prompt="""This reads a true/false setting that may arrive as a bool, a string, an int or `None`. Clean it up:
        `is None` instead of `== None`, `isinstance` instead of `type(...) ==`, and no repeated work. Keep the tests green.
        Careful with the order of the checks.""",
        code="""
        def read_flag(value):
            if value == None:
                return False
            if type(value) == bool:
                return value
            if type(value) == str:
                if value.strip().lower() == "true" or value.strip().lower() == "yes" or value.strip().lower() == "1":
                    return True
                return False
            if type(value) == int:
                return value != 0
            raise TypeError(f"cannot read a flag from {value!r}")
        """,
        tests="""
        def raises(exc, f, *args):
            try:
                f(*args)
            except exc:
                return True
            return False
        assert read_flag(None) is False
        assert read_flag(True) is True and read_flag(False) is False
        assert read_flag(" Yes ") is True and read_flag("no") is False and read_flag("1") is True
        assert read_flag(2) is True and read_flag(0) is False
        assert raises(TypeError, read_flag, 1.5)
        """,
        hints=["`bool` is a subclass of `int` (1.1), so `isinstance(True, int)` is `True`. Which check must come first?",
               "Strip and lower the string once, then test membership: `in {\"true\", \"yes\", \"1\"}`."],
        solution="""
        def read_flag(value):
            if value is None:
                return False
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.strip().lower() in {"true", "yes", "1"}
            if isinstance(value, int):
                return value != 0
            raise TypeError(f"cannot read a flag from {value!r}")
        """,
        why="""`isinstance` also accepts subclasses, which is usually what you want, but here it changes behaviour if the
        order is wrong: with the `int` check first, `True` would be treated as the int 1. Keeping `bool` first preserves the
        old behaviour. `is None` replaces `== None` for the reasons in this lesson. The string is normalised once and checked
        with a set, which reads like the rule it implements."""),
    predict("Read the code: a shared system message", "medium", tag="GenAI",
        code="""
        SYSTEM = {"role": "system", "content": "You are helpful."}

        def new_chat():
            return [SYSTEM]

        chat_a = new_chat()
        chat_b = new_chat()
        chat_a.append({"role": "user", "content": "hi"})
        print(len(chat_a), len(chat_b))
        print(chat_a is chat_b, chat_a[0] is chat_b[0])

        chat_a[0]["content"] = "You are terse."
        print(chat_b[0]["content"])
        print(SYSTEM["content"])
        """,
        hints=["`[SYSTEM]` is a new list each call, but what does that new list contain?"],
        why="""Each call builds a **new list**, so the chats are separate and the `append` affects only `chat_a`. But both
        lists hold the **same** `SYSTEM` dict. Changing it through `chat_a[0]` changes it for every chat and for the module
        constant itself. In a chat server this means one user's edited system prompt leaks into every other conversation.
        The fix, `[dict(SYSTEM)]`, is exactly the copying topic of lesson 2.3."""),
)

section("hard", "Hard",
    predict("When does caching show?", "hard",
        code="""
        a = 256; b = 256
        print(a is b)
        c = int("257"); d = int("257")
        print(c is d, c == d)
        e = 257; f = 257
        print(e is f)
        s1 = "hello_world"; s2 = "hello" + "_world"
        print(s1 is s2)
        s3 = "".join(["hello", "_world"])
        print(s1 is s3, s1 == s3)
        """,
        hints=["Some objects are made when the code is compiled (constants), others while it runs.",
               "When the same constant appears twice in one compiled block, the compiler may store it once."],
        why="""Small ints up to 256 are shared, so `a is b`. `int("257")` runs twice at run time and builds two objects. But
        `e = 257; f = 257` sit in the same compiled code, and the compiler stored the constant 257 **once**, so both names point
        at it. Typed as two separate lines in the REPL, each line is compiled on its own and you get `False`. `"hello" +
        "_world"` is folded into one constant at compile time and interned, while `"".join(...)` builds a new string at run
        time. Same values, different answers: that is why `is` on numbers and strings is never correct."""),
    write("Find this exact object in a list", "hard", tag="GenAI",
        prompt="""An agent keeps a list of tool-call records, and the UI holds a reference to one of them. Write
        `index_of(items, target)` that returns the position of **that exact object**. `items.index(target)` is not
        enough: it returns the first **equal** record. Raise `ValueError` if the object is not in the list, like
        `list.index`.""",
        code="""
        def index_of(items, target):
            pass
        """,
        tests="""
        def raises(exc, f, *args):
            try:
                f(*args)
            except exc:
                return True
            return False
        a = {"tool": "search", "args": {"q": "refund policy"}}
        b = {"tool": "search", "args": {"q": "refund policy"}}
        items = [b, a]
        assert items.index(a) == 0
        assert index_of(items, a) == 1
        assert index_of(items, b) == 0
        assert raises(ValueError, index_of, items, dict(a))
        assert raises(ValueError, index_of, [], a)
        """,
        hints=["`enumerate` and an `is` check. What should happen after the loop?"],
        solution="""
        def index_of(items, target):
            for i, item in enumerate(items):
                if item is target:
                    return i
            raise ValueError(f"object not in list: {target!r}")
        """,
        why="""`list.index` checks `item is target or item == target` from the left, so with equal records it stops at
        the first equal one. Checking `is` alone finds only the exact object. Raising instead of returning -1 keeps the
        same contract as `list.index`, so callers cannot silently use -1, which would mean "last item" if used as an
        index. That is a real off-by-one trap."""),
    fix("Read the code: deleting the wrong message", "hard", tag="GenAI",
        prompt="""This is a small chat-history store. The UI keeps the message object returned by `add` and later asks to
        delete or edit **that** message. When the user has typed the same text twice ("ok"), deleting or editing the second
        one changes the first. Read the whole module, find both bugs, and fix them.""",
        code="""
        SYSTEM = {"role": "system", "content": "Answer from the documents only."}


        def new_history():
            return [dict(SYSTEM)]


        def add(history, role, content):
            msg = {"role": role, "content": content}
            history.append(msg)
            return msg            # the UI keeps this object to edit or delete it later


        def delete(history, msg):
            \"\"\"Delete exactly this message.\"\"\"
            if msg is history[0]:
                raise ValueError("the system prompt cannot be deleted")
            history.remove(msg)


        def edit(history, msg, content):
            \"\"\"Replace the text of exactly this message, return the new message.\"\"\"
            i = history.index(msg)
            history[i] = {"role": msg["role"], "content": content}
            return history[i]
        """,
        tests="""
        def raises(exc, f, *args):
            try:
                f(*args)
            except exc:
                return True
            return False
        h = new_history()
        first = add(h, "user", "ok")
        add(h, "assistant", "Noted.")
        second = add(h, "user", "ok")
        delete(h, second)
        assert [m["content"] for m in h] == [SYSTEM["content"], "ok", "Noted."]
        assert h[1] is first
        h2 = new_history()
        add(h2, "user", "ok")
        add(h2, "assistant", "Sure.")
        last = add(h2, "user", "ok")
        new = edit(h2, last, "ok, thanks")
        assert h2[1]["content"] == "ok" and h2[3]["content"] == "ok, thanks" and new is h2[3]
        assert raises(ValueError, delete, h2, h2[0])
        assert raises(ValueError, delete, h2, {"role": "user", "content": "ok"})
        """,
        hints=["`history.remove(msg)` and `history.index(msg)` both look for the first **equal** message.",
               "Write one helper that finds the position with `is` (like problem 14), then use it in both functions.",
               "The last test deletes an equal message that is not in the history. It must raise, not delete the real one."],
        solution="""
        SYSTEM = {"role": "system", "content": "Answer from the documents only."}


        def new_history():
            return [dict(SYSTEM)]


        def add(history, role, content):
            msg = {"role": role, "content": content}
            history.append(msg)
            return msg


        def _position(history, msg):
            for i, m in enumerate(history):
                if m is msg:
                    return i
            raise ValueError("message is not in this history")


        def delete(history, msg):
            \"\"\"Delete exactly this message.\"\"\"
            i = _position(history, msg)
            if i == 0:
                raise ValueError("the system prompt cannot be deleted")
            del history[i]


        def edit(history, msg, content):
            \"\"\"Replace the text of exactly this message, return the new message.\"\"\"
            i = _position(history, msg)
            history[i] = {"role": msg["role"], "content": content}
            return history[i]
        """,
        why="""Both bugs are the same one: `remove` and `index` match by equality, so two messages with the same role and
        text are interchangeable to them. The code even says "exactly this message" in its docstrings, which is an identity
        requirement. A single `_position` helper that compares with `is` fixes both and also rejects an equal copy that is
        not in the history (the last test), instead of deleting a real message by accident. Real chat apps usually avoid the
        whole problem by giving each message a unique id field, which is an identity you control and can store in a
        database."""),
    write("Repeated rows: objects or values?", "hard", tag="Data work",
        prompt="""A dataset of rows (lists) may have been built by repeating one list object, such as `[row] * 3`, which
        makes every "row" the same object. Write `object_and_value_counts(rows)` that returns `(distinct_objects,
        distinct_values)`. Lists are not hashable, so think about what you can put in a set.""",
        code="""
        def object_and_value_counts(rows):
            pass
        """,
        tests="""
        r = [0, 0]
        assert object_and_value_counts([r, r, r]) == (1, 1)
        assert object_and_value_counts([[0, 0], [0, 0], [1, 2]]) == (3, 2)
        assert object_and_value_counts([r] * 3 + [[0, 0]]) == (2, 1)
        assert object_and_value_counts([]) == (0, 0)
        """,
        hints=["Distinct objects: a set of `id(row)`. Distinct values: a set of something hashable built from each row.",
               "`tuple(row)` is hashable when the items are."],
        solution="""
        def object_and_value_counts(rows):
            objects = {id(row) for row in rows}
            values = {tuple(row) for row in rows}
            return len(objects), len(values)
        """,
        why="""If `distinct_objects` is smaller than `len(rows)`, some rows are the same object, and writing to one changes
        all of them: the `[[0] * 3] * 3` grid trap from your theory notes, and the root of several pandas surprises. Lesson
        2.3 fixes it. `id()` is safe again because all rows are alive during the call. `tuple(row)` turns a list into a
        hashable value with the same contents, the standard way to deduplicate lists by value."""),
    predict("NaN in pandas", "hard", tag="ML",
        code="""
        import numpy as np
        import pandas as pd

        s = pd.Series([1.0, np.nan, 3.0, np.nan])
        print((s == np.nan).sum(), s.isna().sum())
        print(np.nan is np.nan, float("nan") is np.nan)
        print(np.nan in [np.nan], np.nan in s.tolist())
        """,
        hints=["`s == np.nan` compares every value with NaN using `==`.",
               "`np.nan` is one float object made when numpy was imported. Does `tolist()` give back that same object?"],
        why="""`s == np.nan` is `False` for every row, NaN included, so the count is 0: a filter like
        `df[df["x"] == np.nan]` silently returns an empty frame. `isna()` is the correct test. `np.nan` is a single object,
        so `np.nan is np.nan` is `True`, while `float("nan")` is a new one. The last line is the subtle one: the Series stores
        raw numbers, not Python objects, so `tolist()` builds **new** float objects, and `np.nan in` that list no longer finds
        a match through identity. NaN logic that "works" in a small test list can fail on real data for exactly this reason."""),
)

section("interview", "Interview questions",
    explain("What is the difference between `is` and `==`, and when is `is` the right choice?", "medium", tag="Interview",
        why="""`is` checks identity: whether two names point at the same object. It cannot be overridden and is a single
        pointer comparison. `==` checks equality by calling the left object's `__eq__`, which each type defines, so it can
        be slow, can return a non-bool (numpy, pandas, SQLAlchemy), and two different objects can be equal. Use `is` for
        singletons (`None`, `True`, `False`), for sentinels, and when you really mean "this exact object" (finding a specific
        message, deduplicating references). Never use it for numbers or strings, because caching makes the result depend on
        the Python version and on how the value was created. Strong answer: mention that containers use "identity, then
        equality", which explains `nan in [nan]`."""),
    explain("When is `None` not enough as a default, and what do you use instead?", "medium", tag="Interview",
        why="""When `None` is itself a meaningful value the caller may pass. Then you cannot tell "not passed" from "passed
        `None`". Examples: an API where `stop=None` clears stop sequences, a cache where `None` is a valid stored result, or
        `dict.get` with a default. The answer is a sentinel: `MISSING = object()` at module level, checked with
        `is MISSING`. It is unique, so no caller can pass it by accident. Mention that real libraries do this (the OpenAI
        client's `NOT_GIVEN`, `dataclasses.MISSING`), and that typing it well uses an enum with one member or `typing.Final`,
        which shows you have read library code."""),
    explain("Why can `a = 1000; b = 1000; a is b` be `True` in a script but `False` in the REPL?", "hard", tag="Interview",
        why="""The REPL compiles each line separately, so each `1000` becomes its own int object and `is` is `False`. In a
        script (or one line with `;`), both literals are in the same compiled code object, and the compiler stores the
        constant once, so both names point at the same object. Integers from -5 to 256 are always shared, so they are `True`
        everywhere. None of this is guaranteed by the language. It is CPython behaviour that can change between versions,
        so code must never depend on it: compare numbers with `==`. The interviewer is checking whether you know that
        `is` compares identity, not value."""),
)

recap(
    "`=` points a name at an object. It never copies, and moving a name changes no object.",
    "`is` = same object (identity, cannot be overridden). `==` = equal by the type's own rules, and may not even return a bool.",
    "Use `is` for `None`, the other singletons and sentinels. Never for numbers or strings: caching makes it unreliable.",
    "Containers compare with \"identity, then equality\": that is why `nan in [nan]` is `True`, and why `remove` and `index` can pick the wrong equal item.",
    "`id()` is unique only among live objects. Safe within one call, wrong as a long-lived cache key.",
)
