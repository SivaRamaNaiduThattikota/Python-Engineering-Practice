from lesson import *
from diagrams import *

lesson(
    id="m12-2", num="12.2", title="csv, json and JSON Lines",
    intro="The three text formats that move most data between tools: CSV for tables, JSON for nested records and API payloads, "
          "and JSON Lines for datasets, logs and LLM batch files. Readers and writers, quoting and dialects, JSON type mapping and "
          "its traps, custom encoders and decoders, and streaming JSONL with bad-line handling. Applied to labels, metrics, "
          "evaluation exports, chunked corpora and event logs.",
    desc="Readers and writers, dialects, custom encoders, streaming JSONL.",
    keys="csv reader writer dictreader dictwriter newline quoting dialect delimiter utf-8-sig bom json loads dumps load dump indent ensure_ascii sort_keys default object_hook nan allow_nan jsondecodeerror jsonl json lines gzip stream encoder decoder",
)

term("CSV", "Comma-separated values: a table as text, one row per line, fields separated by a delimiter and quoted when they contain it. Every value is a string.")
term("JSON", "JavaScript Object Notation: text for nested data built from objects, arrays, strings, numbers, booleans and null.")
term("JSON Lines", "A file with one complete JSON value (usually an object) per line, so it can be streamed, appended to and split. Also called JSONL or NDJSON.")

section("csv", "CSV with the `csv` module",
    p("""CSV looks simple enough to split on commas, and that is the bug: a field can contain a comma, a quote or even a newline, in which case it is wrapped in
    double quotes and inner quotes are doubled (a field `Smith, "Jr"` is written as `"Smith, \"\"Jr\"\"\"`). The **`csv`** module implements those rules. `csv.reader(f)` yields each row as a
    list of strings, `csv.writer(f).writerow(values)` writes one, and the dictionary versions are what you usually want: **`csv.DictReader`** uses the
    header row as keys, and **`csv.DictWriter(f, fieldnames=...)`** writes dicts, with `writeheader()` for the header line and `extrasaction="ignore"`
    to skip keys that are not columns (by default extra keys raise `ValueError`)."""),
    p("""Three rules make CSV code correct. Open files with **`newline=""`**, so the `csv` module, not text mode, handles line endings, including newlines
    inside quoted fields (the writer ends rows with `\\r\\n`, as the format specifies). Remember that **every value read is a string**, so convert types
    yourself: `int(row["id"])`, `float(row["score"])`, and treat `""` as missing. And pick the encoding deliberately: files saved by Excel as "CSV UTF-8"
    start with a byte-order mark, which `encoding="utf-8-sig"` removes (problem 10). Other dialects are options: `delimiter=";"` for European exports,
    `delimiter="\\t"` for TSV, and `quoting=csv.QUOTE_ALL` or `QUOTE_NONNUMERIC` to control quoting."""),
    ex("""
    import csv, io

    rows = [{"id": 1, "question": "Refund, or credit?", "answer": 'She said "5 days"', "score": 0.9},
            {"id": 2, "question": "Two\\nlines", "answer": "ok", "score": 0.25}]
    buf = io.StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=["id", "question", "answer", "score"])
    writer.writeheader()
    writer.writerows(rows)
    text = buf.getvalue()
    print(repr(text))
    back = list(csv.DictReader(io.StringIO(text, newline="")))
    print(back[0])
    print(back[1]["question"] == "Two\\nlines", type(back[1]["score"]).__name__, float(back[1]["score"]))
    """, "csv_basics.py"),
    p("""`io.StringIO` is an in-memory text file, convenient for examples and tests; the same code works with a real file opened as
    `open(path, "w", encoding="utf-8", newline="")`. The writer quoted only the fields that needed it, doubled the inner quotes, and the reader
    reconstructed every value exactly, as strings."""),
)

section("json", "JSON: type mapping and options",
    fig(table(["Python", "JSON", "back in Python"], [
        ["dict", "object", "dict"],
        ["list, tuple", "array", "list"],
        ["str", "string", "str"],
        ["int, float", "number", "int, float"],
        ["True, False, None", "true, false, null", "True, False, None"],
        ["non-str dict key 1", "\"1\"", "'1' (a str)"],
        ["set, datetime, Decimal", "TypeError", ""],
    ], hl={(1, 2), (5, 2), (6, 1)}, label="how json maps types, there and back"),
        "JSON has fewer types than Python: tuples come back as lists, keys become strings, and some types need a custom encoder."),
    p("""`json.dumps(obj)` turns Python data into a JSON string and `json.loads(text)` parses one; `json.dump(obj, f)` and `json.load(f)` do the same with a
    file. The mapping is: dict to object, list **and tuple** to array, str to string, int and float to number, `True`/`False` to `true`/`false`, `None` to
    `null`. It is lossy in ways that matter: tuples come back as lists, **dictionary keys become strings** (`{1: "a"}` round-trips to `{"1": "a"}`), and
    anything else, such as `datetime`, `Decimal`, `set`, NumPy numbers and your own classes, raises `TypeError: Object of type ... is not JSON
    serializable`."""),
    p("""Useful options: `indent=2` for human-readable output, `sort_keys=True` for stable output that diffs cleanly, `ensure_ascii=False` to write `é`
    instead of `\\u00e9` (keep the file UTF-8), and `separators=(",", ":")` for the most compact form. One trap deserves its own line: by default
    Python writes `float("nan")` and infinities as `NaN` and `Infinity`, which are **not valid JSON**: JavaScript's `JSON.parse`, many databases and
    strict parsers reject them. Pass `allow_nan=False` to make that an error and replace such values deliberately (problem 7)."""),
    ex("""
    import json

    data = {"id": 7, 3: "int key", "pair": (1, 2), "name": "café", "ok": True, "missing": None}
    text = json.dumps(data)
    print(text)
    print(json.loads(text))
    print(json.dumps({"b": 1, "a": [1, 2]}, indent=2, sort_keys=True))
    print(json.dumps({"loss": float("nan")}), json.dumps({"name": "café"}, ensure_ascii=False))
    try:
        json.dumps({"loss": float("inf")}, allow_nan=False)
    except ValueError as e:
        print("ValueError:", e)
    """, "json_basics.py"),
    p("""A parse failure raises **`json.JSONDecodeError`**, a subclass of `ValueError`, with the message, `lineno`, `colno` and character offset `pos`,
    which is what you report for a broken file or an LLM reply cut off mid-object (problem 9)."""),
)

section("custom", "Custom encoders and decoders",
    p("""To serialise other types, pass **`default=`** to `dumps`: a function called for every object the encoder does not know, which must return something it
    does know (a string, number, list or dict), or raise `TypeError`. A single `default` handles dates (`isoformat()`), `Decimal` (`str`, to keep exact
    digits), sets (a sorted list), dataclasses (`dataclasses.asdict`), paths, and NumPy values, which are the commonest cause of "not JSON
    serializable" in ML code, since `np.float32(0.9)` is not a Python `float` (problem 6). Subclassing `json.JSONEncoder` and overriding its `default`
    method does the same thing in class form."""),
    p("""In the other direction, **`object_hook=`** is called with every decoded object (as a dict), and whatever it returns replaces it, which lets you turn
    tagged dicts back into rich types (problem 14). `parse_float=Decimal` parses every number with a fraction as an exact `Decimal`, useful for money.
    Note what cannot be customised: `default` is never called for types JSON already handles, so a tuple always becomes an array, and dict keys must be
    strings, numbers, booleans or `None`; any other key raises `TypeError` even with a `default`."""),
    ex("""
    import json
    from dataclasses import dataclass, asdict
    from datetime import datetime
    from decimal import Decimal

    @dataclass
    class Run:
        name: str
        started: datetime
        cost: Decimal
        tags: set

    def default(o):
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, Decimal):
            return str(o)
        if isinstance(o, set):
            return sorted(o)
        if hasattr(o, "__dataclass_fields__"):
            return asdict(o)
        raise TypeError(f"cannot serialise {type(o).__name__}")

    run = Run("exp-1", datetime(2025, 3, 1, 9, 30), Decimal("0.10"), {"rag", "eval"})
    print(json.dumps(run, default=default))
    print(json.loads('{"price": 0.10}', parse_float=Decimal))
    """, "custom.py"),
)

section("jsonl", "JSON Lines: streaming records",
    fig(chain(["one JSON object|per line", "read line by line", "json.loads(line)", ("constant memory,|bad lines skippable", "good")]),
        "JSON Lines streams records: each line is a complete document, so a reader never needs the whole file in memory."),
    p("""A big JSON array must be parsed whole before you can use its first element. **JSON Lines** puts one JSON object per line instead: a reader handles one
    line at a time with constant memory, a writer appends records as they are produced, a crash loses at most the last line, and files can be split,
    concatenated and counted with ordinary line tools. That is why datasets (Hugging Face), fine-tuning data, LLM batch request and result files,
    evaluation sets and structured logs are almost always `.jsonl`."""),
    p("""Write each record with `json.dumps(record, ensure_ascii=False)` followed by `"\\n"` (no `indent`, which would spread one record over many lines).
    Read by iterating over the file, skipping blank lines, and decide what a bad line means: in a pipeline over millions of records, one broken line
    should usually be **counted and reported with its line number**, not crash the job; for a hand-edited evaluation set, it should fail loudly.
    Compressed files stream the same way with `gzip.open(path, "rt", encoding="utf-8")`."""),
    ex("""
    import gzip, json, os, tempfile

    path = os.path.join(tempfile.mkdtemp(), "batch.jsonl.gz")
    requests = [{"custom_id": f"req-{i}", "body": {"prompt": f"Summarise ticket {i}"}} for i in range(3)]
    with gzip.open(path, "wt", encoding="utf-8") as f:
        for r in requests:
            f.write(json.dumps(r, ensure_ascii=False) + "\\n")
        f.write('{"custom_id": "req-3", "body": {"prom\\n')
    good, bad = [], []
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for number, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                good.append(json.loads(line))
            except json.JSONDecodeError as e:
                bad.append((number, e.msg))
    print(len(good), good[-1]["custom_id"], bad)
    """, "jsonl.py"),
)

section("warmup", "Warm-up",
    predict("CSV quoting and types", "easy",
        code="""
        import csv, io

        buf = io.StringIO(newline="")
        w = csv.writer(buf)
        w.writerow(["id", "text", "score"])
        w.writerow([1, "plain", 0.5])
        w.writerow([2, "a, b", None])
        w.writerow([3, 'say "hi"', True])
        print(buf.getvalue().splitlines())
        rows = list(csv.reader(io.StringIO(buf.getvalue(), newline="")))
        print(rows[2], rows[3][1], len(rows))
        """,
        hints=["Only fields containing the delimiter, a quote or a newline are quoted, and inner quotes are doubled. `None` is written as an empty string."],
        why="""The writer converts every value with `str`, except `None`, which becomes an empty field, so the reader gets back strings: `"2"`, not 2, and `""` where the
        `None` was. A field with a comma is wrapped in quotes and a field with quotes is wrapped and has its quotes doubled; the reader undoes both, so
        `rows[3][1]` is the original text. Four rows were written, header included."""),
    write("Read labelled examples from CSV", "easy", tag="ML",
        prompt="""Write `read_examples(path)` reading a UTF-8 CSV with the columns `id`, `text`, `label` and `score`, and returning a list of dicts with `id` as an int,
        `text` and `label` stripped, and `score` as a float, or `None` when the cell is empty. Skip rows whose `text` is empty after stripping.""",
        code="""
        import csv

        def read_examples(path):
            pass
        """,
        tests="""
        import os, tempfile
        path = os.path.join(tempfile.mkdtemp(), "train.csv")
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write('id,text,label,score\\r\\n1,"Win a prize, now!",spam ,0.97\\r\\n2,  ,ham,0.1\\r\\n3,"Meeting\\nat 3",ham,\\r\\n4,Café hours?, ham,0.2\\r\\n')
        rows = read_examples(path)
        assert [r["id"] for r in rows] == [1, 3, 4]
        assert rows[0] == {"id": 1, "text": "Win a prize, now!", "label": "spam", "score": 0.97}
        assert rows[1]["text"] == "Meeting\\nat 3" and rows[1]["score"] is None and rows[2]["label"] == "ham"
        """,
        hints=["`csv.DictReader(f)` with the file opened using `newline=\"\"`.", "`float(cell) if cell.strip() else None`."],
        solution="""
        import csv


        def read_examples(path):
            out = []
            with open(path, encoding="utf-8", newline="") as f:
                for row in csv.DictReader(f):
                    text = row["text"].strip()
                    if not text:
                        continue
                    score = row["score"].strip()
                    out.append({"id": int(row["id"]), "text": text, "label": row["label"].strip(),
                                "score": float(score) if score else None})
            return out
        """,
        why="""`DictReader` handles the quoting, so a comma or a newline inside a quoted text stays part of the field, which a `split(",")` would break. Everything
        arrives as a string, so the function converts each column explicitly and decides what an empty cell means (`None`, not 0.0, which would be a wrong
        score). Stripping matters because hand-edited CSVs are full of stray spaces, and `"spam "` would become a separate class in a training set."""),
    fix("An export with no header that crashes on extra keys", "easy", tag="Data work",
        prompt="""`export_tickets` writes tickets to CSV with the columns `id`, `title` and `status`. The file has no header row, and tickets that carry extra keys such
        as `internal_note` crash the export with `ValueError`. Fix both, keeping the column order.""",
        code="""
        import csv

        def export_tickets(path, tickets):
            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["id", "title", "status"])
                writer.writerows(tickets)
        """,
        tests="""
        import csv, os, tempfile
        path = os.path.join(tempfile.mkdtemp(), "tickets.csv")
        export_tickets(path, [{"id": 1, "title": "Refund", "status": "open"}, {"id": 2, "status": "closed", "title": "Login", "internal_note": "VIP"}])
        with open(path, encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        assert [r["title"] for r in rows] == ["Refund", "Login"]
        assert list(rows[1]) == ["id", "title", "status"] and "VIP" not in open(path, encoding="utf-8").read()
        """,
        hints=["`writer.writeheader()` before the rows, and `extrasaction=\"ignore\"` in the constructor."],
        solution="""
        import csv

        def export_tickets(path, tickets):
            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["id", "title", "status"], extrasaction="ignore")
                writer.writeheader()
                writer.writerows(tickets)
        """,
        why="""`DictWriter` never writes a header on its own; without it, a reader treats the first ticket as column names. By default it also refuses dicts with keys
        that are not columns, which is a safety feature (a misspelt column would otherwise vanish), so ignoring extras should be a decision: here it is
        right, because `internal_note` must **not** leave the system. Columns come out in `fieldnames` order whatever the order of each dict's keys."""),
    predict("What JSON keeps and loses", "easy",
        code="""
        import json

        data = {"n": 1, 2: "two", "t": (1, 2), "f": 1.0, "none": None, "yes": True}
        text = json.dumps(data)
        print(text)
        back = json.loads(text)
        print(back == data, back["t"], list(back), type(back["f"]).__name__)
        print(json.dumps([float("nan"), -float("inf")]), json.dumps("é"), json.dumps("é", ensure_ascii=False))
        """,
        hints=["Integer keys become strings, tuples become arrays, and floats stay floats."],
        why="""Keys are converted to strings, so `2` comes back as `"2"`, and the tuple comes back as a list; those two changes make the round trip unequal. `1.0` stays a
        float because JSON writes it as `1.0`. NaN and infinity are written as `NaN` and `-Infinity`, which Python accepts but standard JSON does not. With
        the default `ensure_ascii=True`, non-ASCII characters are escaped."""),
)

section("medium", "Medium",
    write("Read and write JSON Lines", "medium", tag="GenAI",
        prompt="""Write `write_jsonl(path, records)` writing one compact JSON object per line (non-ASCII kept as is, UTF-8) and returning the number written, and a
        **generator** `read_jsonl(path, errors=None)` yielding each object. Skip blank lines. A line that is not valid JSON or not a JSON object is bad: if
        `errors` is a list, append `(line_number, message)` and continue (the message is the `JSONDecodeError`'s `msg`, or `"not an object"`); otherwise
        raise `ValueError(f"line {n}: {message}")`.""",
        code="""
        import json

        def write_jsonl(path, records):
            pass

        def read_jsonl(path, errors=None):
            pass
        """,
        tests="""
        import os, tempfile
        d = tempfile.mkdtemp()
        path = os.path.join(d, "turns.jsonl")
        assert write_jsonl(path, [{"role": "user", "content": "Où est ma commande ?"}, {"role": "assistant", "content": "En route."}]) == 2
        assert open(path, encoding="utf-8").read().splitlines()[0] == '{"role": "user", "content": "Où est ma commande ?"}'
        with open(path, "a", encoding="utf-8") as f:
            f.write("\\n[1, 2]\\n{\\"role\\": \\"user\\", \\"content\\": \\"cut\\n")
        errs = []
        assert [r["role"] for r in read_jsonl(path, errs)] == ["user", "assistant"]
        assert errs == [(4, "not an object"), (5, "Invalid control character at")]
        gen = read_jsonl(os.path.join(d, "missing.jsonl"))
        try:
            next(gen)
            assert False
        except FileNotFoundError:
            pass
        try:
            list(read_jsonl(path))
            assert False
        except ValueError as e:
            assert str(e) == "line 4: not an object"
        """,
        hints=["`json.dumps(record, ensure_ascii=False) + \"\\n\"`.",
               "Because `read_jsonl` is a generator, nothing runs (not even `open`) until the first `next`."],
        solution="""
        import json


        def write_jsonl(path, records):
            count = 0
            with open(path, "w", encoding="utf-8") as f:
                for record in records:
                    f.write(json.dumps(record, ensure_ascii=False) + "\\n")
                    count += 1
            return count


        def read_jsonl(path, errors=None):
            with open(path, encoding="utf-8") as f:
                for n, line in enumerate(f, start=1):
                    if not line.strip():
                        continue
                    try:
                        obj = json.loads(line)
                        message = None if isinstance(obj, dict) else "not an object"
                    except json.JSONDecodeError as e:
                        message = e.msg
                    if message is None:
                        yield obj
                    elif errors is not None:
                        errors.append((n, message))
                    else:
                        raise ValueError(f"line {n}: {message}")
        """,
        why="""The writer produces exactly one line per record because `dumps` without `indent` never emits a newline (newlines inside strings are escaped as `\\n`).
        The reader is a generator, so a file of any size is processed one line at a time, and the caller chooses the policy: collect bad lines with
        their numbers (an ingestion job reports "2 bad lines" and continues) or fail at the first one (a test set). Blank lines are skipped without counting,
        but line numbers still count them, so the reported number is the one an editor shows. The truncated last line, typical of a crashed writer or an
        interrupted download, is reported instead of losing the whole file."""),
    write("Serialise ML objects to JSON", "medium", tag="ML",
        prompt="""Write `to_json(obj, **kwargs)` that calls `json.dumps` with a `default` function handling: `datetime` and `date` (ISO strings), `Decimal` (string),
        `set` and `frozenset` (sorted list), dataclass instances (`asdict`), `pathlib.Path` (POSIX string), NumPy scalars (`.item()`) and NumPy arrays
        (`.tolist()`). Anything else raises `TypeError` naming the type. Extra keyword arguments go to `json.dumps`.""",
        code="""
        import json
        from dataclasses import asdict, is_dataclass
        from datetime import date, datetime
        from decimal import Decimal
        from pathlib import PurePath

        import numpy as np

        def to_json(obj, **kwargs):
            pass
        """,
        tests="""
        import json
        from dataclasses import dataclass
        from datetime import date, datetime
        from decimal import Decimal
        from pathlib import PurePosixPath
        import numpy as np

        @dataclass
        class Metrics:
            f1: float
            day: date

        payload = {"acc": np.float32(0.5), "n": np.int64(3), "emb": np.array([[1, 2], [3, 4]]), "when": datetime(2025, 3, 1, 9, 30),
                   "cost": Decimal("0.10"), "tags": {"b", "a"}, "model": PurePosixPath("models/v3.pt"), "m": Metrics(0.9, date(2025, 3, 1))}
        out = json.loads(to_json(payload, sort_keys=True))
        assert out == {"acc": 0.5, "cost": "0.10", "emb": [[1, 2], [3, 4]], "m": {"day": "2025-03-01", "f1": 0.9}, "model": "models/v3.pt",
                       "n": 3, "tags": ["a", "b"], "when": "2025-03-01T09:30:00"}
        assert to_json({"x": 1}, indent=1) == '{\\n "x": 1\\n}'
        try:
            to_json({"f": print})
            assert False
        except TypeError as e:
            assert "builtin_function_or_method" in str(e)
        """,
        hints=["Check `datetime`/`date` with one `isinstance(o, (datetime, date))`; `np.generic` is the base class of NumPy scalars.",
               "`is_dataclass(o) and not isinstance(o, type)` tells an instance from the class itself."],
        solution="""
        import json
        from dataclasses import asdict, is_dataclass
        from datetime import date, datetime
        from decimal import Decimal
        from pathlib import PurePath

        import numpy as np


        def _default(o):
            if isinstance(o, (datetime, date)):
                return o.isoformat()
            if isinstance(o, Decimal):
                return str(o)
            if isinstance(o, (set, frozenset)):
                return sorted(o)
            if is_dataclass(o) and not isinstance(o, type):
                return asdict(o)
            if isinstance(o, PurePath):
                return o.as_posix()
            if isinstance(o, np.generic):
                return o.item()
            if isinstance(o, np.ndarray):
                return o.tolist()
            raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")


        def to_json(obj, **kwargs):
            return json.dumps(obj, default=_default, **kwargs)
        """,
        why="""The encoder calls `default` only for objects it cannot handle, and then encodes whatever `default` returns, recursively. That is why the dataclass works in two
        steps: `asdict` returns a dict that still holds a `date`, and the encoder calls `default` again for it. NumPy is the everyday case in ML: metrics
        computed with NumPy are `np.float32` or `np.int64`, not Python numbers, so `json.dumps(metrics)` fails at the end of a training run unless they are
        converted with `.item()`; arrays become nested lists with `.tolist()`. Decimals become strings to keep their exact digits. Raising `TypeError` for
        unknown types keeps the standard error instead of silently writing something like `str(obj)`."""),
    fix("Metrics JSON that other tools reject", "medium", tag="ML",
        prompt="""`metrics_json` serialises evaluation metrics for a dashboard, but when a metric is undefined (NaN, for example precision with no positive predictions) or
        infinite, the output contains `NaN` or `Infinity`, and the dashboard's JSON parser rejects the whole document. Make it write `null` for every
        non-finite float, at any depth in dicts and lists, and pass `allow_nan=False` so any missed case fails loudly.""",
        code="""
        import json
        import math

        def metrics_json(metrics):
            return json.dumps(metrics, sort_keys=True)
        """,
        tests="""
        import json
        def strict_loads(text):
            def bad(name):
                raise ValueError(f"non-standard constant {name}")
            return json.loads(text, parse_constant=bad)
        m = {"precision": float("nan"), "recall": 0.0, "per_class": [{"label": "spam", "f1": float("inf")}, {"label": "ham", "f1": 0.8}], "n": 10}
        out = strict_loads(metrics_json(m))
        assert out == {"n": 10, "per_class": [{"f1": None, "label": "spam"}, {"f1": 0.8, "label": "ham"}], "precision": None, "recall": 0.0}
        assert metrics_json({"loss": -float("inf"), "steps": (1, float("nan"))}) == '{"loss": null, "steps": [1, null]}'
        assert m["precision"] != m["precision"]
        """,
        hints=["A small recursive function: dicts and lists/tuples are rebuilt, floats checked with `math.isfinite`.", "Do not modify the caller's dict."],
        solution="""
        import json
        import math

        def _clean(value):
            if isinstance(value, float) and not math.isfinite(value):
                return None
            if isinstance(value, dict):
                return {k: _clean(v) for k, v in value.items()}
            if isinstance(value, (list, tuple)):
                return [_clean(v) for v in value]
            return value

        def metrics_json(metrics):
            return json.dumps(_clean(metrics), sort_keys=True, allow_nan=False)
        """,
        why="""Python's `json` module happily writes `NaN` and `Infinity` because JavaScript has those values, but the JSON standard does not, so browsers' `JSON.parse`,
        many databases and strict parsers reject the document. The `default` hook cannot help, because floats are a type JSON "already handles", so the
        values must be cleaned before encoding, recursively and without mutating the caller's metrics (which still hold the NaN, as the last assert shows).
        `null` is the honest value for an undefined metric, and `allow_nan=False` turns any future slip into an exception instead of a broken dashboard."""),
    choose("Copying nested data: deepcopy or a JSON round trip", "medium", tag="Data work",
        prompt="Both copy a list of 300 nested records made only of dicts, lists, strings and numbers. Which is faster?",
        setup="""import copy, json
records = [{"id": i, "tags": ["a", "b"], "meta": {"score": 0.5, "source": "faq.md", "spans": [[0, 10], [12, 20]]}} for i in range(300)]""",
        options={
            "a": "out = copy.deepcopy(records)",
            "b": "out = json.loads(json.dumps(records))",
        },
        answer="b",
        hints=["`copy.deepcopy` is written in Python and handles any object, with a memo of everything it copied; the `json` module has a C accelerator."],
        why="""`deepcopy` is general: for every object it looks up a copier, records the object in a memo dictionary (so shared and recursive references survive), and runs in
        Python code. `json.dumps` and `json.loads` run in C and only understand plain data, which makes the round trip faster for exactly this kind of
        payload. The price is that it is **lossy**: tuples become lists, non-string keys become strings, and anything else raises, so use it only for data
        that is already plain JSON, such as parsed API responses; for anything else, `deepcopy` is the correct tool."""),
    trace("Reading JSONDecodeError", "medium",
        prompt="Fill in `msg`, `line` and `col` after each marked line.",
        code="""
        import json

        def info(text):
            try:
                json.loads(text)
                return "ok", 0, 0
            except json.JSONDecodeError as e:
                return e.msg, e.lineno, e.colno

        msg, line, col = info('{"label": "spam"}')  # row: "valid"
        msg, line, col = info('{"label": "spam",\\n "score": 0.9')  # row: "cut off"
        msg, line, col = info("{'label': 'spam'}")  # row: "single quotes"
        msg, line, col = info('{"a": 1} Hope this helps!')  # row: "chatty reply"
        """,
        trace_vars=["msg", "line", "col"],
        hints=["The messages used here are `Expecting ',' delimiter`, `Expecting property name enclosed in double quotes` and `Extra data`.",
               "`lineno` and `colno` count from 1; the position is where the parser was when it gave up."],
        why="""A truncated object fails where the parser expected a comma or a closing brace: at the end of the text, line 2, just after `0.9`. Python-style single quotes
        are not JSON, so the parser fails at once on the first key, column 2. A valid object followed by chatter fails with "Extra data" at the first
        character after the object, column 10: `json.loads` insists the whole text is one value. These three are the commonest failures when parsing LLM
        output, and reporting the line and column (or the `pos` offset) makes them quick to diagnose."""),
    fix("A CSV from Excel whose header does not match", "medium", tag="Data work",
        prompt="""`load_ids` reads the `id` column of a CSV. It works on the team's exported files but raises `KeyError: 'id'` on the file a colleague saved from Excel,
        although the header clearly reads `id,name`. Fix it so both kinds of file work.""",
        code="""
        import csv

        def load_ids(path):
            with open(path, encoding="utf-8", newline="") as f:
                return [int(row["id"]) for row in csv.DictReader(f)]
        """,
        tests="""
        import os, tempfile
        d = tempfile.mkdtemp()
        excel, plain = os.path.join(d, "excel.csv"), os.path.join(d, "plain.csv")
        with open(excel, "w", encoding="utf-8-sig", newline="") as f:
            f.write("id,name\\r\\n7,Ana\\r\\n9,Bo\\r\\n")
        with open(plain, "w", encoding="utf-8", newline="") as f:
            f.write("id,name\\n1,Cy\\n")
        assert load_ids(excel) == [7, 9]
        assert load_ids(plain) == [1]
        """,
        hints=["Look at the first bytes of the Excel file: `open(excel, \"rb\").read(5)`."],
        solution="""
        import csv

        def load_ids(path):
            with open(path, encoding="utf-8-sig", newline="") as f:
                return [int(row["id"]) for row in csv.DictReader(f)]
        """,
        why="""Excel's "CSV UTF-8" format starts the file with a byte-order mark, the bytes `EF BB BF`. Decoded as plain UTF-8 they become the invisible character `\\ufeff`,
        so the first column is really named `"\\ufeffid"`, and `row["id"]` fails although the header looks right when printed. The `utf-8-sig` codec removes
        a leading mark if there is one and otherwise behaves exactly like UTF-8, so it is the safe choice for reading any CSV that may have passed through
        Excel. When **writing** for Excel users, `utf-8-sig` also makes Excel detect the encoding correctly."""),
    write("Turn a CSV of documents into JSONL chunks", "medium", tag="RAG",
        prompt="""Write `csv_to_chunks(csv_path, out_path, max_words=50)`. The CSV has columns `id`, `title` and `body` (bodies contain commas, quotes and newlines). Split
        each body into words (`split()`) and write one JSONL record per chunk of at most `max_words` words: `{"doc_id": id, "chunk": k, "title": title,
        "text": the words joined with single spaces}`, with `k` counting from 0 per document. Skip documents whose body is empty. Return `(documents,
        chunks)` written.""",
        code="""
        import csv, json

        def csv_to_chunks(csv_path, out_path, max_words=50):
            pass
        """,
        tests="""
        import csv, json, os, tempfile
        d = tempfile.mkdtemp()
        src, out = os.path.join(d, "docs.csv"), os.path.join(d, "chunks.jsonl")
        body = "Refunds take five days, \\"business\\" days.\\nContact support if late. " + " ".join(f"w{i}" for i in range(12))
        with open(src, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerows([["id", "title", "body"], ["faq-1", "Refunds", body], ["faq-2", "Empty", "   "], ["faq-3", "Café", "Open daily"]])
        assert csv_to_chunks(src, out, max_words=10) == (2, 4)
        with open(out, encoding="utf-8") as f:
            recs = [json.loads(line) for line in f]
        assert [(r["doc_id"], r["chunk"]) for r in recs] == [("faq-1", 0), ("faq-1", 1), ("faq-1", 2), ("faq-3", 0)]
        assert recs[0]["text"] == 'Refunds take five days, "business" days. Contact support if late.' and recs[2]["text"] == "w10 w11"
        assert recs[3] == {"doc_id": "faq-3", "chunk": 0, "title": "Café", "text": "Open daily"}
        """,
        hints=["Read with `csv.DictReader` and write with `json.dumps(..., ensure_ascii=False)` inside the same loop, so nothing is held in memory.",
               "`words[i:i + max_words]` for `i` in `range(0, len(words), max_words)`."],
        solution="""
        import csv, json


        def csv_to_chunks(csv_path, out_path, max_words=50):
            documents = chunks = 0
            with open(csv_path, encoding="utf-8-sig", newline="") as src, open(out_path, "w", encoding="utf-8") as out:
                for row in csv.DictReader(src):
                    words = row["body"].split()
                    if not words:
                        continue
                    documents += 1
                    for k, start in enumerate(range(0, len(words), max_words)):
                        record = {"doc_id": row["id"], "chunk": k, "title": row["title"], "text": " ".join(words[start:start + max_words])}
                        out.write(json.dumps(record, ensure_ascii=False) + "\\n")
                        chunks += 1
            return documents, chunks
        """,
        why="""The two formats meet in one streaming loop: `DictReader` parses quoted bodies with commas, quotes and newlines correctly, and each chunk is written as soon as
        it is made, so a corpus of any size needs memory for one document only. `split()` also normalises whitespace, which is why the newline inside the
        body disappears from the chunk text. Each record carries its document id, chunk number and title, the metadata a RAG system stores next to the
        embedding so that answers can cite their source (5.P). Real chunkers split on tokens or sentences and overlap neighbouring chunks, but the file
        handling stays exactly this."""),
    predict("Dialects and QUOTE_NONNUMERIC", "medium",
        code="""
        import csv, io

        text = 'id;name;score\\n1;"Smith; J";0.5\\n2;"multi\\nline";0.7\\n'
        rows = list(csv.reader(io.StringIO(text, newline=""), delimiter=";"))
        print(len(rows), rows[1], rows[2])
        buf = io.StringIO(newline="")
        csv.writer(buf, quoting=csv.QUOTE_NONNUMERIC).writerow(["a", 1, 2.5, None])
        print(repr(buf.getvalue()))
        print(next(csv.reader(io.StringIO(buf.getvalue(), newline=""), quoting=csv.QUOTE_NONNUMERIC)))
        """,
        hints=["A quoted field may contain the delimiter and newlines. `QUOTE_NONNUMERIC` quotes every non-number when writing, and converts every unquoted field to `float` when reading."],
        why="""With `;` as the delimiter, the quoted `Smith; J` is one field, and the quoted field with a newline keeps the second record together, so there are three rows,
        not four. `QUOTE_NONNUMERIC` quotes strings (and `None`, written as `""`) but not numbers, and rows end with `\\r\\n`. Reading with the same option turns
        every unquoted field into a float, so `1` comes back as `1.0`, while the quoted empty string stays a string."""),
)

section("hard", "Hard",
    write("Summarise a compressed event log", "hard", tag="GenAI",
        prompt="""Write `summarise_events(path)` for a JSONL event log that may be gzip-compressed (when the name ends in `.gz`). Each good line is an object with a
        string `type` and an optional integer `tokens` (default 0). Return `{"events": count of good lines, "by_type": {type: count} with types sorted,
        "tokens": total tokens, "bad_lines": [line numbers]}`, where a bad line is invalid JSON, not an object, has no string `type`, or has `tokens` that is
        not an `int` (booleans do not count). Blank lines are ignored. Stream the file; do not read it whole.""",
        code="""
        import gzip, json

        def summarise_events(path):
            pass
        """,
        tests="""
        import gzip, json, os, tempfile
        d = tempfile.mkdtemp()
        lines = ['{"type": "request", "tokens": 120}', '{"type": "tool_call"}', '', '{"type": "request", "tokens": 80}',
                 '["not", "object"]', '{"tokens": 5}', '{"type": "request", "tokens": "12"}', '{"type": "error", "tokens": true}',
                 '{"type": "response", "tokens": 200}', '{"type": "resp']
        text = "\\n".join(lines) + "\\n"
        plain, packed = os.path.join(d, "events.jsonl"), os.path.join(d, "events.jsonl.gz")
        with open(plain, "w", encoding="utf-8") as f:
            f.write(text)
        with gzip.open(packed, "wt", encoding="utf-8") as f:
            f.write(text)
        expected = {"events": 4, "by_type": {"request": 2, "response": 1, "tool_call": 1}, "tokens": 400, "bad_lines": [5, 6, 7, 8, 10]}
        assert summarise_events(plain) == expected
        assert summarise_events(packed) == expected and list(summarise_events(packed)["by_type"]) == ["request", "response", "tool_call"]
        """,
        hints=["Choose the opener once: `opener = gzip.open if str(path).endswith(\".gz\") else open`, then `opener(path, \"rt\", encoding=\"utf-8\")`.",
               "`isinstance(True, int)` is `True`, so exclude `bool` explicitly."],
        solution="""
        import gzip, json


        def _good(obj):
            if not isinstance(obj, dict) or not isinstance(obj.get("type"), str):
                return False
            tokens = obj.get("tokens", 0)
            return isinstance(tokens, int) and not isinstance(tokens, bool)


        def summarise_events(path):
            opener = gzip.open if str(path).endswith(".gz") else open
            events = tokens = 0
            by_type, bad = {}, []
            with opener(path, "rt", encoding="utf-8") as f:
                for n, line in enumerate(f, start=1):
                    if not line.strip():
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        bad.append(n)
                        continue
                    if not _good(obj):
                        bad.append(n)
                        continue
                    events += 1
                    by_type[obj["type"]] = by_type.get(obj["type"], 0) + 1
                    tokens += obj.get("tokens", 0)
            return {"events": events, "by_type": dict(sorted(by_type.items())), "tokens": tokens, "bad_lines": bad}
        """,
        why="""`gzip.open` in text mode returns a file object that decompresses as it is read, so the same streaming loop handles both files, and choosing the opener
        once keeps the loop free of special cases. Validation is explicit because JSON gives no guarantees: an array, a missing `type`, a token count written
        as a string, and `true` (a `bool`, which Python counts as an `int`) are all rejected and reported by line number, and the truncated last line from an
        interrupted writer is just another bad line. Usage dashboards built from LLM gateway logs are computed exactly like this; with tens of gigabytes,
        the same loop runs per file in parallel (14.3) and the summaries are merged."""),
    write("Round-trip rich types with tags", "hard", tag="Data work",
        prompt="""Write `dumps_tagged(obj)` and `loads_tagged(text)` so that `datetime`, `date`, `Decimal`, `set` and `complex` values survive a JSON round trip. Encode
        each as an object `{"__type__": name, "value": ...}` with names `"datetime"`, `"date"` (ISO strings), `"decimal"` (string), `"set"` (a sorted list)
        and `"complex"` (`[real, imag]`). When decoding, convert objects that have exactly the keys `__type__` and `value`; an unknown `__type__` raises
        `ValueError`; other objects are returned unchanged.""",
        code="""
        import json
        from datetime import date, datetime
        from decimal import Decimal

        def dumps_tagged(obj):
            pass

        def loads_tagged(text):
            pass
        """,
        tests="""
        from datetime import date, datetime
        from decimal import Decimal
        data = {"run": "exp-1", "started": datetime(2025, 3, 1, 9, 30, 15), "day": date(2025, 3, 1), "cost": Decimal("0.10"),
                "labels": {"spam", "ham"}, "z": 1 + 2j, "nested": [{"when": date(2024, 12, 31)}]}
        text = dumps_tagged(data)
        back = loads_tagged(text)
        assert back == data and type(back["started"]) is datetime and type(back["day"]) is date
        assert '{"__type__": "date", "value": "2025-03-01"}' in text and '"value": ["ham", "spam"]' in text
        assert loads_tagged('{"__type__": "note", "value": 1, "extra": true}') == {"__type__": "note", "value": 1, "extra": True}
        assert loads_tagged(dumps_tagged((1, 2))) == [1, 2]
        try:
            loads_tagged('{"__type__": "bytes", "value": "AA=="}')
            assert False
        except ValueError:
            pass
        """,
        hints=["Check `datetime` before `date`: a `datetime` is an instance of `date` too.",
               "`json.loads(text, object_hook=...)` calls the hook for every object, innermost first."],
        solution="""
        import json
        from datetime import date, datetime
        from decimal import Decimal


        def _encode(o):
            if isinstance(o, datetime):
                return {"__type__": "datetime", "value": o.isoformat()}
            if isinstance(o, date):
                return {"__type__": "date", "value": o.isoformat()}
            if isinstance(o, Decimal):
                return {"__type__": "decimal", "value": str(o)}
            if isinstance(o, set):
                return {"__type__": "set", "value": sorted(o)}
            if isinstance(o, complex):
                return {"__type__": "complex", "value": [o.real, o.imag]}
            raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")


        _DECODERS = {
            "datetime": datetime.fromisoformat,
            "date": date.fromisoformat,
            "decimal": Decimal,
            "set": set,
            "complex": lambda v: complex(v[0], v[1]),
        }


        def _decode(d):
            if set(d) == {"__type__", "value"}:
                kind = d["__type__"]
                if kind not in _DECODERS:
                    raise ValueError(f"unknown __type__: {kind!r}")
                return _DECODERS[kind](d["value"])
            return d


        def dumps_tagged(obj):
            return json.dumps(obj, default=_encode)


        def loads_tagged(text):
            return json.loads(text, object_hook=_decode)
        """,
        why="""`default` and `object_hook` are the two halves of a custom format: the encoder replaces each unknown object with a tagged plain object, and the decoder sees every
        decoded object (innermost first, so nested values are already converted) and turns tags back into rich types. Checking `datetime` before `date` matters
        because `datetime` is a subclass of `date`; the other order would silently drop the time. Requiring exactly the two keys avoids misreading ordinary
        data that happens to contain a `__type__` field, and unknown tags fail loudly. The tuple shows the limit: JSON already "handles" tuples as arrays, so
        `default` is never called and they come back as lists. Serialisation libraries (and job queues such as Celery and Kombu) use this same tagging trick."""),
    fix("Read the code: an evaluation export", "hard", tag="GenAI",
        prompt="""`export_results` writes evaluation results to CSV for a spreadsheet review. Answers often contain commas, quotes and newlines, which break the columns;
        there is no header; the file is written without an explicit encoding, and the scores are rounded to 2 places. Rewrite it with the `csv` module: a
        header `id,answer,score`, one row per result in order, the score formatted with 3 decimals (`0.900`), extra keys ignored, UTF-8 and the correct
        `newline` argument.""",
        code="""
        def export_results(path, results):
            with open(path, "w") as f:
                for r in results:
                    f.write(str(r["id"]) + "," + r["answer"] + "," + str(round(r["score"], 2)) + "\\n")
        """,
        tests="""
        import csv, os, tempfile
        path = os.path.join(tempfile.mkdtemp(), "review.csv")
        results = [{"id": 1, "answer": "Refunds take 5 days, usually.", "score": 0.9, "latency_ms": 812},
                   {"id": 2, "answer": 'She said "no"\\nand left.', "score": 0.12345},
                   {"id": 3, "answer": "Café opens at 9", "score": 1}]
        export_results(path, results)
        with open(path, encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        assert rows == [{"id": "1", "answer": "Refunds take 5 days, usually.", "score": "0.900"},
                        {"id": "2", "answer": 'She said "no"\\nand left.', "score": "0.123"},
                        {"id": "3", "answer": "Café opens at 9", "score": "1.000"}]
        assert open(path, "rb").read().startswith(b"id,answer,score\\r\\n")
        """,
        hints=["`csv.DictWriter(f, fieldnames=[\"id\", \"answer\", \"score\"], extrasaction=\"ignore\")` on a file opened with `encoding=\"utf-8\", newline=\"\"`.",
               "Build each row as a new dict with the formatted score: `{**r, \"score\": f\"{r['score']:.3f}\"}`."],
        solution="""
        import csv

        FIELDS = ["id", "answer", "score"]


        def export_results(path, results):
            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
                writer.writeheader()
                for r in results:
                    writer.writerow({**r, "score": f"{r['score']:.3f}"})
        """,
        why="""Joining fields with `","` is the original CSV sin: the first answer's comma creates a fourth column and the second answer's newline starts a new row, so the
        spreadsheet is garbage. `DictWriter` quotes exactly the fields that need it and doubles inner quotes. `newline=""` is required so the writer's own
        `\\r\\n` row endings are not translated, and so newlines inside quoted fields are written as they are. A fixed format such as `.3f` gives aligned,
        comparable scores, where `round` produces `0.9` and `1`. Copying each row with `{**r, ...}` formats the score without changing the caller's results,
        and `extrasaction="ignore"` drops the latency column on purpose."""),
    predict("JSON edge cases", "hard",
        code="""
        import json

        print(json.loads('{"a": 1, "a": 2}'), json.loads("12345678901234567890123") + 1)
        print(json.loads("1e400"), json.dumps(0.1 + 0.2), json.loads('"caf\\\\u00e9"'))
        print(json.dumps({1: "a", None: "c", 2.5: "d"}))
        try:
            json.dumps({(1, 2): "pair"})
        except TypeError as e:
            print("TypeError:", e)
        print(json.loads("[1, 2.0, true, null]"), json.dumps({"s": "line\\nbreak"}))
        """,
        hints=["Duplicate keys: the last one wins. Python ints have unlimited size. Keys may be str, int, float, bool or None; anything else is an error."],
        why="""JSON allows duplicate keys and Python keeps the last, silently, which can hide a bug in a generated document. Python parses big integers exactly (JavaScript
        would round this one, the reason APIs send large ids as strings). A number too large for a float becomes infinity; floats are written with the
        shortest repr that round-trips, so `0.1 + 0.2` shows its binary error; and `\\u00e9` escapes decode to `é`. `int`, `None` and `float` keys are
        converted to strings, but a tuple key raises `TypeError` even though tuples are valid values. Finally, a newline inside a string is written as the
        escape `\\n`, which is why one record always fits on one line in JSONL."""),
)

section("interview", "Interview questions",
    explain("CSV, JSON, JSON Lines or Parquet: how do you choose a format?", "medium", tag="Interview",
        why="""**CSV** is for flat tables exchanged with people and spreadsheet tools: universal, but untyped (everything is a string), ambiguous in encoding and dialect, and
        unable to hold nested data. **JSON** suits nested records, configuration and API payloads, with basic types, but a single document must be parsed
        whole. **JSON Lines** keeps JSON's flexibility while streaming: one record per line, appendable, splittable and robust to a truncated last line,
        which is why datasets, fine-tuning files, LLM batch jobs and logs use it. **Parquet** is a typed, compressed, **columnar** binary format for large
        analytical tables: reading two columns of a billion rows reads only those columns, with types preserved, which makes it the default for data lakes and
        feature tables (pandas, Polars, Spark, DuckDB). Rule of thumb: Parquet for analytics at scale, JSONL for record streams and ML/LLM data, JSON for
        configs and APIs, CSV only at the human or legacy boundary."""),
    explain("What can go wrong when data round-trips through JSON?", "medium", tag="Interview",
        why="""Types are lost or changed: tuples become lists, integer dict keys become strings, sets, dates, `Decimal`, bytes and NumPy values cannot be serialised
        without a `default`, and floats that were `Decimal` lose exactness. Numbers have edge cases: Python writes `NaN` and `Infinity`, which are not valid JSON
        and are rejected elsewhere (use `allow_nan=False`); integers beyond `2**53` are exact in Python but rounded in JavaScript, so large ids should travel as
        strings. Duplicate keys are silently resolved by keeping the last. Encoding matters: `ensure_ascii=True` escapes everything, `False` requires the file
        to be UTF-8. And structure is not validated, so a parsed value can be an array where you expected an object; validate it with a schema or Pydantic
        model (11.4) at the boundary."""),
    explain("An ingestion job reads millions of JSONL records and some are malformed. How do you handle them?", "hard", tag="Interview",
        why="""Stream the file line by line so memory stays constant, and separate the **policy** from the parsing. Parse each line inside `try`, then validate its shape (an
        object, required fields, types, ideally a Pydantic model). Bad records should not crash the job at hour three, but they must not disappear either:
        count them, log the line number, file and error type (not the full content if it may hold personal data), and write the raw line to a dead-letter or
        quarantine file so it can be inspected and replayed after a fix. Define a threshold: if more than, say, 0.1% of records are bad, fail the run, because
        that signals an upstream schema change rather than noise. Make the job idempotent and resumable (record the last committed offset or batch, write
        outputs atomically), and report the counts (read, good, bad, by error type) as metrics, so a jump is visible on a dashboard."""),
)

recap(
    "Use the `csv` module, never `split(\",\")`; open files with `newline=\"\"`, convert types yourself, and use `utf-8-sig` for files from Excel.",
    "`DictReader` and `DictWriter` map rows to dicts; call `writeheader()`, and set `extrasaction` deliberately.",
    "JSON loses types: tuples become lists, keys become strings; `NaN` is not valid JSON, so clean it and pass `allow_nan=False`.",
    "`default=` serialises unknown types (dates, Decimal, NumPy) and `object_hook=` decodes them; neither applies to types JSON already handles.",
    "JSON Lines streams one record per line: write without `indent`, read line by line, and report bad lines with their numbers.",
)
