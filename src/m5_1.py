from lesson import *
from diagrams import *

lesson(
    id="m5-1", num="5.1", title="Strings: indexing, slicing, immutability",
    intro="A string is an immutable sequence of Unicode code points. What that means for indexing, slicing, comparing and "
          "building text, the literal syntax that hides real bugs (a missing comma, a stray backslash), and why `len` is "
          "neither \"characters on screen\" nor \"LLM tokens\".",
    desc="Characters are strings, slicing, why every change builds a new string.",
    keys="string str code point character index slice immutable join concatenation compare lexicographic casefold find index startswith raw string triple quoted implicit concatenation len grapheme",
)

term("Code point", "One Unicode number, such as U+0041 for \"A\". A Python `str` is a sequence of code points; `len` counts them.")
term("Immutable string", "A string can never be changed in place. Every \"change\", such as `upper()` or `replace()`, builds a new string.")
term("Raw string", "A literal written `r\"...\"` in which backslashes are kept as they are, used for regex patterns and Windows paths.")
term("Implicit concatenation", "Python joins adjacent string literals: `\"a\" \"b\"` is `\"ab\"`. A missing comma in a list of strings does this silently.")
term("Grapheme", "What a reader sees as one character. It can be several code points, such as a letter plus an accent, or an emoji with a skin tone.")

section("what", "What a string is",
    fig(stage_map(5, "prepare documents for a RAG index"), "Module 5 at a glance: from string basics to Unicode and regular expressions, building up to cleaning documents for retrieval."),
    fig(table(["character", "P", "y", "t", "h", "o", "n"], [
        ["index", "0", "1", "2", "3", "4", "5"],
        ["negative index", "-6", "-5", "-4", "-3", "-2", "-1"],
    ], label="indexes of the string Python"),
        "A string is an immutable sequence of characters, indexed exactly like a list."),
    p("""A Python `str` is an **immutable sequence of Unicode code points**. A code point is one number from the Unicode
    table (`"A"` is 65, `"é"` is 233, `"€"` is 8364), and `ord` and `chr` convert between a one-character string and its
    number. There is no separate "char" type: indexing a string gives you another string, of length 1. Because a string is a
    sequence, everything from 4.1 applies: `len`, indexing, slicing, `in`, iteration, `count` and `index`."""),
    ex("""
    s = "Refund €20"
    print(len(s), s[0], s[-3:], type(s[0]).__name__, len(s[0]))
    print(ord("R"), ord("€"), chr(8364), s[0][0][0])
    for ch in "ab€":
        print(ch, ord(ch), end=" | ")
    print()
    """, "str_basics.py"),
    p("""A string is **not** a sequence of bytes. How a code point is stored as bytes (UTF-8, UTF-16 and so on) is a
    separate question that only matters when text crosses a boundary: a file, a network socket, a database. Lesson 5.4 covers
    encodings; for now, think of a string as a list of Unicode numbers that cannot change."""),
    callout("sql", "SQL / Power BI", """A Python `str` is like SQL Server's `NVARCHAR` (Unicode text), not `VARCHAR` with a
    code page. `s[0]` is `LEFT(s, 1)`, `s[-3:]` is `RIGHT(s, 3)`, `s[2:5]` is `SUBSTRING(s, 3, 3)` (SQL counts from 1,
    Python from 0) and `len(s)` is `LEN(s)` (which, unlike Python, ignores trailing spaces in SQL Server)."""),
)

section("slicing", "Indexing and slicing strings",
    p("""Strings follow exactly the list rules from 4.1: positions start at 0, negative positions count from the end, `stop`
    is never included, slices are clamped and never raise, a step can skip or reverse. Two things are specific to strings:
    every slice is a **new string**, and a string reversed with `[::-1]` is reversed **by code point**, which can break text
    that uses several code points for one visible character (the last section)."""),
    ex("""
    ref = "INV-2025-000731"
    print(ref[:3], ref[4:8], ref[-6:], ref[::-1][:6])
    print(ref[100:], ref[-100:3], "abc"[1:1] == "")
    try:
        ref[50]
    except IndexError as e:
        print("IndexError:", e)
    """, "slicing.py"),
    p("""Fixed positions such as `ref[4:8]` are only safe for strings whose format you control, like your own ids. For text
    from users, files or LLMs, the positions move, and code that slices at fixed offsets silently returns the wrong field
    (problem 15). Splitting on a separator (5.2) or a regex (5.5) is more robust."""),
)

section("immutable", "Immutability, and building strings efficiently",
    fig(table(["building a long string", "what happens", "cost"], [
        ["s += part, in a loop", "a new string each time", "can be O(n squared)"],
        ["parts.append(part), then ''.join(parts)", "one final copy", "O(n)"],
    ], hl={(0, 2), (1, 2)}, label="building strings with += versus join"),
        "Strings cannot change, so every `+=` may copy everything built so far; collect the pieces and join once."),
    p("""You cannot change a string in place: `s[0] = "r"` raises `TypeError`. Every method that seems to change a string,
    `upper`, `replace`, `strip`, returns a **new** string and leaves the original alone, so you must use the return value
    (`s.strip()` on its own line does nothing useful). The benefits are the ones from Module 2: strings can be shared
    freely, used as dict keys and set members, and cached."""),
    ex("""
    s = "refund"
    try:
        s[0] = "R"
    except TypeError as e:
        print("TypeError:", e)
    s.upper()                # returns a new string, which is thrown away here
    print(s)
    s = s.upper()            # rebinding the name to the new string
    print(s, s.replace("F", "f"), s)
    """, "immutable.py"),
    p("""Building a long string from many pieces is where immutability costs. Each `a + b` creates a new string and copies
    both sides, so adding pieces one at a time in a loop copies the growing text again and again: O(n²) characters in the
    worst case. The idiomatic fix is to collect the pieces in a list and join once: `"".join(pieces)` computes the total
    length, allocates one string and copies each piece exactly once, O(n)."""),
    ex("""
    lines = [f"[{i}] chunk {i}" for i in range(5)]
    context = "\\n".join(lines)           # one allocation, one copy of each piece
    print(context)
    print(len(context), context.count("\\n"))
    """, "join.py"),
    callout("note", "Why `+=` sometimes looks fast", """CPython has an optimisation: when a string has no other references,
    `s += piece` may grow it in place instead of copying. So a `+=` loop can be fast in one program and slow in another (for
    example as soon as another name points at the string, or with f-strings, or on other Python implementations). Do not
    rely on it: `join` is fast everywhere (problem 8)."""),
)

section("compare", "Comparing and searching",
    p("""`==` compares strings code point by code point, exactly and case-sensitively. `<` and `>` compare
    **lexicographically by code point**, the dictionary order of the Unicode numbers, which is not human alphabetical order:
    all uppercase letters (65 to 90) come before all lowercase ones (97 to 122), and digits compare as characters, so `"10" <
    "9"`. For case-insensitive comparison, use `casefold()`, a stronger `lower()` designed for exactly this (it maps the German
    `"ß"` to `"ss"`, for example)."""),
    ex("""
    print("Zebra" < "apple", "10" < "9", "apple" < "apples")
    print(sorted(["banana", "Apple", "cherry"]), sorted(["banana", "Apple", "cherry"], key=str.casefold))
    print("Straße".lower() == "STRASSE".lower(), "Straße".casefold() == "STRASSE".casefold())
    """, "compare.py"),
    p("""Searching: `sub in s` tests for a substring. `s.find(sub)` returns the first position or **-1**, while `s.index(sub)`
    returns the position or raises `ValueError`; choose `find` when absence is normal and `index` when absence is a bug.
    `s.count(sub)` counts **non-overlapping** occurrences, and `startswith` / `endswith` accept a tuple of options."""),
    ex("""
    log = "ERROR 2025-06-01 timeout after 30s; retry; ERROR again"
    print("timeout" in log, log.find("ERROR"), log.find("ERROR", 1), log.find("WARN"))
    print(log.count("ERROR"), "aaaa".count("aa"), log.startswith(("ERROR", "WARN")))
    try:
        log.index("WARN")
    except ValueError as e:
        print("ValueError:", e)
    """, "search.py"),
)

section("literals", "String literals and their traps",
    p("""Single and double quotes are the same; triple quotes (`\"\"\"...\"\"\"`) allow line breaks, which is how long prompts
    are usually written. Inside normal quotes, a backslash starts an **escape sequence**: `\\n` is a newline, `\\t` a tab,
    `\\\\` one backslash. A **raw string**, `r"..."`, keeps backslashes as they are, which is what you want for regex patterns
    (5.5) and Windows paths."""),
    ex("""
    print(len("a\\tb"), len(r"a\\tb"), "C:\\\\data\\\\new.csv", r"C:\\data\\new.csv")
    print(repr("line1\\nline2"), "it's", 'say "hi"')
    """, "escapes.py"),
    p("""**Implicit concatenation**: Python joins adjacent string literals at compile time, so `"Hello " "world"` is one
    string. It is handy for splitting a long literal over lines, and a source of silent bugs in lists of strings: a missing
    comma merges two items into one, the list is one item shorter, and nothing raises (problem 2)."""),
    ex("""
    stop_sequences = [
        "###",
        "END"          # missing comma
        "Human:",
    ]
    print(len(stop_sequences), stop_sequences)

    long_prompt = (
        "You are a support assistant. "
        "Answer only from the provided context."
    )
    print(long_prompt)
    """, "implicit_concat.py"),
)

section("length", "What `len` counts, and what it does not",
    fig(table(["text", "len(text)", "len(text.encode('utf-8'))"], [
        ["'cafe'", "4", "4"],
        ["'café' (one é character)", "4", "5"],
        ["'café' (e + combining accent)", "5", "6"],
    ], hl={(2, 1)}, label="characters versus bytes"),
        "`len` counts code points, not what the reader sees and not bytes; the same-looking word can have different lengths."),
    p("""`len(s)` counts **code points**. That is often, but not always, what a person would call characters. A visible
    character can be several code points: `"é"` can be stored as one code point (U+00E9) or as `"e"` plus a combining accent
    (U+0301), and an emoji with a skin tone is two code points. Those strings look identical but have different lengths, and
    reversing one with `[::-1]` can move the accent onto the wrong letter."""),
    ex("""
    precomposed = "café"
    decomposed = "cafe\\u0301"          # e + combining acute accent: looks the same
    print(precomposed, decomposed, len(precomposed), len(decomposed), precomposed == decomposed)
    import unicodedata
    print(unicodedata.normalize("NFC", decomposed) == precomposed)
    thumbs = "\\U0001F44D\\U0001F3FD"    # thumbs up + medium skin tone
    print(len(thumbs), len(thumbs.encode("utf-8")))
    """, "length.py"),
    p("""So there are at least four different "lengths" of a text: **code points** (`len`), **bytes** in an encoding (what a
    database column limit or an HTTP size limit counts, 5.4), **graphemes** (what a reader sees), and **tokens** (what an LLM
    counts and bills: roughly 3 to 4 characters of English per token, more for other languages and code). Normalise text with
    `unicodedata.normalize("NFC", s)` before comparing or deduplicating it, and count tokens with the model's own tokenizer,
    never with `len`."""),
)

section("warmup", "Warm-up",
    predict("Indexing and slicing text", "easy",
        code="""
        s = "Ticket #4821: refund"
        print(s[0], s[-1], s[8:12], s[-6:])
        print(s[::-1][:6], s[100:], s[:0] == "")
        print(s.find("#"), s[s.find("#") + 1:s.find(":")])
        print(type(s[3]).__name__, s[3] == s[3:4])
        """,
        hints=["A single character is a string of length 1, so `s[3]` equals the one-character slice `s[3:4]`."],
        why="""Slices of strings follow the list rules: `s[8:12]` is positions 8 to 11, the digits. Reversing and taking six gives
        the last six characters backwards. `find` locates the `#` and the `:`, and slicing between them extracts the number
        without knowing its length in advance, which is more robust than fixed positions."""),
    fix("A list of stop words that is one short", "easy", tag="Data work",
        prompt="""`STOPWORDS` should contain six words, and `is_stop` should recognise all of them. `"and"` and `"or"` are not
        recognised. Fix the list.""",
        code="""
        STOPWORDS = [
            "the",
            "a",
            "and"
            "or",
            "of",
            "to",
        ]

        def is_stop(word):
            return word.lower() in STOPWORDS
        """,
        tests="""
        assert len(STOPWORDS) == 6
        assert all(is_stop(w) for w in ["the", "A", "and", "or", "of", "To"])
        assert not is_stop("andor")
        """,
        hints=["Look for two string literals with no comma between them."],
        solution="""
        STOPWORDS = frozenset({"the", "a", "and", "or", "of", "to"})

        def is_stop(word):
            return word.lower() in STOPWORDS
        """,
        why="""`"and" "or"` is implicit concatenation: the list contains `"andor"` and has five items, and nothing raises. Writing
        the collection as a set literal on one line makes the missing comma much easier to see, and membership becomes O(1)
        (4.4). Tools help too: Ruff's rule ISC001 flags implicit concatenation on one line, and a trailing comma after the last
        item in a multi-line list makes adding items safer."""),
    write("Mask an API key for logs", "easy", tag="GenAI",
        prompt="""Write `mask(secret, visible=4)` that replaces all but the last `visible` characters with `*`, so logs can
        show which key was used without revealing it. Secrets of `visible` characters or fewer are fully masked, and an empty
        string stays empty.""",
        code="""
        def mask(secret, visible=4):
            pass
        """,
        tests="""
        assert mask("sk-test-1234abcd") == "************abcd"
        assert mask("abc") == "***"
        assert mask("abcd") == "****"
        assert mask("") == ""
        assert mask("token-xyz", visible=2) == "*******yz"
        """,
        hints=["`\"*\" * n` repeats a string. Take the tail with a slice, but watch the `-0` trap from 4.1."],
        solution="""
        def mask(secret, visible=4):
            if len(secret) <= visible:
                return "*" * len(secret)
            return "*" * (len(secret) - visible) + secret[len(secret) - visible:]
        """,
        why="""Short secrets are fully masked, because showing the last 4 characters of a 4-character key would reveal all of it.
        `secret[len(secret) - visible:]` avoids the `-0` slice trap if someone passes `visible=0` (4.1). Masking secrets in logs and
        traces is a basic requirement for LLM applications, whose tracing tools often log every request header by default
        (3.2, problem 12)."""),
    predict("How strings compare", "easy",
        code="""
        print("Zebra" < "apple", "10" < "9", "2" < "10")
        print(sorted(["b", "A", "a", "B"]))
        print(sorted(["b", "A", "a", "B"], key=str.lower))
        print("ß".lower(), "ß".casefold(), "ẞ".lower())
        print(max(["refund", "Refund", "REFUND"]))
        """,
        hints=["Uppercase letters have smaller code points than lowercase ones. Digits compare as characters."],
        why="""Comparison uses code points: `"Z"` (90) is less than `"a"` (97), and `"10" < "9"` because `"1" < "9"` decides it.
        Sorting without a key puts all capitals first; `key=str.lower` sorts case-insensitively and, being stable, keeps
        `"A"` before `"a"` as they appeared. `casefold` maps `"ß"` to `"ss"`, which `lower` does not. `max` returns the string with
        the largest code points, the all-lowercase one."""),
)

section("medium", "Medium",
    write("A palindrome check that ignores punctuation", "medium", tag="Interview",
        prompt="""Write `is_palindrome(text)` that returns `True` if the letters and digits of `text`, ignoring case,
        read the same backwards. Spaces and punctuation are ignored. Use two positions moving towards each other, so no
        cleaned copy of the whole string is built.""",
        code="""
        def is_palindrome(text):
            pass
        """,
        tests="""
        assert is_palindrome("A man, a plan, a canal: Panama")
        assert is_palindrome("No 'x' in Nixon")
        assert not is_palindrome("refund")
        assert is_palindrome("") and is_palindrome(".,!")
        assert is_palindrome("12321") and not is_palindrome("123")
        """,
        hints=["Start `i` at 0 and `j` at the last position. Skip characters that are not `isalnum()` on either side, then compare `casefold()` versions.",
               "Stop when the positions meet."],
        solution="""
        def is_palindrome(text):
            i, j = 0, len(text) - 1
            while i < j:
                if not text[i].isalnum():
                    i += 1
                elif not text[j].isalnum():
                    j -= 1
                elif text[i].casefold() != text[j].casefold():
                    return False
                else:
                    i += 1
                    j -= 1
            return True
        """,
        why="""The two-pointer version uses O(1) extra memory and stops at the first mismatch. The one-liner,
        `cleaned = [c.casefold() for c in text if c.isalnum()]; return cleaned == cleaned[::-1]`, is also correct and fine in most
        code, but builds two copies; interviewers often ask for the pointer version as a follow-up. `isalnum` is Unicode-aware, so
        accented letters count as letters. A string with no letters at all is a palindrome by this definition."""),
    fix("A context block with a trailing separator", "medium", tag="RAG",
        prompt="""`build_context(chunks)` formats retrieved chunks for a prompt as numbered blocks separated by a line with
        `---`. It leaves a stray separator at the end and builds the string by repeated concatenation. Fix both: use `join`.""",
        code="""
        def build_context(chunks):
            context = ""
            for i, chunk in enumerate(chunks, start=1):
                context += f"[{i}] {chunk['source']}\\n{chunk['text']}\\n---\\n"
            return context
        """,
        tests="""
        chunks = [{"source": "faq.md", "text": "Refunds take 5 days."}, {"source": "terms.md", "text": "No refunds after 30 days."}]
        assert build_context(chunks) == "[1] faq.md\\nRefunds take 5 days.\\n---\\n[2] terms.md\\nNo refunds after 30 days."
        assert build_context([]) == ""
        assert build_context(chunks[:1]) == "[1] faq.md\\nRefunds take 5 days."
        """,
        hints=["Build a list of blocks without separators, then `\"\\n---\\n\".join(blocks)`: `join` only puts the separator **between** items."],
        solution="""
        def build_context(chunks):
            blocks = [f"[{i}] {c['source']}\\n{c['text']}" for i, c in enumerate(chunks, start=1)]
            return "\\n---\\n".join(blocks)
        """,
        why="""`join` places the separator only between items, so there is never a leading or trailing one and the empty case is
        the empty string, with no special handling. It also builds the result in one allocation. Numbering the chunks `[1]`,
        `[2]` lets the model cite its sources ("according to [2]"), and a clean, consistent format measurably helps models
        follow citation instructions."""),
    trace("Parsing settings with find and slices", "medium",
        prompt="Fill in `key`, `value` and `rest` after each marked line.",
        code="""
        rest = "model=small; temperature=0.2; stop=###"
        key, value = "", ""
        cut = rest.find(";")
        pair, rest = rest[:cut], rest[cut + 1:].lstrip()  # row: "split off the first pair"
        key, value = pair[:pair.find("=")], pair[pair.find("=") + 1:]  # row: "split the pair"
        cut = rest.find(";")
        pair, rest = rest[:cut], rest[cut + 1:].lstrip()  # row: "split off the next pair"
        key, value = pair[:pair.find("=")], pair[pair.find("=") + 1:]  # row: "split that pair"
        """,
        trace_vars=["key", "value", "rest"],
        hints=["`find` returns the position of the separator; the slices on either side of it are the two parts. `lstrip()` removes leading spaces only."],
        why="""Each step finds a separator and slices around it: everything before `;` is the pair, everything after (minus the
        leading space) is the rest. Inside the pair, the same trick around `=` gives key and value. Note what would happen on the
        **last** pair: there is no `;`, `find` returns -1, and `rest[:-1]` silently drops the last character. That is why lesson
        5.2's `split` and `partition` are the better tools; this trace shows what they do for you."""),
    choose("Growing a prompt with an f-string or join", "medium", tag="GenAI",
        prompt="Both build a context string from 4,000 retrieved snippets. Which is faster?",
        setup="""snippets = [f"snippet number {i:05d}; " for i in range(4000)]""",
        options={
            "a": "text = \"\"\nfor s in snippets:\n    text = f\"{text}{s}\"",
            "b": "text = \"\".join(snippets)",
        },
        answer="b",
        hints=["Each f-string builds a brand-new string. How much text is copied on pass 4,000?"],
        why="""Each pass of A builds a new string containing everything so far plus one snippet, so the total copying is about
        1 + 2 + ... + 4,000 snippets: O(n²) characters. CPython's in-place trick for `+=` cannot apply to an f-string. B measures
        the total once, allocates once and copies each snippet once: O(n). The difference grows with the number of pieces, which
        is exactly the situation of a RAG context or a long report."""),
    write("Truncate at a word boundary", "medium", tag="RAG",
        prompt="""Write `truncate(text, max_chars, ellipsis="…")` that shortens text so the result, **including** the
        ellipsis, is at most `max_chars` characters. Cut at the last space that fits, so no word is broken, and strip trailing
        spaces before adding the ellipsis. Text that already fits is returned unchanged. If even the first word does not fit,
        cut it hard.""",
        code="""
        def truncate(text, max_chars, ellipsis="…"):
            pass
        """,
        tests="""
        t = "Refunds are processed within five business days."
        assert truncate(t, 100) == t
        assert truncate(t, 20) == "Refunds are…"
        assert len(truncate(t, 20)) <= 20
        assert truncate(t, 12) == "Refunds are…"
        assert truncate("Supercalifragilistic", 8) == "Superca…"
        assert truncate(t, 25, ellipsis="...") == "Refunds are processed..."
        """,
        hints=["The text you may keep is `text[:limit]` with `limit = max_chars - len(ellipsis)`. Find its last space with `rfind`.",
               "If the character right after that part is a space, the cut already falls between words: keep it whole.",
               "If there is no space in that part, keep it as it is (a hard cut)."],
        solution="""
        def truncate(text, max_chars, ellipsis="…"):
            if len(text) <= max_chars:
                return text
            limit = max_chars - len(ellipsis)
            room = text[:limit]
            if text[limit] == " ":
                kept = room
            else:
                cut = room.rfind(" ")
                kept = room[:cut] if cut > 0 else room
            return kept.rstrip() + ellipsis
        """,
        why="""Reserving room for the ellipsis first guarantees the length limit, and `rfind` finds the last space inside that
        room so the cut lands between words. The check on `text[limit]` handles the boundary case the tests probe: when the
        room ends exactly at the end of a word, cutting back to the previous space would throw away a whole word for nothing.
        `cut > 0` covers a room whose only space is at position 0. This is how
        search snippets and previews are made. For LLM context limits you would truncate by **tokens** with the model's
        tokenizer instead (the last section), because characters and tokens are not proportional."""),
    fix("Parsing a name and an email", "medium", tag="Data work",
        prompt="""`parse_contact("Ana Lopez <ana@x.io>")` should return `("Ana Lopez", "ana@x.io")`, and a bare email with no
        name should return `("", email)`. It crashes on a bare email with `ValueError`. Fix it.""",
        code="""
        def parse_contact(text):
            start = text.index("<")
            end = text.index(">")
            return text[:start].strip(), text[start + 1:end].strip()
        """,
        tests="""
        assert parse_contact("Ana Lopez <ana@x.io>") == ("Ana Lopez", "ana@x.io")
        assert parse_contact("ben@x.io") == ("", "ben@x.io")
        assert parse_contact("  Cy  < cy@x.io > ") == ("Cy", "cy@x.io")
        """,
        hints=["`index` raises when the character is missing. Use `find` and check for -1, or check `\"<\" in text` first."],
        solution="""
        def parse_contact(text):
            start = text.find("<")
            end = text.find(">", start + 1)
            if start == -1 or end == -1:
                return "", text.strip()
            return text[:start].strip(), text[start + 1:end].strip()
        """,
        why="""`index` is the right call when a missing separator is an error, but here the bare-email form is valid input, so
        absence is normal and `find` with a -1 check expresses that. Searching for `>` only after the `<` avoids matching a `>`
        that appears earlier in the name. Real email address parsing has many more rules; the standard library's
        `email.utils.parseaddr` handles them."""),
    refactor("Character loops to string methods", "medium",
        prompt="Rewrite with slicing and string methods instead of loops. Same results. Keep the tests green.",
        code="""
        def normalise_code(code):
            reversed_code = ""
            for ch in code:
                reversed_code = ch + reversed_code
            upper = ""
            for ch in reversed_code:
                if ch != " ":
                    upper += ch.upper()
            return upper
        """,
        tests="""
        assert normalise_code("ab 12 c") == "C21BA"
        assert normalise_code("") == ""
        assert normalise_code("x") == "X"
        """,
        hints=["Reverse with a slice, remove spaces with `replace`, and upper-case once."],
        solution="""
        def normalise_code(code):
            return code[::-1].replace(" ", "").upper()
        """,
        why="""Each loop rebuilt the string one character at a time, which is O(n²) for the first one (`ch + reversed_code` copies
        the growing string). Slicing, `replace` and `upper` each make one pass in C and say what they do. Chaining methods works
        because each one returns a new string, the direct consequence of immutability."""),
    predict("Triple-quoted prompts and indentation", "medium", tag="GenAI",
        code="""
        import textwrap

        def build_prompt(question):
            prompt = \"\"\"
            Answer briefly.
            Question: {q}
            \"\"\"
            return prompt.format(q=question)

        p = build_prompt("Refund time?")
        print(repr(p[:12]), p.count("\\n"))
        print(repr(textwrap.dedent(p).strip()))
        print(repr(build_prompt("x").splitlines()[1]))
        """,
        hints=["Everything between the triple quotes is in the string, including the first newline and the indentation of each line."],
        why="""A triple-quoted string inside an indented function contains the newline right after the opening quotes **and** the
        indentation spaces of every line, so the model receives a prompt that starts with a blank line and has the function's
        indentation (four spaces here) before each instruction. That wastes tokens and can change behaviour. `textwrap.dedent` removes the common indentation and
        `strip()` removes the blank first and last lines. `inspect.cleandoc` does both in one call."""),
)

section("hard", "Hard",
    predict("Code points, bytes and what you see", "hard",
        code="""
        import unicodedata

        a = "naïve"
        b = "nai\\u0308ve"
        print(a == b, len(a), len(b))
        print(b[::-1])
        nfc = unicodedata.normalize("NFC", b)
        print(nfc == a, len(nfc))
        flag = "\\U0001F1E9\\U0001F1EA"
        print(len(flag), len(flag.encode("utf-8")), len("é".encode("utf-8")), len("e".encode("utf-8")))
        """,
        hints=["`\\u0308` is a combining diaeresis: it attaches to the letter before it.",
               "A flag emoji is two regional-indicator code points; outside the basic range, each takes 4 bytes in UTF-8."],
        why="""The two spellings of "naïve" render the same, but one uses a precomposed `ï` (5 code points) and the other `i` plus a
        combining mark (6), so they are not equal. Reversing the decomposed form by code point puts the combining mark right after the
        `v`, so it attaches to the `v` instead of the `i`: the reversed word, `ev̈ian`, is visibly wrong. NFC normalisation composes `i` + mark into
        `ï`. The German flag is two code points and 8 UTF-8 bytes, `é` is 2 bytes and `e` is 1. Normalise before comparing or
        deduplicating text, and never assume one visible character is one code point or one byte."""),
    write("Longest common prefix", "hard", tag="Interview",
        prompt="""Write `common_prefix(strings)` returning the longest string that every string in the list starts with
        (`""` for an empty list). Compare characters position by position across all strings at once, and stop at the first
        mismatch or at the end of the shortest string.""",
        code="""
        def common_prefix(strings):
            pass
        """,
        tests="""
        assert common_prefix(["refund_policy", "refund_time", "refunds"]) == "refund"
        assert common_prefix(["agent", "rag"]) == ""
        assert common_prefix(["same", "same"]) == "same"
        assert common_prefix(["solo"]) == "solo"
        assert common_prefix([]) == "" and common_prefix(["", "x"]) == ""
        """,
        hints=["`zip(*strings)` yields tuples of the characters at each position, and stops at the shortest string.",
               "A position is common when its tuple has one distinct character: `len(set(chars)) == 1`."],
        solution="""
        def common_prefix(strings):
            prefix = []
            for chars in zip(*strings):
                if len(set(chars)) != 1:
                    break
                prefix.append(chars[0])
            return "".join(prefix)
        """,
        why="""`zip(*strings)` transposes the strings into columns of characters (4.3) and stops at the shortest one, so the
        "end of the shortest string" rule comes for free. A column is common when its set has one element. The work is
        O(total characters examined), and the prefix is collected in a list and joined once. A neat alternative uses the sort
        order: the common prefix of a whole list equals the common prefix of its lexicographically smallest and largest strings
        (`min` and `max`), which is a nice follow-up answer. The standard library also has `os.path.commonprefix`, which does
        this character by character despite its name."""),
    fix("Read the code: a log parser built on fixed positions", "hard", tag="Data work",
        prompt="""This parses lines from an LLM gateway log. It worked until the gateway started logging longer model names
        and request ids, and now the fields come out shifted, while lines without a `user=` field crash. Rewrite `parse_line`
        so it does not depend on fixed positions: the fields are separated by spaces, and `user=...` is optional.""",
        code="""
        def parse_line(line):
            date = line[0:10]
            level = line[11:16].strip()
            model = line[17:22]
            request_id = line[23:31]
            user = line[line.index("user=") + 5:]
            return {"date": date, "level": level, "model": model, "request_id": request_id, "user": user}
        """,
        tests="""
        a = parse_line("2025-06-01 INFO  small r-000017 user=ana")
        assert a == {"date": "2025-06-01", "level": "INFO", "model": "small", "request_id": "r-000017", "user": "ana"}
        b = parse_line("2025-06-02 ERROR gpt-large-2 req-0000000921 user=ben")
        assert b == {"date": "2025-06-02", "level": "ERROR", "model": "gpt-large-2", "request_id": "req-0000000921", "user": "ben"}
        c = parse_line("2025-06-03 WARN medium r-9")
        assert c["user"] is None and c["model"] == "medium" and c["request_id"] == "r-9"
        """,
        hints=["`line.split()` splits on any run of spaces, so the double space after `INFO` does not matter.",
               "The first four parts are fixed fields; look through the remaining parts for one that `startswith(\"user=\")`."],
        solution="""
        def parse_line(line):
            date, level, model, request_id, *extra = line.split()
            user = None
            for part in extra:
                if part.startswith("user="):
                    user = part[len("user="):]
            return {"date": date, "level": level, "model": model, "request_id": request_id, "user": user}
        """,
        why="""Fixed slices encode assumptions about field **widths**, so any change in a model name or id length shifts every
        later field without an error: the worst kind of parser bug, because it produces plausible garbage. Splitting on
        whitespace uses the actual separators, star unpacking (4.3) collects the optional fields, and `part[len("user="):]`
        avoids a hard-coded 5. Optional fields become `None` instead of a crash. For logs you control, write JSON lines instead
        (Module 12), and the parsing problem disappears."""),
    write("Find every occurrence, including overlaps", "hard", tag="Interview",
        prompt="""Write `find_all(text, sub)` returning all start positions of `sub` in `text`, **including overlapping**
        ones (`find_all("aaaa", "aa")` is `[0, 1, 2]`). Use `str.find` with a start position in a loop; an empty `sub` raises
        `ValueError`.""",
        code="""
        def find_all(text, sub):
            pass
        """,
        tests="""
        def raises(exc, f, *args):
            try:
                f(*args)
            except exc:
                return True
            return False
        assert find_all("aaaa", "aa") == [0, 1, 2]
        assert find_all("refund refunds", "refund") == [0, 7]
        assert find_all("abc", "x") == []
        assert "aaaa".count("aa") == 2
        assert raises(ValueError, find_all, "abc", "")
        """,
        hints=["`text.find(sub, start)` searches from `start`. After a match at `i`, continue from `i + 1` to allow overlaps."],
        solution="""
        def find_all(text, sub):
            if not sub:
                raise ValueError("sub must not be empty")
            positions = []
            i = text.find(sub)
            while i != -1:
                positions.append(i)
                i = text.find(sub, i + 1)
            return positions
        """,
        why="""Restarting the search at `i + 1` (rather than `i + len(sub)`) is what allows overlaps, which `str.count` and
        `re.finditer` do not report: the test shows `count` finding only 2. The empty-substring guard matters, because `""` is
        found at every position and the loop would never end (an infinite-loop bug, the kind 4.2 warned about). Each `find` is
        fast C code; for many patterns at once, an Aho-Corasick automaton is the standard algorithm."""),
)

section("interview", "Interview questions",
    explain("Why are Python strings immutable, and what does that imply for your code?", "medium", tag="Interview",
        why="""Immutability makes strings safe to share between names, functions and threads, lets them be hashed once and used as
        dict keys and set members, and allows Python to intern and cache them. The implications: every operation that "changes" a
        string returns a new one, so you must use the return value (`s = s.strip()`); building a long string piece by piece with
        `+` copies the growing text again and again, so collect pieces and `"".join` them; and there is no in-place character
        assignment, so for heavy character-level editing you would work on a list of characters or an `io.StringIO`. Mention
        that CPython's in-place `+=` optimisation is an implementation detail you should not rely on."""),
    explain("How do you build a large string efficiently, and why can repeated `+` be slow?", "medium", tag="Interview",
        why="""Each `a + b` allocates a new string and copies both operands, so appending n pieces one at a time copies about
        n²/2 pieces' worth of characters. `"".join(pieces)` computes the total size, allocates once and copies each piece once,
        O(total length). Alternatives: `io.StringIO` for writing text incrementally, or building lines and writing them to a
        file directly. CPython sometimes resizes a string in place for `s += t` when nothing else refers to `s`, so a `+=` loop
        can look fast in a micro-benchmark, but that breaks with f-strings, extra references, or other interpreters such as
        PyPy, so `join` is the portable answer."""),
    explain("Does `len(text)` tell you how long text is for a user, a database column or an LLM?", "hard", tag="Interview",
        why="""None of them reliably. `len` counts Unicode code points. A user sees **graphemes**: an accented letter can be two
        code points, and emoji with skin tones or flags are several, so visible length and `len` differ (use the `grapheme` or
        `regex` library's `\\X` to count them). A database or protocol limit usually counts **bytes** in an encoding: UTF-8 uses
        1 to 4 bytes per code point, so `len(text.encode("utf-8"))` is what a `VARBINARY` limit or a payload size cares about.
        An LLM counts **tokens** from its own tokenizer (subword pieces, roughly 3 to 4 English characters each, far fewer
        characters per token for code, numbers or many languages), and both context limits and cost are in tokens, so count with
        the model's tokenizer (for example `tiktoken`). Also mention Unicode normalisation (NFC) before comparing text."""),
)

recap(
    "A `str` is an immutable sequence of Unicode code points: indexing gives one-character strings, and every \"change\" builds a new string.",
    "Slicing follows the list rules. Prefer separators (`split`, `partition`, regex) over fixed positions for text you do not control.",
    "Build long strings with `\"\".join(pieces)`, not repeated `+` or f-strings in a loop.",
    "Strings compare by code point: capitals sort first and `\"10\" < \"9\"`. Use `casefold` for case-insensitive comparison.",
    "Watch the literal traps: a missing comma concatenates, `\\` starts escapes (use `r\"...\"`), triple quotes keep indentation. `len` counts code points, not graphemes, bytes or tokens.",
)
