from lesson import *
from diagrams import *

lesson(
    id="m4-6", num="4.6", title="Dict tools: counting and grouping",
    intro="`Counter` for counting, `defaultdict` for creating entries on first use, and the GROUP BY patterns built on "
          "them: grouping, multi-key grouping and several aggregates in one pass. Plus an LRU cache with `OrderedDict` "
          "and rank fusion for hybrid search.",
    desc="`Counter`, `defaultdict`, `setdefault` and group-by patterns.",
    keys="counter most_common total defaultdict default factory setdefault group by grouping aggregate itertools groupby ordereddict move_to_end lru cache chainmap reciprocal rank fusion class weights",
)

term("Counter", "`collections.Counter`: a dict subclass that counts hashable items. Missing items count as 0.")
term("defaultdict", "`collections.defaultdict(factory)`: a dict that calls `factory()` to create a value the first time a missing key is accessed.")
term("Group by", "Splitting items into groups by a key and computing something per group, like SQL `GROUP BY`.")
term("LRU cache", "A fixed-size cache that, when full, evicts the Least Recently Used entry.")
term("Reciprocal rank fusion", "Combining several ranked lists by adding `1 / (k + rank)` for each item: a standard way to merge keyword and vector search results.")

section("counter", "Counting with `Counter`",
    fig(table(["Counter('banana')", "count"], [["a", "3"], ["n", "2"], ["b", "1"]], hl={(0, 1)}, label="counts of each letter"),
        "A `Counter` is a dict from item to count; `most_common` returns the largest counts first."),
    p("""`Counter(iterable)` counts how many times each hashable item appears. It is a dict subclass, so everything from 4.5
    works, with a few changes that make counting painless. Step by step: building it walks the iterable once (in C, which is
    fast) and adds 1 for each item. Reading a **missing** item returns `0` instead of raising, and does not insert it.
    `most_common(n)` returns the top `n` pairs, highest count first, with ties in first-seen order."""),
    ex("""
    from collections import Counter

    labels = ["spam", "ham", "spam", "eggs", "ham", "spam"]
    c = Counter(labels)
    print(c, c["spam"], c["unknown"])           # missing items count as 0
    print(c.most_common(2), c.total())
    c.update(["eggs", "eggs"])                  # update ADDS counts (unlike dict.update)
    c["ham"] -= 1
    print(c.most_common(), "unknown" in c)
    """, "counter_basics.py"),
    p("""Counters also do arithmetic, which turns many comparisons into one line: `c1 + c2` adds counts, `c1 - c2` subtracts
    and **drops anything that ends at zero or below**, `c1 & c2` keeps the minimum of each count and `c1 | c2` the maximum.
    Note that `update` and `+` **add** counts, the opposite of `dict.update`, which replaces values."""),
    ex("""
    from collections import Counter

    train = Counter({"spam": 600, "ham": 400})
    test = Counter({"spam": 50, "ham": 150, "eggs": 5})
    print(train + test)
    print(test - train, train - test)           # zero or negative results disappear
    print(test & train, sorted((train | test).items()))
    """, "counter_math.py"),
    callout("sql", "SQL / Power BI", """`Counter(labels)` is `SELECT label, COUNT(*) FROM t GROUP BY label`, and
    `most_common(3)` adds `ORDER BY COUNT(*) DESC LIMIT 3`. In pandas it is `s.value_counts()`; in Power BI, a count
    measure on a table visual grouped by the label column."""),
)

section("defaultdict", "`defaultdict`: values created on first access",
    p("""A `defaultdict(factory)` behaves like a dict, except that accessing a **missing** key with `d[key]` calls
    `factory()` (with no arguments), stores the result under that key, and returns it. So `defaultdict(list)` gives every
    new key an empty list, `defaultdict(int)` a 0, `defaultdict(set)` an empty set. That removes the "if the key is not
    there yet, create it" step from every grouping and counting loop."""),
    ex("""
    from collections import defaultdict

    by_team = defaultdict(list)
    for ticket, team in [("T1", "billing"), ("T2", "auth"), ("T3", "billing")]:
        by_team[team].append(ticket)             # no need to create the list first
    print(by_team["billing"], dict(by_team))

    tokens = defaultdict(int)
    for model, n in [("small", 120), ("large", 300), ("small", 30)]:
        tokens[model] += n
    print(dict(tokens))
    """, "defaultdict_basics.py"),
    p("""The trap: **any** `d[key]` on a missing key creates an entry, including reads that were only meant to check. A
    report that does `if d[key]:` for keys that may not exist quietly fills the dict with empty entries, which then show up
    in counts, JSON output and plots. Use `key in d` or `d.get(key)` to read without creating (problem 9). And convert to a
    plain dict before returning or serialising, so callers do not inherit the auto-creating behaviour."""),
    ex("""
    from collections import defaultdict

    seen = defaultdict(list)
    seen["a"].append(1)
    if seen["b"]:                 # a "harmless" read...
        pass
    print(dict(seen), "c" in seen, seen.get("c"), dict(seen))   # in and get do not create
    """, "phantom_keys.py"),
)

section("choose", "`get`, `setdefault`, `defaultdict` or `Counter`?",
    fig(flowchart({
        "count": ("ask", 0, 0, "counting things?"),
        "c": ("good", 1, 0, "Counter"),
        "group": ("ask", 0, 1, "collecting groups|of items?"),
        "dd": ("good", 1, 1, "defaultdict(list)"),
        "once": ("ask", 0, 2, "one lookup with|a fallback?"),
        "get": ("good", 1, 2, "d.get(k, default)"),
        "sd": ("step", 0, 3, "d.setdefault(k, v)"),
    }, [("count", "c", "yes"), ("count", "group", "no"), ("group", "dd", "yes"), ("group", "once", "no"), ("once", "get", "yes"), ("once", "sd", "no")],
        cell=(230, 80), label="choosing a dict tool"),
        "Which dict tool to reach for: the question decides it, not habit."),
    html("""<div class="tbl"><table>
      <tr><th>Tool</th><th>Best for</th><th>Watch out for</th></tr>
      <tr><td><code>d.get(k, 0) + 1</code></td><td>an occasional count in a plain dict</td><td>verbose when repeated everywhere</td></tr>
      <tr><td><code>d.setdefault(k, []).append(x)</code></td><td>grouping into a plain dict, one place in the code</td><td>builds the default object on every call, even when unused</td></tr>
      <tr><td><code>defaultdict(list)</code></td><td>grouping or accumulating in a whole loop</td><td>reads create entries; convert with <code>dict()</code> before returning</td></tr>
      <tr><td><code>Counter(items)</code></td><td>counting, top-k by count, comparing distributions</td><td><code>update</code> adds; subtraction drops non-positive counts</td></tr>
    </table></div>"""),
    p("""All four give O(1) work per item. The choice is about clarity and the behaviour on missing keys: a plain dict
    raises or needs a default every time, `defaultdict` creates silently, `Counter` treats missing as zero without creating.
    In function signatures and return values, prefer plain dicts (or `Counter`, which callers understand); keep
    `defaultdict` as an implementation detail inside the function."""),
)

section("groupby", "GROUP BY patterns",
    fig(chain(["rows", "key = row['dept']", "groups[key].append(row)", ("dict: dept -> rows", "good")]),
        "The Python version of SQL's GROUP BY: one pass, one dict of lists, then aggregate each list."),
    p("""Most "per something" questions in data code are a group-by: a key that decides the group, and something computed
    per group. Built on a dict, every variant is one pass over the data, O(n):"""),
    p("""- **Collect members:** `defaultdict(list)`, appending each item under its key.
    - **Several keys:** use a **tuple** as the key, `(region, month)` (4.3), or nested dicts when you want to look up level
      by level.
    - **Aggregates:** keep running values per group (count, sum, min, max) and compute derived ones like the mean at the
      end, so you never store all the members (problem 13)."""),
    ex("""
    from collections import defaultdict

    sales = [("eu", "jan", 120.0), ("us", "jan", 80.0), ("eu", "feb", 60.0), ("eu", "jan", 30.0)]

    totals = defaultdict(float)
    for region, month, amount in sales:
        totals[(region, month)] += amount
    print(dict(totals))

    nested = defaultdict(lambda: defaultdict(float))
    for region, month, amount in sales:
        nested[region][month] += amount
    print({r: dict(m) for r, m in nested.items()})
    """, "group_by.py"),
    p("""`itertools.groupby` sounds like the same thing but is not: it groups only **consecutive** items with equal keys, so
    unsorted input produces several groups for the same key. Use it on data that is already sorted by the key (a sorted log,
    a query with `ORDER BY`), or sort first; otherwise use the dict patterns above."""),
    ex("""
    from itertools import groupby

    events = ["login", "query", "query", "login", "query"]
    print([(k, len(list(g))) for k, g in groupby(events)])           # consecutive runs
    print([(k, len(list(g))) for k, g in groupby(sorted(events))])   # true groups
    """, "itertools_groupby.py"),
)

section("ordered", "`OrderedDict` for caches, and `ChainMap` for layered lookups",
    p("""Plain dicts keep insertion order, so `OrderedDict` is rarely needed today. It still has two methods that plain
    dicts lack and that make it the classic building block of an **LRU cache**: `move_to_end(key)` marks a key as most
    recently used in O(1), and `popitem(last=False)` removes the **oldest** entry in O(1). An LRU cache keeps the `n` most
    recently used results and evicts the least recently used when full (problem 14)."""),
    ex("""
    from collections import OrderedDict

    cache = OrderedDict()
    for key in ["a", "b", "c"]:
        cache[key] = key.upper()
    cache.move_to_end("a")          # "a" was just used: it is now the newest
    oldest = cache.popitem(last=False)
    print(oldest, list(cache))
    """, "ordered_dict.py"),
    p("""`collections.ChainMap(user, env, defaults)` looks a key up in each mapping in order and returns the first hit,
    **without copying or merging** anything. Later changes to the underlying dicts show through immediately, which suits
    layered configuration that can change at run time. For a one-off merged snapshot, `defaults | env | user` (4.5) is
    simpler."""),
)

section("warmup", "Warm-up",
    predict("Counter basics", "easy",
        code="""
        from collections import Counter

        words = "the refund the policy refund the".split()
        c = Counter(words)
        print(c.most_common(2), c["missing"], "missing" in c)
        print(c.total(), len(c))
        c.update({"policy": 2})
        print(c["policy"], c.most_common(1))
        print(Counter("hello"))
        """,
        hints=["`update` adds counts. A string is an iterable of characters."],
        why="""`"the"` appears 3 times and `"refund"` twice. Reading a missing word gives 0 without inserting it, so `in` stays
        `False`. `total()` is the sum of all counts (6) and `len` the number of distinct words (3). `update` adds 2 to
        `"policy"`, giving 3, which ties with `"the"`; `most_common` breaks the tie by first-seen order, so `"the"` stays first.
        `Counter("hello")` counts characters, a common surprise when someone passes a string instead of a list of words."""),
    write("Most common words across documents", "easy", tag="Data work",
        prompt="""Write `top_words(texts, n, stopwords=())` that counts lower-cased words across all texts, ignoring words in
        `stopwords`, and returns the `n` most common as `(word, count)` pairs.""",
        code="""
        from collections import Counter

        def top_words(texts, n, stopwords=()):
            pass
        """,
        tests="""
        docs = ["Refund the order", "the refund was late", "Late refund again"]
        assert top_words(docs, 2, stopwords={"the"}) == [("refund", 3), ("late", 2)]
        assert top_words(docs, 1) == [("refund", 3)]
        assert top_words([], 3) == []
        """,
        hints=["`Counter(w for text in texts for w in text.lower().split() if w not in stop)`, then `most_common(n)`."],
        solution="""
        from collections import Counter

        def top_words(texts, n, stopwords=()):
            stop = set(stopwords)
            return Counter(w for text in texts for w in text.lower().split() if w not in stop).most_common(n)
        """,
        why="""`Counter` takes any iterable, so a generator expression (Module 6) feeds it words without building a list first.
        Converting `stopwords` to a set once makes each check O(1) (4.4). In the second test, `"refund"` (3) beats `"the"` (2)
        even without stopwords. Real text needs better tokenisation than `split` (punctuation stays attached), which is lesson
        5.5's regex territory."""),
    fix("Groups that share one list", "easy", tag="Data work",
        prompt="""`group_by_status` should map each status to the list of its ticket ids. Every status ends up with every id.
        Fix it.""",
        code="""
        def group_by_status(tickets):
            groups = dict.fromkeys([t["status"] for t in tickets], [])
            for t in tickets:
                groups[t["status"]].append(t["id"])
            return groups
        """,
        tests="""
        tickets = [{"id": 1, "status": "open"}, {"id": 2, "status": "closed"}, {"id": 3, "status": "open"}]
        assert group_by_status(tickets) == {"open": [1, 3], "closed": [2]}
        assert group_by_status([]) == {}
        """,
        hints=["`dict.fromkeys(keys, [])` uses one list object for every key (2.2). Create the list per key instead."],
        solution="""
        from collections import defaultdict

        def group_by_status(tickets):
            groups = defaultdict(list)
            for t in tickets:
                groups[t["status"]].append(t["id"])
            return dict(groups)
        """,
        why="""`dict.fromkeys` evaluates `[]` once, so every status points at the same list and every append lands in all of them.
        `defaultdict(list)` calls `list()` separately for each new key. Returning `dict(groups)` gives callers a plain dict, so
        a later lookup of a missing status raises normally instead of silently inserting an empty group."""),
    predict("defaultdict creates entries when you read", "easy",
        code="""
        from collections import defaultdict

        d = defaultdict(list)
        d["a"].append(1)
        print(len(d), d["b"], len(d))
        print("c" in d, d.get("c"), len(d))
        counts = defaultdict(int, {"x": 2})
        counts["y"] += 1
        print(dict(counts), counts.default_factory)
        """,
        hints=["Only `d[key]` on a missing key calls the factory. `in` and `get` never do."],
        why="""Reading `d["b"]` creates an empty list under `"b"`, so the length goes from 1 to 2 just by looking. `in` and
        `get` do not create anything. A `defaultdict` can start from existing data, and `+=` on a missing key reads (creating
        0) then writes 1. `default_factory` is the function it calls, here the `int` type itself."""),
)

section("medium", "Medium",
    write("Tokens per model", "medium", tag="GenAI",
        prompt="""Write `tokens_per_model(calls)` where each call is a dict with `model` and `usage` (a dict with
        `prompt_tokens` and `completion_tokens`, either of which may be missing). Return a **plain** dict from model to total
        tokens, with keys in sorted order.""",
        code="""
        from collections import defaultdict

        def tokens_per_model(calls):
            pass
        """,
        tests="""
        calls = [{"model": "small", "usage": {"prompt_tokens": 100, "completion_tokens": 20}},
                 {"model": "large", "usage": {"prompt_tokens": 300}},
                 {"model": "small", "usage": {"completion_tokens": 5}}]
        out = tokens_per_model(calls)
        assert out == {"large": 300, "small": 125} and list(out) == ["large", "small"]
        assert type(out) is dict
        assert tokens_per_model([]) == {}
        """,
        hints=["Accumulate in a `defaultdict(int)` with `usage.get(..., 0)`, then build `dict(sorted(totals.items()))`."],
        solution="""
        from collections import defaultdict

        def tokens_per_model(calls):
            totals = defaultdict(int)
            for call in calls:
                usage = call["usage"]
                totals[call["model"]] += usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)
            return dict(sorted(totals.items()))
        """,
        why="""`defaultdict(int)` removes the "first time for this model" branch, and `get(..., 0)` treats missing token fields as
        zero instead of crashing. Returning `dict(sorted(...))` gives callers a plain dict with a deterministic order, so the
        same input always prints and serialises the same way. Per-model token totals are the input to any LLM cost report:
        multiply each by that model's price per token."""),
    write("Balanced class weights", "medium", tag="ML",
        prompt="""For imbalanced training data, write `class_weights(labels)` returning a dict from class to weight
        `n_samples / (n_classes * count_of_class)`, the "balanced" rule scikit-learn uses, with keys in sorted order and
        weights rounded to 4 decimals.""",
        code="""
        from collections import Counter

        def class_weights(labels):
            pass
        """,
        tests="""
        y = ["ham"] * 8 + ["spam"] * 2
        assert class_weights(y) == {"ham": 0.625, "spam": 2.5}
        w = class_weights(["a", "b", "c", "c"])
        assert w == {"a": 1.3333, "b": 1.3333, "c": 0.6667}
        assert class_weights([]) == {}
        """,
        hints=["Count once with `Counter`. `n_samples` is `len(labels)` and `n_classes` is `len(counts)`."],
        solution="""
        from collections import Counter

        def class_weights(labels):
            counts = Counter(labels)
            n, k = len(labels), len(counts)
            return {c: round(n / (k * counts[c]), 4) for c in sorted(counts)}
        """,
        why="""The rare class gets a weight above 1 and the common class one below 1, so each class contributes equally to the
        loss in total: 8 × 0.625 = 2 × 2.5 = 5. This is scikit-learn's `class_weight="balanced"` (`compute_class_weight`), used
        when a model would otherwise learn to always predict the majority class. With no labels, `counts` is empty and the
        comprehension returns `{}` without dividing by zero."""),
    trace("Counter operations, step by step", "medium",
        prompt="Fill in `sorted(c.items())` and `c.total()` after each marked line.",
        code="""
        from collections import Counter
        c = Counter(["a", "b", "a"])
        c.update(["b", "c"])  # row: "c.update(['b', 'c'])"
        c["a"] -= 3  # row: "c['a'] -= 3"
        c = +c  # row: "c = +c"
        c = c - Counter({"b": 1, "z": 5})  # row: "c = c - Counter(...)"
        """,
        trace_vars=["sorted(c.items())", "c.total()"],
        hints=["`update` adds. `c[\"a\"] -= 3` can go negative. Unary `+` keeps only positive counts. Subtraction also drops counts that end at zero or below."],
        why="""After `update`, the counts are a 2, b 2, c 1. Plain item assignment allows a **negative** count: a becomes -1, and the
        total drops to 2. Unary `+c` builds a new Counter with only the positive counts, so a disappears. Subtracting removes 1
        from b, and `"z"`, which `c` did not have, would be negative, so it is dropped. Remember the split: methods and item
        assignment keep zero and negative counts, the operators `+`, `-`, `&`, `|` and unary `+` drop them."""),
    choose("Counting with a dict loop or `Counter`", "medium",
        prompt="Both count one million labels. Which is faster?",
        setup="""import random
from collections import Counter
random.seed(3)
labels = [random.choice(["spam", "ham", "eggs", "bacon"]) for _ in range(1_000_000)]""",
        options={
            "a": "counts = {}\nfor x in labels:\n    counts[x] = counts.get(x, 0) + 1",
            "b": "counts = Counter(labels)",
        },
        answer="b",
        hints=["Where does each version do its per-item work: in Python bytecode or in C?"],
        why="""The loop runs Python bytecode for every label: a method call to `get`, an addition and a store. `Counter(labels)`
        hands the whole list to a helper written in C, so the per-item work happens without the interpreter loop. Same result,
        same O(n), and a noticeably smaller constant here; recent Pythons have made the plain loop faster than it used to be,
        so the gap is smaller than old benchmarks suggest. For counting in a pandas column, `value_counts()` is faster again,
        because it works on the underlying array."""),
    fix("A report that invents empty groups", "medium", tag="Data work",
        prompt="""`active_teams` should list the teams that have open tickets, without changing the grouping. After calling it,
        `groups` contains extra empty teams, which then appear in the dashboard. Fix it so checking a team never adds it.""",
        code="""
        from collections import defaultdict

        def build_groups(tickets):
            groups = defaultdict(list)
            for t in tickets:
                if t["open"]:
                    groups[t["team"]].append(t["id"])
            return groups

        def active_teams(groups, teams):
            return [team for team in teams if groups[team]]
        """,
        tests="""
        tickets = [{"id": 1, "team": "billing", "open": True}, {"id": 2, "team": "auth", "open": False}]
        g = build_groups(tickets)
        assert active_teams(g, ["billing", "auth", "infra"]) == ["billing"]
        assert sorted(g) == ["billing"]
        assert type(build_groups([])) is dict
        """,
        hints=["`groups[team]` on a missing team creates an empty list. `get` reads without creating.",
               "`build_groups` should also return a plain dict, as the last test asks."],
        solution="""
        from collections import defaultdict

        def build_groups(tickets):
            groups = defaultdict(list)
            for t in tickets:
                if t["open"]:
                    groups[t["team"]].append(t["id"])
            return dict(groups)

        def active_teams(groups, teams):
            return [team for team in teams if groups.get(team)]
        """,
        why="""Each `groups[team]` for a team with no open tickets called the factory and stored an empty list, so a read-only
        check changed the data. `get` returns `None` for missing teams and never inserts. Returning a plain dict from
        `build_groups` removes the auto-creating behaviour from the caller's hands entirely: `groups["infra"]` would now raise a
        clear `KeyError` instead of quietly adding a team. This exact bug inflates group counts in many dashboards."""),
    write("Revenue by region and month", "medium", tag="Data work",
        prompt="""Write `revenue_table(sales)` for `(region, month, amount)` tuples, returning a **nested plain dict**
        `{region: {month: total}}`, with regions sorted and months in first-seen order within each region.""",
        code="""
        from collections import defaultdict

        def revenue_table(sales):
            pass
        """,
        tests="""
        sales = [("us", "jan", 80.0), ("eu", "jan", 120.0), ("eu", "feb", 60.0), ("eu", "jan", 30.0), ("us", "mar", 10.0)]
        t = revenue_table(sales)
        assert t == {"eu": {"jan": 150.0, "feb": 60.0}, "us": {"jan": 80.0, "mar": 10.0}}
        assert list(t) == ["eu", "us"] and list(t["eu"]) == ["jan", "feb"]
        assert all(type(m) is dict for m in t.values())
        """,
        hints=["`defaultdict(lambda: defaultdict(float))` creates the inner dict automatically.",
               "Convert both levels at the end: `{r: dict(m) for r, m in sorted(outer.items())}`."],
        solution="""
        from collections import defaultdict

        def revenue_table(sales):
            outer = defaultdict(lambda: defaultdict(float))
            for region, month, amount in sales:
                outer[region][month] += amount
            return {region: dict(months) for region, months in sorted(outer.items())}
        """,
        why="""The factory must itself build a new `defaultdict(float)`, hence the `lambda`: `defaultdict(defaultdict)` would create
        inner dicts with no factory of their own. Both levels are converted, so the caller gets plain dicts that print, compare
        and serialise normally. This is a pivot table (`pd.pivot_table` or a Power BI matrix visual with region on rows and
        month on columns) built from one pass."""),
    refactor("Counting and grouping by hand", "medium",
        prompt="Rewrite with `Counter` and `defaultdict`, same results. Keep the tests green.",
        code="""
        def summarise_errors(logs):
            counts = {}
            examples = {}
            for line in logs:
                level, msg = line.split(": ", 1)
                if level in counts:
                    counts[level] = counts[level] + 1
                else:
                    counts[level] = 1
                if level not in examples:
                    examples[level] = []
                examples[level].append(msg)
            return counts, examples
        """,
        tests="""
        logs = ["ERROR: timeout", "WARN: slow", "ERROR: rate limited"]
        counts, examples = summarise_errors(logs)
        assert counts == {"ERROR": 2, "WARN": 1}
        assert examples == {"ERROR": ["timeout", "rate limited"], "WARN": ["slow"]}
        """,
        hints=["One `defaultdict(list)` for the messages is enough: the counts are just the lengths of the lists."],
        solution="""
        from collections import Counter, defaultdict

        def summarise_errors(logs):
            examples = defaultdict(list)
            for line in logs:
                level, msg = line.split(": ", 1)
                examples[level].append(msg)
            counts = Counter({level: len(msgs) for level, msgs in examples.items()})
            return counts, dict(examples)
        """,
        why="""The two hand-written "create if missing" branches collapse into one `defaultdict(list)`, and the counts do not need
        their own bookkeeping because they are derivable from the groups. Keeping one source of truth removes the chance of the
        two dicts disagreeing. `split(": ", 1)` splits only at the first separator, so messages may contain `": "` (lesson 5.2).
        A `Counter` compares equal to a plain dict with the same counts, which is why the test passes."""),
    predict("itertools.groupby needs sorted input", "medium",
        code="""
        from itertools import groupby

        tickets = [("billing", 1), ("auth", 2), ("billing", 3), ("billing", 4), ("auth", 5)]
        print([(team, [i for _, i in grp]) for team, grp in groupby(tickets, key=lambda t: t[0])])
        ordered = sorted(tickets, key=lambda t: t[0])
        print([(team, [i for _, i in grp]) for team, grp in groupby(ordered, key=lambda t: t[0])])
        groups = groupby(ordered, key=lambda t: t[0])
        kept = [(team, grp) for team, grp in groups]
        print([(team, list(grp)) for team, grp in kept])
        """,
        hints=["`groupby` starts a new group whenever the key changes. Each group is a lazy iterator that shares the underlying iterator."],
        why="""On unsorted input `billing` appears as two separate groups, because `groupby` only merges **consecutive** items with
        the same key. Sorting by the key first gives true groups (and the sort is stable, so the ids stay in order). The last
        line is the subtle trap: each group is a lazy view of one shared iterator, so storing the groups and consuming them
        later finds them already exhausted, except possibly the last one. Turn each group into a list immediately, as the
        first two lines do."""),
)

section("hard", "Hard",
    write("Several aggregates per group in one pass", "hard", tag="Interview",
        prompt="""Write `group_stats(rows, by, value)` for a list of dicts: group by the field `by` and return a dict from
        group to `{"count": ..., "sum": ..., "mean": ..., "min": ..., "max": ...}` for the field `value`, groups in sorted
        order. Rows missing the value field are skipped. Do it in one pass without storing the values of each group.""",
        code="""
        def group_stats(rows, by, value):
            pass
        """,
        tests="""
        rows = [{"model": "small", "ms": 120}, {"model": "large", "ms": 900}, {"model": "small", "ms": 80},
                {"model": "small"}, {"model": "large", "ms": 700}]
        assert group_stats(rows, "model", "ms") == {
            "large": {"count": 2, "sum": 1600, "mean": 800.0, "min": 700, "max": 900},
            "small": {"count": 2, "sum": 200, "mean": 100.0, "min": 80, "max": 120},
        }
        assert group_stats([], "model", "ms") == {}
        """,
        hints=["Keep running `count`, `sum`, `min` and `max` per group in a dict of dicts; compute `mean` at the end.",
               "For the first value of a group, `min` and `max` start from that value."],
        solution="""
        def group_stats(rows, by, value):
            acc = {}
            for row in rows:
                if value not in row:
                    continue
                v = row[value]
                s = acc.get(row[by])
                if s is None:
                    acc[row[by]] = {"count": 1, "sum": v, "min": v, "max": v}
                else:
                    s["count"] += 1
                    s["sum"] += v
                    s["min"] = min(s["min"], v)
                    s["max"] = max(s["max"], v)
            return {g: {**s, "mean": s["sum"] / s["count"]} for g, s in sorted(acc.items())}
        """,
        why="""Each aggregate is updated in O(1) per row, so the whole function is O(n) time and O(number of groups) memory: the
        values of a group are never stored, which is what lets this run over a stream or a huge file. The mean is derived from
        `sum` and `count` at the end instead of being averaged incrementally. This is exactly how a database executes
        `SELECT model, COUNT(ms), SUM(ms), AVG(ms), MIN(ms), MAX(ms) FROM rows GROUP BY model` with hash aggregation, and what
        `df.groupby("model")["ms"].agg(["count", "sum", "mean", "min", "max"])` does in pandas. Note that rows missing the value
        are skipped, which matches SQL's behaviour of ignoring NULLs in aggregates."""),
    fix("Read the code: an LRU cache that forgets the wrong things", "hard", tag="GenAI",
        prompt="""This caches embeddings so repeated texts are not sent to the API again, keeping at most `capacity` entries.
        It evicts entries that were just used and keeps stale ones, and its hit counter is wrong. Read the module, find the
        bugs, and fix them so it is a correct LRU cache.""",
        code="""
        from collections import OrderedDict


        def make_embedding_cache(embed, capacity):
            store = OrderedDict()
            stats = {"hits": 0, "misses": 0}

            def get(text):
                if text in store:
                    stats["hits"] =+ 1
                    return store[text]
                stats["misses"] += 1
                vector = embed(text)
                store[text] = vector
                if len(store) > capacity:
                    store.popitem()
                return vector

            return get, stats
        """,
        tests="""
        calls = []
        def embed(t):
            calls.append(t)
            return [len(t)]
        get, stats = make_embedding_cache(embed, capacity=2)
        get("a"); get("bb"); get("a")
        get("ccc")
        get("a")
        assert calls == ["a", "bb", "ccc"]
        get("bb")
        assert calls == ["a", "bb", "ccc", "bb"]
        assert stats == {"hits": 2, "misses": 4}
        """,
        hints=["On a hit, the entry must become the most recently used: `store.move_to_end(text)`.",
               "`popitem()` with no argument removes the **newest** entry. Which one should an LRU cache remove?",
               "Look closely at `=+ 1`."],
        solution="""
        from collections import OrderedDict


        def make_embedding_cache(embed, capacity):
            store = OrderedDict()
            stats = {"hits": 0, "misses": 0}

            def get(text):
                if text in store:
                    stats["hits"] += 1
                    store.move_to_end(text)
                    return store[text]
                stats["misses"] += 1
                vector = embed(text)
                store[text] = vector
                if len(store) > capacity:
                    store.popitem(last=False)
                return vector

            return get, stats
        """,
        why="""Three bugs. A hit did not refresh the entry, so the order was "first inserted" rather than "last used", which is
        FIFO, not LRU. `popitem()` defaults to `last=True` and removed the entry just inserted, so a full cache threw away every
        new vector; `last=False` removes the oldest. And `stats["hits"] =+ 1` is `= +1`: it sets the counter to 1 instead of
        adding, a typo Python accepts silently. Walking the test: after `a, bb, a`, the order is `bb, a`; inserting `ccc` evicts
        `bb`; `a` is a hit; `bb` is a miss again. In production use `functools.lru_cache` for pure functions, or a shared cache
        such as Redis when several processes need the same embeddings."""),
    write("Reciprocal rank fusion", "hard", tag="RAG",
        prompt="""Hybrid search runs a keyword search and a vector search, each returning document ids best first. Write
        `rrf(rankings, k=60)` that fuses any number of ranked lists: each document gets `sum(1 / (k + rank))` over the lists it
        appears in, with rank starting at 1. Return the document ids ordered by fused score, highest first, ties broken by id
        ascending.""",
        code="""
        from collections import defaultdict

        def rrf(rankings, k=60):
            pass
        """,
        tests="""
        bm25 = ["d3", "d1", "d7"]
        vector = ["d1", "d9", "d3"]
        assert rrf([bm25, vector]) == ["d1", "d3", "d9", "d7"]
        assert rrf([["a", "b"]], k=0) == ["a", "b"]
        assert rrf([]) == []
        assert rrf([["x"], ["y"]]) == ["x", "y"]
        """,
        hints=["`scores = defaultdict(float)`; for each list, `for rank, doc in enumerate(ranking, start=1): scores[doc] += 1 / (k + rank)`.",
               "Sort with the key `(-score, doc)`."],
        solution="""
        from collections import defaultdict

        def rrf(rankings, k=60):
            scores = defaultdict(float)
            for ranking in rankings:
                for rank, doc in enumerate(ranking, start=1):
                    scores[doc] += 1 / (k + rank)
            return sorted(scores, key=lambda doc: (-scores[doc], doc))
        """,
        why="""RRF only uses **ranks**, not raw scores, which is why it works for combining BM25 scores and cosine similarities that
        live on completely different scales. A document ranked well by both lists (`d1`: 2nd and 1st) beats one ranked first by
        only one list. The constant `k = 60` comes from the original paper (Cormack and others, 2009) and dampens the advantage
        of the very top ranks. `defaultdict(float)` accumulates scores for documents seen in any list, and the tuple key makes
        ties deterministic. Elasticsearch, OpenSearch and many vector databases offer RRF for hybrid search."""),
    predict("Counter arithmetic and equality", "hard",
        code="""
        from collections import Counter

        a = Counter(x=3, y=1)
        b = Counter(x=1, y=4, z=2)
        print(a - b, b - a)
        c = Counter(a)
        c.subtract(b)
        print(c)
        print(a & b, a | b)
        print(Counter(x=1, y=0) == Counter(x=1), Counter(x=1, y=0) == {"x": 1})
        print(sorted(Counter("abracadabra").elements())[:6])
        """,
        hints=["The `-` operator drops counts at zero or below; `subtract()` keeps them.",
               "`&` takes the minimum per key and `|` the maximum, keeping only positive results."],
        why="""`a - b` keeps only `x` (3 − 1 = 2), because `y` would be −3; `b - a` keeps `y` (3) and `z` (2). `subtract` is the
        method version and keeps zero and negative counts. `&` and `|` give per-key minimum and maximum. Since Python 3.10, two
        Counters compare equal when their positive and zero counts match, treating a missing key as 0, so `Counter(x=1, y=0) ==
        Counter(x=1)` is `True`; comparing with a plain dict uses ordinary dict equality, where the extra `y` key makes them
        differ. `elements()` repeats each item by its count, which is handy for turning counts back into a list."""),
)

section("interview", "Interview questions",
    explain("`Counter`, `defaultdict(int)` or a plain dict with `get`: how do you choose for counting?", "medium", tag="Interview",
        why="""All three are O(1) per item. `Counter` is the most expressive: it counts a whole iterable in one call (implemented in
        C, so it is fastest for bulk counting), treats missing items as 0 without inserting them, and adds `most_common`,
        `total` and count arithmetic. `defaultdict(int)` is best when counting is mixed with other per-key logic in a loop; its
        catch is that any read of a missing key inserts it. A plain dict with `d.get(k, 0) + 1` needs no import and has no hidden
        behaviour, which suits small or one-off code. Mention returning plain dicts or Counters from functions, never a
        `defaultdict`, so callers do not inherit auto-creation."""),
    explain("How would you compute GROUP BY with several aggregates in pure Python, and when would you switch to pandas?", "medium", tag="Interview",
        why="""One pass with a dict keyed by the group (a tuple for several columns): keep running aggregates per group (count,
        sum, min, max, and for variance also a sum of squares, or Welford's online algorithm), and derive the mean and other
        statistics at the end. That is O(n) time and O(number of groups) memory, and it works on streams that do not fit in
        memory. Switch to pandas (or SQL, or Polars) when the data fits in memory as columns and you want vectorised speed,
        many aggregates, joins and readable code: `df.groupby(["region", "month"]).agg(...)`. Stay in pure Python for streaming
        logs, small data in a service, or when you cannot add a dependency. Mention that SQL engines implement GROUP BY with
        exactly this hash-aggregation idea."""),
    explain("Design an LRU cache. What data structures do you use, and what is the cost of each operation?", "hard", tag="Interview",
        why="""You need O(1) lookup by key and O(1) "move this entry to most recent" and "remove the least recent". The classic
        design combines a hash map from key to node with a doubly linked list ordered by recency: a hit moves the node to the
        front, an insert adds at the front, and eviction removes from the back, all O(1). In Python, `OrderedDict` provides
        exactly that combination internally, with `move_to_end` and `popitem(last=False)`, and `functools.lru_cache` gives it
        for pure functions as a decorator. Discuss capacity and memory (cache entries keep objects alive), thread safety (a lock
        around updates, Module 14), what to use as the key (normalise and hash inputs, 2.2), and when a shared cache such as
        Redis is needed instead because several processes serve requests."""),
)

recap(
    "`Counter` counts in one call, treats missing items as 0, and gives `most_common`, `total` and count arithmetic. `update` adds.",
    "`defaultdict(factory)` creates values on first access. Reads with `d[k]` create entries too: use `in` or `get`, and return plain dicts.",
    "GROUP BY in Python: a dict keyed by the group (a tuple for several columns) with running aggregates, one pass, O(n).",
    "`itertools.groupby` only groups consecutive items: sort by the key first, and consume each group immediately.",
    "`OrderedDict.move_to_end` and `popitem(last=False)` make an O(1) LRU cache; RRF fuses ranked lists using ranks only.",
)
