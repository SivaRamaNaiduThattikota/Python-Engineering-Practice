from lesson import *

lesson(
    id="m1-1", num="1.1", title="Numbers, operators and truthiness",
    intro="Division, rounding, precedence and what counts as false. Small rules, but each one is a classic "
          "source of silent bugs in data code, and a favourite in interviews.",
    desc="Integer and float division, rounding, precedence, what counts as false, and chained comparisons.",
    keys="int float division floor modulo divmod round banker decimal isclose precedence truthy falsy and or chained comparison",
)

term("Floor division", "`a // b`: divide, then round down toward minus infinity. `-7 // 2` is -4, not -3.")
term("Banker's rounding", "Round half to even, which is what Python's `round()` does: `round(2.5)` is 2, `round(3.5)` is 4.")
term("Truthy / falsy", "How a value behaves in an `if`. Falsy: None, False, any zero, and empty containers. Everything else is truthy.")
term("Chained comparison", "`a < b < c` means `a < b and b < c`, with `b` evaluated once.")
term("Short-circuit", "`and` / `or` stop as soon as the answer is known and return that operand, not True or False.")

NUMBER_LINE = """
<svg viewBox="0 0 640 132" role="img" aria-label="-7 / 2 is -3.5. Floor division goes down to -4, int() goes toward zero to -3.">
  <defs><marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M0 0 L10 5 L0 10 z" style="fill:var(--accent)"/></marker>
    <marker id="ah2" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M0 0 L10 5 L0 10 z" style="fill:var(--orange)"/></marker></defs>
  <line x1="30" y1="62" x2="610" y2="62" style="stroke:var(--label3);stroke-width:2"/>
  <line x1="40" y1="56" x2="40" y2="68" style="stroke:var(--label3);stroke-width:2"/><text x="40" y="88" class="mid">-5</text>
  <line x1="152" y1="56" x2="152" y2="68" style="stroke:var(--label3);stroke-width:2"/><text x="152" y="88" class="mid">-4</text>
  <line x1="264" y1="56" x2="264" y2="68" style="stroke:var(--label3);stroke-width:2"/><text x="264" y="88" class="mid">-3</text>
  <line x1="376" y1="56" x2="376" y2="68" style="stroke:var(--label3);stroke-width:2"/><text x="376" y="88" class="mid">-2</text>
  <line x1="488" y1="56" x2="488" y2="68" style="stroke:var(--label3);stroke-width:2"/><text x="488" y="88" class="mid">-1</text>
  <line x1="600" y1="56" x2="600" y2="68" style="stroke:var(--label3);stroke-width:2"/><text x="600" y="88" class="mid">0</text>
  <circle cx="208" cy="62" r="6" style="fill:var(--accent)"/><text x="208" y="88" class="v mid">-3.5</text>
  <path d="M200 40 H160" style="stroke:var(--accent);stroke-width:2.5;fill:none" marker-end="url(#ah)"/>
  <text x="152" y="26" class="v">-7 // 2 = -4 (floor: always down)</text>
  <path d="M216 108 H256" style="stroke:var(--orange);stroke-width:2.5;fill:none" marker-end="url(#ah2)"/>
  <text x="270" y="113" class="v">int(-7 / 2) = -3 (truncate: toward zero, like SQL Server)</text>
</svg>"""

section("rules", "The rules in one screen",
    p("""Three number types cover daily work: `int` (whole numbers with no size limit), `float` (64-bit binary,
    about 15 to 16 significant digits) and `bool`, which is a kind of int: `True` is 1 and `False` is 0."""),
    ex("""
    print(7 / 2, 7 // 2, 7 % 2)
    print(-7 / 2, -7 // 2, -7 % 2)
    print(divmod(-7, 2))
    print(int(-3.5))
    """, "division.py"),
    p("""`/` always gives a float. `//` **floors**: it rounds toward minus infinity, not toward zero. `%` follows
    the same rule, so `(a // b) * b + a % b == a` is always true and the remainder takes the sign of the divisor.
    `int()` on a float just cuts off the decimals, which moves toward zero."""),
    fig(NUMBER_LINE, "The same -3.5 gives two different whole numbers depending on which way you round."),
    callout("key", "Step by step: why -7 // 2 is -4", """
    - **Step 1, divide exactly.** `-7 / 2` is `-3.5`.
    - **Step 2, floor it.** Floor means "the nearest whole number that is **less than or equal to** it". The two
      whole numbers around -3.5 are -4 and -3. Which one is smaller? -4, because on the number line it is further
      left. So the answer is -4. For negative numbers, "down" moves **away** from zero.
    - **Step 3, the remainder fills the gap.** `-7 % 2` is whatever makes `2 * (-7 // 2) + (-7 % 2) == -7` true:
      `2 * -4` is -8, and -8 needs **+1** to get back to -7. So `-7 % 2` is 1.
    - **Compare with positive 7.** `7 / 2` is 3.5, the whole numbers around it are 3 and 4, and the smaller is 3.
      So `7 // 2` is 3. Same rule both times: always pick the smaller neighbour."""),
    callout("sql", "SQL / Power BI", """In SQL Server, integer division truncates: `-7 / 2` is `-3`. Python's `-7 // 2` is `-4`.
    Port a bucketing or week-number calculation from SQL and negative values land in a different bucket.
    In DAX, `INT()` rounds down like `//`, and `TRUNC()` behaves like `int()`."""),
    ex("""
    import math
    print(0.1 + 0.2)
    print(0.1 + 0.2 == 0.3, math.isclose(0.1 + 0.2, 0.3))
    print(round(2.5), round(3.5), round(-2.5))
    print(round(2.675, 2))
    """, "floats.py"),
    p("""Floats are stored in binary, so 0.1 is already slightly off before you add anything. Never compare floats
    with `==`. Use `math.isclose` (in numpy `np.isclose`, in tests `pytest.approx`). `round()` rounds a tie to the
    nearest even number, called **banker's rounding**. And 2.675 is really stored as 2.67499999..., so it rounds down."""),
    callout("sql", "Matching a SQL or Excel report", """`ROUND(2.5, 0)` gives 3 in SQL Server and in Excel: both round
    a tie away from zero. Python gives 2. When a Python number has to match a finance report to the cent, use
    `decimal.Decimal` with `ROUND_HALF_UP` (problem 12)."""),
    ex("""
    print(-2 ** 2, 2 ** 3 ** 2)
    print(1 < 2 < 3, 3 > 2 > 2)
    print(not 1 == 2)
    """, "precedence.py"),
    p("""`**` binds tighter than the minus sign in front of it, and it groups right to left: `2 ** 3 ** 2` is
    `2 ** 9`. Comparisons chain: `a < b < c` means `a < b and b < c`. `not` is weaker than `==`, so
    `not 1 == 2` is `not (1 == 2)`."""),
    ex("""
    for v in [0, 0.0, "", [], {}, None, "0", " ", [0], -1]:
        # Inside {v!r:>5} there are two formatting instructions:
        #   !r   show v the way you would type it in code (its repr),
        #        so the string "0" prints as '0' with quotes, and "" as ''.
        #        Without !r, "" and " " would print as nothing at all.
        #   :>5  make it 5 characters wide, pushed to the right (>),
        #        so all the arrows line up in one column.
        print(f"{v!r:>5} -> {bool(v)}")
    """, "truthiness.py"),
    p("""In the f-string, `!r` shows each value as its **repr**, the form you would type in code, so `"0"` appears as
    `'0'` and the empty string as `''`. Without `!r`, the empty string and the space would print as blanks and you
    could not tell them apart. `:>5` pads the text to 5 characters, aligned right. Compare `print(f"{'0'}")`, which
    prints `0`, with `print(f"{'0'!r}")`, which prints `'0'`. Strings (Module 4) covers f-string formatting fully."""),
    p("""Falsy means "acts as False in an `if`": `None`, `False`, zero of any number type, and empty containers.
    Everything else is truthy, including the string `"0"`, a space, and a list holding a zero."""),
    ex("""
    print(0 or "default")
    print("" and 5)
    print(3 and 4)
    print(None or 0 or [])
    """, "and_or.py"),
    p("""`and` and `or` return one of their operands, not `True` or `False`. `or` returns the first truthy value
    (or the last one if none are). `and` returns the first falsy value (or the last one). Both stop early, which
    is called **short-circuit** evaluation."""),
    callout("warn", "The COALESCE trap", """`x or default` looks like SQL's `COALESCE(x, default)`, but COALESCE only
    replaces NULL. `or` also replaces `0`, `""` and `[]`, which are often valid values. The real COALESCE is
    `default if x is None else x`."""),
)

section("warmup", "Warm-up",
    predict("Division with negative numbers", "easy",
        code="""
        print(17 // 5, 17 % 5)
        print(-17 // 5, -17 % 5)
        print(17 // -5, 17 % -5)
        """,
        hints=["Work out the true quotient first (-3.4), then round it toward minus infinity.",
               "The remainder is whatever makes `(a // b) * b + a % b == a` true."],
        why="""`-17 / 5` is -3.4, and floor goes down to -4. Then the remainder must satisfy `-4 * 5 + r == -17`,
        so `r` is 3. In the last line `17 / -5` is also -3.4, floor is -4, and `-4 * -5 + r == 17` gives `r = -3`.
        The remainder always has the sign of the divisor."""),
    predict("Which values are kept?", "easy",
        code="""
        values = [0, "0", [], [[]], 0.0, "False", None]
        print([v for v in values if v])
        """,
        hints=["Only empty containers, zeros, None and False are falsy. Check each one against that list."],
        why="""`"0"` and `"False"` are non-empty strings, so they are truthy. `[[]]` is a list with one item in it
        (that item happens to be an empty list), so it is not empty. The rest are falsy."""),
    predict("and / or return a value", "easy",
        code="""
        print(5 or 0)
        print(0 and 5)
        print("" or "n/a")
        print([] and [1])
        print(None or False)
        """,
        hints=["`or` gives back the first truthy operand, `and` the first falsy one. If no operand settles it, you get the last one."],
        why="""`5 or 0`: 5 is truthy, stop, return 5. `0 and 5`: 0 is falsy, stop, return 0. `"" or "n/a"`: the empty
        string is falsy, so it moves on and returns `"n/a"`. `[] and [1]` stops at `[]`. `None or False`: both are falsy,
        so it returns the last one, `False`."""),
    write("Even or odd", "easy",
        prompt="Write `is_even(n)` that returns `True` for even integers and `False` for odd ones. It must work for 0 and negative numbers.",
        code="""
        def is_even(n):
            pass
        """,
        tests="""
        assert is_even(4) is True
        assert is_even(7) is False
        assert is_even(0) is True
        assert is_even(-3) is False
        assert is_even(-10) is True
        """,
        hints=["What is the remainder when an even number is divided by 2?"],
        solution="""
        def is_even(n):
            return n % 2 == 0
        """,
        why="""`n % 2` is 0 for even numbers and 1 for odd ones, also for negatives, because the remainder takes the
        sign of the divisor (2). In C or Java, `-3 % 2` is -1, so the common check `n % 2 == 1` for "odd" breaks there
        on negatives. In Python it is safe, but `n % 2 == 0` is safe everywhere."""),
    write("Minutes to hours and minutes", "easy",
        prompt="""Write `split_minutes(total)` that returns a tuple `(hours, minutes)`. For example 135 minutes is
        `(2, 15)`. This is the kind of helper you write when turning event durations into features.""",
        code="""
        def split_minutes(total):
            pass
        """,
        tests="""
        assert split_minutes(135) == (2, 15)
        assert split_minutes(0) == (0, 0)
        assert split_minutes(59) == (0, 59)
        assert split_minutes(60) == (1, 0)
        """,
        hints=["Hours come from `//`, minutes from `%`.", "There is a built-in that does both at once and returns a tuple."],
        solution="""
        def split_minutes(total):
            return divmod(total, 60)
        """,
        why="""`divmod(a, b)` returns `(a // b, a % b)` in one call. Writing `(total // 60, total % 60)` is also right.
        `divmod` says what you mean and does the division once."""),
)

section("medium", "Medium",
    fix("The total that never matches", "medium", tag="Data work",
        prompt="""A reconciliation script checks that two amounts add up to an expected total. It reports a mismatch
        for `0.1 + 0.2` against `0.3`. Fix `totals_match` so it compares the way floats should be compared.""",
        code="""
        def totals_match(a, b, expected):
            return a + b == expected
        """,
        tests="""
        assert totals_match(0.1, 0.2, 0.3)
        assert totals_match(1.5, 2.5, 4.0)
        assert not totals_match(0.1, 0.2, 0.31)
        assert totals_match(0.3, -(0.1 + 0.2), 0.0)
        """,
        hints=["Look in the `math` module for a function that compares with a tolerance.",
               "The last test compares against 0.0. A relative tolerance of a tiny number around zero is still tiny. Check the `abs_tol` argument."],
        solution="""
        import math

        def totals_match(a, b, expected):
            return math.isclose(a + b, expected, abs_tol=1e-9)
        """,
        why="""`math.isclose` uses a relative tolerance by default (`rel_tol=1e-09`), meaning "within a billionth of the
        size of the numbers". Near zero that window shrinks to nothing: `0.3 - (0.1 + 0.2)` is about -5.6e-17, and no relative
        tolerance of 0.0 accepts that. `abs_tol` adds a fixed floor, which you need for anything that should be 0,
        like a residual or a difference. For money, the real fix is to store cents as `int` or use `Decimal`."""),
    fix("A discount of zero", "medium", tag="Data work",
        prompt="""`final_price` should apply a 10% discount when no discount is given, and the given discount otherwise.
        A customer with a 0% discount is getting 10% off. Fix it.""",
        code="""
        def final_price(price, discount_pct=None):
            pct = discount_pct or 10   # 10% when no discount is given
            return round(price * (1 - pct / 100), 2)
        """,
        tests="""
        assert final_price(100) == 90.0
        assert final_price(100, 25) == 75.0
        assert final_price(100, 0) == 100.0
        """,
        hints=["What does `0 or 10` return?", "You want to replace only `None`, the way COALESCE replaces only NULL."],
        solution="""
        def final_price(price, discount_pct=None):
            pct = 10 if discount_pct is None else discount_pct
            return round(price * (1 - pct / 100), 2)
        """,
        why="""`0 or 10` is 10 because 0 is falsy. "Missing" and "zero" are different things, so test for `None` directly.
        The same bug shows up in pandas as `df["x"].fillna(...)` versus `df["x"].replace(0, ...)`: decide which one you mean."""),
    trace("Digit sum, step by step", "medium",
        prompt="Fill in `n` and `total` after each pass of the loop.",
        code="""
        n = 4073
        total = 0
        step = 0
        while n > 0:
            step += 1
            total += n % 10
            n //= 10  # row: f"after pass {step}"
        """,
        trace_vars=["n", "total"],
        hints=["`n % 10` is the last digit, `n // 10` drops the last digit."],
        why="""Each pass peels off the last digit with `% 10` and removes it with `// 10`: 3, then 7, then 0, then 4.
        The loop stops when `n` reaches 0. This pattern (digit by digit with `%` and `//`) is the base of many interview
        problems: reversing a number, checking palindromes, converting bases."""),
    write("Age bands", "medium",
        prompt="""Write `age_band(age)` that returns `"child"` under 13, `"teen"` for 13 to 17, `"adult"` for 18 to 64,
        `"senior"` for 65 and over, and `"invalid"` for negative ages. Use chained comparisons like `13 <= age < 18`.
        This is a `CASE WHEN` column in SQL, or a bins / groups column in Power BI.""",
        code="""
        def age_band(age):
            pass
        """,
        tests="""
        assert age_band(-1) == "invalid"
        assert age_band(0) == "child"
        assert age_band(12) == "child"
        assert age_band(13) == "teen"
        assert age_band(17) == "teen"
        assert age_band(18) == "adult"
        assert age_band(64) == "adult"
        assert age_band(65) == "senior"
        """,
        hints=["Write one condition per band, top to bottom. Each band is `low <= age < high`."],
        solution="""
        def age_band(age):
            if age < 0:
                return "invalid"
            if age < 13:
                return "child"
            if 13 <= age < 18:
                return "teen"
            if 18 <= age < 65:
                return "adult"
            return "senior"
        """,
        why="""Half-open ranges (`low <= age < high`) never overlap and never leave gaps, the same reason pandas
        `pd.cut` and most binning tools use them. Since each `if` returns, the lower bounds are not strictly needed
        (`if age < 18` would do), but writing the full range keeps each line readable on its own. The boundary tests
        (12, 13, 17, 18, 64, 65) are where band code usually breaks."""),
    choose("Sum of 1 to n", "medium",
        prompt="Each option computes the sum 1 + 2 + ... + n. Which is fastest for `n = 100_000`?",
        setup="n = 100_000",
        options={
            "a": "total = 0\nfor i in range(1, n + 1):\n    total += i",
            "b": "total = sum(range(1, n + 1))",
            "c": "total = n * (n + 1) // 2",
        },
        answer="c",
        hints=["Count how many steps each one takes as `n` grows."],
        why="""C does a fixed amount of work whatever `n` is: O(1). A and B both touch every number: O(n). B beats A
        because the loop inside `sum` runs in C, while A runs the Python interpreter for each `+=`. The ranking
        **between** A and B is a constant factor; the jump to C is a different growth rate. Module 16 builds on this."""),
    refactor("Clean up the checks", "medium",
        prompt="""This works but is clumsy. Rewrite it in clean, idiomatic Python. Keep the tests green.""",
        code="""
        def describe(items):
            if len(items) == 0:
                return "empty"
            else:
                if len(items) > 0 and items[0] == None:
                    return "starts with None"
                else:
                    return "has " + str(len(items)) + " items"
        """,
        tests="""
        assert describe([]) == "empty"
        assert describe(()) == "empty"
        assert describe([None, 1]) == "starts with None"
        assert describe([1, 2]) == "has 2 items"
        """,
        hints=["An empty sequence is falsy.", "Each branch returns, so the `else` blocks are not needed.", "Compare with `None` using `is`."],
        solution="""
        def describe(items):
            if not items:
                return "empty"
            if items[0] is None:
                return "starts with None"
            return f"has {len(items)} items"
        """,
        why="""`if not items` is the normal way to test for empty. After the first `return`, `len(items) > 0` is
        already known, and the `else` blocks only add indentation. Use `is None` because `None` is a single object,
        and `==` can be redefined: on a numpy array or pandas Series, `== None` compares element by element and does not
        give one True or False. One exception to `if not items`: a numpy array refuses to be used as a bool, so for arrays
        write `if arr.size == 0`."""),
)

section("hard", "Hard",
    write("Round like Excel", "hard", tag="Data work",
        prompt="""Write `round_half_up(x, digits=0)` that rounds the way Excel and SQL Server do: ties go away
        from zero. Return a float. `round_half_up(2.675, 2)` must give 2.68, even though `round(2.675, 2)` gives 2.67.""",
        code="""
        def round_half_up(x, digits=0):
            pass
        """,
        tests="""
        assert round_half_up(2.5) == 3.0
        assert round_half_up(-2.5) == -3.0
        assert round_half_up(2.675, 2) == 2.68
        assert round_half_up(1.005, 2) == 1.01
        assert round_half_up(0.125, 2) == 0.13
        assert round_half_up(7.0) == 7.0
        """,
        hints=["The `decimal` module has a rounding mode called `ROUND_HALF_UP`.",
               "`Decimal(2.675)` copies the binary error. `Decimal(str(2.675))` starts from the text you see.",
               "`Decimal.quantize(Decimal('0.01'), rounding=...)` rounds to two places."],
        solution="""
        from decimal import Decimal, ROUND_HALF_UP

        def round_half_up(x, digits=0):
            step = Decimal(1).scaleb(-digits)        # 0 -> 1, 2 -> 0.01
            d = Decimal(str(x)).quantize(step, rounding=ROUND_HALF_UP)
            return float(d)
        """,
        why="""Two separate problems hide here. First, `round` uses banker's rounding, so `round(2.5)` is 2.
        Second, the float 2.675 is really 2.67499999..., so any rounding of the float itself goes down. Going through
        `str(x)` gives the short decimal text Python prints (`'2.675'`), and `Decimal` then does exact decimal
        arithmetic. `ROUND_HALF_UP` in the decimal module means "ties away from zero", so -2.5 becomes -3."""),
    write("Min-max scaling", "hard", tag="ML",
        prompt="""Write `minmax_scale(xs)` that rescales a list of numbers to the range 0 to 1:
        `(x - min) / (max - min)`. An empty list gives `[]`. If every value is the same, return all `0.0` instead
        of dividing by zero.""",
        code="""
        def minmax_scale(xs):
            pass
        """,
        tests="""
        import math
        assert minmax_scale([10, 20, 30]) == [0.0, 0.5, 1.0]
        assert minmax_scale([5, 5, 5]) == [0.0, 0.0, 0.0]
        assert minmax_scale([]) == []
        assert minmax_scale([-1, 1]) == [0.0, 1.0]
        assert all(math.isclose(a, b) for a, b in zip(minmax_scale([0.1, 0.2, 0.3]), [0.0, 0.5, 1.0]))
        """,
        hints=["Handle the empty list first, before calling `min` or `max` (they fail on empty input).",
               "Compute `span = max - min` once. If it is 0, every output is 0.0."],
        solution="""
        def minmax_scale(xs):
            if not xs:
                return []
            lo, hi = min(xs), max(xs)
            span = hi - lo
            if span == 0:
                return [0.0] * len(xs)
            return [(x - lo) / span for x in xs]
        """,
        why="""This is what scikit-learn's `MinMaxScaler` does per column, including the constant-column case:
        it outputs zeros instead of dividing by zero. Note the last test: `0.2` scaled is 0.5000000000000001, not 0.5,
        so it must use `isclose`. `span == 0` is a safe float comparison here because subtracting a number from itself
        is exactly 0."""),
    write("Convert to any base", "hard", tag="Interview",
        prompt="""Write `to_base(n, base)` that returns the integer `n` written in `base` (2 to 36) as a string,
        using digits `0-9` then `a-z`. Handle 0 and negative numbers. Do not use `bin`, `hex` or `format`.""",
        code="""
        def to_base(n, base):
            pass
        """,
        tests="""
        assert to_base(0, 2) == "0"
        assert to_base(10, 2) == "1010"
        assert to_base(255, 16) == "ff"
        assert to_base(35, 36) == "z"
        assert to_base(-10, 2) == "-1010"
        assert int(to_base(123456, 7), 7) == 123456
        """,
        hints=["`divmod(n, base)` gives the next quotient and the last digit.",
               "The digits come out last first, so collect them and reverse.",
               "Deal with the sign once at the start: work on `abs(n)`."],
        solution="""
        DIGITS = "0123456789abcdefghijklmnopqrstuvwxyz"

        def to_base(n, base):
            if n == 0:
                return "0"
            sign = "-" if n < 0 else ""
            n = abs(n)
            out = []
            while n:
                n, r = divmod(n, base)
                out.append(DIGITS[r])
            return sign + "".join(reversed(out))
        """,
        why="""It is the digit-sum loop from the trace problem with `base` instead of 10. Taking `abs(n)` first matters:
        `divmod(-10, 2)` floors, so on a negative number the remainders come out in a form you do not want. Building a
        list and joining once is the standard way to build a string (Module 4 shows why `+=` in a loop is slower).
        The last test checks against Python's own `int(s, base)`, a good habit: test your code against a trusted version."""),
    predict("Precedence and chaining", "hard",
        code="""
        print(-3 ** 2)
        print(2 ** -1)
        print(1 < 3 > 2)
        print(1 == 1.0 == True)
        print(True + True * 2)
        print(10 - 2 - 3, 2 ** 2 ** 3)
        """,
        hints=["`**` happens before the unary minus, and `**` groups right to left.",
               "`a < b > c` is `a < b and b > c`. `True` equals 1."],
        why="""`-3 ** 2` is `-(3 ** 2)` = -9. `2 ** -1` is 0.5, a float. `1 < 3 > 2` is `1 < 3 and 3 > 2`. `1 == 1.0 == True`
        is `1 == 1.0 and 1.0 == True`, both true since `True` is 1. `True + True * 2` is `1 + 2` = 3. Subtraction groups
        left to right, `(10 - 2) - 3` = 5, but `**` groups right to left: `2 ** (2 ** 3)` = 256."""),
)

section("interview", "Interview questions",
    explain("When is `x or default` wrong?", "easy", tag="Interview",
        prompt="Say your answer out loud or write it down, then compare.",
        why="""When a falsy value is a valid input. `or` replaces every falsy value: 0, 0.0, `""`, `[]`, `{}`, not just
        `None`. So `timeout or 30` turns a timeout of 0 into 30, and `name or "unknown"` turns an empty string into
        `"unknown"`. If only "missing" should get the default, write `default if x is None else x`. Mention that it
        is SQL's `COALESCE` that `is None` matches, not `or`."""),
    explain("Why is `0.1 + 0.2 != 0.3`, and how do you test float code?", "medium", tag="Interview",
        why="""Floats are binary fractions. 0.1 has no exact binary form (like 1/3 has no exact decimal form), so it is
        stored as the nearest binary value, and the small errors add up: `0.1 + 0.2` is 0.30000000000000004.
        In code, compare with a tolerance: `math.isclose`, `numpy.isclose` / `numpy.allclose` for arrays, and
        `pytest.approx` in tests. For money, use integer cents or `decimal.Decimal`. Bonus point: in ML this is why you
        check a loss or a gradient with `allclose`, never `==`."""),
    explain("`-7 // 2` versus `int(-7 / 2)`", "medium", tag="Interview",
        why="""`-7 // 2` is -4: floor division rounds toward minus infinity. `int(-7 / 2)` is -3: `-7 / 2` is -3.5, and
        `int` truncates toward zero. They agree for positive numbers and differ for negatives. Python chose floor so that
        `a % b` has the sign of `b` and `(a // b) * b + a % b == a` holds. That makes `%` safe for wrapping things like
        hours on a clock or array indexes even with negative inputs. C, Java and SQL Server truncate."""),
    explain("`bool` is a subclass of `int`. Where does that help, and where does it bite?", "hard", tag="Interview",
        why="""It helps for counting: `sum(x > 0 for x in xs)` counts matches, and in pandas `(df["x"] > 0).sum()` and
        `.mean()` give the count and the share of rows. It bites in validation: `isinstance(True, int)` is True, so code
        that checks "is this an int" accepts `True`; check `type(x) is int` or exclude bool explicitly. It also bites in
        dict keys: `True == 1` and they hash the same, so `{1: "a", True: "b"}` is `{1: "b"}`."""),
)

recap(
    "`/` gives a float. `//` floors toward minus infinity, and `%` takes the sign of the divisor. `int()` truncates toward zero.",
    "Never compare floats with `==`: use `math.isclose`, `np.isclose` or `pytest.approx`. Add `abs_tol` near zero.",
    "`round()` is banker's rounding. To match Excel or SQL Server, use `Decimal(str(x))` with `ROUND_HALF_UP`.",
    "`**` beats unary minus and groups right to left. Comparisons chain. `not` is weaker than `==`.",
    "Falsy: None, False, zeros, empty containers. `and` / `or` return an operand, and `or` is not COALESCE.",
)
