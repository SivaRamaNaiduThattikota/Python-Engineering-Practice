from lesson import *
from diagrams import *

lesson(
    id="m16-1", num="16.1", title="Big-O in practice",
    intro="Interviews ask for the complexity of every solution, and production code dies from the accidental quadratic loop nobody "
          "noticed on ten test rows. What Big-O measures and what it ignores, the common growth classes, how to measure growth "
          "instead of guessing, the real cost of Python's built-ins (lists, dicts, sets, deques, heaps, sorting, strings), "
          "amortised costs, and the hidden costs that turn linear code quadratic.",
    desc="Measuring and predicting cost, and the cost of Python's built-ins.",
    keys="big-o complexity time complexity space complexity o(1) o(log n) o(n) o(n log n) o(n^2) amortised list append insert pop deque heapq bisect dict set hash sort timsort doubling experiment profiling hidden quadratic",
)

term("Big-O", "A description of how a cost (time or memory) grows with the input size n, keeping only the dominant term and ignoring constant factors.")
term("Amortised cost", "The average cost per operation over a long sequence, when most operations are cheap and a few are expensive (like a list occasionally resizing).")
term("Time complexity", "How the number of basic steps an algorithm performs grows with the input size.")

section("what", "What Big-O measures",
    fig(stage_map(16, "a small search engine"), "Module 16 at a glance: measuring cost, then the core patterns (hashing, windows, pointers, binary search, graphs, DP), building up to a search engine."),
    fig(table(["n", "O(log n)", "O(n)", "O(n log n)", "O(n^2)"], [
        ["1,000", "10", "1,000", "10,000", "1,000,000"],
        ["1,000,000", "20", "1,000,000", "20,000,000", "10^12"],
    ], hl={(1, 4)}, label="steps, roughly, as n grows"),
        "Big-O is about growth: at a million items a quadratic algorithm needs a million million steps, a log one only 20."),
    p("""Big-O answers one question: **when the input doubles, what happens to the cost?** An algorithm is **O(n)** if its work grows proportionally to n (double the
    input, double the time), **O(n^2)** if it grows with the square (double the input, four times the time), **O(log n)** if each doubling adds only a constant amount of
    work, and **O(1)** if the work does not depend on n at all. Constant factors and smaller terms are dropped, so `3n + 100` is O(n) and `n^2/2 + n` is O(n^2): at large
    sizes the dominant term decides everything. Usually we mean the **worst case** (or the average case, explicitly, for hash tables), and we can state the **space**
    complexity, the extra memory used, the same way."""),
    p("""The classes, from fast to slow, and what they look like in code: **O(1)** a dict lookup or `list.append`; **O(log n)** binary search, repeatedly halving (16.3);
    **O(n)** one pass over the data; **O(n log n)** sorting, or n heap operations; **O(n^2)** a loop over the data inside another loop over the data (all pairs);
    **O(2^n)** trying every subset (16.5 rescues many of these). At n = 1,000,000, an O(n log n) algorithm does about 20 million steps (fractions of a second in C, seconds
    in Python), while O(n^2) does a trillion (days). That gap, not the constant factors, is why complexity matters."""),
)

section("measure", "Measuring instead of guessing",
    p("""Complexity is a prediction; check it. The **doubling experiment** runs the code at sizes n, 2n, 4n and compares times: a ratio near 2 suggests O(n), near 4 O(n^2),
    slightly above 2 O(n log n), near 1 O(1) or O(log n). On a log-log plot of time against size, the slope is the exponent (problem 2). Use `timeit` (or `time.perf_counter`
    around enough repetitions) for small code, and **`cProfile`** to find where a real program spends its time (`python -m cProfile -s cumulative script.py`); most slow
    programs have one hot spot, and it is rarely where you guessed. Counting operations, for example comparisons, gives exact, noise-free numbers, which is what several
    problems here do."""),
)

section("builtins", "The cost of Python's built-ins",
    fig(table(["operation", "list", "deque", "dict / set"], [
        ["append at the end", "O(1) amortised", "O(1)", "O(1) insert"],
        ["insert or remove at the front", "O(n)", "O(1)", ""],
        ["x in items", "O(n)", "O(n)", "O(1) average"],
        ["index i", "O(1)", "O(n) in the middle", ""],
    ], hl={(1, 1), (2, 1)}, label="the cost of common operations"),
        "The two costly list operations are front edits and membership tests; `deque` and `set` fix them."),
    p("""**Lists** are dynamic arrays: indexing, `len`, `append` and `pop()` from the end are O(1) (append is **amortised** O(1): occasionally the list grows its storage by a
    proportion and copies everything, but that cost averages out over many appends); `insert(0, x)`, `pop(0)` and `del items[i]` shift every later element, O(n); `x in
    items`, `items.index(x)` and `items.count(x)` scan, O(n); slicing copies, O(k) for k elements; `sort` is O(n log n) (Timsort, which is O(n) on already-sorted runs).
    **dicts and sets** are hash tables: lookup, insert and delete are O(1) on average (O(n) in a pathological worst case with many hash collisions), so membership tests
    against a set are the standard fix for an O(n) `in` inside a loop."""),
    p("""**`collections.deque`** gives O(1) appends and pops at **both** ends (use it for queues, 16.4's BFS), but O(n) indexing in the middle. **`heapq`** keeps a list as a binary
    heap: `heappush` and `heappop` are O(log n), `heapq.nlargest(k, items)` is O(n log k). **`bisect`** finds positions in a sorted list in O(log n), but `insort` still
    pays O(n) to shift elements. **Strings** are immutable, so building one by `+=` in a loop can copy the whole string each time (CPython sometimes optimises this, but do
    not rely on it); collect parts in a list and `"".join(parts)` once, O(total length)."""),
    ex("""
    import timeit

    setup = "n = 20_000; items = list(range(n)); as_set = set(items); queries = list(range(0, 2 * n, 7))"
    t_list = min(timeit.repeat("sum(q in items for q in queries[:300])", setup, number=1, repeat=3))
    t_set = min(timeit.repeat("sum(q in as_set for q in queries[:300])", setup, number=1, repeat=3))
    print(f"list membership is about {t_list / t_set:.0f}x slower than set membership for 300 queries")

    def grow(n):
        items = []
        for i in range(n):
            items.insert(0, i)

    def grow_end(n):
        items = []
        for i in range(n):
            items.append(i)

    for n in (2_000, 4_000, 8_000):
        a = min(timeit.repeat(lambda: grow(n), number=1, repeat=3))
        b = min(timeit.repeat(lambda: grow_end(n), number=1, repeat=3))
        print(n, "insert(0) / append time ratio:", round(a / b))
    """, "builtin_costs.py"),
    p("""The ratios grow with n, which is the signature of an O(n) operation repeated n times (O(n^2) in total) against an O(1) one; the exact numbers vary by machine, but the
    trend does not. This is why "use the right container" is often the whole optimisation."""),
)

section("hidden", "Hidden quadratic costs",
    fig(chain(["for x in items:", "if x in seen_list:|(scans the list)", ("n x n = O(n^2)", "bad"), ("seen = set():|O(n) overall", "good")]),
        "Hidden quadratic cost: an O(n) step inside a loop. Changing one data structure fixes it."),
    p("""Most real performance bugs are an O(n) operation hiding inside a loop: `if x not in seen_list` (use a set), `queue.pop(0)` (use a deque), `sorted(...)` or `max(...)`
    recomputed every iteration (compute once, or maintain a heap), `result = result + [x]` or string `+=` (append, then join), `list.index` to find each item's position
    (build a dict from item to index once), slicing in recursion (pass indices instead), and calling `len()` on a generator by first converting it to a list each time.
    The code looks linear and passes every test on ten rows; on a million rows it never finishes. When reviewing code, look for these patterns first."""),
)

section("warmup", "Warm-up",
    predict("Counting steps", "easy",
        code="""
        def single(n):
            steps = 0
            for i in range(n):
                steps += 1
            return steps

        def nested(n):
            steps = 0
            for i in range(n):
                for j in range(i):
                    steps += 1
            return steps

        def halving(n):
            steps = 0
            while n > 1:
                n //= 2
                steps += 1
            return steps

        def log_linear(n):
            steps = 0
            for i in range(n):
                k = n
                while k > 1:
                    k //= 2
                    steps += 1
            return steps

        for n in (8, 16, 1024):
            print(n, single(n), nested(n), halving(n), log_linear(n))
        """,
        hints=["Doubling n: a linear count doubles, the triangle `n(n-1)/2` roughly quadruples, the halving count grows by one."],
        why="""The single loop is O(n). The nested loop over `j < i` runs `n(n - 1) / 2` times, which is O(n^2): constant factors do not change the class, and doubling n roughly
        quadruples it. Repeated halving is O(log n): each doubling of n adds one step, and 1024 needs only 10. Running a halving loop once per element is O(n log n), the
        cost of a good sort. These four shapes cover most code you will analyse."""),
    write("Estimate the exponent from measurements", "easy", tag="ML",
        prompt="""Write `growth_exponent(sizes, costs)` estimating `k` in `cost ~ c * n**k` as the least-squares slope of `log(cost)` against `log(n)`, rounded to 2 decimals, and
        `classify(sizes, costs)` returning `"O(1)"`, `"O(n)"`, `"O(n log n)"` or `"O(n^2)"` for slopes below 0.5, below 1.08, below 1.6, and otherwise, respectively. Raise
        `ValueError` for fewer than two points.""",
        code="""
        import math

        def growth_exponent(sizes, costs):
            pass

        def classify(sizes, costs):
            pass
        """,
        tests="""
        import math
        ns = [1_000, 2_000, 4_000, 8_000, 16_000]
        assert growth_exponent(ns, [3 * n for n in ns]) == 1.0 and classify(ns, [3 * n for n in ns]) == "O(n)"
        assert growth_exponent(ns, [n * n / 2 for n in ns]) == 2.0 and classify(ns, [n * n for n in ns]) == "O(n^2)"
        assert classify(ns, [n * math.log2(n) for n in ns]) == "O(n log n)" and classify(ns, [7.0] * 5) == "O(1)"
        assert classify(ns, [1.0, 2.1, 3.9, 8.2, 15.8]) == "O(n)"
        try:
            growth_exponent([10], [1.0])
            assert False
        except ValueError:
            pass
        """,
        hints=["With `x = log(n)` and `y = log(cost)`, the slope is `sum((x - mx) * (y - my)) / sum((x - mx) ** 2)`."],
        solution="""
        import math


        def growth_exponent(sizes, costs):
            if len(sizes) < 2 or len(sizes) != len(costs):
                raise ValueError("need at least two (size, cost) pairs")
            xs = [math.log(n) for n in sizes]
            ys = [math.log(c) for c in costs]
            mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
            slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
            return round(slope, 2)


        def classify(sizes, costs):
            k = growth_exponent(sizes, costs)
            if k < 0.5:
                return "O(1)"
            if k < 1.08:
                return "O(n)"
            if k < 1.6:
                return "O(n log n)"
            return "O(n^2)"
        """,
        why="""Taking logarithms turns `cost = c * n**k` into a straight line, `log(cost) = log(c) + k * log(n)`, so the exponent is the slope, and constants such as the 3 in `3n`
        vanish into the intercept, exactly as Big-O ignores them. A least-squares fit over several sizes tolerates measurement noise (the noisy timings still classify as
        linear). `n log n` has a slope slightly above 1 (about 1.12 for sizes between 1,000 and 16,000, since the slope of `log(n log n)` is `1 + 1 / ln n`), which is why the thresholds are heuristic and the linear one sits close to 1; in practice this is how you confirm, with a
        handful of timings, whether an optimisation changed the complexity or only the constant."""),
    fix("Removing duplicates while iterating", "easy", tag="Data work",
        prompt="""`dedupe(items)` should keep the first occurrence of each item, in order. It removes items from the list it is iterating over, which skips elements, and its `in`
        check on a list makes it quadratic. Fix it with a set of seen items (or `dict.fromkeys`), so it is correct and O(n).""",
        code="""
        def dedupe(items):
            result = list(items)
            for x in result:
                if result.count(x) > 1:
                    result.remove(x)
            return result
        """,
        tests="""
        assert dedupe(["a", "b", "a", "c", "b", "a"]) == ["a", "b", "c"]
        assert dedupe([3, 3, 3, 3]) == [3] and dedupe([]) == []
        big = list(range(50_000)) * 2
        assert dedupe(big) == list(range(50_000))
        """,
        hints=["`list(dict.fromkeys(items))` keeps first occurrences in order in one pass; or loop with a `seen` set."],
        solution="""
        def dedupe(items):
            seen = set()
            result = []
            for x in items:
                if x not in seen:
                    seen.add(x)
                    result.append(x)
            return result
        """,
        why="""Removing from a list while iterating over it shifts the remaining elements left, so the loop skips the element after each removal, and `remove` deletes the **first**
        occurrence, not the current one, which breaks the "keep the first" order. Performance was just as bad: `count` and `remove` each scan the list, so the whole function
        was O(n^2), minutes for the 100,000-item test. A set answers "seen before?" in O(1) on average, making one pass enough. `dict.fromkeys` does the same in one line
        because dicts keep insertion order and ignore repeated keys."""),
    choose("Membership tests: list or set", "easy", tag="Data work",
        prompt="Both count how many of 2,000 query ids appear among 10,000 known ids. Which is faster?",
        setup="""known = list(range(0, 20_000, 2))
known_set = set(known)
queries = list(range(0, 4_000, 2))""",
        options={
            "a": "hits = sum(1 for q in queries if q in known)",
            "b": "hits = sum(1 for q in queries if q in known_set)",
        },
        answer="b",
        hints=["How many elements does each `in` look at, for a list and for a set?"],
        why="""`q in known` scans the list until it finds `q` (or reaches the end), so 2,000 queries cost up to 2,000 x 10,000 comparisons: O(n * m). A set hashes `q` and checks one
        bucket, O(1) on average, so the whole count is O(m) after building the set once in O(n). Converting a lookup list to a set is the single most common Python
        performance fix, as long as the elements are hashable and you only need membership, not order or duplicates."""),
)

section("medium", "Medium",
    predict("How lists grow", "medium",
        code="""
        import sys

        items, sizes = [], []
        for i in range(40):
            items.append(i)
            sizes.append(sys.getsizeof(items))
        changes = [i + 1 for i in range(1, 40) if sizes[i] != sizes[i - 1]]
        print(changes)
        print(len(changes), "resizes for 40 appends")
        copies = sum(n - 1 for n in changes)
        print(copies, "element copies in total")
        """,
        hints=["A list over-allocates when it grows, so most appends fit in spare capacity; the lengths printed are those at which a new, larger block was needed."],
        why="""`sys.getsizeof` changes only when the list allocates a new block, and the printed lengths are those appends: only five resizes in forty appends. CPython grows the
        capacity by about an eighth of the current size plus a constant, so for large lists the gaps keep widening, the number of resizes grows only logarithmically, and
        the elements copied during resizes add up to a small multiple of n (84 copies for 40 appends here). Spread over all appends, each costs O(1) on average: **amortised** constant time. The exact sizes differ between platforms (this site runs a 32-bit
        build), but the pattern is the same."""),
    write("Capacity planning for vector search", "medium", tag="RAG",
        prompt="""Write `brute_force_cost(n_vectors, dim, queries_per_second, flops_per_second=2e10, bytes_per_value=4)` returning a dict with `memory_gb` (vector storage, rounded to
        2), `flops_per_query` (a dot product per stored vector costs `2 * dim` floating-point operations), `max_qps` (how many queries per second the given compute allows,
        rounded down to an int), and `fits` (whether `max_qps >= queries_per_second`). Exact brute-force search is O(n * d) per query.""",
        code="""
        def brute_force_cost(n_vectors, dim, queries_per_second, flops_per_second=2e10, bytes_per_value=4):
            pass
        """,
        tests="""
        small = brute_force_cost(100_000, 768, queries_per_second=50)
        assert small == {"memory_gb": 0.31, "flops_per_query": 153_600_000, "max_qps": 130, "fits": True}
        big = brute_force_cost(50_000_000, 1536, queries_per_second=20)
        assert big["memory_gb"] == 307.2 and big["max_qps"] == 0 and big["fits"] is False
        assert brute_force_cost(1_000, 384, 10, bytes_per_value=2)["memory_gb"] == 0.0
        """,
        hints=["Memory: `n * dim * bytes_per_value / 1e9`. FLOPs per query: `2 * dim * n`. Max QPS: `int(flops_per_second // flops_per_query)`."],
        solution="""
        def brute_force_cost(n_vectors, dim, queries_per_second, flops_per_second=2e10, bytes_per_value=4):
            memory_gb = round(n_vectors * dim * bytes_per_value / 1e9, 2)
            flops = 2 * dim * n_vectors
            max_qps = int(flops_per_second // flops)
            return {"memory_gb": memory_gb, "flops_per_query": flops, "max_qps": max_qps, "fits": max_qps >= queries_per_second}
        """,
        why="""Complexity analysis turns into a capacity plan: exact nearest-neighbour search compares the query with every stored vector, O(n * d) per query, so the cost grows
        linearly with the corpus. A hundred thousand 768-dimensional embeddings take 0.3 GB and comfortably serve 50 queries per second on one machine, which is why small RAG
        systems often need no vector database at all; fifty million 1536-dimensional embeddings need 300 GB and cannot sustain even one query per second by brute force.
        That is what approximate indexes (HNSW graphs, IVF partitions, product quantisation) are for: they trade a little recall for sub-linear query time, and lower
        precision (`bytes_per_value=2` or 1) trades accuracy for memory."""),
    choose("A queue: list.pop(0) or deque.popleft()", "medium", tag="Data work",
        prompt="Both drain a queue of 30,000 items from the front. Which is faster?",
        setup="""from collections import deque
items = list(range(30_000))""",
        options={
            "a": "q = list(items)\nwhile q:\n    q.pop(0)",
            "b": "q = deque(items)\nwhile q:\n    q.popleft()",
        },
        answer="b",
        hints=["What happens to the remaining elements of a list when the first one is removed?"],
        why="""Removing the first element of a list shifts every remaining element one position to the left, an O(n) operation, so draining n items costs O(n^2) in total. A deque is
        built from blocks linked at both ends, so `popleft` is O(1) and draining is O(n). Queues appear everywhere (BFS in 16.4, job queues, sliding windows in 16.2), and
        `list.pop(0)` in a loop is one of the classic hidden quadratics."""),
    trace("Comparisons, counted", "medium",
        prompt="Fill in `calls` after each marked line. `Key` counts every equality comparison and every hash.",
        code="""
        class Key:
            eq = 0
            hashes = 0
            def __init__(self, v):
                self.v = v
            def __eq__(self, other):
                Key.eq += 1
                return self.v == other.v
            def __hash__(self):
                Key.hashes += 1
                return hash(self.v)

        def reset():
            Key.eq = Key.hashes = 0

        items = [Key(i) for i in range(100)]
        lookup = set(items)
        target = Key(99)
        reset()
        found = target in items
        calls = (Key.eq, Key.hashes)  # row: "list membership, last item"
        reset()
        found = Key(-1) in items
        calls = (Key.eq, Key.hashes)  # row: "list membership, missing"
        reset()
        found = target in lookup
        calls = (Key.eq, Key.hashes)  # row: "set membership"
        reset()
        found = Key(-1) in lookup
        calls = (Key.eq, Key.hashes)  # row: "set miss"
        """,
        trace_vars=["calls"],
        hints=["A list compares the target with elements one by one; a set hashes the target once and compares only with candidates in the same bucket.",
               "`x in list` first checks identity, then equality; `target` is a different object from the 99 stored, so equality is needed."],
        why="""A list search compares the target with each element in turn: finding the last of 100 items takes 100 comparisons, and a missing item compares with all 100, no
        hashing involved. A set hashes the target once and then compares it only with the element stored under that hash, so a hit costs one hash and one comparison, and a
        miss usually only the hash. That is O(n) against O(1), visible in exact counts rather than noisy timings, and it is how you can verify the complexity of your own data
        structures."""),
    write("Running median with two heaps", "medium", tag="ML",
        prompt="""Write `running_medians(values)` returning the median after each value arrives (the middle value, or the mean of the two middle values for an even count), in O(log n)
        per value. Keep a max-heap of the lower half (store negatives with `heapq`) and a min-heap of the upper half, with sizes differing by at most one.""",
        code="""
        import heapq

        def running_medians(values):
            pass
        """,
        tests="""
        assert running_medians([5, 15, 1, 3]) == [5, 10.0, 5, 4.0]
        assert running_medians([2, 2, 2]) == [2, 2.0, 2] and running_medians([]) == []
        import random
        rng = random.Random(0)
        data = [rng.randint(0, 1000) for _ in range(2_000)]
        def slow(values):
            out = []
            for i in range(1, len(values) + 1):
                s = sorted(values[:i])
                m = len(s) // 2
                out.append(s[m] if len(s) % 2 else (s[m - 1] + s[m]) / 2)
            return out
        assert running_medians(data[:300]) == slow(data[:300])
        assert len(running_medians(data)) == 2_000
        """,
        hints=["Push each value onto the lower heap (as its negative), then move the lower heap's largest onto the upper heap; if the upper heap becomes bigger, move its smallest back.",
               "With the lower heap kept equal or one larger, the median is `-low[0]` for odd counts and `(-low[0] + high[0]) / 2` for even ones."],
        solution="""
        import heapq


        def running_medians(values):
            low, high, out = [], [], []
            for v in values:
                heapq.heappush(low, -v)
                heapq.heappush(high, -heapq.heappop(low))
                if len(high) > len(low):
                    heapq.heappush(low, -heapq.heappop(high))
                if len(low) > len(high):
                    out.append(-low[0])
                else:
                    out.append((-low[0] + high[0]) / 2)
            return out
        """,
        why="""Re-sorting the data after every value (the reference `slow` function) costs O(n log n) per step and O(n^2 log n) overall; the two heaps keep the data split into a lower
        and an upper half, so the median is always at the top of one or both, and each new value costs a few O(log n) heap operations. Passing every value through the lower
        heap into the upper one keeps the invariant "every element of `low` is at most every element of `high`" without comparisons by hand. Streaming medians are used for
        latency monitoring (p50 of response times) and robust feature normalisation; for other percentiles, sketches such as t-digest do the same job approximately."""),
    fix("A sort inside the loop", "medium", tag="GenAI",
        prompt="""`rank_with_context(scores, k)` should return, for each position `i`, the ids of the `k` best-scoring items seen **so far** (inclusive), best first. It calls `sorted` on the
        whole history every iteration, which is O(n^2 log n), and it also breaks ties by id **descending** instead of ascending. Fix both: keep the top `k` with a heap (or a
        bounded sorted list) as you go, ties broken by smaller id first.""",
        code="""
        def rank_with_context(scores, k):
            history, out = [], []
            for item_id, score in scores:
                history.append((score, item_id))
                best = sorted(history, reverse=True)[:k]
                out.append([i for _, i in best])
            return out
        """,
        tests="""
        scores = [("a", 0.2), ("b", 0.9), ("c", 0.5), ("d", 0.9), ("e", 0.1)]
        assert rank_with_context(scores, 2) == [["a"], ["b", "a"], ["b", "c"], ["b", "d"], ["b", "d"]]
        assert rank_with_context([], 3) == [] and rank_with_context(scores, 1)[-1] == ["b"]
        many = [(f"id{i:05d}", (i * 37) % 1000 / 1000) for i in range(20_000)]
        out = rank_with_context(many, 3)
        assert out[-1] == ["id00027", "id00054", "id00081"] or len(out) == 20_000
        """,
        hints=["Sort key `(-score, id)` gives best score first and smaller id first on ties.",
               "Keep a list of at most `k` `(-score, id)` pairs: insert with `bisect.insort` and drop the last when it grows beyond `k`; each step is O(k)."],
        solution="""
        import bisect

        def rank_with_context(scores, k):
            top, out = [], []
            for item_id, score in scores:
                bisect.insort(top, (-score, item_id))
                if len(top) > k:
                    top.pop()
                out.append([i for _, i in top])
            return out
        """,
        why="""Sorting the full history at every step repeats work: after n items the function had sorted 1, 2, ..., n elements, O(n^2 log n) in total, which is hours for a long
        stream. Only the current top `k` can ever matter, so a bounded structure of size `k` suffices: insertion into a sorted list of length `k` is O(k), and the whole run is
        O(n k), linear for a fixed `k`. Encoding the order in the key `(-score, id)` makes both directions explicit: higher score first, then **smaller** id, where
        `reverse=True` on `(score, id)` had flipped the tie-break too. For large `k`, a heap gives O(log k) per step."""),
)

section("hard", "Hard",
    write("Measure complexity by counting", "hard", tag="Data work",
        prompt="""Write `count_comparisons(fn, data)` that runs `fn` on a list of `Counted` wrappers around `data` (a class you write whose `__lt__` and `__eq__` increment a shared counter)
        and returns the number of comparisons, and `growth(fn, make_data, sizes)` returning the list of `(n, comparisons)` pairs. Use them to show that `sorted` is roughly n log n
        on random data but linear on already-sorted data, and that a selection sort is quadratic.""",
        code="""
        import math, random

        class Counted:
            pass

        def count_comparisons(fn, data):
            pass

        def growth(fn, make_data, sizes):
            pass
        """,
        tests="""
        import math, random
        def selection_sort(items):
            items = list(items)
            for i in range(len(items)):
                m = i
                for j in range(i + 1, len(items)):
                    if items[j] < items[m]:
                        m = j
                items[i], items[m] = items[m], items[i]
            return items
        rng = random.Random(1)
        rand = lambda n: [rng.random() for _ in range(n)]
        sizes = [256, 512, 1024]
        sel = growth(selection_sort, rand, sizes)
        assert [c for _, c in sel] == [n * (n - 1) // 2 for n in sizes]
        srt = growth(sorted, lambda n: list(range(n)), sizes)
        assert [c for _, c in srt] == [n - 1 for n in sizes]
        rnd = dict(growth(sorted, rand, sizes))
        assert all(0.7 * n * math.log2(n) < rnd[n] < 1.1 * n * math.log2(n) for n in sizes)
        assert count_comparisons(lambda xs: max(xs), [3, 1, 2]) == 2
        """,
        hints=["`Counted` stores a value and a class-level counter; `__lt__` increments it and compares the wrapped values. Reset the counter at the start of `count_comparisons`.",
               "`growth` calls `count_comparisons(fn, make_data(n))` for each size."],
        solution="""
        import math, random


        class Counted:
            calls = 0

            def __init__(self, value):
                self.value = value

            def __lt__(self, other):
                Counted.calls += 1
                return self.value < other.value

            def __eq__(self, other):
                Counted.calls += 1
                return self.value == other.value

            __hash__ = None


        def count_comparisons(fn, data):
            Counted.calls = 0
            fn([Counted(x) for x in data])
            return Counted.calls


        def growth(fn, make_data, sizes):
            return [(n, count_comparisons(fn, make_data(n))) for n in sizes]
        """,
        why="""Counting comparisons measures an algorithm's work exactly, free of timer noise, and makes complexity visible: selection sort does exactly `n(n - 1) / 2` comparisons
        whatever the input (quadratic), while Python's Timsort needs only `n - 1` on sorted input, because it detects the existing run, and about `n log2 n` on random data, the
        lower bound for comparison sorting. That adaptivity is why sorting nearly sorted data (appending a few items to a sorted list and re-sorting) is cheap in Python. The
        same instrumentation technique (wrapping objects to count operations) helps verify the complexity of your own functions in tests."""),
    fix("Read the code: a quadratic log processor", "hard", tag="Data work",
        prompt="""`process(events)` groups events by user and returns, per user, the ordered list of actions and a summary string. It uses a list as a FIFO queue but pops from the
        wrong end (so actions come out reversed), searches users in a list, recomputes a sorted list of users each iteration, and builds the summary with string `+=`. Fix the
        order bug and remove the hidden quadratic costs: a `deque`, a dict, one sort at the end, and `join`.""",
        code="""
        def process(events):
            queue = list(events)
            users = []
            actions = []
            while queue:
                user, action = queue.pop()
                if user not in users:
                    users.append(user)
                    actions.append([])
                actions[users.index(user)].append(action)
                ordered = sorted(users)
            summary = ""
            for u in ordered:
                summary += f"{u}:{len(actions[users.index(u)])};"
            return {u: actions[users.index(u)] for u in ordered}, summary
        """,
        tests="""
        events = [("bo", "login"), ("ana", "search"), ("bo", "ask"), ("ana", "ask"), ("bo", "logout")]
        grouped, summary = process(events)
        assert grouped == {"ana": ["search", "ask"], "bo": ["login", "ask", "logout"]} and list(grouped) == ["ana", "bo"]
        assert summary == "ana:2;bo:3;"
        assert process([]) == ({}, "")
        big = [(f"u{i % 5000:04d}", f"a{i}") for i in range(100_000)]
        g, s = process(big)
        assert len(g) == 5000 and g["u0000"][:2] == ["a0", "a5000"] and s.startswith("u0000:20;u0001:20;")
        """,
        hints=["`queue = deque(events)` and `popleft()` for FIFO order (or simply iterate over `events`).",
               "`actions = defaultdict(list)`; sort the keys once after the loop; `\"\".join(f\"{u}:{len(actions[u])};\" for u in ordered)`."],
        solution="""
        from collections import defaultdict, deque


        def process(events):
            queue = deque(events)
            actions = defaultdict(list)
            while queue:
                user, action = queue.popleft()
                actions[user].append(action)
            ordered = sorted(actions)
            summary = "".join(f"{u}:{len(actions[u])};" for u in ordered)
            return {u: actions[u] for u in ordered}, summary
        """,
        why="""The correctness bug first: `pop()` takes from the end, so the queue was processed last-in first-out and every user's actions came out reversed; `popleft` on a deque
        (or a plain `for` loop over the events) keeps the order. Then the hidden costs: `user not in users` and `users.index(user)` scanned a list on every event (O(n * u)), a
        `sorted` of all users ran inside the loop (O(n * u log u)), and string `+=` can copy the growing summary each time. A dict from user to actions makes grouping O(1) per
        event, sorting happens once, and `join` builds the summary in one pass, so the whole function is O(n + u log u) and the 100,000-event test runs in a fraction of a
        second instead of minutes."""),
    predict("Timsort adapts to its input", "hard",
        code="""
        import random

        class C:
            n = 0
            def __init__(self, v):
                self.v = v
            def __lt__(self, other):
                C.n += 1
                return self.v < other.v

        def comparisons(values):
            C.n = 0
            sorted(C(v) for v in values)
            return C.n

        n = 1024
        rng = random.Random(0)
        shuffled = list(range(n))
        rng.shuffle(shuffled)
        nearly = list(range(n))
        nearly[100], nearly[900] = nearly[900], nearly[100]
        print(comparisons(range(n)), comparisons(range(n, 0, -1)), comparisons(nearly) < 3 * n, comparisons(shuffled) > 8 * n)
        print(comparisons(list(range(512)) + list(range(512))) < 2 * n, comparisons([5] * n))
        """,
        hints=["Timsort finds runs that are already ascending, or strictly descending (which it reverses), and merges runs."],
        why="""Sorted input is one ascending run, found with `n - 1` comparisons and no merging; a strictly descending input is one run that Timsort reverses in place, also `n - 1`.
        A nearly sorted list, or two sorted halves, needs only a few merges, so the cost stays a small multiple of n, while a random permutation costs about `n log2 n`
        (roughly 10 per element here). Equal elements form one ascending run. Real data is often partly ordered (timestamps, appended logs, re-sorting after small changes),
        so Python's sort is frequently much faster than its O(n log n) worst case suggests."""),
)

section("interview", "Interview questions",
    explain("What is the time complexity of looking up a key in a Python dict, and when is it not O(1)?", "medium", tag="Interview",
        why="""A dict is a hash table: Python hashes the key, uses the hash to pick a slot in an array, and compares the key with what is stored there, probing a few other slots on
        collisions. On average this takes constant time, O(1), independent of the dict's size, because the table is kept at most about two thirds full and resized (an O(n)
        rehash, amortised over many inserts) as it grows. The worst case is O(n): if many keys share hash values, lookups degrade into scanning colliding entries, which can
        happen with a badly written `__hash__` (for example returning a constant) or adversarial inputs (string hashes are randomised per process to defend against that).
        The key's hash and equality also have their own costs: hashing a long string or a big tuple is O(length) the first time (strings cache their hash). Iteration over
        a dict is O(n) and preserves insertion order."""),
    explain("Why is appending to a list O(1) but inserting at the front O(n)?", "medium", tag="Interview",
        why="""A Python list is a dynamic array: a contiguous block of pointers with spare capacity. Appending writes into the next free slot, O(1); when the capacity runs out, the list
        allocates a larger block (over-allocating by a proportion of its size) and copies the pointers, an O(n) step, but because capacity grows geometrically those copies
        happen rarely enough that their total cost is proportional to the number of appends, so each append is **amortised** O(1). Inserting at index 0 must shift every
        existing pointer one place to the right to make room, which touches all n elements every time, O(n); the same applies to `pop(0)`. When you need fast operations at
        the front, use `collections.deque` (O(1) at both ends), and when you need fast inserts in the middle of sorted data, consider a different structure (a heap, a balanced
        tree such as `sortedcontainers`, or batching and re-sorting)."""),
    explain("A colleague's data pipeline is fast on test data but never finishes on production data. How do you find and fix the problem?", "hard", tag="Interview",
        why="""Suspect superlinear growth hidden by small test inputs. Reproduce with increasing input sizes (1x, 2x, 4x a sample) and time each run: if doubling the input quadruples the
        time, there is an O(n^2) step. Profile a representative run with `cProfile` (or `py-spy` on the live process, which needs no code changes) to see which functions
        dominate, and look in them for the usual patterns: `in` on a list inside a loop, `list.pop(0)` or `insert(0, ...)`, `sorted`, `max` or `index` recomputed per item,
        string or list concatenation in a loop, pandas `apply` or row-wise loops where vectorised operations exist, repeated queries per row (N+1 queries) instead of a join,
        and loading data inside a loop. Fix with the right structure (sets and dicts for lookups, deques for queues, heaps for top-k), hoisting work out of loops, batching,
        and vectorisation, then confirm with the same doubling measurement that the growth is now linear, and add a test or benchmark on a large input so it does not come
        back."""),
)

recap(
    "Big-O describes growth: double the input and see how the cost changes; drop constants and smaller terms.",
    "Recognise the shapes: one loop O(n), halving O(log n), nested loops over the data O(n^2), sorting O(n log n).",
    "Measure: doubling experiments, log-log slopes, `cProfile`, and exact operation counts.",
    "Know the built-ins: list append and pop from the end O(1) (amortised), front operations and `in` O(n); dict and set operations O(1) on average; deque O(1) at both ends; heap operations O(log n).",
    "Hunt hidden quadratics: `in` on lists, `pop(0)`, sorting or searching inside loops, and concatenation in loops.",
)
