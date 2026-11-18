from lesson import *

lesson(
    id="m16-5", num="16.5", title="Dynamic programming",
    intro="Dynamic programming solves problems whose answer is built from answers to smaller, overlapping versions of the same problem. "
          "Recognising it, memoization with `functools.cache`, bottom-up tables, reconstructing the solution, and the classics that "
          "interviews and ML code actually use: coin change, longest common subsequence, edit distance (the metric behind word error "
          "rate), knapsack (choosing context chunks under a token budget), longest increasing subsequence and segmentation.",
    desc="Memoization, tabulation and edit distance.",
    keys="dynamic programming dp memoization functools cache lru_cache tabulation bottom-up subproblem recurrence state transition base case coin change longest common subsequence edit distance levenshtein word error rate knapsack longest increasing subsequence kadane word break backtrack",
)

term("Dynamic programming", "Solving a problem by combining the solutions of smaller overlapping subproblems, computing each subproblem once and reusing it.")
term("Memoization", "Caching a function's results by its arguments, so repeated calls with the same arguments return instantly.")
term("Recurrence", "An equation that defines the answer for a state in terms of answers for smaller states, plus base cases that stop it.")

section("idea", "Overlapping subproblems",
    p("""Some recursive solutions call themselves with the **same arguments many times**. The naive Fibonacci `fib(n) = fib(n - 1) + fib(n - 2)` recomputes `fib(n - 2)` from both
    branches, and the number of calls grows exponentially, about 1.6^n. Dynamic programming applies when a problem has **optimal substructure** (the answer for a state is built
    from answers for smaller states) and **overlapping subproblems** (the same smaller states recur). Then each distinct state is computed **once**: the cost becomes the number
    of states times the work per state, often turning O(2^n) into O(n) or O(n^2)."""),
    p("""Every DP solution answers four questions: what is the **state** (the arguments that identify a subproblem: an index, a remaining budget, two prefix lengths), what is the
    **recurrence** (how a state's answer follows from smaller states), what are the **base cases**, and in what **order** states are computed (top-down with a cache, or
    bottom-up in a table). Writing them down before coding is most of the work, in interviews and in practice."""),
)

section("memo", "Top-down: memoization",
    p("""The quickest way from a correct recursive solution to an efficient one is a cache: **`@functools.cache`** (or `@functools.lru_cache(maxsize=None)`) stores each call's result by
    its arguments, which must therefore be hashable (tuples, not lists; problem 3). The code stays close to the recurrence, and only states that are actually reached are
    computed. The costs are Python's recursion limit (about 1,000 frames by default; deep recursion can also crash browser-based Python such as this site's) and function-call
    overhead. `cache_info()` reports hits and misses, and `cache_clear()` empties the cache, which matters when the function depends on data that can change."""),
    ex("""
    from functools import cache

    calls = {"naive": 0}

    def fib_naive(n):
        calls["naive"] += 1
        return n if n < 2 else fib_naive(n - 1) + fib_naive(n - 2)

    @cache
    def fib(n):
        return n if n < 2 else fib(n - 1) + fib(n - 2)

    print(fib_naive(20), calls["naive"])
    print(fib(20), fib.cache_info())
    print(fib(60), fib.cache_info().misses)
    """, "memo.py"),
)

section("table", "Bottom-up: tabulation",
    p("""Bottom-up DP fills a table from the base cases upwards in an order where every state's dependencies are already computed, with plain loops: no recursion limit, no call
    overhead, and often a chance to keep only the last row or two (O(n) memory instead of O(n^2)). Two-sequence problems use a table `dp[i][j]` for the first `i` items of one
    sequence and the first `j` of the other, with an extra row and column for the empty prefixes; most off-by-one errors come from forgetting those (problem 7). To return the
    **solution** and not just its value (which coins, which chunks, which edits), either store choices in the table or walk backwards from the final cell, checking which
    recurrence branch produced each value (problems 9 and 13)."""),
    ex("""
    def edit_distance(a, b):
        prev = list(range(len(b) + 1))
        for i in range(1, len(a) + 1):
            cur = [i] + [0] * len(b)
            for j in range(1, len(b) + 1):
                cost = 0 if a[i - 1] == b[j - 1] else 1
                cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
            prev = cur
        return prev[-1]

    print(edit_distance("kitten", "sitting"), edit_distance("refund", "refunds"), edit_distance("", "abc"), edit_distance("same", "same"))
    ref = "refunds take five business days".split()
    hyp = "refund takes five days".split()
    print(edit_distance(ref, hyp), round(edit_distance(ref, hyp) / len(ref), 2))
    """, "edit_distance.py"),
    p("""Edit distance counts the minimum insertions, deletions and substitutions turning one sequence into another; each cell takes the cheapest of deleting, inserting, or
    substituting (free when the items match), and keeping only the previous row makes memory O(len(b)). Applied to **words**, it is the numerator of **word error rate**, the
    standard metric for speech recognition and a useful one for comparing generated text with a reference: here 3 errors over 5 reference words."""),
)

section("classics", "The classics and where they appear",
    p("""**Coin change** (fewest coins, or number of ways, for an amount) is the template for "combine items to reach a total". **Longest common subsequence** underlies `diff`,
    sequence alignment and ROUGE-L for summarisation. **Edit distance** gives fuzzy matching, typo correction and WER. **0/1 knapsack** chooses items with weights and values
    under a capacity: choosing retrieved chunks to maximise relevance within a token budget is exactly this (problem 9), O(n * capacity). **Longest increasing subsequence** has
    an O(n log n) solution with `bisect` (problem 11). **Kadane's algorithm** finds the best contiguous sum in O(n) by deciding at each step whether to extend the current run or
    start over. **Word break** segments text with a dictionary, related to how tokenizers split words into subwords (problem 12)."""),
)

section("warmup", "Warm-up",
    predict("What memoization saves", "easy",
        code="""
        from functools import cache

        count = {"plain": 0, "memo": 0}

        def ways_plain(n):
            count["plain"] += 1
            if n < 0:
                return 0
            if n == 0:
                return 1
            return ways_plain(n - 1) + ways_plain(n - 2) + ways_plain(n - 3)

        @cache
        def ways_memo(n):
            count["memo"] += 1
            if n < 0:
                return 0
            if n == 0:
                return 1
            return ways_memo(n - 1) + ways_memo(n - 2) + ways_memo(n - 3)

        print(ways_plain(15), count["plain"])
        print(ways_memo(15), count["memo"], ways_memo.cache_info().hits)
        print(ways_memo(16), count["memo"])
        """,
        hints=["The memoised function's body runs once per distinct argument; every other call is a cache hit."],
        why="""Counting the ways to climb 15 stairs taking 1, 2 or 3 steps at a time gives 5,768, and the plain recursion makes tens of thousands of calls because it solves the same
        smaller staircases over and over. With `@cache`, the body runs once for each distinct `n` reached (from -2 to 15, so 18 times: `n == 0` returns without recursing, so -3 is never
        asked for), and every repeated call is a hit. Asking
        for 16 afterwards runs the body only once more, because every smaller answer is already cached."""),
    write("Count step combinations bottom-up", "easy", tag="Data work",
        prompt="""Write `count_ways(n, steps)` returning how many ordered sequences of step sizes from `steps` (positive integers) sum exactly to `n`, bottom-up in O(n * len(steps)) with a list
        `ways` where `ways[0] = 1`. For example `count_ways(4, (1, 2))` is 5.""",
        code="""
        def count_ways(n, steps):
            pass
        """,
        tests="""
        assert [count_ways(n, (1, 2)) for n in range(7)] == [1, 1, 2, 3, 5, 8, 13]
        assert count_ways(15, (1, 2, 3)) == 5768 and count_ways(7, (2, 4)) == 0 and count_ways(0, (5,)) == 1
        assert count_ways(500, (1, 2)) == count_ways(499, (1, 2)) + count_ways(498, (1, 2))
        """,
        hints=["`ways[i] = sum(ways[i - s] for s in steps if s <= i)`."],
        solution="""
        def count_ways(n, steps):
            ways = [0] * (n + 1)
            ways[0] = 1
            for i in range(1, n + 1):
                ways[i] = sum(ways[i - s] for s in steps if s <= i)
            return ways[n]
        """,
        why="""The state is the remaining height `i`, and the recurrence follows from the last step taken: any sequence reaching `i` ends with some step `s`, after a sequence reaching
        `i - s`. With `ways[0] = 1` (the empty sequence) as the base case and the table filled from small to large, every needed value is ready when used, so there is no
        recursion and `n = 500` is instant despite the astronomically large answer (Python integers grow as needed). With steps 1 and 2 this is the Fibonacci sequence."""),
    fix("A memoised function with a list argument", "easy", tag="ML",
        prompt="""`best_split(costs)` is memoised with `@cache` but called with lists, so it raises `TypeError: unhashable type: 'list'`. Fix it so the cache works (convert to a tuple at
        the boundary, keep the public function accepting lists) and the recursion stays memoised.""",
        code="""
        from functools import cache

        @cache
        def best_split(costs):
            # minimal total cost of grouping consecutive items, where a group of k items costs max(group) * k
            if not costs:
                return 0
            best = None
            for k in range(1, len(costs) + 1):
                candidate = max(costs[:k]) * k + best_split(costs[k:])
                if best is None or candidate < best:
                    best = candidate
            return best
        """,
        tests="""
        assert best_split([4, 1, 1, 4]) == 10 and best_split([]) == 0 and best_split([5]) == 5
        assert best_split([3, 3, 3]) == 9 and best_split([1, 9, 1]) == 11
        assert best_split(list(range(1, 25))) == sum(range(1, 25))
        """,
        hints=["A private `@cache` helper `_best(costs)` takes a tuple; `best_split(costs)` calls `_best(tuple(costs))`. Slicing a tuple gives a tuple."],
        solution="""
        from functools import cache

        @cache
        def _best(costs):
            if not costs:
                return 0
            best = None
            for k in range(1, len(costs) + 1):
                candidate = max(costs[:k]) * k + _best(costs[k:])
                if best is None or candidate < best:
                    best = candidate
            return best

        def best_split(costs):
            return _best(tuple(costs))
        """,
        why="""The cache stores results in a dict keyed by the arguments, so every argument must be hashable; a list is not, because it could change after being used as a key. Converting
        to a tuple once, at the public boundary, keeps callers free to pass lists while the memoised helper works on immutable tuples whose slices are tuples too. Even better
        for long inputs is to make the **state** an index (`_best(i)` for the suffix starting at `i`), which avoids building and hashing slices: O(n) states instead of slices of
        every length. Choosing a small, hashable state is half of designing a DP."""),
    predict("Kadane's maximum subarray", "easy",
        code="""
        def max_subarray(values):
            best = cur = values[0]
            start = best_start = best_end = 0
            for i in range(1, len(values)):
                if cur + values[i] < values[i]:
                    cur, start = values[i], i
                else:
                    cur += values[i]
                if cur > best:
                    best, best_start, best_end = cur, start, i
            return best, values[best_start:best_end + 1]

        daily_gain = [3, -5, 4, -1, 2, 1, -6, 5]
        print(max_subarray(daily_gain))
        print(max_subarray([-3, -1, -4]), max_subarray([2, 3, -1, 4]))
        """,
        hints=["At each element: either extend the current run or start a new one there, whichever is larger; remember the best run seen."],
        why="""Kadane's algorithm is DP with a one-number state: the best sum of a run **ending at** the current position, which is either the element alone or the element added to the
        best run ending just before. The overall best is the maximum of those, found in one O(n) pass: `[4, -1, 2, 1]` sums to 6 here. With only negative values the answer is
        the largest single value, and when every prefix helps, the whole array wins (8)."""),
)

section("medium", "Medium",
    write("Coin change: fewest coins and number of ways", "medium", tag="Data work",
        prompt="""Write `min_coins(coins, amount)` returning `(count, combination)` with the fewest coins summing to `amount` (combination sorted descending, any optimal one), or `None` if
        impossible, and `count_combinations(coins, amount)` returning the number of **unordered** combinations (so `1+2` and `2+1` count once). Both bottom-up, O(amount * len(coins)).""",
        code="""
        def min_coins(coins, amount):
            pass

        def count_combinations(coins, amount):
            pass
        """,
        tests="""
        assert min_coins([1, 2, 5], 11) == (3, [5, 5, 1]) and min_coins([2], 3) is None and min_coins([1], 0) == (0, [])
        count, combo = min_coins([1, 3, 4], 6)
        assert count == 2 and sorted(combo) == [3, 3]
        assert count_combinations([1, 2, 5], 5) == 4 and count_combinations([2], 3) == 0 and count_combinations([1, 2, 3], 4) == 4
        assert count_combinations([1, 5, 10, 25], 100) == 242
        """,
        hints=["`best[a]` = fewest coins for amount `a` (infinity if impossible) and `last[a]` = the coin used last; rebuild the combination by following `last`.",
               "For unordered combinations, loop over coins **outside** and amounts inside: `ways[a] += ways[a - c]`."],
        solution="""
        def min_coins(coins, amount):
            INF = float("inf")
            best = [0] + [INF] * amount
            last = [None] * (amount + 1)
            for a in range(1, amount + 1):
                for c in coins:
                    if c <= a and best[a - c] + 1 < best[a]:
                        best[a], last[a] = best[a - c] + 1, c
            if best[amount] == INF:
                return None
            combo, a = [], amount
            while a:
                combo.append(last[a])
                a -= last[a]
            return best[amount], sorted(combo, reverse=True)


        def count_combinations(coins, amount):
            ways = [1] + [0] * amount
            for c in coins:
                for a in range(c, amount + 1):
                    ways[a] += ways[a - c]
            return ways[amount]
        """,
        why="""The state is the remaining amount. For the fewest coins, the recurrence tries every coin as the last one: `best[a] = 1 + min(best[a - c])`, and storing which coin achieved
        the minimum lets you rebuild the combination by walking back from `amount`. Greedy "take the largest coin" fails for coins `[1, 3, 4]` and amount 6 (4 + 1 + 1 instead of
        3 + 3), which is the classic reason to reach for DP. For counting, the loop order decides what is counted: coins outside means each coin's uses are added before the next
        coin is considered, so every combination is built in one canonical order and counted once (242 ways to make a dollar from US coins); amounts outside would count
        orderings, as in problem 2."""),
    write("Word error rate", "medium", tag="GenAI",
        prompt="""Write `edit_distance(a, b)` for any two sequences (strings or lists of words) with unit costs, using two rows of memory, and `word_error_rate(reference, hypothesis)` returning
        the word-level edit distance divided by the number of reference words, rounded to 3, after lower-casing and stripping `.,!?` from words; an empty reference gives 0.0 if the
        hypothesis is empty too, else 1.0.""",
        code="""
        def edit_distance(a, b):
            pass

        def word_error_rate(reference, hypothesis):
            pass
        """,
        tests="""
        assert edit_distance("kitten", "sitting") == 3 and edit_distance("", "abc") == 3 and edit_distance("abc", "abc") == 0
        assert edit_distance(["a", "b", "c"], ["a", "c"]) == 1 and edit_distance("flaw", "lawn") == 2
        assert word_error_rate("Refunds take five business days.", "refund takes five days") == 0.6
        assert word_error_rate("Hello there!", "hello there") == 0.0 and word_error_rate("", "") == 0.0 and word_error_rate("", "x") == 1.0
        assert word_error_rate("a b", "a b c d") == 1.0
        """,
        hints=["Row `prev` holds distances from the first `i - 1` items of `a` to every prefix of `b`; `cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i-1] != b[j-1]))`."],
        solution="""
        def edit_distance(a, b):
            prev = list(range(len(b) + 1))
            for i in range(1, len(a) + 1):
                cur = [i] + [0] * len(b)
                for j in range(1, len(b) + 1):
                    cost = 0 if a[i - 1] == b[j - 1] else 1
                    cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
                prev = cur
            return prev[-1]


        def _words(text):
            return [w.strip(".,!?").lower() for w in text.split() if w.strip(".,!?")]


        def word_error_rate(reference, hypothesis):
            ref, hyp = _words(reference), _words(hypothesis)
            if not ref:
                return 0.0 if not hyp else 1.0
            return round(edit_distance(ref, hyp) / len(ref), 3)
        """,
        why="""Edit distance's state is a pair of prefix lengths; the last items either match (free), or one is substituted, deleted or inserted (cost 1), and the table's first row and column
        are the costs of building a prefix from nothing. Only the previous row is needed for the next, so memory is O(len(b)) while time stays O(len(a) * len(b)). Because the
        function works on any sequences, the same code gives character edits (typo correction, fuzzy matching of entity names) and word edits: word error rate, the main metric
        for speech recognition and a robust way to compare transcripts or extracted text. WER can exceed 1 when the hypothesis has many insertions, so it is not a percentage."""),
    fix("An LCS table without the empty prefixes", "medium", tag="RAG",
        prompt="""`lcs_length(a, b)` should return the length of the longest common subsequence of two token lists (the core of ROUGE-L for summaries), but its table has no row and column
        for empty prefixes: it indexes `dp[i - 1]` with `i = 0`, silently reading the **last** row, and it crashes on empty input. Fix it with an `(len(a) + 1) x (len(b) + 1)`
        table.""",
        code="""
        def lcs_length(a, b):
            dp = [[0] * len(b) for _ in range(len(a))]
            for i in range(len(a)):
                for j in range(len(b)):
                    if a[i] == b[j]:
                        dp[i][j] = dp[i - 1][j - 1] + 1
                    else:
                        dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
            return dp[-1][-1]
        """,
        tests="""
        assert lcs_length(list("ABCBDAB"), list("BDCABA")) == 4
        assert lcs_length("the cat sat on the mat".split(), "the cat lay on a mat".split()) == 4
        assert lcs_length([], ["a"]) == 0 and lcs_length(["x"], ["x"]) == 1 and lcs_length(list("abc"), list("def")) == 0
        assert lcs_length(list("aab"), list("ab")) == 2
        """,
        hints=["`dp = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]`, loop `i` from 1 to `len(a)` and `j` from 1 to `len(b)`, comparing `a[i - 1]` with `b[j - 1]`."],
        solution="""
        def lcs_length(a, b):
            dp = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
            for i in range(1, len(a) + 1):
                for j in range(1, len(b) + 1):
                    if a[i - 1] == b[j - 1]:
                        dp[i][j] = dp[i - 1][j - 1] + 1
                    else:
                        dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
            return dp[-1][-1]
        """,
        why="""`dp[i][j]` should mean "the LCS of the first `i` items of `a` and the first `j` of `b`", which needs `i` and `j` to range from 0 (empty prefix, LCS 0) upwards. Without that row
        and column, the base case was missing, and Python's negative indexing turned `dp[-1]` into the last row of the table, garbage that happens to be 0 at the start, which is
        why the bug can pass small tests. The padded table makes the base cases explicit and the indices honest. ROUGE-L divides the LCS length by the reference and candidate
        lengths to score how much of a reference summary's word order a generated summary preserves."""),
    choose("Naive recursion or memoization", "medium", tag="ML",
        prompt="Both compute the 25th Fibonacci number. Which is faster?",
        setup="""from functools import cache

def fib_naive(n):
    return n if n < 2 else fib_naive(n - 1) + fib_naive(n - 2)

def fib_memo(n):
    @cache
    def f(k):
        return k if k < 2 else f(k - 1) + f(k - 2)
    return f(n)""",
        options={
            "a": "fib_naive(25)",
            "b": "fib_memo(25)",
        },
        answer="b",
        hints=["How many calls does each make? The memoised version builds a fresh cache on each run, so it is not cheating."],
        why="""The naive recursion makes about 250,000 calls because it recomputes the same subproblems exponentially often; the memoised one computes each of the 26 states once, so it does
        a few dozen calls even with a fresh cache per run. This is the whole idea of dynamic programming in one measurement: same recurrence, exponential versus linear work."""),
    trace("Filling a coin-change table", "medium",
        prompt="Fill in `ways` after each marked line: the number of combinations for amounts 0 to 6 after adding each coin.",
        code="""
        amount = 6
        ways = [1] + [0] * amount
        for coin in (1,):
            for a in range(coin, amount + 1):
                ways[a] += ways[a - coin]
        ways = list(ways)  # row: "after coin 1"
        for coin in (2,):
            for a in range(coin, amount + 1):
                ways[a] += ways[a - coin]
        ways = list(ways)  # row: "after coin 2"
        for coin in (5,):
            for a in range(coin, amount + 1):
                ways[a] += ways[a - coin]
        ways = list(ways)  # row: "after coin 5"
        """,
        trace_vars=["ways"],
        hints=["With only coin 1 there is one way to make every amount. Adding coin 2: `ways[a] += ways[a - 2]`, left to right."],
        why="""Each coin updates the table in increasing order of amount, so `ways[a - coin]` already includes combinations that use the current coin, which allows it to be used any number of
        times. With 1s only, every amount has one way. Adding 2s gives `[1, 1, 2, 2, 3, 3, 4]` (for 6: six 1s, one 2, two 2s, three 2s). Adding a 5 changes only amounts 5 and 6, each
        by one new combination (`5`, and `5 + 1`)."""),
    write("Choose chunks under a token budget", "medium", tag="RAG",
        prompt="""Write `select_chunks(chunks, budget)` where each chunk is `(tokens, relevance)`. Choose a subset with total tokens `<= budget` maximising total relevance (0/1 knapsack, O(n *
        budget)), and return `(total_relevance rounded to 3, sorted list of chosen indices)`. When several subsets tie, any optimal one is acceptable but the tests check the
        totals.""",
        code="""
        def select_chunks(chunks, budget):
            pass
        """,
        tests="""
        chunks = [(500, 0.9), (300, 0.6), (300, 0.55), (200, 0.3), (700, 1.2)]
        total, chosen = select_chunks(chunks, 1000)
        assert total == 1.8 and sum(chunks[i][0] for i in chosen) <= 1000 and round(sum(chunks[i][1] for i in chosen), 3) == total
        total, chosen = select_chunks(chunks, 800)
        assert total == 1.5 and chosen == [0, 1]
        assert select_chunks(chunks, 100) == (0.0, []) and select_chunks([], 500) == (0.0, [])
        """,
        hints=["Table `best[i][w]`: best relevance using the first `i` chunks within `w` tokens; either skip chunk `i - 1` or take it if it fits.",
               "Walk back from `best[n][budget]`: if the value differs from `best[i - 1][w]`, chunk `i - 1` was taken; subtract its tokens."],
        solution="""
        def select_chunks(chunks, budget):
            n = len(chunks)
            best = [[0.0] * (budget + 1) for _ in range(n + 1)]
            for i in range(1, n + 1):
                tokens, value = chunks[i - 1]
                for w in range(budget + 1):
                    best[i][w] = best[i - 1][w]
                    if tokens <= w and best[i - 1][w - tokens] + value > best[i][w]:
                        best[i][w] = best[i - 1][w - tokens] + value
            chosen, w = [], budget
            for i in range(n, 0, -1):
                if best[i][w] != best[i - 1][w]:
                    chosen.append(i - 1)
                    w -= chunks[i - 1][0]
            return round(best[n][budget], 3), sorted(chosen)
        """,
        why="""Packing context is a knapsack: each chunk has a weight (its tokens) and a value (its relevance), and the budget is the capacity. Greedy by relevance per token is not optimal (with
        1,000 tokens it might take the 700-token chunk and waste the rest); the DP considers every chunk in or out for every remaining budget, O(n * budget) time, and the table
        lets you walk back to the chosen set. Real systems round token counts to coarser units (multiples of 10 or 50) to shrink the table, and often add constraints such as
        "at most two chunks per document", which become extra state dimensions."""),
    predict("Longest increasing subsequence with bisect", "medium",
        code="""
        from bisect import bisect_left

        def lis(values):
            tails, idx, prev = [], [], [None] * len(values)
            for i, v in enumerate(values):
                k = bisect_left(tails, v)
                if k == len(tails):
                    tails.append(v)
                    idx.append(i)
                else:
                    tails[k] = v
                    idx[k] = i
                prev[i] = idx[k - 1] if k else None
            out, i = [], idx[-1] if idx else None
            while i is not None:
                out.append(values[i])
                i = prev[i]
            return len(tails), tails, out[::-1]

        print(lis([10, 9, 2, 5, 3, 7, 101, 18]))
        print(lis([3, 3, 3]), lis([]), lis([1, 2, 3, 4]))
        """,
        hints=["`tails[k]` is the smallest possible last value of an increasing subsequence of length `k + 1` seen so far; each value replaces the first tail that is not smaller."],
        why="""The patience-sorting idea keeps, for each length, the smallest tail an increasing subsequence of that length can have; a new value extends the longest one if it is larger than
        every tail, or improves (lowers) the first tail it does not exceed, found with `bisect_left` in O(log n), so the whole algorithm is O(n log n) instead of the O(n^2) table.
        `tails` is not in general a real subsequence of the input (here it happens to be one); following the `prev` links from the last tail's index always rebuilds a real
        one, `[2, 3, 7, 18]`. With
        `bisect_left`, equal values do not extend the sequence (strictly increasing), so `[3, 3, 3]` gives length 1."""),
)

section("hard", "Hard",
    write("Segment text with a vocabulary", "hard", tag="GenAI",
        prompt="""Write `segment(text, vocab)` splitting a string without spaces into vocabulary words using the **fewest** words, returning the list of words or `None` if impossible, bottom-up
        over end positions in O(n * L) where `L` is the longest vocabulary word. Ties go to the segmentation whose first differing word is longer.""",
        code="""
        def segment(text, vocab):
            pass
        """,
        tests="""
        vocab = {"re", "fund", "refund", "s", "policy", "pol", "icy", "un", "fun", "fund", "funds"}
        assert segment("refundspolicy", vocab) == ["refund", "s", "policy"] or segment("refundspolicy", vocab) == ["re", "funds", "policy"]
        assert len(segment("refundspolicy", vocab)) == 3
        assert segment("refundpolicy", vocab) == ["refund", "policy"] and segment("policies", vocab) is None and segment("", vocab) == []
        tok = {"un", "believ", "able", "unbeliev", "a", "ble"}
        assert segment("unbelievable", tok) == ["unbeliev", "able"]
        """,
        hints=["`best[i]` = fewest words for `text[:i]` (`best[0] = 0`); for each `i`, try every word length `k <= L` with `text[i - k:i]` in the vocabulary.",
               "Store the start of the last word in `back[i]`, then walk back from `len(text)`."],
        solution="""
        def segment(text, vocab):
            n = len(text)
            longest = max((len(w) for w in vocab), default=0)
            INF = float("inf")
            best = [0] + [INF] * n
            back = [None] * (n + 1)
            for i in range(1, n + 1):
                for k in range(min(longest, i), 0, -1):
                    j = i - k
                    if best[j] + 1 < best[i] and text[j:i] in vocab:
                        best[i], back[i] = best[j] + 1, j
            if best[n] == INF:
                return None
            words, i = [], n
            while i:
                words.append(text[back[i]:i])
                i = back[i]
            return words[::-1]
        """,
        why="""The state is a prefix length; `text[:i]` can be segmented if some vocabulary word ends at `i` and the text before it can be segmented, and taking the minimum over those words
        gives the fewest pieces. Limiting candidates to the longest vocabulary word keeps the work O(n * L) with O(1) set lookups, and `back` records where each best last word
        starts, so the segmentation is rebuilt by walking backwards. Subword tokenizers face the same question of how to split a word into known pieces; WordPiece takes the
        longest match greedily from the left, while a DP like this finds a segmentation that is optimal for a chosen score (fewest pieces here, highest probability in a unigram
        language-model tokenizer)."""),
    write("Explain the edits between two texts", "hard", tag="GenAI",
        prompt="""Write `align(reference, hypothesis)` for two word lists, returning the list of operations that turns the reference into the hypothesis with minimum edit distance:
        `("keep", r)`, `("sub", r, h)`, `("del", r)` and `("ins", h)`, in order. Build the full DP table, then backtrack from the bottom-right cell, preferring keep/sub, then
        delete, then insert when several moves are optimal. Also return the distance.""",
        code="""
        def align(reference, hypothesis):
            pass
        """,
        tests="""
        ref = "refunds take five business days".split()
        hyp = "refund takes five days".split()
        dist, ops = align(ref, hyp)
        assert dist == 3
        assert ops == [("sub", "refunds", "refund"), ("sub", "take", "takes"), ("keep", "five"), ("del", "business"), ("keep", "days")]
        assert align([], ["a", "b"]) == (2, [("ins", "a"), ("ins", "b")]) and align(["a"], []) == (1, [("del", "a")])
        d, o = align("the cat sat".split(), "the cat sat on the mat".split())
        assert d == 3 and o[-3:] == [("ins", "on"), ("ins", "the"), ("ins", "mat")]
        """,
        hints=["`dp[i][j]` for prefixes of length `i` and `j`; first row `j`, first column `i`.",
               "Backtrack while `i > 0 or j > 0`: if `i and j` and `dp[i][j] == dp[i-1][j-1] + cost`, it was keep or sub; elif `i` and `dp[i][j] == dp[i-1][j] + 1`, a deletion; else an insertion. Reverse at the end."],
        solution="""
        def align(reference, hypothesis):
            n, m = len(reference), len(hypothesis)
            dp = [[0] * (m + 1) for _ in range(n + 1)]
            for i in range(n + 1):
                dp[i][0] = i
            for j in range(m + 1):
                dp[0][j] = j
            for i in range(1, n + 1):
                for j in range(1, m + 1):
                    cost = 0 if reference[i - 1] == hypothesis[j - 1] else 1
                    dp[i][j] = min(dp[i - 1][j - 1] + cost, dp[i - 1][j] + 1, dp[i][j - 1] + 1)
            ops, i, j = [], n, m
            while i > 0 or j > 0:
                if i and j:
                    cost = 0 if reference[i - 1] == hypothesis[j - 1] else 1
                    if dp[i][j] == dp[i - 1][j - 1] + cost:
                        ops.append(("keep", reference[i - 1]) if cost == 0 else ("sub", reference[i - 1], hypothesis[j - 1]))
                        i, j = i - 1, j - 1
                        continue
                if i and dp[i][j] == dp[i - 1][j] + 1:
                    ops.append(("del", reference[i - 1]))
                    i -= 1
                else:
                    ops.append(("ins", hypothesis[j - 1]))
                    j -= 1
            return dp[n][m], ops[::-1]
        """,
        why="""The distance alone says how wrong a transcript or generated answer is; the **alignment** says where: which words were substituted, dropped or added, which is what an evaluation
        report or a diff view shows. Recovering it requires the full table (O(n * m) memory instead of two rows), because backtracking asks, at each cell, which neighbour
        produced its value; a fixed preference order makes the result deterministic when several moves are optimal. The same backtracking pattern recovers the chosen items in
        knapsack (problem 9), the words in segmentation (problem 12) and the common subsequence in LCS."""),
    fix("Read the code: counting decodings", "hard", tag="Data work",
        prompt="""Messages are encoded as digit strings with `A=1 ... Z=26`. `count_decodings(s)` should count the ways to decode `s` (`"226"` has 3: `BZ`, `VF`, `BBF`). The recursive version is
        exponential (it recomputes the same suffixes), treats `"0"` as a letter, accepts two-digit codes like `"06"` and `"27"`, and returns 1 for an empty string only by accident.
        Rewrite it bottom-up in O(n): a single `0` decodes to nothing, a two-digit code is valid only from 10 to 26, and the empty string has exactly one decoding.""",
        code="""
        def count_decodings(s):
            if len(s) <= 1:
                return 1
            ways = count_decodings(s[1:])
            if int(s[:2]) <= 26:
                ways += count_decodings(s[2:])
            return ways
        """,
        tests="""
        assert count_decodings("226") == 3 and count_decodings("12") == 2 and count_decodings("") == 1
        assert count_decodings("06") == 0 and count_decodings("10") == 1 and count_decodings("27") == 1 and count_decodings("100") == 0
        assert count_decodings("11106") == 2 and count_decodings("0") == 0
        assert count_decodings("1" * 25) == 121393
        """,
        hints=["`ways[i]` = decodings of `s[:i]`, `ways[0] = 1`. Add `ways[i - 1]` if `s[i - 1] != \"0\"`, and `ways[i - 2]` if `10 <= int(s[i - 2:i]) <= 26`."],
        solution="""
        def count_decodings(s):
            ways = [1] + [0] * len(s)
            for i in range(1, len(s) + 1):
                if s[i - 1] != "0":
                    ways[i] += ways[i - 1]
                if i >= 2 and 10 <= int(s[i - 2:i]) <= 26:
                    ways[i] += ways[i - 2]
            return ways[-1]
        """,
        why="""The recursion had the right shape (the first letter uses one or two digits) but recomputed the same suffixes exponentially often: sixty `1`s would take years, while the table
        needs sixty steps (the answer is a Fibonacci number). The base case "length at most one means one way" was wrong for `"0"`, which cannot be decoded, and the two-digit
        test accepted `"06"` (leading zero) and any number below 27 including single digits; the precise rules are "one digit from 1 to 9" and "two digits from 10 to 26". The
        empty prefix has exactly one decoding (decode nothing), the base case that makes every count correct, the same role `{0: 1}` played in 16.2's prefix sums."""),
    predict("lru_cache details", "hard",
        code="""
        from functools import lru_cache

        @lru_cache(maxsize=2)
        def embed(text, model="small"):
            return (text, model)

        embed("a")
        embed("a")
        embed("a", model="small")
        embed(text="a")
        print(embed.cache_info())
        embed("b")
        embed("c")
        embed("a")
        print(embed.cache_info())
        embed.cache_clear()
        print(embed.cache_info(), embed.__wrapped__("x") == ("x", "small"))
        """,
        hints=["The cache key is built from the arguments as passed: `f(\"a\")`, `f(\"a\", model=\"small\")` and `f(text=\"a\")` are three different keys. With `maxsize=2`, the least recently used entry is evicted."],
        why="""`lru_cache` keys on the arguments exactly as given, so a positional call, the same call with the default spelled out, and a keyword call are three separate cache entries even
        though they mean the same thing: one hit and three misses, with only two entries kept. Adding `"b"` and `"c"` evicts the older entries, so `"a"` is a miss again, and
        `currsize` never exceeds `maxsize`. `cache_clear()` resets the statistics and contents, and `__wrapped__` reaches the original function without the cache. For caches of
        expensive calls (embeddings, completions), normalise arguments into one canonical key yourself."""),
)

section("interview", "Interview questions",
    explain("How do you recognise a dynamic programming problem, and how do you approach it?", "medium", tag="Interview",
        why="""Signals: the question asks for an optimum (minimum cost, maximum value, longest, fewest) or a count of ways, the input is a sequence, string, grid or budget, and a brute force
        would try all combinations, with the same sub-decisions recurring (the remaining amount, the suffix still to process, the prefixes compared so far). The approach: define
        the **state** (the smallest set of parameters that determines a subproblem), write the **recurrence** by considering the last (or first) decision, list the **base
        cases**, and choose an **order**: top-down recursion with `functools.cache` is quick to write and only visits reachable states, bottom-up tabulation avoids recursion limits
        and often allows keeping only one or two rows. State the complexity as states times transitions per state. Then reconstruct the solution if needed by storing choices or
        backtracking through the table. Check small cases by hand, including the empty input, and compare against brute force on random tests."""),
    explain("Memoization or tabulation: what are the trade-offs?", "medium", tag="Interview",
        why="""**Memoization** (top-down) keeps the code close to the recursive definition, computes only the states actually reached (a win when many states are irrelevant), and is fast to
        write with `@functools.cache`; but it pays function-call overhead, hits Python's recursion limit for deep state chains (about 1,000 by default), needs hashable arguments,
        and keeps every cached result in memory. **Tabulation** (bottom-up) uses loops in an order that guarantees dependencies are ready, has no recursion limit and lower
        overhead, and lets you discard old rows (edit distance in O(m) memory instead of O(n m)); but it computes every state in the table, even unused ones, and requires
        working out the iteration order explicitly. In interviews, starting top-down and converting to bottom-up when asked about memory or deep inputs is a good way to show both."""),
    explain("Where does dynamic programming show up in ML and LLM work?", "hard", tag="Interview",
        why="""Many places, often hidden inside libraries. **Evaluation**: edit distance gives word and character error rates for speech and OCR, longest common subsequence gives ROUGE-L for
        summaries, and alignment (backtracking the edit table) explains errors. **Sequence models**: the Viterbi algorithm finds the most likely tag sequence in HMMs and CRFs,
        the forward algorithm computes sequence probabilities, CTC loss for speech recognition sums over alignments with DP, and beam search is a pruned approximation of exact
        DP decoding. **Tokenisation**: unigram language-model tokenizers (SentencePiece) choose the most probable segmentation with DP over the text, the same structure as word
        break. **Retrieval and prompting**: choosing context chunks under a token budget is a knapsack, and dynamic time warping aligns time series. **Reinforcement learning**:
        value iteration and the Bellman equation are DP over states. Knowing the pattern helps you recognise when a greedy shortcut is wrong and when an exact solution is cheap."""),
)

recap(
    "DP applies when the answer for a state is built from smaller overlapping states: compute each state once.",
    "Design it with four questions: state, recurrence, base cases, order; complexity is states times transitions.",
    "Top-down: `@functools.cache` (hashable arguments, recursion limits). Bottom-up: tables filled in dependency order, often with one or two rows of memory.",
    "Pad two-sequence tables with an empty-prefix row and column; reconstruct solutions by storing choices or backtracking.",
    "Classics: coin change, LCS (ROUGE-L), edit distance (WER, alignment), knapsack (context budgets), LIS with `bisect`, Kadane, segmentation.",
)
