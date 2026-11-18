from lesson import *
from diagrams import *

lesson(
    id="m13-4", num="13.4", title="Testing ML and GenAI code",
    intro="ML and LLM systems add three difficulties to testing: numbers that are only approximately right, randomness, and models "
          "whose quality is a statistic rather than a yes or no. What to unit-test and what to evaluate instead, tolerances with "
          "NumPy, seeds and determinism, property and invariance tests, data validation, smoke training tests, prompt and parser "
          "tests, and evaluation gates for LLM changes.",
    desc="Tolerances, seeds, property and invariance tests, data checks, LLM parsers and evaluation gates.",
    keys="testing machine learning numpy testing assert_allclose rtol atol seed default_rng determinism property test metamorphic invariance data validation leakage smoke test training loss decreases llm evaluation golden set threshold regression gate prompt test parser",
)

term("Evaluation set", "A fixed collection of inputs with expected outputs or grading rules, used to measure a model's quality; separate from unit tests, which check code.")
term("Property test", "A test that checks a rule which must hold for any input (probabilities sum to 1, output shape matches input), instead of one exact expected value.")
term("Metamorphic test", "A test that changes the input in a way that should not change the answer (or should change it predictably) and checks that the model agrees.")

section("layers", "What to test, and what to evaluate",
    fig(table(["layer", "checks", "how often"], [
        ["unit tests", "loaders, features, parsers, metrics, prompts", "every change"],
        ["behaviour tests", "properties, shapes, a tiny model trains", "every change"],
        ["evaluation", "accuracy or quality on a dataset", "per model or prompt change"],
    ], label="what to test and what to evaluate"),
        "Ordinary code gets exact tests; the model gets measured with datasets and thresholds."),
    p("""An ML or LLM system is ordinary code around a model. The ordinary code, which is most of it, gets ordinary **unit tests**: data loading and cleaning,
    feature functions, tokenisation and chunking, metric implementations, prompt builders, output parsers and validators, routing and retry logic. These are
    deterministic, or can be made so, and every bug in them corrupts results silently, so they deserve the most tests. The model itself is different:
    "the classifier is good" is not true or false for one input, it is an accuracy of 0.93 on a dataset. That is measured by **evaluation**, with datasets,
    metrics and thresholds, run less often and reported as numbers."""),
    p("""Between the two sit tests that check **behaviour without exact answers**: property tests (outputs are probabilities, shapes match, a scaler's output has
    mean 0), **smoke training tests** (a tiny model on a tiny dataset reaches perfect accuracy and its loss decreases, which catches broken gradients in
    seconds), **data validation** (schemas, ranges, duplicates, leakage between splits), and **invariance tests** (changing the case of an e-mail should not
    change its spam label). A healthy project has many fast unit tests, some of these behavioural tests, and an evaluation suite gating model and prompt changes."""),
)

section("numbers", "Numbers: tolerances and dtypes",
    p("""Floating-point results depend on the order of operations, the library version, the hardware and the dtype, so exact equality is almost never the right check for
    computed values. For NumPy arrays, use **`np.testing.assert_allclose(actual, expected, rtol=1e-7, atol=0)`**: it passes when `|actual - expected| <= atol +
    rtol * |expected|` element-wise, checks shapes, and reports how many elements mismatch and by how much. Choose tolerances deliberately: `float32`
    computations (most deep learning) carry about 7 significant digits, so `rtol=1e-5` is realistic, and values near zero need an `atol`. `np.testing.assert_array_equal`
    is for exact integer or boolean arrays (and treats NaNs in the same places as equal, unlike `==`). Check **dtypes and shapes** explicitly too: a feature
    matrix that silently became `int64` or `(n,)` instead of `(n, 1)` is a common bug."""),
    ex("""
    import numpy as np

    a = np.array([0.1 + 0.2, 1e-9, 100.0])
    b = np.array([0.3, 0.0, 100.0001])
    print(np.array_equal(a, b), np.allclose(a, b))
    try:
        np.testing.assert_allclose(a, b)
    except AssertionError as e:
        print([line.strip() for line in str(e).splitlines() if line.strip().startswith("Mismatched")])
    np.testing.assert_allclose(a, b, rtol=1e-5, atol=1e-8)
    print(np.float32(0.1) == 0.1, np.float32(1 / 3).dtype, np.array([1, 2]).dtype)
    np.testing.assert_array_equal(np.array([1.0, np.nan]), np.array([1.0, np.nan]))
    print(np.array_equal(np.array([np.nan]), np.array([np.nan])))
    """, "tolerances.py"),
)

section("seeds", "Randomness and determinism",
    fig(chain(["seed every source|(random, numpy, model)", "same seed,|same numbers", ("a failing test|fails the same way", "good")]),
        "Fixing seeds makes randomness repeatable, so a test either always passes or always fails."),
    p("""Shuffles, splits, initial weights, sampling and data augmentation all use random numbers. A test that depends on them must control them, and so should
    production code, for reproducible experiments. The robust pattern is to **pass a generator in**: `rng = np.random.default_rng(seed)` or `random.Random(seed)`,
    given to every function that needs randomness, rather than calling the global `np.random.rand` or `random.random`, whose state any other code can change.
    Two generators with the same seed produce the same sequence; one generator used twice produces different numbers each time, so "same seed, same result" tests
    create a fresh generator for each run (problem 3)."""),
    p("""Some randomness cannot be seeded from Python: GPU kernels with non-deterministic reductions, multi-threaded data loaders, and LLM sampling, where even
    temperature 0 is not guaranteed to be identical across calls. For those, test **properties and tolerances**, run several samples and check aggregate
    behaviour, or move the model call out of the unit test entirely."""),
)

section("data", "Testing data",
    p("""Most ML failures are data failures: a column that changed type upstream, labels outside the expected set, duplicated examples, missing values encoded as
    `-1`, or the same customer in both training and test sets (**leakage**, which inflates offline metrics and disappoints in production). These are tested like
    any contract: a validation function returns a list of problems for a batch, unit tests check the validator, and the pipeline runs it on every new batch and
    refuses to train on bad data (problem 6). Libraries such as Pandera, Great Expectations and Pydantic (11.4) formalise the schemas; the checks themselves are
    simple code."""),
)

section("llm", "Testing LLM applications",
    p("""Split an LLM feature into deterministic parts and the model call. **Prompt builders** get unit tests on structure (the context and the question are present, the
    instructions come first, long context is truncated within budget), not on exact wording, which changes often; when an exact template matters, a **snapshot**
    (golden file) test stores the expected prompt and is updated deliberately. **Output parsers and validators** get tests with realistic, messy replies collected
    from real runs: code fences, extra prose, wrong case, missing fields, truncated JSON (13.1 problem 9, 11.4). **Orchestration** (retries, tool loops,
    fallbacks) is tested with fakes (13.3). None of this needs a real model."""),
    p("""Quality is **evaluated**: a versioned evaluation set of inputs with expected answers or grading rules (exact match, contained facts, valid JSON, a rubric scored
    by a judge model), run against the real model when the prompt, the model or the retrieval changes, and compared with the previous **baseline**. A CI gate
    fails the change if a metric drops below a threshold or regresses by more than a tolerance (problem 10). Because outputs vary, evaluations use enough cases to
    be statistically meaningful, report confidence intervals or several runs, and track cost and latency alongside quality."""),
)

section("warmup", "Warm-up",
    predict("NumPy comparisons", "easy",
        code="""
        import numpy as np

        def check(fn):
            try:
                fn()
                return "pass"
            except AssertionError:
                return "fail"

        x = np.array([1.0, 2.0, 3.0])
        print(check(lambda: np.testing.assert_allclose(x + 1e-9, x)), check(lambda: np.testing.assert_allclose(x + 1e-3, x)))
        print(check(lambda: np.testing.assert_allclose(x + 1e-3, x, rtol=1e-3)), check(lambda: np.testing.assert_allclose([0.0], [1e-9])))
        print(check(lambda: np.testing.assert_allclose([0.0], [1e-9], atol=1e-8)), check(lambda: np.testing.assert_allclose(x, x[:2])))
        print(check(lambda: np.testing.assert_array_equal([1, np.nan], [1, np.nan])), bool(np.all(np.array([np.nan]) == np.array([np.nan]))))
        r1, r2 = np.random.default_rng(7), np.random.default_rng(7)
        print(np.array_equal(r1.random(3), r2.random(3)), np.array_equal(r1.random(3), r1.random(3)))
        """,
        hints=["The default `rtol` is `1e-7` and the default `atol` is 0. Shapes must match. NaN is never equal to NaN with `==`."],
        why="""A difference of `1e-9` is far below `1e-7` relative tolerance, but `1e-3` is not, until `rtol=1e-3` allows it (the largest relative error is 0.001 at the
        element 1.0). With `atol` 0, nothing is "close" to exactly 0 except 0, so comparisons near zero need an absolute tolerance. Different shapes always fail.
        `assert_array_equal` treats NaNs in matching positions as equal, while `==` says NaN differs from itself. Two generators with the same seed give the same
        numbers, but one generator moves on, so consecutive draws differ."""),
    write("Test a standard scaler", "easy", tag="ML",
        prompt="""`StandardScaler` learns each column's mean and standard deviation in `fit(X)` and `transform(X)` returns `(X - mean) / std`, using 1 instead of 0 for
        constant columns, always as `float64`, without modifying the input. Write at least four tests with `np.testing.assert_allclose` that pass here and catch
        four buggy versions. Use small arrays whose expected output you can work out by hand.""",
        code="""
        # --- code under test (do not edit) ---
        import numpy as np


        class StandardScaler:
            def fit(self, X):
                X = np.asarray(X, dtype=np.float64)
                self.mean_ = X.mean(axis=0)
                std = X.std(axis=0)
                self.std_ = np.where(std == 0, 1.0, std)
                return self

            def transform(self, X):
                X = np.asarray(X, dtype=np.float64)
                return (X - self.mean_) / self.std_


        # --- tests ---
        import numpy as np
        import pytest
        """,
        tests="""
        import numpy, pytest
        from lessontools import run_pytest, swap_impl
        good = run_pytest(__source__)
        assert good["failed"] == 0 and good["passed"] >= 4, good["output"][-800:]
        BASE = __source__.split("# --- code under test (do not edit) ---")[1].split("# --- tests")[0]
        BUGS = {
            "global_stats": BASE.replace("X.mean(axis=0)", "X.mean()").replace("X.std(axis=0)", "X.std()"),
            "zero_std_nan": BASE.replace("np.where(std == 0, 1.0, std)", "std"),
            "refits_on_transform": BASE.replace("        return (X - self.mean_) / self.std_", "        return (X - X.mean(axis=0)) / self.std_"),
            "int_dtype_kept": BASE.replace("        X = np.asarray(X, dtype=np.float64)\\n        return", "        X = np.asarray(X)\\n        return").replace("return (X - self.mean_) / self.std_", "return ((X - self.mean_) / self.std_).astype(X.dtype)"),
        }
        assert all(b != BASE for b in BUGS.values()), [k for k, b in BUGS.items() if b == BASE]
        escaped = sorted(name for name, impl in BUGS.items() if run_pytest(swap_impl(__source__, impl))["failed"] == 0)
        assert escaped == []
        """,
        hints=["`X = [[1, 10], [3, 30]]` has column means 2 and 20 and standard deviations 1 and 10, so the result is `[[-1, -1], [1, 1]]`.",
               "Transform **new** data with the fitted statistics: `[[5, 20]]` must give `[[3, 0]]`. A constant column must become zeros, not NaN. Pass integers and check the dtype."],
        solution="""
        # --- code under test (do not edit) ---
        import numpy as np


        class StandardScaler:
            def fit(self, X):
                X = np.asarray(X, dtype=np.float64)
                self.mean_ = X.mean(axis=0)
                std = X.std(axis=0)
                self.std_ = np.where(std == 0, 1.0, std)
                return self

            def transform(self, X):
                X = np.asarray(X, dtype=np.float64)
                return (X - self.mean_) / self.std_


        # --- tests ---
        import numpy as np
        import pytest

        TRAIN = np.array([[1, 10], [3, 30]])


        @pytest.fixture
        def scaler():
            return StandardScaler().fit(TRAIN)


        def test_per_column_statistics(scaler):
            np.testing.assert_allclose(scaler.mean_, [2.0, 20.0])
            np.testing.assert_allclose(scaler.transform(TRAIN), [[-1.0, -1.0], [1.0, 1.0]])


        def test_new_data_uses_fitted_statistics(scaler):
            np.testing.assert_allclose(scaler.transform([[5, 20]]), [[3.0, 0.0]])


        def test_constant_column_becomes_zeros():
            X = np.array([[1.0, 7.0], [3.0, 7.0]])
            out = StandardScaler().fit(X).transform(X)
            assert not np.isnan(out).any()
            np.testing.assert_allclose(out[:, 1], [0.0, 0.0])


        def test_output_is_float64_and_input_untouched(scaler):
            X = TRAIN.copy()
            out = scaler.transform(X)
            assert out.dtype == np.float64
            np.testing.assert_array_equal(X, TRAIN)
        """,
        why="""Two rows per column make the expected output easy to derive by hand (mean halfway, population standard deviation half the gap), so the test states the
        exact answer with `assert_allclose` rather than re-computing it with the same formula, which would only prove the code agrees with itself. The second test
        captures the most important rule of preprocessing: **transform** uses the statistics learned in **fit**; a version that re-centres each new batch on its own
        mean leaks information and makes a single-row batch always zero. The constant-column and dtype tests cover the edge cases that silently produce NaNs or
        truncated integers in a real pipeline."""),
    fix("A test that depends on unseeded randomness", "easy", tag="ML",
        prompt="""`bootstrap_ci(values, n, rng)` estimates a confidence interval by resampling with the generator it is given. The test creates an **unseeded** generator and
        compares against numbers copied from one run, so it fails almost every time. Fix the test: make it deterministic with a seeded generator, check that two
        generators with the same seed give the same interval, and check properties that hold for any seed (lower bound not above upper, both within the data
        range).""",
        code="""
        # --- code under test (do not edit) ---
        import numpy as np


        def bootstrap_ci(values, n, rng, level=0.9):
            values = np.asarray(values, dtype=float)
            means = np.array([rng.choice(values, size=len(values), replace=True).mean() for _ in range(n)])
            lo, hi = np.quantile(means, [(1 - level) / 2, 1 - (1 - level) / 2])
            return float(lo), float(hi)


        # --- tests ---
        import numpy as np


        def test_bootstrap():
            rng = np.random.default_rng()
            assert bootstrap_ci([1, 2, 3, 4, 5], 200, rng) == (2.2, 3.8)
        """,
        tests="""
        import numpy, pytest
        from lessontools import run_pytest, swap_impl
        runs = [run_pytest(__source__) for _ in range(3)]
        assert all(r["failed"] == 0 and r["passed"] >= 2 for r in runs), runs[0]["output"][-800:]
        tests_part = __source__.split("# --- tests")[1]
        assert "default_rng()" not in tests_part
        BUG = '''
        import numpy as np


        def bootstrap_ci(values, n, rng, level=0.9):
            values = np.asarray(values, dtype=float)
            means = np.array([np.random.choice(values, size=len(values), replace=True).mean() for _ in range(n)])
            lo, hi = np.quantile(means, [(1 - level) / 2, 1 - (1 - level) / 2])
            return float(lo), float(hi)
        '''
        assert any(run_pytest(swap_impl(__source__, BUG))["failed"] > 0 for _ in range(3))
        """,
        hints=["`np.random.default_rng(0)` twice, called separately, must give identical intervals: that also catches code that ignores the generator.",
               "Use data with many distinct values, then check `min(DATA) <= lo <= hi <= max(DATA)` for several seeds, with `@pytest.mark.parametrize(\"seed\", [0, 1, 2])`."],
        solution="""
        # --- code under test (do not edit) ---
        import numpy as np


        def bootstrap_ci(values, n, rng, level=0.9):
            values = np.asarray(values, dtype=float)
            means = np.array([rng.choice(values, size=len(values), replace=True).mean() for _ in range(n)])
            lo, hi = np.quantile(means, [(1 - level) / 2, 1 - (1 - level) / 2])
            return float(lo), float(hi)


        # --- tests ---
        import numpy as np
        import pytest

        DATA = [0.3, 1.7, 2.2, 2.9, 3.4, 4.1, 4.8, 5.6, 6.3, 7.9]


        def test_same_seed_same_interval():
            a = bootstrap_ci(DATA, 200, np.random.default_rng(0))
            b = bootstrap_ci(DATA, 200, np.random.default_rng(0))
            assert a == b


        @pytest.mark.parametrize("seed", [0, 1, 2])
        def test_interval_is_ordered_and_within_data_range(seed):
            lo, hi = bootstrap_ci(DATA, 200, np.random.default_rng(seed))
            assert min(DATA) <= lo <= hi <= max(DATA)


        def test_interval_contains_sample_mean():
            lo, hi = bootstrap_ci(DATA, 500, np.random.default_rng(3))
            assert lo <= np.mean(DATA) <= hi
        """,
        why="""An unseeded generator gives different numbers on every run, so a test with copied values is flaky by construction. A seeded generator makes runs repeatable,
        and comparing **two fresh generators with the same seed** is the right determinism check; it also exposes code that ignores the generator and uses the
        global NumPy random state (the graded bug), which no seed passed to the function can control. The other tests check properties that hold whatever the
        seed, which keeps them valid if the algorithm changes, unlike golden numbers. The data matters too: with `[1, 2, 3, 4, 5]` the resampled means take few
        distinct values, so two unseeded runs give the same interval about one time in five and the determinism test would sometimes miss the bug. The grader
        ran the suite three times to make sure it is stable."""),
    predict("Why property tests catch overflow", "easy",
        code="""
        import numpy as np

        def softmax_naive(z):
            e = np.exp(z)
            return e / e.sum()

        def softmax_stable(z):
            e = np.exp(z - np.max(z))
            return e / e.sum()

        small = np.array([1.0, 2.0, 3.0])
        large = np.array([1000.0, 1001.0, 1002.0])
        with np.errstate(over="ignore", invalid="ignore"):
            print(np.round(softmax_naive(small), 3), np.round(softmax_stable(small), 3))
            print(softmax_naive(large), np.round(softmax_stable(large), 3))
            print(np.isclose(softmax_naive(large).sum(), 1.0), np.isclose(softmax_stable(large).sum(), 1.0))
        """,
        hints=["`exp(1000)` overflows a float64 to infinity, and infinity divided by infinity is NaN. Subtracting the maximum changes nothing mathematically."],
        why="""On ordinary inputs both versions agree, so a test with only "nice" values would pass the naive one. With large logits, which real models produce, the exponentials
        overflow to infinity and the result is NaN. A **property** test ("outputs are finite, non-negative and sum to 1, for small and large inputs") fails for the
        naive version immediately. The stable version subtracts the maximum, which leaves the result unchanged but keeps every exponent at most 0."""),
)

section("medium", "Medium",
    write("Test precision, recall and F1", "medium", tag="ML",
        prompt="""`prf(y_true, y_pred, positive)` returns `(precision, recall, f1)` for the given positive label, with 0.0 when a ratio's denominator is zero. Write at least
        five tests with hand-computed expectations (use `pytest.approx`), including the edge cases. They must pass here and catch five buggy versions.""",
        code="""
        # --- code under test (do not edit) ---
        def prf(y_true, y_pred, positive):
            tp = sum(t == positive and p == positive for t, p in zip(y_true, y_pred))
            fp = sum(t != positive and p == positive for t, p in zip(y_true, y_pred))
            fn = sum(t == positive and p != positive for t, p in zip(y_true, y_pred))
            precision = tp / (tp + fp) if tp + fp else 0.0
            recall = tp / (tp + fn) if tp + fn else 0.0
            f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
            return precision, recall, f1


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
            "swapped": BASE.replace("    return precision, recall, f1", "    return recall, precision, f1"),
            "zero_division": BASE.replace("tp / (tp + fp) if tp + fp else 0.0", "tp / (tp + fp)"),
            "arithmetic_mean": BASE.replace("2 * precision * recall / (precision + recall) if precision + recall else 0.0", "(precision + recall) / 2"),
            "label_one": BASE.replace("p == positive for t, p in zip(y_true, y_pred))\\n    fn", "p == 1 for t, p in zip(y_true, y_pred))\\n    fn"),
            "fn_counts_tn": BASE.replace("fn = sum(t == positive and p != positive", "fn = sum(t != positive and p != positive"),
        }
        assert all(b != BASE for b in BUGS.values()), [k for k, b in BUGS.items() if b == BASE]
        escaped = sorted(name for name, impl in BUGS.items() if run_pytest(swap_impl(__source__, impl))["failed"] == 0)
        assert escaped == []
        """,
        hints=["Pick a case where precision and recall differ, for example 2 true positives, 1 false positive and 3 false negatives: precision 2/3, recall 2/5.",
               "Use string labels (`\"spam\"`, `\"ham\"`) so a version that assumes the label 1 fails; include a case with no predicted positives and one with true negatives."],
        solution="""
        # --- code under test (do not edit) ---
        def prf(y_true, y_pred, positive):
            tp = sum(t == positive and p == positive for t, p in zip(y_true, y_pred))
            fp = sum(t != positive and p == positive for t, p in zip(y_true, y_pred))
            fn = sum(t == positive and p != positive for t, p in zip(y_true, y_pred))
            precision = tp / (tp + fp) if tp + fp else 0.0
            recall = tp / (tp + fn) if tp + fn else 0.0
            f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
            return precision, recall, f1


        # --- tests ---
        import pytest

        S, H = "spam", "ham"


        def test_mixed_case_by_hand():
            # tp=2, fp=1, fn=3, tn=1
            y_true = [S, S, H, S, S, S, H]
            y_pred = [S, S, S, H, H, H, H]
            p, r, f = prf(y_true, y_pred, S)
            assert (p, r) == pytest.approx((2 / 3, 2 / 5))
            assert f == pytest.approx(2 * (2 / 3) * (2 / 5) / (2 / 3 + 2 / 5))


        def test_true_negatives_do_not_count():
            p, r, f = prf([S, H, H, H], [S, H, H, H], S)
            assert (p, r, f) == pytest.approx((1.0, 1.0, 1.0))


        def test_no_predicted_positives_gives_zero_precision():
            assert prf([S, H], [H, H], S) == (0.0, 0.0, 0.0)


        def test_all_wrong():
            assert prf([S, H], [H, S], S) == (0.0, 0.0, 0.0)


        def test_other_label_as_positive():
            p, r, f = prf([S, H, H], [H, H, S], H)
            assert (p, r) == pytest.approx((0.5, 0.5))
        """,
        why="""Metric code is where silent bugs do the most damage: a swapped precision and recall or an arithmetic mean instead of the harmonic one still produces plausible
        numbers, and every model comparison built on them is wrong. Hand-computed cases where precision and recall **differ** catch swaps and the wrong mean; string
        labels catch code that assumes the positive class is `1`; true negatives in the data catch formulas that count them; and the empty-denominator cases pin the
        convention (0.0 rather than an exception or NaN, as scikit-learn's `zero_division=0` does). Comparing against an independent hand calculation, not the
        same formula, is what makes the tests meaningful."""),
    write("Validate a training batch", "medium", tag="Data work",
        prompt="""Write `validate_batch(rows, labels, max_text=2000)` returning a sorted list of problem strings for a list of dict rows: `"row N: missing KEY"` for each of
        `id`, `text`, `label` absent; `"row N: text must be a non-empty string"`; `"row N: text longer than MAX"`; `"row N: unknown label 'X'"`; and
        `"duplicate id 'X'"` once per repeated id. Rows are numbered from 1. An empty list means the batch is valid.""",
        code="""
        def validate_batch(rows, labels, max_text=2000):
            pass
        """,
        tests="""
        rows = [
            {"id": "a", "text": "Win a prize", "label": "spam"},
            {"id": "b", "text": "", "label": "ham"},
            {"id": "c", "label": "ham"},
            {"id": "a", "text": "Lunch?", "label": "Ham"},
            {"text": "x" * 25, "label": "ham"},
            {"id": "e", "text": 42, "label": "phish"},
            {"id": "a", "text": "again", "label": "spam"},
        ]
        problems = validate_batch(rows, {"spam", "ham", "phish"}, max_text=20)
        assert problems == sorted([
            "row 2: text must be a non-empty string", "row 3: missing text", "row 4: unknown label 'Ham'",
            "row 5: missing id", "row 5: text longer than 20", "row 6: text must be a non-empty string", "duplicate id 'a'",
        ])
        assert validate_batch(rows[:1], {"spam"}) == [] and validate_batch([], {"spam"}) == []
        """,
        hints=["Loop with `enumerate(rows, start=1)`; check missing keys first and skip value checks for keys that are missing.",
               "Count ids with a `Counter` (ignoring rows without an id) and add one message per id seen more than once."],
        solution="""
        from collections import Counter


        def validate_batch(rows, labels, max_text=2000):
            problems = []
            for n, row in enumerate(rows, start=1):
                for key in ("id", "text", "label"):
                    if key not in row:
                        problems.append(f"row {n}: missing {key}")
                if "text" in row:
                    text = row["text"]
                    if not isinstance(text, str) or not text.strip():
                        problems.append(f"row {n}: text must be a non-empty string")
                    elif len(text) > max_text:
                        problems.append(f"row {n}: text longer than {max_text}")
                if "label" in row and row["label"] not in labels:
                    problems.append(f"row {n}: unknown label {row['label']!r}")
            counts = Counter(row["id"] for row in rows if "id" in row)
            problems.extend(f"duplicate id {i!r}" for i, c in counts.items() if c > 1)
            return sorted(problems)
        """,
        why="""A validation function that **collects** every problem, with row numbers, is what a data pipeline needs: one run tells the data owner everything to fix, instead
        of one error per attempt. The checks mirror the common silent failures: missing fields, empty or non-string text (a number where text belongs often
        means a shifted CSV column), oversize inputs that would be truncated by a tokenizer, labels with the wrong case (`"Ham"` becomes a fourth class) and
        duplicates, which inflate metrics when copies land in both training and test sets. The function is pure, so it is trivially unit-tested, and the
        pipeline can refuse to train when the list is not empty."""),
    fix("A prompt test that breaks every day", "medium", tag="GenAI",
        prompt="""`build_prompt(question, chunks, today=None)` puts today's date in the system part. The test compares the whole prompt to a string containing the date on which
        it was written, so it fails on every other day, and it is so exact that harmless wording changes would break it too. Fix it: pass a fixed `today`, and assert
        the **structure** that matters (date line, every chunk with its source, the question last), so it still catches the graded buggy versions.""",
        code="""
        # --- code under test (do not edit) ---
        from datetime import date


        def build_prompt(question, chunks, today=None):
            today = today or date.today()
            lines = [f"You answer support questions. Today is {today.isoformat()}.", "Context:"]
            lines += [f"[{c['source']}] {c['text']}" for c in chunks]
            lines += ["", f"Question: {question}"]
            return "\\n".join(lines)


        # --- tests ---
        CHUNKS = [{"source": "faq.md", "text": "Refunds take 5 days."}, {"source": "terms.md", "text": "No refunds after 30 days."}]


        def test_prompt():
            assert build_prompt("Refund?", CHUNKS) == (
                "You answer support questions. Today is 2025-01-15.\\nContext:\\n"
                "[faq.md] Refunds take 5 days.\\n[terms.md] No refunds after 30 days.\\n\\nQuestion: Refund?"
            )
        """,
        tests="""
        import pytest
        from lessontools import run_pytest, swap_impl
        good = run_pytest(__source__)
        assert good["failed"] == 0 and good["passed"] >= 1, good["output"][-800:]
        assert "date(" in __source__.split("# --- tests")[1]
        BASE = __source__.split("# --- code under test (do not edit) ---")[1].split("# --- tests")[0]
        BUGS = {
            "drops_last_chunk": BASE.replace("for c in chunks]", "for c in chunks[:-1]]"),
            "no_sources": BASE.replace('f"[{c[\\'source\\']}] {c[\\'text\\']}"', 'c["text"]'),
            "question_first": BASE.replace('    lines += ["", f"Question: {question}"]\\n', "").replace('lines = [f"You', 'lines = [f"Question: {question}", f"You'),
            "ignores_today": BASE.replace("today = today or date.today()", "today = date.today()"),
        }
        assert all(b != BASE for b in BUGS.values()), [k for k, b in BUGS.items() if b == BASE]
        escaped = sorted(name for name, impl in BUGS.items() if run_pytest(swap_impl(__source__, impl))["failed"] == 0)
        assert escaped == []
        harmless = BASE.replace("You answer support questions.", "You are a helpful support assistant.")
        assert run_pytest(swap_impl(__source__, harmless))["failed"] == 0
        """,
        hints=["`build_prompt(\"Refund?\", CHUNKS, today=date(2025, 1, 15))`; then check `\"Today is 2025-01-15\" in prompt`, each `[source] text` line, and `prompt.endswith(\"Question: Refund?\")`.",
               "The grader also changes the first sentence's wording; your test must still pass then."],
        solution="""
        # --- code under test (do not edit) ---
        from datetime import date


        def build_prompt(question, chunks, today=None):
            today = today or date.today()
            lines = [f"You answer support questions. Today is {today.isoformat()}.", "Context:"]
            lines += [f"[{c['source']}] {c['text']}" for c in chunks]
            lines += ["", f"Question: {question}"]
            return "\\n".join(lines)


        # --- tests ---
        from datetime import date

        CHUNKS = [{"source": "faq.md", "text": "Refunds take 5 days."}, {"source": "terms.md", "text": "No refunds after 30 days."}]


        def test_prompt_structure():
            prompt = build_prompt("Refund?", CHUNKS, today=date(2025, 1, 15))
            lines = prompt.splitlines()
            assert "Today is 2025-01-15" in lines[0]
            assert "[faq.md] Refunds take 5 days." in lines and "[terms.md] No refunds after 30 days." in lines
            assert lines[-1] == "Question: Refund?"
            assert lines.index("[faq.md] Refunds take 5 days.") < lines.index("[terms.md] No refunds after 30 days.")
        """,
        why="""The original test was wrong for two reasons. It depended on the **real date**, so it could only pass on one day; the function already accepts `today`, so the test
        injects a fixed date, the same idea as the fake clock in 13.3. And it compared the entire string, so rewording the instructions, which prompt engineers do
        constantly, would break it although nothing important changed; the grader checks exactly that. Structural assertions pin what the rest of the system
        depends on: the date is present, every chunk appears with its source in order, and the question comes last. When the exact text matters (a regulated
        disclaimer, say), use a deliberate snapshot file instead."""),
    trace("Seeded generators", "medium",
        prompt="Fill in `same` after each marked line.",
        code="""
        import random

        a, b = random.Random(42), random.Random(42)
        same = a.random() == b.random()  # row: "same seed"
        a.random()
        same = a.random() == b.random()  # row: "a is one step ahead"
        b.random()
        same = a.random() == b.random()  # row: "caught up"
        random.seed(42)
        same = random.random() == random.Random(42).random()  # row: "global versus instance"
        c = random.Random(7)
        state = c.getstate()
        first = c.sample(range(100), 3)
        c.setstate(state)
        same = c.sample(range(100), 3) == first  # row: "restored state"
        """,
        trace_vars=["same"],
        hints=["A generator's output depends only on its seed and how many numbers it has produced. The global functions use a hidden instance seeded with `random.seed`."],
        why="""Two generators with the same seed produce the same sequence, so they agree draw for draw while they stay in step; one extra call on `a` puts it one value ahead,
        and an extra call on `b` brings them back in step. The module-level functions use a hidden global `Random` instance, so seeding it with 42 gives the same
        first value as a fresh `Random(42)`, but any library call that uses `random` in between changes it, which is why passing explicit generators is safer.
        `getstate` and `setstate` snapshot and restore a generator, useful for replaying exactly the same samples."""),
    write("Test a tolerant label parser with real replies", "medium", tag="GenAI",
        prompt="""`parse_label(reply, labels)` extracts a classification label from a model reply: it ignores case and surrounding whitespace and punctuation, accepts
        `"Label: spam"` and replies wrapped in quotes or code fences, and returns the label only if **exactly one** known label appears as a word; otherwise `None`.
        Write a parametrized test over at least eight realistic replies (including ambiguous and refusal ones) that passes here and catches four buggy versions.""",
        code="""
        # --- code under test (do not edit) ---
        import re


        def parse_label(reply, labels):
            words = re.findall(r"[a-z]+", reply.lower())
            found = {w for w in words if w in labels}
            return found.pop() if len(found) == 1 else None


        # --- tests ---
        import pytest

        LABELS = {"spam", "ham", "phish"}
        """,
        tests="""
        import pytest
        from lessontools import run_pytest, swap_impl
        good = run_pytest(__source__)
        assert good["failed"] == 0, good["output"][-800:]
        assert len([n for n in good["outcomes"] if "[" in n]) >= 8
        BASE = __source__.split("# --- code under test (do not edit) ---")[1].split("# --- tests")[0]
        BUGS = {
            "case_sensitive": BASE.replace("reply.lower()", "reply"),
            "first_match": BASE.replace("    found = {w for w in words if w in labels}\\n    return found.pop() if len(found) == 1 else None", "    hits = [w for w in words if w in labels]\\n    return hits[0] if hits else None"),
            "substring_match": BASE.replace("    words = re.findall(r\\"[a-z]+\\", reply.lower())\\n    found = {w for w in words if w in labels}", "    found = {l for l in labels if l in reply.lower()}"),
            "exact_only": BASE.replace("    words = re.findall(r\\"[a-z]+\\", reply.lower())\\n    found = {w for w in words if w in labels}", "    found = {reply.strip().lower()} & set(labels)"),
        }
        assert all(b != BASE for b in BUGS.values()), [k for k, b in BUGS.items() if b == BASE]
        escaped = sorted(name for name, impl in BUGS.items() if run_pytest(swap_impl(__source__, impl))["failed"] == 0)
        assert escaped == []
        """,
        hints=["Use replies like `\"Spam\"`, `\"Label: PHISH.\"`, a fenced reply, `\"hammer time\"` (contains `ham` inside a word), `\"spam or ham?\"` and `\"I cannot help with that.\"`.",
               "A table `@pytest.mark.parametrize(\"reply,expected\", [...])` with `None` as the expected value for ambiguous and unusable replies."],
        solution="""
        # --- code under test (do not edit) ---
        import re


        def parse_label(reply, labels):
            words = re.findall(r"[a-z]+", reply.lower())
            found = {w for w in words if w in labels}
            return found.pop() if len(found) == 1 else None


        # --- tests ---
        import pytest

        LABELS = {"spam", "ham", "phish"}
        FENCE = "`" * 3


        @pytest.mark.parametrize("reply,expected", [
            ("spam", "spam"),
            ("  Spam  ", "spam"),
            ("Label: PHISH.", "phish"),
            ('"ham"', "ham"),
            (f"{FENCE}\\nham\\n{FENCE}", "ham"),
            ("This is spam, definitely spam.", "spam"),
            ("spam or ham? Hard to say.", None),
            ("hammer time", None),
            ("I cannot help with that.", None),
            ("", None),
        ])
        def test_parse_label(reply, expected):
            assert parse_label(reply, LABELS) == expected
        """,
        why="""Parsers of model output should be tested with the replies models actually produce, collected from logs: different case, a `Label:` prefix, quotes, code fences,
        repeated labels, hedging between two labels and refusals. A parametrised table makes each reply a separate, readable test, and adding a newly seen failure
        mode is one line. The table pins the important decisions: repeated mentions of one label are fine, **two different** labels are ambiguous and must not be
        resolved by taking the first, and `ham` inside `hammer` is not the label `ham` (the substring mutant fails). Returning `None` lets the caller retry or
        route to a human instead of acting on a guess."""),
    write("An evaluation gate for CI", "medium", tag="GenAI",
        prompt="""Write `evaluate(predict, cases)` returning `{"n": ..., "accuracy": ..., "by_tag": {tag: accuracy}, "failures": [case ids]}` (accuracies rounded to 3,
        tags sorted), where each case has `id`, `input`, `expected` and `tags`, and a prediction that raises counts as wrong. Then write `gate(report, baseline,
        min_accuracy=0.8, max_drop=0.02)` that raises `AssertionError` listing every problem: overall accuracy below the minimum, overall accuracy more than
        `max_drop` below the baseline's, and any tag more than `max_drop` below its baseline value. Return `True` when the gate passes.""",
        code="""
        def evaluate(predict, cases):
            pass

        def gate(report, baseline, min_accuracy=0.8, max_drop=0.02):
            pass
        """,
        tests="""
        cases = [
            {"id": "c1", "input": "WIN A PRIZE", "expected": "spam", "tags": ["spam"]},
            {"id": "c2", "input": "lunch at 1?", "expected": "ham", "tags": ["ham"]},
            {"id": "c3", "input": "verify your bank login", "expected": "phish", "tags": ["phish", "security"]},
            {"id": "c4", "input": "free gift card", "expected": "spam", "tags": ["spam"]},
            {"id": "c5", "input": "reset your password here", "expected": "phish", "tags": ["phish", "security"]},
        ]
        def model(text):
            if "password" in text:
                raise TimeoutError("model timed out")
            if "bank" in text:
                return "phish"
            return "spam" if any(w in text.lower() for w in ("win", "free")) else "ham"
        report = evaluate(model, cases)
        assert report == {"n": 5, "accuracy": 0.8, "by_tag": {"ham": 1.0, "phish": 0.5, "security": 0.5, "spam": 1.0}, "failures": ["c5"]}
        assert list(report["by_tag"]) == ["ham", "phish", "security", "spam"]
        assert gate(report, {"accuracy": 0.79, "by_tag": {"phish": 0.5}}) is True
        try:
            gate(report, {"accuracy": 0.9, "by_tag": {"phish": 1.0, "spam": 1.0}}, min_accuracy=0.85)
            assert False
        except AssertionError as e:
            msg = str(e)
            assert "accuracy 0.8 below minimum 0.85" in msg and "dropped from 0.9" in msg and "phish" in msg and "spam" not in msg
        assert evaluate(model, [])["accuracy"] == 0.0
        """,
        hints=["Collect per-tag lists of `True`/`False`, then compute the accuracy of each; an empty case list gives accuracy 0.0.",
               "Build a list of problem strings in `gate` and raise once with `\"; \".join(problems)`; compare tags only when they exist in the baseline."],
        solution="""
        def evaluate(predict, cases):
            results, by_tag, failures = [], {}, []
            for case in cases:
                try:
                    ok = predict(case["input"]) == case["expected"]
                except Exception:
                    ok = False
                results.append(ok)
                if not ok:
                    failures.append(case["id"])
                for tag in case.get("tags", []):
                    by_tag.setdefault(tag, []).append(ok)
            accuracy = round(sum(results) / len(results), 3) if results else 0.0
            return {"n": len(results), "accuracy": accuracy,
                    "by_tag": {tag: round(sum(v) / len(v), 3) for tag, v in sorted(by_tag.items())},
                    "failures": failures}


        def gate(report, baseline, min_accuracy=0.8, max_drop=0.02):
            problems = []
            acc = report["accuracy"]
            if acc < min_accuracy:
                problems.append(f"accuracy {acc} below minimum {min_accuracy}")
            if acc < baseline.get("accuracy", 0.0) - max_drop:
                problems.append(f"accuracy dropped from {baseline['accuracy']} to {acc}")
            for tag, old in baseline.get("by_tag", {}).items():
                new = report["by_tag"].get(tag)
                if new is not None and new < old - max_drop:
                    problems.append(f"tag {tag!r} dropped from {old} to {new}")
            if problems:
                raise AssertionError("; ".join(problems))
            return True
        """,
        why="""An evaluation gate turns "the model seems fine" into a check CI can enforce when someone edits a prompt or switches models. Two thresholds work together: an
        absolute minimum protects users, and a maximum **drop from the baseline** catches regressions even when the absolute number is still acceptable. Per-tag
        accuracy matters because an average can hide a collapse in one important slice: here the overall accuracy is fine but phishing, the costliest class,
        fell from 1.0 to 0.5. Exceptions count as wrong answers, since a timeout in production is a failure too, and all problems are reported at once. In practice
        the tolerance should reflect the evaluation set's noise (with 50 cases, one case is 2 points), and the baseline is stored with the prompt and model version."""),
)

section("hard", "Hard",
    write("Smoke tests for a training loop", "hard", tag="ML",
        prompt="""`train_logreg(X, y, lr=0.5, epochs=200, seed=0)` trains logistic regression with gradient descent and returns `(w, b, losses)`; `predict_proba(X, w, b)`
        returns probabilities. Write at least five smoke tests on tiny data that run in milliseconds: the loss decreases, a separable dataset is classified
        perfectly, probabilities are in `[0, 1]` with the right shape, the same seed gives identical weights, and a bias is learned when the data needs one. They
        must pass here and catch five buggy versions.""",
        code="""
        # --- code under test (do not edit) ---
        import numpy as np


        def sigmoid(z):
            return 1 / (1 + np.exp(-z))


        def predict_proba(X, w, b):
            return sigmoid(np.asarray(X, dtype=float) @ w + b)


        def train_logreg(X, y, lr=0.5, epochs=200, seed=0):
            X, y = np.asarray(X, dtype=float), np.asarray(y, dtype=float)
            rng = np.random.default_rng(seed)
            w, b = rng.normal(0, 0.01, X.shape[1]), 0.0
            losses = []
            for _ in range(epochs):
                p = predict_proba(X, w, b)
                losses.append(float(-np.mean(y * np.log(p + 1e-12) + (1 - y) * np.log(1 - p + 1e-12))))
                grad = p - y
                w -= lr * X.T @ grad / len(y)
                b -= lr * grad.mean()
            return w, b, losses


        # --- tests ---
        import numpy as np
        import pytest
        """,
        tests="""
        import numpy, pytest
        from lessontools import run_pytest, swap_impl
        good = run_pytest(__source__)
        assert good["failed"] == 0 and good["passed"] >= 5, good["output"][-800:]
        BASE = __source__.split("# --- code under test (do not edit) ---")[1].split("# --- tests")[0]
        BUGS = {
            "gradient_ascent": BASE.replace("w -= lr * X.T @ grad / len(y)", "w += lr * X.T @ grad / len(y)").replace("b -= lr * grad.mean()", "b += lr * grad.mean()"),
            "no_bias_update": BASE.replace("        b -= lr * grad.mean()\\n", ""),
            "seed_ignored": BASE.replace("rng = np.random.default_rng(seed)", "rng = np.random.default_rng()"),
            "logits_not_probs": BASE.replace("    return sigmoid(np.asarray(X, dtype=float) @ w + b)", "    return np.asarray(X, dtype=float) @ w + b").replace("p = predict_proba(X, w, b)", "p = sigmoid(predict_proba(X, w, b))"),
            "wrong_axis": BASE.replace("w -= lr * X.T @ grad / len(y)", "w -= lr * (X.T @ grad / len(y)).mean()"),
        }
        assert all(b != BASE for b in BUGS.values()), [k for k, b in BUGS.items() if b == BASE]
        escaped = sorted(name for name, impl in BUGS.items() if run_pytest(swap_impl(__source__, impl))["failed"] == 0)
        assert escaped == []
        """,
        hints=["Data: `X = [[0, 0], [0, 1], [1, 0], [1, 1]]` with `y = [0, 0, 0, 1]` (logical AND) is separable but needs a negative bias.",
               "Use a second dataset where the two features matter differently (for example `y` depends only on the first feature) to catch a version that applies one average gradient to every weight.",
               "Probabilities: `predict_proba` on any points must lie in `[0, 1]`; seeds: train twice with `seed=3` and compare with `assert_array_equal`."],
        solution="""
        # --- code under test (do not edit) ---
        import numpy as np


        def sigmoid(z):
            return 1 / (1 + np.exp(-z))


        def predict_proba(X, w, b):
            return sigmoid(np.asarray(X, dtype=float) @ w + b)


        def train_logreg(X, y, lr=0.5, epochs=200, seed=0):
            X, y = np.asarray(X, dtype=float), np.asarray(y, dtype=float)
            rng = np.random.default_rng(seed)
            w, b = rng.normal(0, 0.01, X.shape[1]), 0.0
            losses = []
            for _ in range(epochs):
                p = predict_proba(X, w, b)
                losses.append(float(-np.mean(y * np.log(p + 1e-12) + (1 - y) * np.log(1 - p + 1e-12))))
                grad = p - y
                w -= lr * X.T @ grad / len(y)
                b -= lr * grad.mean()
            return w, b, losses


        # --- tests ---
        import numpy as np
        import pytest

        X_AND = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
        Y_AND = np.array([0, 0, 0, 1])


        @pytest.fixture
        def trained():
            return train_logreg(X_AND, Y_AND, lr=1.0, epochs=2000, seed=0)


        def test_loss_decreases(trained):
            _, _, losses = trained
            assert losses[-1] < losses[0] / 5
            assert all(b <= a + 1e-12 for a, b in zip(losses, losses[1:]))


        def test_separable_data_classified_perfectly(trained):
            w, b, _ = trained
            preds = (predict_proba(X_AND, w, b) > 0.5).astype(int)
            np.testing.assert_array_equal(preds, Y_AND)


        def test_bias_is_learned_when_needed(trained):
            _, b, _ = trained
            assert b < -1.0


        def test_probabilities_in_unit_interval(trained):
            w, b, _ = trained
            p = predict_proba(np.array([[5, 5], [-5, -5], [0.5, 0.5]]), w, b)
            assert p.shape == (3,) and np.all((p >= 0) & (p <= 1))


        def test_same_seed_same_weights():
            w1, b1, _ = train_logreg(X_AND, Y_AND, epochs=20, seed=3)
            w2, b2, _ = train_logreg(X_AND, Y_AND, epochs=20, seed=3)
            np.testing.assert_array_equal(w1, w2)
            assert b1 == b2


        def test_weights_learn_which_feature_matters():
            X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
            y = np.array([0, 0, 1, 1])
            w, b, _ = train_logreg(X, y, lr=1.0, epochs=1000)
            assert w[0] > 2 and abs(w[1]) < 0.5
        """,
        why="""Smoke tests cannot prove a model is good, but they catch the bugs that make training meaningless, in milliseconds instead of a GPU-hour. A decreasing loss
        catches a flipped gradient sign; perfect accuracy on a tiny separable problem (AND) catches broken updates; AND needs a negative bias, so a model without
        bias updates cannot fit it; a probability check on extreme inputs catches outputs that are logits; two runs with one seed catch ignored seeds; and a dataset
        where only the first feature matters catches a gradient averaged across features. Each test encodes a fact about logistic regression, not a magic number,
        which keeps them valid when hyperparameters change. The same ideas, overfitting a single batch first, are standard practice before long deep-learning
        runs."""),
    write("Metamorphic tests for a classifier", "hard", tag="GenAI",
        prompt="""Write `check_invariance(classify, texts, transforms)` for metamorphic testing. `transforms` maps a name to a function that rewrites a text in a way that
        should **not** change its label (upper-casing, extra whitespace, a polite prefix). For each text, compute the original label and each transformed label;
        return a list of violations `(text, transform_name, original_label, new_label)` in input order, then transform order. A transform or classifier that raises
        counts as a violation with the label `"error: ExceptionName"`. Also write `invariance_rate(violations, texts, transforms)` returning the share of
        (text, transform) pairs without a violation, rounded to 3.""",
        code="""
        def check_invariance(classify, texts, transforms):
            pass

        def invariance_rate(violations, texts, transforms):
            pass
        """,
        tests="""
        def classify(text):
            t = text.lower()
            if "prize" in t or "free" in t:
                return "spam"
            if t.startswith("hi") and "please" in t:
                return "spam"
            return "ham"

        def shout(t):
            return t.upper()

        def spaces(t):
            return "  " + "   ".join(t.split()) + "  "

        def polite(t):
            return "Hi team, please read: " + t

        def broken(t):
            raise UnicodeError("bad transform")

        texts = ["Win a free prize now", "Lunch at noon?", "Quarterly report attached"]
        transforms = {"upper": shout, "spaces": spaces, "polite": polite}
        v = check_invariance(classify, texts, transforms)
        assert v == [("Lunch at noon?", "polite", "ham", "spam"), ("Quarterly report attached", "polite", "ham", "spam")]
        assert invariance_rate(v, texts, transforms) == round(7 / 9, 3)
        v2 = check_invariance(classify, texts[:1], {"broken": broken})
        assert v2 == [("Win a free prize now", "broken", "spam", "error: UnicodeError")]
        assert check_invariance(classify, [], transforms) == [] and invariance_rate([], [], transforms) == 1.0
        """,
        hints=["Wrap the transformed classification in a helper that returns either the label or `f\"error: {type(e).__name__}\"`.",
               "The number of pairs is `len(texts) * len(transforms)`; with no pairs, the rate is 1.0."],
        solution="""
        def _label(classify, text, transform=None):
            try:
                return classify(transform(text) if transform else text)
            except Exception as e:
                return f"error: {type(e).__name__}"


        def check_invariance(classify, texts, transforms):
            violations = []
            for text in texts:
                original = _label(classify, text)
                for name, transform in transforms.items():
                    new = _label(classify, text, transform)
                    if new != original:
                        violations.append((text, name, original, new))
            return violations


        def invariance_rate(violations, texts, transforms):
            pairs = len(texts) * len(transforms)
            if pairs == 0:
                return 1.0
            return round(1 - len(violations) / pairs, 3)
        """,
        why="""For a model there is often no "expected output" to compare with, but there are **relations** between outputs that must hold: shouting or extra spaces should not
        turn ham into spam, and a polite greeting certainly should not. Metamorphic testing checks those relations on many inputs without labelling anything, and
        here it found a real weakness: the toy classifier treats "Hi ... please" as spam, so a harmless prefix flips two answers. Reporting violations with the
        text and transform makes them actionable, and the invariance rate is a metric you can track over model versions, alongside accuracy, in the evaluation
        gate. Checklists of such behavioural tests (invariance, directional changes, minimum functionality) are a standard way to probe NLP and LLM systems."""),
    fix("Read the code: weak tests for a feature extractor", "hard", tag="ML",
        prompt="""`featurize(texts)` turns texts into a float matrix with columns `[length, digit_count, upper_ratio]`. Its tests generate random strings without a seed, check
        only the shape, and compare a ratio with `==`. All four graded buggy versions pass them. Rewrite the tests with fixed, hand-checked examples, `assert_allclose`,
        explicit dtype and shape checks, and the empty-text edge case.""",
        code="""
        # --- code under test (do not edit) ---
        import numpy as np


        def featurize(texts):
            rows = []
            for t in texts:
                letters = [c for c in t if c.isalpha()]
                upper = sum(c.isupper() for c in letters) / len(letters) if letters else 0.0
                rows.append([len(t), sum(c.isdigit() for c in t), upper])
            return np.array(rows, dtype=np.float64).reshape(len(texts), 3)


        # --- tests ---
        import random, string
        import numpy as np


        def test_shape():
            texts = ["".join(random.choices(string.ascii_letters, k=10)) for _ in range(5)]
            assert featurize(texts).shape == (5, 3)


        def test_ratio():
            assert featurize(["AB"])[0][2] == 1.0
        """,
        tests="""
        import numpy, pytest
        from lessontools import run_pytest, swap_impl
        good = run_pytest(__source__)
        assert good["failed"] == 0 and good["passed"] >= 4, good["output"][-800:]
        tests_part = __source__.split("# --- tests")[1]
        assert "random.choices" not in tests_part and "assert_allclose" in tests_part
        BASE = __source__.split("# --- code under test (do not edit) ---")[1].split("# --- tests")[0]
        BUGS = {
            "ratio_over_all_chars": BASE.replace("/ len(letters) if letters else 0.0", "/ len(t) if t else 0.0"),
            "digits_as_letters": BASE.replace("letters = [c for c in t if c.isalpha()]", "letters = [c for c in t if c.isalnum()]"),
            "int_dtype": BASE.replace("dtype=np.float64", "dtype=np.int64"),
            "empty_crash": BASE.replace("/ len(letters) if letters else 0.0", "/ len(letters)"),
        }
        assert all(b != BASE for b in BUGS.values()), [k for k, b in BUGS.items() if b == BASE]
        escaped = sorted(name for name, impl in BUGS.items() if run_pytest(swap_impl(__source__, impl))["failed"] == 0)
        assert escaped == []
        """,
        hints=["Hand-check a mixed example: `\"Win 100 GBP\"` has length 11, 3 digits, and 4 of its 6 letters upper case.",
               "Also test `\"\"` (all zeros, no error), a text with no letters (`\"2025\"`), and `out.dtype == np.float64` with `out.shape == (n, 3)`."],
        solution="""
        # --- code under test (do not edit) ---
        import numpy as np


        def featurize(texts):
            rows = []
            for t in texts:
                letters = [c for c in t if c.isalpha()]
                upper = sum(c.isupper() for c in letters) / len(letters) if letters else 0.0
                rows.append([len(t), sum(c.isdigit() for c in t), upper])
            return np.array(rows, dtype=np.float64).reshape(len(texts), 3)


        # --- tests ---
        import numpy as np


        def test_mixed_text_by_hand():
            out = featurize(["Win 100 GBP"])
            np.testing.assert_allclose(out, [[11.0, 3.0, 4 / 6]])


        def test_dtype_and_shape():
            out = featurize(["a", "BB", "c3"])
            assert out.dtype == np.float64 and out.shape == (3, 3)


        def test_ratio_ignores_digits_and_spaces():
            np.testing.assert_allclose(featurize(["AB 12 cd"])[0], [8.0, 2.0, 0.5])


        def test_empty_and_letterless_texts():
            np.testing.assert_allclose(featurize(["", "2025"]), [[0.0, 0.0, 0.0], [4.0, 4.0, 0.0]])


        def test_no_texts():
            assert featurize([]).shape == (0, 3)
        """,
        why="""Random inputs without a seed make failures unreproducible, and "the shape is right" is true of almost any broken implementation. Feature code needs a few
        **hand-checked** examples chosen to exercise each rule: a text mixing upper and lower case letters, digits and spaces shows whether the ratio is over
        letters only and whether digits are counted separately; an empty and a digits-only text cover the division by zero; and an explicit dtype check catches
        integer truncation, which would silently turn every ratio into 0. `assert_allclose` compares whole rows with a tolerance, so `4 / 6` needs no hand-rounded
        literal. If random inputs are useful, seed them and check properties (for example, `0 <= upper_ratio <= 1`)."""),
    predict("NumPy generators and reproducibility", "hard",
        code="""
        import numpy as np

        np.random.seed(0)
        legacy = np.random.rand(2)
        np.random.seed(0)
        print(np.array_equal(legacy, np.random.rand(2)))
        g = np.random.default_rng(0)
        print(np.array_equal(g.random(2), np.random.default_rng(0).random(2)), np.array_equal(legacy, np.random.default_rng(0).random(2)))
        parent = np.random.SeedSequence(42)
        a, b = [np.random.default_rng(s) for s in parent.spawn(2)]
        print(np.array_equal(a.random(3), b.random(3)))
        a2, b2 = [np.random.default_rng(s) for s in np.random.SeedSequence(42).spawn(2)]
        print(np.array_equal(np.random.default_rng(np.random.SeedSequence(42).spawn(2)[0]).random(3), a2.random(3)))
        perm1 = np.random.default_rng(5).permutation(6)
        perm2 = np.random.default_rng(5).permutation(6)
        print(np.array_equal(perm1, perm2), sorted(perm1.tolist()) == list(range(6)))
        """,
        hints=["The legacy global `np.random.seed` and the new `default_rng` use different algorithms. `SeedSequence.spawn` creates independent child seeds, deterministically."],
        why="""Re-seeding the legacy global generator reproduces its numbers, and two `default_rng(0)` generators agree with each other, but the legacy and new APIs use
        different algorithms, so the same seed gives different numbers across them (a surprise when migrating code). `SeedSequence.spawn` derives independent
        streams for parallel workers, so the two children produce different numbers, yet spawning again from the same parent seed reproduces the same children,
        which is how you make parallel experiments both independent and repeatable. A seeded permutation is reproducible and is always a permutation of the
        input."""),
)

section("interview", "Interview questions",
    explain("How do you test a machine learning pipeline?", "medium", tag="Interview",
        why="""In layers. **Unit tests** for deterministic code: data loading and cleaning, feature functions, preprocessing (fit on train, transform with stored statistics),
        metrics, and serialisation, with hand-computed examples and tolerances. **Data validation** on every batch: schema, types, ranges, missing values, label
        sets, duplicates and leakage between splits, failing the pipeline before training on bad data. **Smoke tests** of training: a tiny model overfits a tiny
        batch, the loss decreases, outputs have the right shapes and ranges, and seeds make runs reproducible. **Integration tests** run the pipeline end to end on
        a small fixture dataset and check artefacts (model file, metrics report) are produced. **Model evaluation** on a held-out, versioned dataset with metrics and
        slices, compared with the current production model before promotion, plus behavioural checks (invariance, fairness slices). In production, **monitoring**
        of input drift and prediction distributions closes the loop. Keep randomness injected and seeded so failures are reproducible."""),
    explain("A teammate changed a prompt. How do you decide whether it is safe to ship?", "medium", tag="Interview",
        why="""Run it through the same gates as code. Unit tests first: prompt building and output parsing must still pass, and structural tests should not depend on exact
        wording. Then the **evaluation set**: a versioned collection of representative inputs, including past failures and edge cases, scored with appropriate
        metrics (exact or semantic match, required facts present, valid structured output, a rubric graded by a judge model whose agreement with humans has been
        checked). Compare with the **baseline** of the current prompt on the same model version, overall and per slice, with enough cases and repeated runs to tell a
        real change from noise; block on regressions beyond a tolerance. Check cost and latency (longer prompts cost more) and safety cases (prompt injection, refusals).
        If it passes, roll out gradually or behind a flag, and watch production metrics (user feedback, escalations, parse failures) with the ability to roll back,
        since evaluation sets never cover everything."""),
    explain("Model outputs are non-deterministic. How do you keep your tests from being flaky?", "hard", tag="Interview",
        why="""First, keep the model out of unit tests: inject a fake or mock client so everything around the model (prompt building, parsing, retries, tool dispatch) is tested
        deterministically. Where randomness is yours, control it: pass seeded generators, set framework seeds, and use deterministic algorithms when available.
        Compare numbers with tolerances that reflect the dtype and computation (`assert_allclose` with sensible `rtol`/`atol`), and test properties and relations
        rather than exact values: shapes, ranges, probabilities summing to 1, monotonic loss on a tiny problem, invariance under harmless input changes. For real model
        calls, which belong in evaluation or a few marked integration tests, use temperature 0 where possible, assert on robust properties (valid JSON matching a
        schema, contains the required fact), aggregate over several cases or samples with thresholds instead of single pass/fail outputs, and record and replay
        responses for regression tests. Track flaky tests explicitly and fix their cause rather than adding retries."""),
)

recap(
    "Unit-test the deterministic code around models (features, preprocessing, metrics, prompts, parsers); evaluate model quality separately with datasets and thresholds.",
    "Compare floats with `np.testing.assert_allclose` and deliberate `rtol`/`atol`; check dtypes and shapes explicitly.",
    "Inject seeded generators (`default_rng(seed)`, `random.Random(seed)`); test determinism with two fresh generators, and properties for everything else.",
    "Validate data with functions that collect every problem; smoke-test training on tiny data (loss decreases, perfect fit, bias learned, seeds respected).",
    "Test LLM parsers with real replies, prompts by structure, behaviour with metamorphic checks, and gate changes on evaluation against a baseline.",
)
