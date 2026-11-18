from lesson import *
from diagrams import *

lesson(
    id="m4-p", num="4.P", title="Module 4 practice set and mini project",
    intro="Mixed problems from all of Module 4: lists, sorting and searching, tuples, sets, dicts and the counting and "
          "grouping tools. Then a mini project that needs all of it: an evaluation report for a retrieval system.",
    desc="Mixed problems from the whole module, then one small program that uses all of it.",
    keys="practice mixed review project retrieval evaluation recall mrr data structures list tuple set dict counter bisect",
)

section("how", "How to use this page",
    fig(stage_map(4, "a retrieval evaluation report"), "Module 4 at a glance: the four built-in collections and their tools, building up to an evaluation report."),
    p("""For each problem, first decide **which structure** fits the operations it needs: positions and order (list,
    4.1), sorted order and range questions (4.2), fixed records and composite keys (tuple, 4.3), membership and set algebra
    (set, 4.4), lookup by key (dict, 4.5), or counting and grouping (4.6). Choosing the structure is usually most of the
    solution."""),
)

section("set", "Practice set",
    predict("Slices, tuples and sets together", "easy",
        code="""
        runs = [("r1", 0.81), ("r2", 0.77), ("r3", 0.81), ("r4", 0.60)]
        names, scores = zip(*runs)
        print(names[-2:], scores[::2])
        best = max(runs, key=lambda r: r[1])
        print(best, sorted({s for _, s in runs}, reverse=True))
        first, *_, last = runs
        print(first[0], last[0], len(set(scores)))
        """,
        hints=["`zip(*runs)` transposes. `max` keeps the first of equal items. A set collapses equal scores."],
        why="""`zip(*runs)` gives two tuples, so slicing returns tuples. `max` returns the **first** run with the top score, `r1`,
        not `r3`. The set of scores has three distinct values. Star unpacking with `*_` ignores the middle items."""),
    write("Deduplicate by a key, keeping the first", "easy", tag="Data work",
        prompt="""Write `dedupe(items, key=None)` returning a new list with the first item for each distinct `key(item)`, in
        input order. With `key=None`, items are compared by themselves.""",
        code="""
        def dedupe(items, key=None):
            pass
        """,
        tests="""
        assert dedupe([3, 1, 3, 2, 1]) == [3, 1, 2]
        users = [{"email": "A@x.io", "src": 1}, {"email": "a@x.io", "src": 2}, {"email": "b@x.io", "src": 3}]
        assert [u["src"] for u in dedupe(users, key=lambda u: u["email"].lower())] == [1, 3]
        assert dedupe([]) == []
        """,
        hints=["A `seen` set of keys, and a list of the kept items."],
        solution="""
        def dedupe(items, key=None):
            seen = set()
            out = []
            for item in items:
                k = item if key is None else key(item)
                if k not in seen:
                    seen.add(k)
                    out.append(item)
            return out
        """,
        why="""The set holds **keys**, so the items themselves do not need to be hashable (dicts are fine with a key function), and
        each check is O(1). Keeping the original item rather than the key preserves all its fields. This is the general version
        of `dict.fromkeys` deduplication, the same pattern as pandas `drop_duplicates(subset=...)`, and it works with any
        normalisation you can express as a function."""),
    fix("The most common category is wrong", "easy", tag="Data work",
        prompt="""`top_category(counts)` should return the category with the highest count. It returns `"zip"` for the test
        data, which has the lowest count. Fix it.""",
        code="""
        def top_category(counts):
            return max(counts)
        """,
        tests="""
        assert top_category({"billing": 40, "auth": 75, "zip": 3}) == "auth"
        assert top_category({"a": 1}) == "a"
        """,
        hints=["`max` of a dict iterates over its **keys** and compares them as strings."],
        solution="""
        def top_category(counts):
            return max(counts, key=counts.get)
        """,
        why="""Iterating a dict gives its keys, so `max(counts)` compares category names alphabetically and `"zip"` wins. `key=
        counts.get` compares the counts while still returning the key. `max(counts.items(), key=lambda kv: kv[1])[0]` and
        `Counter(counts).most_common(1)[0][0]` are equivalent. The bug produces a plausible-looking answer, which is why it
        survives until someone checks the numbers."""),
    predict("Views and set operations", "medium",
        code="""
        inventory = {"apple": 3, "pear": 0, "plum": 5}
        wanted = {"apple", "kiwi", "plum"}
        print(sorted(inventory.keys() & wanted), sorted(wanted - inventory.keys()))
        in_stock = {k for k, v in inventory.items() if v}
        print(sorted(in_stock), sorted(inventory.items() - {("pear", 0)}))
        print(sorted(inventory, key=inventory.get, reverse=True)[0])
        """,
        hints=["Key and item views support set operations directly."],
        why="""`keys() & wanted` is the intersection, `wanted - keys()` what is wanted but unknown. A count of 0 is falsy, so
        `"pear"` is not in stock. `items()` behaves like a set of `(key, value)` pairs, so subtracting one pair works. Sorting
        keys by their value with `key=inventory.get` puts the largest stock first."""),
    write("Keep the best copy of duplicate chunks", "medium", tag="RAG",
        prompt="""Retrieval returned duplicate chunks whose text differs only in case and spacing. Write `best_unique(chunks)`
        that keeps, for each normalised text (lower-cased, whitespace collapsed to single spaces, stripped), the chunk with the
        highest `score` (the first one on a tie), and returns them sorted by score, highest first.""",
        code="""
        def best_unique(chunks):
            pass
        """,
        tests="""
        chunks = [{"id": 1, "text": "Refunds take 5 days.", "score": 0.7},
                  {"id": 2, "text": "refunds  take 5 days. ", "score": 0.9},
                  {"id": 3, "text": "Contact support.", "score": 0.4},
                  {"id": 4, "text": "REFUNDS TAKE 5 DAYS.", "score": 0.9}]
        assert [c["id"] for c in best_unique(chunks)] == [2, 3]
        assert best_unique([]) == []
        """,
        hints=["Normalise with `\" \".join(text.lower().split())`, use it as a dict key, and replace the stored chunk only when the new score is strictly higher."],
        solution="""
        def best_unique(chunks):
            best = {}
            for c in chunks:
                key = " ".join(c["text"].lower().split())
                if key not in best or c["score"] > best[key]["score"]:
                    best[key] = c
            return sorted(best.values(), key=lambda c: c["score"], reverse=True)
        """,
        why="""The normalised text is the dict key, so "the same chunk" is defined in exactly one place. Replacing only on a
        strictly higher score keeps the first of equal scores (chunk 2 over chunk 4), and the stable sort keeps that order for
        ties. Returning the original chunk dicts (not copies) preserves ids and metadata for citations."""),
    choose("Allow-list in a tuple or a frozenset", "medium", tag="GenAI",
        prompt="Both check 50,000 requested tool names against an allow-list of 300 names. Which is faster?",
        setup="""names = [f"tool_{i}" for i in range(300)]
as_tuple = tuple(names)
as_set = frozenset(names)
requests = [f"tool_{i % 600}" for i in range(50_000)]""",
        options={
            "a": "ok = sum(1 for r in requests if r in as_tuple)",
            "b": "ok = sum(1 for r in requests if r in as_set)",
        },
        answer="b",
        hints=["How many comparisons does `in` make on a tuple of 300 names when the name is not there?"],
        why="""`in` on a tuple scans it, up to 300 comparisons per request (all 300 for the half of the requests that are not
        allowed). A frozenset hashes the name and checks one slot. Both are immutable, so both are safe to share; the set is
        the right one for membership."""),
    trace("A dict of lists, step by step", "medium",
        prompt="Fill in `d` after each marked line.",
        code="""
        d = {}
        d.setdefault("a", []).append(1)  # row: "setdefault('a').append(1)"
        d.setdefault("a", [99]).append(2)  # row: "setdefault('a', [99]).append(2)"
        d["b"] = d.pop("a")[1:]  # row: "d['b'] = d.pop('a')[1:]"
        d.setdefault("b", []).extend([3, 4])  # row: "extend b"
        """,
        trace_vars=["d"],
        hints=["`setdefault` returns the existing value if the key is there. `pop` removes the key and returns its value."],
        why="""The first `setdefault` creates `[1]` under `"a"`. The second finds `"a"` already present, ignores `[99]`, and
        appends to the existing list. `d.pop("a")` removes `"a"` and returns `[1, 2]`, whose slice `[2]` is stored under
        `"b"`. The last line finds `"b"` and extends it."""),
    fix("A leakage check that misses overlaps", "medium", tag="ML",
        prompt="""`leaked_ids` should report ids that appear in both the training and the test split. It is slow on real
        data, and it misses overlaps because the test ids were loaded from a CSV as strings. Make it fast and correct,
        returning sorted integer ids.""",
        code="""
        def leaked_ids(train_ids, test_ids):
            leaked = []
            for t in test_ids:
                if t in train_ids and t not in leaked:
                    leaked.append(t)
            return leaked
        """,
        tests="""
        train = [1, 2, 3, 10, 42]
        test = ["3", "7", "42", "42", " 10 "]
        assert leaked_ids(train, test) == [3, 10, 42]
        assert leaked_ids([], ["1"]) == []
        """,
        hints=["Normalise both sides to integers (`int(str(x).strip())`), then intersect two sets."],
        solution="""
        def leaked_ids(train_ids, test_ids):
            def norm(x):
                return int(str(x).strip())
            return sorted({norm(t) for t in train_ids} & {norm(t) for t in test_ids})
        """,
        why="""`"3"` and `3` are different values (and hash differently), so the type mismatch hid every overlap, and the loop was
        O(n × m) with membership tests on lists. Normalising first and intersecting two sets is O(n + m). Checking for overlap
        between splits is a standard guard against leakage, which silently inflates evaluation scores; it should run on the same
        normalised ids your pipeline uses."""),
    refactor("A join written as nested loops", "medium", tag="ML",
        prompt="Rewrite this so it runs in O(n + m) with a dict index, same output and order. Keep the tests green.",
        code="""
        def attach_labels(predictions, labels):
            out = []
            for p in predictions:
                for l in labels:
                    if l["id"] == p["id"]:
                        out.append((p["id"], p["pred"], l["label"]))
            return out
        """,
        tests="""
        preds = [{"id": 2, "pred": "spam"}, {"id": 1, "pred": "ham"}, {"id": 9, "pred": "spam"}]
        labs = [{"id": 1, "label": "ham"}, {"id": 2, "label": "ham"}]
        assert attach_labels(preds, labs) == [(2, "spam", "ham"), (1, "ham", "ham")]
        assert attach_labels([], labs) == [] and attach_labels(preds, []) == []
        """,
        hints=["Index the labels by id once (ids are unique here), then look each prediction up."],
        solution="""
        def attach_labels(predictions, labels):
            by_id = {l["id"]: l["label"] for l in labels}
            return [(p["id"], p["pred"], by_id[p["id"]]) for p in predictions if p["id"] in by_id]
        """,
        why="""The nested loops compare every prediction with every label, O(n × m); the dict index makes each match O(1), the hash
        join from 4.5. This version assumes ids are unique in `labels`, which the original did not need; if they can repeat,
        index into lists (4.5, problem 15). Unmatched predictions are skipped, as before (an inner join)."""),
    write("Length buckets for chunking decisions", "hard", tag="RAG",
        prompt="""Before choosing a chunk size, you want the distribution of document lengths. Write `length_histogram(texts,
        edges)` where `edges` is a sorted list of word-count boundaries: return a `Counter`-like plain dict from bucket label to
        count, with labels `"<e0"`, `"e0-e1"`, ..., `">=eN"` (each range includes its lower edge), in bucket order, including
        empty buckets. Use `bisect`.""",
        code="""
        from bisect import bisect_right

        def length_histogram(texts, edges):
            pass
        """,
        tests="""
        texts = ["a b", "a b c d e", "x " * 120, "y " * 600, "one"]
        assert length_histogram(texts, [3, 100, 500]) == {"<3": 2, "3-100": 1, "100-500": 1, ">=500": 1}
        assert list(length_histogram([], [10])) == ["<10", ">=10"]
        """,
        hints=["Build the labels first, then count with `bisect_right(edges, len(text.split()))` as the bucket index (4.2, problem 2)."],
        solution="""
        from bisect import bisect_right

        def length_histogram(texts, edges):
            labels = [f"<{edges[0]}"] + [f"{a}-{b}" for a, b in zip(edges, edges[1:])] + [f">={edges[-1]}"]
            counts = dict.fromkeys(labels, 0)
            for text in texts:
                counts[labels[bisect_right(edges, len(text.split()))]] += 1
            return counts
        """,
        why="""`bisect_right` gives the bucket index directly, with a length equal to an edge going into the bucket that starts at
        that edge, matching the "includes its lower edge" rule. `dict.fromkeys(labels, 0)` creates every bucket up front in order,
        which is safe here because `0` is immutable (unlike `[]`, 2.2), so empty buckets still appear in the report. Pairing
        consecutive edges with `zip(edges, edges[1:])` is a common idiom for ranges. Knowing that most documents are, say, under
        500 words tells you whether chunking is even necessary for them."""),
    explain("Given a list of required operations, how do you choose between a list, deque, set, dict and heap?", "medium", tag="Interview",
        why="""Start from the operations and their frequency. Access by position, appending at the end, keeping order and
        duplicates: **list** (O(1) index and append, O(n) search and front operations). Adding or removing at **both** ends, a
        queue or a sliding window: **deque**. "Is this item present?", deduplication, set algebra: **set** (O(1) membership,
        unordered). Lookup by key, counting, grouping, indexing for joins: **dict** (O(1) by key, ordered by insertion), or
        `Counter`/`defaultdict`. Repeatedly getting the smallest or largest item, top-k, scheduling by priority: **heap**
        (`heapq`, O(log n) push and pop). Sorted order with range queries: a sorted list with `bisect`. Then mention memory, the
        need for hashable keys, and that in data work a numpy array or DataFrame replaces most of these for large numeric
        columns."""),
    explain("State the time complexity of the main list, dict and set operations, and give a case where \"O(1) on average\" breaks down.", "hard", tag="Interview",
        why="""List: index and assignment O(1), append and pop from the end O(1) amortized, insert/pop at the front or middle O(n),
        `in`/`index`/`remove` O(n), sort O(n log n), slicing O(k). Dict and set: lookup, insert, delete and membership O(1) on
        average, iteration O(n), and resizing occasionally O(n) but amortized away. "On average" assumes hashes spread keys
        across slots. It breaks down with many collisions: a class whose `__hash__` returns a constant makes every lookup a scan,
        O(n), and attackers can craft colliding keys against a server, which is why Python randomises string hashes. Also
        mention that the O(1) hides the cost of hashing the key itself, which is O(length) for long strings or tuples."""),
    predict("Everything at once", "hard",
        code="""
        from collections import Counter
        from bisect import bisect_left

        votes = ["b", "a", "b", "c", "a"]
        print(Counter(votes).most_common(1), sorted(Counter(votes).items(), key=lambda kv: (-kv[1], kv[0]))[0])
        scores = sorted([0.2, 0.9, 0.5, 0.5])
        print(bisect_left(scores, 0.5), len(scores) - bisect_left(scores, 0.5))
        merged = {"k": 5} | {"k": 8, "temp": 0.2}
        pairs = [(2, "b"), (1, "z"), (2, "a")]
        print(merged, sorted(pairs)[0], sorted(pairs, key=lambda p: p[0])[1])
        """,
        hints=["`most_common` breaks ties by first appearance. A sort with a key that ignores part of the tuple keeps the original order for that part."],
        why="""`"b"` and `"a"` both have 2 votes; `most_common` breaks the tie by first appearance (`"b"`), while the explicit key
        `(-count, name)` breaks it alphabetically (`"a"`): two "correct" answers, so always decide the tie rule. With duplicates,
        `bisect_left(scores, 0.5)` is the first 0.5, so three scores are at or above 0.5. The merge keeps the later `k`. Sorting
        the pairs fully puts `(1, "z")` first; sorting by the number only keeps `(2, "b")` before `(2, "a")` because the sort is
        stable."""),
)

section("project", "Mini project: a retrieval evaluation report",
    fig(chain(["queries and|retrieved ids", "relevant ids as sets", "precision@k, recall@k,|reciprocal rank", ("report dict", "good")]),
        "The evaluation report: sets for relevance checks, dicts for grouping, sorted lists for ranks."),
    p("""You are comparing retrieval settings for a RAG system. For each test query you have the documents a human marked as
    relevant and the ranked list the system returned. Build the evaluation report. Every rule in the spec maps to a tool from
    this module, and the tests check each one."""),
    write("Evaluate a retrieval run", "hard", key="retrieval-report", tag="Project",
        prompt="""Implement `evaluate(runs, k)`. Each run is a dict with `"query"`, `"topic"`, `"ranked"` (document ids, best
        first, possibly with duplicates) and `"relevant"` (document ids). Return a `Report` named tuple with:

        - **`per_query`**: a list of `QueryResult(query, recall, rr)` named tuples, sorted by recall ascending (worst first),
          ties by query name. `recall` is the share of relevant documents found in the top `k` of the **deduplicated** ranking
          (keep each id's first position); `rr` is `1 / position` of the first relevant document anywhere in the deduplicated
          ranking (positions start at 1), or `0.0`. Round both to 4 decimals.
        - **`by_topic`**: a dict from topic to the mean recall of its queries, rounded to 4 decimals, topics sorted.
        - **`mrr`**: the mean of `rr` over scored queries, rounded to 4 decimals (0.0 if none).
        - **`skipped`**: a sorted list of queries that have no relevant documents (they cannot be scored and appear nowhere
          else).
        - **`missed`**: a dict from document id to how many scored queries it was relevant for but **not** retrieved in the top
          `k`, only ids missed at least once, most missed first, ties by id. These are the documents to look at first.""",
        code="""
        from collections import Counter
        from typing import NamedTuple


        class QueryResult(NamedTuple):
            query: str
            recall: float
            rr: float


        class Report(NamedTuple):
            per_query: list
            by_topic: dict
            mrr: float
            skipped: list
            missed: dict


        def evaluate(runs, k):
            pass
        """,
        tests="""
        runs = [
            {"query": "refund time", "topic": "billing", "ranked": ["d3", "d3", "d1", "d7"], "relevant": ["d1", "d2"]},
            {"query": "reset password", "topic": "auth", "ranked": ["d5", "d9"], "relevant": ["d5"]},
            {"query": "invoice copy", "topic": "billing", "ranked": ["d4", "d8", "d2"], "relevant": ["d2", "d6"]},
            {"query": "office hours", "topic": "misc", "ranked": ["d1"], "relevant": []},
        ]
        r = evaluate(runs, k=2)
        assert r.per_query == [QueryResult("invoice copy", 0.0, 0.3333), QueryResult("refund time", 0.5, 0.5),
                               QueryResult("reset password", 1.0, 1.0)]
        assert r.by_topic == {"auth": 1.0, "billing": 0.25}
        assert r.mrr == 0.6111
        assert r.skipped == ["office hours"]
        assert r.missed == {"d2": 2, "d6": 1}
        assert list(r.missed) == ["d2", "d6"]
        assert evaluate([], 5) == Report([], {}, 0.0, [], {})
        """,
        hints=["Deduplicate the ranking with `list(dict.fromkeys(run[\"ranked\"]))` (4.2, 4.5), then `top = set(ranked[:k])` and `relevant = set(...)` (4.4).",
               "Recall is `len(top & relevant) / len(relevant)`. For the reciprocal rank, `next((i for i, d in enumerate(ranked, 1) if d in relevant), None)`.",
               "Group recalls per topic in a `defaultdict(list)` and average at the end (4.6). Count misses with a `Counter` over `relevant - top`.",
               "Sort `per_query` with the key `(recall, query)`, and order `missed` with the key `(-count, doc_id)`."],
        solution="""
        from collections import Counter, defaultdict
        from typing import NamedTuple


        class QueryResult(NamedTuple):
            query: str
            recall: float
            rr: float


        class Report(NamedTuple):
            per_query: list
            by_topic: dict
            mrr: float
            skipped: list
            missed: dict


        def evaluate(runs, k):
            results = []
            by_topic = defaultdict(list)
            missed = Counter()
            skipped = []
            for run in runs:
                relevant = set(run["relevant"])
                if not relevant:
                    skipped.append(run["query"])
                    continue
                ranked = list(dict.fromkeys(run["ranked"]))
                top = set(ranked[:k])
                recall = len(top & relevant) / len(relevant)
                first = next((i for i, d in enumerate(ranked, start=1) if d in relevant), None)
                rr = 1 / first if first else 0.0
                results.append(QueryResult(run["query"], round(recall, 4), round(rr, 4)))
                by_topic[run["topic"]].append(recall)
                missed.update(relevant - top)
            results.sort(key=lambda r: (r.recall, r.query))
            topic_means = {t: round(sum(v) / len(v), 4) for t, v in sorted(by_topic.items())}
            mrr = round(sum(r.rr for r in results) / len(results), 4) if results else 0.0
            missed_sorted = dict(sorted(missed.items(), key=lambda kv: (-kv[1], kv[0])))
            return Report(results, topic_means, mrr, sorted(skipped), missed_sorted)
        """,
        why="""Every part of the module appears:

        - **Lists and slicing (4.1):** the deduplicated ranking keeps positions, and `ranked[:k]` is the top `k`, safe for any
          `k`.
        - **Sorting (4.2):** worst queries first with a tuple key, and a deterministic order for `missed`. Sorting the topics
          makes the report print the same way every run.
        - **Tuples (4.3):** `QueryResult` and `Report` are named tuples, so callers read `r.mrr` instead of remembering
          positions, and the empty case compares equal to a plain tuple.
        - **Sets (4.4):** relevance is a set question, `top & relevant` and `relevant - top`.
        - **Dicts (4.5):** `dict.fromkeys` deduplicates while keeping first positions, which matters: the duplicate `d3`
          would otherwise push `d1` out of the top 2.
        - **Counting and grouping (4.6):** `defaultdict(list)` groups recalls per topic and a `Counter` counts misses.

        Recall uses unrounded values for the topic means, so rounding happens once at the end. Recall@k and MRR are the two
        standard retrieval metrics; tools such as RAGAS and BEIR add others, but they are computed with exactly these
        structures."""),
)

recap(
    "Pick the structure from the operations: positions (list), both ends (deque), membership (set), lookup by key (dict), counting and grouping (Counter, defaultdict), sorted ranges (bisect), top-k (heapq).",
    "Make outputs deterministic: sort sets and dict items before printing, numbering or saving, and decide tie rules explicitly.",
    "Normalise before comparing: case, spaces and types (`\"3\"` versus `3`) decide what counts as equal.",
    "Dict indexes turn O(n × m) joins and checks into O(n + m). Build them once, outside loops.",
)
