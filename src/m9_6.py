from lesson import *

lesson(
    id="m9-6", num="9.6", title="Class methods and constructors",
    intro="The three kinds of methods: instance methods, `classmethod`s that receive the class, and `staticmethod`s that "
          "receive nothing. Alternative constructors such as `from_dict` and `from_env` that keep working for subclasses, "
          "class-level state, `__new__` and when it is needed, and copying your own objects with `__copy__` and "
          "`__deepcopy__`. Applied to configs, messages, prompts and experiments.",
    desc="`classmethod`, `staticmethod`, alternative constructors, copying objects.",
    keys="classmethod staticmethod cls alternative constructor from_dict from_json from_env factory class state __new__ __init__ interning singleton copy deepcopy __copy__ __deepcopy__ memo clone",
)

term("classmethod", "A method that receives the class (`cls`) instead of an instance. Used for alternative constructors and class-level operations.")
term("staticmethod", "A function placed in a class's namespace that receives neither the instance nor the class.")
term("Alternative constructor", "A classmethod such as `Config.from_dict(d)` that builds an instance from another kind of input and returns `cls(...)`.")

section("kinds", "Three kinds of methods",
    p("""An ordinary method receives the **instance** as its first argument (`self`, 9.1). Two decorators change what the method receives.
    `@classmethod` makes it receive the **class** instead, conventionally named `cls`, whether you call it on the class or on an instance.
    `@staticmethod` makes it receive **nothing** extra: it is a plain function that happens to live in the class's namespace. Both are
    descriptors (9.3) that change how the method is bound when you access it."""),
    ex("""
    class Model:
        default_name = "small"

        def __init__(self, name):
            self.name = name

        def describe(self):                       # instance method: gets self
            return f"instance of {type(self).__name__} named {self.name}"

        @classmethod
        def default(cls):                         # class method: gets the class
            return cls(cls.default_name)

        @staticmethod
        def is_valid_name(name):                  # static method: gets nothing
            return name.isidentifier() and name.islower()

    class LargeModel(Model):
        default_name = "large"

    print(Model.default().describe())
    print(LargeModel.default().describe())
    print(Model.is_valid_name("small"), Model("x").is_valid_name("Big Model"))
    m = Model("tiny")
    print(m.default().name, type(Model.__dict__["default"]).__name__)
    """, "three_kinds.py"),
    p("""`LargeModel.default()` returned a `LargeModel` named "large" although `default` is defined only on `Model`: because it receives `cls`,
    it builds an instance of whichever class it was called on, and reads that class's `default_name`. Calling a classmethod on an instance
    (`m.default()`) still passes the class. A staticmethod is called the same way from the class or an instance and never sees either;
    use one for a helper that belongs with the class conceptually but needs no state, such as a validation function. If it is not closely
    tied to the class, a plain module-level function is simpler and easier to test."""),
)

section("constructors", "Alternative constructors",
    p("""A class has one `__init__`, but data arrives in many forms: a dict from JSON, environment variables, a file, a database row, an API
    response. The idiomatic solution is a set of **alternative constructors**: classmethods named `from_<source>` that parse the input,
    validate it and return `cls(...)`. The standard library uses this everywhere: `dict.fromkeys`, `datetime.fromisoformat`,
    `int.from_bytes`, `pandas.DataFrame.from_records`. Keeping `__init__` simple (just the fields) and putting parsing in named
    constructors makes each input path explicit and testable."""),
    ex("""
    import json

    class Message:
        ROLES = ("system", "user", "assistant")

        def __init__(self, role, content):
            if role not in self.ROLES:
                raise ValueError(f"bad role {role!r}")
            self.role, self.content = role, content

        def __repr__(self):
            return f"{type(self).__name__}({self.role!r}, {self.content!r})"

        @classmethod
        def from_dict(cls, data):
            return cls(data["role"], data["content"])

        @classmethod
        def from_json(cls, text):
            return cls.from_dict(json.loads(text))

        @classmethod
        def user(cls, content):
            return cls("user", content)

        def to_dict(self):
            return {"role": self.role, "content": self.content}

    m = Message.from_json('{"role": "assistant", "content": "Five days."}')
    print(m, Message.user("Refund?"), Message.from_dict(m.to_dict()).to_dict() == m.to_dict())
    """, "alt_constructors.py"),
    p("""The constructors chain: `from_json` parses and delegates to `from_dict`, which delegates to `cls(...)`, so validation in `__init__`
    applies to every path. Writing `cls(...)` instead of `Message(...)` is the important detail: a subclass, `class ToolMessage(Message)`,
    inherits `from_dict` and gets `ToolMessage` instances from it. Hard-coding the class name breaks that silently, returning base-class
    objects from a subclass's constructor (problem 3). That is also why alternative constructors are classmethods and not staticmethods: a
    staticmethod would have no `cls` to call."""),
)

section("classstate", "Class-level state and factories",
    p("""Classmethods are also the natural home for operations on **class-level state**: a registry of subclasses, a count of created
    instances, a cache of shared resources, a default configuration. Inside a classmethod, `cls` is the class the method was called on,
    which can be a subclass, so the choice between `cls.counter` and `Base.counter` matters: `cls.counter += 1` on a subclass reads the
    inherited value and **creates** a separate class attribute on the subclass (the shadowing rule of 9.1, applied to classes), while
    `Base.counter += 1` always updates the shared one."""),
    ex("""
    class Connection:
        _pool = {}                                  # shared by every class in the hierarchy
        created = 0

        def __init__(self, url):
            self.url = url
            type(self).created += 1                 # meant to count per class: see the output

        @classmethod
        def get(cls, url):
            key = (cls.__name__, url)
            if key not in Connection._pool:
                Connection._pool[key] = cls(url)
            return Connection._pool[key]

    class ReadReplica(Connection):
        pass

    a = Connection.get("db://main")
    b = Connection.get("db://main")
    r = ReadReplica.get("db://main")
    print(a is b, type(r).__name__, r is a)
    print(Connection.created, ReadReplica.created, sorted(k[0] for k in Connection._pool))
    """, "class_state.py"),
    p("""Look at the second line of output: `ReadReplica.created` is 2, although only one replica was made. On its first increment,
    `type(self).created` **read** the inherited `Connection.created` (already 1), added one, and stored 2 as a new attribute on
    `ReadReplica`. That is the shadowing rule biting at class level; to count each class from zero, keep the counts in one dict keyed by
    class, as problem 7 does."""),
    p("""`get` is a **factory**: callers ask the class for an object instead of constructing it, and the class decides whether to create a new one
    or return an existing one. Pools of database connections or HTTP clients, and caches of loaded models or tokenizers, are usually
    managed this way, often with a lock in threaded code (14.2)."""),
)

section("new", "`__new__`: controlling creation itself",
    p("""`Class(args)` actually performs two steps (9.1): **`__new__(cls, args)`** creates and returns the new object, then, if that object is an
    instance of `cls`, **`__init__(self, args)`** initialises it. You almost never override `__new__`. The two situations that need it are
    subclassing an **immutable** built-in (`str`, `int`, `tuple`), whose value must be set at creation because there is nothing to change
    afterwards, and controlling **whether** a new object is created at all, for example returning an existing instance (interning, singletons)."""),
    ex("""
    class Label(str):
        def __new__(cls, value):
            return super().__new__(cls, value.strip().lower())   # set the immutable value here

    class Severity:
        _instances = {}

        def __new__(cls, name):
            if name not in cls._instances:
                obj = super().__new__(cls)
                obj.name = name
                cls._instances[name] = obj
            return cls._instances[name]

    l = Label("  SPAM ")
    print(repr(l), isinstance(l, str), l.upper())
    print(Severity("high") is Severity("high"), Severity("low") is Severity("high"))
    """, "dunder_new.py"),
    p("""Beware one trap: when `__new__` returns an existing instance of the class, Python still calls `__init__` on it, every time. An `__init__`
    that resets attributes would wipe the cached object's state on each "creation", which is why the interning example sets its attribute
    in `__new__` and defines no `__init__` (problem 16). For most "one shared object" needs, a module-level instance or a cached factory
    function (8.3) is simpler than overriding `__new__`."""),
)

section("copying", "Copying your own objects",
    p("""`copy.copy(obj)` and `copy.deepcopy(obj)` (2.3) work on your classes too. By default, a shallow copy creates a new instance and copies the
    instance's `__dict__` **shallowly**: the new object has its own attribute dict, but the attribute values (lists, dicts, other objects)
    are shared with the original. A deep copy copies those values recursively. For most data-holding classes that default is fine. It
    becomes wrong when an object holds things that must **not** be duplicated, such as an API client, a database connection, a lock, a large
    read-only dataset or a loaded model, or when some state should be reset in a copy (counters, caches)."""),
    p("""Define **`__copy__(self)`** and **`__deepcopy__(self, memo)`** to take control. `__deepcopy__` receives `memo`, the dict that
    `deepcopy` uses to preserve shared references and handle cycles (2.3); pass it on when you deep-copy your own attributes:
    `copy.deepcopy(self.config, memo)`. A common pattern copies the configuration deeply, **shares** the expensive or unshareable resource,
    and starts the copy with fresh statistics (problem 10)."""),
    ex("""
    import copy

    class Client:                                   # stands in for an SDK client with a network session
        def __init__(self):
            self.session_id = "s-1"

    class Agent:
        def __init__(self, client, config):
            self.client = client
            self.config = config
            self.history = []

        def __deepcopy__(self, memo):
            new = Agent.__new__(Agent)              # create without calling __init__
            memo[id(self)] = new
            new.client = self.client                # share the client: never duplicate a connection
            new.config = copy.deepcopy(self.config, memo)
            new.history = []                        # a copy starts with a clean history
            return new

    a = Agent(Client(), {"model": "small", "stop": ["\\n\\n"]})
    a.history.append("hi")
    b = copy.deepcopy(a)
    b.config["stop"].append("User:")
    print(b.client is a.client, a.config["stop"], b.config["stop"], a.history, b.history)
    shallow = copy.copy(a)
    print(shallow.config is a.config, shallow.history is a.history)
    """, "custom_copy.py"),
    p("""`Agent.__new__(Agent)` builds an empty instance without running `__init__`, the usual way to construct a copy field by field. Registering
    the new object in `memo` before copying attributes is what makes cycles work (an attribute that points back to the agent finds the copy
    in `memo`). The shallow `copy.copy`, which uses the default behaviour here, shares everything, history included. scikit-learn's `clone()`
    takes a related approach: it builds a new estimator from the original's constructor parameters only, never copying fitted state."""),
)

section("warmup", "Warm-up",
    predict("Who receives what", "easy",
        code="""
        class Base:
            kind = "base"

            def show(self):
                return f"show({type(self).__name__})"

            @classmethod
            def make(cls):
                return f"make({cls.__name__}, {cls.kind})"

            @staticmethod
            def helper(x):
                return f"helper({x})"

        class Sub(Base):
            kind = "sub"

        s = Sub()
        print(s.show(), Sub.make(), s.make(), Base.make())
        print(Sub.helper(1), s.helper(2))
        try:
            Base.show()
        except TypeError:
            print("show needs an instance")
        """,
        hints=["A classmethod receives the class it was called on (or the instance's class); a staticmethod receives nothing."],
        why="""`show` sees the instance, of class `Sub`. `make` receives `Sub` both when called on the class and on the instance, and reads `Sub`'s own
        `kind`; on `Base` it receives `Base`. The staticmethod gets only the argument passed, from either place. Calling the instance method
        through the class without an instance leaves `self` missing, hence `TypeError`."""),
    write("Messages from dicts and back", "easy", tag="GenAI",
        prompt="""Write a class `Message(role, content)` with `__eq__` and `__repr__` (`Message('user', 'Hi')`), a classmethod `from_dict(data)` that
        raises `KeyError` naming any missing key (`"missing keys: content"`), strips the content, and ignores extra keys; a classmethod
        `from_pairs(pairs)` returning a list of messages from `(role, content)` tuples; and `to_dict()`.""",
        code="""
        class Message:
            pass
        """,
        tests="""
        m = Message.from_dict({"role": "user", "content": "  Refund? ", "id": 7})
        assert m == Message("user", "Refund?") and repr(m) == "Message('user', 'Refund?')"
        assert m.to_dict() == {"role": "user", "content": "Refund?"} and Message.from_dict(m.to_dict()) == m
        assert Message.from_pairs([("system", "Be brief."), ("user", "Hi")]) == [Message("system", "Be brief."), Message("user", "Hi")]
        try:
            Message.from_dict({"role": "user"})
            assert False
        except KeyError as e:
            assert "content" in str(e)
        """,
        hints=["Compute missing keys with a set difference before building; return `cls(data[\"role\"], data[\"content\"].strip())`."],
        solution="""
        class Message:
            def __init__(self, role, content):
                self.role = role
                self.content = content

            def __repr__(self):
                return f"{type(self).__name__}({self.role!r}, {self.content!r})"

            def __eq__(self, other):
                if not isinstance(other, Message):
                    return NotImplemented
                return (self.role, self.content) == (other.role, other.content)

            @classmethod
            def from_dict(cls, data):
                missing = {"role", "content"} - data.keys()
                if missing:
                    raise KeyError(f"missing keys: {', '.join(sorted(missing))}")
                return cls(data["role"], data["content"].strip())

            @classmethod
            def from_pairs(cls, pairs):
                return [cls(role, content) for role, content in pairs]

            def to_dict(self):
                return {"role": self.role, "content": self.content}
        """,
        why="""`__init__` stays a plain assignment of fields, and each input format gets a named constructor that does its own parsing. `from_dict` and
        `to_dict` are a round trip, which the test checks; that pair is how objects travel through JSON, databases and APIs. Checking all
        missing keys at once produces one useful message instead of failing on the first. `cls(...)` keeps both constructors correct for
        subclasses. Pydantic models provide exactly this pair as `model_validate(dict)` and `model_dump()` (11.4)."""),
    fix("A factory that ignores the subclass", "easy", tag="Data work",
        prompt="""`ProdConfig.from_dict(...)` returns a `Config`, not a `ProdConfig`, so the production defaults and the `is_prod` check are lost.
        Fix the alternative constructor.""",
        code="""
        class Config:
            defaults = {"debug": True, "workers": 1}

            def __init__(self, **values):
                self.values = {**self.defaults, **values}

            @classmethod
            def from_dict(cls, data):
                return Config(**data)

            def is_prod(self):
                return False

        class ProdConfig(Config):
            defaults = {"debug": False, "workers": 8}

            def is_prod(self):
                return True
        """,
        tests="""
        p = ProdConfig.from_dict({"workers": 16})
        assert type(p) is ProdConfig and p.is_prod() and p.values == {"debug": False, "workers": 16}
        c = Config.from_dict({})
        assert type(c) is Config and c.values == {"debug": True, "workers": 1}
        """,
        hints=["Use the class the method received: `cls(**data)`."],
        solution="""
        class Config:
            defaults = {"debug": True, "workers": 1}

            def __init__(self, **values):
                self.values = {**self.defaults, **values}

            @classmethod
            def from_dict(cls, data):
                return cls(**data)

            def is_prod(self):
                return False

        class ProdConfig(Config):
            defaults = {"debug": False, "workers": 8}

            def is_prod(self):
                return True
        """,
        why="""`from_dict` received `cls = ProdConfig` but ignored it and built the hard-coded base class, so the subclass's `defaults` and `is_prod` never
        applied: a silent bug, since a `Config` behaves almost like a `ProdConfig`. `cls(**data)` constructs whatever class the method was
        called on, so every subclass inherits a correct factory for free. The same rule holds inside instance methods that build new objects:
        use `type(self)(...)` rather than naming the class."""),
    predict("Copies of your own objects", "easy",
        code="""
        import copy

        class Run:
            def __init__(self, name, params):
                self.name = name
                self.params = params
                self.scores = []

        r = Run("baseline", {"lr": 0.1, "layers": [64, 32]})
        s = copy.copy(r)
        d = copy.deepcopy(r)
        s.name = "shallow"
        s.params["lr"] = 0.01
        d.params["layers"].append(16)
        s.scores.append(0.8)
        print(r.name, r.params, r.scores)
        print(d.params, d.scores, s.params is r.params, d.params is r.params)
        """,
        hints=["A shallow copy gets its own attribute dict but shares the values; a deep copy copies the values too."],
        why="""Rebinding `s.name` changes only the copy, because the copy has its own attribute dict. But `s.params` and `s.scores` are the **same** dict
        and list as the original's, so changing them through the shallow copy changes the original too (2.3). The deep copy has its own
        nested structures, so appending to its layers list leaves the original alone, and it was taken before `lr` changed, so it still holds
        0.1."""),
)

section("medium", "Medium",
    write("Settings from the environment", "medium", tag="GenAI",
        prompt="""Write a class `ModelSettings(model, temperature, max_tokens)` with a classmethod `from_env(environ, prefix="LLM_")` that reads
        `LLM_MODEL` (default `"small"`), `LLM_TEMPERATURE` (float, default 0.0) and `LLM_MAX_TOKENS` (int, default 512) from the `environ` dict,
        raising `ValueError` naming the variable for values that do not parse or are out of range (temperature 0 to 2, max_tokens positive).
        Add `with_overrides(**changes)` returning a **new** instance with some fields changed (unknown field names raise `TypeError`), and
        `__eq__`/`__repr__`.""",
        code="""
        class ModelSettings:
            pass
        """,
        tests="""
        s = ModelSettings.from_env({"LLM_MODEL": "large", "LLM_TEMPERATURE": "0.7", "HOME": "/root"})
        assert s == ModelSettings("large", 0.7, 512) and repr(s) == "ModelSettings(model='large', temperature=0.7, max_tokens=512)"
        assert ModelSettings.from_env({}) == ModelSettings("small", 0.0, 512)
        t = s.with_overrides(temperature=0.0)
        assert t == ModelSettings("large", 0.0, 512) and s.temperature == 0.7 and t is not s
        for env, var in [({"LLM_TEMPERATURE": "hot"}, "LLM_TEMPERATURE"), ({"LLM_TEMPERATURE": "3"}, "LLM_TEMPERATURE"), ({"LLM_MAX_TOKENS": "0"}, "LLM_MAX_TOKENS")]:
            try:
                ModelSettings.from_env(env)
                assert False, env
            except ValueError as e:
                assert var in str(e)
        try:
            s.with_overrides(temprature=1)
            assert False
        except TypeError:
            pass
        assert ModelSettings.from_env({"APP_MODEL": "x"}, prefix="APP_").model == "x"
        """,
        hints=["A small helper inside `from_env` can parse one variable with a converter and a default, raising `ValueError(f\"{name}: ...\")` on failure.",
               "`with_overrides` can build `{**vars(self), **changes}` after checking `changes.keys() <= vars(self).keys()`."],
        solution="""
        class ModelSettings:
            def __init__(self, model, temperature, max_tokens):
                if not 0 <= temperature <= 2:
                    raise ValueError(f"temperature must be in [0, 2], got {temperature}")
                if max_tokens < 1:
                    raise ValueError(f"max_tokens must be positive, got {max_tokens}")
                self.model = model
                self.temperature = temperature
                self.max_tokens = max_tokens

            def __repr__(self):
                return f"ModelSettings(model={self.model!r}, temperature={self.temperature}, max_tokens={self.max_tokens})"

            def __eq__(self, other):
                if not isinstance(other, ModelSettings):
                    return NotImplemented
                return vars(self) == vars(other)

            @classmethod
            def from_env(cls, environ, prefix="LLM_"):
                def read(name, convert, default):
                    key = prefix + name
                    if key not in environ:
                        return default
                    try:
                        return convert(environ[key])
                    except ValueError:
                        raise ValueError(f"{key}: cannot parse {environ[key]!r}") from None

                model = read("MODEL", str, "small")
                temperature = read("TEMPERATURE", float, 0.0)
                max_tokens = read("MAX_TOKENS", int, 512)
                try:
                    return cls(model, temperature, max_tokens)
                except ValueError as e:
                    var = prefix + ("TEMPERATURE" if "temperature" in str(e) else "MAX_TOKENS")
                    raise ValueError(f"{var}: {e}") from None

            def with_overrides(self, **changes):
                unknown = changes.keys() - vars(self).keys()
                if unknown:
                    raise TypeError(f"unknown settings: {sorted(unknown)}")
                return type(self)(**{**vars(self), **changes})
        """,
        why="""Environment variables are always strings, so `from_env` owns the parsing and turns every failure into an error that names the variable a
        person must fix; validation of ranges stays in `__init__`, so settings created any other way obey the same rules. The environment is
        passed in as a dict, so tests never touch the real `os.environ` (9.5), and the prefix makes the same class usable for several
        components. `with_overrides` returns a new object instead of mutating, so a per-request tweak cannot leak into shared settings (9.1),
        and it builds through `type(self)(...)`, keeping subclasses and validation. Pydantic's `BaseSettings` does all of this declaratively
        (11.4)."""),
    fix("A helper that receives self by accident", "medium", tag="Data work",
        prompt="""`Tokenizer.normalise` was meant to be a static helper, but called on an instance it receives the instance as `text` and fails.
        Fix the class so `normalise` works from the class and from instances, and `tokenize` uses it.""",
        code="""
        class Tokenizer:
            def __init__(self, stop_words):
                self.stop_words = set(stop_words)

            def normalise(text):
                return " ".join(text.lower().split())

            def tokenize(self, text):
                return [w for w in self.normalise(text).split() if w not in self.stop_words]
        """,
        tests="""
        t = Tokenizer(["the", "a"])
        assert t.tokenize("The  Refund policy") == ["refund", "policy"]
        assert Tokenizer.normalise("  A  B ") == "a b" and t.normalise("X") == "x"
        """,
        hints=["Without a decorator, a function in a class is an instance method: `self.normalise(text)` passes two arguments."],
        solution="""
        class Tokenizer:
            def __init__(self, stop_words):
                self.stop_words = set(stop_words)

            @staticmethod
            def normalise(text):
                return " ".join(text.lower().split())

            def tokenize(self, text):
                return [w for w in self.normalise(text).split() if w not in self.stop_words]
        """,
        why="""Every function defined in a class becomes an instance method unless decorated, so `self.normalise(text)` called it with the instance as the
        first argument and the text as a second, unexpected one: "takes 1 positional argument but 2 were given". `@staticmethod` stops the
        binding, so the function receives exactly the arguments written, from the class or an instance. Keeping a pure helper like this static
        (or a module function) also makes it trivial to test alone."""),
    write("Count instances per class", "medium", tag="ML",
        prompt="""Write a base class `Component` that counts created instances **per concrete class**, in one shared dict `Component._counts`
        (class name to count), updated in `__init__(self, name)`. Add a classmethod `count()` returning the count for the class it is called on
        (0 if none), and a classmethod `summary()` on the base returning a copy of the whole dict sorted by name. Subclasses `Embedder` and
        `Reranker` need no code of their own except `pass`.""",
        code="""
        class Component:
            pass

        class Embedder(Component):
            pass

        class Reranker(Component):
            pass
        """,
        tests="""
        Embedder("e1"); Embedder("e2"); Reranker("r1"); Component("base")
        assert Embedder.count() == 2 and Reranker.count() == 1 and Component.count() == 1
        assert Component.summary() == {"Component": 1, "Embedder": 2, "Reranker": 1}
        assert list(Component.summary()) == ["Component", "Embedder", "Reranker"]
        class Retriever(Component):
            pass
        assert Retriever.count() == 0 and Embedder("e3").name == "e3" and Embedder.count() == 3
        Component.summary()["Embedder"] = 99
        assert Embedder.count() == 3
        """,
        hints=["In `__init__`, update `Component._counts[type(self).__name__]`; in `count`, read `Component._counts.get(cls.__name__, 0)`."],
        solution="""
        class Component:
            _counts = {}

            def __init__(self, name):
                self.name = name
                key = type(self).__name__
                Component._counts[key] = Component._counts.get(key, 0) + 1

            @classmethod
            def count(cls):
                return Component._counts.get(cls.__name__, 0)

            @classmethod
            def summary(cls):
                return dict(sorted(Component._counts.items()))

        class Embedder(Component):
            pass

        class Reranker(Component):
            pass
        """,
        why="""One shared dict, deliberately written as `Component._counts` (never `self._counts` or `cls._counts` with assignment), holds all counts, and
        `type(self).__name__` picks the right key for every subclass without subclasses writing any code. `count` uses `cls` to answer for the
        class it was called on, so the same method serves every class in the hierarchy. `summary` returns a sorted copy, so callers cannot
        alter the counts. Counting created components like this is a cheap way to spot accidental re-creation of expensive objects (a model
        loaded per request instead of once)."""),
    choose("Deep-copy a large read-only matrix or share it", "medium", tag="ML",
        prompt="Both copy an experiment object that holds an embedding matrix of 2,000 x 50 floats and a small config; the code copies it 20 times. Which is faster?",
        setup="""import copy

class PlainExperiment:
    def __init__(self, matrix, config):
        self.matrix = matrix
        self.config = config

class SharingExperiment(PlainExperiment):
    def __deepcopy__(self, memo):
        new = SharingExperiment.__new__(SharingExperiment)
        new.matrix = self.matrix                       # read-only: share it
        new.config = copy.deepcopy(self.config, memo)
        return new

matrix = [[float(i * j % 7) for j in range(50)] for i in range(2000)]
plain = PlainExperiment(matrix, {"lr": 0.1, "tags": ["baseline"]})
sharing = SharingExperiment(matrix, {"lr": 0.1, "tags": ["baseline"]})""",
        options={
            "a": "copies = [copy.deepcopy(plain) for _ in range(20)]",
            "b": "copies = [copy.deepcopy(sharing) for _ in range(20)]",
        },
        answer="b",
        hints=["How many objects does the default `deepcopy` visit for the matrix?"],
        why="""The default `deepcopy` walks the matrix and builds 2,000 new lists, checking 100,000 floats along the way, on every copy. The custom
        `__deepcopy__` shares the matrix (the experiment treats it as read-only) and deep-copies only the small config. Copying should follow
        the data's meaning: duplicate what each copy may change, share what is immutable or too expensive to copy. If any copy might modify the
        matrix, sharing would be a bug, so the read-only rule must be real and documented."""),
    trace("Factories and the class they receive", "medium",
        prompt="Fill in `kind` and `registry` after each marked line.",
        code="""
        class Store:
            registry = []

            def __init__(self, url):
                self.url = url

            @classmethod
            def connect(cls, url):
                obj = cls(url)
                Store.registry.append(f"{cls.__name__}:{url}")
                return obj

        class Redis(Store):
            pass

        kind, registry = type(Store.connect("mem://")).__name__, list(Store.registry)  # row: "Store.connect"
        kind, registry = type(Redis.connect("redis://a")).__name__, list(Store.registry)  # row: "Redis.connect"
        kind, registry = type(Redis("x").connect("redis://b")).__name__, list(Store.registry)  # row: "via an instance"
        """,
        trace_vars=["kind", "registry"],
        hints=["`cls` is the class the method was called on; calling on an instance passes the instance's class."],
        why="""`connect` builds `cls(url)`, so it returns a `Store` from `Store` and a `Redis` from `Redis`, and records the class name. Called on a `Redis`
        **instance**, it still receives the class `Redis`. The registry is appended through `Store.registry`, one shared list, which is the
        deliberate use of a mutable class attribute."""),
    fix("A deep copy that shares what it should not", "medium", tag="ML",
        prompt="""`Trainer` holds a `model` (expensive, must be shared between copies), a `config` dict and a `history` list. Its `__deepcopy__`
        returns the same object, so changing a copy's config changes the original. Fix it: a deep copy must share `model`, deep-copy `config`,
        and start with an empty `history`.""",
        code="""
        import copy

        class Trainer:
            def __init__(self, model, config):
                self.model = model
                self.config = config
                self.history = []

            def __deepcopy__(self, memo):
                return self
        """,
        tests="""
        import copy
        model = object()
        t = Trainer(model, {"lr": 0.1, "schedule": [1, 2]})
        t.history.append(0.9)
        c = copy.deepcopy(t)
        c.config["schedule"].append(3)
        c.config["lr"] = 0.01
        assert c is not t and c.model is model and c.history == []
        assert t.config == {"lr": 0.1, "schedule": [1, 2]} and t.history == [0.9]
        pair = copy.deepcopy([t, t])
        assert pair[0] is pair[1] and pair[0] is not t
        """,
        hints=["Create the new object with `Trainer.__new__(Trainer)`, register it with `memo[id(self)] = new`, then fill each attribute.",
               "Pass `memo` to `copy.deepcopy(self.config, memo)`."],
        solution="""
        import copy

        class Trainer:
            def __init__(self, model, config):
                self.model = model
                self.config = config
                self.history = []

            def __deepcopy__(self, memo):
                new = type(self).__new__(type(self))
                memo[id(self)] = new
                new.model = self.model
                new.config = copy.deepcopy(self.config, memo)
                new.history = []
                return new
        """,
        why="""Returning `self` turned "deep copy" into "the same object", so a hyperparameter sweep that copies a trainer per run would have every run
        changing one shared config. The fixed version decides per attribute: share the model (copying it would waste memory or fail for
        objects holding GPU memory or file handles), deep-copy the config, reset the history. Registering the new object in `memo` before
        copying makes shared references inside one `deepcopy` call work: the list `[t, t]` is copied to two references to **one** new trainer,
        as the last test checks. `type(self).__new__(type(self))` keeps subclasses copying to their own class."""),
    write("Prompt templates from text", "medium", tag="GenAI",
        prompt="""Write a class `PromptTemplate(name, body)` with a classmethod `from_text(text)` that parses a header block and a body separated by a
        line containing only `---`: the header has `key: value` lines and must contain `name`; everything after `---` is the body (stripped).
        `variables` is a read-only property listing the `{placeholder}` names in the body in first-seen order. `render(**values)` fills them and
        raises `KeyError` listing missing variables (sorted) before formatting. Raise `ValueError` for text without a `---` line or without a
        name.""",
        code="""
        import re

        class PromptTemplate:
            pass
        """,
        tests="""
        text = "name: qa\\nversion: 2\\n---\\nAnswer using the context.\\nContext: {context}\\nQuestion: {question}\\n"
        t = PromptTemplate.from_text(text)
        assert t.name == "qa" and t.meta == {"name": "qa", "version": "2"} and t.variables == ["context", "question"]
        assert t.render(context="Refunds take 5 days.", question="How long?") == "Answer using the context.\\nContext: Refunds take 5 days.\\nQuestion: How long?"
        try:
            t.render(question="x")
            assert False
        except KeyError as e:
            assert "context" in str(e)
        for bad in ["name: x\\nno separator", "version: 1\\n---\\nbody"]:
            try:
                PromptTemplate.from_text(bad)
                assert False, bad
            except ValueError:
                pass
        assert PromptTemplate("x", "Hi {a} {b} {a}").variables == ["a", "b"]
        """,
        hints=["Split lines, find the index of the `---` line, parse the header lines with `partition(\":\")`.",
               "`re.findall(r\"\\{(\\w+)\\}\", body)` finds placeholders (5.5); dedupe with `dict.fromkeys`."],
        solution="""
        import re

        class PromptTemplate:
            def __init__(self, name, body, meta=None):
                self.name = name
                self.body = body
                self.meta = dict(meta) if meta else {"name": name}

            @classmethod
            def from_text(cls, text):
                lines = text.splitlines()
                if "---" not in [l.strip() for l in lines]:
                    raise ValueError("template needs a '---' line between header and body")
                sep = [l.strip() for l in lines].index("---")
                meta = {}
                for line in lines[:sep]:
                    key, _, value = line.partition(":")
                    if key.strip():
                        meta[key.strip()] = value.strip()
                if "name" not in meta:
                    raise ValueError("template header needs a name")
                body = "\\n".join(lines[sep + 1:]).strip()
                return cls(meta["name"], body, meta)

            @property
            def variables(self):
                return list(dict.fromkeys(re.findall(r"\\{(\\w+)\\}", self.body)))

            def render(self, **values):
                missing = sorted(set(self.variables) - values.keys())
                if missing:
                    raise KeyError(f"missing variables: {', '.join(missing)}")
                return self.body.format(**values)
        """,
        why="""The file format is parsed in one named constructor, and `__init__` accepts already-parsed parts, so templates can also be built directly in
        code or tests (the last assertion). Keeping the header as `meta` preserves information such as the version for logging which prompt
        produced an answer (8.P). `variables` is derived from the body, so it cannot drift. Checking missing variables before formatting gives
        one complete error instead of `str.format`'s first `KeyError`. A real template would also escape literal braces (`{{`), as 5.2 and 5.5
        discussed."""),
    predict("Classmethods, instances and __init__ signatures", "medium",
        code="""
        class Shape:
            def __init__(self, size):
                self.size = size

            @classmethod
            def unit(cls):
                return cls(1)

            def bigger(self):
                return type(self)(self.size * 2)

        class Square(Shape):
            def area(self):
                return self.size ** 2

        class Labelled(Shape):
            def __init__(self, size, label):
                super().__init__(size)
                self.label = label

        print(type(Square.unit()).__name__, Square.unit().bigger().area())
        try:
            Labelled.unit()
        except TypeError:
            print("Labelled.unit needs a label")
        print(type(Square(3).bigger()).__name__)
        """,
        hints=["`cls(1)` calls the subclass's own `__init__`, with whatever parameters it requires."],
        why="""`Square.unit()` builds a `Square`, and `bigger` uses `type(self)(...)`, so it also returns a `Square`, whose area is 4. A subclass that changes the
        constructor's required parameters breaks inherited factories: `Labelled.unit()` calls `Labelled(1)`, which is missing `label`. That
        is the substitution rule of 9.4 applied to constructors: if subclasses must keep working with `cls(...)`, they should keep the base's
        `__init__` signature (adding only optional parameters)."""),
)

section("hard", "Hard",
    write("Clone experiments safely", "hard", tag="ML",
        prompt="""Write a class `Experiment(name, config, dataset)` where `config` is a nested dict and `dataset` is a large shared object. Add: a
        classmethod `from_config(data, dataset)` that requires `"name"` and `"params"` keys (`KeyError` listing missing ones) and stores
        `params` as the config; `clone(name, **param_changes)` returning a new experiment that **shares** the dataset, has a deep-copied config
        with the changes applied at the top level of `params`, and starts with empty `results`; `__deepcopy__` with the same sharing rule; and
        `record(metric, value)` appending to `results`.""",
        code="""
        import copy

        class Experiment:
            pass
        """,
        tests="""
        import copy
        data = object()
        base = Experiment.from_config({"name": "base", "params": {"lr": 0.1, "layers": [64, 32]}}, data)
        base.record("f1", 0.81)
        b = base.clone("bigger", lr=0.05)
        b.config["layers"].append(16)
        assert (b.name, b.config, b.results, b.dataset is data) == ("bigger", {"lr": 0.05, "layers": [64, 32, 16]}, [], True)
        assert base.config == {"lr": 0.1, "layers": [64, 32]} and base.results == [("f1", 0.81)]
        d = copy.deepcopy(base)
        assert d.dataset is data and d.config == base.config and d.config is not base.config and d.results == []
        try:
            Experiment.from_config({"params": {}}, data)
            assert False
        except KeyError as e:
            assert "name" in str(e)
        try:
            base.clone("x", momentum=0.9)
            assert False
        except KeyError as e:
            assert "momentum" in str(e)
        """,
        hints=["Put the sharing rule in one place: `__deepcopy__`. Then `clone` can be `new = copy.deepcopy(self)`, then set the name and apply the changes.",
               "Reject changes to parameters that do not exist in `params` (a typo guard)."],
        solution="""
        import copy

        class Experiment:
            def __init__(self, name, config, dataset):
                self.name = name
                self.config = config
                self.dataset = dataset
                self.results = []

            @classmethod
            def from_config(cls, data, dataset):
                missing = {"name", "params"} - data.keys()
                if missing:
                    raise KeyError(f"missing keys: {', '.join(sorted(missing))}")
                return cls(data["name"], copy.deepcopy(data["params"]), dataset)

            def __deepcopy__(self, memo):
                new = type(self).__new__(type(self))
                memo[id(self)] = new
                new.name = self.name
                new.config = copy.deepcopy(self.config, memo)
                new.dataset = self.dataset
                new.results = []
                return new

            def clone(self, name, **param_changes):
                unknown = param_changes.keys() - self.config.keys()
                if unknown:
                    raise KeyError(f"unknown parameters: {', '.join(sorted(unknown))}")
                new = copy.deepcopy(self)
                new.name = name
                new.config.update(param_changes)
                return new

            def record(self, metric, value):
                self.results.append((metric, value))
        """,
        why="""Two constructors with distinct jobs: `from_config` turns external data into an experiment (copying the params so the caller's dict cannot
        change the experiment later), and `clone` derives a variant from an existing one. Both rely on one copying rule in `__deepcopy__`: the
        dataset is shared because copying it would multiply memory, the config is independent because variants change it, and results start
        empty because a variant has not run yet. Writing that rule once means `copy.deepcopy(exp)` from any other code (a sweep library, a test)
        behaves the same as `clone`. The unknown-parameter check stops a typo like `momentun=0.9` from silently creating a useless run. This is
        the shape of hyperparameter sweeps: one base experiment, many cheap clones."""),
    fix("Read the code: a document model", "hard", tag="RAG",
        prompt="""`Document` is created from JSON records with `from_json`, and `SourcedDocument` adds a `source` field. `SourcedDocument.from_json`
        returns plain `Document`s, a validation helper crashes, and documents created without tags share one tag list. Read it, find the bugs and
        fix them.""",
        code="""
        import json


        class Document:
            def __init__(self, id, text, tags=[]):
                self.id = id
                self.text = text
                self.tags = tags

            def check_text(text):
                if not text.strip():
                    raise ValueError("empty text")
                return text.strip()

            @classmethod
            def from_json(cls, line):
                data = json.loads(line)
                text = Document.check_text(data["text"])
                return Document(data["id"], text, data.get("tags", []))

            def extra(self):
                return {}


        class SourcedDocument(Document):
            def __init__(self, id, text, tags=None, source="unknown"):
                super().__init__(id, text, tags)
                self.source = source
        """,
        tests="""
        a = Document.from_json('{"id": 1, "text": " Refund policy "}')
        b = Document(2, "Reset password")
        a.tags.append("billing")
        assert a.text == "Refund policy" and a.tags == ["billing"] and b.tags == []
        s = SourcedDocument.from_json('{"id": 3, "text": "Window", "tags": ["faq"], "source": "help-centre"}')
        assert type(s) is SourcedDocument and s.source == "help-centre" and s.tags == ["faq"]
        assert SourcedDocument.from_json('{"id": 4, "text": "x"}').source == "unknown"
        try:
            Document.from_json('{"id": 5, "text": "   "}')
            assert False
        except ValueError:
            pass
        assert Document.check_text("  ok ") == "ok" and SourcedDocument(6, "y").tags == []
        """,
        hints=["`tags=[]` is a mutable default (2.4); `check_text` needs `@staticmethod`.",
               "`from_json` must build `cls(...)` and pass the extra keys a subclass accepts. One way: a hook `cls._extra_fields(data)` returning keyword arguments, overridden in the subclass."],
        solution="""
        import json


        class Document:
            def __init__(self, id, text, tags=None):
                self.id = id
                self.text = text
                self.tags = list(tags) if tags is not None else []

            @staticmethod
            def check_text(text):
                if not text.strip():
                    raise ValueError("empty text")
                return text.strip()

            @classmethod
            def _extra_fields(cls, data):
                return {}

            @classmethod
            def from_json(cls, line):
                data = json.loads(line)
                text = cls.check_text(data["text"])
                return cls(data["id"], text, data.get("tags"), **cls._extra_fields(data))


        class SourcedDocument(Document):
            def __init__(self, id, text, tags=None, source="unknown"):
                super().__init__(id, text, tags)
                self.source = source

            @classmethod
            def _extra_fields(cls, data):
                return {"source": data["source"]} if "source" in data else {}
        """,
        why="""Four bugs from this lesson. `from_json` built `Document(...)` by name, so the subclass's constructor produced base objects without a
        `source`; it must build `cls(...)`. Building the right class is not enough, though: the subclass needs its extra field from the JSON,
        so a classmethod hook, `_extra_fields`, lets each class say which extra keyword arguments it reads, while the base handles everything
        common. `check_text` lacked `@staticmethod`, so calling it on the class worked by accident but calling it on an instance would pass the
        instance as `text`. And `tags=[]` was a shared mutable default, so tagging one document tagged every document created without tags;
        `None` plus a copy of the caller's list fixes both sharing directions (9.1). The unused `extra` method was dead code and is removed."""),
    write("Interned labels with __new__", "hard", tag="ML",
        prompt="""Labels repeat millions of times in a dataset. Write a class `Label(name)` that returns **the same object** for the same normalised name
        (stripped, lower-cased): `Label("Spam ") is Label("spam")`. Use `__new__` with a class-level dict, make instances immutable (assigning any
        attribute after creation raises `AttributeError`), give them `__repr__` (`Label('spam')`), and add a classmethod `known()` returning the
        sorted names created so far and `clear()` (a classmethod) emptying the cache. Equality is identity, so `==` and `hash` need no change.""",
        code="""
        class Label:
            pass
        """,
        tests="""
        Label.clear()
        a, b, c = Label("Spam "), Label("spam"), Label("HAM")
        assert a is b and a is not c and repr(a) == "Label('spam')" and a.name == "spam"
        assert Label.known() == ["ham", "spam"] and {a, b, c} == {a, c} and a == Label(" SPAM")
        try:
            a.name = "eggs"
            assert False
        except AttributeError:
            pass
        try:
            a.other = 1
            assert False
        except AttributeError:
            pass
        Label.clear()
        assert Label.known() == [] and Label("spam") is not a
        """,
        hints=["In `__new__`, normalise, then look up the cache; create with `super().__new__(cls)` and set the name with `object.__setattr__` (9.3).",
               "Do not define `__init__`: it would run on every call, even for cached instances."],
        solution="""
        class Label:
            _cache = {}

            def __new__(cls, name):
                key = name.strip().lower()
                obj = cls._cache.get(key)
                if obj is None:
                    obj = super().__new__(cls)
                    object.__setattr__(obj, "name", key)
                    cls._cache[key] = obj
                return obj

            def __setattr__(self, name, value):
                raise AttributeError("Label is immutable")

            def __repr__(self):
                return f"Label({self.name!r})"

            @classmethod
            def known(cls):
                return sorted(cls._cache)

            @classmethod
            def clear(cls):
                cls._cache.clear()
        """,
        why="""`__new__` decides whether a new object is created at all: for a name it has seen, it returns the cached instance, so millions of rows share a
        handful of label objects and comparisons are identity checks. That is safe only because the objects are immutable, which
        `__setattr__` enforces (setting the name once through `object.__setattr__`). There is deliberately no `__init__`: Python calls
        `__init__` after `__new__` whenever the returned object is an instance of the class, **including cached ones**, so an initialiser would
        run again on every lookup. `sys.intern` (2.1) does the same for strings, and pandas' `category` dtype achieves the memory saving for whole
        columns. `clear` exists mainly for tests, so each test starts from an empty cache."""),
    predict("__new__, __init__ and cached instances", "hard",
        code="""
        class Conn:
            _pool = {}

            def __new__(cls, url):
                print(f"  __new__({url})")
                if url not in cls._pool:
                    cls._pool[url] = super().__new__(cls)
                return cls._pool[url]

            def __init__(self, url):
                print(f"  __init__({url})")
                self.url = url
                self.requests = 0

        a = Conn("db://x")
        a.requests = 5
        b = Conn("db://x")
        print(a is b, a.requests)

        class NotMine:
            def __new__(cls):
                return "a string"
            def __init__(self):
                print("never printed")

        print(NotMine())
        """,
        hints=["`__init__` runs whenever `__new__` returns an instance of the class, even an existing one; it is skipped otherwise."],
        why="""The second `Conn("db://x")` gets the pooled object from `__new__`, and then Python calls `__init__` on it again, which resets `requests` to 0:
        the cached connection's state was wiped by "creating" it. That is the trap of combining caching in `__new__` with an `__init__`. When
        `__new__` returns something that is not an instance of the class (here a string), Python skips `__init__` entirely and the call simply
        returns that object."""),
)

section("interview", "Interview questions",
    explain("What is the difference between `classmethod` and `staticmethod`?", "medium", tag="Interview",
        why="""A `classmethod` receives the class as its first argument (`cls`), whether called on the class or on an instance, and when called on a subclass it
        receives the subclass. That makes it the tool for alternative constructors (`return cls(...)`), factories and operations on class-level
        state, all of which stay correct under inheritance. A `staticmethod` receives no implicit argument; it is a plain function placed in the
        class namespace for organisation, suited to helpers related to the class that need neither instance nor class state, such as validators
        or parsers. Without either decorator, a function in a class is an instance method and receives the instance. If a static method has no
        real connection to the class, a module-level function is usually simpler."""),
    explain("Why are alternative constructors written as classmethods, and why use `cls(...)` inside them?", "medium", tag="Interview",
        why="""A class has a single `__init__`, but objects are built from many sources: dicts, JSON, environment variables, files, database rows. Named
        constructors such as `from_dict` and `from_env` keep `__init__` simple (just the fields) and give each input format its own parsing,
        validation and error messages, as in `datetime.fromisoformat` or `DataFrame.from_records`. They must be classmethods so they receive the
        class they were called on, and they should construct with `cls(...)` rather than the class name, so a subclass inherits a factory that
        returns instances of the subclass with its overrides and defaults; hard-coding the name silently returns base-class objects. Subclasses
        should keep the base `__init__` signature compatible (only adding optional parameters) so inherited constructors keep working."""),
    explain("How should copying work for objects that hold external resources such as API clients, connections or models?", "hard", tag="Interview",
        why="""Decide per attribute what a copy means. Configuration and other plain data that a copy may change should be deep-copied; immutable or
        read-only data can be shared; per-object state such as histories, caches and counters often should be reset; and external resources
        (an HTTP session, a database connection, a lock, a GPU-resident model, an open file) must usually be shared or recreated, never
        duplicated by `deepcopy`, which may fail outright or produce two objects fighting over one socket. Implement that rule in `__deepcopy__`
        (creating the new object with `__new__`, registering it in `memo` before copying attributes, and passing `memo` on) and `__copy__`, so
        every caller gets the same behaviour. For configuration-driven objects, a cleaner alternative is to rebuild from parameters, as
        scikit-learn's `clone` does, or to keep resources outside the object and inject them (9.5), so the objects themselves hold only data and
        copy trivially."""),
)

recap(
    "Instance methods get `self`; `@classmethod` gets `cls` (the class it was called on); `@staticmethod` gets nothing.",
    "Alternative constructors are classmethods named `from_<source>` that parse, validate and `return cls(...)`, so subclasses inherit working factories.",
    "Class-level state belongs in classmethods and is updated through the base class name when it is shared; `type(self)(...)` builds same-class objects in instance methods.",
    "`__new__` creates, `__init__` initialises; override `__new__` only for immutable subclasses or controlled creation, and remember `__init__` reruns on returned instances.",
    "Customise `__copy__` and `__deepcopy__(memo)` to share resources, deep-copy configuration and reset per-object state.",
)
