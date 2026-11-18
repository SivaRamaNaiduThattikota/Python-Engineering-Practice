from lesson import *
from diagrams import *

lesson(
    id="m11-p", num="11.P", title="Module 11 practice set and mini project",
    intro="Mixed problems from all of Module 11: type hints and what they do not check, protocols, generics and `TypedDict`, "
          "dataclasses and their options, and Pydantic validation. Then a mini project that needs all of it: a typed evaluation "
          "run that loads test cases from JSON Lines, grades answers through a protocol and reports results as validated models.",
    desc="Mixed problems from the whole module, then one small program that uses all of it.",
    keys="practice mixed review project evaluation eval cases jsonl grader protocol dataclass pydantic typeddict generic result settings environment overrides config version kw_only",
)

section("how", "How to use this page",
    fig(stage_map(11, "a typed evaluation run"), "Module 11 at a glance: type hints for checkers, dataclasses for trusted data, Pydantic for validation at the boundary."),
    p("""For every piece of data, ask two questions. **Who creates it?** If your own code does, from values that are already valid, a dataclass (or a
    `TypedDict` for plain dicts) describes it at almost no cost, and the type checker guards it (11.1 to 11.3). If it comes from outside, a file, an
    environment variable, a request or a model's reply, validate it at the boundary with Pydantic (11.4), then pass the validated object inward.
    **Who uses it?** If callers only need some behaviour, describe that behaviour with a `Protocol` rather than a base class, and write generic code
    with type parameters when the same logic serves several types (11.2)."""),
    p("""The problems mix the lessons on purpose, and the mini project combines all four in the kind of evaluation harness every LLM team runs before
    changing a prompt or a model."""),
)

section("set", "Practice set",
    predict("Hints, dataclasses and models on the same input", "easy",
        code="""
        from dataclasses import dataclass
        from pydantic import BaseModel

        @dataclass
        class D:
            n: int
            tags: tuple[str, ...] = ()

        class M(BaseModel):
            n: int
            tags: tuple[str, ...] = ()

        def double(x: int) -> int:
            return x * 2

        d = D("5", ["a"])
        m = M(n="5", tags=["a"])
        print(repr(d.n), d.tags, repr(m.n), m.tags)
        print(double("ab"), D.__annotations__["n"] is M.model_fields["n"].annotation)
        """,
        hints=["Only one of the three checks anything at run time."],
        why="""Type hints are not checked when the program runs (11.1): `double("ab")` happily repeats the string. A dataclass uses its annotations only to generate
        methods, so it stores the string `"5"` and the list exactly as given (11.3). The Pydantic model validates and converts, storing the integer 5 and a
        tuple (11.4). Both classes read the same annotation, `int`, which is the point: the same type hints, with or without enforcement."""),
    write("Comparable model versions", "easy", tag="ML",
        prompt="""Write a frozen, ordered dataclass `ModelVersion(major, minor, patch=0)` of ints. `__post_init__` raises `ValueError` if any part is negative.
        Add a class method `parse(text)` accepting `"1.2"`, `"1.2.3"` and an optional leading `"v"` (raising `ValueError` for anything else), a `__str__`
        returning `"v1.2.3"`, and `bump(part)` returning a new version with `"major"`, `"minor"` or `"patch"` increased and the lower parts reset to 0.""",
        code="""
        from dataclasses import dataclass, replace

        @dataclass(frozen=True, order=True)
        class ModelVersion:
            pass
        """,
        tests="""
        vs = [ModelVersion.parse(t) for t in ["v1.10.0", "1.2", "v1.2.3", "0.9.9"]]
        assert [str(v) for v in sorted(vs)] == ["v0.9.9", "v1.2.0", "v1.2.3", "v1.10.0"]
        assert max(vs) == ModelVersion(1, 10) and len({ModelVersion(1, 2), ModelVersion.parse("1.2.0")}) == 1
        v = ModelVersion(2, 3, 4)
        assert (str(v.bump("major")), str(v.bump("minor")), str(v.bump("patch")), str(v)) == ("v3.0.0", "v2.4.0", "v2.3.5", "v2.3.4")
        for bad in ["1", "1.2.3.4", "v1.x", "", "1.-2"]:
            try:
                ModelVersion.parse(bad)
                assert False, bad
            except ValueError:
                pass
        try:
            ModelVersion(1, -1)
            assert False
        except ValueError:
            pass
        """,
        hints=["Order compares fields in declaration order, so `major, minor, patch` sorts versions numerically, unlike strings (`\"1.10\" < \"1.2\"`).",
               "`int(\"-2\")` succeeds, so negative parts must be caught by `__post_init__`, which runs for `parse` too."],
        solution="""
        from dataclasses import dataclass, replace


        @dataclass(frozen=True, order=True)
        class ModelVersion:
            major: int
            minor: int
            patch: int = 0

            def __post_init__(self):
                if min(self.major, self.minor, self.patch) < 0:
                    raise ValueError(f"negative version part in {self.major}.{self.minor}.{self.patch}")

            @classmethod
            def parse(cls, text):
                parts = text.removeprefix("v").split(".")
                if len(parts) not in (2, 3):
                    raise ValueError(f"bad version: {text!r}")
                try:
                    numbers = [int(p) for p in parts]
                except ValueError:
                    raise ValueError(f"bad version: {text!r}") from None
                return cls(*numbers)

            def __str__(self):
                return f"v{self.major}.{self.minor}.{self.patch}"

            def bump(self, part):
                if part == "major":
                    return replace(self, major=self.major + 1, minor=0, patch=0)
                if part == "minor":
                    return replace(self, minor=self.minor + 1, patch=0)
                if part == "patch":
                    return replace(self, patch=self.patch + 1)
                raise ValueError(f"unknown part: {part!r}")
        """,
        why="""`order=True` generates comparisons that compare the fields as a tuple, in declaration order, so versions sort numerically: `v1.10.0` after
        `v1.2.3`, which plain strings get wrong. `frozen=True` makes instances immutable and, with the generated `__eq__`, hashable, so equal versions
        collapse in a set. `replace` builds the bumped copy and runs `__post_init__` again, so every way of making a version is checked. The parser
        turns `int`'s error into one clear message with `from None` (7.2). Model registries and artefact stores compare versions exactly like this."""),
    fix("A template with shared defaults", "easy", tag="GenAI",
        prompt="""`PromptTemplate` fails as soon as the module is imported, with "mutable default <class 'list'> for field variables is not allowed". Fix it so each
        template gets its own list and dict, and keep the `render` behaviour.""",
        code="""
        from dataclasses import dataclass

        @dataclass
        class PromptTemplate:
            name: str
            text: str
            variables: list[str] = []
            defaults: dict[str, str] = {}

            def render(self, **values):
                merged = {**self.defaults, **values}
                missing = [v for v in self.variables if v not in merged]
                if missing:
                    raise KeyError(f"missing variables: {missing}")
                return self.text.format(**merged)
        """,
        tests="""
        a = PromptTemplate("qa", "Answer {question} in {lang}.", ["question", "lang"], {"lang": "English"})
        b = PromptTemplate("plain", "Hello")
        b.variables.append("x")
        assert PromptTemplate("other", "Hi").variables == [] and a.render(question="refunds?") == "Answer refunds? in English."
        assert b.defaults == {} and b.defaults is not PromptTemplate("p", "q").defaults
        """,
        hints=["`field(default_factory=list)` and `field(default_factory=dict)`."],
        solution="""
        from dataclasses import dataclass, field

        @dataclass
        class PromptTemplate:
            name: str
            text: str
            variables: list[str] = field(default_factory=list)
            defaults: dict[str, str] = field(default_factory=dict)

            def render(self, **values):
                merged = {**self.defaults, **values}
                missing = [v for v in self.variables if v not in merged]
                if missing:
                    raise KeyError(f"missing variables: {missing}")
                return self.text.format(**merged)
        """,
        why="""A default value in a class body is created once and would be shared by every instance (9.1), so dataclasses refuse unhashable defaults such as lists
        and dicts at class creation time, which is why the error appears on import rather than at the first bug. `default_factory` is called for each new
        instance, so `b.variables.append` no longer changes every other template. Pydantic, by contrast, accepts `= []` because it copies defaults (11.4):
        the same intent, two different mechanisms."""),
    predict("TypedDict at run time and under Pydantic", "medium",
        code="""
        from typing import NotRequired, TypedDict
        from pydantic import TypeAdapter, ValidationError

        class Msg(TypedDict):
            role: str
            tokens: int
            name: NotRequired[str]

        m: Msg = {"role": "user", "tokens": "12"}
        print(type(m).__name__, m["tokens"] * 2, Msg.__required_keys__ == {"role", "tokens"})
        ta = TypeAdapter(Msg)
        v = ta.validate_python({"role": "user", "tokens": "12", "extra": 1})
        print(type(v).__name__, v)
        try:
            ta.validate_python({"role": "user"})
        except ValidationError as e:
            print(e.errors()[0]["loc"], e.errors()[0]["type"])
        """,
        hints=["A `TypedDict` creates ordinary dicts. A `TypeAdapter` validates and converts a dict against it."],
        why="""A `TypedDict` is only a description for the type checker (11.2): the value is a plain `dict`, and nothing stops the string `"12"` from being stored,
        so `"12" * 2` is `"1212"`. The class does record which keys are required, as a frozenset that compares equal to the set. Under a `TypeAdapter`,
        Pydantic validates the dict, converting `"12"` to 12 and returning a plain dict again, with unknown keys dropped by default; a missing required
        key is reported at its location with the `missing` type."""),
    write("Embedders as a protocol", "medium", tag="GenAI",
        prompt="""Define a `runtime_checkable` protocol `Embedder` with an attribute `dim: int` and a method `embed(self, texts: list[str]) -> list[list[float]]`.
        Write `embed_all(embedder, texts, batch_size=2)` that raises `TypeError` if `embedder` does not satisfy the protocol, embeds the texts in batches,
        checks that each batch returns one vector per text (`ValueError("expected N vectors, got M")`) and that every vector has `dim` numbers
        (`ValueError("expected D dims, got K")`), and returns all vectors in order.""",
        code="""
        from typing import Protocol, runtime_checkable

        def embed_all(embedder, texts, batch_size=2):
            pass
        """,
        tests="""
        class Chars:
            dim = 2
            def __init__(self):
                self.calls = []
            def embed(self, texts):
                self.calls.append(len(texts))
                return [[float(len(t)), float(t.count("a"))] for t in texts]

        e = Chars()
        assert embed_all(e, ["a", "banana", "kiwi", "pear", "fig"]) == [[1.0, 1.0], [6.0, 3.0], [4.0, 0.0], [4.0, 1.0], [3.0, 0.0]]
        assert e.calls == [2, 2, 1] and isinstance(e, Embedder) and embed_all(e, []) == []

        class NoDim:
            def embed(self, texts):
                return [[0.0] for _ in texts]
        class Drops(Chars):
            def embed(self, texts):
                return super().embed(texts)[:-1]
        class Wide(Chars):
            dim = 3
        for bad, err, text in [(NoDim(), TypeError, ""), (Drops(), ValueError, "expected 2 vectors, got 1"), (Wide(), ValueError, "expected 3 dims, got 2")]:
            try:
                embed_all(bad, ["x", "y"])
                assert False
            except err as ex:
                assert text in str(ex)
        """,
        hints=["Neither `Chars` nor the others inherit from `Embedder`: `isinstance` with a runtime-checkable protocol checks that the members exist.",
               "Batch with `texts[i:i + batch_size]` for `i` in `range(0, len(texts), batch_size)`."],
        solution="""
        from typing import Protocol, runtime_checkable


        @runtime_checkable
        class Embedder(Protocol):
            dim: int

            def embed(self, texts: list[str]) -> list[list[float]]: ...


        def embed_all(embedder: Embedder, texts: list[str], batch_size: int = 2) -> list[list[float]]:
            if not isinstance(embedder, Embedder):
                raise TypeError(f"{type(embedder).__name__} is not an Embedder")
            vectors: list[list[float]] = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                out = embedder.embed(batch)
                if len(out) != len(batch):
                    raise ValueError(f"expected {len(batch)} vectors, got {len(out)}")
                for vec in out:
                    if len(vec) != embedder.dim:
                        raise ValueError(f"expected {embedder.dim} dims, got {len(vec)}")
                vectors.extend(out)
            return vectors
        """,
        why="""The protocol describes what `embed_all` needs, a `dim` and an `embed` method, so any embedder works without inheriting from anything: a local model, an
        API client, or this test fake (11.2). `runtime_checkable` adds an `isinstance` check that only verifies the members **exist**, not their
        signatures or types, so the shape checks on the actual output are still needed; they catch the two real failures of embedding services, a batch
        that comes back short (a dropped input would silently shift every later vector to the wrong text) and a dimension mismatch after a model change,
        which would corrupt a vector index (5.P)."""),
    write("Config overrides from the command line", "medium", tag="ML",
        prompt="""Write Pydantic models `Optimizer(name: Literal["adam", "sgd"] = "adam", lr: float in (0, 1], default 1e-3)` and `TrainConfig(epochs: int >= 1 =
        10, batch_size: int = 32, optimizer: Optimizer)` (a fresh default `Optimizer`), both forbidding extra fields. Write `apply_overrides(cfg, overrides)`
        taking strings like `"epochs=3"` or `"optimizer.lr=0.01"` and returning a new validated `TrainConfig`. A string without `=` raises `ValueError`, and
        so does a dotted path whose parent is not a nested object; unknown names and bad values raise `ValidationError`.""",
        code="""
        from typing import Literal
        from pydantic import BaseModel, ConfigDict, Field

        def apply_overrides(cfg, overrides):
            pass
        """,
        tests="""
        from pydantic import ValidationError
        cfg = TrainConfig()
        new = apply_overrides(cfg, ["epochs=3", "optimizer.lr=0.01", "optimizer.name=sgd"])
        assert (new.epochs, new.optimizer.lr, new.optimizer.name, new.batch_size) == (3, 0.01, "sgd", 32)
        assert cfg.epochs == 10 and cfg.optimizer.lr == 0.001 and TrainConfig().optimizer is not cfg.optimizer
        for bad, loc in [(["optimizer.lr=2"], ("optimizer", "lr")), (["epoch=3"], ("epoch",)), (["optimizer.momentum=0.9"], ("optimizer", "momentum")), (["epochs=0"], ("epochs",))]:
            try:
                apply_overrides(cfg, bad)
                assert False, bad
            except ValidationError as e:
                assert e.errors()[0]["loc"] == loc
        for bad in [["epochs"], ["epochs.x=1"]]:
            try:
                apply_overrides(cfg, bad)
                assert False, bad
            except ValueError as e:
                assert not isinstance(e, ValidationError)
        """,
        hints=["Start from `data = cfg.model_dump()` (nested dicts), set each override in it, then `TrainConfig.model_validate(data)`.",
               "Walk the dotted path with `node = node.setdefault(part, {})`, checking the node is a dict; the values stay strings and Pydantic converts them."],
        solution="""
        from typing import Literal
        from pydantic import BaseModel, ConfigDict, Field


        class Optimizer(BaseModel):
            model_config = ConfigDict(extra="forbid")
            name: Literal["adam", "sgd"] = "adam"
            lr: float = Field(default=1e-3, gt=0, le=1)


        class TrainConfig(BaseModel):
            model_config = ConfigDict(extra="forbid")
            epochs: int = Field(default=10, ge=1)
            batch_size: int = 32
            optimizer: Optimizer = Field(default_factory=Optimizer)


        def apply_overrides(cfg, overrides):
            data = cfg.model_dump()
            for item in overrides:
                key, sep, value = item.partition("=")
                if not sep:
                    raise ValueError(f"override must look like key=value: {item!r}")
                *parents, last = key.split(".")
                node = data
                for part in parents:
                    node = node.setdefault(part, {})
                    if not isinstance(node, dict):
                        raise ValueError(f"{key!r}: {part!r} is not a nested section")
                node[last] = value
            return TrainConfig.model_validate(data)
        """,
        why="""The function never converts a value itself: it edits the plain-dict form of the config with strings, exactly as they arrive from the command line,
        and lets the model do all conversion and checking in one place. Lax mode turns `"3"` and `"0.01"` into numbers, the literal and the range reject bad
        values, and `extra="forbid"` turns misspelt names (`epoch`, `momentum`) into errors with their full path instead of silently ignored settings,
        which is how a training run with the wrong learning rate happens. The original is untouched because a new model is built. Tools such as Hydra and
        pydantic-settings implement this pattern at scale."""),
    fix("A subclass with required fields after defaults", "medium", tag="GenAI",
        prompt="""Importing the module fails with "non-default argument 'tool' follows default argument". `ToolEvent` must add a required `tool` and an optional
        `args` to `BaseEvent`, whose `ts` has a default. Fix it without giving `tool` a default or changing `BaseEvent`.""",
        code="""
        from dataclasses import dataclass, field

        @dataclass
        class BaseEvent:
            id: str
            ts: float = 0.0

        @dataclass
        class ToolEvent(BaseEvent):
            tool: str
            args: dict = field(default_factory=dict)
        """,
        tests="""
        e = ToolEvent("e1", tool="search")
        assert (e.id, e.ts, e.tool, e.args) == ("e1", 0.0, "search", {})
        assert ToolEvent(id="e2", ts=1.5, tool="calc", args={"x": 1}).args == {"x": 1}
        try:
            ToolEvent("e3")
            assert False
        except TypeError:
            pass
        """,
        hints=["`@dataclass(kw_only=True)` on the subclass makes its new fields keyword-only, which may come after defaulted positional ones."],
        solution="""
        from dataclasses import dataclass, field

        @dataclass
        class BaseEvent:
            id: str
            ts: float = 0.0

        @dataclass(kw_only=True)
        class ToolEvent(BaseEvent):
            tool: str
            args: dict = field(default_factory=dict)
        """,
        why="""A dataclass `__init__` takes fields in order, parents first, so `tool` would come after `ts=0.0` as a positional parameter without a default, which
        Python syntax forbids. Making the subclass's fields keyword-only moves them out of the positional order: the generated signature becomes
        `(id, ts=0.0, *, tool, args=...)`, where a required keyword-only argument after a default is fine (3.1). It is also clearer at the call site, which
        is why many codebases make every field of event and message classes keyword-only."""),
    trace("Equality, hashing and replace", "medium",
        prompt="Fill in `eq` and `size` after each marked line.",
        code="""
        from dataclasses import dataclass, field, replace

        @dataclass(frozen=True)
        class Chunk:
            doc: str
            idx: int
            text: str = field(compare=False)

        a = Chunk("faq", 0, "Refunds")
        b = Chunk("faq", 0, "Refunds take 5 days")
        c = replace(a, idx=1)
        d = replace(c, idx=0, text="other")
        eq, size = a == b, len({a, b})  # row: "text not compared"
        eq, size = a == c, len({a, b, c})  # row: "after replace"
        eq, size = d == a, len({a, b, c, d})  # row: "back to idx 0"
        """,
        trace_vars=["eq", "size"],
        hints=["`compare=False` removes a field from both `__eq__` and `__hash__`."],
        why="""With `compare=False`, chunks are identified by `(doc, idx)` only, so `a` and `b` are equal and hash alike, and the set keeps one of them. `replace` builds a
        new instance with changed fields: `c` has index 1 and is different. `d` returns to index 0 with other text, so it equals `a` and the set still has two
        members. This is a deliberate design for deduplicating retrieved chunks by identity rather than content (11.3)."""),
    write("A generic Result for parsing", "hard", tag="GenAI",
        prompt="""Write a frozen generic dataclass `class Result[T]` with `value: T | None = None` and `error: str | None = None` (`__post_init__` rejects both being set),
        a property `ok` (no error), class methods `success(value)` and `failure(error)`, `map(fn)` (applies `fn` to the value of a success, turning an
        exception into a failure `"<ExceptionName>: <message>"`; failures pass through unchanged) and `unwrap()` (the value, or `ValueError(error)`). Then
        write `parse_all(texts, model_cls)` returning a `Result` per text from `model_validate_json`, where a failure's error lists `"<loc>: <type>"` for
        each validation error, joined with `"; "`, with `reply` for an empty location.""",
        code="""
        from dataclasses import dataclass
        from pydantic import BaseModel, ValidationError

        def parse_all(texts, model_cls):
            pass
        """,
        tests="""
        from typing import Literal
        from pydantic import BaseModel

        class Verdict(BaseModel):
            label: Literal["spam", "ham"]
            confidence: float

        rs = parse_all(['{"label": "spam", "confidence": 0.9}', '{"label": "x"}', "oops"], Verdict)
        assert [r.ok for r in rs] == [True, False, False]
        assert rs[1].error == "label: literal_error; confidence: missing" and rs[2].error == "reply: json_invalid"
        assert rs[0].map(lambda v: v.confidence * 100).value == 90.0 and rs[1].map(lambda v: 1) is rs[1]
        assert rs[0].map(lambda v: 1 / 0).error == "ZeroDivisionError: division by zero"
        assert rs[0].unwrap().label == "spam" and Result.success(None).ok
        for bad in [lambda: rs[2].unwrap(), lambda: Result(1, "both")]:
            try:
                bad()
                assert False
            except ValueError:
                pass
        """,
        hints=["Python 3.12 syntax: `@dataclass(frozen=True)` above `class Result[T]:`; methods can return `Result[T]` without quotes because annotations are lazy in 3.14.",
               "`map` returns `self` for a failure, so the test's `is` check holds."],
        solution="""
        from dataclasses import dataclass
        from pydantic import BaseModel, ValidationError
        from typing import Callable


        @dataclass(frozen=True)
        class Result[T]:
            value: T | None = None
            error: str | None = None

            def __post_init__(self):
                if self.value is not None and self.error is not None:
                    raise ValueError("a result has a value or an error, not both")

            @property
            def ok(self) -> bool:
                return self.error is None

            @classmethod
            def success(cls, value: T) -> Result[T]:
                return cls(value=value)

            @classmethod
            def failure(cls, error: str) -> Result[T]:
                return cls(error=error)

            def map[U](self, fn: Callable[[T], U]) -> Result[U]:
                if not self.ok:
                    return self
                try:
                    return Result.success(fn(self.value))
                except Exception as e:
                    return Result.failure(f"{type(e).__name__}: {e}")

            def unwrap(self) -> T:
                if not self.ok:
                    raise ValueError(self.error)
                return self.value


        def parse_all[M: BaseModel](texts: list[str], model_cls: type[M]) -> list[Result[M]]:
            results = []
            for text in texts:
                try:
                    results.append(Result.success(model_cls.model_validate_json(text)))
                except ValidationError as e:
                    parts = [f"{'.'.join(map(str, err['loc'])) or 'reply'}: {err['type']}" for err in e.errors()]
                    results.append(Result.failure("; ".join(parts)))
            return results
        """,
        why="""Batch jobs over model outputs should not stop at the first bad reply, and should not hide failures either. A `Result` makes success and failure explicit
        values that travel through the pipeline together: `map` chains transformations that only run on successes and turn their exceptions into failures,
        so later steps never see half-processed data, and the caller decides at the end whether to `unwrap` or report. The type parameters make the
        intent checkable (11.2): `parse_all(texts, Verdict)` returns `list[Result[Verdict]]`, and `map` changes `T` into `U`. The error format uses
        Pydantic's stable error **types** rather than messages, which makes failures easy to count and group in a dashboard."""),
    fix("Read the code: settings from the environment", "hard", tag="GenAI",
        prompt="""`load_settings` builds the service's settings from environment variables with the prefix `APP_`. In production, `APP_DEBUG=false` turns debug **on**,
        `APP_TEMPERATURE=0.7` is stored as a string and breaks the client, `APP_ALLOWED_TOOLS=search, calc` is one string, a temperature of 5 is
        accepted, and a misspelt `APP_COLOUR` crashes with a `TypeError`. Rewrite it with a Pydantic model so values are converted and validated
        (temperature in `[0, 2]`, `max_retries` an int from 0 to 10, tools split on commas and stripped) and any unknown `APP_` variable is a
        `ValidationError`.""",
        code="""
        from dataclasses import dataclass, field


        @dataclass
        class Settings:
            model: str = "small"
            temperature: float = 0.0
            debug: bool = False
            allowed_tools: list = field(default_factory=list)
            max_retries: int = 3


        def load_settings(environ, prefix="APP_"):
            values = {}
            for key, value in environ.items():
                if key.startswith(prefix):
                    values[key[len(prefix):].lower()] = value
            s = Settings(**values)
            s.debug = bool(s.debug)
            return s
        """,
        tests="""
        from pydantic import ValidationError
        s = load_settings({"APP_MODEL": "large", "APP_TEMPERATURE": "0.7", "APP_DEBUG": "false", "APP_ALLOWED_TOOLS": "search, calc", "HOME": "/x"})
        assert (s.model, s.temperature, s.debug, s.allowed_tools, s.max_retries) == ("large", 0.7, False, ["search", "calc"], 3)
        assert load_settings({"APP_DEBUG": "1", "APP_MAX_RETRIES": "5"}).debug is True and load_settings({}).allowed_tools == []
        for bad in [{"APP_TEMPERATURE": "5"}, {"APP_MAX_RETRIES": "3.5"}, {"APP_COLOUR": "red"}, {"APP_DEBUG": "maybe"}, {"APP_MAX_RETRIES": "11"}]:
            try:
                load_settings(bad)
                assert False, bad
            except ValidationError:
                pass
        """,
        hints=["Replace the dataclass with a `BaseModel` using `extra=\"forbid\"`, `Field` ranges and a `mode=\"before\"` validator that splits a string of tools.",
               "Build the dict of prefixed variables as before, then call `Settings.model_validate(values)`; Pydantic already parses `\"false\"`, `\"0\"` and `\"yes\"` for a `bool`."],
        solution="""
        from pydantic import BaseModel, ConfigDict, Field, field_validator


        class Settings(BaseModel):
            model_config = ConfigDict(extra="forbid")
            model: str = "small"
            temperature: float = Field(default=0.0, ge=0, le=2)
            debug: bool = False
            allowed_tools: list[str] = []
            max_retries: int = Field(default=3, ge=0, le=10)

            @field_validator("allowed_tools", mode="before")
            @classmethod
            def split_tools(cls, v):
                if isinstance(v, str):
                    return [t.strip() for t in v.split(",") if t.strip()]
                return v


        def load_settings(environ, prefix="APP_"):
            values = {key[len(prefix):].lower(): value for key, value in environ.items() if key.startswith(prefix)}
            return Settings.model_validate(values)
        """,
        why="""Environment variables are always strings, and the dataclass trusted them: `temperature` stayed `"0.7"`, and `bool("false")` is `True` because every
        non-empty string is truthy, the most common configuration bug in Python services. Pydantic's lax mode parses booleans properly (`"false"`, `"0"`,
        `"no"` and `"off"` are `False`; `"maybe"` is an error), numbers from strings, and refuses `"3.5"` for an int. The range constraints catch
        dangerous values at start-up instead of at the first request, the `before` validator accepts the comma-separated format, and `extra="forbid"` turns
        a misspelt variable into a clear validation error naming it. Failing at start-up with every problem listed is the goal of settings validation. The
        `pydantic-settings` package packages this pattern (prefixes, `.env` files, secrets) as `BaseSettings`."""),
    predict("Pydantic with enums, dataclasses and dates", "hard",
        code="""
        from dataclasses import dataclass
        from datetime import date
        from enum import Enum
        from pydantic import BaseModel

        class Level(Enum):
            LOW = "low"
            HIGH = "high"

        @dataclass
        class Span:
            start: int
            end: int

        class Alert(BaseModel):
            level: Level
            span: Span
            day: date

        a = Alert(level="high", span={"start": "1", "end": 4}, day="2025-03-01")
        print(a.level, type(a.span).__name__, a.span)
        print(a.model_dump())
        print(a.model_dump(mode="json"))
        print(a.model_dump_json())
        """,
        hints=["Pydantic validates standard dataclasses used as field types. `model_dump()` keeps Python objects; `mode=\"json\"` converts them to JSON-friendly values."],
        why="""Pydantic converts the string `"high"` into the enum member by value, builds a real `Span` dataclass from the dict (converting `"1"` to 1, because Pydantic
        validates dataclass fields too), and parses the ISO date. `model_dump()` converts models and dataclasses into dicts but keeps other Python objects as
        they are, the enum member and the `date`. `mode="json"` goes all the way to JSON-compatible values, the enum's value and the ISO string, which is what
        `model_dump_json()` writes. Use `mode="json"` when the dict will be sent somewhere that only understands JSON types, such as a message queue."""),
    explain("Type hints, dataclasses, TypedDict and Pydantic: which one where?", "medium", tag="Interview",
        why="""They solve different problems and work together. **Type hints** everywhere document intent and let a type checker (mypy, pyright) catch mistakes before
        the code runs, at no run-time cost. **Dataclasses** for internal objects with behaviour or identity that your code creates: domain records, results,
        configuration already validated, using `frozen`, `slots` and `kw_only` where useful. **`TypedDict`** when the data must stay a plain dict, such as JSON
        passed through to a library or API payload types, giving checked keys without a class. **Pydantic** at every boundary where untrusted data enters:
        requests, settings, files, queues and LLM output, where it validates, converts, reports every error and produces JSON Schema. **Protocols** for the
        interfaces between components, such as an embedder or a retriever, so implementations can be swapped and faked in tests. The rule of thumb: validate
        once at the edge with Pydantic, then pass typed, trusted objects inward."""),
    explain("Your LLM output model needs a new field. How do you change it without breaking things?", "hard", tag="Interview",
        why="""Treat the model as a contract between prompts, parsing code and stored data. Add the field as **optional** (with a default or `None`), so replies from the
        old prompt and records already stored still validate, and new code can start using it; only make it required after every producer emits it. Never
        rename or retype a field in place: add the new one, read both for a while (a `mode="before"` validator can map the old name), then remove the old
        one. Version the schema explicitly, for example a `schema_version` literal or a discriminated union of `V1 | V2` when shapes really differ, and
        store the version with each output. Because the JSON Schema sent to the model changes, also re-run the evaluation set (as in the project below)
        before rollout, since a schema change can shift the model's behaviour, and watch the validation failure rate after deployment. Keep
        `extra="ignore"` (the default) when reading outputs from newer producers, and `extra="forbid"` for inputs you control, such as requests and settings."""),
)

section("project", "Mini project: a typed evaluation run",
    p("""Before changing a prompt or a model, an LLM team runs an evaluation set: questions with expected facts, answered by the system and graded. The cases
    live in a JSON Lines file maintained by hand, so they must be validated; graders are interchangeable; and the report must be a well-defined object that
    can be stored as JSON and compared between runs. Build it from the pieces of this module."""),
    write("Load, run and report an evaluation set", "hard", key="eval-run", tag="Project",
        prompt="""Implement the following.

        - **`EvalCase`**: a Pydantic model forbidding extras and stripping strings, with `id` and `question` (non-empty strings), `expected` (a list of at
          least one string) and `tags` (a list of strings, default empty).
        - **`load_cases(text)`**: parse JSON Lines, skipping blank lines, and return `(cases, errors)`. Invalid lines add one error per validation error,
          `f"line {n}: {loc}: {type}"` (loc dotted, `line` if empty); a repeated id adds `f"line {n}: id: duplicate {id!r}"` and skips the case.
        - **`Grader`**: a `Protocol` with `grade(self, case: EvalCase, answer: str) -> float`.
        - **`ContainsGrader`**: a frozen dataclass with `case_sensitive: bool = False` whose `grade` returns the fraction of `expected` strings found in
          the answer.
        - **`CaseResult`**: a frozen dataclass `(case_id, score, passed, error=None)`.
        - **`RunReport`**: a Pydantic model with `total`, `passed`, `mean_score` (rounded to 3 places), `by_tag` (tag to mean score rounded to 3, tags
          sorted), `failures` (ids that did not pass, in order) and `results: list[CaseResult]`, plus a property `pass_rate` (0.0 for an empty run).
        - **`run_eval(cases, answer_fn, grader, threshold=0.5)`**: answer and grade every case; if `answer_fn` raises, the case scores 0, fails and
          records `f"{ExceptionName}: {message}"` as its error; a case passes when its score is at least `threshold`.""",
        code="""
        import json
        from dataclasses import dataclass
        from typing import Protocol
        from pydantic import BaseModel, ConfigDict, Field, ValidationError


        class EvalCase(BaseModel):
            pass


        def load_cases(text):
            pass


        def run_eval(cases, answer_fn, grader, threshold=0.5):
            pass
        """,
        tests="""
        import json
        lines = [
            '{"id": "r1", "question": "How long do refunds take?", "expected": ["5 days"], "tags": ["billing"]}',
            '',
            '{"id": "r2", "question": "Refund after 30 days?", "expected": ["no", "30 days"], "tags": ["policy", "billing"]}',
            '{"id": "r1", "question": "dup", "expected": ["x"]}',
            '{"id": "r3", "question": "  ", "expected": []}',
            'not json',
            '{"id": "r4", "question": "Who do I contact?", "expected": ["support"], "priority": 1}',
            '{"id": "r5", "question": "Do you ship to the EU?", "expected": ["Yes"], "tags": ["shipping"]}',
        ]
        cases, errors = load_cases("\\n".join(lines))
        assert [c.id for c in cases] == ["r1", "r2", "r5"]
        assert errors == ["line 4: id: duplicate 'r1'", "line 5: question: string_too_short", "line 5: expected: too_short",
                          "line 6: line: json_invalid", "line 7: priority: extra_forbidden"]

        answers = {"How long do refunds take?": "Refunds take 5 days.", "Refund after 30 days?": "No refunds after 30 Days."}
        def answer_fn(question):
            if question not in answers:
                raise ConnectionError("timeout")
            return answers[question]

        report = run_eval(cases, answer_fn, ContainsGrader())
        assert (report.total, report.passed, report.mean_score, report.failures) == (3, 2, 0.667, ["r5"])
        assert report.by_tag == {"billing": 1.0, "policy": 1.0, "shipping": 0.0} and list(report.by_tag) == ["billing", "policy", "shipping"]
        assert report.results[2] == CaseResult("r5", 0.0, False, "ConnectionError: timeout") and abs(report.pass_rate - 2 / 3) < 1e-9
        dumped = json.loads(report.model_dump_json())
        assert dumped["results"][0] == {"case_id": "r1", "score": 1.0, "passed": True, "error": None} and "pass_rate" not in dumped

        strict = run_eval(cases[:2], answer_fn, ContainsGrader(case_sensitive=True), threshold=0.5)
        assert [r.score for r in strict.results] == [1.0, 0.0] and strict.failures == ["r2"]

        class ExactGrader:
            def grade(self, case, answer):
                return float(answer.strip() == case.expected[0])
        half = run_eval([cases[1]], lambda q: "the answer is no", ContainsGrader(), threshold=0.5)
        assert half.results[0].score == 0.5 and half.passed == 1
        assert run_eval([cases[0]], lambda q: "5 days", ExactGrader()).passed == 1
        empty = run_eval([], answer_fn, ContainsGrader())
        assert (empty.total, empty.mean_score, empty.by_tag, empty.pass_rate) == (0, 0.0, {}, 0.0)
        """,
        hints=["`load_cases`: `enumerate(text.splitlines(), start=1)`, `EvalCase.model_validate_json(line)`, and a `seen` set of ids.",
               "`run_eval`: collect `CaseResult`s, then compute the summary; for `by_tag`, gather scores per tag in a dict of lists and build the result from `sorted(...)`.",
               "Pydantic validates a field typed `list[CaseResult]` with a standard dataclass, and dumps it as dicts."],
        solution="""
        import json
        from dataclasses import dataclass
        from typing import Callable, Protocol
        from pydantic import BaseModel, ConfigDict, Field, ValidationError


        class EvalCase(BaseModel):
            model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
            id: str = Field(min_length=1)
            question: str = Field(min_length=1)
            expected: list[str] = Field(min_length=1)
            tags: list[str] = []


        def load_cases(text: str) -> tuple[list[EvalCase], list[str]]:
            cases: list[EvalCase] = []
            errors: list[str] = []
            seen: set[str] = set()
            for n, line in enumerate(text.splitlines(), start=1):
                if not line.strip():
                    continue
                try:
                    case = EvalCase.model_validate_json(line)
                except ValidationError as e:
                    for err in e.errors():
                        loc = ".".join(map(str, err["loc"])) or "line"
                        errors.append(f"line {n}: {loc}: {err['type']}")
                    continue
                if case.id in seen:
                    errors.append(f"line {n}: id: duplicate {case.id!r}")
                    continue
                seen.add(case.id)
                cases.append(case)
            return cases, errors


        class Grader(Protocol):
            def grade(self, case: EvalCase, answer: str) -> float: ...


        @dataclass(frozen=True)
        class ContainsGrader:
            case_sensitive: bool = False

            def grade(self, case: EvalCase, answer: str) -> float:
                if not self.case_sensitive:
                    answer = answer.lower()
                found = sum((e if self.case_sensitive else e.lower()) in answer for e in case.expected)
                return found / len(case.expected)


        @dataclass(frozen=True)
        class CaseResult:
            case_id: str
            score: float
            passed: bool
            error: str | None = None


        class RunReport(BaseModel):
            total: int
            passed: int
            mean_score: float
            by_tag: dict[str, float]
            failures: list[str]
            results: list[CaseResult]

            @property
            def pass_rate(self) -> float:
                return self.passed / self.total if self.total else 0.0


        def run_eval(cases: list[EvalCase], answer_fn: Callable[[str], str], grader: Grader, threshold: float = 0.5) -> RunReport:
            results: list[CaseResult] = []
            tag_scores: dict[str, list[float]] = {}
            for case in cases:
                try:
                    answer = answer_fn(case.question)
                except Exception as e:
                    result = CaseResult(case.id, 0.0, False, f"{type(e).__name__}: {e}")
                else:
                    score = grader.grade(case, answer)
                    result = CaseResult(case.id, score, score >= threshold)
                results.append(result)
                for tag in case.tags:
                    tag_scores.setdefault(tag, []).append(result.score)
            total = len(results)
            return RunReport(
                total=total,
                passed=sum(r.passed for r in results),
                mean_score=round(sum(r.score for r in results) / total, 3) if total else 0.0,
                by_tag={tag: round(sum(s) / len(s), 3) for tag, s in sorted(tag_scores.items())},
                failures=[r.case_id for r in results if not r.passed],
                results=results,
            )
        """,
        why="""Every lesson of the module has a job here:

        - **Pydantic at the boundary (11.4):** the hand-edited JSONL file is untrusted, so each line goes through `model_validate_json`, and every
          problem is reported with its line number and Pydantic's error type: blank questions, empty expectations, broken JSON and misspelt keys
          (`extra="forbid"`) are all caught before the run, not halfway through it. The report is a model too, so it serialises to JSON with its nested
          results in one call and can be stored and compared across runs.
        - **Dataclasses inside (11.3):** results are created by our own code from trusted values, so a frozen dataclass is enough, and Pydantic still
          validates and dumps them as part of the report.
        - **Protocols and hints (11.1, 11.2):** `run_eval` needs only "something with `grade`", so `ContainsGrader` and the test's `ExactGrader` both work
          without a shared base class, and an LLM-as-judge grader could be added the same way. The annotations on every function document the data flow
          for the type checker.

        Failures of the system under test are data, not crashes: a timeout becomes a failed case with its error recorded, so one flaky call cannot
        lose the whole run. `pass_rate` is a property, so it is derived rather than stored, and does not appear in the JSON. Production harnesses add
        concurrency, LLM-graded scores and comparisons with the previous run, but keep exactly this split between validated inputs, pluggable graders
        and a typed report."""),
)

recap(
    "Type hints describe and a type checker enforces before run time; nothing checks them while the program runs unless you validate.",
    "Dataclasses (with `frozen`, `order`, `kw_only`, `default_factory`) model trusted internal data; `TypedDict` types plain dicts.",
    "Protocols describe the behaviour a function needs, so implementations and test fakes plug in without inheritance; generics keep types flowing through.",
    "Pydantic validates and converts at boundaries (files, environment, requests, LLM output), reporting every error with its location and type.",
    "Validate once at the edge, pass typed trusted objects inward, and evolve schemas by adding optional fields and versioning them.",
)
