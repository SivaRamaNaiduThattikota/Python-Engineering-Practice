from lesson import *
from diagrams import *

lesson(
    id="m13-3", num="13.3", title="Mocking",
    intro="Code that calls a model API, a database, the clock or the network cannot be unit-tested by calling the real thing: it is "
          "slow, costs money, needs keys and gives different answers each time. Test doubles replace those dependencies. "
          "`unittest.mock` from the ground up (`Mock`, `return_value`, `side_effect`, call assertions, `spec` and autospec), `patch` "
          "and where to patch, fakes and injected dependencies, and the ways mocking goes wrong.",
    desc="`unittest.mock`, `patch`, fakes, stubs and spies, and where to patch.",
    keys="mock unittest.mock Mock MagicMock return_value side_effect assert_called_once_with call_args call_args_list call_count spec autospec create_autospec patch patch.object patch.dict monkeypatch fake stub spy dependency injection clock",
)

term("Test double", "Any object that stands in for a real dependency in a test: a stub, a fake, a mock or a spy.")
term("Mock", "A test double that records how it was called, so the test can check the calls; `unittest.mock.Mock` creates attributes and return values on demand.")
term("Fake", "A small working implementation of a dependency, such as an in-memory store or a scripted model client, used instead of the real one in tests.")

section("doubles", "Why test doubles, and which kind",
    fig(table(["double", "what it does", "use it to check"], [
        ["stub", "returns canned answers", "what your code returns"],
        ["fake", "a small working version (dict store)", "what your code returns"],
        ["mock", "records every call", "how a dependency was called"],
        ["spy", "wraps the real object, records calls", "calls, with real behaviour"],
    ], label="kinds of test double"),
        "Pick the double by what the test is about: results need stubs or fakes, interactions need mocks."),
    p("""A unit test should be fast, deterministic and free. Calls to an LLM API, a vector database, an HTTP service, the system clock or a random generator are none
    of those, so tests replace them with **test doubles**. The vocabulary helps when discussing designs. A **stub** returns canned answers ("the model always
    replies `spam`"). A **fake** is a simple working implementation (a dict-backed store, a scripted chat model). A **mock** records calls so the test can
    assert **how** the dependency was used ("called once with `max_tokens=200`"). A **spy** wraps the real object and records calls while still doing the real
    work."""),
    p("""Choose by what the test is about. To check **what your code returns** given certain dependency behaviour, stubs and fakes are enough and keep tests
    robust. To check **what your code does to the outside world** (sends one e-mail, retries three times, passes the right parameters to the API), assert on the
    calls of a mock. Asserting on every internal call of everything couples tests to implementation details, so a refactor breaks them although behaviour did
    not change (problem 13)."""),
)

section("mock", "`Mock`: return values, side effects and call records",
    p("""`unittest.mock.Mock()` creates an object that accepts any attribute access and any call: `m.complete("hi")` returns another `Mock`, and every call is
    recorded. Configure behaviour with **`return_value`** (what calling returns) and **`side_effect`**: an exception class or instance to raise, an iterable to
    return (or raise) one item per call, or a function whose result is returned. Inspect with `called`, `call_count`, `call_args` (the last call, as a `call(...)`
    object), `call_args_list` (all calls) and `mock_calls` (including calls on child attributes), or assert with **`assert_called_once_with(...)`**,
    `assert_called_with(...)` (the **last** call only), `assert_any_call(...)`, `assert_has_calls([...])` and `assert_not_called()`."""),
    ex("""
    from unittest.mock import Mock, call

    llm = Mock()
    llm.complete.return_value = "spam"
    print(llm.complete("Classify: WIN A PRIZE", max_tokens=5), llm.complete.call_count)
    llm.complete("second", max_tokens=5)
    print(llm.complete.call_args, llm.complete.call_args_list == [call("Classify: WIN A PRIZE", max_tokens=5), call("second", max_tokens=5)])
    llm.complete.assert_called_with("second", max_tokens=5)
    try:
        llm.complete.assert_called_once_with("second", max_tokens=5)
    except AssertionError as e:
        print("AssertionError:", str(e).splitlines()[0])

    flaky = Mock(side_effect=[TimeoutError("slow"), "ok"])
    for _ in range(2):
        try:
            print(flaky())
        except TimeoutError as e:
            print("raised", e)
    print(type(llm.anything.you.like).__name__)
    """, "mock_basics.py"),
    p("""The last line shows the danger: a bare `Mock` accepts **any** attribute, so if the real client's method is `complete` and your code calls `compelte`, the
    test still passes. **`Mock(spec=RealClass)`** (or `create_autospec(RealClass)`) restricts the mock to the real API: unknown attributes raise
    `AttributeError`, and with autospec, calls with the wrong arguments raise `TypeError` just as the real methods would (problems 3 and 14). `MagicMock`
    additionally supports magic methods such as `len()`, iteration and `with`."""),
)

section("patch", "`patch` and where to patch",
    fig(refs(["weather.fetch", "app.fetch"], ["real fetch", "Mock()"], [(0, 1), (1, 0)], label="from weather import fetch, then patch('weather.fetch')",
        title_names="names", title_objects="objects"),
        "After `from weather import fetch`, `app` has its own name; patching `weather.fetch` leaves `app.fetch` on the real function, so patch `app.fetch`."),
    p("""When code creates or imports its dependency itself instead of receiving it, the test must replace it in place. **`unittest.mock.patch("module.name",
    new=...)`** replaces the attribute `name` of `module` for the duration of a `with` block or a decorated test, and restores it afterwards; `patch.object(obj,
    "attr")` does the same for an object you already hold, and `patch.dict(os.environ, {...})` for dictionary entries. pytest's `monkeypatch.setattr` (13.2)
    is the fixture-based equivalent."""),
    p("""The rule that trips everyone: **patch where the name is looked up, not where it is defined.** If `app.py` does `from weather import fetch`, then `app` has its
    own name `fetch` bound to the function at import time; patching `weather.fetch` changes the `weather` module's attribute, but `app.fetch` still points to the
    original. Patch `app.fetch` instead, or have `app` do `import weather` and call `weather.fetch(...)`, which looks the name up at call time (problem 10)."""),
    ex("""
    from lessontools import run_pytest

    WEATHER = '''
    def fetch(city):
        raise RuntimeError("network access in a test!")
    '''
    APP = '''
    from weather import fetch

    def headline(city):
        return f"{city}: {fetch(city)['temp']} C"
    '''
    SRC = '''
    from unittest.mock import patch
    import app

    def test_patch_definition():
        with patch("weather.fetch", return_value={"temp": 21}):
            assert app.headline("Oslo") == "Oslo: 21 C"

    def test_patch_lookup():
        with patch("app.fetch", return_value={"temp": 21}) as fake:
            assert app.headline("Oslo") == "Oslo: 21 C"
        fake.assert_called_once_with("Oslo")
    '''
    r = run_pytest(SRC, {"weather": WEATHER, "app": APP})
    print(r["outcomes"])
    """, "where_to_patch.py"),
)

section("fakes", "Prefer injected fakes",
    p("""Patching is a workaround for code that hides its dependencies. The cleaner design passes them in: `def summarise(text, client):` or a class that receives its
    client in `__init__`, with a sensible default in production. Then a test passes a **fake**, no patching needed, and the code documents what it depends on.
    The same applies to time (`clock=time.monotonic` as a parameter, or an injected `now()` function), randomness (`rng=random.Random(seed)`), sleeping
    (`sleep=time.sleep`, so retry tests do not actually wait) and file locations (12.1). Fakes are reusable across tests and can model behaviour a stub
    cannot, such as "the store returns what was added", and they keep tests about outcomes rather than calls."""),
    ex("""
    class FakeClock:
        def __init__(self, start=0.0):
            self.now = start
        def __call__(self):
            return self.now
        def advance(self, seconds):
            self.now += seconds

    class TTLCache:
        def __init__(self, ttl, clock):
            self.ttl, self.clock, self._data = ttl, clock, {}
        def set(self, key, value):
            self._data[key] = (value, self.clock() + self.ttl)
        def get(self, key):
            value, expires = self._data.get(key, (None, 0))
            return value if self.clock() < expires else None

    clock = FakeClock()
    cache = TTLCache(ttl=60, clock=clock)
    cache.set("answer:refunds", "5 days")
    clock.advance(59.9)
    print(cache.get("answer:refunds"))
    clock.advance(0.1)
    print(cache.get("answer:refunds"))
    """, "fake_clock.py"),
    p("""Testing the expiry with the real clock would mean sleeping for a minute, or a flaky test with a tiny TTL; the fake clock makes it instant and exact, down to
    the boundary."""),
)

section("pitfalls", "How mocking goes wrong",
    p("""**Mocks that drift from reality:** a mock configured to return a dict when the real client returns an object, or accepting a parameter the real API
    renamed, passes while production fails; use `spec`/autospec, and keep a few integration tests against the real thing (13.4). **Over-mocking:** patching the
    function under test's own helpers, or asserting every internal call, tests the implementation instead of the behaviour, so the test passes for wrong code
    and fails for correct refactors. **Mocking what you don't own:** sprinkling patches of a third-party SDK through many tests ties them to its internals;
    wrap the SDK in a small adapter class of your own (`LLMClient.complete(prompt) -> str`), mock or fake the adapter in unit tests, and test the adapter itself
    against the real SDK separately. **Asserting the wrong call:** `assert_called_with` checks only the last call, so it misses problems in earlier ones
    (problem 7)."""),
)

section("warmup", "Warm-up",
    predict("Mocks record everything", "easy",
        code="""
        from unittest.mock import Mock, call

        client = Mock()
        client.embed.return_value = [0.1, 0.2]
        print(client.embed(["refunds"]), client.embed.called, client.search.called)
        client.search("refunds", k=3)
        client.search("shipping", k=5)
        print(client.search.call_count, client.search.call_args)
        print(client.search.call_args.args, client.search.call_args.kwargs)
        print(client.mock_calls[0], len(client.mock_calls))
        print(client.search.call_args_list[0] == call("refunds", k=3), client.search("x") is client.search("y"))
        """,
        hints=["A `Mock` creates child mocks on first attribute access; calling one returns the same `return_value` mock each time."],
        why="""`embed` returns its configured value; `search` exists as soon as it is accessed, but has not been called yet. After two calls, `call_args` is the last call,
        which unpacks into positional `args` and keyword `kwargs`. `mock_calls` on the parent records calls made on all its children in order, here three.
        Calling an unconfigured child mock always returns the **same** child, its `return_value`, so the two results are identical."""),
    write("Test a summariser with a mock client", "easy", tag="GenAI",
        prompt="""`summarise(client, text, max_words=50)` builds a prompt that contains the text and the word limit, calls `client.complete(prompt, max_tokens=max_words * 2)`
        once, and returns the reply stripped; it raises `ValueError` without calling the client when the text is blank. Write at least four tests with a mock
        client (use `Mock(spec=LLMClient)`) that pass here and catch four buggy versions.""",
        code="""
        # --- code under test (do not edit) ---
        class LLMClient:
            def complete(self, prompt, max_tokens):
                raise NotImplementedError("real API call")


        def summarise(client, text, max_words=50):
            if not text.strip():
                raise ValueError("nothing to summarise")
            prompt = f"Summarise in at most {max_words} words:\\n\\n{text}"
            return client.complete(prompt, max_tokens=max_words * 2).strip()


        # --- tests ---
        import pytest
        from unittest.mock import Mock
        """,
        tests="""
        import pytest
        from lessontools import run_pytest, swap_impl
        good = run_pytest(__source__)
        assert good["failed"] == 0 and good["passed"] >= 4, good["output"][-800:]
        assert "spec=LLMClient" in __source__
        BASE = '''
        class LLMClient:
            def complete(self, prompt, max_tokens):
                raise NotImplementedError("real API call")


        def summarise(client, text, max_words=50):
            if not text.strip():
                raise ValueError("nothing to summarise")
            prompt = f"Summarise in at most {max_words} words:\\\\n\\\\n{text}"
            return client.complete(prompt, max_tokens=max_words * 2).strip()
        '''
        BUGS = {
            "fixed_tokens": BASE.replace("max_tokens=max_words * 2", "max_tokens=100"),
            "no_strip": BASE.replace(").strip()", ")"),
            "text_missing": BASE.replace("{max_words} words:\\\\n\\\\n{text}", "{max_words} words.").replace("words.\\"", "words.\\""),
            "calls_on_blank": BASE.replace('        raise ValueError("nothing to summarise")', '        client.complete("", max_tokens=1)\\n        raise ValueError("nothing to summarise")'),
        }
        assert all(b != BASE for b in BUGS.values()), [k for k, b in BUGS.items() if b == BASE]
        escaped = sorted(name for name, impl in BUGS.items() if run_pytest(swap_impl(__source__, impl))["failed"] == 0)
        assert escaped == []
        """,
        hints=["`client = Mock(spec=LLMClient)`, `client.complete.return_value = \"  A summary. \"`, then check the result and `client.complete.call_args`.",
               "`prompt, = client.complete.call_args.args` and `client.complete.call_args.kwargs[\"max_tokens\"]`; for blank text, `client.complete.assert_not_called()`."],
        solution="""
        # --- code under test (do not edit) ---
        class LLMClient:
            def complete(self, prompt, max_tokens):
                raise NotImplementedError("real API call")


        def summarise(client, text, max_words=50):
            if not text.strip():
                raise ValueError("nothing to summarise")
            prompt = f"Summarise in at most {max_words} words:\\n\\n{text}"
            return client.complete(prompt, max_tokens=max_words * 2).strip()


        # --- tests ---
        import pytest
        from unittest.mock import Mock


        @pytest.fixture
        def client():
            c = Mock(spec=LLMClient)
            c.complete.return_value = "  Refunds take five days.\\n"
            return c


        def test_returns_stripped_reply(client):
            assert summarise(client, "Long refund policy text") == "Refunds take five days."


        def test_calls_client_once_with_token_budget(client):
            summarise(client, "Long refund policy text", max_words=30)
            client.complete.assert_called_once()
            assert client.complete.call_args.kwargs == {"max_tokens": 60}


        def test_prompt_contains_text_and_limit(client):
            summarise(client, "Refunds take five business days.", max_words=20)
            prompt = client.complete.call_args.args[0]
            assert "Refunds take five business days." in prompt and "20 words" in prompt


        def test_blank_text_raises_without_calling(client):
            with pytest.raises(ValueError):
                summarise(client, "   ")
            client.complete.assert_not_called()
        """,
        why="""The mock stands in for the API, returns a canned reply with whitespace (so stripping is visible), and records the call, which lets the tests check the two
        things that matter about the interaction: **what was sent** (the prompt contains the text and the limit, the token budget is derived from `max_words`)
        and **how often** (once, and not at all for blank input, which would waste money). `spec=LLMClient` makes the mock refuse methods the real client does not
        have. Note what the tests do not check: the exact prompt wording, which can change freely without breaking them."""),
    fix("A mock that hides an API mismatch", "easy", tag="GenAI",
        prompt="""The real `SearchClient` has a method `query(text, top_k)`. The tests use a bare `Mock()`, so they would still pass if the code called a method that does not
        exist, which is exactly what the graded buggy version does (`client.search(...)`). Make the tests catch it by giving the mock the real interface, and
        keep checking the arguments.""",
        code="""
        # --- code under test (do not edit) ---
        class SearchClient:
            def query(self, text, top_k):
                raise NotImplementedError("real vector database")


        def top_sources(client, question, k=3):
            hits = client.query(question, top_k=k)
            return [h["source"] for h in hits]


        # --- tests ---
        from unittest.mock import Mock


        def test_top_sources():
            client = Mock()
            client.query.return_value = [{"source": "faq.md"}, {"source": "terms.md"}]
            assert top_sources(client, "refunds?", k=2) == ["faq.md", "terms.md"]
        """,
        tests="""
        import pytest
        from lessontools import run_pytest, swap_impl
        good = run_pytest(__source__)
        assert good["failed"] == 0 and good["passed"] >= 1, good["output"][-800:]
        BUG = '''
        class SearchClient:
            def query(self, text, top_k):
                raise NotImplementedError("real vector database")


        def top_sources(client, question, k=3):
            hits = client.search(question, top_k=k)
            return [h["source"] for h in hits]
        '''
        BUG2 = '''
        class SearchClient:
            def query(self, text, top_k):
                raise NotImplementedError("real vector database")


        def top_sources(client, question, k=3):
            hits = client.query(question, k=k)
            return [h["source"] for h in hits]
        '''
        assert run_pytest(swap_impl(__source__, BUG))["failed"] > 0
        assert run_pytest(swap_impl(__source__, BUG2))["failed"] > 0
        """,
        hints=["`create_autospec(SearchClient, instance=True)` checks both the method names and their signatures.",
               "The second buggy version passes `k=` instead of `top_k=`: autospec rejects an unknown keyword, or assert the call explicitly."],
        solution="""
        # --- code under test (do not edit) ---
        class SearchClient:
            def query(self, text, top_k):
                raise NotImplementedError("real vector database")


        def top_sources(client, question, k=3):
            hits = client.query(question, top_k=k)
            return [h["source"] for h in hits]


        # --- tests ---
        from unittest.mock import create_autospec


        def test_top_sources():
            client = create_autospec(SearchClient, instance=True)
            client.query.return_value = [{"source": "faq.md"}, {"source": "terms.md"}]
            assert top_sources(client, "refunds?", k=2) == ["faq.md", "terms.md"]
            client.query.assert_called_once_with("refunds?", top_k=2)
        """,
        why="""A bare `Mock` invents whatever the code asks for, so `client.search(...)` returned a new mock, and the test only failed by luck or not at all. With an
        autospec, the double has exactly the real class's methods **and signatures**: calling `search` raises `AttributeError`, and calling `query` with `k=` raises
        `TypeError` because the real method has no such parameter, the same errors production would hit. This is the cheapest protection against the main risk of
        mocking: tests passing against an API that does not exist."""),
    predict("The forms of side_effect", "easy",
        code="""
        from unittest.mock import Mock

        def show(m, *args):
            try:
                return repr(m(*args))
            except Exception as e:
                return f"{type(e).__name__}: {e}"

        a = Mock(side_effect=ConnectionError)
        b = Mock(side_effect=ConnectionError("reset by peer"))
        c = Mock(side_effect=["first", TimeoutError("slow"), "third"])
        d = Mock(side_effect=lambda text: text.upper(), return_value="ignored")
        print(show(a), "|", show(b))
        print([show(c) for _ in range(4)])
        print(show(d, "spam"), c.call_count)
        """,
        hints=["An exception class or instance is raised. An iterable yields one item per call, raising items that are exceptions. A function's result wins over `return_value`."],
        why="""A class is instantiated and raised with no message; an instance is raised as it is. An iterable gives successive results, raising those that are exceptions,
        and when exhausted the mock raises `StopIteration`, a common surprise when a test calls the mock more often than expected. A function in `side_effect` is
        called with the same arguments and its result is returned, so `return_value` is ignored. The failed and exhausted calls still count towards
        `call_count`."""),
)

section("medium", "Medium",
    write("Test retries with a mock sleep", "medium", tag="GenAI",
        prompt="""`call_with_backoff(fn, sleep, attempts=3, base=1.0)` calls `fn()`; on `TimeoutError` or `ConnectionError` it calls `sleep(base * 2 ** i)` (1, 2, 4, ...) and
        tries again, up to `attempts` calls in total, re-raising the last error without sleeping after the final attempt; any other exception propagates at once.
        Write at least four tests using `Mock` objects for `fn` and `sleep` that pass here and catch five buggy versions. No test may really sleep.""",
        code="""
        # --- code under test (do not edit) ---
        def call_with_backoff(fn, sleep, attempts=3, base=1.0):
            for i in range(attempts):
                try:
                    return fn()
                except (TimeoutError, ConnectionError):
                    if i == attempts - 1:
                        raise
                    sleep(base * 2 ** i)


        # --- tests ---
        import pytest
        from unittest.mock import Mock, call
        """,
        tests="""
        import pytest
        from lessontools import run_pytest, swap_impl
        good = run_pytest(__source__)
        assert good["failed"] == 0 and good["passed"] >= 4, good["output"][-800:]
        BASE = '''
        def call_with_backoff(fn, sleep, attempts=3, base=1.0):
            for i in range(attempts):
                try:
                    return fn()
                except (TimeoutError, ConnectionError):
                    if i == attempts - 1:
                        raise
                    sleep(base * 2 ** i)
        '''
        BUGS = {
            "linear": BASE.replace("base * 2 ** i", "base * (i + 1)"),
            "sleeps_after_last": BASE.replace("            if i == attempts - 1:\\n                raise\\n            sleep(base * 2 ** i)", "            sleep(base * 2 ** i)\\n            if i == attempts - 1:\\n                raise"),
            "retries_everything": BASE.replace("except (TimeoutError, ConnectionError):", "except Exception:"),
            "one_extra_attempt": BASE.replace("range(attempts)", "range(attempts + 1)").replace("i == attempts - 1", "i == attempts"),
            "swallows_last": BASE.replace("                raise\\n", "                return None\\n"),
        }
        assert all(b != BASE for b in BUGS.values()), [k for k, b in BUGS.items() if b == BASE]
        escaped = sorted(name for name, impl in BUGS.items() if run_pytest(swap_impl(__source__, impl))["failed"] == 0)
        assert escaped == []
        """,
        hints=["`fn = Mock(side_effect=[TimeoutError(), ConnectionError(), \"ok\"])` and `sleep = Mock()`; then compare `sleep.call_args_list` with `[call(1.0), call(2.0)]`.",
               "All failures: `pytest.raises`, then check `fn.call_count` and that only two sleeps happened. A `ValueError` must not be retried."],
        solution="""
        # --- code under test (do not edit) ---
        def call_with_backoff(fn, sleep, attempts=3, base=1.0):
            for i in range(attempts):
                try:
                    return fn()
                except (TimeoutError, ConnectionError):
                    if i == attempts - 1:
                        raise
                    sleep(base * 2 ** i)


        # --- tests ---
        import pytest
        from unittest.mock import Mock, call


        def test_succeeds_after_transient_errors_with_exponential_waits():
            fn = Mock(side_effect=[TimeoutError(), ConnectionError(), "ok"])
            sleep = Mock()
            assert call_with_backoff(fn, sleep, attempts=3, base=0.5) == "ok"
            assert sleep.call_args_list == [call(0.5), call(1.0)]


        def test_gives_up_after_attempts_without_final_sleep():
            fn = Mock(side_effect=TimeoutError("slow"))
            sleep = Mock()
            with pytest.raises(TimeoutError, match="slow"):
                call_with_backoff(fn, sleep, attempts=4)
            assert fn.call_count == 4
            assert sleep.call_args_list == [call(1.0), call(2.0), call(4.0)]


        def test_other_errors_are_not_retried():
            fn = Mock(side_effect=ValueError("bad request"))
            sleep = Mock()
            with pytest.raises(ValueError):
                call_with_backoff(fn, sleep)
            assert fn.call_count == 1
            sleep.assert_not_called()


        def test_first_success_does_not_sleep():
            fn = Mock(return_value=42)
            sleep = Mock()
            assert call_with_backoff(fn, sleep) == 42
            sleep.assert_not_called()
        """,
        why="""Because `sleep` is a parameter, the test passes a `Mock` and the "waiting" is just a recorded call, so a test of a 7-second backoff runs in microseconds and the
        waits themselves become checkable values. `side_effect` with a list scripts the dependency's behaviour call by call (two transient failures, then
        success). The assertions pin the observable contract: the exact wait sequence (exponential, not linear, which needs at least three waits, since 1 then 2 starts both sequences), no pointless sleep after the last attempt,
        the exact number of calls, the error re-raised, and non-transient errors not retried, which matters for LLM APIs where a 400 "bad request" will never
        succeed on retry while a 429 or timeout might."""),
    write("Test a TTL cache with a fake clock", "medium", tag="Data work",
        prompt="""`TTLCache(ttl, clock)` stores values with an expiry time `clock() + ttl`; `get` returns the value while `clock()` is strictly before the expiry and `None`
        afterwards, deleting expired entries; `set` on an existing key refreshes its expiry; `len` counts live entries only. Write a `FakeClock` (or use a list
        and a lambda) and at least four tests that pass here and catch four buggy versions, without any real waiting.""",
        code="""
        # --- code under test (do not edit) ---
        class TTLCache:
            def __init__(self, ttl, clock):
                self.ttl, self.clock, self._data = ttl, clock, {}

            def set(self, key, value):
                self._data[key] = (value, self.clock() + self.ttl)

            def get(self, key):
                if key not in self._data:
                    return None
                value, expires = self._data[key]
                if self.clock() >= expires:
                    del self._data[key]
                    return None
                return value

            def __len__(self):
                now = self.clock()
                return sum(1 for _, expires in self._data.values() if now < expires)


        # --- tests ---
        import pytest
        """,
        tests="""
        import pytest
        from lessontools import run_pytest, swap_impl
        good = run_pytest(__source__)
        assert good["failed"] == 0 and good["passed"] >= 4, good["output"][-800:]
        assert "sleep" not in __source__.split("# --- tests")[1]
        BASE = __source__.split("# --- code under test (do not edit) ---")[1].split("# --- tests")[0]
        BUGS = {
            "inclusive_expiry": BASE.replace("if self.clock() >= expires:", "if self.clock() > expires:"),
            "no_refresh": BASE.replace("        self._data[key] = (value, self.clock() + self.ttl)", "        self._data.setdefault(key, (value, self.clock() + self.ttl))"),
            "len_counts_expired": BASE.replace("if now < expires)", ")"),
            "ttl_ignored": BASE.replace("self.clock() + self.ttl)", "self.clock() + 60)"),
        }
        assert all(b != BASE for b in BUGS.values()), [k for k, b in BUGS.items() if b == BASE]
        escaped = sorted(name for name, impl in BUGS.items() if run_pytest(swap_impl(__source__, impl))["failed"] == 0)
        assert escaped == []
        """,
        hints=["A fake clock: `now = [0.0]` and `clock = lambda: now[0]`; advance with `now[0] += 10`. Or a small class with `__call__` and `advance`.",
               "Test exactly at the boundary (`ttl` seconds later), refreshing with a second `set`, `len` after expiry, and a ttl other than 60."],
        solution="""
        # --- code under test (do not edit) ---
        class TTLCache:
            def __init__(self, ttl, clock):
                self.ttl, self.clock, self._data = ttl, clock, {}

            def set(self, key, value):
                self._data[key] = (value, self.clock() + self.ttl)

            def get(self, key):
                if key not in self._data:
                    return None
                value, expires = self._data[key]
                if self.clock() >= expires:
                    del self._data[key]
                    return None
                return value

            def __len__(self):
                now = self.clock()
                return sum(1 for _, expires in self._data.values() if now < expires)


        # --- tests ---
        import pytest


        class FakeClock:
            def __init__(self):
                self.now = 1000.0

            def __call__(self):
                return self.now

            def advance(self, seconds):
                self.now += seconds


        @pytest.fixture
        def clock():
            return FakeClock()


        @pytest.fixture
        def cache(clock):
            return TTLCache(ttl=30, clock=clock)


        def test_value_available_until_just_before_expiry(cache, clock):
            cache.set("q", "5 days")
            clock.advance(29.999)
            assert cache.get("q") == "5 days"


        def test_expires_exactly_at_ttl(cache, clock):
            cache.set("q", "5 days")
            clock.advance(30)
            assert cache.get("q") is None


        def test_set_refreshes_expiry(cache, clock):
            cache.set("q", "old")
            clock.advance(20)
            cache.set("q", "new")
            clock.advance(20)
            assert cache.get("q") == "new"


        def test_len_counts_only_live_entries(cache, clock):
            cache.set("a", 1)
            clock.advance(15)
            cache.set("b", 2)
            clock.advance(20)
            assert len(cache) == 1


        def test_missing_key(cache):
            assert cache.get("nope") is None
        """,
        why="""Injecting the clock turns time into test data: the fake starts at an arbitrary instant, and `advance` moves it by exact amounts, so the boundary (29.999 versus
        30 seconds) can be tested precisely, which no test using real time could do reliably. The fixtures compose: `cache` asks for the same `clock` instance the
        test receives, so the test controls the cache's notion of now. The cases mirror the specification: strictly-before semantics at the boundary, refresh on
        overwrite, live-only counting, and a TTL other than the mutant's hard-coded 60. Caches of LLM answers and embeddings rely on exactly this logic."""),
    fix("Checking only the last call", "medium", tag="GenAI",
        prompt="""`fetch_all(client, ids)` must call `client.get(id, timeout=5)` for **every** id. The test uses `assert_called_with`, which only checks the **last** call, so the
        graded buggy version (which forgets the timeout on all but the last request) passes. Fix the test to check every call, in order.""",
        code="""
        # --- code under test (do not edit) ---
        def fetch_all(client, ids):
            return [client.get(i, timeout=5) for i in ids]


        # --- tests ---
        from unittest.mock import Mock


        def test_fetch_all_uses_timeout():
            client = Mock()
            client.get.side_effect = lambda i, timeout=None: {"id": i}
            assert fetch_all(client, ["a", "b", "c"]) == [{"id": "a"}, {"id": "b"}, {"id": "c"}]
            client.get.assert_called_with("c", timeout=5)
        """,
        tests="""
        import pytest
        from lessontools import run_pytest, swap_impl
        good = run_pytest(__source__)
        assert good["failed"] == 0 and good["passed"] >= 1, good["output"][-800:]
        BUG = '''
        def fetch_all(client, ids):
            out = [client.get(i) for i in ids[:-1]]
            if ids:
                out.append(client.get(ids[-1], timeout=5))
            return out
        '''
        assert run_pytest(swap_impl(__source__, BUG))["failed"] > 0
        """,
        hints=["Compare `client.get.call_args_list` with `[call(\"a\", timeout=5), call(\"b\", timeout=5), call(\"c\", timeout=5)]`, or use `assert_has_calls`."],
        solution="""
        # --- code under test (do not edit) ---
        def fetch_all(client, ids):
            return [client.get(i, timeout=5) for i in ids]


        # --- tests ---
        from unittest.mock import Mock, call


        def test_fetch_all_uses_timeout():
            client = Mock()
            client.get.side_effect = lambda i, timeout=None: {"id": i}
            assert fetch_all(client, ["a", "b", "c"]) == [{"id": "a"}, {"id": "b"}, {"id": "c"}]
            assert client.get.call_args_list == [call("a", timeout=5), call("b", timeout=5), call("c", timeout=5)]
        """,
        why="""`assert_called_with` compares only `call_args`, the most recent call, so any mistake in earlier calls is invisible; its name invites exactly this misuse. Comparing
        `call_args_list` with the full expected list checks every call, their order and their count. `assert_has_calls(calls)` checks that the calls appear as a
        consecutive sequence (in any surrounding context), and `assert_any_call` that at least one matches; choose the one that states what you mean. Missing
        timeouts are a real production issue: one request without a timeout can hang a worker indefinitely."""),
    trace("Reading a mock's records", "medium",
        prompt="Fill in `count` and `last` after each marked line.",
        code="""
        from unittest.mock import Mock

        tool = Mock(return_value="42")
        tool("2 * 21")
        count, last = tool.call_count, tool.call_args.args  # row: "one call"
        tool("6 * 7", precision=0)
        count, last = tool.call_count, tool.call_args.kwargs  # row: "with a keyword"
        tool.reset_mock()
        count, last = tool.call_count, tool.call_args  # row: "after reset"
        tool.side_effect = KeyError("unknown")
        try:
            tool("bad")
        except KeyError:
            pass
        count, last = tool.call_count, tool.return_value  # row: "after a raising call"
        """,
        trace_vars=["count", "last"],
        hints=["`reset_mock` clears the call records but keeps the configured `return_value`. A call that raises is still recorded."],
        why="""Every call is recorded with its positional and keyword arguments. `reset_mock()` clears the history, so `call_args` becomes `None`, but keeps configuration
        such as `return_value` (pass `return_value=True` to clear it too), which is useful when one mock is reused across phases of a test. A call that raises
        through `side_effect` still counts, which is how tests verify that a failing dependency was tried exactly once."""),
    write("Test a RAG answer function with fakes", "medium", tag="RAG",
        prompt="""`answer(question, retriever, llm, k=3)` retrieves `k` chunks; if there are none it returns `"I don't know."` **without calling the model**; otherwise it
        builds a prompt listing each chunk as `[source] text`, calls `llm(prompt)`, and returns `{"answer": reply, "sources": [...]}` with the unique sources in
        retrieval order. Write a small fake retriever class and use a `Mock` for `llm`; at least four tests must pass here and catch five buggy versions.""",
        code="""
        # --- code under test (do not edit) ---
        def answer(question, retriever, llm, k=3):
            chunks = retriever.retrieve(question, k=k)
            if not chunks:
                return {"answer": "I don't know.", "sources": []}
            context = "\\n".join(f"[{c['source']}] {c['text']}" for c in chunks)
            reply = llm(f"Answer using only the context.\\n{context}\\n\\nQuestion: {question}")
            sources = list(dict.fromkeys(c["source"] for c in chunks))
            return {"answer": reply, "sources": sources}


        # --- tests ---
        import pytest
        from unittest.mock import Mock
        """,
        tests="""
        import pytest
        from lessontools import run_pytest, swap_impl
        good = run_pytest(__source__)
        assert good["failed"] == 0 and good["passed"] >= 4, good["output"][-800:]
        BASE = __source__.split("# --- code under test (do not edit) ---")[1].split("# --- tests")[0]
        BUGS = {
            "calls_llm_without_context": BASE.replace('    if not chunks:\\n        return {"answer": "I don\\'t know.", "sources": []}\\n', ""),
            "ignores_k": BASE.replace("retriever.retrieve(question, k=k)", "retriever.retrieve(question, k=3)"),
            "sorted_sources": BASE.replace("list(dict.fromkeys(c[\\"source\\"] for c in chunks))", "sorted(set(c[\\"source\\"] for c in chunks))"),
            "duplicate_sources": BASE.replace("list(dict.fromkeys(c[\\"source\\"] for c in chunks))", "[c[\\"source\\"] for c in chunks]"),
            "question_missing": BASE.replace("\\\\n\\\\nQuestion: {question}", ""),
        }
        assert all(b != BASE for b in BUGS.values()), [k for k, b in BUGS.items() if b == BASE]
        escaped = sorted(name for name, impl in BUGS.items() if run_pytest(swap_impl(__source__, impl))["failed"] == 0)
        assert escaped == []
        """,
        hints=["A fake retriever: `class FakeRetriever: def __init__(self, chunks): ...; def retrieve(self, question, k): self.calls.append((question, k)); return self.chunks[:k]`.",
               "Use sources in non-alphabetical order with a repeat (`terms.md`, `faq.md`, `terms.md`) to expose ordering and duplicate bugs."],
        solution="""
        # --- code under test (do not edit) ---
        def answer(question, retriever, llm, k=3):
            chunks = retriever.retrieve(question, k=k)
            if not chunks:
                return {"answer": "I don't know.", "sources": []}
            context = "\\n".join(f"[{c['source']}] {c['text']}" for c in chunks)
            reply = llm(f"Answer using only the context.\\n{context}\\n\\nQuestion: {question}")
            sources = list(dict.fromkeys(c["source"] for c in chunks))
            return {"answer": reply, "sources": sources}


        # --- tests ---
        import pytest
        from unittest.mock import Mock


        class FakeRetriever:
            def __init__(self, chunks):
                self.chunks = chunks
                self.calls = []

            def retrieve(self, question, k):
                self.calls.append((question, k))
                return self.chunks[:k]


        CHUNKS = [
            {"source": "terms.md", "text": "No refunds after 30 days."},
            {"source": "faq.md", "text": "Refunds take 5 days."},
            {"source": "terms.md", "text": "Refunds go to the original card."},
        ]


        def test_no_chunks_means_no_model_call():
            llm = Mock()
            assert answer("Refunds?", FakeRetriever([]), llm) == {"answer": "I don't know.", "sources": []}
            llm.assert_not_called()


        def test_prompt_contains_context_and_question():
            llm = Mock(return_value="5 days.")
            answer("How long do refunds take?", FakeRetriever(CHUNKS), llm)
            prompt = llm.call_args.args[0]
            assert "[faq.md] Refunds take 5 days." in prompt and "How long do refunds take?" in prompt


        def test_sources_unique_in_retrieval_order():
            llm = Mock(return_value="5 days.")
            result = answer("Refunds?", FakeRetriever(CHUNKS), llm)
            assert result == {"answer": "5 days.", "sources": ["terms.md", "faq.md"]}


        def test_passes_k_to_retriever():
            retriever = FakeRetriever(CHUNKS)
            answer("Refunds?", retriever, Mock(return_value="x"), k=2)
            assert retriever.calls == [("Refunds?", 2)]
        """,
        why="""Two kinds of double serve two purposes. The **fake** retriever behaves like a tiny real one (returns at most `k` chunks and remembers what it was asked), so
        tests can set up any retrieval result, including none. The **mock** model records the prompt, so tests can check what reaches the model, without depending
        on its exact wording, and can assert that no call is made when there is no context, the guard that prevents hallucinated answers and wasted tokens.
        Sources in deliberately unsorted order with a repeat expose both the sorting and the duplicate mutants; the citation order should follow relevance."""),
    predict("Patching the right name", "medium",
        code="""
        from lessontools import run_pytest

        SAMPLER = '''
        from random import random
        import random as rnd

        def keep_from_import(rate):
            return random() < rate

        def keep_module_lookup(rate):
            return rnd.random() < rate
        '''
        SRC = '''
        import random
        import sampler

        def test_patch_random_module_a(monkeypatch):
            monkeypatch.setattr(random, "random", lambda: -1.0)
            assert sampler.keep_module_lookup(0.0) is True

        def test_patch_random_module_b(monkeypatch):
            monkeypatch.setattr(random, "random", lambda: -1.0)
            assert sampler.keep_from_import(0.0) is True

        def test_patch_sampler_name(monkeypatch):
            monkeypatch.setattr(sampler, "random", lambda: -1.0)
            assert sampler.keep_from_import(0.0) is True
        '''
        r = run_pytest(SRC, {"sampler": SAMPLER})
        print(r["outcomes"])
        """,
        hints=["`from random import random` copies the function into `sampler`'s own namespace when the module is imported; `rnd.random()` looks the attribute up on every call.",
               "The fake returns -1.0, which the real `random()` (always in `[0, 1)`) never does, so each test passes only if the patch took effect."],
        why="""`keep_module_lookup` calls `rnd.random()`, which reads the attribute from the `random` module at call time, so patching the module works. `keep_from_import`
        uses its own global name `random`, bound to the original function when `sampler` was imported, so patching the `random` module has no effect: the real
        `random()` is never below 0, and the assert fails. Patching `sampler.random`, the name where it is looked up, works."""),
    write("A scripted fake LLM", "medium", tag="GenAI",
        prompt="""Write `FakeLLM(script)`, a fake model client for tests. `script` is a list of `(substring, reply)` pairs. `complete(prompt)` records the prompt in
        `self.prompts`, returns the reply of the **first** pair whose substring occurs in the prompt (a reply that is an exception instance is raised instead), and
        raises `AssertionError(f"unexpected prompt: {prompt[:40]!r}")` when nothing matches. Add `assert_all_used()`, raising `AssertionError` naming the
        substrings that never matched.""",
        code="""
        class FakeLLM:
            pass
        """,
        tests="""
        llm = FakeLLM([("Classify", "spam"), ("Summarise", "A short summary."), ("Translate", TimeoutError("model timed out"))])
        assert llm.complete("Classify: WIN A PRIZE") == "spam" and llm.complete("Classify: lunch?") == "spam"
        assert llm.complete("Please Summarise this") == "A short summary."
        try:
            llm.complete("Translate to French")
            assert False
        except TimeoutError as e:
            assert str(e) == "model timed out"
        try:
            llm.complete("Write a poem about refunds, a very long one")
            assert False
        except AssertionError as e:
            assert str(e) == "unexpected prompt: 'Write a poem about refunds, a very long '"
        assert len(llm.prompts) == 5
        unused = FakeLLM([("Classify", "spam"), ("Summarise", "x"), ("Rank", "1")])
        unused.complete("Classify this")
        try:
            unused.assert_all_used()
            assert False
        except AssertionError as e:
            assert "Summarise" in str(e) and "Rank" in str(e) and "Classify" not in str(e)
        llm.assert_all_used()
        """,
        hints=["Keep a set of substrings that matched; `assert_all_used` compares it with all substrings, in script order."],
        solution="""
        class FakeLLM:
            def __init__(self, script):
                self.script = list(script)
                self.prompts = []
                self._used = set()

            def complete(self, prompt):
                self.prompts.append(prompt)
                for substring, reply in self.script:
                    if substring in prompt:
                        self._used.add(substring)
                        if isinstance(reply, BaseException):
                            raise reply
                        return reply
                raise AssertionError(f"unexpected prompt: {prompt[:40]!r}")

            def assert_all_used(self):
                unused = [s for s, _ in self.script if s not in self._used]
                if unused:
                    raise AssertionError(f"script entries never used: {unused}")
        """,
        why="""A scripted fake is the workhorse for testing LLM-driven code: tests state which prompts to expect and what the "model" answers, including failures, and the
        fake checks the other direction too: an unexpected prompt fails loudly instead of returning a meaningless mock, and `assert_all_used` catches code paths
        that silently stopped calling the model. Matching on substrings rather than exact prompts keeps tests robust to wording changes while still pinning the
        important part. Libraries offer the same idea (LangChain's fake chat models, `respx` or `responses` for HTTP-level fakes, VCR-style cassettes that replay
        recorded responses); 13.4 uses this fake for an agent."""),
)

section("hard", "Hard",
    write("Test a tool-calling agent loop", "hard", tag="GenAI",
        prompt="""`run_agent(llm, tools, question, max_steps=4)` sends `messages` to `llm.next(messages)`, which returns either `{"tool": name, "args": {...}}` or `{"answer":
        text}`. For a tool call it runs `tools[name](**args)` and appends the result as a `{"role": "tool", "name": ..., "content": str(result)}` message; an unknown
        tool appends a `"tool"` message with content `"error: unknown tool NAME"`; an answer is returned. After `max_steps` model calls without an answer it raises
        `RuntimeError`. Write at least five tests with `Mock(side_effect=[...])` for the model and mocks for tools. They must pass here and catch five buggy versions.""",
        code="""
        # --- code under test (do not edit) ---
        def run_agent(llm, tools, question, max_steps=4):
            messages = [{"role": "user", "content": question}]
            for _ in range(max_steps):
                step = llm.next(list(messages))
                if "answer" in step:
                    return step["answer"]
                name = step["tool"]
                if name in tools:
                    content = str(tools[name](**step.get("args", {})))
                else:
                    content = f"error: unknown tool {name}"
                messages.append({"role": "tool", "name": name, "content": content})
            raise RuntimeError(f"no answer after {max_steps} steps")


        # --- tests ---
        import pytest
        from unittest.mock import Mock
        """,
        tests="""
        import pytest
        from lessontools import run_pytest, swap_impl
        good = run_pytest(__source__)
        assert good["failed"] == 0 and good["passed"] >= 5, good["output"][-800:]
        BASE = __source__.split("# --- code under test (do not edit) ---")[1].split("# --- tests")[0]
        BUGS = {
            "drops_args": BASE.replace("tools[name](**step.get(\\"args\\", {}))", "tools[name]()"),
            "unknown_tool_crashes": BASE.replace("        if name in tools:\\n            content = str(tools[name](**step.get(\\"args\\", {})))\\n        else:\\n            content = f\\"error: unknown tool {name}\\"\\n",
                                                 "        content = str(tools[name](**step.get(\\"args\\", {})))\\n"),
            "results_not_sent": BASE.replace("        messages.append({\\"role\\": \\"tool\\", \\"name\\": name, \\"content\\": content})\\n", ""),
            "off_by_one_steps": BASE.replace("for _ in range(max_steps):", "for _ in range(max_steps + 1):"),
            "returns_none": BASE.replace('    raise RuntimeError(f"no answer after {max_steps} steps")', "    return None"),
        }
        assert all(b != BASE for b in BUGS.values()), [k for k, b in BUGS.items() if b == BASE]
        escaped = sorted(name for name, impl in BUGS.items() if run_pytest(swap_impl(__source__, impl))["failed"] == 0)
        assert escaped == []
        """,
        hints=["`llm = Mock(); llm.next.side_effect = [{\"tool\": \"calc\", \"args\": {\"expr\": \"2*21\"}}, {\"answer\": \"42\"}]`, and `calc = Mock(return_value=42)`.",
               "The messages passed on the second model call are in `llm.next.call_args_list[1].args[0]`.",
               "For the step limit, make the model always ask for a tool (`side_effect` from a generator or a long list) and check `llm.next.call_count`."],
        solution="""
        # --- code under test (do not edit) ---
        def run_agent(llm, tools, question, max_steps=4):
            messages = [{"role": "user", "content": question}]
            for _ in range(max_steps):
                step = llm.next(list(messages))
                if "answer" in step:
                    return step["answer"]
                name = step["tool"]
                if name in tools:
                    content = str(tools[name](**step.get("args", {})))
                else:
                    content = f"error: unknown tool {name}"
                messages.append({"role": "tool", "name": name, "content": content})
            raise RuntimeError(f"no answer after {max_steps} steps")


        # --- tests ---
        import pytest
        from unittest.mock import Mock


        def model(*steps):
            llm = Mock()
            llm.next.side_effect = list(steps)
            return llm


        def test_direct_answer():
            llm = model({"answer": "Hello"})
            assert run_agent(llm, {}, "Hi") == "Hello"
            assert llm.next.call_args.args[0] == [{"role": "user", "content": "Hi"}]


        def test_tool_called_with_args_and_result_sent_back():
            calc = Mock(return_value=42)
            llm = model({"tool": "calc", "args": {"expr": "2*21"}}, {"answer": "It is 42."})
            assert run_agent(llm, {"calc": calc}, "What is 2*21?") == "It is 42."
            calc.assert_called_once_with(expr="2*21")
            second = llm.next.call_args_list[1].args[0]
            assert second[-1] == {"role": "tool", "name": "calc", "content": "42"}


        def test_unknown_tool_is_reported_to_the_model():
            llm = model({"tool": "browse"}, {"answer": "Sorry."})
            assert run_agent(llm, {}, "Look it up") == "Sorry."
            assert llm.next.call_args_list[1].args[0][-1]["content"] == "error: unknown tool browse"


        def test_stops_after_max_steps():
            search = Mock(return_value="nothing")
            llm = model(*[{"tool": "search", "args": {"q": "x"}}] * 10)
            with pytest.raises(RuntimeError, match="3 steps"):
                run_agent(llm, {"search": search}, "Loop forever", max_steps=3)
            assert llm.next.call_count == 3 and search.call_count == 3


        def test_messages_accumulate_in_order():
            lookup = Mock(side_effect=["A", "B"])
            llm = model({"tool": "lookup"}, {"tool": "lookup"}, {"answer": "done"})
            run_agent(llm, {"lookup": lookup}, "q")
            third = llm.next.call_args_list[2].args[0]
            assert [m["content"] for m in third] == ["q", "A", "B"]
        """,
        why="""The model is scripted step by step with `side_effect`, so each test drives the loop down one path: answer at once, one tool round trip, an unknown tool, a model
        that never stops, and several rounds. Because the code passes a **copy** of the messages on each call, `call_args_list` records exactly what the model saw at
        each step, which is what lets the tests check that tool results are fed back in order; if the code passed the same list object, every recorded call
        would show the final state, a classic trap when asserting on mutable arguments. The step-limit test protects against runaway agents that burn tokens,
        and checking the counts (exactly 3 model calls and 3 tool calls) catches the off-by-one."""),
    fix("Read the code: an over-mocked test suite", "hard", tag="ML",
        prompt="""These tests for `rank_candidates` patch the function's own helper `_score`, so they pass whatever the real scoring does, and they assert on private calls. The
        graded buggy versions break the scoring (wrong weights, reversed order, a missing tie-break) and all pass. Rewrite the tests to check **behaviour** through
        the public function only: no patching of `_score`, no assertions on private helpers. They must pass here and catch the bugs.""",
        code="""
        # --- code under test (do not edit) ---
        def _score(candidate):
            # 70% relevance, 30% freshness, both in [0, 1]
            return 0.7 * candidate["relevance"] + 0.3 * candidate["freshness"]


        def rank_candidates(candidates, k=3):
            ranked = sorted(candidates, key=lambda c: (-_score(c), c["id"]))
            return [c["id"] for c in ranked[:k]]


        # --- tests ---
        import sys
        from unittest.mock import patch


        def test_rank_uses_score():
            module = sys.modules[__name__]
            with patch.object(module, "_score", side_effect=lambda c: c["relevance"]) as fake:
                result = rank_candidates([{"id": "a", "relevance": 0.2, "freshness": 0}, {"id": "b", "relevance": 0.9, "freshness": 0}])
            assert result == ["b", "a"]
            assert fake.call_count == 2
        """,
        tests="""
        import pytest
        from lessontools import run_pytest, swap_impl
        tests_part = __source__.split("# --- tests")[1]
        good = run_pytest(__source__)
        assert good["failed"] == 0 and good["passed"] >= 3, good["output"][-800:]
        assert "patch" not in tests_part and "_score" not in tests_part
        BASE = __source__.split("# --- code under test (do not edit) ---")[1].split("# --- tests")[0]
        BUGS = {
            "weights_swapped": BASE.replace("0.7 * candidate[\\"relevance\\"] + 0.3 * candidate[\\"freshness\\"]", "0.3 * candidate[\\"relevance\\"] + 0.7 * candidate[\\"freshness\\"]"),
            "ascending": BASE.replace("key=lambda c: (-_score(c), c[\\"id\\"])", "key=lambda c: (_score(c), c[\\"id\\"])"),
            "no_tie_break": BASE.replace("key=lambda c: (-_score(c), c[\\"id\\"])", "key=lambda c: -_score(c)"),
            "ignores_k": BASE.replace("ranked[:k]", "ranked[:3]"),
        }
        assert all(b != BASE for b in BUGS.values()), [k for k, b in BUGS.items() if b == BASE]
        escaped = sorted(name for name, impl in BUGS.items() if run_pytest(swap_impl(__source__, impl))["failed"] == 0)
        assert escaped == []
        """,
        hints=["Choose candidates whose order depends on the weights: one high in relevance only, one high in freshness only.",
               "For the tie-break, two candidates with identical scores given in reverse id order; for `k`, ask for 1 and for 4."],
        solution="""
        # --- code under test (do not edit) ---
        def _score(candidate):
            # 70% relevance, 30% freshness, both in [0, 1]
            return 0.7 * candidate["relevance"] + 0.3 * candidate["freshness"]


        def rank_candidates(candidates, k=3):
            ranked = sorted(candidates, key=lambda c: (-_score(c), c["id"]))
            return [c["id"] for c in ranked[:k]]


        # --- tests ---
        import pytest


        def cand(id, relevance, freshness):
            return {"id": id, "relevance": relevance, "freshness": freshness}


        def test_relevance_weighs_more_than_freshness():
            relevant = cand("relevant", 0.9, 0.0)
            fresh = cand("fresh", 0.0, 1.0)
            assert rank_candidates([fresh, relevant]) == ["relevant", "fresh"]


        def test_best_first():
            items = [cand("low", 0.1, 0.1), cand("high", 1.0, 1.0), cand("mid", 0.5, 0.5)]
            assert rank_candidates(items) == ["high", "mid", "low"]


        def test_ties_broken_by_id():
            items = [cand("b", 0.5, 0.5), cand("a", 0.5, 0.5)]
            assert rank_candidates(items) == ["a", "b"]


        @pytest.mark.parametrize("k,expected", [(1, ["high"]), (4, ["high", "mid", "low"])])
        def test_k_limits_results(k, expected):
            items = [cand("low", 0.1, 0.1), cand("high", 1.0, 1.0), cand("mid", 0.5, 0.5)]
            assert rank_candidates(items, k=k) == expected
        """,
        why="""Patching the unit's own helper replaced the logic under test with the test's own idea of it, so the test verified only that `sorted` calls a key function, and
        asserting `call_count == 2` pinned an implementation detail that a harmless refactor (caching scores) would break. Mock **boundaries** (the network, the
        model, the clock), not your own pure code. The rewritten tests use inputs chosen so that the specification decides the order: a relevance-only candidate
        beats a freshness-only one only if relevance weighs more, identical scores reveal the tie-break, and `k` values below and above the list size pin the
        limit. Each is a statement about what users of the function can rely on."""),
    predict("spec, autospec and MagicMock", "hard",
        code="""
        from unittest.mock import MagicMock, Mock, create_autospec

        class Embedder:
            dim = 384
            def embed(self, texts, batch_size=32):
                ...

        def attempt(fn):
            try:
                fn()
                return "ok"
            except Exception as e:
                return type(e).__name__

        plain = Mock(spec=Embedder)
        auto = create_autospec(Embedder, instance=True)
        print(attempt(lambda: plain.embd), attempt(lambda: plain.embed(1, 2, 3, 4)), attempt(lambda: auto.embed(1, 2, 3, 4)))
        print(attempt(lambda: auto.embed(["a"], batch_size=8)), attempt(lambda: auto.embed(texts=["a"], size=8)))
        print(isinstance(plain, Embedder), attempt(lambda: len(Mock())), len(MagicMock()), list(MagicMock()))
        strict = Mock(spec_set=Embedder)
        print(attempt(lambda: setattr(strict, "dimension", 10)), attempt(lambda: setattr(plain, "dimension", 10)))
        """,
        hints=["`spec` restricts attribute names; autospec also checks call signatures. `MagicMock` configures magic methods; `Mock` does not.",
               "`spec_set` also forbids setting attributes the spec does not have."],
        why="""`Mock(spec=...)` rejects misspelt attributes but its methods accept any arguments, while autospec copies the real signatures, so four positional arguments or an
        unknown keyword raise `TypeError` exactly as the real method would. A spec'd mock also passes `isinstance` checks. A plain `Mock` does not support `len()`
        (magic methods must be configured), whereas `MagicMock` supplies defaults: length 0 and empty iteration. `spec_set` additionally refuses to **set** unknown
        attributes, while a `spec` mock lets you add them, which can hide typos in test setup."""),
)

section("interview", "Interview questions",
    explain("What is the difference between a mock, a stub and a fake, and when do you use each?", "medium", tag="Interview",
        why="""All three replace a real dependency in tests. A **stub** returns canned data and does nothing else, useful when the test only needs the dependency to answer (a
        model that always replies `spam`). A **fake** is a lightweight working implementation (an in-memory repository, a scripted LLM, a fake clock); it supports
        realistic sequences of operations, can be shared across many tests, and keeps tests focused on outcomes. A **mock** records interactions so the test can
        verify **how** the dependency was used (called once, with these arguments, never on this path); use it when the interaction is the behaviour, such as
        sending a notification, retrying with backoff or not calling a paid API. Spies wrap the real thing and record calls. Prefer stubs and fakes for state and
        results, mocks for important side effects, and verify mocks against the real interface with `spec`/autospec so they cannot drift."""),
    explain("Why do people say 'don't mock what you don't own'?", "medium", tag="Interview",
        why="""Mocking a third-party library (an LLM SDK, `requests`, a cloud client) directly in many tests encodes your **assumptions** about its behaviour into every test:
        method names, argument shapes, return types and error classes. When the library changes, or when your assumptions were wrong, the tests keep passing
        while production fails, and the patches are scattered everywhere. Instead, wrap the library in a thin adapter you own with a small interface that suits your
        application (`LLMClient.complete(prompt, max_tokens) -> str`, raising your own `LLMError`), mock or fake **that** in unit tests, and test the adapter itself
        against the real library with a few integration tests (or recorded responses). The adapter also gives you one place for retries, timeouts, logging and
        switching providers."""),
    explain("How do you unit-test code that calls an LLM API?", "hard", tag="Interview",
        why="""Separate the parts. Put the API behind a small client interface and inject it, so unit tests pass a fake or a mock: scripted replies for the happy path,
        malformed JSON and refusals for parsing and repair logic, `TimeoutError` and rate-limit errors for retry logic, and assertions on the prompts sent (that
        they contain the context and question, that no call happens when there is no context) and on call counts and parameters. Keep the deterministic logic
        (prompt building, output parsing and validation, routing, tool dispatch) in pure functions tested directly. Use `spec`/autospec so fakes match the real
        client. Then add a thin layer of **integration** tests against the real API, few, marked (`@pytest.mark.integration`) and run in CI with a key and a budget,
        possibly replaying recorded responses (VCR cassettes) for stability. Finally, evaluate model quality separately with an evaluation set (13.4), because
        unit tests check your code's behaviour, not whether the model's answers are good."""),
)

recap(
    "Test doubles replace slow, costly or random dependencies: stubs answer, fakes work, mocks record calls, spies wrap the real thing.",
    "`Mock` configures behaviour with `return_value` and `side_effect` (exception, iterable, function) and records calls; `assert_called_with` checks only the last call.",
    "Use `spec` or `create_autospec` so doubles match the real API; `MagicMock` adds magic methods.",
    "Patch where a name is looked up (`app.fetch`, not `weather.fetch`), or better, inject dependencies such as clients, clocks and `sleep`.",
    "Mock boundaries, not your own logic; assert behaviour, and wrap third-party APIs in adapters you own.",
)
