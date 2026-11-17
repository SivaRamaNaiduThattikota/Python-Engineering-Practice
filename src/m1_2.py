from lesson import *

lesson(
    id="m1-2", num="1.2", title="Control flow and loops",
    intro="if, for and while, plus the tools that make loops clean: range, enumerate, zip, break, continue "
          "and the loop else. Most interview warm-ups are loops, and most loop bugs are off by one.",
    desc="if / elif, for and while, break, continue, loop else, range, enumerate and zip.",
    keys="if elif else for while range enumerate zip strict break continue loop else off by one nested loop walrus",
)

term("Loop else", "An `else` block on a `for` or `while` runs only if the loop finished without hitting `break`.")
term("Off-by-one error", "A loop or range that runs one step too many or too few, usually at the start or end.")
term("enumerate", "`enumerate(xs, start=0)` gives `(index, item)` pairs, so you never need `range(len(xs))`.")
term("zip", "`zip(a, b)` pairs items by position and stops at the shortest input. `strict=True` raises if the lengths differ.")

LOOP_FIG = """
<svg viewBox="0 0 640 150" role="img" aria-label="A for loop: take the next item, run the body; break leaves and skips else; when items run out, else runs.">
  <defs><marker id="a2" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M0 0 L10 5 L0 10 z" style="fill:var(--label2)"/></marker></defs>
  <rect x="10" y="50" width="130" height="44" rx="12" class="box a"/><text x="75" y="77" class="w mid">next item?</text>
  <rect x="200" y="50" width="130" height="44" rx="12" class="box"/><text x="265" y="77" class="v mid">loop body</text>
  <rect x="420" y="6" width="200" height="40" rx="12" class="box"/><text x="520" y="31" class="v mid">else block</text>
  <rect x="420" y="98" width="200" height="40" rx="12" class="box b"/><text x="520" y="123" class="w mid">after the loop</text>
  <path d="M140 72 H196" style="stroke:var(--label2);stroke-width:2;fill:none" marker-end="url(#a2)"/><text x="168" y="64" class="mid">yes</text>
  <path d="M265 50 V30 H75 V46" style="stroke:var(--label2);stroke-width:2;fill:none" marker-end="url(#a2)"/><text x="170" y="24" class="mid">continue / end of body</text>
  <path d="M75 94 V118 H170 Q200 118 200 60 Q200 26 416 26" style="stroke:var(--label2);stroke-width:2;fill:none" marker-end="url(#a2)"/><text x="110" y="134" class="mid">no items left</text>
  <path d="M330 80 H380 V118 H416" style="stroke:var(--red);stroke-width:2;fill:none" marker-end="url(#a2)"/><text x="360" y="72" class="v mid">break</text>
  <path d="M520 46 V94" style="stroke:var(--label2);stroke-width:2;fill:none" marker-end="url(#a2)"/>
</svg>"""

section("rules", "The rules in one screen",
    ex("""
    print(list(range(5)))
    print(list(range(2, 10, 3)))
    print(list(range(5, 0, -1)))
    print(list(range(5, 2)))
    """, "ranges.py"),
    p("""`range(start, stop, step)` includes `start` and stops **before** `stop`, like a half-open interval.
    The length of `range(a, b)` is `b - a`. A step that goes the wrong way gives an empty range, not an error."""),
    ex("""
    names = ["Ana", "Ben", "Chi"]
    scores = [91, 78, 85]
    for i, name in enumerate(names, start=1):
        print(i, name)
    for name, score in zip(names, scores):
        print(f"{name}: {score}")
    """, "enumerate_zip.py"),
    p("""`enumerate` gives you the position and the item together. `zip` walks several sequences side by side.
    Both remove the need for `range(len(xs))` and the `xs[i]` lookups that come with it."""),
    callout("sql", "SQL / Power BI", """`enumerate` is `ROW_NUMBER()`. `zip` is a join **by position**, not by key: if
    one list is sorted differently or has a missing row, `zip` pairs the wrong rows and says nothing. It also silently stops
    at the shorter list. Pass `strict=True` and Python raises instead."""),
    ex("""
    for n in [3, 5, 8, 9]:
        if n % 2 == 0:
            print("first even:", n)
            break
    else:
        print("no even numbers")

    for n in [3, 5, 9]:
        if n % 2 == 0:
            print("first even:", n)
            break
    else:
        print("no even numbers")
    """, "loop_else.py"),
    fig(LOOP_FIG, "`break` jumps straight past `else`. `else` runs only when the loop ran out of items on its own."),
    p("""`break` leaves the loop. `continue` skips to the next item. The loop `else` reads as "no break": it is the
    natural place for "searched everything and did not find it". A `while` loop can have an `else` too."""),
    ex("""
    total = 0
    for i in range(1, 4):
        total += i
    print(i, total)

    n = 37
    steps = 0
    while n != 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        steps += 1
    print(steps)
    """, "after_the_loop.py"),
    p("""The loop variable still exists after the loop and keeps its last value. `x if cond else y` is the one-line
    if, called a conditional expression. Use `while` when you do not know the number of passes in advance."""),
    callout("warn", "Changing a list while looping over it", """Removing items from a list inside `for x in items`
    makes the loop skip the item after each removal, because the positions shift under it. Build a new list instead
    (problem 6)."""),
    callout("sql", "Row by row", """A Python loop over rows is like a SQL cursor: fine for a few thousand items, slow
    for millions. In pandas and numpy you replace most loops with whole-column operations. That comes later, but the
    habit of asking "do I really need a loop here?" starts now."""),
)

section("warmup", "Warm-up",
    predict("Ranges", "easy",
        code="""
        print(list(range(3, 8)))
        print(list(range(0, 10, 4)))
        print(list(range(10, 0, -4)))
        print(list(range(-3, 0)))
        print(len(range(4, 100, 4)))
        """,
        hints=["`stop` is never included. For a step `s`, the values are start, start + s, start + 2s, ... while still before stop.",
               "For the last line, count the multiples of 4 from 4 up to 96."],
        why="""`range(10, 0, -4)` goes 10, 6, 2 and stops before 0. `range(-3, 0)` is -3, -2, -1. The last line counts
        4, 8, ..., 96: that is 96 / 4 = 24 values. `len` on a range is computed instantly, nothing is generated."""),
    predict("Break and the loop else", "easy",
        code="""
        for word in ["alpha", "beta", "gamma"]:
            if word.startswith("b"):
                print("found", word)
                break
            print("checked", word)
        else:
            print("not found")
        print("done")
        """,
        hints=["Walk through it word by word. What happens to `else` when `break` runs?"],
        why="""`alpha` is checked and printed. `beta` matches, so it prints `found beta` and breaks. Because the loop
        ended with `break`, the `else` is skipped. `gamma` is never looked at."""),
    predict("Continue and the leftover variable", "easy",
        code="""
        kept = 0
        for i in range(6):
            if i % 3 == 0:
                continue
            kept += i
        print(kept, i)
        """,
        hints=["Which values of `i` are skipped? `0 % 3` is 0."],
        why="""`continue` skips 0 and 3, so `kept` is 1 + 2 + 4 + 5 = 12. After the loop `i` still holds its last value, 5.
        Relying on that is fragile: if the list is empty, `i` is never set at all."""),
    write("FizzBuzz", "easy", tag="Interview",
        prompt="""Write `fizzbuzz(n)` that returns a list of strings for 1 to n: `"Fizz"` for multiples of 3,
        `"Buzz"` for multiples of 5, `"FizzBuzz"` for multiples of both, and the number as a string otherwise.""",
        code="""
        def fizzbuzz(n):
            pass
        """,
        tests="""
        assert fizzbuzz(5) == ["1", "2", "Fizz", "4", "Buzz"]
        assert fizzbuzz(15)[-1] == "FizzBuzz"
        assert fizzbuzz(0) == []
        assert fizzbuzz(30).count("FizzBuzz") == 2
        """,
        hints=["Loop over `range(1, n + 1)`.", "Check the 15 case first, or it gets caught by the 3 case."],
        solution="""
        def fizzbuzz(n):
            out = []
            for i in range(1, n + 1):
                if i % 15 == 0:
                    out.append("FizzBuzz")
                elif i % 3 == 0:
                    out.append("Fizz")
                elif i % 5 == 0:
                    out.append("Buzz")
                else:
                    out.append(str(i))
            return out
        """,
        why="""The order of the `elif` chain is the whole problem: the most specific condition goes first. Interviewers
        use it to see clean branching and `range(1, n + 1)`, which catches the classic off-by-one of `range(n)`."""),
    write("First value over a limit", "easy",
        prompt="""Write `first_over(nums, limit)` that returns the **index** of the first number greater than `limit`,
        or -1 if there is none. Use `enumerate`.""",
        code="""
        def first_over(nums, limit):
            pass
        """,
        tests="""
        assert first_over([3, 8, 12, 20], 10) == 2
        assert first_over([3, 8], 10) == -1
        assert first_over([], 0) == -1
        assert first_over([11, 50], 10) == 0
        """,
        hints=["`for i, x in enumerate(nums):` and return as soon as you find it."],
        solution="""
        def first_over(nums, limit):
            for i, x in enumerate(nums):
                if x > limit:
                    return i
            return -1
        """,
        why="""Returning from inside the loop is the cleanest `break`. The `return -1` after the loop is the "searched
        everything" case, the same idea as the loop `else`. This is what `str.find` and many search helpers do."""),
)

section("medium", "Medium",
    fix("Removing negatives skips some", "medium",
        prompt="""This should remove every negative number from the list and return it. It misses some. Fix it.""",
        code="""
        def remove_negatives(nums):
            for x in nums:
                if x < 0:
                    nums.remove(x)
            return nums
        """,
        tests="""
        assert remove_negatives([1, -2, 3]) == [1, 3]
        assert remove_negatives([-1, -2, 3]) == [3]
        assert remove_negatives([-5, -5, -5]) == []
        assert remove_negatives([]) == []
        """,
        hints=["Trace `[-1, -2, 3]` by hand. After `-1` is removed, what is at position 0, and which position does the loop look at next?",
               "Do not change the list you are looping over. Build a new one."],
        solution="""
        def remove_negatives(nums):
            return [x for x in nums if x >= 0]
        """,
        why="""The `for` loop walks positions 0, 1, 2... Removing `-1` shifts `-2` into position 0, but the loop moves on
        to position 1 and never sees it. Building a new list avoids the problem and also leaves the caller's list
        untouched (more on why that matters in Module 2). If you must change it in place, `nums[:] = [...]` does it."""),
    fix("The last n items", "medium",
        prompt="""`last_n(items, n)` should return the last `n` items in order. It is off by one. Fix the loop.""",
        code="""
        def last_n(items, n):
            out = []
            for i in range(len(items) - n, len(items) - 1):
                out.append(items[i])
            return out
        """,
        tests="""
        assert last_n([1, 2, 3, 4], 2) == [3, 4]
        assert last_n([1, 2, 3], 3) == [1, 2, 3]
        assert last_n([1, 2], 0) == []
        assert last_n(["a"], 1) == ["a"]
        """,
        hints=["What is the last index of a list? What does `range` do with its `stop`?"],
        solution="""
        def last_n(items, n):
            out = []
            for i in range(len(items) - n, len(items)):
                out.append(items[i])
            return out
        """,
        why="""The last index is `len(items) - 1`, and `range` already stops before `stop`, so `stop` should be
        `len(items)`. Subtracting 1 twice is the most common off-by-one there is. Why not `items[-n:]`? Try it with
        `n = 0`: `items[-0:]` is `items[0:]`, the whole list. That slicing trap comes back in Module 4."""),
    trace("Collatz steps", "medium",
        prompt="Fill in `n` and `steps` after each pass.",
        code="""
        n = 6
        steps = 0
        while n != 1:
            n = n // 2 if n % 2 == 0 else 3 * n + 1
            steps += 1  # row: f"pass {steps}"
        """,
        trace_vars=["n", "steps"],
        hints=["Even: halve it. Odd: times 3 plus 1. Keep going until 1."],
        why="""6 goes 3, 10, 5, 16, 8, 4, 2, 1: eight passes. Nobody knows in advance how many passes it takes (that is
        an open maths problem), which is exactly when `while` is the right loop."""),
    write("Pair names with scores", "medium",
        prompt="""Write `pair_up(names, scores)` that returns a list of strings like `"Ana: 91"`. If the two lists have
        different lengths it must raise `ValueError`, because pairing by position would be wrong.""",
        code="""
        def pair_up(names, scores):
            pass
        """,
        tests="""
        def raises(exc, f, *args):
            try:
                f(*args)
            except exc:
                return True
            return False
        assert pair_up(["Ana", "Ben"], [91, 78]) == ["Ana: 91", "Ben: 78"]
        assert pair_up([], []) == []
        assert raises(ValueError, pair_up, ["Ana"], [91, 78])
        assert raises(ValueError, pair_up, ["Ana", "Ben"], [91])
        """,
        hints=["`zip` has a keyword argument that turns a length mismatch into an error."],
        solution="""
        def pair_up(names, scores):
            return [f"{name}: {score}" for name, score in zip(names, scores, strict=True)]
        """,
        why="""Plain `zip` would quietly drop the extra score, and in a data pipeline that is a silent wrong answer.
        `strict=True` (Python 3.10+) raises `ValueError` as soon as one side runs out early. Use it whenever the inputs
        are supposed to line up."""),
    write("Running maximum", "medium", tag="Data work",
        prompt="""Write `running_max(nums)` that returns a list where each position holds the largest value seen so far.
        `[3, 1, 4, 1, 5]` gives `[3, 3, 4, 4, 5]`. This is a cumulative max, like a running total in Power BI.""",
        code="""
        def running_max(nums):
            pass
        """,
        tests="""
        assert running_max([3, 1, 4, 1, 5]) == [3, 3, 4, 4, 5]
        assert running_max([]) == []
        assert running_max([-2, -5, -1]) == [-2, -2, -1]
        assert running_max([7]) == [7]
        """,
        hints=["Keep one variable for the best so far. Start it from the first value, not from 0, or negative inputs break.",
               "Or start it at `float('-inf')`."],
        solution="""
        def running_max(nums):
            out = []
            best = float("-inf")
            for x in nums:
                best = max(best, x)
                out.append(best)
            return out
        """,
        why="""Starting `best` at 0 is the classic bug: `[-2, -5, -1]` would give `[0, 0, 0]`. Minus infinity is smaller
        than any number, so the first value always wins. The library version is `itertools.accumulate(nums, max)`, and in
        pandas it is `s.cummax()`."""),
    choose("Has a duplicate?", "medium",
        prompt="Both return True if any value appears twice. Which is faster for 2,000 different numbers?",
        setup="import random\nnums = random.sample(range(10**6), 2000)",
        options={
            "a": "found = False\nfor i in range(len(nums)):\n    for j in range(i + 1, len(nums)):\n        if nums[i] == nums[j]:\n            found = True",
            "b": "s = sorted(nums)\nfound = any(s[k] == s[k + 1] for k in range(len(s) - 1))",
        },
        answer="b",
        hints=["How many pairs does A compare for 2,000 items? How much work is one sort?"],
        why="""A compares every pair: about n² / 2, so two million comparisons for 2,000 items. B sorts once (about
        n log n) and then only compares neighbours, since equal values end up next to each other. Module 4 shows the
        fastest version, `len(set(nums)) != len(nums)`, which is one pass."""),
    refactor("Use enumerate and zip", "medium",
        prompt="Rewrite this without manual indexes. Keep the tests green.",
        code="""
        def report(names, scores):
            lines = []
            i = 0
            while i < len(names):
                lines.append(str(i + 1) + ". " + names[i] + " " + str(scores[i]))
                i = i + 1
            return lines
        """,
        tests="""
        assert report(["Ana", "Ben"], [91, 78]) == ["1. Ana 91", "2. Ben 78"]
        assert report([], []) == []
        assert report(["Chi"], [85]) == ["1. Chi 85"]
        """,
        hints=["`enumerate(zip(names, scores), start=1)` gives `(i, (name, score))`."],
        solution="""
        def report(names, scores):
            return [f"{i}. {name} {score}"
                    for i, (name, score) in enumerate(zip(names, scores), start=1)]
        """,
        why="""No counter to forget to increment, no `[i]` lookups, and `start=1` replaces the `i + 1`. Nested unpacking
        `(name, score)` pulls the pair apart right in the loop header. A `while` loop with a manual counter is almost
        always a `for` loop in disguise."""),
)

section("hard", "Hard",
    write("Two numbers that add up", "hard", tag="Interview",
        prompt="""Write `find_pair(nums, target)` that returns the first pair of positions `(i, j)` with `i < j` and
        `nums[i] + nums[j] == target`, scanning `i` from left to right. Return `None` if there is no pair.""",
        code="""
        def find_pair(nums, target):
            pass
        """,
        tests="""
        assert find_pair([2, 7, 11, 15], 9) == (0, 1)
        assert find_pair([3, 2, 4], 6) == (1, 2)
        assert find_pair([3, 3], 6) == (0, 1)
        assert find_pair([1, 2, 3], 7) is None
        assert find_pair([], 1) is None
        """,
        hints=["Two nested loops: `j` starts at `i + 1` so a number is never paired with itself.",
               "To stop both loops at once, `return` from inside the inner one."],
        solution="""
        def find_pair(nums, target):
            for i in range(len(nums)):
                for j in range(i + 1, len(nums)):
                    if nums[i] + nums[j] == target:
                        return i, j
            return None
        """,
        why="""`break` only leaves the inner loop, so for "stop everything" put the loops in a function and `return`.
        Starting `j` at `i + 1` skips self-pairs and duplicate pairs. This is the brute force O(n²) answer to the most
        famous interview question there is. Say so, then give the one-pass dict version (Module 4)."""),
    write("Primes with a loop else", "hard",
        prompt="""Write `primes_up_to(n)` that returns all primes up to and including `n`. Use a `for ... else` to
        decide whether a number is prime, and only test divisors up to its square root.""",
        code="""
        def primes_up_to(n):
            pass
        """,
        tests="""
        assert primes_up_to(10) == [2, 3, 5, 7]
        assert primes_up_to(1) == []
        assert primes_up_to(2) == [2]
        assert primes_up_to(30)[-1] == 29
        assert len(primes_up_to(100)) == 25
        """,
        hints=["For each candidate `k`, loop over `d` from 2 while `d * d <= k`. A `range` can do it: `range(2, int(k ** 0.5) + 1)`.",
               "`break` when `d` divides `k`. The `else` of that inner loop is where `k` is prime."],
        solution="""
        def primes_up_to(n):
            primes = []
            for k in range(2, n + 1):
                for d in range(2, int(k ** 0.5) + 1):
                    if k % d == 0:
                        break
                else:
                    primes.append(k)
            return primes
        """,
        why="""If `k` has a divisor larger than its square root, it also has one smaller than it, so checking up to the
        square root is enough. The `else` belongs to the inner `for`: it runs when no divisor was found. For 2 and 3 the
        inner range is empty, so `else` runs straight away, which is correct. For big `n`, the sieve of Eratosthenes is
        much faster (Module 16)."""),
    write("Run lengths", "hard", tag="Data work",
        prompt="""Write `run_lengths(xs)` that turns consecutive repeats into `(value, count)` pairs:
        `[1, 1, 2, 2, 2, 1]` gives `[(1, 2), (2, 3), (1, 1)]`. In SQL this is the "gaps and islands" problem:
        grouping consecutive rows with the same status.""",
        code="""
        def run_lengths(xs):
            pass
        """,
        tests="""
        assert run_lengths([1, 1, 2, 2, 2, 1]) == [(1, 2), (2, 3), (1, 1)]
        assert run_lengths([]) == []
        assert run_lengths(["a"]) == [("a", 1)]
        assert run_lengths([0, 0, 0]) == [(0, 3)]
        assert run_lengths([None, None, 1]) == [(None, 2), (1, 1)]
        """,
        hints=["Keep the current value and its count. When the value changes, save the finished run and start a new one.",
               "Do not forget the last run: it is still open when the loop ends."],
        solution="""
        def run_lengths(xs):
            out = []
            for x in xs:
                if out and out[-1][0] == x:
                    out[-1] = (x, out[-1][1] + 1)
                else:
                    out.append((x, 1))
            return out
        """,
        why="""Looking at the last saved run (`out[-1]`) avoids a separate "current" variable and the classic bug of
        forgetting the final run after the loop. Note `if out and ...`: the truthiness check stops `out[-1]` failing on
        the first item, and it keeps working when the value is 0 or `None`. The library version is `itertools.groupby`."""),
    predict("While, continue, break, else", "hard",
        code="""
        i = 0
        while i < 10:
            i += 1
            if i % 3:
                continue
            if i > 7:
                break
            print(i)
        else:
            print("finished")
        print("end", i)
        """,
        hints=["`if i % 3:` is true when `i` is not a multiple of 3.", "Does the loop end by its condition or by `break`?"],
        why="""Only multiples of 3 get past the `continue`: 3, 6, 9. 3 and 6 are printed. At 9, `9 > 7`, so it breaks.
        Because the loop ended with `break`, `"finished"` is not printed, and `i` is 9."""),
)

section("interview", "Interview questions",
    explain("Is `for i in range(len(xs))` wrong?", "easy", tag="Interview",
        why="""Not wrong, but usually a sign something cleaner exists. Use `for x in xs` for the items, `enumerate(xs)` if
        you also need the index, and `zip(a, b)` to walk two lists together. `range(len(...))` is fine when you really
        work with positions, for example comparing `xs[i]` with `xs[i + 1]` or the nested `j` in `i + 1` loops."""),
    explain("What does `else` on a loop do, and when would you use it?", "medium", tag="Interview",
        why="""It runs when the loop finishes without `break`. That makes it the "not found" branch of a search: loop
        over candidates, `break` when one matches, put the fallback in `else`. It replaces a `found = False` flag. It
        is easy to misread as "runs if the loop did not run", so many teams prefer a function with an early `return`.
        Know both, and say why."""),
    explain("Why is looping over rows slow in pandas, and what do you do instead?", "medium", tag="Data work",
        why="""Each pass of a Python loop runs the interpreter: look up the row, build Python objects, call your
        function. `df.iterrows()` even builds a new Series per row. Whole-column operations (`df["a"] * df["b"]`,
        `np.where`, `.groupby().agg()`) run one compiled loop in C over the raw arrays, often 100 times faster. It is the
        same lesson as cursors versus set-based SQL. Loops are still fine for small data or for logic that really goes
        row by row."""),
)

recap(
    "`range(start, stop, step)` never includes `stop`. The last index is `len(xs) - 1`, so `range(len(xs))` is already right.",
    "`enumerate` for index + item, `zip` to walk lists together, `zip(..., strict=True)` when they must line up.",
    "`break` leaves the loop, `continue` skips to the next pass, and the loop `else` runs only if there was no `break`.",
    "Never add to or remove from a list while looping over it. Build a new list.",
    "To leave nested loops, put them in a function and `return`. Use `while` when the number of passes is unknown.",
)
