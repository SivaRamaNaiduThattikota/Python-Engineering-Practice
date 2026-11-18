from lesson import *

lesson(
    id="m12-p", num="12.P", title="Module 12 practice set and mini project",
    intro="Mixed problems from all of Module 12: paths and files, CSV, JSON and JSON Lines, logging, and configuration. Then a "
          "mini project that needs all of it: a document ingestion job configured from TOML and the environment that walks a "
          "corpus, skips and deduplicates files, writes JSONL chunks and a manifest atomically, and logs what it did.",
    desc="Mixed problems from the whole module, then one small program that uses all of it.",
    keys="practice mixed review project ingestion job corpus chunks manifest atomic jsonl csv logging configuration toml environment dedupe sha256 rotate metrics prompts",
)

section("how", "How to use this page",
    p("""Every file-handling task raises the same four questions. **Where is it?** Build paths with `pathlib`, find files with explicit filters, and never trust
    that a folder exists (12.1). **What format, and what types?** CSV gives strings, JSON loses some types, JSONL streams, and every reader must decide what
    a bad record means (12.2). **What happens if it fails halfway?** Write atomically, log the failure with its traceback once, and keep going or stop
    deliberately (12.1, 12.3). **Who decides the settings?** Defaults, a file and the environment, parsed strictly at start-up, with secrets kept out of
    code and logs (12.4)."""),
    p("""The problems mix the lessons on purpose, and the mini project combines all four in the kind of batch job that feeds every RAG system."""),
)

section("set", "Practice set",
    predict("Paths, JSON and files together", "easy",
        code="""
        import json, tempfile
        from pathlib import Path

        root = Path(tempfile.mkdtemp())
        cfg = root / "configs" / "run.json"
        cfg.parent.mkdir(parents=True)
        n = cfg.write_text(json.dumps({"lr": 3e-4, "layers": (2, 4)}, indent=1), encoding="utf-8")
        print(n, cfg.read_text(encoding="utf-8").count("\\n"))
        with cfg.open(encoding="utf-8") as f:
            data = json.load(f)
        print(data, cfg.with_suffix(".bak").name, cfg.relative_to(root).as_posix())
        print(sorted(p.name for p in root.rglob("*")), cfg.stat().st_size == n)
        """,
        hints=["`write_text` returns the number of characters written. `indent=1` puts each value on its own line. JSON turns tuples into lists."],
        why="""With `indent=1`, the JSON spreads over seven lines (each list item gets its own), so it contains six newlines; `write_text` returns its character count, which equals the byte size here
        because the text is ASCII. Loading it back gives a list where the tuple was. `rglob("*")` yields folders as well as files, so `configs` is listed too."""),
    write("Append metrics and find the best run", "easy", tag="ML",
        prompt="""Write `append_metrics(path, run, metrics)` appending one JSONL line `{"run": run, **metrics}` to `path` (creating parent folders), and `best_run(path,
        metric)` streaming the file and returning `(run, value)` for the highest value of `metric`, skipping blank lines, invalid JSON and records without a
        numeric `metric` (booleans do not count). Return `None` if no record qualifies.""",
        code="""
        import json
        from pathlib import Path

        def append_metrics(path, run, metrics):
            pass

        def best_run(path, metric):
            pass
        """,
        tests="""
        import tempfile
        from pathlib import Path
        path = Path(tempfile.mkdtemp()) / "exp" / "metrics.jsonl"
        append_metrics(path, "r1", {"f1": 0.81, "loss": 0.4})
        append_metrics(path, "r2", {"f1": 0.87})
        with open(path, "a", encoding="utf-8") as f:
            f.write("\\n{broken\\n" + '{"run": "r3", "f1": "0.99"}\\n' + '{"run": "r4", "f1": true}\\n')
        append_metrics(path, "r5", {"f1": 0.84, "loss": 0.2})
        assert best_run(path, "f1") == ("r2", 0.87) and best_run(path, "loss") == ("r1", 0.4)
        assert best_run(path, "auc") is None and path.read_text(encoding="utf-8").splitlines()[0] == '{"run": "r1", "f1": 0.81, "loss": 0.4}'
        """,
        hints=["`path.parent.mkdir(parents=True, exist_ok=True)`, then open with `\"a\"`.",
               "Check `isinstance(v, (int, float)) and not isinstance(v, bool)`."],
        solution="""
        import json
        from pathlib import Path


        def append_metrics(path, run, metrics):
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"run": run, **metrics}) + "\\n")


        def best_run(path, metric):
            best = None
            with open(path, encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    value = record.get(metric) if isinstance(record, dict) else None
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        if best is None or value > best[1]:
                            best = (record.get("run"), value)
            return best
        """,
        why="""Appending one JSON line per run is the simplest durable experiment log: concurrent-safe enough for one writer, readable after a crash, and greppable. Reading
        it is a streaming scan with explicit tolerance for the junk that accumulates in such files (a broken line, a metric written as a string, a boolean,
        which Python counts as an `int`). The `"loss"` query shows the function is generic, though for a loss you would want the minimum; a real tracker
        (MLflow, Weights & Biases) stores a direction per metric."""),
    fix("A log level from the environment", "easy", tag="GenAI",
        prompt="""`configure` sets the service's log level from `LOG_LEVEL`. Operators write `LOG_LEVEL=debug`, which crashes start-up with `ValueError: Unknown level:
        'debug'`, and a missing variable should mean `INFO`. Accept any case and surrounding spaces, default to `INFO`, and keep rejecting unknown names.""",
        code="""
        import logging

        def configure(logger, environ):
            logger.setLevel(environ.get("LOG_LEVEL"))
            return logger.level
        """,
        tests="""
        import logging
        log = logging.getLogger("f3.svc")
        assert configure(log, {"LOG_LEVEL": " debug "}) == logging.DEBUG and configure(log, {}) == logging.INFO
        assert configure(log, {"LOG_LEVEL": "Warning"}) == logging.WARNING and configure(log, {"LOG_LEVEL": ""}) == logging.INFO
        try:
            configure(log, {"LOG_LEVEL": "loud"})
            assert False
        except ValueError:
            pass
        """,
        hints=["`(environ.get(\"LOG_LEVEL\") or \"INFO\").strip().upper()`, and treat a value that is empty after stripping as `INFO`."],
        solution="""
        import logging

        def configure(logger, environ):
            level = (environ.get("LOG_LEVEL") or "").strip().upper() or "INFO"
            logger.setLevel(level)
            return logger.level
        """,
        why="""`setLevel` accepts level names, but only in upper case, and `setLevel(None)` fails too, so the setting needs the same normalisation as any other environment
        variable (12.4): strip, normalise case, apply a default for missing or empty. Unknown names still raise `ValueError`, which is what you want at start-up:
        a typo in `LOG_LEVEL` should stop the deploy, not silently log at the wrong level."""),
    predict("Lists in CSV cells", "medium",
        code="""
        import csv, io, json

        rows = [{"id": 1, "tags": ["billing", "eu"]}, {"id": 2, "tags": []}]
        buf = io.StringIO(newline="")
        w = csv.DictWriter(buf, fieldnames=["id", "tags", "tags_json"])
        w.writeheader()
        for r in rows:
            w.writerow({**r, "tags_json": json.dumps(r["tags"])})
        print(buf.getvalue().splitlines())
        back = list(csv.DictReader(io.StringIO(buf.getvalue(), newline="")))
        print(back[0]["tags"], type(back[0]["tags"]).__name__, json.loads(back[0]["tags_json"]))
        """,
        hints=["CSV writes every value with `str`, so a list is written as its Python repr. JSON text contains quotes and commas, so the cell is quoted."],
        why="""CSV has no lists: the writer calls `str` on the list and stores its Python repr, which another tool cannot parse reliably and which reads back as a plain
        string. Encoding the list as JSON gives a cell that any language can decode; because JSON uses double quotes and commas, the writer wraps it in quotes and
        doubles the inner quotes, and the reader undoes that. For nested data, JSONL or Parquet is usually the better format than CSV with JSON cells."""),
    write("Load prompt templates from TOML files", "medium", tag="GenAI",
        prompt="""Write `load_prompts(folder, logger)` reading every `*.toml` file in `folder` (not subfolders), in name order. Each must have a string `name`, a string
        `template` and a list of strings `variables`. Return a dict from name to `{"template": ..., "variables": [...], "file": file name}`. Skip a file that
        cannot be parsed or is invalid, logging a warning `"skipping %s: %s"` with the file name and the reason, and skip a duplicate name with a warning
        `"duplicate prompt %r in %s"`.""",
        code="""
        import tomllib
        from pathlib import Path

        def load_prompts(folder, logger):
            pass
        """,
        tests="""
        import logging, tempfile
        from pathlib import Path
        class ListHandler(logging.Handler):
            def __init__(self):
                super().__init__()
                self.records = []
            def emit(self, record):
                self.records.append(record)
        cap = ListHandler()
        log = logging.getLogger("w5.prompts")
        log.handlers[:] = [cap]
        log.setLevel(logging.INFO)
        log.propagate = False
        d = Path(tempfile.mkdtemp())
        files = {"a_qa.toml": 'name = "qa"\\ntemplate = "Answer {question} using {context}."\\nvariables = ["question", "context"]\\n',
                 "b_broken.toml": 'name = "x"\\ntemplate = "unclosed\\n',
                 "c_missing.toml": 'name = "summary"\\ntemplate = "Summarise {text}"\\n',
                 "d_dup.toml": 'name = "qa"\\ntemplate = "Other"\\nvariables = []\\n',
                 "e_tone.toml": 'name = "tone"\\ntemplate = "Rewrite politely: {text}"\\nvariables = ["text"]\\n',
                 "notes.txt": "not a prompt"}
        for name, text in files.items():
            (d / name).write_text(text, encoding="utf-8")
        (d / "old").mkdir()
        (d / "old" / "z.toml").write_text('name = "old"\\ntemplate = "x"\\nvariables = []\\n', encoding="utf-8")
        prompts = load_prompts(d, log)
        assert list(prompts) == ["qa", "tone"] and prompts["qa"] == {"template": "Answer {question} using {context}.", "variables": ["question", "context"], "file": "a_qa.toml"}
        msgs = [r.getMessage() for r in cap.records]
        assert [r.levelname for r in cap.records] == ["WARNING"] * 3 and msgs[0].startswith("skipping b_broken.toml: ")
        assert msgs[1].startswith("skipping c_missing.toml: ") and msgs[2] == "duplicate prompt 'qa' in d_dup.toml"
        """,
        hints=["`sorted(Path(folder).glob(\"*.toml\"))`; open each in binary mode for `tomllib.load`, or use `tomllib.loads(path.read_text(...))`.",
               "Validate with a small function that raises `ValueError(\"...\")`; `TOMLDecodeError` is a `ValueError` too, so one `except ValueError` handles both."],
        solution="""
        import tomllib
        from pathlib import Path


        def _validate(data):
            if not isinstance(data.get("name"), str) or not data["name"]:
                raise ValueError("missing name")
            if not isinstance(data.get("template"), str):
                raise ValueError("missing template")
            variables = data.get("variables")
            if not isinstance(variables, list) or not all(isinstance(v, str) for v in variables):
                raise ValueError("variables must be a list of strings")


        def load_prompts(folder, logger):
            prompts = {}
            for path in sorted(Path(folder).glob("*.toml")):
                try:
                    with open(path, "rb") as f:
                        data = tomllib.load(f)
                    _validate(data)
                except ValueError as e:
                    logger.warning("skipping %s: %s", path.name, e)
                    continue
                if data["name"] in prompts:
                    logger.warning("duplicate prompt %r in %s", data["name"], path.name)
                    continue
                prompts[data["name"]] = {"template": data["template"], "variables": data["variables"], "file": path.name}
            return prompts
        """,
        why="""Prompts kept as files outside the code can be reviewed, diffed and changed without a deploy, and TOML handles multi-line templates well. The loader combines the
        module: `glob` (not `rglob`) for one folder and `sorted` for a deterministic order (12.1), `tomllib.load` on a **binary** file (12.4), validation of
        the parsed data, and warnings with lazy arguments (12.3). Because `TOMLDecodeError` subclasses `ValueError`, syntax errors and validation errors share
        one handler. Whether a bad prompt file should be a warning or a start-up failure is a policy choice; failing hard is safer when the missing prompt would
        break a feature."""),
    fix("Rewriting a file while reading it", "medium", tag="Data work",
        prompt="""`compact(path)` should rewrite a JSONL file keeping only the **last** record for each `id`, in order of first appearance, and return how many it kept. It
        returns 0 and leaves an empty file. Fix it so it works, and make the rewrite atomic so a crash cannot lose the data.""",
        code="""
        import json, os

        def compact(path):
            latest = {}
            with open(path, encoding="utf-8") as src, open(path, "w", encoding="utf-8") as dst:
                for line in src:
                    record = json.loads(line)
                    latest[record["id"]] = record
                for record in latest.values():
                    dst.write(json.dumps(record) + "\\n")
            return len(latest)
        """,
        tests="""
        import json, os, tempfile
        d = tempfile.mkdtemp()
        path = os.path.join(d, "docs.jsonl")
        records = [{"id": "a", "v": 1}, {"id": "b", "v": 1}, {"id": "a", "v": 2}, {"id": "c", "v": 1}, {"id": "b", "v": 3}]
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(json.dumps(r) + "\\n" for r in records)
        assert compact(path) == 3
        with open(path, encoding="utf-8") as f:
            assert [json.loads(line) for line in f] == [{"id": "a", "v": 2}, {"id": "b", "v": 3}, {"id": "c", "v": 1}]
        assert sorted(os.listdir(d)) == ["docs.jsonl"]
        """,
        hints=["Opening with `\"w\"` truncates the file before the first line is read. Read everything into `latest` first, then write a temporary file and `os.replace` it."],
        solution="""
        import json, os

        def compact(path):
            latest = {}
            with open(path, encoding="utf-8") as src:
                for line in src:
                    if line.strip():
                        record = json.loads(line)
                        latest[record["id"]] = record
            tmp = path + ".tmp"
            try:
                with open(tmp, "w", encoding="utf-8") as dst:
                    for record in latest.values():
                        dst.write(json.dumps(record) + "\\n")
                os.replace(tmp, path)
            except BaseException:
                if os.path.exists(tmp):
                    os.remove(tmp)
                raise
            return len(latest)
        """,
        why="""Both `open` calls run before the loop, and `"w"` empties the file at once, so the reader found nothing: the data was destroyed by the attempt to rewrite it.
        Reading into memory first and writing to a temporary file that replaces the original (12.1) fixes both the logic and the crash-safety. Assigning to an
        existing dict key keeps its original position while updating the value, which gives "last record, in order of first appearance" for free. For files
        too large for memory, the same job writes the compacted output to a new file in a second streaming pass, or uses a database."""),
    choose("json.dump to a file, or one write", "medium", tag="Data work",
        prompt="Both write the same 2,000-record payload to an open text file. Which is faster?",
        setup="""import io, json
payload = [{"id": i, "text": "refund policy " * 5, "score": i / 2_000, "tags": ["faq", "eu"]} for i in range(2_000)]""",
        options={
            "a": "f = io.StringIO()\njson.dump(payload, f)",
            "b": "f = io.StringIO()\nf.write(json.dumps(payload))",
        },
        answer="b",
        hints=["`json.dump` writes each piece as the encoder produces it; `json.dumps` builds the whole string in C first."],
        why="""`json.dump` streams: it walks the data and calls `f.write` for every small chunk the encoder produces (each key, value and separator), so the cost is
        dominated by thousands of method calls. `json.dumps` encodes everything in the C accelerator into one string, and a single `write` follows. The
        trade-off is memory: `dumps` holds the whole document as one string, which is fine for megabytes and wasteful for gigabytes, where streaming (or JSONL,
        one `dumps` per record) is the better structure anyway."""),
    write("Rotate log files by size", "hard", tag="Data work",
        prompt="""Write `rotate(path, max_bytes, backups)` that does nothing if `path` does not exist or is at most `max_bytes` bytes. Otherwise it shifts the backups:
        `app.log.{backups-1}` becomes `app.log.{backups}` (replacing it), down to `app.log.1` becoming `app.log.2`, then renames `app.log` to `app.log.1`, and
        returns `True`. With `backups=0` it just deletes the file. Write `log_line(path, line, max_bytes, backups)` that rotates when needed, then appends the
        line and a newline.""",
        code="""
        from pathlib import Path

        def rotate(path, max_bytes, backups):
            pass

        def log_line(path, line, max_bytes, backups):
            pass
        """,
        tests="""
        import tempfile
        from pathlib import Path
        d = Path(tempfile.mkdtemp())
        log = d / "app.log"
        assert rotate(log, 10, 2) is False
        for i in range(7):
            log_line(log, f"event {i}", max_bytes=16, backups=2)
        assert sorted(p.name for p in d.iterdir()) == ["app.log", "app.log.1", "app.log.2"]
        assert log.read_text(encoding="utf-8") == "event 6\\n"
        assert (d / "app.log.1").read_text(encoding="utf-8") == "event 3\\nevent 4\\nevent 5\\n" and (d / "app.log.2").read_text(encoding="utf-8") == "event 0\\nevent 1\\nevent 2\\n"
        small = d / "small.log"
        small.write_text("x" * 20, encoding="utf-8")
        assert rotate(small, 10, 0) is True and not small.exists()
        """,
        hints=["Check the size with `path.stat().st_size`. Shift from the oldest down: `for i in range(backups - 1, 0, -1)`, renaming `.i` to `.i+1` with `replace` when it exists.",
               "`path.with_name(f\"{path.name}.{i}\")` builds the backup names."],
        solution="""
        from pathlib import Path


        def rotate(path, max_bytes, backups):
            path = Path(path)
            if not path.exists() or path.stat().st_size <= max_bytes:
                return False
            if backups <= 0:
                path.unlink()
                return True
            for i in range(backups - 1, 0, -1):
                older = path.with_name(f"{path.name}.{i}")
                if older.exists():
                    older.replace(path.with_name(f"{path.name}.{i + 1}"))
            path.replace(path.with_name(f"{path.name}.1"))
            return True


        def log_line(path, line, max_bytes, backups):
            rotate(path, max_bytes, backups)
            with open(path, "a", encoding="utf-8") as f:
                f.write(line + "\\n")
        """,
        why="""Each event line is 8 bytes, so the file passes 16 bytes with its third line and is rotated before the fourth write, which is why each backup holds three
        complete events. Shifting must start with the **oldest** backup, or renaming `.1` to `.2` would overwrite `.2` before it moved on; `replace` overwrites the last
        backup, which is how old logs fall off the end. This is what `logging.handlers.RotatingFileHandler(path, maxBytes=..., backupCount=...)` does for you,
        and why services rotate logs at all: unbounded log files fill disks, which takes down far more than logging."""),
    fix("Read the code: a nightly metrics export", "hard", tag="ML",
        prompt="""`export_metrics` reads per-run metric files (`*.json` anywhere under `runs_dir`) and writes a CSV summary. Problems found in review: it prints instead of
        logging, so failures are invisible in production; one broken JSON file crashes the whole export; the CSV is written with hand-joined strings and no
        header; `EXPORT_DECIMALS` from the environment is used as a string; and a crash halfway leaves a truncated CSV that the dashboard then reads. Fix it:
        log a warning per unreadable file and skip it, write `run,f1,loss` with the `csv` module, format numbers with the configured decimals (default 3, read at
        call time), write atomically, and return the number of rows.""",
        code="""
        import json, os
        from pathlib import Path


        def export_metrics(runs_dir, out_path, logger):
            decimals = os.getenv("EXPORT_DECIMALS", 3)
            rows = []
            for path in Path(runs_dir).glob("*.json"):
                data = json.loads(path.read_text())
                rows.append((path.stem, data["f1"], data["loss"]))
            print(f"exporting {len(rows)} runs")
            with open(out_path, "w") as f:
                for run, f1, loss in rows:
                    f.write(f"{run},{round(f1, decimals)},{round(loss, decimals)}\\n")
            return len(rows)
        """,
        tests="""
        import csv, json, logging, os, tempfile
        from pathlib import Path
        class ListHandler(logging.Handler):
            def __init__(self):
                super().__init__()
                self.records = []
            def emit(self, record):
                self.records.append(record)
        cap = ListHandler()
        log = logging.getLogger("f9.export")
        log.handlers[:] = [cap]
        log.setLevel(logging.INFO)
        log.propagate = False
        root = Path(tempfile.mkdtemp())
        runs = root / "runs"
        (runs / "2025").mkdir(parents=True)
        (runs / "r1.json").write_text(json.dumps({"f1": 0.81234, "loss": 0.4}), encoding="utf-8")
        (runs / "2025" / "r2.json").write_text(json.dumps({"f1": 0.9, "loss": 0.123456}), encoding="utf-8")
        (runs / "2025" / "r3.json").write_text("{broken", encoding="utf-8")
        (runs / "r4.json").write_text(json.dumps({"f1": 0.5}), encoding="utf-8")
        out = root / "report" / "metrics.csv"
        os.environ["EXPORT_DECIMALS"] = "2"
        assert export_metrics(runs, out, log) == 2
        os.environ.pop("EXPORT_DECIMALS")
        with open(out, encoding="utf-8", newline="") as f:
            assert list(csv.reader(f)) == [["run", "f1", "loss"], ["r1", "0.81", "0.40"], ["r2", "0.90", "0.12"]]
        warnings = sorted(r.getMessage() for r in cap.records if r.levelname == "WARNING")
        assert len(warnings) == 2 and warnings[0].startswith("skipping r3.json") and warnings[1].startswith("skipping r4.json")
        assert export_metrics(runs, out, log) == 2 and open(out, encoding="utf-8").read().splitlines()[1] == "r1,0.812,0.400"
        assert sorted(p.name for p in out.parent.iterdir()) == ["metrics.csv"]
        """,
        hints=["`rglob(\"*.json\")` sorted by stem; wrap each file's parsing in `try` and catch `(json.JSONDecodeError, KeyError, TypeError)`.",
               "Format with `f\"{value:.{decimals}f}\"`; write to `out.with_name(out.name + \".tmp\")` with `newline=\"\"`, then `os.replace`. Create the folder first."],
        solution="""
        import csv, json, os
        from pathlib import Path


        def export_metrics(runs_dir, out_path, logger):
            decimals = int(os.environ.get("EXPORT_DECIMALS", "3"))
            rows = []
            for path in sorted(Path(runs_dir).rglob("*.json"), key=lambda p: p.stem):
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    rows.append((path.stem, float(data["f1"]), float(data["loss"])))
                except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
                    logger.warning("skipping %s: %s: %s", path.name, type(e).__name__, e)
            logger.info("exporting %d runs", len(rows))
            out = Path(out_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            tmp = out.with_name(out.name + ".tmp")
            try:
                with open(tmp, "w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["run", "f1", "loss"])
                    for run, f1, loss in rows:
                        writer.writerow([run, f"{f1:.{decimals}f}", f"{loss:.{decimals}f}"])
                os.replace(tmp, out)
            except BaseException:
                tmp.unlink(missing_ok=True)
                raise
            return len(rows)
        """,
        why="""The fix touches every lesson of the module. Files: `rglob` finds runs in subfolders, sorting makes the report stable, the output folder is created, and the
        temporary file plus `os.replace` means the dashboard always reads a complete CSV, old or new (12.1). Formats: the `csv` writer with a header and
        `newline=""` replaces string joining, and fixed-decimal formatting replaces `round`, which prints `0.4` instead of `0.40` (12.2). Logging: one warning
        per skipped file with the reason, instead of a crash or a `print` nobody sees (12.3). Configuration: the environment value is parsed as an int when the
        function runs, not used as the string `"2"`, which would make `round` fail (12.4)."""),
    predict("Structured logs to a file", "hard",
        code="""
        import json, logging, tempfile
        from pathlib import Path

        class JsonLines(logging.Formatter):
            def format(self, record):
                return json.dumps({"level": record.levelname, "msg": record.getMessage(), "file": getattr(record, "file", None)})

        path = Path(tempfile.mkdtemp()) / "logs" / "ingest.jsonl"
        path.parent.mkdir()
        handler = logging.FileHandler(path, encoding="utf-8")
        handler.setFormatter(JsonLines())
        log = logging.getLogger("p11.ingest")
        log.handlers[:] = [handler]
        log.setLevel(logging.INFO)
        log.propagate = False
        log.info("started")
        log.warning("skipped %s", "a.pdf", extra={"file": "a.pdf"})
        log.debug("details")
        print(path.read_text(encoding="utf-8").count("\\n"), handler.terminator == "\\n")
        handler.close()
        records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        print(records)
        """,
        hints=["A `FileHandler` writes each formatted record followed by its `terminator`; the debug record is below the logger's level."],
        why="""The handler appends each record's formatted text plus a newline, and flushes after every record, so the file already holds two complete lines before it is closed:
        one JSON object per line, which makes the log file itself a JSONL file. The debug record never reaches the handler. `extra` fields become record
        attributes, so the formatter finds `file` on the warning and falls back to `None` on the other record."""),
    explain("Walk through how you would design a batch job that turns a folder of documents into chunks for a vector index.", "medium", tag="Interview",
        why="""Configuration first: source and output locations, file types, chunk size and overlap, read from a TOML file with environment overrides and validated at start-up
        (12.4). Discovery: walk the tree with explicit filters (types, hidden and vendor folders), sorted for reproducibility, and read each file with an explicit
        encoding, treating undecodable or empty files as skipped, not fatal (12.1). Identity: give every document a stable id (its relative path) and a content
        hash, so unchanged documents can be skipped on the next run and duplicates detected. Output: stream chunks to a JSONL file with the document id, chunk
        number and hash, written to a temporary file and atomically replaced, plus a manifest with counts, skipped and duplicate files and the configuration used
        (12.2). Observability: log one line per skipped file with the reason and a summary at the end, structured so it can be charted (12.3). Then embedding and
        upserting read the JSONL, which also makes those steps restartable without redoing the parsing."""),
    explain("Your batch job runs fine locally but produces different output in production. How do you investigate?", "hard", tag="Interview",
        why="""Start with the inputs the code does not control. **Configuration**: print or log the effective settings at start-up with their sources (masking secrets), and
        compare; a different environment variable, a stale `.env`, or a default used because a variable was misspelt is the commonest cause. **Data**: compare
        file lists and content hashes, since a different checkout, mounted folder or `rglob` order (unsorted) can change results. **Encodings and locale**: a
        missing `encoding=` uses the platform default, so the same file decodes differently on Windows and in a Linux container; line endings and BOMs differ
        too. **Versions**: pin and compare dependency versions and the Python version. **Time and randomness**: time zones, the current date, and unseeded random
        generators. Make the job reproducible by design: explicit encodings, sorted iteration, a manifest that records config, input hashes and versions,
        and structured logs, so the two runs can be diffed instead of guessed at."""),
)

section("project", "Mini project: a document ingestion job",
    p("""A RAG system needs its documents as chunks with stable ids. The nightly ingestion job reads its settings from TOML with environment overrides, walks the
    corpus, skips what is not a document, detects duplicates by content, writes the chunks as JSONL and a manifest describing the run, both atomically, and
    logs what it did. Build it from the pieces of this module."""),
    write("Ingest a corpus into JSONL chunks", "hard", key="ingest-job", tag="Project",
        prompt="""Implement `run_ingest(config_toml, environ, logger)`.

        - **Configuration (12.4):** the TOML has an `[ingest]` table with `source` and `output` (paths), `max_words` (int, default 50) and `suffixes` (default
          `[".md", ".txt"]`). The environment variables `INGEST_OUTPUT` and `INGEST_MAX_WORDS` override them; `INGEST_MAX_WORDS` must be a positive integer,
          otherwise raise `ValueError`.
        - **Discovery (12.1):** every file under `source`, sorted by relative POSIX path, whose suffix (case-insensitive) is in `suffixes` and which is not
          inside a folder starting with `.`.
        - **Reading:** decode as UTF-8; a file that is not valid UTF-8 or is empty after stripping is **skipped**, with a warning `"skipping %s: %s"` (relative
          path and `"not UTF-8"` or `"empty"`).
        - **Duplicates:** a file whose SHA-256 equals an earlier file's is a **duplicate**, logged at `INFO` as `"duplicate %s of %s"`, and not chunked.
        - **Output (12.2):** a JSONL file at `output` (parents created) with one record per chunk of at most `max_words` words: `{"doc": relative path, "chunk":
          k, "sha256": first 12 hex digits, "text": words joined by spaces}`, and a manifest at `output` with the suffix replaced by `.manifest.json`:
          `{"documents": n, "chunks": m, "duplicates": [...], "skipped": [...], "max_words": ...}` with `indent=2`. Both are written atomically; no temporary
          files remain.
        - **Logging (12.3):** a final `INFO` record `"ingest done"` with `extra` fields `documents` and `chunks`.
        - Return the manifest dict.""",
        code="""
        import hashlib, json, os, tomllib
        from pathlib import Path


        def run_ingest(config_toml, environ, logger):
            pass
        """,
        tests="""
        import json, logging, tempfile
        from pathlib import Path
        class ListHandler(logging.Handler):
            def __init__(self):
                super().__init__()
                self.records = []
            def emit(self, record):
                self.records.append(record)
        cap = ListHandler()
        log = logging.getLogger("proj.ingest")
        log.handlers[:] = [cap]
        log.setLevel(logging.INFO)
        log.propagate = False

        root = Path(tempfile.mkdtemp())
        src = root / "corpus"
        docs = {"faq/refunds.md": "Refunds take five business days after we receive the item.",
                "faq/copy-of-refunds.md": "Refunds take five business days after we receive the item.",
                "terms.TXT": "No refunds after thirty days.",
                "notes/empty.md": "   \\n",
                ".git/HEAD.txt": "ref: main",
                "logo.png": "binary"}
        for rel, text in docs.items():
            (src / rel).parent.mkdir(parents=True, exist_ok=True)
            (src / rel).write_text(text, encoding="utf-8")
        (src / "legacy.txt").write_bytes(b"caf\\xe9 menu")
        config = f'''[ingest]\\nsource = '{src.as_posix()}'\\noutput = '{(root / "ignored.jsonl").as_posix()}'\\nmax_words = 50\\n'''
        out = root / "build" / "index" / "chunks.jsonl"
        manifest = run_ingest(config, {"INGEST_OUTPUT": str(out), "INGEST_MAX_WORDS": "4"}, log)

        assert manifest == {"documents": 2, "chunks": 5, "duplicates": ["faq/refunds.md"], "skipped": ["legacy.txt", "notes/empty.md"], "max_words": 4}
        lines = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines()]
        assert [(r["doc"], r["chunk"]) for r in lines] == [("faq/copy-of-refunds.md", 0), ("faq/copy-of-refunds.md", 1), ("faq/copy-of-refunds.md", 2), ("terms.TXT", 0), ("terms.TXT", 1)]
        assert lines[0]["text"] == "Refunds take five business" and lines[2]["text"] == "the item." and len(lines[0]["sha256"]) == 12
        assert json.loads((out.parent / "chunks.manifest.json").read_text(encoding="utf-8")) == manifest
        assert sorted(p.name for p in out.parent.iterdir()) == ["chunks.jsonl", "chunks.manifest.json"] and not (root / "ignored.jsonl").exists()
        msgs = [(r.levelname, r.getMessage()) for r in cap.records]
        assert msgs[:3] == [("INFO", "duplicate faq/refunds.md of faq/copy-of-refunds.md"), ("WARNING", "skipping legacy.txt: not UTF-8"), ("WARNING", "skipping notes/empty.md: empty")]
        assert msgs[-1] == ("INFO", "ingest done") and (cap.records[-1].documents, cap.records[-1].chunks) == (2, 5)

        default_out = root / "default.jsonl"
        cfg2 = f'''[ingest]\\nsource = '{src.as_posix()}'\\noutput = '{default_out.as_posix()}'\\n'''
        assert run_ingest(cfg2, {}, log)["max_words"] == 50 and default_out.exists()
        for bad in ["0", "ten", "-3"]:
            try:
                run_ingest(cfg2, {"INGEST_MAX_WORDS": bad}, log)
                assert False, bad
            except ValueError:
                pass
        """,
        hints=["Settings: `tomllib.loads(config_toml)[\"ingest\"]`, then `environ.get(...)` overrides; parse `INGEST_MAX_WORDS` with `int` in `try`.",
               "Discovery: `sorted(...)` the matching files by `rel.as_posix()`; read bytes with `read_bytes()`, hash them, then `decode(\"utf-8\")` in `try`.",
               "Atomic writes: a small helper that writes text to `path.with_name(path.name + \".tmp\")` and `os.replace`s it; build the JSONL text as a list of lines."],
        solution="""
        import hashlib, json, os, tomllib
        from pathlib import Path


        def _settings(config_toml, environ):
            cfg = tomllib.loads(config_toml)["ingest"]
            source = Path(cfg["source"])
            output = Path(environ.get("INGEST_OUTPUT") or cfg["output"])
            max_words = cfg.get("max_words", 50)
            raw = environ.get("INGEST_MAX_WORDS", "").strip()
            if raw:
                try:
                    max_words = int(raw)
                except ValueError:
                    raise ValueError(f"INGEST_MAX_WORDS must be an integer, got {raw!r}") from None
            if not isinstance(max_words, int) or max_words <= 0:
                raise ValueError(f"max_words must be a positive integer, got {max_words!r}")
            suffixes = {s.lower() for s in cfg.get("suffixes", [".md", ".txt"])}
            return source, output, max_words, suffixes


        def _discover(source, suffixes):
            found = []
            for path in source.rglob("*"):
                if not path.is_file() or path.suffix.lower() not in suffixes:
                    continue
                rel = path.relative_to(source)
                if any(part.startswith(".") for part in rel.parts[:-1]):
                    continue
                found.append((rel.as_posix(), path))
            return sorted(found)


        def _write_atomic(path, text):
            tmp = path.with_name(path.name + ".tmp")
            try:
                tmp.write_text(text, encoding="utf-8")
                os.replace(tmp, path)
            except BaseException:
                tmp.unlink(missing_ok=True)
                raise


        def run_ingest(config_toml, environ, logger):
            source, output, max_words, suffixes = _settings(config_toml, environ)
            seen, lines, duplicates, skipped = {}, [], [], []
            documents = 0
            for rel, path in _discover(source, suffixes):
                data = path.read_bytes()
                try:
                    text = data.decode("utf-8")
                except UnicodeDecodeError:
                    logger.warning("skipping %s: %s", rel, "not UTF-8")
                    skipped.append(rel)
                    continue
                words = text.split()
                if not words:
                    logger.warning("skipping %s: %s", rel, "empty")
                    skipped.append(rel)
                    continue
                digest = hashlib.sha256(data).hexdigest()
                if digest in seen:
                    logger.info("duplicate %s of %s", rel, seen[digest])
                    duplicates.append(rel)
                    continue
                seen[digest] = rel
                documents += 1
                for k, start in enumerate(range(0, len(words), max_words)):
                    record = {"doc": rel, "chunk": k, "sha256": digest[:12], "text": " ".join(words[start:start + max_words])}
                    lines.append(json.dumps(record, ensure_ascii=False) + "\\n")
            manifest = {"documents": documents, "chunks": len(lines), "duplicates": duplicates, "skipped": skipped, "max_words": max_words}
            output.parent.mkdir(parents=True, exist_ok=True)
            _write_atomic(output, "".join(lines))
            _write_atomic(output.with_suffix(".manifest.json"), json.dumps(manifest, indent=2))
            logger.info("ingest done", extra={"documents": documents, "chunks": len(lines)})
            return manifest
        """,
        why="""Every lesson of the module has a job here:

        - **Paths and files (12.1):** `rglob` with explicit filters for suffix (case-insensitive, so `terms.TXT` counts) and hidden folders, sorting by relative
          path so "first seen" and the output are deterministic, `mkdir(parents=True, exist_ok=True)` for the output folder, and atomic writes so the index
          builder never reads half a file. Reading **bytes** once serves both the hash and the decoding.
        - **Formats (12.2):** chunks are JSONL, one record per line with the metadata a vector index needs, and the manifest is indented JSON for people. The
          duplicate is reported against the file seen first in sorted order, `copy-of-refunds.md`.
        - **Logging (12.3):** each skipped or duplicate file gets one line with lazy arguments, and the summary record carries its numbers as `extra` fields.
        - **Configuration (12.4):** TOML provides the structure, the environment overrides the output location and chunk size, and a bad override fails at
          start-up with a clear message, before any work is done.

        The manifest makes runs comparable: if tonight's run has fewer documents than last night's, the skipped list says why. Production versions add overlap
        between chunks, token-based sizes, incremental runs that skip unchanged hashes, and parallel reading, but keep this structure."""),
)

recap(
    "Build paths with `pathlib`, filter and sort what `rglob` finds, and never assume folders exist.",
    "Rewrite files through a temporary file and `os.replace`; opening the target with `\"w\"` destroys it first.",
    "Pick the format for the data: CSV for flat tables (strings only), JSON for documents, JSONL for record streams, and decide what a bad record means.",
    "Log skips and failures once, with the reason and context, and summarise runs with structured fields.",
    "Read configuration at start-up from defaults, files and the environment, parse it strictly, and keep secrets out of code and logs.",
)
