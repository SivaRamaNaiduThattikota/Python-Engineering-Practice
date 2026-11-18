from lesson import *

lesson(
    id="m13-2", num="13.2", title="Fixtures",
    intro="Real tests need things: a temporary folder, a configured client, a database with three rows, an environment variable "
          "that must be restored afterwards. Fixtures provide them. How pytest injects fixtures by name, `yield` for cleanup, "
          "scopes and their traps, parametrised and factory fixtures, `conftest.py`, and the built-in fixtures `tmp_path`, "
          "`monkeypatch`, `capsys` and `caplog`. As in 13.1, most problems are graded by running your tests against buggy versions.",
    desc="Setup and teardown with fixtures, scopes, `tmp_path`, `monkeypatch`, `capsys`, `caplog`.",
    keys="pytest fixture yield teardown scope function module session autouse conftest request param factory fixture tmp_path monkeypatch setenv delenv setattr capsys caplog dependency injection isolation",
)

term("Fixture", "A function marked with `@pytest.fixture` that prepares something a test needs; a test receives it by naming it as a parameter.")
term("Teardown", "The cleanup after a test: closing files, deleting data, restoring settings. In a fixture, the code after `yield` runs as teardown.")
term("Test isolation", "Every test starts from a known state and leaves nothing behind, so tests pass in any order and alone.")

section("fixtures", "Fixtures: dependencies by name",
    p("""Tests often need the same preparation: a list of sample documents, a configured object, a file on disk. Copying that code into every test is noisy, and
    putting it in module-level variables shares **mutable state** between tests, which makes them depend on each other's order. A **fixture** is a function
    decorated with `@pytest.fixture` that builds the thing; a test asks for it by **naming a parameter after it**, and pytest calls the fixture, passes the
    result in, and does it again, freshly, for the next test. Fixtures can ask for other fixtures the same way, so setup is composed from small pieces."""),
    p("""This is **dependency injection**: the test declares what it needs and the framework supplies it. It also makes tests read well: `def
    test_search_ranks_exact_match_first(store, sample_docs):` says what the test needs without saying how it is built."""),
    ex("""
    import re
    from lessontools import run_pytest

    SRC = '''
    import pytest

    @pytest.fixture
    def docs():
        print("<building docs>")
        return [{"id": "faq-1", "text": "Refunds take 5 days"}, {"id": "faq-2", "text": "Shipping is free"}]

    @pytest.fixture
    def index(docs):
        print(f"<building index from {len(docs)} docs>")
        return {d["id"]: d["text"].lower() for d in docs}

    def test_lookup(index):
        assert index["faq-1"] == "refunds take 5 days"

    def test_mutation_is_private(docs):
        docs.append({"id": "faq-3", "text": "x"})
        assert len(docs) == 3

    def test_fresh_again(docs):
        assert len(docs) == 2
    '''
    r = run_pytest(SRC, args=["-s", "--tb=no"])
    print(r["outcomes"])
    print(re.findall(r"<([^<>]+)>", r["output"]))
    """, "fixtures.py"),
    p("""`-s` turns off pytest's output capturing so the prints are visible, and `--tb=no` hides tracebacks; the markers in angle brackets are only there to pick
    the prints out of pytest's report. `docs` was built three times, once per test that needed it (`index` asked for it in the first test, so pytest built
    `docs` before `index`), which is why the list appended to in the second test is gone in the third."""),
)

section("yield", "Cleanup with `yield`",
    p("""A fixture that acquires something must release it. Write it as a generator: code before **`yield`** is the setup, the yielded value goes to the test, and code
    after `yield` is the **teardown**, which runs after the test **whether it passed or failed**, like the `finally` of a context manager (10.2). When a
    test uses several fixtures, teardowns run in reverse order of setup. If setup raises, the test is reported as an **error** (not a failure), which tells
    you the problem is in the preparation; a failing teardown is also an error."""),
    ex("""
    import re
    from lessontools import run_pytest

    SRC = '''
    import pytest

    @pytest.fixture
    def connection():
        print("<open connection>")
        yield {"open": True}
        print("<close connection>")

    @pytest.fixture
    def transaction(connection):
        print("<begin>")
        yield []
        print("<rollback>")

    def test_insert(transaction):
        transaction.append("row")
        assert transaction == ["row", "other"]
    '''
    r = run_pytest(SRC, args=["-s", "--tb=no"])
    print(r["outcomes"])
    print(re.findall(r"<([^<>]+)>", r["output"]))
    """, "teardown.py"),
)

section("scope", "Scopes, autouse and conftest.py",
    p("""By default a fixture has **function scope**: it is created for every test that uses it. `@pytest.fixture(scope="module")` creates it once per test file,
    `"class"` once per test class, and `"session"` once per test run, which is how you share something **expensive** such as a loaded model, a started
    container or a database schema. The trap: a shared object is shared, so if one test mutates it, the next sees the change, and the suite becomes
    order-dependent (problem 7). Share only read-only things at wide scope, or pair a wide-scoped resource with a function-scoped fixture that resets it (a
    session database plus a per-test transaction that is rolled back). A fixture can only use fixtures of the same or wider scope."""),
    p("""`autouse=True` applies a fixture to every test in its scope without naming it, useful for "always reset this global" or "never allow network calls",
    but invisible to readers, so use it sparingly. Fixtures defined in a file named **`conftest.py`** are available to every test file in that folder and
    below, with no import; a project usually has one at the top of `tests/` for shared fixtures and more in subfolders for specific ones."""),
    p("""A fixture can be **parametrised**: `@pytest.fixture(params=["small", "large"])` runs every test that uses it once per parameter, with the value in
    `request.param`, which is how one test suite is run against several backends or models. And when tests need several similar objects with variations, a
    **factory fixture** returns a function (`make_doc(id="faq-1", text=...)`) rather than one object, keeping defaults in one place and letting each test
    state only what matters to it (problem 12)."""),
)

section("builtin", "Built-in fixtures",
    p("""pytest ships fixtures for the usual sources of non-isolation. **`tmp_path`** gives each test a fresh, empty `pathlib.Path` folder, so tests never write into
    the project or collide with each other (12.1). **`monkeypatch`** changes things for one test and undoes them afterwards: `monkeypatch.setenv("KEY",
    "value")` and `delenv("KEY", raising=False)` for environment variables (12.4), `monkeypatch.setattr(module, "name", replacement)` to swap a function or
    attribute (13.3 builds on this), `monkeypatch.chdir(path)` and `monkeypatch.setitem(dict, key, value)`. **`capsys`** captures what the code prints:
    `capsys.readouterr()` returns an object with `.out` and `.err`. **`caplog`** captures log records (12.3): `caplog.records`, `caplog.messages`, and
    `caplog.set_level(logging.INFO)` to make sure records below the default level are kept. `request` gives fixtures information about the test using them,
    and `recwarn` records warnings."""),
    ex("""
    from lessontools import run_pytest

    SRC = '''
    import logging, os

    def save_greeting(folder, name):
        path = folder / "greeting.txt"
        path.write_text(f"Hello, {name}", encoding="utf-8")
        print("saved", path.name)
        logging.getLogger("app").warning("wrote %s", path.name)
        return path

    def test_writes_into_tmp_path(tmp_path, capsys, caplog):
        path = save_greeting(tmp_path, os.environ["USER_NAME"]) if "USER_NAME" in os.environ else save_greeting(tmp_path, "Ana")
        assert path.read_text(encoding="utf-8") == "Hello, Ana"
        assert capsys.readouterr().out == "saved greeting.txt\\\\n"
        assert caplog.messages == ["wrote greeting.txt"]

    def test_env_is_restored(monkeypatch):
        monkeypatch.setenv("USER_NAME", "Bo")
        assert os.environ["USER_NAME"] == "Bo"

    def test_after(tmp_path):
        assert "USER_NAME" not in os.environ and list(tmp_path.iterdir()) == []
    '''
    print(run_pytest(SRC)["outcomes"])
    """, "builtin.py"),
)

section("warmup", "Warm-up",
    predict("The order of setup and teardown", "easy",
        code="""
        import re
        from lessontools import run_pytest

        SRC = '''
        import pytest

        @pytest.fixture
        def a():
            print("<a-setup>")
            yield "A"
            print("<a-teardown>")

        @pytest.fixture
        def b(a):
            print("<b-setup>")
            yield a + "B"
            print("<b-teardown>")

        def test_one(b):
            print(f"<test_one {b}>")

        def test_two(a):
            print(f"<test_two {a}>")
            assert False
        '''
        r = run_pytest(SRC, args=["-s", "--tb=no"])
        print(re.findall(r"<([^<>]+)>", r["output"]))
        print(r["outcomes"])
        """,
        hints=["A fixture's dependencies are set up first; teardowns run in reverse order, after the test, even when it fails."],
        why="""For `test_one`, `b` needs `a`, so `a` is set up first, then `b`; after the test, teardown runs in reverse: `b` then `a`. `test_two` gets a **new** `a`
        (function scope), and its teardown still runs although the test failed, which is the whole point of `yield` fixtures."""),
    write("Tests with a fixture for a shopping cart", "easy", tag="Data work",
        prompt="""Write a fixture `cart` that returns a `Cart` with two items already added (`"pen"` at 1.5 x 2 and `"book"` at 12.0 x 1), and at least four tests that use
        it, covering `total`, adding more of an existing item, removing an item, and that removing an unknown item raises `KeyError`. Your tests must pass here
        and catch four buggy versions.""",
        code="""
        # --- code under test (do not edit) ---
        class Cart:
            def __init__(self):
                self.items = {}

            def add(self, name, price, qty=1):
                if qty < 1:
                    raise ValueError("qty must be at least 1")
                old_price, old_qty = self.items.get(name, (price, 0))
                self.items[name] = (price, old_qty + qty)

            def remove(self, name):
                del self.items[name]

            def total(self):
                return round(sum(price * qty for price, qty in self.items.values()), 2)


        # --- tests ---
        import pytest
        """,
        tests="""
        import pytest
        from lessontools import run_pytest, swap_impl
        good = run_pytest(__source__)
        assert good["failed"] == 0 and good["passed"] >= 4, good["output"][-800:]
        assert "@pytest.fixture" in __source__
        BASE = '''
        class Cart:
            def __init__(self):
                self.items = {}

            def add(self, name, price, qty=1):
                if qty < 1:
                    raise ValueError("qty must be at least 1")
                old_price, old_qty = self.items.get(name, (price, 0))
                self.items[name] = (price, old_qty + qty)

            def remove(self, name):
                del self.items[name]

            def total(self):
                return round(sum(price * qty for price, qty in self.items.values()), 2)
        '''
        BUGS = {
            "add_replaces_qty": BASE.replace("old_qty + qty", "qty"),
            "total_ignores_qty": BASE.replace("price * qty for", "price for"),
            "remove_silent": BASE.replace("del self.items[name]", "self.items.pop(name, None)"),
            "remove_clears_all": BASE.replace("del self.items[name]", "self.items.clear()"),
        }
        escaped = sorted(name for name, impl in BUGS.items() if run_pytest(swap_impl(__source__, impl))["failed"] == 0)
        assert escaped == []
        """,
        hints=["`@pytest.fixture` above `def cart():` that builds the cart, adds both items and returns it.",
               "After removing `\"pen\"`, check both what is gone and what is left."],
        solution="""
        # --- code under test (do not edit) ---
        class Cart:
            def __init__(self):
                self.items = {}

            def add(self, name, price, qty=1):
                if qty < 1:
                    raise ValueError("qty must be at least 1")
                old_price, old_qty = self.items.get(name, (price, 0))
                self.items[name] = (price, old_qty + qty)

            def remove(self, name):
                del self.items[name]

            def total(self):
                return round(sum(price * qty for price, qty in self.items.values()), 2)


        # --- tests ---
        import pytest


        @pytest.fixture
        def cart():
            c = Cart()
            c.add("pen", 1.5, qty=2)
            c.add("book", 12.0)
            return c


        def test_total(cart):
            assert cart.total() == 15.0


        def test_adding_existing_item_increases_quantity(cart):
            cart.add("pen", 1.5, qty=3)
            assert cart.items["pen"] == (1.5, 5)
            assert cart.total() == 19.5


        def test_remove_item(cart):
            cart.remove("pen")
            assert "pen" not in cart.items and cart.total() == 12.0


        def test_remove_unknown_raises(cart):
            with pytest.raises(KeyError):
                cart.remove("lamp")


        def test_rejects_zero_quantity(cart):
            with pytest.raises(ValueError):
                cart.add("pen", 1.5, qty=0)
        """,
        why="""The fixture states the common starting point once, and each test reads as "given the cart, when I do X, then Y". Because the fixture runs for every test,
        `test_remove_item` can mutate the cart freely without affecting `test_total`. Each mutant breaks one behaviour: replacing instead of adding quantities
        is caught by adding more pens, ignoring quantities by the total with two pens, a silent remove by the `KeyError` test, and clearing everything by
        checking what is **left** after a removal, a reminder that "the item is gone" is only half of the expected outcome."""),
    fix("Tests that share a module-level list", "easy", tag="GenAI",
        prompt="""These tests for a chat history share the global `HISTORY`, so `test_second_turn` only passes when `test_first_turn` has run before it, and fails when run
        alone (`pytest -k second`). Replace the global with a fixture so every test is independent and still passes.""",
        code="""
        # --- code under test (do not edit) ---
        def add_turn(history, role, content):
            if role not in ("user", "assistant"):
                raise ValueError(f"bad role {role!r}")
            history.append({"role": role, "content": content})
            return len(history)


        # --- tests ---
        import pytest

        HISTORY = []


        def test_first_turn():
            assert add_turn(HISTORY, "user", "Hi") == 1


        def test_second_turn():
            assert add_turn(HISTORY, "assistant", "Hello!") == 2
            assert HISTORY[0]["role"] == "user"
        """,
        tests="""
        import pytest
        from lessontools import run_pytest
        tests_part = __source__.split("# --- tests")[1]
        assert run_pytest(__source__)["failed"] == 0
        alone = run_pytest(__source__, args=["-k", "second"])
        assert alone["failed"] == 0 and alone["passed"] == 1, alone["output"][-600:]
        assert "HISTORY" not in tests_part and "@pytest.fixture" in tests_part
        """,
        hints=["A fixture `history` that returns a list already holding the user's first turn lets `test_second_turn` stand on its own."],
        solution="""
        # --- code under test (do not edit) ---
        def add_turn(history, role, content):
            if role not in ("user", "assistant"):
                raise ValueError(f"bad role {role!r}")
            history.append({"role": role, "content": content})
            return len(history)


        # --- tests ---
        import pytest


        @pytest.fixture
        def history():
            return [{"role": "user", "content": "Hi"}]


        def test_first_turn():
            assert add_turn([], "user", "Hi") == 1


        def test_second_turn(history):
            assert add_turn(history, "assistant", "Hello!") == 2
            assert history[0]["role"] == "user"
        """,
        why="""A module-level list is created once when the file is imported and shared by every test, so the second test silently relied on the first having appended to
        it. Run alone, in another order, or in parallel (`pytest-xdist`), it fails, and a failure that depends on which tests ran is the most confusing kind. The
        fixture gives `test_second_turn` exactly the state it needs, freshly built, so it passes in any order and documents its precondition in its signature."""),
    predict("tmp_path and monkeypatch clean up", "easy",
        code="""
        from lessontools import run_pytest

        SRC = '''
        import os

        def test_a(tmp_path, monkeypatch):
            (tmp_path / "note.txt").write_text("a", encoding="utf-8")
            monkeypatch.setenv("P4_MODE", "test")
            monkeypatch.setattr(os, "sep", "|")
            assert os.environ["P4_MODE"] == "test" and os.sep == "|"

        def test_b(tmp_path):
            assert list(tmp_path.iterdir()) == []
            assert "P4_MODE" not in os.environ
            assert os.sep == "/"

        def test_c(tmp_path, monkeypatch):
            monkeypatch.delenv("P4_MISSING", raising=False)
            monkeypatch.delenv("P4_MISSING")
        '''
        print(run_pytest(SRC)["outcomes"])
        """,
        hints=["Each test gets a new empty `tmp_path`, and `monkeypatch` undoes its changes after the test. `delenv` raises if the variable is missing, unless `raising=False`."],
        why="""`tmp_path` is a different, empty folder for every test, so the file written in `test_a` is not in `test_b`'s folder. Every `monkeypatch` change, environment
        variables and attributes alike, is undone after the test, so `test_b` sees the original `os.sep`. In `test_c`, `raising=False` tolerates a missing
        variable, but the second `delenv` uses the default `raising=True` and raises `KeyError`, failing the test."""),
)

section("medium", "Medium",
    write("Test a JSONL store with tmp_path", "medium", tag="GenAI",
        prompt="""`write_jsonl(path, records)` creates parent folders, overwrites the file, writes one compact JSON object per line keeping non-ASCII characters, and
        returns the count; `read_jsonl(path)` returns the list of objects, skipping blank lines. Write at least four tests using `tmp_path` that pass here and catch
        four buggy versions.""",
        code="""
        # --- code under test (do not edit) ---
        import json


        def write_jsonl(path, records):
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                for r in records:
                    f.write(json.dumps(r, ensure_ascii=False) + "\\n")
            return len(records)


        def read_jsonl(path):
            with open(path, encoding="utf-8") as f:
                return [json.loads(line) for line in f if line.strip()]


        # --- tests ---
        import pytest
        """,
        tests="""
        import pytest
        from lessontools import run_pytest, swap_impl
        good = run_pytest(__source__)
        assert good["failed"] == 0 and good["passed"] >= 4, good["output"][-800:]
        assert "tmp_path" in __source__.split("# --- tests")[1]
        BASE = '''
        import json


        def write_jsonl(path, records):
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                for r in records:
                    f.write(json.dumps(r, ensure_ascii=False) + "\\\\n")
            return len(records)


        def read_jsonl(path):
            with open(path, encoding="utf-8") as f:
                return [json.loads(line) for line in f if line.strip()]
        '''
        BUGS = {
            "appends": BASE.replace('open(path, "w"', 'open(path, "a"'),
            "escapes_ascii": BASE.replace("json.dumps(r, ensure_ascii=False)", "json.dumps(r)"),
            "no_mkdir": BASE.replace("    path.parent.mkdir(parents=True, exist_ok=True)\\n", ""),
            "blank_lines_crash": BASE.replace(" if line.strip()]", "]"),
        }
        assert all(b != BASE for b in BUGS.values())
        escaped = sorted(name for name, impl in BUGS.items() if run_pytest(swap_impl(__source__, impl))["failed"] == 0)
        assert escaped == []
        """,
        hints=["Round trip: write then read and compare. Overwrite: write twice and check only the second set remains.",
               "Check the raw file text contains `é` (not `\\u00e9`); write into `tmp_path / \"a\" / \"b\" / \"x.jsonl\"`; append a blank line by hand before reading."],
        solution="""
        # --- code under test (do not edit) ---
        import json


        def write_jsonl(path, records):
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                for r in records:
                    f.write(json.dumps(r, ensure_ascii=False) + "\\n")
            return len(records)


        def read_jsonl(path):
            with open(path, encoding="utf-8") as f:
                return [json.loads(line) for line in f if line.strip()]


        # --- tests ---
        import pytest

        RECORDS = [{"id": 1, "text": "Où est ma commande ?"}, {"id": 2, "text": "plain"}]


        @pytest.fixture
        def path(tmp_path):
            return tmp_path / "data" / "nested" / "turns.jsonl"


        def test_round_trip_and_count(path):
            assert write_jsonl(path, RECORDS) == 2
            assert read_jsonl(path) == RECORDS


        def test_overwrites_existing_file(path):
            write_jsonl(path, RECORDS)
            write_jsonl(path, [{"id": 3}])
            assert read_jsonl(path) == [{"id": 3}]


        def test_keeps_non_ascii_characters(path):
            write_jsonl(path, RECORDS)
            raw = path.read_text(encoding="utf-8")
            assert "Où" in raw and raw.count("\\n") == 2


        def test_skips_blank_lines(path):
            write_jsonl(path, RECORDS)
            with open(path, "a", encoding="utf-8") as f:
                f.write("\\n   \\n")
            assert len(read_jsonl(path)) == 2
        """,
        why="""`tmp_path` makes file tests safe and independent: every test writes into its own empty folder, so overwriting, appending and missing-folder cases can be
        checked without touching the project or each other, and pytest keeps the last few runs' folders for inspection. A small fixture on top of it (`path`)
        gives every test the same nested location, which is what exercises the folder creation. The tests check observable behaviour (file content and what
        reading returns), so each mutant fails: appending keeps the old records, escaping removes `Où` from the raw text, a missing `mkdir` raises on the nested
        path, and the reader without the blank-line filter crashes on `json.loads("\\n")`."""),
    write("Test environment-based settings with monkeypatch", "medium", tag="GenAI",
        prompt="""`load_settings()` reads `APP_MODEL` (default `"small"`), `APP_TEMPERATURE` (float in `[0, 2]`, default `0.0`) and the required `OPENAI_API_KEY` (a
        `RuntimeError` if missing or empty) from `os.environ`. Write at least four tests using `monkeypatch.setenv` and `delenv` that pass here and catch four
        buggy versions. Your tests must not depend on the real environment of the machine running them.""",
        code="""
        # --- code under test (do not edit) ---
        import os


        def load_settings():
            key = os.environ.get("OPENAI_API_KEY", "")
            if not key:
                raise RuntimeError("OPENAI_API_KEY is not set")
            temperature = float(os.environ.get("APP_TEMPERATURE", "0.0"))
            if not 0 <= temperature <= 2:
                raise ValueError(f"APP_TEMPERATURE out of range: {temperature}")
            return {"model": os.environ.get("APP_MODEL", "small"), "temperature": temperature, "api_key": key}


        # --- tests ---
        import pytest
        """,
        tests="""
        import os, pytest
        from lessontools import run_pytest, swap_impl
        os.environ["OPENAI_API_KEY"] = "sk-real-machine-key"
        os.environ["APP_MODEL"] = "machine-model"
        good = run_pytest(__source__)
        os.environ.pop("OPENAI_API_KEY")
        os.environ.pop("APP_MODEL")
        assert good["failed"] == 0 and good["passed"] >= 4, good["output"][-800:]
        assert "monkeypatch" in __source__.split("# --- tests")[1]
        BASE = '''
        import os


        def load_settings():
            key = os.environ.get("OPENAI_API_KEY", "")
            if not key:
                raise RuntimeError("OPENAI_API_KEY is not set")
            temperature = float(os.environ.get("APP_TEMPERATURE", "0.0"))
            if not 0 <= temperature <= 2:
                raise ValueError(f"APP_TEMPERATURE out of range: {temperature}")
            return {"model": os.environ.get("APP_MODEL", "small"), "temperature": temperature, "api_key": key}
        '''
        BUGS = {
            "empty_key_ok": BASE.replace('os.environ.get("OPENAI_API_KEY", "")\\n    if not key:', 'os.environ.get("OPENAI_API_KEY")\\n    if key is None:'),
            "no_range_check": BASE.replace("if not 0 <= temperature <= 2:", "if temperature != temperature:"),
            "wrong_default_model": BASE.replace('"APP_MODEL", "small"', '"APP_MODEL", "large"'),
            "temperature_string": BASE.replace('"temperature": temperature', '"temperature": os.environ.get("APP_TEMPERATURE", "0.0")'),
        }
        assert all(b != BASE for b in BUGS.values())
        escaped = sorted(name for name, impl in BUGS.items() if run_pytest(swap_impl(__source__, impl))["failed"] == 0)
        assert escaped == []
        """,
        hints=["Start each test from a clean slate: an autouse fixture that `delenv`s the three variables with `raising=False`, then set what the test needs.",
               "Check the empty key (`setenv(\"OPENAI_API_KEY\", \"\")`), a temperature of 2.5, the defaults, and the type of the parsed temperature."],
        solution="""
        # --- code under test (do not edit) ---
        import os


        def load_settings():
            key = os.environ.get("OPENAI_API_KEY", "")
            if not key:
                raise RuntimeError("OPENAI_API_KEY is not set")
            temperature = float(os.environ.get("APP_TEMPERATURE", "0.0"))
            if not 0 <= temperature <= 2:
                raise ValueError(f"APP_TEMPERATURE out of range: {temperature}")
            return {"model": os.environ.get("APP_MODEL", "small"), "temperature": temperature, "api_key": key}


        # --- tests ---
        import pytest


        @pytest.fixture(autouse=True)
        def clean_env(monkeypatch):
            for name in ("OPENAI_API_KEY", "APP_MODEL", "APP_TEMPERATURE"):
                monkeypatch.delenv(name, raising=False)
            monkeypatch.setenv("OPENAI_API_KEY", "sk-test")


        def test_defaults():
            assert load_settings() == {"model": "small", "temperature": 0.0, "api_key": "sk-test"}


        def test_reads_overrides(monkeypatch):
            monkeypatch.setenv("APP_MODEL", "large")
            monkeypatch.setenv("APP_TEMPERATURE", "0.7")
            s = load_settings()
            assert s["model"] == "large" and s["temperature"] == 0.7 and isinstance(s["temperature"], float)


        @pytest.mark.parametrize("value", [None, ""])
        def test_missing_or_empty_key(monkeypatch, value):
            if value is None:
                monkeypatch.delenv("OPENAI_API_KEY")
            else:
                monkeypatch.setenv("OPENAI_API_KEY", value)
            with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
                load_settings()


        @pytest.mark.parametrize("value", ["-0.1", "2.5"])
        def test_temperature_out_of_range(monkeypatch, value):
            monkeypatch.setenv("APP_TEMPERATURE", value)
            with pytest.raises(ValueError, match="out of range"):
                load_settings()
        """,
        why="""The grader ran your tests with a real-looking key and model already set in the environment, as on a developer's machine. A test that assumes "no key is set"
        without removing it would pass or fail depending on who runs it; the autouse fixture removes every variable the code reads and sets a dummy key, so each
        test starts from the same known state, and `monkeypatch` restores the machine's values afterwards. Tests then set only what they are about. The
        parametrised error tests cover missing **and** empty keys (the `is None` mutant only rejects missing) and both sides of the range."""),
    fix("A session fixture that tests mutate", "medium", tag="ML",
        prompt="""Loading the label map is slow, so it was made a `session`-scoped fixture. But `test_add_label` mutates it, and `test_label_count` now fails when it runs after
        it. Keep the expensive load happening **once**, but give each test its own copy, so the tests pass in any order.""",
        code="""
        # --- code under test (do not edit) ---
        def load_label_map():
            # imagine this reads a large file or calls a service
            return {"spam": 0, "ham": 1, "phish": 2}


        # --- tests ---
        import pytest


        @pytest.fixture(scope="session")
        def label_map():
            return load_label_map()


        def test_add_label(label_map):
            label_map["promo"] = 3
            assert len(label_map) == 4


        def test_label_count(label_map):
            assert len(label_map) == 3
        """,
        tests="""
        import pytest
        from lessontools import run_pytest
        r = run_pytest(__source__)
        assert r["failed"] == 0 and r["passed"] == 2, r["output"][-600:]
        counted = run_pytest(__source__.replace("return load_label_map()", "import builtins\\n    builtins.loads = getattr(builtins, 'loads', 0) + 1\\n    return load_label_map()"))
        import builtins
        loads = getattr(builtins, "loads", 0)
        if hasattr(builtins, "loads"):
            del builtins.loads
        assert counted["failed"] == 0 and loads == 1
        """,
        hints=["Keep the session fixture (rename it, e.g. `_label_map_source`), and add a function-scoped `label_map` fixture that returns `dict(...)` of it."],
        solution="""
        # --- code under test (do not edit) ---
        def load_label_map():
            # imagine this reads a large file or calls a service
            return {"spam": 0, "ham": 1, "phish": 2}


        # --- tests ---
        import pytest


        @pytest.fixture(scope="session")
        def label_map_source():
            return load_label_map()


        @pytest.fixture
        def label_map(label_map_source):
            return dict(label_map_source)


        def test_add_label(label_map):
            label_map["promo"] = 3
            assert len(label_map) == 4


        def test_label_count(label_map):
            assert len(label_map) == 3
        """,
        why="""A wider scope shares **one object** among tests, so any mutation leaks into every later test. The standard pattern splits the fixture in two: the expensive
        work stays session-scoped and runs once (the grader counted the loads), and a cheap function-scoped fixture hands each test a copy, or in a database
        test, a transaction that is rolled back. For nested data, `copy.deepcopy` is needed instead of `dict(...)`. Session fixtures are ideal for read-only
        resources such as a loaded tokenizer or model weights, and dangerous for anything a test might change."""),
    trace("A yield fixture is a generator", "medium",
        prompt="Fill in `events` after each marked line. This is what pytest does with a `yield` fixture.",
        code="""
        events = []

        def resource():
            events.append("setup")
            try:
                yield "conn"
            finally:
                events.append("teardown")

        gen = resource()
        value = next(gen)  # row: "setup"
        events.append(f"test uses {value}")  # row: "test runs"
        try:
            next(gen)
        except StopIteration:
            events.append("done")  # row: "after teardown"

        gen2 = resource()
        next(gen2)
        gen2.close()  # row: "closed early"
        """,
        trace_vars=["events"],
        hints=["`next` runs the generator up to `yield`. A second `next` runs the rest and raises `StopIteration`. `close()` raises `GeneratorExit` at the `yield`, so `finally` runs."],
        why="""pytest calls `next` once to run the setup and get the value, runs the test, and calls `next` again so the code after `yield` runs; the generator then finishes
        with `StopIteration`, which pytest expects. If something interrupts the run, closing the generator raises `GeneratorExit` at the `yield`, and the
        `finally` still executes, which is why cleanup in fixtures, like in `@contextmanager` functions (10.2), is safest in a `finally` block or after the
        `yield`."""),
    write("Assert on logs with caplog", "medium", tag="GenAI",
        prompt="""`call_with_retry(fn, attempts=3)` calls `fn()`, and for each failure logs a `WARNING` `"attempt %d failed: %s"` on the logger `"retry"`; when all attempts
        fail it logs an `ERROR` `"giving up after %d attempts"` and re-raises the last error. Write at least three tests using `caplog` (check levels and
        messages) that pass here and catch four buggy versions.""",
        code="""
        # --- code under test (do not edit) ---
        import logging

        log = logging.getLogger("retry")


        def call_with_retry(fn, attempts=3):
            for attempt in range(1, attempts + 1):
                try:
                    return fn()
                except Exception as e:
                    log.warning("attempt %d failed: %s", attempt, e)
                    last = e
            log.error("giving up after %d attempts", attempts)
            raise last


        # --- tests ---
        import pytest
        """,
        tests="""
        import pytest
        from lessontools import run_pytest, swap_impl
        good = run_pytest(__source__)
        assert good["failed"] == 0 and good["passed"] >= 3, good["output"][-800:]
        assert "caplog" in __source__.split("# --- tests")[1]
        BASE = '''
        import logging

        log = logging.getLogger("retry")


        def call_with_retry(fn, attempts=3):
            for attempt in range(1, attempts + 1):
                try:
                    return fn()
                except Exception as e:
                    log.warning("attempt %d failed: %s", attempt, e)
                    last = e
            log.error("giving up after %d attempts", attempts)
            raise last
        '''
        BUGS = {
            "info_level": BASE.replace("log.warning(", "log.info("),
            "no_final_error": BASE.replace('    log.error("giving up after %d attempts", attempts)\\n', ""),
            "zero_based": BASE.replace('"attempt %d failed: %s", attempt, e', '"attempt %d failed: %s", attempt - 1, e'),
            "swallows": BASE.replace("    raise last", "    return None"),
        }
        assert all(b != BASE for b in BUGS.values())
        escaped = sorted(name for name, impl in BUGS.items() if run_pytest(swap_impl(__source__, impl))["failed"] == 0)
        assert escaped == []
        """,
        hints=["A small fake: `iter([...])` of results where exceptions are raised, or a function that fails the first n times.",
               "`[(r.levelname, r.getMessage()) for r in caplog.records]` compares levels and messages at once; `caplog.set_level(logging.INFO)` keeps lower records too."],
        solution="""
        # --- code under test (do not edit) ---
        import logging

        log = logging.getLogger("retry")


        def call_with_retry(fn, attempts=3):
            for attempt in range(1, attempts + 1):
                try:
                    return fn()
                except Exception as e:
                    log.warning("attempt %d failed: %s", attempt, e)
                    last = e
            log.error("giving up after %d attempts", attempts)
            raise last


        # --- tests ---
        import logging
        import pytest


        def flaky(failures):
            calls = {"n": 0}

            def fn():
                calls["n"] += 1
                if calls["n"] <= failures:
                    raise ConnectionError(f"reset {calls['n']}")
                return "ok"
            return fn


        def test_success_after_failures_logs_warnings(caplog):
            caplog.set_level(logging.INFO)
            assert call_with_retry(flaky(2)) == "ok"
            assert [(r.levelname, r.getMessage()) for r in caplog.records] == [
                ("WARNING", "attempt 1 failed: reset 1"), ("WARNING", "attempt 2 failed: reset 2")]


        def test_first_try_logs_nothing(caplog):
            caplog.set_level(logging.INFO)
            assert call_with_retry(flaky(0)) == "ok"
            assert caplog.records == []


        def test_gives_up_with_error_and_reraises(caplog):
            caplog.set_level(logging.INFO)
            with pytest.raises(ConnectionError, match="reset 3"):
                call_with_retry(flaky(5), attempts=3)
            assert [r.levelname for r in caplog.records] == ["WARNING"] * 3 + ["ERROR"]
            assert caplog.records[-1].getMessage() == "giving up after 3 attempts"
            assert caplog.records[-1].name == "retry"
        """,
        why="""Logs are behaviour too: operators rely on the warning per retry and the final error, so tests should pin their level and wording. `caplog` captures records
        from every logger during the test; setting the level to `INFO` matters because otherwise a mutant that logs at `INFO` would simply not be captured and
        the comparison would fail for the wrong reason, or a mutant at a lower level would slip through a looser check. The fake `flaky` function fails a chosen
        number of times, making the retry path deterministic. Checking that the last error is **re-raised** (with its message) catches the swallowing mutant."""),
    predict("Scopes and parametrized fixtures", "medium",
        code="""
        import re
        from lessontools import run_pytest

        SRC = '''
        import pytest

        @pytest.fixture(scope="module")
        def model():
            print("<load model>")
            return "weights"

        @pytest.fixture(params=["small", "large"])
        def size(request):
            print(f"<size {request.param}>")
            return request.param

        def test_one(model):
            pass

        def test_two(model, size):
            pass

        def test_three(size):
            assert size == "small"
        '''
        r = run_pytest(SRC, args=["-s", "--tb=no"])
        print(re.findall(r"<([^<>]+)>", r["output"]))
        print(r["outcomes"])
        """,
        hints=["A module-scoped fixture is created once per file. A parametrised fixture multiplies every test that uses it."],
        why="""The module-scoped model is loaded once and reused by `test_one` and both `test_two` runs. The parametrised `size` fixture turns each test that uses it into
        one test per parameter, with the parameter in the id, and since it has function scope it is set up again for each of them. `test_three[large]` fails
        its assert, so the same test body is reported once as passed and once as failed."""),
    write("Test console output with capsys", "medium", tag="Data work",
        prompt="""`print_report(stats)` prints one aligned line per metric, sorted by name, as `f"{name:<10}{value:>8.3f}"`, then `"total runs: N"`, and prints warnings
        (for negative values) to **standard error** as `"warning: negative NAME"`. Write at least three tests using `capsys` that check standard output and
        standard error separately. They must pass here and catch four buggy versions.""",
        code="""
        # --- code under test (do not edit) ---
        import sys


        def print_report(stats, runs):
            for name in sorted(stats):
                value = stats[name]
                if value < 0:
                    print(f"warning: negative {name}", file=sys.stderr)
                print(f"{name:<10}{value:>8.3f}")
            print(f"total runs: {runs}")


        # --- tests ---
        import pytest
        """,
        tests="""
        import pytest
        from lessontools import run_pytest, swap_impl
        good = run_pytest(__source__)
        assert good["failed"] == 0 and good["passed"] >= 3, good["output"][-800:]
        assert "capsys" in __source__.split("# --- tests")[1]
        BASE = '''
        import sys


        def print_report(stats, runs):
            for name in sorted(stats):
                value = stats[name]
                if value < 0:
                    print(f"warning: negative {name}", file=sys.stderr)
                print(f"{name:<10}{value:>8.3f}")
            print(f"total runs: {runs}")
        '''
        BUGS = {
            "unsorted": BASE.replace("for name in sorted(stats):", "for name in stats:"),
            "warning_to_stdout": BASE.replace(", file=sys.stderr", ""),
            "two_decimals": BASE.replace(">8.3f", ">8.2f"),
            "no_total": BASE.replace('    print(f"total runs: {runs}")\\n', ""),
        }
        assert all(b != BASE for b in BUGS.values())
        escaped = sorted(name for name, impl in BUGS.items() if run_pytest(swap_impl(__source__, impl))["failed"] == 0)
        assert escaped == []
        """,
        hints=["`out, err = capsys.readouterr()` after the call; compare `out.splitlines()` with the exact expected lines.",
               "Pass the stats in non-alphabetical order so sorting is visible."],
        solution="""
        # --- code under test (do not edit) ---
        import sys


        def print_report(stats, runs):
            for name in sorted(stats):
                value = stats[name]
                if value < 0:
                    print(f"warning: negative {name}", file=sys.stderr)
                print(f"{name:<10}{value:>8.3f}")
            print(f"total runs: {runs}")


        # --- tests ---
        import pytest


        def test_lines_are_sorted_and_aligned(capsys):
            print_report({"recall": 0.5, "f1": 0.6667}, runs=3)
            out, err = capsys.readouterr()
            assert out.splitlines() == ["f1           0.667", "recall       0.500", "total runs: 3"]
            assert err == ""


        def test_negative_values_warn_on_stderr(capsys):
            print_report({"delta": -0.25}, runs=1)
            out, err = capsys.readouterr()
            assert err == "warning: negative delta\\n"
            assert "warning" not in out and out.splitlines()[0] == "delta       -0.250"


        def test_empty_stats_still_prints_total(capsys):
            print_report({}, runs=0)
            assert capsys.readouterr().out == "total runs: 0\\n"
        """,
        why="""`capsys` replaces standard output and standard error during the test, and `readouterr()` returns (and resets) what was written to each, so tests can check the
        two streams separately, which matters because scripts and CLIs (15.3) must keep data on stdout and diagnostics on stderr so pipes work. Comparing the
        exact lines checks order, alignment and precision together; feeding the metrics out of alphabetical order is what exposes the unsorted mutant. For
        logging, use `caplog`; for prints, `capsys`."""),
)

section("hard", "Hard",
    write("A factory fixture for a document store", "hard", tag="RAG",
        prompt="""Write a **factory fixture** `make_doc` returning a function `make_doc(id="doc-1", text="Refunds take 5 days", source="faq.md")` that builds document dicts
        with those defaults, and a fixture `store` giving an empty `DocumentStore`. Then write at least five tests for the store that pass here and catch five
        buggy versions: add and get, duplicate ids, delete, search ranking, and `source` filtering.""",
        code="""
        # --- code under test (do not edit) ---
        class DocumentStore:
            def __init__(self):
                self._docs = {}

            def add(self, doc):
                if doc["id"] in self._docs:
                    raise ValueError(f"duplicate id {doc['id']}")
                self._docs[doc["id"]] = dict(doc)

            def get(self, doc_id):
                return dict(self._docs[doc_id])

            def delete(self, doc_id):
                self._docs.pop(doc_id)

            def search(self, query, source=None, k=3):
                words = set(query.lower().split())
                scored = []
                for doc in self._docs.values():
                    if source is not None and doc["source"] != source:
                        continue
                    score = len(words & set(doc["text"].lower().split()))
                    if score:
                        scored.append((-score, doc["id"]))
                return [doc_id for _, doc_id in sorted(scored)[:k]]


        # --- tests ---
        import pytest
        """,
        tests="""
        import pytest
        from lessontools import run_pytest, swap_impl
        good = run_pytest(__source__)
        assert good["failed"] == 0 and good["passed"] >= 5, good["output"][-800:]
        tests_part = __source__.split("# --- tests")[1]
        assert "def make_doc" in tests_part and "def store" in tests_part
        BASE = __source__.split("# --- code under test (do not edit) ---")[1].split("# --- tests")[0]
        BUGS = {
            "duplicates_overwrite": BASE.replace('            raise ValueError(f"duplicate id {doc[\\'id\\']}")\\n', "            pass\\n"),
            "get_returns_internal": BASE.replace("return dict(self._docs[doc_id])", "return self._docs[doc_id]"),
            "rank_ascending": BASE.replace("scored.append((-score, doc[\\"id\\"]))", "scored.append((score, doc[\\"id\\"]))"),
            "ignores_source": BASE.replace('if source is not None and doc["source"] != source:', "if False:"),
            "zero_scores_kept": BASE.replace("            if score:\\n", "            if True:\\n"),
        }
        assert all(b != BASE for b in BUGS.values()), [k for k, b in BUGS.items() if b == BASE]
        escaped = sorted(name for name, impl in BUGS.items() if run_pytest(swap_impl(__source__, impl))["failed"] == 0)
        assert escaped == []
        """,
        hints=["`@pytest.fixture def make_doc(): def _make(id=\"doc-1\", text=..., source=\"faq.md\"): return {...}; return _make`.",
               "Ranking: three documents sharing 3, 1 and 2 query words; a document sharing none must not appear. Mutating the returned dict must not change the store."],
        solution="""
        # --- code under test (do not edit) ---
        class DocumentStore:
            def __init__(self):
                self._docs = {}

            def add(self, doc):
                if doc["id"] in self._docs:
                    raise ValueError(f"duplicate id {doc['id']}")
                self._docs[doc["id"]] = dict(doc)

            def get(self, doc_id):
                return dict(self._docs[doc_id])

            def delete(self, doc_id):
                self._docs.pop(doc_id)

            def search(self, query, source=None, k=3):
                words = set(query.lower().split())
                scored = []
                for doc in self._docs.values():
                    if source is not None and doc["source"] != source:
                        continue
                    score = len(words & set(doc["text"].lower().split()))
                    if score:
                        scored.append((-score, doc["id"]))
                return [doc_id for _, doc_id in sorted(scored)[:k]]


        # --- tests ---
        import pytest


        @pytest.fixture
        def make_doc():
            def _make(id="doc-1", text="Refunds take 5 days", source="faq.md"):
                return {"id": id, "text": text, "source": source}
            return _make


        @pytest.fixture
        def store():
            return DocumentStore()


        def test_add_and_get_returns_a_copy(store, make_doc):
            store.add(make_doc())
            doc = store.get("doc-1")
            assert doc == make_doc()
            doc["text"] = "changed"
            assert store.get("doc-1")["text"] == "Refunds take 5 days"


        def test_duplicate_id_rejected(store, make_doc):
            store.add(make_doc())
            with pytest.raises(ValueError, match="duplicate"):
                store.add(make_doc(text="other"))
            assert store.get("doc-1")["text"] == "Refunds take 5 days"


        def test_delete(store, make_doc):
            store.add(make_doc())
            store.delete("doc-1")
            with pytest.raises(KeyError):
                store.get("doc-1")


        def test_search_ranks_by_shared_words(store, make_doc):
            store.add(make_doc(id="one", text="refund policy"))
            store.add(make_doc(id="three", text="refund policy for late delivery"))
            store.add(make_doc(id="two", text="late refund"))
            store.add(make_doc(id="none", text="shipping is free"))
            assert store.search("late refund policy delivery") == ["three", "one", "two"] or store.search("late refund policy delivery") == ["three", "two", "one"]
            assert store.search("late refund policy delivery", k=5)[0] == "three"
            assert "none" not in store.search("late refund policy delivery", k=5)


        def test_search_filters_by_source(store, make_doc):
            store.add(make_doc(id="faq", text="refund window", source="faq.md"))
            store.add(make_doc(id="terms", text="refund window", source="terms.md"))
            assert store.search("refund", source="terms.md") == ["terms"]
            assert store.search("refund") == ["faq", "terms"]
        """,
        why="""The factory fixture keeps one definition of a valid document, and each test passes only what matters to it (`id`, `text`, `source`), so a reader sees the
        relevant data at a glance; when the document shape changes, one function changes. Each test targets a behaviour a real store must guarantee and a mutant
        breaks: duplicates rejected without overwriting, `get` returning a copy so callers cannot corrupt the store, highest overlap first, documents with no
        overlap excluded rather than returned with score 0, and source filtering. Ties between documents with the same score are ordered by id in this
        implementation; a test that depended on an unspecified tie order would be fragile, which is why the ranking assertion only pins what the
        specification promises."""),
    write("A tiny fixture resolver", "hard", tag="Data work",
        prompt="""Write `run_with_fixtures(test_fn, fixtures)`: `fixtures` maps names to functions that may themselves take other fixtures as parameters, and may be
        plain functions (returning a value) or generator functions (yielding a value, with teardown after the yield). Inspect `test_fn`'s parameters
        (`inspect.signature`), resolve each fixture recursively (each fixture created at most once per call), call the test, then run teardowns in reverse order
        of setup, even if the test raised (re-raise its exception after cleanup). Return the test's return value. Unknown fixture names raise `LookupError`.""",
        code="""
        import inspect

        def run_with_fixtures(test_fn, fixtures):
            pass
        """,
        tests="""
        events = []

        def config():
            events.append("config")
            return {"model": "small"}

        def client(config):
            events.append("client open")
            yield f"client({config['model']})"
            events.append("client close")

        def cache(config):
            events.append("cache open")
            yield {}
            events.append("cache close")

        FIX = {"config": config, "client": client, "cache": cache}

        def test_ok(client, cache, config):
            events.append("test")
            return client, cache, config["model"]

        assert run_with_fixtures(test_ok, FIX) == ("client(small)", {}, "small")
        assert events == ["config", "client open", "cache open", "test", "cache close", "client close"]
        events.clear()

        def test_fails(cache):
            raise AssertionError("boom")

        try:
            run_with_fixtures(test_fails, FIX)
            assert False
        except AssertionError as e:
            assert str(e) == "boom"
        assert events == ["config", "cache open", "cache close"]
        try:
            run_with_fixtures(lambda db: None, FIX)
            assert False
        except LookupError as e:
            assert "db" in str(e)
        """,
        hints=["A recursive `resolve(name)` with a `cache` dict: look up the function, resolve its own parameters first, call it.",
               "If `inspect.isgeneratorfunction(fn)`, call it, take `next(gen)` as the value and push `gen` on a teardown stack; teardown with `next(gen, None)`."],
        solution="""
        import inspect


        def run_with_fixtures(test_fn, fixtures):
            cache, teardown = {}, []

            def resolve(name):
                if name in cache:
                    return cache[name]
                if name not in fixtures:
                    raise LookupError(f"fixture {name!r} not found")
                fn = fixtures[name]
                kwargs = {p: resolve(p) for p in inspect.signature(fn).parameters}
                if inspect.isgeneratorfunction(fn):
                    gen = fn(**kwargs)
                    value = next(gen)
                    teardown.append(gen)
                else:
                    value = fn(**kwargs)
                cache[name] = value
                return value

            try:
                kwargs = {p: resolve(p) for p in inspect.signature(test_fn).parameters}
                return test_fn(**kwargs)
            finally:
                for gen in reversed(teardown):
                    next(gen, None)
        """,
        why="""This is pytest's fixture mechanism reduced to its core. Parameters are read with `inspect.signature`, and each name is resolved by building its own
        dependencies first, so `config` is created before `client` and `cache` even though the test lists it last, and only once, thanks to the per-call cache
        (pytest's function scope). Generator fixtures are advanced to their `yield` for the value and kept on a stack; the `finally` then finishes them in
        reverse order, so the cache closes before the client that was opened earlier, exactly the order of teardown in the warm-up. Because cleanup sits in
        `finally`, a failing test still releases its resources and its own exception propagates. pytest adds scopes (a cache per module or session), errors
        during setup, and plugins, but the idea is this one: dependency injection by parameter name."""),
    fix("Read the code: tests that touch the real world", "hard", tag="GenAI",
        prompt="""This test module passes on its author's laptop and breaks elsewhere. It writes `cache.json` into the current folder, sets `os.environ` directly and never
        restores it, replaces `sys.stdout` by hand, and one test relies on a file the previous test created. Rewrite the tests using `tmp_path`, `monkeypatch`
        and `capsys` so each test is isolated and passes alone, keeping what they check.""",
        code="""
        # --- code under test (do not edit) ---
        import json, os


        def save_cache(path, data):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f)
            print(f"cached {len(data)} answers")


        def load_cache(path):
            if not os.path.exists(path):
                return {}
            with open(path, encoding="utf-8") as f:
                return json.load(f)


        def cache_path():
            return os.path.join(os.environ.get("CACHE_DIR", "."), "cache.json")


        # --- tests ---
        import io, os, sys
        import pytest


        def test_save():
            old = sys.stdout
            sys.stdout = io.StringIO()
            save_cache("cache.json", {"q1": "5 days"})
            out = sys.stdout.getvalue()
            sys.stdout = old
            assert out == "cached 1 answers\\n"


        def test_load_existing():
            assert load_cache("cache.json") == {"q1": "5 days"}


        def test_cache_dir():
            os.environ["CACHE_DIR"] = "/tmp/answers"
            assert cache_path() == "/tmp/answers/cache.json"
        """,
        tests="""
        import os, pytest
        from lessontools import run_pytest
        tests_part = __source__.split("# --- tests")[1]
        os.environ.pop("CACHE_DIR", None)
        r = run_pytest(__source__)
        assert r["failed"] == 0 and r["passed"] >= 3, r["output"][-800:]
        assert "CACHE_DIR" not in os.environ, "a test left CACHE_DIR set"
        alone = run_pytest(__source__, args=["-k", "load"])
        assert alone["failed"] == 0 and alone["passed"] >= 1, alone["output"][-600:]
        assert "sys.stdout =" not in tests_part and "os.environ[" not in tests_part and '_cache("cache.json"' not in tests_part
        assert "tmp_path" in tests_part and "monkeypatch" in tests_part and "capsys" in tests_part
        """,
        hints=["Each test builds its own path with `tmp_path / \"cache.json\"`; the load test saves its own file first.",
               "`monkeypatch.setenv(\"CACHE_DIR\", str(tmp_path))` and compare with `str(tmp_path / \"cache.json\")`; `capsys.readouterr().out` replaces the manual stdout swap."],
        solution="""
        # --- code under test (do not edit) ---
        import json, os


        def save_cache(path, data):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f)
            print(f"cached {len(data)} answers")


        def load_cache(path):
            if not os.path.exists(path):
                return {}
            with open(path, encoding="utf-8") as f:
                return json.load(f)


        def cache_path():
            return os.path.join(os.environ.get("CACHE_DIR", "."), "cache.json")


        # --- tests ---
        import os
        import pytest


        @pytest.fixture
        def path(tmp_path):
            return tmp_path / "cache.json"


        def test_save_prints_count(path, capsys):
            save_cache(path, {"q1": "5 days"})
            assert capsys.readouterr().out == "cached 1 answers\\n"


        def test_load_existing(path):
            save_cache(path, {"q1": "5 days"})
            assert load_cache(path) == {"q1": "5 days"}


        def test_load_missing_returns_empty(path):
            assert load_cache(path) == {}


        def test_cache_dir_from_env(tmp_path, monkeypatch):
            monkeypatch.setenv("CACHE_DIR", str(tmp_path))
            assert cache_path() == os.path.join(str(tmp_path), "cache.json")
        """,
        why="""Each original test leaked into the world. Writing `cache.json` in the current folder litters the repository, can collide with a real cache, and made
        `test_load_existing` depend on `test_save` having run first; `tmp_path` gives every test its own folder, so the load test creates what it needs. Setting
        `os.environ` directly changed the environment for every later test in the process (and the grader checked that nothing was left behind); `monkeypatch`
        restores it. Swapping `sys.stdout` by hand is fragile (an exception before the restore leaves output broken for the rest of the run) and `capsys` does
        it safely. The added missing-file test covers the branch the old suite never reached."""),
    predict("Errors in setup and teardown", "hard",
        code="""
        from lessontools import run_pytest

        SRC = '''
        import pytest

        @pytest.fixture
        def broken_setup():
            raise RuntimeError("cannot connect")
            yield

        @pytest.fixture
        def broken_teardown():
            yield "ok"
            raise RuntimeError("cannot disconnect")

        def test_needs_setup(broken_setup):
            assert True

        def test_needs_teardown(broken_teardown):
            assert broken_teardown == "ok"

        def test_fails_and_teardown_fails(broken_teardown):
            assert False

        def test_unknown_fixture(no_such_fixture):
            pass
        '''
        r = run_pytest(SRC)
        for name, outcome in r["outcomes"].items():
            print(f"{outcome:6} {name}")
        print(r["passed"], r["failed"], "errors" in r["output"] or "error" in r["output"])
        """,
        hints=["A failure during setup or teardown is reported as an error, not a failure. On this site, `outcomes` shows the last phase that went wrong."],
        why="""When setup raises, the test body never runs and pytest reports an **error**, which tells you to look at the fixture rather than the code under test; an
        unknown fixture name is also a setup error. A teardown failure is reported as an error too, even when the test itself passed, so one test can show up as
        "passed" and "error" in pytest's summary; `run_pytest` keeps the worst phase. The last line counts the error outcomes among the failures, which is why
        all four tests count as failing even though one body passed."""),
)

section("interview", "Interview questions",
    explain("What are pytest fixtures, and why are they better than setup and teardown methods?", "medium", tag="Interview",
        why="""A fixture is a function that provides a test dependency, requested by naming it as a parameter; pytest builds it, injects it, and (for `yield` fixtures) runs
        the cleanup after the test. Compared with `setUp`/`tearDown` methods in `unittest`, fixtures are **explicit** (each test lists what it uses, so unused
        setup is not run and readers see the dependencies), **composable** (fixtures use other fixtures, building complex setup from small parts),
        **scoped** (function, class, module or session, so expensive resources can be shared deliberately), **parametrisable** (run the same tests against several
        configurations), and **shareable** across files through `conftest.py` without inheritance. Teardown lives next to setup in one function, with
        guaranteed execution after the test. Built-in fixtures (`tmp_path`, `monkeypatch`, `capsys`, `caplog`) cover the common isolation needs."""),
    explain("How do you keep tests isolated when the code reads files, environment variables and global state?", "medium", tag="Interview",
        why="""Give every test its own world and undo every change. Files: write only inside `tmp_path` (or `tmp_path_factory` for wider scopes), never in the repository
        or the current folder, and make code accept paths as parameters so tests can point it there. Environment: set and remove variables with `monkeypatch.setenv`
        and `delenv`, and start from a known state by deleting the variables the code reads, so the developer's real environment cannot change results. Global
        state (module-level caches, singletons, registries, logging configuration): reset it in a fixture, often `autouse`, or patch it with `monkeypatch.setattr`;
        better still, design code to receive dependencies instead of reaching for globals. Time and randomness: inject a clock and a seeded generator. Then
        verify isolation by running tests alone, in random order (`pytest-randomly`) and in parallel (`pytest-xdist`)."""),
    explain("When would you use a session-scoped fixture, and what can go wrong?", "hard", tag="Interview",
        why="""Use session scope for expensive resources that many tests need and that can be shared safely: starting a database or message-broker container (for example with
        Testcontainers), creating a schema, loading a tokenizer, an embedding model or a large reference dataset, or building a test application once. The risks
        come from sharing. Mutable shared objects make tests order-dependent, so expose them read-only, hand each test a copy, or pair the session resource with a
        function-scoped fixture that isolates each test, such as a transaction rolled back after every test or a fresh database per test created from a template.
        Session fixtures are created lazily on first use and torn down at the very end, so failures in their teardown are reported late, and with `pytest-xdist`
        each worker process gets its own "session", so cross-process resources (ports, files, database names) must be made unique per worker. Finally, slow
        session setup still costs time on every run; keep heavy fixtures behind marks so the fast unit suite does not pay for them."""),
)

recap(
    "A fixture is a function marked `@pytest.fixture`; a test receives it by naming a parameter, and fixtures can depend on other fixtures.",
    "Code after `yield` is teardown and runs even when the test fails; setup and teardown failures are reported as errors.",
    "Scopes (`function`, `class`, `module`, `session`) share objects; never let tests mutate a widely scoped fixture, copy or reset it instead.",
    "Parametrised fixtures run tests per configuration; factory fixtures return functions with defaults; `conftest.py` shares fixtures.",
    "`tmp_path`, `monkeypatch`, `capsys` and `caplog` isolate files, environment and attributes, output, and logs.",
)
