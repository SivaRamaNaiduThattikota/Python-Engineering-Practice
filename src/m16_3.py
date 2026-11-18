from lesson import *

lesson(
    id="m16-3", num="16.3", title="Two pointers and binary search",
    intro="Sorted data unlocks two of the most useful techniques in interviews and in data code: two pointers that walk towards each "
          "other or in step, in O(n) with no extra memory, and binary search, which finds a position, or the best value of a "
          "parameter, in O(log n) steps. The `bisect` module, writing binary search without off-by-one errors, searching on the "
          "answer with a monotone check, and applications such as thresholds, token budgets and point-in-time lookups.",
    desc="Sorted-data patterns and searching on the answer.",
    keys="two pointers sorted array pair sum merge dedupe in place fast slow pointers cycle binary search bisect bisect_left bisect_right insort lower bound upper bound invariant off by one search on the answer monotone predicate threshold point in time",
)

term("Two pointers", "Two indices that move through a sequence (often towards each other on sorted data) so that each step discards part of the search space.")
term("Binary search", "Finding a position in sorted data by repeatedly comparing with the middle element and discarding half, O(log n).")
term("Monotone predicate", "A yes/no test that flips only once along an ordered range, for example false for small values and true from some point on.")

section("pointers", "Two pointers",
    p("""On **sorted** data, two indices can replace a nested loop. To find a pair with a given sum, start one pointer at each end: if the pair's sum is too small, the left
    element is too small for **every** remaining partner, so move left forward; if too large, move right back. Each step discards one element for good, O(n) total with O(1)
    extra memory, compared with the hash-set approach of 16.2, which needs O(n) memory but no sorting. Pointers moving **in step** merge two sorted lists (the merge step of
    merge sort, `heapq.merge`), remove duplicates in place (a slow pointer marks where the next unique value goes, a fast one scans), and partition arrays. **Fast and slow**
    pointers, one moving twice as fast, detect cycles in linked structures: if there is a loop, the fast one laps the slow one (problem 11)."""),
    ex("""
    def pair_sum_sorted(nums, target):
        lo, hi = 0, len(nums) - 1
        while lo < hi:
            s = nums[lo] + nums[hi]
            if s == target:
                return nums[lo], nums[hi]
            if s < target:
                lo += 1
            else:
                hi -= 1
        return None

    def dedupe_sorted_in_place(nums):
        if not nums:
            return 0
        write = 1
        for read in range(1, len(nums)):
            if nums[read] != nums[write - 1]:
                nums[write] = nums[read]
                write += 1
        return write

    print(pair_sum_sorted([1, 3, 4, 6, 8, 11], 14), pair_sum_sorted([1, 2, 3], 10))
    data = [1, 1, 2, 2, 2, 5, 7, 7]
    k = dedupe_sorted_in_place(data)
    print(k, data[:k])
    """, "two_pointers.py"),
)

section("bisect", "Binary search and the bisect module",
    p("""Binary search keeps an interval that must contain the answer and halves it each step: n = 1,000,000 takes about 20 comparisons. Python's **`bisect`** module implements it
    for sorted lists: **`bisect_left(a, x)`** returns the first index where `x` could be inserted keeping order (the index of the first element `>= x`), **`bisect_right(a, x)`**
    the index after the last element `<= x`; their difference counts occurrences of `x`, and `bisect_right(a, x) - 1` is the last element at or before `x`. `insort` inserts
    in order (O(log n) to find the place, O(n) to shift). Since Python 3.10, a `key=` argument lets you search a list of records by a field, as long as the list is sorted by
    that field."""),
    p("""Writing binary search by hand is famously error-prone, so use a fixed **invariant**. For "the first index where `pred(i)` is true" (lower bound): keep `lo` where the
    predicate might still be false and `hi` where it is known true (start `hi = len(a)`), loop `while lo < hi`, compute `mid = (lo + hi) // 2`, and set `hi = mid` if the
    predicate holds at `mid`, else `lo = mid + 1`. The loop always shrinks the interval and ends with `lo == hi` at the answer. Most bugs come from mixing conventions:
    `hi = len(a) - 1` with `while lo < hi` never examines the last element, and `lo = mid` instead of `mid + 1` can loop forever (problem 3)."""),
    ex("""
    from bisect import bisect_left, bisect_right, insort

    scores = [0.12, 0.35, 0.35, 0.35, 0.61, 0.80, 0.93]
    print(bisect_left(scores, 0.35), bisect_right(scores, 0.35), bisect_right(scores, 0.35) - bisect_left(scores, 0.35))
    print(bisect_left(scores, 0.5), bisect_left(scores, 1.0), bisect_left(scores, 0.0))
    insort(scores, 0.5)
    print(scores)

    def lower_bound(n, pred):
        lo, hi = 0, n
        while lo < hi:
            mid = (lo + hi) // 2
            if pred(mid):
                hi = mid
            else:
                lo = mid + 1
        return lo

    print(lower_bound(len(scores), lambda i: scores[i] >= 0.6), lower_bound(100, lambda x: x * x >= 2000))
    """, "bisect_basics.py"),
)

section("answer", "Binary search on the answer",
    p("""Binary search is not only for lists. Whenever a question asks for the **smallest (or largest) value** of some parameter that satisfies a condition, and the condition is
    **monotone** (once true, true for all larger values), you can binary search the parameter itself: the smallest capacity that ships all packages within D days, the
    largest batch size that fits in GPU memory, the lowest classifier threshold that keeps recall above 90%, the smallest number of workers that meets a deadline. Each
    probe runs the (possibly expensive) check once, and O(log range) probes suffice, instead of trying every value. The work is in proving monotonicity and choosing safe
    bounds: `lo` must be a value that is definitely too small (or the smallest possible answer) and `hi` one that definitely works (problems 7 and 12)."""),
)

section("warmup", "Warm-up",
    predict("bisect with duplicates", "easy",
        code="""
        from bisect import bisect_left, bisect_right, insort_left, insort_right

        a = [10, 20, 20, 20, 30]
        print(bisect_left(a, 20), bisect_right(a, 20), bisect_left(a, 25), bisect_right(a, 5), bisect_left(a, 99))
        print(bisect_right(a, 20) - bisect_left(a, 20), bisect_right(a, 29) - 1, a[bisect_right(a, 29) - 1])
        b = [(1, "a"), (2, "b"), (2, "c")]
        insort_right(b, (2, "bb"))
        insort_left(b, (2, "a"))
        print(b)
        """,
        hints=["`bisect_left` gives the first position of an equal element, `bisect_right` the position after the last one."],
        why="""For a value that is present, `bisect_left` points at its first occurrence and `bisect_right` just past its last, so their difference counts it; for an absent value, both
        give the insertion point. `bisect_right(a, x) - 1` is the index of the last element `<= x`, the "value as of" lookup used for timestamps (problem 13). Insertion
        functions compare whole tuples, so `(2, "a")` sorts before `(2, "b")` and `(2, "bb")` between `(2, "b")` and `(2, "c")`."""),
    write("All pairs with a target sum, sorted input", "easy", tag="Data work",
        prompt="""Write `pairs_with_sum(nums, target)` for a **sorted** list, returning every **distinct** pair of values `(a, b)` with `a <= b` and `a + b == target`, in increasing order of
        `a`, using two pointers and O(1) extra memory (apart from the output).""",
        code="""
        def pairs_with_sum(nums, target):
            pass
        """,
        tests="""
        assert pairs_with_sum([1, 2, 3, 4, 5, 6, 7], 8) == [(1, 7), (2, 6), (3, 5)]
        assert pairs_with_sum([1, 1, 2, 2, 3, 3], 4) == [(1, 3), (2, 2)]
        assert pairs_with_sum([2, 2, 2], 4) == [(2, 2)] and pairs_with_sum([1, 5], 3) == [] and pairs_with_sum([], 0) == []
        """,
        hints=["When a pair matches, record it, then move **both** pointers past every copy of their current values to avoid repeats."],
        solution="""
        def pairs_with_sum(nums, target):
            out = []
            lo, hi = 0, len(nums) - 1
            while lo < hi:
                s = nums[lo] + nums[hi]
                if s < target:
                    lo += 1
                elif s > target:
                    hi -= 1
                else:
                    out.append((nums[lo], nums[hi]))
                    a, b = nums[lo], nums[hi]
                    while lo < hi and nums[lo] == a:
                        lo += 1
                    while lo < hi and nums[hi] == b:
                        hi -= 1
            return out
        """,
        why="""Because the list is sorted, a sum that is too small can only be fixed by a larger left value and a sum that is too large by a smaller right value, so each comparison
        discards one element: O(n) after sorting, with constant extra memory. Skipping all copies of both values after a match is what makes the pairs distinct (`(1, 3)` once,
        though there are four index pairs). The `(2, 2)` case shows why the pointers must stay on different indices (`lo < hi`): a value pairs with itself only when it occurs
        twice. Sorting first costs O(n log n), so on unsorted data the hash approach of 16.2 is usually simpler unless memory is tight."""),
    fix("A binary search that misses the last element", "easy", tag="ML",
        prompt="""`find(sorted_ids, target)` should return the index of `target` in a sorted list or `-1`. It mixes conventions (`hi` set to the last index but the loop runs `while lo <
        hi`), so it never finds the last element and reports a missing target in a one-element list. Fix it with one consistent invariant.""",
        code="""
        def find(sorted_ids, target):
            lo, hi = 0, len(sorted_ids) - 1
            while lo < hi:
                mid = (lo + hi) // 2
                if sorted_ids[mid] == target:
                    return mid
                if sorted_ids[mid] < target:
                    lo = mid + 1
                else:
                    hi = mid - 1
            return -1
        """,
        tests="""
        ids = [3, 8, 15, 23, 42, 57]
        assert [find(ids, x) for x in ids] == [0, 1, 2, 3, 4, 5]
        assert find(ids, 4) == -1 and find(ids, 99) == -1 and find([], 1) == -1 and find([7], 7) == 0
        """,
        hints=["Either keep `hi = len - 1` and loop `while lo <= hi`, or use the half-open `[lo, hi)` with `hi = len` and `hi = mid`."],
        solution="""
        def find(sorted_ids, target):
            lo, hi = 0, len(sorted_ids) - 1
            while lo <= hi:
                mid = (lo + hi) // 2
                if sorted_ids[mid] == target:
                    return mid
                if sorted_ids[mid] < target:
                    lo = mid + 1
                else:
                    hi = mid - 1
            return -1
        """,
        why="""With an inclusive interval `[lo, hi]`, the search space is empty only when `lo > hi`, so the loop must run while `lo <= hi`; stopping at `lo == hi` skipped the last
        candidate, which is why the last id and the only element of a one-item list were never found. Pick one convention (inclusive bounds with `<=`, or half-open bounds with
        `<` and `hi = mid`) and keep every update consistent with it. In practice, `i = bisect_left(a, x)` followed by `i < len(a) and a[i] == x` avoids writing the loop at all."""),
    predict("Merging and cleaning sorted data", "easy",
        code="""
        import heapq

        a = [1, 4, 9, 12]
        b = [2, 4, 10]
        c = [0, 15]
        print(list(heapq.merge(a, b, c)))
        print(list(heapq.merge(["b", "a"], ["c"], key=str.lower)))

        def merge_two(x, y):
            i = j = 0
            out = []
            while i < len(x) and j < len(y):
                if x[i] <= y[j]:
                    out.append(x[i])
                    i += 1
                else:
                    out.append(y[j])
                    j += 1
            return out + x[i:] + y[j:]

        print(merge_two(a, b), merge_two([], b), merge_two([5], [1, 2]))
        """,
        hints=["`heapq.merge` assumes each input is already sorted; it does not sort them."],
        why="""Merging sorted inputs takes one pass with a pointer per input, O(total length), which is how merge sort combines halves and how large sorted files or log streams are
        combined without loading them all (`heapq.merge` works lazily on any number of iterators). It trusts its inputs: `["b", "a"]` is not sorted, so the output is not either,
        a reminder that these algorithms rely on their preconditions. The hand-written two-pointer merge appends whichever head is smaller, then the leftovers; using `<=` keeps
        equal elements from the first list first, which makes the merge stable."""),
)

section("medium", "Medium",
    write("Lower and upper bounds from scratch", "medium", tag="Data work",
        prompt="""Without the `bisect` module, write `lower_bound(a, x)` (the first index with `a[i] >= x`) and `upper_bound(a, x)` (the first index with `a[i] > x`) for a sorted list,
        both returning `len(a)` when there is none, and `count_in_range(a, lo, hi)` counting elements with `lo <= v <= hi`, all in O(log n).""",
        code="""
        def lower_bound(a, x):
            pass

        def upper_bound(a, x):
            pass

        def count_in_range(a, lo, hi):
            pass
        """,
        tests="""
        import bisect, random
        a = [1, 3, 3, 3, 5, 8, 8, 13]
        assert [lower_bound(a, x) for x in (0, 1, 3, 4, 8, 13, 14)] == [0, 0, 1, 4, 5, 7, 8]
        assert [upper_bound(a, x) for x in (0, 1, 3, 4, 8, 13, 14)] == [0, 1, 4, 4, 7, 8, 8]
        assert count_in_range(a, 3, 8) == 6 and count_in_range(a, 9, 12) == 0 and count_in_range([], 0, 1) == 0
        rng = random.Random(4)
        data = sorted(rng.randint(0, 50) for _ in range(500))
        assert all(lower_bound(data, x) == bisect.bisect_left(data, x) and upper_bound(data, x) == bisect.bisect_right(data, x) for x in range(-2, 54))
        """,
        hints=["Half-open interval: `lo, hi = 0, len(a)`; while `lo < hi`: `mid = (lo + hi) // 2`; if `a[mid] < x` (or `<= x` for the upper bound) `lo = mid + 1` else `hi = mid`."],
        solution="""
        def lower_bound(a, x):
            lo, hi = 0, len(a)
            while lo < hi:
                mid = (lo + hi) // 2
                if a[mid] < x:
                    lo = mid + 1
                else:
                    hi = mid
            return lo


        def upper_bound(a, x):
            lo, hi = 0, len(a)
            while lo < hi:
                mid = (lo + hi) // 2
                if a[mid] <= x:
                    lo = mid + 1
                else:
                    hi = mid
            return lo


        def count_in_range(a, lo, hi):
            return upper_bound(a, hi) - lower_bound(a, lo)
        """,
        why="""Both functions use the half-open invariant: the answer always lies in `[lo, hi]`, everything before `lo` is known too small, and everything from `hi` on is known to qualify,
        so the loop ends with `lo == hi` at the boundary and never runs forever, because `mid < hi` guarantees progress in both branches. The only difference is `<` versus `<=`,
        which decides whether equal elements count as "before" the boundary. A range count is the difference of two boundaries, O(log n) on a sorted column, which is how
        databases answer `WHERE score BETWEEN a AND b` with an index. Testing against `bisect` on random data catches off-by-one mistakes quickly."""),
    write("The highest threshold that keeps recall", "medium", tag="ML",
        prompt="""For a spam classifier, write `highest_threshold(scores, labels, min_recall)` returning the **highest** threshold `t` (one of the scores) such that predicting spam for
        `score >= t` keeps recall (the share of true spam caught) at least `min_recall`, or `None` if no positives exist. Recall can only fall as the threshold rises, so binary
        search the sorted distinct scores, computing recall in O(log n) per probe with a sorted list of positive scores and `bisect`.""",
        code="""
        from bisect import bisect_left

        def highest_threshold(scores, labels, min_recall):
            pass
        """,
        tests="""
        scores = [0.95, 0.9, 0.8, 0.7, 0.65, 0.6, 0.4, 0.3, 0.2, 0.1]
        labels = [1, 1, 0, 1, 1, 0, 1, 0, 0, 0]
        assert highest_threshold(scores, labels, 1.0) == 0.4
        assert highest_threshold(scores, labels, 0.8) == 0.65
        assert highest_threshold(scores, labels, 0.4) == 0.9 and highest_threshold(scores, labels, 0.2) == 0.95
        assert highest_threshold([0.5, 0.2], [0, 0], 0.5) is None
        """,
        hints=["`pos = sorted(s for s, y in zip(scores, labels) if y)`; recall at `t` is `(len(pos) - bisect_left(pos, t)) / len(pos)`.",
               "Find the last index `i` in the sorted distinct thresholds where recall is still enough: binary search for the first one where it is not, then step back."],
        solution="""
        from bisect import bisect_left


        def highest_threshold(scores, labels, min_recall):
            pos = sorted(s for s, y in zip(scores, labels) if y)
            if not pos:
                return None

            def recall(t):
                return (len(pos) - bisect_left(pos, t)) / len(pos)

            candidates = sorted(set(scores))
            lo, hi = 0, len(candidates)
            while lo < hi:
                mid = (lo + hi) // 2
                if recall(candidates[mid]) >= min_recall:
                    lo = mid + 1
                else:
                    hi = mid
            return candidates[lo - 1] if lo > 0 else None
        """,
        why="""As the threshold rises, fewer examples are predicted positive, so recall never increases: "recall is enough" is true up to some threshold and false after it, a monotone
        predicate, and binary search finds the boundary in O(log n) probes. Each probe counts positives at or above the threshold with one `bisect` on the sorted positive
        scores, so the whole search is O(n log n) for sorting plus O(log^2 n) for searching, instead of recomputing recall over all data for every candidate. Picking the
        highest threshold that meets the recall target minimises false positives subject to the constraint, a common way to set operating points for moderation and fraud
        models."""),
    fix("Binary search on the answer with bad bounds", "medium", tag="ML",
        prompt="""`min_capacity(sizes, batches)` should return the smallest per-batch capacity (in tokens) that lets a list of documents be processed **in order** in at most `batches`
        batches, each batch holding consecutive documents whose sizes sum to at most the capacity. The search starts at `lo = 0`, so it can return a capacity smaller than the
        largest single document (which can never fit), and `hi = sum(sizes) - 1` excludes the answer when one batch is allowed. Fix the bounds.""",
        code="""
        def fits(sizes, capacity, batches):
            used, current = 1, 0
            for s in sizes:
                if current + s > capacity:
                    used += 1
                    current = 0
                current += s
            return used <= batches


        def min_capacity(sizes, batches):
            lo, hi = 0, sum(sizes) - 1
            while lo < hi:
                mid = (lo + hi) // 2
                if fits(sizes, mid, batches):
                    hi = mid
                else:
                    lo = mid + 1
            return lo
        """,
        tests="""
        assert min_capacity([120, 300, 80, 500, 200], 3) == 500
        assert min_capacity([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 5) == 15
        assert min_capacity([3, 2, 2, 4, 1, 4], 3) == 6
        assert min_capacity([7, 2, 5], 1) == 14 and min_capacity([7, 2, 5], 10) == 7
        """,
        hints=["The answer is at least the largest document and at most the total: `lo, hi = max(sizes), sum(sizes)`."],
        solution="""
        def fits(sizes, capacity, batches):
            used, current = 1, 0
            for s in sizes:
                if current + s > capacity:
                    used += 1
                    current = 0
                current += s
            return used <= batches


        def min_capacity(sizes, batches):
            lo, hi = max(sizes), sum(sizes)
            while lo < hi:
                mid = (lo + hi) // 2
                if fits(sizes, mid, batches):
                    hi = mid
                else:
                    lo = mid + 1
            return lo
        """,
        why="""Binary search on the answer is only correct if the predicate is monotone over the whole search range and the range contains the answer. `fits` is monotone for capacities
        at least as large as the biggest document (more capacity never needs more batches), but below that it is wrong: with capacity 0 every document "starts a new batch" and
        is still added, so the greedy count can look acceptable for a capacity that cannot hold anything. Starting at `max(sizes)` keeps the search where the predicate is
        meaningful, and `sum(sizes)`, one batch with everything, is always feasible, so `hi` must include it. The greedy check is O(n) and the search O(n log(sum)), the same
        shape as sizing shards, batches or GPU memory."""),
    choose("Many lookups in a sorted list", "medium", tag="Data work",
        prompt="Both find, for 2,000 timestamps, how many of 50,000 sorted event times are at or before it. Which is faster?",
        setup="""import bisect, random
rng = random.Random(0)
events = sorted(rng.random() * 1000 for _ in range(50_000))
queries = [rng.random() * 1000 for _ in range(2_000)]""",
        options={
            "a": "counts = [sum(1 for e in events if e <= q) for q in queries[:200]]",
            "b": "counts = [bisect.bisect_right(events, q) for q in queries[:200]]",
        },
        answer="b",
        hints=["How much of the list does each version look at per query?"],
        why="""The comprehension scans all 50,000 events for every query, O(n) per query, while `bisect_right` performs about 16 comparisons, O(log n), and runs in C. Once data is sorted,
        any "how many are below", "what is the last one before" or "where would this go" question should be a binary search; sorting once (O(n log n)) pays for itself after a
        handful of queries."""),
    trace("Watching a binary search", "medium",
        prompt="Fill in `steps` after each marked line: the list of `(lo, hi)` pairs at the start of each loop iteration, and the result.",
        code="""
        def first_at_least(a, x):
            lo, hi, history = 0, len(a), []
            while lo < hi:
                history.append((lo, hi))
                mid = (lo + hi) // 2
                if a[mid] < x:
                    lo = mid + 1
                else:
                    hi = mid
            return history, lo

        a = [2, 5, 8, 12, 16, 23, 38, 56]
        steps = first_at_least(a, 23)  # row: "present"
        steps = first_at_least(a, 1)  # row: "smaller than all"
        steps = first_at_least(a, 99)  # row: "larger than all"
        steps = first_at_least(a, 13)  # row: "between"
        """,
        trace_vars=["steps"],
        hints=["Each iteration roughly halves `hi - lo`. `mid = (lo + hi) // 2`; going left keeps `hi = mid`, going right sets `lo = mid + 1`."],
        why="""Every iteration halves the interval, so eight elements need three or four steps, never more than `log2(8) + 1`. For a present value the search narrows to its first index; for a value smaller than
        everything, `hi` keeps moving left and the answer is 0; larger than everything, `lo` keeps moving right and the answer is `len(a)`, meaning "no such element"; for a
        value between elements, the answer is the index where it would be inserted. The number of steps barely depends on the target and grows by one each time the list doubles, which is what O(log n) means in practice."""),
    write("How many chunks fit the budget", "medium", tag="RAG",
        prompt="""Chunks are ranked best first. Write `max_chunks(token_counts, budget)` returning how many leading chunks fit within `budget` tokens, using prefix sums and `bisect` (O(log n)
        per query after O(n) set-up), as a class `Budgeter(token_counts)` with `max_chunks(budget)`. Also write `fit_largest(n_max, fits)` that binary searches the largest `n` in
        `0..n_max` for which the (expensive, monotone) check `fits(n)` is true, calling `fits` at most `ceil(log2(n_max + 1)) + 1` times.""",
        code="""
        from bisect import bisect_right
        from itertools import accumulate

        class Budgeter:
            pass

        def fit_largest(n_max, fits):
            pass
        """,
        tests="""
        import math
        b = Budgeter([120, 300, 80, 500, 200])
        assert [b.max_chunks(t) for t in (0, 119, 120, 499, 500, 1000, 1200, 5000)] == [0, 0, 1, 2, 3, 4, 5, 5]
        calls = []
        def fits(n):
            calls.append(n)
            return n * 37 <= 1000
        assert fit_largest(100, fits) == 27 and len(calls) <= math.ceil(math.log2(101)) + 1
        assert fit_largest(10, lambda n: True) == 10 and fit_largest(10, lambda n: n == 0) == 0
        """,
        hints=["`self.prefix = list(accumulate(token_counts))`; the answer is `bisect_right(self.prefix, budget)`.",
               "For `fit_largest`, search the first `n` in `1..n_max + 1` where `fits(n)` is false (treat `n_max + 1` as false without calling), then subtract one."],
        solution="""
        from bisect import bisect_right
        from itertools import accumulate


        class Budgeter:
            def __init__(self, token_counts):
                self.prefix = list(accumulate(token_counts))

            def max_chunks(self, budget):
                return bisect_right(self.prefix, budget)


        def fit_largest(n_max, fits):
            lo, hi = 1, n_max + 1
            while lo < hi:
                mid = (lo + hi) // 2
                if fits(mid):
                    lo = mid + 1
                else:
                    hi = mid
            return lo - 1
        """,
        why="""Prefix sums turn "the total of the first k chunks" into one array element, and because token counts are positive the prefix sums are sorted, so "how many fit" is a
        `bisect_right` for the budget: the number of prefix totals that are at most the budget. Each new budget (per model, per request) is answered in O(log n). When the check
        is not a simple sum, for example "does the rendered prompt with n examples fit the model's context after tokenisation?", the same idea applies to the parameter itself:
        `fit_largest` makes about seven calls to an expensive check for a range of 100, instead of up to 100. It assumes `fits(0)` holds (an empty prompt always fits)."""),
    predict("Fast and slow pointers", "medium",
        code="""
        def find_cycle(next_of, start):
            slow = fast = start
            while fast in next_of and next_of[fast] in next_of:
                slow = next_of[slow]
                fast = next_of[next_of[fast]]
                if slow == fast:
                    slow = start
                    while slow != fast:
                        slow, fast = next_of[slow], next_of[fast]
                    return slow
            return None

        redirects = {"/a": "/b", "/b": "/c", "/c": "/d", "/d": "/b"}
        print(find_cycle(redirects, "/a"))
        print(find_cycle({"/x": "/y", "/y": "/z"}, "/x"), find_cycle({"/self": "/self"}, "/self"))
        """,
        hints=["If there is a cycle, the fast pointer eventually meets the slow one inside it; restarting one pointer from the start and moving both one step at a time, they meet at the cycle's entry."],
        why="""Following redirects, `/b` leads to `/c`, `/d` and back to `/b`: a loop that would hang a crawler. The fast pointer moves two steps per round and the slow one one step, so
        inside a loop the gap shrinks by one each round and they must meet; then a pointer restarted from the beginning and one from the meeting point, both moving one step,
        meet exactly at the loop's entry, `/b` (Floyd's algorithm). A chain that ends returns `None`, and a page redirecting to itself is a loop of length one. It uses O(1)
        memory; a `seen` set (16.2) is simpler when memory is not a concern."""),
)

section("hard", "Hard",
    write("Split work into k balanced parts", "hard", tag="ML",
        prompt="""Write `split_balanced(costs, k)` that splits a list of task costs into at most `k` **contiguous** parts minimising the largest part's total, returning `(largest, parts)`
        where `parts` lists the parts (as lists). Binary search the largest total between `max(costs)` and `sum(costs)` with a greedy feasibility check, then build the parts
        greedily for the answer. This is how consecutive model layers or sorted documents are assigned to workers.""",
        code="""
        def split_balanced(costs, k):
            pass
        """,
        tests="""
        largest, parts = split_balanced([7, 2, 5, 10, 8], 2)
        assert largest == 18 and parts == [[7, 2, 5], [10, 8]]
        largest, parts = split_balanced([1, 2, 3, 4, 5, 6, 7, 8, 9], 3)
        assert largest == 17 and sum(map(sum, parts)) == 45 and max(map(sum, parts)) == 17 and len(parts) <= 3
        assert split_balanced([4, 4, 4, 4], 4) == (4, [[4], [4], [4], [4]]) and split_balanced([5], 3) == (5, [[5]])
        assert split_balanced([3, 1, 2], 1) == (6, [[3, 1, 2]])
        """,
        hints=["`can(limit)`: walk the costs, starting a new part whenever adding the next cost would exceed `limit`; feasible if parts used <= k.",
               "After finding the smallest feasible limit, run the same greedy walk again, collecting the parts."],
        solution="""
        def _greedy(costs, limit):
            parts, current, total = [], [], 0
            for c in costs:
                if current and total + c > limit:
                    parts.append(current)
                    current, total = [], 0
                current.append(c)
                total += c
            if current:
                parts.append(current)
            return parts


        def split_balanced(costs, k):
            lo, hi = max(costs), sum(costs)
            while lo < hi:
                mid = (lo + hi) // 2
                if len(_greedy(costs, mid)) <= k:
                    hi = mid
                else:
                    lo = mid + 1
            return lo, _greedy(costs, lo)
        """,
        why="""Asking for "the smallest possible maximum" invites binary search on the answer: if every part can stay under a limit L, it can also stay under any larger limit, so feasibility
        is monotone in L, between the largest single cost (no part can be smaller) and the total (one part). The greedy check, packing tasks into the current part until the next
        one would overflow, is optimal for contiguous parts, so each probe is O(n) and the whole search O(n log(sum)). The same greedy walk at the final limit produces the
        assignment. Pipeline-parallel training splits consecutive layers across GPUs exactly this way, and batch jobs split sorted inputs into balanced shards."""),
    write("Point-in-time lookups without leakage", "hard", tag="ML",
        prompt="""For training a churn model, features must use only data known **at** each prediction time. Write `PointInTime(events)` where `events` is a list of `(timestamp, value)`
        (any order), with `as_of(t)` returning the value of the latest event with `timestamp <= t` (or `None`), `count_between(t0, t1)` counting events with `t0 < timestamp <=
        t1`, and `join(labels)` returning, for a list of `(t, label)` rows, `[(t, label, as_of(t))]`. Use sorting once and `bisect` (with `key=` or a separate list of times).""",
        code="""
        from bisect import bisect_right

        class PointInTime:
            pass
        """,
        tests="""
        events = [(30, "gold"), (10, "free"), (20, "pro"), (45, "free")]
        pit = PointInTime(events)
        assert [pit.as_of(t) for t in (5, 10, 15, 20, 44, 45, 100)] == [None, "free", "free", "pro", "gold", "free", "free"]
        assert pit.count_between(10, 30) == 2 and pit.count_between(0, 100) == 4 and pit.count_between(45, 50) == 0
        assert pit.join([(25, 0), (50, 1), (1, 0)]) == [(25, 0, "pro"), (50, 1, "free"), (1, 0, None)]
        tie = PointInTime([(10, "a"), (10, "b")])
        assert tie.as_of(10) == "b"
        """,
        hints=["Sort the events by timestamp, keeping input order for equal timestamps (`sorted` is stable), and store the timestamps in a separate list for `bisect`.",
               "`i = bisect_right(times, t)`; the latest event at or before `t` is at `i - 1` if `i > 0`. Counts are differences of two `bisect_right` calls."],
        solution="""
        from bisect import bisect_right


        class PointInTime:
            def __init__(self, events):
                self.events = sorted(events, key=lambda e: e[0])
                self.times = [t for t, _ in self.events]

            def as_of(self, t):
                i = bisect_right(self.times, t)
                return self.events[i - 1][1] if i else None

            def count_between(self, t0, t1):
                return bisect_right(self.times, t1) - bisect_right(self.times, t0)

            def join(self, labels):
                return [(t, label, self.as_of(t)) for t, label in labels]
        """,
        why="""**Leakage** (using information from after the prediction time) is the most common way ML models look great offline and fail in production: joining each label with the
        customer's **current** plan, instead of the plan at the time, lets the model see the future. A point-in-time join takes, for each label time, the latest event at or before
        it, which on sorted timestamps is `bisect_right(times, t) - 1`, O(log n) per lookup after one O(n log n) sort. Equal timestamps resolve to the last event recorded (stable
        sort plus `bisect_right`), and half-open ranges `(t0, t1]` make windows that tile without double counting. Feature stores and pandas `merge_asof` implement exactly this."""),
    fix("Read the code: three-sum with duplicate bugs", "hard", tag="Data work",
        prompt="""`three_sum(nums, target)` should return every **distinct** sorted triple of values summing to `target`, in sorted order, in O(n^2) with sorting plus two pointers. It
        reports duplicate triples, skips valid ones because it advances past duplicates before checking, and mutates the caller's list by sorting it in place. Fix all three.""",
        code="""
        def three_sum(nums, target=0):
            nums.sort()
            out = []
            for i in range(len(nums) - 2):
                lo, hi = i + 1, len(nums) - 1
                while lo < hi:
                    while lo < hi and nums[lo] == nums[lo + 1]:
                        lo += 1
                    s = nums[i] + nums[lo] + nums[hi]
                    if s == target:
                        out.append((nums[i], nums[lo], nums[hi]))
                        lo += 1
                        hi -= 1
                    elif s < target:
                        lo += 1
                    else:
                        hi -= 1
            return out
        """,
        tests="""
        data = [-1, 0, 1, 2, -1, -4]
        assert three_sum(data) == [(-1, -1, 2), (-1, 0, 1)] and data == [-1, 0, 1, 2, -1, -4]
        assert three_sum([0, 0, 0, 0]) == [(0, 0, 0)] and three_sum([1, 2, 3, 4, 5], 9) == [(1, 3, 5), (2, 3, 4)]
        assert three_sum([1, 1, 1], 5) == [] and three_sum([], 0) == []
        """,
        hints=["Sort a copy. Skip a repeated first element with `if i > 0 and a[i] == a[i - 1]: continue`.",
               "Skip repeated middle and last values **after** recording a match, by moving `lo` and `hi` past their current values."],
        solution="""
        def three_sum(nums, target=0):
            a = sorted(nums)
            out = []
            for i in range(len(a) - 2):
                if i > 0 and a[i] == a[i - 1]:
                    continue
                lo, hi = i + 1, len(a) - 1
                while lo < hi:
                    s = a[i] + a[lo] + a[hi]
                    if s < target:
                        lo += 1
                    elif s > target:
                        hi -= 1
                    else:
                        out.append((a[i], a[lo], a[hi]))
                        mid_val, hi_val = a[lo], a[hi]
                        while lo < hi and a[lo] == mid_val:
                            lo += 1
                        while lo < hi and a[hi] == hi_val:
                            hi -= 1
            return out
        """,
        why="""Three-sum reduces to "for each first element, two-sum on the rest" with two pointers, O(n^2) after an O(n log n) sort. Distinctness needs duplicates skipped at **every**
        level: the first element (otherwise `-1, -1, 2` is found once from each `-1`), and the other two after each match. The original skipped middle duplicates **before**
        evaluating, which jumped over the second `-1` that the triple `(-1, -1, 2)` needs, and never skipped repeated first elements. Sorting `nums` in place silently reordered
        the caller's data, the shared-mutation bug of 2.4; `sorted(nums)` works on a copy."""),
    predict("bisect with key and descending data", "hard",
        code="""
        from bisect import bisect_left, bisect_right, insort

        records = [("2025-01-03", 120), ("2025-01-07", 80), ("2025-01-09", 300)]
        print(bisect_left(records, "2025-01-07", key=lambda r: r[0]), bisect_right(records, "2025-01-08", key=lambda r: r[0]))
        insort(records, ("2025-01-05", 95), key=lambda r: r[0])
        print([d for d, _ in records])
        desc = [0.93, 0.8, 0.61, 0.35, 0.12]
        print(bisect_left(desc, 0.5), bisect_left([-x for x in desc], -0.5), bisect_left(desc, -0.5, key=lambda x: -x))
        ranks = sorted(records, key=lambda r: -r[1])
        print(bisect_right(ranks, -100, key=lambda r: -r[1]), [v for _, v in ranks])
        """,
        hints=["With `key=`, the search value is compared with `key(element)`, so it must be in key form already (a date string, not a record).",
               "bisect assumes ascending order; for descending data, search the negated values or use a key that negates."],
        why="""Since Python 3.10, `key=` makes bisect work on lists of records sorted by a field; the value you search for is a **key value**, the date string, while `insort` inserts a
        whole record and applies the key to it. bisect assumes ascending order: on a descending list it silently returns nonsense (here 0, "before everything", although 0.5 belongs after 0.61), while negating
        the values, or using `key=lambda x: -x` with a negated search value, turns descending into ascending and gives the correct position 3. The last line counts records with
        a value of at least 100 in a list sorted by descending value: two of them."""),
)

section("interview", "Interview questions",
    explain("How do you write a binary search without off-by-one errors?", "medium", tag="Interview",
        why="""Decide what you are searching for in terms of a monotone predicate, typically "the first index where `pred(i)` is true" (lower bound), then pick one interval convention and
        keep it. With the half-open convention: start `lo = 0, hi = len(a)` (so `len(a)` means "not found"), loop `while lo < hi`, compute `mid = (lo + hi) // 2`, and set `hi = mid`
        when `pred(mid)` holds, otherwise `lo = mid + 1`. The invariant is that everything before `lo` fails the predicate and everything from `hi` on satisfies it; `mid` is always
        strictly less than `hi`, so the interval shrinks each iteration and the loop terminates with `lo == hi` at the answer. "Last index where true" is "first index where false,
        minus one". Test the empty input, a single element, a target smaller and larger than everything, duplicates, and compare against `bisect` on random data. In production
        Python code, use `bisect_left` / `bisect_right` (with `key=` for records) rather than hand-written loops."""),
    explain("What is 'binary search on the answer', and how do you recognise when it applies?", "medium", tag="Interview",
        why="""It is binary searching over the space of possible **answers** rather than over an array: when a problem asks for the minimum (or maximum) value of a parameter such that a
        condition holds, and the condition is monotone in that parameter (if capacity C works, any larger capacity works), you can test a candidate with a feasibility check and
        halve the range each time. Recognise it by phrases such as "minimum capacity", "smallest maximum", "largest size that fits", "minimum time to finish", where checking a
        given value is easier than computing the optimum directly. You need safe bounds (a definitely infeasible or minimal `lo`, a definitely feasible `hi`), a correct and
        monotone check (often a greedy O(n) pass), and care with integer versus real-valued answers (for reals, iterate a fixed number of times or to a tolerance). Typical
        complexity is O(n log(range)). Examples: shipping within D days, splitting an array into k parts, choosing a classifier threshold for a recall target, finding the largest
        batch size that fits in memory."""),
    explain("Hash set or two pointers for finding pairs: how do you choose?", "hard", tag="Interview",
        why="""For pair or triple problems on **unsorted** data, a hash set or dict gives O(n) time with O(n) extra memory and keeps original indices easy to return, so it is usually
        the first answer (two-sum). If the data is **already sorted**, or must be sorted anyway, two pointers give O(n) time after sorting with O(1) extra memory, handle
        "closest sum" and "all distinct pairs" naturally (the hash approach needs extra care for duplicates and cannot do "closest" easily), and extend cleanly to three-sum and
        k-sum. Sorting costs O(n log n) and loses original positions unless you sort indices. Other factors: hashable elements are required for hashing, while two pointers need
        a total order; streaming data favours hashing; very large data that does not fit in memory favours sorting (external sort) plus a merge-style pass. State the trade-off
        and pick based on whether order, memory or indices matter."""),
)

recap(
    "On sorted data, two pointers replace nested loops: moving from both ends for pair sums, in step for merges and in-place deduplication, fast and slow for cycles.",
    "Binary search halves the interval each step; use `bisect_left` / `bisect_right` (with `key=` for records) for positions, counts and as-of lookups.",
    "Write searches with one invariant: half-open `[lo, hi)`, `while lo < hi`, `hi = mid` or `lo = mid + 1`.",
    "Binary search on the answer: a monotone feasibility check plus safe bounds finds minimum capacities, maximum sizes and thresholds in O(n log range).",
    "Point-in-time joins with sorted timestamps and `bisect_right` prevent feature leakage in ML datasets.",
)
