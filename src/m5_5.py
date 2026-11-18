from lesson import *

lesson(
    id="m5-5", num="5.5", title="Regex basics",
    intro="Regular expressions describe patterns of text. The pattern language piece by piece, the `re` functions, greedy "
          "and lazy matching, groups (and the `findall` surprise), substitution with functions, flags, and the cases where "
          "a regex is the wrong tool. Applied to logs, LLM replies, citations and redacting personal data.",
    desc="`re.search`, `findall`, groups, `sub`, and when not to use a regex.",
    keys="regex regular expression re search match fullmatch findall finditer sub split compile group named group non capturing greedy lazy quantifier character class anchor word boundary flags ignorecase multiline dotall verbose escape lookahead backtracking",
)

term("Regular expression", "A pattern that describes a set of strings, such as `\\d{4}-\\d{2}-\\d{2}` for dates. Python's `re` module searches text with them.")
term("Quantifier", "How many times the previous item may repeat: `*` (0 or more), `+` (1 or more), `?` (0 or 1), `{m,n}`.")
term("Greedy match", "A quantifier that matches as much as possible, then gives back only if needed. Adding `?` (`.*?`) makes it lazy: as little as possible.")
term("Capture group", "A part of a pattern in parentheses whose matched text you can retrieve with `m.group(1)` or a name: `(?P<year>\\d{4})`.")
term("Word boundary", "`\\b`: the position between a word character and a non-word character, used to match whole words only.")

section("what", "What a regex is, and the `re` functions",
    p("""A **regular expression** (regex) is a small pattern language: `TKT-\\d+` means "the letters TKT, a dash, then one or more
    digits". Python's `re` module compiles a pattern into a matcher and runs it over text. Always write patterns as **raw
    strings**, `r"..."`, because regex syntax uses backslashes heavily and a normal string would turn some of them into escape
    characters first (problem 3)."""),
    html("""<div class="tbl"><table>
      <tr><th>Function</th><th>Returns</th><th>Use for</th></tr>
      <tr><td><code>re.search(p, s)</code></td><td>first match anywhere, or <code>None</code></td><td>"does it contain...", extracting one thing</td></tr>
      <tr><td><code>re.match(p, s)</code></td><td>a match only at the <strong>start</strong>, or <code>None</code></td><td>prefixes (often confused with search)</td></tr>
      <tr><td><code>re.fullmatch(p, s)</code></td><td>a match only if the <strong>whole</strong> string matches</td><td>validating a value</td></tr>
      <tr><td><code>re.findall(p, s)</code></td><td>list of matched strings (or of groups)</td><td>extracting all occurrences</td></tr>
      <tr><td><code>re.finditer(p, s)</code></td><td>iterator of match objects</td><td>all occurrences with positions and groups</td></tr>
      <tr><td><code>re.sub(p, repl, s)</code></td><td>new string with matches replaced</td><td>cleaning, redacting, reformatting</td></tr>
      <tr><td><code>re.split(p, s)</code></td><td>list of pieces between matches</td><td>splitting on a pattern rather than a fixed string</td></tr>
    </table></div>"""),
    ex("""
    import re

    text = "Escalate TKT-00417 and TKT-89; ignore tkt-5."
    m = re.search(r"TKT-\\d+", text)
    print(m.group(), m.start(), m.end())
    print(re.findall(r"TKT-\\d+", text))
    print(re.match(r"TKT", text), re.match(r"Escalate", text) is not None)
    print(re.fullmatch(r"\\d{4}", "2025") is not None, re.fullmatch(r"\\d{4}", "20255") is not None)
    """, "re_functions.py"),
    p("""Why raw strings matter: Python processes backslash escapes in a normal string **before** the `re` module ever sees it.
    `"\\n"` becomes a newline, `"\\t"` a tab, and `"\\b"` the backspace character, so the pattern `"\\bword\\b"` reaches `re` as
    backspace, w, o, r, d, backspace, and never matches. Some escapes happen to survive (`"\\d"` is not a Python escape, so it
    stays as backslash-d, with a warning in recent versions), which is why a missing `r` produces bugs that appear only for some
    patterns. A raw string, `r"\\bword\\b"`, keeps every backslash as written. When part of the pattern comes from a variable,
    combine both prefixes: `rf"\\b{re.escape(word)}\\b"` is a raw f-string."""),
    ex("""
    import re

    print(len("\\b"), repr("\\b"), len(r"\\b"), repr(r"\\b"))
    print(re.findall("\\bcat\\b", "cat catalog cat"), re.findall(r"\\bcat\\b", "cat catalog cat"))
    word = "a+b"
    print(re.findall(rf"{word}", "a+b aab"), re.findall(rf"{re.escape(word)}", "a+b aab"))
    """, "raw_strings.py"),
    p("""A **match object** (`m`) holds the matched text (`m.group()`), where it was (`m.start()`, `m.end()`, `m.span()`) and any
    groups (below). Functions that can fail to match return `None`, so check before using the result: `if m := re.search(...)`
    reads cleanly with the walrus operator."""),
)

section("syntax", "The pattern language, piece by piece",
    html("""<div class="tbl"><table>
      <tr><th>Piece</th><th>Matches</th></tr>
      <tr><td><code>abc</code></td><td>the literal characters a, b, c</td></tr>
      <tr><td><code>.</code></td><td>any character except a newline (with <code>re.DOTALL</code>, also newlines)</td></tr>
      <tr><td><code>[abc]</code>, <code>[a-z0-9]</code>, <code>[^,]</code></td><td>one character from the set or range; <code>^</code> first means "not these"</td></tr>
      <tr><td><code>\\d</code> <code>\\w</code> <code>\\s</code></td><td>a digit, a word character (letter, digit, underscore), whitespace; uppercase <code>\\D \\W \\S</code> are the opposites</td></tr>
      <tr><td><code>^</code> <code>$</code></td><td>start and end of the string (of each line with <code>re.MULTILINE</code>)</td></tr>
      <tr><td><code>\\b</code></td><td>a word boundary: between a word character and a non-word character</td></tr>
      <tr><td><code>*</code> <code>+</code> <code>?</code> <code>{m,n}</code></td><td>repeat the previous item 0+, 1+, 0 or 1, m to n times</td></tr>
      <tr><td><code>a|b</code></td><td>either alternative (tried left to right)</td></tr>
      <tr><td><code>(...)</code>, <code>(?:...)</code></td><td>a capturing group; a group that only groups</td></tr>
      <tr><td><code>\\.</code> <code>\\(</code> <code>\\[</code></td><td>a literal special character, escaped</td></tr>
    </table></div>"""),
    ex("""
    import re

    log = "2025-06-01 09:05:07 ERROR [auth] Token expired for user 42 (retry 3)"
    print(re.search(r"\\d{4}-\\d{2}-\\d{2}", log).group())
    print(re.findall(r"\\[(\\w+)\\]", log), re.findall(r"\\b\\d+\\b", log))
    print(re.findall(r"\\b[A-Z]{3,}\\b", log), re.search(r"retry (\\d)", log).group(1))
    print(re.findall(r"[^ ]+", "a  b c"), re.escape("price (USD) 3.5?"))
    """, "syntax.py"),
    p("""Two things surprise people coming from other tools. In Python 3, `\\d`, `\\w` and `\\s` are **Unicode-aware**: `\\d` matches
    Arabic-Indic and other digits, and `\\w` matches accented letters, which is usually what you want for text but not for
    validating ASCII ids (use `[0-9]` or the `re.ASCII` flag then, problem 16). And `re.escape(text)` turns any literal text
    into a safe pattern, which you need whenever part of a pattern comes from data or a user."""),
    callout("sql", "SQL / Power BI", """SQL's `LIKE 'TKT-%'` is a very small pattern language: `%` is `.*` and `_` is `.`. Regex is
    the full version; PostgreSQL's `~` and `regexp_replace`, Oracle's `REGEXP_LIKE` and `REGEXP_SUBSTR`, and Power Query's
    `Text.Select` cover similar ground. As in SQL, a pattern that needs to scan everything is slow, so keep patterns
    anchored and specific."""),
)

section("engine", "How the engine finds a match, step by step",
    p("""Python's regex engine is a **backtracking** engine, and knowing exactly what it does explains every surprising result
    later in this lesson. For `search`, it tries to match the pattern starting at position 0 of the text. If that fails, it tries
    position 1, then 2, and so on, and it returns the **first position where the whole pattern matches**, not the longest or best
    match anywhere in the text. At each position it walks through the pattern piece by piece, consuming characters. When a piece
    has a choice (a quantifier can take more or fewer characters, an alternation has several options), it takes the first choice
    and remembers the others. If a later piece fails, it goes back to the most recent choice and tries the next option. That
    going back is **backtracking**."""),
    p("""Trace `\\d+%` against `"up 12.5% now"`. Positions 0 to 2 (`u`, `p`, space) fail at once, because `\\d+` needs a digit. At
    position 3, `\\d+` greedily takes `12`, then `%` is needed but the next character is `.`, so it fails. The engine backtracks:
    `\\d+` gives back the `2` and holds only `1`, and `%` is tested against `2`, which fails again. `\\d+` cannot give back its last
    digit (it needs at least one), so position 3 fails as a whole. Position 4 (`2`) fails the same way, and at position 5 (`.`)
    `\\d+` fails. At position 6, `\\d+` takes `5`, `%` matches, and the result is `5%`. The pattern was too narrow for the data;
    `\\d+(?:\\.\\d+)?%` gives `12.5%`."""),
    ex("""
    import re

    print(re.search(r"\\d+%", "up 12.5% now").group())
    print(re.search(r"\\d+(?:\\.\\d+)?%", "up 12.5% now").group())
    print(re.search(r"cat|category", "category").group(), re.search(r"category|cat", "category").group())
    print(re.findall(r"\\d+|\\d+\\.\\d+", "3.5 and 10"), re.findall(r"\\d+\\.\\d+|\\d+", "3.5 and 10"))
    """, "engine.py"),
    p("""The last two lines show the rule for **alternation**: at each position, `a|b` tries `a` first, and if `a` matches, the
    engine takes it without checking whether `b` would have matched more. So `cat|category` finds only `cat` inside "category",
    and `\\d+|\\d+\\.\\d+` splits `3.5` into `3` and `5` because the short alternative wins at position 0. Put the **longer or more
    specific** alternative first. `findall` then continues searching from the end of each match, never inside it, so its
    matches never overlap."""),
    callout("key", "The two rules to remember", """The engine returns the **leftmost** match, and at that position it takes the first
    way the pattern can succeed: greedy quantifiers try the most characters first, alternatives are tried left to right. Almost
    every "why did it match that?" question is answered by tracing these two rules by hand."""),
)

section("greedy", "Greedy and lazy matching",
    p("""Quantifiers are **greedy**: `.*` matches as much as it can, then the engine **backtracks**, giving characters back one
    at a time, until the rest of the pattern can match. So `<b>.*</b>` on a string with two bold sections matches from the
    first `<b>` to the **last** `</b>`, swallowing everything between. Adding `?` makes a quantifier **lazy**: `.*?` matches as
    little as possible and grows only when needed, which gives one section at a time."""),
    ex("""
    import re

    html = "<b>refund</b> and <b>invoice</b>"
    print(re.findall(r"<b>.*</b>", html))
    print(re.findall(r"<b>.*?</b>", html))
    print(re.findall(r"<b>([^<]*)</b>", html))      # often clearer: "anything except <"
    quoted = 'say "yes" or "no"'
    print(re.findall(r'"(.*)"', quoted), re.findall(r'"(.*?)"', quoted))
    """, "greedy_lazy.py"),
    p("""A negated class like `[^<]*` ("any run of characters that are not `<`") is often clearer and faster than a lazy
    `.*?`, because it cannot run past the delimiter. Backtracking also has a dark side: patterns with **nested** quantifiers,
    such as `(a+)+$`, can take exponential time on inputs that almost match, which is called catastrophic backtracking and has
    taken down production services. Keep patterns simple, avoid nested repeats of the same thing, and never run untrusted
    patterns (problem 17)."""),
)

section("groups", "Groups: capturing the parts you need",
    p("""Parentheses create a **capturing group**. After a match, `m.group(1)`, `m.group(2)` and so on return what each group
    matched, `m.groups()` returns all of them, and **named groups**, `(?P<name>...)`, are retrieved by name with
    `m.group("name")` or all at once with `m.groupdict()`. Named groups make patterns self-documenting and turn a match directly
    into a dict."""),
    ex("""
    import re

    pattern = r"(?P<date>\\d{4}-\\d{2}-\\d{2}) (?P<level>[A-Z]+) \\[(?P<service>\\w+)\\] (?P<msg>.*)"
    m = re.fullmatch(pattern, "2025-06-01 ERROR [billing] Card declined")
    print(m.group("level"), m.group(4), m.groups())
    print(m.groupdict())
    """, "groups.py"),
    p("""The **`findall` surprise**: if the pattern contains groups, `findall` returns the **groups**, not the whole match (one
    string per match for one group, a tuple per match for several). So adding parentheses "just for grouping" silently changes
    the result. Use a **non-capturing** group `(?:...)` when you need grouping (for `|` or a quantifier) without capturing, or
    use `finditer` and take `m.group(0)`."""),
    ex("""
    import re

    text = "USD 120, EUR 80, GBP 5"
    print(re.findall(r"(USD|EUR) \\d+", text))          # the group only
    print(re.findall(r"(?:USD|EUR) \\d+", text))        # the whole match
    print(re.findall(r"(USD|EUR) (\\d+)", text))        # tuples of groups
    print([m.group(0) for m in re.finditer(r"(USD|EUR) \\d+", text)])
    """, "findall_groups.py"),
)

section("lookaround", "Lookarounds: conditions that consume nothing",
    p("""Most pattern pieces **consume** characters: they match some text and move the position forward. Anchors such as `^`, `$`
    and `\\b` are different: they test a condition at the current position and consume nothing, which is why they are called
    **zero-width**. **Lookarounds** let you write your own zero-width conditions with any pattern inside."""),
    html("""<div class="tbl"><table>
      <tr><th>Syntax</th><th>Name</th><th>Succeeds when</th></tr>
      <tr><td><code>X(?=Y)</code></td><td>lookahead</td><td>X is followed by Y (Y is not part of the match)</td></tr>
      <tr><td><code>X(?!Y)</code></td><td>negative lookahead</td><td>X is not followed by Y</td></tr>
      <tr><td><code>(?&lt;=Y)X</code></td><td>lookbehind</td><td>X is preceded by Y</td></tr>
      <tr><td><code>(?&lt;!Y)X</code></td><td>negative lookbehind</td><td>X is not preceded by Y</td></tr>
    </table></div>"""),
    p("""Because the condition is not part of the match, the matched text stays clean: `\\d+(?=%)` returns the number without the
    percent sign, and `(?<=\\$)\\d+` returns the amount without the dollar. Negative lookarounds express "not next to something",
    which is how you match a whole token that contains non-word characters. `\\b` needs a word character on one side, so it fails
    around `+` or `#`. But `(?<!\\w)` and `(?!\\w)` mean "no word character before" and "no word character after", which also holds
    at the start and end of the text (problem 3 uses exactly this)."""),
    ex("""
    import re

    text = "Growth 12% on $300, churn 3% of 1500 users, C++ and C# jobs"
    print(re.findall(r"\\d+(?=%)", text), re.findall(r"(?<=\\$)\\d+", text))
    print(re.findall(r"\\b\\d+\\b(?!%)", text))
    print(re.findall(r"\\bC\\+\\+\\b", text), re.findall(r"(?<!\\w)C\\+\\+(?!\\w)", text), re.findall(r"(?<!\\w)C#(?!\\w)", text))
    """, "lookarounds.py"),
    p("""Lookaheads can also stack several conditions at one position, since each one checks without moving:
    `^(?=.*\\d)(?=.*[A-Z]).{8,}$` means "at the start, somewhere ahead there is a digit, somewhere ahead there is a capital, and the
    whole string is at least 8 characters". In Python, a **lookbehind must have a fixed width**: `(?<=\\$)` and `(?<=USD )` are
    fine, `(?<=\\$+)` raises `re.error`. Use lookarounds sparingly; when a pattern needs many, a few lines of ordinary Python are
    often clearer."""),
    ex("""
    import re

    strong = re.compile(r"^(?=.*\\d)(?=.*[A-Z]).{8,}$")
    print([bool(strong.match(pw)) for pw in ["password1", "Password1", "Pass1"]])
    try:
        re.compile(r"(?<=\\$+)\\d+")
    except re.error as e:
        print("re.error:", e)
    """, "lookahead_stack.py"),
)

section("sub", "Substitution, splitting and flags",
    p("""`re.sub(pattern, repl, text)` replaces every match. In the replacement string, `\\1` or `\\g<name>` insert a group, so you
    can reorder parts. The replacement can also be a **function** that receives the match object and returns the replacement
    text, which handles anything a fixed string cannot: conditional replacements, lookups, computed values. `count=` limits the
    number of replacements. `re.split` splits on a pattern, and if the pattern has a group, the separators are **kept** in the
    result."""),
    ex("""
    import re

    print(re.sub(r"(\\d{2})/(\\d{2})/(\\d{4})", r"\\3-\\2-\\1", "due 31/12/2025 or 01/06/2026"))
    print(re.sub(r"\\s+", " ", "  too    many\\n spaces  ").strip())
    prices = "EUR 10, EUR 25.5"
    print(re.sub(r"EUR (\\d+(?:\\.\\d+)?)", lambda m: f"USD {float(m.group(1)) * 1.08:.2f}", prices))
    print(re.split(r"[;,]\\s*", "a, b;c ,d"), re.split(r"([;,])", "a,b;c"))
    """, "sub_split.py"),
    p("""**Flags** change how a pattern matches: `re.IGNORECASE` (`re.I`), `re.MULTILINE` (`re.M`, so `^` and `$` work per line),
    `re.DOTALL` (`re.S`, so `.` matches newlines too), `re.ASCII` (so `\\d \\w \\s` match ASCII only) and `re.VERBOSE` (`re.X`),
    which ignores whitespace in the pattern and allows comments, so complex patterns can be laid out readably. For a pattern
    used many times, `re.compile` builds it once and returns an object with the same methods; Python also caches recently used
    patterns, so compiling is mainly about readability and naming."""),
    ex("""
    import re

    ticket = re.compile(r\"\"\"
        \\b(?P<prefix>[A-Z]{2,4})     # project key
        -(?P<number>\\d{1,6})\\b       # ticket number
    \"\"\", re.VERBOSE)
    print([m.groupdict() for m in ticket.finditer("See OPS-12, BILL-4401 and x-1.")])
    notes = "ok: yes\\nerror: disk\\nError: net"
    print(re.findall(r"^error: (\\w+)", notes, flags=re.M | re.I))
    """, "flags.py"),
)

section("when", "When not to use a regex",
    p("""Regex is powerful and easy to overuse. Prefer simpler tools when they fit:"""),
    p("""- **Fixed text:** `"refund" in text`, `startswith`, `endswith`, `split(",")`, `partition` (5.2) are faster and clearer.
    - **Structured formats:** JSON (`json.loads`), CSV (`csv`), HTML and XML (an HTML parser such as BeautifulSoup, or
      `xml.etree`), URLs (`urllib.parse`), dates (`datetime.strptime`). Regex cannot correctly handle nesting or quoting in
      general, and every hand-written HTML regex eventually meets an input that breaks it.
    - **LLM output:** ask the model for JSON (structured output or JSON mode) and validate it with a schema (Module 11). Use
      regex to **locate** the JSON in a messy reply, then a real parser to read it (problem 5)."""),
    p("""Regex is the right tool for **patterns in free text**: ids, codes, dates and amounts inside sentences, log lines, light
    tokenisation, cleaning whitespace and punctuation, and redacting personal data before text is sent to an LLM or a log
    (problem 9)."""),
)

section("warmup", "Warm-up",
    predict("search, match and fullmatch", "easy",
        code="""
        import re

        s = "Order 1042 shipped; order 77 pending"
        print(re.search(r"\\d+", s).group(), re.findall(r"\\d+", s))
        print(re.match(r"\\d+", s), re.match(r"Order", s).group())
        print(re.fullmatch(r"[A-Za-z]+ \\d+", "Order 1042") is not None, re.fullmatch(r"\\d+", "1042 ") is not None)
        print(re.findall(r"[Oo]rder (\\d+)", s), re.search(r"cancel", s))
        """,
        hints=["`match` only looks at the start of the string; `fullmatch` requires the whole string to match."],
        why="""`search` finds the first number anywhere, `findall` all of them. `match` fails because the string does not start with a
        digit, so it returns `None`. `fullmatch` fails on `"1042 "` because of the trailing space, which is exactly why it is the
        right tool for validation: `search` would accept anything that **contains** a valid value. With a group, `findall`
        returns just the numbers. No match gives `None`, not an exception."""),
    write("Extract ticket ids", "easy", tag="Data work",
        prompt="""Write `ticket_ids(text)` returning the ticket ids in a text, in order and without repeats. An id is `TKT-`
        followed by 4 to 6 digits, upper-case, as a whole word (not part of a longer token such as `XTKT-1234` or
        `TKT-1234567`).""",
        code="""
        import re

        def ticket_ids(text):
            pass
        """,
        tests="""
        t = "Merge TKT-0417 into TKT-88812. Also TKT-0417 again, not tkt-1234, XTKT-9999 or TKT-12."
        assert ticket_ids(t) == ["TKT-0417", "TKT-88812"]
        assert ticket_ids("TKT-1234567 TKT-123456") == ["TKT-123456"]
        assert ticket_ids("") == []
        """,
        hints=["`\\b` on both sides makes it a whole word; `\\d{4,6}` limits the digits.", "Deduplicate in order with `dict.fromkeys` (4.5)."],
        solution="""
        import re

        def ticket_ids(text):
            return list(dict.fromkeys(re.findall(r"\\bTKT-\\d{4,6}\\b", text)))
        """,
        why="""Word boundaries do two jobs: `\\b` before `TKT` rejects `XTKT-9999` (no boundary between `X` and `T`), and `\\b` after the
        digits rejects `TKT-1234567`, because `\\d{4,6}` cannot stop in the middle of a run of digits and still find a boundary.
        Without the second `\\b`, the pattern would happily return `TKT-123456` from inside the seven-digit id. Case-sensitivity is
        the default, so `tkt-1234` is ignored; add `re.I` if lower case should count."""),
    fix("A word boundary that does not work", "easy",
        prompt="""`count_word(text, word)` should count whole-word occurrences. It always returns 0. Fix it.""",
        code="""
        import re

        def count_word(text, word):
            return len(re.findall("\\b" + word + "\\b", text))
        """,
        tests="""
        assert count_word("refund the refund; refunds are slow", "refund") == 2
        assert count_word("a+b and a+b", "a+b") == 2
        assert count_word("nothing here", "refund") == 0
        """,
        hints=["In a normal string, `\\b` is the backspace character, not a word boundary. Use a raw string.",
               "The word itself may contain regex specials like `+`. Escape it with `re.escape`."],
        solution="""
        import re

        def count_word(text, word):
            return len(re.findall(rf"(?<!\\w){re.escape(word)}(?!\\w)", text))
        """,
        why="""Bug one: `"\\b"` without `r` is the backspace character (ASCII 8), so the pattern looked for backspaces. Raw strings keep
        the backslash. Bug two: `word` is data, and `"a+b"` as a pattern means "one or more a's, then b"; `re.escape` makes it
        literal. That second test also needs more than `\\b`: there is no word boundary between `+` and a space, so the solution
        uses lookarounds, `(?<!\\w)` and `(?!\\w)`, meaning "not preceded / not followed by a word character", which works for any
        word. `rf"..."` is a raw f-string."""),
    predict("Greedy versus lazy", "easy",
        code="""
        import re

        s = "[1] Refunds [2] take [3] days"
        print(re.findall(r"\\[.*\\]", s))
        print(re.findall(r"\\[.*?\\]", s))
        print(re.findall(r"\\[(\\d+)\\]", s))
        print(re.search(r"\\d+.*\\d+", "a 12 b 34 c 56").group(), re.search(r"\\d+.*?\\d+", "a 12 b 34 c 56").group())
        """,
        hints=["`.*` takes as much as possible and then backs off until the rest matches. `.*?` takes as little as possible."],
        why="""The greedy `\\[.*\\]` runs to the **last** `]`, so it returns one long match. The lazy version stops at the first `]`, giving
        each citation. A specific pattern, `\\[(\\d+)\\]`, says exactly what is inside, and with a group `findall` returns only the
        numbers. Greedy `\\d+.*\\d+` spans from the first to the last number; lazy stops at the second."""),
)

section("medium", "Medium",
    write("Find the JSON in a model's reply", "medium", tag="GenAI",
        prompt="""Models often wrap JSON in a Markdown code fence and add commentary. Write `extract_json(reply)` that returns
        the parsed object from the **first** fenced block marked `json` (three backticks, `json`, a newline, the JSON, three
        backticks). If there is no such block, try the text from the first `{` to the last `}`. Return `None` if nothing parses.""",
        code="""
        import json, re

        def extract_json(reply):
            pass
        """,
        tests="""
        fence = "`" * 3
        r1 = f'Sure! Here it is:\\n{fence}json\\n{{"label": "spam", "confidence": 0.93}}\\n{fence}\\nAnything else?'
        assert extract_json(r1) == {"label": "spam", "confidence": 0.93}
        r2 = 'The answer is {"label": "ham", "tags": ["a", "b"]} as requested.'
        assert extract_json(r2) == {"label": "ham", "tags": ["a", "b"]}
        assert extract_json("no json here") is None
        assert extract_json("{not: valid}") is None
        """,
        hints=["Search with `re.DOTALL` and a lazy group `(.*?)` between the opening fence (three backticks, then the word json and a newline) and the closing fence.",
               "For the fallback, `find(\"{\")` and `rfind(\"}\")`. Parse with `json.loads` inside `try` / `except json.JSONDecodeError`."],
        solution="""
        import json, re

        FENCE = re.compile(r"`{3}json\\s*\\n(.*?)\\n`{3}", re.DOTALL)

        def extract_json(reply):
            m = FENCE.search(reply)
            if m:
                candidate = m.group(1)
            else:
                start, end = reply.find("{"), reply.rfind("}")
                if start == -1 or end < start:
                    return None
                candidate = reply[start:end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                return None
        """,
        why="""The regex only **locates** the JSON; `json.loads` does the actual parsing, because regex cannot reliably match nested
        braces and quoted strings. `re.DOTALL` lets `.` cross newlines, and the lazy `.*?` stops at the first closing fence, so a
        reply with two code blocks returns the first. The `{`...`}` fallback uses the outermost braces, which works for one object
        with nesting. Returning `None` instead of raising lets the caller retry the model with an error message. With structured
        output or JSON mode in the API, most of this becomes unnecessary, but replies from other tools still need it."""),
    fix("findall returns only the currency", "medium", tag="Data work",
        prompt="""`amounts(text)` should return every amount with its currency, like `"USD 120"`. It returns only `["USD",
        "EUR"]`. Fix the pattern.""",
        code="""
        import re

        def amounts(text):
            return re.findall(r"(USD|EUR|GBP) \\d+(\\.\\d{2})?", text)
        """,
        tests="""
        assert amounts("Paid USD 120 and EUR 80.50, refund GBP 5") == ["USD 120", "EUR 80.50", "GBP 5"]
        assert amounts("none") == []
        """,
        hints=["When a pattern has groups, `findall` returns the groups. Make them non-capturing with `(?:...)`."],
        solution="""
        import re

        def amounts(text):
            return re.findall(r"(?:USD|EUR|GBP) \\d+(?:\\.\\d{2})?", text)
        """,
        why="""The parentheses were only meant to group the alternatives and the optional decimals, but every `(...)` captures, and
        `findall` with two groups returns a tuple of the two groups per match. Non-capturing groups keep the grouping without
        changing what `findall` returns. If you do want both the whole match and parts of it, use `finditer` and read
        `m.group(0)` and `m.group(1)`."""),
    write("Parse log lines with named groups", "medium", tag="Data work",
        prompt="""Write `parse_line(line)` for lines like `"2025-06-01 09:05:07 ERROR [auth] Token expired"`. Return a dict with
        keys `date`, `time`, `level`, `service` and `message`, using **named groups** and `fullmatch`. Return `None` for lines
        that do not have this format.""",
        code="""
        import re

        def parse_line(line):
            pass
        """,
        tests="""
        assert parse_line("2025-06-01 09:05:07 ERROR [auth] Token expired") == {
            "date": "2025-06-01", "time": "09:05:07", "level": "ERROR", "service": "auth", "message": "Token expired"}
        assert parse_line("2025-06-01 09:05:07 INFO [rag-api] ok")["service"] == "rag-api"
        assert parse_line("garbage") is None
        assert parse_line("2025-06-01 09:05:07 ERROR [auth]") is None
        """,
        hints=["`(?P<date>\\d{4}-\\d{2}-\\d{2}) (?P<time>\\d{2}:\\d{2}:\\d{2}) (?P<level>[A-Z]+) \\[(?P<service>[\\w-]+)\\] (?P<message>.+)`",
               "`m.groupdict()` builds the dict."],
        solution="""
        import re

        LINE = re.compile(
            r"(?P<date>\\d{4}-\\d{2}-\\d{2}) (?P<time>\\d{2}:\\d{2}:\\d{2}) "
            r"(?P<level>[A-Z]+) \\[(?P<service>[\\w-]+)\\] (?P<message>.+)"
        )

        def parse_line(line):
            m = LINE.fullmatch(line)
            return m.groupdict() if m else None
        """,
        why="""Named groups make the pattern readable and give you the dict for free. `fullmatch` rejects partial lines (the last test has
        no message), where `search` would accept a line that merely **contains** the format. `[\\w-]+` allows service names with
        dashes, which `\\w` alone does not. Splitting the pattern over two adjacent raw strings uses implicit concatenation (5.1)
        on purpose. This is how log shippers like Logstash's grok patterns work, with a library of named sub-patterns."""),
    choose("A fixed word: `in` or a regex", "medium",
        prompt="Both count the log lines that mention \"error\" in any case, over 200,000 lines. Which is faster?",
        setup="""import re
lines = ["2025-06-01 09:05:07 INFO [api] request ok"] * 190_000 + ["2025-06-01 09:05:07 ERROR [api] timeout"] * 10_000""",
        options={
            "a": "n = sum(1 for line in lines if re.search(\"error\", line, re.IGNORECASE))",
            "b": "n = sum(1 for line in lines if \"error\" in line.lower())",
        },
        answer="b",
        hints=["What does each line cost: a call into the regex engine with case-folding, or one lowering and a substring search?"],
        why="""For a fixed string, `in` is a tight C loop. The regex call has to look up the compiled pattern, set up a match with
        case-insensitive rules and run the engine for every line, which costs more even though the pattern is trivial. Both are
        correct; reach for regex when you need a **pattern** (digits, alternatives, boundaries), not a literal word. (If you also
        needed whole words only, `\\berror\\b` would be a good reason to use the regex.)"""),
    write("Redact personal data before sending text to an LLM", "medium", tag="GenAI",
        prompt="""Write `redact(text)` that replaces email addresses with `[EMAIL]`, phone numbers with `[PHONE]`, and card
        numbers (13 to 16 digits, optionally in groups separated by spaces or dashes) with `[CARD]`. Phone numbers here are an
        optional `+` and country code, then 9 to 12 digits possibly separated by spaces or dashes. Replace cards **before**
        phones, since a card number would also look like a phone number.""",
        code="""
        import re

        def redact(text):
            pass
        """,
        tests="""
        t = "Contact ana.lopez@example.co.uk or +44 20 7946 0958. Card 4111 1111 1111 1111 was charged twice."
        assert redact(t) == "Contact [EMAIL] or [PHONE]. Card [CARD] was charged twice."
        assert redact("call 555-123-4567 now") == "call [PHONE] now"
        assert redact("order 42 shipped") == "order 42 shipped"
        """,
        hints=["Email: `[\\w.+-]+@[\\w-]+(?:\\.[\\w-]+)+`. Card: `\\b(?:\\d[ -]?){12,15}\\d\\b`.",
               "Phone: `\\+?\\d[\\d -]{7,14}\\d`. Apply the three `re.sub` calls in the order email, card, phone."],
        solution="""
        import re

        EMAIL = re.compile(r"[\\w.+-]+@[\\w-]+(?:\\.[\\w-]+)+")
        CARD = re.compile(r"\\b(?:\\d[ -]?){12,15}\\d\\b")
        PHONE = re.compile(r"\\+?\\d[\\d -]{7,14}\\d")

        def redact(text):
            text = EMAIL.sub("[EMAIL]", text)
            text = CARD.sub("[CARD]", text)
            return PHONE.sub("[PHONE]", text)
        """,
        why="""Order matters because the patterns overlap: a card number also matches the phone pattern, so cards go first, and once
        they are `[CARD]` the phone pattern can no longer see their digits. `(?:\\d[ -]?){12,15}\\d` means "13 to 16 digits, each
        optionally followed by a space or dash". These patterns are deliberately simple and will miss some formats and catch some
        non-PII numbers; production systems use dedicated PII detectors (such as Microsoft Presidio) and validate card numbers with
        the Luhn check (1.P). Redacting before text leaves your system (to an LLM API, a log or a vendor) is often a compliance
        requirement."""),
    trace("Regex results step by step", "medium",
        prompt="Fill in `r` after each marked line.",
        code="""
        import re
        s = "id=7; name=Ana; id=12"
        r = re.findall(r"id=(\\d+)", s)  # row: "findall ids"
        r = re.sub(r"id=(\\d+)", r"#\\1", s)  # row: "sub with a group"
        r = re.split(r";\\s*", s)  # row: "split on ; and spaces"
        r = re.split(r"(;)\\s*", s)  # row: "split with a captured separator"
        r = [m.span() for m in re.finditer(r"\\d+", s)]  # row: "spans of numbers"
        """,
        trace_vars=["r"],
        hints=["With a group, `findall` returns group text and `split` keeps the separators. `\\1` in the replacement inserts group 1."],
        why="""`findall` returns only the captured digits. `sub` rewrites each `id=N` as `#N` by reinserting group 1. `split` on `;\\s*`
        drops the separators; with the separator in a group, it is kept as its own item. `finditer` gives match objects, and
        `span()` their start and end positions, which is what you need to highlight matches or cut the text around them."""),
    refactor("String cleanup in one regex pass", "medium", tag="ML",
        prompt="Replace the loops with `re.sub`, same output. Keep the tests green.",
        code="""
        def clean(text):
            out = ""
            for ch in text:
                if ch.isalnum():
                    out += ch
                else:
                    out += " "
            while "  " in out:
                out = out.replace("  ", " ")
            return out.strip().lower()
        """,
        tests="""
        assert clean("Refund!!  (EU-only)\\n--  now?") == "refund eu only now"
        assert clean("") == "" and clean("ok") == "ok"
        """,
        hints=["`[^\\w\\s]` is \"neither a word character nor whitespace\"; `\\s+` is any run of whitespace. Note `\\w` also allows `_`."],
        solution="""
        import re

        def clean(text):
            text = re.sub(r"[^\\w\\s]|_", " ", text)
            return re.sub(r"\\s+", " ", text).strip().lower()
        """,
        why="""Two substitutions replace a character loop (with quadratic string building) and a `while` loop that rescans the whole text
        each time. `\\w` includes the underscore, which `isalnum` does not, so `|_` keeps the behaviour identical. `\\s+` collapses any
        run of whitespace, including the newline, in one pass. Cleaning like this is a typical preprocessing step before bag-of-words
        features; for LLMs, keep punctuation, since models use it."""),
    fix("A tokenizer that breaks numbers and contractions", "medium", tag="ML",
        prompt="""`tokens(text)` uses `\\w+`, which splits `3.5` into `3` and `5` and `don't` into `don` and `t`. Fix the pattern
        so decimals and contractions stay whole, and other words still split as before.""",
        code="""
        import re

        def tokens(text):
            return re.findall(r"\\w+", text.lower())
        """,
        tests="""
        assert tokens("Don't refund 3.5 or 10 units, it's late") == ["don't", "refund", "3.5", "or", "10", "units", "it's", "late"]
        assert tokens("v2.0 rocks") == ["v2", "0", "rocks"]
        assert tokens("") == []
        """,
        hints=["Use alternatives, the most specific first: a decimal number `\\d+\\.\\d+`, then a word with an optional `'` part `\\w+(?:'\\w+)?`.",
               "Alternatives are tried left to right at each position, so order matters."],
        solution="""
        import re

        def tokens(text):
            return re.findall(r"\\b\\d+\\.\\d+\\b|\\w+(?:'\\w+)?", text.lower())
        """,
        why="""At each position the engine tries the alternatives left to right and takes the first that matches, so the decimal
        alternative must come before the general word one, or `\\w+` would grab `3` first. The `\\b` around the decimal keeps
        `v2.0` from being read as a number. `(?:'\\w+)?` attaches an apostrophe part to a word without capturing (so `findall` still
        returns whole tokens). Real tokenizers (spaCy, NLTK, or the subword tokenizers of LLMs) handle far more cases; this is the
        classic first step of a bag-of-words model."""),
)

section("hard", "Hard",
    write("A natural sort key", "hard", tag="Data work",
        prompt="""Write `natural_key(s)` so that `sorted(names, key=natural_key)` orders embedded numbers numerically and text
        case-insensitively: `doc2` before `doc10`, `Chapter 9` before `chapter 10`. Split the string into digit runs and
        non-digit runs with `re.split`, convert digit runs to `int`, and lower-case the rest.""",
        code="""
        import re

        def natural_key(s):
            pass
        """,
        tests="""
        files = ["doc10.txt", "doc2.txt", "Doc1.txt", "doc2b.txt", "doc02.txt"]
        assert sorted(files, key=natural_key) == ["Doc1.txt", "doc2.txt", "doc02.txt", "doc2b.txt", "doc10.txt"]
        assert sorted(["v1.10", "v1.9", "v1.2"], key=natural_key) == ["v1.2", "v1.9", "v1.10"]
        assert natural_key("abc") == ("abc",)
        """,
        hints=["`re.split(r\"(\\d+)\", s)` keeps the digit runs because of the group, and alternates text, number, text, ...",
               "Build a tuple: `int(p)` for digit parts, `p.casefold()` for the others."],
        solution="""
        import re

        def natural_key(s):
            parts = re.split(r"(\\d+)", s)
            return tuple(int(p) if p.isdigit() else p.casefold() for p in parts if p)
        """,
        why="""With a capturing group, `re.split` keeps the separators, so `"doc10.txt"` becomes `["doc", "10", ".txt"]`, and the key
        `("doc", 10, ".txt")` compares the number as a number. Tuples compare element by element (4.3), and because the parts
        alternate text and numbers in the same positions, comparing `int` with `str` never happens for names of the same shape.
        `doc2` and `doc02` get equal keys, and the stable sort keeps their input order. This is what file managers call "natural"
        order; the `natsort` library covers more edge cases."""),
    fix("Read the code: a citation checker", "hard", tag="RAG",
        prompt="""A RAG app asks the model to cite sources as `[1]` or `[1, 3]`. This checker should return the cited source
        names, in first-cited order, plus any citation numbers that point to no source. It crashes on `[1, 3]`, and a greedy
        pattern swallows text between brackets. Read it, find the bugs, and fix them.""",
        code="""
        import re


        def check_citations(answer, sources):
            numbers = []
            for group in re.findall(r"\\[(.*)\\]", answer):
                numbers.append(int(group))
            cited, unknown = [], []
            for n in numbers:
                name = sources[n - 1]
                if name not in cited:
                    cited.append(name)
            return cited, unknown
        """,
        tests="""
        sources = ["faq.md", "terms.md", "policy.md"]
        a = "Refunds take 5 days [1]. After 30 days there are none [2, 3]. See [1] again."
        assert check_citations(a, sources) == (["faq.md", "terms.md", "policy.md"], [])
        assert check_citations("Wrong [4] and [0].", sources) == ([], [4, 0])
        assert check_citations("No citations.", sources) == ([], [])
        assert check_citations("Odd [2,1] spacing", sources) == (["terms.md", "faq.md"], [])
        """,
        hints=["`\\[(.*)\\]` is greedy: on the first answer it captures from the first `[` to the last `]`. Match only digits and commas inside the brackets.",
               "A citation group like `\"2, 3\"` must be split on commas (`re.split(r\"\\s*,\\s*\", ...)`).",
               "A number outside `1..len(sources)` should go to `unknown`. Note that `sources[0 - 1]` would silently return the **last** source."],
        solution="""
        import re

        CITATION = re.compile(r"\\[(\\d+(?:\\s*,\\s*\\d+)*)\\]")


        def check_citations(answer, sources):
            numbers = []
            for group in CITATION.findall(answer):
                numbers.extend(int(n) for n in re.split(r"\\s*,\\s*", group))
            cited, unknown = [], []
            for n in numbers:
                if 1 <= n <= len(sources):
                    name = sources[n - 1]
                    if name not in cited:
                        cited.append(name)
                elif n not in unknown:
                    unknown.append(n)
            return cited, unknown
        """,
        why="""Three bugs. The greedy `.*` captured from the first `[` to the last `]` ("1]. After 30 days ... See [1"), which `int` cannot
        parse. The specific pattern `\\d+(?:\\s*,\\s*\\d+)*` matches exactly "a number, then any number of comma-separated numbers", so
        it cannot run across text. Lists like `2, 3` then need splitting. And `sources[n - 1]` was unchecked: `[4]` raises
        `IndexError`, while `[0]` is worse, because `sources[-1]` silently returns the **last** source, a wrong citation with no error.
        Checking that citations point to real retrieved sources is a cheap, useful guard against hallucinated references."""),
    write("Find template variables, ignoring escaped braces", "hard", tag="GenAI",
        prompt="""Prompt templates use `{name}` placeholders and `{{` / `}}` for literal braces, as `str.format` does. Write
        `template_vars(template)` returning the distinct placeholder names in first-seen order, ignoring anything inside doubled
        braces. Names are word characters. Use lookarounds.""",
        code="""
        import re

        def template_vars(template):
            pass
        """,
        tests="""
        t = "Hi {name}! Reply as JSON: {{\\"label\\": \\"...\\"}}. Q: {question} ({name})"
        assert template_vars(t) == ["name", "question"]
        assert template_vars("{{literal}} only") == []
        assert template_vars("{a}{b}{a}") == ["a", "b"]
        assert template_vars("") == []
        """,
        hints=["`(?<!\\{)\\{(\\w+)\\}(?!\\})` means: a `{` not preceded by `{`, a name, a `}` not followed by `}`.",
               "Deduplicate while keeping order with `dict.fromkeys`."],
        solution="""
        import re

        PLACEHOLDER = re.compile(r"(?<!\\{)\\{(\\w+)\\}(?!\\})")

        def template_vars(template):
            return list(dict.fromkeys(PLACEHOLDER.findall(template)))
        """,
        why="""A **lookbehind** `(?<!\\{)` and a **lookahead** `(?!\\})` check what is before and after the match without consuming
        characters, so `{{literal}}` is skipped (its inner braces are preceded by `{` and followed by `}`) while `{name}` is found.
        Knowing a template's variables lets you validate it before use: compare them with the values you have, and fail early on a
        missing variable instead of sending a half-filled prompt (5.2). For full fidelity with `str.format` (format specs,
        attribute access), `string.Formatter().parse(template)` returns the fields exactly as `format` sees them, and is the better
        tool in production."""),
    predict("Unicode classes and flags", "hard",
        code="""
        import re

        text = "Prix: ٤٢€ for Zoë; ok"
        print(re.findall(r"\\d+", text), re.findall(r"\\d+", text, flags=re.ASCII))
        print(re.findall(r"\\w+", "Zoë_1 x"), re.findall(r"\\w+", "Zoë_1 x", flags=re.ASCII))
        notes = "line one\\nline two"
        print(re.findall(r"^line \\w+$", notes), re.findall(r"^line \\w+$", notes, flags=re.M))
        print(re.search(r"one.line", notes), re.search(r"one.line", notes, flags=re.S).group() == "one\\nline")
        """,
        hints=["In Python 3, `\\d` and `\\w` are Unicode-aware unless you pass `re.ASCII`.",
               "Without `re.M`, `^` and `$` refer to the whole string; without `re.S`, `.` does not match a newline."],
        why="""`\\d` matches the Arabic-Indic digits `٤٢`, and `re.ASCII` restricts it to `0-9`, so for validating ASCII ids you need
        `[0-9]` or the flag. `\\w` includes `ë` and the underscore; with `re.ASCII` the `ë` splits the word. Without `re.M`, the
        pattern must match the whole string from start to end, which fails; with it, each line matches. Without `re.S`, `.` refuses
        the newline, so the search returns `None`. These defaults explain many "the regex works in the online tester but not in
        Python" reports: testers often default to different flags or engines."""),
)

section("interview", "Interview questions",
    explain("What is the difference between greedy and lazy quantifiers, and what is catastrophic backtracking?", "medium", tag="Interview",
        why="""Greedy quantifiers (`*`, `+`, `?`, `{m,n}`) match as much as possible and then backtrack, giving characters back,
        until the rest of the pattern matches; lazy ones (`*?`, `+?`) match as little as possible and expand only when needed. So
        `<.*>` spans from the first `<` to the last `>`, while `<.*?>` matches one tag. Catastrophic backtracking happens when a
        pattern can match the same text in exponentially many ways, typically nested quantifiers like `(a+)+` or `(\\w+\\s?)*$`, and
        the input almost matches but fails at the end: the engine tries every split. It can freeze a server (a regular expression
        denial of service, ReDoS). Prevent it with specific patterns (negated classes like `[^<]*`), no nested repeats of
        overlapping things, anchors, input length limits, timeouts, or a linear-time engine such as RE2 for untrusted patterns."""),
    explain("When should you not use a regular expression?", "medium", tag="Interview",
        why="""When the text is a literal (use `in`, `startswith`, `split`, `partition`, which are faster and clearer), and when the
        data has real structure: JSON, CSV, HTML, XML, URLs, dates, email headers. Those have parsers in the standard library or well
        known packages that handle nesting, quoting and escaping correctly, which regular expressions fundamentally cannot do for
        nested structures. Also avoid one huge clever pattern that nobody can maintain: several small steps, `re.VERBOSE` with
        comments, or a small parser are easier to test. Regex is right for patterns inside free text: ids, dates and amounts in
        sentences, log lines, cleanup, light tokenisation, and redaction."""),
    explain("How do you reliably extract structured data from an LLM's free-text reply?", "hard", tag="Interview",
        why="""Prefer not to: ask for structure at the source. Use the API's structured output or JSON mode, or tool calling with a JSON
        schema, so the model's output is constrained to valid JSON. Then **validate** it against a schema (Pydantic, Module 11),
        because valid JSON can still have wrong types or missing fields. When you must parse free text (older models, third-party
        tools), use regex only to **locate** the payload (a fenced code block, the outermost braces), parse it with a real parser
        (`json.loads`), validate, and on failure retry with the error message included so the model can correct itself, with a
        limit on retries. Log failures with the raw reply for debugging, and add evaluation tests with tricky replies (extra
        commentary, two code blocks, trailing commas) to catch regressions."""),
)

recap(
    "Write patterns as raw strings. `search` finds anywhere, `match` only at the start, `fullmatch` validates the whole string.",
    "Quantifiers are greedy; add `?` for lazy, or better, use a specific class like `[^<]*`. Avoid nested quantifiers.",
    "With groups, `findall` returns the groups. Use `(?:...)` to group without capturing, named groups for readable extraction.",
    "`re.sub` accepts a function for computed replacements; `re.split` keeps captured separators. Know `re.I`, `re.M`, `re.S`, `re.X`, `re.ASCII`.",
    "Regex is for patterns in free text. For literals use `in` and `split`; for JSON, CSV, HTML and URLs use a parser.",
)
