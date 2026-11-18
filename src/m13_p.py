from lesson import *
from diagrams import *

lesson(
    id="m13-p", num="13.P", title="Module 13 practice set and mini project",
    intro="Mixed problems from all of Module 13: pytest basics, fixtures, mocking, and testing ML and LLM code. Then a mini project "
          "that needs all of it: a complete test suite for a RAG answer service with a cache, a retriever, a model client and a "
          "clock, graded against ten realistic bugs.",
    desc="Mixed problems from the whole module, then one small program that uses all of it.",
    keys="practice mixed review project test suite rag answer service cache retriever mock fake clock caplog tmp_path parametrize fixture snapshot golden mock_open patch.dict regex match",
)

section("how", "How to use this page",
    fig(stage_map(13, "a test suite for a RAG answer service"), "Module 13 at a glance: pytest basics, fixtures, test doubles and testing ML code, building up to a full test suite."),
    p("""Before writing a test, ask what would make it **fail**. Pick inputs that separate correct behaviour from plausible mistakes (13.1); give each test its own
    world through fixtures, `tmp_path` and `monkeypatch` (13.2); replace slow or random dependencies with fakes and mocks that match the real interface, and
    patch where names are looked up (13.3); and for numbers, randomness and models, test tolerances, seeds, properties and behaviour, leaving quality to
    evaluation (13.4)."""),
    p("""The problems mix the lessons on purpose, and the mini project combines all four: it is the test suite you would be expected to write for a small production
    service."""),
)

section("set", "Practice set",
    predict("Fixtures, parametrize and mocks together", "easy",
        code="""
        from lessontools import run_pytest

        SRC = '''
        import pytest
        from unittest.mock import Mock

        @pytest.fixture
        def llm():
            m = Mock()
            m.complete.side_effect = lambda p: "SPAM" if "prize" in p else "ham"
            return m

        @pytest.mark.parametrize("text,label", [("win a prize", "spam"), ("lunch?", "ham")])
        def test_label(llm, text, label):
            assert llm.complete(text).lower() == label
            assert llm.complete.call_count == 1

        def test_fresh_mock(llm):
            assert llm.complete.call_count == 0
            llm.complete("x")
            llm.complete.assert_called_once_with("x")

        def test_wrong_assert(llm):
            llm.complete("a")
            llm.complete("b")
            llm.complete.assert_called_once_with("b")
        '''
        print(run_pytest(SRC)["outcomes"])
        """,
        hints=["A function-scoped fixture builds a new mock for every test, including every parametrised case."],
        why="""Each parametrised case gets its own fixture instance, so the call count is 1 in both. `test_fresh_mock` sees a mock with no history for the same reason. In
        `test_wrong_assert`, the mock was called twice, so `assert_called_once_with` fails even though the last call matches: it checks both the count and the
        arguments."""),
    write("Test an e-mail normaliser", "easy", tag="Data work",
        prompt="""`normalize_email(raw)` strips whitespace, lower-cases the whole address, removes a `+tag` from the local part, removes dots from the local part only for
        `gmail.com` addresses, and raises `ValueError` for anything without exactly one `@` or with an empty local part or domain. Write at least five tests that
        pass here and catch five buggy versions.""",
        code="""
        # --- code under test (do not edit) ---
        def normalize_email(raw):
            email = raw.strip().lower()
            if email.count("@") != 1:
                raise ValueError(f"invalid e-mail {raw!r}")
            local, domain = email.split("@")
            if not local or not domain:
                raise ValueError(f"invalid e-mail {raw!r}")
            local = local.split("+", 1)[0]
            if domain == "gmail.com":
                local = local.replace(".", "")
            return f"{local}@{domain}"


        # --- tests ---
        import pytest
        """,
        tests="""
        import pytest
        from lessontools import run_pytest, swap_impl
        good = run_pytest(__source__)
        assert good["failed"] == 0 and good["passed"] >= 5, good["output"][-800:]
        BASE = __source__.split("# --- code under test (do not edit) ---")[1].split("# --- tests")[0]
        BUGS = {
            "no_strip": BASE.replace("raw.strip().lower()", "raw.lower()"),
            "dots_everywhere": BASE.replace('    if domain == "gmail.com":\\n        local = local.replace(".", "")', '    local = local.replace(".", "")'),
            "tag_kept": BASE.replace('    local = local.split("+", 1)[0]\\n', ""),
            "two_ats_ok": BASE.replace('if email.count("@") != 1:', 'if "@" not in email:').replace('local, domain = email.split("@")', 'local, domain = email.split("@", 1)'),
            "domain_case_kept": BASE.replace("email = raw.strip().lower()", "email = raw.strip()").replace('local = local.split("+", 1)[0]', 'local = local.lower().split("+", 1)[0]'),
        }
        assert all(b != BASE for b in BUGS.values()), [k for k, b in BUGS.items() if b == BASE]
        escaped = sorted(name for name, impl in BUGS.items() if run_pytest(swap_impl(__source__, impl))["failed"] == 0)
        assert escaped == []
        """,
        hints=["A parametrised table of `(raw, expected)` pairs, plus a parametrised table of invalid inputs for `pytest.raises`.",
               "Include a non-Gmail address with dots in the local part, an upper-case domain, surrounding spaces and two `@` signs."],
        solution="""
        # --- code under test (do not edit) ---
        def normalize_email(raw):
            email = raw.strip().lower()
            if email.count("@") != 1:
                raise ValueError(f"invalid e-mail {raw!r}")
            local, domain = email.split("@")
            if not local or not domain:
                raise ValueError(f"invalid e-mail {raw!r}")
            local = local.split("+", 1)[0]
            if domain == "gmail.com":
                local = local.replace(".", "")
            return f"{local}@{domain}"


        # --- tests ---
        import pytest


        @pytest.mark.parametrize("raw,expected", [
            ("  Ana.Lee@Shop.IO ", "ana.lee@shop.io"),
            ("ana.lee+news@gmail.com", "analee@gmail.com"),
            ("bo+promo@shop.io", "bo@shop.io"),
            ("CY@EXAMPLE.COM", "cy@example.com"),
        ])
        def test_normalises(raw, expected):
            assert normalize_email(raw) == expected


        @pytest.mark.parametrize("raw", ["no-at-sign", "a@b@c.io", "@shop.io", "ana@", ""])
        def test_rejects_invalid(raw):
            with pytest.raises(ValueError, match="invalid e-mail"):
                normalize_email(raw)
        """,
        why="""Two tables cover the whole specification: valid inputs paired with their exact normal form, and invalid inputs that must raise. Each row is chosen to separate the
        correct rule from a plausible wrong one: the non-Gmail address with dots shows that dots are removed only for Gmail, the upper-case domain shows the whole
        address is lower-cased, the spaces show stripping, and two `@` signs show the exact-count check. E-mail normalisation decides whether two accounts are the
        same customer, so its bugs merge or split identities in every downstream dataset."""),
    fix("A timing test that sleeps", "easy", tag="GenAI",
        prompt="""`Stopwatch` measures the latency of model calls. Its test really sleeps for 0.2 seconds and checks the measured time with a loose range, so it is slow and can
        fail on a busy machine. `Stopwatch` already accepts a `clock`; rewrite the test with a fake clock so it is instant and checks exact values, including that
        `stop()` without `start()` raises `RuntimeError`.""",
        code="""
        # --- code under test (do not edit) ---
        import time


        class Stopwatch:
            def __init__(self, clock=time.perf_counter):
                self.clock = clock
                self._start = None

            def start(self):
                self._start = self.clock()

            def stop(self):
                if self._start is None:
                    raise RuntimeError("stop() before start()")
                elapsed_ms = round((self.clock() - self._start) * 1000)
                self._start = None
                return elapsed_ms


        # --- tests ---
        import time


        def test_measures_elapsed():
            sw = Stopwatch()
            sw.start()
            time.sleep(0.2)
            assert 150 <= sw.stop() <= 400
        """,
        tests="""
        import pytest
        from lessontools import run_pytest, swap_impl
        tests_part = __source__.split("# --- tests")[1]
        assert "sleep" not in tests_part
        good = run_pytest(__source__)
        assert good["failed"] == 0 and good["passed"] >= 2, good["output"][-800:]
        BASE = __source__.split("# --- code under test (do not edit) ---")[1].split("# --- tests")[0]
        BUGS = {
            "seconds": BASE.replace("round((self.clock() - self._start) * 1000)", "round(self.clock() - self._start)"),
            "no_reset": BASE.replace("        self._start = None\\n        return elapsed_ms", "        return elapsed_ms"),
            "no_guard": BASE.replace('        if self._start is None:\\n            raise RuntimeError("stop() before start()")\\n', ""),
        }
        assert all(b != BASE for b in BUGS.values()), [k for k, b in BUGS.items() if b == BASE]
        escaped = sorted(name for name, impl in BUGS.items() if run_pytest(swap_impl(__source__, impl))["failed"] == 0)
        assert escaped == []
        """,
        hints=["`times = iter([10.0, 10.25])` and `Stopwatch(clock=lambda: next(times))`, or a `Mock(side_effect=[...])`.",
               "After one measurement, a second `stop()` without a new `start()` must raise."],
        solution="""
        # --- code under test (do not edit) ---
        import time


        class Stopwatch:
            def __init__(self, clock=time.perf_counter):
                self.clock = clock
                self._start = None

            def start(self):
                self._start = self.clock()

            def stop(self):
                if self._start is None:
                    raise RuntimeError("stop() before start()")
                elapsed_ms = round((self.clock() - self._start) * 1000)
                self._start = None
                return elapsed_ms


        # --- tests ---
        import pytest
        from unittest.mock import Mock


        def test_measures_elapsed_in_ms():
            sw = Stopwatch(clock=Mock(side_effect=[10.0, 10.25]))
            sw.start()
            assert sw.stop() == 250


        def test_stop_without_start_raises():
            with pytest.raises(RuntimeError):
                Stopwatch(clock=Mock(return_value=0.0)).stop()


        def test_stop_resets():
            sw = Stopwatch(clock=Mock(side_effect=[1.0, 1.5]))
            sw.start()
            sw.stop()
            with pytest.raises(RuntimeError):
                sw.stop()
        """,
        why="""Sleeping makes a test slow (a suite of such tests takes minutes) and still flaky, because a loaded CI machine can oversleep beyond the range, and the range is so
        loose that a version measuring in seconds instead of milliseconds would only fail by luck. Feeding the clock exact values makes the expected result exact:
        0.25 seconds is 250 milliseconds, and the seconds mutant returns 0. The same injection lets the tests cover the state rules (no stop before start, reset
        after stop) instantly."""),
    predict("patch.dict and os.environ", "medium",
        code="""
        import os
        from unittest.mock import patch

        os.environ["P4_KEEP"] = "1"
        os.environ.pop("P4_NEW", None)
        with patch.dict(os.environ, {"P4_NEW": "x", "P4_KEEP": "2"}):
            inside = (os.environ["P4_NEW"], os.environ["P4_KEEP"])
        print(inside, os.environ.get("P4_NEW"), os.environ["P4_KEEP"])
        with patch.dict(os.environ, {"ONLY": "this"}, clear=True):
            print(len(os.environ), "P4_KEEP" in os.environ)
        print("P4_KEEP" in os.environ, "ONLY" in os.environ)

        @patch.dict(os.environ, {"P4_DECORATED": "yes"})
        def read():
            return os.environ["P4_DECORATED"]
        print(read(), "P4_DECORATED" in os.environ)
        """,
        hints=["`patch.dict` adds or overrides entries and restores the original dict afterwards; `clear=True` empties it first."],
        why="""Inside the block the new variable exists and the existing one is overridden; afterwards both are restored exactly. With `clear=True`, the environment holds only
        the patched entries during the block, a quick way to test "nothing configured" behaviour, and everything comes back after it. As a decorator, the patch
        applies only while the function runs. `monkeypatch.setenv` does the same inside pytest tests."""),
    write("Test context truncation with a fake tokenizer", "medium", tag="GenAI",
        prompt="""`fit_context(chunks, budget, count_tokens)` keeps chunks in order while their total token count fits the budget, stops at the first chunk that does not fit
        (it does not skip ahead), and returns `(kept, used_tokens)`. Write at least four tests using a simple **fake tokenizer** (for example one token per word)
        that pass here and catch four buggy versions.""",
        code="""
        # --- code under test (do not edit) ---
        def fit_context(chunks, budget, count_tokens):
            kept, used = [], 0
            for chunk in chunks:
                n = count_tokens(chunk)
                if used + n > budget:
                    break
                kept.append(chunk)
                used += n
            return kept, used


        # --- tests ---
        import pytest
        """,
        tests="""
        import pytest
        from lessontools import run_pytest, swap_impl
        good = run_pytest(__source__)
        assert good["failed"] == 0 and good["passed"] >= 4, good["output"][-800:]
        BASE = __source__.split("# --- code under test (do not edit) ---")[1].split("# --- tests")[0]
        BUGS = {
            "skips_ahead": BASE.replace("            break\\n", "            continue\\n"),
            "strict_budget": BASE.replace("if used + n > budget:", "if used + n >= budget:"),
            "counts_chars": BASE.replace("n = count_tokens(chunk)", "n = len(chunk)"),
            "used_wrong": BASE.replace("    return kept, used", "    return kept, budget"),
        }
        assert all(b != BASE for b in BUGS.values()), [k for k, b in BUGS.items() if b == BASE]
        escaped = sorted(name for name, impl in BUGS.items() if run_pytest(swap_impl(__source__, impl))["failed"] == 0)
        assert escaped == []
        """,
        hints=["`def words(text): return len(text.split())` as the tokenizer.",
               "Cases: everything fits, an exact fit at the budget, a big chunk followed by a small one (must stop, not skip), and the `used` count."],
        solution="""
        # --- code under test (do not edit) ---
        def fit_context(chunks, budget, count_tokens):
            kept, used = [], 0
            for chunk in chunks:
                n = count_tokens(chunk)
                if used + n > budget:
                    break
                kept.append(chunk)
                used += n
            return kept, used


        # --- tests ---
        import pytest


        def words(text):
            return len(text.split())


        def test_everything_fits():
            assert fit_context(["a b", "c"], 10, words) == (["a b", "c"], 3)


        def test_exact_fit_is_allowed():
            assert fit_context(["a b c", "d e"], 5, words) == (["a b c", "d e"], 5)


        def test_stops_at_first_chunk_that_does_not_fit():
            chunks = ["one two", "three four five six", "seven"]
            assert fit_context(chunks, 4, words) == (["one two"], 2)


        def test_uses_the_given_tokenizer():
            assert fit_context(["aaaaaaaaaa"], 1, words) == (["aaaaaaaaaa"], 1)


        def test_empty_budget():
            assert fit_context(["a"], 0, words) == ([], 0)
        """,
        why="""The tokenizer is a dependency, so the tests inject a fake that is trivial to reason about (one token per word) instead of a real tokenizer whose counts would
        have to be looked up. Each case pins one decision: an exact fit is allowed (`>` not `>=`), the loop stops instead of skipping to a later small chunk
        (chunks are ranked by relevance, so skipping would put a less relevant chunk ahead of a more relevant, larger one), the count comes from the tokenizer
        and not from characters (a ten-letter word is one "token" here), and the returned total is the real one. Context packing bugs silently waste tokens or
        drop the best evidence."""),
    fix("A raises test whose pattern is a regex", "medium", tag="Data work",
        prompt="""`check_budget(cost, limit)` raises `ValueError("cost ($12.50) exceeds limit ($10.00)")`-style messages. The test's `match=` string is the literal message,
        but `match` is a **regular expression**, where `(`, `$` and `.` mean something else, so the test fails on correct code. Fix the test so it matches the
        literal text, and keep it strict enough to catch the graded buggy version (which reports the limit in the place of the cost).""",
        code="""
        # --- code under test (do not edit) ---
        def check_budget(cost, limit):
            if cost > limit:
                raise ValueError(f"cost (${cost:.2f}) exceeds limit (${limit:.2f})")
            return limit - cost


        # --- tests ---
        import pytest


        def test_over_budget():
            with pytest.raises(ValueError, match="cost ($12.50) exceeds limit ($10.00)"):
                check_budget(12.5, 10)


        def test_within_budget():
            assert check_budget(4, 10) == 6
        """,
        tests="""
        import pytest
        from lessontools import run_pytest, swap_impl
        good = run_pytest(__source__)
        assert good["failed"] == 0 and good["passed"] >= 2, good["output"][-800:]
        BUG = '''
        def check_budget(cost, limit):
            if cost > limit:
                raise ValueError(f"cost (${limit:.2f}) exceeds limit (${limit:.2f})")
            return limit - cost
        '''
        assert run_pytest(swap_impl(__source__, BUG))["failed"] > 0
        """,
        hints=["`match=re.escape(\"cost ($12.50) exceeds limit ($10.00)\")`, or check `str(excinfo.value) == ...` after the block."],
        solution="""
        # --- code under test (do not edit) ---
        def check_budget(cost, limit):
            if cost > limit:
                raise ValueError(f"cost (${cost:.2f}) exceeds limit (${limit:.2f})")
            return limit - cost


        # --- tests ---
        import re
        import pytest


        def test_over_budget():
            with pytest.raises(ValueError, match=re.escape("cost ($12.50) exceeds limit ($10.00)")):
                check_budget(12.5, 10)


        def test_within_budget():
            assert check_budget(4, 10) == 6
        """,
        why="""`match` runs `re.search(pattern, str(exception))`. In the literal message, `(` and `)` form a group, `$` means "end of string" and `.` matches any character, so
        the pattern could never match a message that continues after `$`, and the test failed on correct code. `re.escape` turns the text into a pattern that matches
        it literally. An alternative that avoids regular expressions entirely is `with pytest.raises(ValueError) as excinfo:` followed by `assert
        str(excinfo.value) == "..."`, which is also stricter, since `search` would accept the text anywhere in a longer message."""),
    write("Test a confusion matrix", "medium", tag="ML",
        prompt="""`confusion_matrix(y_true, y_pred, labels)` returns a list of lists where `matrix[i][j]` counts examples whose true label is `labels[i]` and predicted label is
        `labels[j]`; predictions with labels outside `labels` raise `ValueError`. Write at least four tests that pass here and catch four buggy versions.""",
        code="""
        # --- code under test (do not edit) ---
        def confusion_matrix(y_true, y_pred, labels):
            index = {label: i for i, label in enumerate(labels)}
            matrix = [[0] * len(labels) for _ in labels]
            for t, p in zip(y_true, y_pred, strict=True):
                if t not in index or p not in index:
                    raise ValueError(f"unknown label in ({t!r}, {p!r})")
                matrix[index[t]][index[p]] += 1
            return matrix


        # --- tests ---
        import pytest
        """,
        tests="""
        import pytest
        from lessontools import run_pytest, swap_impl
        good = run_pytest(__source__)
        assert good["failed"] == 0 and good["passed"] >= 4, good["output"][-800:]
        BASE = __source__.split("# --- code under test (do not edit) ---")[1].split("# --- tests")[0]
        BUGS = {
            "transposed": BASE.replace("matrix[index[t]][index[p]] += 1", "matrix[index[p]][index[t]] += 1"),
            "shared_rows": BASE.replace("[[0] * len(labels) for _ in labels]", "[[0] * len(labels)] * len(labels)"),
            "unknown_ignored": BASE.replace('            raise ValueError(f"unknown label in ({t!r}, {p!r})")', "            continue"),
            "length_mismatch_ok": BASE.replace("zip(y_true, y_pred, strict=True)", "zip(y_true, y_pred)"),
        }
        assert all(b != BASE for b in BUGS.values()), [k for k, b in BUGS.items() if b == BASE]
        escaped = sorted(name for name, impl in BUGS.items() if run_pytest(swap_impl(__source__, impl))["failed"] == 0)
        assert escaped == []
        """,
        hints=["Use an asymmetric case, where `spam` predicted as `ham` and `ham` predicted as `spam` happen a different number of times, so a transposed matrix differs.",
               "`zip(..., strict=True)` raises `ValueError` for different lengths: test that too."],
        solution="""
        # --- code under test (do not edit) ---
        def confusion_matrix(y_true, y_pred, labels):
            index = {label: i for i, label in enumerate(labels)}
            matrix = [[0] * len(labels) for _ in labels]
            for t, p in zip(y_true, y_pred, strict=True):
                if t not in index or p not in index:
                    raise ValueError(f"unknown label in ({t!r}, {p!r})")
                matrix[index[t]][index[p]] += 1
            return matrix


        # --- tests ---
        import pytest

        LABELS = ["spam", "ham"]


        def test_asymmetric_errors():
            y_true = ["spam", "spam", "spam", "ham", "ham"]
            y_pred = ["spam", "ham", "ham", "spam", "ham"]
            assert confusion_matrix(y_true, y_pred, LABELS) == [[1, 2], [1, 1]]


        def test_perfect_predictions_are_diagonal():
            assert confusion_matrix(["ham", "spam", "ham"], ["ham", "spam", "ham"], LABELS) == [[1, 0], [0, 2]]


        def test_rows_follow_label_order():
            assert confusion_matrix(["spam"], ["ham"], ["ham", "spam"]) == [[0, 0], [1, 0]]


        def test_unknown_label_raises():
            with pytest.raises(ValueError, match="unknown label"):
                confusion_matrix(["spam"], ["phish"], LABELS)


        def test_length_mismatch_raises():
            with pytest.raises(ValueError):
                confusion_matrix(["spam", "ham"], ["spam"], LABELS)
        """,
        why="""An **asymmetric** example is essential: if spam-as-ham and ham-as-spam occurred equally often, a transposed matrix would look identical. The diagonal test exposes
        the classic list-multiplication bug, where every row is the same list object, so one increment shows up in all rows (2.4). Swapping the label order checks
        that rows and columns follow `labels`. The error tests pin the strictness: silently ignoring unknown labels or mismatched lengths would produce a matrix that
        looks plausible and hides a data problem."""),
    write("A snapshot helper", "hard", tag="GenAI",
        prompt="""Write `snapshot(name, value, folder, update=False)` for golden-file tests. It stores `value` as pretty JSON (`indent=2`, sorted keys) in `folder / f"{name}.json"`.
        If the file does not exist, or `update` is true, it writes the file and returns `"written"`. Otherwise it compares: equal values return `"matched"`; different
        values raise `AssertionError` whose message starts with `f"snapshot {name!r} changed"` and, for dicts, lists the added, removed and changed top-level keys
        (`"added: ..."`, `"removed: ..."`, `"changed: ..."`, each comma-separated and sorted, omitted when empty).""",
        code="""
        import json
        from pathlib import Path

        def snapshot(name, value, folder, update=False):
            pass
        """,
        tests="""
        import json, tempfile
        from pathlib import Path
        folder = Path(tempfile.mkdtemp())
        prompt = {"system": "You answer support questions.", "max_tokens": 200, "stop": ["\\n\\n"]}
        assert snapshot("qa_prompt", prompt, folder) == "written"
        assert json.loads((folder / "qa_prompt.json").read_text(encoding="utf-8")) == prompt
        assert snapshot("qa_prompt", dict(prompt), folder) == "matched"
        changed = {"system": "You are a support assistant.", "max_tokens": 200, "temperature": 0.2}
        try:
            snapshot("qa_prompt", changed, folder)
            assert False
        except AssertionError as e:
            msg = str(e)
            assert msg.startswith("snapshot 'qa_prompt' changed") and "added: temperature" in msg and "removed: stop" in msg and "changed: system" in msg
            assert "max_tokens" not in msg
        assert snapshot("qa_prompt", changed, folder, update=True) == "written" and snapshot("qa_prompt", changed, folder) == "matched"
        assert snapshot("chunks", ["a", "b"], folder) == "written"
        try:
            snapshot("chunks", ["a"], folder)
            assert False
        except AssertionError as e:
            assert str(e).startswith("snapshot 'chunks' changed")
        assert (folder / "qa_prompt.json").read_text(encoding="utf-8").startswith('{\\n  "max_tokens"')
        """,
        hints=["Compare after a JSON round trip (`json.loads(json.dumps(value))`), so tuples and lists compare the same way as when stored.",
               "For dicts, use set operations on the keys: `new.keys() - old.keys()` and so on."],
        solution="""
        import json
        from pathlib import Path


        def snapshot(name, value, folder, update=False):
            path = Path(folder) / f"{name}.json"
            text = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False)
            if update or not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text + "\\n", encoding="utf-8")
                return "written"
            old = json.loads(path.read_text(encoding="utf-8"))
            new = json.loads(text)
            if old == new:
                return "matched"
            parts = [f"snapshot {name!r} changed"]
            if isinstance(old, dict) and isinstance(new, dict):
                added = sorted(new.keys() - old.keys())
                removed = sorted(old.keys() - new.keys())
                changed = sorted(k for k in old.keys() & new.keys() if old[k] != new[k])
                for label, keys in (("added", added), ("removed", removed), ("changed", changed)):
                    if keys:
                        parts.append(f"{label}: {', '.join(keys)}")
            raise AssertionError("; ".join(parts))
        """,
        why="""Snapshot tests suit outputs that are large and structured and should change only deliberately: rendered prompts, request payloads sent to a model API, tool schemas,
        exported reports. The first run records the golden file, later runs compare, and an explicit `update` flag (usually a command-line option such as
        `--snapshot-update` in tools like syrupy) re-records after a reviewed change; the file lives in git, so the change shows up in code review. Sorted keys and
        indentation keep the files diff-friendly, comparing after a JSON round trip avoids false alarms from tuples versus lists, and a message that names added,
        removed and changed keys says what moved without a manual diff. Their weakness is that people update snapshots without reading them, so keep them small."""),
    predict("mock_open and MagicMock protocols", "hard",
        code="""
        from unittest.mock import MagicMock, mock_open, patch

        def first_line(path):
            with open(path, encoding="utf-8") as f:
                return f.readline().strip()

        def count_lines(path):
            with open(path, encoding="utf-8") as f:
                return sum(1 for _ in f)

        m = mock_open(read_data="header\\nrow1\\nrow2\\n")
        with patch("builtins.open", m):
            print(first_line("data.csv"), count_lines("data.csv"))
        m.assert_called_with("data.csv", encoding="utf-8")
        print(m.call_count)

        cm = MagicMock()
        cm.__enter__.return_value = "resource"
        with cm as r:
            print(r)
        print(cm.__exit__.call_count, len(MagicMock()))
        """,
        hints=["`mock_open` returns a mock that behaves like `open`: each call yields a fresh handle reading `read_data`, supporting `readline`, iteration and `with`."],
        why="""`mock_open` simulates a text file, so code that reads lines or iterates works unchanged, and each call to the patched `open` starts reading from the beginning
        again, which is why both functions see the same content. The mock records the calls like any other, two here. A `MagicMock` supports the context-manager
        protocol: `__enter__`'s return value is what `as` receives, and `__exit__` is called once when the block ends. Patch `builtins.open` only for code that
        cannot take a path to a real file; for most file code, `tmp_path` (13.2) gives more realistic tests."""),
    explain("How would you structure the test suite of an LLM-backed service?", "medium", tag="Interview",
        why="""As a pyramid that keeps the model out of most tests. At the base, **unit tests** for pure logic: prompt builders (structure, truncation within the token budget),
        output parsers and validators fed with real messy replies, chunking, scoring, caching keys, configuration parsing. Next, **component tests** with
        fakes and mocks that match the real interfaces (autospec): the retrieval-plus-model flow, retries with injected sleep, timeouts, tool loops, the
        no-context path that must not call the model, cache behaviour with `tmp_path` and a fake clock, logging with `caplog`. Then a few **integration tests**
        marked to run separately with real credentials and budgets, or replaying recorded responses, to catch API drift. Alongside, an **evaluation suite** with
        a versioned dataset and quality thresholds gates prompt and model changes. Shared fixtures live in `conftest.py`, everything is deterministic (seeded,
        injected clocks), and the fast layers run on every commit."""),
    explain("What would you check when reviewing someone else's tests?", "medium", tag="Interview",
        why="""That they can fail for the right reasons: each test asserts a specific outcome (not just "no exception" or a truthy value), with inputs that would distinguish
        correct code from plausible bugs, including edge cases and error paths; a quick mental mutation ("if this line were wrong, would a test fail?") helps. That
        they are isolated: no shared mutable globals, real files only in `tmp_path`, environment changes through `monkeypatch`, no dependence on order, time,
        network or unseeded randomness. That doubles are used well: mocks at boundaries only, with `spec`, no patching of the code under test, assertions on all
        relevant calls rather than `assert_called_with` on the last one, patches applied where names are looked up. That they are readable: names describe
        behaviour, arrange-act-assert structure, fixtures and parametrisation instead of copy-paste. And that they are fast and precise: tolerances for floats,
        `match=` (escaped) for error messages, no sleeps."""),
)

section("project", "Mini project: a test suite for a RAG answer service",
    fig(flowchart({
        "q": ("start", 0, 0, "answer(question)"),
        "blank": ("ask", 0, 1, "blank question?"),
        "err": ("bad", 1, 1, "ValueError"),
        "hit": ("ask", 0, 2, "cached on disk?"),
        "ret": ("good", 1, 2, "return the cached|result, log a hit"),
        "chunks": ("ask", 0, 3, "retriever returns|any chunks?"),
        "idk": ("warn", 1, 3, "I don't know.|(warning, no cache)"),
        "llm": ("accent", 0, 4, "call the model,|time it with the clock"),
        "save": ("end", 0, 5, "cache and return"),
    }, [("q", "blank"), ("blank", "err", "yes"), ("blank", "hit", "no"), ("hit", "ret", "yes"), ("hit", "chunks", "no"),
        ("chunks", "idk", "no"), ("chunks", "llm", "yes"), ("llm", "save")], cell=(240, 76), label="the answer service your tests pin down"),
        "Each branch of the service is a behaviour to test, and each needs its own fixture, fake or mock."),
    p("""`AnswerService` answers support questions: it normalises the question, returns a cached answer if one exists on disk, otherwise retrieves chunks, calls the
    model with a prompt built from them, measures latency with an injected clock, caches the result, and logs what happened. Your task is the test suite: it must
    pass on this implementation and catch each of ten realistic bugs, using what this module taught: fixtures, `tmp_path`, mocks with `spec`, fakes, a fake
    clock, `caplog`, `pytest.raises` and parametrisation."""),
    write("Test the answer service", "hard", key="answer-service-tests", tag="Project",
        prompt="""Write at least eight tests below the `# --- tests ---` line. The behaviour to pin down:

        - A blank question raises `ValueError` without touching the retriever or the model.
        - The cache key ignores case and surrounding whitespace, so `"  Refund window? "` and `"refund window?"` share one cached answer, stored as a JSON file in
          `cache_dir`.
        - A cache hit returns the stored result, logs `INFO` `"cache hit ..."`, and does not call the retriever or the model.
        - The retriever is asked for `max_chunks` chunks. With no chunks, the result is `{"answer": "I don't know.", "sources": [], "latency_ms": 0}`, a `WARNING`
          is logged, the model is not called, and nothing is cached.
        - The prompt contains every chunk as `[source] text` and the question; the model's reply is stripped; `sources` are unique in retrieval order;
          `latency_ms` is measured around the model call with the clock, in whole milliseconds.
        - A model `TimeoutError` is logged at `ERROR` and re-raised, and nothing is cached.""",
        code="""
        # --- code under test (do not edit) ---
        import hashlib, json, logging, time

        log = logging.getLogger("answers")


        class AnswerService:
            def __init__(self, retriever, llm, cache_dir, clock=time.monotonic, max_chunks=3):
                self.retriever, self.llm, self.cache_dir = retriever, llm, cache_dir
                self.clock, self.max_chunks = clock, max_chunks

            def _key(self, question):
                return hashlib.sha256(question.strip().lower().encode("utf-8")).hexdigest()[:16]

            def answer(self, question):
                if not question.strip():
                    raise ValueError("empty question")
                key = self._key(question)
                path = self.cache_dir / f"{key}.json"
                if path.exists():
                    log.info("cache hit %s", key)
                    return json.loads(path.read_text(encoding="utf-8"))
                chunks = self.retriever.retrieve(question.strip(), k=self.max_chunks)
                if not chunks:
                    log.warning("no context for %r", question.strip())
                    return {"answer": "I don't know.", "sources": [], "latency_ms": 0}
                context = "\\n".join(f"[{c['source']}] {c['text']}" for c in chunks)
                prompt = f"Answer from the context only.\\n{context}\\n\\nQuestion: {question.strip()}"
                start = self.clock()
                try:
                    reply = self.llm.complete(prompt)
                except TimeoutError:
                    log.error("model timed out for %s", key)
                    raise
                result = {
                    "answer": reply.strip(),
                    "sources": list(dict.fromkeys(c["source"] for c in chunks)),
                    "latency_ms": round((self.clock() - start) * 1000),
                }
                path.write_text(json.dumps(result), encoding="utf-8")
                return result


        class Retriever:
            def retrieve(self, question, k):
                raise NotImplementedError("real vector store")


        class LLM:
            def complete(self, prompt):
                raise NotImplementedError("real model API")


        # --- tests ---
        import logging
        import pytest
        from unittest.mock import Mock
        """,
        tests="""
        import pytest
        from lessontools import run_pytest, swap_impl
        good = run_pytest(__source__)
        assert good["failed"] == 0 and good["passed"] >= 8, good["output"][-1200:]
        tests_part = __source__.split("# --- tests")[1]
        assert "tmp_path" in tests_part and "caplog" in tests_part and "spec=" in tests_part
        BASE = __source__.split("# --- code under test (do not edit) ---")[1].split("# --- tests")[0]
        BUGS = {
            "key_case_sensitive": BASE.replace("question.strip().lower().encode", "question.strip().encode"),
            "key_not_stripped": BASE.replace("question.strip().lower().encode", "question.lower().encode"),
            "cache_not_written": BASE.replace('        path.write_text(json.dumps(result), encoding="utf-8")\\n', ""),
            "cache_never_read": BASE.replace("if path.exists():", "if False:"),
            "no_context_calls_model": BASE.replace('            return {"answer": "I don\\'t know.", "sources": [], "latency_ms": 0}', '            self.llm.complete("")\\n            return {"answer": "I don\\'t know.", "sources": [], "latency_ms": 0}'),
            "max_chunks_ignored": BASE.replace("k=self.max_chunks", "k=3"),
            "latency_seconds": BASE.replace("round((self.clock() - start) * 1000)", "round(self.clock() - start)"),
            "duplicate_sources": BASE.replace('list(dict.fromkeys(c["source"] for c in chunks))', '[c["source"] for c in chunks]'),
            "timeout_swallowed": BASE.replace("            raise\\n", "            return None\\n"),
            "no_warning": BASE.replace('            log.warning("no context for %r", question.strip())\\n', ""),
        }
        assert all(b != BASE for b in BUGS.values()), [k for k, b in BUGS.items() if b == BASE]
        escaped = sorted(name for name, impl in BUGS.items() if run_pytest(swap_impl(__source__, impl))["failed"] == 0)
        assert escaped == []
        """,
        hints=["Fixtures: `retriever` and `llm` as `Mock(spec=Retriever)` and `Mock(spec=LLM)` with default return values, a fake clock (`Mock(side_effect=[10.0, 10.25])`), and `service` built from them with `cache_dir=tmp_path`.",
               "For the cache, call `answer` twice (with different spacing and case) and check `llm.complete.call_count == 1` and the number of files in `tmp_path`.",
               "Use chunks whose sources repeat (`faq.md`, `terms.md`, `faq.md`) and `max_chunks=2` in one test; check log records with `caplog.set_level(logging.INFO)` and `(r.levelname, r.getMessage())`."],
        solution="""
        # --- code under test (do not edit) ---
        import hashlib, json, logging, time

        log = logging.getLogger("answers")


        class AnswerService:
            def __init__(self, retriever, llm, cache_dir, clock=time.monotonic, max_chunks=3):
                self.retriever, self.llm, self.cache_dir = retriever, llm, cache_dir
                self.clock, self.max_chunks = clock, max_chunks

            def _key(self, question):
                return hashlib.sha256(question.strip().lower().encode("utf-8")).hexdigest()[:16]

            def answer(self, question):
                if not question.strip():
                    raise ValueError("empty question")
                key = self._key(question)
                path = self.cache_dir / f"{key}.json"
                if path.exists():
                    log.info("cache hit %s", key)
                    return json.loads(path.read_text(encoding="utf-8"))
                chunks = self.retriever.retrieve(question.strip(), k=self.max_chunks)
                if not chunks:
                    log.warning("no context for %r", question.strip())
                    return {"answer": "I don't know.", "sources": [], "latency_ms": 0}
                context = "\\n".join(f"[{c['source']}] {c['text']}" for c in chunks)
                prompt = f"Answer from the context only.\\n{context}\\n\\nQuestion: {question.strip()}"
                start = self.clock()
                try:
                    reply = self.llm.complete(prompt)
                except TimeoutError:
                    log.error("model timed out for %s", key)
                    raise
                result = {
                    "answer": reply.strip(),
                    "sources": list(dict.fromkeys(c["source"] for c in chunks)),
                    "latency_ms": round((self.clock() - start) * 1000),
                }
                path.write_text(json.dumps(result), encoding="utf-8")
                return result


        class Retriever:
            def retrieve(self, question, k):
                raise NotImplementedError("real vector store")


        class LLM:
            def complete(self, prompt):
                raise NotImplementedError("real model API")


        # --- tests ---
        import logging
        import pytest
        from unittest.mock import Mock

        CHUNKS = [
            {"source": "faq.md", "text": "Refunds take 5 days."},
            {"source": "terms.md", "text": "No refunds after 30 days."},
            {"source": "faq.md", "text": "Refunds go to the original card."},
        ]


        @pytest.fixture
        def retriever():
            r = Mock(spec=Retriever)
            r.retrieve.return_value = CHUNKS
            return r


        @pytest.fixture
        def llm():
            m = Mock(spec=LLM)
            m.complete.return_value = "  Refunds take 5 days.\\n"
            return m


        @pytest.fixture
        def clock():
            return Mock(side_effect=[10.0, 10.25, 20.0, 20.5])


        @pytest.fixture
        def service(retriever, llm, clock, tmp_path):
            return AnswerService(retriever, llm, cache_dir=tmp_path, clock=clock)


        def test_answer_result(service):
            assert service.answer("How long do refunds take?") == {
                "answer": "Refunds take 5 days.", "sources": ["faq.md", "terms.md"], "latency_ms": 250}


        def test_prompt_has_chunks_and_question(service, llm):
            service.answer("  How long do refunds take? ")
            prompt = llm.complete.call_args.args[0]
            for c in CHUNKS:
                assert f"[{c['source']}] {c['text']}" in prompt
            assert prompt.endswith("Question: How long do refunds take?")


        def test_cache_ignores_case_and_spaces(service, llm, retriever, tmp_path):
            first = service.answer("Refund window?")
            second = service.answer("  REFUND window?  ")
            assert first == second
            assert llm.complete.call_count == 1 and retriever.retrieve.call_count == 1
            assert len(list(tmp_path.glob("*.json"))) == 1


        def test_cache_hit_is_logged_and_skips_dependencies(service, llm, retriever, caplog):
            service.answer("Refund window?")
            llm.reset_mock()
            retriever.reset_mock()
            caplog.set_level(logging.INFO)
            service.answer("refund window?")
            llm.complete.assert_not_called()
            retriever.retrieve.assert_not_called()
            assert [r.levelname for r in caplog.records] == ["INFO"] and caplog.records[0].getMessage().startswith("cache hit ")


        def test_retriever_asked_for_max_chunks(retriever, llm, clock, tmp_path):
            svc = AnswerService(retriever, llm, cache_dir=tmp_path, clock=clock, max_chunks=2)
            svc.answer("Refunds?")
            retriever.retrieve.assert_called_once_with("Refunds?", k=2)


        def test_no_context(service, retriever, llm, tmp_path, caplog):
            retriever.retrieve.return_value = []
            caplog.set_level(logging.INFO)
            assert service.answer("Unknown topic") == {"answer": "I don't know.", "sources": [], "latency_ms": 0}
            llm.complete.assert_not_called()
            assert list(tmp_path.iterdir()) == []
            assert [(r.levelname, r.getMessage()) for r in caplog.records] == [("WARNING", "no context for 'Unknown topic'")]


        def test_timeout_logged_reraised_and_not_cached(service, llm, tmp_path, caplog):
            llm.complete.side_effect = TimeoutError("slow model")
            with pytest.raises(TimeoutError):
                service.answer("Refunds?")
            assert [r.levelname for r in caplog.records] == ["ERROR"]
            assert list(tmp_path.iterdir()) == []


        @pytest.mark.parametrize("question", ["", "   ", "\\n\\t"])
        def test_blank_question(service, retriever, llm, question):
            with pytest.raises(ValueError):
                service.answer(question)
            retriever.retrieve.assert_not_called()
            llm.complete.assert_not_called()
        """,
        why="""Every lesson of the module has a job here:

        - **pytest basics (13.1):** exact expected results, `pytest.raises` for errors, and a parametrised table of blank questions.
        - **Fixtures (13.2):** small fixtures (`retriever`, `llm`, `clock`) compose into `service`, with `tmp_path` as the cache folder, so every test gets a
          fresh service and an empty cache, and `caplog` checks the log levels and messages.
        - **Mocking (13.3):** the retriever and model are `Mock(spec=...)` doubles of the real interfaces, configured per test (`return_value`, `side_effect`),
          and their call records prove the important side effects: no model call without context or on a cache hit, `k` passed through, one call for two
          spellings of a question. `reset_mock` separates the setup call from the call under test.
        - **Deterministic tests (13.4):** the clock is scripted, so latency is exactly 250 ms; nothing sleeps, nothing calls the network.

        The ten mutants are the bugs such services really ship with: cache keys that miss case or spacing (paying twice for the same question), caches written
        but never read or never written, model calls on empty context, ignored settings, seconds reported as milliseconds, duplicated citations, swallowed
        timeouts and missing warnings. A suite that catches all of them is one you can refactor the service under with confidence."""),
)

recap(
    "Start every test from \"what would make this fail?\" and choose inputs that separate correct behaviour from plausible bugs.",
    "Compose fixtures for setup; isolate files with `tmp_path`, environment with `monkeypatch` or `patch.dict`, and logs with `caplog`.",
    "Use `spec`'d mocks at boundaries, fakes for behaviour, injected clocks and tokenizers for determinism, and never sleep in tests.",
    "Remember that `match=` is a regular expression (`re.escape` literal text) and that snapshots must be updated deliberately.",
    "A test suite is good when it catches realistic mutants of the code: that is the standard the grader of this module applied.",
)
