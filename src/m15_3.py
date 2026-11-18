from lesson import *

lesson(
    id="m15-3", num="15.3", title="Command-line tools",
    intro="Ingestion jobs, evaluation runs, data exports and admin tasks are run from the command line, by people and by schedulers. "
          "`argparse` from the ground up (positional and optional arguments, types, choices, flags, subcommands), the `main(argv)` "
          "pattern that makes tools testable, standard input, output and error, exit codes, configuration precedence, and entry "
          "points that turn a function into a command.",
    desc="`argparse`, entry points and exit codes.",
    keys="argparse argumentparser add_argument positional optional type choices default store_true booleanoptionalaction nargs subparsers set_defaults argumenttypeerror sys.argv main argv exit code systemexit stdin stdout stderr pipes entry points project.scripts console script",
)

term("Command-line interface", "The arguments, options, input and output through which a program is used from a shell, a script or a scheduler.")
term("Exit code", "The integer a process returns when it ends: 0 means success, anything else failure. Shells, CI and schedulers act on it.")
term("Entry point", "A declaration in `pyproject.toml` (`[project.scripts]`) that installs a command which calls a given Python function.")

section("argparse", "argparse basics",
    p("""`sys.argv` is the list of command-line words, starting with the program name. Parsing it by hand breaks on the first unusual input, so use **`argparse`**: create an
    `ArgumentParser(prog=..., description=...)`, declare arguments with `add_argument`, and call `parse_args(argv)`, which returns a namespace object with one attribute
    per argument. **Positional** arguments are required and identified by order (`add_argument("source")`). **Optional** arguments start with dashes (`--out`, short form
    `-o`), are identified by name, and take a `default`. `type=int` (or any function of one string) converts and validates the value, `choices=[...]` restricts it,
    `required=True` makes an option mandatory, `action="store_true"` makes a flag, `nargs="+"` collects one or more values, and `help=` documents it. `argparse` builds
    `--help` from these declarations and prints a usage message and exits with **code 2** on invalid input."""),
    ex("""
    import argparse

    parser = argparse.ArgumentParser(prog="rag-ingest", description="Chunk documents for the vector index.")
    parser.add_argument("source", help="folder with documents")
    parser.add_argument("-o", "--out", default="chunks.jsonl", help="output JSONL file")
    parser.add_argument("--chunk-size", type=int, default=200)
    parser.add_argument("--format", choices=["md", "txt", "all"], default="all")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("-v", "--verbose", action="count", default=0)

    args = parser.parse_args(["docs/", "--chunk-size", "120", "-vv", "--dry-run"])
    print(args)
    print(args.source, args.out, args.chunk_size + 1, args.dry_run, args.verbose)
    try:
        parser.parse_args(["docs/", "--chunk-size", "big"])
    except SystemExit as e:
        print("exit code", e.code)
    """, "argparse_basics.py"),
    p("""Dashes in option names become underscores in attribute names (`chunk_size`). The invalid value made `argparse` print an error message to standard error and raise
    `SystemExit(2)`; in a real terminal the program ends there, and tests can catch it, as here."""),
)

section("main", "The `main(argv)` pattern",
    p("""Structure every tool as a function **`main(argv=None) -> int`**: it builds the parser, parses `argv` (when `argv` is `None`, `parse_args` uses `sys.argv[1:]`), does the
    work, and **returns** an exit code instead of calling `sys.exit` deep inside. The file ends with `if __name__ == "__main__": raise SystemExit(main())`. Tests can then
    call `main(["docs/", "--dry-run"])` and check the return value and output, without a subprocess, and the same function serves as the entry point of an installed
    command. Keep the CLI layer thin: parse arguments, call ordinary functions that do the work (and that other code can import), and translate their results and
    exceptions into output and exit codes."""),
    p("""Exit codes are the CLI's return value to the world: **0** for success, **1** for a general failure, **2** for bad usage (argparse's convention), and other small numbers
    for specific failures if callers need to tell them apart. Shell scripts (`tool && next`), CI pipelines, cron and orchestrators such as Airflow or Kubernetes jobs
    decide what to do from this number, so a tool that prints "error" and exits 0 makes failures invisible. `raise SystemExit("message")` prints the message to standard
    error and exits with 1."""),
)

section("streams", "Standard input, output and error",
    p("""Every process has three streams. **Standard output** is for the program's **result**, so it can be redirected to a file or piped into another program (`rag-ingest docs/
    | jq .`). **Standard error** is for **diagnostics**: progress, warnings, errors and logs (12.3's handlers default to it), which stay visible on the terminal when stdout is
    redirected. **Standard input** lets a tool read data from a pipe (`cat tickets.jsonl | classify --label spam`); by convention a file argument of `-` means "read stdin".
    Mixing logs into stdout corrupts the data for the next program in the pipe. For testability, let `main` accept the streams as parameters with `sys.stdin`, `sys.stdout`
    and `sys.stderr` as defaults, and stream line by line (12.2) so large inputs work."""),
)

section("advanced", "Subcommands, configuration and entry points",
    p("""Tools with several actions (`git commit`, `uv add`) use **subcommands**: `parser.add_subparsers(dest="command", required=True)` returns an object whose `add_parser("ask")`
    creates a parser per subcommand with its own arguments, and `set_defaults(func=handler)` attaches the function to call, so `main` ends with `return args.func(args)`.
    Settings often come from several places; the usual precedence is **defaults < configuration file < environment variables < command-line flags** (12.4), which
    `argparse` supports through `parser.set_defaults(**values_from_config_and_env)` before parsing: explicit flags then override everything else (problem 8)."""),
    p("""To install a command, declare an **entry point** in `pyproject.toml`: `[project.scripts]` with `rag-ingest = "support_rag.cli:main"`. Installing the package (`pip install
    -e .`, `uv sync`) creates a small `rag-ingest` executable that imports `support_rag.cli` and calls `main()`, exiting with its return value. `python -m support_rag` runs a
    package's `__main__.py`, a useful second way in. Third-party libraries such as Click and Typer (which builds the parser from type hints) reduce boilerplate for larger
    tools; the principles (thin CLI layer, exit codes, streams) are the same."""),
)

section("warmup", "Warm-up",
    predict("What argparse produces", "easy",
        code="""
        import argparse, contextlib, io

        p = argparse.ArgumentParser(prog="evalctl")
        p.add_argument("dataset")
        p.add_argument("--model", default="small", choices=["small", "large"])
        p.add_argument("--limit", type=int)
        p.add_argument("--tags", nargs="+", default=[])
        p.add_argument("--no-cache", action="store_true")

        a = p.parse_args(["faq.jsonl"])
        print(a.dataset, a.model, a.limit, a.tags, a.no_cache)
        b = p.parse_args(["--model", "large", "faq.jsonl", "--tags", "billing", "eu", "--limit", "50", "--no-cache"])
        print(b.model, b.limit, b.tags, b.no_cache, vars(b) == vars(a))
        err = io.StringIO()
        for argv in (["faq.jsonl", "--model", "huge"], [], ["faq.jsonl", "--limit", "ten"]):
            with contextlib.redirect_stderr(err):
                try:
                    p.parse_args(argv)
                except SystemExit as e:
                    print("exit", e.code)
        print([line.split(": error: ")[1] for line in err.getvalue().splitlines() if ": error: " in line])
        """,
        hints=["Options may appear in any order around positionals. A missing value becomes `None` unless a default is given. Errors exit with code 2."],
        why="""Unset options take their defaults (`None` without one); `store_true` flags are `False` unless given. Options may come before or after the positional, `nargs="+"`
        collects values until the next option, and `type=int` converts. Each invalid command line (a value outside `choices`, a missing positional, a non-integer) makes
        `argparse` print usage and an error message to standard error and exit with 2, the conventional "bad usage" code."""),
    write("A parser for an ingestion command", "easy", tag="RAG",
        prompt="""Write `build_parser()` for `rag-ingest SOURCE [-o OUT] [--chunk-size N] [--overlap N] [--dry-run]`: `SOURCE` is required; `--out` defaults to `"chunks.jsonl"`;
        `--chunk-size` is an int defaulting to 200; `--overlap` an int defaulting to 0; `--dry-run` a flag. Then write `main(argv=None)` that parses the arguments, returns 2 (after
        printing `"error: overlap must be smaller than chunk size"` to standard error) when `overlap >= chunk_size`, and otherwise prints one summary line to standard output,
        `f"source={...} out={...} chunk_size={...} overlap={...} dry_run={...}"`, and returns 0.""",
        code="""
        import argparse, sys

        def build_parser():
            pass

        def main(argv=None):
            pass
        """,
        tests="""
        import contextlib, io
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(["docs/", "--chunk-size", "120", "--overlap", "20", "--dry-run"])
        assert code == 0 and out.getvalue() == "source=docs/ out=chunks.jsonl chunk_size=120 overlap=20 dry_run=True\\n" and err.getvalue() == ""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(["docs/", "-o", "x.jsonl", "--overlap", "200"])
        assert code == 2 and out.getvalue() == "" and err.getvalue() == "error: overlap must be smaller than chunk size\\n"
        assert build_parser().parse_args(["d"]).chunk_size == 200 and build_parser().prog == "rag-ingest"
        """,
        hints=["`argparse.ArgumentParser(prog=\"rag-ingest\")`; `add_argument(\"-o\", \"--out\", default=\"chunks.jsonl\")` and so on.",
               "`print(..., file=sys.stderr)` for the error; `parse_args(argv)` with `argv=None` reads `sys.argv`."],
        solution="""
        import argparse, sys


        def build_parser():
            p = argparse.ArgumentParser(prog="rag-ingest", description="Chunk documents for the vector index.")
            p.add_argument("source", help="folder with documents")
            p.add_argument("-o", "--out", default="chunks.jsonl", help="output JSONL file")
            p.add_argument("--chunk-size", type=int, default=200, help="words per chunk")
            p.add_argument("--overlap", type=int, default=0, help="words shared by neighbouring chunks")
            p.add_argument("--dry-run", action="store_true", help="show what would be done")
            return p


        def main(argv=None):
            args = build_parser().parse_args(argv)
            if args.overlap >= args.chunk_size:
                print("error: overlap must be smaller than chunk size", file=sys.stderr)
                return 2
            print(f"source={args.source} out={args.out} chunk_size={args.chunk_size} overlap={args.overlap} dry_run={args.dry_run}")
            return 0
        """,
        why="""Building the parser in its own function lets tests and documentation tools inspect it, and `main(argv)` makes the whole command testable by passing a list instead of
        reading the real command line. Argument-level checks belong to `argparse` (types, choices); rules that involve several arguments, such as overlap versus chunk size,
        are checked after parsing, reported on standard error and turned into exit code 2, the same code argparse uses for bad usage. The summary goes to standard output
        because it is the command's result."""),
    fix("A main that exits instead of returning", "easy", tag="Data work",
        prompt="""`main` reads `sys.argv` directly and calls `sys.exit()` from inside, so tests cannot call it without the test process exiting, and cannot pass their own arguments.
        Make it `main(argv=None)` that parses `argv` with argparse (a required `--day` option) and **returns** 0 on success or 1 when the export fails, printing the error to
        standard error. (In a real file, the last line would be `if __name__ == "__main__": raise SystemExit(main())`; it is left out here because code on this page runs as
        `__main__`, so the line would run the tool immediately.)""",
        code="""
        import sys


        def export(day):
            if day == "1999-01-01":
                raise ValueError("no data for that day")
            return f"exported {day}"


        def main():
            if len(sys.argv) < 3 or sys.argv[1] != "--day":
                print("usage: export --day YYYY-MM-DD")
                sys.exit(2)
            try:
                print(export(sys.argv[2]))
            except ValueError as e:
                print(e)
                sys.exit(1)
            sys.exit(0)
        """,
        tests="""
        import contextlib, io
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            codes = (main(["--day", "2025-03-01"]), main(["--day", "1999-01-01"]))
        assert codes == (0, 1)
        assert out.getvalue() == "exported 2025-03-01\\n" and "no data for that day" in err.getvalue()
        def usage():
            with contextlib.redirect_stderr(io.StringIO()):
                try:
                    main([])
                except SystemExit as e:
                    return e.code
        assert usage() == 2
        """,
        hints=["`parser.add_argument(\"--day\", required=True)`; `args = parser.parse_args(argv)`; catch `ValueError` and `return 1`.",
               "Do not call `sys.exit` inside `main`; the caller (the `__main__` guard in a real file) turns the returned code into the exit status."],
        solution="""
        import argparse, sys


        def export(day):
            if day == "1999-01-01":
                raise ValueError("no data for that day")
            return f"exported {day}"


        def main(argv=None):
            parser = argparse.ArgumentParser(prog="export")
            parser.add_argument("--day", required=True, help="day to export, YYYY-MM-DD")
            args = parser.parse_args(argv)
            try:
                print(export(args.day))
            except ValueError as e:
                print(f"error: {e}", file=sys.stderr)
                return 1
            return 0
        """,
        why="""`sys.exit` raises `SystemExit`, which ends the process, including a test run, when nobody catches it, and reading `sys.argv` ties the function to the real command line.
        Taking `argv` as a parameter and returning the code moves both decisions to the edge: the last line turns the return value into the process's exit code, while tests
        call `main([...])` like any function. argparse still exits with 2 on bad usage, which is the one exit worth keeping (tests catch it). In the real file, `if __name__ == "__main__": raise
        SystemExit(main())` connects the two worlds. Errors go to standard error,
        so they do not mix with the exported data."""),
    predict("Exit codes and SystemExit", "easy",
        code="""
        import contextlib, io, sys

        def run(fn):
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                try:
                    fn()
                    return "returned", None
                except SystemExit as e:
                    return e.code, err.getvalue().strip()

        print(run(lambda: sys.exit()), run(lambda: sys.exit(0)), run(lambda: sys.exit(3)))
        print(run(lambda: sys.exit("fatal: index missing")))
        print(run(lambda: None), issubclass(SystemExit, Exception), issubclass(SystemExit, BaseException))
        """,
        hints=["`sys.exit(x)` raises `SystemExit(x)`. A string code is printed to stderr by the interpreter and the process exits with 1. `SystemExit` is a `BaseException`."],
        why="""`sys.exit()` and `sys.exit(0)` both mean success (the code is `None` or 0); an integer is used as the exit status; a string is not a status at all: the interpreter
        prints it to standard error and exits with 1, a shortcut for fatal errors in scripts. Here nothing printed it because the exception was caught, and the message
        is in `e.code`. `SystemExit` derives from `BaseException`, not `Exception`, so a generic `except Exception` in a tool does not accidentally stop it from exiting."""),
)

section("medium", "Medium",
    write("Subcommands for an LLM tool", "medium", tag="GenAI",
        prompt="""Write `main(argv=None, client=None)` for `llmctl` with three subcommands: `ask QUESTION [--model M]` (default model `"small"`) prints `client.ask(question, model)`;
        `models` prints each name from `client.models()` on its own line; `batch FILE [--concurrency N]` (default 4, must be at least 1) prints `f"would run {FILE} with
        concurrency {N}"`. Use `add_subparsers(dest="command", required=True)` and `set_defaults(func=...)`; return 0 on success, 1 (with `error: ...` on stderr) if the client
        raises `ConnectionError`.""",
        code="""
        import argparse, sys

        def main(argv=None, client=None):
            pass
        """,
        tests="""
        import contextlib, io
        class FakeClient:
            def ask(self, question, model):
                if "down" in question:
                    raise ConnectionError("model service unreachable")
                return f"[{model}] answer to {question}"
            def models(self):
                return ["small", "large"]
        def run(argv):
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                try:
                    code = main(argv, client=FakeClient())
                except SystemExit as e:
                    code = e.code
            return code, out.getvalue(), err.getvalue()
        assert run(["ask", "refund window?"]) == (0, "[small] answer to refund window?\\n", "")
        assert run(["ask", "refund?", "--model", "large"])[1] == "[large] answer to refund?\\n"
        assert run(["models"]) == (0, "small\\nlarge\\n", "")
        assert run(["batch", "q.jsonl", "--concurrency", "8"])[1] == "would run q.jsonl with concurrency 8\\n"
        code, out, err = run(["ask", "is it down?"])
        assert code == 1 and out == "" and err == "error: model service unreachable\\n"
        assert run([])[0] == 2 and run(["batch", "q.jsonl", "--concurrency", "0"])[0] == 2
        """,
        hints=["One handler function per subcommand taking `(args, client)`; attach with `sub.set_defaults(func=handler)` and call `args.func(args, client)`.",
               "Reject a concurrency below 1 with `parser.error(...)` (which exits with 2) or a custom `type` function."],
        solution="""
        import argparse, sys


        def _positive(text):
            value = int(text)
            if value < 1:
                raise argparse.ArgumentTypeError("must be at least 1")
            return value


        def _ask(args, client):
            print(client.ask(args.question, args.model))


        def _models(args, client):
            for name in client.models():
                print(name)


        def _batch(args, client):
            print(f"would run {args.file} with concurrency {args.concurrency}")


        def main(argv=None, client=None):
            parser = argparse.ArgumentParser(prog="llmctl")
            sub = parser.add_subparsers(dest="command", required=True)
            ask = sub.add_parser("ask", help="ask one question")
            ask.add_argument("question")
            ask.add_argument("--model", default="small")
            ask.set_defaults(func=_ask)
            models = sub.add_parser("models", help="list models")
            models.set_defaults(func=_models)
            batch = sub.add_parser("batch", help="run a batch file")
            batch.add_argument("file")
            batch.add_argument("--concurrency", type=_positive, default=4)
            batch.set_defaults(func=_batch)
            args = parser.parse_args(argv)
            try:
                args.func(args, client)
            except ConnectionError as e:
                print(f"error: {e}", file=sys.stderr)
                return 1
            return 0
        """,
        why="""Subparsers give each action its own arguments and help text (`llmctl batch --help`), and `set_defaults(func=...)` stores the handler on the parsed namespace, so
        dispatch is one line with no `if command == ...` chain. Injecting `client` makes every subcommand testable with a fake (13.3). Connection problems are expected
        failures, reported as one clean line on standard error with exit code 1, rather than a traceback; programming errors still produce tracebacks, which is what you want
        for bugs. A custom `type` function rejects an invalid concurrency during parsing, with argparse's usual message and exit code 2."""),
    write("A JSONL filter that works in pipes", "medium", tag="Data work",
        prompt="""Write `main(argv=None, stdin=None, stdout=None, stderr=None)` for `jsonl-filter --label L [--skip-bad]`: read JSON Lines from `stdin`, write the records whose `"label"`
        equals `L` to `stdout` (one compact JSON object per line, non-ASCII kept), and report bad lines on `stderr` as `f"line {n}: invalid JSON"`. Without `--skip-bad`, return 1
        if any line was bad (after processing everything); with it, return 0. Write a final summary `f"kept {k} of {n} records"` to `stderr`. Streams default to the `sys` ones.""",
        code="""
        import argparse, json, sys

        def main(argv=None, stdin=None, stdout=None, stderr=None):
            pass
        """,
        tests="""
        import io
        data = '{"id": 1, "label": "spam"}\\n{"id": 2, "label": "ham"}\\nnot json\\n\\n{"id": 3, "label": "spam", "text": "Gagnez un prix"}\\n'
        out, err = io.StringIO(), io.StringIO()
        code = main(["--label", "spam"], stdin=io.StringIO(data), stdout=out, stderr=err)
        assert code == 1
        assert out.getvalue().splitlines() == ['{"id": 1, "label": "spam"}', '{"id": 3, "label": "spam", "text": "Gagnez un prix"}']
        assert err.getvalue().splitlines() == ["line 3: invalid JSON", "kept 2 of 3 records"]
        out, err = io.StringIO(), io.StringIO()
        assert main(["--label", "ham", "--skip-bad"], stdin=io.StringIO(data), stdout=out, stderr=err) == 0 and out.getvalue() == '{"id": 2, "label": "ham"}\\n'
        """,
        hints=["`stdin = stdin or sys.stdin` and so on; iterate over `stdin` line by line with `enumerate(..., start=1)`, skipping blank lines.",
               "Count valid records for the summary; remember whether any line failed."],
        solution="""
        import argparse, json, sys


        def main(argv=None, stdin=None, stdout=None, stderr=None):
            stdin, stdout, stderr = stdin or sys.stdin, stdout or sys.stdout, stderr or sys.stderr
            parser = argparse.ArgumentParser(prog="jsonl-filter")
            parser.add_argument("--label", required=True)
            parser.add_argument("--skip-bad", action="store_true")
            args = parser.parse_args(argv)
            total = kept = 0
            bad = False
            for n, line in enumerate(stdin, start=1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    print(f"line {n}: invalid JSON", file=stderr)
                    bad = True
                    continue
                total += 1
                if record.get("label") == args.label:
                    stdout.write(json.dumps(record, ensure_ascii=False) + "\\n")
                    kept += 1
            print(f"kept {kept} of {total} records", file=stderr)
            return 1 if bad and not args.skip_bad else 0
        """,
        why="""This is the shape of a Unix filter: data in on standard input, data out on standard output, everything else on standard error, so `cat tickets.jsonl | jsonl-filter
        --label spam > spam.jsonl` produces a clean file while warnings and the summary still appear on the terminal. Streaming line by line keeps memory constant for
        gigabyte inputs (12.2). The exit code tells a pipeline whether to trust the output: bad input fails the step unless the caller explicitly accepts it with
        `--skip-bad`. Accepting the streams as parameters is what makes the test above possible without spawning a process."""),
    fix("A tool that logs to stdout and always succeeds", "medium", tag="ML",
        prompt="""`score` prints scores as CSV for the next tool in a pipeline, but it also prints progress messages to **standard output**, corrupting the CSV, and it returns 0 even
        when some rows fail. Send progress and errors to `stderr`, keep only the header and data rows on `stdout`, and return 1 if any row failed.""",
        code="""
        import sys

        def score(rows, stdout=None, stderr=None):
            stdout, stderr = stdout or sys.stdout, stderr or sys.stderr
            print("scoring", len(rows), "rows...", file=stdout)
            print("id,score", file=stdout)
            for row in rows:
                try:
                    value = round(row["hits"] / row["total"], 3)
                    print(f"{row['id']},{value}", file=stdout)
                except (KeyError, ZeroDivisionError) as e:
                    print(f"skipping {row.get('id')}: {type(e).__name__}", file=stdout)
            print("done", file=stdout)
            return 0
        """,
        tests="""
        import io
        rows = [{"id": "a", "hits": 3, "total": 4}, {"id": "b", "hits": 1, "total": 0}, {"id": "c", "hits": 2, "total": 2}]
        out, err = io.StringIO(), io.StringIO()
        assert score(rows, out, err) == 1
        assert out.getvalue() == "id,score\\na,0.75\\nc,1.0\\n"
        assert err.getvalue().splitlines() == ["scoring 3 rows...", "skipping b: ZeroDivisionError", "done"]
        out, err = io.StringIO(), io.StringIO()
        assert score(rows[:1], out, err) == 0 and out.getvalue() == "id,score\\na,0.75\\n"
        """,
        hints=["Change `file=stdout` to `file=stderr` for the progress, skip and done messages; track whether any row failed."],
        solution="""
        import sys

        def score(rows, stdout=None, stderr=None):
            stdout, stderr = stdout or sys.stdout, stderr or sys.stderr
            print("scoring", len(rows), "rows...", file=stderr)
            print("id,score", file=stdout)
            failed = False
            for row in rows:
                try:
                    value = round(row["hits"] / row["total"], 3)
                    print(f"{row['id']},{value}", file=stdout)
                except (KeyError, ZeroDivisionError) as e:
                    print(f"skipping {row.get('id')}: {type(e).__name__}", file=stderr)
                    failed = True
            print("done", file=stderr)
            return 1 if failed else 0
        """,
        why="""Anything on standard output becomes input for the next program, so `scoring 3 rows...` and `done` would be parsed as CSV rows, and `skipping b` too: the next tool either
        crashes or, worse, silently ingests garbage. Diagnostics belong on standard error, which a pipe does not capture. The exit code was the second lie: a scheduler saw
        success while a row was dropped. Returning 1 lets `score ... && upload ...` stop before uploading incomplete results; a `--allow-failures` option can make partial
        success explicit when that is acceptable."""),
    trace("Defaults, config, environment and flags", "medium",
        prompt="Fill in `settings` after each marked line.",
        code="""
        import argparse

        def load(argv, config=None, env=None):
            p = argparse.ArgumentParser()
            p.add_argument("--model", default="small")
            p.add_argument("--limit", type=int, default=10)
            p.add_argument("--debug", action="store_true")
            layered = {}
            layered.update(config or {})
            env = env or {}
            if "APP_MODEL" in env:
                layered["model"] = env["APP_MODEL"]
            if "APP_LIMIT" in env:
                layered["limit"] = int(env["APP_LIMIT"])
            p.set_defaults(**layered)
            a = p.parse_args(argv)
            return (a.model, a.limit, a.debug)

        settings = load([])  # row: "defaults only"
        settings = load([], config={"model": "medium", "limit": 20})  # row: "config file"
        settings = load([], config={"model": "medium"}, env={"APP_MODEL": "large"})  # row: "env beats config"
        settings = load(["--model", "tiny", "--debug"], config={"model": "medium"}, env={"APP_MODEL": "large", "APP_LIMIT": "5"})  # row: "flags beat everything"
        """,
        trace_vars=["settings"],
        hints=["`set_defaults` replaces the defaults declared in `add_argument`; values given on the command line always win over defaults."],
        why="""`set_defaults` lets the layers below the command line supply the defaults: the configuration file first, then environment variables written over it, so each later
        layer wins. An explicit flag is not a default, so `--model tiny` overrides everything, while the limit still comes from the environment because no flag set it.
        This is the standard precedence (defaults, file, environment, flags), and implementing it in one place keeps every command consistent."""),
    write("Argument types that validate", "medium", tag="ML",
        prompt="""Write three `argparse` type functions that raise `argparse.ArgumentTypeError` with a clear message: `positive_int` (an integer at least 1), `probability` (a float in
        `[0, 1]`), and `existing_file` (a path that exists and is a file, returned as a `pathlib.Path`). Then write `build_parser()` for `train --epochs N --dropout P --data FILE`
        using them (all required).""",
        code="""
        import argparse
        from pathlib import Path

        def positive_int(text):
            pass

        def probability(text):
            pass

        def existing_file(text):
            pass

        def build_parser():
            pass
        """,
        tests="""
        import argparse, contextlib, io, os, tempfile
        from pathlib import Path
        data = os.path.join(tempfile.mkdtemp(), "train.csv")
        open(data, "w").close()
        args = build_parser().parse_args(["--epochs", "3", "--dropout", "0.1", "--data", data])
        assert (args.epochs, args.dropout, args.data) == (3, 0.1, Path(data)) and isinstance(args.data, Path)
        def error(argv):
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                try:
                    build_parser().parse_args(argv)
                except SystemExit as e:
                    return e.code, err.getvalue().strip().splitlines()[-1]
        code, msg = error(["--epochs", "0", "--dropout", "0.1", "--data", data])
        assert code == 2 and msg.endswith("argument --epochs: must be an integer >= 1, got '0'")
        assert error(["--epochs", "2", "--dropout", "1.5", "--data", data])[1].endswith("argument --dropout: must be a probability in [0, 1], got '1.5'")
        assert error(["--epochs", "2", "--dropout", "x", "--data", data])[1].endswith("argument --dropout: must be a probability in [0, 1], got 'x'")
        assert "no such file" in error(["--epochs", "2", "--dropout", "0.2", "--data", data + ".missing"])[1]
        """,
        hints=["Each function converts inside `try`, checks the range, and raises `argparse.ArgumentTypeError(f\"must be ..., got {text!r}\")`.",
               "`Path(text).is_file()` checks existence and type."],
        solution="""
        import argparse
        from pathlib import Path


        def positive_int(text):
            try:
                value = int(text)
            except ValueError:
                value = 0
            if value < 1:
                raise argparse.ArgumentTypeError(f"must be an integer >= 1, got {text!r}")
            return value


        def probability(text):
            try:
                value = float(text)
            except ValueError:
                value = -1.0
            if not 0.0 <= value <= 1.0:
                raise argparse.ArgumentTypeError(f"must be a probability in [0, 1], got {text!r}")
            return value


        def existing_file(text):
            path = Path(text)
            if not path.is_file():
                raise argparse.ArgumentTypeError(f"no such file: {text!r}")
            return path


        def build_parser():
            p = argparse.ArgumentParser(prog="train")
            p.add_argument("--epochs", type=positive_int, required=True)
            p.add_argument("--dropout", type=probability, required=True)
            p.add_argument("--data", type=existing_file, required=True)
            return p
        """,
        why="""A `type` is any function from a string to a value, so validation can happen during parsing, before any expensive work (loading data, allocating a GPU) starts. Raising
        `ArgumentTypeError` makes argparse print `argument --epochs: <your message>` with the usage line and exit with code 2, exactly like its built-in checks, so the user
        sees which argument is wrong and why. Returning a `Path` gives the rest of the program a ready-to-use object (12.1). These small functions are reusable across all
        of a project's commands."""),
    predict("--help and usage", "medium",
        code="""
        import argparse, contextlib, io

        p = argparse.ArgumentParser(prog="rag-eval", description="Evaluate a RAG pipeline on a dataset.")
        p.add_argument("dataset", help="JSONL file with questions")
        p.add_argument("--top-k", type=int, default=5, help="chunks to retrieve (default: %(default)s)")
        p.add_argument("--judge", choices=["exact", "llm"], default="exact")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            try:
                p.parse_args(["--help"])
            except SystemExit as e:
                code = e.code
        lines = out.getvalue().splitlines()
        print(code, lines[0])
        print(lines[2])
        print([l.strip() for l in lines if "--top-k" in l or "dataset" in l.split()[:1]])
        print(p.format_usage().strip())
        """,
        hints=["`--help` prints to standard output and exits with 0. The usage line lists optional arguments in brackets, then positionals."],
        why="""`--help` is a successful request, so it prints to standard output and exits with 0, unlike errors. The usage line is generated from the declarations (optional arguments in
        square brackets, `choices` in braces, metavariables in capitals derived from the option names), followed by the description and one help line per argument, where
        `%(default)s` is filled in. Good help text is the cheapest documentation a tool can have, and because it is generated, it never goes out of date."""),
)

section("hard", "Hard",
    write("Run a console script from pyproject.toml", "hard", tag="Data work",
        prompt="""Write `run_script(pyproject_text, name, argv)` that does what an installed entry point does: read `[project.scripts]`, find `name` (else `LookupError(f"unknown
        command: {name}")`), import the `module:function` target with `importlib.import_module`, call `function(argv)` and return its exit code, mapping `None` to 0. If the
        function raises `SystemExit`, return its code (0 for `None`, 1 for a string); any other exception propagates.""",
        code="""
        import importlib, tomllib

        def run_script(pyproject_text, name, argv):
            pass
        """,
        tests="""
        from lessontools import make_tree, forget
        forget("toolbox_w11")
        make_tree({
            "toolbox_w11/__init__.py": "",
            "toolbox_w11/cli.py": '''
            import argparse
            def main(argv=None):
                p = argparse.ArgumentParser(prog="greet")
                p.add_argument("name")
                args = p.parse_args(argv)
                print(f"hello {args.name}")
                return 0 if args.name != "error" else 3
            def legacy(argv=None):
                raise SystemExit("legacy tool failed")
            def quiet(argv=None):
                return None
            ''',
        })
        pyproject = '''
        [project]
        name = "toolbox"
        version = "0.1.0"
        [project.scripts]
        greet = "toolbox_w11.cli:main"
        legacy = "toolbox_w11.cli:legacy"
        quiet = "toolbox_w11.cli:quiet"
        '''
        import contextlib, io
        with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()):
            assert run_script(pyproject, "greet", ["Ana"]) == 0 and run_script(pyproject, "greet", ["error"]) == 3
            assert run_script(pyproject, "greet", []) == 2
        assert out.getvalue() == "hello Ana\\nhello error\\n"
        assert run_script(pyproject, "legacy", []) == 1 and run_script(pyproject, "quiet", []) == 0
        try:
            run_script(pyproject, "deploy", [])
            assert False
        except LookupError as e:
            assert str(e) == "unknown command: deploy"
        """,
        hints=["`scripts = tomllib.loads(text)[\"project\"].get(\"scripts\", {})`; split the target with `partition(\":\")`.",
               "Wrap the call in `try`/`except SystemExit as e`: `code = e.code`; `None` means 0, an int is itself, anything else (a message) means 1."],
        solution="""
        import importlib, tomllib


        def _exit_code(code):
            if code is None:
                return 0
            if isinstance(code, int):
                return code
            return 1


        def run_script(pyproject_text, name, argv):
            scripts = tomllib.loads(pyproject_text)["project"].get("scripts", {})
            if name not in scripts:
                raise LookupError(f"unknown command: {name}")
            module_name, _, attr = scripts[name].partition(":")
            fn = getattr(importlib.import_module(module_name), attr)
            try:
                return _exit_code(fn(argv))
            except SystemExit as e:
                return _exit_code(e.code)
        """,
        why="""When a package is installed, each `[project.scripts]` entry becomes an executable whose body is essentially this function: import the module, call the function, and
        pass its return value to `sys.exit`, so returning 0, 3 or `None` sets the process's exit code. argparse's own `SystemExit(2)` on bad usage and a legacy tool's
        `SystemExit("message")` are translated the way the interpreter does (a message means 1). Writing it once shows why the `main(argv) -> int` contract is so convenient:
        the same function works as an entry point, under `python -m`, and in tests."""),
    fix("Read the code: a hand-rolled CLI", "hard", tag="GenAI",
        prompt="""`classify_cli` parses `sys.argv`-style lists by hand, so options must come in one exact order, `--threshold` is never converted from a string, errors are printed to
        stdout, bad input crashes with a traceback, the whole input is read into memory, and it always returns 0. Rewrite it as `main(argv, stdin, stdout, stderr)` with
        argparse: `--threshold` a float in `[0, 1]` (default 0.5), an optional `--field` (default `"text"`), reading JSONL from `stdin` line by line, writing `{"id", "label"}` lines
        to `stdout` (`"spam"` when `score(text) >= threshold`), reporting a record missing the field on `stderr` as `f"line {n}: missing {field}"`, and returning 1 if any line
        failed, else 0.""",
        code="""
        import json


        def score(text):
            words = text.lower().split()
            return sum(w in {"win", "prize", "free", "click"} for w in words) / max(len(words), 1)


        def classify_cli(argv, stdin, stdout, stderr):
            threshold = 0.5
            field = "text"
            if len(argv) >= 2 and argv[0] == "--threshold":
                threshold = argv[1]
            if len(argv) >= 4 and argv[2] == "--field":
                field = argv[3]
            records = [json.loads(line) for line in stdin.read().splitlines() if line]
            for r in records:
                label = "spam" if score(r[field]) >= threshold else "ham"
                stdout.write(json.dumps({"id": r["id"], "label": label}) + "\\n")
            return 0
        """,
        tests="""
        import contextlib, io
        data = '{"id": 1, "text": "win a free prize"}\\n{"id": 2, "body": "no text here"}\\n{"id": 3, "text": "lunch at noon"}\\n'
        out, err = io.StringIO(), io.StringIO()
        assert main(["--threshold", "0.4"], io.StringIO(data), out, err) == 1
        assert out.getvalue().splitlines() == ['{"id": 1, "label": "spam"}', '{"id": 3, "label": "ham"}']
        assert err.getvalue() == "line 2: missing text\\n"
        out, err = io.StringIO(), io.StringIO()
        assert main(["--field", "body", "--threshold", "0.9"], io.StringIO('{"id": 9, "body": "click to win"}\\n'), out, err) == 0
        assert out.getvalue() == '{"id": 9, "label": "ham"}\\n'
        with contextlib.redirect_stderr(io.StringIO()):
            try:
                main(["--threshold", "1.5"], io.StringIO(""), io.StringIO(), io.StringIO())
                assert False
            except SystemExit as e:
                assert e.code == 2
        """,
        hints=["Use a `type=` function for the threshold range (problem 9), `parse_args(argv)` for any order, and iterate `for n, line in enumerate(stdin, start=1)`.",
               "Catch `KeyError` for the missing field, write the message to `stderr`, remember the failure and continue."],
        solution="""
        import argparse, json


        def score(text):
            words = text.lower().split()
            return sum(w in {"win", "prize", "free", "click"} for w in words) / max(len(words), 1)


        def _probability(text):
            try:
                value = float(text)
            except ValueError:
                value = -1.0
            if not 0.0 <= value <= 1.0:
                raise argparse.ArgumentTypeError(f"must be in [0, 1], got {text!r}")
            return value


        def main(argv, stdin, stdout, stderr):
            parser = argparse.ArgumentParser(prog="classify")
            parser.add_argument("--threshold", type=_probability, default=0.5)
            parser.add_argument("--field", default="text")
            args = parser.parse_args(argv)
            failed = False
            for n, line in enumerate(stdin, start=1):
                if not line.strip():
                    continue
                record = json.loads(line)
                try:
                    text = record[args.field]
                except KeyError:
                    print(f"line {n}: missing {args.field}", file=stderr)
                    failed = True
                    continue
                label = "spam" if score(text) >= args.threshold else "ham"
                stdout.write(json.dumps({"id": record["id"], "label": label}) + "\\n")
            return 1 if failed else 0
        """,
        why="""Every defect is a rule from this lesson. Hand parsing accepted only one order of options; argparse accepts any order, generates help, and rejects bad values with
        exit code 2. The threshold stayed a string, so `score(...) >= "0.5"` would raise `TypeError` in Python 3; a `type` function converts and validates it. Reading all of
        stdin into a list breaks on large inputs, while iterating the stream handles any size. A record without the field crashed the whole run with a traceback; reporting it
        on standard error with its line number and continuing lets the rest of the data through, and the exit code still signals that something went wrong."""),
    predict("argparse details that surprise people", "hard",
        code="""
        import argparse, contextlib, io

        p = argparse.ArgumentParser(prog="ingest")
        p.add_argument("--chunk-size", type=int, default=200)
        p.add_argument("--cache", action=argparse.BooleanOptionalAction, default=True)
        p.add_argument("--tag", action="append", default=[])
        p.add_argument("--exclude", nargs="*", default=["tmp"])
        p.add_argument("files", nargs="*")

        print(vars(p.parse_args(["--chunk", "64", "--no-cache"])))
        print(vars(p.parse_args(["--tag", "eu", "--tag", "billing", "a.md", "b.md"])))
        print(vars(p.parse_args(["--exclude", "--", "-weird-name.md"])))
        strict = argparse.ArgumentParser(prog="x", allow_abbrev=False)
        strict.add_argument("--chunk-size", type=int)
        with contextlib.redirect_stderr(io.StringIO()):
            try:
                strict.parse_args(["--chunk", "64"])
            except SystemExit as e:
                print("allow_abbrev=False ->", e.code)
        print(p.parse_known_args(["a.md", "--unknown", "1"]))
        """,
        hints=["argparse accepts unambiguous prefixes of long options by default. `--` ends option parsing. `append` collects repeated options. `parse_known_args` returns the leftovers."],
        why="""By default argparse accepts any unambiguous abbreviation, so `--chunk` means `--chunk-size`, which is convenient but means adding a new option such as `--chunked` later
        can break existing scripts; `allow_abbrev=False` turns it off. `BooleanOptionalAction` generates `--cache` and `--no-cache`. `action="append"` collects a repeated option
        into a list, which is the clean way to pass several tags. `nargs="*"` accepts zero values, so `--exclude` given alone produces an empty list, and `--` stops option
        parsing so a file name starting with a dash is treated as a positional. `parse_known_args` returns the parsed namespace and the arguments it did not recognise, which
        wrappers use to pass options through to another program."""),
)

section("interview", "Interview questions",
    explain("What makes a good command-line tool?", "medium", tag="Interview",
        why="""A good CLI is predictable for people and for programs. Arguments are parsed by a real parser (argparse, Click, Typer) with types, choices and good `--help`; required
        inputs are positionals or clearly named options; destructive actions need explicit confirmation or a `--dry-run` preview. Results go to **standard output** in a
        parseable format (JSON or JSONL for machines, a table for humans, ideally selectable with `--format`), and diagnostics go to **standard error**, so the tool composes in
        pipes. **Exit codes** are meaningful (0 success, 1 failure, 2 usage, documented others). Configuration follows a clear precedence (defaults, config file, environment,
        flags) and secrets come from the environment, never from flags that end up in shell history. It reads streams incrementally, handles Ctrl-C cleanly, is idempotent where
        possible, and its core logic lives in importable functions behind a thin `main(argv) -> int`, which makes it testable and reusable."""),
    explain("How do you test a command-line tool?", "medium", tag="Interview",
        why="""Structure it so most tests do not need a subprocess: the business logic lives in ordinary functions tested directly, and `main(argv, ...)` takes the argument list and,
        ideally, the input and output streams as parameters. Tests then call `main([...])` with `io.StringIO` streams (or pytest's `capsys`, 13.2) and assert on the return code,
        standard output and standard error separately, including error paths: bad arguments (argparse exits with 2, so catch `SystemExit`), invalid input lines, and failing
        dependencies replaced by fakes. Use `tmp_path` for files and `monkeypatch` for environment variables and configuration. Add a few end-to-end tests that run the
        installed entry point with `subprocess.run([...], capture_output=True)` to check packaging, the `__main__` guard and real exit codes. Snapshot tests (13.P) work well for
        `--help` output and formatted tables."""),
    explain("A nightly pipeline step 'succeeded' but produced an empty file. What would you change in the tool?", "hard", tag="Interview",
        why="""The tool lied through its exit code, so first make failures visible: return non-zero when anything went wrong (input missing or unreadable, zero records processed when
        some were expected, a dependency failing), and treat "nothing to do" explicitly (a flag such as `--allow-empty`, or a distinct exit code) rather than as silent success.
        Validate inputs and preconditions at start-up and fail fast with a clear message on standard error. Write output **atomically** (12.1) so a crash cannot leave a partial
        or empty file that the next step trusts, and only replace the previous output on success. Emit a summary (records read, written, skipped, errors) to standard error or as
        metrics, and a manifest next to the output, so the scheduler and people can check counts; downstream steps can verify the manifest before consuming. Finally, add tests
        for the failure paths and an alert on the scheduler side for unusually small outputs, because exit codes only catch what the tool knows is wrong."""),
)

recap(
    "Use `argparse`: positionals are required, options have defaults, `type` converts and validates, `choices` restricts, and bad usage exits with code 2.",
    "Write `main(argv=None) -> int` and end the file with `raise SystemExit(main())`; keep the CLI layer thin over importable functions.",
    "Results to standard output, diagnostics to standard error, data read from standard input line by line; accept streams as parameters for tests.",
    "Exit codes are the tool's answer to schedulers and scripts: 0 success, non-zero failure, never print an error and exit 0.",
    "Subcommands with `set_defaults(func=...)`, configuration precedence via `set_defaults`, and `[project.scripts]` entry points that call `main`.",
)
