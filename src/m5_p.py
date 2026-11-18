from lesson import *

lesson(
    id="m5-p", num="5.P", title="Module 5 practice set and mini project",
    intro="Mixed problems from all of Module 5: string basics, methods, formatting, Unicode and bytes, and regular "
          "expressions. Then a mini project that needs all of it: preparing raw documents for a RAG index.",
    desc="Mixed problems from the whole module, then one small program that uses all of it.",
    keys="practice mixed review project ingestion chunking rag strings methods fstring format unicode bytes utf-8 normalize regex streaming sse tool call",
)

section("how", "How to use this page",
    p("""Text problems usually mix several layers, and most bugs come from mixing them up. Before you write code, ask three
    questions. **Bytes or text?** Anything from a file, socket or API arrives as bytes and must be decoded once, at the edge,
    with a known encoding (5.4). **Fixed text or a pattern?** For fixed text, string methods are faster and clearer (5.1,
    5.2); for patterns, use a regex (5.5). **Data or display?** Keep values as numbers and dates while you compute, and
    format them only at the end, with a format spec (5.3)."""),
    p("""The problems are not grouped by lesson on purpose: deciding which tool fits is part of each one. The last problem is
    a mini project that combines every lesson in one realistic pipeline."""),
)

section("set", "Practice set",
    predict("A bit of every lesson", "easy",
        code="""
        s = "  Refund,  late ;fee  "
        print(s.split(), s.split(" ")[:4])
        print(s.strip().partition(";"))
        print(f"[{s.strip()[:6]:>8}]", f"{0.1 + 0.2:.3f}", f"{1234567:,}")
        print(len("café"), len("café".encode()), "é".encode())
        """,
        hints=["`split()` with no argument splits on runs of whitespace and drops empty strings; `split(\" \")` does not.",
               "`é` takes two bytes in UTF-8."],
        why="""`split()` treats any run of whitespace as one separator and ignores leading and trailing whitespace, while `split(" ")`
        splits on every single space, so leading spaces produce empty strings (5.2). `partition` returns the part before, the
        separator and the part after, always three items. In the f-string, `:>8` right-aligns the slice in 8 characters, `.3f`
        rounds for display, and `,` adds thousands separators (5.3). `café` is 4 characters but 5 UTF-8 bytes, because `é` is
        encoded as the two bytes `c3 a9` (5.4)."""),
    write("Cut a reply at the first stop sequence", "easy", tag="GenAI",
        prompt="""LLM APIs accept **stop sequences**: generation ends just before the first one that appears. Write
        `apply_stops(text, stops)` that returns `text` cut before the **earliest** occurrence of any stop string (the stop itself
        is removed), or the whole text if none appears.""",
        code="""
        def apply_stops(text, stops):
            pass
        """,
        tests="""
        reply = "Answer: 42\\nObservation: done\\nUser: next"
        assert apply_stops(reply, ["User:", "\\nObservation:"]) == "Answer: 42"
        assert apply_stops(reply, ["Nope"]) == reply
        assert apply_stops("abc", []) == "abc"
        assert apply_stops("xxSTOPyySTOP", ["STOP", "yy"]) == "xx"
        """,
        hints=["`text.find(stop)` returns `-1` when the stop is absent. Keep the smallest index that is not `-1`."],
        solution="""
        def apply_stops(text, stops):
            positions = [i for stop in stops if (i := text.find(stop)) != -1]
            return text[:min(positions)] if positions else text
        """,
        why="""The cut must happen at the earliest position over **all** stops, not at the first stop in the list: `"User:"` appears
        later in the text than `"\\nObservation:"`, even though it is listed first. `find` returns `-1` for a missing stop, and
        `-1` would slice off the last character, so it has to be filtered out (5.1). The walrus operator keeps each `find` to one
        call. Agent frameworks apply exactly this when a model ignores the API's stop parameter, or when the stop has to be
        checked after streaming."""),
    fix("snake_case to camelCase", "easy", tag="Data work",
        prompt="""`to_camel(name)` should convert JSON keys like `user_id` to `userId` for a JavaScript client. It returns
        `UserId`. Fix it so the first word stays lower case and each later word starts with a capital, with the rest of each
        word unchanged.""",
        code="""
        def to_camel(name):
            return name.title().replace("_", "")
        """,
        tests="""
        assert to_camel("user_id") == "userId"
        assert to_camel("http_url_v2") == "httpUrlV2"
        assert to_camel("id") == "id"
        assert to_camel("max_tokens_GPT") == "maxTokensGPT"
        """,
        hints=["Split on `_`, keep the first part as it is, and capitalise only the first letter of the others: `p[:1].upper() + p[1:]`."],
        solution="""
        def to_camel(name):
            first, *rest = name.split("_")
            return first + "".join(p[:1].upper() + p[1:] for p in rest)
        """,
        why="""`title()` capitalises every word **and lower-cases the rest of it**, so it also turns `GPT` into `Gpt` (5.2). Splitting
        and changing only the first letter of the later parts leaves everything else as written. `p[:1]` instead of `p[0]`
        handles empty parts from a double underscore without an `IndexError`, because slicing never fails (5.1). `str.capitalize`
        has the same problem as `title`: it lower-cases the rest."""),
    predict("Methods versus regex on the same text", "medium",
        code="""
        import re

        s = "id=7;  name = Ana ;tags=a,b"
        print(s.split(";"), re.split(r"\\s*;\\s*", s))
        print([kv.partition("=")[::2] for kv in re.split(r"\\s*;\\s*", s)])
        print(re.findall(r"(\\w+)\\s*=\\s*([^;]+?)\\s*(?:;|$)", s))
        print(f"{'Ana'!r:>8}|{7:03}|{'x':-^5}")
        """,
        hints=["`[::2]` on a 3-tuple takes items 0 and 2. The lazy `+?` stops before the optional spaces and the `;` or end."],
        why="""`str.split(";")` keeps the spaces around each part, while `re.split` with `\\s*;\\s*` removes them as part of the
        separator. `partition("=")[::2]` keeps the key and value and drops the `=`, but the spaces around `=` in `name = Ana`
        stay. The regex handles those too: `\\s*=\\s*` absorbs them, and the lazy `[^;]+?` followed by `\\s*(?:;|$)` stops before
        the trailing spaces (5.5). In the f-string, `!r` applies `repr` before the format spec, so the quotes are part of the
        8-character field (5.3)."""),
    write("Parse a tool call from model text", "medium", tag="GenAI",
        prompt="""A ReAct-style agent prompt asks the model to write tool calls as a line like
        `CALL search(query="refund policy", k=3)`. Write `parse_call(text)` returning `(name, args)` from the first such line,
        where args are a dict: quoted values become strings (without the quotes), bare integers become `int`. Return `None` if
        there is no `CALL` line.""",
        code="""
        import re

        def parse_call(text):
            pass
        """,
        tests="""
        t = "Thought: I need the policy.\\nCALL search(query=\\"refund policy, EU\\", k=3)\\nObservation:"
        assert parse_call(t) == ("search", {"query": "refund policy, EU", "k": 3})
        assert parse_call("CALL now()") == ("now", {})
        assert parse_call("no tools here") is None
        assert parse_call("x\\nCALL get_doc(id=12, lang=\\"en\\")") == ("get_doc", {"id": 12, "lang": "en"})
        """,
        hints=["First find the call line: `re.search(r\"^CALL (\\w+)\\((.*)\\)\\s*$\", text, re.M)`.",
               "Then the arguments: `re.findall(r'(\\w+)=(?:\"([^\"]*)\"|(-?\\d+))', args)` gives `(key, string, number)` tuples, with one of the last two empty."],
        solution="""
        import re

        CALL = re.compile(r"^CALL (\\w+)\\((.*)\\)\\s*$", re.M)
        ARG = re.compile(r'(\\w+)=(?:"([^"]*)"|(-?\\d+))')

        def parse_call(text):
            m = CALL.search(text)
            if not m:
                return None
            name, arg_text = m.groups()
            args = {}
            for key, string, number in ARG.findall(arg_text):
                args[key] = int(number) if number else string
            return name, args
        """,
        why="""Splitting the arguments on `,` would break on `"refund policy, EU"`, so the argument pattern matches either a quoted
        string or an integer; `[^"]*` cannot run past the closing quote. With alternative groups, `findall` returns a tuple with an
        empty string for the group that did not take part, which tells you which kind of value you got (5.5). `re.M` makes `^` and
        `$` work per line, so the call can sit in the middle of the reply. Modern APIs return tool calls as JSON (tool calling),
        which removes this parsing; you still meet text formats like this in older agents and local models."""),
    fix("Labels that do not group", "medium", tag="ML",
        prompt="""Labels exported from three annotation tools do not group correctly: `"\\ufeffSpam"`, `"ｓｐａｍ "`,
        `"SPAM"` and `"spam"` should all be one class, and `"Straße"` should equal `"STRASSE"`. Fix `normalize_label`.""",
        code="""
        def normalize_label(label):
            return label.strip().lower()
        """,
        tests="""
        labels = ["\\ufeffSpam", "ｓｐａｍ ", "SPAM", "spam", "Straße", "STRASSE", "ham\\u200b"]
        assert [normalize_label(x) for x in labels] == ["spam"] * 4 + ["strasse"] * 2 + ["ham"]
        assert normalize_label("  Café\\u0301 ".replace("é", "e")) == "café"
        """,
        hints=["`strip()` does not remove the byte order mark `\\ufeff` or the zero-width space `\\u200b`: they are not whitespace.",
               "NFKC turns full-width letters into normal ones and combines `e` + accent into one `é`; `casefold()` maps `ß` to `ss`."],
        solution="""
        import unicodedata

        INVISIBLE = dict.fromkeys(map(ord, "\\ufeff\\u200b\\u200c\\u200d"))

        def normalize_label(label):
            label = unicodedata.normalize("NFKC", label).translate(INVISIBLE)
            return label.strip().casefold()
        """,
        why="""Each label fails for a different reason. The BOM and the zero-width space are format characters, not whitespace, so
        `strip` leaves them; `translate` with a dict mapping their code points to `None` deletes them (5.2). The full-width
        letters are different code points from `spam`, and NFKC maps these "compatibility" characters to the plain ones, while
        also composing `e` + combining accent into a single `é` (5.4). `lower()` keeps `ß`, while `casefold()` maps it to `ss`,
        which is the right tool for caseless comparison. Unnormalised labels silently split one class into several, which
        lowers per-class counts and can wreck a classifier's metrics."""),
    choose("Many prefixes: a tuple or a loop", "medium",
        prompt="Both keep the log lines that start with any of 12 noisy prefixes, over 200,000 lines. Which is faster?",
        setup="""prefixes = [f"DEBUG [{name}]" for name in ["cache", "http", "pool", "db", "auth", "queue",
                                                         "cron", "mail", "s3", "dns", "gc", "tls"]]
lines = [f"DEBUG [tls] handshake {i}" if i % 2 else f"INFO [api] request {i}" for i in range(200_000)]""",
        options={
            "a": "kept = [line for line in lines if any(line.startswith(p) for p in prefixes)]",
            "b": "prefix_tuple = tuple(prefixes)\nkept = [line for line in lines if line.startswith(prefix_tuple)]",
        },
        answer="b",
        hints=["`str.startswith` accepts a tuple of prefixes and checks them all in C."],
        why="""`startswith(tuple)` runs the whole check in one C call. The `any(...)` version creates a generator for every line and
        makes up to 12 Python-level calls per line, and the lines that match nothing (half of them here) pay for all 12. The
        tuple has to be built once, outside the loop. `endswith` accepts a tuple too, which is handy for file extensions (5.2)."""),
    trace("One string through the pipeline", "medium",
        prompt="Fill in `s` after each marked line.",
        code="""
        s = "  Hello,   World!  "
        s = s.strip()  # row: "strip"
        s = " ".join(s.split())  # row: "collapse spaces"
        s = s.casefold().replace(",", "")  # row: "casefold, drop comma"
        s = f"{s:*^15}"  # row: "centre in 15"
        s = s.encode()[:4]  # row: "first 4 bytes"
        """,
        trace_vars=["s"],
        hints=["`\" \".join(s.split())` is the classic way to collapse whitespace. `*^15` centres with `*` as the fill."],
        why="""`strip` removes the outer spaces, then splitting on whitespace and joining with one space collapses the inner run. The
        f-string centres the 12-character string in 15 characters; the odd padding goes to the right. Encoding gives `bytes`, and
        slicing bytes gives bytes, shown with a `b` prefix (5.4)."""),
    refactor("A prompt builder from string pieces", "medium", tag="GenAI",
        prompt="Rewrite with `join`, `enumerate` and f-strings. Same output; keep the tests green.",
        code="""
        def build_prompt(question, chunks):
            prompt = "Answer using only the sources.\\n\\n"
            i = 1
            for chunk in chunks:
                prompt = prompt + "[" + str(i) + "] " + chunk["source"] + ": " + chunk["text"].strip() + "\\n"
                i = i + 1
            prompt = prompt + "\\nQuestion: %s\\nAnswer:" % question
            return prompt
        """,
        tests="""
        chunks = [{"source": "faq.md", "text": " Refunds take 5 days. "}, {"source": "terms.md", "text": "No refunds after 30 days.\\n"}]
        out = build_prompt("How long do refunds take?", chunks)
        assert out == ("Answer using only the sources.\\n\\n[1] faq.md: Refunds take 5 days.\\n"
                       "[2] terms.md: No refunds after 30 days.\\n\\nQuestion: How long do refunds take?\\nAnswer:")
        assert build_prompt("q", []) == "Answer using only the sources.\\n\\n\\nQuestion: q\\nAnswer:"
        assert build_prompt("50% off?", []).endswith("Question: 50% off?\\nAnswer:")
        """,
        hints=["Build the source lines with a generator inside `\"\".join(...)`, each ending in `\\n`, so an empty list gives an empty string."],
        solution="""
        def build_prompt(question, chunks):
            sources = "".join(
                f"[{i}] {c['source']}: {c['text'].strip()}\\n" for i, c in enumerate(chunks, start=1)
            )
            return f"Answer using only the sources.\\n\\n{sources}\\nQuestion: {question}\\nAnswer:"
        """,
        why="""`enumerate(..., start=1)` replaces the manual counter, the f-string replaces both the `+` chains and `str(i)`, and `join`
        builds the block in one pass instead of copying the growing prompt on every iteration (5.1). Each source line keeps its own
        trailing newline, which is why an empty list still gives exactly the same text as the original. The old `%` formatting
        line had a latent trap: had the template itself contained a literal `%` (like "50% off"), `%` formatting would raise; the
        f-string has no such issue (5.3)."""),
    write("Highlight search terms", "hard", tag="RAG",
        prompt="""Search results show the matched terms highlighted. Write `highlight(text, terms)` that wraps every whole-word,
        case-insensitive occurrence of any term in `[[` and `]]`, keeping the original casing. Terms may contain regex
        characters (`C++`) and may overlap (`refund` and `refund policy`): prefer the **longest** term at each position.""",
        code="""
        import re

        def highlight(text, terms):
            pass
        """,
        tests="""
        t = "Our Refund policy: refunds differ, but a refund policy exists. C++ and c++ too."
        assert highlight(t, ["refund", "refund policy", "c++"]) == (
            "Our [[Refund policy]]: refunds differ, but a [[refund policy]] exists. [[C++]] and [[c++]] too.")
        assert highlight("abc", []) == "abc"
        assert highlight("a.b axb", ["a.b"]) == "[[a.b]] axb"
        """,
        hints=["Escape each term with `re.escape`, sort them longest first, and join with `|` (the engine takes the first alternative that matches, 5.5).",
               "Use `(?<!\\w)(?:...)(?!\\w)` for whole words, since `\\b` fails next to `+`. Replace with `r\"[[\\g<0>]]\"` to keep the casing."],
        solution="""
        import re

        def highlight(text, terms):
            if not terms:
                return text
            alternatives = "|".join(re.escape(t) for t in sorted(terms, key=len, reverse=True))
            pattern = re.compile(rf"(?<!\\w)(?:{alternatives})(?!\\w)", re.IGNORECASE)
            return pattern.sub(r"[[\\g<0>]]", text)
        """,
        why="""Three regex facts from 5.5 meet here. Alternation takes the first alternative that matches, so sorting longest first
        makes `refund policy` win over `refund`. `re.escape` stops `C++` (one or more C's, twice) and `a.b` (`.` is any
        character) from acting as patterns, which the third test checks. And `\\b` would fail after `++`, because there is no word
        boundary between `+` and a space, so lookarounds express "not inside a word" instead. `\\g<0>` puts back the matched text
        exactly as it appeared, so the casing is kept. With no terms, the pattern would be empty and match everywhere, so that case
        returns early. `refunds` is not highlighted because `(?!\\w)` rejects the `s`."""),
    fix("Read the code: a streaming reader that breaks on accents", "hard", tag="GenAI",
        prompt="""LLM APIs stream replies as **server-sent events**: lines like `data: {"delta": "Hi"}`, ending with
        `data: [DONE]`, delivered as arbitrary chunks of bytes. This reader works in testing but crashes in production with a
        `UnicodeDecodeError`, sometimes loses events, and sometimes never stops at `[DONE]`. Read it, find the bugs and fix
        them.""",
        code="""
        import json


        def read_stream(chunks):
            \"\"\"Return the concatenated deltas from a stream of byte chunks.\"\"\"
            parts = []
            for chunk in chunks:
                text = chunk.decode("utf-8")
                for line in text.split("\\n"):
                    if not line.startswith("data: "):
                        continue
                    payload = line[len("data: "):]
                    if payload == "[DONE]":
                        return "".join(parts)
                    parts.append(json.loads(payload)["delta"])
            return "".join(parts)
        """,
        tests="""
        body = 'data: {"delta": "Caf\\u00e9 "}\\r\\ndata: {"delta": "na\\u00efve"}\\r\\n\\r\\ndata: [DONE]\\r\\ndata: {"delta": "x"}\\r\\n'
        raw = body.encode("utf-8")
        cut = raw.index("é".encode()) + 1
        chunks = [raw[:cut], raw[cut:40], raw[40:]]
        assert read_stream(chunks) == "Café naïve"
        assert read_stream([raw]) == "Café naïve"
        assert read_stream([raw[i:i + 1] for i in range(len(raw))]) == "Café naïve"
        assert read_stream([b'data: {"delta": "ok"}\\n']) == "ok"
        """,
        hints=["A chunk can end in the middle of the two bytes of `é`, so decoding chunk by chunk fails. It can also end in the middle of a line.",
               "Keep a `bytes` buffer: append each chunk, and while it contains `b\"\\n\"`, split off one complete line and decode only that. In UTF-8, the byte `\\n` never appears inside a multi-byte character (5.4).",
               "Servers may end lines with `\\r\\n`, so remove a trailing `\\r` before comparing with `[DONE]`."],
        solution="""
        import json


        def read_stream(chunks):
            \"\"\"Return the concatenated deltas from a stream of byte chunks.\"\"\"
            parts = []
            buffer = b""
            for chunk in chunks:
                buffer += chunk
                while b"\\n" in buffer:
                    raw_line, buffer = buffer.split(b"\\n", 1)
                    line = raw_line.decode("utf-8").rstrip("\\r")
                    if not line.startswith("data: "):
                        continue
                    payload = line[len("data: "):]
                    if payload == "[DONE]":
                        return "".join(parts)
                    parts.append(json.loads(payload)["delta"])
            return "".join(parts)
        """,
        why="""Three bugs, all invisible with small ASCII test streams. **Decoding per chunk:** the network splits bytes wherever it
        likes, so a chunk can end after the first byte of `é` (`c3`), and decoding it alone raises. **Lines across chunks:** the end
        of one chunk and the start of the next were treated as two separate lines, so half-lines were dropped (or failed in
        `json.loads`). Buffering bytes and decoding only complete lines fixes both, and it is safe because in UTF-8 every byte of a
        multi-byte character is 128 or above, so the byte `0x0a` (`\\n`) can only ever be a real newline (5.4). **`\\r\\n` line
        endings:** `"[DONE]\\r"` is not `"[DONE]"`, so the reader kept going and appended the `x` sent after it (`json.loads`
        tolerated the `\\r` as whitespace, which hid the problem). Real SDKs do exactly this buffering; `codecs.getincrementaldecoder`
        is the general tool when the text has no convenient delimiter."""),
    write("Extract code blocks from a reply", "hard", tag="GenAI",
        prompt="""Write `code_blocks(markdown)` returning a list of `(language, code)` for every fenced code block in a model's
        reply. A fence is three backticks **at the start of a line**, optionally followed by a language name, then the code,
        then a closing line of three backticks. `language` is `None` when missing; `code` excludes the fence lines and the final
        newline before the closing fence.""",
        code="""
        import re

        def code_blocks(markdown):
            pass
        """,
        tests="""
        f = "`" * 3
        reply = f"Try this:\\n{f}python\\nx = 1\\nprint(x)\\n{f}\\nand run:\\n{f}\\npip install x\\n{f}\\nInline {f} is not a fence."
        assert code_blocks(reply) == [("python", "x = 1\\nprint(x)"), (None, "pip install x")]
        assert code_blocks("no code") == []
        assert code_blocks(f"{f}sql\\nSELECT 1;\\n\\nSELECT 2;\\n{f}") == [("sql", "SELECT 1;\\n\\nSELECT 2;")]
        """,
        hints=["Use `re.M` so `^` and `$` match at line starts and ends, and `re.S` so the code part can span lines; keep the code part lazy.",
               "The opening line is three backticks, then an optional group of word characters for the language, then a newline."],
        solution="""
        import re

        FENCE = re.compile(r"^`{3}(\\w+)?[ \\t]*\\n(.*?)\\n`{3}[ \\t]*$", re.M | re.S)

        def code_blocks(markdown):
            return [(lang or None, code) for lang, code in FENCE.findall(markdown)]
        """,
        why="""`re.M` anchors the fences at line starts, which is what rejects the inline backticks at the end of the reply. `re.S` lets
        the lazy `(.*?)` cross newlines, and laziness makes it stop at the **first** closing fence, so two blocks stay two matches
        (5.5). An optional group that did not take part comes back from `findall` as an empty string, so `lang or None` converts
        it. The `[ \\t]*` parts allow trailing spaces after a fence, which models produce. This regex does not handle nested fences
        or fences of four backticks; a Markdown parser such as `markdown-it-py` does, and is worth it when the replies come from
        users."""),
    explain("What is the difference between `str` and `bytes`, and where should encoding and decoding happen in a program?", "medium", tag="Interview",
        why="""A `str` is a sequence of Unicode code points: text, independent of how it is stored. `bytes` is a sequence of numbers
        from 0 to 255: what files, sockets and APIs actually carry. Encoding (`str.encode`) turns text into bytes using an
        encoding such as UTF-8; decoding (`bytes.decode`) does the reverse, and needs to know the encoding that was used. The rule
        is the "Unicode sandwich": decode once, at the edges where data comes in, work with `str` everywhere inside, and encode once
        where data goes out, always naming the encoding (`open(..., encoding="utf-8")`), because the platform default differs
        between machines. Mixing them causes the classic bugs: `TypeError` when combining `str` and `bytes`, mojibake from decoding
        with the wrong encoding, and `UnicodeDecodeError` when a multi-byte character is split across chunks."""),
    explain("You need to clean and normalise the text of 10 million rows before training a model. How do you make it fast?", "hard", tag="Interview",
        why="""First, measure on a sample, since text cleaning is usually dominated by a few slow steps. Then remove per-character Python
        loops: use C-level operations such as `str.translate` for character deletion and mapping, `split`/`join` for whitespace,
        and compiled regexes for patterns, combining several substitutions into one pass where possible. Avoid building strings
        with `+=` in loops. Use vectorised column methods (`pandas` `.str` accessor, or Polars, whose string functions run in
        Rust and in parallel) instead of `apply` with a Python function per row. Process the data in chunks or as a stream so
        memory stays bounded, and parallelise across processes (for example `multiprocessing` or a Polars or Spark job) because a
        single Python process uses one core. Cache the result to Parquet so the cleaning runs once, and keep the cleaning function
        identical for training and serving, so the model sees the same text in production."""),
    predict("Everything at once", "hard",
        code="""
        import re, unicodedata

        raw = "Ｒéf: 12,5 €\\u00a0— OK".encode("utf-8")
        text = unicodedata.normalize("NFKC", raw.decode("utf-8"))
        print(text, len(raw), len(text))
        print(re.findall(r"\\d+(?:,\\d+)?", text), text.split("\\u00a0"))
        amount = float(re.search(r"\\d+,\\d+", text).group().replace(",", "."))
        print(f"{amount:08.3f}", f"{text[:3]!r}", text.isascii())
        """,
        hints=["NFKC turns the full-width `Ｒ` into `R` and the no-break space into a normal space.",
               "`08.3f` pads with zeros to a total width of 8, including the point."],
        why="""The full-width `Ｒ` takes 3 bytes and `é`, `€` and the no-break space take 2, 3 and 2, which is why the bytes outnumber the
        characters (5.4). NFKC maps both the full-width letter and the no-break space to their plain forms, so `split("\\u00a0")`
        then finds nothing to split on: normalising early changes what later steps see. The regex reads the decimal comma as part
        of the number. Converting it needs `replace(",", ".")` before `float` (5.2), and `08.3f` gives `0012.500` (5.3). `text`
        is still not ASCII, because of `é`, `€` and the dash."""),
)

section("project", "Mini project: prepare documents for a RAG index",
    p("""Before documents go into a vector index, they are cleaned and cut into chunks. Raw files arrive as bytes from different
    tools: some have a byte order mark, some contain invalid bytes, full-width characters, invisible characters, personal data
    and messy whitespace. Build the preparation step. Every rule in the spec maps to a lesson in this module, and the tests check
    each one."""),
    write("Clean and chunk a document", "hard", key="rag-ingest", tag="Project",
        prompt="""Implement `prepare(doc_id, raw, max_chars)`, where `raw` is `bytes`. Return an `Ingested` named tuple with
        `chunks` (a list of `Chunk(id, text)`), `replaced` (how many undecodable bytes were replaced) and `redacted` (how many
        emails were redacted). The steps, in order:

        - **Decode** as UTF-8, dropping a leading byte order mark, replacing invalid bytes with `\\ufffd` (count them).
        - **Normalise** with NFKC, then delete control and format characters (Unicode categories `Cc` and `Cf`), but keep whitespace such as `\\n` and `\\t`.
        - **Redact** email addresses as `[EMAIL]` (count them).
        - **Paragraphs:** split on blank lines (a line break, optional spaces or tabs, another line break, and so on). Inside each
          paragraph, collapse all whitespace runs to one space and strip. Drop empty paragraphs.
        - **Sentences:** split each paragraph after `.`, `!` or `?` followed by whitespace.
        - **Chunks:** pack consecutive sentences of one paragraph into chunks of at most `max_chars` characters, joined by one
          space; never cross a paragraph. A single sentence longer than `max_chars` is cut into pieces of `max_chars`.
        - **Ids:** `f"{doc_id}-{n:03d}"`, numbered from 1 across the whole document.""",
        code="""
        import re
        import unicodedata
        from typing import NamedTuple


        class Chunk(NamedTuple):
            id: str
            text: str


        class Ingested(NamedTuple):
            chunks: list
            replaced: int
            redacted: int


        def prepare(doc_id, raw, max_chars):
            pass
        """,
        tests="""
        raw = ("\\ufeffRefund Policy\\n\\n"
               "Refunds take 5 days.   Contact ana@example.com for help!\\tAfter 30 days, no refunds.\\n"
               " \\n\\n"
               "Ｆｕｌｌ-width text\\u200b is normalised. Ok?\\n").encode("utf-8") + b"Bad byte: \\xff end."
        r = prepare("faq", raw, max_chars=45)
        assert r.replaced == 1 and r.redacted == 1
        assert r.chunks == [
            Chunk("faq-001", "Refund Policy"),
            Chunk("faq-002", "Refunds take 5 days."),
            Chunk("faq-003", "Contact [EMAIL] for help!"),
            Chunk("faq-004", "After 30 days, no refunds."),
            Chunk("faq-005", "Full-width text is normalised. Ok?"),
            Chunk("faq-006", "Bad byte: \\ufffd end."),
        ]
        assert all(len(c.text) <= 45 for c in r.chunks)
        long = prepare("x", b"A" * 25 + b".", max_chars=10)
        assert [c.text for c in long.chunks] == ["AAAAAAAAAA", "AAAAAAAAAA", "AAAAA."]
        assert prepare("e", b"", 50) == Ingested([], 0, 0)
        """,
        hints=["Decode with `raw.decode(\"utf-8-sig\", errors=\"replace\")` and count `\\ufffd` in the result (5.4). Use `unicodedata.category(ch)` to filter `Cc` and `Cf`.",
               "`re.subn` returns the new text and the number of replacements, which gives the email count (5.5).",
               "Paragraphs: `re.split(r\"\\n[ \\t]*\\n\", text)`. Sentences: `re.split(r\"(?<=[.!?])\\s+\", paragraph)`.",
               "Pack greedily: keep a current chunk; if adding `\" \" + sentence` would exceed `max_chars`, close the chunk and start a new one. Cut long sentences with slicing first."],
        solution="""
        import re
        import unicodedata
        from typing import NamedTuple


        class Chunk(NamedTuple):
            id: str
            text: str


        class Ingested(NamedTuple):
            chunks: list
            replaced: int
            redacted: int


        EMAIL = re.compile(r"[\\w.+-]+@[\\w-]+(?:\\.[\\w-]+)+")
        PARAGRAPH_BREAK = re.compile(r"\\n[ \\t]*\\n")
        SENTENCE_END = re.compile(r"(?<=[.!?])\\s+")


        def _clean(raw):
            text = raw.decode("utf-8-sig", errors="replace")
            replaced = text.count("\\ufffd")
            text = unicodedata.normalize("NFKC", text)
            text = "".join(ch for ch in text if ch.isspace() or unicodedata.category(ch) not in ("Cc", "Cf"))
            text, redacted = EMAIL.subn("[EMAIL]", text)
            return text, replaced, redacted


        def _pack(sentences, max_chars):
            pieces = [s[i:i + max_chars] for s in sentences for i in range(0, len(s), max_chars)]
            chunks, current = [], ""
            for piece in pieces:
                if current and len(current) + 1 + len(piece) <= max_chars:
                    current += " " + piece
                else:
                    if current:
                        chunks.append(current)
                    current = piece
            if current:
                chunks.append(current)
            return chunks


        def prepare(doc_id, raw, max_chars):
            text, replaced, redacted = _clean(raw)
            texts = []
            for paragraph in PARAGRAPH_BREAK.split(text):
                paragraph = " ".join(paragraph.split())
                if paragraph:
                    texts.extend(_pack(SENTENCE_END.split(paragraph), max_chars))
            chunks = [Chunk(f"{doc_id}-{n:03d}", t) for n, t in enumerate(texts, start=1)]
            return Ingested(chunks, replaced, redacted)
        """,
        why="""Every lesson of the module has a job here:

        - **Bytes and Unicode (5.4):** `utf-8-sig` drops the BOM, `errors="replace"` keeps going past the bad byte and leaves a
          visible `\\ufffd` you can count, and NFKC turns the full-width letters into plain ones. The category filter deletes the
          zero-width space (`Cf`) but must keep whitespace: `\\n` and `\\t` are also in category `Cc`, and deleting the tab would
          glue `help!` to `After` and lose a sentence boundary. Order matters too: counting `\\ufffd` right after decoding
          counts only the replaced bytes.
        - **Regex (5.5):** `subn` counts redactions in the same pass, the paragraph pattern accepts lines with only spaces or tabs as
          blank, and the lookbehind `(?<=[.!?])` splits after the punctuation without removing it.
        - **Methods (5.2):** `" ".join(paragraph.split())` collapses every whitespace run, including the single line breaks inside
          a paragraph.
        - **Strings and slicing (5.1):** long sentences are cut with slices, which never fail at the end of a string, and chunks
          are built with `+=` on short strings, which is fine at this size.
        - **Formatting (5.3):** `{n:03d}` gives ids that sort correctly as text, which matters when chunks are stored in a
          database or a file system.

        Note that `Bad byte:` belongs to the same paragraph as `Ok?`, because a single line break is not a paragraph break; it
        lands in its own chunk only because it does not fit in the 45 characters. Chunking by sentences and paragraphs keeps each chunk readable for the model, and the `max_chars` limit
        stands in for the token limit of the embedding model; production pipelines (LangChain's text splitters, LlamaIndex's node
        parsers) follow the same idea with token counts and overlap between chunks."""),
)

recap(
    "Bytes at the edges, text inside: decode once with a named encoding, normalise (NFKC, casefold) before comparing.",
    "Fixed text: string methods (`split`, `partition`, `startswith` with a tuple, `translate`). Patterns: regex, escaped and anchored.",
    "Streams and files split data anywhere: buffer bytes and decode only complete units, such as lines.",
    "Keep values as numbers and dates while computing; format with a spec only for display.",
    "Make text pipelines deterministic and testable: each step a small function, each rule checked by a test.",
)
