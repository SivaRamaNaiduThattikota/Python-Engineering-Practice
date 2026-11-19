from lesson import *
from diagrams import *

lesson(
    id="m17-4", num="D.4", title="pandas: time series, text and categoricals",
    intro="Real ML data has timestamps, free text and categories. Parsing dates, resampling to a regular calendar, rolling windows and lag features "
          "that do not peek into the future, time-based splits, vectorised text cleaning and regex extraction, chunking text for retrieval, and the "
          "`category` dtype with encodings that survive new data.",
    desc="Dates, resampling, rolling and lag features without leakage, time-based splits, the .str accessor, regex, chunking, categoricals and one-hot encoding.",
    keys="pandas datetime to_datetime format mixed errors coerce dt accessor dayofweek timedelta time zone utc tz_localize tz_convert resample asfreq date_range rolling expanding ewm shift lag feature leakage time-based split str accessor regex extract contains replace split explode chunking category dtype codes ordered categorical get_dummies one-hot unseen categories reindex sessionize",
)

term("DatetimeIndex", "An index made of timestamps; it enables date slicing such as `ts[\"2026-01\"]` and calendar operations such as `resample`.")
term("Resampling", "Changing the frequency of a time series, such as turning individual events into daily counts, by grouping on calendar bins.")
term("Lag feature", "A feature built from earlier values of a series, such as yesterday's count; it must only use data available at prediction time.")
term("Categorical dtype", "A pandas dtype that stores each distinct value once and every row as a small integer code; categories can be ordered.")

section("dates", "Parsing and using dates",
    p("""Dates arrive as text, and nothing date-like works until they are parsed. **`pd.to_datetime`** converts a column to `datetime64`; give it the `format=` you
    expect (`"%Y-%m-%d"`, `"%d/%m/%Y"`) so ambiguous strings such as `05/01/2026` are read the way your source writes them, and `errors="coerce"` so bad values
    become `NaT` (the missing timestamp) that you can count. pandas 3 infers the format from the first value and **raises** if later values use a different one;
    `format="mixed"` parses each value separately, slower and only for genuinely messy sources, and it has to **guess**: below it reads `05/01/2026`
    month first, as 1 May, which is wrong if the source writes day first. The resolution is inferred too (`datetime64[us]` for these
    strings), not always nanoseconds as in older versions."""),
    p("""The **`.dt` accessor** extracts parts for features: `dt.dayofweek` (Monday is 0), `dt.hour`, `dt.month`, `dt.day_name()`, `dt.date`. Subtracting timestamps gives a
    **`Timedelta`**, and `.dt.total_seconds()` or `/ pd.Timedelta("1D")` turns it into a number, such as "days the company took to respond". Store times in
    **UTC** and convert for display: `tz_localize("UTC")` marks naive timestamps as UTC, `tz_convert(...)` changes the zone. Named zones such as
    `America/New_York` need the tz database (the `tzdata` package in some environments); fixed offsets such as `"+05:30"` always work."""),
    ex("""
    import pandas as pd

    raw = pd.Series(["2026-01-02 09:15", "2026-01-02 23:40", "2026-01-05 08:00", "not a date"])
    ts = pd.to_datetime(raw, format="%Y-%m-%d %H:%M", errors="coerce")
    print(ts.dtype, ts.isna().sum())
    print(ts.dt.dayofweek.tolist(), ts.dt.day_name().tolist()[:3], ts.dt.hour.tolist())
    try:
        pd.to_datetime(pd.Series(["2026-01-05", "05/01/2026"]))
    except ValueError as e:
        print("ValueError:", str(e)[:60])
    print(pd.to_datetime(pd.Series(["2026-01-05", "05/01/2026"]), format="mixed").dt.date.tolist())
    sent, answered = pd.Timestamp("2026-01-02 09:15"), pd.Timestamp("2026-01-04 15:15")
    gap = answered - sent
    print(gap, gap / pd.Timedelta("1D"), gap.total_seconds())
    utc = ts.iloc[0].tz_localize("UTC")
    print(utc, utc.tz_convert("+05:30"))
    """, "dates.py"),
)

section("resample", "Regular calendars: resample and date ranges",
    p("""Events happen at irregular times; models and dashboards usually want a **regular** series: complaints per day, revenue per week. Put the timestamps in the
    index (`set_index("submitted")`) and **`resample(rule)`** groups rows into calendar bins and aggregates them, a group-by on time: `"D"` for days, `"W"` for weeks
    (ending on Sunday by default), `"ME"` for month ends, `"h"` for hours. Days with no events do appear in the result, as 0 for `count`/`sum` or NaN for
    `mean`, which a plain `groupby(dt.date)` would silently skip; Power BI solves the same problem with a separate date table."""),
    p("""A `DatetimeIndex` also allows **date slicing** with strings: `ts["2026-01"]` is all of January, and `ts["2026-01-03":"2026-01-05"]` includes both end days,
    like `loc`. `pd.date_range(start, periods=..., freq=...)` builds a calendar to `reindex` against when you need an explicit list of dates."""),
    ex("""
    import pandas as pd

    events = pd.DataFrame({
        "submitted": pd.to_datetime(["2026-01-01 10:00", "2026-01-01 15:30", "2026-01-03 09:00", "2026-01-06 11:00", "2026-01-06 12:00"]),
        "amount": [20.0, 35.0, 300.0, 15.0, 60.0],
    }).set_index("submitted")
    daily = events.resample("D").agg(n=("amount", "size"), total=("amount", "sum"), avg=("amount", "mean"))
    print(daily)
    print(events.groupby(events.index.date).size().to_dict())
    print(events.resample("W")["amount"].sum().to_dict())
    print(daily.loc["2026-01-02":"2026-01-03", "n"].tolist())
    print(pd.date_range("2026-01-31", periods=3, freq="ME").strftime("%Y-%m-%d").tolist())
    """, "resample.py"),
)

section("windows", "Rolling windows and lag features without leakage",
    p("""**`rolling(window)`** computes a statistic over a moving window of the last `window` rows (or a time span such as `"7D"` on a `DatetimeIndex`); the first
    rows have too little history and give NaN unless you set `min_periods`. **`expanding()`** uses all rows so far, and **`ewm(span=...)`** weights recent rows
    more. **`shift(k)`** moves a series down by `k` rows, so each row sees the value from `k` steps earlier: a **lag feature**. On a group-by, `shift` and
    `rolling` work within each group, so one customer's history never leaks into another's."""),
    p("""The rule that decides whether a time-series model works in production: **a feature for time t may only use data available before t**. `rolling(7).mean()`
    on day t **includes day t itself**; if the label is "complaints on day t", the feature contains the answer. Shift first: `s.shift(1).rolling(7).mean()` is
    the average of the seven days **before** t. The same rule applies to splitting: shuffled train/test splits put future rows in the training set, so the
    test score measures memory of the future. Split by **time** instead: train on everything before a cut-off date, test on everything after."""),
    fig(chain(["day t: predict|its count", ("rolling(7) includes day t:|leaks the label", "bad"), ("shift(1) then rolling(7):|days t-7 to t-1", "good"), "time-based split:|train before the cut-off"]),
        "Features and splits must respect time: only the past is allowed."),
    ex("""
    import pandas as pd

    counts = pd.Series([5, 7, 6, 9, 30, 8, 7], index=pd.date_range("2026-01-01", periods=7, freq="D"), name="n")
    feats = pd.DataFrame({
        "n": counts,
        "roll3_leaky": counts.rolling(3).mean().round(2),
        "roll3": counts.shift(1).rolling(3).mean().round(2),
        "lag1": counts.shift(1),
        "ewm": counts.shift(1).ewm(span=3).mean().round(2),
        "best_so_far": counts.expanding().max(),
    })
    print(feats)
    print(counts.rolling("3D").sum().tolist())
    cut = pd.Timestamp("2026-01-05")
    train, test = feats[feats.index < cut], feats[feats.index >= cut]
    print(len(train), len(test), test.index.min().date())
    """, "windows.py"),
    p("""Look at 5 January, the spike of 30. `roll3_leaky` already shows 15.0 on that day, because the window contains the spike: a model trained on it would look
    brilliant at predicting spikes and fail in production, where the day's count is unknown until the day is over. The shifted `roll3` is 7.33, built only from
    the three previous days. Note also that a time-based window (`"3D"`) works on irregular data and accepts partial windows at the start."""),
)

section("text", "Text with the .str accessor",
    p("""Text columns have a **`.str`** accessor with vectorised versions of Python's string methods (`lower`, `strip`, `replace`, `startswith`, `len`, `split`) plus
    regular-expression tools: `str.contains(pattern)` for filtering, `str.extract(pattern)` to pull **capture groups** into new columns, `str.replace(pattern,
    repl, regex=True)` to normalise, `str.count(pattern)`. Missing values pass through as missing. These run per value in optimised code and keep NaN handling
    consistent, so they beat `apply` with a Python function for anything they can express (Module 5's regex lesson applies directly)."""),
    p("""For LLM and retrieval work, two more tools matter. `str.split()` turns text into lists of words, and **`explode`** turns a column of lists into one row per
    element, keeping the index, which is how a narrative becomes words for counting or **chunks** for embedding. CFPB narratives also contain redactions
    written as runs of `X` (`XXXX`), which are noise for a model and should be normalised to one token before embedding or classification: in the
    example, the two most common "words" are redaction markers."""),
    p("""One measured surprise: with pandas' default Python-backed strings, each `.str` method is still a loop over Python strings, so a chain of two `.str`
    calls ran at about the same speed as one `apply` with a precompiled regex (138 ms against 142 ms for 40,000 texts when this page was built). The
    advantages of `.str` are clarity and missing-value handling; with the PyArrow-backed string storage, which pandas 3 uses when PyArrow is installed, many
    `.str` methods run in compiled code and are much faster."""),
    ex("""
    import pandas as pd

    notes = pd.Series([
        "I was charged $1,200.50 on XX/XX/2026 by XXXX XXXX.",
        "Refund of $35 never arrived!!   Called 3 times.",
        None,
        "Account closed without notice",
    ])
    print(notes.str.contains("refund", case=False).tolist())
    money = notes.str.extract(r"\\$([\\d,]+(?:\\.\\d+)?)", expand=False)
    print(money.tolist(), pd.to_numeric(money.str.replace(",", "")).tolist())
    clean = (notes.str.replace(r"\\bX{2,}\\b", "[REDACTED]", regex=True)
                  .str.replace(r"\\s+", " ", regex=True).str.strip())
    print(clean.tolist()[0])
    words = notes.str.lower().str.findall(r"[a-z]+")
    print(words.str.len().tolist())
    print(words.explode().value_counts().head(3).to_dict())
    """, "text.py"),
)

section("categoricals", "Categoricals and encodings",
    p("""The **`category`** dtype stores each distinct value once and every row as a small integer **code** (D.2 showed the memory saving). Its categories can be
    **ordered** (`pd.Categorical(values, categories=["low", "medium", "high"], ordered=True)`), which makes comparisons and sorting follow the business order
    instead of the alphabet, the pandas version of a "sort by column" setting in Power BI. Codes are also an encoding: `cat.codes` gives integers for an
    ordinal feature."""),
    p("""Most models need numbers. **One-hot encoding** creates one 0/1 column per category (`pd.get_dummies`). The trap is at inference time: new data may lack a
    category (no `mortgage` complaints today) or contain one never seen in training, so `get_dummies` produces **different columns**, and a model receiving
    them gets features in the wrong positions. Fix the column list from training and **`reindex`** new data to it, filling 0; or use scikit-learn's
    `OneHotEncoder(handle_unknown="ignore")`, which remembers its categories (D.6). Converting to a categorical with the training
    categories before `get_dummies` achieves the same, once unseen values have been turned into missing ones with `where(isin(...))`: pandas 3 warns that
    passing unknown values to `pd.Categorical` will become an error."""),
    ex("""
    import pandas as pd

    sev = pd.Categorical(["high", "low", "medium", "low"], categories=["low", "medium", "high"], ordered=True)
    s = pd.Series(sev)
    print(s.sort_values().tolist(), (s > "low").tolist(), s.cat.codes.tolist())
    train = pd.DataFrame({"product": ["card", "loan", "mortgage", "card"]})
    today = pd.DataFrame({"product": ["card", "crypto"]})
    X_train = pd.get_dummies(train["product"], prefix="p", dtype=int)
    X_today = pd.get_dummies(today["product"], prefix="p", dtype=int)
    print(X_train.columns.tolist(), X_today.columns.tolist())
    aligned = X_today.reindex(columns=X_train.columns, fill_value=0)
    print(aligned.values.tolist())
    known = ["card", "loan", "mortgage"]
    fixed = pd.Categorical(today["product"].where(today["product"].isin(known)), categories=known)
    print(pd.get_dummies(fixed, prefix="p", dtype=int).values.tolist())
    """, "categoricals.py"),
)

section("warmup", "Warm-up",
    predict("Dates and their parts", "easy",
        code="""
        import pandas as pd

        s = pd.to_datetime(pd.Series(["2026-02-27 22:00", "2026-03-01 06:30", "bad"]), format="%Y-%m-%d %H:%M", errors="coerce")
        print(s.isna().tolist(), s.dt.month.tolist())
        print(s.dt.day_name().tolist()[:2], s.dt.is_month_end.tolist()[:2])
        print((s.iloc[1] - s.iloc[0]), (s.iloc[1] - s.iloc[0]) / pd.Timedelta("1h"))
        print((s.iloc[0] + pd.Timedelta(days=2)).date(), (s.iloc[0] + pd.offsets.MonthEnd(1)).date())
        """,
        hints=["2026 is not a leap year, so February has 28 days. Missing timestamps are `NaT`, and their parts are NaN."],
        why="""`"bad"` becomes `NaT`, and `dt.month` of `NaT` is NaN, so the months come back as floats (2.0, 3.0, nan). 27 February 2026 is a Friday and 1 March a Sunday;
        27 February is not the last day of the month. From 22:00 on the 27th to 06:30 on 1 March is 1 day 8 hours 30 minutes, which is 32.5 hours. Adding two days
        crosses into March because February 2026 has 28 days, and `MonthEnd(1)` rolls forward to the end of the current month, the 28th."""),
    predict("Rolling, shift and the first rows", "easy",
        code="""
        import pandas as pd

        s = pd.Series([2, 4, 6, 8, 10])
        print(s.shift(1).tolist())
        print(s.rolling(2).sum().tolist())
        print(s.rolling(3, min_periods=1).mean().tolist())
        print(s.shift(1).rolling(2).mean().tolist())
        print(s.diff().tolist(), s.pct_change().round(2).tolist())
        print(s.expanding().sum().tolist())
        """,
        hints=["`shift(1)` puts NaN in the first position. A rolling window with too few values gives NaN unless `min_periods` allows fewer."],
        why="""`shift(1)` moves every value down one row. A window of 2 has no complete window at the first row. With `min_periods=1` the first windows are partial: 2,
        then the mean of 2 and 4, then of 2, 4 and 6, and so on. Shifting first means each window covers the previous two values only, so the first two rows
        are NaN. `diff` is the change from the previous row and `pct_change` the relative change (4 is 100% more than 2). `expanding().sum()` is a running
        total."""),
    write("Daily complaint counts with no gaps", "easy", tag="Data work",
        prompt="""Write `daily_counts(df, start, end)` for a frame with a `submitted` timestamp column: return a Series indexed by **every** day from `start` to `end`
        inclusive (strings such as `"2026-01-01"`), named `"complaints"`, holding the number of complaints submitted on each day as `int`, with 0 for days without
        any. Complaints outside the range are ignored.""",
        code="""
        import pandas as pd


        def daily_counts(df, start, end):
            return df.groupby(df["submitted"].dt.date).size()
        """,
        tests="""
        df = pd.DataFrame({"submitted": pd.to_datetime(["2026-01-01 09:00", "2026-01-01 17:00", "2026-01-03 12:00",
                                                         "2025-12-31 23:00", "2026-01-05 08:00"])})
        out = daily_counts(df, "2026-01-01", "2026-01-04")
        assert out.name == "complaints" and out.dtype.kind == "i"
        assert out.tolist() == [2, 0, 1, 0]
        assert [d.strftime("%m-%d") for d in out.index] == ["01-01", "01-02", "01-03", "01-04"]
        """,
        hints=["`set_index(\"submitted\").resample(\"D\").size()` counts per day, but only between the first and last event.",
               "`reindex(pd.date_range(start, end, freq=\"D\"), fill_value=0)` adds the missing days at both ends."],
        solution="""
        import pandas as pd


        def daily_counts(df, start, end):
            days = pd.date_range(start, end, freq="D")
            counts = df.set_index("submitted").resample("D").size()
            return counts.reindex(days, fill_value=0).astype(int).rename("complaints")
        """,
        why="""Grouping by date only produces days that have events, so a quiet day simply disappears, and a model or chart reading the series thinks the days are
        consecutive. `resample("D")` fills gaps **between** the first and last event, but not the days before the first or after the last one in your requested range,
        and it includes events outside the range. Reindexing to an explicit `date_range` solves both: days outside are dropped, missing days get 0. Both ends of
        `date_range` are inclusive. This calendar-first habit is the pandas version of joining to a date dimension."""),
    write("Extract amounts and dates from narratives", "easy", tag="Data work",
        prompt="""Write `extract_fields(texts)` for a Series of complaint narratives. Return a DataFrame with the same index and two columns: `amount`, the first dollar amount
        in the text as a float (`"$1,200.50"` becomes 1200.5, `"$35"` becomes 35.0), and `date`, the first date written as `YYYY-MM-DD`, as a timestamp. Missing or
        absent values are NaN / NaT. Use `str.extract`, no Python loop.""",
        code="""
        import pandas as pd


        def extract_fields(texts):
            return pd.DataFrame({"amount": texts.str.extract(r"(\\d+)", expand=False)})
        """,
        tests="""
        texts = pd.Series(["Paid $1,200.50 on 2026-01-04, refunded $5", "No money here, see 2026-02-30", None, "Fee of $35 charged 2026-03-01"],
                          index=[10, 11, 12, 13])
        out = extract_fields(texts)
        assert out.index.tolist() == [10, 11, 12, 13] and list(out.columns) == ["amount", "date"]
        assert out["amount"].iloc[0] == 1200.5 and out["amount"].iloc[3] == 35.0 and out["amount"].isna().sum() == 2
        assert str(out["date"].iloc[0].date()) == "2026-01-04" and pd.isna(out["date"].iloc[1])
        assert out["date"].dtype.kind == "M"
        """,
        hints=["Amount pattern: a `$` then digits and commas, optionally a dot and more digits: `r\"\\$([\\d,]+(?:\\.\\d+)?)\"`.",
               "Dates: `r\"(\\d{4}-\\d{2}-\\d{2})\"`, then `pd.to_datetime(..., format=\"%Y-%m-%d\", errors=\"coerce\")` turns the impossible 30 February into NaT."],
        solution="""
        import pandas as pd


        def extract_fields(texts):
            amount = texts.str.extract(r"\\$([\\d,]+(?:\\.\\d+)?)", expand=False)
            date = texts.str.extract(r"(\\d{4}-\\d{2}-\\d{2})", expand=False)
            return pd.DataFrame({
                "amount": pd.to_numeric(amount.str.replace(",", "")),
                "date": pd.to_datetime(date, format="%Y-%m-%d", errors="coerce"),
            })
        """,
        why="""`str.extract` with one capture group and `expand=False` returns a Series of the first match per row, NaN where there is none, aligned to the original index.
        The amount pattern anchors on `$`, so the starter's "first run of digits" (which picked up `1`) is avoided, allows thousands separators, and makes the
        decimal part optional with a non-capturing group `(?:...)`. Commas are removed before `to_numeric`. A string that looks like a date is not necessarily one:
        `2026-02-30` matches the pattern, and `errors="coerce"` turns it into `NaT` instead of raising. Extracting structured fields from text with regex is
        cheap and exact; an LLM is the tool when the wording varies too much for a pattern."""),
)

section("medium", "Medium",
    fix("A rolling feature that sees the label", "medium", tag="ML",
        prompt="""`add_features` builds features to predict each day's complaint count `n`. The model scored suspiciously well offline and badly in production. Fix the two
        leaky features so that each uses only days **before** the current one: `avg7` (mean of the previous 7 days, allowing partial windows of at least 3 days)
        and `max_so_far` (the maximum of all previous days). The first rows should be NaN where there is not enough history.""",
        code="""
        import pandas as pd


        def add_features(daily):
            out = daily.copy()
            out["avg7"] = out["n"].rolling(7, min_periods=3).mean()
            out["max_so_far"] = out["n"].expanding().max()
            return out
        """,
        tests="""
        import numpy as np
        daily = pd.DataFrame({"n": [4, 6, 8, 100, 6, 4, 2, 9]}, index=pd.date_range("2026-01-01", periods=8))
        f = add_features(daily)
        assert f["avg7"].iloc[:3].isna().all()
        assert f["avg7"].iloc[3] == 6.0 and f["avg7"].iloc[7] == np.mean([4, 6, 8, 100, 6, 4, 2])
        assert np.isnan(f["max_so_far"].iloc[0]) and f["max_so_far"].iloc[3] == 8 and f["max_so_far"].iloc[4] == 100
        assert not f["avg7"].equals(f["n"].rolling(7, min_periods=3).mean())
        """,
        hints=["Shift the series by one before the window, so the window ends yesterday."],
        solution="""
        import pandas as pd


        def add_features(daily):
            out = daily.copy()
            past = out["n"].shift(1)
            out["avg7"] = past.rolling(7, min_periods=3).mean()
            out["max_so_far"] = past.expanding().max()
            return out
        """,
        why="""Both windows ended **today**: on 4 January the "average" already contained the spike of 100 it was supposed to predict, and `max_so_far` equalled the label
        whenever a new record was set. Offline, the model learns to read the answer from the feature; in production the day's value is not known until the day is
        over, so the feature is unavailable or different, and accuracy collapses. Shifting by one first makes every window end yesterday. On 8 January the window
        holds exactly the seven days before it, 1 to 7 January; on 4 January it holds the three days that exist, which `min_periods=3` allows. Leakage of this kind is the most
        common reason a time-series model looks too good."""),
    write("A time-based train and test split", "medium", tag="ML",
        prompt="""Write `time_split(df, time_col, test_size=0.25, gap="0D")` returning `(train, test)`: sort by `time_col`, put the latest `test_size` fraction of **rows**
        (rounded up) in `test`, and everything strictly earlier than `test`'s first timestamp minus `gap` (a `Timedelta` string) in `train`, so rows inside the gap
        are in neither. Rows sharing a timestamp must never be split across train and test: if the boundary falls inside a timestamp, the whole timestamp goes to
        `test`.""",
        code="""
        import pandas as pd


        def time_split(df, time_col, test_size=0.25, gap="0D"):
            test = df.sample(frac=test_size, random_state=0)
            train = df.drop(test.index)
            return train, test
        """,
        tests="""
        t = pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04", "2026-01-04", "2026-01-05", "2026-01-06", "2026-01-07"])
        df = pd.DataFrame({"t": t[::-1], "y": range(8)})
        train, test = time_split(df, "t", test_size=0.25)
        assert test["t"].min() == pd.Timestamp("2026-01-06") and len(test) == 2
        assert train["t"].max() < test["t"].min() and len(train) == 6
        train, test = time_split(df, "t", test_size=0.5)
        assert len(test) == 5 and test["t"].min() == pd.Timestamp("2026-01-04")
        train, test = time_split(df, "t", test_size=0.25, gap="2D")
        assert train["t"].max() == pd.Timestamp("2026-01-03") and len(train) + len(test) == 5
        """,
        hints=["`n_test = math.ceil(len(df) * test_size)`; after sorting, the cut-off time is the timestamp at position `len(df) - n_test`.",
               "Test is every row with time `>= cutoff`, train every row with time `< cutoff - pd.Timedelta(gap)`."],
        solution="""
        import math
        import pandas as pd


        def time_split(df, time_col, test_size=0.25, gap="0D"):
            s = df.sort_values(time_col, kind="stable")
            n_test = math.ceil(len(s) * test_size)
            cutoff = s[time_col].iloc[len(s) - n_test]
            test = s[s[time_col] >= cutoff]
            train = s[s[time_col] < cutoff - pd.Timedelta(gap)]
            return train, test
        """,
        why="""A random split puts complaints from next week in the training set and asks the model to "predict" last week, which measures how well it interpolates the
        past, not how it will do on tomorrow's data. A time-based split mirrors production: train on the past, evaluate on the most recent period. Defining the
        test set by a cut-off **time** rather than a row count keeps rows with the same timestamp together (with `test_size=0.5` the boundary falls between the two
        4 January rows, so both go to test, making 5). The optional gap leaves a buffer so that features computed over recent days (rolling windows, slowly
        arriving labels) cannot overlap the test period. scikit-learn's `TimeSeriesSplit` generalises this into several expanding folds, and it has a `gap`
        parameter for the same reason."""),
    write("Lag features per customer", "medium", tag="ML",
        prompt="""Write `add_customer_lags(df)` for complaints with `customer`, `submitted` and `amount`. Return a copy sorted by `customer` then `submitted`, with three new
        columns computed within each customer from **earlier** complaints only: `prev_amount` (the previous complaint's amount), `days_since_prev` (days since the
        previous complaint, as a float) and `n_before` (how many complaints the customer filed before this one). The first complaint of each customer has NaN for
        the first two and 0 for `n_before`.""",
        code="""
        import pandas as pd


        def add_customer_lags(df):
            out = df.sort_values("submitted").copy()
            out["prev_amount"] = out["amount"].shift(1)
            out["days_since_prev"] = out["submitted"].diff().dt.days
            out["n_before"] = range(len(out))
            return out
        """,
        tests="""
        import numpy as np
        df = pd.DataFrame({"customer": ["b", "a", "a", "b", "a"],
                           "submitted": pd.to_datetime(["2026-01-03 00:00", "2026-01-01 00:00", "2026-01-04 12:00", "2026-01-10 00:00", "2026-01-02 00:00"]),
                           "amount": [50.0, 10.0, 30.0, 70.0, 20.0]})
        out = add_customer_lags(df)
        assert out["customer"].tolist() == ["a", "a", "a", "b", "b"]
        assert np.isnan(out["prev_amount"].iloc[0]) and out["prev_amount"].tolist()[1:3] == [10.0, 20.0]
        assert np.isnan(out["prev_amount"].iloc[3]) and out["prev_amount"].iloc[4] == 50.0
        assert out["days_since_prev"].tolist()[1:3] == [1.0, 2.5] and out["days_since_prev"].iloc[4] == 7.0
        assert out["n_before"].tolist() == [0, 1, 2, 0, 1]
        """,
        hints=["`g = out.groupby(\"customer\")`, then `g[\"amount\"].shift(1)`, `g[\"submitted\"].diff()` and `g.cumcount()`.",
               "Convert a Timedelta column to fractional days with `/ pd.Timedelta(\"1D\")`; `dt.days` drops the hours."],
        solution="""
        import pandas as pd


        def add_customer_lags(df):
            out = df.sort_values(["customer", "submitted"], kind="stable").reset_index(drop=True)
            g = out.groupby("customer")
            out["prev_amount"] = g["amount"].shift(1)
            out["days_since_prev"] = g["submitted"].diff() / pd.Timedelta("1D")
            out["n_before"] = g.cumcount()
            return out
        """,
        why="""Without the group-by, the "previous complaint" of a customer's first complaint is someone else's last one, so information flows between customers and the first
        row of each customer gets a meaningless value. Grouped `shift`, `diff` and `cumcount` restart for every customer. Sorting by customer and time first makes
        "previous" mean "previous in time". `dt.days` keeps only whole days (2 days 12 hours becomes 2); dividing by one day keeps the fraction, 2.5, which is the
        more useful feature. `cumcount` counts earlier rows in the group, exactly "complaints before this one", and none of these features look at later rows."""),
    choose("Lags with a group-by or a loop over customers", "medium", tag="ML",
        prompt="Both add the previous amount per customer for 60,000 complaints and 3,000 customers, already sorted. Which is faster?",
        setup="""import numpy as np
import pandas as pd
rng = np.random.default_rng(2)
df = pd.DataFrame({"customer": np.sort(rng.integers(0, 3_000, 60_000)), "amount": rng.uniform(0, 500, 60_000)})""",
        options={
            "a": "prev = pd.concat([g[\"amount\"].shift(1) for _, g in df.groupby(\"customer\")])",
            "b": "prev = df.groupby(\"customer\")[\"amount\"].shift(1)",
        },
        answer="b",
        hints=["Option A creates 3,000 small DataFrames and 3,000 Series, then concatenates them."],
        why="""Iterating over a group-by is convenient, but every group becomes a separate DataFrame object, and each `shift` call pays pandas' fixed overhead, so option A
        spends almost all its time on bookkeeping for 3,000 tiny operations, plus a final `concat`. Option B computes the group boundaries once and shifts the whole
        column in compiled code, respecting the boundaries. The same goes for `cumsum`, `diff`, `rank` and `rolling` on a group-by: call them on the group-by
        object, not inside a loop over groups."""),
    write("Clean narratives before embedding", "medium", tag="GenAI",
        prompt="""Before embedding complaint narratives for retrieval, write `prepare_texts(s, min_words=5)`: replace every redaction (a word made only of two or more `X`s,
        optionally followed by `/` and more `X`s, such as `XXXX` or `XX/XX`) with the single token `[X]`, merge runs of consecutive `[X]` tokens into one, collapse
        whitespace, strip, and drop texts with fewer than `min_words` words, or missing ones. Return a Series keeping the original index of the kept rows.""",
        code="""
        import pandas as pd


        def prepare_texts(s, min_words=5):
            return s.str.replace("XXXX", "[X]")
        """,
        tests="""
        s = pd.Series(["Called XXXX XXXX on XX/XX/2026   and got nothing.", "XXXX", None, "My card was blocked again today", "Too short now"],
                      index=[3, 5, 8, 9, 12])
        out = prepare_texts(s)
        assert out.index.tolist() == [3, 9]
        assert out.loc[3] == "Called [X] on [X]/2026 and got nothing."
        assert out.loc[9] == "My card was blocked again today"
        assert prepare_texts(s, min_words=1).index.tolist() == [3, 5, 9, 12]
        """,
        hints=["Redactions: `r\"\\bX{2,}(?:/X{2,})*\\b\"`. Merge repeats with `r\"\\[X\\](?:\\s+\\[X\\])+\"`.",
               "Count words with `str.split().str.len()`; missing texts give NaN, which fails `>=`."],
        solution="""
        import pandas as pd


        def prepare_texts(s, min_words=5):
            t = s.str.replace(r"\\bX{2,}(?:/X{2,})*\\b", "[X]", regex=True)
            t = t.str.replace(r"\\[X\\](?:\\s+\\[X\\])+", "[X]", regex=True)
            t = t.str.replace(r"\\s+", " ", regex=True).str.strip()
            words = t.str.split().str.len()
            return t[words >= min_words]
        """,
        why="""Redaction markers carry no meaning, but embedding models still spend tokens and attention on them, and narratives that share many `XXXX` runs look similar to
        each other for the wrong reason. Normalising them to one token keeps the information "something was redacted here" without the noise. The `\\b` word
        boundaries stop the pattern from eating the `XX` inside a real word, and the `(?:/X{2,})*` part handles redacted dates such as `XX/XX`, leaving the
        visible year. Very short texts make poor retrieval units and poor training examples, so they are filtered after cleaning (a text of only `XXXX` becomes one
        word). Keeping the original index lets you join embeddings back to the complaint ids."""),
    trace("Categories, codes and order", "medium",
        prompt="Fill in `out` after each marked line.",
        code="""
        import pandas as pd

        s = pd.Series(pd.Categorical(["med", "low", "high", "med"], categories=["low", "med", "high"], ordered=True))
        out = s.cat.codes.tolist()  # row: "codes"
        out = s.sort_values().tolist()  # row: "sorted"
        out = (s >= "med").tolist()  # row: "compare"
        out = s.max()  # row: "max"
        t = s.cat.add_categories(["critical"])
        out = t.cat.categories.tolist()  # row: "added"
        out = t.value_counts().tolist()  # row: "counts"
        u = pd.Series(pd.Categorical(["b", "a", "b"]))
        out = u.cat.codes.tolist()  # row: "unordered codes"
        """,
        trace_vars=["out"],
        hints=["Codes follow the order of `categories`, not of appearance. `value_counts` includes categories with zero rows, sorted by count."],
        why="""Codes are positions in the category list: `low` is 0, `med` 1, `high` 2. Sorting follows that order, and so do comparisons and `max`, because the categorical is
        ordered; with plain strings, `"high" < "low"` alphabetically. Adding a category extends the list without changing any row. `value_counts` reports every
        category, including `critical` with 0, ordered by count (ties keep the category order). Without explicit categories, pandas sorts the distinct values, so
        `a` is 0 and `b` is 1 regardless of which came first."""),
    write("One-hot features that survive new data", "medium", tag="ML",
        prompt="""Write `OneHot` with `fit(df, cols)` that remembers, for each column in `cols`, the categories seen in training (sorted, missing values excluded), and
        `transform(df)` that returns an int DataFrame with one column per (column, category) named `f"{col}={value}"`, in a fixed order (columns in `cols` order,
        categories sorted), with all zeros for unseen or missing values. The output must have identical columns for any input, even an empty frame. Then add a
        method `unseen(df)` returning a dict from column to the sorted list of values not seen in training.""",
        code="""
        import pandas as pd


        class OneHot:
            def fit(self, df, cols):
                self.cols = cols
                return self

            def transform(self, df):
                return pd.get_dummies(df[self.cols], dtype=int)

            def unseen(self, df):
                return {}
        """,
        tests="""
        train = pd.DataFrame({"product": ["card", "loan", "card", None], "channel": ["web", "phone", "web", "web"]})
        enc = OneHot().fit(train, ["product", "channel"])
        new = pd.DataFrame({"product": ["crypto", "loan"], "channel": ["web", "fax"]}, index=[7, 8])
        X = enc.transform(new)
        assert X.columns.tolist() == ["product=card", "product=loan", "channel=phone", "channel=web"]
        assert X.values.tolist() == [[0, 0, 0, 1], [0, 1, 0, 0]] and X.index.tolist() == [7, 8]
        assert enc.transform(new.iloc[:0]).columns.tolist() == X.columns.tolist()
        assert enc.unseen(new) == {"product": ["crypto"], "channel": ["fax"]}
        assert enc.transform(train).sum().tolist() == [2, 1, 1, 3]
        """,
        hints=["Store `sorted(df[c].dropna().unique())` per column in `fit`.", "In `transform`, set unseen values to missing with `df[c].where(df[c].isin(known))`, then convert to `pd.Categorical(..., categories=known)`; `get_dummies` of that produces exactly the known columns."],
        solution="""
        import pandas as pd


        class OneHot:
            def fit(self, df, cols):
                self.cols = list(cols)
                self.cats_ = {c: sorted(df[c].dropna().unique().tolist()) for c in self.cols}
                return self

            def transform(self, df):
                parts = []
                for c in self.cols:
                    known = self.cats_[c]
                    cat = pd.Categorical(df[c].where(df[c].isin(known)), categories=known)
                    d = pd.get_dummies(cat, dtype=int)
                    d.columns = [f"{c}={v}" for v in self.cats_[c]]
                    d.index = df.index
                    parts.append(d)
                return pd.concat(parts, axis=1)

            def unseen(self, df):
                out = {}
                for c in self.cols:
                    extra = set(df[c].dropna()) - set(self.cats_[c])
                    if extra:
                        out[c] = sorted(extra)
                return out
        """,
        why="""`get_dummies` creates columns from whatever values are present, so a batch without loans has no `loan` column and a batch with a new product has an extra one:
        the model then receives features in the wrong positions, usually without any error, because it only sees a matrix. Fixing the categories at `fit` time,
        turning unknown values into missing ones and converting to a categorical with the known categories means `get_dummies` always creates one column per
        category, even with no rows. Looping over a few columns is fine. Reporting unseen values is the monitoring half: a new product appearing in production is
        data drift that someone should know about. scikit-learn's `OneHotEncoder(handle_unknown="ignore")` implements the same contract inside a pipeline."""),
)

section("hard", "Hard",
    write("Sessions from an event log", "hard", tag="Data work",
        prompt="""An agent's tool-call log has `user` and `time` columns. A **session** is a run of a user's events where each event is at most `gap` minutes after the
        previous one. Write `sessionize(events, gap=30)` returning a copy sorted by user and time with an int column `session` numbering each user's sessions from 1,
        and `summarise(sessions)` returning one row per `(user, session)` with `start`, `end`, `events` and `minutes` (duration as a float). Vectorised: group-by
        `diff`, comparison and `cumsum`, no Python loop over rows.""",
        code="""
        import pandas as pd


        def sessionize(events, gap=30):
            out = events.copy()
            out["session"] = 1
            return out


        def summarise(sessions):
            return sessions.groupby("user").size()
        """,
        tests="""
        t = pd.to_datetime(["2026-01-01 10:00", "2026-01-01 10:20", "2026-01-01 11:30", "2026-01-01 10:05", "2026-01-01 11:00", "2026-01-01 11:29"])
        ev = pd.DataFrame({"user": ["u1", "u1", "u1", "u2", "u2", "u2"], "time": t}).sample(frac=1, random_state=3)
        s = sessionize(ev)
        assert s["user"].tolist() == ["u1", "u1", "u1", "u2", "u2", "u2"]
        assert s["session"].tolist() == [1, 1, 2, 1, 2, 2]
        summ = summarise(s)
        assert list(summ.columns) == ["user", "session", "start", "end", "events", "minutes"]
        assert summ["events"].tolist() == [2, 1, 1, 2] and summ["minutes"].tolist() == [20.0, 0.0, 0.0, 29.0]
        assert len(ev) == 6 and "session" not in ev.columns
        """,
        hints=["After sorting, `new = events.groupby(\"user\")[\"time\"].diff() > pd.Timedelta(minutes=gap)`; the first event of each user has NaT, which compares False.",
               "`new.groupby(user).cumsum() + 1` numbers the sessions within each user."],
        solution="""
        import pandas as pd


        def sessionize(events, gap=30):
            out = events.sort_values(["user", "time"], kind="stable").reset_index(drop=True)
            new = out.groupby("user")["time"].diff() > pd.Timedelta(minutes=gap)
            out["session"] = new.groupby(out["user"]).cumsum().astype(int) + 1
            return out


        def summarise(sessions):
            summ = sessions.groupby(["user", "session"], as_index=False).agg(
                start=("time", "min"), end=("time", "max"), events=("time", "size"))
            summ["minutes"] = (summ["end"] - summ["start"]) / pd.Timedelta("1min")
            return summ
        """,
        why="""Sessionisation is the gaps-and-islands problem from SQL, and the pandas answer is three vectorised steps. Within each user, `diff` gives the time since the
        previous event; comparing it with the gap marks the events that **start** a new session (the first event of each user has no previous one, so its `NaT`
        compares as False). The running sum of those booleans within each user increases by one at every new session, so adding 1 numbers them from 1. u2's events
        at 11:00 and 11:29 are 29 minutes apart, inside the gap, so they share a session. The summary is then an ordinary named aggregation. Shuffling the input in
        the test makes sure the function sorts instead of trusting the order."""),
    write("Chunk narratives for retrieval", "hard", tag="GenAI",
        prompt="""Write `chunk_texts(df, size, overlap)` for a frame with `id` and `text`: split every text into words and cut it into chunks of at most `size` words, where
        each chunk starts `size - overlap` words after the previous one, and a text with no more than `size` words gives one chunk. Return a DataFrame with columns
        `id`, `chunk` (0, 1, 2... within each text), `text` (the chunk's words joined by spaces) and `n_words`. Missing or empty texts give no chunks. Raise
        `ValueError` unless `0 <= overlap < size`. Use `explode` for the rows; a Python function per text (not per word) is fine.""",
        code="""
        import pandas as pd


        def chunk_texts(df, size, overlap):
            return df.assign(chunk=0)
        """,
        tests="""
        df = pd.DataFrame({"id": [1, 2, 3, 4], "text": ["a b c d e f g", "short text", None, "   "]})
        out = chunk_texts(df, size=4, overlap=1)
        assert list(out.columns) == ["id", "chunk", "text", "n_words"]
        assert out["id"].tolist() == [1, 1, 2] and out["chunk"].tolist() == [0, 1, 0]
        assert out["text"].tolist() == ["a b c d", "d e f g", "short text"]
        assert out["n_words"].tolist() == [4, 4, 2]
        assert chunk_texts(df, 3, 0)["text"].tolist()[:3] == ["a b c", "d e f", "g"]
        assert chunk_texts(df, 5, 2)["text"].tolist()[:2] == ["a b c d e", "d e f g"]
        import pytest
        with pytest.raises(ValueError):
            chunk_texts(df, 3, 3)
        """,
        hints=["Write `windows(words)` returning a list of word lists: start at 0, step `size - overlap`, and stop once a window reaches the last word.",
               "`df.assign(chunks=words.map(windows)).explode(\"chunks\")`, then `groupby(\"id\").cumcount()` numbers the chunks."],
        solution="""
        import pandas as pd


        def chunk_texts(df, size, overlap):
            if not 0 <= overlap < size:
                raise ValueError("need 0 <= overlap < size")
            step = size - overlap

            def windows(words):
                out = []
                for start in range(0, len(words), step):
                    out.append(words[start:start + size])
                    if start + size >= len(words):
                        break
                return out

            words = df["text"].fillna("").str.split()
            exploded = (df[["id"]].assign(chunks=words.map(windows))
                        .explode("chunks").dropna(subset=["chunks"]))
            exploded["chunk"] = exploded.groupby("id").cumcount()
            exploded["text"] = exploded["chunks"].map(" ".join)
            exploded["n_words"] = exploded["chunks"].map(len)
            return exploded[["id", "chunk", "text", "n_words"]].reset_index(drop=True)
        """,
        why="""Retrieval works on chunks, not whole documents: an embedding of a long narrative blurs its topics, and a prompt has a token budget. Overlap keeps a sentence that
        straddles a boundary intact in at least one chunk (with size 4 and overlap 1, the word `d` ends one chunk and starts the next). The loop stops as soon as a
        window reaches the end, so the tail is never a duplicate fragment already inside the previous chunk (size 5, overlap 2 gives two chunks, not three). Building
        the list of chunks per text and then `explode` produces one row per chunk with the document's id carried along; an empty list explodes to NaN, which
        `dropna` removes, so empty texts disappear. Real chunkers count tokens rather than words and prefer sentence boundaries, but the bookkeeping is the same."""),
    predict("Time-series details that bite", "hard",
        code="""
        import pandas as pd

        idx = pd.date_range("2026-01-29", periods=6, freq="D")
        s = pd.Series([1, 2, 3, 4, 5, 6], index=idx)
        print(s["2026-01-30":"2026-02-01"].tolist())
        print(s["2026-02"].tolist())
        print(s.resample("ME").sum().index.strftime("%m-%d").tolist())
        print(s.resample("W").sum().tolist())
        print(s.rolling("2D").sum().tolist())
        print(s.asfreq("2D").tolist())
        print((s.index[1:] - s.index[:-1]).unique().tolist() == [pd.Timedelta("1D")])
        """,
        hints=["String slices on a DatetimeIndex include both ends. `\"W\"` weeks end on Sunday; 1 February 2026 is a Sunday. `asfreq` keeps the values at the new dates without aggregating."],
        why="""Date-string slices include the end day, so 30 January to 1 February is three values, and `s["2026-02"]` selects the whole of February present (3 values).
        Monthly resampling labels each bin with its **end** date (31 January, 28 February), a frequent surprise when joining with tables keyed by the first of the
        month. Weekly bins end on Sunday: 29 January to 1 February sums to 10, and 2 to 3 February to 11. A time-based rolling window of `"2D"` covers the current day and the one
        before, with a partial first window. `asfreq("2D")` simply samples every second day, keeping values rather than summing them. The regular spacing check
        confirms the index has no gaps."""),
)

section("interview", "Interview questions",
    explain("How do you avoid leakage when building features and splits for time-series data?", "hard", tag="Interview",
        why="""Leakage means a feature or a training row uses information that would not be available at prediction time, so offline scores are optimistic and production
        performance collapses. For features: every value for time t must be computed from data before t (or before t minus the latency with which data really
        arrives), so lags use `shift`, rolling and expanding windows are applied to the shifted series, group-wise features are computed within the entity and in time
        order, and aggregates such as target encodings or normalisation statistics are fitted on the training period only. Watch for subtle sources: a "last status"
        column that is updated after the event, data back-filled later, or features joined from a table snapshot taken after the cut-off. For splits: never shuffle;
        train on a period, validate on the next period, and test on the latest, optionally with a gap; for model selection use rolling-origin or expanding-window
        cross-validation (`TimeSeriesSplit`), and make sure rows from the same entity and timestamp do not straddle the boundary. A good check is to simulate
        prediction: rebuild features "as of" a past date and compare with the training features."""),
    explain("How do you encode categorical features, and what goes wrong in production?", "medium", tag="Interview",
        why="""It depends on the model and the cardinality. One-hot encoding (one 0/1 column per category) suits linear models and low-cardinality columns; ordinal codes suit
        genuinely ordered categories (low, medium, high) and tree models; target encoding (the smoothed mean label per category, fitted out of fold) handles high
        cardinality such as merchants or zip codes; hashing bounds the number of columns; and learned embeddings are the neural option. Gradient-boosting libraries
        such as LightGBM and CatBoost can take categoricals natively. In production the problems are consistency and change: `pd.get_dummies` on new data creates
        different columns when a category is missing or new, so the feature matrix silently shifts; new categories appear (a new product), so the encoder must
        handle unknowns (`handle_unknown="ignore"`, an "other" bucket, or the prior for target encoding); rare categories overfit, so group them; and the category
        list must be saved with the model, ideally as a fitted encoder inside a pipeline. Monitoring the share of unseen categories is a cheap drift alarm."""),
    explain("How would you prepare free-text complaint narratives for a classical classifier versus an LLM or embedding model?", "medium", tag="Interview",
        why="""For a classical model (TF-IDF plus logistic regression), preprocessing shapes the vocabulary, so you lower-case, normalise or remove punctuation, numbers and
        redaction markers, possibly remove stop words or lemmatise, and keep n-grams; the text is reduced to counts, so noise directly becomes features. For an LLM
        or a modern embedding model, the tokenizer and the model already handle case, punctuation and word forms, and aggressive cleaning removes signal (negation,
        casing, structure), so you clean only what is genuinely noise: collapse redaction runs, strip HTML and boilerplate, fix encoding problems, normalise
        whitespace, and remove or mask personal data. You also manage length: truncate or chunk to the model's context and token budget, with overlap for
        retrieval, and keep ids so chunks can be traced back. In both cases de-duplicate, drop empty or near-empty texts, keep the raw text for audit, apply exactly
        the same preprocessing at training and inference time, and check language and length distributions, because a few huge or non-English documents can
        dominate costs or results."""),
)

recap(
    "Parse with `pd.to_datetime(format=..., errors=\"coerce\")` and count the `NaT`s; pandas 3 raises on mixed formats unless `format=\"mixed\"`. Use `.dt` for parts and store UTC.",
    "`resample` groups by calendar bins and keeps empty days; reindex to a `date_range` for a fixed calendar. Date-string slices include both ends; monthly bins are labelled by month end.",
    "Lag and window features must end before the row they describe: `shift(1)` before `rolling` or `expanding`, and within groups. Split by time, never shuffle.",
    "`.str` methods handle missing values and regex (`contains`, `extract`, `replace`); `split` plus `explode` turns text into words or chunks.",
    "`category` stores codes and can be ordered; fix categories at training time and align new data, so one-hot columns never shift.",
)
