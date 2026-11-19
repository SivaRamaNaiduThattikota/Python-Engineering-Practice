from lesson import *
from diagrams import *

lesson(
    id="m17-3", num="D.3", title="pandas: groupby, merge and reshape",
    intro="Most feature engineering and most evaluation reports are a group-by, a join or a reshape. Split-apply-combine with named aggregations, "
          "`transform` for per-row group features, joins and the row explosions they cause, anti-joins, and moving between long and wide tables "
          "with `pivot_table` and `melt`.",
    desc="groupby and named aggregation, transform and filter, merge with validate and indicator, anti-joins, pivot_table, melt and concat.",
    keys="pandas groupby split apply combine agg named aggregation size count nunique transform filter rank cumcount merge join inner left right outer validate one_to_one one_to_many many_to_many indicator anti join left_anti suffixes concat pivot pivot_table melt long wide crosstab target encoding leakage evaluation report pass rate percentile",
)

term("Split-apply-combine", "The group-by pattern: split rows into groups by a key, apply a function to each group, and combine the results into one table.")
term("transform", "A group-by operation that returns one value per original row (such as the row's group mean), so the result can be added as a column.")
term("Anti-join", "A join that keeps the rows of one table that have no match in the other, like SQL's NOT EXISTS.")
term("Long and wide format", "Long: one row per observation (entity, variable, value). Wide: one row per entity with a column per variable.")

DATA = '''import pandas as pd

complaints = pd.DataFrame({
    "id": [1, 2, 3, 4, 5, 6, 7],
    "customer": ["ana", "ben", "ana", "cy", "ben", "ana", "dee"],
    "product": ["card", "loan", "card", "mortgage", "card", "loan", None],
    "amount": [20.0, 300.0, 35.0, 1200.0, 15.0, 250.0, 60.0],
    "timely": [True, False, True, True, False, True, True],
})'''


def with_data(code):
    return DATA + "\n" + dedent(code)


section("groupby", "Split, apply, combine",
    p("""`df.groupby(key)` **splits** the rows into groups that share a key, you **apply** a function to each group, and pandas **combines** the results into a new
    table with one row per group. It is SQL's `GROUP BY` and Power BI's summarise-by-a-column, with Python functions available inside. The clearest form is
    **named aggregation**: `agg(new_name=("column", "function"))`, which says exactly which output column comes from which input and which function, and
    gives the result flat, readable column names."""),
    fig(chain(["7 complaint rows", ("split by customer", "accent"), "apply: count, sum,|mean per group", ("combine: 1 row|per customer", "good")]),
        "Split-apply-combine: one input row per complaint, one output row per customer."),
    ex(with_data("""
    per_customer = complaints.groupby("customer").agg(
        complaints=("id", "size"),
        total=("amount", "sum"),
        avg=("amount", "mean"),
        products=("product", "nunique"),
        timely_rate=("timely", "mean"),
    )
    print(per_customer.round(2))
    print(complaints.groupby("product")["id"].count().to_dict())
    print(complaints.groupby("product", dropna=False)["id"].count().to_dict())
    print(complaints.groupby(["customer", "product"]).size().head(3).to_dict())
    print(complaints.groupby("customer", as_index=False)["amount"].max().head(2))
    """), "groupby.py"),
    p("""Four details. `size` counts rows in each group and `count` counts non-missing values in a column, the same difference as SQL's `COUNT(*)` and
    `COUNT(col)`. The **mean of a boolean** column is the fraction of `True`, the quickest way to get a rate. Rows whose key is **missing are dropped** from the
    groups by default (complaint 7 has no product), like a join on `NULL`; pass `dropna=False` to keep them as their own group. And the group keys become the
    **index** of the result; `as_index=False` (or `.reset_index()`) keeps them as ordinary columns, which is what you want before a merge or a plot."""),
)

section("transform", "transform and filter: group facts on every row",
    p("""`agg` shrinks each group to one row. **`transform`** returns a result **the same length as the input**, aligned to the original rows: each row gets its
    group's value. That is how you build features such as "this complaint's amount compared with the customer's average" or "the share of the customer's
    total", the pandas version of a SQL window function (`AVG(amount) OVER (PARTITION BY customer)`) or a Power BI calculated column using `ALLEXCEPT`.
    `rank`, `cumsum`, `cumcount` and `shift` on a group-by work the same way, row by row within each group. **`filter`** keeps or drops whole groups by a
    condition on the group, like `HAVING`."""),
    fig(table(["", "agg", "transform", "filter"], [
        ["rows out", "one per group", "same as input", "the rows of kept groups"],
        ["SQL", "GROUP BY", "window function OVER (PARTITION BY)", "HAVING"],
        ["typical use", "a summary table", "a feature column", "drop small groups"],
    ], hl={(0, 2)}, label="three things a group-by can return"),
        "Use `agg` for reports, `transform` for features, `filter` to drop groups."),
    ex(with_data("""
    g = complaints.groupby("customer")["amount"]
    complaints["cust_avg"] = g.transform("mean")
    complaints["share"] = (complaints["amount"] / g.transform("sum")).round(2)
    complaints["nth"] = complaints.groupby("customer").cumcount() + 1
    complaints["rank"] = g.rank(ascending=False).astype(int)
    print(complaints[["id", "customer", "amount", "cust_avg", "share", "nth", "rank"]])
    repeat = complaints.groupby("customer").filter(lambda grp: len(grp) >= 2)
    print(sorted(repeat["customer"].unique().tolist()))
    """), "transform.py"),
)

section("merge", "Joins and how they go wrong",
    p("""`pd.merge(left, right, on="key", how=...)` is SQL's join: `"inner"` keeps keys in both tables, `"left"` keeps every left row and fills missing right
    columns with NaN, `"right"` the reverse, `"outer"` keeps all. When both tables have a non-key column with the same name, the result gets `_x` and `_y`
    suffixes (choose better ones with `suffixes=`). As in SQL, if a key appears several times on **both** sides, every pair is produced: three rows times two
    rows gives six. When you expected one match per row, that silently duplicates data, inflates sums and leaks rows between train and test splits."""),
    p("""Two arguments make joins safe. **`validate="many_to_one"`** (or `"one_to_one"`, `"one_to_many"`) checks your assumption about the keys and raises
    `MergeError` if it is wrong, so a duplicated row in a lookup table fails loudly instead of doubling a revenue figure. **`indicator=True`** adds a `_merge`
    column saying `left_only`, `right_only` or `both` for every row, the quickest way to see what did not match. pandas 3 also supports **anti-joins**
    directly: `how="left_anti"` keeps the left rows with **no** match, the "complaints whose customer is not in the CRM" question."""),
    fig(table(["left rows", "right rows", "key per side", "result rows"], [
        ["3", "3", "unique, unique", "up to 3 (one_to_one)"],
        ["7", "4", "repeated, unique", "7 for a left join (many_to_one)"],
        ["3 with key k", "2 with key k", "repeated, repeated", "3 x 2 = 6 for key k"],
    ], hl={(2, 3)}, label="how many rows a join returns"),
        "Repeated keys on both sides multiply; `validate=` turns that surprise into an error."),
    ex(with_data("""
    customers = pd.DataFrame({"customer": ["ana", "ben", "cy", "eve"], "segment": ["retail", "retail", "premium", "premium"]})
    m = complaints.merge(customers, on="customer", how="left", validate="many_to_one", indicator=True)
    print(m[["id", "customer", "segment", "_merge"]].tail(3))
    print(m["_merge"].value_counts().to_dict())
    print(complaints.merge(customers, on="customer", how="left_anti")["id"].tolist())
    print(customers.merge(complaints, on="customer", how="left_anti")["customer"].tolist())
    dup = pd.concat([customers, customers.iloc[[0]]])
    print(len(complaints.merge(dup, on="customer")))
    try:
        complaints.merge(dup, on="customer", validate="many_to_one")
    except pd.errors.MergeError as e:
        print(type(e).__name__, str(e)[:45])
    """), "merge.py"),
)

section("reshape", "Long and wide: pivot_table, melt and concat",
    p("""The same data can be **long** (one row per observation: model, metric, value) or **wide** (one row per model, one column per metric). Long is what
    `groupby`, plotting libraries and databases prefer; wide is what people read and what most models need as features. **`pivot_table(index, columns,
    values, aggfunc)`** goes from long to wide, aggregating duplicates (it is Excel's pivot table and Power BI's matrix visual); `pivot` does the same but
    raises if a cell would get two values. **`melt(id_vars, value_vars)`** goes back from wide to long, Power Query's "unpivot columns".
    **`pd.concat([a, b])`** stacks frames with the same columns, like `UNION ALL`, and `ignore_index=True` renumbers the rows."""),
    fig(chain(["long: model, metric,|value rows", ("pivot_table", "accent"), "wide: one row per model,|a column per metric", ("melt", "accent2"), "long again"]),
        "`pivot_table` and `melt` are inverses: long for computing and plotting, wide for reading and modelling."),
    ex("""
    import pandas as pd

    runs = pd.DataFrame({
        "model": ["small", "small", "large", "large", "small", "large"],
        "metric": ["accuracy", "latency_ms", "accuracy", "latency_ms", "accuracy", "accuracy"],
        "value": [0.81, 120, 0.88, 410, 0.83, 0.90],
    })
    wide = runs.pivot_table(index="model", columns="metric", values="value", aggfunc="mean")
    print(wide)
    print(wide.columns.name, wide.reset_index().columns.tolist())
    long = wide.reset_index().melt(id_vars="model", var_name="metric", value_name="value")
    print(long.sort_values(["model", "metric"]).to_dict("records")[:2])
    print(pd.crosstab(runs["model"], runs["metric"]))
    both = pd.concat([runs.head(2), runs.tail(1)], ignore_index=True)
    print(both.index.tolist(), len(both))
    """, "reshape.py"),
    p("""`pivot_table` averaged the two `small` accuracy runs into 0.82, which is what you want for a report and exactly what hides problems if you expected one
    value per cell: use `pivot` there, or `aggfunc="count"` first to see the duplicates. `crosstab` is a shortcut for counting combinations. After a pivot the
    column index carries a **name** (`metric`), which is why the printed table has an extra header line; `reset_index()` and `rename_axis(columns=None)`
    flatten it before saving."""),
)

section("warmup", "Warm-up",
    predict("size, count, missing keys and as_index", "easy",
        code="""
        import pandas as pd

        df = pd.DataFrame({"k": ["a", "b", "a", None, "b", "a"], "v": [1.0, None, 3.0, 4.0, 5.0, None]})
        print(df.groupby("k").size().to_dict())
        print(df.groupby("k")["v"].count().to_dict())
        print(df.groupby("k")["v"].sum().to_dict())
        print(df.groupby("k", dropna=False).size().tolist())
        print(df.groupby("k", as_index=False)["v"].mean().columns.tolist())
        print(df.groupby("k")["v"].transform("mean").tolist())
        """,
        hints=["`size` counts rows, `count` counts non-missing values, and rows with a missing key are left out unless `dropna=False`."],
        why="""Group `a` has three rows, `b` two, and the row with a missing key belongs to no group, so `size` is `{a: 3, b: 2}`. `count` ignores the NaN values: `a` has 2 and
        `b` has 1. `sum` skips NaN, giving 4.0 and 5.0. With `dropna=False` the missing key becomes a third group of size 1. `as_index=False` keeps `k` as a column.
        `transform` returns one value per original row: group means for `a` (2.0) and `b` (5.0), and NaN for the row with no group."""),
    predict("How many rows does the join return", "easy",
        code="""
        import pandas as pd

        orders = pd.DataFrame({"cust": ["x", "x", "y", "z"], "amt": [10, 20, 30, 40]})
        people = pd.DataFrame({"cust": ["x", "y", "y", "w"], "name": ["Xia", "Yan", "Yan B", "Wu"]})
        print(len(orders.merge(people, on="cust")))
        print(len(orders.merge(people, on="cust", how="left")))
        print(len(orders.merge(people, on="cust", how="outer")))
        print(orders.merge(people, on="cust", how="left")["amt"].sum())
        print(orders.merge(people, on="cust", how="left_anti")["cust"].tolist())
        print(orders.merge(people, on="cust", how="outer", indicator=True)["_merge"].value_counts().to_dict())
        """,
        hints=["`x` appears twice on the left and once on the right; `y` once on the left and twice on the right. Count matches key by key."],
        why="""Key `x`: 2 left rows times 1 right row is 2; key `y`: 1 times 2 is 2; so the inner join has 4 rows. The left join adds `z` with no match: 5. The outer join adds
        `w` from the right too: 6. The sum of `amt` after the left join is 130, not the true total of 100, because order `y` (30) appears twice: the classic
        inflated-revenue bug. Only `z` has no match on the right. The indicator counts 4 `both`, 1 `left_only` and 1 `right_only`."""),
    write("Per-customer features", "easy", tag="ML",
        prompt="""A churn model needs one row per customer. Write `customer_features(df)` for a complaints frame with `customer`, `amount`, `timely` (bool) and `product`,
        returning a frame **with `customer` as an ordinary column**, sorted by customer, with columns `n_complaints`, `total_amount`, `max_amount`, `late_rate` (the
        fraction of complaints that were **not** timely, rounded to 2) and `n_products` (distinct non-missing products). Use one `groupby(...).agg(...)` with named
        aggregations.""",
        code="""
        import pandas as pd


        def customer_features(df):
            return df.groupby("customer").sum()
        """,
        tests="""
        df = pd.DataFrame({"customer": ["ana", "ben", "ana", "ana", "ben"], "amount": [10.0, 5.0, 30.0, None, 5.0],
                           "timely": [True, False, False, True, False], "product": ["card", "loan", "card", None, "card"]})
        f = customer_features(df)
        assert list(f.columns) == ["customer", "n_complaints", "total_amount", "max_amount", "late_rate", "n_products"]
        assert f["customer"].tolist() == ["ana", "ben"]
        assert f["n_complaints"].tolist() == [3, 2] and f["total_amount"].tolist() == [40.0, 10.0]
        assert f["late_rate"].tolist() == [0.33, 1.0] and f["n_products"].tolist() == [1, 2]
        assert f["max_amount"].tolist() == [30.0, 5.0]
        """,
        hints=["Make a `late` column first with `~df[\"timely\"]` (via `assign`), then average it.", "`size` counts rows even when `amount` is missing; `as_index=False` keeps the key as a column."],
        solution="""
        import pandas as pd


        def customer_features(df):
            out = (
                df.assign(late=~df["timely"])
                  .groupby("customer", as_index=False)
                  .agg(n_complaints=("customer", "size"), total_amount=("amount", "sum"), max_amount=("amount", "max"),
                       late_rate=("late", "mean"), n_products=("product", "nunique"))
            )
            out["late_rate"] = out["late_rate"].round(2)
            return out.sort_values("customer").reset_index(drop=True)
        """,
        why="""`sum` over every column adds booleans as counts and concatenates strings, which is meaningless as features. Named aggregations state each feature's source and
        function. `size` counts complaints, including the one with no amount, while `sum` and `max` skip the missing amount. The mean of a boolean is a rate, so
        building `late` as the negation of `timely` and averaging it gives the late rate. `nunique` ignores missing products. This is the usual shape of feature
        engineering for a per-entity model: many event rows aggregated into one row per entity, joined later to the label table."""),
    write("The most common product in each state", "easy", tag="Data work",
        prompt="""Write `top_product(df)` returning a frame with columns `state`, `product` and `n`: for each state, the product with the most complaints and its count.
        Break ties by the alphabetically first product. Rows with a missing state or product are ignored. Sort by state.""",
        code="""
        import pandas as pd


        def top_product(df):
            return df.groupby("state")["product"].max()
        """,
        tests="""
        df = pd.DataFrame({"state": ["CA", "CA", "CA", "NY", "NY", "TX", None, "NY"],
                           "product": ["card", "loan", "card", "loan", "card", "mortgage", "card", None]})
        out = top_product(df)
        assert list(out.columns) == ["state", "product", "n"]
        assert out.values.tolist() == [["CA", "card", 2], ["NY", "card", 1], ["TX", "mortgage", 1]]
        """,
        hints=["Count each (state, product) pair with `groupby([...]).size()`, then sort by state, count descending and product ascending.", "`drop_duplicates(\"state\")` keeps the first row per state."],
        solution="""
        import pandas as pd


        def top_product(df):
            counts = df.groupby(["state", "product"]).size().reset_index(name="n")
            ranked = counts.sort_values(["state", "n", "product"], ascending=[True, False, True])
            return ranked.drop_duplicates("state").reset_index(drop=True)
        """,
        why="""`max` of a text column returns the alphabetically last product, not the most frequent. Counting pairs first gives a long table of `(state, product, n)`;
        sorting by count descending within each state, with the product name as the tie-breaker, puts the winner first, and `drop_duplicates("state")` keeps that
        first row. Grouping by both keys already drops rows where either is missing. NY has one `loan` and one `card`, a tie that the alphabetical rule settles.
        The same sort-then-keep-first pattern answers every "top 1 per group" question; `nlargest` within groups or `idxmax` are alternatives."""),
)

section("medium", "Medium",
    fix("A join that doubles the revenue", "medium", tag="Data work",
        prompt="""`add_segment` attaches each complaint's customer segment, and the dashboard's total refund amount doubled overnight: the CRM export now contains a customer
        twice. Fix the function so it uses one row per customer (keep the **last** row for a duplicated customer, the most recent export line), and so that it
        raises `pandas.errors.MergeError` if a future change brings back a many-to-many join. Every complaint must be kept, even without a segment.""",
        code="""
        import pandas as pd


        def add_segment(complaints, crm):
            return complaints.merge(crm, on="customer")
        """,
        tests="""
        complaints = pd.DataFrame({"id": [1, 2, 3, 4], "customer": ["ana", "ben", "ana", "cy"], "refund": [10.0, 20.0, 30.0, 40.0]})
        crm = pd.DataFrame({"customer": ["ana", "ben", "ana"], "segment": ["retail", "premium", "premium"]})
        out = add_segment(complaints, crm)
        assert len(out) == 4 and out["refund"].sum() == 100.0
        assert out.sort_values("id")["segment"].tolist()[:3] == ["premium", "premium", "premium"]
        assert pd.isna(out.loc[out["id"] == 4, "segment"]).all()
        assert "validate" in __source__
        """,
        hints=["`crm.drop_duplicates(\"customer\", keep=\"last\")`.", "`how=\"left\", validate=\"many_to_one\"`."],
        solution="""
        import pandas as pd


        def add_segment(complaints, crm):
            lookup = crm.drop_duplicates("customer", keep="last")
            return complaints.merge(lookup, on="customer", how="left", validate="many_to_one")
        """,
        why="""Customer `ana` appears twice in the CRM, so each of her two complaints matched twice and her refunds were counted twice; the inner join also dropped `cy`,
        who has no CRM row. De-duplicating the lookup table states the business rule (the last export line wins), a left join keeps every complaint, and
        `validate="many_to_one"` records the assumption that the right side has unique keys, so the next duplicated export fails the job instead of corrupting a
        dashboard. Asserting that a join does not change the row count of the left table is another cheap safety check."""),
    write("Standardise amounts within each product", "medium", tag="ML",
        prompt="""A refund of 300 is large for a credit card and small for a mortgage. Write `add_group_z(df, value, by)` returning a copy of `df` with a new column
        `f"{value}_z"`: the z-score of each row's value **within its group**, `(x - group mean) / group std` (pandas' default std, `ddof=1`), rounded to 3. Groups
        with a single row or zero spread get 0.0 instead of NaN. Use `transform`, not a merge or a loop over groups.""",
        code="""
        import pandas as pd


        def add_group_z(df, value, by):
            out = df.copy()
            out[f"{value}_z"] = (out[value] - out[value].mean()) / out[value].std()
            return out
        """,
        tests="""
        df = pd.DataFrame({"product": ["card", "card", "card", "mortgage", "mortgage", "loan"], "amount": [10.0, 20.0, 30.0, 1000.0, 3000.0, 50.0]})
        out = add_group_z(df, "amount", "product")
        assert out["amount_z"].tolist() == [-1.0, 0.0, 1.0, -0.707, 0.707, 0.0]
        same = pd.DataFrame({"g": ["a", "a"], "x": [5.0, 5.0]})
        assert add_group_z(same, "x", "g")["x_z"].tolist() == [0.0, 0.0]
        assert "amount_z" not in df.columns
        assert "transform" in __source__
        """,
        hints=["`g = df.groupby(by)[value]`, then `g.transform(\"mean\")` and `g.transform(\"std\")` are aligned to the rows.", "Replace NaN or 0 std before dividing, then `fillna(0.0)`."],
        solution="""
        import pandas as pd


        def add_group_z(df, value, by):
            out = df.copy()
            g = out.groupby(by)[value]
            std = g.transform("std")
            z = (out[value] - g.transform("mean")) / std.where(std > 0)
            out[f"{value}_z"] = z.fillna(0.0).round(3)
            return out
        """,
        why="""The starter standardised against the whole column, so every mortgage looks extreme and every card looks tiny: the feature mostly encodes the product, which the
        model already has. `transform("mean")` and `transform("std")` give each row its own group's statistics, aligned to the original rows, so the arithmetic is
        ordinary column math. A single-row group has an undefined sample std (NaN), and a constant group has std 0; `where(std > 0)` turns both into NaN for the
        division, and `fillna(0.0)` reports "average for its group". Group statistics computed on the full dataset leak information like the imputer in D.2, so
        in a real pipeline they are learned on the training split."""),
    write("New complaints since the last export", "medium", tag="Data work",
        prompt="""Write `new_since(current, previous)` returning the rows of `current` whose `id` does not appear in `previous`, using a join (pandas 3's `how="left_anti"`),
        keeping `current`'s columns and order. Then write `changed(current, previous, cols)` returning the ids present in both whose values differ in any of
        `cols`, sorted. Treat two missing values as equal.""",
        code="""
        import pandas as pd


        def new_since(current, previous):
            return current[current["id"] != previous["id"]]


        def changed(current, previous, cols):
            return []
        """,
        tests="""
        prev = pd.DataFrame({"id": [1, 2, 3], "status": ["open", "open", "closed"], "amount": [10.0, None, 5.0]})
        cur = pd.DataFrame({"id": [1, 2, 3, 4, 5], "status": ["closed", "open", "closed", "open", "open"], "amount": [10.0, None, 7.0, 1.0, 2.0]})
        assert new_since(cur, prev)["id"].tolist() == [4, 5]
        assert list(new_since(cur, prev).columns) == ["id", "status", "amount"]
        assert changed(cur, prev, ["status", "amount"]) == [1, 3]
        assert changed(cur, prev, ["status"]) == [1]
        """,
        hints=["`current.merge(previous[[\"id\"]], on=\"id\", how=\"left_anti\")`.", "Inner-join on `id` with `suffixes=(\"\", \"_old\")`, then compare each column pair; `a.eq(b) | (a.isna() & b.isna())` treats NaN pairs as equal."],
        solution="""
        import pandas as pd


        def new_since(current, previous):
            return current.merge(previous[["id"]], on="id", how="left_anti")


        def changed(current, previous, cols):
            both = current.merge(previous, on="id", suffixes=("", "_old"))
            diff = pd.Series(False, index=both.index)
            for c in cols:
                a, b = both[c], both[f"{c}_old"]
                same = a.eq(b) | (a.isna() & b.isna())
                diff |= ~same
            return sorted(both.loc[diff, "id"].tolist())
        """,
        why="""Comparing `current["id"] != previous["id"]` aligns the two Series by **index**, not by value, so it compares row 0 with row 0 and fails when lengths differ.
        The anti-join asks the real question: which current ids have no partner in the previous export. Only `id` is taken from `previous`, so no other columns
        come along. For changes, an inner join puts the old and new values side by side, and a plain `!=` would report the unchanged missing amount of complaint
        2 as a change, because NaN never equals NaN; the explicit "both missing" check fixes that. Looping over a few column names is fine; each comparison is
        vectorised. This is the core of incremental loads and change data capture."""),
    choose("A group-by or a loop over the groups", "medium", tag="Data work",
        prompt="Both compute the mean amount per customer for 100,000 rows and 2,000 customers. Which is faster?",
        setup="""import numpy as np
import pandas as pd
rng = np.random.default_rng(1)
df = pd.DataFrame({"customer": rng.integers(0, 2_000, 100_000), "amount": rng.uniform(0, 500, 100_000)})""",
        options={
            "a": "means = {c: df.loc[df[\"customer\"] == c, \"amount\"].mean() for c in df[\"customer\"].unique()}",
            "b": "means = df.groupby(\"customer\")[\"amount\"].mean()",
        },
        answer="b",
        hints=["Option A scans all 100,000 rows once for every customer."],
        why="""Option A builds a boolean mask over all 100,000 rows for each of the 2,000 customers: 200 million comparisons plus 2,000 filtered copies. `groupby` sorts or
        hashes the keys once and then computes every group's mean in a single pass in compiled code. The gap is two to three orders of magnitude, and it is the
        same mistake as running one SQL query per customer instead of one `GROUP BY`."""),
    trace("Shapes through pivot and melt", "medium",
        prompt="Fill in `shape` and `cols` after each marked line.",
        code="""
        import pandas as pd

        runs = pd.DataFrame({"prompt": ["v1", "v1", "v2", "v2", "v2", "v3"],
                             "judge": ["gpt", "claude", "gpt", "claude", "gpt", "gpt"],
                             "score": [0.7, 0.8, 0.9, 0.85, 0.95, 0.6]})
        t = runs.pivot_table(index="prompt", columns="judge", values="score", aggfunc="mean")
        shape, cols = t.shape, t.columns.tolist()  # row: "pivot"
        t = t.reset_index()
        shape, cols = t.shape, t.columns.tolist()  # row: "reset"
        t = t.melt(id_vars="prompt", var_name="judge", value_name="score")
        shape, cols = t.shape, t.columns.tolist()  # row: "melt"
        t = t.dropna()
        shape, cols = t.shape, sorted(t["prompt"].unique().tolist())  # row: "dropna"
        """,
        trace_vars=["shape", "cols"],
        hints=["The pivot has one row per prompt and one column per judge; `v3` has no `claude` score, so that cell is NaN."],
        why="""Three prompts and two judges give a 3 by 2 table whose columns are the judges, sorted. `reset_index` moves `prompt` back into a column: 3 by 3. `melt` turns the
        two judge columns into rows: 3 prompts times 2 judges is 6 rows of `prompt, judge, score`. The missing `(v3, claude)` cell becomes a NaN row in the long
        table, and `dropna` removes it, leaving 5 rows that still cover all three prompts. Note that the pivot averaged the two `(v2, gpt)` runs into 0.925."""),
    write("An evaluation report per prompt version", "medium", tag="GenAI",
        prompt="""Each row of `results` is one test case run against an LLM: `prompt_version`, `case_id`, `passed` (bool), `latency_ms` and `tokens`. Write `eval_report(results)`
        returning one row per prompt version, sorted by version, with columns `prompt_version`, `cases`, `pass_rate` (rounded to 3), `p50_ms` and `p95_ms` (latency
        percentiles via `quantile`, rounded to 1), and `tokens_per_pass` (total tokens divided by the number of passing cases, rounded to 1; NaN if none passed).""",
        code="""
        import pandas as pd


        def eval_report(results):
            return results.groupby("prompt_version").mean()
        """,
        tests="""
        r = pd.DataFrame({"prompt_version": ["v1"] * 4 + ["v2"] * 3,
                          "case_id": [1, 2, 3, 4, 1, 2, 3],
                          "passed": [True, False, True, True, False, False, False],
                          "latency_ms": [100.0, 200.0, 300.0, 400.0, 50.0, 60.0, 70.0],
                          "tokens": [500, 700, 600, 800, 300, 300, 300]})
        rep = eval_report(r)
        assert list(rep.columns) == ["prompt_version", "cases", "pass_rate", "p50_ms", "p95_ms", "tokens_per_pass"]
        assert rep["cases"].tolist() == [4, 3] and rep["pass_rate"].tolist() == [0.75, 0.0]
        assert rep["p50_ms"].tolist() == [250.0, 60.0] and rep["p95_ms"].tolist() == [385.0, 69.0]
        assert rep["tokens_per_pass"].iloc[0] == 866.7 and pd.isna(rep["tokens_per_pass"].iloc[1])
        """,
        hints=["Named aggregation accepts a function: `p95_ms=(\"latency_ms\", lambda s: s.quantile(0.95))`.", "Aggregate `passes=(\"passed\", \"sum\")` and `tokens=(\"tokens\", \"sum\")`, then divide, using `where(passes > 0)`."],
        solution="""
        import pandas as pd


        def eval_report(results):
            rep = results.groupby("prompt_version", as_index=False).agg(
                cases=("case_id", "size"),
                pass_rate=("passed", "mean"),
                p50_ms=("latency_ms", "median"),
                p95_ms=("latency_ms", lambda s: s.quantile(0.95)),
                tokens=("tokens", "sum"),
                passes=("passed", "sum"),
            )
            rep["tokens_per_pass"] = (rep["tokens"] / rep["passes"].where(rep["passes"] > 0)).round(1)
            rep[["pass_rate"]] = rep[["pass_rate"]].round(3)
            rep[["p50_ms", "p95_ms"]] = rep[["p50_ms", "p95_ms"]].round(1)
            return rep.drop(columns=["tokens", "passes"]).sort_values("prompt_version").reset_index(drop=True)
        """,
        why="""An average latency hides the slow tail that users feel, so evaluation reports give percentiles: `quantile(0.95)` interpolates between the sorted values (385
        lies three quarters of the way from 300 to 400). The mean of `passed` is the pass rate. Tokens per **passing** case is a cost-of-quality metric: a prompt
        that passes more cases with fewer tokens wins on both axes, and a version with no passes has no meaningful value, so the division is masked rather than
        allowed to produce infinity. Helper aggregates such as `tokens` and `passes` are computed in the same pass and dropped at the end."""),
)

section("hard", "Hard",
    write("Target encoding without leakage", "hard", tag="ML",
        prompt="""Target encoding replaces a category (such as `company`) with the average label of training rows in that category. Write `TargetEncoder(smoothing=10)` with
        `fit(X, y, col)` and `transform(X)`. The learned value for a category with `n` training rows and label mean `m` is the **smoothed** mean
        `(n * m + smoothing * prior) / (n + smoothing)`, where `prior` is the overall training label mean, so rare categories are pulled towards the prior.
        `transform` returns a new Series named `f"{col}_te"` aligned to `X`'s index, rounded to 4, using the prior for unseen or missing categories. Use group-by
        and a mapping, no row loops.""",
        code="""
        import pandas as pd


        class TargetEncoder:
            def __init__(self, smoothing=10):
                self.smoothing = smoothing

            def fit(self, X, y, col):
                self.col = col
                return self

            def transform(self, X):
                return X[self.col].map(X.groupby(self.col).size())
        """,
        tests="""
        Xtr = pd.DataFrame({"company": ["a", "a", "a", "a", "b", "c", "c"]})
        ytr = pd.Series([1, 1, 1, 0, 0, 1, 0])
        enc = TargetEncoder(smoothing=2).fit(Xtr, ytr, "company")
        Xte = pd.DataFrame({"company": ["a", "b", "zzz", None]}, index=[10, 11, 12, 13])
        out = enc.transform(Xte)
        assert out.name == "company_te" and out.index.tolist() == [10, 11, 12, 13]
        prior = 4 / 7
        assert out.loc[10] == round((4 * 0.75 + 2 * prior) / 6, 4)
        assert out.loc[11] == round((1 * 0.0 + 2 * prior) / 3, 4)
        assert out.loc[12] == round(prior, 4) and out.loc[13] == round(prior, 4)
        assert enc.transform(Xtr).loc[5] == round((2 * 0.5 + 2 * prior) / 4, 4)
        """,
        hints=["Group the **training labels** by the training column: `y.groupby(X[col]).agg([\"count\", \"mean\"])`.", "`X[col].map(table).fillna(prior)` handles unseen and missing categories."],
        solution="""
        import pandas as pd


        class TargetEncoder:
            def __init__(self, smoothing=10):
                self.smoothing = smoothing

            def fit(self, X, y, col):
                self.col = col
                self.prior_ = float(y.mean())
                stats = y.groupby(X[col]).agg(["count", "mean"])
                n, m = stats["count"], stats["mean"]
                self.table_ = (n * m + self.smoothing * self.prior_) / (n + self.smoothing)
                return self

            def transform(self, X):
                out = X[self.col].map(self.table_).astype(float).fillna(self.prior_).round(4)
                return out.rename(f"{self.col}_te")
        """,
        why="""A category's raw label mean is a powerful feature and a dangerous one. Computed on the rows being scored, it contains each row's own label, so the model sees the
        answer (leakage); computed for a category with one training row, it is either 0 or 1, pure noise that the model trusts completely. Learning the table in
        `fit` from training labels only fixes the first problem; smoothing fixes the second: with `n` rows, the estimate moves from the prior towards the
        category mean as evidence grows (`b`, with one row of label 0, gets 0.381 rather than 0.0). `y.groupby(X[col])` groups the labels by the aligned
        category values. Unseen categories and missing values get the prior, the honest "no information" answer. In practice the training rows themselves are
        encoded out of fold (K-fold), so even the training features never include their own label; scikit-learn's `TargetEncoder` does that automatically."""),
    write("A win-rate table for model comparisons", "hard", tag="GenAI",
        prompt="""A pairwise evaluation asks a judge which of two answers is better. Each row of `votes` has `model_a`, `model_b` and `winner` (`"a"`, `"b"` or `"tie"`).
        Write `win_rates(votes)` returning a square DataFrame indexed and columned by every model (sorted), where cell `[x, y]` is the fraction of x-versus-y
        comparisons that x won, counting a tie as half a win, rounded to 3; the diagonal and pairs that never met are NaN. A comparison counts for the pair
        whichever side each model was on. Use concat, groupby and pivot, no loops over rows.""",
        code="""
        import pandas as pd


        def win_rates(votes):
            return pd.crosstab(votes["model_a"], votes["model_b"])
        """,
        tests="""
        import numpy as np
        votes = pd.DataFrame({"model_a": ["m1", "m1", "m2", "m3", "m1"],
                              "model_b": ["m2", "m2", "m1", "m1", "m3"],
                              "winner": ["a", "tie", "a", "b", "b"]})
        w = win_rates(votes)
        assert w.index.tolist() == ["m1", "m2", "m3"] and w.columns.tolist() == ["m1", "m2", "m3"]
        assert w.loc["m1", "m2"] == 0.5 and w.loc["m2", "m1"] == 0.5
        assert w.loc["m1", "m3"] == 0.5 and w.loc["m3", "m1"] == 0.5
        assert np.isnan(w.loc["m2", "m3"]) and np.isnan(w.loc["m1", "m1"])
        assert ((w + w.T).stack().dropna().round(3) == 1.0).all()
        """,
        hints=["Build a long table with one row per (model, opponent, score) for side a, and another for side b; `concat` them.",
               "Score: 1 for a win, 0.5 for a tie, 0 for a loss; then `pivot_table(index=\"model\", columns=\"opponent\", values=\"score\", aggfunc=\"mean\")` and `reindex` both axes with every model."],
        solution="""
        import pandas as pd


        def win_rates(votes):
            score_a = votes["winner"].map({"a": 1.0, "tie": 0.5, "b": 0.0})
            side_a = pd.DataFrame({"model": votes["model_a"], "opponent": votes["model_b"], "score": score_a})
            side_b = pd.DataFrame({"model": votes["model_b"], "opponent": votes["model_a"], "score": 1.0 - score_a})
            long = pd.concat([side_a, side_b], ignore_index=True)
            models = sorted(set(long["model"]))
            table = long.pivot_table(index="model", columns="opponent", values="score", aggfunc="mean")
            table = table.reindex(index=models, columns=models)
            return table.round(3).rename_axis(index=None, columns=None)
        """,
        why="""The raw votes are in a "match" format where each model can appear on either side, which a crosstab treats as different things. Turning every vote into two rows,
        one from each model's point of view (`model`, `opponent`, `score`), gives a long table where a model's results are in one column no matter which side it
        was on, and the scores of each pair add up to 1. A mean per `(model, opponent)` is the win rate, and `pivot_table` spreads it into a matrix. `reindex` with the
        full sorted list adds rows and columns for pairs that never met, as NaN. m1 against m2: a win for m1, a tie, and a win for m2 averages to 0.5. The last test
        checks the symmetry that any correct table must have. Leaderboards such as Chatbot Arena start from exactly this table before fitting Elo or Bradley-Terry
        ratings."""),
    predict("Group-by details that change results", "hard",
        code="""
        import pandas as pd

        df = pd.DataFrame({"team": ["b", "a", "b", "a", "c"], "pts": [3, 1, 2, 5, 4]})
        print(df.groupby("team").sum().index.tolist(), df.groupby("team", sort=False).sum().index.tolist())
        print(df.groupby("team")["pts"].agg(["min", "max"]).loc["a"].tolist())
        print(df.groupby("team")["pts"].apply(lambda s: s.tolist()).to_dict())
        print(df.groupby("team")["pts"].shift(1).tolist())
        cat = df.assign(team=pd.Categorical(df["team"], categories=["a", "b", "c", "d"]))
        print(cat.groupby("team", observed=False)["pts"].sum().to_dict())
        print(cat.groupby("team", observed=True).size().tolist())
        print(df.groupby(df["pts"] > 2)["team"].apply(list).to_dict())
        """,
        hints=["Groups are sorted by key unless `sort=False`. `shift` works inside each group. A categorical key can produce groups for unused categories."],
        why="""By default the group keys are sorted (`a, b, c`); `sort=False` keeps them in order of first appearance (`b, a, c`). Team `a` has points 1 and 5. `apply` with
        a function receives each group's values in their original order. `shift(1)` within groups moves each value down by one inside its own team, so the first
        row of every team is NaN, the basis of lag features in D.4. A categorical key with `observed=False` creates a group for **every** category, including the
        unused `d`, whose sum is 0; `observed=True` (the pandas 3 default) gives only the three groups that occur. Grouping by a boolean Series splits the rows into
        `False` and `True`."""),
)

section("interview", "Interview questions",
    explain("What is the difference between agg, transform and apply on a group-by?", "medium", tag="Interview",
        why="""All three run per group, but they return different shapes. `agg` (with names such as `"sum"` or named aggregations) reduces each group to one row: a
        summary table, SQL's `GROUP BY`. `transform` returns a result with the **same index as the input**, broadcasting each group's value back to its rows (or
        returning a same-length result such as a rank or cumulative sum): SQL's window functions with `PARTITION BY`, used to add feature columns such as "amount
        relative to the customer mean" without a merge. `apply` is the general escape hatch: it passes each group as a DataFrame to any Python function and stitches
        whatever comes back together, so it is flexible but slower (Python per group) and its output shape depends on the function. Prefer built-in aggregation
        names (they run in optimised code), use `transform` for row-level features, `filter` to keep or drop whole groups, and `apply` only when nothing else
        fits. And remember the defaults: missing keys are dropped (`dropna=True`), keys become the index (`as_index=True`), and keys are sorted."""),
    explain("A join produced more rows than you expected. What happened, and how do you prevent it?", "medium", tag="Interview",
        why="""A join outputs one row for every matching pair of rows, so if a key is duplicated on the side you assumed was unique, each left row matches several right rows
        and the result grows: three orders for a customer with two CRM rows become six. It silently inflates sums and counts, can duplicate examples across train
        and test splits, and the row count often goes unnoticed. To find it: compare `len(result)` with `len(left)`, check `right[key].duplicated().any()`, and use
        `indicator=True` to see matches. To prevent it: de-duplicate the lookup table with an explicit rule (keep the latest, or aggregate), and pass
        `validate="many_to_one"` (or `"one_to_one"`) so pandas raises `MergeError` when the assumption breaks; for left joins assert that the row count is
        unchanged. Also check key types and formatting (an `int` key will not match a `str` one, and `" ana"` will not match `"ana"`), and remember missing keys:
        in pandas, unlike SQL, NaN keys match each other in a merge, which can create surprising pairs."""),
    explain("When would you keep data in long format, and when in wide format?", "medium", tag="Interview",
        why="""Long format has one row per observation, with columns such as `entity, variable, value` (or `date, metric, value`). It is the natural shape for storing and
        computing: new metrics or dates are new rows, not schema changes, group-bys and filters are simple, and plotting libraries such as seaborn and plotly
        expect it. Databases and event logs are long. Wide format has one row per entity and one column per variable; it is easier for people to read and compare,
        it is what spreadsheets and reports show, and it is what most ML models require: a feature matrix with one row per example and one column per feature.
        Typical workflow: keep raw data long, compute aggregates with `groupby`, then `pivot_table` into wide features or report tables, and `melt` back when you
        need to plot or append. Watch for the reshaping traps: `pivot` raises on duplicate entries, `pivot_table` silently aggregates them, and missing
        combinations become NaN cells that need a decision."""),
)

recap(
    "`groupby(...).agg(name=(\"col\", \"func\"))` is GROUP BY with clear names; `size` counts rows, `count` non-missing values; missing keys are dropped unless `dropna=False`.",
    "`transform` returns one value per original row (window functions); `filter` keeps whole groups (HAVING); `cumcount`, `rank` and `shift` work within groups.",
    "Joins multiply repeated keys; de-duplicate lookups, pass `validate=`, use `indicator=True`, and `how=\"left_anti\"` for rows with no match.",
    "`pivot_table` goes long to wide and aggregates duplicates; `melt` goes back; `concat` stacks frames like UNION ALL.",
    "Group statistics used as features (z-scores, target encoding) must be learned on training data only, with smoothing for rare categories.",
)
