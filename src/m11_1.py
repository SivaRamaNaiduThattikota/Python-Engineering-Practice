from lesson import *
from diagrams import *

lesson(
    id="m11-1", num="11.1", title="Type hints",
    intro="Type hints describe what a function accepts and returns. What they are and are not (Python does not enforce "
          "them), the syntax for variables, parameters, returns and built-in generics, unions and `None`, narrowing, "
          "accepting abstract types and returning concrete ones, what a type checker such as mypy or pyright reports, "
          "and how libraries read hints at run time. Applied to text utilities, tool schemas, settings and validation.",
    desc="Annotations, unions, generics, `Optional`, and what a type checker does.",
    keys="type hint annotation typing mypy pyright static type checker int str list dict tuple generic union optional none narrowing isinstance iterable sequence mapping any object get_type_hints get_origin get_args runtime validation annotationlib",
)

term("Type hint", "An annotation such as `x: int` or `-> list[str]` that documents the expected type. Python stores it but does not check it.")
term("Type checker", "A tool (mypy, pyright) that reads hints without running the code and reports calls and returns that do not match.")
term("Narrowing", "When a check such as `if x is None: return` lets a type checker treat `x` as a more specific type (here, not `None`) in the code that follows.")
term("Generic type", "A type with parameters, such as `list[str]` or `dict[str, float]`, describing what the container holds.")

section("what", "What type hints are, and what they are not",
    fig(stage_map(11, "a typed evaluation run"), "Module 11 at a glance: type hints for checkers, dataclasses for trusted data, Pydantic for validation at the boundary."),
    fig(chain(["code with type hints", "a type checker reads it|(mypy, pyright)", "reports mismatches|before running", ("at run time: hints are|not checked at all", "warn")]),
        "Type hints are checked by tools before the program runs; Python itself ignores them when executing."),
    p("""A **type hint** (or annotation) states the type a value is expected to have: `def chunk(text: str, size: int) -> list[str]:` says that `text`
    is a string, `size` an integer, and that the function returns a list of strings. Hints serve three audiences. **People** read them as precise
    documentation of the interface. **Editors** use them for completion and inline errors. **Type checkers**, such as mypy and pyright, analyse the
    whole program without running it and report calls that pass the wrong type, return values that do not match, attributes that do not exist,
    and possible `None` values used carelessly."""),
    p("""What hints are **not** is a run-time check. Python stores them (in `func.__annotations__`) and otherwise ignores them: calling the function with
    the wrong type runs exactly as it would without hints, and fails, or worse, does not fail, wherever the wrong value is first used. Checking at
    run time is the job of libraries that **read** the hints, such as Pydantic (11.4), FastAPI and the tool-schema generators of 8.4."""),
    ex("""
    import typing

    def chunk(text: str, size: int = 200) -> list[str]:
        return [text[i:i + size] for i in range(0, len(text), size)]

    print(chunk("abcdefg", 3))
    print(chunk(["a", "b", "c", "d"], 2))         # the wrong type: Python does not stop it
    print(chunk.__annotations__)
    print(typing.get_type_hints(chunk))
    """, "not_enforced.py"),
    p("""The second call passed a list where a string was expected and quietly returned a list of lists: the hint documented the mistake, but only a
    type checker (before running) or validation code (while running) would have caught it. In Python 3.14, annotations are also evaluated
    **lazily** (PEP 649): the expressions are computed only when something asks for them, so a hint can refer to a class defined later in the
    file without quotes. `typing.get_type_hints(func)` is still the reliable way to get them as real types (8.4)."""),
)

section("syntax", "The syntax: variables, parameters, returns and containers",
    p("""Parameters are annotated with a colon, `name: type`, with the default after it, `size: int = 200`. The return type follows an arrow before the
    colon of the `def`, `-> list[str]`; a function that returns nothing is annotated `-> None`. Variables can be annotated too, `count: int = 0`,
    which is mostly useful for attributes in classes (11.3) and for empty containers whose type cannot be guessed: `seen: set[str] = set()`."""),
    p("""Containers take their element types in square brackets, using the built-in names directly (Python 3.9+): `list[str]` (a list of strings),
    `dict[str, float]` (keys and values), `set[int]`, `tuple[str, int]` (a pair: a string then an int, fixed length) and `tuple[int, ...]` (any number
    of ints). Nesting works as you would expect: `dict[str, list[tuple[int, float]]]`. For readability, give complex types a name, a **type alias**:
    `type Vector = list[float]` (Python 3.12+) or simply `Vector = list[float]`."""),
    ex("""
    import typing

    type Vector = list[float]
    Scores = dict[str, float]

    def top_k(scores: Scores, k: int = 3) -> list[tuple[str, float]]:
        return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:k]

    def mean_vector(vectors: list[Vector]) -> Vector:
        n = len(vectors)
        return [sum(col) / n for col in zip(*vectors)]

    def log_event(name: str, **fields: str | int) -> None:
        print("event", name, fields)

    print(top_k({"faq": 0.9, "terms": 0.4, "blog": 0.7}, 2))
    print(mean_vector([[1.0, 2.0], [3.0, 4.0]]))
    log_event("search", query="refund", k=3)
    print(typing.get_type_hints(top_k)["return"], typing.get_type_hints(log_event))
    """, "syntax.py"),
    p("""`**fields: str | int` annotates the type of **each** keyword value, not of the dict, and `*args: int` likewise annotates each positional extra. Hints
    describe what the code accepts; they should be true. A hint that claims `-> list[str]` while one branch returns `None` is worse than no hint,
    because it tells readers and tools something false (problem 3)."""),
)

section("unions", "Unions, `None` and narrowing",
    fig(flowchart({
        "in": ("start", 0, 0, "x: str | None"),
        "ask": ("ask", 0, 1, "x is None?"),
        "none": ("warn", 1, 1, "here x is None:|return a default"),
        "str": ("good", 0, 2, "here x is str:|x.upper() is safe"),
    }, [("in", "ask"), ("ask", "none", "yes"), ("ask", "str", "no")], cell=(230, 80), label="narrowing an optional value"),
        "Checking for `None` narrows the type: after the check, the checker knows which branch has a real string."),
    p("""A value that can be one of several types has a **union** type, written `A | B` (Python 3.10+; older code writes `Union[A, B]`). The most common
    union is "a value or nothing": `str | None`, which older code writes as `Optional[str]`. The name `Optional` misleads: it does not mean "an
    optional argument" (that is a default value), it means "**may be `None`**". `def find(q: str) -> Doc | None` warns every caller that the result
    must be checked before use."""),
    p("""Type checkers follow your code's checks, which is called **narrowing**. After `if doc is None: return`, the checker knows `doc` is a `Doc` in the
    rest of the function; after `if isinstance(x, str):`, it treats `x` as a string inside the branch. That is exactly how you should write code
    with unions: check, then use. Using a `str | None` value without a check is the single most common error type checkers find in real code,
    because it is the `AttributeError: 'NoneType' object has no attribute ...` of production."""),
    ex("""
    def find_doc(docs: dict[str, str], doc_id: str) -> str | None:
        return docs.get(doc_id)

    def title_of(docs: dict[str, str], doc_id: str) -> str:
        text = find_doc(docs, doc_id)
        if text is None:                      # narrowing: after this, text is a str
            return "(missing)"
        return text.split("\\n", 1)[0].strip()

    def describe(value: int | str | list[str]) -> str:
        if isinstance(value, int):
            return f"number {value}"
        if isinstance(value, str):
            return f"text of {len(value)} chars"
        return f"list of {len(value)} items"

    docs = {"faq": "Refunds\\nTake 5 days."}
    print(title_of(docs, "faq"), "|", title_of(docs, "nope"))
    print([describe(v) for v in [3, "abc", ["a", "b"]]])
    print(isinstance(3, int | str), isinstance(None, str | None))
    """, "unions.py"),
    p("""Deciding between returning `None` and raising is a design choice (7.3): return `X | None` when "not found" is a normal outcome callers will handle,
    raise when it is an error. Since Python 3.10, `isinstance` accepts a union directly, as the last line shows, but not a parameterised
    generic: `isinstance(x, list[str])` raises `TypeError`, because checking every element is not what `isinstance` does (problem 4)."""),
)

section("abstract", "Accept general types, return specific ones",
    fig(table(["in a signature", "prefer", "because"], [
        ["parameters", "Iterable[str], Mapping[str, int]", "callers can pass any suitable type"],
        ["return value", "list[str], dict[str, int]", "callers get a precise type"],
    ], label="accept general types, return specific ones"),
        "Accept the most general type that works and return the most specific one you can promise."),
    p("""For parameters, annotate with the **most general type your code actually needs**. A function that only loops over its input needs an
    `Iterable[str]`, so it accepts lists, tuples, sets, generators and files; one that indexes and takes `len` needs a `Sequence[str]`; one that only
    reads keys needs a `Mapping[str, float]`, which also accepts read-only mappings. These come from `collections.abc` (9.5). Annotating
    `list[str]` instead makes the type checker reject a perfectly good tuple or generator, the static twin of the `isinstance(x, list)` mistake of
    9.5 (problem 6). For return values, be **specific**: return `list[str]`, not `Iterable[str]`, so callers know they can index and append."""),
    ex("""
    from collections.abc import Iterable, Mapping, Sequence

    def count_tokens(texts: Iterable[str]) -> int:
        return sum(len(t.split()) for t in texts)

    def last(items: Sequence[str]) -> str:
        return items[-1]

    def total_cost(prices: Mapping[str, float], usage: Mapping[str, int]) -> float:
        return round(sum(prices[m] * n for m, n in usage.items()), 4)

    print(count_tokens(["a b", "c"]), count_tokens(("x",)), count_tokens(t for t in ["one two"]))
    print(last(("a", "b")), last("xyz"), total_cost({"small": 0.002}, {"small": 1500}))
    """, "abstract_types.py"),
    p("""Two special types complete the picture. **`Any`** switches type checking off for a value: anything can be assigned to it and anything can be done
    with it, which is how untyped code and JSON-like data enter a typed program; use it sparingly, at boundaries. **`object`** is the opposite in
    spirit: it accepts any value too, but the checker then lets you do almost nothing with it until you narrow it, which makes it the honest type for
    "I accept anything and will check what it is"."""),
)

section("checker", "What a type checker reports",
    p("""A type checker reads your code and the hints, infers types for everything it can (local variables, expressions, return values), and reports
    places where they cannot fit together. You run it like a linter, `mypy src/` or `pyright`, locally and in CI; nothing changes at run time. Typical
    reports look like this:"""),
    html("""<div class="tbl"><table>
      <tr><th>Code</th><th>What the checker says</th></tr>
      <tr><td><code>chunk(["a", "b"], 2)</code></td><td>Argument 1 has incompatible type "list[str]"; expected "str"</td></tr>
      <tr><td><code>title = find_doc(docs, "x").upper()</code></td><td>Item "None" of "str | None" has no attribute "upper"</td></tr>
      <tr><td><code>def f() -> int: return "3"</code></td><td>Incompatible return value type (got "str", expected "int")</td></tr>
      <tr><td><code>cfg.temprature</code></td><td>"Config" has no attribute "temprature"</td></tr>
      <tr><td><code>scores: dict[str, float] = {}; scores[1] = 0.5</code></td><td>Invalid index type "int" for "dict[str, float]"</td></tr>
    </table></div>"""),
    p("""Each of these is a bug that would otherwise surface at run time, often only on a rare path (the missing document, the failed request). Type
    checking is **gradual**: unannotated functions are treated leniently, so you can add hints module by module, starting with the code that matters
    most, and tighten settings (mypy's `--strict`) as coverage grows. Third-party libraries ship their own hints (`py.typed`) or have stub
    packages (`pandas-stubs`), and NumPy, pandas, Pydantic and the LLM SDKs are well typed, which makes editors and checkers useful on ML code
    too. This page's in-browser Python cannot run mypy, so the problems here check hints the way libraries do: by reading them at run time."""),
)

section("runtime", "Reading hints at run time",
    p("""Because hints are stored as data, code can read them, and a large part of the modern Python ecosystem does: `dataclasses` builds `__init__` from
    annotated class attributes (11.3); Pydantic validates and converts data according to field types (11.4); FastAPI decides which parameters are path,
    query or body values from their annotations; Typer builds command-line interfaces; agent frameworks generate tool schemas (8.4). The tools are
    `typing.get_type_hints(obj)` for the evaluated hints, and `typing.get_origin` and `typing.get_args` to take generic types apart: `list[int]` has
    origin `list` and arguments `(int,)`; `int | None` has the union type as origin (`typing.Union`, which since Python 3.14 is the same object as
    `types.UnionType`, so either name works in comparisons) and arguments `(int, NoneType)`."""),
    ex("""
    import types, typing

    def search(query: str, k: int = 5, tags: list[str] | None = None, weights: dict[str, float] | None = None) -> list[str]:
        return []

    for name, hint in typing.get_type_hints(search).items():
        origin, args = typing.get_origin(hint), typing.get_args(hint)
        print(f"{name:8} {str(hint):26} origin={getattr(origin, '__name__', origin)} args={args}")
    print(typing.get_origin(int | None) is types.UnionType, type(None) in typing.get_args(int | None))
    """, "runtime_hints.py"),
    p("""Walking hints like this is how a small runtime validator works (problem 7): plain classes are checked with `isinstance`, and generic types are
    checked by recursing into their arguments. Real validators also convert values (the string `"5"` to the int 5) and report every problem at once,
    which is exactly what Pydantic adds."""),
)

section("warmup", "Warm-up",
    predict("Hints are stored, not enforced", "easy",
        code="""
        import typing

        def scale(values: list[float], factor: float = 2.0) -> list[float]:
            return [v * factor for v in values]

        print(scale([1.0, 2.5]), scale("ab", 3))
        print(scale.__annotations__["return"], typing.get_type_hints(scale)["factor"])
        x: int = "not an int"
        print(x, type(x).__name__)
        print(sorted(typing.get_type_hints(scale)))
        """,
        hints=["Python stores annotations and runs the code normally. Multiplying a string by an int repeats it."],
        why="""Calling with a string is not prevented: `"a" * 3` and `"b" * 3` are valid operations, so the function returns a list of repeated strings,
        despite the hint. The annotations are ordinary data, available through `__annotations__` and `get_type_hints`. A variable annotation does not
        check the assigned value either. Only a type checker, before running, would flag both mistakes."""),
    write("Annotate and implement a chunker", "easy", tag="RAG",
        prompt="""Write `split_words(text, max_words=50, overlap=0)` that splits a text into chunks of at most `max_words` words, each chunk starting
        `max_words - overlap` words after the previous one (no chunk for empty text), returned as a list of strings. Annotate it fully: `text` is a
        `str`, the two counts are `int`, and it returns a `list[str]`. Raise `ValueError` unless `0 <= overlap < max_words`.""",
        code="""
        def split_words(text, max_words=50, overlap=0):
            pass
        """,
        tests="""
        import typing
        assert typing.get_type_hints(split_words) == {"text": str, "max_words": int, "overlap": int, "return": list[str]}
        assert split_words("a b c d e", 2) == ["a b", "c d", "e"]
        assert split_words("a b c d e", 3, overlap=1) == ["a b c", "c d e"]
        assert split_words("", 3) == [] and split_words("one", 5) == ["one"]
        try:
            split_words("a b", 2, overlap=2)
            assert False
        except ValueError:
            pass
        """,
        hints=["Step through the word list with `range(0, len(words), step)` and stop once a chunk has reached the end."],
        solution="""
        def split_words(text: str, max_words: int = 50, overlap: int = 0) -> list[str]:
            if not 0 <= overlap < max_words:
                raise ValueError("need 0 <= overlap < max_words")
            words = text.split()
            step = max_words - overlap
            chunks = []
            for start in range(0, len(words), step):
                chunks.append(" ".join(words[start:start + max_words]))
                if start + max_words >= len(words):
                    break
            return chunks
        """,
        why="""The hints state the contract in one line: give me a string and two ints, get back a list of strings. A type checker now flags `split_words(doc)` where
        `doc` might be `None`, or a caller that treats the result as a single string. The `break` stops once a chunk reaches the end, so with overlap
        the last window is not repeated as a smaller duplicate. `get_type_hints` returns real types, so the test (and tools such as tool-schema
        generators) can compare them directly."""),
    fix("A hint that lies about None", "easy", tag="GenAI",
        prompt="""`extract_answer(reply)` returns the text after `"Answer:"`, or nothing if the marker is missing. Its hint promises `-> str`, but one path returns
        `None`, so callers (and the type checker) are misled. Fix the hint to tell the truth, and keep the behaviour.""",
        code="""
        def extract_answer(reply: str) -> str:
            marker = "Answer:"
            if marker not in reply:
                return None
            return reply.split(marker, 1)[1].strip()
        """,
        tests="""
        import typing
        assert extract_answer("Thinking...\\nAnswer: 5 days") == "5 days"
        assert extract_answer("no marker") is None
        assert typing.get_type_hints(extract_answer)["return"] == str | None
        """,
        hints=["A value that can be `None` has the type `str | None`."],
        solution="""
        def extract_answer(reply: str) -> str | None:
            marker = "Answer:"
            if marker not in reply:
                return None
            return reply.split(marker, 1)[1].strip()
        """,
        why="""With `-> str`, a type checker would accept `extract_answer(r).upper()` everywhere, which crashes on replies without the marker. Declaring
        `str | None` makes every caller handle the missing case (`if answer is None: ...`), which is the whole value of the hint. A checker would
        also have flagged the original, since `return None` does not fit `str`. Whether to return `None` or raise is a design decision (7.3); the hint
        must simply describe the decision that was made."""),
    predict("Unions and isinstance", "easy",
        code="""
        import typing

        print(isinstance(5, int | str), isinstance(None, int | None), isinstance(2.5, int | str))
        try:
            isinstance([1, 2], list[int])
        except TypeError as e:
            print("TypeError")
        print(typing.get_args(str | None), typing.get_origin(list[int]) is list)
        print(int | str == str | int, (int | None) | None == int | None)
        """,
        hints=["`isinstance` accepts classes and unions of classes, not parameterised generics like `list[int]`."],
        why="""Since Python 3.10, `isinstance` accepts a union and checks each member, so `None` matches `int | None` (the `None` in a union means `NoneType`).
        A parameterised generic is refused, because `isinstance` checks only the outer type and cannot promise anything about the elements. Unions
        are sets of types: their order does not matter and duplicates collapse."""),
)

section("medium", "Medium",
    write("The first usable text", "medium", tag="GenAI",
        prompt="""Write `first_text(items)` returning the first item that is a non-blank string, stripped, or `None` if there is none. Items may be strings,
        `None`, or other values, and `items` can be any iterable (lists, tuples, generators). Annotate it as accepting an
        `Iterable[object]` and returning `str | None`, with `Iterable` from `collections.abc`.""",
        code="""
        from collections.abc import Iterable

        def first_text(items):
            pass
        """,
        tests="""
        import typing
        from collections.abc import Iterable
        assert first_text([None, "  ", 3, " Refund window ", "later"]) == "Refund window"
        assert first_text(x for x in [None, ""]) is None and first_text(()) is None
        assert first_text(("a",)) == "a"
        assert typing.get_type_hints(first_text) == {"items": Iterable[object], "return": str | None}
        """,
        hints=["Narrow with `isinstance(item, str)` before calling `.strip()`."],
        solution="""
        from collections.abc import Iterable

        def first_text(items: Iterable[object]) -> str | None:
            for item in items:
                if isinstance(item, str) and item.strip():
                    return item.strip()
            return None
        """,
        why="""`Iterable[object]` is the most honest parameter type: the function accepts any iterable of anything, and because the elements are `object`, a type
        checker insists on the `isinstance` check before `.strip()` is called, which is exactly the check that protects the code from `None` and numbers
        at run time. After `isinstance(item, str)`, the checker narrows `item` to `str`. The return type tells callers they must handle `None`. This kind
        of helper is common when cleaning model outputs or optional fields from JSON."""),
    fix("A parameter type that is too narrow", "medium", tag="Data work",
        prompt="""`average_length(texts: list[str])` only loops over its argument, but the hint makes a type checker reject tuples, sets and generators, and
        `keys: dict[str, str]` rejects any read-only mapping. Fix the annotations to the most general types the function needs (from
        `collections.abc`), and keep the return type specific.""",
        code="""
        def average_length(texts: list[str]) -> float:
            texts = list(texts)
            return sum(len(t) for t in texts) / len(texts) if texts else 0.0

        def lookup_all(keys: list[str], table: dict[str, str]) -> list[str]:
            return [table[k] for k in keys if k in table]
        """,
        tests="""
        import typing
        from collections.abc import Iterable, Mapping
        assert typing.get_type_hints(average_length) == {"texts": Iterable[str], "return": float}
        assert typing.get_type_hints(lookup_all) == {"keys": Iterable[str], "table": Mapping[str, str], "return": list[str]}
        assert average_length(t for t in ["ab", "abcd"]) == 3.0 and average_length(()) == 0.0
        from types import MappingProxyType
        assert lookup_all(("a", "z"), MappingProxyType({"a": "x"})) == ["x"]
        """,
        hints=["Looping needs `Iterable[str]`; reading keys and `in` needs `Mapping[str, str]`."],
        solution="""
        from collections.abc import Iterable, Mapping

        def average_length(texts: Iterable[str]) -> float:
            texts = list(texts)
            return sum(len(t) for t in texts) / len(texts) if texts else 0.0

        def lookup_all(keys: Iterable[str], table: Mapping[str, str]) -> list[str]:
            return [table[k] for k in keys if k in table]
        """,
        why="""A parameter hint is a promise about what the function **needs**, and `list[str]` over-promised: it demanded a list when any iterable works, so a
        type checker would reject correct calls with generators or tuples, pushing callers to write pointless `list(...)` conversions. `Mapping` is the
        read-only interface of a dict, so it accepts dicts, `MappingProxyType` views and custom mappings (9.5). The return types stay concrete (`float`,
        `list[str]`) so callers can rely on everything a list offers. "Accept the most general, return the most specific" is the rule."""),
    write("Check a value against a hint", "medium", tag="Data work",
        prompt="""Write `matches(value, hint)` returning whether `value` conforms to the type hint. Support: plain classes (`int`, `str`, ...; `bool` does **not**
        count as `int`, and an `int` counts as a `float`); `None` / `type(None)`; unions `X | Y`; `list[X]`; `dict[K, V]`; `tuple[X, ...]` (any length) and
        `tuple[X, Y]` (fixed length); and `typing.Any` (always true). Raise `TypeError` for other hints.""",
        code="""
        import types, typing

        def matches(value, hint):
            pass
        """,
        tests="""
        import typing
        assert matches(3, int) and not matches(True, int) and matches(2, float) and matches(2.5, float) and not matches("3", int)
        assert matches(None, None) and matches(None, str | None) and matches("a", str | None) and not matches(1, str | None)
        assert matches([1, 2], list[int]) and not matches([1, "2"], list[int]) and matches([], list[str])
        assert matches({"a": [0.5]}, dict[str, list[float]]) and not matches({1: [0.5]}, dict[str, list[float]])
        assert matches((1, 2, 3), tuple[int, ...]) and matches(("a", 1), tuple[str, int]) and not matches(("a",), tuple[str, int])
        assert matches(object(), typing.Any) and matches([None, 1], list[int | None])
        try:
            matches(1, set[int])
            assert False
        except TypeError:
            pass
        """,
        hints=["Start with `typing.Any` and `None`; then `origin = typing.get_origin(hint)` and `args = typing.get_args(hint)`.",
               "For unions, `origin` is `types.UnionType` (or `typing.Union`): check any of the args. Plain classes have no origin."],
        solution="""
        import types, typing

        def matches(value, hint):
            if hint is typing.Any:
                return True
            if hint is None or hint is type(None):
                return value is None
            origin, args = typing.get_origin(hint), typing.get_args(hint)
            if origin in (types.UnionType, typing.Union):
                return any(matches(value, a) for a in args)
            if origin is None:
                if hint is float:
                    return isinstance(value, (int, float)) and not isinstance(value, bool)
                if hint is int:
                    return isinstance(value, int) and not isinstance(value, bool)
                return isinstance(value, hint)
            if origin is list:
                return isinstance(value, list) and all(matches(v, args[0]) for v in value)
            if origin is dict:
                return isinstance(value, dict) and all(matches(k, args[0]) and matches(v, args[1]) for k, v in value.items())
            if origin is tuple:
                if not isinstance(value, tuple):
                    return False
                if len(args) == 2 and args[1] is Ellipsis:
                    return all(matches(v, args[0]) for v in value)
                return len(value) == len(args) and all(matches(v, a) for v, a in zip(value, args))
            raise TypeError(f"unsupported hint: {hint!r}")
        """,
        why="""The function recurses through the structure of the hint, which is what every runtime validator does: plain classes are an `isinstance` check,
        unions succeed if any member matches, and containers check themselves and then each element against the inner type. The special cases
        follow the conventions of type checkers and JSON: `bool` is excluded from `int` (1.2) and `int` is accepted where `float` is expected. Checking
        every element is O(n), which is why `isinstance(x, list[int])` refuses to do it, and why validation belongs at boundaries (API input, model
        output) rather than in every function. Pydantic implements this, much faster, in Rust, plus conversion and error reporting (11.4)."""),
    trace("Taking hints apart", "medium",
        prompt="Fill in `origin` and `args` after each marked line.",
        code="""
        import typing

        def parts(hint):
            o = typing.get_origin(hint)
            return (getattr(o, "__name__", None), tuple(getattr(a, "__name__", str(a)) for a in typing.get_args(hint)))

        origin, args = parts(int)  # row: "int"
        origin, args = parts(list[str])  # row: "list[str]"
        origin, args = parts(dict[str, list[int]])  # row: "nested dict"
        origin, args = parts(int | None)  # row: "int | None"
        origin, args = parts(tuple[float, ...])  # row: "variable tuple"
        """,
        trace_vars=["origin", "args"],
        hints=["Plain classes have no origin and no args. The `...` in `tuple[float, ...]` is the `Ellipsis` object."],
        why="""A plain class is not generic, so both functions return nothing for it. A parameterised container's origin is the container class and its args are
        the parameters, which may themselves be generic: the second argument of the dict hint is `list[int]`, shown here by its `__name__`, which for a
        generic alias is just the name of its origin, `"list"`. A union's origin is the union type, named `Union` in Python 3.14, and `None` appears as
        `NoneType`. The `...` of a variable-length tuple is a real object, `Ellipsis`, passed as the second argument."""),
    write("Validate calls against their hints", "medium", tag="GenAI",
        prompt="""Using the `matches` function provided in the starter, write a decorator `validated` that, on every call, binds the arguments to the function's
        signature (with defaults applied) and raises `TypeError(f"{name} must be {hint}, got {type(value).__name__}")` for the first argument that does
        not match its hint (unannotated parameters are not checked); it also checks the **return value** against the return hint, raising `TypeError`
        mentioning `"return"`. Compute the hints once, at decoration time. Use `functools.wraps`.""",
        code="""
        import functools, inspect, types, typing

        def matches(value, hint):
            if hint is typing.Any:
                return True
            if hint is None or hint is type(None):
                return value is None
            origin, args = typing.get_origin(hint), typing.get_args(hint)
            if origin in (types.UnionType, typing.Union):
                return any(matches(value, a) for a in args)
            if origin is None:
                if hint in (int, float) and isinstance(value, bool):
                    return False
                return isinstance(value, (int, float)) if hint is float else isinstance(value, hint)
            if origin is list:
                return isinstance(value, list) and all(matches(v, args[0]) for v in value)
            if origin is dict:
                return isinstance(value, dict) and all(matches(k, args[0]) and matches(v, args[1]) for k, v in value.items())
            raise TypeError(f"unsupported hint: {hint!r}")

        def validated(func):
            pass
        """,
        tests="""
        @validated
        def search(query: str, k: int = 3, tags: list[str] | None = None) -> list[str]:
            return [f"{query}-{i}" for i in range(k)]

        assert search("refund", 2) == ["refund-0", "refund-1"] and search("x", tags=["eu"]) == ["x-0", "x-1", "x-2"]
        for args, kwargs, word in [(("refund", "2"), {}, "k"), ((42,), {}, "query"), (("x",), {"tags": ["eu", 1]}, "tags")]:
            try:
                search(*args, **kwargs)
                assert False, word
            except TypeError as e:
                assert str(e).startswith(word + " must be")

        @validated
        def broken(n: int) -> str:
            return n * 2
        try:
            broken(2)
            assert False
        except TypeError as e:
            assert "return" in str(e)
        assert search.__name__ == "search"
        """,
        hints=["`hints = typing.get_type_hints(func)`, `ret = hints.pop(\"return\", None)`, `sig = inspect.signature(func)` once in the decorator.",
               "In the wrapper: `bound = sig.bind(*args, **kwargs)`, `bound.apply_defaults()`, check each `name, value` that has a hint."],
        solution="""
        import functools, inspect, types, typing

        def matches(value, hint):
            if hint is typing.Any:
                return True
            if hint is None or hint is type(None):
                return value is None
            origin, args = typing.get_origin(hint), typing.get_args(hint)
            if origin in (types.UnionType, typing.Union):
                return any(matches(value, a) for a in args)
            if origin is None:
                if hint in (int, float) and isinstance(value, bool):
                    return False
                return isinstance(value, (int, float)) if hint is float else isinstance(value, hint)
            if origin is list:
                return isinstance(value, list) and all(matches(v, args[0]) for v in value)
            if origin is dict:
                return isinstance(value, dict) and all(matches(k, args[0]) and matches(v, args[1]) for k, v in value.items())
            raise TypeError(f"unsupported hint: {hint!r}")

        def validated(func):
            hints = typing.get_type_hints(func)
            return_hint = hints.pop("return", inspect.Signature.empty)
            sig = inspect.signature(func)

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                for name, value in bound.arguments.items():
                    hint = hints.get(name)
                    if hint is not None and not matches(value, hint):
                        raise TypeError(f"{name} must be {hint}, got {type(value).__name__}")
                result = func(*args, **kwargs)
                if return_hint is not inspect.Signature.empty and not matches(result, return_hint):
                    raise TypeError(f"return value must be {return_hint}, got {type(result).__name__}")
                return result
            return wrapper
        """,
        why="""This combines three earlier tools: a decorator (8.1), signature binding (8.4) and hint introspection. Binding with defaults applied means
        default values are validated too, and each argument is matched to its parameter however it was passed. Computing the hints and signature
        once keeps each call cheap. Checking the return value catches a function that violates its own contract (`broken` returns an `int` while
        promising `str`). Pydantic's `@validate_call` is the production version: it also **converts** compatible values (`"2"` to `2` when the mode
        allows), and collects all errors in one exception. Use such validation at boundaries, where untrusted data enters; inside the program, a
        static type checker gives the same safety at no run-time cost."""),
    fix("Annotations that lie about the return value", "medium", tag="ML",
        prompt="""A team decorates every public function with the provided `@check_return`, which raises if a result does not match the return hint.
        `label_counts` now fails, because its hint does not describe what it returns (a dict from label to count, not a list). Fix the **hint**, not
        the code.""",
        code="""
        import functools, typing
        from collections import Counter

        def check_return(func):
            hint = typing.get_type_hints(func)["return"]
            origin, args = typing.get_origin(hint), typing.get_args(hint)

            @functools.wraps(func)
            def wrapper(*args_, **kwargs):
                result = func(*args_, **kwargs)
                ok = isinstance(result, origin or hint)
                if ok and origin is dict:
                    ok = all(isinstance(k, args[0]) and isinstance(v, args[1]) for k, v in result.items())
                if not ok:
                    raise TypeError(f"{func.__name__} returned {type(result).__name__}, expected {hint}")
                return result
            return wrapper

        @check_return
        def label_counts(labels: list[str]) -> list[tuple[str, int]]:
            return dict(Counter(labels))
        """,
        tests="""
        import typing
        assert label_counts(["spam", "ham", "spam"]) == {"spam": 2, "ham": 1}
        assert label_counts([]) == {}
        assert typing.get_type_hints(label_counts.__wrapped__)["return"] == dict[str, int]
        """,
        hints=["The function returns a `dict` whose keys are labels and values are counts."],
        solution="""
        import functools, typing
        from collections import Counter

        def check_return(func):
            hint = typing.get_type_hints(func)["return"]
            origin, args = typing.get_origin(hint), typing.get_args(hint)

            @functools.wraps(func)
            def wrapper(*args_, **kwargs):
                result = func(*args_, **kwargs)
                ok = isinstance(result, origin or hint)
                if ok and origin is dict:
                    ok = all(isinstance(k, args[0]) and isinstance(v, args[1]) for k, v in result.items())
                if not ok:
                    raise TypeError(f"{func.__name__} returned {type(result).__name__}, expected {hint}")
                return result
            return wrapper

        @check_return
        def label_counts(labels: list[str]) -> dict[str, int]:
            return dict(Counter(labels))
        """,
        why="""The hint promised a list of pairs (the shape of `Counter.most_common()`), but the function returns a dict. Without the decorator nothing would fail at
        run time, and every caller writing `for label, n in label_counts(x)` would get keys only, while a type checker, believing the hint, would
        approve it. Hints are only useful if they are true, which is why tools that **read** them (this decorator, Pydantic, FastAPI) are valuable:
        they turn a wrong hint into an immediate error. `__wrapped__` (8.1) lets the test read the original function's hints."""),
    predict("Any, object and default None", "medium",
        code="""
        import typing

        def a(x: typing.Any) -> None: ...
        def b(x: object = None) -> None: ...
        def c(x: int = None) -> int | None:
            return x

        print(typing.get_type_hints(a), typing.get_type_hints(b)["x"])
        print(typing.get_type_hints(c))
        print(c(), c(5), a.__annotations__["return"])
        """,
        hints=["`get_type_hints` returns the annotations as written; it does not add `| None` for a default of `None`."],
        why="""`Any` and `object` are both stored as written. `-> None` appears as `NoneType` in `get_type_hints` (and as `None` in the raw annotations). A
        parameter annotated `int` with a default of `None` keeps the hint `int`: older type checkers used to infer `int | None` implicitly, but mypy and
        pyright no longer do and report the default as an error, so write `x: int | None = None` explicitly. The function itself runs either way."""),
)

section("hard", "Hard",
    write("Convert strings to hinted types", "hard", tag="GenAI",
        prompt="""Settings arrive as strings (environment variables, query parameters, CSV cells). Write `coerce(raw, hint)` converting a string to the hinted type:
        `str` (unchanged), `int`, `float`, `bool` (`true/false/yes/no/1/0`, any case), `list[X]` (comma-separated, items stripped, empty string gives
        `[]`), and `X | None` (an empty or blank string, or `"none"`/`"null"` in any case, gives `None`; otherwise convert to `X`). Raise `ValueError` naming
        the hint for strings that cannot be converted, and `TypeError` for unsupported hints. Then write `load_settings(cls_hints, env)` that converts
        every key of the dict `cls_hints` (name to hint) present in `env`, and returns a dict.""",
        code="""
        import types, typing

        def coerce(raw, hint):
            pass

        def load_settings(cls_hints, env):
            pass
        """,
        tests="""
        assert coerce("42", int) == 42 and coerce(" 0.5 ", float) == 0.5 and coerce("Yes", bool) is True and coerce("0", bool) is False
        assert coerce("a, b ,c", list[str]) == ["a", "b", "c"] and coerce("1,2", list[int]) == [1, 2] and coerce("", list[int]) == []
        assert coerce("", int | None) is None and coerce("NULL", float | None) is None and coerce("7", int | None) == 7
        for raw, hint in [("x", int), ("maybe", bool), ("1,a", list[int])]:
            try:
                coerce(raw, hint)
                assert False, (raw, hint)
            except ValueError as e:
                assert str(hint) in str(e)
        try:
            coerce("a", dict[str, str])
            assert False
        except TypeError:
            pass
        hints = {"model": str, "temperature": float, "max_tokens": int, "stream": bool, "stop": list[str], "seed": int | None}
        env = {"model": "large", "temperature": "0.2", "stream": "no", "stop": "User:,###", "seed": "", "extra": "ignored"}
        assert load_settings(hints, env) == {"model": "large", "temperature": 0.2, "stream": False, "stop": ["User:", "###"], "seed": None}
        """,
        hints=["Handle unions first: if `None` is among the args, blank/none/null gives `None`; otherwise coerce to the other member.",
               "Wrap the `int`/`float` conversions in `try` and re-raise `ValueError(f\"cannot convert {raw!r} to {hint}\")`."],
        solution="""
        import types, typing

        TRUE, FALSE = {"true", "yes", "1"}, {"false", "no", "0"}

        def coerce(raw, hint):
            origin, args = typing.get_origin(hint), typing.get_args(hint)
            if origin in (types.UnionType, typing.Union):
                if type(None) in args and raw.strip().lower() in ("", "none", "null"):
                    return None
                others = [a for a in args if a is not type(None)]
                if len(others) != 1:
                    raise TypeError(f"unsupported union: {hint!r}")
                return coerce(raw, others[0])
            if origin is list:
                items = [part.strip() for part in raw.split(",")] if raw.strip() else []
                try:
                    return [coerce(item, args[0]) for item in items]
                except ValueError:
                    raise ValueError(f"cannot convert {raw!r} to {hint}") from None
            if hint is str:
                return raw
            if hint is bool:
                text = raw.strip().lower()
                if text in TRUE:
                    return True
                if text in FALSE:
                    return False
                raise ValueError(f"cannot convert {raw!r} to {hint}")
            if hint in (int, float):
                try:
                    return hint(raw.strip())
                except ValueError:
                    raise ValueError(f"cannot convert {raw!r} to {hint}") from None
            raise TypeError(f"unsupported hint: {hint!r}")

        def load_settings(cls_hints, env):
            return {name: coerce(env[name], hint) for name, hint in cls_hints.items() if name in env}
        """,
        why="""Strings are what the outside world gives you, and hints say what the program needs, so a converter driven by hints is the bridge: one table of
        field types replaces a hand-written parse per setting. Unions with `None` are resolved first, so an empty variable can mean "not set"; lists
        convert each item with the element type, recursively. `bool` needs an explicit vocabulary because `bool("false")` is `True` (8.P). Errors
        name both the bad value and the expected type, which is what a person fixing a configuration needs. Pydantic's settings models and Typer's CLI
        parsing implement this same conversion, driven by class annotations (11.4)."""),
    fix("Read the code: a schema generator that ignores Optional", "hard", tag="GenAI",
        prompt="""This generates JSON schemas for agent tools from type hints (8.4). Parameters annotated `X | None` crash it with `KeyError`, and parameters with
        defaults are wrongly marked as required. A parameter `p: X | None = None` should produce `{"type": [<X's type>, "null"]}` and not be required;
        any parameter with a default is not required. Read it, find the bugs and fix them.""",
        code="""
        import inspect, types, typing

        JSON = {str: "string", int: "integer", float: "number", bool: "boolean"}


        def tool_schema(func):
            hints = typing.get_type_hints(func)
            props, required = {}, []
            for name, param in inspect.signature(func).parameters.items():
                hint = hints[name]
                if typing.get_origin(hint) is list:
                    props[name] = {"type": "array", "items": {"type": JSON[typing.get_args(hint)[0]]}}
                else:
                    props[name] = {"type": JSON[hint]}
                required.append(name)
            return {"name": func.__name__, "parameters": {"type": "object", "properties": props, "required": required}}
        """,
        tests="""
        def search(query: str, k: int = 5, lang: str | None = None, tags: list[str] | None = None) -> list[str]:
            return []

        s = tool_schema(search)["parameters"]
        assert s["required"] == ["query"]
        assert s["properties"] == {
            "query": {"type": "string"}, "k": {"type": "integer"},
            "lang": {"type": ["string", "null"]},
            "tags": {"type": ["array", "null"], "items": {"type": "string"}},
        }
        def strict(flag: bool, ids: list[int]):
            return None
        assert tool_schema(strict)["parameters"]["required"] == ["flag", "ids"]
        """,
        hints=["Unwrap `X | None` first: if the hint is a union containing `NoneType`, build the schema for `X`, then make its `\"type\"` a list `[t, \"null\"]`.",
               "Required means `param.default is inspect.Parameter.empty`."],
        solution="""
        import inspect, types, typing

        JSON = {str: "string", int: "integer", float: "number", bool: "boolean"}


        def _schema(hint):
            if typing.get_origin(hint) is list:
                return {"type": "array", "items": _schema(typing.get_args(hint)[0])}
            return {"type": JSON[hint]}


        def tool_schema(func):
            hints = typing.get_type_hints(func)
            props, required = {}, []
            for name, param in inspect.signature(func).parameters.items():
                hint = hints[name]
                nullable = False
                if typing.get_origin(hint) in (types.UnionType, typing.Union):
                    members = [a for a in typing.get_args(hint) if a is not type(None)]
                    nullable = len(members) < len(typing.get_args(hint))
                    if len(members) != 1:
                        raise TypeError(f"{name}: only X | None unions are supported")
                    hint = members[0]
                schema = _schema(hint)
                if nullable:
                    schema["type"] = [schema["type"], "null"]
                props[name] = schema
                if param.default is inspect.Parameter.empty:
                    required.append(name)
            return {"name": func.__name__, "parameters": {"type": "object", "properties": props, "required": required}}
        """,
        why="""Two bugs. A union such as `str | None` is not a key of the `JSON` dict, so the lookup raised `KeyError`; unions must be unwrapped first, keeping the
        non-`None` member for the schema and recording that `null` is allowed, which JSON Schema expresses as a list of types. And every parameter
        was appended to `required`, so the model was told it must always send `k`, `lang` and `tags`, even though they have defaults; required means
        "no default". Both mistakes change how an LLM calls the tool: missing nullability makes it invent values, wrong required lists make it fill
        parameters it should omit. Moving the per-type logic into `_schema` makes nested lists work too. Unsupported unions raise a clear error
        instead of producing a wrong schema."""),
    write("A readable signature from hints", "hard", tag="Data work",
        prompt="""Write `describe(func)` returning a one-line description such as `search(query: str, k: int = 5, tags: list[str] | None = None) -> list[str]`, using
        `inspect.signature` and `typing.get_type_hints`. Format types as written in modern syntax: plain classes by `__name__`, generics as
        `name[args]`, unions with `|`, `None` for `NoneType`, `...` for `Ellipsis`. Defaults use `repr`, with spaces around `=` only for
        annotated parameters, as PEP 8 recommends (`k: int = 5` but `y='z'`). Unannotated parameters show only the name;
        `*args` and `**kwargs` keep their stars. Omit the arrow when there is no return hint.""",
        code="""
        import inspect, types, typing

        def describe(func):
            pass
        """,
        tests="""
        def search(query: str, k: int = 5, tags: list[str] | None = None, *, weights: dict[str, float] | None = None) -> list[str]:
            return []
        assert describe(search) == "search(query: str, k: int = 5, tags: list[str] | None = None, weights: dict[str, float] | None = None) -> list[str]"

        def misc(a, b: tuple[int, ...] = (1,), *args: str, **kwargs: int) -> None:
            pass
        assert describe(misc) == "misc(a, b: tuple[int, ...] = (1,), *args: str, **kwargs: int) -> None"

        def plain(x, y="z"):
            pass
        assert describe(plain) == "plain(x, y='z')"
        """,
        hints=["A recursive `fmt(hint)`: `None`/`NoneType` gives `\"None\"`, `Ellipsis` gives `\"...\"`, unions join members with `\" | \"`, generics are `f\"{origin.__name__}[{', '.join(...)}]\"`.",
               "The keyword-only marker `*` is not part of the expected output; just list the parameters."],
        solution="""
        import inspect, types, typing

        def fmt(hint):
            if hint is None or hint is type(None):
                return "None"
            if hint is Ellipsis:
                return "..."
            origin, args = typing.get_origin(hint), typing.get_args(hint)
            if origin in (types.UnionType, typing.Union):
                return " | ".join(fmt(a) for a in args)
            if origin is not None:
                return f"{origin.__name__}[{', '.join(fmt(a) for a in args)}]"
            return getattr(hint, "__name__", repr(hint))

        def describe(func):
            hints = typing.get_type_hints(func)
            parts = []
            for name, p in inspect.signature(func).parameters.items():
                prefix = {p.VAR_POSITIONAL: "*", p.VAR_KEYWORD: "**"}.get(p.kind, "")
                text = prefix + name
                if name in hints:
                    text += f": {fmt(hints[name])}"
                if p.default is not p.empty:
                    text += (" = " if name in hints else "=") + repr(p.default)
                parts.append(text)
            result = f"{func.__name__}({', '.join(parts)})"
            if "return" in hints:
                result += f" -> {fmt(hints['return'])}"
            return result
        """,
        why="""The formatter mirrors how hints are built: a union is a set of members, a generic is an origin with arguments, and both recurse, so `dict[str,
        float] | None` comes out exactly as written. `NoneType` and `Ellipsis` need special cases because they are values standing in for types.
        Walking the signature gives parameter kinds and defaults, and the hints give the types; the two are separate because a parameter can have a
        default without an annotation and vice versa. Documentation generators, CLI help (Typer, Click) and tool descriptions for LLMs are all built
        from exactly these two sources."""),
    predict("Lazy annotations in Python 3.14", "hard",
        code="""
        import annotationlib

        def ingest(doc: Document, store: "VectorStore | None" = None) -> Report:
            return None

        print("defined without NameError")
        try:
            ingest.__annotations__
        except NameError as e:
            print("NameError:", e)
        strings = annotationlib.get_annotations(ingest, format=annotationlib.Format.STRING)
        print(strings)

        class Document: pass
        class Report: pass
        print(sorted(ingest.__annotations__), ingest.__annotations__["doc"].__name__)
        """,
        hints=["Python 3.14 evaluates annotations only when they are requested (PEP 649), so names used in hints may be defined later."],
        why="""Defining the function does not evaluate its annotations, so using `Document` before the class exists is fine. Asking for `__annotations__` evaluates
        them, and fails while `Document` is still undefined. `annotationlib.get_annotations` with the `STRING` format returns the annotations as source
        text without evaluating anything, which is what documentation tools use. Once the classes exist, evaluating succeeds. The quoted
        `"VectorStore | None"` stays a string even when evaluated, since a string annotation is just a string value: quoting forward references was the
        old workaround, and with lazy annotations it is no longer needed."""),
)

section("interview", "Interview questions",
    explain("Are type hints enforced in Python? Then what are they for?", "medium", tag="Interview",
        why="""No: the interpreter stores annotations (in `__annotations__`) and otherwise ignores them, so passing a wrong type runs exactly as it would without
        hints. They are for three things. Documentation that cannot drift as easily as comments, because tools read it. Static analysis: type
        checkers such as mypy and pyright analyse the code without running it and catch mismatched arguments, wrong return types, missing attributes
        and unhandled `None` values before production, and editors use the same information for completion and refactoring. And runtime use by
        libraries that read the hints on purpose: dataclasses generate methods from them, Pydantic validates and converts data, FastAPI and Typer build
        APIs and CLIs, agent frameworks build tool schemas. A good practice is static checking inside the program and explicit validation at its
        boundaries, where untrusted data enters."""),
    explain("What does `str | None` (or `Optional[str]`) mean, and how should code handle it?", "medium", tag="Interview",
        why="""It means the value is either a string or `None`; `Optional` does not mean the parameter is optional (that is a default value), it means "may be
        None". A function returning `str | None` tells every caller that a missing result is a normal outcome they must handle. Code handles it by
        **narrowing**: checking `if value is None:` (and returning, raising or using a fallback) before using it as a string, after which the type
        checker treats it as `str`; `isinstance` checks narrow the same way. A parameter that defaults to `None` should be annotated `X | None = None`
        explicitly. Unhandled `None` is the most common bug type checkers catch, because in production it shows up as `AttributeError: 'NoneType'
        object has no attribute ...` on the rare path where a lookup failed."""),
    explain("How would you introduce type checking into an existing ML codebase?", "hard", tag="Interview",
        why="""Gradually. Add a type checker (mypy or pyright) to the editor and CI in a lenient mode first, so unannotated code is not flagged, and fix the
        errors it already finds in annotated code. Then annotate the boundaries that matter most: public functions of shared modules, data loading and
        feature pipelines, configuration, and the code that calls model APIs, using precise types for inputs (`Iterable[str]`, `Mapping[str, float]`),
        `X | None` where values can be missing, dataclasses or Pydantic models instead of loose dicts for structured records, and protocols for
        pluggable components. Enable stricter settings per module as coverage grows (mypy's per-module `strict`), and install stub packages such as
        `pandas-stubs`; for array shapes and dtypes, which types capture poorly, keep runtime assertions. Avoid `Any` except at real boundaries, and
        validate external data (API payloads, model output, files) at run time with Pydantic, since static types cannot check data that arrives while the
        program runs. Measure progress by the share of typed modules and the number of production bugs caught earlier."""),
)

recap(
    "Type hints (`x: int`, `-> list[str]`) document types for people, editors and type checkers; Python does not enforce them.",
    "Use built-in generics (`list[str]`, `dict[str, float]`, `tuple[int, ...]`) and aliases for long types; annotate `-> None` for functions returning nothing.",
    "`X | None` means \"may be None\"; handle it by narrowing (`if x is None:`, `isinstance`) before use. Keep hints truthful.",
    "Accept the most general types (`Iterable`, `Sequence`, `Mapping`), return specific ones; `Any` disables checking, `object` forces narrowing.",
    "Libraries read hints at run time with `typing.get_type_hints`, `get_origin` and `get_args`: dataclasses, Pydantic, FastAPI and tool schemas.",
)
