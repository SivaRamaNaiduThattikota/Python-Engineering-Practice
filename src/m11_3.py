from lesson import *

lesson(
    id="m11-3", num="11.3", title="Dataclasses",
    intro="`@dataclass` writes the boilerplate of data-holding classes from their type hints: `__init__`, `__repr__`, "
          "`__eq__`, and optionally ordering, hashing and slots. Fields and defaults (and the mutable-default rule), "
          "`field()` options, `__post_init__` for validation and derived values, frozen instances and `replace`, "
          "`asdict` and `fields`, inheritance and keyword-only fields, and what dataclasses do not do (validate types). "
          "Applied to documents, configs, chunks and experiment records.",
    desc="Fields, `default_factory`, frozen, `__post_init__`, slots.",
    keys="dataclass field default_factory post_init frozen replace asdict astuple fields slots order unsafe_hash kw_only initvar init repr compare namedtuple config experiment",
)

term("Dataclass", "A class decorated with `@dataclass`, which generates `__init__`, `__repr__` and `__eq__` (and more on request) from its annotated class attributes.")
term("Field", "One annotated attribute of a dataclass, such as `score: float = 0.0`. `dataclasses.field(...)` customises it.")
term("default_factory", "A function called to create a fresh default value for each instance, required for mutable defaults: `field(default_factory=list)`.")

section("why", "From boilerplate to one decorator",
    p("""Many classes are mainly **data**: a document with an id, text and tags; a configuration; an evaluation result; a record from a file. Writing them
    by hand means an `__init__` that copies every parameter to an attribute, a `__repr__` that shows them, and an `__eq__` (and maybe `__hash__`) that
    compares them, all of which must be updated every time a field is added (9.1, 9.2). **`@dataclass`** generates those methods from the class's
    annotated attributes, so the class body states only what matters: the fields, their types and their defaults."""),
    ex("""
    from dataclasses import dataclass

    @dataclass
    class Document:
        id: str
        text: str
        score: float = 0.0

    d = Document("faq-1", "Refunds take 5 days.")
    print(d)
    print(d == Document("faq-1", "Refunds take 5 days."), d.score, Document("x", "y", score=0.9))
    try:
        Document("only-id")
    except TypeError as e:
        print("TypeError:", e)
    """, "first_dataclass.py"),
    p("""The generated `__init__` takes the fields in the order they are declared, with the declared defaults, exactly as if you had written it; the
    `__repr__` shows class name and fields, readable in logs and test failures; `__eq__` compares instances of the same class field by field, as a
    tuple. Everything is normal Python afterwards: you can add methods, properties and class methods (9.3, 9.6). Note that the **type hints are not
    checked**: `Document(1, None)` is accepted. Dataclasses generate code from hints; validation is Pydantic's job (11.4)."""),
)

section("defaults", "Defaults, `default_factory` and `field()`",
    p("""A field's default is evaluated **once**, when the class is defined, and shared by every instance, which is safe for numbers, strings and `None`
    but would be the mutable-default bug of 2.4 for a list or dict. Dataclasses refuse it outright: `tags: list[str] = []` raises `ValueError:
    mutable default <class 'list'> for field tags is not allowed` when the class is created. Use **`field(default_factory=list)`** instead: the
    factory is called for every new instance, so each gets its own list (problem 3)."""),
    p("""`dataclasses.field(...)` customises a field in other ways too. `repr=False` hides it from the repr (secrets, huge embeddings). `compare=False`
    leaves it out of `__eq__` (and of ordering and hashing): for caches, timestamps or metadata that should not affect identity. `init=False` removes
    it from `__init__`, for values computed in `__post_init__` (below). `kw_only=True` makes it keyword-only. `metadata={...}` attaches arbitrary
    information that tools can read through `dataclasses.fields()`."""),
    ex("""
    from dataclasses import dataclass, field

    @dataclass
    class Chunk:
        doc_id: str
        text: str
        tags: list[str] = field(default_factory=list)
        embedding: list[float] = field(default_factory=list, repr=False, compare=False)
        source: str = field(default="unknown", metadata={"help": "where the text came from"})

    a, b = Chunk("d1", "Refunds"), Chunk("d1", "Refunds")
    a.tags.append("billing")
    print(a, b.tags)
    b.embedding = [0.1, 0.2]
    a.tags.clear()
    print(a == b)

    try:
        @dataclass
        class Bad:
            tags: list[str] = []
    except ValueError as e:
        print("ValueError:", e)
    """, "defaults.py"),
    p("""`a == b` is true even though only `b` has an embedding, because `compare=False` excluded it: two chunks with the same document and text are the same
    chunk whatever their cached vectors. The order rule for defaults is the same as for function parameters: fields without defaults must come before
    fields with defaults, or the class definition fails. Keyword-only fields lift that restriction (problem 6)."""),
)

section("postinit", "`__post_init__`: validation and derived fields",
    p("""The generated `__init__` only assigns fields. If you define **`__post_init__(self)`**, the generated `__init__` calls it at the end, after all fields
    are set. It is the place to **validate** (raise `ValueError` for impossible values), to **normalise** (strip text, lower-case labels, sort tags) and
    to **compute derived fields**, declared with `field(init=False)` so they are not constructor arguments. For values needed only during
    construction, not stored, declare them as `InitVar[...]`: they are passed to `__init__` and then to `__post_init__` as arguments."""),
    ex("""
    from dataclasses import dataclass, field, InitVar

    @dataclass
    class Prediction:
        label: str
        probs: dict[str, float]
        threshold: InitVar[float] = 0.5
        confident: bool = field(init=False)

        def __post_init__(self, threshold):
            self.label = self.label.strip().lower()
            if self.label not in self.probs:
                raise ValueError(f"label {self.label!r} has no probability")
            total = sum(self.probs.values())
            if abs(total - 1) > 1e-6:
                raise ValueError(f"probabilities sum to {total}, not 1")
            self.confident = self.probs[self.label] >= threshold

    p = Prediction(" Spam ", {"spam": 0.8, "ham": 0.2})
    print(p, Prediction("ham", {"spam": 0.45, "ham": 0.55}, threshold=0.6).confident)
    try:
        Prediction("phish", {"spam": 1.0})
    except ValueError as e:
        print("ValueError:", e)
    """, "post_init.py"),
    p("""`__post_init__` runs only at construction. Assigning a field later (`p.label = "x"`) bypasses it, so derived fields can go stale and invariants can
    be broken. For data that changes, use properties (9.3) for derived values, or make the dataclass **frozen** so that it cannot change at all."""),
)

section("frozen", "Frozen dataclasses, `replace`, ordering and slots",
    p("""`@dataclass(frozen=True)` makes instances immutable: assigning a field raises `FrozenInstanceError`. Because equal frozen objects can never change,
    the dataclass also gets a `__hash__` built from the compared fields, so instances work in sets and as dict keys (9.2). To "change" a frozen
    object, **`dataclasses.replace(obj, field=new)`** builds a new instance with some fields changed, calling `__init__` (and `__post_init__`) again,
    so validation applies to the copy too. Inside `__post_init__` of a frozen class, normalising a field requires `object.__setattr__(self, "name",
    value)`, since normal assignment is blocked (9.3)."""),
    ex("""
    import dataclasses
    from dataclasses import dataclass

    @dataclass(frozen=True, slots=True, order=True)
    class Version:
        major: int
        minor: int = 0
        patch: int = 0

    v = Version(1, 9)
    print(v, sorted([Version(1, 10), v, Version(0, 9, 3)]), v < Version(1, 10))
    try:
        v.minor = 10
    except dataclasses.FrozenInstanceError as e:
        print("FrozenInstanceError:", e)
    w = dataclasses.replace(v, minor=10)
    print(w, v, {v, Version(1, 9)}, hasattr(v, "__dict__"))
    """, "frozen.py"),
    p("""`order=True` generates `__lt__` and friends comparing the fields **as a tuple, in declaration order**, which is right for a version but a trap for
    records whose first field is a name: sorting would then be alphabetical, not by score (problem 10). `slots=True` (Python 3.10+) generates
    `__slots__` (9.3): smaller instances and no accidental new attributes. `unsafe_hash=True` adds a hash to a mutable dataclass, which is only safe if
    the compared fields are never changed while the object is in a set or dict (problem 14)."""),
)

section("utilities", "Inspecting and converting: `fields`, `asdict`, `astuple`",
    p("""The `dataclasses` module exposes the structure it generated. **`fields(obj_or_class)`** returns `Field` objects with each field's name, type, default
    and metadata, which is how generic code (serialisers, config loaders, CLI builders) works with any dataclass. **`asdict(obj)`** converts an
    instance into a dict, **recursively**: nested dataclasses, and lists and dicts containing them, become plain dicts and lists, ready for
    `json.dumps`. **`astuple`** does the same into tuples. Both deep-copy the values, so the result is independent of the object. Going the other
    way, from a dict to nested dataclasses, needs a little code, usually a classmethod `from_dict` (9.6, problem 7)."""),
    ex("""
    import json
    from dataclasses import dataclass, field, fields, asdict

    @dataclass
    class Metric:
        name: str
        value: float

    @dataclass
    class Run:
        run_id: str
        params: dict[str, float]
        metrics: list[Metric] = field(default_factory=list)

    r = Run("r1", {"lr": 0.1}, [Metric("f1", 0.81), Metric("loss", 0.42)])
    print([(f.name, f.type) for f in fields(Run)])
    data = asdict(r)
    print(json.dumps(data))
    data["params"]["lr"] = 999
    print(r.params["lr"], type(data["metrics"][0]).__name__)
    """, "utilities.py"),
)

section("inheritance", "Inheritance, keyword-only fields, and limits",
    p("""Dataclasses can inherit: the subclass's fields come after the base's, and the generated `__init__` takes them all. The rule that fields without
    defaults must come first applies across the whole hierarchy, so a base class with a default field followed by a subclass with a required one fails
    at class creation (`TypeError: non-default argument follows default argument`). **`kw_only=True`**, on the decorator or on individual fields,
    solves it: keyword-only fields may be declared in any order, and calls become self-documenting, `Config(model="small", retries=3)`."""),
    ex("""
    from dataclasses import dataclass, KW_ONLY

    @dataclass(kw_only=True)
    class BaseConfig:
        timeout: float = 30.0

    @dataclass(kw_only=True)
    class LLMConfig(BaseConfig):
        model: str
        temperature: float = 0.0

    @dataclass
    class Request:
        prompt: str
        _: KW_ONLY
        stream: bool = False
        user: str = "anon"

    print(LLMConfig(model="small"), Request("hi", stream=True))
    try:
        Request("hi", True)
    except TypeError as e:
        print("TypeError:", str(e)[:60])
    """, "inheritance.py"),
    p("""Know the limits. Dataclasses **do not validate types** (hints are documentation, 11.1), they do not parse or convert input, and they do not
    serialise anything more complex than `asdict`. That is what makes them fast and simple, and what Pydantic adds (11.4). Compared with
    `typing.NamedTuple`, a dataclass is mutable by default, can have defaults computed per instance, `__post_init__`, slots and ordering control;
    a named tuple is an immutable tuple (it can be unpacked and indexed), lighter, but less flexible. Use dataclasses for internal structured data,
    Pydantic models at boundaries, `TypedDict` for dicts that stay dicts (11.2)."""),
)

section("warmup", "Warm-up",
    predict("What @dataclass generates", "easy",
        code="""
        from dataclasses import dataclass

        @dataclass
        class Result:
            query: str
            hits: int = 0
            score: float = 0.0

        a = Result("refund", 3)
        b = Result("refund", hits=3)
        print(a, a == b, a is b)
        print(Result("x") == Result("x", 0, 0.0), Result("x") == ("x", 0, 0.0))
        print(Result(42, "many"))
        """,
        hints=["The generated `__eq__` compares instances of the same class field by field; types are not checked."],
        why="""The generated `__init__` accepts positional and keyword arguments in field order, with the declared defaults, and the repr shows every field. Two
        instances with equal fields are equal but distinct objects. Equality with a tuple is `False`: the generated `__eq__` only compares instances of
        the same class (it returns `NotImplemented` otherwise, 9.2). The last line shows that hints are not enforced: an int query and a string hit
        count are stored without complaint."""),
    write("A document dataclass", "easy", tag="RAG",
        prompt="""Write a dataclass `Document` with fields `id: str`, `text: str`, `tags: list[str]` (default: a new empty list per instance), `score: float = 0.0`
        and `embedding: list[float]` (default empty list, hidden from the repr and ignored by `==`). Add a method `word_count()` and a method
        `tag(label)` that adds a lower-cased label if it is not present and returns `self`.""",
        code="""
        from dataclasses import dataclass, field

        @dataclass
        class Document:
            pass
        """,
        tests="""
        a = Document("d1", "Refund policy for orders")
        b = Document("d2", "Reset password")
        a.tag("Billing").tag("billing").tag("FAQ")
        assert a.tags == ["billing", "faq"] and b.tags == [] and a.word_count() == 4
        assert repr(b) == "Document(id='d2', text='Reset password', tags=[], score=0.0)"
        c = Document("d1", "Refund policy for orders", tags=["billing", "faq"], embedding=[0.1])
        assert c == a and Document("d3", "x", score=0.5).score == 0.5
        """,
        hints=["`tags: list[str] = field(default_factory=list)`; `embedding: list[float] = field(default_factory=list, repr=False, compare=False)`."],
        solution="""
        from dataclasses import dataclass, field

        @dataclass
        class Document:
            id: str
            text: str
            tags: list[str] = field(default_factory=list)
            score: float = 0.0
            embedding: list[float] = field(default_factory=list, repr=False, compare=False)

            def word_count(self):
                return len(self.text.split())

            def tag(self, label):
                label = label.lower()
                if label not in self.tags:
                    self.tags.append(label)
                return self
        """,
        why="""`default_factory=list` gives each document its own tag list, so tagging `a` leaves `b` untouched, the bug that mutable defaults cause in hand-written
        classes (9.1) is impossible here. Hiding the embedding from the repr keeps logs readable (embeddings are hundreds of floats), and excluding it
        from comparison means a document is identified by its id, text, tags and score, not by a cached vector. Methods live in the class as usual;
        `@dataclass` only adds the generated ones."""),
    fix("A mutable default that breaks the class", "easy", tag="GenAI",
        prompt="""Defining `Conversation` fails with `ValueError: mutable default <class 'list'> for field messages is not allowed`. Fix the field so every
        conversation gets its own message list.""",
        code="""
        from dataclasses import dataclass

        @dataclass
        class Conversation:
            system: str
            messages: list[dict] = []

            def add(self, role, content):
                self.messages.append({"role": role, "content": content})
        """,
        tests="""
        a, b = Conversation("Be brief."), Conversation("Be formal.")
        a.add("user", "hi")
        assert a.messages == [{"role": "user", "content": "hi"}] and b.messages == []
        assert Conversation("x", [{"role": "user", "content": "y"}]).messages[0]["content"] == "y"
        """,
        hints=["`from dataclasses import field` and use `field(default_factory=list)`."],
        solution="""
        from dataclasses import dataclass, field

        @dataclass
        class Conversation:
            system: str
            messages: list[dict] = field(default_factory=list)

            def add(self, role, content):
                self.messages.append({"role": role, "content": content})
        """,
        why="""A default value is created once, when the class is defined, and a plain class would share that one list between every instance that did not pass its
        own (the bug of 2.4 and 9.1). Dataclasses detect mutable defaults of the common types (`list`, `dict`, `set`) and refuse to create the class,
        turning a subtle data leak into an error at import time. `default_factory=list` calls `list()` for each new instance. Note that a caller who
        passes their own list still shares it with the conversation; copying in `__post_init__` would prevent that."""),
    predict("Frozen instances and replace", "easy",
        code="""
        import dataclasses
        from dataclasses import dataclass

        @dataclass(frozen=True)
        class Settings:
            model: str
            temperature: float = 0.0

        s = Settings("small")
        t = dataclasses.replace(s, temperature=0.7)
        print(s, t, s is t)
        try:
            s.model = "large"
        except dataclasses.FrozenInstanceError:
            print("cannot assign")
        print(len({s, Settings("small"), t}), {s: "cached"}[Settings("small")])
        """,
        hints=["A frozen dataclass is hashable by its fields; `replace` builds a new instance."],
        why="""`replace` returns a new object with one field changed and leaves the original as it was. Assignment raises `FrozenInstanceError`. Because frozen instances
        cannot change, the dataclass generates a hash from the fields, so equal settings collapse in a set and work as dict keys: `Settings("small")` finds
        the entry stored under `s`. That makes frozen dataclasses good cache keys for model configurations (8.3)."""),
)

section("medium", "Medium",
    write("A validated, immutable generation config", "medium", tag="GenAI",
        prompt="""Write a frozen dataclass with slots, `GenerationConfig(model: str, temperature: float = 0.0, max_tokens: int = 512, stop: tuple[str, ...] = ())`,
        whose `__post_init__` raises `ValueError` for a blank model, a temperature outside `[0, 2]` or a non-positive `max_tokens`, and **normalises** `stop`
        by removing duplicates while keeping order (it must still be a tuple). Add `with_changes(**changes)` returning a new, validated config.""",
        code="""
        import dataclasses
        from dataclasses import dataclass

        @dataclass(frozen=True, slots=True)
        class GenerationConfig:
            pass
        """,
        tests="""
        import dataclasses
        c = GenerationConfig("small", stop=("###", "User:", "###"))
        assert c.stop == ("###", "User:") and c.temperature == 0.0 and not hasattr(c, "__dict__")
        hot = c.with_changes(temperature=0.9)
        assert hot.temperature == 0.9 and c.temperature == 0.0 and hot.stop == ("###", "User:")
        for bad in [dict(model=" "), dict(model="x", temperature=3), dict(model="x", max_tokens=0)]:
            try:
                GenerationConfig(**bad)
                assert False, bad
            except ValueError:
                pass
        try:
            c.with_changes(temperature=-1)
            assert False
        except ValueError:
            pass
        assert len({c, GenerationConfig("small", stop=("###", "User:"))}) == 1
        """,
        hints=["In a frozen dataclass, normalise with `object.__setattr__(self, \"stop\", ...)` inside `__post_init__`.",
               "`with_changes` is `dataclasses.replace(self, **changes)`, which runs `__post_init__` again."],
        solution="""
        import dataclasses
        from dataclasses import dataclass

        @dataclass(frozen=True, slots=True)
        class GenerationConfig:
            model: str
            temperature: float = 0.0
            max_tokens: int = 512
            stop: tuple[str, ...] = ()

            def __post_init__(self):
                if not self.model.strip():
                    raise ValueError("model must not be blank")
                if not 0 <= self.temperature <= 2:
                    raise ValueError(f"temperature must be in [0, 2], got {self.temperature}")
                if self.max_tokens < 1:
                    raise ValueError(f"max_tokens must be positive, got {self.max_tokens}")
                object.__setattr__(self, "stop", tuple(dict.fromkeys(self.stop)))

            def with_changes(self, **changes):
                return dataclasses.replace(self, **changes)
        """,
        why="""Immutability plus validation in `__post_init__` gives the strongest guarantee a plain Python object can have: every config that exists is valid, and stays
        valid, because nothing can change it, and every "change" goes through `replace`, which constructs a new instance and validates it again. Frozen
        dataclasses block `self.stop = ...`, so normalisation uses `object.__setattr__`, the same escape hatch as 9.3. `dict.fromkeys` removes duplicate
        stop sequences in order (4.5). Being frozen also makes configs hashable, so they can key caches of model responses, and slots make them small.
        This is the hand-made version of a Pydantic model with `frozen=True` and validators (11.4)."""),
    fix("Inherited defaults block a required field", "medium", tag="ML",
        prompt="""`TrainConfig` inherits from `BaseConfig`, whose fields have defaults, and adds a required `dataset` field. Defining it fails with `TypeError:
        non-default argument 'dataset' follows default argument`. Fix it without giving `dataset` a default, so that calls use keyword arguments.""",
        code="""
        from dataclasses import dataclass

        @dataclass
        class BaseConfig:
            seed: int = 0
            device: str = "cpu"

        @dataclass
        class TrainConfig(BaseConfig):
            dataset: str
            epochs: int = 3
        """,
        tests="""
        c = TrainConfig(dataset="tickets.jsonl", epochs=5)
        assert (c.dataset, c.epochs, c.seed, c.device) == ("tickets.jsonl", 5, 0, "cpu")
        assert TrainConfig(dataset="x", seed=42).seed == 42
        try:
            TrainConfig()
            assert False, "dataset is required"
        except TypeError:
            pass
        """,
        hints=["Make the fields keyword-only: `@dataclass(kw_only=True)` on the subclass (and, for consistency, the base)."],
        solution="""
        from dataclasses import dataclass

        @dataclass(kw_only=True)
        class BaseConfig:
            seed: int = 0
            device: str = "cpu"

        @dataclass(kw_only=True)
        class TrainConfig(BaseConfig):
            dataset: str
            epochs: int = 3
        """,
        why="""The generated `__init__` lists the base's fields first, then the subclass's, and Python forbids a parameter without a default after parameters with
        defaults, so `dataset` could not come after `seed` and `device`. Keyword-only parameters have no positional order, so the restriction disappears:
        `dataset` stays required, and every call names its arguments, which for configs with many fields is clearer anyway (`TrainConfig(dataset=...,
        epochs=5)` cannot silently swap two numbers). `KW_ONLY` (a pseudo-field) makes only the fields after it keyword-only, when some should stay
        positional."""),
    write("Nested dataclasses from and to dicts", "medium", tag="ML",
        prompt="""Write dataclasses `Metric(name: str, value: float)` and `Run(run_id: str, params: dict[str, float], metrics: list[Metric] = [] via a factory)`.
        Add a classmethod `Run.from_dict(data)` that builds the nested objects from a dict like `asdict` produces (raising `KeyError` naming missing keys),
        a method `to_json()` using `asdict` and `json.dumps(sort_keys=True)`, and a method `best(name)` returning the highest value of a metric or `None`.""",
        code="""
        import json
        from dataclasses import dataclass, field, asdict

        @dataclass
        class Metric:
            pass

        @dataclass
        class Run:
            pass
        """,
        tests="""
        import json
        from dataclasses import asdict
        r = Run("r1", {"lr": 0.1}, [Metric("f1", 0.81), Metric("f1", 0.84), Metric("loss", 0.3)])
        data = asdict(r)
        again = Run.from_dict(data)
        assert again == r and isinstance(again.metrics[0], Metric)
        assert json.loads(r.to_json()) == data and r.to_json().startswith('{"metrics"')
        assert r.best("f1") == 0.84 and r.best("auc") is None
        assert Run.from_dict({"run_id": "r2", "params": {}}).metrics == []
        try:
            Run.from_dict({"params": {}})
            assert False
        except KeyError as e:
            assert "run_id" in str(e)
        """,
        hints=["`from_dict`: check `{\"run_id\", \"params\"} - data.keys()`, then `cls(data[\"run_id\"], dict(data[\"params\"]), [Metric(**m) for m in data.get(\"metrics\", [])])`."],
        solution="""
        import json
        from dataclasses import dataclass, field, asdict

        @dataclass
        class Metric:
            name: str
            value: float

        @dataclass
        class Run:
            run_id: str
            params: dict[str, float]
            metrics: list[Metric] = field(default_factory=list)

            @classmethod
            def from_dict(cls, data):
                missing = {"run_id", "params"} - data.keys()
                if missing:
                    raise KeyError(f"missing keys: {', '.join(sorted(missing))}")
                return cls(data["run_id"], dict(data["params"]), [Metric(**m) for m in data.get("metrics", [])])

            def to_json(self):
                return json.dumps(asdict(self), sort_keys=True)

            def best(self, name):
                values = [m.value for m in self.metrics if m.name == name]
                return max(values) if values else None
        """,
        why="""`asdict` converts nested dataclasses to plain dicts and lists recursively, which makes saving runs to JSON one line, but it is one-way: going back requires
        knowing which dicts should become `Metric`s, which is what `from_dict` encodes. The round trip test (`from_dict(asdict(r)) == r`) is the check
        every serialisable class should have. `Metric(**m)` unpacks each dict into the constructor, so an unexpected key in the data raises `TypeError`,
        a cheap guard against silently dropping fields. Experiment trackers store run records in exactly this shape; Pydantic does the reverse
        conversion automatically from the type hints (11.4)."""),
    choose("Serialising records: asdict or a direct dict", "medium", tag="Data work",
        prompt="Both turn 50,000 dataclass records into dicts for JSON. Which is faster?",
        setup="""import dataclasses
from dataclasses import dataclass

@dataclass
class Row:
    id: int
    label: str
    score: float

rows = [Row(i, "spam", 0.5) for i in range(50_000)]""",
        options={
            "a": "out = [dataclasses.asdict(r) for r in rows]",
            "b": "out = [{'id': r.id, 'label': r.label, 'score': r.score} for r in rows]",
        },
        answer="b",
        hints=["What does `asdict` do with every field value, in case it is a nested dataclass, list or dict?"],
        why="""`asdict` is general: for every field it checks whether the value is a dataclass, a list, a tuple or a dict, recurses into it, and deep-copies what it
        finds, so that the result shares nothing with the object. For flat records of strings and numbers that machinery is pure overhead; a dict built
        directly reads three attributes. Use `asdict` when you need its guarantees (nested dataclasses, an independent copy), and build dicts directly,
        or use `vars(row)` for a shallow copy of the fields, on hot paths such as serialising every row of an export."""),
    trace("Inspecting a dataclass", "medium",
        prompt="Fill in `r` after each marked line.",
        code="""
        import dataclasses
        from dataclasses import dataclass, field

        @dataclass
        class Inner:
            x: int

        @dataclass
        class Outer:
            name: str
            inner: Inner
            tags: list[str] = field(default_factory=list)
            cache: dict = field(default_factory=dict, repr=False, compare=False)

        o = Outer("a", Inner(1), ["t"])
        r = [f.name for f in dataclasses.fields(Outer)]  # row: "field names"
        r = dataclasses.asdict(o)  # row: "asdict"
        r = dataclasses.astuple(o)  # row: "astuple"
        r = repr(dataclasses.replace(o, name="b"))  # row: "replace"
        r = o == Outer("a", Inner(1), ["t"], cache={"k": 1})  # row: "compare=False"
        """,
        trace_vars=["r"],
        hints=["`asdict` and `astuple` recurse into nested dataclasses; `repr=False` hides a field from the repr; `compare=False` ignores it in `==`."],
        why="""`fields` lists all fields in declaration order, including hidden ones. `asdict` turns the nested `Inner` into a dict and includes every field;
        `astuple` does the same with tuples. `replace` builds a new instance whose repr leaves out `cache`. The comparison ignores `cache`, so instances
        that differ only in their cache are equal."""),
    fix("Sorting that uses the wrong field", "medium", tag="ML",
        prompt="""`Candidate` uses `order=True` so results can be sorted, but `sorted(candidates)` sorts by `name` instead of by `score`, and ties should then go by
        `name`. Fix the class so the generated ordering compares by score first, then name, without changing the constructor's argument order
        (`Candidate(name, score, meta)`), and so that `meta` is ignored by comparisons.""",
        code="""
        from dataclasses import dataclass, field

        @dataclass(order=True)
        class Candidate:
            name: str
            score: float
            meta: dict = field(default_factory=dict)
        """,
        tests="""
        cs = [Candidate("b", 0.5), Candidate("a", 0.9), Candidate("c", 0.5, {"x": 1})]
        assert [c.name for c in sorted(cs)] == ["b", "c", "a"]
        assert [c.name for c in sorted(cs, reverse=True)] == ["a", "c", "b"]
        assert Candidate("a", 0.9) == Candidate("a", 0.9, {"note": "differs"})
        assert repr(Candidate("a", 1.0)) == "Candidate(name='a', score=1.0, meta={})"
        """,
        hints=["Add a first field `sort_key: tuple = field(init=False, repr=False)` set in `__post_init__` to `(self.score, self.name)`; mark the other fields `compare=False`."],
        solution="""
        from dataclasses import dataclass, field

        @dataclass(order=True)
        class Candidate:
            sort_key: tuple = field(init=False, repr=False)
            name: str = field(compare=False)
            score: float = field(compare=False)
            meta: dict = field(default_factory=dict, compare=False)

            def __post_init__(self):
                self.sort_key = (self.score, self.name)
        """,
        why="""`order=True` compares fields as a tuple **in declaration order**, so the first field, `name`, decided the order. The documented pattern is a hidden first
        field holding the sort key, computed in `__post_init__` and excluded from `__init__` and the repr, while the real fields are marked
        `compare=False`. Equality then also uses only the key, which is consistent: two candidates with the same score and name are equal whatever their
        metadata. Since `sort_key` has no default and comes first, the others still follow the non-default-first rule (the later fields have no defaults
        either). For one-off sorts, `sorted(cs, key=lambda c: (c.score, c.name))` is simpler; `order=True` is for types whose natural order is used
        everywhere."""),
    write("Frozen chunks for deduplication", "medium", tag="RAG",
        prompt="""Write a frozen dataclass `Chunk(doc_id: str, text: str, position: int = 0)` that normalises `text` in `__post_init__` (strip and collapse inner
        whitespace to single spaces) and rejects empty text and negative positions with `ValueError`. Add a property `length` (number of characters) and a
        function `dedupe(chunks)` returning the chunks without duplicates (same doc, normalised text and position), keeping the first occurrence and the
        order.""",
        code="""
        from dataclasses import dataclass

        @dataclass(frozen=True)
        class Chunk:
            pass

        def dedupe(chunks):
            pass
        """,
        tests="""
        a = Chunk("faq", "  Refunds   take 5 days. ")
        assert a.text == "Refunds take 5 days." and a.length == 20
        chunks = [a, Chunk("faq", "Refunds take 5 days."), Chunk("faq", "Refunds take 5 days.", 1), Chunk("terms", "No refunds.")]
        assert dedupe(chunks) == [a, chunks[2], chunks[3]]
        assert len(set(chunks)) == 3
        for bad in [("x", "   "), ("x", "ok", -1)]:
            try:
                Chunk(*bad)
                assert False, bad
            except ValueError:
                pass
        """,
        hints=["`object.__setattr__(self, \"text\", \" \".join(self.text.split()))` in `__post_init__`.", "`dict.fromkeys(chunks)` keeps the first of equal (hashable) items, in order."],
        solution="""
        from dataclasses import dataclass

        @dataclass(frozen=True)
        class Chunk:
            doc_id: str
            text: str
            position: int = 0

            def __post_init__(self):
                normalised = " ".join(self.text.split())
                if not normalised:
                    raise ValueError("chunk text must not be empty")
                if self.position < 0:
                    raise ValueError(f"position must not be negative, got {self.position}")
                object.__setattr__(self, "text", normalised)

            @property
            def length(self):
                return len(self.text)

        def dedupe(chunks):
            return list(dict.fromkeys(chunks))
        """,
        why="""Normalising in `__post_init__` means equality and hashing see the cleaned text, so two chunks that differ only in whitespace are the same chunk; that is
        what lets `dict.fromkeys` (4.5) remove duplicates in one line, keeping the first of each and the original order. Being frozen is what makes the
        generated `__hash__` safe: the fields that define identity can never change after construction. Properties work on dataclasses as on any class
        (9.3). Deduplicating chunks before embedding saves cost and keeps repeated boilerplate (footers, disclaimers) from flooding retrieval results."""),
    predict("InitVar, init=False and repr=False", "medium",
        code="""
        from dataclasses import dataclass, field, InitVar, fields

        @dataclass
        class Account:
            user: str
            raw_key: InitVar[str]
            key_hint: str = field(init=False)
            secret: str = field(default="", repr=False)

            def __post_init__(self, raw_key):
                self.key_hint = raw_key[:4] + "..."

        a = Account("ana", "sk-123456")
        print(a, a.key_hint)
        print([f.name for f in fields(Account)], hasattr(a, "raw_key"))
        b = Account("bo", "sk-999", secret="s3")
        print(b, b.secret)
        """,
        hints=["An `InitVar` is a constructor argument passed to `__post_init__`, not stored. `init=False` fields are not constructor arguments."],
        why="""`raw_key` goes to `__init__` and on to `__post_init__`, which derives `key_hint` from it, but it is not a field: it is not stored, not in the repr and not
        listed by `fields`, a good way to accept a secret and keep only a harmless hint. `key_hint` is computed rather than passed. `secret` is a normal
        field that the repr hides, so it can be set and read, but never appears in a log line that prints the object."""),
)

section("hard", "Hard",
    write("Flatten and rebuild nested configs", "hard", tag="ML",
        prompt="""Experiment trackers store configs as flat `"section.field": value` dicts. For nested dataclasses, write `flatten(obj)` returning such a dict (nested
        dataclass fields joined with dots, 6.2) and `unflatten(cls, flat)` rebuilding an instance, converting string values to the field's annotated type
        when the field is `int`, `float` or `bool` (`"true"/"false"`), so that values typed on a command line work. Missing keys use the field defaults;
        unknown keys raise `KeyError`. Use `dataclasses.fields` and `typing.get_type_hints`.""",
        code="""
        import dataclasses, typing
        from dataclasses import dataclass, field

        def flatten(obj, prefix=""):
            pass

        def unflatten(cls, flat):
            pass
        """,
        tests="""
        from dataclasses import dataclass, field

        @dataclass
        class Optim:
            lr: float = 0.001
            momentum: float = 0.9

        @dataclass
        class Model:
            name: str = "small"
            layers: int = 2
            dropout: bool = False

        @dataclass
        class Config:
            model: Model = field(default_factory=Model)
            optim: Optim = field(default_factory=Optim)
            seed: int = 0

        c = Config(Model("large", 4), Optim(lr=0.01))
        flat = flatten(c)
        assert flat == {"model.name": "large", "model.layers": 4, "model.dropout": False, "optim.lr": 0.01, "optim.momentum": 0.9, "seed": 0}
        assert unflatten(Config, flat) == c
        cli = {"model.layers": "8", "optim.lr": "3e-4", "model.dropout": "true", "seed": "7"}
        assert unflatten(Config, cli) == Config(Model("small", 8, True), Optim(lr=0.0003), seed=7)
        try:
            unflatten(Config, {"model.layerz": "3"})
            assert False
        except KeyError as e:
            assert "model.layerz" in str(e)
        """,
        hints=["`flatten`: for each field, if the value is a dataclass instance (`dataclasses.is_dataclass`), recurse with `prefix + name + \".\"`.",
               "`unflatten`: group keys by their first part; for a field whose type is a dataclass, recurse with the sub-dict; otherwise convert and assign. Track used keys to detect unknown ones."],
        solution="""
        import dataclasses, typing
        from dataclasses import dataclass, field


        def flatten(obj, prefix=""):
            out = {}
            for f in dataclasses.fields(obj):
                value = getattr(obj, f.name)
                if dataclasses.is_dataclass(value):
                    out.update(flatten(value, prefix + f.name + "."))
                else:
                    out[prefix + f.name] = value
            return out


        def _convert(value, hint):
            if not isinstance(value, str) or hint is str:
                return value
            if hint is bool:
                if value.lower() in ("true", "false"):
                    return value.lower() == "true"
                raise ValueError(f"not a bool: {value!r}")
            if hint in (int, float):
                return hint(value)
            return value


        def unflatten(cls, flat, _prefix=""):
            hints = typing.get_type_hints(cls)
            names = {f.name for f in dataclasses.fields(cls)}
            if not _prefix:
                for key in flat:
                    head = key.split(".", 1)[0]
                    if head not in names:
                        raise KeyError(f"unknown config key: {key}")
            kwargs = {}
            for f in dataclasses.fields(cls):
                key = _prefix + f.name
                hint = hints[f.name]
                if dataclasses.is_dataclass(hint):
                    sub_names = {g.name for g in dataclasses.fields(hint)}
                    for k in flat:
                        if k.startswith(key + ".") and k[len(key) + 1:].split(".", 1)[0] not in sub_names:
                            raise KeyError(f"unknown config key: {k}")
                    if any(k.startswith(key + ".") for k in flat):
                        kwargs[f.name] = unflatten(hint, flat, key + ".")
                elif key in flat:
                    kwargs[f.name] = _convert(flat[key], hint)
            return cls(**kwargs)
        """,
        why="""`dataclasses.fields` and the type hints are all a generic tool needs: `flatten` walks the fields and recurses into nested dataclasses, producing the flat
        keys that trackers like MLflow and Weights & Biases expect, and `unflatten` uses each field's annotated type to decide whether to recurse (a
        dataclass) or to convert (a string from the command line to `int`, `float` or `bool`). Fields not present keep their defaults, because they are
        simply not passed to the constructor, and unknown keys are rejected so that a typo like `model.layerz=3` fails instead of being silently ignored,
        the most common way hyperparameter overrides go wrong. This is the core of what configuration libraries such as Hydra and OmegaConf structured
        configs, and `simple_parsing`, do with dataclasses."""),
    fix("Read the code: a dataclass with hidden traps", "hard", tag="RAG",
        prompt="""`IndexEntry` objects are kept in a set to avoid indexing the same document twice. Documents re-indexed after an edit are not found in the set, two
        entries for the same document compare unequal because of a timestamp, and `normalised_title` is wrong after a title change. Read it, find the bugs and
        fix them: identity is `(doc_id, version)`; `indexed_at` is metadata; the title is normalised once at creation and entries never change after
        creation.""",
        code="""
        from dataclasses import dataclass, field


        @dataclass(unsafe_hash=True)
        class IndexEntry:
            doc_id: str
            version: int
            title: str
            indexed_at: float = 0.0
            normalised_title: str = field(init=False)

            def __post_init__(self):
                self.normalised_title = self.title.strip().lower()
        """,
        tests="""
        import dataclasses
        seen = set()
        a = IndexEntry("faq", 1, "  Refund Policy ", indexed_at=100.0)
        seen.add(a)
        assert IndexEntry("faq", 1, "Refund Policy", indexed_at=200.0) in seen
        assert IndexEntry("faq", 2, "Refund Policy") not in seen
        assert a.normalised_title == "refund policy"
        try:
            a.title = "Changed"
            assert False, "entries must be immutable"
        except dataclasses.FrozenInstanceError:
            pass
        b = dataclasses.replace(a, title="New Title", version=2)
        assert b.normalised_title == "new title" and b.version == 2 and a in seen
        """,
        hints=["Make it `frozen=True` (which also gives a safe `__hash__`) and drop `unsafe_hash`.",
               "Mark `title`, `indexed_at` and `normalised_title` with `compare=False`; set `normalised_title` with `object.__setattr__`."],
        solution="""
        from dataclasses import dataclass, field


        @dataclass(frozen=True)
        class IndexEntry:
            doc_id: str
            version: int
            title: str = field(compare=False)
            indexed_at: float = field(default=0.0, compare=False)
            normalised_title: str = field(init=False, compare=False)

            def __post_init__(self):
                object.__setattr__(self, "normalised_title", self.title.strip().lower())
        """,
        why="""Three bugs. **Identity was every field**: equality and the hash included `title`, `indexed_at` and `normalised_title`, so the same document indexed at a
        different time (or with a different title spelling) counted as new; marking metadata `compare=False` makes identity exactly `(doc_id, version)`,
        and both `__eq__` and `__hash__` follow. **`unsafe_hash` on a mutable class**: the hash was computed from fields that could change, so changing a
        title after adding the entry to a set left it in the wrong bucket, unfindable. **A derived field that went stale**: `normalised_title` was
        computed once in `__post_init__` but `title` could be reassigned later. `frozen=True` fixes the last two at once: nothing changes after
        creation, so the generated hash is safe and the derived value cannot drift, and `replace` builds a corrected copy that recomputes it. The
        normalisation must then use `object.__setattr__`."""),
    write("Diff two configs", "hard", tag="ML",
        prompt="""Write `diff(a, b)` for two instances of the same dataclass (raise `TypeError` otherwise) returning a dict of the fields that differ, as dotted paths
        for nested dataclasses, mapping to `(old, new)` pairs. Fields marked `compare=False` are ignored. Lists and dicts are compared by value and reported
        whole. Use `dataclasses.fields`.""",
        code="""
        import dataclasses

        def diff(a, b, prefix=""):
            pass
        """,
        tests="""
        from dataclasses import dataclass, field

        @dataclass
        class Optim:
            lr: float = 0.001
            schedule: list[int] = field(default_factory=list)

        @dataclass
        class Config:
            model: str = "small"
            optim: Optim = field(default_factory=Optim)
            notes: str = field(default="", compare=False)

        base = Config()
        new = Config(model="large", optim=Optim(lr=0.01, schedule=[10, 20]), notes="tried bigger")
        assert diff(base, new) == {"model": ("small", "large"), "optim.lr": (0.001, 0.01), "optim.schedule": ([], [10, 20])}
        assert diff(base, Config(notes="only notes")) == {}
        try:
            diff(base, Optim())
            assert False
        except TypeError:
            pass
        """,
        hints=["Iterate `dataclasses.fields(a)`, skip `not f.compare`, recurse when both values are dataclass instances, else compare with `!=`."],
        solution="""
        import dataclasses

        def diff(a, b, prefix=""):
            if type(a) is not type(b) or not dataclasses.is_dataclass(a):
                raise TypeError(f"cannot diff {type(a).__name__} with {type(b).__name__}")
            changes = {}
            for f in dataclasses.fields(a):
                if not f.compare:
                    continue
                old, new = getattr(a, f.name), getattr(b, f.name)
                path = prefix + f.name
                if dataclasses.is_dataclass(old) and dataclasses.is_dataclass(new) and type(old) is type(new):
                    changes.update(diff(old, new, path + "."))
                elif old != new:
                    changes[path] = (old, new)
            return changes
        """,
        why="""Experiment comparison ("what changed between run 12 and run 13?") is mostly a structural diff of configs, and dataclass metadata makes it generic:
        `fields()` gives every field and its `compare` flag, so notes and timestamps marked `compare=False` are skipped automatically, matching what the
        generated `__eq__` considers. Recursing into nested dataclasses gives precise dotted paths instead of "the whole optimiser config changed". Lists
        are compared by value and reported whole, which is the useful granularity for schedules and layer sizes. Tools such as MLflow's run comparison and
        `deepdiff` provide richer versions."""),
    predict("asdict copies, equality across types", "hard",
        code="""
        import dataclasses
        from dataclasses import dataclass, field

        @dataclass
        class A:
            tags: list[str] = field(default_factory=list)

        @dataclass
        class B:
            tags: list[str] = field(default_factory=list)

        a = A(["x"])
        d = dataclasses.asdict(a)
        d["tags"].append("y")
        print(a.tags, d)
        print(A(["x"]) == B(["x"]), A(["x"]) == A(["x"]), dataclasses.astuple(a) == (["x"],))
        try:
            hash(A())
        except TypeError as e:
            print("TypeError:", e)
        print(dataclasses.is_dataclass(A), dataclasses.is_dataclass(a), dataclasses.is_dataclass(dict))
        """,
        hints=["`asdict` deep-copies values. The generated `__eq__` compares only instances of the same class. A non-frozen dataclass with `eq=True` is unhashable."],
        why="""`asdict` builds new lists, so appending to the dict's list leaves the dataclass unchanged. Instances of two different dataclasses are never equal, even
        with identical fields, because the generated `__eq__` returns `NotImplemented` for other classes; `astuple` gives a plain tuple, which compares
        by value. A regular (mutable) dataclass defines `__eq__` and therefore has `__hash__ = None` (9.2), so hashing it fails. `is_dataclass` accepts
        both the class and its instances."""),
)

section("interview", "Interview questions",
    explain("What does `@dataclass` generate, and when would you not use it?", "medium", tag="Interview",
        why="""From the annotated class attributes it generates `__init__` (fields in declaration order, with defaults and `default_factory`), `__repr__` and `__eq__`;
        with options, ordering methods (`order=True`), immutability plus `__hash__` (`frozen=True`), `__slots__` (`slots=True`) and keyword-only
        parameters (`kw_only=True`); `__post_init__` hooks into construction for validation and derived fields, and `fields`, `asdict`, `astuple` and
        `replace` work with any dataclass. Do not use it when you need validation or conversion of untrusted input (use Pydantic), when the object is
        mostly behaviour with internal state rather than data (a client, a cache: write a normal class), when the data should stay a plain dict for an
        API (TypedDict), or for huge numbers of records where columnar structures (DataFrames, arrays) are far more efficient."""),
    explain("Explain the hashing rules of dataclasses: `eq`, `frozen` and `unsafe_hash`.", "medium", tag="Interview",
        why="""With the default `eq=True` and `frozen=False`, a dataclass defines value-based `__eq__` and sets `__hash__` to `None`, so instances are unhashable: a mutable
        object whose equality depends on its fields must not live in a set, since changing a field would break the set. With `frozen=True` (and `eq=True`),
        fields cannot be reassigned, so the dataclass generates `__hash__` from the same fields as `__eq__` (those with `compare=True`), and instances work
        as set members and dict keys. `unsafe_hash=True` forces a field-based hash on a mutable dataclass; it is only correct if the compared fields are
        never changed while the object is stored, which is easy to violate. `eq=False` keeps identity-based equality and hashing from `object`. Use
        `compare=False` on fields that should not affect identity, such as timestamps or caches."""),
    explain("How would you model configuration for ML experiments, and why?", "hard", tag="Interview",
        why="""Use typed, nested, structured objects instead of loose dicts: one dataclass (or Pydantic model) per component (data, model, optimiser, training,
        evaluation), composed into a root config, with types and defaults in one place. Make configs immutable (frozen) so a run cannot change its own
        settings halfway, and derive variants with `replace` or overrides; validate values when the config is built (ranges, allowed choices with `Literal`),
        failing before any expensive work starts. Support overrides from the command line or files by flattening to dotted keys and converting strings to the
        annotated types, rejecting unknown keys so typos fail. Serialise the fully resolved config (`asdict` to JSON or YAML) and log it with every run,
        together with the code version and data version, so results are reproducible, and diff configs to explain differences between runs. Libraries such
        as Hydra and OmegaConf structured configs, or Pydantic settings, implement these patterns; at the boundary where configs are loaded from files or
        environment variables, Pydantic's validation and error messages are especially valuable."""),
)

recap(
    "`@dataclass` generates `__init__`, `__repr__` and `__eq__` from annotated fields; hints are not validated.",
    "Mutable defaults need `field(default_factory=list)`; `field()` also offers `repr=False`, `compare=False`, `init=False`, `kw_only` and `metadata`.",
    "`__post_init__` validates, normalises and computes `init=False` fields; `InitVar` passes construction-only values.",
    "`frozen=True` makes instances immutable and hashable; `replace` builds validated copies; `order=True` compares fields in declaration order; `slots=True` saves memory.",
    "`fields`, `asdict` and `astuple` make generic tools possible; use `kw_only` for inheritance with defaults, and Pydantic when input must be validated.",
)
