from lesson import *

lesson(
    id="m7-2", num="7.2", title="Raising and custom exceptions",
    intro="How to raise well: choosing the type, writing messages people can act on, and re-raising without losing the "
          "original. Defining your own exception classes and hierarchies, chaining with `raise ... from`, adding notes, "
          "exception groups for several errors at once, and why `assert` is not validation. Applied to LLM client errors, "
          "configuration and data validation.",
    desc="Raising well, custom exception classes, `raise ... from`, notes and exception groups.",
    keys="raise reraise custom exception class hierarchy subclass message raise from cause context suppress add_note notes exceptiongroup except star assert validation valueerror typeerror notimplementederror",
)

term("Custom exception", "An exception class you define, such as `class RateLimitError(Exception): pass`, so callers can catch your specific error.")
term("Exception chaining", "Linking a new exception to the one that caused it with `raise NewError(...) from original`, so both appear in the traceback.")
term("Exception group", "An `ExceptionGroup` bundles several exceptions raised together; `except*` handles the ones of a given type.")

section("raise", "Raising: the type, the message, and re-raising",
    p("""`raise SomeError("message")` creates an exception object and raises it. You can also write `raise SomeError` without
    parentheses; Python then creates the instance for you with no arguments. The two decisions that matter are **which type**
    and **what message**, because those are what the caller and the person reading the log will act on."""),
    html("""<div class="tbl"><table>
      <tr><th>Raise</th><th>When</th><th>Example</th></tr>
      <tr><td><code>TypeError</code></td><td>the argument has the wrong type</td><td>a list where a string is required</td></tr>
      <tr><td><code>ValueError</code></td><td>right type, unacceptable value</td><td><code>temperature=5</code> when the range is 0 to 2</td></tr>
      <tr><td><code>KeyError</code> / <code>LookupError</code></td><td>a lookup by key or name found nothing</td><td>an unknown model name in a registry</td></tr>
      <tr><td><code>NotImplementedError</code></td><td>a method that a subclass must provide</td><td>a base provider class's <code>complete()</code></td></tr>
      <tr><td><code>RuntimeError</code></td><td>the operation is not possible in the current state</td><td>calling <code>send()</code> on a closed client</td></tr>
      <tr><td>your own class</td><td>an error callers will want to catch specifically</td><td><code>RateLimitError</code>, <code>InvalidOutputError</code></td></tr>
    </table></div>"""),
    p("""A good message answers three questions: **what** was wrong, **which value** caused it, and **what was expected**.
    `ValueError("bad value")` forces the reader to debug; `ValueError("temperature must be between 0 and 2, got 5.0")` tells them
    exactly what to change. Include the offending value with `!r` so strings show their quotes and invisible whitespace, and never
    include secrets (API keys, passwords, personal data) in messages, because messages end up in logs."""),
    ex("""
    def set_temperature(t):
        if isinstance(t, bool) or not isinstance(t, (int, float)):
            raise TypeError(f"temperature must be a number, got {type(t).__name__}")
        if not 0 <= t <= 2:
            raise ValueError(f"temperature must be between 0 and 2, got {t!r}")
        return float(t)

    for value in [0.7, 5, "0.7", True]:
        try:
            print(set_temperature(value))
        except (TypeError, ValueError) as e:
            print(f"{type(e).__name__}: {e}")
    """, "raise_well.py"),
    p("""`bool` is checked first because `True` is an instance of `int` (1.2) and would otherwise be accepted as `1.0`. Inside an
    `except` block, a bare **`raise`** (no argument) re-raises the exception being handled, **unchanged**: same type, same
    message, same traceback. Use it when you only want to do something on the way out, such as log, count or clean up, and
    then let the error continue. Writing `raise e` also works, but adds the current line to the traceback; `raise
    Exception(str(e))` is worse, because it replaces the type, so callers can no longer catch the specific error (problem 3)."""),
    ex("""
    failures = []

    def parse(text):
        try:
            return int(text)
        except ValueError:
            failures.append(text)        # record it...
            raise                        # ...and let the same exception continue

    try:
        parse("4x")
    except ValueError as e:
        print(type(e).__name__, "|", e, "|", failures)
    """, "bare_raise.py"),
)

section("custom", "Defining your own exceptions",
    p("""Built-in types describe **what kind** of problem happened; your own types describe **which** problem, in your domain's
    terms. That matters to callers: code that calls an LLM client wants to retry a rate limit, show a message for a bad request
    and alert someone for an authentication failure, and it can only tell them apart if they are different types. Defining one
    takes a single line, using the `class` statement, which Module 9 covers in full:"""),
    ex("""
    class LLMError(Exception):
        \"\"\"Base class for every error raised by our LLM client.\"\"\"

    class RateLimitError(LLMError):
        pass

    class InvalidOutputError(LLMError):
        pass

    print(RateLimitError.__mro__[1].__name__, issubclass(RateLimitError, Exception))
    try:
        raise RateLimitError("429: slow down")
    except LLMError as e:                  # the base class catches every subclass
        print(type(e).__name__, "|", e)
    """, "custom_basic.py"),
    p("""`class RateLimitError(LLMError):` creates a new type that **inherits** from `LLMError`, which inherits from `Exception`. The
    body can be just `pass` or a docstring: everything an exception needs (storing the message, printing it) is inherited. Because
    of the hierarchy, `except RateLimitError` catches only rate limits, while `except LLMError` catches every error from your
    client, and nothing from elsewhere. The usual design is **one base class per library or component**, with a few subclasses for
    the cases callers handle differently. Inherit from `Exception` (never `BaseException`), and name classes with an `Error`
    suffix."""),
    p("""Exceptions can carry **data** as well as a message, which makes them much more useful to handlers: a rate limit can say how
    long to wait, an invalid output can carry the raw text. Add an `__init__` method that stores the extra values as attributes and
    passes the message on to the parent class with `super().__init__(message)` (Module 9 explains `__init__` and `super` in
    depth; here the pattern is all you need)."""),
    ex("""
    class LLMError(Exception):
        pass

    class RateLimitError(LLMError):
        def __init__(self, message, retry_after):
            super().__init__(message)          # the message works as usual
            self.retry_after = retry_after     # extra data for handlers

    class InvalidOutputError(LLMError):
        def __init__(self, message, raw):
            super().__init__(message)
            self.raw = raw

    try:
        raise RateLimitError("rate limited by provider", retry_after=2.5)
    except RateLimitError as e:
        print(e, "| wait", e.retry_after, "s |", e.args)

    err = InvalidOutputError("reply is not JSON", raw="Sure! {label: spam}")
    print(repr(err), "|", err.raw)
    """, "custom_data.py"),
    callout("sql", "SQL / Power BI", """Database drivers work exactly this way. `psycopg` raises `UniqueViolation`, a subclass of
    `IntegrityError`, a subclass of its base `Error`, and each carries the SQLSTATE code and details. Code catches
    `UniqueViolation` to handle a duplicate insert, and the base class to log anything else from the database. Your own hierarchy
    gives your callers the same choice."""),
)

section("chain", "Chaining: `raise ... from`",
    p("""Often the right response to a low-level error is to raise a **higher-level** one that means something to your caller: a
    `JSONDecodeError` while reading the settings file becomes a `ConfigError("settings.json is not valid JSON")`. The danger is
    losing the original, which holds the precise detail (line, column, the bad character). Python has three behaviours for an
    exception raised while handling another:"""),
    p("""- **Implicit chaining:** a plain `raise NewError(...)` inside `except` stores the original in `new.__context__`. The
    traceback shows both, separated by "During handling of the above exception, another exception occurred", which reads like
    a second bug happened in the handler.
    - **Explicit chaining:** `raise NewError(...) from original` stores it in `new.__cause__`. The traceback shows both with
      "The above exception was the direct cause of the following exception": this one is deliberate translation. Use it whenever
      you convert an error.
    - **Suppressed:** `raise NewError(...) from None` hides the original from the traceback. Use it only when the original is
      noise, for example a `KeyError` from an internal lookup that you replace with a clear "unknown model" message."""),
    ex("""
    import json, traceback

    class ConfigError(Exception):
        pass

    def load(text, style):
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            if style == "implicit":
                raise ConfigError("settings are not valid JSON")
            if style == "from":
                raise ConfigError("settings are not valid JSON") from e
            raise ConfigError("settings are not valid JSON") from None

    for style in ["implicit", "from", "none"]:
        try:
            load("{bad", style)
        except ConfigError as err:
            text = traceback.format_exc()
            print(style, type(err.__cause__).__name__, type(err.__context__).__name__, err.__suppress_context__,
                  "direct cause" in text, "During handling" in text)
    """, "chaining.py"),
    p("""Read the output column by column: with `from e`, `__cause__` is set and the traceback says "direct cause"; implicit
    chaining sets only `__context__`; `from None` sets `__suppress_context__`, so the original is still stored in
    `__context__` (for debuggers) but not printed. Handlers can use `err.__cause__` to get at the original details (problem 6)."""),
)

section("notes", "Adding context with notes",
    p("""Sometimes you do not want a new type at all, only more **context**: the error is a perfectly good `ValueError`, but the log
    should also say which file and which line was being processed. Since Python 3.11, any exception has an `add_note(text)` method.
    Notes are stored in `e.__notes__` and printed under the message in the traceback. The pattern is: catch, add a note, re-raise
    with a bare `raise`, so the type and traceback stay exactly as they were."""),
    ex("""
    import traceback

    def parse_line(line):
        name, score = line.split(",")
        return name, float(score)

    def parse_file(lines, filename):
        out = []
        for n, line in enumerate(lines, start=1):
            try:
                out.append(parse_line(line))
            except ValueError as e:
                e.add_note(f"in {filename}, line {n}: {line!r}")
                raise
        return out

    try:
        parse_file(["ana,0.9", "bo,high"], "scores.csv")
    except ValueError as e:
        print(type(e).__name__, "|", e, "|", e.__notes__)
        print(traceback.format_exc().strip().splitlines()[-1])
    """, "notes.py"),
    p("""The caller still catches a `ValueError`, nothing about the error's type changed, but whoever reads the traceback sees the
    file and line immediately. Notes are ideal in loops and pipelines, where the low-level code that fails does not know where its
    input came from, and the code that knows does not want to change the exception type."""),
)

section("groups", "Several errors at once: exception groups",
    p("""Normally one exception stops everything. Two situations need to report **several** at once: concurrent tasks that fail
    independently (Module 14's `asyncio.TaskGroup` raises them together), and validation, where telling the user about all five
    problems in their request is better than revealing them one at a time. Python 3.11 added **`ExceptionGroup(message,
    [exceptions])`** for this, and the **`except*`** clause to handle it: each `except* SomeType` clause receives a group containing
    only the exceptions of that type, and the others continue to the next clause."""),
    ex("""
    def validate(request):
        errors = []
        if not request.get("prompt"):
            errors.append(ValueError("prompt is required"))
        if not 0 <= request.get("temperature", 0) <= 2:
            errors.append(ValueError("temperature must be between 0 and 2"))
        if not isinstance(request.get("max_tokens", 1), int):
            errors.append(TypeError("max_tokens must be an int"))
        if errors:
            raise ExceptionGroup("invalid request", errors)

    try:
        validate({"prompt": "", "temperature": 3, "max_tokens": "512"})
    except* ValueError as group:
        print("values:", [str(e) for e in group.exceptions])
    except* TypeError as group:
        print("types:", [str(e) for e in group.exceptions])
    """, "exception_groups.py"),
    p("""Both handlers ran, each with its own part of the group, which a normal `except` cannot do. A plain `except ExceptionGroup as
    eg:` also works and gives you the whole group in `eg.exceptions`. Libraries such as Pydantic collect all validation errors in a
    similar spirit, in their own `ValidationError` type (11.4). Use groups when callers genuinely benefit from several errors; for a
    single failure, raise a single exception."""),
)

section("assert", "`assert` is not validation",
    p("""`assert condition, "message"` raises `AssertionError` when the condition is false. It is meant for **internal invariants**:
    things that can only be false if **your own code** has a bug, such as "this list is sorted here" or "the shapes match after my
    reshape". It is not a way to check **input**, for two reasons. Python removes every `assert` when it runs with the `-O`
    (optimise) flag, which some deployments use, so the check silently disappears. And `AssertionError` tells the caller nothing
    about what kind of problem it was; a `ValueError` or `TypeError` says "your argument is wrong", which is what input validation
    means (problem 9)."""),
    ex("""
    import numpy as np

    def cosine(a, b):
        a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
        if a.shape != b.shape:                       # input validation: raise
            raise ValueError(f"shapes differ: {a.shape} vs {b.shape}")
        norm = np.linalg.norm(a) * np.linalg.norm(b)
        if norm == 0:
            raise ValueError("cosine is undefined for a zero vector")
        result = float(a @ b / norm)
        assert -1.0001 <= result <= 1.0001, result   # invariant: can only fail if the maths above is wrong
        return round(result, 4)

    print(cosine([1, 0], [1, 1]))
    try:
        cosine([1, 2, 3], [1, 2])
    except ValueError as e:
        print("ValueError:", e)
    """, "assert_vs_raise.py"),
)

section("warmup", "Warm-up",
    predict("Raising and re-raising", "easy",
        code="""
        try:
            raise ValueError
        except ValueError as e:
            print(repr(e), e.args)

        def inner():
            raise KeyError("model")

        def outer():
            try:
                inner()
            except KeyError as e:
                print("logging", e)
                raise

        try:
            outer()
        except KeyError as e:
            print("caller got", type(e).__name__, e.args)
        print(str(ValueError("bad", 42)))
        """,
        hints=["`raise ValueError` creates an instance with no arguments. A bare `raise` re-raises the same exception object."],
        why="""Raising the class creates an instance with empty `args`. `outer` logs and re-raises the **same** `KeyError`, so the caller
        receives it unchanged, with the original `args`. An exception created with several arguments prints them as a tuple,
        which is why messages should be one formatted string."""),
    write("Validate generation settings", "easy", tag="GenAI",
        prompt="""Write `check_settings(temperature, max_tokens)` that returns `(float(temperature), max_tokens)` when valid, and
        raises: `TypeError` if `temperature` is not an `int` or `float` (booleans are not numbers here) or `max_tokens` is not an
        `int` (booleans neither); `ValueError` if `temperature` is outside 0 to 2 or `max_tokens` is not positive. Messages must name
        the setting and show the bad value with `repr`.""",
        code="""
        def check_settings(temperature, max_tokens):
            pass
        """,
        tests="""
        assert check_settings(0.7, 256) == (0.7, 256) and check_settings(0, 1) == (0.0, 1)
        cases = [(("0.7", 256), TypeError, "'0.7'"), ((True, 256), TypeError, "True"), ((3, 256), ValueError, "3"),
                 ((0.5, 0), ValueError, "0"), ((0.5, 2.5), TypeError, "2.5"), ((0.5, False), TypeError, "False")]
        for args, kind, shown in cases:
            try:
                check_settings(*args)
                assert False, args
            except kind as e:
                assert shown in str(e) and ("temperature" in str(e) or "max_tokens" in str(e)), str(e)
        assert check_settings(2, 10_000) == (2.0, 10_000)
        """,
        hints=["Test `isinstance(x, bool)` first: `True` is an `int`.", "Raise `TypeError` for wrong types before checking ranges, so `\"0.7\" < 0` is never evaluated."],
        solution="""
        def check_settings(temperature, max_tokens):
            if isinstance(temperature, bool) or not isinstance(temperature, (int, float)):
                raise TypeError(f"temperature must be a number, got {temperature!r}")
            if isinstance(max_tokens, bool) or not isinstance(max_tokens, int):
                raise TypeError(f"max_tokens must be an int, got {max_tokens!r}")
            if not 0 <= temperature <= 2:
                raise ValueError(f"temperature must be between 0 and 2, got {temperature!r}")
            if max_tokens <= 0:
                raise ValueError(f"max_tokens must be positive, got {max_tokens!r}")
            return float(temperature), max_tokens
        """,
        why="""Type checks come first because comparing a string with a number would raise its own, less helpful, `TypeError`. The split
        between the two exception types follows their meaning: a string or a boolean is the wrong **kind** of value (`TypeError`), 3
        is the right kind with an unacceptable **value** (`ValueError`). Each message names the setting and shows the value with
        `repr`, so `'0.7'` (a string) is distinguishable from `0.7`. This is what API servers do when they return a 400 response with
        a message per field; Pydantic (11.4) generates such checks from type annotations."""),
    fix("A re-raise that loses the error type", "easy", tag="Data work",
        prompt="""`load_number(text)` logs failures and re-raises them. Callers catch `ValueError` for bad input, but they receive a
        plain `Exception` and crash. Fix the re-raise so callers get the original exception.""",
        code="""
        log = []

        def load_number(text):
            try:
                return float(text)
            except (ValueError, TypeError) as e:
                log.append(f"failed on {text!r}")
                raise Exception(str(e))
        """,
        tests="""
        assert load_number("2.5") == 2.5
        try:
            load_number("abc")
            assert False
        except ValueError as e:
            assert "abc" in str(e)
        try:
            load_number(None)
            assert False
        except TypeError:
            pass
        assert log == ["failed on 'abc'", "failed on None"]
        """,
        hints=["A bare `raise` inside `except` re-raises the exception being handled, with its type and traceback."],
        solution="""
        log = []

        def load_number(text):
            try:
                return float(text)
            except (ValueError, TypeError):
                log.append(f"failed on {text!r}")
                raise
        """,
        why="""`raise Exception(str(e))` threw away the exception's **type**, so `except ValueError` in the caller no longer matched,
        and the traceback now starts at the re-raise instead of at `float`. A bare `raise` re-raises the original object unchanged.
        The rule: when you only want to observe an exception (log it, count it), re-raise it as it is; when you want to change its
        meaning, raise a specific new type **from** it (below)."""),
    predict("Catching by base class", "easy",
        code="""
        class AppError(Exception): pass
        class ConfigError(AppError): pass
        class MissingKeyError(ConfigError, KeyError): pass

        def check(exc):
            try:
                raise exc
            except ConfigError:
                return "config"
            except AppError:
                return "app"
            except KeyError:
                return "key"

        print(check(MissingKeyError("model")), check(AppError()), check(KeyError("x")))
        print(issubclass(MissingKeyError, KeyError), isinstance(ConfigError(), AppError))
        print(check(MissingKeyError) == "config", str(MissingKeyError("model")))
        """,
        hints=["A class can inherit from two exception types; it then matches handlers for either.", "`str` of a `KeyError` subclass shows the repr of its argument."],
        why="""`MissingKeyError` is both a `ConfigError` (so the first handler matches) and a `KeyError` (so code that expects a dict-like
        `KeyError` can catch it too); inheriting from a built-in type like this lets a custom error fit existing handlers. A plain
        `AppError` falls through to the second handler. Raising the class itself works, as Python instantiates it. Because
        `MissingKeyError` inherits `KeyError`'s string behaviour, its message is shown with quotes."""),
)

section("medium", "Medium",
    write("Map HTTP errors to client exceptions", "medium", tag="GenAI",
        prompt="""Define `LLMError(Exception)` and three subclasses: `AuthError`, `RateLimitError` (with an attribute
        `retry_after`, a float in seconds) and `BadRequestError`. Then write `raise_for_status(status, body, headers)` that does
        nothing for a 2xx status and otherwise raises: 401 or 403 `AuthError`; 429 `RateLimitError` with `retry_after` from the
        `retry-after` header (default 1.0); other 4xx `BadRequestError`; 5xx `LLMError`. Every message starts with the status code
        and includes `body[:100]`.""",
        code="""
        class LLMError(Exception):
            pass


        def raise_for_status(status, body, headers):
            pass
        """,
        tests="""
        assert raise_for_status(200, "ok", {}) is None
        cases = [(401, AuthError), (403, AuthError), (400, BadRequestError), (404, BadRequestError), (503, LLMError)]
        for status, kind in cases:
            try:
                raise_for_status(status, "error body " * 30, {})
                assert False, status
            except kind as e:
                assert str(e).startswith(str(status)) and type(e) is kind
        try:
            raise_for_status(429, "slow down", {"retry-after": "2.5"})
        except RateLimitError as e:
            assert e.retry_after == 2.5 and "slow down" in str(e) and isinstance(e, LLMError)
        try:
            raise_for_status(429, "", {})
        except RateLimitError as e:
            assert e.retry_after == 1.0
        assert issubclass(AuthError, LLMError) and issubclass(BadRequestError, LLMError)
        """,
        hints=["`class RateLimitError(LLMError):` with an `__init__(self, message, retry_after)` that calls `super().__init__(message)` and stores `self.retry_after`.",
               "Order the checks: 2xx return, 401/403, 429, other 4xx, then the rest."],
        solution="""
        class LLMError(Exception):
            pass


        class AuthError(LLMError):
            pass


        class BadRequestError(LLMError):
            pass


        class RateLimitError(LLMError):
            def __init__(self, message, retry_after):
                super().__init__(message)
                self.retry_after = retry_after


        def raise_for_status(status, body, headers):
            if 200 <= status < 300:
                return
            message = f"{status}: {body[:100]}"
            if status in (401, 403):
                raise AuthError(message)
            if status == 429:
                raise RateLimitError(message, retry_after=float(headers.get("retry-after", 1.0)))
            if 400 <= status < 500:
                raise BadRequestError(message)
            raise LLMError(message)
        """,
        why="""Each subclass corresponds to a different **reaction**: authentication errors need a human (a wrong or expired key),
        rate limits need waiting, bad requests need the request fixed, and server errors are often worth a retry. That is the test
        for whether an error deserves its own class. Putting `retry_after` on the exception gives the retry code exactly what it
        needs without parsing the message. All of them inherit from `LLMError`, so a caller who does not care about the details can
        catch the base class. Official SDKs (OpenAI's, Anthropic's) have almost this hierarchy: `AuthenticationError`,
        `RateLimitError`, `BadRequestError`, `InternalServerError`, all under one `APIError`."""),
    fix("A translated error that loses its cause", "medium", tag="Data work",
        prompt="""`read_config(text)` converts JSON errors into `ConfigError`. The support tooling reads `err.__cause__` to show
        the line and column of the JSON problem, but it is always `None`. Fix the raise so the cause is recorded.""",
        code="""
        import json

        class ConfigError(Exception):
            pass

        def read_config(text):
            try:
                return json.loads(text)
            except json.JSONDecodeError as e:
                raise ConfigError(f"invalid config: {e.msg}")
        """,
        tests="""
        assert read_config('{"model": "small"}') == {"model": "small"}
        assert read_config("[]") == []
        try:
            read_config('{"model": "small",\\n "retries": }')
            assert False
        except ConfigError as err:
            cause = err.__cause__
            assert isinstance(cause, json.JSONDecodeError) and (cause.lineno, cause.colno) == (2, 13)
            assert "invalid config" in str(err)
        """,
        hints=["`raise NewError(...) from original` sets `__cause__`. Without `from`, only `__context__` is set."],
        solution="""
        import json

        class ConfigError(Exception):
            pass

        def read_config(text):
            try:
                return json.loads(text)
            except json.JSONDecodeError as e:
                raise ConfigError(f"invalid config: {e.msg}") from e
        """,
        why="""Raising inside `except` without `from` chains implicitly: the original is in `__context__`, and the traceback suggests a
        second bug occurred while handling the first. `from e` marks the translation as deliberate and stores the original in
        `__cause__`, where tools and handlers look for the root problem; here it carries the exact line and column. Translating
        low-level errors into your own types, always with `from`, lets callers catch `ConfigError` without knowing that JSON is
        involved, while keeping every detail for debugging."""),
    write("Add the line number and re-raise", "medium", tag="Data work",
        prompt="""Write `parse_lines(lines)` that parses lines of `name,score` into `(name, float(score))` tuples. If any line
        fails with `ValueError` (wrong number of fields or a bad score), add the note `"line N: <repr of the line>"` (N from 1) to
        the exception and re-raise it **unchanged**: same type, same message.""",
        code="""
        def parse_lines(lines):
            pass
        """,
        tests="""
        assert parse_lines(["ana,0.9", "bo, 0.5"]) == [("ana", 0.9), ("bo", 0.5)]
        try:
            parse_lines(["ana,0.9", "bo,high", "cy,1"])
            assert False
        except ValueError as e:
            assert "could not convert" in str(e) and e.__notes__ == ["line 2: 'bo,high'"]
        try:
            parse_lines(["just-a-name"])
            assert False
        except ValueError as e:
            assert e.__notes__ == ["line 1: 'just-a-name'"] and "unpack" in str(e)
        assert parse_lines([]) == []
        """,
        hints=["`name, score = line.split(\",\")` raises `ValueError` for the wrong number of fields; `float` raises it for a bad score.",
               "In `except ValueError as e:` call `e.add_note(...)`, then a bare `raise`."],
        solution="""
        def parse_lines(lines):
            out = []
            for n, line in enumerate(lines, start=1):
                try:
                    name, score = line.split(",")
                    out.append((name.strip(), float(score)))
                except ValueError as e:
                    e.add_note(f"line {n}: {line!r}")
                    raise
            return out
        """,
        why="""Both failure modes are `ValueError`s, from unpacking and from `float`, and both keep their own precise message; the note adds
        the location, which the low-level code could not know. Because the type is unchanged, callers that already catch
        `ValueError` keep working, and the traceback still points at the line that failed. Notes appear under the message when the
        traceback is printed, so logs show "line 2: 'bo,high'" without any extra logging code."""),
    trace("Cause, context and suppression", "medium",
        prompt="Fill in `cause`, `context` and `hidden` after each marked line.",
        code="""
        def make(style):
            try:
                {}["k"]
            except KeyError as e:
                if style == "plain":
                    raise ValueError("plain")
                if style == "from":
                    raise ValueError("from") from e
                raise ValueError("none") from None

        def info(style):
            try:
                make(style)
            except ValueError as err:
                return (type(err.__cause__).__name__, type(err.__context__).__name__, err.__suppress_context__)

        cause, context, hidden = info("plain")  # row: "plain raise"
        cause, context, hidden = info("from")  # row: "raise from e"
        cause, context, hidden = info("none")  # row: "raise from None"
        """,
        trace_vars=["cause", "context", "hidden"],
        hints=["`type(None).__name__` is `\"NoneType\"`. `from` sets `__cause__` and also suppresses the context display."],
        why="""A plain raise inside `except` sets only `__context__`. `from e` sets `__cause__` to `e` (and `__context__` is still the same
        `KeyError`), and `__suppress_context__` becomes `True` so the traceback shows the "direct cause" message instead of "during
        handling". `from None` sets no cause but also suppresses the context, so nothing of the original is printed, though it is
        still stored in `__context__`."""),
    fix("Validation that disappears with -O", "medium", tag="ML",
        prompt="""`normalise(vectors)` scales each embedding to unit length. It validates its input with `assert`, which is removed
        when Python runs with `-O`, and raises `AssertionError`, which callers do not expect. Replace the asserts with proper
        exceptions: `ValueError` for an empty list, vectors of different lengths, or a zero vector.""",
        code="""
        import math

        def normalise(vectors):
            assert vectors, "no vectors"
            dim = len(vectors[0])
            out = []
            for v in vectors:
                assert len(v) == dim, "length mismatch"
                norm = math.sqrt(sum(x * x for x in v))
                assert norm > 0, "zero vector"
                out.append([round(x / norm, 4) for x in v])
            return out
        """,
        tests="""
        assert normalise([[3, 4], [0, 2]]) == [[0.6, 0.8], [0.0, 1.0]]
        for bad, word in [([], "empty"), ([[1, 2], [1, 2, 3]], "length"), ([[0, 0]], "zero")]:
            try:
                normalise(bad)
                assert False, bad
            except ValueError as e:
                assert word in str(e), str(e)
        assert normalise([[1]]) == [[1.0]]
        """,
        hints=["Use `if ...: raise ValueError(...)` for each check, with a message containing the word the test looks for and the details."],
        solution="""
        import math

        def normalise(vectors):
            if not vectors:
                raise ValueError("cannot normalise an empty list of vectors")
            dim = len(vectors[0])
            out = []
            for i, v in enumerate(vectors):
                if len(v) != dim:
                    raise ValueError(f"vector {i} has length {len(v)}, expected {dim}")
                norm = math.sqrt(sum(x * x for x in v))
                if norm == 0:
                    raise ValueError(f"vector {i} is a zero vector and has no direction")
                out.append([round(x / norm, 4) for x in v])
            return out
        """,
        why="""`assert` documents what **your code** guarantees; it is not for checking what **callers** pass in. With `python -O` every
        `assert` is stripped, so the bad input would flow on and fail later with a confusing `ZeroDivisionError` or an `IndexError`.
        `ValueError` is the expected type for unacceptable input, and the new messages say which vector failed and why, which
        `AssertionError("length mismatch")` did not. The test words (`empty`, `length`, `zero`) stand in for what a user would need
        to find in the message."""),
    refactor("Error codes to exceptions", "medium", tag="Data work",
        prompt="""The helpers return `(None, error)` tuples that every caller must check. Make the helpers raise `ValueError`
        instead, and let `import_user` catch it once. `import_user`'s results must stay the same. Keep the tests green.""",
        code="""
        def parse_age(raw):
            if not raw.strip().isdigit():
                return None, f"age is not a number: {raw!r}"
            age = int(raw)
            if age > 130:
                return None, f"age out of range: {age}"
            return age, None

        def parse_email(raw):
            email = raw.strip().lower()
            if email.count("@") != 1:
                return None, f"invalid email: {raw!r}"
            return email, None

        def import_user(row):
            age, err = parse_age(row["age"])
            if err:
                return {"ok": False, "error": err}
            email, err = parse_email(row["email"])
            if err:
                return {"ok": False, "error": err}
            return {"ok": True, "user": {"age": age, "email": email}}
        """,
        tests="""
        assert import_user({"age": " 34", "email": "Ana@Example.com "}) == {"ok": True, "user": {"age": 34, "email": "ana@example.com"}}
        assert import_user({"age": "x", "email": "a@b.c"}) == {"ok": False, "error": "age is not a number: 'x'"}
        assert import_user({"age": "200", "email": "a@b.c"}) == {"ok": False, "error": "age out of range: 200"}
        assert import_user({"age": "1", "email": "nope"}) == {"ok": False, "error": "invalid email: 'nope'"}
        """,
        hints=["Each helper returns just the value or raises `ValueError(message)`.", "`import_user` wraps both calls in one `try` and returns the error dict with `str(e)`."],
        solution="""
        def parse_age(raw):
            if not raw.strip().isdigit():
                raise ValueError(f"age is not a number: {raw!r}")
            age = int(raw)
            if age > 130:
                raise ValueError(f"age out of range: {age}")
            return age

        def parse_email(raw):
            email = raw.strip().lower()
            if email.count("@") != 1:
                raise ValueError(f"invalid email: {raw!r}")
            return email

        def import_user(row):
            try:
                user = {"age": parse_age(row["age"]), "email": parse_email(row["email"])}
            except ValueError as e:
                return {"ok": False, "error": str(e)}
            return {"ok": True, "user": user}
        """,
        why="""With error codes, every call site needs an `if err:` check, and forgetting one lets a `None` slip into the data. With
        exceptions, the helpers return plain values and the failure path is handled in one place, at the level that knows what to do
        with it (here: turn it into a result dict). The helpers also become easier to reuse, since callers that want a crash on
        bad data get one for free. Error codes still have their place at **boundaries** where exceptions cannot cross, such as an
        API response, which is exactly what `import_user` returns."""),
    write("Collect every validation error", "medium", tag="GenAI",
        prompt="""Write `validate_request(req)` for a chat request dict. Collect **all** problems and, if there are any, raise
        `ExceptionGroup("invalid request", errors)`: `ValueError("messages must be a non-empty list")` if `messages` is missing,
        not a list or empty; for each message `i` without a `role` in `{"system", "user", "assistant"}`,
        `ValueError(f"message {i}: bad role {role!r}")`; `TypeError("temperature must be a number")` if `temperature` is present and
        not an `int`/`float` (not `bool`). Return `True` if valid.""",
        code="""
        def validate_request(req):
            pass
        """,
        tests="""
        good = {"messages": [{"role": "system", "content": "x"}, {"role": "user", "content": "y"}], "temperature": 0.3}
        assert validate_request(good) is True
        assert validate_request({"messages": [{"role": "user"}]}) is True
        bad = {"messages": [{"role": "user"}, {"role": "bot"}, {}], "temperature": "hot"}
        try:
            validate_request(bad)
            assert False
        except ExceptionGroup as eg:
            assert [str(e) for e in eg.exceptions] == ["message 1: bad role 'bot'", "message 2: bad role None",
                                                       "temperature must be a number"]
            values, types = eg.split(ValueError)
            assert len(values.exceptions) == 2 and len(types.exceptions) == 1
        try:
            validate_request({"messages": []})
            assert False
        except ExceptionGroup as eg:
            assert [type(e) for e in eg.exceptions] == [ValueError]
        """,
        hints=["Append exceptions to a list instead of raising them. `msg.get(\"role\")` gives `None` for a missing role.",
               "Only check the messages one by one if `messages` is a non-empty list."],
        solution="""
        ROLES = {"system", "user", "assistant"}

        def validate_request(req):
            errors = []
            messages = req.get("messages")
            if not isinstance(messages, list) or not messages:
                errors.append(ValueError("messages must be a non-empty list"))
            else:
                for i, msg in enumerate(messages):
                    role = msg.get("role")
                    if role not in ROLES:
                        errors.append(ValueError(f"message {i}: bad role {role!r}"))
            if "temperature" in req:
                t = req["temperature"]
                if isinstance(t, bool) or not isinstance(t, (int, float)):
                    errors.append(TypeError("temperature must be a number"))
            if errors:
                raise ExceptionGroup("invalid request", errors)
            return True
        """,
        why="""Creating exceptions without raising them is perfectly fine: they are ordinary objects until `raise`. Collecting them gives
        the user every problem in one round trip, which matters for API clients and form-like inputs. `eg.split(ValueError)` (used in
        the test) divides a group by type, the same thing `except*` does behind the scenes. The `else` branch avoids validating
        individual messages when the list itself is unusable, so the errors stay meaningful. In practice, Pydantic does this
        collection for you and reports each field's problem with its location (11.4)."""),
    predict("Messages, notes and suppressed context", "medium",
        code="""
        import traceback

        class InvalidOutputError(Exception):
            def __init__(self, message, raw):
                super().__init__(message)
                self.raw = raw

        e = InvalidOutputError("not JSON", raw="{label: x}")
        print(str(e), e.args, e.raw)

        try:
            try:
                {}["model"]
            except KeyError:
                raise LookupError("unknown model 'gpt-x'") from None
        except LookupError as err:
            err.add_note("known models: small, large")
            lines = traceback.format_exc().strip().splitlines()
            print(lines[-2:], "KeyError" in "".join(lines))
        """,
        hints=["Only the message passed to `super().__init__` is in `args`.", "`from None` hides the original from the printed traceback."],
        why="""The extra attribute `raw` is stored separately; `args` and `str` come from the message passed to the parent class. In the
        second part, `from None` suppresses the `KeyError`, so the printed traceback mentions only the `LookupError`, and the note
        appears as the last line, under the message. That is the clean way to replace an internal error with a user-facing one."""),
)

section("hard", "Hard",
    write("Translate library errors at the boundary", "hard", tag="GenAI",
        prompt="""Your code wraps a third-party provider SDK, and you want callers to see only your own exceptions. Write
        `translate(fn, mapping)` that calls `fn()` and returns its result. If it raises an exception that is an instance of a key in
        `mapping` (a dict from SDK exception class to your exception class, checked **in order**, so put subclasses first), raise the
        mapped exception with the message `f"{type(e).__name__}: {e}"`, chained **from** the original. Other exceptions propagate
        unchanged.""",
        code="""
        def translate(fn, mapping):
            pass
        """,
        tests="""
        class SDKError(Exception): pass
        class SDKRateLimit(SDKError): pass
        class AppError(Exception): pass
        class AppRateLimit(AppError): pass

        mapping = {SDKRateLimit: AppRateLimit, SDKError: AppError}

        def raiser(exc):
            def fn():
                raise exc
            return fn

        assert translate(lambda: 42, mapping) == 42
        assert translate(lambda: "ok", {}) == "ok"
        try:
            translate(raiser(SDKRateLimit("429")), mapping)
            assert False
        except AppRateLimit as e:
            assert str(e) == "SDKRateLimit: 429" and isinstance(e.__cause__, SDKRateLimit)
        try:
            translate(raiser(SDKError("boom")), mapping)
            assert False
        except AppError as e:
            assert type(e) is AppError and type(e.__cause__) is SDKError
        try:
            translate(raiser(ZeroDivisionError("bug")), mapping)
            assert False
        except ZeroDivisionError as e:
            assert e.__cause__ is None
        """,
        hints=["Catch `Exception as e`, loop over `mapping.items()`, and `raise target(...) from e` on the first `isinstance` match.",
               "If nothing matches, a bare `raise` re-raises the original unchanged."],
        solution="""
        def translate(fn, mapping):
            try:
                return fn()
            except Exception as e:
                for source, target in mapping.items():
                    if isinstance(e, source):
                        raise target(f"{type(e).__name__}: {e}") from e
                raise
        """,
        why="""Catching `Exception` is acceptable here because the handler does not swallow anything: it either translates or re-raises
        the original with a bare `raise`, so a bug like `ZeroDivisionError` still surfaces with its own traceback. Dicts keep
        insertion order, which makes "subclasses first" a reliable rule: `SDKRateLimit` must be checked before its parent `SDKError`,
        or every rate limit would become a generic `AppError`. `from e` keeps the SDK's exception, with its status code and response
        details, available in `__cause__`. This boundary pattern is what keeps an application independent of any one provider: the
        rest of the code catches `AppRateLimit`, whichever SDK is behind it."""),
    fix("Read the code: a client that retries the wrong errors", "hard", tag="GenAI",
        prompt="""`send(request, transport, attempts)` calls `transport(request)` and should retry **only** `RateLimited`, up to
        `attempts` calls in total, re-raising the last `RateLimited` unchanged if all fail. `BadRequest` and any other error must
        propagate immediately, unchanged, after one call. The current code retries everything and replaces the error with a plain
        `Exception`. Read it, find the bugs and fix them.""",
        code="""
        class ProviderError(Exception):
            pass


        class RateLimited(ProviderError):
            pass


        class BadRequest(ProviderError):
            pass


        def send(request, transport, attempts=3):
            for attempt in range(attempts):
                try:
                    return transport(request)
                except Exception as e:
                    if attempt == attempts - 1:
                        raise Exception(f"request failed after {attempts} attempts: {e}")
        """,
        tests="""
        def scripted(*outcomes):
            calls = []
            def transport(req):
                calls.append(req)
                out = outcomes[len(calls) - 1]
                if isinstance(out, Exception):
                    raise out
                return out
            return transport, calls

        t, calls = scripted(RateLimited("429 a"), "done")
        assert send("r", t) == "done" and len(calls) == 2
        t, calls = scripted("first try")
        assert send("r", t, attempts=1) == "first try" and len(calls) == 1
        t, calls = scripted(RateLimited("a"), RateLimited("b"), RateLimited("c"))
        try:
            send("r", t, attempts=3)
            assert False
        except RateLimited as e:
            assert str(e) == "c" and len(calls) == 3
        for err in [BadRequest("400: bad"), KeyError("bug")]:
            t, calls = scripted(err, "never")
            try:
                send("r", t)
                assert False
            except type(err) as e:
                assert e is err and len(calls) == 1
        """,
        hints=["Catch only `RateLimited`. Everything else then propagates on its own, unchanged, after one call.",
               "On the last attempt, a bare `raise` re-raises the final `RateLimited` itself."],
        solution="""
        class ProviderError(Exception):
            pass


        class RateLimited(ProviderError):
            pass


        class BadRequest(ProviderError):
            pass


        def send(request, transport, attempts=3):
            for attempt in range(1, attempts + 1):
                try:
                    return transport(request)
                except RateLimited:
                    if attempt == attempts:
                        raise
        """,
        why="""Three bugs. `except Exception` retried a `BadRequest` (which will fail identically every time, wasting calls and money) and
        even a `KeyError` from a bug. The final `raise Exception(...)` replaced the specific type, so callers could no longer catch
        `RateLimited` or `BadRequest`, and the message became the only trace of what happened. Catching only `RateLimited` fixes
        both: every other exception leaves the function untouched on the first call. The bare `raise` on the last attempt re-raises
        the actual `RateLimited` object, so its `retry_after` or other details survive. Retries also need waiting between attempts
        (exponential backoff), which 7.4 and 8.3 add."""),
    write("Walk an exception chain", "hard", tag="Data work",
        prompt="""Error reports often show the full chain of causes. Write `chain(exc)` returning a list of `"Type: message"`
        strings, starting with `exc` and following each exception's link to the one before it: `__cause__` if it is set, otherwise
        `__context__`, unless `__suppress_context__` is true (then stop). Guard against cycles.""",
        code="""
        def chain(exc):
            pass
        """,
        tests="""
        import json

        def build(style):
            try:
                try:
                    json.loads("{bad")
                except ValueError as e:
                    raise KeyError("model") from e
            except KeyError as k:
                if style == "context":
                    raise RuntimeError("load failed")
                raise RuntimeError("load failed") from None

        try:
            build("context")
        except RuntimeError as e:
            out = chain(e)
        assert out[0] == "RuntimeError: load failed" and out[1] == "KeyError: 'model'" and out[2].startswith("JSONDecodeError: Expecting")
        assert len(out) == 3
        try:
            build("none")
        except RuntimeError as e:
            assert chain(e) == ["RuntimeError: load failed"]
        assert chain(ValueError("solo")) == ["ValueError: solo"]
        a, b = ValueError("a"), ValueError("b")
        a.__context__, b.__context__ = b, a
        assert chain(a) == ["ValueError: a", "ValueError: b"]
        """,
        hints=["Loop while `exc is not None`; keep a set of `id(exc)` already seen to stop on cycles.",
               "Next link: `exc.__cause__` if it is not `None`, else `None` if `exc.__suppress_context__`, else `exc.__context__`."],
        solution="""
        def chain(exc):
            out, seen = [], set()
            while exc is not None and id(exc) not in seen:
                seen.add(id(exc))
                out.append(f"{type(exc).__name__}: {exc}")
                if exc.__cause__ is not None:
                    exc = exc.__cause__
                elif exc.__suppress_context__:
                    exc = None
                else:
                    exc = exc.__context__
            return out
        """,
        why="""These are exactly the rules the traceback printer uses: an explicit cause wins, `from None` stops the chain, and otherwise the
        implicit context is followed. Each link is an exception object you can inspect, which is how error trackers such as Sentry
        show the whole story of a failure. The cycle guard matters because nothing forbids two exceptions from pointing at each
        other, and the standard library's printer has the same protection. `id()` is safe here because all the objects in the chain
        are alive at the same time (2.1). Note that the `KeyError`'s message keeps its quotes, as `str` of a `KeyError` always does."""),
    predict("except* splits a group", "hard",
        code="""
        def fail_many():
            raise ExceptionGroup("batch", [
                ValueError("bad row 3"),
                TimeoutError("embedding call"),
                ValueError("bad row 9"),
                ExceptionGroup("nested", [KeyError("id")]),
            ])

        try:
            fail_many()
        except* ValueError as g:
            print("values:", [str(e) for e in g.exceptions])
        except* (TimeoutError, KeyError) as g:
            print("other:", len(g.exceptions), type(g.exceptions[-1]).__name__)

        try:
            try:
                fail_many()
            except* ValueError:
                print("handled values only")
        except ExceptionGroup as rest:
            print("left over:", [type(e).__name__ for e in rest.exceptions])
        """,
        hints=["`except*` keeps the group's nesting: the matching part of a nested group stays nested.",
               "Exceptions not matched by any `except*` clause are re-raised as a new group."],
        why="""The first `except*` receives a group of the two `ValueError`s. The second receives everything matching its tuple: the
        `TimeoutError` at the top level and the nested group containing the `KeyError`, kept as a nested group, which is why its last
        item is an `ExceptionGroup`. In the second block only `ValueError`s are handled, so the rest is re-raised automatically as a
        group of what was left, still including the nested group. This automatic re-raise is the key difference from `except`:
        unhandled parts of a group can never be silently dropped."""),
)

section("interview", "Interview questions",
    explain("When should you define a custom exception, and how would you design the exception hierarchy for a library?", "medium", tag="Interview",
        why="""Define a custom exception when callers need to **react differently** to a failure than to other failures: retry a rate
        limit, re-authenticate on an auth error, report bad input to the user. If no caller would ever catch it specifically, a
        built-in type with a good message is enough. For a library, create one base class (`class MyLibError(Exception)`) so users can
        catch everything from your library in one clause, and a small number of subclasses for the distinct reactions; inherit from a
        built-in as well when it fits existing expectations (a "not found" error can also subclass `LookupError`). Put useful data
        on the exception as attributes (status code, retry delay, the invalid value) instead of making users parse the message.
        Translate errors from your dependencies into your own types at the boundary, with `raise ... from e`, and document which
        exceptions each public function raises."""),
    explain("What is the difference between `raise X from e`, raising inside `except` without `from`, and `raise X from None`?", "medium", tag="Interview",
        why="""All three happen while another exception `e` is being handled. Without `from`, Python sets `X.__context__ = e` (implicit
        chaining), and the traceback shows both with "During handling of the above exception, another exception occurred", which
        suggests the handler itself failed by accident. With `from e`, Python sets `X.__cause__ = e` and the traceback says "The
        above exception was the direct cause of the following exception": a deliberate translation, the right choice when you
        convert a low-level error into a meaningful one. With `from None`, the context is still stored but `__suppress_context__` is
        set, so only `X` is printed; use it when the original is an implementation detail that would only confuse the reader, such
        as a `KeyError` from an internal dict lookup replaced by "unknown model"."""),
    explain("How should a client library for an LLM API expose errors to its users?", "hard", tag="Interview",
        why="""With a small, documented hierarchy under one base class, organised by what the user should do: authentication and
        permission errors (fix the key, no retry), bad requests including validation and context-length errors (fix the request, no
        retry), rate limits (wait, with the delay as an attribute from the `Retry-After` header), timeouts and connection errors (safe
        to retry with backoff), and server errors (often retryable). Each exception should carry structured data: HTTP status,
        provider error code, request id for support tickets, and the response body where safe, without leaking the API key. Low-level
        network exceptions are translated with `from e` so their details remain available. The library can retry transient errors
        itself, with a configurable maximum and exponential backoff with jitter, and should raise the final error, not swallow it.
        Streaming responses need the same treatment for errors that arrive mid-stream. The OpenAI and Anthropic Python SDKs follow
        exactly this design, which is why `except anthropic.RateLimitError` works the way users expect."""),
)

recap(
    "Pick the type by meaning (`TypeError` wrong kind, `ValueError` bad value, your own class for errors callers handle specially), and write messages with what, which value and what was expected.",
    "A bare `raise` re-raises unchanged; never replace a specific error with a plain `Exception`.",
    "Custom exceptions: one base class per component, subclasses per reaction, data as attributes via `super().__init__(message)`.",
    "Translate with `raise New(...) from e`; `from None` hides internal noise; `add_note` adds context without changing the type.",
    "`ExceptionGroup` and `except*` report several errors at once. `assert` checks your own invariants, never input.",
)
