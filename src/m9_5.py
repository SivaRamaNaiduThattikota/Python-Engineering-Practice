from lesson import *

lesson(
    id="m9-5", num="9.5", title="Composition and protocols",
    intro="Building objects from other objects instead of inheriting from them. Composition and delegation, passing "
          "collaborators in (dependency injection) so code is testable, duck typing, abstract base classes that enforce an "
          "interface, `collections.abc` mixins, and `typing.Protocol` for structural interfaces. Applied to one interface "
          "for many LLM providers, wrappers that add caching and fallbacks, and RAG pipelines with swappable parts.",
    desc="Duck typing, ABCs, protocols, one interface for many LLM providers.",
    keys="composition delegation has a dependency injection fake test double duck typing abstract base class abc abstractmethod collections.abc mapping iterable protocol typing.protocol runtime_checkable structural typing strategy wrapper proxy __getattr__ interface",
)

term("Composition", "Building an object that holds other objects and delegates work to them (\"has a\"), instead of inheriting from them (\"is a\").")
term("Dependency injection", "Passing the objects a class depends on (a client, a clock, a store) into it, instead of creating them inside, so they can be swapped and faked in tests.")
term("Duck typing", "Using an object because it has the methods you need, whatever its class: \"if it walks like a duck and quacks like a duck\".")
term("Protocol", "A `typing.Protocol` class that describes an interface by its methods; any class with those methods matches, without inheriting from it.")

section("compose", "Composition: has a, uses a",
    p("""With **composition**, an object holds other objects as attributes and calls them to do parts of its work. A chat session **has a**
    client; a cached retriever **uses a** retriever; a RAG pipeline **has** an embedder, a vector store and a model. Instead of inheriting
    behaviour, the outer object **delegates**: its method calls the inner object's method and adds something around it. The inner object
    can be anything with the right methods, so one wrapper works for every implementation, and the parts can be swapped at run time."""),
    ex("""
    class KeywordRetriever:
        def __init__(self, docs):
            self.docs = docs
        def retrieve(self, query, k=2):
            words = set(query.lower().split())
            hits = [d for d in self.docs if words & set(d.lower().split())]
            return hits[:k]

    class CachedRetriever:
        \"\"\"Adds caching to ANY object with a retrieve(query, k) method.\"\"\"
        def __init__(self, inner):
            self.inner = inner
            self._cache = {}
            self.hits = 0

        def retrieve(self, query, k=2):
            key = (query.lower().strip(), k)
            if key in self._cache:
                self.hits += 1
            else:
                self._cache[key] = self.inner.retrieve(query, k)   # delegate on a miss
            return list(self._cache[key])

    docs = ["Refund policy", "Refund window", "Reset password"]
    r = CachedRetriever(KeywordRetriever(docs))
    print(r.retrieve("refund"), r.retrieve("Refund "), r.hits)
    """, "composition.py"),
    p("""Compare this with the caching **subclass** of 9.4: the subclass works only for the one retriever class it extends, while the wrapper
    works for a keyword retriever, a vector retriever or a hybrid one, including classes written later, and it can wrap another wrapper
    (`CachedRetriever(FallbackRetriever(...))`). Composition also keeps each class small and focused, and its dependencies visible in
    `__init__`. Its cost is a little forwarding code, and the wrapper only exposes the methods it chooses to."""),
)

section("di", "Dependency injection: pass collaborators in",
    p("""A class that **creates** its collaborators inside, `self.client = OpenAIClient()` or `time.time()` in a method, is welded to them: you
    cannot test it without calling the real API, and you cannot switch provider without editing it. **Dependency injection** means passing
    collaborators in, usually through `__init__`: `ChatService(client, clock)`. Production code passes the real client and `time.monotonic`;
    tests pass a **fake**, a tiny object with the same methods that returns canned answers, records calls, or raises on demand. You have
    used this idea since 7.3 with injected `clock`, `sleep` and `rng`; here it is applied to whole objects (problem 14)."""),
    ex("""
    class FakeClient:
        def __init__(self, replies):
            self.replies = list(replies)
            self.prompts = []
        def complete(self, prompt):
            self.prompts.append(prompt)
            reply = self.replies.pop(0)
            if isinstance(reply, Exception):
                raise reply
            return reply

    class Summariser:
        def __init__(self, client, max_words=5):
            self.client = client                 # injected: real or fake
            self.max_words = max_words
        def summarise(self, text):
            reply = self.client.complete(f"Summarise in {self.max_words} words: {text}")
            return " ".join(reply.split()[: self.max_words])

    fake = FakeClient(["Refunds take five business days usually", TimeoutError("slow")])
    s = Summariser(fake)
    print(s.summarise("long refund policy text"), "|", fake.prompts[0][:25])
    try:
        s.summarise("again")
    except TimeoutError:
        print("timeout path tested without a network")
    """, "injection.py"),
    p("""Notice that `FakeClient` does not inherit from any client class. `Summariser` only ever calls `client.complete(prompt)`, so any object
    with that method works: that is **duck typing**, the next section. Injection pays off three times: tests are fast and deterministic, the
    failure paths can be exercised on purpose, and swapping implementations is a configuration change at the place where objects are
    created (often a small "composition root" function or the app's start-up code)."""),
)

section("duck", "Duck typing",
    p("""Python does not check types when you call a method: `obj.read()` works if `obj` has a `read` method, whatever its class. **Duck
    typing** designs code around that: a function that needs "something with `read()`" accepts files, `io.StringIO` objects, network
    streams and fakes alike. Built-in functions work the same way: `sum`, `sorted` and `for` accept any iterable, `len` anything with
    `__len__` (9.2). Checking `isinstance(x, list)` before using `x` throws that flexibility away: it rejects tuples, generators,
    NumPy arrays and every custom sequence that would have worked (problem 10)."""),
    ex("""
    import io

    def count_lines(source):
        return sum(1 for line in source if line.strip())   # needs only iteration over lines

    class FakeStream:
        def __iter__(self):
            yield "refund\\n"
            yield "\\n"
            yield "reset\\n"

    print(count_lines(io.StringIO("a\\n\\nb\\nc\\n")), count_lines(["x", " ", "y"]), count_lines(FakeStream()))

    def describe(model):
        try:
            name = model.name
        except AttributeError:
            name = type(model).__name__
        return f"model {name}"

    class Small:
        name = "small"
    print(describe(Small()), describe(object()))
    """, "duck_typing.py"),
    p("""The price of duck typing is that mistakes surface at run time, when a missing method is finally called, and that the expected
    interface is implicit. The next two tools make the interface explicit: abstract base classes enforce it at instantiation, and
    protocols let type checkers verify it before the program runs."""),
)

section("abc", "Abstract base classes",
    p("""An **abstract base class** (ABC) declares an interface that subclasses must implement. Inherit from `abc.ABC` and mark the required
    methods with `@abstractmethod`. Python then refuses to **instantiate** any class that still has unimplemented abstract methods, with a
    `TypeError` naming them, which is earlier and clearer than a `NotImplementedError` raised on first use (9.4). Abstract methods can
    contain a default implementation that subclasses call with `super()`, and the ABC can provide ordinary concrete methods built on the
    abstract ones."""),
    ex("""
    from abc import ABC, abstractmethod

    class LLMProvider(ABC):
        def __init__(self, model):
            self.model = model

        @abstractmethod
        def _complete(self, prompt):
            \"\"\"Return the model's text for one prompt.\"\"\"

        def complete(self, prompt):                    # concrete method built on the abstract one
            if not prompt.strip():
                raise ValueError("empty prompt")
            return {"model": self.model, "text": self._complete(prompt).strip()}

    class Echo(LLMProvider):
        def _complete(self, prompt):
            return prompt

    class Forgetful(LLMProvider):
        pass

    print(Echo("echo-1").complete(" hi "))
    for cls in (LLMProvider, Forgetful):
        try:
            cls("x")
        except TypeError as e:
            print("TypeError:", e)
    """, "abc.py"),
    p("""The standard library's **`collections.abc`** module defines ABCs for Python's protocols: `Iterable`, `Sequence`, `Mapping`,
    `MutableMapping`, `Callable` and more. They serve two purposes. `isinstance(x, Iterable)` checks for the protocol rather than a
    specific type. And subclassing one gives you **mixin methods**: inherit `collections.abc.Mapping`, implement just `__getitem__`,
    `__iter__` and `__len__`, and you get `keys`, `items`, `values`, `get`, `__contains__` and `__eq__` for free, all consistent with
    your three methods (problem 7)."""),
    ex("""
    from collections.abc import Mapping, Iterable, Sequence

    class Settings(Mapping):
        def __init__(self, raw):
            self._data = {k.lower(): v for k, v in raw.items()}
        def __getitem__(self, key):
            return self._data[key.lower()]
        def __iter__(self):
            return iter(self._data)
        def __len__(self):
            return len(self._data)

    s = Settings({"MODEL": "small", "Temperature": 0.2})
    print(s["model"], s.get("TOP_P", 1.0), "temperature" in s, sorted(s.items()), dict(s) == {"model": "small", "temperature": 0.2})
    print(isinstance([1], Iterable), isinstance((x for x in []), Sequence), isinstance("ab", Sequence), isinstance(s, Mapping))
    """, "collections_abc.py"),
)

section("protocol", "Protocols: interfaces without inheritance",
    p("""ABCs are **nominal**: a class matches only if it inherits from the ABC (or is explicitly registered). Duck typing is **structural**:
    anything with the right methods matches. **`typing.Protocol`** brings structural typing to type hints. You describe the interface as a
    class whose methods have bodies of `...`, and any class with matching methods counts as implementing it, without importing or
    inheriting from it. Type checkers such as mypy and pyright (11.1) then verify, before the program runs, that what you pass has those
    methods with compatible signatures. Decorating the protocol with `@runtime_checkable` also allows `isinstance` checks, which test only
    that the methods **exist**, not their signatures."""),
    ex("""
    from typing import Protocol, runtime_checkable

    @runtime_checkable
    class Embedder(Protocol):
        def embed(self, texts: list[str]) -> list[list[float]]:
            ...

    class LengthEmbedder:                         # no inheritance at all
        def embed(self, texts):
            return [[float(len(t)), float(t.count(" "))] for t in texts]

    class NotAnEmbedder:
        def encode(self, texts):
            return []

    def nearest(embedder: Embedder, query: str, docs: list[str]) -> str:
        q, *vectors = embedder.embed([query, *docs])
        distance = lambda v: sum((a - b) ** 2 for a, b in zip(q, v))
        return min(zip(docs, vectors), key=lambda pair: distance(pair[1]))[0]

    print(nearest(LengthEmbedder(), "refund window", ["refund policy", "reset password now", "hi"]))
    print(isinstance(LengthEmbedder(), Embedder), isinstance(NotAnEmbedder(), Embedder))
    """, "protocols.py"),
    p("""Protocols fit code you do not control: your function can require "an embedder" and accept a class from any library that happens to
    have `embed`, without that library knowing about your protocol. ABCs fit hierarchies you own, where you want shared concrete methods and
    instantiation-time checks. Many projects use both: an ABC as the base for their own implementations, and a protocol in the type hints of
    the code that consumes them."""),
)

section("delegate", "Wrappers, strategies and delegation",
    p("""Composition gives you a handful of patterns that cover most designs. A **wrapper** (or decorator object) has the same interface as
    what it wraps and adds behaviour: caching, retries, fallbacks, logging, rate limiting, each a small class, stacked like decorators in
    8.2. A **strategy** is a swappable part: a pipeline holds a `chunker`, a `retriever` and a `reranker`, each chosen by configuration. Plain
    functions are often the simplest strategy (`key=`, `score=`), and classes take over when the strategy has state or settings."""),
    p("""When a wrapper should forward **everything** it does not handle itself, `__getattr__` helps: Python calls `obj.__getattr__(name)` only
    when normal lookup **fails**, so a proxy can define the few methods it changes and forward the rest with `return getattr(self._inner,
    name)` (problem 15). Use it sparingly: forwarded attributes are invisible to IDEs and type checkers, typos turn into confusing errors
    from the inner object, and every forwarded access is slower than a normal one (problem 8)."""),
    ex("""
    class FallbackProvider:
        def __init__(self, *providers, on=(TimeoutError, ConnectionError)):
            self.providers = providers
            self.on = on
            self.last_used = None

        def complete(self, prompt):
            last_error = None
            for p in self.providers:
                try:
                    result = p.complete(prompt)
                except self.on as e:
                    last_error = e
                    continue
                self.last_used = type(p).__name__
                return result
            raise last_error

    class Down:
        def complete(self, prompt):
            raise TimeoutError("primary timed out")

    class Up:
        def complete(self, prompt):
            return f"answer to {prompt}"

    fp = FallbackProvider(Down(), Up())
    print(fp.complete("refund?"), fp.last_used)
    """, "wrappers.py"),
)

section("warmup", "Warm-up",
    predict("Abstract classes refuse to be instantiated", "easy",
        code="""
        from abc import ABC, abstractmethod

        class Store(ABC):
            @abstractmethod
            def get(self, key): ...

            @abstractmethod
            def put(self, key, value): ...

            def get_or(self, key, default):
                try:
                    return self.get(key)
                except KeyError:
                    return default

        class Half(Store):
            def get(self, key):
                return {"a": 1}[key]

        class Full(Half):
            def put(self, key, value):
                pass

        for cls in (Store, Half, Full):
            try:
                obj = cls()
                print(cls.__name__, "ok", obj.get_or("z", 0), obj.get_or("a", 0))
            except TypeError as e:
                print(cls.__name__, "TypeError")
        print(sorted(Half.__abstractmethods__), sorted(Full.__abstractmethods__))
        """,
        hints=["A class is instantiable only when every abstract method has an implementation, inherited ones included."],
        why="""`Store` has two abstract methods and `Half` implements only one, so both refuse instantiation. `Full` inherits `get` from `Half` and adds
        `put`, so nothing abstract remains, and the concrete `get_or` from the ABC works on top of it. `__abstractmethods__` lists what is still
        missing for each class."""),
    write("A cache wrapper for any retriever", "easy", tag="RAG",
        prompt="""Write `CachedRetriever(inner, max_entries=256)` that wraps **any** object with a `retrieve(query, k)` method. It caches results by
        `(query, k)`, returns a copy of the cached list, evicts the oldest entry when full, counts `hits` and `misses`, and exposes `clear()`.
        Do not inherit from anything.""",
        code="""
        class CachedRetriever:
            pass
        """,
        tests="""
        class Counting:
            def __init__(self):
                self.calls = 0
            def retrieve(self, query, k):
                self.calls += 1
                return [f"{query}-{i}" for i in range(k)]

        inner = Counting()
        r = CachedRetriever(inner, max_entries=2)
        a = r.retrieve("refund", 2)
        a.append("junk")
        assert r.retrieve("refund", 2) == ["refund-0", "refund-1"] and inner.calls == 1 and (r.hits, r.misses) == (1, 1)
        r.retrieve("reset", 1); r.retrieve("x", 1)
        r.retrieve("refund", 2)
        assert inner.calls == 4 and r.misses == 4
        r.clear()
        r.retrieve("x", 1)
        assert inner.calls == 5
        assert CachedRetriever(CachedRetriever(Counting())).retrieve("q", 1) == ["q-0"]
        """,
        hints=["Store the inner object in `__init__` and call `self.inner.retrieve(query, k)` only on a miss."],
        solution="""
        class CachedRetriever:
            def __init__(self, inner, max_entries=256):
                self.inner = inner
                self.max_entries = max_entries
                self._cache = {}
                self.hits = 0
                self.misses = 0

            def retrieve(self, query, k):
                key = (query, k)
                if key in self._cache:
                    self.hits += 1
                else:
                    self.misses += 1
                    if len(self._cache) >= self.max_entries:
                        del self._cache[next(iter(self._cache))]
                    self._cache[key] = list(self.inner.retrieve(query, k))
                return list(self._cache[key])

            def clear(self):
                self._cache.clear()
        """,
        why="""The wrapper depends only on the inner object's `retrieve` method, so it works with every retriever, including another `CachedRetriever` (the
        last test), which is what makes wrappers composable like decorators. Eviction removes the oldest key, the first in a dict's insertion
        order (8.3). Copies in and out protect the cache from callers changing lists. Because nothing is inherited, the wrapper's behaviour is
        entirely visible in this class: no inherited methods it might accidentally expose."""),
    fix("A provider that cannot be created", "easy", tag="GenAI",
        prompt="""`MockProvider` should be usable in tests, but `MockProvider()` raises `TypeError: Can't instantiate abstract class`. Implement what
        is missing so that `complete` returns the configured reply for every prompt and records the prompts.""",
        code="""
        from abc import ABC, abstractmethod

        class Provider(ABC):
            @abstractmethod
            def _complete(self, prompt): ...

            @abstractmethod
            def count_tokens(self, text): ...

            def complete(self, prompt):
                return {"text": self._complete(prompt), "tokens": self.count_tokens(prompt)}

        class MockProvider(Provider):
            def __init__(self, reply="ok"):
                self.reply = reply
                self.prompts = []

            def _complete(self, prompt):
                self.prompts.append(prompt)
                return self.reply
        """,
        tests="""
        m = MockProvider("refund in 5 days")
        assert m.complete("refund window?") == {"text": "refund in 5 days", "tokens": 2}
        assert m.prompts == ["refund window?"] and isinstance(m, Provider)
        assert MockProvider().complete("a b c")["tokens"] == 3
        """,
        hints=["Every abstract method must be implemented before instantiation works. `count_tokens` can count words."],
        solution="""
        from abc import ABC, abstractmethod

        class Provider(ABC):
            @abstractmethod
            def _complete(self, prompt): ...

            @abstractmethod
            def count_tokens(self, text): ...

            def complete(self, prompt):
                return {"text": self._complete(prompt), "tokens": self.count_tokens(prompt)}

        class MockProvider(Provider):
            def __init__(self, reply="ok"):
                self.reply = reply
                self.prompts = []

            def _complete(self, prompt):
                self.prompts.append(prompt)
                return self.reply

            def count_tokens(self, text):
                return len(text.split())
        """,
        why="""The ABC listed two required methods and the subclass implemented one, so Python refused to create it, naming `count_tokens`: the
        interface is enforced at the moment an object would exist, not when the missing method is first called deep inside some code path.
        Implementing it makes the mock a complete `Provider`, so it can stand in for a real one anywhere the base type is expected. Fakes that
        implement the full interface are the safest kind of test double."""),
    predict("Duck typing and runtime protocols", "easy",
        code="""
        from typing import Protocol, runtime_checkable

        @runtime_checkable
        class Closeable(Protocol):
            def close(self) -> None: ...

        class File:
            def close(self):
                return "closed file"

        class Conn:
            def close(self, force):
                return "closed conn"

        class Nothing:
            pass

        print([isinstance(x, Closeable) for x in (File(), Conn(), Nothing())])

        def shutdown(items):
            out = []
            for item in items:
                try:
                    out.append(item.close())
                except AttributeError:
                    out.append("skipped")
                except TypeError:
                    out.append("bad signature")
            return out

        print(shutdown([File(), Nothing(), Conn()]))
        """,
        hints=["A runtime `isinstance` check against a protocol only checks that the methods exist, not their signatures."],
        why="""`isinstance` with a runtime-checkable protocol looks only for an attribute named `close`, so `Conn` passes even though its `close` needs an
        argument; a static type checker would flag that mismatch. The duck-typed loop simply tries: objects without `close` raise
        `AttributeError`, and calling `Conn.close()` without `force` raises `TypeError`."""),
)

section("medium", "Medium",
    write("A fallback provider", "medium", tag="GenAI",
        prompt="""Write `FallbackProvider(*providers, on=(TimeoutError, ConnectionError))` that has the same `complete(prompt)` interface as the
        providers it holds. It tries them in order, moving on only for exceptions in `on`; records `self.used` (a list of the class names that
        answered, one per call) and `self.failures` (a `collections.Counter` of exception type names); and if all fail, raises the last error
        with a note listing the providers tried. Other exceptions propagate immediately.""",
        code="""
        from collections import Counter

        class FallbackProvider:
            pass
        """,
        tests="""
        class Slow:
            def complete(self, prompt):
                raise TimeoutError("slow")

        class Offline:
            def complete(self, prompt):
                raise ConnectionError("offline")

        class Good:
            def complete(self, prompt):
                return f"good: {prompt}"

        class Buggy:
            def complete(self, prompt):
                raise KeyError("bug")

        fp = FallbackProvider(Slow(), Offline(), Good())
        assert fp.complete("hi") == "good: hi" and fp.complete("again") == "good: again"
        assert fp.used == ["Good", "Good"] and fp.failures == Counter({"TimeoutError": 2, "ConnectionError": 2})
        try:
            FallbackProvider(Slow(), Offline()).complete("x")
            assert False
        except ConnectionError as e:
            assert e.__notes__ == ["tried: Slow, Offline"]
        try:
            FallbackProvider(Buggy(), Good()).complete("x")
            assert False
        except KeyError:
            pass
        """,
        hints=["Loop over `self.providers`; on an `on` exception, count it and `continue`; on success, record and return."],
        solution="""
        from collections import Counter

        class FallbackProvider:
            def __init__(self, *providers, on=(TimeoutError, ConnectionError)):
                if not providers:
                    raise ValueError("at least one provider is required")
                self.providers = providers
                self.on = on
                self.used = []
                self.failures = Counter()

            def complete(self, prompt):
                last_error = None
                for p in self.providers:
                    try:
                        result = p.complete(prompt)
                    except self.on as e:
                        self.failures[type(e).__name__] += 1
                        last_error = e
                        continue
                    self.used.append(type(p).__name__)
                    return result
                last_error.add_note("tried: " + ", ".join(type(p).__name__ for p in self.providers))
                raise last_error
        """,
        why="""Because `FallbackProvider` exposes the same `complete` method as what it holds, callers cannot tell it apart from a single provider,
        and it can itself be wrapped (by a cache, by another fallback): composition of objects with one shared interface. The failure counter
        turns degradation into data: a dashboard showing many `TimeoutError`s for the primary tells you it is struggling before users notice.
        Only the listed transient errors trigger the fallback; a `KeyError` is a bug and propagates at once (7.3). The note on the final error
        records the whole path without changing its type."""),
    fix("A stack that exposes too much", "medium", tag="Data work",
        prompt="""`UndoStack` must only allow `push`, `pop`, `peek`, `len` and truthiness. Because it inherits from `list`, callers can `insert`,
        `sort` or index into it and break the undo order. Rewrite it with composition: hold a list internally and expose only the allowed
        operations (`pop` and `peek` on an empty stack raise `IndexError("undo stack is empty")`).""",
        code="""
        class UndoStack(list):
            def push(self, action):
                self.append(action)

            def peek(self):
                return self[-1]
        """,
        tests="""
        s = UndoStack()
        s.push("type a"); s.push("type b")
        assert len(s) == 2 and s.peek() == "type b" and s.pop() == "type b" and bool(s)
        for name in ["insert", "sort", "append", "__getitem__", "extend"]:
            assert not hasattr(s, name), name
        s.pop()
        assert not s
        for op in (s.pop, s.peek):
            try:
                op()
                assert False
            except IndexError as e:
                assert str(e) == "undo stack is empty"
        """,
        hints=["Store `self._items = []` and write the five operations as methods that use it."],
        solution="""
        class UndoStack:
            def __init__(self):
                self._items = []

            def push(self, action):
                self._items.append(action)

            def pop(self):
                if not self._items:
                    raise IndexError("undo stack is empty")
                return self._items.pop()

            def peek(self):
                if not self._items:
                    raise IndexError("undo stack is empty")
                return self._items[-1]

            def __len__(self):
                return len(self._items)
        """,
        why="""Inheriting from `list` made the stack promise the whole list interface: `insert`, `sort`, slicing, `del s[0]`, any of which destroys the
        undo order. A stack is not a list; it **uses** one. Composition exposes exactly the five operations the stack should have, so its rule
        ("last in, first out") cannot be broken from outside, and the error message can speak the stack's language. `__len__` gives both
        `len(s)` and truthiness (9.2). This is the substitution test from 9.4 applied in reverse: if the subclass would have to disable base
        methods, use composition."""),
    write("A read-only config view with collections.abc", "medium", tag="GenAI",
        prompt="""Write `EnvConfig(environ, prefix)` as a subclass of `collections.abc.Mapping` that presents only the entries of `environ` (a dict)
        whose keys start with `prefix`, with the prefix removed and the rest lower-cased (`"APP_MODEL"` becomes `"model"` for prefix `"APP_"`).
        Implement only `__getitem__`, `__iter__` and `__len__`; `get`, `in`, `keys` and `items` must then work. It is a **live view**: later
        changes to `environ` are visible. Add a `__repr__` like `EnvConfig(prefix='APP_', keys=['model', 'timeout'])`.""",
        code="""
        from collections.abc import Mapping

        class EnvConfig(Mapping):
            pass
        """,
        tests="""
        env = {"APP_MODEL": "small", "APP_TIMEOUT": "30", "HOME": "/root", "APPLE": "x"}
        cfg = EnvConfig(env, "APP_")
        assert cfg["model"] == "small" and cfg.get("timeout") == "30" and cfg.get("missing", "d") == "d"
        assert "model" in cfg and "home" not in cfg and len(cfg) == 2 and sorted(cfg) == ["model", "timeout"]
        assert dict(cfg.items()) == {"model": "small", "timeout": "30"}
        env["APP_TEMPERATURE"] = "0.2"
        assert cfg["temperature"] == "0.2" and len(cfg) == 3
        assert repr(cfg) == "EnvConfig(prefix='APP_', keys=['model', 'temperature', 'timeout'])"
        try:
            cfg["apple"]
            assert False
        except KeyError:
            pass
        """,
        hints=["`__getitem__(key)` looks up `environ[prefix + key.upper()]`; `__iter__` yields matching keys with the prefix cut and lower-cased."],
        solution="""
        from collections.abc import Mapping

        class EnvConfig(Mapping):
            def __init__(self, environ, prefix):
                self._environ = environ
                self._prefix = prefix

            def __getitem__(self, key):
                return self._environ[self._prefix + key.upper()]

            def __iter__(self):
                for k in self._environ:
                    if k.startswith(self._prefix):
                        yield k[len(self._prefix):].lower()

            def __len__(self):
                return sum(1 for _ in self)

            def __repr__(self):
                return f"EnvConfig(prefix={self._prefix!r}, keys={sorted(self)})"
        """,
        why="""`Mapping` builds `get`, `__contains__`, `keys`, `items`, `values` and `__eq__` from the three methods, all consistent with them: `get`
        catches the `KeyError` from `__getitem__`, `in` uses `__getitem__` too, and `items` pairs `__iter__` with `__getitem__`. Writing just the
        three core methods is less code and fewer chances for inconsistency than implementing all of them by hand. Holding a reference to
        `environ` rather than a copy makes it a live view, like dict views (4.5); pass `os.environ` in production and a plain dict in tests,
        which is dependency injection again. Being a `Mapping` (not a `MutableMapping`) also documents that configuration is read-only here."""),
    choose("Explicit forwarding or __getattr__", "medium",
        prompt="Both proxies forward `retrieve` to an inner object; the code calls it 200,000 times. Which is faster?",
        setup="""class Inner:
    def retrieve(self, q):
        return q

class Explicit:
    def __init__(self, inner):
        self._inner = inner
    def retrieve(self, q):
        return self._inner.retrieve(q)

class Magic:
    def __init__(self, inner):
        self._inner = inner
    def __getattr__(self, name):
        return getattr(self._inner, name)

e, m = Explicit(Inner()), Magic(Inner())""",
        options={
            "a": "for i in range(200_000):\n    e.retrieve(i)",
            "b": "for i in range(200_000):\n    m.retrieve(i)",
        },
        answer="a",
        hints=["When is `__getattr__` called, and what has already happened by then?"],
        why="""`__getattr__` runs only after normal attribute lookup has **failed**: Python searches the instance dict and the class (and raises an internal
        `AttributeError`), then calls `__getattr__`, which does another `getattr` on the inner object. The explicit method is found on the class
        immediately and makes one ordinary call. Beyond speed, explicit forwarding documents the interface; `__getattr__` is worth it only when
        a proxy must forward a large or unknown set of attributes."""),
    trace("Injected fakes in action", "medium",
        prompt="Fill in `result` and `log` after each marked line.",
        code="""
        class FakeClock:
            def __init__(self, times):
                self.times = list(times)
            def __call__(self):
                return self.times.pop(0)

        class FakeModel:
            def __init__(self, reply):
                self.reply = reply
            def complete(self, prompt):
                return self.reply

        class Timed:
            def __init__(self, model, clock):
                self.model, self.clock, self.log = model, clock, []
            def ask(self, prompt):
                start = self.clock()
                text = self.model.complete(prompt)
                self.log.append(round(self.clock() - start, 2))
                return text

        t = Timed(FakeModel("5 days"), FakeClock([0.0, 1.25, 10.0, 10.5]))
        result, log = t.ask("refund?"), list(t.log)  # row: "first call"
        result, log = t.ask("again"), list(t.log)  # row: "second call"
        t.model = FakeModel("30 days")
        t.clock = FakeClock([3.0, 3.0])
        result, log = t.ask("window?"), list(t.log)  # row: "swapped parts"
        """,
        trace_vars=["result", "log"],
        hints=["The clock returns its listed times in order, one per call; each `ask` calls it twice."],
        why="""The fake clock makes the timings exact: 1.25 seconds for the first call and 0.5 for the second, with no real waiting. Because the
        collaborators are ordinary attributes, they can be replaced at any time, here by a different model and a clock that reports zero
        elapsed time. `Timed` never knew it was talking to fakes: it only relied on `complete()` and on the clock being callable."""),
    fix("A type check that rejects valid input", "medium", tag="ML",
        prompt="""`normalise_scores(scores)` rejects anything that is not a `list`, so tuples, generators and `range`s fail although the code only
        needs to iterate. Make it accept any iterable of numbers (strings must still be rejected with `TypeError`, since iterating a string gives
        characters), and return a list.""",
        code="""
        def normalise_scores(scores):
            if not isinstance(scores, list):
                raise TypeError("scores must be a list")
            values = list(scores)
            top = max(values) if values else 0
            return [v / top for v in values] if top else [0.0 for _ in values]
        """,
        tests="""
        assert normalise_scores([2, 4]) == [0.5, 1.0] and normalise_scores((1, 4)) == [0.25, 1.0]
        assert normalise_scores(x for x in [5, 10]) == [0.5, 1.0] and normalise_scores(range(3)) == [0.0, 0.5, 1.0]
        assert normalise_scores([]) == [] and normalise_scores([0, 0]) == [0.0, 0.0]
        for bad in ["123", 5]:
            try:
                normalise_scores(bad)
                assert False, bad
            except TypeError:
                pass
        """,
        hints=["`isinstance(x, collections.abc.Iterable)` checks the protocol. Strings and bytes are iterable, so reject them explicitly."],
        solution="""
        from collections.abc import Iterable

        def normalise_scores(scores):
            if isinstance(scores, (str, bytes)) or not isinstance(scores, Iterable):
                raise TypeError(f"scores must be an iterable of numbers, got {type(scores).__name__}")
            values = list(scores)
            top = max(values) if values else 0
            return [v / top for v in values] if top else [0.0 for _ in values]
        """,
        why="""The function only iterates over its input once (by converting it to a list), so requiring a `list` was an arbitrary restriction that
        broke tuples, generators, `range` and NumPy arrays, the duck-typing mistake. `collections.abc.Iterable` checks the capability instead
        of the type. Strings are the classic exception: they are iterable, but iterating gives characters, so "123" would be silently
        treated as three digits; rejecting `str` and `bytes` explicitly is a common, deliberate rule. An integer is not iterable and is
        rejected with a clear message instead of failing inside `list()`."""),
    write("Code against a protocol", "medium", tag="RAG",
        prompt="""Define a runtime-checkable protocol `VectorStore` with `add(ids, vectors)` and `query(vector, k)` returning a list of ids. Write a
        class `MemoryStore` that implements it **without inheriting** (cosine similarity, highest first, ties by insertion order), and a function
        `index_and_search(store, embed, docs, query, k)` that works with any `VectorStore`: it embeds the docs with `embed(texts)` (a function),
        adds them with ids `"d0"`, `"d1"`, ..., and returns the ids for the query. Raise `TypeError` if `store` is not a `VectorStore`.""",
        code="""
        import math
        from typing import Protocol, runtime_checkable

        def index_and_search(store, embed, docs, query, k):
            pass
        """,
        tests="""
        def embed(texts):
            vocab = ["refund", "window", "reset", "password", "policy"]
            return [[float(w in t.lower().split()) for w in vocab] for t in texts]

        docs = ["Refund policy", "Reset password", "Refund window"]
        store = MemoryStore()
        assert isinstance(store, VectorStore)
        assert index_and_search(store, embed, docs, "refund window", 2) == ["d2", "d0"]
        assert index_and_search(MemoryStore(), embed, docs, "reset", 1) == ["d1"]
        try:
            index_and_search(object(), embed, docs, "x", 1)
            assert False
        except TypeError:
            pass
        assert VectorStore not in MemoryStore.__mro__
        """,
        hints=["A protocol is a class inheriting `Protocol` with method stubs (`...`). `MemoryStore` keeps lists of ids and vectors.",
               "Cosine: `dot / (norm_a * norm_b)`, treating a zero norm as similarity 0."],
        solution="""
        import math
        from typing import Protocol, runtime_checkable


        @runtime_checkable
        class VectorStore(Protocol):
            def add(self, ids: list[str], vectors: list[list[float]]) -> None: ...
            def query(self, vector: list[float], k: int) -> list[str]: ...


        class MemoryStore:
            def __init__(self):
                self._ids, self._vectors = [], []

            def add(self, ids, vectors):
                self._ids.extend(ids)
                self._vectors.extend(vectors)

            @staticmethod
            def _cosine(a, b):
                na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(x * x for x in b))
                return sum(x * y for x, y in zip(a, b)) / (na * nb) if na and nb else 0.0

            def query(self, vector, k):
                scored = [(self._cosine(vector, v), i) for i, v in zip(self._ids, self._vectors)]
                ranked = sorted(scored, key=lambda p: p[0], reverse=True)
                return [i for _, i in ranked[:k]]


        def index_and_search(store, embed, docs, query, k):
            if not isinstance(store, VectorStore):
                raise TypeError(f"{type(store).__name__} does not implement VectorStore")
            store.add([f"d{i}" for i in range(len(docs))], embed(docs))
            return store.query(embed([query])[0], k)
        """,
        why="""`index_and_search` depends only on the two methods of the protocol, so it works with this in-memory store, with a client for Chroma,
        Qdrant or pgvector wrapped to have `add` and `query`, or with a test fake, and `MemoryStore` never imports or inherits the protocol
        (the last assertion). The `isinstance` check gives an early, clear error, though it only verifies that the methods exist. Stable
        sorting keeps ties in insertion order. Passing `embed` as a plain function is the simplest strategy object; if the embedder needed
        state (a model, a cache), it would be an object satisfying an `Embedder` protocol instead."""),
    predict("Mixin methods from collections.abc", "medium",
        code="""
        from collections.abc import Mapping, Sequence

        class Squares(Sequence):
            def __init__(self, n):
                self.n = n
            def __len__(self):
                return self.n
            def __getitem__(self, i):
                if not 0 <= i < self.n:
                    raise IndexError(i)
                return i * i

        s = Squares(5)
        print(list(s), 9 in s, s.index(16), s.count(4), list(reversed(s)))
        print(isinstance(s, Sequence), isinstance(range(3), Sequence), isinstance({}, Mapping), isinstance({}, Sequence))
        """,
        hints=["`Sequence` provides `__iter__`, `__contains__`, `index`, `count` and `__reversed__` from `__len__` and `__getitem__`."],
        why="""Two methods were written and five more came from the `Sequence` ABC, all built on `__getitem__` and `__len__`: iteration, `in`, `index`,
        `count` and `reversed`. `range` is registered as a `Sequence`, and dicts are `Mapping`s, not `Sequence`s: these `isinstance` checks test
        capabilities, which is how generic code distinguishes "list-like" from "dict-like" input. (This `__getitem__` accepts only
        non-negative ints, so negative indexes and slices are not supported, which `Sequence` does not add for you.)"""),
)

section("hard", "Hard",
    write("A pipeline of swappable steps", "hard", tag="RAG",
        prompt="""Write `Pipeline(steps, clock)` where `steps` is a list of `(name, step)` pairs and each step is a callable taking and returning a
        dict (the "state"). `run(state)` passes a **copy** of the state through every step in order, records `self.trace` as a list of `(name,
        seconds)` using the injected clock, and returns the final state. If a step raises, add the note `"in step <name>"` and re-raise, keeping
        the trace of the steps that ran. Add `replace(name, step)` returning a **new** pipeline with one step swapped (unknown name: `KeyError`).""",
        code="""
        class Pipeline:
            pass
        """,
        tests="""
        ticks = iter([0.0, 0.1, 0.1, 0.4, 0.4, 1.4, 5.0, 5.2, 5.2, 5.3, 6.0])
        clock = lambda: next(ticks)

        def retrieve(s):
            return {**s, "docs": [f"doc about {s['query']}"]}

        def rerank(s):
            return {**s, "docs": sorted(s["docs"])}

        def generate(s):
            if not s["docs"]:
                raise ValueError("no context")
            return {**s, "answer": f"Based on {len(s['docs'])} doc(s)"}

        p = Pipeline([("retrieve", retrieve), ("rerank", rerank), ("generate", generate)], clock)
        start = {"query": "refund"}
        out = p.run(start)
        assert out["answer"] == "Based on 1 doc(s)" and start == {"query": "refund"}
        assert [(n, round(t, 2)) for n, t in p.trace] == [("retrieve", 0.1), ("rerank", 0.3), ("generate", 1.0)]

        empty = p.replace("retrieve", lambda s: {**s, "docs": []})
        try:
            empty.run({"query": "x"})
            assert False
        except ValueError as e:
            assert e.__notes__ == ["in step generate"] and [n for n, _ in empty.trace] == ["retrieve", "rerank"]
        assert [n for n, _ in p.trace] == ["retrieve", "rerank", "generate"]
        try:
            p.replace("summarise", rerank)
            assert False
        except KeyError:
            pass
        """,
        hints=["`replace` builds a new list of steps and returns `Pipeline(new_steps, self.clock)`; the original stays unchanged.",
               "Record the trace entry for a step only after it succeeds; use `try`/`except Exception as e: e.add_note(...); raise`."],
        solution="""
        class Pipeline:
            def __init__(self, steps, clock):
                self.steps = list(steps)
                self.clock = clock
                self.trace = []

            def run(self, state):
                self.trace = []
                state = dict(state)
                for name, step in self.steps:
                    start = self.clock()
                    try:
                        state = step(state)
                    except Exception as e:
                        e.add_note(f"in step {name}")
                        raise
                    self.trace.append((name, self.clock() - start))
                return state

            def replace(self, name, step):
                names = [n for n, _ in self.steps]
                if name not in names:
                    raise KeyError(name)
                new_steps = [(n, step if n == name else s) for n, s in self.steps]
                return Pipeline(new_steps, self.clock)
        """,
        why="""The pipeline knows nothing about retrieval or generation: it composes callables that share one contract (state in, state out), so every
        step can be a function, a callable object (9.2) or a wrapper, and swapping one is a configuration change. `replace` returns a **new**
        pipeline, so experiments (a different reranker) cannot affect the original, the immutable-update style of 2.3. Copying the input state
        keeps the caller's dict untouched, and steps return new dicts rather than mutating. The trace with an injected clock gives exact
        per-step timings in tests, and the note on failures names the step without changing the exception type (7.2). LangChain's runnables
        and Haystack pipelines are this idea with many more features."""),
    fix("Read the code: a service that cannot be tested", "hard", tag="GenAI",
        prompt="""`AnswerService` creates its own client and reads the real clock inside its methods, so tests cannot run it without a network and
        cannot check its timings; it also inherits from the client, so callers can reach `raw_request` directly and bypass the service's limits.
        Rewrite it to receive `client` and `clock` in `__init__` (composition instead of inheritance), keeping its behaviour: reject questions
        over `max_chars`, call `client.complete(prompt)` with the prompt `"Answer briefly: <question>"`, and record `(question, seconds)` in
        `self.history`.""",
        code="""
        import time


        class RealClient:
            def raw_request(self, payload):
                raise RuntimeError("network not available in tests")

            def complete(self, prompt):
                return self.raw_request({"prompt": prompt})


        class AnswerService(RealClient):
            def __init__(self, max_chars=200):
                self.max_chars = max_chars
                self.history = []

            def answer(self, question):
                if len(question) > self.max_chars:
                    raise ValueError("question too long")
                start = time.time()
                text = self.complete(f"Answer briefly: {question}")
                self.history.append((question, time.time() - start))
                return text
        """,
        tests="""
        class FakeClient:
            def __init__(self):
                self.prompts = []
            def complete(self, prompt):
                self.prompts.append(prompt)
                return "Five days."

        ticks = iter([100.0, 100.75])
        fake = FakeClient()
        svc = AnswerService(client=fake, clock=lambda: next(ticks), max_chars=40)
        assert svc.answer("How long do refunds take?") == "Five days."
        assert fake.prompts == ["Answer briefly: How long do refunds take?"] and svc.history == [("How long do refunds take?", 0.75)]
        try:
            svc.answer("x" * 41)
            assert False
        except ValueError:
            assert len(fake.prompts) == 1
        assert not hasattr(svc, "raw_request") and not isinstance(svc, RealClient)
        """,
        hints=["Remove the base class; store `self.client` and `self.clock`; call `self.client.complete(...)` and `self.clock()`.",
               "Give `clock` a production default such as `time.monotonic`."],
        solution="""
        import time


        class RealClient:
            def raw_request(self, payload):
                raise RuntimeError("network not available in tests")

            def complete(self, prompt):
                return self.raw_request({"prompt": prompt})


        class AnswerService:
            def __init__(self, client, clock=time.monotonic, max_chars=200):
                self.client = client
                self.clock = clock
                self.max_chars = max_chars
                self.history = []

            def answer(self, question):
                if len(question) > self.max_chars:
                    raise ValueError("question too long")
                start = self.clock()
                text = self.client.complete(f"Answer briefly: {question}")
                self.history.append((question, self.clock() - start))
                return text
        """,
        why="""Three problems, one cure. Inheriting from `RealClient` welded the service to one client implementation and exposed `raw_request`, so any
        caller could bypass the length limit; a service **uses** a client, it is not one. Calling `time.time()` inside the method made timings
        untestable (and `time.time` can jump, 8.3; `time.monotonic` is the right default). Receiving both collaborators in `__init__` fixes all
        of it: production code builds `AnswerService(RealClient())`, tests pass a fake client and a scripted clock and check the exact prompt,
        timing and rejection path, and switching providers later means passing another object with `complete`. This is the most common
        refactoring that makes LLM application code testable."""),
    write("A metering proxy", "hard", tag="GenAI",
        prompt="""Write `Metered(inner)`, a proxy that forwards **every** attribute access to `inner` using `__getattr__`. Callable attributes are
        returned wrapped so each call is counted in `self.calls` (a `Counter` by method name) and then delegated; non-callable attributes are
        returned as they are. The proxy's own attributes (`calls` and the inner object) must not be forwarded, and assigning an attribute on the
        proxy must set it on the **inner** object, except for the proxy's own two attributes.""",
        code="""
        from collections import Counter

        class Metered:
            pass
        """,
        tests="""
        class Client:
            def __init__(self):
                self.model = "small"
            def complete(self, prompt):
                return f"{self.model}: {prompt}"
            def embed(self, texts):
                return [[len(t)] for t in texts]

        inner = Client()
        m = Metered(inner)
        assert m.complete("hi") == "small: hi" and m.complete("yo") == "small: yo" and m.embed(["ab"]) == [[2]]
        assert m.calls == Counter({"complete": 2, "embed": 1}) and m.model == "small"
        m.model = "large"
        assert inner.model == "large" and m.complete("x") == "large: x" and m.calls["complete"] == 3
        try:
            m.missing
            assert False
        except AttributeError:
            pass
        assert "model" not in vars(m)
        """,
        hints=["Set the proxy's own attributes with `object.__setattr__(self, ...)` in `__init__`, because `__setattr__` is overridden.",
               "`__getattr__(self, name)`: get `attr = getattr(self._inner, name)`; if callable, return a small wrapper function that counts and calls it."],
        solution="""
        from collections import Counter

        class Metered:
            _OWN = ("_inner", "calls")

            def __init__(self, inner):
                object.__setattr__(self, "_inner", inner)
                object.__setattr__(self, "calls", Counter())

            def __getattr__(self, name):
                attr = getattr(self._inner, name)
                if not callable(attr):
                    return attr

                def counted(*args, **kwargs):
                    self.calls[name] += 1
                    return attr(*args, **kwargs)
                return counted

            def __setattr__(self, name, value):
                if name in self._OWN:
                    object.__setattr__(self, name, value)
                else:
                    setattr(self._inner, name, value)
        """,
        why="""`__getattr__` is only consulted when normal lookup fails, so the proxy's real attributes (`_inner`, `calls`, its methods) are found
        normally and never forwarded, while everything else, `complete`, `embed`, `model` and any method added to the client later, is fetched
        from the inner object. Wrapping callables in a small closure lets the proxy count calls without knowing the inner object's interface.
        Overriding `__setattr__` makes assignments go to the inner object too, which is why `__init__` must bypass it with
        `object.__setattr__`. A missing attribute raises the inner object's `AttributeError` naturally. Proxies like this are how libraries add
        instrumentation to SDK clients (OpenTelemetry's auto-instrumentation, request-recording test tools); the trade-off is that IDEs and type
        checkers cannot see the forwarded attributes."""),
    predict("Registered virtual subclasses", "hard",
        code="""
        from abc import ABC, abstractmethod

        class Retriever(ABC):
            @abstractmethod
            def retrieve(self, query): ...

        class ThirdPartySearch:                 # from a library you do not control
            def search(self, q):
                return [q]

        Retriever.register(ThirdPartySearch)
        t = ThirdPartySearch()
        print(isinstance(t, Retriever), issubclass(ThirdPartySearch, Retriever), Retriever in ThirdPartySearch.__mro__)
        try:
            t.retrieve("x")
        except AttributeError as e:
            print("AttributeError")

        class Adapter(Retriever):
            def __init__(self, inner):
                self.inner = inner
            def retrieve(self, query):
                return self.inner.search(query)

        print(Adapter(t).retrieve("refund"), isinstance(Adapter(t), Retriever))
        """,
        hints=["`register` makes `isinstance` and `issubclass` succeed without inheritance, and without checking anything."],
        why="""`Retriever.register(ThirdPartySearch)` declares a **virtual subclass**: `isinstance` and `issubclass` now return `True`, but nothing is inherited
        (the ABC is not in the MRO) and nothing is checked, so the missing `retrieve` method is only discovered when called. Registration is a
        promise you make on someone else's behalf. The adapter is the honest alternative: a small composed class that implements the interface
        by translating to the third-party method, which is how real code integrates libraries with different method names."""),
)

section("interview", "Interview questions",
    explain("Compare duck typing, abstract base classes and `typing.Protocol`.", "medium", tag="Interview",
        why="""All three describe "an object with these methods", with different enforcement. Duck typing has no declaration at all: code simply calls
        the methods it needs, so any object with them works, and mistakes surface at run time when a method is missing. An ABC (`abc.ABC` with
        `@abstractmethod`) is nominal: implementations inherit from it (or are registered), Python refuses to instantiate subclasses missing
        abstract methods, and the ABC can supply shared concrete methods, like `collections.abc.Mapping` deriving `get` and `items`. A `Protocol`
        is structural: any class with matching methods satisfies it without inheriting, and type checkers verify signatures before running;
        `@runtime_checkable` adds `isinstance` support that checks only method names. Use ABCs for hierarchies you own and want enforced at
        instantiation, protocols to type the code that consumes interfaces (especially from third-party classes), and plain duck typing for
        small internal code."""),
    explain("What is dependency injection, and why does it matter for testing LLM applications?", "medium", tag="Interview",
        why="""Dependency injection means a component receives the objects it depends on (an LLM client, a vector store, a clock, a random generator, a
        logger) instead of constructing them itself, usually through `__init__` parameters with production defaults. The wiring happens in one
        place at start-up. For LLM applications it is what makes tests possible and cheap: a fake client returns scripted replies, raises
        timeouts or rate limits on demand, and records the prompts it received, so tests can assert on exact prompts, retries, fallbacks and
        parsing without network calls, cost or non-determinism; a fake clock makes timing and backoff checks instant. It also makes swapping
        providers, models or stores a configuration change rather than a code change. The sign it is missing: classes that call
        `OpenAI()`, `time.time()` or `random.random()` deep inside their methods."""),
    explain("Design the components of a pluggable RAG system. Where do you use composition, protocols and inheritance?", "hard", tag="Interview",
        why="""Define small interfaces as protocols for each role: a `Loader` (path to documents), a `Chunker` (document to chunks), an `Embedder` (texts to
        vectors), a `VectorStore` (add, query, delete by id), a `Reranker` (query and candidates to ordered candidates), and an `LLM` (messages to a
        response). The RAG service is composed of one object per role, all injected, so each can be swapped by configuration (a different
        embedding model, Qdrant instead of an in-memory store) and faked in tests. Cross-cutting behaviour is added by composition as wrappers
        with the same interface: a caching embedder, a retrying LLM, a fallback between providers, a tracing layer around every component.
        Inheritance is kept shallow and local: an ABC or base class for your own implementations of one role when they share real code (common
        validation and batching in embedders), and exception hierarchies. Plain functions serve as simple strategies (chunking rules, scoring).
        The design makes each component testable alone, lets evaluations compare variants by swapping one component, and keeps vendor SDKs at
        the edges behind adapters."""),
)

recap(
    "Composition (has a, uses a) builds objects from other objects and delegates to them; wrappers with the same interface stack like decorators.",
    "Inject collaborators (clients, stores, clocks) through `__init__`; tests then pass fakes and check prompts, timings and failure paths.",
    "Duck typing: rely on the methods you call, not on the type; check capabilities (`collections.abc.Iterable`) rather than `isinstance(x, list)`.",
    "ABCs with `@abstractmethod` enforce an interface at instantiation and can supply concrete methods; `collections.abc` mixins derive many methods from a few.",
    "`typing.Protocol` defines structural interfaces checked by type checkers; prefer composition to inheritance unless there is a real \"is a\".",
)
