from lesson import *

lesson(
    id="m1-p", num="1.P", title="Module 1 practice set and mini project",
    intro="Mixed problems from 1.1 and 1.2, in no particular topic order, the way they come up in real work and "
          "interviews. Then one small project that needs all of it.",
    desc="Mixed problems from the whole module, then one small program that uses all of it.",
    keys="practice mixed review project payments batch decimal rounding bands luhn collatz second largest ceiling division",
)

section("how", "How to use this page",
    p("""No recap here: each problem says which lesson it leans on only in its hint. Try each one cold first. If you
    get stuck for more than ten minutes, open a hint, not the solution. Problems you solve after opening the solution
    are marked that way, so the score on this page stays honest."""),
)

section("set", "Practice set",
    predict("Truthy on one line", "easy",
        code="""
        for v in [0, 1, "", "a", None, [0]]:
            print("yes" if v else "no", end=" ")
        print()
        print(len([v for v in range(-3, 4) if v]))
        """,
        hints=["`end=\" \"` keeps everything on one line. In the last line, which number in -3 to 3 is falsy? (1.1)"],
        why="""Only 0, `""` and `None` are falsy here, and `[0]` is a non-empty list. The second line counts the
        truthy numbers from -3 to 3: all seven except 0, so 6."""),
    write("Clamp a value", "easy",
        prompt="Write `clamp(x, lo, hi)` that returns `x` limited to the range `lo` to `hi` (both included).",
        code="""
        def clamp(x, lo, hi):
            pass
        """,
        tests="""
        assert clamp(5, 0, 10) == 5
        assert clamp(-3, 0, 10) == 0
        assert clamp(99, 0, 10) == 10
        assert clamp(0.5, 0.0, 1.0) == 0.5
        """,
        hints=["You can do it with `if`, or with one line of `min` and `max`."],
        solution="""
        def clamp(x, lo, hi):
            return max(lo, min(x, hi))
        """,
        why="""`min(x, hi)` cuts off the top, then `max(lo, ...)` cuts off the bottom. Clamping shows up all over ML:
        clipping gradients, clipping predicted probabilities away from 0 and 1 before a log loss (`np.clip`)."""),
    write("Count the digits", "easy",
        prompt="""Write `count_digits(n)` that returns how many digits the integer `n` has, using a loop with `//`, not
        `len(str(n))`. `0` has one digit, and the sign does not count.""",
        code="""
        def count_digits(n):
            pass
        """,
        tests="""
        assert count_digits(7) == 1
        assert count_digits(0) == 1
        assert count_digits(4073) == 4
        assert count_digits(-120) == 3
        assert count_digits(10 ** 20) == 21
        """,
        hints=["Work on `abs(n)`, and handle 0 before the loop (or use a loop that always runs once)."],
        solution="""
        def count_digits(n):
            n = abs(n)
            count = 1
            while n >= 10:
                n //= 10
                count += 1
            return count
        """,
        why="""Starting `count` at 1 and looping while `n >= 10` handles 0 without a special case. The `abs` matters:
        `-120 // 10` is -12, and `-1 // 10` is -1, not 0, so a loop on a negative number with `while n != 0` never
        ends. That is floor division from 1.1 biting back."""),
    trace("To binary, step by step", "medium",
        prompt="Fill in `x` and `bits` after each pass. Strings can be typed with or without quotes.",
        code="""
        x = 13
        bits = ""
        while x:
            bits = str(x % 2) + bits
            x //= 2  # row: f"pass {len(bits)}"
        """,
        trace_vars=["x", "bits"],
        hints=["`x % 2` is the last binary digit. It goes on the **front** of `bits`."],
        why="""13 is 1101 in binary. The remainders come out last digit first (1, 0, 1, 1), so each one is put in
        front. `while x:` is truthiness: the loop stops when `x` reaches 0."""),
    fix("Average of a list", "medium", tag="Data work",
        prompt="""`average(nums)` has two bugs: it crashes on an empty list and gives a wrong answer for `[1, 2]`.
        An empty list should return `None`.""",
        code="""
        def average(nums):
            total = 0
            for x in nums:
                total += x
            return total // len(nums)
        """,
        tests="""
        assert average([1, 2]) == 1.5
        assert average([4, 4, 4]) == 4
        assert average([]) is None
        assert average([-1, -2]) == -1.5
        """,
        hints=["Which division operator did 1.1 say always gives a float?", "Check for the empty list before dividing."],
        solution="""
        def average(nums):
            if not nums:
                return None
            return sum(nums) / len(nums)
        """,
        why="""`//` floors, so `3 // 2` is 1, and `-3 // 2` is -2, which is wrong in a different direction. Returning
        `None` for no data (rather than 0) matches SQL's `AVG` over no rows, which gives NULL. The library version is
        `statistics.mean`, which raises on empty input instead."""),
    write("Round up to a multiple", "medium", tag="Interview",
        prompt="""Write `next_multiple(n, k)` that returns the smallest multiple of `k` that is greater than or equal
        to `n` (`k` is positive). Do it without `math.ceil` and without a loop.""",
        code="""
        def next_multiple(n, k):
            pass
        """,
        tests="""
        assert next_multiple(7, 5) == 10
        assert next_multiple(10, 5) == 10
        assert next_multiple(0, 3) == 0
        assert next_multiple(-7, 5) == -5
        assert next_multiple(10 ** 18 + 1, 10) == 10 ** 18 + 10
        """,
        hints=["`n // k` rounds down. How do you get a division that rounds up?", "Try `-(-n // k)`."],
        solution="""
        def next_multiple(n, k):
            return -(-n // k) * k
        """,
        why="""Flooring a negated number and negating back is ceiling division: `-(-7 // 5)` is `-(-2)` = 2. It stays in
        exact integers, so it works for huge numbers where `math.ceil(n / k)` would go through a float and lose
        precision (the last test). Use it for "how many pages / batches do I need": `-(-rows // batch_size)`."""),
    write("Second largest", "medium", tag="Interview",
        prompt="""Write `second_largest(nums)` that returns the second largest **distinct** value in one pass, without
        sorting. Return `None` if there is no such value.""",
        code="""
        def second_largest(nums):
            pass
        """,
        tests="""
        assert second_largest([3, 9, 4, 9, 7]) == 7
        assert second_largest([5, 5, 5]) is None
        assert second_largest([1]) is None
        assert second_largest([-1, -5]) == -5
        assert second_largest([2, 8]) == 2
        """,
        hints=["Keep two variables, `first` and `second`, both starting at `None`.",
               "A new value bigger than `first` pushes the old `first` down to `second`. A value equal to `first` is ignored."],
        solution="""
        def second_largest(nums):
            first = second = None
            for x in nums:
                if first is None or x > first:
                    first, second = x, first
                elif x != first and (second is None or x > second):
                    second = x
            return second
        """,
        why="""Three cases per value: a new maximum (shift down), a duplicate of the maximum (skip), or a new runner-up.
        `first, second = x, first` swaps in one step without a temporary. Starting at `None` instead of 0 keeps
        negative inputs working, and the `is None` checks, not truthiness, keep a real 0 from being treated as missing."""),
    choose("Is it prime?", "medium",
        prompt="Both check whether `n = 1_000_003` is prime. Which is faster?",
        setup="n = 1_000_003",
        options={
            "a": "prime = n > 1\nfor d in range(2, n):\n    if n % d == 0:\n        prime = False\n        break",
            "b": "prime = n > 1\nfor d in range(2, int(n ** 0.5) + 1):\n    if n % d == 0:\n        prime = False\n        break",
        },
        answer="b",
        hints=["1,000,003 is prime, so neither loop breaks early. How many divisors does each one try?"],
        why="""A tries about a million divisors, B about a thousand, because a divisor above the square root would come
        with a partner below it (1.2, problem 15). Same answer, a thousand times less work."""),
    refactor("Grade bands", "medium",
        prompt="Flatten this into one clean `if / elif` chain with chained comparisons. Keep the tests green.",
        code="""
        def grade(score):
            if score >= 0:
                if score <= 100:
                    if score >= 90:
                        return "A"
                    else:
                        if score >= 75:
                            return "B"
                        else:
                            if score >= 50:
                                return "C"
                            else:
                                return "F"
            return "invalid"
        """,
        tests="""
        assert grade(95) == "A"
        assert grade(90) == "A"
        assert grade(89) == "B"
        assert grade(75) == "B"
        assert grade(50) == "C"
        assert grade(49) == "F"
        assert grade(101) == "invalid"
        assert grade(-1) == "invalid"
        """,
        hints=["Handle the invalid case first with one chained comparison: `not 0 <= score <= 100`."],
        solution="""
        def grade(score):
            if not 0 <= score <= 100:
                return "invalid"
            if score >= 90:
                return "A"
            if score >= 75:
                return "B"
            if score >= 50:
                return "C"
            return "F"
        """,
        why="""Guard clause first, then the bands from the top down. Each `if` returns, so the order does the job of the
        lower bounds. The nesting went five deep, the flat version reads like the spec."""),
    predict("Adding 0.1 ten times", "hard",
        code="""
        import math
        total = 0.0
        for _ in range(10):
            total += 0.1
        print(total)
        print(total == 1.0, math.isclose(total, 1.0))
        print(sum([0.1] * 10), math.fsum([0.1] * 10))
        """,
        hints=["Each `+=` rounds to the nearest float, and the tiny errors add up.",
               "`math.fsum` tracks the lost bits. And since Python 3.12, so does the built-in `sum` for floats."],
        why="""The loop rounds after every `+=` and ends up just under 1, so `==` fails and `isclose` passes. The
        surprise is the last line: since Python 3.12, `sum()` on floats uses compensated summation, which keeps track
        of the rounding error as it goes, so it gives exactly 1.0, the same as `math.fsum`. Older Pythons print
        0.9999999999999999 there, so this is also a nice interview detail. The lesson stays the same: when you add many
        floats, such as losses over a dataset, the method of adding changes the last digits. Compare with `isclose`,
        and know that numpy's `sum` uses yet another method (pairwise summation)."""),
    write("Longest Collatz chain", "hard",
        prompt="""For each starting number from 1 up to (not including) `limit`, count the Collatz steps to reach 1
        (1.2, problem 8). Write `longest_collatz(limit)` that returns the starting number with the most steps. On a tie,
        return the smaller number.""",
        code="""
        def longest_collatz(limit):
            pass
        """,
        tests="""
        assert longest_collatz(2) == 1
        assert longest_collatz(10) == 9
        assert longest_collatz(30) == 27
        assert longest_collatz(7) == 6
        """,
        hints=["Write a small helper `steps(n)` with a `while` loop first.",
               "Use `>` (not `>=`) when updating the best, so the first, smaller number keeps a tie."],
        solution="""
        def steps(n):
            count = 0
            while n != 1:
                n = n // 2 if n % 2 == 0 else 3 * n + 1
                count += 1
            return count

        def longest_collatz(limit):
            best, best_steps = 1, 0
            for start in range(1, limit):
                s = steps(start)
                if s > best_steps:
                    best, best_steps = start, s
            return best
        """,
        why="""Splitting out `steps` keeps each loop simple. The tie rule comes free from the comparison: with `>` an
        equal later value never replaces the current best. 27 takes 111 steps, far more than its neighbours, which is
        why it is the famous example. For big limits you would cache steps already computed (Module 5)."""),
    write("Check a card number", "hard", tag="Data work",
        prompt="""Write `luhn_valid(number)` for a string of digits. The Luhn check: starting from the **rightmost**
        digit, double every second digit; if doubling gives more than 9, subtract 9; add everything up. The number is
        valid if the total is a multiple of 10. Card numbers and many ID numbers use it to catch typing mistakes.""",
        code="""
        def luhn_valid(number):
            pass
        """,
        tests="""
        assert luhn_valid("79927398713")
        assert not luhn_valid("79927398710")
        assert luhn_valid("4111111111111111")
        assert not luhn_valid("4111111111111112")
        assert luhn_valid("0")
        """,
        hints=["Loop over `reversed(number)` with `enumerate`. Positions 1, 3, 5, ... (counting from 0) get doubled.",
               "`int(ch)` turns a digit character into a number."],
        solution="""
        def luhn_valid(number):
            total = 0
            for i, ch in enumerate(reversed(number)):
                d = int(ch)
                if i % 2 == 1:
                    d *= 2
                    if d > 9:
                        d -= 9
                total += d
            return total % 10 == 0
        """,
        why="""Walking the digits right to left with `enumerate(reversed(...))` makes "every second digit from the right"
        simply "odd positions". `d - 9` is the same as adding the two digits of `d` (for 10 to 18). Validations like
        this are typical data-quality rules in a pipeline: cheap checks before a row is loaded."""),
    predict("Nested loops and break", "hard",
        code="""
        for i in range(3):
            for j in range(3):
                if j == i:
                    break
                print(i, j)
            else:
                print("inner finished", i)
        print("outer done")
        """,
        hints=["`break` only leaves the inner loop. The `else` belongs to the inner loop too."],
        why="""For `i = 0`, `j = 0` equals `i` straight away, so it breaks with nothing printed and the inner `else` is
        skipped. `i = 1` prints `1 0`, then breaks at `j = 1`. `i = 2` prints `2 0` and `2 1`, then breaks. The inner
        loop never finishes on its own, so `"inner finished"` never prints."""),
)

PROJECT_FIG = """
<svg viewBox="0 0 640 96" role="img" aria-label="Payments flow through three functions: band, round_money and summarize.">
  <defs><marker id="a3" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M0 0 L10 5 L0 10 z" style="fill:var(--label2)"/></marker></defs>
  <rect x="6" y="26" width="128" height="44" rx="12" class="box"/><text x="70" y="53" class="v mid">payments list</text>
  <rect x="176" y="4" width="150" height="38" rx="12" class="box a"/><text x="251" y="28" class="w mid">band(amount)</text>
  <rect x="176" y="54" width="150" height="38" rx="12" class="box a"/><text x="251" y="78" class="w mid">round_money(x)</text>
  <rect x="368" y="26" width="140" height="44" rx="12" class="box b"/><text x="438" y="53" class="w mid">summarize()</text>
  <rect x="548" y="26" width="86" height="44" rx="12" class="box"/><text x="591" y="53" class="v mid">report</text>
  <path d="M134 40 L172 24" style="stroke:var(--label2);stroke-width:2;fill:none" marker-end="url(#a3)"/>
  <path d="M134 56 L172 72" style="stroke:var(--label2);stroke-width:2;fill:none" marker-end="url(#a3)"/>
  <path d="M326 24 L364 40" style="stroke:var(--label2);stroke-width:2;fill:none" marker-end="url(#a3)"/>
  <path d="M326 72 L364 56" style="stroke:var(--label2);stroke-width:2;fill:none" marker-end="url(#a3)"/>
  <path d="M508 48 H544" style="stroke:var(--label2);stroke-width:2;fill:none" marker-end="url(#a3)"/>
</svg>"""

section("project", "Mini project: a payment batch checker",
    p("""A finance team sends a batch of payment amounts every night. Before loading it, you check it and send back a
    short summary. The amounts are floats. Some are missing (`None`), some are refunds (negative), and `0` is a real,
    valid payment. Build three functions; the tests check all three."""),
    fig(PROJECT_FIG, "Two small helpers, then one function that loops over the batch once and uses both."),
    write("Payment batch checker", "hard", key="batch-checker", tag="Project",
        prompt="""**1. `band(amount)`** returns `"refund"` for negative amounts, `"small"` for 0 up to (not including)
        100, `"medium"` for 100 up to 1000, and `"large"` for 1000 and over.

        **2. `round_money(x)`** rounds to 2 decimal places the way the finance system does: ties away from zero
        (1.1, problem 12), returning a float.

        **3. `summarize(payments, limit)`** returns a dict with:

        - `"count"`: how many amounts are present (not `None`)
        - `"missing"`: how many are `None`
        - `"total"`: the sum of the present amounts, rounded with `round_money`
        - `"bands"`: a dict of how many amounts fall in each band, with all four keys always present
        - `"first_over"`: the position in the list of the first amount above `limit`, or `None`
        - `"ok"`: `True` only if nothing is missing and nothing is above `limit`""",
        code="""
        def band(amount):
            pass


        def round_money(x):
            pass


        def summarize(payments, limit):
            pass
        """,
        tests="""
        assert band(-5) == "refund"
        assert band(0) == "small"
        assert band(99.99) == "small"
        assert band(100) == "medium"
        assert band(1000) == "large"
        assert round_money(2.675) == 2.68
        assert round_money(-0.125) == -0.13
        batch = [120.5, None, 0, -20.25, 2500, 99.99, None, 0.1, 0.2]
        report = summarize(batch, 2000)
        assert report["count"] == 7
        assert report["missing"] == 2
        assert report["total"] == 2700.54
        assert report["bands"] == {"refund": 1, "small": 4, "medium": 1, "large": 1}
        assert report["first_over"] == 4
        assert report["ok"] is False
        assert summarize([0.1, 0.2], 1)["total"] == 0.3
        assert summarize([], 100) == {"count": 0, "missing": 0, "total": 0.0, "first_over": None, "ok": True,
                                      "bands": {"refund": 0, "small": 0, "medium": 0, "large": 0}}
        assert summarize([0, 0], 100)["ok"] is True
        """,
        hints=["`band`: a guard for negatives, then chained comparisons (1.1).",
               "`round_money`: `Decimal(str(x)).quantize(Decimal(\"0.01\"), rounding=ROUND_HALF_UP)`.",
               "`summarize`: one `for i, amount in enumerate(payments)` loop. Use `is None` for missing, never `if not amount`, or the zero payments disappear.",
               "Only record `first_over` the first time: check `first_over is None` before setting it. Round the total once, at the end."],
        solution="""
        from decimal import Decimal, ROUND_HALF_UP


        def band(amount):
            if amount < 0:
                return "refund"
            if amount < 100:
                return "small"
            if amount < 1000:
                return "medium"
            return "large"


        def round_money(x):
            return float(Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


        def summarize(payments, limit):
            bands = {"refund": 0, "small": 0, "medium": 0, "large": 0}
            count = missing = 0
            total = 0.0
            first_over = None
            for i, amount in enumerate(payments):
                if amount is None:
                    missing += 1
                    continue
                count += 1
                total += amount
                bands[band(amount)] += 1
                if amount > limit and first_over is None:
                    first_over = i
            return {
                "count": count,
                "missing": missing,
                "total": round_money(total),
                "bands": bands,
                "first_over": first_over,
                "ok": missing == 0 and first_over is None,
            }
        """,
        why="""Everything from the module meets here:

        - `amount is None` rather than `if not amount`: the batch contains real zero payments (1.1, the COALESCE trap).
        - `continue` skips missing rows early, which keeps the rest of the loop flat (1.2).
        - `enumerate` gives the position for `first_over`, and the `first_over is None` check keeps the **first** one,
          like the search problems in 1.2, without stopping the loop, because the counts still need every row.
        - The raw float total of `0.1 + 0.2` is 0.30000000000000004. Rounding once at the end with a decimal
          rounding mode gives the 0.3 the finance team expects (1.1).
        - Chained comparisons are not needed in `band` because each `if` returns. The order of the checks does it.

        A real version would read the batch from a file (Module 12), raise a custom error on bad rows (Module 8) and
        come with a pytest suite (Module 13). The structure stays the same."""),
)

recap(
    "Missing is not zero: test for `None` with `is None`, and keep truthiness for real emptiness checks.",
    "Floor division, ceiling division `-(-n // k)`, and `%` cover most counting, paging and digit problems.",
    "Round money once, at the end, with `Decimal` and an explicit rounding mode. Compare floats with `isclose`.",
    "One loop with `enumerate` and `continue` can count, sum, search and band a whole batch in one pass.",
)
