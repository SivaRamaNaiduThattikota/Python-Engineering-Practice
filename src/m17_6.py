from lesson import *
from diagrams import *

lesson(
    id="m17-6", num="D.6", title="scikit-learn: pipelines, validation and metrics",
    intro="scikit-learn turns the pieces of the last five lessons into models you can trust. The estimator API, honest splits and cross-validation, "
          "pipelines that make leakage impossible, preprocessing mixed columns, metrics that fit the problem (and the baseline to beat), a text "
          "classifier, hyperparameter search, and your own transformer.",
    desc="fit/predict/transform, stratified splits, cross-validation, Pipeline and ColumnTransformer, metrics and baselines, TF-IDF text models, grid search, custom transformers.",
    keys="scikit-learn sklearn estimator fit predict predict_proba transform fit_transform score random_state train_test_split stratify cross_val_score cross_validate StratifiedKFold TimeSeriesSplit pipeline make_pipeline ColumnTransformer SimpleImputer StandardScaler OneHotEncoder handle_unknown leakage DummyClassifier baseline accuracy precision recall f1 confusion_matrix classification_report roc_auc average_precision imbalanced class_weight TfidfVectorizer LogisticRegression GridSearchCV param grid get_params clone BaseEstimator TransformerMixin cohen_kappa",
)

term("Estimator", "Any scikit-learn object with `fit`; models add `predict`, transformers add `transform`. Learned values are stored in attributes ending in `_`.")
term("Pipeline", "A chain of transformers ending in a model, fitted and applied as one estimator, so every preprocessing step is learned from training data only.")
term("Cross-validation", "Estimating performance by training and scoring on several different train/validation splits of the training data, then averaging.")
term("Baseline", "The simplest reasonable predictor (always the majority class, or a rule); a model is only useful if it clearly beats it.")

section("api", "One API for every model",
    p("""Every scikit-learn object follows one small contract, which is why you can swap a logistic regression for a random forest in one line. An **estimator** is
    created with its settings (**hyperparameters**: `LogisticRegression(C=1.0, max_iter=1000)`), and **`fit(X, y)`** learns from data and returns the estimator itself.
    What it learned is stored in attributes ending with an underscore: `coef_`, `classes_`, `mean_`. Models then offer **`predict(X)`** (labels),
    **`predict_proba(X)`** (one probability column per class, in the order of `classes_`) and **`score(X, y)`** (accuracy for classifiers, R^2 for regressors).
    **Transformers** such as `StandardScaler` offer **`transform(X)`**, and `fit_transform` does both steps on the same data."""),
    p("""`X` is a 2-D table (`(n_samples, n_features)`, a NumPy array or a DataFrame) and `y` a 1-D array of labels: the `make_xy` of D.2. Anything random (splits, model
    initialisation, forests) takes a **`random_state`**; set it, so a result can be reproduced and two experiments differ only in what you changed."""),
    ex("""
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    X = np.array([[20.0, 1], [35.0, 0], [300.0, 3], [1200.0, 5], [15.0, 0], [250.0, 4]])
    y = np.array(["low", "low", "high", "high", "low", "high"])
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)
    print(scaler.mean_.round(1), Xs.mean(axis=0).round(6), Xs.std(axis=0).round(6))
    model = LogisticRegression(random_state=0)
    print(model.fit(Xs, y) is model, model.classes_)
    new = scaler.transform([[40.0, 1], [900.0, 4]])
    print(model.predict(new), model.predict_proba(new).round(3))
    print(model.score(Xs, y), model.coef_.shape)
    """, "api.py"),
    p("""The new rows were scaled with `scaler.transform`, using the mean and spread learned from the training rows; calling `fit_transform` on them would rescale
    them by their own statistics, the leakage and inconsistency D.2's imputer warned about. Keeping fit and transform straight by hand is error-prone, which is
    what pipelines are for."""),
)

section("split", "Honest splits and cross-validation",
    p("""A model is judged on data it did not learn from. **`train_test_split(X, y, test_size=0.2, stratify=y, random_state=0)`** holds out a test set;
    `stratify=y` keeps the class proportions equal in both parts, which matters when one class is rare (with 5% urgent complaints, an unstratified split can put
    almost none in the test set). The test set is used **once**, at the end. Choices made while developing (features, models, hyperparameters) are compared with
    **cross-validation** on the training part: `cross_val_score(model, X, y, cv=StratifiedKFold(5, shuffle=True, random_state=0))` trains five times, each time
    holding out a different fifth, and returns five scores whose mean and spread are much more reliable than one split. For time-ordered data use
    `TimeSeriesSplit` instead (D.4)."""),
    fig(chain(["all labelled data", ("train 80%", "accent"), "5-fold cross-validation:|compare ideas", "refit the chosen|pipeline on train", ("test 20%:|scored once", "good")]),
        "The test set is touched once; every decision before that uses cross-validation on the training data."),
    ex("""
    import numpy as np
    from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
    from sklearn.linear_model import LogisticRegression

    rng = np.random.default_rng(0)
    X = rng.normal(size=(400, 3))
    y = (X[:, 0] + 0.5 * X[:, 1] + rng.normal(scale=0.8, size=400) > 1.6).astype(int)
    print("positive rate:", y.mean())
    for strat in (None, y):
        _, _, _, y_te = train_test_split(X, y, test_size=0.2, random_state=3, stratify=strat)
        print("stratified" if strat is not None else "plain", round(y_te.mean(), 3))
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=0, stratify=y)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
    scores = cross_val_score(LogisticRegression(), X_tr, y_tr, cv=cv)
    print(scores.round(3), round(scores.mean(), 3), round(scores.std(), 3))
    """, "split.py"),
)

section("pipelines", "Pipelines and ColumnTransformer",
    p("""A **`Pipeline`** chains steps into one estimator: `Pipeline([("scale", StandardScaler()), ("clf", LogisticRegression())])`. Calling `fit` fits each transformer on
    the training data and passes the transformed data to the next step; `predict` applies the **already fitted** transformers and then the model. Inside
    `cross_val_score`, the whole pipeline is refitted on each training fold, so scaling, imputation and encoding statistics never see the fold being scored.
    That makes the commonest leakage (preprocessing fitted on all the data before splitting) impossible by construction, and it means the object you save is
    the complete recipe from raw columns to prediction."""),
    p("""Real tables mix types, and each needs different treatment. A **`ColumnTransformer`** applies a transformer to a list of columns, in parallel: numeric columns
    get `SimpleImputer(strategy="median")` then `StandardScaler()`, categorical ones `SimpleImputer(strategy="most_frequent")` then
    `OneHotEncoder(handle_unknown="ignore")` (the safe one-hot of D.4), and text columns a vectoriser. The outputs are placed side by side as one feature matrix.
    Parameters of inner steps are addressed with double underscores: `clf__C`, `prep__num__impute__strategy`."""),
    fig(flowchart({
        "raw": ("start", 1, 0, "raw complaints table"),
        "num": ("step", 0, 1, "amount, days:|impute median, scale"),
        "cat": ("step", 1, 1, "product, state:|impute, one-hot"),
        "txt": ("step", 2, 1, "narrative:|TF-IDF"),
        "mat": ("accent", 1, 2, "one feature matrix"),
        "clf": ("end", 1, 3, "LogisticRegression"),
    }, [("raw", "num", "", {"route": "hv"}), ("raw", "cat"), ("raw", "txt", "", {"route": "hv"}),
        ("num", "mat", "", {"route": "vh"}), ("cat", "mat"), ("txt", "mat", "", {"route": "vh"}), ("mat", "clf")],
        cell=(220, 80), label="a ColumnTransformer inside a Pipeline"),
        "Each column group gets its own preprocessing; the pipeline fits all of it on training data only."),
    ex("""
    import pandas as pd
    from sklearn.compose import ColumnTransformer
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler

    df = pd.DataFrame({"amount": [20, None, 300, 1200, 15, 250, 80, 40],
                       "product": ["card", "card", "mortgage", "mortgage", "card", None, "loan", "card"],
                       "urgent": [0, 0, 1, 1, 0, 1, 0, 0]})
    num = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())])
    cat = Pipeline([("impute", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore"))])
    prep = ColumnTransformer([("num", num, ["amount"]), ("cat", cat, ["product"])])
    model = Pipeline([("prep", prep), ("clf", LogisticRegression())])
    model.fit(df[["amount", "product"]], df["urgent"])
    print(model.named_steps["prep"].get_feature_names_out().tolist())
    new = pd.DataFrame({"amount": [900, None], "product": ["crypto", "card"]})
    print(model.predict(new), model.predict_proba(new)[:, 1].round(3))
    print(model.named_steps["prep"].named_transformers_["num"].named_steps["impute"].statistics_)
    print(sorted(k for k in model.get_params() if k.startswith("clf__"))[:3])
    """, "pipeline.py"),
    p("""The unseen product `crypto` did not break anything: `handle_unknown="ignore"` encodes it as all zeros, and the missing amount was filled with the training
    median (printed on the third line). `get_feature_names_out` shows the columns the model actually sees. The parameter names printed last are what a grid
    search uses."""),
)

section("metrics", "Metrics and the baseline to beat",
    p("""**Accuracy** is the fraction of correct predictions, and it is misleading when classes are imbalanced: if 5% of complaints are urgent, a model that never
    predicts "urgent" is 95% accurate and useless. So start every project with a **baseline**, `DummyClassifier(strategy="most_frequent")`, and report metrics
    that look at the class you care about. **Precision**: of the complaints flagged urgent, how many were? **Recall**: of the urgent complaints, how many were
    flagged? **F1** is their harmonic mean. Which matters more is a business choice: missing an urgent fraud case (low recall) usually costs more than reviewing a
    false alarm (low precision). `classification_report` prints all of them per class, and `confusion_matrix` gives the counts behind them."""),
    p("""Threshold-free metrics judge the **scores** rather than one cut-off: **ROC AUC** is the probability that a random positive gets a higher score than a random
    negative (0.5 is chance), and **average precision** (the area under the precision-recall curve) is more informative when positives are rare. With
    imbalance, `class_weight="balanced"` makes the model pay more attention to the rare class, and choosing the threshold from a precision-recall curve (D.5)
    sets the operating point."""),
    fig(table(["", "predicted urgent", "predicted normal"], [
        ["truly urgent", "TP: caught", "FN: missed"],
        ["truly normal", "FP: false alarm", "TN: correctly ignored"],
    ], hl={(0, 2), (1, 1)}, label="precision = TP / (TP + FP), recall = TP / (TP + FN)"),
        "Precision looks down the first column, recall along the first row."),
    ex("""
    import numpy as np
    from sklearn.dummy import DummyClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, average_precision_score, classification_report, confusion_matrix, f1_score, roc_auc_score
    from sklearn.model_selection import train_test_split

    rng = np.random.default_rng(1)
    X = rng.normal(size=(2_000, 4))
    y = (X[:, 0] + X[:, 1] + rng.normal(scale=1.0, size=2_000) > 2.6).astype(int)
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, stratify=y, random_state=0)
    print("urgent share:", round(y.mean(), 3))
    for name, m in [("baseline", DummyClassifier(strategy="most_frequent")),
                    ("logreg", LogisticRegression()),
                    ("balanced", LogisticRegression(class_weight="balanced"))]:
        p = m.fit(X_tr, y_tr).predict(X_te)
        print(name, round(accuracy_score(y_te, p), 3), round(f1_score(y_te, p, zero_division=0), 3))
    model = LogisticRegression().fit(X_tr, y_tr)
    s = model.predict_proba(X_te)[:, 1]
    print(confusion_matrix(y_te, model.predict(X_te)).tolist())
    print(round(roc_auc_score(y_te, s), 3), round(average_precision_score(y_te, s), 3))
    print(classification_report(y_te, model.predict(X_te), digits=2).splitlines()[3])
    """, "metrics.py"),
    p("""Read the output against the baseline: always predicting "not urgent" is already about 94% accurate with an F1 of 0, so the plain model's 97% is a smaller
    step than it looks, and its confusion matrix shows 13 urgent complaints missed. The `balanced` model scored **worse** here: class weights push predictions
    towards the rare class at the default 0.5 threshold, and on this data that cost more precision than it gained in recall. Class weights move the trade-off;
    they do not add signal, so compare them with cross-validation and a chosen threshold rather than assuming they help."""),
)

section("text", "A text classifier and a hyperparameter search",
    p("""For text, **`TfidfVectorizer`** turns documents into sparse vectors: one column per word (or word pair, with `ngram_range=(1, 2)`), weighted by how often the word
    appears in the document and how rare it is across documents, so `the` counts for little and `foreclosure` for a lot. Followed by `LogisticRegression`, it is
    the strong, fast, explainable baseline for complaint routing that any LLM-based classifier should be compared against: it trains in seconds, runs anywhere,
    and its coefficients show which words drive each class."""),
    p("""**Hyperparameters** (the regularisation strength `C`, the n-gram range, the minimum document frequency) are chosen by search, never on the test set.
    **`GridSearchCV(pipeline, param_grid, cv=...)`** tries every combination with cross-validation inside the training data, refits the best on all of it, and
    exposes `best_params_`, `best_score_` and the refitted `best_estimator_`. Because the vectoriser is inside the pipeline, its vocabulary is rebuilt per fold,
    so no word statistics leak from validation folds."""),
    ex("""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import GridSearchCV
    from sklearn.pipeline import Pipeline

    texts = ["charged twice for one payment", "unauthorized charge on my card", "card charged a fee I never agreed to",
             "refund for duplicate charge not received", "mortgage escrow payment increased", "lender lost my mortgage payment",
             "foreclosure notice sent in error", "escrow account shortage on my mortgage",
             "student loan servicer misapplied payment", "loan forgiveness application ignored", "student loan interest is wrong",
             "servicer put my loan in forbearance"]
    labels = ["card"] * 4 + ["mortgage"] * 4 + ["student loan"] * 4
    pipe = Pipeline([("tfidf", TfidfVectorizer()), ("clf", LogisticRegression(max_iter=1000))])
    search = GridSearchCV(pipe, {"clf__C": [0.1, 1, 10], "tfidf__ngram_range": [(1, 1), (1, 2)]}, cv=4)
    search.fit(texts, labels)
    print(search.best_params_, round(search.best_score_, 3))
    best = search.best_estimator_
    print(best.predict(["my card was charged for something I did not buy", "escrow went up again", "my loan servicer ignored me"]).tolist())
    vocab = best.named_steps["tfidf"].get_feature_names_out()
    coef = best.named_steps["clf"].coef_
    for cls, row in zip(best.classes_, coef):
        print(cls, [vocab[i] for i in row.argsort()[::-1][:3]])
    """, "text_model.py"),
)

section("warmup", "Warm-up",
    predict("The estimator contract", "easy",
        code="""
        import numpy as np
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import StandardScaler

        X = np.array([[1.0], [2.0], [3.0], [4.0]])
        y = np.array([0, 0, 1, 1])
        m = LogisticRegression()
        print(hasattr(m, "coef_"), m.fit(X, y) is m, hasattr(m, "coef_"))
        print(m.classes_.tolist(), m.predict([[0.0], [5.0]]).tolist(), m.predict_proba([[2.5]]).round(2).tolist())
        s = StandardScaler().fit(X)
        print(s.mean_.tolist(), s.transform([[2.5]]).tolist())
        print(StandardScaler().fit_transform([[10.0], [20.0]]).ravel().tolist())
        print(m.get_params()["C"], LogisticRegression(C=5).get_params()["C"])
        """,
        hints=["Learned attributes only exist after `fit`. Halfway between the two classes, a symmetric problem gives probability 0.5 for each."],
        why="""An unfitted estimator has only its settings; `coef_` appears after `fit`, which returns the estimator itself so calls can be chained. The classes are sorted,
        and `predict_proba` columns follow that order. The data is symmetric around 2.5, so that point gets 0.5 for both classes. The scaler learned the mean 2.5,
        so 2.5 transforms to 0. Two values 10 and 20 standardise to -1 and 1 (scikit-learn's `std` divides by `n`, not `n - 1`). `get_params` returns the
        hyperparameters, here the default `C=1.0` and an explicit 5."""),
    predict("Stratified or not", "easy",
        code="""
        import numpy as np
        from sklearn.model_selection import train_test_split, StratifiedKFold

        y = np.array([1] * 10 + [0] * 90)
        X = np.arange(100).reshape(-1, 1)
        _, _, _, plain = train_test_split(X, y, test_size=0.2, random_state=4)
        _, _, _, strat = train_test_split(X, y, test_size=0.2, random_state=4, stratify=y)
        print(len(plain), int(plain.sum()), int(strat.sum()))
        folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=0).split(X, y)
        print([int(y[test].sum()) for _, test in folds])
        _, X_te, _, _ = train_test_split(X, y, test_size=0.2, shuffle=False)
        print(X_te.ravel().tolist()[:3], int(y[80:].sum()))
        """,
        hints=["Stratification keeps the 10% positive rate in every part: 2 of 20. Without shuffling, the test set is simply the last 20 rows."],
        why="""A plain random split leaves the number of positives in the test set to chance, so the test estimate is noisy. Stratifying keeps the proportion: 2 of 20.
        Stratified folds put exactly 2 positives in each of the five folds. With `shuffle=False` the test set is the last 20 rows, which here contain no positives at
        all, because the data is sorted by label, an extreme version of why sorted data must be shuffled (or, for time series, split deliberately by time)."""),
    write("Beat the baseline", "easy", tag="ML",
        prompt="""Write `compare_to_baseline(X, y, seed=0)`: split with `test_size=0.25`, stratified, `random_state=seed`; fit a `DummyClassifier(strategy="most_frequent")` and a
        `LogisticRegression(max_iter=1000)` on the training part; return a dict `{"baseline": {...}, "model": {...}}` where each inner dict has `accuracy`, `recall`
        and `f1` for the positive class 1 on the test part, rounded to 3 (use `zero_division=0`).""",
        code="""
        from sklearn.linear_model import LogisticRegression


        def compare_to_baseline(X, y, seed=0):
            m = LogisticRegression().fit(X, y)
            return {"model": {"accuracy": m.score(X, y)}}
        """,
        tests="""
        import numpy as np
        rng = np.random.default_rng(2)
        X = rng.normal(size=(800, 3))
        y = (X[:, 0] - X[:, 2] + rng.normal(scale=0.7, size=800) > 1.8).astype(int)
        r = compare_to_baseline(X, y)
        assert set(r) == {"baseline", "model"} and set(r["model"]) == {"accuracy", "recall", "f1"}
        assert r["baseline"]["recall"] == 0.0 and r["baseline"]["f1"] == 0.0
        assert abs(r["baseline"]["accuracy"] - (1 - y.mean())) < 0.01
        assert r["model"]["f1"] > 0.5 and r["model"]["recall"] > r["baseline"]["recall"]
        assert r["model"]["accuracy"] - r["baseline"]["accuracy"] < 0.15
        """,
        hints=["`train_test_split(X, y, test_size=0.25, stratify=y, random_state=seed)`.", "`from sklearn.metrics import accuracy_score, recall_score, f1_score`."],
        solution="""
        from sklearn.dummy import DummyClassifier
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import accuracy_score, f1_score, recall_score
        from sklearn.model_selection import train_test_split


        def compare_to_baseline(X, y, seed=0):
            X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, stratify=y, random_state=seed)
            out = {}
            for name, est in [("baseline", DummyClassifier(strategy="most_frequent")), ("model", LogisticRegression(max_iter=1000))]:
                p = est.fit(X_tr, y_tr).predict(X_te)
                out[name] = {"accuracy": round(accuracy_score(y_te, p), 3),
                             "recall": round(recall_score(y_te, p, zero_division=0), 3),
                             "f1": round(f1_score(y_te, p, zero_division=0), 3)}
            return out
        """,
        why="""The starter scored the model on the data it was trained on, which measures memory, and gave no reference point. When positives are rare, "always negative" is
        already highly accurate, so the model's accuracy looks only a few points better, as the last test checks; recall and F1 for the positive class show the
        real difference (the baseline catches nothing). Every model report should include a baseline row; it also catches pipelines that are broken in a way that
        makes them predict one class."""),
)

section("medium", "Medium",
    fix("A selector that has seen the validation folds", "medium", tag="ML",
        prompt="""`evaluate` reports a cross-validated accuracy, but the scaler and the feature selection were fitted on **all** the data before cross-validation, so
        information from every validation fold leaked into training. Rewrite it with a `Pipeline` so that scaling and `SelectKBest(k=5)` are refitted inside each fold,
        and return the mean of `cross_val_score` with the given `cv`, rounded to 3. The function must also return the pipeline fitted on all the data as the second
        value.""",
        code="""
        from sklearn.feature_selection import SelectKBest
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import cross_val_score
        from sklearn.preprocessing import StandardScaler


        def evaluate(X, y, cv):
            Xs = StandardScaler().fit_transform(X)
            Xk = SelectKBest(k=5).fit_transform(Xs, y)
            model = LogisticRegression(max_iter=1000)
            score = cross_val_score(model, Xk, y, cv=cv).mean()
            return round(score, 3), model.fit(Xk, y)
        """,
        tests="""
        import numpy as np
        from sklearn.model_selection import StratifiedKFold
        from sklearn.pipeline import Pipeline
        rng = np.random.default_rng(7)
        X = rng.normal(size=(60, 500))
        y = rng.integers(0, 2, 60)
        cv = StratifiedKFold(5, shuffle=True, random_state=0)
        score, model = evaluate(X, y, cv)
        assert isinstance(model, Pipeline) and len(model.steps) == 3
        assert score < 0.7
        assert model.predict(X[:3]).shape == (3,)
        assert hasattr(model.named_steps[model.steps[1][0]], "scores_")
        """,
        hints=["`Pipeline([(\"scale\", StandardScaler()), (\"select\", SelectKBest(k=5)), (\"clf\", LogisticRegression(max_iter=1000))])`.", "Pass the raw `X` to `cross_val_score`."],
        solution="""
        from sklearn.feature_selection import SelectKBest
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import cross_val_score
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler


        def evaluate(X, y, cv):
            pipe = Pipeline([("scale", StandardScaler()), ("select", SelectKBest(k=5)),
                             ("clf", LogisticRegression(max_iter=1000))])
            score = cross_val_score(pipe, X, y, cv=cv).mean()
            return round(float(score), 3), pipe.fit(X, y)
        """,
        why="""The test data is pure noise: 500 random features and random labels, so the honest answer is about 50% accuracy. Selecting the 5 features most correlated
        with the labels **on all 60 rows** finds features that happen to correlate with the labels of the validation folds too, so the leaky version reports a
        score far above chance on data with no signal at all. That is selection leakage, a famous failure in genomics and in any wide dataset. Inside a pipeline,
        `cross_val_score` refits the scaler and the selector on each training fold only, and the score drops back to chance, as the test requires. The same
        applies to imputation, encoding, TF-IDF vocabularies, and oversampling."""),
    write("A pipeline for a mixed complaints table", "medium", tag="ML",
        prompt="""Write `build_model(numeric, categorical)` returning an unfitted `Pipeline` with steps named `"prep"` and `"clf"`: `"prep"` is a `ColumnTransformer` with a
        `"num"` part (median imputation then standard scaling) for the `numeric` columns and a `"cat"` part (most-frequent imputation then
        `OneHotEncoder(handle_unknown="ignore")`) for the `categorical` columns; `"clf"` is `LogisticRegression(max_iter=1000, class_weight="balanced")`. The model must
        train on a DataFrame with missing values and predict for rows with categories never seen in training.""",
        code="""
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline


        def build_model(numeric, categorical):
            return Pipeline([("clf", LogisticRegression())])
        """,
        tests="""
        import numpy as np
        import pandas as pd
        rng = np.random.default_rng(8)
        n = 300
        df = pd.DataFrame({"amount": rng.lognormal(4, 1, n), "days": rng.integers(0, 60, n).astype(float),
                           "product": rng.choice(["card", "loan", "mortgage"], n), "channel": rng.choice(["web", "phone"], n)})
        df.loc[::10, "amount"] = np.nan
        df.loc[::7, "product"] = None
        y = ((df["product"] == "mortgage") & (df["days"] > 20)).astype(int)
        model = build_model(["amount", "days"], ["product", "channel"])
        assert [s[0] for s in model.steps] == ["prep", "clf"]
        model.fit(df, y)
        new = pd.DataFrame({"amount": [np.nan, 50.0], "days": [40.0, 1.0], "product": ["mortgage", "crypto"], "channel": ["fax", "web"]})
        assert model.predict(new).tolist() == [1, 0]
        names = model.named_steps["prep"].get_feature_names_out().tolist()
        assert "num__amount" in names and "cat__product_mortgage" in names
        assert model.named_steps["clf"].class_weight == "balanced"
        """,
        hints=["`ColumnTransformer([(\"num\", num_pipe, numeric), (\"cat\", cat_pipe, categorical)])`.", "Each part is itself a small `Pipeline` of an imputer and a scaler or encoder."],
        solution="""
        from sklearn.compose import ColumnTransformer
        from sklearn.impute import SimpleImputer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import OneHotEncoder, StandardScaler


        def build_model(numeric, categorical):
            num = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())])
            cat = Pipeline([("impute", SimpleImputer(strategy="most_frequent")),
                            ("onehot", OneHotEncoder(handle_unknown="ignore"))])
            prep = ColumnTransformer([("num", num, list(numeric)), ("cat", cat, list(categorical))])
            return Pipeline([("prep", prep), ("clf", LogisticRegression(max_iter=1000, class_weight="balanced"))])
        """,
        why="""This is the standard shape of a tabular model, and it encodes every lesson of this module: imputation statistics and scaling learned from training data
        (D.2), one-hot categories fixed at fit time with unknowns ignored (D.4), and a model that does not ignore the rare class. Because it is one estimator, it
        can be cross-validated, grid-searched, pickled and served as a unit: the serving code passes a raw DataFrame and gets a prediction, with no separate
        preprocessing script to keep in sync. Feature names such as `num__amount` and `cat__product_mortgage` come from the step names, which makes coefficients and
        feature importances readable."""),
    write("Metrics that tell the truth on imbalanced data", "medium", tag="ML",
        prompt="""Write `report(y_true, scores, threshold=0.5)` for binary labels and predicted probabilities. Return a dict with `accuracy`, `precision`, `recall`, `f1`
        (for class 1, predicting 1 when the score is at least the threshold, `zero_division=0`), `roc_auc`, `average_precision`, the confusion counts `tp`, `fp`,
        `fn`, `tn` as ints, and `base_rate` (the share of positives), all floats rounded to 3. Use `sklearn.metrics`.""",
        code="""
        from sklearn.metrics import accuracy_score


        def report(y_true, scores, threshold=0.5):
            pred = [1 if s > 0.5 else 0 for s in scores]
            return {"accuracy": accuracy_score(y_true, pred)}
        """,
        tests="""
        import numpy as np
        y = np.array([0] * 90 + [1] * 10)
        s = np.r_[np.linspace(0.0, 0.6, 90), np.linspace(0.4, 0.9, 10)]
        r = report(y, s)
        tp, fp, fn, tn = int(((s >= 0.5) & (y == 1)).sum()), int(((s >= 0.5) & (y == 0)).sum()), int(((s < 0.5) & (y == 1)).sum()), int(((s < 0.5) & (y == 0)).sum())
        assert r["base_rate"] == 0.1 and (r["tp"], r["fp"], r["fn"], r["tn"]) == (tp, fp, fn, tn)
        assert r["accuracy"] == round((tp + tn) / 100, 3) and r["precision"] == round(tp / (tp + fp), 3) and r["recall"] == round(tp / 10, 3)
        assert 0.9 < r["roc_auc"] < 1.0 and r["average_precision"] < r["roc_auc"]
        assert report(y, s, threshold=0.65)["fp"] == 0
        assert all(isinstance(r[k], int) for k in ("tp", "fp", "fn", "tn"))
        """,
        hints=["`pred = (np.asarray(scores) >= threshold).astype(int)`; `confusion_matrix(y, pred, labels=[0, 1]).ravel()` returns `tn, fp, fn, tp`."],
        solution="""
        import numpy as np
        from sklearn.metrics import (accuracy_score, average_precision_score, confusion_matrix, f1_score,
                                     precision_score, recall_score, roc_auc_score)


        def report(y_true, scores, threshold=0.5):
            y = np.asarray(y_true)
            s = np.asarray(scores, dtype=float)
            pred = (s >= threshold).astype(int)
            tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
            r = lambda v: round(float(v), 3)
            return {
                "accuracy": r(accuracy_score(y, pred)),
                "precision": r(precision_score(y, pred, zero_division=0)),
                "recall": r(recall_score(y, pred, zero_division=0)),
                "f1": r(f1_score(y, pred, zero_division=0)),
                "roc_auc": r(roc_auc_score(y, s)),
                "average_precision": r(average_precision_score(y, s)),
                "tp": int(tp), "fp": int(fp), "fn": int(fn), "tn": int(tn),
                "base_rate": r(y.mean()),
            }
        """,
        why="""Each number answers a different question, and a report needs them together. The base rate (10%) is the context for accuracy: a score in the 80s sounds fine
        until you see that always predicting "no" would score 90%. Low precision says most flags are false alarms, recall says what share of urgent cases is
        caught, and a ROC AUC above 0.9 says the scores rank cases well, so the problem is the threshold: raising it to 0.65 removes every false positive here.
        Average precision is lower than ROC AUC because it focuses on the rare class, where the errors are. `confusion_matrix(...).ravel()` returns the counts in the
        order `tn, fp, fn, tp`, and passing `labels=[0, 1]` keeps that order even if a batch contains only one class. The starter's `>` instead of `>=` also
        silently changes results at scores equal to the threshold."""),
    write("Route complaints with TF-IDF and logistic regression", "medium", tag="GenAI",
        prompt="""Write `train_router(texts, labels)` returning a fitted `Pipeline` of `TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)` and
        `LogisticRegression(max_iter=1000)`, and `explain(model, k=3)` returning a dict from each class to its `k` highest-weighted features (words or word pairs), in
        order. Then write `route(model, texts, min_confidence)` returning, for each text, the predicted class, or `"human review"` when the highest class probability is
        below `min_confidence`.""",
        code="""
        def train_router(texts, labels):
            return None


        def explain(model, k=3):
            return {}


        def route(model, texts, min_confidence):
            return ["human review"] * len(texts)
        """,
        tests="""
        texts = ["charged twice on my card", "card fee I never agreed to", "unauthorized card charge", "card statement wrong",
                 "mortgage escrow went up", "lender lost mortgage payment", "foreclosure notice in error", "mortgage payment misapplied",
                 "student loan servicer ignored me", "loan forgiveness denied", "student loan interest wrong", "loan servicer forbearance"]
        labels = ["card"] * 4 + ["mortgage"] * 4 + ["loan"] * 4
        model = train_router(texts, labels)
        assert model.predict(["my card was charged twice"]).tolist() == ["card"]
        ex = explain(model, k=2)
        assert set(ex) == {"card", "loan", "mortgage"} and all(len(v) == 2 for v in ex.values())
        assert "card" in ex["card"] and "mortgage" in ex["mortgage"]
        out = route(model, ["mortgage escrow payment lost", "hello there"], 0.5)
        assert out == ["mortgage", "human review"]
        """,
        hints=["`vocab = model.named_steps[...].get_feature_names_out()`; for each class row of `coef_`, `argsort()[::-1][:k]`.",
               "`proba = model.predict_proba(texts)`; `proba.max(axis=1)` is the confidence and `model.classes_[proba.argmax(axis=1)]` the class."],
        solution="""
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline


        def train_router(texts, labels):
            pipe = Pipeline([("tfidf", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)),
                             ("clf", LogisticRegression(max_iter=1000))])
            return pipe.fit(texts, labels)


        def explain(model, k=3):
            vocab = model.named_steps["tfidf"].get_feature_names_out()
            coef = model.named_steps["clf"].coef_
            return {cls: [vocab[i] for i in row.argsort()[::-1][:k]] for cls, row in zip(model.classes_, coef)}


        def route(model, texts, min_confidence):
            proba = model.predict_proba(texts)
            best = model.classes_[proba.argmax(axis=1)]
            return [str(c) if p >= min_confidence else "human review" for c, p in zip(best, proba.max(axis=1))]
        """,
        why="""TF-IDF plus logistic regression is the baseline every LLM classifier should beat: it trains in milliseconds, costs nothing per prediction, and is explainable,
        because each class has one weight per word and the largest weights read like a summary of the class. `sublinear_tf` dampens repeated words and bigrams catch
        phrases such as "student loan". The routing rule adds a confidence gate: a text that shares no vocabulary with the training data ("hello there") gets nearly
        uniform probabilities (about a third each), so it goes to a person instead of being forced into a queue. The same pattern (a cheap model first, a
        fallback for low confidence) is common in LLM systems, where the fallback is the expensive model or a human."""),
    choose("Predict one row at a time or in one batch", "medium", tag="ML",
        prompt="Both score 2,000 complaints with a fitted pipeline. Which is faster?",
        setup="""import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
rng = np.random.default_rng(0)
X = rng.normal(size=(2_000, 10))
y = (X[:, 0] > 0).astype(int)
model = make_pipeline(StandardScaler(), LogisticRegression()).fit(X, y)""",
        options={
            "a": "preds = [model.predict(row.reshape(1, -1))[0] for row in X]",
            "b": "preds = model.predict(X)",
        },
        answer="b",
        hints=["Every `predict` call validates its input and runs each pipeline step, whatever the number of rows."],
        why="""Each `predict` call has a fixed overhead: input validation, dtype checks, and one call per pipeline step, before a tiny amount of arithmetic. Option A pays it
        2,000 times; option B pays it once and does the arithmetic as one matrix product. In a web service that scores requests one by one this overhead is the
        latency floor, which is why batch jobs, and services that micro-batch concurrent requests, are far more efficient."""),
    write("A cross-validation report", "medium", tag="ML",
        prompt="""Write `cv_report(models, X, y, folds=5, seed=0)` where `models` is a dict from name to unfitted estimator. Use `cross_validate` with
        `StratifiedKFold(folds, shuffle=True, random_state=seed)` and the scorers `"accuracy"`, `"f1"` and `"roc_auc"`, and return a DataFrame indexed by model
        name with columns `accuracy_mean`, `accuracy_std`, `f1_mean`, `f1_std`, `roc_auc_mean`, `roc_auc_std` (rounded to 3), sorted by `f1_mean` descending.""",
        code="""
        import pandas as pd


        def cv_report(models, X, y, folds=5, seed=0):
            return pd.DataFrame({name: {"f1_mean": 0.0} for name in models}).T
        """,
        tests="""
        import numpy as np
        from sklearn.dummy import DummyClassifier
        from sklearn.linear_model import LogisticRegression
        from sklearn.tree import DecisionTreeClassifier
        rng = np.random.default_rng(9)
        X = rng.normal(size=(300, 4))
        y = (X[:, 0] + X[:, 1] > 0.8).astype(int)
        rep = cv_report({"dummy": DummyClassifier(strategy="most_frequent"), "logreg": LogisticRegression(),
                         "tree": DecisionTreeClassifier(max_depth=3, random_state=0)}, X, y)
        assert list(rep.columns) == ["accuracy_mean", "accuracy_std", "f1_mean", "f1_std", "roc_auc_mean", "roc_auc_std"]
        assert rep.index[0] == "logreg" and rep.index[-1] == "dummy"
        assert rep.loc["dummy", "f1_mean"] == 0.0 and rep.loc["dummy", "roc_auc_mean"] == 0.5
        assert rep.loc["logreg", "roc_auc_mean"] > 0.95 and (rep.filter(like="_std") >= 0).all().all()
        """,
        hints=["`cross_validate(est, X, y, cv=cv, scoring=[\"accuracy\", \"f1\", \"roc_auc\"])` returns arrays under keys such as `test_f1`."],
        solution="""
        import pandas as pd
        from sklearn.model_selection import StratifiedKFold, cross_validate


        def cv_report(models, X, y, folds=5, seed=0):
            cv = StratifiedKFold(folds, shuffle=True, random_state=seed)
            rows = {}
            for name, est in models.items():
                res = cross_validate(est, X, y, cv=cv, scoring=["accuracy", "f1", "roc_auc"])
                rows[name] = {f"{m}_{stat}": round(float(getattr(res[f"test_{m}"], stat)()), 3)
                              for m in ("accuracy", "f1", "roc_auc") for stat in ("mean", "std")}
            return pd.DataFrame.from_dict(rows, orient="index").sort_values("f1_mean", ascending=False)
        """,
        why="""Comparing models on one split mixes up model quality with the luck of the split; five folds give five scores per model, and the standard deviation says how
        much of a difference is noise (two models whose means differ by less than their spread are not clearly different). Using the **same** `cv` object with a
        fixed seed for every model means they are scored on identical folds, a fair comparison. Several scorers at once show trade-offs, and the dummy row
        anchors the table: an F1 of 0 and an AUC of 0.5 are what "no skill" looks like."""),
)

section("hard", "Hard",
    write("Tune a pipeline, then test it once", "hard", tag="ML",
        prompt="""Write `tune_and_test(X, y, seed=0)`: hold out 25% as a stratified test set; on the training part run `GridSearchCV` over a pipeline of `StandardScaler` and
        `LogisticRegression(max_iter=1000)` with `C` in `[0.01, 0.1, 1, 10]` and `class_weight` in `[None, "balanced"]`, scoring `"f1"`, with `StratifiedKFold(5,
        shuffle=True, random_state=seed)`; return a dict with `best_params` (the parameter dict with the step prefix removed, such as `{"C": 1, "class_weight":
        "balanced"}`), `cv_f1` (best cross-validated F1, rounded to 3) and `test_f1` (F1 of the refitted best model on the test set, rounded to 3).""",
        code="""
        from sklearn.linear_model import LogisticRegression


        def tune_and_test(X, y, seed=0):
            best = None
            for C in [0.01, 0.1, 1, 10]:
                m = LogisticRegression(C=C).fit(X, y)
                if best is None or m.score(X, y) > best.score(X, y):
                    best = m
            return {"best_params": {"C": best.C}}
        """,
        tests="""
        import numpy as np
        rng = np.random.default_rng(10)
        X = rng.normal(size=(600, 5))
        y = (X[:, 0] + 0.6 * X[:, 1] + rng.normal(scale=0.8, size=600) > 1.9).astype(int)
        r = tune_and_test(X, y)
        assert set(r) == {"best_params", "cv_f1", "test_f1"}
        assert set(r["best_params"]) == {"C", "class_weight"} and r["best_params"]["class_weight"] in (None, "balanced")
        assert r["best_params"]["C"] in (0.01, 0.1, 1, 10)
        assert 0.4 < r["cv_f1"] < 1 and 0.4 < r["test_f1"] < 1
        assert r == tune_and_test(X, y)
        """,
        hints=["Name the steps, for example `\"clf\"`, and use `{\"clf__C\": [...], \"clf__class_weight\": [...]}` as the grid.",
               "`search.best_params_` has keys like `clf__C`; `k.split(\"__\", 1)[1]` removes the prefix. `search.predict(X_te)` uses the refitted best model."],
        solution="""
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import f1_score
        from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler


        def tune_and_test(X, y, seed=0):
            X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, stratify=y, random_state=seed)
            pipe = Pipeline([("scale", StandardScaler()), ("clf", LogisticRegression(max_iter=1000))])
            grid = {"clf__C": [0.01, 0.1, 1, 10], "clf__class_weight": [None, "balanced"]}
            search = GridSearchCV(pipe, grid, scoring="f1", cv=StratifiedKFold(5, shuffle=True, random_state=seed))
            search.fit(X_tr, y_tr)
            params = {k.split("__", 1)[1]: v for k, v in search.best_params_.items()}
            return {"best_params": params, "cv_f1": round(float(search.best_score_), 3),
                    "test_f1": round(float(f1_score(y_te, search.predict(X_te))), 3)}
        """,
        why="""The starter chose `C` by accuracy on the training data, which rewards memorising and ignores the minority class. The grid search compares all eight settings by
        cross-validated F1 inside the training set, so the choice reflects the rare class the F1 objective cares about, whichever setting wins. The
        cross-validated score of the winner is slightly optimistic (it was the maximum over eight noisy estimates), which is why the test set exists: scored once,
        at the end, it is the number to report. Fixed seeds everywhere make the whole procedure repeatable, which the last test checks."""),
    write("Your own transformer for text statistics", "hard", tag="GenAI",
        prompt="""Write a transformer `TextStats(BaseEstimator, TransformerMixin)` that turns a list (or Series) of texts into a float array with four columns: number of words,
        mean word length, share of characters that are upper-case letters (rounded to 4), and number of redaction markers (words of two or more `X`, as in D.4),
        with `get_feature_names_out()` returning `["n_words", "mean_word_len", "upper_share", "n_redactions"]`. It learns nothing, but `fit` must return `self`. Then
        write `text_model()` returning a `Pipeline` that feeds the same texts to both a `TfidfVectorizer` and `TextStats` followed by `StandardScaler`, combined with
        `FeatureUnion`, into `LogisticRegression(max_iter=1000)`.""",
        code="""
        from sklearn.base import BaseEstimator, TransformerMixin


        class TextStats(BaseEstimator, TransformerMixin):
            def transform(self, X):
                return [len(t) for t in X]


        def text_model():
            return None
        """,
        tests="""
        import numpy as np
        ts = TextStats()
        assert ts.fit(["a"]) is ts
        out = ts.transform(["Charged TWICE by XXXX", "ok", ""])
        assert out.shape == (3, 4) and out.dtype == float
        assert out[0].tolist() == [4.0, 4.5, round(10 / 21, 4), 1.0]
        assert out[2].tolist() == [0.0, 0.0, 0.0, 0.0]
        assert ts.get_feature_names_out().tolist() == ["n_words", "mean_word_len", "upper_share", "n_redactions"]
        texts = ["URGENT fraud XXXX charged", "my card was charged twice", "FRAUD on account XXXX XXXX", "fee on statement",
                 "UNAUTHORIZED XXXX transfer", "question about my bill"] * 3
        y = [1, 0, 1, 0, 1, 0] * 3
        m = text_model().fit(texts, y)
        assert m.predict(["FRAUD XXXX now", "a question about a fee"]).tolist() == [1, 0]
        from sklearn.base import clone
        assert clone(ts).get_params() == {}
        """,
        hints=["Compute each row's four numbers in a list comprehension over texts and return `np.array(rows, dtype=float)`.",
               "`FeatureUnion([(\"tfidf\", TfidfVectorizer()), (\"stats\", make_pipeline(TextStats(), StandardScaler()))])`."],
        solution="""
        import re
        import numpy as np
        from sklearn.base import BaseEstimator, TransformerMixin
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import FeatureUnion, Pipeline, make_pipeline
        from sklearn.preprocessing import StandardScaler

        REDACTION = re.compile(r"\\bX{2,}\\b")


        class TextStats(BaseEstimator, TransformerMixin):
            def fit(self, X, y=None):
                return self

            def transform(self, X):
                rows = []
                for t in X:
                    t = t or ""
                    words = t.split()
                    upper = sum(c.isupper() for c in t)
                    rows.append([
                        len(words),
                        float(np.mean([len(w) for w in words])) if words else 0.0,
                        round(upper / len(t), 4) if t else 0.0,
                        len(REDACTION.findall(t)),
                    ])
                return np.array(rows, dtype=float).reshape(-1, 4)

            def get_feature_names_out(self, input_features=None):
                return np.array(["n_words", "mean_word_len", "upper_share", "n_redactions"], dtype=object)


        def text_model():
            features = FeatureUnion([("tfidf", TfidfVectorizer()),
                                     ("stats", make_pipeline(TextStats(), StandardScaler()))])
            return Pipeline([("features", features), ("clf", LogisticRegression(max_iter=1000))])
        """,
        why="""Anything that follows the contract (`fit` returning `self`, `transform` returning a 2-D array) plugs into pipelines, cross-validation and grid search.
        Inheriting from `BaseEstimator` provides `get_params` and `set_params` from the `__init__` arguments (none here, so `clone` gives an empty dict), and
        `TransformerMixin` provides `fit_transform`. A stateless transformer still needs `fit`, because pipelines call it. `FeatureUnion` runs both branches on the
        same input and concatenates their columns, so the model sees the sparse word features and four dense style features side by side; the style features are
        scaled so their size does not dominate. Shouting, redactions and length are signals that a bag of words misses, and in LLM systems the same pattern computes
        cheap features (length, language, presence of personal data) that route requests or flag them for review."""),
    write("How often does the LLM judge agree with people", "hard", tag="GenAI",
        prompt="""An LLM labels complaints, and a sample was also labelled by people. Write `agreement(human, llm, labels)` returning a dict with `accuracy` (share of identical
        labels), `kappa` (Cohen's kappa, `sklearn.metrics.cohen_kappa_score`), `per_label_recall` (a dict from each label to the share of human-labelled items of that
        label that the LLM also gave it), and `top_confusions`, a list of the three most frequent `(human, llm, count)` disagreements, most frequent first, ties broken
        by labels alphabetically. Round floats to 3.""",
        code="""
        def agreement(human, llm, labels):
            same = sum(h == l for h, l in zip(human, llm))
            return {"accuracy": same / len(human)}
        """,
        tests="""
        human = ["card"] * 10 + ["loan"] * 6 + ["mortgage"] * 4
        llm = ["card"] * 8 + ["loan"] * 2 + ["loan"] * 4 + ["card"] * 2 + ["mortgage"] * 3 + ["loan"]
        r = agreement(human, llm, ["card", "loan", "mortgage"])
        assert r["accuracy"] == 0.75
        assert r["per_label_recall"] == {"card": 0.8, "loan": 0.667, "mortgage": 0.75}
        assert r["top_confusions"] == [("card", "loan", 2), ("loan", "card", 2), ("mortgage", "loan", 1)]
        from sklearn.metrics import cohen_kappa_score
        assert r["kappa"] == round(cohen_kappa_score(human, llm), 3) and r["kappa"] < r["accuracy"]
        """,
        hints=["`confusion_matrix(human, llm, labels=labels)` gives counts; recall is the diagonal over the row sums.",
               "Collect off-diagonal cells as `(-count, h, l)` tuples and sort them, then take three."],
        solution="""
        import numpy as np
        from sklearn.metrics import cohen_kappa_score, confusion_matrix


        def agreement(human, llm, labels):
            C = confusion_matrix(human, llm, labels=labels)
            rows = C.sum(axis=1)
            recall = {lab: round(float(C[i, i] / rows[i]), 3) if rows[i] else 0.0 for i, lab in enumerate(labels)}
            off = sorted((-int(C[i, j]), labels[i], labels[j]) for i in range(len(labels)) for j in range(len(labels))
                         if i != j and C[i, j] > 0)
            return {
                "accuracy": round(float(np.trace(C) / C.sum()), 3),
                "kappa": round(float(cohen_kappa_score(human, llm)), 3),
                "per_label_recall": recall,
                "top_confusions": [(h, l, -n) for n, h, l in off[:3]],
            }
        """,
        why="""Before trusting an LLM as a labeller or a judge, measure it against people on a sample, exactly as you would a model. Raw agreement is inflated by chance:
        if most items are `card`, two labellers who both guess `card` often agree. **Cohen's kappa** subtracts the agreement expected from each labeller's label
        frequencies, so 0 means chance and 1 perfect agreement; here 0.75 raw agreement becomes a noticeably lower kappa. Per-label recall shows where the judge is
        weak, and the most frequent confusions tell you what to fix in the prompt or the label definitions (card versus loan is the main confusion in both
        directions). A confusion matrix over the label list keeps every label in a fixed position, including labels that one side never used."""),
    predict("Pipelines, params and clones", "hard",
        code="""
        from sklearn.base import clone
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler

        pipe = make_pipeline(StandardScaler(), LogisticRegression(C=0.5))
        print([name for name, _ in pipe.steps])
        print(pipe.get_params()["logisticregression__C"])
        pipe.set_params(logisticregression__C=2.0)
        print(pipe.named_steps["logisticregression"].C, pipe[-1].C)
        pipe.fit([[0.0], [1.0], [2.0], [3.0]], [0, 0, 1, 1])
        c = clone(pipe)
        print(hasattr(pipe[-1], "coef_"), hasattr(c[-1], "coef_"), c[-1].C)
        print(pipe[:-1].transform([[1.5]]).round(3).tolist())
        try:
            pipe.set_params(logisticregression__alpha=1)
        except ValueError:
            print("ValueError")
        """,
        hints=["`make_pipeline` names steps after the lower-cased class names. `clone` copies the settings but not what was learned."],
        why="""`make_pipeline` names each step after its class in lower case, so parameters are addressed as `logisticregression__C`. `set_params` changes the estimator
        inside the pipeline (indexing `pipe[-1]` gets the same object). `clone` builds a new, unfitted estimator with the same parameters, which is what
        `cross_val_score` and `GridSearchCV` do for every fold: fitted state is never shared between folds. Slicing a pipeline gives a sub-pipeline, here just the
        fitted scaler, whose mean of 1.5 maps 1.5 to 0. An unknown parameter name raises `ValueError`, which catches typos in grid definitions."""),
)

section("interview", "Interview questions",
    explain("What is data leakage, and how do pipelines help prevent it?", "medium", tag="Interview",
        why="""Leakage is any way information that would not be available at prediction time gets into training or model selection, so offline scores are better than
        production performance. Common forms: preprocessing fitted on all data before splitting (scaling, imputation, encoding, TF-IDF vocabularies, feature
        selection, oversampling); target leakage, where a feature is a consequence of the label (a "refund issued" flag when predicting refund requests); temporal
        leakage, training on the future (D.4); duplicate or near-duplicate rows on both sides of a split; and tuning on the test set. A scikit-learn `Pipeline` bundles
        every learned preprocessing step with the model, so `fit` learns them from training data only, and `cross_val_score` or `GridSearchCV` refit the whole
        pipeline per fold, which makes the first form impossible by construction; it also means the deployed object applies exactly the same steps. Pipelines do
        not fix target, temporal or duplicate leakage: those need feature review, time-based splits, group-aware splits (`GroupKFold`) and de-duplication."""),
    explain("Which metric would you use for an imbalanced classification problem, and why not accuracy?", "medium", tag="Interview",
        why="""With imbalance, accuracy is dominated by the majority class: at 2% positives, predicting "negative" always scores 98%. Choose metrics that reflect the cost of
        each error on the class you care about. Precision (how many flagged items are real) matters when false alarms are expensive; recall (how many real items
        are caught) when misses are expensive, such as fraud or safety; F1 or F-beta combine them with a chosen weighting. For the ranking quality of scores,
        average precision (area under the precision-recall curve) is more informative than ROC AUC under heavy imbalance, because ROC AUC can look excellent while
        precision at useful thresholds is poor. Always report the base rate and a baseline, look at the confusion matrix, choose the threshold from the
        precision-recall curve against business constraints ("recall at least 90%"), and use stratified splits and folds so the rare class appears in every
        evaluation. Techniques such as `class_weight="balanced"` or resampling (inside the pipeline) help training, but the metric choice is what keeps evaluation
        honest."""),
    explain("When would you choose a TF-IDF plus logistic regression model over an LLM for text classification?", "hard", tag="Interview",
        why="""When the classes are well defined and there are enough labelled examples (hundreds to thousands), a TF-IDF and logistic regression model is often within a few
        points of an LLM, at a tiny fraction of the cost and latency: it trains in seconds, predicts in microseconds on a CPU, needs no external API (so no data
        leaves your environment), is deterministic, and is explainable through its word weights. It is also the baseline that justifies, or not, an LLM's cost.
        Choose an LLM (zero- or few-shot, or fine-tuned) when labelled data is scarce, labels change often or are defined in natural language, the task needs
        reasoning or world knowledge beyond word overlap, the text is long or multilingual, or you need extraction and explanations, not just a label. Common
        hybrids: an LLM labels data to train a cheap model; a cheap model handles confident cases and routes uncertain ones to the LLM or to people; or embeddings
        from a language model feed a logistic regression. Decide with an evaluation on the same held-out set, including cost per thousand predictions and latency,
        not only accuracy."""),
)

recap(
    "The estimator contract: settings in the constructor, `fit` returns `self`, learned values end in `_`, then `predict`, `predict_proba`, `transform`. Set `random_state`.",
    "Hold out a stratified test set and use it once; compare ideas with cross-validation on the training data (`StratifiedKFold`, or `TimeSeriesSplit` for time).",
    "Put every learned preprocessing step in a `Pipeline` (with a `ColumnTransformer` for mixed columns), so it is refitted per fold and deployed as one object.",
    "Beat a `DummyClassifier`; on imbalanced data report precision, recall, F1, average precision and the base rate, and choose the threshold deliberately.",
    "TF-IDF plus logistic regression is the fast, explainable text baseline; `GridSearchCV` tunes `step__param` names; custom transformers follow `fit`/`transform`.",
)
