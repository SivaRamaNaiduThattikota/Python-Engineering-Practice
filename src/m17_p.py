from lesson import *
from diagrams import *

lesson(
    id="m17-p", num="D.P", title="Module D practice set and mini project",
    intro="Mixed problems across NumPy, pandas, matplotlib and scikit-learn, the way real data work mixes them: reshaping and resampling, leakage in "
          "group features, near-duplicate embeddings, calibration, drift and error analysis. Then a mini project that uses all of it: a complaint "
          "escalation classifier, from a raw CSV to a time-based evaluation, an explained model and a two-panel report figure.",
    desc="Mixed problems from the whole module, then one end-to-end classifier from raw CSV to evaluated model and report.",
    keys="practice mixed review project end to end classifier csv cleaning time split tfidf column transformer pipeline baseline metrics confusion matrix calibration reliability diagram drift psi population stability error analysis near duplicate embeddings cosine pivot resample leakage",
)

section("how", "How to use this page",
    fig(stage_map(17, "a complaint classifier, end to end"), "Module D at a glance: NumPy, pandas, matplotlib and scikit-learn, building up to one end-to-end classifier."),
    p("""Each problem names the libraries it needs but not the exact function, so start by saying the shape of the data at each step: what is a row, what are the
    columns, which dtype, and what the result should look like. Then pick the tool: NumPy for whole-array arithmetic (D.1), pandas for cleaning, joins,
    group-bys, time and text (D.2 to D.4), matplotlib to look at the result (D.5), and scikit-learn for anything learned from data, inside a pipeline (D.6)."""),
    p("""Two questions apply to every ML problem here: **could this leak** (is anything computed from data the model would not have at prediction time?) and **what is
    the baseline** (what would the simplest answer score?). The mini project asks both, at the scale of a real first model."""),
    fig(flowchart({
        "csv": ("start", 0, 0, "raw CSV"),
        "clean": ("step", 0, 1, "clean with pandas:|types, text, duplicates"),
        "split": ("accent", 0, 2, "time-based split"),
        "pipe": ("accent2", 1, 2, "pipeline: TF-IDF, impute,|scale, one-hot, model"),
        "eval": ("step", 1, 1, "metrics vs a baseline"),
        "report": ("end", 1, 0, "figure and top words"),
    }, [("csv", "clean"), ("clean", "split"), ("split", "pipe"), ("pipe", "eval"), ("eval", "report")],
        cell=(270, 84), label="the mini project, step by step"),
        "The mini project: every step is one lesson of this module."),
)

section("set", "Practice set",
    predict("NumPy and pandas together", "easy",
        code="""
        import numpy as np
        import pandas as pd

        df = pd.DataFrame({"a": [1, 2, 3], "b": [0.5, None, 1.5]})
        arr = df.to_numpy()
        print(arr.dtype, arr.shape, np.isnan(arr).sum())
        print(df["a"].to_numpy().dtype == np.int64, (df["a"] * 2).tolist())
        print(np.mean(df["b"]), np.nanmean(df["b"].to_numpy()), df["b"].mean())
        X = df.fillna(0).to_numpy()
        print((X - X.mean(axis=0)).round(2).tolist()[0])
        print(df.sum(axis=1).tolist(), df.values.sum())
        """,
        hints=["A DataFrame with an int and a float column becomes one float array. NumPy functions applied to a Series follow pandas' missing-value rules."],
        why="""`to_numpy` must find one dtype for both columns, so the ints become floats and the missing value is `nan`: one NaN in a `(3, 2)` array. pandas keeps the
        int column as `int64`. `np.mean(series)` dispatches to pandas' own `mean`, which skips NaN (1.0), as does `nanmean` on the array; on a plain NumPy array,
        `np.mean` would return `nan`. Filling with 0 and centring column by column gives the first row's deviations. Row sums skip NaN in pandas (`2.0` for the
        second row), but the NumPy array's `sum` includes the NaN and returns `nan`."""),
    write("Weekly complaint counts by product", "medium", tag="Data work",
        prompt="""Write `weekly_by_product(df)` for complaints with `submitted` (timestamps) and `product`. Return a wide DataFrame indexed by week (weeks ending on Sunday, as
        `resample("W")` labels them) with one column per product (sorted), holding the number of complaints, with 0 for weeks without any, covering every week
        from the first to the last complaint. Column names must be plain strings and the column index unnamed.""",
        code="""
        import pandas as pd


        def weekly_by_product(df):
            return df.groupby("product").size()
        """,
        tests="""
        df = pd.DataFrame({"submitted": pd.to_datetime(["2026-01-01 10:00", "2026-01-02 09:00", "2026-01-03 11:00", "2026-01-14 08:00", "2026-01-15 12:00"]),
                           "product": ["card", "loan", "card", "card", "mortgage"]})
        w = weekly_by_product(df)
        assert w.columns.tolist() == ["card", "loan", "mortgage"] and w.columns.name is None
        assert [d.strftime("%m-%d") for d in w.index] == ["01-04", "01-11", "01-18"]
        assert w.values.tolist() == [[2, 1, 0], [0, 0, 0], [1, 0, 1]]
        """,
        hints=["Group by product **and** a weekly `pd.Grouper(key=\"submitted\", freq=\"W\")`, count with `size`, then `unstack(\"product\", fill_value=0)`.",
               "`asfreq(\"W\", fill_value=0)` adds the empty weeks between the first and last; `rename_axis(columns=None)` removes the column name."],
        solution="""
        import pandas as pd


        def weekly_by_product(df):
            counts = df.groupby([pd.Grouper(key="submitted", freq="W"), "product"]).size()
            wide = counts.unstack("product", fill_value=0).sort_index(axis=1)
            wide = wide.asfreq("W", fill_value=0)
            return wide.rename_axis(index=None, columns=None).astype(int)
        """,
        why="""This combines D.3 and D.4: a group-by on two keys, one of them a time bin (`pd.Grouper` is `resample` inside a group-by), then `unstack` to go from long
        `(week, product)` counts to a wide table, filling missing combinations with 0. Weeks with no complaints at all are missing from the group-by result, so
        `asfreq("W")` reinstates them; skipping that step makes a chart or a forecasting model treat the third week as following the first directly. Removing the
        axis names gives plain columns for saving or plotting, and `wide.plot()` would now draw one line per product (D.5)."""),
    fix("A customer feature that leaks the label", "medium", tag="ML",
        prompt="""`add_customer_rate` adds each customer's historical escalation rate as a feature. It is computed on the whole dataset before splitting, so every row's
        own label is included in its feature, and the validation score is far too good. Rewrite it as `add_customer_rate(train, test)` that returns `(train_out,
        test_out)`: test rows get the rate learned from **train** (the global train rate for unknown customers), and train rows get a **leave-one-out** rate, the
        customer's rate over their **other** training rows (the global train rate if they have none). Round to 3.""",
        code="""
        import pandas as pd


        def add_customer_rate(df):
            out = df.copy()
            out["cust_rate"] = out.groupby("customer")["escalated"].transform("mean").round(3)
            return out
        """,
        tests="""
        train = pd.DataFrame({"customer": ["a", "a", "a", "b", "c", "c"], "escalated": [1, 1, 0, 1, 0, 0]})
        test = pd.DataFrame({"customer": ["a", "c", "z"], "escalated": [1, 1, 0]})
        tr, te = add_customer_rate(train, test)
        assert tr["cust_rate"].tolist() == [0.5, 0.5, 1.0, 0.5, 0.0, 0.0]
        assert te["cust_rate"].tolist() == [0.667, 0.0, 0.5]
        assert "cust_rate" not in train.columns and len(te) == 3
        """,
        hints=["Leave-one-out: `(group sum - own label) / (group count - 1)`, with `transform(\"sum\")` and `transform(\"count\")`.",
               "Rows whose customer has only one training row divide by zero; replace those with the global train mean."],
        solution="""
        import pandas as pd


        def add_customer_rate(train, test):
            prior = train["escalated"].mean()
            g = train.groupby("customer")["escalated"]
            total, count = g.transform("sum"), g.transform("count")
            loo = (total - train["escalated"]) / (count - 1).where(count > 1)
            tr = train.assign(cust_rate=loo.fillna(prior).round(3))
            rates = g.mean()
            te = test.assign(cust_rate=test["customer"].map(rates).fillna(prior).round(3))
            return tr, te
        """,
        why="""A group mean that includes the row's own label is a disguised copy of the label: customer `b` has one row, so the "rate" is exactly that row's answer. The
        model learns to trust it, scores brilliantly in validation, and degrades in production, where the current complaint's outcome is not yet known. Test rows
        must only see training statistics (D.2's imputer rule). Training rows need the same honesty, which leave-one-out provides: customer `a`'s first complaint
        sees the other two (one escalated of two, 0.5), and its third sees two escalations (1.0). Customers with a single row, and unseen customers, fall back to the
        global rate. This is the same idea as out-of-fold target encoding in D.3, with folds of size one."""),
    write("Near-duplicate embeddings", "medium", tag="GenAI",
        prompt="""Before indexing documents for RAG, near-duplicates should be removed. Write `near_duplicates(E, ids, threshold=0.95)` returning a sorted list of `(id_a, id_b,
        similarity)` for every pair with cosine similarity at or above `threshold`, where `id_a` comes before `id_b` in `ids`, similarity rounded to 3. Compute all
        similarities with one matrix product and select the upper triangle with NumPy (no Python double loop). Then write `keep(ids, pairs)` returning the ids to
        keep: drop the later id of every pair.""",
        code="""
        import numpy as np


        def near_duplicates(E, ids, threshold=0.95):
            out = []
            for i in range(len(ids)):
                for j in range(len(ids)):
                    if E[i] @ E[j] >= threshold:
                        out.append((ids[i], ids[j], float(E[i] @ E[j])))
            return out


        def keep(ids, pairs):
            return ids
        """,
        tests="""
        E = np.array([[1.0, 0.0, 0.0], [0.99, 0.1, 0.0], [0.0, 1.0, 0.0], [0.0, 2.0, 0.05], [0.7, 0.7, 0.0]])
        ids = ["d1", "d2", "d3", "d4", "d5"]
        pairs = near_duplicates(E, ids)
        assert pairs == [("d1", "d2", 0.995), ("d3", "d4", 1.0)]
        assert keep(ids, pairs) == ["d1", "d3", "d5"]
        assert near_duplicates(E, ids, threshold=0.7)[0] == ("d1", "d2", 0.995) and len(near_duplicates(E, ids, threshold=0.7)) == 6
        assert "triu" in __source__ and "for j in" not in __source__
        """,
        hints=["Normalise the rows, `S = En @ En.T`, then `i, j = np.where(np.triu(S >= threshold, k=1))` gives each pair once, without the diagonal."],
        solution="""
        import numpy as np


        def near_duplicates(E, ids, threshold=0.95):
            E = np.asarray(E, dtype=float)
            En = E / np.maximum(np.linalg.norm(E, axis=1, keepdims=True), 1e-12)
            S = En @ En.T
            i, j = np.where(np.triu(S >= threshold, k=1))
            return sorted((ids[a], ids[b], round(float(S[a, b]), 3)) for a, b in zip(i, j))


        def keep(ids, pairs):
            drop = {b for _, b, _ in pairs}
            return [x for x in ids if x not in drop]
        """,
        why="""The starter compared raw dot products (so the long vector `d4` looked unlike its twin `d3`), compared every document with itself (similarity 1 on the
        diagonal), and listed each pair twice. Normalising first makes the dot product a cosine (D.1); one matrix product gives all `n * n` similarities;
        `np.triu(..., k=1)` keeps only pairs above the diagonal, so `i < j` and each pair appears once. This is quadratic in memory, fine for thousands of documents;
        for millions, the same idea runs inside an approximate nearest-neighbour index or with MinHash. Dropping the later document of each pair keeps the earliest
        version, a deterministic rule."""),
    write("Is the model calibrated", "hard", tag="ML",
        prompt="""A model's probabilities are **calibrated** if, among cases scored around 0.8, about 80% are positive. Write `calibration_table(y_true, proba, bins=5)` returning a
        DataFrame with one row per probability bin of equal width on [0, 1] that contains predictions (`pd.cut` with `include_lowest=True`), columns `bin` (the
        interval as a string), `n`, `mean_pred` and `frac_pos` (rounded to 3). Then write `plot_calibration(table)` drawing `mean_pred` against `frac_pos` with
        markers, a dashed diagonal from (0, 0) to (1, 1) for perfect calibration, axis labels `"mean predicted probability"` and `"fraction positive"`, both axes from
        0 to 1, and return the Axes. Finally, write `ece(table)`, the expected calibration error: the `n`-weighted mean of `|mean_pred - frac_pos|`, rounded to 3.""",
        code="""
        import pandas as pd
        import matplotlib.pyplot as plt


        def calibration_table(y_true, proba, bins=5):
            return pd.DataFrame()


        def plot_calibration(table):
            fig, ax = plt.subplots()
            return ax


        def ece(table):
            return 0.0
        """,
        tests="""
        import numpy as np
        y = np.array([0, 0, 1, 0, 1, 1, 1, 0, 1, 1])
        p = np.array([0.05, 0.15, 0.3, 0.35, 0.5, 0.55, 0.7, 0.75, 0.9, 0.95])
        t = calibration_table(y, p, bins=5)
        assert list(t.columns) == ["bin", "n", "mean_pred", "frac_pos"] and t["n"].tolist() == [2, 2, 2, 2, 2]
        assert t["mean_pred"].tolist() == [0.1, 0.325, 0.525, 0.725, 0.925] and t["frac_pos"].tolist() == [0.0, 0.5, 1.0, 0.5, 1.0]
        assert ece(t) == round(float(np.mean([0.1, 0.175, 0.475, 0.225, 0.075])), 3)
        ax = plot_calibration(t)
        assert ax.get_xlim() == (0, 1) and ax.get_ylim() == (0, 1)
        assert ax.lines[0].get_xdata().tolist() == t["mean_pred"].tolist()
        assert any(l.get_linestyle() == "--" for l in ax.lines) and ax.get_xlabel() == "mean predicted probability"
        assert len(calibration_table(y, np.full(10, 0.5), bins=5)) == 1
        """,
        hints=["`edges = np.linspace(0, 1, bins + 1)`; `pd.cut(proba, edges, include_lowest=True)` assigns each score to a bin.",
               "Group by the bin with `observed=True` (only bins that occur), aggregate `n`, `mean_pred`, `frac_pos`, then turn the bin into a string with `astype(str)`."],
        solution="""
        import numpy as np
        import pandas as pd
        import matplotlib.pyplot as plt


        def calibration_table(y_true, proba, bins=5):
            df = pd.DataFrame({"y": np.asarray(y_true), "p": np.asarray(proba, dtype=float)})
            df["bin"] = pd.cut(df["p"], np.linspace(0, 1, bins + 1), include_lowest=True)
            t = df.groupby("bin", observed=True).agg(n=("y", "size"), mean_pred=("p", "mean"), frac_pos=("y", "mean")).reset_index()
            t["bin"] = t["bin"].astype(str)
            t[["mean_pred", "frac_pos"]] = t[["mean_pred", "frac_pos"]].round(3)
            return t


        def plot_calibration(table):
            fig, ax = plt.subplots(figsize=(3.6, 3.4))
            ax.plot(table["mean_pred"], table["frac_pos"], marker="o", label="model")
            ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="perfect")
            ax.set(xlabel="mean predicted probability", ylabel="fraction positive", xlim=(0, 1), ylim=(0, 1))
            ax.legend()
            return ax


        def ece(table):
            gap = (table["mean_pred"] - table["frac_pos"]).abs()
            return round(float((gap * table["n"]).sum() / table["n"].sum()), 3)
        """,
        why="""Ranking metrics such as ROC AUC ignore whether the probabilities mean what they say, but any decision that uses the number itself (expected cost, a "70%
        likely" message to an agent, combining scores) needs calibration. `pd.cut` with fixed edges assigns each score to a bin, the group-by gives the average
        prediction and the observed rate per bin, and the reliability diagram plots one against the other: points below the diagonal mean the model is
        over-confident. Grouping with `observed=True` skips empty bins, as the last test checks. The expected calibration error summarises the gaps weighted by
        how many predictions fall in each bin. scikit-learn's `calibration_curve` and `CalibratedClassifierCV` compute and fix this; LLM confidence scores are
        notoriously uncalibrated, which is why they are checked the same way."""),
    write("Has the input data drifted", "medium", tag="ML",
        prompt="""Write `psi(reference, current)` computing the **population stability index** between two categorical Series: for every category in either, take its share
        in each (adding `eps=1e-4` to every share before the logarithm), and sum `(cur - ref) * ln(cur / ref)`; round to 3. Then write `drift_report(train_df,
        new_df, cols)` returning a DataFrame indexed by column with `psi` and `status`: `"stable"` below 0.1, `"watch"` from 0.1 to below 0.25, `"drift"` at 0.25 or
        more, sorted by `psi` descending.""",
        code="""
        import numpy as np
        import pandas as pd


        def psi(reference, current):
            return 0.0


        def drift_report(train_df, new_df, cols):
            return pd.DataFrame()
        """,
        tests="""
        ref = pd.Series(["card"] * 50 + ["loan"] * 30 + ["mortgage"] * 20)
        same = pd.Series(["card"] * 5 + ["loan"] * 3 + ["mortgage"] * 2)
        shifted = pd.Series(["card"] * 20 + ["loan"] * 20 + ["mortgage"] * 40 + ["crypto"] * 20)
        assert psi(ref, same) == 0.0
        expected = sum((c - r) * np.log(c / r) for r, c in [(0.5001, 0.2001), (0.3001, 0.2001), (0.2001, 0.4001), (0.0001, 0.2001)])
        assert psi(ref, shifted) == round(expected, 3)
        train = pd.DataFrame({"product": ref, "channel": ["web"] * 60 + ["phone"] * 40})
        new = pd.DataFrame({"product": shifted, "channel": ["web"] * 58 + ["phone"] * 42})
        rep = drift_report(train, new, ["channel", "product"])
        assert rep.index.tolist() == ["product", "channel"] and rep["status"].tolist() == ["drift", "stable"]
        """,
        hints=["`ref.value_counts(normalize=True)` gives shares; `reindex` both on the union of categories with `fill_value=0`, then add `eps`.",
               "`pd.cut(psi_values, [-inf, 0.1, 0.25, inf], right=False, labels=[...])` or plain `np.select` gives the status."],
        solution="""
        import numpy as np
        import pandas as pd


        def psi(reference, current, eps=1e-4):
            r = reference.value_counts(normalize=True)
            c = current.value_counts(normalize=True)
            cats = r.index.union(c.index)
            r = r.reindex(cats, fill_value=0) + eps
            c = c.reindex(cats, fill_value=0) + eps
            return round(float(((c - r) * np.log(c / r)).sum()), 3)


        def drift_report(train_df, new_df, cols):
            values = pd.Series({col: psi(train_df[col], new_df[col]) for col in cols})
            status = np.select([values < 0.1, values < 0.25], ["stable", "watch"], default="drift")
            return pd.DataFrame({"psi": values, "status": status}).sort_values("psi", ascending=False)
        """,
        why="""A model is trained on one distribution and served on another; when inputs shift, its accuracy can fall long before labels arrive to measure it, so input
        drift is the first thing production monitoring checks. PSI compares the share of each category: each term is positive whenever shares differ, and it grows
        quickly for categories that appear from nowhere, such as `crypto`, which is why the small `eps` matters (without it, a share of zero would make the logarithm
        infinite). Aligning both distributions on the union of categories is the same unseen-category problem as D.4's one-hot encoder. The 0.1 and 0.25 cut-offs are
        industry conventions from credit scoring; numeric columns are handled the same way after binning them with the training quantiles."""),
    predict("Encoders and their output", "easy",
        code="""
        import pandas as pd
        from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder

        train = pd.DataFrame({"product": ["card", "loan", "card"], "size": ["S", "L", "M"]})
        oh = OneHotEncoder(handle_unknown="ignore", sparse_output=False).fit(train[["product"]])
        print(oh.categories_[0].tolist(), oh.get_feature_names_out().tolist())
        print(oh.transform(pd.DataFrame({"product": ["loan", "crypto"]})).tolist())
        ordc = OrdinalEncoder(categories=[["S", "M", "L"]]).fit(train[["size"]])
        print(ordc.transform(train[["size"]]).ravel().tolist())
        print(OrdinalEncoder().fit(train[["size"]]).categories_[0].tolist())
        """,
        hints=["Categories are sorted unless you give them. An unknown category with `handle_unknown=\"ignore\"` becomes all zeros."],
        why="""`OneHotEncoder` learns the sorted categories and names its outputs `product_card` and `product_loan`. `loan` becomes `[0, 1]`, and the unseen `crypto` becomes
        `[0, 0]` instead of an error. An `OrdinalEncoder` with explicit categories maps S, L, M to 0, 2, 1, the business order; without them it sorts the strings, giving
        L, M, S, an order with no meaning, which is why ordinal encodings should always state their categories."""),
    write("Where does the model fail", "medium", tag="ML",
        prompt="""Write `error_analysis(df, by, min_n=5)` for predictions with columns `y_true`, `y_pred` and a segment column `by`. Return a DataFrame indexed by segment with
        `n`, `accuracy` and `errors` (count of wrong predictions), only for segments with at least `min_n` rows, sorted by `accuracy` ascending (worst first; ties by
        larger `n` first), and a final row named `"ALL"` with the overall numbers. Round accuracy to 3.""",
        code="""
        import pandas as pd


        def error_analysis(df, by, min_n=5):
            return df.groupby(by).mean()
        """,
        tests="""
        df = pd.DataFrame({"product": ["card"] * 6 + ["loan"] * 5 + ["auto"] * 2 + ["mortgage"] * 5,
                           "y_true": [1, 0, 1, 0, 1, 0] + [1, 1, 0, 0, 1] + [1, 0] + [0, 0, 0, 1, 1],
                           "y_pred": [1, 0, 1, 0, 0, 0] + [0, 1, 1, 0, 1] + [0, 1] + [0, 0, 0, 1, 0]})
        r = error_analysis(df, "product")
        assert r.index.tolist() == ["loan", "mortgage", "card", "ALL"]
        assert r.loc["loan", "accuracy"] == 0.6 and r.loc["loan", "errors"] == 2
        assert r.loc["card", "accuracy"] == 0.833 and r.loc["mortgage", "n"] == 5
        assert r.loc["ALL", "n"] == 18 and r.loc["ALL", "errors"] == 6 and r.loc["ALL", "accuracy"] == round(12 / 18, 3)
        """,
        hints=["`df.assign(correct=df.y_true == df.y_pred)`, then a named aggregation per segment.", "The `ALL` row uses every row, including small segments; build it separately and `pd.concat` it at the end."],
        solution="""
        import pandas as pd


        def error_analysis(df, by, min_n=5):
            d = df.assign(correct=(df["y_true"] == df["y_pred"]).astype(int))
            seg = d.groupby(by).agg(n=("correct", "size"), correct=("correct", "sum"))
            seg = seg[seg["n"] >= min_n]
            total = pd.DataFrame({"n": [len(d)], "correct": [d["correct"].sum()]}, index=["ALL"])
            out = pd.concat([seg.sort_index(), total])
            out["accuracy"] = (out["correct"] / out["n"]).round(3)
            out["errors"] = out["n"] - out["correct"]
            body = out.drop(index="ALL").sort_values(["accuracy", "n"], ascending=[True, False], kind="stable")
            return pd.concat([body, out.loc[["ALL"]]])[["n", "accuracy", "errors"]]
        """,
        why="""An overall accuracy of 0.667 hides that loans are at 0.6 while mortgages reach 0.8 and cards 0.833; error analysis by segment tells you where to look next (more data for loans,
        a feature that separates loan cases, or a different threshold). Tiny segments are dropped from the ranking because their accuracy is mostly noise (two auto
        loans), but they still count in the overall row, so the totals reconcile with the full evaluation. Sorting worst first with size as the tie-breaker puts the
        biggest problem at the top. The same table, with `y_true` and `y_pred` from an LLM judge, is how GenAI teams find the prompt's weak categories."""),
    explain("Walk me through how you would build a first model for a new tabular or text dataset.", "medium", tag="Interview",
        why="""Start with the question and the decision: what is predicted, when, for whom, and what does each kind of error cost; that defines the label, the metric and the
        split. Then look at the data before modelling: row meaning, dtypes, missing values, duplicates, class balance and time range (`info`, a quality report,
        histograms, a few raw examples), and check for label leakage (columns created after the outcome). Define the split to match production, by time or by
        entity, keep a test set aside, and set up cross-validation. Build a baseline (majority class, or a simple rule), then a simple, strong model inside one
        pipeline: imputation, scaling and one-hot for tabular columns, TF-IDF for text, logistic regression or gradient boosting. Evaluate with the chosen metric
        against the baseline, look at the confusion matrix, the calibration and errors by segment, and inspect the model (coefficients, important features) for
        nonsense. Only then iterate on features, models and thresholds, each change judged by cross-validation; finally score the test set once, document the
        results, and plan monitoring (input drift, prediction rates, delayed labels)."""),
    explain("Once a model is in production, what do you monitor, and why?", "medium", tag="Interview",
        why="""Model quality decays silently, because the world changes and nothing crashes. Monitor at several levels. **Service health**: latency, error rates and
        throughput, like any API. **Inputs**: schema and type checks, missing-value rates, ranges, and distribution drift per feature (PSI or KS tests against
        training data), plus the rate of unseen categories; these move first and need no labels. **Outputs**: the distribution of scores and the share of each
        predicted class; a sudden jump in "urgent" predictions is either a real event or a broken feature. **Quality**: once labels arrive (often days later),
        precision, recall and calibration over time and per segment, compared with the offline evaluation. For LLM features add cost per request, token counts,
        refusal and format-error rates, and a regular sampled human or LLM-judge review. Each metric needs a threshold and an owner, and the response playbook
        includes rolling back, retraining on recent data, or adjusting the threshold. Logging inputs and predictions with model versions makes all of this
        possible."""),
)

section("project", "Mini project: a complaint escalation classifier",
    p("""A consumer-finance company wants to flag complaints that are likely to be **escalated**, so they reach a senior agent on day one. You have a CSV export with
    `id`, `submitted`, `product`, `narrative`, `amount` and the label `escalated`. Build the whole first version with this module's tools: clean the raw table,
    split by time, train a pipeline on text, numbers and categories, compare it with a baseline, explain it, and draw a report figure."""),
    write("Build the escalation classifier", "hard", key="escalation-classifier", tag="Project",
        prompt="""Implement `run_project(csv_text, test_frac=0.25)` returning a dict.

        - **Load and clean (D.2, D.4):** read the CSV with pandas; `product` stripped and lower-cased; `amount` numeric (unparseable or empty becomes NaN);
          `submitted` parsed with the format `"%Y-%m-%d %H:%M"`; in `narrative`, every redaction word of two or more `X` replaced by `[X]`; rows with a repeated `id`
          dropped, keeping the first.
        - **Split by time (D.4):** sort by `submitted`; the latest `ceil(test_frac * n)` rows are the test set, the rest the training set.
        - **Model (D.6):** a `Pipeline` with a `ColumnTransformer` named `"prep"` that has three parts: `"text"`, a `TfidfVectorizer(ngram_range=(1, 2))` on `narrative`;
          `"num"`, median imputation and scaling of `amount`; `"cat"`, `OneHotEncoder(handle_unknown="ignore")` on `product`; followed by
          `LogisticRegression(max_iter=1000, class_weight="balanced")` named `"clf"`. Fit on the training set only.
        - **Evaluate:** on the test set, `accuracy`, `precision`, `recall` and `f1` for class 1, and `baseline_accuracy` from a `DummyClassifier(strategy="most_frequent")`
          fitted on the training labels; all rounded to 3, in a dict under `"metrics"`.
        - **Explain:** `"top_words"`, the 5 text features with the largest positive coefficients, without the `text__` prefix.
        - **Report (D.5):** `"figure"`, a figure with two Axes: a confusion-matrix heatmap of the test set with the counts written in the cells, titled
          `"confusion matrix"`, and a horizontal bar chart of recall per product on the test set, titled `"recall by product"`.
        - Also return `"model"` (the fitted pipeline), `"n_train"`, `"n_test"` and `"split_time"` (the first test timestamp).""",
        code="""
        import math, re
        import numpy as np
        import pandas as pd
        import matplotlib.pyplot as plt


        def run_project(csv_text, test_frac=0.25):
            pass
        """,
        tests="""
        import io, math
        import numpy as np
        import pandas as pd
        rng = np.random.default_rng(11)
        bad = ["fraud on my account", "unauthorized charge", "stolen card used", "identity theft reported"]
        ok = ["question about a fee", "statement was late", "address change request", "payment date question", "interest rate question"]
        start = pd.Timestamp("2026-01-01 08:00")
        rows = []
        for i in range(240):
            esc = bool(rng.random() < 0.3)
            pool = bad if esc else ok
            if rng.random() < 0.08:
                pool = ok if esc else bad
            text = f"Customer reports {pool[int(rng.integers(len(pool)))]} XXXX XXXX"
            prod = [" Credit card", "credit card", "Mortgage", "Checking "][int(rng.integers(4))]
            amount = "" if rng.random() < 0.1 else f"{rng.lognormal(5, 1):.2f}"
            when = (start + pd.Timedelta(hours=7 * i)).strftime("%Y-%m-%d %H:%M")
            rows.append(f"{1000 + i},{when},{prod},{text},{amount},{int(esc)}")
        rows.insert(50, rows[10])
        csv = "id,submitted,product,narrative,amount,escalated\\n" + "\\n".join(rows)
        r = run_project(csv)
        assert r["n_train"] == 180 and r["n_test"] == 60
        assert r["split_time"] == start + pd.Timedelta(hours=7 * 180)
        m = r["metrics"]
        assert set(m) == {"accuracy", "precision", "recall", "f1", "baseline_accuracy"}
        assert m["f1"] > 0.7 and m["accuracy"] > m["baseline_accuracy"]
        assert any(w in r["top_words"] for w in ["fraud", "unauthorized", "stolen", "theft"]) and len(r["top_words"]) == 5
        assert all(not w.startswith("text__") for w in r["top_words"])
        model = r["model"]
        new = pd.DataFrame({"narrative": ["Customer reports fraud on my account [X]", "Customer reports question about a fee [X]"],
                            "amount": [np.nan, 50.0], "product": ["crypto", "mortgage"]})
        assert model.predict(new).tolist() == [1, 0]
        assert set(model.named_steps["prep"].named_transformers_) >= {"text", "num", "cat"}
        fig = r["figure"]
        titles = [a.get_title() for a in fig.axes]
        assert "confusion matrix" in titles and "recall by product" in titles
        cm_ax = fig.axes[titles.index("confusion matrix")]
        assert len(cm_ax.images) == 1 and sum(int(t.get_text()) for t in cm_ax.texts) == 60
        bar_ax = fig.axes[titles.index("recall by product")]
        assert sorted(t.get_text() for t in bar_ax.get_yticklabels()) == ["checking", "credit card", "mortgage"]
        """,
        hints=["Pass the text column to the ColumnTransformer as a **string** (`\"narrative\"`), not a list: `TfidfVectorizer` expects a 1-D sequence of documents.",
               "Feature names from `prep.get_feature_names_out()` line up with `clf.coef_[0]`; keep those starting with `text__`.",
               "Recall per product: group the test rows with `y_true == 1` by product and average `y_pred == 1`."],
        solution="""
        import io, math, re
        import numpy as np
        import pandas as pd
        import matplotlib.pyplot as plt
        from sklearn.compose import ColumnTransformer
        from sklearn.dummy import DummyClassifier
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.impute import SimpleImputer
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import OneHotEncoder, StandardScaler

        FEATURES = ["narrative", "amount", "product"]


        def load(csv_text):
            df = pd.read_csv(io.StringIO(csv_text), dtype={"amount": "str"})
            return (df.assign(
                        product=lambda d: d["product"].str.strip().str.lower(),
                        amount=lambda d: pd.to_numeric(d["amount"], errors="coerce"),
                        submitted=lambda d: pd.to_datetime(d["submitted"], format="%Y-%m-%d %H:%M"),
                        narrative=lambda d: d["narrative"].fillna("").str.replace(r"\\bX{2,}\\b", "[X]", regex=True))
                      .drop_duplicates("id", keep="first"))


        def build_model():
            num = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())])
            prep = ColumnTransformer([
                ("text", TfidfVectorizer(ngram_range=(1, 2)), "narrative"),
                ("num", num, ["amount"]),
                ("cat", OneHotEncoder(handle_unknown="ignore"), ["product"]),
            ])
            return Pipeline([("prep", prep), ("clf", LogisticRegression(max_iter=1000, class_weight="balanced"))])


        def report_figure(y_true, y_pred, products):
            C = confusion_matrix(y_true, y_pred, labels=[0, 1])
            fig, (a, b) = plt.subplots(1, 2, figsize=(8, 3.2))
            a.imshow(C, cmap="Blues")
            for i in range(2):
                for j in range(2):
                    a.text(j, i, str(C[i, j]), ha="center", va="center", color="white" if C[i, j] > C.max() / 2 else "black")
            a.set_xticks([0, 1], labels=["normal", "escalated"])
            a.set_yticks([0, 1], labels=["normal", "escalated"])
            a.set(title="confusion matrix", xlabel="predicted", ylabel="true")
            pos = pd.DataFrame({"product": products, "hit": np.asarray(y_pred) == 1})[np.asarray(y_true) == 1]
            recall = pos.groupby("product")["hit"].mean().sort_values()
            b.barh(recall.index, recall.values)
            b.set(title="recall by product", xlim=(0, 1), xlabel="recall")
            fig.tight_layout()
            return fig


        def run_project(csv_text, test_frac=0.25):
            df = load(csv_text).sort_values("submitted", kind="stable").reset_index(drop=True)
            n_test = math.ceil(test_frac * len(df))
            train, test = df.iloc[: len(df) - n_test], df.iloc[len(df) - n_test:]
            model = build_model().fit(train[FEATURES], train["escalated"])
            pred = model.predict(test[FEATURES])
            y = test["escalated"].to_numpy()
            base = DummyClassifier(strategy="most_frequent").fit(train[FEATURES], train["escalated"]).predict(test[FEATURES])
            r3 = lambda v: round(float(v), 3)
            metrics = {"accuracy": r3(accuracy_score(y, pred)), "precision": r3(precision_score(y, pred, zero_division=0)),
                       "recall": r3(recall_score(y, pred, zero_division=0)), "f1": r3(f1_score(y, pred, zero_division=0)),
                       "baseline_accuracy": r3(accuracy_score(y, base))}
            names = model.named_steps["prep"].get_feature_names_out()
            coef = model.named_steps["clf"].coef_[0]
            text_idx = [i for i, n in enumerate(names) if n.startswith("text__")]
            top = sorted(text_idx, key=lambda i: -coef[i])[:5]
            return {"model": model, "metrics": metrics, "top_words": [names[i][len("text__"):] for i in top],
                    "figure": report_figure(y, pred, test["product"].to_numpy()),
                    "n_train": len(train), "n_test": len(test), "split_time": test["submitted"].iloc[0]}
        """,
        why="""Every step is one lesson, and the order matters as much as the steps. Cleaning comes first and is applied identically to all rows (stripping and lower-casing
        merges `" Credit card"` and `"credit card"` into one category; the duplicated export row is removed before it can land in both splits). The split is by
        time, so the evaluation asks the production question: trained on earlier complaints, how well does it flag later ones? Everything learned (the TF-IDF
        vocabulary, the median amount, the product categories, the model weights) sits inside one pipeline fitted on the training rows only, so the test set never
        influences preprocessing, and the fitted object accepts raw columns, including an unseen product and a missing amount. The baseline gives the metrics their
        meaning: about 70% of complaints are not escalated, so accuracy alone says little, while F1 for the escalated class shows real skill. The top words are a
        sanity check that the model learned the intended signal (fraud, unauthorized, stolen) rather than an artefact such as the redaction marker. The report figure
        is what you would show a stakeholder: where the errors are, and whether any product is badly served.

        From here, the next steps are the ones in the interview answers above: cross-validated tuning, a threshold chosen from the precision-recall curve,
        calibration, error analysis by product, and monitoring for drift once it is live."""),
)

recap(
    "Say the shape of the data at every step: what a row is, which columns and dtypes, and what the result should look like.",
    "NumPy for whole-array maths, pandas for cleaning, joins, group-bys, time and text, matplotlib to look, scikit-learn pipelines for anything learned.",
    "Ask of every feature and split: could this leak? Group statistics need out-of-fold or leave-one-out values; splits follow time or entities.",
    "Always compare with a baseline, then check calibration, errors by segment and the model's top features before trusting a score.",
    "Production adds monitoring: input drift (PSI), output rates and delayed-label quality, with thresholds and owners.",
)
