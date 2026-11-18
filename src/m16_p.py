from lesson import *
from diagrams import *

lesson(
    id="m16-p", num="16.P", title="Module 16 practice set and mini project",
    intro="Mixed problems from all of Module 16: complexity, hashing, two pointers and binary search, graphs and dynamic programming, "
          "the toolkit interviews test and production code relies on. Then a mini project that needs all of it: a small search engine "
          "with an inverted index, TF-IDF ranking with a heap, the shortest snippet covering the query, near-duplicate merging with "
          "union-find, and a knapsack that fits results into a token budget.",
    desc="Mixed problems from the whole module, then one small program that uses all of it.",
    keys="practice mixed review project search engine inverted index tf-idf heap top-k snippet sliding window union-find knapsack merge intervals critical path dag grid bfs integer square root",
)

section("how", "How to use this page",
    fig(stage_map(16, "a small search engine"), "Module 16 at a glance: measuring cost, then the core patterns (hashing, windows, pointers, binary search, graphs, DP), building up to a search engine."),
    p("""For every problem, first say the brute force and its cost (16.1), then ask which structure removes the repeated work: a dict or set for lookups and counts (16.2), sorting
    plus two pointers or binary search for ordered data and monotone questions (16.3), a graph search for connections and dependencies (16.4), or a table of subproblems when
    the same smaller question recurs (16.5). State the final time and memory complexity, and test the edge cases: empty input, one element, duplicates, and the extremes."""),
    p("""The problems mix the lessons on purpose, and the mini project combines all five in a retrieval component of the kind every RAG system contains."""),
)

section("set", "Practice set",
    predict("Name the complexity", "easy",
        code="""
        def count_ops(fn, n):
            ops = [0]
            fn(n, ops)
            return ops[0]

        def a(n, ops):
            for i in range(n):
                j = 1
                while j < n:
                    j *= 2
                    ops[0] += 1

        def b(n, ops):
            seen = set()
            for i in range(n):
                ops[0] += 1
                seen.add(i % 10)

        def c(n, ops):
            for i in range(n):
                for j in range(i, n):
                    ops[0] += 1

        def d(n, ops):
            while n > 0:
                n //= 3
                ops[0] += 1

        for fn in (a, b, c, d):
            print(fn.__name__, [count_ops(fn, n) for n in (9, 27, 81)])
        """,
        hints=["Compare how each count changes when n triples."],
        why="""`a` runs a doubling loop (O(log n)) inside a loop over n, so it is O(n log n): the counts grow a bit faster than n. `b` is a single pass, O(n), and its set never grows beyond
        ten items, so its memory is O(1). `c` counts the pairs `j >= i`, `n(n + 1) / 2`, so tripling n multiplies it by about nine: O(n^2). `d` divides by three each time, so
        tripling n adds one step: O(log n)."""),
    write("The first unique event", "easy", tag="Data work",
        prompt="""Write `first_unique(events)` returning the first event that occurs exactly once in the list, or `None`, in O(n) with a `Counter`. Then write `first_unique_stream()`, a class
        with `add(event)` and `first()` answering the same question for a stream after each addition, with `first()` amortised O(1) (keep a deque of candidates and drop those
        that became duplicates).""",
        code="""
        from collections import Counter, deque

        def first_unique(events):
            pass

        class first_unique_stream:
            pass
        """,
        tests="""
        assert first_unique(["login", "ask", "login", "logout", "ask"]) == "logout" and first_unique(["a", "a"]) is None and first_unique([]) is None
        s = first_unique_stream()
        out = []
        for e in ["a", "b", "a", "c", "b", "c", "d"]:
            s.add(e)
            out.append(s.first())
        assert out == ["a", "a", "b", "b", "c", None, "d"]
        """,
        hints=["Count, then scan the list in order for the first count of 1.",
               "Stream: keep counts and a deque of events in arrival order; `first()` pops from the left while the front has a count above 1."],
        solution="""
        from collections import Counter, deque


        def first_unique(events):
            counts = Counter(events)
            for e in events:
                if counts[e] == 1:
                    return e
            return None


        class first_unique_stream:
            def __init__(self):
                self.counts = Counter()
                self.queue = deque()

            def add(self, event):
                self.counts[event] += 1
                if self.counts[event] == 1:
                    self.queue.append(event)

            def first(self):
                while self.queue and self.counts[self.queue[0]] > 1:
                    self.queue.popleft()
                return self.queue[0] if self.queue else None
        """,
        why="""Two passes with a `Counter` answer the batch question in O(n): count everything, then return the first event whose count is 1. For a stream, recounting after every event would be
        O(n) each time; instead each event enters the deque once when first seen and leaves it at most once, when it turns out to be a duplicate, so the total work over the stream
        is O(n) and each `first()` is amortised O(1), the same accounting that makes list appends cheap (16.1). Detecting the first unrepeated event is useful in logs (the first
        unusual error in a burst) and in deduplicating message streams."""),
    fix("An integer square root with bad bounds", "easy", tag="ML",
        prompt="""`isqrt(n)` should return the largest integer `r` with `r * r <= n` by binary search on the answer. It sets `hi = n // 2`, which is too small for `n` of 0 to 3 (the root of 1 is
        1, not 0), and updates `lo = mid` in a loop `while lo < hi`, which can loop forever. Fix the bounds and the update; compare with `math.isqrt`.""",
        code="""
        def isqrt(n):
            lo, hi = 0, n // 2
            steps = 0
            while lo < hi and steps < 100:
                steps += 1
                mid = (lo + hi) // 2
                if mid * mid <= n:
                    lo = mid
                else:
                    hi = mid - 1
            return lo
        """,
        tests="""
        import math
        assert [isqrt(n) for n in range(10)] == [math.isqrt(n) for n in range(10)]
        assert all(isqrt(n) == math.isqrt(n) for n in (15, 16, 17, 10**12, 10**12 + 1, 2**61 - 1))
        """,
        hints=["Search for the last `r` with `r * r <= n` in `[0, n]`: use `mid = (lo + hi + 1) // 2` (round up) so `lo = mid` always makes progress.",
               "Or search for the first `r` with `r * r > n` using the half-open pattern and subtract one."],
        solution="""
        def isqrt(n):
            lo, hi = 0, n
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if mid * mid <= n:
                    lo = mid
                else:
                    hi = mid - 1
            return lo
        """,
        why="""Searching for the **last** value with a property needs the middle rounded **up**: with `lo = 4, hi = 5`, rounding down gives `mid = 4`, and `lo = mid` leaves the interval unchanged
        forever (the starter needed a step counter to stop). Rounding up makes `mid` strictly greater than `lo`, so both branches shrink the interval. The upper bound must
        contain the answer for every input: `n // 2` excludes the roots of 1, 2 and 3; `n` itself is always safe. About 64 iterations handle any 64-bit number, which is why binary
        search on the answer works even when the answer is huge; in real code, use `math.isqrt`."""),
    predict("Shortest path on a grid", "medium",
        code="""
        from collections import deque

        def shortest(grid, start, goal):
            rows, cols = len(grid), len(grid[0])
            dist = {start: 0}
            q = deque([start])
            while q:
                r, c = q.popleft()
                if (r, c) == goal:
                    return dist[(r, c)]
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != "#" and (nr, nc) not in dist:
                        dist[(nr, nc)] = dist[(r, c)] + 1
                        q.append((nr, nc))
            return None

        floor = ["....#",
                 ".##.#",
                 "...#.",
                 "#...."]
        print(shortest(floor, (0, 0), (3, 4)), shortest(floor, (0, 0), (0, 3)), shortest(floor, (0, 0), (2, 4)))
        print(shortest([".#.", "#.#", ".#."], (0, 0), (2, 2)), shortest(["."], (0, 0), (0, 0)))
        """,
        hints=["Each cell is a node with up to four neighbours; walls (`#`) are not nodes. BFS gives the fewest moves."],
        why="""A grid is an implicit graph: cells are nodes and moves to open neighbours are edges, so BFS finds the fewest moves without building an adjacency list. Reaching the bottom
        right corner takes 7 moves around the walls; the last open cell of the first row is 3 moves away; the cell at the right end of row 2 is walled off from the left by
        the `#` beside it, so the path must reach the bottom-right corner first and step up, 8 moves. A cell surrounded by walls is unreachable (`None`), and the start is at
        distance 0 from itself."""),
    write("Merge overlapping intervals", "medium", tag="RAG",
        prompt="""Write `merge_intervals(intervals)` that merges overlapping or touching `[start, end)` intervals (sort by start, then sweep), returning a sorted list of tuples, and
        `covered_length(intervals)` returning the total length covered. Retrieved passages that overlap within a document should be merged before building a prompt, so text is
        not repeated.""",
        code="""
        def merge_intervals(intervals):
            pass

        def covered_length(intervals):
            pass
        """,
        tests="""
        spans = [(120, 300), (0, 50), (280, 400), (50, 60), (500, 520), (390, 410)]
        assert merge_intervals(spans) == [(0, 60), (120, 410), (500, 520)]
        assert covered_length(spans) == 370 and merge_intervals([]) == [] and covered_length([]) == 0
        assert merge_intervals([(5, 10), (1, 3)]) == [(1, 3), (5, 10)] and merge_intervals([(1, 10), (2, 3)]) == [(1, 10)]
        """,
        hints=["Sort by start; keep the current merged interval and extend its end with `max` while the next start is `<=` the current end."],
        solution="""
        def merge_intervals(intervals):
            merged = []
            for start, end in sorted(intervals):
                if merged and start <= merged[-1][1]:
                    merged[-1] = (merged[-1][0], max(merged[-1][1], end))
                else:
                    merged.append((start, end))
            return merged


        def covered_length(intervals):
            return sum(end - start for start, end in merge_intervals(intervals))
        """,
        why="""After sorting by start, any interval that overlaps the current merged block must start before that block ends, so one left-to-right sweep (two pointers in spirit: the current
        block and the next interval) merges everything in O(n log n) total, dominated by the sort. Taking the `max` of the ends handles intervals nested inside others, and `<=`
        merges intervals that merely touch, which for half-open character ranges means contiguous text. In a RAG pipeline, merging overlapping passages from the same document
        avoids sending the same sentences to the model twice, saving tokens and reducing repetition in answers."""),
    write("The k nearest embeddings", "medium", tag="RAG",
        prompt="""Write `k_nearest(query, vectors, k)` returning the ids of the `k` vectors (a dict from id to list of floats) with the highest cosine similarity to `query`, best first, ties by
        id, using `heapq.nlargest` (O(n log k)); vectors with zero norm are skipped. Also return the similarities rounded to 3, as a list of `(id, similarity)` pairs.""",
        code="""
        import heapq, math

        def k_nearest(query, vectors, k):
            pass
        """,
        tests="""
        vectors = {"faq": [1.0, 0.0], "terms": [0.7, 0.7], "blog": [0.0, 1.0], "zero": [0.0, 0.0], "dup": [2.0, 0.0], "anti": [-1.0, 0.0]}
        assert k_nearest([1.0, 0.1], vectors, 3) == [("dup", 0.995), ("faq", 0.995), ("terms", 0.774)]
        assert k_nearest([0.0, 1.0], vectors, 1) == [("blog", 1.0)] and k_nearest([1.0, 0.0], {}, 2) == []
        assert [i for i, _ in k_nearest([-1.0, 0.0], vectors, 6)] == ["anti", "blog", "terms", "dup", "faq"]
        """,
        hints=["Cosine similarity: `dot / (norm_q * norm_v)`. Use the key `(similarity, negated order)`; since ids are strings, sort ties afterwards, or rank by `(-sim, id)` with `heapq.nsmallest`."],
        solution="""
        import heapq, math


        def k_nearest(query, vectors, k):
            qn = math.sqrt(sum(x * x for x in query))
            scored = []
            for vid, v in vectors.items():
                vn = math.sqrt(sum(x * x for x in v))
                if vn == 0 or qn == 0:
                    continue
                sim = sum(a * b for a, b in zip(query, v)) / (qn * vn)
                scored.append((round(sim, 3), vid))
            best = heapq.nsmallest(k, scored, key=lambda t: (-t[0], t[1]))
            return [(vid, sim) for sim, vid in best]
        """,
        why="""Exact nearest-neighbour search scores every vector, O(n d), and keeps the best `k` with a heap in O(n log k) instead of sorting all n scores (16.1). Cosine similarity ignores
        vector length, so `dup` (twice as long as `faq`) ties with it, and ranking by `(-similarity, id)` makes ties deterministic, which matters for reproducible retrieval tests.
        Zero vectors have no direction and are skipped instead of dividing by zero. This is precisely what a vector database does at small scale, and what approximate indexes
        (HNSW, IVF) speed up when n reaches millions."""),
    fix("Counting paths on a grid with obstacles", "medium", tag="Data work",
        prompt="""`count_paths(grid)` counts the ways to go from the top-left to the bottom-right of a grid moving only right or down, avoiding `#` cells. It initialises the whole first row and
        column to 1, ignoring obstacles there (cells after an obstacle in the first row or column are unreachable), and does not handle a blocked start. Fix the initialisation.""",
        code="""
        def count_paths(grid):
            rows, cols = len(grid), len(grid[0])
            dp = [[0] * cols for _ in range(rows)]
            for r in range(rows):
                dp[r][0] = 1
            for c in range(cols):
                dp[0][c] = 1
            for r in range(1, rows):
                for c in range(1, cols):
                    if grid[r][c] == "#":
                        dp[r][c] = 0
                    else:
                        dp[r][c] = dp[r - 1][c] + dp[r][c - 1]
            return dp[-1][-1]
        """,
        tests="""
        assert count_paths(["...", "...", "..."]) == 6
        assert count_paths(["...", ".#.", "..."]) == 2
        assert count_paths([".#.", "...", "..."]) == 3
        assert count_paths(["#..", "...", "..."]) == 0 and count_paths(["..", "#."]) == 1 and count_paths(["."]) == 1
        """,
        hints=["Treat every cell the same way: `dp[r][c] = 0` for an obstacle, otherwise the sum of the cell above and the cell to the left (each if it exists), with `dp[0][0] = 1` when open."],
        solution="""
        def count_paths(grid):
            rows, cols = len(grid), len(grid[0])
            dp = [[0] * cols for _ in range(rows)]
            for r in range(rows):
                for c in range(cols):
                    if grid[r][c] == "#":
                        dp[r][c] = 0
                    elif r == 0 and c == 0:
                        dp[r][c] = 1
                    else:
                        dp[r][c] = (dp[r - 1][c] if r else 0) + (dp[r][c - 1] if c else 0)
            return dp[-1][-1]
        """,
        why="""The special-cased edges were the bug: setting the first row to 1 assumes every cell in it is reachable, but an obstacle in the first row blocks every cell to its right, and the
        same for the first column. Applying the one recurrence (paths into a cell come from above or from the left) to **every** cell, with "outside the grid" contributing 0 and
        the start contributing 1, removes the special cases and makes blocked starts and edges correct automatically. This is a general DP lesson: base cases should be as few
        and as small as possible, and edges are usually better handled by the recurrence with zeros outside."""),
    write("The critical path of a pipeline", "hard", tag="ML",
        prompt="""A training pipeline is a DAG of steps with durations: `steps` maps a step to `(duration, [dependencies])`. With unlimited parallel workers, the pipeline takes as long as its
        **critical path**, the longest chain of dependent durations. Write `critical_path(steps)` returning `(total_time, path)`, the path listing steps from first to last. Compute
        a topological order (Kahn's algorithm), then DP: `finish[s] = duration[s] + max(finish[d] for d in deps)`, with ties broken by the alphabetically smaller dependency.
        Raise `ValueError` on a cycle.""",
        code="""
        def critical_path(steps):
            pass
        """,
        tests="""
        steps = {
            "download": (20, []),
            "clean": (30, ["download"]),
            "features": (45, ["clean"]),
            "labels": (10, ["download"]),
            "train": (120, ["features", "labels"]),
            "eval": (15, ["train"]),
            "report": (5, ["eval", "labels"]),
        }
        assert critical_path(steps) == (235, ["download", "clean", "features", "train", "eval", "report"])
        assert critical_path({"a": (3, []), "b": (3, [])}) == (3, ["a"]) and critical_path({}) == (0, [])
        try:
            critical_path({"x": (1, ["y"]), "y": (1, ["x"])})
            assert False
        except ValueError:
            pass
        """,
        hints=["Kahn's algorithm with in-degrees over the dependency edges; process ready steps in sorted order.",
               "Keep `best_dep[s]` (the dependency giving the maximum finish). The answer ends at the step with the largest finish time (ties by name); walk `best_dep` back."],
        solution="""
        from collections import deque


        def critical_path(steps):
            if not steps:
                return 0, []
            indeg = {s: len(deps) for s, (_, deps) in steps.items()}
            dependants = {s: [] for s in steps}
            for s, (_, deps) in steps.items():
                for d in deps:
                    dependants[d].append(s)
            queue = deque(sorted(s for s, n in indeg.items() if n == 0))
            order = []
            while queue:
                s = queue.popleft()
                order.append(s)
                for t in sorted(dependants[s]):
                    indeg[t] -= 1
                    if indeg[t] == 0:
                        queue.append(t)
            if len(order) != len(steps):
                raise ValueError("pipeline has a cycle")
            finish, best_dep = {}, {}
            for s in order:
                duration, deps = steps[s]
                prev = max(sorted(deps), key=lambda d: finish[d], default=None)
                best_dep[s] = prev
                finish[s] = duration + (finish[prev] if prev else 0)
            end = max(sorted(finish), key=lambda s: finish[s])
            path = []
            while end is not None:
                path.append(end)
                end = best_dep[end]
            return finish[path[0]], path[::-1]
        """,
        why="""Two lessons combine: a topological order (16.4) guarantees every step is processed after its dependencies, and then a DP (16.5) computes each step's earliest finish time from its
        dependencies' finish times, one pass, O(V + E). The longest such chain is the critical path: here download, clean, features, train, eval and report take 235 minutes, and
        `labels` has slack (it could take 75 minutes longer without delaying anything). Speeding up anything off the critical path is wasted effort, which is why build systems,
        project planners and ML pipeline schedulers compute it. In a general graph, longest paths are hard; in a DAG they are this easy."""),
    explain("Walk me through how you approach an algorithm question you have not seen before.", "medium", tag="Interview",
        why="""Clarify first: restate the problem, ask about input sizes, value ranges, duplicates, empty inputs and what to return on ties or failure, and work through a small example by hand.
        Then state a brute-force solution and its complexity out loud, which shows correctness first and gives a baseline. Look for the repeated work in the brute force and match
        it to a pattern: a lookup inside a loop suggests a hash map; sorted data or a monotone condition suggests two pointers or binary search (including on the answer); contiguous
        ranges suggest a sliding window or prefix sums; connections or dependencies suggest BFS, DFS or a topological sort; recurring subproblems suggest dynamic programming; "top k"
        suggests a heap. Write clean code with meaningful names, then test it on the edge cases you listed and trace one example. Finish by stating the time and space complexity,
        and mention trade-offs or follow-ups (streaming input, memory limits, parallelism) if there is time."""),
    explain("You need the top 10 results from 100 million scored items. What are your options and their costs?", "hard", tag="Interview",
        why="""Sorting everything costs O(n log n) time and O(n) memory, wasteful when only 10 are needed. A **heap** of size k, pushing each item and popping the smallest when the heap exceeds k
        (or `heapq.nlargest(10, stream)`), costs O(n log k) time and O(k) memory and works on a **stream**, so the items never need to fit in memory at once. **Quickselect**
        (`numpy.argpartition`) finds the top k in O(n) average time but needs the data in memory. With **partitioned** data, each worker computes its local top 10 and a final step
        merges the k times workers candidates, which is how distributed engines and search systems do it (each shard returns its top hits). If the scores come from comparing a
        query with stored vectors, an **approximate nearest-neighbour index** avoids scoring all 100 million items in the first place, trading a little recall for sub-linear time.
        Deterministic tie-breaking (by id) keeps results stable across runs."""),
)

section("project", "Mini project: a small search engine",
    fig(chain(["add(): inverted|index (dict)", "search(): TF-IDF,|heapq.nlargest", "snippet():|minimum window", "dedupe():|union-find", ("pack(): knapsack|into a budget", "good")]),
        "MiniSearch: each method is one technique from this module, at the complexity it promises."),
    p("""Retrieval is the first half of every RAG system. Build `MiniSearch`, an in-memory engine that indexes documents, ranks them for a query, shows the most relevant snippet, merges
    near-duplicate documents in its results, and packs the best results into a token budget for the prompt. Each part is one technique from this module, and its complexity
    should be the one the technique promises."""),
    write("Build MiniSearch", "hard", key="mini-search", tag="Project",
        prompt="""Implement the class `MiniSearch` (tokens are lower-cased words with `.,!?` stripped):

        - **`add(doc_id, text)`**: store the tokens and update an **inverted index** from term to `{doc_id: term count}` (16.2). Adding an existing id raises `ValueError`.
        - **`search(query, k=3)`**: score each document containing at least one query term by TF-IDF, `sum(count * idf(term))` with `idf = log((N + 1) / (df + 1)) + 1`, touching only
          the postings of the query terms; return the top `k` as `(doc_id, score rounded to 3)` with `heapq.nlargest` and ties by id (16.1).
        - **`snippet(doc_id, query)`**: the shortest window of the document's tokens containing every query term that occurs in it, joined by spaces, leftmost on ties (16.2's
          minimum window); an empty string if none occur.
        - **`dedupe(results, threshold=0.6)`**: given search results, merge documents whose token sets have Jaccard similarity at or above the threshold using **union-find** (16.4),
          keeping only the best-ranked document of each group, in rank order.
        - **`pack(results, budget)`**: choose results maximising total score with total tokens (document lengths) at most `budget`, by 0/1 knapsack (16.5); return the chosen ids in rank order.""",
        code="""
        import heapq, math
        from collections import Counter, defaultdict


        class MiniSearch:
            pass
        """,
        tests="""
        engine = MiniSearch()
        docs = {
            "refunds": "Refunds take five business days. Refunds go to the original card.",
            "refunds-copy": "Refunds take five business days. Refunds go to the original card!",
            "returns": "Returns are free within thirty days. Start a return from your orders page.",
            "shipping": "Shipping is free on orders over fifty euros.",
            "card": "We accept every major card. The card is charged when the order ships.",
        }
        for doc_id, text in docs.items():
            engine.add(doc_id, text)
        try:
            engine.add("refunds", "again")
            assert False
        except ValueError:
            pass
        results = engine.search("refunds card days", k=4)
        assert [r[0] for r in results] == ["refunds", "refunds-copy", "card", "returns"]
        assert results[0][1] == results[1][1] and results[1][1] > results[2][1]
        assert engine.search("warranty") == [] and len(engine.search("refunds card", k=10)) == 3
        assert engine.snippet("refunds", "card refunds") == "refunds go to the original card"
        assert engine.snippet("card", "card") == "card" and engine.snippet("shipping", "refunds") == ""
        assert engine.dedupe(results) == ["refunds", "card", "returns"]
        deduped = [r for r in results if r[0] in engine.dedupe(results)]
        assert engine.pack(results, 25) == ["refunds", "refunds-copy"] and engine.pack(deduped, 25) == ["refunds", "card"]
        assert engine.pack(deduped, 12) == ["refunds"] and engine.pack(deduped, 5) == []
        """,
        hints=["Keep `self.tokens = {}` and `self.index = defaultdict(dict)`; `N = len(self.tokens)`, `df = len(self.index[term])`.",
               "Score with a `defaultdict(float)` accumulated over the query terms' postings; rank with `heapq.nsmallest(k, scores.items(), key=lambda kv: (-kv[1], kv[0]))`.",
               "Union-find over the result ids with pairwise Jaccard (results are few); knapsack over `(len(tokens), score)` with an O(n * budget) table and backtracking."],
        solution="""
        import heapq, math
        from collections import Counter, defaultdict


        def _tokens(text):
            return [w.strip(".,!?").lower() for w in text.split() if w.strip(".,!?")]


        class MiniSearch:
            def __init__(self):
                self.tokens = {}
                self.index = defaultdict(dict)

            def add(self, doc_id, text):
                if doc_id in self.tokens:
                    raise ValueError(f"duplicate document id {doc_id!r}")
                toks = _tokens(text)
                self.tokens[doc_id] = toks
                for term, count in Counter(toks).items():
                    self.index[term][doc_id] = count

            def _idf(self, term):
                n, df = len(self.tokens), len(self.index.get(term, {}))
                return math.log((n + 1) / (df + 1)) + 1

            def search(self, query, k=3):
                scores = defaultdict(float)
                for term in set(_tokens(query)):
                    idf = self._idf(term)
                    for doc_id, count in self.index.get(term, {}).items():
                        scores[doc_id] += count * idf
                best = heapq.nsmallest(k, scores.items(), key=lambda kv: (-kv[1], kv[0]))
                return [(doc_id, round(score, 3)) for doc_id, score in best]

            def snippet(self, doc_id, query):
                toks = self.tokens[doc_id]
                need = Counter(t for t in set(_tokens(query)) if t in set(toks))
                if not need:
                    return ""
                missing, left, best = len(need), 0, None
                for right, tok in enumerate(toks):
                    if need[tok] > 0:
                        missing -= 1
                    need[tok] -= 1
                    while missing == 0:
                        if best is None or right + 1 - left < best[1] - best[0]:
                            best = (left, right + 1)
                        need[toks[left]] += 1
                        if need[toks[left]] > 0:
                            missing += 1
                        left += 1
                return " ".join(toks[best[0]:best[1]])

            def dedupe(self, results, threshold=0.6):
                ids = [doc_id for doc_id, _ in results]
                parent = {i: i for i in ids}

                def find(x):
                    while parent[x] != x:
                        parent[x] = parent[parent[x]]
                        x = parent[x]
                    return x

                sets = {i: set(self.tokens[i]) for i in ids}
                for a in range(len(ids)):
                    for b in range(a + 1, len(ids)):
                        x, y = ids[a], ids[b]
                        union = sets[x] | sets[y]
                        if union and len(sets[x] & sets[y]) / len(union) >= threshold:
                            rx, ry = find(x), find(y)
                            if rx != ry:
                                parent[max(rx, ry, key=ids.index)] = min(rx, ry, key=ids.index)
                kept, seen = [], set()
                for i in ids:
                    root = find(i)
                    if root not in seen:
                        seen.add(root)
                        kept.append(i)
                return kept

            def pack(self, results, budget):
                items = [(len(self.tokens[d]), s, d) for d, s in results]
                n = len(items)
                best = [[0.0] * (budget + 1) for _ in range(n + 1)]
                for i in range(1, n + 1):
                    w, v, _ = items[i - 1]
                    for cap in range(budget + 1):
                        best[i][cap] = best[i - 1][cap]
                        if w <= cap and best[i - 1][cap - w] + v > best[i][cap]:
                            best[i][cap] = best[i - 1][cap - w] + v
                chosen, cap = [], budget
                for i in range(n, 0, -1):
                    if best[i][cap] != best[i - 1][cap]:
                        chosen.append(items[i - 1][2])
                        cap -= items[i - 1][0]
                return [d for d, _ in results if d in chosen]
        """,
        why="""Every lesson of the module has a job here:

        - **Hashing (16.2):** the inverted index maps each term to the documents containing it, so a query touches only the postings of its terms rather than every document, and the
          snippet is the minimum-window sliding window over the document's tokens.
        - **Complexity (16.1):** scoring is proportional to the postings read, and the top `k` come from a heap with an explicit tie-break, O(m log k) for m scored documents.
        - **Graphs (16.4):** union-find groups near-identical documents (`refunds` and `refunds-copy` differ by one character of punctuation) so the user does not see the same text twice,
          and each group is represented by its best-ranked member.
        - **Dynamic programming (16.5):** knapsack packing chooses the subset of results with the most total relevance that fits the token budget, which can beat taking results in rank
          order until the budget runs out. The tests show why deduplication comes first: packing the raw results spends the whole budget on two copies of the
          refunds text, while packing the deduplicated results adds the card document instead.
        - **Search (16.3)** appears in the budget logic's spirit: when the check is monotone, a sorted structure answers it quickly, as prefix sums plus `bisect` would for packing in
          rank order.

        The same pieces, scaled up, are BM25 ranking in Elasticsearch, snippet highlighting, result diversification and context assembly in production RAG systems."""),
)

recap(
    "Start from the brute force and its cost, then remove the repeated work with the matching technique.",
    "Hashing for lookups, counts and windows; sorting with two pointers, sweeps and binary search for ordered and monotone questions.",
    "Graphs for connections and dependencies: BFS for fewest steps, topological order for DAGs, union-find for grouping.",
    "Dynamic programming when subproblems recur: grids, budgets, sequences and DAG longest paths.",
    "Always state time and memory complexity, make ties deterministic, and test empty, single, duplicate and extreme inputs.",
)
