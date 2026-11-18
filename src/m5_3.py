from lesson import *

lesson(
    id="m5-3", num="5.3", title="f-strings and formatting",
    intro="How f-strings evaluate, the format-spec mini-language part by part (width, alignment, precision, separators, "
          "types), how formatting rounds, dates, the other formatting tools and when each is right, and why logs should "
          "not use f-strings.",
    desc="Width, alignment, precision, `!r`, thousands separators, dates.",
    keys="f-string format spec mini language width align fill precision thousands separator percent exponent general format type conversion repr debug equals strftime isoformat str.format format_map percent formatting template logging lazy",
)

term("f-string", "A string literal prefixed with `f` whose `{...}` fields are Python expressions, evaluated when the line runs and inserted as text.")
term("Format spec", "The part after `:` in a field, such as `>10.2f`: fill, alignment, sign, width, grouping, precision and type.")
term("Conversion", "`!r`, `!s` or `!a` before the format spec: format `repr(x)`, `str(x)` or `ascii(x)` instead of `x`.")
term("Lazy formatting", "Passing values to a logger separately (`log.info(\"x=%s\", x)`) so the text is only built if the message is actually emitted.")

section("fstrings", "f-strings: expressions inside text",
    p("""An f-string is a string literal with an `f` prefix. Each `{...}` field holds a **Python expression**: a name, an
    arithmetic expression, a function call, an index, a conditional expression. Step by step, when the line runs, Python
    evaluates each expression, converts the result to text (by calling `format(value, spec)`, which usually means `str`), and
    joins the pieces. It happens **every time the line runs**, and only then: an f-string is not a template that can be filled
    later (problem 12)."""),
    ex("""
    model, tokens, price = "small", 1234, 0.15
    print(f"{model} used {tokens} tokens costing ${tokens * price / 1000:.4f}")
    docs = [{"id": "faq"}, {"id": "terms"}]
    print(f"top doc: {docs[0]['id']}, total {len(docs)}, {'ok' if tokens < 4000 else 'too long'}")
    print(f"{{literal braces}} and a value: {tokens}")
    """, "fstring_basics.py"),
    p("""To put a literal `{` or `}` in an f-string, double it: `{{` and `}}`. That matters for prompts that contain JSON
    examples (problem 3). Since Python 3.12 you can also reuse the same quote character inside a field
    (`f"{d["id"]}"`), but code that must run on older versions should use the other quote type."""),
    p("""Two field features are especially useful. A **conversion** `!r` formats `repr(value)` instead of `str(value)`, which
    shows quotes and escape characters, so stray spaces and newlines become visible in logs (5.1). And the **`=` specifier**
    (`f"{x=}"`) prints the expression's text, an equals sign and its value: the fastest debugging print there is."""),
    ex("""
    label = "spam "
    print(f"[{label}]", f"[{label!r}]")
    tokens, limit = 4200, 4096
    print(f"{tokens=}, {limit=}, {tokens > limit=}")
    print(f"{tokens / limit = :.2f}")
    """, "debug_specifier.py"),
)

section("spec", "The format spec, part by part",
    p("""After the colon in a field comes the **format spec**, a small language with a fixed order:
    `[[fill]align][sign][#][0][width][grouping][.precision][type]`. Every part is optional. Reading a spec left to right:"""),
    html("""<div class="tbl"><table>
      <tr><th>Part</th><th>Examples</th><th>Meaning</th></tr>
      <tr><td>fill + align</td><td><code>&lt;</code> <code>&gt;</code> <code>^</code>, <code>*^</code></td><td>left, right, centre; an optional fill character before the alignment</td></tr>
      <tr><td>sign</td><td><code>+</code>, <code>-</code>, space</td><td>always show the sign; only for negatives (default); a space for positives</td></tr>
      <tr><td>width</td><td><code>10</code>, <code>08</code></td><td>minimum total width; a leading <code>0</code> pads numbers with zeros after the sign</td></tr>
      <tr><td>grouping</td><td><code>,</code> <code>_</code></td><td>thousands separators</td></tr>
      <tr><td>precision</td><td><code>.2</code></td><td>digits after the point (<code>f</code>, <code>%</code>, <code>e</code>), significant digits (<code>g</code>), or maximum length for strings</td></tr>
      <tr><td>type</td><td><code>f</code> <code>e</code> <code>g</code> <code>%</code> <code>d</code> <code>x</code> <code>b</code> <code>s</code></td><td>fixed point, exponent, general, percentage, integer, hex, binary, string</td></tr>
    </table></div>"""),
    ex("""
    x = 1234567.891
    print(f"[{x:,.2f}] [{x:_.0f}] [{x:.3e}] [{x:.3g}]")
    print(f"[{0.4567:.1%}] [{-3:05d}] [{42:+d}] [{255:#x}] [{5:08b}]")
    print(f"[{'left':<10}] [{'right':>10}] [{'mid':^10}] [{'mid':*^10}]")
    print(f"[{'a long description':.8}] [{'cut':>6.2}]")
    width = 12
    print(f"[{x:>{width},.1f}]")       # a nested field supplies part of the spec
    """, "format_spec.py"),
    p("""A few rules worth remembering. Numbers right-align by default and strings left-align. Width is a **minimum**: a value
    longer than the width is never cut, except strings with a precision (`.8` keeps the first 8 characters). The `g` type
    picks fixed or exponent notation depending on the size and drops trailing zeros. A nested `{width}` inside the spec lets
    you compute alignment at run time, which is how aligned tables of unknown widths are built (problem 14)."""),
    callout("sql", "SQL / Power BI", """The format spec is Python's version of Excel and Power BI format strings: `:,.2f` is
    `#,##0.00`, `:.1%` is `0.0%`, `:08d` is `00000000`. Like those, formatting changes only the **text**, never the stored
    value, so format at the very end, in the report, not in the data."""),
)

section("rounding", "How formatting rounds",
    p("""Precision **rounds** (it never truncates), and it rounds the exact binary value of the float, with ties to even. So
    formatting shows the same surprises as `round` in 1.1: `2.675` is stored as 2.67499999..., so `f"{2.675:.2f}"` is `"2.67"`,
    and exact halves like 0.5 and 2.5 go to the even neighbour. For displaying measurements this is fine. For **money**, where a
    report must match an accounting system to the cent, round with `Decimal` first (1.1, problem 12) and then format."""),
    ex("""
    from decimal import Decimal, ROUND_HALF_UP

    print(f"{2.675:.2f} {0.5:.0f} {1.5:.0f} {2.5:.0f}")
    amount = Decimal("2.675").quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    print(f"{amount}", f"{amount:,.2f}", f"{Decimal('1234567.5'):,.2f}")
    print(f"{0.1 + 0.2}", f"{0.1 + 0.2:.2f}", f"{1e-7:.3f}", f"{1e-7:.3g}")
    """, "rounding.py"),
    p("""The last line shows two more things: formatting is the right way to hide float noise (`0.30000000000000004` displays as
    `0.30`), and fixed-point formatting of a tiny number can show `0.000` and hide that it is not zero, where `g` or `e` keeps
    the information. Pick `f` for amounts and percentages of normal size, `g` or `e` for values that span many magnitudes,
    such as learning rates and p-values."""),
)

section("dates", "Dates and times",
    p("""`datetime` objects have their own format codes, the same as `strftime`, and an f-string field passes them through:
    `f"{dt:%Y-%m-%d %H:%M}"`. For machine-readable text (logs, APIs, file names that must sort), use ISO 8601,
    `dt.isoformat()`, which sorts correctly as text and includes the time zone offset when the datetime has one. Never build
    dates by concatenating numbers: `f"{d.year}-{d.month}-{d.day}"` gives `2025-6-1`, which neither sorts nor parses
    reliably."""),
    ex("""
    from datetime import datetime, timezone

    dt = datetime(2025, 6, 1, 9, 5, 7, tzinfo=timezone.utc)
    print(f"{dt:%Y-%m-%d %H:%M:%S}", f"{dt:%d %b %Y}", f"{dt:%A}")
    print(dt.isoformat(), f"{dt.year}-{dt.month}-{dt.day}")
    print(sorted(["2025-10-01", "2025-9-30", "2025-09-30"]))
    """, "dates.py"),
)

section("tools", "The other formatting tools, and when to use each",
    p("""Python has four ways to put values into text. They overlap, but each has a job:"""),
    p("""- **f-strings**: your own code, values known at that line. Fastest and most readable.
    - **`str.format` / `format_map`**: a template that is defined in one place and **filled later**, such as a prompt
      template loaded from a file (`template.format_map(values)`, 5.2). The template must be trusted: `format` can read
      attributes of the values.
    - **`%` formatting**: mostly legacy, but still the standard for **logging**, because the logger only builds the message
      if it will actually be emitted.
    - **`string.Template`**: templates written by **users** or non-programmers. Its `$name` syntax cannot evaluate
      expressions or read attributes, and `safe_substitute` leaves unknown names alone instead of raising."""),
    ex("""
    import logging
    from string import Template

    prompt = "Answer in {lang}: {question}"
    print(prompt.format(lang="French", question="Refund time?"))
    print("%-8s|%6.2f|%03d" % ("small", 3.14159, 7))

    user_tpl = Template("Dear $name, your ticket $ticket is $status.")
    print(user_tpl.safe_substitute(name="Ana", ticket="T-42"))

    log = logging.getLogger("demo")
    log.debug("expensive value: %s", list(range(5)))    # not formatted at all: DEBUG is off
    """, "tools.py"),
    callout("warn", "Why not log with f-strings", """`log.debug(f"state: {big_object}")` builds the string (calling `repr` of
    `big_object`) even when debug logging is off, every time the line runs. `log.debug("state: %s", big_object)` passes the
    value along, and the text is only built if the message is emitted. Log aggregators can also group messages by their
    unchanged template. In hot paths the difference is large (problem 8)."""),
)

section("warmup", "Warm-up",
    predict("Format specs for numbers", "easy",
        code="""
        revenue = 1234567.891
        rate = 0.04567
        print(f"{revenue:,.2f} | {revenue:.0f} | {revenue:,.0f}")
        print(f"{rate:.1%} | {rate:.3f} | {rate:.2e}")
        print(f"[{42:5d}] [{42:<5d}] [{42:05d}] [{-42:05d}]")
        print(f"[{'id':>6}] [{3.14159:8.3f}] [{7:^7}]")
        """,
        hints=["`,` adds thousands separators, `%` multiplies by 100, a leading `0` in the width pads with zeros after the sign."],
        why="""`,.2f` groups thousands and keeps two decimals; `.0f` rounds to a whole number. `.1%` multiplies by 100 and adds
        the sign: 4.6%. Numbers are right-aligned by default, `<` overrides that, and zero-padding goes after the minus sign
        (`-0042`). Strings are left-aligned by default, so `>6` is needed to right-align `"id"`. A width of 8 with `.3f` gives
        `   3.142`."""),
    write("Human-readable file sizes", "easy", tag="Data work",
        prompt="""Write `human_size(n)` for a number of bytes, returning `"999 B"` below 1024, otherwise the value divided by
        1024 as many times as needed (KB, MB, GB, TB) with one decimal: `"1.5 KB"`, `"2.0 MB"`. Stop at TB.""",
        code="""
        def human_size(n):
            pass
        """,
        tests="""
        assert human_size(0) == "0 B" and human_size(999) == "999 B" and human_size(1023) == "1023 B"
        assert human_size(1536) == "1.5 KB"
        assert human_size(2 * 1024 ** 2) == "2.0 MB"
        assert human_size(5 * 1024 ** 5) == "5120.0 TB"
        """,
        hints=["Loop over the units, dividing while the value is at least 1024 and there is a bigger unit left."],
        solution="""
        def human_size(n):
            if n < 1024:
                return f"{n} B"
            value = n / 1024
            for unit in ["KB", "MB", "GB", "TB"]:
                if value < 1024 or unit == "TB":
                    return f"{value:.1f} {unit}"
                value /= 1024
        """,
        why="""Each pass divides by 1024 and moves to the next unit; the `unit == "TB"` check stops at the largest unit instead of
        running out of names. Bytes stay integers, everything else gets one decimal with `:.1f`. (Strictly, powers of 1024 are
        KiB, MiB and so on; many tools say KB anyway. Disk vendors use 1000, so pick one and label it.)"""),
    fix("A prompt with a JSON example", "easy", tag="GenAI",
        prompt="""`make_prompt` should insert the question and show the model the JSON shape to answer in. The first version
        printed the placeholder names literally; after adding `f`, it crashes with an error about the braces. Fix it so the
        output is exactly what the test expects.""",
        code="""
        def make_prompt(question):
            return f"Answer the question.\\nReply as JSON: {"label": "...", "confidence": 0.0}\\nQuestion: {question}"
        """,
        tests="""
        out = make_prompt("Is this spam?")
        assert out == 'Answer the question.\\nReply as JSON: {"label": "...", "confidence": 0.0}\\nQuestion: Is this spam?'
        assert make_prompt("{question}").endswith("Question: {question}")
        """,
        hints=["In an f-string, `{` starts a field. A literal brace is written `{{` or `}}`."],
        solution="""
        def make_prompt(question):
            return f'Answer the question.\\nReply as JSON: {{"label": "...", "confidence": 0.0}}\\nQuestion: {question}'
        """,
        why="""The JSON example's braces were read as an f-string field containing a dict expression, which fails to parse or
        produces the wrong text. Doubling them makes them literal. Switching the outer quotes to `'` also keeps the inner `"`
        readable. The second test shows that the **value** of `question` is inserted as plain text even if it contains braces:
        f-strings evaluate once and never re-scan what they insert, unlike the `replace`-based templates in 5.2."""),
    predict("Debug fields and conversions", "easy",
        code="""
        user = "ana "
        score = 0.8125
        items = ["a", "b"]
        print(f"{user=}")
        print(f"{user!r:>8}|{user:>8}|")
        print(f"{score=:.2f}, {len(items)=}")
        print(f"{items!s} {items!r} {'é'!a}")
        """,
        hints=["`=` prints the expression text too. `!r` uses `repr`, which adds quotes. `!a` is like `!r` but escapes non-ASCII characters."],
        why="""`f"{user=}"` shows the name, an equals sign and the **repr** of the value, which makes the trailing space visible.
        `!r` with `>8` right-aligns the quoted text. A format spec after `=` applies to the value. For a list, `str` and `repr`
        are the same text. `!a` escapes `é` as `'\\xe9'`, useful when logs must stay ASCII."""),
)

section("medium", "Medium",
    write("An aligned metrics report", "medium", tag="ML",
        prompt="""Write `metrics_report(metrics)` for a dict from metric name to value. Return lines `"<name>  <value>"` with
        names left-aligned to the longest name, values right-aligned in a column of width 8: values between 0 and 1 (exclusive of
        1 only when the name ends with `"_rate"`) are shown as percentages with one decimal, everything else with three
        decimals. Keep the dict's order.""",
        code="""
        def metrics_report(metrics):
            pass
        """,
        tests="""
        m = {"precision": 0.8231, "recall": 0.61, "error_rate": 0.0425, "n": 1400}
        assert metrics_report(m) == (
            "precision      0.823\\n"
            "recall         0.610\\n"
            "error_rate      4.2%\\n"
            "n           1400.000"
        )
        assert metrics_report({}) == ""
        """,
        hints=["Compute `width = max(map(len, metrics))` (guard the empty dict).",
               "Choose the spec per value: `f\"{v:8.1%}\"` for rates, `f\"{v:8.3f}\"` otherwise, and the name with `f\"{name:<{width}}\"`."],
        solution="""
        def metrics_report(metrics):
            if not metrics:
                return ""
            width = max(map(len, metrics))
            lines = []
            for name, value in metrics.items():
                text = f"{value:8.1%}" if name.endswith("_rate") else f"{value:8.3f}"
                lines.append(f"{name:<{width}}  {text}")
            return "\\n".join(lines)
        """,
        why="""A nested field, `{name:<{width}}`, computes the alignment from the data, so the report adapts to long metric names.
        Choosing the presentation by the metric's name, not its value, keeps a rate of 1.0 (100%) consistent with its
        neighbours. Formatting is the last step: the dict keeps full precision for anything that compares or plots it later."""),
    fix("Invoice totals off by a cent", "medium", tag="Data work",
        prompt="""`format_total(amounts)` should sum line amounts given as strings like `"19.99"` and print the total with
        thousands separators and exactly two decimals, rounding half up as the accounting system does. It uses floats and gets
        some totals wrong by a cent. Fix it.""",
        code="""
        def format_total(amounts):
            total = sum(float(a) for a in amounts)
            return f"{total:,.2f}"
        """,
        tests="""
        assert format_total(["1.005"]) == "1.01"
        assert format_total(["2.675", "0"]) == "2.68"
        assert format_total(["1000000.10", "234567.80"]) == "1,234,567.90"
        assert format_total([]) == "0.00"
        """,
        hints=["Parse with `Decimal(a)` (from the strings, not from floats), sum, then `quantize(Decimal(\"0.01\"), rounding=ROUND_HALF_UP)`.",
               "f-strings format `Decimal` values with the same `,.2f` spec."],
        solution="""
        from decimal import Decimal, ROUND_HALF_UP

        def format_total(amounts):
            total = sum((Decimal(a) for a in amounts), Decimal("0"))
            return f"{total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,.2f}"
        """,
        why="""`float("1.005")` is stored as 1.00499999..., so formatting rounds it down, and summing floats accumulates further
        binary error. `Decimal` built from the **strings** keeps the exact decimal values, `quantize` applies the business rounding
        rule explicitly, and the f-string only adds separators. Starting `sum` with `Decimal("0")` avoids mixing an int start
        value into the arithmetic and makes the empty case `0.00`."""),
    trace("Formatting one value many ways", "medium",
        prompt="Fill in `s` and `len(s)` after each marked line. `x = 3.14159`.",
        code="""
        x = 3.14159
        s = f"{x:.2f}"  # row: ".2f"
        s = f"{x:8.3f}"  # row: "8.3f"
        s = f"{x:<8.1f}|"  # row: "<8.1f with a bar"
        s = f"{x:+.0f}"  # row: "+.0f"
        s = f"{x:.3g}"  # row: ".3g"
        s = f"{x * 1000:,.1f}"  # row: "x * 1000 with ,.1f"
        """,
        trace_vars=["s", "len(s)"],
        hints=["Width is the total length including the point and decimals; `<` pads on the right."],
        why="""`.2f` keeps two decimals. `8.3f` is 5 characters of number padded to 8 on the left. `<8.1f` pads `3.1` to 8 on the
        right, so the bar shows the padding. `+.0f` rounds to 3 and always shows the sign. `.3g` keeps three significant digits.
        `,.1f` on 3141.59 adds a thousands separator and rounds to `3,141.6`."""),
    choose("Logging with an f-string or arguments", "medium", tag="GenAI",
        prompt="""Debug logging is turned off. Both lines run 20,000 times inside a request handler, logging the current list of
        retrieved chunk ids. Which is faster?""",
        setup="""import logging
log = logging.getLogger("rag")
log.setLevel(logging.WARNING)
chunk_ids = [f"chunk-{i:05d}" for i in range(300)]""",
        options={
            "a": "for _ in range(20_000):\n    log.debug(f\"retrieved {chunk_ids}\")",
            "b": "for _ in range(20_000):\n    log.debug(\"retrieved %s\", chunk_ids)",
        },
        answer="b",
        hints=["What does Python do with the f-string before `debug` even gets to decide whether to log?"],
        why="""The f-string is evaluated **before** `debug` is called, so A builds the text of a 300-item list 20,000 times, only for
        `debug` to throw it away because the level is WARNING. B passes the list along unformatted; the logger checks the level
        first and never formats anything. In a busy service this is real CPU, and the same applies to expensive values like a
        DataFrame or a model's output. Linters flag it (Ruff rule G004, "logging-f-string")."""),
    write("A cost line for an LLM call", "medium", tag="GenAI",
        prompt="""Write `cost_line(tokens_in, tokens_out, price_in, price_out)` where prices are in dollars **per million
        tokens**. Return text like `"$0.0123 (1,234 in, 567 out)"`: the cost with 4 decimals, and token counts with thousands
        separators.""",
        code="""
        def cost_line(tokens_in, tokens_out, price_in, price_out):
            pass
        """,
        tests="""
        assert cost_line(1234, 567, 3.0, 15.0) == "$0.0122 (1,234 in, 567 out)"
        assert cost_line(0, 0, 3.0, 15.0) == "$0.0000 (0 in, 0 out)"
        assert cost_line(2_000_000, 500_000, 0.25, 1.25) == "$1.1250 (2,000,000 in, 500,000 out)"
        """,
        hints=["cost = tokens_in / 1e6 * price_in + tokens_out / 1e6 * price_out."],
        solution="""
        def cost_line(tokens_in, tokens_out, price_in, price_out):
            cost = tokens_in / 1_000_000 * price_in + tokens_out / 1_000_000 * price_out
            return f"${cost:.4f} ({tokens_in:,} in, {tokens_out:,} out)"
        """,
        why="""Prices quoted per million tokens are the norm for LLM APIs, with output tokens usually priced several times higher
        than input tokens, which is why both counts appear. `:,` works on integers without a type letter. Four decimals keep small
        per-call costs visible; when summing many calls for a bill, keep the unrounded floats (or `Decimal`) and format only the
        total."""),
    fix("Dates built by hand", "medium", tag="Data work",
        prompt="""`partition_name(dt)` should return a file name like `"events_2025-06-01.parquet"` that sorts by date as text.
        Single-digit months and days break the sorting. Fix it.""",
        code="""
        def partition_name(dt):
            return "events_" + str(dt.year) + "-" + str(dt.month) + "-" + str(dt.day) + ".parquet"
        """,
        tests="""
        from datetime import date
        assert partition_name(date(2025, 6, 1)) == "events_2025-06-01.parquet"
        names = [partition_name(date(2025, m, d)) for m, d in [(10, 1), (9, 30), (1, 5)]]
        assert sorted(names) == [partition_name(date(2025, 1, 5)), partition_name(date(2025, 9, 30)), partition_name(date(2025, 10, 1))]
        """,
        hints=["`f\"{dt:%Y-%m-%d}\"` or `dt.isoformat()` pad month and day to two digits."],
        solution="""
        def partition_name(dt):
            return f"events_{dt:%Y-%m-%d}.parquet"
        """,
        why="""`str(6)` is `"6"`, so June 1st becomes `2025-6-1`, and as text `"2025-10-01" < "2025-9-30"`, which puts October before
        September. `%m` and `%d` always produce two digits, so text order equals date order. This is why data lakes partition by
        `YYYY-MM-DD` (or `year=2025/month=06/...`): tools list and prune partitions by name."""),
    refactor("From % and + to f-strings", "medium",
        prompt="Rewrite with f-strings, same output. Keep the tests green.",
        code="""
        def summary(name, n, rate, elapsed):
            return name + ": " + str(n) + " requests, " + "%.1f" % (rate * 100) + "% errors, " + "%d" % int(elapsed * 1000) + " ms"
        """,
        tests="""
        assert summary("search", 1200, 0.0425, 1.2345) == "search: 1200 requests, 4.2% errors, 1234 ms"
        assert summary("x", 0, 0.0, 0.0) == "x: 0 requests, 0.0% errors, 0 ms"
        """,
        hints=["`:.1%` does the multiply-by-100 and the percent sign. `int(elapsed * 1000)` truncates; `:.0f` would round, so keep `int`."],
        solution="""
        def summary(name, n, rate, elapsed):
            return f"{name}: {n} requests, {rate:.1%} errors, {int(elapsed * 1000)} ms"
        """,
        why="""The f-string reads like the output. `:.1%` replaces the manual `* 100` and the separate `"%"`. One detail must be kept:
        the original **truncated** milliseconds with `int`, while `:.0f` would round 1234.5 up to 1235, so a "pure formatting"
        refactor would silently change the numbers. Refactors of formatting code should be checked against the original output,
        exactly as these tests do."""),
    predict("An f-string is evaluated once", "medium", tag="GenAI",
        code="""
        style = "brief"
        prompt_f = f"Answer in a {style} style."
        prompt_t = "Answer in a {style} style."
        style = "detailed"
        print(prompt_f)
        print(prompt_t.format(style=style))
        make = lambda: f"Answer in a {style} style."
        style = "formal"
        print(make())
        """,
        hints=["The f-string on line 2 runs immediately, with the value `style` has at that moment."],
        why="""`prompt_f` was built when its line ran, with `"brief"`, and is now just a plain string: changing `style` later does
        nothing to it. A plain string with `{style}` is a **template** that `format` fills when called. Putting the f-string inside a
        function (here a lambda) delays evaluation to each call, so it sees the current value (late binding, 3.4). Prompt
        templates defined as module-level f-strings are a common bug: the values are baked in at import time."""),
)

section("hard", "Hard",
    write("A text progress bar", "hard", tag="ML",
        prompt="""Write `progress(done, total, width=20)` returning `"[########------------] 40.0% (4/10)"`: `#` for the done
        fraction of `width` (rounded down), `-` for the rest, then the percentage with one decimal and the counts. Clamp
        `done` to the range 0 to `total`, and show an empty bar at 0.0% when `total` is 0.""",
        code="""
        def progress(done, total, width=20):
            pass
        """,
        tests="""
        assert progress(4, 10) == "[########------------] 40.0% (4/10)"
        assert progress(10, 10, width=5) == "[#####] 100.0% (10/10)"
        assert progress(15, 10, width=4) == "[####] 100.0% (10/10)"
        assert progress(-3, 10, width=4) == "[----] 0.0% (0/10)"
        assert progress(0, 0, width=3) == "[---] 0.0% (0/0)"
        assert progress(1, 3, width=10) == "[###-------] 33.3% (1/3)"
        """,
        hints=["Clamp with `max(0, min(done, total))`, compute `fraction = done / total if total else 0.0`, then `filled = int(fraction * width)`."],
        solution="""
        def progress(done, total, width=20):
            done = max(0, min(done, total))
            fraction = done / total if total else 0.0
            filled = int(fraction * width)
            bar = "#" * filled + "-" * (width - filled)
            return f"[{bar}] {fraction:.1%} ({done}/{total})"
        """,
        why="""Clamping first means every later step can trust its input (a guard clause, 3.1). `int(...)` rounds the filled length
        down, so the bar is only full at exactly 100%; with `round`, 97.5% would already look complete. `:.1%` formats the
        fraction directly. Libraries such as `tqdm` do this (plus rates and time estimates) for training loops and batch
        jobs."""),
    fix("Read the code: an invoice table with formatting bugs", "hard", tag="Data work",
        prompt="""This renders an invoice as a fixed-width table: description 20 characters wide (longer ones cut to 20),
        quantity right-aligned in 4, unit price right-aligned in 10 with two decimals and thousands separators, and line total
        the same. The output is misaligned and long descriptions push the columns over. Read the function, find the format
        spec bugs, and fix them.""",
        code="""
        def render(lines):
            out = []
            for desc, qty, price in lines:
                total = qty * price
                out.append(f"{desc:20} {qty:<4} {price:10.2} {total:>10,.2f}")
            grand = sum(q * p for _, q, p in lines)
            out.append(f"{'TOTAL':20} {'':4} {'':10} {grand:10.2f}")
            return "\\n".join(out)
        """,
        tests="""
        rows = [("Embedding API credits (annual)", 2, 1250.5), ("Support", 12, 80.0)]
        assert render(rows) == (
            "Embedding API credit    2   1,250.50   2,501.00\\n"
            "Support                12      80.00     960.00\\n"
            "TOTAL                                  3,461.00"
        )
        assert all(len(line) == 47 for line in render(rows).splitlines())
        """,
        hints=["A width alone never cuts a string: add a precision, `.20`.",
               "`<4` left-aligns the quantity; numbers should be right-aligned (the default, or `>`).",
               "`10.2` without a type means two **significant** digits; use `,.2f`. The grand total also needs `,`."],
        solution="""
        def render(lines):
            out = []
            for desc, qty, price in lines:
                total = qty * price
                out.append(f"{desc:20.20} {qty:>4} {price:>10,.2f} {total:>10,.2f}")
            grand = sum(q * p for _, q, p in lines)
            out.append(f"{'TOTAL':20} {'':4} {'':10} {grand:>10,.2f}")
            return "\\n".join(out)
        """,
        why="""Four spec bugs, each producing plausible output. Width is a minimum, so the long description overflowed and pushed
        every column right; `.20` is a maximum for strings. `<4` left-aligned the quantities. `10.2` without a type is the general
        format with **two significant digits**, so 1250.5 printed as `1.3e+03`. And the total line lacked the thousands separator
        that the line totals had. When you build fixed-width reports, test against exact expected text, as here: a misaligned
        column is invisible in a quick glance at small numbers."""),
    write("Format a duration", "hard", tag="GenAI",
        prompt="""Write `duration(seconds)` for a non-negative number of seconds (a float), returning the two largest non-zero
        units among days, hours, minutes and seconds, like `"2d 03h"`, `"1h 02m"`, `"4m 05s"`, `"45s"`, with the second unit
        zero-padded to two digits. Sub-second durations show milliseconds, `"350ms"`, and `0` is `"0s"`.""",
        code="""
        def duration(seconds):
            pass
        """,
        tests="""
        assert duration(0) == "0s"
        assert duration(0.35) == "350ms"
        assert duration(45) == "45s"
        assert duration(245) == "4m 05s"
        assert duration(3725) == "1h 02m"
        assert duration(2 * 86400 + 3 * 3600 + 59) == "2d 03h"
        assert duration(3600) == "1h 00m"
        """,
        hints=["Split with `divmod` (1.1): days and the rest from 86,400, then hours from 3,600, then minutes from 60.",
               "Pair each value with its unit, find the first non-zero one, and format it with the next one, `f\"{a}{u1} {b:02d}{u2}\"`."],
        solution="""
        def duration(seconds):
            if seconds < 1:
                return f"{round(seconds * 1000)}ms" if seconds > 0 else "0s"
            total = int(seconds)
            days, rest = divmod(total, 86_400)
            hours, rest = divmod(rest, 3_600)
            minutes, secs = divmod(rest, 60)
            parts = [(days, "d"), (hours, "h"), (minutes, "m"), (secs, "s")]
            for i, (value, unit) in enumerate(parts):
                if value:
                    if i == len(parts) - 1:
                        return f"{value}{unit}"
                    nxt, nxt_unit = parts[i + 1]
                    return f"{value}{unit} {nxt:02d}{nxt_unit}"
            return "0s"
        """,
        why="""The `divmod` chain is the 1.1 pattern: each step takes off the largest unit and passes the remainder on. Showing the
        two largest units keeps the text short and meaningful: nobody cares about the seconds of a two-day job. Zero-padding the
        second unit (`03h`, `05s`) keeps columns aligned in logs, and `1h 00m` still shows the second unit because it is the one
        after the first non-zero unit, which is the readable choice. This is the kind of helper that turns raw latency and
        job-duration numbers into dashboards and agent progress messages."""),
    predict("Format spec edge cases", "hard",
        code="""
        print(f"{2.5:.0f} {3.5:.0f} {-0.4:.0f} {0.125:.2f}")
        print(f"{1e-7:f} {1e-7:g} {123456789:g} {0.00012345:.2g}")
        print(f"{True:d} {True} {None!r:>6} {'abc':.0}|")
        print(f"{-7:+05d} {7: d} {1234:_} {0.5:%}")
        print(f"{float('nan'):.2f} {float('inf'):,.1f} {-0.0:.1f}")
        """,
        hints=["Formatting rounds halves to even, like `round`. `g` switches to exponent notation for very large or small values.",
               "`-0.0` is a real float value with a sign."],
        why="""Halves round to even: `2.5` gives 2, `3.5` gives 4, and `-0.4` rounds to `-0`, keeping its sign. `0.125` is exactly
        representable, so it rounds to even, `0.12`. Default `f` has 6 decimals, which shows `0.000000` for 1e-7, while `g` keeps it
        visible as `1e-07` and writes large integers in exponent form. `True` formats as `1` with `d` and as `True` otherwise; a
        string precision of 0 gives the empty string. The space sign leaves room for a minus. `nan` and `inf` ignore precision, and
        `-0.0` keeps its minus sign, which surprises people in reports: add `z` (`f"{-0.0:z.1f}"`, Python 3.11+) to normalise it."""),
)

section("interview", "Interview questions",
    explain("f-strings, `str.format`, `%` formatting or `string.Template`: when do you use each?", "medium", tag="Interview",
        why="""f-strings for almost all of your own code: the values are known where the text is built, they are the most
        readable and the fastest, and they support the full format-spec language plus `=` for debugging. `str.format` or
        `format_map` when the template is defined separately and filled later, such as prompt templates stored in files; the
        template must be trusted, since format fields can access attributes. `%` formatting mainly for logging calls, where the
        logger formats lazily only when the message is emitted. `string.Template` for templates written by users or
        non-programmers: `$name` placeholders cannot run expressions, and `safe_substitute` tolerates missing values. For
        HTML or anything needing escaping, use a real template engine such as Jinja2 with autoescaping."""),
    explain("Why should log messages use `%s` arguments instead of f-strings?", "medium", tag="Interview",
        why="""An f-string is evaluated before the logging call, so the message text (including `repr` of large objects) is built
        even when that log level is disabled, every time the line runs. Passing arguments (`log.debug("x=%s", x)`) lets the logger
        check the level first and format only when the record is actually emitted, which matters in hot paths. It also keeps the
        message **template** constant, so log aggregators (Datadog, ELK, Sentry) can group occurrences and extract the values as
        fields. Exceptions: f-strings are fine for messages that are always emitted and cheap to build, and structured logging
        libraries take keyword fields instead (`log.info("retrieved", n=len(chunks))`)."""),
    explain("How do you format floats for financial reports correctly?", "hard", tag="Interview",
        why="""Do not do money arithmetic in binary floats: values like 2.675 or 1.005 are not exactly representable, so sums drift
        and formatting can round the "wrong" way, and format specs round half to even. Parse amounts as `Decimal` from strings (or
        store integer cents), do the arithmetic in that type, round **once** at the defined point with an explicit rule
        (`quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)` or banker's rounding if the business requires it), and only then
        format for display with `:,.2f`. Keep full precision in storage, format at the edge, and be aware that thousands and
        decimal separators are locale-specific (`babel` or `locale` for non-English reports). Test against totals produced by the
        accounting system, because "matches Excel" is usually the real requirement."""),
)

recap(
    "f-string fields are expressions evaluated when the line runs. Use `{{` `}}` for literal braces, `!r` to see quotes and whitespace, `{x=}` to debug.",
    "Format spec order: fill, align, sign, `#`, `0`, width, grouping, `.precision`, type. Width is a minimum; only a string precision cuts.",
    "Formatting rounds the binary value with ties to even. For money, round with `Decimal` first, then format.",
    "Dates: `f\"{dt:%Y-%m-%d}\"` or `isoformat()`, never concatenated numbers.",
    "f-strings for your code, `format_map` for templates filled later, `%` arguments for logging, `Template` for user-written templates.",
)
