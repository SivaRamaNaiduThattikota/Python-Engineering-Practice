from lesson import *

lesson(
    id="m9-3", num="9.3", title="Properties and encapsulation",
    intro="How Python protects an object's rules without private fields: naming conventions, `@property` for computed "
          "and validated attributes, setters that keep invariants, `functools.cached_property`, name mangling, and "
          "`__slots__`. How properties work underneath (descriptors), and the bugs they prevent. Applied to model "
          "configs, conversations, datasets and API keys.",
    desc="Validation with `property`, computed attributes, `cached_property`, `__slots__`.",
    keys="encapsulation property getter setter deleter computed attribute validation invariant cached_property private underscore name mangling __slots__ descriptor read only immutable value object",
)

term("Property", "A method that is accessed like an attribute (`obj.total`, no parentheses). It can compute a value, validate assignments, or be read-only.")
term("Invariant", "A rule about an object's state that must always hold, such as \"temperature is between 0 and 2\". Methods and setters protect it.")
term("Name mangling", "Python renames attributes written `__name` inside a class to `_ClassName__name`, to avoid clashes with subclasses.")
term("__slots__", "A class attribute listing the only allowed instance attributes. It removes the per-instance `__dict__`, saving memory and rejecting typos.")

section("conventions", "Encapsulation by convention",
    p("""Many languages enforce privacy: a `private` field cannot be touched from outside. Python does not. Every attribute can be read and
    changed from anywhere, and the community relies on **conventions** instead, summarised as "we are all consenting adults". A name
    with **one leading underscore**, `self._tokens`, means "internal: not part of the public interface, may change without notice, do
    not touch from outside". Tools respect it: `from module import *` skips such names, and linters and IDEs warn when you access them
    on another object. A name without an underscore is public and is a promise to callers."""),
    p("""Encapsulation is still possible, and it is about **invariants**, not secrecy: rules about the state that must always hold. A token
    budget's spent amount must never exceed its limit; a config's temperature must stay between 0 and 2; an index's two dicts must
    agree (9.1). The tools for protecting them are: keep the raw state in underscore attributes, change it only through methods, expose
    read access through **properties**, validate in setters and in `__init__`, and never hand out internal mutable objects (return
    copies or read-only views, 2.2)."""),
    callout("sql", "SQL / Power BI", """This is the role of a view and of constraints in a database: users query a view (the public
    interface) instead of the raw tables, and `CHECK` constraints reject invalid rows at write time. In Power BI, measures are the
    public interface over hidden columns. Properties and setters play the same parts for an object."""),
)

section("property", "`@property`: methods that look like attributes",
    p("""Decorating a method with `@property` turns it into an attribute that is **computed when read**: `conv.token_count` calls the method,
    with no parentheses. This is ideal for values derived from other state, because they can never be out of date: there is nothing
    to keep in sync. A property with only a getter is **read-only**: assigning to it raises `AttributeError`."""),
    ex("""
    class Order:
        def __init__(self, items):
            self._items = list(items)            # list of (name, price, qty)

        @property
        def total(self):
            return round(sum(price * qty for _, price, qty in self._items), 2)

        @property
        def items(self):
            return tuple(self._items)             # a read-only view, not the internal list

        def add(self, name, price, qty=1):
            self._items.append((name, price, qty))

    o = Order([("pen", 1.5, 4)])
    print(o.total)
    o.add("book", 12.0)
    print(o.total, o.items)
    try:
        o.total = 100
    except AttributeError as e:
        print("AttributeError:", e)
    """, "property_basics.py"),
    p("""Properties also solve an evolution problem. In Java-style code, every field gets `get_x()` and `set_x()` methods "just in case"
    validation is needed later. In Python, start with a plain public attribute, `self.temperature = t`. If you later need validation or
    computation, replace it with a property of the **same name**, and every caller that wrote `config.temperature` keeps working
    unchanged. That is why Python code rarely has getter and setter methods: the attribute syntax is the interface, and a property can
    take over behind it at any time (problem 17)."""),
)

section("setter", "Setters that keep invariants",
    p("""A property can also control **assignment**. After defining the getter, decorate a second method with `@name.setter`; it receives the
    new value and decides what to store, usually after validating it. The value itself lives in an underscore attribute, `self._name`,
    because the property has taken over the public name: if the setter assigned `self.name = value`, it would call itself forever
    (problem 3)."""),
    ex("""
    class GenerationConfig:
        def __init__(self, temperature=0.7, max_tokens=256):
            self.temperature = temperature          # goes through the setter: validated from the start
            self.max_tokens = max_tokens

        @property
        def temperature(self):
            return self._temperature

        @temperature.setter
        def temperature(self, value):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"temperature must be a number, got {value!r}")
            if not 0 <= value <= 2:
                raise ValueError(f"temperature must be in [0, 2], got {value}")
            self._temperature = float(value)

        @property
        def max_tokens(self):
            return self._max_tokens

        @max_tokens.setter
        def max_tokens(self, value):
            if not isinstance(value, int) or value < 1:
                raise ValueError(f"max_tokens must be a positive int, got {value!r}")
            self._max_tokens = value

    cfg = GenerationConfig()
    cfg.temperature = 1
    print(cfg.temperature, type(cfg.temperature).__name__, vars(cfg))
    for bad in [3, "hot"]:
        try:
            cfg.temperature = bad
        except (ValueError, TypeError) as e:
            print(type(e).__name__, "-", e, "| still", cfg.temperature)
    try:
        GenerationConfig(max_tokens=0)
    except ValueError as e:
        print("at creation:", e)
    """, "setters.py"),
    p("""Three details make this robust. `__init__` assigns through the **public** name, so the same validation runs at construction;
    assigning `self._temperature` directly in `__init__` would let an invalid object be created (problem 14). A failed assignment raises
    **before** storing, so the object keeps its previous valid value. And the setter can **normalise** (here, storing a float), so the
    rest of the code can rely on one type. `vars(cfg)` shows that the instance stores only the underscore attributes: the properties
    live on the class."""),
)

section("cached", "Computing once: `functools.cached_property`",
    p("""A property runs its method on **every** access. That is right when the value is cheap or the underlying state changes, and wasteful
    when the computation is expensive and the inputs never change after creation: building a vocabulary from a corpus, loading a
    tokenizer, computing statistics of a fixed dataset. `functools.cached_property` runs the method on the **first** access and stores
    the result in the instance's `__dict__` under the same name; later accesses find it there and never call the method again."""),
    ex("""
    import functools

    class Corpus:
        def __init__(self, texts):
            self._texts = list(texts)
            self.builds = 0

        @functools.cached_property
        def vocab(self):
            self.builds += 1
            return sorted({w for t in self._texts for w in t.lower().split()})

        def add(self, text):
            self._texts.append(text)
            self.__dict__.pop("vocab", None)          # invalidate the cached value

    c = Corpus(["Refund policy", "refund window"])
    print(c.vocab, c.vocab is c.vocab, c.builds)
    print("vocab" in vars(c))
    c.add("Shipping policy")
    print(c.vocab, c.builds)
    """, "cached_property.py"),
    p("""The cost of caching is **staleness**: if the inputs change, the cached value is now wrong, and nothing recomputes it automatically.
    Whoever changes the inputs must invalidate the cache, here by removing the stored value from `__dict__` (`del c.vocab` also works when
    it is present). Use `cached_property` for values derived from state that is fixed after construction, or pair it with a clear
    invalidation rule in every method that changes that state (problem 7). Unlike `lru_cache` on a method (8.3), it stores the value
    on the instance itself, so it disappears with the object and does not keep instances alive."""),
)

section("mangling", "Name mangling: `__name`",
    p("""A name with **two** leading underscores (and at most one trailing), such as `self.__secret`, is **mangled** inside a class body:
    Python rewrites it to `self._ClassName__secret`. The purpose is to avoid **accidental clashes in subclasses**: if both a base class and
    a subclass use `self.__cache`, each gets its own attribute (`_Base__cache` and `_Sub__cache`) instead of overwriting the other's.
    It is not a security feature: the mangled name is easy to reach from outside, and it makes debugging and testing more awkward."""),
    ex("""
    class Client:
        def __init__(self, key):
            self.__key = key                    # stored as _Client__key
            self._session = "s-1"               # one underscore: internal by convention

        def masked(self):
            return self.__key[:3] + "..."

    c = Client("sk-12345")
    print(sorted(vars(c)), c.masked(), c._session)
    try:
        c.__key
    except AttributeError as e:
        print("AttributeError:", e)
    print(c._Client__key)                       # still reachable: mangling is not protection
    """, "mangling.py"),
    p("""In practice: use **one** underscore for internal attributes, and reserve two underscores for classes designed to be subclassed by
    people who might pick the same names. Names with two underscores on **both** sides (`__init__`, `__len__`) are not mangled; they are
    the special methods of 9.2, and inventing new ones of your own is discouraged. And secrets such as API keys need real protection
    (environment variables, a secrets manager, 12.4); within an object, the useful measure is a `__repr__` that never shows them
    (problem 11)."""),
)

section("slots", "`__slots__`: fixed attributes, less memory",
    p("""Normally each instance stores its attributes in its own `__dict__`, which is flexible (you can add any attribute at any time) but
    costs memory: a dict per object, typically around a hundred bytes or more on top of the values. A class can instead declare
    **`__slots__`**, a tuple of the attribute names it allows. Instances then have **no** `__dict__`; the values are stored in fixed
    slots, each object is smaller, and assigning any attribute not listed raises `AttributeError`, so a typo such as `self.socre = 1`
    fails loudly instead of silently creating a new attribute (problem 10)."""),
    ex("""
    import sys

    class PointDict:
        def __init__(self, x, y):
            self.x, self.y = x, y

    class PointSlots:
        __slots__ = ("x", "y")
        def __init__(self, x, y):
            self.x, self.y = x, y

    a, b = PointDict(1, 2), PointSlots(1, 2)
    print(hasattr(a, "__dict__"), hasattr(b, "__dict__"))
    print(sys.getsizeof(a) + sys.getsizeof(a.__dict__) > sys.getsizeof(b))
    a.z = 3                                     # allowed: goes into a.__dict__
    try:
        b.z = 3
    except AttributeError as e:
        print("AttributeError:", e)
    """, "slots.py"),
    p("""Use `__slots__` for classes with **many instances** (millions of tokens, spans, graph nodes or records) where the memory saving is
    real, or when catching attribute typos matters. The trade-offs: no dynamic attributes, no `cached_property` (it needs `__dict__`)
    unless you add `"__dict__"` to the slots, class-level default values for slotted names are not allowed, and with inheritance every
    class in the chain must declare its own `__slots__` to keep the benefit. `@dataclass(slots=True)` (11.3) generates them for you."""),
)

section("descriptors", "How properties work",
    p("""A `property` is an object stored **on the class**, under the attribute's name. Objects that define `__get__` (and optionally
    `__set__`) are called **descriptors**, and attribute lookup gives them special treatment: when you read `obj.temperature`, Python finds
    the `property` object on the class and calls its `__get__`, which calls your getter method with `obj`. Assignment `obj.temperature =
    v` calls its `__set__`, which calls your setter. That is the whole mechanism; methods themselves work the same way, which is how
    `obj.method` becomes a bound method (9.1)."""),
    p("""The lookup order from 9.1 has one refinement because of this. A **data descriptor** (one with `__set__`, such as `property`) on the class
    takes precedence over the instance's `__dict__`, so a property cannot be bypassed by putting a value in the instance dict. A
    **non-data descriptor** (only `__get__`, such as a plain function or `cached_property`) is overridden by the instance's `__dict__`, which
    is exactly how `cached_property` works: after the first access, the stored value in the instance dict wins and the method is no
    longer called (problem 16). Frameworks build on descriptors: Django and SQLAlchemy model fields, and Pydantic's validated fields, are
    descriptors or work alongside them."""),
    ex("""
    import functools

    class Demo:
        @property
        def p(self):
            return "property value"

        @functools.cached_property
        def c(self):
            return "computed once"

    d = Demo()
    d.__dict__["p"] = "instance dict value"
    d.__dict__["c"] = "instance dict value"
    print(d.p, "|", d.c)
    print(type(Demo.__dict__["p"]).__name__, hasattr(Demo.__dict__["p"], "__set__"))
    """, "descriptors.py"),
)

section("warmup", "Warm-up",
    predict("Computed and read-only", "easy",
        code="""
        class Cart:
            def __init__(self):
                self._items = {}

            def add(self, name, price):
                self._items[name] = price

            @property
            def total(self):
                print("  computing")
                return sum(self._items.values())

        c = Cart()
        c.add("pen", 2); c.add("book", 10)
        print(c.total)
        print(c.total + 1)
        try:
            c.total = 0
        except AttributeError:
            print("read-only")
        print(type(Cart.total).__name__, "total" in vars(c))
        """,
        hints=["A property runs its method on every read. Without a setter, assignment fails."],
        why="""Each read of `c.total` calls the method, so "computing" prints twice. The property has no setter, so assignment raises
        `AttributeError`. The property object lives on the class (`type(Cart.total)` is `property`), and the instance stores no `total` at
        all: the value is derived from `_items` every time, so it can never be stale."""),
    write("A validated generation config", "easy", tag="GenAI",
        prompt="""Write a class `SamplingConfig(temperature=1.0, top_p=1.0)` with properties `temperature` (a number in `[0, 2]`) and `top_p`
        (a number in `(0, 1]`, so 0 is not allowed), each with a setter that raises `ValueError` (with the name and the value in the message)
        and keeps the old value on failure. Booleans are not numbers here (`TypeError`). `__init__` must validate too. Add a read-only
        property `is_greedy`, true when temperature is 0.""",
        code="""
        class SamplingConfig:
            pass
        """,
        tests="""
        c = SamplingConfig()
        assert (c.temperature, c.top_p, c.is_greedy) == (1.0, 1.0, False)
        c.temperature = 0
        assert c.is_greedy and c.temperature == 0
        for attr, bad, kind in [("temperature", 2.5, ValueError), ("top_p", 0, ValueError), ("top_p", 1.2, ValueError), ("temperature", True, TypeError)]:
            try:
                setattr(c, attr, bad)
                assert False, (attr, bad)
            except kind as e:
                assert attr in str(e)
        assert c.temperature == 0 and c.top_p == 1.0
        try:
            SamplingConfig(top_p=0)
            assert False
        except ValueError:
            pass
        try:
            c.is_greedy = True
            assert False
        except AttributeError:
            pass
        """,
        hints=["A small helper `_check_number(name, value)` can raise the `TypeError` for both setters.", "In `__init__`, assign `self.temperature = temperature` so the setter runs."],
        solution="""
        class SamplingConfig:
            def __init__(self, temperature=1.0, top_p=1.0):
                self.temperature = temperature
                self.top_p = top_p

            @staticmethod
            def _check_number(name, value):
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise TypeError(f"{name} must be a number, got {value!r}")

            @property
            def temperature(self):
                return self._temperature

            @temperature.setter
            def temperature(self, value):
                self._check_number("temperature", value)
                if not 0 <= value <= 2:
                    raise ValueError(f"temperature must be in [0, 2], got {value}")
                self._temperature = value

            @property
            def top_p(self):
                return self._top_p

            @top_p.setter
            def top_p(self, value):
                self._check_number("top_p", value)
                if not 0 < value <= 1:
                    raise ValueError(f"top_p must be in (0, 1], got {value}")
                self._top_p = value

            @property
            def is_greedy(self):
                return self._temperature == 0
        """,
        why="""Each setter is the single gate for its field, and `__init__` goes through the gates too, so no `SamplingConfig` can ever hold invalid
        values, whichever way it was created or changed. Checks run before storing, so a rejected assignment leaves the old value. The
        read-only `is_greedy` is derived from the stored temperature, so it is always correct. The shared type check lives in a static
        helper (9.6). This is the behaviour Pydantic gives a model field with `Field(ge=0, le=2)` (11.4), here written by hand so you can see
        what it does."""),
    fix("A setter that calls itself", "easy", tag="Data work",
        prompt="""Setting `Account.balance` crashes with `RecursionError`. Fix the property so the value is stored, and negative balances are
        rejected with `ValueError`.""",
        code="""
        class Account:
            def __init__(self, balance=0):
                self.balance = balance

            @property
            def balance(self):
                return self.balance

            @balance.setter
            def balance(self, value):
                if value < 0:
                    raise ValueError("balance cannot be negative")
                self.balance = value
        """,
        tests="""
        import sys
        _old_limit = sys.getrecursionlimit()
        sys.setrecursionlimit(120)          # the browser's stack is small: fail fast on runaway recursion
        a = Account(10)
        a.balance = 25
        assert a.balance == 25
        try:
            a.balance = -1
            assert False
        except ValueError:
            assert a.balance == 25
        assert Account().balance == 0
        sys.setrecursionlimit(_old_limit)
        """,
        hints=["Inside the property, `self.balance` **is** the property. Store the value under another name, `self._balance`."],
        solution="""
        class Account:
            def __init__(self, balance=0):
                self.balance = balance

            @property
            def balance(self):
                return self._balance

            @balance.setter
            def balance(self, value):
                if value < 0:
                    raise ValueError("balance cannot be negative")
                self._balance = value
        """,
        why="""The property owns the name `balance` on the class, and data descriptors take precedence over the instance dict, so every
        `self.balance = ...` inside the setter called the setter again, and every `self.balance` inside the getter called the getter again,
        until Python's recursion limit. The convention is to keep the real value in `self._balance` and let the property be the public face of
        it. `__init__` still assigns `self.balance`, deliberately, so the initial value is validated too."""),
    predict("Mangled names", "easy",
        code="""
        class Base:
            def __init__(self):
                self.__token = "base"
                self._note = "shared"

            def base_token(self):
                return self.__token

        class Child(Base):
            def __init__(self):
                super().__init__()
                self.__token = "child"
                self._note = "child note"

            def child_token(self):
                return self.__token

        c = Child()
        print(sorted(vars(c)))
        print(c.base_token(), c.child_token(), c._note)
        print(hasattr(c, "__token"), c._Base__token)
        """,
        hints=["Inside class `Base`, `self.__token` becomes `self._Base__token`; inside `Child`, `self._Child__token`."],
        why="""Each class's `__token` is mangled with its own class name, so the base and the child keep separate attributes and neither overwrites the
        other, which is the purpose of mangling. The single-underscore `_note` is not mangled, so the child's assignment replaces the base's
        value. From outside, `__token` does not exist under that name, but the mangled name is perfectly reachable."""),
)

section("medium", "Medium",
    write("A conversation with computed properties", "medium", tag="GenAI",
        prompt="""Write a class `Conversation(system_prompt)` with: a `system_prompt` property whose setter rejects empty or whitespace-only text
        (`ValueError`) and stores it stripped; `add(role, content)`; a read-only `messages` property returning a **tuple** of new dicts,
        system message first; a read-only `token_count` property (words in all messages, `len(text.split())`); and a read-only `turns`
        property (number of non-system messages).""",
        code="""
        class Conversation:
            pass
        """,
        tests="""
        c = Conversation("  Be brief. ")
        c.add("user", "What is the refund window?")
        c.add("assistant", "Thirty days.")
        assert c.system_prompt == "Be brief." and c.turns == 2 and c.token_count == 2 + 5 + 2
        msgs = c.messages
        assert isinstance(msgs, tuple) and msgs[0] == {"role": "system", "content": "Be brief."}
        msgs[1]["content"] = "changed"
        assert c.messages[1]["content"] == "What is the refund window?"
        c.system_prompt = "Be formal and brief."
        assert c.messages[0]["content"] == "Be formal and brief." and c.token_count == 11
        try:
            c.system_prompt = "   "
            assert False
        except ValueError:
            assert c.system_prompt == "Be formal and brief."
        try:
            c.turns = 0
            assert False
        except AttributeError:
            pass
        """,
        hints=["Store the turns in `self._turns` (a list) and the prompt in `self._system_prompt`; build `messages` from both on each read."],
        solution="""
        class Conversation:
            def __init__(self, system_prompt):
                self.system_prompt = system_prompt
                self._turns = []

            @property
            def system_prompt(self):
                return self._system_prompt

            @system_prompt.setter
            def system_prompt(self, text):
                text = text.strip()
                if not text:
                    raise ValueError("system prompt must not be empty")
                self._system_prompt = text

            def add(self, role, content):
                self._turns.append({"role": role, "content": content})

            @property
            def messages(self):
                system = {"role": "system", "content": self._system_prompt}
                return (system, *(dict(m) for m in self._turns))

            @property
            def token_count(self):
                return sum(len(m["content"].split()) for m in self.messages)

            @property
            def turns(self):
                return len(self._turns)
        """,
        why="""Everything a caller can see is either validated (`system_prompt`) or derived (`messages`, `token_count`, `turns`), so there is no
        state that can drift out of sync: changing the system prompt immediately changes the messages and the token count. The
        `messages` property returns a tuple of copied dicts, so callers can read the history and pass it to an API, but cannot alter the
        conversation by accident (2.3). Because these are properties, the call sites read naturally, `client.send(conv.messages)`, and if
        `token_count` later needs a real tokenizer or caching, its callers do not change."""),
    fix("A method used as if it were a property", "medium", tag="ML",
        prompt="""`Metrics.accuracy` is meant to be read as an attribute, but code such as `if m.accuracy > 0.9` behaves strangely and the
        report prints `<bound method ...>`. Fix the class so `accuracy` and `error_rate` are read-only computed attributes.""",
        code="""
        class Metrics:
            def __init__(self, correct, total):
                self.correct = correct
                self.total = total

            def accuracy(self):
                return self.correct / self.total if self.total else 0.0

            def error_rate(self):
                return 1 - self.accuracy

            def report(self):
                return f"accuracy={self.accuracy:.3f}"
        """,
        tests="""
        m = Metrics(45, 50)
        assert m.accuracy == 0.9 and round(m.error_rate, 3) == 0.1
        assert m.report() == "accuracy=0.900"
        m.correct = 50
        assert m.accuracy == 1.0
        assert Metrics(0, 0).accuracy == 0.0
        """,
        hints=["Without `@property`, `self.accuracy` is a bound method object, not a number."],
        solution="""
        class Metrics:
            def __init__(self, correct, total):
                self.correct = correct
                self.total = total

            @property
            def accuracy(self):
                return self.correct / self.total if self.total else 0.0

            @property
            def error_rate(self):
                return 1 - self.accuracy

            def report(self):
                return f"accuracy={self.accuracy:.3f}"
        """,
        why="""Without the decorator, `self.accuracy` evaluates to a bound method, so `1 - self.accuracy` raises `TypeError`, the f-string format
        `:.3f` fails, and in code that does not crash, `m.accuracy > 0.9` raises a `TypeError` too. `@property` makes reading the name call
        the method. Because the value is computed on each read, it follows changes to `correct` immediately. Deciding between a property and
        a method: use a property for cheap, side-effect-free values that feel like data, and a method for anything slow, with side effects,
        or needing arguments."""),
    write("Cache a vocabulary, and invalidate it", "medium", tag="ML",
        prompt="""Write a class `TextDataset(texts)` with a `functools.cached_property` `vocab` (sorted list of distinct lower-cased words), a
        `cached_property` `word_counts` (a `Counter` of all words), a counter attribute `builds` incremented each time either is computed,
        and methods `add(text)` and `remove(index)` that change the texts **and invalidate both cached values**. `len(dataset)` returns the
        number of texts.""",
        code="""
        import functools
        from collections import Counter

        class TextDataset:
            pass
        """,
        tests="""
        d = TextDataset(["Refund policy", "refund window"])
        assert d.vocab == ["policy", "refund", "window"] and d.vocab is d.vocab
        assert d.word_counts["refund"] == 2 and d.builds == 2
        d.vocab; d.word_counts
        assert d.builds == 2
        d.add("Shipping policy")
        assert d.vocab == ["policy", "refund", "shipping", "window"] and d.word_counts["policy"] == 2 and d.builds == 4
        d.remove(0)
        assert d.word_counts["policy"] == 1 and "policy" in d.vocab and len(d) == 2 and d.builds == 6
        """,
        hints=["Invalidate with `self.__dict__.pop(\"vocab\", None)` (and the same for `word_counts`), which works whether or not the value was computed."],
        solution="""
        import functools
        from collections import Counter

        class TextDataset:
            _CACHED = ("vocab", "word_counts")

            def __init__(self, texts):
                self._texts = list(texts)
                self.builds = 0

            def __len__(self):
                return len(self._texts)

            @functools.cached_property
            def word_counts(self):
                self.builds += 1
                return Counter(w for t in self._texts for w in t.lower().split())

            @functools.cached_property
            def vocab(self):
                self.builds += 1
                return sorted({w for t in self._texts for w in t.lower().split()})

            def _invalidate(self):
                for name in self._CACHED:
                    self.__dict__.pop(name, None)

            def add(self, text):
                self._texts.append(text)
                self._invalidate()

            def remove(self, index):
                del self._texts[index]
                self._invalidate()
        """,
        why="""Each cached value is computed on first access and stored in the instance dict, so repeated reads are free, which the unchanged
        `builds` count shows. Every method that changes `_texts` calls one `_invalidate` helper, so there is exactly one place that knows
        which values depend on the texts; forgetting it in a new method is the classic stale-cache bug. Popping with a default makes
        invalidation safe whether or not the value has been computed yet. For a dataset that changes constantly, plain properties (or
        updating the counts incrementally) may be better than caching at all."""),
    choose("Recompute on every read or cache", "medium", tag="RAG",
        prompt="Both classes expose the average document length of a fixed corpus of 5,000 texts; the code reads it 100 times. Which is faster?",
        setup="""import functools

texts = [f"refund request {i} about order {i % 97} " * 3 for i in range(5_000)]

class Live:
    def __init__(self, texts):
        self.texts = texts
    @property
    def avg_len(self):
        return sum(len(t.split()) for t in self.texts) / len(self.texts)

class Cached:
    def __init__(self, texts):
        self.texts = texts
    @functools.cached_property
    def avg_len(self):
        return sum(len(t.split()) for t in self.texts) / len(self.texts)""",
        options={
            "a": "c = Live(texts)\nvalues = [c.avg_len for _ in range(100)]",
            "b": "c = Cached(texts)\nvalues = [c.avg_len for _ in range(100)]",
        },
        answer="b",
        hints=["How many times does each version split 5,000 texts?"],
        why="""The plain property splits every text on every read: 100 passes over the corpus. The cached version does it once and then returns the
        value stored in the instance dict, a plain attribute read. Caching is correct here because the corpus does not change after
        construction; if texts could be added, the cached value would need invalidation, and the live property would be the safe default."""),
    trace("Setters that guard the state", "medium",
        prompt="Fill in `value` and `log` after each marked line.",
        code="""
        class Threshold:
            def __init__(self, value):
                self.log = []
                self.value = value

            @property
            def value(self):
                return self._value

            @value.setter
            def value(self, v):
                if not 0 <= v <= 1:
                    self.log.append(f"rejected {v}")
                    raise ValueError(v)
                self._value = round(v, 2)
                self.log.append(f"set {self._value}")

        t = Threshold(0.5)
        value, log = t.value, list(t.log)  # row: "created"
        t.value = 0.756
        value, log = t.value, list(t.log)  # row: "set 0.756"
        try:
            t.value = 1.5
        except ValueError:
            pass
        value, log = t.value, list(t.log)  # row: "rejected 1.5"
        """,
        trace_vars=["value", "log"],
        hints=["`__init__` assigns through the property. A rejected value raises before `_value` changes."],
        why="""Construction goes through the setter, so the first log entry comes from `__init__`. The setter normalises by rounding to two decimals, so
        0.756 is stored as 0.76. The invalid 1.5 is logged and rejected before `_value` is touched, so the threshold keeps 0.76: the
        invariant "between 0 and 1" holds at every moment."""),
    fix("A typo that silently creates a new attribute", "medium", tag="ML",
        prompt="""`TrainingState.step()` misspells an attribute, so the loss never updates and no error is raised. Make the class reject unknown
        attributes with `AttributeError` (so the typo fails loudly), and fix the typo.""",
        code="""
        class TrainingState:
            def __init__(self):
                self.epoch = 0
                self.best_loss = float("inf")

            def step(self, loss):
                self.epoch += 1
                if loss < self.best_loss:
                    self.best_los = loss
                return self.best_loss
        """,
        tests="""
        s = TrainingState()
        assert s.step(0.9) == 0.9 and s.step(1.2) == 0.9 and s.step(0.5) == 0.5 and s.epoch == 3
        try:
            s.best_los = 0.1
            assert False, "unknown attributes must be rejected"
        except AttributeError:
            pass
        assert not hasattr(s, "__dict__")
        """,
        hints=["`__slots__ = (\"epoch\", \"best_loss\")` removes `__dict__`, so only the listed names can be assigned."],
        solution="""
        class TrainingState:
            __slots__ = ("epoch", "best_loss")

            def __init__(self):
                self.epoch = 0
                self.best_loss = float("inf")

            def step(self, loss):
                self.epoch += 1
                if loss < self.best_loss:
                    self.best_loss = loss
                return self.best_loss
        """,
        why="""With a normal `__dict__`, `self.best_los = loss` is a valid assignment that creates a new attribute, so the bug was invisible: training
        "worked" and the best loss stayed infinite, which might make early stopping or checkpointing never trigger. `__slots__` fixes the set
        of attributes, so any misspelt assignment raises `AttributeError` at the exact line. Linters and type checkers (11.1) catch many
        such typos statically too. Saving memory is the other benefit of slots, irrelevant for one training state but large for millions of
        small objects."""),
    write("An API key that never leaks", "medium", tag="GenAI",
        prompt="""Write a class `Secret(value)` for API keys: `__repr__` and `__str__` both return `Secret('sk-1...')` style masking (first 4
        characters, then `...`; for values of 4 characters or fewer, just `Secret('***')`); a method `reveal()` returning the real value; a
        read-only property `fingerprint` returning the first 8 hex characters of the SHA-256 of the value; equality by value (and a matching
        hash). Reject empty values with `ValueError`.""",
        code="""
        import hashlib

        class Secret:
            pass
        """,
        tests="""
        k = Secret("sk-live-1234567890")
        assert repr(k) == "Secret('sk-l...')" and str(k) == repr(k) and f"{k}" == "Secret('sk-l...')"
        assert k.reveal() == "sk-live-1234567890" and "1234567890" not in repr([k, {"key": k}])
        assert k.fingerprint == hashlib.sha256(b"sk-live-1234567890").hexdigest()[:8]
        assert k == Secret("sk-live-1234567890") and len({k, Secret("sk-live-1234567890")}) == 1
        assert repr(Secret("abc")) == "Secret('***')"
        try:
            k.fingerprint = "x"
            assert False
        except AttributeError:
            pass
        try:
            Secret("")
            assert False
        except ValueError:
            pass
        """,
        hints=["Store the value in `self._value`; `__str__` can return `repr(self)`.", "`hashlib.sha256(value.encode()).hexdigest()[:8]`."],
        solution="""
        import hashlib

        class Secret:
            def __init__(self, value):
                if not value:
                    raise ValueError("secret must not be empty")
                self._value = value

            def __repr__(self):
                shown = self._value[:4] + "..." if len(self._value) > 4 else "***"
                return f"Secret({shown!r})"

            __str__ = __repr__

            def reveal(self):
                return self._value

            @property
            def fingerprint(self):
                return hashlib.sha256(self._value.encode()).hexdigest()[:8]

            def __eq__(self, other):
                if not isinstance(other, Secret):
                    return NotImplemented
                return self._value == other._value

            def __hash__(self):
                return hash(self._value)
        """,
        why="""Keys leak most often through logs, error messages and debug prints: an exception that shows a config dict, a log line with a client
        object, a test failure message. Making both `repr` and `str` masked means the key cannot appear by accident, even inside containers;
        reading the real value requires an explicit `reveal()` call that is easy to search for in code review. The fingerprint lets you
        log **which** key was used (for example after a rotation) without exposing it. Pydantic has `SecretStr` with the same idea, and this
        only protects against accidents: anyone with access to the process can still read `_value`."""),
    predict("cached_property lives in the instance", "medium",
        code="""
        import functools

        class Loader:
            def __init__(self):
                self.calls = 0

            @functools.cached_property
            def model(self):
                self.calls += 1
                return f"model-{self.calls}"

        a = Loader()
        print(a.model, a.model, a.calls, "model" in vars(a))
        del a.model
        print(a.model, a.calls)
        b = Loader()
        print(b.model, a.model)
        a.model = "patched"
        print(a.model, b.model)
        """,
        hints=["The first access stores the result in `vars(a)`; deleting it makes the next access compute again."],
        why="""The first access computes and stores `"model-1"` in the instance dict, so the second access just reads it and `calls` stays 1. `del a.model`
        removes the stored value, so the next access computes `"model-2"`. Each instance caches separately: `b` computes its own. Because
        `cached_property` is a non-data descriptor, assigning `a.model` simply writes the instance dict, which is handy for injecting a fake
        model in tests."""),
)

section("hard", "Hard",
    write("Linked properties that keep an invariant", "hard", tag="Data work",
        prompt="""Write a class `Window(start, end)` for a time range in seconds with properties `start`, `end` and `length`. Invariant:
        `0 <= start <= end`. Setting `start` or `end` to a value that breaks the invariant raises `ValueError` and changes nothing. Setting
        `length` keeps `start` and moves `end` (negative lengths are rejected). Add `shift(delta)` that moves both ends, rejected as a whole if
        it would make `start` negative, and `__repr__` like `Window(10, 25)`.""",
        code="""
        class Window:
            pass
        """,
        tests="""
        w = Window(10, 25)
        assert (w.start, w.end, w.length, repr(w)) == (10, 25, 15, "Window(10, 25)")
        w.length = 5
        assert (w.start, w.end) == (10, 15)
        w.end = 40
        w.start = 30
        assert (w.start, w.end, w.length) == (30, 40, 10)
        for attr, bad in [("start", 41), ("end", 29), ("start", -1), ("length", -2)]:
            try:
                setattr(w, attr, bad)
                assert False, (attr, bad)
            except ValueError:
                assert (w.start, w.end) == (30, 40)
        w.shift(-25)
        assert (w.start, w.end) == (5, 15)
        try:
            w.shift(-6)
            assert False
        except ValueError:
            assert (w.start, w.end) == (5, 15)
        try:
            Window(5, 1)
            assert False
        except ValueError:
            pass
        """,
        hints=["Validate a candidate pair with one private method, `_set(start, end)`, that checks and then assigns both. Every setter and `shift` goes through it."],
        solution="""
        class Window:
            def __init__(self, start, end):
                self._set(start, end)

            def _set(self, start, end):
                if not 0 <= start <= end:
                    raise ValueError(f"need 0 <= start <= end, got start={start}, end={end}")
                self._start, self._end = start, end

            def __repr__(self):
                return f"Window({self._start}, {self._end})"

            @property
            def start(self):
                return self._start

            @start.setter
            def start(self, value):
                self._set(value, self._end)

            @property
            def end(self):
                return self._end

            @end.setter
            def end(self, value):
                self._set(self._start, value)

            @property
            def length(self):
                return self._end - self._start

            @length.setter
            def length(self, value):
                if value < 0:
                    raise ValueError(f"length must not be negative, got {value}")
                self._set(self._start, self._start + value)

            def shift(self, delta):
                self._set(self._start + delta, self._end + delta)
        """,
        why="""All changes funnel through `_set`, which validates the **complete** new state before assigning anything, so no sequence of property
        assignments can leave the window invalid, even halfway. That is why setting `end = 40` before `start = 30` works but the opposite
        order (start 30 first) would be rejected while `end` was still 15: invariants that span several fields constrain the order of
        updates, and a method that sets both at once (like `shift`, or a `move_to(start, end)`) is often friendlier. `length` is not stored at
        all, so it can never disagree with `start` and `end`. This is the pattern for any object with related fields: one validating
        method, and properties as its public face."""),
    fix("Read the code: a model config", "hard", tag="GenAI",
        prompt="""`ModelConfig` should validate `temperature` (0 to 2) at creation and on assignment, never let callers modify its stop
        sequences except through `add_stop`, and report a `prompt_tokens` count that always matches the current `prompt`. Invalid configs can
        be created, `cfg.stop.append(...)` changes the config, and `prompt_tokens` is stale after the prompt changes. Read it, find the bugs
        and fix them.""",
        code="""
        import functools


        class ModelConfig:
            def __init__(self, prompt, temperature=0.7, stop=None):
                self.prompt = prompt
                self._temperature = temperature
                self._stop = stop if stop is not None else []

            @property
            def temperature(self):
                return self._temperature

            @temperature.setter
            def temperature(self, value):
                if not 0 <= value <= 2:
                    raise ValueError(f"temperature must be in [0, 2], got {value}")
                self._temperature = value

            @property
            def stop(self):
                return self._stop

            def add_stop(self, seq):
                if seq and seq not in self._stop:
                    self._stop.append(seq)

            @functools.cached_property
            def prompt_tokens(self):
                return len(self.prompt.split())
        """,
        tests="""
        try:
            ModelConfig("hi", temperature=5)
            assert False, "invalid temperature at creation"
        except ValueError:
            pass
        caller_stops = ["\\n\\n"]
        cfg = ModelConfig("Summarise the refund policy", stop=caller_stops)
        cfg.add_stop("User:")
        assert cfg.stop == ("\\n\\n", "User:") and caller_stops == ["\\n\\n"]
        try:
            cfg.stop.append("x")
            assert False, "stop must be read-only"
        except AttributeError:
            pass
        assert cfg.prompt_tokens == 4
        cfg.prompt = "Summarise the refund policy in three bullet points"
        assert cfg.prompt_tokens == 8
        cfg.temperature = 1.5
        assert cfg.temperature == 1.5
        """,
        hints=["`__init__` bypasses the setter by assigning `_temperature`.",
               "`stop` returns the internal list; return a tuple, and copy the caller's list in `__init__`.",
               "A cached value of a mutable input goes stale. A plain property (it is cheap) is the simplest fix."],
        solution="""
        class ModelConfig:
            def __init__(self, prompt, temperature=0.7, stop=None):
                self.prompt = prompt
                self.temperature = temperature
                self._stop = list(stop) if stop is not None else []

            @property
            def temperature(self):
                return self._temperature

            @temperature.setter
            def temperature(self, value):
                if not 0 <= value <= 2:
                    raise ValueError(f"temperature must be in [0, 2], got {value}")
                self._temperature = value

            @property
            def stop(self):
                return tuple(self._stop)

            def add_stop(self, seq):
                if seq and seq not in self._stop:
                    self._stop.append(seq)

            @property
            def prompt_tokens(self):
                return len(self.prompt.split())
        """,
        why="""Four bugs from this lesson. `__init__` assigned `self._temperature` directly, skipping the validation, so `temperature=5` created an
        invalid config; assigning through `self.temperature` makes construction obey the same rule as every later change. The `stop`
        property returned the internal list, so `cfg.stop.append(...)` bypassed `add_stop`; returning a tuple makes the public view
        read-only. `__init__` also stored the **caller's** list, so `add_stop` would have modified the caller's `caller_stops` (2.4);
        copying with `list(stop)` gives the config its own. And `prompt_tokens` was a `cached_property` over a mutable public attribute, so
        changing `prompt` left the count at the old value; counting words is cheap, so a plain property is both correct and simple. Caching
        is only safe when the inputs cannot change, or every change invalidates the cache."""),
    write("An immutable value object", "hard", tag="Data work",
        prompt="""Write a class `Price(amount, currency)` that is **immutable**: use `__slots__`, store the values in private slots, expose
        read-only properties `amount` and `currency`, and make **any** attribute assignment after construction raise `AttributeError` (override
        `__setattr__`). Normalise `currency` to upper case and reject negative amounts. Add `with_discount(pct)` returning a **new** `Price`,
        `__repr__` (`Price(19.99, 'EUR')`), and `__eq__`/`__hash__` by value.""",
        code="""
        class Price:
            pass
        """,
        tests="""
        p = Price(20.0, "eur")
        assert (p.amount, p.currency, repr(p)) == (20.0, "EUR", "Price(20.0, 'EUR')")
        q = p.with_discount(25)
        assert q == Price(15.0, "EUR") and p.amount == 20.0 and q is not p
        for attr in ["amount", "currency", "_amount", "anything"]:
            try:
                setattr(p, attr, 1)
                assert False, attr
            except AttributeError:
                pass
        assert p == Price(20, "EUR") and len({p, Price(20.0, "EUR"), q}) == 2 and not hasattr(p, "__dict__")
        try:
            Price(-1, "EUR")
            assert False
        except ValueError:
            pass
        """,
        hints=["`__setattr__` runs for **every** assignment, including those in `__init__`. Inside `__init__`, set the slots with `object.__setattr__(self, \"_amount\", value)`.",
               "`with_discount` builds a new object with `Price(...)`; it never changes `self`."],
        solution="""
        class Price:
            __slots__ = ("_amount", "_currency")

            def __init__(self, amount, currency):
                if amount < 0:
                    raise ValueError(f"amount must not be negative, got {amount}")
                object.__setattr__(self, "_amount", float(amount))
                object.__setattr__(self, "_currency", currency.upper())

            def __setattr__(self, name, value):
                raise AttributeError(f"Price is immutable: cannot set {name!r}")

            @property
            def amount(self):
                return self._amount

            @property
            def currency(self):
                return self._currency

            def with_discount(self, pct):
                return Price(round(self._amount * (1 - pct / 100), 2), self._currency)

            def __repr__(self):
                return f"Price({self._amount!r}, {self._currency!r})"

            def __eq__(self, other):
                if not isinstance(other, Price):
                    return NotImplemented
                return (self._amount, self._currency) == (other._amount, other._currency)

            def __hash__(self):
                return hash((self._amount, self._currency))
        """,
        why="""Immutability makes a value object safe to share and to use as a dict key or set member: the hash can never change, and no caller can
        alter a price another part of the program is relying on (2.2). `__setattr__` intercepts every assignment, so even the private slots
        cannot be changed from outside; construction uses `object.__setattr__`, the underlying mechanism, to set them once. Operations that
        "change" the value return a new object, like `str.upper()` or `int + int`. Storing `float(amount)` normalises `20` and `20.0` to one
        representation, so they compare and hash equal. `@dataclass(frozen=True, slots=True)` (11.3) generates almost exactly this class from
        two lines of field declarations."""),
    predict("Data and non-data descriptors", "hard",
        code="""
        import functools

        class Settings:
            def __init__(self):
                self._mode = "safe"

            @property
            def mode(self):
                return self._mode

            @functools.cached_property
            def limits(self):
                return {"safe": 10}[self._mode]

            def describe(self):
                return f"{self.mode}:{self.limits}"

        s = Settings()
        print(s.describe())
        s.__dict__["mode"] = "fast"
        s.__dict__["limits"] = 99
        print(s.mode, s.limits, s.describe())
        s.describe = lambda: "replaced"
        print(s.describe(), Settings.describe(s))
        """,
        hints=["A `property` defines `__set__`, so it wins over the instance dict. `cached_property` and plain functions do not."],
        why="""`property` is a data descriptor, so it takes precedence over the instance's `__dict__`: the entry `"mode"` placed there is ignored, and
        `s.mode` still calls the getter. `cached_property` and plain methods are non-data descriptors: an entry in the instance dict wins,
        so `s.limits` returns 99 and assigning `s.describe` replaces the method for that instance only, while calling it through the class
        still runs the original. This precedence rule is what makes properties reliable gates and cached properties cheap after the first
        access."""),
)

section("interview", "Interview questions",
    explain("Why does Python code use properties instead of getter and setter methods?", "medium", tag="Interview",
        why="""Because attribute access is the interface, and a property can take it over later without changing callers. You start with a plain
        public attribute; if you later need validation, normalisation, a computed value or lazy loading, you replace it with a `@property`
        of the same name, and `obj.x` and `obj.x = v` keep working everywhere. Writing `get_x()` and `set_x()` up front, as in Java, adds
        boilerplate for flexibility Python already gives you. Properties are for cheap, side-effect-free operations that feel like reading
        data; anything slow, with side effects or needing arguments should remain a method, so callers are not surprised by an attribute
        read that hits the network."""),
    explain("How does privacy work in Python: no underscore, one underscore, two underscores?", "medium", tag="Interview",
        why="""Nothing is truly private; privacy is a convention. A plain name is public API. A single leading underscore (`_cache`) marks an
        internal detail: callers should not use it, it can change without notice, `import *` skips it, and tools warn about outside access.
        Two leading underscores (`__cache`) trigger name mangling inside the class body, renaming it to `_ClassName__cache`, which prevents
        accidental collisions with attributes of the same name in subclasses; it does not prevent access, and it complicates testing, so it
        is used sparingly. Dunder names with underscores on both sides are special methods, not private. Real protection of invariants
        comes from properties, validating methods and returning copies, and real protection of secrets comes from keeping them out of the
        code and out of `repr`."""),
    explain("How do `property` and `functools.cached_property` work under the hood, and why does the difference matter?", "hard", tag="Interview",
        why="""Both are descriptors: objects stored on the class that customise attribute access via `__get__`. When you read `obj.name`, Python
        checks the class for a descriptor under that name. A **data descriptor** (one that defines `__set__` or `__delete__`, like `property`)
        takes precedence over the instance `__dict__`, so every read and write goes through the getter and setter, and nothing in the
        instance can bypass it: that is why properties work as validation gates. A **non-data descriptor** (only `__get__`, like
        functions and `cached_property`) is used only if the instance `__dict__` has no entry with that name. `cached_property` exploits this:
        its `__get__` computes the value and stores it in the instance dict, so later reads find the dict entry and never call the
        descriptor again, making them as fast as a normal attribute. Consequences: cached values can go stale and must be invalidated by
        deleting the entry, `cached_property` needs a `__dict__` (so it does not work with plain `__slots__`), and tests can override a cached
        property simply by assigning to it."""),
)

recap(
    "Python privacy is a convention: `_name` means internal. Encapsulation means protecting invariants, not hiding data.",
    "`@property` gives computed, read-only attributes; `@x.setter` validates and normalises assignments into `self._x`. Validate in `__init__` by assigning through the property.",
    "Start with plain attributes; switch to a property later without changing callers. Return tuples or copies, never internal mutable objects.",
    "`functools.cached_property` computes once and stores in the instance dict; invalidate it whenever its inputs change.",
    "`__name` is mangled to `_Class__name` (clash avoidance, not security). `__slots__` saves memory and rejects typo attributes. Properties are data descriptors and win over the instance dict.",
)
