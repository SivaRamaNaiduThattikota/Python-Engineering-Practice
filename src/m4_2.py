from lesson import *
from diagrams import *

lesson(
    id="m4-2", num="4.2", title="Lists: sorting, searching and cost",
    intro="How Python's sort behaves on real data (stable, and much faster on data that is already partly sorted), binary "
          "search with `bisect`, top-k without sorting everything, why NaN quietly breaks a sort, and how to reason about "
          "and measure cost.",
    desc="`sort` vs `sorted`, keys, stable sorting, `in` is O(n), `bisect`.",
    keys="sort sorted stable timsort runs adaptive comparisons cmp_to_key binary search bisect bisect_left bisect_right insort heapq nlargest nsmallest top k quickselect nan big o timeit",
)

term("Stable sort", "A sort that keeps items with equal keys in their original order. Python's sort is always stable.")
term("Timsort", "The algorithm behind Python's `sort`: it finds runs that are already in order and merges them, so partly sorted data sorts quickly.")
term("Binary search", "Finding a position in a sorted list by repeatedly halving the range: O(log n) instead of O(n).")
term("bisect", "The standard-library module for binary search on sorted lists: `bisect_left`, `bisect_right` and `insort`.")
term("Top-k", "The k largest (or smallest) items. `heapq.nlargest(k, xs)` finds them in O(n log k) without sorting everything.")

section("sort", "`sort`, `sorted` and stability",
    fig(table(["step", "rows (name, dept)"], [
        ["input", "(Bo, ops) (Ana, ml) (Cy, ops) (Di, ml)"],
        ["sort by name", "(Ana, ml) (Bo, ops) (Cy, ops) (Di, ml)"],
        ["then sort by dept", "(Ana, ml) (Di, ml) (Bo, ops) (Cy, ops)"],
    ], label="a stable sort keeps earlier order among equal keys"),
        "Python's sort is stable: after sorting by department, people inside each department are still in name order from the first sort."),
    p("""`xs.sort()` sorts the list **in place** and returns `None`; `sorted(iterable)` builds a **new** list from any
    iterable (2.2). Both take `key=` (3.5) and `reverse=True`. Both are **stable**: items whose keys are equal keep the
    order they had before the sort. Stability is what lets you sort by several rules in separate passes, least important
    first, and it holds even with `reverse=True`."""),
    ex("""
    tickets = [("billing", "B-7"), ("auth", "A-2"), ("billing", "B-3"), ("auth", "A-9")]
    print(sorted(tickets, key=lambda t: t[0]))                 # B-7 stays before B-3, A-2 before A-9
    print(sorted(tickets, key=lambda t: t[0], reverse=True))   # still stable within each team

    by_id = sorted(tickets, key=lambda t: t[1])                # secondary rule first
    print(sorted(by_id, key=lambda t: t[0]))                   # primary rule second: both hold
    """, "stability.py"),
    callout("sql", "SQL / Power BI", """`ORDER BY team, id` in SQL is one tuple key in Python: `key=lambda t: (t[0], t[1])`.
    SQL makes no promise about the order of rows with equal sort values unless you list enough columns; Python's
    stability **is** that promise, which is why the two-pass trick works and why a sort never shuffles ties."""),
)

section("timsort", "How the sort behaves on real data",
    p("""Python uses **Timsort**. Step by step: it scans the list for **runs**, stretches that are already ascending (or
    strictly descending, which it reverses), extends short runs with insertion sort, and then merges runs pairwise, much like
    merge sort. The consequences you can rely on:"""),
    p("""- **Worst case O(n log n)** comparisons, and never the O(n²) worst case some quicksorts have.
    - **Adaptive:** already sorted or reversed data takes about n comparisons, O(n). Data that is "mostly sorted" (log lines
      appended in time order with a few late arrivals, scores that change a little between runs) is much cheaper than random
      data.
    - **Stable**, as above, and it only uses `<` between keys."""),
    p("""You can watch this by counting comparisons. `functools.cmp_to_key` wraps an old-style comparison function, and ours
    counts every call:"""),
    ex("""
    import random
    from functools import cmp_to_key

    def count_comparisons(data):
        calls = 0
        def cmp(a, b):
            nonlocal calls
            calls += 1
            return (a > b) - (a < b)
        sorted(data, key=cmp_to_key(cmp))
        return calls

    n = 1000
    ordered = list(range(n))
    random.seed(0)
    shuffled = random.sample(ordered, n)
    nearly = ordered[:]
    for i in range(0, n, 100):                 # a few items out of place
        nearly[i], nearly[i + 1] = nearly[i + 1], nearly[i]
    print("sorted  ", count_comparisons(ordered))
    print("reversed", count_comparisons(ordered[::-1]))
    print("nearly  ", count_comparisons(nearly))
    print("shuffled", count_comparisons(shuffled))
    """, "comparisons.py"),
    p("""Sorted and reversed input cost about n comparisons; random input costs many more, roughly `n * log2(n)`, and the
    nearly sorted case sits in between. The rule of thumb: **sorting is cheap, but not free**. Sort once and reuse the result
    rather than sorting inside a loop, and do not sort at all when you only need the minimum, the maximum or a few top items
    (next sections)."""),
)

section("search", "Searching: linear scans and binary search",
    fig(flowchart({
        "once": ("ask", 0, 0, "searching|only once?"),
        "scan": ("step", 1, 0, "linear scan: x in xs|O(n)"),
        "sorted": ("ask", 0, 1, "is the data|sorted?"),
        "bis": ("good", 1, 1, "bisect: O(log n)"),
        "hash": ("good", 0, 2, "build a set or dict once,|then O(1) lookups"),
    }, [("once", "scan", "yes"), ("once", "sorted", "no"), ("sorted", "bis", "yes"), ("sorted", "hash", "no")], cell=(250, 84),
        label="choosing how to search"),
        "Choosing a search: one lookup is a scan; many lookups pay for sorting once (bisect) or for building a set or dict."),
    p("""`x in xs`, `xs.index(x)` and `xs.count(x)` scan from the front: O(n). If you search a list many times, either put
    the values in a `set` or `dict` (O(1) per lookup, 4.4) or, when you need **order-based** questions ("where would this
    value go?", "how many values are below 0.5?", "all events between two times"), keep the list **sorted** and use
    **binary search**."""),
    p("""Binary search step by step: look at the middle item of the range. If the target is smaller, keep only the left half;
    otherwise keep the right half. Repeat until the range is empty. Each step halves the range, so a million items need
    about 20 steps. The `bisect` module implements it correctly (writing it yourself is a famous source of off-by-one bugs,
    problem 8):"""),
    p("""- `bisect_left(xs, x)`: the first position where `x` could be inserted and keep `xs` sorted, which is **before** any
      items equal to `x`.
    - `bisect_right(xs, x)` (or plain `bisect`): the position **after** any items equal to `x`.
    - `insort(xs, x)`: insert `x` at the right place. Finding the place is O(log n), but inserting still shifts items, O(n)."""),
    ex("""
    from bisect import bisect_left, bisect_right, insort

    latencies = [12, 15, 15, 15, 20, 31, 48]       # sorted
    print(bisect_left(latencies, 15), bisect_right(latencies, 15))
    print(bisect_right(latencies, 15) - bisect_left(latencies, 15))   # how many are exactly 15
    print(bisect_left(latencies, 30), len(latencies) - bisect_left(latencies, 30))  # values >= 30
    insort(latencies, 18)
    print(latencies)
    """, "bisect_basics.py"),
    p("""The two "how many" lines are the useful pattern: with a sorted list, **counts in a range** are a subtraction of two
    bisect positions, O(log n) each, instead of a scan. Since Python 3.10 the `bisect` functions also take `key=`, so you can
    search a sorted list of records by one field."""),
)

section("topk", "Top-k without sorting everything",
    fig(chain(["n scored items", "heapq.nlargest(k, ...)", "keeps only k items|in a heap", ("top k in O(n log k)", "good")]),
        "Top-k without sorting everything: the heap never holds more than k items."),
    p("""To get the 10 best of a million scores, sorting all of them is O(n log n) work to keep 10 items. `heapq.nlargest(k,
    xs)` walks the data once while keeping only the best `k` in a small heap, about O(n log k) time and O(k) memory, and it
    works on any iterable, including a generator that never fits in memory (Module 6). `heapq.nsmallest` is the mirror. For
    a single best item, `max` and `min` are O(n) and simplest of all."""),
    ex("""
    import heapq

    scores = {"d1": 0.31, "d2": 0.92, "d3": 0.77, "d4": 0.92, "d5": 0.15}
    print(heapq.nlargest(3, scores.items(), key=lambda kv: kv[1]))
    print(heapq.nsmallest(2, scores, key=scores.get))
    print(max(scores, key=scores.get))
    """, "top_k.py"),
    callout("note", "Rules of thumb for k", """For k = 1, use `max` / `min`. For small k (say up to a few hundred) on big
    data, use `heapq.nlargest`. When k is a large fraction of n, plain `sorted(...)[:k]` is just as fast. For numpy arrays,
    `np.argpartition(arr, -k)[-k:]` finds the top-k positions in O(n), then you sort only those k."""),
)

section("nan", "What breaks a sort: NaN and mixed types",
    p("""A sort assumes its comparisons are consistent: if `a < b` and `b < c`, then `a < c`. **NaN breaks that**, because
    every comparison with NaN is `False` (2.1). Python does not raise an error; it just produces an order that is not
    sorted, and where the NaNs end up depends on the input. Mixed types fail loudly instead: Python 3 refuses to compare,
    say, `None` with a number (3.5)."""),
    ex("""
    nan = float("nan")
    scores = [0.3, nan, 0.9, 0.1, nan, 0.5]
    print(sorted(scores))                          # NOT sorted, and no error
    import math
    clean = sorted(s for s in scores if not math.isnan(s))
    print(clean)
    print(sorted(scores, key=lambda s: (math.isnan(s), s)))   # NaNs last, the rest in order
    """, "nan_sort.py"),
    p("""This matters in ML, where a model can output NaN for a bad input and a ranking step silently mis-orders every item
    around it. Filter NaNs out, or sort with a key that puts them in a group of their own, as above. (numpy's `np.sort` and
    pandas put NaN at the end by design.)"""),
)

section("warmup", "Warm-up",
    predict("Stable sorting with reverse", "easy",
        code="""
        runs = [("exp-a", 0.81), ("exp-b", 0.79), ("exp-c", 0.81), ("exp-d", 0.79)]
        print([r[0] for r in sorted(runs, key=lambda r: r[1])])
        print([r[0] for r in sorted(runs, key=lambda r: r[1], reverse=True)])
        print([r[0] for r in sorted(runs, key=lambda r: -r[1])])
        print([r[0] for r in sorted(runs, reverse=True)])
        """,
        hints=["Equal keys keep their original order, even with `reverse=True`.",
               "Without a key, tuples compare by their first element, the name."],
        why="""With `key=score`, the two 0.79 runs keep their original order (b before d), and so do the 0.81 runs (a before c).
        `reverse=True` puts 0.81 first and still keeps each group in its original order, which is exactly what the negated key
        does too. Without a key, the tuples are compared as wholes, by name first, so `reverse=True` simply orders names from
        d down to a."""),
    write("Map a score to a band with bisect", "easy", tag="ML",
        prompt="""Write `band(score, cutoffs, labels)` where `cutoffs` is sorted, `len(labels) == len(cutoffs) + 1`, and a
        score below `cutoffs[0]` gets `labels[0]`, a score at or above `cutoffs[i]` (and below the next cutoff) gets
        `labels[i + 1]`. Use `bisect`, not an `if` chain.""",
        code="""
        from bisect import bisect_right

        def band(score, cutoffs, labels):
            pass
        """,
        tests="""
        cut = [0.4, 0.7, 0.9]
        lab = ["low", "medium", "high", "critical"]
        assert [band(s, cut, lab) for s in [0.1, 0.4, 0.69, 0.7, 0.95, 0.9]] == ["low", "medium", "medium", "high", "critical", "critical"]
        assert band(0.5, [], ["only"]) == "only"
        """,
        hints=["`bisect_right(cutoffs, score)` counts how many cutoffs are less than or equal to the score. That count is the label index."],
        solution="""
        from bisect import bisect_right

        def band(score, cutoffs, labels):
            return labels[bisect_right(cutoffs, score)]
        """,
        why="""`bisect_right` returns the number of cutoffs `<=` score, which is exactly the index of the band, so a score equal
        to a cutoff moves up into the next band (0.4 is `"medium"`). With `bisect_left`, an exact cutoff would stay in the lower
        band; choosing between them is choosing which side the boundary belongs to. The Python docs use this exact pattern for
        exam grades; in ML it turns probabilities into risk bands, and pandas `pd.cut` does it for whole columns."""),
    fix("Chunk files sorted in the wrong order", "easy", tag="RAG",
        prompt="""Chunk files are named like `doc_2.txt`, `doc_10.txt`. Sorting them puts `doc_10` before `doc_2`, so the
        document is reassembled in the wrong order. Fix `ordered` so files sort by the number in their name.""",
        code="""
        def ordered(names):
            return sorted(names)
        """,
        tests="""
        files = ["doc_10.txt", "doc_2.txt", "doc_1.txt", "doc_33.txt", "doc_3.txt"]
        assert ordered(files) == ["doc_1.txt", "doc_2.txt", "doc_3.txt", "doc_10.txt", "doc_33.txt"]
        assert ordered([]) == []
        """,
        hints=["Strings compare character by character, so `\"1\" < \"2\"` decides `doc_10` versus `doc_2`. Sort by the number instead.",
               "Take the part between `_` and `.`: `name.split(\"_\")[1].split(\".\")[0]`, and convert it with `int`."],
        solution="""
        def ordered(names):
            return sorted(names, key=lambda n: int(n.split("_")[1].split(".")[0]))
        """,
        why="""String order is lexicographic: `"doc_10"` and `"doc_2"` differ first at `"1"` versus `"2"`, so 10 sorts first. A
        numeric key fixes it. Version strings have the same problem (`"1.10" < "1.9"` as strings); the fix there is
        `key=lambda v: tuple(int(p) for p in v.split("."))`. For general "natural sort" of arbitrary names, split each name into
        text and number parts with a regex (lesson 5.5)."""),
    predict("bisect_left and bisect_right with duplicates", "easy",
        code="""
        from bisect import bisect_left, bisect_right

        xs = [1, 3, 3, 3, 7]
        print(bisect_left(xs, 3), bisect_right(xs, 3))
        print(bisect_left(xs, 0), bisect_right(xs, 9))
        print(bisect_left(xs, 5), bisect_right(xs, 5))
        print(xs[bisect_left(xs, 3):bisect_right(xs, 3)])
        """,
        hints=["Left means \"before all the equal items\", right means \"after them\". For a missing value they agree."],
        why="""For 3, the left insertion point is position 1 and the right one is position 4, so the slice between them is
        exactly the three 3s. Values below everything go to 0; above everything, to `len(xs)`. A value not present (5) has a
        single insertion point, so both functions return 4. Slicing between the two positions is the standard way to fetch all
        items equal to a value, or in a range, from a sorted list."""),
)

section("medium", "Medium",
    write("Rank with ties", "medium", tag="ML",
        prompt="""Write `ranks(scores)` that returns the rank of each score in the original order, where rank 1 is the highest
        and tied scores share the best rank they would get (competition ranking: 1, 2, 2, 4). Do it with one sort.""",
        code="""
        def ranks(scores):
            pass
        """,
        tests="""
        assert ranks([0.9, 0.7, 0.8, 0.7]) == [1, 3, 2, 3]
        assert ranks([5, 5, 5]) == [1, 1, 1]
        assert ranks([1, 2, 3, 4]) == [4, 3, 2, 1]
        assert ranks([]) == []
        """,
        hints=["Sort the positions by score, highest first: `order = sorted(range(len(scores)), key=lambda i: -scores[i])`.",
               "Walk `order`; when a score equals the previous one, reuse the previous rank, otherwise the rank is the current position + 1."],
        solution="""
        def ranks(scores):
            order = sorted(range(len(scores)), key=lambda i: -scores[i])
            out = [0] * len(scores)
            for pos, i in enumerate(order):
                if pos > 0 and scores[i] == scores[order[pos - 1]]:
                    out[i] = out[order[pos - 1]]
                else:
                    out[i] = pos + 1
            return out
        """,
        why="""Sorting the **positions** (an "argsort") rather than the scores keeps track of where each score came from, so the
        ranks can be written back in the original order. Equal scores are adjacent after the sort, so one comparison with the
        previous item detects ties. This is SQL's `RANK()` window function; `DENSE_RANK()` would give 1, 2, 2, 3. In pandas,
        `s.rank(method="min", ascending=False)` does this one, and numpy's `argsort` is the array version of `order`."""),
    choose("Top 10 of a million", "medium", tag="RAG",
        prompt="Both return the 10 highest of one million similarity scores. Which is faster?",
        setup="""import random, heapq
random.seed(1)
scores = [random.random() for _ in range(1_000_000)]""",
        options={
            "a": "top = sorted(scores, reverse=True)[:10]",
            "b": "top = heapq.nlargest(10, scores)",
        },
        answer="b",
        hints=["How much of the million items does each approach have to put in order?"],
        why="""`sorted` puts all million scores in order, O(n log n), to keep ten. `nlargest` keeps a heap of only the best 10 and
        compares each new score with the heap's smallest item, which usually rejects it immediately: about O(n log k) with tiny
        constant work per item. Retrieval systems face this exact choice after scoring every chunk; vector databases go further
        and avoid scoring every item at all, with approximate indexes."""),
    write("Events in a time range", "medium", tag="Data work",
        prompt="""`times` is a sorted list of event timestamps (seconds). Write `count_between(times, start, end)` returning how
        many events have `start <= t < end`, and `events_between(times, start, end)` returning them as a list. Both must use
        `bisect`, so each query is O(log n) plus the size of the answer.""",
        code="""
        from bisect import bisect_left

        def count_between(times, start, end):
            pass

        def events_between(times, start, end):
            pass
        """,
        tests="""
        t = [10, 12, 12, 15, 20, 20, 31]
        assert count_between(t, 12, 20) == 3
        assert events_between(t, 12, 20) == [12, 12, 15]
        assert count_between(t, 0, 100) == 7 and count_between(t, 21, 31) == 0
        assert events_between(t, 20, 21) == [20, 20]
        assert count_between([], 1, 2) == 0
        """,
        hints=["For a half-open range `[start, end)`, both bounds use `bisect_left`: the first position `>= start` and the first position `>= end`."],
        solution="""
        from bisect import bisect_left

        def count_between(times, start, end):
            return max(0, bisect_left(times, end) - bisect_left(times, start))

        def events_between(times, start, end):
            return times[bisect_left(times, start):bisect_left(times, end)]
        """,
        why="""`bisect_left(times, start)` is the first event at or after `start`, and `bisect_left(times, end)` the first event at
        or after `end`, which is exactly where the half-open range stops: events at `end` are excluded. Counting is a
        subtraction, with no scan. `max(0, ...)` handles a backwards range. This is how time-series stores answer "events in
        the last hour" on sorted data, and the same reason a database index on a timestamp makes range queries fast."""),
    fix("A binary search that misses items", "medium", tag="Interview",
        prompt="""This hand-written binary search should return the position of `target` in the sorted list, or -1. It
        reports -1 for some items that are in the list. Fix it.""",
        code="""
        def find(xs, target):
            lo, hi = 0, len(xs) - 1
            while lo < hi:
                mid = (lo + hi) // 2
                if xs[mid] < target:
                    lo = mid + 1
                else:
                    hi = mid - 1
            return lo if xs and xs[lo] == target else -1
        """,
        tests="""
        xs = [2, 5, 8, 12, 16, 23, 38]
        assert [find(xs, x) for x in xs] == list(range(len(xs)))
        assert find(xs, 7) == -1 and find(xs, 1) == -1 and find(xs, 40) == -1
        assert find([], 3) == -1 and find([4], 4) == 0
        """,
        hints=["`hi = mid - 1` throws away position `mid`. What if `xs[mid]` **is** the target?",
               "Use the half-open convention: `lo, hi = 0, len(xs)`, `while lo < hi`, then `lo = mid + 1` or `hi = mid`."],
        solution="""
        def find(xs, target):
            lo, hi = 0, len(xs)
            while lo < hi:
                mid = (lo + hi) // 2
                if xs[mid] < target:
                    lo = mid + 1
                else:
                    hi = mid
            return lo if lo < len(xs) and xs[lo] == target else -1
        """,
        why="""When `xs[mid]` equals the target, the `else` branch runs `hi = mid - 1` and the target's own position is excluded,
        so the search can finish on a neighbour and report -1. The other classic mistake is the mirror image, `lo = mid`, which
        never shrinks the range once `hi == lo + 1` and loops **forever**. The half-open version avoids both with one invariant:
        the answer is always in `[lo, hi)`, every pass strictly shrinks it, and at the end `lo` is the leftmost position where
        `target` could go, exactly what `bisect_left` returns. In real code call `bisect_left`; in interviews, state the invariant
        out loud, because that is what they are checking."""),
    trace("Binary search, step by step", "medium",
        prompt="""Fill in `lo`, `hi` and the item looked at (`seen`) after each pass, searching for 23 in a list of 7 items.""",
        code="""
        xs = [2, 5, 8, 12, 16, 23, 38]
        target = 23
        lo, hi = 0, len(xs)
        while lo < hi:
            mid = (lo + hi) // 2
            if xs[mid] < target:
                lo = mid + 1
            else:
                hi = mid
            seen = xs[mid]  # row: f"pass looking at position {mid}"
        """,
        trace_vars=["lo", "hi", "seen"],
        hints=["Each pass looks at `xs[mid]`: smaller than 23 means the answer is to the right (`lo = mid + 1`), otherwise `hi = mid`."],
        why="""The range starts as `[0, 7)`. Position 3 holds 12 < 23, so `lo` becomes 4. Position 5 holds 23, which is not
        smaller, so `hi` becomes 5. Position 4 holds 16 < 23, so `lo` becomes 5, and now `lo == hi == 5`: the loop ends at
        position 5, where 23 is. Three passes for seven items; a million items would take about twenty."""),
    write("Keep streaming results sorted", "medium", tag="GenAI",
        prompt="""Results from several retrievers arrive one at a time. Write `add_result(results, item)` that inserts the dict
        `item` into `results`, which is kept sorted by `item["score"]` **highest first**, using `bisect.insort` with a `key`
        (no full re-sort). Items with equal scores keep arrival order. Return `None`; the list is changed in place.""",
        code="""
        import bisect

        def add_result(results, item):
            pass
        """,
        tests="""
        res = []
        for doc, s in [("a", 0.5), ("b", 0.9), ("c", 0.5), ("d", 0.7), ("e", 0.95)]:
            assert add_result(res, {"doc": doc, "score": s}) is None
        assert [r["doc"] for r in res] == ["e", "b", "d", "a", "c"]
        assert len(res) == 5 and res[0]["score"] == 0.95
        assert add_result(res, {"doc": "f", "score": 0.5}) is None and res[-1]["doc"] == "f"
        """,
        hints=["`insort` keeps a list in **ascending** order of the key. A key of `-score` makes ascending order mean highest score first.",
               "`insort` is `insort_right`: an equal key goes after the existing ones, which keeps arrival order."],
        solution="""
        import bisect

        def add_result(results, item):
            bisect.insort(results, item, key=lambda r: -r["score"])
        """,
        why="""`insort` finds the position by binary search on the keys and inserts there, so the list stays sorted without
        sorting it again: O(log n) to find the place plus O(n) to shift items, cheaper than O(n log n) for a full sort after every
        arrival. The negated score turns "ascending" into "highest first", and because `insort` inserts to the **right** of equal
        keys, results that tie keep the order they arrived in (`a` before `c`). The `key` parameter needs Python 3.10 or
        later."""),
    refactor("Find the best item and its position", "medium",
        prompt="Shorten this to one expression with the same results, including the tie rule (first occurrence wins). Keep the tests green.",
        code="""
        def best(scores):
            best_i = None
            best_s = None
            for i in range(len(scores)):
                if best_s is None or scores[i] > best_s:
                    best_i = i
                    best_s = scores[i]
            return best_i, best_s
        """,
        tests="""
        assert best([0.2, 0.9, 0.4, 0.9]) == (1, 0.9)
        assert best([5]) == (0, 5)
        assert best([]) == (None, None)
        """,
        hints=["`max(enumerate(scores), key=...)` returns the `(index, value)` pair with the largest value, and `max` keeps the first of equal items.",
               "`max(..., default=(None, None))` handles the empty list."],
        solution="""
        def best(scores):
            return max(enumerate(scores), key=lambda p: p[1], default=(None, None))
        """,
        why="""`enumerate` pairs each score with its index, `key` compares by the score, and `max` returns the **first** maximal
        item, which matches the loop's strict `>` tie rule. `default` covers the empty input without a special case. In numpy,
        `arr.argmax()` gives the index the same way, also returning the first maximum."""),
    predict("Counting comparisons", "medium",
        code="""
        from functools import cmp_to_key

        def comparisons(data):
            calls = 0
            def cmp(a, b):
                nonlocal calls
                calls += 1
                return (a > b) - (a < b)
            result = sorted(data, key=cmp_to_key(cmp))
            return calls, result[:3]

        print(comparisons([1, 2, 3, 4, 5, 6, 7, 8]))
        print(comparisons([8, 7, 6, 5, 4, 3, 2, 1]))
        print(comparisons([5, 1, 8, 2, 7, 3, 6, 4]))
        """,
        hints=["Already-sorted input is one run. Strictly descending input is one run that Timsort simply reverses."],
        why="""For sorted input, Timsort only confirms the run: n - 1 = 7 comparisons. Strictly descending input is also detected
        as one run and reversed in place, again 7 comparisons. Shuffled input needs real work, so it costs clearly more. The
        sorted results are the same in all three cases: only the cost depends on how ordered the input was."""),
)

section("hard", "Hard",
    write("The k-th smallest in average O(n)", "hard", tag="Interview",
        prompt="""Write `kth_smallest(xs, k)` returning the k-th smallest value (k = 1 is the minimum) in **average O(n)**
        time, without sorting: quickselect. Pick a random pivot, split into items less than, equal to and greater than it, and
        continue only in the part that contains the answer. Raise `ValueError` if `k` is out of range.""",
        code="""
        import random

        def kth_smallest(xs, k):
            pass
        """,
        tests="""
        def raises(exc, f, *args):
            try:
                f(*args)
            except exc:
                return True
            return False
        data = [7, 2, 9, 4, 4, 1, 8]
        assert [kth_smallest(data, k) for k in range(1, 8)] == sorted(data)
        assert data == [7, 2, 9, 4, 4, 1, 8]
        assert kth_smallest([5], 1) == 5
        assert raises(ValueError, kth_smallest, data, 0) and raises(ValueError, kth_smallest, data, 8)
        import random as _r
        big = [_r.random() for _ in range(5000)]
        assert kth_smallest(big, 2500) == sorted(big)[2499]
        """,
        hints=["Three lists: `lows`, `pivots`, `highs`. If `k <= len(lows)`, the answer is in `lows`; if it is within the pivots, it is the pivot; otherwise look in `highs` with `k` reduced.",
               "A loop that keeps replacing `xs` and `k` avoids deep recursion."],
        solution="""
        import random

        def kth_smallest(xs, k):
            if not 1 <= k <= len(xs):
                raise ValueError("k out of range")
            items = xs
            while True:
                pivot = random.choice(items)
                lows = [x for x in items if x < pivot]
                pivots = [x for x in items if x == pivot]
                if k <= len(lows):
                    items = lows
                elif k <= len(lows) + len(pivots):
                    return pivot
                else:
                    k -= len(lows) + len(pivots)
                    items = [x for x in items if x > pivot]
        """,
        why="""Each pass keeps only the part that can contain the answer, so on average the work is n + n/2 + n/4 + ... = O(2n),
        compared with O(n log n) for sorting. The random pivot makes the bad case (always picking the extreme) very unlikely; the
        `pivots` group handles duplicates, which would otherwise make a two-way split loop forever on data like `[4, 4, 4]`.
        The input is never changed, because each pass builds new lists. In practice, `heapq.nsmallest(k, xs)[-1]` or numpy's
        `np.partition` do this job; quickselect is the classic interview follow-up to "can you do better than sorting?"."""),
    fix("Read the code: a leaderboard upside down", "hard", tag="ML",
        prompt="""A leaderboard for model evaluation runs, kept sorted with `bisect`. `top` returns the worst runs instead of
        the best, `top(board, 0)` returns everything, and `rank_of` gives rank 1 to the worst run. Read the module, find the
        bugs, and fix them. Higher scores are better; ties keep the order runs were added.""",
        code="""
        import bisect


        def add_run(board, name, score):
            bisect.insort(board, (score, name))


        def top(board, k):
            \"\"\"The k best runs as (name, score), best first.\"\"\"
            return [(name, score) for score, name in board[-k:][::-1]]


        def rank_of(board, name):
            \"\"\"1 for the best run.\"\"\"
            for i, (score, n) in enumerate(board):
                if n == name:
                    return i + 1
            raise KeyError(name)
        """,
        tests="""
        board = []
        for name, s in [("run-a", 0.71), ("run-b", 0.88), ("run-c", 0.64), ("run-d", 0.88)]:
            add_run(board, name, s)
        assert top(board, 2) == [("run-b", 0.88), ("run-d", 0.88)]
        assert top(board, 0) == []
        assert rank_of(board, "run-b") == 1 and rank_of(board, "run-d") == 2 and rank_of(board, "run-c") == 4
        assert len(top(board, 10)) == 4
        """,
        hints=["Store the board so that **ascending** order means best first, and equal scores keep insertion order: `insort` with a key of `-score` on `(name, score)` pairs.",
               "Then `top` is just `board[:k]`, which is also safe for `k = 0`, and `rank_of` is position + 1."],
        solution="""
        import bisect


        def add_run(board, name, score):
            bisect.insort(board, (name, score), key=lambda entry: -entry[1])


        def top(board, k):
            \"\"\"The k best runs as (name, score), best first.\"\"\"
            return board[:k]


        def rank_of(board, name):
            \"\"\"1 for the best run.\"\"\"
            for i, (n, score) in enumerate(board):
                if n == name:
                    return i + 1
            raise KeyError(name)
        """,
        why="""The original stored `(score, name)` ascending, so the best runs were at the **end**: `rank_of` counted from the
        worst, and `top` had to slice from the end, where `board[-0:]` returned the whole board (4.1). Equal scores were also
        ordered by **name**, not by when they were added, because the name was part of the tuple being compared. Storing
        `(name, score)` with `key=-score` fixes all three at once: ascending order of the key means best first, `insort` puts
        ties after existing entries (arrival order), and `top` becomes a plain front slice. Choosing the storage order so that the
        common query is the simple one is a general design habit."""),
    write("Merge k ranked lists", "hard", tag="Interview",
        prompt="""Results come from `k` index shards, each already sorted by score **highest first**, as `(score, doc_id)`
        pairs. Write `merge_shards(shards, limit)` returning the overall top `limit` results, highest first, without
        concatenating and sorting everything. Use a heap.""",
        code="""
        import heapq

        def merge_shards(shards, limit):
            pass
        """,
        tests="""
        s1 = [(0.95, "a1"), (0.70, "a2"), (0.10, "a3")]
        s2 = [(0.90, "b1"), (0.85, "b2")]
        s3 = [(0.99, "c1"), (0.20, "c2")]
        assert merge_shards([s1, s2, s3], 4) == [(0.99, "c1"), (0.95, "a1"), (0.90, "b1"), (0.85, "b2")]
        assert merge_shards([s1, s2, s3], 100)[-1] == (0.10, "a3")
        assert merge_shards([[], s2], 1) == [(0.90, "b1")]
        assert merge_shards([], 3) == []
        """,
        hints=["`heapq.merge(*shards, key=lambda r: r[0], reverse=True)` merges already-sorted iterables lazily.",
               "Take only the first `limit` items with `itertools.islice`, so the rest is never even merged."],
        solution="""
        import heapq
        from itertools import islice

        def merge_shards(shards, limit):
            merged = heapq.merge(*shards, key=lambda r: r[0], reverse=True)
            return list(islice(merged, limit))
        """,
        why="""`heapq.merge` keeps one candidate per shard in a heap and repeatedly yields the best, so producing each result costs
        O(log k), and it is lazy: `islice` stops after `limit` items, so most of the data is never touched. Total work is about
        O(limit · log k) instead of sorting everything, O(N log N). `reverse=True` is needed because the inputs are sorted
        highest first. This is the merge step of distributed search (each shard returns its local top results, a coordinator
        merges them) and of external sorting when data does not fit in memory."""),
    predict("NaN in a ranking", "hard", tag="ML",
        code="""
        import math

        nan = float("nan")
        scores = [0.4, nan, 0.9, 0.2, 0.7]
        ranked = sorted(scores, reverse=True)
        print(ranked)
        print(ranked == sorted(ranked, reverse=True))
        print(max(scores), max(scores[1:]), min([nan, 0.1, 0.5]))
        safe = sorted(scores, key=lambda s: (not math.isnan(s), s), reverse=True)
        print(safe)
        """,
        hints=["Every comparison with NaN is `False`, so NaN never counts as larger or smaller. `max` keeps its first item unless something is strictly larger.",
               "If you sort the result a second time, does anything change? Would that tell you the first sort was wrong?"],
        why="""Because NaN compares `False` with everything, the sort cannot place it and the values around it end up out of
        order: `0.9` sits after `0.4`. Worse, sorting the broken result again gives back **the same list** (`True`), so
        "re-sort and compare" cannot detect the problem, and nothing raises an error. `max` and
        `min` are just as fragile: they keep the first item unless a later one compares strictly better, so a NaN in first place
        "wins", while a NaN later on is ignored. The output depends on where the NaN happens to be. The safe sort groups NaNs
        explicitly: the key `(not isnan, value)` with `reverse=True` puts real scores first, highest first, and NaNs last."""),
)

section("interview", "Interview questions",
    explain("What are the properties of Python's sort, and why do they matter?", "medium", tag="Interview",
        why="""Python's `sort`/`sorted` use Timsort: O(n log n) in the worst case, O(n) on already sorted or reverse-sorted
        data (it is adaptive, finding existing runs and merging them), and **stable**, so equal keys keep their original order,
        even with `reverse=True`. Stability enables multi-key sorting in passes (least important key first) and makes results
        deterministic for ties. It compares keys only with `<`, so inconsistent comparisons, such as NaN or mixed types, give
        wrong orders or `TypeError`. `key=` is computed once per item (decorate-sort-undecorate), which is why a key function is
        much cheaper than a comparison function. `sort` is in place and returns `None`; `sorted` returns a new list from any
        iterable."""),
    explain("When would you use binary search (`bisect`) in real code?", "medium", tag="Interview",
        why="""Whenever data is sorted and you ask order-based questions repeatedly: where a value would go, how many values fall
        in a range, which bucket a value belongs to. Examples: mapping scores to bands or grades with cutoffs, counting events
        in a time window from a sorted log, looking up the version or price that applies at a date, percentiles in a sorted
        sample, and keeping a sorted list up to date with `insort`. Each query is O(log n) instead of an O(n) scan. Mention the
        difference between `bisect_left` and `bisect_right` (which side of equal values), the `key=` parameter since Python
        3.10, and that `insort` still costs O(n) to insert, so for heavy insert workloads a heap or a sorted container library
        is better."""),
    explain("You need the top 100 of 100 million scores that arrive as a stream. How do you do it?", "hard", tag="Interview",
        why="""Do not collect and sort everything. Keep a **min-heap of size 100**: push the first 100 scores, then for each new
        score compare it with the heap's smallest; if it is larger, replace the smallest (`heapq.heappushpop`). That is O(n log k)
        time and O(k) memory, and it works on a stream because it never holds more than 100 items. `heapq.nlargest(100,
        stream)` implements exactly this. If the data is already in a numpy array, `np.argpartition` finds the top-k in O(n). If
        it is distributed, compute a local top-100 per partition and merge them (as in problem 15). Mention ties and NaN
        handling, and that approximate methods are acceptable when exact top-k is not needed."""),
)

recap(
    "`sort` (in place, returns `None`) and `sorted` (new list) are stable, O(n log n), and close to O(n) on partly sorted data.",
    "Stability enables multi-key sorts in passes: least important key first, most important last.",
    "`in`, `index` and `count` scan: O(n). On a sorted list, `bisect` answers \"where\" and \"how many in a range\" in O(log n).",
    "For top-k, use `max`/`min` (k = 1), `heapq.nlargest` (small k), or `np.argpartition`; do not sort everything to keep a few.",
    "NaN silently breaks sorting, `max` and `min`. Filter it or give it its own key group.",
)
