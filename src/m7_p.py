from lesson import *
from diagrams import *

lesson(
    id="m7-p", num="7.P", title="Module 7 practice set and mini project",
    intro="Mixed problems from all of Module 7: try/except/else/finally, raising and custom exceptions, chaining and "
          "notes, design choices such as EAFP and consistency, and the failure modes of API calls. Then a mini project "
          "that needs all of it: a resilient client that gets valid JSON from an LLM.",
    desc="Mixed problems from the whole module, then one small program that uses all of it.",
    keys="practice mixed review project resilient client retry backoff jitter fallback repair exception hierarchy idempotency cleanup exceptiongroup stream error agent loop",
)

section("how", "How to use this page",
    fig(stage_map(7, "a resilient JSON client"), "Module 7 at a glance: how exceptions travel, how to raise and design them, and how remote calls fail, building up to a client that survives all of it."),
    p("""For every error in a problem, ask the three questions this module has been about. **Who should handle it?** The lowest
    level that can do something useful; everyone else lets it pass (7.3). **What kind is it?** Expected and recoverable (bad
    input, a missing optional value), transient (timeouts, rate limits, overloaded servers), permanent (a bad request, a wrong
    key), or a bug (7.4). **What must survive?** The original type and traceback (bare `raise`, `raise ... from`), the
    consistency of the data, and enough context to debug it later (7.2)."""),
    p("""The problems mix the lessons on purpose. The mini project at the end combines all of them in one client that real
    applications need."""),
)

section("set", "Practice set",
    predict("The whole statement", "easy",
        code="""
        import json

        def run(text):
            out = []
            try:
                data = json.loads(text)
                out.append("parsed")
            except ValueError as e:
                out.append(type(e).__name__)
            else:
                out.append(f"keys={sorted(data)}")
            finally:
                out.append("done")
            return out

        print(run('{"b": 1, "a": 2}'))
        print(run("{bad"))
        try:
            run('[1, 2]')
        except TypeError as e:
            print("caller:", type(e).__name__)
        """,
        hints=["`sorted` on a list of numbers works; on a dict it sorts the keys.", "An error in `else` is not caught by the same statement's `except`."],
        why="""For valid JSON the `try` succeeds, `else` lists the keys and `finally` adds "done". Invalid JSON raises `JSONDecodeError`, a
        `ValueError`, so the handler records its exact type, `else` is skipped and `finally` still runs. For `[1, 2]` the parse
        succeeds, and `sorted([1, 2])` also works, so no error happens: the result is returned, nothing reaches the caller's `except`,
        and nothing is printed for it."""),
    write("Parse a boolean setting", "easy", tag="Data work",
        prompt="""Environment variables and config files hold booleans as text. Write `parse_bool(value)` accepting `true/false`,
        `yes/no`, `on/off` and `1/0` in any case and with surrounding spaces, and real `bool`s. Anything else raises `ValueError` with a
        message listing the accepted values and showing the bad one with `repr`.""",
        code="""
        def parse_bool(value):
            pass
        """,
        tests="""
        assert [parse_bool(v) for v in ["true", " YES ", "On", "1", True]] == [True] * 5
        assert [parse_bool(v) for v in ["false", "no", "OFF", "0", False]] == [False] * 5
        for bad in ["maybe", "", "2", None]:
            try:
                parse_bool(bad)
                assert False, bad
            except ValueError as e:
                assert repr(bad) in str(e) and "yes" in str(e)
        """,
        hints=["Handle `bool` first, then `str(value).strip().lower()` and look it up in two sets."],
        solution="""
        TRUE = {"true", "yes", "on", "1"}
        FALSE = {"false", "no", "off", "0"}

        def parse_bool(value):
            if isinstance(value, bool):
                return value
            text = value.strip().lower() if isinstance(value, str) else None
            if text in TRUE:
                return True
            if text in FALSE:
                return False
            accepted = ", ".join(sorted(TRUE | FALSE))
            raise ValueError(f"expected one of {accepted}, got {value!r}")
        """,
        why="""`bool("false")` is `True` (any non-empty string is truthy, 1.1), which is why configuration parsing needs an explicit function.
        Accepting a fixed vocabulary and rejecting everything else with a message that lists the options turns a silent
        misconfiguration into an error at start-up, where it is cheap to fix. `None` becomes a `ValueError` with the same message
        rather than an `AttributeError` from calling `.strip()` on it. Sorting the accepted values makes the message the same on every
        run, since sets of strings have no stable order (6.2)."""),
    fix("An except clause that catches less than it says", "easy", tag="Data work",
        prompt="""`to_float(value)` should return `None` for values that are not numbers, both bad strings and wrong types. It still
        crashes on `None`. Fix the `except` clause.""",
        code="""
        def to_float(value):
            try:
                return float(value)
            except ValueError or TypeError:
                return None
        """,
        tests="""
        assert to_float("2.5") == 2.5 and to_float(3) == 3.0
        assert to_float("abc") is None
        assert to_float(None) is None and to_float([1]) is None
        """,
        hints=["`ValueError or TypeError` is an expression; evaluate it in your head."],
        solution="""
        def to_float(value):
            try:
                return float(value)
            except (ValueError, TypeError):
                return None
        """,
        why="""`except` takes an expression that evaluates to an exception class or a tuple of them. `ValueError or TypeError` is an `or`
        expression, which returns its first truthy operand (1.1), and a class is always truthy, so it evaluates to just `ValueError`:
        `TypeError` was never caught. A tuple lists several types. Linters flag this pattern, which looks right when read aloud and is
        silently wrong."""),
    predict("Notes, causes and the as name", "medium",
        code="""
        class ParseError(Exception):
            pass

        def parse(row):
            try:
                return int(row["n"])
            except (KeyError, ValueError) as e:
                err = ParseError(f"bad row {row!r}")
                err.add_note(f"original: {type(e).__name__}")
                raise err from e

        for row in [{"n": "4"}, {"n": "x"}, {}]:
            try:
                print(parse(row))
            except ParseError as e:
                print(e, "|", e.__notes__, "|", type(e.__cause__).__name__)
        print("e" in dir(), "err" in dir())
        """,
        hints=["Each failure creates a new `ParseError` linked to the original with `from`."],
        why="""The valid row returns 4. The other two raise a `ParseError` whose message shows the row, whose note names the original type,
        and whose `__cause__` is the original exception (a `ValueError` from `int`, a `KeyError` from the missing key). At module level
        after the loop, the `as e` name has been deleted by the last handler, and `err` was local to `parse`, so neither exists."""),
    write("Wrap JSON errors with the line number", "medium", tag="Data work",
        prompt="""Define `RecordError(ValueError)` with a `lineno` attribute. Write a generator `records(lines)` that yields the
        parsed object of each non-blank line and, on invalid JSON, raises `RecordError(f"line {n}: {e.msg}")` with `lineno=n`
        (counting from 1), chained from the original error.""",
        code="""
        import json

        def records(lines):
            pass
        """,
        tests="""
        lines = ['{"id": 1}', "", '{"id": 2', '{"id": 3}']
        g = records(lines)
        assert next(g) == {"id": 1}
        try:
            next(g)
            assert False
        except RecordError as e:
            assert e.lineno == 3 and str(e) == "line 3: Expecting ',' delimiter" and isinstance(e.__cause__, json.JSONDecodeError)
        assert issubclass(RecordError, ValueError)
        assert list(records(['{"a": 1}', "  ", '[2]'])) == [{"a": 1}, [2]]
        """,
        hints=["`class RecordError(ValueError):` with `__init__(self, message, lineno)` calling `super().__init__(message)`.",
               "In the generator: `for n, line in enumerate(lines, start=1)`, skip blank lines, put only `json.loads(line)` in the `try`, and `yield` the result after it."],
        solution="""
        import json


        class RecordError(ValueError):
            def __init__(self, message, lineno):
                super().__init__(message)
                self.lineno = lineno


        def records(lines):
            for n, line in enumerate(lines, start=1):
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as e:
                    raise RecordError(f"line {n}: {e.msg}", lineno=n) from e
                yield obj
        """,
        why="""Inheriting from `ValueError` means existing code that catches `ValueError` keeps working, while new code can catch `RecordError`
        and read `e.lineno` instead of parsing the message. The parse is in the `try` and the `yield` outside it: if the `yield` were inside,
        an exception thrown into the generator at that point by its consumer could be caught by the wrong handler. `e.msg` is the
        `JSONDecodeError`'s message without position details, and `from e` keeps those details in `__cause__`. Because the generator
        is lazy (6.3), the error is raised when the bad line is reached, after the first record was already delivered."""),
    fix("A retry that creates duplicates", "medium", tag="GenAI",
        prompt="""`create_ticket(api, payload, attempts)` calls `api(payload, idempotency_key)` and retries on `TimeoutError`. The
        API creates a ticket once per idempotency key, but customers get duplicate tickets after timeouts. Fix it so every attempt for
        one ticket uses the **same** key. (`new_key` is injected so the test can see the keys.)""",
        code="""
        def create_ticket(api, payload, attempts, new_key):
            for attempt in range(1, attempts + 1):
                try:
                    return api(payload, new_key())
                except TimeoutError:
                    if attempt == attempts:
                        raise
        """,
        tests="""
        import itertools
        counter = itertools.count(1)
        new_key = lambda: f"key-{next(counter)}"
        created, seen_keys = {}, []
        def api(payload, key):
            seen_keys.append(key)
            created.setdefault(key, payload)       # the server creates once per key
            if len(seen_keys) < 3:
                raise TimeoutError("response lost")   # the ticket WAS created, but the reply timed out
            return key
        assert create_ticket(api, {"title": "refund"}, 5, new_key) == "key-1"
        assert seen_keys == ["key-1", "key-1", "key-1"] and len(created) == 1
        """,
        hints=["Generate the key once, before the loop."],
        solution="""
        def create_ticket(api, payload, attempts, new_key):
            key = new_key()
            for attempt in range(1, attempts + 1):
                try:
                    return api(payload, key)
                except TimeoutError:
                    if attempt == attempts:
                        raise
        """,
        why="""A timeout does not tell you whether the server did the work; here it did, every time, and only the replies were lost. With a
        new key per attempt, the server saw three different operations and created three tickets. The idempotency key identifies the
        **logical operation**, so it must be created once, before the first attempt, and reused for every retry; then the server can
        recognise a repeat and return the original result. Payment APIs (Stripe), and increasingly LLM batch and file APIs, support
        idempotency keys for exactly this reason."""),
    write("Attempt every cleanup step", "medium", tag="ML",
        prompt="""After a training run, several temporary files must be removed. Write `cleanup(paths, remove)` that calls
        `remove(path)` for **every** path, even after failures. `FileNotFoundError` is fine and ignored. Other `OSError`s are collected;
        at the end, if there were any, raise `ExceptionGroup("cleanup failed", errors)`, each error with a note naming its path. Return
        the number of files removed.""",
        code="""
        def cleanup(paths, remove):
            pass
        """,
        tests="""
        removed = []
        def remove(path):
            if path.startswith("gone"):
                raise FileNotFoundError(path)
            if path.startswith("locked"):
                raise PermissionError(f"in use: {path}")
            removed.append(path)

        assert cleanup(["a.tmp", "gone.tmp", "b.tmp"], remove) == 2 and removed == ["a.tmp", "b.tmp"]
        removed.clear()
        try:
            cleanup(["locked1.ckpt", "c.tmp", "gone2", "locked2.ckpt"], remove)
            assert False
        except ExceptionGroup as eg:
            assert removed == ["c.tmp"]
            assert [e.__notes__ for e in eg.exceptions] == [["path: locked1.ckpt"], ["path: locked2.ckpt"]]
        assert cleanup([], remove) == 0
        """,
        hints=["Catch `FileNotFoundError` before `OSError` (it is a subclass). Collect the others with `e.add_note(...)`."],
        solution="""
        def cleanup(paths, remove):
            errors, count = [], 0
            for path in paths:
                try:
                    remove(path)
                except FileNotFoundError:
                    continue
                except OSError as e:
                    e.add_note(f"path: {path}")
                    errors.append(e)
                else:
                    count += 1
            if errors:
                raise ExceptionGroup("cleanup failed", errors)
            return count
        """,
        why="""Cleanup is the one place where stopping at the first error is wrong: one locked file should not leave every other temporary file
        on disk. So each step is attempted, the failures are collected, and they are all reported together at the end, which is what
        exception groups are for (7.2). `FileNotFoundError` is caught first because it is an `OSError` too, and "already gone" is the
        desired end state. The notes record which path each error belongs to without changing the exception types, so a caller can
        still use `except* PermissionError`. Only `OSError`s are collected; anything else, such as a `TypeError` from a bad path, is a
        bug and stops the loop at once."""),
    choose("Mostly invalid numbers: check first or catch", "medium",
        prompt="Both convert 200,000 strings to integers, using `None` for invalid ones. 90% of the strings are invalid. Which is faster?",
        setup="""values = [str(i) if i % 10 == 0 else f"id-{i}" for i in range(200_000)]""",
        options={
            "a": "out = []\nfor v in values:\n    try:\n        out.append(int(v))\n    except ValueError:\n        out.append(None)",
            "b": "out = [int(v) if v.isdigit() else None for v in values]",
        },
        answer="b",
        hints=["What does each version pay for an invalid string?"],
        why="""For each invalid string, version A starts converting, raises a `ValueError` (building the exception and its traceback), unwinds
        to the handler and clears it. Version B asks `isdigit`, a quick C-level scan, and skips the conversion entirely. When failures are
        the **common** case, look-before-you-leap is faster (7.3); when they are rare, the `try` version costs almost nothing. Note that
        `isdigit` is not a full validator: it rejects `"-5"` and `" 5"`, which `int` accepts, so the two versions only agree because the
        data here has no signs or spaces."""),
    trace("An exception crossing three functions", "medium",
        prompt="Fill in `log` after each marked line.",
        code="""
        log = []

        def low(x):
            try:
                return 10 // x
            finally:
                log.append("low finally")

        def mid(x):
            try:
                return low(x) + 1
            except TypeError:
                log.append("mid TypeError")
                return -1

        def top(x):
            try:
                return mid(x)
            except ZeroDivisionError:
                log.append("top ZeroDivision")
                return 0
            finally:
                log.append("top finally")

        top(5)  # row: "x = 5"
        log.clear(); top(0)  # row: "x = 0"
        log.clear(); top("a")  # row: "x = 'a'"
        """,
        trace_vars=["log"],
        hints=["Each `finally` runs as the exception passes through its function. The first matching handler up the stack handles it."],
        why="""With 5, nothing fails: both `finally` blocks run on the way out. With 0, `low` raises `ZeroDivisionError`; its `finally` runs as the
        exception leaves; `mid` only handles `TypeError`, so the exception continues to `top`, whose handler runs, then its `finally`.
        With `"a"`, `10 // "a"` raises `TypeError`; `low`'s `finally` runs, and `mid` handles it and returns normally, so `top` sees no
        exception and only its `finally` runs."""),
    refactor("Flatten nested try blocks", "medium", tag="GenAI",
        prompt="Rewrite with a single `try` and one `except` per error type. Same results. Keep the tests green.",
        code="""
        import json

        def load_prompt(path):
            try:
                f = open(path, encoding="utf-8")
                try:
                    try:
                        data = json.load(f)
                        try:
                            return data["template"].strip()
                        except KeyError:
                            return "error: no template"
                    except json.JSONDecodeError:
                        return "error: invalid JSON"
                finally:
                    f.close()
            except FileNotFoundError:
                return "error: missing file"
        """,
        tests="""
        import os, tempfile
        d = tempfile.mkdtemp()
        def write(name, text):
            p = os.path.join(d, name)
            with open(p, "w", encoding="utf-8") as f:
                f.write(text)
            return p
        assert load_prompt(write("ok.json", '{"template": "  Answer: {q} "}')) == "Answer: {q}"
        assert load_prompt(write("nokey.json", '{"x": 1}')) == "error: no template"
        assert load_prompt(write("bad.json", "{oops")) == "error: invalid JSON"
        assert load_prompt(os.path.join(d, "missing.json")) == "error: missing file"
        """,
        hints=["`with open(...)` replaces the inner `try`/`finally`. The three handlers can all follow one `try`."],
        solution="""
        import json

        def load_prompt(path):
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                return data["template"].strip()
            except FileNotFoundError:
                return "error: missing file"
            except json.JSONDecodeError:
                return "error: invalid JSON"
            except KeyError:
                return "error: no template"
        """,
        why="""The nesting existed for two reasons: closing the file (which `with` does, 10.2) and pairing each handler with its step. Since
        the three exception types cannot be confused with each other, one `try` with three handlers is equivalent and readable from top to
        bottom. Reading the template after the `with` block also closes the file as early as possible. If two steps could raise the same
        type for different reasons, separate `try` blocks would still be needed, which is the narrowness rule of 7.1."""),
    write("Errors in the middle of a stream", "hard", tag="GenAI",
        prompt="""Streaming APIs can report an error **after** sending part of the answer, as an event like `{"type": "error",
        "error": {"type": "overloaded_error", "message": "..."}}`. Define `StreamError(Exception)` with attributes `kind` and
        `partial` (the text received so far). Write a generator `stream_text(events)` that yields the `"text"` of each `{"type":
        "delta", "text": ...}` event, stops at `{"type": "stop"}`, ignores other event types, and on an error event raises
        `StreamError(message, kind, partial)`. If the events end without a stop event, raise `StreamError("stream ended early",
        "incomplete", partial)`.""",
        code="""
        def stream_text(events):
            pass
        """,
        tests="""
        ok = [{"type": "ping"}, {"type": "delta", "text": "Refunds "}, {"type": "delta", "text": "take 5 days."}, {"type": "stop"}]
        assert "".join(stream_text(ok)) == "Refunds take 5 days."
        bad = [{"type": "delta", "text": "Refunds "}, {"type": "error", "error": {"type": "overloaded_error", "message": "busy"}}]
        got = []
        try:
            for piece in stream_text(bad):
                got.append(piece)
            assert False
        except StreamError as e:
            assert (str(e), e.kind, e.partial, got) == ("busy", "overloaded_error", "Refunds ", ["Refunds "])
        try:
            list(stream_text([{"type": "delta", "text": "Hi"}]))
            assert False
        except StreamError as e:
            assert e.kind == "incomplete" and e.partial == "Hi"
        assert list(stream_text([{"type": "stop"}, {"type": "delta", "text": "late"}])) == []
        """,
        hints=["Keep the pieces in a list as you yield them; `\"\".join(parts)` is the partial text.",
               "Use the `for` loop's `else` (it runs when the events run out) or a flag for the missing stop event."],
        solution="""
        class StreamError(Exception):
            def __init__(self, message, kind, partial):
                super().__init__(message)
                self.kind = kind
                self.partial = partial


        def stream_text(events):
            parts = []
            for event in events:
                kind = event.get("type")
                if kind == "delta":
                    parts.append(event["text"])
                    yield event["text"]
                elif kind == "stop":
                    return
                elif kind == "error":
                    err = event.get("error", {})
                    raise StreamError(err.get("message", "stream error"), err.get("type", "unknown"), "".join(parts))
            raise StreamError("stream ended early", "incomplete", "".join(parts))
        """,
        why="""In a stream, the HTTP status was 200 long before the problem, so the error arrives as data and must be turned into an exception
        by your code. Carrying the partial text on the exception lets the caller choose: show what arrived with a warning, retry the
        whole request, or ask the model to continue from where it stopped. The user has already seen those words, so silently discarding
        them is rarely right. A stream that ends without its stop event is also an error, typically a dropped connection, and treating it
        as a complete answer would pass off a truncated reply as finished. The event names follow Anthropic's streaming format; OpenAI's
        streams differ in detail but need the same handling."""),
    fix("Read the code: an agent loop", "hard", tag="GenAI",
        prompt="""`run_agent(model, tools, question, max_steps)` asks the model what to do; the model either answers or requests a tool
        call. Tool problems the model can fix (an unknown tool, wrong arguments, a `ToolError`) should be sent back to it as an error
        message; any other exception from a tool is a bug and must propagate. After `max_steps` model calls without an answer, raise
        `AgentError`. The current code can loop forever and feeds bugs to the model. Read it, find the bugs and fix them.""",
        code="""
        class ToolError(Exception):
            pass


        class AgentError(Exception):
            pass


        def run_agent(model, tools, question, max_steps=5):
            messages = [{"role": "user", "content": question}]
            while True:
                reply = model(messages)
                if reply["type"] == "answer":
                    return reply["text"]
                try:
                    result = tools[reply["tool"]](**reply["args"])
                    messages.append({"role": "tool", "content": str(result)})
                except Exception as e:
                    messages.append({"role": "tool", "content": f"error: {e}"})
        """,
        tests="""
        def scripted(*replies):
            seen = []
            def model(messages):
                seen.append(messages[-1]["content"])
                return replies[len(seen) - 1]
            return model, seen

        def search(query):
            if not query:
                raise ToolError("empty query")
            return ["doc1"]

        def broken(x):
            return x.missing_attribute

        tools = {"search": search, "broken": broken}
        model, seen = scripted({"type": "tool", "tool": "lookup", "args": {}},
                               {"type": "tool", "tool": "search", "args": {"q": "x"}},
                               {"type": "tool", "tool": "search", "args": {"query": ""}},
                               {"type": "tool", "tool": "search", "args": {"query": "refund"}},
                               {"type": "answer", "text": "5 days"})
        assert run_agent(model, tools, "refund time?") == "5 days"
        assert seen[1] == "error: unknown tool 'lookup'" and seen[2].startswith("error: bad arguments") and seen[3] == "error: empty query"
        assert seen[4] == "['doc1']"

        model, seen = scripted(*[{"type": "tool", "tool": "search", "args": {"query": "a"}}] * 10)
        try:
            run_agent(model, tools, "loop", max_steps=3)
            assert False
        except AgentError:
            assert len(seen) == 3

        model, _ = scripted({"type": "tool", "tool": "broken", "args": {"x": 1}})
        try:
            run_agent(model, tools, "bug")
            assert False
        except AttributeError:
            pass
        """,
        hints=["Replace `while True` with `for step in range(max_steps)` and raise `AgentError` after the loop.",
               "Check `reply[\"tool\"] in tools` before calling. Use `inspect.signature(fn).bind(**args)` to detect wrong arguments without calling (7.3).",
               "Catch only `ToolError` around the actual call."],
        solution="""
        import inspect


        class ToolError(Exception):
            pass


        class AgentError(Exception):
            pass


        def _tool_message(tools, name, args):
            fn = tools.get(name)
            if fn is None:
                return f"error: unknown tool {name!r}"
            try:
                inspect.signature(fn).bind(**args)
            except TypeError as e:
                return f"error: bad arguments for {name!r}: {e}"
            try:
                return str(fn(**args))
            except ToolError as e:
                return f"error: {e}"


        def run_agent(model, tools, question, max_steps=5):
            messages = [{"role": "user", "content": question}]
            for _ in range(max_steps):
                reply = model(messages)
                if reply["type"] == "answer":
                    return reply["text"]
                messages = messages + [{"role": "tool", "content": _tool_message(tools, reply["tool"], reply["args"])}]
            raise AgentError(f"no answer after {max_steps} steps")
        """,
        why="""Three bugs. **No step limit**: a model that keeps calling tools would loop forever, costing money on every iteration; agent loops
        always need a maximum number of steps (and usually a token or time budget too), with a specific error when it is reached.
        **`except Exception`**: the `AttributeError` inside `broken` is a bug in your tool, and feeding it to the model as "error: 'int'
        object has no attribute..." hides it from you and confuses the model. **Unhelpful messages**: an unknown tool produced
        `error: 'lookup'` (the `str` of a `KeyError`), which the model cannot act on. The fix separates the three model-fixable cases,
        each with a clear message, from everything else, which propagates. The helper also keeps `run_agent` short, and building a new
        `messages` list each step avoids changing a list the model function might still hold (2.4)."""),
    explain("How do you test error-handling code?", "medium", tag="Interview",
        why="""By making the failures happen on demand. Inject dependencies (the transport, `sleep`, `clock`, the random generator) so tests can
        pass fakes that raise specific exceptions on specific calls, return truncated or invalid output, or advance time instantly; then
        assert on behaviour: which exception reaches the caller (`pytest.raises(SomeError, match=...)`, 13.1), how many calls were made,
        which delays would have been waited, what was logged, and that data was left consistent. Test each class of failure separately:
        the expected ones (handled), the transient ones (retried, then raised), the permanent ones (not retried) and bugs (propagated).
        Test the boundaries too: zero attempts, deadlines exactly reached, empty batches. In larger systems, fault-injection tools and
        chaos testing deliberately break dependencies in staging, because fallbacks that are never exercised tend not to work."""),
    explain("What makes error handling for LLM and other remote APIs different from error handling in local code?", "hard", tag="Interview",
        why="""Local errors are mostly deterministic: the same input fails the same way, so they are bugs to fix. Remote calls add failures that
        depend on time and on systems you do not control: timeouts, dropped connections, rate limits and overload, which are transient and
        need retries with backoff, jitter and deadlines; and ambiguity, since after a timeout you do not know whether the work was done,
        which makes idempotency essential. LLMs add a further layer: a successful response can still be wrong for your purposes,
        truncated, refused, or not in the required format, so validation, repair loops and explicit checks of finish reasons are part of
        error handling. Costs and latency matter (every retry is paid for and slow), so budgets, circuit breakers and caching are part of
        the design. And observability becomes central: request ids, attempt counts, error types and latencies must be logged, because
        intermittent failures can only be diagnosed after the fact."""),
    predict("Everything at once", "hard",
        code="""
        import warnings

        class AppError(Exception): pass
        class RetryableError(AppError): pass

        def step(n):
            if n == 1:
                raise RetryableError("flaky")
            if n == 2:
                raise KeyError("bug")
            return n * 10

        results = []
        for n in [0, 1, 2, 3]:
            try:
                results.append(step(n))
            except AppError as e:
                results.append(type(e).__name__)
            except LookupError:
                results.append("lookup")
                continue
            finally:
                results.append(f"f{n}")
        print(results)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            warnings.warn("fallback used", RuntimeWarning)
        print(w[0].category.__name__, issubclass(RetryableError, Exception), isinstance(KeyError(), LookupError))
        """,
        hints=["`finally` runs even when the handler uses `continue`."],
        why="""For 0 and 3 the step succeeds and the result is appended, then the `finally` marker. For 1, the `RetryableError` is caught by the
        base-class handler, which appends the exact type name. For 2, the `KeyError` is a `LookupError`; its handler appends "lookup"
        and continues, but `finally` still runs first, so `f2` is recorded. The warning keeps its category, and both class checks are
        true."""),
)

section("project", "Mini project: a resilient JSON client",
    fig(flowchart({
        "send": ("start", 1, 0, "send the request"),
        "ok": ("ask", 1, 1, "request|succeeded?"),
        "valid": ("ask", 1, 2, "reply is|valid JSON?"),
        "ret": ("end", 1, 3, "return the data"),
        "trans": ("ask", 2, 1, "transient error and|attempts left?"),
        "wait": ("step", 2, 0, "wait (backoff)"),
        "fail": ("bad", 3, 1, "raise with context"),
        "repair": ("warn", 0, 2, "ask again with|the parse error"),
    }, [("send", "ok"), ("ok", "valid", "yes"), ("ok", "trans", "no"), ("trans", "wait", "yes"), ("wait", "send"),
        ("trans", "fail", "no"), ("valid", "ret", "yes"), ("valid", "repair", "no"), ("repair", "send", "", {"route": [(0, 0)]})],
        cell=(190, 82), label="the resilient JSON client's control flow"),
        "The client's flow: transient failures are retried with backoff, bad JSON is repaired by asking again, and anything else is raised with context."),
    p("""Your application needs structured answers from a model: a JSON object with specific keys. Two providers are available, a
    primary and a fallback. The client must retry transient failures with backoff, move on to the fallback when the primary keeps
    failing, repair invalid output by telling the model what was wrong, stop within a deadline, and raise clear, specific
    exceptions. All dependencies are injected so every behaviour can be tested instantly."""),
    write("Get valid JSON, reliably", "hard", key="resilient-client", tag="Project",
        prompt="""Implement `complete_json(prompt, providers, required, *, sleep, clock, rng, attempts=3, repairs=2, deadline=30.0,
        base=0.5)`.

        - `providers` is a list of `(name, call)`; `call(messages)` returns reply text or raises. Try them in order.
        - **Transient errors** (`TimeoutError`, `ConnectionError`, `RateLimitError`, `ServerError`) are retried on the same provider up
          to `attempts` calls in total, waiting `rng.uniform(0, base * 2 ** (n - 1))` before retry `n`, or the rate limit's
          `retry_after` if larger. Before any wait, if `clock() - start + wait > deadline`, raise `DeadlineError` from the last error.
          When a provider's attempts are used up, move to the next provider (no wait). If all fail, raise `UnavailableError` from the last
          error.
        - **`BadRequestError`** is permanent: re-raise it unchanged, immediately. Other exceptions propagate.
        - **Invalid output** (not a JSON object, or missing a `required` key): append the reply as an assistant message and a user message
          `"Invalid reply: <error>. Reply with only a JSON object with keys: <keys>."`, and call the **same** provider again, up to
          `repairs` times; repair calls do not count as transient attempts. When repairs run out, raise `InvalidOutputError` from the last
          error.
        - Return `(data, info)` where `info` is `{"provider": name, "calls": total calls made, "repairs": repairs used}`.

        The exception classes are defined for you; `LLMError` is the base of all of them. The caller's `messages` are never modified
        (the client builds them from `prompt`).""",
        code="""
        import json


        class LLMError(Exception):
            pass


        class RateLimitError(LLMError):
            def __init__(self, message, retry_after=None):
                super().__init__(message)
                self.retry_after = retry_after


        class ServerError(LLMError):
            pass


        class BadRequestError(LLMError):
            pass


        class UnavailableError(LLMError):
            pass


        class DeadlineError(LLMError):
            pass


        class InvalidOutputError(LLMError):
            pass


        def complete_json(prompt, providers, required, *, sleep, clock, rng, attempts=3, repairs=2, deadline=30.0, base=0.5):
            pass
        """,
        tests="""
        from types import SimpleNamespace
        top = SimpleNamespace(uniform=lambda a, b: b)
        now = [0.0]
        clock = lambda: now[0]
        waits = []
        def sleep(s):
            waits.append(s)
            now[0] += s

        def provider(*outcomes):
            log = []
            def call(messages):
                log.append([m["content"] for m in messages])
                out = outcomes[len(log) - 1]
                if isinstance(out, Exception):
                    raise out
                return out
            return call, log

        def reset():
            now[0] = 0.0
            waits.clear()

        # 1. transient errors, then a repair, on the primary
        reset()
        a, a_log = provider(TimeoutError("t"), RateLimitError("429", retry_after=3.0), '{"label": "spam"}', '{"label": "spam", "score": 0.9}')
        data, info = complete_json("classify", [("a", a)], ["label", "score"], sleep=sleep, clock=clock, rng=top)
        assert data == {"label": "spam", "score": 0.9} and info == {"provider": "a", "calls": 4, "repairs": 1}
        assert waits == [0.5, 3.0]
        assert a_log[3][-1] == "Invalid reply: missing keys: score. Reply with only a JSON object with keys: label, score."
        assert a_log[3][0] == "classify" and a_log[3][1] == '{"label": "spam"}'

        # 2. the primary is down, the fallback answers
        reset()
        a, _ = provider(ServerError("500"), ConnectionError("c"), TimeoutError("t"))
        b, b_log = provider('{"label": "ham", "score": 0.2}')
        data, info = complete_json("x", [("a", a), ("b", b)], ["label", "score"], sleep=sleep, clock=clock, rng=top)
        assert info == {"provider": "b", "calls": 4, "repairs": 0} and waits == [0.5, 1.0] and b_log == [["x"]]

        # 3. everything down
        reset()
        a, _ = provider(TimeoutError("a1"), TimeoutError("a2"))
        b, _ = provider(TimeoutError("b1"), TimeoutError("b2"))
        try:
            complete_json("x", [("a", a), ("b", b)], ["k"], sleep=sleep, clock=clock, rng=top, attempts=2)
            assert False
        except UnavailableError as e:
            assert str(e.__cause__) == "b2" and isinstance(e, LLMError)

        # 4. bad request is not retried, not failed over
        reset()
        a, a_log = provider(BadRequestError("400 too long"), "never")
        b, b_log = provider("never")
        try:
            complete_json("x", [("a", a), ("b", b)], ["k"], sleep=sleep, clock=clock, rng=top)
            assert False
        except BadRequestError as e:
            assert str(e) == "400 too long" and len(a_log) == 1 and b_log == []

        # 5. the deadline stops the waits
        reset()
        a, a_log = provider(RateLimitError("429", retry_after=20.0), RateLimitError("429", retry_after=20.0), "never")
        try:
            complete_json("x", [("a", a)], ["k"], sleep=sleep, clock=clock, rng=top, deadline=30.0)
            assert False
        except DeadlineError as e:
            assert waits == [20.0] and len(a_log) == 2 and isinstance(e.__cause__, RateLimitError)

        # 6. output that never becomes valid
        reset()
        a, a_log = provider("not json", "[1, 2]", "still not")
        try:
            complete_json("x", [("a", a)], ["k"], sleep=sleep, clock=clock, rng=top, repairs=2)
            assert False
        except InvalidOutputError as e:
            assert len(a_log) == 3 and isinstance(e.__cause__, ValueError) and waits == []

        # 7. a bug propagates
        reset()
        a, _ = provider(KeyError("bug"))
        try:
            complete_json("x", [("a", a)], ["k"], sleep=sleep, clock=clock, rng=top)
            assert False
        except KeyError:
            pass
        """,
        hints=["Split the work: a `_parse(reply, required)` that returns a dict or raises `ValueError`, and a loop per provider that counts transient attempts and repairs separately.",
               "Keep `messages` per provider, starting from `[{\"role\": \"user\", \"content\": prompt}]`, and extend it with `+` for repairs.",
               "For each provider: `while True:` call; on a transient error, count an attempt, and either wait (after the deadline check) or break to the next provider; on success, parse, and on `ValueError` either repair (`continue`) or raise `InvalidOutputError`.",
               "Track `calls` across providers, and the last transient error for the final `UnavailableError`."],
        solution="""
        import json


        class LLMError(Exception):
            pass


        class RateLimitError(LLMError):
            def __init__(self, message, retry_after=None):
                super().__init__(message)
                self.retry_after = retry_after


        class ServerError(LLMError):
            pass


        class BadRequestError(LLMError):
            pass


        class UnavailableError(LLMError):
            pass


        class DeadlineError(LLMError):
            pass


        class InvalidOutputError(LLMError):
            pass


        TRANSIENT = (TimeoutError, ConnectionError, RateLimitError, ServerError)


        def _parse(reply, required):
            data = json.loads(reply)
            if not isinstance(data, dict):
                raise ValueError("reply is not a JSON object")
            missing = [k for k in required if k not in data]
            if missing:
                raise ValueError(f"missing keys: {', '.join(missing)}")
            return data


        def complete_json(prompt, providers, required, *, sleep, clock, rng, attempts=3, repairs=2, deadline=30.0, base=0.5):
            start = clock()
            calls = 0
            last_transient = None
            for name, call in providers:
                messages = [{"role": "user", "content": prompt}]
                failures = 0
                repairs_used = 0
                while True:
                    calls += 1
                    try:
                        reply = call(messages)
                    except TRANSIENT as e:
                        last_transient = e
                        failures += 1
                        if failures >= attempts:
                            break
                        wait = rng.uniform(0, base * 2 ** (failures - 1))
                        wait = max(wait, getattr(e, "retry_after", None) or 0)
                        if clock() - start + wait > deadline:
                            raise DeadlineError(f"deadline of {deadline}s would be exceeded") from e
                        sleep(wait)
                        continue
                    try:
                        data = _parse(reply, required)
                    except ValueError as e:
                        if repairs_used >= repairs:
                            raise InvalidOutputError(f"invalid output from {name} after {repairs_used} repairs") from e
                        repairs_used += 1
                        messages = messages + [
                            {"role": "assistant", "content": reply},
                            {"role": "user", "content": f"Invalid reply: {e}. Reply with only a JSON object with keys: {', '.join(required)}."},
                        ]
                        continue
                    return data, {"provider": name, "calls": calls, "repairs": repairs_used}
            raise UnavailableError(f"all {len(providers)} providers failed") from last_transient
        """,
        why="""Every lesson of the module has a job here:

        - **try / except / else (7.1):** two separate `try` blocks keep the call and the parsing apart, so a transient network error and an
          invalid reply can never be confused, and `BadRequestError`, being neither transient nor a `ValueError`, propagates untouched,
          as does the `KeyError` bug.
        - **Custom exceptions and chaining (7.2):** one `LLMError` base lets callers catch everything from the client, while
          `UnavailableError`, `DeadlineError` and `InvalidOutputError` tell them **why** it failed; each is raised `from` the last
          underlying error, so the details survive in `__cause__`.
        - **Design (7.3):** the fallback provider is used only after transient failures, never for bad requests or bugs; `info`
          records which provider answered and how many repairs were needed, so degradation is measurable; and the conversation is
          rebuilt with `+`, never modifying shared state.
        - **API errors (7.4):** exponential backoff with injected jitter, `Retry-After` taking precedence, a deadline checked before
          every wait, no wait before failing over, and a repair loop that shows the model its invalid reply and the exact error.

        Injecting `sleep`, `clock` and `rng` is what made seven scenarios testable in milliseconds. In production you would pass
        `time.sleep`, `time.monotonic` and `random.Random()`, add logging of each attempt (7.4), and possibly a circuit breaker per
        provider (7.3). Module 8 turns the retry part into a reusable decorator."""),
)

recap(
    "Handle each error where something useful can be done; everywhere else, let it pass untouched.",
    "Classify by reaction: expected, transient (retry with backoff, jitter and a deadline), permanent (raise), bug (propagate).",
    "Keep the evidence: bare `raise`, `raise ... from`, notes, attributes on custom exceptions, and one log entry with the traceback.",
    "Keep data consistent and operations safe to repeat: build new then swap, idempotency keys created once.",
    "Inject time, randomness and transports so every failure path can be tested.",
)
