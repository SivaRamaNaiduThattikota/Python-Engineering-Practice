from lesson import *
from diagrams import *

lesson(
    id="m5-2", num="5.2", title="String methods",
    intro="The methods you use daily for cleaning and parsing text, with the exact rules that cause bugs: `split()` versus "
          "`split(\" \")`, `strip` removing a set of characters rather than a prefix, `partition`, case methods that change "
          "length, the digit tests, `translate`, and building aligned text.",
    desc="`split`, `join`, `strip`, `replace`, `find`, case methods and checks.",
    keys="split rsplit maxsplit splitlines partition rpartition join strip lstrip rstrip removeprefix removesuffix replace upper lower title capitalize casefold isdigit isdecimal isnumeric isalpha isspace ljust rjust center zfill translate maketrans",
)

term("split()", "With no argument: split on any run of whitespace and drop empty strings. With a separator: split on exactly that text, keeping empty strings.")
term("partition", "`s.partition(sep)` returns a 3-tuple `(before, sep, after)` at the first `sep`, or `(s, \"\", \"\")` if it is absent. It never raises.")
term("strip(chars)", "Removes any of the given characters from both ends, in any order. It treats its argument as a set of characters, not a prefix.")
term("translate", "`s.translate(table)` maps, replaces or deletes many characters in one pass, using a table from `str.maketrans`.")

section("split", "Splitting and joining",
    fig(table(["call", "result"], [
        ["'a,b,,c'.split(',')", "['a', 'b', '', 'c']"],
        ["'  a   b '.split()", "['a', 'b']"],
        ["'k=v=w'.split('=', 1)", "['k', 'v=w']"],
        ["', '.join(['a', 'b'])", "'a, b'"],
    ], label="split and join"),
        "With a separator, `split` keeps empty fields; with no argument, it splits on any whitespace and drops the empty ones."),
    p("""`split` is the workhorse of text parsing, and its two modes behave differently in a way that matters:"""),
    p("""- **`s.split()`** with no argument splits on **any run of whitespace** (spaces, tabs, newlines), ignores leading and
      trailing whitespace, and never returns empty strings. It is the right choice for "the words of this text".
    - **`s.split(sep)`** splits on **exactly** `sep`, and keeps the empty strings between consecutive separators and at the
      ends. It is the right choice for formats with a fixed delimiter, where an empty field is meaningful."""),
    ex("""
    line = "  refund   policy\\tEU  "
    print(line.split())                    # words
    print(line.split(" "))                 # every single space is a separator
    print("a,,b,".split(","))              # empty fields are kept
    print("k=v=w".split("=", 1), "a/b/c".rsplit("/", 1))   # maxsplit: split only so many times
    print("one\\ntwo\\r\\nthree\\n".splitlines(), "one\\ntwo\\n".split("\\n"))
    """, "split.py"),
    p("""`maxsplit` limits the number of splits, which keeps any later separators inside the last part: `"k=v=w".split("=",
    1)` gives a key and a value that may itself contain `=`. `rsplit` splits from the right, so `rsplit("/", 1)` separates a
    file name from its directory. `splitlines()` splits on every kind of line break (`\\n`, `\\r\\n` and others) and does not
    produce a trailing empty string, which `split("\\n")` does when the text ends with a newline."""),
    p("""`sep.join(iterable)` is the inverse: it puts `sep` **between** the items, which must all be strings (a number in the
    list raises `TypeError`; convert with `map(str, ...)`). It is the efficient way to build text (5.1)."""),
    callout("sql", "SQL / Power BI", """`split(",")` is SQL Server's `STRING_SPLIT(s, ',')` and Power Query's "Split column by
    delimiter"; `",".join(values)` is `STRING_AGG(value, ',')` or DAX `CONCATENATEX`. Power Query's "Trim" and "Clean"
    steps correspond to `strip()` and removing control characters."""),
)

section("partition", "`partition`: split once, never fail",
    p("""`s.partition(sep)` splits at the **first** `sep` and always returns three parts: the text before, the separator
    itself, and the text after. If `sep` is not present, you get `(s, "", "")`: the middle part being empty tells you it was
    missing. `rpartition` does the same at the **last** occurrence. Because it always returns three items, it unpacks
    safely, which makes it ideal for "key: value" lines, URLs and file names."""),
    ex("""
    key, sep, value = "Authorization: Bearer abc:123".partition(": ")
    print(key, "|", value)
    print("no separator here".partition("="))
    base, dot, ext = "report.final.pdf".rpartition(".")
    print(base, ext, "README".rpartition("."))
    """, "partition.py"),
)

section("strip", "Trimming: `strip` removes characters, `removeprefix` removes a prefix",
    fig(table(["call on 'www.site.com'", "result"], [
        [".strip('w.')", "'site.com'  (removes any of w and .)"],
        [".removeprefix('www.')", "'site.com'"],
        ["'wow.site'.strip('w.')", "'ow.site'  (stops at the first o)"],
    ], hl={(2, 1)}, label="strip removes characters, removeprefix removes a prefix"),
        "`strip` treats its argument as a set of characters, not a word; use `removeprefix` and `removesuffix` for exact text."),
    p("""`strip()`, `lstrip()` and `rstrip()` with no argument remove whitespace from the ends. With an argument, they remove
    **any of those characters**, in any order and any number of times, until they meet a character not in the set. They do
    **not** remove a prefix or suffix as a unit. That is a famous bug: `url.lstrip("https://")` removes every leading
    `h`, `t`, `p`, `s`, `:` and `/`, which also eats the start of a domain such as `"shop.example.com"`."""),
    ex("""
    print("xxhixx".strip("x"), "  hi \\n".strip(), "--==hi==--".strip("-="))
    url = "https://shop.example.com/refunds"
    print(url.lstrip("https://"))                 # removes characters: 'shop' loses its letters too
    print(url.removeprefix("https://"))           # removes the prefix once, exactly
    print("report.csv.csv".removesuffix(".csv"), "data.json".rstrip(".json"))
    """, "strip.py"),
    p("""Use `removeprefix` and `removesuffix` (Python 3.9+) to remove a known prefix or suffix exactly once; they return the
    string unchanged if it does not start or end with it. Keep `strip(chars)` for its real purpose: trimming a **set** of
    padding characters such as quotes, punctuation or zero-width spaces."""),
)

section("case", "Case, replacing and testing",
    p("""`upper`, `lower`, `casefold`, `title`, `capitalize` and `swapcase` all return new strings. Two warnings. `title()`
    upper-cases the first letter after **any** non-letter, so `"o'neil's"` becomes `"O'Neil'S"`; it is meant for simple
    words, not names or headlines. And case mapping can change the **length** of a string, because some characters map to
    several (`"ß".upper()` is `"SS"`), so never assume `len(s.upper()) == len(s)`."""),
    ex("""
    print("o'neil's refund".title(), "it's fine".capitalize())
    print("ß".upper(), len("Straße".upper()), "ﬁle".upper())
    print("refund refund refund".replace("refund", "return", 2))
    """, "case.py"),
    p("""`replace(old, new, count)` replaces non-overlapping occurrences, left to right, optionally only the first `count`.
    The `is...` tests check that **every** character is of a kind, and return `False` for the empty string. The digit tests
    differ in what they accept, which matters for user input:"""),
    ex("""
    for s in ["42", "-5", "3.2", "²", "½", "٤٢", "", " 7"]:
        print(f"{s!r:6} isdecimal={s.isdecimal()!s:5} isdigit={s.isdigit()!s:5} isnumeric={s.isnumeric()!s:5}")
    print("Refund".isalpha(), "café".isalpha(), "abc123".isalnum(), " \\t\\n".isspace())
    """, "is_tests.py"),
    p("""None of them recognise `"-5"` or `"3.2"`, and `isdigit` accepts `"²"`, which `int()` rejects. To check whether text is
    a number, the reliable test is to **try converting it** (`int(s)` or `float(s)` inside `try`, Module 8). `isdecimal` is the
    closest match to "characters `int()` accepts"; note that it accepts digits from other scripts, such as Arabic-Indic
    `"٤٢"`, which `int` also converts to 42."""),
)

section("translate", "`translate` and alignment",
    p("""For mapping or deleting **many characters at once**, `str.maketrans` builds a table and `translate` applies it in a
    single pass in C: much faster and clearer than a chain of `replace` calls. `maketrans` takes either a dict from
    characters to replacements (or `None` to delete), or two equal-length strings to map, plus an optional third string of
    characters to delete."""),
    ex("""
    import string

    no_punct = str.maketrans("", "", string.punctuation)
    print("Refund?! (EU-only), see: faq.".translate(no_punct))
    smart = str.maketrans({"\\u2018": "'", "\\u2019": "'", "\\u201c": '"', "\\u201d": '"', "\\u00a0": " "})
    print("\\u201cIt\\u2019s\\u00a0fine\\u201d".translate(smart))
    """, "translate.py"),
    p("""For fixed-width text such as console tables and logs, `ljust(width)`, `rjust(width)` and `center(width)` pad a string
    to a width (with spaces or a fill character), and `zfill(width)` pads a number string with zeros, keeping a sign in front.
    f-strings can do the same with format specs (5.3)."""),
    ex("""
    rows = [("faq.md", 0.913), ("terms-and-conditions.md", 0.4), ("api.md", 0.75)]
    width = max(len(name) for name, _ in rows)
    for name, score in rows:
        print(name.ljust(width), str(round(score, 2)).rjust(5))
    print("7".zfill(3), "-7".zfill(4))
    """, "align.py"),
)

section("warmup", "Warm-up",
    predict("split with and without a separator", "easy",
        code="""
        s = " a  b,c ,, d "
        print(s.split())
        print(s.split(" "))
        print(s.split(","))
        print([p.strip() for p in s.split(",") if p.strip()])
        print("a\\nb\\n".split("\\n"), "a\\nb\\n".splitlines())
        """,
        hints=["`split()` merges runs of whitespace and drops empties; `split(\" \")` treats each single space as a separator."],
        why="""`split()` gives the "words": runs of whitespace collapse and the ends are ignored. `split(" ")` keeps an empty string
        for every extra space. `split(",")` keeps the empty field between `,,`, which for a CSV-like format is correct. The
        cleaning comprehension strips each field and drops empty ones, a common one-liner. `split("\\n")` leaves a trailing empty
        string when the text ends with a newline; `splitlines()` does not."""),
    fix("Stripping a URL prefix eats the domain", "easy", tag="Data work",
        prompt="""`domain(url)` should return the host of an `https://` or `http://` URL. For `"https://shop.example.com/x"` it
        returns `"op.example.com"`. Fix it.""",
        code="""
        def domain(url):
            return url.lstrip("https://").lstrip("http://").split("/")[0]
        """,
        tests="""
        assert domain("https://shop.example.com/refunds") == "shop.example.com"
        assert domain("http://help.site.io") == "help.site.io"
        assert domain("https://www.x.com/a/b") == "www.x.com"
        assert domain("sftp.host.org/file") == "sftp.host.org"
        """,
        hints=["`lstrip(\"https://\")` removes any of the characters h, t, p, s, : and / from the start, not the prefix.",
               "`removeprefix` removes an exact prefix once, and does nothing if it is not there."],
        solution="""
        def domain(url):
            rest = url.removeprefix("https://").removeprefix("http://")
            return rest.partition("/")[0]
        """,
        why="""`lstrip` treats its argument as a **set** of characters and keeps removing while the next character is in the set, so
        `"shop"` loses `s` and `h` too. `removeprefix` removes the exact prefix or nothing. `partition("/")[0]` is the part before
        the first slash, or the whole string when there is none. For real URLs use `urllib.parse.urlsplit(url).hostname`, which
        also handles ports, credentials and upper-case schemes."""),
    write("A URL slug without regex", "easy", tag="Data work",
        prompt="""Write `slugify(title)` that lower-cases the title, turns every run of characters that are not letters or
        digits into a single `-`, and removes `-` at the ends. Use `isalnum` and `join`, not regex.""",
        code="""
        def slugify(title):
            pass
        """,
        tests="""
        assert slugify("Refund Policy (EU) — 2025!") == "refund-policy-eu-2025"
        assert slugify("  Hello,   World  ") == "hello-world"
        assert slugify("---") == ""
        assert slugify("Café Ünique") == "café-ünique"
        """,
        hints=["Replace each non-alphanumeric character with a space, then `\"-\".join(text.split())` collapses runs and drops the ends."],
        solution="""
        def slugify(title):
            spaced = "".join(ch if ch.isalnum() else " " for ch in title.lower())
            return "-".join(spaced.split())
        """,
        why="""Turning separators into spaces and then using `split()` reuses its two best properties: runs collapse into one
        break, and the ends disappear, so `join` with `-` produces exactly one dash between words and none at the edges.
        `isalnum` is Unicode-aware, so accented letters stay. Many systems also remove accents for slugs (normalise to NFKD and
        drop combining marks, 5.4) so URLs stay ASCII."""),
    predict("What the digit tests accept", "easy",
        code="""
        tests = ["7", "007", "-7", "7.5", "²", "½", "٧", ""]
        print([t for t in tests if t.isdecimal()])
        print([t for t in tests if t.isdigit()])
        print([t for t in tests if t.isnumeric()])
        print(int("007"), int("٧"), int(" 7 "))
        """,
        hints=["Each test is stricter than the next: `isdecimal` ⊂ `isdigit` ⊂ `isnumeric`. None accept signs or decimal points."],
        why="""`isdecimal` accepts only characters that are decimal digits in some script, including the Arabic-Indic `"٧"`.
        `isdigit` also accepts superscripts like `"²"`, and `isnumeric` also accepts fractions like `"½"`. All three reject the
        sign and the decimal point, and are `False` for the empty string. `int` accepts leading zeros, other scripts' digits and
        surrounding whitespace. So "is this a number?" is best answered by attempting the conversion."""),
)

section("medium", "Medium",
    write("Parse `key: value` lines", "medium", tag="GenAI",
        prompt="""An LLM was asked to answer as lines of `key: value`. Write `parse_fields(text)` that returns a dict from
        lower-cased, stripped keys to stripped values. Skip blank lines and lines starting with `#`. Values may themselves contain
        `:`. A line without `:` raises `ValueError` naming the line.""",
        code="""
        def parse_fields(text):
            pass
        """,
        tests="""
        def raises(exc, f, *args):
            try:
                f(*args)
            except exc as e:
                return str(e)
            return False
        out = parse_fields("Title: Refund delayed\\n\\n# model notes\\nPriority : high\\nURL: https://x.io/a")
        assert out == {"title": "Refund delayed", "priority": "high", "url": "https://x.io/a"}
        assert parse_fields("") == {}
        msg = raises(ValueError, parse_fields, "title: ok\\nnot a field")
        assert msg and "not a field" in msg
        """,
        hints=["`text.splitlines()`, then `key, sep, value = line.partition(\":\")`. An empty `sep` means the line had no colon."],
        solution="""
        def parse_fields(text):
            out = {}
            for line in text.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                key, sep, value = line.partition(":")
                if not sep:
                    raise ValueError(f"not a key: value line: {line!r}")
                out[key.strip().lower()] = value.strip()
            return out
        """,
        why="""`partition(":")` splits only at the **first** colon, so the URL keeps its own colon, and its empty middle part is a
        clean signal for a malformed line. `split(":")` would cut the URL into pieces. Raising with the offending line in the
        message makes the error useful to log or to send back to the model for a retry. For anything nested or typed, ask the
        model for JSON instead and parse it with `json.loads` (Module 12)."""),
    fix("Title case that mangles names", "medium", tag="Data work",
        prompt="""`display_name` formats names from a CRM: the first letter of each **space-separated** word upper-case, the
        rest lower-case, and extra spaces removed. `title()` gets it wrong: `"mcdonald's"` becomes `"Mcdonald'S"`. Fix it.""",
        code="""
        def display_name(name):
            return name.title()
        """,
        tests="""
        assert display_name("mcdonald's pub") == "Mcdonald's Pub"
        assert display_name("  ana   lopez ") == "Ana Lopez"
        assert display_name("o'neil") == "O'neil"
        assert display_name("") == ""
        """,
        hints=["Split on whitespace, then build each word as `w[:1].upper() + w[1:].lower()`."],
        solution="""
        def display_name(name):
            return " ".join(w[:1].upper() + w[1:].lower() for w in name.split())
        """,
        why="""`title()` treats every non-letter, including an apostrophe, as a word boundary, so the `s` after `'` is capitalised.
        Splitting on whitespace gives the words you actually mean, and `w[:1]` (not `w[0]`) is safe even for an empty string.
        `str.capitalize` per word would do the same. Note that this rule is still wrong for names like "McDonald" or "van der
        Berg": real name formatting is cultural, which is why systems should store names as typed rather than re-case them."""),
    trace("Taking a path apart", "medium",
        prompt="Fill in `head` and `tail` after each marked line.",
        code="""
        path = "data/raw/2025/report.final.tar.gz"
        head, _, tail = path.rpartition("/")  # row: "rpartition('/')"
        head, _, tail = tail.partition(".")  # row: "partition('.')"
        head, _, tail = path.rpartition(".")  # row: "rpartition('.')"
        head, tail = path.split("/", 1)  # row: "split('/', 1)"
        """,
        trace_vars=["head", "tail"],
        hints=["`partition` uses the first separator, `rpartition` the last; `split(sep, 1)` splits once from the left."],
        why="""The last `/` separates the directory from the file name. The first `.` of the file name splits off the stem
        `"report"` and leaves `"final.tar.gz"`. The last `.` gives the final extension only, `"gz"`, which is why "the extension"
        of `.tar.gz` files is ambiguous. `split("/", 1)` separates the first directory from the rest. For real paths use
        `pathlib.Path` (Module 12), whose `.name`, `.stem`, `.suffix` and `.suffixes` encode these exact rules."""),
    choose("Removing punctuation: replace loop or translate", "medium", tag="ML",
        prompt="Both remove all ASCII punctuation from 2,000 reviews before tokenising. Which is faster?",
        setup="""import string
reviews = ["Great!!! Refund came fast, thanks; 10/10 (would buy again)... :-)"] * 2000
table = str.maketrans("", "", string.punctuation)""",
        options={
            "a": "out = []\nfor r in reviews:\n    for p in string.punctuation:\n        r = r.replace(p, \"\")\n    out.append(r)",
            "b": "out = [r.translate(table) for r in reviews]",
        },
        answer="b",
        hints=["`string.punctuation` has 32 characters. How many passes over each review does A make?"],
        why="""A makes 32 passes over every review, one `replace` per punctuation character, and builds a new string each time.
        B makes **one** pass per review, looking each character up in the table. `replace` is fast C code too, so the measured
        gap is a few times rather than 32 times, but A still pays for 32 passes and up to 32 new strings per review, and the gap
        grows with the number of characters to replace. The same reasoning applies whenever you chain many `replace` calls for
        single characters."""),
    write("An aligned text table", "medium", tag="Data work",
        prompt="""Write `format_table(header, rows)` that returns the table as a string: one line per row, columns separated by
        two spaces, each column as wide as its widest cell (header included). Text columns are left-aligned; columns whose cells
        are all numbers (`int` or `float`) are right-aligned. Lines must have no trailing spaces.""",
        code="""
        def format_table(header, rows):
            pass
        """,
        tests="""
        out = format_table(["doc", "score", "tokens"], [["faq.md", 0.91, 120], ["terms-and-conditions.md", 0.4, 2300]])
        assert out == (
            "doc                      score  tokens\\n"
            "faq.md                    0.91     120\\n"
            "terms-and-conditions.md    0.4    2300"
        )
        assert format_table(["a"], []) == "a"
        """,
        hints=["Convert every cell with `str`, then compute each column's width with `max(len(...))` over the header and the cells.",
               "A column is numeric when every row's value in it is an `int` or `float`. Join the padded cells with two spaces and `rstrip` each line."],
        solution="""
        def format_table(header, rows):
            cols = list(zip(*([header] + rows)))
            widths = [max(len(str(c)) for c in col) for col in cols]
            numeric = [bool(rows) and all(isinstance(r[i], (int, float)) for r in rows) for i in range(len(header))]
            lines = []
            for row in [header] + rows:
                cells = [str(c).rjust(w) if num else str(c).ljust(w) for c, w, num in zip(row, widths, numeric)]
                lines.append("  ".join(cells).rstrip())
            return "\\n".join(lines)
        """,
        why="""Transposing with `zip(*...)` (4.3) gives each column, so widths are one `max` per column. Right-aligning numbers makes
        their digits line up, the convention in every spreadsheet and report; the header of a numeric column is right-aligned too,
        so it sits over its numbers. `rstrip` removes the padding after the last column, which would otherwise make tests and diffs
        noisy. Libraries such as `tabulate` and `rich` do this (with borders and colours); pandas does it in `DataFrame.to_string`."""),
    fix("Labels that look the same but do not match", "medium", tag="ML",
        prompt="""Annotators typed labels by hand. `clean_label` should map variants such as `" New  York "`,
        `"new york\\t"` and `"NEW\\u00a0YORK"` (with a non-breaking space) to the same value, `"new york"`. It still produces
        three different labels. Fix it.""",
        code="""
        def clean_label(label):
            return label.strip().lower()
        """,
        tests="""
        variants = [" New  York ", "new york\\t", "NEW\\u00a0YORK", "New\\nYork"]
        assert {clean_label(v) for v in variants} == {"new york"}
        assert clean_label("  Spam ") == "spam" and clean_label("") == ""
        """,
        hints=["`strip` only trims the ends. Internal runs of whitespace (including a non-breaking space) need to be collapsed too.",
               "`split()` with no argument splits on all Unicode whitespace, `\\u00a0` included."],
        solution="""
        def clean_label(label):
            return " ".join(label.split()).casefold()
        """,
        why="""The variants differ **inside** the string: two spaces, a tab, a non-breaking space, a newline. `" ".join(label.split())`
        collapses every run of any whitespace into one space and trims the ends in one step, because `split()` recognises all
        Unicode whitespace. `casefold` handles case more thoroughly than `lower`. Inconsistent labels like these silently split one
        class into several in training data, which shows up as a model "confusing" classes that are actually identical."""),
    refactor("A chain of replace calls", "medium",
        prompt="Replace the chain with one translation table, same output. Keep the tests green.",
        code="""
        def normalise_quotes(text):
            text = text.replace("\\u2018", "'")
            text = text.replace("\\u2019", "'")
            text = text.replace("\\u201c", '"')
            text = text.replace("\\u201d", '"')
            text = text.replace("\\u2013", "-")
            text = text.replace("\\u2014", "-")
            text = text.replace("\\u00a0", " ")
            return text
        """,
        tests="""
        assert normalise_quotes("\\u201cIt\\u2019s\\u00a0fine\\u201d \\u2014 ok") == '"It\\'s fine" - ok'
        assert normalise_quotes("plain") == "plain"
        """,
        hints=["Build the table once at module level with `str.maketrans({...})`, from each character to its replacement."],
        solution="""
        TYPOGRAPHY = str.maketrans({
            "\\u2018": "'", "\\u2019": "'", "\\u201c": '"', "\\u201d": '"',
            "\\u2013": "-", "\\u2014": "-", "\\u00a0": " ",
        })

        def normalise_quotes(text):
            return text.translate(TYPOGRAPHY)
        """,
        why="""Seven passes over the text become one, and the mapping becomes **data** that is easy to read and extend. Building the
        table once at module level avoids rebuilding it per call. Normalising "smart" punctuation like this is a common step before
        matching or deduplicating text copied from documents and web pages, and before comparing LLM outputs with expected
        answers."""),
    predict("Splitting model output into lines", "medium", tag="GenAI",
        code="""
        reply = "1. Check the order\\r\\n2. Refund\\r\\n\\r\\n3. Close ticket\\r\\n"
        print(len(reply.split("\\n")), repr(reply.split("\\n")[0]))
        print(reply.splitlines())
        steps = [line for line in reply.splitlines() if line.strip()]
        print(len(steps), [s.partition(". ")[2] for s in steps])
        """,
        hints=["`\\r\\n` is a Windows line break. `split(\"\\n\")` leaves the `\\r` at the end of each line."],
        why="""Splitting on `"\\n"` keeps a `\\r` at the end of every line, plus empty strings for the blank line and the trailing
        break, so line-based comparisons quietly fail (`"2. Refund\\r" != "2. Refund"`). `splitlines()` understands `\\r\\n` and
        drops the trailing break. Filtering with `line.strip()` removes blank lines, and `partition(". ")` strips the numbering.
        Model output, HTTP bodies and files from Windows all produce `\\r\\n`, so prefer `splitlines()` for text."""),
)

section("hard", "Hard",
    write("Greedy word wrap", "hard", tag="Interview",
        prompt="""Write `wrap(text, width)` that returns a list of lines, each at most `width` characters, filled greedily with
        whole words separated by single spaces. A word longer than `width` goes on its own line, unbroken. Whitespace in the
        input is normalised.""",
        code="""
        def wrap(text, width):
            pass
        """,
        tests="""
        t = "Refunds are processed within five business days of the request"
        assert wrap(t, 20) == ["Refunds are", "processed within", "five business days", "of the request"]
        assert wrap("a supercalifragilistic word", 10) == ["a", "supercalifragilistic", "word"]
        assert wrap("", 10) == [] and wrap("  one  ", 3) == ["one"]
        assert all(len(l) <= 20 for l in wrap(t, 20))
        """,
        hints=["Walk the words with a `current` list and its length. Adding a word costs `len(word)` plus one space if the line is not empty.",
               "When the next word does not fit, finish the current line with `\" \".join(current)` and start a new one with that word."],
        solution="""
        def wrap(text, width):
            lines, current, length = [], [], 0
            for word in text.split():
                extra = len(word) + (1 if current else 0)
                if current and length + extra > width:
                    lines.append(" ".join(current))
                    current, length = [word], len(word)
                else:
                    current.append(word)
                    length += extra
            if current:
                lines.append(" ".join(current))
            return lines
        """,
        why="""Tracking the current length avoids re-measuring the joined line for every word, so the function is O(n). The
        `if current` checks handle two edge cases at once: the first word on a line needs no space, and a word longer than the
        width is accepted onto an empty line instead of looping forever. The final `if current` flushes the last line, the classic
        thing to forget (1.2, run lengths). `textwrap.wrap` in the standard library does this with more options, including
        breaking long words."""),
    fix("Read the code: a prompt renderer that can be hijacked", "hard", tag="GenAI",
        prompt="""This renders prompt templates with `{placeholders}` by repeated `replace`. Two problems: `{name}` also eats the
        start of `{name_full}`, and a user who types `{system}` into their question gets the system text injected into their
        prompt. Rewrite `render` so each placeholder is replaced exactly once, by name, and values are never re-scanned.""",
        code="""
        def render(template, values):
            out = template
            for key, value in values.items():
                out = out.replace("{" + key, str(value))
            return out.replace("}", "")
        """,
        tests="""
        tpl = "Hi {name} ({name_full}). Q: {question}"
        vals = {"name": "Ana", "name_full": "Ana Lopez", "question": "What is {system}?", "system": "SECRET RULES"}
        assert render(tpl, vals) == "Hi Ana (Ana Lopez). Q: What is {system}?"
        assert render("{a}{b}", {"a": 1, "b": 2}) == "12"
        def raises(exc, f, *args):
            try:
                f(*args)
            except exc:
                return True
            return False
        assert raises(KeyError, render, "{missing}", {})
        """,
        hints=["`str.format_map(values)` parses the template once and inserts each value as plain text, without looking for placeholders inside it.",
               "It raises `KeyError` for a placeholder with no value, which is what the last test wants."],
        solution="""
        def render(template, values):
            return template.format_map(values)
        """,
        why="""The replace loop has two classic flaws. Replacing `"{name"` (without the closing brace) also matches the start of
        `"{name_full"`, and the order of the dict decides which wins. Worse, each replacement is applied to text that already
        contains user values, so a value like `"{system}"` becomes a placeholder and gets filled with secret instructions: a
        template injection, the string-level cousin of prompt injection. `format_map` parses the template once, substitutes by
        exact field name, and never re-scans inserted values, so user text appears literally. (Templates themselves must come
        from you, not users: `format` can read attributes of the values, for example `{obj.__class__}`.)"""),
    write("Split a line with quoted fields", "hard", tag="Data work",
        prompt="""Write `split_fields(line, sep=",")` that splits on `sep` except inside double quotes, removes the quotes from
        quoted fields, and keeps empty fields. Quotes inside a quoted field are written twice (`""`), as in CSV. Do it with a
        single loop over the characters, not the `csv` module.""",
        code="""
        def split_fields(line, sep=","):
            pass
        """,
        tests="""
        assert split_fields('a,b,c') == ["a", "b", "c"]
        assert split_fields('1,"Lopez, Ana",ana@x.io') == ["1", "Lopez, Ana", "ana@x.io"]
        assert split_fields('x,,"",y') == ["x", "", "", "y"]
        assert split_fields('\"He said \"\"hi\"\"\",2') == ['He said "hi"', "2"]
        assert split_fields("") == [""]
        """,
        hints=["Keep `fields`, the characters of the current field, and a flag `in_quotes`. A `sep` ends a field only when not in quotes.",
               "A `\"` inside quotes followed by another `\"` is a literal quote; otherwise it closes the quotes. Use an index loop so you can look one character ahead."],
        solution="""
        def split_fields(line, sep=","):
            fields, current, in_quotes = [], [], False
            i = 0
            while i < len(line):
                ch = line[i]
                if in_quotes:
                    if ch == '"' and i + 1 < len(line) and line[i + 1] == '"':
                        current.append('"')
                        i += 1
                    elif ch == '"':
                        in_quotes = False
                    else:
                        current.append(ch)
                elif ch == '"':
                    in_quotes = True
                elif ch == sep:
                    fields.append("".join(current))
                    current = []
                else:
                    current.append(ch)
                i += 1
            fields.append("".join(current))
            return fields
        """,
        why="""`line.split(",")` breaks `"Lopez, Ana"` into two fields, which shifts every later column by one: the most common bug in
        hand-rolled CSV parsing. A small state machine (inside or outside quotes) fixes it, with one look-ahead for the doubled
        quote. Characters are collected in a list and joined per field (5.1). The final `append` keeps the last field even when it
        is empty. In real code use the `csv` module (Module 12), which implements exactly these rules plus newlines inside quoted
        fields and other dialects."""),
    predict("Case mapping can change length", "hard",
        code="""
        words = ["straße", "ﬁle", "İstanbul", "ǅemal"]
        for w in words:
            print(w, len(w), w.upper(), len(w.upper()), w.lower(), len(w.lower()))
        print("STRASSE".lower() == "straße".lower(), "STRASSE".casefold() == "straße".casefold())
        print("ǅ".isupper(), "ǅ".istitle(), "ǅ".upper(), "ǅ".lower())
        """,
        hints=["Some characters have no single upper- or lower-case form, so they map to two code points.",
               "`ǅ` is a title-case letter: neither upper nor lower."],
        why="""`ß` upper-cases to `SS` and the `ﬁ` ligature to `FI`, so the strings get longer. Lower-casing `İ` (capital I with a dot)
        gives `i` plus a combining dot, also longer. `ǅ` is one of the rare title-case letters, which is why `isupper` is `False`.
        Two lessons follow. Code that indexes into `s.upper()` using positions from `s` can be off. And for case-insensitive
        matching, compare `casefold()` forms, which map `ß` and `SS` to the same thing; `lower()` does not."""),
)

section("interview", "Interview questions",
    explain("What is the difference between `s.split()` and `s.split(\" \")`?", "medium", tag="Interview",
        why="""`split()` with no argument splits on any run of whitespace (spaces, tabs, newlines, and Unicode spaces such as a
        non-breaking space), ignores leading and trailing whitespace and never returns empty strings: it gives the words.
        `split(" ")` splits on each single space character only: consecutive spaces produce empty strings, tabs and newlines are
        not separators, and leading or trailing spaces produce empty strings at the ends. Use `split()` for natural text and
        `split(sep)` for delimited formats where empty fields matter. Mention `maxsplit`, `rsplit`, `partition` for "split once"
        and `splitlines` for line breaks."""),
    explain("Why does `\"https://shop.com\".lstrip(\"https://\")` give `\"op.com\"`?", "medium", tag="Interview",
        why="""`lstrip` (like `strip` and `rstrip`) treats its argument as a **set of characters**, not as a prefix: it removes
        characters from the left as long as each one is in `{"h", "t", "p", "s", ":", "/"}`. After `https://` it continues through
        `s` and `h` of `shop` and stops at `o`. To remove an exact prefix or suffix once, use `removeprefix` / `removesuffix`
        (Python 3.9+) or slice after a `startswith` check. The same trap applies to `rstrip(".json")`, which would also eat a
        trailing `n` or `o` of the name. Use `strip(chars)` only for trimming a set of padding characters."""),
    explain("How would you normalise text before matching or deduplicating it, and what can go wrong?", "hard", tag="Interview",
        why="""A typical pipeline: Unicode-normalise (NFC to unify composed and decomposed accents, or NFKC to also fold
        compatibility forms such as ligatures and full-width letters), `casefold` for case, collapse whitespace with
        `" ".join(s.split())`, map typographic quotes and dashes with a translation table, and optionally remove punctuation or
        accents. What can go wrong: each step loses information, so normalise a **copy** for matching and keep the original
        for display; NFKC changes meaning in some cases (`"²"` becomes `"2"`); removing accents merges different words in some
        languages; and normalising one side of a comparison but not the other silently breaks matches. Apply the same function
        to both sides, and test it with real messy examples."""),
)

recap(
    "`split()` gives words (any whitespace, no empties); `split(sep)` follows a delimiter exactly and keeps empty fields. `splitlines()` handles `\\r\\n`.",
    "`partition` and `rpartition` split once and always return three parts: the safe way to parse `key: value`, URLs and file names.",
    "`strip(chars)` removes a set of characters. Use `removeprefix` / `removesuffix` for an exact prefix or suffix.",
    "Case mapping can change length; compare with `casefold()`. The `is...` digit tests do not answer \"is this a number?\": try converting.",
    "Use `translate` for many single-character replacements, `join` to build, and `format_map` (not repeated `replace`) to fill templates.",
)
