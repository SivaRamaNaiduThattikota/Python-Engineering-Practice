from lesson import *
from diagrams import *

lesson(
    id="m9-4", num="9.4", title="Inheritance and super",
    intro="A subclass reuses and specialises another class. How attribute lookup walks the class chain, overriding and "
          "extending methods with `super()`, what `super()` really calls (the method resolution order), the template-method "
          "pattern, the substitution rule that keeps hierarchies honest, cooperative multiple inheritance and mixins, "
          "`__init_subclass__`, and why subclassing `dict` misleads. Applied to retrievers, providers, metrics and loaders.",
    desc="Overriding, `super()`, the MRO, and when not to inherit.",
    keys="inheritance subclass base class parent child override super method resolution order mro c3 diamond multiple inheritance mixin cooperative template method liskov substitution isinstance issubclass init_subclass userdict",
)

term("Subclass", "A class defined from another, `class Child(Base)`, which inherits all of the base's attributes and methods and can override some of them.")
term("Override", "Defining a method in a subclass with the same name as one in the base class, so the subclass's version is used for its instances.")
term("MRO", "Method resolution order: the list of classes Python searches, in order, to find an attribute. `Class.__mro__` shows it.")
term("Mixin", "A small class that adds one capability (such as `to_json`) and is meant to be combined with other classes by multiple inheritance.")

section("basics", "Subclasses inherit, and can specialise",
    p("""`class KeywordRetriever(Retriever):` defines a **subclass**: every attribute and method of `Retriever`, the **base class**, is
    available on instances of `KeywordRetriever` without being written again. The subclass can add new methods, and it can **override**
    inherited ones by defining a method with the same name. The relationship should read as "is a": a keyword retriever **is a**
    retriever, so anywhere code expects a `Retriever`, a `KeywordRetriever` can be used."""),
    p("""Inheritance works through attribute lookup (9.1). For `obj.name`, Python searches the instance's `__dict__`, then the object's
    class, then that class's base, and so on up the chain, ending at `object`, the root of every class. The first match wins, which is
    exactly why overriding works: the subclass is searched before the base."""),
    ex("""
    class Retriever:
        def __init__(self, docs):
            self.docs = list(docs)

        def score(self, query, doc):
            return 0

        def retrieve(self, query, k=2):
            ranked = sorted(self.docs, key=lambda d: self.score(query, d), reverse=True)
            return ranked[:k]

    class KeywordRetriever(Retriever):
        def score(self, query, doc):                      # override
            return len(set(query.lower().split()) & set(doc.lower().split()))

    docs = ["Refund policy for orders", "Reset your password", "Refund window is 30 days"]
    kr = KeywordRetriever(docs)
    print(kr.retrieve("refund window"))
    print(isinstance(kr, Retriever), issubclass(KeywordRetriever, Retriever), type(kr) is Retriever)
    print([c.__name__ for c in KeywordRetriever.__mro__])
    """, "inherit.py"),
    p("""`retrieve` is defined once, in the base class, and it calls `self.score(...)`. For a `KeywordRetriever`, `self.score` finds the
    subclass's override first. So the base class's algorithm uses the subclass's scoring without knowing it exists: the base defines
    the **steps**, the subclass fills in one of them. That is the **template method** pattern, the most useful thing inheritance does
    (problem 2). `isinstance` respects the hierarchy, while `type(x) is Base` does not, which is why `isinstance` is the right check
    in almost all code."""),
)

section("super", "Extending a method with `super()`",
    p("""Often a subclass wants to **add** to an inherited method rather than replace it: do what the base does, plus something more.
    `super().method(...)` calls the next class's version of the method on the same instance. The most important case is `__init__`:
    if a subclass defines its own `__init__`, the base's `__init__` is **not** called automatically, so the base's attributes are never
    set unless the subclass calls `super().__init__(...)`. Forgetting it is the most common inheritance bug, and it fails later, with an
    `AttributeError` far from the cause (problem 3)."""),
    ex("""
    class Retriever:
        def __init__(self, docs):
            self.docs = list(docs)
            self.calls = 0

        def retrieve(self, query, k=2):
            self.calls += 1
            return [d for d in self.docs if query.lower() in d.lower()][:k]

    class FilteredRetriever(Retriever):
        def __init__(self, docs, banned):
            super().__init__(docs)                 # set up everything the base needs
            self.banned = set(banned)

        def retrieve(self, query, k=2):
            results = super().retrieve(query, k=len(self.docs))   # reuse, then extend
            return [d for d in results if not self.banned & set(d.lower().split())][:k]

    fr = FilteredRetriever(["Refund policy", "Refund scam alert", "Refund window"], banned=["scam"])
    print(fr.retrieve("refund"), fr.calls, sorted(vars(fr)))
    """, "super_extend.py"),
    p("""`super()` without arguments works inside methods because Python knows which class the method was defined in and which instance it
    was called on. The extension pattern is: call `super()` to get the base behaviour, then add or adjust. Calling `Retriever.retrieve(self,
    ...)` by name also works with single inheritance, but it breaks the cooperation that multiple inheritance needs (below), so
    `super()` is the habit to build."""),
)

section("mro", "What `super()` really calls: the MRO",
    fig(chain([("D(B, C)", "accent"), "B(A)", "C(A)", "A", "object"], note="D.__mro__: D, B, C, A, object"),
        "For the diamond `class D(B, C)` with `B` and `C` both inheriting `A`, the MRO visits each class once; `super()` moves one step along it."),
    p("""With single inheritance, `super()` means "the parent". In general it means something more precise: **the next class in the method
    resolution order** of the instance's class. The MRO is the list Python searches for attributes, available as `Class.__mro__`. For
    multiple inheritance, `class D(B, C)`, Python computes it with the **C3 linearisation** algorithm, which guarantees that every class
    appears before its bases, that the order of bases you wrote is respected, and that each class appears exactly once."""),
    ex("""
    class Base:
        def greet(self):
            return ["Base"]

    class Polite(Base):
        def greet(self):
            return ["Polite"] + super().greet()

    class Brief(Base):
        def greet(self):
            return ["Brief"] + super().greet()

    class Assistant(Polite, Brief):
        def greet(self):
            return ["Assistant"] + super().greet()

    print([c.__name__ for c in Assistant.__mro__])
    print(Assistant().greet())
    print(Polite().greet())
    """, "mro.py"),
    p("""In `Assistant`, `super()` inside `Polite.greet` does **not** go to `Base`, even though `Base` is `Polite`'s parent: it goes to `Brief`,
    the next class in `Assistant`'s MRO. Only `Brief`'s `super()` reaches `Base`. That is how every class in a "diamond" gets called
    exactly once, in a predictable order. It also means a class using `super()` does not know which method it will call next; that is
    decided by the class of the actual instance. For this to work, every method in the chain must call `super()` and accept the
    arguments the others might pass, usually through `**kwargs` (problem 11)."""),
)

section("contract", "The substitution rule",
    p("""Inheritance is a promise: an instance of the subclass can be used **wherever** the base class is expected, without the caller
    noticing a difference in the rules. This is the **Liskov substitution principle**. In practice an override must accept the same
    arguments as the base method (it may accept more, with defaults), return the same kind of result, and not raise errors that
    callers of the base would not expect, or demand more of its inputs. Breaking the promise makes the base class's own code fail:
    the template method calls the hook with the base's signature (problem 9)."""),
    ex("""
    class Loader:
        def load(self, path, encoding="utf-8"):
            return f"text of {path}"

        def load_many(self, paths):
            return [self.load(p, encoding="utf-8") for p in paths]

    class BrokenPDFLoader(Loader):
        def load(self, path):                       # dropped the encoding parameter
            return f"pdf text of {path}"

    class PDFLoader(Loader):
        def load(self, path, encoding="utf-8", password=None):   # same contract, plus an optional extra
            return f"pdf text of {path}"

    print(PDFLoader().load_many(["a.pdf", "b.pdf"]))
    try:
        BrokenPDFLoader().load_many(["a.pdf"])
    except TypeError as e:
        print("TypeError:", e)
    """, "substitution.py"),
    p("""A classic violation is a "read-only list" that subclasses `list` and raises on `append`: any function that receives a list and
    appends to it breaks. If the subclass cannot honour the base's interface, it is not an "is a" relationship, and composition (9.5),
    holding the other object instead of inheriting from it, is the right design."""),
)

section("mixins", "Multiple inheritance and mixins",
    p("""Python allows several base classes. The common, safe use is **mixins**: small classes that each add one capability and are combined
    with a main class: a `JsonMixin` that adds `to_json()`, a `ReprMixin` that adds a generic `__repr__`, a `TimestampMixin` that records
    creation time. Mixins usually have no state of their own, or initialise it cooperatively: their `__init__` takes `**kwargs`, picks
    out what it needs, and passes the rest on with `super().__init__(**kwargs)`, so that every class in the MRO gets its arguments."""),
    ex("""
    import json

    class JsonMixin:
        def to_json(self):
            return json.dumps({k: v for k, v in vars(self).items() if not k.startswith("_")}, sort_keys=True)

    class TaggedMixin:
        def __init__(self, *, tags=(), **kwargs):
            super().__init__(**kwargs)
            self.tags = sorted(set(tags))

    class Record:
        def __init__(self, *, id, text):
            self.id = id
            self.text = text

    class Document(JsonMixin, TaggedMixin, Record):
        pass

    d = Document(id=7, text="Refund policy", tags=["billing", "faq", "billing"])
    print(d.to_json())
    print([c.__name__ for c in Document.__mro__])
    """, "mixins.py"),
    p("""Calling `Document(...)` runs the first `__init__` found in the MRO, `TaggedMixin.__init__`, which takes `tags` and forwards `id` and
    `text` to the next class, `Record`. Keyword-only arguments make this forwarding safe. Mixins are how frameworks compose behaviour:
    Django's class-based views, scikit-learn's `ClassifierMixin` and `TransformerMixin` (which add `score` and `fit_transform`), and
    `socketserver.ThreadingMixIn`. Deep or tangled multiple inheritance, with state in several bases, is hard to reason about; keep
    mixins small and focused."""),
)

section("special", "Two specialised tools: `__init_subclass__` and subclassing built-ins",
    p("""A base class can react whenever a **subclass is defined**, by defining the class method `__init_subclass__(cls, **kwargs)`. Python
    calls it at class-creation time with the new subclass. It is the class-based version of registration decorators (8.4): a plugin
    base class can register every subclass automatically, validate that subclasses define required attributes, or accept keyword
    arguments in the class line, `class EchoProvider(Provider, name="echo"):` (problem 13)."""),
    ex("""
    class Provider:
        registry = {}

        def __init_subclass__(cls, *, name, **kwargs):
            super().__init_subclass__(**kwargs)
            if name in Provider.registry:
                raise ValueError(f"duplicate provider {name!r}")
            cls.name = name
            Provider.registry[name] = cls

        def complete(self, prompt):
            raise NotImplementedError

    class Echo(Provider, name="echo"):
        def complete(self, prompt):
            return prompt

    class Shout(Provider, name="shout"):
        def complete(self, prompt):
            return prompt.upper()

    print(sorted(Provider.registry), Provider.registry["shout"]().complete("hi"), Echo.name)
    """, "init_subclass.py"),
    p("""Subclassing **built-in** types needs care. A subclass of `dict` that overrides `__setitem__` (to lower-case keys, say) does not
    affect `dict.__init__`, `update` or `setdefault`, because the C implementation of those methods does not call your `__setitem__`.
    The object then holds keys that bypassed your rule (problem 6). The `collections` module offers `UserDict`, `UserList` and
    `UserString`, written in Python precisely so that every operation goes through the methods you override."""),
    ex("""
    from collections import UserDict

    class LowerDict(dict):
        def __setitem__(self, key, value):
            super().__setitem__(key.lower(), value)

    class LowerUserDict(UserDict):
        def __setitem__(self, key, value):
            super().__setitem__(key.lower(), value)

    a = LowerDict({"Model": "small"})
    a.update({"TEMP": 0.2})
    a["Seed"] = 1
    b = LowerUserDict({"Model": "small"})
    b.update({"TEMP": 0.2})
    b["Seed"] = 1
    print(sorted(a), sorted(b))
    """, "builtin_subclass.py"),
)

section("when", "When not to inherit",
    fig(flowchart({
        "isa": ("ask", 0, 0, "is it really a kind of|the parent, usable anywhere|the parent is?"),
        "inh": ("good", 1, 0, "inherit"),
        "comp": ("accent", 0, 1, "compose: keep the other|object as an attribute"),
    }, [("isa", "inh", "yes"), ("isa", "comp", "no")], cell=(270, 100), label="inheritance or composition"),
        "Inherit only for true is-a relationships that keep every promise of the parent; otherwise hold the other object and delegate to it."),
    p("""Inheritance couples the subclass tightly to the base: every change to the base's internals can break subclasses, subclasses depend on
    which methods the base calls internally, and deep hierarchies make it hard to see where a method comes from. Use it when there is a
    genuine "is a" relationship, a shared contract, and the base was designed for extension (it documents which methods to override).
    Typical good uses: exception hierarchies (7.2), a framework's base classes (`nn.Module`, `BaseEstimator`, a provider base), and
    mixins."""),
    p("""Prefer **composition**, holding another object and calling it, when you want to **reuse** code without promising the whole
    interface, when the relationship is "has a" or "uses a" (a chat session **has a** client; a cached retriever **uses a** retriever), or
    when the behaviour should be swappable at run time. Lesson 9.5 shows composition and protocols, which most modern Python code prefers
    for flexibility. A useful smell test: if you are overriding methods to make them raise or do nothing, inheritance is the wrong tool."""),
)

section("warmup", "Warm-up",
    predict("Lookup through the chain", "easy",
        code="""
        class Base:
            kind = "base"
            def describe(self):
                return f"{self.kind}:{self.name()}"
            def name(self):
                return "B"

        class Child(Base):
            kind = "child"
            def name(self):
                return "C"

        class GrandChild(Child):
            def describe(self):
                return "gc+" + super().describe()

        print(Base().describe(), Child().describe(), GrandChild().describe())
        print([c.__name__ for c in GrandChild.__mro__])
        print(isinstance(GrandChild(), Base), type(GrandChild()) is Child)
        """,
        hints=["`self.kind` and `self.name()` are looked up starting from the instance's own class."],
        why="""`Base.describe` uses `self.kind` and `self.name()`, which for a `Child` instance find `Child`'s versions. `GrandChild` inherits `kind`
        and `name` from `Child`, and its `describe` extends the inherited one through `super()`. The MRO lists the classes from the most
        specific to `object`. `isinstance` follows the hierarchy; an exact `type` comparison does not."""),
    write("A template method for retrievers", "easy", tag="RAG",
        prompt="""Write a base class `Retriever(docs)` whose `retrieve(query, k=3)` returns the top `k` documents ordered by
        `self.score(query, doc)` (highest first, ties keep the original order) and **only documents with a positive score**. Its own
        `score` raises `NotImplementedError`. Then write two subclasses: `OverlapRetriever` (score = number of shared lower-cased words) and
        `PrefixRetriever` (score = 1 if the document starts with the query, case-insensitive, else 0).""",
        code="""
        class Retriever:
            pass
        """,
        tests="""
        docs = ["Refund policy for orders", "Reset your password", "Refund window is 30 days", "Order status"]
        assert OverlapRetriever(docs).retrieve("refund window", k=2) == ["Refund window is 30 days", "Refund policy for orders"]
        assert OverlapRetriever(docs).retrieve("shipping") == []
        assert PrefixRetriever(docs).retrieve("refund") == ["Refund policy for orders", "Refund window is 30 days"]
        try:
            Retriever(docs).retrieve("x")
            assert False
        except NotImplementedError:
            pass
        assert issubclass(PrefixRetriever, Retriever)
        """,
        hints=["`sorted` is stable, so sorting by score with `reverse=True` keeps ties in their original order.", "Compute each score once: build `(score, doc)` pairs first."],
        solution="""
        class Retriever:
            def __init__(self, docs):
                self.docs = list(docs)

            def score(self, query, doc):
                raise NotImplementedError(f"{type(self).__name__} must implement score()")

            def retrieve(self, query, k=3):
                scored = [(self.score(query, d), d) for d in self.docs]
                ranked = sorted((pair for pair in scored if pair[0] > 0), key=lambda p: p[0], reverse=True)
                return [d for _, d in ranked[:k]]


        class OverlapRetriever(Retriever):
            def score(self, query, doc):
                return len(set(query.lower().split()) & set(doc.lower().split()))


        class PrefixRetriever(Retriever):
            def score(self, query, doc):
                return int(doc.lower().startswith(query.lower()))
        """,
        why="""The base owns the algorithm (score, filter, sort, cut), and each subclass supplies only the step that differs. Adding a third strategy
        means writing one small method. The base's `score` raises `NotImplementedError` with the subclass's name, so forgetting to override
        it fails loudly with a clear message; 9.5 shows how an abstract base class turns this into an error at instantiation. Scoring each
        document once matters when scoring is expensive (an embedding call), which is also why the scores are computed before sorting rather
        than inside the sort key."""),
    fix("A subclass that skips the base initialiser", "easy", tag="GenAI",
        prompt="""`StreamingClient` adds a buffer size to `Client`, but calling `ask` fails with `AttributeError: ... no attribute 'model'`.
        Fix the subclass.""",
        code="""
        class Client:
            def __init__(self, model, timeout=30):
                self.model = model
                self.timeout = timeout

            def ask(self, prompt):
                return f"[{self.model}, {self.timeout}s] {prompt}"

        class StreamingClient(Client):
            def __init__(self, model, buffer_size=64, timeout=30):
                self.buffer_size = buffer_size

            def ask(self, prompt):
                return super().ask(prompt) + f" (streamed in {self.buffer_size}-char chunks)"
        """,
        tests="""
        s = StreamingClient("small", buffer_size=16, timeout=10)
        assert s.ask("hi") == "[small, 10s] hi (streamed in 16-char chunks)"
        assert vars(s) == {"model": "small", "timeout": 10, "buffer_size": 16}
        assert StreamingClient("x").ask("y").startswith("[x, 30s]")
        """,
        hints=["Defining `__init__` in a subclass replaces the base's; call `super().__init__(model, timeout)` explicitly."],
        solution="""
        class Client:
            def __init__(self, model, timeout=30):
                self.model = model
                self.timeout = timeout

            def ask(self, prompt):
                return f"[{self.model}, {self.timeout}s] {prompt}"

        class StreamingClient(Client):
            def __init__(self, model, buffer_size=64, timeout=30):
                super().__init__(model, timeout)
                self.buffer_size = buffer_size

            def ask(self, prompt):
                return super().ask(prompt) + f" (streamed in {self.buffer_size}-char chunks)"
        """,
        why="""Python does not call a base `__init__` automatically when the subclass has its own; the subclass's `__init__` is simply found first in the
        MRO and runs alone. So `model` and `timeout` were never set, and the error appeared only when an inherited method used them.
        `super().__init__(...)` runs the base's setup on the same instance. Calling it first is the usual order, so the subclass can rely on
        the base's attributes; occasionally a subclass must prepare something before, which is fine as long as it calls it at all."""),
    predict("Types in a hierarchy", "easy",
        code="""
        class Animal: pass
        class Dog(Animal): pass
        class Puppy(Dog): pass

        p = Puppy()
        print(isinstance(p, Animal), isinstance(p, (int, Dog)), issubclass(Puppy, Animal))
        print(type(p) is Dog, type(p).__name__, Puppy.__bases__[0].__name__)
        print(issubclass(Dog, Dog), issubclass(Animal, Dog), issubclass(bool, int), isinstance(True, int))
        print([c.__name__ for c in Puppy.__mro__][-1])
        """,
        hints=["`issubclass(C, C)` is true. `bool` is a subclass of `int`. Every MRO ends with `object`."],
        why="""`isinstance` and `issubclass` follow the whole chain, and accept a tuple meaning "any of these". `type(p) is Dog` asks for the exact class,
        which is `Puppy`. A class counts as a subclass of itself. `bool` really is a subclass of `int`, which explains several surprises in
        earlier lessons (booleans accepted where numbers are expected). Every class ultimately inherits from `object`."""),
)

section("medium", "Medium",
    write("A provider base class", "medium", tag="GenAI",
        prompt="""Write a base class `Provider(model)` with a public method `complete(prompt)` that: strips the prompt and raises `ValueError` for an
        empty one; calls the hook `self._call(prompt)`, which subclasses implement (the base raises `NotImplementedError`); strips the result;
        increments `self.calls`; and returns `{"model": ..., "text": ...}`. Then write `EchoProvider` (returns the prompt) and
        `ReverseProvider` (returns the words in reverse order), each overriding only `_call`.""",
        code="""
        class Provider:
            pass
        """,
        tests="""
        e = EchoProvider("echo-1")
        assert e.complete("  refund policy ") == {"model": "echo-1", "text": "refund policy"}
        r = ReverseProvider("rev")
        assert r.complete("one two three")["text"] == "three two one" and r.calls == 1 and e.calls == 1
        for bad in ["", "   "]:
            try:
                e.complete(bad)
                assert False
            except ValueError:
                pass
        assert e.calls == 1
        try:
            Provider("base").complete("x")
            assert False
        except NotImplementedError:
            pass
        """,
        hints=["Keep validation, counting and post-processing in `complete`, so every subclass gets them for free."],
        solution="""
        class Provider:
            def __init__(self, model):
                self.model = model
                self.calls = 0

            def complete(self, prompt):
                prompt = prompt.strip()
                if not prompt:
                    raise ValueError("prompt must not be empty")
                text = self._call(prompt).strip()
                self.calls += 1
                return {"model": self.model, "text": text}

            def _call(self, prompt):
                raise NotImplementedError(f"{type(self).__name__} must implement _call()")


        class EchoProvider(Provider):
            def _call(self, prompt):
                return prompt


        class ReverseProvider(Provider):
            def _call(self, prompt):
                return " ".join(reversed(prompt.split()))
        """,
        why="""The public method is defined once and handles everything that must be the same for every provider (validation, counting, the result
        shape); subclasses implement only the one step that differs. The underscore on `_call` marks it as a hook for subclasses, not part of
        the public interface, so callers always go through `complete` and its rules. Real client libraries use this split: LangChain's chat
        models implement `_generate` while the base class handles callbacks, retries and output formatting; adding a new provider means
        implementing one method. Rejected prompts never reach `_call` or the counter."""),
    fix("A dict subclass whose rule is bypassed", "medium", tag="Data work",
        prompt="""`CaseInsensitiveHeaders` should store every key lower-cased, however the data arrives. Keys given to the constructor or to
        `update` keep their original case, so lookups fail. Fix it by building on `collections.UserDict`.""",
        code="""
        class CaseInsensitiveHeaders(dict):
            def __setitem__(self, key, value):
                super().__setitem__(key.lower(), value)

            def __getitem__(self, key):
                return super().__getitem__(key.lower())
        """,
        tests="""
        h = CaseInsensitiveHeaders({"Content-Type": "application/json"})
        h.update({"X-Request-ID": "r1"})
        h["Retry-After"] = "2"
        assert h["content-type"] == "application/json" and h["X-REQUEST-ID"] == "r1" and h["retry-after"] == "2"
        assert sorted(h) == ["content-type", "retry-after", "x-request-id"]
        assert "CONTENT-TYPE" in h and h.get("Retry-After") == "2"
        """,
        hints=["`UserDict` keeps the data in `self.data` and routes `__init__`, `update` and `setdefault` through `__setitem__`.",
               "Also lower-case keys in `__contains__`; `get` uses `__getitem__` in `UserDict`."],
        solution="""
        from collections import UserDict

        class CaseInsensitiveHeaders(UserDict):
            def __setitem__(self, key, value):
                self.data[key.lower()] = value

            def __getitem__(self, key):
                return self.data[key.lower()]

            def __contains__(self, key):
                return key.lower() in self.data
        """,
        why="""`dict`'s constructor and `update` are implemented in C and write directly into the hash table, so they never call a subclass's
        `__setitem__`; the rule "keys are lower-cased" held only for one way of adding data, which is the worst kind of invariant. `UserDict`
        is a plain Python class that stores the real dict in `self.data` and implements every method in terms of a few core ones, so
        overriding `__setitem__`, `__getitem__` and `__contains__` covers construction, `update`, `get` and `in`. HTTP headers are a real case:
        `requests` uses a similar case-insensitive mapping, because header names are case-insensitive by the HTTP standard."""),
    write("Metrics with a shared interface", "medium", tag="ML",
        prompt="""Write a base class `Metric` with `update(y_true, y_pred)` (taking lists of equal length, else `ValueError`), `compute()`,
        `reset()` and a `name` class attribute. The base's `update` checks lengths and calls the hook `self._update(y_true, y_pred)`; `reset`
        calls `__init__` again. Write `Accuracy` (correct / total, 0.0 if empty) and `MeanAbsoluteError` (mean of `abs(t - p)`, 0.0 if empty),
        each accumulating across several `update` calls. Write `evaluate(metrics, batches)` returning `{metric.name: rounded 4 value}`.""",
        code="""
        class Metric:
            pass
        """,
        tests="""
        batches = [([1, 0, 1], [1, 1, 1]), ([0, 0], [0, 0])]
        assert evaluate([Accuracy(), MeanAbsoluteError()], batches) == {"accuracy": 0.8, "mae": 0.2}
        acc = Accuracy()
        acc.update([1], [1]); acc.update([1, 1], [0, 1])
        assert round(acc.compute(), 4) == 0.6667
        acc.reset()
        assert acc.compute() == 0.0
        try:
            MeanAbsoluteError().update([1, 2], [1])
            assert False
        except ValueError:
            pass
        assert isinstance(Accuracy(), Metric)
        """,
        hints=["Each subclass's `__init__` sets its own counters; `reset` can simply call `self.__init__()`.", "`evaluate` resets each metric, feeds every batch, then computes."],
        solution="""
        class Metric:
            name = "metric"

            def update(self, y_true, y_pred):
                if len(y_true) != len(y_pred):
                    raise ValueError(f"length mismatch: {len(y_true)} vs {len(y_pred)}")
                self._update(y_true, y_pred)

            def _update(self, y_true, y_pred):
                raise NotImplementedError

            def compute(self):
                raise NotImplementedError

            def reset(self):
                self.__init__()


        class Accuracy(Metric):
            name = "accuracy"

            def __init__(self):
                self.correct = 0
                self.total = 0

            def _update(self, y_true, y_pred):
                self.correct += sum(t == p for t, p in zip(y_true, y_pred))
                self.total += len(y_true)

            def compute(self):
                return self.correct / self.total if self.total else 0.0


        class MeanAbsoluteError(Metric):
            name = "mae"

            def __init__(self):
                self.error = 0.0
                self.total = 0

            def _update(self, y_true, y_pred):
                self.error += sum(abs(t - p) for t, p in zip(y_true, y_pred))
                self.total += len(y_true)

            def compute(self):
                return self.error / self.total if self.total else 0.0


        def evaluate(metrics, batches):
            for m in metrics:
                m.reset()
                for y_true, y_pred in batches:
                    m.update(y_true, y_pred)
            return {m.name: round(m.compute(), 4) for m in metrics}
        """,
        why="""Every metric follows the same contract, so `evaluate` works with any of them, and with metrics not written yet: that is the payoff of a
        shared base. Validation lives once in the base's `update`; subclasses implement only accumulation and the final formula. Metrics that
        accumulate across batches (rather than averaging per-batch values) give the exact result for the whole dataset, which matters when
        batches have different sizes. `reset` reusing `__init__` keeps the initial state defined in one place. `torchmetrics` and Keras
        metrics use this exact `update`/`compute`/`reset` design."""),
    trace("The MRO and cooperative super", "medium",
        prompt="Fill in `order` and `calls` after each marked line.",
        code="""
        calls = []

        class A:
            def setup(self):
                calls.append("A")

        class B(A):
            def setup(self):
                calls.append("B")
                super().setup()

        class C(A):
            def setup(self):
                calls.append("C")
                super().setup()

        class D(B, C):
            def setup(self):
                calls.append("D")
                super().setup()

        order = [k.__name__ for k in D.__mro__][:-1]  # row: "MRO of D"
        D().setup()
        order = order  # row: "D().setup()"
        calls.clear(); B().setup()
        order = [k.__name__ for k in B.__mro__][:-1]  # row: "B alone"
        """,
        trace_vars=["order", "calls"],
        hints=["In `D`'s MRO, the class after `B` is `C`, not `A`."],
        why="""C3 linearisation puts `D` first, then its bases in the written order, then their common base `A`, so the order is D, B, C, A (then
        `object`, cut off here). Each `super().setup()` calls the next class in **D's** MRO, so `B`'s `super()` reaches `C`, and `A` runs
        once, last. For a plain `B` instance, the MRO is B, A, so `B`'s `super()` goes straight to `A`: the same line of code calls a
        different method depending on the instance's class."""),
    fix("An override that breaks the contract", "medium", tag="RAG",
        prompt="""`Chunker.chunk_all` calls `self.chunk(text, size)` for each document. `SentenceChunker` overrides `chunk` without the `size`
        parameter, so `chunk_all` fails for it. Fix the override so it honours the base contract: split into sentences on `". "`, then pack
        sentences into chunks of at most `size` characters (joined with `". "`), never splitting a sentence.""",
        code="""
        class Chunker:
            def chunk(self, text, size):
                return [text[i:i + size] for i in range(0, len(text), size)]

            def chunk_all(self, texts, size=40):
                return [c for t in texts for c in self.chunk(t, size)]

        class SentenceChunker(Chunker):
            def chunk(self, text):
                return [s.strip() for s in text.split(". ") if s.strip()]
        """,
        tests="""
        text = "Refunds take 5 days. Contact support for help. Orders ship in 2 days"
        assert SentenceChunker().chunk_all([text], size=50) == ["Refunds take 5 days. Contact support for help", "Orders ship in 2 days"]
        assert SentenceChunker().chunk_all([text], size=10) == ["Refunds take 5 days", "Contact support for help", "Orders ship in 2 days"]
        assert Chunker().chunk_all(["abcdef"], size=4) == ["abcd", "ef"]
        """,
        hints=["Keep the signature `chunk(self, text, size)`. Pack greedily: add a sentence to the current chunk if the joined length stays within `size`, else start a new chunk."],
        solution="""
        class Chunker:
            def chunk(self, text, size):
                return [text[i:i + size] for i in range(0, len(text), size)]

            def chunk_all(self, texts, size=40):
                return [c for t in texts for c in self.chunk(t, size)]

        class SentenceChunker(Chunker):
            def chunk(self, text, size):
                sentences = [s.strip() for s in text.split(". ") if s.strip()]
                chunks, current = [], ""
                for s in sentences:
                    candidate = f"{current}. {s}" if current else s
                    if current and len(candidate) > size:
                        chunks.append(current)
                        current = s
                    else:
                        current = candidate
                if current:
                    chunks.append(current)
                return chunks
        """,
        why="""The base class's `chunk_all` is written against the base contract, `chunk(text, size)`; any subclass must accept those arguments, or the
        base's own code breaks for it, which is the substitution rule in practice. Accepting `size` and **using** it keeps the meaning too:
        a chunk never exceeds the limit unless a single sentence is longer than it, in which case it stays whole (the second test), a
        deliberate choice for sentence-based chunking. This is exactly how LangChain-style text splitters are organised: one base interface,
        several strategies."""),
    refactor("Duplicate classes into a base", "medium", tag="Data work",
        prompt="Move the shared code of `CsvExporter` and `TsvExporter` into a base class `Exporter`; keep their behaviour identical. Keep the tests green.",
        code="""
        class CsvExporter:
            def __init__(self, columns):
                self.columns = list(columns)
                self.rows_written = 0

            def export(self, rows):
                lines = [",".join(self.columns)]
                for row in rows:
                    lines.append(",".join(str(row.get(c, "")) for c in self.columns))
                    self.rows_written += 1
                return "\\n".join(lines)

        class TsvExporter:
            def __init__(self, columns):
                self.columns = list(columns)
                self.rows_written = 0

            def export(self, rows):
                lines = ["\\t".join(self.columns)]
                for row in rows:
                    lines.append("\\t".join(str(row.get(c, "")) for c in self.columns))
                    self.rows_written += 1
                return "\\n".join(lines)
        """,
        tests="""
        rows = [{"id": 1, "name": "Ana"}, {"id": 2}]
        csv = CsvExporter(["id", "name"])
        assert csv.export(rows) == "id,name\\n1,Ana\\n2," and csv.rows_written == 2
        tsv = TsvExporter(["id", "name"])
        assert tsv.export(rows[:1]) == "id\\tname\\n1\\tAna" and tsv.rows_written == 1
        """,
        hints=["The only difference is the separator: make it a class attribute `sep` that each subclass sets."],
        solution="""
        class Exporter:
            sep = ","

            def __init__(self, columns):
                self.columns = list(columns)
                self.rows_written = 0

            def export(self, rows):
                lines = [self.sep.join(self.columns)]
                for row in rows:
                    lines.append(self.sep.join(str(row.get(c, "")) for c in self.columns))
                    self.rows_written += 1
                return "\\n".join(lines)

        class CsvExporter(Exporter):
            sep = ","

        class TsvExporter(Exporter):
            sep = "\\t"
        """,
        why="""The two classes differed in a single value, so the base holds all the logic and each subclass only overrides a class attribute: the
        lightest possible specialisation, using the lookup rule that `self.sep` finds the subclass's value first. A bug fix in `export` now
        happens once. When the difference is that small, a parameter (`Exporter(columns, sep="\\t")`) would work just as well; subclasses earn
        their place when they bring different methods, or when other code needs to dispatch on the type. Real CSV output should use the
        `csv` module, which handles quoting (12.2)."""),
    write("Cooperative mixins", "medium", tag="Data work",
        prompt="""Write two mixins and a record class that cooperate through `super().__init__(**kwargs)`: `TimestampMixin` (takes keyword
        `created_at`, default `0.0`, and stores it), `ValidateMixin` (no arguments of its own; after the rest of `__init__` has run, calls
        `self.validate()` and raises `ValueError` if it returns a non-empty list of problems), and `Record(*, id, text)`. Then define
        `Note(TimestampMixin, ValidateMixin, Record)` whose `validate()` reports `"empty text"` and `"bad id"` (id must be a positive int).
        Add `to_dict()` on `Record` returning all instance attributes.""",
        code="""
        class TimestampMixin:
            pass

        class ValidateMixin:
            pass

        class Record:
            pass

        class Note(TimestampMixin, ValidateMixin, Record):
            pass
        """,
        tests="""
        n = Note(id=7, text="Call back", created_at=12.5)
        assert n.to_dict() == {"created_at": 12.5, "id": 7, "text": "Call back"}
        assert Note(id=1, text="x").created_at == 0.0
        try:
            Note(id=0, text=" ")
            assert False
        except ValueError as e:
            assert "empty text" in str(e) and "bad id" in str(e)
        assert [c.__name__ for c in Note.__mro__][:4] == ["Note", "TimestampMixin", "ValidateMixin", "Record"]
        """,
        hints=["Each `__init__` takes `**kwargs`, takes out its own arguments, and calls `super().__init__(**kwargs)`.",
               "`ValidateMixin.__init__` calls `super().__init__(**kwargs)` **first**, so the record's fields exist, then validates."],
        solution="""
        class TimestampMixin:
            def __init__(self, *, created_at=0.0, **kwargs):
                self.created_at = created_at
                super().__init__(**kwargs)

        class ValidateMixin:
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                problems = self.validate()
                if problems:
                    raise ValueError("; ".join(problems))

            def validate(self):
                return []

        class Record:
            def __init__(self, *, id, text):
                self.id = id
                self.text = text

            def to_dict(self):
                return dict(vars(self))

        class Note(TimestampMixin, ValidateMixin, Record):
            def validate(self):
                problems = []
                if not self.text.strip():
                    problems.append("empty text")
                if isinstance(self.id, bool) or not isinstance(self.id, int) or self.id <= 0:
                    problems.append("bad id")
                return problems
        """,
        why="""`Note(...)` runs `TimestampMixin.__init__` first (the start of the MRO), which takes `created_at` and passes the rest along; `ValidateMixin`
        passes everything on to `Record`, which sets the fields; control then returns to `ValidateMixin`, which can now validate a complete
        object. Each class handles only its own keyword arguments, and none of them needs to know which classes come next: that is
        cooperative multiple inheritance. `validate` is a hook with a harmless default, overridden by `Note`, and collecting all problems
        before raising gives a complete error message (7.2). Keyword-only arguments are essential here, since positional arguments cannot be
        safely forwarded through a chain whose order depends on the final class."""),
    predict("super() follows the instance's MRO", "medium",
        code="""
        class Logger:
            def log(self, msg):
                return [f"log:{msg}"]

        class Timestamped(Logger):
            def log(self, msg):
                return ["ts"] + super().log(msg)

        class Redacted(Logger):
            def log(self, msg):
                return ["redact"] + super().log(msg.replace("sk-123", "***"))

        class AppLogger(Redacted, Timestamped):
            pass

        print(AppLogger().log("key sk-123"))
        print(Timestamped().log("key sk-123"))
        print([c.__name__ for c in AppLogger.__mro__])
        """,
        hints=["For an `AppLogger`, the class after `Redacted` is `Timestamped`."],
        why="""`AppLogger` defines nothing, so `log` is found on `Redacted`, which redacts and calls `super().log`: the next class in `AppLogger`'s MRO is
        `Timestamped`, not `Logger`. `Timestamped` adds its marker and calls `super()`, which reaches `Logger`. A plain `Timestamped`
        instance never involves `Redacted`, so the key is not redacted there. Composing behaviours this way works only because every
        override calls `super()`."""),
)

section("hard", "Hard",
    write("Auto-registering plugins", "hard", tag="GenAI",
        prompt="""Write a base class `Tool` that registers every subclass in `Tool.registry` under a `name` given in the class line
        (`class Search(Tool, name="search")`). `__init_subclass__` must: require `name` (a `TypeError` is fine if missing), reject duplicates
        with `ValueError`, require subclasses to override `run` (raise `TypeError` at class creation if `run` is still the base's), and store
        `cls.name`. Add a class-level function `Tool.create(name, **config)` returning an instance of the registered class (`KeyError` for unknown
        names), where `__init__(self, **config)` stores `config`.""",
        code="""
        class Tool:
            pass
        """,
        tests="""
        class Search(Tool, name="search"):
            def run(self, query):
                return [f"{query} doc"] * self.config.get("k", 1)

        class Calculator(Tool, name="calc"):
            def run(self, expr):
                a, b = expr.split("+")
                return int(a) + int(b)

        assert sorted(Tool.registry) == ["calc", "search"] and Tool.registry["search"] is Search
        assert Tool.create("search", k=2).run("refund") == ["refund doc", "refund doc"]
        assert Tool.create("calc").run("2+3") == 5 and Search.name == "search"
        try:
            class Search2(Tool, name="search"):
                def run(self, q):
                    return q
            assert False
        except ValueError:
            pass
        try:
            class Lazy(Tool, name="lazy"):
                pass
            assert False
        except TypeError:
            pass
        assert "lazy" not in Tool.registry
        try:
            Tool.create("nope")
            assert False
        except KeyError:
            pass
        """,
        hints=["`def __init_subclass__(cls, *, name, **kwargs)`; call `super().__init_subclass__(**kwargs)` first.",
               "Compare `cls.run is Tool.run` to detect a missing override. Use `@classmethod` (9.6) or a `staticmethod` for `create`; a classmethod receives `cls`."],
        solution="""
        class Tool:
            registry = {}

            def __init_subclass__(cls, *, name, **kwargs):
                super().__init_subclass__(**kwargs)
                if name in Tool.registry:
                    raise ValueError(f"tool {name!r} is already registered by {Tool.registry[name].__name__}")
                if cls.run is Tool.run:
                    raise TypeError(f"{cls.__name__} must implement run()")
                cls.name = name
                Tool.registry[name] = cls

            def __init__(self, **config):
                self.config = config

            def run(self, *args, **kwargs):
                raise NotImplementedError

            @classmethod
            def create(cls, name, **config):
                return cls.registry[name](**config)
        """,
        why="""`__init_subclass__` runs when each `class` statement finishes, so registration and checks happen at import time, like the registration
        decorators of 8.4 but without a decorator line: subclassing **is** registering. Checking `cls.run is Tool.run` catches a subclass that
        forgot to implement the required method before any instance exists, earlier than the `NotImplementedError` approach, and the failed
        classes never enter the registry because the checks come before the assignment. The registry is a class attribute of the base on
        purpose: shared by all subclasses, which is the one case where a mutable class attribute is the design (always written as
        `Tool.registry`, never through `self`). `create` builds instances by name, the way configuration files select a component."""),
    fix("Read the code: a family of document loaders", "hard", tag="RAG",
        prompt="""`BaseLoader.load_all` loads many files and records each loaded path in `self.loaded`. `JsonLoader` and `TextLoader` share
        bugs: loaded paths from one loader appear in the other's list, `TextLoader` crashes because its base attributes are missing, and
        `JsonLoader.load` returns a different type from the base contract (a list of `Document`s, each a `(source, text)` tuple). Read it, find
        the bugs and fix them.""",
        code="""
        import json


        class BaseLoader:
            loaded = []

            def __init__(self, encoding="utf-8"):
                self.encoding = encoding

            def read(self, path, files):
                return files[path]

            def load(self, path, files):
                return [(path, self.read(path, files))]

            def load_all(self, paths, files):
                docs = []
                for p in paths:
                    docs.extend(self.load(p, files))
                    self.loaded.append(p)
                return docs


        class JsonLoader(BaseLoader):
            def load(self, path, files):
                data = json.loads(self.read(path, files))
                return "\\n".join(item["text"] for item in data)


        class TextLoader(BaseLoader):
            def __init__(self, strip=True):
                self.strip = strip

            def read(self, path, files):
                text = super().read(path, files)
                return text.strip() if self.strip else text
        """,
        tests="""
        files = {"a.json": '[{"text": "Refunds take 5 days"}, {"text": "Contact support"}]', "b.txt": "  Reset your password  "}
        jl, tl = JsonLoader(), TextLoader()
        assert jl.load_all(["a.json"], files) == [("a.json", "Refunds take 5 days"), ("a.json", "Contact support")]
        assert tl.load_all(["b.txt"], files) == [("b.txt", "Reset your password")]
        assert jl.loaded == ["a.json"] and tl.loaded == ["b.txt"]
        assert tl.encoding == "utf-8" and TextLoader(strip=False).load("b.txt", files) == [("b.txt", "  Reset your password  ")]
        """,
        hints=["`loaded = []` is a mutable class attribute shared by every loader instance.",
               "`TextLoader.__init__` must call `super().__init__()`, ideally passing `encoding` through.",
               "`JsonLoader.load` must return a list of `(source, text)` tuples, like the base."],
        solution="""
        import json


        class BaseLoader:
            def __init__(self, encoding="utf-8"):
                self.encoding = encoding
                self.loaded = []

            def read(self, path, files):
                return files[path]

            def load(self, path, files):
                return [(path, self.read(path, files))]

            def load_all(self, paths, files):
                docs = []
                for p in paths:
                    docs.extend(self.load(p, files))
                    self.loaded.append(p)
                return docs


        class JsonLoader(BaseLoader):
            def load(self, path, files):
                data = json.loads(self.read(path, files))
                return [(path, item["text"]) for item in data]


        class TextLoader(BaseLoader):
            def __init__(self, strip=True, encoding="utf-8"):
                super().__init__(encoding)
                self.strip = strip

            def read(self, path, files):
                text = super().read(path, files)
                return text.strip() if self.strip else text
        """,
        why="""Three bugs, all about the base-subclass relationship. `loaded = []` on the base class was one list shared by **every** loader of every
        subclass (9.1), so each loader's history included the others'; it belongs in `__init__`. `TextLoader.__init__` replaced the base's
        without calling it, so `encoding` (and, after the first fix, `loaded`) never existed; calling `super().__init__(encoding)` and
        accepting `encoding` as a parameter keeps the subclass substitutable. And `JsonLoader.load` returned a joined string where the base
        contract promises a list of documents: `load_all` then extended the result list with individual **characters**, a silent corruption
        that a substitution check catches immediately. Returning one `(source, text)` tuple per JSON item honours the contract and keeps
        each item a separate document for retrieval."""),
    write("Extend a method with caching", "hard", tag="RAG",
        prompt="""Given the base class `Retriever` (provided in the starter), write a subclass `CachingRetriever(docs, max_entries=128)` that
        overrides `retrieve(query, k)` to return cached results for repeated `(normalised query, k)` pairs (normalise: lower-case, collapse
        spaces), calling `super().retrieve` only on a miss, evicting the oldest entry when full, and returning a **copy** of the cached list.
        Track `self.hits` and `self.misses`. Adding documents with the base's `add(doc)` must clear the cache (override `add` and call
        `super().add`).""",
        code="""
        class Retriever:
            def __init__(self, docs):
                self.docs = list(docs)
                self.searches = 0

            def add(self, doc):
                self.docs.append(doc)

            def retrieve(self, query, k=2):
                self.searches += 1
                words = set(query.lower().split())
                scored = [(len(words & set(d.lower().split())), d) for d in self.docs]
                return [d for s, d in sorted(scored, key=lambda p: -p[0]) if s > 0][:k]


        class CachingRetriever(Retriever):
            pass
        """,
        tests="""
        r = CachingRetriever(["Refund policy", "Refund window 30 days", "Reset password"], max_entries=2)
        first = r.retrieve("refund  WINDOW")
        assert first == ["Refund window 30 days", "Refund policy"]
        first.append("junk")
        assert r.retrieve("Refund window") == ["Refund window 30 days", "Refund policy"]
        assert (r.hits, r.misses, r.searches) == (1, 1, 1)
        r.retrieve("reset"); r.retrieve("policy")
        assert r.misses == 3 and r.searches == 3
        r.retrieve("refund window")
        assert r.misses == 4
        r.add("Refund window extended to 60 days")
        assert "Refund window extended to 60 days" in r.retrieve("refund window", k=3)
        assert isinstance(r, Retriever) and r.searches == 5
        """,
        hints=["Call `super().__init__(docs)` first, then set up the cache dict and counters.",
               "In `retrieve`, build the key, check the cache, else `result = super().retrieve(query, k)`, store it, and return `list(...)`."],
        solution="""
        class Retriever:
            def __init__(self, docs):
                self.docs = list(docs)
                self.searches = 0

            def add(self, doc):
                self.docs.append(doc)

            def retrieve(self, query, k=2):
                self.searches += 1
                words = set(query.lower().split())
                scored = [(len(words & set(d.lower().split())), d) for d in self.docs]
                return [d for s, d in sorted(scored, key=lambda p: -p[0]) if s > 0][:k]


        class CachingRetriever(Retriever):
            def __init__(self, docs, max_entries=128):
                super().__init__(docs)
                self.max_entries = max_entries
                self._cache = {}
                self.hits = 0
                self.misses = 0

            def retrieve(self, query, k=2):
                key = (" ".join(query.lower().split()), k)
                if key in self._cache:
                    self.hits += 1
                    return list(self._cache[key])
                self.misses += 1
                result = super().retrieve(query, k)
                if len(self._cache) >= self.max_entries:
                    del self._cache[next(iter(self._cache))]
                self._cache[key] = list(result)
                return list(result)

            def add(self, doc):
                super().add(doc)
                self._cache.clear()
        """,
        why="""The subclass extends two methods with `super()`: `retrieve` adds a cache around the base's search, and `add` adds invalidation after the
        base's update, so a new document is visible immediately. Because it overrides methods with the same signatures and results, a
        `CachingRetriever` can replace a `Retriever` anywhere. Copies on the way in and out protect the cache from callers modifying lists
        (the `junk` test). The counters show the cache working: only misses reach `super().retrieve`, which increments the base's
        `searches`. The same behaviour could be built by composition, a `CachedRetriever` that **holds** any retriever and wraps it, which
        works for every retriever class at once; 9.5 compares the two."""),
    predict("Calling an override from the base initialiser", "hard",
        code="""
        class Base:
            def __init__(self):
                print("Base init, describe() ->", self.describe())

            def describe(self):
                return "base"

        class Child(Base):
            def __init__(self, label):
                super().__init__()
                self.label = label

            def describe(self):
                return f"child {getattr(self, 'label', '<label not set yet>')}"

        c = Child("x")
        print(c.describe())

        class Config:
            defaults = {"model": "small"}

        class Prod(Config):
            defaults = {**Config.defaults, "model": "large"}

        print(Config.defaults, Prod.defaults, Prod().defaults is Prod.defaults)
        """,
        hints=["Inside `Base.__init__`, `self` is already a `Child`, so `self.describe()` runs `Child.describe`, before `label` exists."],
        why="""During `Base.__init__`, the object is already an instance of `Child`, so the call `self.describe()` dispatches to the override, which runs
        before `Child.__init__` has set `label`: the `getattr` default shows the gap. Calling overridable methods from a base initialiser
        is a classic trap; with a plain `self.label` the code would crash with `AttributeError`. The second part shows the safe way to
        specialise a class attribute: build a **new** dict in the subclass (`{**Config.defaults, ...}`) instead of mutating the base's."""),
)

section("interview", "Interview questions",
    explain("What does `super()` do, and what is the MRO?", "medium", tag="Interview",
        why="""The method resolution order is the sequence of classes Python searches for an attribute: the class itself, then its bases in an order
        computed by the C3 linearisation algorithm, ending with `object`; `Class.__mro__` shows it. C3 guarantees each class comes before its
        bases, the written order of bases is respected, and each class appears once. `super().method()` calls the version of `method` in
        the **next** class after the current one in the MRO of the instance's actual class, not necessarily the current class's parent. With
        single inheritance those are the same; with multiple inheritance, it lets every class in a diamond run exactly once in a defined
        order, provided every method calls `super()` and passes along arguments it does not use, usually via keyword arguments. The most
        common use is extending `__init__`: a subclass that defines `__init__` must call `super().__init__(...)`, or the base's setup never
        runs."""),
    explain("Inheritance versus composition: when do you use each?", "medium", tag="Interview",
        why="""Inheritance models "is a": the subclass promises the whole interface of the base and can be substituted for it everywhere, reusing its
        code and overriding parts. It fits exception hierarchies, framework base classes designed for extension (template methods with
        documented hooks) and small mixins. Its cost is tight coupling: subclasses depend on the base's internals, deep hierarchies obscure where
        behaviour comes from, and violating the base's contract breaks code that uses the base. Composition models "has a" or "uses a": an
        object holds another and delegates to it, so components can be swapped at run time, tested separately with fakes, and combined
        freely (a retriever wrapped by a cache, a client with a retry policy). Prefer composition by default, and inherit when there is a
        genuine substitutable relationship or a framework requires it. Overriding methods to disable them is a sign inheritance was wrong."""),
    explain("Design a class hierarchy for supporting several LLM providers. What pitfalls would you avoid?", "hard", tag="Interview",
        why="""Define a small base contract (an abstract base class or a protocol, 9.5) with one public method such as `complete(messages, **params)`
        returning a provider-neutral response object, and put shared behaviour in the base: input validation, retries and timeouts, usage
        accounting, tracing. Each provider subclass implements one protected hook that translates to its API and back, and maps its SDK's
        errors into your exception hierarchy (7.2). Register providers by name (`__init_subclass__` or a decorator) so configuration can pick
        one. Pitfalls: subclasses that change the public method's signature or return provider-specific types, which breaks substitutability;
        forgetting `super().__init__`; mutable class attributes shared across providers; deep hierarchies built per model version instead of
        configuration; putting provider-specific features in the base. Often composition is better for cross-cutting features (wrap any
        provider with a caching or fallback layer) than adding them as subclasses, so the hierarchy stays one level deep."""),
)

recap(
    "`class Child(Base)` inherits everything; lookup searches instance, class, then bases (the MRO). Overrides win because the subclass is searched first.",
    "Template method: the base defines the algorithm and calls hooks (`self.score`); subclasses override only the hooks.",
    "A subclass `__init__` must call `super().__init__(...)`. `super()` calls the next class in the instance's MRO, which makes cooperative multiple inheritance work.",
    "Honour the base contract (same arguments, same kind of result): substitutability is the point of inheritance.",
    "Mixins and `__init_subclass__` are the specialised tools; subclass `UserDict` rather than `dict`; prefer composition when there is no real \"is a\".",
)
