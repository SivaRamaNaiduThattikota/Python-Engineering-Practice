from lesson import *
from diagrams import *

lesson(
    id="m17-2", num="D.2", title="pandas essentials: selection, cleaning and dtypes",
    intro="pandas is where raw data becomes model input. DataFrames and their dtypes, selecting with `loc` and `iloc`, boolean filters, missing values, "
          "type conversion, the new defaults of pandas 3 (the `str` dtype and Copy-on-Write), and the cleaning steps that come before every model: "
          "trimming, de-duplicating, a data quality report, and imputation without leakage.",
    desc="DataFrames, loc and iloc, filters, missing values, dtypes, pandas 3 strings and Copy-on-Write, cleaning for ML.",
    keys="pandas dataframe series index read_csv stringio dtypes info describe head loc iloc boolean filter isin between query missing nan isna fillna dropna nullable int64 pd.NA astype to_numeric coerce str dtype string copy-on-write chained assignment ChainedAssignmentError assign method chaining duplicated drop_duplicates value_counts data quality report imputation leakage train test split memory_usage",
)

term("DataFrame", "pandas' table: named columns, each a Series with its own dtype, sharing one row index.")
term("Index", "The row labels of a Series or DataFrame; `loc` selects by these labels, `iloc` by position.")
term("Copy-on-Write", "pandas 3's rule that every result of indexing behaves as a copy: changing it never changes the original, and chained assignment has no effect.")
term("Imputation", "Filling missing values with an estimate, such as the training median; the estimate must be learned from training data only.")

CSV = '''id,product,issue,amount,state,submitted
101, Mortgage ,Late fee,120.5,CA,2026-01-03
102,credit card,Billing dispute,,NY,2026-01-05
103,Mortgage,Escrow,n/a,,2026-01-05
102,credit card,Billing dispute,,NY,2026-01-05
104,Student loan,Repayment,89,TX,2026-01-09'''
CSV_IN = CSV.replace("\n", "\n    ")   # indent the data lines like the example code, so dedent keeps them intact

section("frames", "DataFrames, Series and dtypes",
    p("""A **DataFrame** is a table: named **columns**, each one a **Series** (a one-dimensional array with a dtype, usually a NumPy array underneath), all sharing a
    row **Index**. If you know Power BI, a DataFrame is a table in the data view and a Series is one column; if you know SQL, it is the result of a `SELECT`,
    held in memory, that you can keep transforming in Python. Because each column has one dtype, column operations are vectorised like D.1's arrays, and
    the same rule applies: work with whole columns, not row loops."""),
    p("""The first three calls on any new dataset are `df.head()` (the first rows), `df.info()` (each column's dtype and non-null count, plus memory) and
    `df.describe()` (count, mean, spread and quartiles of the numeric columns). `info` is the most useful: a numeric column read as text, or a column that is
    90% empty, shows up immediately."""),
    ex(f"""
    import io
    import pandas as pd

    CSV = '''{CSV_IN}'''
    df = pd.read_csv(io.StringIO(CSV))
    print(df.shape)
    print(df.head(3))
    df.info()
    print(df["amount"].describe().round(2).to_dict())
    """, "frames.py"),
    p("""Read the `info` output column by column. `id` is `int64`. `product`, `issue` and `state` have dtype **`str`**: since pandas 3, text columns get a real string
    dtype instead of the old catch-all `object`, so `.str` methods are fast and a non-string cannot sneak in. `amount` is `float64` with only 2 non-null
    values: `read_csv` treats empty fields and common markers such as `n/a`, `NA` and `null` as missing (`NaN`), and a column of integers with a missing
    value becomes float, because NumPy integers have no "missing" value. `submitted` is text: dates are not parsed unless you ask (`parse_dates=` or
    `pd.to_datetime`, D.4). And notice what pandas did **not** fix: the padded `" Mortgage "`, the lower-case `credit card`, the duplicated complaint 102."""),
)

section("select", "Selecting rows and columns",
    p("""`df["col"]` returns one column as a Series and `df[["a", "b"]]` several as a DataFrame. For rows, use the two indexers and never mix them up. **`loc`** selects
    by **label**: `df.loc[row_labels, column_labels]`, and its slices **include** the end label (`df.loc[0:2]` is three rows). **`iloc`** selects by **position**,
    like NumPy, and its slices **exclude** the end (`df.iloc[0:2]` is two rows). After filtering or sorting, labels and positions no longer agree, which is
    exactly when the difference bites."""),
    fig(table(["expression", "selects", "end included?"], [
        ["df['amount']", "one column, as a Series", ""],
        ["df[['id', 'amount']]", "two columns, as a DataFrame", ""],
        ["df.loc[2:4, 'issue']", "rows labelled 2 to 4, one column", "yes"],
        ["df.iloc[2:4, 0]", "positions 2 and 3, first column", "no"],
        ["df.loc[mask, ['id']]", "rows where mask is True", ""],
        ["df.query('amount > 100')", "rows matching an expression", ""],
    ], hl={(2, 2), (3, 2)}, label="the main ways to select"),
        "`loc` is by label and includes the end; `iloc` is by position and excludes it, like Python slices."),
    p("""A **boolean mask** is a Series of `True`/`False` aligned to the rows, and `df[mask]` or `df.loc[mask, cols]` keeps the `True` rows: the `WHERE` clause.
    Combine conditions with `&`, `|` and `~`, each in parentheses. `isin([...])` is SQL's `IN`, `between(a, b)` is `BETWEEN` (inclusive), and `query("amount > 100
    and state == 'CA'")` reads like SQL when the expression gets long. Comparisons with `NaN` are always `False`, so a missing amount is in neither `amount >
    100` nor `amount <= 100`; ask for missing rows with `isna()` explicitly."""),
    ex(f"""
    import io
    import pandas as pd

    df = pd.read_csv(io.StringIO('''{CSV_IN}'''))
    print(df.loc[1:3, ["id", "state"]])
    print(df.iloc[1:3, [0, 4]])
    s = df.sort_values("id", ascending=False)
    print(s.loc[4, "id"], s.iloc[0]["id"])
    print(df[(df["amount"] > 100) | (df["state"] == "TX")]["id"].tolist())
    print(df[df["state"].isin(["NY", "TX"])]["id"].tolist())
    print(df["amount"].gt(100).tolist(), df["amount"].le(100).tolist())
    print(df.query("amount > 50 and state != 'CA'")["id"].tolist())
    """, "select.py"),
)

section("missing", "Missing values",
    p("""pandas marks missing data with `NaN` in float columns and in the default `str` columns, `NaT` in datetime columns, and `pd.NA` in the optional **nullable**
    dtypes (`Int64`, `Float64`, `boolean`, `string`), which can hold a missing value without turning integers into floats. `isna()` finds them all; `isna().sum()`
    counts them per column, and `isna().mean()` gives the fraction. Statistics such as `mean` and `sum` **skip** missing values by default, which is convenient
    and dangerous: a mean over 2 of 5 rows looks just like a mean over 5."""),
    p("""Three ways to deal with them, all of which you will use. **Drop** rows (`dropna(subset=[...])`) when the value is essential and rarely missing, such as the
    label of a training example. **Fill** (`fillna(value)` or `fillna({col: value})`) when a sensible default exists: 0 for "no payments", `"unknown"` for a
    category. **Impute** a statistic such as the median for a numeric feature, and add an indicator column `amount_missing` so the model can learn that
    "missing" itself carries information. For ML, the statistic must come from the **training split only**, or the test score leaks information from the
    test set (problem 6)."""),
    ex(f"""
    import io
    import pandas as pd

    df = pd.read_csv(io.StringIO('''{CSV_IN}'''))
    print(df.isna().sum().to_dict())
    print(df["amount"].mean(), df["amount"].count(), len(df))
    print(df.dropna(subset=["state"])["id"].tolist())
    filled = df.fillna({{"state": "unknown", "amount": df["amount"].median()}})
    print(filled[["id", "amount", "state"]])
    print(pd.Series([1, None]).dtype, pd.Series([1, None], dtype="Int64").tolist())
    print(pd.NA == 1, pd.NA | True, pd.NA & False)
    """, "missing.py"),
    p("""The last line shows why `pd.NA` is not just another `NaN`: it follows **three-valued logic**, like SQL's `NULL`. `NA == 1` is `NA` (unknown), `NA | True` is
    `True` (true whatever the unknown is) and `NA & False` is `False`. Using `NA` in an `if` raises `TypeError: boolean value of NA is ambiguous`, which is better
    than silently picking a branch."""),
)

section("dtypes", "Dtypes and conversions",
    p("""Correct dtypes are the difference between a working feature and a silent bug: a numeric column read as text cannot be averaged, an id read as a number
    loses its leading zeros, and a category stored as text wastes memory. `astype("float64")` converts and **raises** on anything that does not parse;
    `pd.to_numeric(s, errors="coerce")` turns unparseable values into `NaN`, which you then count, so data problems become visible numbers instead of crashes.
    Read identifiers as strings from the start with `read_csv(..., dtype={"zip": "str"})`."""),
    p("""Memory follows dtype. `df.memory_usage(deep=True)` reports bytes per column, including the strings themselves. A text column with few distinct values
    (`state`, `product`) is far smaller as **`category`**, which stores each distinct value once plus small integer codes (D.4 covers it), and `float32` halves a
    float column. On a 10-million-row complaint table these choices decide whether the data fits in memory."""),
    ex("""
    import pandas as pd

    raw = pd.Series(["12.5", "7", "n/a", " 30 ", "1,200"])
    try:
        raw.astype("float64")
    except ValueError as e:
        print("astype:", e)
    nums = pd.to_numeric(raw.str.strip().str.replace(",", ""), errors="coerce")
    print(nums.tolist(), nums.isna().sum())
    zips = pd.Series(["02134", "10001"])
    print(zips.astype("int64").tolist(), zips.tolist())
    states = pd.Series(["CA", "NY", "TX", "CA"] * 25_000)
    print(states.dtype, states.memory_usage(deep=True) // 1000, "KB")
    print(states.astype("category").memory_usage(deep=True) // 1000, "KB")
    """, "dtypes.py"),
)

section("cow", "Copy-on-Write and method chaining",
    p("""In older pandas, whether `sub = df[df.a > 0]` was a view or a copy depended on internals, so changing `sub` sometimes changed `df` and sometimes did not, with
    a `SettingWithCopyWarning` that nobody understood. **pandas 3 settles it with Copy-on-Write**: every indexing result **behaves as a copy**. Changing `sub`
    never changes `df` (data is only actually copied when you write, so it stays cheap). The consequence is that **chained assignment**, `df[mask]["col"] = 0`,
    can never work: the first `[]` produces a new object, the assignment changes that object, and it is thrown away. pandas 3 warns with
    `ChainedAssignmentError` and leaves `df` unchanged. Write it as one `loc` call: `df.loc[mask, "col"] = 0`."""),
    fig(flowchart({
        "goal": ("start", 0, 0, "change some values in df"),
        "how": ("ask", 0, 1, "one indexing step?|df.loc[mask, col] = v"),
        "ok": ("good", 1, 1, "df is updated"),
        "chain": ("bad", 0, 2, "df[mask][col] = v: a temporary|copy changes, df does not"),
    }, [("goal", "how"), ("how", "ok", "yes"), ("how", "chain", "no")], cell=(260, 84), label="assignment under Copy-on-Write"),
        "Under Copy-on-Write, only a single indexing step on `df` itself can write into `df`."),
    ex(f"""
    import io, warnings
    import pandas as pd

    df = pd.read_csv(io.StringIO('''{CSV_IN}'''))
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        df[df["state"] == "NY"]["amount"] = 0
    print([type(w.message).__name__ for w in caught], df["amount"].tolist())
    df.loc[df["state"] == "NY", "amount"] = 0
    print(df["amount"].tolist())
    sub = df[["id", "amount"]]
    sub.loc[0, "amount"] = -1
    print(df.loc[0, "amount"], sub.loc[0, "amount"])
    clean = (
        df.assign(product=lambda d: d["product"].str.strip().str.lower())
          .drop_duplicates()
          .query("product != 'student loan'")
          .reset_index(drop=True)
    )
    print(clean[["id", "product"]])
    """, "cow.py"),
    p("""The last statement is **method chaining**: each step returns a new DataFrame, so a cleaning pipeline reads top to bottom like a Power Query applied-steps list,
    without intermediate variables to keep in sync. `assign(col=lambda d: ...)` adds or replaces a column computed from the frame **at that step**, and
    `reset_index(drop=True)` renumbers the rows after filtering. Note that `drop_duplicates` only removed the repeated complaint 102 because its two rows were
    already identical; the `" Mortgage "` row only matches `"Mortgage"` after the strip and lower-casing."""),
)

section("warmup", "Warm-up",
    predict("loc, iloc and a shuffled index", "easy",
        code="""
        import pandas as pd

        df = pd.DataFrame({"x": [10, 20, 30, 40, 50]}, index=[3, 1, 4, 0, 2])
        print(df.loc[1, "x"], df.iloc[1, 0])
        print(df.loc[1:0, "x"].tolist())
        print(df.iloc[1:3, 0].tolist())
        print(df.sort_index().loc[0:2, "x"].tolist())
        print(df[df["x"] > 25].index.tolist(), len(df.loc[[3, 3]]))
        """,
        hints=["`loc` uses the labels 3, 1, 4, 0, 2 in their current order, and a label slice includes both ends. `iloc` counts positions from 0."],
        why="""Label 1 is the second row, so `loc[1]` and `iloc[1]` happen to agree (20). The label slice `1:0` walks the index **in its current order** from label 1 to label 0,
        inclusive: labels 1, 4, 0, values 20, 30, 40. `iloc[1:3]` is positions 1 and 2. After `sort_index`, labels 0, 1, 2 are the first three rows, with values 40,
        20 and 50. The filter keeps rows whose value exceeds 25, reporting their labels, and `loc` with a repeated label returns the row twice."""),
    predict("Missing values in comparisons and statistics", "easy",
        code="""
        import numpy as np
        import pandas as pd

        s = pd.Series([4.0, np.nan, 10.0, np.nan])
        print(s.mean(), s.sum(), s.count(), s.size)
        print((s > 5).tolist(), (s <= 5).tolist())
        print(s.isna().mean(), s.fillna(0).mean())
        print(s.max(skipna=False), s.dropna().index.tolist())
        print(pd.Series(["a", None, "c"]).str.upper().tolist())
        """,
        hints=["Statistics skip missing values by default; comparisons with NaN are always False."],
        why="""`mean` and `sum` skip the two NaNs, so the mean is 7.0 over 2 values, while `size` still counts 4 positions; `count` counts only non-missing ones.
        Comparisons with NaN are False in **both** directions, so missing rows silently fall out of any filter. Half the values are missing; filling them with 0
        changes the mean to 3.5, which is why the fill value is a modelling decision, not a formatting one. `skipna=False` makes a statistic honest about missing
        data. String methods pass missing values through as missing."""),
    write("A data quality report", "easy", tag="ML",
        prompt="""Before training, you want one table describing every column. Write `quality_report(df)` returning a DataFrame indexed by column name with these columns,
        in this order: `dtype` (the dtype as a string), `missing` (count), `missing_pct` (percentage rounded to 1), `unique` (distinct non-missing values) and
        `example` (the first non-missing value, or `None` if the column is empty). Sort the rows by `missing_pct`, highest first, keeping the original column
        order for ties. Compute each statistic for all columns at once (no loop over rows).""",
        code="""
        import pandas as pd


        def quality_report(df):
            rows = []
            for i, row in df.iterrows():
                rows.append(row.isna().sum())
            return pd.DataFrame({"missing": rows})
        """,
        tests="""
        import numpy as np
        df = pd.DataFrame({"a": [1, 2, 2, None], "b": ["x", None, None, None], "c": [None] * 4, "d": [5, 6, 7, 8]})
        r = quality_report(df)
        assert list(r.columns) == ["dtype", "missing", "missing_pct", "unique", "example"]
        assert list(r.index) == ["c", "b", "a", "d"]
        assert r.loc["b", "missing"] == 3 and r.loc["b", "missing_pct"] == 75.0
        assert r.loc["a", "unique"] == 2 and r.loc["a", "example"] == 1.0
        assert r.loc["c", "example"] is None and r.loc["d", "dtype"] == "int64"
        """,
        hints=["`df.isna().sum()` and `df.nunique()` each return one value per column.", "`df.apply(lambda col: ...)` runs once per **column**; `col.first_valid_index()` finds the first non-missing label."],
        solution="""
        import pandas as pd


        def first_value(col):
            i = col.first_valid_index()
            return None if i is None else col[i]


        def quality_report(df):
            missing = df.isna().sum()
            report = pd.DataFrame({
                "dtype": df.dtypes.astype(str),
                "missing": missing,
                "missing_pct": (missing / len(df) * 100).round(1),
                "unique": df.nunique(),
                "example": pd.Series({c: first_value(df[c]) for c in df.columns}, dtype=object),
            })
            return report.sort_values("missing_pct", ascending=False, kind="stable")
        """,
        why="""Every statistic here is a **per-column** reduction, and pandas has one for each: `isna().sum()`, `nunique()` (which skips missing values), `dtypes`. They return
        Series indexed by column name, so building the report is just putting them side by side; the starter looped over rows, which is both slow and the wrong
        direction. `first_valid_index` handles an all-missing column by returning `None`. The `example` column is built as `object` dtype so that a Python
        `None` stays `None`. `kind="stable"` keeps the original order among equal percentages, so the report is deterministic. Run this on every new dataset:
        it is the `df.info()` you can sort, filter and save."""),
    write("Clean a complaints table with one chain", "easy", tag="Data work",
        prompt="""Write `clean(df)` for a complaints frame with columns `id`, `product`, `amount` (text) and `state`. Return a new frame where `product` is trimmed and
        lower-case, `amount` is numeric (text such as `" 1,200 "` becomes 1200.0; anything unparseable becomes NaN), `state` is upper-case with missing values
        replaced by `"UNKNOWN"`, exact duplicate rows (after cleaning) are dropped, and the index runs 0, 1, 2... Do not modify the input. Use a method chain.""",
        code="""
        import pandas as pd


        def clean(df):
            df["product"] = df["product"].str.lower()
            df["amount"] = df["amount"].astype(float)
            return df.drop_duplicates()
        """,
        tests="""
        raw = pd.DataFrame({"id": [1, 2, 2, 3], "product": [" Mortgage", "Credit card ", "credit card", "Loan"],
                            "amount": [" 1,200 ", "n/a", "n/a", "50"], "state": ["ca", None, None, "ny"]})
        before = raw.copy()
        out = clean(raw)
        assert out["product"].tolist() == ["mortgage", "credit card", "loan"]
        assert out["amount"].iloc[0] == 1200.0 and pd.isna(out["amount"].iloc[1])
        assert out["state"].tolist() == ["CA", "UNKNOWN", "NY"]
        assert out.index.tolist() == [0, 1, 2]
        assert raw.equals(before)
        """,
        hints=["`assign` with lambdas returns a new frame; `pd.to_numeric(..., errors=\"coerce\")` after removing commas and spaces.", "Drop duplicates **after** cleaning, then `reset_index(drop=True)`."],
        solution="""
        import pandas as pd


        def clean(df):
            return (
                df.assign(
                    product=lambda d: d["product"].str.strip().str.lower(),
                    amount=lambda d: pd.to_numeric(d["amount"].str.strip().str.replace(",", ""), errors="coerce"),
                    state=lambda d: d["state"].str.upper().fillna("UNKNOWN"),
                )
                .drop_duplicates()
                .reset_index(drop=True)
            )
        """,
        why="""The starter assigned into the caller's frame, so cleaning a dataset also rewrote the raw copy that other code relies on; `assign` builds a new frame
        instead. `astype(float)` raises on `"n/a"` and `"1,200"`, while stripping, removing the thousands separator and `to_numeric(errors="coerce")` keep what is
        parseable and mark the rest as NaN, which a quality report then counts. The two rows for complaint 2 differ only in case and whitespace, so they become
        duplicates only after normalising, which is why de-duplication comes last. `reset_index(drop=True)` throws away the gaps that dropping left in the index."""),
)

section("medium", "Medium",
    fix("An update that never happens", "medium", tag="Data work",
        prompt="""`flag_large` should set `priority` to `"high"` for complaints with `amount` above `limit` and return the frame. With pandas 3 the column never changes and a
        `ChainedAssignmentError` warning appears. Fix it without copying the whole frame by hand, and make sure the function returns a new frame rather than
        modifying its argument.""",
        code="""
        import pandas as pd


        def flag_large(df, limit):
            df["priority"] = "normal"
            df[df["amount"] > limit]["priority"] = "high"
            return df
        """,
        tests="""
        import warnings
        raw = pd.DataFrame({"amount": [10.0, 500.0, None, 900.0]})
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            out = flag_large(raw, 100)
        assert out["priority"].tolist() == ["normal", "high", "normal", "high"]
        assert "priority" not in raw.columns
        """,
        hints=["Under Copy-on-Write, `df[mask]` is a new object. Assign with one `loc` call.", "Start from `df.assign(priority=\"normal\")` so the input is left alone."],
        solution="""
        import pandas as pd


        def flag_large(df, limit):
            out = df.assign(priority="normal")
            out.loc[out["amount"] > limit, "priority"] = "high"
            return out
        """,
        why="""`df[mask]` returns a new DataFrame (Copy-on-Write makes every indexing result behave as a copy), and `["priority"] = "high"` then changes that temporary
        object, which is discarded. pandas 3 detects the pattern and raises the `ChainedAssignmentError` **warning**, which the test turns into an error. One
        `loc[rows, column]` call writes into the frame itself. The starter also added the column to the caller's frame; `assign` creates the new frame first, and
        Copy-on-Write keeps that cheap, because untouched columns are shared until written. The NaN amount compares as False, so it stays `"normal"`."""),
    write("Impute without leaking the test set", "medium", tag="ML",
        prompt="""Write a small class `MedianImputer` with `fit(train_df, columns)` that learns the median of each listed numeric column **from the training frame only**, and
        `transform(df)` that returns a new frame where missing values in those columns are filled with the learned medians and, for each column, a new int column
        `<col>_missing` is 1 where the value was missing and 0 otherwise. Calling `transform` before `fit` must raise `RuntimeError`.""",
        code="""
        import pandas as pd


        class MedianImputer:
            def fit(self, train_df, columns):
                self.columns = columns
                return self

            def transform(self, df):
                out = df.copy()
                for c in self.columns:
                    out[c] = out[c].fillna(out[c].median())
                return out
        """,
        tests="""
        train = pd.DataFrame({"amount": [10.0, None, 30.0, 50.0], "days": [1.0, 2.0, None, 4.0]})
        test = pd.DataFrame({"amount": [None, 1000.0, None], "days": [None, 5.0, 6.0]})
        imp = MedianImputer().fit(train, ["amount", "days"])
        out = imp.transform(test)
        assert out["amount"].tolist() == [30.0, 1000.0, 30.0]
        assert out["days"].tolist() == [2.0, 5.0, 6.0]
        assert out["amount_missing"].tolist() == [1, 0, 1] and out["days_missing"].dtype.kind == "i"
        assert test["amount"].isna().sum() == 2
        import pytest
        with pytest.raises(RuntimeError):
            MedianImputer().transform(test)
        """,
        hints=["Store `train_df[columns].median()` in `fit`.", "Build the indicator from `isna()` **before** filling, with `.astype(int)`."],
        solution="""
        import pandas as pd


        class MedianImputer:
            def __init__(self):
                self.medians_ = None

            def fit(self, train_df, columns):
                self.columns = list(columns)
                self.medians_ = train_df[self.columns].median()
                return self

            def transform(self, df):
                if self.medians_ is None:
                    raise RuntimeError("call fit() first")
                out = df.copy()
                for c in self.columns:
                    out[f"{c}_missing"] = out[c].isna().astype(int)
                out[self.columns] = out[self.columns].fillna(self.medians_)
                return out
        """,
        why="""The starter computed the median **of the frame being transformed**, so the test set was filled with the test set's own median: information from the data you
        are evaluating on leaks into its features, and the score becomes optimistic. Worse, the same row would get different values depending on what else is in
        the batch. Learning the statistics in `fit` and only applying them in `transform` is the contract scikit-learn uses for every transformer (D.6), which is
        why its `SimpleImputer` exists. The indicator columns let a model learn that "amount was missing" is a signal in itself, and they must be computed before
        filling erases it. `fillna` with a Series fills each column with its own value."""),
    choose("A row-wise apply or column arithmetic", "medium", tag="Data work",
        prompt="Both compute a fee-adjusted amount for 50,000 complaints. Which is faster?",
        setup="""import numpy as np
import pandas as pd
rng = np.random.default_rng(0)
df = pd.DataFrame({"amount": rng.uniform(0, 1000, 50_000), "fee": rng.uniform(0, 50, 50_000)})""",
        options={
            "a": "out = df.apply(lambda r: r[\"amount\"] - r[\"fee\"] if r[\"amount\"] > 100 else r[\"amount\"], axis=1)",
            "b": "out = (df[\"amount\"] - df[\"fee\"]).where(df[\"amount\"] > 100, df[\"amount\"])",
        },
        answer="b",
        hints=["`apply(axis=1)` builds a Series object for every row and calls your function 50,000 times."],
        why="""`apply` with `axis=1` is a Python loop in disguise: for each of the 50,000 rows pandas builds a Series, calls the lambda, and collects the results, so the cost is
        tens of microseconds per row. Option B does three vectorised column operations: a subtraction, a comparison, and `where`, which keeps the first value where
        the condition is True and takes the second elsewhere (`np.where` works too). The usual gap is a factor of several hundred. Reach for `apply` only for logic
        that genuinely cannot be expressed with column operations, and even then try `.map` on one column or a NumPy function first."""),
    write("Features and labels for a model", "medium", tag="ML",
        prompt="""Write `make_xy(df, label, drop=())` that returns `(X, y)` for training: `y` is the `label` column; `X` holds every other column except those in `drop`
        and except columns that are entirely missing; rows whose label is missing are removed from both. `X` must be a DataFrame and `y` a Series with the same
        index, and the input must be unchanged. Raise `KeyError` if `label` is not a column.""",
        code="""
        import pandas as pd


        def make_xy(df, label, drop=()):
            X = df.drop(columns=[label])
            y = df[label]
            return X, y
        """,
        tests="""
        df = pd.DataFrame({"id": [1, 2, 3, 4], "amount": [5.0, 6.0, None, 8.0], "notes": [None] * 4,
                           "timely": ["yes", None, "no", "yes"]})
        X, y = make_xy(df, "timely", drop=["id"])
        assert list(X.columns) == ["amount"]
        assert y.tolist() == ["yes", "no", "yes"] and X.index.equals(y.index)
        assert X.index.tolist() == [0, 2, 3]
        assert df.shape == (4, 4)
        import pytest
        with pytest.raises(KeyError):
            make_xy(df, "missing")
        """,
        hints=["`df.dropna(subset=[label])` removes unlabelled rows.", "`X.columns[X.notna().any()]` keeps columns with at least one value."],
        solution="""
        import pandas as pd


        def make_xy(df, label, drop=()):
            if label not in df.columns:
                raise KeyError(label)
            labelled = df.dropna(subset=[label])
            X = labelled.drop(columns=[label, *drop])
            X = X.loc[:, X.notna().any()]
            return X, labelled[label]
        """,
        why="""A row without a label cannot be used for supervised training, and leaving it in makes most libraries fail or, worse, treat the missing label as a class, so
        those rows go first, from both `X` and `y` at once, which keeps their indexes aligned. Identifiers such as `id` must not be features: a model can memorise
        them and look accurate on data it has seen, then fail on new ids. A column with no values carries no information. `X.notna().any()` is a boolean Series
        over columns, and `loc[:, mask]` selects those columns. pandas raises `KeyError` itself for a missing column in `df[label]`, but checking first gives a
        clearer error before any work is done."""),
    trace("Filters, assignment and the index", "medium",
        prompt="Fill in `n` and `ids` after each marked line.",
        code="""
        import pandas as pd

        df = pd.DataFrame({"id": [7, 3, 9, 3, 5], "score": [0.9, 0.4, None, 0.4, 0.7]})
        kept = df[df["score"] >= 0.5]
        n, ids = len(kept), kept.index.tolist()  # row: "filter"
        kept = df.drop_duplicates()
        n, ids = len(kept), kept["id"].tolist()  # row: "dedupe"
        kept = df.dropna().sort_values("score")
        n, ids = len(kept), kept.index.tolist()  # row: "dropna, sort"
        kept = kept.reset_index(drop=True)
        n, ids = len(kept), kept.index.tolist()  # row: "reset"
        df.loc[df["id"] == 3, "score"] = 1.0
        n, ids = int(df["score"].eq(1.0).sum()), df.loc[df["score"] > 0.8, "id"].tolist()  # row: "loc update"
        """,
        trace_vars=["n", "ids"],
        hints=["Filtering keeps the original index labels. NaN fails every comparison. `sort_values` is stable for equal scores."],
        why="""The filter keeps scores 0.9 and 0.7 (the NaN fails `>= 0.5`), at labels 0 and 4. `drop_duplicates` removes the second `(3, 0.4)` row, leaving four ids in
        their original order. `dropna` removes label 2, and sorting by score puts the two 0.4 rows first (labels 1 and 3, in their original order) then 0.7 and 0.9.
        `reset_index(drop=True)` renumbers the four rows 0 to 3. Finally, one `loc` call sets both id-3 rows to 1.0, so ids 7, 3 and 3 have scores above 0.8."""),
    write("Prompt-ready records from a frame", "medium", tag="GenAI",
        prompt="""An LLM classifier receives complaints as a list of dicts. Write `to_records(df, text_col, max_chars, fields)` returning a list with one dict per row
        that has non-empty text: `{"id": ..., "text": ..., **fields}`, where `text` is the stripped text cut to at most `max_chars` characters (if cut, end it with
        `"..."` so the total length is exactly `max_chars`), and `fields` lists other columns to include. Missing values in those fields must become `None`, not
        NaN (NaN is not valid JSON). Row order is kept.""",
        code="""
        import pandas as pd


        def to_records(df, text_col, max_chars, fields):
            return df[["id", text_col, *fields]].to_dict("records")
        """,
        tests="""
        import json
        df = pd.DataFrame({"id": [1, 2, 3, 4], "narrative": ["  Charged twice for one payment.  ", "", None, "x" * 50],
                           "product": ["card", "loan", "card", None], "amount": [20.0, None, 5.0, None]})
        recs = to_records(df, "narrative", 20, ["product", "amount"])
        assert [r["id"] for r in recs] == [1, 4]
        assert recs[0] == {"id": 1, "text": "Charged twice for...", "product": "card", "amount": 20.0}
        assert len(recs[1]["text"]) == 20 and recs[1]["text"].endswith("...")
        assert recs[1]["product"] is None and recs[1]["amount"] is None
        json.dumps(recs, allow_nan=False)
        """,
        hints=["Strip first, then keep rows where `text.str.len() > 0` (missing text gives NaN, which fails the comparison).",
               "`frame.astype(object).where(frame.notna(), None)` replaces every missing value with `None`."],
        solution="""
        import pandas as pd


        def to_records(df, text_col, max_chars, fields):
            text = df[text_col].str.strip()
            keep = df[text.str.len() > 0]
            text = text[keep.index]
            cut = text.str.len() > max_chars
            text = text.where(~cut, text.str[: max_chars - 3] + "...")
            out = keep[["id", *fields]].astype(object)
            out = out.where(out.notna(), None)
            out.insert(1, "text", text)
            return out.to_dict("records")
        """,
        why="""`to_dict("records")` turns each row into a dict, but it keeps NaN as a float, and `json.dumps` writes it as the bare word `NaN`, which is not JSON:
        many LLM APIs and parsers reject the request. Converting the fields to `object` dtype first lets `where` put a real `None` in every missing cell, which
        serialises as `null`. Empty and missing narratives carry nothing to classify, so they are dropped before spending tokens on them. Truncation is a
        character budget standing in for a token budget; cutting to `max_chars - 3` and adding the ellipsis makes the model, and a human reviewing the prompt,
        see that the text was shortened. The `allow_nan=False` in the test makes `json.dumps` refuse NaN outright."""),
)

section("hard", "Hard",
    write("Find duplicate complaints across messy text", "hard", tag="Data work",
        prompt="""The same complaint is often submitted twice with small differences. Write `dedupe(df)`: two rows are duplicates when their `customer` (case-insensitive,
        trimmed) and normalised `narrative` match, where normalising means lower-case, every run of non-alphanumeric characters replaced by one space, and the
        result stripped. Keep the **earliest** `submitted` row of each group (ties: the smaller `id`), return the kept rows sorted by `id`, and add a column
        `copies` with the size of each kept row's group. Vectorised string methods only; no Python loop over rows.""",
        code="""
        import pandas as pd


        def dedupe(df):
            return df.drop_duplicates(subset=["customer", "narrative"])
        """,
        tests="""
        df = pd.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "customer": ["Ana", "ana ", "Ben", "Ana", "Ben"],
            "narrative": ["Charged twice!!", "charged   twice", "Card blocked.", "Late fee", "card BLOCKED"],
            "submitted": pd.to_datetime(["2026-01-05", "2026-01-02", "2026-01-03", "2026-01-01", "2026-01-03"]),
        })
        out = dedupe(df)
        assert out["id"].tolist() == [2, 3, 4]
        assert out["copies"].tolist() == [2, 2, 1]
        assert list(out.columns) == ["id", "customer", "narrative", "submitted", "copies"]
        assert len(df) == 5
        """,
        hints=["`str.replace(r\"[^a-z0-9]+\", \" \", regex=True)` after `str.lower()`.",
               "Sort by `submitted` then `id`, build a key, then use `groupby(key).transform(\"size\")` for `copies` and `drop_duplicates(subset=key)` to keep the first of each group."],
        solution="""
        import pandas as pd


        def dedupe(df):
            key_customer = df["customer"].str.strip().str.lower()
            key_text = df["narrative"].str.lower().str.replace(r"[^a-z0-9]+", " ", regex=True).str.strip()
            work = df.assign(_k1=key_customer, _k2=key_text)
            work["copies"] = work.groupby(["_k1", "_k2"])["id"].transform("size")
            kept = work.sort_values(["submitted", "id"]).drop_duplicates(subset=["_k1", "_k2"])
            return kept.drop(columns=["_k1", "_k2"]).sort_values("id").reset_index(drop=True)
        """,
        why="""Exact matching misses every real duplicate here, because people retype the same complaint with different case, spacing and punctuation. Normalising
        builds a **key** that ignores those differences: lower-case, collapse every run of non-alphanumeric characters (punctuation, repeated spaces) into one
        space, and strip. `groupby(...).transform("size")` returns, for every row, the size of its group, aligned to the original rows, so it can be stored before
        anything is dropped. Sorting by `submitted` and then `id` makes "keep the first" mean "keep the earliest, then the smallest id"; `drop_duplicates` keeps the
        first row per key by default. This is the cheap, exact layer of de-duplication; near-duplicates with different wording need MinHash or embeddings
        (16.2 sketched shingles and Jaccard)."""),
    write("Shrink a frame's memory", "hard", tag="Data work",
        prompt="""Write `shrink(df, max_unique_ratio=0.5)` that returns a new frame using less memory: integer columns are downcast to the smallest integer type that holds
        their values (`pd.to_numeric(..., downcast="integer")`), float columns to `float32`, and text (`str` or `object`) columns whose number of distinct values is
        at most `max_unique_ratio` times the number of rows become `category`. Other columns are unchanged. Also write `saved(before, after)` returning the
        percentage of memory saved (with `memory_usage(deep=True)`), rounded to 1.""",
        code="""
        import pandas as pd


        def shrink(df, max_unique_ratio=0.5):
            return df.astype("category")


        def saved(before, after):
            return 0.0
        """,
        tests="""
        import numpy as np
        n = 1000
        df = pd.DataFrame({"count": np.arange(n, dtype=np.int64) % 100, "big": np.arange(n, dtype=np.int64) * 100_000, "score": np.linspace(0, 1, n),
                           "state": ["CA", "NY", "TX", "WA"] * (n // 4), "text": [f"complaint {i}" for i in range(n)]})
        out = shrink(df)
        assert out["count"].dtype == np.int8 and out["big"].dtype == np.int32
        assert out["score"].dtype == np.float32 and out["state"].dtype == "category"
        assert out["text"].dtype == df["text"].dtype
        assert (out["state"] == df["state"]).all() and np.allclose(out["score"], df["score"])
        assert saved(df, out) > 40
        assert df["count"].dtype == np.int64
        """,
        hints=["Loop over **columns** (a handful), not rows; check kinds with `pd.api.types.is_integer_dtype`, `is_float_dtype` and `is_string_dtype`.",
               "Saved percentage: `100 * (1 - after_bytes / before_bytes)`."],
        solution="""
        import pandas as pd
        from pandas.api import types as pdt


        def shrink(df, max_unique_ratio=0.5):
            out = df.copy()
            for col in out.columns:
                s = out[col]
                if pdt.is_integer_dtype(s):
                    out[col] = pd.to_numeric(s, downcast="integer")
                elif pdt.is_float_dtype(s):
                    out[col] = s.astype("float32")
                elif pdt.is_string_dtype(s) or pdt.is_object_dtype(s):
                    if s.nunique() <= max_unique_ratio * len(s):
                        out[col] = s.astype("category")
            return out


        def saved(before, after):
            b = before.memory_usage(deep=True).sum()
            a = after.memory_usage(deep=True).sum()
            return round(100 * (1 - a / b), 1)
        """,
        why="""Defaults are generous: `read_csv` gives every integer column `int64` and every float `float64`, eight bytes per value. Values from 0 to 99 fit in one byte (`int8`), values
        up to about 100 million in four (`int32`), and `downcast="integer"` picks the smallest type that holds the actual minimum and maximum. `float32` halves
        floats at the cost of precision beyond 7 digits, usually fine for features (D.1). A text column with four distinct values repeated 1,000 times is mostly
        repeated strings; as a `category` each value is stored once with one-byte codes. A column of unique strings would get **bigger** as a category (codes
        plus every value), which is why the ratio check exists. Looping over columns is fine: there are few, and each operation inside is vectorised. The input
        keeps its dtypes because the function works on a copy."""),
    predict("Strings, NA and dtypes in pandas 3", "hard",
        code="""
        import pandas as pd

        s = pd.Series(["7", "x", None, "12"])
        print(s.dtype, s.str.len().tolist())
        print(pd.to_numeric(s, errors="coerce").tolist())
        print(s.str.isdigit().tolist())
        n = pd.Series([1, None, 3], dtype="Int64")
        print(n.dtype, (n > 1).tolist(), n.sum(), n.mean())
        m = pd.Series([1, 2, 3])
        m2 = m
        m2 = m2.replace(2, 20)
        print(m.tolist(), m2.tolist())
        df = pd.DataFrame({"a": [1, 2]})
        view = df["a"]
        view.iloc[0] = 100
        print(df["a"].tolist(), view.tolist())
        """,
        hints=["The default text dtype keeps missing values as NaN. Nullable integers keep `<NA>`. Under Copy-on-Write a column you pulled out is its own object."],
        why="""Text columns get the `str` dtype; string methods return NaN for the missing value, so lengths come back as floats (`1.0, 1.0, nan, 2.0`), but a method that returns booleans,
        such as `isdigit`, reports `False` for the missing value, so it can be used directly as a mask. `to_numeric(errors="coerce")` turns `"x"` into NaN. The nullable `Int64` column prints `<NA>` and compares with three-valued logic,
        so `NA > 1` is `<NA>`; `sum` and `mean` skip it (4 and 2.0). `replace` returns a new Series, and rebinding `m2` never touched `m`. The last case is the one
        Copy-on-Write changed: in pandas 2, `df["a"]` could be a view and writing into it changed `df`; in pandas 3 the extracted column behaves as a copy, so `df` keeps
        `[1, 2]`."""),
)

section("interview", "Interview questions",
    explain("What is the difference between loc and iloc, and where do people go wrong?", "medium", tag="Interview",
        why="""`loc` selects by **label** (index values and column names) and `iloc` by **integer position**, like NumPy. Their slices differ: `df.loc["a":"c"]` includes
        `"c"`, because labels have no natural "one past the end", while `df.iloc[0:3]` excludes position 3, like Python. The common mistakes: assuming labels equal
        positions after filtering or sorting (after `df[df.x > 0]` the labels have gaps, so `loc[0]` may not exist or may be any row); using `df[0]`, which looks up
        a **column** named 0; chained indexing such as `df[mask]["col"] = v`, which under pandas 3 Copy-on-Write never writes into `df` (use `df.loc[mask, "col"] =
        v`); and forgetting that boolean masks must be aligned Series or arrays of the right length. Rule of thumb: use `loc` with masks and column names in
        application code, `iloc` for "the first n rows" or positional sampling, and `reset_index(drop=True)` when you want labels to equal positions again."""),
    explain("How do you handle missing values when preparing data for a model?", "hard", tag="Interview",
        why="""First, measure and understand them: count and fraction per column (`isna().mean()`), and ask **why** they are missing, because the mechanism decides the
        treatment: missing at random, missing because of the value itself (high incomes unreported), or structurally missing (no second applicant). Then decide
        per column. Drop rows only when the value is essential (the label) or rarely missing; drop columns that are nearly empty. Impute numeric features with the
        median (robust to outliers) or a model-based estimate, categorical ones with the mode or an explicit `"unknown"` category, and add missing-indicator
        columns because missingness is often predictive. The critical rule is **no leakage**: imputation statistics are learned on the training split only and
        applied to validation, test and production data, ideally inside a scikit-learn `Pipeline` with `SimpleImputer` so cross-validation refits them per fold
        (D.6). Some models (gradient-boosted trees such as LightGBM and XGBoost, or `HistGradientBoostingClassifier`) handle NaN natively. Finally, beware
        defaults that hide missingness: pandas statistics skip NaN, and comparisons with NaN are False, so filters silently drop those rows."""),
    explain("What changed with Copy-on-Write in pandas 3, and why does it matter?", "medium", tag="Interview",
        why="""Before pandas 3, an indexing result could be a view or a copy depending on the operation and memory layout, so modifying a subset sometimes modified the parent
        frame and sometimes did not, and `SettingWithCopyWarning` tried, unreliably, to warn about it. pandas 3 makes Copy-on-Write the only behaviour: any object
        derived from another (a column, a filtered frame, the result of `reset_index` or `rename`) **behaves as a copy**, so changing it never changes the original.
        Internally pandas still shares memory until one side is written, so operations that used to copy defensively are now often cheaper. Consequences for code:
        chained assignment `df[mask]["col"] = v` never works (pandas emits `ChainedAssignmentError`) and must be one `df.loc[mask, "col"] = v`; `inplace=True` is
        rarely useful; functions can return modified copies safely; and `to_numpy()` may return a read-only array, so call `to_numpy(copy=True)` if you need to write.
        For teams it removes a whole class of "my preprocessing changed the raw data" bugs."""),
)

recap(
    "A DataFrame is named columns, each a Series with one dtype, sharing an Index. Start with `head`, `info` and `describe`; pandas 3 reads text as the `str` dtype.",
    "`loc` is by label and includes the slice end; `iloc` is by position and excludes it. Masks combine with `&`, `|`, `~`; NaN fails every comparison.",
    "Missing values: count with `isna()`, then drop, fill, or impute with training statistics plus an indicator column. `pd.NA` uses three-valued logic.",
    "Convert with `pd.to_numeric(errors=\"coerce\")` and count the NaNs; downcast numbers and use `category` for repetitive text to save memory.",
    "Copy-on-Write: every indexing result behaves as a copy, so chained assignment never works; write `df.loc[mask, col] = v` or chain `assign` calls.",
)
