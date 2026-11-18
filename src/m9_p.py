from lesson import *

lesson(
    id="m9-p", num="9.P", title="Module 9 practice set and mini project",
    intro="Mixed problems from all of Module 9: classes and instances, dunder methods, properties, inheritance and super, "
          "composition and protocols, class methods and copying. Then a mini project that needs all of it: a small "
          "provider layer for LLMs with a registry, validated settings, usage accounting and a caching wrapper.",
    desc="Mixed problems from the whole module, then one small program that uses all of it.",
    keys="practice mixed review project provider layer abc registry init_subclass from_config usage dunder property cache composition scaler transformer hybrid retriever attribute lookup",
)

section("how", "How to use this page",
    p("""For every class you write or read, check four things. **State:** what the instance owns, created in `__init__`, never shared through class
    attributes or mutable defaults (9.1). **Rules:** which invariants hold, guarded by properties and validating methods, with copies instead of
    internal objects handed out (9.3). **Protocol:** which dunders make it behave like the built-ins it resembles, with `__eq__` and
    `__hash__` consistent and `NotImplemented` for foreign types (9.2). **Relationships:** "is a" (inherit, honour the contract, call
    `super()`) or "has a" (compose and inject), and constructors that build `cls(...)` (9.4 to 9.6)."""),
    p("""The problems mix the lessons on purpose. The mini project combines all of them in the kind of layer every LLM application ends up
    writing."""),
)

section("set", "Practice set",
    predict("Instances, classes and methods", "easy",
        code="""
        class Counter:
            total = 0

            def __init__(self, name):
                self.name = name
                self.count = 0

            def hit(self):
                self.count += 1
                Counter.total += 1
                return self

            @classmethod
            def make(cls, name):
                return cls(name.upper())

        a, b = Counter("a"), Counter.make("b")
        a.hit().hit(); b.hit()
        print(a.count, b.count, Counter.total, a.total, b.name)
        a.total = 100
        print(Counter.total, a.total, vars(a))
        """,
        hints=["`Counter.total += 1` updates the class attribute; `a.total = 100` creates an instance attribute."],
        why="""Each instance has its own `count`, while `total` is updated through the class, so it is shared: 3 hits in total, visible from any instance.
        `make` is a classmethod factory that builds `cls(...)`, here with an upper-cased name. Assigning `a.total` creates an instance attribute
        that shadows the class value for `a` only, which `vars(a)` shows."""),
    write("A time interval value", "easy", tag="Data work",
        prompt="""Write a class `Interval(start, end)` (raise `ValueError` if `start > end`) with `__repr__` (`Interval(3, 8)`), `__len__` (the length),
        `__contains__` for numbers (`start <= x < end`), `__eq__` and `__hash__` by both ends, and a method `overlaps(other)`.""",
        code="""
        class Interval:
            pass
        """,
        tests="""
        a, b = Interval(3, 8), Interval(7, 10)
        assert repr(a) == "Interval(3, 8)" and len(a) == 5 and 3 in a and 8 not in a and 7.5 in a
        assert a.overlaps(b) and not a.overlaps(Interval(8, 9)) and a == Interval(3, 8) and len({a, Interval(3, 8), b}) == 2
        assert not Interval(4, 4) and (a == (3, 8)) is False
        try:
            Interval(5, 1)
            assert False
        except ValueError:
            pass
        """,
        hints=["`__len__` returning 0 makes empty intervals falsy. Two half-open intervals overlap when `a.start < b.end and b.start < a.end`."],
        solution="""
        class Interval:
            def __init__(self, start, end):
                if start > end:
                    raise ValueError(f"start {start} is after end {end}")
                self.start, self.end = start, end

            def __repr__(self):
                return f"Interval({self.start}, {self.end})"

            def __len__(self):
                return self.end - self.start

            def __contains__(self, x):
                return self.start <= x < self.end

            def __eq__(self, other):
                if not isinstance(other, Interval):
                    return NotImplemented
                return (self.start, self.end) == (other.start, other.end)

            def __hash__(self):
                return hash((self.start, self.end))

            def overlaps(self, other):
                return self.start < other.end and other.start < self.end
        """,
        why="""Each dunder hooks one piece of syntax (9.2): `len`, `in` and `==`, with the hash built from the same fields as equality so intervals work
        in sets. Half-open intervals (`start` included, `end` excluded) make adjacent intervals not overlap and lengths add up, the same
        convention as `range` and slicing. `__len__` returning 0 also makes an empty interval falsy. Note that `__len__` must return an
        integer, so this class works for integer ends; a float-based interval would expose a `length` property instead."""),
    fix("A repr that breaks printing", "easy", tag="GenAI",
        prompt="""Printing a `ToolCall` or a list of them raises `TypeError: __repr__ returned non-string`. Fix `__repr__` to return
        `ToolCall('search', {'q': 'refund'})`, and add a `__str__` returning `search(q='refund')`.""",
        code="""
        class ToolCall:
            def __init__(self, name, args):
                self.name = name
                self.args = dict(args)

            def __repr__(self):
                return (self.name, self.args)
        """,
        tests="""
        t = ToolCall("search", {"q": "refund"})
        assert repr(t) == "ToolCall('search', {'q': 'refund'})"
        assert str(t) == "search(q='refund')" and f"{t}" == "search(q='refund')"
        assert repr([t]) == "[ToolCall('search', {'q': 'refund'})]"
        assert str(ToolCall("now", {})) == "now()"
        """,
        hints=["`__repr__` and `__str__` must return strings. Build the arguments part with `\", \".join(f\"{k}={v!r}\" ...)`."],
        solution="""
        class ToolCall:
            def __init__(self, name, args):
                self.name = name
                self.args = dict(args)

            def __repr__(self):
                return f"{type(self).__name__}({self.name!r}, {self.args!r})"

            def __str__(self):
                arguments = ", ".join(f"{k}={v!r}" for k, v in self.args.items())
                return f"{self.name}({arguments})"
        """,
        why="""Python checks that `__repr__` and `__str__` return `str`; returning a tuple raises `TypeError` the first time anything prints the object, which
        can be deep inside a logging call. The repr shows the constructor form for developers; the str shows the call as a person would read
        it in an agent trace. `type(self).__name__` keeps the repr right for subclasses, and `!r` quotes string values."""),
    predict("A property overridden in a subclass", "medium",
        code="""
        class Plan:
            def __init__(self, seats):
                self.seats = seats

            @property
            def monthly(self):
                return self.seats * self.price_per_seat()

            def price_per_seat(self):
                return 10

        class Team(Plan):
            def price_per_seat(self):
                return 8 if self.seats >= 10 else super().price_per_seat()

        class Enterprise(Team):
            @property
            def monthly(self):
                return max(500, super().monthly)

        print(Plan(3).monthly, Team(3).monthly, Team(12).monthly)
        print(Enterprise(12).monthly, Enterprise(100).monthly, type(Team.monthly).__name__)
        """,
        hints=["The base property calls `self.price_per_seat()`, which subclasses override. `super().monthly` reads the parent's property."],
        why="""`Plan.monthly` is a template that calls an overridable hook: `Team` changes only the per-seat price, with a volume discount from 10 seats.
        `Enterprise` overrides the property itself and uses `super().monthly`, which evaluates the parent's property on the same instance (so
        `Team`'s price applies), then applies a minimum of 500. Properties are inherited and can be overridden like methods, since they are
        class attributes too."""),
    write("A conversation log with the container protocol", "medium", tag="GenAI",
        prompt="""Write a class `ConversationLog` with a classmethod `from_messages(messages)` (a list of `{"role", "content"}` dicts, copied), `append(role,
        content)`, `__len__`, `__iter__` (yielding copies of the dicts), `__getitem__` (an int gives a copy of one message dict, a slice gives a
        new `ConversationLog`), `__contains__` for a text (true if any message's content contains it, case-insensitive), and a `last_user`
        property returning the content of the last user message (or `None`).""",
        code="""
        class ConversationLog:
            pass
        """,
        tests="""
        msgs = [{"role": "system", "content": "Be brief."}, {"role": "user", "content": "Refund?"}, {"role": "assistant", "content": "5 days."}]
        log = ConversationLog.from_messages(msgs)
        msgs.append({"role": "user", "content": "late"})
        assert len(log) == 3 and log[1] == {"role": "user", "content": "Refund?"}
        log[1]["content"] = "changed"
        assert log[1]["content"] == "Refund?" and "REFUND" in log and "invoice" not in log
        tail = log[1:]
        assert isinstance(tail, ConversationLog) and len(tail) == 2 and log.last_user == "Refund?"
        log.append("user", "And invoices?")
        assert log.last_user == "And invoices?" and [m["role"] for m in log] == ["system", "user", "assistant", "user"]
        assert ConversationLog().last_user is None
        """,
        hints=["Store `self._messages` as a list of copied dicts; every method that hands out a message hands out `dict(m)`."],
        solution="""
        class ConversationLog:
            def __init__(self):
                self._messages = []

            @classmethod
            def from_messages(cls, messages):
                log = cls()
                for m in messages:
                    log.append(m["role"], m["content"])
                return log

            def append(self, role, content):
                self._messages.append({"role": role, "content": content})

            def __len__(self):
                return len(self._messages)

            def __iter__(self):
                for m in self._messages:
                    yield dict(m)

            def __getitem__(self, key):
                if isinstance(key, slice):
                    return type(self).from_messages(self._messages[key])
                return dict(self._messages[key])

            def __contains__(self, text):
                needle = text.lower()
                return any(needle in m["content"].lower() for m in self._messages)

            @property
            def last_user(self):
                for m in reversed(self._messages):
                    if m["role"] == "user":
                        return m["content"]
                return None
        """,
        why="""The class behaves like a read-only sequence of messages (indexing, slicing, iteration, `len`, `in`), but every message handed out is a
        copy, so callers cannot corrupt the history: the encapsulation rule of 9.3 implemented through the container protocol of 9.2. `in`
        is given a meaning that fits the domain (a text search) rather than dict equality. The slice builds a new log through the classmethod
        constructor, using `type(self)` so subclasses stay subclasses (9.6). `from_messages` reuses `append`, so there is one place where
        messages enter."""),
    fix("A subclass that tramples the base's internals", "medium", tag="RAG",
        prompt="""`Retriever` keeps its own cache in `self._cache`. `LoggingRetriever`, written by another team, also uses `self._cache` for its log of
        queries, which breaks the base's caching. Fix the **base** class so subclasses cannot clash with its private attributes (use name
        mangling), without changing `LoggingRetriever`.""",
        code="""
        class Retriever:
            def __init__(self, docs):
                self.docs = docs
                self._cache = {}

            def retrieve(self, query):
                if query not in self._cache:
                    self._cache[query] = [d for d in self.docs if query in d.lower()]
                return list(self._cache[query])

        class LoggingRetriever(Retriever):
            def __init__(self, docs):
                super().__init__(docs)
                self._cache = []

            def retrieve(self, query):
                self._cache.append(query)
                return super().retrieve(query)
        """,
        tests="""
        r = LoggingRetriever(["refund policy", "reset password"])
        assert r.retrieve("refund") == ["refund policy"] and r.retrieve("refund") == ["refund policy"]
        assert r._cache == ["refund", "refund"]
        assert Retriever(["a"]).retrieve("a") == ["a"]
        """,
        hints=["Rename the base's attribute to `self.__cache`; inside `Retriever`, Python stores it as `_Retriever__cache`."],
        solution="""
        class Retriever:
            def __init__(self, docs):
                self.docs = docs
                self.__cache = {}

            def retrieve(self, query):
                if query not in self.__cache:
                    self.__cache[query] = [d for d in self.docs if query in d.lower()]
                return list(self.__cache[query])

        class LoggingRetriever(Retriever):
            def __init__(self, docs):
                super().__init__(docs)
                self._cache = []

            def retrieve(self, query):
                self._cache.append(query)
                return super().retrieve(query)
        """,
        why="""Both classes wrote `self._cache` on the same instance, so the subclass replaced the base's dict with a list and the base's `query not in
        self._cache` then tested list membership, and indexing a list with a string crashed. This is precisely the problem name mangling solves
        (9.3): inside `Retriever`, `self.__cache` becomes `self._Retriever__cache`, a name no subclass will pick by accident. It is the right
        tool for base classes meant to be subclassed by other people; the alternative is composition (9.5), where the two objects never share
        attributes at all."""),
    write("Scalers with a shared interface", "medium", tag="ML",
        prompt="""Write an abstract base class `Scaler` (use `abc`) with abstract methods `fit(values)` and `_apply(value)`, a concrete `transform(values)`
        that raises `NotFittedError` (define it) if `fit` was not called, and a concrete `fit_transform(values)`. `fit` must return `self`. Implement
        `StandardScaler` (subtract the mean, divide by the population standard deviation, 1 if it is 0) and `MinMaxScaler` (map to `[0, 1]`, range 1
        if it is 0). Round transformed values to 4 decimals.""",
        code="""
        from abc import ABC, abstractmethod

        class Scaler(ABC):
            pass
        """,
        tests="""
        assert StandardScaler().fit_transform([1, 2, 3]) == [-1.2247, 0.0, 1.2247]
        mm = MinMaxScaler().fit([10, 20, 30])
        assert mm.transform([10, 25, 40]) == [0.0, 0.75, 1.5]
        assert StandardScaler().fit([5, 5]).transform([5, 7]) == [0.0, 2.0]
        try:
            MinMaxScaler().transform([1])
            assert False
        except NotFittedError:
            pass
        try:
            Scaler()
            assert False
        except TypeError:
            pass
        assert isinstance(mm, Scaler)
        """,
        hints=["Set a flag `self._fitted = True` at the end of each `fit`; `transform` checks it and maps `self._apply`.",
               "Population standard deviation: `sqrt(sum((x - mean) ** 2) / n)`."],
        solution="""
        import math
        from abc import ABC, abstractmethod


        class NotFittedError(Exception):
            pass


        class Scaler(ABC):
            _fitted = False

            @abstractmethod
            def fit(self, values):
                ...

            @abstractmethod
            def _apply(self, value):
                ...

            def transform(self, values):
                if not self._fitted:
                    raise NotFittedError(f"{type(self).__name__} must be fitted before transform")
                return [round(self._apply(v), 4) for v in values]

            def fit_transform(self, values):
                return self.fit(values).transform(values)


        class StandardScaler(Scaler):
            def fit(self, values):
                n = len(values)
                self.mean = sum(values) / n
                self.std = math.sqrt(sum((v - self.mean) ** 2 for v in values) / n) or 1.0
                self._fitted = True
                return self

            def _apply(self, value):
                return (value - self.mean) / self.std


        class MinMaxScaler(Scaler):
            def fit(self, values):
                self.low = min(values)
                self.range = (max(values) - self.low) or 1.0
                self._fitted = True
                return self

            def _apply(self, value):
                return (value - self.low) / self.range
        """,
        why="""The ABC fixes the interface every scaler shares, so pipeline code can call `fit` and `transform` on any of them, and it supplies
        `fit_transform` and the not-fitted check once. `fit` returning `self` allows `fit(...).transform(...)` chains, scikit-learn's convention.
        `_fitted = False` as a class attribute is a safe immutable default that each instance shadows when fitted (9.1). The scalers learn their
        parameters from training data only; applying them to new data (`25` and `40`) uses the stored parameters, which is why fitting on the
        test set is a leakage bug. scikit-learn's real `StandardScaler` follows exactly this `fit`/`transform` split."""),
    trace("Lookup, super and class methods together", "medium",
        prompt="Fill in `r` after each marked line.",
        code="""
        class Base:
            tag = "base"
            def __init__(self, x):
                self.x = x
            @classmethod
            def build(cls, x):
                return cls(x * 2)
            def label(self):
                return f"{self.tag}:{self.x}"

        class Mid(Base):
            tag = "mid"
            def label(self):
                return "[" + super().label() + "]"

        class Leaf(Mid):
            def __init__(self, x):
                super().__init__(x + 1)

        r = Base.build(1).label()  # row: "Base.build"
        r = Mid.build(1).label()  # row: "Mid.build"
        r = Leaf.build(1).label()  # row: "Leaf.build"
        r = [c.__name__ for c in Leaf.__mro__][:3]  # row: "Leaf MRO"
        """,
        trace_vars=["r"],
        hints=["`build` constructs `cls(x * 2)`, so `Leaf`'s own `__init__` runs and adds one."],
        why="""`build` doubles the value and constructs whichever class it was called on. `Mid` inherits `build` and `__init__`, and its `label` wraps the
        base's result, which reads `self.tag`, found on `Mid`. `Leaf` inherits `tag` and `label` from `Mid`, and its `__init__` adds one before
        calling the base initialiser, so `build(1)` gives 2, then 3. The MRO shows the search order behind all of it."""),
    write("A hybrid retriever by composition", "hard", tag="RAG",
        prompt="""Write `HybridRetriever(keyword, vector, weight=0.5)` composed of two retrievers, each an object with `search(query, k)` returning a list of
        `(doc_id, score)` pairs. `search(query, k)` asks both for `2 * k` results, normalises each list's scores to `[0, 1]` by dividing by that
        list's maximum (a list whose maximum is 0 contributes zeros), combines them as `weight * vector + (1 - weight) * keyword` (a document missing
        from one list gets 0 there), and returns the top `k` `(doc_id, combined)` pairs, highest first, ties by doc id, scores rounded to 4 decimals.
        Raise `ValueError` unless `0 <= weight <= 1`.""",
        code="""
        class HybridRetriever:
            pass
        """,
        tests="""
        class Fake:
            def __init__(self, results):
                self.results = results
                self.asked = []
            def search(self, query, k):
                self.asked.append(k)
                return self.results[:k]

        kw = Fake([("d1", 12.0), ("d2", 6.0), ("d3", 3.0)])
        vec = Fake([("d3", 0.9), ("d1", 0.45), ("d4", 0.3)])
        h = HybridRetriever(kw, vec, weight=0.5)
        assert h.search("refund", 2) == [("d1", 0.75), ("d3", 0.625)]
        assert kw.asked == [4] and vec.asked == [4]
        assert HybridRetriever(kw, vec, weight=1.0).search("x", 1) == [("d3", 1.0)]
        assert HybridRetriever(kw, Fake([]), weight=0.0).search("x", 3) == [("d1", 1.0), ("d2", 0.5), ("d3", 0.25)]
        try:
            HybridRetriever(kw, vec, weight=1.5)
            assert False
        except ValueError:
            pass
        """,
        hints=["A helper `_normalise(pairs)` returns a dict `{doc_id: score / max}`.", "Combine over the union of ids; sort with the key `(-score, doc_id)`."],
        solution="""
        class HybridRetriever:
            def __init__(self, keyword, vector, weight=0.5):
                if not 0 <= weight <= 1:
                    raise ValueError(f"weight must be in [0, 1], got {weight}")
                self.keyword = keyword
                self.vector = vector
                self.weight = weight

            @staticmethod
            def _normalise(pairs):
                top = max((s for _, s in pairs), default=0)
                return {d: (s / top if top else 0.0) for d, s in pairs}

            def search(self, query, k):
                kw = self._normalise(self.keyword.search(query, 2 * k))
                vec = self._normalise(self.vector.search(query, 2 * k))
                combined = {
                    d: round(self.weight * vec.get(d, 0.0) + (1 - self.weight) * kw.get(d, 0.0), 4)
                    for d in kw.keys() | vec.keys()
                }
                return sorted(combined.items(), key=lambda p: (-p[1], p[0]))[:k]
        """,
        why="""The hybrid retriever **has** two retrievers and knows only their `search` method, so either can be BM25, a vector store, a fake, or another
        hybrid: composition and duck typing (9.5). The two score scales are incomparable (BM25 scores of 12 versus cosine similarities below
        1), so each list is normalised before mixing; real systems also use reciprocal rank fusion, which ignores raw scores entirely. Asking each
        side for more candidates than needed (`2 * k`) lets a document that is second in one list and third in the other still win. Sorting by
        `(-score, id)` makes ties deterministic. The `weight` is validated once, at construction (9.3)."""),
    fix("Read the code: an agent class", "hard", tag="GenAI",
        prompt="""`Agent` holds a client and a set of tools; `SupportAgent` adds a greeting. Every agent shares one tool registry, `SupportAgent.create`
        returns plain `Agent`s, its tools are missing, and the repr prints the API key. Read it, find the bugs and fix them: each agent must have its
        own tools, `create` must build the class it is called on, `SupportAgent` must initialise its base, and the repr must mask the key
        (`Agent(model='small', key='sk-t...', tools=['search'])`).""",
        code="""
        class Agent:
            tools = {}

            def __init__(self, model, api_key):
                self.model = model
                self.api_key = api_key

            @classmethod
            def create(cls, config):
                return Agent(config["model"], config["api_key"])

            def add_tool(self, name, fn):
                self.tools[name] = fn
                return self

            def __repr__(self):
                return f"Agent(model={self.model!r}, key={self.api_key!r}, tools={sorted(self.tools)})"


        class SupportAgent(Agent):
            def __init__(self, model, api_key, greeting="Hi!"):
                self.greeting = greeting

            def reply(self, text):
                return f"{self.greeting} You said: {text}"
        """,
        tests="""
        a = Agent("small", "sk-test-123").add_tool("search", lambda q: [q])
        b = Agent("large", "sk-other-9")
        assert b.tools == {} and sorted(a.tools) == ["search"]
        assert repr(a) == "Agent(model='small', key='sk-t...', tools=['search'])" and "123" not in repr(a)
        s = SupportAgent.create({"model": "small", "api_key": "sk-test-123"})
        assert type(s) is SupportAgent and s.model == "small" and s.reply("refund") == "Hi! You said: refund"
        s.add_tool("faq", lambda q: q)
        assert sorted(s.tools) == ["faq"] and repr(s).startswith("SupportAgent(model='small', key='sk-t...'")
        """,
        hints=["`tools = {}` is a mutable class attribute; create it in `__init__`.",
               "`create` must return `cls(...)`; `SupportAgent.__init__` must call `super().__init__(model, api_key)`.",
               "Mask with `self.api_key[:4] + \"...\"`, and use `type(self).__name__` in the repr."],
        solution="""
        class Agent:
            def __init__(self, model, api_key):
                self.model = model
                self.api_key = api_key
                self.tools = {}

            @classmethod
            def create(cls, config):
                return cls(config["model"], config["api_key"])

            def add_tool(self, name, fn):
                self.tools[name] = fn
                return self

            def __repr__(self):
                masked = self.api_key[:4] + "..."
                return f"{type(self).__name__}(model={self.model!r}, key={masked!r}, tools={sorted(self.tools)})"


        class SupportAgent(Agent):
            def __init__(self, model, api_key, greeting="Hi!"):
                super().__init__(model, api_key)
                self.greeting = greeting

            def reply(self, text):
                return f"{self.greeting} You said: {text}"
        """,
        why="""Four bugs, one from each part of the module. The class-level `tools = {}` was one dict for every agent (9.1), so a tool added to one agent
        appeared on all of them: in a multi-tenant system, one customer's tools would be available to another's agent. `create` hard-coded
        `Agent(...)`, so the subclass's factory returned the base class (9.6). `SupportAgent.__init__` never called `super().__init__`, so
        `model` and `api_key` were never set (9.4). And the repr printed the full API key, which would end up in logs and tracebacks (9.3); the
        fixed repr masks it and uses the real class name. Each fix is small; together they are the difference between a toy and code you can
        deploy."""),
    explain("When would you make an object immutable, and how do you do it in Python?", "medium", tag="Interview",
        why="""Make an object immutable when it represents a **value**: money, a version, an interval, a label, a configuration snapshot, a cache key. Immutable
        objects can be shared freely without defensive copies, used as dict keys and set members (their hash cannot change), compared by value,
        and reasoned about easily, including across threads; "changes" return new objects, as with strings and tuples. In Python, use
        `@dataclass(frozen=True)` (11.3) or a `NamedTuple` for the common case; by hand, store values in `__slots__` or private attributes, expose
        read-only properties, block `__setattr__`, and define `__eq__` and `__hash__` from the fields. Remember that immutability is shallow:
        a frozen object holding a list can still have that list changed, so use tuples and frozensets inside. Keep mutable objects for things
        with identity and changing state: sessions, caches, connections, accumulators."""),
    explain("Walk through exactly what happens when Python evaluates `obj.attr`.", "hard", tag="Interview",
        why="""Python calls `type(obj).__getattribute__(obj, "attr")`, which for normal classes does the following. It searches the class's MRO for `attr`; if
        it finds a **data descriptor** there (an object with `__set__` or `__delete__`, such as a `property`), it calls its `__get__` and returns
        the result, so properties win over instance attributes. Otherwise it looks in the instance's `__dict__` (or its slots) and returns the
        value if present. Otherwise, if the class attribute found earlier is a **non-data descriptor** (a function, `classmethod`, `staticmethod`,
        `cached_property`), it calls its `__get__`, which for a function produces a bound method; if it is a plain class attribute, it returns
        it. If nothing was found, `__getattribute__` raises `AttributeError`, and Python then calls `__getattr__` if the class defines it, which
        is how proxies forward missing attributes. Dunder methods used by syntax (`len`, `+`) skip the instance entirely and are looked up on
        the type. Understanding this chain explains bound methods, property validation, `cached_property`, shadowing of class attributes and
        delegation."""),
    predict("Everything at once", "hard",
        code="""
        import copy
        from abc import ABC, abstractmethod

        class Shape(ABC):
            registry = {}
            def __init_subclass__(cls, **kw):
                super().__init_subclass__(**kw)
                Shape.registry[cls.__name__.lower()] = cls
            @abstractmethod
            def area(self): ...
            def __lt__(self, other):
                return self.area() < other.area()
            def __repr__(self):
                return f"{type(self).__name__}({self.area()})"

        class Square(Shape):
            def __init__(self, side):
                self.side = side
            def area(self):
                return self.side ** 2

        class Rect(Square):
            def __init__(self, w, h):
                super().__init__(w)
                self.h = h
            def area(self):
                return self.side * self.h

        shapes = [Rect(2, 5), Square(3), Rect(1, 2)]
        print(sorted(shapes), max(shapes), sorted(Shape.registry))
        c = copy.copy(shapes[1]); c.side = 4
        print(shapes[1], c, isinstance(c, Shape), Shape.registry["rect"].__mro__[1].__name__)
        """,
        hints=["`sorted` and `max` use `__lt__`; the registry fills when each subclass is defined; a shallow copy has its own `__dict__`."],
        why="""`__init_subclass__` registered both subclasses at definition time. Sorting uses `__lt__`, which compares areas: 2, 9 and 10, and `max` returns
        the largest. `Rect` inherits from `Square` and overrides `area`, so the repr (defined once in the ABC) shows each class's own area. The
        shallow copy of the square has its own attribute dict, so changing `side` on the copy leaves the original at 9. `Rect`'s MRO continues
        with `Square`, its direct base."""),
)

section("project", "Mini project: a provider layer for LLMs",
    p("""Every LLM application ends up with a thin layer between its business logic and the providers' SDKs: one interface for every model,
    validated settings, usage accounting, a way to choose a provider from configuration, and wrappers such as caching. Build that layer.
    Every rule in the spec maps to a lesson in this module, and the tests check each one."""),
    write("Build the provider layer", "hard", key="provider-layer", tag="Project",
        prompt="""Implement the following.

        - **`Usage(prompt=0, completion=0)`**: `__repr__` (`Usage(prompt=3, completion=2)`), `total` property, `__add__` and `__radd__` (so `sum()`
          works), and `__eq__`.
        - **`Response(text, usage, provider)`**: a plain class with those three attributes.
        - **`Provider`**, an abstract base class. Subclasses register themselves with a name in the class line, `class EchoProvider(Provider,
          name="echo")`, into `Provider.registry` (duplicates raise `ValueError`). `__init__(self, model, temperature=0.0)`; `temperature` is a
          property validated to `[0, 2]` (`ValueError`), also at construction. `complete(prompt)` strips the prompt, rejects an empty one with
          `ValueError`, calls the abstract `_generate(prompt)` which returns `(text, usage)`, adds the usage to a per-instance `usage_total`, and
          returns a `Response` with the provider's registered name. The classmethod `from_config(config)` builds the registered class named by
          `config["provider"]` (unknown names raise `KeyError`) with the remaining keys as keyword arguments.
        - **`EchoProvider`** (name `"echo"`): replies with the prompt; usage counts the words of the prompt and of the reply.
        - **`ReverseProvider`** (name `"reverse"`): replies with the prompt's words reversed; same usage rule.
        - **`CachedProvider(inner)`**: composition, not inheritance. Its `complete(prompt)` returns the cached `Response` for a prompt already
          seen (after stripping), and otherwise delegates to `inner.complete`. It counts `hits` and `misses`, and exposes `usage_total` as a
          read-only property that forwards to the inner provider.""",
        code="""
        from abc import ABC, abstractmethod


        class Usage:
            pass


        class Response:
            pass


        class Provider(ABC):
            pass


        class EchoProvider(Provider, name="echo"):
            pass


        class ReverseProvider(Provider, name="reverse"):
            pass


        class CachedProvider:
            pass
        """,
        tests="""
        assert sorted(Provider.registry) == ["echo", "reverse"] and Provider.registry["echo"] is EchoProvider
        u = Usage(3, 2) + Usage(1, 1)
        assert u == Usage(4, 3) and u.total == 7 and repr(u) == "Usage(prompt=4, completion=3)"
        assert sum([Usage(1, 2), Usage(3, 4)]) == Usage(4, 6)

        echo = Provider.from_config({"provider": "echo", "model": "e-1", "temperature": 0.5})
        assert type(echo) is EchoProvider and echo.temperature == 0.5 and echo.model == "e-1"
        r = echo.complete("  refund policy please ")
        assert (r.text, r.usage, r.provider) == ("refund policy please", Usage(3, 3), "echo")
        rev = ReverseProvider("r-1")
        assert rev.complete("one two three").text == "three two one"
        echo.complete("hi")
        assert echo.usage_total == Usage(4, 4) and rev.usage_total == Usage(3, 3)

        for bad in [lambda: echo.complete("   "), lambda: EchoProvider("x", temperature=3)]:
            try:
                bad()
                assert False
            except ValueError:
                pass
        try:
            echo.temperature = -1
            assert False
        except ValueError:
            assert echo.temperature == 0.5
        try:
            Provider.from_config({"provider": "nope", "model": "x"})
            assert False
        except KeyError:
            pass
        try:
            Provider("x")
            assert False
        except TypeError:
            pass
        try:
            class AnotherEcho(Provider, name="echo"):
                def _generate(self, prompt):
                    return prompt, Usage()
            assert False
        except ValueError:
            pass

        cached = CachedProvider(EchoProvider("e-2"))
        first = cached.complete("refund?")
        again = cached.complete(" refund? ")
        assert again is first and (cached.hits, cached.misses) == (1, 1) and cached.usage_total == Usage(1, 1)
        cached.complete("other")
        assert cached.misses == 2 and cached.usage_total == Usage(2, 2)
        try:
            cached.usage_total = Usage()
            assert False
        except AttributeError:
            pass
        assert not isinstance(cached, Provider)
        """,
        hints=["`__init_subclass__(cls, *, name, **kwargs)` registers each provider; check for duplicates before storing.",
               "In `__init__`, assign `self.temperature = temperature` so the property's setter validates; set `self.usage_total = Usage()`.",
               "`from_config` copies the dict, pops `\"provider\"`, looks up the class, and returns `cls_found(**rest)`.",
               "`CachedProvider` stores the inner provider and a dict from stripped prompt to `Response`."],
        solution="""
        from abc import ABC, abstractmethod


        class Usage:
            def __init__(self, prompt=0, completion=0):
                self.prompt = prompt
                self.completion = completion

            def __repr__(self):
                return f"Usage(prompt={self.prompt}, completion={self.completion})"

            @property
            def total(self):
                return self.prompt + self.completion

            def __add__(self, other):
                if not isinstance(other, Usage):
                    return NotImplemented
                return Usage(self.prompt + other.prompt, self.completion + other.completion)

            def __radd__(self, other):
                if other == 0:
                    return self
                return self.__add__(other)

            def __eq__(self, other):
                if not isinstance(other, Usage):
                    return NotImplemented
                return (self.prompt, self.completion) == (other.prompt, other.completion)


        class Response:
            def __init__(self, text, usage, provider):
                self.text = text
                self.usage = usage
                self.provider = provider


        class Provider(ABC):
            registry = {}

            def __init_subclass__(cls, *, name, **kwargs):
                super().__init_subclass__(**kwargs)
                if name in Provider.registry:
                    raise ValueError(f"provider {name!r} is already registered")
                cls.provider_name = name
                Provider.registry[name] = cls

            def __init__(self, model, temperature=0.0):
                self.model = model
                self.temperature = temperature
                self.usage_total = Usage()

            @property
            def temperature(self):
                return self._temperature

            @temperature.setter
            def temperature(self, value):
                if not 0 <= value <= 2:
                    raise ValueError(f"temperature must be in [0, 2], got {value}")
                self._temperature = value

            @abstractmethod
            def _generate(self, prompt):
                ...

            def complete(self, prompt):
                prompt = prompt.strip()
                if not prompt:
                    raise ValueError("prompt must not be empty")
                text, usage = self._generate(prompt)
                self.usage_total = self.usage_total + usage
                return Response(text, usage, self.provider_name)

            @classmethod
            def from_config(cls, config):
                options = dict(config)
                name = options.pop("provider")
                return cls.registry[name](**options)


        class EchoProvider(Provider, name="echo"):
            def _generate(self, prompt):
                return prompt, Usage(len(prompt.split()), len(prompt.split()))


        class ReverseProvider(Provider, name="reverse"):
            def _generate(self, prompt):
                text = " ".join(reversed(prompt.split()))
                return text, Usage(len(prompt.split()), len(text.split()))


        class CachedProvider:
            def __init__(self, inner):
                self.inner = inner
                self._cache = {}
                self.hits = 0
                self.misses = 0

            def complete(self, prompt):
                key = prompt.strip()
                if key in self._cache:
                    self.hits += 1
                    return self._cache[key]
                self.misses += 1
                response = self.inner.complete(prompt)
                self._cache[key] = response
                return response

            @property
            def usage_total(self):
                return self.inner.usage_total
        """,
        why="""Every lesson of the module has a job here:

        - **Classes and instances (9.1):** each provider owns its `usage_total`, created in `__init__`; the only shared mutable state is the
          registry, written deliberately through `Provider.registry`.
        - **Dunder methods (9.2):** `Usage` behaves like a number: `+`, `sum()` (thanks to `__radd__`), equality and a readable repr.
        - **Properties (9.3):** `temperature` is validated on assignment **and** at construction, and a failed assignment keeps the old value;
          `total` and the cache's `usage_total` are read-only views.
        - **Inheritance (9.4):** `complete` is a template method; providers implement only `_generate`; `__init_subclass__` registers each one by
          the name given in its class line and rejects duplicates.
        - **Composition and ABCs (9.5):** `Provider` cannot be instantiated without `_generate`; `CachedProvider` is not a `Provider` subclass
          but has the same `complete` method, so it wraps any provider.
        - **Class methods (9.6):** `from_config` picks the class from configuration and builds it, the way a settings file selects a model.

        Real layers add streaming, tool calling and async methods, but they keep this shape: one small interface, implementations registered by
        name, shared behaviour in the base, and cross-cutting features as wrappers (and Module 11 will let type checkers verify the whole
        structure)."""),
)

recap(
    "Own your state: create it in `__init__`, never in class attributes or mutable defaults, and hand out copies, not internals.",
    "Make objects feel native with dunders; keep `__eq__` and `__hash__` consistent; return `NotImplemented` for foreign types.",
    "Guard invariants with properties and validating methods, including in `__init__`.",
    "Inherit for real \"is a\" relationships with template methods and `super()`; compose and inject for everything else.",
    "Alternative constructors and registries are classmethods (or `__init_subclass__`) that build `cls(...)`; copy objects according to what they mean.",
)
