from lesson import *
from diagrams import *

lesson(
    id="m12-3", num="12.3", title="logging",
    intro="When a service misbehaves at 3 a.m., its logs are the only witness. The `logging` module from the ground up: loggers "
          "and their hierarchy, levels, handlers and formatters, lazy formatting, exceptions with tracebacks, configuration for "
          "applications versus libraries, filters for redaction and request context, and structured JSON logs. Applied to "
          "LLM calls, retrieval libraries and ETL jobs.",
    desc="Loggers, levels, handlers, formatters and structured logs.",
    keys="logging getlogger __name__ logger hierarchy propagate level debug info warning error critical handler streamhandler filehandler rotatingfilehandler formatter filter nullhandler basicconfig dictconfig exception exc_info extra contextvars json structured redaction",
)

term("Logger", "A named object you call to record events (`log.info(...)`). Names form a dotted hierarchy, such as `app.db` under `app`.")
term("Handler", "The part of `logging` that sends records somewhere: a stream, a file, a network service. A logger can have several.")
term("Log record", "The object created for each logging call, holding the message, arguments, level, logger name, time, exception and any extra fields.")

section("why", "Why logging instead of print",
    p("""`print` writes text to standard output and that is all. A real program needs more from its diagnostic messages: a **severity** so routine chatter can be
    hidden and errors cannot, a **source** (which module said it), a **destination** that may be a console, a file, or a log service, a **format**
    with timestamps and context, and the ability to change all of that **without editing the code that emits the messages**, because the same library
    runs inside a notebook, a test and a production server. The `logging` module separates those concerns: code calls a logger, and the application
    decides, once, where records go and which ones are kept."""),
    p("""The five standard levels are numbers, so they compare: `DEBUG` (10) for detail useful while diagnosing, `INFO` (20) for normal milestones (a job started,
    a model loaded), `WARNING` (30) for something unexpected that was handled (a retry, a fallback), `ERROR` (40) for an operation that failed, and
    `CRITICAL` (50) for a failure of the whole program. A logger or handler set to a level drops everything below it."""),
)

section("loggers", "Loggers, the hierarchy and levels",
    fig(flowchart({
        "call": ("start", 0, 0, "log.info(...) on|myapp.retrieval"),
        "lvl": ("ask", 0, 1, "INFO at or above the|effective level?"),
        "drop": ("bad", 1, 1, "dropped, nothing|formatted"),
        "own": ("step", 0, 2, "filters, then this|logger's handlers"),
        "prop": ("ask", 0, 3, "propagate is True?"),
        "stop": ("end", 1, 3, "stop"),
        "up": ("accent", 0, 4, "handlers of each ancestor,|up to root"),
    }, [("call", "lvl"), ("lvl", "drop", "no"), ("lvl", "own", "yes"), ("own", "prop"), ("prop", "stop", "no"), ("prop", "up", "yes")],
        cell=(250, 80), label="what happens to a log record"),
        "The level is checked once, on the logger you called; after that the record propagates to ancestor handlers, and only each handler's own level can still drop it."),
    p("""Every module gets its own logger with **`log = logging.getLogger(__name__)`**. `__name__` is the module's dotted import name (`myapp.retrieval.search`),
    so loggers form a tree that mirrors the package, and `getLogger` returns the **same** object for the same name, wherever it is called. A record created on
    a logger is checked against that logger's **effective level** (its own level, or if it has none, `NOTSET`, the nearest ancestor's), then passed to the
    logger's handlers and, because `propagate` is `True` by default, to the handlers of every ancestor up to the **root logger**. That is why an application
    usually attaches handlers only to the root (or to its top package logger), and every module's messages arrive there."""),
    p("""Call the level methods with a format string and **separate arguments**: `log.info("loaded %d docs from %s", n, path)`. The message is only formatted if a
    handler will actually emit it, and the arguments are kept in the record, which structured logging uses. An f-string, `log.debug(f"state {state}")`, is
    formatted **before** the call, even when debug logging is off. Note that arguments are still **evaluated**: `log.debug("%s", expensive())` runs
    `expensive()` every time, so guard truly expensive work with `if log.isEnabledFor(logging.DEBUG):` (problem 8)."""),
    ex("""
    import io, logging

    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(levelname)-7s %(name)s: %(message)s"))
    app = logging.getLogger("shop")
    app.addHandler(handler)
    app.setLevel(logging.INFO)
    app.propagate = False

    db = logging.getLogger("shop.db")
    print(db.parent.name, db.level, db.getEffectiveLevel(), logging.getLogger("shop.db") is db)
    db.debug("SELECT * FROM orders")
    db.info("loaded %d orders in %.1f ms", 120, 4.25)
    db.warning("slow query: %s", "orders by customer")
    app.error("checkout failed for order %s", "A-17")
    print(stream.getvalue(), end="")
    """, "hierarchy.py"),
    p("""`shop.db` has no level of its own (`0`, `NOTSET`), so it inherits `INFO` from `shop`; the debug message is dropped, the others travel up to the handler on
    `shop`, and the format shows which logger produced each one. The examples here attach handlers to their own loggers and set `propagate = False`, so they
    do not depend on the root logger; an application would normally configure the root instead."""),
)

section("handlers", "Handlers, formatters and configuration",
    fig(chain(["logger", "record", "handler (its|own level, filters)", "formatter", ("text to a stream,|file or service", "good")]),
        "Loggers create records, handlers decide where they go, formatters decide how they look."),
    p("""A **handler** delivers records: `StreamHandler` (standard error by default, or any file-like stream), `FileHandler`, `RotatingFileHandler` and
    `TimedRotatingFileHandler` (start a new file at a size or time and keep a fixed number of old ones), `logging.handlers.QueueHandler` for handing records to a
    background thread, and handlers for syslog, HTTP and cloud log services. Each handler has its own level, so one logger can send everything to a file and
    only errors to the console. A **formatter** turns a record into text with `%`-style fields: `%(asctime)s`, `%(levelname)s`, `%(name)s`, `%(message)s`,
    `%(module)s`, `%(funcName)s`, `%(lineno)d`, `%(process)d`, `%(threadName)s`."""),
    p("""**Applications configure logging once, at start-up; libraries never do.** In a script, `logging.basicConfig(level=logging.INFO, format=...)` adds one
    handler to the root logger; larger applications use `logging.config.dictConfig(config)`, a dict (often loaded from a file) describing formatters, handlers
    and logger levels (problem 14), including quieting chatty dependencies such as `logging.getLogger("httpx").setLevel(logging.WARNING)`. A library only
    creates loggers and, by convention, attaches a `logging.NullHandler()` to its top-level logger, so it stays silent unless the application asks to see its
    messages. A library calling `logging.basicConfig`, or the module-level shortcuts `logging.info(...)` (which log to the root and **configure it** if it has no
    handlers), takes that decision away from the application (problem 10)."""),
    ex("""
    import io, logging

    stream = io.StringIO()
    errors_only = io.StringIO()
    everything = logging.StreamHandler(stream)
    everything.setFormatter(logging.Formatter("%(levelname)s [%(name)s.%(funcName)s] %(message)s"))
    alerts = logging.StreamHandler(errors_only)
    alerts.setLevel(logging.ERROR)
    alerts.setFormatter(logging.Formatter("ALERT %(message)s"))

    log = logging.getLogger("ingest")
    log.setLevel(logging.DEBUG)
    log.propagate = False
    log.handlers[:] = [everything, alerts]

    def load(path):
        log.debug("opening %s", path)
        log.error("cannot parse %s", path)

    load("docs/faq.md")
    print(stream.getvalue(), end="")
    print(errors_only.getvalue(), end="")
    """, "handlers.py"),
)

section("exceptions", "Logging exceptions",
    p("""Inside an `except` block, **`log.exception("message")`** logs at `ERROR` level **with the traceback**, which is what makes the record useful later;
    `log.error("failed: %s", e)` keeps only the exception's message and loses where it happened (problem 3). Any level method accepts `exc_info=True` to
    attach the current exception (`log.warning("retrying", exc_info=True)`), and `stack_info=True` adds the current call stack even without an exception.
    Log an exception **once**, where it is handled; logging and re-raising at every layer prints the same traceback five times."""),
    ex("""
    import io, logging

    stream = io.StringIO()
    h = logging.StreamHandler(stream)
    h.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    log = logging.getLogger("llm.client")
    log.handlers[:] = [h]
    log.propagate = False

    def parse(reply):
        import json
        return json.loads(reply)

    try:
        parse('{"label": "spam"')
    except ValueError:
        log.exception("could not parse reply for request %s", "r-42")
    lines = stream.getvalue().splitlines()
    print(lines[0])
    print(lines[1])
    print(lines[-1])
    """, "exceptions.py"),
)

section("context", "Extra fields, filters and request context",
    p("""Every record carries standard attributes, and `extra={"request_id": "r-42", "latency_ms": 812}` adds your own, available to formatters as
    `%(request_id)s` and to handlers as `record.request_id`. A **filter**, either an object with a `filter(record)` method or a plain function, is attached
    to a logger or a handler and returns `False` to drop a record; it may also **modify** the record, which is how you add context to every message or
    redact secrets (problems 7 and 11). Filters on a **handler** see every record that reaches it, including those propagated from child loggers; filters on a
    logger only see records created on that logger."""),
    p("""In a web service, the context you need on every line is the request: its id, the user or tenant, the model. Passing it to every call is impractical,
    so it is stored in a **`contextvars.ContextVar`**, which behaves like a global variable but has a separate value per request, even when requests
    interleave in threads or `asyncio` tasks (14.4), and a filter copies it onto each record."""),
    ex("""
    import io, logging
    from contextvars import ContextVar

    request_id = ContextVar("request_id", default="-")

    def add_request_id(record):
        record.request_id = request_id.get()
        return True

    stream = io.StringIO()
    h = logging.StreamHandler(stream)
    h.addFilter(add_request_id)
    h.setFormatter(logging.Formatter("%(request_id)s %(levelname)s %(message)s"))
    log = logging.getLogger("api")
    log.handlers[:] = [h]
    log.setLevel(logging.INFO)
    log.propagate = False

    log.info("server started")
    token = request_id.set("r-7")
    log.info("retrieved %d chunks", 5, extra={"latency_ms": 41})
    request_id.reset(token)
    log.info("idle")
    print(stream.getvalue(), end="")
    """, "context.py"),
)

section("structured", "Structured logs",
    fig(table(["", "text line", "JSON line"], [
        ["looks like", "INFO answers: done in 812 ms", "{\"level\": \"INFO\", \"latency_ms\": 812}"],
        ["searching", "regular expressions", "query by field"],
        ["aggregating", "parse first", "sum or average directly"],
    ], hl={(1, 2), (2, 2)}, label="text logs versus structured logs"),
        "Structured logs keep fields as fields, so a log platform can filter and aggregate them without parsing."),
    p("""Text logs are written for people; production logs are read by machines first. Log platforms (Elasticsearch and Kibana, Datadog, Grafana Loki, CloudWatch)
    work best with **structured logs**: one JSON object per line with consistent fields such as `time`, `level`, `logger`, `message`, `request_id`, `model`,
    `latency_ms` and `tokens`, so you can filter "all errors for tenant X with latency above 2 s" instead of grepping. In Python that is a formatter whose
    `format(record)` returns `json.dumps` of the fields you choose (problem 5); libraries such as `structlog` and `python-json-logger` provide one."""),
    p("""Two rules apply to every log line. **Never log secrets** (API keys, passwords, tokens) or more personal data than you need; full prompts and documents
    often contain both, so log ids, sizes and hashes instead of content by default, and redact patterns such as keys and e-mail addresses with a filter as a
    safety net. And **log at boundaries**: one line when a request or job starts and ends, one per external call (model, database, tool) with its latency and
    outcome, and one per handled failure. Logging inside tight loops slows the program and buries the lines that matter."""),
)

section("warmup", "Warm-up",
    predict("Levels and effective levels", "easy",
        code="""
        import io, logging

        s = io.StringIO()
        h = logging.StreamHandler(s)
        h.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
        log = logging.getLogger("p1.app")
        log.addHandler(h)
        log.propagate = False
        log.setLevel(logging.WARNING)
        print(log.level, logging.getLevelName(log.getEffectiveLevel()), logging.INFO, logging.ERROR)
        log.debug("d")
        log.info("i")
        log.warning("w")
        log.error("e %s", 1)
        child = logging.getLogger("p1.app.worker")
        child.info("child info")
        child.critical("child critical")
        print(s.getvalue().splitlines())
        """,
        hints=["A logger drops records below its effective level; a child with no level of its own uses its parent's."],
        why="""The logger is set to `WARNING` (30), so `debug` and `info` are dropped and `warning` and `error` are emitted, the latter with its argument formatted in.
        The child has no level of its own, inherits `WARNING` from `p1.app`, drops its `info`, and its `critical` record propagates to the parent's handler,
        where the format shows the child's name."""),
    write("A logger factory that does not duplicate handlers", "easy", tag="Data work",
        prompt="""Write `make_logger(name, stream, level="INFO")` returning the logger `name` configured with exactly one `StreamHandler` writing to `stream`, the format
        `"%(levelname)s %(name)s: %(message)s"`, the given level (a name such as `"DEBUG"`) and `propagate = False`. Calling it again for the same name must
        replace the handler (so the new stream and level apply) rather than add a second one.""",
        code="""
        import logging

        def make_logger(name, stream, level="INFO"):
            pass
        """,
        tests="""
        import io, logging
        first, second = io.StringIO(), io.StringIO()
        log = make_logger("w2.etl", first)
        log.debug("hidden")
        log.info("rows=%d", 3)
        assert first.getvalue() == "INFO w2.etl: rows=3\\n"
        again = make_logger("w2.etl", second, level="DEBUG")
        again.debug("now visible")
        assert again is log and len(log.handlers) == 1 and log.propagate is False
        assert first.getvalue() == "INFO w2.etl: rows=3\\n" and second.getvalue() == "DEBUG w2.etl: now visible\\n"
        """,
        hints=["`logging.getLogger(name)` always returns the same object; clear its handlers with `log.handlers.clear()` before adding the new one.",
               "`setLevel` accepts level names as strings."],
        solution="""
        import logging


        def make_logger(name, stream, level="INFO"):
            log = logging.getLogger(name)
            log.handlers.clear()
            handler = logging.StreamHandler(stream)
            handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
            log.addHandler(handler)
            log.setLevel(level)
            log.propagate = False
            return log
        """,
        why="""Loggers are process-wide singletons per name, so configuration done inside a function accumulates: a factory that only calls `addHandler` gives every message
        twice after the second call, three times after the third, the classic "duplicate log lines" bug in notebooks, where cells are re-run. Clearing the
        handlers makes the function idempotent. `propagate = False` stops the records from also reaching the root logger's handlers. In an application this
        configuration belongs in one start-up function; a factory like this is handy for scripts and tests."""),
    fix("Errors logged without a traceback", "easy", tag="GenAI",
        prompt="""`summarise` logs failures of the model call, but the log only says `model call failed: division by zero`, with no traceback to show where it happened.
        Make it log the traceback, at `ERROR` level, and still return `None`.""",
        code="""
        import logging

        log = logging.getLogger("f3.summarise")

        def summarise(text, model):
            try:
                return model(text)
            except Exception as e:
                log.error("model call failed: %s", e)
                return None
        """,
        tests="""
        import io, logging
        s = io.StringIO()
        h = logging.StreamHandler(s)
        h.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
        log.handlers[:] = [h]
        log.propagate = False
        def broken(text):
            return len(text) / 0
        assert summarise("hello", broken) is None and summarise("ok", str.upper) == "OK"
        out = s.getvalue()
        assert out.startswith("ERROR model call failed") and "Traceback (most recent call last):" in out and "in broken" in out
        assert out.rstrip().endswith("ZeroDivisionError: division by zero")
        """,
        hints=["`log.exception(...)` inside the `except` block, which adds `exc_info` automatically."],
        solution="""
        import logging

        log = logging.getLogger("f3.summarise")

        def summarise(text, model):
            try:
                return model(text)
            except Exception:
                log.exception("model call failed")
                return None
        """,
        why="""An exception's message rarely tells you where or why it happened; the traceback does, down to `broken`'s line. `log.exception` logs at `ERROR` and attaches
        the exception being handled, which the formatter renders as the full traceback after the message, ending with the exception type and message, so
        repeating the message in the text is unnecessary. This matters most exactly where code swallows an exception and returns a fallback: without the
        traceback, the failure becomes invisible."""),
    predict("What lazy formatting saves", "easy",
        code="""
        import io, logging

        class Expensive:
            calls = 0
            def __str__(self):
                Expensive.calls += 1
                return "big object"

        def build():
            print("  build() ran")
            return Expensive()

        s = io.StringIO()
        h = logging.StreamHandler(s)
        h.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
        log = logging.getLogger("p4.lazy")
        log.handlers[:] = [h]
        log.setLevel(logging.INFO)
        log.propagate = False

        log.debug("state: %s", build())
        log.debug(f"state: {Expensive()}")
        log.info("state: %s", Expensive())
        print(Expensive.calls, s.getvalue().splitlines())
        """,
        hints=["Arguments are always evaluated before the call. Formatting with `%s` only happens if the record is emitted; an f-string is formatted before the call."],
        why="""`build()` runs even though the debug message is dropped: Python evaluates arguments before calling `log.debug`. What lazy formatting saves is the string
        conversion, so `__str__` is not called for that record. The f-string converts its object before the call, so `__str__` runs although the message is
        then dropped. The emitted `info` record converts its argument once. Lazy `%s` arguments avoid formatting costs; an `isEnabledFor` guard is needed to
        avoid computing the arguments themselves."""),
)

section("medium", "Medium",
    write("A JSON formatter", "medium", tag="GenAI",
        prompt="""Write `JsonFormatter(logging.Formatter)` whose constructor takes `fields=()`, the names of extra record attributes to include. `format(record)` returns one
        JSON line (no trailing newline) with `level`, `logger` and `message` (the formatted message), then each listed field the record has, then `exc` (the
        formatted traceback) if the record carries exception info. Non-JSON values are converted with `str`; non-ASCII characters are written as is.""",
        code="""
        import json, logging

        class JsonFormatter(logging.Formatter):
            pass
        """,
        tests="""
        import io, json, logging
        s = io.StringIO()
        h = logging.StreamHandler(s)
        h.setFormatter(JsonFormatter(fields=("request_id", "latency_ms", "model")))
        log = logging.getLogger("w5.api")
        log.handlers[:] = [h]
        log.setLevel(logging.INFO)
        log.propagate = False
        log.info("retrieved %d docs for %s", 3, "café", extra={"request_id": "r-1", "latency_ms": 12, "model": object})
        try:
            1 / 0
        except ZeroDivisionError:
            log.exception("failed", extra={"request_id": "r-2"})
        first, second = [json.loads(line) for line in s.getvalue().splitlines()]
        assert first == {"level": "INFO", "logger": "w5.api", "message": "retrieved 3 docs for café", "request_id": "r-1", "latency_ms": 12, "model": "<class 'object'>"}
        assert list(second) == ["level", "logger", "message", "request_id", "exc"] and second["exc"].startswith("Traceback")
        assert second["exc"].endswith("ZeroDivisionError: division by zero") and "café" in s.getvalue()
        """,
        hints=["Call `super().__init__()` and store the fields. `record.getMessage()` applies the arguments.",
               "`self.formatException(record.exc_info)` renders a traceback; `json.dumps(data, default=str, ensure_ascii=False)`."],
        solution="""
        import json, logging


        class JsonFormatter(logging.Formatter):
            def __init__(self, fields=()):
                super().__init__()
                self.fields = tuple(fields)

            def format(self, record):
                data = {"level": record.levelname, "logger": record.name, "message": record.getMessage()}
                for name in self.fields:
                    if hasattr(record, name):
                        data[name] = getattr(record, name)
                if record.exc_info:
                    data["exc"] = self.formatException(record.exc_info)
                return json.dumps(data, default=str, ensure_ascii=False)
        """,
        why="""A formatter is the single place where a record becomes text, so switching an application to structured logs is one class, with no change to the code that
        logs. `getMessage()` merges the arguments into the message; `extra=` values are plain attributes of the record, included only when present, so the
        schema stays stable. The traceback, which a text formatter would print over several lines, becomes one escaped string field, keeping the
        one-record-per-line guarantee that log shippers rely on. `default=str` makes sure a strange value never breaks logging, which must not crash the program
        it is observing. A real formatter would also add `time` from `record.created`."""),
    fix("Every worker message appears twice", "medium", tag="Data work",
        prompt="""`setup` configures logging for an ETL job. Messages from the `f6.etl` logger appear once, but every message from `f6.etl.worker` appears twice. Fix the
        configuration so each message appears exactly once, keeping the `f6.etl` handler.""",
        code="""
        import logging

        def setup(stream):
            handler = logging.StreamHandler(stream)
            handler.setFormatter(logging.Formatter("%(name)s %(message)s"))
            app = logging.getLogger("f6.etl")
            app.setLevel(logging.INFO)
            app.propagate = False
            app.handlers[:] = [handler]
            worker = logging.getLogger("f6.etl.worker")
            worker.handlers[:] = [handler]
            return app, worker
        """,
        tests="""
        import io
        s = io.StringIO()
        app, worker = setup(s)
        worker.info("batch %d done", 1)
        app.info("job finished")
        assert s.getvalue().splitlines() == ["f6.etl.worker batch 1 done", "f6.etl job finished"]
        s2 = io.StringIO()
        app, worker = setup(s2)
        worker.warning("slow")
        assert s2.getvalue() == "f6.etl.worker slow\\n"
        """,
        hints=["A record is handled by its own logger's handlers **and**, while `propagate` is true, by each ancestor's."],
        solution="""
        import logging

        def setup(stream):
            handler = logging.StreamHandler(stream)
            handler.setFormatter(logging.Formatter("%(name)s %(message)s"))
            app = logging.getLogger("f6.etl")
            app.setLevel(logging.INFO)
            app.propagate = False
            app.handlers[:] = [handler]
            worker = logging.getLogger("f6.etl.worker")
            worker.handlers.clear()
            return app, worker
        """,
        why="""The worker's records were emitted by the worker's own handler and then propagated to `f6.etl`, whose handler emitted them again. The design rule is to attach
        handlers high in the tree, usually only at the root or the application's top logger, and let child loggers propagate; giving each module its own
        handler always duplicates. Setting `worker.propagate = False` would also stop the duplicates, but then every module needs its own handler and
        configuration, which defeats the hierarchy."""),
    write("Redact secrets from log messages", "medium", tag="GenAI",
        prompt="""Write `RedactFilter(logging.Filter)` that replaces API keys (`sk-` followed by at least 8 letters, digits, `_` or `-`) and e-mail addresses in the
        **formatted** message with `[REDACTED]`, stores the result as the record's message with no arguments, and always returns `True`. Attach it to a handler
        so it also covers child loggers.""",
        code="""
        import logging, re

        class RedactFilter(logging.Filter):
            pass
        """,
        tests="""
        import io, logging
        s = io.StringIO()
        h = logging.StreamHandler(s)
        h.addFilter(RedactFilter())
        h.setFormatter(logging.Formatter("%(name)s %(message)s"))
        root = logging.getLogger("w7")
        root.handlers[:] = [h]
        root.setLevel(logging.INFO)
        root.propagate = False
        logging.getLogger("w7.client").info("calling model with key %s for %s", "sk-proj_AbC123xyz-99", "ana.lee+test@shop.io")
        root.info("100%% of %d requests ok; short sk-abc stays", 5)
        assert "sk-proj" not in s.getvalue() and "ana.lee" not in s.getvalue()
        assert s.getvalue().splitlines() == ["w7.client calling model with key [REDACTED] for [REDACTED]", "w7 100% of 5 requests ok; short sk-abc stays"]
        """,
        hints=["`record.getMessage()` gives the message with arguments applied; then set `record.msg` to the redacted text and `record.args = None`."],
        solution="""
        import logging, re

        _PATTERNS = [
            re.compile(r"sk-[A-Za-z0-9_-]{8,}"),
            re.compile(r"[\\w.+-]+@[\\w-]+(\\.[\\w-]+)+"),
        ]


        class RedactFilter(logging.Filter):
            def filter(self, record):
                message = record.getMessage()
                for pattern in _PATTERNS:
                    message = pattern.sub("[REDACTED]", message)
                record.msg = message
                record.args = None
                return True
        """,
        why="""Secrets usually arrive through the **arguments**, not the format string, so redacting `record.msg` alone would miss the key; formatting first with `getMessage()`
        and then redacting covers both. Storing the result with `args = None` stops the message from being formatted a second time, which matters because
        `%%` has already been turned into `%` and a stray `%` would break a second formatting pass. Attached to the handler, the filter sees records propagated
        from every child logger; on the `w7` logger it would only see records created there. Redaction is a safety net, not a licence: the first defence is not
        passing secrets to log calls at all."""),
    choose("Logging an expensive debug value", "medium", tag="GenAI",
        prompt="Debug logging is off. Both run in the hot path 50 times per request. Which is faster?",
        setup="""import json, logging
log = logging.getLogger("c8.quiet")
log.setLevel(logging.INFO)
log.propagate = False
log.handlers[:] = [logging.NullHandler()]
state = {"docs": [{"id": i, "text": "x" * 50} for i in range(200)]}""",
        options={
            "a": "for _ in range(50):\n    log.debug(\"state %s\", json.dumps(state))",
            "b": "for _ in range(50):\n    if log.isEnabledFor(logging.DEBUG):\n        log.debug(\"state %s\", json.dumps(state))",
        },
        answer="b",
        hints=["Is `json.dumps(state)` evaluated in option A when the record is dropped?"],
        why="""Lazy `%s` formatting only defers turning the arguments into text; the arguments themselves are evaluated before `log.debug` is even called, so option A
        serialises the whole state 50 times and throws the result away. The `isEnabledFor` guard skips the work entirely when debug is off, and costs almost
        nothing (the result is cached per logger). Use the guard only when computing an argument is expensive; for ordinary values, lazy arguments are enough."""),
    trace("Where records go", "medium",
        prompt="Fill in `last` (the last line written) and `count` (lines written so far) after each marked line.",
        code="""
        import io, logging

        s = io.StringIO()
        h = logging.StreamHandler(s)
        h.setFormatter(logging.Formatter("%(name)s %(levelname)s %(message)s"))
        app = logging.getLogger("t9.app")
        app.setLevel(logging.INFO)
        app.handlers[:] = [h]
        app.propagate = False
        db = logging.getLogger("t9.app.db")

        def step(method, message):
            method(message)
            lines = s.getvalue().splitlines()
            return (lines[-1] if lines else ""), len(lines)

        last, count = step(db.debug, "query")  # row: "debug from child"
        last, count = step(db.warning, "slow query")  # row: "warning from child"
        db.setLevel(logging.DEBUG)
        last, count = step(db.debug, "plan")  # row: "child level lowered"
        h.setLevel(logging.WARNING)
        last, count = step(db.info, "rows=3")  # row: "handler raised"
        """,
        trace_vars=["last", "count"],
        hints=["The level check happens on the logger where the record is created; handlers then apply their own level."],
        why="""The child inherits `INFO`, so its debug record is never created and nothing is written. Its warning passes and propagates to the handler on `t9.app`. Once the
        child's own level is `DEBUG`, its debug records pass the logger check and the parent's handler, at `NOTSET`, writes them, even though the **parent
        logger** is at `INFO`: ancestors' levels are not consulted during propagation, only their handlers' levels. Raising the handler to `WARNING` then drops
        the info record, so the last line and the count stay the same."""),
    fix("A library that logs to the root logger", "medium", tag="RAG",
        prompt="""`ragkit.search.rag_search` is a small library function. It logs with `logging.info` and `logging.warning`, so applications cannot raise or lower its
        verbosity separately, and its records claim to come from `root`. Make it log through the logger `ragkit.search` and give the package logger `ragkit` a
        `NullHandler`, as libraries should.""",
        code="""
        import logging

        def rag_search(query, index):
            logging.info("searching for %r", query)
            hits = [doc for doc in index if query.lower() in doc.lower()]
            if not hits:
                logging.warning("no hits for %r", query)
            return hits
        """,
        tests="""
        import logging
        class ListHandler(logging.Handler):
            def __init__(self):
                super().__init__()
                self.records = []
            def emit(self, record):
                self.records.append(record)
        pkg = logging.getLogger("ragkit")
        cap = ListHandler()
        pkg.addHandler(cap)
        pkg.setLevel(logging.INFO)
        pkg.propagate = False
        assert rag_search("refund", ["Refund policy", "Shipping"]) == ["Refund policy"] and rag_search("tax", ["Shipping"]) == []
        assert [(r.name, r.levelname, r.getMessage()) for r in cap.records] == [("ragkit.search", "INFO", "searching for 'refund'"),
            ("ragkit.search", "INFO", "searching for 'tax'"), ("ragkit.search", "WARNING", "no hits for 'tax'")]
        assert any(isinstance(h, logging.NullHandler) for h in pkg.handlers)
        pkg.removeHandler(cap)
        """,
        hints=["`log = logging.getLogger(\"ragkit.search\")` at module level (in the real package, `getLogger(__name__)`).",
               "`logging.getLogger(\"ragkit\").addHandler(logging.NullHandler())`."],
        solution="""
        import logging

        logging.getLogger("ragkit").addHandler(logging.NullHandler())
        log = logging.getLogger("ragkit.search")

        def rag_search(query, index):
            log.info("searching for %r", query)
            hits = [doc for doc in index if query.lower() in doc.lower()]
            if not hits:
                log.warning("no hits for %r", query)
            return hits
        """,
        why="""Module-level `logging.info` logs on the root logger, so the application can only turn the library up or down together with everything else, and log lines
        do not say where they came from. Worse, when the root has no handlers, those functions call `basicConfig()` themselves, configuring the application's
        logging behind its back. A named logger fits into the hierarchy, so `logging.getLogger("ragkit").setLevel(logging.WARNING)` silences the library's
        chatter alone. The `NullHandler` stops Python's "last resort" handler from printing the library's warnings to standard error when the application has
        configured nothing, and leaves the decision to the application."""),
    write("Request ids on every line", "medium", tag="GenAI",
        prompt="""Write a `ContextVar` `request_id` (default `"-"`), a `ContextFilter(logging.Filter)` that sets `record.request_id` from it and returns `True`, and
        `handle(rid, fn, *args)` that sets the request id, calls `fn(*args)`, and restores the previous id afterwards, even if `fn` raises.""",
        code="""
        import logging
        from contextvars import ContextVar

        def handle(rid, fn, *args):
            pass
        """,
        tests="""
        import io, logging
        s = io.StringIO()
        h = logging.StreamHandler(s)
        h.addFilter(ContextFilter())
        h.setFormatter(logging.Formatter("%(request_id)s %(message)s"))
        log = logging.getLogger("w11.api")
        log.handlers[:] = [h]
        log.setLevel(logging.INFO)
        log.propagate = False
        def retrieve(q):
            log.info("retrieving %s", q)
            return 3
        def answer(q):
            log.info("answering %s", q)
            n = handle("r-1.sub", retrieve, q)
            log.info("got %d docs", n)
            raise TimeoutError("model slow")
        log.info("start")
        try:
            handle("r-1", answer, "refunds")
        except TimeoutError:
            log.info("after failure")
        assert s.getvalue().splitlines() == ["- start", "r-1 answering refunds", "r-1.sub retrieving refunds", "r-1 got 3 docs", "- after failure"]
        assert request_id.get() == "-"
        """,
        hints=["`token = request_id.set(rid)`, then `request_id.reset(token)` in a `finally`."],
        solution="""
        import logging
        from contextvars import ContextVar

        request_id = ContextVar("request_id", default="-")


        class ContextFilter(logging.Filter):
            def filter(self, record):
                record.request_id = request_id.get()
                return True


        def handle(rid, fn, *args):
            token = request_id.set(rid)
            try:
                return fn(*args)
            finally:
                request_id.reset(token)
        """,
        why="""The filter adds the current request id to every record passing through the handler, so no logging call needs to mention it, and a formatter can use
        `%(request_id)s` safely because every record has it. `set` returns a token, and `reset(token)` restores exactly the previous value, which makes nested
        scopes (a sub-request inside a request) and failures behave: after the timeout, the id is back to `-`. Because context variables are per thread and per
        `asyncio` task, concurrent requests each see their own id (14.4); a module-level global would mix them up. Searching the logs for `r-1` then shows one
        request's whole story."""),
    predict("Exceptions and exc_info", "medium",
        code="""
        import io, logging

        s = io.StringIO()
        h = logging.StreamHandler(s)
        h.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
        log = logging.getLogger("p12.exc")
        log.handlers[:] = [h]
        log.setLevel(logging.INFO)
        log.propagate = False

        try:
            {"a": 1}["b"]
        except KeyError:
            log.exception("lookup failed for %s", "b")
            log.warning("handled", exc_info=False)
        lines = s.getvalue().splitlines()
        print(lines[0], "|", lines[1], "|", lines[-2], "|", lines[-1])
        log.info("outside", exc_info=True)
        print(s.getvalue().splitlines()[-2:])
        """,
        hints=["`exception` adds the traceback; `exc_info=True` outside an `except` block has no exception to attach."],
        why="""`log.exception` writes the message and then the traceback, which starts with the usual header and ends with the exception type and its message; the warning
        with `exc_info=False` is a single line. Outside an `except` block there is no current exception, so `exc_info=True` attaches the empty triple and
        the formatter prints `NoneType: None`, a sign in real logs that someone passed `exc_info=True` in the wrong place."""),
)

section("hard", "Hard",
    write("A decorator that logs LLM calls", "hard", tag="GenAI",
        prompt="""Write `log_llm_calls(logger, model, clock=time.perf_counter)`, a decorator factory for functions `fn(prompt, **kwargs)`. On success it logs at `INFO` the
        message `"llm_call"` with `extra` fields `model`, `latency_ms` (rounded int) and `prompt_chars`, and returns the result. On an exception it logs at
        `ERROR` the message `"llm_call failed"` with the traceback and the same fields, then re-raises. Preserve the function's name with `functools.wraps`.""",
        code="""
        import functools, logging, time

        def log_llm_calls(logger, model, clock=time.perf_counter):
            pass
        """,
        tests="""
        import logging
        class ListHandler(logging.Handler):
            def __init__(self):
                super().__init__()
                self.records = []
            def emit(self, record):
                self.records.append(record)
        cap = ListHandler()
        log = logging.getLogger("w13.llm")
        log.handlers[:] = [cap]
        log.setLevel(logging.INFO)
        log.propagate = False
        ticks = iter([10.0, 10.25, 20.0, 21.5])

        @log_llm_calls(log, "small-v2", clock=lambda: next(ticks))
        def complete(prompt, temperature=0.0):
            if "crash" in prompt:
                raise ConnectionError("reset by peer")
            return prompt.upper()

        assert complete("hello", temperature=0.5) == "HELLO" and complete.__name__ == "complete"
        try:
            complete("please crash")
            assert False
        except ConnectionError:
            pass
        ok, bad = cap.records
        assert (ok.levelname, ok.getMessage(), ok.model, ok.latency_ms, ok.prompt_chars, ok.exc_info) == ("INFO", "llm_call", "small-v2", 250, 5, None)
        assert (bad.levelname, bad.getMessage(), bad.latency_ms, bad.prompt_chars) == ("ERROR", "llm_call failed", 1500, 12) and bad.exc_info[0] is ConnectionError
        """,
        hints=["Take `start = clock()` before the call and compute the latency in both branches.",
               "`logger.exception(\"llm_call failed\", extra=...)` inside `except`, then a bare `raise`."],
        solution="""
        import functools, logging, time


        def log_llm_calls(logger, model, clock=time.perf_counter):
            def decorator(fn):
                @functools.wraps(fn)
                def wrapper(prompt, **kwargs):
                    start = clock()
                    try:
                        result = fn(prompt, **kwargs)
                    except Exception:
                        fields = {"model": model, "latency_ms": round((clock() - start) * 1000), "prompt_chars": len(prompt)}
                        logger.exception("llm_call failed", extra=fields)
                        raise
                    fields = {"model": model, "latency_ms": round((clock() - start) * 1000), "prompt_chars": len(prompt)}
                    logger.info("llm_call", extra=fields)
                    return result
                return wrapper
            return decorator
        """,
        why="""Every external call should produce one record with its outcome and latency, and a decorator (8.2) adds that to any client function without touching its code.
        The message is a fixed event name, `llm_call`, and the variable data travels in `extra` fields, which is what structured logs need: a dashboard can then
        group by `model` and chart `latency_ms` without parsing text. The clock is injectable so the test is deterministic, and the failure path logs the
        traceback once and re-raises, so the caller can still retry or handle it (7.3). The prompt's **length** is logged, not its content, which may contain
        personal data."""),
    write("Configure an application's logging with dictConfig", "hard", tag="Data work",
        prompt="""Write `configure_logging(level="INFO", json_format=False, stream=None)` that configures the **root** logger with `logging.config.dictConfig`: one
        `StreamHandler` writing to `stream` (default `sys.stderr`), formatted either as `"%(levelname)s %(name)s: %(message)s"` or with the given
        `JsonFormatter`; the root at `level`; the noisy libraries `httpx`, `urllib3` and `openai` at `WARNING`; and loggers that already exist left enabled.
        Calling it again must replace the configuration, not add handlers. An unknown level raises `ValueError`.""",
        code="""
        import json, logging, logging.config, sys

        class JsonFormatter(logging.Formatter):
            def format(self, record):
                return json.dumps({"level": record.levelname, "logger": record.name, "message": record.getMessage()})

        NOISY = ("httpx", "urllib3", "openai")

        def configure_logging(level="INFO", json_format=False, stream=None):
            pass
        """,
        tests="""
        import io, json, logging
        root = logging.getLogger()
        saved = (root.handlers[:], root.level)
        early = logging.getLogger("w14.early")
        out = io.StringIO()
        configure_logging("DEBUG", stream=out)
        configure_logging("INFO", stream=out)
        logging.getLogger("w14.app").info("started %s", "v1")
        logging.getLogger("w14.app").debug("hidden")
        logging.getLogger("httpx").info("GET /v1/models 200")
        early.warning("still enabled")
        assert out.getvalue().splitlines() == ["INFO w14.app: started v1", "WARNING w14.early: still enabled"]
        assert len(root.handlers) == 1 and logging.getLogger("openai").level == logging.WARNING
        jout = io.StringIO()
        configure_logging("WARNING", json_format=True, stream=jout)
        logging.getLogger("w14.app").error("boom")
        assert json.loads(jout.getvalue()) == {"level": "ERROR", "logger": "w14.app", "message": "boom"} and len(out.getvalue().splitlines()) == 2
        def bad_level():
            try:
                configure_logging("LOUD", stream=io.StringIO())
            except ValueError:
                return True
            return False
        assert bad_level()
        root.handlers[:] = saved[0]
        root.setLevel(saved[1])
        for name in NOISY:
            logging.getLogger(name).setLevel(logging.NOTSET)
        """,
        hints=["The dict needs `version: 1`, `disable_existing_loggers: False`, `formatters`, `handlers`, `root` and `loggers`.",
               "A formatter entry `{\"()\": JsonFormatter}` builds a custom class; a handler entry can pass `\"stream\": stream` straight to `StreamHandler`."],
        solution="""
        import json, logging, logging.config, sys


        class JsonFormatter(logging.Formatter):
            def format(self, record):
                return json.dumps({"level": record.levelname, "logger": record.name, "message": record.getMessage()})


        NOISY = ("httpx", "urllib3", "openai")


        def configure_logging(level="INFO", json_format=False, stream=None):
            config = {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "plain": {"format": "%(levelname)s %(name)s: %(message)s"},
                    "json": {"()": JsonFormatter},
                },
                "handlers": {
                    "main": {
                        "class": "logging.StreamHandler",
                        "formatter": "json" if json_format else "plain",
                        "stream": stream if stream is not None else sys.stderr,
                    },
                },
                "root": {"level": level, "handlers": ["main"]},
                "loggers": {name: {"level": "WARNING"} for name in NOISY},
            }
            logging.config.dictConfig(config)
        """,
        why="""`dictConfig` describes the whole logging setup as data, which is why real applications load it from a YAML or TOML file and adjust it per environment. It
        **replaces** the root's handlers each time, so the function is idempotent. `disable_existing_loggers: False` is essential: the default `True` silently
        disables every logger created before the call, typically all module-level loggers of already-imported modules, and their messages vanish. The
        `loggers` section quiets HTTP and SDK libraries that log every request at `INFO`, a common source of noise in LLM services. An invalid level fails
        loudly at start-up with `ValueError`, which is where configuration errors should surface."""),
    fix("Read the code: logging in a chat service", "hard", tag="GenAI",
        prompt="""`answer` calls a model and logs as it goes. In production: each call adds another handler, so lines multiply; the full API key appears in the logs; the
        debug f-string formats the question even with debug off; and failures are logged without a traceback. Fix all four: one handler however many calls,
        only the key's last 4 characters (`key ...wxyz`), lazy debug arguments, and `log.exception("model call failed")`. `answer` still returns `None` on
        failure.""",
        code="""
        import logging


        def get_logger(stream):
            log = logging.getLogger("f15.chat")
            handler = logging.StreamHandler(stream)
            handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
            log.addHandler(handler)
            log.setLevel(logging.INFO)
            log.propagate = False
            return log


        def answer(question, client, api_key, stream):
            log = get_logger(stream)
            log.info(f"calling model with key {api_key}")
            log.debug(f"question: {question}")
            try:
                return client(question, api_key)
            except Exception as e:
                log.error(f"model call failed: {e}")
                return None
        """,
        tests="""
        import io
        class Question:
            conversions = 0
            def __init__(self, text):
                self.text = text
            def __str__(self):
                Question.conversions += 1
                return self.text
            def __format__(self, spec):
                Question.conversions += 1
                return self.text
        def client(q, key):
            if "fail" in q.text:
                raise RuntimeError("upstream 503")
            return f"answer to {q.text}"
        import logging
        logging.getLogger("f15.chat").handlers.clear()
        s = io.StringIO()
        key = "sk-live-1234567890wxyz"
        assert answer(Question("refunds?"), client, key, s) == "answer to refunds?"
        assert answer(Question("please fail"), client, key, s) is None
        lines = s.getvalue().splitlines()
        assert lines[:3] == ["INFO calling model with key ...wxyz", "INFO calling model with key ...wxyz", "ERROR model call failed"]
        assert key not in s.getvalue() and "RuntimeError: upstream 503" in lines[-1] and "Traceback (most recent call last):" in lines
        assert Question.conversions == 0
        """,
        hints=["Create the handler only if the logger has none (`if not log.handlers:`).",
               "`log.info(\"calling model with key ...%s\", api_key[-4:])` and `log.debug(\"question: %s\", question)`."],
        solution="""
        import logging


        def get_logger(stream):
            log = logging.getLogger("f15.chat")
            if not log.handlers:
                handler = logging.StreamHandler(stream)
                handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
                log.addHandler(handler)
                log.setLevel(logging.INFO)
                log.propagate = False
            return log


        def answer(question, client, api_key, stream):
            log = get_logger(stream)
            log.info("calling model with key ...%s", api_key[-4:])
            log.debug("question: %s", question)
            try:
                return client(question, api_key)
            except Exception:
                log.exception("model call failed")
                return None
        """,
        why="""Each bug is a lesson section. Handlers were added on every call because loggers are global singletons, so configuration must happen once (here guarded by
        `if not log.handlers`; in an application, at start-up). A full key in a log file is a leaked key, since logs are copied to many systems and kept for
        months, so log only an identifying suffix, or nothing. The f-string formatted the question, calling `__format__`, for a debug message that was then
        dropped; lazy `%s` arguments are only converted when emitted, so the conversion counter stays at 0. `log.error` with the message loses the traceback,
        while `log.exception` keeps it. Together, these are the logging review comments seen most often on LLM service code."""),
    predict("Propagation, levels and disable", "hard",
        code="""
        import io, logging

        s = io.StringIO()
        h = logging.StreamHandler(s)
        h.setFormatter(logging.Formatter("%(name)s:%(message)s"))
        parent = logging.getLogger("p16")
        parent.setLevel(logging.INFO)
        parent.handlers[:] = [h]
        parent.propagate = False
        child = logging.getLogger("p16.worker")
        child.handlers[:] = [h]

        child.info("twice?")
        child.propagate = False
        child.info("once")
        child.propagate = True
        child.setLevel(logging.ERROR)
        parent.setLevel(logging.CRITICAL)
        child.warning("dropped")
        child.error("err")
        logging.disable(logging.ERROR)
        child.error("disabled")
        child.critical("crit")
        logging.disable(logging.NOTSET)
        print(s.getvalue().splitlines())
        print(child.getEffectiveLevel(), logging.getLogger("p16.worker.sub").getEffectiveLevel(), child.parent.name)
        """,
        hints=["A record goes to its logger's handlers and to every ancestor's while `propagate` is true; ancestors' logger levels are not checked.",
               "`logging.disable(level)` drops everything at that level and below, everywhere."],
        why="""With the same handler on child and parent, a propagating record is written twice; with `propagate = False`, once. The child's own `ERROR` level drops the
        warning. The error is written twice even though the parent is now at `CRITICAL`, because during propagation only the ancestors' **handlers** are
        used, not their logger levels. `logging.disable(logging.ERROR)` is a global switch that drops records of `ERROR` and below on every logger, so only the
        critical record appears, twice again. The grandchild inherits the child's level, 40."""),
)

section("interview", "Interview questions",
    explain("Why use logging instead of print, and what would you log in an LLM-backed service?", "medium", tag="Interview",
        why="""`logging` gives every message a severity, a source (the logger name), a timestamp and context, and lets the application decide at run time where messages go
        and which levels are kept, without changing the code that emits them; libraries can log without forcing output on their users. `print` has none of
        that and mixes diagnostics with real output. In an LLM service I would log, at boundaries: request start and end with a request id, route, status and
        total latency; every model call with model name, latency, token counts, cost estimate, retries and finish reason; retrieval with the number of chunks
        and top scores; tool calls with name, outcome and latency; validation failures of structured output with error types; and every handled exception
        with its traceback, once. I would not log raw prompts, documents or answers by default (personal data, secrets, volume), only their ids, sizes or hashes,
        with content sampling behind an explicit, access-controlled switch. Logs go out as structured JSON with a request id on every line."""),
    explain("Should a library configure logging? What should it do instead?", "medium", tag="Interview",
        why="""No. Configuration (handlers, formats, levels, destinations) belongs to the **application**, because only it knows whether it runs in a notebook, a test, a
        CLI or a server with a log shipper. A library that calls `logging.basicConfig`, adds handlers to the root, or prints, overrides or duplicates the
        application's choices, and module-level `logging.info(...)` calls can configure the root logger implicitly. A library should create loggers with
        `logging.getLogger(__name__)`, so its messages are namespaced under the package and can be tuned with one line by the application; log with lazy
        arguments at sensible levels (`DEBUG` for detail, `WARNING` for handled problems, never `ERROR` for something it re-raises); attach a
        `logging.NullHandler()` to its top-level logger so nothing is printed when the application has not configured logging; and never log secrets passed to
        it."""),
    explain("How do you debug one failing request in a busy, concurrent service from its logs?", "hard", tag="Interview",
        why="""Without correlation, lines from hundreds of interleaved requests are useless, so every request gets an id at the edge (or reuses an incoming
        `X-Request-ID` or trace id), stored in a `ContextVar` and attached to every record by a filter, so it survives threads and `asyncio` tasks. The id is
        returned to the client and passed to downstream services in headers, so one search in the log platform shows the whole story across services. Logs
        are structured JSON with consistent fields (request id, user or tenant, model, latency, error type), so you can filter instead of grep. Each boundary
        logs one line with its outcome and latency, and each handled exception logs its traceback once. For latency questions, logs are complemented by
        **tracing** (OpenTelemetry spans for each step, model call and tool call), and by **metrics** for rates and percentiles, since logs are expensive to
        aggregate. Finally, sample verbose debug logs, keep retention and access controls on logs that may contain personal data, and make log levels
        adjustable at run time so you can raise detail for one component while investigating."""),
)

recap(
    "Use `logging.getLogger(__name__)` per module; loggers form a dotted tree, inherit levels, and propagate records to ancestors' handlers.",
    "Levels DEBUG < INFO < WARNING < ERROR < CRITICAL filter on loggers and handlers; pass arguments lazily, and guard expensive ones with `isEnabledFor`.",
    "Applications configure once (`basicConfig`, `dictConfig` with `disable_existing_loggers: False`); libraries only add a `NullHandler`.",
    "`log.exception` in `except` keeps the traceback; log each exception once, where it is handled.",
    "Filters add context (request ids via `ContextVar`) and redact secrets; structured JSON logs with consistent fields serve machines and people.",
)
