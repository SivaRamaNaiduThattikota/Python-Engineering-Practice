from lesson import *
from diagrams import *

lesson(
    id="m17-1", num="D.1", title="NumPy for ML: arrays, broadcasting and vectorisation",
    intro="Every ML library sits on NumPy arrays: feature matrices, embeddings, predictions and metrics are all arrays. What an array is and why it is "
          "fast, dtypes and shapes, views versus copies, broadcasting, reductions along an axis, and the vectorised patterns behind softmax, "
          "cosine search, distances and pooling.",
    desc="Arrays, dtypes, views and copies, broadcasting, axis reductions, and vectorised ML building blocks.",
    keys="numpy ndarray array dtype shape ndim reshape view copy shares_memory slicing boolean mask fancy indexing broadcasting keepdims axis reduction sum mean argmax argsort argpartition where ufunc vectorisation softmax log-sum-exp cosine similarity embeddings normalise top-k euclidean distance one-hot bincount mean pooling attention mask default_rng float32 overflow",
)

term("ndarray", "NumPy's array: a block of memory holding values of one dtype, plus a shape that says how to read it as rows, columns and more dimensions.")
term("dtype", "The type of every element in a NumPy array, such as int64, float32 or bool; it fixes the size of each element and how arithmetic behaves.")
term("View", "An array that shares another array's memory, such as a basic slice or a reshape; writing to it changes the original.")
term("Broadcasting", "NumPy's rule for combining arrays of different shapes: dimensions are matched from the right, and a dimension of size 1 is stretched to fit.")
term("Vectorisation", "Writing a computation as whole-array operations, so the loop runs in compiled code instead of the Python interpreter.")

section("arrays", "What an array is, and why it is fast",
    fig(stage_map(17, "a complaint classifier, end to end"), "Module D at a glance: NumPy, pandas, matplotlib and scikit-learn, the four libraries under almost every ML project, building up to one small end-to-end classifier."),
    p("""A Python list of numbers is a list of **pointers**: each element is a separate Python object somewhere in memory, with its own type and reference count,
    so `sum(xs)` follows a pointer and checks a type for every element. A NumPy **array** stores the raw numbers next to each other in one block of memory, all
    of the same **dtype** (`float64`, `int32`, `bool`...), plus a **shape** such as `(1000, 768)`: a thousand rows of 768 numbers, the usual layout for a batch
    of embeddings. Because the layout is known, an operation like `a * 2` runs one tight loop in compiled C over the block, with no per-element Python work.
    That is the whole reason NumPy, pandas, scikit-learn and PyTorch exist in their current form."""),
    p("""Think of it like the difference between a SQL table with a declared column type and a column of `sql_variant`: once every value has the same type and
    width, the engine can scan it at full speed. The price is the same as in SQL: one dtype per array. Mixing ints and floats gives floats, mixing numbers
    and strings gives an array of strings, and fixed-size integers **wrap around** silently on overflow instead of growing like Python ints."""),
    fig(table(["", "Python list", "NumPy array"], [
        ["stores", "pointers to separate objects", "raw values in one block"],
        ["element types", "anything, mixed", "one dtype for all"],
        ["x * 2", "repeats the list", "multiplies every element"],
        ["loop runs in", "the interpreter", "compiled C"],
        ["integer overflow", "never (ints grow)", "wraps around silently"],
    ], hl={(2, 2), (4, 2)}, label="list versus ndarray"),
        "An array trades flexibility for speed: one dtype, one block of memory, loops in compiled code."),
    ex("""
    import numpy as np

    xs = [1, 2, 3]
    a = np.array(xs)
    print(xs * 2, a * 2)
    print(a.dtype, a.shape, a.ndim)
    print(np.array([1, 2.5]).dtype, np.array([1, "a"]).dtype)
    m = np.zeros((2, 3))
    print(m.shape, m.dtype, m.size)
    print(np.arange(0, 1, 0.25), np.linspace(0, 1, 5))
    small = np.array([120, 7], dtype=np.int8)
    print(small + 10, small.dtype)
    print(np.float32(0.1) == np.float64(0.1), float(np.float32(0.1)), np.float32(0.1).nbytes, np.float64(0.1).nbytes)
    print(np.float32(0.1) == 0.1)
    """, "arrays.py"),
    p("""Three details from that output matter in ML work. `120 + 10` in `int8` became `-126`: the value wrapped, with no error, which is how pixel or token-id
    arithmetic in small dtypes goes wrong. `float32` stores 4 bytes per value instead of 8, half the memory for an embedding matrix, but only about 7
    significant digits: `float32(0.1)` is really 0.10000000149..., so it differs from the `float64` 0.1. The last line looks like a contradiction but is a NumPy 2
    rule: a plain Python float compared with a `float32` is first converted **to** `float32`, so both sides round the same way. Compare arrays with a
    tolerance (13.4), never with `==`. Finally, the default integer dtype printed `int32` because this site runs a 32-bit Python in the browser; on 64-bit
    Linux, macOS and (since NumPy 2) Windows it is `int64`. Write `dtype=np.int64` when the size matters, for example for row ids or token counts that can
    pass 2 billion."""),
    p("""`arange` with a float step is fine for display but can gain or lose a final element through rounding; `linspace(start, stop, n)` is the safe way to
    get `n` evenly spaced points."""),
)

section("indexing", "Indexing: views, copies and masks",
    p("""**Basic indexing** (integers and slices, `a[1:3]`, `m[:, 0]`) returns a **view**: a new array object that points into the same memory. Writing to the
    view writes to the original. `reshape` and `.T` are views too, whenever the memory layout allows it. **Advanced indexing**, with a boolean **mask**
    (`a[a > 0]`) or an integer list (`a[[0, 2]]`), returns a **copy**, because the selected elements are not evenly spaced in memory. `np.shares_memory(x, y)`
    tells you which case you are in, and `.copy()` makes an independent array when you need one."""),
    fig(refs(["a", "v = a[1:3]", "c = a[[1, 2]]"], ["buffer [0, 1, 2, 3]", ("new buffer [1, 2]", "accent")], [(0, 0), (1, 0), (2, 1)],
        label="a slice is a window, fancy indexing is a copy", title_names="names", title_objects="memory"),
        "`v` is a window onto `a`'s memory, so `v[0] = 99` changes `a`; `c` owns new memory, so changing it leaves `a` alone."),
    ex("""
    import numpy as np

    a = np.arange(4)
    v = a[1:3]
    c = a[[1, 2]]
    v[0] = 99
    c[1] = -1
    print(a, v, c)
    print(np.shares_memory(a, v), np.shares_memory(a, c))
    m = np.arange(6).reshape(2, 3)
    print(m)
    print(m[:, 1], m[1], m[m % 2 == 0])
    m[m > 3] = 0
    print(m)
    print(np.shares_memory(m, m.T), np.shares_memory(m, m.reshape(3, 2)))
    """, "views.py"),
    p("""Masks are NumPy's `WHERE` clause: `scores[labels == 1]` keeps the scores of positive examples, and `x[x > 3] = 0` updates in place, like an `UPDATE ...
    WHERE`. Combine conditions with `&`, `|` and `~` (not `and`/`or`/`not`, which try to turn the whole array into one bool and raise), and put each comparison
    in parentheses because `&` binds tighter than `>`. A function that receives an array and slices it **can modify the caller's data** through the view, which
    is the NumPy version of the shared-list bugs in Module 2; copy before modifying, or document that the function works in place."""),
)

section("broadcasting", "Broadcasting",
    p("""Broadcasting is how NumPy combines arrays of different shapes without copying. Line the shapes up **from the right**; two dimensions are compatible if they
    are equal or one of them is **1**, and a size-1 dimension is stretched to match. Missing dimensions on the left count as 1. So a `(1000, 768)` embedding
    matrix minus a `(768,)` mean vector subtracts the mean from every row, and a `(3, 1)` column plus a `(1, 4)` row gives a `(3, 4)` grid: every pair, which is
    the trick behind pairwise distances. If no rule applies, NumPy raises `ValueError: operands could not be broadcast together`."""),
    fig(table(["left shape", "right shape", "result", "what happened"], [
        ["(1000, 768)", "(768,)", "(1000, 768)", "the vector is used for every row"],
        ["(1000, 768)", "(1000, 1)", "(1000, 768)", "one value per row, stretched across"],
        ["(3, 1)", "(1, 4)", "(3, 4)", "every pair: an outer operation"],
        ["(5,)", "(5, 1)", "(5, 5)", "often a bug: you wanted (5,)"],
        ["(1000, 768)", "(1000,)", "error", "trailing 768 vs 1000"],
    ], hl={(3, 2), (4, 2)}, label="broadcasting, matched from the right"),
        "Shapes are compared from the right; a 1 stretches. The fourth row is the classic silent bug."),
    ex("""
    import numpy as np

    X = np.array([[1.0, 10.0], [3.0, 30.0], [5.0, 50.0]])
    mu = X.mean(axis=0)
    print(mu.shape, X - mu)
    row_norm = np.linalg.norm(X, axis=1, keepdims=True)
    print(row_norm.shape, (X / row_norm).round(3))
    y = np.array([1.0, 2.0, 3.0])
    pred = np.array([[1.5], [2.0], [2.0]])
    print((y - pred).shape, ((y - pred) ** 2).mean(), ((y - pred.ravel()) ** 2).mean())
    try:
        X - np.ones(3)
    except ValueError as e:
        print(e)
    """, "broadcast.py"),
    p("""The middle lines show the trap that costs ML engineers whole afternoons: `y` has shape `(3,)` and `pred` has shape `(3, 1)` (a column, as many models return),
    so `y - pred` broadcasts to `(3, 3)`, every target minus every prediction, and the "mean squared error" is a wrong number with no error raised. Flatten with
    `.ravel()` or `reshape(-1)`, or assert shapes before computing a metric. `keepdims=True` is the opposite habit: it keeps a reduced axis as size 1, so the
    result `(3, 1)` broadcasts back over the rows it came from."""),
)

section("axis", "Reductions along an axis",
    p("""`sum`, `mean`, `std`, `max`, `argmax` and friends take an **`axis`**: the dimension that is **collapsed**. For a `(rows, columns)` matrix, `axis=0` collapses
    the rows and gives one value per column (like `SELECT AVG(col1), AVG(col2) FROM t`), and `axis=1` collapses the columns, one value per row (like a
    calculated column in Power BI that averages across a row). With no axis, the whole array becomes one number. `argmax(axis=1)` on a `(batch, classes)`
    matrix of scores is how a classifier's predicted class is read off; `argsort` sorts indices; `argpartition(-scores, k)[:k]` finds the top `k` without
    sorting everything, which matters when searching a million embeddings."""),
    ex("""
    import numpy as np

    scores = np.array([[0.1, 0.7, 0.2],
                       [0.5, 0.3, 0.2],
                       [0.2, 0.2, 0.6]])
    print(scores.sum(axis=1), scores.mean(axis=0).round(3))
    print(scores.argmax(axis=1), scores.max(axis=1))
    sims = np.array([0.12, 0.91, 0.45, 0.88, 0.05, 0.67])
    top = np.argpartition(-sims, 3)[:3]
    print(sorted(top.tolist()), top[np.argsort(-sims[top])])
    v = np.array([1.0, np.nan, 3.0])
    print(v.mean(), np.nanmean(v), np.isnan(v).sum())
    """, "axis.py"),
    p("""Two details. `argpartition` only guarantees that the first `k` positions hold the `k` largest (in any order), so sort those `k` afterwards if order matters:
    `O(n + k log k)` instead of `O(n log n)`. And a single `NaN` poisons `mean`, `sum` and `max`; the `nan*` functions skip them, but in a pipeline it is usually
    better to find out **why** there is a NaN (a division by zero, a missing feature) than to skip it silently."""),
)

section("vectorise", "Vectorised building blocks for ML",
    p("""**Vectorising** means expressing a computation as whole-array operations so the loop runs in C. Element-wise math (`np.exp`, `np.log`, `np.sqrt`, `+`, `*`)
    is done by **ufuncs**; `np.where(cond, a, b)` is a vectorised if/else (Power BI's `IF` on a whole column); matrix products use `@`. Most ML formulas are
    written this way, and three of them appear in every GenAI codebase."""),
    p("""**Softmax** turns scores into probabilities: `exp(z) / sum(exp(z))`. Computed literally, `exp(1000)` overflows to `inf` and the result is `nan`, so real code
    subtracts the row maximum first, which changes nothing mathematically and keeps every exponent at or below 0. **Cosine similarity** between embeddings
    is the dot product of unit vectors: normalise each row once (`E / norm(E, axis=1, keepdims=True)`), then one matrix product `Q @ E.T` gives every
    query-document similarity. **Masked mean pooling** averages token embeddings `(batch, tokens, dim)` while ignoring padding: multiply by the mask with an
    added axis, sum over tokens, divide by the number of real tokens."""),
    fig(chain(["scores z", ("z - z.max()", "accent"), "np.exp", "divide by|the row sum", ("probabilities|summing to 1", "good")], note="subtracting the max keeps every exp() at or below 1"),
        "Stable softmax: the same result as the textbook formula, without overflow."),
    ex("""
    import numpy as np

    def softmax(z, axis=-1):
        z = z - z.max(axis=axis, keepdims=True)
        e = np.exp(z)
        return e / e.sum(axis=axis, keepdims=True)

    z = np.array([[1000.0, 1001.0, 1002.0], [1.0, 2.0, 3.0]])
    with np.errstate(over="ignore", invalid="ignore"):
        naive = np.exp(z) / np.exp(z).sum(axis=1, keepdims=True)
    print(naive.round(4))
    print(softmax(z).round(4), softmax(z).sum(axis=1))

    E = np.array([[3.0, 4.0], [1.0, 0.0], [0.0, 2.0]])
    E_unit = E / np.linalg.norm(E, axis=1, keepdims=True)
    q = np.array([[0.6, 0.8]])
    print((q @ E_unit.T).round(3))

    tokens = np.array([[[1.0, 1.0], [3.0, 5.0], [9.0, 9.0]]])
    mask = np.array([[1, 1, 0]])
    pooled = (tokens * mask[..., None]).sum(axis=1) / mask.sum(axis=1, keepdims=True)
    print(pooled)
    print(np.where(np.array([0.2, 0.7, 0.5]) >= 0.5, "spam", "ham"))
    rng = np.random.default_rng(0)
    print(rng.integers(0, 10, 5), rng.normal(size=2).round(3))
    """, "vectorised.py"),
    p("""For random numbers, use a **`Generator`** from `np.random.default_rng(seed)` and pass it around, as 13.4 did: it is reproducible, independent of other code,
    and the modern API (`integers`, `normal`, `choice`, `permutation`). The old global functions such as `np.random.rand` share one hidden state across the whole
    program."""),
)

section("warmup", "Warm-up",
    predict("Dtypes and shapes", "easy",
        code="""
        import numpy as np

        a = np.array([[1, 2, 3], [4, 5, 6]])
        print(a.shape, a.dtype, a.size)
        print(a.reshape(3, -1).shape, a.ravel().shape, a[:, :1].shape, a[:, 0].shape)
        print((a / 2).dtype, (a // 2).dtype, (a > 2).dtype)
        print(np.array([True, 2]).dtype, np.array([1, None]).dtype)
        print(np.array([200], dtype=np.uint8) + np.uint8(100))
        """,
        hints=["`-1` in `reshape` means \"whatever fits\". Slicing `:1` keeps the dimension, an integer index removes it. `uint8` holds 0 to 255."],
        why="""`a` is 2 by 3 with 6 integers (`int32` in this 32-bit browser Python, `int64` on most machines). `reshape(3, -1)` infers 2 columns; `ravel` flattens to `(6,)`. The slice `:1` keeps a column dimension of size 1, giving
        `(2, 1)`, while the integer `0` removes it, giving `(2,)`: the same distinction that causes broadcasting bugs. True division always gives floats, floor
        division keeps ints, comparisons give bools. A bool mixed with an int becomes an int; `None` cannot be stored as a number, so the array falls back to
        `object` dtype (slow, Python objects again). `200 + 100` does not fit in `uint8` and wraps around to `300 - 256 = 44`."""),
    predict("Views or copies", "easy",
        code="""
        import numpy as np

        a = np.arange(6)
        b = a[2:5]
        c = a[a > 3]
        d = a.reshape(2, 3)
        b[0] = 100
        c[0] = -1
        d[1, 2] = 7
        print(a)
        print(b, c)
        e = a[::2].copy()
        e[:] = 0
        print(a[::2], np.shares_memory(a, d))
        """,
        hints=["Slices and reshapes share memory with `a`; a boolean mask makes a copy; `.copy()` always does."],
        why="""`b` is a slice and `d` a reshape, so both write into `a`: position 2 becomes 100 and position 5 (row 1, column 2 of `d`) becomes 7. `c` was made with a mask,
        so it is a copy holding `[4, 5]` at the time; setting `c[0]` changes only `c`. `e` is an explicit copy, so zeroing it leaves `a[::2]` as `[0, 100, 4]`. The same
        rules decide whether a function that receives an array can damage the caller's data."""),
    write("Normalise embeddings to unit length", "easy", tag="GenAI",
        prompt="""Cosine search needs every embedding scaled to length 1. Write `normalise(E, eps=1e-12)` for a 2-D array of shape `(n, d)`: return a new `float64` array in
        which each row is divided by its Euclidean norm, without a Python loop and without changing `E`. A row of all zeros must stay zeros (divide by `max(norm,
        eps)`), not become NaN.""",
        code="""
        import numpy as np


        def normalise(E, eps=1e-12):
            out = []
            for row in E:
                out.append(row / np.linalg.norm(row))
            return np.array(out)
        """,
        tests="""
        E = np.array([[3, 4], [0, 0], [1, 1]])
        N = normalise(E)
        assert N.dtype == np.float64 and N.shape == (3, 2)
        assert np.allclose(N[0], [0.6, 0.8])
        assert np.array_equal(N[1], [0.0, 0.0])
        assert np.allclose(np.linalg.norm(N[[0, 2]], axis=1), 1.0)
        assert E.tolist() == [[3, 4], [0, 0], [1, 1]]
        assert "for " not in __source__
        """,
        hints=["`np.linalg.norm(E, axis=1, keepdims=True)` gives shape `(n, 1)`, which broadcasts across each row.", "`np.maximum(norms, eps)` replaces tiny norms."],
        solution="""
        import numpy as np


        def normalise(E, eps=1e-12):
            E = np.asarray(E, dtype=np.float64)
            norms = np.linalg.norm(E, axis=1, keepdims=True)
            return E / np.maximum(norms, eps)
        """,
        why="""`axis=1` computes one norm per row, and `keepdims=True` keeps it as a `(n, 1)` column so the division broadcasts across the row's `d` values. Without
        `keepdims`, a `(n,)` vector would be lined up with the **columns** instead, which only happens to work when `n == d` and is wrong even then. `np.maximum`
        with a tiny `eps` keeps zero rows at zero instead of producing `0 / 0 = nan`, which would otherwise poison every similarity score computed later.
        `np.asarray(..., dtype=float64)` converts integer input and creates a new array, so the caller's data is never modified."""),
    write("Min-max scale each feature column", "easy", tag="ML",
        prompt="""Write `minmax(X)` that rescales each **column** of a 2-D array to the range 0 to 1: `(x - column min) / (column max - column min)`. A constant column
        (max equals min) must become all zeros instead of NaN. Return a new float array; no loops.""",
        code="""
        import numpy as np


        def minmax(X):
            X = np.asarray(X, dtype=float)
            return (X - X.min()) / (X.max() - X.min())
        """,
        tests="""
        X = np.array([[1, 10, 5], [3, 30, 5], [5, 20, 5]])
        S = minmax(X)
        assert S.shape == (3, 3)
        assert np.allclose(S[:, 0], [0.0, 0.5, 1.0])
        assert np.allclose(S[:, 1], [0.0, 1.0, 0.5])
        assert np.array_equal(S[:, 2], [0.0, 0.0, 0.0])
        assert not np.isnan(S).any()
        """,
        hints=["`X.min(axis=0)` gives one minimum per column.", "Replace a zero range with 1 using `np.where(rng == 0, 1, rng)`: the numerator is already 0 there."],
        solution="""
        import numpy as np


        def minmax(X):
            X = np.asarray(X, dtype=float)
            lo = X.min(axis=0)
            rng = X.max(axis=0) - lo
            return (X - lo) / np.where(rng == 0, 1.0, rng)
        """,
        why="""Without an axis, `min` and `max` look at the whole matrix, so every column is scaled by the global range (1 to 30) and only the widest column reaches 1.
        `axis=0` collapses the rows and leaves one statistic per column, shape `(3,)`, which broadcasts against `(3, 3)` row by row. For a constant column the range
        is 0; dividing by 1 there leaves `x - min = 0`, the conventional output, instead of `0 / 0`. In a real pipeline the min and max are learned on the
        training split only and reused on the test split, which is exactly what scikit-learn's `MinMaxScaler` does in D.6."""),
)

section("medium", "Medium",
    fix("A mean squared error that is quietly wrong", "medium", tag="ML",
        prompt="""The model returns predictions as a column, shape `(n, 1)`, and the targets are a flat `(n,)` array. The metric below runs without error but reports the
        wrong number. Fix `mse` so it accepts either shape for either argument, and raises `ValueError` if the two do not hold the same number of values.""",
        code="""
        import numpy as np


        def mse(y_true, y_pred):
            y_true = np.asarray(y_true, dtype=float)
            y_pred = np.asarray(y_pred, dtype=float)
            return float(((y_true - y_pred) ** 2).mean())
        """,
        tests="""
        y = np.array([1.0, 2.0, 3.0])
        p = np.array([[1.0], [2.0], [5.0]])
        assert abs(mse(y, p) - 4 / 3) < 1e-12
        assert abs(mse(p, y) - 4 / 3) < 1e-12
        assert mse([0, 0], [0, 0]) == 0.0
        import pytest
        with pytest.raises(ValueError):
            mse([1, 2, 3], [1, 2])
        """,
        hints=["Print `(y_true - y_pred).shape` for the failing case.", "`reshape(-1)` flattens both; then compare sizes."],
        solution="""
        import numpy as np


        def mse(y_true, y_pred):
            y_true = np.asarray(y_true, dtype=float).reshape(-1)
            y_pred = np.asarray(y_pred, dtype=float).reshape(-1)
            if y_true.shape != y_pred.shape:
                raise ValueError(f"shapes differ: {y_true.shape} vs {y_pred.shape}")
            return float(((y_true - y_pred) ** 2).mean())
        """,
        why="""`(3,)` minus `(3, 1)` broadcasts to `(3, 3)`: every target minus every prediction. Its mean is a real number, so nothing fails, and a model can be
        "selected" on a metric that measures nothing. Flattening both inputs makes the subtraction element by element, and checking the shapes afterwards turns a
        length mismatch into a clear error instead of another broadcast. scikit-learn's metrics do the same validation, which is one reason to use them in D.6."""),
    write("A numerically stable softmax", "medium", tag="ML",
        prompt="""Write `softmax(z, axis=-1)` for an array of any number of dimensions: probabilities along `axis` that sum to 1, without overflow for large scores and
        without loops. Also write `log_softmax(z, axis=-1)` that returns `log(softmax(z))` computed stably as `z - max - log(sum(exp(z - max)))`, so that very
        negative log-probabilities stay finite instead of becoming `log(0) = -inf`.""",
        code="""
        import numpy as np


        def softmax(z, axis=-1):
            e = np.exp(z)
            return e / e.sum()


        def log_softmax(z, axis=-1):
            return np.log(softmax(z, axis))
        """,
        tests="""
        z = np.array([[1000.0, 1001.0, 1002.0], [1.0, 2.0, 3.0]])
        with np.errstate(all="ignore"):
            s = softmax(z)
        assert np.all(np.isfinite(s))
        assert np.allclose(s.sum(axis=1), 1.0)
        assert np.allclose(s[0], s[1])
        assert np.allclose(softmax(np.array([0.0, np.log(3.0)])), [0.25, 0.75])
        assert np.allclose(softmax(z, axis=0)[:, 0], [1.0, 0.0])
        with np.errstate(all="ignore"):
            ls = log_softmax(np.array([0.0, -1000.0]))
        assert np.isfinite(ls).all() and abs(ls[1] - (-1000.0)) < 1e-9
        """,
        hints=["Subtract `z.max(axis=axis, keepdims=True)` before `exp`.", "Sum with the same `axis` and `keepdims=True`."],
        solution="""
        import numpy as np


        def softmax(z, axis=-1):
            z = np.asarray(z, dtype=float)
            z = z - z.max(axis=axis, keepdims=True)
            e = np.exp(z)
            return e / e.sum(axis=axis, keepdims=True)


        def log_softmax(z, axis=-1):
            z = np.asarray(z, dtype=float)
            z = z - z.max(axis=axis, keepdims=True)
            return z - np.log(np.exp(z).sum(axis=axis, keepdims=True))
        """,
        why="""Softmax does not change if you subtract the same constant from every score in a row, because the constant cancels between numerator and denominator.
        Subtracting the row maximum makes the largest exponent `exp(0) = 1`, so nothing overflows, and rows `[1000, 1001, 1002]` and `[1, 2, 3]` give identical
        probabilities, as they should. The starter also summed over the **whole array**, so rows did not sum to 1 individually. `log_softmax` is the
        log-sum-exp trick: `log(exp(-1000) / ...)` underflows to `log(0)`, but `-1000 - log(1 + exp(-1000))` is finite. Cross-entropy losses in every framework
        are built from this, never from `log(softmax(z))`."""),
    write("Top-k cosine search over embeddings", "medium", tag="GenAI",
        prompt="""Write `search(query, E, k)`: `E` is an `(n, d)` matrix of document embeddings, `query` a `(d,)` vector. Return a list of `(index, score)` for the `k`
        documents with the highest cosine similarity, best first, scores rounded to 4 places, ties broken by the smaller index. Use one matrix-vector product for
        the similarities and `np.argpartition` to find candidates (not a full sort of all `n`). If `k >= n`, return all documents ranked.""",
        code="""
        import numpy as np


        def search(query, E, k):
            results = []
            for i, row in enumerate(E):
                score = row @ query
                results.append((i, round(float(score), 4)))
            results.sort(key=lambda t: -t[1])
            return results[:k]
        """,
        tests="""
        E = np.array([[1.0, 0.0], [10.0, 10.0], [0.0, 3.0], [-1.0, 0.0], [2.0, 2.0]])
        q = np.array([1.0, 1.0])
        assert search(q, E, 2) == [(1, 1.0), (4, 1.0)]
        assert search(q, E, 3)[2] == (0, 0.7071)
        assert [i for i, _ in search(q, E, 10)] == [1, 4, 0, 2, 3]
        assert search(np.array([0.0, 2.0]), E, 1) == [(2, 1.0)]
        assert "argpartition" in __source__ and "for i, row" not in __source__
        """,
        hints=["Normalise `E` rows and `query`, then `sims = En @ qn`.", "`np.argpartition(-sims, k - 1)[:k]` finds the `k` best, but which of several tied scores it keeps is arbitrary: use it to find the cut-off score, then keep everything at or above it."],
        solution="""
        import numpy as np


        def search(query, E, k):
            E = np.asarray(E, dtype=float)
            q = np.asarray(query, dtype=float)
            En = E / np.maximum(np.linalg.norm(E, axis=1, keepdims=True), 1e-12)
            qn = q / max(np.linalg.norm(q), 1e-12)
            sims = np.round(En @ qn, 4)
            n = len(sims)
            if k >= n:
                idx = np.arange(n)
            else:
                cut = sims[np.argpartition(-sims, k - 1)[:k]].min()
                idx = np.flatnonzero(sims >= cut)
            order = sorted(idx.tolist(), key=lambda i: (-sims[i], i))[:k]
            return [(i, float(sims[i])) for i in order]
        """,
        why="""The starter used raw dot products, so long vectors win: `[10, 10]` scores 20 against `[2, 2]`'s 4, although they point in exactly the same direction.
        Cosine similarity divides out the lengths, which is why both score 1.0 and the index breaks the tie. `argpartition(-sims, k - 1)` places the `k`
        largest similarities in the first `k` slots in `O(n)`, but when several documents tie with the `k`-th score it keeps an arbitrary one of them: here
        documents 0 and 2 both score 0.7071 for the third place. So the solution uses the partition only to find the cut-off score, keeps every document at or
        above it (a handful), and sorts those by `(-score, index)`. Rounding before ranking makes ties exact, so the tie rule is applied to scores that print the
        same. This is what a vector database does in miniature; with a million documents it replaces a million-element sort with a
        linear pass."""),
    choose("A Python loop or a vectorised expression", "medium", tag="Data work",
        prompt="Both compute the squared distance of 20,000 points to one centre. Which is faster?",
        setup="""import numpy as np
X = np.random.default_rng(0).normal(size=(20_000, 3))
c = np.array([0.5, -0.2, 1.0])""",
        options={
            "a": "d = np.array([((row - c) ** 2).sum() for row in X])",
            "b": "d = ((X - c) ** 2).sum(axis=1)",
        },
        answer="b",
        hints=["How many times does each option enter NumPy from Python?"],
        why="""Option A enters NumPy 20,000 times, and every call pays Python overhead: building a small array for `row - c`, another for the square, and a sum, each with
        type checks and allocation, to do three multiplications. Option B makes three whole-array calls, and the loops over 60,000 numbers run in compiled code. The
        measured gap is close to 100 times, and it grows with the data. The rule: a Python `for` over the rows of an array is a smell; look for an
        `axis=` argument, broadcasting, or a matrix product."""),
    write("One-hot encode labels with fancy indexing", "medium", tag="ML",
        prompt="""Write `one_hot(labels, n_classes)` that turns an integer label array of shape `(n,)` into an `(n, n_classes)` float array with a 1 in each row's label
        column and 0 elsewhere. Raise `ValueError` if any label is negative or `>= n_classes`. Use integer-array indexing, not a loop. Also write `from_one_hot(Y)`
        that goes back to the labels.""",
        code="""
        import numpy as np


        def one_hot(labels, n_classes):
            Y = np.zeros((len(labels), n_classes))
            Y[:, labels] = 1
            return Y


        def from_one_hot(Y):
            return Y.max(axis=1)
        """,
        tests="""
        Y = one_hot(np.array([2, 0, 1, 2]), 3)
        assert Y.shape == (4, 3) and Y.dtype == np.float64
        assert Y.tolist() == [[0, 0, 1], [1, 0, 0], [0, 1, 0], [0, 0, 1]]
        assert from_one_hot(Y).tolist() == [2, 0, 1, 2]
        import pytest
        with pytest.raises(ValueError):
            one_hot(np.array([0, 3]), 3)
        with pytest.raises(ValueError):
            one_hot(np.array([-1]), 3)
        """,
        hints=["`Y[rows, cols] = 1` with `rows = np.arange(n)` sets exactly one cell per row.", "`argmax` returns the column of the largest value."],
        solution="""
        import numpy as np


        def one_hot(labels, n_classes):
            labels = np.asarray(labels)
            if labels.size and (labels.min() < 0 or labels.max() >= n_classes):
                raise ValueError("label out of range")
            Y = np.zeros((labels.size, n_classes))
            Y[np.arange(labels.size), labels] = 1.0
            return Y


        def from_one_hot(Y):
            return np.asarray(Y).argmax(axis=1)
        """,
        why="""`Y[:, labels] = 1` selects whole **columns**: every row gets a 1 in every column that appears anywhere in `labels`. Pairing two index arrays,
        `Y[np.arange(n), labels]`, selects one cell per row: (0, 2), (1, 0), (2, 1), (3, 2). Negative labels would silently index from the end (`-1` is the last
        class), which is why the range check comes first. `max(axis=1)` returns the value 1, not where it is; `argmax` returns the position, which is the label.
        The same `argmax(axis=1)` turns a classifier's probability matrix into predictions."""),
    fix("A helper that edits the caller's array", "medium", tag="ML",
        prompt="""`clip_outliers(x, limit)` is meant to return a copy of a feature column with values above `limit` replaced by `limit`. After calling it, the training data
        itself has changed, which corrupted a later experiment. Fix it so the input is never modified, keeping it vectorised.""",
        code="""
        import numpy as np


        def clip_outliers(x, limit):
            col = x[:]
            col[col > limit] = limit
            return col
        """,
        tests="""
        data = np.array([1.0, 50.0, 3.0, 99.0])
        out = clip_outliers(data, 10.0)
        assert out.tolist() == [1.0, 10.0, 3.0, 10.0]
        assert data.tolist() == [1.0, 50.0, 3.0, 99.0]
        assert not np.shares_memory(out, data)
        X = np.array([[1.0, 20.0], [30.0, 2.0]])
        assert clip_outliers(X[:, 0], 5.0).tolist() == [1.0, 5.0] and X[1, 0] == 30.0
        """,
        hints=["For lists, `x[:]` copies. For arrays, what does a slice return?", "`np.minimum(x, limit)` or `np.clip` return new arrays."],
        solution="""
        import numpy as np


        def clip_outliers(x, limit):
            return np.minimum(x, limit)
        """,
        why="""For a Python list, `x[:]` is a copy, and the bug comes from carrying that habit over: for a NumPy array a slice is a **view**, so the masked assignment
        writes into the caller's memory. The column `X[:, 0]` is itself a view of the matrix, so the damage reaches the whole dataset. `np.minimum(x, limit)` (or
        `np.clip(x, None, limit)`) computes a new array in one call. Where an in-place update is really wanted for memory reasons, say so in the name or the
        docstring, as NumPy does with `out=` parameters."""),
)

section("hard", "Hard",
    write("Pairwise distances without loops", "hard", tag="ML",
        prompt="""k-nearest-neighbours needs the squared Euclidean distance between every row of `A` `(n, d)` and every row of `B` `(m, d)`. Write `pairwise_sq(A, B)`
        returning an `(n, m)` array, using the expansion `|a - b|^2 = |a|^2 + |b|^2 - 2 a.b` with one matrix product, no Python loops and no `(n, m, d)`
        intermediate array. Rounding can make tiny results negative; clip them at 0. Then write `knn_predict(A_train, y_train, A_test, k)` that returns the
        majority label among the `k` nearest training rows for each test row (ties go to the smaller label).""",
        code="""
        import numpy as np


        def pairwise_sq(A, B):
            return ((A[:, None, :] - B[None, :, :]) ** 2).sum(axis=2)


        def knn_predict(A_train, y_train, A_test, k):
            pass
        """,
        tests="""
        A = np.array([[0.0, 0.0], [1.0, 1.0], [3.0, 4.0]])
        B = np.array([[0.0, 0.0], [3.0, 4.0]])
        D = pairwise_sq(A, B)
        assert D.shape == (3, 2)
        assert np.allclose(D, [[0, 25], [2, 13], [25, 0]])
        assert (pairwise_sq(B, B) >= 0).all() and np.allclose(np.diag(pairwise_sq(B, B)), 0)
        assert "None, :, :" not in __source__ and "@" in __source__
        Xtr = np.array([[0, 0], [0, 1], [5, 5], [6, 5], [5, 6]], dtype=float)
        ytr = np.array([0, 0, 1, 1, 1])
        assert knn_predict(Xtr, ytr, np.array([[0.2, 0.3], [5.5, 5.2]]), 3).tolist() == [0, 1]
        assert knn_predict(Xtr, ytr, np.array([[2.5, 2.5]]), 2).tolist() == [0]
        """,
        hints=["`(A ** 2).sum(axis=1)[:, None]` is `(n, 1)`, `(B ** 2).sum(axis=1)[None, :]` is `(1, m)`, and `A @ B.T` is `(n, m)`.",
               "For each test row, `np.argsort(D[i])[:k]` gives the neighbours; `np.bincount(labels).argmax()` takes the smallest label on ties."],
        solution="""
        import numpy as np


        def pairwise_sq(A, B):
            A = np.asarray(A, dtype=float)
            B = np.asarray(B, dtype=float)
            aa = (A ** 2).sum(axis=1)[:, None]
            bb = (B ** 2).sum(axis=1)[None, :]
            return np.maximum(aa + bb - 2 * A @ B.T, 0.0)


        def knn_predict(A_train, y_train, A_test, k):
            D = pairwise_sq(A_test, A_train)
            nearest = np.argsort(D, axis=1, kind="stable")[:, :k]
            votes = np.asarray(y_train)[nearest]
            return np.array([np.bincount(row).argmax() for row in votes])
        """,
        why="""The starter is correct but builds an `(n, m, d)` array: for 10,000 test rows, 100,000 training rows and 768 dimensions that is 768 billion numbers, far more
        memory than any machine has. The expansion needs only the `(n, m)` result: squared norms as a column and a row, broadcast together, minus twice the
        matrix product, which runs in optimised BLAS code. Floating-point cancellation can leave values like `-1e-15` for identical points, hence the clip. For
        the vote, `argsort` along `axis=1` ranks the neighbours of every test row at once, fancy indexing `y_train[nearest]` looks up their labels as a
        `(n_test, k)` array, and `bincount(...).argmax()` returns the first (smallest) label among the most common, which is the tie rule. In the second test the
        two nearest points are one of each class, so the tie goes to 0."""),
    write("Masked mean pooling for a batch of sentences", "hard", tag="GenAI",
        prompt="""A transformer returns token embeddings of shape `(batch, tokens, dim)` and an attention mask `(batch, tokens)` with 1 for real tokens and 0 for padding.
        Write `mean_pool(H, mask)` returning `(batch, dim)` sentence embeddings: the mean over real tokens only. A sentence with no real tokens must give zeros,
        not NaN. Then write `max_pool(H, mask)`, the element-wise maximum over real tokens only (padding must never win, even if its values are large; an empty
        sentence again gives zeros). No loops.""",
        code="""
        import numpy as np


        def mean_pool(H, mask):
            return H.mean(axis=1)


        def max_pool(H, mask):
            return H.max(axis=1)
        """,
        tests="""
        H = np.array([[[1.0, 2.0], [3.0, 4.0], [100.0, 100.0]],
                      [[5.0, -1.0], [7.0, -3.0], [9.0, 9.0]],
                      [[4.0, 4.0], [4.0, 4.0], [4.0, 4.0]]])
        mask = np.array([[1, 1, 0], [1, 1, 1], [0, 0, 0]])
        mp = mean_pool(H, mask)
        assert mp.shape == (3, 2)
        assert np.allclose(mp, [[2.0, 3.0], [7.0, 5 / 3], [0.0, 0.0]])
        xp = max_pool(H, mask)
        assert np.allclose(xp, [[3.0, 4.0], [9.0, 9.0], [0.0, 0.0]])
        assert H[0, 2, 0] == 100.0
        """,
        hints=["`mask[..., None]` has shape `(batch, tokens, 1)`, which broadcasts over `dim`.",
               "For the max, replace padding with `-np.inf` using `np.where`, take the max, then turn rows that stayed `-inf` into 0."],
        solution="""
        import numpy as np


        def mean_pool(H, mask):
            m = np.asarray(mask, dtype=float)[..., None]
            summed = (H * m).sum(axis=1)
            counts = m.sum(axis=1)
            return summed / np.maximum(counts, 1.0)


        def max_pool(H, mask):
            m = np.asarray(mask, dtype=bool)[..., None]
            masked = np.where(m, H, -np.inf)
            out = masked.max(axis=1)
            return np.where(np.isinf(out), 0.0, out)
        """,
        why="""Padding tokens exist only to make sentences the same length, so including them drags every short sentence's embedding towards whatever the padding
        vectors happen to be (here 100). Adding an axis to the mask, `(batch, tokens, 1)`, lets it broadcast over the embedding dimension, so multiplying zeroes
        the padding, and dividing by the count of real tokens gives the true mean. Clamping the count at 1 turns an empty sentence into `0 / 1`. For max pooling,
        multiplying by 0 is not enough (a 0 could beat negative real values), so padding is replaced with `-inf`, which can never win; a row with no real tokens
        stays `-inf` and is set to 0. `np.where` builds new arrays, so `H` is untouched. This is exactly how sentence-transformers pools BERT outputs."""),
    write("A confusion matrix in one call", "hard", tag="ML",
        prompt="""Write `confusion(y_true, y_pred, n_classes)` returning an `(n_classes, n_classes)` integer matrix where cell `[i, j]` counts examples whose true class
        is `i` and predicted class is `j`, with no Python loop over examples. Then write `per_class_recall(C)` (diagonal divided by row sums) and
        `per_class_precision(C)` (diagonal divided by column sums), returning 0.0 for classes with no examples in the relevant direction instead of NaN.""",
        code="""
        import numpy as np


        def confusion(y_true, y_pred, n_classes):
            C = np.zeros((n_classes, n_classes), dtype=int)
            C[y_true, y_pred] += 1
            return C


        def per_class_recall(C):
            return np.diag(C) / C.sum(axis=0)


        def per_class_precision(C):
            return np.diag(C) / C.sum(axis=1)
        """,
        tests="""
        yt = np.array([0, 0, 1, 1, 1, 2])
        yp = np.array([0, 1, 1, 1, 0, 1])
        C = confusion(yt, yp, 3)
        assert C.tolist() == [[1, 1, 0], [1, 2, 0], [0, 1, 0]]
        assert C.dtype.kind == "i"
        assert np.allclose(per_class_recall(C), [0.5, 2 / 3, 0.0])
        assert np.allclose(per_class_precision(C), [0.5, 0.5, 0.0])
        with np.errstate(all="raise"):
            per_class_recall(confusion(np.array([0]), np.array([0]), 2))
        """,
        hints=["`C[rows, cols] += 1` with repeated pairs only adds once. Combine the pair into one index, `y_true * n + y_pred`, and count with `np.bincount(..., minlength=n * n)`.",
               "Recall uses row sums (`axis=1`); divide only where the sum is positive, for example with `np.divide(a, b, out=np.zeros(...), where=b > 0)`."],
        solution="""
        import numpy as np


        def confusion(y_true, y_pred, n_classes):
            idx = np.asarray(y_true) * n_classes + np.asarray(y_pred)
            return np.bincount(idx, minlength=n_classes * n_classes).reshape(n_classes, n_classes)


        def _safe_div(a, b):
            a = a.astype(float)
            return np.divide(a, b, out=np.zeros_like(a), where=b > 0)


        def per_class_recall(C):
            return _safe_div(np.diag(C), C.sum(axis=1))


        def per_class_precision(C):
            return _safe_div(np.diag(C), C.sum(axis=0))
        """,
        why="""Buffered fancy assignment is the trap: `C[y_true, y_pred] += 1` reads all the cells, adds 1, and writes them back, so a pair that occurs twice is still
        counted once. Encoding each `(true, pred)` pair as one integer `true * n + pred` and counting with `bincount` handles repeats, and `minlength` guarantees
        all `n * n` cells exist before reshaping. (`np.add.at(C, (y_true, y_pred), 1)` is the unbuffered alternative.) The starter also swapped the axes: recall
        asks "of the true class-i examples, how many were found", which is row `i`, so it divides by row sums; precision divides by column sums. `np.divide` with
        `where=` skips empty classes instead of dividing by zero, and the last test turns any division warning into an error to prove it."""),
    predict("Precision you did not ask for", "hard",
        code="""
        import numpy as np

        big = np.float32(16_777_216)
        print(big + 1 == big, np.float64(16_777_216) + 1 == 16_777_216)
        x = np.full(10_000_000, 0.1, dtype=np.float32)
        print(round(float(x.sum()), 1), round(float(x.astype(np.float64).sum()), 1))
        s = np.float32(0)
        for _ in range(10_000):
            s += np.float32(0.1)
        print(round(float(s), 2))
        print(np.array([3_000_000_000]).dtype, np.array([2, 3], dtype=np.int32).prod() ** 31 < 0)
        print((np.arange(5) / 0.1)[3], np.arange(0, 1, 0.1).size, np.linspace(0, 1, 11).size)
        """,
        hints=["`float32` has 24 bits of precision: 16,777,216 is 2 to the 24th. NumPy's `sum` adds in pairs, not one by one."],
        why="""At 2^24, adjacent `float32` values are 2 apart, so adding 1 rounds back to the same number, while `float64` still has room. Summing ten million `float32`
        values of 0.1 gives `1000000.1` in `float32` and `1000000.0` in `float64`. The stored value of `float32(0.1)` is slightly above 0.1, so the exact total is
        about 1,000,000.015; near a million, `float32` can only step in sixteenths, so it lands a little off. That error is small because NumPy uses **pairwise
        summation**. A naive one-at-a-time loop, as in the third line, rounds at every step, so 10,000 additions already drift to `999.9` instead of 1,000.0.
        This is why mixed-precision training keeps sums and optimiser state in `float32` or `float64` while the bulk data is in 16 bits. Integers too large for `int32` get `int64` automatically, but arithmetic inside a fixed dtype wraps: `6 ** 31` overflows
        `int32` and comes out negative. The last line shows float steps: `arange(0, 1, 0.1)` gives 10 values here, but such counts can change with rounding;
        `linspace` states the count directly."""),
)

section("interview", "Interview questions",
    explain("What is the difference between a view and a copy in NumPy, and when does each happen?", "medium", tag="Interview",
        why="""A **view** is a new array object that shares memory with another array; a **copy** owns its own memory. Basic indexing with integers and slices
        (`a[2:5]`, `m[:, 0]`, `a[::2]`), `reshape` when the layout allows, `.T` and `ravel` when possible all return views, because the selected elements can be
        described as the same buffer with different offsets and strides. Advanced indexing, with boolean masks or integer arrays, returns copies, because the
        chosen elements are scattered. Arithmetic always produces new arrays. Consequences: writing to a view changes the original (a feature for in-place
        updates of big data, a bug when a helper modifies its caller's training set), and a small view keeps a huge base array alive in memory. Check with
        `np.shares_memory` or `arr.base`, and call `.copy()` when you need independence. pandas has the same question, which pandas 3 answers with Copy-on-Write
        (D.2)."""),
    explain("Explain broadcasting, and describe a bug it can cause.", "medium", tag="Interview",
        why="""Broadcasting lets NumPy combine arrays of different shapes without copying data. Shapes are compared from the right; each pair of dimensions must be equal or
        contain a 1, and missing leading dimensions count as 1; size-1 dimensions are stretched virtually. So `(n, d) - (d,)` centres every row, `(n, d) / (n, 1)`
        scales each row by its own value, and `(n, 1) + (1, m)` builds an `(n, m)` grid, the basis of pairwise distances and attention scores. The classic bug is
        `(n,)` combined with `(n, 1)`: it broadcasts to `(n, n)` instead of failing, so `y_true - y_pred` with a column of predictions computes every target minus
        every prediction, and an MSE or accuracy is silently wrong. Defences: flatten predictions, use `keepdims=True` for reductions you will broadcast back,
        assert shapes at function boundaries, and prefer library metrics that validate inputs."""),
    explain("Why is vectorised NumPy code so much faster than a Python loop, and when is it not the answer?", "hard", tag="Interview",
        why="""A Python loop executes bytecode for every element: it fetches an object, checks its type, dispatches the operation, allocates a result object and updates
        reference counts. A vectorised NumPy call checks types once and runs a compiled loop over a contiguous block of a single dtype, often using SIMD
        instructions, and matrix products go to optimised BLAS libraries that use cache blocking and several cores. That is typically 10 to 100 times faster, and
        more for matrix work. It is not always the answer: vectorising can create huge temporary arrays (the `(n, m, d)` distance cube), so you may need chunking
        or a smarter formula; computations where each step depends on the previous (a recurrence, an early-exit search) do not vectorise naturally and are
        better served by Numba, Cython, or a library function that already implements them; and for tiny arrays the per-call overhead of NumPy can exceed a plain
        loop. Measure, as Module 16 said, and remember that clarity matters: `np.where` chains five deep are harder to review than a loop."""),
)

recap(
    "An `ndarray` is one block of memory with one dtype and a shape; operations run as compiled loops. Fixed-size ints wrap on overflow; `float32` keeps about 7 digits.",
    "Slices and reshapes are **views** (writes reach the original); masks and integer-array indexing make **copies**. Check with `np.shares_memory`, copy with `.copy()`.",
    "Broadcasting matches shapes from the right and stretches size-1 dimensions; `(n,)` with `(n, 1)` silently gives `(n, n)`, so flatten or assert shapes.",
    "`axis` is the dimension that is collapsed: `axis=0` gives one value per column, `axis=1` one per row; `keepdims=True` keeps it ready to broadcast back.",
    "Vectorised ML blocks: stable softmax (subtract the max), cosine search (normalise once, one matrix product, `argpartition`), masked pooling, `bincount`.",
)
