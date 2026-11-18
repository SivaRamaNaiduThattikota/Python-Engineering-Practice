from lesson import *

lesson(
    id="m6-2", num="6.2", title="Dict, set and nested comprehensions",
    intro="The same comprehension syntax builds dicts and sets. Duplicate keys and how the last one wins, inverting a "
          "mapping safely, why grouping is the job comprehensions do badly, ordering and determinism, and the "
          "`dict.fromkeys` trap. Applied to label maps, vocabularies, configs, inverted indexes and confusion matrices.",
    desc="`{k: v for ...}` and `{x for ...}`, duplicate keys, grouping, nested dicts, label maps.",
    keys="dict comprehension set comprehension nested comprehension invert mapping duplicate keys last wins label2id id2label vocabulary index grouping fromkeys merge config flatten confusion matrix determinism",
)

term("Dict comprehension", "An expression like `{k: v for k, v in pairs if cond}` that builds a new dict in one step. If a key repeats, the last value wins.")
term("Set comprehension", "An expression like `{f(x) for x in xs}` that builds a set: unique values, no order. `{}` alone is an empty dict, not a set.")
term("Label map", "A pair of dicts, `label2id` and `id2label`, that convert class names to the integer ids a model uses and back.")

section("dict", "Dict comprehensions",
    p("""A **dict comprehension** has the same shape as a list comprehension, with curly braces and a `key: value` pair in front:
    `{key_expr: value_expr for name in iterable if condition}`. It means exactly this loop: start with an empty dict, and for
    every item that passes the condition, evaluate both expressions and **assign** `d[key] = value`. The word "assign"
    matters, as you will see in a moment."""),
    ex("""
    prices = {"gpt-small": 0.15, "gpt-large": 2.50, "embed": 0.02}

    cheap = {}
    for name, price in prices.items():          # the loop
        if price < 1:
            cheap[name] = price * 1000
    cheap2 = {name: price * 1000 for name, price in prices.items() if price < 1}
    print(cheap == cheap2, cheap2)

    words = ["refund", "policy", "reset"]
    print({w: len(w) for w in words}, {i: w for i, w in enumerate(words)})
    print(dict(zip(words, [3, 1, 2])))
    """, "dict_comp.py"),
    p("""The most common sources are `d.items()` (to transform or filter an existing dict, unpacking each pair into two names),
    `enumerate` (to number things) and `zip` (to pair two lists). For a plain pairing with no transformation,
    `dict(zip(keys, values))` is shorter than a comprehension and says the same thing. Remember from 4.1 that `zip` stops at
    the shorter input silently; pass `strict=True` when the lengths must match."""),
    p("""Because each item does `d[key] = value`, a **repeated key overwrites** the earlier value: the last one wins. The key keeps
    the position where it was **first** inserted, though, because assigning to an existing key does not move it (4.5). This is
    the source of a classic bug: inverting a dict whose values are not unique silently loses entries."""),
    ex("""
    pairs = [("a", 1), ("b", 2), ("a", 3)]
    print({k: v for k, v in pairs})
    category = {"faq.md": "billing", "terms.md": "legal", "invoice.md": "billing"}
    print({cat: doc for doc, cat in category.items()})       # loses faq.md
    print(len(category), len({cat: doc for doc, cat in category.items()}))
    """, "last_wins.py"),
    p("""The inverted dict has two keys for three documents: `faq.md` was overwritten by `invoice.md`, with no error. When values
    can repeat, inverting is really **grouping** (one key, several values), which needs a list per key; the next sections show
    why a comprehension is the wrong tool for that and what to use instead (problem 3)."""),
)

section("set", "Set comprehensions",
    p("""A **set comprehension** uses curly braces with a single expression: `{expr for name in iterable if condition}`. It builds a
    set, so duplicates disappear and membership checks are O(1) (4.4). It is the natural way to **transform and deduplicate
    at once**: the distinct domains of a list of emails, the distinct lower-cased words of a text, the ids that appear in a
    log."""),
    ex("""
    emails = ["ana@Example.com", "bo@example.com", "cy@test.io", "dee@EXAMPLE.com"]
    domains = {e.split("@")[1].lower() for e in emails}
    print(sorted(domains), len(domains))
    text = "Refund the refund, then REFUND it"
    print(sorted({w.strip(",").lower() for w in text.split()}))
    print(type({}).__name__, type({1}).__name__, type(set()).__name__, type({x for x in ""}).__name__)
    """, "set_comp.py"),
    p("""Two details catch people. `{}` is an **empty dict**, not an empty set, because dicts came first in Python; an empty set
    is written `set()`. And a set has **no meaningful order**: for strings, the order even changes between runs of the program,
    because string hashes are randomised per process for security (hash randomisation, controlled by the `PYTHONHASHSEED`
    environment variable). So never number, save or display a set without sorting it first; the examples on this page always
    print `sorted(...)`. Building anything from a set, such as ids for labels, without sorting makes the result different on
    every run, which is a real bug in ML code (problem 19)."""),
    p("""Equality also decides what counts as a duplicate: `{1, 1.0, True}` has one element, because `1 == 1.0 == True` and they
    hash the same, while `0.1 + 0.2` and `0.3` are two elements, because they are not equal (1.1). Normalise values (case,
    whitespace, rounding) inside the comprehension when "the same" should mean more than `==`."""),
)

section("group", "Grouping: the job comprehensions do badly",
    p("""A frequent wish is "a dict from each category to the list of its items". You can write it as a nested comprehension,
    `{c: [x for x in items if key(x) == c] for c in categories}`, and it gives the right answer. But look at what it does: for
    **every** category, it scans **all** items. With `n` items and `k` categories that is `n x k` checks, where a single pass
    with a `defaultdict(list)` does `n` (4.6). With 100,000 items and 50 categories, that is 5,000,000 checks instead of
    100,000 (problem 8)."""),
    ex("""
    from collections import defaultdict

    docs = [("faq.md", "billing"), ("terms.md", "legal"), ("invoice.md", "billing"), ("gdpr.md", "legal")]

    cats = sorted({cat for _, cat in docs})
    slow = {c: [d for d, cat in docs if cat == c] for c in cats}     # scans docs once per category

    groups = defaultdict(list)                                       # one pass
    for doc, cat in docs:
        groups[cat].append(doc)
    print(slow, dict(groups), slow == dict(groups))
    """, "grouping.py"),
    p("""So the rule is: a comprehension **transforms or filters** one item at a time; **grouping** and **counting** accumulate
    across items, which is what `defaultdict` and `Counter` are for. Comprehensions combine well with the result, though: after
    grouping, a dict comprehension can turn each group into a summary, such as its size or mean, in one readable line."""),
    ex("""
    from collections import defaultdict

    latencies = [("rag-api", 120), ("auth", 30), ("rag-api", 340), ("auth", 50), ("rag-api", 200)]
    groups = defaultdict(list)
    for service, ms in latencies:
        groups[service].append(ms)
    summary = {s: {"n": len(v), "mean": sum(v) / len(v), "max": max(v)} for s, v in sorted(groups.items())}
    print(summary)
    """, "group_then_summarise.py"),
)

section("fromkeys", "`dict.fromkeys`, merging, and initial values",
    p("""`dict.fromkeys(keys, value)` builds a dict with every key mapped to the **same** value. For an immutable value like `0` or
    `None` that is fine. For a mutable value like `[]` or `{}` it is a trap, exactly like `[[]] * 3` in 6.1: there is one list,
    and every key refers to it, so appending under one key appends under all of them. A dict comprehension evaluates the value
    expression once **per key**, creating a separate list each time (problem 11)."""),
    ex("""
    classes = ["ham", "spam"]
    shared = dict.fromkeys(classes, [])
    shared["spam"].append(0.9)
    separate = {c: [] for c in classes}
    separate["spam"].append(0.9)
    print(shared, separate)
    print(dict.fromkeys(["b", "a", "b"]), list(dict.fromkeys(["b", "a", "b"])))
    """, "fromkeys.py"),
    p("""The last line is the good use of `fromkeys` you saw in 4.5: deduplicating while keeping order, since every value is `None`.
    For **merging** dicts, you rarely need a comprehension. `{**defaults, **overrides}` and `defaults | overrides` (Python 3.9+)
    both build a new dict where later keys win, and `|=` updates in place. A comprehension is for when the merge has a rule,
    such as ignoring overrides that are `None`, or rejecting unknown keys (problem 6)."""),
    ex("""
    defaults = {"model": "small", "temperature": 0.7, "max_tokens": 256}
    overrides = {"temperature": 0, "max_tokens": None}
    print({**defaults, **overrides})
    print(defaults | overrides == {**defaults, **overrides})
    print({k: overrides[k] if overrides.get(k) is not None else v for k, v in defaults.items()})
    print({k: overrides.get(k) or v for k, v in defaults.items()})      # wrong: drops temperature 0
    """, "merging.py"),
    p("""The last line shows the falsy trap of 1.2 inside a comprehension: `x or default` replaces **any** falsy value, so a
    deliberate `temperature=0` (deterministic output) is silently turned back into `0.7`. Test for `None` explicitly when 0,
    `""` or `False` are valid values."""),
)

section("nested", "Nested dict comprehensions",
    p("""The value expression of a dict comprehension can be another comprehension, which builds nested structures: a dict of lists,
    a dict of dicts, a dict of sets. Read it from the outside in: the outer `for` decides the keys, and the inner comprehension
    builds the value for each key. Two typical ML uses are a **confusion matrix** as a dict of dicts, `{actual: {predicted:
    count}}`, and per-document sets of words for keyword search."""),
    ex("""
    from collections import Counter

    y_true = ["spam", "ham", "spam", "ham", "spam"]
    y_pred = ["spam", "spam", "ham", "ham", "spam"]
    classes = sorted(set(y_true) | set(y_pred))
    pairs = Counter(zip(y_true, y_pred))
    matrix = {a: {p: pairs[(a, p)] for p in classes} for a in classes}
    print(matrix)
    recall = {c: matrix[c][c] / sum(matrix[c].values()) for c in classes}
    print({c: round(r, 3) for c, r in recall.items()})
    """, "confusion.py"),
    p("""Notice the division of labour: `Counter` does the counting in one pass, then the comprehension only **looks up** counts,
    which is cheap. A `Counter` returns 0 for a missing pair instead of raising, which is why `pairs[("ham", "ham")]` works
    even if that pair never occurred. Using `classes` for both loops gives every row every column, in a fixed order, which is
    what makes the matrix printable and comparable between runs."""),
    ex("""
    docs = {"faq": "Refunds take 5 days.", "terms": "No refunds after 30 days.", "auth": "Reset your password."}
    words = {doc_id: {w.strip(".,").lower() for w in text.split()} for doc_id, text in docs.items()}
    print(sorted(words["terms"]))
    query = {"refunds", "days"}
    print([doc_id for doc_id, ws in words.items() if query <= ws])
    """, "word_sets.py"),
    p("""`query <= ws` is the subset test of 4.4: the document contains every query word. This is the core of keyword (lexical)
    search, the half of hybrid retrieval that catches exact terms such as product codes, which embeddings can miss (problem 7).
    Beyond two levels of nesting, write a function for the inner part and call it in the comprehension; three nested
    comprehensions are hard for anyone to check."""),
)

section("ml", "Label maps and vocabularies: comprehensions in model code",
    p("""Models work with integers, people with names. Every classification project therefore has a **label map**: `label2id`
    from class name to integer and `id2label` back. Hugging Face models store exactly these two dicts in their `config.json`.
    Both are one dict comprehension over a **sorted** list of unique labels, and the sorting is what makes the ids the same on
    every machine and every run."""),
    ex("""
    raw_labels = ["spam", "ham", "phishing", "spam", "ham"]
    classes = sorted(set(raw_labels))
    label2id = {label: i for i, label in enumerate(classes)}
    id2label = {i: label for label, i in label2id.items()}
    print(label2id, id2label)
    print([label2id[l] for l in raw_labels], [id2label[i] for i in [2, 0]])
    """, "label_maps.py"),
    p("""Inverting is safe here because the ids are unique by construction. A **vocabulary** works the same way, with a filter for
    rare words and special entries for padding and unknown tokens. Note the order of the comprehension's parts: the specials come
    first so their ids are fixed (0 and 1), and the real words are numbered after them with `enumerate(..., start=2)`."""),
    ex("""
    from collections import Counter

    corpus = ["refund my order", "refund policy", "order status", "my refund"]
    counts = Counter(w for line in corpus for w in line.split())
    specials = ["<pad>", "<unk>"]
    words = sorted(w for w, n in counts.items() if n >= 2)
    vocab = {**{s: i for i, s in enumerate(specials)}, **{w: i for i, w in enumerate(words, start=len(specials))}}
    print(vocab)
    print([vocab.get(w, vocab["<unk>"]) for w in "refund status please".split()])
    """, "vocab.py"),
    p("""`vocab.get(w, vocab["<unk>"])` maps unseen words to the unknown id instead of raising, which is what a model needs at
    serving time, when users type words that were never in the training data. The vocabulary and label maps must be **saved
    with the model** and loaded at serving time, never rebuilt from new data, or the ids will not mean what the model learned
    (problem 19)."""),
)

section("warmup", "Warm-up",
    predict("Dict and set comprehension basics", "easy",
        code="""
        print({w: len(w) for w in ["ab", "cde", "ab"]})
        print({k: v for k, v in [("x", 1), ("y", 2), ("x", 3)]})
        print(sorted({n % 3 for n in range(10)}), type({}).__name__)
        scores = {"a": 0.9, "b": 0.4, "c": 0.7}
        print({k: v for k, v in scores.items() if v > 0.5}, {v: k for k, v in scores.items()}[0.4])
        """,
        hints=["A repeated key is assigned again: the value changes, the position does not."],
        why="""`"ab"` appears twice but is one key. In the second line, `x` is assigned 1 and then 3; it keeps its first position,
        before `y`. The set of remainders has three values. `{}` is a dict. Filtering `items()` keeps the pairs that pass, and
        inverting works here because the scores are unique."""),
    write("Label maps for a classifier", "easy", tag="ML",
        prompt="""Write `label_maps(labels)` returning `(label2id, id2label)` for the distinct labels, numbered from 0 in sorted
        order, using dict comprehensions.""",
        code="""
        def label_maps(labels):
            pass
        """,
        tests="""
        l2i, i2l = label_maps(["spam", "ham", "phishing", "spam"])
        assert l2i == {"ham": 0, "phishing": 1, "spam": 2}
        assert i2l == {0: "ham", 1: "phishing", 2: "spam"}
        assert all(i2l[l2i[x]] == x for x in l2i)
        assert label_maps([]) == ({}, {})
        """,
        hints=["`sorted(set(labels))` gives the distinct labels in a fixed order; `enumerate` numbers them."],
        solution="""
        def label_maps(labels):
            classes = sorted(set(labels))
            label2id = {label: i for i, label in enumerate(classes)}
            id2label = {i: label for label, i in label2id.items()}
            return label2id, id2label
        """,
        why="""The set removes duplicates and `sorted` fixes the order, so the same labels always get the same ids, whatever order they
        arrive in and on whatever machine. Without `sorted`, the ids would follow the set's order, which for strings changes
        between runs. Inverting is safe because each id is unique. These are the `label2id` and `id2label` fields of a Hugging Face
        model config."""),
    fix("Inverting a mapping loses documents", "easy", tag="Data work",
        prompt="""`docs_by_category(category)` should turn `{doc: category}` into `{category: sorted list of docs}`. Documents
        disappear. Fix it.""",
        code="""
        def docs_by_category(category):
            return {cat: [doc] for doc, cat in category.items()}
        """,
        tests="""
        category = {"faq.md": "billing", "terms.md": "legal", "invoice.md": "billing", "gdpr.md": "legal", "a.md": "misc"}
        assert docs_by_category(category) == {"billing": ["faq.md", "invoice.md"], "legal": ["gdpr.md", "terms.md"], "misc": ["a.md"]}
        assert docs_by_category({}) == {}
        """,
        hints=["Repeated keys overwrite in a dict comprehension. This is grouping: one pass with a `defaultdict(list)`, then sort each list."],
        solution="""
        from collections import defaultdict

        def docs_by_category(category):
            groups = defaultdict(list)
            for doc, cat in category.items():
                groups[cat].append(doc)
            return {cat: sorted(docs) for cat, docs in groups.items()}
        """,
        why="""Each `billing` document assigned a new one-item list to the same key, so only the last survived. Grouping accumulates across
        items, which a comprehension cannot do; `defaultdict(list)` appends in one pass (4.6). A comprehension is still the right
        tool for the second step, turning each group into its sorted form. Dict equality ignores key order, so the test passes
        whatever order the categories were first seen in."""),
    predict("Sets, zip and filtering items", "easy",
        code="""
        names = ["Ana", "bo", "ANA", "Cy"]
        print(sorted({n.lower() for n in names}), len({n for n in names}))
        print(dict(zip(["a", "b", "c"], [1, 2])))
        cfg = {"model": "small", "debug": False, "seed": 0, "tag": ""}
        print({k: v for k, v in cfg.items() if v}, sorted({k for k, v in cfg.items() if v is not None}))
        """,
        hints=["`zip` stops at the shorter input. A plain `if v` drops every falsy value."],
        why="""Lower-casing before building the set merges `Ana` and `ANA`; without it there are four distinct names. `zip` silently drops
        `"c"`. Filtering with `if v` removes `False`, `0` and `""`, which are real settings, while `is not None` keeps them all,
        so the set has all four keys; it is sorted before printing because a set of strings has no stable order."""),
)

section("medium", "Medium",
    write("Cost per model", "medium", tag="GenAI",
        prompt="""Write `costs(usage, prices)` where `usage` maps model name to `{"in": tokens, "out": tokens}` and `prices` maps
        model name to `{"in": dollars per 1M tokens, "out": dollars per 1M tokens}`. Return a dict from model to cost in dollars,
        rounded to 4 decimals, for models that have a price, ordered from most to least expensive. Return models without a price
        separately as a sorted list: the result is `(costs_dict, unpriced)`.""",
        code="""
        def costs(usage, prices):
            pass
        """,
        tests="""
        usage = {"small": {"in": 1_200_000, "out": 300_000}, "large": {"in": 50_000, "out": 20_000},
                 "local": {"in": 9_000, "out": 1_000}, "embed": {"in": 2_000_000, "out": 0}}
        prices = {"small": {"in": 0.15, "out": 0.60}, "large": {"in": 2.50, "out": 10.00}, "embed": {"in": 0.02, "out": 0.0}}
        c, unpriced = costs(usage, prices)
        assert c == {"small": 0.36, "large": 0.325, "embed": 0.04}
        assert list(c) == ["small", "large", "embed"]
        assert unpriced == ["local"]
        assert costs({}, prices) == ({}, [])
        """,
        hints=["First a dict comprehension over `usage.items()` filtered by `m in prices`. Then order it with `dict(sorted(c.items(), key=..., reverse=True))`.",
               "The unpriced models are a set difference: `sorted(usage.keys() - prices.keys())`."],
        solution="""
        def costs(usage, prices):
            raw = {
                m: round((u["in"] * prices[m]["in"] + u["out"] * prices[m]["out"]) / 1_000_000, 4)
                for m, u in usage.items()
                if m in prices
            }
            ordered = dict(sorted(raw.items(), key=lambda kv: kv[1], reverse=True))
            return ordered, sorted(usage.keys() - prices.keys())
        """,
        why="""The comprehension filters and transforms in one step; `m in prices` is an O(1) dict check (4.5). Ordering a dict means
        rebuilding it from sorted items, since dicts keep insertion order. Dict key views support set operations, so
        `usage.keys() - prices.keys()` gives the unpriced models directly (4.4), and sorting makes the list deterministic. Prices
        per million tokens is how LLM providers quote them, which is why the division by 1,000,000 happens once at the end."""),
    fix("A config merge that ignores temperature 0", "medium", tag="GenAI",
        prompt="""`merge(defaults, overrides)` should apply every override whose value is not `None`, keep defaults otherwise, and
        raise `KeyError` naming any override key that is not a known setting. A `temperature` of `0` is ignored, and typos pass
        silently. Fix it.""",
        code="""
        def merge(defaults, overrides):
            return {k: overrides.get(k) or v for k, v in defaults.items()}
        """,
        tests="""
        defaults = {"model": "small", "temperature": 0.7, "max_tokens": 256, "stream": True}
        assert merge(defaults, {"temperature": 0, "max_tokens": None, "stream": False}) == {
            "model": "small", "temperature": 0, "max_tokens": 256, "stream": False}
        assert merge(defaults, {}) == defaults
        try:
            merge(defaults, {"temprature": 0.2})
            assert False, "typo should raise"
        except KeyError as e:
            assert "temprature" in str(e)
        """,
        hints=["`x or default` replaces every falsy value, including `0` and `False`. Test `is not None` instead.",
               "Unknown keys: `overrides.keys() - defaults.keys()`."],
        solution="""
        def merge(defaults, overrides):
            unknown = overrides.keys() - defaults.keys()
            if unknown:
                raise KeyError(f"unknown settings: {sorted(unknown)}")
            return {k: v if overrides.get(k) is None else overrides[k] for k, v in defaults.items()}
        """,
        why="""Two bugs. `or` treats `0` and `False` as missing, so a deterministic `temperature=0` and `stream=False` were silently
        replaced by the defaults (1.2); `is None` distinguishes "not given" from "given as a falsy value". And iterating over
        `defaults` alone means override keys that are not settings were never looked at, so a typo like `temprature` was simply
        ignored and the run used the default. Rejecting unknown keys is the behaviour of Pydantic models with `extra="forbid"`
        (Module 11), which is what production config loaders use."""),
    write("Keyword search with word sets", "medium", tag="RAG",
        prompt="""Write `keyword_search(docs, query)` where `docs` maps doc id to text. Return the sorted ids of documents that
        contain **every** word of the query. Words are compared lower-cased, with `.,!?` stripped from their ends; an empty query
        returns `[]`. Build each document's word set with a set comprehension inside a dict comprehension.""",
        code="""
        def keyword_search(docs, query):
            pass
        """,
        tests="""
        docs = {"faq": "Refunds take 5 days.", "terms": "No refunds after 30 days!", "auth": "Reset your password.",
                "old": "Refund policy, 2019."}
        assert keyword_search(docs, "refunds days") == ["faq", "terms"]
        assert keyword_search(docs, "Refunds, 30") == ["terms"]
        assert keyword_search(docs, "refund") == ["old"]
        assert keyword_search(docs, "  ") == []
        """,
        hints=["Write one helper, `words(text)`, returning `{w.strip(\".,!?\").lower() for w in text.split()}`, and use it for documents and query alike.",
               "A document matches when `query_words <= doc_words`."],
        solution="""
        def words(text):
            return {w.strip(".,!?").lower() for w in text.split()} - {""}

        def keyword_search(docs, query):
            q = words(query)
            if not q:
                return []
            index = {doc_id: words(text) for doc_id, text in docs.items()}
            return sorted(doc_id for doc_id, ws in index.items() if q <= ws)
        """,
        why="""Using the same `words` function for documents and query guarantees both are normalised the same way; tokenising them
        differently is the classic reason keyword search "misses" obvious matches. Subtracting `{""}` removes the empty string a
        bare punctuation token would leave. The subset test `q <= ws` is "all query words present" (4.4). Note that `refund` does
        not match `refunds`: exact-word search needs stemming or a proper analyser for that, which is what BM25 libraries and
        search engines add. Without the empty-query check, `set() <= ws` would be true for every document."""),
    choose("Group by category: a comprehension per key or one pass", "medium",
        prompt="Both group 100,000 tickets into lists by their category (50 categories). Which is faster?",
        setup="""from collections import defaultdict
cats = [f"cat{i}" for i in range(50)]
tickets = [(i, cats[i % 50]) for i in range(100_000)]""",
        options={
            "a": "groups = {c: [t for t, cat in tickets if cat == c] for c in cats}",
            "b": "groups = defaultdict(list)\nfor t, cat in tickets:\n    groups[cat].append(t)",
        },
        answer="b",
        hints=["How many times does each version look at each ticket?"],
        why="""The comprehension scans all 100,000 tickets once **per category**: 5,000,000 comparisons. The `defaultdict` loop looks at
        each ticket once and appends it to its group: 100,000 steps. The comprehension is shorter, but its cost grows with
        `tickets x categories`, so it gets worse as either grows. Grouping is accumulation across items, which is the job of
        `defaultdict` (or `itertools.groupby` on sorted data, 6.4, or `df.groupby` in pandas)."""),
    trace("Dict comprehensions step by step", "medium",
        prompt="Fill in `d` after each marked line.",
        code="""
        words = ["Refund", "policy", "refund", "EU"]
        d = {w.lower(): len(w) for w in words}  # row: "lower-cased keys"
        d = {k: v for k, v in d.items() if v > 2}  # row: "filter items"
        d = {v: k for k, v in d.items()}  # row: "invert"
        d = {k: sorted(v) for k, v in {"a": {3, 1}, "b": set()}.items()}  # row: "sorted sets"
        d = dict.fromkeys("aba", 0)  # row: "fromkeys"
        """,
        trace_vars=["d"],
        hints=["Repeated keys keep their first position and take the last value."],
        why="""`Refund` and `refund` collapse to one key, `refund`, with the length of the last one (both 6). The filter drops `eu`.
        Inverting gives `{6: "policy"}`, because both remaining values are 6 and the last pair wins: the second data loss of
        the trace. Sorting each set turns it into a list, the empty set into `[]`. `fromkeys` over a string uses its characters,
        once each."""),
    refactor("Per-class metrics without the loop", "medium", tag="ML",
        prompt="Rewrite with dict comprehensions, same result. Keep the tests green.",
        code="""
        def precision_recall(tp, fp, fn):
            classes = sorted(set(tp) | set(fp) | set(fn))
            out = {}
            for c in classes:
                t = tp.get(c, 0)
                p_den = t + fp.get(c, 0)
                r_den = t + fn.get(c, 0)
                if p_den:
                    precision = round(t / p_den, 3)
                else:
                    precision = 0.0
                if r_den:
                    recall = round(t / r_den, 3)
                else:
                    recall = 0.0
                out[c] = {"precision": precision, "recall": recall}
            return out
        """,
        tests="""
        tp = {"spam": 8, "ham": 30}
        fp = {"spam": 2, "ham": 4, "phish": 1}
        fn = {"spam": 4, "ham": 2}
        assert precision_recall(tp, fp, fn) == {
            "ham": {"precision": 0.882, "recall": 0.938},
            "phish": {"precision": 0.0, "recall": 0.0},
            "spam": {"precision": 0.8, "recall": 0.667},
        }
        assert precision_recall({}, {}, {}) == {}
        """,
        hints=["A small helper `ratio(num, den)` that returns `0.0` when `den` is 0 removes the repeated `if`.",
               "Then a dict comprehension over `classes`, with a dict as the value."],
        solution="""
        def ratio(num, den):
            return round(num / den, 3) if den else 0.0

        def precision_recall(tp, fp, fn):
            classes = sorted(tp.keys() | fp.keys() | fn.keys())
            return {
                c: {
                    "precision": ratio(tp.get(c, 0), tp.get(c, 0) + fp.get(c, 0)),
                    "recall": ratio(tp.get(c, 0), tp.get(c, 0) + fn.get(c, 0)),
                }
                for c in classes
            }
        """,
        why="""The repeated "divide unless the denominator is 0" logic moves into one named helper, which is what makes the comprehension
        short enough to read. Key views support `|` directly, so there is no need to build sets first. The class `phish` has
        only a false positive: its precision is 0 out of 1, and its recall has a denominator of 0, which the helper turns into
        0.0 instead of a `ZeroDivisionError`. scikit-learn's `classification_report` computes the same
        numbers, and its `zero_division` parameter is exactly this helper's choice of 0.0."""),
    fix("Per-class scores that all end up together", "medium", tag="ML",
        prompt="""`scores_by_class(preds, classes)` collects the predicted probability of each prediction under its class. Every
        class ends up with every score. Fix it.""",
        code="""
        def scores_by_class(preds, classes):
            out = dict.fromkeys(classes, [])
            for label, score in preds:
                out[label].append(score)
            return out
        """,
        tests="""
        preds = [("spam", 0.9), ("ham", 0.6), ("spam", 0.7)]
        assert scores_by_class(preds, ["ham", "spam", "phish"]) == {"ham": [0.6], "spam": [0.9, 0.7], "phish": []}
        assert scores_by_class([], []) == {}
        """,
        hints=["`fromkeys` puts the **same** list object under every key. Build a new list per key."],
        solution="""
        def scores_by_class(preds, classes):
            out = {c: [] for c in classes}
            for label, score in preds:
                out[label].append(score)
            return out
        """,
        why="""`dict.fromkeys(classes, [])` evaluates `[]` once and stores that one list under all keys, so each `append` shows up under
        every class. The dict comprehension evaluates `[]` once per key. Unlike a `defaultdict`, pre-creating the keys from
        `classes` also gives classes with no predictions an empty list, which a report needs to show "phish: 0 predictions", and
        an unexpected label still raises `KeyError` instead of silently creating a new class."""),
    predict("Merging and key collisions", "medium",
        code="""
        a = {"model": "small", "temperature": 0.7}
        b = {"temperature": 0.2, "seed": 1}
        print({**a, **b}, a | b == {**b, **a})
        tags = ["Refund", "refund", "EU", "eu", "Eu"]
        print({t.lower(): t for t in tags})
        print({i % 2: i for i in range(5)}, {len(t) for t in tags})
        """,
        hints=["When keys collide, the later dict or the later item wins. `{**b, **a}` lets `a` win."],
        why="""In `{**a, **b}`, `b` comes later, so its temperature wins; `a | b` is the same merge, and `{**b, **a}` is a different one
        (with `a`'s temperature), so the comparison is false. Lower-casing makes the tags collide, and each key keeps the
        **original** spelling of its **last** occurrence. `i % 2` has two keys, holding the last even and last odd numbers, 4
        and 3."""),
)

section("hard", "Hard",
    write("Flatten a nested config", "hard", tag="Data work",
        prompt="""Experiment trackers log nested configs as flat keys. Write `flatten(config, sep=".")` that turns nested dicts into
        one level with joined keys: `{"model": {"name": "small", "lora": {"r": 8}}}` becomes `{"model.name": "small",
        "model.lora.r": 8}`. Non-dict values (including lists) are kept as they are; an empty nested dict disappears. Use a dict
        comprehension and recursion.""",
        code="""
        def flatten(config, sep="."):
            pass
        """,
        tests="""
        cfg = {"model": {"name": "small", "lora": {"r": 8, "alpha": 16}}, "lr": 3e-4, "tags": ["a", "b"], "extra": {}}
        assert flatten(cfg) == {"model.name": "small", "model.lora.r": 8, "model.lora.alpha": 16, "lr": 3e-4, "tags": ["a", "b"]}
        assert flatten({"a": {"b": 1}}, sep="/") == {"a/b": 1}
        assert flatten({}) == {}
        assert list(flatten(cfg))[:3] == ["model.name", "model.lora.r", "model.lora.alpha"]
        """,
        hints=["For each `key, value`: if `value` is a dict, flatten it recursively and prefix each of its keys; otherwise yield the pair as it is.",
               "A dict comprehension with two `for` clauses can walk the pairs that the inner call returns: `{f\"{k}{sep}{ik}\": iv for k, v in ... for ik, iv in flatten(v, sep).items()}`. Handle non-dict values by wrapping them as a one-item dict."],
        solution="""
        def flatten(config, sep="."):
            return {
                f"{key}{sep}{inner_key}" if inner_key else key: inner_value
                for key, value in config.items()
                for inner_key, inner_value in (flatten(value, sep).items() if isinstance(value, dict) else [("", value)])
            }
        """,
        why="""Each item either is a leaf, represented as one pair with an empty inner key, or a nested dict, whose already-flattened
        pairs are walked by the second `for` clause and prefixed with the outer key. The recursion ends at leaves, and an empty
        nested dict produces no pairs at all, so it disappears. The conditional expression in the key position decides between
        `key` and `key.inner_key`. Iteration order follows the original dict, so the flat keys stay in a readable order. This is
        compact, and near the limit of what a comprehension should hold; a written generator function (6.3) is the more readable
        version for a team. Trackers like MLflow and Weights & Biases flatten configs this way to make them searchable."""),
    write("A confusion matrix as a nested dict", "hard", tag="ML",
        prompt="""Write `confusion(y_true, y_pred)` returning `(matrix, recall)`. `matrix[actual][predicted]` is the count of each
        pair, with **every** class (from both lists, sorted) present in both levels, including zeros. `recall[c]` is the diagonal
        count divided by the row total, rounded to 3 decimals, or `0.0` for a class with no true examples. Raise `ValueError` if
        the lists have different lengths.""",
        code="""
        def confusion(y_true, y_pred):
            pass
        """,
        tests="""
        y_true = ["spam", "ham", "spam", "ham", "spam", "ham"]
        y_pred = ["spam", "spam", "ham", "ham", "spam", "phish"]
        m, r = confusion(y_true, y_pred)
        assert m == {"ham": {"ham": 1, "phish": 1, "spam": 1}, "phish": {"ham": 0, "phish": 0, "spam": 0},
                     "spam": {"ham": 1, "phish": 0, "spam": 2}}
        assert r == {"ham": 0.333, "phish": 0.0, "spam": 0.667}
        assert list(m) == ["ham", "phish", "spam"] and list(m["spam"]) == ["ham", "phish", "spam"]
        assert confusion([], []) == ({}, {})
        try:
            confusion(["a"], [])
            assert False
        except ValueError:
            pass
        """,
        hints=["Count pairs once with `Counter(zip(y_true, y_pred))`, then look counts up in a nested comprehension.",
               "The row total is `sum(matrix[c].values())`."],
        solution="""
        from collections import Counter

        def confusion(y_true, y_pred):
            if len(y_true) != len(y_pred):
                raise ValueError("y_true and y_pred must have the same length")
            classes = sorted(set(y_true) | set(y_pred))
            pairs = Counter(zip(y_true, y_pred))
            matrix = {a: {p: pairs[(a, p)] for p in classes} for a in classes}
            recall = {
                c: round(matrix[c][c] / total, 3) if (total := sum(matrix[c].values())) else 0.0
                for c in classes
            }
            return matrix, recall
        """,
        why="""Counting happens once, in O(n), and the nested comprehension only looks up counts, O(k^2) for k classes, which is small.
        A `Counter` returns 0 for a pair that never occurred, so every cell exists. Taking classes from **both** lists matters:
        `phish` was only ever predicted, and a matrix built from `y_true` alone would hide that the model invents a class. The
        walrus computes each row total once for both the test and the division. The length check runs first because `zip` would
        otherwise silently drop the extra items (4.1). This is `sklearn.metrics.confusion_matrix` with `labels=`, returned as
        named rows instead of a bare array."""),
    fix("Read the code: an experiment summary", "hard", tag="ML",
        prompt="""This summarises experiment runs: for each model, the best F1, the mean F1 over its runs, and the number of runs,
        sorted by model name. The best F1 is often wrong, the means are all the same, and the order changes between runs of the
        program. Read it, find the bugs and fix them.""",
        code="""
        def summarize(runs):
            models = {r["model"] for r in runs}
            best = {r["model"]: r for r in runs}
            f1s = dict.fromkeys(models, [])
            for r in runs:
                f1s[r["model"]].append(r["f1"])
            return [
                (m, best[m]["f1"], round(sum(f1s[m]) / len(f1s[m]), 3), len(f1s[m]))
                for m in models
            ]
        """,
        tests="""
        runs = [
            {"model": "logreg", "f1": 0.81}, {"model": "xgb", "f1": 0.88}, {"model": "logreg", "f1": 0.84},
            {"model": "xgb", "f1": 0.86}, {"model": "bert", "f1": 0.91}, {"model": "logreg", "f1": 0.79},
        ]
        assert summarize(runs) == [("bert", 0.91, 0.91, 1), ("logreg", 0.84, 0.813, 3), ("xgb", 0.88, 0.87, 2)]
        assert summarize([]) == []
        """,
        hints=["`{r[\"model\"]: r for r in runs}` keeps the **last** run per model, not the best.",
               "`dict.fromkeys(models, [])` shares one list. And iterating over a set of strings gives a different order per process."],
        solution="""
        def summarize(runs):
            f1s = {}
            for r in runs:
                f1s.setdefault(r["model"], []).append(r["f1"])
            return [
                (m, max(scores), round(sum(scores) / len(scores), 3), len(scores))
                for m, scores in sorted(f1s.items())
            ]
        """,
        why="""Three bugs, each a rule from this lesson. The dict comprehension `best` assigns every run under its model, so the
        **last** run wins, which happens to be the best only sometimes. `dict.fromkeys(models, [])` puts one shared list under
        every model, so all means were the mean of all runs. And `for m in models` iterates a set of strings, whose order depends
        on hash randomisation and changes between processes, so the report order was not stable. The fix groups once (here with
        `setdefault`, equivalent to a `defaultdict`), takes `max` of each group instead of relying on order, and iterates
        `sorted(f1s.items())`. Once the runs are grouped, the best, the mean and the count all come from the same list, so they
        cannot disagree."""),
    predict("Equality, hashing and order", "hard",
        code="""
        print({1, 1.0, True}, {0.1 + 0.2, 0.3}.__len__())
        print({k: k for k in [1, 1.0, True]})
        calls = []

        def val(k):
            calls.append(k)
            return k * 10

        d = {k: val(k) for k in ["a", "b", "a"]}
        print(d, calls)
        print({x: y for x, y in zip("abc", range(3)) if y}, sorted({len(w) for w in "to be or not".split()}))
        """,
        hints=["`1`, `1.0` and `True` are equal and hash the same, so they are one key; the first-inserted key object is kept.",
               "The value expression runs for every item, including repeated keys."],
        why="""For both the set and the dict, `1`, `1.0` and `True` count as one element. The set keeps the first object it saw, `1`. The
        dict keeps the first **key** object, `1`, but takes the **last value**, `True`: assigning to an existing key replaces the
        value and leaves the key alone. `0.1 + 0.2` is not equal to `0.3`, so the second set has two elements. The value expression
        ran three times, once per item, even though only two keys remain, which matters when it is expensive or has side
        effects. Filtering with `if y` drops the pair with `y == 0`."""),
)

section("interview", "Interview questions",
    explain("What happens with duplicate keys in a dict comprehension, and how do you invert a dict safely?", "medium", tag="Interview",
        why="""A dict comprehension assigns `d[key] = value` for every item, so a repeated key is overwritten: the last value wins, and
        the key keeps the position of its first insertion. There is no error, so data loss is silent. Inverting `{k: v}` with
        `{v: k for k, v in d.items()}` is only safe when the values are unique and hashable; you can check with `len(set(d.values()))
        == len(d)`, or assert it. If values can repeat, inversion is grouping: one pass with a `defaultdict(list)` gives `{v: [keys]}`.
        If values are unhashable (lists, dicts), they cannot be keys at all, and you need to convert them (for example to tuples) or
        rethink the structure."""),
    explain("When should you use a set comprehension instead of a list comprehension, and why can a set's order change between runs?", "medium", tag="Interview",
        why="""Use a set comprehension when you need distinct values or fast membership tests and do not care about order or count:
        unique domains, vocabulary candidates, ids already seen. Use a list when order, duplicates or positions matter. A set stores
        elements by hash in a table, so iteration order follows hash values and table layout, not insertion. For strings and bytes,
        Python randomises the hash function per process (to defend against attacks that force hash collisions), so the order of a
        set of strings can differ every time the program runs; `PYTHONHASHSEED` can fix it, but the robust answer is to sort before
        anything order-dependent: numbering, saving, printing, comparing outputs in tests."""),
    explain("How would you make label ids and vocabularies reproducible between training and serving?", "hard", tag="Interview",
        why="""Build them deterministically and then treat them as part of the model. Deterministically means from a sorted list of unique
        values (`{label: i for i, label in enumerate(sorted(set(labels)))}`), with special tokens (`<pad>`, `<unk>`) at fixed
        positions, and filters such as a minimum count applied in a fixed order, never from a set's iteration order. Part of the
        model means saving them with the weights (Hugging Face stores `label2id` and `id2label` in `config.json`, tokenizers in
        their own files), versioning them together, and loading them at serving time instead of rebuilding them from new data,
        which would renumber classes and silently scramble predictions. At serving time, map unknown values to `<unk>` or an
        "other" class, log how often that happens, and add a test that loads the saved maps and checks a few known ids."""),
)

recap(
    "`{k: v for ...}` assigns for every item: a repeated key keeps its first position and takes the last value, silently.",
    "`{x for ...}` builds a set: distinct by equality and hash, no order. Sort before numbering, saving or printing. `{}` is an empty dict.",
    "Comprehensions transform and filter; grouping and counting accumulate, so use `defaultdict` or `Counter`, then summarise with a comprehension.",
    "`dict.fromkeys(keys, [])` shares one list; `{k: [] for k in keys}` does not. Test `is None` when 0 or False are valid values.",
    "Label maps and vocabularies: built from sorted unique values, saved with the model, loaded at serving time.",
)
