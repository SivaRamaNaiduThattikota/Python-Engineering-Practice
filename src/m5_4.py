from lesson import *

lesson(
    id="m5-4", num="5.4", title="Unicode, bytes and encodings",
    intro="Text inside Python is Unicode; text in files, networks and databases is bytes. How UTF-8 turns code points into "
          "bytes, `encode` and `decode` with their error modes, mojibake and how to recognise it, reading files safely on "
          "Windows, the BOM, and normalisation for matching text.",
    desc="Code points, UTF-8, `encode` / `decode`, and reading text safely.",
    keys="unicode code point bytes bytearray encode decode utf-8 utf-16 latin-1 cp1252 ascii unicodedecodeerror errors replace ignore surrogateescape mojibake bom utf-8-sig normalize nfc nfd nfkc nfkd combining open encoding",
)

term("bytes", "An immutable sequence of integers from 0 to 255: raw data as stored in files or sent over a network. Written `b\"...\"`.")
term("Encoding", "A rule for turning code points into bytes and back, such as UTF-8, UTF-16 or cp1252.")
term("UTF-8", "The standard text encoding: 1 byte for ASCII, 2 to 4 bytes for other code points, and ASCII-compatible.")
term("Mojibake", "Garbled text such as \"cafÃ©\", produced by decoding bytes with the wrong encoding.")
term("BOM", "Byte order mark: optional bytes at the start of a file (EF BB BF in UTF-8) that some Windows tools add.")
term("Normalization", "Converting text to one canonical form (NFC, NFD, NFKC, NFKD) so visually identical strings compare equal.")

UTF8_FIG = """
<svg viewBox="0 0 640 140" role="img" aria-label="encode turns the str 'café' into the bytes 63 61 66 c3 a9; decode turns them back.">
  <defs><marker id="u1" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M0 0 L10 5 L0 10 z" style="fill:var(--label2)"/></marker></defs>
  <rect x="10" y="40" width="170" height="54" rx="12" class="box a"/>
  <text x="95" y="62" class="w mid">str: "café"</text><text x="95" y="82" class="w mid">4 code points</text>
  <rect x="440" y="40" width="190" height="54" rx="12" class="box b"/>
  <text x="535" y="62" class="w mid">bytes: 63 61 66 c3 a9</text><text x="535" y="82" class="w mid">5 bytes (é takes 2)</text>
  <path d="M184 56 L434 56" style="stroke:var(--label2);stroke-width:2;fill:none" marker-end="url(#u1)"/>
  <text x="310" y="48" class="mid">.encode("utf-8")</text>
  <path d="M434 80 L184 80" style="stroke:var(--label2);stroke-width:2;fill:none" marker-end="url(#u1)"/>
  <text x="310" y="100" class="mid">.decode("utf-8")</text>
  <text x="310" y="128" class="mid">inside Python: str. At every boundary (file, network, database): bytes.</text>
</svg>"""

section("model", "Text inside, bytes outside",
    p("""Inside your program, text is `str`: a sequence of Unicode **code points** (5.1). Outside your program, in files,
    network messages, HTTP bodies and database drivers, everything is **bytes**: numbers from 0 to 255. An **encoding** is the
    rule that converts between the two. `s.encode(encoding)` turns a `str` into `bytes`; `b.decode(encoding)` turns `bytes`
    back into a `str`. The golden rule follows: **decode as early as possible when data comes in, work with `str`, encode as late
    as possible when it goes out**, and always say which encoding."""),
    fig(UTF8_FIG, "Encoding and decoding happen at the edges of a program, never in the middle."),
    ex("""
    s = "café €5"
    b = s.encode("utf-8")
    print(type(b).__name__, b, len(s), len(b))
    print(list(b[3:5]), b[0], chr(b[0]))          # indexing bytes gives integers
    print(b.decode("utf-8") == s)
    try:
        "x" + b
    except TypeError as e:
        print("TypeError:", e)
    """, "str_vs_bytes.py"),
    p("""`bytes` look like strings when printed (`b'caf\\xc3\\xa9'`), but they are a different type: indexing gives an
    **integer**, you cannot mix them with `str` in `+`, `in` or `==` (a `str` never equals a `bytes`), and their methods
    (`split`, `startswith`) take bytes arguments. `bytearray` is the mutable version. Python 3 refuses to mix the two silently,
    which turns encoding confusion into an immediate `TypeError` instead of corrupted data."""),
    callout("sql", "SQL / Power BI", """In SQL Server, `NVARCHAR` stores Unicode and `VARCHAR` stores bytes in a code page (or
    UTF-8 with a `_UTF8` collation); `VARBINARY` is raw bytes. A `str` is like `NVARCHAR`, `bytes` like `VARBINARY`, and the
    encoding is the collation's code page. Importing a CSV into Power BI with the wrong "File origin" setting is the same
    mistake as decoding with the wrong encoding: you get `Ã©` where `é` should be."""),
)

section("utf8", "How UTF-8 works",
    p("""UTF-8 is the encoding to use unless something forces you otherwise: it is the default for the web, JSON, Python
    source files, Linux and macOS, and most databases. It stores each code point in **1 to 4 bytes**:"""),
    html("""<div class="tbl"><table>
      <tr><th>Code points</th><th>Bytes</th><th>Examples</th></tr>
      <tr><td>U+0000 to U+007F (ASCII)</td><td>1</td><td><code>A</code>, <code>7</code>, <code>{</code></td></tr>
      <tr><td>U+0080 to U+07FF</td><td>2</td><td><code>é</code>, <code>ß</code>, Greek, Cyrillic, Arabic, Hebrew</td></tr>
      <tr><td>U+0800 to U+FFFF</td><td>3</td><td><code>€</code>, most Chinese, Japanese and Korean characters</td></tr>
      <tr><td>U+10000 and above</td><td>4</td><td>emoji, rare scripts</td></tr>
    </table></div>"""),
    p("""Two properties make it so popular. **ASCII text is unchanged**: an ASCII file is already valid UTF-8, byte for byte.
    And it is **self-synchronising**: the first byte of a character says how many bytes follow, and continuation bytes always
    start with the bits `10`, so a decoder can tell where characters begin. That is also why cutting UTF-8 bytes at an
    arbitrary position can split a character in half, producing invalid data (problem 13)."""),
    ex("""
    for ch in ["A", "é", "€", "\\U0001F600"]:
        b = ch.encode("utf-8")
        print(ch, f"U+{ord(ch):04X}", len(b), " ".join(f"{x:08b}" for x in b))
    print(len("naïve résumé".encode("utf-8")), len("naïve résumé"))
    """, "utf8_bytes.py"),
    p("""Other encodings you will meet: **UTF-16** (2 or 4 bytes per code point, used inside Windows and Java, and by Excel's
    "Unicode text" export), **Latin-1** (ISO-8859-1, one byte per character, only the first 256 code points) and **cp1252**
    (Windows-1252, Latin-1 plus `€` and typographic quotes, the old Windows default for Western European text). The last two
    can decode **any** byte sequence without error, which makes them dangerous fallbacks: they never fail, they just produce
    the wrong characters."""),
)

section("errors", "Decoding errors and error modes",
    p("""Decoding bytes that are not valid in the chosen encoding raises `UnicodeDecodeError`, which reports the encoding, the
    offending byte and its position. Encoding a character the target encoding cannot represent raises `UnicodeEncodeError`.
    The `errors=` argument chooses what to do instead of raising:"""),
    ex("""
    data = "café".encode("utf-8") + b"\\xff"            # valid UTF-8 followed by one bad byte
    try:
        data.decode("utf-8")
    except UnicodeDecodeError as e:
        print("UnicodeDecodeError:", e)
    print(data.decode("utf-8", errors="replace"))        # U+FFFD replacement character
    print(data.decode("utf-8", errors="ignore"))         # silently drop the bad byte
    print(repr(data.decode("utf-8", errors="backslashreplace")))
    try:
        "€5".encode("latin-1")
    except UnicodeEncodeError as e:
        print("UnicodeEncodeError:", e)
    print("€5".encode("ascii", errors="xmlcharrefreplace"))
    """, "error_modes.py"),
    p("""Choose deliberately. `strict` (the default) is right for data you produce or that must be correct: failing loudly is
    better than corrupting it. `replace` is good for display and logs: the `�` shows where something was wrong. `ignore` loses
    data without a trace, so avoid it except for throwaway analysis. `backslashreplace` keeps the bad bytes visible and
    recoverable, which suits logs of untrusted input. Whatever you choose, **count** how many replacements happened in a data
    pipeline (problem 9), because "a few bad characters" can mean the whole file was decoded with the wrong encoding."""),
)

section("mojibake", "Mojibake: decoding with the wrong encoding",
    p("""The most common encoding bug is not an error at all. Bytes written as UTF-8 and read back as cp1252 (or Latin-1)
    decode without complaint, because those encodings accept any byte, and every non-ASCII character turns into two or three
    wrong ones: `é` becomes `Ã©`, `€` becomes `â‚¬`, a typographic apostrophe `’` becomes `â€™` (a plain `'` is ASCII and survives). This is called **mojibake**, and its
    tell-tale sign is `Ã` or `â€` appearing in text that should contain accents or typographic punctuation."""),
    ex("""
    original = "Café – it's 5€"
    garbled = original.encode("utf-8").decode("cp1252")
    print(garbled)
    repaired = garbled.encode("cp1252").decode("utf-8")
    print(repaired, repaired == original)
    """, "mojibake.py"),
    p("""When the damage is exactly one wrong decode, reversing it (encode with the wrong encoding, decode with the right
    one) restores the text, as above. When text was garbled twice, or saved after garbling with information lost, repair is
    guesswork; the `ftfy` library automates the common cases. The real fix is upstream: find the step that decoded with the
    wrong encoding, which is usually a file opened without `encoding=` (next section) or a database connection with the wrong
    character set."""),
)

section("files", "Reading and writing files safely",
    p("""`open(path)` in text mode decodes bytes into `str` for you, using an encoding. If you do not pass `encoding=`,
    Python uses the **locale's** encoding, which is UTF-8 on Linux and macOS but traditionally cp1252 on Windows (Python 3.15
    makes UTF-8 the default everywhere). Code that works on a Mac and garbles text on a Windows VDI almost always has this
    bug. So: **always pass `encoding="utf-8"`** (or the file's real encoding) to `open`, `pathlib.Path.read_text` and
    `write_text`, and to `pandas.read_csv` when the file is not UTF-8."""),
    ex("""
    import os, tempfile

    path = os.path.join(tempfile.mkdtemp(), "notes.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("Résumé – naïve café\\n")
    with open(path, "rb") as f:
        raw = f.read()
    print(raw[:12], len(raw))
    with open(path, encoding="utf-8") as f:
        print(f.read().strip())
    with open(path, encoding="cp1252") as f:
        print(f.read().strip())                    # wrong encoding: mojibake, no error
    """, "files.py"),
    p("""Two more Windows realities. Some tools (Excel's "CSV UTF-8", Notepad in older versions) write a **BOM**, the three
    bytes `EF BB BF`, at the start of a UTF-8 file. Decoded as plain `utf-8`, it becomes the invisible character `\\ufeff`
    glued to the first value, so the first column header is `"\\ufeffid"` and `row["id"]` fails. Reading with
    `encoding="utf-8-sig"` strips it (and works for files without a BOM too). And files exported as "Unicode" from Excel are
    usually **UTF-16**, which `utf-8` cannot decode at all."""),
    ex("""
    data = "\\ufeffid,name\\n1,Ana\\n".encode("utf-8")
    print(data[:5])
    print(repr(data.decode("utf-8").split(",")[0]), repr(data.decode("utf-8-sig").split(",")[0]))
    """, "bom.py"),
)

section("normalize", "Normalization: making equal text compare equal",
    p("""The same visible text can be written with different code points. `é` can be one precomposed code point (U+00E9) or
    `e` plus a combining accent (U+0301), and macOS file names and some keyboards produce the decomposed form. Compatibility
    characters add more variants: the ligature `ﬁ`, full-width `ＡＢＣ`, superscript `²`, the non-breaking space. Unicode
    defines four **normal forms** to make such text comparable:"""),
    p("""- **NFC**: compose where possible (`e` + accent becomes `é`). The standard form for storage and comparison.
    - **NFD**: decompose (`é` becomes `e` + accent). Useful for removing accents: decompose, then drop the combining marks.
    - **NFKC** / **NFKD**: also replace **compatibility** characters with their plain equivalents (`ﬁ` to `fi`, `²` to `2`,
      full-width to normal width). Good for search and matching, but it changes meaning in some cases, so do not use it for
      storage."""),
    ex("""
    import unicodedata as ud

    a, b = "café", "cafe\\u0301"
    print(a == b, ud.normalize("NFC", a) == ud.normalize("NFC", b), len(ud.normalize("NFD", a)))
    for s in ["ﬁle", "ＡＢＣ", "x²", "\\u00a0"]:
        print(repr(s), repr(ud.normalize("NFKC", s)))
    print(ud.name("é"), "|", ud.name("\\u0301"), "|", ud.category("\\u0301"))
    """, "normalize.py"),
)

section("warmup", "Warm-up",
    predict("str versus bytes", "easy",
        code="""
        s = "Refund €20"
        b = s.encode("utf-8")
        print(len(s), len(b), b[0], b[:6])
        print(s == b, s.encode() == b, b.decode() == s)
        print(b"abc".upper(), b"a,b".split(b","), "€".encode("utf-8").hex())
        """,
        hints=["`€` needs 3 bytes in UTF-8. Indexing bytes gives an integer; slicing gives bytes."],
        why="""The string has 10 code points, and the bytes 12, because `€` takes 3 bytes. `b[0]` is the integer 82 (`"R"`), and a
        slice stays `bytes`. A `str` never equals a `bytes`, even with the "same" content. `encode()` and `decode()` default to
        UTF-8. Bytes have string-like methods, but their arguments must be bytes too. `.hex()` shows the 3 bytes of `€`:
        `e282ac`."""),
    write("Byte length for a column limit", "easy", tag="Data work",
        prompt="""A database column stores at most `max_bytes` bytes of UTF-8. Write `fits(text, max_bytes)` that returns
        `True` if the UTF-8 encoding of `text` fits, and `utf8_len(text)` returning that byte length. `len(text)` is not the
        right measure.""",
        code="""
        def utf8_len(text):
            pass

        def fits(text, max_bytes):
            pass
        """,
        tests="""
        assert utf8_len("abc") == 3 and utf8_len("café") == 5 and utf8_len("€") == 3
        assert fits("café", 5) and not fits("café", 4)
        assert not fits("\\U0001F600" * 3, 10) and fits("\\U0001F600" * 3, 12)
        """,
        hints=["Encode and take the length of the bytes."],
        solution="""
        def utf8_len(text):
            return len(text.encode("utf-8"))

        def fits(text, max_bytes):
            return utf8_len(text) <= max_bytes
        """,
        why="""A column limit like MySQL's `VARCHAR(255)` with a byte-based limit, an index key limit, or an HTTP header size limit
        counts **bytes**, so a 255-character name with accents or emoji can be rejected or silently truncated even though `len`
        says it fits. Measuring the encoded length uses the same rule the database will. (Many databases count characters for
        `VARCHAR(n)` and bytes for other limits; check which one applies.)"""),
    fix("A CSV header with an invisible character", "easy", tag="Data work",
        prompt="""A CSV exported from Excel is read with `decode("utf-8")`, and `row["id"]` raises `KeyError` although the
        header clearly says `id`. Fix `parse_csv` so the first header is clean, whether or not the file has a BOM.""",
        code="""
        def parse_csv(data):
            text = data.decode("utf-8")
            lines = text.splitlines()
            header = lines[0].split(",")
            return [dict(zip(header, line.split(","))) for line in lines[1:]]
        """,
        tests="""
        with_bom = "\\ufeffid,name\\n1,Ana\\n2,Ben\\n".encode("utf-8")
        without = "id,name\\n3,Cy\\n".encode("utf-8")
        assert parse_csv(with_bom)[0]["id"] == "1" and parse_csv(with_bom)[1]["name"] == "Ben"
        assert parse_csv(without) == [{"id": "3", "name": "Cy"}]
        """,
        hints=["The file starts with the byte order mark `EF BB BF`. Which codec strips it automatically?"],
        solution="""
        def parse_csv(data):
            text = data.decode("utf-8-sig")
            lines = text.splitlines()
            header = lines[0].split(",")
            return [dict(zip(header, line.split(","))) for line in lines[1:]]
        """,
        why="""Excel's "CSV UTF-8" format starts the file with a BOM. Plain `utf-8` decodes it as the character `\\ufeff`, which is
        invisible when printed, so the first key is really `"\\ufeffid"`. `utf-8-sig` removes a leading BOM if present and
        otherwise behaves exactly like `utf-8`, so it is the safe choice for reading files that may come from Windows tools. With
        pandas, `read_csv(..., encoding="utf-8-sig")` does the same."""),
    predict("Error modes", "easy",
        code="""
        raw = b"Caf\\xc3\\xa9 \\xff ok"
        print(raw.decode("utf-8", errors="replace"))
        print(raw.decode("utf-8", errors="ignore"))
        print(raw.decode("latin-1"))
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError as e:
            print(e.start, e.end, e.reason)
        """,
        hints=["`\\xff` can never appear in valid UTF-8. Latin-1 maps every byte to some character, so it never fails."],
        why="""`replace` puts `�` where the bad byte was, `ignore` drops it, and both decode `\\xc3\\xa9` correctly as `é`. Latin-1
        never fails, but it decodes each byte separately, so the UTF-8 `é` becomes two wrong characters `Ã©`: no error, wrong text.
        The exception object tells you exactly where the problem is (`start`, `end`) and why, which is what you log when
        investigating bad input."""),
)

section("medium", "Medium",
    write("Repair simple mojibake", "medium", tag="Data work",
        prompt="""Text was written as UTF-8 and read back as cp1252 once. Write `fix_mojibake(text)` that reverses that
        (encode as cp1252, decode as UTF-8) when it works, and returns the text **unchanged** if the reversal fails or the text
        does not look garbled. Treat text as garbled only if it contains `Ã` or `â€`.""",
        code="""
        def fix_mojibake(text):
            pass
        """,
        tests="""
        assert fix_mojibake("CafÃ© â€“ itâ€™s 5â‚¬") == "Café – it’s 5€"
        assert fix_mojibake("Café") == "Café"
        assert fix_mojibake("plain text") == "plain text"
        assert fix_mojibake("Ã") == "Ã"
        """,
        hints=["Check for the tell-tale sequences first. Then try `text.encode(\"cp1252\").decode(\"utf-8\")` inside `try` / `except UnicodeError`."],
        solution="""
        def fix_mojibake(text):
            if "Ã" not in text and "â€" not in text:
                return text
            try:
                return text.encode("cp1252").decode("utf-8")
            except UnicodeError:
                return text
        """,
        why="""A single wrong decode is reversible: encoding with the same wrong codec gives back the original bytes, which then decode
        correctly. Two guards keep it safe: only touch text that shows the signature of mojibake (so a real `Café` is never
        "repaired" into garbage), and give up if the round trip fails (`Ã` alone is not valid UTF-8 after re-encoding).
        `UnicodeError` catches both decode and encode errors. For real cleanup, `ftfy.fix_text` handles many more cases, but the
        better fix is always to read the source with the right encoding."""),
    fix("Notes that turn into mojibake on Windows", "medium", tag="GenAI",
        prompt="""`save_notes` and `load_notes` store an agent's notes in a text file. On Linux they round-trip perfectly; on the
        Windows VDI, accented text comes back garbled. Fix both functions so the round trip works everywhere.""",
        code="""
        def save_notes(path, notes):
            with open(path, "w") as f:
                f.write("\\n".join(notes))

        def load_notes(path):
            with open(path) as f:
                return f.read().split("\\n")
        """,
        tests="""
        import builtins, codecs, os, tempfile
        p = os.path.join(tempfile.mkdtemp(), "notes.txt")
        notes = ["Résumé reviewed", "Customer: Zoë – urgent", "Refund 50€"]
        used = []
        real_open = builtins.open
        def watching_open(*args, **kwargs):
            enc = kwargs.get("encoding", args[3] if len(args) > 3 else None)
            used.append(codecs.lookup(enc).name if enc else "platform default")
            return real_open(*args, **kwargs)
        builtins.open = watching_open
        try:
            save_notes(p, notes)
            loaded = load_notes(p)
        finally:
            builtins.open = real_open
        assert loaded == notes
        assert used == ["utf-8", "utf-8"], f"encodings used: {used}"
        """,
        hints=["Without `encoding=`, `open` uses the platform's default encoding. Pass `encoding=\"utf-8\"` to both calls.",
               "This page's Python happens to default to UTF-8, so the test watches `open` and checks that the encoding is passed explicitly, which is what makes the code correct on every machine."],
        solution="""
        def save_notes(path, notes):
            with open(path, "w", encoding="utf-8") as f:
                f.write("\\n".join(notes))

        def load_notes(path):
            with open(path, encoding="utf-8") as f:
                return f.read().split("\\n")
        """,
        why="""Text mode always encodes and decodes; the only question is with what. Without `encoding=`, it is the locale default,
        UTF-8 on Linux and macOS but cp1252 on many Windows setups, so the same code writes different bytes on different machines
        and a file moved between them is misread. Passing `encoding="utf-8"` explicitly makes the file format part of the code.
        The second test checks the bytes on disk are UTF-8, which is what other tools reading the file expect. Ruff's rule PLW1514
        (`unspecified-encoding`) flags every `open` without an encoding."""),
    trace("Encoding step by step", "medium",
        prompt="Fill in `b.hex()` and `len(b)` after each marked line.",
        code="""
        b = "A".encode("utf-8")  # row: "'A' in UTF-8"
        b = "é".encode("utf-8")  # row: "'é' in UTF-8"
        b = "é".encode("latin-1")  # row: "'é' in Latin-1"
        b = "é".encode("utf-16-le")  # row: "'é' in UTF-16-LE"
        b = "€".encode("utf-8")  # row: "'€' in UTF-8"
        b = "€".encode("cp1252")  # row: "'€' in cp1252"
        """,
        trace_vars=["b.hex()", "len(b)"],
        hints=["`é` is U+00E9 and `€` is U+20AC. Latin-1 and cp1252 use one byte per character; UTF-16-LE uses two, low byte first."],
        why="""ASCII is one byte, `41`. UTF-8 needs two bytes for `é` (`c3a9`) and three for `€` (`e282ac`). Latin-1 stores `é` as the
        single byte `e9`, its code point. UTF-16 little-endian writes U+00E9 as `e900`. cp1252 puts `€` at byte `80`, a position
        Latin-1 uses for an invisible control character, which is why the two "Western" encodings disagree exactly on `€` and
        typographic quotes. The same character, four different byte sequences: bytes mean nothing without their encoding."""),
    choose("Is it ASCII? A per-character check or isascii", "medium",
        prompt="Both test whether each of 20,000 strings is pure ASCII. Which is faster?",
        setup="""texts = (["refund policy for the EU region"] * 9 + ["café opening hours"]) * 2000""",
        options={
            "a": "flags = [all(ord(ch) < 128 for ch in t) for t in texts]",
            "b": "flags = [t.isascii() for t in texts]",
        },
        answer="b",
        hints=["How much Python code runs per character in A?"],
        why="""A runs a Python generator, calling `ord` and comparing, for every character of every string. `str.isascii()` (Python
        3.7+) answers from information CPython already stores with each string (it tracks the widest character), so it is
        effectively instant regardless of length. Checking for ASCII is a common fast path: ASCII text needs no normalisation and
        encodes byte for byte."""),
    write("Count decoding problems in a batch", "medium", tag="Data work",
        prompt="""Write `decode_batch(rows)` for a list of `bytes` values from an old system. Decode each as UTF-8 with
        `errors="replace"`, and return `(texts, bad_rows)` where `bad_rows` is the list of row indices that contained at least one
        undecodable byte. A file with many bad rows was probably not UTF-8 at all.""",
        code="""
        def decode_batch(rows):
            pass
        """,
        tests="""
        rows = [b"ok", "café".encode("utf-8"), b"caf\\xe9", b"\\xff\\xfe", b""]
        texts, bad = decode_batch(rows)
        assert texts == ["ok", "café", "caf\\ufffd", "\\ufffd\\ufffd", ""]
        assert bad == [2, 3]
        """,
        hints=["After decoding with `replace`, a row had problems if `\"\\ufffd\"` is in the text and was not in the original bytes.",
               "The replacement character itself encodes to `b\"\\xef\\xbf\\xbd\"` in UTF-8. A row that already contained it legitimately is rare; checking for it is fine here."],
        solution="""
        def decode_batch(rows):
            texts, bad = [], []
            for i, raw in enumerate(rows):
                text = raw.decode("utf-8", errors="replace")
                if "\\ufffd" in text and b"\\xef\\xbf\\xbd" not in raw:
                    bad.append(i)
                texts.append(text)
            return texts, bad
        """,
        why="""`errors="replace"` keeps the pipeline running, but silently. Recording which rows were damaged turns a hidden data
        quality problem into a number you can alert on: one bad row is noise, half the rows means the source encoding is wrong
        (here `b"caf\\xe9"` is Latin-1 `café`). The check excludes rows whose bytes already contained a genuine replacement
        character. Logging the indices (not the content) also avoids leaking customer data into logs."""),
    fix("Accents break the search", "medium", tag="RAG",
        prompt="""A keyword search compares the query with document titles case-insensitively, but `"cafe"` does not find
        `"Café Menu"`, and a title typed on a Mac (decomposed accents) is not found by `"café"` either. Make `matches` ignore
        case **and** accents, so all four tests pass.""",
        code="""
        def matches(query, title):
            return query.casefold() in title.casefold()
        """,
        tests="""
        assert matches("cafe", "Café Menu")
        assert matches("café", "Cafe\\u0301 Menu")
        assert matches("CAFÉ", "café menu")
        assert not matches("tea", "Café Menu")
        """,
        hints=["Decompose with `unicodedata.normalize(\"NFD\", s)`, drop characters whose `unicodedata.combining(ch)` is non-zero, then casefold.",
               "Apply the same function to both the query and the title."],
        solution="""
        import unicodedata

        def fold(text):
            decomposed = unicodedata.normalize("NFD", text)
            return "".join(ch for ch in decomposed if not unicodedata.combining(ch)).casefold()

        def matches(query, title):
            return fold(query) in fold(title)
        """,
        why="""NFD splits `é` into `e` plus a combining accent, whatever form it was typed in, and dropping the combining marks leaves
        the base letters, so precomposed, decomposed and unaccented spellings all become `cafe`. Folding **both** sides with one
        function is the important design point (5.2). Accent folding is right for search and matching, but keep the original for
        display, and note it merges words that differ only by accent in some languages. Search engines do this with
        "ASCII folding" analysers."""),
    refactor("Explicit encodings, in one place", "medium",
        prompt="""This code passes `"utf-8"` and an error mode around in several places. Refactor so there is one pair of
        helpers, `to_bytes` and `to_text`, with the encoding and error handling defined once. Keep the tests green.""",
        code="""
        def send(payload):
            return payload.encode("utf-8", "strict")

        def receive(data):
            return data.decode("utf-8", "strict")

        def receive_log(data):
            return data.decode("utf-8", "backslashreplace")
        """,
        tests="""
        assert send("€1") == b"\\xe2\\x82\\xac1"
        assert receive(b"\\xe2\\x82\\xac1") == "€1"
        assert receive_log(b"ok\\xff") == "ok\\\\xff"
        """,
        hints=["Module constants `ENCODING = \"utf-8\"`, and helpers with an `errors` parameter defaulting to `\"strict\"`."],
        solution="""
        ENCODING = "utf-8"

        def to_bytes(text, errors="strict"):
            return text.encode(ENCODING, errors)

        def to_text(data, errors="strict"):
            return data.decode(ENCODING, errors)

        def send(payload):
            return to_bytes(payload)

        def receive(data):
            return to_text(data)

        def receive_log(data):
            return to_text(data, errors="backslashreplace")
        """,
        why="""Encoding decisions belong at the boundaries, and they should be made **once**: if the protocol ever changes encoding, one
        constant changes. The default `strict` keeps correctness the norm, and the one place that tolerates bad input (logging)
        says so explicitly. The same idea is behind setting `encoding` once on a database connection or an HTTP client, rather
        than decoding by hand at every call site."""),
    predict("Normal forms side by side", "medium",
        code="""
        import unicodedata as ud

        words = ["café", "cafe\\u0301", "ﬁancé", "ＣＡＦＥ"]
        for form in ["NFC", "NFD", "NFKC"]:
            print(form, [len(ud.normalize(form, w)) for w in words])
        print(ud.normalize("NFC", words[0]) == ud.normalize("NFC", words[1]))
        print(ud.normalize("NFKC", words[3]).casefold() == "cafe")
        """,
        hints=["NFC composes, NFD decomposes, NFKC also replaces compatibility characters (ligatures, full-width letters)."],
        why="""NFC makes both spellings of café 4 code points; NFD makes both 5 (`e` + accent). The `ﬁ` ligature is one code point under
        NFC and NFD but becomes `f` + `i` under NFKC, and full-width letters become ordinary ones. So NFC is enough to make the two
        cafés equal, while NFKC plus casefold makes full-width `ＣＡＦＥ` match `cafe`. Pick the weakest form that does the job: NFC
        for storage, NFKC for search keys."""),
)

section("hard", "Hard",
    write("Truncate bytes without splitting a character", "hard", tag="GenAI",
        prompt="""An API field accepts at most `max_bytes` bytes of UTF-8. Write `truncate_utf8(text, max_bytes)` returning the
        longest **prefix** of `text` whose UTF-8 encoding fits, never cutting a character in half. Return a `str`.""",
        code="""
        def truncate_utf8(text, max_bytes):
            pass
        """,
        tests="""
        assert truncate_utf8("hello", 3) == "hel"
        assert truncate_utf8("café", 4) == "caf"
        assert truncate_utf8("café", 5) == "café"
        assert truncate_utf8("€€€", 7) == "€€"
        assert truncate_utf8("\\U0001F600ok", 3) == ""
        assert truncate_utf8("", 10) == ""
        """,
        hints=["Encode, cut the bytes at `max_bytes`, then decode with `errors=\"ignore\"`: a cut in the middle of a character leaves an incomplete sequence at the end, which `ignore` drops.",
               "Is it safe to use `ignore` here? Only the end can be damaged, because the bytes came from valid UTF-8."],
        solution="""
        def truncate_utf8(text, max_bytes):
            return text.encode("utf-8")[:max_bytes].decode("utf-8", errors="ignore")
        """,
        why="""Cutting the bytes can leave the first one or two bytes of a multi-byte character at the end, which is invalid UTF-8.
        Because the input was valid UTF-8, the **only** damage is that incomplete tail, so decoding with `ignore` drops exactly those
        bytes and nothing else: a rare case where `ignore` is the right tool. Slicing the `str` by characters would not work, since
        the limit is in bytes (`"€€€"` is 3 characters but 9 bytes). This is how you safely fit text into byte-limited fields such as
        HTTP headers, database index keys or some LLM metadata fields."""),
    fix("Read the code: a loader that guesses wrong", "hard", tag="Data work",
        prompt="""This loader reads files of unknown encoding. It tries Latin-1 first "because it never fails", so UTF-8 files
        come out as mojibake, and UTF-16 files (Excel's "Unicode text") come out full of null characters. Rewrite `load_text` to
        try encodings in a sensible order: UTF-16 if the data starts with a UTF-16 BOM, then UTF-8 (stripping a BOM), and only then
        cp1252 as a last resort. Return `(text, encoding_used)`.""",
        code="""
        def load_text(data):
            for enc in ["latin-1", "utf-8", "utf-16"]:
                try:
                    return data.decode(enc), enc
                except UnicodeDecodeError:
                    continue
        """,
        tests="""
        assert load_text("Café €5".encode("utf-8")) == ("Café €5", "utf-8")
        assert load_text("\\ufeffid,name".encode("utf-8")) == ("id,name", "utf-8")
        assert load_text("Café".encode("utf-16")) == ("Café", "utf-16")
        assert load_text("Café €5".encode("cp1252")) == ("Café €5", "cp1252")
        assert load_text(b"plain") == ("plain", "utf-8")
        """,
        hints=["A decoder that never fails must come **last**, otherwise nothing after it is ever tried.",
               "UTF-16 files written by Python and Excel start with a BOM: `b\"\\xff\\xfe\"` or `b\"\\xfe\\xff\"`. Check `data.startswith(...)` first.",
               "Decode UTF-8 with `utf-8-sig` so a UTF-8 BOM is removed, but report the encoding as `\"utf-8\"`."],
        solution="""
        def load_text(data):
            if data.startswith((b"\\xff\\xfe", b"\\xfe\\xff")):
                return data.decode("utf-16"), "utf-16"
            try:
                return data.decode("utf-8-sig"), "utf-8"
            except UnicodeDecodeError:
                return data.decode("cp1252", errors="replace"), "cp1252"
        """,
        why="""The original's order was backwards: Latin-1 accepts every byte sequence, so it always "succeeded" first and the better
        candidates were never tried. The rule for guessing is **strictest first**: a BOM is near-certain evidence, UTF-8 rarely
        decodes non-UTF-8 text by accident (random high bytes almost never form valid sequences), and a permissive single-byte
        encoding is only a fallback. cp1252 is a better fallback than Latin-1 for Western data because it maps `€` and smart quotes
        correctly, and `errors="replace"` covers its five undefined bytes. Returning the encoding used lets callers log it. For
        harder cases, the `charset-normalizer` library makes statistical guesses; the best solution is still to agree on UTF-8
        with whoever produces the files."""),
    write("Remove invisible and control characters", "hard", tag="RAG",
        prompt="""Text extracted from PDFs and web pages contains invisible characters that break matching and waste tokens:
        zero-width spaces, BOMs, soft hyphens, control characters, and odd spaces. Write `clean_invisible(text)` that removes
        characters whose Unicode category is `Cf` (format) or `Cc` (control), **except** `\\n` and `\\t`, and turns every
        character in category `Zs` (space separators, such as the non-breaking space) into a normal space.""",
        code="""
        import unicodedata

        def clean_invisible(text):
            pass
        """,
        tests="""
        raw = "Re\\u200bfund\\u00a0policy\\ufeff\\u00ad:\\x07 5\\u2009days\\nnext\\tline"
        assert clean_invisible(raw) == "Refund policy: 5 days\\nnext\\tline"
        assert clean_invisible("plain") == "plain"
        assert len(clean_invisible("\\u200b\\u200c\\u200d")) == 0
        """,
        hints=["`unicodedata.category(ch)` returns a two-letter code. Build the result with a generator and `join`.",
               "Check `\\n` and `\\t` before the control-character rule, because they are in category `Cc`."],
        solution="""
        import unicodedata

        def clean_invisible(text):
            out = []
            for ch in text:
                cat = unicodedata.category(ch)
                if ch in "\\n\\t":
                    out.append(ch)
                elif cat in ("Cf", "Cc"):
                    continue
                elif cat == "Zs":
                    out.append(" ")
                else:
                    out.append(ch)
            return "".join(out)
        """,
        why="""Unicode categories describe what a character **is**, so the rule covers every zero-width character, BOM, soft hyphen and
        control code without listing them one by one: `U+200B` (zero-width space), `U+FEFF` (BOM) and `U+00AD` (soft hyphen) are
        `Cf`, the bell character is `Cc`, and both the non-breaking space and the thin space are `Zs`. Newlines and tabs are kept
        explicitly because they carry structure. Invisible characters are a real RAG problem: "Re\\u200bfund" never matches "Refund"
        in keyword search, inflates token counts, and can even be used to hide instructions from human reviewers in prompt injection
        attacks."""),
    predict("Bytes, slices and decoding traps", "hard",
        code="""
        data = "€uro".encode("utf-8")
        print(data, len(data))
        print(data[:2].decode("utf-8", errors="replace"), data[1:].decode("utf-8", errors="replace"))
        print(data.decode("cp1252"))
        print("Zoë".encode("utf-16"), len("Zoë".encode("utf-16")))
        print(b"A" == "A", b"A"[0] == ord("A"), bytes([72, 105]))
        """,
        hints=["`€` is three bytes. A slice of bytes can start or end in the middle of a character.",
               "UTF-16 output from Python starts with a 2-byte BOM."],
        why="""Cutting after two bytes keeps an incomplete `€`, shown as one `�`; starting at byte 1 begins with two continuation bytes,
        each replaced. Decoding the UTF-8 `€` as cp1252 gives the classic mojibake `â‚¬`. Python's `utf-16` codec writes a BOM
        (`\\xff\\xfe`, little-endian) then two bytes per character, 8 bytes for "Zoë". A `bytes` never equals a `str`, but a byte is
        just an integer, so `b"A"[0]` equals `ord("A")`, and `bytes([72, 105])` builds bytes from integers."""),
)

section("interview", "Interview questions",
    explain("What is the difference between `str` and `bytes` in Python 3, and where does each belong?", "medium", tag="Interview",
        why="""`str` is a sequence of Unicode code points: text. `bytes` is an immutable sequence of integers 0 to 255: raw data. An
        encoding (usually UTF-8) converts between them with `encode` and `decode`. Text belongs in `str` everywhere inside the
        program; `bytes` belongs at the boundaries: files opened in binary mode, sockets, HTTP bodies, hashing (`hashlib` needs
        bytes), compression, encryption and binary formats. The rule is "decode early, encode late, and name the encoding
        explicitly". Python 3 deliberately refuses to mix them (`"a" + b"a"` raises), which turns encoding mistakes into errors
        instead of silent corruption, unlike Python 2."""),
    explain("A colleague says \"it works on my Mac but the text is garbled on the Windows server\". What do you check?", "medium", tag="Interview",
        why="""Almost certainly an implicit encoding: `open()`, `read_text()`, `subprocess` output or a CSV reader without
        `encoding=`, which uses the platform default (UTF-8 on macOS and Linux, often cp1252 on Windows), so UTF-8 files are
        decoded as cp1252 and accents turn into `Ã©`. Check every boundary: file reads and writes, `pd.read_csv`, database
        connection character sets, HTTP response decoding, and console output (a cp1252 console can raise `UnicodeEncodeError` on
        `print`). Fix by passing `encoding="utf-8"` explicitly (and `utf-8-sig` for files from Excel), or enable UTF-8 mode with
        `PYTHONUTF8=1`, which Python 3.15 makes the default. Also look for a BOM breaking the first column name."""),
    explain("How would you handle text of unknown or mixed encoding in a data pipeline?", "hard", tag="Interview",
        why="""First try to remove the unknown: ask the source, read metadata (HTTP `Content-Type` charset, XML declarations, database
        collations). If you must guess, go strictest first: a BOM identifies UTF-8 or UTF-16; then try strict UTF-8, which rarely
        decodes non-UTF-8 data by accident; only then fall back to a single-byte encoding such as cp1252, which never fails and
        therefore must be last; libraries like `charset-normalizer` add statistical detection. Record the encoding used per file and
        count replacement characters, so silent fallbacks show up in monitoring. After decoding, normalise (NFC), remove invisible
        characters and fix mojibake (`ftfy`) as a cleaning step that keeps the original bytes available. And store everything as
        UTF-8 from then on, so the problem happens once, at ingestion."""),
)

recap(
    "Inside Python text is `str` (code points); at every boundary it is `bytes`. Decode early, encode late, and always name the encoding.",
    "UTF-8 uses 1 to 4 bytes per code point and leaves ASCII unchanged. Byte length is not `len`, and cutting bytes can split a character.",
    "`strict` errors are the default for a reason. `replace` for display, `backslashreplace` for logs; count replacements in pipelines.",
    "Mojibake (`Ã©`, `â€™`) means bytes were decoded with the wrong encoding, usually a missing `encoding=` on Windows. Latin-1 and cp1252 never fail, so they hide the bug.",
    "Read Excel CSVs with `utf-8-sig`. Normalise with NFC for storage, NFKC (and accent folding) for search keys.",
)
