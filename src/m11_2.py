from lesson import *

lesson(
    id="m11-2", num="11.2", title="Advanced typing",
    intro="The typing tools that describe real data and APIs: `TypedDict` for JSON-shaped dicts, `Literal` for fixed sets "
          "of values, `Callable` for callbacks, generic functions and classes with type parameters, `NewType`, `Annotated` "
          "metadata and `Final`, and exhaustiveness checks with `assert_never`. What each does at run time (often nothing) "
          "and how libraries read them. Applied to chat messages, events, tool schemas and structured LLM output.",
    desc="`TypedDict`, `Literal`, `Protocol`, `Callable`, `TypeVar`.",
    keys="typeddict literal callable typevar generic type parameter pep 695 protocol newtype annotated final assert_never exhaustive required notrequired json schema discriminated union structured output",
)

term("TypedDict", "A type describing a dict with fixed string keys and a type per key, such as a JSON message. At run time it is an ordinary dict.")
term("Literal", "A type whose only allowed values are listed: `Literal[\"user\", \"assistant\"]` accepts just those two strings.")
term("Type parameter", "A placeholder such as `T` in `def first[T](items: list[T]) -> T`, so the checker knows the result has the same type as the elements.")
term("Annotated", "`Annotated[int, metadata]` is an `int` for type checkers, with extra metadata that libraries such as Pydantic and FastAPI read.")

section("typeddict", "`TypedDict`: the shape of a dict",
    p("""Much data in Python code is a dict with a fixed set of string keys: a chat message `{"role": ..., "content": ...}`, a JSON payload, a row from
    a database, an API response. `dict[str, str]` cannot describe it, because the keys are not arbitrary and the values have different types.
    **`TypedDict`** does: you declare the keys and their types in class syntax, and a type checker then knows that `msg["role"]` is a string,
    that `msg["contnet"]` is a typo, and that a dict missing `content` is not a valid message."""),
    ex("""
    from typing import TypedDict, NotRequired, get_type_hints

    class ChatMessage(TypedDict):
        role: str
        content: str
        name: NotRequired[str]          # may be absent

    msg: ChatMessage = {"role": "user", "content": "Refund?"}
    print(msg, type(msg).__name__, isinstance(msg, dict))
    print(sorted(ChatMessage.__required_keys__), sorted(ChatMessage.__optional_keys__))
    print(get_type_hints(ChatMessage))
    bad: ChatMessage = {"role": 1}      # a type checker reports this; Python does not
    print(bad)
    """, "typeddict.py"),
    p("""At run time a `TypedDict` is **just a dict**: `ChatMessage(...)` builds a plain dict, nothing is validated, and `isinstance(x, ChatMessage)` is not
    allowed. Its value is static: the checker verifies every place that builds or reads such dicts. Keys are required by default; `NotRequired[...]`
    marks one as optional, and `class Options(TypedDict, total=False)` makes all keys optional (with `Required[...]` for exceptions). The class keeps
    `__required_keys__`, `__optional_keys__` and its hints, which is enough for a runtime validator (problem 5). Choose a `TypedDict` for data that
    stays a dict (JSON in and out); choose a dataclass or a Pydantic model for objects with behaviour or validation (11.3, 11.4)."""),
)

section("literal", "`Literal`: a fixed set of values",
    p("""Many strings in real code are not arbitrary: a message role is `"system"`, `"user"`, `"assistant"` or `"tool"`; a finish reason is one of a few
    values; a mode is `"fast"` or `"accurate"`. **`Literal["user", "assistant"]`** is a type whose only members are those exact values, so a type
    checker rejects `role="admin"` or the typo `"asistant"` at the call site. It works with strings, integers, booleans, enums and `None`, and
    combines with unions. Give the type a name with an alias so the set of values is defined once."""),
    ex("""
    from typing import Literal, get_args

    Role = Literal["system", "user", "assistant", "tool"]
    FinishReason = Literal["stop", "length", "tool_calls", "content_filter"]

    def message(role: Role, content: str) -> dict:
        if role not in get_args(Role):              # runtime check from the same definition
            raise ValueError(f"role must be one of {get_args(Role)}, got {role!r}")
        return {"role": role, "content": content}

    print(get_args(Role), message("user", "hi"))
    try:
        message("admin", "x")
    except ValueError as e:
        print("ValueError:", e)
    print(get_args(Literal["a", 1, None]))
    """, "literal.py"),
    p("""Because `get_args` returns the allowed values, the same alias can drive both static checking and runtime validation: there is one source of
    truth, so adding `"tool"` to the alias updates the validator too. A separate hard-coded list of valid roles is a classic drift bug: someone adds
    a role to the type and forgets the list (problem 3). LLM structured-output schemas turn `Literal` into a JSON Schema `enum`, which constrains the
    model to the listed values (problem 12)."""),
)

section("callable", "`Callable`: functions as values",
    p("""Functions passed as arguments (callbacks, key functions, scorers, hooks, retry predicates) are typed with **`Callable[[arg types], return type]`**
    from `collections.abc`: `Callable[[str], None]` is "a function taking one string and returning nothing", like a streaming `on_token` callback;
    `Callable[[str, list[str]], float]` is a scorer. `Callable[..., T]` accepts any arguments. The checker then verifies both sides: that you pass a
    compatible function, and that you call it with the right arguments (problem 9). Objects with `__call__` (9.2) satisfy `Callable` too."""),
    ex("""
    from collections.abc import Callable

    def stream(text: str, on_token: Callable[[str], None]) -> int:
        count = 0
        for token in text.split():
            on_token(token)
            count += 1
        return count

    def rank(docs: list[str], score: Callable[[str], float], k: int = 2) -> list[str]:
        return sorted(docs, key=score, reverse=True)[:k]

    received: list[str] = []
    print(stream("refunds take five days", received.append), received)
    print(rank(["short", "a much longer document", "medium one"], score=len))
    """, "callable.py"),
    p("""For decorators, which must accept "any function" and return "a function with the same signature", plain `Callable[..., Any]` loses the parameter
    types; `typing.ParamSpec` captures them, so a type checker still knows the decorated function's arguments. Library code uses it; in
    application code, `functools.wraps` plus `Callable` is usually enough."""),
)

section("generics", "Generics: functions and classes with type parameters",
    p("""Some functions work for **any** element type but connect their inputs and outputs: `first(items)` returns an element of the same type as the
    items; a cache maps keys of one type to values of another. Writing `def first(items: list[Any]) -> Any` loses that connection, so the checker no
    longer knows that `first(["a"])` is a string. A **type parameter** keeps it: `def first[T](items: Iterable[T]) -> T | None` says "for some
    type `T`, given items of type `T`, return a `T` (or `None`)". The square brackets after the name are Python 3.12 syntax (PEP 695); older code
    declares `T = TypeVar("T")` at module level and uses it the same way."""),
    ex("""
    from collections.abc import Iterable, Hashable

    def first[T](items: Iterable[T]) -> T | None:
        for item in items:
            return item
        return None

    def group_by[K: Hashable, V](items: Iterable[V], key) -> dict[K, list[V]]:
        out: dict = {}
        for item in items:
            out.setdefault(key(item), []).append(item)
        return out

    class Registry[K, V]:
        def __init__(self) -> None:
            self._items: dict[K, V] = {}
        def add(self, key: K, value: V) -> None:
            self._items[key] = value
        def get(self, key: K) -> V | None:
            return self._items.get(key)

    print(first(["refund", "reset"]), first([]), first(x * 2 for x in [3, 4]))
    print(group_by(["refund", "reset", "invoice"], key=lambda w: w[0]))
    r: Registry[str, float] = Registry()
    r.add("small", 0.002)
    print(r.get("small"), first.__type_params__, Registry.__type_params__)
    """, "generics.py"),
    p("""`[K: Hashable, V]` adds a **bound**: `K` may be any type that is hashable, because it is used as a dict key. A **constraint** list, `[T: (int, float)]`,
    allows exactly the listed types. At run time the parameters exist as objects (`__type_params__`) but nothing is checked; generics are for the
    type checker, which can now tell that `r.get("small")` returns `float | None`, and that `r.add(1, "x")` is wrong. Library containers are
    generic in the same way: `list[T]`, `dict[K, V]`, and the `Sequence` and `Mapping` of 11.1."""),
)

section("extras", "`NewType`, `Annotated` and `Final`",
    p("""**`NewType("UserId", str)`** creates a distinct type for the checker that is the same as `str` at run time: a function taking a `UserId` rejects a
    plain `str` (or an `OrderId`) unless you wrap it with `UserId(value)`, which simply returns the value. It is a zero-cost way to stop ids,
    tokens or currencies of different kinds being mixed up. **`Final`** marks a name as a constant that must not be reassigned, and the checker
    enforces it. **`Annotated[T, metadata...]`** is the type `T` for the checker, with arbitrary extra metadata attached for libraries: Pydantic reads
    `Annotated[int, Field(gt=0)]` as "a positive int", FastAPI reads `Annotated[str, Query(max_length=50)]` as a query parameter constraint, and you
    can read it yourself with `get_type_hints(func, include_extras=True)`."""),
    ex("""
    from typing import Annotated, Final, NewType, get_args, get_type_hints

    UserId = NewType("UserId", str)
    MAX_TOKENS: Final = 4096

    def load_profile(user: UserId) -> str:
        return f"profile of {user}"

    uid = UserId("u-123")
    print(load_profile(uid), uid == "u-123", type(uid).__name__, UserId.__name__)

    def search(query: Annotated[str, "the user's question"], k: Annotated[int, "between 1 and 20"] = 5) -> list[str]:
        return []

    plain = get_type_hints(search)
    extras = get_type_hints(search, include_extras=True)
    print(plain["k"], extras["k"])
    print(get_args(extras["query"]))
    """, "extras.py"),
    p("""Without `include_extras=True`, `get_type_hints` strips the metadata and returns the plain type; with it, `get_args` returns the type followed by its
    metadata. That is how a schema generator can take parameter descriptions from `Annotated` instead of parsing docstrings, and how LLM tool
    frameworks let you write `city: Annotated[str, "city name, e.g. Paris"]` (problem 12)."""),
)

section("exhaustive", "Exhaustiveness with `assert_never`",
    p("""When code branches on a `Literal` or a union, you want to know that **every** case is handled, especially when a new case is added later (a new
    finish reason, a new event type). `typing.assert_never(value)` is the tool: put it in the final `else` branch. A type checker narrows the value
    through the earlier branches; if any member remains unhandled, the checker reports an error at `assert_never`, pointing at the forgotten case.
    At run time, reaching it raises `AssertionError`, which is the right behaviour for a value that should be impossible (problem 10)."""),
    ex("""
    from typing import Literal, assert_never

    Finish = Literal["stop", "length", "tool_calls"]

    def handle(reason: Finish, text: str) -> str:
        if reason == "stop":
            return text
        elif reason == "length":
            return text + " [truncated]"
        elif reason == "tool_calls":
            return "(calling a tool)"
        else:
            assert_never(reason)          # a checker errors here if a case is missing

    print(handle("stop", "done"), "|", handle("length", "half"))
    try:
        handle("content_filter", "")      # a value the type does not allow
    except AssertionError as e:
        print("AssertionError:", str(e)[:40])
    """, "assert_never.py"),
    p("""`match` statements (Python 3.10) work the same way: `case _: assert_never(reason)`. Together with `Literal` aliases and tagged `TypedDict`s (a
    `"type"` key whose value is a literal), this gives "discriminated unions", the pattern used for events in streaming APIs and for tool-call
    payloads: the tag says which shape the rest of the data has (problem 14)."""),
)

section("warmup", "Warm-up",
    predict("TypedDict at run time", "easy",
        code="""
        from typing import TypedDict, NotRequired

        class Usage(TypedDict):
            prompt_tokens: int
            completion_tokens: int
            cached_tokens: NotRequired[int]

        u = Usage(prompt_tokens=10, completion_tokens=5)
        print(u, type(u) is dict)
        print(sorted(Usage.__required_keys__), sorted(Usage.__optional_keys__))
        wrong = Usage(prompt_tokens="ten")
        print(wrong)
        try:
            isinstance(u, Usage)
        except TypeError:
            print("isinstance is not supported")
        """,
        hints=["Calling a `TypedDict` class builds a plain dict and checks nothing."],
        why="""`Usage(...)` returns an ordinary `dict`, so printing it shows a dict and `type(u) is dict` is true. The class records which keys are required and which
        are optional, but nothing enforces either, so a dict with a missing key and a string value is created without complaint: a type checker would
        flag it, Python does not. `isinstance` is refused because a `TypedDict` describes a shape, not a class that objects belong to."""),
    write("Messages with a Literal role", "easy", tag="GenAI",
        prompt="""Define `Role = Literal["system", "user", "assistant", "tool"]` and a `TypedDict` `Message` with `role: Role` and `content: str`. Write
        `make_message(role, content)` that validates the role at run time **using `get_args(Role)`** (not a separate list), raises `ValueError` for an
        empty content, and returns a `Message`. Annotate it.""",
        code="""
        from typing import Literal, TypedDict, get_args

        def make_message(role, content):
            pass
        """,
        tests="""
        import typing
        assert make_message("user", "Refund?") == {"role": "user", "content": "Refund?"}
        assert make_message("tool", "{}")["role"] == "tool"
        for role, content in [("admin", "x"), ("user", "  ")]:
            try:
                make_message(role, content)
                assert False, role
            except ValueError:
                pass
        assert typing.get_args(Role) == ("system", "user", "assistant", "tool")
        assert typing.get_type_hints(make_message) == {"role": Role, "content": str, "return": Message}
        assert typing.get_type_hints(Message) == {"role": Role, "content": str}
        """,
        hints=["Define `Role` and `Message` at module level, before the function."],
        solution="""
        from typing import Literal, TypedDict, get_args

        Role = Literal["system", "user", "assistant", "tool"]


        class Message(TypedDict):
            role: Role
            content: str


        def make_message(role: Role, content: str) -> Message:
            if role not in get_args(Role):
                raise ValueError(f"role must be one of {get_args(Role)}, got {role!r}")
            if not content.strip():
                raise ValueError("content must not be empty")
            return {"role": role, "content": content}
        """,
        why="""The `Literal` alias is the single source of truth for valid roles: the type checker uses it at every call site, and the runtime check reads the same
        values with `get_args`, so the two can never disagree. The `TypedDict` describes the dict the function returns, so code that reads
        `msg["role"]` later is checked too. Returning a plain dict keeps the message ready to send to a chat API, which expects exactly this JSON
        shape. The SDKs of OpenAI and Anthropic define their message parameters as `TypedDict`s with `Literal` roles for this reason."""),
    fix("A validation list that drifted from the type", "easy", tag="GenAI",
        prompt="""The team added `"tool_calls"` and `"content_filter"` to the `Finish` type, but `is_valid` still uses an old hard-coded list, so valid finish reasons
        are rejected. Make `is_valid` derive the allowed values from the `Finish` type itself.""",
        code="""
        from typing import Literal, get_args

        Finish = Literal["stop", "length", "tool_calls", "content_filter"]
        VALID = ["stop", "length"]

        def is_valid(reason: str) -> bool:
            return reason in VALID
        """,
        tests="""
        assert all(is_valid(r) for r in ["stop", "length", "tool_calls", "content_filter"])
        assert not is_valid("done") and not is_valid("")
        """,
        hints=["`get_args(Finish)` returns the tuple of allowed values."],
        solution="""
        from typing import Literal, get_args

        Finish = Literal["stop", "length", "tool_calls", "content_filter"]

        def is_valid(reason: str) -> bool:
            return reason in get_args(Finish)
        """,
        why="""Two definitions of the same set of values will eventually disagree, and here they did: the type knew four reasons, the check only two, so tool-calling
        responses were treated as invalid. Reading the values from the `Literal` with `get_args` leaves one definition to maintain. The same rule
        applies to enums (`Enum` classes iterate over their members) and to Pydantic models, whose JSON schema is generated from the same types that
        validate the data."""),
    predict("Annotated metadata", "easy",
        code="""
        from typing import Annotated, get_args, get_origin, get_type_hints

        Positive = Annotated[int, "must be > 0"]

        def batch(size: Positive, name: Annotated[str, "label", "max 20 chars"] = "run") -> None:
            pass

        print(get_type_hints(batch)["size"], get_type_hints(batch, include_extras=True)["size"])
        h = get_type_hints(batch, include_extras=True)["name"]
        print(get_origin(h) is Annotated, get_args(h))
        print(Positive.__metadata__, Positive.__origin__)
        """,
        hints=["Without `include_extras=True`, the metadata is stripped. `get_args` of an `Annotated` type is the type followed by its metadata."],
        why="""For type checkers, `Annotated[int, ...]` is simply `int`, and `get_type_hints` returns that by default. With `include_extras=True` the full annotation is
        kept; its origin is `Annotated`, and `get_args` returns the underlying type followed by every metadata item, which here are plain strings. An
        `Annotated` object also exposes `__origin__` (the type) and `__metadata__` (the extras), which is what Pydantic and FastAPI read."""),
)

section("medium", "Medium",
    write("Validate a dict against a TypedDict", "medium", tag="GenAI",
        prompt="""Write `check(data, td)` that validates a dict against a `TypedDict` class at run time and returns a list of problems (empty if valid): `"missing
        key: k"` for each required key that is absent, `"unknown key: k"` for keys not declared, and `"k: expected T, got U"` for values whose type is
        wrong. Support value hints that are plain classes, `Literal[...]` (the value must be one of the options), and `X | None`. Report problems
        in this order: missing keys, then unknown keys, then type problems, each sorted by key. Treat `bool` as **not** an `int`.""",
        code="""
        import types, typing

        def check(data, td):
            pass
        """,
        tests="""
        from typing import Literal, NotRequired, TypedDict

        class ToolCall(TypedDict):
            name: str
            arguments: str
            id: NotRequired[str]
            kind: Literal["function", "builtin"]
            index: int | None

        good = {"name": "search", "arguments": "{}", "kind": "function", "index": None}
        assert check(good, ToolCall) == [] and check({**good, "id": "c1", "index": 0}, ToolCall) == []
        bad = {"name": 3, "kind": "other", "extra": 1, "index": True}
        assert check(bad, ToolCall) == [
            "missing key: arguments", "unknown key: extra",
            "index: expected int | None, got bool", "kind: expected one of ('function', 'builtin'), got 'other'", "name: expected str, got int",
        ]
        """,
        hints=["Use `td.__required_keys__`, `typing.get_type_hints(td)` for the declared keys, and `typing.get_origin` to recognise `Literal` and unions.",
               "Format union hints with `str(hint)` and literals with their `get_args` tuple."],
        solution="""
        import types, typing


        def _ok(value, hint):
            origin, args = typing.get_origin(hint), typing.get_args(hint)
            if origin is typing.Literal:
                return value in args
            if origin in (types.UnionType, typing.Union):
                return any(_ok(value, a) for a in args)
            if hint is type(None):
                return value is None
            if hint is int and isinstance(value, bool):
                return False
            return isinstance(value, hint)


        def _describe(hint):
            if typing.get_origin(hint) is typing.Literal:
                return f"one of {typing.get_args(hint)}"
            return getattr(hint, "__name__", str(hint)) if typing.get_origin(hint) is None else str(hint)


        def check(data, td):
            hints = typing.get_type_hints(td)
            problems = [f"missing key: {k}" for k in sorted(td.__required_keys__ - data.keys())]
            problems += [f"unknown key: {k}" for k in sorted(data.keys() - hints.keys())]
            for key in sorted(data.keys() & hints.keys()):
                value, hint = data[key], hints[key]
                if not _ok(value, hint):
                    problems.append(f"{key}: expected {_describe(hint)}, got {value!r}" if typing.get_origin(hint) is typing.Literal
                                    else f"{key}: expected {_describe(hint)}, got {type(value).__name__}")
            return problems
        """,
        why="""A `TypedDict` carries everything a validator needs: its hints (types per key) and its required and optional key sets, with `NotRequired` keys
        allowed to be absent. Literals are checked by membership in their options, unions by trying each member, and `bool` is excluded from `int`
        because JSON booleans should not pass as indexes. Collecting **all** problems in a predictable order produces one complete error report,
        which is far more useful when the data came from a model and you want to send the errors back for repair (7.4). This is a small version of
        what Pydantic's `TypeAdapter(ToolCall).validate_python(data)` does, including turning the `TypedDict` into a validator."""),
    fix("A helper that forgets what type it returns", "medium", tag="Data work",
        prompt="""`first` and `pick` are annotated with `Any`, so a type checker cannot tell that `first(["a"])` is a `str`. Rewrite their annotations as
        **generic** functions with type parameters (Python 3.12 syntax): `first[T](items: Iterable[T]) -> T | None` and
        `pick[K, V](mapping: Mapping[K, V], keys: Iterable[K]) -> dict[K, V]`. Keep the behaviour.""",
        code="""
        from collections.abc import Iterable, Mapping
        from typing import Any

        def first(items: Iterable[Any]) -> Any:
            for item in items:
                return item
            return None

        def pick(mapping: Mapping[Any, Any], keys: Iterable[Any]) -> dict[Any, Any]:
            return {k: mapping[k] for k in keys if k in mapping}
        """,
        tests="""
        import typing
        from collections.abc import Iterable, Mapping
        assert first(["a", "b"]) == "a" and first([]) is None and pick({"a": 1, "b": 2}, ["b", "z"]) == {"b": 2}
        (T,) = first.__type_params__
        assert T.__name__ == "T" and typing.get_type_hints(first) == {"items": Iterable[T], "return": T | None}
        K, V = pick.__type_params__
        assert typing.get_type_hints(pick) == {"mapping": Mapping[K, V], "keys": Iterable[K], "return": dict[K, V]}
        """,
        hints=["`def first[T](items: Iterable[T]) -> T | None:` declares `T` for this function only."],
        solution="""
        from collections.abc import Iterable, Mapping

        def first[T](items: Iterable[T]) -> T | None:
            for item in items:
                return item
            return None

        def pick[K, V](mapping: Mapping[K, V], keys: Iterable[K]) -> dict[K, V]:
            return {k: mapping[k] for k in keys if k in mapping}
        """,
        why="""`Any` switches checking off, so the information "the result has the same type as the elements" was lost, and a caller doing `first(names).upper()` or
        `first(scores) + 1` got no help at all. Type parameters keep the link: for `first(["a"])` the checker solves `T = str` and knows the result is
        `str | None`, so it also insists on the `None` check. `pick` relates three types at once: the keys you pass must match the mapping's key type, and
        the result keeps both. The parameters are visible at run time in `__type_params__`, but only the checker uses them."""),
    write("A typed cache class", "medium", tag="ML",
        prompt="""Write a generic class `LRU[K, V]` (Python 3.12 syntax) with `__init__(self, maxsize: int)`, `get(self, key: K) -> V | None` (marks the key as
        recently used), `put(self, key: K, value: V) -> None` (evicts the least recently used key when full), `__len__` and `__contains__`. Annotate every
        method.""",
        code="""
        class LRU:
            pass
        """,
        tests="""
        import typing
        c: "LRU[str, list[float]]" = LRU(2)
        c.put("a", [0.1]); c.put("b", [0.2])
        assert c.get("a") == [0.1]
        c.put("c", [0.3])
        assert "b" not in c and "a" in c and len(c) == 2 and c.get("b") is None
        K, V = LRU.__type_params__
        assert typing.get_type_hints(LRU.get) == {"key": K, "return": V | None}
        assert typing.get_type_hints(LRU.put) == {"key": K, "value": V, "return": type(None)}
        assert typing.get_type_hints(LRU.__init__) == {"maxsize": int, "return": type(None)}
        """,
        hints=["`class LRU[K, V]:` declares the parameters for the whole class. Store `self._data: dict[K, V] = {}`; dict order tracks recency (9.2)."],
        solution="""
        class LRU[K, V]:
            def __init__(self, maxsize: int) -> None:
                self.maxsize = maxsize
                self._data: dict[K, V] = {}

            def get(self, key: K) -> V | None:
                if key not in self._data:
                    return None
                value = self._data.pop(key)
                self._data[key] = value
                return value

            def put(self, key: K, value: V) -> None:
                if key in self._data:
                    del self._data[key]
                elif len(self._data) >= self.maxsize:
                    del self._data[next(iter(self._data))]
                self._data[key] = value

            def __len__(self) -> int:
                return len(self._data)

            def __contains__(self, key: object) -> bool:
                return key in self._data
        """,
        why="""With the class parameterised, a variable annotated `LRU[str, list[float]]` lets the checker verify every use: `put(1, [0.1])` is a wrong key type,
        `get("a")` returns `list[float] | None`, so callers must handle a miss. The implementation is the dict-ordering LRU of 9.2. `__contains__` takes
        `object` because `in` may be asked about anything; restricting it to `K` would make harmless checks a type error. Generic containers are
        everywhere in library code (vector stores keyed by id, caches, registries), and typing them once makes every user's code checked."""),
    trace("Literal, Annotated and generics at run time", "medium",
        prompt="Fill in `r` after each marked line.",
        code="""
        import typing
        from typing import Annotated, Literal

        Mode = Literal["fast", "accurate"]
        Score = Annotated[float, "0 to 1"]

        def f[T](x: T) -> list[T]:
            return [x]

        r = typing.get_args(Mode)  # row: "Literal options"
        r = typing.get_args(Score)  # row: "Annotated parts"
        r = [p.__name__ for p in f.__type_params__]  # row: "type params"
        r = f("x") + f(1)  # row: "calling a generic"
        r = typing.get_args(Literal["a"] | Literal["b"] | None)  # row: "combined literals"
        """,
        trace_vars=["r"],
        hints=["Generics are not checked at run time, so `f` works for any value. A union keeps each of its members, literals included."],
        why="""`get_args` gives a literal's options and an `Annotated` type's base type plus metadata. Type parameters are real objects with names. Calling the generic
        function with different types works, because nothing is checked at run time; a type checker would infer `list[str]` and `list[int]`. A union of
        literals keeps each `Literal` as a separate member at run time (a type checker treats it like `Literal["a", "b"]`), followed by `NoneType`."""),
    fix("A callback called with the wrong arguments", "medium", tag="GenAI",
        prompt="""`stream_reply` is documented (and typed) to call `on_token` with **one** argument, the token text, but it calls it with two, so every callback
        written to the hint fails with `TypeError`. Fix the call so it matches the `Callable[[str], None]` hint, and keep the token count as the return value.""",
        code="""
        from collections.abc import Callable

        def stream_reply(tokens: list[str], on_token: Callable[[str], None]) -> int:
            for i, token in enumerate(tokens):
                on_token(i, token)
            return len(tokens)
        """,
        tests="""
        seen = []
        assert stream_reply(["Refunds", " take", " 5 days."], seen.append) == 3 and seen == ["Refunds", " take", " 5 days."]
        printed = []
        assert stream_reply([], printed.append) == 0 and printed == []
        """,
        hints=["The hint says the callback takes exactly one string."],
        solution="""
        from collections.abc import Callable

        def stream_reply(tokens: list[str], on_token: Callable[[str], None]) -> int:
            for token in tokens:
                on_token(token)
            return len(tokens)
        """,
        why="""`Callable[[str], None]` is a contract in both directions: callers may pass any function that takes one string, and the function promises to call it
        that way. Calling it with an index as well broke every conforming callback, here `list.append`, which takes exactly one argument. A type
        checker would report the call `on_token(i, token)` as having too many arguments, before the code ever ran. If the index were really needed, the
        right change is to the hint, `Callable[[int, str], None]`, and to every caller, which the checker would then list."""),
    write("Handle every finish reason", "medium", tag="GenAI",
        prompt="""Define `Finish = Literal["stop", "length", "tool_calls", "content_filter"]` and write `postprocess(reason: Finish, text: str) -> str`:
        `"stop"` returns the text stripped; `"length"` returns the stripped text plus `" ..."`; `"tool_calls"` returns `""`; `"content_filter"` returns
        `"[filtered]"`. End the branches with `typing.assert_never(reason)`, so a missing case is a type error and an unknown value raises
        `AssertionError` at run time. Use a `match` statement.""",
        code="""
        from typing import Literal, assert_never

        def postprocess(reason, text):
            pass
        """,
        tests="""
        import typing
        assert postprocess("stop", " Done. ") == "Done." and postprocess("length", "The policy says ") == "The policy says ..."
        assert postprocess("tool_calls", "x") == "" and postprocess("content_filter", "y") == "[filtered]"
        try:
            postprocess("end_turn", "z")
            assert False
        except AssertionError:
            pass
        assert typing.get_args(Finish) == ("stop", "length", "tool_calls", "content_filter")
        assert typing.get_type_hints(postprocess)["reason"] == Finish
        """,
        hints=["`match reason:` with `case \"stop\":` and so on, and `case _: assert_never(reason)`."],
        solution="""
        from typing import Literal, assert_never

        Finish = Literal["stop", "length", "tool_calls", "content_filter"]

        def postprocess(reason: Finish, text: str) -> str:
            match reason:
                case "stop":
                    return text.strip()
                case "length":
                    return text.strip() + " ..."
                case "tool_calls":
                    return ""
                case "content_filter":
                    return "[filtered]"
                case _:
                    assert_never(reason)
        """,
        why="""The checker narrows `reason` through each `case`; if someone later adds `"end_turn"` to `Finish` without a new case, `assert_never` receives a value whose
        type is not `Never`, and the checker reports it right there, so the forgotten case is caught before deployment. At run time, a value outside
        the type (an unexpected string from a new API version) reaches `assert_never`, which raises `AssertionError` instead of silently returning
        `None`. Different providers name finish reasons differently (`end_turn`, `max_tokens`), so a mapping into one internal `Literal` plus an
        exhaustive handler is a robust way to support several (7.4)."""),
    predict("NewType and Final at run time", "medium",
        code="""
        from typing import Final, NewType

        UserId = NewType("UserId", str)
        OrderId = NewType("OrderId", str)
        LIMIT: Final = 10

        u = UserId("u-1")
        o = OrderId("u-1")
        print(u == o, type(u).__name__, UserId("x") == "x")
        print(UserId.__name__, UserId.__supertype__.__name__)
        LIMIT = 20
        print(LIMIT)
        try:
            isinstance(u, UserId)
        except TypeError:
            print("isinstance not supported")
        """,
        hints=["`NewType` returns its argument unchanged at run time; only the checker sees a distinct type. `Final` is not enforced at run time."],
        why="""At run time a `NewType` is an identity function: `UserId("u-1")` is just the string, so a user id and an order id with the same text compare equal and
        are both `str`. The distinction exists only for the type checker, which would reject passing an `OrderId` where a `UserId` is expected.
        `__supertype__` records the underlying type. Reassigning a `Final` name works at run time; the checker reports it. And `isinstance` refuses
        a `NewType`, since there is no class to test against."""),
)

section("hard", "Hard",
    write("A JSON schema from a TypedDict", "hard", tag="GenAI",
        prompt="""Structured-output and tool APIs take a JSON Schema. Write `json_schema(td)` for a `TypedDict` class whose value hints may be `str`, `int`, `float`,
        `bool`, `list[X]`, `Literal[...]` (becomes `{"type": "string", "enum": [...]}` for string literals), `X | None` (adds `"null"` to the type), and
        any of these wrapped in `Annotated[X, "description"]` (adds `"description"`). Return `{"type": "object", "properties": {...}, "required": [...],
        "additionalProperties": False}` with `required` from the class's required keys, sorted.""",
        code="""
        import types, typing

        def json_schema(td):
            pass
        """,
        tests="""
        from typing import Annotated, Literal, NotRequired, TypedDict

        class Classification(TypedDict):
            label: Annotated[Literal["spam", "ham", "phish"], "the predicted class"]
            confidence: Annotated[float, "between 0 and 1"]
            reasons: list[str]
            language: NotRequired[str | None]

        assert json_schema(Classification) == {
            "type": "object",
            "properties": {
                "label": {"type": "string", "enum": ["spam", "ham", "phish"], "description": "the predicted class"},
                "confidence": {"type": "number", "description": "between 0 and 1"},
                "reasons": {"type": "array", "items": {"type": "string"}},
                "language": {"type": ["string", "null"]},
            },
            "required": ["confidence", "label", "reasons"],
            "additionalProperties": False,
        }

        class Tiny(TypedDict):
            n: int
        assert json_schema(Tiny) == {"type": "object", "properties": {"n": {"type": "integer"}}, "required": ["n"], "additionalProperties": False}
        """,
        hints=["Read hints with `typing.get_type_hints(td, include_extras=True)` so `Annotated` metadata survives.",
               "A recursive `_schema(hint)`: unwrap `NotRequired` and `Annotated` (both survive `include_extras`), then handle unions, `Literal`, `list` and plain classes."],
        solution="""
        import types, typing

        SIMPLE = {str: "string", int: "integer", float: "number", bool: "boolean"}


        def _schema(hint):
            origin, args = typing.get_origin(hint), typing.get_args(hint)
            if origin in (typing.NotRequired, typing.Required):
                return _schema(args[0])               # kept by include_extras; the key set already says it
            if origin is typing.Annotated:
                schema = _schema(args[0])
                descriptions = [m for m in args[1:] if isinstance(m, str)]
                if descriptions:
                    schema["description"] = descriptions[0]
                return schema
            if origin in (types.UnionType, typing.Union):
                members = [a for a in args if a is not type(None)]
                if len(members) != 1 or len(members) == len(args):
                    raise TypeError(f"only X | None unions are supported: {hint!r}")
                schema = _schema(members[0])
                schema["type"] = [schema["type"], "null"]
                return schema
            if origin is typing.Literal:
                return {"type": "string", "enum": list(args)}
            if origin is list:
                return {"type": "array", "items": _schema(args[0])}
            if hint in SIMPLE:
                return {"type": SIMPLE[hint]}
            raise TypeError(f"unsupported type: {hint!r}")


        def json_schema(td):
            hints = typing.get_type_hints(td, include_extras=True)
            return {
                "type": "object",
                "properties": {name: _schema(h) for name, h in hints.items()},
                "required": sorted(td.__required_keys__),
                "additionalProperties": False,
            }
        """,
        why="""This is the bridge between Python types and constrained LLM output: the `TypedDict` describes the answer you want, and the generated schema is what you
        send as the response format or tool parameters, so the model can only produce the listed labels (`enum`), a number for confidence, and a list of
        strings for reasons. `Annotated` carries the per-field descriptions into the schema, where they act as instructions to the model.
        `include_extras=True` is essential, or the metadata is stripped; it also keeps the `NotRequired` wrapper, which the schema unwraps because
        the class's key sets already record which keys are optional. `NotRequired` keys are left out of `required`, and `additionalProperties: False`
        forbids invented fields, which strict structured-output modes require. Pydantic's `model_json_schema()` and `TypeAdapter(...).json_schema()` do
        this generation for you (11.4), but this is what they produce."""),
    fix("Read the code: an event dispatcher", "hard", tag="GenAI",
        prompt="""Streaming events have a `"type"` tag, declared as `EventType = Literal["text", "tool_call", "error", "done"]`. `dispatch` should route each event to the
        handler registered for its type, reject event types outside `EventType`, and require every type to have a handler at **registration** time
        (`build_dispatcher` checks completeness). Unknown types are silently ignored, a missing handler is only discovered when such an event arrives, and
        the descriptions printed by `describe_handlers` are always empty because the code reads the `Annotated` metadata wrongly. Read it, find the bugs and
        fix them.""",
        code="""
        from typing import Annotated, Literal, get_args, get_type_hints

        EventType = Literal["text", "tool_call", "error", "done"]


        def build_dispatcher(handlers):
            def dispatch(event):
                handler = handlers.get(event["type"])
                if handler is None:
                    return None
                return handler(event)
            return dispatch


        def describe_handlers(handlers):
            out = {}
            for etype, fn in handlers.items():
                hint = get_type_hints(fn).get("event")
                meta = getattr(hint, "__metadata__", ())
                out[etype] = meta[0] if meta else ""
            return out
        """,
        tests="""
        def on_text(event: Annotated[dict, "append text to the reply"]):
            return "text:" + event["text"]
        def on_tool(event: Annotated[dict, "run the requested tool"]):
            return "tool:" + event["name"]
        def on_error(event: Annotated[dict, "surface the error"]):
            return "error:" + event["message"]
        def on_done(event: Annotated[dict, "finish the turn"]):
            return "done"

        handlers = {"text": on_text, "tool_call": on_tool, "error": on_error, "done": on_done}
        dispatch = build_dispatcher(handlers)
        assert dispatch({"type": "text", "text": "Hi"}) == "text:Hi" and dispatch({"type": "done"}) == "done"
        try:
            dispatch({"type": "ping"})
            assert False, "unknown event types must be rejected"
        except ValueError as e:
            assert "ping" in str(e)
        try:
            build_dispatcher({"text": on_text, "done": on_done})
            assert False, "missing handlers must be caught at build time"
        except ValueError as e:
            assert "error" in str(e) and "tool_call" in str(e)
        assert describe_handlers(handlers) == {"text": "append text to the reply", "tool_call": "run the requested tool",
                                               "error": "surface the error", "done": "finish the turn"}
        """,
        hints=["Compare `set(handlers)` with `set(get_args(EventType))` when building; report missing types sorted.",
               "In `dispatch`, an event type outside `get_args(EventType)` raises `ValueError`.",
               "`get_type_hints` strips `Annotated` unless you pass `include_extras=True`."],
        solution="""
        from typing import Annotated, Literal, get_args, get_type_hints

        EventType = Literal["text", "tool_call", "error", "done"]
        EVENT_TYPES = frozenset(get_args(EventType))


        def build_dispatcher(handlers):
            missing = EVENT_TYPES - handlers.keys()
            extra = handlers.keys() - EVENT_TYPES
            if missing or extra:
                raise ValueError(f"handlers do not match EventType: missing {sorted(missing)}, unknown {sorted(extra)}")

            def dispatch(event):
                etype = event.get("type")
                if etype not in EVENT_TYPES:
                    raise ValueError(f"unknown event type {etype!r}")
                return handlers[etype](event)
            return dispatch


        def describe_handlers(handlers):
            out = {}
            for etype, fn in handlers.items():
                hint = get_type_hints(fn, include_extras=True).get("event")
                meta = getattr(hint, "__metadata__", ())
                out[etype] = meta[0] if meta else ""
            return out
        """,
        why="""Three bugs. Unknown event types returned `None` silently, so a new event type from a provider (or a typo in your own code) disappeared without a trace;
        rejecting values outside the `Literal` turns it into an immediate, named error. Completeness was only discovered at run time, when an `error`
        event finally arrived and found no handler; checking the registered types against `get_args(EventType)` when the dispatcher is built is the
        runtime version of `assert_never`'s exhaustiveness, and it also catches handlers registered under misspelt types. And `get_type_hints` strips
        `Annotated` metadata by default, so `__metadata__` was never there; `include_extras=True` keeps it. The `Literal` alias is the single source of
        truth for all three checks."""),
    write("Parse a tagged union of events", "hard", tag="GenAI",
        prompt="""Define three `TypedDict`s that share a `type` key with a `Literal` tag: `TextEvent` (`type: Literal["text"]`, `text: str`), `ToolEvent` (`type:
        Literal["tool"]`, `name: str`, `args: dict`), `DoneEvent` (`type: Literal["done"]`, `tokens: int`). Write `parse_event(data)` that picks the
        `TypedDict` whose tag matches `data["type"]` (build the mapping from the classes' hints, not by hand), checks that the required keys are present
        with the right plain types (`bool` is not an `int`), and returns `(class_name, data)`. Raise `ValueError` with a clear message for an unknown or
        missing tag, a missing key, or a wrong type.""",
        code="""
        import typing
        from typing import Literal, TypedDict

        def parse_event(data):
            pass
        """,
        tests="""
        assert parse_event({"type": "text", "text": "Hi"}) == ("TextEvent", {"type": "text", "text": "Hi"})
        assert parse_event({"type": "tool", "name": "search", "args": {"q": "x"}})[0] == "ToolEvent"
        assert parse_event({"type": "done", "tokens": 42})[0] == "DoneEvent"
        for bad, word in [({"type": "ping"}, "ping"), ({"text": "x"}, "type"), ({"type": "tool", "name": "s"}, "args"),
                          ({"type": "done", "tokens": "42"}, "tokens"), ({"type": "done", "tokens": True}, "tokens")]:
            try:
                parse_event(bad)
                assert False, bad
            except ValueError as e:
                assert word in str(e), (bad, str(e))
        assert sorted(EVENTS) == ["done", "text", "tool"] and EVENTS["tool"] is ToolEvent
        """,
        hints=["Build `EVENTS = {typing.get_args(typing.get_type_hints(cls)[\"type\"])[0]: cls for cls in (TextEvent, ToolEvent, DoneEvent)}`.",
               "For the other keys, compare `type(value)`-compatibility with `isinstance`, excluding `bool` for `int`."],
        solution="""
        import typing
        from typing import Literal, TypedDict


        class TextEvent(TypedDict):
            type: Literal["text"]
            text: str


        class ToolEvent(TypedDict):
            type: Literal["tool"]
            name: str
            args: dict


        class DoneEvent(TypedDict):
            type: Literal["done"]
            tokens: int


        EVENTS = {typing.get_args(typing.get_type_hints(cls)["type"])[0]: cls for cls in (TextEvent, ToolEvent, DoneEvent)}


        def parse_event(data):
            if "type" not in data:
                raise ValueError("event has no 'type' tag")
            cls = EVENTS.get(data["type"])
            if cls is None:
                raise ValueError(f"unknown event type {data['type']!r}; expected one of {sorted(EVENTS)}")
            hints = typing.get_type_hints(cls)
            for key in sorted(cls.__required_keys__ - {"type"}):
                if key not in data:
                    raise ValueError(f"{cls.__name__}: missing key {key!r}")
                expected, value = hints[key], data[key]
                if (expected is int and isinstance(value, bool)) or not isinstance(value, expected):
                    raise ValueError(f"{cls.__name__}: {key!r} must be {expected.__name__}, got {type(value).__name__}")
            return cls.__name__, data
        """,
        why="""A **discriminated union** is a set of shapes distinguished by one tag field, and the tag tells you which shape to validate against: exactly how
        streaming events, tool calls and many JSON APIs are structured. Building the tag-to-class mapping from the classes' own `Literal` hints keeps
        it in sync with the definitions, so adding a fourth event type is a new class plus one name in the tuple. Each kind of failure gets its own
        message (unknown tag, missing key, wrong type), which is what you want in logs when a provider changes its format. For a type checker, after
        checking `data["type"] == "tool"` on a `TextEvent | ToolEvent | DoneEvent`, the value narrows to `ToolEvent`, so `data["name"]` is known to be a
        string. Pydantic supports this pattern directly with `Field(discriminator="type")` (11.4)."""),
    predict("Type parameters and type aliases at run time", "hard",
        code="""
        type Pair[T] = tuple[T, T]
        type Matrix = list[list[float]]

        def swap[T](p: Pair[T]) -> Pair[T]:
            return (p[1], p[0])

        print(swap((1, 2)), swap(("a", 3)))
        (T,) = swap.__type_params__
        print(T.__name__, type(T).__name__, Pair.__name__, Pair.__type_params__[0].__name__)
        print(Matrix.__value__, Pair[int].__value__ if hasattr(Pair[int], "__value__") else Pair.__value__)
        print(type(Matrix).__name__, Pair[str])
        """,
        hints=["The `type` statement creates a `TypeAliasType` whose value is evaluated lazily and available as `__value__`.",
               "Nothing about type parameters is checked when the function runs."],
        why="""`swap` runs for any tuple, including the mixed `("a", 3)`, which a type checker would reject for `Pair[T]` (both items must share a type). The type
        parameter is a `TypeVar` object named `T`. The `type` statement creates a `TypeAliasType` with its own name and parameters, whose value is
        evaluated on demand and exposed as `__value__`; subscripting it, `Pair[int]` or `Pair[str]`, gives a parameterised alias that prints as
        written. `Pair[int]` forwards attribute access to the alias, so its `__value__` is the alias's own value, `tuple[T, T]`, not `tuple[int, int]`:
        substituting `int` for `T` is something only the type checker does."""),
)

section("interview", "Interview questions",
    explain("When would you use a `TypedDict`, a dataclass, or a Pydantic model?", "medium", tag="Interview",
        why="""A `TypedDict` is for data that should **stay a dict**: JSON payloads, API parameters, messages passed straight to an SDK. It costs nothing at run time
        and gives static checking of keys and value types, but no validation, no methods and no defaults. A **dataclass** is for structured objects
        inside your program: it generates `__init__`, `__repr__` and `__eq__` from typed fields, supports defaults, immutability and slots, and is
        fast, but it does not validate or convert input. A **Pydantic model** is for data crossing a boundary: requests, configuration, files, LLM
        output; it validates and converts at run time, collects errors, serialises to and from JSON and generates JSON Schema, at some cost per object.
        A common architecture validates external data into Pydantic models at the edges, uses dataclasses or plain typed objects internally, and keeps
        TypedDicts for the exact JSON shapes that third-party SDKs expect."""),
    explain("What are generic types and type parameters for?", "medium", tag="Interview",
        why="""They let one piece of code work for many types while keeping the relationships between types visible to the checker. Without them, a function like
        `first(items)` or a container like a cache must use `Any`, and the checker forgets that `first(list_of_str)` returns a `str` or that `cache.get(key)`
        returns the cached value's type, so errors downstream go unnoticed. With a type parameter, `def first[T](items: Iterable[T]) -> T | None`, the
        checker solves `T` from each call; with a generic class, `class Cache[K, V]`, each instance is checked against its declared key and value types.
        Bounds (`[K: Hashable]`) and constraints (`[T: (int, float)]`) restrict what `T` may be. The standard collections (`list[T]`, `dict[K, V]`,
        `Sequence[T]`) are generic in exactly this way. At run time nothing is enforced: generics are a static tool, introspectable through
        `__type_params__`."""),
    explain("How do Python types relate to structured output from LLMs?", "hard", tag="Interview",
        why="""Structured output (JSON mode with a schema, tool calling, "response format") constrains the model to produce JSON matching a JSON Schema, and that
        schema is best generated from Python types rather than written by hand: a `TypedDict`, dataclass or Pydantic model describes the fields, `Literal`
        becomes an `enum` so the model can only choose valid labels, `X | None` becomes nullable, `list[X]` becomes an array, and `Annotated` metadata or
        field descriptions become instructions the model reads. Required keys and `additionalProperties: false` keep it from omitting or inventing
        fields. The reply must still be **validated** against the same types (constraints can fail or be unsupported on some models, and values can be
        semantically wrong), usually by parsing into a Pydantic model, with a repair or retry loop that sends the validation errors back (7.4). Using
        the types as the single source of truth keeps the prompt, the schema, the validator and the code that consumes the result in agreement."""),
)

recap(
    "`TypedDict` types JSON-shaped dicts (required and `NotRequired` keys); at run time it is a plain dict and validates nothing.",
    "`Literal[...]` lists exact allowed values; read them with `get_args` so runtime checks and the type share one definition.",
    "`Callable[[args], ret]` types callbacks; type parameters (`def f[T]`, `class C[K, V]`) keep input and output types linked.",
    "`NewType` makes distinct ids for the checker at zero cost; `Annotated` attaches metadata for libraries; `Final` marks constants.",
    "`assert_never` makes branches over literals and unions exhaustive; tagged `TypedDict`s form discriminated unions.",
)
