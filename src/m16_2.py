from lesson import *
from diagrams import *

lesson(
    id="m16-2", num="16.2", title="Hashing patterns",
    intro="A large share of interview problems, and of real data code, is solved by one idea: trade memory for time with a dict or a "
          "set. Counting, complement lookups (two-sum), grouping by a canonical key, sliding windows, prefix sums, LRU caches and "
          "near-duplicate detection, each with its complexity and its traps, including the hash and equality contract that every "
          "key must follow.",
    desc="Counting, two-sum style lookups and sliding windows.",
    keys="hashing dict set counter defaultdict two-sum complement grouping anagram canonical key sliding window two pointers prefix sum subarray sum lru cache ordereddict jaccard shingles near duplicate hash eq contract",
)

term("Hash table", "The structure behind dict and set: keys are hashed to positions in an array, giving average O(1) insert, delete and lookup.")
term("Sliding window", "A range of consecutive elements that moves along a sequence, updated incrementally as elements enter on one side and leave on the other.")
term("Prefix sum", "The running total up to each position; the sum of any range is the difference of two prefix sums.")

section("idea", "The core idea: remember what you have seen",
    fig(flowchart({
        "x": ("start", 0, 0, "next value x"),
        "ask": ("ask", 0, 1, "target - x in seen?"),
        "found": ("good", 1, 1, "found a pair"),
        "add": ("step", 0, 2, "seen[x] = index"),
    }, [("x", "ask"), ("ask", "found", "yes"), ("ask", "add", "no"), ("add", "x", "", {"route": [(-0.45, 2), (-0.45, 0)]})],
        cell=(240, 80), label="two-sum in one pass"),
        "Remember what you have seen in a dict, and each new value needs one O(1) lookup instead of a scan."),
    p("""Brute force often compares every element with every other, O(n^2). Hashing replaces the inner loop with a **lookup**: as you pass over the data once, store what you need
    in a dict or a set, and for each new element ask the table an O(1) question ("have I seen this?", "how many times?", "where was its complement?"). The result is O(n)
    time for O(n) extra memory, the trade behind most "optimise this" interview answers. The questions decide the structure: a **set** for presence, a **dict** from key to
    count, index, or list of items, `collections.Counter` for counts, `defaultdict(list)` for groups."""),
    ex("""
    from collections import Counter, defaultdict

    words = "the refund the policy refund window the".split()
    counts = Counter(words)
    print(counts.most_common(2), counts["missing"], sum(counts.values()))

    def two_sum(nums, target):
        seen = {}
        for i, x in enumerate(nums):
            if target - x in seen:
                return seen[target - x], i
            seen[x] = i
        return None

    print(two_sum([3, 8, 11, 4, 7], 15), two_sum([1, 2], 9))

    groups = defaultdict(list)
    for w in ["listen", "silent", "enlist", "google", "gogole", "cat"]:
        groups["".join(sorted(w))].append(w)
    print(list(groups.values()))
    """, "hash_basics.py"),
    p("""`two_sum` stores each value's index and, for every new value, looks up the **complement** it needs; one pass, O(n), instead of checking all pairs. Grouping uses a
    **canonical key**, a representation that is equal for items that belong together (the sorted letters of an anagram); the same trick normalises emails, case-folds
    titles or hashes document contents (12.1)."""),
)

section("windows", "Sliding windows",
    fig(table(["values", "3", "1", "4", "1", "5", "window sum"], [
        ["window 1", "in", "in", "in", "", "", "8"],
        ["window 2", "out", "in", "in", "in", "", "8 - 3 + 1 = 6"],
        ["window 3", "", "out", "in", "in", "in", "6 - 1 + 5 = 10"],
    ], hl={(1, 1), (2, 2)}, label="a sliding window of size 3"),
        "Each step adds the value that enters and subtracts the one that leaves, so the whole scan is O(n)."),
    p("""Many problems ask about **contiguous** ranges: the best sum of k consecutive values, the longest substring without repeated characters, the shortest span containing
    every keyword, requests in the last 60 seconds. Recomputing each window from scratch is O(n * k); a **sliding window** keeps a summary of the current range (a sum, a
    Counter, a set, a deque of timestamps) and updates it as one element enters at the right and, when needed, others leave at the left. Each element enters and leaves
    once, so the total is O(n). Fixed-size windows move both ends together; variable-size windows grow the right end and shrink the left end while a condition is
    violated (problems 5 and 13)."""),
)

section("prefix", "Prefix sums and hash maps",
    fig(table(["k", "0", "1", "2", "3", "4", "5"], [
        ["values[k]", "3", "1", "4", "1", "5", ""],
        ["prefix[k]", "0", "3", "4", "8", "9", "14"],
    ], hl={(1, 2), (1, 5)}, label="sum(values[2:5]) = prefix[5] - prefix[2] = 14 - 4 = 10"),
        "Prefix sums: one pass up front, then every range sum is a single subtraction."),
    p("""The sum of `values[i:j]` equals `prefix[j] - prefix[i]`, where `prefix[k]` is the sum of the first k values, so after one O(n) pass any range sum costs O(1). Combined with
    a dict this answers counting questions: the number of subarrays summing to k is the number of pairs of prefix sums that differ by k, so as you compute each prefix sum
    `p`, add how many earlier prefix sums equal `p - k` (problem 7). Seeding the dict with `{0: 1}`, the empty prefix, is what lets subarrays that start at index 0 count."""),
)

section("contract", "The hash and equality contract",
    p("""Dicts and sets rely on one rule: **objects that are equal must have equal hashes**. Python's built-ins follow it (so `1`, `1.0` and `True` are the same key), and
    `@dataclass(frozen=True)` generates matching `__eq__` and `__hash__` (11.3). A class that defines `__eq__` without `__hash__` becomes unhashable, which is the safe default;
    a hand-written `__hash__` that disagrees with `__eq__` makes "equal" objects land in different buckets, so sets keep duplicates and lookups miss. And a key must not
    **change** while it is in a table: mutating an object used as a key changes its hash, and the table can no longer find it, which is why lists and dicts are unhashable
    and tuples of immutable values are the standard composite key."""),
)

section("warmup", "Warm-up",
    predict("Counter and defaultdict", "easy",
        code="""
        from collections import Counter, defaultdict

        c = Counter("mississippi")
        print(c.most_common(3), c["z"], len(c))
        d = Counter(a=3, b=1)
        e = Counter(a=1, b=2, c=5)
        print(d + e, d - e, d & e, d | e)
        tags = defaultdict(list)
        for doc, tag in [("d1", "billing"), ("d2", "eu"), ("d1", "eu")]:
            tags[doc].append(tag)
        print(dict(tags), "d3" in tags, tags["d3"], "d3" in tags)
        """,
        hints=["`most_common` orders by count, keeping first-seen order for ties. Subtraction drops counts that are zero or negative. A `defaultdict` creates the default on read."],
        why="""`i` and `s` both appear four times and `i` was seen first, so it comes first; a missing key counts as 0 without being stored. Counter arithmetic is per key: `+` adds,
        `-` subtracts and drops results that are not positive, `&` takes minimums and `|` maximums. A `defaultdict` creates a value whenever a missing key is **read**, so merely
        looking at `tags["d3"]` adds an empty list, a common source of phantom keys; use `in` or `.get` to check without creating."""),
    write("Two sum, and all pairs", "easy", tag="Data work",
        prompt="""Write `two_sum(nums, target)` returning the indices `(i, j)` with `i < j` of the first pair (smallest `j`, then smallest `i`) whose values sum to `target`, or `None`, in
        O(n). Then write `count_pairs(nums, target)` returning how many index pairs `i < j` sum to `target`, also in O(n).""",
        code="""
        def two_sum(nums, target):
            pass

        def count_pairs(nums, target):
            pass
        """,
        tests="""
        assert two_sum([3, 8, 11, 4, 7], 15) == (2, 3) and two_sum([2, 7, 11, 15], 9) == (0, 1)
        assert two_sum([3, 3], 6) == (0, 1) and two_sum([1, 2, 3], 7) is None and two_sum([5, 1, 5], 10) == (0, 2)
        assert count_pairs([1, 5, 7, -1, 5], 6) == 3 and count_pairs([2, 2, 2, 2], 4) == 6 and count_pairs([], 1) == 0
        """,
        hints=["Store the **first** index of each value (`setdefault`), and check for the complement before storing the current value, so an element is not paired with itself.",
               "For counting, keep a `Counter` of values seen so far and add `seen[target - x]` at each step."],
        solution="""
        from collections import Counter


        def two_sum(nums, target):
            first = {}
            for j, x in enumerate(nums):
                if target - x in first:
                    return first[target - x], j
                first.setdefault(x, j)
            return None


        def count_pairs(nums, target):
            seen, total = Counter(), 0
            for x in nums:
                total += seen[target - x]
                seen[x] += 1
            return total
        """,
        why="""Checking the complement **before** inserting the current value is what keeps an element from pairing with itself (`[3]` with target 6) while still pairing two equal
        values at different positions (`[3, 3]`). Scanning left to right returns the pair with the smallest second index, and keeping the first index of each value makes the
        first index as small as possible. Counting pairs generalises the lookup: each new value pairs with every earlier occurrence of its complement, so four 2s give 0 + 1 +
        2 + 3 = 6 pairs, all in one pass instead of the O(n^2) double loop."""),
    fix("Grouping by an unhashable key", "easy", tag="Data work",
        prompt="""`group_anagrams` crashes with `TypeError: unhashable type: 'list'` because it uses `sorted(word)` (a list) as a dict key. Fix it with a hashable canonical key, and make
        grouping ignore case, keeping each group's words in input order and the groups in order of first appearance.""",
        code="""
        def group_anagrams(words):
            groups = {}
            for w in words:
                key = sorted(w)
                groups.setdefault(key, []).append(w)
            return list(groups.values())
        """,
        tests="""
        assert group_anagrams(["Listen", "silent", "enlist", "google", "gogole", "cat", "act"]) == [["Listen", "silent", "enlist"], ["google", "gogole"], ["cat", "act"]]
        assert group_anagrams([]) == [] and group_anagrams(["a", "A"]) == [["a", "A"]]
        """,
        hints=["`\"\".join(sorted(w.lower()))` (or `tuple(sorted(...))`) is hashable and equal for anagrams."],
        solution="""
        def group_anagrams(words):
            groups = {}
            for w in words:
                key = "".join(sorted(w.lower()))
                groups.setdefault(key, []).append(w)
            return list(groups.values())
        """,
        why="""Dict keys must be hashable, and lists are not, because they can change after insertion, which would break the table. A string or a tuple built from the sorted letters
        is immutable and equal for exactly the anagrams, so it works as the canonical key; lower-casing first makes the key ignore case while the stored words keep their
        original form. Sorting each word costs O(L log L), so the whole grouping is O(n L log L); a `Counter` of letters as a frozenset of items, or a 26-count tuple, gives
        O(n L) for long words."""),
    predict("A fixed-size sliding window", "easy",
        code="""
        def window_sums(values, k):
            if k > len(values):
                return []
            total = sum(values[:k])
            sums = [total]
            for i in range(k, len(values)):
                total += values[i] - values[i - k]
                sums.append(total)
            return sums

        latency = [120, 80, 300, 90, 110, 400, 70]
        sums = window_sums(latency, 3)
        print(sums, max(sums), sums.index(max(sums)))
        print(window_sums(latency, 1) == latency, window_sums(latency, 7), window_sums(latency, 8))
        """,
        hints=["Each step adds the element entering on the right and subtracts the one leaving on the left."],
        why="""The first window's sum is computed once; then each step adds the new element and subtracts the one that left, so all windows cost O(n) instead of O(n * k). The slowest
        stretch of three consecutive requests is the window starting at index 3, `90 + 110 + 400 = 600`, which `max` and `index` find. A window of 1 reproduces the data, a window of the full length has one
        sum, and a window longer than the data has none."""),
)

section("medium", "Medium",
    write("Longest substring without repeats", "medium", tag="Data work",
        prompt="""Write `longest_unique(s)` returning `(length, start)` of the longest substring with no repeated character (the leftmost one if several have the same length), in O(n),
        using a dict from character to its last index and a moving left edge.""",
        code="""
        def longest_unique(s):
            pass
        """,
        tests="""
        assert longest_unique("abcabcbb") == (3, 0) and longest_unique("bbbbb") == (1, 0) and longest_unique("pwwkew") == (3, 2)
        assert longest_unique("") == (0, 0) and longest_unique("abba") == (2, 0) and longest_unique("dvdf") == (3, 1)
        assert longest_unique("refund policy") == (13, 0) and longest_unique("tokens to tokenize") == (8, 9)
        """,
        hints=["When `ch` was last seen at an index `>= left`, move `left` to that index + 1; never move `left` backwards (the `abba` case).",
               "Update the best when `i - left + 1` is strictly greater than the current best length."],
        solution="""
        def longest_unique(s):
            last = {}
            left = best_len = best_start = 0
            for i, ch in enumerate(s):
                if ch in last and last[ch] >= left:
                    left = last[ch] + 1
                last[ch] = i
                if i - left + 1 > best_len:
                    best_len, best_start = i - left + 1, left
            return best_len, best_start
        """,
        why="""The window `[left, i]` always holds distinct characters: when the new character already occurs inside it, the left edge jumps just past that earlier occurrence, so
        each index is passed by both edges at most once, O(n). Storing the **last** index of each character lets the jump happen in O(1) instead of shrinking step by step.
        The `last[ch] >= left` test matters for `"abba"`: when the second `a` arrives, its earlier occurrence is already outside the window, and jumping back to it would grow
        the window wrongly. The same skeleton handles "longest run of tokens without a repeated n-gram" or "longest session without a duplicate event"."""),
    write("A sliding-window rate limiter", "medium", tag="GenAI",
        prompt="""Write a class `SlidingWindowLimiter(limit, window)` with `allow(user, t)` returning `True` if `user` has made fewer than `limit` allowed requests in the half-open
        interval `(t - window, t]` (and recording this one), else `False` (not recorded). Timestamps for each user arrive in non-decreasing order. Use a dict from user to a
        `deque` of timestamps, dropping old ones from the left.""",
        code="""
        from collections import defaultdict, deque

        class SlidingWindowLimiter:
            pass
        """,
        tests="""
        lim = SlidingWindowLimiter(limit=3, window=60)
        got = [lim.allow("ana", t) for t in (0, 10, 20, 30, 59, 60, 61)]
        assert got == [True, True, True, False, False, True, False]
        assert [lim.allow("bo", t) for t in (5, 5, 5, 5)] == [True, True, True, False]
        assert lim.allow("ana", 70) is True and lim.allow("ana", 71) is False and len(lim.history["ana"]) == 3
        """,
        hints=["On each call, pop timestamps `<= t - window` from the left of the user's deque; then allow if its length is below `limit`."],
        solution="""
        from collections import defaultdict, deque


        class SlidingWindowLimiter:
            def __init__(self, limit, window):
                self.limit, self.window = limit, window
                self.history = defaultdict(deque)

            def allow(self, user, t):
                q = self.history[user]
                while q and q[0] <= t - self.window:
                    q.popleft()
                if len(q) < self.limit:
                    q.append(t)
                    return True
                return False
        """,
        why="""A per-user deque is a sliding window over time: new requests enter on the right, and requests older than the window leave on the left, each exactly once, so every call is
        amortised O(1) and memory is bounded by `limit` per user. The half-open interval decides the boundary: at `t = 60`, the request from `t = 0` has just left the window, so
        a new one is allowed, but at `t = 61` the requests from 10, 20 and 60 are all still inside it, so the next one is refused. Rejected requests are not recorded, so a client hammering the API does not lock itself out for longer. This is the "sliding log" limiter; the
        token bucket of 14.2 uses O(1) memory per user at the cost of allowing bursts, and production systems keep such state in Redis to share it across servers."""),
    fix("Prefix sums that forget the empty prefix", "medium", tag="ML",
        prompt="""`count_subarrays(values, k)` should count contiguous subarrays summing to `k` in O(n) with prefix sums and a dict of how often each prefix sum occurred. It misses every
        subarray that starts at index 0. Fix it.""",
        code="""
        def count_subarrays(values, k):
            seen = {}
            prefix = total = 0
            for v in values:
                prefix += v
                total += seen.get(prefix - k, 0)
                seen[prefix] = seen.get(prefix, 0) + 1
            return total
        """,
        tests="""
        assert count_subarrays([1, 1, 1], 2) == 2
        assert count_subarrays([3, 4, 7, 2, -3, 1, 4, 2], 7) == 4
        assert count_subarrays([0, 0, 0], 0) == 6 and count_subarrays([], 3) == 0
        """,
        hints=["Before the loop, record that the empty prefix (sum 0) has been seen once: `seen = {0: 1}`."],
        solution="""
        def count_subarrays(values, k):
            seen = {0: 1}
            prefix = total = 0
            for v in values:
                prefix += v
                total += seen.get(prefix - k, 0)
                seen[prefix] = seen.get(prefix, 0) + 1
            return total
        """,
        why="""A subarray `values[i:j]` sums to `k` exactly when `prefix[j] - prefix[i] == k`, so at each position the number of good subarrays ending there is the number of earlier
        prefixes equal to `prefix - k`. The prefix before any element is 0, and subarrays starting at index 0 need it: without `{0: 1}`, `[3, 4]` (sum 7, starting at 0) was never
        counted. With negative numbers a sliding window does not work (sums are not monotonic), which is exactly when the prefix-sum dict is the tool. The zeros case shows it
        counts all six subarrays of `[0, 0, 0]`."""),
    choose("Counting words: a manual dict or Counter", "medium", tag="Data work",
        prompt="Both count 200,000 words. Which is faster?",
        setup="""import random
from collections import Counter
rng = random.Random(0)
vocab = [f"w{i}" for i in range(2_000)]
words = [rng.choice(vocab) for _ in range(200_000)]""",
        options={
            "a": "counts = {}\nfor w in words:\n    counts[w] = counts.get(w, 0) + 1",
            "b": "counts = Counter(words)",
        },
        answer="b",
        hints=["Where does each version's loop run?"],
        why="""Both are O(n), but `Counter(iterable)` counts with a helper implemented in C, so the per-word work avoids the interpreter's overhead of a Python loop, a method call
        (`get`) and a store. Complexity tells you how cost grows; constant factors decide how fast it is at a given size, and in Python, moving loops into built-ins
        (`Counter`, `sum`, `sorted`, `str.join`, `set` operations) is the main lever for those constants."""),
    trace("At most k distinct in a window", "medium",
        prompt="Fill in `best` after each marked line: the length of the longest substring with at most `k` distinct characters.",
        code="""
        from collections import Counter

        def longest_k_distinct(s, k):
            counts, left, best = Counter(), 0, 0
            for right, ch in enumerate(s):
                counts[ch] += 1
                while len(counts) > k:
                    counts[s[left]] -= 1
                    if counts[s[left]] == 0:
                        del counts[s[left]]
                    left += 1
                best = max(best, right - left + 1)
            return best

        best = longest_k_distinct("eceba", 2)  # row: "eceba, k=2"
        best = longest_k_distinct("aaabbbccc", 1)  # row: "runs, k=1"
        best = longest_k_distinct("aaabbbccc", 2)  # row: "runs, k=2"
        best = longest_k_distinct("abc", 0)  # row: "k=0"
        """,
        trace_vars=["best"],
        hints=["The window grows to the right and shrinks from the left while it holds more than k distinct characters; deleting zero counts keeps `len(counts)` honest."],
        why="""For `eceba` with two distinct letters, `ece` is the longest window. Runs of one letter give 3 for k=1, and two adjacent runs give 6 for k=2. With k=0, every character
        forces the window to shrink to empty, so the answer is 0. Deleting a key when its count reaches zero is essential: a `Counter` keeps zero entries otherwise, and
        `len(counts)` would overstate the number of distinct letters in the window."""),
    write("Near-duplicate documents with shingles", "medium", tag="RAG",
        prompt="""Write `shingles(text, n=3)` returning the set of word n-grams (tuples of `n` consecutive lower-cased words; a text with fewer words gives one tuple of all its words, or an
        empty set when empty), `jaccard(a, b)` (size of intersection over size of union, 0.0 if both empty), and `near_duplicates(docs, threshold=0.5, n=3)` returning sorted
        `(id1, id2, similarity)` pairs (id1 < id2, similarity rounded to 3) at or above the threshold. Avoid comparing every pair: build an inverted index from shingle to doc
        ids and compare only documents that share at least one shingle.""",
        code="""
        from collections import defaultdict
        from itertools import combinations

        def shingles(text, n=3):
            pass

        def jaccard(a, b):
            pass

        def near_duplicates(docs, threshold=0.5, n=3):
            pass
        """,
        tests="""
        docs = {
            "faq-1": "Refunds take five business days after we receive the item",
            "faq-2": "refunds take five business days after we receive your item",
            "faq-3": "Shipping is free for orders over fifty euros",
            "faq-4": "shipping is free for all orders over fifty euros",
            "faq-5": "Contact support",
        }
        assert shingles("A b c d") == {("a", "b", "c"), ("b", "c", "d")} and shingles("hi there") == {("hi", "there")} and shingles("") == set()
        assert jaccard({1, 2, 3}, {2, 3, 4}) == 0.5 and jaccard(set(), set()) == 0.0
        assert near_duplicates(docs, threshold=0.5) == [("faq-1", "faq-2", 0.6)]
        assert near_duplicates(docs, threshold=0.3) == [("faq-1", "faq-2", 0.6), ("faq-3", "faq-4", 0.444)]
        """,
        hints=["Inverted index: `for doc_id, sh in sets.items(): for s in sh: index[s].add(doc_id)`; candidate pairs come from `combinations(sorted(ids), 2)` for each shingle's ids.",
               "Collect candidate pairs in a set first, so each pair is scored once."],
        solution="""
        from collections import defaultdict
        from itertools import combinations


        def shingles(text, n=3):
            words = text.lower().split()
            if not words:
                return set()
            if len(words) < n:
                return {tuple(words)}
            return {tuple(words[i:i + n]) for i in range(len(words) - n + 1)}


        def jaccard(a, b):
            union = a | b
            return len(a & b) / len(union) if union else 0.0


        def near_duplicates(docs, threshold=0.5, n=3):
            sets = {doc_id: shingles(text, n) for doc_id, text in docs.items()}
            index = defaultdict(set)
            for doc_id, sh in sets.items():
                for s in sh:
                    index[s].add(doc_id)
            candidates = set()
            for ids in index.values():
                candidates.update(combinations(sorted(ids), 2))
            out = []
            for a, b in sorted(candidates):
                sim = jaccard(sets[a], sets[b])
                if sim >= threshold:
                    out.append((a, b, round(sim, 3)))
            return out
        """,
        why="""Near-duplicates (the same FAQ answer pasted twice with one word changed) waste index space and make retrieval return the same content several times. Word shingles turn
        each document into a set, and Jaccard similarity measures overlap. Comparing all pairs is O(n^2); an **inverted index** from shingle to documents means only documents
        that share at least one shingle are ever compared, which for real corpora is a tiny fraction of the pairs. At web scale, **MinHash** with locality-sensitive hashing
        replaces exact sets with short signatures, but the structure (hash features, index them, compare candidates) is the same."""),
    predict("Hashes, equality and keys", "medium",
        code="""
        from dataclasses import dataclass

        print(len({1, 1.0, True}), {1: "int", 1.0: "float", True: "bool"})

        class BadKey:
            def __init__(self, v):
                self.v = v
            def __eq__(self, other):
                return self.v == other.v
            def __hash__(self):
                return id(self)

        @dataclass(frozen=True)
        class GoodKey:
            v: str

        print(len({BadKey("a"), BadKey("a")}), len({GoodKey("a"), GoodKey("a")}))

        class NoHash:
            def __init__(self, v):
                self.v = v
            def __eq__(self, other):
                return self.v == other.v

        try:
            {NoHash(1)}
        except TypeError as e:
            print("TypeError:", e)
        key = [1, 2]
        try:
            {key: "x"}
        except TypeError as e:
            print("TypeError:", e)
        print({(1, 2): "tuple key"}[(1, 2)], hash((1, 2)) == hash((1, 2)))
        """,
        hints=["Equal objects must have equal hashes. `1 == 1.0 == True`. Defining `__eq__` without `__hash__` makes instances unhashable."],
        why="""`1`, `1.0` and `True` are equal and hash alike, so they are one key: the first insertion fixes the key object and later ones overwrite the value. `BadKey` breaks the
        contract (equal objects, different hashes), so the set keeps two "equal" members; the frozen dataclass generates a hash from its fields and dedupes correctly. A class
        that defines only `__eq__` gets `__hash__ = None` and cannot be used as a key at all, the safe default. Lists are unhashable because they are mutable, and tuples of
        hashable values are the standard composite key."""),
)

section("hard", "Hard",
    write("An LRU cache for completions", "hard", tag="GenAI",
        prompt="""Write `LRUCache(capacity)` with `get(key)` (the value, or `None`; a hit makes the key most recently used) and `put(key, value)` (insert or update, making it most recent; when
        over capacity, evict the **least** recently used), both O(1), using `collections.OrderedDict`. Track `hits`, `misses` and `evictions`.""",
        code="""
        from collections import OrderedDict

        class LRUCache:
            pass
        """,
        tests="""
        c = LRUCache(2)
        c.put("q1", "a1")
        c.put("q2", "a2")
        assert c.get("q1") == "a1"
        c.put("q3", "a3")
        assert c.get("q2") is None and c.get("q3") == "a3" and c.get("q1") == "a1"
        c.put("q1", "a1-new")
        c.put("q4", "a4")
        assert list(c.data) == ["q1", "q4"] and c.get("q1") == "a1-new"
        assert (c.hits, c.misses, c.evictions) == (4, 1, 2)
        try:
            LRUCache(0)
            assert False
        except ValueError:
            pass
        """,
        hints=["`OrderedDict.move_to_end(key)` marks a key as most recent; `popitem(last=False)` removes the oldest."],
        solution="""
        from collections import OrderedDict


        class LRUCache:
            def __init__(self, capacity):
                if capacity < 1:
                    raise ValueError("capacity must be at least 1")
                self.capacity = capacity
                self.data = OrderedDict()
                self.hits = self.misses = self.evictions = 0

            def get(self, key):
                if key not in self.data:
                    self.misses += 1
                    return None
                self.data.move_to_end(key)
                self.hits += 1
                return self.data[key]

            def put(self, key, value):
                if key in self.data:
                    self.data.move_to_end(key)
                self.data[key] = value
                if len(self.data) > self.capacity:
                    self.data.popitem(last=False)
                    self.evictions += 1
        """,
        why="""An LRU cache needs two O(1) operations: find a key, and know which key was used least recently. An `OrderedDict` provides both, a hash table for lookups plus a linked
        order that `move_to_end` updates in O(1), so the oldest entry is always at the front for `popitem(last=False)`. Caching LLM completions or embeddings by a hash of the
        prompt and parameters saves money on repeated questions, and the hit, miss and eviction counters tell you whether the capacity is right. `functools.lru_cache` is the
        decorator version (8.4); a hand-written class is needed when keys must be computed from arguments or the cache must be shared and inspected."""),
    write("Minimum window containing all keywords", "hard", tag="RAG",
        prompt="""Write `min_window(tokens, required)` returning `(start, end)` of the **shortest** contiguous slice `tokens[start:end]` that contains every token in the `required` list
        **with multiplicity** (a keyword listed twice must appear twice), the leftmost on ties, or `None`. Use a sliding window with a `Counter` of what is still missing, in
        O(n).""",
        code="""
        from collections import Counter

        def min_window(tokens, required):
            pass
        """,
        tests="""
        text = "the refund policy says a refund is issued within five days of the return".split()
        assert min_window(text, ["refund", "days"]) == (5, 11) and text[5:11] == ["refund", "is", "issued", "within", "five", "days"]
        assert min_window(text, ["refund", "refund"]) == (1, 6)
        assert min_window(text, ["refund", "warranty"]) is None and min_window(text, []) == (0, 0)
        assert min_window(list("ADOBECODEBANC"), list("ABC")) == (9, 13)
        """,
        hints=["Keep `need = Counter(required)` and `missing = len(required)`. Moving `right`: if `need[tok] > 0`, decrement `missing`; then decrement `need[tok]` (it may go negative for surplus).",
               "While `missing == 0`, record the window if shorter, then move `left`: increment `need[tokens[left]]`, and if it becomes positive, increment `missing`."],
        solution="""
        from collections import Counter


        def min_window(tokens, required):
            if not required:
                return (0, 0)
            need = Counter(required)
            missing = len(required)
            best = None
            left = 0
            for right, tok in enumerate(tokens):
                if need[tok] > 0:
                    missing -= 1
                need[tok] -= 1
                while missing == 0:
                    if best is None or right + 1 - left < best[1] - best[0]:
                        best = (left, right + 1)
                    need[tokens[left]] += 1
                    if need[tokens[left]] > 0:
                        missing += 1
                    left += 1
            return best
        """,
        why="""The window expands to the right until it contains everything required, then shrinks from the left as long as it still does, recording each valid window; every token enters
        and leaves once, so the whole search is O(n). The `need` counter goes negative for surplus tokens, which is what lets the window shrink past an extra `refund` without
        losing validity, and `missing` counts how many required tokens are still absent, so validity is checked in O(1) instead of comparing counters. In search and RAG this
        finds the tightest passage containing all query keywords, a good snippet to show or to feed a model."""),
    fix("Read the code: top-k frequent terms", "hard", tag="GenAI",
        prompt="""`top_terms(docs, k)` returns the `k` most frequent words across documents, ignoring a stop-word list, ties broken alphabetically. It counts by calling `list.count` for
        every distinct word (quadratic), keeps stop words in a list, breaks ties in reverse alphabetical order, and treats `Refund` and `refund` as different words. Fix it with a
        set of stop words, a `Counter`, lower-casing, and a sort key `(-count, word)`.""",
        code="""
        STOP = ["the", "a", "of", "to", "is", "and"]


        def top_terms(docs, k):
            words = []
            for doc in docs:
                for w in doc.split():
                    w = w.strip(".,!?")
                    if w not in STOP:
                        words.append(w)
            counts = [(words.count(w), w) for w in set(words)]
            counts.sort(reverse=True)
            return [w for _, w in counts[:k]]
        """,
        tests="""
        docs = ["The refund is processed.", "Refund and return the item!", "A return label is attached.", "Shipping of the item"]
        assert top_terms(docs, 3) == ["item", "refund", "return"]
        assert top_terms(docs, 1) == ["item"] and top_terms([], 2) == []
        big = ["alpha beta gamma " * 50] * 2_000
        assert top_terms(big, 2) == ["alpha", "beta"]
        """,
        hints=["`STOP = frozenset({...})`; `counts = Counter(w.strip(\".,!?\").lower() for doc in docs for w in doc.split())`, then drop stop words and empty strings.",
               "`sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:k]`."],
        solution="""
        from collections import Counter

        STOP = frozenset({"the", "a", "of", "to", "is", "and"})


        def top_terms(docs, k):
            counts = Counter()
            for doc in docs:
                for w in doc.split():
                    w = w.strip(".,!?").lower()
                    if w and w not in STOP:
                        counts[w] += 1
            ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
            return [w for w, _ in ranked[:k]]
        """,
        why="""`words.count(w)` scans the whole word list once per distinct word, O(n * u), which for the 300,000-word test is billions of steps; a `Counter` counts in one pass.
        Membership in a list of stop words is a scan too, a `frozenset` makes it O(1). Sorting tuples `(count, word)` in reverse also reverses the tie-break (`return` before
        `refund`); the key `(-count, word)` sorts counts descending and words ascending explicitly. And `Refund` versus `refund` split one term's count in two, so normalising
        case belongs before counting. For a huge vocabulary with a small `k`, `heapq.nsmallest(k, counts.items(), key=...)` avoids sorting everything."""),
    predict("Grouping and counting idioms", "hard",
        code="""
        from collections import Counter, defaultdict
        from itertools import groupby

        events = [("ana", "login"), ("bo", "ask"), ("ana", "ask"), ("ana", "ask"), ("bo", "logout")]
        by_user = defaultdict(Counter)
        for user, action in events:
            by_user[user][action] += 1
        print({u: dict(c) for u, c in by_user.items()})
        print([(k, len(list(g))) for k, g in groupby(events, key=lambda e: e[0])])
        print([(k, len(list(g))) for k, g in groupby(sorted(events), key=lambda e: e[0])])
        totals = Counter(action for _, action in events)
        print(totals.most_common(), totals.total(), sorted(totals.elements())[:3])
        first_seen = {}
        for i, (user, _) in enumerate(events):
            first_seen.setdefault(user, i)
        print(first_seen)
        """,
        hints=["`groupby` groups **consecutive** equal keys only, so unsorted input gives repeated groups. `setdefault` only sets a key the first time."],
        why="""A `defaultdict(Counter)` builds a nested count per user in one pass. `itertools.groupby` is not a hash-based group-by: it groups **runs** of equal keys, so on unsorted
        events `ana` appears twice; sorting first (O(n log n)) or using a dict (O(n)) gives one group per user. `Counter.total()` sums the counts and `elements()` repeats each key
        by its count. `setdefault` records the first index for each user and ignores later ones, the hash-based way to remember first occurrences."""),
)

section("interview", "Interview questions",
    explain("When would you reach for a hash map in an interview problem, and what does it cost?", "medium", tag="Interview",
        why="""Whenever the brute-force solution has an inner loop that **searches** for something: a complement (two-sum), a previous occurrence (first repeat, longest substring without
        repeats), a count (frequencies, anagrams, majority element), a group (group by canonical key), or a previous state (prefix sums for subarray sums, visited states in a
        search). Replacing that search with an O(1) average dict or set lookup usually turns O(n^2) into O(n). The costs: O(n) extra memory, keys must be hashable and must
        follow the hash and equality contract, iteration order is insertion order (dicts) or arbitrary (sets), and the worst case degrades with many collisions. If the data
        is sorted or can be sorted, two pointers or binary search (16.3) may give the same speed with O(1) extra memory; mention the trade-off."""),
    explain("Explain the sliding window technique and when it applies.", "medium", tag="Interview",
        why="""A sliding window maintains a summary of a contiguous range `[left, right]` of a sequence and updates it incrementally: extend `right` one element at a time, and move `left`
        forward when the window becomes invalid (variable-size windows) or to keep a fixed size, updating the summary (a sum, a `Counter`, a set, a deque) by adding the entering
        element and removing the leaving one. Each element enters and leaves once, so the total is O(n) instead of O(n * k) or O(n^2). It applies to problems about **contiguous**
        subarrays or substrings where validity changes monotonically as the window grows or shrinks: longest substring with at most k distinct characters, smallest window
        containing all keywords, maximum sum of k consecutive values, rate limits over the last T seconds, moving averages of metrics. It does **not** apply when validity is not
        monotonic, for example subarray sums with negative numbers, where prefix sums with a hash map are used instead."""),
    explain("How would you deduplicate a corpus of 50 million documents, including near-duplicates?", "hard", tag="Interview",
        why="""In two stages. **Exact duplicates**: normalise each document (Unicode normalisation, whitespace, case where appropriate, boilerplate removal), hash it (SHA-256 or a 64-bit hash
        such as xxHash), and keep one document per hash; this is a streaming, hash-set operation, partitioned by hash prefix across workers if it does not fit on one machine.
        **Near duplicates**: represent each document by its set of shingles (word or character n-grams), compute a **MinHash** signature (say 128 hashes), whose agreement rate
        estimates Jaccard similarity, and use **locality-sensitive hashing** (split signatures into bands; documents sharing a band bucket become candidates), so only candidate
        pairs are compared instead of all pairs; then confirm candidates above a threshold and cluster them with union-find, keeping one representative per cluster (by quality
        or recency). Tools such as `datasketch` or distributed implementations in Spark do this at scale. Embedding-based similarity catches paraphrases too, at a higher cost
        (approximate nearest-neighbour search). Report how many documents each stage removed, and spot-check samples, because thresholds trade lost content against redundancy."""),
)

recap(
    "Replace an inner search loop with a dict or set lookup: counting, complements, groups and seen-before checks become O(n) for O(n) memory.",
    "Group with a canonical, hashable key (sorted letters, normalised text, a content hash); use tuples or frozen dataclasses as composite keys.",
    "Sliding windows update a running summary as elements enter and leave, O(n) for contiguous-range questions when validity is monotonic.",
    "Prefix sums plus a dict count subarrays with a given sum, including negative values; seed with `{0: 1}`.",
    "Respect the contract: equal keys must hash equally and must not change while stored; `OrderedDict` gives O(1) LRU caches.",
)
