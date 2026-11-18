from lesson import *
from diagrams import *

lesson(
    id="m13-1", num="13.1", title="pytest basics",
    intro="Tests are how you know code works today and still works after the next change, and in interviews and code reviews "
          "they are how others judge your engineering. pytest from the ground up: test discovery, plain `assert` with "
          "rewriting, floats with `approx`, exceptions with `raises`, parametrised cases, marks, and what makes a test "
          "worth having. Most problems here ask you to write the tests, and they are graded by running real pytest against "
          "a correct implementation and several buggy ones.",
    desc="Test discovery, assert rewriting, `raises`, `approx`, parametrize and marks.",
    keys="pytest test discovery assert rewriting approx raises match excinfo parametrize ids pytest.param mark skip skipif xfail strict arrange act assert edge cases mutation unit test",
)

term("Unit test", "A small automated check of one behaviour of one piece of code, such as a function returning the right value for one kind of input.")
term("Test runner", "The program that finds tests, runs them and reports results. pytest is the standard one for Python.")
term("Mutation testing", "Judging tests by deliberately introducing bugs (mutants) into the code and checking that at least one test fails for each.")

section("why", "What a test is and how pytest finds it",
    fig(stage_map(13, "a test suite for a RAG answer service"), "Module 13 at a glance: pytest basics, fixtures, test doubles and testing ML code, building up to a full test suite."),
    fig(chain(["arrange:|build the input", "act:|call the code", ("assert:|check the result", "accent")]),
        "Every test has the same three steps; a test name states the behaviour they check."),
    fig(chain(["pytest", "collect test_*.py|files", "collect test_*|functions", "run each,|report failures", ("rewritten assert shows|both sides on failure", "good")]),
        "pytest finds tests by naming convention, runs each one separately, and explains failed asserts."),
    p("""A **test** is code that runs other code with a known input and checks the output. Written once, it runs in a second every time anything changes, so
    regressions are caught before users or downstream jobs find them, and refactoring becomes safe. A good test reads as a specification: its name states a
    behaviour (`test_slugify_collapses_repeated_separators`), and its body follows **arrange, act, assert**: set up the input, call the code, check the
    result."""),
    p("""**pytest** finds tests by convention: files named `test_*.py` or `*_test.py`, functions named `test_*` in them, and methods named `test_*` in classes
    named `Test*` that have no `__init__`. You check results with the plain **`assert`** statement; pytest rewrites asserts in test files when it imports them,
    so a failure shows the values involved (`assert 4 == 5` with `where 4 = add(2, 2)`) instead of a bare `AssertionError`. A test **passes** if it returns
    without an exception and **fails** if anything raises, so a test with no assert passes whenever the code merely does not crash, which is rarely enough."""),
    p("""On your machine you run `pytest` in the project folder (or `python -m pytest`); useful options are `-q` (quiet), `-v` (one line per test), `-x` (stop at
    the first failure), `-k "slug and not unicode"` (select by name), `--lf` (rerun last failures) and a node id such as `tests/test_text.py::test_slugify`
    to run one test. **On this site**, the helper `run_pytest(source)` from `lessontools` writes `source` to a fresh folder as `test_main.py`, runs real
    pytest on it in the browser, and returns a dict with each test's outcome, the counts and pytest's output. `swap_impl(source, code)` replaces the section
    between the comments `# --- code under test` and `# --- tests` with other code, which is how your tests are run against buggy versions."""),
    ex("""
    from lessontools import run_pytest

    SRC = '''
    def add(a, b):
        return a + b

    def test_add_numbers():
        result = add(2, 3)
        assert result == 5

    def test_add_lists():
        assert add([1], [2, 3]) == [1, 2]
    '''
    r = run_pytest(SRC)
    print(r["outcomes"], r["passed"], r["failed"])
    print([line for line in r["output"].splitlines() if line.startswith("E ")])
    """, "first_test.py"),
    p("""The failure report shows the actual value (`[1, 2, 3]`), the expected one, and where they differ, without any message written by hand. That is the
    reason to prefer a plain `assert` over `assertEqual`-style helpers in pytest code."""),
)

section("asserts", "Writing assertions: values, floats and exceptions",
    p("""Assert the most specific thing you can. `assert result == {"label": "spam", "score": 0.9}` checks everything at once and pytest prints a diff of
    the dicts; `assert result` or `assert "spam" in str(result)` pass for many wrong results. Compare whole values where possible, check types when they
    matter (`isinstance`), and use `is` only for `None`, `True` and `False`."""),
    p("""Floats need tolerance, because arithmetic in binary rounds: `0.1 + 0.2 == 0.3` is `False`. **`pytest.approx(expected)`** compares within a relative
    tolerance of one millionth by default (`rel=1e-6`), plus an absolute tolerance of `1e-12` for values near zero; set `rel=` or `abs=` explicitly when you
    know the precision you need. It works for single numbers, and element-wise for lists, tuples and dict values, and NumPy arrays, so `assert
    metrics == pytest.approx({"precision": 0.667, "recall": 0.5}, abs=1e-3)` checks a whole metrics dict."""),
    p("""Errors are behaviour too. **`with pytest.raises(ValueError, match="overlap"):`** passes only if the block raises `ValueError` (or a subclass) whose message
    matches the regular expression; if nothing is raised, the test fails with `DID NOT RAISE`. Use `as excinfo` to inspect the exception afterwards
    (`excinfo.value`, `excinfo.type`). Keep only the raising call inside the block: anything after it never runs. `pytest.warns(DeprecationWarning)` does the
    same for warnings."""),
    ex("""
    import pytest

    print(0.1 + 0.2 == 0.3, 0.1 + 0.2 == pytest.approx(0.3))
    print({"p": 0.6667, "r": 0.5} == pytest.approx({"p": 2 / 3, "r": 0.5}, abs=1e-3), 1e-9 == pytest.approx(0))
    with pytest.raises(ValueError, match="invalid literal") as excinfo:
        int("twelve")
    print(excinfo.type.__name__, excinfo.value)
    """, "asserts.py"),
)

section("param", "Parametrize: one test, many cases",
    fig(chain(["@pytest.mark.parametrize(|'text, want', cases)", "one test function", ("one separate test|per case, with its own id", "good")]),
        "Parametrize turns a table of cases into separate tests, so one failing case does not hide the others."),
    p("""Edge cases are where bugs live, and writing a separate function for each is tedious. **`@pytest.mark.parametrize("text,expected", [...])`** runs one test
    function once per tuple, each as a separate test with its own outcome and an id built from the values (`test_slugify[Hello World-hello-world]`), so one
    failing case does not hide the others. Give readable ids with `ids=[...]` or `pytest.param(value, id="unicode")`, and attach marks to single cases with
    `pytest.param(..., marks=pytest.mark.xfail)`. Stacking two `parametrize` decorators runs every combination, which suits checks such as every model with
    every temperature."""),
    p("""Choose cases deliberately: the normal case, the **empty** input, a single element, **boundaries** (exactly at a limit, one below, one above), invalid
    input that must raise, unusual characters (Unicode, whitespace, very long strings), and anything a past bug taught you. That list is more valuable than many
    random normal cases."""),
    ex("""
    from lessontools import run_pytest

    SRC = '''
    import pytest

    def word_count(text):
        return len(text.split())

    @pytest.mark.parametrize("text,expected", [
        ("refund window", 2),
        ("", 0),
        ("  spaced   out  ", 2),
        pytest.param("tab\\\\tand\\\\nnewline", 3, id="whitespace"),
        pytest.param("don't stop", 3, id="apostrophe", marks=pytest.mark.xfail(reason="counts words, not tokens")),
    ])
    def test_word_count(text, expected):
        assert word_count(text) == expected
    '''
    for name, outcome in run_pytest(SRC)["outcomes"].items():
        print(f"{outcome:8} {name}")
    """, "parametrize.py"),
)

section("marks", "Marks: skipping and expected failures",
    p("""**Marks** attach metadata to tests. `@pytest.mark.skip(reason=...)` never runs a test; `@pytest.mark.skipif(condition, reason=...)` skips it when the condition
    is true, for example on another operating system, without a GPU, or without an API key in the environment. `@pytest.mark.xfail(reason=...)` documents a
    known bug: the test runs, a failure is reported as `xfailed` (expected), and if it unexpectedly passes it is `xpassed`; with **`strict=True`**, an
    unexpected pass is a failure, which forces you to remove the mark once the bug is fixed. Custom marks (`@pytest.mark.slow`, `@pytest.mark.integration`)
    are registered in the configuration and selected with `-m "not slow"`, so a fast suite runs on every change and the slow one in CI."""),
)

section("good", "What makes a test worth having",
    p("""A test is worth having if it **fails when the code is wrong** and **passes when the code is right**, every time. That gives the checklist. It tests
    **behaviour** through the public interface, not implementation details, so a refactor does not break it. It is **deterministic**: no dependence on the
    clock, randomness without a seed, the network, test order or leftover files (13.2 and 13.3 show how to control those). It is **fast**, so people run it
    constantly. It checks **one behaviour**, so its name says what broke. And it would have **caught a real bug**: the grading of this lesson's problems,
    mutation testing, measures exactly that by running your tests against deliberately broken versions of the code."""),
)

section("warmup", "Warm-up",
    predict("What pytest collects and how it judges", "easy",
        code="""
        from lessontools import run_pytest

        SRC = '''
        import pytest

        def add(a, b):
            return a + b

        def test_add():
            assert add(2, 3) == 5

        def test_add_strings():
            assert add("a", "b") == "ab "

        def test_no_assert():
            add(1, 1)

        def check_add():
            assert False

        def test_error():
            assert add(1, None) == 1

        def test_raises():
            with pytest.raises(TypeError):
                add(1, None)

        class TestAdd:
            def test_negative(self):
                assert add(-1, -1) == -2

        class TestWithInit:
            def __init__(self):
                self.x = 1
            def test_never(self):
                assert False
        '''
        r = run_pytest(SRC)
        for name, outcome in r["outcomes"].items():
            print(name, outcome)
        print(r["passed"], r["failed"], r["exit"])
        """,
        hints=["Only `test_*` functions and `test_*` methods of `Test*` classes without `__init__` are collected. Any exception in a test makes it fail."],
        why="""`check_add` is not collected because of its name, and `TestWithInit` is skipped by collection (pytest warns) because a test class cannot have an
        `__init__`. `test_no_assert` passes since nothing raised: a test without an assertion only checks that the code does not crash. The `TypeError` in
        `test_error` makes it fail just like a failed assert, while `test_raises` expects exactly that error and passes. The exit code 1 means "some tests
        failed"; 0 would mean all passed."""),
    write("Test a slugify function", "easy", tag="Data work",
        prompt="""`slugify(text)` turns titles into URL-safe ids: it lower-cases, keeps ASCII letters and digits, turns every run of other characters into **one**
        hyphen, and never starts or ends with a hyphen (`"  Refund Policy (EU)! "` becomes `"refund-policy-eu"`, `"Café menu"` becomes `"caf-menu"`, `""` stays
        `""`). Write at least four tests below the `# --- tests ---` line. They must all pass on this implementation and catch each of five buggy versions.""",
        code="""
        # --- code under test (do not edit) ---
        def slugify(text):
            out, dash = [], False
            for ch in text.lower():
                if ch.isascii() and ch.isalnum():
                    out.append(ch)
                    dash = False
                elif not dash and out:
                    out.append("-")
                    dash = True
            return "".join(out).strip("-")


        # --- tests ---
        import pytest


        def test_lowercases():
            pass
        """,
        tests="""
        import pytest
        from lessontools import run_pytest, swap_impl
        good = run_pytest(__source__)
        assert good["failed"] == 0 and good["passed"] >= 4, good["output"][-800:]
        BUGS = {
            "keeps_case": '''
        def slugify(text):
            out, dash = [], False
            for ch in text:
                if ch.isascii() and ch.isalnum():
                    out.append(ch)
                    dash = False
                elif not dash and out:
                    out.append("-")
                    dash = True
            return "".join(out).strip("-")
        ''',
            "keeps_unicode": '''
        def slugify(text):
            out, dash = [], False
            for ch in text.lower():
                if ch.isalnum():
                    out.append(ch)
                    dash = False
                elif not dash and out:
                    out.append("-")
                    dash = True
            return "".join(out).strip("-")
        ''',
            "no_collapse": '''
        def slugify(text):
            out = []
            for ch in text.lower():
                if ch.isascii() and ch.isalnum():
                    out.append(ch)
                elif out:
                    out.append("-")
            return "".join(out).strip("-")
        ''',
            "trailing_hyphen": '''
        def slugify(text):
            out, dash = [], False
            for ch in text.lower():
                if ch.isascii() and ch.isalnum():
                    out.append(ch)
                    dash = False
                elif not dash and out:
                    out.append("-")
                    dash = True
            return "".join(out)
        ''',
            "keeps_punctuation": '''
        def slugify(text):
            out, dash = [], False
            for ch in text.lower():
                if ch not in " ":
                    out.append(ch)
                    dash = False
                elif not dash and out:
                    out.append("-")
                    dash = True
            return "".join(out).strip("-")
        ''',
        }
        escaped = sorted(name for name, impl in BUGS.items() if run_pytest(swap_impl(__source__, impl))["failed"] == 0)
        assert escaped == []
        """,
        hints=["One test per rule in the description: case, non-ASCII characters, runs of separators, edges, punctuation, and the empty string.",
               "If the grader lists a bug as escaped, read that buggy version and write the input that makes it differ from the correct one."],
        solution="""
        # --- code under test (do not edit) ---
        def slugify(text):
            out, dash = [], False
            for ch in text.lower():
                if ch.isascii() and ch.isalnum():
                    out.append(ch)
                    dash = False
                elif not dash and out:
                    out.append("-")
                    dash = True
            return "".join(out).strip("-")


        # --- tests ---
        import pytest


        def test_lowercases():
            assert slugify("Refund Policy") == "refund-policy"


        def test_drops_non_ascii_letters():
            assert slugify("Café menu") == "caf-menu"


        def test_collapses_runs_of_separators():
            assert slugify("refund -- policy!!") == "refund-policy"


        def test_no_leading_or_trailing_hyphens():
            assert slugify("  (EU) refunds! ") == "eu-refunds"


        def test_drops_punctuation():
            assert slugify("what's new?") == "what-s-new"


        def test_empty_and_symbols_only():
            assert slugify("") == ""
            assert slugify("!!!") == ""
        """,
        why="""Each test pins one rule of the specification, with an input chosen so that a version breaking that rule gives a different answer: mixed case, an accented letter,
        a run of several separators, separators at both ends, punctuation inside a word, and inputs with nothing to keep. That is how to write tests from a
        spec: list the rules, then the input that would expose a violation of each. The grader's five mutants are exactly such violations, and a suite that
        lets one survive has a hole that a real bug could slip through. Comparing the full returned string is what makes each test strict."""),
    fix("A float test that fails on correct code", "easy", tag="ML",
        prompt="""`mean_reciprocal_rank` is correct, but its test fails because it compares floats with `==`, and the test suite does not notice a bug that divides by the
        wrong count. Fix the tests: use `pytest.approx`, and add a case that catches the bug (the graded buggy version divides by the number of queries that
        had a hit, instead of all queries).""",
        code="""
        # --- code under test (do not edit) ---
        def mean_reciprocal_rank(ranks):
            # ranks: 1-based position of the first relevant result per query, or None if there was none
            return sum(1 / r for r in ranks if r is not None) / len(ranks)


        # --- tests ---
        import pytest


        def test_mrr():
            assert mean_reciprocal_rank([1, 2, 3]) == 0.611111
        """,
        tests="""
        import pytest
        from lessontools import run_pytest, swap_impl
        good = run_pytest(__source__)
        assert good["failed"] == 0 and good["passed"] >= 2, good["output"][-800:]
        BUG = '''
        def mean_reciprocal_rank(ranks):
            hits = [r for r in ranks if r is not None]
            return sum(1 / r for r in hits) / len(hits)
        '''
        assert run_pytest(swap_impl(__source__, BUG))["failed"] > 0
        """,
        hints=["`assert value == pytest.approx(11 / 18)`, or `pytest.approx(0.6111, abs=1e-4)`.", "Which input makes the two versions differ? A query with no hit."],
        solution="""
        # --- code under test (do not edit) ---
        def mean_reciprocal_rank(ranks):
            # ranks: 1-based position of the first relevant result per query, or None if there was none
            return sum(1 / r for r in ranks if r is not None) / len(ranks)


        # --- tests ---
        import pytest


        def test_mrr_of_ranks():
            assert mean_reciprocal_rank([1, 2, 3]) == pytest.approx(11 / 18)


        def test_queries_without_a_hit_count_as_zero():
            assert mean_reciprocal_rank([1, None]) == pytest.approx(0.5)
        """,
        why="""`(1 + 1/2 + 1/3) / 3` is `0.6111...` with many more digits, so an exact comparison against a rounded literal fails although the code is right; `approx`
        compares within a relative tolerance, and writing the exact fraction `11 / 18` makes the intent clear. The second test adds the case the first could not
        see: a query with no relevant result must count as a reciprocal rank of 0, which is what makes MRR penalise a retriever that finds nothing. With only
        "every query has a hit" in the suite, both versions agree and the bug ships. A green test suite is only as strong as its cases."""),
    predict("pytest.approx in detail", "easy",
        code="""
        import pytest

        print(0.1 + 0.2 == pytest.approx(0.3), [0.1 + 0.2, 1] == pytest.approx([0.3, 1]))
        print(1.0001 == pytest.approx(1), 1.0001 == pytest.approx(1, rel=1e-3))
        print(1e-7 == pytest.approx(0), 1e-7 == pytest.approx(0, abs=1e-6))
        print({"f1": 0.8333} == pytest.approx({"f1": 5 / 6}, abs=1e-3), (1, 2) == pytest.approx([1, 2]))
        """,
        hints=["The default relative tolerance is `1e-6`, and the default absolute tolerance is `1e-12`, which is what applies when comparing with 0."],
        why="""The float rounding error is far inside the default tolerance, and lists are compared element by element. `1.0001` is 100 parts per million away from 1,
        outside the default one part per million but inside `rel=1e-3`. Near zero, a relative tolerance is useless (a fraction of zero is zero), so only the
        tiny default absolute tolerance applies and `1e-7` is not "approximately 0" until you say what "small" means with `abs=`. Dict values are compared by
        key. A tuple even equals an approx of a list, because `approx` compares any two sequences element by element; it does not check the container type,
        so add an `isinstance` assert when the type matters."""),
)

section("medium", "Medium",
    write("Test a chunker, including its errors", "medium", tag="RAG",
        prompt="""`chunk_words(text, size, overlap=0)` splits text into chunks of `size` words, each starting `size - overlap` words after the previous one, keeping a
        shorter last chunk only when it contains words not already covered; it raises `ValueError` mentioning `size` if `size < 1` and mentioning `overlap` if
        `overlap` is negative or not smaller than `size`. Write at least five tests (use `pytest.raises` with `match=`) that pass here and catch four buggy
        versions.""",
        code="""
        # --- code under test (do not edit) ---
        def chunk_words(text, size, overlap=0):
            if size < 1:
                raise ValueError("size must be at least 1")
            if not 0 <= overlap < size:
                raise ValueError("overlap must be in [0, size)")
            words = text.split()
            step = size - overlap
            chunks = []
            for start in range(0, len(words), step):
                chunks.append(" ".join(words[start:start + size]))
                if start + size >= len(words):
                    break
            return chunks


        # --- tests ---
        import pytest


        def test_chunks_without_overlap():
            pass
        """,
        tests="""
        import pytest
        from lessontools import run_pytest, swap_impl
        good = run_pytest(__source__)
        assert good["failed"] == 0 and good["passed"] >= 5, good["output"][-800:]
        BUGS = {
            "ignores_overlap": '''
        def chunk_words(text, size, overlap=0):
            if size < 1:
                raise ValueError("size must be at least 1")
            if not 0 <= overlap < size:
                raise ValueError("overlap must be in [0, size)")
            words = text.split()
            return [" ".join(words[i:i + size]) for i in range(0, len(words), size)]
        ''',
            "drops_last_chunk": '''
        def chunk_words(text, size, overlap=0):
            if size < 1:
                raise ValueError("size must be at least 1")
            if not 0 <= overlap < size:
                raise ValueError("overlap must be in [0, size)")
            words = text.split()
            step = size - overlap
            return [" ".join(words[i:i + size]) for i in range(0, len(words) - size + 1, step)]
        ''',
            "no_overlap_check": '''
        def chunk_words(text, size, overlap=0):
            if size < 1:
                raise ValueError("size must be at least 1")
            words = text.split()
            step = size - overlap
            chunks = []
            for start in range(0, len(words), step):
                chunks.append(" ".join(words[start:start + size]))
                if start + size >= len(words):
                    break
            return chunks
        ''',
            "redundant_tail": '''
        def chunk_words(text, size, overlap=0):
            if size < 1:
                raise ValueError("size must be at least 1")
            if not 0 <= overlap < size:
                raise ValueError("overlap must be in [0, size)")
            words = text.split()
            step = size - overlap
            return [" ".join(words[i:i + size]) for i in range(0, len(words), step)]
        ''',
        }
        escaped = sorted(name for name, impl in BUGS.items() if run_pytest(swap_impl(__source__, impl))["failed"] == 0)
        assert escaped == []
        """,
        hints=["A ten-word text with `size=4, overlap=1` exercises the step, the overlap and the last chunk at once; write the expected chunks out by hand.",
               "`overlap == size` must raise with a message about overlap; the buggy version raises too, but from `range` with a different message, so `match=\"overlap\"` tells them apart.",
               "When the last full chunk already reaches the end, no extra shorter chunk may follow: try 5 words with `size=3, overlap=1`."],
        solution="""
        # --- code under test (do not edit) ---
        def chunk_words(text, size, overlap=0):
            if size < 1:
                raise ValueError("size must be at least 1")
            if not 0 <= overlap < size:
                raise ValueError("overlap must be in [0, size)")
            words = text.split()
            step = size - overlap
            chunks = []
            for start in range(0, len(words), step):
                chunks.append(" ".join(words[start:start + size]))
                if start + size >= len(words):
                    break
            return chunks


        # --- tests ---
        import pytest

        TEN = "w0 w1 w2 w3 w4 w5 w6 w7 w8 w9"


        def test_chunks_without_overlap():
            assert chunk_words(TEN, 4) == ["w0 w1 w2 w3", "w4 w5 w6 w7", "w8 w9"]


        def test_chunks_with_overlap():
            assert chunk_words(TEN, 4, overlap=1) == ["w0 w1 w2 w3", "w3 w4 w5 w6", "w6 w7 w8 w9"]


        def test_no_redundant_tail_chunk():
            assert chunk_words("a b c d e", 3, overlap=1) == ["a b c", "c d e"]


        def test_empty_text():
            assert chunk_words("", 3) == []


        @pytest.mark.parametrize("overlap", [-1, 3, 4])
        def test_rejects_bad_overlap(overlap):
            with pytest.raises(ValueError, match="overlap"):
                chunk_words(TEN, 3, overlap=overlap)


        def test_rejects_bad_size():
            with pytest.raises(ValueError, match="size"):
                chunk_words(TEN, 0)
        """,
        why="""Writing the expected chunks out by hand for one well-chosen input (ten numbered words) checks the step, the overlap and the final chunk together, and
        numbered words make mistakes easy to see. The redundant-tail case is the subtle one: with overlap, a naive loop emits a last chunk made only of words
        already included, which wastes an embedding and double-counts text in retrieval. `match=` matters for errors: the version without the overlap check
        still raises `ValueError` for `overlap == size`, but from `range()` ("arg 3 must not be zero"), and for `overlap > size` it silently loops backwards;
        checking the message proves the error comes from **your** validation. Parametrising the bad values keeps each case visible in the report."""),
    write("Parametrized tests for a duration parser", "medium", tag="Data work",
        prompt="""`parse_duration(text)` turns `"1h30m"`, `"45s"`, `"2h"`, `"1h0m5s"` into seconds; units must appear in the order h, m, s, at most once each; whitespace
        around the text is ignored; anything else (`""`, `"10"`, `"5x"`, `"1m1h"`, `"h"`) raises `ValueError`. Write a **parametrized** test with at least six
        valid cases and another with at least five invalid ones. Your tests must pass here and catch four buggy versions.""",
        code="""
        # --- code under test (do not edit) ---
        def parse_duration(text):
            text = text.strip()
            units = {"h": 3600, "m": 60, "s": 1}
            total, number, seen = 0, "", []
            for ch in text:
                if ch.isdigit():
                    number += ch
                elif ch in units and number:
                    if seen and "hms".index(ch) <= "hms".index(seen[-1]):
                        raise ValueError(f"bad unit order in {text!r}")
                    total += int(number) * units[ch]
                    seen.append(ch)
                    number = ""
                else:
                    raise ValueError(f"bad duration {text!r}")
            if number or not seen:
                raise ValueError(f"bad duration {text!r}")
            return total


        # --- tests ---
        import pytest
        """,
        tests="""
        import pytest
        from lessontools import run_pytest, swap_impl
        good = run_pytest(__source__)
        assert good["failed"] == 0, good["output"][-800:]
        params = [n for n in good["outcomes"] if "[" in n]
        assert len(params) >= 11 and len({n.split("[")[0] for n in params}) >= 2
        BUGS = {
            "no_strip": '''
        def parse_duration(text):
            units = {"h": 3600, "m": 60, "s": 1}
            total, number, seen = 0, "", []
            for ch in text:
                if ch.isdigit():
                    number += ch
                elif ch in units and number:
                    if seen and "hms".index(ch) <= "hms".index(seen[-1]):
                        raise ValueError("order")
                    total += int(number) * units[ch]
                    seen.append(ch)
                    number = ""
                else:
                    raise ValueError("bad")
            if number or not seen:
                raise ValueError("bad")
            return total
        ''',
            "any_order": '''
        def parse_duration(text):
            text = text.strip()
            units = {"h": 3600, "m": 60, "s": 1}
            total, number, seen = 0, "", []
            for ch in text:
                if ch.isdigit():
                    number += ch
                elif ch in units and number:
                    total += int(number) * units[ch]
                    seen.append(ch)
                    number = ""
                else:
                    raise ValueError("bad")
            if number or not seen:
                raise ValueError("bad")
            return total
        ''',
            "bare_number_ok": '''
        def parse_duration(text):
            text = text.strip()
            if text.isdigit():
                return int(text)
            units = {"h": 3600, "m": 60, "s": 1}
            total, number, seen = 0, "", []
            for ch in text:
                if ch.isdigit():
                    number += ch
                elif ch in units and number:
                    if seen and "hms".index(ch) <= "hms".index(seen[-1]):
                        raise ValueError("order")
                    total += int(number) * units[ch]
                    seen.append(ch)
                    number = ""
                else:
                    raise ValueError("bad")
            if number or not seen:
                raise ValueError("bad")
            return total
        ''',
            "minutes_wrong": '''
        def parse_duration(text):
            text = text.strip()
            units = {"h": 3600, "m": 100, "s": 1}
            total, number, seen = 0, "", []
            for ch in text:
                if ch.isdigit():
                    number += ch
                elif ch in units and number:
                    if seen and "hms".index(ch) <= "hms".index(seen[-1]):
                        raise ValueError("order")
                    total += int(number) * units[ch]
                    seen.append(ch)
                    number = ""
                else:
                    raise ValueError("bad")
            if number or not seen:
                raise ValueError("bad")
            return total
        ''',
        }
        escaped = sorted(name for name, impl in BUGS.items() if run_pytest(swap_impl(__source__, impl))["failed"] == 0)
        assert escaped == []
        """,
        hints=["`@pytest.mark.parametrize(\"text,seconds\", [(\"45s\", 45), ...])` above `def test_valid(text, seconds):`.",
               "Include a case with surrounding spaces, one with minutes, and invalid inputs such as a bare number and units out of order."],
        solution="""
        # --- code under test (do not edit) ---
        def parse_duration(text):
            text = text.strip()
            units = {"h": 3600, "m": 60, "s": 1}
            total, number, seen = 0, "", []
            for ch in text:
                if ch.isdigit():
                    number += ch
                elif ch in units and number:
                    if seen and "hms".index(ch) <= "hms".index(seen[-1]):
                        raise ValueError(f"bad unit order in {text!r}")
                    total += int(number) * units[ch]
                    seen.append(ch)
                    number = ""
                else:
                    raise ValueError(f"bad duration {text!r}")
            if number or not seen:
                raise ValueError(f"bad duration {text!r}")
            return total


        # --- tests ---
        import pytest


        @pytest.mark.parametrize("text,seconds", [
            ("45s", 45),
            ("2h", 7200),
            ("1h30m", 5400),
            ("1h0m5s", 3605),
            ("90m", 5400),
            ("  10m ", 600),
            ("0s", 0),
        ])
        def test_valid_durations(text, seconds):
            assert parse_duration(text) == seconds


        @pytest.mark.parametrize("text", ["", "10", "5x", "1m1h", "h", "1h1h", "1.5h"])
        def test_invalid_durations(text):
            with pytest.raises(ValueError):
                parse_duration(text)
        """,
        why="""Parametrisation turns a table of examples into separate tests, each reported with its own id, so the report says exactly which input broke. The valid table
        covers each unit alone, combinations, a zero component, a value above 60 for minutes and surrounding spaces; the invalid table covers empty input, a
        number without a unit, an unknown unit, units out of order, a unit without a number, a repeated unit and a decimal. Each mutant fails at least one row:
        `"  10m "` catches the missing strip, `"1m1h"` the missing order check, `"10"` the bare-number shortcut, and any minute case the wrong multiplier."""),
    fix("Tests that cannot fail", "medium", tag="GenAI",
        prompt="""These tests for `classify(text)` all pass, yet the graded buggy version, which labels everything `"ham"`, passes them too. Each test has a flaw: an assert
        that is always true, a check after the line that raises, and a membership test that accepts any label. Fix the tests so they pass here and fail on the
        bug.""",
        code="""
        # --- code under test (do not edit) ---
        def classify(text):
            if not text.strip():
                raise ValueError("empty message")
            spammy = ("win", "prize", "free", "click")
            return "spam" if any(w in text.lower() for w in spammy) else "ham"


        # --- tests ---
        import pytest


        def test_spam():
            assert (classify("WIN a free prize"), "spam")


        def test_empty_rejected():
            with pytest.raises(ValueError):
                classify("   ")
                assert classify("hello") == "ham"


        def test_labels():
            assert classify("Click here") in ["spam", "ham"]
        """,
        tests="""
        import pytest
        from lessontools import run_pytest, swap_impl
        good = run_pytest(__source__)
        assert good["failed"] == 0 and good["passed"] >= 3, good["output"][-800:]
        BUG = '''
        def classify(text):
            if not text.strip():
                raise ValueError("empty message")
            return "ham"
        '''
        assert run_pytest(swap_impl(__source__, BUG))["failed"] > 0
        assert "assert (" not in __source__.split("# --- tests")[1]
        """,
        hints=["`assert (x, y)` asserts a non-empty tuple, which is always true (Python even warns). Use `==`.",
               "Move the second check out of the `with pytest.raises` block. Assert the exact label."],
        solution="""
        # --- code under test (do not edit) ---
        def classify(text):
            if not text.strip():
                raise ValueError("empty message")
            spammy = ("win", "prize", "free", "click")
            return "spam" if any(w in text.lower() for w in spammy) else "ham"


        # --- tests ---
        import pytest


        def test_spam():
            assert classify("WIN a free prize") == "spam"


        def test_empty_rejected():
            with pytest.raises(ValueError, match="empty"):
                classify("   ")


        def test_ham():
            assert classify("hello, lunch at noon?") == "ham"


        def test_click_is_spam():
            assert classify("Click here") == "spam"
        """,
        why="""All three are classic ways to write a test that cannot fail. `assert (value, "spam")` asserts a two-element tuple, which is always truthy; Python emits
        `SyntaxWarning: assertion is always true` for exactly this. Inside `pytest.raises`, the block stops at the first raising line, so the `ham` check never
        ran. And "the label is one of the labels" is true of any classifier. A useful habit: after writing a test, break the code on purpose and watch the test
        fail; a test you have never seen fail is not yet trustworthy."""),
    trace("Inspecting pytest.raises", "medium",
        prompt="Fill in `kind` and `text` after each marked line.",
        code="""
        import pytest

        with pytest.raises(ValueError) as info:
            int("x")
        kind, text = info.type.__name__, str(info.value)  # row: "ValueError"
        with pytest.raises(LookupError) as info:
            {"model": "small"}["temperature"]
        kind, text = info.type.__name__, str(info.value)  # row: "a subclass"
        with pytest.raises((TypeError, ValueError)) as info:
            len(5)
        kind, text = info.type.__name__, info.match("has no len")  # row: "a tuple of types"

        def check():
            try:
                with pytest.raises(ValueError):
                    int("3")
            except BaseException as e:
                return type(e).__name__, str(e)

        kind, text = check()  # row: "nothing raised"
        """,
        trace_vars=["kind", "text"],
        hints=["`info.type` is the class actually raised. A `KeyError`'s string is the repr of the key. `match` returns `True` when the pattern is found.",
               "When the block does not raise, `pytest.raises` raises pytest's own `Failed` exception."],
        why="""`pytest.raises` accepts the expected class or any superclass, so `LookupError` catches the `KeyError`, and `info.type` reports the real class. A `KeyError`
        prints as the quoted key, which is why `match=` patterns for key errors look odd. A tuple accepts any of the types, and `info.match` searches the message
        with a regular expression and returns `True` (or raises `AssertionError`). When nothing is raised, the context manager raises `Failed: DID NOT RAISE`,
        an exception that derives from `BaseException`, so a plain `except Exception` in test helpers does not swallow it."""),
    write("Test an LLM JSON extractor", "medium", tag="GenAI",
        prompt="""`extract_json(reply)` pulls a JSON object out of a model reply: it accepts a bare object, an object inside a fenced block such as three backticks
        followed by `json`, and an object surrounded by chatter, using the first `{` and the last `}`; it raises `ValueError` when there is no object or the
        JSON is invalid. Write at least five tests that pass here and catch three buggy versions.""",
        code="""
        # --- code under test (do not edit) ---
        import json


        def extract_json(reply):
            start, end = reply.find("{"), reply.rfind("}")
            if start == -1 or end < start:
                raise ValueError("no JSON object in reply")
            try:
                value = json.loads(reply[start:end + 1])
            except json.JSONDecodeError as e:
                raise ValueError(f"invalid JSON: {e.msg}") from e
            return value


        # --- tests ---
        import pytest
        """,
        tests="""
        import pytest
        from lessontools import run_pytest, swap_impl
        good = run_pytest(__source__)
        assert good["failed"] == 0 and good["passed"] >= 5, good["output"][-800:]
        BUGS = {
            "first_brace_only": '''
        import json
        def extract_json(reply):
            start, end = reply.find("{"), reply.find("}")
            if start == -1 or end < start:
                raise ValueError("no JSON object in reply")
            try:
                value = json.loads(reply[start:end + 1])
            except json.JSONDecodeError as e:
                raise ValueError(f"invalid JSON: {e.msg}") from e
            return value
        ''',
            "leaks_decode_error": '''
        import json
        def extract_json(reply):
            start, end = reply.find("{"), reply.rfind("}")
            if start == -1 or end < start:
                raise ValueError("no JSON object in reply")
            value = json.loads(reply[start:end + 1].replace("'", '"'))
            return value
        ''',
            "none_when_missing": '''
        import json
        def extract_json(reply):
            start, end = reply.find("{"), reply.rfind("}")
            if start == -1 or end < start:
                return None
            try:
                value = json.loads(reply[start:end + 1])
            except json.JSONDecodeError as e:
                raise ValueError(f"invalid JSON: {e.msg}") from e
            return value
        ''',
        }
        escaped = sorted(name for name, impl in BUGS.items() if run_pytest(swap_impl(__source__, impl))["failed"] == 0)
        assert escaped == []
        """,
        hints=["A nested object (`{\"a\": {\"b\": 1}}`) defeats a version that stops at the first `}`.",
               "Single quotes (`{'label': 'spam'}`) are invalid JSON and must give a `ValueError`, not be repaired silently."],
        solution="""
        # --- code under test (do not edit) ---
        import json


        def extract_json(reply):
            start, end = reply.find("{"), reply.rfind("}")
            if start == -1 or end < start:
                raise ValueError("no JSON object in reply")
            try:
                value = json.loads(reply[start:end + 1])
            except json.JSONDecodeError as e:
                raise ValueError(f"invalid JSON: {e.msg}") from e
            return value


        # --- tests ---
        import pytest

        FENCE = "`" * 3


        def test_bare_object():
            assert extract_json('{"label": "spam", "score": 0.9}') == {"label": "spam", "score": 0.9}


        def test_fenced_block():
            reply = f'Here you go:\\n{FENCE}json\\n{{"label": "ham"}}\\n{FENCE}'
            assert extract_json(reply) == {"label": "ham"}


        def test_nested_object_with_chatter():
            reply = 'Sure! {"label": "spam", "meta": {"reasons": ["prize"]}} Hope this helps.'
            assert extract_json(reply) == {"label": "spam", "meta": {"reasons": ["prize"]}}


        def test_no_object_raises():
            with pytest.raises(ValueError, match="no JSON object"):
                extract_json("I cannot classify this message.")


        def test_single_quotes_are_invalid():
            with pytest.raises(ValueError, match="invalid JSON"):
                extract_json("{'label': 'spam'}")


        def test_array_reply_has_no_object():
            with pytest.raises(ValueError, match="no JSON object"):
                extract_json("[1, 2, 3]")
        """,
        why="""Each test targets one documented behaviour with realistic model output: a fenced block, chatter around a **nested** object (which defeats "stop at the first
        closing brace"), no object at all, Python-style quotes, and text whose first-brace-to-last-brace span is not one object. The quote test also shows why
        tests should check the **type** of error: the buggy version that "repairs" quotes returns a value instead of raising, which a looser test (`assert
        result`) would accept. The missing-object tests assert an exception, so a version returning `None` fails. Note what is **not** tested: when the
        text from the first `{` to the last `}` parses, it is always an object, so a check for "not an object" after parsing could never trigger; a branch no
        test can reach is usually dead code to delete."""),
    predict("Marks and their outcomes", "medium",
        code="""
        from lessontools import run_pytest

        SRC = '''
        import sys
        import pytest

        @pytest.mark.skip(reason="slow")
        def test_skipped():
            assert False

        @pytest.mark.skipif(sys.version_info < (3, 10), reason="needs match statements")
        def test_new_syntax():
            assert True

        @pytest.mark.xfail(reason="known tokenizer bug")
        def test_known_bug():
            assert 1 + 1 == 3

        @pytest.mark.xfail(reason="maybe fixed")
        def test_fixed_meanwhile():
            assert True

        @pytest.mark.xfail(strict=True, reason="must still fail")
        def test_strict():
            assert True

        @pytest.mark.parametrize("n", [1, pytest.param(2, marks=pytest.mark.xfail), pytest.param(3, id="three")])
        def test_odd(n):
            assert n % 2 == 1
        '''
        r = run_pytest(SRC)
        for name, outcome in r["outcomes"].items():
            print(f"{outcome:8} {name}")
        print(r["exit"])
        """,
        hints=["An xfail test that passes is `xpassed`, unless the mark is strict, in which case it fails."],
        why="""`skip` never runs the test, and `skipif` runs it because the condition is false on Python 3.14. A failing `xfail` test is reported as expected (`xfailed`); a
        passing one is `xpassed`, a hint that the bug was fixed. With `strict=True` that unexpected pass is a failure, which is what sets the exit code to 1. Marks
        can be attached to single parameter sets with `pytest.param`, and `id=` replaces the generated id."""),
)

section("hard", "Hard",
    write("Property tests for a dataset split", "hard", tag="ML",
        prompt="""`split(items, test_size, seed)` returns `(train, test)`: a shuffled copy of `items` (shuffled with `random.Random(seed)`), with `round(len(items) *
        test_size)` items in `test` and the rest in `train`; it never modifies `items`, and raises `ValueError` unless `0 < test_size < 1`. Write tests for
        **properties** that must hold for any input (sizes, no overlap, nothing lost, determinism, input untouched, different seeds giving different splits)
        rather than one hard-coded split. They must pass here and catch five buggy versions.""",
        code="""
        # --- code under test (do not edit) ---
        import random


        def split(items, test_size, seed):
            if not 0 < test_size < 1:
                raise ValueError("test_size must be between 0 and 1")
            shuffled = list(items)
            random.Random(seed).shuffle(shuffled)
            n_test = round(len(shuffled) * test_size)
            return shuffled[n_test:], shuffled[:n_test]


        # --- tests ---
        import pytest
        """,
        tests="""
        import pytest
        from lessontools import run_pytest, swap_impl
        good = run_pytest(__source__)
        assert good["failed"] == 0 and good["passed"] >= 5, good["output"][-800:]
        BUGS = {
            "mutates_input": '''
        import random
        def split(items, test_size, seed):
            if not 0 < test_size < 1:
                raise ValueError("test_size must be between 0 and 1")
            random.Random(seed).shuffle(items)
            n_test = round(len(items) * test_size)
            return items[n_test:], items[:n_test]
        ''',
            "ignores_seed": '''
        import random
        def split(items, test_size, seed):
            if not 0 < test_size < 1:
                raise ValueError("test_size must be between 0 and 1")
            shuffled = list(items)
            random.shuffle(shuffled)
            n_test = round(len(shuffled) * test_size)
            return shuffled[n_test:], shuffled[:n_test]
        ''',
            "overlap": '''
        import random
        def split(items, test_size, seed):
            if not 0 < test_size < 1:
                raise ValueError("test_size must be between 0 and 1")
            shuffled = list(items)
            random.Random(seed).shuffle(shuffled)
            n_test = round(len(shuffled) * test_size)
            return shuffled[n_test - 1:], shuffled[:n_test]
        ''',
            "truncates_size": '''
        import random
        def split(items, test_size, seed):
            if not 0 < test_size < 1:
                raise ValueError("test_size must be between 0 and 1")
            shuffled = list(items)
            random.Random(seed).shuffle(shuffled)
            n_test = int(len(shuffled) * test_size)
            return shuffled[n_test:], shuffled[:n_test]
        ''',
            "no_shuffle": '''
        import random
        def split(items, test_size, seed):
            if not 0 < test_size < 1:
                raise ValueError("test_size must be between 0 and 1")
            shuffled = list(items)
            n_test = round(len(shuffled) * test_size)
            return shuffled[n_test:], shuffled[:n_test]
        ''',
        }
        escaped = sorted(name for name, impl in BUGS.items() if run_pytest(swap_impl(__source__, impl))["failed"] == 0)
        assert escaped == []
        """,
        hints=["Use a list of distinct items such as `list(range(100))` and check `len(test)`, `set(train) & set(test)`, and `sorted(train + test)`.",
               "Determinism: the same seed twice gives the same split; seeds 1 and 2 give different test sets. Not shuffled: is the test set just the first items?",
               "Rounding: with 7 items and `test_size=0.3`, `round` gives 2 and `int` gives 2 as well; find a size where they differ, such as 9 items at 0.3."],
        solution="""
        # --- code under test (do not edit) ---
        import random


        def split(items, test_size, seed):
            if not 0 < test_size < 1:
                raise ValueError("test_size must be between 0 and 1")
            shuffled = list(items)
            random.Random(seed).shuffle(shuffled)
            n_test = round(len(shuffled) * test_size)
            return shuffled[n_test:], shuffled[:n_test]


        # --- tests ---
        import pytest

        ITEMS = list(range(100))


        @pytest.mark.parametrize("n,test_size,expected", [(100, 0.2, 20), (9, 0.3, 3), (10, 0.25, 2), (3, 0.5, 2)])
        def test_test_set_size_is_rounded(n, test_size, expected):
            train, test = split(list(range(n)), test_size, seed=0)
            assert len(test) == expected and len(train) == n - expected


        def test_no_overlap_and_nothing_lost():
            train, test = split(ITEMS, 0.2, seed=1)
            assert set(train).isdisjoint(test)
            assert sorted(train + test) == ITEMS


        def test_same_seed_same_split():
            assert split(ITEMS, 0.2, seed=42) == split(ITEMS, 0.2, seed=42)


        def test_different_seeds_differ_and_are_shuffled():
            _, a = split(ITEMS, 0.2, seed=1)
            _, b = split(ITEMS, 0.2, seed=2)
            assert a != b
            assert a != ITEMS[:20]


        def test_input_is_not_modified():
            items = list(range(10))
            split(items, 0.3, seed=3)
            assert items == list(range(10))


        @pytest.mark.parametrize("test_size", [0, 1, -0.1, 1.5])
        def test_rejects_bad_test_size(test_size):
            with pytest.raises(ValueError):
                split(ITEMS, test_size, seed=0)
        """,
        why="""A split cannot be checked against one hard-coded expected output without reimplementing the shuffle, so the tests check **properties** that any correct
        split has: the sizes, disjointness, the union being exactly the input, determinism for one seed, variation across seeds, an actual shuffle, and an
        untouched input. Each mutant breaks one property: shuffling in place changes the caller's list (a real bug in data pipelines, where the same list feeds
        several experiments), the global `random` ignores the seed, the off-by-one slice puts one item in both sets (data leakage), `int` truncates 2.7 to 2,
        and the unshuffled version puts the first items in the test set. Tools such as Hypothesis generate the inputs for property tests automatically; the
        properties themselves are the part you design."""),
    fix("Read the code: a fragile test module", "hard", tag="Data work",
        prompt="""This test module for `normalise_scores` has several problems: one test depends on another having run first through a shared list, one test is never
        collected, one compares floats exactly, one catches any `Exception`, and the suite misses the bug in the graded buggy version (which forgets to handle
        all-equal scores and raises `ZeroDivisionError`). Rewrite the tests so each is
        independent, collected, precise, and the bug is caught.""",
        code="""
        # --- code under test (do not edit) ---
        def normalise_scores(scores):
            # min-max scaling to [0, 1]; all-equal scores map to 0.0; empty input gives []
            if not scores:
                return []
            lo, hi = min(scores), max(scores)
            if hi == lo:
                return [0.0 for _ in scores]
            return [(s - lo) / (hi - lo) for s in scores]


        # --- tests ---
        import pytest

        RESULTS = []


        def test_basic():
            RESULTS.extend(normalise_scores([1, 2, 3]))
            assert RESULTS[0] == 0.0


        def test_middle_value():
            assert RESULTS[1] == 0.5


        def check_top_value():
            assert normalise_scores([1, 2, 3])[2] == 1.0


        def test_fractions():
            assert normalise_scores([0.1, 0.2, 0.4]) == [0.0, 0.3333333333333333, 1.0]


        def test_bad_input():
            with pytest.raises(Exception):
                normalise_scores([1, "a"])
        """,
        tests="""
        import pytest
        from lessontools import run_pytest, swap_impl
        tests_part = __source__.split("# --- tests")[1]
        good = run_pytest(__source__)
        assert good["failed"] == 0 and good["passed"] >= 4, good["output"][-800:]
        alone = run_pytest(__source__, args=["-k", "middle or top"])
        assert alone["failed"] == 0 and "RESULTS" not in tests_part and "check_" not in tests_part
        assert "pytest.raises(Exception)" not in tests_part
        BUG = '''
        def normalise_scores(scores):
            if not scores:
                return []
            lo, hi = min(scores), max(scores)
            return [(s - lo) / (hi - lo) for s in scores]
        '''
        assert run_pytest(swap_impl(__source__, BUG))["failed"] > 0
        """,
        hints=["Give each test its own input and expected output; rename `check_top_value` to start with `test_`.",
               "Use `pytest.approx` for the fractions, `pytest.raises(TypeError)` for mixed types, and add the all-equal and empty cases."],
        solution="""
        # --- code under test (do not edit) ---
        def normalise_scores(scores):
            # min-max scaling to [0, 1]; all-equal scores map to 0.0; empty input gives []
            if not scores:
                return []
            lo, hi = min(scores), max(scores)
            if hi == lo:
                return [0.0 for _ in scores]
            return [(s - lo) / (hi - lo) for s in scores]


        # --- tests ---
        import pytest


        def test_scales_to_unit_interval():
            assert normalise_scores([1, 2, 3]) == [0.0, 0.5, 1.0]


        def test_middle_value():
            assert normalise_scores([1, 2, 3])[1] == 0.5


        def test_top_value():
            assert normalise_scores([1, 2, 3])[2] == 1.0


        def test_fractions():
            assert normalise_scores([0.1, 0.2, 0.4]) == pytest.approx([0.0, 1 / 3, 1.0])


        def test_all_equal_scores_map_to_zero():
            assert normalise_scores([0.7, 0.7]) == [0.0, 0.0]


        def test_empty_input():
            assert normalise_scores([]) == []


        def test_mixed_types_raise_type_error():
            with pytest.raises(TypeError):
                normalise_scores([1, "a"])
        """,
        why="""Each problem is a common way test suites rot. A test that reads state written by another passes only when run in that order, so `pytest -k middle` or a
        parallel run breaks it; every test must arrange its own data. A function not named `test_*` is silently skipped, giving a false sense of coverage. The
        exact float comparison happens to pass today but breaks on another platform or after a harmless refactor, while `approx` states the intended precision.
        `pytest.raises(Exception)` passes for **any** error, including a bug that raises `NameError`; name the expected type. Finally, the missing edge case
        (all scores equal, which happens whenever a retriever returns identical scores) is exactly where the buggy version divides by zero."""),
    write("A tiny test runner", "hard", tag="Data work",
        prompt="""To see what pytest does underneath, write `run_tests(namespace)`. It finds callables whose names start with `test` in `namespace` (a dict, in insertion
        order), runs each, and records `"passed"`, `"failed"` (an `AssertionError`) or `f"error: {ExceptionName}"` (any other exception). A function with a
        `params` attribute (a list of argument tuples, set by the decorator `parametrize(*cases)` that you also write) runs once per tuple, recorded as
        `f"{name}[{i}]"`. Return the dict of results.""",
        code="""
        def parametrize(*cases):
            pass

        def run_tests(namespace):
            pass
        """,
        tests="""
        def add(a, b):
            return a + b

        def test_add():
            assert add(2, 2) == 4

        def test_wrong():
            assert add(2, 2) == 5

        def test_crash():
            return {}["missing"]

        @parametrize((1, 2, 3), (0, 0, 0), (2, 2, 5))
        def test_cases(a, b, expected):
            assert add(a, b) == expected

        def helper_not_a_test():
            raise RuntimeError

        test_value = 42

        ns = {"add": add, "test_add": test_add, "test_wrong": test_wrong, "test_crash": test_crash, "test_cases": test_cases,
              "helper_not_a_test": helper_not_a_test, "test_value": test_value}
        results = run_tests(ns)
        assert results == {"test_add": "passed", "test_wrong": "failed", "test_crash": "error: KeyError",
                           "test_cases[0]": "passed", "test_cases[1]": "passed", "test_cases[2]": "failed"}
        assert test_cases.params == [(1, 2, 3), (0, 0, 0), (2, 2, 5)] and test_cases(1, 1, 2) is None
        """,
        hints=["`parametrize` returns a decorator that sets `fn.params = list(cases)` and returns `fn` unchanged.",
               "In the runner, `getattr(fn, \"params\", None)` decides between one call and one call per tuple; a small inner function records one outcome."],
        solution="""
        def parametrize(*cases):
            def decorator(fn):
                fn.params = list(cases)
                return fn
            return decorator


        def _outcome(fn, args):
            try:
                fn(*args)
            except AssertionError:
                return "failed"
            except Exception as e:
                return f"error: {type(e).__name__}"
            return "passed"


        def run_tests(namespace):
            results = {}
            for name, fn in namespace.items():
                if not name.startswith("test") or not callable(fn):
                    continue
                params = getattr(fn, "params", None)
                if params is None:
                    results[name] = _outcome(fn, ())
                else:
                    for i, args in enumerate(params):
                        results[f"{name}[{i}]"] = _outcome(fn, args)
            return results
        """,
        why="""This is pytest's core loop in miniature: discovery by naming convention (`test_value` is skipped because it is not callable), one isolated call per test with
        exceptions turned into outcomes, and parametrisation implemented as metadata attached by a decorator (8.3) that the runner reads, which is literally how
        `pytest.mark.parametrize` works: marks are stored on the function and expanded at collection time. Distinguishing a failed assertion from another
        exception mirrors pytest's report, where a `KeyError` points to a broken test or code rather than a wrong value. What pytest adds is fixtures (13.2),
        assertion rewriting, plugins and rich reporting."""),
    predict("Stacked parametrize and ids", "hard",
        code="""
        from lessontools import run_pytest

        SRC = '''
        import pytest

        @pytest.mark.parametrize("model", ["small", "large"])
        @pytest.mark.parametrize("temperature", [0.0, 0.7])
        def test_settings(model, temperature):
            assert not (model == "large" and temperature > 0.5)

        @pytest.mark.parametrize("text,expected", [("a", 1), ("", 0)], ids=["one-char", "empty"])
        def test_length(text, expected):
            assert len(text) == expected
        '''
        r = run_pytest(SRC)
        for name, outcome in r["outcomes"].items():
            print(f"{outcome:7} {name}")
        print(r["passed"], r["failed"])
        """,
        hints=["Two stacked `parametrize` decorators give every combination. The decorator closest to the function contributes the first part of each id."],
        why="""Stacking produces the Cartesian product, 2 models times 2 temperatures, as four separate tests; the id joins the values with `-`, starting with the innermost
        decorator's value (`0.0-small`), and in the run order the outer parameter, the model, changes fastest. Only the large model at temperature 0.7 fails. Explicit `ids` replace the generated ones, which
        matters when values are long strings or objects whose generated ids are unreadable."""),
)

section("interview", "Interview questions",
    explain("What makes a good unit test?", "medium", tag="Interview",
        why="""A good unit test fails when the behaviour it covers is broken and passes otherwise, reliably. Concretely: it tests one behaviour through the public interface,
        with a name that states that behaviour, so a failure explains itself; it follows arrange, act, assert and asserts the specific expected value, not just
        "something truthy"; it is deterministic (no real clock, network, unseeded randomness, shared state or test order) and fast, so it can run on every
        change; it is independent of other tests and cleans up after itself; it covers edge cases and error paths, not only the happy path; and it is
        resilient to refactoring because it checks outcomes, not implementation details such as which private helper was called. A useful check of a test's
        value is whether it would catch a plausible bug: break the code deliberately and see it fail. Coverage percentages measure what code ran, not what
        was verified."""),
    explain("Why does pytest use plain assert statements, and how does it show useful failure messages?", "medium", tag="Interview",
        why="""Plain `assert` keeps tests short and readable: `assert result == expected` instead of a family of methods such as `assertEqual`, `assertIn`, `assertAlmostEqual`.
        Normally a failed `assert` only raises a bare `AssertionError`, so pytest **rewrites** the assert statements in test modules when it imports them,
        through an import hook that transforms the module's syntax tree: each assert is expanded into code that saves intermediate values, and on failure
        builds a message showing them, such as `assert 4 == 5` where `4 = add(2, 2)`, and diffs for long strings, lists and dicts. That is why it only works in
        test files and modules registered for rewriting (helpers can be registered with `pytest.register_assert_rewrite`), and why running Python with `-O`,
        which strips asserts, must never be used for tests."""),
    explain("What is a flaky test, what causes it, and what do you do about it?", "hard", tag="Interview",
        why="""A flaky test passes and fails on the same code. Common causes: dependence on test **order** or shared state (module globals, files, databases, environment
        variables left behind); **time** (the current date, time zones, timeouts, `sleep`-based waits); unseeded **randomness**; **concurrency** races; real
        **network** calls and external services; floating-point comparisons that depend on platform; and leaking resources. Flaky tests are harmful because
        people learn to ignore red builds and rerun until green, so real failures get missed. Fix them rather than retrying: isolate state with fixtures and
        temporary directories (13.2), freeze or inject the clock, seed randomness, replace network calls with fakes or mocks (13.3), wait on conditions instead of
        sleeping, and use `approx` for floats. To find them, run the suite in random order (`pytest-randomly`) and repeatedly, and quarantine (mark and track)
        a flaky test only as a short-term measure with an owner and a deadline. For LLM-dependent tests, keep model calls out of unit tests entirely (13.4)."""),
)

recap(
    "pytest collects `test_*` functions in `test_*.py` files (and `test_*` methods of `Test*` classes); any exception fails a test, so assert something specific.",
    "Plain `assert` is rewritten to show values; compare whole results, use `pytest.approx` for floats, and set `abs=` near zero.",
    "`pytest.raises(Type, match=...)` checks errors; keep only the raising call inside the block.",
    "`@pytest.mark.parametrize` turns a table of cases into separate tests; choose empty, boundary, invalid and unusual inputs deliberately.",
    "Marks skip or expect failures (`strict=True` keeps xfail honest); judge tests by whether they catch real bugs, as mutation testing does.",
)
