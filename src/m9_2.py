from lesson import *

lesson(
    id="m9-2", num="9.2", title="Dunder methods",
    intro="Double-underscore methods are the hooks that make your objects work with Python's syntax and built-ins: "
          "`print`, `==`, `len`, `in`, `[]`, `+`, `sorted`, `if`, and calling. `__repr__` and `__str__`, equality and "
          "hashing and the rule that links them, ordering, the container protocol, arithmetic with `NotImplemented`, and "
          "callable objects. Applied to money, token usage, versions, batches and vectors.",
    desc="`__repr__`, `__eq__` and `__hash__`, ordering, containers and truthiness.",
    keys="dunder magic method data model protocol __repr__ __str__ __eq__ __hash__ __lt__ total_ordering __len__ __getitem__ __contains__ __iter__ __bool__ __add__ __radd__ __mul__ __call__ notimplemented hashable",
)

term("Dunder method", "A method named with double underscores, such as `__len__`, that Python calls for you when you use syntax or a built-in (`len(x)`).")
term("Protocol", "A set of dunder methods that makes an object usable in some way: define `__len__` and `__getitem__` and it behaves like a sequence.")
term("NotImplemented", "A special value an operator method returns to say \"I cannot handle this type\", so Python can try the other operand's method.")

section("hooks", "Hooks for syntax and built-ins",
    p("""Python's syntax and built-in functions are translated into method calls on your objects. `len(x)` calls `x.__len__()`; `x == y`
    calls `x.__eq__(y)`; `x + y` calls `x.__add__(y)`; `x[i]` calls `x.__getitem__(i)`; `str(x)` calls `x.__str__()`; `if x:` calls
    `x.__bool__()`. These methods are called **dunder** methods ("double underscore") or "special methods", and together they form
    Python's **data model**. Defining them in your class makes your objects behave like built-in ones, with the same syntax."""),
    p("""This is how libraries feel native. A NumPy array supports `a + b` and `a[1:3]` because it defines `__add__` and `__getitem__`; a
    pandas DataFrame supports `df["col"]` and `len(df)`; a PyTorch model is called like a function, `model(x)`, because it defines
    `__call__`. The rule for your own code: implement the dunders that match what your object **is** (a container, a number, a value),
    and you almost never call them directly; you use the syntax, and Python calls them."""),
    ex("""
    class Playlist:
        def __init__(self, songs):
            self.songs = list(songs)

        def __len__(self):
            return len(self.songs)

        def __getitem__(self, i):
            return self.songs[i]

        def __contains__(self, song):
            return song in self.songs

    p = Playlist(["intro", "verse", "outro"])
    print(len(p), p[0], p[-1], "verse" in p, p[1:])
    print([s.upper() for s in p])        # iteration works through __getitem__ (10.1)
    print(len(p) == p.__len__())
    """, "hooks.py"),
    p("""Defining `__getitem__` with integer indexes already makes the object iterable: a `for` loop falls back to calling `p[0]`, `p[1]`,
    ... until `IndexError`. Lesson 10.1 shows the proper iteration protocol, `__iter__`. Note that dunder methods are looked up on
    the **class**, not the instance: assigning `p.__len__ = ...` on one object does not change what `len(p)` does (problem 16)."""),
)

section("repr", "`__repr__` and `__str__`: how an object prints",
    p("""Without help, an object prints as `<__main__.Money object at 0x7f...>`, which tells you nothing in a log or a debugger. Two methods
    control the text. **`__repr__`** is for developers: it should be unambiguous and, ideally, look like the code that would recreate
    the object, `Money(12.5, 'EUR')`. **`__str__`** is for end users: readable, `12.50 EUR`. `print(x)` and `str(x)` use `__str__`;
    the REPL, debuggers, `repr(x)`, the `!r` conversion in f-strings and the display of objects **inside containers** use
    `__repr__`. If you define only one, define `__repr__`: `str` falls back to it, but not the other way round."""),
    ex("""
    class Money:
        def __init__(self, amount, currency):
            self.amount = amount
            self.currency = currency

        def __repr__(self):
            return f"Money({self.amount!r}, {self.currency!r})"

        def __str__(self):
            return f"{self.amount:.2f} {self.currency}"

    m = Money(12.5, "EUR")
    print(m)
    print(repr(m), f"{m} | {m!r}")
    print([m, Money(3, "USD")])           # containers show the repr of their items
    """, "repr_str.py"),
    p("""Use `!r` for the fields inside `__repr__`, so strings show their quotes and `Money('12.5', 'EUR')` (a string amount, probably a
    bug) is distinguishable from `Money(12.5, 'EUR')`. A good repr pays for itself the first time you print a list of objects while
    debugging, and logging libraries and test failure messages rely on it. Keep it free of secrets: an API client's repr should not
    show its key."""),
)

section("eq", "Equality and hashing",
    p("""By default, `==` between two instances of your class compares **identity**: two separate `Money(12.5, "EUR")` objects are not equal
    (2.1). Defining **`__eq__(self, other)`** lets you decide what equality means, usually "all the fields that define the value are
    equal". If `other` is not something you know how to compare, return the special value **`NotImplemented`** (not `False`, and do not
    raise): Python then tries the other operand's `__eq__`, and if that also gives up, falls back to identity. Returning
    `NotImplemented` keeps `m == "text"` working and `False`, instead of crashing with an `AttributeError` (problem 6)."""),
    p("""Equality is tied to **hashing**. Sets and dict keys find objects by their `__hash__` value first and then confirm with `__eq__`, so
    the rule is: **objects that compare equal must have equal hashes**. To protect you, Python sets `__hash__` to `None` as soon as a
    class defines `__eq__` without `__hash__`, which makes instances **unhashable**: putting one in a set raises `TypeError` (problem
    3). If your objects are values that should work in sets and as keys, define `__hash__` from the **same fields** as `__eq__`,
    typically `hash((self.a, self.b))`, and treat those fields as immutable: if a field changes while the object is in a set, the set can
    no longer find it."""),
    ex("""
    class Money:
        def __init__(self, amount, currency):
            self.amount = amount
            self.currency = currency

        def __repr__(self):
            return f"Money({self.amount!r}, {self.currency!r})"

        def __eq__(self, other):
            if not isinstance(other, Money):
                return NotImplemented
            return (self.amount, self.currency) == (other.amount, other.currency)

        def __hash__(self):
            return hash((self.amount, self.currency))

    a, b = Money(5, "EUR"), Money(5, "EUR")
    print(a == b, a is b, a == "5 EUR", a != Money(5, "USD"))
    print(len({a, b, Money(5, "USD")}), {a: "price"}[b])     # 2 distinct values; b finds a's entry

    class NoHash:
        def __eq__(self, other):
            return True
    try:
        {NoHash()}
    except TypeError as e:
        print("TypeError:", e)
    """, "eq_hash.py"),
    p("""`!=` uses `__ne__`, which by default inverts `__eq__`, so you rarely define it. Mutable objects whose equality depends on changing
    state (a conversation, a cache) should usually stay unhashable: equal now does not mean equal later. Dataclasses (11.3) generate
    `__eq__` for you, and `@dataclass(frozen=True)` generates a matching `__hash__` too."""),
)

section("order", "Ordering",
    p("""`sorted`, `min`, `max` and `<` use **`__lt__`** ("less than"), and the other comparisons use `__le__`, `__gt__` and `__ge__`. Without
    them, sorting your objects raises `TypeError: '<' not supported`. The decorator `functools.total_ordering` fills in the other
    three from `__eq__` and `__lt__`. As with equality, return `NotImplemented` for types you cannot compare. For a value type with a
    natural order (versions, money in one currency, dates), define the ordering by comparing **tuples** of fields, which compare element
    by element (4.3)."""),
    ex("""
    import functools

    @functools.total_ordering
    class Version:
        def __init__(self, text):
            self.parts = tuple(int(p) for p in text.split("."))

        def __repr__(self):
            return f"Version({'.'.join(map(str, self.parts))!r})"

        def __eq__(self, other):
            return self.parts == other.parts if isinstance(other, Version) else NotImplemented

        def __lt__(self, other):
            return self.parts < other.parts if isinstance(other, Version) else NotImplemented

        def __hash__(self):
            return hash(self.parts)

    versions = [Version(v) for v in ["1.10.0", "1.9.2", "2.0", "1.9.10"]]
    print(sorted(versions), max(versions))
    print(Version("1.10") > Version("1.9"), "1.10" > "1.9")
    """, "ordering.py"),
    p("""The last line shows why ordering by the right representation matters: as strings, `"1.10"` sorts before `"1.9"`, because strings
    compare character by character (5.1). Comparing tuples of integers gives the order people expect (problem 10). When objects have
    no single natural order (documents by score, by date, by length), do not define `__lt__` at all; pass a `key` function to
    `sorted` instead, which is clearer at the call site."""),
)

section("containers", "Containers and truthiness",
    p("""An object that holds items can implement the **container** methods: `__len__` for `len`, `__getitem__` for `obj[key]` (an
    integer, a slice or a dict-like key: the method receives exactly what is inside the brackets), `__setitem__` and `__delitem__` for
    assignment and `del`, `__contains__` for `in`, and `__iter__` for loops (10.1). Each is optional; implement the ones your object
    should support. When `obj[1:3]` is used, `__getitem__` receives a `slice` object; returning an instance of your own class keeps the
    type, as lists and DataFrames do."""),
    p("""**Truthiness** (`if obj:`, `while obj:`, `bool(obj)`) calls `__bool__`, and if there is no `__bool__`, falls back to `__len__`
    (empty means false). Without either, every instance is truthy. Defining `__len__` on a container therefore makes empty containers
    falsy, exactly like lists, which is usually what you want, but can surprise: `if result:` on an empty result object is false even
    though the object exists. Use `if result is not None:` when you mean existence (1.2)."""),
    ex("""
    class Batch:
        def __init__(self, items):
            self.items = list(items)

        def __repr__(self):
            return f"Batch({self.items!r})"

        def __len__(self):
            return len(self.items)

        def __getitem__(self, key):
            if isinstance(key, slice):
                return Batch(self.items[key])       # slicing keeps the type
            return self.items[key]

        def __contains__(self, item):
            return item in self.items

    b = Batch(["a", "b", "c", "d"])
    print(len(b), b[0], b[1:3], "c" in b, bool(b), bool(Batch([])))
    empty = Batch([])
    print("empty is falsy" if not empty else "truthy", empty is not None)
    """, "containers.py"),
)

section("arith", "Arithmetic, `NotImplemented` and calling",
    p("""Operators map to methods too: `+` to `__add__`, `-` to `__sub__`, `*` to `__mul__`, `@` to `__matmul__` (matrix product), `abs()` to
    `__abs__`, unary `-` to `__neg__`. For `x + y`, Python first calls `x.__add__(y)`; if that returns `NotImplemented` (or does not
    exist), it calls the **reflected** method `y.__radd__(x)`. That second chance is what makes `2 * vector` work when only the vector
    knows how to multiply, and it is why `sum()` needs `__radd__`: `sum` starts from `0`, so its first step is `0 + first_item`, and
    `int` does not know your type (problem 12)."""),
    ex("""
    class Usage:
        def __init__(self, prompt=0, completion=0):
            self.prompt = prompt
            self.completion = completion

        def __repr__(self):
            return f"Usage(prompt={self.prompt}, completion={self.completion})"

        def __add__(self, other):
            if not isinstance(other, Usage):
                return NotImplemented
            return Usage(self.prompt + other.prompt, self.completion + other.completion)

        def __radd__(self, other):
            if other == 0:                      # sum() starts with 0
                return self
            return self.__add__(other)

    calls = [Usage(120, 40), Usage(300, 80), Usage(50, 10)]
    print(calls[0] + calls[1], sum(calls))
    try:
        calls[0] + 5
    except TypeError as e:
        print("TypeError:", e)
    """, "arithmetic.py"),
    p("""Operators should return **new** objects and leave the operands unchanged, as numbers do; in-place versions (`__iadd__` for `+=`, 2.2)
    may modify `self` and return it. Finally, **`__call__`** makes instances callable like functions: `scorer(text)` runs
    `scorer.__call__(text)`. A callable object is a function with state and configuration: a scorer with weights, a decorator class that
    keeps statistics, a PyTorch module (`model(x)` calls `__call__`, which runs hooks and then `forward`)."""),
    ex("""
    class KeywordScorer:
        def __init__(self, weights):
            self.weights = dict(weights)
            self.calls = 0

        def __call__(self, text):
            self.calls += 1
            words = text.lower().split()
            return sum(self.weights.get(w, 0) for w in words)

        def __repr__(self):
            return f"KeywordScorer({len(self.weights)} weights, {self.calls} calls)"

    score = KeywordScorer({"refund": 2, "urgent": 3, "thanks": -1})
    docs = ["Thanks for the help", "URGENT refund needed", "refund status"]
    print(sorted(docs, key=score, reverse=True), score, callable(score))
    """, "callable.py"),
)

section("warmup", "Warm-up",
    predict("How objects print", "easy",
        code="""
        class Tag:
            def __init__(self, name):
                self.name = name
            def __repr__(self):
                return f"Tag({self.name!r})"

        class Label(Tag):
            def __str__(self):
                return f"#{self.name}"

        t, l = Tag("eu"), Label("vip")
        print(t, l)
        print([t, l], f"{l} {l!r}", str(t))
        print("{}".format(l), repr(l))
        """,
        hints=["`print` and `str` use `__str__`, falling back to `__repr__`. Containers and `!r` always use `__repr__`."],
        why="""`Tag` defines only `__repr__`, so `print(t)` and `str(t)` fall back to it. `Label` inherits that `__repr__` and adds a `__str__`, so
        printing it shows `#vip`, while the list display and `!r` use the repr. `format` uses `__str__` as well (through `__format__`'s
        default)."""),
    write("A money value", "easy", tag="Data work",
        prompt="""Write a class `Money(amount, currency)` with `__repr__` returning `Money(12.5, 'EUR')`, `__str__` returning `"12.50 EUR"`,
        `__eq__` comparing amount and currency (and returning `NotImplemented` for other types), and a matching `__hash__`.""",
        code="""
        class Money:
            pass
        """,
        tests="""
        m = Money(12.5, "EUR")
        assert repr(m) == "Money(12.5, 'EUR')" and str(m) == "12.50 EUR" and f"{m}" == "12.50 EUR"
        assert m == Money(12.5, "EUR") and m != Money(12.5, "USD") and m != Money(10, "EUR")
        assert (m == "12.50 EUR") is False
        assert len({m, Money(12.5, "EUR"), Money(3, "EUR")}) == 2
        assert [Money(1, "USD")] == [Money(1, "USD")]
        """,
        hints=["Compare tuples of the fields in `__eq__`, and hash the same tuple in `__hash__`."],
        solution="""
        class Money:
            def __init__(self, amount, currency):
                self.amount = amount
                self.currency = currency

            def __repr__(self):
                return f"Money({self.amount!r}, {self.currency!r})"

            def __str__(self):
                return f"{self.amount:.2f} {self.currency}"

            def __eq__(self, other):
                if not isinstance(other, Money):
                    return NotImplemented
                return (self.amount, self.currency) == (other.amount, other.currency)

            def __hash__(self):
                return hash((self.amount, self.currency))
        """,
        why="""The repr uses `!r` so the currency appears with quotes and the output looks like the call that builds it. Equality and hashing use
        the same tuple of fields, which satisfies the rule "equal objects have equal hashes", so the set keeps one of the two equal values.
        Comparing with a string returns `NotImplemented`, Python tries the string's comparison, which also declines, and the result falls
        back to `False`, with no error. List equality compares items with `==`, so it works through your `__eq__`. Real money code would
        use `decimal.Decimal` for amounts (1.1)."""),
    fix("Equal objects that cannot go in a set", "easy", tag="RAG",
        prompt="""`Chunk` defines equality by document id and position so duplicate chunks can be removed with a set, but building the set
        raises `TypeError: unhashable type`. Fix the class.""",
        code="""
        class Chunk:
            def __init__(self, doc_id, position, text):
                self.doc_id = doc_id
                self.position = position
                self.text = text

            def __eq__(self, other):
                if not isinstance(other, Chunk):
                    return NotImplemented
                return (self.doc_id, self.position) == (other.doc_id, other.position)
        """,
        tests="""
        chunks = [Chunk("faq", 0, "Refunds take 5 days."), Chunk("faq", 1, "Contact us."), Chunk("faq", 0, "Refunds take 5 days.")]
        unique = set(chunks)
        assert len(unique) == 2
        assert Chunk("faq", 0, "edited text") in unique
        assert {Chunk("a", 1, "x"): "seen"}[Chunk("a", 1, "y")] == "seen"
        """,
        hints=["Defining `__eq__` sets `__hash__` to `None`. Add a `__hash__` built from the same fields that `__eq__` compares."],
        solution="""
        class Chunk:
            def __init__(self, doc_id, position, text):
                self.doc_id = doc_id
                self.position = position
                self.text = text

            def __eq__(self, other):
                if not isinstance(other, Chunk):
                    return NotImplemented
                return (self.doc_id, self.position) == (other.doc_id, other.position)

            def __hash__(self):
                return hash((self.doc_id, self.position))
        """,
        why="""When a class defines `__eq__`, Python removes the inherited identity-based hash, because it would violate "equal objects must hash
        equally": two equal chunks would land in different places in a set. Hashing exactly the fields that `__eq__` compares restores the
        guarantee. The text is deliberately left out of both, so an edited chunk at the same position counts as the same chunk, which is
        the identity a vector store uses for upserts. Those identity fields should not be changed while the object is in a set or used as a
        key."""),
    predict("Length, truth and existence", "easy",
        code="""
        class Results:
            def __init__(self, hits):
                self.hits = list(hits)
            def __len__(self):
                return len(self.hits)

        class Flag:
            def __init__(self, on):
                self.on = on
            def __bool__(self):
                return self.on

        r_empty, r_full = Results([]), Results(["a"])
        print(bool(r_empty), bool(r_full), len(r_full))
        print("found" if r_empty else "nothing", r_empty is not None)
        print(bool(Flag(False)), bool(Flag(True)), bool(object()))
        x = Results([]) or "fallback"
        print(x)
        """,
        hints=["Without `__bool__`, truthiness falls back to `__len__`; without either, objects are truthy."],
        why="""`Results` has no `__bool__`, so `bool` uses `__len__`: empty results are falsy, like an empty list, even though the object exists,
        which `is not None` confirms. `Flag` decides truthiness explicitly. A plain `object()` is truthy. `or` returns its first truthy
        operand (1.2), so an empty `Results` is skipped in favour of the fallback, a subtle effect of defining `__len__`."""),
)

section("medium", "Medium",
    write("Token usage that adds up", "medium", tag="GenAI",
        prompt="""Write a class `Usage(prompt=0, completion=0, cost=0.0)` with `__repr__` (`Usage(prompt=120, completion=40, cost=0.002)`),
        `__add__` returning a new `Usage` with summed fields (and `NotImplemented` for other types), `__radd__` so `sum(usages)` works,
        `__eq__`, a method `total()` returning prompt + completion tokens, and `__bool__` that is false only when all fields are zero.""",
        code="""
        class Usage:
            pass
        """,
        tests="""
        a = Usage(120, 40, 0.002)
        b = Usage(300, 80, 0.005)
        assert repr(a) == "Usage(prompt=120, completion=40, cost=0.002)"
        s = a + b
        assert (s.prompt, s.completion, round(s.cost, 6)) == (420, 120, 0.007) and a.prompt == 120
        total = sum([a, b, Usage(5, 5)])
        assert total == Usage(425, 125, 0.007) and total.total() == 550
        assert not Usage() and bool(Usage(cost=0.1))
        try:
            a + 1
            assert False
        except TypeError:
            pass
        assert sum([]) == 0 and sum([], Usage()) == Usage()
        """,
        hints=["`sum` starts with `0`, so `__radd__` must accept `0` and return `self`.", "Compare costs with `round` in `__eq__` to avoid float noise: `round(self.cost - other.cost, 9) == 0`."],
        solution="""
        class Usage:
            def __init__(self, prompt=0, completion=0, cost=0.0):
                self.prompt = prompt
                self.completion = completion
                self.cost = cost

            def __repr__(self):
                return f"Usage(prompt={self.prompt}, completion={self.completion}, cost={self.cost})"

            def __add__(self, other):
                if not isinstance(other, Usage):
                    return NotImplemented
                return Usage(self.prompt + other.prompt, self.completion + other.completion, self.cost + other.cost)

            def __radd__(self, other):
                if other == 0:
                    return self
                return self.__add__(other)

            def __eq__(self, other):
                if not isinstance(other, Usage):
                    return NotImplemented
                return (self.prompt, self.completion) == (other.prompt, other.completion) and round(self.cost - other.cost, 9) == 0

            def total(self):
                return self.prompt + self.completion

            def __bool__(self):
                return bool(self.prompt or self.completion or self.cost)
        """,
        why="""`sum([a, b, c])` computes `((0 + a) + b) + c`. The first step calls `int.__add__(0, a)`, which returns `NotImplemented`, so Python
        tries `a.__radd__(0)`; returning `self` for 0 lets the rest use `__add__`. Every addition builds a new `Usage`, leaving `a` and `b`
        unchanged, as numbers behave. Floats such as `0.002 + 0.005` are not exactly `0.007` (1.1), so the cost comparison tolerates tiny
        differences. With `__bool__`, an empty usage is falsy, convenient for "skip if nothing was spent". This is the kind of object SDKs
        return as `response.usage`, and summing it over a run gives the total bill."""),
    fix("Equality that crashes on other types", "medium", tag="Data work",
        prompt="""`Version.__eq__` raises `AttributeError` when a version is compared with anything that is not a `Version`, which breaks
        `in` checks on mixed lists and comparisons with `None`. Fix `__eq__` (and `__lt__`) to cooperate with other types.""",
        code="""
        class Version:
            def __init__(self, text):
                self.parts = tuple(int(p) for p in text.split("."))

            def __eq__(self, other):
                return self.parts == other.parts

            def __lt__(self, other):
                return self.parts < other.parts

            def __hash__(self):
                return hash(self.parts)
        """,
        tests="""
        v = Version("1.2.0")
        assert v == Version("1.2.0") and v < Version("1.10")
        assert (v == "1.2.0") is False and (v == None) is False and v != 3
        assert v in [None, "1.2.0", Version("1.2.0")]
        try:
            v < "2.0"
            assert False
        except TypeError:
            pass
        """,
        hints=["Return `NotImplemented` when `other` is not a `Version`. Python then handles the fallback."],
        solution="""
        class Version:
            def __init__(self, text):
                self.parts = tuple(int(p) for p in text.split("."))

            def __eq__(self, other):
                if not isinstance(other, Version):
                    return NotImplemented
                return self.parts == other.parts

            def __lt__(self, other):
                if not isinstance(other, Version):
                    return NotImplemented
                return self.parts < other.parts

            def __hash__(self):
                return hash(self.parts)
        """,
        why="""Python calls `__eq__` in many places you do not see: `in` on a list compares the item with every element, dict lookups compare
        keys, `x == None` happens in old code. Assuming `other` has `.parts` turned those into `AttributeError`s. Returning `NotImplemented`
        lets Python try the other operand and then fall back: for `==` the fallback is identity (so `False`), and for `<` there is no
        fallback, so Python raises the proper `TypeError: '<' not supported between instances`. Returning `False` from `__lt__` instead
        would make sorting mixed lists silently wrong rather than failing."""),
    write("A batch container", "medium", tag="ML",
        prompt="""Write a class `Batch(items)` for training data: `__len__`; `__getitem__` that returns one item for an integer index and
        a new `Batch` for a slice; `__iter__` (yield the items); `__contains__`; `__repr__` showing the count, `Batch(3 items)`; and a
        method `split(n)` returning a list of batches of at most `n` items. A batch must not be affected by later changes to the list it
        was created from.""",
        code="""
        class Batch:
            pass
        """,
        tests="""
        data = [{"x": i} for i in range(5)]
        b = Batch(data)
        data.append({"x": 99})
        assert len(b) == 5 and b[0] == {"x": 0} and b[-1] == {"x": 4}
        s = b[1:3]
        assert isinstance(s, Batch) and len(s) == 2 and s[0] == {"x": 1}
        assert [row["x"] for row in b] == [0, 1, 2, 3, 4] and {"x": 2} in b and {"x": 99} not in b
        assert repr(b) == "Batch(5 items)" and [len(p) for p in b.split(2)] == [2, 2, 1]
        assert not Batch([]) and bool(b)
        """,
        hints=["Copy the input with `list(items)` in `__init__`. `__getitem__` receives a `slice` object for `b[1:3]`.",
               "`__iter__` can simply `yield from self._items`."],
        solution="""
        class Batch:
            def __init__(self, items):
                self._items = list(items)

            def __len__(self):
                return len(self._items)

            def __getitem__(self, key):
                if isinstance(key, slice):
                    return Batch(self._items[key])
                return self._items[key]

            def __iter__(self):
                yield from self._items

            def __contains__(self, item):
                return item in self._items

            def __repr__(self):
                return f"Batch({len(self)} items)"

            def split(self, n):
                return [self[i:i + n] for i in range(0, len(self), n)]
        """,
        why="""Each dunder connects one piece of syntax to the internal list: `len`, indexing, slicing, `for` and `in` all work as they would on a
        list, and slicing returns a `Batch` so the type survives, like slicing a DataFrame returns a DataFrame. `split` is written with the
        class's own slicing, a small sign that the protocol is complete. Copying the input list protects the batch from later appends,
        though the dicts inside are still shared (2.3). `__len__` also makes an empty batch falsy. PyTorch's `Dataset` is this same idea:
        `__len__` plus `__getitem__`, which is all a `DataLoader` needs."""),
    choose("Membership: scan or set", "medium", tag="RAG",
        prompt="Both classes hold 20,000 document ids; the code checks 2,000 ids with `in`. Which is faster?",
        setup="""class ScanIds:
    def __init__(self, ids):
        self._ids = list(ids)
    def __getitem__(self, i):
        return self._ids[i]

class SetIds:
    def __init__(self, ids):
        self._ids = list(ids)
        self._lookup = set(ids)
    def __getitem__(self, i):
        return self._ids[i]
    def __contains__(self, x):
        return x in self._lookup

ids = [f"doc{i}" for i in range(20_000)]
a, b = ScanIds(ids), SetIds(ids)
queries = [f"doc{i * 7}" for i in range(2_000)]""",
        options={
            "a": "found = sum(q in a for q in queries)",
            "b": "found = sum(q in b for q in queries)",
        },
        answer="b",
        hints=["Without `__contains__`, how does `in` decide?"],
        why="""`ScanIds` has no `__contains__`, so `in` falls back to iterating: it calls `__getitem__(0)`, `__getitem__(1)`, ... in Python, comparing
        each id until it finds a match, thousands of Python-level calls per query. `SetIds` answers with one hash lookup (4.4). Defining
        `__contains__` lets a container choose the right data structure for membership while keeping its order for iteration and indexing.
        Python's fallbacks make protocols easy to start with, but they are correct rather than fast."""),
    trace("Sorting with total_ordering", "medium",
        prompt="Fill in `r` after each marked line.",
        code="""
        import functools

        @functools.total_ordering
        class Priority:
            ORDER = {"low": 0, "normal": 1, "high": 2}
            def __init__(self, level):
                self.level = level
            def __repr__(self):
                return self.level
            def __eq__(self, other):
                return self.ORDER[self.level] == self.ORDER[other.level]
            def __lt__(self, other):
                return self.ORDER[self.level] < self.ORDER[other.level]

        items = [Priority(x) for x in ["normal", "high", "low", "high"]]
        r = sorted(items)  # row: "sorted"
        r = max(items)  # row: "max"
        r = Priority("low") >= Priority("normal")  # row: "derived >="
        r = sorted(items, reverse=True)[0] == Priority("high")  # row: "first of reverse"
        """,
        trace_vars=["r"],
        hints=["`total_ordering` derives `>=` from `__lt__` and `__eq__`. `sorted` is stable."],
        why="""Sorting uses `__lt__`, which compares the mapped numbers, and the repr shows the level names. `max` returns the first of the equal
        maximum elements it meets (the first `high`). `>=` was not defined, so `total_ordering` built it from `__lt__`: low is not greater
        than or equal to normal. The reversed sort starts with a `high`, which equals a new `Priority("high")` through `__eq__`."""),
    fix("Versions that sort as text", "medium", tag="ML",
        prompt="""Model checkpoints are compared by version to find the newest, but `max` picks `v1.9` over `v1.10`. Fix the comparison so
        versions compare numerically, part by part.""",
        code="""
        import functools

        @functools.total_ordering
        class Checkpoint:
            def __init__(self, name):
                self.name = name
                self.version = name.split("-v")[1]

            def __repr__(self):
                return f"Checkpoint({self.name!r})"

            def __eq__(self, other):
                if not isinstance(other, Checkpoint):
                    return NotImplemented
                return self.version == other.version

            def __lt__(self, other):
                if not isinstance(other, Checkpoint):
                    return NotImplemented
                return self.version < other.version

            def __hash__(self):
                return hash(self.version)
        """,
        tests="""
        cps = [Checkpoint(n) for n in ["ranker-v1.9", "ranker-v1.10", "ranker-v1.2.3", "ranker-v2.0"]]
        assert max(cps).name == "ranker-v2.0"
        assert [c.name for c in sorted(cps)] == ["ranker-v1.2.3", "ranker-v1.9", "ranker-v1.10", "ranker-v2.0"]
        assert Checkpoint("a-v1.10") > Checkpoint("a-v1.9") and Checkpoint("a-v1.0") == Checkpoint("b-v1.0")
        """,
        hints=["Store the version as a tuple of integers: `tuple(int(p) for p in ...split(\".\"))`."],
        solution="""
        import functools

        @functools.total_ordering
        class Checkpoint:
            def __init__(self, name):
                self.name = name
                self.version = tuple(int(p) for p in name.split("-v")[1].split("."))

            def __repr__(self):
                return f"Checkpoint({self.name!r})"

            def __eq__(self, other):
                if not isinstance(other, Checkpoint):
                    return NotImplemented
                return self.version == other.version

            def __lt__(self, other):
                if not isinstance(other, Checkpoint):
                    return NotImplemented
                return self.version < other.version

            def __hash__(self):
                return hash(self.version)
        """,
        why="""Strings compare character by character, so `"1.10" < "1.9"` because `"1"` is less than `"9"` at the third character (5.1). Tuples of
        integers compare part by part numerically: `(1, 10) > (1, 9)`, and `(1, 2, 3) < (1, 9)`. Parsing once in `__init__` keeps every
        comparison cheap and makes the representation explicit. Note that `(1, 0)` and `(1, 0, 0)` are different tuples; real version
        libraries (`packaging.version`) normalise trailing zeros and handle pre-releases like `2.0rc1`."""),
    write("A callable scorer", "medium", tag="RAG",
        prompt="""Write a class `BoostScorer(base_scores, boosts)` where `base_scores` maps doc id to a retrieval score and `boosts` maps a
        source name to a multiplier. Calling an instance with a result dict `{"id": ..., "source": ...}` returns the base score times the
        source's boost (default 1.0), rounded to 4 decimals, and counts the calls in `self.calls`. Give it a `__repr__` like
        `BoostScorer(2 boosts)`. It must work as a `key` for `sorted`.""",
        code="""
        class BoostScorer:
            pass
        """,
        tests="""
        results = [{"id": "d1", "source": "forum"}, {"id": "d2", "source": "docs"}, {"id": "d3", "source": "blog"}]
        score = BoostScorer({"d1": 0.9, "d2": 0.7, "d3": 0.8}, {"docs": 1.5, "forum": 0.8})
        ranked = sorted(results, key=score, reverse=True)
        assert [r["id"] for r in ranked] == ["d2", "d3", "d1"]
        assert score({"id": "d2", "source": "docs"}) == 1.05 and score.calls == 4
        assert repr(score) == "BoostScorer(2 boosts)" and callable(score)
        """,
        hints=["Store copies of both dicts in `__init__`; the scoring goes in `__call__(self, result)`."],
        solution="""
        class BoostScorer:
            def __init__(self, base_scores, boosts):
                self.base_scores = dict(base_scores)
                self.boosts = dict(boosts)
                self.calls = 0

            def __call__(self, result):
                self.calls += 1
                base = self.base_scores[result["id"]]
                return round(base * self.boosts.get(result["source"], 1.0), 4)

            def __repr__(self):
                return f"BoostScorer({len(self.boosts)} boosts)"
        """,
        why="""`sorted` only needs something callable as its `key`, so an object with `__call__` fits anywhere a function does, while carrying
        configuration (the scores and boosts) and state (the call count) that a plain function would need globals or a closure for. Boosting
        scores by source is a common re-ranking step: official docs above forum posts. The `sorted` call scored each result once (three
        calls) and the direct call made the fourth. PyTorch modules, scikit-learn transformers used in pipelines and many retriever classes
        are callable objects in exactly this sense."""),
    predict("Reflected operators and sum", "medium",
        code="""
        class Tokens:
            def __init__(self, n):
                self.n = n
            def __repr__(self):
                return f"Tokens({self.n})"
            def __add__(self, other):
                if isinstance(other, Tokens):
                    return Tokens(self.n + other.n)
                if isinstance(other, int):
                    return Tokens(self.n + other)
                return NotImplemented
            def __radd__(self, other):
                print("  radd with", other)
                return self.__add__(other)

        print(Tokens(2) + Tokens(3), Tokens(2) + 1)
        print(10 + Tokens(5))
        print(sum([Tokens(1), Tokens(2)]))
        try:
            Tokens(1) + "x"
        except TypeError as e:
            print("TypeError")
        """,
        hints=["`10 + t` first tries `int.__add__`, which returns `NotImplemented` for a `Tokens`, then `t.__radd__(10)`."],
        why="""The first two additions are handled by `Tokens.__add__`. `10 + Tokens(5)` cannot be handled by `int`, so Python calls the reflected
        `__radd__` with 10. `sum` starts from 0: `0 + Tokens(1)` goes through `__radd__` with 0 (which this `__add__` accepts as an int), and
        the next step is `Tokens + Tokens`. Adding a string: `__add__` returns `NotImplemented`, `str` has no way to add a `Tokens`, so
        Python raises `TypeError`."""),
)

section("hard", "Hard",
    write("A small vector type", "hard", tag="ML",
        prompt="""Write a class `Vector(*components)` (floats) with: `__repr__` (`Vector(1.0, 2.0)`), `__len__`, `__iter__`, `__getitem__`,
        `__eq__`, `__add__` and `__sub__` (same length, else `ValueError`), `__mul__` and `__rmul__` for multiplying by a number,
        `__matmul__` for the dot product, `__abs__` for the Euclidean norm, and a method `cosine(other)` (raise `ValueError` for a zero
        vector). Return `NotImplemented` for unsupported operand types.""",
        code="""
        import math

        class Vector:
            pass
        """,
        tests="""
        a, b = Vector(1, 2, 2), Vector(2, 0, 1)
        assert repr(a) == "Vector(1.0, 2.0, 2.0)" and len(a) == 3 and list(a) == [1.0, 2.0, 2.0] and a[1] == 2.0
        assert a + b == Vector(3, 2, 3) and a - b == Vector(-1, 2, 1) and 2 * a == a * 2 == Vector(2, 4, 4)
        assert a @ b == 4.0 and abs(a) == 3.0 and round(a.cosine(b), 4) == 0.5963
        try:
            a + Vector(1, 2)
            assert False
        except ValueError:
            pass
        try:
            Vector(0, 0).cosine(a)
            assert False
        except ValueError:
            pass
        try:
            a * "x"
            assert False
        except TypeError:
            pass
        assert (a == [1, 2, 2]) is False
        """,
        hints=["Store `self._c = tuple(float(x) for x in components)`. A private helper can check lengths for `+`, `-` and `@`.",
               "In `__mul__`, accept `int` and `float` (but not `bool` is fine either way here); otherwise return `NotImplemented`."],
        solution="""
        import math

        class Vector:
            def __init__(self, *components):
                self._c = tuple(float(x) for x in components)

            def __repr__(self):
                return f"Vector({', '.join(map(str, self._c))})"

            def __len__(self):
                return len(self._c)

            def __iter__(self):
                return iter(self._c)

            def __getitem__(self, i):
                return self._c[i]

            def __eq__(self, other):
                if not isinstance(other, Vector):
                    return NotImplemented
                return self._c == other._c

            def __hash__(self):
                return hash(self._c)

            def _check(self, other):
                if len(self) != len(other):
                    raise ValueError(f"length mismatch: {len(self)} vs {len(other)}")

            def __add__(self, other):
                if not isinstance(other, Vector):
                    return NotImplemented
                self._check(other)
                return Vector(*(x + y for x, y in zip(self, other)))

            def __sub__(self, other):
                if not isinstance(other, Vector):
                    return NotImplemented
                self._check(other)
                return Vector(*(x - y for x, y in zip(self, other)))

            def __mul__(self, k):
                if not isinstance(k, (int, float)):
                    return NotImplemented
                return Vector(*(x * k for x in self))

            __rmul__ = __mul__

            def __matmul__(self, other):
                if not isinstance(other, Vector):
                    return NotImplemented
                self._check(other)
                return sum(x * y for x, y in zip(self, other))

            def __abs__(self):
                return math.sqrt(self @ self)

            def cosine(self, other):
                denom = abs(self) * abs(other)
                if denom == 0:
                    raise ValueError("cosine is undefined for a zero vector")
                return (self @ other) / denom
        """,
        why="""Each operator is one dunder, and together they make the class read like the mathematics: `a @ b / (abs(a) * abs(b))` is the
        cosine similarity used everywhere in retrieval. `__rmul__ = __mul__` reuses the same function for `2 * a`, valid because scalar
        multiplication is commutative. Storing components in a tuple makes the vector immutable, so a `__hash__` is safe and every
        operator returns a new vector. Returning `NotImplemented` for strings lets Python raise the standard `TypeError`, while a length
        mismatch is a value problem and raises `ValueError`. `__iter__` makes `zip(self, other)` work on vectors directly. NumPy does all
        of this in C on arrays of any shape, which is why real code uses it; implementing it once shows what `a @ b` means."""),
    fix("Read the code: span objects for highlighting", "hard", tag="RAG",
        prompt="""`Span(start, end, label)` marks a highlighted region in a retrieved document. Duplicate spans should be removed with a set,
        spans should sort by start (then end), and equal spans must be equal on start, end **and** label. Duplicates survive the set,
        `Span(0, 5, "a") == Span(0, 9, "b")` is true, and sorting is backwards. Read it, find the bugs and fix them.""",
        code="""
        class Span:
            def __init__(self, start, end, label):
                if start > end:
                    raise ValueError("start must not exceed end")
                self.start = start
                self.end = end
                self.label = label

            def __repr__(self):
                return f"Span({self.start}, {self.end}, {self.label!r})"

            def __eq__(self, other):
                return self.start == other.start

            __hash__ = object.__hash__

            def __lt__(self, other):
                return (self.start, self.end) > (other.start, other.end)

            def __len__(self):
                return self.end - self.start
        """,
        tests="""
        spans = [Span(10, 15, "refund"), Span(0, 5, "policy"), Span(10, 15, "refund"), Span(0, 9, "policy"), Span(0, 5, "date")]
        unique = set(spans)
        assert len(unique) == 4
        assert Span(0, 5, "a") != Span(0, 9, "a") and Span(0, 5, "a") != Span(0, 5, "b")
        assert sorted(set(spans), key=lambda s: (s.start, s.end, s.label)) == [Span(0, 5, "date"), Span(0, 5, "policy"), Span(0, 9, "policy"), Span(10, 15, "refund")]
        assert sorted([Span(10, 15, "x"), Span(0, 9, "x"), Span(0, 5, "x")]) == [Span(0, 5, "x"), Span(0, 9, "x"), Span(10, 15, "x")]
        assert (Span(0, 1, "x") == "x") is False and len(Span(3, 8, "x")) == 5
        """,
        hints=["`__eq__` must compare all three fields and return `NotImplemented` for other types.",
               "`object.__hash__` hashes by identity, which breaks the equal-means-equal-hash rule. Hash the same fields as `__eq__`.",
               "`__lt__` uses `>`."],
        solution="""
        class Span:
            def __init__(self, start, end, label):
                if start > end:
                    raise ValueError("start must not exceed end")
                self.start = start
                self.end = end
                self.label = label

            def __repr__(self):
                return f"Span({self.start}, {self.end}, {self.label!r})"

            def _key(self):
                return (self.start, self.end, self.label)

            def __eq__(self, other):
                if not isinstance(other, Span):
                    return NotImplemented
                return self._key() == other._key()

            def __hash__(self):
                return hash(self._key())

            def __lt__(self, other):
                if not isinstance(other, Span):
                    return NotImplemented
                return (self.start, self.end) < (other.start, other.end)

            def __len__(self):
                return self.end - self.start
        """,
        why="""Four bugs. `__eq__` compared only `start`, so spans with different ends and labels were "equal". Someone restored hashability with
        `__hash__ = object.__hash__`, which hashes by **identity**: two equal spans then usually land in different buckets, so the set kept
        both duplicates, the exact violation of "equal objects must have equal hashes" that Python tries to prevent by removing the hash.
        Using one `_key()` for both `__eq__` and `__hash__` keeps them consistent by construction. `__lt__` used `>`, sorting backwards, and
        neither comparison handled other types. Note that sorting by `(start, end)` alone leaves the order of equal-position spans to the
        stable sort, which is why the test sorts the set with an explicit key."""),
    write("A dict with a size limit", "hard", tag="Data work",
        prompt="""Write a class `LRUDict(maxsize)` that behaves like a dict with a size limit: `d[key] = value` stores (moving the key to
        "most recent"), `d[key]` returns the value and marks it most recent (`KeyError` if missing), `del d[key]`, `key in d` (which does
        **not** count as a use), `len(d)`, iteration over keys from least to most recent, and `__repr__` like `LRUDict({'a': 1}, maxsize=2)`.
        When a new key would exceed `maxsize`, evict the least recently used one and record it in `self.evicted`.""",
        code="""
        class LRUDict:
            pass
        """,
        tests="""
        d = LRUDict(maxsize=2)
        d["a"] = 1; d["b"] = 2
        assert d["a"] == 1
        d["c"] = 3
        assert list(d) == ["a", "c"] and d.evicted == ["b"] and "b" not in d and len(d) == 2
        d["a"] = 10
        d["d"] = 4
        assert list(d) == ["a", "d"] and d.evicted == ["b", "c"]
        assert "a" in d and list(d) == ["a", "d"]
        del d["a"]
        assert list(d) == ["d"] and repr(d) == "LRUDict({'d': 4}, maxsize=2)"
        try:
            d["zzz"]
            assert False
        except KeyError:
            pass
        """,
        hints=["A normal dict keeps insertion order. To mark a key as most recent, `pop` it and insert it again.",
               "Evict with `next(iter(self._data))`, the oldest key."],
        solution="""
        class LRUDict:
            def __init__(self, maxsize):
                if maxsize < 1:
                    raise ValueError("maxsize must be at least 1")
                self.maxsize = maxsize
                self._data = {}
                self.evicted = []

            def __getitem__(self, key):
                value = self._data.pop(key)
                self._data[key] = value
                return value

            def __setitem__(self, key, value):
                if key in self._data:
                    del self._data[key]
                elif len(self._data) >= self.maxsize:
                    oldest = next(iter(self._data))
                    del self._data[oldest]
                    self.evicted.append(oldest)
                self._data[key] = value

            def __delitem__(self, key):
                del self._data[key]

            def __contains__(self, key):
                return key in self._data

            def __len__(self):
                return len(self._data)

            def __iter__(self):
                return iter(list(self._data))

            def __repr__(self):
                return f"LRUDict({self._data!r}, maxsize={self.maxsize})"
        """,
        why="""Because dicts preserve insertion order, "most recently used" can be represented as "inserted last": a read pops the key and reinserts
        it, and the first key in iteration order is always the least recently used one, which is what gets evicted. `pop` raises `KeyError`
        for a missing key, so `d["zzz"]` behaves exactly like a dict. Updating an existing key removes it first so it moves to the end without
        triggering an eviction. `__contains__` deliberately does not reorder, so checking membership does not change what gets evicted.
        `__iter__` iterates a snapshot list, so a loop that reads values (and therefore reorders keys) does not break iteration. The standard
        library offers `collections.OrderedDict.move_to_end` for the same job, and `functools.lru_cache` (8.3) uses a linked list internally."""),
    predict("Dunders are looked up on the class", "hard",
        code="""
        class Box:
            def __init__(self, items):
                self.items = items
            def __len__(self):
                return len(self.items)

        b = Box([1, 2, 3])
        b.__len__ = lambda: 99
        print(len(b), b.__len__())

        Box.__len__ = lambda self: 42
        print(len(b), len(Box([])))

        class A:
            def __eq__(self, other):
                print("  A.__eq__")
                return NotImplemented
        class B:
            def __eq__(self, other):
                print("  B.__eq__")
                return NotImplemented
        a, b2 = A(), B()
        print(a == b2, a == a)
        """,
        hints=["`len(x)` calls `type(x).__len__(x)`, ignoring instance attributes.", "When both sides return `NotImplemented`, `==` falls back to identity."],
        why="""Implicit dunder calls (`len(b)`) look up the method on the **type**, not the instance, so the instance attribute `__len__` is used only
        by the explicit call `b.__len__()`. Changing the class's method changes `len` for every instance. For `a == b2`, Python asks `A`'s
        `__eq__`, then the reflected `B.__eq__`; both decline, so the comparison falls back to identity: `False`. For `a == a`, both attempts
        are again `A.__eq__` (first normal, then reflected), and the identity fallback gives `True`."""),
)

section("interview", "Interview questions",
    explain("What is the difference between `__repr__` and `__str__`?", "medium", tag="Interview",
        why="""`__repr__` gives the developer-facing representation: unambiguous, ideally valid Python that recreates the object (`Money(12.5,
        'EUR')`), used by the REPL, debuggers, `repr()`, `!r` in f-strings, logging of objects and the display of items inside containers.
        `__str__` gives the user-facing text (`12.50 EUR`), used by `print`, `str()` and plain f-string interpolation. If only `__repr__` is
        defined, `str()` falls back to it; the reverse is not true, so always define `__repr__` first. A good repr makes debugging and test
        failure messages useful; it should never include secrets such as API keys."""),
    explain("Why does defining `__eq__` make a class unhashable, and how should you define `__hash__`?", "medium", tag="Interview",
        why="""Sets and dicts locate objects by hash and then confirm with `==`, which only works if equal objects have equal hashes. The default
        `__hash__` is based on identity, which is consistent with the default identity-based `__eq__`. Once you define value-based equality,
        the identity hash would violate the rule (two equal objects in different buckets), so Python sets `__hash__ = None`, making instances
        unhashable, rather than letting sets silently misbehave. If the objects are values that belong in sets or as keys, define
        `__hash__` from exactly the fields used in `__eq__`, usually `hash((self.a, self.b))`, and treat those fields as immutable, since
        changing them while the object is stored corrupts the container. Mutable objects whose equality changes over time should stay
        unhashable. `@dataclass(frozen=True)` generates consistent `__eq__` and `__hash__`."""),
    explain("Explain Python's data model and why it matters for libraries like NumPy, pandas and PyTorch.", "hard", tag="Interview",
        why="""The data model is the set of special methods through which syntax and built-ins operate on objects: `len()` calls `__len__`, `x[k]`
        calls `__getitem__`, `for` uses `__iter__`, `in` uses `__contains__`, operators call `__add__`, `__mul__`, `__matmul__` and their
        reflected and in-place versions, comparisons call `__eq__` and `__lt__`, truthiness calls `__bool__` or `__len__`, `with` uses
        `__enter__` and `__exit__`, and calling uses `__call__`. Operator methods return `NotImplemented` to let the other operand try, which
        is how mixed-type arithmetic works. Because these protocols are duck-typed, any object implementing them works with all the code
        written against them. That is how NumPy arrays support `a + b`, slicing and broadcasting with plain syntax, how pandas offers
        `df["col"]`, `len(df)` and boolean masks, and how PyTorch tensors overload arithmetic and modules are called as `model(x)`. It also
        explains some surprises: `if df:` raises an error because pandas makes `__bool__` ambiguous on purpose, and `a == b` on arrays
        returns an array rather than a boolean."""),
)

recap(
    "Dunder methods connect syntax and built-ins to your objects: `len` to `__len__`, `[]` to `__getitem__`, `+` to `__add__`, `==` to `__eq__`, calling to `__call__`.",
    "Always define `__repr__` (developers, containers, `!r`); add `__str__` for user-facing text.",
    "`__eq__` and `__hash__` go together: hash the same fields you compare, keep them immutable, and return `NotImplemented` for other types.",
    "Order with `__lt__` (plus `functools.total_ordering`) on the right representation, such as tuples of ints; otherwise sort with a `key`.",
    "Containers: `__len__`, `__getitem__` (slices included), `__contains__`, `__iter__`; truthiness falls back to `__len__`. `__radd__` makes `sum` work.",
)
